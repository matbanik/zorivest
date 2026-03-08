# Implementation Plan — backup-recovery-config-image

> Project: `backup-recovery-config-image` | Phase 2A (completion) + Phase 3 (start) | 2026-03-08

---

## Goal

Complete Phase 2A by implementing the remaining backup/restore and config export features (MEU-20, MEU-21), then start Phase 3 with the image processing pipeline (MEU-22). All dependencies are satisfied: MEU-17/18/19 ✅, Phase 2 ✅.

---

## Project Scope

| Field | Value |
|-------|-------|
| **Slug** | `backup-recovery-config-image` |
| **MEUs** | MEU-20, MEU-21, MEU-22 |
| **Execution order** | MEU-20 → MEU-21 → MEU-22 |
| **Build-plan sections** | [02a §2A.4](../../build-plan/02a-backup-restore.md) (10d), [02a §2A.5](../../build-plan/02a-backup-restore.md) (10e), [image-architecture](../../build-plan/image-architecture.md) (11) |
| **In-scope** | BackupRecoveryManager, ConfigExportService, image processing functions, unit tests, integration tests |
| **Out-of-scope** | REST endpoints (Phase 4), MCP tools (Phase 5), GUI (Phase 6), Alembic migration infrastructure |

---

## Task Table

| # | Task | Owner Role | Deliverable | Validation | Status |
|---|------|-----------|-------------|------------|--------|
| 0 | Gate: confirm all deps ✅ | orchestrator | MEU-17/18/19 approved in registry | `rg "MEU-1[7-9]\b.*✅ approved" .agent/context/meu-registry.md` — 3 matches | ✅ |
| 1 | MEU-20 FIC + Red tests | coder | `tests/unit/test_backup_recovery.py` | `uv run pytest tests/unit/test_backup_recovery.py -x --tb=short -v` — all FAIL | ✅ |
| 2 | MEU-20 Green implementation | coder | `backup_recovery_manager.py`, result types, exceptions | `uv run pytest tests/unit/test_backup_recovery.py -x --tb=short -v` — all PASS | ✅ |
| 3 | MEU-20 integration tests | coder | `tests/integration/test_backup_recovery_integration.py` | `uv run pytest tests/integration/test_backup_recovery_integration.py -x --tb=short -v` — all PASS | ✅ |
| 4 | MEU-20 quality gate | tester | Zero errors | pyright + ruff + anti-placeholder | ✅ |
| 5 | MEU-20 handoff | coder | `021-2026-03-08-backup-recovery-bp02as2A.4.md` | Handoff created with ≥7 sections | ✅ |
| 6 | MEU-20 validation | reviewer | Codex appends to handoff 021 | Verdict: approved (after corrections) | ✅ |
| 7 | MEU-21 FIC + Red tests | coder | `tests/unit/test_config_export.py` | `uv run pytest tests/unit/test_config_export.py -x --tb=short -v` — all FAIL | ✅ |
| 8 | MEU-21 Green implementation | coder | `config_export.py`, `ImportValidation` | `uv run pytest tests/unit/test_config_export.py -x --tb=short -v` — all PASS | ✅ |
| 9 | MEU-21 quality gate | tester | Zero errors | pyright + ruff + anti-placeholder | ✅ |
| 10 | MEU-21 handoff | coder | `022-2026-03-08-config-export-bp02as2A.5.md` | Handoff created with ≥7 sections | ✅ |
| 11 | MEU-21 validation | reviewer | Codex appends to handoff 022 | Verdict: approved (after corrections) | ✅ |
| 12 | MEU-22 FIC + Red tests | coder | `tests/unit/test_image_processing.py` | `uv run pytest tests/unit/test_image_processing.py -x --tb=short -v` — all FAIL | ✅ |
| 13 | MEU-22 Green implementation | coder | `image_processing.py` | `uv run pytest tests/unit/test_image_processing.py -x --tb=short -v` — all PASS | ✅ |
| 14 | MEU-22 quality gate | tester | Zero errors | pyright + ruff + anti-placeholder | ✅ |
| 15 | MEU-22 handoff | coder | `023-2026-03-08-image-processing-bp03sIMG.md` | Handoff created with ≥7 sections | ✅ |
| 16 | MEU-22 validation | reviewer | Codex appends to handoff 023 | Verdict: approved (after corrections) | ✅ |
| 17 | BUILD_PLAN.md update | coder | Phase tracker + MEU statuses + summary counts | All 3 MEUs ✅, phases completed, counts updated | ✅ |
| 18 | MEU registry update | coder | MEU-20/21/22 rows + Phase 3 section + execution order | All rows added, Phase 3 section created | ✅ |
| 19 | MEU gate | tester | Zero errors | `uv run python tools/validate_codebase.py --scope meu` — pass | ✅ |
| 20 | Full regression | tester | All tests pass | `uv run pytest tests/ -q` — 501 passed, 1 skipped | ✅ |
| 21 | Anti-placeholder scan | tester | Clean | `rg "TODO|FIXME|NotImplementedError" packages/` — clean | ✅ |
| 22 | Reflection | tester | Reflection file exists | File created | ✅ |
| 23 | Metrics | tester | Row appended | Row added to metrics.md | ✅ |
| 24 | Commit messages | coder | Proposed commit messages file | File created | ✅ |
| 25 | Session state | orchestrator | Pomera note saved | session-state.md + pomera note #344 | ✅ |

**Role progression per MEU:** orchestrator (gate) → coder (FIC + Red + Green + handoff) → tester (quality gate) → reviewer/Codex (validation appended to handoff)

---

## Spec Sufficiency — MEU-20: backup-recovery

| Behavior / Contract | Source Type | Source | Resolved? | Notes |
|---|---|---|---|---|
| restore_backup 11-step flow | Spec | 02a §2A.4 L631-661 | ✅ | Decrypt → verify → stage → swap → migrate |
| verify_backup non-destructive | Spec | 02a §2A.3 L613-615 | ✅ | Opens ZIP, checks hashes, does not modify |
| repair_database 4-step flow | Spec | 02a §2A.3 L617-624 | ✅ | integrity_check → cipher_migrate → export → log |
| Legacy format detection | Spec | 02a §2A.4 L641-660 | ✅ | .zvbak / .zip / .db / .db.gz |
| Result types | Local Canon | Derived from spec descriptions | ✅ | Frozen dataclasses with status + warnings |
| InvalidPassphraseError | Local Canon | 02a test L946 | ✅ | New exception in domain/exceptions.py |
| CorruptedBackupError | Local Canon | Derived from manifest hash mismatch test | ✅ | New exception |
| Atomic swap via `os.replace()` | Spec | 02a §2A.4 L651 | ✅ | |
| Maintenance mode (close connections) | Spec | 02a §2A.4 L650 | ✅ | Callback-based |
| Post-restore migrations | Spec | 02a §2A.4 L653 | ✅ | Stub: log check, no real Alembic yet |
| KDF key derivation | Local Canon | backup_manager.py L175-194 | ✅ | Extract to shared utility |

## Feature Intent Contract — MEU-20

**AC-20.1** [Spec]: `restore_backup()` opens a `.zvbak` file, verifies manifest hashes, stages to temp dir, performs atomic swap, and returns `RestoreResult(status="success")`.

**AC-20.2** [Spec]: `restore_backup()` with wrong passphrase raises `InvalidPassphraseError`.

**AC-20.3** [Spec]: `restore_backup()` with tampered file (hash mismatch) raises `CorruptedBackupError`.

**AC-20.4** [Spec]: `verify_backup()` opens and validates a backup without modifying anything, returns `VerifyResult(status="valid")` with file details.

**AC-20.5** [Spec]: `verify_backup()` detects corrupted backup and returns `VerifyResult(status="corrupted")`.

**AC-20.6** [Spec]: `repair_database()` runs PRAGMA integrity_check, and on failure attempts recovery by creating a new DB and exporting data.

**AC-20.7** [Spec]: Legacy `.zip` format backup detected and extracted correctly.

**AC-20.8** [Spec]: Legacy `.db` and `.db.gz` formats detected and handled.

**AC-20.9** [Local Canon]: Maintenance mode hooks (close_connections/reopen_connections callbacks) are invoked during restore.

---

## Spec Sufficiency — MEU-21: config-export

| Behavior / Contract | Source Type | Source | Resolved? | Notes |
|---|---|---|---|---|
| build_export with allowlist filtering | Spec | 02a §2A.5 L711-725 | ✅ | |
| _is_portable symmetric predicate | Spec | 02a §2A.5 L727-733 | ✅ | exportable AND non-sensitive |
| validate_import accepted/rejected/unknown | Spec | 02a §2A.5 L735-747 | ✅ | |
| ImportValidation type | Local Canon | Derived from spec | ✅ | Frozen dataclass |
| Export schema | Spec | 02a §2A.5 L678-692 | ✅ | config_version, app_version, created_at |
| Security: never export SECRET/SENSITIVE | Spec | 02a §2A.5 L695 | ✅ | |
| Sensitivity enum | Local Canon | settings.py L19 | ✅ | Already implemented |
| SettingSpec dependency | Local Canon | settings.py L33 | ✅ | Already implemented |
| SettingsResolver dependency | Local Canon | MEU-18 | ✅ | Consumed upstream by SettingsService; ConfigExportService accepts pre-resolved values (SRP) |

## Feature Intent Contract — MEU-21

**AC-21.1** [Spec]: `build_export()` returns a dict with `config_version`, `app_version`, `created_at`, and `settings` containing only exportable, non-sensitive keys with typed values.

**AC-21.2** [Spec]: `build_export()` excludes all settings where `sensitivity == SECRET` or `sensitivity == SENSITIVE`.

**AC-21.3** [Spec]: `build_export()` excludes settings where `exportable == False`.

**AC-21.4** [Spec]: `validate_import()` categorizes import keys into `accepted`, `rejected`, and `unknown` lists.

**AC-21.5** [Spec]: `validate_import()` rejects non-portable keys (non-exportable or sensitive) even if they appear in import data.

**AC-21.6** [Spec]: Export and import use the same `_is_portable()` predicate — symmetric security enforcement.

**AC-21.7** [Spec]: `ImportValidation` is a frozen dataclass with `accepted: list[str]`, `rejected: list[str]`, `unknown: list[str]`.

---

## Spec Sufficiency — MEU-22: image-processing

| Behavior / Contract | Source Type | Source | Resolved? | Notes |
|---|---|---|---|---|
| validate_image magic bytes | Spec | image-architecture L158-176 | ✅ | PNG, JPEG, GIF, WebP |
| 10MB size limit | Spec | image-architecture L154-156 | ✅ | |
| Dimension extraction | Spec | image-architecture L147-176 | ✅ | Returns (mime, width, height) |
| standardize_to_webp (quality=85) | Spec | image-architecture L108-126 | ✅ | |
| Alpha channel preservation | Spec | image-architecture L121-122 | ✅ | |
| generate_thumbnail (200×200) | Spec | image-architecture L129-144 | ✅ | LANCZOS, quality=80 |
| MIME normalization | Spec | image-architecture L97-99 | ✅ | Always image/webp |
| Unsupported format ValueError | Spec | image-architecture L176 | ✅ | |
| Pillow dependency | Local Canon | dependency-manifest | ✅ | |

## Feature Intent Contract — MEU-22

**AC-22.1** [Spec]: `validate_image()` accepts PNG, JPEG, GIF, and WebP by magic bytes and returns `(original_mime_type, width, height)`.

**AC-22.2** [Spec]: `validate_image()` raises `ValueError` for images exceeding 10MB.

**AC-22.3** [Spec]: `validate_image()` raises `ValueError` for unsupported formats.

**AC-22.4** [Spec]: `standardize_to_webp()` converts PNG/JPEG/GIF/WebP to WebP format with `quality=85`.

**AC-22.5** [Spec]: `standardize_to_webp()` preserves alpha channel for images with transparency.

**AC-22.6** [Spec]: `standardize_to_webp()` converts non-RGB/RGBA images to RGB.

**AC-22.7** [Spec]: `generate_thumbnail()` creates a WebP thumbnail capped at 200×200 preserving aspect ratio.

**AC-22.8** [Spec]: `generate_thumbnail()` uses LANCZOS resampling and `quality=80`.

---

## Proposed Changes

### MEU-20: BackupRecoveryManager

#### [NEW] backup_recovery_types.py
`packages/infrastructure/src/zorivest_infra/backup/backup_recovery_types.py`
Result types: `RestoreResult`, `VerifyResult`, `RepairResult`, status enums.

#### [NEW] backup_recovery_manager.py
`packages/infrastructure/src/zorivest_infra/backup/backup_recovery_manager.py`
`BackupRecoveryManager` with restore, verify, repair, legacy format detection.

#### [MODIFY] exceptions.py
`packages/core/src/zorivest_core/domain/exceptions.py`
Add `InvalidPassphraseError` and `CorruptedBackupError`.

#### [NEW] test_backup_recovery.py
`tests/unit/test_backup_recovery.py`

#### [NEW] test_backup_recovery_integration.py
`tests/integration/test_backup_recovery_integration.py`

---

### MEU-21: ConfigExportService

#### [NEW] config_export.py
`packages/core/src/zorivest_core/domain/config_export.py`
`ConfigExportService` class and `ImportValidation` frozen dataclass.

#### [NEW] test_config_export.py
`tests/unit/test_config_export.py`

---

### MEU-22: Image Processing

#### [NEW] image_processing.py
`packages/infrastructure/src/zorivest_infra/image_processing.py`
`validate_image()`, `standardize_to_webp()`, `generate_thumbnail()`.

#### [NEW] test_image_processing.py
`tests/unit/test_image_processing.py`

---

### BUILD_PLAN.md Update

#### [MODIFY] BUILD_PLAN.md
`docs/BUILD_PLAN.md`
- Phase 2A status: `🔵 In Progress` → `✅ Completed` (L61)
- Phase 3 status: `⚪ Not Started` → `✅ Completed` (L62) — MEU-22 completes Phase 3
- MEU-20 and MEU-21 status: `⬜` → `✅` (L151-152)
- MEU-22 status: `⬜` → `✅` (L160)
- MEU Summary table (L459-476): Phase 2/2A completed `5` → `10`, Phase 3/4 completed `0` → `1`, Total `19` → `22`

---

### State Management

#### [MODIFY] meu-registry.md
`.agent/context/meu-registry.md`
- Update heading: `Phase 1 + 1A + 2` → `Phase 1 + 1A + 2 + 2A + 3`
- Add MEU-20 row: `| MEU-20 | backup-recovery | 10d | BackupRecoveryManager (restore + repair) | ✅ approved |`
- Add MEU-21 row: `| MEU-21 | config-export | 10e | ConfigExportService (JSON export/import) | ✅ approved |`
- Create new `## Phase 3: Service Layer (P0)` section with MEU-22 row
- Update Execution Order: add `Phase 2A: MEU-17 → MEU-18 → MEU-19 → MEU-20 → MEU-21` and `Phase 3: MEU-22`
- Update Phase-Exit Criteria: add Phase 2A and Phase 3 lines

---

## Verification Plan

### Automated Tests

```bash
# Unit tests for all three MEUs
uv run pytest tests/unit/test_backup_recovery.py -v
uv run pytest tests/unit/test_config_export.py -v
uv run pytest tests/unit/test_image_processing.py -v

# Integration tests
uv run pytest tests/integration/test_backup_recovery_integration.py -v

# Full regression
uv run pytest tests/ -v

# MEU gate
uv run python tools/validate_codebase.py --scope meu

# Anti-placeholder scan
rg "TODO|FIXME|NotImplementedError" packages/
```

### Manual Verification

None required — all behaviors are covered by automated tests.

---

## Handoff Paths

| MEU | Handoff Path |
|-----|-------------|
| MEU-20 | `.agent/context/handoffs/021-2026-03-08-backup-recovery-bp02as2A.4.md` |
| MEU-21 | `.agent/context/handoffs/022-2026-03-08-config-export-bp02as2A.5.md` |
| MEU-22 | `.agent/context/handoffs/023-2026-03-08-image-processing-bp03sIMG.md` |
