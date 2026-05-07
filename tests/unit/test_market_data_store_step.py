# tests/unit/test_market_data_store_step.py
"""MEU-193 — MarketDataStoreStep unit tests.

FIC: implementation-plan.md §MEU-193 AC-1..AC-8
Tests the pipeline store step for market data persistence:
  AC-1: Step registered as 'market_data_store'
  AC-2: Config validates data_type enum
  AC-3: Auto-mapping resolves data_type → target table
  AC-4: INSERT mode writes new rows without dedup
  AC-5: UPSERT mode deduplicates by ticker+timestamp/date
  AC-6: Per-table validators reject malformed data before write
  AC-7: batch_size controls write commit frequency
  AC-8: Extra fields in config rejected
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

# Ensure step registry is populated
import zorivest_core.pipeline_steps  # noqa: F401


# ── AC-1: Registration ───────────────────────────────────────────────────


class TestAC1Registration:
    """AC-1: MarketDataStoreStep registered as 'market_data_store'."""

    def test_step_registered_in_registry(self) -> None:
        from zorivest_core.domain.step_registry import has_step

        # Also import the module to trigger registration
        from zorivest_core.pipeline_steps import market_data_store_step  # noqa: F401

        assert has_step("market_data_store"), (
            "Expected 'market_data_store' in STEP_REGISTRY"
        )

    def test_step_class_has_correct_type_name(self) -> None:
        from zorivest_core.pipeline_steps.market_data_store_step import (
            MarketDataStoreStep,
        )

        assert MarketDataStoreStep.type_name == "market_data_store"

    def test_step_has_side_effects(self) -> None:
        from zorivest_core.pipeline_steps.market_data_store_step import (
            MarketDataStoreStep,
        )

        assert MarketDataStoreStep.side_effects is True


# ── AC-2: Config data_type enum validation ────────────────────────────────


class TestAC2DataTypeEnum:
    """AC-2: Config validates data_type against enum."""

    VALID_TYPES = [
        "ohlcv",
        "earnings",
        "dividends",
        "splits",
        "insider",
        "fundamentals",
    ]

    @pytest.mark.parametrize("data_type", VALID_TYPES)
    def test_valid_data_types_accepted(self, data_type: str) -> None:
        from zorivest_core.pipeline_steps.market_data_store_step import (
            MarketDataStoreConfig,
        )

        config = MarketDataStoreConfig(data_type=data_type)
        assert config.data_type == data_type

    def test_invalid_data_type_rejected(self) -> None:
        from zorivest_core.pipeline_steps.market_data_store_step import (
            MarketDataStoreConfig,
        )

        with pytest.raises(Exception):  # Pydantic ValidationError
            MarketDataStoreConfig(data_type="invalid")


# ── AC-3: Auto-mapping data_type → target table ──────────────────────────


class TestAC3TableMapping:
    """AC-3: Auto-mapping resolves data_type to correct target table."""

    EXPECTED_MAPPING = {
        "ohlcv": "market_ohlcv",
        "earnings": "market_earnings",
        "dividends": "market_dividends",
        "splits": "market_splits",
        "insider": "market_insider",
        "fundamentals": "market_fundamentals",
    }

    @pytest.mark.parametrize(
        "data_type,expected_table",
        list(EXPECTED_MAPPING.items()),
    )
    def test_data_type_maps_to_table(self, data_type: str, expected_table: str) -> None:
        from zorivest_core.pipeline_steps.market_data_store_step import (
            DATA_TYPE_TABLE_MAP,
        )

        assert DATA_TYPE_TABLE_MAP[data_type] == expected_table


# ── AC-4: INSERT mode writes without dedup ────────────────────────────────


class TestAC4InsertMode:
    """AC-4: INSERT mode writes new rows without dedup."""

    @pytest.mark.asyncio
    async def test_insert_mode_appends(self) -> None:
        from zorivest_core.domain.pipeline import StepContext
        from zorivest_core.pipeline_steps.market_data_store_step import (
            MarketDataStoreStep,
        )

        step = MarketDataStoreStep()
        mock_writer = MagicMock()
        mock_writer.write.return_value = 3

        context = StepContext(
            run_id="test-run",
            policy_id="test-policy",
            outputs={"db_writer": mock_writer},
        )

        await step.execute(
            params={
                "data_type": "ohlcv",
                "write_mode": "insert",
                "records": [
                    {
                        "ticker": "AAPL",
                        "timestamp": "2024-01-01",
                        "open": 100.0,
                        "high": 105.0,
                        "low": 99.0,
                        "close": 103.0,
                        "volume": 1000,
                        "provider": "test",
                    },
                    {
                        "ticker": "AAPL",
                        "timestamp": "2024-01-01",
                        "open": 100.0,
                        "high": 105.0,
                        "low": 99.0,
                        "close": 103.0,
                        "volume": 1000,
                        "provider": "test",
                    },
                    {
                        "ticker": "AAPL",
                        "timestamp": "2024-01-02",
                        "open": 103.0,
                        "high": 107.0,
                        "low": 102.0,
                        "close": 106.0,
                        "volume": 1200,
                        "provider": "test",
                    },
                ],
            },
            context=context,
        )

        # Should call write with disposition="append"
        mock_writer.write.assert_called_once()
        call_kwargs = mock_writer.write.call_args[1]
        assert call_kwargs["disposition"] == "append"
        assert call_kwargs["table"] == "market_ohlcv"


# ── AC-5: UPSERT mode deduplicates ───────────────────────────────────────


class TestAC5UpsertMode:
    """AC-5: UPSERT mode deduplicates by ticker+timestamp/date."""

    @pytest.mark.asyncio
    async def test_upsert_mode_merges(self) -> None:
        from zorivest_core.domain.pipeline import StepContext
        from zorivest_core.pipeline_steps.market_data_store_step import (
            MarketDataStoreStep,
        )

        step = MarketDataStoreStep()
        mock_writer = MagicMock()
        mock_writer.write.return_value = 2

        context = StepContext(
            run_id="test-run",
            policy_id="test-policy",
            outputs={"db_writer": mock_writer},
        )

        await step.execute(
            params={
                "data_type": "ohlcv",
                "write_mode": "upsert",
                "records": [
                    {
                        "ticker": "AAPL",
                        "timestamp": "2024-01-01",
                        "open": 100.0,
                        "high": 105.0,
                        "low": 99.0,
                        "close": 103.0,
                        "volume": 1000,
                        "provider": "test",
                    },
                ],
            },
            context=context,
        )

        mock_writer.write.assert_called_once()
        call_kwargs = mock_writer.write.call_args[1]
        assert call_kwargs["disposition"] == "merge"
        assert call_kwargs["key_columns"] is not None
        assert "ticker" in call_kwargs["key_columns"]


# ── AC-6: Per-table validators reject malformed data ─────────────────────


class TestAC6Validators:
    """AC-6: Per-table validators reject malformed data before write."""

    @pytest.mark.asyncio
    async def test_missing_required_field_skipped(self) -> None:
        from zorivest_core.domain.pipeline import StepContext
        from zorivest_core.pipeline_steps.market_data_store_step import (
            MarketDataStoreStep,
        )

        step = MarketDataStoreStep()
        mock_writer = MagicMock()
        mock_writer.write.return_value = 0

        context = StepContext(
            run_id="test-run",
            policy_id="test-policy",
            outputs={"db_writer": mock_writer},
        )

        result = await step.execute(
            params={
                "data_type": "ohlcv",
                "write_mode": "insert",
                "records": [
                    # Missing required 'ticker' field
                    {
                        "timestamp": "2024-01-01",
                        "open": 100.0,
                        "high": 105.0,
                        "low": 99.0,
                        "close": 103.0,
                        "volume": 1000,
                        "provider": "test",
                    },
                ],
            },
            context=context,
        )

        # Invalid records should be filtered out → 0 records written
        # Either write not called, or called with empty list
        if mock_writer.write.called:
            call_kwargs = mock_writer.write.call_args[1]
            _ = call_kwargs.get("df", None)
            # Records should be filtered to empty
        assert result.output.get("skipped", 0) >= 1


# ── AC-7: batch_size controls commit frequency ───────────────────────────


class TestAC7BatchSize:
    """AC-7: batch_size controls write commit frequency."""

    def test_batch_size_validation(self) -> None:
        from zorivest_core.pipeline_steps.market_data_store_step import (
            MarketDataStoreConfig,
        )

        config = MarketDataStoreConfig(data_type="ohlcv", batch_size=100)
        assert config.batch_size == 100

    def test_batch_size_min_constraint(self) -> None:
        from zorivest_core.pipeline_steps.market_data_store_step import (
            MarketDataStoreConfig,
        )

        with pytest.raises(Exception):
            MarketDataStoreConfig(data_type="ohlcv", batch_size=0)

    def test_batch_size_max_constraint(self) -> None:
        from zorivest_core.pipeline_steps.market_data_store_step import (
            MarketDataStoreConfig,
        )

        with pytest.raises(Exception):
            MarketDataStoreConfig(data_type="ohlcv", batch_size=5001)

    @pytest.mark.asyncio
    async def test_batch_size_controls_write_call_count(self) -> None:
        """Verify batch_size=2 with 5 records produces 3 write() calls."""
        from zorivest_core.domain.pipeline import StepContext
        from zorivest_core.pipeline_steps.market_data_store_step import (
            MarketDataStoreStep,
        )

        step = MarketDataStoreStep()
        mock_writer = MagicMock()
        # Each write call returns the batch size as rows written
        mock_writer.write.side_effect = [2, 2, 1]

        context = StepContext(
            run_id="test-run",
            policy_id="test-policy",
            outputs={"db_writer": mock_writer},
        )

        records = [
            {
                "ticker": "AAPL",
                "timestamp": f"2024-01-0{i + 1}",
                "open": 100.0,
                "high": 105.0,
                "low": 99.0,
                "close": 103.0,
                "volume": 1000,
                "provider": "test",
            }
            for i in range(5)
        ]

        result = await step.execute(
            params={
                "data_type": "ohlcv",
                "write_mode": "insert",
                "batch_size": 2,
                "records": records,
            },
            context=context,
        )

        assert mock_writer.write.call_count == 3, (
            f"Expected 3 write() calls for 5 records with batch_size=2, "
            f"got {mock_writer.write.call_count}"
        )
        assert result.output["records_written"] == 5
        assert result.output["batch_count"] == 3


# ── AC-8: Extra fields in config rejected ─────────────────────────────────


class TestAC8ExtraFields:
    """AC-8: Extra fields in config rejected."""

    def test_extra_field_rejected(self) -> None:
        from zorivest_core.pipeline_steps.market_data_store_step import (
            MarketDataStoreConfig,
        )

        with pytest.raises(Exception):
            MarketDataStoreConfig(
                data_type="ohlcv",
                extra_field="should_not_exist",  # type: ignore[call-arg]
            )

    def test_write_mode_default(self) -> None:
        from zorivest_core.pipeline_steps.market_data_store_step import (
            MarketDataStoreConfig,
        )

        config = MarketDataStoreConfig(data_type="ohlcv")
        assert config.write_mode == "insert"

    def test_write_mode_validates_enum(self) -> None:
        from zorivest_core.pipeline_steps.market_data_store_step import (
            MarketDataStoreConfig,
        )

        with pytest.raises(Exception):
            MarketDataStoreConfig(data_type="ohlcv", write_mode="truncate")  # type: ignore[arg-type]


# ── F1-FIX: source_step_id resolves records from context ────────────────


class TestSourceStepIdResolution:
    """Finding 1 fix: MarketDataStoreStep resolves records from prior step output."""

    def test_config_accepts_source_step_id(self) -> None:
        """MarketDataStoreConfig accepts source_step_id field."""
        from zorivest_core.pipeline_steps.market_data_store_step import (
            MarketDataStoreConfig,
        )

        config = MarketDataStoreConfig(
            data_type="ohlcv",
            source_step_id="fetch_ohlcv",
        )
        assert config.source_step_id == "fetch_ohlcv"

    def test_config_source_step_id_defaults_none(self) -> None:
        """source_step_id defaults to None for backward compatibility."""
        from zorivest_core.pipeline_steps.market_data_store_step import (
            MarketDataStoreConfig,
        )

        config = MarketDataStoreConfig(data_type="ohlcv")
        assert config.source_step_id is None

    @pytest.mark.asyncio
    async def test_execute_resolves_records_from_context(self) -> None:
        """When source_step_id is set and no inline records, pull from context."""
        from zorivest_core.domain.pipeline import StepContext
        from zorivest_core.pipeline_steps.market_data_store_step import (
            MarketDataStoreStep,
        )

        step = MarketDataStoreStep()
        mock_writer = MagicMock()
        mock_writer.write.return_value = 2

        # Simulate prior fetch step output in context
        fetch_output = {
            "records": [
                {
                    "ticker": "AAPL",
                    "timestamp": "2024-01-01",
                    "open": 100.0,
                    "high": 105.0,
                    "low": 99.0,
                    "close": 103.0,
                    "volume": 1000,
                    "provider": "test",
                },
                {
                    "ticker": "AAPL",
                    "timestamp": "2024-01-02",
                    "open": 103.0,
                    "high": 107.0,
                    "low": 102.0,
                    "close": 106.0,
                    "volume": 1200,
                    "provider": "test",
                },
            ],
            "content": "...",
        }

        context = StepContext(
            run_id="test-run",
            policy_id="test-policy",
            outputs={
                "db_writer": mock_writer,
                "fetch_ohlcv": fetch_output,
            },
        )

        result = await step.execute(
            params={
                "data_type": "ohlcv",
                "write_mode": "upsert",
                "source_step_id": "fetch_ohlcv",
            },
            context=context,
        )

        # Records should have been pulled from context
        mock_writer.write.assert_called_once()
        assert result.output["records_written"] == 2

    @pytest.mark.asyncio
    async def test_inline_records_override_source_step_id(self) -> None:
        """If inline records are provided, they take priority over source_step_id."""
        from zorivest_core.domain.pipeline import StepContext
        from zorivest_core.pipeline_steps.market_data_store_step import (
            MarketDataStoreStep,
        )

        step = MarketDataStoreStep()
        mock_writer = MagicMock()
        mock_writer.write.return_value = 1

        context = StepContext(
            run_id="test-run",
            policy_id="test-policy",
            outputs={
                "db_writer": mock_writer,
                "fetch_ohlcv": {"records": [{"a": 1}, {"b": 2}]},
            },
        )

        result = await step.execute(
            params={
                "data_type": "ohlcv",
                "write_mode": "insert",
                "source_step_id": "fetch_ohlcv",
                "records": [
                    {
                        "ticker": "MSFT",
                        "timestamp": "2024-01-01",
                        "open": 200.0,
                        "high": 205.0,
                        "low": 199.0,
                        "close": 203.0,
                        "volume": 800,
                        "provider": "test",
                    },
                ],
            },
            context=context,
        )

        # Inline records should be used, not context records
        mock_writer.write.assert_called_once()
        assert result.output["records_written"] == 1
