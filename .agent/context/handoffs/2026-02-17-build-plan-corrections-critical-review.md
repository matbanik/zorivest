# Handoff: Build Plan Corrections — Critical Review Findings

**Date**: 2026-02-17  
**Task**: Correct 7 findings from critical review of backup/restore build plan  
**Predecessor**: `2026-02-18-build-plan-backup-restore-defaults-critical-review.md`

---

## What Was Done

All 7 findings from the critical review were corrected across 6 files:

| # | Severity | Finding | Fix | Files |
|---|----------|---------|-----|-------|
| F1 | Critical | Passphrase UX gap — GUI has no passphrase input for restore/verify | Backup uses session-held passphrase; removed per-call parameter from endpoints; added session auth note to GUI behavior | `02a`, `06f` |
| F2 | High | Settings key drift — `display.use_percent_mode` (bool) vs `display.percent_mode` (string) | Canonicalized to `display.percent_mode` (string, "daily") everywhere | `06f`, `input-index` |
| F3 | High | Import validation weaker than export — missing sensitivity check | Created shared `_is_portable()` predicate; added `test_import_rejects_sensitive_keys` | `02a` |
| F4 | High | Typed resolver values vs string-only API/MCP boundary | Added wire-type rules table; qualified MCP convention; added `ResolvedSettingResponse` model | `02a`, `05`, `04` |
| F5 | Medium | Overview dependency graph missing Phase 2A | Updated Phase 3 dep to `1, 2, 2A`; inserted Phase 2A box in ASCII diagram | `00` |
| F6 | Medium | Duplicate `6f.5` section numbering | Renumbered Logging from `6f.5` → `6f.4` | `06f` |
| F7 | Low | Outputs statement only mentions `PUT /settings` | Listed all consumed endpoints | `06f` |

## Design Decisions

1. **Session passphrase**: Backup verify/restore reuse the session-unlocked passphrase injected at app boot — no second prompt needed. GUI shows re-auth modal if session expired.
2. **Wire-type split**: `GET/PUT /settings` stays string-only (MCP convention); `/settings/resolved` and `/config/*` use typed JSON values.
3. **Import security**: Symmetric with export — both use `_is_portable()` checking `exportable AND sensitivity == NON_SENSITIVE`.

## Files Modified

- `docs/build-plan/02a-backup-restore.md` — F1, F3, F4
- `docs/build-plan/06f-gui-settings.md` — F1, F2, F6, F7
- `docs/build-plan/00-overview.md` — F5
- `docs/build-plan/05-mcp-server.md` — F4
- `docs/build-plan/04-rest-api.md` — F4
- `docs/build-plan/input-index.md` — F2

## Verification

```
✅ No duplicate section numbers in 06f (6f.4, 6f.5, 6f.6, 6f.7)
✅ No passphrase.*Body in 02a backup endpoints
✅ Phase 3 dep includes 2A in overview
✅ display.percent_mode canonical as string everywhere
✅ input-index.md percent_mode type corrected to string
```

## Next Steps

- Proceed with code implementation per the corrected build plan
- Phase 2A should be built after Phase 2 and before Phase 3
