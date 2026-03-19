# Task — MCP Trade Tool Smoke Test Fixes

> Project: `2026-03-19-mcp-trade-smoke-test-fixes`

## Task Table

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 1 | Write failing TDD test — schema accepts `confirmation_token` (AC-1) | Opus | `trade-tools.test.ts` new test | `npm test -- trade-tools` — test fails (red) | ✅ |
| 2 | Write failing TDD test — token not forwarded to API body (AC-3) | Opus | `trade-tools.test.ts` new test | `npm test -- trade-tools` — test fails (red) | ✅ |
| 3 | Write failing TDD test — static-mode confirmation round-trip (AC-2) | Opus | `trade-tools.test.ts` new test | `npm test -- trade-tools` — test fails (red) | ✅ |
| 4 | Write failing TDD test — dynamic-mode backward compat (AC-4) | Opus | `trade-tools.test.ts` new test | `npm test -- trade-tools` — test fails (red) | ✅ |
| 5 | Add `confirmation_token` to `create_trade` inputSchema | Opus | `trade-tools.ts` schema fix | `npm test -- trade-tools` — all tests pass (green) | ✅ |
| 6 | Run full MCP test suite | Opus | No regressions | `npm test` in `mcp-server/` — all 21 test files pass | ✅ |
| 7 | Update `known-issues.md` | Opus | MCP-CONFIRM entry (fixed) | `rg -c "MCP-CONFIRM" .agent/context/known-issues.md` returns 1 AND `rg "MCP-CONFIRM" -A 5 .agent/context/known-issues.md` contains `Fixed` | ✅ |
| 8 | Verify `docs/BUILD_PLAN.md` accuracy | Opus | MEU-35 still ✅ in both files | `rg -c "mcp-trade-analytics.*✅" docs/BUILD_PLAN.md` returns 1 AND `rg -c "MEU-35.*✅ approved" .agent/context/meu-registry.md` returns 1 | ✅ |
