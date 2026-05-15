# tests/unit/test_tax_ytd_summary.py
"""FIC tests for TaxService.ytd_summary() — MEU-150 ACs 150.1–150.6.

Feature Intent Contract:
  ytd_summary(tax_year, account_id=None) → YtdTaxSummary
  Composes: get_ytd_pnl, get_taxable_gains, get_trapped_losses,
            compute_tax_liability, compute_niit, quarterly_estimate.

Acceptance Criteria:
  AC-150.1: Method accepts tax_year: int and optional account_id: str | None
             Source: Spec: 04f-api-tax.md line 156–159
  AC-150.2: Returns YtdTaxSummary dataclass with 8 fields
             Source: Spec: 05h-mcp-tax.md lines 397–404
  AC-150.3: Composes get_ytd_pnl, get_taxable_gains, get_trapped_losses
             Source: Local Canon: existing TaxService methods
  AC-150.4: Tax estimates use compute_tax_liability + NIIT threshold check
             Source: Local Canon: MEU-146 (marginal_tax_calc), MEU-147 (niit_alert)
  AC-150.5: Quarterly payments section shows Q1–Q4 status
             Source: Spec: 05h-mcp-tax.md line 404
  AC-150.6: Empty portfolio returns zeroed summary (no errors)
             Source: Local Canon: established empty-result pattern

All tests use mocked UoW — no database access.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock


from zorivest_core.domain.entities import TaxLot, TaxProfile, QuarterlyEstimate
from zorivest_core.domain.enums import (
    CostBasisMethod,
    FilingStatus,
    WashSaleMatchingMethod,
)
from zorivest_core.services.tax_service import TaxService, YtdTaxSummary


# ── Helpers ──────────────────────────────────────────────────────────────


def _closed_lot(
    lot_id: str = "L1",
    ticker: str = "AAPL",
    account_id: str = "ACC-1",
    cost_basis: Decimal = Decimal("100.00"),
    quantity: float = 100.0,
    proceeds: Decimal = Decimal("150.00"),
    open_date: datetime | None = None,
    close_date: datetime | None = None,
    wash_sale_adjustment: Decimal = Decimal("0.00"),
) -> TaxLot:
    return TaxLot(
        lot_id=lot_id,
        account_id=account_id,
        ticker=ticker,
        open_date=open_date or datetime(2023, 1, 1, tzinfo=timezone.utc),
        close_date=close_date or datetime(2026, 6, 1, tzinfo=timezone.utc),
        quantity=quantity,
        cost_basis=cost_basis,
        proceeds=proceeds,
        wash_sale_adjustment=wash_sale_adjustment,
        is_closed=True,
        linked_trade_ids=[],
        realized_gain_loss=(proceeds - cost_basis) * Decimal(str(quantity)),
    )


def _profile(
    tax_year: int = 2026,
    agi: Decimal = Decimal("300000"),
    prior_year_tax: Decimal = Decimal("50000"),
) -> TaxProfile:
    return TaxProfile(
        id=1,
        filing_status=FilingStatus.SINGLE,
        tax_year=tax_year,
        federal_bracket=0.32,
        state_tax_rate=0.06,
        state="NY",
        prior_year_tax=prior_year_tax,
        agi_estimate=agi,
        capital_loss_carryforward=Decimal("0"),
        wash_sale_method=WashSaleMatchingMethod.CONSERVATIVE,
        default_cost_basis=CostBasisMethod.FIFO,
    )


def _quarterly_estimate(
    quarter: int = 1,
    tax_year: int = 2026,
    actual_payment: Decimal = Decimal("5000"),
    required_payment: Decimal = Decimal("12500"),
) -> QuarterlyEstimate:
    return QuarterlyEstimate(
        id=quarter,
        tax_year=tax_year,
        quarter=quarter,
        due_date=datetime(2026, 4, 15, tzinfo=timezone.utc),
        required_payment=required_payment,
        actual_payment=actual_payment,
        method="annualized",
        cumulative_ytd_gains=Decimal("0"),
        underpayment_penalty_risk=Decimal("0"),
    )


def _mock_uow(
    lots: list[TaxLot] | None = None,
    profile: TaxProfile | None = None,
    quarterly_estimates: list[QuarterlyEstimate] | None = None,
    accounts: dict[str, bool] | None = None,
) -> MagicMock:
    """Create a mock UnitOfWork with repos needed for ytd_summary."""
    uow = MagicMock()
    uow.__enter__ = MagicMock(return_value=uow)
    uow.__exit__ = MagicMock(return_value=False)

    # tax_lots repo
    lot_map = {lot.lot_id: lot for lot in (lots or [])}
    uow.tax_lots.get.side_effect = lambda lid: lot_map.get(lid)
    uow.tax_lots.list_filtered.return_value = lots or []
    uow.tax_lots.list_all_filtered.return_value = lots or []

    # accounts repo — for tax-advantaged filtering
    accounts_map = accounts or {}

    def _get_account(account_id: str) -> MagicMock | None:
        if account_id in accounts_map:
            acc = MagicMock()
            acc.account_id = account_id
            acc.is_tax_advantaged = accounts_map[account_id]
            return acc
        # Default: not tax-advantaged
        acc = MagicMock()
        acc.account_id = account_id
        acc.is_tax_advantaged = False
        return acc

    uow.accounts.get.side_effect = _get_account

    # tax_profiles repo
    uow.tax_profiles.get_for_year.return_value = profile

    # wash_sale_chains repo — for get_trapped_losses
    uow.wash_sale_chains.list_active.return_value = []

    # quarterly_estimates repo — for Q1–Q4 payment status
    uow.quarterly_estimates.list_for_year.return_value = quarterly_estimates or []

    return uow


# ── AC-150.1: Method signature ──────────────────────────────────────────


class TestYtdSummarySignature:
    """AC-150.1: ytd_summary accepts tax_year and optional account_id."""

    def test_accepts_tax_year_only(self) -> None:
        """AC-150.1: tax_year is required, account_id defaults to None."""
        uow = _mock_uow(profile=_profile())
        svc = TaxService(uow)
        result = svc.ytd_summary(tax_year=2026)
        assert result is not None

    def test_accepts_tax_year_and_account_id(self) -> None:
        """AC-150.1: Both tax_year and account_id accepted."""
        uow = _mock_uow(profile=_profile())
        svc = TaxService(uow)
        result = svc.ytd_summary(tax_year=2026, account_id="ACC-1")
        assert result is not None


# ── AC-150.2: Return type structure ─────────────────────────────────────


class TestYtdSummaryReturnType:
    """AC-150.2: Returns YtdTaxSummary with all 8 fields."""

    def test_returns_ytd_tax_summary_dataclass(self) -> None:
        """AC-150.2: Return type is YtdTaxSummary."""
        uow = _mock_uow(profile=_profile())
        svc = TaxService(uow)
        result = svc.ytd_summary(tax_year=2026)
        assert isinstance(result, YtdTaxSummary)

    def test_has_all_required_fields(self) -> None:
        """AC-150.2: All 8 fields are present."""
        lot = _closed_lot()
        uow = _mock_uow(lots=[lot], profile=_profile())
        svc = TaxService(uow)
        result = svc.ytd_summary(tax_year=2026)

        # Verify all 8 fields exist (access won't raise AttributeError)
        assert isinstance(result.realized_st_gain, Decimal)
        assert isinstance(result.realized_lt_gain, Decimal)
        assert isinstance(result.total_realized, Decimal)
        assert isinstance(result.wash_sale_adjustments, Decimal)
        assert isinstance(result.trades_count, int)
        assert isinstance(result.estimated_federal_tax, Decimal)
        assert isinstance(result.estimated_state_tax, Decimal)
        assert isinstance(result.quarterly_payments, list)


# ── AC-150.3: Composition ──────────────────────────────────────────────


class TestYtdSummaryComposition:
    """AC-150.3: Composes get_ytd_pnl, get_taxable_gains, get_trapped_losses."""

    def test_realized_gains_from_closed_lots(self) -> None:
        """AC-150.3: ST/LT gains come from get_ytd_pnl composition."""
        st_lot = _closed_lot(
            lot_id="L-ST",
            cost_basis=Decimal("100.00"),
            proceeds=Decimal("150.00"),
            quantity=100.0,
            # ST: opened recently
            open_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
            close_date=datetime(2026, 6, 1, tzinfo=timezone.utc),
        )
        lt_lot = _closed_lot(
            lot_id="L-LT",
            cost_basis=Decimal("80.00"),
            proceeds=Decimal("120.00"),
            quantity=50.0,
            # LT: opened > 1 year ago
            open_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            close_date=datetime(2026, 6, 1, tzinfo=timezone.utc),
        )
        uow = _mock_uow(lots=[st_lot, lt_lot], profile=_profile())
        svc = TaxService(uow)
        result = svc.ytd_summary(tax_year=2026)

        # ST gain = (150-100)*100 = 5000
        assert result.realized_st_gain == Decimal("5000.00")
        # LT gain = (120-80)*50 = 2000
        assert result.realized_lt_gain == Decimal("2000.00")
        assert result.total_realized == Decimal("7000.00")

    def test_wash_sale_adjustments_from_trapped_losses(self) -> None:
        """AC-150.3: wash_sale_adjustments from get_trapped_losses chains."""
        from zorivest_core.domain.tax.wash_sale import WashSaleChain
        from zorivest_core.domain.enums import WashSaleStatus

        chain = WashSaleChain(
            chain_id="WSC-1",
            ticker="AAPL",
            loss_lot_id="L1",
            loss_date=datetime(2026, 3, 1, tzinfo=timezone.utc),
            loss_amount=Decimal("1000.00"),
            disallowed_amount=Decimal("500.00"),
            status=WashSaleStatus.ABSORBED,
        )
        uow = _mock_uow(profile=_profile())
        uow.wash_sale_chains.list_active.return_value = [chain]
        svc = TaxService(uow)
        result = svc.ytd_summary(tax_year=2026)

        assert result.wash_sale_adjustments == Decimal("500.00")

    def test_trades_count_matches_lot_count(self) -> None:
        """AC-150.3: trades_count = number of closed lots in year."""
        lots = [_closed_lot(lot_id=f"L{i}") for i in range(3)]
        uow = _mock_uow(lots=lots, profile=_profile())
        svc = TaxService(uow)
        result = svc.ytd_summary(tax_year=2026)

        assert result.trades_count == 3


# ── AC-150.4: Tax estimates ─────────────────────────────────────────────


class TestYtdSummaryTaxEstimates:
    """AC-150.4: Uses compute_tax_liability + NIIT threshold check."""

    def test_federal_tax_estimate_nonzero_for_gains(self) -> None:
        """AC-150.4: Estimated federal tax computed for realized gains."""
        lot = _closed_lot(
            cost_basis=Decimal("100.00"),
            proceeds=Decimal("200.00"),
            quantity=100.0,
            open_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            close_date=datetime(2026, 6, 1, tzinfo=timezone.utc),
        )
        profile = _profile(agi=Decimal("300000"))
        uow = _mock_uow(lots=[lot], profile=profile)
        svc = TaxService(uow)
        result = svc.ytd_summary(tax_year=2026)

        # Should have some federal tax estimate
        assert result.estimated_federal_tax > Decimal("0")

    def test_state_tax_estimate_nonzero_for_gains(self) -> None:
        """AC-150.4: Estimated state tax computed from profile state_tax_rate."""
        lot = _closed_lot(
            cost_basis=Decimal("100.00"),
            proceeds=Decimal("200.00"),
            quantity=100.0,
            open_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            close_date=datetime(2026, 6, 1, tzinfo=timezone.utc),
        )
        profile = _profile(agi=Decimal("300000"))
        uow = _mock_uow(lots=[lot], profile=profile)
        svc = TaxService(uow)
        result = svc.ytd_summary(tax_year=2026)

        # Should have some state tax estimate
        assert result.estimated_state_tax > Decimal("0")

    def test_no_profile_returns_zero_tax_estimates(self) -> None:
        """AC-150.4 fallback: No TaxProfile → zero tax estimates."""
        lot = _closed_lot()
        uow = _mock_uow(lots=[lot], profile=None)
        svc = TaxService(uow)
        result = svc.ytd_summary(tax_year=2026)

        assert result.estimated_federal_tax == Decimal("0")
        assert result.estimated_state_tax == Decimal("0")


# ── AC-150.5: Quarterly payments ────────────────────────────────────────


class TestYtdSummaryQuarterlyPayments:
    """AC-150.5: Shows Q1–Q4 status with required/paid/due per quarter."""

    def test_quarterly_payments_has_4_entries(self) -> None:
        """AC-150.5: quarterly_payments list has exactly 4 entries."""
        estimates = [_quarterly_estimate(quarter=q) for q in range(1, 5)]
        uow = _mock_uow(profile=_profile(), quarterly_estimates=estimates)
        svc = TaxService(uow)
        result = svc.ytd_summary(tax_year=2026)

        assert len(result.quarterly_payments) == 4

    def test_quarterly_payments_reflects_actual_payments(self) -> None:
        """AC-150.5: Each entry shows actual payment amounts."""
        estimates = [
            _quarterly_estimate(quarter=1, actual_payment=Decimal("5000")),
            _quarterly_estimate(quarter=2, actual_payment=Decimal("3000")),
            _quarterly_estimate(quarter=3, actual_payment=Decimal("0")),
            _quarterly_estimate(quarter=4, actual_payment=Decimal("0")),
        ]
        uow = _mock_uow(profile=_profile(), quarterly_estimates=estimates)
        svc = TaxService(uow)
        result = svc.ytd_summary(tax_year=2026)

        # Q1 and Q2 have payments
        assert result.quarterly_payments[0]["paid"] == Decimal("5000")
        assert result.quarterly_payments[1]["paid"] == Decimal("3000")
        # Q3/Q4 unpaid
        assert result.quarterly_payments[2]["paid"] == Decimal("0")
        assert result.quarterly_payments[3]["paid"] == Decimal("0")

    def test_quarterly_payments_empty_when_no_estimates(self) -> None:
        """AC-150.5: No QuarterlyEstimate records → 4 zeroed entries."""
        uow = _mock_uow(profile=_profile())
        svc = TaxService(uow)
        result = svc.ytd_summary(tax_year=2026)

        assert len(result.quarterly_payments) == 4
        for entry in result.quarterly_payments:
            assert entry["paid"] == Decimal("0")
            assert entry["required"] == Decimal("0")


# ── AC-150.6: Empty portfolio ───────────────────────────────────────────


class TestYtdSummaryEmptyPortfolio:
    """AC-150.6: Empty portfolio returns zeroed summary."""

    def test_empty_portfolio_returns_zeros(self) -> None:
        """AC-150.6: No lots → all fields zero/empty."""
        uow = _mock_uow(lots=[], profile=_profile())
        svc = TaxService(uow)
        result = svc.ytd_summary(tax_year=2026)

        assert result.realized_st_gain == Decimal("0")
        assert result.realized_lt_gain == Decimal("0")
        assert result.total_realized == Decimal("0")
        assert result.wash_sale_adjustments == Decimal("0")
        assert result.trades_count == 0
        assert result.estimated_federal_tax == Decimal("0")
        assert result.estimated_state_tax == Decimal("0")
        assert len(result.quarterly_payments) == 4

    def test_empty_portfolio_no_exceptions(self) -> None:
        """AC-150.6: No errors raised for empty portfolio."""
        uow = _mock_uow(lots=[], profile=None)
        svc = TaxService(uow)
        # Should not raise
        result = svc.ytd_summary(tax_year=2026)
        assert result.total_realized == Decimal("0")
