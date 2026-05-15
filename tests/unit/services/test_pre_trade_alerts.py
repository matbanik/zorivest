# tests/unit/services/test_pre_trade_alerts.py
"""Tests for pre-trade wash sale alert enrichment (MEU-136 AC-136.1–136.4).

RED phase: SimulationResult doesn't have wash_sale_warnings or wait_days yet.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import MagicMock

from zorivest_core.domain.entities import TaxLot
from zorivest_core.services.tax_service import TaxService


# ── Helpers ──────────────────────────────────────────────────────────────

NOW = datetime(2026, 5, 10, tzinfo=timezone.utc)


def _make_lot(
    lot_id: str = "lot-1",
    ticker: str = "AAPL",
    account_id: str = "acc-1",
    open_date: datetime | None = None,
    close_date: datetime | None = None,
    quantity: float = 100.0,
    cost_basis: Decimal = Decimal("150.00"),
    proceeds: Decimal = Decimal("0.00"),
    wash_sale_adjustment: Decimal = Decimal("0.00"),
    is_closed: bool | None = None,
) -> TaxLot:
    if open_date is None:
        open_date = datetime(2026, 1, 15, tzinfo=timezone.utc)
    if is_closed is None:
        is_closed = close_date is not None
    return TaxLot(
        lot_id=lot_id,
        account_id=account_id,
        ticker=ticker,
        open_date=open_date,
        close_date=close_date,
        quantity=quantity,
        cost_basis=cost_basis,
        proceeds=proceeds,
        wash_sale_adjustment=wash_sale_adjustment,
        is_closed=is_closed,
    )


def _lot_filter_factory(lots: list[TaxLot]):
    """Create a side_effect function that mimics list_all_filtered kwargs."""

    def _filter(**kwargs: object) -> list[TaxLot]:
        result = lots
        if "ticker" in kwargs and kwargs["ticker"] is not None:
            result = [lot for lot in result if lot.ticker == kwargs["ticker"]]
        if "is_closed" in kwargs and kwargs["is_closed"] is not None:
            result = [lot for lot in result if lot.is_closed == kwargs["is_closed"]]
        if "account_id" in kwargs and kwargs["account_id"] is not None:
            result = [lot for lot in result if lot.account_id == kwargs["account_id"]]
        return result

    return _filter


def _list_filtered_factory(lots: list[TaxLot]):
    """Create a side_effect function for list_filtered (with limit/offset)."""

    def _filter(
        limit: int = 100,
        offset: int = 0,
        account_id: str | None = None,
        ticker: str | None = None,
        is_closed: bool | None = None,
    ) -> list[TaxLot]:
        result = lots
        if account_id is not None:
            result = [lot for lot in result if lot.account_id == account_id]
        if ticker is not None:
            result = [lot for lot in result if lot.ticker == ticker]
        if is_closed is not None:
            result = [lot for lot in result if lot.is_closed == is_closed]
        return result[offset : offset + limit]

    return _filter


def _mock_uow(lots: list[TaxLot] | None = None) -> MagicMock:
    """Create a mock UoW with repos needed for simulate_impact."""
    uow = MagicMock()
    uow.__enter__ = MagicMock(return_value=uow)
    uow.__exit__ = MagicMock(return_value=False)

    all_lots = lots or []
    lot_map = {lot.lot_id: lot for lot in all_lots}
    uow.tax_lots.get.side_effect = lambda lid: lot_map.get(lid)
    uow.tax_lots.list_filtered.side_effect = _list_filtered_factory(all_lots)
    uow.tax_lots.list_all_filtered.side_effect = _lot_filter_factory(all_lots)

    # tax_profiles repo — default no profile
    uow.tax_profiles.get_for_year.return_value = None

    return uow


# ── AC-136.1: SimulationResult fields ───────────────────────────────────


class TestSimulationResultFields:
    """AC-136.1: SimulationResult includes wash_sale_warnings and wait_days."""

    def test_simulation_result_has_warnings_field(self) -> None:
        from zorivest_core.services.tax_service import SimulationResult

        result = SimulationResult(
            lot_details=[],
            total_lt_gain=Decimal("0"),
            total_st_gain=Decimal("0"),
            estimated_tax=Decimal("0"),
            wash_risk=False,
            wash_sale_warnings=[],
            wait_days=0,
        )
        assert result.wash_sale_warnings == []
        assert result.wait_days == 0

    def test_simulation_result_backwards_compatible(self) -> None:
        """Default values allow old callers to not pass the new fields."""
        from zorivest_core.services.tax_service import SimulationResult

        result = SimulationResult(
            lot_details=[],
            total_lt_gain=Decimal("0"),
            total_st_gain=Decimal("0"),
            estimated_tax=Decimal("0"),
            wash_risk=False,
        )
        assert result.wash_sale_warnings == []
        assert result.wait_days == 0


# ── AC-136.2: simulate_impact returns alerts ────────────────────────────


class TestSimulateImpactPreTradeAlerts:
    """AC-136.2/136.3: simulate_impact populates wash_sale_warnings for
    loss sales with recent replacement purchases in the 61-day window.
    """

    def test_loss_sale_with_recent_purchase_warns(self) -> None:
        """Codex probe scenario: loss sale + recent replacement purchase
        (opened 10 days ago) + NO closed losses → warnings generated.
        """
        from zorivest_core.domain.enums import CostBasisMethod

        # Lot to sell at a LOSS (cost=200, sale_price=155 → -45)
        open_lot = _make_lot(
            lot_id="lot-open",
            open_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
            is_closed=False,
            quantity=100.0,
            cost_basis=Decimal("200.00"),
        )
        # Recent replacement purchase — opened 10 days ago, still open
        replacement_purchase = _make_lot(
            lot_id="lot-replacement",
            open_date=NOW - timedelta(days=10),
            is_closed=False,
            quantity=50.0,
            cost_basis=Decimal("155.00"),
        )

        uow = _mock_uow(lots=[open_lot, replacement_purchase])
        svc = TaxService(uow)

        result = svc.simulate_impact(
            account_id="acc-1",
            ticker="AAPL",
            quantity=50.0,
            sale_price=Decimal("155.00"),
            method=CostBasisMethod.FIFO,
            now=NOW,
        )

        # AC-136.3: loss sale + recent purchase → warnings
        assert len(result.wash_sale_warnings) >= 1
        assert result.wait_days > 0
        assert result.wash_risk is True

    def test_no_recent_purchase_no_alert(self) -> None:
        """Loss sale but NO recent purchases → empty warnings, wait_days=0."""
        from zorivest_core.domain.enums import CostBasisMethod

        # Single lot to sell at a loss, no other lots exist
        open_lot = _make_lot(
            lot_id="lot-open",
            open_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
            is_closed=False,
            quantity=100.0,
            cost_basis=Decimal("200.00"),
        )

        uow = _mock_uow(lots=[open_lot])
        svc = TaxService(uow)

        result = svc.simulate_impact(
            account_id="acc-1",
            ticker="AAPL",
            quantity=50.0,
            sale_price=Decimal("155.00"),  # Loss: -45
            method=CostBasisMethod.FIFO,
            now=NOW,
        )

        assert result.wash_sale_warnings == []
        assert result.wait_days == 0

    def test_old_purchase_outside_window_no_alert(self) -> None:
        """Purchase older than 30 days before sale → no warning (window expired)."""
        from zorivest_core.domain.enums import CostBasisMethod

        open_lot = _make_lot(
            lot_id="lot-open",
            open_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
            is_closed=False,
            quantity=100.0,
            cost_basis=Decimal("200.00"),
        )
        # Old purchase — 35 days ago, outside the 30-day pre-sale window
        old_purchase = _make_lot(
            lot_id="lot-old",
            open_date=NOW - timedelta(days=35),
            is_closed=False,
            quantity=50.0,
            cost_basis=Decimal("155.00"),
        )

        uow = _mock_uow(lots=[open_lot, old_purchase])
        svc = TaxService(uow)

        result = svc.simulate_impact(
            account_id="acc-1",
            ticker="AAPL",
            quantity=50.0,
            sale_price=Decimal("155.00"),
            method=CostBasisMethod.FIFO,
            now=NOW,
        )

        # Window expired → no warnings
        assert result.wash_sale_warnings == []
        assert result.wait_days == 0

    def test_exact_30_day_boundary_warns(self) -> None:
        """Purchase exactly 30 days ago → still within window, warning issued.

        IRS 61-day window = 30 days before + sale day + 30 days after.
        The domain detector uses inclusive <= boundaries. The pre-trade
        alert must be consistent: day 30 IS part of the window.
        """
        from zorivest_core.domain.enums import CostBasisMethod

        open_lot = _make_lot(
            lot_id="lot-open",
            open_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
            is_closed=False,
            quantity=100.0,
            cost_basis=Decimal("200.00"),
        )
        # Purchased exactly 30 days ago — edge of window
        boundary_purchase = _make_lot(
            lot_id="lot-boundary",
            open_date=NOW - timedelta(days=30),
            is_closed=False,
            quantity=50.0,
            cost_basis=Decimal("155.00"),
        )

        uow = _mock_uow(lots=[open_lot, boundary_purchase])
        svc = TaxService(uow)

        result = svc.simulate_impact(
            account_id="acc-1",
            ticker="AAPL",
            quantity=50.0,
            sale_price=Decimal("155.00"),
            method=CostBasisMethod.FIFO,
            now=NOW,
        )

        # Day 30 is within window → warning with days_remaining=0
        assert len(result.wash_sale_warnings) == 1
        assert result.wash_sale_warnings[0].days_remaining == 0
        assert result.wait_days == 0  # 30 - 30 = 0 remaining

    def test_purchase_31_days_ago_no_warning(self) -> None:
        """Purchase 31 days ago → outside window, no warning."""
        from zorivest_core.domain.enums import CostBasisMethod

        open_lot = _make_lot(
            lot_id="lot-open",
            open_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
            is_closed=False,
            quantity=100.0,
            cost_basis=Decimal("200.00"),
        )
        # 31 days ago — just outside the 30-day window
        outside_purchase = _make_lot(
            lot_id="lot-outside",
            open_date=NOW - timedelta(days=31),
            is_closed=False,
            quantity=50.0,
            cost_basis=Decimal("155.00"),
        )

        uow = _mock_uow(lots=[open_lot, outside_purchase])
        svc = TaxService(uow)

        result = svc.simulate_impact(
            account_id="acc-1",
            ticker="AAPL",
            quantity=50.0,
            sale_price=Decimal("155.00"),
            method=CostBasisMethod.FIFO,
            now=NOW,
        )

        # Day 31 is outside window → no warnings
        assert result.wash_sale_warnings == []
        assert result.wait_days == 0


# ── AC-136.4: wait_days computation ─────────────────────────────────────


class TestWaitDaysComputation:
    """AC-136.4: wait_days = max days_remaining across all warnings."""

    def test_wait_days_reflects_max_remaining(self) -> None:
        """Two recent purchases → wait_days = max(days_remaining)."""
        from zorivest_core.domain.enums import CostBasisMethod

        # Open lot to sell at LOSS (cost=200, sale_price=155 → -45)
        open_lot = _make_lot(
            lot_id="lot-open",
            open_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
            is_closed=False,
            quantity=100.0,
            cost_basis=Decimal("200.00"),
        )
        # Purchase 10 days ago → 20 days remaining
        purchase1 = _make_lot(
            lot_id="lot-purchase-1",
            open_date=NOW - timedelta(days=10),
            is_closed=False,
            quantity=50.0,
            cost_basis=Decimal("155.00"),
        )
        # Purchase 5 days ago → 25 days remaining
        purchase2 = _make_lot(
            lot_id="lot-purchase-2",
            open_date=NOW - timedelta(days=5),
            is_closed=False,
            quantity=30.0,
            cost_basis=Decimal("155.00"),
        )

        uow = _mock_uow(lots=[open_lot, purchase1, purchase2])
        svc = TaxService(uow)

        result = svc.simulate_impact(
            account_id="acc-1",
            ticker="AAPL",
            quantity=50.0,
            sale_price=Decimal("155.00"),
            method=CostBasisMethod.FIFO,
            now=NOW,
        )

        assert result.wait_days == 25


# ── F2: Gain sale must NOT generate warnings ─────────────────────────────


class TestGainSaleSuppression:
    """F2: simulate_impact for a gain-producing sale should NOT generate
    wash sale warnings (AC-136.3 negative test).
    """

    def test_gain_sale_no_warnings(self) -> None:
        """Sale at gain + recent purchase exists → NO warnings."""
        from zorivest_core.domain.enums import CostBasisMethod

        # Open lot to sell at GAIN (cost=100, sale_price=155 → gain)
        open_lot = _make_lot(
            lot_id="lot-open",
            open_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
            is_closed=False,
            quantity=100.0,
            cost_basis=Decimal("100.00"),
        )
        # Recent purchase exists (should not trigger warning on gain sale)
        recent_purchase = _make_lot(
            lot_id="lot-purchase",
            open_date=NOW - timedelta(days=10),
            is_closed=False,
            quantity=50.0,
            cost_basis=Decimal("155.00"),
        )

        uow = _mock_uow(lots=[open_lot, recent_purchase])
        svc = TaxService(uow)

        result = svc.simulate_impact(
            account_id="acc-1",
            ticker="AAPL",
            quantity=50.0,
            sale_price=Decimal("155.00"),  # Gain: 155 - 100 = 55
            method=CostBasisMethod.FIFO,
            now=NOW,
        )

        # AC-136.3: gain sale → no warnings
        assert result.wash_sale_warnings == []
        assert result.wait_days == 0

    def test_loss_sale_with_purchase_triggers_warnings(self) -> None:
        """Sale at loss + recent replacement purchase → warnings generated."""
        from zorivest_core.domain.enums import CostBasisMethod

        # Open lot to sell at LOSS (cost=200, sale_price=155 → loss)
        open_lot = _make_lot(
            lot_id="lot-open",
            open_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
            is_closed=False,
            quantity=100.0,
            cost_basis=Decimal("200.00"),
        )
        # Recent replacement purchase within 30-day window
        recent_purchase = _make_lot(
            lot_id="lot-purchase",
            open_date=NOW - timedelta(days=10),
            is_closed=False,
            quantity=50.0,
            cost_basis=Decimal("155.00"),
        )

        uow = _mock_uow(lots=[open_lot, recent_purchase])
        svc = TaxService(uow)

        result = svc.simulate_impact(
            account_id="acc-1",
            ticker="AAPL",
            quantity=50.0,
            sale_price=Decimal("155.00"),  # Loss: 155 - 200 = -45
            method=CostBasisMethod.FIFO,
            now=NOW,
        )

        # AC-136.3: loss sale + recent purchase → warnings present
        assert len(result.wash_sale_warnings) >= 1
        assert result.wait_days > 0


# ── F3: wash_risk must reflect warnings ──────────────────────────────────


class TestWashRiskFromWarnings:
    """F3: wash_risk should be True when wash_sale_warnings is non-empty
    (AC-136.5).
    """

    def test_warnings_imply_wash_risk_true(self) -> None:
        """When wash_sale_warnings is populated, wash_risk must be True."""
        from zorivest_core.domain.enums import CostBasisMethod

        # Open lot to sell at LOSS
        open_lot = _make_lot(
            lot_id="lot-open",
            open_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
            is_closed=False,
            quantity=100.0,
            cost_basis=Decimal("200.00"),
        )
        # Recent replacement purchase within 30-day window
        recent_purchase = _make_lot(
            lot_id="lot-purchase",
            open_date=NOW - timedelta(days=10),
            is_closed=False,
            quantity=50.0,
            cost_basis=Decimal("155.00"),
        )

        uow = _mock_uow(lots=[open_lot, recent_purchase])
        svc = TaxService(uow)

        result = svc.simulate_impact(
            account_id="acc-1",
            ticker="AAPL",
            quantity=50.0,
            sale_price=Decimal("155.00"),  # Loss sale
            method=CostBasisMethod.FIFO,
            now=NOW,
        )

        # AC-136.5: warnings present → wash_risk must be True
        assert len(result.wash_sale_warnings) >= 1
        assert result.wash_risk is True

    def test_no_warnings_no_adjustment_wash_risk_false(self) -> None:
        """No warnings and no lot adjustments → wash_risk must be False."""
        from zorivest_core.domain.enums import CostBasisMethod

        open_lot = _make_lot(
            lot_id="lot-open",
            open_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
            is_closed=False,
            quantity=100.0,
            cost_basis=Decimal("150.00"),
        )

        uow = _mock_uow(lots=[open_lot])
        svc = TaxService(uow)

        result = svc.simulate_impact(
            account_id="acc-1",
            ticker="AAPL",
            quantity=50.0,
            sale_price=Decimal("155.00"),
            method=CostBasisMethod.FIFO,
            now=NOW,
        )

        assert result.wash_sale_warnings == []
        assert result.wash_risk is False
