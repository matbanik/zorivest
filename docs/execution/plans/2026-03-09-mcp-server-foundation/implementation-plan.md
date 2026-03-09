# MCP Server Foundation — Implementation Plan

> **Project slug:** `mcp-server-foundation`
> **MEUs:** MEU-31, MEU-33, MEU-32 (execution order)
> **Build-plan sections:** [05 §core](file:///p:/zorivest/docs/build-plan/05-mcp-server.md), [05a](file:///p:/zorivest/docs/build-plan/05a-mcp-zorivest-settings.md), [05c §trade](file:///p:/zorivest/docs/build-plan/05c-mcp-trade-analytics.md), [05d §calculator](file:///p:/zorivest/docs/build-plan/05d-mcp-trade-planning.md)

---

## Goal

Scaffold the `mcp-server/` TypeScript project and implement the Day-1 MCP tool vertical slice: **8 tools** covering trade CRUD, screenshots, calculator, and settings — all proxying to the existing Python REST API via `fetch()`. Verify the full TS→Python round-trip with a live integration test.

---

## User Review Required

> [!IMPORTANT]
> **BUILD_PLAN.md drift detected.** The MEU Summary table shows `P0 — Phase 3/4 | Completed: 1` but all 9 MEUs (MEU-22..30) are ✅ approved. The Phase Status table also shows Phase 4 as `🟡 In Progress` despite completion. This plan fixes both.

> [!IMPORTANT]
> **Auth bootstrap scope.** The current REST API starts **locked** (`main.py:61 → db_unlocked = False`). All trade/settings/image routes are gated by `require_unlocked_db`, which returns 403 until `POST /api/v1/auth/unlock` is called with a valid API key. Per [05-mcp-server.md §5.7](file:///p:/zorivest/docs/build-plan/05-mcp-server.md#L196), the canonical auth flow is: **IDE provides `zrv_sk_...` key → MCP server exchanges it for a session token via `POST /auth/unlock` → caches session token for proxied calls**. The MCP server does NOT create keys — key creation is admin-only ([04c-api-auth.md §API Key Management](file:///p:/zorivest/docs/build-plan/04c-api-auth.md#L79)). This project implements `bootstrapAuth(apiKey)` which takes a pre-provisioned key as input, unlocks the DB, and caches the session token. For **unit tests** (mocked fetch), auth is irrelevant. For **integration tests**, the test harness creates a key via `POST /auth/keys` in `beforeAll` (test-only setup, not runtime behavior), then calls `bootstrapAuth()` with that key. The full §5.7 HTTP-header extraction model is deferred to MEU-38/42 (requires Streamable HTTP transport).

---

## Spec Sufficiency

### MEU-31: `mcp-core-tools` (Build-plan item 13)

| Behavior / Contract | Source | Resolved? |
|---|---|---|
| Project scaffold (package.json, tsconfig, vitest) | [dependency-manifest](file:///p:/zorivest/docs/build-plan/dependency-manifest.md) | ✅ Spec |
| Standard response envelope `{success, data, error}` | [05 §SDK Compat](file:///p:/zorivest/docs/build-plan/05-mcp-server.md#L1017) | ✅ Spec |
| `create_trade` tool (schema, fetch, response) | [05c](file:///p:/zorivest/docs/build-plan/05c-mcp-trade-analytics.md#L9) | ✅ Spec |
| `list_trades` tool | [05c](file:///p:/zorivest/docs/build-plan/05c-mcp-trade-analytics.md#L62) | ✅ Spec |
| `attach_screenshot` tool (base64→multipart) | [05c](file:///p:/zorivest/docs/build-plan/05c-mcp-trade-analytics.md#L95) | ✅ Spec |
| `get_trade_screenshots` tool | [05c](file:///p:/zorivest/docs/build-plan/05c-mcp-trade-analytics.md#L140) | ✅ Spec |
| `get_screenshot` tool (mixed content) | [05c](file:///p:/zorivest/docs/build-plan/05c-mcp-trade-analytics.md#L171) | ✅ Spec |
| `calculate_position_size` tool | [05d](file:///p:/zorivest/docs/build-plan/05d-mcp-trade-planning.md#L7) | ✅ Spec |
| Zod raw shape convention | [known-issues MCP-ZODSTRIP](file:///p:/zorivest/.agent/context/known-issues.md) | ✅ Local Canon |
| stdio transport (primary) | [known-issues MCP-HTTPBROKEN](file:///p:/zorivest/.agent/context/known-issues.md) | ✅ Local Canon |
| MCP SDK v1.x import paths | [05 §SDK](file:///p:/zorivest/docs/build-plan/05-mcp-server.md#L1010) | ✅ Spec |
| Entry point bootstrap (McpServer + StdioTransport) | MCP SDK npm docs | ✅ Research-backed |
| tsconfig.json settings | MCP SDK examples | ✅ Research-backed |

### MEU-33: `mcp-settings` (Build-plan item 15b)

| Behavior / Contract | Source | Resolved? |
|---|---|---|
| `get_settings` tool | [05a](file:///p:/zorivest/docs/build-plan/05a-mcp-zorivest-settings.md#L7) | ✅ Spec |
| `update_settings` tool | [05a](file:///p:/zorivest/docs/build-plan/05a-mcp-zorivest-settings.md#L49) | ✅ Spec |
| String-valued settings boundary | [05a §convention](file:///p:/zorivest/docs/build-plan/05a-mcp-zorivest-settings.md#L84) | ✅ Spec |

### MEU-32: `mcp-integration-test` (Build-plan item 14)

| Behavior / Contract | Source | Resolved? |
|---|---|---|
| Live Python API spawn + health poll | [testing-strategy §Approach 3](file:///p:/zorivest/docs/build-plan/testing-strategy.md#L42) | ✅ Spec |
| `create_trade` round-trip assertion | [testing-strategy §Live Example](file:///p:/zorivest/docs/build-plan/testing-strategy.md#L76) | ✅ Spec |

**Gaps resolved:** 4 findings from critical review corrected (auth bootstrap, `create_trade` `time` field, ESLint scaffold, Phase 4 status).

---

## Proposed Changes

### MCP Server Scaffold

> Creates the entire `mcp-server/` directory from scratch.

#### [NEW] [package.json](file:///p:/zorivest/mcp-server/package.json)

Node.js project manifest with:
- `@modelcontextprotocol/sdk@^1.26.0`, `zod` as runtime deps
- `typescript`, `vitest`, `@types/node`, `tsx`, `eslint`, `@typescript-eslint/parser`, `@typescript-eslint/eslint-plugin` as dev deps
- Scripts: `build`, `dev`, `test`, `lint`, `start`

#### [NEW] [tsconfig.json](file:///p:/zorivest/mcp-server/tsconfig.json)

TypeScript config: `module: "NodeNext"`, `target: "ES2022"`, `outDir: "dist/"`, strict mode.

#### [NEW] [eslint.config.mjs](file:///p:/zorivest/mcp-server/eslint.config.mjs)

ESLint flat config for TypeScript. Required because `validate_codebase.py` runs `npx eslint src/ --max-warnings 0` when `mcp-server/` exists (line 380-383). Uses `@typescript-eslint/parser` + recommended rules.

#### [NEW] [vitest.config.ts](file:///p:/zorivest/mcp-server/vitest.config.ts)

Vitest configuration with `globals: true` for test environment.

---

### MEU-31: Core Trade + Calculator Tools

#### [NEW] [src/index.ts](file:///p:/zorivest/mcp-server/src/index.ts)

MCP server entry point:
- Creates `McpServer` instance with name "zorivest" and version "0.1.0"
- Connects via `StdioServerTransport`
- Imports and calls all `register*Tools(server)` functions
- Handles startup errors gracefully

#### [NEW] [src/utils/api-client.ts](file:///p:/zorivest/mcp-server/src/utils/api-client.ts)

Shared utilities:
- `API_BASE` constant from env (`ZORIVEST_API_URL ?? 'http://localhost:8765/api/v1'`)
- `bootstrapAuth(apiKey: string)` — takes a pre-provisioned API key, exchanges it for a session token via `POST /auth/unlock`, caches the session token. Does NOT create keys (key creation is admin-only per [04c](file:///p:/zorivest/docs/build-plan/04c-api-auth.md#L79)). Called once at MCP server startup with key from env (`ZORIVEST_API_KEY`) or passed by IDE.
- `getAuthHeaders()` — returns `{ Authorization: 'Bearer <session_token>' }` after bootstrap. Throws if not yet authenticated.
- `fetchApi()` helper wrapping fetch + auth headers + response envelope
- `McpResult` type

#### [NEW] [src/tools/trade-tools.ts](file:///p:/zorivest/mcp-server/src/tools/trade-tools.ts)

`registerTradeTools(server)` function implementing:
- `create_trade` — POST /trades with dedup; includes `time` field (ISO 8601 string, defaults to `new Date().toISOString()` if omitted by agent) to match `CreateTradeRequest` schema in `trades.py:27`
- `list_trades` — GET /trades with pagination
- `attach_screenshot` — POST multipart with base64→binary
- `get_trade_screenshots` — GET /trades/{id}/images
- `get_screenshot` — GET /images/{id} + /images/{id}/full (mixed MCP content)

#### [NEW] [src/tools/calculator-tools.ts](file:///p:/zorivest/mcp-server/src/tools/calculator-tools.ts)

`registerCalculatorTools(server)` function implementing:
- `calculate_position_size` — POST /calculator/position-size

---

### MEU-33: Settings Tools

#### [NEW] [src/tools/settings-tools.ts](file:///p:/zorivest/mcp-server/src/tools/settings-tools.ts)

`registerSettingsTools(server)` function implementing:
- `get_settings` — GET /settings or /settings/{key}
- `update_settings` — PUT /settings with key-value map

---

### MEU-31/33: Vitest Unit Tests (Mocked Fetch)

#### [NEW] [tests/trade-tools.test.ts](file:///p:/zorivest/mcp-server/tests/trade-tools.test.ts)

Unit tests for all 5 trade tools:
- Mock `global.fetch` responses
- Verify correct REST endpoints and methods called
- Verify Zod input validation (invalid inputs rejected)
- Verify standard response envelope structure
- Verify mixed content for `get_screenshot`

#### [NEW] [tests/calculator-tools.test.ts](file:///p:/zorivest/mcp-server/tests/calculator-tools.test.ts)

Unit tests for `calculate_position_size`:
- Verify POST to correct endpoint
- Verify all input params forwarded
- Verify response envelope

#### [NEW] [tests/settings-tools.test.ts](file:///p:/zorivest/mcp-server/tests/settings-tools.test.ts)

Unit tests for settings tools:
- `get_settings` with/without key filter
- `update_settings` with key-value map
- String-valued boundary verification

---

### MEU-32: Integration Test

#### [NEW] [tests/integration.test.ts](file:///p:/zorivest/mcp-server/tests/integration.test.ts)

Live API integration test (Approach 3):
- `beforeAll`: spawn Python API process → poll `/health` → **test setup only:** create API key via `POST /auth/keys` (not runtime behavior, just harness setup) → unlock DB via `POST /auth/unlock` with returned key → cache session token
- `afterAll`: kill spawned process
- Test: `create_trade` round-trip (POST /trades with `time` → verify response)
- Test: `list_trades` round-trip (GET /trades → verify array)
- Test: `get_settings` round-trip (GET /settings → verify map)
- Test: `calculate_position_size` round-trip (POST /calculator/position-size → verify result)

---

### BUILD_PLAN.md Maintenance

#### [MODIFY] [BUILD_PLAN.md](file:///p:/zorivest/docs/BUILD_PLAN.md)

1. Fix Phase Status table: Phase 4 → `✅ Completed` (line 63, currently shows `🟡 In Progress`)
2. Fix MEU Summary table: Phase 3/4 completed count `1` → `9`
3. Update Phase 5 status to `🟡 In Progress` with date
4. Update MEU-31, MEU-32, MEU-33 status to ✅ after execution
5. Update MEU Summary Phase 5 completed count

#### [MODIFY] [meu-registry.md](file:///p:/zorivest/.agent/context/meu-registry.md)

Add Phase 4 and Phase 5 sections with MEU status rows.

---

## Task Table

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 1 | Scaffold `mcp-server/` project | coder | package.json, tsconfig, vitest.config, eslint.config.mjs | `npm install` + `npx tsc --noEmit` + `npx eslint src/ --max-warnings 0` succeeds | ⬜ |
| 2 | MEU-31 FIC: write trade + calculator tool tests (Red) | coder | tests/trade-tools.test.ts, tests/calculator-tools.test.ts | `npx vitest run` — all FAIL | ⬜ |
| 3 | MEU-31: implement trade + calculator tools (Green) | coder | src/tools/trade-tools.ts, src/tools/calculator-tools.ts, src/index.ts, src/utils/api-client.ts | `npx vitest run` — all PASS | ⬜ |
| 4 | MEU-33 FIC: write settings tool tests (Red) | coder | tests/settings-tools.test.ts | `npx vitest run` — settings FAIL | ⬜ |
| 5 | MEU-33: implement settings tools (Green) | coder | src/tools/settings-tools.ts | `npx vitest run` — all PASS | ⬜ |
| 6 | MEU-32: write + run integration test | coder | tests/integration.test.ts | `npx vitest run tests/integration.test.ts` with live Python API | ⬜ |
| 7 | Create handoffs (032, 033, 034) | coder | 3 handoff files in .agent/context/handoffs/ | Files exist with evidence bundle | ⬜ |
| 8 | Update BUILD_PLAN.md (fix drift + Phase 5 status) | coder | BUILD_PLAN.md edits | `Completed` count correct, Phase 5 = In Progress | ⬜ |
| 9 | Update meu-registry.md | coder | Phase 4+5 rows added | Registry reflects ✅ for MEU-31..33 | ⬜ |
| 10 | MEU gate | tester | `uv run python tools/validate_codebase.py --scope meu` | Gate passes. **Known issue:** crashes on Windows with `FileNotFoundError` when spawning `npx`. Substitute checks: `tsc --noEmit` + `eslint` + `vitest run`. | ⬜ |
| 11 | Full regression | tester | `uv run pytest tests/ -v` | All existing Python tests pass | ⬜ |
| 12 | Reflection + metrics + pomera save + commit messages | coder | reflection, metrics, pomera note, commit messages | All artifacts created | ⬜ |

---

## FIC — MEU-31: `mcp-core-tools`

### Acceptance Criteria

| AC | Description | Source |
|----|-------------|--------|
| AC-1 | `create_trade` tool calls `POST /api/v1/trades` with payload including `time` field (ISO 8601) and returns standard envelope | Spec (05c) + Local Canon (trades.py:27) |
| AC-2 | `list_trades` tool calls `GET /api/v1/trades` with limit/offset query params | Spec (05c) |
| AC-3 | `attach_screenshot` decodes base64, creates multipart FormData, POSTs to `/trades/{id}/images` | Spec (05c) |
| AC-4 | `get_trade_screenshots` calls `GET /api/v1/trades/{id}/images` | Spec (05c) |
| AC-5 | `get_screenshot` returns mixed MCP content: text metadata + image (base64) | Spec (05c) |
| AC-6 | `calculate_position_size` calls `POST /api/v1/calculator/position-size` | Spec (05d) |
| AC-7 | All tools use standard response envelope `{success, data, error}` | Spec (05 §SDK) |
| AC-8 | MCP server bootstraps with `StdioServerTransport`, calls `bootstrapAuth(apiKey)` with pre-provisioned key from env, and registers all tools | Spec (05 §5.7) + Local Canon (auth_service.py) |
| AC-9 | Zod schemas use raw shapes (not `z.object()`) per MCP-ZODSTRIP workaround | Local Canon |
| AC-10 | All tools have correct annotation blocks (readOnlyHint, destructiveHint, idempotentHint) | Spec (05c, 05d) |
| AC-11 | ESLint config scaffolded; `npx eslint src/ --max-warnings 0` passes | Local Canon (validate_codebase.py:380) |

---

## FIC — MEU-33: `mcp-settings`

### Acceptance Criteria

| AC | Description | Source |
|----|-------------|--------|
| AC-1 | `get_settings` with no key calls `GET /api/v1/settings` | Spec (05a) |
| AC-2 | `get_settings` with key calls `GET /api/v1/settings/{key}` | Spec (05a) |
| AC-3 | `update_settings` calls `PUT /api/v1/settings` with JSON map body | Spec (05a) |
| AC-4 | Setting values are strings at the MCP boundary | Spec (05a) |
| AC-5 | Both tools return standard envelope `{success, data, error}` | Spec (05 §SDK) |

---

## FIC — MEU-32: `mcp-integration-test`

### Acceptance Criteria

| AC | Description | Source |
|----|-------------|--------|
| AC-1 | Test spawns Python API process and waits for `/health` ready | Spec (testing-strategy §3) |
| AC-2 | Test harness creates API key + unlocks DB in `beforeAll` (test-only setup, not runtime behavior) | Local Canon (auth_service.py, trades.py) |
| AC-3 | `create_trade` round-trip: POST /trades with `time` → verify response | Spec (testing-strategy) + Local Canon (trades.py:27) |
| AC-4 | Process is cleaned up after tests complete | Spec (testing-strategy §3) |
| AC-5 | Health poll timeout produces clear error message | Spec (testing-strategy) |

---

## Verification Plan

### Automated Tests

```bash
# 1. TypeScript compilation check
cd mcp-server && npx tsc --noEmit

# 2. ESLint (must pass for MEU gate)
cd mcp-server && npx eslint src/ --max-warnings 0

# 3. Vitest unit tests (mocked fetch)
cd mcp-server && npx vitest run

# 4. Integration test (requires live Python API — spawns, creates key, unlocks DB)
cd mcp-server && npx vitest run tests/integration.test.ts

# 5. Python regression (ensure nothing broke)
cd p:\zorivest && uv run pytest tests/ -v

# 6. MEU gate
cd p:\zorivest && uv run python tools/validate_codebase.py --scope meu
```

### Manual Verification

No manual verification needed — all checks are automated via Vitest and pytest.

---

## Handoff Naming

| MEU | Handoff File |
|-----|-------------|
| MEU-31 | `032-2026-03-09-mcp-core-tools-bp05s5.1.md` |
| MEU-33 | `033-2026-03-09-mcp-settings-bp05as5a.md` |
| MEU-32 | `034-2026-03-09-mcp-integration-test-bp05s5.1.md` |
