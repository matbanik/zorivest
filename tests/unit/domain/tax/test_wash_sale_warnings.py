# tests/unit/domain/tax/test_wash_sale_warnings.py
"""Tests for wash sale warning generation (MEU-135 AC-135.1–135.5).

RED phase: WashSaleWarning, WarningType, and check_conflicts() don't exist yet.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

import pytest

from zorivest_core.domain.entities import TaxLot


def _make_lot(
    lot_id: str,
    ticker: str,
    open_date: datetime,
    close_date: Optional[datetime],
    quantity: float,
    cost_basis: Decimal,
    proceeds: Decimal = Decimal("0.00"),
    account_id: str = "acc-1",
) -> TaxLot:
    """Helper to build TaxLot with sensible defaults."""
    return TaxLot(
        lot_id=lot_id,
        account_id=account_id,
        ticker=ticker,
        open_date=open_date,
        close_date=close_date,
        quantity=quantity,
        cost_basis=cost_basis,
        proceeds=proceeds,
        wash_sale_adjustment=Decimal("0.00"),
        is_closed=close_date is not None,
    )


NOW = datetime(2026, 5, 10, tzinfo=timezone.utc)


# ── AC-135.1: WashSaleWarning dataclass ─────────────────────────────────


class TestWashSaleWarningDataclass:
    """AC-135.1: WashSaleWarning frozen dataclass with 5 fields."""

    def test_warning_importable(self) -> None:
        from zorivest_core.domain.tax.wash_sale_warnings import WashSaleWarning

        assert WashSaleWarning is not None

    def test_warning_has_required_fields(self) -> None:
        from zorivest_core.domain.tax.wash_sale_warnings import (
            WashSaleWarning,
            WarningType,
        )

        w = WashSaleWarning(
            warning_type=WarningType.REBALANCE_CONFLICT,
            ticker="AAPL",
            message="Rebalance would trigger wash sale",
            conflicting_lot_id="lot-1",
            days_remaining=15,
        )
        assert w.warning_type == WarningType.REBALANCE_CONFLICT
        assert w.ticker == "AAPL"
        assert w.message == "Rebalance would trigger wash sale"
        assert w.conflicting_lot_id == "lot-1"
        assert w.days_remaining == 15

    def test_warning_is_frozen(self) -> None:
        from zorivest_core.domain.tax.wash_sale_warnings import (
            WashSaleWarning,
            WarningType,
        )

        w = WashSaleWarning(
            warning_type=WarningType.DRIP_CONFLICT,
            ticker="AAPL",
            message="Test",
            conflicting_lot_id="lot-1",
            days_remaining=0,
        )
        with pytest.raises(AttributeError):
            w.ticker = "MSFT"  # type: ignore[misc]


# ── AC-135.2: WarningType enum ──────────────────────────────────────────


class TestWarningTypeEnum:
    """AC-135.2: WarningType has REBALANCE_CONFLICT, SPOUSAL_CONFLICT, DRIP_CONFLICT."""

    def test_enum_members(self) -> None:
        from zorivest_core.domain.tax.wash_sale_warnings import WarningType

        assert hasattr(WarningType, "REBALANCE_CONFLICT")
        assert hasattr(WarningType, "SPOUSAL_CONFLICT")
        assert hasattr(WarningType, "DRIP_CONFLICT")
        assert len(WarningType) == 3


# ── AC-135.3: check_conflicts() — rebalance warning ────────────────────


class TestCheckConflictsRebalance:
    """AC-135.3: Warn when recent loss + pending rebalance within 30-day window."""

    def test_recent_loss_generates_rebalance_warning(self) -> None:
        """Loss closed 10 days ago → rebalance purchase within 30-day window → warning."""
        from zorivest_core.domain.tax.wash_sale_warnings import (
            WarningType,
            check_conflicts,
        )

        recent_loss = _make_lot(
            "lot-loss",
            "AAPL",
            NOW - timedelta(days=60),
            NOW - timedelta(days=10),
            100,
            Decimal("150.00"),
            Decimal("140.00"),
        )
        warnings = check_conflicts(
            ticker="AAPL",
            recent_losses=[recent_loss],
            now=NOW,
        )
        assert len(warnings) == 1
        assert warnings[0].warning_type == WarningType.REBALANCE_CONFLICT
        assert warnings[0].ticker == "AAPL"
        assert warnings[0].days_remaining == 20  # 30 - 10

    def test_no_recent_loss_no_warning(self) -> None:
        """AC-135.3 negative: no recent loss → empty list."""
        from zorivest_core.domain.tax.wash_sale_warnings import check_conflicts

        warnings = check_conflicts(
            ticker="AAPL",
            recent_losses=[],
            now=NOW,
        )
        assert warnings == []

    def test_loss_older_than_30_days_no_warning(self) -> None:
        """AC-135.5: loss closed >30 days ago → 0 days remaining, no warning."""
        from zorivest_core.domain.tax.wash_sale_warnings import check_conflicts

        old_loss = _make_lot(
            "lot-old",
            "AAPL",
            NOW - timedelta(days=120),
            NOW - timedelta(days=35),
            100,
            Decimal("150.00"),
            Decimal("140.00"),
        )
        warnings = check_conflicts(
            ticker="AAPL",
            recent_losses=[old_loss],
            now=NOW,
        )
        assert warnings == []


# ── AC-135.4: Spousal conflict ──────────────────────────────────────────


class TestSpousalConflict:
    """AC-135.4: Spousal lots included when include_spousal=True."""

    def test_spousal_loss_generates_spousal_warning(self) -> None:
        from zorivest_core.domain.tax.wash_sale_warnings import (
            WarningType,
            check_conflicts,
        )

        spousal_loss = _make_lot(
            "lot-sp",
            "AAPL",
            NOW - timedelta(days=60),
            NOW - timedelta(days=5),
            50,
            Decimal("160.00"),
            Decimal("140.00"),
            account_id="spouse-acc",
        )
        warnings = check_conflicts(
            ticker="AAPL",
            recent_losses=[spousal_loss],
            now=NOW,
            spousal_lot_ids={"lot-sp"},
            include_spousal=True,
        )
        assert len(warnings) == 1
        assert warnings[0].warning_type == WarningType.SPOUSAL_CONFLICT

    def test_spousal_excluded_when_flag_false(self) -> None:
        """AC-135.4 negative: include_spousal=False → spousal lots excluded."""
        from zorivest_core.domain.tax.wash_sale_warnings import check_conflicts

        spousal_loss = _make_lot(
            "lot-sp",
            "AAPL",
            NOW - timedelta(days=60),
            NOW - timedelta(days=5),
            50,
            Decimal("160.00"),
            Decimal("140.00"),
            account_id="spouse-acc",
        )
        warnings = check_conflicts(
            ticker="AAPL",
            recent_losses=[spousal_loss],
            now=NOW,
            spousal_lot_ids={"lot-sp"},
            include_spousal=False,
        )
        assert warnings == []


# ── AC-135.5: days_remaining computation ────────────────────────────────


class TestDaysRemaining:
    """AC-135.5: days_remaining = 30 - days since sale."""

    def test_days_remaining_exact(self) -> None:
        from zorivest_core.domain.tax.wash_sale_warnings import check_conflicts

        # Loss closed exactly 15 days ago
        loss = _make_lot(
            "lot-15",
            "AAPL",
            NOW - timedelta(days=60),
            NOW - timedelta(days=15),
            100,
            Decimal("150.00"),
            Decimal("140.00"),
        )
        warnings = check_conflicts(
            ticker="AAPL",
            recent_losses=[loss],
            now=NOW,
        )
        assert len(warnings) == 1
        assert warnings[0].days_remaining == 15

    def test_days_remaining_zero_boundary(self) -> None:
        """Loss closed exactly 30 days ago → days_remaining=0, no warning."""
        from zorivest_core.domain.tax.wash_sale_warnings import check_conflicts

        loss = _make_lot(
            "lot-30",
            "AAPL",
            NOW - timedelta(days=90),
            NOW - timedelta(days=30),
            100,
            Decimal("150.00"),
            Decimal("140.00"),
        )
        warnings = check_conflicts(
            ticker="AAPL",
            recent_losses=[loss],
            now=NOW,
        )
        assert warnings == []
