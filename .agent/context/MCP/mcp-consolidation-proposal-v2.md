# MCP Tool Consolidation — Corrected Proposal v2

> **Status**: Corrected — ready for Codex review
> **Date**: 2026-04-29
> **Phase**: P2.5f — MCP Tool Consolidation
> **Prerequisite**: P2.5e ✅
> **Resolves**: [MCP-TOOLPROLIFERATION], partially [MCP-TOOLDISCOVERY], [MCP-TOOLCAP]
> **Supersedes**: [mcp-consolidation-proposal.md](mcp-consolidation-proposal.md) (v1)

---

## 1. Review Findings Addressed

| # | Finding | Severity | Resolution |
|---|---------|----------|------------|
| F1 | v1 aliases conflict with ≤12 tools exit criterion | High | **No visible aliases.** SDK `tools/list` filters by `enabled` flag (line 69 of `mcp.js`). Old tool names are NOT re-registered. Migration is clean cut: 76 tools removed, 13 tools registered. Agents calling old names get `Tool not found` — server instructions document the new names. |
| F2 | Deferred-loading root cause under-specified | High | **Empirical AC added.** Current code: `registerAllToolsets()` pre-connect → `applyModeFilter()` in `oninitialized` → `handle.disable()` for non-selected. CLI defaults to `{kind:"defaults"}`. Disable DOES filter from `tools/list`. Root cause of "all load eagerly" is that ALL 10 IDE configs use `--toolsets all` or no flag with `isDefault:true` on trade-analytics/trade-planning only. MC4 must capture `tools/list` output for 3 modes. |
| F3 | Mapping mixes callable/ghost/spec/stub | Medium | **4-tier inventory** in §2 below. |
| F4 | Docs sync running last is backwards | Medium | **MC0 added** — build plan + registry updates BEFORE code MEUs. |
| F5 | [MCP-ZODSTRIP] not accounted for | Medium | Existing code already uses `registerTool()` with raw shapes (verified in `settings-tools.ts`). Compound tools MUST use same pattern. AC added: startup assertion for non-empty `inputSchema.properties` on all 13 compound tools. |
| F6 | zorivest_analytics is a weak bounded context | Medium | **Tax extracted to `zorivest_tax`** (4 stubs). Final count: **13 compound tools**, not 12. Honest count > forced consolidation. |

---

## 2. Tool Inventory (4-Tier Classification)

### Tier A: Currently Callable (59 tools — handler executes real logic)

| Toolset | Tools | Count |
|---------|-------|-------|
| core | `get_settings`, `update_settings`, `zorivest_diagnose`, `zorivest_launch_gui` | 4 |
| discovery | `list_available_toolsets`, `describe_toolset`, `enable_toolset`, `get_confirmation_token` | 4 |
| trade-analytics | `create_trade`, `list_trades`, `attach_screenshot`, `get_trade_screenshots`, `get_screenshot`, `get_analytics_summary`, `get_trade_streaks` | 7 |
| trade-planning | `calculate_position_size`, `create_trade_plan`, `list_trade_plans`, `delete_trade_plan`, `create_watchlist`, `list_watchlists`, `get_watchlist`, `add_to_watchlist`, `remove_from_watchlist` | 9 |
| market-data | `get_stock_quote`, `get_market_news`, `search_ticker`, `get_sec_filings`, `list_market_providers`, `disconnect_market_provider`, `test_market_provider` | 7 |
| accounts | `list_accounts`, `get_account`, `create_account`, `update_account`, `delete_account`, `archive_account`, `reassign_trades`, `record_balance`, `get_account_review_checklist` | 9 |
| scheduling | `create_policy`, `list_policies`, `run_pipeline`, `preview_report`, `update_policy_schedule`, `get_pipeline_history`, `delete_policy`, `update_policy`, `get_email_config` | 9 |
| pipeline-security | `emulate_policy`, `validate_sql`, `list_db_tables`, `get_db_row_samples`, `create_email_template`, `get_email_template`, `list_email_templates`, `update_email_template`, `delete_email_template`, `preview_email_template` | 10 |

### Tier B: Registry-Only / 501 Stub (14 tools — registered, returns 501)

| Toolset | Tools | Count |
|---------|-------|-------|
| accounts | `sync_broker`, `list_brokers`, `resolve_identifiers`, `import_bank_statement`, `import_broker_csv`, `import_broker_pdf`, `list_bank_accounts` | 7 |
| tax | `estimate_tax`, `find_wash_sales`, `manage_lots`, `harvest_losses` | 4 |
| pipeline-security | `list_step_types`, `list_provider_capabilities` | 2 |
| trade-planning | `create_trade` (cross-tag duplicate of trade-analytics) | 1 |

### Tier C: Ghost / No Handler (3 tools — in seed.ts `tools[]` but `register: () => []`)

| Toolset | Tools | Count |
|---------|-------|-------|
| behavioral | `track_mistakes`, `calculate_expectancy`, `monte_carlo_sim` | 3 |

### Tier D: Spec-Only / Future (8+ tools — in 05-mcp-server.md but not in seed.ts)

Emergency stop/unlock, service status/restart/logs, log settings, workspace setup — depend on unbuilt phases (10, 1A, 5.H).

**Summary**: 59 callable + 14 stubs + 3 ghosts + 1 cross-tag = **76 registered** (matches audit).

---

## 3. Target Architecture — 13 Compound Tools

### Alias Policy Decision

**No v1 aliases.** Clean cut. Rationale:
- SDK `tools/list` filters `enabled === false` tools from listing but still allows `tools/call` on disabled tools (throws `"Tool disabled"`). There is no "hidden but callable" mode.
- Registering aliases as separate tools inflates the count.
- Server instructions will document the compound tool names. Agent prompts update naturally.
- The `/mcp-audit` baseline validates the new names.

### Toolset Structure (10 → 4)

| Toolset | Compound Tools | Load | Count |
|---------|---------------|------|-------|
| `core` | `zorivest_system` | ✅ Always | 1 |
| `trade` | `zorivest_trade`, `zorivest_report`, `zorivest_plan`, `zorivest_analytics` | ✅ Default | 4 |
| `data` | `zorivest_market`, `zorivest_account`, `zorivest_watchlist`, `zorivest_import`, `zorivest_tax` | ⬜ Deferred | 5 |
| `ops` | `zorivest_policy`, `zorivest_template`, `zorivest_db` | ⬜ Deferred | 3 |

**Default visible: 5 tools** (core + trade). Deferred: 8 tools via `zorivest_system(action:"toolset_enable")`.

### Compound Tool → Action Mapping

Each action delegates to an existing handler function. No new business logic.

**1. `zorivest_system`** (core toolset, always loaded)

| Action | Tier | Current Tool | Handler |
|--------|------|-------------|---------|
| `diagnose` | A | `zorivest_diagnose` | `diagnostics-tools.ts` |
| `settings_get` | A | `get_settings` | `settings-tools.ts` |
| `settings_update` | A | `update_settings` | `settings-tools.ts` |
| `confirm_token` | A | `get_confirmation_token` | `discovery-tools.ts` |
| `launch_gui` | A | `zorivest_launch_gui` | `gui-tools.ts` |
| `email_config` | A | `get_email_config` | `scheduling-tools.ts` |
| `toolsets_list` | A | `list_available_toolsets` | `discovery-tools.ts` |
| `toolset_describe` | A | `describe_toolset` | `discovery-tools.ts` |
| `toolset_enable` | A | `enable_toolset` | `discovery-tools.ts` |

**2. `zorivest_trade`** (trade toolset)

| Action | Tier | Current Tool |
|--------|------|-------------|
| `create` | A | `create_trade` |
| `list` | A | `list_trades` |
| `delete` | A | `delete_trade` (implicit in trade-tools) |
| `screenshot_attach` | A | `attach_screenshot` |
| `screenshot_list` | A | `get_trade_screenshots` |
| `screenshot_get` | A | `get_screenshot` |

**3. `zorivest_report`** (trade toolset)

| Action | Tier | Current Tool |
|--------|------|-------------|
| `create` | A | `create_report` |
| `get` | A | `get_report_for_trade` |

**4. `zorivest_plan`** (trade toolset)

| Action | Tier | Current Tool |
|--------|------|-------------|
| `create` | A | `create_trade_plan` |
| `list` | A | `list_trade_plans` |
| `delete` | A | `delete_trade_plan` |

**5. `zorivest_analytics`** (trade toolset)

| Action | Tier | Current Tool |
|--------|------|-------------|
| `summary` | A | `get_analytics_summary` |
| `streaks` | A | `get_trade_streaks` |
| `position_size` | A | `calculate_position_size` |

Note: Future analytics actions (expectancy, sqn, drawdown, round_trips, etc.) added when their MEUs are implemented — not pre-stubbed.

**6. `zorivest_market`** (data toolset)

| Action | Tier | Current Tool |
|--------|------|-------------|
| `quote` | A | `get_stock_quote` |
| `news` | A | `get_market_news` |
| `search` | A | `search_ticker` |
| `filings` | A | `get_sec_filings` |
| `providers` | A | `list_market_providers` |
| `test_provider` | A | `test_market_provider` |
| `disconnect` | A | `disconnect_market_provider` |

**7. `zorivest_account`** (data toolset)

| Action | Tier | Current Tool |
|--------|------|-------------|
| `list` | A | `list_accounts` |
| `get` | A | `get_account` |
| `create` | A | `create_account` |
| `update` | A | `update_account` |
| `delete` | A | `delete_account` |
| `archive` | A | `archive_account` |
| `reassign` | A | `reassign_trades` |
| `balance` | A | `record_balance` |
| `checklist` | A | `get_account_review_checklist` |

**8. `zorivest_watchlist`** (data toolset)

| Action | Tier | Current Tool |
|--------|------|-------------|
| `list` | A | `list_watchlists` |
| `get` | A | `get_watchlist` |
| `create` | A | `create_watchlist` |
| `add_ticker` | A | `add_to_watchlist` |
| `remove_ticker` | A | `remove_from_watchlist` |

**9. `zorivest_import`** (data toolset)

| Action | Tier | Current Tool |
|--------|------|-------------|
| `broker_csv` | B | `import_broker_csv` |
| `broker_pdf` | B | `import_broker_pdf` |
| `bank_statement` | B | `import_bank_statement` |
| `sync_broker` | B | `sync_broker` |

**10. `zorivest_tax`** (data toolset)

| Action | Tier | Current Tool |
|--------|------|-------------|
| `estimate` | B | `estimate_tax` |
| `wash_sales` | B | `find_wash_sales` |
| `manage_lots` | B | `manage_lots` |
| `harvest` | B | `harvest_losses` |

**11. `zorivest_policy`** (ops toolset)

| Action | Tier | Current Tool |
|--------|------|-------------|
| `list` | A | `list_policies` |
| `create` | A | `create_policy` |
| `update` | A | `update_policy` |
| `delete` | A | `delete_policy` |
| `schedule` | A | `update_policy_schedule` |
| `run` | A | `run_pipeline` |
| `history` | A | `get_pipeline_history` |
| `emulate` | A | `emulate_policy` |
| `preview` | A | `preview_report` |

**12. `zorivest_template`** (ops toolset)

| Action | Tier | Current Tool |
|--------|------|-------------|
| `list` | A | `list_email_templates` |
| `get` | A | `get_email_template` |
| `create` | A | `create_email_template` |
| `update` | A | `update_email_template` |
| `delete` | A | `delete_email_template` |
| `preview` | A | `preview_email_template` |

**13. `zorivest_db`** (ops toolset)

| Action | Tier | Current Tool |
|--------|------|-------------|
| `tables` | A | `list_db_tables` |
| `samples` | A | `get_db_row_samples` |
| `validate_sql` | A | `validate_sql` |
| `step_types` | B | `list_step_types` |
| `provider_capabilities` | B | `list_provider_capabilities` |

### Omitted Tools

| Tool | Tier | Disposition |
|------|------|-------------|
| `list_brokers` | B | Redundant with `zorivest_import(action:"sync_broker")` response |
| `resolve_identifiers` | B | Folded into import step — no standalone compound action |
| `list_bank_accounts` | B | Folded into `zorivest_account(action:"list")` with type filter |
| `track_mistakes` | C | Ghost (no handler). Re-added when behavioral MEU implements it |
| `calculate_expectancy` | C | Ghost. Re-added when behavioral MEU implements it |
| `monte_carlo_sim` | C | Ghost. Re-added when behavioral MEU implements it |
| `create_trade` (cross-tag) | B | Duplicate registration removed. Only in `zorivest_trade` |

---

## 4. Schema Strategy ([MCP-ZODSTRIP] Compliance)

All compound tools MUST use:

1. **`registerTool()` with raw shapes** (not `server.tool()` with `z.object()`) — matches existing pattern in all 13 tool files.
2. **Zod discriminated union on `action` field** using raw shape:
   ```ts
   inputSchema: {
     action: z.enum(["list", "get", "create", ...]).describe("Action to perform"),
     // Per-action fields — all optional, validated in handler
     id: z.number().optional(),
     ...
   }
   ```
3. **Per-action validation inside handler** — the compound router validates action-specific required fields after dispatch (not via Zod discriminated union at registration, since raw shapes don't support it natively).
4. **Startup assertion**: `assert(Object.keys(tool.inputSchema.properties).length > 0)` for all 13 compound tools.
5. **Unknown action → MCP InvalidParams error** (not 500).

---

## 5. MEU Sequence (6 MEUs)

### MC0: Build Plan + Registry Sync (docs-first)

| Field | Value |
|-------|-------|
| **Slug** | `mcp-buildplan-presync` |
| **Effort** | ~2h |
| **Risk** | Low (documentation only) |

**Scope:**
1. Add P2.5f section to `BUILD_PLAN.md` with MC0–MC5 entries
2. Add P2.5f section to `meu-registry.md`
3. Update `05-mcp-server.md` §5.11: toolset table (10→4), compound tool catalog (76→13)
4. Rewrite `mcp-tool-index.md`: 76-row flat → 13-row compound with action sub-tables
5. Update `build-priority-matrix.md`

**AC:**
- AC-1: BUILD_PLAN.md contains MC0–MC5 with status/deliverables
- AC-2: mcp-tool-index.md describes 13 compound tools with action sub-tables
- AC-3: 05-mcp-server.md §5.11 shows 4 toolsets, 13 compound tools

### MC1: Compound Tool Infrastructure + `zorivest_system`

| Field | Value |
|-------|-------|
| **Slug** | `mcp-compound-infra` |
| **Effort** | ~4h |
| **Risk** | Low |

**Scope:**
1. Create `compound-router.ts`: action dispatch, per-action validation, error normalization
2. Consolidate core (4) + discovery (4) → `zorivest_system` (9 actions)
3. Remove 8 individual tool registrations
4. Startup assertion: non-empty `inputSchema.properties` on zorivest_system
5. Use `registerTool()` raw shape (ZODSTRIP compliance)

**AC:**
- AC-1: `zorivest_system(action:"diagnose")` returns same output as former `zorivest_diagnose`
- AC-2: `zorivest_system(action:"settings_get", key:"theme")` works
- AC-3: Unknown action returns MCP InvalidParams error
- AC-4: `tools/list` returns exactly N tools (76 − 8 + 1 = 69 during transition)
- AC-5: Startup assertion passes for non-empty inputSchema.properties

### MC2: CRUD Compounds — Template + Watchlist + Account + Import + Tax

| Field | Value |
|-------|-------|
| **Slug** | `mcp-crud-compounds` |
| **Effort** | ~4h |
| **Risk** | Low–Medium |

**Scope:**
1. `zorivest_template` (6 actions), `zorivest_watchlist` (5 actions), `zorivest_account` (9 actions), `zorivest_import` (4 actions), `zorivest_tax` (4 actions)
2. Migrate confirmation gates for destructive actions (delete_account, reassign_trades, delete_email_template)
3. Remove ~30 individual tool registrations + 3 redundant stubs (list_brokers, resolve_identifiers, list_bank_accounts)

**AC:**
- AC-1: `zorivest_account(action:"delete", ...)` requires confirmation_token
- AC-2: `zorivest_import(action:"broker_csv")` returns 501
- AC-3: `zorivest_tax(action:"estimate")` returns 501
- AC-4: `tools/list` count = 69 − 33 + 5 = 41
- AC-5: Boundary Input Contract: every action validates required fields, rejects extra fields

### MC3: Trade Compounds — Trade + Report + Plan + Analytics

| Field | Value |
|-------|-------|
| **Slug** | `mcp-trade-compounds` |
| **Effort** | ~4h |
| **Risk** | Medium |

**Scope:**
1. `zorivest_trade` (6 actions), `zorivest_report` (2 actions), `zorivest_plan` (3 actions), `zorivest_analytics` (3 actions)
2. Migrate confirmation gate for delete_trade, delete_trade_plan
3. Remove ~15 individual tool registrations + cross-tag duplicate

**AC:**
- AC-1: `zorivest_trade(action:"delete", ...)` requires confirmation_token
- AC-2: `zorivest_analytics(action:"position_size", ...)` returns same output
- AC-3: `tools/list` count = 41 − 16 + 4 = 29

### MC4: Ops Compounds + Deferred Loading + CI Gate

| Field | Value |
|-------|-------|
| **Slug** | `mcp-deferred-loading` |
| **Effort** | ~4h |
| **Risk** | Medium–High |

**Scope:**
1. `zorivest_market` (7 actions), `zorivest_policy` (9 actions), `zorivest_db` (5 actions)
2. Migrate confirmation gate for delete_policy, run_pipeline
3. Remove ~21 individual tool registrations
4. Restructure `seed.ts`: 10 toolset definitions → 4
5. Verify deferred loading works: capture `tools/list` for 3 modes
6. Add CI gate: fail if tool count > 13

**AC:**
- AC-1: `zorivest_policy(action:"delete", ...)` requires confirmation_token
- AC-2: **Empirical**: `tools/list` with no flag returns 5 tools (core + trade)
- AC-3: **Empirical**: `tools/list` with `--toolsets data` returns 10 tools (core + trade + data)
- AC-4: **Empirical**: `tools/list` with `--toolsets all` returns 13 tools
- AC-5: CI gate rejects tool_count > 13
- AC-6: Final `tools/list` count = 13

### MC5: Baseline Regen + Audit + Cleanup

| Field | Value |
|-------|-------|
| **Slug** | `mcp-baseline-audit` |
| **Effort** | ~2h |
| **Risk** | Low |

**Scope:**
1. Regenerate `baseline-snapshot.json` (76→13)
2. Run `/mcp-audit` against 13-tool baseline
3. Update server instructions (compound tool names, action examples)
4. Archive [MCP-TOOLPROLIFERATION] in known-issues.md
5. Update `current-focus.md`
6. Run full `validate_codebase.py`

**AC:**
- AC-1: `/mcp-audit` passes with 13-tool baseline
- AC-2: `validate_codebase.py` passes
- AC-3: [MCP-TOOLPROLIFERATION] archived

---

## 6. Boundary Input Contract Coverage

Every compound action MUST satisfy:

1. **Schema owner**: Zod raw shape in `registerTool()` config
2. **Action validation**: `z.enum([...])` on action field — unknown → InvalidParams
3. **Per-action required fields**: Validated in handler, not schema (raw shape limitation)
4. **Extra-field policy**: Zod `passthrough` at schema level (raw shapes don't support strict); handler ignores unknown fields
5. **Error mapping**: Invalid action → MCP InvalidParams; missing required field → MCP InvalidParams; API error → tool error response
6. **Destructive action gates**: Actions mapped to destructive operations require `confirmation_token` parameter — same middleware as current individual tools

---

## 7. Exit Criteria

- [ ] Total MCP tools in `tools/list`: **≤ 13**
- [ ] Default-loaded tools (no flag): **≤ 5** (core: 1, trade: 4)
- [ ] `tools/list` captured for: no-flag, `--toolsets data`, `--toolsets all`
- [ ] All existing `/mcp-audit` CRUD tests pass with compound names
- [ ] CI gate: fail if `tool_count > 13`
- [ ] Deferred loading verified (data + ops load on `toolset_enable`)
- [ ] Build plan files updated BEFORE code (MC0)
- [ ] `baseline-snapshot.json` updated to 13-tool baseline
- [ ] [MCP-TOOLPROLIFERATION] archived
- [ ] All compound tools use `registerTool()` raw shapes (ZODSTRIP compliant)
- [ ] Startup assertion: non-empty `inputSchema.properties` on all 13 tools

---

## 8. Effort Summary

| MEU | Slug | Effort | Risk | Δ Tools |
|-----|------|--------|------|---------|
| MC0 | `mcp-buildplan-presync` | ~2h | Low | Docs only |
| MC1 | `mcp-compound-infra` | ~4h | Low | 76→69 |
| MC2 | `mcp-crud-compounds` | ~4h | Low–Med | 69→41 |
| MC3 | `mcp-trade-compounds` | ~4h | Medium | 41→29 |
| MC4 | `mcp-deferred-loading` | ~4h | Med–High | 29→13 |
| MC5 | `mcp-baseline-audit` | ~2h | Low | Verification |
| **Total** | | **~20h** | | **76 → 13** |
