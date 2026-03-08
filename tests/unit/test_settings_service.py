# tests/unit/test_settings_service.py
"""Tests for SettingsService orchestration (MEU-18)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional
from unittest.mock import MagicMock

import pytest

from zorivest_core.domain.settings import SETTINGS_REGISTRY
from zorivest_core.domain.settings_cache import SettingsCache
from zorivest_core.domain.settings_resolver import ResolvedSetting, SettingsResolver
from zorivest_core.domain.settings_validator import (
    SettingsValidationError,
    SettingsValidator,
)
from zorivest_core.services.settings_service import SettingsService


@dataclass
class FakeRow:
    key: str
    value: str


class FakeSettingsRepo:
    def __init__(self) -> None:
        self._data: dict[str, FakeRow] = {}

    def get(self, key: str) -> Optional[FakeRow]:
        return self._data.get(key)

    def get_all(self) -> list[FakeRow]:
        return list(self._data.values())

    def bulk_upsert(self, settings: dict[str, Any]) -> None:
        for k, v in settings.items():
            self._data[k] = FakeRow(key=k, value=str(v))

    def delete(self, key: str) -> None:
        self._data.pop(key, None)


class FakeAppDefaultsRepo:
    def __init__(self) -> None:
        self._data: dict[str, FakeRow] = {}

    def get(self, key: str) -> Optional[FakeRow]:
        return self._data.get(key)

    def get_all(self) -> list[FakeRow]:
        return list(self._data.values())


class FakeUoW:
    def __init__(self) -> None:
        self.settings = FakeSettingsRepo()
        self.app_defaults = FakeAppDefaultsRepo()
        self._committed = False

    def commit(self) -> None:
        self._committed = True

    def rollback(self) -> None:
        pass

    def __enter__(self) -> FakeUoW:
        return self

    def __exit__(self, *args: object) -> None:
        pass


class TestServiceGet:
    """get() uses cache first, then resolves from DB."""

    def test_get_from_cache(self) -> None:
        uow = FakeUoW()
        cache = SettingsCache(ttl_seconds=300)
        cache.populate({
            "ui.theme": ResolvedSetting(key="ui.theme", value="dark", source="user", value_type="str")
        })
        service = SettingsService(uow=uow, cache=cache)
        result = service.get("ui.theme")
        assert result is not None
        assert result.value == "dark"

    def test_get_from_db_on_cache_miss(self) -> None:
        uow = FakeUoW()
        uow.app_defaults._data["ui.theme"] = FakeRow(key="ui.theme", value="dark")
        service = SettingsService(uow=uow, cache=SettingsCache(ttl_seconds=300))
        result = service.get("ui.theme")
        assert result is not None
        assert result.value == "dark"
        assert result.source == "default"

    def test_get_hardcoded_fallback(self) -> None:
        uow = FakeUoW()
        service = SettingsService(uow=uow, cache=SettingsCache(ttl_seconds=300))
        result = service.get("ui.theme")
        assert result is not None
        assert result.value == "dark"
        assert result.source == "hardcoded"


class TestServiceBulkUpsert:
    """bulk_upsert validates then writes."""

    def test_valid_upsert_commits(self) -> None:
        uow = FakeUoW()
        service = SettingsService(uow=uow, cache=SettingsCache(ttl_seconds=300))
        result = service.bulk_upsert({"ui.theme": "light"})
        assert result["status"] == "updated"
        assert result["count"] == 1
        assert uow._committed

    def test_invalid_upsert_raises(self) -> None:
        uow = FakeUoW()
        service = SettingsService(uow=uow, cache=SettingsCache(ttl_seconds=300))
        with pytest.raises(SettingsValidationError):
            service.bulk_upsert({"ui.theme": "neon"})

    def test_upsert_invalidates_cache(self) -> None:
        uow = FakeUoW()
        cache = SettingsCache(ttl_seconds=300)
        cache.populate({
            "ui.theme": ResolvedSetting(key="ui.theme", value="dark", source="user", value_type="str")
        })
        service = SettingsService(uow=uow, cache=cache)
        service.bulk_upsert({"ui.theme": "light"})
        assert cache.get("ui.theme") is None  # Cache was invalidated


class TestServiceResetToDefault:
    """reset_to_default removes user override."""

    def test_reset_deletes_and_invalidates(self) -> None:
        uow = FakeUoW()
        uow.settings._data["ui.theme"] = FakeRow(key="ui.theme", value="light")
        cache = SettingsCache(ttl_seconds=300)
        cache.populate({
            "ui.theme": ResolvedSetting(key="ui.theme", value="light", source="user", value_type="str")
        })
        service = SettingsService(uow=uow, cache=cache)
        service.reset_to_default("ui.theme")
        assert uow.settings.get("ui.theme") is None
        assert cache.get("ui.theme") is None
        assert uow._committed


class TestServiceGetAllResolved:
    """get_all_resolved uses cache or resolves all from DB."""

    def test_get_all_from_cache(self) -> None:
        uow = FakeUoW()
        cache = SettingsCache(ttl_seconds=300)
        data = {
            "ui.theme": ResolvedSetting(key="ui.theme", value="dark", source="user", value_type="str"),
        }
        cache.populate(data)
        service = SettingsService(uow=uow, cache=cache)
        result = service.get_all_resolved()
        assert "ui.theme" in result

    def test_get_all_from_db_populates_cache(self) -> None:
        uow = FakeUoW()
        cache = SettingsCache(ttl_seconds=300)
        service = SettingsService(uow=uow, cache=cache)
        result = service.get_all_resolved()
        # Should resolve all 24 registry keys
        assert len(result) == 24
        # Cache should now be populated
        assert cache.get_all() is not None


class TestServiceGetAll:
    """get_all() returns raw unresolved rows."""

    def test_get_all_returns_raw_rows(self) -> None:
        uow = FakeUoW()
        uow.settings._data["ui.theme"] = FakeRow(key="ui.theme", value="dark")
        uow.settings._data["data.sync_interval_minutes"] = FakeRow(
            key="data.sync_interval_minutes", value="15"
        )
        service = SettingsService(uow=uow)
        rows = service.get_all()
        assert len(rows) == 2
        keys = {r.key for r in rows}
        assert keys == {"ui.theme", "data.sync_interval_minutes"}

    def test_get_all_empty(self) -> None:
        uow = FakeUoW()
        service = SettingsService(uow=uow)
        rows = service.get_all()
        assert rows == []
