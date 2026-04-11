# Task Handoff Template

## Task

- **Date:** 2026-04-11
- **Task slug:** boundary-validation-phase2-plan-critical-review
- **Owner role:** reviewer
- **Scope:** Plan review of `docs/execution/plans/2026-04-11-boundary-validation-phase2/` triggered from `/critical-review-feedback`

## Inputs

- User request: Review the linked workflow, `implementation-plan.md`, and `task.md`
- Specs/docs referenced:
  - `AGENTS.md`
  - `.agent/workflows/critical-review-feedback.md`
  - `.agent/context/current-focus.md`
  - `.agent/context/known-issues.md`
  - `.agent/docs/emerging-standards.md`
  - `docs/execution/plans/2026-04-11-boundary-validation-phase2/implementation-plan.md`
  - `docs/execution/plans/2026-04-11-boundary-validation-phase2/task.md`
  - `docs/build-plan/04-rest-api.md`
  - `docs/build-plan/04d-api-settings.md`
  - `docs/build-plan/06c-gui-planning.md`
  - `docs/build-plan/09-scheduling.md`
  - `packages/api/src/zorivest_api/routes/scheduling.py`
  - `packages/api/src/zorivest_api/routes/watchlists.py`
  - `packages/api/src/zorivest_api/routes/settings.py`
  - `tests/unit/test_api_scheduling.py`
  - `tests/unit/test_api_watchlists.py`
  - `tests/unit/test_api_settings.py`
  - `mcp-server/src/tools/settings-tools.ts`
  - `mcp-server/tests/settings-tools.test.ts`
  - `docs/execution/plans/2026-03-19-mcp-trade-smoke-test-fixes/implementation-plan.md`
- Constraints:
  - Review-only pass; no plan or product-code corrections in this session
  - Canonical review file for this plan folder
  - Findings must be evidence-backed and severity-ranked

## Role Plan

1. orchestrator
2. tester
3. reviewer

## Coder Output

- Changed files:
  - `.agent/context/handoffs/2026-04-11-boundary-validation-phase2-plan-critical-review.md`
- Design notes / ADRs referenced:
  - None
- Commands run:
  - `Get-ChildItem P:\zorivest\.agent\context\handoffs\*.md -Exclude README.md,TEMPLATE.md`
  - `Get-ChildItem P:\zorivest\docs\build-plan\*.md`
  - `rg -n "watchlist|watchlists|/watchlists" P:\zorivest\docs\build-plan`
  - `rg -n "patch_schedule|/policies/\{policy_id\}/schedule|cron_expression|enabled: bool|timezone" P:\zorivest\docs\build-plan\09-scheduling.md P:\zorivest\tests\unit\test_api_scheduling.py P:\zorivest\mcp-server P:\zorivest\ui`
- Results:
  - No product-code changes; review-only

## Tester Output

- Commands run:
  - `Get-ChildItem P:\zorivest\.agent\context\handoffs\*.md -Exclude README.md,TEMPLATE.md`
  - `Get-ChildItem P:\zorivest\docs\build-plan\*.md`
  - `rg -n "watchlist|watchlists|/watchlists" P:\zorivest\docs\build-plan`
  - `rg -n "patch_schedule|/policies/\{policy_id\}/schedule|cron_expression|enabled: bool|timezone" P:\zorivest\docs\build-plan\09-scheduling.md P:\zorivest\tests\unit\test_api_scheduling.py P:\zorivest\mcp-server P:\zorivest\ui`
- Additional evidence gathered:
  - Confirmed this is **plan review mode**, not implementation review: `task.md` has no completed items and no correlated work handoffs exist for `MEU-BV6`, `MEU-BV7`, or `MEU-BV8`
  - Verified current REST, MCP, and test contracts for scheduling, watchlists, and settings before evaluating the proposed hardening
- Pass/fail matrix:
  - Review-mode correlation and canonical handoff target: PASS
  - Source-traceability for watchlist scope: FAIL
  - Settings contract preservation: FAIL
  - Scheduling patch contract preservation: FAIL
  - Task-state accuracy for an unstarted plan: FAIL
- Repro failures:
  - `implementation-plan.md` proposes wrapping `PUT /settings` in `{ "settings": { ... } }`, but the canonical settings spec and MCP callers currently use a flat JSON map
  - `implementation-plan.md` proposes moving `PATCH /policies/{id}/schedule` from discrete parameters to a request body, but the current Phase 9 spec and route tests still define parameter-based patching
  - The plan cites `04b` for watchlists even though `04b-api-accounts.md` is the accounts spec; the actual watchlist canon is `04-rest-api.md` inline plus `06c-gui-planning.md`
  - `task.md` frontmatter says `status: "in_progress"` while every listed task remains `[ ]`
- Coverage/test gaps:
  - The plan does not yet include any evidence that the two proposed contract migrations were reconciled with the published build-plan docs or existing MCP consumers
- Evidence bundle location:
  - Inline in this handoff
- FAIL_TO_PASS / PASS_TO_PASS result:
  - Not applicable; review-only
- Mutation score:
  - Not run
- Contract verification status:
  - `changes_required`

## Reviewer Output

- Findings by severity:
  - **High:** The settings hardening plan changes the public `PUT /settings` request shape and mislabels that change as `Local Canon`, but the current canon and callers all require the existing flat map contract. The proposed wrapper appears at `docs/execution/plans/2026-04-11-boundary-validation-phase2/implementation-plan.md:35` and is reinforced by AC-1 plus the spec-sufficiency table at `docs/execution/plans/2026-04-11-boundary-validation-phase2/implementation-plan.md:131` and `docs/execution/plans/2026-04-11-boundary-validation-phase2/implementation-plan.md:140`. That conflicts with the published REST spec in `docs/build-plan/04d-api-settings.md:47`, which explicitly defines `body: dict[str, Any]` with `Body: {"key1": "value1", "key2": "value2"}`; with the existing route tests in `tests/unit/test_api_settings.py:54`, `tests/unit/test_api_settings.py:83`, and `tests/unit/test_api_settings.py:219`, which all exercise flat-map writes; with the MCP implementation in `mcp-server/src/tools/settings-tools.ts:71`, which sends `JSON.stringify(params.settings)` directly to `/settings`; and with `mcp-server/tests/settings-tools.test.ts:97`, which asserts the body keys are top-level strings (`body.theme`, `body.timezone`). The repo also already recorded this exact flat-map behavior as correct, not buggy, in `docs/execution/plans/2026-03-19-mcp-trade-smoke-test-fixes/implementation-plan.md:18`. This is a breaking REST/MCP contract change, not an in-place boundary-hardening step, so it needs either a spec update plus caller migration plan or a redesign that preserves the flat-map body while tightening validation.
  - **High:** The scheduling plan treats a query/parameter-to-body migration as `Local Canon`, but the current Phase 9 canon still defines `PATCH /policies/{id}/schedule` with discrete optional parameters, and the current unit tests assert that contract. The migration is introduced at `docs/execution/plans/2026-04-11-boundary-validation-phase2/implementation-plan.md:32`, then encoded as AC-3 and the spec-sufficiency rationale at `docs/execution/plans/2026-04-11-boundary-validation-phase2/implementation-plan.md:57` and `docs/execution/plans/2026-04-11-boundary-validation-phase2/implementation-plan.md:66`. The authoritative scheduling spec still shows `cron_expression`, `enabled`, and `timezone` as route parameters in `docs/build-plan/09-scheduling.md:2614`, and the current route test still calls the endpoint with `params={"cron_expression": "0 10 * * *"}` at `tests/unit/test_api_scheduling.py:306`. The live route implementation matches that spec in `packages/api/src/zorivest_api/routes/scheduling.py:280`. Even if there are no current GUI callers, this is still a public API contract rewrite, not a carry-forward BV1 pattern. The plan needs either a source-backed spec change before approval or a non-breaking hardening strategy that preserves the current patch surface.
  - **Medium:** Watchlist source traceability is incomplete and partly wrong, which means the plan does not pass the Spec Sufficiency Gate for that MEU yet. The plan frontmatter cites only scheduling and settings sources at `docs/execution/plans/2026-04-11-boundary-validation-phase2/implementation-plan.md:4`, while the header claims watchlists belong to `04b` at `docs/execution/plans/2026-04-11-boundary-validation-phase2/implementation-plan.md:13`. But `04b-api-accounts.md` is the accounts spec; the actual watchlist route canon is inline in `docs/build-plan/04-rest-api.md:221` and consumed by the Planning GUI contract in `docs/build-plan/06c-gui-planning.md:148`. The plan may still choose the proposed request-model hardening, but it should cite the real watchlist authorities before claiming the ACs are source-backed.
  - **Low:** `task.md` describes an unstarted plan as `status: "in_progress"` even though every listed task is still unchecked. The mismatch appears in `docs/execution/plans/2026-04-11-boundary-validation-phase2/task.md:5` versus the `[ ]` task table rows starting at `docs/execution/plans/2026-04-11-boundary-validation-phase2/task.md:17`. This does not block the technical design, but it weakens review-mode auto-discovery and state clarity.
- Open questions:
  - Should the settings MEU preserve the flat `dict[str, Any]` request shape and harden it in-place, instead of wrapping it in `BulkUpdateSettingsRequest`?
  - Is there a human-approved reason to change the scheduling patch endpoint contract before the build-plan docs are updated, or should boundary validation remain non-breaking here?
- Verdict:
  - `changes_required`
- Residual risk:
  - If approved as written, this plan will convert two existing public write surfaces into new request contracts while describing both changes as routine boundary hardening. That creates avoidable breakage risk for MCP consumers and spec drift risk for the REST layer before implementation even starts.
- Anti-deferral scan result:
  - No product-code placeholders introduced in this review. Findings require `/planning-corrections` on the plan artifacts before approval.

## Guardrail Output (If Required)

- Safety checks:
  - Review-only session; no destructive operations
- Blocking risks:
  - The two contract migrations above should not proceed as implicit `Local Canon` decisions
- Verdict:
  - Not required

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:** human
- **Timestamp:** pending

## Final Summary

- Status:
  - `changes_required`
- Next steps:
  - Rework the settings MEU so boundary hardening preserves the current flat-map `PUT /settings` contract, or explicitly escalate a spec-breaking change with caller migration scope
  - Remove the unsupported `Local Canon` claim from the scheduling PATCH body migration unless the build plan is updated first
  - Correct the watchlist source references to the actual canonical docs before approving the plan
  - Align `task.md` status with the fact that implementation has not started

---

## Recheck Update — 2026-04-11

### Scope

- Rechecked the revised `implementation-plan.md` and `task.md` against the four findings from the initial review.
- Verified current file state against the same canonical sources used in the first pass: `04d-api-settings.md`, `09-scheduling.md`, `04-rest-api.md`, `06c-gui-planning.md`, the MCP settings tool/tests, and the current API route tests.

### Resolved Since Prior Pass

- The plan no longer rewrites the `PUT /settings` contract. It now explicitly preserves the flat-map body shape in `docs/execution/plans/2026-04-11-boundary-validation-phase2/implementation-plan.md:31` and `docs/execution/plans/2026-04-11-boundary-validation-phase2/implementation-plan.md:122`, which matches the 04d spec at `docs/build-plan/04d-api-settings.md:47`, the MCP tool body construction at `mcp-server/src/tools/settings-tools.ts:79`, the MCP test assertions at `mcp-server/tests/settings-tools.test.ts:111`, and the existing route tests at `tests/unit/test_api_settings.py:77`.
- The scheduling MEU no longer migrates PATCH scheduling to a request body. It now preserves discrete query params in `docs/execution/plans/2026-04-11-boundary-validation-phase2/implementation-plan.md:45` and `docs/execution/plans/2026-04-11-boundary-validation-phase2/implementation-plan.md:56`, which aligns with the Phase 9 spec at `docs/build-plan/09-scheduling.md:2614` and the current route test at `tests/unit/test_api_scheduling.py:306`.
- Watchlist source traceability is corrected. The plan now cites `04-rest-api.md` and `06c-gui-planning.md` in frontmatter and header at `docs/execution/plans/2026-04-11-boundary-validation-phase2/implementation-plan.md:4` and `docs/execution/plans/2026-04-11-boundary-validation-phase2/implementation-plan.md:13`, matching the canonical watchlist route tables at `docs/build-plan/04-rest-api.md:221` and `docs/build-plan/06c-gui-planning.md:148`.
- `task.md` status now reflects an unstarted plan. The frontmatter is `status: "draft"` at `docs/execution/plans/2026-04-11-boundary-validation-phase2/task.md:5`, consistent with the fully unchecked task table starting at `docs/execution/plans/2026-04-11-boundary-validation-phase2/task.md:17`.

### Findings

- No remaining findings from the prior pass.

### Verdict

`approved`

### Residual Risk

- This approval covers the revised plan and task artifacts only. Implementation has not started yet, so runtime boundary-hardening quality still depends on the later TDD execution and verification passes.
