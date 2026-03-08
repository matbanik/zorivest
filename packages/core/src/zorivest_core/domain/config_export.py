# packages/core/src/zorivest_core/domain/config_export.py
"""ConfigExportService — JSON config export/import with security filtering.

Source: 02a-backup-restore.md §2A.5

Responsibilities:
- Build export dict with only portable (exportable + non-sensitive) settings
- Validate import data: categorize keys as accepted, rejected, or unknown
- Symmetric _is_portable() predicate for both export and import filtering
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from zorivest_core.domain.settings import SETTINGS_REGISTRY, Sensitivity, SettingSpec

# Export schema version — bump when export format changes
CONFIG_VERSION = 1
APP_VERSION = "0.1.0"


@dataclass(frozen=True)
class ImportValidation:
    """Result of validating import data against the settings registry.

    accepted — keys that are portable and can be safely imported
    rejected — keys that exist in registry but are not portable (sensitive/non-exportable)
    unknown  — keys that don't exist in the registry at all
    """

    accepted: list[str] = field(default_factory=list)
    rejected: list[str] = field(default_factory=list)
    unknown: list[str] = field(default_factory=list)


class ConfigExportService:
    """JSON config export/import with security-aware filtering.

    Uses the _is_portable() predicate symmetrically for both
    export (allowlist) and import (validation) operations.

    Args:
        registry: Settings registry to use. Defaults to SETTINGS_REGISTRY.
    """

    def __init__(
        self,
        registry: dict[str, SettingSpec] | None = None,
    ) -> None:
        self._registry = registry or SETTINGS_REGISTRY

    def build_export(
        self,
        resolved_values: dict[str, Any],
    ) -> dict[str, Any]:
        """Build a config export dict containing only portable settings.

        Args:
            resolved_values: Mapping of setting key → resolved value.
                Only portable keys will be included in the export.

        Returns:
            Dict with config_version, app_version, created_at, and
            settings containing only exportable, non-sensitive key/value pairs.
        """
        portable_settings: dict[str, Any] = {}
        for key, value in resolved_values.items():
            if self._is_portable(key):
                portable_settings[key] = value

        return {
            "config_version": CONFIG_VERSION,
            "app_version": APP_VERSION,
            "created_at": datetime.now(tz=timezone.utc).isoformat(),
            "settings": portable_settings,
        }

    def validate_import(
        self,
        import_data: dict[str, Any],
    ) -> ImportValidation:
        """Validate import data by categorizing setting keys.

        Expects the export-shape payload: ``{"config_version": ...,
        "settings": {key: value, ...}}``.  Iterates only the ``settings``
        sub-dict so that ``validate_import(build_export(...))`` works.

        Args:
            import_data: Config export payload (must contain a ``settings`` key).

        Returns:
            ImportValidation with accepted, rejected, and unknown lists.
        """
        settings = import_data.get("settings", {})
        if not isinstance(settings, dict):
            settings = {}

        accepted: list[str] = []
        rejected: list[str] = []
        unknown: list[str] = []

        for key in settings:
            if key not in self._registry:
                unknown.append(key)
            elif self._is_portable(key):
                accepted.append(key)
            else:
                rejected.append(key)

        return ImportValidation(
            accepted=accepted,
            rejected=rejected,
            unknown=unknown,
        )

    def _is_portable(self, key: str) -> bool:
        """Check if a setting key is portable (safe for export/import).

        A setting is portable if and only if:
        1. It exists in the registry
        2. It is marked as exportable
        3. Its sensitivity is NON_SENSITIVE

        This predicate is used symmetrically by both build_export()
        and validate_import() to enforce consistent security filtering.
        """
        spec = self._registry.get(key)
        return (
            spec is not None
            and spec.exportable
            and spec.sensitivity == Sensitivity.NON_SENSITIVE
        )
