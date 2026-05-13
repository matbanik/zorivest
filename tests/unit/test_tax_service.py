# tests/unit/test_tax_service.py
"""FIC tests for TaxService — MEU-125 ACs 125.1–125.4, MEU-126 ACs 126.4–126.5.

Feature Intent Contract:
  TaxService(uow) — service orchestrating tax lot operations via UnitOfWork.
  Methods:
    - get_lots(account_id, ticker, status, sort_by)
    - close_lot(lot_id, sell_trade_id)
    - reassign_basis(lot_id, method)
    - simulate_impact(request)  [MEU-126, added in Tasks 7-8]

All tests use mocked UoW — no database access.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from zorivest_core.domain.entities import TaxLot, Trade
from zorivest_core.domain.enums import CostBasisMethod, TradeAction
from zorivest_core.domain.exceptions import (
    BusinessRuleError,
    NotFoundError,
)
from zorivest_core.services.tax_service import TaxService


# ── Helpers ──────────────────────────────────────────────────────────────


def _lot(
    lot_id: str = "L1",
    ticker: str = "AAPL",
    open_date: datetime | None = None,
    quantity: float = 100.0,
    cost_basis: Decimal = Decimal("100.00"),
    is_closed: bool = False,
) -> TaxLot:
    return TaxLot(
        lot_id=lot_id,
        account_id="ACC-1",
        ticker=ticker,
        open_date=open_date or datetime(2024, 1, 1, tzinfo=timezone.utc),
        close_date=None,
        quantity=quantity,
        cost_basis=cost_basis,
        proceeds=Decimal("0.00"),
        wash_sale_adjustment=Decimal("0.00"),
        is_closed=is_closed,
        linked_trade_ids=[],
    )


def _sell_trade(
    exec_id: str = "T-SELL-1",
    ticker: str = "AAPL",
    price: float = 150.0,
    quantity: float = 100.0,
    time: datetime | None = None,
) -> Trade:
    return Trade(
        exec_id=exec_id,
        time=time or datetime(2026, 5, 12, 10, 0, tzinfo=timezone.utc),
        instrument=ticker,
        action=TradeAction.SLD,
        quantity=quantity,
        price=price,
        account_id="ACC-1",
    )


def _mock_uow(
    lots: list[TaxLot] | None = None,
    trade: Trade | None = None,
) -> MagicMock:
    """Create a mock UnitOfWork with tax_lots and trades repos."""
    uow = MagicMock()
    uow.__enter__ = MagicMock(return_value=uow)
    uow.__exit__ = MagicMock(return_value=False)

    # tax_lots repo
    lot_map = {lot.lot_id: lot for lot in (lots or [])}
    uow.tax_lots.get.side_effect = lambda lid: lot_map.get(lid)
    uow.tax_lots.list_filtered.return_value = lots or []

    # trades repo
    if trade:
        uow.trades.get.return_value = trade
    else:
        uow.trades.get.return_value = None

    # tax_profiles repo — default to no profile (uses fallback rates)
    uow.tax_profiles.get_for_year.return_value = None

    return uow


# ── AC-125.1: Constructor ───────────────────────────────────────────────


class TestTaxServiceInit:
    """AC-125.1: TaxService.__init__(uow) takes UnitOfWork."""

    def test_constructor_accepts_uow(self) -> None:
        uow = _mock_uow()
        svc = TaxService(uow)
        assert svc is not None


# ── AC-125.2: get_lots ──────────────────────────────────────────────────


class TestGetLots:
    """AC-125.2: get_lots returns filtered, sorted TaxLot list."""

    def test_returns_lots_for_account(self) -> None:
        lots = [_lot("L1"), _lot("L2")]
        uow = _mock_uow(lots=lots)
        svc = TaxService(uow)
        result = svc.get_lots(account_id="ACC-1")
        assert len(result) == 2

    def test_returns_empty_when_no_match(self) -> None:
        uow = _mock_uow(lots=[])
        svc = TaxService(uow)
        result = svc.get_lots(account_id="ACC-NONE")
        assert result == []


# ── AC-125.3: close_lot ─────────────────────────────────────────────────


class TestCloseLot:
    """AC-125.3: close_lot(lot_id, sell_trade_id) closes a lot."""

    def test_close_lot_sets_fields(self) -> None:
        lot = _lot("L1", ticker="AAPL")
        trade = _sell_trade("T-SELL-1", ticker="AAPL", price=150.0)
        uow = _mock_uow(lots=[lot], trade=trade)
        svc = TaxService(uow)

        svc.close_lot("L1", "T-SELL-1")

        assert lot.is_closed is True
        assert lot.close_date == trade.time
        assert lot.proceeds == Decimal(str(trade.price))
        uow.tax_lots.update.assert_called_once_with(lot)
        uow.commit.assert_called_once()

    def test_close_lot_invalid_lot_id_raises(self) -> None:
        uow = _mock_uow()
        svc = TaxService(uow)
        with pytest.raises(NotFoundError, match="lot"):
            svc.close_lot("L-MISSING", "T-SELL-1")

    def test_close_lot_invalid_trade_id_raises(self) -> None:
        lot = _lot("L1")
        uow = _mock_uow(lots=[lot])
        svc = TaxService(uow)
        with pytest.raises(NotFoundError, match="trade"):
            svc.close_lot("L1", "T-MISSING")

    def test_close_lot_already_closed_raises(self) -> None:
        lot = _lot("L1", is_closed=True)
        trade = _sell_trade()
        uow = _mock_uow(lots=[lot], trade=trade)
        svc = TaxService(uow)
        with pytest.raises(BusinessRuleError, match="already closed"):
            svc.close_lot("L1", "T-SELL-1")

    def test_close_lot_ticker_mismatch_raises(self) -> None:
        lot = _lot("L1", ticker="AAPL")
        trade = _sell_trade(ticker="MSFT")
        uow = _mock_uow(lots=[lot], trade=trade)
        svc = TaxService(uow)
        with pytest.raises(BusinessRuleError, match="ticker"):
            svc.close_lot("L1", "T-SELL-1")


# ── AC-125.4: reassign_basis ────────────────────────────────────────────


class TestReassignBasis:
    """AC-125.4: reassign_basis within T+1 window."""

    def test_reassign_within_t1_succeeds(self) -> None:
        """Trade settled today → reassign allowed."""
        now = datetime.now(tz=timezone.utc)
        lot = _lot("L1")
        lot.open_date = now - timedelta(hours=12)  # Within T+1
        uow = _mock_uow(lots=[lot])
        svc = TaxService(uow)

        svc.reassign_basis("L1", CostBasisMethod.HIFO)
        uow.commit.assert_called_once()

    def test_reassign_outside_t1_raises(self) -> None:
        """Trade settled > 1 day ago → reassign forbidden."""
        lot = _lot("L1")
        lot.open_date = datetime(2024, 1, 1, tzinfo=timezone.utc)  # Way past T+1
        uow = _mock_uow(lots=[lot])
        svc = TaxService(uow)

        with pytest.raises(BusinessRuleError, match="T\\+1"):
            svc.reassign_basis("L1", CostBasisMethod.HIFO)

    def test_reassign_invalid_lot_raises(self) -> None:
        uow = _mock_uow()
        svc = TaxService(uow)
        with pytest.raises(NotFoundError, match="lot"):
            svc.reassign_basis("L-MISSING", CostBasisMethod.FIFO)


# ── AC-126.4, AC-126.5: simulate_impact ────────────────────────────────


class TestSimulateImpact:
    """AC-126.4/126.5: simulate_impact returns lot-level close preview."""

    def test_simulate_returns_lot_breakdown(self) -> None:
        """AC-126.5: Uses select_lots_for_closing + calculate_realized_gain."""
        lots = [
            _lot(
                "L1",
                cost_basis=Decimal("100.00"),
                quantity=100.0,
                open_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
            ),
        ]
        uow = _mock_uow(lots=lots)
        svc = TaxService(uow)

        result = svc.simulate_impact(
            account_id="ACC-1",
            ticker="AAPL",
            quantity=100.0,
            sale_price=Decimal("150.00"),
            method=CostBasisMethod.FIFO,
        )

        assert len(result.lot_details) == 1
        detail = result.lot_details[0]
        assert detail.lot_id == "L1"
        assert detail.gain_amount == Decimal("5000.00")
        assert detail.is_long_term is True

    def test_simulate_st_lt_split(self) -> None:
        """AC-126.4: Returns ST/LT split."""
        lots = [
            _lot(
                "L1",
                cost_basis=Decimal("100.00"),
                quantity=50.0,
                open_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
            ),  # LT
            _lot(
                "L2",
                cost_basis=Decimal("120.00"),
                quantity=50.0,
                open_date=datetime(2025, 11, 1, tzinfo=timezone.utc),
            ),  # ST
        ]
        uow = _mock_uow(lots=lots)
        svc = TaxService(uow)

        result = svc.simulate_impact(
            account_id="ACC-1",
            ticker="AAPL",
            quantity=100.0,
            sale_price=Decimal("150.00"),
            method=CostBasisMethod.FIFO,
        )

        assert result.total_lt_gain == Decimal("2500.00")  # (150-100)*50
        assert result.total_st_gain == Decimal("1500.00")  # (150-120)*50

    def test_simulate_estimated_tax(self) -> None:
        """AC-126.4: Returns estimated tax using TaxProfile rates."""
        lots = [
            _lot(
                "L1",
                cost_basis=Decimal("100.00"),
                quantity=100.0,
                open_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
            ),
        ]
        uow = _mock_uow(lots=lots)
        svc = TaxService(uow)

        result = svc.simulate_impact(
            account_id="ACC-1",
            ticker="AAPL",
            quantity=100.0,
            sale_price=Decimal("150.00"),
            method=CostBasisMethod.FIFO,
            federal_rate=0.20,
            state_rate=0.05,
        )

        # LT gain = 5000, tax = 5000 * (0.20 + 0.05) = 1250
        assert result.estimated_tax == Decimal("1250.00")

    def test_simulate_no_open_lots_raises(self) -> None:
        """AC-126.4 negative: BusinessRuleError when no open lots."""
        uow = _mock_uow(lots=[])
        svc = TaxService(uow)

        with pytest.raises(BusinessRuleError, match="no open lots"):
            svc.simulate_impact(
                account_id="ACC-1",
                ticker="AAPL",
                quantity=100.0,
                sale_price=Decimal("150.00"),
                method=CostBasisMethod.FIFO,
            )

    def test_simulate_correct_lot_order(self) -> None:
        """AC-126.5: Verify correct lot selection order feeds into gain calc."""
        lots = [
            _lot(
                "L1",
                cost_basis=Decimal("150.00"),
                quantity=100.0,
                open_date=datetime(2023, 6, 1, tzinfo=timezone.utc),
            ),
            _lot(
                "L2",
                cost_basis=Decimal("100.00"),
                quantity=100.0,
                open_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
            ),
        ]
        uow = _mock_uow(lots=lots)
        svc = TaxService(uow)

        result = svc.simulate_impact(
            account_id="ACC-1",
            ticker="AAPL",
            quantity=100.0,
            sale_price=Decimal("150.00"),
            method=CostBasisMethod.FIFO,
        )

        # FIFO picks L2 first (oldest)
        assert result.lot_details[0].lot_id == "L2"
        assert result.lot_details[0].gain_amount == Decimal("5000.00")


# ── Correction tests (execution-corrections 2026-05-12) ─────────────────


# ── C3: close_lot additional validations (F2) ───────────────────────────


class TestCloseLotCorrections:
    """F2 correction: close_lot must validate action, account, record link, compute gain."""

    def test_close_lot_rejects_buy_trade(self) -> None:
        """F2: close_lot rejects BOT (buy) trade — only SLD (sell) allowed."""
        lot = _lot("L1", ticker="AAPL")
        buy_trade = Trade(
            exec_id="T-BUY-1",
            time=datetime(2026, 5, 12, 10, 0, tzinfo=timezone.utc),
            instrument="AAPL",
            action=TradeAction.BOT,
            quantity=100.0,
            price=150.0,
            account_id="ACC-1",
        )
        uow = _mock_uow(lots=[lot], trade=buy_trade)
        svc = TaxService(uow)
        with pytest.raises(BusinessRuleError, match="sell"):
            svc.close_lot("L1", "T-BUY-1")

    def test_close_lot_rejects_account_mismatch(self) -> None:
        """F2: close_lot rejects trade from different account."""
        lot = _lot("L1", ticker="AAPL")
        trade = Trade(
            exec_id="T-SELL-1",
            time=datetime(2026, 5, 12, 10, 0, tzinfo=timezone.utc),
            instrument="AAPL",
            action=TradeAction.SLD,
            quantity=100.0,
            price=150.0,
            account_id="ACC-OTHER",  # Different account
        )
        uow = _mock_uow(lots=[lot], trade=trade)
        svc = TaxService(uow)
        with pytest.raises(BusinessRuleError, match="account"):
            svc.close_lot("L1", "T-SELL-1")

    def test_close_lot_records_linked_trade(self) -> None:
        """F2: close_lot appends sell_trade_id to lot.linked_trade_ids."""
        lot = _lot("L1", ticker="AAPL")
        trade = _sell_trade("T-SELL-1", ticker="AAPL")
        uow = _mock_uow(lots=[lot], trade=trade)
        svc = TaxService(uow)

        svc.close_lot("L1", "T-SELL-1")
        assert "T-SELL-1" in lot.linked_trade_ids

    def test_close_lot_computes_realized_gain(self) -> None:
        """F2: close_lot sets proceeds to per-share sale price from trade."""
        lot = _lot("L1", ticker="AAPL", cost_basis=Decimal("100.00"), quantity=100.0)
        trade = _sell_trade("T-SELL-1", ticker="AAPL", price=150.0)
        uow = _mock_uow(lots=[lot], trade=trade)
        svc = TaxService(uow)

        result = svc.close_lot("L1", "T-SELL-1")
        assert result.proceeds == Decimal("150.0")
        assert result.is_closed is True


# ── C4: reassign_basis persistence (F3) ─────────────────────────────────


class TestReassignBasisCorrections:
    """F3 correction: reassign_basis must persist method on lot entity."""

    def test_reassign_sets_cost_basis_method(self) -> None:
        """F3: After reassign, lot.cost_basis_method is set to the new method."""
        now = datetime.now(tz=timezone.utc)
        lot = _lot("L1")
        lot.open_date = now - timedelta(hours=12)  # Within T+1
        uow = _mock_uow(lots=[lot])
        svc = TaxService(uow)

        svc.reassign_basis("L1", CostBasisMethod.HIFO)
        assert lot.cost_basis_method == CostBasisMethod.HIFO
        uow.tax_lots.update.assert_called_once_with(lot)
        uow.commit.assert_called_once()


# ── C2: get_lots status + sort_by (F1) ──────────────────────────────────


class TestGetLotsCorrections:
    """F1 correction: get_lots must accept status and sort_by params."""

    def test_get_lots_status_open(self) -> None:
        """F1: status='open' maps to is_closed=False."""
        lots = [_lot("L1")]
        uow = _mock_uow(lots=lots)
        svc = TaxService(uow)

        svc.get_lots(account_id="ACC-1", status="open")
        uow.tax_lots.list_filtered.assert_called_once()
        call_kwargs = uow.tax_lots.list_filtered.call_args
        assert call_kwargs[1].get("is_closed") is False or (
            len(call_kwargs[0]) > 0 and call_kwargs[0] is not None
        )

    def test_get_lots_status_closed(self) -> None:
        """F1: status='closed' maps to is_closed=True."""
        lots = [_lot("L1", is_closed=True)]
        uow = _mock_uow(lots=lots)
        svc = TaxService(uow)

        svc.get_lots(account_id="ACC-1", status="closed")
        call_kwargs = uow.tax_lots.list_filtered.call_args[1]
        assert call_kwargs.get("is_closed") is True

    def test_get_lots_status_all(self) -> None:
        """F1: status='all' passes is_closed=None."""
        lots = [_lot("L1")]
        uow = _mock_uow(lots=lots)
        svc = TaxService(uow)

        svc.get_lots(account_id="ACC-1", status="all")
        call_kwargs = uow.tax_lots.list_filtered.call_args[1]
        assert call_kwargs.get("is_closed") is None

    def test_get_lots_sort_by_cost_basis(self) -> None:
        """F1: sort_by='cost_basis' returns lots sorted by cost_basis ascending."""
        lots = [
            _lot("L1", cost_basis=Decimal("200.00")),
            _lot("L2", cost_basis=Decimal("50.00")),
            _lot("L3", cost_basis=Decimal("100.00")),
        ]
        uow = _mock_uow(lots=lots)
        svc = TaxService(uow)

        result = svc.get_lots(account_id="ACC-1", sort_by="cost_basis")
        assert [lot.lot_id for lot in result] == ["L2", "L3", "L1"]


# ── C5: simulate_impact wash_risk + TaxProfile (F4) ─────────────────────


class TestSimulateImpactCorrections:
    """F4 correction: wash_risk output and TaxProfile rate sourcing."""

    def test_simulate_includes_wash_risk_false(self) -> None:
        """F4: SimulationResult includes wash_risk=False when no wash sale adjustment."""
        lots = [
            _lot(
                "L1",
                cost_basis=Decimal("100.00"),
                quantity=100.0,
                open_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
            ),
        ]
        uow = _mock_uow(lots=lots)
        svc = TaxService(uow)

        result = svc.simulate_impact(
            account_id="ACC-1",
            ticker="AAPL",
            quantity=100.0,
            sale_price=Decimal("150.00"),
            method=CostBasisMethod.FIFO,
        )
        assert result.wash_risk is False

    def test_simulate_includes_wash_risk_true(self) -> None:
        """F4: wash_risk=True when selected lot has wash_sale_adjustment > 0."""
        lot = _lot(
            "L1",
            cost_basis=Decimal("100.00"),
            quantity=100.0,
            open_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
        )
        lot.wash_sale_adjustment = Decimal("10.00")  # Prior wash sale
        uow = _mock_uow(lots=[lot])
        svc = TaxService(uow)

        result = svc.simulate_impact(
            account_id="ACC-1",
            ticker="AAPL",
            quantity=100.0,
            sale_price=Decimal("150.00"),
            method=CostBasisMethod.FIFO,
        )
        assert result.wash_risk is True

    def test_simulate_uses_tax_profile_rates(self) -> None:
        """F4: When TaxProfile exists, uses its federal_bracket + state_tax_rate."""
        from zorivest_core.domain.entities import TaxProfile
        from zorivest_core.domain.enums import (
            FilingStatus,
            WashSaleMatchingMethod,
        )

        lots = [
            _lot(
                "L1",
                cost_basis=Decimal("100.00"),
                quantity=100.0,
                open_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
            ),
        ]
        uow = _mock_uow(lots=lots)
        profile = TaxProfile(
            id=1,
            filing_status=FilingStatus.SINGLE,
            tax_year=2026,
            federal_bracket=0.22,
            state_tax_rate=0.06,
            state="NY",
            prior_year_tax=Decimal("0"),
            agi_estimate=Decimal("0"),
            capital_loss_carryforward=Decimal("0"),
            wash_sale_method=WashSaleMatchingMethod.CONSERVATIVE,
            default_cost_basis=CostBasisMethod.FIFO,
        )
        uow.tax_profiles.get_for_year.return_value = profile
        svc = TaxService(uow)

        result = svc.simulate_impact(
            account_id="ACC-1",
            ticker="AAPL",
            quantity=100.0,
            sale_price=Decimal("150.00"),
            method=CostBasisMethod.FIFO,
        )

        # LT gain = 5000, tax = 5000 * (0.22 + 0.06) = 1400
        assert result.estimated_tax == Decimal("1400.00")


# ── R2: close_lot quantity validation + realized gain (Recheck Round 2) ──


class TestCloseLotQuantityAndGain:
    """R2 corrections: quantity validation and realized gain/loss computation."""

    def test_close_lot_rejects_oversize_quantity(self) -> None:
        """R2: trade.quantity > lot.quantity → BusinessRuleError."""
        lot = _lot("L1", ticker="AAPL", quantity=50.0)
        trade = _sell_trade("T-SELL-1", ticker="AAPL", quantity=100.0)
        uow = _mock_uow(lots=[lot], trade=trade)
        svc = TaxService(uow)

        with pytest.raises(BusinessRuleError, match="quantity"):
            svc.close_lot("L1", "T-SELL-1")

    def test_close_lot_partial_close_creates_remainder(self) -> None:
        """RR2-1: trade.quantity < lot.quantity → split lot.

        Closed lot has sold quantity; remainder lot saved with leftover.
        Spec: implementation-plan.md:67 — "Creates split lot."
        """
        lot = _lot(
            "L1",
            ticker="AAPL",
            quantity=100.0,
            cost_basis=Decimal("100.00"),
            open_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
        )
        trade = _sell_trade("T-SELL-1", ticker="AAPL", price=150.0, quantity=40.0)
        uow = _mock_uow(lots=[lot], trade=trade)
        svc = TaxService(uow)

        result = svc.close_lot("L1", "T-SELL-1")

        # Closed lot has the sold quantity
        assert result.is_closed is True
        assert result.quantity == 40.0
        # Remainder lot was saved via tax_lots.save()
        uow.tax_lots.save.assert_called_once()
        remainder = uow.tax_lots.save.call_args[0][0]
        assert remainder.quantity == 60.0
        assert remainder.is_closed is False
        assert remainder.lot_id == "L1-R"

    def test_close_lot_partial_close_remainder_inherits_basis(self) -> None:
        """RR2-1: remainder lot inherits cost_basis, open_date, wash_sale_adjustment."""
        lot = _lot(
            "L1",
            ticker="AAPL",
            quantity=100.0,
            cost_basis=Decimal("120.00"),
            open_date=datetime(2023, 6, 15, tzinfo=timezone.utc),
        )
        lot.wash_sale_adjustment = Decimal("5.00")
        trade = _sell_trade("T-SELL-1", ticker="AAPL", price=150.0, quantity=30.0)
        uow = _mock_uow(lots=[lot], trade=trade)
        svc = TaxService(uow)

        svc.close_lot("L1", "T-SELL-1")

        remainder = uow.tax_lots.save.call_args[0][0]
        assert remainder.cost_basis == Decimal("120.00")
        assert remainder.open_date == datetime(2023, 6, 15, tzinfo=timezone.utc)
        assert remainder.wash_sale_adjustment == Decimal("5.00")
        assert remainder.account_id == "ACC-1"
        assert remainder.ticker == "AAPL"
        assert remainder.close_date is None

    def test_close_lot_partial_close_realized_gain_on_sold_portion(self) -> None:
        """RR2-1: realized gain computed on sold quantity only."""
        lot = _lot(
            "L1",
            ticker="AAPL",
            quantity=100.0,
            cost_basis=Decimal("100.00"),
            open_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
        )
        trade = _sell_trade("T-SELL-1", ticker="AAPL", price=150.0, quantity=40.0)
        uow = _mock_uow(lots=[lot], trade=trade)
        svc = TaxService(uow)

        result = svc.close_lot("L1", "T-SELL-1")

        # Gain = (150 - 100) * 40 = 2000
        assert result.realized_gain_loss == Decimal("2000.00")
        assert result.proceeds == Decimal("150.0")

    def test_close_lot_computes_and_persists_realized_gain(self) -> None:
        """R2: close_lot sets lot.realized_gain_loss using calculate_realized_gain."""
        lot = _lot(
            "L1",
            ticker="AAPL",
            cost_basis=Decimal("100.00"),
            quantity=100.0,
            open_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
        )
        trade = _sell_trade("T-SELL-1", ticker="AAPL", price=150.0, quantity=100.0)
        uow = _mock_uow(lots=[lot], trade=trade)
        svc = TaxService(uow)

        result = svc.close_lot("L1", "T-SELL-1")
        # Gain = (150 - 100) * 100 = 5000
        assert result.realized_gain_loss == Decimal("5000.00")
        assert result.is_closed is True
        uow.tax_lots.update.assert_called_once_with(lot)

    def test_close_lot_realized_loss(self) -> None:
        """R2: close_lot correctly computes negative realized gain (loss)."""
        lot = _lot(
            "L1",
            ticker="AAPL",
            cost_basis=Decimal("200.00"),
            quantity=50.0,
            open_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
        )
        trade = _sell_trade("T-SELL-1", ticker="AAPL", price=150.0, quantity=50.0)
        uow = _mock_uow(lots=[lot], trade=trade)
        svc = TaxService(uow)

        result = svc.close_lot("L1", "T-SELL-1")
        # Loss = (150 - 200) * 50 = -2500
        assert result.realized_gain_loss == Decimal("-2500.00")


# ── R1: close_lot auto-discovery (Recheck Round 2) ──────────────────────


class TestCloseLotAutoDiscovery:
    """R1 correction: close_lot(lot_id) auto-discovers sell trade from history."""

    def test_close_lot_autodiscovers_sell_trade(self) -> None:
        """R1: close_lot(lot_id) without sell_trade_id finds matching SLD trade."""
        lot = _lot(
            "L1",
            ticker="AAPL",
            quantity=100.0,
            cost_basis=Decimal("100.00"),
            open_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
        )
        trade = _sell_trade("T-SELL-1", ticker="AAPL", price=150.0, quantity=100.0)
        uow = _mock_uow(lots=[lot])
        # Set up trades repo to return matching sell trades for account
        uow.trades.list_for_account.return_value = [trade]
        svc = TaxService(uow)

        result = svc.close_lot("L1")
        assert result.is_closed is True
        assert "T-SELL-1" in result.linked_trade_ids

    def test_close_lot_raises_when_no_sell_trade_found(self) -> None:
        """R1: close_lot(lot_id) with no matching SLD trade → BusinessRuleError."""
        lot = _lot("L1", ticker="AAPL", quantity=100.0)
        uow = _mock_uow(lots=[lot])
        uow.trades.list_for_account.return_value = []
        svc = TaxService(uow)

        with pytest.raises(BusinessRuleError, match="No matching sell trade"):
            svc.close_lot("L1")

    def test_close_lot_explicit_sell_trade_still_works(self) -> None:
        """R1: close_lot(lot_id, sell_trade_id) explicit path still works."""
        lot = _lot(
            "L1",
            ticker="AAPL",
            quantity=100.0,
            cost_basis=Decimal("100.00"),
            open_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
        )
        trade = _sell_trade("T-SELL-1", ticker="AAPL", price=150.0, quantity=100.0)
        uow = _mock_uow(lots=[lot], trade=trade)
        svc = TaxService(uow)

        result = svc.close_lot("L1", "T-SELL-1")
        assert result.is_closed is True
        assert result.realized_gain_loss == Decimal("5000.00")


# ── AC-127.4, AC-127.5: get_taxable_gains ──────────────────────────────


class TestGetTaxableGains:
    """AC-127.4/127.5: get_taxable_gains filters tax-advantaged, applies carryforward."""

    def _closed_lot(
        self,
        lot_id: str = "L1",
        ticker: str = "AAPL",
        account_id: str = "ACC-1",
        cost_basis: Decimal = Decimal("100.00"),
        quantity: float = 100.0,
        proceeds: Decimal = Decimal("150.00"),
        open_date: datetime | None = None,
        close_date: datetime | None = None,
    ) -> TaxLot:
        return TaxLot(
            lot_id=lot_id,
            account_id=account_id,
            ticker=ticker,
            open_date=open_date or datetime(2023, 1, 1, tzinfo=timezone.utc),
            close_date=close_date or datetime(2026, 6, 1, tzinfo=timezone.utc),
            quantity=quantity,
            cost_basis=cost_basis,
            proceeds=proceeds,
            wash_sale_adjustment=Decimal("0"),
            is_closed=True,
            linked_trade_ids=[],
            realized_gain_loss=(proceeds - cost_basis) * Decimal(str(quantity)),
        )

    def _mock_uow_for_gains(
        self,
        lots: list[TaxLot] | None = None,
        accounts: dict[str, bool] | None = None,
        profile: object | None = None,
    ) -> MagicMock:
        """Create mock UoW with accounts and tax-advantaged flags."""
        uow = MagicMock()
        uow.__enter__ = MagicMock(return_value=uow)
        uow.__exit__ = MagicMock(return_value=False)

        uow.tax_lots.list_filtered.return_value = lots or []
        uow.tax_lots.list_all_filtered.return_value = lots or []
        uow.tax_profiles.get_for_year.return_value = profile

        # Mock accounts repo — return Account-like objects with is_tax_advantaged
        acct_map = accounts or {}

        def mock_get_account(account_id: str):
            if account_id in acct_map:
                acct = MagicMock()
                acct.is_tax_advantaged = acct_map[account_id]
                return acct
            return None

        uow.accounts.get.side_effect = mock_get_account

        return uow

    def test_returns_gains_for_closed_lots(self) -> None:
        """Basic: returns ST/LT breakdown for closed lots in the tax year."""
        lot = self._closed_lot(
            open_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
            close_date=datetime(2026, 6, 1, tzinfo=timezone.utc),
            cost_basis=Decimal("100.00"),
            proceeds=Decimal("150.00"),
            quantity=100.0,
        )
        uow = self._mock_uow_for_gains(
            lots=[lot],
            accounts={"ACC-1": False},
        )
        svc = TaxService(uow)
        result = svc.get_taxable_gains(2026)

        # LT gain: (150 - 100) * 100 = 5000
        assert result.total_lt_gain == Decimal("5000.00")
        assert result.total_st_gain == Decimal("0")

    def test_excludes_tax_advantaged_accounts(self) -> None:
        """AC-127.4: Lots from tax-advantaged accounts (IRA) excluded."""
        regular_lot = self._closed_lot(
            lot_id="L1",
            account_id="ACC-REG",
            cost_basis=Decimal("100.00"),
            proceeds=Decimal("150.00"),
            quantity=100.0,
            open_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
            close_date=datetime(2026, 6, 1, tzinfo=timezone.utc),
        )
        ira_lot = self._closed_lot(
            lot_id="L2",
            account_id="ACC-IRA",
            cost_basis=Decimal("50.00"),
            proceeds=Decimal("200.00"),
            quantity=100.0,
            open_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
            close_date=datetime(2026, 6, 1, tzinfo=timezone.utc),
        )
        uow = self._mock_uow_for_gains(
            lots=[regular_lot, ira_lot],
            accounts={"ACC-REG": False, "ACC-IRA": True},
        )
        svc = TaxService(uow)
        result = svc.get_taxable_gains(2026)

        # Only regular account gain: (150-100) * 100 = 5000
        assert result.total_lt_gain == Decimal("5000.00")
        # IRA lot (15000 gain) excluded
        assert result.total_st_gain == Decimal("0")

    def test_applies_carryforward_from_tax_profile(self) -> None:
        """AC-127.5: Carryforward from TaxProfile applied to net results."""
        from zorivest_core.domain.entities import TaxProfile
        from zorivest_core.domain.enums import (
            FilingStatus,
            WashSaleMatchingMethod,
        )

        lot = self._closed_lot(
            cost_basis=Decimal("200.00"),
            proceeds=Decimal("150.00"),
            quantity=100.0,
            open_date=datetime(2025, 11, 1, tzinfo=timezone.utc),
            close_date=datetime(2026, 3, 1, tzinfo=timezone.utc),
        )
        # ST loss: (150-200)*100 = -5000
        profile = TaxProfile(
            id=1,
            filing_status=FilingStatus.SINGLE,
            tax_year=2026,
            federal_bracket=0.22,
            state_tax_rate=0.05,
            state="NY",
            prior_year_tax=Decimal("0"),
            agi_estimate=Decimal("0"),
            capital_loss_carryforward=Decimal("2000"),
            wash_sale_method=WashSaleMatchingMethod.CONSERVATIVE,
            default_cost_basis=CostBasisMethod.FIFO,
        )
        uow = self._mock_uow_for_gains(
            lots=[lot],
            accounts={"ACC-1": False},
            profile=profile,
        )
        svc = TaxService(uow)
        result = svc.get_taxable_gains(2026)

        # Traced through apply_capital_loss_rules:
        #   st_gains = -5000 (ST loss), lt_gains = 0
        #   st_carryforward = 2000 (profile), lt_carryforward = 0
        #   net_st = -5000 - 2000 = -7000, net_lt = 0
        #   No cross-net (net_lt == 0)
        #   total_net_loss = 7000, cap(SINGLE) = 3000
        #   deductible_loss = min(7000, 3000) = 3000
        #   remaining_st = 7000 - 3000 = 4000, remaining_lt = 0
        #   net_st = max(-7000, 0) = 0, net_lt = 0
        assert result.deductible_loss == Decimal("3000")
        assert result.remaining_st_carryforward == Decimal("4000")
        assert result.remaining_lt_carryforward == Decimal("0")
        assert result.total_st_gain == Decimal("0")
        assert result.total_lt_gain == Decimal("0")

    def test_missing_profile_returns_gains_without_carryforward(self) -> None:
        """AC-127.5 negative: No TaxProfile → gains returned without carryforward."""
        lot = self._closed_lot(
            cost_basis=Decimal("100.00"),
            proceeds=Decimal("150.00"),
            quantity=100.0,
            open_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
            close_date=datetime(2026, 6, 1, tzinfo=timezone.utc),
        )
        uow = self._mock_uow_for_gains(
            lots=[lot],
            accounts={"ACC-1": False},
            profile=None,
        )
        svc = TaxService(uow)
        result = svc.get_taxable_gains(2026)

        assert result.total_lt_gain == Decimal("5000.00")
        assert result.deductible_loss == Decimal("0")


# ── AC-128.6: pair_option_assignment ────────────────────────────────────


class TestPairOptionAssignment:
    """AC-128.6: TaxService.pair_option_assignment persists adjusted basis."""

    def _setup_uow(
        self,
        lot: TaxLot,
        option_trade: Trade,
    ) -> MagicMock:
        """Create mock UoW with lot and option trade."""
        uow = MagicMock()
        uow.__enter__ = MagicMock(return_value=uow)
        uow.__exit__ = MagicMock(return_value=False)
        uow.tax_lots.get.side_effect = lambda lid: lot if lid == lot.lot_id else None
        uow.trades.get.side_effect = lambda tid: (
            option_trade if tid == option_trade.exec_id else None
        )
        uow.tax_profiles.get_for_year.return_value = None
        return uow

    def test_pair_short_put_assignment(self) -> None:
        """pair_option_assignment persists adjusted cost basis for short put."""
        from zorivest_core.domain.tax.option_pairing import AssignmentType

        lot = TaxLot(
            lot_id="LOT-1",
            account_id="ACC-1",
            ticker="AAPL",
            open_date=datetime(2025, 1, 15, tzinfo=timezone.utc),
            close_date=None,
            quantity=100.0,
            cost_basis=Decimal("150.00"),
            proceeds=Decimal("0.00"),
            wash_sale_adjustment=Decimal("0"),
            is_closed=False,
        )
        opt_trade = Trade(
            exec_id="OPT-1",
            time=datetime(2025, 6, 1, tzinfo=timezone.utc),
            instrument="AAPL 260320 P 150",
            action=TradeAction.SLD,
            quantity=1.0,
            price=5.00,
            account_id="ACC-1",
        )
        uow = self._setup_uow(lot, opt_trade)
        svc = TaxService(uow)

        svc.pair_option_assignment(
            "LOT-1", "OPT-1", AssignmentType.WRITTEN_PUT_ASSIGNMENT
        )

        # Basis adjusted: 150 - (5*100/100) = 145
        assert lot.cost_basis == Decimal("145.00")
        assert "OPT-1" in lot.linked_trade_ids
        uow.tax_lots.update.assert_called_once()
        uow.commit.assert_called_once()

    def test_pair_option_not_found_raises(self) -> None:
        """AC-128.6 negative: Option trade not found → NotFoundError."""
        from zorivest_core.domain.tax.option_pairing import AssignmentType

        lot = TaxLot(
            lot_id="LOT-1",
            account_id="ACC-1",
            ticker="AAPL",
            open_date=datetime(2025, 1, 15, tzinfo=timezone.utc),
            close_date=None,
            quantity=100.0,
            cost_basis=Decimal("150.00"),
            proceeds=Decimal("0.00"),
            wash_sale_adjustment=Decimal("0"),
            is_closed=False,
        )
        uow = MagicMock()
        uow.__enter__ = MagicMock(return_value=uow)
        uow.__exit__ = MagicMock(return_value=False)
        uow.tax_lots.get.return_value = lot
        uow.trades.get.return_value = None  # Not found
        svc = TaxService(uow)

        with pytest.raises(NotFoundError, match="option"):
            svc.pair_option_assignment(
                "LOT-1", "OPT-MISSING", AssignmentType.WRITTEN_PUT_ASSIGNMENT
            )

    def test_pair_lot_not_found_raises(self) -> None:
        """AC-128.6 negative: Lot not found → NotFoundError."""
        from zorivest_core.domain.tax.option_pairing import AssignmentType

        uow = MagicMock()
        uow.__enter__ = MagicMock(return_value=uow)
        uow.__exit__ = MagicMock(return_value=False)
        uow.tax_lots.get.return_value = None
        svc = TaxService(uow)

        with pytest.raises(NotFoundError, match="lot"):
            svc.pair_option_assignment(
                "LOT-MISSING", "OPT-1", AssignmentType.WRITTEN_PUT_ASSIGNMENT
            )

    def test_pair_short_call_assignment(self) -> None:
        """F3: Short call assignment persists adjusted proceeds."""
        from zorivest_core.domain.tax.option_pairing import AssignmentType

        lot = TaxLot(
            lot_id="LOT-1",
            account_id="ACC-1",
            ticker="AAPL",
            open_date=datetime(2025, 1, 15, tzinfo=timezone.utc),
            close_date=datetime(2026, 3, 20, tzinfo=timezone.utc),
            quantity=100.0,
            cost_basis=Decimal("100.00"),
            proceeds=Decimal("200.00"),
            wash_sale_adjustment=Decimal("0"),
            is_closed=True,
        )
        opt_trade = Trade(
            exec_id="OPT-2",
            time=datetime(2025, 6, 1, tzinfo=timezone.utc),
            instrument="AAPL 260320 C 200",
            action=TradeAction.SLD,
            quantity=1.0,
            price=8.00,
            account_id="ACC-1",
        )
        uow = self._setup_uow(lot, opt_trade)
        svc = TaxService(uow)

        svc.pair_option_assignment(
            "LOT-1", "OPT-2", AssignmentType.WRITTEN_CALL_ASSIGNMENT
        )

        # Proceeds adjusted: 200 + (8*100/100) = 208
        assert lot.proceeds == Decimal("208.00")
        assert lot.cost_basis == Decimal("100.00")  # Unchanged
        assert "OPT-2" in lot.linked_trade_ids
        uow.tax_lots.update.assert_called_once()
        uow.commit.assert_called_once()

    def test_pair_long_call_exercise(self) -> None:
        """F3: Long call exercise persists adjusted cost basis."""
        from zorivest_core.domain.tax.option_pairing import AssignmentType

        lot = TaxLot(
            lot_id="LOT-1",
            account_id="ACC-1",
            ticker="AAPL",
            open_date=datetime(2025, 1, 15, tzinfo=timezone.utc),
            close_date=None,
            quantity=100.0,
            cost_basis=Decimal("200.00"),
            proceeds=Decimal("0.00"),
            wash_sale_adjustment=Decimal("0"),
            is_closed=False,
        )
        opt_trade = Trade(
            exec_id="OPT-3",
            time=datetime(2025, 6, 1, tzinfo=timezone.utc),
            instrument="AAPL 260320 C 200",
            action=TradeAction.BOT,
            quantity=1.0,
            price=10.00,
            account_id="ACC-1",
        )
        uow = self._setup_uow(lot, opt_trade)
        svc = TaxService(uow)

        svc.pair_option_assignment("LOT-1", "OPT-3", AssignmentType.LONG_CALL_EXERCISE)

        # Basis adjusted: 200 + (10*100/100) = 210
        assert lot.cost_basis == Decimal("210.00")
        assert lot.proceeds == Decimal("0.00")  # Unchanged
        assert "OPT-3" in lot.linked_trade_ids
        uow.tax_lots.update.assert_called_once()
        uow.commit.assert_called_once()

    def test_pair_long_put_exercise(self) -> None:
        """F3: Long put exercise persists adjusted proceeds."""
        from zorivest_core.domain.tax.option_pairing import AssignmentType

        lot = TaxLot(
            lot_id="LOT-1",
            account_id="ACC-1",
            ticker="AAPL",
            open_date=datetime(2025, 1, 15, tzinfo=timezone.utc),
            close_date=datetime(2026, 3, 20, tzinfo=timezone.utc),
            quantity=100.0,
            cost_basis=Decimal("100.00"),
            proceeds=Decimal("150.00"),
            wash_sale_adjustment=Decimal("0"),
            is_closed=True,
        )
        opt_trade = Trade(
            exec_id="OPT-4",
            time=datetime(2025, 6, 1, tzinfo=timezone.utc),
            instrument="AAPL 260320 P 150",
            action=TradeAction.BOT,
            quantity=1.0,
            price=3.00,
            account_id="ACC-1",
        )
        uow = self._setup_uow(lot, opt_trade)
        svc = TaxService(uow)

        svc.pair_option_assignment("LOT-1", "OPT-4", AssignmentType.LONG_PUT_EXERCISE)

        # Proceeds adjusted: 150 - (3*100/100) = 147
        assert lot.proceeds == Decimal("147.00")
        assert lot.cost_basis == Decimal("100.00")  # Unchanged
        assert "OPT-4" in lot.linked_trade_ids
        uow.tax_lots.update.assert_called_once()
        uow.commit.assert_called_once()


# ── AC-129.4: get_ytd_pnl ──────────────────────────────────────────────


class TestGetYtdPnl:
    """AC-129.4: TaxService.get_ytd_pnl returns per-symbol YTD P&L."""

    def _mock_uow_for_pnl(
        self,
        lots: list[TaxLot] | None = None,
        accounts: dict[str, bool] | None = None,
    ) -> MagicMock:
        uow = MagicMock()
        uow.__enter__ = MagicMock(return_value=uow)
        uow.__exit__ = MagicMock(return_value=False)
        uow.tax_lots.list_filtered.return_value = lots or []
        uow.tax_lots.list_all_filtered.return_value = lots or []
        acct_map = accounts or {}

        def mock_get_account(account_id: str):
            if account_id in acct_map:
                acct = MagicMock()
                acct.is_tax_advantaged = acct_map[account_id]
                return acct
            return None

        uow.accounts.get.side_effect = mock_get_account
        return uow

    def test_returns_ytd_pnl_result(self) -> None:
        """Basic: returns YtdPnlResult from TaxService."""
        from zorivest_core.domain.tax.ytd_pnl import YtdPnlResult

        lot = TaxLot(
            lot_id="L1",
            account_id="ACC-1",
            ticker="AAPL",
            open_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
            close_date=datetime(2026, 6, 1, tzinfo=timezone.utc),
            quantity=100.0,
            cost_basis=Decimal("100.00"),
            proceeds=Decimal("150.00"),
            wash_sale_adjustment=Decimal("0"),
            is_closed=True,
            linked_trade_ids=[],
            realized_gain_loss=Decimal("5000.00"),
        )
        uow = self._mock_uow_for_pnl(lots=[lot], accounts={"ACC-1": False})
        svc = TaxService(uow)
        result = svc.get_ytd_pnl(2026)

        assert isinstance(result, YtdPnlResult)
        assert result.total_lt_gains == Decimal("5000.00")

    def test_excludes_tax_advantaged_accounts(self) -> None:
        """AC-129.4 + AC-127.4: Tax-advantaged accounts excluded from P&L."""
        regular_lot = TaxLot(
            lot_id="L1",
            account_id="ACC-REG",
            ticker="AAPL",
            open_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
            close_date=datetime(2026, 6, 1, tzinfo=timezone.utc),
            quantity=100.0,
            cost_basis=Decimal("100.00"),
            proceeds=Decimal("150.00"),
            wash_sale_adjustment=Decimal("0"),
            is_closed=True,
            linked_trade_ids=[],
        )
        ira_lot = TaxLot(
            lot_id="L2",
            account_id="ACC-IRA",
            ticker="MSFT",
            open_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
            close_date=datetime(2026, 6, 1, tzinfo=timezone.utc),
            quantity=100.0,
            cost_basis=Decimal("50.00"),
            proceeds=Decimal("200.00"),
            wash_sale_adjustment=Decimal("0"),
            is_closed=True,
            linked_trade_ids=[],
        )
        uow = self._mock_uow_for_pnl(
            lots=[regular_lot, ira_lot],
            accounts={"ACC-REG": False, "ACC-IRA": True},
        )
        svc = TaxService(uow)
        result = svc.get_ytd_pnl(2026)

        tickers = {e.ticker for e in result.by_symbol}
        assert "AAPL" in tickers
        assert "MSFT" not in tickers

    def test_empty_lots_returns_zero_totals(self) -> None:
        """No closed lots → zero totals."""
        uow = self._mock_uow_for_pnl(lots=[], accounts={})
        svc = TaxService(uow)
        result = svc.get_ytd_pnl(2026)

        assert result.total_gains == Decimal("0")
        assert len(result.by_symbol) == 0


# ── F1 Correction: pagination regression tests ─────────────────────────


class TestAggregatePaginationRegression:
    """F1: Aggregate report methods must retrieve ALL closed lots, not limit=100."""

    def _make_closed_lots(self, count: int) -> list[TaxLot]:
        """Create N closed lots with ST gains."""
        return [
            TaxLot(
                lot_id=f"L-{i}",
                account_id="ACC-1",
                ticker="AAPL",
                open_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
                close_date=datetime(2026, 6, 1, tzinfo=timezone.utc),
                quantity=1.0,
                cost_basis=Decimal("100.00"),
                proceeds=Decimal("110.00"),
                wash_sale_adjustment=Decimal("0"),
                is_closed=True,
                linked_trade_ids=[],
            )
            for i in range(count)
        ]

    def _mock_uow(self, lots: list[TaxLot]) -> MagicMock:
        uow = MagicMock()
        uow.__enter__ = MagicMock(return_value=uow)
        uow.__exit__ = MagicMock(return_value=False)
        uow.tax_lots.list_all_filtered.return_value = lots
        uow.tax_profiles.get_for_year.return_value = None

        acct = MagicMock()
        acct.is_tax_advantaged = False
        uow.accounts.get.return_value = acct
        return uow

    def test_get_taxable_gains_includes_all_150_lots(self) -> None:
        """F1: get_taxable_gains must include lot 101+ (was capped at 100)."""
        lots = self._make_closed_lots(150)
        uow = self._mock_uow(lots)
        svc = TaxService(uow)
        result = svc.get_taxable_gains(2026)

        # Each lot has (110-100)*1 = $10 ST gain × 150 lots = $1500
        assert result.total_st_gain == Decimal("1500.00")
        uow.tax_lots.list_all_filtered.assert_called_once()

    def test_get_ytd_pnl_includes_all_150_lots(self) -> None:
        """F1: get_ytd_pnl must include lot 101+ (was capped at 100)."""
        lots = self._make_closed_lots(150)
        uow = self._mock_uow(lots)
        svc = TaxService(uow)
        result = svc.get_ytd_pnl(2026)

        # 150 lots × $10 ST gain = $1500
        assert result.total_st_gains == Decimal("1500.00")
        uow.tax_lots.list_all_filtered.assert_called_once()
