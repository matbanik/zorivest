---
meu: 83
slug: pipeline-runner
phase: 9
priority: P1
status: ready_for_review
agent: antigravity
iteration: 1
files_changed: 1
tests_added: 16
tests_passing: 16
---

# MEU-83: PipelineRunner

## Scope

Implements the async PipelineRunner — the sequential execution engine for pipeline policies. Handles ref resolution, skip conditions, error modes (fail/continue/retry), dry-run, resume-from-failure, persistence hooks for run/step tracking, and zombie recovery (§9.3e).

Build plan reference: [09-scheduling.md §9.3a](file:///p:/zorivest/docs/build-plan/09-scheduling.md)

## Feature Intent Contract

### Intent Statement
The core execution engine that runs pipeline policies step-by-step, with resilience features (retry, skip, dry-run) and structured result reporting.

### Acceptance Criteria
- AC-1: Sequential step execution — steps run in order, sharing a StepContext
- AC-2: Skip conditions — steps with matching skip_if are SKIPPED
- AC-3: Dry-run mode — steps with side_effects=True are SKIPPED
- AC-4: Error mode FAIL_PIPELINE — stops execution on step failure
- AC-5: Error mode LOG_AND_CONTINUE — logs error, proceeds to next step
- AC-6: Error mode RETRY_THEN_FAIL — retries N times, then fails pipeline
- AC-7: Ref resolution — `{"ref": "ctx.step_a.result"}` resolved from prior outputs
- AC-8: Return dict with run_id, status, duration_ms, error, steps
- AC-9: Resume from failure — `resume_from` skips prior steps
- AC-10: Unknown step type returns FAILED result
- AC-11: Step timeout aborts pipeline
- AC-12: Cancellation returns cancelled status
- AC-13: Zombie recovery marks orphaned runs as failed
- AC-14: Live UoW persistence creates DB rows

### Negative Cases
- Must NOT: Continue after FAIL_PIPELINE error (step_c should NOT run after step_b fails)
- Must NOT: Mark pipeline SUCCESS when RETRY_THEN_FAIL retries are exhausted

### Test Mapping
| Criterion | Test File | Test Function |
|-----------|-----------|---------------|
| AC-1 | `tests/unit/test_pipeline_runner.py` | `TestSequentialExecution` (2 tests) |
| AC-2 | `tests/unit/test_pipeline_runner.py` | `TestSkipConditions` (1 test) |
| AC-3 | `tests/unit/test_pipeline_runner.py` | `TestDryRun` (1 test) |
| AC-4 | `tests/unit/test_pipeline_runner.py` | `TestFailPipeline` (1 test) |
| AC-5 | `tests/unit/test_pipeline_runner.py` | `TestLogAndContinue` (1 test) |
| AC-6 | `tests/unit/test_pipeline_runner.py` | `TestRetryThenFail` (2 tests) |
| AC-7 | `tests/unit/test_pipeline_runner.py` | `TestRefResolution` (1 test) |
| AC-8 | `tests/unit/test_pipeline_runner.py` | `TestReturnStructure` (1 test) |
| AC-9 | `tests/unit/test_pipeline_runner.py` | `TestResumeFrom` (1 test) |
| AC-10 | `tests/unit/test_pipeline_runner.py` | `TestUnknownStepType` (1 test) |
| AC-11 | `tests/unit/test_pipeline_runner.py` | `TestTimeoutHandling` (1 test) |
| AC-12 | `tests/unit/test_pipeline_runner.py` | `TestCancellationHandling` (1 test) |
| AC-13 | `tests/unit/test_pipeline_runner.py` | `TestZombieRecovery` (1 test) |
| AC-14 | `tests/unit/test_pipeline_runner.py` | `TestPersistenceWithUoW` (1 test) |

## Design Decisions & Known Risks

- **Decision**: `policy_id` passed as arg instead of `policy.id` — **Reasoning**: `PolicyDocument` (domain model) has no `id` field; that's on `PolicyModel` (infra). Keeps clean architecture boundary.
- **Decision**: `asyncio.run()` wrapper in tests instead of pytest-asyncio — **Reasoning**: pytest-asyncio is not a project dependency; using stdlib avoids adding deps for tests.
- **Bug fix**: Spec had `RETRY_THEN_FAIL` handled only inside `_execute_step` but the `run()` loop only checked FAIL_PIPELINE and LOG_AND_CONTINUE. Added explicit RETRY_THEN_FAIL exhaustion handling in the run loop.
- **Decision**: Persistence hooks are no-op when `uow=None` — **Reasoning**: Allows unit tests to run without DB infrastructure while production code persists run/step records.
- **Implementation**: `_create_run_record()`, `_persist_step()`, `_finalize_run()`, `_load_prior_output()`, and `recover_zombies()` all implemented per spec §9.3a/9.3e.

## Changed Files

| File | Action | Description |
|------|--------|-------------|
| `packages/core/src/zorivest_core/services/pipeline_runner.py` | Created | Async PipelineRunner with retry/skip/dry-run/resume |
| `tests/unit/test_pipeline_runner.py` | Created | 16 tests with mock step implementations + live UoW |

## Commands Executed

| Command | Result | Notes |
|---------|--------|-------|
| `uv run pytest tests/unit/test_pipeline_runner.py -v` | PASS (16/16) | All green |
| `uv run pytest tests/ --tb=no -q` | PASS (1309/1309) | Full regression |

## FAIL_TO_PASS Evidence

| Test | Before | After |
|------|--------|-------|
| `test_pipeline_runner.py` (16 tests) | FAIL (module not found) | PASS |

---
## Codex Validation Report
{Left blank — Codex fills this section during validation-review workflow}
