# MCP Guard, Metrics & Discovery — Implementation Plan

> Project: `mcp-guard-metrics-discovery` | MEUs: 39, 38, 41 | Date: 2026-03-09

## Goal

Implement the three remaining MCP server infrastructure middleware and meta-tools: per-tool performance metrics (`MetricsCollector` + `withMetrics`), MCP guard circuit breaker middleware (`guardCheck` + `withGuard`), and discovery meta-tools (`ToolsetRegistry` + 4 tools). These collectively enable tool access control, observability, and dynamic toolset management.

---

## MEU Scope Boundaries

> [!IMPORTANT]
> **ToolsetRegistry boundary** — MEU-41 creates the `ToolsetRegistry` *class* (data structure: register/get/getAll/markLoaded). MEU-42 adds the startup behavior (`--toolsets` CLI, `ZORIVEST_TOOLSET_CONFIG` env var, client detection, `registerToolsForClient()`). This is a deliberate scope split: MEU-41 ships the skeleton that discovery tools depend on; MEU-42 owns the authoritative loading logic.
>
> **Middleware composition boundary** — MEU-38/39 ship the middleware modules *and* prove composition works on at least one registered tool. MEU-42 owns the full `registerToolsForClient()` flow that applies middleware to all tools via the registry.

---

## Proposed Changes

### MEU-39 — Performance Metrics Middleware (`mcp-perf-metrics`)

> Build Plan: [05-mcp-server.md §5.9](file:///p:/zorivest/docs/build-plan/05-mcp-server.md)

#### [NEW] [metrics.ts](file:///p:/zorivest/mcp-server/src/middleware/metrics.ts)

- `MetricsCollector` class: per-tool latency, call counts, error rates, payload sizes
- Ring buffer (last 1000 entries per tool) for bounded memory
- `getSummary(verbose)`: session uptime, total calls, error rate, calls/minute, slowest/most-errored tool
- Auto-warnings: >10% error rate, >2000ms p95 (non-network tools excluded)
- Network tools exclusion set: `get_stock_quote`, `get_market_news`, `get_sec_filings`, `search_ticker`
- `withMetrics<T>(toolName, handler)` HOF wrapper
- Singleton `metricsCollector` export

#### [MODIFY] [diagnostics-tools.ts](file:///p:/zorivest/mcp-server/src/tools/diagnostics-tools.ts)

- Replace stub `metricsCollector` (lines 16-36) with real import from `middleware/metrics.ts`
- Update import statement: `import { metricsCollector } from '../middleware/metrics.js'`

#### [NEW] [metrics.test.ts](file:///p:/zorivest/mcp-server/tests/metrics.test.ts)

Tests from spec:
- Records latency and computes percentiles (p50, p95)
- Tracks error count and rate
- Warns when error rate >10%
- Excludes network tools from slow warnings
- Ring buffer bounds memory (2000 entries → min ≥ 1000)
- `withMetrics` wrapper records successful calls
- `withMetrics` wrapper records failed calls

---

### MEU-38 — MCP Guard Middleware (`mcp-guard`)

> Build Plan: [05-mcp-server.md §5.6](file:///p:/zorivest/docs/build-plan/05-mcp-server.md) | REST routes: [04g-api-system.md](file:///p:/zorivest/docs/build-plan/04g-api-system.md)

#### [NEW] [mcp-guard.ts](file:///p:/zorivest/mcp-server/src/middleware/mcp-guard.ts)

- `guardCheck()`: POST `/api/v1/mcp-guard/check` with auth headers
- `withGuard<T>(handler)` HOF wrapper: blocks with descriptive MCP error when `allowed=false`
- Error text includes reason and unlock guidance (GUI + `zorivest_emergency_unlock` tool)

#### [NEW] [guard.test.ts](file:///p:/zorivest/mcp-server/tests/guard.test.ts)

Tests from spec:
- Allows tool execution when guard returns `allowed: true`
- Blocks tool execution when guard is locked (with reason)
- Blocks when rate limit exceeded
- Handles fetch failure gracefully (guard check network error → block as safety default)

---

### MEU-41 — Discovery Meta-Tools (`mcp-discovery`)

> Build Plan: [05j-mcp-discovery.md](file:///p:/zorivest/docs/build-plan/05j-mcp-discovery.md) | Registry: [05-mcp-server.md §5.11](file:///p:/zorivest/docs/build-plan/05-mcp-server.md)

#### [NEW] [registry.ts](file:///p:/zorivest/mcp-server/src/toolsets/registry.ts)

- `ToolsetDefinition` interface: name, description, tools, register, loaded, alwaysLoaded
- `ToolsetRegistry` class: register, getAll, get, markLoaded
- Singleton `toolsetRegistry` export
- **Scope:** Data structure only. No `--toolsets` CLI, config loading, or client detection (MEU-42)

#### [NEW] [discovery-tools.ts](file:///p:/zorivest/mcp-server/src/tools/discovery-tools.ts)

4 tools per spec:
1. `list_available_toolsets` — lists all toolset groups (read-only, in-memory)
2. `describe_toolset` — returns tool details for a named toolset
3. `enable_toolset` — dynamically registers tools + sends `notifications/tools/list_changed`
4. `get_confirmation_token` — calls `POST /api/v1/confirmation-tokens` for destructive ops

Response contracts:
- `list_available_toolsets`, `describe_toolset`, `enable_toolset`: standard `{ success, data, error }` envelope
- `get_confirmation_token`: **flat canonical payload** `{ token, action, params_summary, expires_in_seconds, instruction }` per [05j L219-228](file:///p:/zorivest/docs/build-plan/05j-mcp-discovery.md) and [04c L130-148](file:///p:/zorivest/docs/build-plan/04c-api-auth.md)

All annotated with `alwaysLoaded: true`, toolset: `discovery`.

#### [NEW] [discovery-tools.test.ts](file:///p:/zorivest/mcp-server/tests/discovery-tools.test.ts)

Tests from spec:
- `list_available_toolsets` returns all registered toolsets with counts
- `describe_toolset` returns tool details for known toolset
- `describe_toolset` returns isError for unknown toolset
- `enable_toolset` registers tools and sends notification on dynamic client
- `enable_toolset` returns error on static client
- `enable_toolset` returns info if already loaded
- `enable_toolset` blocked when MCP Guard is locked (testing-strategy L374)
- `get_confirmation_token` calls REST API — returns flat `{ token, action, params_summary, expires_in_seconds, instruction }`
- `get_confirmation_token` returns isError for non-destructive/unknown action

---

### Infrastructure & Index Wiring

#### [MODIFY] [index.ts](file:///p:/zorivest/mcp-server/src/index.ts)

- Import and register discovery tools
- **Proof-of-composition:** Wrap at least one existing tool handler (e.g., `get_settings`) with `withMetrics(withGuard(handler))` per [§5.14 composition order](file:///p:/zorivest/docs/build-plan/05-mcp-server.md): `Tool call → withMetrics → withGuard → handler`
- Full registry-driven composition for all tools deferred to MEU-42

---

### Project Artifacts

#### [MODIFY] `docs/BUILD_PLAN.md`

- Update MEU-38, 39, 41 status from ⬜ to ✅ (after approval)
- Update Phase 5 completed count in summary table

#### [MODIFY] `.agent/context/meu-registry.md`

- Update MEU-38, 39, 41 status to ✅ approved

#### [NEW] Handoff files

- `037-2026-03-09-mcp-perf-metrics-bp05s5.9.md`
- `038-2026-03-09-mcp-guard-bp05s5.6.md`
- `039-2026-03-09-mcp-discovery-bp05js5j.md`

---

## Spec Sufficiency

| MEU | Behavior | Source | Resolved? |
|-----|----------|--------|:---------:|
| 39 | MetricsCollector ring buffer, percentiles, warnings | Spec §5.9 | ✅ |
| 39 | withMetrics HOF, singleton export | Spec §5.9 | ✅ |
| 39 | Network tools excluded from slow warnings | Spec §5.9 | ✅ |
| 38 | guardCheck POST /mcp-guard/check | Spec §5.6 | ✅ |
| 38 | withGuard HOF blocks when allowed=false | Spec §5.6 | ✅ |
| 38 | Guard bypass for unguarded tools | Spec §5.6, §5.10 | ✅ |
| 38 | Fail-closed on network error (default; GUI toggle to fail-open deferred to Phase 6) | Human-approved ([ADR-0002](file:///p:/zorivest/docs/decisions/ADR-0002-mcp-guard-fail-closed-default.md)) | ✅ |
| 38+39 | `withMetrics(withGuard(handler))` composition proof | Spec §5.14; Local Canon (testing-strategy.md L120) | ✅ |
| 41 | ToolsetRegistry class (get, getAll, markLoaded) | Spec 05j (class definition only — startup behavior is MEU-42) | ✅ |
| 41 | 4 discovery tools with annotations | Spec 05j | ✅ |
| 41 | get_confirmation_token flat payload contract | Spec 05j L219-228, 04c L130-148 | ✅ |
| 41 | get_confirmation_token rejects non-destructive actions | Spec 05j L247; Local Canon (testing-strategy.md L375) | ✅ |
| 41 | enable_toolset sends notifications/tools/list_changed | Spec 05j | ✅ |
| 41 | enable_toolset blocked when guard is locked | Local Canon (testing-strategy.md L374) | ✅ |

---

## Feature Intent Contracts (FIC)

### MEU-39 FIC — MetricsCollector + withMetrics

| AC | Description | Source |
|----|-------------|--------|
| AC-1 | `record()` stores latency, payload size, error flag per tool | Spec §5.9 |
| AC-2 | Ring buffer caps at 1000 entries per tool | Spec §5.9 |
| AC-3 | `getSummary(true)` includes per-tool percentiles (p50, p95, p99) | Spec §5.9 |
| AC-4 | `getSummary(false)` omits per_tool object | Spec §5.9 |
| AC-5 | Auto-warning when error rate >10% | Spec §5.9 |
| AC-6 | Auto-warning when p95 >2000ms for non-network tools | Spec §5.9 |
| AC-7 | Network tools excluded from slow warnings | Spec §5.9 |
| AC-8 | `withMetrics()` records success and error metrics | Spec §5.9 |
| AC-9 | Diagnostics tool uses real MetricsCollector (no stub) | Spec §5.9 |

### MEU-38 FIC — guardCheck + withGuard

| AC | Description | Source |
|----|-------------|--------|
| AC-1 | `guardCheck()` calls POST /api/v1/mcp-guard/check with auth headers | Spec §5.6 |
| AC-2 | `withGuard()` passes through when `allowed: true` | Spec §5.6 |
| AC-3 | `withGuard()` returns MCP error with reason when `allowed: false` | Spec §5.6 |
| AC-4 | Error message includes unlock guidance | Spec §5.6 |
| AC-5 | Network failure → blocks (fail-closed default; GUI toggle to fail-open deferred to Phase 6) | Human-approved ([ADR-0002](file:///p:/zorivest/docs/decisions/ADR-0002-mcp-guard-fail-closed-default.md)) |

### MEU-38+39 FIC — Middleware Composition Proof

| AC | Description | Source |
|----|-------------|--------|
| AC-10 | `withMetrics(withGuard(handler))` composition executes both middleware layers on a registered tool | Spec §5.14; Local Canon (testing-strategy.md L120) |

### MEU-41 FIC — Discovery Tools + ToolsetRegistry

| AC | Description | Source |
|----|-------------|--------|
| AC-1 | `ToolsetRegistry.getAll()` returns all registered toolsets | Spec 05j |
| AC-2 | `list_available_toolsets` returns name, description, tool_count, loaded | Spec 05j |
| AC-3 | `describe_toolset` returns tool details for known toolset | Spec 05j |
| AC-4 | `describe_toolset` returns isError for unknown toolset | Spec 05j |
| AC-5 | `enable_toolset` registers tools when client supports listChanged | Spec 05j |
| AC-6 | `enable_toolset` returns error on static client | Spec 05j |
| AC-7 | `enable_toolset` returns already_loaded info | Spec 05j |
| AC-8 | `get_confirmation_token` calls POST /api/v1/confirmation-tokens, returns flat `{ token, action, params_summary, expires_in_seconds, instruction }` | Spec 05j L219-228, 04c L130-148 |
| AC-9 | All 4 tools have correct annotations and _meta | Spec 05j |
| AC-10 | `get_confirmation_token` returns isError for non-destructive/unknown action names | Spec 05j L247; Local Canon (testing-strategy.md L375) |
| AC-11 | `enable_toolset` blocked when MCP Guard is locked | Local Canon (testing-strategy.md L374) |

---

## Verification Plan

### Automated Tests

All tests are Vitest (TypeScript). Run from `mcp-server` directory:

```bash
# Per-MEU targeted tests
cd mcp-server && npx vitest run tests/metrics.test.ts        # MEU-39
cd mcp-server && npx vitest run tests/guard.test.ts          # MEU-38
cd mcp-server && npx vitest run tests/discovery-tools.test.ts # MEU-41

# Full MCP regression
cd mcp-server && npx vitest run
```

### TypeScript Quality Gate

```bash
# Type checking
cd mcp-server && npx tsc --noEmit

# Linting
cd mcp-server && npm run lint

# Production build
cd mcp-server && npm run build
```

> If `npm run lint` fails due to missing/incomplete eslint config, document the issue and create a waiver or fix the config inline.

### Python Regression

```bash
# Full Python regression (from repo root)
uv run pytest tests/ -v
```

### MEU Gate

```bash
uv run python tools/validate_codebase.py --scope meu
```

> Known issue: MEU gate may fail on Windows due to npx spawn issue (documented waiver from prior project).

---

## Task Table

| # | Task | owner_role | Deliverable | Validation | Status |
|---|------|-----------|-------------|------------|:------:|
| 1 | Approve plan | orchestrator | This document | `notify_user` with `BlockedOnUser: true` | ⬜ |
| 2 | Write FIC for MEU-39 | coder | In TDD tests | `cd mcp-server && npx vitest run tests/metrics.test.ts` (expect FAIL) | ⬜ |
| 3 | Write metrics.test.ts (RED) | coder | Test file | `cd mcp-server && npx vitest run tests/metrics.test.ts` (expect FAIL) | ⬜ |
| 4 | Implement metrics.ts (GREEN) | coder | Middleware module | `cd mcp-server && npx vitest run tests/metrics.test.ts` (expect PASS) | ⬜ |
| 5 | Wire MetricsCollector into diagnostics-tools.ts | coder | Import swap | `cd mcp-server && npx vitest run tests/diagnostics-tools.test.ts` | ⬜ |
| 6 | Write FIC for MEU-38 | coder | In TDD tests | `cd mcp-server && npx vitest run tests/guard.test.ts` (expect FAIL) | ⬜ |
| 7 | Write guard.test.ts (RED) | coder | Test file | `cd mcp-server && npx vitest run tests/guard.test.ts` (expect FAIL) | ⬜ |
| 8 | Implement mcp-guard.ts (GREEN) | coder | Middleware module | `cd mcp-server && npx vitest run tests/guard.test.ts` (expect PASS) | ⬜ |
| 9 | Write FIC for MEU-41 | coder | In TDD tests | `cd mcp-server && npx vitest run tests/discovery-tools.test.ts` (expect FAIL) | ⬜ |
| 10 | Implement registry.ts | coder | Toolset registry | `cd mcp-server && npx tsc --noEmit` | ⬜ |
| 11 | Write discovery-tools.test.ts (RED) | coder | Test file | `cd mcp-server && npx vitest run tests/discovery-tools.test.ts` (expect FAIL) | ⬜ |
| 12 | Implement discovery-tools.ts (GREEN) | coder | Tool module | `cd mcp-server && npx vitest run tests/discovery-tools.test.ts` (expect PASS) | ⬜ |
| 13 | Wire discovery tools into index.ts | coder | Updated entrypoint | `cd mcp-server && npx vitest run` | ⬜ |
| 14 | Proof-of-composition: wrap one tool with withMetrics+withGuard | coder | Wired handler + test | `cd mcp-server && npx vitest run tests/metrics.test.ts` (composition test PASS) | ⬜ |
| 15 | Run tsc --noEmit | tester | Clean compile | `cd mcp-server && npx tsc --noEmit` | ⬜ |
| 16 | Run npm run lint | tester | Clean lint | `cd mcp-server && npm run lint` | ⬜ |
| 17 | Run npm run build | tester | Clean build | `cd mcp-server && npm run build` | ⬜ |
| 18 | Run full Vitest regression | tester | All tests pass | `cd mcp-server && npx vitest run` | ⬜ |
| 19 | Run full Python regression | tester | All tests pass | `uv run pytest tests/ -v` | ⬜ |
| 20 | Run MEU gate | tester | Gate output | `uv run python tools/validate_codebase.py --scope meu` | ⬜ |
| 21 | Codex validation handoff | reviewer | Validation report | `rg "verdict" .agent/context/handoffs/037-* .agent/context/handoffs/038-* .agent/context/handoffs/039-*` | ⬜ |
| 22 | Create 3 handoff files | coder | Handoff artifacts | `Get-ChildItem .agent/context/handoffs/037-*,.agent/context/handoffs/038-*,.agent/context/handoffs/039-*` | ⬜ |
| 23 | Update BUILD_PLAN.md + meu-registry.md | coder | Status updates | `rg "MEU-38" docs/BUILD_PLAN.md .agent/context/meu-registry.md; rg "MEU-39" docs/BUILD_PLAN.md; rg "MEU-41" docs/BUILD_PLAN.md` | ⬜ |
| 24 | Create reflection file | coder | Reflection artifact | `Get-ChildItem docs/execution/reflections/*mcp-guard*` | ⬜ |
| 25 | Update metrics table | coder | Metrics row | `rg "mcp-guard-metrics-discovery" docs/execution/metrics.md` | ⬜ |
| 26 | Save session state to pomera | coder | pomera note | MCP tool: `pomera_notes` `action: search` `search_term: Memory/Session/mcp-guard*` (verified at runtime via MCP) | ⬜ |
| 27 | Propose commit messages | coder | Messages | `rg "feat\|fix" .agent/context/handoffs/037-* .agent/context/handoffs/038-* .agent/context/handoffs/039-*` (verify messages appear in handoff) | ⬜ |
