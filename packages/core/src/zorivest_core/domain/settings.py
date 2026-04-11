# packages/core/src/zorivest_core/domain/settings.py
"""Settings registry: SettingSpec, Sensitivity enum, and SETTINGS_REGISTRY.

Source: 02a-backup-restore.md §2A.1, §2A.2

Contains:
- Sensitivity enum (NON_SENSITIVE, SENSITIVE, SECRET)
- SettingSpec frozen dataclass (registry entry metadata)
- SETTINGS_REGISTRY dict — canonical list of all 27 known settings
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional


class Sensitivity(Enum):
    """Sensitivity classification for settings export filtering.

    NON_SENSITIVE — safe to include in JSON config exports
    SENSITIVE     — user-specific data, excluded from exports
    SECRET        — API keys, passwords — never exported or logged
    """

    NON_SENSITIVE = "non_sensitive"
    SENSITIVE = "sensitive"
    SECRET = "secret"


@dataclass(frozen=True)
class SettingSpec:
    """Registry entry defining a known setting and its metadata.

    Used by SettingsResolver for three-tier resolution,
    SettingsValidator for constraint enforcement, and
    ConfigExportService for allowlist filtering.
    """

    key: str
    value_type: str  # "str", "int", "float", "bool", "json"
    hardcoded_default: Any  # Safety net for missing DB data
    category: str  # "dialog", "logging", "display", "backup", "ui", "notification"
    exportable: bool = True  # Whether included in JSON config export
    sensitivity: Sensitivity = Sensitivity.NON_SENSITIVE
    validator: Optional[Callable[[Any], bool]] = None
    description: str = ""
    allowed_values: Optional[list[str]] = None  # Enum constraint
    min_value: Optional[float] = None  # Numeric range floor
    max_value: Optional[float] = None  # Numeric range ceiling
    max_length: int = 1024  # String length cap (security)


# ── Canonical Settings Registry ──────────────────────────────────────────
# Source: 02a-backup-restore.md §2A.1 L41-66 (24 entries)
# Validation rules: §2A.1 L75-92


SETTINGS_REGISTRY: dict[str, SettingSpec] = {
    # ── Dialog confirmations (5 entries) ──────────────────────────────────
    "dialog.confirm_delete": SettingSpec(
        key="dialog.confirm_delete",
        value_type="bool",
        hardcoded_default=True,
        category="dialog",
        description="Confirm before deleting trades/records",
    ),
    "dialog.confirm_restore": SettingSpec(
        key="dialog.confirm_restore",
        value_type="bool",
        hardcoded_default=True,
        category="dialog",
        description="Confirm before restoring from backup",
    ),
    "dialog.confirm_clear_data": SettingSpec(
        key="dialog.confirm_clear_data",
        value_type="bool",
        hardcoded_default=True,
        category="dialog",
        description="Confirm before clearing all data",
    ),
    "dialog.confirm_export": SettingSpec(
        key="dialog.confirm_export",
        value_type="bool",
        hardcoded_default=True,
        category="dialog",
        description="Confirm before config export",
    ),
    "dialog.confirm_import": SettingSpec(
        key="dialog.confirm_import",
        value_type="bool",
        hardcoded_default=True,
        category="dialog",
        description="Confirm before config import",
    ),
    # ── Logging (4 entries) ───────────────────────────────────────────────
    "logging.trades.level": SettingSpec(
        key="logging.trades.level",
        value_type="str",
        hardcoded_default="INFO",
        category="logging",
        description="Log level for trade operations",
        allowed_values=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    ),
    "logging.api.level": SettingSpec(
        key="logging.api.level",
        value_type="str",
        hardcoded_default="INFO",
        category="logging",
        description="Log level for REST API",
        allowed_values=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    ),
    "logging.rotation_mb": SettingSpec(
        key="logging.rotation_mb",
        value_type="int",
        hardcoded_default=10,
        category="logging",
        description="Max log file size before rotation (MB)",
        min_value=1,
        max_value=500,
    ),
    "logging.backup_count": SettingSpec(
        key="logging.backup_count",
        value_type="int",
        hardcoded_default=5,
        category="logging",
        description="Number of rotated log files to keep",
        min_value=1,
        max_value=50,
    ),
    # ── Display (3 entries) ───────────────────────────────────────────────
    "display.hide_dollars": SettingSpec(
        key="display.hide_dollars",
        value_type="bool",
        hardcoded_default=False,
        category="display",
        description="Privacy mode — hide dollar amounts",
    ),
    "display.hide_percentages": SettingSpec(
        key="display.hide_percentages",
        value_type="bool",
        hardcoded_default=False,
        category="display",
        description="Privacy mode — hide percentages",
    ),
    "display.percent_mode": SettingSpec(
        key="display.percent_mode",
        value_type="str",
        hardcoded_default="daily",
        category="display",
        description="Percentage display mode",
        allowed_values=["daily", "total"],
    ),
    # ── Backup (4 entries) ────────────────────────────────────────────────
    "backup.auto_interval_seconds": SettingSpec(
        key="backup.auto_interval_seconds",
        value_type="int",
        hardcoded_default=300,
        category="backup",
        description="Automatic backup interval (5 minutes)",
        min_value=60,
        max_value=86400,
    ),
    "backup.auto_change_threshold": SettingSpec(
        key="backup.auto_change_threshold",
        value_type="int",
        hardcoded_default=100,
        category="backup",
        description="Change count that triggers backup",
        min_value=1,
        max_value=10000,
    ),
    "backup.compression_enabled": SettingSpec(
        key="backup.compression_enabled",
        value_type="bool",
        hardcoded_default=True,
        category="backup",
        description="Enable compression for auto backups",
    ),
    "backup.max_age_days": SettingSpec(
        key="backup.max_age_days",
        value_type="int",
        hardcoded_default=90,
        category="backup",
        description="Maximum age before backup is pruned",
        min_value=1,
        max_value=3650,
    ),
    # ── UI (4 entries) ────────────────────────────────────────────────────
    "ui.theme": SettingSpec(
        key="ui.theme",
        value_type="str",
        hardcoded_default="dark",
        category="ui",
        description="Light/dark theme preference",
        allowed_values=["light", "dark"],
    ),
    "ui.activePage": SettingSpec(
        key="ui.activePage",
        value_type="str",
        hardcoded_default="/",
        category="ui",
        description="Last active route",
        sensitivity=Sensitivity.SENSITIVE,
        exportable=False,
        max_length=256,
    ),
    "ui.panel.*.collapsed": SettingSpec(
        key="ui.panel.*.collapsed",
        value_type="bool",
        hardcoded_default=False,
        category="ui",
        description="Panel collapse state (dynamic key)",
        exportable=False,
        sensitivity=Sensitivity.SENSITIVE,
    ),
    "ui.sidebar.width": SettingSpec(
        key="ui.sidebar.width",
        value_type="int",
        hardcoded_default=280,
        category="ui",
        description="Sidebar width in pixels",
        min_value=150,
        max_value=600,
    ),
    "ui.accounts.active": SettingSpec(
        key="ui.accounts.active",
        value_type="str",
        hardcoded_default="",
        category="ui",
        description="Currently selected account UUID (empty if none)",
        sensitivity=Sensitivity.SENSITIVE,
        exportable=False,
        max_length=36,
    ),
    "ui.accounts.mru": SettingSpec(
        key="ui.accounts.mru",
        value_type="json",
        hardcoded_default="[]",
        category="ui",
        description="Most Recently Used account UUIDs (max 3, JSON array)",
        sensitivity=Sensitivity.SENSITIVE,
        exportable=False,
        max_length=256,
    ),
    "ui.watchlist.colorblind_mode": SettingSpec(
        key="ui.watchlist.colorblind_mode",
        value_type="bool",
        hardcoded_default=False,
        category="ui",
        description="Use colorblind-friendly palette for watchlist gain/loss colors",
    ),
    # ── Notifications (4 entries) ─────────────────────────────────────────
    "notification.success.enabled": SettingSpec(
        key="notification.success.enabled",
        value_type="bool",
        hardcoded_default=True,
        category="notification",
        description="Show success toasts",
    ),
    "notification.info.enabled": SettingSpec(
        key="notification.info.enabled",
        value_type="bool",
        hardcoded_default=True,
        category="notification",
        description="Show info toasts",
    ),
    "notification.warning.enabled": SettingSpec(
        key="notification.warning.enabled",
        value_type="bool",
        hardcoded_default=True,
        category="notification",
        description="Show warning toasts",
    ),
    "notification.confirmation.enabled": SettingSpec(
        key="notification.confirmation.enabled",
        value_type="bool",
        hardcoded_default=True,
        category="notification",
        description="Show confirmation dialogs",
    ),
}
