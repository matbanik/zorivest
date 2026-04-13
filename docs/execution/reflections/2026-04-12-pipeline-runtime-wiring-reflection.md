# Reflection — MEU-PW1: Pipeline Runtime Wiring

**Date:** 2026-04-12
**MEU:** MEU-PW1 (`pipeline-runtime-wiring`)
**Build Plan:** 09-scheduling §9.49.4

## What Went Well

1. **Scope refinement saved time.** The original MEU scoping (from MEU-PW1 discovery session) correctly identified that `MarketDataProviderAdapter` should be deferred to PW2, preventing scope creep while keeping 4/5 step types operational.
2. **TDD caught a real bug.** The `initial_outputs` injection test revealed that `compute_content_hash` calls `model_dump()` on the policy — the mock fixture needed explicit setup. This validated the test-first approach.
3. **Integration tests provided high confidence.** The 10-test integration suite directly verifies each dependency slot via `TestClient` lifespan, catching the `_runner` vs `_pipeline_runner` attribute naming mismatch immediately.
4. **Clean stub retirement.** Deleting `StubMarketDataService` and `StubProviderConnectionService` removed ~50 lines of dead code with zero ripple effects on the 1904-test suite.

## What Could Improve

1. **text-editor append-via-MCP was unreliable.** The first attempt to add `get_smtp_runtime_config()` via `mcp_text-editor` silently failed — required fallback to `replace_file_content`. Lesson: verify file state after MCP edits.
2. **Registry/BUILD_PLAN didn't have MEU-PW1 initially.** The scoping session created the MEU in `meu-pw1-scope.md` but BUILD_PLAN.md already had the entry at L126. Registry needed description update. Lesson: scoping-session outputs should include registry+BUILD_PLAN updates atomically.

## Metrics

| Metric | Value |
|--------|-------|
| Production lines added/modified | ~90 |
| Production lines deleted | ~55 |
| New test files | 4 |
| New test assertions | 32 |
| TDD Red→Green cycles | 3 (constructor, SMTP, DbWriteAdapter) |
| Quality gate passes | 8/8 |
| Existing test regression | 0 |
