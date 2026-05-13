# packages/core/src/zorivest_core/domain/tax/gains_calculator.py
"""Pure domain function for realized gain/loss calculation.

MEU-126: Computes realized gain/loss for a closed tax lot,
including ST/LT classification and wash sale adjustment.

Spec: domain-model-reference.md A2, A5 (366-day boundary)
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from zorivest_core.domain.entities import TaxLot

# IRS long-term holding threshold (domain-model-reference.md A2)
_LT_THRESHOLD_DAYS = 366


@dataclass(frozen=True)
class RealizedGainResult:
    """Result of a realized gain/loss calculation.

    AC-126.2: Frozen dataclass with gain_amount, is_long_term,
    holding_period_days, tax_type.
    """

    gain_amount: Decimal
    is_long_term: bool
    holding_period_days: int
    tax_type: str  # "short_term" | "long_term"


def calculate_realized_gain(
    lot: TaxLot,
    sale_price: Decimal,
) -> RealizedGainResult:
    """Compute the realized gain/loss for a tax lot sale.

    AC-126.1: Pure domain function returning RealizedGainResult.
    AC-126.3: Formula accounts for wash_sale_adjustment in basis.

    Formula:
        adjusted_cost_basis = cost_basis + wash_sale_adjustment
        gain_amount = (sale_price - adjusted_cost_basis) × quantity

    Args:
        lot: The TaxLot being sold (should have close_date set).
        sale_price: Per-share sale price.

    Returns:
        RealizedGainResult with computed gain, holding classification,
        and holding period in days.
    """
    adjusted_basis = lot.cost_basis + lot.wash_sale_adjustment
    gain_per_share = sale_price - adjusted_basis
    gain_amount = gain_per_share * Decimal(str(lot.quantity))

    holding_days = lot.holding_period_days
    is_lt = holding_days >= _LT_THRESHOLD_DAYS

    return RealizedGainResult(
        gain_amount=gain_amount,
        is_long_term=is_lt,
        holding_period_days=holding_days,
        tax_type="long_term" if is_lt else "short_term",
    )
