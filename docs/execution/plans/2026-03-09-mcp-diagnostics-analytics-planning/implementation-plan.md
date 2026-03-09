# MCP Diagnostics & Trade Analytics

> Project: `mcp-diagnostics-analytics-planning` | MEUs: 34, 35 | Date: 2026-03-09
>
> MEU-36 (`create_trade_plan`) deferred — draft spec + REST route deferred to MEU-66/P2.
> Report tools (`create_report`, `get_report_for_trade`) deferred — REST route deferred to MEU-52/P1.

## Goal

Implement two MCP tool modules that extend the Zorivest MCP server with diagnostics and trade analytics capabilities. All tools proxy to existing REST API endpoints via `fetchApi()`.

---

## MEU → Tool Mapping

| MEU | Slug | Tools | New Files | Handoff |
|-----|------|:-----:|-----------|---------|
| MEU-34 | `mcp-diagnostics` | 1 | `diagnostics-tools.ts`, `diagnostics-tools.test.ts` | `035-2026-03-09-mcp-diagnostics-bp05bs5b.md` |
| MEU-35 | `mcp-trade-analytics` | 12 | `analytics-tools.ts`, `analytics-tools.test.ts` | `036-2026-03-09-mcp-trade-analytics-bp05cs5c.md` |

**Execution order:** MEU-34 → MEU-35 (smallest to largest; no cross-dependencies)

---

## Spec Sufficiency

### MEU-34: zorivest_diagnose

| Behavior / Contract | Source Type | Source | Resolved? | Notes |
|---|---|---|---|---|
| Tool params: `verbose` (bool, default false) | Spec | [05b §zorivest_diagnose](file:///p:/zorivest/docs/build-plan/05b-mcp-zorivest-diagnostics.md) | ✅ | |
| Output: JSON report with backend, version, database, guard, providers, mcp_server, metrics | Spec | 05b | ✅ | |
| Error posture: never throws, safe-fetch with null fallback | Spec | 05b | ✅ | |
| NOT guarded (callable even when guard is locked) | Spec | [05 §5.8](file:///p:/zorivest/docs/build-plan/05-mcp-server.md) | ✅ | |
| Annotations: readOnly=true, destructive=false, idempotent=true | Spec | 05b | ✅ | |
| `_meta`: toolset=core, alwaysLoaded=true | Spec | 05b | ✅ | |
| MetricsCollector dependency | Local Canon | 05 §5.9 spec (not yet implemented — MEU-39) | ✅ | Stub metrics; real collector comes in MEU-39 |
| Provider endpoint availability | Research-backed | Phase 8 `/market-data/providers` not yet registered | ✅ | Safe-fetch returns `providers: []` — partial availability explicitly tested |
| Unauthenticated/partial results | Spec | [testing-strategy.md](file:///p:/zorivest/docs/build-plan/testing-strategy.md):116-121 | ✅ | Auth-dependent fields report `"unavailable"` when session lacks token |

### MEU-35: Trade Analytics Tools (12 tools)

| Behavior / Contract | Source Type | Source | Resolved? | Notes |
|---|---|---|---|---|
| get_round_trips: GET /round-trips with account_id, status params | Spec | [05c §get_round_trips](file:///p:/zorivest/docs/build-plan/05c-mcp-trade-analytics.md) | ✅ | REST exists in round_trips.py |
| enrich_trade_excursion: POST /analytics/excursion/{id} | Spec | 05c | ✅ | REST exists in analytics.py |
| get_fee_breakdown: GET /fees/summary | Spec | 05c | ✅ | REST exists in fees.py |
| score_execution_quality: GET /analytics/execution-quality | Spec | 05c | ✅ | REST exists |
| estimate_pfof_impact: GET /analytics/pfof-report | Spec | 05c | ✅ | REST exists |
| get_expectancy_metrics: GET /analytics/expectancy | Spec | 05c | ✅ | REST exists |
| simulate_drawdown: GET /analytics/drawdown | Spec | 05c | ✅ | REST exists |
| get_strategy_breakdown: GET /analytics/strategy-breakdown | Spec | 05c | ✅ | REST exists |
| get_sqn: GET /analytics/sqn | Spec | 05c | ✅ | REST exists |
| get_cost_of_free: GET /analytics/cost-of-free | Spec | 05c | ✅ | REST exists |
| ai_review_trade: POST /analytics/ai-review | Spec | 05c | ✅ | REST exists |
| detect_options_strategy: POST /analytics/options-strategy | Spec | 05c | ✅ | REST exists |

> **Out of scope (deferred):** `create_report` and `get_report_for_trade` depend on REST routes deferred to MEU-52/P1. Will be implemented alongside that MEU.

---

## Proposed Changes

### MEU-34: Diagnostics Tool

#### [NEW] [diagnostics-tools.ts](file:///p:/zorivest/mcp-server/src/tools/diagnostics-tools.ts)

Single tool: `zorivest_diagnose`. Uses safe fetch pattern (try/catch → null). Calls REST endpoints in parallel: `/health`, `/version/`, `/mcp-guard/status`. The `/market-data/providers` endpoint is Phase 8 and not yet registered — the safe-fetch pattern returns `providers: []` when the endpoint is unavailable.

Returns structured JSON report with `backend`, `version`, `database`, `guard`, `providers`, `mcp_server`, `metrics` sections. Includes stub `metricsCollector` (placeholder until MEU-39 builds the real MetricsCollector). The stub returns process uptime and empty per-tool metrics.

When unauthenticated, auth-dependent fields report `"unavailable"` instead of failing.

#### [NEW] [diagnostics-tools.test.ts](file:///p:/zorivest/mcp-server/tests/diagnostics-tools.test.ts)

Tests:
- Returns full report when backend reachable (mock 3 fetch responses)
- Reports unreachable when backend is down (mock fetch rejection)
- Never reveals API keys in provider list
- Returns `providers: []` when provider endpoint returns 404 (Phase 8 not yet available)
- Includes per-tool metrics section when verbose=true
- Returns summary-only metrics when verbose=false
- Returns `"unavailable"` for auth-dependent fields when unauthenticated

#### [MODIFY] [index.ts](file:///p:/zorivest/mcp-server/src/index.ts)

Add import and registration call for `registerDiagnosticsTools(server)`.

---

### MEU-35: Trade Analytics Tools

#### [NEW] [analytics-tools.ts](file:///p:/zorivest/mcp-server/src/tools/analytics-tools.ts)

12 tools, all using `fetchApi()` with query string construction or POST body:
- `get_round_trips` → GET /round-trips
- `enrich_trade_excursion` → POST /analytics/excursion/{id}
- `get_fee_breakdown` → GET /fees/summary
- `score_execution_quality` → GET /analytics/execution-quality
- `estimate_pfof_impact` → GET /analytics/pfof-report
- `get_expectancy_metrics` → GET /analytics/expectancy
- `simulate_drawdown` → GET /analytics/drawdown
- `get_strategy_breakdown` → GET /analytics/strategy-breakdown
- `get_sqn` → GET /analytics/sqn
- `get_cost_of_free` → GET /analytics/cost-of-free
- `ai_review_trade` → POST /analytics/ai-review
- `detect_options_strategy` → POST /analytics/options-strategy

All annotated with `toolset: "trade-analytics"`, `alwaysLoaded: false`.

#### [NEW] [analytics-tools.test.ts](file:///p:/zorivest/mcp-server/tests/analytics-tools.test.ts)

Tests for all 12 analytics tools. Each test verifies:
- Correct REST endpoint called (URL + method)
- Query params / POST body forwarded correctly
- Standard envelope response structure

#### [MODIFY] [index.ts](file:///p:/zorivest/mcp-server/src/index.ts)

Add import and registration for `registerAnalyticsTools(server)`.

---

### BUILD_PLAN.md Hub Maintenance

#### [MODIFY] [BUILD_PLAN.md](file:///p:/zorivest/docs/BUILD_PLAN.md)

Update Phase 5 MEU status table:
- MEU-34: ⬜ → ✅
- MEU-35: ⬜ → ✅

MEU-36 remains ⬜ (deferred — draft spec + P2 REST dependency).

---

## Feature Intent Contracts (FIC)

### MEU-34 FIC: zorivest_diagnose

| AC | Description | Source |
|----|-------------|--------|
| AC-1 | Tool named `zorivest_diagnose` registered with `verbose: boolean` param (default false) | Spec: 05b |
| AC-2 | Returns JSON text with `backend.reachable`, `backend.status`, `version`, `database.unlocked`, `guard`, `providers[]`, `mcp_server.node_version`, `mcp_server.uptime_minutes`, `metrics` keys | Spec: 05b |
| AC-3 | Never throws — uses safe fetch (try/catch → null fallback) for all REST endpoints | Spec: 05b |
| AC-4 | Provider list never contains `api_key` field | Spec: 05b |
| AC-5 | Annotations: `readOnlyHint: true`, `destructiveHint: false`, `idempotentHint: true` | Spec: 05b |
| AC-6 | `_meta`: `toolset: "core"`, `alwaysLoaded: true` | Spec: 05b |
| AC-7 | `verbose=true` includes per-tool metrics; `verbose=false` includes summary only | Spec: 05b |
| AC-8 | Returns `providers: []` when `/market-data/providers` returns 404 (Phase 8) | Research-backed |
| AC-9 | Auth-dependent fields report `"unavailable"` when session lacks token | Spec: testing-strategy.md |

### MEU-35 FIC: Trade Analytics Tools

| AC | Description | Source |
|----|-------------|--------|
| AC-1 | 12 analytics tools registered with correct names per spec | Spec: 05c |
| AC-2 | Each tool calls the correct REST endpoint (URL + HTTP method) | Spec: 05c |
| AC-3 | Query params forwarded correctly for GET endpoints | Spec: 05c |
| AC-4 | POST body forwarded correctly for POST endpoints | Spec: 05c |
| AC-5 | All tools return fetchApi envelope (`{success, data?, error?}`) | Local Canon: api-client.ts |
| AC-6 | All analytics tools annotated with `readOnlyHint: true` (except `enrich_trade_excursion` which is `readOnlyHint: false`) | Spec: 05c |
| AC-7 | All tools have `_meta`: `toolset: "trade-analytics"`, `alwaysLoaded: false` | Spec: 05c |

---

## Task Table

| # | task | owner_role | deliverable | validation | status |
|---|------|------------|-------------|------------|--------|
| 1 | MEU-34: Write FIC → tests → `diagnostics-tools.ts` | coder | Source + tests | `cd mcp-server && npx vitest run tests/diagnostics-tools.test.ts` | ⬜ |
| 2 | MEU-34: Register in `index.ts` | coder | Modified index.ts | `cd mcp-server && npx tsc --noEmit` | ⬜ |
| 3 | MEU-34: MEU validation gate | tester | Gate pass | `uv run python tools/validate_codebase.py --scope meu` | ⬜ |
| 4 | MEU-34: Create handoff 035 | coder | Handoff file | `Test-Path .agent/context/handoffs/035-*.md` | ⬜ |
| 5 | MEU-35: Write FIC → tests → `analytics-tools.ts` | coder | Source + tests | `cd mcp-server && npx vitest run tests/analytics-tools.test.ts` | ⬜ |
| 6 | MEU-35: Register in `index.ts` | coder | Modified index.ts | `cd mcp-server && npx tsc --noEmit` | ⬜ |
| 7 | MEU-35: MEU validation gate | tester | Gate pass | `uv run python tools/validate_codebase.py --scope meu` | ⬜ |
| 8 | MEU-35: Create handoff 036 | coder | Handoff file | `Test-Path .agent/context/handoffs/036-*.md` | ⬜ |
| 9 | Update BUILD_PLAN.md + meu-registry.md | coder | MEU-34/35 status → ✅ | `rg -e MEU-34 -e MEU-35 docs/BUILD_PLAN.md .agent/context/meu-registry.md` | ⬜ |
| 10 | Run full regression | tester | All tests green | `cd mcp-server && npx vitest run` | ⬜ |
| 11 | Create reflection | coder | Reflection file | `Test-Path docs/execution/reflections/2026-03-09-mcp-diagnostics-analytics-planning-reflection.md` | ⬜ |
| 12 | Review deliverables | reviewer | Review verdict | `Test-Path .agent/context/handoffs/*mcp-diagnostics-analytics*` | ⬜ |
| 13 | Save session + commit messages | coder | Note + messages | `cd mcp-server && npx vitest run` (final green confirmation) | ⬜ |

---

## Verification Plan

### Automated Tests

All TypeScript tests use the established InMemoryTransport + mocked `global.fetch` pattern:

```bash
# Per-MEU (during TDD)
cd mcp-server && npx vitest run tests/diagnostics-tools.test.ts
cd mcp-server && npx vitest run tests/analytics-tools.test.ts

# Full TypeScript regression
cd mcp-server && npx vitest run

# Type checking
cd mcp-server && npx tsc --noEmit

# Linting
cd mcp-server && npx eslint src/ tests/
```

### MEU Validation Gate (per-MEU, mandatory)

```bash
# AGENTS.md §Execution Contract — required after each MEU
uv run python tools/validate_codebase.py --scope meu
```

This runs `pyright`, `ruff`, `pytest`, and anti-placeholder scan scoped to touched packages/files.

### Role Transitions

Explicit `orchestrator → coder → tester → reviewer` flow per AGENTS.md contract:
- **orchestrator**: Scope and plan (this document)
- **coder**: Write FIC → tests → implementation
- **tester**: Run MEU validation gate + full regression
- **reviewer**: Review deliverables and create handoff verdict

### Manual Verification

None required. All tools are thin proxies to existing REST endpoints. Each tool is unit-tested via InMemoryTransport + mocked `global.fetch`, which verifies tool registration, Zod schema validation, response formatting, and annotation metadata. The existing `integration.test.ts` (MEU-32) exercises REST endpoints directly and does NOT cover MCP tool paths — MCP→API round-trip integration testing is a separate future concern (testing-strategy.md §Unit vs Integration).

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Defer MEU-36 (`create_trade_plan`) | Spec labels it "draft — requires review before implementation"; REST route deferred to MEU-66/P2 |
| Defer report tools from MEU-35 | REST report routes deferred to MEU-52/P1; shipping permanently-404ing wrappers violates anti-deferral rule |
| Stub metricsCollector in diagnostics tool | Real MetricsCollector is MEU-39; stub keeps tool contract correct without premature dependency |
| Provider list filtering (never expose `api_key`) | Explicit spec requirement; `map()` strips to `{name, is_enabled, has_key}` only |
| Safe-fetch for unavailable providers endpoint | `/market-data/providers` is Phase 8; safe-fetch returns `[]` gracefully |

---

## Lessons Applied from Most Recent Reflection

From `mcp-server-foundation` reflection (2026-03-09):

1. **Source annotation values from build plan** — every `readOnlyHint`, `destructiveHint`, `idempotentHint` will be copy-pasted from the spec, not inferred
2. **Update all status artifacts atomically** — BUILD_PLAN.md + meu-registry.md updated in the same step after MEU completion
3. **Use `fetchApiBinary()` for binary endpoints** — analytics tools all return JSON, so `fetchApi()` is correct for all tools in this project (no binary endpoints)
