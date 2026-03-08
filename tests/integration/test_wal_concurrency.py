# tests/integration/test_wal_concurrency.py
"""WAL mode and concurrency tests (MEU-16, Finding 2).

Source: 02-infrastructure.md §2.2 exit criteria, §2.3 test plan
Requires file-based SQLite (WAL doesn't work with :memory:).
"""

from __future__ import annotations

import threading

from sqlalchemy import text
from sqlalchemy.orm import Session

from zorivest_infra.database.models import Base
from zorivest_infra.database.unit_of_work import create_engine_with_wal


class TestWalMode:
    """Verify WAL journaling is enabled on file-based DBs."""

    def test_wal_mode_enabled(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        """WAL pragma returns 'wal' for file-based engine."""
        db_path = tmp_path / "test_wal.db"
        engine = create_engine_with_wal(f"sqlite:///{db_path}")
        Base.metadata.create_all(engine)

        with Session(engine) as session:
            result = session.execute(text("PRAGMA journal_mode"))
            mode = result.scalar()
            assert mode == "wal"

    def test_synchronous_normal(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        """SYNCHRONOUS pragma is set to NORMAL (1)."""
        db_path = tmp_path / "test_sync.db"
        engine = create_engine_with_wal(f"sqlite:///{db_path}")
        Base.metadata.create_all(engine)

        with Session(engine) as session:
            result = session.execute(text("PRAGMA synchronous"))
            level = result.scalar()
            assert level == 1  # 1 = NORMAL


class TestPerThreadSessions:
    """Verify per-thread Session isolation per spec §2.2."""

    def test_concurrent_read_write(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        """Two threads can read/write concurrently with separate sessions."""
        db_path = tmp_path / "test_concurrent.db"
        engine = create_engine_with_wal(f"sqlite:///{db_path}")

        # Create schema
        with engine.connect() as conn:
            conn.execute(text("CREATE TABLE items (id INTEGER PRIMARY KEY, val TEXT)"))
            conn.commit()

        errors: list[Exception] = []

        def writer() -> None:
            try:
                with Session(engine) as session:
                    session.execute(
                        text("INSERT INTO items (val) VALUES (:v)"),
                        {"v": "from_writer"},
                    )
                    session.commit()
            except Exception as e:
                errors.append(e)

        def reader() -> None:
            try:
                with Session(engine) as session:
                    session.execute(text("SELECT * FROM items"))
            except Exception as e:
                errors.append(e)

        t1 = threading.Thread(target=writer)
        t2 = threading.Thread(target=reader)
        t1.start()
        t2.start()
        t1.join(timeout=5)
        t2.join(timeout=5)

        assert not errors, f"Thread errors: {errors}"

        # Verify write persisted
        with Session(engine) as session:
            result = session.execute(text("SELECT val FROM items"))
            rows = result.fetchall()
            assert any(r[0] == "from_writer" for r in rows)
