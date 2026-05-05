# Feature Intent Contract: MEU-203 — Scheduling Surface Enhancements (Policies + Templates)

> **MEU**: MEU-203 (`gui-scheduling-table-enhance`)
> **Matrix Item**: 35p
> **Depends on**: MEU-199 (infrastructure primitives) ✅
> **Source**: [implementation-plan.md §MEU-203](implementation-plan.md), [proposal §MEU-203](gui-table-list-enhancements-proposal.md)

## Current State

`PolicyList.tsx` (148 LOC) — sidebar list component:
- Sorted by name via `useMemo`
- No search/filter, no multi-select, no bulk delete
- Single-policy delete handled by `PolicyDetail.tsx` via `useConfirmDelete`

`EmailTemplateList.tsx` (103 LOC) — sidebar list component:
- No sort, no search/filter, no multi-select, no bulk delete
- Single-template delete handled by `EmailTemplateDetail.tsx` via `useConfirmDelete`

## Acceptance Criteria

### AC-1: Policy list — multi-select checkboxes
- Each policy item renders a `SelectionCheckbox`
- A header `SelectionCheckbox` toggles all visible (filtered) policies
- **Source**: `Spec` (proposal §2.2, §MEU-203)

### AC-2: Policy list — bulk delete
- When ≥1 policy selected, `BulkActionBar` appears with "Delete Selected"
- Clicking triggers `ConfirmDeleteModal` in bulk mode
- On confirm, each policy deleted via individual `DELETE` calls (D4)
- After bulk delete, selection cleared and list refetched
- **Source**: `Spec` (proposal §2.2, §MEU-203), `Human-approved` (D4)

### AC-3: Policy list — search filter
- Search input filters by policy name (case-insensitive substring)
- **Source**: `Spec` (proposal §2.3, §MEU-203)

### AC-4: Template list — multi-select checkboxes
- Each template item renders a `SelectionCheckbox`
- A header `SelectionCheckbox` toggles all visible templates
- **Source**: `Spec` (proposal §2.2, §MEU-203)

### AC-5: Template list — bulk delete
- When ≥1 template selected, `BulkActionBar` appears with "Delete Selected"
- Clicking triggers `ConfirmDeleteModal` in bulk mode
- On confirm, each template deleted via individual calls (D4)
- Default templates are skipped during bulk delete
- **Source**: `Spec` (proposal §2.2, §MEU-203), `Human-approved` (D4)

### AC-6: Template list — search filter
- Search input filters by template name (case-insensitive substring)
- **Source**: `Spec` (proposal §2.3, §MEU-203)

### AC-7: No regression
- All existing scheduling tests pass
- No TypeScript compilation errors
- **Source**: `Local Canon` (AGENTS.md §TDD Protocol)

## Out of Scope

- Full table migration (sidebar list pattern preserved, D3)
- Policy sort enhancements (already sorted by name)
- Template sort (deferred — simple list adequate)

## Test Plan

| AC | Test Description | Expected Result |
|----|-----------------|-----------------|
| AC-1 | PolicyList renders checkboxes per item | `data-testid="policy-row-checkbox-{id}"` present |
| AC-1 | Header checkbox toggles all | all checked after click |
| AC-2 | BulkActionBar visible when ≥1 selected | bar with count |
| AC-3 | Search filters by name | only matching policies shown |
| AC-4 | TemplateList renders checkboxes per item | `data-testid="template-row-checkbox-{name}"` |
| AC-5 | Bulk delete triggers confirm modal | modal with count |
| AC-6 | Search filters templates by name | only matching shown |
