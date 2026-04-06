# tests/unit/test_account_service.py
"""Tests for AccountService (MEU-12, AC-12.7, AC-12.8)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from zorivest_core.application.commands import CreateAccount, UpdateBalance
from zorivest_core.domain.entities import Account, BalanceSnapshot
from zorivest_core.domain.enums import AccountType
from zorivest_core.domain.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
)
from zorivest_core.services.account_service import AccountService


def _make_uow() -> MagicMock:
    uow = MagicMock()
    uow.__enter__ = MagicMock(return_value=uow)
    uow.__exit__ = MagicMock(return_value=False)
    return uow


class TestCreateAccount:
    """AC-12.7."""

    def test_create_account(self) -> None:
        """AC-12.7: create_account persists via UoW."""
        uow = _make_uow()
        svc = AccountService(uow)

        cmd = CreateAccount(
            account_id="ACC001",
            name="Main Brokerage",
            account_type=AccountType.BROKER,
        )
        result = svc.create_account(cmd)

        assert result.account_id == "ACC001"
        assert result.name == "Main Brokerage"
        uow.accounts.save.assert_called_once()
        uow.commit.assert_called_once()


class TestAddBalanceSnapshot:
    """AC-12.8."""

    def test_add_snapshot_success(self) -> None:
        account = Account(
            account_id="ACC001",
            name="Test",
            account_type=AccountType.BROKER,
        )
        uow = _make_uow()
        uow.accounts.get.return_value = account

        svc = AccountService(uow)
        cmd = UpdateBalance(
            account_id="ACC001",
            balance=Decimal("50000.00"),
            snapshot_datetime=datetime(2025, 1, 15),
        )
        result = svc.add_balance_snapshot(cmd)

        assert result.account_id == "ACC001"
        assert result.balance == Decimal("50000.00")
        uow.balance_snapshots.save.assert_called_once()
        uow.commit.assert_called_once()

    def test_add_snapshot_unknown_account(self) -> None:
        """AC-12.8: raises NotFoundError for unknown account."""
        uow = _make_uow()
        uow.accounts.get.return_value = None

        svc = AccountService(uow)
        cmd = UpdateBalance(
            account_id="UNKNOWN",
            balance=Decimal("1000.00"),
        )
        with pytest.raises(NotFoundError, match="UNKNOWN"):
            svc.add_balance_snapshot(cmd)


# ── MEU-71: Account API Completion ──────────────────────────────────────


class TestListBalanceHistory:
    """AC-5: list_balance_history delegates to repo with limit/offset."""

    def test_list_history_delegates_to_repo(self) -> None:
        """AC-5: list_balance_history calls repo.list_for_account with pagination."""
        uow = _make_uow()
        snap1 = BalanceSnapshot(
            id=1,
            account_id="ACC001",
            datetime=datetime(2025, 1, 15),
            balance=Decimal("50000.00"),
        )
        snap2 = BalanceSnapshot(
            id=2,
            account_id="ACC001",
            datetime=datetime(2025, 2, 15),
            balance=Decimal("52000.00"),
        )
        uow.accounts.get.return_value = Account(
            account_id="ACC001",
            name="Test",
            account_type=AccountType.BROKER,
        )
        uow.balance_snapshots.list_for_account.return_value = [snap2, snap1]

        svc = AccountService(uow)
        result = svc.list_balance_history("ACC001", limit=10, offset=0)

        assert result == [snap2, snap1]
        uow.balance_snapshots.list_for_account.assert_called_once_with(
            "ACC001",
            limit=10,
            offset=0,
        )

    def test_list_history_unknown_account(self) -> None:
        """AC-5: raises NotFoundError for unknown account."""
        uow = _make_uow()
        uow.accounts.get.return_value = None

        svc = AccountService(uow)
        with pytest.raises(NotFoundError, match="MISSING"):
            svc.list_balance_history("MISSING", limit=10, offset=0)


class TestGetPortfolioTotal:
    """AC-6: get_portfolio_total returns sum of all latest balances."""

    def test_sums_latest_balances(self) -> None:
        """AC-6: returns sum of latest balances across all accounts."""
        uow = _make_uow()
        acc1 = Account(
            account_id="ACC001",
            name="One",
            account_type=AccountType.BROKER,
        )
        acc2 = Account(
            account_id="ACC002",
            name="Two",
            account_type=AccountType.BANK,
        )
        uow.accounts.list_all.return_value = [acc1, acc2]
        # get_latest returns the most recent snapshot for each account
        uow.balance_snapshots.get_latest.side_effect = [
            BalanceSnapshot(
                id=1,
                account_id="ACC001",
                datetime=datetime(2025, 2, 15),
                balance=Decimal("50000.00"),
            ),
            BalanceSnapshot(
                id=2,
                account_id="ACC002",
                datetime=datetime(2025, 2, 15),
                balance=Decimal("30000.00"),
            ),
        ]

        svc = AccountService(uow)
        total = svc.get_portfolio_total()

        assert total == Decimal("80000.00")

    def test_returns_zero_no_accounts(self) -> None:
        """AC-6: returns zero when no accounts exist."""
        uow = _make_uow()
        uow.accounts.list_all.return_value = []

        svc = AccountService(uow)
        total = svc.get_portfolio_total()

        assert total == Decimal("0")

    def test_skips_accounts_without_snapshots(self) -> None:
        """AC-6: accounts with no snapshots contribute 0 to total."""
        uow = _make_uow()
        acc1 = Account(
            account_id="ACC001",
            name="One",
            account_type=AccountType.BROKER,
        )
        uow.accounts.list_all.return_value = [acc1]
        uow.balance_snapshots.get_latest.return_value = None

        svc = AccountService(uow)
        total = svc.get_portfolio_total()

        assert total == Decimal("0")


# ── MEU-37: Account Integrity ───────────────────────────────────────────


class TestSystemAccountGuard:
    """AC-6, AC-7: System accounts cannot be mutated."""

    def test_update_system_account_raises_forbidden(self) -> None:
        """AC-6: update_account on system account raises ForbiddenError."""
        uow = _make_uow()
        system_acct = Account(
            account_id="SYSTEM_DEFAULT",
            name="System Reassignment Account",
            account_type=AccountType.BROKER,
            is_system=True,
        )
        uow.accounts.get.return_value = system_acct

        svc = AccountService(uow)
        with pytest.raises(ForbiddenError, match="SYSTEM_DEFAULT"):
            svc.update_account("SYSTEM_DEFAULT", name="Hacked")

    def test_delete_system_account_raises_forbidden(self) -> None:
        """AC-7: delete_account on system account raises ForbiddenError."""
        uow = _make_uow()
        system_acct = Account(
            account_id="SYSTEM_DEFAULT",
            name="System Reassignment Account",
            account_type=AccountType.BROKER,
            is_system=True,
        )
        uow.accounts.get.return_value = system_acct

        svc = AccountService(uow)
        with pytest.raises(ForbiddenError, match="SYSTEM_DEFAULT"):
            svc.delete_account("SYSTEM_DEFAULT")

    def test_archive_system_account_raises_forbidden(self) -> None:
        """AC-7: archive_account on system account raises ForbiddenError."""
        uow = _make_uow()
        system_acct = Account(
            account_id="SYSTEM_DEFAULT",
            name="System Reassignment Account",
            account_type=AccountType.BROKER,
            is_system=True,
        )
        uow.accounts.get.return_value = system_acct

        svc = AccountService(uow)
        with pytest.raises(ForbiddenError, match="SYSTEM_DEFAULT"):
            svc.archive_account("SYSTEM_DEFAULT")

    def test_reassign_system_account_raises_forbidden(self) -> None:
        """AC-7: reassign_trades_and_delete on system account raises ForbiddenError."""
        uow = _make_uow()
        system_acct = Account(
            account_id="SYSTEM_DEFAULT",
            name="System Reassignment Account",
            account_type=AccountType.BROKER,
            is_system=True,
        )
        uow.accounts.get.return_value = system_acct

        svc = AccountService(uow)
        with pytest.raises(ForbiddenError, match="SYSTEM_DEFAULT"):
            svc.reassign_trades_and_delete("SYSTEM_DEFAULT")


class TestDeleteAccountBlockOnly:
    """AC-8, AC-9: Block-only deletion semantics."""

    def test_delete_with_trades_raises_conflict(self) -> None:
        """AC-8: delete_account rejects when trades exist."""
        uow = _make_uow()
        account = Account(
            account_id="ACC001",
            name="Test",
            account_type=AccountType.BROKER,
        )
        uow.accounts.get.return_value = account
        uow.trades.list_for_account.return_value = [MagicMock()]  # 1 trade
        uow.trade_plans.count_for_account.return_value = 0

        svc = AccountService(uow)
        with pytest.raises(ConflictError, match="1 trade"):
            svc.delete_account("ACC001")
        uow.accounts.delete.assert_not_called()

    def test_delete_without_trades_succeeds(self) -> None:
        """AC-9: delete_account succeeds when no trades exist."""
        uow = _make_uow()
        account = Account(
            account_id="ACC001",
            name="Test",
            account_type=AccountType.BROKER,
        )
        uow.accounts.get.return_value = account
        uow.trades.list_for_account.return_value = []
        uow.trade_plans.count_for_account.return_value = 0

        svc = AccountService(uow)
        svc.delete_account("ACC001")
        uow.accounts.delete.assert_called_once_with("ACC001")
        uow.commit.assert_called_once()

    def test_delete_unknown_account_raises_not_found(self) -> None:
        """delete_account on missing ID raises NotFoundError."""
        uow = _make_uow()
        uow.accounts.get.return_value = None

        svc = AccountService(uow)
        with pytest.raises(NotFoundError, match="MISSING"):
            svc.delete_account("MISSING")


class TestArchiveAccount:
    """AC-10: Soft-delete sets is_archived=True."""

    def test_archive_sets_is_archived(self) -> None:
        """AC-10: archive_account sets is_archived=True and commits."""
        uow = _make_uow()
        account = Account(
            account_id="ACC001",
            name="Test",
            account_type=AccountType.BROKER,
        )
        uow.accounts.get.return_value = account

        svc = AccountService(uow)
        svc.archive_account("ACC001")

        uow.accounts.update.assert_called_once()
        updated = uow.accounts.update.call_args[0][0]
        assert updated.is_archived is True
        uow.commit.assert_called_once()

    def test_archive_unknown_raises_not_found(self) -> None:
        """archive_account on missing ID raises NotFoundError."""
        uow = _make_uow()
        uow.accounts.get.return_value = None

        svc = AccountService(uow)
        with pytest.raises(NotFoundError, match="MISSING"):
            svc.archive_account("MISSING")


class TestReassignTradesAndDelete:
    """AC-11: Move trades to SYSTEM_DEFAULT then hard-delete."""

    def test_reassign_moves_trades_and_deletes(self) -> None:
        """AC-11: reassign_trades_and_delete moves trades, hard-deletes, returns count."""
        uow = _make_uow()
        account = Account(
            account_id="ACC001",
            name="Test",
            account_type=AccountType.BROKER,
        )
        uow.accounts.get.return_value = account
        uow.accounts.reassign_trades_to.return_value = 5

        svc = AccountService(uow)
        count = svc.reassign_trades_and_delete("ACC001")

        assert count == 5
        uow.accounts.reassign_trades_to.assert_called_once_with(
            source_id="ACC001",
            target_id="SYSTEM_DEFAULT",
        )
        uow.accounts.delete.assert_called_once_with("ACC001")
        uow.commit.assert_called_once()

    def test_reassign_unknown_raises_not_found(self) -> None:
        """reassign_trades_and_delete on missing ID raises NotFoundError."""
        uow = _make_uow()
        uow.accounts.get.return_value = None

        svc = AccountService(uow)
        with pytest.raises(NotFoundError, match="MISSING"):
            svc.reassign_trades_and_delete("MISSING")


class TestGetAccountMetrics:
    """AC-12: Computed trade-based metrics."""

    def test_metrics_with_trades(self) -> None:
        """AC-12: get_account_metrics returns computed values."""
        uow = _make_uow()
        account = Account(
            account_id="ACC001",
            name="Test",
            account_type=AccountType.BROKER,
        )
        uow.accounts.get.return_value = account

        trade1 = MagicMock()
        trade1.realized_pnl = Decimal("100.50")
        trade2 = MagicMock()
        trade2.realized_pnl = Decimal("-50.00")
        trade3 = MagicMock()
        trade3.realized_pnl = Decimal("200.00")
        uow.trades.list_for_account.return_value = [trade1, trade2, trade3]
        uow.round_trips = MagicMock()
        uow.round_trips.list_for_account.return_value = [MagicMock(), MagicMock()]

        svc = AccountService(uow)
        metrics = svc.get_account_metrics("ACC001")

        assert metrics["trade_count"] == 3
        assert metrics["round_trip_count"] == 2
        assert metrics["win_rate"] == 66.67  # 2/3 winners
        assert metrics["total_realized_pnl"] == Decimal("250.50")

    def test_metrics_with_no_trades(self) -> None:
        """AC-12: get_account_metrics returns zeroes with no trades."""
        uow = _make_uow()
        account = Account(
            account_id="ACC001",
            name="Test",
            account_type=AccountType.BROKER,
        )
        uow.accounts.get.return_value = account
        uow.trades.list_for_account.return_value = []

        svc = AccountService(uow)
        metrics = svc.get_account_metrics("ACC001")

        assert metrics["trade_count"] == 0
        assert metrics["round_trip_count"] == 0
        assert metrics["win_rate"] == 0.0
        assert metrics["total_realized_pnl"] == 0

    def test_metrics_unknown_account_raises_not_found(self) -> None:
        """get_account_metrics on missing ID raises NotFoundError."""
        uow = _make_uow()
        uow.accounts.get.return_value = None

        svc = AccountService(uow)
        with pytest.raises(NotFoundError, match="MISSING"):
            svc.get_account_metrics("MISSING")
