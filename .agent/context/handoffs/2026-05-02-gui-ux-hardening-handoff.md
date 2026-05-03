# Handoff: GUI UX Hardening (Form Guard)
<!-- CACHE BOUNDARY -->

**Date**: 2026-05-02  
**MEUs**: MEU-196, MEU-197, MEU-198  
**Status**: Complete. All 32 tasks closed, E2E dirty-guard tests passing, MEU gates green, review approved.

## Summary

Implemented Universal Form Guard UX across all CRUD modules. Created shared `useFormGuard` hook and `UnsavedChangesModal` component, then wired 3-button "Save & Continue" modal and amber-pulse dirty-state feedback into all 6 feature areas.

## Changed Files

```diff
# New files
+ ui/src/renderer/src/hooks/useFormGuard.ts
+ ui/src/renderer/src/hooks/__tests__/useFormGuard.test.ts
+ ui/src/renderer/src/components/UnsavedChangesModal.tsx
+ ui/src/renderer/src/components/__tests__/UnsavedChangesModal.test.tsx
+ ui/src/renderer/src/styles/form-guard.css

# Modified files (guard wiring)
~ ui/src/renderer/src/features/accounts/AccountsHome.tsx (useFormGuard + childDirty)
~ ui/src/renderer/src/features/accounts/AccountDetailPanel.tsx (forwardRef + useImperativeHandle)
~ ui/src/renderer/src/features/trades/TradesLayout.tsx (useFormGuard + childDirty)
~ ui/src/renderer/src/features/trades/TradeDetailPanel.tsx (forwardRef + useImperativeHandle)
~ ui/src/renderer/src/features/planning/TradePlanPage.tsx (useFormGuard + isDirty + amber-pulse)
~ ui/src/renderer/src/features/planning/WatchlistPage.tsx (useFormGuard + isDirty + amber-pulse)
~ ui/src/renderer/src/features/settings/MarketDataProvidersPage.tsx (useFormGuard + "Disabled" label)
~ ui/src/renderer/src/features/scheduling/PolicyDetail.tsx (forwardRef + useImperativeHandle + amber-pulse)
~ ui/src/renderer/src/features/scheduling/EmailTemplateDetail.tsx (forwardRef + useImperativeHandle + amber-pulse)
~ ui/src/renderer/src/features/scheduling/SchedulingLayout.tsx (useFormGuard + UnsavedChangesModal + refs)
~ ui/tests/e2e/test-ids.ts (UNSAVED_CHANGES constants)
~ ui/src/renderer/src/features/settings/EmailSettingsPage.tsx (isDirty + amber-pulse)
~ .agent/context/meu-registry.md (MEU-196/197/198 → 🔄)
```

## Test Results

- **Vitest**: 31 files, 522 tests passed (20 G22/G23 guard tests + 3 G23 EmailSettingsPage dirty-state)
- **Playwright E2E**: 4/4 dirty-guard tests passed (scheduling, market-data, accounts, trade-plans)
- **MEU gate**: 8/8 blocking checks passed
- **TSC**: 0 errors
- **Anti-placeholder**: 0 matches

## Status

All 33 tasks complete. MEU-196/197/198 gates closed. Review verdict: `approved`.

## Architecture Decisions

1. **Child-owned vs Parent-owned forms**: Accounts/Trades use `onDirtyChange` callback (child lifts dirty state). TradePlans/Watchlists compute `isDirty` at parent level.
2. **Imperative save pattern**: `forwardRef` + `useImperativeHandle` exposes `save()` for parent-orchestrated "Save & Continue" flow.
3. **Scheduling refactored to shared modal**: Initially preserved inline modal (task 7 → 7a), later refactored to shared `useFormGuard<SchedulingNavTarget>` + `UnsavedChangesModal` during corrections (F2). ~90 lines of inline portal markup removed.
