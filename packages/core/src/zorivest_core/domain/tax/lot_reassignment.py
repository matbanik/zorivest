# packages/core/src/zorivest_core/domain/tax/lot_reassignment.py
"""Pure domain function for post-trade lot reassignment.

MEU-141: Implements ACs 141.1–141.7.
- ReassignmentEligibility frozen dataclass.
- can_reassign_lots(lot, now, settlement_days) — checks T+1 window.
- reassign_lots(lots, quantity, new_method, sale_price) — re-selects lots.

Spec: domain-model-reference.md C5 ("Allow changing lot-matching method
before settlement (T+1)").
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from zorivest_core.domain.entities import TaxLot
from zorivest_core.domain.enums import CostBasisMethod
from zorivest_core.domain.tax.lot_selector import select_lots_for_closing

# US equities T+1 settlement (SEC rule, effective May 28, 2024)
SETTLEMENT_DAYS: int = 1


@dataclass(frozen=True)
class ReassignmentEligibility:
    """Whether a lot can still have its cost basis method reassigned.

    AC-141.2: 4 fields — eligible, deadline, hours_remaining, reason.
    """

    eligible: bool
    deadline: datetime
    hours_remaining: float
    reason: str


def can_reassign_lots(
    lot: TaxLot,
    now: datetime,
    settlement_days: int = SETTLEMENT_DAYS,
) -> ReassignmentEligibility:
    """Check if a lot is within the settlement window for reassignment.

    AC-141.1: Returns ReassignmentEligibility.
    AC-141.3: Window = close_date + settlement_days.
    AC-141.6: settlement_days parameter override for future broker configs.
    AC-141.7: Open lots (close_date is None) → always eligible.

    Args:
        lot: Tax lot to check.
        now: Current datetime (timezone-aware).
        settlement_days: Settlement window in days (default: 1 for T+1).

    Returns:
        ReassignmentEligibility result.
    """
    # AC-141.7: Open lots are always eligible
    if lot.close_date is None:
        return ReassignmentEligibility(
            eligible=True,
            deadline=now + timedelta(days=settlement_days),
            hours_remaining=float(settlement_days * 24),
            reason="Lot is still open — reassignment always permitted.",
        )

    # AC-141.3: Settlement deadline = close_date + settlement_days
    deadline = lot.close_date + timedelta(days=settlement_days)
    remaining = deadline - now

    if remaining.total_seconds() <= 0:
        return ReassignmentEligibility(
            eligible=False,
            deadline=deadline,
            hours_remaining=0.0,
            reason=(
                f"Settlement deadline passed. "
                f"Close date: {lot.close_date.isoformat()}, "
                f"deadline: {deadline.isoformat()}."
            ),
        )

    hours = remaining.total_seconds() / 3600.0
    return ReassignmentEligibility(
        eligible=True,
        deadline=deadline,
        hours_remaining=round(hours, 2),
        reason=(
            f"Within settlement window. "
            f"{round(hours, 1)} hours remaining until deadline."
        ),
    )


def reassign_lots(
    lots: list[TaxLot],
    quantity: float,
    new_method: CostBasisMethod,
    sale_price: Decimal,
    lot_ids: Optional[list[str]] = None,
) -> list[tuple[TaxLot, float]]:
    """Re-select lots using a different CostBasisMethod.

    AC-141.4: Delegates to select_lots_for_closing with the new method.
    AC-141.5: Reuses existing lot_selector infrastructure.

    Args:
        lots: Open lots available for selection.
        quantity: Number of shares to sell.
        new_method: New cost basis selection method.
        sale_price: Per-share sale price.
        lot_ids: Explicit lot IDs for SPEC_ID method.

    Returns:
        List of (TaxLot, quantity_to_close) tuples.

    Raises:
        ValueError: If quantity exceeds available or SPEC_ID without lot_ids.
    """
    return select_lots_for_closing(
        lots,
        quantity,
        new_method,
        sale_price=sale_price,
        lot_ids=lot_ids,
    )
