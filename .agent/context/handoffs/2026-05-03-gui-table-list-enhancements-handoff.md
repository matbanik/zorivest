# Handoff — GUI Table & List Enhancements

> **Project**: `2026-05-03-gui-table-list-enhancements`
> **MEUs**: MEU-199, MEU-200, MEU-201, MEU-202, MEU-203
> **Status**: Blocked — 3 E2E tasks pending (shipping gate requires Playwright proof)
> **Date**: 2026-05-03

<!-- CACHE BOUNDARY -->

## What Was Done

### Infrastructure Primitives (MEU-199)
- `ConfirmDeleteModal` — portal-based delete/archive confirmation with focus trap, Escape dismiss
- `BulkActionBar` — floating bar showing selected count with bulk delete/clear actions
- `SortableColumnHeader` — clickable column header with ascending/descending sort indicators
- `SelectionCheckbox` — individual row and "select all" checkbox primitives
- `useConfirmDelete` hook — manages modal state, targets, and confirmation flow
- `useTableSelection` hook — manages selection state with select-all toggle
- `TableFilterBar` — search input + dropdown filter for table surfaces
- `table-enhancements.css` — shared styles for all enhancement components

### Surface Integration (MEU-200–203)
All 5 surfaces enhanced with delete confirmation, multi-select, bulk delete, filter, and sort:
- **Accounts** (MEU-200): `AccountsHome.tsx`
- **Trade Plans** (MEU-201): `TradePlanPage.tsx`
- **Watchlists** (MEU-202): `WatchlistPage.tsx`
- **Scheduling** (MEU-203): `PolicyList.tsx`, `EmailTemplateList.tsx`, `SchedulingLayout.tsx`
- **Trades** (AH-8): `TradesTable.tsx`, `TradesLayout.tsx`

### Ad-Hoc Bug Fixes (AH-1 through AH-14)
14 defects/enhancements found and fixed during interactive testing, including Trade Plan 422 validation, Scheduling bulk delete wiring, clipboard paste in Electron, account archive UX, tiered account deletion with TDD tests, Tradier API hardening, and MCP system audit.

### Tradier API Hardening (AH-12 + AH-13)
- Added `Accept: application/json` header to Tradier's provider registry configuration (was returning XML)
- Implemented provider-specific response validators for Tradier (`profile` key) and Alpaca (`id` key)
- Fixed UI dirty-state reset in `MarketDataProvidersPage.tsx` after successful API key save
- TDD tests: `TestTradierAcceptHeader`, provider-specific validator tests, UI dirty-state tests

### MCP System Audit (AH-14)
- Full regression audit of 13 MCP compound tools / 74 actions
- **Result**: 68/70 pass (97.1%), zero regressions vs baseline v2
- Updated baseline snapshot to v3
- Report: `.agent/context/MCP/mcp-tool-audit-report.md`

## Quality Evidence

| Gate | Result |
|------|--------|
| Vitest | 635 pass / 0 fail |
| pytest | 2768 pass / 0 fail |
| pyright | 0 errors, 0 warnings |
| tsc --noEmit | Clean |
| Production build | ✓ 5.37s |
| Anti-placeholder | 0 matches |
| E2E | 37 pass / 13 fail (all 13 pre-existing) |
| MCP Audit | 68/70 pass, 0 regressions |

### E2E Selector Fix
Updated `account-crud.test.ts` to use `testId(CONFIRM_DELETE.CONFIRM_BTN)` instead of `getByText('Confirm Delete')` — now all 5 account-crud E2E tests pass.

### FAIL_TO_PASS Evidence

All evidence produced retroactively using the break→capture→restore technique: temporarily stub the component under test to return null (or throw), run tests to capture failures, restore original, confirm green.

#### MEU-199: ConfirmDeleteModal + useConfirmDelete (22 tests)

**ConfirmDeleteModal** (`ConfirmDeleteModal.test.tsx` — 15 tests):
```
# RED: Component stubbed to return null
FAIL ConfirmDeleteModal > clicking backdrop calls onCancel
  Unable to find element with testId: confirm-delete-backdrop
  <body><div /></body>
======================== 14 failed | 1 passed (open=false) in 815ms ===

# GREEN: Component restored
15 passed in 856ms
```

**useConfirmDelete** (`useConfirmDelete.test.ts` — 7 tests):
```
# RED: Hook replaced with throw Error("not yet implemented")
FAIL useConfirmDelete > confirmSingle opens modal with target
  Error: useConfirmDelete not yet implemented
======================== 7 failed in 788ms ===

# GREEN: Hook restored
7 passed in 764ms
```

#### MEU-200–203: Table Enhancement Tests (41 tests)

Red-phase produced by stubbing shared `BulkActionBar` component to `return null`:

```
# RED: BulkActionBar stubbed to return null
AccountsHome.enhance.test.tsx   — 3 failed | 8 passed (11)
TradePlanPage.enhance.test.tsx  — 3 failed | 7 passed (10)
WatchlistTable.enhance.test.tsx — 3 failed | 7 passed (10)
scheduling.enhance.test.tsx     — 2 failed | 8 passed (10)
======================== 11 failed | 30 passed (41) in 4.92s ===

Failing tests: AC-2 bulk action bar visibility/interaction tests across all surfaces
Error: Unable to find element with testId: bulk-action-bar
  <body><div /></body>

# GREEN: BulkActionBar restored
41 passed in 1.90s
```

#### AH-11: Tiered Deletion TDD (33 tests)

**Service layer** (`test_service_trade_counts.py` — 6 tests):
```
# RED: get_trade_counts() replaced with NotImplementedError
FAILED test_single_account_with_trades
  NotImplementedError: get_trade_counts not yet implemented
======================== 1 failed (stopped at first) in 0.36s ===

# GREEN: Implementation restored
6 passed in 0.26s
```

**API layer** (`test_api_trade_counts.py` — 8 tests):
```
# RED: Endpoint replaced with HTTPException(501)
FAILED test_returns_200_with_counts
  assert 501 == 200 (Response [501 Not Implemented])
======================== 1 failed (stopped at first) in 0.98s ===

# GREEN: Endpoint restored
8 passed in 1.23s
```

**Frontend component** (`TradeWarningModal.test.tsx` — 19 tests):
```
# RED: Component stubbed to return null
FAIL TradeWarningModal > shows singular "trade" for count of 1
  Unable to find element with text: /1 trade /i
======================== 18 failed | 1 passed (open=false) in 786ms ===

# GREEN: Component restored
19 passed in 852ms
```

## Blocked Items

| Task | Reason | Follow-up |
|------|--------|-----------|
| #21 Trade Plans E2E | No pre-existing E2E test file for planning delete flows | Create `planning-crud.test.ts` in a future E2E wave |
| #27 Watchlist E2E | No pre-existing E2E test file for watchlist flows | Create `watchlist-crud.test.ts` in a future E2E wave |
| #34 Scheduling E2E | No delete E2E in existing `scheduling.test.ts` | Extend `scheduling.test.ts` with delete confirm scenario |

## Pre-Existing E2E Failures (not from this project)

13 failures unrelated to table/list enhancements:
- `backup-restore` (2): Passphrase fill timeout
- `import` (2): setInputFiles timeout + axe-core protocol error
- `launch` (1): axe-core `browserContext.newPage` protocol error
- `mode-gating` (1): `toBeDisabled` timeout
- `position-size dirty-guard` (1): `plan-ticker` testid resolves to `<div>` not `<input>`
- `scheduling-tz` (2): Timezone assertion + strict mode violation on 12 policy items
- `settings-market-data` (1): Provider count 14 vs expected
- `trade-entry` (2): axe-core + visual regression screenshot diff

## Changed Files

```diff
# Infrastructure (MEU-199)
+ ui/src/renderer/src/components/ConfirmDeleteModal.tsx
+ ui/src/renderer/src/components/BulkActionBar.tsx
+ ui/src/renderer/src/components/SortableColumnHeader.tsx
+ ui/src/renderer/src/components/SelectionCheckbox.tsx
+ ui/src/renderer/src/components/TableFilterBar.tsx
+ ui/src/renderer/src/hooks/useConfirmDelete.ts
+ ui/src/renderer/src/hooks/useTableSelection.ts
+ ui/src/renderer/src/styles/table-enhancements.css

# Surface integrations (MEU-200–203 + AH)
~ ui/src/renderer/src/features/accounts/AccountsHome.tsx
~ ui/src/renderer/src/features/planning/TradePlanPage.tsx
~ ui/src/renderer/src/features/planning/WatchlistPage.tsx
~ ui/src/renderer/src/features/scheduling/SchedulingLayout.tsx
~ ui/src/renderer/src/features/scheduling/PolicyList.tsx
~ ui/src/renderer/src/features/scheduling/EmailTemplateList.tsx
~ ui/src/renderer/src/features/trades/TradesTable.tsx
~ ui/src/renderer/src/features/trades/TradesLayout.tsx
~ ui/src/renderer/src/features/trades/ScreenshotPanel.tsx

# AH-10: Tiered account deletion
+ ui/src/renderer/src/components/TradeWarningModal.tsx
~ ui/src/renderer/src/hooks/useAccounts.ts
~ ui/src/renderer/src/features/accounts/AccountDetailPanel.tsx
~ packages/core/src/zorivest_core/services/account_service.py
~ packages/api/src/zorivest_api/routes/accounts.py

# AH-11: TDD tests for tiered deletion
+ tests/unit/test_service_trade_counts.py
+ tests/unit/test_api_trade_counts.py
+ ui/src/renderer/src/components/__tests__/TradeWarningModal.test.tsx
~ ui/src/renderer/src/features/accounts/__tests__/AccountsHome.test.tsx
~ ui/src/renderer/src/features/accounts/__tests__/AccountsHome.enhance.test.tsx
~ ui/src/renderer/src/features/accounts/__tests__/AccountDetailPanel.test.tsx

# E2E & docs
~ ui/tests/e2e/account-crud.test.ts
~ ui/tests/e2e/test-ids.ts
~ docs/build-plan/06-gui.md

# AH-12: Tradier API hardening
~ packages/infrastructure/src/zorivest_infra/market_data/provider_registry.py
~ packages/core/src/zorivest_core/services/provider_connection_service.py
~ ui/src/renderer/src/features/settings/MarketDataProvidersPage.tsx

# AH-13: TDD tests for Tradier hardening
~ tests/unit/test_provider_registry.py
~ tests/unit/test_provider_connection_service.py
~ ui/src/renderer/src/features/settings/__tests__/MarketDataProvidersPage.test.tsx

# AH-14: MCP system audit
+ .agent/context/MCP/mcp-tool-audit-report.md
~ .agent/skills/mcp-audit/resources/baseline-snapshot.json
```

## Pomera Session
Note ID: 1060 — `Memory/Session/Zorivest-gui-table-enhancements-2026-05-03`
