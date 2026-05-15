"""Integration tests for inline schema migrations (TAX-DBMIGRATION).

Verifies that the ``_inline_migrations`` list in ``main.py`` correctly
adds Phase 3B/3C columns to an old-shape ``tax_lots`` table, that the
migration is idempotent, and that fresh databases already have the
columns via ``Base.metadata.create_all()``.
"""

from __future__ import annotations

from sqlalchemy import create_engine, inspect, text

from zorivest_infra.database.models import Base


# ── The 11 original columns (pre-Phase 3B/3C) ─────────────────────────
_OLD_SHAPE_DDL = """\
CREATE TABLE tax_lots (
    lot_id     VARCHAR    PRIMARY KEY,
    account_id VARCHAR    NOT NULL,
    ticker     VARCHAR    NOT NULL,
    open_date  DATETIME   NOT NULL,
    close_date DATETIME,
    quantity   FLOAT      NOT NULL,
    cost_basis NUMERIC(15,6) NOT NULL,
    proceeds   NUMERIC(15,6) NOT NULL DEFAULT 0,
    wash_sale_adjustment NUMERIC(15,6) NOT NULL DEFAULT 0,
    is_closed  BOOLEAN    NOT NULL DEFAULT 0,
    linked_trade_ids TEXT
);
"""

# The 3 columns that Phase 3B/3C added to TaxLotModel but forgot to
# add to ``_inline_migrations``.
EXPECTED_NEW_COLUMNS = {"cost_basis_method", "realized_gain_loss", "acquisition_source"}


def _get_column_names(engine, table: str) -> set[str]:
    """Return column names for *table* using the SQLAlchemy inspector."""
    insp = inspect(engine)
    return {col["name"] for col in insp.get_columns(table)}


def _run_inline_migrations(engine) -> None:  # noqa: ANN001
    """Execute the inline migration loop from ``main.py``.

    We import the list directly so the test stays in sync with the real
    startup code — no duplication of SQL strings.
    """
    # Import the migration list from the actual module
    from zorivest_api.main import _get_inline_migrations

    migrations = _get_inline_migrations()
    with engine.connect() as conn:
        for stmt in migrations:
            try:
                conn.execute(text(stmt))
                conn.commit()
            except Exception:
                conn.rollback()


# ── Tests ──────────────────────────────────────────────────────────────


class TestInlineMigrationsTaxLots:
    """Verify that inline migrations backfill the 3 missing tax_lots columns."""

    def test_old_shape_gains_columns_after_migration(self) -> None:
        """An old-shape tax_lots table (11 columns) should gain all 3
        Phase 3B/3C columns after running inline migrations."""
        engine = create_engine("sqlite://", echo=False)

        # Create old-shape table manually (no ORM)
        with engine.connect() as conn:
            conn.execute(text(_OLD_SHAPE_DDL))
            conn.commit()

        # Precondition: new columns do NOT exist
        before = _get_column_names(engine, "tax_lots")
        assert EXPECTED_NEW_COLUMNS.isdisjoint(before), (
            f"Old-shape table should not have new columns, found: "
            f"{EXPECTED_NEW_COLUMNS & before}"
        )

        # Act: run inline migrations
        _run_inline_migrations(engine)

        # Assert: all 3 columns now exist
        after = _get_column_names(engine, "tax_lots")
        missing = EXPECTED_NEW_COLUMNS - after
        assert not missing, f"Columns still missing after migration: {missing}"

    def test_migration_is_idempotent(self) -> None:
        """Running inline migrations twice on the same database must not
        raise errors and must not duplicate columns."""
        engine = create_engine("sqlite://", echo=False)

        with engine.connect() as conn:
            conn.execute(text(_OLD_SHAPE_DDL))
            conn.commit()

        # First run
        _run_inline_migrations(engine)
        cols_after_first = _get_column_names(engine, "tax_lots")

        # Second run — must not error
        _run_inline_migrations(engine)
        cols_after_second = _get_column_names(engine, "tax_lots")

        assert cols_after_first == cols_after_second, (
            "Column set changed after second migration run"
        )

    def test_fresh_db_has_all_columns(self) -> None:
        """A fresh database created via ``Base.metadata.create_all()``
        should already have all 3 Phase 3B/3C columns without needing
        the ALTER TABLE migration (AC-MIG.6)."""
        engine = create_engine("sqlite://", echo=False)
        Base.metadata.create_all(engine)

        cols = _get_column_names(engine, "tax_lots")
        missing = EXPECTED_NEW_COLUMNS - cols
        assert not missing, f"Fresh create_all DB missing columns: {missing}"
