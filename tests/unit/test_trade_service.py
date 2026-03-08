# tests/unit/test_trade_service.py
"""Tests for TradeService (MEU-12, AC-12.1 through AC-12.4)."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from zorivest_core.application.commands import CreateTrade
from zorivest_core.domain.entities import Trade
from zorivest_core.domain.enums import TradeAction
from zorivest_core.domain.exceptions import BusinessRuleError, NotFoundError
from zorivest_core.services.trade_service import TradeService


def _make_uow() -> MagicMock:
    """Create a mock UoW with trades, images, accounts, balance_snapshots, round_trips."""
    uow = MagicMock()
    uow.__enter__ = MagicMock(return_value=uow)
    uow.__exit__ = MagicMock(return_value=False)
    return uow


def _make_create_trade_cmd(**overrides: object) -> CreateTrade:
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
    return CreateTrade(**defaults)  # type: ignore[arg-type]


class TestCreateTrade:
    """AC-12.1, AC-12.2, AC-12.3."""

    def test_create_trade_success(self) -> None:
        """AC-12.3: create_trade saves and commits on success."""
        uow = _make_uow()
        uow.trades.exists.return_value = False
        uow.trades.exists_by_fingerprint_since.return_value = False

        svc = TradeService(uow)
        cmd = _make_create_trade_cmd()
        result = svc.create_trade(cmd)

        assert result.exec_id == "E001"
        assert result.instrument == "AAPL"
        uow.trades.save.assert_called_once()
        uow.commit.assert_called_once()

    def test_create_trade_deduplicates_by_exec_id(self) -> None:
        """AC-12.1: rejects duplicate exec_id with BusinessRuleError."""
        uow = _make_uow()
        uow.trades.exists.return_value = True

        svc = TradeService(uow)
        with pytest.raises(BusinessRuleError, match="already exists"):
            svc.create_trade(_make_create_trade_cmd())

    def test_create_trade_deduplicates_by_fingerprint(self) -> None:
        """AC-12.2: rejects fingerprint match within 30-day window."""
        uow = _make_uow()
        uow.trades.exists.return_value = False
        uow.trades.exists_by_fingerprint_since.return_value = True

        svc = TradeService(uow)
        with pytest.raises(BusinessRuleError, match="fingerprint"):
            svc.create_trade(_make_create_trade_cmd())


class TestGetTrade:
    def test_get_trade_success(self) -> None:
        trade = Trade(
            exec_id="E001",
            time=datetime(2025, 1, 15),
            instrument="AAPL",
            action=TradeAction.BOT,
            quantity=100.0,
            price=150.50,
            account_id="ACC001",
        )
        uow = _make_uow()
        uow.trades.get.return_value = trade

        svc = TradeService(uow)
        result = svc.get_trade("E001")
        assert result.exec_id == "E001"

    def test_get_trade_not_found(self) -> None:
        uow = _make_uow()
        uow.trades.get.return_value = None

        svc = TradeService(uow)
        with pytest.raises(NotFoundError, match="E999"):
            svc.get_trade("E999")


class TestMatchRoundTrips:
    """AC-12.4."""

    def test_match_round_trips(self) -> None:
        """AC-12.4: groups executions via list_for_account and saves to round_trips."""
        t1 = Trade(
            exec_id="E001", time=datetime(2025, 1, 15),
            instrument="AAPL", action=TradeAction.BOT,
            quantity=100.0, price=150.0, account_id="ACC001",
        )
        t2 = Trade(
            exec_id="E002", time=datetime(2025, 1, 16),
            instrument="AAPL", action=TradeAction.SLD,
            quantity=100.0, price=155.0, account_id="ACC001",
        )
        uow = _make_uow()
        uow.trades.list_for_account.return_value = [t1, t2]

        svc = TradeService(uow)
        result = svc.match_round_trips("ACC001")

        assert len(result) == 1
        assert result[0]["instrument"] == "AAPL"
        uow.round_trips.save.assert_called_once()
        uow.commit.assert_called_once()
