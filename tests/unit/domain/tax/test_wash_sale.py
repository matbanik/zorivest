# tests/unit/domain/tax/test_wash_sale.py
"""Tests for WashSaleChain and WashSaleEntry entities (MEU-130 AC-130.1, AC-130.2)."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from zorivest_core.domain.enums import WashSaleEventType, WashSaleStatus
from zorivest_core.domain.tax.wash_sale import WashSaleChain, WashSaleEntry


# ── AC-130.1: WashSaleChain mutable dataclass ───────────────────────────


class TestWashSaleChain:
    """AC-130.1: WashSaleChain mutable dataclass with 8 fields."""

    def test_create_chain_with_all_fields(self) -> None:
        """All 8 required fields are accepted."""
        entry = WashSaleEntry(
            entry_id="e1",
            chain_id="c1",
            event_type=WashSaleEventType.LOSS_DISALLOWED,
            lot_id="lot-1",
            amount=Decimal("500.00"),
            event_date=datetime(2026, 3, 15, tzinfo=timezone.utc),
            account_id="acc-1",
        )
        chain = WashSaleChain(
            chain_id="c1",
            ticker="AAPL",
            loss_lot_id="lot-1",
            loss_date=datetime(2026, 3, 15, tzinfo=timezone.utc),
            loss_amount=Decimal("500.00"),
            disallowed_amount=Decimal("500.00"),
            status=WashSaleStatus.DISALLOWED,
            entries=[entry],
        )
        assert chain.chain_id == "c1"
        assert chain.ticker == "AAPL"
        assert chain.loss_lot_id == "lot-1"
        assert chain.loss_amount == Decimal("500.00")
        assert chain.disallowed_amount == Decimal("500.00")
        assert chain.status == WashSaleStatus.DISALLOWED
        assert len(chain.entries) == 1

    def test_chain_is_mutable(self) -> None:
        """WashSaleChain status can be mutated (not frozen)."""
        chain = WashSaleChain(
            chain_id="c1",
            ticker="AAPL",
            loss_lot_id="lot-1",
            loss_date=datetime(2026, 3, 15, tzinfo=timezone.utc),
            loss_amount=Decimal("500.00"),
            disallowed_amount=Decimal("500.00"),
            status=WashSaleStatus.DISALLOWED,
            entries=[],
        )
        chain.status = WashSaleStatus.ABSORBED
        assert chain.status == WashSaleStatus.ABSORBED

    def test_missing_required_fields_raises_type_error(self) -> None:
        """Negative: missing required fields raise TypeError."""
        with pytest.raises(TypeError):
            WashSaleChain(  # type: ignore[call-arg]
                chain_id="c1",
                ticker="AAPL",
                # missing: loss_lot_id, loss_date, loss_amount, disallowed_amount, status, entries
            )


# ── AC-130.2: WashSaleEntry frozen dataclass ────────────────────────────


class TestWashSaleEntry:
    """AC-130.2: WashSaleEntry frozen dataclass with 7 fields."""

    def test_create_entry_with_all_fields(self) -> None:
        """All 7 required fields are accepted."""
        entry = WashSaleEntry(
            entry_id="e1",
            chain_id="c1",
            event_type=WashSaleEventType.LOSS_DISALLOWED,
            lot_id="lot-1",
            amount=Decimal("500.00"),
            event_date=datetime(2026, 3, 15, tzinfo=timezone.utc),
            account_id="acc-1",
        )
        assert entry.entry_id == "e1"
        assert entry.chain_id == "c1"
        assert entry.event_type == WashSaleEventType.LOSS_DISALLOWED
        assert entry.lot_id == "lot-1"
        assert entry.amount == Decimal("500.00")
        assert entry.account_id == "acc-1"

    def test_entry_is_frozen(self) -> None:
        """WashSaleEntry is immutable (frozen dataclass)."""
        entry = WashSaleEntry(
            entry_id="e1",
            chain_id="c1",
            event_type=WashSaleEventType.LOSS_DISALLOWED,
            lot_id="lot-1",
            amount=Decimal("500.00"),
            event_date=datetime(2026, 3, 15, tzinfo=timezone.utc),
            account_id="acc-1",
        )
        with pytest.raises(AttributeError):
            entry.amount = Decimal("999.99")  # type: ignore[misc]


# ── AC-130.3: WashSaleStatus enum ───────────────────────────────────────


class TestWashSaleStatus:
    """AC-130.3: WashSaleStatus enum with 4 members."""

    def test_all_statuses_exist(self) -> None:
        assert WashSaleStatus.DISALLOWED == "DISALLOWED"
        assert WashSaleStatus.ABSORBED == "ABSORBED"
        assert WashSaleStatus.RELEASED == "RELEASED"
        assert WashSaleStatus.DESTROYED == "DESTROYED"

    def test_invalid_status_raises_value_error(self) -> None:
        """Negative: invalid status string raises ValueError."""
        with pytest.raises(ValueError):
            WashSaleStatus("INVALID")


# ── AC-130.4: WashSaleEventType enum ────────────────────────────────────


class TestWashSaleEventType:
    """AC-130.4: WashSaleEventType enum with 5 members."""

    def test_all_event_types_exist(self) -> None:
        assert WashSaleEventType.LOSS_DISALLOWED == "LOSS_DISALLOWED"
        assert WashSaleEventType.BASIS_ADJUSTED == "BASIS_ADJUSTED"
        assert WashSaleEventType.CHAIN_CONTINUED == "CHAIN_CONTINUED"
        assert WashSaleEventType.LOSS_RELEASED == "LOSS_RELEASED"
        assert WashSaleEventType.LOSS_DESTROYED == "LOSS_DESTROYED"
