# Reflection — Phase 9 Scheduling Infrastructure (MEU-81..84)

> Date: 2026-03-15
> Project: `2026-03-15-scheduling-infrastructure`
> MEUs: 81, 82, 83, 84

## What Went Well

- **TDD cycle worked**: Tests written first, all passed after implementation.
- **Clean Architecture boundaries respected**: PipelineRunner in `core/` doesn't import infra models at class level — deferred imports only in persistence methods.
- **UoW optional pattern**: `uow=None` allows pure unit tests; live UoW test verifies real persistence.

## What Could Be Improved

- **Column name mismatch escaped initial tests**: `pipeline_run_id` vs `run_id` wasn't caught because all tests used `uow=None`. Adding the live UoW test (AC-14) was essential for catching this class of bug.
- **Implementation plan overstated `asyncio.to_thread()`**: Plan said sync calls would be bridged via `to_thread`, but code called sync directly. The plan-contract gap caused repeated review findings until corrected.
- **Post-MEU deliverables deferred too long**: Handoff body text, BUILD_PLAN, meu-registry updates were delayed, creating 4 review passes worth of "stale evidence" findings.

## Key Decisions

| Decision | Rationale |
|----------|-----------|
| Sync repo calls from async runner (no `to_thread`) | SQLite sessions are fast/non-blocking; build-plan spec doesn't require async bridge |
| `policy_id` as separate arg | `PolicyDocument` is a pure domain model without DB identity |
| Persistence hooks no-op when `uow=None` | Unit test isolation without DB infrastructure |

## Review Pass Summary

| Pass | Findings | Verdict |
|------|----------|---------|
| 1 | 4 High, 1 Medium, 1 Low | `changes_required` |
| 2 | 1 High, 3 Medium | `changes_required` |
| 3 | 2 Medium, 1 Low | `changes_required` |
| 4 | 2 Medium, 1 Low | `changes_required` |

## Metrics

- **Lines of code**: ~424 (pipeline_runner.py) + ~306 (scheduling_repositories.py)
- **Tests**: 16 (pipeline_runner) + 18 (scheduling_repos) + 25 (ref_resolver) + 18 (scheduling_models) = **77 new tests**
- **Full regression**: 1309 passed, 0 failed
