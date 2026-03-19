# tests/integration/test_watchlist_repository.py
"""Integration tests for SqlAlchemyWatchlistRepository.

Covers AC-4 (watchlists attr on UoW) and AC-5 (get, save, update, delete,
exists_by_name, add_item, remove_item, get_items, list_all).
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from zorivest_core.domain.entities import Watchlist, WatchlistItem
from zorivest_infra.database.watchlist_repository import (
    SqlAlchemyWatchlistRepository,
)


@pytest.fixture()
def repo(db_session):
    """Create a watchlist repository backed by the test session."""
    return SqlAlchemyWatchlistRepository(db_session)


def _make_watchlist(name: str = "Test WL", desc: str = "desc") -> Watchlist:
    return Watchlist(
        id=0,
        name=name,
        description=desc,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        tickers=[],
    )


def _make_item(watchlist_id: int, ticker: str = "AAPL") -> WatchlistItem:
    return WatchlistItem(
        id=0,
        watchlist_id=watchlist_id,
        ticker=ticker,
        added_at=datetime.now(timezone.utc),
        notes="test note",
    )


class TestWatchlistCRUD:
    """AC-5: save, get, list_all, update, delete."""

    def test_save_and_get(self, repo):
        wl = _make_watchlist()
        repo.save(wl)
        assert wl.id > 0, "save() should hydrate auto-ID"

        fetched = repo.get(wl.id)
        assert fetched is not None
        assert fetched.name == "Test WL"

    def test_list_all(self, repo):
        repo.save(_make_watchlist("A"))
        repo.save(_make_watchlist("B"))
        repo.save(_make_watchlist("C"))

        result = repo.list_all(limit=2)
        assert len(result) == 2

        all_result = repo.list_all()
        assert len(all_result) >= 3

    def test_update(self, repo):
        wl = _make_watchlist("Original")
        repo.save(wl)

        wl.name = "Updated"
        wl.description = "new desc"
        repo.update(wl)

        fetched = repo.get(wl.id)
        assert fetched is not None
        assert fetched.name == "Updated"
        assert fetched.description == "new desc"

    def test_delete(self, repo):
        wl = _make_watchlist("ToDelete")
        repo.save(wl)
        wl_id = wl.id

        repo.delete(wl_id)
        assert repo.get(wl_id) is None

    def test_get_nonexistent_returns_none(self, repo):
        assert repo.get(99999) is None


class TestWatchlistItems:
    """AC-5: add_item, get_items, remove_item."""

    def test_add_and_get_items(self, repo):
        wl = _make_watchlist("With Items")
        repo.save(wl)

        repo.add_item(_make_item(wl.id, "AAPL"))
        repo.add_item(_make_item(wl.id, "GOOGL"))

        items = repo.get_items(wl.id)
        assert len(items) == 2
        tickers = {i.ticker for i in items}
        assert tickers == {"AAPL", "GOOGL"}

    def test_remove_item(self, repo):
        wl = _make_watchlist("Remove Test")
        repo.save(wl)

        repo.add_item(_make_item(wl.id, "MSFT"))
        repo.add_item(_make_item(wl.id, "TSLA"))

        repo.remove_item(wl.id, "MSFT")
        items = repo.get_items(wl.id)
        assert len(items) == 1
        assert items[0].ticker == "TSLA"


class TestExistsByName:
    """AC-5: exists_by_name."""

    def test_exists_true(self, repo):
        repo.save(_make_watchlist("UniqueWL"))
        assert repo.exists_by_name("UniqueWL") is True

    def test_exists_false(self, repo):
        assert repo.exists_by_name("NonexistentWL") is False
