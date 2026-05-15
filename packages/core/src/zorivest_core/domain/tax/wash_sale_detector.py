# packages/core/src/zorivest_core/domain/tax/wash_sale_detector.py
"""Wash sale detection algorithm.

MEU-130 AC-130.5 (61-day window), AC-130.6 (ticker matching),
AC-130.7 (partial wash sale proportional rule).
MEU-133 AC-133.1–133.4 (options-to-stock matching via wash_sale_method).
MEU-134 AC-134.3/134.4 (DRIP detection + is_drip_triggered flag).

Reference: IRS Publication 550 — wash sale rule.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal

from zorivest_core.domain.entities import TaxLot
from zorivest_core.domain.enums import AcquisitionSource, WashSaleMatchingMethod
from zorivest_core.domain.tax.option_pairing import parse_option_symbol


@dataclass(frozen=True)
class WashSaleMatch:
    """Result of a wash sale detection match.

    Represents a single pairing between a loss lot and a replacement lot.
    """

    loss_lot_id: str
    replacement_lot_id: str
    matched_quantity: float
    disallowed_loss: Decimal
    is_drip_triggered: bool = False  # MEU-134 AC-134.4


def _is_substantially_identical(
    loss_ticker: str,
    candidate_ticker: str,
    method: WashSaleMatchingMethod,
) -> bool:
    """Check if a candidate lot is substantially identical to the loss lot.

    AC-133.2: CONSERVATIVE — equity options on the same underlying
    are substantially identical (IRS Pub 550 p.58).
    AC-133.3: AGGRESSIVE — only exact ticker match (different CUSIP = not identical).
    AC-133.4: Malformed option symbol → None → skip (no crash).

    Args:
        loss_ticker: Ticker of the loss lot (e.g., "AAPL").
        candidate_ticker: Ticker of the candidate replacement (e.g., "AAPL 260420 C 200").
        method: CONSERVATIVE or AGGRESSIVE matching method.

    Returns:
        True if the candidate is substantially identical to the loss.
    """
    # Exact ticker match always qualifies
    if candidate_ticker == loss_ticker:
        return True

    # AGGRESSIVE mode: only exact match (handled above)
    if method == WashSaleMatchingMethod.AGGRESSIVE:
        return False

    # CONSERVATIVE mode: check if candidate is an option on the same underlying
    option_details = parse_option_symbol(candidate_ticker)
    if option_details is not None and option_details.underlying == loss_ticker:
        return True

    return False


def detect_wash_sales(
    loss_lot: TaxLot,
    candidate_lots: list[TaxLot],
    *,
    include_drip: bool = True,
    wash_sale_method: WashSaleMatchingMethod = WashSaleMatchingMethod.CONSERVATIVE,
) -> list[WashSaleMatch]:
    """Detect wash sales for a given loss lot against candidate replacements.

    AC-130.5: Scans for purchases of substantially identical securities
    within a 61-day window (30 days before + sale day + 30 days after).

    AC-130.6: Matching is by ticker (same ticker = substantially identical).

    AC-130.7: Partial wash sale support — if replacement quantity < loss
    quantity, only the proportional amount of the loss is disallowed.

    AC-133.1: wash_sale_method param (default CONSERVATIVE).
    AC-133.2: CONSERVATIVE includes options on same underlying.
    AC-133.3: AGGRESSIVE ignores options (strict ticker match only).

    AC-134.3: When include_drip=True (default), DRIP lots are valid
    replacement candidates. When False, DRIP lots are excluded.

    AC-134.4: WashSaleMatch.is_drip_triggered is True when the replacement
    lot has acquisition_source == DRIP.

    Args:
        loss_lot: The closed lot that realized a loss.
        candidate_lots: All lots to check as potential replacements.
        include_drip: If False, exclude DRIP-sourced lots from matching.
        wash_sale_method: CONSERVATIVE or AGGRESSIVE matching method.

    Returns:
        List of WashSaleMatch objects for each triggering replacement lot.
    """
    if not loss_lot.close_date:
        return []

    sale_date = loss_lot.close_date
    window_start = sale_date - timedelta(days=30)
    window_end = sale_date + timedelta(days=30)

    # Per-share loss
    per_share_loss = loss_lot.cost_basis - loss_lot.proceeds
    if per_share_loss <= Decimal("0"):
        # No loss → no wash sale
        return []

    remaining_loss_qty = loss_lot.quantity
    matches: list[WashSaleMatch] = []

    # Sort candidates by purchase date for deterministic allocation
    sorted_candidates = sorted(candidate_lots, key=lambda lot: lot.open_date)

    for candidate in sorted_candidates:
        if remaining_loss_qty <= 0:
            break

        # AC-133.2/133.3: substantially identical check (replaces AC-130.6 ticker-only)
        if not _is_substantially_identical(
            loss_lot.ticker,
            candidate.ticker,
            wash_sale_method,
        ):
            continue

        # AC-130.5: purchase must be within the 61-day window
        if not (window_start <= candidate.open_date <= window_end):
            continue

        # Don't match the loss lot against itself
        if candidate.lot_id == loss_lot.lot_id:
            continue

        # AC-134.3: exclude DRIP lots when include_drip is False
        is_drip = (
            getattr(candidate, "acquisition_source", None) == AcquisitionSource.DRIP
        )
        if is_drip and not include_drip:
            continue

        # AC-130.7: matched quantity is min(replacement qty, remaining loss qty)
        matched_qty = min(candidate.quantity, remaining_loss_qty)
        disallowed = per_share_loss * Decimal(str(matched_qty))

        matches.append(
            WashSaleMatch(
                loss_lot_id=loss_lot.lot_id,
                replacement_lot_id=candidate.lot_id,
                matched_quantity=matched_qty,
                disallowed_loss=disallowed,
                is_drip_triggered=is_drip,  # AC-134.4
            )
        )
        remaining_loss_qty -= matched_qty

    return matches
