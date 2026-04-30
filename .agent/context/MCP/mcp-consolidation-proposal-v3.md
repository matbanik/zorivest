# MCP Tool Consolidation — Corrected Proposal v3.1

> **Status**: Corrected — ready for Codex review
> **Date**: 2026-04-29
> **Phase**: P2.5f — MCP Tool Consolidation
> **Prerequisite**: P2.5e ✅
> **Supersedes**: v1, v2

---

## 1. v2→v3 Corrections

| # | v2 Finding | Resolution in v3 |
|---|-----------|-------------------|
| H1 | Analytics inventory dropped 11 callable tools | **Fixed.** Built inventory from `registerTool()` calls, not `seed.ts`. All 14 analytics-tools.ts registrations preserved. `get_analytics_summary` and `get_trade_streaks` confirmed as **ghost** (in seed.ts metadata, no registerTool) — correctly omitted. |
| H2 | `list_step_types` and `list_provider_capabilities` misclassified as stubs | **Fixed.** Both are Tier A callable (fetchApi to real endpoints: `/scheduling/step-types`, `/market-data/providers`). Reclassified. |
| M1 | Omitted tools were silent product decisions | **Fixed.** `list_brokers`, `resolve_identifiers`, `list_bank_accounts` preserved as 501 actions in their compound tools. No removals without explicit approval. |
| M2 | Extra-field passthrough violates repo boundary contract | **Fixed.** `z.object({...}).strict()` at registration level rejects unknown top-level fields via SDK validation. Per-action strict schemas in compound router reject unknown action-specific fields. |
| M3 | Transition counts were wrong | **Fixed.** Recalculated from 85 actual registrations. |
| L1 | `--toolsets data` behavior under-specified | **Fixed.** Explicit mode: `alwaysLoaded + explicitly named only`. Trade defaults NOT auto-included. Documented in §6. |

---

## 2. Ground-Truth Tool Inventory

**Source**: `Select-String -Pattern 'registerTool\(' -Path "*.ts"` across all 13 tool files.
**Total**: 85 `registerTool()` calls.

### Callable (78 tools — handler calls fetchApi, uploadFile, or executes real logic)

| Source File | Tools | Count |
|-------------|-------|-------|
| `accounts-tools.ts` | `sync_broker`, `import_bank_statement`, `import_broker_csv`, `import_broker_pdf`, `get_account_review_checklist`, `list_accounts`, `get_account`, `create_account`, `update_account`, `delete_account`, `archive_account`, `reassign_trades`, `record_balance` | 13 |
| `analytics-tools.ts` | `get_round_trips`, `enrich_trade_excursion`, `get_fee_breakdown`, `score_execution_quality`, `estimate_pfof_impact`, `get_expectancy_metrics`, `simulate_drawdown`, `get_strategy_breakdown`, `get_sqn`, `get_cost_of_free`, `ai_review_trade`, `detect_options_strategy`, `create_report`, `get_report_for_trade` | 14 |
| `calculator-tools.ts` | `calculate_position_size` | 1 |
| `diagnostics-tools.ts` | `zorivest_diagnose` | 1 |
| `discovery-tools.ts` | `list_available_toolsets`, `describe_toolset`, `enable_toolset`, `get_confirmation_token` | 4 |
| `gui-tools.ts` | `zorivest_launch_gui` | 1 |
| `market-data-tools.ts` | `get_stock_quote`, `get_market_news`, `search_ticker`, `get_sec_filings`, `list_market_providers`, `disconnect_market_provider`, `test_market_provider` | 7 |
| `pipeline-security-tools.ts` | `emulate_policy`, `validate_sql`, `list_db_tables`, `get_db_row_samples`, `create_email_template`, `get_email_template`, `list_email_templates`, `update_email_template`, `delete_email_template`, `preview_email_template`, `list_step_types`, `list_provider_capabilities` | 12 |
| `planning-tools.ts` | `create_trade_plan`, `create_watchlist`, `list_watchlists`, `get_watchlist`, `add_to_watchlist`, `remove_from_watchlist`, `list_trade_plans`, `delete_trade_plan` | 8 |
| `scheduling-tools.ts` | `create_policy`, `list_policies`, `run_pipeline`, `preview_report`, `update_policy_schedule`, `get_pipeline_history`, `delete_policy`, `update_policy`, `get_email_config` | 9 |
| `settings-tools.ts` | `get_settings`, `update_settings` | 2 |
| `trade-tools.ts` | `create_trade`, `list_trades`, `attach_screenshot`, `get_trade_screenshots`, `get_screenshot`, `delete_trade` | 6 |
| **Callable subtotal** | | **78** |

### 501 Stubs (7 tools — registered, returns structured 501 "Not Implemented")

| Source File | Tools | Count |
|-------------|-------|-------|
| `accounts-tools.ts` | `list_brokers`, `resolve_identifiers`, `list_bank_accounts` | 3 |
| `tax-tools.ts` | `estimate_tax`, `find_wash_sales`, `manage_lots`, `harvest_losses` | 4 |
| **Stub subtotal** | | **7** |

### Ghosts (2 names in seed.ts metadata, NO registerTool call)

`get_analytics_summary`, `get_trade_streaks` — in `seed.ts` TOOLSET_DEFINITIONS[].tools[] but no matching `registerTool()` in any source file. Never registered with the SDK.

### Spec-Only (not in seed.ts or any tool file)

Emergency stop/unlock, service status/restart/logs, log settings, workspace setup — depend on unbuilt phases.

**Total registered: 78 callable + 7 stubs = 85 `registerTool()` calls.**

---

## 3. Target Architecture — 13 Compound Tools

### Alias Policy

**No v1 aliases. Clean cut.** Old tool names are not re-registered. Agents calling old names get `Tool not found`. Server instructions document new compound names.

### Toolset Structure (10 current → 4 target)

| Toolset | Compound Tools | Load | Visible Count |
|---------|---------------|------|---------------|
| `core` | `zorivest_system` | ✅ Always | 1 |
| `trade` | `zorivest_trade`, `zorivest_report`, `zorivest_analytics` | ✅ Default | 3 |
| `data` | `zorivest_market`, `zorivest_account`, `zorivest_watchlist`, `zorivest_import`, `zorivest_tax` | ⬜ Deferred | 5 |
| `ops` | `zorivest_plan`, `zorivest_policy`, `zorivest_template`, `zorivest_db` | ⬜ Deferred | 4 |

**Default visible**: 4 tools (core + trade). Deferred: 9 tools via `zorivest_system(action:"toolset_enable")`.

### Compound Tool → Action Mapping

**1. `zorivest_system`** (core, always loaded) — 9 actions

| Action | Source Tool | Tier |
|--------|-----------|------|
| `diagnose` | `zorivest_diagnose` | A |
| `settings_get` | `get_settings` | A |
| `settings_update` | `update_settings` | A |
| `confirm_token` | `get_confirmation_token` | A |
| `launch_gui` | `zorivest_launch_gui` | A |
| `email_config` | `get_email_config` | A |
| `toolsets_list` | `list_available_toolsets` | A |
| `toolset_describe` | `describe_toolset` | A |
| `toolset_enable` | `enable_toolset` | A |

**2. `zorivest_trade`** (trade, default) — 6 actions

| Action | Source Tool | Tier |
|--------|-----------|------|
| `create` | `create_trade` | A |
| `list` | `list_trades` | A |
| `delete` | `delete_trade` | A |
| `screenshot_attach` | `attach_screenshot` | A |
| `screenshot_list` | `get_trade_screenshots` | A |
| `screenshot_get` | `get_screenshot` | A |

**3. `zorivest_report`** (trade, default) — 2 actions

| Action | Source Tool | Tier |
|--------|-----------|------|
| `create` | `create_report` | A |
| `get` | `get_report_for_trade` | A |

**4. `zorivest_analytics`** (trade, default) — 13 actions

| Action | Source Tool | Tier |
|--------|-----------|------|
| `position_size` | `calculate_position_size` | A |
| `round_trips` | `get_round_trips` | A |
| `excursion` | `enrich_trade_excursion` | A |
| `fee_breakdown` | `get_fee_breakdown` | A |
| `execution_quality` | `score_execution_quality` | A |
| `pfof_impact` | `estimate_pfof_impact` | A |
| `expectancy` | `get_expectancy_metrics` | A |
| `drawdown` | `simulate_drawdown` | A |
| `strategy_breakdown` | `get_strategy_breakdown` | A |
| `sqn` | `get_sqn` | A |
| `cost_of_free` | `get_cost_of_free` | A |
| `ai_review` | `ai_review_trade` | A |
| `options_strategy` | `detect_options_strategy` | A |

**5. `zorivest_market`** (data, deferred) — 7 actions

| Action | Source Tool | Tier |
|--------|-----------|------|
| `quote` | `get_stock_quote` | A |
| `news` | `get_market_news` | A |
| `search` | `search_ticker` | A |
| `filings` | `get_sec_filings` | A |
| `providers` | `list_market_providers` | A |
| `test_provider` | `test_market_provider` | A |
| `disconnect` | `disconnect_market_provider` | A |

**6. `zorivest_account`** (data, deferred) — 9 actions

| Action | Source Tool | Tier |
|--------|-----------|------|
| `list` | `list_accounts` | A |
| `get` | `get_account` | A |
| `create` | `create_account` | A |
| `update` | `update_account` | A |
| `delete` | `delete_account` | A |
| `archive` | `archive_account` | A |
| `reassign` | `reassign_trades` | A |
| `balance` | `record_balance` | A |
| `checklist` | `get_account_review_checklist` | A |

**7. `zorivest_watchlist`** (data, deferred) — 5 actions

| Action | Source Tool | Tier |
|--------|-----------|------|
| `list` | `list_watchlists` | A |
| `get` | `get_watchlist` | A |
| `create` | `create_watchlist` | A |
| `add_ticker` | `add_to_watchlist` | A |
| `remove_ticker` | `remove_from_watchlist` | A |

**8. `zorivest_import`** (data, deferred) — 7 actions

| Action | Source Tool | Tier |
|--------|-----------|------|
| `broker_csv` | `import_broker_csv` | A |
| `broker_pdf` | `import_broker_pdf` | A |
| `bank_statement` | `import_bank_statement` | A |
| `sync_broker` | `sync_broker` | A |
| `list_brokers` | `list_brokers` | B (501) |
| `resolve_identifiers` | `resolve_identifiers` | B (501) |
| `list_bank_accounts` | `list_bank_accounts` | B (501) |

**9. `zorivest_tax`** (data, deferred) — 4 actions

| Action | Source Tool | Tier |
|--------|-----------|------|
| `estimate` | `estimate_tax` | B (501) |
| `wash_sales` | `find_wash_sales` | B (501) |
| `manage_lots` | `manage_lots` | B (501) |
| `harvest` | `harvest_losses` | B (501) |

**10. `zorivest_plan`** (ops, deferred) — 3 actions

| Action | Source Tool | Tier |
|--------|-----------|------|
| `create` | `create_trade_plan` | A |
| `list` | `list_trade_plans` | A |
| `delete` | `delete_trade_plan` | A |

**11. `zorivest_policy`** (ops, deferred) — 9 actions

| Action | Source Tool | Tier |
|--------|-----------|------|
| `list` | `list_policies` | A |
| `create` | `create_policy` | A |
| `update` | `update_policy` | A |
| `delete` | `delete_policy` | A |
| `schedule` | `update_policy_schedule` | A |
| `run` | `run_pipeline` | A |
| `history` | `get_pipeline_history` | A |
| `emulate` | `emulate_policy` | A |
| `preview` | `preview_report` | A |

**12. `zorivest_template`** (ops, deferred) — 6 actions

| Action | Source Tool | Tier |
|--------|-----------|------|
| `list` | `list_email_templates` | A |
| `get` | `get_email_template` | A |
| `create` | `create_email_template` | A |
| `update` | `update_email_template` | A |
| `delete` | `delete_email_template` | A |
| `preview` | `preview_email_template` | A |

**13. `zorivest_db`** (ops, deferred) — 5 actions

| Action | Source Tool | Tier |
|--------|-----------|------|
| `tables` | `list_db_tables` | A |
| `samples` | `get_db_row_samples` | A |
| `validate_sql` | `validate_sql` | A |
| `step_types` | `list_step_types` | A |
| `provider_capabilities` | `list_provider_capabilities` | A |

### Coverage Verification

Total actions across 13 compound tools: 9+6+2+13+7+9+5+7+4+3+9+6+5 = **85 actions**.
Source tools mapped: **85 registerTool() calls** → 85 compound actions.
**Zero tools dropped. Zero silent product decisions.**

---

## 4. Boundary Input Contract

Per repo rules (`extra="forbid"` unless source-backed exception):

1. **Action field**: `z.enum([...])` — unknown action → MCP InvalidParams (SDK-level validation)
2. **Top-level unknown fields**: Rejected by `z.object({...}).strict()` at registration level → SDK returns InvalidParams before handler runs
3. **Per-action required fields**: Validated in compound router dispatch via per-action strict Zod schemas. Missing required field → MCP InvalidParams
4. **Per-action unknown fields**: Each action handler parses its params through a strict sub-schema. Extra keys → InvalidParams from router
5. **Error mapping**: Invalid action → InvalidParams; missing field → InvalidParams; unknown field → InvalidParams; API error → tool error response
6. **Destructive gates**: Actions mapped to destructive operations require `confirmation_token` — same `withConfirmation` middleware

---

## 5. Schema Strategy

### ZODSTRIP Analysis (Empirical)

[MCP-ZODSTRIP] is specific to `server.tool()` — the legacy overload API where `z.object()` can be misinterpreted as annotations during argument parsing. `server.registerTool()` takes a structured config object with an explicit `inputSchema` field — no overload ambiguity.

SDK code path for `registerTool()` (verified in `mcp.js`):
1. `registerTool(name, config, cb)` → extracts `config.inputSchema` (line 702)
2. `_createRegisteredTool(...)` → `getZodSchemaObject(inputSchema)` (line 611)
3. `getZodSchemaObject`: if input is a raw shape → wraps with `objectFromShape()`; if already a `z.object()` → **returns as-is** (line 867)
4. Validation: `normalizeObjectSchema()` → returns schema as-is if it has `shape` property (line 116-117) → `safeParseAsync()` runs with full `.strict()` semantics
5. JSON Schema generation: `toJsonSchemaCompat()` correctly converts `.strict()` schemas for `tools/list`

**Conclusion**: `z.object({...}).strict()` with `registerTool()` is safe. The `.strict()` modifier is preserved through storage, validation, and JSON Schema generation.

### Compound Tool Schema Pattern

Each compound tool registers with `z.object({...}).strict()`:

```ts
server.registerTool("zorivest_account", {
  inputSchema: z.object({
    action: z.enum(["list", "get", "create", "update", "delete", "archive", "reassign", "balance", "checklist"]),
    account_id: z.string().optional(),
    // ... all per-action fields as optional
    confirmation_token: z.string().optional(),
  }).strict(),
  // ...
}, handler);
```

- `.strict()` rejects unknown top-level keys at SDK validation (before handler)
- `action` enum rejects unknown actions at SDK validation
- Handler's compound router validates per-action required fields and rejects per-action unknowns
- Startup assertion: verify each compound tool's stored Zod schema has a non-empty shape (via `getObjectShape(tool.inputSchema)`) — not JSON Schema `.properties`, since `registerTool()` stores Zod objects internally

---

## 6. Deferred Loading Contract

Current `isToolsetEnabled()` logic (verified in `registration.ts:83-100`):

| Selection Mode | Behavior |
|---------------|----------|
| `kind: "all"` | All toolsets enabled |
| `kind: "defaults"` | `alwaysLoaded` OR `isDefault === true` |
| `kind: "explicit"` | `alwaysLoaded` OR `selection.names.includes(name)` |

**Explicit mode does NOT auto-include defaults.** `--toolsets data` enables `alwaysLoaded + data` only — NOT trade defaults. This is correct behavior per current implementation and will be preserved.

**Expected `tools/list` counts after consolidation:**

| Flag | Selection | Toolsets Enabled | Tool Count |
|------|-----------|-----------------|------------|
| (none/default) | `kind: "defaults"` | core + trade | 4 |
| `--toolsets data` | `kind: "explicit"` | core + data | 6 |
| `--toolsets trade,data` | `kind: "explicit"` | core + trade + data | 9 |
| `--toolsets all` | `kind: "all"` | all | 13 |

---

## 7. MEU Sequence (6 MEUs)

### MC0: Build Plan + Registry Sync

| Field | Value |
|-------|-------|
| **Effort** | ~2h |
| **Risk** | Low |

**Scope**: Update BUILD_PLAN.md, meu-registry.md, 05-mcp-server.md §5.11, mcp-tool-index.md, build-priority-matrix.md

**AC**: AC-1: BUILD_PLAN.md has MC0–MC5. AC-2: mcp-tool-index.md describes 13 compound tools (85 actions). AC-3: 05-mcp-server.md shows 4 toolsets, 13 compound tools.

### MC1: Compound Router + `zorivest_system`

| Field | Value |
|-------|-------|
| **Effort** | ~4h |
| **Risk** | Low |

**Scope**: Create compound-router.ts (action dispatch, strict per-action validation, error normalization). Consolidate core (4) + discovery (4) + gui (1) → `zorivest_system` (9 actions). Remove 9 individual registrations.

**AC**: AC-1: `zorivest_system(action:"diagnose")` returns same output. AC-2: Unknown action → InvalidParams. AC-3: Extra fields rejected → InvalidParams. AC-4: `tools/list` count = 85 − 9 + 1 = **77**. AC-5: Startup assertion passes.

### MC2: Trade Compounds — Trade + Report + Analytics

| Field | Value |
|-------|-------|
| **Effort** | ~5h |
| **Risk** | Medium |

**Scope**: `zorivest_trade` (6 actions from trade-tools.ts), `zorivest_report` (2 actions from analytics-tools.ts), `zorivest_analytics` (13 actions from analytics-tools.ts + calculator-tools.ts). Remove 21 individual registrations.

**AC**: AC-1: `zorivest_trade(action:"delete")` requires confirmation_token. AC-2: All 13 analytics actions callable. AC-3: `zorivest_analytics(action:"ai_review")` returns same output. AC-4: `tools/list` count = 77 − 21 + 3 = **59**.

### MC3: Data Compounds — Market + Account + Watchlist + Import + Tax

| Field | Value |
|-------|-------|
| **Effort** | ~5h |
| **Risk** | Low–Medium |

**Scope**: `zorivest_market` (7), `zorivest_account` (9), `zorivest_watchlist` (5), `zorivest_import` (7), `zorivest_tax` (4). All 501 stubs preserved as compound actions. Remove 32 individual registrations.

**AC**: AC-1: `zorivest_account(action:"delete")` requires confirmation_token. AC-2: `zorivest_import(action:"list_brokers")` returns 501. AC-3: `zorivest_import(action:"resolve_identifiers")` returns 501. AC-4: `zorivest_import(action:"list_bank_accounts")` returns 501. AC-5: `zorivest_tax(action:"estimate")` returns 501. AC-6: `tools/list` count = 59 − 32 + 5 = **32**.

### MC4: Ops Compounds + Deferred Loading + CI Gate

| Field | Value |
|-------|-------|
| **Effort** | ~5h |
| **Risk** | Medium–High |

**Scope**: `zorivest_plan` (3), `zorivest_policy` (9), `zorivest_template` (6), `zorivest_db` (5). Remove 23 individual registrations. Restructure seed.ts (10→4 toolsets). CI gate: fail if tool_count > 13.

**AC**: AC-1: `zorivest_policy(action:"delete")` requires confirmation_token. AC-2: `zorivest_db(action:"step_types")` returns real data. AC-3: `zorivest_db(action:"provider_capabilities")` returns real data. AC-4: **Empirical**: `tools/list` with defaults → 4 tools (core + trade). AC-5: **Empirical**: `tools/list` with `--toolsets data` → 6 tools (core + data). AC-6: **Empirical**: `tools/list` with `--toolsets all` → 13 tools. AC-7: CI gate rejects tool_count > 13. AC-8: `tools/list` count = 32 − 23 + 4 = **13**. AC-9: **Empirical**: `zorivest_system(action:"toolset_enable", toolset:"ops")` → subsequent `tools/list` shows 5 tools (core + ops), confirming dynamic enablement.

### MC5: Baseline Regen + Audit + Cleanup

| Field | Value |
|-------|-------|
| **Effort** | ~2h |
| **Risk** | Low |

**Scope**: Regenerate baseline-snapshot.json (85→13). Run /mcp-audit. Update server instructions. Archive [MCP-TOOLPROLIFERATION]. Run validate_codebase.py.

**AC**: AC-1: /mcp-audit passes with 13-tool baseline. AC-2: validate_codebase.py passes. AC-3: [MCP-TOOLPROLIFERATION] archived.

---

## 8. Transition Count Trace

| After MEU | Removed | Added | Running Total |
|-----------|---------|-------|---------------|
| Start | — | — | 85 |
| MC1 | 9 (core+discovery+gui+settings+email_config) | 1 (zorivest_system) | 77 |
| MC2 | 21 (trade-tools+analytics-tools+calculator-tools) | 3 (zorivest_trade, zorivest_report, zorivest_analytics) | 59 |
| MC3 | 32 (market+accounts+planning-watchlists+tax) | 5 (zorivest_market, zorivest_account, zorivest_watchlist, zorivest_import, zorivest_tax) | 32 |
| MC4 | 23 (planning-plans+scheduling+pipeline-security) | 4 (zorivest_plan, zorivest_policy, zorivest_template, zorivest_db) | 13 |

**Verification**: 85 − 9 − 21 − 32 − 23 + 1 + 3 + 5 + 4 = 85 − 85 + 13 = **13** ✅

---

## 9. Exit Criteria

- [ ] Total MCP tools in `tools/list`: **≤ 13**
- [ ] Default-loaded tools (no flag): **4** (core: 1, trade: 3)
- [ ] `tools/list` captured for: defaults, `--toolsets data`, `--toolsets all`
- [ ] All 85 current tool functions preserved as compound actions (zero dropped)
- [ ] All 7 current 501 stubs preserved as 501 compound actions
- [ ] CI gate: fail if `tool_count > 13`
- [ ] Deferred loading verified (data + ops load on `toolset_enable`)
- [ ] Build plan files updated BEFORE code (MC0)
- [ ] `baseline-snapshot.json` updated to 13-tool baseline
- [ ] [MCP-TOOLPROLIFERATION] archived
- [ ] All compound tools use `registerTool()` with `z.object().strict()` (ZODSTRIP-safe — `registerTool()` path preserves schema)
- [ ] Startup assertion: non-empty Zod shape (via `getObjectShape()`) on all 13 compound tools
- [ ] Per-action validation rejects unknown fields with InvalidParams
- [ ] MCP Resources (6 in pipeline-security-tools.ts) remain unchanged

---

## 10. Effort Summary

| MEU | Effort | Risk | Δ Tools |
|-----|--------|------|---------|
| MC0 | ~2h | Low | Docs only |
| MC1 | ~4h | Low | 85→77 |
| MC2 | ~5h | Medium | 77→59 |
| MC3 | ~5h | Low–Med | 59→32 |
| MC4 | ~5h | Med–High | 32→13 |
| MC5 | ~2h | Low | Verification |
| **Total** | **~23h** | | **85 → 13** |
