# tests/unit/test_tax_alpha.py
"""FIC tests for TaxService.tax_alpha_report() — MEU-152 ACs 152.1–152.5.

Feature Intent Contract:
  tax_alpha_report(tax_year) → TaxAlphaReport
  Computes counterfactual FIFO tax vs actual tax, plus harvesting savings.

Acceptance Criteria:
  AC-152.1: Method accepts tax_year: int
             Source: Spec: build-priority-matrix.md item 79
  AC-152.2: Returns TaxAlphaReport with 6 fields
             Source: Spec: "YTD savings from lot optimization + loss harvesting"
  AC-152.3: Counterfactual: re-calculates as if FIFO used, compares to actual
             Source: Spec: build-priority-matrix item 79; Local Canon: gains_calculator
  AC-152.4: Harvesting savings from actually-executed harvest lots
             Source: Local Canon: harvest_scanner.py results
  AC-152.5: Empty portfolio → zeroed report
             Source: Local Canon: established empty-result pattern

All tests use mocked UoW — no database access.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock


from zorivest_core.domain.entities import TaxLot, TaxProfile
from zorivest_core.domain.enums import (
    CostBasisMethod,
    FilingStatus,
    WashSaleMatchingMethod,
)
from zorivest_core.services.tax_service import TaxService, TaxAlphaReport


# ── Helpers ──────────────────────────────────────────────────────────────


def _closed_lot(
    lot_id: str = "L1",
    ticker: str = "AAPL",
    account_id: str = "ACC-1",
    cost_basis: Decimal = Decimal("100.00"),
    proceeds: Decimal = Decimal("150.00"),
    quantity: float = 100.0,
    open_date: datetime | None = None,
    close_date: datetime | None = None,
    cost_basis_method: CostBasisMethod | None = None,
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
        wash_sale_adjustment=Decimal("0.00"),
        is_closed=True,
        linked_trade_ids=[],
        realized_gain_loss=(proceeds - cost_basis) * Decimal(str(quantity)),
        cost_basis_method=cost_basis_method,
    )


def _profile(tax_year: int = 2026) -> TaxProfile:
    return TaxProfile(
        id=1,
        filing_status=FilingStatus.SINGLE,
        tax_year=tax_year,
        federal_bracket=0.32,
        state_tax_rate=0.06,
        state="NY",
        prior_year_tax=Decimal("50000"),
        agi_estimate=Decimal("300000"),
        capital_loss_carryforward=Decimal("0"),
        wash_sale_method=WashSaleMatchingMethod.CONSERVATIVE,
        default_cost_basis=CostBasisMethod.FIFO,
    )


def _mock_uow(
    lots: list[TaxLot] | None = None,
    open_lots: list[TaxLot] | None = None,
    profile: TaxProfile | None = None,
    accounts: dict[str, bool] | None = None,
) -> MagicMock:
    """Create a mock UnitOfWork for alpha tests.

    Args:
        lots: Closed lots (returned by list_all_filtered(is_closed=True)).
        open_lots: Open lots (combined with lots for unfiltered queries).
        profile: TaxProfile to return.
        accounts: Mapping of account_id -> is_tax_advantaged.
    """
    uow = MagicMock()
    uow.__enter__ = MagicMock(return_value=uow)
    uow.__exit__ = MagicMock(return_value=False)

    closed = lots or []
    opened = open_lots or []
    all_lots = closed + opened
    lot_map = {lot.lot_id: lot for lot in all_lots}
    uow.tax_lots.get.side_effect = lambda lid: lot_map.get(lid)

    def _list_all_filtered(
        account_id: str | None = None,
        ticker: str | None = None,
        is_closed: bool | None = None,
    ) -> list[TaxLot]:
        pool = all_lots
        if is_closed is True:
            pool = [lt for lt in pool if lt.is_closed]
        elif is_closed is False:
            pool = [lt for lt in pool if not lt.is_closed]
        if ticker is not None:
            pool = [lt for lt in pool if lt.ticker == ticker]
        if account_id is not None:
            pool = [lt for lt in pool if lt.account_id == account_id]
        return pool

    uow.tax_lots.list_all_filtered.side_effect = _list_all_filtered

    accounts_map = accounts or {}

    def _get_account(account_id: str) -> MagicMock:
        acc = MagicMock()
        acc.account_id = account_id
        acc.is_tax_advantaged = accounts_map.get(account_id, False)
        return acc

    uow.accounts.get.side_effect = _get_account

    uow.tax_profiles.get_for_year.return_value = profile

    return uow


# ── AC-152.1: Method signature ──────────────────────────────────────────


class TestTaxAlphaSignature:
    """AC-152.1: tax_alpha_report accepts tax_year."""

    def test_accepts_tax_year(self) -> None:
        """AC-152.1: Method accepts tax_year parameter."""
        uow = _mock_uow(profile=_profile())
        svc = TaxService(uow)
        result = svc.tax_alpha_report(tax_year=2026)
        assert result is not None


# ── AC-152.2: Return type structure ─────────────────────────────────────


class TestTaxAlphaReturnType:
    """AC-152.2: Returns TaxAlphaReport with 6 fields."""

    def test_returns_tax_alpha_report(self) -> None:
        """AC-152.2: Return type is TaxAlphaReport."""
        uow = _mock_uow(profile=_profile())
        svc = TaxService(uow)
        result = svc.tax_alpha_report(tax_year=2026)
        assert isinstance(result, TaxAlphaReport)

    def test_has_all_required_fields(self) -> None:
        """AC-152.2: All 6 fields present."""
        lot = _closed_lot()
        uow = _mock_uow(lots=[lot], profile=_profile())
        svc = TaxService(uow)
        result = svc.tax_alpha_report(tax_year=2026)

        assert isinstance(result.actual_tax_estimate, Decimal)
        assert isinstance(result.naive_fifo_tax_estimate, Decimal)
        assert isinstance(result.tax_savings, Decimal)
        assert isinstance(result.savings_from_lot_optimization, Decimal)
        assert isinstance(result.savings_from_harvesting, Decimal)
        assert isinstance(result.trades_optimized_count, int)


# ── AC-152.3: Counterfactual FIFO comparison ───────────────────────────


class TestTaxAlphaCounterfactual:
    """AC-152.3: Counterfactual FIFO vs actual tax comparison."""

    def test_savings_when_hifo_used(self) -> None:
        """AC-152.3: HIFO closed lot + open FIFO-eligible lot → savings.

        Setup:
          Lot A (old, open, FIFO-eligible): cost=100, qty=100
          Lot B (new, closed via HIFO):     cost=180, proceeds=200, qty=100
            → actual gain = (200-180)*100 = 2000

        FIFO counterfactual: would have sold Lot A (oldest) instead.
          → FIFO gain = (200-100)*100 = 10000

        Combined rate = 0.32 + 0.06 = 0.38
        naive_fifo_tax = 10000 * 0.38 = 3800
        actual_tax     = 2000 * 0.38 = 760
        tax_savings    = 3800 - 760 = 3040
        """
        # Lot A: older, lower basis, STILL OPEN (FIFO would pick this)
        lot_a_open = TaxLot(
            lot_id="L-OLD-OPEN",
            account_id="ACC-1",
            ticker="AAPL",
            open_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
            close_date=None,
            quantity=100.0,
            cost_basis=Decimal("100.00"),
            proceeds=Decimal("0"),
            wash_sale_adjustment=Decimal("0"),
            is_closed=False,
            linked_trade_ids=[],
            realized_gain_loss=Decimal("0"),
            cost_basis_method=None,
        )
        # Lot B: newer, higher basis, CLOSED via HIFO
        lot_b_closed = _closed_lot(
            lot_id="L-NEW-HIFO",
            ticker="AAPL",
            cost_basis=Decimal("180.00"),
            proceeds=Decimal("200.00"),
            quantity=100.0,
            cost_basis_method=CostBasisMethod.HIFO,
            open_date=datetime(2024, 6, 1, tzinfo=timezone.utc),
            close_date=datetime(2026, 6, 1, tzinfo=timezone.utc),
        )
        uow = _mock_uow(
            lots=[lot_b_closed],
            open_lots=[lot_a_open],
            profile=_profile(),
        )
        svc = TaxService(uow)
        result = svc.tax_alpha_report(tax_year=2026)

        # FIFO counterfactual produces higher gains → higher tax
        assert result.naive_fifo_tax_estimate > result.actual_tax_estimate
        assert result.tax_savings > Decimal("0")

    def test_no_savings_when_fifo_only(self) -> None:
        """AC-152.3: Pure FIFO lots → zero savings."""
        lot = _closed_lot(
            cost_basis=Decimal("100.00"),
            proceeds=Decimal("150.00"),
            quantity=100.0,
            cost_basis_method=CostBasisMethod.FIFO,
        )
        uow = _mock_uow(lots=[lot], profile=_profile())
        svc = TaxService(uow)
        result = svc.tax_alpha_report(tax_year=2026)

        # When only FIFO used, actual = naive → savings = 0
        assert result.tax_savings == Decimal("0")

    def test_single_non_fifo_lot_uses_same_basis(self) -> None:
        """AC-152.3: Single HIFO lot has no FIFO alternative → savings = 0."""
        lot = _closed_lot(
            lot_id="L-SOLO-HIFO",
            cost_basis=Decimal("150.00"),
            proceeds=Decimal("200.00"),
            quantity=100.0,
            cost_basis_method=CostBasisMethod.HIFO,
            open_date=datetime(2024, 6, 1, tzinfo=timezone.utc),
            close_date=datetime(2026, 6, 1, tzinfo=timezone.utc),
        )
        uow = _mock_uow(lots=[lot], profile=_profile())
        svc = TaxService(uow)
        result = svc.tax_alpha_report(tax_year=2026)

        # Only one lot exists — FIFO would have picked the same lot
        assert result.naive_fifo_tax_estimate == result.actual_tax_estimate
        assert result.tax_savings == Decimal("0")


# ── AC-152.4: Harvesting savings ───────────────────────────────────────


class TestTaxAlphaHarvesting:
    """AC-152.4: Harvesting savings from executed harvests."""

    def test_harvesting_savings_from_losses(self) -> None:
        """AC-152.4: Lots with losses contribute to concrete harvesting savings.

        Loss lot: cost=200, proceeds=150, qty=100 → loss = -5000
        Combined rate = 0.38
        Harvesting savings = 5000 * 0.38 = 1900.00
        """
        loss_lot = _closed_lot(
            lot_id="L-HARVEST",
            cost_basis=Decimal("200.00"),
            proceeds=Decimal("150.00"),
            quantity=100.0,
            close_date=datetime(2026, 6, 1, tzinfo=timezone.utc),
        )
        uow = _mock_uow(lots=[loss_lot], profile=_profile())
        svc = TaxService(uow)
        result = svc.tax_alpha_report(tax_year=2026)

        # Loss = (150-200)*100 = -5000 → savings = 5000 * 0.38 = 1900.00
        assert result.savings_from_harvesting == Decimal("1900.00")


# ── AC-152.5: Empty portfolio ───────────────────────────────────────────


class TestTaxAlphaEmpty:
    """AC-152.5: Empty portfolio → zeroed report."""

    def test_empty_portfolio_returns_zeros(self) -> None:
        """AC-152.5: No lots → all fields zero."""
        uow = _mock_uow(lots=[], profile=_profile())
        svc = TaxService(uow)
        result = svc.tax_alpha_report(tax_year=2026)

        assert result.actual_tax_estimate == Decimal("0")
        assert result.naive_fifo_tax_estimate == Decimal("0")
        assert result.tax_savings == Decimal("0")
        assert result.savings_from_lot_optimization == Decimal("0")
        assert result.savings_from_harvesting == Decimal("0")
        assert result.trades_optimized_count == 0

    def test_empty_portfolio_no_profile_ok(self) -> None:
        """AC-152.5: No lots + no profile → no errors."""
        uow = _mock_uow(lots=[], profile=None)
        svc = TaxService(uow)
        result = svc.tax_alpha_report(tax_year=2026)
        assert result.actual_tax_estimate == Decimal("0")
