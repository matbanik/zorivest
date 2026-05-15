# tests/unit/test_tax_deferred_loss.py
"""FIC tests for TaxService.deferred_loss_report() — MEU-151 ACs 151.1–151.5.

Feature Intent Contract:
  deferred_loss_report(tax_year=None) → DeferredLossReport
  Composes: get_trapped_losses, lot enrichment, IRA-destroyed chains.

Acceptance Criteria:
  AC-151.1: Method accepts optional tax_year: int
             Source: Spec: build-priority-matrix.md item 78
  AC-151.2: Returns DeferredLossReport with trapped_chains[], total_deferred,
             total_permanent_loss
             Source: Spec: domain-model-reference.md L353-366
  AC-151.3: Uses get_trapped_losses() to load ABSORBED chains, enriches with lot details
             Source: Local Canon: TaxService.get_trapped_losses()
  AC-151.4: Computes real_pnl vs reported_pnl delta
             Source: Spec: build-priority-matrix.md "Real P&L vs reported P&L"
  AC-151.5: Empty result when no trapped chains
             Source: Local Canon: established empty-result pattern

All tests use mocked UoW — no database access.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock


from zorivest_core.domain.entities import TaxLot
from zorivest_core.domain.enums import (
    WashSaleStatus,
)
from zorivest_core.domain.tax.wash_sale import WashSaleChain
from zorivest_core.services.tax_service import TaxService, DeferredLossReport


# ── Helpers ──────────────────────────────────────────────────────────────


def _closed_lot(
    lot_id: str = "L1",
    ticker: str = "AAPL",
    account_id: str = "ACC-1",
    cost_basis: Decimal = Decimal("100.00"),
    proceeds: Decimal = Decimal("80.00"),
    quantity: float = 100.0,
    open_date: datetime | None = None,
    close_date: datetime | None = None,
) -> TaxLot:
    return TaxLot(
        lot_id=lot_id,
        account_id=account_id,
        ticker=ticker,
        open_date=open_date or datetime(2024, 1, 1, tzinfo=timezone.utc),
        close_date=close_date or datetime(2026, 3, 1, tzinfo=timezone.utc),
        quantity=quantity,
        cost_basis=cost_basis,
        proceeds=proceeds,
        wash_sale_adjustment=Decimal("0.00"),
        is_closed=True,
        linked_trade_ids=[],
        realized_gain_loss=(proceeds - cost_basis) * Decimal(str(quantity)),
    )


def _wash_chain(
    chain_id: str = "WSC-1",
    loss_lot_id: str = "L1",
    ticker: str = "AAPL",
    disallowed_amount: Decimal = Decimal("500.00"),
    loss_amount: Decimal = Decimal("2000.00"),
    status: WashSaleStatus = WashSaleStatus.ABSORBED,
    loss_date: datetime | None = None,
) -> WashSaleChain:
    return WashSaleChain(
        chain_id=chain_id,
        ticker=ticker,
        loss_lot_id=loss_lot_id,
        loss_date=loss_date or datetime(2026, 3, 1, tzinfo=timezone.utc),
        loss_amount=loss_amount,
        disallowed_amount=disallowed_amount,
        status=status,
    )


def _mock_uow(
    lots: list[TaxLot] | None = None,
    chains: list[WashSaleChain] | None = None,
) -> MagicMock:
    """Create a mock UnitOfWork for deferred loss tests."""
    uow = MagicMock()
    uow.__enter__ = MagicMock(return_value=uow)
    uow.__exit__ = MagicMock(return_value=False)

    # tax_lots repo
    lot_map = {lot.lot_id: lot for lot in (lots or [])}
    uow.tax_lots.get.side_effect = lambda lid: lot_map.get(lid)
    uow.tax_lots.list_all_filtered.return_value = lots or []

    # wash_sale_chains repo — filter by status like production code
    all_chains = chains or []

    def _list_active(status: WashSaleStatus | None = None) -> list[WashSaleChain]:
        if status is None:
            return all_chains
        return [c for c in all_chains if c.status == status]

    uow.wash_sale_chains.list_active.side_effect = _list_active

    # accounts repo — defaults to non-tax-advantaged
    def _get_account(account_id: str) -> MagicMock:
        acc = MagicMock()
        acc.account_id = account_id
        acc.is_tax_advantaged = False
        return acc

    uow.accounts.get.side_effect = _get_account

    # tax_profiles — not needed for deferred loss
    uow.tax_profiles.get_for_year.return_value = None

    return uow


# ── AC-151.1: Method signature ──────────────────────────────────────────


class TestDeferredLossSignature:
    """AC-151.1: deferred_loss_report accepts optional tax_year."""

    def test_accepts_no_args(self) -> None:
        """AC-151.1: Method works with no arguments."""
        uow = _mock_uow()
        svc = TaxService(uow)
        result = svc.deferred_loss_report()
        assert result is not None

    def test_accepts_tax_year(self) -> None:
        """AC-151.1: Method accepts tax_year parameter."""
        uow = _mock_uow()
        svc = TaxService(uow)
        result = svc.deferred_loss_report(tax_year=2026)
        assert result is not None


# ── AC-151.2: Return type structure ─────────────────────────────────────


class TestDeferredLossReturnType:
    """AC-151.2: Returns DeferredLossReport with required fields."""

    def test_returns_deferred_loss_report(self) -> None:
        """AC-151.2: Return type is DeferredLossReport."""
        uow = _mock_uow()
        svc = TaxService(uow)
        result = svc.deferred_loss_report()
        assert isinstance(result, DeferredLossReport)

    def test_has_all_required_fields(self) -> None:
        """AC-151.2: All required fields present."""
        chain = _wash_chain()
        lot = _closed_lot(lot_id="L1")
        uow = _mock_uow(lots=[lot], chains=[chain])
        svc = TaxService(uow)
        result = svc.deferred_loss_report()

        assert isinstance(result.trapped_chains, list)
        assert isinstance(result.total_deferred, Decimal)
        assert isinstance(result.total_permanent_loss, Decimal)

    def test_chain_detail_fields(self) -> None:
        """AC-151.2: Each chain detail has expected fields."""
        chain = _wash_chain(chain_id="WSC-1", loss_lot_id="L1")
        lot = _closed_lot(lot_id="L1")
        uow = _mock_uow(lots=[lot], chains=[chain])
        svc = TaxService(uow)
        result = svc.deferred_loss_report()

        assert len(result.trapped_chains) == 1
        detail = result.trapped_chains[0]
        assert detail["loss_lot_id"] == "L1"
        assert "original_loss" in detail
        assert "deferred_amount" in detail
        assert "chain_status" in detail


# ── AC-151.3: Composition ──────────────────────────────────────────────


class TestDeferredLossComposition:
    """AC-151.3: Uses get_trapped_losses, enriches with lot details."""

    def test_total_deferred_sums_chain_amounts(self) -> None:
        """AC-151.3: total_deferred = sum of all chain disallowed_amounts."""
        chains = [
            _wash_chain(
                chain_id="WSC-1", loss_lot_id="L1", disallowed_amount=Decimal("500")
            ),
            _wash_chain(
                chain_id="WSC-2", loss_lot_id="L2", disallowed_amount=Decimal("300")
            ),
        ]
        lots = [_closed_lot(lot_id="L1"), _closed_lot(lot_id="L2")]
        uow = _mock_uow(lots=lots, chains=chains)
        svc = TaxService(uow)
        result = svc.deferred_loss_report()

        assert result.total_deferred == Decimal("800")

    def test_permanent_loss_from_destroyed_chains(self) -> None:
        """AC-151.3: total_permanent_loss from DESTROYED status chains."""
        chains = [
            _wash_chain(
                chain_id="WSC-DESTROY",
                loss_lot_id="L1",
                disallowed_amount=Decimal("1000"),
                status=WashSaleStatus.DESTROYED,
            ),
            _wash_chain(
                chain_id="WSC-ABSORB",
                loss_lot_id="L2",
                disallowed_amount=Decimal("500"),
                status=WashSaleStatus.ABSORBED,
            ),
        ]
        lots = [_closed_lot(lot_id="L1"), _closed_lot(lot_id="L2")]
        uow = _mock_uow(lots=lots, chains=chains)
        # Return both types from list_active
        uow.wash_sale_chains.list_active.return_value = chains
        svc = TaxService(uow)
        result = svc.deferred_loss_report()

        assert result.total_permanent_loss == Decimal("1000")
        assert result.total_deferred == Decimal("500")  # Only ABSORBED


# ── AC-151.4: Real vs Reported P&L delta ───────────────────────────────


class TestDeferredLossRealVsReported:
    """AC-151.4: Computes real_pnl vs reported_pnl delta."""

    def test_reported_pnl_excludes_deferred(self) -> None:
        """AC-151.4: reported_pnl = realized gains - deferred losses."""
        chain = _wash_chain(disallowed_amount=Decimal("500"))
        lot = _closed_lot(lot_id="L1")
        uow = _mock_uow(lots=[lot], chains=[chain])
        svc = TaxService(uow)
        result = svc.deferred_loss_report()

        assert isinstance(result.reported_pnl, Decimal)
        assert isinstance(result.real_pnl, Decimal)
        # reported_pnl should be real_pnl minus deferred amount
        assert result.real_pnl - result.reported_pnl == Decimal("500")


# ── AC-151.5: Empty result ─────────────────────────────────────────────


class TestDeferredLossEmpty:
    """AC-151.5: Empty result when no trapped chains."""

    def test_no_chains_returns_zeroed_report(self) -> None:
        """AC-151.5: No chains → all fields zero/empty."""
        uow = _mock_uow()
        svc = TaxService(uow)
        result = svc.deferred_loss_report()

        assert result.trapped_chains == []
        assert result.total_deferred == Decimal("0")
        assert result.total_permanent_loss == Decimal("0")
        assert result.reported_pnl == Decimal("0")
        assert result.real_pnl == Decimal("0")

    def test_no_chains_no_exceptions(self) -> None:
        """AC-151.5: No errors for empty result."""
        uow = _mock_uow()
        svc = TaxService(uow)
        # Should not raise
        result = svc.deferred_loss_report()
        assert result is not None
