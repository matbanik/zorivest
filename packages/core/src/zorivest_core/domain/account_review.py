# packages/core/src/zorivest_core/domain/account_review.py
"""MEU-11: Account Review workflow domain logic.

Guided step-through process for updating all account balances.
Pure domain logic only — GUI/API/MCP layers are built in later phases.

Source: domain-model-reference.md lines 161–207 (Local Canon derivation).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from zorivest_core.domain.entities import Account, BalanceSnapshot
from zorivest_core.domain.enums import AccountType


@dataclass(frozen=True)
class AccountReviewItem:
    """A single account entry in the review checklist.

    Attributes:
        account_id: Unique account identifier.
        name: Display name of the account.
        account_type: Type (BROKER, BANK, REVOLVING, etc.).
        institution: Financial institution name.
        last_balance: Most recent balance snapshot value, or None if no snapshots.
        last_balance_datetime: Timestamp of the most recent snapshot, or None.
        supports_api_fetch: True for BROKER accounts (can fetch via API).
    """

    account_id: str
    name: str
    account_type: AccountType
    institution: str
    last_balance: Decimal | None
    last_balance_datetime: datetime | None
    supports_api_fetch: bool


@dataclass(frozen=True)
class AccountReviewResult:
    """Result of reviewing a single account.

    Attributes:
        account_id: Which account was reviewed.
        action: "updated" if a new balance was logged, "skipped" otherwise.
        old_balance: Previous latest balance (None if no prior snapshots).
        new_balance: Newly submitted balance (None if skipped).
    """

    account_id: str
    action: str  # "updated" | "skipped"
    old_balance: Decimal | None
    new_balance: Decimal | None


@dataclass(frozen=True)
class AccountReviewSummary:
    """Aggregated summary of the entire review session.

    Attributes:
        total_accounts: Number of accounts in the review.
        updated_count: How many were updated with new balances.
        skipped_count: How many were skipped.
        old_total: Sum of latest balances before this review session.
        new_total: Sum of latest balances after this review session.
        results: Individual results for each account.
    """

    total_accounts: int
    updated_count: int
    skipped_count: int
    old_total: Decimal
    new_total: Decimal
    results: list[AccountReviewResult]


def _latest_snapshot(account: Account) -> BalanceSnapshot | None:
    """Get the most recent snapshot by datetime, or None."""
    if not account.balance_snapshots:
        return None
    return max(account.balance_snapshots, key=lambda s: s.datetime)


def _latest_balance(account: Account) -> Decimal | None:
    """Get the latest balance value, or None if no snapshots."""
    snap = _latest_snapshot(account)
    return snap.balance if snap is not None else None


def prepare_review_checklist(accounts: list[Account]) -> list[AccountReviewItem]:
    """Build the review checklist from a list of accounts.

    BROKER accounts get supports_api_fetch=True.
    All other account types get supports_api_fetch=False.
    Last balance and datetime are extracted from the most recent snapshot
    (by max datetime), or None if no snapshots exist.

    Args:
        accounts: List of Account entities to review.

    Returns:
        Ordered list of AccountReviewItem entries.
    """
    items: list[AccountReviewItem] = []
    for account in accounts:
        snap = _latest_snapshot(account)
        items.append(
            AccountReviewItem(
                account_id=account.account_id,
                name=account.name,
                account_type=account.account_type,
                institution=account.institution,
                last_balance=snap.balance if snap else None,
                last_balance_datetime=snap.datetime if snap else None,
                supports_api_fetch=account.account_type == AccountType.BROKER,
            )
        )
    return items


def apply_balance_update(
    account: Account,
    new_balance: Decimal,
    snapshot_datetime: datetime,
) -> AccountReviewResult:
    """Apply a balance update to an account.

    Creates a new BalanceSnapshot if the balance has changed.
    If new_balance equals the latest existing balance (dedup rule),
    returns a "skipped" result without creating a snapshot.

    Args:
        account: The Account to update.
        new_balance: The new balance value.
        snapshot_datetime: Timestamp for the new snapshot.

    Returns:
        AccountReviewResult with action "updated" or "skipped".
    """
    old_balance = _latest_balance(account)

    # Dedup rule: skip if balance unchanged
    if old_balance is not None and old_balance == new_balance:
        return AccountReviewResult(
            account_id=account.account_id,
            action="skipped",
            old_balance=old_balance,
            new_balance=None,
        )

    # Create new snapshot
    new_snapshot = BalanceSnapshot(
        id=0,  # ID assigned by persistence layer
        account_id=account.account_id,
        datetime=snapshot_datetime,
        balance=new_balance,
    )
    account.balance_snapshots.append(new_snapshot)

    return AccountReviewResult(
        account_id=account.account_id,
        action="updated",
        old_balance=old_balance,
        new_balance=new_balance,
    )


def skip_account(account: Account) -> AccountReviewResult:
    """Skip an account without making changes.

    Args:
        account: The Account to skip.

    Returns:
        AccountReviewResult with action "skipped", no side effects.
    """
    old_balance = _latest_balance(account)
    return AccountReviewResult(
        account_id=account.account_id,
        action="skipped",
        old_balance=old_balance,
        new_balance=None,
    )


def summarize_review(
    results: list[AccountReviewResult],
    accounts: list[Account],
) -> AccountReviewSummary:
    """Aggregate review results into a summary.

    Computes counts of updated vs skipped accounts and calculates
    old/new portfolio totals from the current account state.

    Args:
        results: Individual review results for each account.
        accounts: The accounts after all updates have been applied.

    Returns:
        AccountReviewSummary with counts and totals.
    """
    updated_count = sum(1 for r in results if r.action == "updated")
    skipped_count = sum(1 for r in results if r.action == "skipped")

    # Compute old total from results
    old_total = Decimal("0")
    for r in results:
        if r.old_balance is not None:
            old_total += r.old_balance

    # Compute new total from current account state
    new_total = Decimal("0")
    for account in accounts:
        balance = _latest_balance(account)
        if balance is not None:
            new_total += balance

    return AccountReviewSummary(
        total_accounts=len(results),
        updated_count=updated_count,
        skipped_count=skipped_count,
        old_total=old_total,
        new_total=new_total,
        results=results,
    )
