# packages/core/src/zorivest_core/domain/tax/lot_matcher.py
"""Pure domain function for tax lot detail enrichment and selection preview.

MEU-140: Implements ACs 140.1–140.6.
- LotDetail frozen dataclass with 9 fields.
- get_lot_details(lots, current_price) — enriches lots with unrealized P&L.
- preview_lot_selection(lots, quantity, method, sale_price) — lot selection
  preview with per-lot enrichment.

Spec: domain-model-reference.md C4 ("pick exactly which lots to close").
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from zorivest_core.domain.entities import TaxLot
from zorivest_core.domain.enums import CostBasisMethod
from zorivest_core.domain.tax.lot_selector import select_lots_for_closing

# IRS long-term holding threshold (domain-model-reference.md A2)
_LT_THRESHOLD_DAYS = 366


@dataclass(frozen=True)
class LotDetail:
    """Per-lot enrichment result with unrealized P&L and holding data.

    AC-140.2: 9 fields — lot_id, ticker, quantity, cost_basis,
    unrealized_gain, unrealized_gain_pct, holding_period_days,
    days_to_long_term, is_long_term.
    """

    lot_id: str
    ticker: str
    quantity: float
    cost_basis: Decimal
    unrealized_gain: Decimal
    unrealized_gain_pct: Decimal
    holding_period_days: int
    days_to_long_term: int
    is_long_term: bool


def get_lot_details(
    lots: list[TaxLot],
    current_price: Decimal,
) -> list[LotDetail]:
    """Enrich tax lots with unrealized gain/loss and holding period info.

    AC-140.1: Returns per-lot data: cost_basis, unrealized_gain,
    unrealized_gain_pct, holding_period_days, days_to_long_term, is_long_term.

    AC-140.4: unrealized_gain = (current_price - adjusted_basis) × quantity
    where adjusted_basis = cost_basis + wash_sale_adjustment.

    AC-140.3: days_to_long_term = max(0, 366 - holding_period_days).

    Args:
        lots: Tax lots to enrich.
        current_price: Current per-share market price.

    Returns:
        List of LotDetail objects, one per input lot.
    """
    results: list[LotDetail] = []

    for lot in lots:
        adjusted_basis = lot.cost_basis + lot.wash_sale_adjustment
        gain_per_share = current_price - adjusted_basis
        unrealized_gain = gain_per_share * Decimal(str(lot.quantity))

        # Percentage: (current_price - adjusted_basis) / adjusted_basis * 100
        if adjusted_basis != 0:
            unrealized_gain_pct = (
                gain_per_share / adjusted_basis * Decimal("100")
            ).quantize(Decimal("0.01"))
        else:
            unrealized_gain_pct = Decimal("0.00")

        holding_days = lot.holding_period_days
        is_lt = holding_days >= _LT_THRESHOLD_DAYS
        days_to_lt = max(0, _LT_THRESHOLD_DAYS - holding_days)

        results.append(
            LotDetail(
                lot_id=lot.lot_id,
                ticker=lot.ticker,
                quantity=lot.quantity,
                cost_basis=lot.cost_basis,
                unrealized_gain=unrealized_gain,
                unrealized_gain_pct=unrealized_gain_pct,
                holding_period_days=holding_days,
                days_to_long_term=days_to_lt,
                is_long_term=is_lt,
            )
        )

    return results


def preview_lot_selection(
    lots: list[TaxLot],
    quantity: float,
    method: CostBasisMethod,
    sale_price: Decimal,
    lot_ids: Optional[list[str]] = None,
) -> list[LotDetail]:
    """Select lots for closing and return enriched per-lot details.

    AC-140.5: Enriches select_lots_for_closing output with per-lot detail.
    AC-140.6: Results sorted by the selected CostBasisMethod.

    Args:
        lots: Open lots available for selection.
        quantity: Number of shares to sell.
        method: Cost basis selection method.
        sale_price: Per-share sale price.
        lot_ids: Explicit lot IDs for SPEC_ID method.

    Returns:
        List of LotDetail for the selected lots with quantities adjusted
        to reflect the selection.

    Raises:
        ValueError: If quantity exceeds available or SPEC_ID without lot_ids.
    """
    selected = select_lots_for_closing(
        lots,
        quantity,
        method,
        sale_price=sale_price,
        lot_ids=lot_ids,
    )

    results: list[LotDetail] = []
    for lot, qty in selected:
        adjusted_basis = lot.cost_basis + lot.wash_sale_adjustment
        gain_per_share = sale_price - adjusted_basis
        unrealized_gain = gain_per_share * Decimal(str(qty))

        if adjusted_basis != 0:
            unrealized_gain_pct = (
                gain_per_share / adjusted_basis * Decimal("100")
            ).quantize(Decimal("0.01"))
        else:
            unrealized_gain_pct = Decimal("0.00")

        holding_days = lot.holding_period_days
        is_lt = holding_days >= _LT_THRESHOLD_DAYS
        days_to_lt = max(0, _LT_THRESHOLD_DAYS - holding_days)

        results.append(
            LotDetail(
                lot_id=lot.lot_id,
                ticker=lot.ticker,
                quantity=qty,
                cost_basis=lot.cost_basis,
                unrealized_gain=unrealized_gain,
                unrealized_gain_pct=unrealized_gain_pct,
                holding_period_days=holding_days,
                days_to_long_term=days_to_lt,
                is_long_term=is_lt,
            )
        )

    return results
