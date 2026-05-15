# tests/unit/domain/tax/test_rate_comparison.py
"""FIC tests for rate_comparison — MEU-142 ACs 142.1–142.7.

Feature Intent Contract:
  StLtComparison frozen dataclass with 7 fields.
  compare_st_lt_tax(lot, sale_price, tax_profile) — computes
    ST vs LT tax comparison showing potential savings from
    holding a lot until it becomes long-term.

All tests are pure domain — no mocks, no I/O.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from zorivest_core.domain.entities import TaxLot, TaxProfile
from zorivest_core.domain.enums import (
    CostBasisMethod,
    FilingStatus,
    WashSaleMatchingMethod,
)

from zorivest_core.domain.tax.rate_comparison import (
    StLtComparison,
    compare_st_lt_tax,
)


# ── Helpers ──────────────────────────────────────────────────────────────


def _lot(
    lot_id: str = "L1",
    ticker: str = "AAPL",
    open_date: datetime | None = None,
    quantity: float = 100.0,
    cost_basis: Decimal = Decimal("100.00"),
    wash_sale_adjustment: Decimal = Decimal("0.00"),
    close_date: datetime | None = None,
) -> TaxLot:
    return TaxLot(
        lot_id=lot_id,
        account_id="ACC-1",
        ticker=ticker,
        open_date=open_date or datetime(2026, 3, 1, tzinfo=timezone.utc),
        close_date=close_date,
        quantity=quantity,
        cost_basis=cost_basis,
        proceeds=Decimal("0.00"),
        wash_sale_adjustment=wash_sale_adjustment,
        is_closed=False,
        linked_trade_ids=[],
    )


def _profile(
    filing_status: FilingStatus = FilingStatus.SINGLE,
    tax_year: int = 2026,
    agi_estimate: Decimal = Decimal("100000"),
    state_tax_rate: float = 0.0,
) -> TaxProfile:
    return TaxProfile(
        id=1,
        filing_status=filing_status,
        tax_year=tax_year,
        federal_bracket=0.22,
        state_tax_rate=state_tax_rate,
        state="TX",
        prior_year_tax=Decimal("0"),
        agi_estimate=agi_estimate,
        capital_loss_carryforward=Decimal("0"),
        wash_sale_method=WashSaleMatchingMethod.CONSERVATIVE,
        default_cost_basis=CostBasisMethod.FIFO,
    )


# ── AC-142.2: StLtComparison is frozen ────────────────────────────────


class TestStLtComparisonFrozen:
    """AC-142.2: StLtComparison must be a frozen dataclass."""

    def test_frozen(self) -> None:
        c = StLtComparison(
            tax_now=Decimal("100"),
            rate_now=Decimal("0.22"),
            tax_lt=Decimal("50"),
            rate_lt=Decimal("0.15"),
            days_remaining=100,
            tax_savings=Decimal("50"),
            holding_classification="short_term",
        )
        with pytest.raises(FrozenInstanceError):
            c.tax_now = Decimal("200")  # type: ignore[misc]


# ── AC-142.1: compare_st_lt_tax basic ─────────────────────────────────


class TestCompareStLtTax:
    """AC-142.1: compare_st_lt_tax returns StLtComparison."""

    def test_short_term_lot_shows_savings(self) -> None:
        """ST lot → tax_now > tax_lt → positive savings."""
        lot = _lot(
            "L1",
            cost_basis=Decimal("100.00"),
            quantity=100.0,
            open_date=datetime(2026, 3, 1, tzinfo=timezone.utc),
        )
        profile = _profile(agi_estimate=Decimal("100000"))
        result = compare_st_lt_tax(lot, Decimal("200.00"), profile)

        assert isinstance(result, StLtComparison)
        assert result.days_remaining > 0
        assert result.holding_classification == "short_term"
        # ST rate should be higher than LT rate for 100K income
        assert result.tax_now > result.tax_lt
        assert result.tax_savings > 0

    def test_already_long_term(self) -> None:
        """AC-142.1 negative: already LT → days_remaining == 0, savings == 0."""
        lot = _lot(
            "L1",
            cost_basis=Decimal("100.00"),
            quantity=100.0,
            open_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
        )
        profile = _profile(agi_estimate=Decimal("100000"))
        result = compare_st_lt_tax(lot, Decimal("200.00"), profile)

        assert result.days_remaining == 0
        assert result.tax_savings == Decimal("0")
        assert result.holding_classification == "long_term"


# ── AC-142.3: tax_now uses ST marginal rate ────────────────────────────


class TestTaxNowMarginalRate:
    """AC-142.3: tax_now uses compute_marginal_rate for ST gains."""

    def test_tax_now_uses_marginal_rate(self) -> None:
        """For $100K income SINGLE, marginal rate is 22%."""
        lot = _lot(
            cost_basis=Decimal("100.00"),
            quantity=100.0,
            open_date=datetime(2026, 3, 1, tzinfo=timezone.utc),
        )
        profile = _profile(
            filing_status=FilingStatus.SINGLE,
            agi_estimate=Decimal("100000"),
        )
        result = compare_st_lt_tax(lot, Decimal("200.00"), profile)

        # Gain = (200 - 100) * 100 = 10000
        # ST rate for $100K SINGLE = 22% (2026 brackets)
        # tax_now = 0.22 * 10000 = 2200
        assert result.rate_now == Decimal("0.22")
        assert result.tax_now == Decimal("2200.00")


# ── AC-142.4: tax_lt uses LTCG preferential rate ──────────────────────


class TestTaxLtPreferentialRate:
    """AC-142.4: tax_lt uses compute_capital_gains_tax."""

    def test_tax_lt_uses_ltcg_rate(self) -> None:
        """For $100K income SINGLE, LTCG rate is 15%."""
        lot = _lot(
            cost_basis=Decimal("100.00"),
            quantity=100.0,
            open_date=datetime(2026, 3, 1, tzinfo=timezone.utc),
        )
        profile = _profile(
            filing_status=FilingStatus.SINGLE,
            agi_estimate=Decimal("100000"),
        )
        result = compare_st_lt_tax(lot, Decimal("200.00"), profile)

        # LTCG for $100K SINGLE = 15%
        # tax_lt = 10000 * 0.15 = 1500
        assert result.rate_lt == Decimal("0.15")
        assert result.tax_lt == Decimal("1500.00")

    def test_zero_bracket_ltcg(self) -> None:
        """AC-142.4 negative: Low income → 0% LTCG bracket → tax_lt == 0."""
        lot = _lot(
            cost_basis=Decimal("100.00"),
            quantity=10.0,
            open_date=datetime(2026, 3, 1, tzinfo=timezone.utc),
        )
        profile = _profile(
            filing_status=FilingStatus.SINGLE,
            agi_estimate=Decimal("30000"),
        )
        result = compare_st_lt_tax(lot, Decimal("200.00"), profile)

        # LTCG 0% bracket for SINGLE ≤ ~$47K
        assert result.tax_lt == Decimal("0")


# ── AC-142.5: tax_savings ──────────────────────────────────────────────


class TestTaxSavings:
    """AC-142.5: tax_savings = tax_now - tax_lt."""

    def test_savings_positive(self) -> None:
        """Positive savings when waiting converts ST→LT."""
        lot = _lot(
            cost_basis=Decimal("100.00"),
            quantity=100.0,
            open_date=datetime(2026, 3, 1, tzinfo=timezone.utc),
        )
        profile = _profile(agi_estimate=Decimal("100000"))
        result = compare_st_lt_tax(lot, Decimal("200.00"), profile)

        assert result.tax_savings == result.tax_now - result.tax_lt
        assert result.tax_savings > 0

    def test_already_lt_savings_zero(self) -> None:
        """AC-142.5: Already LT → savings == 0."""
        lot = _lot(
            cost_basis=Decimal("100.00"),
            quantity=100.0,
            open_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
        )
        profile = _profile(agi_estimate=Decimal("100000"))
        result = compare_st_lt_tax(lot, Decimal("200.00"), profile)

        assert result.tax_savings == Decimal("0")


# ── AC-142.6: Negative gain ───────────────────────────────────────────


class TestNegativeGain:
    """AC-142.6: Unrealized loss → both taxes are 0, savings 0."""

    def test_loss_lot_all_zeros(self) -> None:
        lot = _lot(
            cost_basis=Decimal("200.00"),
            quantity=100.0,
            open_date=datetime(2026, 3, 1, tzinfo=timezone.utc),
        )
        profile = _profile(agi_estimate=Decimal("100000"))
        result = compare_st_lt_tax(lot, Decimal("150.00"), profile)

        assert result.tax_now == Decimal("0")
        assert result.tax_lt == Decimal("0")
        assert result.tax_savings == Decimal("0")


# ── AC-142.7: State tax inclusion ─────────────────────────────────────


class TestStateTaxInclusion:
    """AC-142.7: State tax included via compute_combined_rate."""

    def test_with_state_tax(self) -> None:
        """state_tax_rate > 0 → ST rate includes state."""
        lot = _lot(
            cost_basis=Decimal("100.00"),
            quantity=100.0,
            open_date=datetime(2026, 3, 1, tzinfo=timezone.utc),
        )
        profile = _profile(
            agi_estimate=Decimal("100000"),
            state_tax_rate=0.05,
        )
        result = compare_st_lt_tax(lot, Decimal("200.00"), profile)

        # 22% federal + 5% state = 27%
        assert result.rate_now == Decimal("0.27")
        # Gain = 10000, tax = 10000 * 0.27 = 2700
        assert result.tax_now == Decimal("2700.00")

    def test_without_state_tax(self) -> None:
        """state_tax_rate=0 → federal-only."""
        lot = _lot(
            cost_basis=Decimal("100.00"),
            quantity=100.0,
            open_date=datetime(2026, 3, 1, tzinfo=timezone.utc),
        )
        profile = _profile(state_tax_rate=0.0, agi_estimate=Decimal("100000"))
        result = compare_st_lt_tax(lot, Decimal("200.00"), profile)

        # 22% federal only
        assert result.rate_now == Decimal("0.22")
