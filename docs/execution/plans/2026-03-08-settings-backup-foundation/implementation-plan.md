# Settings & Backup Foundation

Implement the first three MEUs of Phase 2A (Backup/Restore). This project builds the settings infrastructure (defaults registry, three-tier resolver, validator, cache) and the encrypted backup manager — the foundation upon which restore, repair, and config export (MEU-20/21) will build.

> **Build plan source**: [02a-backup-restore.md](file:///p:/zorivest/docs/build-plan/02a-backup-restore.md) §2A.1–§2A.3

---

## User Review Required

> [!IMPORTANT]
> **Seeding mechanism**: The spec references "seeding migration" but no Alembic infrastructure exists in the project. This plan resolves MEU-17 as a `seed_defaults()` function callable at app initialization via `Base.metadata.create_all()` + seed call, rather than an Alembic migration. This is consistent with the current Phase 2 pattern where all tables use `create_all()`.

> [!IMPORTANT]
> **UoW extension**: MEU-18 requires adding `settings` and `app_defaults` repository attributes to the `UnitOfWork` protocol and its SQLAlchemy implementation. This extends an existing contract (currently 5 repos → 7 repos). The `test_ports.py` protocol invariant (RULE-2 from reflection) must be updated from 9 → 11 protocols.

> [!IMPORTANT]
> **pyzipper dependency**: MEU-19 requires `pyzipper` (AES-256 ZIP encryption). The dependency-manifest.md lists `uv add --package zorivest-infra pyzipper` but it is not yet installed. Will be added during MEU-19 execution.

---

## Proposed Changes

### MEU-17: `app-defaults` — Settings Registry & Default Seeding

Build-plan ref: [02a §2A.1](file:///p:/zorivest/docs/build-plan/02a-backup-restore.md) | Matrix item: 10a | Handoff: `018-2026-03-08-app-defaults-bp02as2A.1.md`

#### [NEW] [settings.py](file:///p:/zorivest/packages/core/src/zorivest_core/domain/settings.py)
- `SettingSpec` frozen dataclass (key, value_type, hardcoded_default, category, exportable, sensitivity, validator, description, allowed_values, min_value, max_value, max_length)
- `Sensitivity` enum (NON_SENSITIVE, SENSITIVE, SECRET)
- `SETTINGS_REGISTRY: dict[str, SettingSpec]` — canonical registry of all 24 known settings from the spec table (02a §2A.1 L41-66)

#### [NEW] [seed_defaults.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/seed_defaults.py)
- `seed_defaults(session: Session, registry: dict[str, SettingSpec])` — idempotent function that populates `app_defaults` table from registry
- Checks existing rows before insert (upsert-on-key semantics)
- Called at app startup after `create_all()`

#### [NEW] [test_settings_registry.py](file:///p:/zorivest/tests/unit/test_settings_registry.py)
- Verify all 24 registry entries have valid value_type
- Verify seeding populates all rows
- Verify idempotent re-seeding
- Verify each category matches expected set

---

### MEU-18: `settings-resolver` — Resolver, Validator, Cache & Service

Build-plan ref: [02a §2A.2](file:///p:/zorivest/docs/build-plan/02a-backup-restore.md) | Matrix item: 10b | Handoff: `019-2026-03-08-settings-resolver-bp02as2A.2.md`

#### [NEW] [settings_resolver.py](file:///p:/zorivest/packages/core/src/zorivest_core/domain/settings_resolver.py)
- `ResolvedSetting` dataclass (key, value, source, value_type)
- `SettingsResolver` class — three-tier resolution (user → default → hardcoded)
- `_parse()` static method — type coercion (bool/int/float/json/str)
- `is_exportable()` — sensitivity + exportable check

#### [NEW] [settings_validator.py](file:///p:/zorivest/packages/core/src/zorivest_core/domain/settings_validator.py)
- `ValidationResult` dataclass
- `SettingsValidationError` exception with per-key errors
- `SettingsValidator` class — 3-stage pipeline (type → format → security)
- Module-level compiled regex patterns (path traversal, SQL injection, script injection)
- `_resolve_spec()` with glob pattern fallback
- `validate_bulk()` for batch validation

#### [NEW] [settings_cache.py](file:///p:/zorivest/packages/core/src/zorivest_core/domain/settings_cache.py)
- `SettingsCache` class — thread-safe (`threading.Lock`), TTL-based staleness
- `get()`, `get_all()`, `populate()`, `invalidate()`

#### [MODIFY] [ports.py](file:///p:/zorivest/packages/core/src/zorivest_core/application/ports.py)
- Add `SettingsRepository(Protocol)` — `get(key)`, `get_all()`, `bulk_upsert(settings)`, `delete(key)`
- Add `AppDefaultsRepository(Protocol)` — `get(key)`, `get_all()`
- Add `settings: SettingsRepository` and `app_defaults: AppDefaultsRepository` to `UnitOfWork`

#### [MODIFY] [repositories.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/repositories.py)
- Add `SqlAlchemySettingsRepository` implementation
- Add `SqlAlchemyAppDefaultsRepository` implementation

#### [MODIFY] [unit_of_work.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/unit_of_work.py)
- Add `settings` and `app_defaults` attributes to `SqlAlchemyUnitOfWork`

#### [NEW] [settings_service.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/settings_service.py)
- `SettingsService` class — orchestrates resolver + validator + cache + UoW
- `get()`, `get_all()`, `get_all_resolved()`, `bulk_upsert()`, `reset_to_default()`

#### Test files

| File | Scope |
|------|-------|
| [NEW] [test_settings_resolver.py](file:///p:/zorivest/tests/unit/test_settings_resolver.py) | Extend with resolver tests (user wins, fallback to default, fallback to hardcoded, unknown key, type coercion) |
| [NEW] [test_settings_validator.py](file:///p:/zorivest/tests/unit/test_settings_validator.py) | Type validation, format checks (ranges, enums, length), security patterns (path traversal, SQL injection, XSS), glob pattern fallback, bulk validation, SettingsValidationError |
| [NEW] [test_settings_cache.py](file:///p:/zorivest/tests/unit/test_settings_cache.py) | Cache hit/miss, TTL staleness, invalidation, thread safety |
| [NEW] [test_settings_service.py](file:///p:/zorivest/tests/unit/test_settings_service.py) | Service integration with mock UoW (get, bulk_upsert with validation, reset) |
| [MODIFY] [test_ports.py](file:///p:/zorivest/tests/unit/test_ports.py) | Update protocol invariant count: 9 → 11 (add SettingsRepository, AppDefaultsRepository) |

---

### MEU-19: `backup-manager` — Encrypted Backup & GFS Rotation

Build-plan ref: [02a §2A.3](file:///p:/zorivest/docs/build-plan/02a-backup-restore.md) | Matrix item: 10c | Handoff: `020-2026-03-08-backup-manager-bp02as2A.3.md`

#### [NEW] [backup/](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/backup/)
New package directory for backup infrastructure.

#### [NEW] [backup_manager.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/backup/backup_manager.py)
- `BackupManager` class
- `create_snapshot(db_name, source_conn) → Path` — SQLite Online Backup API
- `package_backup(snapshot_paths) → Path` — AES-encrypted ZIP via pyzipper with manifest
- `rotate_backups() → list[Path]` — GFS retention (5 daily, 4 weekly, 3 monthly)
- `create_backup() → BackupResult` — full workflow (snapshot → package → rotate → verify)
- `_derive_backup_key()` — Argon2id with `zorivest-backup-v1` domain label + separate salt
- `_build_manifest()` — JSON manifest with file hashes, KDF params, SQLCipher metadata
- `_verify_backup()` — re-open ZIP, check manifest integrity

#### [NEW] [backup_types.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/backup/backup_types.py)
- `BackupResult` dataclass (path, size, manifest, created_at)
- `BackupManifest` typed dict / dataclass matching the manifest schema

#### Test files

| File | Scope |
|------|-------|
| [NEW] [test_backup_manager.py](file:///p:/zorivest/tests/unit/test_backup_manager.py) | Snapshot creation via Online Backup API, AES round-trip (encrypt → decrypt), manifest integrity, GFS rotation (keep counts), domain-separated key derivation |
| [NEW] [test_backup_integration.py](file:///p:/zorivest/tests/integration/test_backup_integration.py) | Full backup cycle: create DB → seed data → snapshot → package → verify → GFS rotate |

---

### BUILD_PLAN.md Maintenance Task

#### [MODIFY] [BUILD_PLAN.md](file:///p:/zorivest/docs/BUILD_PLAN.md)
- Phase 2A status: `⚪ Not Started` → `🔵 In Progress` (stays in-progress until all 5 MEUs complete)
- MEU 17-19 rows already exist with correct refs; no structural changes needed

#### [MODIFY] [meu-registry.md](file:///p:/zorivest/.agent/context/meu-registry.md)
- Add Phase 2A section with MEU-17, MEU-18, MEU-19 rows
- Update execution order to include Phase 2A

**Validation**: `rg -n "Phase 2A|2A —" docs/BUILD_PLAN.md` — verify status shows `🔵 In Progress` (not `⚪ Not Started` or `✅ Completed`) after this project ends.

---

## Spec Sufficiency Tables

### MEU-17 Sufficiency

| Behavior / Contract | Source Type | Source | Resolved? |
|---|---|---|---|
| AppDefaultModel schema | Spec | 02a §2A.1 L19-36 | ✅ (already in models.py) |
| 24 default settings entries | Spec | 02a §2A.1 L41-66 | ✅ |
| SettingSpec dataclass | Spec | 02a §2A.2 L100-128 | ✅ |
| Sensitivity enum | Spec | 02a §2A.2 L108-111 | ✅ |
| Idempotent seeding mechanism | Local Canon | create_all() pattern from Phase 2 | ✅ |

### MEU-18 Sufficiency

| Behavior / Contract | Source Type | Source | Resolved? |
|---|---|---|---|
| Three-tier resolution | Spec | 02a §2A.2 L150-178 | ✅ |
| Type coercion (5 types) | Spec | 02a §2A.2 L186-202 | ✅ |
| 3-stage validation pipeline | Spec | 02a §2A.2b L252-369 | ✅ |
| Security regex patterns | Spec | 02a §2A.2b L237-249 | ✅ |
| Glob pattern fallback | Spec | 02a §2A.2b L286-298 | ✅ |
| TTL cache with invalidation | Spec | 02a §2A.2c L378-429 | ✅ |
| Validation rules table | Spec | 02a §2A.1 L75-92 | ✅ |
| SettingsService contract | Spec | 02a §2A.2d L436-479 | ✅ |
| SettingsRepository port | Local Canon | UoW pattern from Phase 2 | ✅ |

### MEU-19 Sufficiency

| Behavior / Contract | Source Type | Source | Resolved? |
|---|---|---|---|
| SQLite Online Backup API | Spec | 02a §2A.3 L489,566-568 | ✅ |
| AES-encrypted ZIP (pyzipper) | Spec | 02a §2A.3 L490 | ✅ |
| Domain-separated Argon2id KDF | Spec | 02a §2A.3 L491,515-523 | ✅ |
| Backup container (.zvbak) | Spec | 02a §2A.3 L496-500 | ✅ |
| Manifest JSON schema | Spec | 02a §2A.3 L504-539 | ✅ |
| GFS rotation (5/4/3) | Spec | 02a §2A.3 L579 | ✅ |
| Post-backup verification | Spec | 02a §2A.3 L557 | ✅ |
| pyzipper dependency install | Spec | dependency-manifest.md L22 | ✅ |

---

## Feature Intent Contracts (FIC)

### MEU-17 FIC: app-defaults

| AC | Description | Source | Test |
|---|---|---|---|
| AC-17.1 | SETTINGS_REGISTRY contains exactly 24 entries matching spec table | Spec | `test_registry_has_24_entries` |
| AC-17.2 | Every registry entry has valid value_type ∈ {str, int, float, bool, json} | Spec | `test_all_value_types_valid` |
| AC-17.3 | Every registry entry has non-empty category ∈ {dialog, logging, display, backup, ui, notification} | Spec | `test_all_categories_valid` |
| AC-17.4 | `seed_defaults()` populates app_defaults table with all 24 rows | Spec | `test_seed_populates_all_rows` |
| AC-17.5 | `seed_defaults()` is idempotent (re-run doesn't duplicate or error) | Local Canon | `test_seed_is_idempotent` |
| AC-17.6 | Dynamic key `ui.panel.*.collapsed` is present in registry | Spec | `test_dynamic_key_in_registry` |

### MEU-18 FIC: settings-resolver

| AC | Description | Source | Test |
|---|---|---|---|
| AC-18.1 | User override wins over default and hardcoded | Spec | `test_user_override_wins` |
| AC-18.2 | Falls back to app default when no user override | Spec | `test_falls_back_to_default` |
| AC-18.3 | Falls back to hardcoded when neither user nor default | Spec | `test_falls_back_to_hardcoded` |
| AC-18.4 | Unknown key raises KeyError | Spec | `test_unknown_key_raises` |
| AC-18.5 | Type coercion parses "true"→True, "20"→20, etc. | Spec | `test_type_coercion_*` |
| AC-18.6 | Validator Stage 1: rejects invalid type (e.g., "abc" for int) | Spec | `test_validate_type_rejection` |
| AC-18.7 | Validator Stage 2: rejects out-of-range values | Spec | `test_validate_range_rejection` |
| AC-18.8 | Validator Stage 2: rejects values not in allowed_values | Spec | `test_validate_enum_rejection` |
| AC-18.9 | Validator Stage 3: rejects path traversal | Spec | `test_validate_path_traversal` |
| AC-18.10 | Validator Stage 3: rejects SQL injection patterns | Spec | `test_validate_sql_injection` |
| AC-18.11 | Validator Stage 3: rejects script injection | Spec | `test_validate_script_injection` |
| AC-18.12 | Validator glob fallback resolves `ui.panel.sidebar.collapsed` via `ui.panel.*.collapsed` | Spec | `test_glob_pattern_fallback` |
| AC-18.13 | Cache returns same value within TTL | Spec | `test_cache_within_ttl` |
| AC-18.14 | Cache returns None after TTL expires | Spec | `test_cache_stale_after_ttl` |
| AC-18.15 | Cache invalidate() clears all entries | Spec | `test_cache_invalidate` |
| AC-18.16 | SettingsRepository port has get, get_all, bulk_upsert, delete | Local Canon | `test_ports.py` invariant |
| AC-18.17 | AppDefaultsRepository port has get, get_all | Local Canon | `test_ports.py` invariant |
| AC-18.18 | UoW has settings and app_defaults attributes | Local Canon | `test_ports.py` invariant |
| AC-18.19 | SettingsService.bulk_upsert raises SettingsValidationError on invalid input | Spec | `test_service_bulk_upsert_validation_error` |
| AC-18.20 | SettingsService.bulk_upsert invalidates cache after write | Spec | `test_service_invalidates_cache` |
| AC-18.21 | SettingsService.reset_to_default removes user override | Spec | `test_service_reset_to_default` |

### MEU-19 FIC: backup-manager

| AC | Description | Source | Test |
|---|---|---|---|
| AC-19.1 | `create_snapshot()` uses SQLite Online Backup API | Spec | `test_snapshot_creates_valid_db` |
| AC-19.2 | Snapshot DB is openable and contains same data | Spec | `test_snapshot_data_integrity` |
| AC-19.3 | `package_backup()` creates .zvbak file | Spec | `test_package_creates_zvbak` |
| AC-19.4 | Backup container is AES-256 encrypted (wrong password fails) | Spec | `test_wrong_password_fails` |
| AC-19.5 | Manifest contains app_id, version, created_at, kdf, files, sqlcipher sections | Spec | `test_manifest_schema` |
| AC-19.6 | Manifest file hashes match actual file SHA-256 | Spec | `test_manifest_hash_integrity` |
| AC-19.7 | Key derivation uses Argon2id with `zorivest-backup-v1` domain label | Spec | `test_domain_separated_kdf` |
| AC-19.8 | GFS rotation keeps 5 daily, 4 weekly, 3 monthly | Spec | `test_gfs_rotation_counts` |
| AC-19.9 | GFS removes expired backups | Spec | `test_gfs_removes_expired` |
| AC-19.10 | Post-backup verification confirms integrity | Spec | `test_post_backup_verify` |
| AC-19.11 | Full backup cycle: snapshot → package → rotate → verify | Spec | `test_full_backup_cycle` |

---

## Verification Plan

### Automated Tests

All tests use `pytest` with in-memory SQLite where possible.

```bash
# MEU-17 tests
uv run pytest tests/unit/test_settings_registry.py -v

# MEU-18 tests
uv run pytest tests/unit/test_settings_resolver.py tests/unit/test_settings_validator.py tests/unit/test_settings_cache.py tests/unit/test_settings_service.py -v

# MEU-19 tests
uv run pytest tests/unit/test_backup_manager.py tests/integration/test_backup_integration.py -v

# Protocol invariant (RULE-2)
uv run pytest tests/unit/test_ports.py -v

# Full regression
uv run pytest tests/ -v

# MEU-scoped quality gate
uv run python tools/validate_codebase.py --scope meu
```

### Manual Verification

No manual verification required — all MEUs have automated test coverage per spec.

---

## Task Table

| # | Task | owner_role | Deliverable | Validation | Status |
|---|---|---|---|---|---|
| 1 | MEU-17: Write `SettingSpec`, `Sensitivity`, `SETTINGS_REGISTRY` | coder | `settings.py` | `uv run python -c "from zorivest_core.domain.settings import SETTINGS_REGISTRY; assert len(SETTINGS_REGISTRY) == 24"` | ⬜ |
| 2 | MEU-17: Write `seed_defaults()` | coder | `seed_defaults.py` | `uv run pytest tests/unit/test_settings_registry.py::TestSeedDefaults -v` | ⬜ |
| 3 | MEU-17: Write tests + verify RED→GREEN | tester | `test_settings_registry.py` | `uv run pytest tests/unit/test_settings_registry.py -v` | ⬜ |
| 4 | MEU-17: Handoff | coder | `018-2026-03-08-app-defaults-bp02as2A.1.md` | `(Get-Content .agent/context/handoffs/018-*.md \| Select-String '^## ').Count -ge 9` | ⬜ |
| 5 | MEU-18: Write resolver, validator, cache | coder | `settings_resolver.py`, `settings_validator.py`, `settings_cache.py` | `uv run pytest tests/unit/test_settings_resolver.py tests/unit/test_settings_validator.py tests/unit/test_settings_cache.py -v` | ⬜ |
| 6 | MEU-18: Add ports + repo impls + UoW ext | coder | `ports.py`, `repositories.py`, `unit_of_work.py` | `uv run pytest tests/unit/test_ports.py -v` | ⬜ |
| 7 | MEU-18: Write SettingsService | coder | `settings_service.py` | `uv run pytest tests/unit/test_settings_service.py -v` | ⬜ |
| 8 | MEU-18: Write all tests + verify RED→GREEN | tester | 4 test files | `uv run pytest tests/unit/test_settings_resolver.py tests/unit/test_settings_validator.py tests/unit/test_settings_cache.py tests/unit/test_settings_service.py -v` | ⬜ |
| 9 | MEU-18: Handoff | coder | `019-2026-03-08-settings-resolver-bp02as2A.2.md` | `(Get-Content .agent/context/handoffs/019-*.md \| Select-String '^## ').Count -ge 9` | ⬜ |
| 10 | MEU-19: Install pyzipper | coder | `pyproject.toml` | `uv run python -c "import pyzipper; print(pyzipper.__version__)"` | ⬜ |
| 11 | MEU-19: Write BackupManager + types | coder | `backup_manager.py`, `backup_types.py` | `uv run pytest tests/unit/test_backup_manager.py -v` | ⬜ |
| 12 | MEU-19: Write tests + verify RED→GREEN | tester | `test_backup_manager.py`, `test_backup_integration.py` | `uv run pytest tests/unit/test_backup_manager.py tests/integration/test_backup_integration.py -v` | ⬜ |
| 13 | MEU-19: Handoff | coder | `020-2026-03-08-backup-manager-bp02as2A.3.md` | `(Get-Content .agent/context/handoffs/020-*.md \| Select-String '^## ').Count -ge 9` | ⬜ |
| 14 | Update MEU registry | coder | `meu-registry.md` | `rg -c "MEU-17\|MEU-18\|MEU-19" .agent/context/meu-registry.md` — expect 3 | ⬜ |
| 15 | Validate BUILD_PLAN.md hub | coder | `BUILD_PLAN.md` | `rg -n "Phase 2A\|2A —" docs/BUILD_PLAN.md` — verify `🔵 In Progress` | ⬜ |
| 16 | Run full regression | tester | all tests pass | `uv run pytest tests/ -v` | ⬜ |
| 17 | Reflection + metrics | reviewer | `2026-03-08-settings-backup-foundation-reflection.md` | `Test-Path docs/execution/reflections/2026-03-08-settings-backup-foundation-reflection.md` | ⬜ |
| 18 | Proposed commit messages | coder | `commit-messages.md` | `Test-Path docs/execution/plans/2026-03-08-settings-backup-foundation/commit-messages.md` | ⬜ |
