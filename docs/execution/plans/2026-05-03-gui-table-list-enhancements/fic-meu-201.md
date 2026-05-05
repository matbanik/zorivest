# Feature Intent Contract: MEU-201 — Trade Plans Table Enhancements

> **MEU**: MEU-201 (`gui-tradeplans-table-enhance`)
> **Matrix Item**: 35n
> **Depends on**: MEU-199 (infrastructure primitives) ✅
> **Source**: [implementation-plan.md §MEU-201](implementation-plan.md), [proposal §MEU-201](gui-table-list-enhancements-proposal.md)

## Current State

`TradePlanPage.tsx` (984 LOC) has:
- Manual `useMemo` filter with status and conviction dropdowns (lines 191-197)
- Plan list rendered as card buttons (lines 489-530)
- Single-delete confirmation already wired via `useConfirmDelete` (line 375)
- `ConfirmDeleteModal` already imported and rendered (line 7, 958)
- No multi-select or bulk operations
- No text search filter (only dropdown filters exist)

## Acceptance Criteria

### AC-1: Multi-select row checkboxes
- Each plan card renders a `SelectionCheckbox` as the first inline element
- A header `SelectionCheckbox` toggles all visible (filtered) plans
- Selected cards receive a visual highlight (e.g., `bg-bg-subtle` or accent border)
- Checkbox click does NOT trigger plan detail navigation (stopPropagation)
- **Source**: `Spec` (proposal §2.2, §MEU-201)

### AC-2: Bulk action bar
- When ≥1 plan is selected, `BulkActionBar` appears showing "{N} selected" count
- Bar contains a "Delete Selected" button
- Clicking "Delete Selected" triggers `ConfirmDeleteModal` in bulk mode with count
- On confirm, each selected plan is deleted via individual `DELETE /api/v1/trade-plans/{id}` calls (D4: individual calls)
- After bulk delete completes, selection is cleared and plans list is refetched
- **Source**: `Spec` (proposal §2.2, §MEU-201), `Human-approved` (D4)

### AC-3: Text search filter
- `TableFilterBar` renders above the plan list with a search input
- Typing filters plans by ticker or strategy name (case-insensitive substring match)
- The existing status and conviction dropdown filters are preserved alongside the search
- Filter state resets when the search input is cleared
- **Source**: `Spec` (proposal §2.3, §MEU-201)

### AC-4: Delete confirmation remains functional (existing)
- Single-plan delete confirmation in detail panel continues to work
- Verify no regression from multi-select additions
- **Source**: `Local Canon` (existing implementation in `TradePlanPage.tsx:374-392`)

### AC-5: data-testid attributes
- Required IDs: `select-all-plan-checkbox`, `plan-row-checkbox-{id}`, `bulk-action-bar`, `bulk-delete-btn`, `table-search-input`
- **Source**: `Local Canon` ([06-gui.md §GUI Shipping Gate](../../build-plan/06-gui.md#gui-shipping-gate-mandatory-for-all-gui-meus))

### AC-6: No regression
- All 88 existing `planning.test.tsx` tests continue to pass
- No TypeScript compilation errors
- **Source**: `Local Canon` (AGENTS.md §TDD Protocol)

## Out of Scope

- TanStack Table migration (card-based layout preserved; TanStack deferred)
- Undo-toast pattern (D2: modal only)
- Batch DELETE API endpoint (D4: individual calls in loop)
- Column sorting headers (plans use card layout, not table columns)

## Test Plan

Each AC maps to ≥1 Vitest assertion:

| AC | Test Description | Expected Result |
|----|-----------------|-----------------|
| AC-1 | Renders `SelectionCheckbox` in each plan card | checkbox rendered with `data-testid="plan-row-checkbox-{id}"` |
| AC-1 | Header checkbox toggles all visible plans | all plan checkboxes become checked |
| AC-2 | `BulkActionBar` appears when ≥1 plan selected | bar visible with "{N} selected" text |
| AC-2 | "Delete Selected" click opens bulk confirm modal | modal renders with count |
| AC-3 | Search input filters by ticker | only matching plans shown |
| AC-3 | Search input filters by strategy name | only matching plans shown |
| AC-5 | All required `data-testid` attributes present | `getByTestId` succeeds for each |
| AC-6 | Existing 88 tests pass without modification | 88/88 pass |
