# packages/core/src/zorivest_core/domain/import_types.py
"""Core Pydantic models for the broker import pipeline.

These models define the canonical ingestion schema shared across all
broker adapters (IBKR FlexQuery, TOS CSV, NinjaTrader CSV, etc.).
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from zorivest_core.domain.enums import (
    AssetClass,
    BrokerType,
    ImportStatus,
    TradeAction,
)


class RawExecution(BaseModel):
    """Canonical ingestion record — all broker data normalizes to this."""

    broker: BrokerType
    account_id: str
    exec_time: datetime  # UTC-normalized
    symbol: str  # Normalized ticker
    asset_class: AssetClass
    side: TradeAction  # BOT / SLD
    quantity: Decimal
    price: Decimal
    commission: Decimal = Decimal("0")
    fees: Decimal = Decimal("0")  # Non-commission fees (routing, exchange, etc.)
    currency: str = "USD"  # ISO 4217 — original trade currency
    base_currency: str = "USD"  # Account base currency
    base_amount: Decimal | None = None  # price × qty in base currency (via fxRateToBase)
    contract_multiplier: Decimal = Decimal("1")
    order_id: str | None = None  # Broker's order reference
    raw_data: dict[str, str] = Field(default_factory=dict)  # Preserved original fields


class ImportError(BaseModel):
    """Per-row error detail for partial-success imports (ADR-0003)."""

    row_number: int | None = None
    field: str
    message: str
    raw_line: str = ""


class ImportResult(BaseModel):
    """Aggregated import result — captures both successes and errors."""

    status: ImportStatus
    broker: BrokerType
    executions: list[RawExecution] = Field(default_factory=list)
    errors: list[ImportError] = Field(default_factory=list)
    total_rows: int = 0
    parsed_rows: int = 0
    skipped_rows: int = 0
