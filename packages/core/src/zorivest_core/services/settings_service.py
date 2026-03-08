# packages/core/src/zorivest_core/services/settings_service.py
"""SettingsService — orchestrates settings I/O with validation and caching.

Source: 02a-backup-restore.md §2A.2d
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from zorivest_core.domain.settings import SETTINGS_REGISTRY
from zorivest_core.domain.settings_cache import SettingsCache
from zorivest_core.domain.settings_resolver import ResolvedSetting, SettingsResolver
from zorivest_core.domain.settings_validator import (
    SettingsValidationError,
    SettingsValidator,
)

if TYPE_CHECKING:
    from zorivest_core.application.ports import UnitOfWork


class SettingsService:
    """Orchestrates settings I/O with validation and caching."""

    def __init__(
        self,
        uow: UnitOfWork,
        resolver: SettingsResolver | None = None,
        validator: SettingsValidator | None = None,
        cache: SettingsCache | None = None,
    ) -> None:
        self._uow = uow
        self._resolver = resolver or SettingsResolver()
        self._validator = validator or SettingsValidator(SETTINGS_REGISTRY)
        self._cache = cache or SettingsCache()

    def get(self, key: str) -> Optional[ResolvedSetting]:
        """Read a single setting. Uses cache when available."""
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        return self._resolve_from_db(key)

    def get_all(self) -> list[Any]:
        """Return all raw user setting rows (unresolved)."""
        return self._uow.settings.get_all()

    def get_all_resolved(self) -> dict[str, ResolvedSetting]:
        """Bulk read all settings with three-tier resolution."""
        cached = self._cache.get_all()
        if cached is not None:
            return cached
        resolved = self._resolve_all_from_db()
        self._cache.populate(resolved)
        return resolved

    def bulk_upsert(self, settings: dict[str, Any]) -> dict[str, Any]:
        """Validate then write. All-or-nothing on validation failure."""
        errors = self._validator.validate_bulk(settings)
        if errors:
            raise SettingsValidationError(errors)
        self._uow.settings.bulk_upsert(settings)
        self._uow.commit()
        self._cache.invalidate()
        return {"status": "updated", "count": len(settings)}

    def reset_to_default(self, key: str) -> None:
        """Remove user override; value falls through to next tier."""
        self._uow.settings.delete(key)
        self._uow.commit()
        self._cache.invalidate()

    # ── Private helpers ──────────────────────────────────────────

    def _resolve_from_db(self, key: str) -> ResolvedSetting:
        """Resolve single key from DB without cache."""
        user_row = self._uow.settings.get(key)
        default_row = self._uow.app_defaults.get(key)
        return self._resolver.resolve(
            key,
            user_value=user_row.value if user_row else None,
            default_value=default_row.value if default_row else None,
        )

    def _resolve_all_from_db(self) -> dict[str, ResolvedSetting]:
        """Resolve all known keys from DB."""
        user_settings = {s.key: s.value for s in self._uow.settings.get_all()}
        defaults = {d.key: d.value for d in self._uow.app_defaults.get_all()}
        resolved: dict[str, ResolvedSetting] = {}
        for key in self._resolver._registry:
            resolved[key] = self._resolver.resolve(
                key,
                user_value=user_settings.get(key),
                default_value=defaults.get(key),
            )
        return resolved
