# packages/core/src/zorivest_core/pipeline_steps/market_data_store_step.py
"""MarketDataStoreStep — persist fetched market data to expansion tables (§8a.12).

Pipeline step that validates, batch-processes, and writes market data records
to the appropriate expansion table based on data_type auto-mapping.

Supports INSERT (append) and UPSERT (merge by dedup keys) write modes.
Per-table Pydantic validators reject malformed records before write.

Spec: 08a-market-data-expansion.md §8a.12
MEU: 193
"""

from __future__ import annotations

import logging
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from zorivest_core.domain.enums import PipelineStatus
from zorivest_core.domain.pipeline import StepContext, StepResult
from zorivest_core.domain.step_registry import RegisteredStep

logger = logging.getLogger(__name__)

# ── Data type → table mapping (AC-3) ─────────────────────────────────────

DATA_TYPE_TABLE_MAP: dict[str, str] = {
    "ohlcv": "market_ohlcv",
    "earnings": "market_earnings",
    "dividends": "market_dividends",
    "splits": "market_splits",
    "insider": "market_insider",
    "fundamentals": "market_fundamentals",
}

# ── Dedup key columns per data type (AC-5) ────────────────────────────────

DEDUP_KEY_COLUMNS: dict[str, list[str]] = {
    "ohlcv": ["ticker", "timestamp", "provider"],
    "earnings": ["ticker", "fiscal_period", "fiscal_year"],
    "dividends": ["ticker", "ex_date"],
    "splits": ["ticker", "execution_date"],
    "insider": ["ticker", "name", "transaction_date", "transaction_code"],
    "fundamentals": ["ticker", "metric", "period", "provider"],
}

# ── Valid data_type values ────────────────────────────────────────────────

VALID_DATA_TYPES = list(DATA_TYPE_TABLE_MAP.keys())

# ── Per-table record validators (AC-6) ────────────────────────────────────


class OHLCVRecord(BaseModel):
    """Validator for OHLCV records."""

    model_config = {"extra": "forbid"}

    ticker: str
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    vwap: float | None = None
    trade_count: int | None = None
    adjusted_close: float | None = None
    provider: str
    data_type: str | None = None
    fetched_at: str | None = None


class EarningsRecord(BaseModel):
    """Validator for earnings records."""

    model_config = {"extra": "forbid"}

    ticker: str
    fiscal_period: str
    fiscal_year: int
    report_date: str
    eps_actual: float | None = None
    eps_estimate: float | None = None
    eps_surprise: float | None = None
    revenue_actual: float | None = None
    revenue_estimate: float | None = None
    provider: str


class DividendsRecord(BaseModel):
    """Validator for dividend records."""

    model_config = {"extra": "forbid"}

    ticker: str
    dividend_amount: float
    currency: str
    ex_date: str
    record_date: str | None = None
    pay_date: str | None = None
    declaration_date: str | None = None
    frequency: str | None = None
    provider: str


class SplitsRecord(BaseModel):
    """Validator for stock split records."""

    model_config = {"extra": "forbid"}

    ticker: str
    execution_date: str
    ratio_from: int
    ratio_to: int
    provider: str


class InsiderRecord(BaseModel):
    """Validator for insider transaction records."""

    model_config = {"extra": "forbid"}

    ticker: str
    name: str
    title: str | None = None
    transaction_date: str
    transaction_code: str
    shares: int
    price: float | None = None
    value: float | None = None
    shares_owned_after: int | None = None
    provider: str


class FundamentalsRecord(BaseModel):
    """Validator for fundamentals records."""

    model_config = {"extra": "forbid"}

    ticker: str
    metric: str
    value: float
    period: str
    provider: str
    fetched_at: str | None = None


# Map data_type → validator class
RECORD_VALIDATORS: dict[str, type[BaseModel]] = {
    "ohlcv": OHLCVRecord,
    "earnings": EarningsRecord,
    "dividends": DividendsRecord,
    "splits": SplitsRecord,
    "insider": InsiderRecord,
    "fundamentals": FundamentalsRecord,
}


# ── Config model (AC-2, AC-8) ────────────────────────────────────────────


class MarketDataStoreConfig(BaseModel):
    """Configuration schema for MarketDataStoreStep.

    Validates data_type against allowed enum values,
    write_mode, batch_size, and rejects extra fields.
    """

    model_config = {"extra": "forbid"}

    data_type: str = Field(
        ...,
        description="Market data type to store (ohlcv, earnings, etc.)",
    )
    write_mode: Literal["insert", "upsert"] = Field(
        default="insert",
        description="Write mode: 'insert' (append) or 'upsert' (merge/dedup)",
    )
    batch_size: int = Field(
        default=1000,
        ge=1,
        le=5000,
        description="Number of records per write commit batch",
    )
    ticker: str = Field(
        default="",
        description="Optional ticker filter (1-10 uppercase chars)",
    )
    source_step_id: str | None = Field(
        default=None,
        description="Step ID whose output 'records' key provides data to store. "
        "When set and no inline records are provided, the step pulls "
        "records from context.outputs[source_step_id]['records'].",
    )

    @field_validator("data_type")
    @classmethod
    def validate_data_type(cls, v: str) -> str:
        if v not in VALID_DATA_TYPES:
            raise ValueError(
                f"Invalid data_type '{v}'. Must be one of: {VALID_DATA_TYPES}"
            )
        return v


# ── Step implementation ───────────────────────────────────────────────────


class _DictWrapper:
    """Thin wrapper to satisfy DbWriteAdapter's df.to_dict(orient='records') interface."""

    def __init__(self, records: list[dict[str, Any]]) -> None:
        self._records = records

    def to_dict(self, orient: str = "records") -> list[dict[str, Any]]:
        return self._records


class MarketDataStoreStep(RegisteredStep):
    """Persist fetched market data to the appropriate expansion table.

    Auto-registers as ``type_name="market_data_store"`` in the step registry.
    """

    type_name = "market_data_store"
    side_effects = True

    class Params(BaseModel):
        """Alias for MarketDataStoreConfig — exposed via params_schema()."""

        model_config = {"extra": "forbid"}

        data_type: str
        write_mode: Literal["insert", "upsert"] = "insert"
        batch_size: int = Field(default=1000, ge=1, le=5000)
        ticker: str = ""
        records: list[dict[str, Any]] = Field(default_factory=list)
        source_step_id: str | None = None

        @field_validator("data_type")
        @classmethod
        def validate_data_type(cls, v: str) -> str:
            if v not in VALID_DATA_TYPES:
                raise ValueError(
                    f"Invalid data_type '{v}'. Must be one of: {VALID_DATA_TYPES}"
                )
            return v

    async def execute(self, params: dict, context: StepContext) -> StepResult:
        """Execute the market data store step.

        1. Validate config
        2. Validate each record against per-type Pydantic validator
        3. Write valid records to target table via db_writer
        """
        config = MarketDataStoreConfig(
            **{k: v for k, v in params.items() if k != "records"}
        )
        records: list[dict[str, Any]] = params.get("records", [])

        # Resolve records from prior step output when source_step_id is set
        if not records and config.source_step_id:
            source_output = context.outputs.get(config.source_step_id)
            if isinstance(source_output, dict):
                records = source_output.get("records", [])
            if not records:
                logger.warning(
                    "source_step_id '%s' resolved no records",
                    config.source_step_id,
                )

        target_table = DATA_TYPE_TABLE_MAP[config.data_type]
        validator_cls = RECORD_VALIDATORS.get(config.data_type)

        # Validate records (AC-6)
        valid_records: list[dict[str, Any]] = []
        skipped = 0

        for record in records:
            if validator_cls is not None:
                try:
                    validated = validator_cls(**record)
                    valid_records.append(validated.model_dump(exclude_none=False))
                except Exception as e:
                    logger.warning(
                        "Skipping invalid %s record: %s", config.data_type, e
                    )
                    skipped += 1
            else:
                valid_records.append(record)

        if not valid_records:
            return StepResult(
                status=PipelineStatus.SUCCESS,
                output={
                    "table": target_table,
                    "records_written": 0,
                    "skipped": skipped,
                    "data_type": config.data_type,
                },
            )

        # Get db_writer from context
        db_writer = context.outputs.get("db_writer")
        if db_writer is None:
            raise ValueError(
                "db_writer required in context.outputs for MarketDataStoreStep"
            )

        # Write in batches (AC-7)
        total_written = 0
        for i in range(0, len(valid_records), config.batch_size):
            batch = valid_records[i : i + config.batch_size]
            df_wrapper = _DictWrapper(batch)

            disposition = "append" if config.write_mode == "insert" else "merge"
            key_columns = (
                DEDUP_KEY_COLUMNS.get(config.data_type)
                if disposition == "merge"
                else None
            )

            written = db_writer.write(
                df=df_wrapper,
                table=target_table,
                disposition=disposition,
                key_columns=key_columns,
            )
            total_written += written

        return StepResult(
            status=PipelineStatus.SUCCESS,
            output={
                "table": target_table,
                "records_written": total_written,
                "skipped": skipped,
                "data_type": config.data_type,
                "batch_count": (len(valid_records) + config.batch_size - 1)
                // config.batch_size,
            },
        )
