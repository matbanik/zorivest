# Task Handoff

## Task

- **Date:** 2026-03-09
- **Task slug:** mcp-core-tools-bp05s5.1
- **Owner role:** coder
- **Scope:** MEU-31 — MCP server scaffold + core trade/calculator tools

## Inputs

- User request: Implement MEU-31 per `mcp-server-foundation` plan
- Specs/docs referenced:
  - `05-mcp-server.md` §5.1, §5.7
  - `05c-mcp-trade-analytics.md`
  - `05d-mcp-trade-planning.md`
  - `04c-api-auth.md` §API Key Management
  - `docs/execution/plans/2026-03-09-mcp-server-foundation/implementation-plan.md`
- Constraints:
  - Auth bootstrap takes pre-provisioned key only — no runtime key creation (admin-only per 04c)
  - Calculator fields must match actual API contract (`balance`, `risk_pct`, `stop_loss`, `target_price`)
  - ESLint must pass for quality gate (`validate_codebase.py:380`)

## Coder Output

- Changed files:

| File | Change |
|------|--------|
| `mcp-server/package.json` | [NEW] Node manifest: MCP SDK, Zod, TS, Vitest, ESLint |
| `mcp-server/tsconfig.json` | [NEW] ES2022, NodeNext, strict mode |
| `mcp-server/eslint.config.mjs` | [NEW] Flat ESLint config for TS |
| `mcp-server/vitest.config.ts` | [NEW] Vitest with globals, 30s timeout |
| `mcp-server/src/index.ts` | [NEW] MCP server entry point with StdioTransport, bootstrapAuth |
| `mcp-server/src/utils/api-client.ts` | [NEW] `bootstrapAuth(apiKey)`, `getAuthHeaders()`, `fetchApi()`, `McpResult` |
| `mcp-server/src/tools/trade-tools.ts` | [NEW] 5 trade tools (create, list, attach_screenshot, get_trade_screenshots, get_screenshot) |
| `mcp-server/src/tools/calculator-tools.ts` | [NEW] `calculate_position_size` tool |
| `tests/trade-tools.test.ts` | [NEW] 7 unit tests (mocked fetch) |
| `tests/calculator-tools.test.ts` | [NEW] 2 unit tests (mocked fetch) |

- Design notes:
  - **Auth model:** `bootstrapAuth(apiKey)` exchanges pre-provisioned key for session token via `POST /auth/unlock`. Never creates keys.
  - **SDK overload:** Uses `tool(name, description, paramsSchema, cb)` — 4-arg form. Annotations dropped from Day-1 due to SDK type fragility.
  - **Calculator contract mismatch:** Build plan used `account_balance`/`risk_percent`/`stop_loss_price` but actual API uses `balance`/`risk_pct`/`stop_loss`/`target_price`. Aligned to live API.

- Commands run:
  - `npm install` → 248 packages, 0 vulnerabilities
  - `npx tsc --noEmit` → clean
  - `npx eslint src/ --max-warnings 0` → clean
  - `npx vitest run` → 9 passed

## Tester Output

- Pass/fail matrix:

| Test | AC | Result |
|------|-----|--------|
| `create_trade > calls POST /trades with correct payload` | AC-1 | ✅ |
| `create_trade > defaults time to current ISO string` | AC-1 | ✅ |
| `list_trades > calls GET /trades with query params` | AC-2 | ✅ |
| `list_trades > calls GET /trades without query` | AC-2 | ✅ |
| `attach_screenshot > sends multipart POST` | AC-3 | ✅ |
| `get_trade_screenshots > calls GET /trades/{id}/images` | AC-4 | ✅ |
| `get_screenshot > returns mixed content` | AC-5 | ✅ |
| `calculate_position_size > calls POST with all params` | AC-6 | ✅ |
| `calculate_position_size > returns error envelope` | AC-7 | ✅ |

- Negative cases: API failure envelope (422), missing params (Zod validation)
- Anti-placeholder: `rg "TODO|FIXME|NotImplementedError" mcp-server/src/` → clean

## Reviewer Output

- Findings by severity: None (pending Codex review)
- Verdict: pending

## Final Summary

- Status: MEU-31 implementation complete, 9 unit tests passing
- Next steps: Codex validation
