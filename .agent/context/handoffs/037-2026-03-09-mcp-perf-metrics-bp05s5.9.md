# Task Handoff

## Task

- **Date:** 2026-03-09
- **Task slug:** mcp-perf-metrics
- **Owner role:** coder
- **Scope:** MEU-39 — MetricsCollector + withMetrics HOF

## Inputs

- User request:
  Implement per-tool performance metrics middleware per §5.9 spec.
- Specs/docs referenced:
  `docs/build-plan/05-mcp-server.md` §5.9, `docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/implementation-plan.md`
- Constraints:
  Ring buffer capped at 1000 entries per tool. Network tools excluded from slow warnings.

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
  | `mcp-server/src/middleware/metrics.ts` | NEW — MetricsCollector class, withMetrics HOF, singleton export |
  | `mcp-server/tests/metrics.test.ts` | NEW — 16 unit tests (AC-1 through AC-8 + composition proof AC-10) |
  | `mcp-server/src/tools/diagnostics-tools.ts` | MODIFIED — replaced stub metricsCollector with real import |
- Design notes / ADRs referenced:
  `metricsCollector` is a module-level singleton. `withMetrics` accepts an optional collector for testability. Network tools excluded via `NETWORK_TOOLS` Set.
- Commands run:
  `cd mcp-server && npx vitest run tests/metrics.test.ts`
- Results:
  16 tests passed

## Tester Output

- Commands run:
  - `cd mcp-server && npx vitest run tests/metrics.test.ts` → 16/16 ✅
  - `cd mcp-server && npx vitest run` → 74/74 ✅ (full regression)
  - `cd mcp-server && npx tsc --noEmit` → clean ✅
  - `cd mcp-server && npm run lint` → 2 warnings (expected for composition `as any` in trade-tools.ts) ✅
  - `cd mcp-server && npm run build` → clean ✅
- Pass/fail matrix:
  | Test | AC | Status |
  |------|-----|--------|
  | records latency and computes percentiles | AC-1, AC-3 | ✅ |
  | tracks error count and rate | AC-1 | ✅ |
  | warns when error rate exceeds 10% | AC-5 | ✅ |
  | warns when p95 exceeds 2000ms for non-network tool | AC-6 | ✅ |
  | excludes network tools from slow warnings | AC-7 | ✅ |
  | uses ring buffer to bound memory | AC-2 | ✅ |
  | omits per_tool when verbose=false | AC-4 | ✅ |
  | computes session-level totals and rates | AC-1 | ✅ |
  | identifies slowest and most-errored tools | AC-1 | ✅ |
  | tracks average payload size | AC-1 | ✅ |
  | records successful call metrics | AC-8 | ✅ |
  | records failed call metrics and re-throws | AC-8 | ✅ |
  | records isError results as errors | AC-8 | ✅ |
  | exports a singleton MetricsCollector instance | AC-9 | ✅ |
  | composition: both metrics and guard layers execute | AC-10 | ✅ |
  | composition: guard-blocked call recorded as error | AC-10 | ✅ |
- Repro failures: None.
- Coverage/test gaps:
  Composition proof (withMetrics+withGuard) in separate MEU-38+39 section. Diagnostics swap verified by existing diagnostics-tools.test.ts (9/9 still pass).
- Evidence bundle location: This handoff + test output.
- FAIL_TO_PASS / PASS_TO_PASS result:
  All tests written before implementation (TDD Red). All passed after implementation (Green).
- Mutation score: Not run.
- Contract verification status:
  FIC AC-1 through AC-9 verified by functional tests. AC-10 (composition proof) verified in separate describe block.

## Reviewer Output

- Findings by severity: Pending Codex validation.
- Open questions: None.
- Verdict: Pending.
- Residual risk: None identified.
- Anti-deferral scan result:
  Clean. No TODO/FIXME/NotImplementedError in `metrics.ts`.

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status:
  Implementation complete. 16/16 tests green. 74/74 full regression green. Awaiting Codex reviewer validation.
- Next steps:
  Codex validation pass, then project closeout (reflection, metrics, pomera state, commit).
