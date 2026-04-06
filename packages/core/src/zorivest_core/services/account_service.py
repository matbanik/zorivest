"""AccountService — account CRUD, soft-delete, reassignment, and metrics.

Source: domain-model-reference §Account, BUILD_PLAN.md §MEU-37
Uses: CreateAccount, UpdateBalance commands (commands.py)
Decision provenance: pomera note 732 (D1-D3)
"""

from __future__ import annotations

from decimal import Decimal

from zorivest_core.application.commands import CreateAccount, UpdateBalance
from zorivest_core.application.ports import UnitOfWork
from zorivest_core.domain.entities import Account, BalanceSnapshot
from zorivest_core.domain.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
)

# Sentinel ID for the system reassignment account (D1)
SYSTEM_DEFAULT_ACCOUNT_ID = "SYSTEM_DEFAULT"


class AccountService:
    """Account management: create, get, list, delete, archive, reassign, metrics."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    # ── Guards ───────────────────────────────────────────────────────────

    def _guard_not_found(self, account_id: str) -> Account:
        """Get an account or raise NotFoundError."""
        account = self.uow.accounts.get(account_id)
        if account is None:
            raise NotFoundError(f"Account not found: {account_id}")
        return account

    def _guard_not_system(self, account: Account) -> None:
        """Raise ForbiddenError if the account is a system account."""
        if account.is_system:
            raise ForbiddenError(f"Cannot modify system account: {account.account_id}")

    # ── Create ───────────────────────────────────────────────────────────

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

    # ── Read ─────────────────────────────────────────────────────────────

    def get_account(self, account_id: str) -> Account:
        """Retrieve an account by ID.

        Raises:
            NotFoundError: If account does not exist.
        """
        with self.uow:
            return self._guard_not_found(account_id)

    def list_accounts(
        self,
        limit: int = 100,
        offset: int = 0,
        include_archived: bool = False,
        include_system: bool = False,
    ) -> list[Account]:
        """List accounts with optional archived/system filtering."""
        with self.uow:
            return self.uow.accounts.list_all(
                limit=limit,
                offset=offset,
                include_archived=include_archived,
                include_system=include_system,
            )

    # ── Update ───────────────────────────────────────────────────────────

    def update_account(self, account_id: str, **kwargs: object) -> Account:
        """Update account fields by account_id.

        Raises:
            ForbiddenError: If account is a system account (is_system=True).
            NotFoundError: If account does not exist.
        """
        with self.uow:
            account = self._guard_not_found(account_id)
            self._guard_not_system(account)
            # Validate create/update invariant parity — name must not be blank
            if "name" in kwargs and (
                not kwargs["name"] or not str(kwargs["name"]).strip()
            ):
                msg = "name must not be empty"
                raise ValueError(msg)
            # Account is a mutable dataclass — create new instance with updated fields
            updated = Account(**{**account.__dict__, **kwargs})
            self.uow.accounts.update(updated)
            self.uow.commit()
            return updated

    # ── Delete (block-only) ──────────────────────────────────────────────

    def delete_account(self, account_id: str) -> None:
        """Delete account if it has no trades or trade plans (AC-7, AC-8, AC-9).

        Raises:
            ForbiddenError: If account is a system account (is_system=True).
            ConflictError: If account has associated trades or trade plans.
            NotFoundError: If account does not exist.
        """
        with self.uow:
            account = self._guard_not_found(account_id)
            self._guard_not_system(account)
            # Block if trades exist
            trades = self.uow.trades.list_for_account(account_id)
            # Block if trade plans reference this account
            plan_count = self.uow.trade_plans.count_for_account(account_id)

            conflicts: list[str] = []
            if trades:
                conflicts.append(f"{len(trades)} trade(s)")
            if plan_count:
                conflicts.append(f"{plan_count} trade plan(s)")

            if conflicts:
                raise ConflictError(
                    f"Cannot delete account '{account.name}': "
                    f"{' and '.join(conflicts)} reference this account. "
                    "Use archive or reassign-trades instead."
                )
            self.uow.accounts.delete(account_id)
            self.uow.commit()

    # ── Archive (soft-delete) ────────────────────────────────────────────

    def archive_account(self, account_id: str) -> None:
        """Soft-delete: set is_archived=True. Trades remain unchanged (AC-10).

        Raises:
            ForbiddenError: If account is a system account (is_system=True).
            NotFoundError: If account does not exist.
        """
        with self.uow:
            account = self._guard_not_found(account_id)
            self._guard_not_system(account)
            archived = Account(**{**account.__dict__, "is_archived": True})
            self.uow.accounts.update(archived)
            self.uow.commit()

    # ── Reassign trades and delete ───────────────────────────────────────

    def reassign_trades_and_delete(self, account_id: str) -> int:
        """Move all trades to SYSTEM_DEFAULT, then hard-delete the account (AC-11).

        Returns:
            Number of trades reassigned.

        Raises:
            ForbiddenError: If account is a system account (is_system=True).
            NotFoundError: If account does not exist.
        """
        with self.uow:
            account = self._guard_not_found(account_id)
            self._guard_not_system(account)
            count = self.uow.accounts.reassign_trades_to(
                source_id=account_id,
                target_id=SYSTEM_DEFAULT_ACCOUNT_ID,
            )
            self.uow.accounts.delete(account_id)
            self.uow.commit()
            return count

    # ── Computed Metrics ─────────────────────────────────────────────────

    def get_account_metrics(self, account_id: str) -> dict:
        """Compute trade-based metrics for an account (AC-12).

        Returns:
            dict with trade_count, round_trip_count, win_rate, total_realized_pnl
        """
        with self.uow:
            self._guard_not_found(account_id)
            trades = self.uow.trades.list_for_account(account_id)
            trade_count = len(trades)
            total_realized_pnl = sum(t.realized_pnl for t in trades)

            # Round-trip count: use round_trips repo if available
            round_trip_count = 0
            if hasattr(self.uow, "round_trips"):
                rts = self.uow.round_trips.list_for_account(account_id)
                round_trip_count = len(rts)

            # Win rate: % of trades with positive realized_pnl
            winning_trades = sum(1 for t in trades if t.realized_pnl > 0)
            win_rate = (winning_trades / trade_count * 100) if trade_count > 0 else 0.0

            return {
                "trade_count": trade_count,
                "round_trip_count": round_trip_count,
                "win_rate": round(win_rate, 2),
                "total_realized_pnl": round(total_realized_pnl, 2),
            }

    # ── Balance management ───────────────────────────────────────────────

    def add_balance_snapshot(self, command: UpdateBalance) -> BalanceSnapshot:
        """Record a balance snapshot for an account.

        Raises:
            NotFoundError: If the account does not exist.
        """
        with self.uow:
            self._guard_not_found(command.account_id)
            snapshot = BalanceSnapshot(
                id=0,  # assigned by repository
                account_id=command.account_id,
                datetime=command.snapshot_datetime,
                balance=command.balance,
            )
            self.uow.balance_snapshots.save(snapshot)
            self.uow.commit()
            return snapshot

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
            self._guard_not_found(account_id)
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
            accounts = self.uow.accounts.list_all(
                limit=10000, offset=0, include_system=True
            )
            total = Decimal("0")
            for acct in accounts:
                latest = self.uow.balance_snapshots.get_latest(acct.account_id)
                if latest is not None:
                    total += latest.balance
            return total
