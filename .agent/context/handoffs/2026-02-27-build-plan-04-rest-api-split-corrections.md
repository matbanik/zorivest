# Corrections Handoff: REST API Split

## Task

- **Date:** 2026-02-27
- **Task slug:** build-plan-04-rest-api-split-corrections
- **Owner role:** coder → tester → reviewer
- **Scope:** Fix 7 findings from critical review of `04*.md` split

## Findings Applied

| # | Sev | Finding | Files Changed |
|---|-----|---------|---------------|
| H1 | High | Fixed 5 broken consumer-note links (`05a-mcp-core.md` → `05a-mcp-zorivest-settings.md`, `06c-gui-auth.md` → `06a-gui-shell.md`, etc.) | `04a`, `04c`, `04d`, `04e`, `04g` |
| H2 | High | Added 7 missing routers to hub manifest (broker, banking, import, mistakes, fees, calculator, system) | `04-rest-api.md` |
| M1 | Med | Updated 12 stale `Step 4.x` / `§4.x` references → specific sub-file links | `mcp-planned-readiness.md`, `input-index.md`, `06f-gui-settings.md` |
| M2 | Med | Added Phase 2A route inventory table (9 routes) to `04d-api-settings.md` | `04d-api-settings.md` |
| M3 | Med | Added health/status/graceful-shutdown route specs + tests to `04g-api-system.md` | `04g-api-system.md` |
| L1 | Low | Normalized 2 package paths (`zorivest_server` → `zorivest_api`) and 2 tag cases (`Accounts`/`Calculator` → lowercase) | `04b`, `04e` |

## Verification Results

| Check | Command | Result |
|-------|---------|--------|
| H1: No broken link targets | `rg "05a-mcp-core\|05b-mcp-settings\|06c-gui-auth\|06e-gui-analytics\|06h-gui-system" docs/build-plan/04*.md` | ✅ 0 matches |
| H2: Router manifest count | `rg "include_router" docs/build-plan/04-rest-api.md \| Measure-Object -Line` | ✅ 19 routers |
| M1: No stale Step refs | `rg "Step 4\.[0-9]\|§4\.[0-9]" docs/build-plan/mcp-planned-readiness.md docs/build-plan/input-index.md docs/build-plan/06f-gui-settings.md` | ✅ 0 matches |
| L1: No capitalized tags | `rg 'tags=\["[A-Z]' docs/build-plan/04*.md` | ✅ 0 matches |
| L1: No zorivest_server paths | `rg "zorivest_server" docs/build-plan/04*.md` | ✅ 0 matches |

## Approval Gate

- **Human approval required:** yes
- **Approval status:** complete (findings resolved)
