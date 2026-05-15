---
project: "2026-05-14-tax-gui"
date: "2026-05-14"
source: "docs/build-plan/06g-gui-tax.md, docs/build-plan/06h-gui-calculator.md"
meus: ["MEU-154", "MEU-155", "MEU-156"]
phase: "3E"
session: "5b — GUI"
depends_on: ["Phase 3E Session 5a (MEU-148–153) ✅"]
template_version: "2.0"
---

# Implementation Plan — Phase 3E Tax GUI (Session 5b)

> **Project:** `2026-05-14-tax-gui`
> **Scope:** MEU-154, MEU-155, MEU-156 (3 MEUs)
> **Type:** GUI
> **Session:** 5b (GUI) — follows Session 5a (Backend + MCP)

---

## Spec Sources

| Spec | File | Sections |
|------|------|----------|
| Tax GUI | [06g-gui-tax.md](../../../build-plan/06g-gui-tax.md) | All sections (Dashboard → Audit) |
| Calculator Expansion | [06h-gui-calculator.md](../../../build-plan/06h-gui-calculator.md) | §Instrument Modes, §Warning Rules, §Scenario, §History |
| Domain Model | [domain-model-reference.md](../../../build-plan/domain-model-reference.md) | Module G (Section 475/1256/Forex) |
| Emerging Standards | [emerging-standards.md](../../../../.agent/docs/emerging-standards.md) | G23 (Form Guard), G14 (Auto-populate) |
| Build Matrix | [build-priority-matrix.md](../../../build-plan/build-priority-matrix.md) | §Phase 3E items 81, 81a, 82 |

---

## Goal

Build the Tax GUI feature surface: Tax Dashboard, Lot Viewer, Wash Sale Monitor, What-If Simulator, Loss Harvesting Tool, Quarterly Payments Tracker, and Transaction Audit. Expand the Position Calculator with 5 instrument modes, scenario comparison, and calculation history. Add Section 475/1256/Forex election toggles to Settings.

---

## Resolved Design Decisions

| # | Decision | Resolution | Source |
|---|----------|------------|--------|
| 1 | **Nav Rail Position**: Tax as 6th top-level nav item | Yes — 06-gui.md L255 explicitly specifies Tax as 6th item with `Ctrl+6` | `Spec` |
| 2 | **Calculator Expansion Scope**: 5 modes, scenario (max 5), history (max 10), session-scoped | Confirmed — all React state, no persistence | `Spec` |
| 3 | **Section Toggles Location**: Settings > Tax Profile tab | Confirmed — 06f-gui-settings.md §Tax Profile specifies this location | `Spec` |
| 4 | **Tax Year Persistence**: Default to current year, no session persistence | Prevents stale-year confusion; matches TurboTax/TaxAct patterns | `Research-backed` |
| 5 | **Lot Viewer Actions**: Close/Reassign buttons rendered as disabled with tooltip | Satisfies spec (buttons present) + Wave 11 test-ids without backend | `Spec` + `Local Canon` |

---

## Architecture Overview

```
API Layer (exists ✅)                  GUI Layer (new)
┌───────────────────────┐              ┌──────────────────────────────────┐
│ routes/tax.py         │              │ features/tax/                    │
│ ├ GET /ytd-summary    │◀─── fetch ──│ ├ TaxDashboard.tsx               │
│ ├ GET /lots           │              │ ├ TaxLotViewer.tsx               │
│ ├ GET /wash-sales     │              │ ├ WashSaleMonitor.tsx            │
│ ├ POST /simulate      │              │ ├ WhatIfSimulator.tsx            │
│ ├ GET /harvest        │              │ ├ LossHarvestingTool.tsx         │
│ ├ GET /quarterly      │              │ ├ QuarterlyTracker.tsx           │
│ ├ POST /audit         │              │ ├ TransactionAudit.tsx           │
│ ├ GET /alpha          │              │ └ TaxLayout.tsx (tab container)  │
│ └ GET /deferred-losses│              │                                  │
└───────────────────────┘              │ features/planning/               │
                                       │ └ PositionCalculatorModal.tsx     │
                                       │   (expanded: 5 modes + scenarios)│
                                       │                                  │
                                       │ features/settings/               │
                                       │ └ TaxProfileSettings.tsx (§475+) │
                                       └──────────────────────────────────┘
```

---

## Execution Order

| Order | MEU | Slug | Scope | Depends On |
|-------|-----|------|-------|------------|
| 1 | MEU-154 | `tax-gui` | Tax feature: Dashboard + Lot Viewer + Wash Sale + Simulator + Harvesting + Quarterly + Audit | Tax API ✅ |
| 2 | MEU-155 | `tax-calc-expansion` | Calculator: 5 modes + warnings + scenarios + history | Existing PositionCalculatorModal ✅ |
| 3 | MEU-156 | `tax-section-toggles` | Settings: §475/§1256/Forex toggles | Tax API ✅ |

---

## Boundary Input Contract

### GUI Form Surfaces

| Surface | Validation Owner | Key Constraints | Guard |
|---------|-----------------|-----------------|-------|
| What-If Simulator form | React component state + API 422 | `ticker: string (required)`, `quantity: number (>0)`, `price: number (>0)`, `account_id: string`, `cost_basis_method: select` | G23 FormGuard on input fields |
| Quarterly Payment entry | React component + API 422 | `quarter: select (Q1–Q4)`, `payment_amount: float (>0)`, `tax_year: int`, `confirm: bool (required=true)` | G23 FormGuard |
| Calculator inputs (all modes) | React component math | `entry/stop/target: number`, `risk_pct: number`, mode-specific fields per spec | Existing calculator validation |
| Section toggle form | React component (read-only display from TaxProfile) | `section_475_elected: boolean`, `section_1256_eligible: boolean`, `forex_worksheet: boolean` (display only — persistence `[B]` blocked pending TaxProfile CRUD API) | G23 FormGuard (deferred until write is enabled) |

---

## MEU-154: Tax GUI Core

> **Matrix Item:** 81 | **Spec:** [06g-gui-tax.md](../../../build-plan/06g-gui-tax.md)

### Acceptance Criteria

| AC | Description | Source |
|----|-------------|--------|
| AC-154.1 | `/tax` route registered in `router.tsx` with lazy-loaded `TaxLayout` | Spec: 06g L477 (route reachable via nav rail) |
| AC-154.2 | Nav rail shows "Tax" entry with Lucide `Receipt` icon between Planning and Scheduling | Spec: 06g L477; Local Canon: NavRail.tsx pattern |
| AC-154.3 | `TaxLayout` renders tab bar: Dashboard, Lots, Wash Sales, Simulator, Harvesting, Quarterly, Audit | Spec: 06g §Quick Actions L56–58 |
| AC-154.4 | Tax Dashboard fetches `GET /api/v1/tax/ytd-summary` and renders 7 summary cards (ST Gains, LT Gains, Wash Sale Adj, Estimated Tax, Loss Carryforward, Harvestable Losses, Tax Alpha) | Spec: 06g L66–75 |
| AC-154.5 | YTD P&L by Symbol table renders with per-ticker ST/LT breakdown via `GET /api/v1/tax/ytd-summary?group_by=symbol` | Spec: 06g L44–53, L82 |
| AC-154.6 | Tax year selector defaults to current year, filters all dashboard data | Spec: 06g L25 |
| AC-154.7 | Lot Viewer fetches `GET /api/v1/tax/lots` with filters (open/closed, ticker, account) and renders TanStack-style table. "Close This Lot" and "Reassign Method" buttons rendered as **disabled** with tooltip "Coming soon — Module C4/C5" | Spec: 06g L120–139; Wave 11 test-ids: `tax-lot-close-btn`, `tax-lot-reassign-btn` |
| AC-154.8 | Lot rows show ST/LT classification with days-to-LT countdown for open lots (🕐 Nd) | Spec: 06g L107 |
| AC-154.9 | Wash Sale Monitor fetches `GET /api/v1/tax/wash-sales` and renders list/detail split pane | Spec: 06g L160–186 |
| AC-154.10 | What-If Simulator form posts to `POST /api/v1/tax/simulate` and renders per-lot breakdown + tax impact summary | Spec: 06g L273–294 |
| AC-154.11 | G23 FormGuard on Simulator form — dirty check before tab switching | Standard: G23 |
| AC-154.12 | Loss Harvesting tab fetches `GET /api/v1/tax/harvest` and renders table ranked by harvestable amount | Spec: 06g L345–354 |
| AC-154.13 | Quarterly Tracker fetches `GET /api/v1/tax/quarterly?quarter={Q}&tax_year={Y}` for each quarter (4 requests) and renders 4-quarter timeline cards | Spec: 06g L416–425; API: `quarter` + `tax_year` required query params |
| AC-154.14 | Quarterly payment entry form with G23 FormGuard, posts to `POST /api/v1/tax/quarterly/payment` with body `{ quarter, tax_year, payment_amount, confirm: true }` | Spec: 06g L427–433; API: `RecordPaymentRequest` at tax.py L81–87 |
| AC-154.15 | Transaction Audit tab posts to `POST /api/v1/tax/audit` and renders findings with severity badges | Spec: 06g L449–458 |
| AC-154.16 | Every tax output surface displays disclaimer: "This is an estimator, not tax advice. Always consult a CPA." | Spec: 06g L11, L60 |
| AC-154.17 | All interactive elements have unique `data-testid` attributes per `ui/tests/e2e/test-ids.ts` Wave 11 | Standard: GUI Shipping Gate |
| AC-154.18 | Wave 11 Playwright E2E tests pass: route/nav assertion (`nav-tax` visible), happy path (dashboard renders summary cards), `data-testid` coverage for all 23 Wave 11 IDs | Standard: GUI Shipping Gate (06-gui.md L577–585) |

### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| Tab container routing pattern | Local Canon | Follow SchedulingLayout tabbed pattern |
| Summary card component styling | Local Canon | Follow AccountsHome card grid pattern |
| TanStack table usage | Local Canon | Lot viewer uses same pattern as WatchlistTable |
| Disclaimer component | Spec | Shared `TaxDisclaimer` component per 06g L11 |
| Form guard integration | Standard G23 | Use existing `useFormGuard` hook |

### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `ui/src/renderer/src/features/tax/TaxLayout.tsx` | new | Tab container with 7 tabs |
| `ui/src/renderer/src/features/tax/TaxDashboard.tsx` | new | Summary cards + P&L table |
| `ui/src/renderer/src/features/tax/TaxLotViewer.tsx` | new | Lot table with filters |
| `ui/src/renderer/src/features/tax/WashSaleMonitor.tsx` | new | Chain list + detail split |
| `ui/src/renderer/src/features/tax/WhatIfSimulator.tsx` | new | Simulation form + results |
| `ui/src/renderer/src/features/tax/LossHarvestingTool.tsx` | new | Harvesting table |
| `ui/src/renderer/src/features/tax/QuarterlyTracker.tsx` | new | Quarter cards + payment form |
| `ui/src/renderer/src/features/tax/TransactionAudit.tsx` | new | Audit findings table |
| `ui/src/renderer/src/features/tax/TaxDisclaimer.tsx` | new | Shared disclaimer banner |
| `ui/src/renderer/src/router.tsx` | modify | Add `/tax` route |
| `ui/src/renderer/src/components/layout/NavRail.tsx` | modify | Add Tax nav item |
| `ui/src/renderer/src/components/layout/AppShell.tsx` | modify | Add `/tax` to navRoutes for `Ctrl+6` |
| `ui/src/renderer/src/features/tax/__tests__/tax-gui.test.tsx` | new | Component tests |
| `ui/tests/e2e/tax-dashboard.test.ts` | new | Wave 11 E2E: nav, summary cards, axe-core |
| `ui/tests/e2e/tax-lots.test.ts` | new | Wave 11 E2E: lot table render, sort/filter |
| `ui/tests/e2e/tax-wash-sales.test.ts` | new | Wave 11 E2E: monitor render, chain detail |
| `ui/tests/e2e/tax-what-if.test.ts` | new | Wave 11 E2E: simulator form, result |
| `ui/tests/e2e/tax-quarterly.test.ts` | new | Wave 11 E2E: tracker render, payment entry |

---

## MEU-155: Position Calculator Expansion

> **Matrix Item:** 81a | **Spec:** [06h-gui-calculator.md](../../../build-plan/06h-gui-calculator.md) §Expansion

### Acceptance Criteria

| AC | Description | Source |
|----|-------------|--------|
| AC-155.1 | Mode selector dropdown: Equity (default), Futures, Options, Forex, Crypto | Spec: 06h L26–27, L79 |
| AC-155.2 | Mode change dynamically shows/hides instrument-specific input fields | Spec: 06h L97–241 |
| AC-155.3 | **Futures**: extra fields (multiplier, tick_size, margin_per_contract), preset auto-fill for /ES, /NQ, /YM, /RTY, /CL, /GC, /MES, /MNQ | Spec: 06h L125–143 |
| AC-155.4 | **Futures**: computes risk_per_contract, contract_size, total_margin, margin_to_account_pct | Spec: 06h L145–154 |
| AC-155.5 | **Options**: extra fields (option_type, premium, delta, underlying_price, contracts_multiplier=100) | Spec: 06h L162–168 |
| AC-155.6 | **Options**: computes max_loss_per_contract, contract_count, delta_shares, delta_exposure, breakeven | Spec: 06h L170–181 |
| AC-155.7 | **Forex**: extra fields (currency_pair, lot_type, pip_value, leverage) | Spec: 06h L191–196 |
| AC-155.8 | **Forex**: computes risk_pips, lot_size, units, margin_required | Spec: 06h L206–216 |
| AC-155.9 | **Crypto**: extra fields (leverage=1, fee_rate=0.1%) | Spec: 06h L224–227 |
| AC-155.10 | **Crypto**: computes quantity (fractional), margin_required, estimated_fees, liquidation_price | Spec: 06h L229–240 |
| AC-155.11 | Common warnings: position>100%, risk>3%, R:R<1, entry==stop, balance<=0 | Spec: 06h L248–254 |
| AC-155.12 | Mode-specific warnings: Futures (margin>50%), Options (delta<0.1), Forex (leverage>100), Crypto (leverage>20, fees>10% risk) | Spec: 06h L256–282 |
| AC-155.13 | Save Scenario: adds current calc to comparison table (max 5, session-scoped) | Spec: 06h L286–294 |
| AC-155.14 | Scenario table highlights best R:R and smallest position% | Spec: 06h L292 |
| AC-155.15 | Calculation History: last 10 entries with mode icon and Load button (session-scoped, FIFO eviction) | Spec: 06h L298–312 |
| AC-155.16 | All new fields have `data-testid` attributes | Standard: GUI Shipping Gate |

### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| Equity mode computation | Local Canon | Existing PositionCalculatorModal.tsx (lines 192–212) |
| Futures preset auto-fill | Spec | Table at 06h L134–143 — hardcoded map |
| Options breakeven formula | Spec | Call: entry+premium, Put: entry-premium (06h L179) |
| Forex pip sizing | Spec | Standard/Mini/Micro lot units (06h L194) |
| Crypto liquidation price | Spec | Long: entry×(1-1/leverage), Short: entry×(1+1/leverage) (06h L240) |
| Session-scoped state | Spec | React useState, no persistence (06h L293, L312) |

### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `ui/src/renderer/src/features/planning/PositionCalculatorModal.tsx` | modify | Add mode selector, mode-specific fields, warnings, scenarios, history |
| `ui/src/renderer/src/features/planning/__tests__/calculator-expansion.test.tsx` | new | Mode switching, computation, warning, scenario tests |

---

## MEU-156: Section 475/1256/Forex Tax Toggles

> **Matrix Item:** 82 | **Spec:** [domain-model-reference.md](../../../build-plan/domain-model-reference.md) §Module G

> [!WARNING]
> **Persistence blocked.** The `TaxProfile` entity exists in the domain layer (`entities.py:242`) with fields `section_475_elected` and `section_1256_eligible`, and has its own `TaxProfileRepository`. However, there is NO REST endpoint for TaxProfile CRUD. The `SETTINGS_REGISTRY` has 0 tax keys, and `PUT /api/v1/settings` rejects unknown keys with 422. Toggle persistence is `[B]` blocked pending a TaxProfile CRUD REST API (separate backend MEU). The GUI renders toggles as **read-only displays** of current TaxProfile state.
>
> `forex_worksheet` has NO corresponding domain entity field — only spec reference. Blocked pending domain model expansion.

### Acceptance Criteria

| AC | Description | Source |
|----|-------------|--------|
| AC-156.1 | Tax Profile section in Settings shows 3 toggle switches: Section 475 MTM (`section_475_elected`), Section 1256 (60/40) (`section_1256_eligible`), Forex Income Worksheet (`forex_worksheet`) | Spec: domain-model-reference.md L596–608; 06f-gui-settings.md L355–357 |
| AC-156.2 | Section 475 toggle shows explanatory text: "All losses become ordinary (no $3K cap), no wash sales apply" | Spec: domain-model-reference.md L597–599 |
| AC-156.3 | Section 1256 toggle shows: "60% LT / 40% ST treatment for futures regardless of holding period" | Spec: domain-model-reference.md L601–603 |
| AC-156.4 | Forex toggle shows: "IBKR multi-currency forex income/loss reporting" | Spec: domain-model-reference.md L605–607 |
| AC-156.5 | `[B]` ~~Toggles persist via TaxProfile CRUD API~~ — **Blocked**: No TaxProfile REST endpoint exists. Toggles render current state as read-only. Follow-up: TaxProfile CRUD API MEU required before write is enabled | Spec: 06f-gui-settings.md §Tax Profile; Blocked: no REST surface for TaxProfile |
| AC-156.6 | `[B]` ~~G23 FormGuard protects toggle changes~~ — **Blocked**: Deferred until write is enabled (no dirty state if read-only) | Standard: G23; Blocked: depends on AC-156.5 |
| AC-156.7 | Each toggle conditionally renders when applicable (475 only for Trader Tax Status, 1256 only if futures in scope) | Spec: domain-model-reference.md "Only if..." notes |
| AC-156.8 | All toggles have `data-testid` attributes | Standard: GUI Shipping Gate |

### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `ui/src/renderer/src/features/settings/TaxProfileSettings.tsx` | new | Section toggle component |
| `ui/src/renderer/src/features/settings/SettingsLayout.tsx` | modify | Add Tax Profile tab/section |
| `ui/src/renderer/src/features/settings/__tests__/tax-toggles.test.tsx` | new | Toggle render + persist tests |

---

## Out of Scope

- Backend tax API changes (completed in Session 5a)
- MCP tax tool changes (completed in Session 5a)
- Lot closing **dialog/logic** (Module C4 — lot management; buttons are rendered disabled with tooltip)
- Lot reassignment **logic** (Module C5 — T+1 settlement; button rendered disabled with tooltip)
- Tax Profile full settings (filing status, bracket — existing in 06f)
- TaxProfile CRUD REST API (required for MEU-156 persistence — separate backend MEU)
- `forex_worksheet` domain model expansion (no entity field exists yet)

---

## BUILD_PLAN.md Audit

This project does not modify build-plan sections. Validation:

```powershell
rg "MEU-154|gui-tax|MEU-155|gui-calculator|MEU-156|tax-section-toggles" docs/BUILD_PLAN.md *> C:\Temp\zorivest\buildplan-audit.txt; Get-Content C:\Temp\zorivest\buildplan-audit.txt
# Expected: existing rows show ⬜ status — no stale references to update
```

---

## Verification Plan

### 1. TypeScript Type Check
```powershell
cd ui && npx tsc --noEmit *> C:\Temp\zorivest\tsc-tax-gui.txt; Get-Content C:\Temp\zorivest\tsc-tax-gui.txt | Select-Object -Last 30
```

### 2. Component Tests
```powershell
cd ui && npx vitest run src/renderer/src/features/tax/__tests__/ src/renderer/src/features/planning/__tests__/calculator-expansion.test.tsx src/renderer/src/features/settings/__tests__/tax-toggles.test.tsx *> C:\Temp\zorivest\vitest-tax-gui.txt; Get-Content C:\Temp\zorivest\vitest-tax-gui.txt | Select-Object -Last 40
```

### 3. Full Vitest Regression
```powershell
cd ui && npx vitest run *> C:\Temp\zorivest\vitest-full.txt; Get-Content C:\Temp\zorivest\vitest-full.txt | Select-Object -Last 40
```

### 4. Anti-Placeholder Scan
```powershell
rg "TODO|FIXME|NotImplementedError" ui/src/renderer/src/features/tax/ ui/src/renderer/src/features/planning/PositionCalculatorModal.tsx ui/src/renderer/src/features/settings/TaxProfileSettings.tsx *> C:\Temp\zorivest\placeholder-gui.txt; Get-Content C:\Temp\zorivest\placeholder-gui.txt
```

### 5. E2E Build + Wave 11
```powershell
cd ui && npm run build *> C:\Temp\zorivest\electron-build.txt; Get-Content C:\Temp\zorivest\electron-build.txt | Select-Object -Last 20
cd ui && npx playwright test tests/e2e/tax-*.test.ts *> C:\Temp\zorivest\e2e-wave11.txt; Get-Content C:\Temp\zorivest\e2e-wave11.txt | Select-Object -Last 40
```

### 6. BUILD_PLAN.md Audit
```powershell
rg "MEU-154|gui-tax|MEU-155|gui-calculator|MEU-156|tax-section-toggles" docs/BUILD_PLAN.md *> C:\Temp\zorivest\buildplan-audit.txt; Get-Content C:\Temp\zorivest\buildplan-audit.txt
```

---

## Risk Register

| Risk | Impact | Mitigation |
|------|--------|------------|
| Large component count (10+ new files) | High — scope creep | TDD discipline per MEU; tab container isolates each sub-feature |
| Calculator modal complexity explosion | High — 567 LOC already | Extract mode-specific computation into separate functions/modules |
| API endpoint shape mismatch | Medium — runtime errors | Cross-reference 06g endpoint tables with actual tax.py routes |
| FormGuard integration in tabbed layout | Medium — edge cases | Follow SchedulingLayout pattern (proven in MEU-196) |
| Nav rail 6th item crowding | Low — visual | Spec confirms 6-item rail (06-gui.md L255); Material Design supports 3–7 |

---

## Resolved Design Decisions (Post-Review)

All open questions from the original plan have been resolved. See "Resolved Design Decisions" table at the top of this document for the full list with source labels.

---

## Research References

- [06g-gui-tax.md](../../../build-plan/06g-gui-tax.md) — Full tax GUI specification
- [06h-gui-calculator.md](../../../build-plan/06h-gui-calculator.md) — Calculator expansion specification
- [domain-model-reference.md](../../../build-plan/domain-model-reference.md) — Module G (Section toggles)
- [emerging-standards.md](../../../../.agent/docs/emerging-standards.md) — G23 (Form Guard), G14 (Auto-populate)
