# tests/unit/test_transform_step.py
"""TDD Red-phase tests for TransformStep (MEU-86).

Acceptance criteria AC-T1..AC-T13 per implementation-plan §9.5.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pandas as pd
import pytest
from pydantic import ValidationError


# ---------------------------------------------------------------------------
# AC-T1: TransformStep auto-registers with type_name="transform"
# ---------------------------------------------------------------------------


def test_AC_T1_transform_step_auto_registers():
    """TransformStep auto-registers in STEP_REGISTRY with type_name='transform'."""
    from zorivest_core.domain.step_registry import STEP_REGISTRY, get_step

    # Import pipeline_steps to trigger eager imports
    import zorivest_core.pipeline_steps  # noqa: F401

    from zorivest_core.pipeline_steps.transform_step import TransformStep

    assert "transform" in STEP_REGISTRY
    assert get_step("transform") is TransformStep


# ---------------------------------------------------------------------------
# AC-T2: TransformStep Params validates required target_table
# ---------------------------------------------------------------------------


def test_AC_T2_params_validates_required_target_table():
    """TransformStep.Params rejects missing target_table."""
    from zorivest_core.pipeline_steps.transform_step import TransformStep

    # Should succeed with required field
    p = TransformStep.Params(target_table="market_ohlcv")
    assert p.target_table == "market_ohlcv"

    # Should fail without target_table
    with pytest.raises(ValidationError):
        TransformStep.Params()


# ---------------------------------------------------------------------------
# AC-T3: apply_field_mapping() maps known fields + captures extras
# ---------------------------------------------------------------------------


def test_AC_T3_field_mapping_with_extras():
    """apply_field_mapping maps known fields and captures unmapped in _extra."""
    from zorivest_infra.market_data.field_mappings import apply_field_mapping

    source_record = {
        "o": 100.0,
        "h": 105.0,
        "l": 99.0,
        "c": 103.0,
        "v": 1000000,
        "unknown_field": "extra_value",
    }

    result = apply_field_mapping(
        record=source_record,
        provider="generic",
        data_type="ohlcv",
    )

    assert result["open"] == 100.0
    assert result["high"] == 105.0
    assert result["low"] == 99.0
    assert result["close"] == 103.0
    assert result["volume"] == 1000000
    assert "_extra" in result
    assert result["_extra"]["unknown_field"] == "extra_value"


# ---------------------------------------------------------------------------
# AC-T4: apply_field_mapping() returns empty dict for empty mapping
# ---------------------------------------------------------------------------


def test_AC_T4_field_mapping_empty_input():
    """apply_field_mapping returns empty dict for empty source data."""
    from zorivest_infra.market_data.field_mappings import apply_field_mapping

    result = apply_field_mapping(
        record={},
        provider="generic",
        data_type="ohlcv",
    )

    # Only _extra key with empty dict
    assert result.get("_extra") == {} or result == {"_extra": {}}


# ---------------------------------------------------------------------------
# AC-T5: validate_dataframe() passes all-valid OHLCV data
# ---------------------------------------------------------------------------


def test_AC_T5_validate_valid_ohlcv():
    """validate_dataframe passes all-valid OHLCV data through."""
    from zorivest_core.services.validation_gate import validate_dataframe

    df = pd.DataFrame({
        "open": [100.0, 101.0],
        "high": [105.0, 106.0],
        "low": [99.0, 100.0],
        "close": [103.0, 104.0],
        "volume": [1000000, 1100000],
    })

    valid, quarantined = validate_dataframe(df, schema_name="ohlcv")

    assert len(valid) == 2
    assert len(quarantined) == 0


# ---------------------------------------------------------------------------
# AC-T6: validate_dataframe() quarantines invalid records
# ---------------------------------------------------------------------------


def test_AC_T6_validate_quarantines_invalid():
    """validate_dataframe quarantines records with negative prices."""
    from zorivest_core.services.validation_gate import validate_dataframe

    df = pd.DataFrame({
        "open": [100.0, -5.0],    # Second row has negative open
        "high": [105.0, 106.0],
        "low": [99.0, 100.0],
        "close": [103.0, 104.0],
        "volume": [1000000, 1100000],
    })

    valid, quarantined = validate_dataframe(df, schema_name="ohlcv")

    assert len(valid) == 1
    assert len(quarantined) == 1


# ---------------------------------------------------------------------------
# AC-T7: Quality threshold < 0.8 → FAILED status
# ---------------------------------------------------------------------------


def test_AC_T7_quality_below_threshold():
    """Quality ratio below threshold returns failed quality check."""
    from zorivest_core.services.validation_gate import check_quality

    # 2 valid out of 10 total = 0.2 ratio, well below 0.8
    result = check_quality(valid_count=2, total_count=10, threshold=0.8)
    assert result["passed"] is False
    assert result["ratio"] < 0.8


def test_AC_T7_quality_above_threshold():
    """Quality ratio above threshold returns passed quality check."""
    from zorivest_core.services.validation_gate import check_quality

    # 9 valid out of 10 total = 0.9 ratio, above 0.8
    result = check_quality(valid_count=9, total_count=10, threshold=0.8)
    assert result["passed"] is True
    assert result["ratio"] >= 0.8


# ---------------------------------------------------------------------------
# AC-T8: TABLE_ALLOWLIST rejects unknown tables
# ---------------------------------------------------------------------------


def test_AC_T8_table_allowlist_rejects_unknown():
    """TABLE_ALLOWLIST rejects writes to unknown tables."""
    from zorivest_infra.repositories.write_dispositions import (
        TABLE_ALLOWLIST,
        validate_table,
    )

    # Known table should pass
    assert validate_table("market_ohlcv") is True

    # Unknown table should fail
    assert validate_table("drop_students; --") is False
    assert validate_table("nonexistent_table") is False


# ---------------------------------------------------------------------------
# AC-T9: _validate_columns rejects columns not in allowlist
# ---------------------------------------------------------------------------


def test_AC_T9_validate_columns_rejects_unknown():
    """validate_columns rejects column names not in the table's allowlist."""
    from zorivest_infra.repositories.write_dispositions import (
        validate_columns,
    )

    # Valid OHLCV columns
    assert validate_columns("market_ohlcv", ["open", "high", "low", "close", "volume"]) is True

    # Invalid column
    assert validate_columns("market_ohlcv", ["open", "DROP TABLE"]) is False


# ---------------------------------------------------------------------------
# AC-T10: to_micros() / from_micros() round-trip precision
# ---------------------------------------------------------------------------


def test_AC_T10_micros_round_trip():
    """to_micros and from_micros preserve precision in round trips."""
    from zorivest_core.domain.precision import from_micros, to_micros

    original = 123.456789
    micros = to_micros(original)
    restored = from_micros(micros)

    assert isinstance(micros, int)
    assert abs(restored - original) < 1e-6


def test_AC_T10_micros_precision_edge_cases():
    """to_micros handles edge cases like very small and very large values."""
    from zorivest_core.domain.precision import from_micros, to_micros

    # Small value
    assert from_micros(to_micros(0.000001)) == pytest.approx(0.000001, abs=1e-6)

    # Large value
    assert from_micros(to_micros(999999.999999)) == pytest.approx(999999.999999, abs=1e-6)


# ---------------------------------------------------------------------------
# AC-T11: parse_monetary() avoids float precision errors
# ---------------------------------------------------------------------------


def test_AC_T11_parse_monetary_precision():
    """parse_monetary avoids float precision errors like 0.1 + 0.2 != 0.3."""
    from zorivest_core.domain.precision import parse_monetary

    # Classic float precision issue
    result = parse_monetary("0.1") + parse_monetary("0.2")
    expected = parse_monetary("0.3")

    assert result == expected  # Decimal comparison, no float issues


# ---------------------------------------------------------------------------
# AC-T12: TransformStep side_effects=True
# ---------------------------------------------------------------------------


def test_AC_T12_transform_step_side_effects():
    """TransformStep declares side_effects=True."""
    from zorivest_core.pipeline_steps.transform_step import TransformStep

    assert TransformStep.side_effects is True


# ---------------------------------------------------------------------------
# AC-T13: Live UoW test — write_append creates rows
# ---------------------------------------------------------------------------


def test_AC_T13_live_uow_write_append():
    """write_append() with in-memory SQLite creates actual rows."""
    from sqlalchemy import Column, Integer, String, create_engine, text
    from sqlalchemy.orm import DeclarativeBase, Session

    from zorivest_infra.repositories.write_dispositions import write_append

    # Create in-memory test table
    engine = create_engine("sqlite:///:memory:")

    class TestBase(DeclarativeBase):
        pass

    class TestTable(TestBase):
        __tablename__ = "market_ohlcv"
        id = Column(Integer, primary_key=True, autoincrement=True)
        ticker = Column(String, nullable=False)
        open = Column(Integer)
        high = Column(Integer)
        low = Column(Integer)
        close = Column(Integer)
        volume = Column(Integer)

    TestBase.metadata.create_all(engine)

    with Session(engine) as session:
        records = [
            {"ticker": "AAPL", "open": 100, "high": 105, "low": 99, "close": 103, "volume": 1000000},
            {"ticker": "GOOG", "open": 200, "high": 210, "low": 198, "close": 205, "volume": 500000},
        ]

        write_append(session=session, table_name="market_ohlcv", records=records)
        session.commit()

        result = session.execute(text("SELECT COUNT(*) FROM market_ohlcv"))
        count = result.scalar()
        assert count == 2


# ---------------------------------------------------------------------------
# AC-T14: TransformStep.execute() validates records via quality gate
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_AC_T14_transform_step_execute_validates_records():
    """TransformStep.execute() processes valid OHLCV records through the
    validation→quality pipeline and reports correct records_written count."""
    import json
    from unittest.mock import MagicMock

    from zorivest_core.domain.pipeline import StepContext
    from zorivest_core.pipeline_steps.transform_step import TransformStep

    mock_writer = MagicMock()
    mock_writer.write.return_value = 2

    step = TransformStep()
    records = [
        {"open": 100.0, "high": 110.0, "low": 95.0, "close": 105.0, "volume": 1000},
        {"open": 200.0, "high": 210.0, "low": 195.0, "close": 205.0, "volume": 2000},
    ]
    context = StepContext(
        run_id="run-1",
        policy_id="pol-1",
        outputs={
            "fetch_result": {"content": json.dumps(records).encode()},
            "db_writer": mock_writer,
        },
    )

    result = await step.execute(
        params={"target_table": "market_ohlcv"},
        context=context,
    )

    assert result.status.value == "success"
    assert result.output["records_written"] == 2
    assert result.output["records_quarantined"] == 0
    assert result.output["quality_ratio"] == 1.0
    assert result.output["target_table"] == "market_ohlcv"


@pytest.mark.asyncio
async def test_AC_T14b_transform_step_execute_quality_gate_rejects():
    """TransformStep.execute() fails when quality ratio is below threshold."""
    import json

    from zorivest_core.domain.pipeline import StepContext
    from zorivest_core.pipeline_steps.transform_step import TransformStep

    step = TransformStep()
    # 1 valid + 9 invalid (negative prices) → quality 10% < 80% threshold
    records = [{"open": 100.0, "high": 110.0, "low": 95.0, "close": 105.0, "volume": 1000}]
    records += [{"open": -1.0, "high": -1.0, "low": -1.0, "close": -1.0, "volume": 0}] * 9
    context = StepContext(
        run_id="run-1",
        policy_id="pol-1",
        outputs={"fetch_result": {"content": json.dumps(records).encode()}},
    )

    result = await step.execute(
        params={"target_table": "market_ohlcv", "quality_threshold": 0.8},
        context=context,
    )

    assert result.status.value == "failed"
    assert "Quality" in result.error
    assert result.output["records_valid"] == 1
    assert result.output["records_quarantined"] == 9


# ---------------------------------------------------------------------------
# AC-T15: TransformStep._write_data() delegates to injected db_writer
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_AC_T15_transform_step_write_data_calls_db_writer():
    """When db_writer is injected via context.outputs,
    _write_data() calls writer.write() with correct args."""
    import json
    from unittest.mock import MagicMock

    from zorivest_core.domain.pipeline import StepContext
    from zorivest_core.pipeline_steps.transform_step import TransformStep

    mock_writer = MagicMock()
    mock_writer.write.return_value = 5  # Pretend 5 rows written

    step = TransformStep()
    records = [
        {"open": 100.0, "high": 110.0, "low": 95.0, "close": 105.0, "volume": 1000},
        {"open": 200.0, "high": 210.0, "low": 195.0, "close": 205.0, "volume": 2000},
    ]
    context = StepContext(
        run_id="run-1",
        policy_id="pol-1",
        outputs={
            "fetch_result": {"content": json.dumps(records).encode()},
            "db_writer": mock_writer,
        },
    )

    result = await step.execute(
        params={"target_table": "market_ohlcv", "write_disposition": "append"},
        context=context,
    )

    assert result.status.value == "success"
    # Verify writer was called
    mock_writer.write.assert_called_once()
    call_kwargs = mock_writer.write.call_args.kwargs
    assert call_kwargs["table"] == "market_ohlcv"
    assert call_kwargs["disposition"] == "append"
    # records_written should be the value returned by the writer
    assert result.output["records_written"] == 5


# ---------------------------------------------------------------------------
# AC-T16: TransformStep raises ValueError when db_writer is missing
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_AC_T16_transform_step_raises_without_writer():
    """TransformStep.execute() raises ValueError when db_writer is not
    injected via context.outputs."""
    import json

    from zorivest_core.domain.pipeline import StepContext
    from zorivest_core.pipeline_steps.transform_step import TransformStep

    step = TransformStep()
    records = [
        {"open": 100.0, "high": 110.0, "low": 95.0, "close": 105.0, "volume": 1000},
    ]
    context = StepContext(
        run_id="run-1",
        policy_id="pol-1",
        outputs={"fetch_result": {"content": json.dumps(records).encode()}},
    )

    with pytest.raises(ValueError, match="db_writer required"):
        await step.execute(
            params={"target_table": "market_ohlcv"},
            context=context,
        )
