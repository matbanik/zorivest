# tests/unit/domain/tax/test_lot_reassignment.py
"""FIC tests for lot_reassignment — MEU-141 ACs 141.1–141.7.

Feature Intent Contract:
  ReassignmentEligibility frozen dataclass.
  can_reassign_lots(lot, now) — checks if lot is within T+1 settlement window.
  reassign_lots(lots, closed_lots, quantity, new_method, sale_price) —
    re-selects lots using a different CostBasisMethod.

All tests are pure domain — no mocks, no I/O.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone, timedelta
from decimal import Decimal

import pytest

from zorivest_core.domain.entities import TaxLot
from zorivest_core.domain.enums import CostBasisMethod

from zorivest_core.domain.tax.lot_reassignment import (
    SETTLEMENT_DAYS,
    ReassignmentEligibility,
    can_reassign_lots,
    reassign_lots,
)


# ── Helpers ──────────────────────────────────────────────────────────────


def _lot(
    lot_id: str = "L1",
    ticker: str = "AAPL",
    open_date: datetime | None = None,
    quantity: float = 100.0,
    cost_basis: Decimal = Decimal("100.00"),
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
        wash_sale_adjustment=Decimal("0.00"),
        is_closed=is_closed,
        linked_trade_ids=[],
    )


# ── AC-141.2: ReassignmentEligibility frozen ─────────────────────────


class TestReassignmentEligibilityFrozen:
    """AC-141.2: ReassignmentEligibility must be a frozen dataclass."""

    def test_frozen(self) -> None:
        e = ReassignmentEligibility(
            eligible=True,
            deadline=datetime(2026, 5, 15, tzinfo=timezone.utc),
            hours_remaining=12.0,
            reason="Within settlement window",
        )
        with pytest.raises(FrozenInstanceError):
            e.eligible = False  # type: ignore[misc]

    def test_all_fields(self) -> None:
        e = ReassignmentEligibility(
            eligible=False,
            deadline=datetime(2026, 5, 14, tzinfo=timezone.utc),
            hours_remaining=0.0,
            reason="Past settlement deadline",
        )
        assert e.eligible is False
        assert isinstance(e.deadline, datetime)
        assert e.hours_remaining == 0.0
        assert (
            "settlement" in e.reason.lower()
            or "deadline" in e.reason.lower()
            or e.reason != ""
        )


# ── AC-141.1: can_reassign_lots ──────────────────────────────────────


class TestCanReassignLots:
    """AC-141.1: can_reassign_lots checks settlement window."""

    def test_within_settlement_eligible(self) -> None:
        """Lot closed within T+1 → eligible=True."""
        now = datetime(2026, 5, 14, 12, 0, tzinfo=timezone.utc)
        lot = _lot(
            "L1",
            close_date=now - timedelta(hours=6),
            is_closed=True,
        )
        result = can_reassign_lots(lot, now)
        assert result.eligible is True
        assert result.hours_remaining > 0

    def test_past_settlement_not_eligible(self) -> None:
        """AC-141.1 negative: Lot closed > T+1 → eligible=False."""
        now = datetime(2026, 5, 14, 12, 0, tzinfo=timezone.utc)
        lot = _lot(
            "L1",
            close_date=now - timedelta(days=3),
            is_closed=True,
        )
        result = can_reassign_lots(lot, now)
        assert result.eligible is False
        assert result.hours_remaining == 0.0


# ── AC-141.3: Settlement window = close_date + SETTLEMENT_DAYS ──────


class TestSettlementWindow:
    """AC-141.3: Settlement window = close_date + SETTLEMENT_DAYS."""

    def test_default_settlement_days(self) -> None:
        """Default SETTLEMENT_DAYS = 1 (T+1 US equities)."""
        assert SETTLEMENT_DAYS == 1

    def test_exactly_at_deadline(self) -> None:
        """Exactly at deadline → not eligible (deadline passed)."""
        now = datetime(2026, 5, 14, 12, 0, tzinfo=timezone.utc)
        close_date = now - timedelta(days=SETTLEMENT_DAYS)
        lot = _lot("L1", close_date=close_date, is_closed=True)
        result = can_reassign_lots(lot, now)
        assert result.eligible is False


# ── AC-141.4: reassign_lots ──────────────────────────────────────────


class TestReassignLots:
    """AC-141.4: reassign_lots re-selects lots with a different method."""

    def test_basic_reassignment(self) -> None:
        """Re-selects lots using HIFO instead of FIFO."""
        lots = [
            _lot(
                "L1",
                cost_basis=Decimal("100.00"),
                quantity=50.0,
                open_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            ),
            _lot(
                "L2",
                cost_basis=Decimal("200.00"),
                quantity=50.0,
                open_date=datetime(2024, 6, 1, tzinfo=timezone.utc),
            ),
        ]
        result = reassign_lots(
            lots=lots,
            quantity=50.0,
            new_method=CostBasisMethod.HIFO,
            sale_price=Decimal("150.00"),
        )
        assert len(result) == 1
        # HIFO: picks L2 (highest cost)
        assert result[0][0].lot_id == "L2"

    def test_quantity_exceeds_raises(self) -> None:
        """AC-141.4 negative: quantity > available → ValueError."""
        lots = [_lot("L1", quantity=50.0)]
        with pytest.raises(ValueError, match="[Qq]uantity|exceed"):
            reassign_lots(
                lots=lots,
                quantity=100.0,
                new_method=CostBasisMethod.FIFO,
                sale_price=Decimal("100.00"),
            )


# ── AC-141.6: Custom settlement_days ────────────────────────────────


class TestCustomSettlementDays:
    """AC-141.6: settlement_days parameter override."""

    def test_custom_settlement_days_2(self) -> None:
        """Custom settlement_days=2 → T+2 window."""
        now = datetime(2026, 5, 14, 12, 0, tzinfo=timezone.utc)
        # Closed 1.5 days ago → eligible with T+2 but not T+1
        lot = _lot(
            "L1",
            close_date=now - timedelta(hours=36),
            is_closed=True,
        )
        # T+1: not eligible
        result_t1 = can_reassign_lots(lot, now, settlement_days=1)
        assert result_t1.eligible is False

        # T+2: eligible
        result_t2 = can_reassign_lots(lot, now, settlement_days=2)
        assert result_t2.eligible is True


# ── AC-141.7: Open lots always eligible ─────────────────────────────


class TestOpenLotsEligible:
    """AC-141.7: Open lots (close_date is None) → always eligible."""

    def test_open_lot_eligible(self) -> None:
        now = datetime(2026, 5, 14, 12, 0, tzinfo=timezone.utc)
        lot = _lot("L1", close_date=None, is_closed=False)
        result = can_reassign_lots(lot, now)
        assert result.eligible is True
