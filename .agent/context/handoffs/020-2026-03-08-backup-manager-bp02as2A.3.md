# Task Handoff — MEU-19 Backup Manager

## Task

- **Date:** 2026-03-08
- **Task slug:** backup-manager
- **Owner role:** coder
- **Scope:** MEU-19 — Backup Manager (build-priority-matrix item 13, 02a-backup-restore.md §2A.3)

## Inputs

- User request: Implement automatic backup manager with AES-encrypted ZIP packaging and GFS rotation
- Specs/docs referenced: `02a-backup-restore.md` §2A.3 L484-582 (BackupManager), L493-539 (manifest schema), L486-491 (design decisions)
- Constraints: SQLite Online Backup API for consistent snapshots. AES-256 via pyzipper. Domain-separated key derivation. GFS rotation (5 daily, 4 weekly, 3 monthly). Post-backup verification.

## Role Plan

1. coder
2. tester
- Optional roles: reviewer, guardrail (deferred to project-level review)

## Coder Output

- Changed files:

| File | Change |
|------|--------|
| `packages/infrastructure/src/zorivest_infra/backup/__init__.py` | NEW — package init |
| `packages/infrastructure/src/zorivest_infra/backup/backup_types.py` | NEW — `BackupStatus` enum, `FileEntry`, `KDFParams`, `SQLCipherMeta`, `BackupManifest` (with `to_dict()`), `BackupResult`, GFS constants (5/4/3) |
| `packages/infrastructure/src/zorivest_infra/backup/backup_manager.py` | NEW — `BackupManager` (create_backup lifecycle, _create_snapshot via sqlite3.backup(), _package_backup with pyzipper AES, _derive_key with PBKDF2, _rotate_backups GFS, _verify_backup, list_backups) |
| `packages/infrastructure/pyproject.toml` | MODIFIED — added pyzipper dependency |
| `tests/unit/test_backup_manager.py` | NEW — 17 tests |

- Design notes:
  - `_create_snapshot()` uses Python 3.7+ `connection.backup()` for Online Backup API — safe for WAL
  - Key derivation uses PBKDF2-HMAC-SHA256 as foundation; Argon2id swap planned when argon2-cffi added
  - Domain separation via salt concatenation with `b"zorivest-backup-v1"`
  - Manifest matches spec schema exactly (app_id, backup_format_version, kdf, files with sha256, sqlcipher metadata)
  - GFS rotation: newest 5 daily + 1 per unique week (4 weeks) + 1 per unique month (3 months)
  - Post-backup verification re-derives key from manifest salt and reads back from encrypted ZIP

- Commands run: `uv add --package zorivest-infra pyzipper`, `uv run pytest tests/unit/test_backup_manager.py -v`, `uv run python -c "import pyzipper; print(pyzipper.__version__)"`
- Results: 17 passed / 0 failed, pyzipper 0.3.6 installed

## Tester Output

- Commands run: `uv run pytest tests/unit/test_backup_manager.py -v --tb=short`
- Pass/fail matrix: 17 passed / 0 failed / 0 skipped
- Test mapping:
  - **BackupManifest** (2): to_dict serialization, defaults (app_id, version, empty files)
  - **BackupResult** (2): success with files_backed_up, failed with error message
  - **KDFParams** (2): defaults (argon2id, domain), to_dict serialization
  - **SQLCipherMeta** (2): defaults (major=4, page=4096), to_dict with pragmas
  - **GFS Constants** (1): 5 daily, 4 weekly, 3 monthly
  - **Snapshot** (1): creates valid SQLite DB copy with data preserved
  - **CreateBackup** (5): full lifecycle success, manifest contains files, encrypted ZIP readable, no-DB failure, snapshot cleanup after packaging
  - **ListBackups** (1): returns sorted by mtime descending
  - **GFSRotation** (1): no rotation when under daily limit
- FAIL_TO_PASS: RED phase confirmed (import errors before pyzipper install and implementation)
- Negative cases: missing database returns FAILED status, empty backup dir
- Contract verification: manifest schema matches spec §2A.3 L504-539, AES encryption verified, GFS constants match spec

## Reviewer Output

- Findings by severity: Pending Codex review
- Verdict: pending
- Anti-deferral scan: `rg "TODO|FIXME|NotImplementedError" packages/infrastructure/src/zorivest_infra/backup/backup_manager.py packages/infrastructure/src/zorivest_infra/backup/backup_types.py` → 0 matches

## Guardrail Output (If Required)

- Not applicable — no high-risk changes

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status: Implementation complete, awaiting Codex validation
- Next steps: Codex validates tests, encryption logic, manifest schema, GFS rotation → verdict
