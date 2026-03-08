# tests/unit/test_trade_fingerprint.py
"""Tests for trade fingerprint function (MEU-12, AC-12.10)."""

from __future__ import annotations

from datetime import datetime

from zorivest_core.domain.entities import Trade
from zorivest_core.domain.enums import TradeAction
from zorivest_core.domain.trades.identity import trade_fingerprint


def _make_trade(**overrides: object) -> Trade:
    """Factory helper for Trade entities."""
    defaults = {
        "exec_id": "E001",
        "time": datetime(2025, 1, 15, 10, 30, 0),
        "instrument": "AAPL",
        "action": TradeAction.BOT,
        "quantity": 100.0,
        "price": 150.50,
        "account_id": "ACC001",
    }
    defaults.update(overrides)
    return Trade(**defaults)  # type: ignore[arg-type]


class TestTradeFingerprint:
    """AC-12.10: trade_fingerprint is deterministic and collision-resistant."""

    def test_deterministic(self) -> None:
        """Same trade produces same fingerprint."""
        trade = _make_trade()
        fp1 = trade_fingerprint(trade)
        fp2 = trade_fingerprint(trade)
        assert fp1 == fp2

    def test_different_exec_id_same_fingerprint(self) -> None:
        """Fingerprint is based on core fields, not exec_id."""
        t1 = _make_trade(exec_id="E001")
        t2 = _make_trade(exec_id="E999")
        assert trade_fingerprint(t1) == trade_fingerprint(t2)

    def test_different_instrument_different_fingerprint(self) -> None:
        t1 = _make_trade(instrument="AAPL")
        t2 = _make_trade(instrument="MSFT")
        assert trade_fingerprint(t1) != trade_fingerprint(t2)

    def test_different_action_different_fingerprint(self) -> None:
        t1 = _make_trade(action=TradeAction.BOT)
        t2 = _make_trade(action=TradeAction.SLD)
        assert trade_fingerprint(t1) != trade_fingerprint(t2)

    def test_different_quantity_different_fingerprint(self) -> None:
        t1 = _make_trade(quantity=100.0)
        t2 = _make_trade(quantity=200.0)
        assert trade_fingerprint(t1) != trade_fingerprint(t2)

    def test_different_price_different_fingerprint(self) -> None:
        t1 = _make_trade(price=150.50)
        t2 = _make_trade(price=151.00)
        assert trade_fingerprint(t1) != trade_fingerprint(t2)

    def test_different_time_different_fingerprint(self) -> None:
        t1 = _make_trade(time=datetime(2025, 1, 15, 10, 30, 0))
        t2 = _make_trade(time=datetime(2025, 1, 15, 10, 31, 0))
        assert trade_fingerprint(t1) != trade_fingerprint(t2)

    def test_different_account_different_fingerprint(self) -> None:
        t1 = _make_trade(account_id="ACC001")
        t2 = _make_trade(account_id="ACC002")
        assert trade_fingerprint(t1) != trade_fingerprint(t2)

    def test_returns_hex_string(self) -> None:
        fp = trade_fingerprint(_make_trade())
        assert isinstance(fp, str)
        assert len(fp) == 64  # SHA-256 hex digest
        assert all(c in "0123456789abcdef" for c in fp)
