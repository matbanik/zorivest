# Task Handoff

## Task

- **Date:** 2026-03-24
- **Task slug:** 2026-03-20-gui-plans-reports-multiaccnt-implementation-critical-review
- **Owner role:** reviewer
- **Scope:** implementation-review pass for `docs/execution/plans/2026-03-20-gui-plans-reports-multiaccnt/`, correlated handoffs `087`, `088`, `089`, live UI/API file state, and shared closeout artifacts

## Inputs

- User request:
  - Review `.agent/workflows/critical-review-feedback.md` against:
    - `.agent/context/handoffs/087-2026-03-20-multi-account-ui-bp06bs19.md`
    - `.agent/context/handoffs/088-2026-03-20-report-gui-bp06bs20.md`
    - `.agent/context/handoffs/089-2026-03-20-gui-plans-bp06cs16.md`
- Specs/docs referenced:
  - `AGENTS.md`
  - `.agent/docs/emerging-standards.md`
  - `docs/execution/plans/2026-03-20-gui-plans-reports-multiaccnt/implementation-plan.md`
  - `docs/execution/plans/2026-03-20-gui-plans-reports-multiaccnt/task.md`
  - `docs/build-plan/06b-gui-trades.md`
  - `packages/api/src/zorivest_api/routes/accounts.py`
  - `packages/api/src/zorivest_api/routes/plans.py`
  - `packages/core/src/zorivest_core/services/report_service.py`
- Constraints:
  - Review-only workflow; no product fixes
  - File state, not handoff prose, is source of truth
  - Current repo is dirty and has later follow-on changes, so direct file-state checks were used alongside test reruns

## Role Plan

1. orchestrator
2. tester
3. reviewer
- Optional roles: researcher, guardrail

## Coder Output

- Changed files:
  - No product changes; review-only
- Design notes / ADRs referenced:
  - N/A
- Commands run:
  - N/A
- Results:
  - N/A

## Tester Output

- Commands run:
  - `Get-Content SOUL.md`
  - `Get-Content .agent/context/current-focus.md`
  - `Get-Content .agent/context/known-issues.md`
  - `Get-Content .agent/docs/emerging-standards.md`
  - `Get-Content .agent/workflows/critical-review-feedback.md`
  - `Get-Content docs/execution/plans/2026-03-20-gui-plans-reports-multiaccnt/implementation-plan.md`
  - `Get-Content docs/execution/plans/2026-03-20-gui-plans-reports-multiaccnt/task.md`
  - `Get-Content .agent/context/handoffs/087-2026-03-20-multi-account-ui-bp06bs19.md`
  - `Get-Content .agent/context/handoffs/088-2026-03-20-report-gui-bp06bs20.md`
  - `Get-Content .agent/context/handoffs/089-2026-03-20-gui-plans-bp06cs16.md`
  - `git status --short -- docs/execution/plans/2026-03-20-gui-plans-reports-multiaccnt .agent/context/handoffs ui packages/api docs .agent/context`
  - `git diff -- docs/execution/plans/2026-03-20-gui-plans-reports-multiaccnt ...`
  - `rg -n "account dropdown|followed_plan|linked_plan_id|emotional_state|IRA|Paper|Margin|Cash|401k|custom|broker|account type|badge" docs/build-plan/06b-gui-trades.md docs/build-plan/06c-gui-planning.md docs/build-plan/06h-gui-calculator.md packages/core/src/zorivest_core/domain/entities.py packages/core/src/zorivest_core/domain/enums.py`
  - `rg -n "refetchInterval|useQuery<.*accounts|queryKey: \\['accounts'\\]|queryKey: \\['trades-for-link'\\]|mcp-guard-status|trade-picker" ui/src/renderer/src/features/planning/TradePlanPage.tsx ui/src/renderer/src/features/trades/TradesLayout.tsx`
  - `rg -n "PUT|status bar|Journal saved|Updating journal|save PUT|existing report|trade-report-save|setStatus" ui/src/renderer/src/features/trades/__tests__/trades.test.tsx`
  - `rg -n "trade picker|plan-trade-picker|trade-picker-search|executed|copy-to-clipboard|watchlist-price|plan-account-select|executed_at|cancelled_at|refetchInterval|status bar|useStatusBar" ui/src/renderer/src/features/planning/__tests__/planning.test.tsx`
  - `npx vitest run src/renderer/src/features/trades/__tests__/trades.test.tsx`
  - `npx vitest run src/renderer/src/features/planning/__tests__/planning.test.tsx`
  - `uv run pytest tests/unit/test_api_plans.py`
  - `npx playwright test tests/e2e/position-size.test.ts`
- Pass/fail matrix:
  - `trades.test.tsx`: PASS, 50/50
  - `planning.test.tsx`: PASS, 45/45
  - `tests/unit/test_api_plans.py`: PASS, 18/18
  - `position-size.test.ts`: FAIL locally, Electron process failed to launch in current environment
- Repro failures:
  - `npx playwright test tests/e2e/position-size.test.ts` failed with `Process failed to launch!` for both tests in this review environment, so the claimed prior PASS could not be re-verified locally
- Coverage/test gaps:
  - MEU-54 tests do not verify `/api/v1/accounts` is called, do not verify trade refetch with `account_id`, and do not verify badge color classes
  - MEU-55 tests do not currently verify `PUT` update path or `useStatusBar` feedback despite handoff claims
  - MEU-48/T5 tests do not verify `executed_at` persistence on the `PATCH .../status` + `linked_trade_id` path
  - MEU-48/T3 tests encode the wrong accounts API shape (`id` instead of `account_id`)
- Evidence bundle location:
  - This handoff
- FAIL_TO_PASS / PASS_TO_PASS result:
  - Review-only; reran claimed green suites
- Mutation score:
  - Not run
- Contract verification status:
  - Failed for MEU-54 account filter contract
  - Failed for MEU-48 T3 account dropdown API contract
  - Failed for MEU-48 T5 executed timestamp persistence contract
  - Overstated for MEU-48 Wave 4 accessibility gate

### IR-5 Test Rigor Audit

| File | Test | Rating | Notes |
|---|---|---|---|
| `ui/src/renderer/src/features/trades/__tests__/trades.test.tsx` | `AC-1: should fetch existing report on mount via GET` | 🟢 Strong | Verifies actual endpoint call |
| `ui/src/renderer/src/features/trades/__tests__/trades.test.tsx` | `AC-2: should initialize with empty defaults on 404` | 🟢 Strong | Verifies concrete empty field state |
| `ui/src/renderer/src/features/trades/__tests__/trades.test.tsx` | `AC-3: save button should call POST for new report` | 🟡 Adequate | Verifies method only, not payload shape or status-bar feedback |
| `ui/src/renderer/src/features/trades/__tests__/trades.test.tsx` | `AC-4a: should convert star ratings to letter grades in payload` | 🟢 Strong | Captures payload and asserts transformed value |
| `ui/src/renderer/src/features/trades/__tests__/trades.test.tsx` | `AC-4b: should send followed_plan as boolean` | 🟢 Strong | Captures payload and asserts boolean |
| `ui/src/renderer/src/features/trades/__tests__/trades.test.tsx` | `AC-4c: should send emotional_state as string` | 🔴 Weak | Only checks `typeof === "string"`; would pass for wrong values/options |
| `ui/src/renderer/src/features/trades/__tests__/trades.test.tsx` | `AccountTypeBadge` label tests | 🟡 Adequate | Checks labels/case-insensitivity but not claimed color classes |
| `ui/src/renderer/src/features/trades/__tests__/trades.test.tsx` | `should populate dropdown with unique account IDs from trades` | 🟢 Strong | Strong assertion, but it proves the wrong behavior relative to the handoff contract |
| `ui/src/renderer/src/features/trades/__tests__/trades.test.tsx` | `should update filter value when account is selected` | 🔴 Weak | Only checks local select state; does not prove re-query or `account_id` propagation |
| `ui/src/renderer/src/features/planning/__tests__/planning.test.tsx` | `should change status via PATCH (AC-5a)` | 🟡 Adequate | Verifies route/method but not request body semantics or timestamps |
| `ui/src/renderer/src/features/planning/__tests__/planning.test.tsx` | `should populate account dropdown with fetched accounts` | 🔴 Weak | Only checks option count and uses wrong mock shape (`id`) |
| `ui/src/renderer/src/features/planning/__tests__/planning.test.tsx` | `should set account_id when account is selected` | 🟡 Adequate | Captures payload, but still built on wrong API fixture shape |
| `ui/src/renderer/src/features/planning/__tests__/planning.test.tsx` | `should show executed_at timestamp for executed plans` | 🟡 Adequate | Checks presence only, not persisted round-trip or rendered value |
| `ui/src/renderer/src/features/planning/__tests__/planning.test.tsx` | `AC-T4-DATE-1: date label format is MM-DD-YYYY` | 🟢 Strong | Verifies exact visible format and rejects old locale format |
| `ui/src/renderer/src/features/planning/__tests__/planning.test.tsx` | `AC-T4-SELECT-1: clicking a trade option shows the selected label` | 🟢 Strong | Verifies label-in-input behavior and list collapse |
| `ui/tests/e2e/position-size.test.ts` | `calculator produces correct position size` | 🟢 Strong | Verifies concrete numeric output |
| `ui/tests/e2e/position-size.test.ts` | `calculator modal has no accessibility violations` | 🔴 Weak | Runs `axe` on the whole document, not the modal it claims to gate |
| `tests/unit/test_api_plans.py` | `test_patch_status_executed_with_link` | 🟡 Adequate | Verifies route choice, but not `executed_at` persistence |
| `tests/unit/test_api_plans.py` | `test_create_and_get_plan_real_wiring` | 🟢 Strong | Real wiring round-trip with concrete values |

## Reviewer Output

- Findings by severity:
  - **High** — MEU-54’s core account-filter contract was not implemented as claimed. The handoff, task, and implementation plan all say the dropdown fetches `/api/v1/accounts` and renders one option per account ([087-2026-03-20-multi-account-ui-bp06bs19.md](/p:/zorivest/.agent/context/handoffs/087-2026-03-20-multi-account-ui-bp06bs19.md#L18), [087-2026-03-20-multi-account-ui-bp06bs19.md](/p:/zorivest/.agent/context/handoffs/087-2026-03-20-multi-account-ui-bp06bs19.md#L30), [implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-03-20-gui-plans-reports-multiaccnt/implementation-plan.md#L22), [implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-03-20-gui-plans-reports-multiaccnt/implementation-plan.md#L45), [implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-03-20-gui-plans-reports-multiaccnt/implementation-plan.md#L97), [task.md](/p:/zorivest/docs/execution/plans/2026-03-20-gui-plans-reports-multiaccnt/task.md#L8)). The live component never queries `/api/v1/accounts`; it derives options from whatever accounts happen to appear in the currently loaded trades ([TradesLayout.tsx](/p:/zorivest/ui/src/renderer/src/features/trades/TradesLayout.tsx#L52), [TradesLayout.tsx](/p:/zorivest/ui/src/renderer/src/features/trades/TradesLayout.tsx#L68), [TradesLayout.tsx](/p:/zorivest/ui/src/renderer/src/features/trades/TradesLayout.tsx#L211)). The MEU-54 tests also codify the wrong behavior by asserting “unique account IDs from trades” and only checking the select value, not a re-fetch with `account_id` ([trades.test.tsx](/p:/zorivest/ui/src/renderer/src/features/trades/__tests__/trades.test.tsx#L615), [trades.test.tsx](/p:/zorivest/ui/src/renderer/src/features/trades/__tests__/trades.test.tsx#L624)). This is both a product-contract miss and a false-positive evidence bundle.
  - **High** — The T5 timestamp work has a real persistence bug on the `PATCH /trade-plans/{id}/status` + `linked_trade_id` path. The handoff claims `executed_at`/`cancelled_at` fields were added and auto-set on status transition ([089-2026-03-20-gui-plans-bp06cs16.md](/p:/zorivest/.agent/context/handoffs/089-2026-03-20-gui-plans-bp06cs16.md#L93)). In the live route, `patch_plan_status()` computes `update_data["executed_at"]`, but when `linked_trade_id` is present it calls `service.link_plan_to_trade()` instead of persisting `update_data`; it then mutates the returned entity in memory only for the response ([plans.py](/p:/zorivest/packages/api/src/zorivest_api/routes/plans.py#L195), [plans.py](/p:/zorivest/packages/api/src/zorivest_api/routes/plans.py#L202), [plans.py](/p:/zorivest/packages/api/src/zorivest_api/routes/plans.py#L208)). The service method itself updates only `linked_trade_id`, `status`, and `updated_at` and never sets `executed_at` ([report_service.py](/p:/zorivest/packages/core/src/zorivest_core/services/report_service.py#L198), [report_service.py](/p:/zorivest/packages/core/src/zorivest_core/services/report_service.py#L219)). The current tests missed this path entirely; the route test asserts status/linking only and never verifies timestamp persistence ([test_api_plans.py](/p:/zorivest/tests/unit/test_api_plans.py#L241)). A GET after link can therefore lose the claimed `executed_at`.
  - **High** — The MEU-48/T3 account dropdown is wired against a non-existent API field and is therefore broken with real account responses. `TradePlanPage` defines `Account` as `{ id, name, account_type }` and renders `<option value={acct.id}>` ([TradePlanPage.tsx](/p:/zorivest/ui/src/renderer/src/features/planning/TradePlanPage.tsx#L33), [TradePlanPage.tsx](/p:/zorivest/ui/src/renderer/src/features/planning/TradePlanPage.tsx#L645)). But the actual accounts API returns `account_id`, not `id` ([accounts.py](/p:/zorivest/packages/api/src/zorivest_api/routes/accounts.py#L43), [accounts.py](/p:/zorivest/packages/api/src/zorivest_api/routes/accounts.py#L78)). That means real dropdown options render with `undefined` values and cannot reliably submit the selected account. The tests encode the same wrong fixture shape (`{ id: 'acc-1', ... }`), so they mask the break instead of catching it ([planning.test.tsx](/p:/zorivest/ui/src/renderer/src/features/planning/__tests__/planning.test.tsx#L531), [planning.test.tsx](/p:/zorivest/ui/src/renderer/src/features/planning/__tests__/planning.test.tsx#L564)).
  - **Medium** — The Wave 4 accessibility “gate” does not prove what the handoff claims it proves. The handoff states the calculator modal has no WCAG 2.1 AA violations and treats that as the Wave 4 gate ([089-2026-03-20-gui-plans-bp06cs16.md](/p:/zorivest/.agent/context/handoffs/089-2026-03-20-gui-plans-bp06cs16.md#L37), [089-2026-03-20-gui-plans-bp06cs16.md](/p:/zorivest/.agent/context/handoffs/089-2026-03-20-gui-plans-bp06cs16.md#L103)). But the actual Playwright test calls `window.axe.run()` with no modal scoping, so it audits the whole page ([position-size.test.ts](/p:/zorivest/ui/tests/e2e/position-size.test.ts#L74)). The reflection explicitly acknowledges this and says the scan “runs on the full page (not scoped to modal)” and should be scoped to the modal root later ([2026-03-24-gui-plans-reports-multiaccnt-reflection.md](/p:/zorivest/docs/execution/reflections/2026-03-24-gui-plans-reports-multiaccnt-reflection.md#L29), [2026-03-24-gui-plans-reports-multiaccnt-reflection.md](/p:/zorivest/docs/execution/reflections/2026-03-24-gui-plans-reports-multiaccnt-reflection.md#L49)). This is an overstated gate, not a modal-specific accessibility proof.
  - **Medium** — The shared project artifacts are internally inconsistent, which breaks auditability of the closeout bundle. The task file records the actual handoffs `087/088/089` and marks all post-MEU deliverables done ([task.md](/p:/zorivest/docs/execution/plans/2026-03-20-gui-plans-reports-multiaccnt/task.md#L11), [task.md](/p:/zorivest/docs/execution/plans/2026-03-20-gui-plans-reports-multiaccnt/task.md#L24), [task.md](/p:/zorivest/docs/execution/plans/2026-03-20-gui-plans-reports-multiaccnt/task.md#L45), [task.md](/p:/zorivest/docs/execution/plans/2026-03-20-gui-plans-reports-multiaccnt/task.md#L79)). The implementation plan still lists `082/083/084`, leaves the handoff/BUILD_PLAN/registry/reflection/metrics rows unchecked, and still cites the pre-expansion `180 tests` total ([implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-03-20-gui-plans-reports-multiaccnt/implementation-plan.md#L285), [implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-03-20-gui-plans-reports-multiaccnt/implementation-plan.md#L286), [implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-03-20-gui-plans-reports-multiaccnt/implementation-plan.md#L291), [implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-03-20-gui-plans-reports-multiaccnt/implementation-plan.md#L332), [implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-03-20-gui-plans-reports-multiaccnt/implementation-plan.md#L338)). The review target therefore cannot be treated as a coherent evidence bundle.
  - **Medium** — Several handoff-specific test claims are stale or overstated relative to the current suites. MEU-54 claims tests for “re-queries on filter change” and badge-color ACs ([087-2026-03-20-multi-account-ui-bp06bs19.md](/p:/zorivest/.agent/context/handoffs/087-2026-03-20-multi-account-ui-bp06bs19.md#L41), [087-2026-03-20-multi-account-ui-bp06bs19.md](/p:/zorivest/.agent/context/handoffs/087-2026-03-20-multi-account-ui-bp06bs19.md#L60)), but the live tests only check labels, option count, and local select value ([trades.test.tsx](/p:/zorivest/ui/src/renderer/src/features/trades/__tests__/trades.test.tsx#L533), [trades.test.tsx](/p:/zorivest/ui/src/renderer/src/features/trades/__tests__/trades.test.tsx#L624)). MEU-55 claims tests for the `PUT` existing-report path and status-bar feedback ([088-2026-03-20-report-gui-bp06bs20.md](/p:/zorivest/.agent/context/handoffs/088-2026-03-20-report-gui-bp06bs20.md#L47), [088-2026-03-20-report-gui-bp06bs20.md](/p:/zorivest/.agent/context/handoffs/088-2026-03-20-report-gui-bp06bs20.md#L63)), but the current suite contains no `PUT` assertion and no `setStatus` expectation ([trades.test.tsx](/p:/zorivest/ui/src/renderer/src/features/trades/__tests__/trades.test.tsx#L344), [trades.test.tsx](/p:/zorivest/ui/src/renderer/src/features/trades/__tests__/trades.test.tsx#L418)). This is not just wording drift; it weakens the claimed evidence for the delivered behaviors.
- Open questions:
  - None. The code and artifact state are sufficient to require corrections.
- Verdict:
  - `changes_required`
- Residual risk:
  - The project has real UI/API contract breaks in expansion paths (`/accounts` handling, status timestamp persistence) and its strongest end-to-end accessibility claim is currently broader and weaker than advertised.
- Anti-deferral scan result:
  - No product edits were made during review.
  - Findings require a correction pass; at least two are behavior bugs, not documentation-only cleanups.

## Guardrail Output (If Required)

- Safety checks:
  - Not required for this docs/code review scope
- Blocking risks:
  - N/A
- Verdict:
  - N/A

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status:
  - Review completed; implementation handoff set is not approvable in current state
- Next steps:
  - Route fixes through `/planning-corrections`
  - Correct MEU-54 `/accounts` contract and test coverage
  - Fix `PATCH /trade-plans/{id}/status` timestamp persistence and add route-level regression coverage
  - Fix TradePlan account dropdown to use `account_id` and rewrite the test fixture to match the real API
  - Tighten or re-scope the Wave 4 accessibility test so the claim matches the evidence

---

## Corrections Applied — 2026-03-24

**Verdict:** `corrections_applied` ✅

All 5 findings resolved via `/planning-corrections`. Verified clean.

### F1 (High) — MEU-54: GET /api/v1/accounts wired
- `TradesLayout.tsx`: added `useQuery<AccountSummary[]>` for `/api/v1/accounts`; trade-derived accumulation kept as fallback
- `trades.test.tsx`: MEU-54 `beforeEach` now mocks `/api/v1/accounts`; added AC-3 and AC-4 contract tests replacing stale "from trades" tests

### F2 (High) — T5: executed_at persisted in link_plan_to_trade
- `report_service.py:16`: added `timezone` to datetime import
- `report_service.py:219-225`: `replace()` now includes `executed_at=datetime.now(timezone.utc)`
- `plans.py:202-206`: removed stale in-memory mutation block
- `test_api_plans.py`: added `test_patch_status_executed_with_link_sets_executed_at` regression test

### F3 (High) — T3: Account interface field corrected
- `TradePlanPage.tsx:35`: `id: string` → `account_id: string`
- `TradePlanPage.tsx:646`: `acct.id` → `acct.account_id` in option key + value
- `planning.test.tsx:533-535`: fixture uses `account_id: 'acc-1'`

### F4 (Medium) — Wave 4 axe scan scoped to modal
- `position-size.test.ts:80-86`: `axe.run()` now receives `document.querySelector('[data-testid="calculator-modal"]') ?? document` as context

### F5 (Medium) — implementation-plan.md stale references
- Test counts: 180 → 207; handoffs: 082/083/084 → 087/088/089; 6 previously unchecked rows marked `[x]`

### Verification

| Command | Result |
|---------|--------|
| `npx vitest run` | ✅ 15 files, 214 tests, 0 failed |
| `npx tsc --noEmit` | ✅ Exit 0 |
| `uv run pytest tests/unit/test_api_plans.py -x -q` | ✅ 19 passed |

---

## Recheck Update — 2026-03-24 (Functionality + TDD Focus)

This pass intentionally deprioritized documentation drift and rechecked the current code for runtime behavior, UI/API contract validity, and whether the existing tests would actually fail on the broken paths.

### Commands rerun

- `npx vitest run src/renderer/src/features/planning/__tests__/planning.test.tsx` → PASS (45/45)
- `npx vitest run src/renderer/src/features/trades/__tests__/trades.test.tsx` → PASS (51/51)
- `uv run pytest tests/unit/test_api_plans.py` → PASS (19/19)

### Findings

- **High** — Trade linking in the plan UI is still not persisted. Selecting a trade in the picker only updates local component state via `setLinkedTradeId(...)` and `updateField('linked_trade_id', ...)` ([TradePlanPage.tsx](/p:/zorivest/ui/src/renderer/src/features/planning/TradePlanPage.tsx#L784), [TradePlanPage.tsx](/p:/zorivest/ui/src/renderer/src/features/planning/TradePlanPage.tsx#L788)), but neither persistence path sends that value. `handleSave()` omits both `linked_trade_id` and `status` from the `PUT` payload ([TradePlanPage.tsx](/p:/zorivest/ui/src/renderer/src/features/planning/TradePlanPage.tsx#L231), [TradePlanPage.tsx](/p:/zorivest/ui/src/renderer/src/features/planning/TradePlanPage.tsx#L257)), and the status PATCH sends only `{ status }` ([TradePlanPage.tsx](/p:/zorivest/ui/src/renderer/src/features/planning/TradePlanPage.tsx#L275), [TradePlanPage.tsx](/p:/zorivest/ui/src/renderer/src/features/planning/TradePlanPage.tsx#L278)). The backend already supports persisted linking via `linked_trade_id` on `PUT`/`PATCH` ([plans.py](/p:/zorivest/packages/api/src/zorivest_api/routes/plans.py#L165), [plans.py](/p:/zorivest/packages/api/src/zorivest_api/routes/plans.py#L202)), so the current UI exposes a link workflow that never reaches the server.

- **High** — The trade picker queries an unsupported backend contract, and the tests do not catch it. `TradePlanPage` fetches linkable trades with `/api/v1/trades?ticker=...&limit=50` ([TradePlanPage.tsx](/p:/zorivest/ui/src/renderer/src/features/planning/TradePlanPage.tsx#L170), [TradePlanPage.tsx](/p:/zorivest/ui/src/renderer/src/features/planning/TradePlanPage.tsx#L174)), but the actual trades route only accepts `limit`, `offset`, `account_id`, `search`, and `sort` ([trades.py](/p:/zorivest/packages/api/src/zorivest_api/routes/trades.py#L101), [trades.py](/p:/zorivest/packages/api/src/zorivest_api/routes/trades.py#L106)). The planning tests stub any `/api/v1/trades` request and only assert that an option renders, so they stay green even if the request shape is invalid ([planning.test.tsx](/p:/zorivest/ui/src/renderer/src/features/planning/__tests__/planning.test.tsx#L769), [planning.test.tsx](/p:/zorivest/ui/src/renderer/src/features/planning/__tests__/planning.test.tsx#L772), [planning.test.tsx](/p:/zorivest/ui/src/renderer/src/features/planning/__tests__/planning.test.tsx#L798)).

- **Medium** — Status transitions can leave the UI in a false state on PATCH failure. Clicking a segmented status button mutates local form state before the request runs ([TradePlanPage.tsx](/p:/zorivest/ui/src/renderer/src/features/planning/TradePlanPage.tsx#L695), [TradePlanPage.tsx](/p:/zorivest/ui/src/renderer/src/features/planning/TradePlanPage.tsx#L697)), and the error path only sets a status-bar message with no rollback or refetch ([TradePlanPage.tsx](/p:/zorivest/ui/src/renderer/src/features/planning/TradePlanPage.tsx#L272), [TradePlanPage.tsx](/p:/zorivest/ui/src/renderer/src/features/planning/TradePlanPage.tsx#L283)). Because `isExecutedStatus` is derived from `form.status` ([TradePlanPage.tsx](/p:/zorivest/ui/src/renderer/src/features/planning/TradePlanPage.tsx#L168)), a failed click to `executed` can still unlock the trade-link UI locally. The current test only checks that a PATCH call was made; it never simulates rejection or verifies rollback ([planning.test.tsx](/p:/zorivest/ui/src/renderer/src/features/planning/__tests__/planning.test.tsx#L234), [planning.test.tsx](/p:/zorivest/ui/src/renderer/src/features/planning/__tests__/planning.test.tsx#L251)).

- **Medium** — `TradeReportForm` still collapses all GET failures into the “no report yet” path, which can turn backend errors into silent create flows. `apiFetch()` throws for every non-2xx response ([api.ts](/p:/zorivest/ui/src/renderer/src/lib/api.ts#L15), [api.ts](/p:/zorivest/ui/src/renderer/src/lib/api.ts#L23)), but the report query catches every error and returns `null` ([TradeReportForm.tsx](/p:/zorivest/ui/src/renderer/src/features/trades/TradeReportForm.tsx#L200), [TradeReportForm.tsx](/p:/zorivest/ui/src/renderer/src/features/trades/TradeReportForm.tsx#L208)). The backend contract is specifically `404` for “no report” ([reports.py](/p:/zorivest/packages/api/src/zorivest_api/routes/reports.py#L108), [reports.py](/p:/zorivest/packages/api/src/zorivest_api/routes/reports.py#L110)), so `500`, auth failures, and transport failures are currently misclassified as empty state. The test suite only exercises the 404 case and POST-new path ([trades.test.tsx](/p:/zorivest/ui/src/renderer/src/features/trades/__tests__/trades.test.tsx#L329), [trades.test.tsx](/p:/zorivest/ui/src/renderer/src/features/trades/__tests__/trades.test.tsx#L344)); it still has no regression for non-404 failures or the `PUT` update path.

- **Medium** — The calculator integration is still only partially specified by tests: the modal supports ticker prefill, but the dispatching page does not send it. `PositionCalculatorModal` listens for `detail.ticker` and applies it ([PositionCalculatorModal.tsx](/p:/zorivest/ui/src/renderer/src/features/planning/PositionCalculatorModal.tsx#L57), [PositionCalculatorModal.tsx](/p:/zorivest/ui/src/renderer/src/features/planning/PositionCalculatorModal.tsx#L65)), while `TradePlanPage` dispatches only prices ([TradePlanPage.tsx](/p:/zorivest/ui/src/renderer/src/features/planning/TradePlanPage.tsx#L303), [TradePlanPage.tsx](/p:/zorivest/ui/src/renderer/src/features/planning/TradePlanPage.tsx#L308)). The current test asserts those prices and therefore passes despite the missing ticker handoff ([planning.test.tsx](/p:/zorivest/ui/src/renderer/src/features/planning/__tests__/planning.test.tsx#L670), [planning.test.tsx](/p:/zorivest/ui/src/renderer/src/features/planning/__tests__/planning.test.tsx#L686)).

### Focused verdict

- **Current verdict:** `changes_required`
- **Why:** the earlier `/accounts` and `executed_at` defects appear fixed, but the delivered trade-link flow is still not functionally complete and the passing tests do not protect the real failure modes.

### Test-rigor summary

- The planning suite proves basic rendering and local UI transitions, but it does not prove persistence for `linked_trade_id`, backend-compatible trade filtering, or status rollback on failed PATCH.
- The trades suite proves new-report creation, but it still does not distinguish `404` from other GET failures and does not cover the existing-report `PUT` path.

---

## Recheck Update — 2026-03-24 (Explicit Review of This Handoff)

This pass reviewed the current implementation-review handoff itself against the live code and tests using the modified `critical-review-feedback` workflow priorities: runtime behavior first, then test rigor, with documentation drift treated as secondary unless it misstates behavior or evidence.

### Commands rerun

- `npx vitest run src/renderer/src/features/planning/__tests__/planning.test.tsx` → PASS (49/49)
- `npx vitest run src/renderer/src/features/trades/__tests__/trades.test.tsx` → PASS (53/53)
- `uv run pytest tests/unit/test_api_plans.py` → PASS (19/19)
- Targeted file-state reads for:
  - `ui/src/renderer/src/features/planning/TradePlanPage.tsx`
  - `ui/src/renderer/src/features/trades/TradeReportForm.tsx`
  - `packages/api/src/zorivest_api/routes/trades.py`
  - `ui/src/renderer/src/features/planning/__tests__/planning.test.tsx`
  - `ui/src/renderer/src/features/trades/__tests__/trades.test.tsx`

### Findings

- **Low** — The latest functionality findings in this handoff are now stale. The code and tests have since been corrected for the five issues listed in the previous `Functionality + TDD Focus` section:
  - trade-link saves now include `linked_trade_id` in `PUT` and `PATCH` paths ([TradePlanPage.tsx](/p:/zorivest/ui/src/renderer/src/features/planning/TradePlanPage.tsx#L245), [TradePlanPage.tsx](/p:/zorivest/ui/src/renderer/src/features/planning/TradePlanPage.tsx#L283), [planning.test.tsx](/p:/zorivest/ui/src/renderer/src/features/planning/__tests__/planning.test.tsx#L873))
  - trade lookup now uses `search=` rather than unsupported `ticker=` ([TradePlanPage.tsx](/p:/zorivest/ui/src/renderer/src/features/planning/TradePlanPage.tsx#L174), [trades.py](/p:/zorivest/packages/api/src/zorivest_api/routes/trades.py#L104), [planning.test.tsx](/p:/zorivest/ui/src/renderer/src/features/planning/__tests__/planning.test.tsx#L894))
  - local plan status no longer flips before a failed PATCH confirms success ([TradePlanPage.tsx](/p:/zorivest/ui/src/renderer/src/features/planning/TradePlanPage.tsx#L275), [TradePlanPage.tsx](/p:/zorivest/ui/src/renderer/src/features/planning/TradePlanPage.tsx#L291), [planning.test.tsx](/p:/zorivest/ui/src/renderer/src/features/planning/__tests__/planning.test.tsx#L910))
  - `TradeReportForm` now treats only `404` as “no report” and surfaces non-404 load errors; the suite also covers the `PUT` path ([TradeReportForm.tsx](/p:/zorivest/ui/src/renderer/src/features/trades/TradeReportForm.tsx#L206), [TradeReportForm.tsx](/p:/zorivest/ui/src/renderer/src/features/trades/TradeReportForm.tsx#L288), [trades.test.tsx](/p:/zorivest/ui/src/renderer/src/features/trades/__tests__/trades.test.tsx#L668), [trades.test.tsx](/p:/zorivest/ui/src/renderer/src/features/trades/__tests__/trades.test.tsx#L683))
  - calculator open events now include ticker ([TradePlanPage.tsx](/p:/zorivest/ui/src/renderer/src/features/planning/TradePlanPage.tsx#L316), [PositionCalculatorModal.tsx](/p:/zorivest/ui/src/renderer/src/features/planning/PositionCalculatorModal.tsx#L65), [planning.test.tsx](/p:/zorivest/ui/src/renderer/src/features/planning/__tests__/planning.test.tsx#L933))

- **Low** — Two weak tests remain, but they no longer hide a known behavior bug:
  - `AC-4c` still only asserts that `emotional_state` is a string, not that the selected value is preserved ([trades.test.tsx](/p:/zorivest/ui/src/renderer/src/features/trades/__tests__/trades.test.tsx#L419))
  - the calculator ticker regression checks presence/type of `ticker`, not the exact expected ticker value ([planning.test.tsx](/p:/zorivest/ui/src/renderer/src/features/planning/__tests__/planning.test.tsx#L933))

### Updated verdict

- **Current verdict:** `approved`
- **Why:** the prior functionality blockers recorded in this handoff no longer reproduce in current code, and the remaining gaps are low-risk test-strength issues rather than broken behavior.

### Residual risk

- The review history in this file now contains superseded red findings followed by later fixes and this recheck. Future readers should treat this section as the current state.
