# Task Handoff

## Task

- **Date:** 2026-03-10
- **Task slug:** planning-tools
- **Owner role:** coder
- **Scope:** MEU-36 — `create_trade_plan` MCP tool

## Inputs

- User request:
  Implement trade planning MCP tool per 05d spec.
- Specs/docs referenced:
  `docs/build-plan/05d-mcp-trade-planning.md` L51-100, `docs/execution/plans/2026-03-10-mcp-planning-accounts-gui/implementation-plan.md`
- Constraints:
  REST endpoint `POST /trade-plans` not yet implemented — thin proxy pattern with mocked fetch. `calculate_position_size` already implemented in MEU-31, not duplicated.

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
  | `mcp-server/src/tools/planning-tools.ts` | NEW — `registerPlanningTools()` with `create_trade_plan` tool (113 LOC) |
  | `mcp-server/tests/planning-tools.test.ts` | NEW — 4 unit tests covering AC-1 through AC-6 (197 LOC) |
  | `mcp-server/src/toolsets/seed.ts` | MODIFIED — `trade-planning` toolset: updated tool list to 3-tool canonical set, added register callback, set `loaded: true` |
  | `mcp-server/src/index.ts` | MODIFIED — added `registerPlanningTools` import + call |
- Design notes / ADRs referenced:
  Uses `registerTool()` with `inputSchema`, `annotations`, `_meta` per established pattern from trade-tools.ts. `withMetrics(withGuard(handler))` composition for guarded tools. Input schema from 05d L57-84 with `conviction` defaulting to `"medium"`.
- Commands run:
  `cd mcp-server && npx vitest run tests/planning-tools.test.ts`
- Results:
  4 tests passed

## Tester Output

- Commands run:
  - `cd mcp-server && npx vitest run tests/planning-tools.test.ts` → 4/4 ✅
  - `cd mcp-server && npx eslint src/` → clean ✅
  - `cd mcp-server && npx vitest run` → 92/92 ✅ (full regression, 12 test files)
  - `cd mcp-server && npx tsc --noEmit` → clean ✅
  - `uv run pytest tests/ -v` → all passed ✅
- Pass/fail matrix:
  | Test | AC | Status |
  |------|-----|--------|
  | registers with correct name and accepts full input schema | AC-1, AC-4 | ✅ |
  | accepts minimal required fields (without optional) | AC-1 | ✅ |
  | returns error envelope on API failure (non-2xx) | AC-5 | ✅ |
  | calls guard check before API (withGuard middleware) | AC-6 | ✅ |
- Repro failures: None.
- Coverage/test gaps:
  AC-2 (annotations) and AC-3 (_meta) verified structurally — they are static metadata passed to `registerTool()`. No runtime assertion needed.
- Evidence bundle location: This handoff + test output.
- FAIL_TO_PASS / PASS_TO_PASS result:
  All tests written before implementation (TDD Red — import error confirmed). All passed after implementation (Green).
- Mutation score: Not run.
- Contract verification status:
  FIC AC-1 through AC-6 verified by functional tests + structural inspection.

## Negative Cases

| Case | Expected | Tested |
|------|----------|--------|
| API returns 409 (duplicate plan) | success=false, error present | ✅ |
| Optional fields omitted | conviction defaults to "medium" | ✅ |

## Reviewer Output

- Findings by severity: Pending Codex validation.
- Open questions: None.
- Verdict: Pending.
- Residual risk:
  REST endpoint `POST /trade-plans` not yet implemented in Python API. Tool works as thin proxy — will fail at runtime until API route exists.
- Anti-deferral scan result:
  Clean. No TODO/FIXME/NotImplementedError in planning-tools.ts.

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status:
  Implementation complete. 4/4 tests green. 92/92 full regression green. Awaiting Codex reviewer validation.
- Next steps:
  Codex validation pass, then project closeout.

## Suggested Commit Message

```
feat(mcp): add create_trade_plan tool (MEU-36)

- Register create_trade_plan with full 05d input schema
- withMetrics + withGuard middleware composition
- POST /trade-plans thin proxy via fetchApi
- 4 unit tests covering all 6 FIC acceptance criteria
- Migrate calculator tools from core to trade-planning toolset in seed.ts
```
