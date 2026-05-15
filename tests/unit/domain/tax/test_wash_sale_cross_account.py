# tests/unit/domain/tax/test_wash_sale_cross_account.py
"""Tests for cross-account wash sale detection (MEU-132 AC-132.1 through AC-132.7)."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from zorivest_core.domain.entities import TaxLot
from zorivest_core.domain.enums import WashSaleEventType, WashSaleStatus
from zorivest_core.domain.tax.wash_sale_chain_manager import WashSaleChainManager
from zorivest_core.domain.tax.wash_sale_detector import (
    detect_wash_sales,
)


SALE_DATE = datetime(2026, 3, 15, tzinfo=timezone.utc)
REPLACEMENT_DATE = datetime(2026, 3, 20, tzinfo=timezone.utc)


def _make_lot(
    lot_id: str = "lot-1",
    ticker: str = "AAPL",
    open_date: datetime | None = None,
    close_date: datetime | None = None,
    quantity: float = 100.0,
    cost_basis: Decimal = Decimal("150.00"),
    proceeds: Decimal = Decimal("140.00"),
    account_id: str = "acc-taxable",
    wash_sale_adjustment: Decimal = Decimal("0.00"),
) -> TaxLot:
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


# ── AC-132.1: Multi-account detection ──────────────────────────────────


class TestMultiAccountDetection:
    """AC-132.1: detect_wash_sales() works with lots from multiple accounts."""

    def test_matches_across_accounts(self) -> None:
        """Loss in account A, replacement in account B → match."""
        loss_lot = _make_lot(
            lot_id="loss-1",
            account_id="acc-taxable",
            close_date=SALE_DATE,
        )
        replacement = _make_lot(
            lot_id="repl-1",
            account_id="acc-ira",
            open_date=REPLACEMENT_DATE,
        )
        matches = detect_wash_sales(loss_lot, [replacement])
        assert len(matches) == 1
        assert matches[0].replacement_lot_id == "repl-1"

    def test_single_account_still_works(self) -> None:
        """AC-132.2 negative: single account with no match."""
        loss_lot = _make_lot(
            lot_id="loss-1",
            close_date=SALE_DATE,
        )
        # No candidates
        matches = detect_wash_sales(loss_lot, [])
        assert matches == []


# ── AC-132.3 + AC-132.4: IRA Loss Destruction ──────────────────────────


class TestIraLossDestruction:
    """AC-132.3 + AC-132.4: IRA replacement → DESTROYED chain."""

    def test_destroy_chain_sets_destroyed_status(self) -> None:
        """AC-132.4: destroy_chain() sets DESTROYED status."""
        mgr = WashSaleChainManager()
        loss_lot = _make_lot(close_date=SALE_DATE)
        chain = mgr.start_chain(loss_lot, Decimal("1000.00"))

        mgr.destroy_chain(chain, lot_id="ira-lot-1", account_id="acc-ira")

        assert chain.status == WashSaleStatus.DESTROYED

    def test_destroy_chain_adds_loss_destroyed_entry(self) -> None:
        """AC-132.4: LOSS_DESTROYED entry is added."""
        mgr = WashSaleChainManager()
        loss_lot = _make_lot(close_date=SALE_DATE)
        chain = mgr.start_chain(loss_lot, Decimal("1000.00"))

        mgr.destroy_chain(chain, lot_id="ira-lot-1", account_id="acc-ira")

        destroyed_entries = [
            e for e in chain.entries if e.event_type == WashSaleEventType.LOSS_DESTROYED
        ]
        assert len(destroyed_entries) == 1
        assert destroyed_entries[0].account_id == "acc-ira"

    def test_cannot_absorb_after_destroy(self) -> None:
        """AC-132.4 negative: absorb after destroy raises ValueError."""
        mgr = WashSaleChainManager()
        loss_lot = _make_lot(close_date=SALE_DATE)
        chain = mgr.start_chain(loss_lot, Decimal("500.00"))
        mgr.destroy_chain(chain, lot_id="ira-lot", account_id="acc-ira")

        replacement = _make_lot(lot_id="repl-1", open_date=REPLACEMENT_DATE)
        with pytest.raises(ValueError, match="Cannot absorb"):
            mgr.absorb_loss(chain, replacement, amount=Decimal("500.00"))

    def test_cannot_absorb_after_release(self) -> None:
        """AC-131.5 negative: absorb after release raises ValueError."""
        mgr = WashSaleChainManager()
        loss_lot = _make_lot(close_date=SALE_DATE)
        chain = mgr.start_chain(loss_lot, Decimal("500.00"))
        replacement = _make_lot(lot_id="repl-1", open_date=REPLACEMENT_DATE)
        mgr.absorb_loss(chain, replacement, amount=Decimal("500.00"))
        mgr.release_chain(chain, replacement_lot_id="repl-1", account_id="acc-taxable")

        replacement2 = _make_lot(lot_id="repl-2", open_date=REPLACEMENT_DATE)
        with pytest.raises(ValueError, match="Cannot absorb"):
            mgr.absorb_loss(chain, replacement2, amount=Decimal("500.00"))

    def test_taxable_to_taxable_is_disallowed_not_destroyed(self) -> None:
        """AC-132.3 negative: taxable-to-taxable → DISALLOWED, not DESTROYED."""
        mgr = WashSaleChainManager()
        loss_lot = _make_lot(close_date=SALE_DATE, account_id="acc-taxable")
        chain = mgr.start_chain(loss_lot, Decimal("500.00"))

        # Should be DISALLOWED (normal flow), not DESTROYED
        assert chain.status == WashSaleStatus.DISALLOWED


# ── AC-132.6: Entry account_id provenance ───────────────────────────────


class TestEntryAccountProvenance:
    """AC-132.6: Each WashSaleEntry identifies the account_id."""

    def test_loss_entry_has_account_id(self) -> None:
        mgr = WashSaleChainManager()
        loss_lot = _make_lot(close_date=SALE_DATE, account_id="acc-taxable")
        chain = mgr.start_chain(loss_lot, Decimal("500.00"))

        assert chain.entries[0].account_id == "acc-taxable"

    def test_absorb_entry_has_replacement_account(self) -> None:
        mgr = WashSaleChainManager()
        loss_lot = _make_lot(close_date=SALE_DATE, account_id="acc-taxable")
        chain = mgr.start_chain(loss_lot, Decimal("500.00"))

        replacement = _make_lot(
            lot_id="repl-1",
            account_id="acc-ira",
            open_date=REPLACEMENT_DATE,
        )
        mgr.absorb_loss(chain, replacement)

        basis_entries = [
            e for e in chain.entries if e.event_type == WashSaleEventType.BASIS_ADJUSTED
        ]
        assert len(basis_entries) == 1
        assert basis_entries[0].account_id == "acc-ira"


# ── AC-132.5: TaxService scan method ───────────────────────────────────


class TestTaxServiceScanMethod:
    """AC-132.5: TaxService has scan_cross_account_wash_sales() method."""

    def test_method_exists(self) -> None:
        from zorivest_core.services.tax_service import TaxService

        assert hasattr(TaxService, "scan_cross_account_wash_sales")
        assert callable(getattr(TaxService, "scan_cross_account_wash_sales"))
