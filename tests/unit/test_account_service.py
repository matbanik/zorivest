# tests/unit/test_account_service.py
"""Tests for AccountService (MEU-12, AC-12.7, AC-12.8)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from zorivest_core.application.commands import CreateAccount, UpdateBalance
from zorivest_core.domain.entities import Account
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
