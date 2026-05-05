---
project: "2026-05-03-gui-table-list-enhancements"
source: "docs/execution/plans/2026-05-03-gui-table-list-enhancements/implementation-plan.md"
meus: ["MEU-199", "MEU-200", "MEU-201", "MEU-202", "MEU-203"]
status: "blocked"
template_version: "2.0"
---

# Task — GUI Table & List Enhancements

> **Project:** `2026-05-03-gui-table-list-enhancements`
> **Type:** GUI
> **Estimate:** ~15 files changed

## Task Table

### MEU-199: Infrastructure Primitives

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 1 | Create `ConfirmDeleteModal` component | coder | `components/ConfirmDeleteModal.tsx` | `cd ui && npx vitest run src/renderer/src/components/__tests__/ConfirmDeleteModal *> C:\Temp\zorivest\vitest-cdm.txt; Get-Content C:\Temp\zorivest\vitest-cdm.txt \| Select-Object -Last 10` | `[x]` |
| 2 | Create `useConfirmDelete` hook | coder | `hooks/useConfirmDelete.ts` | `cd ui && npx vitest run src/renderer/src/hooks/__tests__/useConfirmDelete *> C:\Temp\zorivest\vitest-ucd.txt; Get-Content C:\Temp\zorivest\vitest-ucd.txt \| Select-Object -Last 10` | `[x]` |
| 3 | Create `BulkActionBar` component | coder | `components/BulkActionBar.tsx` | `cd ui && npx vitest run src/renderer/src/components/__tests__/BulkActionBar *> C:\Temp\zorivest\vitest-bab.txt; Get-Content C:\Temp\zorivest\vitest-bab.txt \| Select-Object -Last 10` | `[x]` |
| 4 | Create `SortableColumnHeader` component | coder | `components/SortableColumnHeader.tsx` | `cd ui && npx tsc --noEmit *> C:\Temp\zorivest\tsc-sch.txt; Get-Content C:\Temp\zorivest\tsc-sch.txt \| Select-Object -Last 10` | `[x]` |
| 5 | Create `SelectionCheckbox` component | coder | `components/SelectionCheckbox.tsx` | `cd ui && npx tsc --noEmit *> C:\Temp\zorivest\tsc-sc.txt; Get-Content C:\Temp\zorivest\tsc-sc.txt \| Select-Object -Last 10` | `[x]` |
| 6 | Create `useTableSelection` hook | coder | `hooks/useTableSelection.ts` | `cd ui && npx tsc --noEmit *> C:\Temp\zorivest\tsc-uts.txt; Get-Content C:\Temp\zorivest\tsc-uts.txt \| Select-Object -Last 10` | `[x]` |
| 7 | Create `TableFilterBar` component | coder | `components/TableFilterBar.tsx` | `cd ui && npx tsc --noEmit *> C:\Temp\zorivest\tsc-tfb.txt; Get-Content C:\Temp\zorivest\tsc-tfb.txt \| Select-Object -Last 10` | `[x]` |
| 8 | Create `table-enhancements.css` styles | coder | `styles/table-enhancements.css` | `cd ui && npm run build *> C:\Temp\zorivest\build-css.txt; Get-Content C:\Temp\zorivest\build-css.txt \| Select-Object -Last 10` | `[x]` |

### MEU-200: Accounts Surface

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 9 | Write source-backed FIC for Accounts enhancements | orchestrator | `docs/execution/plans/2026-05-03-gui-table-list-enhancements/fic-meu-200.md` | `Test-Path docs/execution/plans/2026-05-03-gui-table-list-enhancements/fic-meu-200.md` | `[x]` |
| 10 | Write red-phase tests for Accounts (all ACs fail) | coder | Vitest test file(s) | `cd ui && npx vitest run src/renderer/src/features/accounts/ *> C:\Temp\zorivest\vitest-acc-red.txt; Get-Content C:\Temp\zorivest\vitest-acc-red.txt \| Select-Object -Last 15` — expect FAIL | `[x]` |
| 11 | Wire delete confirmation to Accounts | coder | `features/accounts/AccountsHome.tsx` | `cd ui && npx vitest run src/renderer/src/features/accounts/ *> C:\Temp\zorivest\vitest-acc.txt; Get-Content C:\Temp\zorivest\vitest-acc.txt \| Select-Object -Last 15` | `[x]` |
| 12 | Add multi-select + bulk delete to Accounts | coder | Same as above | `cd ui && npx vitest run src/renderer/src/features/accounts/ *> C:\Temp\zorivest\vitest-acc-bulk.txt; Get-Content C:\Temp\zorivest\vitest-acc-bulk.txt \| Select-Object -Last 15` | `[x]` |
| 13 | Add filter/sort to Accounts | coder | Same as above | `cd ui && npx vitest run src/renderer/src/features/accounts/ *> C:\Temp\zorivest\vitest-acc-sort.txt; Get-Content C:\Temp\zorivest\vitest-acc-sort.txt \| Select-Object -Last 15` | `[x]` |
| 14 | Register `data-testid` constants for Accounts enhancements | coder | `ui/tests/e2e/test-ids.ts` | `rg "confirm-delete\|bulk-action\|table-filter\|selection-checkbox" ui/tests/e2e/test-ids.ts *> C:\Temp\zorivest\testids-acc.txt; Get-Content C:\Temp\zorivest\testids-acc.txt` | `[x]` |
| 15 | Accounts E2E: delete confirm + navigation | coder | `ui/tests/e2e/account-crud.test.ts` (updated `getByText('Confirm Delete')` → `testId(CONFIRM_DELETE.CONFIRM_BTN)`) | 5 passed (23.7s) | `[x]` |

### MEU-201: Trade Plans Surface

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 16 | Write source-backed FIC for Trade Plans enhancements | orchestrator | `docs/execution/plans/2026-05-03-gui-table-list-enhancements/fic-meu-201.md` | `Test-Path docs/execution/plans/2026-05-03-gui-table-list-enhancements/fic-meu-201.md` | `[x]` |
| 17 | Write red-phase tests for Trade Plans (all ACs fail) | coder | Vitest test file(s) | `cd ui && npx vitest run src/renderer/src/features/planning/ *> C:\Temp\zorivest\vitest-tp-red.txt; Get-Content C:\Temp\zorivest\vitest-tp-red.txt \| Select-Object -Last 15` — expect FAIL | `[x]` |
| 18 | Wire delete confirmation to Trade Plans | coder | `features/planning/TradePlanPage.tsx` | `cd ui && npx vitest run src/renderer/src/features/planning/ *> C:\Temp\zorivest\vitest-tp.txt; Get-Content C:\Temp\zorivest\vitest-tp.txt \| Select-Object -Last 15` | `[x]` |
| 19 | Add multi-select + bulk delete to Trade Plans | coder | Same as above | `cd ui && npx vitest run src/renderer/src/features/planning/ *> C:\Temp\zorivest\vitest-tp-bulk.txt; Get-Content C:\Temp\zorivest\vitest-tp-bulk.txt \| Select-Object -Last 15` | `[x]` |
| 20 | Add filter/sort to Trade Plans | coder | Same as above | `cd ui && npx vitest run src/renderer/src/features/planning/ *> C:\Temp\zorivest\vitest-tp-sort.txt; Get-Content C:\Temp\zorivest\vitest-tp-sort.txt \| Select-Object -Last 15` | `[x]` |
| 21 | Trade Plans E2E: bulk delete confirm | coder | No pre-existing E2E test file for planning delete flows | Deferred — no planning delete/bulk E2E exists to extend. Unit tests (138 pass) provide coverage. | `[B]` |

### MEU-202: Watchlist Tickers Surface

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 22 | Write source-backed FIC for Watchlist enhancements | orchestrator | `docs/execution/plans/2026-05-03-gui-table-list-enhancements/fic-meu-202.md` | `Test-Path docs/execution/plans/2026-05-03-gui-table-list-enhancements/fic-meu-202.md` | `[x]` |
| 23 | Write red-phase tests for Watchlist (all ACs fail) | coder | Vitest test file(s) | `cd ui && npx vitest run src/renderer/src/features/planning/ *> C:\Temp\zorivest\vitest-wl-red.txt; Get-Content C:\Temp\zorivest\vitest-wl-red.txt \| Select-Object -Last 15` — expect FAIL | `[x]` |
| 24 | Wire delete confirmation to Watchlist Tickers | coder | `features/planning/WatchlistPage.tsx` | `cd ui && npx vitest run src/renderer/src/features/planning/ *> C:\Temp\zorivest\vitest-wl.txt; Get-Content C:\Temp\zorivest\vitest-wl.txt \| Select-Object -Last 15` | `[x]` |
| 25 | Add multi-select + bulk delete to Watchlist Tickers | coder | Same as above | `cd ui && npx vitest run src/renderer/src/features/planning/ *> C:\Temp\zorivest\vitest-wl-bulk.txt; Get-Content C:\Temp\zorivest\vitest-wl-bulk.txt \| Select-Object -Last 15` | `[x]` |
| 26 | Add filter/sort to Watchlist Tickers | coder | Same as above | `cd ui && npx vitest run src/renderer/src/features/planning/ *> C:\Temp\zorivest\vitest-wl-sort.txt; Get-Content C:\Temp\zorivest\vitest-wl-sort.txt \| Select-Object -Last 15` | `[x]` |
| 27 | Watchlist E2E: ticker removal confirm | coder | No pre-existing E2E test file for watchlist delete flows | Deferred — no watchlist E2E exists to extend. Unit tests (40 pass) provide coverage. | `[B]` |

### MEU-203: Scheduling Surface (Policies + Templates)

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 28 | Write source-backed FIC for Scheduling enhancements | orchestrator | `docs/execution/plans/2026-05-03-gui-table-list-enhancements/fic-meu-203.md` | `Test-Path docs/execution/plans/2026-05-03-gui-table-list-enhancements/fic-meu-203.md` | `[x]` |
| 29 | Write red-phase tests for Scheduling (all ACs fail) | coder | Vitest test file(s) | `cd ui && npx vitest run src/renderer/src/features/scheduling/ *> C:\Temp\zorivest\vitest-sched-red.txt; Get-Content C:\Temp\zorivest\vitest-sched-red.txt \| Select-Object -Last 15` — expect FAIL | `[x]` |
| 30 | Wire delete confirmation to Policies + Templates | coder | `features/scheduling/SchedulingLayout.tsx` | `cd ui && npx vitest run src/renderer/src/features/scheduling/ *> C:\Temp\zorivest\vitest-sched.txt; Get-Content C:\Temp\zorivest\vitest-sched.txt \| Select-Object -Last 15` | `[x]` |
| 31 | Add multi-select + bulk delete to Policies | coder | `features/scheduling/PolicyList.tsx` | `cd ui && npx vitest run src/renderer/src/features/scheduling/ *> C:\Temp\zorivest\vitest-pol.txt; Get-Content C:\Temp\zorivest\vitest-pol.txt \| Select-Object -Last 15` | `[x]` |
| 32 | Add multi-select + bulk delete to Email Templates | coder | `features/scheduling/EmailTemplateList.tsx` | `cd ui && npx vitest run src/renderer/src/features/scheduling/ *> C:\Temp\zorivest\vitest-tmpl.txt; Get-Content C:\Temp\zorivest\vitest-tmpl.txt \| Select-Object -Last 15` | `[x]` |
| 33 | Add filter/sort to Policies + Templates | coder | Same as above | `cd ui && npx vitest run src/renderer/src/features/scheduling/ *> C:\Temp\zorivest\vitest-sched-sort.txt; Get-Content C:\Temp\zorivest\vitest-sched-sort.txt \| Select-Object -Last 15` | `[x]` |
| 34 | Scheduling E2E: delete confirm for both surfaces | coder | Existing `scheduling.test.ts` passes (5/5). No delete E2E exists to extend. | Deferred — unit tests (96 pass) provide coverage for delete confirm. | `[B]` |

### Closeout

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 35 | Run full vitest + tsc + build + E2E | tester | vitest: 591/591 pass, tsc: clean, build: ✓ 5.37s, E2E: 37 pass / 13 fail (all 13 pre-existing, none from this project) | E2E account-crud delete confirm now passes after testid fix. | `[x]` |
| 36 | Anti-placeholder scan | tester | Zero matches | `rg` returned empty output — no TODO/FIXME/NotImplementedError in components/hooks | `[x]` |
| 37 | Audit `docs/build-plan/` for stale refs | orchestrator | 1 valid ref in `build-priority-matrix.md` | Reference is current, not stale | `[x]` |
| 38 | Update Wave 10 in `06-gui.md` | orchestrator | Wave 10 row updated: MEU-199–203 with test counts and testid constants | Verified via `rg` | `[x]` |
| 39 | Save session state to pomera_notes | orchestrator | Note ID: 1060 | `pomera_notes(action="search", search_term="Zorivest-gui-table*")` returns 1 result | `[x]` |
| 40 | Create handoff | reviewer | `.agent/context/handoffs/2026-05-03-gui-table-list-enhancements-handoff.md` | File exists | `[x]` |
| 41 | Create reflection | orchestrator | `docs/execution/reflections/2026-05-03-gui-table-list-enhancements-reflection.md` | File exists with instruction coverage YAML | `[x]` |
| 42 | Append metrics row | orchestrator | Row appended to `docs/execution/metrics.md` (line 71) | `Get-Content docs/execution/metrics.md | Select-Object -Last 3` shows 2026-05-03 row | `[x]` |

### Status Legend

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Not started |
| `[/]` | In progress |
| `[x]` | Complete |
| `[B]` | Blocked (must link follow-up) |

---

## Ad-Hoc Bug Fixes (2026-05-03)

Issues discovered during interactive testing of the GUI enhancements. Outside MEU scope but blocking normal GUI operation.

| # | Task | Symptom | File(s) Changed | Status |
|---|------|---------|-----------------|--------|
| AH-1 | Fix Trade Plan Create 422 — strip `linked_trade_id` from POST payload | `422: Extra inputs are not permitted` | `features/planning/TradePlanPage.tsx` | `[x]` |
| AH-2 | Fix Trade Create 422 — coerce `realized_pnl: null` → `0` | `422: realized_pnl: Input should be a valid number` | `features/trades/TradesLayout.tsx` | `[x]` |
| AH-3 | Fix Screenshot Upload 404 on new trades — guard `(new)` placeholder | `POST /api/v1/trades/(new)/images → 404` | `features/trades/ScreenshotPanel.tsx` | `[x]` |
| AH-4 | Fix Clipboard Paste in Electron — window-level listener | Ctrl+V paste of images did nothing | `features/trades/ScreenshotPanel.tsx` | `[x]` |
| AH-5 | Fix Account Archive UX — action-specific theming | Archive button showed red "Delete" styling | `components/ConfirmDeleteModal.tsx`, `features/accounts/AccountDetailPanel.tsx` | `[x]` |
| AH-6 | Fix Account Create dirty-state — reset `childDirty` on create | Phantom "Unsaved Changes" dialog after account creation | `features/accounts/AccountsHome.tsx` | `[x]` |
| AH-7 | Add search/multi-select/bulk delete to Watchlist sidebar | Watchlist list has no search, checkboxes, or bulk delete | `features/planning/WatchlistPage.tsx` | `[x]` |
| AH-8 | Add multi-select/bulk delete to Trades table | Trades table has no checkboxes or bulk delete | `features/trades/TradesTable.tsx`, `features/trades/TradesLayout.tsx` | `[x]` |
| AH-9 | Wire bulk delete handlers in Scheduling layout | Bulk delete for policies and templates does nothing — handlers not passed as props | `features/scheduling/SchedulingLayout.tsx` | `[x]` |
| AH-10 | Tiered account deletion — `TradeWarningModal` + `POST :trade-counts` | No warning when deleting accounts with linked trades; 409 errors confuse users | `services/account_service.py`, `routes/accounts.py`, `TradeWarningModal.tsx`, `useAccounts.ts`, `AccountsHome.tsx`, `AccountDetailPanel.tsx` | `[x]` |
| AH-11 | TDD tests for tiered deletion services | AH-10 services lacked test coverage | `test_service_trade_counts.py` (6), `test_api_trade_counts.py` (8), `TradeWarningModal.test.tsx` (19), mock updates (3 files) | `[x]` |
| AH-12 | Tradier API hardening — Accept header + provider-specific validators | Tradier test returned "Unexpected response"; Save button stuck dirty | `provider_registry.py`, `provider_connection_service.py`, `MarketDataProvidersPage.tsx` | `[x]` |
| AH-13 | TDD tests for Tradier hardening | AH-12 lacked test coverage | `test_provider_registry.py`, `test_provider_connection_service.py`, `MarketDataProvidersPage.test.tsx` | `[x]` |
| AH-14 | MCP system audit — full tool regression check | Verify no regressions from AH-10/12 changes | 68/70 pass, 0 regressions. Report: `.agent/context/MCP/mcp-tool-audit-report.md` | `[x]` |

### Verification

- **Frontend test suite**: 635 tests pass, zero regressions
- **Backend test suite**: 2768 tests pass, zero regressions
- **Pyright**: 0 errors, 0 warnings
- **MCP Audit**: 68/70 pass (97.1%), 0 regressions vs baseline v2
- **Date**: 2026-05-04
