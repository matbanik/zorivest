# Corrections Handoff: REST API Split Recheck

## Task

- **Date:** 2026-02-27
- **Task slug:** build-plan-04-rest-api-split-recheck-fixes
- **Owner role:** coder → tester → reviewer
- **Scope:** Fix 4 findings from recheck + canonical route registry

## Findings Applied

| # | Sev | Finding | Files Changed |
|---|-----|---------|---------------|
| F1 | High | Namespace drift: `/system/*` → canonical `/health` + `/service/*` | `04g`, `04-rest-api.md` |
| F2 | High | Consumer notes: fixed tool names and 05-file ownership (5 sub-files) | `04a`, `04b`, `04e`, `04f`, `04g` |
| F3 | Med | Missing round-trip route: added `GET /api/v1/round-trips` spec + tests | `04a`, `04-rest-api.md` |
| F4 | Med | Guard pre-unlock: `GET /mcp-guard/status` now accessible before unlock | `04g` |
| — | — | Canonical Route Contract Registry (38 routes × 6 columns) | `04-rest-api.md` |

## Verification Results

| Check | Command | Result |
|-------|---------|--------|
| F1: No `/api/v1/system` in 04 files | `rg "/api/v1/system" docs/build-plan/04*.md` | ✅ 0 matches |
| F1: No `system_router` in hub | `rg "system_router" docs/build-plan/04-rest-api.md` | ✅ 0 matches |
| F2: No stale `record_quarterly_payment` | `rg "record_quarterly_payment[^s]" docs/build-plan/04f-api-tax.md` | ✅ 0 matches |
| F3: Round-trips in 04a + hub | `rg "round-trips" docs/build-plan/04a-api-trades.md docs/build-plan/04-rest-api.md` | ✅ Present |
| F4: Guard test split | Visual confirmation: status 200 pre-unlock, lock/unlock 403 | ✅ |
| Route registry present | `rg "Route Contract Registry" docs/build-plan/04-rest-api.md` | ✅ L130 |
