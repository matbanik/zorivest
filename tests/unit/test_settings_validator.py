# tests/unit/test_settings_validator.py
"""Tests for SettingsValidator three-stage pipeline (MEU-18)."""

from __future__ import annotations


from zorivest_core.domain.settings import SETTINGS_REGISTRY
from zorivest_core.domain.settings_validator import (
    SettingsValidationError,
    SettingsValidator,
    ValidationResult,
)


class TestTypeValidation:
    """Stage 1: type check."""

    def setup_method(self) -> None:
        self.validator = SettingsValidator(SETTINGS_REGISTRY)

    def test_valid_bool(self) -> None:
        result = self.validator.validate("dialog.confirm_delete", "true")
        assert result.valid

    def test_invalid_bool(self) -> None:
        result = self.validator.validate("dialog.confirm_delete", "maybe")
        assert not result.valid
        assert len(result.errors) >= 1
        assert result.key == "dialog.confirm_delete"
        assert result.raw_value == "maybe"
        assert any("Cannot parse" in e for e in result.errors)

    def test_valid_int(self) -> None:
        result = self.validator.validate("logging.rotation_mb", "10")
        assert result.valid

    def test_invalid_int(self) -> None:
        result = self.validator.validate("logging.rotation_mb", "abc")
        assert not result.valid
        assert len(result.errors) >= 1
        assert result.key == "logging.rotation_mb"


class TestFormatValidation:
    """Stage 2: format checks (enums, ranges, length)."""

    def setup_method(self) -> None:
        self.validator = SettingsValidator(SETTINGS_REGISTRY)

    def test_allowed_values_pass(self) -> None:
        result = self.validator.validate("ui.theme", "dark")
        assert result.valid

    def test_allowed_values_reject(self) -> None:
        result = self.validator.validate("ui.theme", "neon")
        assert not result.valid
        assert len(result.errors) >= 1
        assert result.key == "ui.theme"
        assert result.raw_value == "neon"
        assert any("not in allowed values" in e for e in result.errors)

    def test_min_value_reject(self) -> None:
        result = self.validator.validate("backup.auto_interval_seconds", "30")
        assert not result.valid
        assert len(result.errors) >= 1
        assert result.key == "backup.auto_interval_seconds"
        assert any("below minimum" in e for e in result.errors)

    def test_max_value_reject(self) -> None:
        result = self.validator.validate("backup.auto_interval_seconds", "100000")
        assert not result.valid
        assert len(result.errors) >= 1
        assert result.key == "backup.auto_interval_seconds"
        assert any("above maximum" in e for e in result.errors)

    def test_string_length_reject(self) -> None:
        result = self.validator.validate("ui.activePage", "x" * 300)
        assert not result.valid
        assert len(result.errors) >= 1
        assert result.key == "ui.activePage"
        assert any("exceeds max" in e for e in result.errors)

    def test_log_level_allowed(self) -> None:
        result = self.validator.validate("logging.trades.level", "DEBUG")
        assert result.valid

    def test_log_level_rejected(self) -> None:
        result = self.validator.validate("logging.trades.level", "VERBOSE")
        assert not result.valid
        assert len(result.errors) >= 1
        assert result.key == "logging.trades.level"


class TestSecurityValidation:
    """Stage 3: security checks."""

    def setup_method(self) -> None:
        self.validator = SettingsValidator(SETTINGS_REGISTRY)

    def test_path_traversal_rejected(self) -> None:
        result = self.validator.validate("ui.activePage", "../../etc/passwd")
        assert not result.valid
        assert len(result.errors) >= 1
        assert result.key == "ui.activePage"
        assert any("path traversal" in e for e in result.errors)

    def test_sql_injection_rejected(self) -> None:
        result = self.validator.validate("ui.activePage", "'; DROP TABLE users;--")
        assert not result.valid
        assert len(result.errors) >= 1
        assert result.key == "ui.activePage"
        assert any("SQL injection" in e for e in result.errors)

    def test_script_injection_rejected(self) -> None:
        result = self.validator.validate("ui.activePage", '<script>alert("xss")</script>')
        assert not result.valid
        assert len(result.errors) >= 1
        assert result.key == "ui.activePage"
        assert any("script injection" in e for e in result.errors)


class TestDynamicKeyResolution:
    """Glob pattern matching for dynamic keys."""

    def setup_method(self) -> None:
        self.validator = SettingsValidator(SETTINGS_REGISTRY)

    def test_dynamic_panel_key_resolves(self) -> None:
        result = self.validator.validate("ui.panel.screenshot.collapsed", "true")
        assert result.valid

    def test_unknown_key_rejected(self) -> None:
        result = self.validator.validate("totally.unknown.key", "value")
        assert not result.valid
        assert len(result.errors) >= 1
        assert result.key == "totally.unknown.key"
        assert any("Unknown setting" in e for e in result.errors)


class TestBulkValidation:
    """validate_bulk returns errors per key."""

    def setup_method(self) -> None:
        self.validator = SettingsValidator(SETTINGS_REGISTRY)

    def test_bulk_all_valid(self) -> None:
        errors = self.validator.validate_bulk({"ui.theme": "dark", "logging.rotation_mb": "10"})
        assert errors == {}

    def test_bulk_some_invalid(self) -> None:
        errors = self.validator.validate_bulk({"ui.theme": "neon", "logging.rotation_mb": "10"})
        assert "ui.theme" in errors
        assert len(errors["ui.theme"]) >= 1
        assert "logging.rotation_mb" not in errors


class TestValidationResult:
    """ValidationResult structure."""

    def test_valid_result(self) -> None:
        vr = ValidationResult(valid=True, key="k", raw_value="v")
        assert vr.valid
        assert vr.errors == []

    def test_invalid_result(self) -> None:
        vr = ValidationResult(valid=False, errors=["bad"], key="k", raw_value="v")
        assert not vr.valid
        assert len(vr.errors) == 1
        assert vr.key == "k"
        assert vr.raw_value == "v"
        assert "bad" in vr.errors


class TestSettingsValidationError:
    """SettingsValidationError carries per-key details."""

    def test_error_attributes(self) -> None:
        err = SettingsValidationError({"key1": ["err1"], "key2": ["err2"]})
        assert len(err.per_key_errors) == 2
        assert "2 key(s)" in str(err)
