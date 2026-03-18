# Reflection — Scheduling API + Guardrails (MEU-89/90)

> Date: 2026-03-18
> MEUs: MEU-89 (scheduling-api-mcp), MEU-90 (scheduling-guardrails)

## Summary

Delivered 16 REST endpoints, 6 MCP tools + 2 resources, 4 pipeline guardrails, and scheduler lifecycle management. Two correction rounds required after critical review.

## What Went Well

- Pipeline guardrails (16/16 tests green) were solid from the start — protocol-based design paid off
- MCP tool registration pattern (6 tools + seed integration) was familiar from prior MEUs
- Round 1 code fixes (runner invocation, approval reset, deserialization) were straightforward

## What Needed Correction

### Round 1 (F1-F6)
- **F2**: Services not wired into FastAPI app state — hidden by dependency overrides in tests
- **F3**: `trigger_run()` created records but never called runner; `patch_schedule()` didn't reset approval
- **F4**: MCP resources defined but never registered in seed path
- **F5**: Tests passed despite broken behavior — false confidence

### Round 2 (R1-R4)
- **R1**: Closeout docs (BUILD_PLAN, meu-registry, metrics, handoff copies) not done
- **R2**: Scheduler lifecycle hooks (start/shutdown) missing from lifespan
- **R3**: No live-wiring route test — all tests used dependency overrides
- **R4**: Handoff 076 prose used wrong method/protocol names

## Lessons Learned

1. **Live wiring tests are essential** — dependency override tests mask missing app-state wiring. At least one test should use real app state.
2. **Execution path tests must assert the action, not just the record** — `trigger_run()` passed tests by creating a run record, but never executed anything.
3. **Closeout docs should be done inline** — deferring BUILD_PLAN/registry updates creates a whole category of review findings.

## Rules Checked (10/10)

1. ✅ TDD: Tests written before/alongside implementation
2. ✅ No file deletion without backup
3. ✅ Cross-doc consistency maintained (12→16 endpoints in 4 files)
4. ✅ Handoff prose matches implementation
5. ✅ Protocol-based dependency injection
6. ✅ Pyright clean (0 errors)
7. ✅ Regression suite green (1515 passed, 1 pre-existing)
8. ✅ Canonical handoff location used
9. ✅ MEU registry updated
10. ✅ Metrics row added
