# tests/unit/test_report_service.py
"""Unit tests for ReportService (MEU-52).

Tests written FIRST (RED) — now updated to verify context manager usage.
FIC: implementation-plan.md §ReportService
Canon: 04a-api-trades.md L126-151 (method names: create, get_for_trade, update, delete)
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from unittest.mock import MagicMock

import pytest

from zorivest_core.domain.entities import TradeReport

pytestmark = pytest.mark.unit


# ── Stub UoW for isolation ──────────────────────────────────────────────


def _make_uow() -> MagicMock:
    """Return a mock UoW with trade_reports and trades repos + context manager."""
    uow = MagicMock()
    uow.__enter__ = MagicMock(return_value=uow)
    uow.__exit__ = MagicMock(return_value=False)
    uow.trade_reports = MagicMock()
    uow.trades = MagicMock()
    return uow


def _report_data() -> dict:
    """Minimal valid report creation payload."""
    return {
        "setup_quality": 4,
        "execution_quality": 3,
        "followed_plan": True,
        "emotional_state": "confident",
        "lessons_learned": "Good timing",
        "tags": ["spy", "options"],
    }


# ── Tests ───────────────────────────────────────────────────────────────


class TestReportServiceCreate:
    """FIC-52 AC-5: create() persists a TradeReport."""

    def test_create_saves_report(self) -> None:
        from zorivest_core.services.report_service import ReportService

        uow = _make_uow()
        # Simulate trade exists
        uow.trades.get.return_value = MagicMock(exec_id="T001")
        uow.trade_reports.get_for_trade.side_effect = [None, TradeReport(
            id=42, trade_id="T001", setup_quality=4,
            execution_quality=3, followed_plan=True,
            emotional_state="confident",
            created_at=datetime(2025, 7, 15),
            lessons_learned="Good timing",
            tags=["spy", "options"],
        )]

        svc = ReportService(uow)
        result = svc.create("T001", _report_data())

        assert isinstance(result, TradeReport)
        assert result.trade_id == "T001"
        assert result.id == 42  # Hydrated ID
        uow.trade_reports.save.assert_called_once()
        uow.commit.assert_called_once()
        uow.__enter__.assert_called_once()

    def test_create_raises_if_trade_not_found(self) -> None:
        from zorivest_core.services.report_service import ReportService

        uow = _make_uow()
        uow.trades.get.return_value = None

        svc = ReportService(uow)
        with pytest.raises(ValueError, match="Trade.*not found"):
            svc.create("MISSING", _report_data())

    def test_create_raises_if_report_already_exists(self) -> None:
        from zorivest_core.services.report_service import ReportService

        uow = _make_uow()
        uow.trades.get.return_value = MagicMock(exec_id="T001")
        uow.trade_reports.get_for_trade.return_value = MagicMock()

        svc = ReportService(uow)
        with pytest.raises(ValueError, match="already exists"):
            svc.create("T001", _report_data())


class TestReportServiceGetForTrade:
    """FIC-52 AC-6: get_for_trade() returns report or None."""

    def test_get_for_trade_returns_report(self) -> None:
        from zorivest_core.services.report_service import ReportService

        uow = _make_uow()
        expected = TradeReport(
            id=1, trade_id="T001", setup_quality=4,
            execution_quality=3, followed_plan=True,
            emotional_state="neutral",
            created_at=datetime(2025, 7, 15),
        )
        uow.trade_reports.get_for_trade.return_value = expected

        svc = ReportService(uow)
        result = svc.get_for_trade("T001")
        assert result == expected
        uow.__enter__.assert_called_once()

    def test_get_for_trade_returns_none(self) -> None:
        from zorivest_core.services.report_service import ReportService

        uow = _make_uow()
        uow.trade_reports.get_for_trade.return_value = None

        svc = ReportService(uow)
        result = svc.get_for_trade("T001")
        assert result is None


class TestReportServiceUpdate:
    """FIC-52 AC-7: update() modifies existing report."""

    def test_update_merges_changes(self) -> None:
        from zorivest_core.services.report_service import ReportService

        uow = _make_uow()
        existing = TradeReport(
            id=1, trade_id="T001", setup_quality=3,
            execution_quality=3, followed_plan=False,
            emotional_state="anxious",
            created_at=datetime(2025, 7, 15),
        )
        uow.trade_reports.get_for_trade.return_value = existing

        svc = ReportService(uow)
        result = svc.update("T001", {"setup_quality": 5, "lessons_learned": "Better"})

        assert result is not None
        assert result.setup_quality == 5
        assert result.lessons_learned == "Better"
        uow.trade_reports.update.assert_called_once()
        uow.commit.assert_called_once()
        uow.__enter__.assert_called_once()

    def test_update_raises_if_no_report(self) -> None:
        from zorivest_core.services.report_service import ReportService

        uow = _make_uow()
        uow.trade_reports.get_for_trade.return_value = None

        svc = ReportService(uow)
        with pytest.raises(ValueError, match="not found"):
            svc.update("T001", {"setup_quality": 5})


class TestReportServiceDelete:
    """FIC-52: delete() removes report."""

    def test_delete_removes_report(self) -> None:
        from zorivest_core.services.report_service import ReportService

        uow = _make_uow()
        existing = TradeReport(
            id=42, trade_id="T001", setup_quality=3,
            execution_quality=3, followed_plan=True,
            emotional_state="neutral",
            created_at=datetime(2025, 7, 15),
        )
        uow.trade_reports.get_for_trade.return_value = existing

        svc = ReportService(uow)
        svc.delete("T001")

        uow.trade_reports.delete.assert_called_once_with(42)
        uow.commit.assert_called_once()
        uow.__enter__.assert_called_once()

    def test_delete_raises_if_no_report(self) -> None:
        from zorivest_core.services.report_service import ReportService

        uow = _make_uow()
        uow.trade_reports.get_for_trade.return_value = None

        svc = ReportService(uow)
        with pytest.raises(ValueError, match="not found"):
            svc.delete("T001")
