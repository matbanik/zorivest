# tests/unit/services/test_tax_service_wash_sale.py
"""Behavior tests for TaxService wash sale methods (MEU-131, MEU-132).

C5 correction: Replaces method-existence checks with real orchestration tests.
C2 correction: Tests IRA service integration wiring.

All tests use mocked UoW — no database access.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import MagicMock

from typing import Any

import pytest

from zorivest_core.domain.entities import TaxLot
from zorivest_core.domain.enums import AccountType, WashSaleEventType, WashSaleStatus
from zorivest_core.domain.exceptions import BusinessRuleError, NotFoundError
from zorivest_core.services.tax_service import TaxService


# ── Helpers ──────────────────────────────────────────────────────────────


SALE_DATE = datetime(2026, 3, 15, tzinfo=timezone.utc)
REPLACEMENT_DATE = datetime(2026, 3, 20, tzinfo=timezone.utc)


def _make_lot(
    lot_id: str = "loss-1",
    ticker: str = "AAPL",
    account_id: str = "acc-taxable",
    open_date: datetime | None = None,
    close_date: datetime | None = None,
    quantity: float = 100.0,
    cost_basis: Decimal = Decimal("150.00"),
    proceeds: Decimal = Decimal("140.00"),
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


def _mock_uow(
    lots: list[TaxLot] | None = None,
    accounts: list[Any] | None = None,
) -> MagicMock:
    """Create a mock UoW with tax_lots, wash_sale_chains, and accounts repos."""
    uow = MagicMock()
    uow.__enter__ = MagicMock(return_value=uow)
    uow.__exit__ = MagicMock(return_value=False)

    # tax_lots repo
    lot_map = {lot.lot_id: lot for lot in (lots or [])}
    uow.tax_lots.get.side_effect = lambda lid: lot_map.get(lid)
    uow.tax_lots.list_all_filtered.side_effect = _lot_filter_factory(lots or [])

    # wash_sale_chains repo
    uow.wash_sale_chains.save = MagicMock()
    uow.wash_sale_chains.list_active = MagicMock(return_value=[])

    # accounts repo — default no spousal
    acct_list = accounts or []
    uow.accounts.list_all.return_value = acct_list
    acct_map = {a.account_id: a for a in acct_list if hasattr(a, "account_id")}
    uow.accounts.get.side_effect = lambda aid: acct_map.get(aid)

    # tax_profiles repo
    uow.tax_profiles.get_for_year.return_value = None

    return uow


def _lot_filter_factory(lots: list[TaxLot]):
    """Create a side_effect function that mimics list_all_filtered kwargs."""

    def _filter(**kwargs: object) -> list[TaxLot]:
        result = lots
        if "account_id" in kwargs and kwargs["account_id"] is not None:
            result = [lot for lot in result if lot.account_id == kwargs["account_id"]]
        if "ticker" in kwargs and kwargs["ticker"] is not None:
            result = [lot for lot in result if lot.ticker == kwargs["ticker"]]
        if "is_closed" in kwargs and kwargs["is_closed"] is not None:
            result = [lot for lot in result if lot.is_closed == kwargs["is_closed"]]
        return result

    return _filter


# ── AC-131.8: detect_and_apply_wash_sales ────────────────────────────────


class TestDetectAndApplyWashSales:
    """AC-131.8: TaxService.detect_and_apply_wash_sales orchestration."""

    def test_detects_and_creates_chain(self) -> None:
        """Loss lot + replacement within 30 days → creates chain + adjusts basis."""
        loss_lot = _make_lot(
            lot_id="loss-1",
            close_date=SALE_DATE,
            cost_basis=Decimal("150.00"),
            proceeds=Decimal("140.00"),
            is_closed=True,
        )
        replacement = _make_lot(
            lot_id="repl-1",
            open_date=REPLACEMENT_DATE,
            cost_basis=Decimal("142.00"),
            proceeds=Decimal("0.00"),
            is_closed=False,
        )
        uow = _mock_uow(lots=[loss_lot, replacement])
        svc = TaxService(uow)

        matches = svc.detect_and_apply_wash_sales("loss-1")

        assert len(matches) == 1
        assert matches[0].replacement_lot_id == "repl-1"
        # Chain was saved
        uow.wash_sale_chains.save.assert_called_once()
        saved_chain = uow.wash_sale_chains.save.call_args[0][0]
        assert saved_chain.status == WashSaleStatus.ABSORBED
        # Replacement lot was updated with adjusted basis
        uow.tax_lots.update.assert_called_once()
        uow.commit.assert_called_once()

    def test_multi_replacement_per_match_allocation(self) -> None:
        """C1: Two replacements → each gets proportional disallowed loss, not total."""
        loss_lot = _make_lot(
            lot_id="loss-1",
            close_date=SALE_DATE,
            quantity=100.0,
            cost_basis=Decimal("150.00"),
            proceeds=Decimal("140.00"),
            is_closed=True,
        )
        repl1 = _make_lot(
            lot_id="repl-1",
            open_date=REPLACEMENT_DATE,
            quantity=60.0,
            cost_basis=Decimal("142.00"),
            proceeds=Decimal("0.00"),
            is_closed=False,
        )
        repl2 = _make_lot(
            lot_id="repl-2",
            open_date=REPLACEMENT_DATE + timedelta(days=1),
            quantity=40.0,
            cost_basis=Decimal("143.00"),
            proceeds=Decimal("0.00"),
            is_closed=False,
        )
        uow = _mock_uow(lots=[loss_lot, repl1, repl2])
        svc = TaxService(uow)

        matches = svc.detect_and_apply_wash_sales("loss-1")

        assert len(matches) == 2
        # Per-share loss = $10; repl1 gets 60*$10=$600, repl2 gets 40*$10=$400
        saved_chain = uow.wash_sale_chains.save.call_args[0][0]
        # Verify the chain has 3 entries: 1 LOSS_DISALLOWED + 2 BASIS_ADJUSTED
        basis_entries = [
            e
            for e in saved_chain.entries
            if e.event_type == WashSaleEventType.BASIS_ADJUSTED
        ]
        assert len(basis_entries) == 2
        assert basis_entries[0].amount == Decimal("600.00")
        assert basis_entries[1].amount == Decimal("400.00")

    def test_no_matches_returns_empty_no_chain(self) -> None:
        """No replacement within window → no chain created."""
        loss_lot = _make_lot(
            lot_id="loss-1",
            close_date=SALE_DATE,
            cost_basis=Decimal("150.00"),
            proceeds=Decimal("140.00"),
            is_closed=True,
        )
        # Replacement outside 30-day window
        far_lot = _make_lot(
            lot_id="repl-far",
            open_date=SALE_DATE + timedelta(days=60),
            is_closed=False,
        )
        uow = _mock_uow(lots=[loss_lot, far_lot])
        svc = TaxService(uow)

        matches = svc.detect_and_apply_wash_sales("loss-1")

        assert matches == []
        uow.wash_sale_chains.save.assert_not_called()

    def test_missing_lot_raises_not_found(self) -> None:
        """Non-existent lot_id → NotFoundError."""
        uow = _mock_uow(lots=[])
        svc = TaxService(uow)

        with pytest.raises(NotFoundError, match="not found"):
            svc.detect_and_apply_wash_sales("no-such-lot")

    def test_open_lot_raises_business_error(self) -> None:
        """Unclosed lot → BusinessRuleError."""
        open_lot = _make_lot(lot_id="lot-1", is_closed=False)
        uow = _mock_uow(lots=[open_lot])
        svc = TaxService(uow)

        with pytest.raises(BusinessRuleError, match="closed"):
            svc.detect_and_apply_wash_sales("lot-1")


# ── AC-131.7: get_trapped_losses ─────────────────────────────────────────


class TestGetTrappedLosses:
    """AC-131.7: TaxService.get_trapped_losses returns ABSORBED chains."""

    def test_returns_absorbed_chains(self) -> None:
        from zorivest_core.domain.tax.wash_sale import WashSaleChain

        absorbed_chain = WashSaleChain(
            chain_id="chain-1",
            ticker="AAPL",
            loss_lot_id="lot-1",
            loss_date=SALE_DATE,
            loss_amount=Decimal("1000.00"),
            disallowed_amount=Decimal("1000.00"),
            status=WashSaleStatus.ABSORBED,
        )
        uow = _mock_uow()
        uow.wash_sale_chains.list_active.return_value = [absorbed_chain]
        svc = TaxService(uow)

        result = svc.get_trapped_losses()

        assert len(result) == 1
        assert result[0].chain_id == "chain-1"
        uow.wash_sale_chains.list_active.assert_called_once_with(
            status=WashSaleStatus.ABSORBED
        )


# ── AC-132.5 + AC-132.7: Cross-Account Scan ─────────────────────────────


class TestScanCrossAccountWashSales:
    """AC-132.5: scan_cross_account_wash_sales orchestration behavior."""

    def test_detects_cross_account_match(self) -> None:
        """Loss in taxable, replacement in IRA → match detected."""
        loss_lot = _make_lot(
            lot_id="loss-1",
            account_id="acc-taxable",
            close_date=datetime(2026, 6, 15, tzinfo=timezone.utc),
            cost_basis=Decimal("150.00"),
            proceeds=Decimal("140.00"),
            is_closed=True,
        )
        replacement = _make_lot(
            lot_id="repl-1",
            account_id="acc-ira",
            open_date=datetime(2026, 6, 20, tzinfo=timezone.utc),
            cost_basis=Decimal("142.00"),
            proceeds=Decimal("0.00"),
            is_closed=False,
        )
        uow = _mock_uow(lots=[loss_lot, replacement])
        svc = TaxService(uow)

        matches = svc.scan_cross_account_wash_sales(tax_year=2026)

        assert len(matches) == 1
        assert matches[0].replacement_lot_id == "repl-1"

    def test_spousal_excluded_when_flag_false(self) -> None:
        """AC-132.7: include_spousal=False excludes spousal accounts."""
        spousal_lot = _make_lot(
            lot_id="spouse-loss",
            account_id="acc-spouse",
            close_date=datetime(2026, 6, 15, tzinfo=timezone.utc),
            cost_basis=Decimal("150.00"),
            proceeds=Decimal("140.00"),
            is_closed=True,
        )

        # Mock account with is_spousal attribute
        spousal_account = MagicMock()
        spousal_account.account_id = "acc-spouse"
        spousal_account.is_spousal = True

        uow = _mock_uow(lots=[spousal_lot], accounts=[spousal_account])
        svc = TaxService(uow)

        matches = svc.scan_cross_account_wash_sales(
            tax_year=2026, include_spousal=False
        )

        # Spousal lots should be filtered out
        assert matches == []

    def test_ira_replacement_creates_destroyed_chain(self) -> None:
        """AC-132.3: Taxable loss + IRA replacement → DESTROYED chain, no basis adjustment."""
        loss_lot = _make_lot(
            lot_id="loss-1",
            account_id="acc-taxable",
            close_date=datetime(2026, 6, 15, tzinfo=timezone.utc),
            cost_basis=Decimal("150.00"),
            proceeds=Decimal("140.00"),
            is_closed=True,
        )
        replacement = _make_lot(
            lot_id="repl-ira",
            account_id="acc-ira",
            open_date=datetime(2026, 6, 20, tzinfo=timezone.utc),
            cost_basis=Decimal("142.00"),
            proceeds=Decimal("0.00"),
            is_closed=False,
        )

        ira_account = MagicMock()
        ira_account.account_id = "acc-ira"
        ira_account.account_type = AccountType.IRA
        ira_account.is_tax_advantaged = True

        taxable_acct = MagicMock()
        taxable_acct.account_id = "acc-taxable"
        taxable_acct.account_type = AccountType.BROKER
        taxable_acct.is_tax_advantaged = False

        uow = _mock_uow(
            lots=[loss_lot, replacement],
            accounts=[ira_account, taxable_acct],
        )
        svc = TaxService(uow)

        matches = svc.scan_cross_account_wash_sales(tax_year=2026)

        assert len(matches) == 1
        # Chain was saved with DESTROYED status
        uow.wash_sale_chains.save.assert_called_once()
        saved_chain = uow.wash_sale_chains.save.call_args[0][0]
        assert saved_chain.status == WashSaleStatus.DESTROYED
        # Has LOSS_DESTROYED entry (plus LOSS_DISALLOWED from start_chain)
        destroyed_entries = [
            e
            for e in saved_chain.entries
            if e.event_type == WashSaleEventType.LOSS_DESTROYED
        ]
        assert len(destroyed_entries) == 1
        assert destroyed_entries[0].account_id == "acc-ira"
        # No basis adjustment — IRA loss is permanently gone
        uow.tax_lots.update.assert_not_called()

    def test_taxable_replacement_creates_absorbed_chain(self) -> None:
        """Cross-account taxable→taxable → ABSORBED chain + basis adjustment."""
        loss_lot = _make_lot(
            lot_id="loss-1",
            account_id="acc-taxable-1",
            close_date=datetime(2026, 6, 15, tzinfo=timezone.utc),
            cost_basis=Decimal("150.00"),
            proceeds=Decimal("140.00"),
            is_closed=True,
        )
        replacement = _make_lot(
            lot_id="repl-1",
            account_id="acc-taxable-2",
            open_date=datetime(2026, 6, 20, tzinfo=timezone.utc),
            cost_basis=Decimal("142.00"),
            proceeds=Decimal("0.00"),
            is_closed=False,
        )

        acct1 = MagicMock()
        acct1.account_id = "acc-taxable-1"
        acct1.is_tax_advantaged = False

        acct2 = MagicMock()
        acct2.account_id = "acc-taxable-2"
        acct2.is_tax_advantaged = False

        uow = _mock_uow(
            lots=[loss_lot, replacement],
            accounts=[acct1, acct2],
        )
        svc = TaxService(uow)

        matches = svc.scan_cross_account_wash_sales(tax_year=2026)

        assert len(matches) == 1
        # Chain saved with ABSORBED status
        uow.wash_sale_chains.save.assert_called_once()
        saved_chain = uow.wash_sale_chains.save.call_args[0][0]
        assert saved_chain.status == WashSaleStatus.ABSORBED
        # Has BASIS_ADJUSTED entry
        basis_entries = [
            e
            for e in saved_chain.entries
            if e.event_type == WashSaleEventType.BASIS_ADJUSTED
        ]
        assert len(basis_entries) == 1
        # Replacement lot was updated
        uow.tax_lots.update.assert_called_once()

    def test_mixed_ira_and_taxable_replacements(self) -> None:
        """AC-132.3 boundary: one IRA repl → DESTROYED, one taxable repl → ABSORBED."""
        loss_lot = _make_lot(
            lot_id="loss-1",
            account_id="acc-taxable",
            close_date=datetime(2026, 6, 15, tzinfo=timezone.utc),
            quantity=100.0,
            cost_basis=Decimal("150.00"),
            proceeds=Decimal("140.00"),
            is_closed=True,
        )
        repl_ira = _make_lot(
            lot_id="repl-ira",
            account_id="acc-ira",
            open_date=datetime(2026, 6, 20, tzinfo=timezone.utc),
            quantity=60.0,
            cost_basis=Decimal("142.00"),
            proceeds=Decimal("0.00"),
            is_closed=False,
        )
        repl_taxable = _make_lot(
            lot_id="repl-tax",
            account_id="acc-taxable-2",
            open_date=datetime(2026, 6, 21, tzinfo=timezone.utc),
            quantity=40.0,
            cost_basis=Decimal("143.00"),
            proceeds=Decimal("0.00"),
            is_closed=False,
        )

        ira_acct = MagicMock()
        ira_acct.account_id = "acc-ira"
        ira_acct.account_type = AccountType.IRA
        ira_acct.is_tax_advantaged = True

        tax_acct = MagicMock()
        tax_acct.account_id = "acc-taxable"
        tax_acct.account_type = AccountType.BROKER
        tax_acct.is_tax_advantaged = False

        tax_acct2 = MagicMock()
        tax_acct2.account_id = "acc-taxable-2"
        tax_acct2.account_type = AccountType.BROKER
        tax_acct2.is_tax_advantaged = False

        uow = _mock_uow(
            lots=[loss_lot, repl_ira, repl_taxable],
            accounts=[ira_acct, tax_acct, tax_acct2],
        )
        svc = TaxService(uow)

        matches = svc.scan_cross_account_wash_sales(tax_year=2026)

        assert len(matches) == 2
        # Two chains saved — one DESTROYED (IRA), one ABSORBED (taxable)
        assert uow.wash_sale_chains.save.call_count == 2
        saved_chains = [c[0][0] for c in uow.wash_sale_chains.save.call_args_list]
        statuses = {c.status for c in saved_chains}
        assert WashSaleStatus.DESTROYED in statuses
        assert WashSaleStatus.ABSORBED in statuses
        # Only taxable replacement gets basis update
        uow.tax_lots.update.assert_called_once()

    def test_k401_replacement_not_destroyed(self) -> None:
        """AC-132.3 guard: K401 is tax-advantaged but NOT IRA — must NOT trigger DESTROYED.

        K401 permanent-loss destruction is deferred pending human approval.
        Until then, K401 replacements get standard ABSORBED treatment.
        """

        loss_lot = _make_lot(
            lot_id="loss-1",
            account_id="acc-taxable",
            close_date=datetime(2026, 6, 15, tzinfo=timezone.utc),
            cost_basis=Decimal("150.00"),
            proceeds=Decimal("140.00"),
            is_closed=True,
        )
        replacement = _make_lot(
            lot_id="repl-k401",
            account_id="acc-k401",
            open_date=datetime(2026, 6, 20, tzinfo=timezone.utc),
            cost_basis=Decimal("142.00"),
            proceeds=Decimal("0.00"),
            is_closed=False,
        )

        k401_acct = MagicMock()
        k401_acct.account_id = "acc-k401"
        k401_acct.account_type = AccountType.K401
        k401_acct.is_tax_advantaged = True

        taxable_acct = MagicMock()
        taxable_acct.account_id = "acc-taxable"
        taxable_acct.account_type = AccountType.BROKER
        taxable_acct.is_tax_advantaged = False

        uow = _mock_uow(
            lots=[loss_lot, replacement],
            accounts=[k401_acct, taxable_acct],
        )
        svc = TaxService(uow)

        matches = svc.scan_cross_account_wash_sales(tax_year=2026)

        assert len(matches) == 1
        # Chain saved with ABSORBED status — NOT DESTROYED
        uow.wash_sale_chains.save.assert_called_once()
        saved_chain = uow.wash_sale_chains.save.call_args[0][0]
        assert saved_chain.status == WashSaleStatus.ABSORBED
        # Basis adjustment applied (standard treatment)
        uow.tax_lots.update.assert_called_once()


# ── F1: Service-level option candidate retrieval ─────────────────────────


class TestOptionCandidateRetrieval:
    """F1: detect_and_apply_wash_sales must include option lots as candidates
    when using CONSERVATIVE mode (AC-133.5).
    """

    def test_conservative_mode_includes_option_candidates(self) -> None:
        """Stock loss + option replacement in CONSERVATIVE mode → match found."""
        from zorivest_core.domain.enums import WashSaleMatchingMethod

        loss_lot = _make_lot(
            lot_id="loss-stock",
            ticker="AAPL",
            account_id="acc-taxable",
            close_date=SALE_DATE,
            cost_basis=Decimal("150.00"),
            proceeds=Decimal("140.00"),
            is_closed=True,
        )
        # Option lot on same underlying, purchased within 30-day window
        option_lot = _make_lot(
            lot_id="repl-option",
            ticker="AAPL 260420 C 200",  # Normalized option format
            account_id="acc-taxable",
            open_date=REPLACEMENT_DATE,
            cost_basis=Decimal("5.00"),
            proceeds=Decimal("0.00"),
            is_closed=False,
            quantity=1.0,
        )

        # Create mock profile with CONSERVATIVE method
        profile = MagicMock()
        profile.include_drip_wash_detection = True
        profile.wash_sale_method = WashSaleMatchingMethod.CONSERVATIVE

        uow = _mock_uow(lots=[loss_lot, option_lot])
        uow.tax_profiles.get_for_year.return_value = profile
        svc = TaxService(uow)

        matches = svc.detect_and_apply_wash_sales(loss_lot_id="loss-stock")

        # AC-133.5: option lot should be detected as replacement
        assert len(matches) == 1
        assert matches[0].replacement_lot_id == "repl-option"

    def test_aggressive_mode_excludes_option_candidates(self) -> None:
        """Stock loss + option replacement in AGGRESSIVE mode → no match."""
        from zorivest_core.domain.enums import WashSaleMatchingMethod

        loss_lot = _make_lot(
            lot_id="loss-stock",
            ticker="AAPL",
            account_id="acc-taxable",
            close_date=SALE_DATE,
            cost_basis=Decimal("150.00"),
            proceeds=Decimal("140.00"),
            is_closed=True,
        )
        option_lot = _make_lot(
            lot_id="repl-option",
            ticker="AAPL 260420 C 200",
            account_id="acc-taxable",
            open_date=REPLACEMENT_DATE,
            cost_basis=Decimal("5.00"),
            proceeds=Decimal("0.00"),
            is_closed=False,
            quantity=1.0,
        )

        profile = MagicMock()
        profile.include_drip_wash_detection = True
        profile.wash_sale_method = WashSaleMatchingMethod.AGGRESSIVE

        uow = _mock_uow(lots=[loss_lot, option_lot])
        uow.tax_profiles.get_for_year.return_value = profile
        svc = TaxService(uow)

        matches = svc.detect_and_apply_wash_sales(loss_lot_id="loss-stock")

        # AGGRESSIVE: only exact ticker match, so no match for option
        assert len(matches) == 0


# ── F4: Spousal include_spousal wiring from TaxProfile ───────────────────


class TestSpousalIncludeWiring:
    """F4: check_wash_sale_conflicts must wire TaxProfile.include_spousal_accounts
    to check_conflicts(include_spousal=...) (AC-135.4).
    """

    def test_include_spousal_false_excludes_spousal_warnings(self) -> None:
        """Profile says include_spousal=False + spousal lots → no spousal warnings."""
        from zorivest_core.domain.tax.wash_sale_warnings import WarningType

        NOW = datetime(2026, 5, 10, tzinfo=timezone.utc)

        # Loss in spousal account, closed 10 days ago
        spousal_loss = _make_lot(
            lot_id="spousal-loss",
            ticker="AAPL",
            account_id="acc-spouse",
            close_date=NOW - timedelta(days=10),
            cost_basis=Decimal("160.00"),
            proceeds=Decimal("140.00"),
            is_closed=True,
        )

        # Profile with include_spousal_accounts=False
        profile = MagicMock()
        profile.include_spousal_accounts = False

        uow = _mock_uow(lots=[spousal_loss])
        uow.tax_profiles.get_for_year.return_value = profile
        svc = TaxService(uow)

        warnings = svc.check_wash_sale_conflicts(
            ticker="AAPL",
            now=NOW,
            spousal_lot_ids={"spousal-loss"},
        )

        # F4: spousal warnings should be excluded
        spousal_warnings = [
            w for w in warnings if w.warning_type == WarningType.SPOUSAL_CONFLICT
        ]
        assert len(spousal_warnings) == 0

    def test_include_spousal_true_includes_spousal_warnings(self) -> None:
        """Profile says include_spousal=True + spousal lots → spousal warning."""
        from zorivest_core.domain.tax.wash_sale_warnings import WarningType

        NOW = datetime(2026, 5, 10, tzinfo=timezone.utc)

        spousal_loss = _make_lot(
            lot_id="spousal-loss",
            ticker="AAPL",
            account_id="acc-spouse",
            close_date=NOW - timedelta(days=10),
            cost_basis=Decimal("160.00"),
            proceeds=Decimal("140.00"),
            is_closed=True,
        )

        profile = MagicMock()
        profile.include_spousal_accounts = True

        uow = _mock_uow(lots=[spousal_loss])
        uow.tax_profiles.get_for_year.return_value = profile
        svc = TaxService(uow)

        warnings = svc.check_wash_sale_conflicts(
            ticker="AAPL",
            now=NOW,
            spousal_lot_ids={"spousal-loss"},
        )

        spousal_warnings = [
            w for w in warnings if w.warning_type == WarningType.SPOUSAL_CONFLICT
        ]
        assert len(spousal_warnings) == 1
