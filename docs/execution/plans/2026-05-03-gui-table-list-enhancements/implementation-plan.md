---
project: "2026-05-03-gui-table-list-enhancements"
meus: ["MEU-199", "MEU-200", "MEU-201", "MEU-202", "MEU-203"]
priority: "P2.2"
status: "in_progress"
---

# Implementation Plan: GUI Table & List Enhancements

> **Source**: User request (2026-05-03) + [approved proposal](gui-table-list-enhancements-proposal.md)
> **Build Plan Ref**: [06-gui.md](../../build-plan/06-gui.md), [build-priority-matrix.md §P2.2](../../build-plan/build-priority-matrix.md)
> **Depends on**: MEU-196/197/198 ✅ (GUI UX Hardening)

## Scope

5 MEUs implementing three enhancement categories across 5 GUI surfaces:

1. **Delete confirmation dialogs** — Mandatory confirmation before any destructive action (`Spec`: WCAG 2.1 AA, proposal §2.1)
2. **Multi-select + bulk delete** — Checkbox-based row selection with contextual action bar (`Spec`: proposal §2.2)
3. **Unified filter/sort** — TanStack Table standardization (sorting, filtering, pagination) (`Spec`: proposal §2.3)

## Resolved Decisions

> Decisions from [proposal §9 Open Questions](gui-table-list-enhancements-proposal.md#9-open-questions), resolved before execution.

| # | Question | Decision | Source |
|---|----------|----------|--------|
| D1 | Should Trades table receive `ConfirmDeleteModal`? | **Yes** — already wired during ad-hoc GUI session. Evidence: [`TradesLayout.tsx:7,233,345`](../../../ui/src/renderer/src/features/trades/TradesLayout.tsx). | `Human-approved` |
| D2 | Undo toast vs confirmation modal? | **Confirmation modal only.** Consistent with existing `UnsavedChangesModal` pattern. Undo-toast deferred to future UX iteration. | `Human-approved` |
| D3 | Sidebar lists vs full tables for Policies/Templates? | **Keep sidebar list pattern** with enhanced filter/sort overlays. Full table migration out of scope. | `Local Canon` ([proposal §MEU-203 note](gui-table-list-enhancements-proposal.md#L290-291)) |
| D4 | Batch DELETE endpoints vs individual calls? | **Individual DELETE calls in loop.** No batch endpoints exist in the API layer; adding them is out of scope for this GUI project. | `Local Canon` (no batch endpoints in [routes/](../../../packages/api/src/zorivest_api/routes/)) |

## E2E Wave Assignment

> **Source**: [06-gui.md §Wave Activation Schedule](../../build-plan/06-gui.md#wave-activation-schedule), [06-gui.md §GUI Shipping Gate](../../build-plan/06-gui.md#gui-shipping-gate-mandatory-for-all-gui-meus)

MEU-199–203 are assigned to **Wave 10** in the E2E Wave Activation Schedule. During execution, the implementing agent must:

1. **Register `data-testid` constants** in `ui/tests/e2e/test-ids.ts` for all new interactive elements (confirm modal, bulk action bar, filter bar, selection checkboxes, sortable headers)
2. **Write Playwright E2E tests** per surface MEU that exercise: delete confirmation flow, bulk selection + delete, and filter/sort interaction
3. **Update Wave 10 row** in `06-gui.md:428` with concrete test file names, test counts, and `data-testid` IDs added

### Planned `data-testid` Constants

| Constant | Value | Component |
|----------|-------|-----------|
| `CONFIRM_DELETE_MODAL` | `confirm-delete-modal` | `ConfirmDeleteModal` |
| `CONFIRM_DELETE_CONFIRM_BTN` | `confirm-delete-confirm-btn` | `ConfirmDeleteModal` |
| `CONFIRM_DELETE_CANCEL_BTN` | `confirm-delete-cancel-btn` | `ConfirmDeleteModal` |
| `BULK_ACTION_BAR` | `bulk-action-bar` | `BulkActionBar` |
| `BULK_DELETE_BTN` | `bulk-delete-btn` | `BulkActionBar` |
| `BULK_SELECTED_COUNT` | `bulk-selected-count` | `BulkActionBar` |
| `TABLE_FILTER_BAR` | `table-filter-bar` | `TableFilterBar` |
| `TABLE_FILTER_SEARCH` | `table-filter-search` | `TableFilterBar` |
| `SELECTION_CHECKBOX` | `selection-checkbox` | `SelectionCheckbox` |
| `SELECT_ALL_CHECKBOX` | `select-all-checkbox` | `SelectionCheckbox` (header) |

---

### MEU-199: `gui-table-list-primitives` (Infrastructure)

> **Matrix Item**: 35l
> **Depends on**: MEU-196 ✅
> **Unblocks**: MEU-200, MEU-201, MEU-202, MEU-203

Shared reusable components:

| Deliverable | File | Purpose |
|-------------|------|---------|
| `ConfirmDeleteModal` | `components/ConfirmDeleteModal.tsx` | Portal-based delete confirmation (single + bulk modes), WCAG 2.1 AA |
| `useConfirmDelete` | `hooks/useConfirmDelete.ts` | Hook for delete confirmation state management |
| `BulkActionBar` | `components/BulkActionBar.tsx` | Contextual toolbar ("{N} selected" + action buttons) |
| `SortableColumnHeader` | `components/SortableColumnHeader.tsx` | TanStack-compatible sortable header with `▲▼` indicators |
| `TableFilterBar` | `components/TableFilterBar.tsx` | Reusable search input + category filter dropdown bar |
| `SelectionCheckbox` | `components/SelectionCheckbox.tsx` | Row/header checkbox with indeterminate state |
| `useTableSelection` | `hooks/useTableSelection.ts` | TanStack row selection state wrapper |
| `table-enhancements.css` | `styles/table-enhancements.css` | Styles for selection highlight, bulk bar, sort indicators |

**Tests**: Vitest: ConfirmDeleteModal (open/close, single/bulk, escape, focus trap), useConfirmDelete (state transitions), BulkActionBar (visibility, count display)

---

### MEU-200: `gui-accounts-table-enhance` (Accounts)

> **Matrix Item**: 35m
> **Depends on**: MEU-199

| Deliverable | Description |
|-------------|-------------|
| Account deletion confirmation | Wrap `handleDeleteAccount` with `useConfirmDelete` |
| Multi-select | Add row selection checkboxes to accounts table |
| Bulk delete | Wire `BulkActionBar` → batch `DELETE /api/v1/accounts/{id}` (D4: individual calls) |
| Filter bar | Search by name/institution, filter by account type dropdown |
| Column sorting | TanStack sorting on: Name, Type, Institution, Balance, Updated |

**Current**: `AccountsHome.tsx` uses manual `useMemo` sort/filter
**Target**: TanStack Table with shared components
**Tests**: Vitest: filter/sort state, bulk selection count; Playwright E2E: delete confirmation flow, navigation reachability

---

### MEU-201: `gui-tradeplans-table-enhance` (Trade Plans)

> **Matrix Item**: 35n
> **Depends on**: MEU-199

| Deliverable | Description |
|-------------|-------------|
| Trade plan deletion confirmation | Wrap delete handler with `useConfirmDelete` |
| Multi-select | Add row selection checkboxes to trade plans list |
| Bulk delete | Wire `BulkActionBar` → batch `DELETE /api/v1/plans/{id}` (D4: individual calls) |
| Filter bar | Search by ticker/strategy, filter by status/conviction/direction |
| Column sorting | TanStack sorting on: Ticker, Strategy, Status, Conviction, Entry, Target, Created |

**Current**: `TradePlanPage.tsx` has manual filter
**Target**: TanStack Table with shared components
**Tests**: Vitest: filter/sort state; Playwright E2E: bulk delete confirmation

---

### MEU-202: `gui-watchlist-table-enhance` (Watchlist Tickers)

> **Matrix Item**: 35o
> **Depends on**: MEU-199

| Deliverable | Description |
|-------------|-------------|
| Ticker removal confirmation | Wrap remove-ticker handler with `useConfirmDelete` |
| Multi-select | Add row selection checkboxes to watchlist ticker table |
| Bulk remove | Wire `BulkActionBar` → batch `DELETE /api/v1/watchlists/{id}/tickers/{ticker}` (D4: individual calls) |
| Filter bar | Search by ticker/notes |
| Column sorting | Standardize sort on: Ticker, Price, Change, Change%, Position Size, Added |

**Current**: `WatchlistTable.tsx` has manual sort implementation
**Target**: TanStack Table with shared sort components
**Tests**: Vitest: selection state; Playwright E2E: ticker removal confirmation

---

### MEU-203: `gui-scheduling-table-enhance` (Policies + Email Templates)

> **Matrix Item**: 35p
> **Depends on**: MEU-199

> **Note**: Policies and Templates share `SchedulingLayout.tsx` — combining them in one MEU avoids cross-MEU layout conflicts. The sidebar list pattern is preserved (D3), with collapsible filter row instead of table headers.

| Deliverable | Description |
|-------------|-------------|
| **Policies** | |
| Policy deletion confirmation | Wrap delete handler with `useConfirmDelete` |
| Multi-select | Add selection to PolicyList sidebar |
| Bulk delete | Wire `BulkActionBar` → batch policy deletion (D4: individual calls) |
| Filter/sort | Search by name, filter by enabled/disabled status, sort by name/next-run/last-run |
| **Email Templates** | |
| Template deletion confirmation | Wrap delete handler with `useConfirmDelete` (protect default template) |
| Multi-select | Add selection to EmailTemplateList sidebar |
| Bulk delete | Wire `BulkActionBar` → batch template deletion (skip protected defaults) |
| Filter/sort | Search by name, sort by name/modified date |

**Current**: `PolicyList.tsx` and `EmailTemplateList.tsx` are simple sidebar lists
**Target**: Enhanced lists with filter/sort/select capabilities
**Tests**: Vitest: filter/sort state for both; Playwright E2E: delete confirmation for both

---

## Verification Plan

```powershell
# Vitest (TypeScript tests) — run from ui/ workspace
cd ui && npx vitest run *> C:\Temp\zorivest\vitest.txt; Get-Content C:\Temp\zorivest\vitest.txt | Select-Object -Last 40

# TypeScript type check — run from ui/ workspace
cd ui && npx tsc --noEmit *> C:\Temp\zorivest\tsc.txt; Get-Content C:\Temp\zorivest\tsc.txt | Select-Object -Last 30

# Playwright E2E (after build) — run from ui/ workspace
cd ui && npm run build *> C:\Temp\zorivest\build.txt; npx playwright test *> C:\Temp\zorivest\e2e.txt; Get-Content C:\Temp\zorivest\e2e.txt | Select-Object -Last 30

# Anti-placeholder scan — run from repo root
rg "TODO|FIXME|NotImplementedError" ui/src/renderer/src/components/ ui/src/renderer/src/hooks/ *> C:\Temp\zorivest\placeholder.txt; Get-Content C:\Temp\zorivest\placeholder.txt
```

## TDD Workflow (Mandatory per AGENTS.md §228-241)

> **Source**: [`AGENTS.md:228-241`](../../../AGENTS.md) — FIC-Based TDD Workflow (Mandatory)

Each surface MEU (MEU-200 through MEU-203) must follow the FIC-based TDD cycle during execution:

1. **Write source-backed FIC** — Feature Intent Contract with acceptance criteria (AC-1, AC-2, ...) before any code. Each AC labeled `Spec`, `Local Canon`, `Research-backed`, or `Human-approved`.
2. **Write ALL tests FIRST** — every AC becomes at least one Vitest assertion
3. **Run tests** — confirm they FAIL (Red phase). **Save failure output as FAIL_TO_PASS evidence.**
4. **Implement** — write just enough code to make tests pass (Green phase)
5. **Refactor** — clean up while keeping tests green
6. **Run checks**: `cd ui && npx vitest run`, `cd ui && npx tsc --noEmit`

MEU-199 (Infrastructure) was implemented prior to this TDD obligation being surfaced; its components already have passing Vitest tests (ConfirmDeleteModal, useConfirmDelete, BulkActionBar). Remaining MEU-200–203 must follow the full FIC cycle.

> ⚠️ **Test Immutability**: Once tests are written in Red phase, do NOT modify test assertions in Green phase. Fix the implementation, not the test.

---

## Ad-Hoc Bug Fixes (2026-05-03)

The following issues were discovered and fixed during interactive testing of the GUI enhancements. They are outside the planned MEU scope but block normal GUI operation.

### AH-1: Trade Plan Creation 422 Error

- **Symptom**: Creating a new trade plan returned `422 Unprocessable Entity — Extra inputs are not permitted`.
- **Root cause**: `TradePlanPage.tsx` `handleSave` sent `linked_trade_id: null` on POST. Backend `CreatePlanRequest` uses `extra="forbid"` and does not include `linked_trade_id` (only `UpdatePlanRequest` does).
- **Fix**: Conditionally include `linked_trade_id` only during updates, not creates.
- **File**: `ui/src/renderer/src/features/planning/TradePlanPage.tsx` (line ~302-322)

### AH-2: Trade Creation 422 Error

- **Symptom**: Creating a new trade returned `422 — realized_pnl: Input should be a valid number, input: null`.
- **Root cause**: `TradesLayout.tsx` spread the form data (which defaults `realized_pnl: null`) directly into the POST payload. Backend `CreateTradeRequest` expects `realized_pnl: float = 0.0` (not nullable).
- **Fix**: Apply nullish coalescing (`?? 0`) to `realized_pnl` and `notes` before sending CREATE payload.
- **File**: `ui/src/renderer/src/features/trades/TradesLayout.tsx` (line ~200-213)

### AH-3: Screenshot Upload 404 on New Trades

- **Symptom**: `POST /api/v1/trades/%28new%29/images` → 404. Screenshot panel attempted API calls using the `(new)` placeholder exec_id.
- **Root cause**: `ScreenshotPanel.tsx` had no guard against the `(new)` placeholder trade ID.
- **Fix**: Added `isNewTrade` guard. Query disabled, upload/paste/drop silently ignored, panel shows "Save the trade first to attach screenshots."
- **File**: `ui/src/renderer/src/features/trades/ScreenshotPanel.tsx`

### AH-4: Clipboard Paste Not Working in Electron

- **Symptom**: Ctrl+V paste of images into ScreenshotPanel did nothing.
- **Root cause**: Paste handler used React `onPaste` on a `<div>`, which only fires when that specific DOM element has focus. In Electron, Ctrl+V is intercepted by the app menu accelerator before reaching the element.
- **Fix**: Replaced `onPaste` prop with `window.addEventListener('paste', ...)` inside `useEffect`. Fires regardless of focus, only processes `image/*` clipboard items.
- **File**: `ui/src/renderer/src/features/trades/ScreenshotPanel.tsx`

### AH-5: Account Archive Button Showing Delete Confirmation

- **Symptom**: Archive button showed 🗑 "Delete" themed confirmation modal instead of archive-specific messaging.
- **Root cause**: `ConfirmDeleteModal` had no action differentiation — always showed destructive (red/trash) theme.
- **Fix**: Added `action` prop (`'delete'` | `'archive'`) with dynamic theming: amber/📦 for archive vs red/🗑 for delete. Updated `AccountDetailPanel` to use `action="archive"`.
- **Files**: `ui/src/renderer/src/components/ConfirmDeleteModal.tsx`, `ui/src/renderer/src/features/accounts/AccountDetailPanel.tsx`

### AH-6: Account Create — Phantom Unsaved Changes Dialog

- **Symptom**: After creating a new account, clicking any account triggered the "Unsaved Changes" modal. "Keep Editing" appeared to do nothing.
- **Root cause**: Two issues:
  1. `onCreated` callback only called `setShowCreateForm(false)` without resetting `childDirty`. The create form unmounted before `useEffect` could propagate `isDirty=false`.
  2. Create-mode `AccountDetailPanel` was missing `ref={panelRef}`, making "Save & Continue" silently fail.
- **Fix**: Added `setChildDirty(false)` to `onCreated` callback. Added `ref={panelRef}` to create-mode panel.
- **File**: `ui/src/renderer/src/features/accounts/AccountsHome.tsx`

### AH-7: Watchlist Sidebar Missing Search/Bulk Delete

- **Symptom**: Watchlist list sidebar has no search filter, multi-select, or bulk delete — inconsistent with Accounts, Policies, and Templates sidebars.
- **Root cause**: MEU-202 scope was "Watchlist Tickers" (the ticker table inside a watchlist), not the sidebar list of watchlists themselves.
- **Fix**: Add search input, `SelectionCheckbox` per row + select-all, `BulkActionBar`, and `ConfirmDeleteModal` to `WatchlistPage.tsx` sidebar.
- **File**: `ui/src/renderer/src/features/planning/WatchlistPage.tsx`

### AH-8: Trades Table Missing Multi-select/Bulk Delete

- **Symptom**: Trades table has filter bar and single-delete confirmation but no multi-select checkboxes or bulk delete — inconsistent with Trade Plans, Accounts, and Watchlist tables.
- **Root cause**: Trades table was not scoped as a separate MEU for multi-select/bulk delete enhancements.
- **Fix**: Add `SelectionCheckbox` column to `TradesTable.tsx` (via TanStack column), `BulkActionBar`, and bulk delete handler in `TradesLayout.tsx`.
- **Files**: `ui/src/renderer/src/features/trades/TradesTable.tsx`, `ui/src/renderer/src/features/trades/TradesLayout.tsx`

### AH-10: Tiered Account Deletion with Trade Warning

- **Symptom**: Deleting an account with linked trades gives no warning about data impact. Trades silently reassigned or deletion blocked with a 409 error the user doesn't understand.
- **Root cause**: No pre-delete check for associated trades/plans, and no second-confirmation step for accounts with linked data.
- **Fix**:
  - **Backend**: New `AccountService.get_trade_counts()` method (proper UoW session management). New `POST /accounts:trade-counts` lightweight batch endpoint with `extra="forbid"` and `min_length=1` / `max_length=100` validation. Refactored route to delegate to service instead of direct UoW access.
  - **Frontend**: New `TradeWarningModal` component (portal-based, WCAG 2.1 AA: `role="alertdialog"`, focus trap, 48px bold red trade count display). Two-stage deletion flow in `AccountsHome.tsx` (bulk) and `AccountDetailPanel.tsx` (single): first confirmation → trade count check → sequential `TradeWarningModal` for each account with trades → force-delete (reassign to SYSTEM_DEFAULT).
  - **Data**: Extended `Account` interface with `trade_count`. Added `fetchTradeCounts` utility.
- **Files**:
  - `packages/core/src/zorivest_core/services/account_service.py` — new `get_trade_counts()` method
  - `packages/api/src/zorivest_api/routes/accounts.py` — new `:trade-counts` endpoint
  - `ui/src/renderer/src/components/TradeWarningModal.tsx` — new component
  - `ui/src/renderer/src/hooks/useAccounts.ts` — `fetchTradeCounts` utility, `Account.trade_count`
  - `ui/src/renderer/src/features/accounts/AccountsHome.tsx` — two-stage bulk delete
  - `ui/src/renderer/src/features/accounts/AccountDetailPanel.tsx` — two-stage single delete

### AH-11: TDD Tests for Tiered Deletion Services

- **Symptom**: New services from AH-10 lacked test coverage.
- **Fix**: Comprehensive TDD tests following existing patterns:
  - **Python service tests** (`test_service_trade_counts.py`): 6 tests covering single/multi account, None handling, empty input, UoW lifecycle
  - **Python API tests** (`test_api_trade_counts.py`): 8 tests covering response shape, input validation (empty, missing, extra fields), boundary limits (100 max), service delegation
  - **Frontend component tests** (`TradeWarningModal.test.tsx`): 19 tests covering rendering, count display (trade+plan combo, singular/plural), button handlers, ARIA accessibility, focus trap, escape key, backdrop click, loading state, data-testid
  - **Test mock updates**: Added `fetchTradeCounts` mock to `AccountsHome.test.tsx`, `AccountsHome.enhance.test.tsx`, and `AccountDetailPanel.test.tsx`
- **Files**:
  - `tests/unit/test_service_trade_counts.py` — 6 tests
  - `tests/unit/test_api_trade_counts.py` — 8 tests
  - `ui/src/renderer/src/components/__tests__/TradeWarningModal.test.tsx` — 19 tests
  - `ui/src/renderer/src/features/accounts/__tests__/AccountsHome.test.tsx` — mock update
  - `ui/src/renderer/src/features/accounts/__tests__/AccountsHome.enhance.test.tsx` — mock update
  - `ui/src/renderer/src/features/accounts/__tests__/AccountDetailPanel.test.tsx` — mock update

### AH-12: Tradier API Hardening — Accept Header + Provider-Specific Validators

- **Symptom**: Saving and testing the Tradier API key returned "Unexpected response" in the Market Data Providers settings page. The "Save Changes" button never reset to its normal state after save.
- **Root cause (backend)**: Two issues:
  1. `provider_registry.py` — Tradier's `headers_template` was missing `Accept: application/json`, causing Tradier to respond with XML instead of JSON. The generic JSON validator then failed parsing.
  2. `provider_connection_service.py` — `_interpret_response` used a generic validator for all providers. Tradier returns `{"profile": {"account": ...}}` and Alpaca returns `{"id": ..., "status": ...}` — both need provider-specific validation.
- **Root cause (frontend)**: `MarketDataProvidersPage.tsx` — After successful save, the form state retained `api_key` and `api_secret` values, keeping the form in a "dirty" state and preventing the "Save Changes" button from resetting.
- **Fix**:
  - **Registry**: Added `"Accept": "application/json"` to Tradier's `headers_template` in `provider_registry.py`.
  - **Service**: Added `_validate_tradier()` (checks for `profile` key) and `_validate_alpaca()` (checks for `id` key) provider-specific validators in `provider_connection_service.py`. Dispatcher in `_interpret_response` selects validator by provider name.
  - **UI**: Reset `api_key` and `api_secret` to empty strings in form state after successful save in `MarketDataProvidersPage.tsx`.
- **Files**:
  - `packages/infrastructure/src/zorivest_infra/market_data/provider_registry.py` — Accept header
  - `packages/core/src/zorivest_core/services/provider_connection_service.py` — Provider-specific validators
  - `ui/src/renderer/src/features/settings/MarketDataProvidersPage.tsx` — Dirty state reset

### AH-13: TDD Tests for Tradier Hardening

- **Symptom**: New validators and header configuration from AH-12 lacked test coverage.
- **Fix**: Comprehensive TDD tests following existing patterns:
  - **Provider registry tests** (`test_provider_registry.py`): New `TestTradierAcceptHeader` class — validates that `Accept: application/json` is present in Tradier's headers template.
  - **Provider connection service tests** (`test_provider_connection_service.py`): Replaced generic `test_validate_provider_response_success` with provider-specific tests: `test_validate_tradier_response_valid_profile`, `test_validate_alpaca_response_valid_id`, `test_validate_tradier_xml_response_failure`. Validates that XML responses correctly trigger failure.
  - **Frontend tests** (`MarketDataProvidersPage.test.tsx`): Added tests verifying that clicking Save resets `api_key`/`api_secret` form state and clears the dirty indicator on the "Save Changes" button.
- **Files**:
  - `tests/unit/test_provider_registry.py` — Accept header validation
  - `tests/unit/test_provider_connection_service.py` — Provider-specific validator tests
  - `ui/src/renderer/src/features/settings/__tests__/MarketDataProvidersPage.test.tsx` — Dirty state reset tests

### MCP System Audit (2026-05-04)

- **Purpose**: Comprehensive health check of all 13 MCP compound tools / 74 actions to verify no regressions from the Tradier hardening and ad-hoc changes.
- **Result**: 68/70 functional tests pass (97.1%). Zero regressions vs baseline v2.
- **Report**: [`.agent/context/MCP/mcp-tool-audit-report.md`](../../../.agent/context/MCP/mcp-tool-audit-report.md)
- **Baseline**: Updated to v3 at `.agent/skills/mcp-audit/resources/baseline-snapshot.json`
- **Known pre-existing issues**: `market.news` (503 — Finnhub 422), `market.filings` (503 — normalizer not configured)

### Verification

- **Frontend test suite**: 635 tests pass, zero regressions
- **Backend test suite**: 2768 tests pass, zero regressions
- **Pyright**: 0 errors, 0 warnings
- **MCP Audit**: 68/70 pass, 0 regressions
- **Date**: 2026-05-04
