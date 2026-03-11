# tests/unit/test_settings_resolver.py
"""Tests for SettingsResolver three-tier resolution (MEU-18)."""

from __future__ import annotations

import pytest

from zorivest_core.domain.settings_resolver import ResolvedSetting, SettingsResolver


class TestThreeTierResolution:
    """Verify user → default → hardcoded resolution chain."""

    def setup_method(self) -> None:
        self.resolver = SettingsResolver()

    def test_user_value_wins(self) -> None:
        result = self.resolver.resolve("ui.theme", user_value="light", default_value="dark")
        assert result.value == "light"
        assert result.source == "user"

    def test_default_value_when_no_user(self) -> None:
        result = self.resolver.resolve("ui.theme", user_value=None, default_value="dark")
        assert result.value == "dark"
        assert result.source == "default"

    def test_hardcoded_fallback(self) -> None:
        result = self.resolver.resolve("ui.theme", user_value=None, default_value=None)
        assert result.value == "dark"
        assert result.source == "hardcoded"

    def test_unknown_key_raises(self) -> None:
        with pytest.raises(KeyError, match="Unknown setting key"):
            self.resolver.resolve("nonexistent.key", None, None)


class TestTypeParsing:
    """Verify _parse correctly coerces types."""

    def test_parse_bool_true(self) -> None:
        assert SettingsResolver._parse("true", "bool") is True
        assert SettingsResolver._parse("1", "bool") is True
        assert SettingsResolver._parse("yes", "bool") is True

    def test_parse_bool_false(self) -> None:
        assert SettingsResolver._parse("false", "bool") is False
        assert SettingsResolver._parse("0", "bool") is False

    def test_parse_int(self) -> None:
        assert SettingsResolver._parse("42", "int") == 42

    def test_parse_float(self) -> None:
        assert SettingsResolver._parse("3.14", "float") == pytest.approx(3.14)

    def test_parse_str(self) -> None:
        assert SettingsResolver._parse("hello", "str") == "hello"

    def test_parse_json(self) -> None:
        result = SettingsResolver._parse('{"a": 1}', "json")
        assert result == {"a": 1}

    def test_parse_bool_invalid(self) -> None:
        with pytest.raises(ValueError, match="Invalid bool value"):
            SettingsResolver._parse("maybe", "bool")


class TestExportability:
    """Verify is_exportable respects sensitivity and exportable flags."""

    def setup_method(self) -> None:
        self.resolver = SettingsResolver()

    def test_non_sensitive_exportable(self) -> None:
        assert self.resolver.is_exportable("ui.theme") is True

    def test_sensitive_not_exportable(self) -> None:
        assert self.resolver.is_exportable("ui.activePage") is False

    def test_unknown_key_not_exportable(self) -> None:
        assert self.resolver.is_exportable("nonexistent") is False


class TestResolvedSettingDataclass:
    """Verify ResolvedSetting structure."""

    def test_resolved_setting_fields(self) -> None:
        rs = ResolvedSetting(key="k", value="v", source="user", value_type="str")
        assert rs.key == "k"
        assert rs.value == "v"
        assert rs.source == "user"
        assert rs.value_type == "str"
