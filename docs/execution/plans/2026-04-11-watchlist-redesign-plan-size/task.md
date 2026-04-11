---
project: "2026-04-11-watchlist-redesign-plan-size"
source: "docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/implementation-plan.md"
meus: ["MEU-70a"]
status: "approved"
template_version: "2.0"
---

# Task — Watchlist Visual Redesign + Plan Size Propagation

> **Project:** `2026-04-11-watchlist-redesign-plan-size`
> **Type:** Domain | API | MCP | GUI
> **Estimate:** ~16 files changed (6 new, 10 modified)

## Task Table

### Sub-MEU A: PLAN-NOSIZE — Backend + MCP (TDD)

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 1 | Write backend tests for `position_size` round-trip (Red) | tester | `test_api_plans.py` — tests fail | `uv run pytest tests/unit/test_api_plans.py -x --tb=short -v *> C:\Temp\zorivest\pytest-plans-red.txt; Get-Content C:\Temp\zorivest\pytest-plans-red.txt \| Select-Object -Last 40` | `[x]` |
| 2 | Add `position_size` to TradePlan entity | coder | `entities.py` updated | `uv run pyright packages/core *> C:\Temp\zorivest\pyright-core.txt; Get-Content C:\Temp\zorivest\pyright-core.txt \| Select-Object -Last 20` | `[x]` |
| 3 | Add `position_size` column to TradePlanModel | coder | `models.py` updated | `uv run pyright packages/infrastructure *> C:\Temp\zorivest\pyright-infra.txt; Get-Content C:\Temp\zorivest\pyright-infra.txt \| Select-Object -Last 20` | `[x]` |
| 4 | Add ALTER TABLE migration for `position_size` | coder | `main.py` migration list updated | Manual: verify column exists after startup | `[x]` |
| 5 | Add `position_size` to API schemas + `_to_response()` | coder | `plans.py` Create/Update/Response updated | `uv run pytest tests/unit/test_api_plans.py -x --tb=short -v *> C:\Temp\zorivest\pytest-plans-green.txt; Get-Content C:\Temp\zorivest\pytest-plans-green.txt \| Select-Object -Last 40` | `[x]` |
| 6 | Add `shares_planned` + `position_size` to MCP `create_trade_plan` | coder | `planning-tools.ts` schema + body updated | `cd p:\zorivest\mcp-server; npm run build *> C:\Temp\zorivest\mcp-build.txt; Get-Content C:\Temp\zorivest\mcp-build.txt \| Select-Object -Last 20` | `[x]` |
| 7 | Regenerate OpenAPI spec | coder | `openapi.committed.json` updated | `uv run python tools/export_openapi.py --check openapi.committed.json *> C:\Temp\zorivest\openapi.txt; Get-Content C:\Temp\zorivest\openapi.txt` | `[x]` |

### Sub-MEU B: Watchlist Visual Redesign (TDD)

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 8 | Write test asserting `ui.watchlist.colorblind_mode` exists in SETTINGS_REGISTRY (Red) | tester | `test_settings_registry.py` — new test fails | `uv run pytest tests/unit/test_settings_registry.py -x --tb=short -v *> C:\Temp\zorivest\pytest-settings-red.txt; Get-Content C:\Temp\zorivest\pytest-settings-red.txt \| Select-Object -Last 20` | `[x]` |
| 9 | Register `ui.watchlist.colorblind_mode` in `SETTINGS_REGISTRY` (Green) | coder | `settings.py` updated — test passes | `uv run pytest tests/unit/test_settings_registry.py -x --tb=short -v *> C:\Temp\zorivest\pytest-settings-green.txt; Get-Content C:\Temp\zorivest\pytest-settings-green.txt \| Select-Object -Last 20` | `[x]` |
| 10 | Write tests for watchlist utilities (Red) | tester | `watchlist-utils.test.ts` — all tests fail | `cd p:\zorivest\ui; npx vitest run src/renderer/src/features/planning/__tests__/watchlist-utils.test.ts *> C:\Temp\zorivest\vitest-utils-red.txt; Get-Content C:\Temp\zorivest\vitest-utils-red.txt \| Select-Object -Last 30` | `[x]` |
| 11 | Create `watchlist-utils.ts` formatting utilities (Green) | coder | formatVolume, formatPrice, getChangeColor, formatFreshness — all tests pass | `cd p:\zorivest\ui; npx vitest run src/renderer/src/features/planning/__tests__/watchlist-utils.test.ts *> C:\Temp\zorivest\vitest-utils-green.txt; Get-Content C:\Temp\zorivest\vitest-utils-green.txt \| Select-Object -Last 30` | `[x]` |
| 12 | Create `watchlist-tokens.css` design tokens | coder | New CSS file with dark palette variables | `Test-Path p:\zorivest\ui\src\renderer\src\styles\watchlist-tokens.css` | `[x]` |
| 13 | Create `WatchlistTable.tsx` component | coder | Professional data table with all columns | `cd p:\zorivest\ui; npx tsc --noEmit *> C:\Temp\zorivest\tsc-table.txt; Get-Content C:\Temp\zorivest\tsc-table.txt \| Select-Object -Last 30` | `[x]` |
| 14 | Integrate WatchlistTable into WatchlistPage | coder | New table, colorblind toggle, stagger polling | `cd p:\zorivest\ui; npx vitest run *> C:\Temp\zorivest\vitest-watchlist.txt; Get-Content C:\Temp\zorivest\vitest-watchlist.txt \| Select-Object -Last 40` | `[x]` |

### Sub-MEU C: Calculator Write-Back (TDD)

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 15 | Write tests for calculator write-back + readonly `position_size` (Red) | tester | `planning.test.tsx` — new tests fail: readonly display, calculator-apply event populate, Apply button dispatch, no-payload ignored | `cd p:\zorivest\ui; npx vitest run src/renderer/src/features/planning/__tests__/planning.test.tsx *> C:\Temp\zorivest\vitest-calc-red.txt; Get-Content C:\Temp\zorivest\vitest-calc-red.txt \| Select-Object -Last 40` | `[x]` |
| 16 | Add readonly `position_size` display to TradePlanPage (Green) | coder | Computed field in detail panel (shares_planned stays editable) | `cd p:\zorivest\ui; npx tsc --noEmit *> C:\Temp\zorivest\tsc-plan.txt; Get-Content C:\Temp\zorivest\tsc-plan.txt \| Select-Object -Last 30` | `[x]` |
| 17 | Add "Apply to Plan" button to PositionCalculatorModal (Green) | coder | Calculator dispatches `zorivest:calculator-apply` event | `cd p:\zorivest\ui; npx vitest run *> C:\Temp\zorivest\vitest-calc-green.txt; Get-Content C:\Temp\zorivest\vitest-calc-green.txt \| Select-Object -Last 40` | `[x]` |
| 18 | Wire calculator-apply event in TradePlanPage (Green) | coder | Form populates `shares_planned` (editable) + `position_size` (readonly) from calculator — all Red tests pass | `cd p:\zorivest\ui; npx vitest run src/renderer/src/features/planning/__tests__/planning.test.tsx *> C:\Temp\zorivest\vitest-wire-green.txt; Get-Content C:\Temp\zorivest\vitest-wire-green.txt \| Select-Object -Last 40` | `[x]` |

### Sub-MEU D: Post-Implementation

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 19 | Update MEU-70a status in registry + known-issues | orchestrator | meu-registry.md ✅, known-issues.md [PLAN-NOSIZE] archived | `rg "MEU-70a" .agent/context/meu-registry.md` | `[x]` |
| 20 | Run full verification plan (8 checks) | tester | All checks pass (TSC, vitest 346, pytest 40, pyright 0, ruff clean, MCP build, anti-placeholder) | See implementation-plan.md §Verification Plan | `[x]` |
| 21 | Save session state to pomera_notes | orchestrator | `Memory/Session/Zorivest-watchlist-redesign-plan-size-2026-04-11` (ID: 797) | pomera search ≥1 result | `[x]` |
| 22 | Create handoff | reviewer | `.agent/context/handoffs/111-2026-04-11-watchlist-redesign-bp06is1+PLAN-NOSIZE.md` | `Test-Path .agent/context/handoffs/111-*` | `[x]` |
| 23 | Create reflection | orchestrator | `docs/execution/reflections/2026-04-11-watchlist-redesign-reflection.md` | `Test-Path docs/execution/reflections/2026-04-11-watchlist*` | `[x]` |
| 24 | Append metrics row | orchestrator | Row appended to `docs/execution/metrics.md` | `Get-Content docs/execution/metrics.md \| Select-Object -Last 3` | `[x]` |

### Status Legend

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Not started |
| `[/]` | In progress |
| `[x]` | Complete |
| `[B]` | Blocked (must link follow-up) |
