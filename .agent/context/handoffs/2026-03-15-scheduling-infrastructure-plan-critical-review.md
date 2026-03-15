# Task Handoff Template

## Task

- **Date:** 2026-03-15
- **Task slug:** 2026-03-15-scheduling-infrastructure-plan-critical-review
- **Owner role:** reviewer
- **Scope:** Plan review mode for `docs/execution/plans/2026-03-15-scheduling-infrastructure/` (`implementation-plan.md`, `task.md`) plus cited canonical sources in `docs/build-plan/09-scheduling.md`, `AGENTS.md`, `.agent/workflows/critical-review-feedback.md`, current domain/infrastructure file state, and handoff registry state.

## Inputs

- User request: review [`docs/execution/plans/2026-03-15-scheduling-infrastructure/implementation-plan.md`], [`docs/execution/plans/2026-03-15-scheduling-infrastructure/task.md`], and the critical review workflow.
- Specs/docs referenced:
  - `SOUL.md`
  - `GEMINI.md`
  - `AGENTS.md`
  - `.agent/context/current-focus.md`
  - `.agent/context/known-issues.md`
  - `.agent/workflows/critical-review-feedback.md`
  - `docs/build-plan/09-scheduling.md`
  - `docs/BUILD_PLAN.md`
  - `.agent/context/meu-registry.md`
  - `packages/core/src/zorivest_core/domain/pipeline.py`
  - `packages/infrastructure/src/zorivest_infra/database/repositories.py`
  - `packages/infrastructure/src/zorivest_infra/database/unit_of_work.py`
- Constraints:
  - Findings-first review only. No product changes.
  - Canonical review continuity required at `.agent/context/handoffs/2026-03-15-scheduling-infrastructure-plan-critical-review.md`.

## Role Plan

1. orchestrator
2. tester
3. reviewer

## Coder Output

- Changed files: No product changes; review-only.
- Design notes / ADRs referenced: None.
- Commands run: None.
- Results: No code or docs corrected in this pass.

## Tester Output

- Commands run:
  - `rg -n "9\.2[a-j]|9\.3[a-f]|PipelineRunner|RefResolver|ConditionEvaluator|PolicyRepository|PipelineRunRepository|ReportRepository|FetchCacheRepository|AuditLogRepository|ReportVersionModel|ReportDeliveryModel|FetchCacheModel|AuditLogModel" docs/build-plan/09-scheduling.md`
  - `rg -n "MEU-81|MEU-82|MEU-83|MEU-84|P2\.5|Phase 9" docs/BUILD_PLAN.md .agent/context/meu-registry.md`
  - `rg --files packages/core/src/zorivest_core/services tests/unit packages/infrastructure/src/zorivest_infra/database .agent/context/handoffs | rg "(pipeline_runner|ref_resolver|condition_evaluator|test_pipeline_runner|test_ref_resolver|test_scheduling_models|test_scheduling_repos|scheduling_repositories|2026-03-15-scheduling-infrastructure-(plan|implementation)-critical-review|061-2026-03-15|062-2026-03-15|063-2026-03-15|064-2026-03-15)"`
  - `rg -n "class (PolicyModel|PipelineRunModel|PipelineStepModel|PipelineStateModel|ReportModel|ReportVersionModel|ReportDeliveryModel|FetchCacheModel|AuditLogModel|PolicyRepository|PipelineRunRepository|ReportRepository|FetchCacheRepository|AuditLogRepository|PipelineRunner|RefResolver|ConditionEvaluator)" packages tests`
  - `Get-ChildItem .agent/context/handoffs | Sort-Object Name | Select-Object -Last 15 | ForEach-Object { $_.Name }`
  - `Test-Path .agent/context/handoffs/2026-03-15-scheduling-infrastructure-plan-critical-review.md`
  - Line-numbered `Get-Content` reads for:
    - `docs/execution/plans/2026-03-15-scheduling-infrastructure/implementation-plan.md`
    - `docs/execution/plans/2026-03-15-scheduling-infrastructure/task.md`
    - `docs/build-plan/09-scheduling.md`
    - `packages/core/src/zorivest_core/domain/pipeline.py`
    - `packages/infrastructure/src/zorivest_infra/database/repositories.py`
    - `packages/infrastructure/src/zorivest_infra/database/unit_of_work.py`
    - `AGENTS.md`
    - `.agent/workflows/critical-review-feedback.md`
- Pass/fail matrix:
  - Not-started confirmation: PASS. No correlated MEU handoffs or implementation files exist yet for this project.
  - Plan/task alignment: FAIL. Handoff naming is provisional in `implementation-plan.md` but hard-coded in `task.md`.
  - Task contract completeness: FAIL. `task.md` is checklist-only and does not use required task fields.
  - Source contract coherence: FAIL. PipelineRunner input/repository contracts are still under-specified or contradictory.
  - Trigger verification readiness: FAIL. Trigger work is in scope but no migration deliverable or trigger-proof validation exists.
- Repro failures:
  - `rg --files ... | rg "(pipeline_runner|ref_resolver|condition_evaluator|...)"` returned no matches for implementation artifacts or MEU handoffs, confirming plan-review mode.
  - `rg -n "class (...)" packages tests` returned no scheduling infrastructure classes, confirming work has not started.
- Coverage/test gaps:
  - No explicit validation exists for Alembic trigger creation or trigger runtime behavior.
  - No validation exists to prove the chosen repo interface shape matches `PipelineRunner` expectations.
- Evidence bundle location:
  - This handoff plus the cited file/line references.
- FAIL_TO_PASS / PASS_TO_PASS result:
  - Not applicable; review-only.
- Mutation score:
  - Not applicable.
- Contract verification status:
  - Failed. Plan requires corrections before implementation begins.

## Reviewer Output

- Findings by severity:
  - **High:** `task.md` does not satisfy the required plan-task contract. Project rules require every plan task to include `task`, `owner_role`, `deliverable`, `validation`, and `status` in canonical form ([AGENTS.md](P:\zorivest\AGENTS.md#L64), `.agent/workflows/critical-review-feedback.md:180-199`). The current task artifact is only a checkbox list with no owner-role assignment, deliverable field, or standalone validation/status columns ([task.md](P:\zorivest\docs\execution\plans\2026-03-15-scheduling-infrastructure\task.md#L8)). This fails PR-3 before execution starts.
  - **High:** `PipelineRunner`'s core input contract is unresolved. The source spec constructs `StepContext(policy_id=policy.id)` inside `PipelineRunner.run()` ([09-scheduling.md](P:\zorivest\docs\build-plan\09-scheduling.md#L855), [09-scheduling.md](P:\zorivest\docs\build-plan\09-scheduling.md#L881)), but the actual `PolicyDocument` model in the codebase has no `id` field ([pipeline.py](P:\zorivest\packages\core\src\zorivest_core\domain\pipeline.py#L131)). The plan repeats the `PolicyDocument`-based runner contract without resolving where the persisted policy UUID comes from ([implementation-plan.md](P:\zorivest\docs\execution\plans\2026-03-15-scheduling-infrastructure\implementation-plan.md#L173)). As written, implementation would need to invent behavior or silently change the runtime contract.
  - **High:** The repo interface contract is contradictory across MEU-82 and MEU-83. The authoritative Phase 9 spec sketches scheduling repositories as `async def` methods ([09-scheduling.md](P:\zorivest\docs\build-plan\09-scheduling.md#L747)), and `PipelineRunner` awaits those repo calls ([09-scheduling.md](P:\zorivest\docs\build-plan\09-scheduling.md#L889), [09-scheduling.md](P:\zorivest\docs\build-plan\09-scheduling.md#L1269)). The existing infrastructure/UoW pattern is synchronous `Session`-backed repositories and a sync context manager ([repositories.py](P:\zorivest\packages\infrastructure\src\zorivest_infra\database\repositories.py#L137), [unit_of_work.py](P:\zorivest\packages\infrastructure\src\zorivest_infra\database\unit_of_work.py#L59)). The plan only says to follow the existing Session-based pattern ([implementation-plan.md](P:\zorivest\docs\execution\plans\2026-03-15-scheduling-infrastructure\implementation-plan.md#L119), [implementation-plan.md](P:\zorivest\docs\execution\plans\2026-03-15-scheduling-infrastructure\implementation-plan.md#L168)) and never resolves whether scheduling repos must remain sync, become async, or be wrapped. That is a cross-MEU contract hole with direct implementation risk.
  - **High:** SQL trigger work is declared in scope, but the plan neither assigns a migration deliverable nor defines trigger-proof validation. The source spec explicitly says the report-versioning and audit append-only triggers run via Alembic migration ([09-scheduling.md](P:\zorivest\docs\build-plan\09-scheduling.md#L683), [09-scheduling.md](P:\zorivest\docs\build-plan\09-scheduling.md#L721)). The plan lists triggers as in scope ([implementation-plan.md](P:\zorivest\docs\execution\plans\2026-03-15-scheduling-infrastructure\implementation-plan.md#L10)), but MEU-81 files only cover `models.py` plus a unit test file ([implementation-plan.md](P:\zorivest\docs\execution\plans\2026-03-15-scheduling-infrastructure\implementation-plan.md#L49)), and the verification section contains no migration or trigger-behavior command ([implementation-plan.md](P:\zorivest\docs\execution\plans\2026-03-15-scheduling-infrastructure\implementation-plan.md#L212)). That would allow the project to claim completion without proving the trigger contract exists at all.
  - **Medium:** Handoff naming is internally inconsistent. `implementation-plan.md` says sequence numbers are only estimates to be finalized at execution time ([implementation-plan.md](P:\zorivest\docs\execution\plans\2026-03-15-scheduling-infrastructure\implementation-plan.md#L246)), but `task.md` hard-codes those same filenames as required outputs ([task.md](P:\zorivest\docs\execution\plans\2026-03-15-scheduling-infrastructure\task.md#L13)). That creates avoidable plan/task drift on the first renumbering or sequencing change.
- Open questions:
  - Should scheduling repositories remain synchronous to match the current infra/UoW pattern, or is Phase 9 intentionally introducing async repositories?
  - Should `PipelineRunner.run()` accept a persisted policy record / policy ID separately from `PolicyDocument`, or should `PolicyDocument` itself be extended with persistence identity?
  - Which Alembic migration file is responsible for the trigger DDL, and what command/test proves both trigger sets exist and behave correctly on SQLite/SQLCipher?
- Verdict:
  - `changes_required`
- Residual risk:
  - Starting implementation from this plan would force undocumented product decisions in core execution paths, especially around persistence identity, repository calling convention, and trigger installation. Those are architecture-shaping decisions, not safe execution-time improvisations.
- Anti-deferral scan result:
  - No evidence of started implementation was found, so correction can happen cleanly in planning. The required next step is `/planning-corrections`, not partial execution.

## Guardrail Output (If Required)

- Safety checks: Not required for docs-only review.
- Blocking risks: None beyond the review findings above.
- Verdict: Not applicable.

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status: `changes_required`
- Next steps:
  - Rewrite `task.md` into the required canonical task table/field structure.
  - Resolve and document the `PipelineRunner` persistence identity contract.
  - Resolve and document the scheduling repo sync/async contract across MEU-82 and MEU-83.
  - Add the missing trigger migration deliverable plus trigger-specific validation commands before implementation starts.

---

## Corrections Applied — 2026-03-15

### Findings Addressed

| # | Severity | Finding | Resolution |
|---|----------|---------|------------|
| F1 | High | `task.md` missing canonical fields | Fully rewritten with task tables: owner, deliverable, validation, status columns |
| F2 | High | `PolicyDocument` has no `.id` — `PipelineRunner` contract hole | Added design decision: `policy_id: str` passed as separate arg; `PolicyDocument` stays pure authoring model |
| F3 | High | Sync/async repo contract unresolved | Added `[!IMPORTANT]` callout: sync repos + `asyncio.to_thread()` bridge in PipelineRunner |
| F4 | High | Trigger migration deliverable missing | Added trigger DDL via `event.listen` deliverable, AC-11/AC-12, `uv run pytest -k trigger` validation |
| F5 | Medium | Hard-coded handoff seq numbers in task.md | Replaced with `<seq>` placeholder + runtime resolution note |

### Verification

```bash
# F1: task.md has canonical fields
rg -c "owner|deliverable|validation|Status" task.md  # → 5

# F2: policy_id design note present
rg -n "policy_id.*separate.*arg" implementation-plan.md  # → L176

# F3: sync/async decision documented
rg -n "Sync/Async Decision" implementation-plan.md  # → L129

# F4: trigger deliverable + ACs
rg -n "AC-11|AC-12|event.listen" implementation-plan.md  # → multiple hits

# F5: no hard-coded seq numbers
rg -n "061-|062-|063-|064-" task.md implementation-plan.md  # → 0 matches
```

All 5 checks passed.

### Updated Verdict

- **Status**: `corrections_applied` — ready for recheck
- **Open questions resolved**:
  1. Repos stay sync (existing infra pattern); PipelineRunner bridges via `asyncio.to_thread()`
  2. `policy_id` supplied as separate arg by caller (API/scheduler/MCP), not from `PolicyDocument`
  3. Triggers installed via `event.listen(Base.metadata, 'after_create')` — no Alembic needed (project uses `create_all()`); proven by AC-11, AC-12 trigger tests
