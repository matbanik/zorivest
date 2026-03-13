# Task Handoff — MEU-69: Watchlist MCP Tools

## Task

- **Date:** 2026-03-12
- **Task slug:** watchlist-mcp-tools
- **Owner role:** orchestrator
- **Scope:** Watchlist MCP Tools (MEU-69)
- **Build Plan ref:** bp05ds5d

## Inputs

- User request: Implement 5 Watchlist MCP tools in the trade-planning toolset
- Specs/docs referenced: `build-priority-matrix.md` item 34, `05d-mcp-trade-planning.md`, existing `planning-tools.ts` pattern
- Constraints: Follow existing `create_trade_plan` pattern — `registerTool`, zod schemas, annotations, `_meta`, `withMetrics(withGuard(...))`

## Role Plan

1. orchestrator — scoped from implementation-plan.md
2. coder — 5 tools + seed.ts update
3. tester — 10 new tests
4. reviewer — this handoff

## Coder Output

- Changed files:
  - `mcp-server/src/tools/planning-tools.ts` — Added 5 watchlist tools: `create_watchlist`, `list_watchlists`, `get_watchlist`, `add_to_watchlist`, `remove_from_watchlist`
  - `mcp-server/src/toolsets/seed.ts` — Updated `trade-planning` toolset: 3→8 tools, added 5 watchlist entries
  - `mcp-server/tests/planning-tools.test.ts` — Added 10 new tests (2 per tool)
- Design notes:
  - All tools follow exact `create_trade_plan` pattern
  - `list_watchlists` and `get_watchlist`: `readOnlyHint: true`, `idempotentHint: true`
  - `remove_from_watchlist`: `destructiveHint: true`, `idempotentHint: true`
  - Create/add tools: all hints false
  - All tools wrapped with `withMetrics(withGuard(...))`
- Commands run: `npx tsc --noEmit` (0 errors), `npx vitest run` (160 passed across 17 files)

## Tester Output

- Commands run:
  - `npx vitest run tests/planning-tools.test.ts --reporter=verbose` — 14 passed (4 existing + 10 new)
  - `npx vitest run` — 160 passed across 17 test files
- Pass/fail matrix:

| Test Suite | Pass | Fail |
|---|---|---|
| planning-tools.test.ts | 14 | 0 |
| Full MCP regression | 160 | 0 |

- Coverage: All 5 tools have happy-path + error-path tests (list_watchlists has both)
- FAIL_TO_PASS: All 10 new tests passed on first run (tools written before tests due to pattern simplicity)

## Reviewer Output

- Findings by severity: None
- Open questions: None
- Verdict: `ready_for_review`
- Residual risk: None — MCP tools proxy to REST API; business logic validated in MEU-68
- Anti-deferral scan: No TODO/FIXME in touched files

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:** —
- **Timestamp:** —

## Final Summary

- Status: MEU-69 complete — 5 tools registered, 10 new watchlist tests (14 total with 4 existing), all passing
- Annotation metadata: All 5 tools have `readOnlyHint`/`destructiveHint`/`idempotentHint` set per tool semantics in source; not asserted in tests (SDK does not expose annotation metadata on client side)
- Next steps: Canon doc updates (`04-rest-api.md`, `05d-mcp-trade-planning.md`, `05-mcp-server.md`), BUILD_PLAN/registry updates, project closeout
