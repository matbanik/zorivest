# Phase 2A: Backup/Restore, Settings Defaults & Config Export

> Part of [Zorivest Build Plan](../BUILD_PLAN.md) | Prerequisites: [Phase 2](02-infrastructure.md) | Outputs: [Phase 3](03-service-layer.md), [Phase 4](04-rest-api.md), [Phase 6](06-gui.md) ([Settings](06f-gui-settings.md))

---

## Goal

Implement three interconnected features: encrypted database backup/restore, application setting defaults with three-tier resolution, and portable JSON config export/import. This phase extends the infrastructure layer with new models and services before the service layer is built.

> **Architecture reference**: See [`_backup-restore-architecture.md`](../_backup-restore-architecture.md) for the full backup/restore architecture (two-manager design, GFS rotation, restore flow).

---

## Step 2A.1: Application Defaults Schema

Add an `AppDefaultModel` table alongside the existing `SettingModel`. Together they form the two-table foundation for three-tier settings resolution.

```python
# packages/infrastructure/src/zorivest_infra/database/models.py  (addition)

class AppDefaultModel(Base):
    """Application-level setting defaults. Seeded from code registry during migration.
    
    Users never write to this table directly — they write to SettingModel (user overrides).
    This table is the source of truth for "Reset to Default" and for showing
    default values in the GUI.
    """
    __tablename__ = "app_defaults"

    key = Column(String, primary_key=True)
    value = Column(Text, nullable=False)
    value_type = Column(String(20), nullable=False)     # "str", "int", "float", "bool", "json"
    category = Column(String(50), nullable=False)        # "dialog", "logging", "display", "backup"
    description = Column(Text, nullable=True)            # Human-readable description for GUI tooltips
    updated_at = Column(DateTime, nullable=False)
```

### Default Settings Registry (Seeded Values)

| Key | Value | Type | Category | Description |
|-----|-------|------|----------|-------------|
| `dialog.confirm_delete` | `true` | bool | dialog | Confirm before deleting trades/records |
| `dialog.confirm_restore` | `true` | bool | dialog | Confirm before restoring from backup |
| `dialog.confirm_clear_data` | `true` | bool | dialog | Confirm before clearing all data |
| `dialog.confirm_export` | `true` | bool | dialog | Confirm before config export |
| `dialog.confirm_import` | `true` | bool | dialog | Confirm before config import |
| `logging.trades.level` | `INFO` | str | logging | Log level for trade operations |
| `logging.api.level` | `INFO` | str | logging | Log level for REST API |
| `logging.rotation_mb` | `10` | int | logging | Max log file size before rotation (MB) |
| `logging.backup_count` | `5` | int | logging | Number of rotated log files to keep |
| `display.hide_dollars` | `false` | bool | display | Privacy mode — hide dollar amounts |
| `display.hide_percentages` | `false` | bool | display | Privacy mode — hide percentages |
| `display.percent_mode` | `daily` | str | display | Percentage display mode |
| `backup.auto_interval_seconds` | `300` | int | backup | Automatic backup interval (5 minutes) |
| `backup.auto_change_threshold` | `100` | int | backup | Change count that triggers backup |
| `backup.compression_enabled` | `true` | bool | backup | Enable gzip compression for auto backups |
| `backup.max_age_days` | `90` | int | backup | Maximum age before backup is pruned |
| `ui.theme` | `dark` | str | ui | Light/dark theme preference |
| `ui.activePage` | `/` | str | ui | Last active route |
| `ui.panel.*.collapsed` | `false` | bool | ui | Panel collapse state (dynamic key — see note below) |
| `ui.sidebar.width` | `280` | int | ui | Sidebar width in pixels |
| `notification.success.enabled` | `true` | bool | notification | Show success toasts |
| `notification.info.enabled` | `true` | bool | notification | Show info toasts |
| `notification.warning.enabled` | `true` | bool | notification | Show warning toasts |
| `notification.confirmation.enabled` | `true` | bool | notification | Show confirmation dialogs |

> [!NOTE]
> **Dynamic keys**: `ui.panel.*.collapsed` uses a wildcard segment (e.g., `ui.panel.screenshot.collapsed`). The validator's `_resolve_spec()` method checks exact match first, then falls back to glob-pattern entries where `*` matches any single segment. This allows open-ended panel names without pre-registering every panel.

### Validation Rules per Setting

Concrete constraints enforced by `SettingsValidator` (see Step 2A.2b). Settings not listed here use type-check only.

| Key Pattern | `allowed_values` | `min_value` | `max_value` | `max_length` | Notes |
|---|---|---|---|---|---|
| `logging.*.level` | `["DEBUG","INFO","WARNING","ERROR","CRITICAL"]` | — | — | — | All 11 feature loggers |
| `logging.rotation_mb` | — | `1` | `500` | — | Positive integer range |
| `logging.backup_count` | — | `1` | `50` | — | Positive integer range |
| `display.percent_mode` | `["daily","total"]` | — | — | — | Enum constraint |
| `display.hide_dollars` | — | — | — | — | Bool type-check only |
| `display.hide_percentages` | — | — | — | — | Bool type-check only |
| `backup.auto_interval_seconds` | — | `60` | `86400` | — | 1 minute to 24 hours |
| `backup.auto_change_threshold` | — | `1` | `10000` | — | Positive integer range |
| `backup.compression_enabled` | — | — | — | — | Bool type-check only |
| `backup.max_age_days` | — | `1` | `3650` | — | 1 day to ~10 years |
| `dialog.*` (all 5) | — | — | — | — | Bool type-check only |
| `ui.theme` | `["light","dark"]` | — | — | — | Enum constraint |
| `ui.activePage` | — | — | — | `256` | Str type-check + security |
| `ui.sidebar.width` | — | `150` | `600` | — | Pixel range |
| `ui.panel.*.collapsed` | — | — | — | — | Bool type-check only (dynamic) |
| `notification.*.enabled` | — | — | — | — | Bool type-check only |

---

## Step 2A.2: Settings Registry & Three-Tier Resolver

### SettingSpec (Domain Layer)

```python
# packages/core/src/zorivest_core/domain/settings.py

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional


class Sensitivity(Enum):
    NON_SENSITIVE = "non_sensitive"      # Safe to export to JSON
    SENSITIVE = "sensitive"              # Contains user-specific data, not exported
    SECRET = "secret"                    # API keys, passwords — never exported


@dataclass(frozen=True)
class SettingSpec:
    """Registry entry defining a known setting and its metadata."""
    key: str
    value_type: str                      # "str", "int", "float", "bool", "json"
    hardcoded_default: Any               # Safety net for missing DB data
    category: str                        # "dialog", "logging", "display", "backup", etc.
    exportable: bool = True              # Whether included in JSON config export
    sensitivity: Sensitivity = Sensitivity.NON_SENSITIVE
    validator: Optional[Callable[[Any], bool]] = None
    description: str = ""
    allowed_values: Optional[list[str]] = None     # Enum constraint (e.g., log levels)
    min_value: Optional[float] = None               # Numeric range floor
    max_value: Optional[float] = None               # Numeric range ceiling
    max_length: int = 1024                           # String length cap (security)
```

### SettingsResolver (Domain Service)

```python
# packages/core/src/zorivest_core/domain/settings_resolver.py

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class ResolvedSetting:
    """A resolved setting value with its source for UI rendering."""
    key: str
    value: Any
    source: str                          # "user" | "default" | "hardcoded"
    value_type: str


class SettingsResolver:
    """Three-tier setting resolution: user override → app default → hardcoded fallback.
    
    Pure domain logic — no I/O. Receives data from service layer.
    """

    def __init__(self, registry: dict[str, "SettingSpec"]):
        self._registry = registry

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
            return ResolvedSetting(key=key, value=self._parse(user_value, spec.value_type),
                                   source="user", value_type=spec.value_type)

        if default_value is not None:
            return ResolvedSetting(key=key, value=self._parse(default_value, spec.value_type),
                                   source="default", value_type=spec.value_type)

        return ResolvedSetting(key=key, value=spec.hardcoded_default,
                               source="hardcoded", value_type=spec.value_type)

    def is_exportable(self, key: str) -> bool:
        """Check if a setting is safe to include in JSON config export."""
        spec = self._registry.get(key)
        return spec is not None and spec.exportable and spec.sensitivity == Sensitivity.NON_SENSITIVE

    @staticmethod
    def _parse(raw: str, value_type: str) -> Any:
        """Parse a raw string value into the correct Python type."""
        if value_type == "bool":
            lower = raw.lower()
            if lower in ("true", "1", "yes"):
                return True
            if lower in ("false", "0", "no"):
                return False
            raise ValueError(f"Invalid bool value: '{raw}' (expected true/false/1/0/yes/no)")
        if value_type == "int":
            return int(raw)
        if value_type == "float":
            return float(raw)
        if value_type == "json":
            import json
            return json.loads(raw)
        return raw  # str
```

### Step 2A.2b: Settings Validator (Domain Service)

Three-stage validation pipeline that runs before any write to `SettingModel`. Pure domain logic — no I/O.

> **Inspired by**: [`_settings-architecture.md`](../_settings-architecture.md) §3 SettingsValidator — multi-level validation with security checks.

```python
# packages/core/src/zorivest_core/domain/settings_validator.py

from dataclasses import dataclass, field
from typing import Any
import re


@dataclass
class ValidationResult:
    """Outcome of validating a single setting value."""
    valid: bool
    errors: list[str] = field(default_factory=list)
    key: str = ""
    raw_value: Any = None


class SettingsValidationError(Exception):
    """Raised when one or more settings fail validation.
    Contains per-key error details for the REST layer to surface as 422."""
    def __init__(self, per_key_errors: dict[str, list[str]]):
        self.per_key_errors = per_key_errors
        super().__init__(f"Validation failed for {len(per_key_errors)} key(s)")


# Security patterns — compiled once at module level
_PATH_TRAVERSAL = re.compile(r"\.\.[\\/]")
_SQL_INJECTION = re.compile(
    r"('\s*;\s*(DROP|ALTER|DELETE|UPDATE|INSERT))"
    r"|(\bOR\b\s+\d+\s*=\s*\d+)"
    r"|(\bUNION\b\s+\bSELECT\b)",
    re.IGNORECASE,
)
_SCRIPT_INJECTION = re.compile(
    r"<\s*script"
    r"|javascript\s*:"
    r"|on(load|error|click|mouseover)\s*=",
    re.IGNORECASE,
)


class SettingsValidator:
    """Three-stage validation pipeline: type → format → security.

    Runs on every PUT /settings write. Pure domain — no I/O.
    Stages run in order; pipeline stops at the first stage that produces errors.
    """

    def __init__(self, registry: dict[str, "SettingSpec"]):
        self._registry = registry

    def validate(self, key: str, raw_value: Any) -> ValidationResult:
        """Run all three stages. Returns on first failing stage."""
        spec = self._resolve_spec(key)
        if spec is None:
            return ValidationResult(valid=False, errors=[f"Unknown setting: {key}"],
                                    key=key, raw_value=raw_value)

    def _resolve_spec(self, key: str) -> Optional["SettingSpec"]:
        """Look up spec by exact key, then fall back to glob patterns (e.g., ui.panel.*.collapsed)."""
        spec = self._registry.get(key)
        if spec is not None:
            return spec
        # Glob fallback: replace middle segments with * and try matching
        parts = key.split(".")
        for i in range(len(parts)):
            pattern_parts = parts[:i] + ["*"] + parts[i+1:]
            pattern_key = ".".join(pattern_parts)
            spec = self._registry.get(pattern_key)
            if spec is not None:
                return spec
        return None

        # Stage 1: Type validation
        type_errors = self._validate_type(raw_value, spec)
        if type_errors:
            return ValidationResult(valid=False, errors=type_errors,
                                    key=key, raw_value=raw_value)

        # Stage 2: Format validation (ranges, enums, custom)
        format_errors = self._validate_format(raw_value, spec)
        if format_errors:
            return ValidationResult(valid=False, errors=format_errors,
                                    key=key, raw_value=raw_value)

        # Stage 3: Security validation
        security_errors = self._validate_security(raw_value, spec)
        return ValidationResult(valid=len(security_errors) == 0,
                                errors=security_errors, key=key, raw_value=raw_value)

    def validate_bulk(self, settings: dict[str, Any]) -> dict[str, list[str]]:
        """Validate multiple settings. Returns dict of key → errors (empty if all valid)."""
        errors = {}
        for key, value in settings.items():
            result = self.validate(key, value)
            if not result.valid:
                errors[key] = result.errors
        return errors

    # ── Stage 1: Type ───────────────────────────────────────────

    @staticmethod
    def _validate_type(raw_value: Any, spec: "SettingSpec") -> list[str]:
        """Verify raw_value can be parsed to spec.value_type."""
        try:
            SettingsResolver._parse(str(raw_value), spec.value_type)
            return []
        except (ValueError, TypeError) as e:
            return [f"Cannot parse '{raw_value}' as {spec.value_type}: {e}"]

    # ── Stage 2: Format ─────────────────────────────────────────

    @staticmethod
    def _validate_format(raw_value: Any, spec: "SettingSpec") -> list[str]:
        """Check allowed_values, numeric ranges, string length, custom validator."""
        errors = []
        str_val = str(raw_value)

        # Enum constraint
        if spec.allowed_values is not None and str_val not in spec.allowed_values:
            errors.append(f"'{str_val}' not in allowed values: {spec.allowed_values}")

        # Numeric range
        if spec.value_type in ("int", "float"):
            try:
                num = float(str_val)
                if spec.min_value is not None and num < spec.min_value:
                    errors.append(f"Value {num} below minimum {spec.min_value}")
                if spec.max_value is not None and num > spec.max_value:
                    errors.append(f"Value {num} above maximum {spec.max_value}")
            except ValueError:
                pass  # Already caught by Stage 1

        # String length cap
        if len(str_val) > spec.max_length:
            errors.append(f"Value length {len(str_val)} exceeds max {spec.max_length}")

        # Custom per-key validator
        if spec.validator is not None and not spec.validator(raw_value):
            errors.append(f"Custom validation failed for '{spec.key}'")

        return errors

    # ── Stage 3: Security ───────────────────────────────────────

    @staticmethod
    def _validate_security(raw_value: Any, spec: "SettingSpec") -> list[str]:
        """Reject path traversal, SQL injection, and script injection."""
        errors = []
        str_val = str(raw_value)

        if _PATH_TRAVERSAL.search(str_val):
            errors.append("Value contains path traversal pattern")
        if _SQL_INJECTION.search(str_val):
            errors.append("Value contains SQL injection pattern")
        if _SCRIPT_INJECTION.search(str_val):
            errors.append("Value contains script injection pattern")

        return errors
```

### Step 2A.2c: Settings Cache (Domain Service)

Thread-safe in-memory read cache with TTL-based staleness protection. Eliminates redundant DB reads for frequently-accessed settings (display flags, logging levels).

> **Inspired by**: [`_settings-architecture.md`](../_settings-architecture.md) §2 DatabaseSettingsManager — in-memory cache with write-through invalidation.

```python
# packages/core/src/zorivest_core/domain/settings_cache.py

import time
from threading import Lock
from typing import Any, Optional


class SettingsCache:
    """Thread-safe in-memory settings cache with TTL expiry.

    Strategy:
    - Populated on startup from get_all_resolved()
    - Invalidated on writes (bulk_upsert, reset_to_default)
    - TTL-based staleness protection (default 60s)
    - Full cache flush on any write (simple strategy; no per-key tracking)
    """

    def __init__(self, ttl_seconds: int = 60):
        self._cache: dict[str, ResolvedSetting] = {}
        self._loaded_at: float = 0.0
        self._ttl = ttl_seconds
        self._lock = Lock()

    def get(self, key: str) -> Optional[ResolvedSetting]:
        """Read from cache. Returns None on cache miss or stale."""
        with self._lock:
            if self._is_stale():
                return None
            return self._cache.get(key)

    def get_all(self) -> Optional[dict[str, ResolvedSetting]]:
        """Return full cache dict, or None if stale/empty."""
        with self._lock:
            if self._is_stale() or not self._cache:
                return None
            return dict(self._cache)

    def populate(self, resolved: dict[str, ResolvedSetting]) -> None:
        """Bulk load resolved settings into cache."""
        with self._lock:
            self._cache = dict(resolved)
            self._loaded_at = time.monotonic()

    def invalidate(self) -> None:
        """Flush entire cache. Called after any write operation."""
        with self._lock:
            self._cache.clear()
            self._loaded_at = 0.0

    def _is_stale(self) -> bool:
        return (time.monotonic() - self._loaded_at) > self._ttl
```

### Step 2A.2d: SettingsService Integration

The `SettingsService` uses both `SettingsValidator` and `SettingsCache`:

```python
# packages/core/src/zorivest_core/services/settings_service.py  (updated contract)

class SettingsService:
    """Orchestrates settings I/O with validation and caching."""

    def __init__(self, uow: UnitOfWork, resolver: SettingsResolver,
                 validator: SettingsValidator, cache: SettingsCache):
        self._uow = uow
        self._resolver = resolver
        self._validator = validator
        self._cache = cache

    def get(self, key: str) -> Optional[ResolvedSetting]:
        """Read a single setting. Uses cache when available."""
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        return self._resolve_from_db(key)

    def get_all(self) -> dict[str, str]:
        """Bulk read all user-set settings."""
        cached = self._cache.get_all()
        if cached is not None:
            return {k: v.value for k, v in cached.items()}
        resolved = self._resolve_all_from_db()
        self._cache.populate(resolved)
        return {k: v.value for k, v in resolved.items()}

    def bulk_upsert(self, settings: dict[str, Any]) -> dict:
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
```

---

## Step 2A.3: Encrypted Database Backup

### Design Decisions

1. **Back up ciphertext, not logical exports** — SQLCipher DB files are snapshotted as-is, preserving page encryption + Fernet field-level ciphertext. No decryption occurs during backup.
2. **SQLite Online Backup API** for consistent snapshots — safe for WAL mode, avoids file-lock corruption.
3. **AES-encrypted ZIP** via `pyzipper` — Python stdlib `zipfile` encryption is weak (ZipCrypto). `pyzipper` provides AES-256 encryption.
4. **Domain-separated key derivation** — same user passphrase, but backup container uses its own Argon2id derivation with a `"zorivest-backup-v1"` domain label and separate salt. This prevents reuse of raw SQLCipher key bytes for ZIP encryption.

### Backup Container Structure

```
zorivest-backup-{YYYY-MM-DD-HHmmss}.zvbak   (AES-256 encrypted ZIP via pyzipper)
├── manifest.json
├── settings.snapshot.db
└── notes.snapshot.db
```

### Manifest Schema

```python
# Manifest is written as JSON inside the encrypted ZIP

manifest = {
    "app_id": "zorivest",
    "backup_format_version": 1,
    "created_at": "2026-02-17T20:30:00Z",          # ISO 8601
    "app_version": "0.1.0",                         # semver
    "platform": "win32",

    # KDF parameters for backup container (NOT for SQLCipher DBs)
    "kdf": {
        "algorithm": "argon2id",
        "salt_b64": "<base64-encoded-salt>",
        "time_cost": 3,
        "memory_kib": 65536,
        "parallelism": 4,
        "hash_len": 32,
        "key_domain": "zorivest-backup-v1"
    },

    # Payload file inventory
    "files": [
        {"path": "settings.snapshot.db", "sha256": "abc...", "size_bytes": 32768},
        {"path": "notes.snapshot.db",    "sha256": "def...", "size_bytes": 65536}
    ],

    # SQLCipher compatibility metadata
    "sqlcipher": {
        "expected_major": 4,
        "pragmas": {
            "cipher_page_size": 4096,
            "kdf_iter": 256000
        }
    }
}
```

### BackupManager (Automatic Backups)

Extends the architecture from [`_backup-restore-architecture.md`](../_backup-restore-architecture.md):

```python
# packages/infrastructure/src/zorivest_infra/backup/backup_manager.py

class BackupManager:
    """Automatic timed backups with GFS rotation.
    
    Responsibilities:
    - Schedule periodic backups (time-based, change-based)
    - Create consistent snapshots via SQLite Online Backup API
    - Package into AES-encrypted ZIP (pyzipper)
    - Rotate with GFS retention policy
    - Run post-backup verification (sanity check: open snapshot with key)
    """

    def __init__(self, db_paths: dict[str, Path], backup_dir: Path,
                 passphrase: str, settings_service: "SettingsService"):
        # passphrase is injected once at app boot (session unlock) and held
        # in memory for the session lifetime. Not passed per-call.
        ...

    def create_snapshot(self, db_name: str, source_conn) -> Path:
        """Use SQLite Online Backup API to create consistent snapshot."""
        # source_conn.backup(dest_conn)  — Python 3.7+ sqlite3 module
        ...

    def package_backup(self, snapshot_paths: list[Path]) -> Path:
        """Create AES-encrypted ZIP with manifest and snapshots."""
        # 1. Derive backup key: Argon2id(passphrase, backup_salt, domain="zorivest-backup-v1")
        # 2. Build manifest.json (file hashes, KDF params, SQLCipher metadata)
        # 3. Write AES-encrypted ZIP via pyzipper.AESZipFile
        # 4. Verify: re-open ZIP, check manifest integrity
        ...

    def rotate_backups(self) -> list[Path]:
        """Apply GFS retention: 5 daily, 4 weekly, 3 monthly. Remove expired."""
        ...
```

### BackupRecoveryManager (Manual Operations)

```python
# packages/infrastructure/src/zorivest_infra/backup/backup_recovery_manager.py

class BackupRecoveryManager:
    """Manual backup, restore, repair, and config export/import.
    
    Responsibilities:
    - Create ad-hoc manual backups
    - Restore from backup file (decrypt → verify → stage → swap)
    - Detect and handle legacy backup formats (ZIP/DB/GZ)
    - Database repair (integrity_check → extract → rebuild)
    - JSON config export/import (via ConfigExportService)
    """

    def restore_backup(self, backup_path: Path) -> RestoreResult:
        """Full restore flow (uses session-held passphrase from __init__):
        1. Open AES-encrypted ZIP with derived key
        2. Verify file hashes from manifest.json
        3. Enter maintenance mode (close all DB connections)
        4. Stage extracted files to temp directory
        5. Verify extracted DBs can be opened with passphrase
        6. Atomic swap: os.replace() current DBs with snapshots
        7. Run post-restore migrations (Alembic)
        8. Return RestoreResult with status and any warnings
        """
        ...

    def verify_backup(self, backup_path: Path) -> VerifyResult:
        """Non-destructive verification (uses session-held passphrase)."""
        ...

    def repair_database(self, db_path: Path, passphrase: str) -> RepairResult:
        """Database repair when restore succeeds but DB won't open cleanly:
        1. PRAGMA integrity_check
        2. Try cipher_migrate for cross-version issues
        3. Fallback: ATTACH + sqlcipher_export() into new DB
        4. Record repair actions in repair log
        """
        ...
```

---

## Step 2A.4: Restore Flow (Sequence)

```
User clicks "Restore Backup"
    │
    ▼
 Prompt for backup file path
    │
    ▼
 Verify session passphrase available (401 → re-auth modal if expired)
    │
    ▼
 Detect format: .zvbak (new) │ .zip (legacy) │ .db / .db.gz (legacy)
    │
    ├─ .zvbak ──────────────────────────────────────────────────────┐
    │   1. Derive backup key: Argon2id(passphrase, manifest.kdf)   │
    │   2. Open AES-encrypted ZIP (pyzipper)                       │
    │   3. Parse manifest.json                                     │
    │   4. Verify SHA-256 checksums of all files                   │
    │   5. Extract to temp dir                                     │
    │   6. Verify each .snapshot.db opens with passphrase           │
    │   7. Close all active DB connections                         │
    │   8. Atomic swap: os.replace(snapshot → live DB)             │
    │   9. Re-open connections                                     │
    │  10. Run Alembic migrations (if schema version mismatch)     │
    │  11. Return RestoreResult(success=True)                      │
    │                                                              │
    ├─ .zip (legacy) ──────────────────────────────────────────────┤
    │   Extract settings.db + notes.db → swap                     │
    │                                                              │
    └─ .db / .db.gz (legacy) ──────────────────────────────────────┘
        Decompress (if .gz) → swap settings.db only
```

---

## Step 2A.5: JSON Config Export/Import

### Wire-Type Rules

| Endpoint | Wire Type | Rationale |
|----------|-----------|----------|
| `GET/PUT /settings` | string-only | Backward compat, MCP convention |
| `GET /settings/resolved` | typed JSON (bool, int, float, str) | SettingsResolver returns typed values |
| `GET /config/export` | typed JSON | Config is structured data |
| `POST /config/import` | typed JSON | Mirrors export format |

### Export Schema

```json
{
    "config_version": 1,
    "app_version": "0.1.0",
    "created_at": "2026-02-17T20:30:00Z",
    "settings": {
        "dialog.confirm_delete": true,
        "dialog.confirm_restore": true,
        "display.hide_dollars": false,
        "display.percent_mode": "daily",
        "logging.trades.level": "INFO",
        "logging.rotation_mb": 10,
        "backup.auto_interval_seconds": 300
    }
}
```

> **Security invariant**: Only settings where `SettingSpec.exportable == True` and `SettingSpec.sensitivity == NON_SENSITIVE` appear in export. API keys, SMTP passwords, Fernet-encrypted fields, and database paths are **never** exported.

### ConfigExportService (Domain Service)

```python
# packages/core/src/zorivest_core/domain/config_export.py

class ConfigExportService:
    """Build/parse JSON config exports using the settings registry as allowlist."""

    def __init__(self, registry: dict[str, SettingSpec], resolver: SettingsResolver):
        self._registry = registry
        self._resolver = resolver

    def build_export(self, user_settings: dict[str, str],
                     defaults: dict[str, str]) -> dict:
        """Build JSON-serializable export dict from exportable settings only."""
        export = {}
        for key, spec in self._registry.items():
            if not self._is_portable(key):
                continue  # Hard skip — never export sensitive keys
            resolved = self._resolver.resolve(key, user_settings.get(key), defaults.get(key))
            export[key] = resolved.value
        return {
            "config_version": 1,
            "app_version": self._app_version,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "settings": export,
        }

    def _is_portable(self, key: str) -> bool:
        """Shared predicate: can this key appear in export AND import?
        Must be exportable AND non-sensitive."""
        spec = self._registry.get(key)
        return (spec is not None
                and spec.exportable
                and spec.sensitivity == Sensitivity.NON_SENSITIVE)

    def validate_import(self, config_data: dict) -> ImportValidation:
        """Validate import data against registry. Returns accepted/rejected/unknown keys.
        Uses same predicate as build_export() — symmetric security enforcement."""
        accepted, rejected, unknown = [], [], []
        for key, value in config_data.get("settings", {}).items():
            spec = self._registry.get(key)
            if spec is None:
                unknown.append(key)
            elif not self._is_portable(key):
                rejected.append(key)  # non-exportable OR sensitive
            else:
                accepted.append(key)
        return ImportValidation(accepted=accepted, rejected=rejected, unknown=unknown)
```

### REST Endpoints

```python
# packages/api/src/zorivest_api/routes/config.py

config_router = APIRouter(prefix="/api/v1/config", tags=["config"])

@config_router.get("/export")
async def export_config(service: ConfigService = Depends(get_config_service)):
    """Export non-sensitive application config as JSON download."""
    export = service.build_export()
    return Response(
        content=json.dumps(export, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=zorivest-config-{date.today()}.json"}
    )

@config_router.post("/import")
async def import_config(
    body: dict,
    dry_run: bool = Query(False),
    service: ConfigService = Depends(get_config_service),
):
    """Import config from JSON. dry_run=true returns diff without writing.
    
    Import writes to user_settings only — never touches app_defaults.
    """
    validation = service.validate_import(body)
    if dry_run:
        return {"status": "preview", "validation": validation}
    result = service.apply_import(body)
    return {"status": "imported", "count": result.count, "validation": validation}
```

### Backup/Restore REST Endpoints

```python
# packages/api/src/zorivest_api/routes/backups.py

backup_router = APIRouter(prefix="/api/v1/backups", tags=["backups"])

@backup_router.post("/", status_code=201)
async def create_backup(service: BackupService = Depends(get_backup_service)):
    """Create a manual encrypted backup. Returns backup file path."""
    result = service.create_manual_backup()
    return {"status": "created", "path": str(result.path), "size_bytes": result.size}

@backup_router.get("/")
async def list_backups(service: BackupService = Depends(get_backup_service)):
    """List available backups with metadata (date, size, type)."""
    return service.list_backups()

@backup_router.post("/restore")
async def restore_backup(
    backup_path: str = Body(...),
    service: BackupService = Depends(get_backup_service),
):
    """Restore from a backup file. Uses session-held passphrase.
    If session is expired, returns 401 — GUI should show re-auth modal."""
    result = service.restore(Path(backup_path))
    return {"status": result.status, "warnings": result.warnings}

@backup_router.post("/verify")
async def verify_backup(
    backup_path: str = Body(...),
    service: BackupService = Depends(get_backup_service),
):
    """Non-destructive backup verification. Uses session-held passphrase."""
    result = service.verify(Path(backup_path))
    return {"status": result.status, "files": result.file_details}
```

### Settings Resolver REST Endpoints

```python
# Enhancement to existing packages/api/src/zorivest_api/routes/settings.py

@settings_router.get("/resolved")
async def get_resolved_settings(service: SettingsService = Depends(get_settings_service)):
    """Bulk read all settings with three-tier resolution.
    
    Returns map of key → {value, source, value_type} where
    source is "user" | "default" | "hardcoded".
    """
    return service.get_all_resolved()

@settings_router.delete("/{key}")
async def reset_setting(key: str, service: SettingsService = Depends(get_settings_service)):
    """Reset a setting to its default by removing the user override."""
    service.reset_to_default(key)
    return {"status": "reset", "key": key}
```

---

## Step 2A.6: Tests

### Unit Tests — Settings Resolution

```python
# tests/unit/test_settings_resolver.py

class TestSettingsResolver:
    def test_user_override_wins(self):
        """User value takes precedence over default and hardcoded."""
        resolver = make_resolver()
        result = resolver.resolve("display.hide_dollars", user_value="true", default_value="false")
        assert result.value is True
        assert result.source == "user"

    def test_falls_back_to_default(self):
        """When no user override, app default is used."""
        result = resolver.resolve("display.hide_dollars", user_value=None, default_value="false")
        assert result.value is False
        assert result.source == "default"

    def test_falls_back_to_hardcoded(self):
        """When neither user nor default exists, hardcoded fallback."""
        result = resolver.resolve("display.hide_dollars", user_value=None, default_value=None)
        assert result.source == "hardcoded"

    def test_unknown_key_raises(self):
        """Unknown keys are rejected."""
        with pytest.raises(KeyError):
            resolver.resolve("unknown.key", user_value=None, default_value=None)

    def test_type_coercion(self):
        """String values are parsed to correct Python types."""
        result = resolver.resolve("logging.rotation_mb", user_value="20", default_value="10")
        assert result.value == 20
        assert isinstance(result.value, int)
```

### Unit Tests — Config Export

```python
# tests/unit/test_config_export.py

class TestConfigExportService:
    def test_excludes_secret_settings(self):
        """API keys and passwords are never exported."""
        export = service.build_export(user_settings=all_settings, defaults={})
        assert "market_data.alpha_vantage.api_key" not in export["settings"]

    def test_excludes_non_exportable_settings(self):
        """Settings marked exportable=False are excluded."""
        export = service.build_export(user_settings=all_settings, defaults={})
        for key in export["settings"]:
            assert registry[key].exportable is True

    def test_import_rejects_unknown_keys(self):
        """Unknown keys in import data are flagged."""
        result = service.validate_import({"settings": {"unknown.key": "value"}})
        assert "unknown.key" in result.unknown

    def test_import_rejects_non_exportable_keys(self):
        """Non-exportable keys in import data are rejected."""
        result = service.validate_import({"settings": {"internal.db_path": "/foo"}})
        assert "internal.db_path" in result.rejected

    def test_import_rejects_sensitive_keys(self):
        """Sensitive keys are rejected even if exportable flag drifts.
        Symmetric with build_export() security invariant."""
        result = service.validate_import({"settings": {"email.smtp_password": "secret123"}})
        assert "email.smtp_password" in result.rejected
```

### Integration Tests — Backup/Restore Cycle

```python
# tests/integration/test_backup_restore.py

class TestBackupRestoreCycle:
    def test_full_backup_restore_roundtrip(self, tmp_path, passphrase):
        """Create backup → verify → restore → validate data integrity."""
        # 1. Create test databases with known data
        # 2. Create encrypted backup
        backup_path = manager.create_backup()
        assert backup_path.exists()
        assert backup_path.suffix == ".zvbak"

        # 3. Verify backup
        verify = recovery.verify_backup(backup_path, passphrase)
        assert verify.status == "valid"

        # 4. Corrupt live database
        # 5. Restore from backup
        result = recovery.restore_backup(backup_path, passphrase)
        assert result.status == "success"

        # 6. Verify data integrity after restore
        # 7. Query both DBs and compare with original

    def test_restore_wrong_passphrase_fails(self):
        """Restore with wrong passphrase fails gracefully."""
        with pytest.raises(InvalidPassphraseError):
            recovery.restore_backup(backup_path, "wrong-passphrase")

    def test_manifest_hash_mismatch_detected(self):
        """Tampered backup file is detected during verification."""
        ...
```

### Integration Tests — JSON Export/Import

```python
# tests/integration/test_config_export_import.py

class TestConfigExportImport:
    def test_export_import_roundtrip(self, client):
        """Export config → import on fresh install → settings match."""
        # 1. Set some user settings via PUT /api/v1/settings
        # 2. Export via GET /api/v1/config/export
        # 3. Clear user settings
        # 4. Import via POST /api/v1/config/import
        # 5. Verify settings match original

    def test_dry_run_does_not_write(self, client):
        """Import with dry_run=true returns preview but doesn't change DB."""
        response = client.post("/api/v1/config/import?dry_run=true", json=config)
        assert response.json()["status"] == "preview"
        # Verify no settings were changed
```

---

## Exit Criteria

- `pytest tests/unit/test_settings_resolver.py` — all resolution tests pass
- `pytest tests/unit/test_config_export.py` — allowlist enforcement verified
- `pytest tests/integration/test_backup_restore.py` — full cycle passes
- `pytest tests/integration/test_config_export_import.py` — roundtrip passes
- No sensitive data appears in JSON export output (verified by test)

## Outputs

- `AppDefaultModel` table in `settings.db`
- `SettingSpec` and `SettingsResolver` in domain layer
- `ConfigExportService` with allowlist-based export/import
- `BackupManager` with SQLite Online Backup API + AES-encrypted ZIP
- `BackupRecoveryManager` with restore + verify + repair flows
- REST endpoints: `/api/v1/backups`, `/api/v1/config`, `/api/v1/settings/resolved`
- `manifest.json` schema for self-contained backup files
- `pyzipper` added to infrastructure dependencies
