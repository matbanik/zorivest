# Task List — Phase 9 Scheduling Infrastructure Core

> Project: `2026-03-15-scheduling-infrastructure`
> MEUs: 81, 84, 82, 83

---

## MEU-81: Scheduling Models

| # | task | owner_role | deliverable | validation | status |
|---|------|------------|-------------|------------|--------|
| 1 | Write tests (Red phase) | coder | `tests/unit/test_scheduling_models.py` | `uv run pytest tests/unit/test_scheduling_models.py -v 2>&1 \| Select-String "FAILED"` returns matches | not_started |
| 2 | Add 9 model classes + trigger DDL (Green phase) | coder | `packages/infrastructure/src/zorivest_infra/database/models.py` | `uv run pytest tests/unit/test_scheduling_models.py -v` — 0 failures | not_started |
| 3 | Create handoff | coder | `.agent/context/handoffs/<seq>-2026-03-15-scheduling-models-bp09s9.2.md` | `Test-Path .agent/context/handoffs/*scheduling-models*` returns True | not_started |

## MEU-84: RefResolver + ConditionEvaluator

| # | task | owner_role | deliverable | validation | status |
|---|------|------------|-------------|------------|--------|
| 1 | Write tests (Red phase) | coder | `tests/unit/test_ref_resolver.py` | `uv run pytest tests/unit/test_ref_resolver.py -v 2>&1 \| Select-String "FAILED"` returns matches | not_started |
| 2 | Create `ref_resolver.py` (Green phase) | coder | `packages/core/src/zorivest_core/services/ref_resolver.py` | `uv run pytest tests/unit/test_ref_resolver.py::TestRefResolver -v` — 0 failures | not_started |
| 3 | Create `condition_evaluator.py` (Green phase) | coder | `packages/core/src/zorivest_core/services/condition_evaluator.py` | `uv run pytest tests/unit/test_ref_resolver.py::TestConditionEvaluator -v` — 0 failures | not_started |
| 4 | Create handoff | coder | `.agent/context/handoffs/<seq>-2026-03-15-ref-resolver-bp09s9.3b+9.3c.md` | `Test-Path .agent/context/handoffs/*ref-resolver*` returns True | not_started |

## MEU-82: Scheduling Repos

| # | task | owner_role | deliverable | validation | status |
|---|------|------------|-------------|------------|--------|
| 1 | Write tests (Red phase) | coder | `tests/unit/test_scheduling_repos.py` | `uv run pytest tests/unit/test_scheduling_repos.py -v 2>&1 \| Select-String "FAILED"` returns matches | not_started |
| 2 | Create `scheduling_repositories.py` (Green phase) | coder | `packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py` | `uv run pytest tests/unit/test_scheduling_repos.py -v` — 0 failures | not_started |
| 3 | Extend `unit_of_work.py` with 5 scheduling repo attrs | coder | `packages/infrastructure/src/zorivest_infra/database/unit_of_work.py` | `rg -c "scheduling" packages/infrastructure/src/zorivest_infra/database/unit_of_work.py` returns ≥5 | not_started |
| 4 | Create handoff | coder | `.agent/context/handoffs/<seq>-2026-03-15-scheduling-repos-bp09s9.2j.md` | `Test-Path .agent/context/handoffs/*scheduling-repos*` returns True | not_started |

## MEU-83: PipelineRunner

| # | task | owner_role | deliverable | validation | status |
|---|------|------------|-------------|------------|--------|
| 1 | Write tests (Red phase) | coder | `tests/unit/test_pipeline_runner.py` | `uv run pytest tests/unit/test_pipeline_runner.py -v 2>&1 \| Select-String "FAILED"` returns matches | not_started |
| 2 | Create `pipeline_runner.py` (Green phase) | coder | `packages/core/src/zorivest_core/services/pipeline_runner.py` | `uv run pytest tests/unit/test_pipeline_runner.py -v` — 0 failures | not_started |
| 3 | Create handoff | coder | `.agent/context/handoffs/<seq>-2026-03-15-pipeline-runner-bp09s9.3a+9.3e.md` | `Test-Path .agent/context/handoffs/*pipeline-runner*` returns True | not_started |

## Post-MEU Deliverables

| # | task | owner_role | deliverable | validation | status |
|---|------|------------|-------------|------------|--------|
| 1 | MEU gate | tester | Gate pass output | `uv run python tools/validate_codebase.py --scope meu` — 0 errors | not_started |
| 2 | Update meu-registry | coder | `.agent/context/meu-registry.md` | `rg -c "MEU-81\|MEU-82\|MEU-83\|MEU-84" .agent/context/meu-registry.md` returns ≥4 | not_started |
| 3 | Update BUILD_PLAN | coder | `docs/BUILD_PLAN.md` | `rg "Phase 9.*In Progress" docs/BUILD_PLAN.md` returns match | not_started |
| 4 | Full regression | tester | Test output | `uv run pytest tests/ -v` — 0 failures | not_started |
| 5 | Anti-placeholder scan | tester | Scan output | `rg "TODO\|FIXME\|NotImplementedError" packages/core/src/zorivest_core/services/ packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py` — 0 matches | not_started |
| 6 | Create reflection | coder | `docs/execution/reflections/2026-03-15-scheduling-infra-reflection.md` | `Test-Path docs/execution/reflections/2026-03-15-scheduling-infra-reflection.md` returns True | not_started |
| 7 | Update metrics | coder | `docs/execution/metrics.md` | `rg "scheduling-infrastructure" docs/execution/metrics.md` returns match | not_started |
| 8 | Save session state | coder | `pomera_notes` | Verified via MCP `pomera_notes search` tool in agent session | not_started |
| 9 | Prepare commit messages | coder | Commit messages | `git log -1 --format=%s` starts with `feat:` or `test:` or `refactor:` | not_started |
