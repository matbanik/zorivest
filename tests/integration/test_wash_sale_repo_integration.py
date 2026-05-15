# tests/integration/test_wash_sale_repo_integration.py
"""Integration tests for WashSaleChain repository CRUD (MEU-130 AC-130.10).

C5 correction: Real save/get/update/list round-trip tests using db_session fixture.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from zorivest_core.domain.enums import WashSaleEventType, WashSaleStatus
from zorivest_core.domain.tax.wash_sale import WashSaleChain, WashSaleEntry


# ── Fixtures ────────────────────────────────────────────────────────────


@pytest.fixture()
def engine():
    """Override the integration conftest engine to include wash sale tables."""
    import zorivest_infra.database.wash_sale_models  # noqa: F401 — register models with Base

    from sqlalchemy import create_engine

    from zorivest_infra.database.models import Base

    eng = create_engine(
        "sqlite://", echo=False, connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture()
def wash_sale_repo(db_session):
    """Create a WashSaleChain repository backed by the test session."""
    from zorivest_infra.database.wash_sale_repository import SqlWashSaleChainRepository

    return SqlWashSaleChainRepository(db_session)


# ── Factories ───────────────────────────────────────────────────────────


def _make_chain(
    chain_id: str = "chain-001",
    ticker: str = "AAPL",
    loss_lot_id: str = "lot-001",
    loss_date: datetime | None = None,
    loss_amount: Decimal = Decimal("1000.00"),
    disallowed_amount: Decimal = Decimal("1000.00"),
    status: WashSaleStatus = WashSaleStatus.DISALLOWED,
    loss_open_date: datetime | None = None,
    entries: list[WashSaleEntry] | None = None,
) -> WashSaleChain:
    return WashSaleChain(
        chain_id=chain_id,
        ticker=ticker,
        loss_lot_id=loss_lot_id,
        loss_date=loss_date or datetime(2026, 3, 15, tzinfo=timezone.utc),
        loss_amount=loss_amount,
        disallowed_amount=disallowed_amount,
        status=status,
        loss_open_date=loss_open_date or datetime(2026, 1, 15, tzinfo=timezone.utc),
        entries=entries or [],
    )


def _make_entry(
    entry_id: str = "entry-001",
    chain_id: str = "chain-001",
    event_type: WashSaleEventType = WashSaleEventType.LOSS_DISALLOWED,
    lot_id: str = "lot-001",
    amount: Decimal = Decimal("1000.00"),
    event_date: datetime | None = None,
    account_id: str = "acc-taxable",
) -> WashSaleEntry:
    return WashSaleEntry(
        entry_id=entry_id,
        chain_id=chain_id,
        event_type=event_type,
        lot_id=lot_id,
        amount=amount,
        event_date=event_date or datetime(2026, 3, 15, tzinfo=timezone.utc),
        account_id=account_id,
    )


# ── CRUD Tests ──────────────────────────────────────────────────────────


class TestWashSaleChainCRUD:
    """Real CRUD round-trip tests for SqlWashSaleChainRepository."""

    def test_save_and_get(self, wash_sale_repo) -> None:
        """Save a chain, fetch it back, verify all fields round-trip."""
        entry = _make_entry()
        chain = _make_chain(entries=[entry])
        wash_sale_repo.save(chain)

        fetched = wash_sale_repo.get("chain-001")
        assert fetched is not None
        assert fetched.chain_id == "chain-001"
        assert fetched.ticker == "AAPL"
        assert fetched.loss_lot_id == "lot-001"
        assert fetched.loss_amount == Decimal("1000.00")
        assert fetched.disallowed_amount == Decimal("1000.00")
        assert fetched.status == WashSaleStatus.DISALLOWED
        assert fetched.loss_open_date is not None

    def test_save_with_entries_roundtrip(self, wash_sale_repo) -> None:
        """Entries are persisted and returned with the chain."""
        entry = _make_entry(account_id="acc-taxable")
        chain = _make_chain(entries=[entry])
        wash_sale_repo.save(chain)

        fetched = wash_sale_repo.get("chain-001")
        assert fetched is not None
        assert len(fetched.entries) == 1
        assert fetched.entries[0].entry_id == "entry-001"
        assert fetched.entries[0].event_type == WashSaleEventType.LOSS_DISALLOWED
        assert fetched.entries[0].account_id == "acc-taxable"
        assert fetched.entries[0].amount == Decimal("1000.00")

    def test_get_nonexistent_returns_none(self, wash_sale_repo) -> None:
        """Non-existent chain_id → None."""
        assert wash_sale_repo.get("no-such-chain") is None

    def test_update(self, wash_sale_repo) -> None:
        """Save, mutate, update, re-fetch — verify changes persisted."""
        entry = _make_entry()
        chain = _make_chain(entries=[entry])
        wash_sale_repo.save(chain)

        # Mutate
        chain.status = WashSaleStatus.ABSORBED
        absorbed_entry = _make_entry(
            entry_id="entry-002",
            event_type=WashSaleEventType.BASIS_ADJUSTED,
            lot_id="repl-001",
            amount=Decimal("1000.00"),
            account_id="acc-brokerage",
        )
        chain.entries.append(absorbed_entry)
        wash_sale_repo.update(chain)

        fetched = wash_sale_repo.get("chain-001")
        assert fetched is not None
        assert fetched.status == WashSaleStatus.ABSORBED
        assert len(fetched.entries) == 2
        adjusted_entries = [
            e
            for e in fetched.entries
            if e.event_type == WashSaleEventType.BASIS_ADJUSTED
        ]
        assert len(adjusted_entries) == 1

    def test_list_for_ticker(self, wash_sale_repo) -> None:
        """list_for_ticker returns only chains for the given ticker."""
        wash_sale_repo.save(_make_chain(chain_id="c1", ticker="AAPL"))
        wash_sale_repo.save(_make_chain(chain_id="c2", ticker="MSFT"))
        wash_sale_repo.save(_make_chain(chain_id="c3", ticker="AAPL"))

        result = wash_sale_repo.list_for_ticker("AAPL")
        assert len(result) == 2
        assert all(c.ticker == "AAPL" for c in result)

    def test_list_active_default(self, wash_sale_repo) -> None:
        """list_active() without status returns DISALLOWED + ABSORBED chains."""
        wash_sale_repo.save(
            _make_chain(chain_id="c1", status=WashSaleStatus.DISALLOWED)
        )
        wash_sale_repo.save(_make_chain(chain_id="c2", status=WashSaleStatus.ABSORBED))
        wash_sale_repo.save(_make_chain(chain_id="c3", status=WashSaleStatus.RELEASED))
        wash_sale_repo.save(_make_chain(chain_id="c4", status=WashSaleStatus.DESTROYED))

        active = wash_sale_repo.list_active()
        assert len(active) == 2
        active_ids = {c.chain_id for c in active}
        assert active_ids == {"c1", "c2"}

    def test_list_active_by_status(self, wash_sale_repo) -> None:
        """list_active(status=X) returns only chains with that status."""
        wash_sale_repo.save(
            _make_chain(chain_id="c1", status=WashSaleStatus.DISALLOWED)
        )
        wash_sale_repo.save(_make_chain(chain_id="c2", status=WashSaleStatus.ABSORBED))

        absorbed = wash_sale_repo.list_active(status=WashSaleStatus.ABSORBED)
        assert len(absorbed) == 1
        assert absorbed[0].chain_id == "c2"

    def test_decimal_precision_roundtrip(self, wash_sale_repo) -> None:
        """Decimal fields maintain precision through persistence."""
        chain = _make_chain(
            loss_amount=Decimal("12345.67"),
            disallowed_amount=Decimal("9876.54"),
        )
        wash_sale_repo.save(chain)

        fetched = wash_sale_repo.get("chain-001")
        assert fetched is not None
        assert fetched.loss_amount == Decimal("12345.67")
        assert fetched.disallowed_amount == Decimal("9876.54")

    def test_entry_account_provenance_roundtrip(self, wash_sale_repo) -> None:
        """Entry account_id round-trips correctly through persistence."""
        entry = _make_entry(account_id="acc-ira-special")
        chain = _make_chain(entries=[entry])
        wash_sale_repo.save(chain)

        fetched = wash_sale_repo.get("chain-001")
        assert fetched is not None
        assert fetched.entries[0].account_id == "acc-ira-special"
