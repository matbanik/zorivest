# pyright: reportArgumentType=false, reportReturnType=false, reportAttributeAccessIssue=false
# SQLAlchemy Column/Session types need suppression for Column[T] → T assignments.

"""SqlAlchemy Watchlist Repository implementation.

Source: 09a-persistence-integration.md §9A.3
Implements WatchlistRepository port (ports.py §WatchlistRepository).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from zorivest_core.domain.entities import Watchlist, WatchlistItem
from zorivest_infra.database.models import WatchlistItemModel, WatchlistModel


class SqlAlchemyWatchlistRepository:
    """SQL-backed watchlist repository.

    Implements all 9 methods from the WatchlistRepository port:
    get, save, update, delete, exists_by_name, add_item, remove_item,
    get_items, list_all.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    # ── CRUD ──────────────────────────────────────────────────────────

    def get(self, watchlist_id: int) -> Optional[Watchlist]:
        model = self._session.get(WatchlistModel, watchlist_id)
        if model is None:
            return None
        return _model_to_watchlist(model)

    def save(self, watchlist: Watchlist) -> None:
        model = _watchlist_to_model(watchlist)
        self._session.add(model)
        self._session.flush()
        watchlist.id = model.id  # hydrate auto-ID

    def update(self, watchlist: Watchlist) -> None:
        model = self._session.get(WatchlistModel, watchlist.id)
        if model is None:
            raise ValueError(f"Watchlist not found: {watchlist.id}")
        model.name = watchlist.name
        model.description = watchlist.description
        model.updated_at = datetime.now(timezone.utc)
        self._session.flush()

    def delete(self, watchlist_id: int) -> None:
        model = self._session.get(WatchlistModel, watchlist_id)
        if model is not None:
            self._session.delete(model)
            self._session.flush()

    def list_all(self, limit: int = 100, offset: int = 0) -> list[Watchlist]:
        models = (
            self._session.query(WatchlistModel)
            .order_by(WatchlistModel.id)
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [_model_to_watchlist(m) for m in models]

    def exists_by_name(self, name: str) -> bool:
        return (
            self._session.query(WatchlistModel).filter_by(name=name).first() is not None
        )

    # ── Items ─────────────────────────────────────────────────────────

    def add_item(self, item: WatchlistItem) -> None:
        model = WatchlistItemModel(
            watchlist_id=item.watchlist_id,
            ticker=item.ticker,
            added_at=item.added_at,
            notes=item.notes,
        )
        self._session.add(model)
        self._session.flush()

    def remove_item(self, watchlist_id: int, ticker: str) -> None:
        item = (
            self._session.query(WatchlistItemModel)
            .filter_by(watchlist_id=watchlist_id, ticker=ticker)
            .first()
        )
        if item is not None:
            self._session.delete(item)
            self._session.flush()

    def get_items(self, watchlist_id: int) -> list[WatchlistItem]:
        models = (
            self._session.query(WatchlistItemModel)
            .filter_by(watchlist_id=watchlist_id)
            .all()
        )
        return [_item_model_to_entity(m) for m in models]

    def update_item(self, item: WatchlistItem) -> None:
        model = (
            self._session.query(WatchlistItemModel)
            .filter_by(watchlist_id=item.watchlist_id, ticker=item.ticker)
            .first()
        )
        if model is None:
            raise ValueError(
                f"Item '{item.ticker}' not found in watchlist {item.watchlist_id}"
            )
        model.notes = item.notes
        self._session.flush()


# ── Mappers ──────────────────────────────────────────────────────────────


def _model_to_watchlist(model: WatchlistModel) -> Watchlist:
    return Watchlist(
        id=model.id,
        name=model.name,
        description=model.description or "",
        created_at=model.created_at,
        updated_at=model.updated_at or model.created_at,
        tickers=[_item_model_to_entity(i) for i in (model.items or [])],
    )


def _watchlist_to_model(wl: Watchlist) -> WatchlistModel:
    return WatchlistModel(
        name=wl.name,
        description=wl.description,
        created_at=wl.created_at,
        updated_at=wl.updated_at,
    )


def _item_model_to_entity(model: WatchlistItemModel) -> WatchlistItem:
    return WatchlistItem(
        id=model.id,
        watchlist_id=model.watchlist_id,
        ticker=model.ticker,
        added_at=model.added_at,
        notes=model.notes or "",
    )
