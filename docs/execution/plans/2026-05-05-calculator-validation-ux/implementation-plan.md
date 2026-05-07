---
project: "2026-05-05-calculator-validation-ux"
date: "2026-05-05"
source: "docs/build-plan/06-gui.md, docs/build-plan/06c-gui-planning.md, docs/build-plan/06h-gui-calculator.md"
meus: ["MEU-204", "MEU-205", "MEU-206"]
status: "approved"
template_version: "2.0"
---

# Implementation Plan: Calculator & Validation UX Hardening

> **Project**: `2026-05-05-calculator-validation-ux`
> **Build Plan Section(s)**: [06-gui.md §UX Hardening](../../build-plan/06-gui.md), [06c-gui-planning.md](../../build-plan/06c-gui-planning.md), [06h-gui-calculator.md](../../build-plan/06h-gui-calculator.md)
> **Status**: `approved`

---

## Goal

Complete three categories of GUI UX hardening for the Trade Plan and Calculator workflows:

1. **Form validation hardening** — Add inline validation errors (red "X is required" messages) for all CRUD forms (TradePlan, Watchlist, Accounts) + disable Save & Continue when required fields are missing.
2. **Calculator workflow integration** — Replace Apply to Plan button with searchable plan picker, add configurable toggle switches for which fields to copy, implement auto-save for new unsaved plans before opening calculator.
3. **Trade Plan layout redesign** — 4-column price level grid, auto-recalculate position_size on shares/entry change, move calculator button to centered action row.

---

## User Review Required

> [!IMPORTANT]
> All work was completed during the session and manually verified by the user via live Electron app. 630/630 Vitest tests pass. TypeScript clean.

---

## Proposed Changes

### MEU-204: `gui-form-validation-hardening` — Inline Validation & Button Disabling

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-1 | TradePlan shows red "Ticker is required" / "Strategy Name is required" on empty save | Spec: 06c §form validation | Save with empty ticker → red error under field |
| AC-2 | Watchlist shows red "Name is required" on empty save/update | Spec: 06i §form validation | Save with empty name → red error |
| AC-3 | Account balance save shows required error when value is empty | Spec: 06d §balance snapshot | Save without balance → error shown |
| AC-4 | Save & Continue disabled when required fields missing across all forms | Research-backed: web search on form UX best practices | Button visually disabled + tooltip/reduced opacity |
| AC-5 | Validation errors clear when form is modified or selection changes | Research-backed: form UX patterns | Change entry → errors disappear |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `ui/src/renderer/src/features/planning/TradePlanPage.tsx` | modify | Add fieldErrors state, inline red error messages for ticker/strategy_name |
| `ui/src/renderer/src/features/planning/WatchlistPage.tsx` | modify | Add fieldErrors state, inline red error for name field |
| `ui/src/renderer/src/features/accounts/AccountDetailPanel.tsx` | modify | Add balance required validation |
| `ui/src/renderer/src/hooks/useFormGuard.ts` | modify | Add `isFormInvalid` check for Save & Continue disabling |
| `ui/src/renderer/src/features/scheduling/SchedulingLayout.tsx` | modify | Wire disabled state for Save & Continue when form invalid |

### MEU-205: `gui-calculator-workflow` — Calculator Plan Picker & Toggles

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-6 | Calculator modal has searchable trade plan picker dropdown | Human-approved: user request | — |
| AC-7 | Toggle switches control which fields copy to plan (shares, position_size, entry, stop, target, account) | Human-approved: user request | Toggle off shares → shares not copied |
| AC-8 | Toggle state persisted in localStorage (`zorivest:calc-apply-toggles`) | Spec: 06h §calculator state | Reload app → toggles restored |
| AC-9 | Toggles display in 3-column × 2-row grid with title "Select what to copy to the plan:" | Human-approved: user request | — |
| AC-10 | Toggles show green (on) / red (off) with "Copying: X, Y, Z" status line | Human-approved: user request | All off → "Nothing selected" red text |
| AC-11 | Apply to Plan closes modal after dispatching event | Spec: 06h §apply workflow | Click Apply → modal closes |
| AC-12 | Apply button centered, auto-sized to text (not full-width stretched) | Human-approved: user request | — |
| AC-13 | Calculator auto-saves new unsaved plan before opening (validates ticker+strategy_name first) | Human-approved: user request | Missing ticker on new plan → error, no calculator |
| AC-14 | Button shows "🧮 Calculator" text for discoverability | Human-approved: user request | — |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `ui/src/renderer/src/features/planning/PositionCalculatorModal.tsx` | modify | Plan picker, toggle switches, apply closes modal, green/red colors, status line |
| `ui/src/renderer/src/features/planning/TradePlanPage.tsx` | modify | Async handleCalculatePosition with auto-save, centered button placement |

### MEU-206: `gui-tradeplan-layout` — Trade Plan Layout Redesign

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-15 | Price row displays 4-column grid: Entry Price, Planned Shares, Stop Loss, Target | Human-approved: user request | — |
| AC-16 | Metrics row displays: Position Size, Risk/Share, Reward/Share, R:R Ratio | Human-approved: user request | — |
| AC-17 | Position Size auto-recalculates when entry_price or shares_planned changes | Spec: 06c §computed fields | Change shares → position_size updates |
| AC-18 | Calculator button in centered action row below input fields | Research-backed: web search on primary action UX placement | — |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `ui/src/renderer/src/features/planning/TradePlanPage.tsx` | modify | 4-col grid, computed metrics row, useEffect auto-recalc, centered button |

---

## Out of Scope

- Backend API changes (all work is frontend-only)
- E2E Playwright tests (no E2E infrastructure changes)
- Calculator expansion modes (Futures/Options/Forex/Crypto) — deferred to MEU-155

---

## BUILD_PLAN.md Audit

This project adds a new section **P2.3 — Calculator & Validation UX Hardening** to BUILD_PLAN.md with MEU-204, MEU-205, MEU-206.

```powershell
rg "MEU-204" docs/BUILD_PLAN.md  # Expected: 1 match after update
```

---

## Verification Plan

### 1. Vitest (630 tests)
```powershell
npx vitest run *> C:\Temp\zorivest\vitest.txt; Get-Content C:\Temp\zorivest\vitest.txt | Select-Object -Last 10
```

### 2. TypeScript
```powershell
npx tsc --noEmit *> C:\Temp\zorivest\tsc.txt; Get-Content C:\Temp\zorivest\tsc.txt | Select-Object -Last 5
```

---

## Open Questions

> [!WARNING]
> None — all design decisions were resolved during the session via user feedback.

---

## Research References

- Web search: "disable save button when form has validation errors UX best practice" — confirmed pattern of disabling + visual feedback
- Web search: "calculator apply button placement UX" — confirmed centered below inputs is standard for primary actions
