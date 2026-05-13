# tests/unit/test_option_pairing.py
"""FIC tests for MEU-128: Options Assignment/Exercise Cost Basis Pairing.

Feature Intent Contract:
  parse_option_symbol(instrument) → OptionDetails | None
  adjust_basis_for_assignment(stock_lot, option_trade, assignment_type)
    → AdjustedBasisResult

Acceptance Criteria:
  AC-128.1: parse_option_symbol parses normalized format
  AC-128.2–128.5: adjust_basis_for_assignment (4 IRS paths)
  AC-128.7: OptionDetails frozen dataclass
  AC-128.9: assignment_type consistency with option_trade.action

Source: IRS Pub 550 §Puts and Calls, domain-model-reference.md A4
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from zorivest_core.domain.entities import TaxLot, Trade
from zorivest_core.domain.enums import TradeAction
from zorivest_core.domain.exceptions import BusinessRuleError
from zorivest_core.domain.tax.option_pairing import (
    AssignmentType,
    OptionDetails,
    adjust_basis_for_assignment,
    parse_option_symbol,
)


# ── Helpers ──────────────────────────────────────────────────────────────


def _stock_lot(
    lot_id: str = "LOT-1",
    ticker: str = "AAPL",
    cost_basis: Decimal = Decimal("150.00"),
    quantity: float = 100.0,
    proceeds: Decimal = Decimal("0.00"),
) -> TaxLot:
    return TaxLot(
        lot_id=lot_id,
        account_id="ACC-1",
        ticker=ticker,
        open_date=datetime(2025, 1, 15, tzinfo=timezone.utc),
        close_date=None,
        quantity=quantity,
        cost_basis=cost_basis,
        proceeds=proceeds,
        wash_sale_adjustment=Decimal("0"),
        is_closed=False,
        linked_trade_ids=[],
    )


def _option_trade(
    exec_id: str = "OPT-1",
    instrument: str = "AAPL 260320 C 200",
    action: TradeAction = TradeAction.SLD,
    price: float = 5.00,
    quantity: float = 1.0,
) -> Trade:
    return Trade(
        exec_id=exec_id,
        time=datetime(2025, 6, 1, tzinfo=timezone.utc),
        instrument=instrument,
        action=action,
        quantity=quantity,
        price=price,
        account_id="ACC-1",
    )


# ── AC-128.1: parse_option_symbol ───────────────────────────────────────


class TestParseOptionSymbol:
    """AC-128.1: parse_option_symbol parses normalized option format."""

    def test_parses_call_option(self) -> None:
        """Standard call: 'AAPL 260320 C 200' → OptionDetails."""
        result = parse_option_symbol("AAPL 260320 C 200")
        assert result is not None
        assert result.underlying == "AAPL"
        assert result.expiry == date(2026, 3, 20)
        assert result.put_call == "C"
        assert result.strike == Decimal("200")

    def test_parses_put_option(self) -> None:
        """Standard put: 'MSFT 250815 P 350.50' → OptionDetails."""
        result = parse_option_symbol("MSFT 250815 P 350.50")
        assert result is not None
        assert result.underlying == "MSFT"
        assert result.expiry == date(2025, 8, 15)
        assert result.put_call == "P"
        assert result.strike == Decimal("350.50")

    def test_non_option_returns_none(self) -> None:
        """Non-option instrument returns None (stock symbol passthrough)."""
        result = parse_option_symbol("AAPL")
        assert result is None

    def test_malformed_date_returns_none(self) -> None:
        """Malformed date component returns None."""
        result = parse_option_symbol("AAPL 999999 C 200")
        assert result is None

    def test_raw_occ_21char_returns_none(self) -> None:
        """AC-128.1 negative: Raw 21-char OCC string returns None
        (handled by infrastructure adapters)."""
        result = parse_option_symbol("AAPL  260320C00200000")
        assert result is None

    def test_empty_string_returns_none(self) -> None:
        result = parse_option_symbol("")
        assert result is None

    def test_missing_strike_returns_none(self) -> None:
        result = parse_option_symbol("AAPL 260320 C")
        assert result is None

    def test_invalid_put_call_returns_none(self) -> None:
        result = parse_option_symbol("AAPL 260320 X 200")
        assert result is None


# ── AC-128.7: OptionDetails frozen dataclass ────────────────────────────


class TestOptionDetailsFrozen:
    """AC-128.7: OptionDetails is frozen with correct fields."""

    def test_frozen_dataclass(self) -> None:
        """OptionDetails fields are immutable."""
        details = OptionDetails(
            underlying="AAPL",
            expiry=date(2026, 3, 20),
            put_call="C",
            strike=Decimal("200"),
        )
        with pytest.raises(AttributeError):
            details.underlying = "MSFT"  # type: ignore[misc]


# ── AC-128.2: Short put assignment ──────────────────────────────────────


class TestShortPutAssignment:
    """AC-128.2: Short put assignment reduces stock cost basis by premium."""

    def test_reduces_cost_basis_by_premium(self) -> None:
        """Writer (SLD) put assigned → stock cost basis reduced by premium received."""
        lot = _stock_lot(cost_basis=Decimal("150.00"), quantity=100.0)
        opt = _option_trade(
            instrument="AAPL 260320 P 150",
            action=TradeAction.SLD,
            price=5.00,
            quantity=1.0,  # 1 contract = 100 shares
        )
        result = adjust_basis_for_assignment(
            lot, opt, AssignmentType.WRITTEN_PUT_ASSIGNMENT
        )
        # Premium received: $5.00 * 100 = $500
        # New basis = 150.00 - (500 / 100 shares) = 145.00
        assert result.adjusted_cost_basis == Decimal("145.00")

    def test_wrong_action_raises(self) -> None:
        """AC-128.9: BOT trade + WRITTEN_PUT_ASSIGNMENT → BusinessRuleError."""
        lot = _stock_lot()
        opt = _option_trade(action=TradeAction.BOT)  # Wrong — should be SLD
        with pytest.raises(BusinessRuleError, match="action"):
            adjust_basis_for_assignment(lot, opt, AssignmentType.WRITTEN_PUT_ASSIGNMENT)


# ── AC-128.3: Short call assignment ────────────────────────────────────


class TestShortCallAssignment:
    """AC-128.3: Short call assignment increases amount realized by premium."""

    def test_increases_proceeds_by_premium(self) -> None:
        """Writer (SLD) call assigned → amount realized increased by premium."""
        lot = _stock_lot(
            cost_basis=Decimal("100.00"),
            quantity=100.0,
            proceeds=Decimal("200.00"),
        )
        lot.is_closed = True
        lot.close_date = datetime(2026, 3, 20, tzinfo=timezone.utc)
        opt = _option_trade(
            instrument="AAPL 260320 C 200",
            action=TradeAction.SLD,
            price=8.00,
            quantity=1.0,
        )
        result = adjust_basis_for_assignment(
            lot, opt, AssignmentType.WRITTEN_CALL_ASSIGNMENT
        )
        # Premium received: $8.00 * 100 = $800
        # Adjusted proceeds = 200 + (800 / 100) = 208.00
        assert result.adjusted_proceeds == Decimal("208.00")

    def test_ticker_mismatch_raises(self) -> None:
        """AC-128.3 negative: Ticker mismatch between option underlying and lot."""
        lot = _stock_lot(ticker="AAPL")
        opt = _option_trade(instrument="MSFT 260320 C 200", action=TradeAction.SLD)
        with pytest.raises(BusinessRuleError, match="ticker"):
            adjust_basis_for_assignment(
                lot, opt, AssignmentType.WRITTEN_CALL_ASSIGNMENT
            )


# ── AC-128.4: Long call exercise ────────────────────────────────────────


class TestLongCallExercise:
    """AC-128.4: Long call exercise adds premium paid to stock cost basis."""

    def test_adds_premium_to_cost_basis(self) -> None:
        """Holder (BOT) call exercised → premium added to stock cost basis."""
        lot = _stock_lot(cost_basis=Decimal("200.00"), quantity=100.0)
        opt = _option_trade(
            instrument="AAPL 260320 C 200",
            action=TradeAction.BOT,
            price=10.00,
            quantity=1.0,
        )
        result = adjust_basis_for_assignment(
            lot, opt, AssignmentType.LONG_CALL_EXERCISE
        )
        # Premium paid: $10.00 * 100 = $1000
        # Adjusted basis = 200 + (1000 / 100) = 210.00
        assert result.adjusted_cost_basis == Decimal("210.00")

    def test_wrong_action_raises(self) -> None:
        """AC-128.9: SLD trade + LONG_CALL_EXERCISE → BusinessRuleError."""
        lot = _stock_lot()
        opt = _option_trade(action=TradeAction.SLD)  # Wrong — should be BOT
        with pytest.raises(BusinessRuleError, match="action"):
            adjust_basis_for_assignment(lot, opt, AssignmentType.LONG_CALL_EXERCISE)


# ── AC-128.5: Long put exercise ─────────────────────────────────────────


class TestLongPutExercise:
    """AC-128.5: Long put exercise reduces amount realized by premium paid."""

    def test_reduces_proceeds_by_premium(self) -> None:
        """Holder (BOT) put exercised → amount realized reduced by premium paid."""
        lot = _stock_lot(
            cost_basis=Decimal("100.00"),
            quantity=100.0,
            proceeds=Decimal("150.00"),
        )
        lot.is_closed = True
        lot.close_date = datetime(2026, 3, 20, tzinfo=timezone.utc)
        opt = _option_trade(
            instrument="AAPL 260320 P 150",
            action=TradeAction.BOT,
            price=3.00,
            quantity=1.0,
        )
        result = adjust_basis_for_assignment(lot, opt, AssignmentType.LONG_PUT_EXERCISE)
        # Premium paid: $3.00 * 100 = $300
        # Adjusted proceeds = 150 - (300 / 100) = 147.00
        assert result.adjusted_proceeds == Decimal("147.00")

    def test_wrong_lot_side_raises(self) -> None:
        """AC-128.5 negative: BOT put with mismatched lot raises error."""
        lot = _stock_lot(ticker="MSFT")  # Different ticker
        opt = _option_trade(
            instrument="AAPL 260320 P 150",
            action=TradeAction.BOT,
        )
        with pytest.raises(BusinessRuleError, match="ticker"):
            adjust_basis_for_assignment(lot, opt, AssignmentType.LONG_PUT_EXERCISE)


# ── F2 Correction: put/call↔AssignmentType mismatch ────────────────────


class TestPutCallAssignmentMismatch:
    """F2: option put_call must match AssignmentType kind.

    Written put/long put require P; written call/long call require C.
    """

    def test_call_option_with_written_put_assignment_raises(self) -> None:
        """Call option (C) routed through WRITTEN_PUT_ASSIGNMENT → error."""
        lot = _stock_lot(ticker="AAPL", cost_basis=Decimal("150.00"))
        opt = _option_trade(
            instrument="AAPL 260320 C 150",  # C = call
            action=TradeAction.SLD,
            price=5.00,
        )
        with pytest.raises(BusinessRuleError, match="put_call"):
            adjust_basis_for_assignment(lot, opt, AssignmentType.WRITTEN_PUT_ASSIGNMENT)

    def test_put_option_with_written_call_assignment_raises(self) -> None:
        """Put option (P) routed through WRITTEN_CALL_ASSIGNMENT → error."""
        lot = _stock_lot(
            ticker="AAPL",
            cost_basis=Decimal("100.00"),
            proceeds=Decimal("200.00"),
        )
        opt = _option_trade(
            instrument="AAPL 260320 P 150",  # P = put
            action=TradeAction.SLD,
            price=8.00,
        )
        with pytest.raises(BusinessRuleError, match="put_call"):
            adjust_basis_for_assignment(
                lot, opt, AssignmentType.WRITTEN_CALL_ASSIGNMENT
            )

    def test_put_option_with_long_call_exercise_raises(self) -> None:
        """Put option (P) routed through LONG_CALL_EXERCISE → error."""
        lot = _stock_lot(ticker="AAPL", cost_basis=Decimal("200.00"))
        opt = _option_trade(
            instrument="AAPL 260320 P 200",  # P = put
            action=TradeAction.BOT,
            price=10.00,
        )
        with pytest.raises(BusinessRuleError, match="put_call"):
            adjust_basis_for_assignment(lot, opt, AssignmentType.LONG_CALL_EXERCISE)

    def test_call_option_with_long_put_exercise_raises(self) -> None:
        """Call option (C) routed through LONG_PUT_EXERCISE → error."""
        lot = _stock_lot(
            ticker="AAPL",
            cost_basis=Decimal("100.00"),
            proceeds=Decimal("150.00"),
        )
        opt = _option_trade(
            instrument="AAPL 260320 C 150",  # C = call
            action=TradeAction.BOT,
            price=3.00,
        )
        with pytest.raises(BusinessRuleError, match="put_call"):
            adjust_basis_for_assignment(lot, opt, AssignmentType.LONG_PUT_EXERCISE)
