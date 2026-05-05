# Feature Intent Contract: MEU-202 — Watchlist Tickers Table Enhancements

> **MEU**: MEU-202 (`gui-watchlist-table-enhance`)
> **Matrix Item**: 35o
> **Depends on**: MEU-199 (infrastructure primitives) ✅
> **Source**: [implementation-plan.md §MEU-202](implementation-plan.md), [proposal §MEU-202](gui-table-list-enhancements-proposal.md)

## Current State

`WatchlistTable.tsx` (330 LOC) — child component rendered by `WatchlistPage.tsx`:
- Manual sort with `handleSort` and `SortIndicator` (already functional)
- Row-level "✕" remove button with no confirmation
- No multi-select or bulk operations
- No text search filter (only sort)

`WatchlistPage.tsx` (499 LOC) — parent component:
- `handleRemoveTicker` calls `DELETE /api/v1/watchlists/{id}/items/{ticker}` directly (no confirmation)
- Single-watchlist delete confirmation already wired via `useConfirmDelete` (line 231)
- `ConfirmDeleteModal` already imported and rendered (line 8, 488)

## Acceptance Criteria

### AC-1: Multi-select row checkboxes
- Each ticker row renders a `SelectionCheckbox` as the first column
- A header `SelectionCheckbox` toggles all visible rows
- Selected rows receive a visual highlight
- **Source**: `Spec` (proposal §2.2, §MEU-202)

### AC-2: Bulk action bar
- When ≥1 ticker is selected, `BulkActionBar` appears showing "{N} selected" count
- Bar contains a "Remove Selected" button
- Clicking "Remove Selected" triggers `ConfirmDeleteModal` in bulk mode with count
- On confirm, each selected ticker is removed via individual `DELETE /api/v1/watchlists/{id}/items/{ticker}` calls (D4)
- After bulk remove completes, selection is cleared and watchlist is refetched
- **Source**: `Spec` (proposal §2.2, §MEU-202), `Human-approved` (D4)

### AC-3: Text search filter
- A search input renders above the watchlist table
- Typing filters tickers by ticker symbol or notes (case-insensitive substring match)
- Filter state resets when the search input is cleared
- **Source**: `Spec` (proposal §2.3, §MEU-202)

### AC-4: Single-ticker removal confirmation
- Wrap existing `handleRemoveTicker` with `ConfirmDeleteModal`
- User must confirm before any single ticker is removed
- **Source**: `Spec` (proposal §2.1)

### AC-5: data-testid attributes
- Required IDs: `select-all-ticker-checkbox`, `ticker-row-checkbox-{ticker}`, `bulk-action-bar`, `bulk-delete-btn`, `ticker-search-input`
- **Source**: `Local Canon` ([06-gui.md §GUI Shipping Gate](../../build-plan/06-gui.md#gui-shipping-gate-mandatory-for-all-gui-meus))

### AC-6: No regression
- All 88 existing `planning.test.tsx` tests continue to pass
- No TypeScript compilation errors
- **Source**: `Local Canon` (AGENTS.md §TDD Protocol)

## Out of Scope

- TanStack Table migration (existing sort is already manual and functional)
- Undo-toast pattern (D2: modal only)
- Batch DELETE API endpoint (D4: individual calls in loop)

## Test Plan

Each AC maps to ≥1 Vitest assertion:

| AC | Test Description | Expected Result |
|----|-----------------|-----------------|
| AC-1 | Renders `SelectionCheckbox` in each ticker row | checkbox with `data-testid="ticker-row-checkbox-{ticker}"` |
| AC-1 | Header checkbox toggles all tickers | all row checkboxes become checked |
| AC-2 | `BulkActionBar` appears when ≥1 ticker selected | bar visible with "{N} selected" text |
| AC-2 | "Remove Selected" click opens bulk confirm modal | modal renders with count |
| AC-3 | Search input filters by ticker | only matching tickers shown |
| AC-3 | Search input filters by notes | only matching tickers shown |
| AC-5 | All required `data-testid` attributes present | `getByTestId` succeeds for each |
| AC-6 | Existing 88 tests pass without modification | 88/88 pass |
