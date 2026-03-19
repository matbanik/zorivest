# MCP Trade Smoke Test Fixes + GUI Trades — Reflection

**Date**: 2026-03-19
**Project**: mcp-trade-smoke-test-fixes (+ ad-hoc GUI trades work)
**Phase**: P5 MCP Server + P6 GUI
**Session length**: ~1,973 lines / 14 friction points

## What Went Well

1. **Live MCP smoke test as discovery tool** — Running every MCP tool against the live backend immediately surfaced the `confirmation_token` schema gap. This "test the whole surface" approach found a critical bug that unit tests alone missed because the MCP SDK silently strips unknown keys.

2. **TDD discipline for the fix** — Wrote 4 AC tests covering schema acceptance, body exclusion, static-mode round-trip, and dynamic-mode backward compat. The red phase correctly identified AC-2 as the failing test (not AC-1 as initially assumed), which proved the schema stripping theory.

3. **Full round-trip validation** — Minted a real token → created a trade → verified it in the GUI → created 3 more → deleted 1, all via MCP. The GUI's 5-second auto-refresh showed trades appearing/disappearing in real time.

4. **Meta-review → emerging standards pipeline** — Extracted 16 standards from session friction, created a templatized living doc, and linked it into 3 workflows + AGENTS.md for automatic LLM steering in future sessions.

## What I Learned

1. **MCP SDK Zod behavior: strip, not passthrough** — The MCP TS SDK applies `.strict()` or `.strip()` on Zod schemas by default. Any field not explicitly declared in the tool's input schema is silently removed before reaching the handler. This means middleware that reads undeclared fields will never see them.

2. **`dist/` is the truth for MCP** — The MCP server runs `node dist/index.js`, not source TS. Editing `src/` without `npm run build` is invisible. This cost 2 IDE restarts.

3. **SQLite `CAST(datetime AS TEXT)` is unusable** — It produces an opaque format. Must use `strftime('%Y-%m-%d %H:%M', column)` for human-searchable datetime text.

4. **Scope expansion during TDD is debt, not velocity** — Adding `delete_trade`, refresh button, search, pagination, and command palette fixes during a TDD session meant the handoff no longer matched the plan. The critical review correctly flagged this as F3/F4.

## What Went Wrong

1. **Backend startup friction** — AI didn't know the port (8765), env var (`ZORIVEST_DEV_UNLOCK`), or that `npm run dev` runs both frontend and backend. Cost 8+ tool calls and 2 failed starts. Fixed: created backend-startup SKILL.md.

2. **Fell back to curl instead of MCP** — When `create_trade` was blocked, the AI tried `curl` instead of diagnosing why the MCP tool was failing. User caught it — "why are you running curl?" This should have triggered a tool schema investigation.

3. **Scope creep without plan update** — User's organic requests ("add delete tool", "add refresh button", "add search") were executed immediately without updating the plan or task.md. The critical review correctly flagged the drift. Fixed: added scope-expansion CAUTION to TDD workflow.

4. **Command palette field mismatch** — `useDynamicEntries.ts` used `trade.id` / `trade.symbol` when the API returns `exec_id` / `instrument`. Classic mock-contract drift caught live.

## Process Improvements Applied

| Improvement | Target | Status |
|-------------|--------|--------|
| Backend Startup skill | `.agent/skills/backend-startup/SKILL.md` | ✅ Applied |
| Emerging Standards doc | `.agent/docs/emerging-standards.md` (16 standards) | ✅ Applied |
| MCP-DIST-REBUILD known issue | `.agent/context/known-issues.md` | ✅ Applied |
| OpenAPI spec drift check #10 | `.agent/skills/quality-gate/SKILL.md` | ✅ Applied |
| Scope Expansion Gate CAUTION | `.agent/workflows/tdd-implementation.md` | ✅ Applied |
| Emerging standards in `/create-plan` prereqs | `.agent/workflows/create-plan.md` | ✅ Applied |
| Emerging standards in `/critical-review-feedback` prereqs | `.agent/workflows/critical-review-feedback.md` | ✅ Applied |
| Emerging standards in `/tdd-implementation` prereqs | `.agent/workflows/tdd-implementation.md` | ✅ Applied |

## Metrics

| Metric | Value |
|--------|-------|
| MCP tests before | 194 |
| MCP tests after | 195 (+1: delete_trade) |
| Test files changed | 1 (`trade-tools.test.ts`) |
| Production files changed (MCP) | 2 (`trade-tools.ts`, `confirmation.ts`) |
| Production files changed (GUI) | 5 (`TradesLayout`, `TradesTable`, `TradeDetailPanel`, `TradeReportForm`, `McpServerStatusPanel`) |
| Production files changed (API) | 4 (`repositories.py`, `stubs.py`, `ports.py`, `trade_service.py`, `routes/trades.py`) |
| Agent docs created/updated | 6 (`emerging-standards.md`, `backend-startup/SKILL.md`, `known-issues.md`, `quality-gate/SKILL.md`, `AGENTS.md`, 3 workflows) |
| Friction points (critical) | 3 |
| Friction points (total) | 14 |
| Fixed during session | 12/14 |
| Open (recheck scope) | 2 (F3/F4: scope expansion → needs plan update or handoff narrowing) |

## Next Session Design Rules

1. **Always read backend-startup SKILL.md** before starting any backend or MCP testing.
2. **When MCP tool fails, diagnose the schema first** — check if the field exists in the Zod input schema before falling back to direct API calls.
3. **After any `mcp-server/src/` edit**, run `cd mcp-server && npm run build` before testing live.
4. **If user requests out-of-scope features during TDD**, pause and ask about plan update per the new Scope Expansion Gate.
5. **After any API route change**, run `uv run python tools/export_openapi.py --check openapi.committed.json`.
