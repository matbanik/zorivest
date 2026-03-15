# Scheduling Infrastructure Implementation Critical Review

## 2026-03-15 Review Pass 1

## Task

- **Date:** 2026-03-15
- **Task slug:** scheduling-infrastructure-implementation-critical-review
- **Owner role:** reviewer
- **Scope:** implementation review of the user-supplied handoff set for `docs/execution/plans/2026-03-15-scheduling-infrastructure/`

## Inputs

- User request:
  - Review `.agent/context/handoffs/066-2026-03-15-scheduling-models-bp09s9.2a-i.md`
  - Review `.agent/context/handoffs/067-2026-03-15-scheduling-repos-bp09s9.2j.md`
  - Review `.agent/context/handoffs/068-2026-03-15-pipeline-runner-bp09s9.3a.md`
  - Review `.agent/context/handoffs/069-2026-03-15-ref-resolver-bp09s9.3b+9.3c.md`
- Specs/docs referenced:
  - `docs/execution/plans/2026-03-15-scheduling-infrastructure/implementation-plan.md`
  - `docs/execution/plans/2026-03-15-scheduling-infrastructure/task.md`
  - `docs/build-plan/09-scheduling.md`
  - `docs/BUILD_PLAN.md`
  - `.agent/context/meu-registry.md`
- Constraints:
  - Review-only workflow. No product fixes in this pass.
  - Explicit handoff paths were supplied, then expanded/correlated to the shared plan folder via same-date slug + `implementation-plan.md` `Handoff Files`.
  - Untracked files were validated via direct file reads and commands because `git diff` does not cover them.

## Role Plan

1. orchestrator
2. tester
3. reviewer
- Optional roles: researcher, guardrail

## Coder Output

- Changed files:
  - No product changes; review-only.
- Design notes / ADRs referenced:
  - None
- Commands run:
  - None
- Results:
  - None

## Tester Output

- Commands run:
  - `git status --short`
  - `git diff -- packages/core/src/zorivest_core/services/pipeline_runner.py packages/core/src/zorivest_core/services/ref_resolver.py packages/core/src/zorivest_core/services/condition_evaluator.py packages/infrastructure/src/zorivest_infra/database/models.py packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py packages/infrastructure/src/zorivest_infra/database/unit_of_work.py tests/unit/test_pipeline_runner.py tests/unit/test_ref_resolver.py tests/unit/test_scheduling_models.py tests/unit/test_scheduling_repos.py tests/unit/test_models.py docs/BUILD_PLAN.md .agent/context/meu-registry.md docs/execution/plans/2026-03-15-scheduling-infrastructure/implementation-plan.md docs/execution/plans/2026-03-15-scheduling-infrastructure/task.md`
  - `uv run pytest tests/unit/test_scheduling_models.py -q`
  - `uv run pytest tests/unit/test_scheduling_repos.py -q`
  - `uv run pytest tests/unit/test_ref_resolver.py -q`
  - `uv run pytest tests/unit/test_pipeline_runner.py -q`
  - `uv run pytest tests/unit/test_models.py -q`
  - `uv run pytest tests/ --tb=no -q`
  - `uv run ruff check packages/core/src/zorivest_core/services/pipeline_runner.py packages/core/src/zorivest_core/services/ref_resolver.py packages/core/src/zorivest_core/services/condition_evaluator.py packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py packages/infrastructure/src/zorivest_infra/database/models.py packages/infrastructure/src/zorivest_infra/database/unit_of_work.py tests/unit/test_pipeline_runner.py tests/unit/test_ref_resolver.py tests/unit/test_scheduling_models.py tests/unit/test_scheduling_repos.py tests/unit/test_models.py`
  - `uv run pyright packages/core/src/zorivest_core/services/pipeline_runner.py packages/core/src/zorivest_core/services/ref_resolver.py packages/core/src/zorivest_core/services/condition_evaluator.py packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py packages/infrastructure/src/zorivest_infra/database/models.py packages/infrastructure/src/zorivest_infra/database/unit_of_work.py`
  - `uv run python tools/validate_codebase.py --scope meu`
  - `rg -n "recover_zombies|_create_run_record|_persist_step|_finalize_run|_load_prior_output|resume_from|CancelledError|timeout\(|dry_run|skip_if" packages/core/src/zorivest_core/services/pipeline_runner.py tests/unit/test_pipeline_runner.py docs/build-plan/09-scheduling.md`
  - `rg -n "list_recent|find_zombies|update_status|get_versions|append|list_all|enabled_only" packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py tests/unit/test_scheduling_repos.py docs/build-plan/09-scheduling.md`
  - `rg -n "@pytest\.mark\.(skip|xfail)|skip\(|xfail\(" tests/unit/test_pipeline_runner.py tests/unit/test_ref_resolver.py tests/unit/test_scheduling_models.py tests/unit/test_scheduling_repos.py`
- Pass/fail matrix:
  - `pytest tests/unit/test_scheduling_models.py -q`: PASS (`18 passed`)
  - `pytest tests/unit/test_scheduling_repos.py -q`: PASS (`17 passed`)
  - `pytest tests/unit/test_ref_resolver.py -q`: PASS (`25 passed`)
  - `pytest tests/unit/test_pipeline_runner.py -q`: PASS (`11 passed`)
  - `pytest tests/unit/test_models.py -q`: PASS (`11 passed`)
  - `pytest tests/ --tb=no -q`: PASS (`1303 passed, 1 skipped`)
  - `ruff check ...`: FAIL
    - `packages/core/src/zorivest_core/services/pipeline_runner.py:80` unused `content_hash`
    - `tests/unit/test_ref_resolver.py:224` unused `ctx`
    - `tests/unit/test_scheduling_repos.py:101` unused `pid1`
  - `pyright ...`: FAIL
    - `packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py:84,146,148,150,151,232,233,234,235,236,237`
  - `python tools/validate_codebase.py --scope meu`: FAIL (`pyright` + `ruff` blocking)
- Repro failures:
  - Quality gate is not green despite handoff status `ready_for_review`.
- Coverage/test gaps:
  - No `tests/unit/test_pipeline_runner.py` coverage for `resume_from`, timeout handling, cancellation handling, persistence hooks, or `recover_zombies`.
  - No `PipelineRunRepository.list_recent` test coverage; the only `list_recent` assertion is `AuditLogRepository` at `tests/unit/test_scheduling_repos.py:301`.
- Evidence bundle location:
  - This handoff file.
- FAIL_TO_PASS / PASS_TO_PASS result:
  - PASS_TO_PASS reproduced for current tests only.
  - FAIL_TO_PASS evidence was not re-created in this review.
- Mutation score:
  - Not run.
- Contract verification status:
  - FAILED. MEU-82 and MEU-83 do not fully match the correlated plan/build-plan contract.

## Reviewer Output

- Findings by severity:
  - **High** — `PipelineRunner` was handed off as ready even though the correlated plan/spec requires persistence hooks, resume hydration, and zombie recovery that are not implemented. The plan requires `resume_from` to load prior outputs and requires `recover_zombies()` plus persistence helpers at `docs/execution/plans/2026-03-15-scheduling-infrastructure/implementation-plan.md:169`, `docs/execution/plans/2026-03-15-scheduling-infrastructure/implementation-plan.md:193`, `docs/execution/plans/2026-03-15-scheduling-infrastructure/implementation-plan.md:196`, `docs/execution/plans/2026-03-15-scheduling-infrastructure/implementation-plan.md:201`. The build-plan code contract likewise requires `_create_run_record`, `_load_prior_output`, `_persist_step`, `_finalize_run`, and `recover_zombies()` at `docs/build-plan/09-scheduling.md:889`, `docs/build-plan/09-scheduling.md:903`, `docs/build-plan/09-scheduling.md:932`, `docs/build-plan/09-scheduling.md:1017`, `docs/build-plan/09-scheduling.md:1021`, `docs/build-plan/09-scheduling.md:1025`, `docs/build-plan/09-scheduling.md:1029`, `docs/build-plan/09-scheduling.md:1264`. The actual file only exposes `run()` and `_execute_step()` at `packages/core/src/zorivest_core/services/pipeline_runner.py:55` and `packages/core/src/zorivest_core/services/pipeline_runner.py:159`, and the handoff explicitly documents the deferral at `.agent/context/handoffs/068-2026-03-15-pipeline-runner-bp09s9.3a.md:60`. This is a silent scope cut, not an approved follow-up.
  - **High** — `PipelineRunner` test coverage does not exercise the omitted contract, so the handoff gives false confidence. The test file contains only the test classes listed at `tests/unit/test_pipeline_runner.py:137`, `tests/unit/test_pipeline_runner.py:160`, `tests/unit/test_pipeline_runner.py:185`, `tests/unit/test_pipeline_runner.py:208`, `tests/unit/test_pipeline_runner.py:245`, `tests/unit/test_pipeline_runner.py:267`, `tests/unit/test_pipeline_runner.py:320`, `tests/unit/test_pipeline_runner.py:347`, and `tests/unit/test_pipeline_runner.py:366`; grep found no `resume_from`, `recover_zombies`, `CancelledError`, or timeout-specific tests. That leaves the required behaviors from `docs/execution/plans/2026-03-15-scheduling-infrastructure/implementation-plan.md:193` and `docs/execution/plans/2026-03-15-scheduling-infrastructure/implementation-plan.md:196` completely unverified.
  - **High** — `PipelineRunRepository.list_recent()` is required by the correlated plan/spec but missing from the implementation and tests. The plan marks that API as resolved at `docs/execution/plans/2026-03-15-scheduling-infrastructure/implementation-plan.md:120`, and the build plan defines it at `docs/build-plan/09-scheduling.md:770`. The implementation defines only `create`, `get_by_id`, `list_by_policy`, `update_status`, and `find_zombies` in `packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py:92`, `packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py:98`, `packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py:125`, `packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py:128`, `packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py:139`, and `packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py:153`. The handoff narrows AC-2/AC-3 accordingly at `.agent/context/handoffs/067-2026-03-15-scheduling-repos-bp09s9.2j.md:29`, `.agent/context/handoffs/067-2026-03-15-scheduling-repos-bp09s9.2j.md:30`, and the test file has no pipeline-run `list_recent` coverage.
  - **High** — The claimed green verification evidence is false. `uv run python tools/validate_codebase.py --scope meu` fails in the current tree, and both blocking subchecks fail: `ruff` reports unused variables at `packages/core/src/zorivest_core/services/pipeline_runner.py:80`, `tests/unit/test_ref_resolver.py:224`, and `tests/unit/test_scheduling_repos.py:101`; `pyright` reports attribute-assignment errors in `packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py:84`, `packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py:146`, `packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py:148`, `packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py:150`, `packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py:151`, `packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py:232`, `packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py:233`, `packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py:234`, `packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py:235`, `packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py:236`, and `packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py:237`. Because the task still leaves the MEU gate unfinished at `docs/execution/plans/2026-03-15-scheduling-infrastructure/task.md:46`, these handoffs should not be treated as ready for approval.
  - **Medium** — Required project-state deliverables were not completed, so repository state still contradicts the handoff set. The task still marks handoff creation, registry updates, `BUILD_PLAN` updates, reflection, metrics, session save, and commit-message prep as `not_started` at `docs/execution/plans/2026-03-15-scheduling-infrastructure/task.md:14`, `docs/execution/plans/2026-03-15-scheduling-infrastructure/task.md:23`, `docs/execution/plans/2026-03-15-scheduling-infrastructure/task.md:32`, `docs/execution/plans/2026-03-15-scheduling-infrastructure/task.md:40`, `docs/execution/plans/2026-03-15-scheduling-infrastructure/task.md:47`, `docs/execution/plans/2026-03-15-scheduling-infrastructure/task.md:48`, `docs/execution/plans/2026-03-15-scheduling-infrastructure/task.md:51`, `docs/execution/plans/2026-03-15-scheduling-infrastructure/task.md:52`, `docs/execution/plans/2026-03-15-scheduling-infrastructure/task.md:53`, and `docs/execution/plans/2026-03-15-scheduling-infrastructure/task.md:54`. The canonical status docs were not updated either: `docs/BUILD_PLAN.md:276`, `docs/BUILD_PLAN.md:277`, `docs/BUILD_PLAN.md:278`, `docs/BUILD_PLAN.md:279`, and `docs/BUILD_PLAN.md:471` still show the Phase 9 work as incomplete, and `.agent/context/meu-registry.md:115` through `.agent/context/meu-registry.md:123` still stop at MEU-80. `docs/execution/reflections/2026-03-15-scheduling-infra-reflection.md` and `docs/execution/plans/2026-03-15-scheduling-infrastructure/commit-messages.md` do not exist, and `rg -n "scheduling-infrastructure" docs/execution/metrics.md` returns no matches.
  - **Low** — Handoff auditability is stale in a few places. The plan/task still point to `.agent/context/handoffs/<seq>-2026-03-15-scheduling-models-bp09s9.2.md` and `.agent/context/handoffs/<seq>-2026-03-15-pipeline-runner-bp09s9.3a+9.3e.md` at `docs/execution/plans/2026-03-15-scheduling-infrastructure/task.md:14`, `docs/execution/plans/2026-03-15-scheduling-infrastructure/task.md:40`, `docs/execution/plans/2026-03-15-scheduling-infrastructure/implementation-plan.md:273`, and `docs/execution/plans/2026-03-15-scheduling-infrastructure/implementation-plan.md:276`, but the actual handoffs are `066-2026-03-15-scheduling-models-bp09s9.2a-i.md` and `068-2026-03-15-pipeline-runner-bp09s9.3a.md`. Test totals are also stale in two handoffs: `.agent/context/handoffs/067-2026-03-15-scheduling-repos-bp09s9.2j.md:11`, `.agent/context/handoffs/067-2026-03-15-scheduling-repos-bp09s9.2j.md:66`, `.agent/context/handoffs/069-2026-03-15-ref-resolver-bp09s9.3b+9.3c.md:11`, and `.agent/context/handoffs/069-2026-03-15-ref-resolver-bp09s9.3b+9.3c.md:74` claim `16` and `24` tests, while the current files run `17` and `25`.
- Open questions:
  - None. The blocking items are determinable from local spec, file state, and reproduced commands.
- Verdict:
  - `changes_required`
- Residual risk:
  - Phase 9 downstream work would be built on an incomplete execution engine and stale project-state docs if this handoff set were approved as-is. The main behavioral risk is around run persistence, resume semantics, and zombie recovery, which are foundational for scheduler/service integration.
- Anti-deferral scan result:
  - Direct placeholder scan on the touched implementation paths passed, but the MEU-83 handoff itself documents a deferred contract (`_create_run_record`, `_persist_step`, `_finalize_run`, `_load_prior_output`) that is not backed by an approved follow-up artifact.
- Adversarial Verification Checklist:
  - `AV-1` Failing-then-passing proof: PASS for current test files only; FAIL for omitted MEU-83 contract areas because no red/green evidence exists for resume/persistence/zombie recovery.
  - `AV-2` No bypass hacks: PASS in reviewed tests.
  - `AV-3` Changed paths exercised by assertions: PARTIAL. Core happy paths are asserted; omitted spec paths are not exercised.
  - `AV-4` No skipped/xfail masking: PASS for the touched test files.
  - `AV-5` No unresolved placeholders: PASS for code placeholders; FAIL for documented feature deferral in handoff 068.
  - `AV-6` Source-backed criteria: FAIL for the narrowed MEU-82/83 scope because the omissions are not justified by `Spec`, `Local Canon`, `Research-backed`, or `Human-approved` approval.

## Guardrail Output (If Required)

- Safety checks:
  - Not invoked; review-only workflow.
- Blocking risks:
  - None beyond reviewer findings.
- Verdict:
  - Not applicable.

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status:
  - `changes_required`
- Next steps:
  - Route this project through `/planning-corrections`.
  - Restore MEU-83 to the plan/build-plan contract or explicitly re-plan/split the deferred persistence + zombie-recovery work with source-backed acceptance criteria.
  - Add the missing `PipelineRunRepository.list_recent()` contract and tests.
  - Make the MEU gate actually pass (`ruff`, `pyright`, `validate_codebase.py --scope meu`).
  - Update `task.md`, `docs/BUILD_PLAN.md`, `.agent/context/meu-registry.md`, and the missing reflection/metrics/session artifacts before another approval attempt.

## 2026-03-15 Recheck Pass 2

### Scope Reviewed

- Same correlated implementation target:
  - `docs/execution/plans/2026-03-15-scheduling-infrastructure/`
  - `.agent/context/handoffs/066-2026-03-15-scheduling-models-bp09s9.2a-i.md`
  - `.agent/context/handoffs/067-2026-03-15-scheduling-repos-bp09s9.2j.md`
  - `.agent/context/handoffs/068-2026-03-15-pipeline-runner-bp09s9.3a.md`
  - `.agent/context/handoffs/069-2026-03-15-ref-resolver-bp09s9.3b+9.3c.md`

### Commands Executed

- `uv run pytest tests/unit/test_pipeline_runner.py -q`
- `uv run pytest tests/unit/test_scheduling_repos.py -q`
- `uv run ruff check packages/core/src/zorivest_core/services/pipeline_runner.py packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py tests/unit/test_pipeline_runner.py tests/unit/test_scheduling_repos.py tests/unit/test_ref_resolver.py`
- `uv run pyright packages/core/src/zorivest_core/services/pipeline_runner.py packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py`
- `uv run python tools/validate_codebase.py --scope meu`
- `uv run pytest tests/ --tb=no -q`
- Inline repro harness with a real in-memory `SqlAlchemyUnitOfWork` and seeded `PolicyModel` to exercise `PipelineRunner.run(...)` persistence path
- `rg -n "pipeline_run_id|_persist_step|_load_prior_output|recover_zombies|list_recent\(|to_thread|not_started|MEU-81|MEU-82|MEU-83|MEU-84" ...`

### Recheck Results

- `pytest tests/unit/test_pipeline_runner.py -q`: PASS (`15 passed, 1 warning`)
- `pytest tests/unit/test_scheduling_repos.py -q`: PASS (`18 passed`)
- `ruff check ...`: PASS
- `pyright ...`: PASS
- `python tools/validate_codebase.py --scope meu`: PASS
- `pytest tests/ --tb=no -q`: PASS (`1308 passed, 1 skipped, 1 warning`)
- Real-UoW repro harness: FAIL
  - `TypeError: 'pipeline_run_id' is an invalid keyword argument for PipelineStepModel`

### Findings by Severity

- **High** — The newly added persistence path in `PipelineRunner` is still broken under a real UoW. `PipelineStepModel` defines the FK column as `run_id` at `packages/infrastructure/src/zorivest_infra/database/models.py:438` and `packages/infrastructure/src/zorivest_infra/database/models.py:444`, but the runner persists and queries using `pipeline_run_id` at `packages/core/src/zorivest_core/services/pipeline_runner.py:318`, `packages/core/src/zorivest_core/services/pipeline_runner.py:358`, and `packages/core/src/zorivest_core/services/pipeline_runner.py:391`. I reproduced this with an inline in-memory SQLite harness using a real `SqlAlchemyUnitOfWork`; `runner.run(...)` fails with `TypeError: 'pipeline_run_id' is an invalid keyword argument for PipelineStepModel` before a persisted run can complete. This means the first-pass contract gap is no longer “missing implementation,” but it is still a blocking runtime defect.
- **Medium** — The new tests still do not exercise the live persistence path that was added. Every `PipelineRunner` test still constructs the runner through `_runner()` with `uow=None` at `tests/unit/test_pipeline_runner.py:125` and `tests/unit/test_pipeline_runner.py:127`, including the newly added `TestResumeFrom`, `TestTimeoutHandling`, `TestCancellationHandling`, and `TestZombieRecovery` cases at `tests/unit/test_pipeline_runner.py:387`, `tests/unit/test_pipeline_runner.py:431`, `tests/unit/test_pipeline_runner.py:452`, and `tests/unit/test_pipeline_runner.py:474`. That is why the broken `pipeline_run_id` path escaped despite the green gate.
- **Medium** — The sync/async bridge still does not match the correlated plan contract. The plan explicitly says persistence calls are wrapped via `asyncio.to_thread()` at `docs/execution/plans/2026-03-15-scheduling-infrastructure/implementation-plan.md:129`, `docs/execution/plans/2026-03-15-scheduling-infrastructure/implementation-plan.md:177`, and `docs/execution/plans/2026-03-15-scheduling-infrastructure/implementation-plan.md:183`, but the persistence helpers at `packages/core/src/zorivest_core/services/pipeline_runner.py:281`, `packages/core/src/zorivest_core/services/pipeline_runner.py:304`, `packages/core/src/zorivest_core/services/pipeline_runner.py:332`, and `packages/core/src/zorivest_core/services/pipeline_runner.py:347` call sync UoW/session work directly from the async runner.
- **Medium** — Project-state artifacts are still incomplete. `task.md` still marks the MEU gate and all post-MEU documentation artifacts as `not_started` at `docs/execution/plans/2026-03-15-scheduling-infrastructure/task.md:46`, `docs/execution/plans/2026-03-15-scheduling-infrastructure/task.md:47`, `docs/execution/plans/2026-03-15-scheduling-infrastructure/task.md:48`, `docs/execution/plans/2026-03-15-scheduling-infrastructure/task.md:51`, `docs/execution/plans/2026-03-15-scheduling-infrastructure/task.md:52`, `docs/execution/plans/2026-03-15-scheduling-infrastructure/task.md:53`, and `docs/execution/plans/2026-03-15-scheduling-infrastructure/task.md:54`, even though the MEU gate now passes. `docs/BUILD_PLAN.md:276` through `docs/BUILD_PLAN.md:279` still show MEU-81..84 as incomplete, `.agent/context/meu-registry.md` still stops at MEU-80, and the reflection / metrics / commit-message artifacts are still absent.

### Resolved Since Pass 1

- `PipelineRunner` now includes `_create_run_record`, `_persist_step`, `_finalize_run`, `_load_prior_output`, and `recover_zombies()`.
- `PipelineRunRepository.list_recent()` now exists and has a unit test at `tests/unit/test_scheduling_repos.py:206`.
- `ruff`, `pyright`, the MEU gate, and full regression now pass.

### Verdict

- `changes_required`

### Residual Risk

- The project is much closer to approvable than in Pass 1, but the runtime persistence path is still not trustworthy. Any caller that supplies a real UoW can trigger a hard failure in step persistence, and the current test suite would not catch similar breakage in resume or zombie-recovery DB access.

## 2026-03-15 Recheck Pass 3

### Scope Reviewed

- Same correlated implementation target:
  - `docs/execution/plans/2026-03-15-scheduling-infrastructure/`
  - `.agent/context/handoffs/066-2026-03-15-scheduling-models-bp09s9.2a-i.md`
  - `.agent/context/handoffs/067-2026-03-15-scheduling-repos-bp09s9.2j.md`
  - `.agent/context/handoffs/068-2026-03-15-pipeline-runner-bp09s9.3a.md`
  - `.agent/context/handoffs/069-2026-03-15-ref-resolver-bp09s9.3b+9.3c.md`

### Commands Executed

- `uv run python tools/validate_codebase.py --scope meu`
- `uv run pytest tests/ --tb=no -q`
- `Get-Content -Raw packages/core/src/zorivest_core/services/pipeline_runner.py`
- Inline repro harness with a real in-memory `SqlAlchemyUnitOfWork`, seeded `PolicyModel`, and patched step registry to run `PipelineRunner.run(...)` end-to-end and query persisted `PipelineStepModel` rows
- `rg -n "tests_added:|tests_passing:|AC-9|AC-10|AC-11|AC-12|AC-13|16/16|1303/1303|11 tests" .agent/context/handoffs/068-2026-03-15-pipeline-runner-bp09s9.3a.md`
- `rg -n "tests_added:|tests_passing:|AC-2: PipelineRunRepository|list_recent|18/18|1303/1303|16 tests|TestPipelineRunRepository" .agent/context/handoffs/067-2026-03-15-scheduling-repos-bp09s9.2j.md`
- `rg -n "MEU gate|Update meu-registry|Update BUILD_PLAN|Create reflection|Update metrics|Save session state|Prepare commit messages|not_started" docs/execution/plans/2026-03-15-scheduling-infrastructure/task.md`
- `rg -n "MEU-81|MEU-82|MEU-83|MEU-84|P2.5" docs/BUILD_PLAN.md .agent/context/meu-registry.md`
- `rg -n "to_thread|Repo bridge|Sync/Async Decision" docs/execution/plans/2026-03-15-scheduling-infrastructure/implementation-plan.md`

### Recheck Results

- `uv run python tools/validate_codebase.py --scope meu`: PASS
- `uv run pytest tests/ --tb=no -q`: PASS (`1309 passed, 1 skipped, 1 warning`)
- Real-UoW repro harness: PASS
  - `PipelineRunner.run(...)` completed successfully
  - one persisted `PipelineStepModel` row was written with `run_id` matching the pipeline run

### Findings by Severity

- **Medium** — Completion-state artifacts are still out of sync with the actual verified state, so the project cannot yet be treated as complete. The task file still marks the MEU gate and every remaining post-MEU artifact as `not_started` at `docs/execution/plans/2026-03-15-scheduling-infrastructure/task.md:46`, `docs/execution/plans/2026-03-15-scheduling-infrastructure/task.md:47`, `docs/execution/plans/2026-03-15-scheduling-infrastructure/task.md:48`, `docs/execution/plans/2026-03-15-scheduling-infrastructure/task.md:51`, `docs/execution/plans/2026-03-15-scheduling-infrastructure/task.md:52`, `docs/execution/plans/2026-03-15-scheduling-infrastructure/task.md:53`, and `docs/execution/plans/2026-03-15-scheduling-infrastructure/task.md:54`, even though the MEU gate now passes. The status docs are still stale too: `docs/BUILD_PLAN.md:276` through `docs/BUILD_PLAN.md:279` still show MEU-81..84 unchecked, `docs/BUILD_PLAN.md:471` still counts only 4 completed P2.5 items, and `.agent/context/meu-registry.md:115` still stops at the domain-foundation subset with no MEU-81..84 entries.
- **Medium** — The implementation still deviates from the correlated plan’s explicit sync/async bridge contract. The plan says the async runner must bridge sync persistence via `asyncio.to_thread()` at `docs/execution/plans/2026-03-15-scheduling-infrastructure/implementation-plan.md:129`, `docs/execution/plans/2026-03-15-scheduling-infrastructure/implementation-plan.md:177`, and `docs/execution/plans/2026-03-15-scheduling-infrastructure/implementation-plan.md:183`, but the persistence helpers in `packages/core/src/zorivest_core/services/pipeline_runner.py` still perform direct sync UoW/session calls. The current code works in the reviewed in-memory path, but it still does not match the documented contract used to justify the design.
- **Low** — Two handoff artifacts remain stale enough to reduce auditability. The pipeline-runner handoff now claims `16` tests in front matter and command output at `.agent/context/handoffs/068-2026-03-15-pipeline-runner-bp09s9.3a.md:10`, `.agent/context/handoffs/068-2026-03-15-pipeline-runner-bp09s9.3a.md:11`, and `.agent/context/handoffs/068-2026-03-15-pipeline-runner-bp09s9.3a.md:74`, but its FIC/test mapping still stops at AC-10 and its changed-files / FAIL_TO_PASS text still says `11 tests` at `.agent/context/handoffs/068-2026-03-15-pipeline-runner-bp09s9.3a.md:68` and `.agent/context/handoffs/068-2026-03-15-pipeline-runner-bp09s9.3a.md:81`. The scheduling-repos handoff similarly still omits `list_recent()` from the acceptance criteria and test mapping at `.agent/context/handoffs/067-2026-03-15-scheduling-repos-bp09s9.2j.md:29` and `.agent/context/handoffs/067-2026-03-15-scheduling-repos-bp09s9.2j.md:42`, while its changed-files / FAIL_TO_PASS text still says `16 tests` at `.agent/context/handoffs/067-2026-03-15-scheduling-repos-bp09s9.2j.md:60` and `.agent/context/handoffs/067-2026-03-15-scheduling-repos-bp09s9.2j.md:74`.

### Resolved Since Pass 2

- The real-UoW persistence bug is fixed. `PipelineRunner` now persists `PipelineStepModel` rows using `run_id`, and the end-to-end repro succeeds.
- No remaining high-severity runtime defect was reproduced in the reviewed scheduling-infrastructure code path.

### Verdict

- `changes_required`

### Residual Risk

- The code path I rechecked is functionally stronger than in prior passes, but approval would still bless a project state that contradicts its own task ledger, build plan, registry, and handoff evidence. The remaining risk is operational/audit drift rather than immediate runtime failure.

## 2026-03-15 Recheck Pass 4

### Scope Reviewed

- Same correlated implementation target:
  - `docs/execution/plans/2026-03-15-scheduling-infrastructure/`
  - `.agent/context/handoffs/066-2026-03-15-scheduling-models-bp09s9.2a-i.md`
  - `.agent/context/handoffs/067-2026-03-15-scheduling-repos-bp09s9.2j.md`
  - `.agent/context/handoffs/068-2026-03-15-pipeline-runner-bp09s9.3a.md`
  - `.agent/context/handoffs/069-2026-03-15-ref-resolver-bp09s9.3b+9.3c.md`

### Commands Executed

- `uv run python tools/validate_codebase.py --scope meu`
- `uv run pytest tests/ --tb=no -q`
- Inline repro harness with a real in-memory `SqlAlchemyUnitOfWork` and seeded `PolicyModel` to run `PipelineRunner.run(...)` and confirm persisted `PipelineStepModel` rows
- `rg -n "not_started|MEU gate|Update meu-registry|Update BUILD_PLAN|Create reflection|Update metrics|Save session state|Prepare commit messages" docs/execution/plans/2026-03-15-scheduling-infrastructure/task.md`
- `rg -n "MEU-81|MEU-82|MEU-83|MEU-84|P2.5" docs/BUILD_PLAN.md .agent/context/meu-registry.md`
- `rg -n "to_thread|Repo bridge|Sync/Async Decision" docs/execution/plans/2026-03-15-scheduling-infrastructure/implementation-plan.md`
- `rg -n "11 tests|16/16|18/18|1303/1303|list_recent\(|AC-10|tests_added:|tests_passing:" .agent/context/handoffs/067-2026-03-15-scheduling-repos-bp09s9.2j.md .agent/context/handoffs/068-2026-03-15-pipeline-runner-bp09s9.3a.md`

### Recheck Results

- `uv run python tools/validate_codebase.py --scope meu`: PASS
- `uv run pytest tests/ --tb=no -q`: PASS (`1309 passed, 1 skipped, 1 warning`)
- Real-UoW repro harness: PASS
  - `PipelineRunner.run(...)` completed successfully
  - one persisted `PipelineStepModel` row was written

### Findings by Severity

- **Medium** — The only remaining blocking issue is completion-state drift across canonical project artifacts. `task.md` still leaves the MEU gate and post-MEU documentation work as `not_started` at `docs/execution/plans/2026-03-15-scheduling-infrastructure/task.md:46`, `docs/execution/plans/2026-03-15-scheduling-infrastructure/task.md:47`, `docs/execution/plans/2026-03-15-scheduling-infrastructure/task.md:48`, `docs/execution/plans/2026-03-15-scheduling-infrastructure/task.md:51`, `docs/execution/plans/2026-03-15-scheduling-infrastructure/task.md:52`, `docs/execution/plans/2026-03-15-scheduling-infrastructure/task.md:53`, and `docs/execution/plans/2026-03-15-scheduling-infrastructure/task.md:54`. `docs/BUILD_PLAN.md:276` through `docs/BUILD_PLAN.md:279` and `docs/BUILD_PLAN.md:471` still represent MEU-81..84 / P2.5 as incomplete, and `.agent/context/meu-registry.md:115` still has no MEU-81..84 entries. The reflection and commit-message artifacts also still do not exist.
- **Medium** — The implementation continues to diverge from the documented `asyncio.to_thread()` bridge contract at `docs/execution/plans/2026-03-15-scheduling-infrastructure/implementation-plan.md:129`, `docs/execution/plans/2026-03-15-scheduling-infrastructure/implementation-plan.md:177`, and `docs/execution/plans/2026-03-15-scheduling-infrastructure/implementation-plan.md:183`. I did not reproduce a runtime failure from this in the reviewed path, but it remains a plan-contract mismatch.
- **Low** — Handoff bookkeeping is still stale. `.agent/context/handoffs/068-2026-03-15-pipeline-runner-bp09s9.3a.md:68` and `.agent/context/handoffs/068-2026-03-15-pipeline-runner-bp09s9.3a.md:81` still say `11 tests` while the same handoff now claims `16/16`, and `.agent/context/handoffs/067-2026-03-15-scheduling-repos-bp09s9.2j.md` still omits `list_recent()` from its AC/test mapping even though the code and tests now include it.

### Resolved Since Pass 3

- No high-severity runtime or gate failures were reproduced.
- The real-UoW `PipelineRunner` repro, MEU gate, and full regression remained green.

### Verdict

- `changes_required`

### Residual Risk

- Remaining risk is now documentation, auditability, and project-state integrity rather than reproduced behavioral failure. Approval at this point would mostly certify stale status tracking.

## 2026-03-15 Recheck Pass 5

### Scope Reviewed

- Same correlated implementation target:
  - `docs/execution/plans/2026-03-15-scheduling-infrastructure/`
  - `.agent/context/handoffs/066-2026-03-15-scheduling-models-bp09s9.2a-i.md`
  - `.agent/context/handoffs/067-2026-03-15-scheduling-repos-bp09s9.2j.md`
  - `.agent/context/handoffs/068-2026-03-15-pipeline-runner-bp09s9.3a.md`
  - `.agent/context/handoffs/069-2026-03-15-ref-resolver-bp09s9.3b+9.3c.md`

### Commands Executed

- `git status --short`
- `uv run python tools/validate_codebase.py --scope meu`
- `uv run pytest tests/ --tb=no -q`
- `rg -n "not_started|MEU gate|Update meu-registry|Update BUILD_PLAN|Create reflection|Update metrics|Save session state|Prepare commit messages" docs/execution/plans/2026-03-15-scheduling-infrastructure/task.md`
- `rg -n "MEU-81|MEU-82|MEU-83|MEU-84|P2.5|Phase 9.*In Progress" docs/BUILD_PLAN.md .agent/context/meu-registry.md docs/execution/metrics.md`
- `Test-Path docs/execution/reflections/2026-03-15-scheduling-infra-reflection.md`
- `Test-Path docs/execution/plans/2026-03-15-scheduling-infrastructure/commit-messages.md`
- `rg -n "to_thread|direct sync|SQLite sessions|asyncio.to_thread|Sync/Async Decision" docs/execution/plans/2026-03-15-scheduling-infrastructure/implementation-plan.md packages/core/src/zorivest_core/services/pipeline_runner.py`
- `rg -n "1303/1303|1309 passed|11 tests|16/16|18/18|list_recent\(|AC-10|tests_added:|tests_passing:" .agent/context/handoffs/067-2026-03-15-scheduling-repos-bp09s9.2j.md .agent/context/handoffs/068-2026-03-15-pipeline-runner-bp09s9.3a.md`

### Recheck Results

- `uv run python tools/validate_codebase.py --scope meu`: PASS
- `uv run pytest tests/ --tb=no -q`: PASS (`1309 passed, 1 skipped, 1 warning`)
- Task ledger, BUILD_PLAN, meu-registry, metrics row, reflection, and commit-message artifacts are now present and aligned with completion state.
- The prior sync/async plan-contract mismatch is now resolved by updating the implementation plan to document the direct synchronous repo bridge.

### Findings by Severity

- **Low** — Two MEU handoffs still contain stale full-regression evidence. The scheduling-repos handoff still records `uv run pytest tests/ --tb=no -q` as `PASS (1303/1303)` at `.agent/context/handoffs/067-2026-03-15-scheduling-repos-bp09s9.2j.md:68`, and the pipeline-runner handoff still records the same outdated total at `.agent/context/handoffs/068-2026-03-15-pipeline-runner-bp09s9.3a.md:85`. On this pass, the actual rerun result was `1309 passed, 1 skipped, 1 warning`. This no longer indicates a product/runtime defect, but it is still inaccurate evidence inside the deliverable handoffs.

### Resolved Since Pass 4

- `task.md` now marks the MEU gate and post-MEU artifacts done.
- `docs/BUILD_PLAN.md`, `.agent/context/meu-registry.md`, and `docs/execution/metrics.md` now reflect MEU-81..84 completion.
- `docs/execution/reflections/2026-03-15-scheduling-infra-reflection.md` and `docs/execution/plans/2026-03-15-scheduling-infrastructure/commit-messages.md` now exist.
- The implementation plan now documents the direct sync repo bridge, so the prior `asyncio.to_thread()` plan mismatch is closed.

### Verdict

- `changes_required`

### Residual Risk

- Remaining risk is limited to audit/evidence accuracy. The reviewed code and validation path are green, but approving with stale command evidence would still certify handoffs that do not exactly match the current verified state.

## 2026-03-15 Recheck Pass 6

### Scope Reviewed

- Same correlated implementation target:
  - `docs/execution/plans/2026-03-15-scheduling-infrastructure/`
  - `.agent/context/handoffs/066-2026-03-15-scheduling-models-bp09s9.2a-i.md`
  - `.agent/context/handoffs/067-2026-03-15-scheduling-repos-bp09s9.2j.md`
  - `.agent/context/handoffs/068-2026-03-15-pipeline-runner-bp09s9.3a.md`
  - `.agent/context/handoffs/069-2026-03-15-ref-resolver-bp09s9.3b+9.3c.md`

### Commands Executed

- `uv run python tools/validate_codebase.py --scope meu`
- `uv run pytest tests/ --tb=no -q`
- `rg -n "1303/1303|1309/1309|1309 passed|skipped|warning|Full regression" .agent/context/handoffs/066-2026-03-15-scheduling-models-bp09s9.2a-i.md .agent/context/handoffs/067-2026-03-15-scheduling-repos-bp09s9.2j.md .agent/context/handoffs/068-2026-03-15-pipeline-runner-bp09s9.3a.md .agent/context/handoffs/069-2026-03-15-ref-resolver-bp09s9.3b+9.3c.md`
- `rg -n "MEU gate|Update meu-registry|Update BUILD_PLAN|Create reflection|Update metrics|Save session state|Prepare commit messages" docs/execution/plans/2026-03-15-scheduling-infrastructure/task.md`
- `rg -n "MEU-81|MEU-82|MEU-83|MEU-84|P2.5" docs/BUILD_PLAN.md .agent/context/meu-registry.md docs/execution/metrics.md`
- `rg -n "Sync/Async Decision|Repo bridge|asyncio.to_thread\(\)|calls sync repos directly" docs/execution/plans/2026-03-15-scheduling-infrastructure/implementation-plan.md`

### Recheck Results

- `uv run python tools/validate_codebase.py --scope meu`: PASS
- `uv run pytest tests/ --tb=no -q`: PASS (`1309 passed, 1 skipped, 1 warning`)
- No stale `1303/1303` full-regression entries remain in the correlated MEU handoffs.
- Task ledger, BUILD_PLAN, meu-registry, metrics, reflection, commit-message artifacts, and implementation-plan contract remain aligned.

### Findings by Severity

- No findings.

### Resolved Since Pass 5

- The previously stale full-regression evidence in `.agent/context/handoffs/067-2026-03-15-scheduling-repos-bp09s9.2j.md` and `.agent/context/handoffs/068-2026-03-15-pipeline-runner-bp09s9.3a.md` has been refreshed.
- The four correlated MEU handoffs now consistently report the current full-regression passed-count summary (`1309/1309`), and no earlier `1303/1303` evidence remains.

### Verdict

- `approved`

### Residual Risk

- No blocking risk was reproduced on this pass. The only remaining note is the non-blocking pytest warning in `tests/unit/test_pipeline_runner.py::TestTimeoutHandling::test_step_timeout_fails_pipeline`, which does not currently invalidate the reviewed implementation or handoff set.
