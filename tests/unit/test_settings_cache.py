# tests/unit/test_settings_cache.py
"""Tests for SettingsCache TTL and thread-safety (MEU-18)."""

from __future__ import annotations


from zorivest_core.domain.settings_cache import SettingsCache
from zorivest_core.domain.settings_resolver import ResolvedSetting


def _make_resolved(key: str = "ui.theme", value: str = "dark") -> ResolvedSetting:
    return ResolvedSetting(key=key, value=value, source="user", value_type="str")


class TestCacheBasics:
    """Basic get/populate/invalidate."""

    def test_empty_cache_returns_none(self) -> None:
        cache = SettingsCache()
        assert cache.get("ui.theme") is None

    def test_populate_and_get(self) -> None:
        cache = SettingsCache(ttl_seconds=60)
        cache.populate({"ui.theme": _make_resolved()})
        result = cache.get("ui.theme")
        assert result is not None
        assert result.value == "dark"

    def test_get_all_returns_copy(self) -> None:
        cache = SettingsCache(ttl_seconds=60)
        data = {"ui.theme": _make_resolved()}
        cache.populate(data)
        all_items = cache.get_all()
        assert all_items is not None
        assert "ui.theme" in all_items
        # Verify it's a copy
        all_items["new_key"] = _make_resolved("new_key")
        assert cache.get("new_key") is None

    def test_invalidate_clears_cache(self) -> None:
        cache = SettingsCache(ttl_seconds=60)
        cache.populate({"ui.theme": _make_resolved()})
        cache.invalidate()
        assert cache.get("ui.theme") is None
        assert cache.get_all() is None


class TestCacheTTL:
    """TTL-based staleness."""

    def test_stale_cache_returns_none(self) -> None:
        cache = SettingsCache(ttl_seconds=1)
        cache.populate({"ui.theme": _make_resolved()})
        # Simulate staleness by setting loaded_at far in the past
        cache._loaded_at = 0.0
        assert cache.get("ui.theme") is None
        # Value: also verify get_all returns None when stale
        assert cache.get_all() is None

    def test_fresh_cache_returns_value(self) -> None:
        cache = SettingsCache(ttl_seconds=300)
        cache.populate({"ui.theme": _make_resolved()})
        result = cache.get("ui.theme")
        assert result is not None
        # Value: verify the actual resolved value
        assert result.value == "dark"
        assert result.source == "user"
        assert result.key == "ui.theme"


class TestCacheEmpty:
    """Edge cases."""

    def test_get_all_empty_after_populate_empty(self) -> None:
        cache = SettingsCache(ttl_seconds=60)
        cache.populate({})
        assert cache.get_all() is None  # Empty cache returns None
