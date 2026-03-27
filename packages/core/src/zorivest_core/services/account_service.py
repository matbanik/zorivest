"""AccountService — account CRUD and balance snapshots.

Source: domain-model-reference §Account
Uses: CreateAccount, UpdateBalance commands (commands.py)
"""

from __future__ import annotations

from decimal import Decimal

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
                raise NotFoundError(f"Account not found: {command.account_id}")
            snapshot = BalanceSnapshot(
                id=0,  # assigned by repository
                account_id=command.account_id,
                datetime=command.snapshot_datetime,
                balance=command.balance,
            )
            self.uow.balance_snapshots.save(snapshot)
            self.uow.commit()
            return snapshot

    def update_account(self, account_id: str, **kwargs: object) -> Account:
        """Update account fields by account_id.

        Raises:
            NotFoundError: If account does not exist.
        """
        with self.uow:
            account = self.uow.accounts.get(account_id)
            if account is None:
                raise NotFoundError(f"Account not found: {account_id}")
            # Frozen dataclass — create new instance with updated fields
            updated = Account(**{**account.__dict__, **kwargs})
            self.uow.accounts.update(updated)
            self.uow.commit()
            return updated

    def delete_account(self, account_id: str) -> None:
        """Delete an account by account_id."""
        with self.uow:
            self.uow.accounts.delete(account_id)
            self.uow.commit()

    # ── MEU-71: Balance history & portfolio total ───────────────────────

    def list_balance_history(
        self,
        account_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[BalanceSnapshot]:
        """List balance snapshots for an account with pagination.

        Raises:
            NotFoundError: If the account does not exist.
        """
        with self.uow:
            account = self.uow.accounts.get(account_id)
            if account is None:
                raise NotFoundError(f"Account not found: {account_id}")
            return self.uow.balance_snapshots.list_for_account(
                account_id,
                limit=limit,
                offset=offset,
            )

    def count_balance_history(self, account_id: str) -> int:
        """Return total count of balance snapshots for an account."""
        with self.uow:
            return self.uow.balance_snapshots.count_for_account(account_id)

    def get_latest_balance(self, account_id: str) -> BalanceSnapshot | None:
        """Return the most recent balance snapshot for an account, or None."""
        with self.uow:
            return self.uow.balance_snapshots.get_latest(account_id)

    def get_portfolio_total(self) -> Decimal:
        """Return the sum of most recent balances across all accounts."""
        with self.uow:
            accounts = self.uow.accounts.list_all(limit=10000, offset=0)
            total = Decimal("0")
            for acct in accounts:
                latest = self.uow.balance_snapshots.get_latest(acct.account_id)
                if latest is not None:
                    total += latest.balance
            return total
