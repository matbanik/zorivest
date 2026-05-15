# packages/core/src/zorivest_core/domain/tax/wash_sale_warnings.py
"""Wash sale warning generation for rebalance, spousal, and DRIP conflicts.

MEU-135 AC-135.1–135.5.
Reference: IRS Publication 550 — wash sale rule (30-day post-sale window).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum

from zorivest_core.domain.entities import TaxLot


class WarningType(StrEnum):
    """AC-135.2: Warning categories for wash sale conflict detection."""

    REBALANCE_CONFLICT = "REBALANCE_CONFLICT"  # DCA/rebalance would trigger wash sale
    SPOUSAL_CONFLICT = "SPOUSAL_CONFLICT"  # Spouse's purchase conflicts
    DRIP_CONFLICT = "DRIP_CONFLICT"  # Dividend reinvestment conflicts


@dataclass(frozen=True)
class WashSaleWarning:
    """AC-135.1: Advisory warning for potential wash sale conflict.

    Frozen dataclass with 5 fields — advisory only, does not block trades.
    """

    warning_type: WarningType
    ticker: str
    message: str
    conflicting_lot_id: str
    days_remaining: int  # Days until the 30-day post-sale window expires


def check_conflicts(
    *,
    ticker: str,
    recent_losses: list[TaxLot],
    now: datetime | None = None,
    spousal_lot_ids: set[str] | None = None,
    include_spousal: bool = True,
) -> list[WashSaleWarning]:
    """Check for wash sale conflicts if a purchase of `ticker` were made now.

    AC-135.3: Returns warnings when a recent loss exists and a purchase
    would occur within the 30-day post-sale window.

    AC-135.4: When include_spousal=True, spousal account lots are included.

    AC-135.5: days_remaining = 30 - (now - close_date).days.

    Args:
        ticker: The ticker being considered for purchase.
        recent_losses: Closed lots with losses in this ticker.
        now: Current datetime (defaults to UTC now).
        spousal_lot_ids: Set of lot IDs belonging to spousal accounts.
        include_spousal: If False, exclude spousal lots from conflict check.

    Returns:
        List of WashSaleWarning objects (advisory only).
    """
    if now is None:
        now = datetime.now(tz=timezone.utc)

    if spousal_lot_ids is None:
        spousal_lot_ids = set()

    warnings: list[WashSaleWarning] = []

    for loss_lot in recent_losses:
        if loss_lot.close_date is None:
            continue

        # Only care about actual losses
        if loss_lot.cost_basis <= loss_lot.proceeds:
            continue

        # Filter by ticker
        if loss_lot.ticker != ticker:
            continue

        # Check if this is a spousal lot
        is_spousal = loss_lot.lot_id in spousal_lot_ids

        # AC-135.4: exclude spousal lots when include_spousal=False
        if is_spousal and not include_spousal:
            continue

        # AC-135.5: compute days remaining in the 30-day post-sale window
        days_since_sale = (now - loss_lot.close_date).days
        days_remaining = 30 - days_since_sale

        # If window has expired (days_remaining <= 0), no warning needed
        if days_remaining <= 0:
            continue

        # Determine warning type
        if is_spousal:
            warning_type = WarningType.SPOUSAL_CONFLICT
            message = (
                f"Spousal account loss on {ticker} closed {days_since_sale} days ago. "
                f"Purchase would trigger wash sale ({days_remaining} days remaining)."
            )
        else:
            warning_type = WarningType.REBALANCE_CONFLICT
            message = (
                f"Loss on {ticker} closed {days_since_sale} days ago. "
                f"Purchase would trigger wash sale ({days_remaining} days remaining)."
            )

        warnings.append(
            WashSaleWarning(
                warning_type=warning_type,
                ticker=ticker,
                message=message,
                conflicting_lot_id=loss_lot.lot_id,
                days_remaining=days_remaining,
            )
        )

    return warnings
