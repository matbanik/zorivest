# packages/core/src/zorivest_core/domain/tax/lot_selector.py
"""Pure domain function for tax lot selection.

MEU-125: Implements all 8 CostBasisMethod algorithms, including
IBKR Tax Optimizer 4-tier priority logic for MAX_* methods.

Source: implementation-plan.md ACs 125.5–125.11
IBKR: ibkrguides.com/traderworkstation/lot-matching-methods.htm
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from zorivest_core.domain.entities import TaxLot
from zorivest_core.domain.enums import CostBasisMethod

# 366 days = IRS long-term holding threshold (domain-model-reference.md A2)
_LT_THRESHOLD_DAYS = 366


def select_lots_for_closing(
    lots: list[TaxLot],
    quantity: float,
    method: CostBasisMethod,
    sale_price: Optional[Decimal] = None,
    lot_ids: Optional[list[str]] = None,
) -> list[tuple[TaxLot, float]]:
    """Select which tax lots to close for a sale.

    Args:
        lots: Open lots available for closing.
        quantity: Number of shares to sell.
        method: Cost basis selection method (one of 8 CostBasisMethod values).
        sale_price: Per-share sale price. Required for MAX_* methods to compute
            per-lot gain/loss for IBKR 4-tier priority ranking.
        lot_ids: Explicit lot IDs for SPEC_ID method.

    Returns:
        List of (TaxLot, quantity_to_close) tuples in selection order.

    Raises:
        ValueError: If quantity exceeds total available, sale_price missing
            for MAX_* methods, or lot_ids missing/empty for SPEC_ID.
    """
    total_available = sum(lot.quantity for lot in lots)
    if quantity > total_available:
        msg = (
            f"Requested quantity {quantity} exceeds total open lot "
            f"quantity {total_available}"
        )
        raise ValueError(msg)

    if method == CostBasisMethod.SPEC_ID:
        return _select_spec_id(lots, quantity, lot_ids)

    if method in _MAX_METHODS:
        if sale_price is None:
            msg = "sale_price is required for MAX_* cost basis methods"
            raise ValueError(msg)
        sorted_lots = _sort_max_priority(lots, method, sale_price)
    else:
        sorted_lots = _sort_simple(lots, method)

    return _fill(sorted_lots, quantity)


# ── Simple sort methods ──────────────────────────────────────────────────

_SIMPLE_SORT_KEYS = {
    CostBasisMethod.FIFO: lambda lot: (lot.open_date, lot.lot_id),
    CostBasisMethod.LIFO: lambda lot: (lot.open_date, lot.lot_id),
    CostBasisMethod.HIFO: lambda lot: (lot.cost_basis, lot.lot_id),
}


def _sort_simple(lots: list[TaxLot], method: CostBasisMethod) -> list[TaxLot]:
    """Sort lots for FIFO, LIFO, or HIFO."""
    key = _SIMPLE_SORT_KEYS[method]
    reverse = method in (CostBasisMethod.LIFO, CostBasisMethod.HIFO)
    return sorted(lots, key=key, reverse=reverse)


# ── IBKR 4-tier MAX_* methods ───────────────────────────────────────────

_MAX_METHODS = frozenset(
    {
        CostBasisMethod.MAX_LT_GAIN,
        CostBasisMethod.MAX_LT_LOSS,
        CostBasisMethod.MAX_ST_GAIN,
        CostBasisMethod.MAX_ST_LOSS,
    }
)


# Each MAX_* method has 4 priority tiers. Each tier is defined by:
#   (is_long_term, is_gain, maximize_magnitude)
# where:
#   is_long_term: True = long-term lots, False = short-term lots
#   is_gain: True = gain lots, False = loss lots
#   maximize_magnitude: True = pick largest |gain/loss|, False = pick smallest
#
# Source: IBKR lot-matching-methods.htm
_MAX_TIER_RULES: dict[CostBasisMethod, list[tuple[bool, bool, bool]]] = {
    # MLG: ① Max LT gain → ② Max ST gain → ③ Min ST loss → ④ Min LT loss
    CostBasisMethod.MAX_LT_GAIN: [
        (True, True, True),  # ① LT gain, maximize
        (False, True, True),  # ② ST gain, maximize
        (False, False, False),  # ③ ST loss, minimize
        (True, False, False),  # ④ LT loss, minimize
    ],
    # MLL: ① Max LT loss → ② Max ST loss → ③ Min ST gain → ④ Min LT gain
    CostBasisMethod.MAX_LT_LOSS: [
        (True, False, True),  # ① LT loss, maximize
        (False, False, True),  # ② ST loss, maximize
        (False, True, False),  # ③ ST gain, minimize
        (True, True, False),  # ④ LT gain, minimize
    ],
    # MSG: ① Max ST gain → ② Max LT gain → ③ Min LT loss → ④ Min ST loss
    CostBasisMethod.MAX_ST_GAIN: [
        (False, True, True),  # ① ST gain, maximize
        (True, True, True),  # ② LT gain, maximize
        (True, False, False),  # ③ LT loss, minimize
        (False, False, False),  # ④ ST loss, minimize
    ],
    # MSL: ① Max ST loss → ② Max LT loss → ③ Min LT gain → ④ Min ST gain
    CostBasisMethod.MAX_ST_LOSS: [
        (False, False, True),  # ① ST loss, maximize
        (True, False, True),  # ② LT loss, maximize
        (True, True, False),  # ③ LT gain, minimize
        (False, True, False),  # ④ ST gain, minimize
    ],
}


def _sort_max_priority(
    lots: list[TaxLot],
    method: CostBasisMethod,
    sale_price: Decimal,
) -> list[TaxLot]:
    """Sort lots using IBKR 4-tier priority for MAX_* methods.

    Lots are partitioned into the first matching tier, then sorted
    within that tier by gain/loss magnitude. Remaining lots from
    lower tiers are appended in their own priority order.
    """
    tiers = _MAX_TIER_RULES[method]
    used: set[str] = set()
    result: list[TaxLot] = []

    for is_lt, is_gain, maximize in tiers:
        tier_lots = []
        for lot in lots:
            if lot.lot_id in used:
                continue
            lot_is_lt = lot.holding_period_days >= _LT_THRESHOLD_DAYS
            gain_per_share = sale_price - lot.cost_basis
            lot_is_gain = gain_per_share > 0

            if lot_is_lt == is_lt and lot_is_gain == is_gain:
                tier_lots.append((lot, gain_per_share))

        if not tier_lots:
            continue

        # Sort by magnitude of gain/loss per share
        tier_lots.sort(key=lambda x: abs(x[1]), reverse=maximize)
        for lot, _ in tier_lots:
            result.append(lot)
            used.add(lot.lot_id)

    return result


# ── SPEC_ID ──────────────────────────────────────────────────────────────


def _select_spec_id(
    lots: list[TaxLot],
    quantity: float,
    lot_ids: Optional[list[str]],
) -> list[tuple[TaxLot, float]]:
    """Select specific lots by ID (SPEC_ID method)."""
    if not lot_ids:
        msg = "lot_ids parameter is required for SPEC_ID method"
        raise ValueError(msg)

    lot_map = {lot.lot_id: lot for lot in lots}
    selected: list[TaxLot] = []
    for lid in lot_ids:
        if lid not in lot_map:
            msg = f"Lot ID '{lid}' not found in available lots"
            raise ValueError(msg)
        selected.append(lot_map[lid])

    return _fill(selected, quantity)


# ── Fill helper ──────────────────────────────────────────────────────────


def _fill(
    sorted_lots: list[TaxLot],
    quantity: float,
) -> list[tuple[TaxLot, float]]:
    """Consume lots in order until quantity is filled.

    Returns (lot, quantity_to_close) tuples.
    """
    result: list[tuple[TaxLot, float]] = []
    remaining = quantity

    for lot in sorted_lots:
        if remaining <= 0:
            break
        take = min(lot.quantity, remaining)
        result.append((lot, take))
        remaining -= take

    return result
