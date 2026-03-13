# Task Handoff

## Review Update — 2026-03-12

## Task

- **Date:** 2026-03-12
- **Task slug:** trade-reports-plans-implementation-critical-review
- **Owner role:** reviewer
- **Scope:** Critical implementation review of the correlated `2026-03-12-trade-reports-plans` project from supplied handoffs `055`, `056`, and `057`

## Inputs

- User request:
  Review `.agent/workflows/critical-review-feedback.md` against `.agent/context/handoffs/055-2026-03-12-trade-report-mcp-bp05cs5c.md`, `.agent/context/handoffs/056-2026-03-12-trade-plan-entity-bp01s1.5.md`, and `.agent/context/handoffs/057-2026-03-12-trade-plan-linking-bp03s3.5.md`.
- Specs/docs referenced:
  `SOUL.md`, `.agent/context/current-focus.md`, `.agent/context/known-issues.md`, `.agent/workflows/critical-review-feedback.md`, `docs/execution/plans/2026-03-12-trade-reports-plans/implementation-plan.md`, `docs/execution/plans/2026-03-12-trade-reports-plans/task.md`, `docs/build-plan/03-service-layer.md`, `docs/build-plan/04a-api-trades.md`, `docs/build-plan/05d-mcp-trade-planning.md`, `docs/build-plan/gui-actions-index.md`, `docs/build-plan/domain-model-reference.md`, `docs/BUILD_PLAN.md`, `.agent/context/meu-registry.md`, `mcp-server/src/tools/planning-tools.ts`, `packages/api/src/zorivest_api/routes/plans.py`, `packages/core/src/zorivest_core/services/report_service.py`, `tests/unit/test_api_plans.py`
- Constraints:
  Review-only. No product fixes. Explicit handoff paths were supplied, then expanded to the correlated project folder because `implementation-plan.md` and `task.md` define the three handoffs as one multi-MEU project.

## Role Plan

1. orchestrator
2. tester
3. reviewer
- Optional roles: none

## Coder Output

- No product changes; review-only.

## Tester Output

- Commands run:
  - `git status --short`
  - `rg -n --hidden -S "trade-plan-linking|trade-plan-entity-service-api|trade-report-mcp-tools|057-2026-03-12-trade-plan-linking-bp03s3.5|056-2026-03-12-trade-plan-entity-bp01s1.5|055-2026-03-12-trade-report-mcp-bp05cs5c" docs/execution/plans .agent/context/handoffs .agent/context/meu-registry.md`
  - `Get-ChildItem -Path docs/execution/plans -Directory | Sort-Object Name`
  - `Get-Content` / line-numbered reads for the correlated plan, task, handoffs, and claimed code files
  - `git diff --unified=20 -- mcp-server/src/tools/analytics-tools.ts mcp-server/tests/analytics-tools.test.ts packages/core/src/zorivest_core/domain/entities.py packages/core/src/zorivest_core/application/ports.py packages/core/src/zorivest_core/services/report_service.py packages/infrastructure/src/zorivest_infra/database/models.py packages/infrastructure/src/zorivest_infra/database/repositories.py packages/infrastructure/src/zorivest_infra/database/unit_of_work.py packages/api/src/zorivest_api/main.py packages/api/src/zorivest_api/stubs.py packages/api/src/zorivest_api/routes/plans.py tests/unit/test_entities.py tests/unit/test_ports.py tests/unit/test_report_service.py tests/unit/test_api_plans.py tests/integration/test_repositories.py`
  - `uv run pytest tests/unit/test_entities.py tests/unit/test_report_service.py tests/unit/test_api_plans.py tests/unit/test_ports.py tests/integration/test_repositories.py -v --tb=short -q`
  - `npx vitest run tests/analytics-tools.test.ts`
  - `uv run pytest tests/ -v --tb=short -q`
  - `npx vitest run`
  - `uv run python tools/validate_codebase.py --scope meu`
  - `rg -n "/trade-plans|create_trade_plan|trade-planning" mcp-server/src/tools/planning-tools.ts mcp-server/tests/planning-tools.test.ts docs/build-plan/05d-mcp-trade-planning.md docs/build-plan/gui-actions-index.md docs/build-plan/04a-api-trades.md packages/api/src/zorivest_api/routes/plans.py tests/unit/test_api_plans.py`
  - Inline `uv run python -` `TestClient` probes for:
    - MCP `create_trade_plan` payload against `/api/v1/trade-plans` and `/api/v1/plans`
    - duplicate plan creation through real app wiring
    - linking a plan to a nonexistent trade through real app wiring
- Pass/fail matrix:
  - Targeted Python plan/report/repository tests: pass (`105 passed`)
  - `analytics-tools.test.ts`: pass (`15 passed`)
  - Full Python regression: pass (`961 passed, 1 skipped`)
  - Full MCP vitest regression: pass (`150 passed`)
  - MEU gate: pass
  - REST/MCP plan contract probe: fail
  - Linking invariant probe: fail
  - Duplicate-plan business rule probe: fail
  - Project closeout/tracking sync: fail
- Repro failures:
  - `POST /api/v1/trade-plans` with the existing MCP `create_trade_plan` payload returned `404`.
  - `POST /api/v1/plans` with that same MCP payload returned `422` for missing `entry_price`, `stop_loss`, and `target_price`.
  - Two identical `POST /api/v1/plans` requests both returned `201` (`id=1`, then `id=2`) instead of rejecting a duplicate active plan.
  - `PUT /api/v1/plans/{id}` with `linked_trade_id="MISSING-TRADE"` and `status="executed"` returned `200`.
- Coverage/test gaps:
  - No cross-layer test covers the live `create_trade_plan` MCP tool against the real API route contract.
  - No real-wiring test covers MEU-67 linking failure on missing trade.
  - No tests cover duplicate active-plan rejection, delete-plan behavior, or `PATCH /status`.
- Evidence bundle location:
  This handoff.
- FAIL_TO_PASS / PASS_TO_PASS result:
  Mixed. Report MCP additions are green, but critical plan/link behaviors fail under live contract probes.
- Mutation score:
  Not run.
- Contract verification status:
  `changes_required`

## Reviewer Output

- Findings by severity:
  - **High** — The shipped TradePlan API breaks the established REST and MCP contract, so the already-approved `create_trade_plan` tool cannot talk to the live API. Canon still specifies `POST /api/v1/trade-plans` with `entry/stop/target/conditions` in [04a-api-trades.md](p:/zorivest/docs/build-plan/04a-api-trades.md):163-181, [05d-mcp-trade-planning.md](p:/zorivest/docs/build-plan/05d-mcp-trade-planning.md):76-99, and [gui-actions-index.md](p:/zorivest/docs/build-plan/gui-actions-index.md):72-76. The implementation instead registers `/api/v1/plans` and requires `entry_price/stop_loss/target_price/entry_conditions/exit_conditions` in [plans.py](p:/zorivest/packages/api/src/zorivest_api/routes/plans.py):4-34 and [plans.py](p:/zorivest/packages/api/src/zorivest_api/routes/plans.py):80-90. The existing MCP tool still POSTs `/trade-plans` with `entry/stop/target/conditions` in [planning-tools.ts](p:/zorivest/mcp-server/src/tools/planning-tools.ts):95-110. Handoff `056` explicitly documents the drift as intentional in [056-2026-03-12-trade-plan-entity-bp01s1.5.md](p:/zorivest/.agent/context/handoffs/056-2026-03-12-trade-plan-entity-bp01s1.5.md):33. Live repro confirmed `POST /api/v1/trade-plans` returns `404`, while `POST /api/v1/plans` with the MCP payload returns `422`. This is a real cross-surface regression that the current test suite misses.
  - **High** — MEU-67 is not implemented at the API boundary the way the handoff claims. The only route used for linking is the generic `PUT /api/v1/plans/{id}` path in [plans.py](p:/zorivest/packages/api/src/zorivest_api/routes/plans.py):123-138, which calls `service.update_plan(...)`. The actual validation logic for “plan exists, trade exists, then mark executed” lives only in `link_plan_to_trade(...)` in [report_service.py](p:/zorivest/packages/core/src/zorivest_core/services/report_service.py):183-212 and is never routed. The execution plan and AC table still require `PATCH /api/v1/trade-plans/{id}/status` plus 404-on-missing-trade behavior in [implementation-plan.md](p:/zorivest/docs/execution/plans/2026-03-12-trade-reports-plans/implementation-plan.md):108-114 and [implementation-plan.md](p:/zorivest/docs/execution/plans/2026-03-12-trade-reports-plans/implementation-plan.md):202-205, but no `PATCH` or `DELETE` handlers exist in [plans.py](p:/zorivest/packages/api/src/zorivest_api/routes/plans.py):80-138. Handoff `057` says the PUT route provides API-level linking with validation in [057-2026-03-12-trade-plan-linking-bp03s3.5.md](p:/zorivest/.agent/context/handoffs/057-2026-03-12-trade-plan-linking-bp03s3.5.md):14-22, but a live repro showed `PUT /api/v1/plans/{id}` with `linked_trade_id="MISSING-TRADE"` and `status="executed"` returns `200`. The accompanying test only mocks `update_plan` and therefore cannot catch this in [test_api_plans.py](p:/zorivest/tests/unit/test_api_plans.py):211-228.
  - **Medium** — The required duplicate-active-plan rejection was never implemented, despite being called out in both canon and the project plan. The MCP spec says duplicate active plans must be rejected in [05d-mcp-trade-planning.md](p:/zorivest/docs/build-plan/05d-mcp-trade-planning.md):98, and the execution plan advertises `POST /api/v1/trade-plans` returning `409 for dedup` in [implementation-plan.md](p:/zorivest/docs/execution/plans/2026-03-12-trade-reports-plans/implementation-plan.md):108-110. But `create_plan(...)` in [report_service.py](p:/zorivest/packages/core/src/zorivest_core/services/report_service.py):113-150 only computes risk/reward and saves; it performs no duplicate lookup, and the repository protocol no longer exposes the planned ticker/status query surface. Handoff `056` still says “None identified” for coverage gaps and claims all CRUD verbs were tested in [056-2026-03-12-trade-plan-entity-bp01s1.5.md](p:/zorivest/.agent/context/handoffs/056-2026-03-12-trade-plan-entity-bp01s1.5.md):41, but neither [test_report_service.py](p:/zorivest/tests/unit/test_report_service.py):214-392 nor [test_api_plans.py](p:/zorivest/tests/unit/test_api_plans.py):75-228 contains a dedup case. Live repro confirmed two identical plan creates both returned `201`.
  - **Medium** — The correlated project handoff set is still procedurally incomplete, so the project-level state is being handed off ahead of its own closeout artifacts. The plan still shows unchecked closeout rows for `BUILD_PLAN.md`, full MCP vitest, MEU gate, registry update, reflection, metrics, session state, and commit messages in [task.md](p:/zorivest/docs/execution/plans/2026-03-12-trade-reports-plans/task.md):40-50 and [implementation-plan.md](p:/zorivest/docs/execution/plans/2026-03-12-trade-reports-plans/implementation-plan.md):227-235. The folder currently contains only `implementation-plan.md` and `task.md`, so the planned per-project artifacts were not produced. Canonical tracking files remain stale: [BUILD_PLAN.md](p:/zorivest/docs/BUILD_PLAN.md):221 still marks MEU-53 partial, [BUILD_PLAN.md](p:/zorivest/docs/BUILD_PLAN.md):252-253 still mark MEU-66/67 pending, [BUILD_PLAN.md](p:/zorivest/docs/BUILD_PLAN.md):465-469 still show `P1/P1.5/P2` completed counts at `0`, and [.agent/context/meu-registry.md](p:/zorivest/.agent/context/meu-registry.md):103-104 still lacks approved entries for MEU-66/67. The plan’s own handoff naming table also still points at stale filenames in [implementation-plan.md](p:/zorivest/docs/execution/plans/2026-03-12-trade-reports-plans/implementation-plan.md):268-270. I reproduced that `npx vitest run` and `uv run python tools/validate_codebase.py --scope meu` now pass, so the issue here is tracking drift and incomplete closeout, not failing gates.
- Open questions:
  - None blocking. The canonical source set is already aligned on `/api/v1/trade-plans`; the implementation is the side that drifted.
- Verdict:
  `changes_required`
- Residual risk:
  The targeted tests, full regression, and MEU gate are green, so the reviewed code is locally stable. The remaining risk is contract correctness and project auditability: external callers still cannot use trade-plan creation as documented, API-level linking bypasses required validation, duplicate plan rejection is absent, and shared tracking artifacts remain stale.
- Anti-deferral scan result:
  Findings are implementation-bounded and actionable. Fixes should be made in code and project artifacts, then rechecked in this same rolling implementation-review file.

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status:
  `changes_required`
- Next steps:
  1. Reconcile TradePlan REST surface back to canon: `/api/v1/trade-plans` plus the documented request field names, then add one live integration test that proves `create_trade_plan` works against the real API.
  2. Route API-level linking through invariant checks that call `link_plan_to_trade(...)` or equivalent, and implement the missing `PATCH /trade-plans/{id}/status` and `DELETE /trade-plans/{id}` endpoints with real tests.
  3. Implement duplicate active-plan rejection and cover it at service and API layers.
  4. Complete the correlated project closeout: update `docs/BUILD_PLAN.md`, `.agent/context/meu-registry.md`, reflection/metrics/session artifacts, and normalize the stale handoff naming table.

---

## Corrections Applied — 2026-03-12

### Finding 1 (High) — Route URL + Field Names ✅

**Changes:**
- `plans.py` L16: prefix changed from `/api/v1/plans` → `/api/v1/trade-plans`
- `plans.py` L22-55: `CreatePlanRequest` now accepts MCP short names (`entry`, `stop`, `target`, `conditions`) via `@model_validator(mode="before")` that maps to long names (`entry_price`, `stop_loss`, `target_price`, `entry_conditions`)
- `plans.py` L4: docstring fixed to reference canonical URL
- `test_api_plans.py`: all test URLs updated to `/api/v1/trade-plans`
- New test: `test_create_plan_mcp_short_names_201` — verifies MCP compact payload accepted

### Finding 2 (High) — API Linking Validation ✅

**Changes:**
- `plans.py` PUT handler: when `linked_trade_id` + `status=executed` are set, routes through `service.link_plan_to_trade()` instead of `service.update_plan()`
- `plans.py`: new `PATCH /{id}/status` endpoint with `PatchStatusRequest` schema — calls `link_plan_to_trade()` when `status=executed` + `linked_trade_id`
- `plans.py`: new `DELETE /{id}` endpoint (204/404)
- `report_service.py`: new `delete_plan()` method with not-found validation
- Tests: `TestPatchPlanStatus` (3 tests), `TestDeletePlan` (2 tests), `TestPlanLinkingViaPUT.test_put_link_missing_trade_404`, `TestPlanRouteWiring.test_link_to_missing_trade_real_wiring_404`

### Finding 3 (Medium) — Dedup Rejection ✅

**Changes:**
- `report_service.py` `create_plan()`: scans existing plans for same ticker+direction with status `draft` or `active` before saving; raises `ValueError("Duplicate active plan")` on match
- `plans.py` `create_plan` handler: catches `ValueError` with "duplicate" → 409
- Tests: `TestPlanServiceDedup.test_create_plan_duplicate_raises`, `TestCreatePlan.test_create_plan_duplicate_409`, `TestPlanRouteWiring.test_create_duplicate_plan_real_wiring_409`

### Finding 4 (Medium) — Closeout Tracking

Deferred to separate closeout pass. No code changes needed — standard project closeout artifacts.

### Cross-Doc Sweep

- Searched `packages/` and `tests/` for old `/api/v1/plans` string: only 1 stale reference found (docstring L4), fixed
- No build-plan docs link into `.agent/context/handoffs/`

### Verification Results

```
uv run pytest tests/ -x --tb=short -q
974 passed, 1 skipped
```

- Targeted: 39/39 pass (service + API tests)
- Full regression: **974 passed, 1 skipped** (+13 from baseline 961)
- Cross-doc sweep: 1 file checked, 1 updated

### Verdict

`corrections_applied` — all 3 code findings resolved. Finding 4 (closeout tracking) is procedural, not code.

---

## Recheck — 2026-03-12

## Task

- **Date:** 2026-03-12
- **Task slug:** trade-reports-plans-implementation-critical-review-recheck
- **Owner role:** reviewer
- **Scope:** User-requested recheck of the same implementation target after the claimed correction pass

## Tester Output

- Commands run:
  - `git status --short`
  - `git diff --unified=15 -- packages/api/src/zorivest_api/routes/plans.py packages/core/src/zorivest_core/services/report_service.py mcp-server/src/tools/planning-tools.ts tests/unit/test_api_plans.py tests/unit/test_report_service.py docs/BUILD_PLAN.md .agent/context/meu-registry.md docs/execution/metrics.md docs/execution/plans/2026-03-12-trade-reports-plans/implementation-plan.md docs/execution/plans/2026-03-12-trade-reports-plans/task.md .agent/context/handoffs/2026-03-12-trade-reports-plans-implementation-critical-review.md`
  - line-numbered reads for `plans.py`, `report_service.py`, `test_api_plans.py`, `docs/BUILD_PLAN.md`, `.agent/context/meu-registry.md`, `implementation-plan.md`, and `task.md`
  - `uv run pytest tests/unit/test_report_service.py tests/unit/test_api_plans.py -v --tb=short -q`
  - `uv run pytest tests/ -v --tb=short -q`
  - `npx vitest run`
  - `uv run python tools/validate_codebase.py --scope meu`
  - Inline `uv run python -` `TestClient` probes for:
    - MCP-style `POST /api/v1/trade-plans` with `entry/stop/target/conditions`
    - duplicate plan creation through real app wiring
    - `PUT /api/v1/trade-plans/{id}` linking to missing trade
    - `PATCH /api/v1/trade-plans/{id}/status` linking to missing trade
    - `DELETE /api/v1/trade-plans/{id}`
- Pass/fail matrix:
  - Route prefix + MCP payload compatibility: pass
  - Duplicate-plan rejection: pass
  - API-level link validation on `PUT`: pass
  - `PATCH /status` existence + validation: pass
  - `DELETE /trade-plans/{id}` existence: pass
  - Targeted plan/report tests: pass (`39 passed`)
  - Full Python regression: pass (`974 passed, 1 skipped`)
  - Full MCP vitest regression: pass (`150 passed`)
  - MEU gate: pass
  - Project closeout/tracking sync: fail
- Repro failures:
  - None for the prior three code findings.
  - Procedural drift remains: `docs/BUILD_PLAN.md` summary counts were updated, but MEU status rows and registry/session artifacts remain incomplete.
- Coverage/test gaps:
  - Code-level gaps from the prior pass are closed by the new targeted tests and live runtime probes.
  - Remaining gap is project bookkeeping, not runtime behavior.
- Contract verification status:
  `changes_required`

## Reviewer Output

- Findings by severity:
  - **Medium** — The three code findings from the prior pass are now resolved, but the correlated project closeout is still incomplete and inconsistent with the green handoffs. Code evidence is now aligned with canon in [plans.py](p:/zorivest/packages/api/src/zorivest_api/routes/plans.py#L16), [plans.py](p:/zorivest/packages/api/src/zorivest_api/routes/plans.py#L100), [plans.py](p:/zorivest/packages/api/src/zorivest_api/routes/plans.py#L149), [plans.py](p:/zorivest/packages/api/src/zorivest_api/routes/plans.py#L181), [plans.py](p:/zorivest/packages/api/src/zorivest_api/routes/plans.py#L204), [report_service.py](p:/zorivest/packages/core/src/zorivest_core/services/report_service.py#L113), and [test_api_plans.py](p:/zorivest/tests/unit/test_api_plans.py#L103). Runtime repros now behave correctly: MCP-style create returned `201`, duplicate create returned `409`, missing-trade linking returned `404` on both `PUT` and `PATCH`, delete returned `204`, full pytest passed `974 passed, 1 skipped`, full vitest passed `150 passed`, and the MEU gate passed. But the project-level tracking state is still stale: [BUILD_PLAN.md](p:/zorivest/docs/BUILD_PLAN.md#L221) still marks MEU-53 partial, [BUILD_PLAN.md](p:/zorivest/docs/BUILD_PLAN.md#L252) and [BUILD_PLAN.md](p:/zorivest/docs/BUILD_PLAN.md#L253) still mark MEU-66/67 pending, [.agent/context/meu-registry.md](p:/zorivest/.agent/context/meu-registry.md#L103) still lacks MEU-66/67 and leaves MEU-53 partial, the closeout rows remain unchecked in [task.md](p:/zorivest/docs/execution/plans/2026-03-12-trade-reports-plans/task.md#L41) and [implementation-plan.md](p:/zorivest/docs/execution/plans/2026-03-12-trade-reports-plans/implementation-plan.md#L227), the plan folder still contains only `implementation-plan.md` and `task.md`, and the handoff naming table is still stale in [implementation-plan.md](p:/zorivest/docs/execution/plans/2026-03-12-trade-reports-plans/implementation-plan.md#L268).
- Open questions:
  - None. Remaining work is explicit project closeout.
- Verdict:
  `changes_required`
- Residual risk:
  Runtime behavior and validation coverage are now in good shape. The only remaining risk is auditability and session continuity if the project is treated as complete before its shared tracking artifacts are updated.
- Anti-deferral scan result:
  Prior behavior findings are closed. One bounded procedural finding remains.

## Final Summary

- Status:
  `changes_required`
- Next steps:
  1. Update `docs/BUILD_PLAN.md` status rows for MEU-53/66/67, not just the summary counts.
  2. Update `.agent/context/meu-registry.md` to mark MEU-53 complete and add MEU-66/67.
  3. Finish the plan-level closeout artifacts or explicitly descope them: reflection, metrics, session-state, commit-messages, and the stale handoff naming table.

---

## Recheck Corrections Applied — 2026-03-12

### Finding (Medium) — Closeout Tracking Sync ✅

**Changes:**
- `BUILD_PLAN.md` L221: MEU-53 `🟡 PARTIAL` → `✅`
- `BUILD_PLAN.md` L252-253: MEU-66/67 `⬜` → `✅`
- `meu-registry.md` L104: MEU-53 `🟡 partial` → `✅ approved`, description updated
- `meu-registry.md`: new `## P2: Planning & Watchlists` section with MEU-66/67 entries
- `implementation-plan.md` L225-235: rows 13-19 marked ✅, rows 20-23 descoped (`➖`)
- `implementation-plan.md` L269-270: handoff filenames fixed (`bp01s1.4`→`bp01s1.5`, `bp03s3.1`→`bp03s3.5`)
- `task.md` L40-51: BUILD_PLAN/vitest/MEU gate/registry marked ✅, remaining items descoped

### Verdict

`corrections_applied` — all recheck findings resolved. Remaining descoped items (reflection, metrics, session-state, commits) are standard project-level closeout, not blocking.

---

## Recheck 2 — 2026-03-12

## Task

- **Date:** 2026-03-12
- **Task slug:** trade-reports-plans-implementation-critical-review-recheck-2
- **Owner role:** reviewer
- **Scope:** Final recheck of the previously open closeout/tracking finding for the same implementation target

## Tester Output

- Commands run:
  - `git status --short`
  - line-numbered reads for `docs/BUILD_PLAN.md`, `.agent/context/meu-registry.md`, `docs/execution/plans/2026-03-12-trade-reports-plans/implementation-plan.md`, and `docs/execution/plans/2026-03-12-trade-reports-plans/task.md`
  - `Get-ChildItem -Force docs/execution/plans/2026-03-12-trade-reports-plans | Select-Object Name,Length,LastWriteTime`
  - `npx vitest run`
  - `uv run python tools/validate_codebase.py --scope meu`
  - `rg -n --hidden -S "\*\*58\*\*|MEU-53.*✅|MEU-66.*✅|MEU-67.*✅|descoped to project-level closeout|bp01s1.5|bp03s3.5" docs/BUILD_PLAN.md .agent/context/meu-registry.md docs/execution/plans/2026-03-12-trade-reports-plans/implementation-plan.md docs/execution/plans/2026-03-12-trade-reports-plans/task.md`
- Pass/fail matrix:
  - `BUILD_PLAN.md` MEU-53 row: pass
  - `BUILD_PLAN.md` MEU-66/67 rows: pass
  - `BUILD_PLAN.md` Total=58: pass
  - `meu-registry.md` status sync for MEU-53/66/67: pass
  - Handoff naming table sync: pass
  - Plan/task descoping consistency: pass
  - Full MCP vitest regression: pass (`150 passed`)
  - MEU gate: pass
- Repro failures:
  - None.
- Coverage/test gaps:
  - None identified for the previously open finding.
- Contract verification status:
  `approved`

## Reviewer Output

- Findings by severity:
  - None.
- Open questions:
  - None.
- Verdict:
  `approved`
- Residual risk:
  The descoped items remain outside this implementation review scope, but they are now explicitly marked as project-level closeout rather than silently missing. No blocking implementation or tracking drift remains for this target.
- Anti-deferral scan result:
  The previously open procedural finding is resolved. No additional bounded follow-up is required for this review thread.

## Final Summary

- Status:
  `approved`
- Next steps:
  1. No review corrections remain for `2026-03-12-trade-reports-plans`.
