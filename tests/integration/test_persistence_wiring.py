# tests/integration/test_persistence_wiring.py
"""Integration tests for UoW round-trip persistence.

Covers AC-1 (real UoW), AC-2 (services receive real UoW), AC-4 (watchlists
attr on UoW), AC-10 (trade round-trip).
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from zorivest_core.domain.entities import Trade, Watchlist
from zorivest_core.domain.enums import TradeAction
from zorivest_infra.database.unit_of_work import SqlAlchemyUnitOfWork


@pytest.fixture()
def uow(engine):
    """Create a real UoW backed by the integration test engine."""
    return SqlAlchemyUnitOfWork(engine)


class TestUoWTradeRoundTrip:
    """AC-10: create trade via UoW, commit, verify persistence."""

    def _make_trade(self, exec_id: str = "test-exec-1") -> Trade:
        return Trade(
            exec_id=exec_id,
            time=datetime.now(timezone.utc),
            instrument="AAPL",
            action=TradeAction.BOT,
            quantity=100,
            price=150.0,
            account_id="acct-1",
        )

    def test_trade_save_and_get(self, uow):
        trade = self._make_trade("save-get-exec")
        with uow:
            uow.trades.save(trade)
            uow.commit()

        with uow:
            fetched = uow.trades.get("save-get-exec")
            assert fetched is not None
            assert fetched.instrument == "AAPL"
            assert fetched.action == TradeAction.BOT

    def test_trade_list(self, uow):
        with uow:
            uow.trades.save(self._make_trade("list-exec-1"))
            uow.commit()

        with uow:
            trades = uow.trades.list_all()
            assert len(trades) >= 1

    def test_trade_delete(self, uow):
        trade = self._make_trade("del-exec-1")
        with uow:
            uow.trades.save(trade)
            uow.commit()

        with uow:
            uow.trades.delete("del-exec-1")
            uow.commit()

        with uow:
            assert uow.trades.get("del-exec-1") is None


class TestUoWWatchlistRoundTrip:
    """AC-4 + AC-10: watchlists attr exists and supports round-trip."""

    def test_watchlist_attr_exists(self, uow):
        """AC-4: SqlAlchemyUnitOfWork has a 'watchlists' attribute."""
        with uow:
            assert hasattr(uow, "watchlists"), "UoW must have 'watchlists' repo"

    def test_watchlist_create_and_get(self, uow):
        wl = Watchlist(
            id=0,
            name="UoW Test WL",
            description="round-trip test",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            tickers=[],
        )
        with uow:
            uow.watchlists.save(wl)
            uow.commit()

        with uow:
            fetched = uow.watchlists.get(wl.id)
            assert fetched is not None
            assert fetched.name == "UoW Test WL"


class TestUoWSettingsRoundTrip:
    """AC-10: settings persistence."""

    def test_settings_save_and_get(self, uow):
        with uow:
            uow.settings.bulk_upsert({"test.key": "test-value"})
            uow.commit()

        with uow:
            model = uow.settings.get("test.key")
            assert model is not None
            assert model.value == "test-value"


class TestUoWNestedRollbackIsolation:
    """Regression: failed inner `with uow:` must rollback, not leak dirty writes."""

    def test_nested_failure_does_not_leak(self, uow):
        """A failed inner context at depth=2 must not persist dirty writes."""
        # Outer context (simulates lifespan pre-entry)
        with uow:
            uow.settings.bulk_upsert({"clean.key": "clean_value"})
            uow.commit()

            # Inner context that fails (simulates a service request)
            try:
                with uow:
                    uow.settings.bulk_upsert({"leaked.key": "leaked_value"})
                    raise RuntimeError("simulated request failure")
            except RuntimeError:
                pass

            # The dirty write from the failed inner block should be rolled back
            uow.commit()  # Commit any prior clean work

        # Verify: leaked writes must NOT have persisted
        with uow:
            result = uow.settings.get("leaked.key")
            assert result is None, (
                "Dirty write from failed inner block was not rolled back"
            )

            # Clean write should still be there
            clean = uow.settings.get("clean.key")
            assert clean is not None
            assert clean.value == "clean_value"
