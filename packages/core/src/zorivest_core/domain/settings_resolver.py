# packages/core/src/zorivest_core/domain/settings_resolver.py
"""Three-tier settings resolver: user override → app default → hardcoded fallback.

Source: 02a-backup-restore.md §2A.2

Pure domain logic — no I/O. Receives data from the service layer.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Optional

from zorivest_core.domain.settings import SETTINGS_REGISTRY, Sensitivity, SettingSpec


@dataclass
class ResolvedSetting:
    """A resolved setting value with its source for UI rendering."""

    key: str
    value: Any
    source: str  # "user" | "default" | "hardcoded"
    value_type: str


class SettingsResolver:
    """Three-tier setting resolution: user override → app default → hardcoded fallback.

    Pure domain logic — no I/O. Receives data from service layer.
    """

    def __init__(self, registry: dict[str, SettingSpec] | None = None) -> None:
        self._registry = registry or SETTINGS_REGISTRY

    def resolve(
        self,
        key: str,
        user_value: Optional[str],
        default_value: Optional[str],
    ) -> ResolvedSetting:
        """Resolve a single setting through the three-tier chain."""
        spec = self._registry.get(key)
        if spec is None:
            raise KeyError(f"Unknown setting key: {key}")

        if user_value is not None:
            return ResolvedSetting(
                key=key,
                value=self._parse(user_value, spec.value_type),
                source="user",
                value_type=spec.value_type,
            )

        if default_value is not None:
            return ResolvedSetting(
                key=key,
                value=self._parse(default_value, spec.value_type),
                source="default",
                value_type=spec.value_type,
            )

        return ResolvedSetting(
            key=key,
            value=spec.hardcoded_default,
            source="hardcoded",
            value_type=spec.value_type,
        )

    def is_exportable(self, key: str) -> bool:
        """Check if a setting is safe to include in JSON config export."""
        spec = self._registry.get(key)
        return (
            spec is not None
            and spec.exportable
            and spec.sensitivity == Sensitivity.NON_SENSITIVE
        )

    @staticmethod
    def _parse(raw: str, value_type: str) -> Any:
        """Parse a raw string value into the correct Python type."""
        if value_type == "bool":
            lower = raw.lower()
            if lower in ("true", "1", "yes"):
                return True
            if lower in ("false", "0", "no"):
                return False
            raise ValueError(
                f"Invalid bool value: '{raw}' (expected true/false/1/0/yes/no)"
            )
        if value_type == "int":
            return int(raw)
        if value_type == "float":
            return float(raw)
        if value_type == "json":
            return json.loads(raw)
        return raw  # str
