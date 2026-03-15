# Task List — Phase 9 Scheduling Infrastructure Core

> Project: `2026-03-15-scheduling-infrastructure`
> MEUs: 81, 84, 82, 83

---

## MEU-81: Scheduling Models

- [ ] Write `test_scheduling_models.py` (Red phase)
- [ ] Add 9 model classes to `models.py` (Green phase)
- [ ] Run `uv run pytest tests/unit/test_scheduling_models.py -v` — all pass
- [ ] Create handoff `061-2026-03-15-scheduling-models-bp09s9.2.md`

## MEU-84: RefResolver + ConditionEvaluator

- [ ] Write `test_ref_resolver.py` (Red phase)
- [ ] Create `ref_resolver.py` (Green phase)
- [ ] Create `condition_evaluator.py` (Green phase)
- [ ] Run `uv run pytest tests/unit/test_ref_resolver.py -v` — all pass
- [ ] Create handoff `062-2026-03-15-ref-resolver-bp09s9.3b+9.3c.md`

## MEU-82: Scheduling Repos

- [ ] Write `test_scheduling_repos.py` (Red phase)
- [ ] Create `scheduling_repositories.py` (Green phase)
- [ ] Extend `unit_of_work.py` with scheduling repo attributes (Green phase)
- [ ] Run `uv run pytest tests/unit/test_scheduling_repos.py -v` — all pass
- [ ] Create handoff `063-2026-03-15-scheduling-repos-bp09s9.2j.md`

## MEU-83: PipelineRunner

- [ ] Write `test_pipeline_runner.py` (Red phase)
- [ ] Create `pipeline_runner.py` (Green phase)
- [ ] Run `uv run pytest tests/unit/test_pipeline_runner.py -v` — all pass
- [ ] Create handoff `064-2026-03-15-pipeline-runner-bp09s9.3a+9.3e.md`

## Post-MEU Deliverables

- [ ] Run MEU gate: `uv run python tools/validate_codebase.py --scope meu`
- [ ] Update `.agent/context/meu-registry.md` (add MEU-81, 82, 83, 84)
- [ ] Update `docs/BUILD_PLAN.md` status columns + Phase 9 status + summary counts
- [ ] Run full regression: `uv run pytest tests/ -v`
- [ ] Create reflection at `docs/execution/reflections/2026-03-15-scheduling-infra-reflection.md`
- [ ] Update metrics table in `docs/execution/metrics.md`
- [ ] Save session state to `pomera_notes`
- [ ] Prepare proposed commit messages
