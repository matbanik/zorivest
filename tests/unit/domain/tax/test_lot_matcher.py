# tests/unit/domain/tax/test_lot_matcher.py
"""FIC tests for lot_matcher — MEU-140 ACs 140.1–140.6.

Feature Intent Contract:
  LotDetail frozen dataclass with 9 enrichment fields.
  get_lot_details(lots, current_price) — enriches open lots with
    unrealized gain, holding period, days to long-term.
  preview_lot_selection(lots, quantity, method, sale_price) — selects
    and enriches lots via lot_selector + get_lot_details.

All tests are pure domain — no mocks, no I/O.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from zorivest_core.domain.entities import TaxLot
from zorivest_core.domain.enums import CostBasisMethod

# Imports under test — will fail until implementation exists
from zorivest_core.domain.tax.lot_matcher import (
    LotDetail,
    get_lot_details,
    preview_lot_selection,
)


# ── Helpers ──────────────────────────────────────────────────────────────


def _lot(
    lot_id: str = "L1",
    ticker: str = "AAPL",
    open_date: datetime | None = None,
    quantity: float = 100.0,
    cost_basis: Decimal = Decimal("100.00"),
    wash_sale_adjustment: Decimal = Decimal("0.00"),
    is_closed: bool = False,
    close_date: datetime | None = None,
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


# ── AC-140.2: LotDetail is frozen ──────────────────────────────────────


class TestLotDetailFrozen:
    """AC-140.2: LotDetail must be a frozen dataclass with 9 fields."""

    def test_lot_detail_is_frozen(self) -> None:
        detail = LotDetail(
            lot_id="L1",
            ticker="AAPL",
            quantity=100.0,
            cost_basis=Decimal("100.00"),
            unrealized_gain=Decimal("500.00"),
            unrealized_gain_pct=Decimal("5.00"),
            holding_period_days=400,
            days_to_long_term=0,
            is_long_term=True,
        )
        with pytest.raises(FrozenInstanceError):
            detail.lot_id = "L2"  # type: ignore[misc]

    def test_lot_detail_has_all_nine_fields(self) -> None:
        detail = LotDetail(
            lot_id="L1",
            ticker="AAPL",
            quantity=100.0,
            cost_basis=Decimal("100.00"),
            unrealized_gain=Decimal("0"),
            unrealized_gain_pct=Decimal("0"),
            holding_period_days=0,
            days_to_long_term=366,
            is_long_term=False,
        )
        assert detail.lot_id == "L1"
        assert detail.ticker == "AAPL"
        assert detail.quantity == 100.0
        assert detail.cost_basis == Decimal("100.00")
        assert detail.unrealized_gain == Decimal("0")
        assert detail.unrealized_gain_pct == Decimal("0")
        assert detail.holding_period_days == 0
        assert detail.days_to_long_term == 366
        assert detail.is_long_term is False


# ── AC-140.1: get_lot_details ──────────────────────────────────────────


class TestGetLotDetails:
    """AC-140.1: get_lot_details enriches lots with unrealized P&L data."""

    def test_basic_gain(self) -> None:
        """Lot with unrealized gain at current_price > cost_basis."""
        lot = _lot(
            "L1",
            cost_basis=Decimal("100.00"),
            quantity=50.0,
            open_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        results = get_lot_details([lot], current_price=Decimal("110.00"))
        assert len(results) == 1

        d = results[0]
        assert d.lot_id == "L1"
        assert d.ticker == "AAPL"
        assert d.quantity == 50.0
        assert d.cost_basis == Decimal("100.00")
        # unrealized_gain = (110 - 100) * 50 = 500
        assert d.unrealized_gain == Decimal("500.00")
        # unrealized_gain_pct = (110 - 100) / 100 * 100 = 10.00
        assert d.unrealized_gain_pct == Decimal("10.00")

    def test_unrealized_loss(self) -> None:
        """AC-140.4 negative: current_price < cost_basis → negative unrealized gain."""
        lot = _lot("L1", cost_basis=Decimal("100.00"), quantity=100.0)
        results = get_lot_details([lot], current_price=Decimal("80.00"))
        d = results[0]
        # unrealized_gain = (80 - 100) * 100 = -2000
        assert d.unrealized_gain == Decimal("-2000.00")
        # pct = (80 - 100) / 100 * 100 = -20.00
        assert d.unrealized_gain_pct == Decimal("-20.00")

    def test_empty_lots(self) -> None:
        """AC-140.1 negative: empty lots → empty result."""
        results = get_lot_details([], current_price=Decimal("100.00"))
        assert results == []

    def test_wash_sale_adjustment_in_basis(self) -> None:
        """AC-140.4: adjusted_basis = cost_basis + wash_sale_adjustment."""
        lot = _lot(
            "L1",
            cost_basis=Decimal("100.00"),
            wash_sale_adjustment=Decimal("10.00"),
            quantity=100.0,
        )
        results = get_lot_details([lot], current_price=Decimal("120.00"))
        d = results[0]
        # adjusted_basis = 100 + 10 = 110
        # unrealized_gain = (120 - 110) * 100 = 1000
        assert d.unrealized_gain == Decimal("1000.00")
        # pct = (120 - 110) / 110 * 100 ≈ 9.09
        assert d.unrealized_gain_pct == pytest.approx(
            Decimal("9.09"), abs=Decimal("0.01")
        )

    def test_multiple_lots(self) -> None:
        """Multiple lots enriched independently."""
        lots = [
            _lot("L1", cost_basis=Decimal("100.00"), quantity=100.0),
            _lot("L2", cost_basis=Decimal("200.00"), quantity=50.0),
        ]
        results = get_lot_details(lots, current_price=Decimal("150.00"))
        assert len(results) == 2
        assert results[0].lot_id == "L1"
        assert results[1].lot_id == "L2"


# ── AC-140.3: days_to_long_term ────────────────────────────────────────


class TestDaysToLongTerm:
    """AC-140.3: days_to_long_term = max(0, 366 - holding_period_days)."""

    def test_short_term_lot(self) -> None:
        """ST lot → days_to_long_term > 0."""
        lot = _lot(
            "L1",
            open_date=datetime(2026, 4, 1, tzinfo=timezone.utc),
        )
        results = get_lot_details([lot], current_price=Decimal("100.00"))
        d = results[0]
        assert d.is_long_term is False
        assert d.days_to_long_term > 0
        assert d.days_to_long_term == max(0, 366 - d.holding_period_days)

    def test_long_term_lot(self) -> None:
        """AC-140.3: LT lot → days_to_long_term == 0."""
        lot = _lot(
            "L1",
            open_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
        )
        results = get_lot_details([lot], current_price=Decimal("100.00"))
        d = results[0]
        assert d.is_long_term is True
        assert d.days_to_long_term == 0

    def test_exactly_at_threshold(self) -> None:
        """Lot with exactly 366 holding days → LT, days_to_long_term == 0."""
        from datetime import timedelta

        base = datetime(2026, 5, 14, tzinfo=timezone.utc)
        lot = _lot(
            "L1",
            # Set close_date so holding_period_days is exactly 366
            open_date=base - timedelta(days=366),
            close_date=base,
        )
        results = get_lot_details([lot], current_price=Decimal("100.00"))
        d = results[0]
        assert d.holding_period_days == 366
        assert d.is_long_term is True
        assert d.days_to_long_term == 0


# ── AC-140.5: preview_lot_selection ────────────────────────────────────


class TestPreviewLotSelection:
    """AC-140.5: preview_lot_selection enriches selected lots with detail."""

    def test_fifo_selection_enriched(self) -> None:
        """FIFO selects oldest lot first, returns enriched LotDetail list."""
        lots = [
            _lot(
                "L2",
                cost_basis=Decimal("120.00"),
                quantity=50.0,
                open_date=datetime(2025, 6, 1, tzinfo=timezone.utc),
            ),
            _lot(
                "L1",
                cost_basis=Decimal("100.00"),
                quantity=50.0,
                open_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            ),
        ]
        results = preview_lot_selection(
            lots,
            quantity=50.0,
            method=CostBasisMethod.FIFO,
            sale_price=Decimal("150.00"),
        )
        assert len(results) == 1
        # FIFO picks L1 (oldest)
        assert results[0].lot_id == "L1"
        # unrealized_gain = (150 - 100) * 50 = 2500
        assert results[0].unrealized_gain == Decimal("2500.00")

    def test_quantity_exceeds_available_raises(self) -> None:
        """AC-140.5 negative: quantity > available → ValueError."""
        lots = [_lot("L1", quantity=50.0)]
        with pytest.raises(ValueError, match="[Qq]uantity|exceed"):
            preview_lot_selection(
                lots,
                quantity=100.0,
                method=CostBasisMethod.FIFO,
                sale_price=Decimal("100.00"),
            )

    def test_partial_fill(self) -> None:
        """Partial fill: takes from first lot, leaves remainder."""
        lots = [_lot("L1", cost_basis=Decimal("100.00"), quantity=100.0)]
        results = preview_lot_selection(
            lots,
            quantity=40.0,
            method=CostBasisMethod.FIFO,
            sale_price=Decimal("120.00"),
        )
        assert len(results) == 1
        # Only 40 shares selected (partial from lot)
        assert results[0].quantity == 40.0
        # unrealized_gain = (120 - 100) * 40 = 800
        assert results[0].unrealized_gain == Decimal("800.00")


# ── AC-140.6: Results sorted by selected method ────────────────────────


class TestPreviewSortOrder:
    """AC-140.6: Results sorted by CostBasisMethod order."""

    def test_hifo_returns_highest_cost_first(self) -> None:
        """HIFO: highest cost basis lot first."""
        lots = [
            _lot("L1", cost_basis=Decimal("100.00"), quantity=50.0),
            _lot("L2", cost_basis=Decimal("200.00"), quantity=50.0),
        ]
        results = preview_lot_selection(
            lots,
            quantity=50.0,
            method=CostBasisMethod.HIFO,
            sale_price=Decimal("150.00"),
        )
        assert len(results) == 1
        assert results[0].lot_id == "L2"
