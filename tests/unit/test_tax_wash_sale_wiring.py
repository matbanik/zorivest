# tests/unit/test_tax_wash_sale_wiring.py
"""FIC tests for MEU-218c — Wash Sale Scan Pipeline Wiring.

Feature Intent Contract:
  TaxService.get_trapped_losses() and scan_cross_account_wash_sales(tax_year)
  wire the existing wash sale detector + chain manager + repository into the
  service layer, completing the end-to-end pipeline.

  Behaviors:
    - AC-218c-1: get_trapped_losses() returns active chains via UoW
    - AC-218c-2: scan_cross_account_wash_sales() orchestrates detect → chain → persist
    - AC-218c-3: Scan is idempotent (re-running doesn't duplicate)
    - AC-218c-4: Replacement lot wash_sale_adjustment updated after absorb

All tests written per TDD protocol. Methods exist — validating untested wiring.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock


from zorivest_core.domain.entities import TaxLot
from zorivest_core.domain.enums import WashSaleStatus, AccountType
from zorivest_core.domain.tax.wash_sale import WashSaleChain
from zorivest_core.services.tax_service import TaxService


# ── Helpers ──────────────────────────────────────────────────────────────


def _make_lot(
    lot_id: str = "L1",
    ticker: str = "META",
    account_id: str = "ACC-1",
    quantity: float = 100.0,
    cost_basis: Decimal = Decimal("200.00"),
    proceeds: Decimal = Decimal("0.00"),
    is_closed: bool = False,
    open_date: datetime | None = None,
    close_date: datetime | None = None,
    wash_sale_adjustment: Decimal = Decimal("0.00"),
) -> TaxLot:
    return TaxLot(
        lot_id=lot_id,
        account_id=account_id,
        ticker=ticker,
        open_date=open_date or datetime(2025, 3, 1, tzinfo=timezone.utc),
        close_date=close_date,
        quantity=quantity,
        cost_basis=cost_basis,
        proceeds=proceeds,
        wash_sale_adjustment=wash_sale_adjustment,
        is_closed=is_closed,
        linked_trade_ids=[],
    )


def _make_chain(
    chain_id: str = "CH-1",
    ticker: str = "META",
    loss_lot_id: str = "L-LOSS",
    status: WashSaleStatus = WashSaleStatus.ABSORBED,
    disallowed_amount: Decimal = Decimal("1000.00"),
) -> WashSaleChain:
    return WashSaleChain(
        chain_id=chain_id,
        ticker=ticker,
        loss_lot_id=loss_lot_id,
        loss_date=datetime(2025, 4, 5, tzinfo=timezone.utc),
        loss_amount=Decimal("1000.00"),
        disallowed_amount=disallowed_amount,
        status=status,
        loss_open_date=datetime(2025, 1, 15, tzinfo=timezone.utc),
        entries=[],
    )


def _mock_uow(
    lots: list[TaxLot] | None = None,
    chains: list[WashSaleChain] | None = None,
    tax_advantaged_account_ids: set[str] | None = None,
) -> MagicMock:
    """Create a mock UoW for wash sale wiring tests."""
    uow = MagicMock()
    uow.__enter__ = MagicMock(return_value=uow)
    uow.__exit__ = MagicMock(return_value=False)

    all_lots = lots or []
    lot_map = {lot.lot_id: lot for lot in all_lots}

    # tax_lots repo
    uow.tax_lots.list_all_filtered.return_value = all_lots
    uow.tax_lots.get.side_effect = lambda lid: lot_map.get(lid)

    # wash_sale_chains repo
    all_chains = chains or []
    uow.wash_sale_chains.list_active.return_value = all_chains
    uow.wash_sale_chains.list_for_ticker.return_value = []

    # accounts repo
    advantaged = tax_advantaged_account_ids or set()

    def _get_account(aid: str) -> MagicMock:
        acct = MagicMock()
        acct.account_id = aid
        acct.is_tax_advantaged = aid in advantaged
        acct.account_type = AccountType.IRA if aid in advantaged else AccountType.BROKER
        acct.is_spousal = False
        return acct

    uow.accounts.get.side_effect = _get_account
    uow.accounts.list_all.return_value = [
        _get_account(aid) for aid in {lot.account_id for lot in all_lots}
    ]

    # tax_profiles repo — no profile (defaults)
    uow.tax_profiles.get_for_year.return_value = None

    # settings repo
    uow.settings = MagicMock()
    uow.settings.get.return_value = "flag"

    return uow


# ── Group 1: get_trapped_losses() ────────────────────────────────────────


class TestGetTrappedLosses:
    """AC-218c-1: get_trapped_losses() returns active chains from UoW."""

    def test_returns_active_chains(self) -> None:
        """Two chains with ABSORBED status — both returned."""
        chains = [
            _make_chain("CH-1", status=WashSaleStatus.ABSORBED),
            _make_chain("CH-2", loss_lot_id="L-LOSS-2", status=WashSaleStatus.ABSORBED),
        ]
        uow = _mock_uow(chains=chains)
        svc = TaxService(uow)

        result = svc.get_trapped_losses()

        assert len(result) == 2
        uow.wash_sale_chains.list_active.assert_called_once()

    def test_empty_when_no_chains(self) -> None:
        """No chains → empty list."""
        uow = _mock_uow(chains=[])
        svc = TaxService(uow)

        result = svc.get_trapped_losses()

        assert result == []

    def test_returns_only_absorbed_status(self) -> None:
        """list_active is called with ABSORBED filter — repository handles filtering."""
        uow = _mock_uow(chains=[])
        svc = TaxService(uow)

        svc.get_trapped_losses()

        # Verify the service passes the correct status filter
        uow.wash_sale_chains.list_active.assert_called_once_with(
            status=WashSaleStatus.ABSORBED,
        )


# ── Group 2: scan_cross_account_wash_sales() ─────────────────────────────


class TestScanCrossAccountWashSales:
    """AC-218c-2: scan_cross_account_wash_sales() orchestrates full pipeline."""

    def test_detects_wash_sale_within_window(self) -> None:
        """Loss lot + replacement 15 days later → at least 1 match."""
        loss_lot = _make_lot(
            lot_id="L-LOSS",
            ticker="META",
            is_closed=True,
            cost_basis=Decimal("200.00"),
            proceeds=Decimal("150.00"),  # $50/share loss
            open_date=datetime(2025, 1, 15, tzinfo=timezone.utc),
            close_date=datetime(2025, 4, 5, tzinfo=timezone.utc),
        )
        replacement_lot = _make_lot(
            lot_id="L-REPL",
            ticker="META",
            is_closed=False,
            cost_basis=Decimal("155.00"),
            open_date=datetime(2025, 4, 20, tzinfo=timezone.utc),  # 15 days after sale
        )
        uow = _mock_uow(lots=[loss_lot, replacement_lot])
        svc = TaxService(uow)

        matches = svc.scan_cross_account_wash_sales(2025)

        assert len(matches) >= 1
        assert matches[0].loss_lot_id == "L-LOSS"
        assert matches[0].replacement_lot_id == "L-REPL"
        # Chains should be persisted
        uow.wash_sale_chains.save.assert_called()
        uow.commit.assert_called()

    def test_no_chains_when_no_losses(self) -> None:
        """Only gains → no matches."""
        gain_lot = _make_lot(
            lot_id="L-GAIN",
            is_closed=True,
            cost_basis=Decimal("100.00"),
            proceeds=Decimal("200.00"),  # Gain, not loss
            close_date=datetime(2025, 6, 1, tzinfo=timezone.utc),
        )
        uow = _mock_uow(lots=[gain_lot])
        svc = TaxService(uow)

        matches = svc.scan_cross_account_wash_sales(2025)

        assert matches == []
        uow.wash_sale_chains.save.assert_not_called()

    def test_no_chains_outside_window(self) -> None:
        """Replacement purchased 45 days after loss → outside 30-day window."""
        loss_lot = _make_lot(
            lot_id="L-LOSS",
            ticker="META",
            is_closed=True,
            cost_basis=Decimal("200.00"),
            proceeds=Decimal("150.00"),
            open_date=datetime(2025, 1, 15, tzinfo=timezone.utc),
            close_date=datetime(2025, 4, 5, tzinfo=timezone.utc),
        )
        outside_lot = _make_lot(
            lot_id="L-FAR",
            ticker="META",
            is_closed=False,
            open_date=datetime(2025, 5, 20, tzinfo=timezone.utc),  # 45 days after
        )
        uow = _mock_uow(lots=[loss_lot, outside_lot])
        svc = TaxService(uow)

        matches = svc.scan_cross_account_wash_sales(2025)

        assert matches == []

    def test_scan_idempotent(self) -> None:
        """AC-218c-3: Running scan twice with same data → same match count."""
        loss_lot = _make_lot(
            lot_id="L-LOSS",
            ticker="META",
            is_closed=True,
            cost_basis=Decimal("200.00"),
            proceeds=Decimal("150.00"),
            open_date=datetime(2025, 1, 15, tzinfo=timezone.utc),
            close_date=datetime(2025, 4, 5, tzinfo=timezone.utc),
        )
        replacement = _make_lot(
            lot_id="L-REPL",
            ticker="META",
            is_closed=False,
            open_date=datetime(2025, 4, 20, tzinfo=timezone.utc),
        )
        uow = _mock_uow(lots=[loss_lot, replacement])
        svc = TaxService(uow)

        matches_1 = svc.scan_cross_account_wash_sales(2025)
        matches_2 = svc.scan_cross_account_wash_sales(2025)

        # Both scans should produce the same count of matches
        # (idempotency at the detection level — same inputs, same outputs)
        assert len(matches_1) == len(matches_2)

    def test_adjusts_replacement_basis(self) -> None:
        """AC-218c-4: After scan, replacement lot's wash_sale_adjustment increases."""
        loss_lot = _make_lot(
            lot_id="L-LOSS",
            ticker="META",
            is_closed=True,
            cost_basis=Decimal("200.00"),
            proceeds=Decimal("150.00"),
            open_date=datetime(2025, 1, 15, tzinfo=timezone.utc),
            close_date=datetime(2025, 4, 5, tzinfo=timezone.utc),
        )
        replacement = _make_lot(
            lot_id="L-REPL",
            ticker="META",
            is_closed=False,
            cost_basis=Decimal("155.00"),
            open_date=datetime(2025, 4, 20, tzinfo=timezone.utc),
        )
        uow = _mock_uow(lots=[loss_lot, replacement])
        svc = TaxService(uow)

        matches = svc.scan_cross_account_wash_sales(2025)

        assert len(matches) >= 1
        # The UoW's tax_lots.update should have been called with an
        # updated replacement lot (wash_sale_adjustment > 0)
        update_calls = uow.tax_lots.update.call_args_list
        assert len(update_calls) >= 1
        updated_lot = update_calls[0][0][0]
        assert updated_lot.wash_sale_adjustment > Decimal("0")


# ── Group 3: Round-trip ──────────────────────────────────────────────────


class TestScanThenGetTrapped:
    """AC-218c-1 + AC-218c-2: End-to-end pipeline validation."""

    def test_scan_then_get_trapped_returns_chain(self) -> None:
        """After scan creates chains, get_trapped_losses sees them."""
        loss_lot = _make_lot(
            lot_id="L-LOSS",
            ticker="META",
            is_closed=True,
            cost_basis=Decimal("200.00"),
            proceeds=Decimal("150.00"),
            open_date=datetime(2025, 1, 15, tzinfo=timezone.utc),
            close_date=datetime(2025, 4, 5, tzinfo=timezone.utc),
        )
        replacement = _make_lot(
            lot_id="L-REPL",
            ticker="META",
            is_closed=False,
            open_date=datetime(2025, 4, 20, tzinfo=timezone.utc),
        )
        uow = _mock_uow(lots=[loss_lot, replacement])
        svc = TaxService(uow)

        # Step 1: Scan creates chains
        matches = svc.scan_cross_account_wash_sales(2025)
        assert len(matches) >= 1

        # Step 2: Capture the chain that was saved
        saved_chain = uow.wash_sale_chains.save.call_args[0][0]
        assert isinstance(saved_chain, WashSaleChain)
        assert saved_chain.ticker == "META"
        assert saved_chain.loss_lot_id == "L-LOSS"

        # Step 3: Mock list_active to return the saved chain for get_trapped
        uow.wash_sale_chains.list_active.return_value = [saved_chain]

        trapped = svc.get_trapped_losses()
        assert len(trapped) == 1
        assert trapped[0].chain_id == saved_chain.chain_id
