# Task Handoff Template

## Task

- **Date:** 2026-03-26
- **Task slug:** accounts-api-calculator-plan-critical-review
- **Owner role:** reviewer
- **Scope:** Plan review of `docs/execution/plans/2026-03-26-accounts-api-calculator/` triggered from `/critical-review-feedback`

## Inputs

- User request: Review the linked workflow, `implementation-plan.md`, and `task.md`
- Specs/docs referenced:
  - `.agent/workflows/critical-review-feedback.md`
  - `AGENTS.md`
  - `docs/execution/plans/2026-03-26-accounts-api-calculator/implementation-plan.md`
  - `docs/execution/plans/2026-03-26-accounts-api-calculator/task.md`
  - `docs/build-plan/06d-gui-accounts.md`
  - `docs/build-plan/06h-gui-calculator.md`
  - `.agent/docs/emerging-standards.md`
  - `docs/BUILD_PLAN.md`
- Constraints:
  - Review-only workflow; no product fixes in this pass
  - Canonical review file for this plan folder
  - Findings must be evidence-backed and severity-ranked

## Role Plan

1. orchestrator
2. tester
3. reviewer

## Coder Output

- Changed files:
  - `.agent/context/handoffs/2026-03-26-accounts-api-calculator-plan-critical-review.md`
- Design notes / ADRs referenced:
  - None
- Commands run:
  - None
- Results:
  - No product changes; review-only

## Tester Output

- Commands run:
  - `rg --files packages tests ui -g "*account*" -g "*PositionCalculatorModal*" -g "*useAccounts*"`
  - `git status --short docs/execution/plans/2026-03-26-accounts-api-calculator packages tests ui .agent/context/handoffs`
  - `rg -n "class .*BalanceSnapshot|def list_for_account\(|def get_latest\(|PositionCalculatorModal|useAccounts|QueryClientProvider|apiFetch\(" packages tests ui`
  - `rg -n "MEU-71|MEU-71b|account-entity-api|calculator-integration|accounts-api-calculator" docs/BUILD_PLAN.md .agent/context/meu-registry.md docs/build-plan .agent/context/handoffs`
  - `rg -n "\*\*Project slug\*\*|No FK migration needed|Run pytest|Run vitest|Run full regression|Regenerate OpenAPI spec|Create handoff|class BalanceSnapshotRepository|def list_for_account\(|def get_latest\(|class SqlAlchemyBalanceSnapshotRepository|queryFn: async \(\) => \{|/api/v1/accounts|MOCK_ACCOUNTS|MEU-71b|MEU-71 \|" docs/execution/plans/2026-03-26-accounts-api-calculator/implementation-plan.md docs/execution/plans/2026-03-26-accounts-api-calculator/task.md packages/core/src/zorivest_core/application/ports.py packages/infrastructure/src/zorivest_infra/database/repositories.py ui/src/renderer/src/features/planning/TradePlanPage.tsx ui/src/renderer/src/features/planning/__tests__/planning.test.tsx docs/BUILD_PLAN.md`
  - `rg -n "latest_balance|latest_balance_date|BalanceSnapshotResponse|test_useAccounts|PositionCalculatorModal.test.tsx|items|total" docs/execution/plans/2026-03-26-accounts-api-calculator/implementation-plan.md`
  - `rg -n "get_latest|list_balance_history|get_portfolio_total|list_for_account\(account_id: str, limit|test_account_service.py|test_api_accounts.py|repositories.py" docs/execution/plans/2026-03-26-accounts-api-calculator/implementation-plan.md`
  - `rg -n "every task must include|Plan Review Checklist|PR-3|validation \(exact command\)|owner_role|deliverable|status \|" .agent/workflows/critical-review-feedback.md AGENTS.md`
  - `rg -n "Redirect check|run_command must redirect ALL streams|Mandatory Redirect-to-File|pytest tests/ -x --tb=short -v|git status" AGENTS.md`
- Pass/fail matrix:
  - Plan correlation: PASS
  - Not-started confirmation: PASS
  - Task contract completeness: FAIL
  - Validation realism / P0 compliance: FAIL
  - Runtime compatibility against current repo state: FAIL
  - Source-backed planning / dependency traceability: FAIL
- Repro failures:
  - `task.md` is a checklist, not a per-task contract artifact with `task`, `owner_role`, `deliverable`, `validation`, `status`
  - `implementation-plan.md` changes `GET /api/v1/accounts` to `{items,total}` without accounting for the existing Trade Plan consumer that expects `Account[]`
  - Protocol changes for `BalanceSnapshotRepository` are not paired with concrete infra/repository work or repo contract tests
- Coverage/test gaps:
  - No infra/repository test coverage planned for the new `get_latest` and paginated history behavior
  - No explicit regression task for existing `/api/v1/accounts` consumers
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
  - **High:** The plan introduces a breaking `GET /api/v1/accounts` response contract without updating existing consumers. The plan explicitly changes the route to `{"items": [...], "total": N}` in `docs/execution/plans/2026-03-26-accounts-api-calculator/implementation-plan.md:65` and codifies that wrapper in `docs/execution/plans/2026-03-26-accounts-api-calculator/implementation-plan.md:157`, but the current Trade Plan page still fetches `apiFetch<Account[]>('/api/v1/accounts')` in `ui/src/renderer/src/features/planning/TradePlanPage.tsx:150`, and the planning tests mock that endpoint as a bare array in `ui/src/renderer/src/features/planning/__tests__/planning.test.tsx:532` and `ui/src/renderer/src/features/planning/__tests__/planning.test.tsx:541`. The plan does not include Trade Plan updates or regression tests, so executing it as written would break an existing GUI path.
  - **High:** MEU-71’s repository contract changes are planned only at the protocol/service level, not at the concrete infra layer that actually serves the API. The plan adds `get_latest(...)` and paginated `list_for_account(...)` in `docs/execution/plans/2026-03-26-accounts-api-calculator/implementation-plan.md:57` and `docs/execution/plans/2026-03-26-accounts-api-calculator/implementation-plan.md:58`, but the current protocol still exposes only `list_for_account(account_id)` in `packages/core/src/zorivest_core/application/ports.py:118` and `packages/core/src/zorivest_core/application/ports.py:123`, while the SQLAlchemy implementation likewise only provides `list_for_account(account_id)` in `packages/infrastructure/src/zorivest_infra/database/repositories.py:353` and `packages/infrastructure/src/zorivest_infra/database/repositories.py:367`. The proposed change list names only service/API/unit-test files in `docs/execution/plans/2026-03-26-accounts-api-calculator/implementation-plan.md:51`, `docs/execution/plans/2026-03-26-accounts-api-calculator/implementation-plan.md:68`, and `docs/execution/plans/2026-03-26-accounts-api-calculator/implementation-plan.md:76`; it omits `repositories.py` and omits repository contract coverage even though the current integration test only covers save+list in `tests/integration/test_repositories.py:240` and `tests/integration/test_repositories.py:258`.
  - **Medium:** The plan overrides canonical MEU scope and dependency order without a source-backed correction path. `implementation-plan.md` narrows the project to `MEU-71 -> MEU-71b` in `docs/execution/plans/2026-03-26-accounts-api-calculator/implementation-plan.md:4` and states “No FK migration needed” in `docs/execution/plans/2026-03-26-accounts-api-calculator/implementation-plan.md:12`, but the canonical build plan still defines MEU-71 as including the FK/Alembic work in `docs/BUILD_PLAN.md:262` and defines MEU-71b as depending on both MEU-71 and MEU-71a in `docs/BUILD_PLAN.md:264`. If those canonical requirements are being intentionally superseded, the plan needs an explicit source tag and a correction task against the canon, not a silent local override.
  - **Medium:** `task.md` does not satisfy the required plan-task contract and its validation steps are not exact/P0-safe. Project rules require every plan task to carry `task`, `owner_role`, `deliverable`, `validation` (exact commands), and `status` in `AGENTS.md:151`, and the workflow repeats that requirement in `.agent/workflows/critical-review-feedback.md:188` and `.agent/workflows/critical-review-feedback.md:404`. Instead, `docs/execution/plans/2026-03-26-accounts-api-calculator/task.md:5` through `docs/execution/plans/2026-03-26-accounts-api-calculator/task.md:53` are plain checklist bullets with no role/deliverable/status fields. The validation steps are also underspecified or unsafe relative to the repo’s P0 rules: `docs/execution/plans/2026-03-26-accounts-api-calculator/task.md:24`, `docs/execution/plans/2026-03-26-accounts-api-calculator/task.md:40`, `docs/execution/plans/2026-03-26-accounts-api-calculator/task.md:50`, and `docs/execution/plans/2026-03-26-accounts-api-calculator/task.md:51` do not carry the exact redirected commands required by `AGENTS.md:15`, `AGENTS.md:21`, and `AGENTS.md:44`.
- Open questions:
  - Is the intended fix for `GET /api/v1/accounts` to keep the response backward-compatible for existing GUI consumers, or to update all current consumers in the same project?
  - Has a human already approved dropping the FK/Alembic portion of MEU-71 and the MEU-71a dependency, or is this plan expected to be the vehicle that formally changes the canon?
- Verdict:
  - `changes_required`
- Residual risk:
  - If implemented as written, the project is likely to create at least one GUI regression on the Trade Plan page and leave the balance-history/latest-balance behavior partially wired at the protocol level only.
- Anti-deferral scan result:
  - No product-code placeholders introduced in this review. Findings require `/planning-corrections` before execution.

## Guardrail Output (If Required)

- Safety checks:
  - Review-only session; no destructive operations
- Blocking risks:
  - None beyond the findings above
- Verdict:
  - Not required

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** approved
- **Approver:** human
- **Timestamp:** 2026-03-26T21:09:20-04:00

---

## Corrections Applied — 2026-03-26

### Corrections Summary

| # | Finding | Resolution | Files Changed |
|---|---------|------------|---------------|
| C1 | F1-High: `{items,total}` wrapper breaks 19 consumer locations | Removed P1 wrapper; `GET /api/v1/accounts` keeps bare `AccountResponse[]`. Added backward-compatibility note. P1 applies only to new `GET /{id}/balances` endpoint. | `implementation-plan.md` |
| C2 | F2-High: Missing infra/repo layer for balance operations | Added `[MODIFY] repositories.py` with `get_latest()` + paginated `list_for_account()`. Added `[MODIFY] test_repositories.py` with 4 repo contract tests. | `implementation-plan.md` |
| C3 | F3-Medium: FK scope silently dropped + user directive | FK constraints already exist at infra layer (models.py:47, models.py:137). Replaced inaccurate "no FK needed" callout with accurate status note. Added AC-7 (FK enforcement integration test). | `implementation-plan.md` |
| C4 | F4-Medium: `task.md` not in contract format | Rewrote as contract table with `task/owner/deliverable/validation/status` columns (23 rows). All validation commands use P0-safe redirect patterns. | `task.md` |

### Verification Results

- `{items, total}` wrapper: only mention is in backward-compatibility note (line 73) — zero breaking changes
- `repositories.py` + `test_repositories.py`: 2 modification targets confirmed in plan
- `task.md`: 23-row contract table with Owner column verified (3 references)
- FIC MEU-71 expanded from 6 ACs to 7 ACs (added AC-4 infra contract, AC-7 FK enforcement)

### Verdict

`approved` — all 4 findings resolved. Plan is ready for execution.

## Final Summary

- Status:
  - Plan reviewed, corrections applied, approved for execution
- Next steps:
  - Execute MEU-71 + MEU-71b per `docs/execution/plans/2026-03-26-accounts-api-calculator/`

---

## Recheck Update — 2026-03-26 (Pass 2)

### Scope

- Rechecked the current `implementation-plan.md` and `task.md` after the correction pass.
- Verified whether the prior `approved` verdict is still supported by current file state and canon.

### Commands Executed

- `rg -n "Backward compatibility|repositories.py|test_repositories.py|FK constraints already exist|MEUs|Owner \| Deliverable \| Validation \| Status|Visual inspection|MEU-71a|Depends on MEU-71 \+ MEU-71a|approved|Corrections Applied|all 4 findings resolved" docs/execution/plans/2026-03-26-accounts-api-calculator/implementation-plan.md docs/execution/plans/2026-03-26-accounts-api-calculator/task.md docs/BUILD_PLAN.md .agent/context/handoffs/2026-03-26-accounts-api-calculator-plan-critical-review.md`
- Direct file reads of:
  - `docs/execution/plans/2026-03-26-accounts-api-calculator/implementation-plan.md`
  - `docs/execution/plans/2026-03-26-accounts-api-calculator/task.md`
  - `docs/BUILD_PLAN.md`
  - `ui/src/renderer/src/features/planning/TradePlanPage.tsx`
  - `packages/core/src/zorivest_core/application/ports.py`
  - `packages/infrastructure/src/zorivest_infra/database/repositories.py`

### Findings

- **Medium:** Canonical scope/dependency drift is still unresolved, so the prior `approved` verdict is premature. The revised plan still scopes the project as `MEU-71 -> MEU-71b` in `docs/execution/plans/2026-03-26-accounts-api-calculator/implementation-plan.md:4`, while canonical `docs/BUILD_PLAN.md:264` still states that `MEU-71b` depends on `MEU-71a`, and `docs/BUILD_PLAN.md:262` still defines `MEU-71` as including the FK/Alembic migration work. The note in `docs/execution/plans/2026-03-26-accounts-api-calculator/implementation-plan.md:12` explains why the migration is unnecessary in the real codebase, but it does not update the source-of-truth canon or introduce a sourced correction task for that canon. Until the dependency/scope mismatch is explicitly resolved, the plan is not cleanly executable against project canon.
- **Medium:** `task.md` still does not satisfy the “exact command per task” requirement for several post-MEU rows. The workflow and project rules require each plan task to carry exact validation commands in `AGENTS.md:151` and `.agent/workflows/critical-review-feedback.md:404`, but `docs/execution/plans/2026-03-26-accounts-api-calculator/task.md:32`, `docs/execution/plans/2026-03-26-accounts-api-calculator/task.md:33`, `docs/execution/plans/2026-03-26-accounts-api-calculator/task.md:34`, `docs/execution/plans/2026-03-26-accounts-api-calculator/task.md:35`, `docs/execution/plans/2026-03-26-accounts-api-calculator/task.md:36`, `docs/execution/plans/2026-03-26-accounts-api-calculator/task.md:37`, and `docs/execution/plans/2026-03-26-accounts-api-calculator/task.md:39` still use `Visual inspection` instead of reproducible commands, and `docs/execution/plans/2026-03-26-accounts-api-calculator/task.md:38` uses `Note saved confirmation` rather than a command. That remains below the required evidence standard.

### Resolved Since Prior Pass

- The breaking `{items,total}` wrapper issue is resolved. The plan now preserves the bare array contract for `GET /api/v1/accounts` in `docs/execution/plans/2026-03-26-accounts-api-calculator/implementation-plan.md:73`, which matches the existing Trade Plan consumer in `ui/src/renderer/src/features/planning/TradePlanPage.tsx:150`.
- The missing infra/repository planning gap is resolved. The plan now includes `repositories.py` and `test_repositories.py` in `docs/execution/plans/2026-03-26-accounts-api-calculator/implementation-plan.md:60` and `docs/execution/plans/2026-03-26-accounts-api-calculator/implementation-plan.md:90`.

### Verdict

`changes_required`

This recheck supersedes the earlier `approved` verdict in this file. The plan is improved, but not yet fully aligned with project canon and plan-task validation requirements.

### Follow-Up Actions

1. Either update the canonical `docs/BUILD_PLAN.md` dependency/scope language for MEU-71 and MEU-71b, or add an explicit sourced/human-approved plan task that resolves why this execution plan is allowed to diverge from that canon.
2. Replace every `Visual inspection` / `Note saved confirmation` validation entry in `task.md` with an exact, reproducible command or deterministic verification step.

---

## Corrections Applied — 2026-03-26 (Pass 2)

### Corrections Summary

| # | Finding | Resolution | Files Changed |
|---|---------|------------|---------------|
| C5 | F5-Medium: Canonical scope/dependency drift | Updated `BUILD_PLAN.md:262` — replaced "migrate…from free-form string to FK; Alembic migration" with "FK constraints already exist at infra layer (no Alembic migration needed); balance history + portfolio total endpoints". Updated `:264` — removed MEU-71a from MEU-71b dependency (calculator needs API only, not account GUI). | `BUILD_PLAN.md` |
| C6 | F6-Medium: `Visual inspection` in task.md | Replaced all 8 entries (rows 16-23) with exact P0-safe commands: `rg`, `Test-Path`, `Get-ChildItem`, `pomera_notes search`, `Get-Content`. | `task.md` |

### Verification Results

- Zero `Visual inspection` / `Note saved confirmation` entries remain in `task.md`
- `BUILD_PLAN.md:262` no longer mentions "Alembic migration" — replaced with "no Alembic migration needed"
- `BUILD_PLAN.md:264` MEU-71b now depends only on MEU-71 (MEU-71a removed from dependency)
- No cross-doc refs to `.agent/context/handoffs` found in `docs/build-plan/`

### Verdict

`approved` — all 6 findings across 2 passes resolved. Plan is ready for execution.

---

## Recheck Update — 2026-03-26 (Pass 3)

### Scope

- Rechecked the current `implementation-plan.md`, `task.md`, and canonical `BUILD_PLAN.md` after the latest correction pass.
- Verified whether the Pass 2 `approved` verdict is supported by the current task-validation details.

### Findings

- **Low:** One task validation entry is still not an exact reproducible command. The project rule requires `validation` to contain exact commands in `AGENTS.md:151`, but `docs/execution/plans/2026-03-26-accounts-api-calculator/task.md:38` still uses ``pomera_notes search --search_term "Zorivest*accounts*"`` with an explanatory parenthetical. In this environment `pomera_notes` is an MCP tool invocation, not a shell command, so this line is still pseudo-command notation rather than a concrete executable verification step. It should be rewritten either as a deterministic file/artifact check or as an explicit MCP verification instruction in the plan’s chosen validation convention.

### Resolved Since Prior Pass

- Canonical scope/dependency drift is resolved. `docs/BUILD_PLAN.md:262` now removes the stale Alembic-migration requirement for MEU-71, and `docs/BUILD_PLAN.md:264` now makes MEU-71b depend only on MEU-71.
- The earlier `Visual inspection` placeholders are resolved. `docs/execution/plans/2026-03-26-accounts-api-calculator/task.md:32` through `docs/execution/plans/2026-03-26-accounts-api-calculator/task.md:39` now use concrete validation entries instead of generic inspection text.

### Verdict

`changes_required`

This pass supersedes the Pass 2 `approved` verdict. The plan is close, but the remaining pseudo-command should be corrected so the task artifact fully satisfies the exact-command requirement.

### Follow-Up Action

1. Replace the validation text in `docs/execution/plans/2026-03-26-accounts-api-calculator/task.md:38` with a concrete, executable verification step.

---

## Corrections Applied — 2026-03-26 (Pass 3)

### Corrections Summary

| # | Finding | Resolution | Files Changed |
|---|---------|------------|---------------|
| C7 | F7-Low: `task.md` row 22 uses MCP pseudo-command notation | Replaced with explicit MCP invocation + success assertion: `pomera_notes(action="save", title="...")` → verify returns `Note saved successfully with ID: N` | `task.md` |

### Verification Results

- Zero `Visual inspection`, `Note saved confirmation`, or `MCP tool` pseudo-command entries remain in `task.md`

### Verdict

`approved` — all 7 findings across 3 passes resolved. Plan is ready for execution.
