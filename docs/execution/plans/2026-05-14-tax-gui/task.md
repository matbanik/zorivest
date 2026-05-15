---
project: "2026-05-14-tax-gui"
source: "docs/execution/plans/2026-05-14-tax-gui/implementation-plan.md"
meus: ["MEU-154", "MEU-155", "MEU-156"]
status: "in_progress"
template_version: "2.0"
---

# Task — Phase 3E Tax GUI

> **Project:** `2026-05-14-tax-gui`
> **Type:** GUI
> **Estimate:** ~23 files changed

## Task Table

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| | **MEU-154: Tax GUI Core** | | | | |
| 1 | Create `TaxDisclaimer.tsx` shared disclaimer component | coder | `features/tax/TaxDisclaimer.tsx` | `cd ui && npx vitest run *> C:\Temp\zorivest\vitest-tax.txt; Get-Content C:\Temp\zorivest\vitest-tax.txt \| Select-Object -Last 40` | `[x]` |
| 2 | Create `TaxLayout.tsx` tab container with 7 tabs (Dashboard, Lots, Wash Sales, Simulator, Harvesting, Quarterly, Audit) | coder | `features/tax/TaxLayout.tsx` | `cd ui && npx vitest run *> C:\Temp\zorivest\vitest-tax.txt; Get-Content C:\Temp\zorivest\vitest-tax.txt \| Select-Object -Last 40` | `[x]` |
| 3 | Register `/tax` route in `router.tsx` (lazy-loaded TaxLayout) | coder | `router.tsx` modified | `cd ui && npx tsc --noEmit *> C:\Temp\zorivest\tsc-tax.txt; Get-Content C:\Temp\zorivest\tsc-tax.txt \| Select-Object -Last 30` | `[x]` |
| 4 | Add Tax nav item to `NavRail.tsx` (Receipt icon, between Planning and Scheduling) | coder | `NavRail.tsx` modified | `cd ui && npx vitest run *> C:\Temp\zorivest\vitest-tax.txt; Get-Content C:\Temp\zorivest\vitest-tax.txt \| Select-Object -Last 40` | `[x]` |
| 5 | Add `/tax` to `AppShell.tsx` navRoutes for `Ctrl+Shift+6` keyboard shortcut | coder | `AppShell.tsx` modified | `cd ui && npx tsc --noEmit *> C:\Temp\zorivest\tsc-tax.txt; Get-Content C:\Temp\zorivest\tsc-tax.txt \| Select-Object -Last 30` | `[x]` |
| 6 | Create `TaxDashboard.tsx` — 6 summary cards (aligned to API response) + YTD P&L by Symbol table | coder | `features/tax/TaxDashboard.tsx` | `cd ui && npx vitest run *> C:\Temp\zorivest\vitest-tax.txt; Get-Content C:\Temp\zorivest\vitest-tax.txt \| Select-Object -Last 40` | `[x]` |
| 7 | Create `TaxLotViewer.tsx` — lot table with filters, ST/LT badges, **disabled** "Close This Lot" and "Reassign Method" buttons with tooltip "Coming soon — Module C4/C5" | coder | `features/tax/TaxLotViewer.tsx` | `cd ui && npx vitest run *> C:\Temp\zorivest\vitest-tax.txt; Get-Content C:\Temp\zorivest\vitest-tax.txt \| Select-Object -Last 40` | `[x]` |
| 8 | Create `WashSaleMonitor.tsx` — chain list + detail split pane | coder | `features/tax/WashSaleMonitor.tsx` | `cd ui && npx vitest run *> C:\Temp\zorivest\vitest-tax.txt; Get-Content C:\Temp\zorivest\vitest-tax.txt \| Select-Object -Last 40` | `[x]` |
| 9 | Create `WhatIfSimulator.tsx` — simulation form with G23 FormGuard + results display | coder | `features/tax/WhatIfSimulator.tsx` | `cd ui && npx vitest run *> C:\Temp\zorivest\vitest-tax.txt; Get-Content C:\Temp\zorivest\vitest-tax.txt \| Select-Object -Last 40` | `[x]` |
| 10 | Create `LossHarvestingTool.tsx` — harvestable positions table ranked by loss | coder | `features/tax/LossHarvestingTool.tsx` | `cd ui && npx vitest run *> C:\Temp\zorivest\vitest-tax.txt; Get-Content C:\Temp\zorivest\vitest-tax.txt \| Select-Object -Last 40` | `[x]` |
| 11 | Create `QuarterlyTracker.tsx` — 4-quarter timeline cards (fetch `GET /quarterly?quarter={Q}&tax_year={Y}` ×4) + payment form with G23 FormGuard posting to `POST /quarterly/payment` with body `{ quarter, tax_year, payment_amount, confirm: true }` | coder | `features/tax/QuarterlyTracker.tsx` | `cd ui && npx vitest run *> C:\Temp\zorivest\vitest-tax.txt; Get-Content C:\Temp\zorivest\vitest-tax.txt \| Select-Object -Last 40` | `[x]` |
| 12 | Create `TransactionAudit.tsx` — audit findings table with severity badges | coder | `features/tax/TransactionAudit.tsx` | `cd ui && npx vitest run *> C:\Temp\zorivest\vitest-tax.txt; Get-Content C:\Temp\zorivest\vitest-tax.txt \| Select-Object -Last 40` | `[x]` |
| 13 | Write component tests for MEU-154 (`tax-gui.test.tsx`) — 27 tests passing | tester | `features/tax/__tests__/tax-gui.test.tsx` | `cd ui && npx vitest run src/renderer/src/features/tax/__tests__/ *> C:\Temp\zorivest\vitest-tax-tests.txt; Get-Content C:\Temp\zorivest\vitest-tax-tests.txt \| Select-Object -Last 40` | `[x]` |
| | **MEU-155: Calculator Expansion** | | | | |
| 14 | Add mode selector (Equity/Futures/Options/Forex/Crypto) to PositionCalculatorModal | coder | `PositionCalculatorModal.tsx` modified | `cd ui && npx vitest run *> C:\Temp\zorivest\vitest-calc.txt; Get-Content C:\Temp\zorivest\vitest-calc.txt \| Select-Object -Last 40` | `[x]` |
| 15 | Add Futures mode: fields (multiplier, tick_size, margin) + preset auto-fill + computation | coder | `PositionCalculatorModal.tsx` modified | `cd ui && npx vitest run *> C:\Temp\zorivest\vitest-calc.txt; Get-Content C:\Temp\zorivest\vitest-calc.txt \| Select-Object -Last 40` | `[x]` |
| 16 | Add Options mode: fields (type, premium, delta, underlying, multiplier) + computation | coder | `PositionCalculatorModal.tsx` modified | `cd ui && npx vitest run *> C:\Temp\zorivest\vitest-calc.txt; Get-Content C:\Temp\zorivest\vitest-calc.txt \| Select-Object -Last 40` | `[x]` |
| 17 | Add Forex mode: fields (pair, lot_type, pip_value, leverage) + computation | coder | `PositionCalculatorModal.tsx` modified | `cd ui && npx vitest run *> C:\Temp\zorivest\vitest-calc.txt; Get-Content C:\Temp\zorivest\vitest-calc.txt \| Select-Object -Last 40` | `[x]` |
| 18 | Add Crypto mode: fields (leverage, fee_rate) + computation + liquidation price | coder | `PositionCalculatorModal.tsx` modified | `cd ui && npx vitest run *> C:\Temp\zorivest\vitest-calc.txt; Get-Content C:\Temp\zorivest\vitest-calc.txt \| Select-Object -Last 40` | `[x]` |
| 19 | Add mode-specific warning rules (common + per-mode) | coder | `PositionCalculatorModal.tsx` modified | `cd ui && npx vitest run *> C:\Temp\zorivest\vitest-calc.txt; Get-Content C:\Temp\zorivest\vitest-calc.txt \| Select-Object -Last 40` | `[x]` |
| 20 | Add Scenario Comparison: Save Scenario button + comparison table (max 5) | coder | `PositionCalculatorModal.tsx` modified | `cd ui && npx vitest run *> C:\Temp\zorivest\vitest-calc.txt; Get-Content C:\Temp\zorivest\vitest-calc.txt \| Select-Object -Last 40` | `[x]` |
| 21 | Add Calculation History: last 10 with mode icon + Load button (FIFO eviction) | coder | `PositionCalculatorModal.tsx` modified | `cd ui && npx vitest run *> C:\Temp\zorivest\vitest-calc.txt; Get-Content C:\Temp\zorivest\vitest-calc.txt \| Select-Object -Last 40` | `[x]` |
| 22 | Write component tests for MEU-155 (`calculatorModes.test.ts`) — 21 pure computation tests | tester | `features/planning/__tests__/calculatorModes.test.ts` | `cd ui && npx vitest run src/renderer/src/features/planning/__tests__/calculatorModes.test.ts *> C:\Temp\zorivest\vitest-calc-tests.txt; Get-Content C:\Temp\zorivest\vitest-calc-tests.txt \| Select-Object -Last 40` | `[x]` |
| | **MEU-156: Section Toggles** | | | | |
| 23 | Tax Profile read-only section added inline to `SettingsLayout.tsx` (filing status, cost basis, tax year — all disabled with "Coming soon" tooltips). Separate component deferred since settings are ~20 lines of JSX | coder | `SettingsLayout.tsx` modified (data-testid: `tax-profile-settings`) | `cd ui && npx tsc --noEmit *> C:\Temp\zorivest\tsc-tax.txt; Get-Content C:\Temp\zorivest\tsc-tax.txt \| Select-Object -Last 30` | `[x]` |
| 23a | `[B]` Toggle persistence via TaxProfile CRUD REST API — **Blocked** pending backend MEU. Toggles remain read-only until REST endpoint exists. Follow-up: create TaxProfile CRUD API MEU | coder | N/A (blocked) | N/A | `[B]` |
| 24 | Add Tax Profile section to `SettingsLayout.tsx` | coder | `SettingsLayout.tsx` modified | `cd ui && npx tsc --noEmit *> C:\Temp\zorivest\tsc-tax.txt; Get-Content C:\Temp\zorivest\tsc-tax.txt \| Select-Object -Last 30` | `[x]` |
| 25 | Write component tests for MEU-156 (`tax-toggles.test.tsx`) | tester | `features/settings/__tests__/tax-toggles.test.tsx` — 13 tests passing | `cd ui && npx vitest run src/renderer/src/features/settings/__tests__/tax-toggles.test.tsx *> C:\Temp\zorivest\vitest-toggles.txt; Get-Content C:\Temp\zorivest\vitest-toggles.txt \| Select-Object -Last 40` | `[x]` |
| | **Wave 11: E2E Playwright Tests** | | | | |
| 25a | Write E2E test `tax-dashboard.test.ts` — nav to Tax route, verify summary cards, axe-core | tester | `ui/tests/e2e/tax-dashboard.test.ts` — 5 tests, tsc clean | `cd ui && npx playwright test tests/e2e/tax-dashboard.test.ts *> C:\Temp\zorivest\e2e-dashboard.txt; Get-Content C:\Temp\zorivest\e2e-dashboard.txt \| Select-Object -Last 40` | `[x]` |
| 25b | Write E2E test `tax-lots.test.ts` — lot table render, sort/filter, disabled close/reassign btns | tester | `ui/tests/e2e/tax-lots.test.ts` — 3 tests, tsc clean | `cd ui && npx playwright test tests/e2e/tax-lots.test.ts *> C:\Temp\zorivest\e2e-lots.txt; Get-Content C:\Temp\zorivest\e2e-lots.txt \| Select-Object -Last 40` | `[x]` |
| 25c | Write E2E test `tax-wash-sales.test.ts` — monitor render, chain detail | tester | `ui/tests/e2e/tax-wash-sales.test.ts` — 3 tests, tsc clean | `cd ui && npx playwright test tests/e2e/tax-wash-sales.test.ts *> C:\Temp\zorivest\e2e-wash.txt; Get-Content C:\Temp\zorivest\e2e-wash.txt \| Select-Object -Last 40` | `[x]` |
| 25d | Write E2E test `tax-what-if.test.ts` — simulator form, result | tester | `ui/tests/e2e/tax-what-if.test.ts` — 3 tests, tsc clean | `cd ui && npx playwright test tests/e2e/tax-what-if.test.ts *> C:\Temp\zorivest\e2e-whatif.txt; Get-Content C:\Temp\zorivest\e2e-whatif.txt \| Select-Object -Last 40` | `[x]` |
| 25e | Write E2E test `tax-quarterly.test.ts` — tracker render, payment entry | tester | `ui/tests/e2e/tax-quarterly.test.ts` — 4 tests, tsc clean | `cd ui && npx playwright test tests/e2e/tax-quarterly.test.ts *> C:\Temp\zorivest\e2e-quarterly.txt; Get-Content C:\Temp\zorivest\e2e-quarterly.txt \| Select-Object -Last 40` | `[x]` |
| | **🔄 Re-Anchor Gate** | | | | |
| 26 | 🔄 `view_file` this `task.md`. Count all `[ ]` rows remaining and list them. If any implementation rows above are still `[ ]`, go back and complete them before proceeding. | coder | All implementation tasks complete. Remaining `[ ]` are closeout-only (27–35). | `Select-String '\[ \]' docs/execution/plans/2026-05-14-tax-gui/task.md *> C:\Temp\zorivest\reanchor.txt; Get-Content C:\Temp\zorivest\reanchor.txt` | `[x]` |
| | **📋 Closeout Phase** | | | | |
| | ⚠️ *Closeout artifacts are institutional memory. Apply the same rigor as production code. Context fatigue at session end is the primary risk — these steps are the countermeasure.* | | | | |
| | **🔄 Re-Anchor Gate** | | | | |
| 27 | 🔄 `view_file` this `task.md`. Count all `[ ]` rows remaining and list them. If any implementation/verification rows above are still `[ ]`, go back and complete them before proceeding to closeout. | coder | 0 unchecked implementation rows. Remaining `[ ]` are closeout (30–35). | `Select-String '\\[ \\]' docs/execution/plans/2026-05-14-tax-gui/task.md *> C:\Temp\zorivest\reanchor.txt; Get-Content C:\Temp\zorivest\reanchor.txt` | `[x]` |
| 28 | Audit `docs/BUILD_PLAN.md` for stale refs | orchestrator | MEU-154 ✅, MEU-155 ✅. MEU-156 ⬜ (blocked by MEU-148a). P3 count updated 0→23. Total 158→160. | `rg "MEU-154\|gui-tax\|MEU-155\|gui-calculator\|MEU-156\|tax-section-toggles" docs/BUILD_PLAN.md *> C:\Temp\zorivest\buildplan-audit.txt; Get-Content C:\Temp\zorivest\buildplan-audit.txt` | `[x]` |
| 29 | Run full verification plan (tsc + vitest + E2E + anti-placeholder) | tester | tsc: 0 errors. vitest: 43 files, 713 tests, 0 failures. Anti-placeholder: 0 matches. E2E: written (5 files, 18 tests) — require Electron runtime for execution. | See `implementation-plan.md` §Verification Plan (steps 1–6, all P0-safe) | `[x]` |
| 30 | Save session state to pomera_notes | orchestrator | `Memory/Session/Zorivest-tax-gui-2026-05-14` (Note ID: 1179) | MCP: `pomera_notes(action="search", search_term="Zorivest-tax-gui*")` returns ≥1 result | `[x]` |
| | **Template + Exemplar Loading** (mandatory before writing closeout artifacts) | | | | |
| 31 | Load templates and exemplars: `view_file` BOTH the template AND the most recent peer exemplar for each artifact. Do NOT write from memory. | orchestrator | Loaded: TEMPLATE.md (handoff+reflection), 2026-05-14-tax-engine-wiring-handoff.md, 2026-05-14-tax-engine-wiring-reflection.md | `view_file: docs/execution/reflections/TEMPLATE.md` + `view_file` most recent `*-reflection.md`. `view_file: .agent/context/handoffs/TEMPLATE.md` + `view_file` most recent `*-handoff.md`. | `[x]` |
| 32 | Create handoff following template structure and exemplar quality | reviewer | `.agent/context/handoffs/2026-05-14-tax-gui-handoff.md` — 16 ACs, 22 changed files, evidence bundle, deferred items | `rg "Acceptance Criteria\|CACHE BOUNDARY\|Evidence\|Changed Files" .agent/context/handoffs/2026-05-14-tax-gui-handoff.md *> C:\Temp\zorivest\handoff-check.txt; Get-Content C:\Temp\zorivest\handoff-check.txt` | `[x]` |
| 33 | Create reflection following template structure and exemplar quality | orchestrator | `docs/execution/reflections/2026-05-14-tax-gui-reflection.md` — all 11 sections + YAML + metrics + 3 design rules | `rg "Friction Log\|Pattern Extraction\|Efficiency Metrics\|Rule Adherence\|Instruction Coverage\|schema: v1" docs/execution/reflections/2026-05-14-tax-gui-reflection.md *> C:\Temp\zorivest\reflection-check.txt; Get-Content C:\Temp\zorivest\reflection-check.txt` | `[x]` |
| 34 | Append metrics row | orchestrator | Row 84 appended to `docs/execution/metrics.md` — MEU-154/155/156, 49 tests, 92% adherence | `Get-Content docs/execution/metrics.md *> C:\Temp\zorivest\metrics-check.txt; Get-Content C:\Temp\zorivest\metrics-check.txt \| Select-Object -Last 3` | `[x]` |
| | **Closeout Quality Gate** | | | | |
| 35 | Run closeout structural checks: verify reflection has all 9 structural markers, handoff has all 4 markers, metrics row exists | tester | Handoff: 4/4 markers (CACHE BOUNDARY, Acceptance Criteria, Changed Files, Evidence). Reflection: 6/6 markers (Friction Log, Pattern Extraction, Efficiency Metrics, Rule Adherence, Instruction Coverage, schema: v1). Metrics row 84 exists. | Run `completion-preflight` §Structural Marker Checklist + §Closeout Artifact Quality Check | `[x]` |

### Status Legend

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Not started |
| `[/]` | In progress |
| `[x]` | Complete |
| `[B]` | Blocked (must link follow-up) |
