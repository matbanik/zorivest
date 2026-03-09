# Task Handoff

## Task

- **Date:** 2026-03-09
- **Task slug:** mcp-diagnostics
- **Owner role:** coder
- **Scope:** MEU-34 — `zorivest_diagnose` MCP tool

## Inputs

- User request:
  Implement `zorivest_diagnose` tool per 05b spec with safe-fetch, stub metrics, partial-availability.
- Specs/docs referenced:
  `docs/build-plan/05b-mcp-zorivest-diagnostics.md`, `docs/build-plan/05-mcp-server.md` §5.8–5.9, `docs/build-plan/testing-strategy.md` §116-121, `docs/execution/plans/2026-03-09-mcp-diagnostics-analytics-planning/implementation-plan.md`
- Constraints:
  Never reveal API keys. Stub MetricsCollector until MEU-39. Handle unavailable `/market-data/providers` endpoint (Phase 8).

## Role Plan

1. orchestrator — scoped in implementation plan
2. coder — FIC → tests → implementation
3. tester — vitest run, full regression
4. reviewer — pending Codex validation
- Optional roles: none

## Coder Output

- Changed files:
  | File | Change |
  |------|--------|
  | `mcp-server/src/tools/diagnostics-tools.ts` | NEW — `zorivest_diagnose` with safe-fetch, stub metrics |
  | `mcp-server/tests/diagnostics-tools.test.ts` | NEW — 9 unit tests |
  | `mcp-server/src/index.ts` | MODIFIED — added import + registration |
- Design notes / ADRs referenced:
  Stub `metricsCollector` pattern (inline object with `getUptimeMinutes()` and `getSummary(verbose)`). Separate `safeFetch()` utility using try/catch → null.
- Commands run:
  `cd mcp-server && npx vitest run tests/diagnostics-tools.test.ts`
- Results:
  9 tests passed (20ms)

## Tester Output

- Commands run:
  - `cd mcp-server && npx vitest run tests/diagnostics-tools.test.ts` → 9/9 ✅
  - `cd mcp-server && npx vitest run` → 39/39 ✅ (full regression)
- Pass/fail matrix:
  | Test | Status |
  |------|--------|
  | Returns full report when backend reachable (correct guard schema) | ✅ |
  | Reports unreachable when backend is down | ✅ |
  | Never reveals API keys in provider list | ✅ |
  | Returns providers: [] when provider endpoint returns 404 | ✅ |
  | Includes per-tool metrics when verbose=true | ✅ |
  | Returns summary-only metrics when verbose=false | ✅ |
  | Returns "unavailable" for auth-dependent fields | ✅ |
  | Passes auth headers to mcp-guard and market-data endpoints | ✅ |
  | Registers tool with correct annotations and _meta | ✅ |
- Repro failures:
  None.
- Coverage/test gaps:
  Stub metrics returns zero values — real MetricsCollector coverage deferred to MEU-39.
- Evidence bundle location:
  This handoff + test output.
- FAIL_TO_PASS / PASS_TO_PASS result:
  All tests written before implementation (TDD Red). All passed after implementation (Green).
- Mutation score:
  Not run.
- Contract verification status:
  FIC acceptance criteria verified by functional tests. Metadata annotations verified via listTools discovery test.

## Reviewer Output

- Findings by severity:
  Pending Codex validation.
- Open questions:
  None.
- Verdict:
  Pending.
- Residual risk:
  Stub metrics returns zeros — acceptable until MEU-39.
- Anti-deferral scan result:
  Clean. No TODO/FIXME/NotImplementedError in `diagnostics-tools.ts`.

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status:
  Implementation complete. 9/9 tests green. Awaiting Codex reviewer validation.
- Next steps:
  Codex validation pass, then git commit.
