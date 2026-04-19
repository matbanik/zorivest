# Reflection: Pipeline Charmap + Zombie Hardening (MEU-PW4, MEU-PW5)

> **Date:** 2026-04-19
> **MEUs:** MEU-PW4, MEU-PW5
> **Plan:** `docs/execution/plans/2026-04-19-pipeline-charmap-zombie/`

## What Went Well

1. **TDD discipline held** — All tests written before implementation. 6 PW4 tests and 9 PW5 tests confirmed Red→Green cycle.
2. **Clean architectural separation** — The persistence ownership model (scheduler creates, runner owns lifecycle) is clean and eliminates the zombie race condition at the protocol level.
3. **Backward compatibility preserved** — `PipelineRunner.run()` works with or without `run_id`, so manual triggers and existing tests are unaffected.
4. **Quality gates clean** — pyright 0 errors, ruff all passed, 2026 tests green, MEU gate 8/8.

## What Could Improve

1. **Workflow discipline** — Earlier session had confusion about plan file destinations (agent workspace vs project folder). This was resolved by known-issues update but cost review cycles.
2. **`recover_zombies()` is async but startup call is synchronous-style** — The `await` in lifespan is correct but the method itself queries the ORM synchronously. If the run table grows large, this could slow startup. Consider async query or pagination in PW8.

## Key Decisions

| Decision | Rationale | Source |
|----------|-----------|--------|
| Runner owns full lifecycle (pending→running→success/failed) | Single-writer eliminates race condition; scheduler only initializes | Spec §9B.3 |
| `httpx.Timeout` with segmented values | Granular control prevents connect timeouts from being conflated with slow reads | Spec §9B.3, httpx docs |
| `type: ignore[union-attr]` on `sys.stderr.reconfigure()` | CPython has it but stubs type as `TextIO` without it; `hasattr` guard ensures runtime safety | Research-backed |

## Metrics

- **Tests added:** 15 (6 PW4 + 9 PW5)
- **Files changed:** 7 (2 new, 5 modified)
- **Total test suite:** 2026 passed, 15 skipped, 0 failures
- **Quality gate:** 8/8 blocking passed
