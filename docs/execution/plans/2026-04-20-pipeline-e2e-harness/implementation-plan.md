---
project: "2026-04-20-pipeline-e2e-harness"
date: "2026-04-20"
source: "docs/build-plan/09b-pipeline-hardening.md §9B.6"
meus: ["MEU-PW8"]
status: "in_progress_extended"
template_version: "2.0"
---

# Implementation Plan: Pipeline E2E Test Harness

> **Project**: `2026-04-20-pipeline-e2e-harness`
> **Build Plan Section(s)**: 09b §9B.6
> **Status**: `in_progress_extended` (original E2E harness complete; extended with bug fixes + diagnostics)

---

## Goal

Create the end-to-end integration test infrastructure for the pipeline execution engine. No integration tests currently validate that a policy document traverses the complete execution path:

```
SchedulingService.trigger_run()
     → PipelineRunner.run()
          → Step type lookup (registry)
               → RefResolver (param resolution)
                    → Step.execute() (all 5 types)
                         → Persistence hooks
                              → Audit trail
```

This MEU delivers: 7 reusable test policy fixtures, 6 mock step implementations, and 18+ integration tests that validate the full service stack with real SQLAlchemy persistence (in-memory SQLite, no stubs).

---

## User Review Required

> [!IMPORTANT]
> **No breaking changes.** This MEU is test-only — it creates no new production code, no API surfaces, and modifies no existing behavior. All changes are in `tests/`.

### Design Decision: Full Stack vs. Mid-Stack Testing

The tests wire up the **full SchedulingService stack** (SchedulingService → PipelineRunner → StepRegistry → UoW → Persistence → Audit) using real adapters from `scheduling_adapters.py`. This is the heaviest-weight approach but provides the most complete coverage. A stub `SchedulerService` is used since APScheduler job scheduling is out of scope for pipeline execution E2E tests.

### Design Decision: Mock Step Registry Cleanup

Mock steps auto-register via `RegisteredStep.__init_subclass__`. To prevent registry pollution across test modules, a session-scoped fixture imports `mock_steps` and removes mock entries from `STEP_REGISTRY` on teardown. This follows the spec's risk mitigation: "Scoped registration in conftest; cleanup after test session" (§9B.8).

---

## Proposed Changes

### MEU-PW8: Pipeline E2E Test Harness

#### Boundary Inventory

No external input surfaces — this MEU is test-only.

| Surface | Schema Owner | Field Constraints | Extra-Field Policy |
|---------|-------------|-------------------|-------------------|
| N/A (test-only MEU) | — | — | — |

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-1 | 7 test policy fixtures importable from `tests.fixtures.policies` | `Spec` (§9B.6b) | — |
| AC-2 | 6 mock step classes registered in StepRegistry when `mock_steps` imported | `Spec` (§9B.6c) | — |
| AC-3 | Mock step types are cleaned up from `STEP_REGISTRY` after test session | `Spec` (§9B.8) | — |
| AC-4 | `test_create_approve_run_success`: Full lifecycle through SchedulingService completes with `status=success` | `Spec` (§9B.6d) | — |
| AC-5 | `test_run_unapproved_policy_rejected`: Unapproved policy returns error via guardrails | `Spec` (§9B.6d) | Unapproved → error |
| AC-6 | `test_delete_policy_unschedules`: Deleted policy no longer retrievable | `Spec` (§9B.6d) | — |
| AC-7 | `test_all_steps_execute_in_order`: Steps execute sequentially per policy step list | `Spec` (§9B.6d) | — |
| AC-8 | `test_ref_resolution_across_steps`: `{ref: ctx.X.output.Y}` resolves correctly to prior step output | `Spec` (§9B.6d) | — |
| AC-9 | `test_step_output_persisted_to_db`: Step records exist in pipeline_steps table after run | `Spec` (§9B.6d) | — |
| AC-10 | `test_fail_pipeline_aborts`: First step failure aborts pipeline, second step never runs | `Spec` (§9B.6d) | — |
| AC-11 | `test_log_and_continue_proceeds`: Failed step with `on_error=log_and_continue` doesn't abort; next step runs | `Spec` (§9B.6d) | — |
| AC-12 | `test_dry_run_skips_side_effects`: Steps with `side_effects=True` skipped in dry-run mode | `Spec` (§9B.6d) | — |
| AC-13 | `test_skip_condition_evaluated`: Step with `skip_if` condition evaluating to True is skipped | `Spec` (§9B.6d) | — |
| AC-14 | `test_cancel_running_pipeline`: Running pipeline can be cancelled; status transitions to `cancelled` | `Spec` (§9B.6d) | — |
| AC-15 | `test_cancel_idempotent_on_completed`: Cancel on terminal-state run returns current state without error | `Spec` (§9B.6d) | — |
| AC-16 | `test_unicode_error_messages_no_crash`: Non-ASCII error messages (PW4 regression) don't crash pipeline | `Spec` (§9B.6d) | — |
| AC-17 | `test_run_creates_audit_entry`: Triggering a run creates `pipeline.run` audit log entry | `Spec` (§9B.6d) | — |
| AC-18 | `test_cancel_creates_audit_entry`: Cancelling a run creates `pipeline.cancel` audit log entry | `Spec` (§9B.6d) | — |
| AC-19 | `test_retry_exhaustion_fails`: Step with retry mode exhausts retries then fails pipeline | `Spec` (§9B.6d L854) | — |
| AC-20 | `test_startup_zombie_recovery`: Zombie runs (status=running at startup) are recovered to failed | `Spec` (§9B.6d L868) | — |
| AC-21 | `test_no_dual_write_records`: PipelineRunner with pre-created `run_id` does not create a duplicate run record | `Spec` (§9B.6d L869) | — |
| AC-22 | `test_bytes_output_serializable`: Step output containing `bytes` values serializes without crash | `Spec` (§9B.6d L874) | — |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| Policy fixture JSON structure | `Spec` | §9B.6b provides all 7 complete dict fixtures |
| Mock step class signatures | `Spec` | §9B.6c provides all 6 class implementations |
| Test class/method structure | `Spec` | §9B.6d provides 8 class outlines with 18+ methods |
| Service wiring for tests | `Local Canon` | `scheduling_adapters.py` provides PolicyStoreAdapter, RunStoreAdapter, StepStoreAdapter, AuditCounterAdapter; `pipeline_runner.py` constructor shows all dependencies |
| UoW test fixture pattern | `Local Canon` | `tests/conftest.py` provides engine + db_session fixtures |
| Registry cleanup strategy | `Spec` | §9B.8 specifies "scoped registration in conftest; cleanup after test session" |
| Zombie recovery test approach | `Local Canon` | `PipelineRunner.recover_zombies()` reads `find_zombies()` from pipeline_runs repo; testable by inserting a run record with status=running pre-test |
| Step persistence verification | `Local Canon` | Runner calls `_persist_step()` which writes `PipelineStepModel` via UoW session; query `pipeline_steps` table via StepStoreAdapter |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `tests/fixtures/__init__.py` | **NEW** | Package init — empty |
| `tests/fixtures/policies.py` | **NEW** | 7 policy dict fixtures matching §9B.6b |
| `tests/fixtures/mock_steps.py` | **NEW** | 6 mock step classes matching §9B.6c |
| `tests/conftest.py` | **MODIFY** | Add pipeline service stack fixtures (UoW, adapters, SchedulingService, PipelineRunner) + mock step registration/cleanup |
| `tests/integration/test_pipeline_e2e.py` | **NEW** | 18+ integration tests across 8 test classes |

---

## Out of Scope

- GUI cancel button (GUI-layer, separate MEU)
- Scheduler job management (APScheduler, cron evaluation)

---

## BUILD_PLAN.md Audit

This project updates the MEU-PW8 status from ⬜ to 🟡 (ready_for_review) in `docs/BUILD_PLAN.md`.

```powershell
rg "MEU-PW8" docs/BUILD_PLAN.md  # Expected: 1 match, status column update
```

---

## Completed During Execution (Beyond Original Scope)

During live GUI testing and user-requested diagnostics, the following additional work was completed:

### BF-1: Dedup Key Fallback (PIPE-DEDUP — Resolved)

- **Root cause:** `compute_dedup_key()` in `send_step.py` computed keys from `snapshot_hash`, but when `StoreReportStep` was not in the pipeline (or snapshot was `None`), the dedup key was identical across runs → second run was silently skipped.
- **Fix:** Added `run_id` fallback in dedup key computation (lines 124-133). When `snapshot_hash` is absent, `context.run_id` is used instead, ensuring unique keys per execution.
- **Files changed:** [send_step.py:124-133](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/send_step.py#L124-L133), [test_send_step.py](file:///p:/zorivest/tests/unit/test_send_step.py)
- **TDD evidence:** `test_dedup_key_fallback_to_run_id` — RED then GREEN.

### BF-2: SMTP Security Field Wiring

- **Root cause:** `get_smtp_runtime_config()` included `security` (STARTTLS/SSL) in the config dict, but downstream tests and integration wiring didn't account for the new key → assertion failures.
- **Fix:** Updated `test_smtp_runtime_config.py` expected keys set and `test_pipeline_wiring.py` SMTP config assertions to include `security`.
- **Files changed:** [test_smtp_runtime_config.py](file:///p:/zorivest/tests/unit/test_smtp_runtime_config.py), [test_pipeline_wiring.py](file:///p:/zorivest/tests/integration/test_pipeline_wiring.py)
- **TDD evidence:** Both test files pass with security field included.

### DA-1: Template Rendering Gap Analysis

- **Report:** [template_rendering_gap_analysis.md](file:///p:/zorivest/.agent/context/scheduling/template_rendering_gap_analysis.md)
- **Key finding:** 3-layer disconnection — `EMAIL_TEMPLATES` registry (Layer 1) is never queried, `template_engine` (Layer 2) is injected into context but unread by SendStep, and `body_template` (Layer 3) is treated as a raw literal string instead of a template key. Result: emails are sent with the template name as the body text.
- **Tracked as:** [TEMPLATE-RENDER] in `known-issues.md`

### DA-2: Data Flow Gap Analysis

- **Report:** [data_flow_gap_analysis.md](file:///p:/zorivest/.agent/context/scheduling/data_flow_gap_analysis.md)
- **Key findings:** (1) No end-to-end integration test exercising real FetchStep→TransformStep→StoreReportStep data handoff, (2) Cache upsert after HTTP 200 untested, (3) Pipeline state cursor tracking modeled but unused, (4) 48 planned use cases catalogued with 44/48 implemented.
- **Tracked as:** [PIPE-E2E-CHAIN], [PIPE-CACHEUPSERT], [PIPE-CURSORS] in `known-issues.md`

---

## Verification Plan

### 1. Unit Tests — Policy Fixtures Importable
```powershell
uv run python -c "from tests.fixtures.policies import SMOKE_POLICY_BASIC, POLICY_ERROR_FAIL, POLICY_ERROR_CONTINUE, POLICY_DRY_RUN, POLICY_SKIP_CONDITION, POLICY_CANCELLABLE, POLICY_UNICODE_ERROR; print('OK:', len([SMOKE_POLICY_BASIC, POLICY_ERROR_FAIL, POLICY_ERROR_CONTINUE, POLICY_DRY_RUN, POLICY_SKIP_CONDITION, POLICY_CANCELLABLE, POLICY_UNICODE_ERROR]))" *> C:\Temp\zorivest\imports.txt; Get-Content C:\Temp\zorivest\imports.txt
```

### 2. E2E Test Suite
```powershell
uv run pytest tests/integration/test_pipeline_e2e.py -v *> C:\Temp\zorivest\e2e.txt; Get-Content C:\Temp\zorivest\e2e.txt | Select-Object -Last 40
```

### 3. Full Regression
```powershell
uv run pytest tests/ -x --tb=short -q *> C:\Temp\zorivest\regression.txt; Get-Content C:\Temp\zorivest\regression.txt | Select-Object -Last 20
```

### 4. Type Check
```powershell
uv run pyright packages/ tests/ *> C:\Temp\zorivest\pyright.txt; Get-Content C:\Temp\zorivest\pyright.txt | Select-Object -Last 30
```

### 5. Lint
```powershell
uv run ruff check packages/ tests/ *> C:\Temp\zorivest\ruff.txt; Get-Content C:\Temp\zorivest\ruff.txt | Select-Object -Last 20
```

### 6. MEU Gate
```powershell
uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate.txt; Get-Content C:\Temp\zorivest\validate.txt | Select-Object -Last 50
```

---

## Open Questions

None. All behaviors are fully specified in §9B.6 or resolvable from Local Canon.

---

## Research References

- [09b-pipeline-hardening.md §9B.6](file:///p:/zorivest/docs/build-plan/09b-pipeline-hardening.md) — Primary spec
- [scheduling_adapters.py](file:///p:/zorivest/packages/api/src/zorivest_api/scheduling_adapters.py) — Adapter pattern for test wiring
- [pipeline_runner.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/pipeline_runner.py) — Runner implementation
- [scheduling_service.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/scheduling_service.py) — Service facade
- [pipeline_guardrails.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/pipeline_guardrails.py) — Guardrails implementation
- [unit_of_work.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/unit_of_work.py) — UoW + engine creation
