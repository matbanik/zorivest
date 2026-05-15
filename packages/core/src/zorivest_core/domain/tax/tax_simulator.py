# packages/core/src/zorivest_core/domain/tax/tax_simulator.py
"""Pure domain function for pre-trade "what-if" tax simulation.

MEU-137: Implements ACs 137.1–137.10.
- TaxImpactResult frozen dataclass.
- simulate_tax_impact() — orchestrates lot selection + gain calc +
  wash sale detection + tax estimation + NIIT.

Spec: domain-model-reference.md C1 ("what-if tax simulator").

Tax Estimation Basis (Simplified Model):
  ST gains: compute_marginal_rate(agi_estimate, ...) * gain
  LT gains: compute_capital_gains_tax(gain, agi_estimate, ...)
  NIIT: compute_niit(agi_estimate, net_investment_income, filing_status)
  State: flat rate from TaxProfile.state_tax_rate
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from zorivest_core.domain.entities import TaxLot, TaxProfile
from zorivest_core.domain.enums import CostBasisMethod
from zorivest_core.domain.tax.brackets import (
    compute_capital_gains_tax,
    compute_combined_rate,
    compute_marginal_rate,
)
from zorivest_core.domain.tax.gains_calculator import calculate_realized_gain
from zorivest_core.domain.tax.lot_matcher import LotDetail
from zorivest_core.domain.tax.lot_selector import select_lots_for_closing
from zorivest_core.domain.tax.niit import compute_niit
from zorivest_core.domain.tax.wash_sale_detector import WashSaleMatch, detect_wash_sales


@dataclass(frozen=True)
class TaxImpactResult:
    """Result of a pre-trade tax simulation.

    AC-137.2: Frozen dataclass with lots_selected, realized_st_gain,
    realized_lt_gain, estimated_st_tax, estimated_lt_tax, estimated_niit,
    total_estimated_tax, wash_sale_warnings.
    """

    lots_selected: list[LotDetail]
    realized_st_gain: Decimal
    realized_lt_gain: Decimal
    estimated_st_tax: Decimal
    estimated_lt_tax: Decimal
    estimated_niit: Decimal
    total_estimated_tax: Decimal
    wash_sale_warnings: list[WashSaleMatch]


def simulate_tax_impact(
    lots: list[TaxLot],
    ticker: str,
    quantity: float,
    sale_price: Decimal,
    tax_profile: TaxProfile,
    cost_basis_method: Optional[CostBasisMethod] = None,
    lot_ids: Optional[list[str]] = None,
) -> TaxImpactResult:
    """Simulate the tax impact of selling shares.

    AC-137.1: Main orchestration function combining lot selection,
    gain calculation, wash sale detection, and tax estimation.

    AC-137.3: Uses tax_profile.default_cost_basis or explicit override.
    AC-137.4: ST/LT classification via calculate_realized_gain.
    AC-137.5: ST tax via compute_marginal_rate, LT via compute_capital_gains_tax.
    AC-137.6: Wash sale risk via detect_wash_sales.
    AC-137.7: NIIT via compute_niit.
    AC-137.8: total = estimated_st_tax + estimated_lt_tax + estimated_niit.
    AC-137.9: cost_basis_method param overrides profile default.
    AC-137.10: State tax via compute_combined_rate.

    Args:
        lots: All open tax lots (will be filtered to ticker).
        ticker: Ticker symbol to simulate selling.
        quantity: Number of shares to sell.
        sale_price: Hypothetical per-share sale price.
        tax_profile: User's tax configuration.
        cost_basis_method: Optional override for lot selection method.
        lot_ids: Explicit lot IDs for SPEC_ID method.

    Returns:
        TaxImpactResult with full simulation breakdown.

    Raises:
        ValueError: If ticker not found in lots, quantity exceeds available,
            or SPEC_ID without lot_ids.
    """
    # Filter lots for the given ticker
    ticker_lots = [lot for lot in lots if lot.ticker == ticker and not lot.is_closed]
    if not ticker_lots:
        msg = f"No open lots found for ticker '{ticker}'"
        raise ValueError(msg)

    # AC-137.3 / AC-137.9: Determine cost basis method
    method = cost_basis_method or tax_profile.default_cost_basis

    # Select lots for closing
    selected = select_lots_for_closing(
        ticker_lots,
        quantity,
        method,
        sale_price=sale_price,
        lot_ids=lot_ids,
    )

    # AC-137.4: Calculate realized gains per lot
    realized_st_gain = Decimal("0")
    realized_lt_gain = Decimal("0")
    lot_details: list[LotDetail] = []

    for lot, qty in selected:
        # Create a temporary closed-state view for gain calculation
        gain_result = calculate_realized_gain(lot, sale_price)
        # Scale gain by the fraction of the lot being sold
        fraction = Decimal(str(qty)) / Decimal(str(lot.quantity))
        scaled_gain = (gain_result.gain_amount * fraction).quantize(Decimal("0.01"))

        if gain_result.is_long_term:
            realized_lt_gain += scaled_gain
        else:
            realized_st_gain += scaled_gain

        # Enrich lot detail
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
        is_lt = holding_days >= 366
        days_to_lt = max(0, 366 - holding_days)

        lot_details.append(
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

    # AC-137.5: Tax estimates
    state_rate = Decimal(str(tax_profile.state_tax_rate))

    # ST tax: marginal rate × ST gain
    if realized_st_gain > 0:
        federal_st_rate = compute_marginal_rate(
            tax_profile.agi_estimate,
            tax_profile.filing_status,
            tax_profile.tax_year,
        )
        combined_st_rate = compute_combined_rate(federal_st_rate, state_rate)
        estimated_st_tax = (realized_st_gain * combined_st_rate).quantize(
            Decimal("0.01")
        )
    else:
        estimated_st_tax = Decimal("0")

    # LT tax: LTCG preferential rate
    if realized_lt_gain > 0:
        estimated_lt_tax_federal = compute_capital_gains_tax(
            realized_lt_gain,
            tax_profile.agi_estimate,
            tax_profile.filing_status,
            tax_profile.tax_year,
        )
        estimated_lt_tax_state = (realized_lt_gain * state_rate).quantize(
            Decimal("0.01")
        )
        estimated_lt_tax = estimated_lt_tax_federal + estimated_lt_tax_state
    else:
        estimated_lt_tax = Decimal("0")

    # AC-137.7: NIIT
    total_gain = realized_st_gain + realized_lt_gain
    niit_result = compute_niit(
        tax_profile.agi_estimate,
        total_gain if total_gain > 0 else Decimal("0"),
        tax_profile.filing_status,
    )
    estimated_niit = niit_result.niit_amount

    # AC-137.8: Total
    total_estimated_tax = estimated_st_tax + estimated_lt_tax + estimated_niit

    # AC-137.6: Wash sale detection — check each selected lot for risk
    wash_warnings: list[WashSaleMatch] = []
    now = datetime.now(tz=timezone.utc)
    for lot, qty in selected:
        # Simulate the lot as if it were closed today (hypothetical sale date)
        simulated_lot = TaxLot(
            lot_id=lot.lot_id,
            account_id=lot.account_id,
            ticker=lot.ticker,
            open_date=lot.open_date,
            close_date=now,  # Hypothetical sale date for simulation
            quantity=qty,
            cost_basis=lot.cost_basis,
            proceeds=sale_price,
            wash_sale_adjustment=lot.wash_sale_adjustment,
            is_closed=True,
            linked_trade_ids=list(lot.linked_trade_ids),
        )
        # Only check if the lot has a loss
        gain_per_share = sale_price - (lot.cost_basis + lot.wash_sale_adjustment)
        if gain_per_share < 0:
            matches = detect_wash_sales(
                simulated_lot,
                ticker_lots,
                wash_sale_method=tax_profile.wash_sale_method,
            )
            wash_warnings.extend(matches)

    return TaxImpactResult(
        lots_selected=lot_details,
        realized_st_gain=realized_st_gain,
        realized_lt_gain=realized_lt_gain,
        estimated_st_tax=estimated_st_tax,
        estimated_lt_tax=estimated_lt_tax,
        estimated_niit=estimated_niit,
        total_estimated_tax=total_estimated_tax,
        wash_sale_warnings=wash_warnings,
    )
