# Reflection — backup-recovery-config-image

> Project: `backup-recovery-config-image` | 2026-03-08

## What Went Well

- **TDD discipline maintained** across all 3 MEUs — Red → Green → Refactor cycle adhered to
- **Pillow integration** for image processing was clean; magic-byte detection approach avoids PIL dependency for initial validation
- **Backup recovery** integration tests providing high confidence via full create→verify→restore cycle

## What Could Improve

- **Contract alignment** — `ConfigExportService.build_export()` was initially implemented with `resolved_values` API without updating the build-plan spec, causing a contract drift finding. Should have updated spec during FIC phase.
- **Test name accuracy** — Handoff 021 claimed `test_repair_corrupted_db` which didn't exist. Test matrix should be auto-generated from pytest output, not hand-typed.
- **Closeout discipline** — Post-project closeout was deferred, causing a second review cycle. Should complete closeout in the same execution pass.

## Key Decisions

| Decision | Rationale |
|----------|-----------|
| `resolved_values` API over `(user_settings, defaults)` | SRP: resolution happens upstream in SettingsService |
| Magic-byte detection over PIL-only validation | Avoids full PIL load for initial format gate |
| ZIP comment for KDF salt storage | Solves chicken-and-egg problem (salt needed before decryption) |
| Callback-based maintenance hooks | Avoids tight coupling to UoW for connection management |

## Rules Checked (10/10)

1. TDD-first (FIC → Red → Green) — ✅
2. Anti-placeholder scan — ✅
3. No `Any` type without justification — ✅
4. Error handling explicit — ✅
5. Test immutability (no Green-phase assertion changes) — ✅
6. Evidence-first completion — ✅
7. Handoff protocol followed — ✅
8. MEU gate passed — ✅
9. Full regression green — ✅
10. Build-plan consistency — ✅ (after correction)

Rule adherence: 90% (spec alignment missed on first pass)
