# Task List — Phase 9 Scheduling Infrastructure Core

> Project: `2026-03-15-scheduling-infrastructure`
> MEUs: 81, 84, 82, 83

---

## MEU-81: Scheduling Models

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 1 | Write tests (Red phase) | coder | `tests/unit/test_scheduling_models.py` | Tests exist and fail (no models yet) | [ ] |
| 2 | Add 9 model classes (Green phase) | coder | `models.py` (append 9 classes) | `uv run pytest tests/unit/test_scheduling_models.py -v` — all pass | [ ] |
| 3 | Add trigger DDL via `event.listen` | coder | `models.py` (report versioning + audit append-only triggers) | AC-11: UPDATE on `reports` inserts into `report_versions`; AC-12: UPDATE/DELETE on `audit_log` raises error | [ ] |
| 4 | Create handoff | coder | `.agent/context/handoffs/<seq>-2026-03-15-scheduling-models-bp09s9.2.md` | Handoff follows `TEMPLATE.md` | [ ] |

## MEU-84: RefResolver + ConditionEvaluator

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 1 | Write tests (Red phase) | coder | `tests/unit/test_ref_resolver.py` | Tests exist and fail (no impl yet) | [ ] |
| 2 | Create `ref_resolver.py` (Green phase) | coder | `packages/core/src/zorivest_core/services/ref_resolver.py` | `uv run pytest tests/unit/test_ref_resolver.py::TestRefResolver -v` — all pass | [ ] |
| 3 | Create `condition_evaluator.py` (Green phase) | coder | `packages/core/src/zorivest_core/services/condition_evaluator.py` | `uv run pytest tests/unit/test_ref_resolver.py::TestConditionEvaluator -v` — all pass | [ ] |
| 4 | Create handoff | coder | `.agent/context/handoffs/<seq>-2026-03-15-ref-resolver-bp09s9.3b+9.3c.md` | Handoff follows `TEMPLATE.md` | [ ] |

## MEU-82: Scheduling Repos

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 1 | Write tests (Red phase) | coder | `tests/unit/test_scheduling_repos.py` | Tests exist and fail (no repos yet) | [ ] |
| 2 | Create `scheduling_repositories.py` (Green phase) | coder | `packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py` | `uv run pytest tests/unit/test_scheduling_repos.py -v` — all pass | [ ] |
| 3 | Extend `unit_of_work.py` | coder | `unit_of_work.py` (5 new repo attributes) | UoW context manager creates scheduling repo attrs | [ ] |
| 4 | Create handoff | coder | `.agent/context/handoffs/<seq>-2026-03-15-scheduling-repos-bp09s9.2j.md` | Handoff follows `TEMPLATE.md` | [ ] |

## MEU-83: PipelineRunner

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 1 | Write tests (Red phase) | coder | `tests/unit/test_pipeline_runner.py` | Tests exist and fail (no runner yet) | [ ] |
| 2 | Create `pipeline_runner.py` (Green phase) | coder | `packages/core/src/zorivest_core/services/pipeline_runner.py` | `uv run pytest tests/unit/test_pipeline_runner.py -v` — all pass | [ ] |
| 3 | Create handoff | coder | `.agent/context/handoffs/<seq>-2026-03-15-pipeline-runner-bp09s9.3a+9.3e.md` | Handoff follows `TEMPLATE.md` | [ ] |

## Post-MEU Deliverables

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 1 | MEU gate | tester | Gate pass output | `uv run python tools/validate_codebase.py --scope meu` — 0 errors | [ ] |
| 2 | Update meu-registry | coder | `.agent/context/meu-registry.md` | MEU-81, 82, 83, 84 marked ✅ | [ ] |
| 3 | Update BUILD_PLAN | coder | `docs/BUILD_PLAN.md` | Phase 9 status + summary counts updated | [ ] |
| 4 | Full regression | tester | Test output | `uv run pytest tests/ -v` — all pass | [ ] |
| 5 | Anti-placeholder scan | tester | Scan output | `rg "TODO\|FIXME\|NotImplementedError" packages/` — 0 matches in new files | [ ] |
| 6 | Create reflection | coder | `docs/execution/reflections/2026-03-15-scheduling-infra-reflection.md` | Follows reflection template | [ ] |
| 7 | Update metrics | coder | `docs/execution/metrics.md` | Row added for this project | [ ] |
| 8 | Save session state | coder | `pomera_notes` | Session saved | [ ] |
| 9 | Prepare commit messages | coder | Commit messages | Conventional commit format | [ ] |
