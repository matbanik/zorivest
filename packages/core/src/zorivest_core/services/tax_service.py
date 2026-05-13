# packages/core/src/zorivest_core/services/tax_service.py
"""Tax calculation service — lot management and gains calculation.

MEU-125: Tax lot tracking (get_lots, close_lot, reassign_basis).
MEU-126: Gains calculation (simulate_impact) — added in Tasks 7-8.

Spec: 03-service-layer.md §TaxService
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

from zorivest_core.domain.entities import TaxLot
from zorivest_core.domain.enums import CostBasisMethod, TradeAction
from zorivest_core.domain.exceptions import BusinessRuleError, NotFoundError
from zorivest_core.domain.tax.lot_selector import select_lots_for_closing
from zorivest_core.domain.tax.gains_calculator import (
    calculate_realized_gain,
)
from zorivest_core.domain.tax.loss_carryforward import (
    apply_capital_loss_rules,
)
from zorivest_core.domain.tax.option_pairing import (
    AssignmentType,
    adjust_basis_for_assignment,
)
from zorivest_core.domain.tax.ytd_pnl import (
    YtdPnlResult as YtdPnlResult,
    compute_ytd_pnl,
)

if TYPE_CHECKING:
    from zorivest_core.application.ports import UnitOfWork

# T+1 settlement window for basis reassignment (domain-model-reference.md C5)
_T_PLUS_1_HOURS = 24

# Mapping from API status string to internal is_closed filter
_STATUS_MAP: dict[str, bool | None] = {
    "open": False,
    "closed": True,
    "all": None,
}

# Supported sort_by fields
_SORT_KEY_MAP = {
    "acquired_date": lambda lot: lot.open_date,
    "cost_basis": lambda lot: lot.cost_basis,
}


# ── Result types for simulate_impact ─────────────────────────────────────


@dataclass(frozen=True)
class LotDetail:
    """Per-lot detail in a tax simulation result."""

    lot_id: str
    quantity: float
    gain_amount: Decimal
    is_long_term: bool
    holding_period_days: int
    tax_type: str  # "short_term" | "long_term"


@dataclass(frozen=True)
class SimulationResult:
    """Result of simulate_impact — pre-trade what-if tax analysis.

    AC-126.4: lot-level close preview with ST/LT split, estimated tax, wash risk.
    """

    lot_details: list[LotDetail]
    total_lt_gain: Decimal
    total_st_gain: Decimal
    estimated_tax: Decimal
    wash_risk: bool


@dataclass(frozen=True)
class TaxableGainsResult:
    """Result of get_taxable_gains — annual taxable gains with carryforward.

    AC-127.4/127.5: ST/LT breakdown, deductible loss, remaining carryforward.
    """

    total_st_gain: Decimal
    total_lt_gain: Decimal
    deductible_loss: Decimal
    remaining_st_carryforward: Decimal
    remaining_lt_carryforward: Decimal


class TaxService:
    """Service orchestrating tax lot operations via UnitOfWork.

    AC-125.1: Constructor takes UnitOfWork.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    # ── AC-125.2: get_lots ──────────────────────────────────────────────

    def get_lots(
        self,
        account_id: str | None = None,
        ticker: str | None = None,
        status: str = "all",
        sort_by: str = "acquired_date",
    ) -> list[TaxLot]:
        """Return filtered, sorted TaxLot list.

        Args:
            account_id: Filter by account.
            ticker: Filter by ticker symbol.
            status: "open", "closed", or "all" (default).
            sort_by: "acquired_date" (default) or "cost_basis".

        Returns:
            List of matching TaxLot entities.
        """
        is_closed = _STATUS_MAP.get(status)

        with self._uow:
            lots = self._uow.tax_lots.list_filtered(
                account_id=account_id,
                ticker=ticker,
                is_closed=is_closed,
            )

        # Post-query sorting
        sort_fn = _SORT_KEY_MAP.get(sort_by, _SORT_KEY_MAP["acquired_date"])
        return sorted(lots, key=sort_fn)

    # ── AC-125.3: close_lot ─────────────────────────────────────────────

    def close_lot(self, lot_id: str, sell_trade_id: str | None = None) -> TaxLot:
        """Close a tax lot by linking it to a sell trade.

        When sell_trade_id is omitted (API canon: close_lot(lot_id)),
        auto-discovers the most recent matching SLD trade for the lot's
        account + ticker.

        The sell trade provides sale_price, close_date, and quantity.
        Zorivest imports trade results — it never executes trades.

        Args:
            lot_id: ID of the lot to close.
            sell_trade_id: Optional exec_id of the sell trade. If None,
                auto-discovers from trade history.

        Returns:
            The updated TaxLot entity with realized_gain_loss computed.

        Raises:
            NotFoundError: If lot_id or sell_trade_id not found.
            BusinessRuleError: If lot already closed, ticker mismatch,
                trade is not a sell, account mismatch, or quantity mismatch.
        """
        with self._uow:
            lot = self._uow.tax_lots.get(lot_id)
            if lot is None:
                raise NotFoundError(f"Tax lot '{lot_id}' not found")

            if lot.is_closed:
                raise BusinessRuleError(f"Tax lot '{lot_id}' is already closed")

            # R1: Auto-discover sell trade if not provided
            if sell_trade_id is not None:
                trade = self._uow.trades.get(sell_trade_id)
                if trade is None:
                    raise NotFoundError(f"Sell trade '{sell_trade_id}' not found")
            else:
                # Look up matching SLD trades for this lot's account+ticker
                all_trades = self._uow.trades.list_for_account(lot.account_id)
                candidates = [
                    t
                    for t in all_trades
                    if t.instrument == lot.ticker and t.action == TradeAction.SLD
                ]
                if not candidates:
                    raise BusinessRuleError(
                        f"No matching sell trade found for lot '{lot_id}' "
                        f"(account={lot.account_id}, ticker={lot.ticker})"
                    )
                # Use the most recent matching trade
                trade = sorted(candidates, key=lambda t: t.time, reverse=True)[0]

            # Validate trade.action is SLD (sell)
            if trade.action != TradeAction.SLD:
                raise BusinessRuleError(
                    f"Trade '{trade.exec_id}' is not a sell trade "
                    f"(action={trade.action})"
                )

            if trade.instrument != lot.ticker:
                raise BusinessRuleError(
                    f"Sell trade ticker '{trade.instrument}' does not match "
                    f"lot ticker '{lot.ticker}'"
                )

            # Validate account match
            if trade.account_id != lot.account_id:
                raise BusinessRuleError(
                    f"Sell trade account '{trade.account_id}' does not match "
                    f"lot account '{lot.account_id}'"
                )

            # RR2-1: Quantity validation with split-lot support
            # Spec: implementation-plan.md:67 — "Creates split lot"
            if trade.quantity > lot.quantity:
                raise BusinessRuleError(
                    f"Trade quantity ({trade.quantity}) exceeds "
                    f"lot quantity ({lot.quantity})"
                )

            # Partial close → create remainder lot before modifying the original
            if trade.quantity < lot.quantity:
                remainder_qty = lot.quantity - trade.quantity
                remainder_lot = TaxLot(
                    lot_id=f"{lot.lot_id}-R",
                    account_id=lot.account_id,
                    ticker=lot.ticker,
                    open_date=lot.open_date,
                    close_date=None,
                    quantity=remainder_qty,
                    cost_basis=lot.cost_basis,
                    proceeds=Decimal("0.00"),
                    wash_sale_adjustment=lot.wash_sale_adjustment,
                    is_closed=False,
                    linked_trade_ids=[],
                )
                self._uow.tax_lots.save(remainder_lot)

            # Derive close fields from the sell trade
            # Normalize trade.time to UTC-aware (SQLite strips tzinfo on storage)
            close_time = trade.time
            if close_time.tzinfo is None:
                close_time = close_time.replace(tzinfo=timezone.utc)
            lot.quantity = trade.quantity  # Narrow to sold portion
            lot.is_closed = True
            lot.close_date = close_time
            lot.proceeds = Decimal(str(trade.price))

            # Record the sell trade linkage
            if trade.exec_id not in lot.linked_trade_ids:
                lot.linked_trade_ids.append(trade.exec_id)

            # R2: Compute realized gain/loss using domain calculator
            gain_result = calculate_realized_gain(lot, Decimal(str(trade.price)))
            lot.realized_gain_loss = gain_result.gain_amount

            self._uow.tax_lots.update(lot)
            self._uow.commit()

        return lot

    # ── AC-125.4: reassign_basis ────────────────────────────────────────

    def reassign_basis(self, lot_id: str, method: CostBasisMethod) -> None:
        """Change cost basis method for a lot within T+1 settlement window.

        Args:
            lot_id: ID of the lot to reassign.
            method: New cost basis method.

        Raises:
            NotFoundError: If lot_id not found.
            BusinessRuleError: If outside T+1 window.
        """
        with self._uow:
            lot = self._uow.tax_lots.get(lot_id)
            if lot is None:
                raise NotFoundError(f"Tax lot '{lot_id}' not found")

            now = datetime.now(tz=timezone.utc)
            window_end = lot.open_date + timedelta(hours=_T_PLUS_1_HOURS)
            if now > window_end:
                raise BusinessRuleError(
                    f"Cannot reassign basis for lot '{lot_id}': "
                    f"T+1 settlement window expired"
                )

            # F3: Persist the method override on the lot entity
            lot.cost_basis_method = method

            self._uow.tax_lots.update(lot)
            self._uow.commit()

    # ── AC-126.4/126.5: simulate_impact ─────────────────────────────────

    def simulate_impact(
        self,
        account_id: str,
        ticker: str,
        quantity: float,
        sale_price: Decimal,
        method: CostBasisMethod,
        federal_rate: float = 0.0,
        state_rate: float = 0.0,
        lot_ids: list[str] | None = None,
    ) -> SimulationResult:
        """Pre-trade what-if tax simulation.

        AC-126.4: Returns lot-level close preview with ST/LT split,
        estimated tax, and wash risk flag.
        AC-126.5: Uses select_lots_for_closing + calculate_realized_gain.

        Args:
            account_id: Account to query lots from.
            ticker: Ticker symbol to simulate sale for.
            quantity: Number of shares to sell.
            sale_price: Expected per-share sale price.
            method: Cost basis lot selection method.
            federal_rate: Federal tax rate fallback (used if no TaxProfile).
            state_rate: State tax rate fallback (used if no TaxProfile).
            lot_ids: Explicit lot IDs for SPEC_ID method.

        Returns:
            SimulationResult with per-lot breakdown, tax estimate, and wash risk.

        Raises:
            BusinessRuleError: If no open lots for the ticker.
        """
        with self._uow:
            open_lots = self._uow.tax_lots.list_filtered(
                account_id=account_id,
                ticker=ticker,
                is_closed=False,
            )

            # F4: Look up TaxProfile for rates (current year)
            current_year = datetime.now(tz=timezone.utc).year
            profile = self._uow.tax_profiles.get_for_year(current_year)

        if not open_lots:
            raise BusinessRuleError(
                f"Account '{account_id}' has no open lots for '{ticker}'"
            )

        # Select lots using cost basis method
        kwargs: dict = (
            {"sale_price": sale_price}
            if method
            in (
                CostBasisMethod.MAX_LT_GAIN,
                CostBasisMethod.MAX_LT_LOSS,
                CostBasisMethod.MAX_ST_GAIN,
                CostBasisMethod.MAX_ST_LOSS,
            )
            else {}
        )
        if lot_ids:
            kwargs["lot_ids"] = lot_ids

        selected = select_lots_for_closing(open_lots, quantity, method, **kwargs)

        # Calculate gain/loss for each selected lot
        lot_details: list[LotDetail] = []
        total_lt = Decimal("0.00")
        total_st = Decimal("0.00")
        has_wash_risk = False

        for lot, qty in selected:
            gain_result = calculate_realized_gain(lot, sale_price)
            # Scale gain by proportion of lot being sold
            proportion = Decimal(str(qty)) / Decimal(str(lot.quantity))
            scaled_gain = gain_result.gain_amount * proportion

            detail = LotDetail(
                lot_id=lot.lot_id,
                quantity=qty,
                gain_amount=scaled_gain,
                is_long_term=gain_result.is_long_term,
                holding_period_days=gain_result.holding_period_days,
                tax_type=gain_result.tax_type,
            )
            lot_details.append(detail)

            if gain_result.is_long_term:
                total_lt += scaled_gain
            else:
                total_st += scaled_gain

            # F4: Detect wash sale risk — lot has existing wash adjustment
            if lot.wash_sale_adjustment > 0:
                has_wash_risk = True

        # Determine tax rates — prefer TaxProfile, fall back to explicit params
        if profile is not None:
            effective_federal = profile.federal_bracket
            effective_state = profile.state_tax_rate
        else:
            effective_federal = federal_rate
            effective_state = state_rate

        combined_rate = Decimal(str(effective_federal + effective_state))
        total_gain = total_lt + total_st
        estimated_tax = total_gain * combined_rate

        return SimulationResult(
            lot_details=lot_details,
            total_lt_gain=total_lt,
            total_st_gain=total_st,
            estimated_tax=estimated_tax,
            wash_risk=has_wash_risk,
        )

    # ── AC-127.4/127.5: get_taxable_gains ───────────────────────────────

    def get_taxable_gains(self, tax_year: int) -> TaxableGainsResult:
        """Compute taxable gains for a given year, excluding tax-advantaged accounts.

        AC-127.4: Excludes lots from accounts where is_tax_advantaged=True.
        AC-127.5: Applies carryforward from TaxProfile to net results.

        Human-approved: ST-first allocation for carryforward
        (conversation 65dc5cb3, 2026-05-12).

        Args:
            tax_year: The tax year to compute gains for.

        Returns:
            TaxableGainsResult with ST/LT breakdown and carryforward application.
        """
        with self._uow:
            # Get all closed lots — unpaginated for aggregate reporting (F1 fix)
            closed_lots = self._uow.tax_lots.list_all_filtered(is_closed=True)
            profile = self._uow.tax_profiles.get_for_year(tax_year)

            # Filter: only lots closed in the specified tax year
            year_lots = [
                lot
                for lot in closed_lots
                if lot.close_date is not None and lot.close_date.year == tax_year
            ]

            # AC-127.4: Exclude lots from tax-advantaged accounts
            taxable_lots = []
            for lot in year_lots:
                account = self._uow.accounts.get(lot.account_id)
                if account is not None and account.is_tax_advantaged:
                    continue
                taxable_lots.append(lot)

        # Aggregate ST/LT gains using the gains calculator
        total_st = Decimal("0")
        total_lt = Decimal("0")

        for lot in taxable_lots:
            gain_result = calculate_realized_gain(lot, lot.proceeds)
            if gain_result.is_long_term:
                total_lt += gain_result.gain_amount
            else:
                total_st += gain_result.gain_amount

        # AC-127.5: Apply carryforward if TaxProfile exists
        if profile is not None:
            # ST-first allocation: split single carryforward into ST first
            carryforward = profile.capital_loss_carryforward
            st_cf = carryforward  # All to ST first per Human-approved rule
            lt_cf = Decimal("0")

            loss_result = apply_capital_loss_rules(
                st_gains=total_st,
                lt_gains=total_lt,
                st_carryforward=st_cf,
                lt_carryforward=lt_cf,
                filing_status=profile.filing_status,
            )

            return TaxableGainsResult(
                total_st_gain=loss_result.net_st,
                total_lt_gain=loss_result.net_lt,
                deductible_loss=loss_result.deductible_loss,
                remaining_st_carryforward=loss_result.remaining_st_carryforward,
                remaining_lt_carryforward=loss_result.remaining_lt_carryforward,
            )
        else:
            # No profile — return raw gains, no carryforward
            return TaxableGainsResult(
                total_st_gain=max(total_st, Decimal("0")),
                total_lt_gain=max(total_lt, Decimal("0")),
                deductible_loss=Decimal("0"),
                remaining_st_carryforward=Decimal("0"),
                remaining_lt_carryforward=Decimal("0"),
            )

    # ── AC-128.6: pair_option_assignment ─────────────────────────────────

    def pair_option_assignment(
        self,
        lot_id: str,
        option_exec_id: str,
        assignment_type: AssignmentType,
    ) -> None:
        """Pair an option trade to a stock lot, adjusting cost basis or proceeds.

        AC-128.6: Persists adjusted basis and links trades for all four
        IRS scenarios. Side derived from loaded option trade's action.

        Args:
            lot_id: ID of the stock TaxLot.
            option_exec_id: exec_id of the option Trade.
            assignment_type: Which IRS adjustment path to apply.

        Raises:
            NotFoundError: If lot_id or option_exec_id not found.
            BusinessRuleError: If action/assignment_type mismatch or ticker mismatch.
        """
        with self._uow:
            lot = self._uow.tax_lots.get(lot_id)
            if lot is None:
                raise NotFoundError(f"Tax lot '{lot_id}' not found")

            option_trade = self._uow.trades.get(option_exec_id)
            if option_trade is None:
                raise NotFoundError(
                    f"Option trade (option exec) '{option_exec_id}' not found"
                )

            result = adjust_basis_for_assignment(lot, option_trade, assignment_type)

            # Persist adjusted values on the lot
            lot.cost_basis = result.adjusted_cost_basis
            lot.proceeds = result.adjusted_proceeds

            # Link option trade to lot
            if option_trade.exec_id not in lot.linked_trade_ids:
                lot.linked_trade_ids.append(option_trade.exec_id)

            self._uow.tax_lots.update(lot)
            self._uow.commit()

    # ── AC-129.4: get_ytd_pnl ───────────────────────────────────────────

    def get_ytd_pnl(self, tax_year: int) -> YtdPnlResult:
        """Compute YTD P&L by symbol for a given tax year.

        AC-129.4: Filters tax-advantaged accounts and delegates to
        compute_ytd_pnl domain function.

        Args:
            tax_year: The year to compute P&L for.

        Returns:
            YtdPnlResult with per-symbol breakdown and totals.
        """
        with self._uow:
            closed_lots = self._uow.tax_lots.list_all_filtered(is_closed=True)

            # Filter to target year
            year_lots = [
                lot
                for lot in closed_lots
                if lot.close_date is not None and lot.close_date.year == tax_year
            ]

            # Exclude tax-advantaged accounts (same as get_taxable_gains)
            taxable_lots = []
            for lot in year_lots:
                account = self._uow.accounts.get(lot.account_id)
                if account is not None and account.is_tax_advantaged:
                    continue
                taxable_lots.append(lot)

        return compute_ytd_pnl(taxable_lots, tax_year)
