---
name: MCP Tool Audit
description: Systematic CRUD and functional testing of all Zorivest MCP tools. Discovers toolsets, exercises every tool, logs issues, compares against baseline, and produces a structured audit report.
---

# MCP Tool Audit Skill

## Overview

This skill provides a repeatable protocol for auditing all Zorivest MCP tools. It tests CRUD lifecycle completeness, functional correctness, regression detection against a baseline, and tool consolidation metrics. Invoke via `/mcp-audit` workflow or read this file directly when MCP server changes are made.

## When to Invoke

| Trigger | Reason |
|---------|--------|
| After `mcp-server/src/` changes | New/modified tools need validation |
| After API route additions/removals | Backend changes may break MCP tools |
| Pre-release gate | Ensure all tools work before version bump |
| Weekly / on-demand via `/mcp-audit` | Routine health check |
| When `known-issues.md` references `[MCP-TOOLAUDIT]` | Track remediation progress |

## Prerequisites

- Backend API running (verify via `zorivest_diagnose` → `backend.reachable: true`)
- MCP server connected (verify via `zorivest_diagnose` → `database.unlocked: true`)
- No other audit running concurrently

## Execution Protocol

### Phase 1: Discovery

1. Call `list_available_toolsets` → record toolset names, tool counts, loaded status
2. For each toolset, call `describe_toolset({toolset_name})` → record tool names and descriptions
3. Compare against `resources/baseline-snapshot.json`:
   - **New tools** (in server, not in baseline) → flag for testing, add to baseline
   - **Removed tools** (in baseline, not in server) → flag as **REGRESSION**
   - **Count mismatch** (toolset exists but tool count differs) → investigate
   - **Ghost tools** (described by `describe_toolset` but not callable) → flag as **Issue**

### Phase 2: CRUD Testing

For each resource domain that supports CRUD, execute the full lifecycle. **All test entities MUST be cleaned up** (see §Cleanup Contract).

#### 2a. Accounts

```
1. list_accounts → record baseline count
2. create_account(name: "MCP-Audit-{timestamp}", type: BROKER) → record account_id
3. get_account(account_id) → verify fields match creation params
4. update_account(account_id, name: "MCP-Audit-Updated") → verify update applied
5. record_balance(account_id, balance: 99999) → verify snapshot created
6. archive_account(account_id) → verify is_archived=true via list_accounts(include_archived=true)
7. get_confirmation_token(action: delete_account) → delete_account(account_id, token) → verify deletion
8. list_accounts → verify count restored to baseline
```

#### 2b. Trades

```
1. list_trades(limit: 1) → record baseline total
2. get_confirmation_token(action: create_trade) → create_trade(exec_id: "MCP-AUDIT-{timestamp}", ...) → verify creation
3. get_report_for_trade(exec_id) → expect 404 (no report yet)
4. create_report(trade_id: exec_id, ...) → verify report created
5. get_report_for_trade(exec_id) → verify report fields
6. get_confirmation_token(action: delete_trade) → delete_trade(exec_id, token) → verify deletion
7. list_trades(limit: 1) → verify total restored
```

#### 2c. Watchlists

```
1. list_watchlists → record baseline count
2. create_watchlist(name: "MCP-Audit-{timestamp}") → record watchlist_id
3. add_to_watchlist(watchlist_id, ticker: "AUDIT", notes: "test") → verify addition
4. get_watchlist(watchlist_id) → verify ticker present
5. remove_from_watchlist(watchlist_id, ticker: "AUDIT") → verify removal
6. get_watchlist(watchlist_id) → verify empty items
7. [If delete_watchlist exists] delete_watchlist → verify deletion
```

#### 2d. Email Templates

```
1. list_email_templates → record baseline count
2. create_email_template(name: "mcp-audit-{timestamp}", body_html: "<p>test</p>") → verify creation
3. get_email_template(name) → verify fields
4. preview_email_template(name, data: {}) → verify rendered output
5. update_email_template(name, description: "updated") → verify update
6. delete_email_template(name) → verify deletion
7. list_email_templates → verify count restored
```

### Phase 3: Functional Testing

For each non-CRUD tool, call with **valid minimal params** and record:

| Field | Description |
|-------|-------------|
| `tool_name` | MCP tool name |
| `status` | `pass` / `fail` / `partial` / `skip` |
| `http_code` | Response code (200, 404, 422, 500, 503) |
| `error` | Error message if any |
| `notes` | Contextual notes (e.g., "expected — no API key") |

**Categories to test:**

- **Market Data**: `search_ticker`, `get_stock_quote`, `get_market_news`, `get_sec_filings`, `list_market_providers`, `list_provider_capabilities`, `test_market_provider`
- **Analytics**: `get_expectancy_metrics`, `get_sqn`, `simulate_drawdown`, `get_strategy_breakdown`, `get_fee_breakdown`, `get_cost_of_free`, `estimate_pfof_impact`
- **Planning**: `calculate_position_size`, `create_trade_plan`, `detect_options_strategy`
- **Scheduling**: `list_policies`, `get_pipeline_history`, `list_step_types`
- **Security**: `validate_sql` (valid + DDL injection test), `list_db_tables`, `get_db_row_samples`, `emulate_policy`, `resolve_identifiers`
- **Core**: `get_settings`, `get_settings(key)`, `update_settings`, `get_email_config`
- **Discovery**: `list_available_toolsets`, `describe_toolset`, `get_confirmation_token`

### Phase 3a: Provider API Validation (Live)

> Prerequisite: At least one market data provider must have a configured API key.

For each market data provider with a configured API key:

1. Call `zorivest_market(action: "test_provider", provider_name: "{name}")` → record success/fail
2. For each data type the provider supports (per `ProviderCapabilities`):
   - Call the corresponding MCP action (e.g., `action: "quote"`, `action: "ohlcv"`)
   - Validate response shape matches expected DTO fields
   - Record: provider, data_type, status, response_time, error
3. Test fallback chain: if primary fails, verify fallback provider responds

**Exit**: All configured providers tested; response shapes validated.

### Phase 3b: Report Pipeline Validation

1. Create a test policy with fetch→transform→send chain:
   - FetchStep: quote data for AAPL from best available provider
   - TransformStep: field mapping + validation
   - StoreStep (if MEU-193 complete): persist to market_quotes table
2. Run policy with `dry_run: true` → verify PARSE+VALIDATE+SIMULATE pass
3. Verify pipeline_state_repo has cursor entry
4. Clean up: delete test policy

**Exit**: At least one end-to-end pipeline validates successfully.

### Phase 4: Regression Detection

1. Load `resources/baseline-snapshot.json`
2. For each tool in the baseline:
   - **Was PASS, now FAIL** → **REGRESSION** (flag immediately)
   - **Was FAIL, still FAIL** → **KNOWN ISSUE** (reference existing issue ID)
   - **Was FAIL, now PASS** → **FIXED** (update baseline, celebrate)
   - **Not in baseline** → **NEW** (add to baseline with current result)
3. Generate regression delta summary

### Phase 5: Report & Record

1. Write structured report to `.agent/context/MCP/mcp-tool-audit-report.md` (overwrite previous)
2. Update `known-issues.md` `[MCP-TOOLAUDIT]` entry with:
   - New issue count
   - Regression count
   - Fixed count
3. Update `resources/baseline-snapshot.json` with current results
4. Calculate **consolidation score**: `current_tool_count / 13` (ideal target: 13 compound tools after P2.5f consolidation)

## Cleanup Contract

> [!CAUTION]
> **Mandatory cleanup.** Every test entity created during the audit MUST be deleted before the audit completes. Failure to clean up pollutes the production database.

- **Accounts**: Delete via `get_confirmation_token` + `delete_account`
- **Trades**: Delete via `get_confirmation_token` + `delete_trade`
- **Watchlists**: Delete if tool exists; otherwise note residual in report
- **Templates**: Delete via `delete_email_template`
- **Trade plans**: Note if stale plan blocks creation (no delete tool exists)

If a deletion tool returns an error (e.g., `delete_trade` → 500), log it as an issue and flag for manual cleanup in the report.

## Output Format

The audit report MUST include:

1. **Header**: Date, agent, backend version, tool count
2. **Scorecard table**: tested / passed / failed / partial per category
3. **CRUD matrix**: per-resource operation × result table
4. **Functional test results**: per-tool status table
5. **Issues log**: severity × component × tool × error × description
6. **Regression delta**: compared to previous baseline
7. **Consolidation score**: current vs ideal

## Interpreting Results

| Consolidation Score | Meaning |
|:---:|---------|
| < 2.0 | Excellent — approaching ideal tool count |
| 2.0–3.0 | Good — manageable for most IDEs |
| 3.0–5.0 | Warning — IDE tool limits may be hit |
| > 5.0 | Critical — consolidation strongly recommended |

## Related Files

- **Audit report**: [`.agent/context/MCP/mcp-tool-audit-report.md`](../../context/MCP/mcp-tool-audit-report.md)
- **Baseline**: [`resources/baseline-snapshot.json`](resources/baseline-snapshot.json)
- **Workflow**: [`.agent/workflows/mcp-audit.md`](../../workflows/mcp-audit.md)
- **Known issues**: [`.agent/context/known-issues.md`](../../context/known-issues.md) — `[MCP-TOOLAUDIT]`
- **Consolidation proposal**: Audit report §Tool Consolidation Reflection
