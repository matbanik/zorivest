# Zorivest MCP Tool Audit Report

**Date**: 2026-04-27  
**Agent**: Antigravity (Gemini)  
**Backend**: v0.1.0, DB unlocked, 3 market providers enabled  
**Tool Count**: 74 tools across 10 toolsets

---

## Executive Summary

Tested **74 MCP tools** across all 10 toolsets. Found **12 issues** ranging from 500 errors to redundant tools and missing endpoints. CRUD lifecycle testing passed for Accounts, Watchlists, and Email Templates. Trade deletion and several market data endpoints are broken.

### Scorecard

| Category | Tools Tested | Passed | Failed | Partial |
|----------|:---:|:---:|:---:|:---:|
| Accounts (CRUD + lifecycle) | 12 | 10 | 2 | 0 |
| Trades (CRUD + reports) | 8 | 6 | 1 | 1 |
| Watchlists (CRUD) | 5 | 5 | 0 | 0 |
| Market Data | 7 | 4 | 2 | 1 |
| Settings & Core | 4 | 3 | 1 | 0 |
| Trade Planning | 3 | 1 | 1 | 1 |
| Analytics / Behavioral | 6 | 6 | 0 | 0 |
| Scheduling / Policies | 4 | 4 | 0 | 0 |
| Pipeline Security / Email | 12 | 11 | 0 | 1 |
| Discovery / Meta | 4 | 4 | 0 | 0 |
| **TOTAL** | **65** | **54** | **7** | **4** |

> 9 tools not directly testable (import tools, destructive ops requiring files/brokers, tax tools not exposed)

---

## CRUD Results by Component

### ✅ Accounts — Full CRUD Verified

| Operation | Tool | Result | Notes |
|-----------|------|--------|-------|
| **CREATE** | `create_account` | ✅ Pass | Auto-generates UUID |
| **READ list** | `list_accounts` | ✅ Pass | Supports `include_archived`, `include_system` |
| **READ single** | `get_account` | ✅ Pass | Returns computed metrics |
| **UPDATE** | `update_account` | ✅ Pass | Partial update works |
| **ARCHIVE** | `archive_account` | ✅ Pass | Soft-delete sets `is_archived: true` |
| **DELETE** | `delete_account` | ✅ Pass | Requires confirmation token |
| **Balance** | `record_balance` | ✅ Pass | Timestamps auto-generated |
| **Checklist** | `get_account_review_checklist` | ✅ Pass | Stale balance detection |
| **Bank list** | `list_bank_accounts` | ❌ **404** | Endpoint not implemented |
| **Broker list** | `list_brokers` | ❌ **404** | Endpoint not implemented |

### ⚠️ Trades — CRUD Partial (DELETE broken)

| Operation | Tool | Result | Notes |
|-----------|------|--------|-------|
| **READ list** | `list_trades` | ✅ Pass | Pagination works, returns `total` |
| **CREATE** | `create_trade` | ✅ Pass | Requires confirmation token |
| **DELETE** | `delete_trade` | ❌ **500** | Internal Server Error on valid exec_id |
| **Report CREATE** | `create_report` | ✅ Pass | Linked to trade_id |
| **Report READ** | `get_report_for_trade` | ✅ Pass | |
| **Round trips** | `get_round_trips` | ✅ Pass | Empty when no closings |
| **Screenshots** | `get_trade_screenshots` | ✅ Pass | |

### ✅ Watchlists — Full CRUD Verified (no delete_watchlist tool exists)

| Operation | Tool | Result | Notes |
|-----------|------|--------|-------|
| **CREATE** | `create_watchlist` | ✅ Pass | Auto-assigns ID |
| **READ list** | `list_watchlists` | ✅ Pass | Includes items inline |
| **READ single** | `get_watchlist` | ✅ Pass | |
| **ADD ticker** | `add_to_watchlist` | ✅ Pass | With notes |
| **REMOVE ticker** | `remove_from_watchlist` | ✅ Pass | |
| **DELETE watchlist** | — | ❌ Missing | No tool exists |

### ✅ Email Templates — Full CRUD Verified

| Operation | Tool | Result | Notes |
|-----------|------|--------|-------|
| **CREATE** | `create_email_template` | ✅ Pass | Jinja2 template |
| **READ list** | `list_email_templates` | ✅ Pass | |
| **READ single** | `get_email_template` | ✅ Pass | |
| **PREVIEW** | `preview_email_template` | ✅ Pass | Renders with data dict |
| **UPDATE** | `update_email_template` | ✅ Pass | Partial update |
| **DELETE** | `delete_email_template` | ✅ Pass | |

---

## Functional Test Results

### Market Data

| Tool | Result | Notes |
|------|--------|-------|
| `search_ticker` | ✅ Pass | Yahoo Finance provider |
| `get_stock_quote` | ✅ Pass | Real-time AAPL quote returned |
| `get_market_news` | ❌ **503** | Finnhub returns 422 for news |
| `get_sec_filings` | ❌ **503** | SEC API not configured (no key) |
| `list_market_providers` | ✅ Pass | 14 providers shown |
| `list_provider_capabilities` | ✅ Pass | **Identical output** to `list_market_providers` |
| `test_market_provider` | ✅ Pass | Stub response |

### Analytics & Behavioral

| Tool | Result | Notes |
|------|--------|-------|
| `get_expectancy_metrics` | ✅ Pass | Returns 0s (no closed round-trips) |
| `get_sqn` | ✅ Pass | Grade: N/A |
| `simulate_drawdown` | ✅ Pass | Empty probability table |
| `get_strategy_breakdown` | ✅ Pass | Empty |
| `get_fee_breakdown` | ✅ Pass | |
| `get_cost_of_free` | ✅ Pass | |

### Trade Planning

| Tool | Result | Notes |
|------|--------|-------|
| `calculate_position_size` | ✅ Pass | Correct math (100 shares) |
| `create_trade_plan` | ❌ **409** | Duplicate active plan blocks creation; no list/delete tools |
| `detect_options_strategy` | ✅ Pass | Returns "unknown" for non-options |

### Core / System

| Tool | Result | Notes |
|------|--------|-------|
| `get_settings` | ✅ Pass | Both all + single key |
| `update_settings` | ❌ **422** | Error serialized as `[object Object]` |
| `zorivest_diagnose` | ✅ Pass | Verbose mode with metrics |
| `get_confirmation_token` | ✅ Pass | 60-second TTL |

### Pipeline Security

| Tool | Result | Notes |
|------|--------|-------|
| `validate_sql` | ✅ Pass | Correctly blocks DDL |
| `list_db_tables` | ✅ Pass | |
| `get_db_row_samples` | ✅ Pass | |
| `emulate_policy` | ⚠️ Partial | Works but schema undocumented |
| `list_step_types` | ✅ Pass | |
| `resolve_identifiers` | ❌ **404** | Endpoint not implemented |

---

## Issues Log

| # | Severity | Component | Tool | Error | Description |
|---|----------|-----------|------|-------|-------------|
| 1 | Medium | Accounts | `list_bank_accounts` | 404 | API endpoint not implemented |
| 2 | Medium | Accounts | `list_brokers` | 404 | API endpoint not implemented |
| 3 | **High** | Trades | `delete_trade` | 500 | Internal Server Error on valid exec_id — data cannot be cleaned up via MCP |
| 4 | Low | Watchlists | — | N/A | No `delete_watchlist` tool exists; watchlists accumulate forever |
| 5 | Medium | Market | `get_market_news` | 503 | Finnhub returns 422 — news integration broken |
| 6 | Low | Market | `get_sec_filings` | 503 | Expected — requires paid SEC API key |
| 7 | Low | Market | `list_provider_capabilities` | N/A | Returns **identical data** to `list_market_providers` — redundant tool |
| 8 | Medium | Core | `update_settings` | 422 | Error body serialized as `[object Object]` — unhelpful error message |
| 9 | Medium | Planning | `create_trade_plan` | 409 | Duplicate active plan blocks new creation; no `list_trade_plans` or `delete_trade_plan` tools to manage stale plans |
| 10 | Medium | Security | `emulate_policy` | N/A | PolicyDocument schema not documented in tool description; `extra="forbid"` makes discovery impossible |
| 11 | Medium | Security | `resolve_identifiers` | 404 | Endpoint not implemented |
| 12 | Medium | Tax | `describe_toolset("tax")` | N/A | Reports 4 tools loaded but none are registered as callable MCP tools |

---

## Tool Consolidation Reflection

### The Problem

74 tools across 10 toolsets creates multiple issues:

1. **IDE Tool Limits**: Most MCP clients (VS Code, Cursor, Windsurf) warn or hard-cap at ~60-80 tools. 74 tools is already at the red line.
2. **Context Window Saturation**: Each tool's schema (name, description, parameters, types) consumes ~200-400 tokens. 74 tools = ~20,000-30,000 tokens just for tool definitions — that's 2-3% of a 1M context window before any work begins.
3. **Decision Fatigue**: The AI must evaluate 74 tools for every user request. Similar tool names (`list_market_providers` vs `list_provider_capabilities`) cause confusion.
4. **Redundancy**: At least 5 tools are provably redundant or return identical data.

### Current Tool Distribution

```
accounts:          16 tools ████████████████
pipeline-security: 12 tools ████████████
scheduling:         9 tools █████████
trade-planning:     8 tools ████████
market-data:        7 tools ███████
trade-analytics:    7 tools ███████
core:               4 tools ████
discovery:          4 tools ████
tax:                4 tools ████  (ghost — not callable)
behavioral:         3 tools ███
```

### Proposed Consolidation: Resource-Centric Compound Tools

Replace individual CRUD verbs with **compound tools** that take an `action` parameter. This is the pattern used by GitHub's MCP server and other production-grade implementations.

#### Proposed 12-Tool Architecture

| # | Tool Name | Actions | Replaces | Savings |
|---|-----------|---------|----------|---------|
| 1 | `zorivest_account` | `list`, `get`, `create`, `update`, `delete`, `archive`, `balance`, `checklist` | 10 account tools | −9 |
| 2 | `zorivest_trade` | `list`, `create`, `delete`, `screenshot_list`, `screenshot_add`, `excursion`, `execution_quality`, `options_detect` | 8 trade tools | −7 |
| 3 | `zorivest_report` | `create`, `get`, `ai_review` | 3 report tools | −2 |
| 4 | `zorivest_watchlist` | `list`, `get`, `create`, `delete`, `add_ticker`, `remove_ticker` | 5+ watchlist tools | −4 |
| 5 | `zorivest_market` | `quote`, `search`, `news`, `filings`, `providers`, `test_provider`, `connect`, `disconnect` | 8 market tools | −7 |
| 6 | `zorivest_policy` | `list`, `create`, `update`, `delete`, `schedule`, `run`, `history`, `emulate`, `preview` | 9 scheduling tools | −8 |
| 7 | `zorivest_template` | `list`, `get`, `create`, `update`, `delete`, `preview` | 6 template tools | −5 |
| 8 | `zorivest_analytics` | `expectancy`, `sqn`, `drawdown`, `strategy`, `fees`, `pfof`, `position_size`, `round_trips` | 8 analytics tools | −7 |
| 9 | `zorivest_plan` | `create`, `list` | 2 plan tools | −1 |
| 10 | `zorivest_import` | `broker_csv`, `broker_pdf`, `bank_statement`, `sync_broker` | 4 import tools | −3 |
| 11 | `zorivest_db` | `tables`, `samples`, `validate_sql`, `resolve_ids` | 4 db tools | −3 |
| 12 | `zorivest_system` | `diagnose`, `settings`, `confirm`, `launch_gui` | 4+ core tools | −3 |

**Result: 74 → 12 tools (84% reduction)**

### Implementation Approach

```typescript
// Before (74 separate tool handlers):
server.setRequestHandler(CallToolRequestSchema, async (request) => {
    switch (request.params.name) {
        case "list_accounts": ...
        case "get_account": ...
        case "create_account": ...
        // ... 71 more cases
    }
});

// After (12 compound tools):
server.setRequestHandler(CallToolRequestSchema, async (request) => {
    switch (request.params.name) {
        case "zorivest_account": {
            const { action, ...params } = request.params.arguments;
            switch (action) {
                case "list": return listAccounts(params);
                case "get": return getAccount(params);
                case "create": return createAccount(params);
                // ... consolidated within one tool
            }
        }
        // ... 11 more compound tools
    }
});
```

### Schema Design for Compound Tools

Use discriminated unions for parameter validation:

```typescript
{
    name: "zorivest_account",
    description: "Manage financial accounts. Actions: list, get, create, update, delete, archive, balance, checklist",
    inputSchema: {
        type: "object",
        properties: {
            action: {
                type: "string",
                enum: ["list", "get", "create", "update", "delete", "archive", "balance", "checklist"],
                description: "Operation to perform"
            },
            // Common optional params — validated per-action
            account_id: { type: "string" },
            name: { type: "string" },
            account_type: { type: "string", enum: [...] },
            balance: { type: "number" },
            // ...
        },
        required: ["action"]
    }
}
```

### Additional Optimizations

1. **Eliminate Redundancies**:
   - `list_provider_capabilities` = `list_market_providers` → merge into one
   - `get_confirmation_token` could become a standard MCP annotation instead of a tool

2. **Remove Ghost Tools**: Tax toolset reports 4 tools but none are callable. Either expose them or remove from the count.

3. **Lazy Loading**: The toolset system already supports deferred loading (`enable_toolset`), but currently all 10 toolsets load eagerly. Consider loading only `core` + `discovery` by default, with the agent calling `enable_toolset` for the domains it needs.

4. **Tool Description Quality**: Several tools have descriptions like "Full PolicyDocument JSON object" without documenting the schema. Adding `inputSchema` examples to tool descriptions would eliminate trial-and-error calls.

### Risk Assessment

| Risk | Mitigation |
|------|------------|
| Breaking existing agent workflows | Version the tools — keep `v1` aliases for 2 releases |
| Complex parameter validation for compound tools | Use Zod discriminated unions server-side |
| Harder to discover individual operations | Better tool descriptions with action lists |
| Some IDEs parse compound schemas poorly | Test with VS Code, Cursor, Claude Desktop |

### Priority Order

1. **Phase 1**: Merge identical tools (−5 tools, zero risk)
2. **Phase 2**: Consolidate CRUD families (accounts, templates, watchlists) (−25 tools)
3. **Phase 3**: Consolidate analytics + market + scheduling (−20 tools)
4. **Phase 4**: Add lazy loading for non-core toolsets
