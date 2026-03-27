"""Property-based tests for trade entity invariants.

Tests that trades are never silently lost during save/list/delete cycles.

Source: testing-strategy.md §Property-Based Tests
Phase:  3.1 of Test Rigor Audit
"""

from __future__ import annotations

from datetime import datetime

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from zorivest_core.domain.entities import Trade
from zorivest_core.domain.enums import TradeAction
from zorivest_infra.database.models import Base
from zorivest_infra.database.repositories import SqlAlchemyTradeRepository


# ── Fixtures ────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def engine():
    """In-memory SQLite engine for trade invariant tests."""
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture()
def session(engine):
    """Per-test session with savepoint rollback."""
    connection = engine.connect()
    transaction = connection.begin()
    sess = Session(bind=connection)

    # Intercept commit → savepoint
    nested = connection.begin_nested()

    @event.listens_for(sess, "after_transaction_end")
    def _restart_savepoint(session, txn):
        nonlocal nested
        if txn.nested and not txn._parent.nested:
            nested = connection.begin_nested()

    yield sess

    sess.close()
    transaction.rollback()
    connection.close()


# ── Strategies ──────────────────────────────────────────────────────────

# Exec IDs: alphanumeric strings 1-20 chars, unique per test
exec_id_strat = st.text(
    alphabet=st.sampled_from("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"),
    min_size=1,
    max_size=20,
)

finite_float = st.floats(
    min_value=0.01, max_value=1e6, allow_nan=False, allow_infinity=False
)


def make_trade(exec_id: str, *, price: float = 100.0, qty: float = 10.0) -> Trade:
    return Trade(
        exec_id=exec_id,
        time=datetime(2025, 7, 1),
        instrument="SPY",
        action=TradeAction.BOT,
        quantity=qty,
        price=price,
        account_id="TEST",
    )


# ── Invariants ──────────────────────────────────────────────────────────


class TestTradeRoundtrip:
    """Trade save → get must return identical data."""

    @given(exec_id=exec_id_strat, price=finite_float, qty=finite_float)
    @settings(max_examples=50)
    def test_save_get_roundtrip(self, engine, exec_id, price, qty):
        """save() → get() returns identical field values."""
        # Fresh session per hypothesis example
        connection = engine.connect()
        transaction = connection.begin()
        sess = Session(bind=connection)

        try:
            repo = SqlAlchemyTradeRepository(sess)
            trade = make_trade(exec_id, price=price, qty=qty)
            repo.save(trade)
            sess.flush()

            loaded = repo.get(exec_id)
            assert loaded is not None
            assert loaded.exec_id == exec_id
            assert loaded.price == pytest.approx(price, rel=1e-6)
            assert loaded.quantity == pytest.approx(qty, rel=1e-6)
        finally:
            sess.close()
            transaction.rollback()
            connection.close()


class TestTradeNeverLost:
    """Trades must never be silently dropped."""

    @given(
        n=st.integers(min_value=1, max_value=20),
    )
    @settings(max_examples=30)
    def test_bulk_insert_preserves_count(self, engine, n):
        """Insert N trades → list_all() returns exactly N."""
        connection = engine.connect()
        transaction = connection.begin()
        sess = Session(bind=connection)

        try:
            repo = SqlAlchemyTradeRepository(sess)
            for i in range(n):
                trade = make_trade(f"BULK-{i}")
                repo.save(trade)
            sess.flush()

            all_trades = repo.list_all()
            assert len(all_trades) == n
        finally:
            sess.close()
            transaction.rollback()
            connection.close()

    @given(
        n=st.integers(min_value=2, max_value=10),
        delete_idx=st.integers(min_value=0),
    )
    @settings(max_examples=30)
    def test_delete_one_preserves_rest(self, engine, n, delete_idx):
        """Delete 1 of N trades → N-1 remain."""
        delete_idx = delete_idx % n  # Ensure valid index
        connection = engine.connect()
        transaction = connection.begin()
        sess = Session(bind=connection)

        try:
            repo = SqlAlchemyTradeRepository(sess)
            ids = [f"DEL-{i}" for i in range(n)]
            for eid in ids:
                repo.save(make_trade(eid))
            sess.flush()

            repo.delete(ids[delete_idx])
            sess.flush()

            remaining = repo.list_all()
            assert len(remaining) == n - 1
            remaining_ids = {t.exec_id for t in remaining}
            assert ids[delete_idx] not in remaining_ids
        finally:
            sess.close()
            transaction.rollback()
            connection.close()
