---
project: "2026-05-02-gui-ux-hardening"
source: "docs/execution/plans/2026-05-02-gui-ux-hardening/implementation-plan.md"
meus: ["MEU-196", "MEU-197", "MEU-198"]
status: "complete"
template_version: "2.0"
---

# Task — GUI UX Hardening: Unsaved Changes Guard

> **Project:** `2026-05-02-gui-ux-hardening`
> **Type:** GUI
> **Estimate:** ~25 files changed

## Task Table

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 1 | Write `useFormGuard` hook tests (AC-1→AC-5) | tester | `ui/src/renderer/src/hooks/__tests__/useFormGuard.test.ts` | `cd ui; npx vitest run src/renderer/src/hooks/__tests__/useFormGuard.test.ts *> C:\Temp\zorivest\vitest-hook.txt; Get-Content C:\Temp\zorivest\vitest-hook.txt` — all RED | `[x]` |
| 2 | Write `UnsavedChangesModal` tests (AC-6→AC-9) | tester | `ui/src/renderer/src/components/__tests__/UnsavedChangesModal.test.tsx` | `cd ui; npx vitest run src/renderer/src/components/__tests__/UnsavedChangesModal.test.tsx *> C:\Temp\zorivest\vitest-modal.txt; Get-Content C:\Temp\zorivest\vitest-modal.txt` — all RED | `[x]` |
| 3 | Implement `useFormGuard<T>` hook | coder | `ui/src/renderer/src/hooks/useFormGuard.ts` | `cd ui; npx vitest run src/renderer/src/hooks/__tests__/useFormGuard.test.ts *> C:\Temp\zorivest\vitest-hook-green.txt; Get-Content C:\Temp\zorivest\vitest-hook-green.txt` — all GREEN | `[x]` |
| 4 | Implement `UnsavedChangesModal` component | coder | `ui/src/renderer/src/components/UnsavedChangesModal.tsx` | `cd ui; npx vitest run src/renderer/src/components/__tests__/UnsavedChangesModal.test.tsx *> C:\Temp\zorivest\vitest-modal-green.txt; Get-Content C:\Temp\zorivest\vitest-modal-green.txt` — all GREEN | `[x]` |
| 5 | Create `form-guard.css` with amber-pulse animation (AC-10, AC-11) | coder | `ui/src/renderer/src/styles/form-guard.css` | `rg "amber-pulse" ui/src/renderer/src/styles/form-guard.css *> C:\Temp\zorivest\css-check.txt; Get-Content C:\Temp\zorivest\css-check.txt` | `[x]` |
| 6 | Add `UNSAVED_CHANGES` constants to `ui/tests/e2e/test-ids.ts` | coder | Updated `test-ids.ts` lines 225-230 with modal + button test-ids | `rg "UNSAVED_CHANGES" ui/tests/e2e/test-ids.ts` — matches found | `[x]` |
| 7 | ~~Refactor `SchedulingLayout.tsx` to consume shared components~~ | coder | Superseded by task 7a → restored by corrections (F2) | N/A | `[x]` |
| 7a | ~~Inline modal~~ → Refactored to shared `useFormGuard` + `UnsavedChangesModal` (F2 correction) + `forwardRef`/`useImperativeHandle` + amber-pulse + aria-labels (F3a) + `Save Changes •` dirty text (F3b) | coder | `PolicyDetail.tsx`, `EmailTemplateDetail.tsx`, `SchedulingLayout.tsx`, `UnsavedChangesModal.tsx`, + 7 save buttons updated | `cd ui; npx tsc --noEmit` clean, `npx vitest run` 499 passed | `[x]` |
| 8 | Write Playwright E2E dirty-guard test for Scheduling (extend Wave 8) | tester | `ui/tests/e2e/scheduling.test.ts` — dirty-guard test: modify JSON editor → switch policy → UnsavedChangesModal → Keep Editing. **1 passed (7.1s)** | `npx playwright test scheduling.test.ts --grep dirty-guard` — 1 passed | `[x]` |
| 9 | MEU-196 gate | tester | **8/8 blocking checks PASSED** (pyright, ruff, pytest, tsc, eslint, vitest, anti-placeholder, anti-deferral) | `uv run python tools/validate_codebase.py --scope meu` — exit 0, all pass | `[x]` |
| 10 | Write MarketDataProvidersPage guard + "Disabled" label tests (AC-14→AC-18) | tester | Updated `MarketDataProvidersPage.test.tsx` — 8 new G22 tests (23 total) | `cd ui; npx vitest run src/renderer/src/features/settings/__tests__/MarketDataProvidersPage.test.tsx` — 23 GREEN | `[x]` |
| 11 | Wire `useFormGuard` to MarketDataProvidersPage + "off"→"Disabled" + amber-pulse (AC-14→AC-18) | coder | Modified `MarketDataProvidersPage.tsx` | `cd ui; npx vitest run src/renderer/src/features/settings/__tests__/MarketDataProvidersPage.test.tsx *> C:\Temp\zorivest\vitest-mktdata-green.txt; Get-Content C:\Temp\zorivest\vitest-mktdata-green.txt` — all GREEN (G18) | `[x]` |
| 12 | Write Playwright E2E dirty-guard test for Market Data (extend Wave 6) | tester | `ui/tests/e2e/settings-market-data.test.ts` — dirty-guard test: select provider → edit API key → switch → UnsavedChangesModal → Discard. **1 passed (5.7s)** | `npx playwright test settings-market-data.test.ts --grep dirty-guard` — 1 passed | `[x]` |
| 13 | MEU-197 gate | tester | **8/8 blocking checks PASSED** (shared gate with MEU-196/198 — single `--scope meu` run covers all) | `uv run python tools/validate_codebase.py --scope meu` — exit 0, all pass | `[x]` |
| 14 | Write AccountDetailPanel guard tests (AC-20→AC-21) — btn-save-dirty + onDirtyChange callback | tester | Updated `AccountDetailPanel.test.tsx` — 3 new G22 tests (14 total) | `cd ui; npx vitest run src/renderer/src/features/accounts/` — 14 GREEN | `[x]` |
| 15 | Wire `useFormGuard` to AccountsHome + `forwardRef`/`useImperativeHandle` on AccountDetailPanel + amber-pulse + `onSave` (AC-20→AC-21) | coder | Modified `AccountsHome.tsx`, `AccountDetailPanel.tsx` | `cd ui; npx vitest run src/renderer/src/features/accounts/ *> C:\Temp\zorivest\vitest-acct-green.txt; Get-Content C:\Temp\zorivest\vitest-acct-green.txt` — all GREEN | `[x]` |
| 16 | Write TradeDetailPanel guard tests (AC-22→AC-23) — btn-save-dirty + onDirtyChange callback | tester | Updated `trades.test.tsx` — 3 new G22 tests (56 total) | `cd ui; npx vitest run src/renderer/src/features/trades/` — 56 GREEN | `[x]` |
| 17 | Wire `useFormGuard` to TradesLayout + `forwardRef`/`useImperativeHandle` on TradeDetailPanel + amber-pulse + `onSave` (AC-22→AC-23) | coder | Modified `TradesLayout.tsx`, `TradeDetailPanel.tsx` | `cd ui; npx vitest run src/renderer/src/features/trades/ *> C:\Temp\zorivest\vitest-trades-green.txt; Get-Content C:\Temp\zorivest\vitest-trades-green.txt` — all GREEN | `[x]` |
| 18 | Write TradePlanPage guard tests (AC-24→AC-25) — btn-save-dirty + guard modal on dirty switch | tester | Updated `planning.test.tsx` — 4 new G22 tests (88 total) | `cd ui; npx vitest run src/renderer/src/features/planning/` — 88 GREEN | `[x]` |
| 19 | Wire `useFormGuard` to TradePlanPage + amber-pulse + `onSave` (AC-24→AC-25) | coder | Modified `TradePlanPage.tsx` | `cd ui; npx vitest run src/renderer/src/features/planning/ *> C:\Temp\zorivest\vitest-plan-green.txt; Get-Content C:\Temp\zorivest\vitest-plan-green.txt` — all GREEN | `[x]` |
| 20 | Write WatchlistPage guard tests (AC-26→AC-27) — btn-save-dirty + guard modal on dirty switch | tester | Updated `planning.test.tsx` — 2 new G22 tests (88 total) | `cd ui; npx vitest run src/renderer/src/features/planning/` — 88 GREEN | `[x]` |
| 21 | Wire `useFormGuard` to WatchlistPage + amber-pulse + `onSave` (AC-26→AC-27) | coder | Modified `WatchlistPage.tsx` | `cd ui; npx vitest run src/renderer/src/features/planning/ *> C:\Temp\zorivest\vitest-wl-green.txt; Get-Content C:\Temp\zorivest\vitest-wl-green.txt` — all GREEN | `[x]` |
| 22 | Write Playwright E2E dirty-guard tests for Accounts (Wave 2) + Trade Plans (Wave 4) | tester | `ui/tests/e2e/account-crud.test.ts` — dirty-guard test: create 2 accounts → edit name → switch → UnsavedChangesModal → Keep Editing. **1 passed (5.5s)**. `ui/tests/e2e/position-size.test.ts` — Wave 4 dirty-guard test: create plan via API → edit → switch → UnsavedChangesModal → Keep Editing (added in R1 corrections, 2026-05-03). | `npx playwright test account-crud.test.ts --grep dirty-guard` — 1 passed; `npx playwright test position-size.test.ts` — TSC-validated | `[x]` |
| 23 | MEU-198 gate | tester | **8/8 blocking checks PASSED** (shared gate with MEU-196/197 — single `--scope meu` run covers all) | `uv run python tools/validate_codebase.py --scope meu` — exit 0, all pass | `[x]` |
| 24 | Run full Vitest suite — all tests GREEN | tester | 31 files, 522 tests passed (519 + 3 G23 EmailSettingsPage dirty-state tests) | `cd ui; npx vitest run` — 522 passed | `[x]` |
| 25 | Run TypeScript build gate | tester | 0 errors | `cd ui; npx tsc --noEmit` — clean | `[x]` |
| 26 | Anti-placeholder scan | tester | 0 matches | `rg` — no output | `[x]` |
| 27 | Audit `docs/BUILD_PLAN.md` for stale refs | orchestrator | P2.1 row present | `rg "MEU-196"` — 1 match | `[x]` |
| 28 | Update MEU registry status | orchestrator | MEU-196/197/198 → 🔄 impl done | Updated `meu-registry.md` lines 411-413 | `[x]` |
| 29 | Save session state to pomera_notes | orchestrator | Note ID 1056 | `pomera_notes` search confirms | `[x]` |
| 30 | Create handoff | reviewer | `.agent/context/handoffs/2026-05-02-gui-ux-hardening-handoff.md` | Created | `[x]` |
| 31 | Create reflection | orchestrator | `docs/execution/reflections/2026-05-02-gui-ux-hardening-reflection.md` | Created | `[x]` |
| 32 | Append metrics row | orchestrator | Row 71 in `docs/execution/metrics.md` | Appended | `[x]` |
| 33 | Wire `isDirty` + amber-pulse to EmailSettingsPage (Human-approved mid-execution scope expansion — visual only, no `useFormGuard`/modal) | coder | Modified `EmailSettingsPage.tsx` — save button dirty class + 3 G23 unit tests | `cd ui; npx vitest run src/renderer/src/features/settings/` — all GREEN | `[x]` |

### Status Legend

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Not started |
| `[/]` | In progress |
| `[x]` | Complete |
| `[B]` | Blocked (must link follow-up) |
