# tests/integration/conftest.py
"""Shared fixtures for integration tests.

Provides session-scoped engine and per-test transaction rollback
to ensure test isolation without recreating tables each test.
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from zorivest_infra.database.models import Base


@pytest.fixture(scope="session")
def engine():
    """Session-scoped in-memory SQLite engine with all tables created once."""
    eng = create_engine(
        "sqlite://", echo=False, connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture()
def db_session(engine):
    """Per-test session with transaction rollback for isolation.

    Each test gets a fresh session inside a savepoint. After the test
    completes (pass or fail), the savepoint is rolled back, leaving
    the database clean for the next test without DDL overhead.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    # Handle nested SAVEPOINT for tests that call session.commit()
    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(sess, trans):  # noqa: ANN001
        if trans.nested and not trans._parent.nested:
            sess.begin_nested()

    session.begin_nested()
    yield session

    session.close()
    transaction.rollback()
    connection.close()
