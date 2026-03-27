# packages/core/src/zorivest_core/services/watchlist_service.py
"""Watchlist lifecycle management.

MEU-68: FIC AC-2 through AC-5. Standalone WatchlistService with CRUD
and item management. Follows the same UoW pattern as ReportService.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from typing import TYPE_CHECKING, Any

from zorivest_core.domain.entities import Watchlist, WatchlistItem

if TYPE_CHECKING:
    from zorivest_core.application.ports import UnitOfWork


class WatchlistService:
    """Watchlist CRUD and item management.

    MEU-68: Standalone service following the ReportService UoW pattern.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    # ── Watchlist CRUD ──────────────────────────────────────────────────

    def create(self, name: str, description: str = "") -> Watchlist:
        """Create a named watchlist.

        Raises:
            ValueError: If a watchlist with the same name already exists.
        """
        with self.uow:
            # AC-4: Duplicate watchlist name rejection
            if self.uow.watchlists.exists_by_name(name):
                msg = f"Watchlist '{name}' already exists"
                raise ValueError(msg)

            now = datetime.now()
            watchlist = Watchlist(
                id=0,  # auto-assigned by DB
                name=name,
                description=description,
                created_at=now,
                updated_at=now,
            )
            self.uow.watchlists.save(watchlist)
            self.uow.commit()

            # Re-fetch to hydrate the DB-assigned ID
            hydrated = self.uow.watchlists.get(watchlist.id)
            return hydrated if hydrated is not None else watchlist

    def get(self, watchlist_id: int) -> Watchlist | None:
        """Fetch a watchlist by ID."""
        with self.uow:
            return self.uow.watchlists.get(watchlist_id)

    def list_all(self, limit: int = 100, offset: int = 0) -> list[Watchlist]:
        """List watchlists with pagination."""
        with self.uow:
            return self.uow.watchlists.list_all(limit=limit, offset=offset)

    def update(self, watchlist_id: int, updates: dict[str, Any]) -> Watchlist:
        """Update a watchlist's metadata.

        Raises:
            ValueError: If no watchlist exists with the given ID.
            ValueError: If name update conflicts with an existing watchlist.
        """
        with self.uow:
            existing = self.uow.watchlists.get(watchlist_id)
            if existing is None:
                msg = f"Watchlist {watchlist_id} not found"
                raise ValueError(msg)

            # AC-4: Reject duplicate name on update
            new_name = updates.get("name")
            if new_name and new_name != existing.name:
                if self.uow.watchlists.exists_by_name(new_name):
                    msg = f"Watchlist '{new_name}' already exists"
                    raise ValueError(msg)

            updated = replace(existing, **updates, updated_at=datetime.now())
            self.uow.watchlists.update(updated)
            self.uow.commit()
            return updated

    def delete(self, watchlist_id: int) -> None:
        """Delete a watchlist by ID (cascades items).

        Raises:
            ValueError: If no watchlist exists with the given ID.
        """
        with self.uow:
            existing = self.uow.watchlists.get(watchlist_id)
            if existing is None:
                msg = f"Watchlist {watchlist_id} not found"
                raise ValueError(msg)
            self.uow.watchlists.delete(watchlist_id)
            self.uow.commit()

    # ── Item management ─────────────────────────────────────────────────

    def add_ticker(
        self,
        watchlist_id: int,
        ticker: str,
        notes: str = "",
    ) -> WatchlistItem:
        """Add a ticker to a watchlist.

        Raises:
            ValueError: If watchlist not found.
            ValueError: If ticker already in this watchlist (AC-5).
        """
        with self.uow:
            wl = self.uow.watchlists.get(watchlist_id)
            if wl is None:
                msg = f"Watchlist {watchlist_id} not found"
                raise ValueError(msg)

            # AC-5: Duplicate ticker in same watchlist rejection
            existing_items = self.uow.watchlists.get_items(watchlist_id)
            for item in existing_items:
                if item.ticker.upper() == ticker.upper():
                    msg = f"Ticker '{ticker}' already in watchlist {watchlist_id}"
                    raise ValueError(msg)

            item = WatchlistItem(
                id=0,  # auto-assigned by DB
                watchlist_id=watchlist_id,
                ticker=ticker.upper(),
                added_at=datetime.now(),
                notes=notes,
            )
            self.uow.watchlists.add_item(item)
            self.uow.commit()

            # Re-fetch items to get hydrated ID
            items = self.uow.watchlists.get_items(watchlist_id)
            for i in items:
                if i.ticker == ticker.upper():
                    return i
            return item

    def remove_ticker(self, watchlist_id: int, ticker: str) -> None:
        """Remove a ticker from a watchlist.

        Raises:
            ValueError: If watchlist or ticker not found.
        """
        with self.uow:
            wl = self.uow.watchlists.get(watchlist_id)
            if wl is None:
                msg = f"Watchlist {watchlist_id} not found"
                raise ValueError(msg)

            self.uow.watchlists.remove_item(watchlist_id, ticker.upper())
            self.uow.commit()

    def get_items(self, watchlist_id: int) -> list[WatchlistItem]:
        """Get all items in a watchlist.

        Raises:
            ValueError: If watchlist not found.
        """
        with self.uow:
            wl = self.uow.watchlists.get(watchlist_id)
            if wl is None:
                msg = f"Watchlist {watchlist_id} not found"
                raise ValueError(msg)
            return self.uow.watchlists.get_items(watchlist_id)
