# packages/core/src/zorivest_core/domain/tax/rate_comparison.py
"""Pure domain function for ST vs LT tax rate dollar comparison.

MEU-142: Implements ACs 142.1–142.7.
- StLtComparison frozen dataclass with 7 fields.
- compare_st_lt_tax(lot, sale_price, tax_profile) — computes the
  tax if sold now (ST rate) vs tax if held until long-term (LT rate)
  and the dollar savings from waiting.

Spec: domain-model-reference.md C6 ("wait N days, save $X").

Tax Estimation Basis (Simplified Model):
  ST gains: compute_marginal_rate(agi_estimate, ...) * gain
  LT gains: compute_capital_gains_tax(gain, agi_estimate, ...)
  State tax: flat rate from TaxProfile.state_tax_rate
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from zorivest_core.domain.entities import TaxLot, TaxProfile
from zorivest_core.domain.tax.brackets import (
    compute_capital_gains_tax,
    compute_combined_rate,
    compute_marginal_rate,
)

# IRS long-term holding threshold
_LT_THRESHOLD_DAYS = 366


@dataclass(frozen=True)
class StLtComparison:
    """Result of ST vs LT tax comparison.

    AC-142.2: Frozen dataclass with 7 fields.
    """

    tax_now: Decimal
    rate_now: Decimal
    tax_lt: Decimal
    rate_lt: Decimal
    days_remaining: int
    tax_savings: Decimal
    holding_classification: str  # "short_term" | "long_term"


def compare_st_lt_tax(
    lot: TaxLot,
    sale_price: Decimal,
    tax_profile: TaxProfile,
) -> StLtComparison:
    """Compare tax if sold now (ST rate) vs held until long-term (LT rate).

    AC-142.1: Returns StLtComparison with tax_if_sold_now, tax_if_held_lt,
    days_remaining, and tax_savings.

    AC-142.3: ST tax uses compute_marginal_rate(agi_estimate, ...).
    AC-142.4: LT tax uses compute_capital_gains_tax(lt_gains, agi_estimate, ...).
    AC-142.5: tax_savings = tax_now - tax_lt.
    AC-142.6: Negative gain → both taxes 0, savings 0.
    AC-142.7: State tax via compute_combined_rate.

    Args:
        lot: Open tax lot to evaluate.
        sale_price: Current or hypothetical per-share sale price.
        tax_profile: User's tax configuration.

    Returns:
        StLtComparison result.
    """
    adjusted_basis = lot.cost_basis + lot.wash_sale_adjustment
    gain_per_share = sale_price - adjusted_basis
    gain = gain_per_share * Decimal(str(lot.quantity))

    holding_days = lot.holding_period_days
    is_lt = holding_days >= _LT_THRESHOLD_DAYS
    days_remaining = max(0, _LT_THRESHOLD_DAYS - holding_days)
    classification = "long_term" if is_lt else "short_term"

    state_rate = Decimal(str(tax_profile.state_tax_rate))

    # AC-142.6: Negative gain → all zeros
    if gain <= 0:
        return StLtComparison(
            tax_now=Decimal("0"),
            rate_now=Decimal("0"),
            tax_lt=Decimal("0"),
            rate_lt=Decimal("0"),
            days_remaining=days_remaining,
            tax_savings=Decimal("0"),
            holding_classification=classification,
        )

    # AC-142.3: ST tax via marginal rate
    federal_st_rate = compute_marginal_rate(
        tax_profile.agi_estimate,
        tax_profile.filing_status,
        tax_profile.tax_year,
    )
    # AC-142.7: Include state tax
    combined_st_rate = compute_combined_rate(federal_st_rate, state_rate)
    tax_now = (gain * combined_st_rate).quantize(Decimal("0.01"))

    # AC-142.4: LT tax via LTCG preferential rate
    tax_lt_federal = compute_capital_gains_tax(
        gain,
        tax_profile.agi_estimate,
        tax_profile.filing_status,
        tax_profile.tax_year,
    )
    # Add state tax to LT as well
    tax_lt_state = (gain * state_rate).quantize(Decimal("0.01"))
    tax_lt = tax_lt_federal + tax_lt_state

    # Compute LT rate for display
    rate_lt = (tax_lt / gain).quantize(Decimal("0.01")) if gain > 0 else Decimal("0")

    # AC-142.5: If already LT, tax_now == tax_lt, savings == 0
    if is_lt:
        return StLtComparison(
            tax_now=tax_lt,
            rate_now=rate_lt,
            tax_lt=tax_lt,
            rate_lt=rate_lt,
            days_remaining=0,
            tax_savings=Decimal("0"),
            holding_classification=classification,
        )

    # AC-142.5: tax_savings = tax_now - tax_lt
    tax_savings = tax_now - tax_lt

    return StLtComparison(
        tax_now=tax_now,
        rate_now=combined_st_rate,
        tax_lt=tax_lt,
        rate_lt=rate_lt,
        days_remaining=days_remaining,
        tax_savings=tax_savings,
        holding_classification=classification,
    )
