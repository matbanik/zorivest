# tests/unit/domain/tax/test_wash_sale_chain_manager.py
"""Tests for WashSaleChainManager state machine (MEU-131 AC-131.1 through AC-131.7)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from zorivest_core.domain.entities import TaxLot
from zorivest_core.domain.enums import WashSaleEventType, WashSaleStatus
from zorivest_core.domain.tax.wash_sale_chain_manager import WashSaleChainManager


def _make_lot(
    lot_id: str = "lot-1",
    ticker: str = "AAPL",
    open_date: datetime | None = None,
    close_date: datetime | None = None,
    quantity: float = 100.0,
    cost_basis: Decimal = Decimal("150.00"),
    proceeds: Decimal = Decimal("140.00"),
    account_id: str = "acc-1",
    wash_sale_adjustment: Decimal = Decimal("0.00"),
) -> TaxLot:
    """Helper to build TaxLot with sensible defaults."""
    if open_date is None:
        open_date = datetime(2026, 1, 15, tzinfo=timezone.utc)
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
        is_closed=close_date is not None,
    )


LOSS_DATE = datetime(2026, 3, 15, tzinfo=timezone.utc)
REPLACEMENT_DATE = datetime(2026, 3, 20, tzinfo=timezone.utc)


# ── AC-131.1: WashSaleChainManager API ──────────────────────────────────


class TestChainManagerAPI:
    """AC-131.1: WashSaleChainManager has start_chain, absorb_loss, release_chain, continue_chain."""

    def test_has_all_methods(self) -> None:
        mgr = WashSaleChainManager()
        assert callable(mgr.start_chain)
        assert callable(mgr.absorb_loss)
        assert callable(mgr.release_chain)
        assert callable(mgr.continue_chain)


# ── AC-131.2: start_chain ───────────────────────────────────────────────


class TestStartChain:
    """AC-131.2: Creates chain with DISALLOWED status + LOSS_DISALLOWED entry."""

    def test_creates_chain_with_disallowed_status(self) -> None:
        mgr = WashSaleChainManager()
        loss_lot = _make_lot(
            close_date=LOSS_DATE,
            cost_basis=Decimal("150.00"),
            proceeds=Decimal("140.00"),
        )
        chain = mgr.start_chain(
            loss_lot=loss_lot,
            disallowed_amount=Decimal("1000.00"),
        )
        assert chain.status == WashSaleStatus.DISALLOWED
        assert chain.ticker == "AAPL"
        assert chain.loss_lot_id == "lot-1"
        assert chain.disallowed_amount == Decimal("1000.00")

    def test_creates_loss_disallowed_entry(self) -> None:
        mgr = WashSaleChainManager()
        loss_lot = _make_lot(close_date=LOSS_DATE)
        chain = mgr.start_chain(
            loss_lot=loss_lot,
            disallowed_amount=Decimal("1000.00"),
        )
        assert len(chain.entries) == 1
        entry = chain.entries[0]
        assert entry.event_type == WashSaleEventType.LOSS_DISALLOWED
        assert entry.amount == Decimal("1000.00")


# ── AC-131.3: absorb_loss ──────────────────────────────────────────────


class TestAbsorbLoss:
    """AC-131.3: Adjusts replacement lot basis, adds BASIS_ADJUSTED entry, sets ABSORBED."""

    def test_adjusts_replacement_lot_basis(self) -> None:
        mgr = WashSaleChainManager()
        loss_lot = _make_lot(close_date=LOSS_DATE)
        chain = mgr.start_chain(loss_lot=loss_lot, disallowed_amount=Decimal("1000.00"))

        replacement = _make_lot(
            lot_id="lot-repl",
            open_date=REPLACEMENT_DATE,
            cost_basis=Decimal("142.00"),
        )
        updated_repl = mgr.absorb_loss(chain, replacement)

        assert updated_repl.wash_sale_adjustment == Decimal("1000.00")
        assert chain.status == WashSaleStatus.ABSORBED

    def test_adds_basis_adjusted_entry(self) -> None:
        mgr = WashSaleChainManager()
        loss_lot = _make_lot(close_date=LOSS_DATE)
        chain = mgr.start_chain(loss_lot=loss_lot, disallowed_amount=Decimal("1000.00"))

        replacement = _make_lot(lot_id="lot-repl", open_date=REPLACEMENT_DATE)
        mgr.absorb_loss(chain, replacement)

        entries = [
            e for e in chain.entries if e.event_type == WashSaleEventType.BASIS_ADJUSTED
        ]
        assert len(entries) == 1
        assert entries[0].lot_id == "lot-repl"


# ── AC-131.4: Holding period tacking ───────────────────────────────────


class TestHoldingPeriodTacking:
    """AC-131.4: absorb_loss tacks holding period (replacement gets original open_date)."""

    def test_replacement_inherits_loss_lot_open_date(self) -> None:
        mgr = WashSaleChainManager()
        original_open = datetime(2026, 1, 1, tzinfo=timezone.utc)
        loss_lot = _make_lot(open_date=original_open, close_date=LOSS_DATE)
        chain = mgr.start_chain(loss_lot=loss_lot, disallowed_amount=Decimal("500.00"))

        replacement = _make_lot(
            lot_id="lot-repl",
            open_date=REPLACEMENT_DATE,
        )
        updated_repl = mgr.absorb_loss(chain, replacement)

        # Replacement lot should now have the ORIGINAL lot's open_date
        assert updated_repl.open_date == original_open


# ── AC-131.5: release_chain ─────────────────────────────────────────────


class TestReleaseChain:
    """AC-131.5: Sets RELEASED status + LOSS_RELEASED entry."""

    def test_release_absorbed_chain(self) -> None:
        mgr = WashSaleChainManager()
        loss_lot = _make_lot(close_date=LOSS_DATE)
        chain = mgr.start_chain(loss_lot=loss_lot, disallowed_amount=Decimal("500.00"))
        replacement = _make_lot(lot_id="lot-repl", open_date=REPLACEMENT_DATE)
        mgr.absorb_loss(chain, replacement)

        mgr.release_chain(chain, replacement.lot_id)

        assert chain.status == WashSaleStatus.RELEASED
        release_entries = [
            e for e in chain.entries if e.event_type == WashSaleEventType.LOSS_RELEASED
        ]
        assert len(release_entries) == 1

    def test_cannot_release_non_absorbed_chain(self) -> None:
        """Negative: releasing a DISALLOWED chain raises error."""
        mgr = WashSaleChainManager()
        loss_lot = _make_lot(close_date=LOSS_DATE)
        chain = mgr.start_chain(loss_lot=loss_lot, disallowed_amount=Decimal("500.00"))

        with pytest.raises(ValueError, match="ABSORBED"):
            mgr.release_chain(chain, "lot-repl")


# ── AC-131.6: continue_chain ───────────────────────────────────────────


class TestContinueChain:
    """AC-131.6: Extends chain with CHAIN_CONTINUED entry."""

    def test_continue_chain_adds_entry(self) -> None:
        mgr = WashSaleChainManager()
        loss_lot = _make_lot(close_date=LOSS_DATE)
        chain = mgr.start_chain(loss_lot=loss_lot, disallowed_amount=Decimal("500.00"))
        replacement = _make_lot(lot_id="lot-repl", open_date=REPLACEMENT_DATE)
        mgr.absorb_loss(chain, replacement)

        new_replacement = _make_lot(
            lot_id="lot-repl2",
            open_date=REPLACEMENT_DATE + timedelta(days=10),
        )
        mgr.continue_chain(chain, new_replacement)

        continued_entries = [
            e
            for e in chain.entries
            if e.event_type == WashSaleEventType.CHAIN_CONTINUED
        ]
        assert len(continued_entries) == 1
        assert continued_entries[0].lot_id == "lot-repl2"
        # Status should revert to DISALLOWED (loss is deferred again)
        assert chain.status == WashSaleStatus.DISALLOWED


# ── AC-131.7: get_trapped_losses ────────────────────────────────────────


class TestGetTrappedLosses:
    """AC-131.7: Returns chains in ABSORBED status."""

    def test_returns_absorbed_chains(self) -> None:
        mgr = WashSaleChainManager()

        # Build two chains: one absorbed, one disallowed
        lot1 = _make_lot(lot_id="lot-1", close_date=LOSS_DATE)
        chain1 = mgr.start_chain(lot1, Decimal("500.00"))
        repl1 = _make_lot(lot_id="lot-r1", open_date=REPLACEMENT_DATE)
        mgr.absorb_loss(chain1, repl1)  # → ABSORBED

        lot2 = _make_lot(lot_id="lot-2", close_date=LOSS_DATE)
        chain2 = mgr.start_chain(lot2, Decimal("300.00"))
        # chain2 stays DISALLOWED

        trapped = mgr.get_trapped_losses([chain1, chain2])
        assert len(trapped) == 1
        assert trapped[0].chain_id == chain1.chain_id

    def test_no_active_chains_returns_empty(self) -> None:
        """Negative: no chains → empty list."""
        mgr = WashSaleChainManager()
        trapped = mgr.get_trapped_losses([])
        assert trapped == []


# ── C4: Release entry provenance ────────────────────────────────────────


class TestReleaseEntryProvenance:
    """C4 correction: release_chain creates entry with actual account_id."""

    def test_release_entry_has_account_id(self) -> None:
        """Release entry must have the releasing account's ID, not empty string."""
        mgr = WashSaleChainManager()
        loss_lot = _make_lot(close_date=LOSS_DATE, account_id="acc-taxable")
        chain = mgr.start_chain(loss_lot, Decimal("500.00"))
        replacement = _make_lot(
            lot_id="lot-repl", open_date=REPLACEMENT_DATE, account_id="acc-brokerage"
        )
        mgr.absorb_loss(chain, replacement)

        mgr.release_chain(chain, replacement.lot_id, account_id="acc-brokerage")

        release_entries = [
            e for e in chain.entries if e.event_type == WashSaleEventType.LOSS_RELEASED
        ]
        assert len(release_entries) == 1
        assert release_entries[0].account_id == "acc-brokerage"
        assert release_entries[0].account_id != ""


# ── C1: Multi-replacement per-match allocation ──────────────────────────


class TestMultiReplacementAllocation:
    """C1 correction: absorb_loss uses per-match amount, not total chain amount."""

    def test_two_replacements_get_proportional_share(self) -> None:
        """1 loss lot, 2 replacement lots → each gets its proportional share only."""
        mgr = WashSaleChainManager()
        # Loss: 100 shares at $150, sold at $140 → $10/share loss = $1000 total
        loss_lot = _make_lot(
            close_date=LOSS_DATE,
            quantity=100.0,
            cost_basis=Decimal("150.00"),
            proceeds=Decimal("140.00"),
        )
        chain = mgr.start_chain(loss_lot, Decimal("1000.00"))

        # Replacement 1: 60 shares → $600 disallowed
        repl1 = _make_lot(lot_id="repl-1", open_date=REPLACEMENT_DATE, quantity=60.0)
        updated1 = mgr.absorb_loss(chain, repl1, amount=Decimal("600.00"))

        # Replacement 2: 40 shares → $400 disallowed
        repl2 = _make_lot(lot_id="repl-2", open_date=REPLACEMENT_DATE, quantity=40.0)
        updated2 = mgr.absorb_loss(chain, repl2, amount=Decimal("400.00"))

        # Each replacement gets ONLY its share, not the total $1000
        assert updated1.wash_sale_adjustment == Decimal("600.00")
        assert updated2.wash_sale_adjustment == Decimal("400.00")

        # Total adjustments = total disallowed
        total = updated1.wash_sale_adjustment + updated2.wash_sale_adjustment
        assert total == Decimal("1000.00")

    def test_single_replacement_still_works_without_amount(self) -> None:
        """Single replacement without explicit amount uses chain.disallowed_amount."""
        mgr = WashSaleChainManager()
        loss_lot = _make_lot(close_date=LOSS_DATE)
        chain = mgr.start_chain(loss_lot, Decimal("500.00"))

        replacement = _make_lot(lot_id="repl-1", open_date=REPLACEMENT_DATE)
        updated = mgr.absorb_loss(chain, replacement)

        assert updated.wash_sale_adjustment == Decimal("500.00")

    def test_basis_adjusted_entries_have_per_match_amounts(self) -> None:
        """Each BASIS_ADJUSTED entry records the per-match amount, not total."""
        mgr = WashSaleChainManager()
        loss_lot = _make_lot(close_date=LOSS_DATE)
        chain = mgr.start_chain(loss_lot, Decimal("1000.00"))

        repl1 = _make_lot(lot_id="repl-1", open_date=REPLACEMENT_DATE)
        mgr.absorb_loss(chain, repl1, amount=Decimal("600.00"))
        repl2 = _make_lot(lot_id="repl-2", open_date=REPLACEMENT_DATE)
        mgr.absorb_loss(chain, repl2, amount=Decimal("400.00"))

        adjusted_entries = [
            e for e in chain.entries if e.event_type == WashSaleEventType.BASIS_ADJUSTED
        ]
        assert len(adjusted_entries) == 2
        assert adjusted_entries[0].amount == Decimal("600.00")
        assert adjusted_entries[1].amount == Decimal("400.00")
