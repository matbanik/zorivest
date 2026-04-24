"""Unit tests for DbWriteAdapter (MEU-PW1).

AC-4: DbWriteAdapter.write() dispatches to write_append/write_replace/write_merge
      by disposition parameter. Invalid disposition raises ValueError.

Source: docs/execution/plans/2026-04-12-pipeline-runtime-wiring/implementation-plan.md
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from zorivest_infra.adapters.db_write_adapter import DbWriteAdapter


def _make_adapter(session: Any | None = None) -> DbWriteAdapter:
    """Create a DbWriteAdapter with a mock session."""
    return DbWriteAdapter(session=session or MagicMock())


class TestDbWriteAdapterDispatch:
    """AC-4: write() dispatches to correct write_dispositions function."""

    @patch("zorivest_infra.adapters.db_write_adapter.write_append")
    def test_append_disposition(self, mock_append: MagicMock) -> None:
        """'append' disposition dispatches to write_append."""
        mock_append.return_value = 3
        session = MagicMock()
        adapter = _make_adapter(session=session)

        # df must be convertible to records — use a list of dicts directly
        df_mock = MagicMock()
        df_mock.to_dict.return_value = [
            {"ticker": "AAPL", "close": 150.0},
            {"ticker": "GOOG", "close": 2800.0},
            {"ticker": "MSFT", "close": 330.0},
        ]

        result = adapter.write(df=df_mock, table="market_ohlcv", disposition="append")

        assert result == 3
        mock_append.assert_called_once_with(
            session=session,
            table_name="market_ohlcv",
            records=df_mock.to_dict.return_value,
        )

    @patch("zorivest_infra.adapters.db_write_adapter.write_replace")
    def test_replace_disposition(self, mock_replace: MagicMock) -> None:
        """'replace' disposition dispatches to write_replace."""
        mock_replace.return_value = 2
        session = MagicMock()
        adapter = _make_adapter(session=session)

        df_mock = MagicMock()
        df_mock.to_dict.return_value = [{"ticker": "AAPL", "close": 150.0}]

        result = adapter.write(df=df_mock, table="market_ohlcv", disposition="replace")

        assert result == 2
        mock_replace.assert_called_once_with(
            session=session,
            table_name="market_ohlcv",
            records=df_mock.to_dict.return_value,
        )

    @patch("zorivest_infra.adapters.db_write_adapter.write_merge")
    def test_merge_disposition(self, mock_merge: MagicMock) -> None:
        """'merge' disposition dispatches to write_merge."""
        mock_merge.return_value = 5
        session = MagicMock()
        adapter = _make_adapter(session=session)

        df_mock = MagicMock()
        df_mock.to_dict.return_value = [{"ticker": "AAPL", "close": 150.0}]

        result = adapter.write(
            df=df_mock,
            table="market_ohlcv",
            disposition="merge",
            key_columns=["ticker"],
        )

        assert result == 5
        mock_merge.assert_called_once_with(
            session=session,
            table_name="market_ohlcv",
            records=df_mock.to_dict.return_value,
            key_columns=["ticker"],
        )


class TestDbWriteAdapterNegative:
    """AC-4 negative: invalid disposition raises ValueError."""

    def test_invalid_disposition_raises_value_error(self) -> None:
        """Unknown disposition string raises ValueError."""
        adapter = _make_adapter()
        df_mock = MagicMock()
        df_mock.to_dict.return_value = [{"a": 1}]

        with pytest.raises(ValueError, match="Unknown write disposition"):
            adapter.write(df=df_mock, table="market_ohlcv", disposition="truncate")

    def test_merge_without_key_columns_raises_value_error(self) -> None:
        """'merge' disposition without key_columns raises ValueError."""
        adapter = _make_adapter()
        df_mock = MagicMock()
        df_mock.to_dict.return_value = [{"a": 1}]

        with pytest.raises(ValueError, match="key_columns required"):
            adapter.write(df=df_mock, table="market_ohlcv", disposition="merge")


class TestDbWriteAdapterInterface:
    """Verify adapter matches TransformStep._write_data() call interface."""

    def test_write_signature_matches_transform_step(self) -> None:
        """write() accepts df, table, disposition — matching TransformStep L185-188."""
        import inspect

        sig = inspect.signature(DbWriteAdapter.write)
        params = list(sig.parameters.keys())

        # Must have: self, df, table, disposition (+ optional key_columns)
        assert "df" in params
        assert "table" in params
        assert "disposition" in params


# ---------------------------------------------------------------------------
# Pandas type sanitization regression tests
# ---------------------------------------------------------------------------


class TestSanitizeValue:
    """Tests for _sanitize_value — converts pandas/numpy types to Python natives.

    Regression: production crash sqlite3.ProgrammingError:
        type 'Timestamp' is not supported
    """

    def test_none_passthrough(self) -> None:
        from zorivest_infra.adapters.db_write_adapter import _sanitize_value

        assert _sanitize_value(None) is None

    def test_python_string_passthrough(self) -> None:
        from zorivest_infra.adapters.db_write_adapter import _sanitize_value

        assert _sanitize_value("hello") == "hello"

    def test_python_int_passthrough(self) -> None:
        from zorivest_infra.adapters.db_write_adapter import _sanitize_value

        assert _sanitize_value(42) == 42

    def test_python_float_passthrough(self) -> None:
        from zorivest_infra.adapters.db_write_adapter import _sanitize_value

        result = _sanitize_value(3.14)
        assert result == 3.14

    def test_python_datetime_passthrough(self) -> None:
        from zorivest_infra.adapters.db_write_adapter import _sanitize_value

        dt = datetime(2026, 4, 21, tzinfo=timezone.utc)
        assert _sanitize_value(dt) == dt

    def test_pandas_timestamp_converted_to_datetime(self) -> None:
        """Regression test: this was the production crash."""
        pd = pytest.importorskip("pandas")
        from zorivest_infra.adapters.db_write_adapter import _sanitize_value

        ts = pd.Timestamp("2026-04-21 03:58:45.511907")
        result = _sanitize_value(ts)
        assert isinstance(result, datetime)
        assert result.year == 2026
        assert result.month == 4
        assert result.day == 21

    def test_pandas_nat_converted_to_none(self) -> None:
        pd = pytest.importorskip("pandas")
        from zorivest_infra.adapters.db_write_adapter import _sanitize_value

        result = _sanitize_value(pd.NaT)
        assert result is None

    def test_float_nan_converted_to_none(self) -> None:
        from zorivest_infra.adapters.db_write_adapter import _sanitize_value

        result = _sanitize_value(float("nan"))
        assert result is None

    def test_numpy_nan_converted_to_none(self) -> None:
        np = pytest.importorskip("numpy")
        from zorivest_infra.adapters.db_write_adapter import _sanitize_value

        result = _sanitize_value(np.nan)
        assert result is None

    def test_numpy_int64_converted_to_python_int(self) -> None:
        np = pytest.importorskip("numpy")
        from zorivest_infra.adapters.db_write_adapter import _sanitize_value

        result = _sanitize_value(np.int64(42))
        assert isinstance(result, int)
        assert result == 42

    def test_numpy_float64_converted_to_python_float(self) -> None:
        np = pytest.importorskip("numpy")
        from zorivest_infra.adapters.db_write_adapter import _sanitize_value

        result = _sanitize_value(np.float64(3.14))
        assert isinstance(result, float)
        assert abs(result - 3.14) < 1e-10


class TestSanitizeRecords:
    """Tests for _sanitize_records — batch sanitization of dict records."""

    def test_empty_records_returns_empty(self) -> None:
        from zorivest_infra.adapters.db_write_adapter import _sanitize_records

        assert _sanitize_records([]) == []

    def test_mixed_types_sanitized(self) -> None:
        """Simulates the exact production record layout that caused the crash."""
        pd = pytest.importorskip("pandas")
        np = pytest.importorskip("numpy")
        from zorivest_infra.adapters.db_write_adapter import _sanitize_records

        records = [
            {
                "ticker": "AAPL",
                "last": np.float64(273.05),
                "volume": np.int64(34667241),
                "change": 2.82,
                "change_pct": 1.0436,
                "provider": "Yahoo Finance",
                "timestamp": pd.Timestamp("2026-04-21 03:58:45.511907"),
                "bid": float("nan"),
                "ask": pd.NaT,
            }
        ]

        sanitized = _sanitize_records(records)
        assert len(sanitized) == 1
        rec = sanitized[0]

        assert rec["ticker"] == "AAPL"
        assert isinstance(rec["last"], float)
        assert isinstance(rec["volume"], int)
        assert isinstance(rec["timestamp"], datetime)
        assert rec["bid"] is None  # NaN → None
        assert rec["ask"] is None  # NaT → None

    def test_records_roundtrip_through_dataframe(self) -> None:
        """Full roundtrip: dict → DataFrame → to_dict → sanitize.

        This is the exact code path that crashed in production.
        pandas auto-detects datetime-like strings and converts them
        to pandas.Timestamp when the column is cast to datetime64.
        """
        pd = pytest.importorskip("pandas")
        from zorivest_infra.adapters.db_write_adapter import _sanitize_records

        # Input: what _enrich_records produces (ISO string timestamp)
        input_records = [
            {
                "ticker": "AAPL",
                "last": 273.05,
                "volume": 34667241,
                "change": 2.82,
                "change_pct": 1.0436,
                "provider": "Yahoo Finance",
                "timestamp": "2026-04-21T03:58:45.511907+00:00",
            }
        ]

        # Simulate the DataFrame roundtrip with explicit datetime casting
        # (pandas infers datetime64 when column values look like timestamps)
        df = pd.DataFrame(input_records)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        raw = df.to_dict(orient="records")

        # Before sanitization: timestamp is a pandas Timestamp
        assert type(raw[0]["timestamp"]).__name__ == "Timestamp"

        # After sanitization: all native Python types
        sanitized = _sanitize_records(raw)
        rec = sanitized[0]
        assert isinstance(rec["timestamp"], datetime)
        assert isinstance(rec["ticker"], str)
