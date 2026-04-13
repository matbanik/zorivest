"""Unit tests for DbWriteAdapter (MEU-PW1).

AC-4: DbWriteAdapter.write() dispatches to write_append/write_replace/write_merge
      by disposition parameter. Invalid disposition raises ValueError.

Source: docs/execution/plans/2026-04-12-pipeline-runtime-wiring/implementation-plan.md
"""

from __future__ import annotations

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
