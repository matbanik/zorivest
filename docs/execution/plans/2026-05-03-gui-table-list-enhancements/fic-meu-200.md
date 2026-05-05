# Feature Intent Contract: MEU-200 — Accounts Table Enhancements

> **MEU**: MEU-200 (`gui-accounts-table-enhance`)
> **Matrix Item**: 35m
> **Depends on**: MEU-199 (infrastructure primitives) ✅
> **Source**: [implementation-plan.md §MEU-200](implementation-plan.md), [proposal §MEU-200](gui-table-list-enhancements-proposal.md#L207-223)

## Current State

`AccountsHome.tsx` (445 LOC) has:
- Manual `useMemo` sort/filter (lines 238-273)
- Column sort with `handleColumnSort` callback (line 168)
- Type filter dropdown (line 322-334)
- Delete confirmation already wired in `AccountDetailPanel.tsx` via `useConfirmDelete` (line 78)
- No multi-select or bulk operations
- No text search filter

## Acceptance Criteria

### AC-1: Multi-select row checkboxes
- Each account row renders a `SelectionCheckbox` as the first column
- A header `SelectionCheckbox` toggles all visible (filtered) rows
- Selected rows receive a `selected` CSS highlight class from `table-enhancements.css`
- **Source**: `Spec` (proposal §2.2, §MEU-200 line 215)

### AC-2: Bulk action bar
- When ≥1 row is selected, `BulkActionBar` appears showing "{N} selected" count
- Bar contains a "Delete Selected" button
- Clicking "Delete Selected" triggers `ConfirmDeleteModal` in bulk mode with count
- On confirm, each selected account is deleted via individual `DELETE /api/v1/accounts/{id}` calls (D4: individual calls)
- After bulk delete completes, selection is cleared and accounts list is refetched
- **Source**: `Spec` (proposal §2.2, §MEU-200 line 216), `Human-approved` (D4)

### AC-3: Text search filter
- `TableFilterBar` renders above the table with a search input
- Typing filters accounts by name or institution (case-insensitive substring match)
- The existing type dropdown filter is preserved and integrated into `TableFilterBar`
- Filter state resets when the search input is cleared
- **Source**: `Spec` (proposal §2.3, §MEU-200 line 217)

### AC-4: Column sorting with sort indicators
- Replace manual sort arrows with `SortableColumnHeader` components
- Each sortable column header shows `▲`/`▼` indicators from the shared component
- Existing sort behavior (toggle direction, default direction per column type) is preserved
- Columns: Type, Name, Institution, Balance, Last Used, Portfolio %
- **Source**: `Spec` (proposal §2.3, §MEU-200 line 218)

### AC-5: Delete confirmation remains functional (existing)
- Single-account delete confirmation in `AccountDetailPanel` continues to work
- This is NOT new work — it was wired during the original GUI build
- Verify no regression from multi-select additions
- **Source**: `Local Canon` (existing implementation in `AccountDetailPanel.tsx:78,432-438`)

### AC-6: data-testid attributes
- All new interactive elements have `data-testid` attributes registered in `test-ids.ts`
- Required IDs: `select-all-checkbox`, `bulk-action-bar`, `bulk-delete-btn`, `table-filter-input`, `account-row-checkbox-{id}`
- **Source**: `Local Canon` ([06-gui.md §GUI Shipping Gate](../../build-plan/06-gui.md#gui-shipping-gate-mandatory-for-all-gui-meus))

### AC-7: No regression
- All 12 existing `AccountsHome.test.tsx` tests continue to pass
- `AccountDetailPanel.test.tsx` tests continue to pass
- No TypeScript compilation errors
- **Source**: `Local Canon` (AGENTS.md §TDD Protocol)

## Out of Scope

- TanStack Table migration (existing sort/filter logic is adequate; TanStack deferred to future iteration)
- Undo-toast pattern (D2: modal only)
- Batch DELETE API endpoint (D4: individual calls in loop)
- Archive via bulk action bar (only delete is in scope per proposal)

## Test Plan

Each AC maps to ≥1 Vitest assertion:

| AC | Test Description | Expected Result |
|----|-----------------|-----------------|
| AC-1 | Renders `SelectionCheckbox` in each row | checkbox rendered with `data-testid="account-row-checkbox-{id}"` |
| AC-1 | Header checkbox toggles all visible rows | all row checkboxes become checked |
| AC-2 | `BulkActionBar` appears when ≥1 row selected | bar visible with "{N} selected" text |
| AC-2 | "Delete Selected" click opens bulk confirm modal | modal renders with count |
| AC-3 | Search input filters by name | only matching accounts shown |
| AC-3 | Search input filters by institution | only matching accounts shown |
| AC-3 | Type dropdown filter preserved | filtered by type when selected |
| AC-4 | `SortableColumnHeader` renders sort indicators | `▲`/`▼` visible on active column |
| AC-6 | All required `data-testid` attributes present | `getByTestId` succeeds for each |
| AC-7 | Existing tests pass without modification | 12/12 pass |
