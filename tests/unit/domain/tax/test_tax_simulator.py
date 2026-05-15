# tests/unit/domain/tax/test_tax_simulator.py
"""FIC tests for tax_simulator — MEU-137 ACs 137.1–137.10.

Feature Intent Contract:
  TaxImpactResult frozen dataclass.
  simulate_tax_impact(lots, ticker, quantity, sale_price, tax_profile, ...) —
    orchestrates lot selection + gain calc + wash sale check + tax estimate.

All tests are pure domain — no mocks, no I/O.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from decimal import Decimal

import pytest

from zorivest_core.domain.entities import TaxLot, TaxProfile
from zorivest_core.domain.enums import (
    CostBasisMethod,
    FilingStatus,
    WashSaleMatchingMethod,
)

from zorivest_core.domain.tax.tax_simulator import (
    TaxImpactResult,
    simulate_tax_impact,
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
    is_closed: bool = False,
) -> TaxLot:
    return TaxLot(
        lot_id=lot_id,
        account_id="ACC-1",
        ticker=ticker,
        open_date=open_date or datetime(2024, 1, 1, tzinfo=timezone.utc),
        close_date=close_date,
        quantity=quantity,
        cost_basis=cost_basis,
        proceeds=Decimal("0.00"),
        wash_sale_adjustment=wash_sale_adjustment,
        is_closed=is_closed,
        linked_trade_ids=[],
    )


def _profile(
    filing_status: FilingStatus = FilingStatus.SINGLE,
    tax_year: int = 2026,
    agi_estimate: Decimal = Decimal("100000"),
    state_tax_rate: float = 0.0,
    default_cost_basis: CostBasisMethod = CostBasisMethod.FIFO,
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
        default_cost_basis=default_cost_basis,
    )


# ── AC-137.1: simulate_tax_impact basic ──────────────────────────────


class TestSimulateTaxImpact:
    """AC-137.1: simulate_tax_impact returns TaxImpactResult."""

    def test_basic_lt_gain(self) -> None:
        """Long-term lot → realized_lt_gain populated, estimated_lt_tax computed."""
        lots = [
            _lot(
                "L1",
                cost_basis=Decimal("100.00"),
                quantity=100.0,
                open_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
            ),
        ]
        profile = _profile(agi_estimate=Decimal("100000"))
        result = simulate_tax_impact(
            lots=lots,
            ticker="AAPL",
            quantity=100.0,
            sale_price=Decimal("150.00"),
            tax_profile=profile,
        )

        assert isinstance(result, TaxImpactResult)
        assert len(result.lots_selected) == 1
        assert result.lots_selected[0].lot_id == "L1"
        # Gain = (150 - 100) * 100 = 5000
        assert result.realized_lt_gain == Decimal("5000.00")
        assert result.realized_st_gain == Decimal("0")
        assert result.estimated_lt_tax > 0

    def test_ticker_not_in_lots_raises(self) -> None:
        """AC-137.1 negative: ticker not in lots → ValueError."""
        lots = [_lot("L1", ticker="MSFT")]
        profile = _profile()
        with pytest.raises(ValueError, match="ticker|no.*lots"):
            simulate_tax_impact(
                lots=lots,
                ticker="AAPL",
                quantity=100.0,
                sale_price=Decimal("150.00"),
                tax_profile=profile,
            )


# ── AC-137.2: TaxImpactResult fields ────────────────────────────────


class TestTaxImpactResultFields:
    """AC-137.2: TaxImpactResult frozen dataclass with all required fields."""

    def test_all_fields_present(self) -> None:
        lots = [
            _lot(
                "L1",
                cost_basis=Decimal("100.00"),
                quantity=100.0,
                open_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
            ),
        ]
        profile = _profile(agi_estimate=Decimal("100000"))
        result = simulate_tax_impact(
            lots=lots,
            ticker="AAPL",
            quantity=100.0,
            sale_price=Decimal("150.00"),
            tax_profile=profile,
        )
        # All fields must be present with correct types
        assert isinstance(result.lots_selected, list)
        assert isinstance(result.realized_st_gain, Decimal)
        assert isinstance(result.realized_lt_gain, Decimal)
        assert isinstance(result.estimated_st_tax, Decimal)
        assert isinstance(result.estimated_lt_tax, Decimal)
        assert isinstance(result.estimated_niit, Decimal)
        assert isinstance(result.total_estimated_tax, Decimal)
        assert isinstance(result.wash_sale_warnings, list)


# ── AC-137.3: Uses tax_profile.default_cost_basis ────────────────────


class TestCostBasisMethod:
    """AC-137.3/AC-137.9: Uses profile default or explicit override."""

    def test_uses_profile_default(self) -> None:
        """AC-137.3: Defaults to tax_profile.default_cost_basis (FIFO)."""
        lots = [
            _lot(
                "L1",
                cost_basis=Decimal("150.00"),
                quantity=50.0,
                open_date=datetime(2024, 6, 1, tzinfo=timezone.utc),
            ),
            _lot(
                "L2",
                cost_basis=Decimal("100.00"),
                quantity=50.0,
                open_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            ),
        ]
        profile = _profile(default_cost_basis=CostBasisMethod.FIFO)
        result = simulate_tax_impact(
            lots=lots,
            ticker="AAPL",
            quantity=50.0,
            sale_price=Decimal("200.00"),
            tax_profile=profile,
        )
        # FIFO: picks oldest (L2) first
        assert result.lots_selected[0].lot_id == "L2"

    def test_explicit_override(self) -> None:
        """AC-137.9: Explicit method overrides profile default."""
        lots = [
            _lot(
                "L1",
                cost_basis=Decimal("150.00"),
                quantity=50.0,
                open_date=datetime(2024, 6, 1, tzinfo=timezone.utc),
            ),
            _lot(
                "L2",
                cost_basis=Decimal("100.00"),
                quantity=50.0,
                open_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            ),
        ]
        profile = _profile(default_cost_basis=CostBasisMethod.FIFO)
        result = simulate_tax_impact(
            lots=lots,
            ticker="AAPL",
            quantity=50.0,
            sale_price=Decimal("200.00"),
            tax_profile=profile,
            cost_basis_method=CostBasisMethod.HIFO,
        )
        # HIFO: picks highest cost (L1) first
        assert result.lots_selected[0].lot_id == "L1"

    def test_spec_id_without_lot_ids_raises(self) -> None:
        """AC-137.3 negative: SPEC_ID without lot_ids → ValueError."""
        lots = [_lot("L1")]
        profile = _profile()
        with pytest.raises(ValueError, match="lot_ids|SPEC_ID"):
            simulate_tax_impact(
                lots=lots,
                ticker="AAPL",
                quantity=100.0,
                sale_price=Decimal("150.00"),
                tax_profile=profile,
                cost_basis_method=CostBasisMethod.SPEC_ID,
            )


# ── AC-137.4: ST/LT classification ──────────────────────────────────


class TestStLtClassification:
    """AC-137.4: ST/LT classification via calculate_realized_gain."""

    def test_mixed_st_lt(self) -> None:
        """Mix of ST and LT lots → both gains populated."""
        lots = [
            _lot(
                "L1",
                cost_basis=Decimal("100.00"),
                quantity=50.0,
                open_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
            ),  # LT
            _lot(
                "L2",
                cost_basis=Decimal("120.00"),
                quantity=50.0,
                open_date=datetime(2026, 3, 1, tzinfo=timezone.utc),
            ),  # ST
        ]
        profile = _profile()
        result = simulate_tax_impact(
            lots=lots,
            ticker="AAPL",
            quantity=100.0,
            sale_price=Decimal("150.00"),
            tax_profile=profile,
        )
        # L1: (150-100)*50 = 2500 LT
        assert result.realized_lt_gain == Decimal("2500.00")
        # L2: (150-120)*50 = 1500 ST
        assert result.realized_st_gain == Decimal("1500.00")


# ── AC-137.5: Tax estimates ──────────────────────────────────────────


class TestTaxEstimates:
    """AC-137.5: ST via marginal rate, LT via LTCG rate."""

    def test_zero_gain_zero_tax(self) -> None:
        """AC-137.5 negative: Zero gain → zero tax."""
        lots = [
            _lot(
                "L1",
                cost_basis=Decimal("150.00"),
                quantity=100.0,
                open_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
            )
        ]
        profile = _profile()
        result = simulate_tax_impact(
            lots=lots,
            ticker="AAPL",
            quantity=100.0,
            sale_price=Decimal("150.00"),
            tax_profile=profile,
        )
        assert result.estimated_st_tax == Decimal("0")
        assert result.estimated_lt_tax == Decimal("0")
        assert result.total_estimated_tax == Decimal("0")

    def test_st_tax_uses_marginal_rate(self) -> None:
        """ST gain taxed at marginal rate."""
        lots = [
            _lot(
                "L1",
                cost_basis=Decimal("100.00"),
                quantity=100.0,
                open_date=datetime(2026, 3, 1, tzinfo=timezone.utc),
            )
        ]
        profile = _profile(agi_estimate=Decimal("100000"))
        result = simulate_tax_impact(
            lots=lots,
            ticker="AAPL",
            quantity=100.0,
            sale_price=Decimal("150.00"),
            tax_profile=profile,
        )
        # ST gain = 5000, marginal rate for $100K SINGLE = 22%
        # estimated_st_tax = 5000 * 0.22 = 1100
        assert result.estimated_st_tax == Decimal("1100.00")


# ── AC-137.6: Wash sale detection ────────────────────────────────────


class TestWashSaleDetection:
    """AC-137.6: Wash sale risk detected via detect_wash_sales."""

    def test_no_recent_purchases(self) -> None:
        """No recent purchases → empty wash_sale_warnings."""
        lots = [
            _lot(
                "L1",
                cost_basis=Decimal("200.00"),
                quantity=100.0,
                open_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
            )
        ]
        profile = _profile()
        result = simulate_tax_impact(
            lots=lots,
            ticker="AAPL",
            quantity=100.0,
            sale_price=Decimal("150.00"),
            tax_profile=profile,
        )
        assert result.wash_sale_warnings == []

    def test_wash_sale_warning_with_recent_purchase(self) -> None:
        """AC-137.6 positive: loss lot + recent same-ticker replacement
        bought 10 days ago → wash_sale_warnings is non-empty."""
        now = datetime.now(tz=timezone.utc)
        loss_lot = _lot(
            "L1",
            cost_basis=Decimal("200.00"),
            quantity=100.0,
            open_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
        )
        replacement_lot = _lot(
            "L2",
            cost_basis=Decimal("140.00"),
            quantity=50.0,
            open_date=now - timedelta(days=10),
        )
        profile = _profile()
        result = simulate_tax_impact(
            lots=[loss_lot, replacement_lot],
            ticker="AAPL",
            quantity=100.0,
            sale_price=Decimal("150.00"),
            tax_profile=profile,
        )
        # Selling L1 at 150 vs cost 200 = loss. L2 bought 10 days ago = replacement.
        assert len(result.wash_sale_warnings) >= 1
        match = result.wash_sale_warnings[0]
        assert match.loss_lot_id == "L1"
        assert match.replacement_lot_id == "L2"
        assert match.matched_quantity == 50.0
        assert match.disallowed_loss > Decimal("0")


# ── AC-137.7: NIIT computation ───────────────────────────────────────


class TestNiitComputation:
    """AC-137.7: NIIT via compute_niit."""

    def test_below_threshold(self) -> None:
        """AGI below NIIT threshold → NIIT == 0."""
        lots = [
            _lot(
                "L1",
                cost_basis=Decimal("100.00"),
                quantity=100.0,
                open_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
            )
        ]
        profile = _profile(agi_estimate=Decimal("100000"))
        result = simulate_tax_impact(
            lots=lots,
            ticker="AAPL",
            quantity=100.0,
            sale_price=Decimal("150.00"),
            tax_profile=profile,
        )
        assert result.estimated_niit == Decimal("0")

    def test_above_threshold(self) -> None:
        """AGI above NIIT threshold → NIIT > 0."""
        lots = [
            _lot(
                "L1",
                cost_basis=Decimal("100.00"),
                quantity=1000.0,
                open_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
            )
        ]
        profile = _profile(agi_estimate=Decimal("300000"))
        result = simulate_tax_impact(
            lots=lots,
            ticker="AAPL",
            quantity=1000.0,
            sale_price=Decimal("200.00"),
            tax_profile=profile,
        )
        # NIIT = 3.8% × min(NII, AGI-threshold)
        # 300K SINGLE threshold = 200K, excess = 100K
        # Gain = (200-100)*1000 = 100K
        # NIIT = 3.8% * min(100K, 100K) = 3800
        assert result.estimated_niit == Decimal("3800.00")


# ── AC-137.8: total_estimated_tax ────────────────────────────────────


class TestTotalEstimatedTax:
    """AC-137.8: total = estimated_st_tax + estimated_lt_tax + estimated_niit."""

    def test_total_equals_sum(self) -> None:
        lots = [
            _lot(
                "L1",
                cost_basis=Decimal("100.00"),
                quantity=100.0,
                open_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
            )
        ]
        profile = _profile(agi_estimate=Decimal("100000"))
        result = simulate_tax_impact(
            lots=lots,
            ticker="AAPL",
            quantity=100.0,
            sale_price=Decimal("150.00"),
            tax_profile=profile,
        )
        expected = (
            result.estimated_st_tax + result.estimated_lt_tax + result.estimated_niit
        )
        assert result.total_estimated_tax == expected


# ── AC-137.10: State tax ─────────────────────────────────────────────


class TestStateTaxInclusion:
    """AC-137.10: State tax included when state_tax_rate > 0."""

    def test_state_tax_increases_estimate(self) -> None:
        lots = [
            _lot(
                "L1",
                cost_basis=Decimal("100.00"),
                quantity=100.0,
                open_date=datetime(2026, 3, 1, tzinfo=timezone.utc),
            )
        ]
        profile_no_state = _profile(agi_estimate=Decimal("100000"), state_tax_rate=0.0)
        profile_with_state = _profile(
            agi_estimate=Decimal("100000"), state_tax_rate=0.05
        )

        result_no = simulate_tax_impact(
            lots=lots,
            ticker="AAPL",
            quantity=100.0,
            sale_price=Decimal("150.00"),
            tax_profile=profile_no_state,
        )
        result_with = simulate_tax_impact(
            lots=lots,
            ticker="AAPL",
            quantity=100.0,
            sale_price=Decimal("150.00"),
            tax_profile=profile_with_state,
        )
        assert result_with.estimated_st_tax > result_no.estimated_st_tax

    def test_federal_only_when_no_state(self) -> None:
        lots = [
            _lot(
                "L1",
                cost_basis=Decimal("100.00"),
                quantity=100.0,
                open_date=datetime(2026, 3, 1, tzinfo=timezone.utc),
            )
        ]
        profile = _profile(agi_estimate=Decimal("100000"), state_tax_rate=0.0)
        result = simulate_tax_impact(
            lots=lots,
            ticker="AAPL",
            quantity=100.0,
            sale_price=Decimal("150.00"),
            tax_profile=profile,
        )
        # 22% * 5000 = 1100
        assert result.estimated_st_tax == Decimal("1100.00")
