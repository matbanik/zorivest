# packages/core/src/zorivest_core/domain/portfolio_balance.py
"""MEU-9: Total portfolio balance computation.

Pure function that computes the total portfolio balance from a list of accounts
by summing the latest BalanceSnapshot for each account.

Source: domain-model-reference.md lines 115–122 (Local Canon derivation).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from zorivest_core.domain.entities import Account


@dataclass(frozen=True)
class TotalPortfolioBalance:
    """Computed total across all accounts.

    Attributes:
        total: Sum of the latest balance for every account (includes negatives).
        per_account: Mapping of account_id → latest balance for each account.
        computed_at: Timestamp when this computation was performed.
    """

    total: Decimal
    per_account: dict[str, Decimal]
    computed_at: datetime


def _latest_balance(account: Account) -> Decimal:
    """Extract the latest balance from an account's snapshots.

    Returns Decimal("0") if the account has no snapshots.
    Uses max(snapshot.datetime) to determine the latest, not list position.
    """
    if not account.balance_snapshots:
        return Decimal("0")
    latest = max(account.balance_snapshots, key=lambda s: s.datetime)
    return latest.balance


def calculate_total_portfolio_balance(
    accounts: list[Account],
) -> TotalPortfolioBalance:
    """Compute total portfolio balance from a list of accounts.

    Sums the latest BalanceSnapshot.balance for each account.
    Accounts with no snapshots contribute Decimal("0").
    Negative balances (credit cards, loans) are included.

    Args:
        accounts: List of Account entities to sum.

    Returns:
        TotalPortfolioBalance with total, per-account breakdown, and timestamp.
    """
    per_account: dict[str, Decimal] = {}
    total = Decimal("0")

    for account in accounts:
        balance = _latest_balance(account)
        per_account[account.account_id] = balance
        total += balance

    return TotalPortfolioBalance(
        total=total,
        per_account=per_account,
        computed_at=datetime.now(),
    )
