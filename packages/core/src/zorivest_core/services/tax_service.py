# packages/core/src/zorivest_core/services/tax_service.py
"""Tax calculation service — lot management and gains calculation.

MEU-125: Tax lot tracking (get_lots, close_lot, reassign_basis).
MEU-126: Gains calculation (simulate_impact) — added in Tasks 7-8.
MEU-145: Quarterly estimate orchestration + record_payment (Phase 3D).
MEU-150: YTD tax summary dashboard composition (Phase 3E).

Spec: 03-service-layer.md §TaxService
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

from zorivest_core.domain.entities import QuarterlyEstimate, TaxLot, TaxProfile
from zorivest_core.domain.enums import (
    AccountType,
    CostBasisMethod,
    TradeAction,
    WashSaleMatchingMethod,
    WashSaleStatus,
)
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
from zorivest_core.domain.tax.wash_sale import WashSaleChain
from zorivest_core.domain.tax.wash_sale_chain_manager import WashSaleChainManager
from zorivest_core.domain.tax.wash_sale_detector import (
    WashSaleMatch,
    detect_wash_sales,
)
from zorivest_core.domain.tax.wash_sale_warnings import (
    WarningType,
    WashSaleWarning,
    check_conflicts,
)
from zorivest_core.domain.tax.ytd_pnl import (
    YtdPnlResult as YtdPnlResult,
    compute_ytd_pnl,
)
from zorivest_core.domain.tax.brackets import compute_tax_liability
from zorivest_core.domain.tax.niit import compute_niit
from zorivest_core.domain.tax.quarterly import (
    compute_safe_harbor,
    get_quarterly_due_dates,
    compute_annualized_installment,
)

if TYPE_CHECKING:
    from zorivest_core.application.ports import UnitOfWork

# ── Result types ─────────────────────────────────────────────────────────


@dataclass(frozen=True)
class QuarterlyEstimateResult:
    """Result of TaxService.quarterly_estimate() orchestration.

    Combines safe harbor or annualized computation with due date
    and penalty estimation per the 04f-api-tax.md contract.

    Fields match the API response shape: required/paid/due/penalty/due_date.
    Before MEU-148 persistence, paid=0 and penalty=0.
    """

    quarter: int
    tax_year: int
    required_amount: Decimal
    due_date: date
    method: (
        str  # "safe_harbor_100" | "safe_harbor_110" | "current_year_90" | "annualized"
    )
    paid: Decimal  # Decimal("0") until MEU-148 persistence
    due: Decimal  # = required_amount - paid
    penalty: Decimal  # Decimal("0") until MEU-148 payment tracking


@dataclass(frozen=True)
class YtdTaxSummary:
    """Year-to-date tax dashboard summary.

    MEU-150: Composes multiple TaxService queries into a single result
    for the /tax/ytd-summary REST endpoint and MCP ytd_summary tool.

    Spec: 05h-mcp-tax.md lines 397-404.
    """

    realized_st_gain: Decimal
    realized_lt_gain: Decimal
    total_realized: Decimal
    wash_sale_adjustments: Decimal
    trades_count: int
    estimated_federal_tax: Decimal
    estimated_state_tax: Decimal
    quarterly_payments: list[dict]  # Q1-Q4 status dicts


@dataclass(frozen=True)
class DeferredLossReport:
    """Deferred loss carryover report.

    MEU-151: Surfaces wash sale chain data with real vs reported P&L delta.
    Spec: build-priority-matrix.md item 78.
    """

    trapped_chains: list[dict]  # Per-chain detail dicts
    total_deferred: Decimal  # Sum of ABSORBED chain disallowed amounts
    total_permanent_loss: Decimal  # Sum of DESTROYED chain amounts (IRA)
    real_pnl: Decimal  # Realized gains (unmodified)
    reported_pnl: Decimal  # Realized gains minus deferred losses


@dataclass(frozen=True)
class TaxAlphaReport:
    """Tax alpha savings summary.

    MEU-152: Compares actual tax outcome vs naive FIFO counterfactual
    and quantifies savings from lot optimization + loss harvesting.
    Spec: build-priority-matrix.md item 79.
    """

    actual_tax_estimate: Decimal
    naive_fifo_tax_estimate: Decimal
    tax_savings: Decimal  # naive - actual
    savings_from_lot_optimization: Decimal
    savings_from_harvesting: Decimal
    trades_optimized_count: int


@dataclass(frozen=True)
class AuditFinding:
    """Single audit finding from a transaction audit.

    MEU-153 AC-153.7: Each finding has type, severity, message, lot_id, details.
    """

    finding_type: str  # e.g. "missing_basis", "duplicate_lot"
    severity: str  # "error", "warning", "info"
    message: str
    lot_id: str
    details: dict  # Additional context


@dataclass(frozen=True)
class AuditReport:
    """Transaction audit report.

    MEU-153 AC-153.2: Contains findings[] and severity_summary.
    """

    findings: list[AuditFinding]
    severity_summary: dict[str, int]  # {"error": N, "warning": N, "info": N}


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
    AC-136.1: wash_sale_warnings and wait_days for pre-trade alerts.
    """

    lot_details: list[LotDetail]
    total_lt_gain: Decimal
    total_st_gain: Decimal
    estimated_tax: Decimal
    wash_risk: bool
    wash_sale_warnings: list[WashSaleWarning] = field(default_factory=list)
    wait_days: int = 0


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
        now: datetime | None = None,
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

        # AC-136.2/136.3: Pre-trade wash sale alert enrichment.
        # Sale-side logic: warn when the proposed sale produces a net loss
        # AND there are recent replacement purchases within the 30-day
        # pre-sale window (IRS 61-day rule, pre-sale half).
        # This is NOT the same as check_conflicts() which is purchase-side.
        pre_trade_warnings: list[WashSaleWarning] = []
        wait_days = 0
        if total_gain < Decimal("0"):
            effective_now = now if now is not None else datetime.now(tz=timezone.utc)
            selling_lot_ids = {lot.lot_id for lot, _ in selected}

            with self._uow:
                all_ticker_lots = self._uow.tax_lots.list_all_filtered(
                    ticker=ticker,
                )

            for candidate in all_ticker_lots:
                # Skip lots being sold in this simulation
                if candidate.lot_id in selling_lot_ids:
                    continue
                # AC-136.3: check if this lot was purchased within 30-day
                # pre-sale window (open_date is the purchase date)
                days_since_purchase = (effective_now - candidate.open_date).days
                if days_since_purchase < 0 or days_since_purchase > 30:
                    continue
                days_remaining = 30 - days_since_purchase

                pre_trade_warnings.append(
                    WashSaleWarning(
                        warning_type=WarningType.REBALANCE_CONFLICT,
                        ticker=ticker,
                        message=(
                            f"Recent purchase of {ticker} {days_since_purchase} "
                            f"days ago. Selling at a loss would trigger wash "
                            f"sale ({days_remaining} days remaining)."
                        ),
                        conflicting_lot_id=candidate.lot_id,
                        days_remaining=days_remaining,
                    )
                )

            # AC-136.4: wait_days = max days_remaining across all warnings
            wait_days = (
                max(w.days_remaining for w in pre_trade_warnings)
                if pre_trade_warnings
                else 0
            )

        # F3/AC-136.5: wash_risk from existing adjustments OR new warnings
        wash_risk = has_wash_risk or len(pre_trade_warnings) > 0

        return SimulationResult(
            lot_details=lot_details,
            total_lt_gain=total_lt,
            total_st_gain=total_st,
            estimated_tax=estimated_tax,
            wash_risk=wash_risk,
            wash_sale_warnings=pre_trade_warnings,
            wait_days=wait_days,
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

    # ── AC-135.4: Wash Sale Conflict Checking ────────────────────────────

    def check_wash_sale_conflicts(
        self,
        ticker: str,
        now: datetime | None = None,
        spousal_lot_ids: set[str] | None = None,
    ) -> list[WashSaleWarning]:
        """Check for wash sale conflicts before a trade.

        AC-135.4: Service-level method that loads lots from the UoW and
        delegates to the pure domain check_conflicts function.

        Args:
            ticker: The ticker symbol to check.
            now: Reference time for 30-day window (defaults to UTC now).
            spousal_lot_ids: Optional set of spousal lot IDs for spousal
                conflict detection.

        Returns:
            List of WashSaleWarning objects for any detected conflicts.
        """
        effective_now = now if now is not None else datetime.now(tz=timezone.utc)

        with self._uow:
            closed_lots = self._uow.tax_lots.list_all_filtered(
                ticker=ticker,
                is_closed=True,
            )

            # F4/AC-135.4: Wire TaxProfile.include_spousal_accounts
            current_year = effective_now.year
            profile = self._uow.tax_profiles.get_for_year(current_year)

        include_spousal = (
            profile.include_spousal_accounts if profile is not None else True
        )

        return check_conflicts(
            ticker=ticker,
            recent_losses=closed_lots,
            now=effective_now,
            spousal_lot_ids=spousal_lot_ids,
            include_spousal=include_spousal,
        )

    # ── AC-131.8: Wash Sale Integration ─────────────────────────────────

    def detect_and_apply_wash_sales(
        self,
        loss_lot_id: str,
    ) -> list[WashSaleMatch]:
        """Detect wash sales for a closed lot and create chains.

        AC-131.8: Orchestrates detection + chain creation + basis adjustment.

        Args:
            loss_lot_id: The lot ID that realized a loss.

        Returns:
            List of WashSaleMatch results.

        Raises:
            NotFoundError: If the lot doesn't exist.
            BusinessRuleError: If the lot is not closed or has no loss.
        """
        with self._uow:
            loss_lot = self._uow.tax_lots.get(loss_lot_id)
            if loss_lot is None:
                raise NotFoundError(f"TaxLot not found: {loss_lot_id}")

            if not loss_lot.is_closed:
                raise BusinessRuleError("Can only detect wash sales on closed lots")

            # MEU-134/133: Load TaxProfile for DRIP and method settings
            # Must load before candidate retrieval (F1 uses wash_method).
            current_year = datetime.now(tz=timezone.utc).year
            profile = self._uow.tax_profiles.get_for_year(current_year)
            include_drip = (
                profile.include_drip_wash_detection if profile is not None else True
            )
            wash_method = profile.wash_sale_method if profile is not None else None

            # F1: Broaden candidate retrieval for CONSERVATIVE option matching.
            # CONSERVATIVE mode checks options on the same underlying, so we
            # need all lots in the account (not just same ticker).
            # AGGRESSIVE mode uses exact ticker only.
            if (
                wash_method == WashSaleMatchingMethod.CONSERVATIVE
                or wash_method is None  # default = CONSERVATIVE
            ):
                all_lots = self._uow.tax_lots.list_all_filtered(
                    account_id=loss_lot.account_id,
                )
            else:
                all_lots = self._uow.tax_lots.list_all_filtered(
                    ticker=loss_lot.ticker,
                )
            candidates = [lot for lot in all_lots if lot.lot_id != loss_lot.lot_id]

            detect_kwargs: dict = {"include_drip": include_drip}
            if wash_method is not None:
                detect_kwargs["wash_sale_method"] = wash_method

            matches = detect_wash_sales(loss_lot, candidates, **detect_kwargs)

            if matches:
                total_disallowed = sum((m.disallowed_loss for m in matches), Decimal(0))
                mgr = WashSaleChainManager()
                chain = mgr.start_chain(loss_lot, total_disallowed)

                # Absorb into each replacement lot with per-match amount
                for match in matches:
                    repl_lot = self._uow.tax_lots.get(match.replacement_lot_id)
                    if repl_lot is not None:
                        updated = mgr.absorb_loss(
                            chain, repl_lot, amount=match.disallowed_loss
                        )
                        self._uow.tax_lots.update(updated)

                self._uow.wash_sale_chains.save(chain)
                self._uow.commit()

            return matches

    def get_trapped_losses(self) -> list[WashSaleChain]:
        """AC-131.7: Return all wash sale chains with trapped (ABSORBED) losses.

        Returns:
            List of WashSaleChain objects in ABSORBED status.
        """
        from zorivest_core.domain.enums import WashSaleStatus

        with self._uow:
            return self._uow.wash_sale_chains.list_active(
                status=WashSaleStatus.ABSORBED
            )

    # ── AC-132.5: Cross-Account Wash Sale Scan ─────────────────────────

    def scan_cross_account_wash_sales(
        self,
        tax_year: int,
        include_spousal: bool = True,
    ) -> list[WashSaleMatch]:
        """AC-132.5 + AC-132.7: Scan all accounts for cross-account wash sale violations.

        Collects closed lots with losses from all accounts in the filing scope
        and checks each against replacement purchases across all accounts.

        AC-132.3: When the replacement purchase is in an IRA (or other
        tax-advantaged account), the loss is permanently destroyed — no basis
        adjustment is applied. Taxable-to-taxable replacements receive the
        standard ABSORBED treatment with basis adjustment.

        Args:
            tax_year: The tax year to scan.
            include_spousal: If True, include spousal accounts in the scan.
                When False, spousal accounts are excluded (AC-132.7).

        Returns:
            List of all WashSaleMatch results found.
        """
        with self._uow:
            # Get all closed lots for the year
            all_closed = self._uow.tax_lots.list_all_filtered(is_closed=True)
            year_closed = [
                lot
                for lot in all_closed
                if lot.close_date is not None and lot.close_date.year == tax_year
            ]

            # Get all lots (open + closed) as candidates
            all_lots = self._uow.tax_lots.list_all_filtered()

            # AC-132.7: Filter out spousal accounts if not included
            if not include_spousal:
                spousal_account_ids = self._get_spousal_account_ids()
                year_closed = [
                    lot
                    for lot in year_closed
                    if lot.account_id not in spousal_account_ids
                ]
                all_lots = [
                    lot for lot in all_lots if lot.account_id not in spousal_account_ids
                ]

            # MEU-134/133: Load TaxProfile for DRIP and method settings
            current_year_profile = self._uow.tax_profiles.get_for_year(tax_year)
            include_drip = (
                current_year_profile.include_drip_wash_detection
                if current_year_profile is not None
                else True
            )
            wash_method = (
                current_year_profile.wash_sale_method
                if current_year_profile is not None
                else None
            )
            cross_detect_kwargs: dict = {"include_drip": include_drip}
            if wash_method is not None:
                cross_detect_kwargs["wash_sale_method"] = wash_method

            all_matches: list[WashSaleMatch] = []
            mgr = WashSaleChainManager()

            for loss_lot in year_closed:
                # Only process lots with actual losses
                if loss_lot.cost_basis <= loss_lot.proceeds:
                    continue

                candidates = [lot for lot in all_lots if lot.lot_id != loss_lot.lot_id]
                matches = detect_wash_sales(loss_lot, candidates, **cross_detect_kwargs)

                # AC-132.3: Route each match based on replacement account type
                for match in matches:
                    repl_lot = self._uow.tax_lots.get(match.replacement_lot_id)
                    if repl_lot is None:
                        continue

                    repl_account = self._uow.accounts.get(repl_lot.account_id)
                    # AC-132.3: Only IRA triggers permanent destruction.
                    # K401 destruction is deferred pending human approval.
                    is_ira = (
                        repl_account is not None
                        and repl_account.account_type == AccountType.IRA
                    )

                    chain = mgr.start_chain(loss_lot, match.disallowed_loss)

                    if is_ira:
                        # IRA replacement: loss permanently destroyed, no basis adjustment
                        mgr.destroy_chain(
                            chain,
                            lot_id=repl_lot.lot_id,
                            account_id=repl_lot.account_id,
                        )
                    else:
                        # Taxable replacement: absorb loss into replacement basis
                        updated = mgr.absorb_loss(
                            chain, repl_lot, amount=match.disallowed_loss
                        )
                        self._uow.tax_lots.update(updated)

                    self._uow.wash_sale_chains.save(chain)

                all_matches.extend(matches)

            if all_matches:
                self._uow.commit()

            return all_matches

    def _get_spousal_account_ids(self) -> set[str]:
        """Get account IDs tagged as spousal.

        Returns:
            Set of account_id strings belonging to the spouse.
        """
        accounts = self._uow.accounts.list_all()
        return {a.account_id for a in accounts if getattr(a, "is_spousal", False)}

    # ── AC-145.6: quarterly_estimate ────────────────────────────────────

    # API-facing method names per 04f-api-tax.md:121.
    # 'prior_year' maps to domain safe harbor. 'actual' requires MEU-148.
    _VALID_METHODS = frozenset({"annualized", "prior_year", "actual"})

    def quarterly_estimate(
        self,
        quarter: int,
        tax_year: int,
        method: str = "annualized",
    ) -> QuarterlyEstimateResult:
        """Compute quarterly estimated tax payment.

        AC-145.6: Orchestrates bracket + prior-year safe harbor or
        annualized computation using TaxProfile data. Returns the
        recommended payment for a specific quarter.

        Spec: 04f-api-tax.md §quarterly_estimate.

        The service accepts integer quarters (1-4). The API router
        (MEU-148+) converts Q1/Q2/Q3/Q4 string literals to ints.

        Args:
            quarter: Quarter number (1-4).
            tax_year: Calendar year for the estimate.
            method: Estimation method — "annualized" (default),
                "prior_year" (safe harbor), or "actual" (MEU-148).

        Returns:
            QuarterlyEstimateResult with required_amount, due_date,
            paid, due, penalty, and method label.

        Raises:
            BusinessRuleError: If quarter not in 1-4, invalid method,
                no TaxProfile exists, or 'actual' method invoked
                before MEU-148 persistence is available.
        """
        if not (1 <= quarter <= 4):
            raise BusinessRuleError(f"Invalid quarter {quarter}: must be 1-4")
        if method not in self._VALID_METHODS:
            raise BusinessRuleError(
                f"Invalid method '{method}': must be one of {sorted(self._VALID_METHODS)}"
            )
        if method == "actual":
            raise BusinessRuleError(
                "The 'actual' estimation method requires per-quarter "
                "income data (deferred to MEU-148 infrastructure wiring)"
            )

        with self._uow:
            profile = self._uow.tax_profiles.get_for_year(tax_year)

        if profile is None:
            raise BusinessRuleError(
                f"No TaxProfile found for tax year {tax_year}. "
                f"Create one first via the tax profile API."
            )

        # Resolve due date for this quarter
        due_dates = get_quarterly_due_dates(tax_year)
        due_date = due_dates[quarter - 1].due_date

        if method == "prior_year":
            return self._quarterly_prior_year(quarter, tax_year, profile, due_date)

        # Default: annualized
        return self._quarterly_annualized(quarter, tax_year, profile, due_date)

    def _quarterly_prior_year(
        self,
        quarter: int,
        tax_year: int,
        profile: TaxProfile,
        due_date: date,
    ) -> QuarterlyEstimateResult:
        """Prior-year safe harbor path — compute 90% current / 100-110% prior.

        API name: 'prior_year'. Domain: safe harbor calculator.
        """
        current_year_estimate = compute_tax_liability(
            profile.agi_estimate,
            profile.filing_status,
            tax_year,  # type: ignore[union-attr]
        )

        result = compute_safe_harbor(
            current_year_estimate=current_year_estimate,
            prior_year_tax=profile.prior_year_tax,  # type: ignore[union-attr]
            agi=profile.agi_estimate,  # type: ignore[union-attr]
            filing_status=profile.filing_status,  # type: ignore[union-attr]
        )

        return QuarterlyEstimateResult(
            quarter=quarter,
            tax_year=tax_year,
            required_amount=result.quarterly_payment,
            due_date=due_date,
            method=result.method,
            paid=Decimal("0"),
            due=result.quarterly_payment,
            penalty=Decimal("0"),
        )

    def _quarterly_annualized(
        self,
        quarter: int,
        tax_year: int,
        profile: TaxProfile,
        due_date: date,
    ) -> QuarterlyEstimateResult:
        """Annualized income method — assumes even income distribution.

        Uses uniform quarterly income derived from AGI / 4 as a default
        when per-quarter income data is not yet available (requires
        MEU-148 persistence).
        """
        # Default: divide AGI evenly across 4 quarters
        quarterly_income = (profile.agi_estimate / 4).quantize(Decimal("0.01"))  # type: ignore[union-attr]
        quarterly_incomes = [quarterly_income] * 4

        annualized = compute_annualized_installment(
            quarterly_incomes=quarterly_incomes,
            filing_status=profile.filing_status,  # type: ignore[union-attr]
            tax_year=tax_year,
        )

        return QuarterlyEstimateResult(
            quarter=quarter,
            tax_year=tax_year,
            required_amount=annualized.installments[quarter - 1],
            due_date=due_date,
            method="annualized",
            paid=Decimal("0"),
            due=annualized.installments[quarter - 1],
            penalty=Decimal("0"),
        )

    # ── AC-150: ytd_summary ──────────────────────────────────────────────

    def ytd_summary(
        self,
        tax_year: int,
        account_id: str | None = None,
    ) -> YtdTaxSummary:
        """Compose a year-to-date tax dashboard summary.

        AC-150.1: Accepts tax_year and optional account_id.
        AC-150.2: Returns YtdTaxSummary with 8 fields.
        AC-150.3: Composes get_ytd_pnl, get_taxable_gains, get_trapped_losses.
        AC-150.4: Tax estimates via compute_tax_liability + NIIT.
        AC-150.5: Q1-Q4 payment status from QuarterlyEstimate records.
        AC-150.6: Empty portfolio returns zeroed summary.

        Args:
            tax_year: Calendar year for the summary.
            account_id: Optional filter to a single account.

        Returns:
            YtdTaxSummary with realized gains, tax estimates, and Q1-Q4 status.
        """
        # ── Step 1: Gather closed lots for the year ──
        with self._uow:
            closed_lots = self._uow.tax_lots.list_all_filtered(is_closed=True)
            profile = self._uow.tax_profiles.get_for_year(tax_year)

            # Filter to target year
            year_lots = [
                lot
                for lot in closed_lots
                if lot.close_date is not None and lot.close_date.year == tax_year
            ]

            # Optional account filter
            if account_id is not None:
                year_lots = [lot for lot in year_lots if lot.account_id == account_id]

            # Exclude tax-advantaged accounts
            taxable_lots = []
            for lot in year_lots:
                account = self._uow.accounts.get(lot.account_id)
                if account is not None and account.is_tax_advantaged:
                    continue
                taxable_lots.append(lot)

            # ── Step 2: Compute realized gains (ST/LT) ──
            total_st = Decimal("0")
            total_lt = Decimal("0")

            for lot in taxable_lots:
                gain_result = calculate_realized_gain(lot, lot.proceeds)
                if gain_result.is_long_term:
                    total_lt += gain_result.gain_amount
                else:
                    total_st += gain_result.gain_amount

            # ── Step 3: Wash sale adjustments ──
            trapped = self._uow.wash_sale_chains.list_active(
                status=WashSaleStatus.ABSORBED
            )
            wash_adjustments = sum(
                (chain.disallowed_amount for chain in trapped), Decimal(0)
            )

            # ── Step 4: Tax estimates ──
            estimated_federal = Decimal("0")
            estimated_state = Decimal("0")

            if profile is not None:
                total_gain = total_st + total_lt
                if total_gain > Decimal("0"):
                    # Federal: marginal rate on gains
                    estimated_federal = (
                        total_gain * Decimal(str(profile.federal_bracket))
                    ).quantize(Decimal("0.01"))

                    # NIIT check — add if applicable
                    niit_result = compute_niit(
                        magi=profile.agi_estimate,
                        net_investment_income=total_gain,
                        filing_status=profile.filing_status,
                    )
                    estimated_federal = estimated_federal + niit_result.niit_amount

                    # State tax
                    estimated_state = (
                        total_gain * Decimal(str(profile.state_tax_rate))
                    ).quantize(Decimal("0.01"))

            # ── Step 5: Quarterly payments ──
            quarterly_estimates = self._uow.quarterly_estimates.list_for_year(tax_year)
            estimate_map = {e.quarter: e for e in quarterly_estimates}

        quarterly_payments: list[dict] = []
        for q in range(1, 5):
            if q in estimate_map:
                est = estimate_map[q]
                quarterly_payments.append(
                    {
                        "quarter": q,
                        "required": est.required_payment,
                        "paid": est.actual_payment,
                        "due": est.required_payment - est.actual_payment,
                    }
                )
            else:
                quarterly_payments.append(
                    {
                        "quarter": q,
                        "required": Decimal("0"),
                        "paid": Decimal("0"),
                        "due": Decimal("0"),
                    }
                )

        return YtdTaxSummary(
            realized_st_gain=total_st,
            realized_lt_gain=total_lt,
            total_realized=total_st + total_lt,
            wash_sale_adjustments=wash_adjustments,
            trades_count=len(taxable_lots),
            estimated_federal_tax=estimated_federal,
            estimated_state_tax=estimated_state,
            quarterly_payments=quarterly_payments,
        )

    # ── AC-151: deferred_loss_report ─────────────────────────────────────

    def deferred_loss_report(
        self,
        tax_year: int | None = None,
    ) -> DeferredLossReport:
        """Generate a deferred loss carryover report.

        AC-151.1: Accepts optional tax_year.
        AC-151.2: Returns DeferredLossReport with chain details.
        AC-151.3: Uses get_trapped_losses + lot enrichment.
        AC-151.4: Computes real vs reported P&L delta.
        AC-151.5: Empty result when no trapped chains.

        Args:
            tax_year: Optional filter — when set, only include chains
                whose loss_date falls in this year.

        Returns:
            DeferredLossReport with chain details and P&L delta.
        """
        with self._uow:
            # Load all chains (ABSORBED + DESTROYED)
            absorbed = self._uow.wash_sale_chains.list_active(
                status=WashSaleStatus.ABSORBED
            )
            destroyed = self._uow.wash_sale_chains.list_active(
                status=WashSaleStatus.DESTROYED
            )
            all_chains = absorbed + destroyed

            # Optional year filter
            if tax_year is not None:
                all_chains = [c for c in all_chains if c.loss_date.year == tax_year]
                absorbed = [
                    c for c in all_chains if c.status == WashSaleStatus.ABSORBED
                ]
                destroyed = [
                    c for c in all_chains if c.status == WashSaleStatus.DESTROYED
                ]

            # Build chain detail dicts
            trapped_chains: list[dict] = []
            for chain in all_chains:
                lot = self._uow.tax_lots.get(chain.loss_lot_id)
                trapped_chains.append(
                    {
                        "chain_id": chain.chain_id,
                        "loss_lot_id": chain.loss_lot_id,
                        "ticker": chain.ticker,
                        "original_loss": chain.loss_amount,
                        "deferred_amount": chain.disallowed_amount,
                        "chain_status": chain.status.value,
                        "loss_date": chain.loss_date.isoformat()
                        if chain.loss_date
                        else None,
                    }
                )

            # Compute totals
            total_deferred = sum((c.disallowed_amount for c in absorbed), Decimal(0))
            total_permanent = sum((c.disallowed_amount for c in destroyed), Decimal(0))

            # P&L delta: get realized gains
            closed_lots = self._uow.tax_lots.list_all_filtered(is_closed=True)

        # Filter by year if specified
        if tax_year is not None:
            closed_lots = [
                lot
                for lot in closed_lots
                if lot.close_date is not None and lot.close_date.year == tax_year
            ]

        real_pnl = Decimal("0")
        for lot in closed_lots:
            gain_result = calculate_realized_gain(lot, lot.proceeds)
            real_pnl += gain_result.gain_amount

        # reported_pnl = real gains - deferred losses (deferred losses reduce
        # what's "reported" because they are pushed forward)
        reported_pnl = real_pnl - total_deferred

        return DeferredLossReport(
            trapped_chains=trapped_chains,
            total_deferred=total_deferred,
            total_permanent_loss=total_permanent,
            real_pnl=real_pnl,
            reported_pnl=reported_pnl,
        )

    # ── AC-152: tax_alpha_report ───────────────────────────────────────

    def tax_alpha_report(self, tax_year: int) -> TaxAlphaReport:
        """Generate a tax alpha savings summary.

        AC-152.1: Accepts tax_year.
        AC-152.2: Returns TaxAlphaReport with 6 fields.
        AC-152.3: Counterfactual FIFO vs actual tax comparison.
        AC-152.4: Harvesting savings from executed losses.
        AC-152.5: Empty portfolio returns zeroed report.

        The "alpha" represents the tax savings achieved through
        intelligent lot selection (HIFO, tax-loss harvesting) vs
        a naive FIFO approach.

        Args:
            tax_year: Calendar year for the report.

        Returns:
            TaxAlphaReport with actual vs counterfactual tax comparison.
        """
        with self._uow:
            closed_lots = self._uow.tax_lots.list_all_filtered(is_closed=True)
            profile = self._uow.tax_profiles.get_for_year(tax_year)

            # Filter to target year
            year_lots = [
                lot
                for lot in closed_lots
                if lot.close_date is not None and lot.close_date.year == tax_year
            ]

            # Exclude tax-advantaged accounts
            taxable_lots = []
            for lot in year_lots:
                account = self._uow.accounts.get(lot.account_id)
                if account is not None and account.is_tax_advantaged:
                    continue
                taxable_lots.append(lot)

        if not taxable_lots:
            return TaxAlphaReport(
                actual_tax_estimate=Decimal("0"),
                naive_fifo_tax_estimate=Decimal("0"),
                tax_savings=Decimal("0"),
                savings_from_lot_optimization=Decimal("0"),
                savings_from_harvesting=Decimal("0"),
                trades_optimized_count=0,
            )

        # Determine combined tax rate
        if profile is not None:
            combined_rate = Decimal(
                str(profile.federal_bracket + profile.state_tax_rate)
            )
        else:
            combined_rate = Decimal("0")

        # ── Actual gains ──
        actual_gains = Decimal("0")
        gain_lots: list[TaxLot] = []  # Lots with positive gains
        loss_lots: list[TaxLot] = []  # Lots with losses (harvesting)
        optimized_count = 0

        for lot in taxable_lots:
            gain_result = calculate_realized_gain(lot, lot.proceeds)
            actual_gains += gain_result.gain_amount

            if gain_result.gain_amount < Decimal("0"):
                loss_lots.append(lot)
            else:
                gain_lots.append(lot)

            # Count lots that used non-FIFO methods as "optimized"
            if (
                lot.cost_basis_method is not None
                and lot.cost_basis_method != CostBasisMethod.FIFO
            ):
                optimized_count += 1

        actual_tax = (
            max(actual_gains * combined_rate, Decimal("0")).quantize(Decimal("0.01"))
            if combined_rate > 0
            else Decimal("0")
        )

        # ── FIFO counterfactual ──
        # For each non-FIFO closed lot, determine what gain FIFO
        # would have produced by selecting the oldest available lot
        # for that ticker instead. This requires fetching ALL lots
        # (open + closed) for tickers that have optimized sales.
        fifo_gains = actual_gains  # Start with actual gains

        # Collect tickers with non-FIFO sales for counterfactual
        non_fifo_tickers = {
            lot.ticker
            for lot in taxable_lots
            if lot.cost_basis_method is not None
            and lot.cost_basis_method != CostBasisMethod.FIFO
        }

        if non_fifo_tickers:
            for ticker in non_fifo_tickers:
                # Get ALL lots (open + closed) for this ticker
                all_ticker_lots = self._uow.tax_lots.list_all_filtered(ticker=ticker)
                # Exclude tax-advantaged accounts
                ticker_lots = [
                    tl
                    for tl in all_ticker_lots
                    if not getattr(
                        self._uow.accounts.get(tl.account_id),
                        "is_tax_advantaged",
                        False,
                    )
                ]
                # Sort by open_date for FIFO ordering
                ticker_lots.sort(
                    key=lambda tl: (
                        tl.open_date or datetime.min.replace(tzinfo=timezone.utc)
                    )
                )

                # Get closed non-FIFO lots for this ticker, sorted by
                # close_date (chronological sale order)
                non_fifo_closed = [
                    tl
                    for tl in taxable_lots
                    if tl.ticker == ticker
                    and tl.cost_basis_method is not None
                    and tl.cost_basis_method != CostBasisMethod.FIFO
                ]
                non_fifo_closed.sort(
                    key=lambda tl: (
                        tl.close_date or datetime.min.replace(tzinfo=timezone.utc)
                    )
                )

                # Track which lots FIFO has "used"
                fifo_used: set[str] = set()

                for sold_lot in non_fifo_closed:
                    # Find the oldest lot FIFO would have picked
                    fifo_pick = None
                    for candidate in ticker_lots:
                        if candidate.lot_id not in fifo_used:
                            fifo_pick = candidate
                            break

                    if fifo_pick is None or fifo_pick.lot_id == sold_lot.lot_id:
                        # No alternative lot or same lot → no delta
                        fifo_used.add(sold_lot.lot_id)
                        continue

                    fifo_used.add(fifo_pick.lot_id)

                    # Compute gain delta: FIFO gain - actual gain
                    actual_gain = calculate_realized_gain(
                        sold_lot, sold_lot.proceeds
                    ).gain_amount
                    # FIFO counterfactual: same proceeds, different basis
                    fifo_gain = (sold_lot.proceeds - fifo_pick.cost_basis) * Decimal(
                        str(sold_lot.quantity)
                    )
                    # Adjust fifo_gains: remove actual, add counterfactual
                    fifo_gains = fifo_gains - actual_gain + fifo_gain

        naive_fifo_tax = (
            max(fifo_gains * combined_rate, Decimal("0")).quantize(Decimal("0.01"))
            if combined_rate > 0
            else Decimal("0")
        )

        # ── Harvesting savings ──
        # Harvesting savings = absolute value of losses * tax rate
        total_harvested_losses = sum(
            (
                abs(calculate_realized_gain(lot, lot.proceeds).gain_amount)
                for lot in loss_lots
            ),
            Decimal(0),
        )
        harvesting_savings = (
            (total_harvested_losses * combined_rate).quantize(Decimal("0.01"))
            if combined_rate > 0
            else Decimal("0")
        )

        tax_savings = naive_fifo_tax - actual_tax
        lot_opt_savings = tax_savings - harvesting_savings
        # Clamp to non-negative
        lot_opt_savings = max(lot_opt_savings, Decimal("0"))

        return TaxAlphaReport(
            actual_tax_estimate=actual_tax,
            naive_fifo_tax_estimate=naive_fifo_tax,
            tax_savings=tax_savings,
            savings_from_lot_optimization=lot_opt_savings,
            savings_from_harvesting=harvesting_savings,
            trades_optimized_count=optimized_count,
        )

    # ── AC-153: run_audit ─────────────────────────────────────────────

    def run_audit(
        self,
        account_id: str | None = None,
        tax_year: int | None = None,
    ) -> AuditReport:
        """Run a transaction audit on tax lots.

        AC-153.1: Accepts optional account_id and tax_year.
        AC-153.2: Returns AuditReport with findings[] and severity_summary.
        AC-153.3: Missing basis check.
        AC-153.4: Duplicate lot check.
        AC-153.5: Orphaned lot check.
        AC-153.6: Invalid proceeds check.
        AC-153.7: Each finding has standard fields.

        Args:
            account_id: Optional filter to a single account.
            tax_year: Optional filter to a specific year.

        Returns:
            AuditReport with findings and severity counts.
        """
        with self._uow:
            all_lots = self._uow.tax_lots.list_all_filtered()

        # Apply filters
        lots = all_lots
        if account_id is not None:
            lots = [lot for lot in lots if lot.account_id == account_id]
        if tax_year is not None:
            lots = [
                lot
                for lot in lots
                if (lot.open_date is not None and lot.open_date.year == tax_year)
                or (lot.close_date is not None and lot.close_date.year == tax_year)
            ]

        findings: list[AuditFinding] = []

        # ── AC-153.3: Missing basis ──
        for lot in lots:
            if lot.cost_basis is None or lot.cost_basis == Decimal("0"):
                findings.append(
                    AuditFinding(
                        finding_type="missing_basis",
                        severity="error",
                        message=f"Lot {lot.lot_id} has zero or missing cost basis",
                        lot_id=lot.lot_id,
                        details={
                            "cost_basis": str(lot.cost_basis),
                            "ticker": lot.ticker,
                        },
                    )
                )

        # ── AC-153.4: Duplicate lots ──
        seen_keys: dict[tuple, str] = {}  # key → first lot_id
        for lot in lots:
            key = (lot.account_id, lot.ticker, lot.open_date, lot.quantity)
            if key in seen_keys:
                findings.append(
                    AuditFinding(
                        finding_type="duplicate_lot",
                        severity="warning",
                        message=(
                            f"Lot {lot.lot_id} appears to be a duplicate of "
                            f"{seen_keys[key]} (same account+ticker+open_date+quantity)"
                        ),
                        lot_id=lot.lot_id,
                        details={
                            "original_lot_id": seen_keys[key],
                            "ticker": lot.ticker,
                        },
                    )
                )
            else:
                seen_keys[key] = lot.lot_id

        # ── AC-153.5: Orphaned lots ──
        for lot in lots:
            if lot.is_closed and not lot.linked_trade_ids:
                findings.append(
                    AuditFinding(
                        finding_type="orphaned_lot",
                        severity="warning",
                        message=f"Closed lot {lot.lot_id} has no linked trades",
                        lot_id=lot.lot_id,
                        details={
                            "ticker": lot.ticker,
                            "close_date": str(lot.close_date),
                        },
                    )
                )

        # ── AC-153.6: Invalid proceeds ──
        for lot in lots:
            if (
                lot.is_closed
                and lot.proceeds is not None
                and lot.proceeds <= Decimal("0")
            ):
                findings.append(
                    AuditFinding(
                        finding_type="invalid_proceeds",
                        severity="error",
                        message=(
                            f"Closed lot {lot.lot_id} has zero or negative "
                            f"proceeds ({lot.proceeds})"
                        ),
                        lot_id=lot.lot_id,
                        details={"proceeds": str(lot.proceeds), "ticker": lot.ticker},
                    )
                )

        # Build severity summary
        summary = {"error": 0, "warning": 0, "info": 0}
        for f in findings:
            if f.severity in summary:
                summary[f.severity] += 1

        return AuditReport(findings=findings, severity_summary=summary)

    # ── AC-145.7 + AC-148.6: record_payment (persisted via QuarterlyEstimate)

    def record_payment(
        self,
        tax_year: int,
        quarter: int,
        amount: Decimal,
        payment_date: datetime | None = None,
    ) -> None:
        """Record an actual quarterly estimated tax payment.

        AC-145.7: Parameter validation.
        AC-148.6: Full persistence via QuarterlyEstimateRepository.

        If a QuarterlyEstimate record for (tax_year, quarter) already exists,
        updates actual_payment. Otherwise, creates a new record with the payment.

        Args:
            tax_year: Calendar year.
            quarter: Quarter number (1-4).
            amount: Payment amount (must be > 0).
            payment_date: When the payment was made (defaults to now).

        Raises:
            BusinessRuleError: If quarter not in 1-4 or amount <= 0.
        """
        if not (1 <= quarter <= 4):
            raise BusinessRuleError(f"Invalid quarter {quarter}: must be 1-4")
        if amount <= 0:
            raise BusinessRuleError(f"Invalid amount {amount}: must be > 0")

        with self._uow:
            existing = self._uow.quarterly_estimates.get_for_quarter(tax_year, quarter)
            if existing is not None:
                # Update existing record with new payment
                updated = QuarterlyEstimate(
                    id=existing.id,
                    tax_year=existing.tax_year,
                    quarter=existing.quarter,
                    due_date=existing.due_date,
                    required_payment=existing.required_payment,
                    actual_payment=amount,
                    method=existing.method,
                    cumulative_ytd_gains=existing.cumulative_ytd_gains,
                    underpayment_penalty_risk=existing.underpayment_penalty_risk,
                )
                self._uow.quarterly_estimates.update(updated)
            else:
                # Create new record — get_quarterly_due_dates is
                # already imported at module level (line 58).
                due_dates = get_quarterly_due_dates(tax_year)
                due_dt = datetime.combine(
                    due_dates[quarter - 1].due_date,
                    datetime.min.time(),
                    tzinfo=timezone.utc,
                )
                new_estimate = QuarterlyEstimate(
                    id=0,  # Auto-increment
                    tax_year=tax_year,
                    quarter=quarter,
                    due_date=due_dt,
                    required_payment=Decimal("0"),
                    actual_payment=amount,
                    method="annualized",
                    cumulative_ytd_gains=Decimal("0"),
                    underpayment_penalty_risk=Decimal("0"),
                )
                self._uow.quarterly_estimates.save(new_estimate)
            self._uow.commit()
