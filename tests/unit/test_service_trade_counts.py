# tests/unit/test_service_trade_counts.py
"""Tests for AccountService.get_trade_counts — batch trade count query.

Red phase — written FIRST per TDD protocol.
Covers: get_trade_counts service method used by the two-stage account
deletion workflow (TradeWarningModal).
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock


from zorivest_core.domain.entities import Account, Trade
from zorivest_core.domain.enums import AccountType, TradeAction
from zorivest_core.services.account_service import AccountService


def _make_uow() -> MagicMock:
    """Create a mock UoW with standard context-manager support."""
    uow = MagicMock()
    uow.__enter__ = MagicMock(return_value=uow)
    uow.__exit__ = MagicMock(return_value=False)
    return uow


def _sample_trade(exec_id: str = "E001", account_id: str = "ACC001") -> Trade:
    return Trade(
        exec_id=exec_id,
        time=datetime(2025, 1, 15, 10, 30),
        instrument="AAPL",
        action=TradeAction.BOT,
        quantity=100.0,
        price=150.50,
        account_id=account_id,
    )


def _sample_account(account_id: str = "ACC001", **overrides: object) -> Account:
    defaults = {
        "account_id": account_id,
        "name": "Main Brokerage",
        "account_type": AccountType.BROKER,
    }
    defaults.update(overrides)
    return Account(**defaults)  # type: ignore[arg-type]


# ── get_trade_counts ────────────────────────────────────────────────────


class TestGetTradeCounts:
    """AccountService.get_trade_counts — batch trade/plan count query."""

    def test_single_account_with_trades(self) -> None:
        """Returns correct trade_count and plan_count for one account."""
        uow = _make_uow()
        uow.trades.list_for_account.return_value = [
            _sample_trade("E001"),
            _sample_trade("E002"),
        ]
        uow.trade_plans.count_for_account.return_value = 1

        svc = AccountService(uow)
        result = svc.get_trade_counts(["ACC001"])

        assert result == {
            "ACC001": {"trade_count": 2, "plan_count": 1},
        }
        uow.trades.list_for_account.assert_called_once_with("ACC001")
        uow.trade_plans.count_for_account.assert_called_once_with("ACC001")

    def test_single_account_no_trades(self) -> None:
        """Returns zero counts when account has no trades or plans."""
        uow = _make_uow()
        uow.trades.list_for_account.return_value = []
        uow.trade_plans.count_for_account.return_value = 0

        svc = AccountService(uow)
        result = svc.get_trade_counts(["ACC001"])

        assert result == {
            "ACC001": {"trade_count": 0, "plan_count": 0},
        }

    def test_multiple_accounts_mixed(self) -> None:
        """Returns correct counts for multiple accounts with mixed trade states."""
        uow = _make_uow()

        # ACC001 has 3 trades, 0 plans
        # ACC002 has 0 trades, 2 plans
        # ACC003 has 0 trades, 0 plans
        def mock_trades(account_id: str):
            if account_id == "ACC001":
                return [
                    _sample_trade("E001", "ACC001"),
                    _sample_trade("E002", "ACC001"),
                    _sample_trade("E003", "ACC001"),
                ]
            return []

        def mock_plans(account_id: str):
            if account_id == "ACC002":
                return 2
            return 0

        uow.trades.list_for_account.side_effect = mock_trades
        uow.trade_plans.count_for_account.side_effect = mock_plans

        svc = AccountService(uow)
        result = svc.get_trade_counts(["ACC001", "ACC002", "ACC003"])

        assert result == {
            "ACC001": {"trade_count": 3, "plan_count": 0},
            "ACC002": {"trade_count": 0, "plan_count": 2},
            "ACC003": {"trade_count": 0, "plan_count": 0},
        }

    def test_none_trades_treated_as_zero(self) -> None:
        """Handles repo returning None instead of empty list."""
        uow = _make_uow()
        uow.trades.list_for_account.return_value = None
        uow.trade_plans.count_for_account.return_value = None

        svc = AccountService(uow)
        result = svc.get_trade_counts(["ACC001"])

        assert result == {
            "ACC001": {"trade_count": 0, "plan_count": 0},
        }

    def test_empty_account_ids_returns_empty(self) -> None:
        """Returns empty dict when no account IDs provided."""
        uow = _make_uow()

        svc = AccountService(uow)
        result = svc.get_trade_counts([])

        assert result == {}
        uow.trades.list_for_account.assert_not_called()
        uow.trade_plans.count_for_account.assert_not_called()

    def test_uow_context_manager_used(self) -> None:
        """Verifies UoW context manager is entered for session management."""
        uow = _make_uow()
        uow.trades.list_for_account.return_value = []
        uow.trade_plans.count_for_account.return_value = 0

        svc = AccountService(uow)
        svc.get_trade_counts(["ACC001"])

        uow.__enter__.assert_called_once()
