# tests/unit/test_watchlist_service.py
"""WatchlistService unit tests (MEU-68).

Tests AC-2 (CRUD), AC-3 (item management), AC-4 (duplicate name),
AC-5 (duplicate ticker), AC-9 (cascade delete).
"""

from __future__ import annotations

import pytest

from zorivest_api.stubs import StubUnitOfWork
from zorivest_core.services.watchlist_service import WatchlistService


@pytest.fixture()
def service() -> WatchlistService:
    """Create a WatchlistService with in-memory stub UoW."""
    return WatchlistService(StubUnitOfWork())  # type: ignore[arg-type]


# ── AC-2: CRUD ──────────────────────────────────────────────────────────


class TestCreate:
    def test_create_returns_watchlist_with_id(self, service: WatchlistService) -> None:
        wl = service.create("Momentum Plays", "High-beta names")
        assert wl.id > 0
        assert wl.name == "Momentum Plays"
        assert wl.description == "High-beta names"

    def test_create_sets_timestamps(self, service: WatchlistService) -> None:
        wl = service.create("Test")
        assert wl.created_at is not None
        assert wl.updated_at is not None

    def test_create_default_empty_description(self, service: WatchlistService) -> None:
        wl = service.create("Basic")
        assert wl.description == ""


class TestGet:
    def test_get_existing(self, service: WatchlistService) -> None:
        created = service.create("Tech")
        fetched = service.get(created.id)
        assert fetched is not None
        assert fetched.name == "Tech"

    def test_get_nonexistent_returns_none(self, service: WatchlistService) -> None:
        assert service.get(999) is None


class TestListAll:
    def test_list_empty(self, service: WatchlistService) -> None:
        assert service.list_all() == []

    def test_list_returns_all(self, service: WatchlistService) -> None:
        service.create("A")
        service.create("B")
        result = service.list_all()
        assert len(result) == 2

    def test_list_pagination(self, service: WatchlistService) -> None:
        for i in range(5):
            service.create(f"WL-{i}")
        page = service.list_all(limit=2, offset=2)
        assert len(page) == 2


class TestUpdate:
    def test_update_name(self, service: WatchlistService) -> None:
        wl = service.create("Old Name")
        updated = service.update(wl.id, {"name": "New Name"})
        assert updated.name == "New Name"

    def test_update_nonexistent_raises(self, service: WatchlistService) -> None:
        with pytest.raises(ValueError, match="not found"):
            service.update(999, {"name": "X"})


class TestDelete:
    def test_delete_existing(self, service: WatchlistService) -> None:
        wl = service.create("ToDelete")
        service.delete(wl.id)
        assert service.get(wl.id) is None

    def test_delete_nonexistent_raises(self, service: WatchlistService) -> None:
        with pytest.raises(ValueError, match="not found"):
            service.delete(999)


# ── AC-4: Duplicate name rejection ──────────────────────────────────────


class TestDuplicateName:
    def test_create_duplicate_name_raises(self, service: WatchlistService) -> None:
        service.create("Unique")
        with pytest.raises(ValueError, match="already exists"):
            service.create("Unique")

    def test_update_to_duplicate_name_raises(self, service: WatchlistService) -> None:
        service.create("First")
        wl2 = service.create("Second")
        with pytest.raises(ValueError, match="already exists"):
            service.update(wl2.id, {"name": "First"})

    def test_update_same_name_ok(self, service: WatchlistService) -> None:
        wl = service.create("Same")
        # Updating with same name should not raise
        updated = service.update(wl.id, {"name": "Same", "description": "updated"})
        assert updated.description == "updated"


# ── AC-3: Item management ──────────────────────────────────────────────


class TestAddTicker:
    def test_add_ticker(self, service: WatchlistService) -> None:
        wl = service.create("Test")
        item = service.add_ticker(wl.id, "AAPL", "Core holding")
        assert item.id > 0
        assert item.ticker == "AAPL"
        assert item.notes == "Core holding"
        assert item.watchlist_id == wl.id

    def test_add_ticker_normalizes_case(self, service: WatchlistService) -> None:
        wl = service.create("Test")
        item = service.add_ticker(wl.id, "aapl")
        assert item.ticker == "AAPL"

    def test_add_to_nonexistent_watchlist_raises(self, service: WatchlistService) -> None:
        with pytest.raises(ValueError, match="not found"):
            service.add_ticker(999, "SPY")


class TestRemoveTicker:
    def test_remove_ticker(self, service: WatchlistService) -> None:
        wl = service.create("Test")
        service.add_ticker(wl.id, "AAPL")
        service.remove_ticker(wl.id, "AAPL")
        items = service.get_items(wl.id)
        assert len(items) == 0

    def test_remove_from_nonexistent_watchlist_raises(self, service: WatchlistService) -> None:
        with pytest.raises(ValueError, match="not found"):
            service.remove_ticker(999, "SPY")


class TestGetItems:
    def test_get_items_returns_all(self, service: WatchlistService) -> None:
        wl = service.create("Test")
        service.add_ticker(wl.id, "AAPL")
        service.add_ticker(wl.id, "MSFT")
        items = service.get_items(wl.id)
        assert len(items) == 2
        tickers = {i.ticker for i in items}
        assert tickers == {"AAPL", "MSFT"}

    def test_get_items_nonexistent_watchlist_raises(self, service: WatchlistService) -> None:
        with pytest.raises(ValueError, match="not found"):
            service.get_items(999)


# ── AC-5: Duplicate ticker rejection ────────────────────────────────────


class TestDuplicateTicker:
    def test_add_duplicate_ticker_raises(self, service: WatchlistService) -> None:
        wl = service.create("Test")
        service.add_ticker(wl.id, "AAPL")
        with pytest.raises(ValueError, match="already in watchlist"):
            service.add_ticker(wl.id, "AAPL")

    def test_case_insensitive_duplicate_raises(self, service: WatchlistService) -> None:
        wl = service.create("Test")
        service.add_ticker(wl.id, "AAPL")
        with pytest.raises(ValueError, match="already in watchlist"):
            service.add_ticker(wl.id, "aapl")


# ── AC-9: Cascade delete ────────────────────────────────────────────────


class TestCascadeDelete:
    """AC-9: Deleting a watchlist removes all its items."""

    def test_delete_watchlist_cascades_items(self, service: WatchlistService) -> None:
        # Create two watchlists with items
        wl_a = service.create("WatchlistA")
        service.add_ticker(wl_a.id, "AAPL")
        service.add_ticker(wl_a.id, "MSFT")
        wl_b = service.create("WatchlistB")
        service.add_ticker(wl_b.id, "SPY")

        # Delete watchlist A
        service.delete(wl_a.id)

        # Watchlist B items must be intact
        items_b = service.get_items(wl_b.id)
        assert len(items_b) == 1
        assert items_b[0].ticker == "SPY"

        # Directly verify no orphaned items remain for deleted watchlist A
        repo = service.uow.watchlists  # type: ignore[union-attr]
        orphans = [i for i in repo._items if i.watchlist_id == wl_a.id]  # type: ignore[attr-defined]
        assert orphans == [], f"Orphaned items found: {orphans}"
