---
project: "2026-05-05-calculator-validation-ux"
source: "docs/execution/plans/2026-05-05-calculator-validation-ux/implementation-plan.md"
meus: ["MEU-204", "MEU-205", "MEU-206"]
status: "complete"
template_version: "2.0"
---

# Task — Calculator & Validation UX Hardening

> **Project:** `2026-05-05-calculator-validation-ux`
> **Type:** GUI
> **Estimate:** 7 files changed

## Task Table

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 1 | Add inline validation errors (red required messages) to TradePlanPage | coder | `TradePlanPage.tsx` — fieldErrors state + red messages for ticker/strategy_name | `npx vitest run` — 630 pass | `[x]` |
| 2 | Add inline validation errors to WatchlistPage | coder | `WatchlistPage.tsx` — fieldErrors state + red message for name | `npx vitest run` — 630 pass | `[x]` |
| 3 | Add balance required validation to AccountDetailPanel | coder | `AccountDetailPanel.tsx` — balance save shows required error | `npx vitest run` — 630 pass | `[x]` |
| 4 | Add `isFormInvalid` to useFormGuard hook + disable Save & Continue | coder | `useFormGuard.ts`, `SchedulingLayout.tsx` — button disabled when invalid | `npx vitest run` — useFormGuard tests pass | `[x]` |
| 5 | Implement calculator plan picker dropdown | coder | `PositionCalculatorModal.tsx` — searchable plan picker | `npx vitest run` — 630 pass | `[x]` |
| 6 | Add toggle switches for field copying with localStorage persistence | coder | `PositionCalculatorModal.tsx` — 6 toggles, localStorage save/load | `npx vitest run` — 630 pass | `[x]` |
| 7 | Toggle 3×2 grid layout with title + green/red colors + copying status | coder | `PositionCalculatorModal.tsx` — grid layout, color states, status text | `npx vitest run` — 630 pass | `[x]` |
| 8 | Apply to Plan closes modal + auto-sized centered button | coder | `PositionCalculatorModal.tsx` — onClose after dispatch, remove w-full | `npx vitest run` — 630 pass | `[x]` |
| 9 | Auto-save new plans before opening calculator | coder | `TradePlanPage.tsx` — async handleCalculatePosition with POST + refetch | `npx vitest run` — 630 pass | `[x]` |
| 10 | Trade Plan 4-column price grid + computed metrics row | coder | `TradePlanPage.tsx` — grid-cols-4 price row, metrics row | `npx vitest run` — 630 pass | `[x]` |
| 11 | Auto-recalculate position_size on shares/entry change | coder | `TradePlanPage.tsx` — useEffect for position_size | `npx vitest run` — 630 pass | `[x]` |
| 12 | Move calculator button to centered action row | coder | `TradePlanPage.tsx` — centered row below inputs | `npx vitest run` — 630 pass | `[x]` |
| 13 | Run TypeScript type check | tester | Clean `tsc --noEmit` | `npx tsc --noEmit` — 0 errors | `[x]` |
| 14 | Update `docs/BUILD_PLAN.md` — add P2.3 section + MEU-204/205/206 | orchestrator | New section in BUILD_PLAN.md | `rg "MEU-204" docs/BUILD_PLAN.md` — 3 matches ✅ | `[x]` |
| 15 | Update `.agent/context/meu-registry.md` — add MEU-204/205/206 | orchestrator | 3 new rows in registry | `rg "MEU-204" .agent/context/meu-registry.md` — 1 match ✅ | `[x]` |
| 16 | Save session state to pomera_notes | orchestrator | `Memory/Session/Zorivest-calculator-validation-ux-2026-05-05` — Note ID 1067 | MCP: `pomera_notes(action="search", search_term="Zorivest-calculator*")` returns ≥1 result ✅ | `[x]` |
| 17 | Create handoff | reviewer | `.agent/context/handoffs/2026-05-05-calculator-validation-ux-handoff.md` | `Test-Path` → True ✅ | `[x]` |
| 18 | Create reflection | orchestrator | `docs/execution/reflections/2026-05-05-calculator-validation-ux-reflection.md` | `Test-Path` → True ✅ | `[x]` |

### Status Legend

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Not started |
| `[/]` | In progress |
| `[x]` | Complete |
| `[B]` | Blocked (must link follow-up) |
