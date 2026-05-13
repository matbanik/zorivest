# tests/integration/test_tax_service_integration.py
"""Integration tests for TaxService with real SQLite — MEU-126 AC-126.6.

Tests the full round-trip: get_lots → close_lot → gain calculation
using a real SqlAlchemyUnitOfWork backed by in-memory SQLite.

AC-126.6: Verify TaxService orchestration with real persistence.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from zorivest_core.domain.entities import TaxLot, Trade
from zorivest_core.domain.enums import (
    CostBasisMethod,
    TradeAction,
)
from zorivest_core.domain.exceptions import BusinessRuleError, NotFoundError
from zorivest_core.services.tax_service import TaxService


# ── Fixtures ────────────────────────────────────────────────────────────


@pytest.fixture()
def uow(engine):
    """Create a real SqlAlchemyUnitOfWork backed by in-memory SQLite."""
    from zorivest_infra.database.unit_of_work import SqlAlchemyUnitOfWork

    return SqlAlchemyUnitOfWork(engine)


@pytest.fixture()
def seeded_uow(uow):
    """UoW pre-seeded with 2 open lots and 1 sell trade."""
    with uow:
        lot1 = TaxLot(
            lot_id="lot-int-1",
            account_id="acct-int",
            ticker="AAPL",
            open_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
            close_date=None,
            quantity=100.0,
            cost_basis=Decimal("100.00"),
            proceeds=Decimal("0.00"),
            wash_sale_adjustment=Decimal("0.00"),
            is_closed=False,
            linked_trade_ids=[],
        )
        lot2 = TaxLot(
            lot_id="lot-int-2",
            account_id="acct-int",
            ticker="AAPL",
            open_date=datetime(2025, 11, 1, tzinfo=timezone.utc),
            close_date=None,
            quantity=50.0,
            cost_basis=Decimal("120.00"),
            proceeds=Decimal("0.00"),
            wash_sale_adjustment=Decimal("0.00"),
            is_closed=False,
            linked_trade_ids=[],
        )
        sell_trade = Trade(
            exec_id="trade-sell-1",
            time=datetime(2026, 5, 12, 10, 0, tzinfo=timezone.utc),
            instrument="AAPL",
            action=TradeAction.SLD,
            quantity=100.0,
            price=150.0,
            account_id="acct-int",
        )

        uow.tax_lots.save(lot1)
        uow.tax_lots.save(lot2)
        uow.trades.save(sell_trade)
        uow.commit()

    return uow


# ── Integration: get_lots ───────────────────────────────────────────────


class TestGetLotsIntegration:
    """get_lots with real SQLite returns persisted lots."""

    def test_get_lots_returns_seeded(self, seeded_uow) -> None:
        svc = TaxService(seeded_uow)
        lots = svc.get_lots(account_id="acct-int", ticker="AAPL")
        assert len(lots) == 2

    def test_get_lots_filter_closed(self, seeded_uow) -> None:
        svc = TaxService(seeded_uow)
        lots = svc.get_lots(account_id="acct-int", status="open")
        assert len(lots) == 2

    def test_get_lots_empty_account(self, seeded_uow) -> None:
        svc = TaxService(seeded_uow)
        lots = svc.get_lots(account_id="nonexistent")
        assert lots == []


# ── Integration: close_lot ──────────────────────────────────────────────


class TestCloseLotIntegration:
    """close_lot with real SQLite persists lot closure."""

    def test_close_lot_roundtrip(self, seeded_uow) -> None:
        svc = TaxService(seeded_uow)
        closed = svc.close_lot("lot-int-1", "trade-sell-1")

        assert closed.is_closed is True
        assert closed.close_date is not None
        assert closed.proceeds == Decimal("150.0")

        # Verify persisted
        with seeded_uow:
            fetched = seeded_uow.tax_lots.get("lot-int-1")
            assert fetched is not None
            assert fetched.is_closed is True

    def test_close_lot_nonexistent_raises(self, seeded_uow) -> None:
        svc = TaxService(seeded_uow)
        with pytest.raises(NotFoundError):
            svc.close_lot("lot-missing", "trade-sell-1")

    def test_close_lot_partial_close_roundtrip(self, uow) -> None:
        """RR3-1: Partial close creates remainder lot via real SQLite round-trip.

        Seeds a 100-share lot + 40-share sell trade. After close_lot:
        - Sold lot: closed, qty=40, realized gain computed
        - Remainder lot: open, qty=60, inherited basis/dates
        - Total quantity conserved: 40 + 60 = 100
        """
        # Seed: 100-share lot + 40-share partial sell
        with uow:
            lot = TaxLot(
                lot_id="lot-partial",
                account_id="acct-partial",
                ticker="TSLA",
                open_date=datetime(2023, 6, 15, tzinfo=timezone.utc),
                close_date=None,
                quantity=100.0,
                cost_basis=Decimal("200.00"),
                proceeds=Decimal("0.00"),
                wash_sale_adjustment=Decimal("3.50"),
                is_closed=False,
                linked_trade_ids=[],
            )
            sell_trade = Trade(
                exec_id="trade-partial-sell",
                time=datetime(2026, 5, 12, 14, 0, tzinfo=timezone.utc),
                instrument="TSLA",
                action=TradeAction.SLD,
                quantity=40.0,
                price=250.0,
                account_id="acct-partial",
            )
            uow.tax_lots.save(lot)
            uow.trades.save(sell_trade)
            uow.commit()

        # Act: partial close
        svc = TaxService(uow)
        closed = svc.close_lot("lot-partial", "trade-partial-sell")

        # Assert return value
        assert closed.is_closed is True
        assert closed.quantity == 40.0
        assert closed.proceeds == Decimal("250.0")
        # Gain = (250 - (200 + 3.50)) * 40 = 46.50 * 40 = 1860
        assert closed.realized_gain_loss == Decimal("1860.00")

        # Verify persistence: reopen UoW and check both lots
        with uow:
            sold = uow.tax_lots.get("lot-partial")
            assert sold is not None
            assert sold.is_closed is True
            assert sold.quantity == 40.0
            assert sold.realized_gain_loss == Decimal("1860.00")
            assert sold.close_date is not None

            remainder = uow.tax_lots.get("lot-partial-R")
            assert remainder is not None
            assert remainder.is_closed is False
            assert remainder.quantity == 60.0
            assert remainder.cost_basis == Decimal("200.00")
            assert remainder.open_date == datetime(2023, 6, 15, tzinfo=timezone.utc)
            assert remainder.wash_sale_adjustment == Decimal("3.50")
            assert remainder.close_date is None
            assert remainder.account_id == "acct-partial"
            assert remainder.ticker == "TSLA"

            # Quantity conservation
            assert sold.quantity + remainder.quantity == 100.0


# ── Integration: simulate_impact ────────────────────────────────────────


class TestSimulateImpactIntegration:
    """simulate_impact with real SQLite verifies end-to-end."""

    def test_simulate_lt_st_split(self, seeded_uow) -> None:
        """Full round-trip: select lots, compute gain, split ST/LT."""
        svc = TaxService(seeded_uow)
        result = svc.simulate_impact(
            account_id="acct-int",
            ticker="AAPL",
            quantity=150.0,
            sale_price=Decimal("150.00"),
            method=CostBasisMethod.FIFO,
        )

        # FIFO: lot-int-1 (LT, 100 shares, basis $100) → lot-int-2 (ST, 50 shares, basis $120)
        assert len(result.lot_details) == 2
        assert result.lot_details[0].lot_id == "lot-int-1"
        assert result.lot_details[0].is_long_term is True
        assert result.lot_details[0].gain_amount == Decimal("5000.00")

        assert result.lot_details[1].lot_id == "lot-int-2"
        assert result.lot_details[1].is_long_term is False
        assert result.lot_details[1].gain_amount == Decimal("1500.00")

        assert result.total_lt_gain == Decimal("5000.00")
        assert result.total_st_gain == Decimal("1500.00")

    def test_simulate_with_tax_estimate(self, seeded_uow) -> None:
        svc = TaxService(seeded_uow)
        result = svc.simulate_impact(
            account_id="acct-int",
            ticker="AAPL",
            quantity=100.0,
            sale_price=Decimal("150.00"),
            method=CostBasisMethod.FIFO,
            federal_rate=0.20,
            state_rate=0.05,
        )

        # 100 shares from lot-int-1 (LT), gain = (150-100)*100 = 5000
        # tax = 5000 * 0.25 = 1250
        assert result.estimated_tax == Decimal("1250.00")

    def test_simulate_no_lots_raises(self, seeded_uow) -> None:
        svc = TaxService(seeded_uow)
        with pytest.raises(BusinessRuleError, match="no open lots"):
            svc.simulate_impact(
                account_id="acct-int",
                ticker="MSFT",  # No MSFT lots
                quantity=100.0,
                sale_price=Decimal("300.00"),
                method=CostBasisMethod.FIFO,
            )
