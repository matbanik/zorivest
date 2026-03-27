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
from zorivest_core.domain.exceptions import NotFoundError
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
