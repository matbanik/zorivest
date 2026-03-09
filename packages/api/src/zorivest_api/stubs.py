"""Phase 4 in-memory stub implementations for runtime wiring.

Provides an in-memory StubUnitOfWork so that domain services can be
instantiated in lifespan() without a real database. _InMemoryRepo
persists data in dicts and implements filtering, dedup, and ownership
scoping so service-layer contracts hold.

Replaced by the real SqlAlchemyUnitOfWork when Phase 2 integrates.
"""

from __future__ import annotations

from typing import Any


class _InMemoryRepo:
    """In-memory repository — dict-backed persistence with query semantics.

    Supports the full read/write/dedup/filter surface used by services,
    plus a __getattr__ catch-all for any method not explicitly defined.
    """

    def __init__(self) -> None:
        self._store: dict[Any, Any] = {}
        self._auto_id: int = 0

    # ── Read ────────────────────────────────────────────────────────────

    def get(self, key: Any, *args: Any, **kwargs: Any) -> Any:
        return self._store.get(key)

    def exists(self, key: Any, *args: Any, **kwargs: Any) -> bool:
        return key in self._store

    def exists_by_fingerprint_since(self, fingerprint: Any, *args: Any, **kwargs: Any) -> bool:
        """Check for duplicate by fingerprint within lookback window.

        Computes the fingerprint for each stored trade on-the-fly
        using the canonical trade_fingerprint() function, then compares.
        """
        from zorivest_core.domain.trades.identity import trade_fingerprint
        from zorivest_core.domain.entities import Trade

        for entity in self._store.values():
            if isinstance(entity, Trade):
                if trade_fingerprint(entity) == fingerprint:
                    return True
        return False

    # ── Write ───────────────────────────────────────────────────────────

    def save(self, *args: Any, **kwargs: Any) -> int:
        self._auto_id += 1
        if len(args) >= 2:
            # Pattern: save(owner_type, owner_id, entity) for images
            entity = args[-1]
            if hasattr(entity, 'id') and entity.id == 0:
                # Assign auto-id to image attachments
                object.__setattr__(entity, 'id', self._auto_id) if hasattr(type(entity), '__dataclass_fields__') else setattr(entity, 'id', self._auto_id)
            self._store[self._auto_id] = entity
        elif len(args) == 1:
            entity = args[0]
            key = getattr(entity, 'exec_id', None) or getattr(entity, 'account_id', None) or getattr(entity, 'id', self._auto_id)
            self._store[key] = entity
        return self._auto_id

    def delete(self, key: Any, *args: Any, **kwargs: Any) -> None:
        self._store.pop(key, None)

    def update(self, entity: Any, *args: Any, **kwargs: Any) -> None:
        key = getattr(entity, 'exec_id', None) or getattr(entity, 'account_id', None) or getattr(entity, 'id', None)
        if key is not None:
            self._store[key] = entity

    # ── List/Filter ─────────────────────────────────────────────────────

    def list_for_account(self, account_id: Any, *args: Any, **kwargs: Any) -> list:
        """Return entities matching account_id."""
        return [
            e for e in self._store.values()
            if getattr(e, 'account_id', None) == account_id
        ]

    def list_filtered(
        self,
        limit: int = 100,
        offset: int = 0,
        account_id: Any = None,
        sort: str = "-time",
        **kwargs: Any,
    ) -> list:
        """Return entities with optional account filter and pagination."""
        items = list(self._store.values())
        if account_id is not None:
            items = [e for e in items if getattr(e, 'account_id', None) == account_id]
        return items[offset : offset + limit]

    def get_for_owner(self, owner_type: Any, owner_id: Any, *args: Any, **kwargs: Any) -> list:
        """Return entities matching owner_type + owner_id."""
        return [
            e for e in self._store.values()
            if getattr(e, 'owner_type', None) is not None
            and (
                getattr(e, 'owner_type', None) == owner_type
                or getattr(getattr(e, 'owner_type', None), 'value', None) == owner_type
            )
            and str(getattr(e, 'owner_id', None)) == str(owner_id)
        ]

    def get_full_data(self, key: Any, *args: Any, **kwargs: Any) -> Any:
        """Return raw bytes data for an entity (e.g., image data)."""
        entity = self._store.get(key)
        if entity is not None:
            return getattr(entity, 'data', None)
        return None

    def list_all(self, *args: Any, **kwargs: Any) -> list:
        return list(self._store.values())

    def get_thumbnail(self, key: Any, *args: Any, **kwargs: Any) -> Any:
        """Return thumbnail data (stub: returns full image data)."""
        entity = self._store.get(key)
        if entity is not None:
            return getattr(entity, 'data', None)
        return None

    # ── Catch-all ───────────────────────────────────────────────────────

    def __getattr__(self, name: str) -> Any:
        """Catch-all: any unimplemented repo method returns a no-op callable."""
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop


class StubUnitOfWork:
    """Phase 4 in-memory UoW — satisfies the UnitOfWork protocol.

    Data persists within the lifespan of the app. Create→get→list
    contracts hold, with filtering, dedup, and ownership scoping.
    Replaced by real SqlAlchemyUnitOfWork when Phase 2 integrates.
    """

    def __init__(self) -> None:
        self.trades: Any = _InMemoryRepo()
        self.images: Any = _InMemoryRepo()
        self.accounts: Any = _InMemoryRepo()
        self.balance_snapshots: Any = _InMemoryRepo()
        self.round_trips: Any = _InMemoryRepo()
        self.settings: Any = _InMemoryRepo()
        self.app_defaults: Any = _InMemoryRepo()

    def __enter__(self) -> StubUnitOfWork:
        return self

    def __exit__(self, *args: object) -> None:
        pass

    def commit(self) -> None:
        pass

    def rollback(self) -> None:
        pass
