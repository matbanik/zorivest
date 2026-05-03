---
project: "2026-05-02-gui-ux-hardening"
date: "2026-05-02"
source: "docs/build-plan/06-gui.md §UX Hardening"
meus: ["MEU-196", "MEU-197", "MEU-198"]
status: "draft"
template_version: "2.0"
---

# Implementation Plan: GUI UX Hardening — Unsaved Changes Guard

> **Project**: `2026-05-02-gui-ux-hardening`
> **Build Plan Section(s)**: [06-gui.md §UX Hardening](../../build-plan/06-gui.md#ux-hardening--unsaved-changes-guard), [build-priority-matrix.md §P2.1](../../build-plan/build-priority-matrix.md)
> **Status**: `draft`

---

## Goal

Data entry forms across 5 list+detail modules (Market Data Providers, Accounts, Trades, Trade Plans, Watchlists) lose unsaved changes silently when users click a different list item. The scheduling module already solved this with an inline 80-line implementation in `SchedulingLayout.tsx`. This project extracts that pattern into shared infrastructure (`useFormGuard` hook + `UnsavedChangesModal` component), adds accessibility and visual cues (amber-pulse save button, `prefers-reduced-motion` support), and rolls it out to all 5 modules. The "off" status label is also replaced with "Disabled" for clarity.

---

## User Review Required

> [!IMPORTANT]
> **Resolved decisions** (from plan-critical-review):
> 1. **Save & Continue button**: Shown conditionally when the consumer provides an `onSave` callback. Pages where the child component owns the form (Trades, Accounts) get 2-button modal only (Keep Editing, Discard). Pages where the parent has a direct save handler (MarketData, TradePlan, Watchlist) get 3-button modal. SchedulingLayout refactor preserves existing 2-button behavior.
> 2. **No new npm dependencies**: Focus trap implemented manually (lightweight `onKeyDown` Tab/Shift+Tab wrap + `useEffect` auto-focus). Standard pattern for simple modals; avoids dependency churn. **Source**: WCAG 2.1 §2.1.2 — focus must be keyboard-operable; manual trap is the standard approach for 2-3 button dialogs.
> 3. **EmailSettingsPage excluded** *(original decision)*: EmailSettingsPage is a standalone route page (`/settings/email`), not a list+detail layout. The form guard pattern intercepts intra-page item selection, not cross-route navigation. Route-level guards (`beforeunload`, React Router `useBlocker`) are out of scope. **Source**: Live code — `SettingsLayout.tsx` uses `navigate({ to: '/settings/email' })` (line 154), confirming route-level ownership.
>    - **Addendum (mid-execution, Human-approved):** User directed adding `isDirty` + amber-pulse save indicators to EmailSettingsPage during the session. This applies the visual dirty-state UX only (save button class `btn-save-dirty`, "Save Changes •" text) — NOT the full `useFormGuard` modal pattern. 3 G23 unit tests added for coverage. The exclusion of `useFormGuard`/`UnsavedChangesModal` remains correct (no list+detail selection to intercept).

---

## Proposed Changes

### MEU-196: Shared Form Guard Infrastructure

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| UnsavedChangesModal 3-button layout (Keep Editing, Discard, Save & Continue) | Spec | 06-gui.md §UX Hardening — Table row definitions |
| `useFormGuard<T>` generic hook with `isDirty`, `onNavigate`, `onSave` | Spec | 06-gui.md §UX Hardening — TypeScript interface |
| Portal-based modal rendering to `document.body` | Local Canon | G20 — Themed portaled modals |
| WCAG 2.1 AA focus trap (`role="alertdialog"`, `aria-modal`, Escape key) | Research-backed | WCAG 2.1 §2.1.2 (keyboard-operable) + §1.3.1 (info/relationships) |
| Amber-pulse CSS animation (`#ffb86c`, 2s ease-in-out) | Spec | 06-gui.md — CSS block with `@keyframes amber-pulse` |
| `prefers-reduced-motion` media query disables animation | Spec | 06-gui.md — `@media` block |
| Button text change "Save" → "Save Changes •" when dirty | Spec | 06-gui.md §Amber-Pulse — "tertiary text indicator" |
| SchedulingLayout refactor to consume shared components | Spec | 06-gui.md §SchedulingLayout Refactor |
| Manual focus trap (no `focus-trap-react` dependency) | Research-backed | Standard pattern for simple modals; avoids npm dependency |
| Auto-focus "Keep Editing" button on modal open | Spec | 06-gui.md §Accessibility requirements |

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-1 | `useFormGuard` returns `showModal=false` when `isDirty=false` and `guardedSelect` is called → `onNavigate` fires immediately | Spec | Call `guardedSelect` when dirty → `onNavigate` must NOT fire |
| AC-2 | `useFormGuard` returns `showModal=true` when `isDirty=true` and `guardedSelect` is called | Spec | — |
| AC-3 | `handleCancel` sets `showModal=false` without calling `onNavigate` | Spec | — |
| AC-4 | `handleDiscard` sets `showModal=false` and calls `onNavigate(pendingTarget)` | Spec | — |
| AC-5 | `handleSaveAndContinue` calls `onSave()`, then `onNavigate(pendingTarget)` on success | Spec | `onSave` rejects → `onNavigate` must NOT fire |
| AC-6 | `UnsavedChangesModal` renders 2 buttons when `onSave` is undefined, 3 buttons when provided | Spec | — |
| AC-7 | Modal has `role="alertdialog"`, `aria-modal="true"`, `aria-labelledby` pointing to heading | Research-backed | — |
| AC-8 | Pressing Escape key dismisses modal (calls `onCancel`) | Spec | — |
| AC-9 | Tab key wraps focus within modal (focus trap) | Research-backed | Tab on last button → focus returns to first button |
| AC-10 | `form-guard.css` defines `@keyframes amber-pulse` and `.btn-save-dirty` class | Spec | — |
| AC-11 | `.btn-save-dirty` has `animation: none` inside `@media (prefers-reduced-motion: reduce)` | Spec | — |
| AC-12 | SchedulingLayout refactored to use shared `UnsavedChangesModal` — inline modal JSX removed | Spec | — |
| AC-13 | SchedulingLayout behavior unchanged after refactor (same 2-button modal, same dirty tracking) | Spec | — |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `ui/src/renderer/src/hooks/useFormGuard.ts` | new | Generic `useFormGuard<T>` hook |
| `ui/src/renderer/src/components/UnsavedChangesModal.tsx` | new | Portal-based modal with focus trap |
| `ui/src/renderer/src/styles/form-guard.css` | new | Amber-pulse animation + reduced-motion |
| `ui/src/renderer/src/features/scheduling/SchedulingLayout.tsx` | modify | Replace inline modal with shared components |
| `ui/src/renderer/src/hooks/__tests__/useFormGuard.test.ts` | new | Hook unit tests |
| `ui/src/renderer/src/components/__tests__/UnsavedChangesModal.test.tsx` | new | Modal unit tests |
| `ui/tests/e2e/test-ids.ts` | modify | Add `FORM_GUARD` test-id constants |
| `ui/tests/e2e/scheduling.test.ts` | modify | Extend Wave 8 — add dirty-guard scenario for SchedulingLayout refactor |

---

### MEU-197: Form Guard Wiring — Market Data Providers

#### Scope Rationale

> **EmailSettingsPage excluded from guard wiring (source-backed exception):** `EmailSettingsPage` is a standalone route page rendered at `/settings/email` via `navigate({ to: '/settings/email' })` in `SettingsLayout.tsx:154`. It has no list+detail item selection pattern — there is nothing to intercept within the page. Guarding cross-route navigation requires `beforeunload` or React Router `useBlocker`, which is explicitly out of scope (see Out of Scope §1). The `useFormGuard` hook intercepts intra-page item selection only.
>
> **Note (mid-execution scope expansion, Human-approved):** `isDirty` + amber-pulse save indicators were added to EmailSettingsPage at user direction. This is a visual-only enhancement (no `useFormGuard`, no `UnsavedChangesModal`). See task 33 in task.md.

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| MarketDataProvidersPage guards on provider selection when dirty | Spec | 06-gui.md §Settings Pages Wiring |
| "off" → "Disabled" label replacement | Spec | 06-gui.md §Status label fix |
| Amber-pulse applied to Save button when form is dirty | Spec | 06-gui.md §Amber-Pulse Save Button |
| Dirty state tracking via form field comparison | Local Canon | SchedulingLayout `policyDirty` pattern |
| All existing tests updated with useFormGuard mock | Local Canon | G18 — Shared Hook Mock Inventory |
| Save & Continue available (parent owns save handler) | Local Canon | `MarketDataProvidersPage.tsx` has inline `saveMutation` on parent |

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-14 | MarketDataProvidersPage: selecting a different provider while form is dirty shows UnsavedChangesModal | Spec | Selecting same provider → no modal |
| AC-15 | MarketDataProvidersPage: "Discard" navigates to new provider, "Keep Editing" stays | Spec | — |
| AC-16 | MarketDataProvidersPage: "Save & Continue" saves current form then navigates | Spec | Save fails → stays on current provider |
| AC-17 | MarketDataProvidersPage: Save button shows `btn-save-dirty` class + "Save Changes •" text when dirty | Spec | Clean form → no dirty class |
| AC-18 | MarketDataProvidersPage: disabled providers show "Disabled" not "off" in the list | Spec | — |
| AC-19 | Existing MarketDataProvidersPage tests still pass (G18 compliance) | Local Canon | — |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `ui/src/renderer/src/features/settings/MarketDataProvidersPage.tsx` | modify | Add `useFormGuard`, dirty tracking, amber-pulse, "Disabled" label |
| `ui/src/renderer/src/features/settings/__tests__/MarketDataProvidersPage.test.tsx` | modify | Add guard tests + update mocks (G18) |
| `ui/tests/e2e/settings-market-data.test.ts` | modify | Extend Wave 6 — add dirty-guard scenario for provider selection |

---

### MEU-198: Form Guard Wiring — CRUD Pages

#### Per-Page Save & Continue Integration Contracts

> **Context**: `useFormGuard` accepts an optional `onSave?: () => Promise<void>`. When provided, the modal renders 3 buttons including "Save & Continue". When absent, only 2 buttons render. The table below documents each page's save architecture and resulting button count.

| Page | Form Owner | Save Trigger | `onSave` Viable? | Modal Buttons | Notes |
|------|-----------|-------------|-------------------|---------------|-------|
| **TradePlanPage** | Parent (`handleSave` at line 251) | Parent `onClick` | ✅ Yes | 3 (Keep Editing, Discard, Save & Continue) | Parent owns `handleSave` — wrap as zero-arg `onSave` |
| **WatchlistPage** | Parent (`handleSave` at line 173) | Parent `onClick` | ✅ Yes | 3 (Keep Editing, Discard, Save & Continue) | Parent owns `handleSave` — wrap as zero-arg `onSave` |
| **AccountsHome** | Child (`AccountDetailPanel` at line 108, `useForm` at line 78) | Child `form.handleSubmit(onSave)` | ❌ No (child-owned form) | 2 (Keep Editing, Discard) | Save is inside child's React Hook Form submit. Imperative handle needed for 3-button; deferred. |
| **TradesLayout** | Child (`TradeDetailPanel` at line 70, `useForm` at line 91) | Child `form.handleSubmit(onSave)` via prop | ❌ No (child-owned form) | 2 (Keep Editing, Discard) | `onSave` prop is typed `(data: TradeFormData) => void` — parent cannot trigger submit without imperative ref. Deferred. |

> **Source-backed exception**: Pages with child-owned React Hook Form instances cannot provide a zero-arg `onSave` without adding imperative submit handles (`useImperativeHandle` + `forwardRef`). That refactor is deferred to keep MEU-198 focused on the guard pattern itself. The 2-button modal (Keep Editing, Discard) still prevents data loss.

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| AccountsHome guards on account selection when dirty | Spec | 06-gui.md §CRUD Pages Wiring |
| TradesLayout guards on trade selection when dirty | Spec | 06-gui.md §CRUD Pages Wiring |
| TradePlanPage guards on plan selection when dirty | Spec | 06-gui.md §CRUD Pages Wiring |
| WatchlistPage guards on watchlist selection when dirty | Spec | 06-gui.md §CRUD Pages Wiring |
| Amber-pulse on Save buttons for all CRUD pages | Spec | 06-gui.md §Amber-Pulse |
| Save & Continue only on pages with parent-owned save | Local Canon | Per-page contract table above |
| Dirty tracking: child `onDirtyChange` callback for Accounts/Trades | Local Canon | New prop on detail panels to report dirty state upward |
| All existing tests updated with useFormGuard mock | Local Canon | G18 — Shared Hook Mock Inventory |

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-20 | AccountsHome: selecting different account while dirty shows modal (2-button) | Spec | Clean form → no modal |
| AC-21 | AccountsHome: Save button shows amber-pulse when dirty | Spec | — |
| AC-22 | TradesLayout: selecting different trade while dirty shows modal (2-button) | Spec | — |
| AC-23 | TradesLayout: Save button shows amber-pulse when dirty | Spec | — |
| AC-24 | TradePlanPage: selecting different plan while dirty shows modal (3-button) | Spec | — |
| AC-25 | TradePlanPage: Save button shows amber-pulse when dirty | Spec | — |
| AC-26 | WatchlistPage: selecting different watchlist while dirty shows modal (3-button) | Spec | — |
| AC-27 | WatchlistPage: Save button shows amber-pulse when dirty | Spec | — |
| AC-28 | Pages with `onSave`: "Save & Continue" saves+navigates; save failure → stays | Spec | Save rejects → no navigation |
| AC-29 | Existing tests for all 4 pages still pass (G18 compliance) | Local Canon | — |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `ui/src/renderer/src/features/accounts/AccountsHome.tsx` | modify | Add `useFormGuard`, dirty tracking via `onDirtyChange`, amber-pulse |
| `ui/src/renderer/src/features/accounts/AccountDetailPanel.tsx` | modify | Add `onDirtyChange` prop to report dirty state to parent |
| `ui/src/renderer/src/features/trades/TradesLayout.tsx` | modify | Add `useFormGuard`, dirty tracking via `onDirtyChange`, amber-pulse |
| `ui/src/renderer/src/features/trades/TradeDetailPanel.tsx` | modify | Add `onDirtyChange` prop to report dirty state to parent |
| `ui/src/renderer/src/features/planning/TradePlanPage.tsx` | modify | Add `useFormGuard`, dirty tracking, amber-pulse, `onSave` for Save & Continue |
| `ui/src/renderer/src/features/planning/WatchlistPage.tsx` | modify | Add `useFormGuard`, dirty tracking, amber-pulse, `onSave` for Save & Continue |
| `ui/src/renderer/src/features/accounts/__tests__/*` | modify | Add guard tests + update mocks (G18) |
| `ui/src/renderer/src/features/trades/__tests__/*` | modify | Add guard tests + update mocks (G18) |
| `ui/src/renderer/src/features/planning/__tests__/*` | modify | Add guard tests + update mocks (G18) |
| `ui/tests/e2e/account-crud.test.ts` | modify | Extend Wave 2 — add dirty-guard scenario for account selection |
| `ui/tests/e2e/position-size.test.ts` | modify | Extend Wave 4 — add dirty-guard scenario for plan selection |

---

## Out of Scope

- Router-level navigation guard (e.g., `beforeunload`, React Router `useBlocker`) — this project guards intra-page item selection, not cross-route navigation. EmailSettingsPage's `useFormGuard`/`UnsavedChangesModal` is excluded per this rule (standalone route, no list+detail). **Note:** `isDirty` + amber-pulse visual indicators were added to EmailSettingsPage mid-execution at user direction (Human-approved) — this is a visual-only enhancement, not a navigation guard.
- Undo/Redo stack for form changes
- Auto-save timer (forms save only on explicit user action)
- Imperative submit handles for child-owned forms (Accounts, Trades) — deferred; these pages get 2-button modal instead of 3-button

---

## BUILD_PLAN.md Audit

P2.1 section and MEU-196/197/198 rows were added earlier in this session. After execution:
- Update status column from ⬜ to ✅ for completed MEUs
- Verify total count remains 253

```powershell
rg "gui-ux-hardening" docs/BUILD_PLAN.md *> C:\Temp\zorivest\bp-audit-slug.txt; Get-Content C:\Temp\zorivest\bp-audit-slug.txt
# Expected: 0 matches (project slug not in hub)
```

```powershell
rg "MEU-196|MEU-197|MEU-198" docs/BUILD_PLAN.md *> C:\Temp\zorivest\bp-audit-meu.txt; Get-Content C:\Temp\zorivest\bp-audit-meu.txt
# Expected: matches in MEU summary table
```

---

## Verification Plan

### 1. TypeScript Build Gate
```powershell
cd ui; npm run build *> C:\Temp\zorivest\ui-build.txt; Get-Content C:\Temp\zorivest\ui-build.txt | Select-Object -Last 20
```

### 2. Vitest Unit Tests
```powershell
cd ui; npx vitest run *> C:\Temp\zorivest\vitest.txt; Get-Content C:\Temp\zorivest\vitest.txt | Select-Object -Last 40
```

### 3. Anti-Placeholder Scan
```powershell
rg "TODO|FIXME|NotImplementedError" ui/src/renderer/src/hooks/useFormGuard.ts ui/src/renderer/src/components/UnsavedChangesModal.tsx ui/src/renderer/src/styles/form-guard.css *> C:\Temp\zorivest\placeholder-scan.txt; Get-Content C:\Temp\zorivest\placeholder-scan.txt
```

### 4. CSS Import Verification
```powershell
rg "form-guard" ui/src/renderer/src/ *> C:\Temp\zorivest\css-import.txt; Get-Content C:\Temp\zorivest\css-import.txt
```

### 5. E2E Tests — Extend Existing Waves (per 06-gui.md:565)

Dirty-guard E2E scenarios extend Waves 2, 4, 6, 8 — no new wave row needed.

```powershell
# Wave 8: Scheduling guard (MEU-196 refactor)
(& { cd ui; npm run build; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }; npx playwright test scheduling.test.ts }) *> C:\Temp\zorivest\e2e-wave8.txt; Get-Content C:\Temp\zorivest\e2e-wave8.txt | Select-Object -Last 30
```

```powershell
# Wave 6: Market Data guard (MEU-197)
(& { cd ui; npm run build; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }; npx playwright test settings-market-data.test.ts }) *> C:\Temp\zorivest\e2e-wave6.txt; Get-Content C:\Temp\zorivest\e2e-wave6.txt | Select-Object -Last 30
```

```powershell
# Wave 2 + 4: Accounts + Plans guard (MEU-198)
(& { cd ui; npm run build; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }; npx playwright test account-crud.test.ts position-size.test.ts }) *> C:\Temp\zorivest\e2e-wave24.txt; Get-Content C:\Temp\zorivest\e2e-wave24.txt | Select-Object -Last 30
```

### 6. MEU Gate (per MEU)
```powershell
uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\meu-gate.txt; Get-Content C:\Temp\zorivest\meu-gate.txt | Select-Object -Last 50
```

---

## Open Questions

> [!WARNING]
> All spec gaps resolved. Decisions documented in "User Review Required" section:
> 1. ✅ Save & Continue: conditional per page (3-button for parent-owned save, 2-button for child-owned)
> 2. ✅ Focus trap: manual implementation (Research-backed: WCAG 2.1 §2.1.2)
> 3. ✅ EmailSettingsPage: guard excluded (standalone route, not list+detail — source: live `SettingsLayout.tsx:154`). `isDirty` + amber-pulse indicators added mid-execution (Human-approved, visual-only — no `useFormGuard`/modal). 3 G23 tests cover the enhancement.

---

## Research References

- [06-gui.md §UX Hardening](../../build-plan/06-gui.md#ux-hardening--unsaved-changes-guard) — canonical spec
- [WCAG 2.1 §2.1.2 No Keyboard Trap](https://www.w3.org/WAI/WCAG21/Understanding/no-keyboard-trap.html) — focus trap requirement
- [WCAG 2.1 §1.4.1 Use of Color](https://www.w3.org/WAI/WCAG21/Understanding/use-of-color.html) — amber + animation + text as 3 redundant cues
- Emerging Standard G20 — Portal modal pattern
- Emerging Standard G18 — Shared hook mock inventory
