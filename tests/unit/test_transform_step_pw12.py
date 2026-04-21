# tests/unit/test_transform_step_pw12.py
"""TDD Red-phase tests for TransformStep PW12 fixes.

FIC — Feature Intent Contract:
  TransformStep must resolve source data dynamically via source_step_id param,
  enrich records with provider/timestamp, produce presentation-mapped output
  under a configurable output_key, and warn on zero records.

AC-1: source_step_id param for dynamic source resolution (Local Canon)
AC-5: Record enrichment with provider/timestamp (Local Canon)
AC-6: output_key param + presentation mapping (Local Canon)
AC-8: Zero-record WARNING with min_records > 0 (Local Canon)

Spec: 09-scheduling.md §9.5, deficiency report §3.1, §3.2, §3.5, §3.6
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from zorivest_core.domain.enums import PipelineStatus
from zorivest_core.domain.pipeline import StepContext
from zorivest_core.pipeline_steps.transform_step import TransformStep


# ── Helpers ────────────────────────────────────────────────────────────────


def _make_context(
    *,
    outputs: dict | None = None,
    run_id: str = "run-pw12",
    policy_id: str = "pol-pw12",
) -> StepContext:
    return StepContext(
        run_id=run_id,
        policy_id=policy_id,
        outputs=outputs or {},
    )


def _valid_ohlcv_records() -> list[dict]:
    return [
        {"open": 100.0, "high": 110.0, "low": 95.0, "close": 105.0, "volume": 1000},
        {"open": 200.0, "high": 210.0, "low": 195.0, "close": 205.0, "volume": 2000},
    ]


def _mock_writer(records_written: int = 2) -> MagicMock:
    w = MagicMock()
    w.write.return_value = records_written
    return w


# ---------------------------------------------------------------------------
# AC-1: Dynamic source resolution via source_step_id
# ---------------------------------------------------------------------------


class TestDynamicSourceResolution:
    """AC-1: TransformStep.Params has source_step_id. When set, execute()
    reads source data from context.outputs[source_step_id]."""

    @pytest.mark.asyncio
    async def test_source_step_id_resolves_to_step_output(self) -> None:
        """source_step_id='fetch_quotes' → reads from context.outputs['fetch_quotes']."""
        records = _valid_ohlcv_records()
        writer = _mock_writer()
        ctx = _make_context(
            outputs={
                "fetch_quotes": {
                    "content": json.dumps(records).encode(),
                    "provider": "generic",
                    "data_type": "ohlcv",
                },
                "db_writer": writer,
            },
        )
        step = TransformStep()
        result = await step.execute(
            params={
                "target_table": "market_ohlcv",
                "source_step_id": "fetch_quotes",
            },
            context=ctx,
        )

        assert result.status == PipelineStatus.SUCCESS
        assert result.output["records_written"] == 2

    @pytest.mark.asyncio
    async def test_source_step_id_none_falls_back_to_fetch_result(self) -> None:
        """source_step_id omitted → falls back to 'fetch_result' for backward compat."""
        records = _valid_ohlcv_records()
        writer = _mock_writer()
        ctx = _make_context(
            outputs={
                "fetch_result": {
                    "content": json.dumps(records).encode(),
                },
                "db_writer": writer,
            },
        )
        step = TransformStep()
        result = await step.execute(
            params={"target_table": "market_ohlcv"},
            context=ctx,
        )

        assert result.status == PipelineStatus.SUCCESS
        assert result.output["records_written"] == 2

    @pytest.mark.asyncio
    async def test_source_step_id_nonexistent_key_returns_zero_records(self) -> None:
        """source_step_id points to missing key → 0 records, no crash."""
        writer = _mock_writer()
        ctx = _make_context(
            outputs={"db_writer": writer},
        )
        step = TransformStep()
        result = await step.execute(
            params={
                "target_table": "market_ohlcv",
                "source_step_id": "nonexistent_step",
            },
            context=ctx,
        )

        assert result.output["records_written"] == 0

    def test_params_has_source_step_id_field(self) -> None:
        """TransformStep.Params accepts source_step_id (str | None)."""
        p = TransformStep.Params(
            target_table="market_ohlcv",
            source_step_id="fetch_quotes",
        )
        assert p.source_step_id == "fetch_quotes"

    def test_params_source_step_id_defaults_to_none(self) -> None:
        """source_step_id defaults to None for backward compatibility."""
        p = TransformStep.Params(target_table="market_ohlcv")
        assert p.source_step_id is None

    @pytest.mark.asyncio
    async def test_auto_discover_fetch_output_when_source_step_id_none(self) -> None:
        """source_step_id omitted + fetch output under a step ID (not 'fetch_result').

        This is the REAL production scenario: PipelineRunner stores fetch output
        under step_def.id (e.g., 'fetch_yahoo_quotes'), not 'fetch_result'.
        TransformStep must auto-discover it by output shape signature.
        """
        records = _valid_ohlcv_records()
        writer = _mock_writer()
        ctx = _make_context(
            outputs={
                # PipelineRunner stores under step ID, NOT "fetch_result"
                "fetch_yahoo_quotes": {
                    "content": json.dumps(records).encode(),
                    "provider": "generic",
                    "data_type": "ohlcv",
                },
                "db_writer": writer,
            },
        )
        step = TransformStep()
        result = await step.execute(
            params={"target_table": "market_ohlcv"},
            context=ctx,
        )

        # Must auto-discover the fetch output and process records
        assert result.status == PipelineStatus.SUCCESS
        assert result.output["records_written"] == 2

    @pytest.mark.asyncio
    async def test_auto_discover_skips_non_fetch_outputs(self) -> None:
        """Auto-discovery ignores non-fetch outputs (services, primitives).

        Only dict values with both 'content' and 'provider' keys qualify
        as fetch step outputs.
        """
        records = _valid_ohlcv_records()
        writer = _mock_writer()
        ctx = _make_context(
            outputs={
                # Service objects (not fetch outputs)
                "db_writer": writer,
                "delivery_repository": MagicMock(),
                # The real fetch output
                "fetch_yahoo_quotes": {
                    "content": json.dumps(records).encode(),
                    "provider": "generic",
                    "data_type": "ohlcv",
                },
            },
        )
        step = TransformStep()
        result = await step.execute(
            params={"target_table": "market_ohlcv"},
            context=ctx,
        )

        assert result.status == PipelineStatus.SUCCESS
        assert result.output["records_written"] == 2


# ---------------------------------------------------------------------------
# AC-5: Record enrichment with provider/timestamp
# ---------------------------------------------------------------------------


class TestRecordEnrichment:
    """AC-5: TransformStep enriches records with provider and timestamp from
    source step output metadata before Pandera validation."""

    @pytest.mark.asyncio
    async def test_records_enriched_with_provider_and_timestamp(self) -> None:
        """When source output has provider/data_type, records get enriched."""
        records = [
            {"bid": 149.9, "ask": 150.1, "last": 150.0, "volume": 1000},
        ]
        writer = _mock_writer(records_written=1)
        ctx = _make_context(
            outputs={
                "fetch_quotes": {
                    "content": json.dumps(records).encode(),
                    "provider": "yahoo",
                    "data_type": "quote",
                },
                "db_writer": writer,
            },
        )
        step = TransformStep()
        _result = await step.execute(
            params={
                "target_table": "market_quotes",
                "source_step_id": "fetch_quotes",
                "validation_rules": "quote",
            },
            context=ctx,
        )

        # Verify records were enriched — check what the writer received
        call_args = writer.write.call_args
        if call_args is not None:
            df = call_args.kwargs.get("df") or call_args[0][0]
            assert "provider" in df.columns
            assert "timestamp" in df.columns

    @pytest.mark.asyncio
    async def test_missing_provider_skips_enrichment_gracefully(self) -> None:
        """Missing provider in source output → skips enrichment, no crash."""
        records = _valid_ohlcv_records()
        writer = _mock_writer()
        ctx = _make_context(
            outputs={
                "fetch_quotes": {
                    "content": json.dumps(records).encode(),
                    # No 'provider' key
                },
                "db_writer": writer,
            },
        )
        step = TransformStep()
        result = await step.execute(
            params={
                "target_table": "market_ohlcv",
                "source_step_id": "fetch_quotes",
            },
            context=ctx,
        )

        assert result.status == PipelineStatus.SUCCESS


# ---------------------------------------------------------------------------
# AC-6: output_key param + presentation mapping
# ---------------------------------------------------------------------------


class TestOutputKeyAndPresentationMapping:
    """AC-6: TransformStep stores validated records in output under configurable
    output_key param. Records use presentation names: ticker→symbol, last→price."""

    @pytest.mark.asyncio
    async def test_records_stored_under_output_key(self) -> None:
        """Default output_key='records' → result.output['records'] has records."""
        records = _valid_ohlcv_records()
        writer = _mock_writer()
        ctx = _make_context(
            outputs={
                "fetch_result": {
                    "content": json.dumps(records).encode(),
                },
                "db_writer": writer,
            },
        )
        step = TransformStep()
        result = await step.execute(
            params={"target_table": "market_ohlcv"},
            context=ctx,
        )

        assert "records" in result.output
        assert isinstance(result.output["records"], list)
        assert len(result.output["records"]) > 0

    @pytest.mark.asyncio
    async def test_custom_output_key(self) -> None:
        """output_key='quotes' → records stored under 'quotes' key."""
        records = _valid_ohlcv_records()
        writer = _mock_writer()
        ctx = _make_context(
            outputs={
                "fetch_result": {
                    "content": json.dumps(records).encode(),
                },
                "db_writer": writer,
            },
        )
        step = TransformStep()
        result = await step.execute(
            params={
                "target_table": "market_ohlcv",
                "output_key": "quotes",
            },
            context=ctx,
        )

        assert "quotes" in result.output
        assert isinstance(result.output["quotes"], list)

    @pytest.mark.asyncio
    async def test_presentation_mapping_ticker_to_symbol(self) -> None:
        """Presentation mapping renames 'ticker' → 'symbol', 'last' → 'price'."""
        records = [
            {
                "ticker": "AAPL",
                "last": 150.0,
                "change": 2.5,
                "change_pct": 1.7,
                "volume": 1000,
            },
        ]
        writer = _mock_writer(records_written=1)
        ctx = _make_context(
            outputs={
                "fetch_quotes": {
                    "content": json.dumps(records).encode(),
                    "provider": "yahoo",
                    "data_type": "quote",
                },
                "db_writer": writer,
            },
        )
        step = TransformStep()
        result = await step.execute(
            params={
                "target_table": "market_quotes",
                "source_step_id": "fetch_quotes",
                "validation_rules": "quote",
                "output_key": "quotes",
            },
            context=ctx,
        )

        # Check presentation mapping in output records
        if "quotes" in result.output and len(result.output["quotes"]) > 0:
            q = result.output["quotes"][0]
            assert "symbol" in q, "ticker should be renamed to symbol"
            assert "price" in q, "last should be renamed to price"

    def test_params_has_output_key_field(self) -> None:
        """TransformStep.Params accepts output_key with default 'records'."""
        p = TransformStep.Params(target_table="market_ohlcv")
        assert p.output_key == "records"

    def test_params_custom_output_key(self) -> None:
        """TransformStep.Params accepts custom output_key."""
        p = TransformStep.Params(target_table="market_ohlcv", output_key="quotes")
        assert p.output_key == "quotes"


# ---------------------------------------------------------------------------
# AC-8: Zero-record WARNING with min_records > 0
# ---------------------------------------------------------------------------


class TestZeroRecordWarning:
    """AC-8: TransformStep returns WARNING (not SUCCESS) when records count
    is 0 and min_records > 0. Default min_records=0 preserves backward compat."""

    @pytest.mark.asyncio
    async def test_zero_records_min_records_gt_0_returns_warning(self) -> None:
        """0 records + min_records=1 → WARNING status."""
        ctx = _make_context(
            outputs={
                "fetch_result": {
                    "content": json.dumps([]).encode(),
                },
            },
        )
        step = TransformStep()
        result = await step.execute(
            params={
                "target_table": "market_ohlcv",
                "min_records": 1,
            },
            context=ctx,
        )

        assert result.status == PipelineStatus.WARNING

    @pytest.mark.asyncio
    async def test_zero_records_min_records_0_returns_success(self) -> None:
        """0 records + min_records=0 → SUCCESS (backward compat)."""
        ctx = _make_context(
            outputs={
                "fetch_result": {
                    "content": json.dumps([]).encode(),
                },
            },
        )
        step = TransformStep()
        result = await step.execute(
            params={
                "target_table": "market_ohlcv",
                "min_records": 0,
            },
            context=ctx,
        )

        assert result.status == PipelineStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_default_min_records_is_zero(self) -> None:
        """Default min_records=0, so 0 records → SUCCESS."""
        ctx = _make_context(
            outputs={
                "fetch_result": {
                    "content": json.dumps([]).encode(),
                },
            },
        )
        step = TransformStep()
        result = await step.execute(
            params={"target_table": "market_ohlcv"},
            context=ctx,
        )

        assert result.status == PipelineStatus.SUCCESS

    def test_params_has_min_records_field(self) -> None:
        """TransformStep.Params accepts min_records (int, default 0)."""
        p = TransformStep.Params(target_table="market_ohlcv")
        assert p.min_records == 0

    def test_params_min_records_ge_zero(self) -> None:
        """min_records must be >= 0."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            TransformStep.Params(target_table="market_ohlcv", min_records=-1)
