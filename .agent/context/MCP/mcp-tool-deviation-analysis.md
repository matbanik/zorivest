# MCP Tool Deviation Analysis: Plan vs. Reality

## Executive Summary

The build plan specified **9 toolsets with 79 unique tools** (65 specified + 12 planned + 2 future), with a deliberate design constraint: **38 tools loaded by default** to stay under IDE tool limits. The actual implementation has **10 toolsets with 76+ tools**, but critically: **all toolsets load eagerly** and the plan's grouping boundaries were not followed. Several toolsets expanded beyond their spec, new toolsets were invented, and planned toolsets had their contents redistributed. The IDE sees ~85 tools due to cross-tagging.

---

## Plan Specification (Build Plan §5.11)

The original plan in [05-mcp-server.md §5.11](file:///p:/zorivest/docs/build-plan/05-mcp-server.md) and [mcp-tool-index.md](file:///p:/zorivest/docs/build-plan/mcp-tool-index.md) defined:

| Toolset | Plan Count | Category Files | Default |
|---------|-----------|----------------|---------|
| `core` | **12** | 05a, 05b, 05k | ✅ Always |
| `discovery` | **4** | 05j | ✅ Always |
| `trade-analytics` | **19** | 05c | ✅ Default |
| `trade-planning` | **3** | 05c, 05d | ✅ Default |
| `market-data` | **7** | 05e | ⬜ Deferred |
| `accounts` | **13** | 05f | ⬜ Deferred |
| `scheduling` | **6** | 05g | ⬜ Deferred |
| `tax` | **8** | 05h | ⬜ Deferred |
| `behavioral` | **3** | 05i | ⬜ Deferred |
| **Total unique** | **~74** | | **38 default** |

Key design constraints from the plan:
- Default active tools: `core(12) + discovery(4) + trade-analytics(19) + trade-planning(3)` = **38 tools** (fits Cursor's 40-tool limit)
- Deferred toolsets require `enable_toolset` to activate
- `--toolsets` CLI flag for explicit selection
- Stage 1 target: **8–12 tools** for trade CRUD vertical slice

---

## Actual Implementation (seed.ts)

| Toolset | Actual Count | Plan Count | Delta | Loading |
|---------|-------------|-----------|-------|---------|
| `core` | **4** | 12 | **−8** | ✅ Always |
| `discovery` | **4** | 4 | 0 | ✅ Always |
| `trade-analytics` | **7** | 19 | **−12** | ✅ Default |
| `trade-planning` | **10** | 3 | **+7** | ✅ Default |
| `market-data` | **7** | 7 | 0 | ⬜ → **✅ All load** |
| `accounts` | **16** | 13 | **+3** | ⬜ → **✅ All load** |
| `scheduling` | **9** | 6 | **+3** | ⬜ → **✅ All load** |
| `pipeline-security` | **12** | — | **+12 NEW** | ⬜ → **✅ All load** |
| `tax` | **4** | 8 | **−4** | ⬜ → **✅ All load** |
| `behavioral` | **3** | 3 | 0 | ⬜ → **✅ All load** |
| **Total** | **76** | 74 | **+2** | **All load** |

---

## Deviation Breakdown

### 1. `core` — Dramatically Shrunk (12 → 4)

**Plan**: Settings (4) + Emergency stop/unlock (2) + Diagnostics (3) + GUI launch (1) + Service tools (3) + Workspace setup (1) = 12 tools

**Actual**: `get_settings`, `update_settings`, `zorivest_diagnose`, `zorivest_launch_gui` = 4 tools

**Missing from core**:
- `zorivest_emergency_stop` — not implemented
- `zorivest_emergency_unlock` — not implemented  
- `zorivest_service_status` — not implemented
- `zorivest_service_restart` — not implemented
- `zorivest_service_logs` — not implemented
- `get_log_settings` — not implemented
- `update_log_level` — not implemented
- `zorivest_setup_workspace` — not implemented

> **Impact**: Core was supposed to be the most important toolset (always loaded, operational tools). 67% of planned core tools are missing.

### 2. `trade-analytics` — Heavily Reduced (19 → 7)

**Plan**: Trade CRUD (3) + Screenshots (3) + Report CRUD (3) + Round trips (1) + Excursion (1) + Fee breakdown (1) + Execution quality (1) + PFOF (1) + Expectancy (1) + Drawdown sim (1) + Strategy breakdown (1) + SQN (1) + Cost of free (1) + AI review (1) + Options detect (1) = 19 tools

**Actual**: 7 tools — `create_trade`, `list_trades`, `attach_screenshot`, `get_trade_screenshots`, `get_screenshot`, `get_analytics_summary`, `get_trade_streaks`

**What happened**: Analytics tools were moved to other locations:
- `get_round_trips`, `delete_trade`, `create_report`, `get_report_for_trade`, `enrich_trade_excursion`, `score_execution_quality`, `ai_review_trade`, `detect_options_strategy` → registered directly on the server outside the seed, inflating the IDE tool count
- `get_expectancy_metrics`, `get_sqn`, `simulate_drawdown`, `get_strategy_breakdown`, `get_fee_breakdown`, `estimate_pfof_impact`, `get_cost_of_free` → registered as standalone analytics tools, appear in IDE without toolset grouping

### 3. `trade-planning` — Exploded (3 → 10)

**Plan**: `calculate_position_size`, `create_trade_plan`, `create_trade` (cross-tag) = 3 tools

**Actual**: 10 tools — original 3 + all 5 watchlist tools + `list_trade_plans` + `delete_trade_plan`

**What happened**:
- Watchlists (`create_watchlist`, `list_watchlists`, `get_watchlist`, `add_to_watchlist`, `remove_from_watchlist`) were supposed to be in `accounts` but got moved here
- `list_trade_plans` and `delete_trade_plan` added in TA4 remediation (2026-04-29)
- This violates the plan's 38-tool default budget — trade-planning alone is now 10 tools (was 3)

### 4. `pipeline-security` — New Toolset (0 → 12)

**Not in the original plan at all.** This entire toolset was invented during Phase 2.5 development:
- 4 DB tools: `emulate_policy`, `validate_sql`, `list_db_tables`, `get_db_row_samples`
- 6 email template tools: `create_email_template`, `get_email_template`, `list_email_templates`, `update_email_template`, `delete_email_template`, `preview_email_template`
- 2 discovery tools: `list_step_types`, `list_provider_capabilities`

> **Impact**: +12 tools that didn't exist in any plan, all loading eagerly.

### 5. `scheduling` — Expanded (6 → 9)

**Plan**: `create_policy`, `list_policies`, `run_pipeline`, `preview_report`, `update_policy_schedule`, `get_pipeline_history` = 6 tools

**Actual**: Plan's 6 + `delete_policy`, `update_policy`, `get_email_config` = 9 tools

Added during MEU-PH12 (approval security hardening). These additions are reasonable but weren't spec'd.

### 6. `accounts` — Expanded (13 → 16)

**Plan**: 12 tools from 05f + `get_account_review_checklist` = 13

**Actual**: 16 tools — plan's 13 minus watchlists (moved to trade-planning) plus:
- `delete_account` (was implicit in plan)
- `archive_account` (was implicit in plan)  
- `reassign_trades` (new lifecycle tool)
- 3 501 stubs from TA3: `list_bank_accounts`, `list_brokers`, `resolve_identifiers` (now return 501 instead of 404)

### 7. `tax` — Reduced (8 → 4)

**Plan**: `estimate_tax`, `find_wash_sales`, `simulate_tax_impact`, `get_tax_lots`, `get_quarterly_estimate`, `record_quarterly_tax_payment`, `harvest_losses`, `get_ytd_tax_summary` = 8 fully-specified tools

**Actual**: 4 tools (all 501 stubs): `estimate_tax`, `find_wash_sales`, `manage_lots`, `harvest_losses`

**What happened**: Tool names don't even match the plan. `manage_lots` wasn't in the spec; `simulate_tax_impact`, `get_tax_lots`, `get_quarterly_estimate`, `record_quarterly_tax_payment`, `get_ytd_tax_summary` are all missing.

---

## The Critical Deviation: All Toolsets Load Eagerly

The plan's most important constraint was **deferred loading**:

> "Default active tools: `core` + `discovery` + `trade-analytics` + `trade-planning` = **38 tools**."

In practice, **all 10 toolsets load when the MCP server starts**. The `--toolsets` CLI flag behavior and the deferred loading mechanism exist in the registry code, but the Antigravity IDE configuration doesn't use them — it gets all 76+ tools dumped into context.

This defeats the entire purpose of the toolset system.

---

## Root Causes

| Cause | Effect |
|-------|--------|
| **No consolidation gate** in the workflow | Each MEU adds individual tools; no one checks total count against the plan's 38-tool budget |
| **"Fix by adding" bias** | Audit findings (missing delete, missing list, missing stubs) are solved by adding tools instead of consolidating |
| **pipeline-security invented ad-hoc** | 12 tools for emulator/templates/DB were needed but the plan wasn't updated to account for them |
| **Watchlist misplacement** | 5 watchlist tools moved from accounts to trade-planning without updating the plan's tool count budget |
| **Eager loading default** | The IDE config loads all toolsets, so the deferred loading design is never exercised |
| **No tool count regression test** | The audit baseline records tool count but no CI gate enforces it |

---

## Current vs. Planned Consolidation

| Metric | Plan Target | Current | Gap |
|--------|-------------|---------|-----|
| Default-loaded tools | 38 | 76+ (all load) | **2× over budget** |
| Total toolsets | 9 | 10 | +1 (pipeline-security) |
| Total unique tools | 74 | 76 | +2 (and growing) |
| IDE-visible tools | 38–74 (depends on config) | ~85 (cross-tags) | Exceeds IDE limits |
| Consolidation target | — | 12 (from audit proposal) | Not started |

---

## Project: MCP Tool Consolidation (76 → 12)

> **Status**: Approved for execution  
> **Source**: [mcp-audit-workflow-proposal.md](file:///p:/zorivest/.agent/context/MCP/mcp-audit-workflow-proposal.md) §6, [mcp-tool-audit-report.md](file:///p:/zorivest/.agent/context/MCP/mcp-tool-audit-report.md) §Consolidation  
> **Tracked as**: `[MCP-TOOLPROLIFERATION]` in [known-issues.md](file:///p:/zorivest/.agent/context/known-issues.md)

### Target Architecture: 12 Compound Tools

Each compound tool uses a `action` discriminated union — a single MCP entry point per resource domain that routes to isolated handlers internally. This is NOT a "God Tool" anti-pattern because each action has its own Zod validation schema and isolated handler function.

| # | Compound Tool | Actions | Replaces | Net Δ |
|---|---------------|---------|----------|-------|
| 1 | `zorivest_trade` | `create`, `list`, `get`, `delete`, `screenshot_attach`, `screenshot_list`, `screenshot_get` | 7 trade + screenshot tools | −6 |
| 2 | `zorivest_account` | `list`, `get`, `create`, `update`, `delete`, `archive`, `reassign`, `balance`, `checklist` | 9 account tools | −8 |
| 3 | `zorivest_watchlist` | `create`, `list`, `get`, `add_ticker`, `remove_ticker` | 5 watchlist tools | −4 |
| 4 | `zorivest_market` | `quote`, `news`, `search`, `filings`, `providers`, `test_provider`, `disconnect_provider` | 7 market-data tools | −6 |
| 5 | `zorivest_report` | `create`, `get` | 2 report tools | −1 |
| 6 | `zorivest_policy` | `list`, `create`, `update`, `delete`, `schedule`, `run`, `history`, `emulate`, `preview` | 9 scheduling tools | −8 |
| 7 | `zorivest_template` | `list`, `get`, `create`, `update`, `delete`, `preview` | 6 template tools | −5 |
| 8 | `zorivest_analytics` | `expectancy`, `sqn`, `drawdown`, `strategy`, `fees`, `pfof`, `cost_of_free`, `round_trips`, `excursion`, `execution_quality`, `options_detect`, `ai_review`, `position_size` | 13 analytics tools | −12 |
| 9 | `zorivest_plan` | `create`, `list`, `delete` | 3 plan tools | −2 |
| 10 | `zorivest_import` | `broker_csv`, `broker_pdf`, `bank_statement`, `sync_broker` | 4 import tools | −3 |
| 11 | `zorivest_db` | `tables`, `samples`, `validate_sql`, `step_types`, `provider_capabilities` | 5 db/discovery tools | −4 |
| 12 | `zorivest_system` | `diagnose`, `settings_get`, `settings_update`, `confirm_token`, `launch_gui`, `email_config`, `toolsets_list`, `toolset_describe`, `toolset_enable` | 9 core/discovery tools | −8 |
| | **Totals** | | **76 individual tools** | **= 12 compound** |

### Zod Discriminated Union Pattern

```typescript
// Example: zorivest_account compound tool
const AccountAction = z.discriminatedUnion("action", [
  z.object({ action: z.literal("list"), include_archived: z.boolean().default(false) }),
  z.object({ action: z.literal("get"), account_id: z.string() }),
  z.object({ action: z.literal("create"), name: z.string(), account_type: z.enum([...]) }),
  z.object({ action: z.literal("update"), account_id: z.string(), name: z.string().optional() }),
  z.object({ action: z.literal("delete"), account_id: z.string(), confirmation_token: z.string().optional() }),
  z.object({ action: z.literal("archive"), account_id: z.string() }),
  z.object({ action: z.literal("balance"), account_id: z.string(), balance: z.number() }),
  z.object({ action: z.literal("checklist"), scope: z.enum(["all","stale_only","broker_only","bank_only"]).default("stale_only") }),
]);
```

---

### Implementation Roadmap

| Phase | Scope | Effort | Risk | Deliverable |
|-------|-------|--------|------|-------------|
| **Phase 1: Merge Identicals** | Eliminate redundant tools (`list_provider_capabilities` → `list_market_providers`, etc.) | 2h | Zero | −5 tools, 71 remaining |
| **Phase 2: CRUD Families** | Consolidate `account`, `watchlist`, `template` CRUD families into compound tools | 4h | Low | −25 tools, 46 remaining |
| **Phase 3: Analytics + Scheduling** | Consolidate analytics, market, scheduling, plan, import, db tools | 4h | Medium | −22 tools, 24 remaining |
| **Phase 4: System + Deferred Loading** | Merge core/discovery into `zorivest_system`, re-enable deferred loading, add CI gate | 2h | Medium | 12 compound tools, deferred loading working |

#### Phase Dependencies
```
Phase 1 (identicals) → Phase 2 (CRUD) → Phase 3 (analytics) → Phase 4 (system)
                                                                      ↓
                                                              CI gate enforcement
```

---

### Build Plan Files Requiring Updates

> Every file below must be updated to reflect the 12 compound-tool architecture. Changes range from simple tool-name renames to structural rewrites of tool registration specs.

#### Primary MCP Specs (must rewrite tool contracts)

| File | What Changes | Severity |
|------|-------------|----------|
| [05-mcp-server.md](file:///p:/zorivest/docs/build-plan/05-mcp-server.md) | §5.11 Toolset definitions (9→4 toolsets), §5.10 Registration Index (compound routing), §5.9 Metrics middleware (compound tool names) | **Major rewrite** |
| [05a-mcp-zorivest-settings.md](file:///p:/zorivest/docs/build-plan/05a-mcp-zorivest-settings.md) | Settings tools merge into `zorivest_system` compound | Moderate |
| [05b-mcp-zorivest-diagnostics.md](file:///p:/zorivest/docs/build-plan/05b-mcp-zorivest-diagnostics.md) | Diagnostics + service tools merge into `zorivest_system` | Moderate |
| [05c-mcp-trade-analytics.md](file:///p:/zorivest/docs/build-plan/05c-mcp-trade-analytics.md) | 19 tools split into `zorivest_trade` (CRUD) + `zorivest_analytics` (metrics) + `zorivest_report` | **Major rewrite** |
| [05d-mcp-trade-planning.md](file:///p:/zorivest/docs/build-plan/05d-mcp-trade-planning.md) | Calculator moves to `zorivest_analytics`, plan CRUD to `zorivest_plan` | Moderate |
| [05e-mcp-market-data.md](file:///p:/zorivest/docs/build-plan/05e-mcp-market-data.md) | All 7 tools → `zorivest_market` compound | Moderate |
| [05f-mcp-accounts.md](file:///p:/zorivest/docs/build-plan/05f-mcp-accounts.md) | Account CRUD → `zorivest_account`, imports → `zorivest_import`, watchlists → `zorivest_watchlist` | **Major rewrite** |
| [05g-mcp-scheduling.md](file:///p:/zorivest/docs/build-plan/05g-mcp-scheduling.md) | All 6+ tools → `zorivest_policy` compound | Moderate |
| [05h-mcp-tax.md](file:///p:/zorivest/docs/build-plan/05h-mcp-tax.md) | Tax tools → absorb into `zorivest_analytics` or dedicated compound | Moderate |
| [05i-mcp-behavioral.md](file:///p:/zorivest/docs/build-plan/05i-mcp-behavioral.md) | Behavioral tools → absorb into `zorivest_analytics` | Minor |
| [05j-mcp-discovery.md](file:///p:/zorivest/docs/build-plan/05j-mcp-discovery.md) | Discovery tools merge into `zorivest_system` compound | Moderate |
| [05k-mcp-setup-workspace.md](file:///p:/zorivest/docs/build-plan/05k-mcp-setup-workspace.md) | Workspace setup → `zorivest_system.setup_workspace` action | Minor |

#### Index Files (must update tool names)

| File | What Changes |
|------|-------------|
| [mcp-tool-index.md](file:///p:/zorivest/docs/build-plan/mcp-tool-index.md) | Complete rewrite — 74-row catalog → 12-row compound catalog with action sub-tables |
| [mcp-planned-readiness.md](file:///p:/zorivest/docs/build-plan/mcp-planned-readiness.md) | Update tool names in readiness matrix |
| [input-index.md](file:///p:/zorivest/docs/build-plan/input-index.md) | Update MCP tool references (searches for old tool names) |
| [output-index.md](file:///p:/zorivest/docs/build-plan/output-index.md) | Update MCP tool references |
| [gui-actions-index.md](file:///p:/zorivest/docs/build-plan/gui-actions-index.md) | Update tool name references in GUI→MCP mappings |

#### Supporting Docs (reference updates only)

| File | What Changes |
|------|-------------|
| [build-priority-matrix.md](file:///p:/zorivest/docs/build-plan/build-priority-matrix.md) | Add MCP Consolidation as a phase; update tool references in MEU descriptions |
| [testing-strategy.md](file:///p:/zorivest/docs/build-plan/testing-strategy.md) | Update MCP test patterns for compound tools |
| [dependency-manifest.md](file:///p:/zorivest/docs/build-plan/dependency-manifest.md) | Update if MCP dependencies change |
| [00-overview.md](file:///p:/zorivest/docs/build-plan/00-overview.md) | Update MCP rollout stages tool counts |

#### Implementation Files (code changes)

| File | What Changes |
|------|-------------|
| [seed.ts](file:///p:/zorivest/mcp-server/src/toolsets/seed.ts) | 10 toolset definitions → 4 (always, default-trade, deferred-data, deferred-ops) |
| `mcp-server/src/tools/*.ts` (13 files) | Refactor into compound tool handlers with discriminated union routing |
| `mcp-server/tests/**/*.test.ts` | Update all test tool names and parameter shapes |
| [baseline-snapshot.json](file:///p:/zorivest/.agent/skills/mcp-audit/resources/baseline-snapshot.json) | Replace 76-tool baseline with 12-tool baseline |

---

### Post-Consolidation Toolset Structure

After consolidation, the toolset system simplifies from 10 toolsets to 4:

| Toolset | Compound Tools | Default | Description |
|---------|---------------|---------|-------------|
| `core` | `zorivest_system` | ✅ Always | Settings, diagnostics, GUI, discovery, confirmation tokens |
| `trade` | `zorivest_trade`, `zorivest_report`, `zorivest_plan`, `zorivest_analytics` | ✅ Default | Trade CRUD, reports, plans, all analytics |
| `data` | `zorivest_market`, `zorivest_account`, `zorivest_watchlist`, `zorivest_import` | ⬜ Deferred | Market data, accounts, watchlists, imports |
| `ops` | `zorivest_policy`, `zorivest_template`, `zorivest_db` | ⬜ Deferred | Scheduling, templates, DB tools |

**Default active: 5 compound tools** (core + trade). Deferred: 7 compound tools loaded on-demand via `zorivest_system(action: "toolset_enable")`.

---

### Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Breaking existing agent workflows | Keep `v1` aliases for old tool names for 2 releases, then deprecate |
| Complex compound parameter validation | Zod discriminated unions validate per-action — no loss of type safety |
| Harder to discover individual operations | Compound tool descriptions list all actions with `use_when` per action |
| Some IDEs parse compound schemas poorly | Test with Cursor, Antigravity, Claude Desktop; fall back to `--legacy-tools` flag if needed |
| Regression during migration | Run `/mcp-audit` before and after each phase; compare baselines |

### Exit Criteria

- [ ] Total MCP tools registered: **≤ 12**
- [ ] Default-loaded tools: **≤ 5** (core + trade toolsets)
- [ ] Consolidation score: **1.0** (12/12)
- [ ] All existing `/mcp-audit` CRUD tests pass with compound tool names
- [ ] `--toolsets` CLI flag works with new 4-toolset structure
- [ ] Deferred loading verified (data + ops only load on `zorivest_system(action: "toolset_enable")`)
- [ ] CI gate added: fail if `tool_count > 12`
- [ ] Build plan files updated (all files listed above)
- [ ] `mcp-tool-index.md` reflects compound-tool catalog
- [ ] Old tool aliases deprecated with removal date
