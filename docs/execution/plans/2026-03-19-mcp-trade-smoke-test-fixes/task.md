# Task — MCP Trade Tool Smoke Test Fixes

> Project: `2026-03-19-mcp-trade-smoke-test-fixes`

## TDD Phase: Red → Green

- [/] Write failing test: `create_trade` accepts `confirmation_token` as argument
- [/] Write failing test: `confirmation_token` not forwarded to REST API body
- [ ] Verify tests fail (red phase) — `npm test -- trade-tools` in `mcp-server/`
- [ ] Fix: add `confirmation_token: z.string().optional()` to `trade-tools.ts` inputSchema
- [ ] Verify tests pass (green phase) — `npm test -- trade-tools` in `mcp-server/`

## Regression

- [ ] Full MCP test suite passes — `npm test` in `mcp-server/`

## Documentation

- [ ] Update `known-issues.md` — add MCP-CONFIRM entry (marked fixed)
- [ ] Verify `docs/BUILD_PLAN.md` — no stale refs needed (patch to ✅ MEU, no status change)
