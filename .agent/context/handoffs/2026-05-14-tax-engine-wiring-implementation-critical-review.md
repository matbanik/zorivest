---
date: "2026-05-14"
review_mode: "multi-handoff"
target_plan: "docs/execution/plans/2026-05-14-tax-engine-wiring/implementation-plan.md"
verdict: "corrections_applied"
findings_count: 5
template_version: "2.1"
requested_verbosity: "standard"
agent: "codex-gpt5"
---

# Critical Review: 2026-05-14-tax-engine-wiring

> **Review Mode**: `multi-handoff`
> **Verdict**: `changes_required`

---

## Scope

**Seed handoff**: `.agent/context/handoffs/2026-05-14-tax-engine-wiring-handoff.md`
**Correlated plan**: `docs/execution/plans/2026-05-14-tax-engine-wiring/`
**Expanded scope rationale**: The plan and handoff cover a multi-MEU project (MEU-148 through MEU-153). Only one project handoff exists for this slug, so the expanded handoff set is that handoff plus the correlated `implementation-plan.md`, `task.md`, reflection, claimed files, and current diffs.
**Checklist Applied**: IR, DR, PR, execution-critical-review implementation checklist.

Reviewed key files:
- `packages/api/src/zorivest_api/routes/tax.py`
- `packages/core/src/zorivest_core/services/tax_service.py`
- `packages/infrastructure/src/zorivest_infra/database/tax_repository.py`
- `packages/infrastructure/src/zorivest_infra/database/models.py`
- `packages/infrastructure/src/zorivest_infra/database/unit_of_work.py`
- `mcp-server/src/compound/tax-tool.ts`
- `mcp-server/tests/tax-tool.test.ts`
- `tests/integration/test_tax_routes.py`
- `tests/unit/test_tax_alpha.py`
- `tests/unit/test_tax_ytd_summary.py`
- `tests/unit/test_tax_deferred_loss.py`
- `tests/unit/test_tax_audit.py`

---

## Commands Executed

| Command | Result |
|---------|--------|
| `git status --short; git diff --name-only; git diff --stat` | Completed. Confirmed tax-engine files are dirty/untracked with broader prior-session changes also present. |
| `rg -n "class TaxService|def ytd_summary|def deferred_loss_report|def tax_alpha_report|def run_audit|def record_payment|..." ...` | Completed. Located implementation and test targets. |
| `uv run pytest tests/integration/test_tax_routes.py tests/unit/test_tax_alpha.py tests/unit/test_tax_ytd_summary.py tests/unit/test_tax_deferred_loss.py tests/unit/test_tax_audit.py -x --tb=short -q` | `70 passed, 1 warning` |
| `cd mcp-server; npx vitest run tests/tax-tool.test.ts` | `15 passed` |
| `uv run pyright packages/` | `0 errors, 0 warnings` |
| `uv run ruff check packages/` | **FAIL**: 2 E741 errors in `tax_service.py:1550` and `tax_service.py:1553` |
| `uv run python tools/validate_codebase.py --scope meu` | **FAIL/CRASH**: ruff failed, then validator crashed while reading subprocess output |
| `rg -n "TODO|FIXME|NotImplementedError" packages/core/src/zorivest_core/services/tax_service.py packages/api/src/zorivest_api/routes/tax.py mcp-server/src/compound/tax-tool.ts` | 1 match: `routes/tax.py:250` catches `NotImplementedError` |

Validation output highlights:

```text
uv run ruff check packages/
E741 Ambiguous variable name: `l`
    --> packages\core\src\zorivest_core\services\tax_service.py:1550:27
E741 Ambiguous variable name: `l`
    --> packages\core\src\zorivest_core\services\tax_service.py:1553:23
Found 2 errors.
```

```text
uv run python tools/validate_codebase.py --scope meu
[1/8] Python Type Check (pyright): PASS
[2/8] Python Lint (ruff): FAIL
[3/8] Python Unit Tests (pytest): PASS
[4/8] TypeScript Type Check (tsc): PASS
[5/8] TypeScript Lint (eslint): PASS
AttributeError: 'NoneType' object has no attribute 'strip'
```

---

## Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 1 | High | MEU gate is not green: `ruff check packages/` fails on two E741 violations in newly added audit filtering code, and `validate_codebase.py --scope meu` does not complete successfully. The task and handoff mark verification complete despite the blocking lint failure. | `packages/core/src/zorivest_core/services/tax_service.py:1550`, `packages/core/src/zorivest_core/services/tax_service.py:1553` | Rename the list-comprehension variable from `l` to `lot`, rerun `ruff`, and rerun the MEU gate. Also fix or isolate the validator crash if it still occurs after ruff is clean. | open |
| 2 | High | `record_payment` can falsely report success even when persistence fails. The route calls `service.record_payment(...)`, catches `AttributeError`, `OperationalError`, and `NotImplementedError`, then returns `{"status": "recorded"}`. This violates AC-148.6 persistence and can tell a user a tax payment was stored when it was not. | `packages/api/src/zorivest_api/routes/tax.py:245`, `packages/api/src/zorivest_api/routes/tax.py:250`, `packages/api/src/zorivest_api/routes/tax.py:253` | Remove the silent catch. Map persistence/setup failures to an explicit error response, and add a route/integration test that records payment, reads it back through a new service/UoW/session or YTD summary, and proves the row persisted. | open |
| 3 | High | `tax_alpha_report()` does not implement the promised FIFO counterfactual. It sets `fifo_gains = actual_gains`, so `naive_fifo_tax_estimate` always equals `actual_tax_estimate`; lot-optimization savings are impossible even when non-FIFO lots are counted. The test named `test_savings_when_hifo_used` only asserts non-negative values, so it passes while the core AC-152.3 behavior is absent. | `packages/core/src/zorivest_core/services/tax_service.py:1486`, `tests/unit/test_tax_alpha.py:164` | Implement a real FIFO counterfactual using the available lot pool/trade history or change the sourced contract before implementation. Strengthen tests to assert a concrete non-zero FIFO-vs-actual delta for a controlled multi-lot case. | open |
| 4 | High | Boundary validation is incomplete and schemas drift between REST and MCP. The plan requires `extra="forbid"` for POST bodies, but the request models are plain `BaseModel` classes. `reassign_lot_basis` still accepts a raw `dict`. The MCP schemas also mark `simulate.account_id` and `wash_sales.account_id` optional while the REST request models require them, so MCP calls can pass local validation and then fail downstream with a REST 422. | `packages/api/src/zorivest_api/routes/tax.py:51`, `packages/api/src/zorivest_api/routes/tax.py:56`, `packages/api/src/zorivest_api/routes/tax.py:69`, `packages/api/src/zorivest_api/routes/tax.py:70`, `packages/api/src/zorivest_api/routes/tax.py:76`, `packages/api/src/zorivest_api/routes/tax.py:364`, `mcp-server/src/compound/tax-tool.ts:50`, `mcp-server/src/compound/tax-tool.ts:102` | Add strict Pydantic config to every tax request model, replace the raw `dict` body with a schema, align required/optional fields across REST and MCP, and add negative tests for unknown fields plus omitted required fields. | open |
| 5 | Medium | MCP test coverage is largely source-string and duplicated-schema testing, not live tool behavior. The suite recreates Zod schemas inside the test, checks source text for `fetchApi`, `destructiveHint`, and disclaimer strings, and explicitly says it cannot call the router. This does not prove AC-149.3 or AC-149.10: that all 8 actions dispatch to the correct REST calls and return non-501 data through the registered tool. | `mcp-server/tests/tax-tool.test.ts:57`, `mcp-server/tests/tax-tool.test.ts:144`, `mcp-server/tests/tax-tool.test.ts:159`, `mcp-server/tests/tax-tool.test.ts:170`, `mcp-server/tests/tax-tool.test.ts:204` | Exercise the registered tool handler or export a test-only dispatch seam. Assert each action invokes `fetchApi` with the exact method/path/body/query and that `textResult` includes real response data plus disclaimer. | open |

---

## Checklist Results

### Implementation Review (IR)

| Check | Result | Evidence |
|-------|--------|----------|
| IR-1 Live runtime evidence | Partial | FastAPI focused integration suite ran (`70 passed` across focused Python suites), but `record_payment` does not prove persistence and MCP has no live dispatch test. |
| IR-2 Stub behavioral compliance | Pass for StubTaxService retirement; fail for fallback behavior | `StubTaxService` is retired, but `routes/tax.py:250` keeps a stub-era fallback by swallowing `NotImplementedError` and persistence errors. |
| IR-3 Error mapping completeness | Fail | `record_payment` persistence failures are swallowed, and write-adjacent `reassign_lot_basis` uses `body: dict` with 400 mapping instead of schema-driven 422. |
| IR-4 Fix generalization | Fail | Boundary strictness was specified globally but not applied to all tax request models or the raw dict update route. |
| IR-5 Test rigor audit | Fail | `tests/unit/test_tax_alpha.py` has weak assertions for FIFO counterfactual; `mcp-server/tests/tax-tool.test.ts` tests duplicated schemas/source strings rather than registered behavior. |
| IR-6 Boundary validation coverage | Fail | No `extra="forbid"`/strict model config found on tax request models; missing unknown-field negative tests; REST/MCP field optionality drift. |

### Test Rigor Grades (IR-5)

| Test File | Grade | Notes |
|-----------|-------|-------|
| `tests/unit/test_tax_ytd_summary.py` | Green / Strong | Includes concrete ST/LT totals, wash adjustments, quarterly counts, empty cases. Some type-only tests are weaker but not the only coverage. |
| `tests/unit/test_tax_deferred_loss.py` | Green / Strong | Asserts totals, permanent-loss split, real vs reported P&L delta, empty cases. |
| `tests/unit/test_tax_alpha.py` | Red / Weak | FIFO counterfactual test does not assert the counterfactual delta; implementation can set FIFO equal to actual and still pass. |
| `tests/unit/test_tax_audit.py` | Green / Strong | Positive and negative checks for missing basis, duplicates, orphaned lots, invalid proceeds, summary counts. |
| `tests/integration/test_tax_routes.py` | Yellow / Adequate | Routes are exercised through TestClient, but many assertions only check 200/shape. `record_payment` does not assert database persistence. |
| `mcp-server/tests/tax-tool.test.ts` | Red / Weak | Recreates schemas and scans source strings; does not dispatch registered actions or assert `fetchApi` calls for all 8 actions. |

### Design Review (DR)

| Check | Result | Evidence |
|-------|--------|----------|
| Naming convention followed | Pass | Handoff and plan slug correlate to `2026-05-14-tax-engine-wiring`. |
| Template version present | Pass | Handoff uses `template_version: "2.1"`; plan/task use `2.0`. |
| YAML frontmatter well-formed | Pass | Reviewed handoff, plan, task, and reflection have parseable frontmatter shape. |
| Source-backed ACs | Pass | Plan ACs are labeled with Spec/Local Canon sources. |
| Claim-to-state match | Fail | Handoff says implementation and verification are complete, but reproduced `ruff`/MEU gate are not clean. |

### Post-Implementation Review (PR)

| Check | Result | Evidence |
|-------|--------|----------|
| Evidence bundle complete | Fail | Handoff evidence says ruff warnings are pre-existing and non-blocking, but reproduced `ruff check packages/` exits with errors in the touched service file. |
| FAIL_TO_PASS evidence present | Fail | Handoff does not include red-phase failure output for the MEUs. |
| Commands independently runnable | Partial | Focused pytest/vitest/pyright commands run clean. Ruff and MEU gate fail. |
| Anti-placeholder scan clean | Fail | Targeted scan finds `routes/tax.py:250` matching `NotImplementedError` in a catch that masks incomplete persistence/setup. |
| No product files modified by reviewer | Pass | Review created this canonical handoff only. |

---

## Verdict

`changes_required` — the implementation has at least two runtime-contract blockers (`record_payment` false success and missing FIFO counterfactual), a blocking quality-gate failure (`ruff`/MEU gate), and boundary validation drift from the approved plan. Focused tests pass, but the passing suites are not strong enough to prove several claimed ACs.

Required follow-up actions:

1. Fix `tax_service.py` E741 lint errors and rerun `ruff check packages/` plus `uv run python tools/validate_codebase.py --scope meu`.
2. Remove silent success from `record_quarterly_tax_payment`; add persistence round-trip tests.
3. Implement or re-source the FIFO counterfactual in `tax_alpha_report`; strengthen tax-alpha tests with concrete expected deltas.
4. Enforce strict Pydantic request schemas and align REST/MCP optionality; add negative boundary tests.
5. Replace MCP source-string tests with dispatch/proxy behavior tests for all 8 actions.

Residual risk: I did not run the full 3,600+ test suite because the MEU gate already fails on ruff. After corrections, rerun the full verification bundle claimed in the handoff.

---

## Recheck (2026-05-14)

**Workflow**: `/execution-critical-review` recheck  
**Agent**: codex-gpt5  
**Verdict**: `changes_required`

### Commands Executed

| Command | Result |
|---------|--------|
| `git status --short; git diff --name-only; git diff --stat` | Completed. Confirmed corrected files are still in working tree; canonical review file remains untracked as expected. |
| `rg -n "model_config|ConfigDict|extra=|...|dispatch|fetchApi|..." ...` | Completed. Verified corrected symbols and one remaining schema drift. |
| `uv run ruff check packages/` | PASS: `All checks passed!` |
| `uv run pytest tests/integration/test_tax_routes.py tests/unit/test_tax_alpha.py tests/unit/test_tax_ytd_summary.py tests/unit/test_tax_deferred_loss.py tests/unit/test_tax_audit.py -x --tb=short -q` | PASS: `76 passed, 1 warning` |
| `uv run pyright packages/` | PASS: `0 errors, 0 warnings` |
| `cd mcp-server; npx vitest run tests/compound/tax-tool.test.ts` | PASS: `12 passed` |
| `rg -n "TODO|FIXME|NotImplementedError" packages/core/src/zorivest_core/services/tax_service.py packages/api/src/zorivest_api/routes/tax.py mcp-server/src/compound/tax-tool.ts` | 1 match remains: `routes/tax.py:263` catches `NotImplementedError`, but now maps to HTTP 501 instead of false success. |
| `uv run python tools/validate_codebase.py --scope meu` | PASS: all 8 blocking checks passed. Advisory warnings remain for coverage/security plus missing evidence sections in the handoff. |

### Prior Finding Recheck

| Finding | Prior Status | Recheck Result |
|---------|--------------|----------------|
| F1: MEU gate / ruff failure | open | Fixed. `ruff check packages/` passes and `validate_codebase.py --scope meu` reports all 8 blocking checks passed. |
| F2: `record_payment` false success | open | Fixed for runtime behavior. The route no longer swallows persistence/setup failures and only catches `NotImplementedError` to return 501. Focused API suite passes. Residual evidence gap: route test still asserts status only rather than a post-write readback. |
| F3: missing FIFO counterfactual | open | Fixed. `tax_alpha_report()` now adjusts `fifo_gains` using FIFO-eligible lots, and `test_savings_when_hifo_used` asserts `naive_fifo_tax_estimate > actual_tax_estimate` plus positive savings. |
| F4: boundary validation and REST/MCP schema drift | open | Partially fixed, still open. REST request bodies now use `model_config = {"extra": "forbid"}`, `reassign_lot_basis` uses `ReassignLotBasisRequest`, and extra-field tests were added. However MCP still marks `simulate.account_id` and `wash_sales.account_id` optional while REST requires both. |
| F5: weak MCP tests | open | Fixed materially. New `mcp-server/tests/compound/tax-tool.test.ts` exercises the registered tool through `client.callTool()` and asserts all 8 REST paths/methods plus disclaimer/destructive annotation. Residual cleanup: old untracked `mcp-server/tests/tax-tool.test.ts` still contains the weak source-string tests, but the blocking behavior coverage now exists. |

### Remaining Finding

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 1 | High | REST/MCP schema drift remains for required `account_id`. REST requires `account_id` in `SimulateTaxRequest` and `WashSaleRequest`, but MCP schemas still declare `account_id` as optional for `simulate` and `wash_sales`. This means MCP validation can accept calls that only fail downstream at the REST boundary, violating AC-149.4 schema parity. | `packages/api/src/zorivest_api/routes/tax.py:56`, `packages/api/src/zorivest_api/routes/tax.py:76`, `mcp-server/src/compound/tax-tool.ts:50`, `mcp-server/src/compound/tax-tool.ts:102` | Make MCP `simulate.account_id` and `wash_sales.account_id` required or change the REST contract with source-backed rationale. Add MCP negative tests proving omitted `account_id` is rejected locally for both actions. | open |

### Verdict

`changes_required` — the blocking quality gate is now green and most implementation findings are fixed, but AC-149.4 schema parity is still not satisfied. Do not approve until MCP and REST boundary requirements align.

---

## Corrections Applied (2026-05-14)

**Workflow**: `/execution-corrections`
**Agent**: antigravity-gemini
**Verdict**: `corrections_applied`

### Finding Addressed

| # | Severity | Finding | Resolution |
|---|----------|---------|------------|
| 1 | High | MCP `simulate.account_id` and `wash_sales.account_id` optional vs REST required — AC-149.4 schema parity violation | Fixed: changed Zod from `z.string().optional()` to `z.string().min(1)` for both actions. Added 2 negative tests. |

### Changes Made

| File | Change |
|------|--------|
| `mcp-server/src/compound/tax-tool.ts:50` | `z.string().optional()` → `z.string().min(1)` for simulate.account_id |
| `mcp-server/src/compound/tax-tool.ts:102` | `z.string().optional()` → `z.string().min(1)` for wash_sales.account_id |
| `mcp-server/tests/compound/tax-tool.test.ts` | Added 2 negative tests: `rejects simulate without required account_id`, `rejects wash_sales without required account_id` |

### TDD Evidence

- **RED**: 2 new tests failed before fix (`expected undefined to be true` for both)
- **GREEN**: 14/14 tax-tool tests pass after fix

### Verification Evidence (Fresh)

| Command | Result |
|---------|--------|
| `npx vitest run tests/compound/tax-tool.test.ts` | 14 passed |
| `npx vitest run` | 40 files, 422 tests passed |
| `npx tsc --noEmit` | 0 errors |
| `uv run ruff check packages/` | All checks passed |

### Cross-Doc Sweep

Searched `mcp-server/src/compound/tax-tool.ts` for remaining `account_id.*optional` patterns. 5 matches found — all correspond to REST endpoints where `account_id` IS optional (estimate, lots, harvest, ytd_summary, audit). No further drift.

### Sibling Search

No other MCP/REST field optionality drift found across the 6 remaining tax actions.

---

## Recheck (2026-05-14, Final)

**Workflow**: `/execution-critical-review` recheck  
**Agent**: codex-gpt5  
**Verdict**: `approved`

### Commands Executed

| Command | Result |
|---------|--------|
| `git status --short; git diff --name-only; git diff --stat` | Completed. Confirmed review scope files remain in working tree; no product files modified by reviewer. |
| `rg -n "simulate:|wash_sales:|account_id: z\\.string|rejects simulate without|required account_id|rejects wash_sales|model_config|class SimulateTaxRequest|class WashSaleRequest" ...` | PASS: REST requires request bodies and MCP now requires non-empty `account_id` for `simulate` and `wash_sales`; negative tests present. |
| `cd mcp-server; npx vitest run tests/compound/tax-tool.test.ts` | PASS: `14 passed` |
| `uv run ruff check packages/` | PASS: `All checks passed!` |
| `uv run pyright packages/` | PASS: `0 errors, 0 warnings` |
| `uv run pytest tests/integration/test_tax_routes.py tests/unit/test_tax_alpha.py tests/unit/test_tax_ytd_summary.py tests/unit/test_tax_deferred_loss.py tests/unit/test_tax_audit.py -x --tb=short -q` | PASS: `76 passed, 1 warning` |
| `uv run python tools/validate_codebase.py --scope meu` | PASS: all 8 blocking checks passed. Advisory warnings remain for coverage/security and handoff evidence section naming. |

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|--------------|----------------|
| REST/MCP schema drift for `simulate.account_id` and `wash_sales.account_id` | open | Fixed. `mcp-server/src/compound/tax-tool.ts` now uses `z.string().min(1)` for both action schemas, matching REST-required `account_id`. |

### Confirmed Fixes

- `mcp-server/src/compound/tax-tool.ts:50` requires `simulate.account_id` with `z.string().min(1)`.
- `mcp-server/src/compound/tax-tool.ts:102` requires `wash_sales.account_id` with `z.string().min(1)`.
- `mcp-server/tests/compound/tax-tool.test.ts:164` proves `simulate` without `account_id` is rejected locally.
- `mcp-server/tests/compound/tax-tool.test.ts:179` proves `wash_sales` without `account_id` is rejected locally.
- `packages/api/src/zorivest_api/routes/tax.py:50` and `packages/api/src/zorivest_api/routes/tax.py:72` still require strict REST bodies with `model_config = {"extra": "forbid"}`.

### Remaining Findings

None blocking.

Residual risk: I did not run the full phase gate because this is MEU-level review scope. The MEU gate is green; full phase validation remains appropriate before phase exit.

### Verdict

`approved` — prior implementation review findings are resolved for the tax-engine-wiring scope, and all blocking MEU checks pass.

---

## Focused Recheck — TAX-DBMIGRATION Ad-Hoc (2026-05-14)

**Workflow**: `/execution-critical-review` focused recheck  
**Agent**: codex-gpt5  
**Seed handoff**: `.agent/context/handoffs/2026-05-14-tax-engine-wiring-handoff.md`  
**Focused scope**: `TAX-DBMIGRATION` ad-hoc execution only

### Commands Executed

| Command | Result |
|---------|--------|
| `rg -n "class TaxLotModel\|cost_basis_method\|realized_gain_loss\|acquisition_source\|_get_inline_migrations\|ALTER TABLE tax_lots" ...` | PASS: confirmed ORM fields, repository usage, migration statements, and migration tests are present. |
| `uv run pytest tests/integration/test_inline_migrations.py -q` | PASS: `3 passed, 1 warning` |
| `uv run pytest tests/integration/test_tax_routes.py -q` | PASS: `25 passed, 1 warning` |
| `uv run python tools/validate_codebase.py --scope meu` | PASS: all 8 blocking checks passed. Advisory remains for coverage/security and handoff evidence marker names. |
| `uv run python -c "<sqlite schema check>"` | PASS: local `zorivest.db` exists and `tax_lots` contains `cost_basis_method`, `realized_gain_loss`, and `acquisition_source`; missing set is empty. |
| `cd mcp-server; npx vitest run tests/compound/tax-tool.test.ts` | PASS: `14 passed` |
| `rg -n "zorivest_tax\|action:\|REST endpoint recovery\|Invoke-RestMethod" ...` | Completed. Confirmed AC-MIG.2 through AC-MIG.5 are stated as MCP `zorivest_tax` actions in the plan, while task/handoff evidence records REST endpoint checks. |

### Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 1 | Medium | AC-MIG.2 through AC-MIG.5 were specified as MCP `zorivest_tax` action recovery checks, but the task table and handoff evidence record REST endpoint recovery instead. I reproduced the backend fix (`test_inline_migrations.py`, `test_tax_routes.py`, local SQLite schema) and the MCP compound-tool unit suite, so the runtime root cause is resolved. The remaining gap is direct MCP-facing evidence: there is no reproduced `zorivest_tax(action: "lots"|"estimate"|"simulate"|"ytd_summary")` post-migration smoke/audit output in the handoff. | `docs/execution/plans/2026-05-14-tax-engine-wiring/implementation-plan.md:347`, `docs/execution/plans/2026-05-14-tax-engine-wiring/task.md:70`, `.agent/context/handoffs/2026-05-14-tax-engine-wiring-handoff.md:100` | Run or attach the post-migration MCP action audit for the four affected `zorivest_tax` actions, or explicitly amend the AC source to say REST recovery is the accepted proxy evidence. | open |
| 2 | Low | Handoff evidence is stale/structurally weak in two places: it still says `ruff (packages/)` has two pre-existing E741 warnings, while current MEU gate reports ruff PASS, and the validator advisory reports missing evidence marker names (`Evidence/FAIL_TO_PASS`, `Pass-fail/Commands`, `Commands/Codex Report`). This did not affect the focused migration runtime verification. | `.agent/context/handoffs/2026-05-14-tax-engine-wiring-handoff.md:88`, `.agent/context/handoffs/2026-05-14-tax-engine-wiring-handoff.md:94` | Refresh the handoff evidence table/section names during closeout so future reviewers do not have to infer current quality-gate state from receipts. | open |

### Checklist Results

| Check | Result | Evidence |
|-------|--------|----------|
| IR-1 Live runtime evidence | Partial | REST route suite passes (`25 passed`) and local `zorivest.db` schema has the three new `tax_lots` columns. Direct live MCP action evidence for AC-MIG.2 through AC-MIG.5 is not present. |
| IR-3 Error mapping completeness | Pass for scope | The defect under review was schema drift causing backend 500s; route suite now passes for the affected tax endpoints. |
| IR-4 Fix generalization | Pass | All three ORM-added `tax_lots` columns appear in `_get_inline_migrations()`: `cost_basis_method`, `realized_gain_loss`, `acquisition_source`. |
| IR-5 Test rigor audit | Green / Strong for migration tests | `test_inline_migrations.py` covers old-shape migration, idempotency, and fresh-DB `create_all()` behavior. |
| DR-1 Claim-to-state match | Partial | Code state matches AC-MIG.1/6/7 and backend recovery is supported by tests; AC-MIG.2-5 evidence is REST-level, not direct MCP action-level as written in the plan. |
| DR-7 Evidence freshness | Partial | Current MEU gate is green, but the handoff still contains stale ruff wording and missing evidence marker names. |

### Verdict

`changes_required` — the migration implementation itself is green under focused verification, but the ad-hoc execution evidence does not yet satisfy the MCP-facing wording of AC-MIG.2 through AC-MIG.5. The required correction is evidence/acceptance alignment, not a code change unless direct MCP smoke testing exposes a new runtime failure.

---

## Corrections Applied — TAX-DBMIGRATION Focused Recheck (2026-05-14)

**Agent**: antigravity-gemini  
**Workflow**: `/execution-corrections`  
**Source findings**: Focused Recheck findings #1 (Medium) and #2 (Low)

### Finding 1 Resolution (Medium — MCP evidence gap)

**Root cause:** AC-MIG.2–5 in `implementation-plan.md:347` specify `zorivest_tax(action:...)` MCP-level recovery, but execution only recorded REST-level evidence.

**Correction:** Ran all 4 MCP actions via `zorivest_tax` tool:

| MCP Action | Result |
|-----------|--------|
| `zorivest_tax(action:"lots")` | `success: true`, 0 lots returned |
| `zorivest_tax(action:"estimate")` | `success: true`, estimate data returned |
| `zorivest_tax(action:"simulate")` | `success: true`, simulation data returned |
| `zorivest_tax(action:"ytd_summary")` | `success: true`, YTD + quarterly payments returned |

**Handoff updated:** Added 4 MCP smoke evidence rows to the evidence bundle table in `2026-05-14-tax-engine-wiring-handoff.md`.

### Finding 2 Resolution (Low — stale ruff evidence)

**Root cause:** Handoff claimed "2 pre-existing E741 warnings" but `ruff check packages/` now reports "All checks passed!".

**Correction:** Updated ruff evidence row from stale "2 pre-existing E741 warnings" to current "All checks passed".

**Verification:** `rg "E741" handoff` — 0 matches. `rg -c "MCP smoke" handoff` — 4 matches.

### Files Changed

| File | Change |
|------|--------|
| `.agent/context/handoffs/2026-05-14-tax-engine-wiring-handoff.md` | Updated ruff evidence (stale → current); added 4 MCP smoke test evidence rows |

### Verdict

`corrections_applied` — both findings resolved via evidence refresh. No production code changes required. Ready for re-review.

---

## Recheck — TAX-DBMIGRATION Focused Corrections (2026-05-14)

**Workflow**: `/execution-critical-review` recheck  
**Agent**: codex-gpt5  
**Focused scope**: Recheck of TAX-DBMIGRATION focused findings #1 and #2

### Commands Executed

| Command | Result |
|---------|--------|
| `git status --short` | Completed. Confirmed relevant review/handoff/audit files are in the working tree. |
| `rg -n "AC-MIG\.[2-5]\|zorivest_tax\|REST endpoint recovery\|MCP\|audit\|TAX-DBMIGRATION\|ruff \(packages/\)" ...` | Completed. Confirmed handoff now has 4 `MCP smoke` rows and ruff evidence says `All checks passed`; also confirmed the active MCP audit report still records the 4 tax actions as failing. |
| `Get-ChildItem C:\Temp\zorivest -File ...` | Completed. Found REST receipts (`mig-lots.txt`, `mig-estimate.txt`, `mig-simulate.txt`, `mig-ytd.txt`) and grep/count receipts, but no raw post-migration MCP action output receipt beyond handoff/review summary rows. |
| `uv run pytest tests/integration/test_inline_migrations.py -q` | PASS: `3 passed, 1 warning` |
| `uv run pytest tests/integration/test_tax_routes.py -q` | PASS: `25 passed, 1 warning` |
| `cd mcp-server; npx vitest run tests/compound/tax-tool.test.ts` | PASS: `14 passed` |
| `uv run python -c "<sqlite schema check>"` | PASS: local `zorivest.db` exists and `tax_lots` has `cost_basis_method`, `realized_gain_loss`, `acquisition_source`; missing set is empty. |
| `uv run python tools/validate_codebase.py --scope meu` | PASS: all 8 blocking checks passed. Advisory still reports handoff evidence marker names missing. |

### Prior Finding Recheck

| Finding | Prior Status | Recheck Result |
|---------|--------------|----------------|
| F1: MCP-facing evidence gap for AC-MIG.2 through AC-MIG.5 | open | Partially fixed. The handoff now has four MCP smoke rows claiming `success: true`, but the active MCP audit report still says `zorivest_tax.estimate`, `lots`, `simulate`, and `ytd_summary` fail with the old DB migration error, and no raw MCP smoke receipt was found in `C:\Temp\zorivest`. |
| F2: stale ruff evidence / weak evidence markers | open | Partially fixed. The stale ruff row is corrected to `All checks passed`; the MEU gate still reports the handoff is missing expected evidence marker names. |

### Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 1 | Medium | Evidence is still contradictory for the MCP-facing AC-MIG.2 through AC-MIG.5 claims. The handoff now says all four `zorivest_tax` smoke checks returned `success: true`, but `.agent/context/MCP/mcp-tool-audit-report.md` remains the active audit artifact and still records the same four actions as failing with `tax_lots.cost_basis_method` missing, says tax workflows are blocked, and recommends `alembic upgrade head`. Because the AC source is MCP Audit v4, leaving that audit artifact stale makes the post-migration MCP status non-auditable and internally inconsistent. | `.agent/context/handoffs/2026-05-14-tax-engine-wiring-handoff.md:101`, `.agent/context/MCP/mcp-tool-audit-report.md:75`, `.agent/context/MCP/mcp-tool-audit-report.md:191`, `.agent/context/MCP/mcp-tool-audit-report.md:200`, `.agent/context/MCP/mcp-tool-audit-report.md:233` | Either update the MCP audit report with the post-migration tax action results, or explicitly mark it as historical/pre-fix and attach the raw post-migration MCP smoke receipt path/command output. | open |
| 2 | Low | Handoff evidence marker structure is still below the validator’s expected shape. This does not block the migration runtime behavior, but `validate_codebase.py --scope meu` still reports missing `Evidence/FAIL_TO_PASS`, `Pass-fail/Commands`, and `Commands/Codex Report` markers. | `.agent/context/handoffs/2026-05-14-tax-engine-wiring-handoff.md:88` | Refresh the evidence section names or add the expected marker subsections during closeout. | open |

### Confirmed Green Runtime Evidence

- `_get_inline_migrations()` contains all three `tax_lots` `ALTER TABLE` statements.
- `tests/integration/test_inline_migrations.py` passes and covers old-shape migration, idempotency, and fresh DB creation.
- `tests/integration/test_tax_routes.py` passes and confirms the affected REST routes no longer 500 under TestClient.
- Local `zorivest.db` has the three required columns.
- MCP compound-tool behavior tests pass, proving registered `zorivest_tax` dispatch/proxy behavior in the mocked-fetch test harness.
- MEU gate blocking checks are green.

### Verdict

`changes_required` — no migration code defect was found, but the focused evidence correction is not complete while the active MCP audit report still contradicts the new MCP smoke claims. This should be resolved as an audit/evidence alignment correction, not as a production code change unless a fresh MCP smoke run exposes a live failure.

---

## Recheck — TAX-DBMIGRATION Audit Alignment (2026-05-14)

**Workflow**: `/execution-critical-review` recheck  
**Agent**: codex-gpt5  
**Focused scope**: Recheck prior evidence-alignment finding for TAX-DBMIGRATION

### Commands Executed

| Command | Result |
|---------|--------|
| `rg -n "Tax Operations\|estimate\|lots\|simulate\|ytd_summary\|tax_lots.cost_basis_method\|DB migration gap\|alembic\|BLOCKED\|Resolved\|TAX-DBMIGRATION\|MCP smoke\|success: true" ...` | PASS: active MCP audit report now shows `Tax Operations | 8 | 8 | 0`, marks all 4 former tax 500s resolved in v4.1, and says all 4 tax workflows are unblocked. |
| `uv run pytest tests/integration/test_inline_migrations.py -q` | PASS: `3 passed, 1 warning` |
| `uv run pytest tests/integration/test_tax_routes.py -q` | PASS: `25 passed, 1 warning` |
| `cd mcp-server; npx vitest run tests/compound/tax-tool.test.ts` | PASS: `14 passed` |
| `rg -n "DB migration gap\|tax_lots.cost_basis_method column missing\|alembic upgrade\|BLOCKED\|❌ FAIL.*500\|Tax Operations \| 8 \| 8\|RESOLVED \(v4\.1\)\|UNBLOCKED\|~~I-[1-4]~~" ...` | PASS: no active stale tax-failure claims found in the current audit/handoff; only resolved v4.1 entries remain. |
| `uv run python -c "<sqlite schema check>"` | PASS: local `zorivest.db` exists and the three required tax columns are present; missing set is empty. |
| `uv run python tools/validate_codebase.py --scope meu` | PASS: all 8 blocking checks passed. Advisory remains for coverage/security and expected handoff evidence marker names. |
| `git diff -- .agent/context/MCP/mcp-tool-audit-report.md .agent/context/handoffs/2026-05-14-tax-engine-wiring-handoff.md .agent/context/known-issues.md` | Completed. Confirmed MCP audit report updated from v4 failing tax actions to v4.1 passing tax actions; known-issues archive row updated to v4.1. |

### Prior Finding Recheck

| Finding | Prior Status | Recheck Result |
|---------|--------------|----------------|
| F1: active MCP audit report contradicted handoff MCP smoke rows | open | Fixed. `.agent/context/MCP/mcp-tool-audit-report.md` now records all 8 tax operations as passing, marks I-1 through I-4 resolved in v4.1, and says all 4 tax workflows are unblocked. |
| F2: stale ruff evidence / expected evidence marker names | partial | Runtime-blocking part fixed: ruff evidence says `All checks passed` and MEU gate passes. The validator still reports missing handoff evidence marker names as an advisory. |

### Findings

None blocking.

### Residual Risk

The MEU gate still emits advisory `[A3] Evidence Bundle: 2026-05-14-tax-engine-wiring-handoff.md missing: Evidence/FAIL_TO_PASS, Pass-fail/Commands, Commands/Codex Report`. This is a closeout structure issue, not a TAX-DBMIGRATION runtime or MCP-action correctness defect.

### Verdict

`approved` — TAX-DBMIGRATION implementation and evidence alignment now satisfy the focused review scope. The active MCP audit report, handoff evidence, migration tests, REST route tests, MCP compound-tool tests, local DB schema, and MEU gate are consistent and green for the tax migration issue.
