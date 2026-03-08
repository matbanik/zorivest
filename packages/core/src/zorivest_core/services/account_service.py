"""AccountService — account CRUD and balance snapshots.

Source: domain-model-reference §Account
Uses: CreateAccount, UpdateBalance commands (commands.py)
"""

from __future__ import annotations

from zorivest_core.application.commands import CreateAccount, UpdateBalance
from zorivest_core.application.ports import UnitOfWork
from zorivest_core.domain.entities import Account, BalanceSnapshot
from zorivest_core.domain.exceptions import NotFoundError


class AccountService:
    """Account management: create, get, list, balance snapshots."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    def create_account(self, command: CreateAccount) -> Account:
        """Create a new financial account."""
        with self.uow:
            account = Account(
                account_id=command.account_id,
                name=command.name,
                account_type=command.account_type,
                institution=command.institution,
                currency=command.currency,
                is_tax_advantaged=command.is_tax_advantaged,
                notes=command.notes,
                balance_source=command.balance_source,
            )
            self.uow.accounts.save(account)
            self.uow.commit()
            return account

    def get_account(self, account_id: str) -> Account:
        """Retrieve an account by ID.

        Raises:
            NotFoundError: If account does not exist.
        """
        with self.uow:
            account = self.uow.accounts.get(account_id)
            if account is None:
                raise NotFoundError(f"Account not found: {account_id}")
            return account

    def list_accounts(self, limit: int = 100, offset: int = 0) -> list[Account]:
        """List all accounts with pagination."""
        with self.uow:
            return self.uow.accounts.list_all(limit=limit, offset=offset)

    def add_balance_snapshot(self, command: UpdateBalance) -> BalanceSnapshot:
        """Record a balance snapshot for an account.

        Raises:
            NotFoundError: If the account does not exist.
        """
        with self.uow:
            account = self.uow.accounts.get(command.account_id)
            if account is None:
                raise NotFoundError(
                    f"Account not found: {command.account_id}"
                )
            snapshot = BalanceSnapshot(
                id=0,  # assigned by repository
                account_id=command.account_id,
                datetime=command.snapshot_datetime,
                balance=command.balance,
            )
            self.uow.balance_snapshots.save(snapshot)
            self.uow.commit()
            return snapshot
