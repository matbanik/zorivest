---
project: "2026-04-29-mcp-consolidation"
date: "2026-04-29"
source: "docs/build-plan/05-mcp-server.md"
meus: ["MC0", "MC1", "MC2", "MC3", "MC4", "MC5"]
status: "draft"
template_version: "2.0"
---

# Implementation Plan: MCP Tool Consolidation (P2.5f)

> **Project**: `2026-04-29-mcp-consolidation`
> **Build Plan Section(s)**: [05-mcp-server.md](../../build-plan/05-mcp-server.md), new P2.5f sub-phase
> **Status**: `draft`
> **Baseline Proposal**: [mcp-consolidation-proposal-v3.1](../../../../.agent/context/MCP/mcp-consolidation-proposal-v3.md)

---

## Goal

The Zorivest MCP server currently registers **85 individual tools** (`registerTool()` calls) across 13 source files. Most MCP clients warn or hard-cap at 60–80 tools; tool definitions consume ~20–30K tokens of context window. This project consolidates all 85 registrations into **13 compound tools** using discriminated-union action routing, strict boundary validation (`z.object().strict()`), and deferred toolset loading — delivering a clean, maintainable tool surface for AI agents.

**Resolves**: [MCP-TOOLPROLIFERATION]
**Prerequisite**: P2.5e ✅ (MCP Tool Remediation complete)

---

## User Review Required

> [!IMPORTANT]
> 1. **Zero-drop guarantee**: All 78 callable tools and 7 stubs are preserved as compound actions. No functionality is removed.
> 2. **No backward compatibility aliases**: Old tool names (`create_trade`, `list_accounts`, etc.) stop working after their MC step completes. AI agents will need to use the new compound tool names (`zorivest_trade(action:"create")`, `zorivest_account(action:"list")`). This is an intentional clean cut — no deprecation window.
> 3. **TypeScript-only project**: No Python code changes. All work is in `mcp-server/src/**`.

---

## Proposed Changes

### MC0 — Documentation Sync

Update BUILD_PLAN.md, meu-registry.md, known-issues.md, 05-mcp-server.md, mcp-tool-index.md, and build-priority-matrix.md to reflect the consolidation project before any code changes.

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-0.1 | P2.5f section exists in BUILD_PLAN.md with 6 MEU rows | Spec (v3.1 §7) | N/A (docs-only) |
| AC-0.2 | MC0–MC5 registered in meu-registry.md | Local Canon (AGENTS.md §MEU Boundaries) | N/A |
| AC-0.3 | P2.5e status corrected to ✅ in BUILD_PLAN.md | Local Canon (observed drift) | N/A |
| AC-0.4 | [MCP-TOOLPROLIFERATION] status updated to "In Progress" | Local Canon (known-issues.md) | N/A |
| AC-0.5 | `05-mcp-server.md` §5.11 updated to show 4 toolsets, 13 compound tools | Spec (v3.1 §7 MC0 AC-3) | N/A |
| AC-0.6 | `mcp-tool-index.md` created describing 13 compound tools (85 actions) | Spec (v3.1 §7 MC0 AC-2) | N/A |
| AC-0.7 | `build-priority-matrix.md` updated with P2.5f entries | Spec (v3.1 §7 MC0) | N/A |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `docs/BUILD_PLAN.md` | modify | Add P2.5f section (6 MEU rows), fix P2.5e status, update Phase 9 tracker |
| `.agent/context/meu-registry.md` | modify | Add P2.5f section with MC0–MC5 entries |
| `.agent/context/known-issues.md` | modify | Update [MCP-TOOLPROLIFERATION] status |
| `docs/build-plan/05-mcp-server.md` | modify | Update §5.11 to show 4 toolsets, 13 compound tools |
| `.agent/context/MCP/mcp-tool-index.md` | new | 13 compound tools with 85 action mappings |
| `docs/build-plan/build-priority-matrix.md` | modify | Add P2.5f entries |

---

### MC1 — Infrastructure + Core Compound Tool

Implement the CompoundToolRouter utility and create `zorivest_system` — the first compound tool absorbing 9 individual tools from core/discovery/gui/settings/scheduling-config.

#### Boundary Inventory

| Surface | Schema Owner | Field Constraints | Extra-Field Policy |
|---------|-------------|-------------------|-------------------|
| MCP tool input (`zorivest_system`) | `z.object({action: z.enum([...])}).strict()` via `registerTool()` | `action` = 9 known values; per-action fields optional at top level, validated required by router | `.strict()` → SDK rejects unknown top-level fields with InvalidParams |

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-1.1 | `CompoundToolRouter` class exists in `mcp-server/src/compound/router.ts` with `dispatch(action, params)` method | Spec (v3.1 §5) | N/A |
| AC-1.2 | Router validates per-action params via strict Zod sub-schemas; unknown action-specific fields → InvalidParams | Spec (v3.1 §4 item 4) | Pass `{action:"diagnose", bogus_field:"x"}` → InvalidParams |
| AC-1.3 | `zorivest_system` registered with `registerTool()` + `z.object({...}).strict()` | Spec (v3.1 §5) | Pass `{action:"diagnose", unknown_top:"x"}` → SDK InvalidParams |
| AC-1.4 | `zorivest_system` routes 9 actions: `diagnose`, `launch_gui`, `settings_get`, `settings_update`, `toolsets_list`, `toolset_describe`, `toolset_enable`, `confirm_token`, `email_config` | Spec (v3.1 §3) | N/A |
| AC-1.5 | 9 old registrations removed from their source files | Spec (v3.1 §8, MC1 removes 9) | N/A |
| AC-1.6 | `tools/list` count = 85 − 9 + 1 = **77** | Spec (v3.1 §8) | N/A |
| AC-1.7 | Destructive system actions (none currently) preserve `withConfirmation` if applicable | Local Canon (emerging-standards M3) | N/A |
| AC-1.8 | `npm run build` succeeds after changes | Local Canon (emerging-standards M4) | N/A |
| AC-1.9 | `npx vitest run` passes (existing + new tests) | Local Canon (AGENTS.md §Testing) | N/A |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| CompoundToolRouter dispatch pattern | Spec | v3.1 §5 — action enum + per-action strict sub-schema |
| zorivest_system action list | Spec | v3.1 §3 compound tool table — 9 actions |
| 501 stubs in import tool | Spec | v3.1 §3 — list_brokers, resolve_identifiers, list_bank_accounts preserved as 501 in zorivest_import |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `mcp-server/src/compound/router.ts` | new | CompoundToolRouter class |
| `mcp-server/src/compound/system-tool.ts` | new | zorivest_system compound tool registration |
| `mcp-server/src/compound/index.ts` | new | Barrel export |
| `mcp-server/src/tools/diagnostics-tools.ts` | modify | Remove `zorivest_diagnose` registration (absorbed) |
| `mcp-server/src/tools/gui-tools.ts` | modify | Remove `zorivest_launch_gui` registration (absorbed) |
| `mcp-server/src/tools/settings-tools.ts` | modify | Remove `get_settings`, `update_settings` registrations (absorbed) |
| `mcp-server/src/tools/discovery-tools.ts` | modify | Remove 4 discovery tool registrations (absorbed) |
| `mcp-server/src/tools/scheduling-tools.ts` | modify | Remove `get_email_config` registration (absorbed) |
| `mcp-server/src/toolsets/seed.ts` | modify | Update toolset definitions for core/discovery toolsets |
| `mcp-server/tests/compound/router.test.ts` | new | CompoundToolRouter unit tests |
| `mcp-server/tests/compound/system-tool.test.ts` | new | zorivest_system integration tests |

---

### MC2 — Trade Toolset Compound Tools

Consolidate trade-tools.ts (6), analytics-tools.ts (14), and calculator-tools.ts (1) into 3 compound tools: `zorivest_trade` (6 actions), `zorivest_report` (2 actions), `zorivest_analytics` (13 actions).

#### Boundary Inventory

| Surface | Schema Owner | Field Constraints | Extra-Field Policy |
|---------|-------------|-------------------|-------------------|
| MCP `zorivest_trade` | `z.object({action: z.enum(6)}).strict()` | `action` in `[create,list,delete,screenshot_attach,screenshot_list,screenshot_get]` | `.strict()` rejects unknowns |
| MCP `zorivest_report` | `z.object({action: z.enum(2)}).strict()` | `action` in `[create,get_for_trade]` | `.strict()` rejects unknowns |
| MCP `zorivest_analytics` | `z.object({action: z.enum(13)}).strict()` | `action` in `[position_size,round_trips,excursion,fees,execution_quality,pfof,expectancy,drawdown,strategy,sqn,cost_of_free,ai_review,options_strategy]` | `.strict()` rejects unknowns |

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-2.1 | `zorivest_trade` registered with 6 actions mapping to current trade-tools.ts | Spec (v3.1 §3) | Unknown action → InvalidParams |
| AC-2.2 | `zorivest_report` registered with 2 actions mapping to analytics-tools.ts report functions | Spec (v3.1 §3) | Unknown action → InvalidParams |
| AC-2.3 | `zorivest_analytics` registered with 13 actions including `position_size` from calculator-tools.ts | Spec (v3.1 §3) | Unknown action → InvalidParams |
| AC-2.4 | `delete_trade` action requires `confirmation_token` via `withConfirmation` | Local Canon (M3) | Missing token → confirmation prompt |
| AC-2.5 | `calculate_position_size` absorbed into `zorivest_analytics(action:"position_size")` | Spec (v3.1 §3) | N/A |
| AC-2.6 | 21 old registrations removed | Spec (v3.1 §8, MC2 removes 21) | N/A |
| AC-2.7 | `tools/list` count = 77 − 21 + 3 = **59** | Spec (v3.1 §8) | N/A |
| AC-2.8 | All analytics tool handlers call `fetchApi` to the same endpoints as before | Local Canon (zero-drop guarantee) | N/A |
| AC-2.9 | `npm run build` + `npx vitest run` pass | Local Canon (M4) | N/A |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `mcp-server/src/compound/trade-tool.ts` | new | zorivest_trade compound tool |
| `mcp-server/src/compound/report-tool.ts` | new | zorivest_report compound tool |
| `mcp-server/src/compound/analytics-tool.ts` | new | zorivest_analytics compound tool |
| `mcp-server/src/tools/trade-tools.ts` | modify | Remove 6 registrations |
| `mcp-server/src/tools/analytics-tools.ts` | modify | Remove 14 registrations |
| `mcp-server/src/tools/calculator-tools.ts` | modify | Remove 1 registration |
| `mcp-server/src/toolsets/seed.ts` | modify | Update trade toolset definition |
| `mcp-server/tests/compound/trade-tool.test.ts` | new | Trade compound tool tests |
| `mcp-server/tests/compound/analytics-tool.test.ts` | new | Analytics compound tool tests |

---

### MC3 — Data Toolset Compound Tools

Consolidate market-data-tools.ts (7), accounts-tools.ts (13), planning-tools.ts (watchlist portion: 5), and tax-tools.ts (4 stubs) into 5 compound tools: `zorivest_market` (7 actions), `zorivest_account` (9 actions), `zorivest_watchlist` (5 actions), `zorivest_import` (7 actions), `zorivest_tax` (4 stub actions).

#### Boundary Inventory

| Surface | Schema Owner | Field Constraints | Extra-Field Policy |
|---------|-------------|-------------------|-------------------|
| MCP `zorivest_account` | `z.object({action: z.enum(9)}).strict()` | `action` includes destructive: `delete`, `archive`, `reassign` | `.strict()` rejects unknowns |
| MCP `zorivest_market` | `z.object({action: z.enum(7)}).strict()` | `action` in market data operations | `.strict()` rejects unknowns |
| MCP `zorivest_watchlist` | `z.object({action: z.enum(5)}).strict()` | `action` in watchlist operations | `.strict()` rejects unknowns |
| MCP `zorivest_import` | `z.object({action: z.enum(7)}).strict()` | `action` includes 3 × 501 stubs: `list_brokers`, `resolve_identifiers`, `list_bank_accounts` | `.strict()` rejects unknowns |
| MCP `zorivest_tax` | `z.object({action: z.enum(4)}).strict()` | All 4 actions return 501 | `.strict()` rejects unknowns |

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-3.1 | `zorivest_account` registered with 9 actions (list, get, create, update, delete, archive, reassign, balance, checklist) | Spec (v3.1 §3) | Unknown action → InvalidParams |
| AC-3.2 | `zorivest_market` registered with 7 actions mapping to market-data-tools.ts | Spec (v3.1 §3) | N/A |
| AC-3.3 | `zorivest_watchlist` registered with 5 actions (create, list, get, add_ticker, remove_ticker) | Spec (v3.1 §3) | N/A |
| AC-3.4 | `zorivest_import` registered with 7 actions (broker_csv, broker_pdf, bank_statement, sync_broker, list_brokers[501], resolve_identifiers[501], list_bank_accounts[501]) | Spec (v3.1 §3) | N/A |
| AC-3.5 | `zorivest_tax` registered with 4 stub actions (estimate, wash_sales, manage_lots, harvest) returning 501 | Spec (v3.1 §2) | N/A |
| AC-3.6 | Destructive account actions (delete, archive, reassign) require `confirmation_token` | Local Canon (M3) | Missing token → confirmation prompt |
| AC-3.7 | 32 old registrations removed | Spec (v3.1 §8, MC3 removes 32) | N/A |
| AC-3.8 | `tools/list` count = 59 − 32 + 5 = **32** | Spec (v3.1 §8) | N/A |
| AC-3.9 | `npm run build` + `npx vitest run` pass | Local Canon (M4) | N/A |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `mcp-server/src/compound/account-tool.ts` | new | zorivest_account compound tool |
| `mcp-server/src/compound/market-tool.ts` | new | zorivest_market compound tool |
| `mcp-server/src/compound/watchlist-tool.ts` | new | zorivest_watchlist compound tool |
| `mcp-server/src/compound/import-tool.ts` | new | zorivest_import compound tool |
| `mcp-server/src/compound/tax-tool.ts` | new | zorivest_tax compound tool |
| `mcp-server/src/tools/market-data-tools.ts` | modify | Remove 7 registrations |
| `mcp-server/src/tools/accounts-tools.ts` | modify | Remove all 13 registrations (9 callable → account, 4 → import) |
| `mcp-server/src/tools/planning-tools.ts` | modify | Remove 5 watchlist registrations |
| `mcp-server/src/tools/tax-tools.ts` | modify | Remove 4 stub registrations |
| `mcp-server/src/toolsets/seed.ts` | modify | Update data toolset definitions |
| `mcp-server/tests/compound/account-tool.test.ts` | new | Account compound tool tests |
| `mcp-server/tests/compound/market-tool.test.ts` | new | Market compound tool tests |

---

### MC4 — Ops Toolset Compound Tools + CI Gate

Consolidate planning-tools.ts (plan portion: 3), scheduling-tools.ts (8), and pipeline-security-tools.ts (12) into 4 compound tools: `zorivest_plan` (3 actions), `zorivest_policy` (9 actions), `zorivest_template` (6 actions), `zorivest_db` (5 actions). Restructure seed.ts from 10→4 toolsets. Add CI assertion `tool_count ≤ 13`.

#### Boundary Inventory

| Surface | Schema Owner | Field Constraints | Extra-Field Policy |
|---------|-------------|-------------------|-------------------|
| MCP `zorivest_policy` | `z.object({action: z.enum(9)}).strict()` | `action` includes destructive: `delete` | `.strict()` rejects unknowns |
| MCP `zorivest_template` | `z.object({action: z.enum(6)}).strict()` | `action` includes destructive: `delete` | `.strict()` rejects unknowns |
| MCP `zorivest_db` | `z.object({action: z.enum(5)}).strict()` | All discovery/validation actions | `.strict()` rejects unknowns |

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-4.1 | `zorivest_plan` registered with 3 actions (create, list, delete) | Spec (v3.1 §3) | Unknown action → InvalidParams |
| AC-4.2 | `zorivest_policy` registered with 9 actions (create, list, run, preview, update_schedule, get_history, delete, update, emulate) | Spec (v3.1 §3) | N/A |
| AC-4.3 | `zorivest_template` registered with 6 actions (create, get, list, update, delete, preview) | Spec (v3.1 §3) | N/A |
| AC-4.4 | `zorivest_db` registered with 5 actions (validate_sql, list_tables, row_samples, step_types, provider_capabilities) | Spec (v3.1 §3) | N/A |
| AC-4.5 | `delete_trade_plan` requires confirmation_token | Local Canon (M3) | Missing token → confirmation prompt |
| AC-4.6 | `delete_policy` requires confirmation_token | Local Canon (M3) | Missing token → confirmation prompt |
| AC-4.7 | `delete_email_template` requires confirmation_token | Local Canon (M3) | Missing token → confirmation prompt |
| AC-4.8 | `zorivest_db(action:"step_types")` returns real data from `/scheduling/step-types` | Spec (v3.1 MC4 AC-2) | N/A |
| AC-4.9 | `zorivest_db(action:"provider_capabilities")` returns real data from `/market-data/providers` | Spec (v3.1 MC4 AC-3) | N/A |
| AC-4.10 | **Empirical**: `tools/list` with defaults → 4 tools (core: zorivest_system; trade: zorivest_trade, zorivest_report, zorivest_analytics) | Spec (v3.1 MC4 AC-4) | N/A |
| AC-4.11 | **Empirical**: `tools/list` with `--toolsets data` → 6 tools (core + zorivest_market, zorivest_account) | Spec (v3.1 MC4 AC-5) | N/A |
| AC-4.12 | **Empirical**: `tools/list` with `--toolsets all` → 13 tools | Spec (v3.1 MC4 AC-6) | N/A |
| AC-4.13 | **Empirical**: `zorivest_system(action:"toolset_enable", toolset:"ops")` → subsequent `tools/list` shows 5 tools (core + ops) | Spec (v3.1 MC4 AC-9) | N/A |
| AC-4.14 | CI gate assertion: fail if `tool_count > 13` | Spec (v3.1 MC4 AC-7) | N/A |
| AC-4.15 | seed.ts restructured from 10→4 toolsets (core, trade, data, ops) | Spec (v3.1 §3) | N/A |
| AC-4.16 | 23 old registrations removed; `tools/list` count = 32 − 23 + 4 = **13** | Spec (v3.1 §8) | N/A |
| AC-4.17 | `npm run build` + `npx vitest run` pass | Local Canon (M4) | N/A |
| AC-4.18 | Startup assertion: verify non-empty Zod shape (via `getObjectShape()`) on all 13 compound tools | Spec (v3.1 §9) | N/A |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `mcp-server/src/compound/plan-tool.ts` | new | zorivest_plan compound tool |
| `mcp-server/src/compound/policy-tool.ts` | new | zorivest_policy compound tool |
| `mcp-server/src/compound/template-tool.ts` | new | zorivest_template compound tool |
| `mcp-server/src/compound/db-tool.ts` | new | zorivest_db compound tool |
| `mcp-server/src/tools/planning-tools.ts` | modify | Remove 3 plan registrations |
| `mcp-server/src/tools/scheduling-tools.ts` | modify | Remove 8 registrations |
| `mcp-server/src/tools/pipeline-security-tools.ts` | modify | Remove 12 registrations |
| `mcp-server/src/toolsets/seed.ts` | modify | Restructure to 4 toolsets |
| `mcp-server/src/toolsets/registration.ts` | modify | Add startup Zod shape assertion |
| `mcp-server/tests/compound/policy-tool.test.ts` | new | Policy compound tool tests |
| `mcp-server/tests/compound/db-tool.test.ts` | new | DB compound tool tests |
| `mcp-server/tests/tool-count-gate.test.ts` | new | CI gate test (tool_count ≤ 13) |

---

### MC5 — Baseline Regen + Audit + Cleanup

Regenerate baseline-snapshot.json (85→13). Run /mcp-audit. Update server instructions. Archive [MCP-TOOLPROLIFERATION].

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-5.1 | `/mcp-audit` passes with 13-tool baseline | Spec (v3.1 MC5 AC-1) | N/A |
| AC-5.2 | `validate_codebase.py --scope meu` passes | Local Canon (AGENTS.md §Execution Contract) | N/A |
| AC-5.3 | [MCP-TOOLPROLIFERATION] archived in known-issues | Spec (v3.1 MC5 AC-3) | N/A |
| AC-5.4 | Server instructions (`serverInstructions` in index.ts) updated to list 13 compound tools with action summaries | Spec (v3.1 exit criteria) + Local Canon (M7) | N/A |
| AC-5.5 | `baseline-snapshot.json` has exactly 13 tool entries | Spec (v3.1 exit criteria) | N/A |
| AC-5.6 | MCP Resources (6 in pipeline-security-tools.ts) remain unchanged | Spec (v3.1 exit criteria) | N/A |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `mcp-server/tests/baseline-snapshot.json` | modify | Regenerate with 13 tools |
| `mcp-server/src/index.ts` | modify | Update serverInstructions |
| `.agent/context/known-issues.md` | modify | Archive [MCP-TOOLPROLIFERATION] |

---

## Out of Scope

- **TD1 (tool description enrichment)** — separate MEU, not part of consolidation
- **New functionality** — no new API endpoints, no new tool capabilities
- **Ghost tools** (`get_analytics_summary`, `get_trade_streaks`) — never registered, not migrated
- **Spec-only tools** (emergency stop, service status, workspace setup) — depend on unbuilt phases
- **Python code changes** — this is TypeScript-only
- **GUI changes** — no Electron code touched

---

## BUILD_PLAN.md Audit

This project **does** modify BUILD_PLAN.md:

1. Add P2.5f section with 6 MEU rows (MC0–MC5)
2. Fix P2.5e status (currently shows "4 | 0" → should be "4 | 4")
3. Update Phase 9 status tracker line
4. Add P2.5f row to MEU Summary table

Validation after MC0:
```powershell
rg "P2.5f" docs/BUILD_PLAN.md *> C:\Temp\zorivest\bp-check.txt; Get-Content C:\Temp\zorivest\bp-check.txt
# Expected: 3+ matches (section header, status tracker, summary row)
```

---

## Verification Plan

### 1. TypeScript Type Check
```powershell
cd mcp-server; npx tsc --noEmit *> C:\Temp\zorivest\tsc.txt; Get-Content C:\Temp\zorivest\tsc.txt | Select-Object -Last 20
```

### 2. Unit Tests
```powershell
cd mcp-server; npx vitest run *> C:\Temp\zorivest\vitest.txt; Get-Content C:\Temp\zorivest\vitest.txt | Select-Object -Last 40
```

### 3. Build
```powershell
cd mcp-server; npm run build *> C:\Temp\zorivest\build.txt; Get-Content C:\Temp\zorivest\build.txt | Select-Object -Last 20
```

### 4. Tool Count Gate (after MC4)
```powershell
# Vitest test that asserts tools/list count ≤ 13
cd mcp-server; npx vitest run tests/tool-count-gate.test.ts *> C:\Temp\zorivest\gate.txt; Get-Content C:\Temp\zorivest\gate.txt | Select-Object -Last 20
```

### 5. Anti-Placeholder Scan
```powershell
rg "TODO|FIXME|NotImplementedError" mcp-server/src/ *> C:\Temp\zorivest\placeholder.txt; Get-Content C:\Temp\zorivest\placeholder.txt
# Expected: 0 matches
```

### 6. MCP Audit (after MC5)
```powershell
# Run /mcp-audit workflow against live server
```

### 7. MEU Quality Gate
```powershell
uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate.txt; Get-Content C:\Temp\zorivest\validate.txt | Select-Object -Last 50
```

---

## Open Questions

> [!WARNING]
> None. The v3.1 proposal has been reviewed through 4 iterations (v1→v2→v3→v3.1) with all architecture decisions resolved. The boundary input contract, schema strategy, inventory, and transition counts are all verified.

---

## Research References

- [MCP Consolidation Proposal v3.1](../../../../.agent/context/MCP/mcp-consolidation-proposal-v3.md)
- [MCP Tool Audit Report](../../../../.agent/context/MCP/mcp-tool-audit-report.md)
- [MCP-ZODSTRIP Analysis](../../../../.agent/context/known-issues.md) — SDK `server.tool()` overload bug; `registerTool()` is safe
- [MCP TS-SDK `mcp.js` source](../../../../mcp-server/node_modules/@modelcontextprotocol/sdk/dist/esm/server/mcp.js) — empirical `registerTool()` code path verification
