# Handoff: Backup/Restore & Settings Defaults Build Plan

**Date**: 2026-02-17
**Task**: Add backup/restore, JSON config export/import, and application defaults to build plan
**Status**: ✅ Complete — all documentation changes implemented
**Owner Role**: coder (documentation)

---

## What Was Done

### Research Phase
- 3 Tavily advanced web searches (SQLCipher backup, settings patterns, Electron config)
- 1 OpenAI GPT-5.2 research query (comprehensive architectural analysis)
- Key findings synthesized into architectural decisions

### Documentation Changes

| File | Change |
|------|--------|
| **`02a-backup-restore.md`** | **NEW** — Full Phase 2A spec: encrypted backup, settings resolver, JSON config export |
| `00-overview.md` | Added Phase 2A row to phase table + cross-reference (74 items) |
| `02-infrastructure.md` | Added `AppDefaultModel` table alongside `SettingModel` |
| `03-service-layer.md` | Added `SettingsService`, `BackupService`, `ConfigExportService` to outputs |
| `04-rest-api.md` | Added cross-reference to Phase 2A endpoints |
| `06f-gui-settings.md` | Added Backup/Restore page (6f.5), Config Export/Import (6f.6), Reset to Default (6f.7) |
| `build-priority-matrix.md` | Added items 10a-10e (P0) + 35d-35f (P2), total 68→74 |
| `dependency-manifest.md` | Added `pyzipper` to Phase 2A |

---

## Key Architectural Decisions

1. **Back up ciphertext files** via SQLite Online Backup API — no decryption during backup
2. **AES-encrypted ZIP** via `pyzipper` with domain-separated Argon2id key derivation
3. **Self-contained manifest.json** inside backup with file hashes and KDF params
4. **Two-table model**: `app_defaults` (migration-seeded) + `user_settings` (user overrides)
5. **Three-tier resolver**: user → default → hardcoded, returns source metadata
6. **Allowlist-based JSON export**: only `exportable=true` + `NON_SENSITIVE` keys

---

## Next Steps

- No immediate follow-up needed — these are build plan docs, not code
- Code implementation follows the phased build order (Phase 2A after Phase 2)
- When Phase 2 (Infrastructure) is complete, Phase 2A items can begin

---

## Blockers / Risks

None identified.
