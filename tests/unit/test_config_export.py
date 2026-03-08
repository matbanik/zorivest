# tests/unit/test_config_export.py
"""Unit tests for ConfigExportService (MEU-21).

AC-21.1: build_export() returns dict with config_version, app_version, created_at, settings
AC-21.2: build_export() excludes SECRET/SENSITIVE settings
AC-21.3: build_export() excludes non-exportable settings
AC-21.4: validate_import() categorizes into accepted/rejected/unknown
AC-21.5: validate_import() rejects non-portable keys
AC-21.6: Export and import use same _is_portable() predicate
AC-21.7: ImportValidation is a frozen dataclass
"""

from __future__ import annotations

import pytest

from zorivest_core.domain.config_export import (
    ConfigExportService,
    ImportValidation,
)
from zorivest_core.domain.settings import (
    SETTINGS_REGISTRY,
    Sensitivity,
    SettingSpec,
)


# ── Fixtures ─────────────────────────────────────────────────────────────


@pytest.fixture()
def small_registry() -> dict[str, SettingSpec]:
    """A minimal registry with different sensitivity/exportable combos."""
    return {
        "dialog.confirm_delete": SettingSpec(
            key="dialog.confirm_delete",
            value_type="bool",
            hardcoded_default=True,
            category="dialog",
            exportable=True,
            sensitivity=Sensitivity.NON_SENSITIVE,
        ),
        "ui.theme": SettingSpec(
            key="ui.theme",
            value_type="str",
            hardcoded_default="dark",
            category="ui",
            exportable=True,
            sensitivity=Sensitivity.NON_SENSITIVE,
        ),
        "ui.activePage": SettingSpec(
            key="ui.activePage",
            value_type="str",
            hardcoded_default="/",
            category="ui",
            exportable=False,
            sensitivity=Sensitivity.SENSITIVE,
        ),
        "api.key": SettingSpec(
            key="api.key",
            value_type="str",
            hardcoded_default="",
            category="secret",
            exportable=False,
            sensitivity=Sensitivity.SECRET,
        ),
    }


@pytest.fixture()
def service(small_registry: dict[str, SettingSpec]) -> ConfigExportService:
    """ConfigExportService with the small test registry."""
    return ConfigExportService(registry=small_registry)


# ── AC-21.1: build_export structure ──────────────────────────────────────


class TestBuildExport:
    """Tests for build_export()."""

    def test_export_has_required_keys(
        self, service: ConfigExportService
    ) -> None:
        """AC-21.1: Export dict has config_version, app_version, created_at, settings."""
        result = service.build_export(resolved_values={
            "dialog.confirm_delete": True,
            "ui.theme": "dark",
        })

        assert "config_version" in result
        assert "app_version" in result
        assert "created_at" in result
        assert "settings" in result
        assert isinstance(result["settings"], dict)

    def test_export_includes_only_portable_keys(
        self, service: ConfigExportService
    ) -> None:
        """AC-21.1: Only exportable, non-sensitive keys appear in settings."""
        result = service.build_export(resolved_values={
            "dialog.confirm_delete": True,
            "ui.theme": "dark",
            "ui.activePage": "/trades",
            "api.key": "sk-secret",
        })

        exported_keys = set(result["settings"].keys())
        assert "dialog.confirm_delete" in exported_keys
        assert "ui.theme" in exported_keys
        # Sensitive/non-exportable must NOT appear
        assert "ui.activePage" not in exported_keys
        assert "api.key" not in exported_keys

    def test_export_excludes_secret_sensitivity(
        self, service: ConfigExportService
    ) -> None:
        """AC-21.2: SECRET settings never exported."""
        result = service.build_export(resolved_values={
            "api.key": "sk-secret-value",
        })
        assert "api.key" not in result["settings"]

    def test_export_excludes_sensitive(
        self, service: ConfigExportService
    ) -> None:
        """AC-21.2: SENSITIVE settings never exported."""
        result = service.build_export(resolved_values={
            "ui.activePage": "/trades",
        })
        assert "ui.activePage" not in result["settings"]

    def test_export_excludes_non_exportable(
        self, service: ConfigExportService
    ) -> None:
        """AC-21.3: exportable=False settings excluded even if non-sensitive."""
        # Create a spec that's non-sensitive but not exportable
        registry = {
            "internal.flag": SettingSpec(
                key="internal.flag",
                value_type="bool",
                hardcoded_default=False,
                category="internal",
                exportable=False,
                sensitivity=Sensitivity.NON_SENSITIVE,
            ),
        }
        svc = ConfigExportService(registry=registry)
        result = svc.build_export(resolved_values={"internal.flag": False})
        assert "internal.flag" not in result["settings"]

    def test_export_with_real_registry(self) -> None:
        """AC-21.1: Using the real SETTINGS_REGISTRY, no sensitive keys leak."""
        svc = ConfigExportService(registry=SETTINGS_REGISTRY)
        # Use hardcoded defaults for all settings
        resolved = {k: v.hardcoded_default for k, v in SETTINGS_REGISTRY.items()}
        result = svc.build_export(resolved_values=resolved)

        for key in result["settings"]:
            spec = SETTINGS_REGISTRY[key]
            assert spec.exportable is True
            assert spec.sensitivity == Sensitivity.NON_SENSITIVE


# ── AC-21.4 / 21.5: validate_import ─────────────────────────────────────


class TestValidateImport:
    """Tests for validate_import()."""

    def test_accepted_keys(
        self, service: ConfigExportService
    ) -> None:
        """AC-21.4: Portable keys in import data are accepted."""
        result = service.validate_import(
            import_data={"settings": {"dialog.confirm_delete": True, "ui.theme": "light"}}
        )
        assert "dialog.confirm_delete" in result.accepted
        assert "ui.theme" in result.accepted

    def test_rejected_keys(
        self, service: ConfigExportService
    ) -> None:
        """AC-21.5: Non-portable keys are rejected."""
        result = service.validate_import(
            import_data={"settings": {"ui.activePage": "/", "api.key": "hack"}}
        )
        assert "ui.activePage" in result.rejected
        assert "api.key" in result.rejected
        assert len(result.accepted) == 0

    def test_unknown_keys(
        self, service: ConfigExportService
    ) -> None:
        """AC-21.4: Keys not in registry are classified as unknown."""
        result = service.validate_import(
            import_data={"settings": {"nonexistent.setting": 42}}
        )
        assert "nonexistent.setting" in result.unknown
        assert len(result.accepted) == 0
        assert len(result.rejected) == 0

    def test_mixed_categories(
        self, service: ConfigExportService
    ) -> None:
        """AC-21.4: Mix of accepted, rejected, unknown in one import."""
        result = service.validate_import(
            import_data={"settings": {
                "ui.theme": "light",          # accepted
                "api.key": "secret",          # rejected
                "unknown.key": "val",         # unknown
            }}
        )
        assert "ui.theme" in result.accepted
        assert "api.key" in result.rejected
        assert "unknown.key" in result.unknown

    def test_round_trip(
        self, service: ConfigExportService
    ) -> None:
        """Round-trip: validate_import(build_export(...)) returns non-empty accepted."""
        export = service.build_export(resolved_values={
            "dialog.confirm_delete": True,
            "ui.theme": "dark",
        })
        result = service.validate_import(import_data=export)
        assert len(result.accepted) >= 2
        assert "dialog.confirm_delete" in result.accepted
        assert "ui.theme" in result.accepted
        assert len(result.rejected) == 0
        assert len(result.unknown) == 0


# ── AC-21.6: _is_portable symmetry ──────────────────────────────────────


class TestPortableSymmetry:
    """AC-21.6: Export and import use the same _is_portable predicate."""

    def test_is_portable_true_for_exportable_nonsensitive(
        self, service: ConfigExportService
    ) -> None:
        """Portable = exportable AND non-sensitive."""
        assert service._is_portable("dialog.confirm_delete") is True
        assert service._is_portable("ui.theme") is True

    def test_is_portable_false_for_sensitive(
        self, service: ConfigExportService
    ) -> None:
        """SENSITIVE settings are not portable."""
        assert service._is_portable("ui.activePage") is False

    def test_is_portable_false_for_secret(
        self, service: ConfigExportService
    ) -> None:
        """SECRET settings are not portable."""
        assert service._is_portable("api.key") is False

    def test_is_portable_false_for_unknown(
        self, service: ConfigExportService
    ) -> None:
        """Unknown keys are not portable."""
        assert service._is_portable("does.not.exist") is False


# ── AC-21.7: ImportValidation frozen dataclass ───────────────────────────


class TestImportValidation:
    """AC-21.7: ImportValidation is a frozen dataclass."""

    def test_importvalidation_fields(self) -> None:
        """Has accepted, rejected, unknown list fields."""
        iv = ImportValidation(
            accepted=["a"],
            rejected=["b"],
            unknown=["c"],
        )
        assert iv.accepted == ["a"]
        assert iv.rejected == ["b"]
        assert iv.unknown == ["c"]

    def test_importvalidation_frozen(self) -> None:
        """Cannot mutate fields (frozen=True)."""
        iv = ImportValidation(accepted=[], rejected=[], unknown=[])
        with pytest.raises(AttributeError):
            iv.accepted = ["should", "fail"]  # type: ignore[misc]
