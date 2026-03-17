# tests/unit/test_report_service.py
"""Unit tests for ReportService (MEU-52).

Tests written FIRST (RED) — now updated to verify context manager usage.
FIC: implementation-plan.md §ReportService
Canon: 04a-api-trades.md L126-151 (method names: create, get_for_trade, update, delete)
"""

from __future__ import annotations

from datetime import datetime
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
    uow.trade_plans = MagicMock()
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
        assert result.trade_id == "T001"
        assert result.setup_quality == 4
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
        # Value: verify get_for_trade was called with correct trade_id
        uow.trade_reports.get_for_trade.assert_called_once_with("T001")

    def test_delete_raises_if_no_report(self) -> None:
        from zorivest_core.services.report_service import ReportService

        uow = _make_uow()
        uow.trade_reports.get_for_trade.return_value = None

        svc = ReportService(uow)
        with pytest.raises(ValueError, match="not found"):
            svc.delete("T001")


# ── MEU-66: TradePlan service methods ───────────────────────────────────


def _plan_data() -> dict:
    """Minimal valid plan creation payload."""
    return {
        "ticker": "AAPL",
        "direction": "BOT",
        "conviction": "high",
        "strategy_name": "Gap & Go",
        "strategy_description": "Long after gap up",
        "entry_price": 200.0,
        "stop_loss": 195.0,
        "target_price": 215.0,
        "entry_conditions": "Gap > 2%",
        "exit_conditions": "Target hit or EOD",
        "timeframe": "intraday",
    }


class TestPlanServiceCreate:
    """FIC-66 AC-3: create_plan() persists a TradePlan."""

    def test_create_plan_saves_and_returns(self) -> None:
        from zorivest_core.domain.entities import TradePlan
        from zorivest_core.services.report_service import ReportService

        uow = _make_uow()
        uow.trade_plans.get.return_value = TradePlan(
            id=1, ticker="AAPL", direction="BOT", conviction="high",
            strategy_name="Gap & Go", strategy_description="Long after gap up",
            entry_price=200.0, stop_loss=195.0, target_price=215.0,
            entry_conditions="Gap > 2%", exit_conditions="Target hit or EOD",
            timeframe="intraday", risk_reward_ratio=3.0, status="draft",
            created_at=datetime(2026, 3, 12), updated_at=datetime(2026, 3, 12),
        )

        svc = ReportService(uow)
        result = svc.create_plan(_plan_data())

        assert isinstance(result, TradePlan)
        assert result.ticker == "AAPL"
        assert result.direction == "BOT"
        assert result.strategy_name == "Gap & Go"
        uow.trade_plans.save.assert_called_once()
        uow.commit.assert_called_once()
        uow.__enter__.assert_called_once()


class TestPlanServiceGet:
    """FIC-66 AC-4: get_plan() returns plan by ID or None."""

    def test_get_plan_returns_plan(self) -> None:
        from zorivest_core.domain.entities import TradePlan
        from zorivest_core.services.report_service import ReportService

        uow = _make_uow()
        expected = TradePlan(
            id=1, ticker="SPY", direction="SLD", conviction="medium",
            strategy_name="Breakdown", strategy_description="Short below support",
            entry_price=600.0, stop_loss=605.0, target_price=585.0,
            entry_conditions="Break below VWAP", exit_conditions="Cover at target",
            timeframe="intraday", risk_reward_ratio=3.0, status="active",
            created_at=datetime(2026, 3, 12), updated_at=datetime(2026, 3, 12),
        )
        uow.trade_plans.get.return_value = expected

        svc = ReportService(uow)
        result = svc.get_plan(1)
        assert result == expected
        assert result.ticker == "SPY"
        assert result.direction == "SLD"
        assert result.status == "active"
        uow.__enter__.assert_called_once()

    def test_get_plan_returns_none(self) -> None:
        from zorivest_core.services.report_service import ReportService

        uow = _make_uow()
        uow.trade_plans.get.return_value = None

        svc = ReportService(uow)
        result = svc.get_plan(999)
        assert result is None


class TestPlanServiceList:
    """FIC-66: list_plans() returns paginated plan list."""

    def test_list_plans_returns_list(self) -> None:
        from zorivest_core.services.report_service import ReportService

        uow = _make_uow()
        uow.trade_plans.list_all.return_value = []

        svc = ReportService(uow)
        result = svc.list_plans(limit=10, offset=0)
        assert result == []
        uow.trade_plans.list_all.assert_called_once_with(limit=10, offset=0)
        uow.__enter__.assert_called_once()


class TestPlanServiceUpdate:
    """FIC-66: update_plan() merges changes to existing plan."""

    def test_update_plan_merges_changes(self) -> None:
        from zorivest_core.domain.entities import TradePlan
        from zorivest_core.services.report_service import ReportService

        uow = _make_uow()
        existing = TradePlan(
            id=1, ticker="AAPL", direction="BOT", conviction="high",
            strategy_name="Gap & Go", strategy_description="Long gap",
            entry_price=200.0, stop_loss=195.0, target_price=215.0,
            entry_conditions="Gap > 2%", exit_conditions="Target or EOD",
            timeframe="intraday", risk_reward_ratio=3.0, status="draft",
            created_at=datetime(2026, 3, 12), updated_at=datetime(2026, 3, 12),
        )
        uow.trade_plans.get.return_value = existing

        svc = ReportService(uow)
        result = svc.update_plan(1, {"status": "active", "conviction": "max"})

        assert result.status == "active"
        assert result.conviction == "max"
        uow.trade_plans.update.assert_called_once()
        uow.commit.assert_called_once()

    def test_update_plan_raises_if_not_found(self) -> None:
        from zorivest_core.services.report_service import ReportService

        uow = _make_uow()
        uow.trade_plans.get.return_value = None

        svc = ReportService(uow)
        with pytest.raises(ValueError, match="not found"):
            svc.update_plan(999, {"status": "active"})


# ── MEU-67: TradePlan ↔ Trade Linking ───────────────────────────────────


class TestPlanServiceLink:
    """FIC-67: link_plan_to_trade() sets linked_trade_id and status→executed."""

    def test_link_plan_to_trade_happy_path(self) -> None:
        from zorivest_core.domain.entities import TradePlan
        from zorivest_core.services.report_service import ReportService

        uow = _make_uow()
        existing = TradePlan(
            id=1, ticker="AAPL", direction="BOT", conviction="high",
            strategy_name="Gap & Go", strategy_description="Long gap",
            entry_price=200.0, stop_loss=195.0, target_price=215.0,
            entry_conditions="Gap > 2%", exit_conditions="Target or EOD",
            timeframe="intraday", risk_reward_ratio=3.0, status="active",
            created_at=datetime(2026, 3, 12), updated_at=datetime(2026, 3, 12),
        )
        uow.trade_plans.get.return_value = existing
        uow.trades.get.return_value = MagicMock(exec_id="T001")

        svc = ReportService(uow)
        result = svc.link_plan_to_trade(1, "T001")

        assert result.linked_trade_id == "T001"
        assert result.status == "executed"
        uow.trade_plans.update.assert_called_once()
        uow.commit.assert_called_once()

    def test_link_plan_not_found(self) -> None:
        from zorivest_core.services.report_service import ReportService

        uow = _make_uow()
        uow.trade_plans.get.return_value = None

        svc = ReportService(uow)
        with pytest.raises(ValueError, match="Plan .* not found"):
            svc.link_plan_to_trade(999, "T001")

    def test_link_trade_not_found(self) -> None:
        from zorivest_core.domain.entities import TradePlan
        from zorivest_core.services.report_service import ReportService

        uow = _make_uow()
        uow.trade_plans.get.return_value = TradePlan(
            id=1, ticker="AAPL", direction="BOT", conviction="high",
            strategy_name="Gap & Go", strategy_description="Long gap",
            entry_price=200.0, stop_loss=195.0, target_price=215.0,
            entry_conditions="Gap > 2%", exit_conditions="Target or EOD",
            timeframe="intraday", risk_reward_ratio=3.0, status="active",
            created_at=datetime(2026, 3, 12), updated_at=datetime(2026, 3, 12),
        )
        uow.trades.get.return_value = None

        svc = ReportService(uow)
        with pytest.raises(ValueError, match="Trade .* not found"):
            svc.link_plan_to_trade(1, "T999")


class TestPlanServiceDedup:
    """F3: create_plan rejects duplicate active plans."""

    def test_create_plan_duplicate_raises(self) -> None:
        from zorivest_core.domain.entities import TradePlan
        from zorivest_core.services.report_service import ReportService

        uow = _make_uow()
        # Simulate an existing active plan for AAPL/BOT
        existing = TradePlan(
            id=1, ticker="AAPL", direction="BOT", conviction="high",
            strategy_name="Gap & Go", strategy_description="Long gap",
            entry_price=200.0, stop_loss=195.0, target_price=215.0,
            entry_conditions="Gap > 2%", exit_conditions="EOD",
            timeframe="intraday", risk_reward_ratio=3.0, status="active",
            created_at=datetime(2026, 3, 12), updated_at=datetime(2026, 3, 12),
        )
        uow.trade_plans.list_all.return_value = [existing]

        svc = ReportService(uow)
        with pytest.raises(ValueError, match="Duplicate active plan"):
            svc.create_plan({
                "ticker": "AAPL",
                "direction": "BOT",
                "strategy_name": "Gap & Go",
                "entry_price": 200.0,
                "stop_loss": 195.0,
                "target_price": 215.0,
            })


class TestPlanServiceDelete:
    """delete_plan removes plan or raises ValueError."""

    def test_delete_plan_success(self) -> None:
        from zorivest_core.domain.entities import TradePlan
        from zorivest_core.services.report_service import ReportService

        uow = _make_uow()
        uow.trade_plans.get.return_value = TradePlan(
            id=1, ticker="AAPL", direction="BOT", conviction="high",
            strategy_name="Gap & Go", strategy_description="Long gap",
            entry_price=200.0, stop_loss=195.0, target_price=215.0,
            entry_conditions="Gap > 2%", exit_conditions="EOD",
            timeframe="intraday", risk_reward_ratio=3.0, status="draft",
            created_at=datetime(2026, 3, 12), updated_at=datetime(2026, 3, 12),
        )
        svc = ReportService(uow)
        svc.delete_plan(1)
        uow.trade_plans.delete.assert_called_once_with(1)
        uow.commit.assert_called_once()
        # Value: verify get was called with correct plan_id
        uow.trade_plans.get.assert_called_once_with(1)

    def test_delete_plan_not_found(self) -> None:
        from zorivest_core.services.report_service import ReportService

        uow = _make_uow()
        uow.trade_plans.get.return_value = None

        svc = ReportService(uow)
        with pytest.raises(ValueError, match="Plan 999 not found"):
            svc.delete_plan(999)
