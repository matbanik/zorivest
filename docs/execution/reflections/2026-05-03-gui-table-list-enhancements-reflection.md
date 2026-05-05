# Reflection — GUI Table & List Enhancements

> **Project**: `2026-05-03-gui-table-list-enhancements`
> **Date**: 2026-05-03 → 2026-05-04

## Session Summary

This session completed the GUI Table & List Enhancements project spanning 5 MEUs (199–203) and 14 ad-hoc fixes/enhancements. The project added delete confirmation modals, multi-select with bulk delete, and filter/sort capabilities across all 5 interactive surfaces (Accounts, Trade Plans, Watchlists, Trades, Scheduling). Additionally implemented a tiered account deletion workflow with a `TradeWarningModal`, Tradier API hardening (Accept header + provider-specific validators + UI dirty-state fix), and a comprehensive MCP system audit verifying zero regressions across all 13 compound tools.

## Metrics

| Metric | Value |
|--------|-------|
| MEUs completed | 5 (MEU-199 through MEU-203) |
| Ad-hoc fixes | 14 (AH-1 through AH-14) |
| Frontend unit tests | 635 pass / 0 fail |
| Backend unit tests | 2768 pass / 0 fail |
| Pyright | 0 errors, 0 warnings |
| E2E tests | 37 pass / 13 fail (pre-existing) |
| MCP Audit | 68/70 pass (97.1%), 0 regressions |
| Files changed | ~30 source files |
| New components | 6 (ConfirmDeleteModal, BulkActionBar, SortableColumnHeader, SelectionCheckbox, TableFilterBar, TradeWarningModal) |
| New hooks | 2 (useConfirmDelete, useTableSelection) |
| New API endpoints | 1 (POST /accounts:trade-counts) |
| New service methods | 1 (AccountService.get_trade_counts) |
| Provider validators added | 2 (_validate_tradier, _validate_alpaca) |
| Type check | Clean |
| Build | ✓ 5.37s |

## Lessons Learned

1. **E2E selector fragility**: The `account-crud.test.ts` used `getByText('Confirm Delete')` which broke when the ConfirmDeleteModal component was introduced with different button text ("Delete"). Always prefer `data-testid` selectors over text-based selectors for E2E stability.

2. **Frontend validation prevents UX confusion**: The Trade Plan 422 error (AH-1) was caused by placeholder text being mistaken for actual input. Adding frontend validation with clear error messages is essential for forms with required fields.

3. **Prop wiring is the #1 integration failure mode**: The Scheduling bulk delete (AH-9) failed silently because `SchedulingLayout` never passed the `onDeletePolicies` and `onDeleteTemplates` callbacks to child components. TypeScript's optional props (`?:`) mask this — consider making critical callback props required.

4. **Test setup vs assertion distinction**: When new validation logic breaks existing tests, the fix is updating test **setup** (adding required fields), not test **assertions**. The `account_id` test needed `strategy_name` populated to pass the new validation gate.

5. **UoW session management**: Direct `service.uow.repos.method()` access from API routes bypasses session lifecycle management. Always delegate to a service method that wraps repo access in `with self.uow:` to ensure proper session enter/exit.

6. **Test mocks must track interface growth**: Adding `fetchTradeCounts` to `useAccounts.ts` required updating mock factories in 3 test files. Missing mocks cause silent test failures. Keep a checklist of mock sites when extending exported module interfaces.

7. **Provider-specific API response validation**: Generic validators fail when providers return different response structures (Tradier `{profile: {account: ...}}` vs Alpaca `{id: ..., status: ...}`). Always implement provider-specific validators and request correct `Content-Type` headers (`Accept: application/json`).

8. **UI dirty-state management**: Form fields populated with API keys/secrets must be cleared after successful save, or the form will remain in a "dirty" state. The save handler must reset both the API call state AND the form field state.

9. **MCP audit as regression detection**: Running a full MCP tool audit after infrastructure changes is an effective regression detection mechanism. The 68/70 pass rate confirmed that provider-specific validators and Accept header changes had zero side effects on other tools.

## Instruction Coverage

```yaml
schema: v1
session:
  id: e0a34551-f6a5-47fc-ad24-c8950f751f20
  task_class: tdd
  outcome: success
  tokens_in: 0
  tokens_out: 0
  turns: 12
sections:
  - id: testing_tdd_protocol
    cited: true
    influence: 3
  - id: execution_contract
    cited: true
    influence: 2
  - id: session_discipline
    cited: true
    influence: 2
  - id: operating_model
    cited: true
    influence: 1
loaded:
  workflows: [execution_session]
  roles: [coder, tester, reviewer]
  skills: [e2e_testing, terminal_preflight]
  refs: [docs/build-plan/06-gui.md]
decisive_rules:
  - "P1:tests-first-implementation-after"
  - "P0:never-modify-tests-to-pass (test setup ≠ test assertion)"
  - "P1:anti-premature-stop"
  - "P0:redirect-to-file-pattern"
  - "P1:mcp-audit-baseline-verification"
conflicts: []
note: "E2E tasks for 3 surfaces deferred — no pre-existing test files to extend. Tradier API hardening (AH-12/13) and MCP audit (AH-14) added as ad-hoc items. MCP baseline updated to v3."
```
