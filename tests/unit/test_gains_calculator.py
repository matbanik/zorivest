# tests/unit/test_gains_calculator.py
"""FIC tests for gains_calculator.py — MEU-126 ACs 126.1–126.3.

Feature Intent Contract:
  calculate_realized_gain(lot, sale_price) → RealizedGainResult
  - Pure domain function computing realized gain/loss for a closed lot.
  - Returns frozen dataclass with: gain_amount, is_long_term, holding_period_days, tax_type.
  - Gain formula: (sale_price - adjusted_cost_basis) × quantity
    where adjusted_cost_basis = cost_basis + wash_sale_adjustment.

Source: implementation-plan.md ACs 126.1–126.3
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from zorivest_core.domain.entities import TaxLot
from zorivest_core.domain.tax.gains_calculator import (
    RealizedGainResult,
    calculate_realized_gain,
)


# ── Helpers ──────────────────────────────────────────────────────────────


def _lot(
    lot_id: str = "L1",
    open_date: datetime | None = None,
    close_date: datetime | None = None,
    quantity: float = 100.0,
    cost_basis: Decimal = Decimal("100.00"),
    wash_sale_adjustment: Decimal = Decimal("0.00"),
) -> TaxLot:
    return TaxLot(
        lot_id=lot_id,
        account_id="ACC-1",
        ticker="AAPL",
        open_date=open_date or datetime(2024, 1, 1, tzinfo=timezone.utc),
        close_date=close_date,
        quantity=quantity,
        cost_basis=cost_basis,
        proceeds=Decimal("0.00"),
        wash_sale_adjustment=wash_sale_adjustment,
        is_closed=True,
        linked_trade_ids=[],
    )


# ── AC-126.2: RealizedGainResult frozen dataclass ───────────────────────


class TestRealizedGainResult:
    """AC-126.2: RealizedGainResult is a frozen dataclass."""

    def test_fields_present(self) -> None:
        r = RealizedGainResult(
            gain_amount=Decimal("5000.00"),
            is_long_term=True,
            holding_period_days=400,
            tax_type="long_term",
        )
        assert r.gain_amount == Decimal("5000.00")
        assert r.is_long_term is True
        assert r.holding_period_days == 400
        assert r.tax_type == "long_term"

    def test_is_frozen(self) -> None:
        r = RealizedGainResult(
            gain_amount=Decimal("100"),
            is_long_term=False,
            holding_period_days=10,
            tax_type="short_term",
        )
        with pytest.raises(AttributeError):
            r.gain_amount = Decimal("999")  # type: ignore[misc]


# ── AC-126.1: calculate_realized_gain ────────────────────────────────────


class TestCalculateRealizedGain:
    """AC-126.1: calculate_realized_gain returns correct RealizedGainResult."""

    def test_long_term_gain(self) -> None:
        """Lot held > 366 days with gain."""
        lot = _lot(
            open_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
            close_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
            quantity=100.0,
            cost_basis=Decimal("100.00"),
        )
        result = calculate_realized_gain(lot, Decimal("150.00"))
        assert result.gain_amount == Decimal("5000.00")  # (150-100)*100
        assert result.is_long_term is True
        assert result.tax_type == "long_term"
        assert result.holding_period_days >= 366

    def test_short_term_gain(self) -> None:
        """Lot held < 366 days with gain."""
        lot = _lot(
            open_date=datetime(2025, 11, 1, tzinfo=timezone.utc),
            close_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
            quantity=50.0,
            cost_basis=Decimal("100.00"),
        )
        result = calculate_realized_gain(lot, Decimal("120.00"))
        assert result.gain_amount == Decimal("1000.00")  # (120-100)*50
        assert result.is_long_term is False
        assert result.tax_type == "short_term"

    def test_loss(self) -> None:
        """Gain is negative (loss)."""
        lot = _lot(
            open_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            close_date=datetime(2024, 6, 1, tzinfo=timezone.utc),
            quantity=100.0,
            cost_basis=Decimal("150.00"),
        )
        result = calculate_realized_gain(lot, Decimal("100.00"))
        assert result.gain_amount == Decimal("-5000.00")

    def test_zero_gain(self) -> None:
        """AC-126.1 negative: zero gain when cost == sale."""
        lot = _lot(cost_basis=Decimal("100.00"), quantity=100.0)
        result = calculate_realized_gain(lot, Decimal("100.00"))
        assert result.gain_amount == Decimal("0.00")

    # ── AC-126.3: wash_sale_adjustment ──────────────────────────────────

    def test_wash_sale_adjustment_increases_basis(self) -> None:
        """AC-126.3: wash_sale_adjustment added to basis, reducing gain."""
        lot = _lot(
            open_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            close_date=datetime(2025, 6, 1, tzinfo=timezone.utc),
            quantity=100.0,
            cost_basis=Decimal("100.00"),
            wash_sale_adjustment=Decimal("10.00"),
        )
        # adjusted basis = 100 + 10 = 110
        # gain = (150 - 110) × 100 = 4000
        result = calculate_realized_gain(lot, Decimal("150.00"))
        assert result.gain_amount == Decimal("4000.00")

    def test_wash_sale_adjustment_turns_gain_to_loss(self) -> None:
        """Large wash adjustment can turn a gain into a loss."""
        lot = _lot(
            cost_basis=Decimal("100.00"),
            wash_sale_adjustment=Decimal("60.00"),
            quantity=100.0,
        )
        # adjusted basis = 100 + 60 = 160
        # gain = (150 - 160) × 100 = -1000
        result = calculate_realized_gain(lot, Decimal("150.00"))
        assert result.gain_amount == Decimal("-1000.00")

    # ── Holding period classification ───────────────────────────────────

    def test_exactly_366_days_is_long_term(self) -> None:
        """IRS boundary: 366 days = long-term."""
        lot = _lot(
            open_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
            close_date=datetime(2026, 1, 2, tzinfo=timezone.utc),  # 366 days
            quantity=100.0,
            cost_basis=Decimal("100.00"),
        )
        result = calculate_realized_gain(lot, Decimal("150.00"))
        assert result.is_long_term is True
        assert result.holding_period_days == 366

    def test_365_days_is_short_term(self) -> None:
        """IRS boundary: 365 days = short-term."""
        lot = _lot(
            open_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
            close_date=datetime(2026, 1, 1, tzinfo=timezone.utc),  # 365 days
            quantity=100.0,
            cost_basis=Decimal("100.00"),
        )
        result = calculate_realized_gain(lot, Decimal("150.00"))
        assert result.is_long_term is False
        assert result.holding_period_days == 365
