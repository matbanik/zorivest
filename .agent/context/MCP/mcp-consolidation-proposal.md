# MCP Tool Consolidation — MEU Proposal

> **Status**: Proposed for Codex review
> **Date**: 2026-04-29
> **Phase**: P2.5f — MCP Tool Consolidation
> **Prerequisite**: P2.5e ✅ (MCP Tool Remediation complete)
> **Resolves**: [MCP-TOOLPROLIFERATION], partially [MCP-TOOLDISCOVERY], partially [MCP-TOOLCAP]
> **Source**: [mcp-tool-deviation-analysis.md](mcp-tool-deviation-analysis.md) (validated), [mcp-tool-audit-report.md](mcp-tool-audit-report.md)

---

## 1. Deviation Analysis Validation Summary

The [deviation analysis](mcp-tool-deviation-analysis.md) was validated against:
- [05-mcp-server.md §5.11](file:///p:/zorivest/docs/build-plan/05-mcp-server.md) (plan spec)
- [mcp-tool-index.md](file:///p:/zorivest/docs/build-plan/mcp-tool-index.md) (74 unique tools catalog)
- [MCP Tool Audit Report](mcp-tool-audit-report.md) (74→76 actual count)
- [BUILD_PLAN.md](file:///p:/zorivest/docs/BUILD_PLAN.md) (MEU registry)

### Verified Claims

| Claim | Status | Source |
|-------|--------|--------|
| Plan spec: 9 toolsets, ~74 unique tools, 38 default | ✅ Verified | 05-mcp-server.md §5.11 line 736-748 |
| Actual: 10 toolsets, 76 tools | ✅ Verified | Audit report (74) + TA4 (+2) |
| All toolsets load eagerly | ✅ Verified | IDE config doesn't use `--toolsets` |
| `pipeline-security` is entirely new (not in plan) | ✅ Verified | No reference in 05a-05k category files |
| `trade-planning` exploded 3→10 (watchlist misplacement + TA4) | ✅ Verified | Watchlists in 05f, implemented in trade-planning |
| `core` shrunk 12→4 | ✅ Verified | 8 tools depend on unbuilt phases (10, 1A, 5.H) |

### Gaps Found in Deviation Analysis

| # | Gap | Impact | Resolution |
|---|-----|--------|------------|
| G1 | Tax tools not assigned to any compound tool (line 245 says "absorb or dedicated" — vague) | 4 stub tools unplaced | **Decision**: Absorb into `zorivest_analytics` as stub actions. When MEU-149 implements real tax, extract to `zorivest_tax` if warranted. |
| G2 | Behavioral tools (3) missing from target architecture table | 3 stub tools unplaced | **Decision**: `track_mistake`/`link_trade_journal` → `zorivest_trade` (write ops on trade); `get_mistake_summary` → `zorivest_analytics` |
| G3 | `emergency_stop`/`emergency_unlock` not mapped to `zorivest_system` | Unimplemented tools omitted from compound mapping | **Decision**: Add as `zorivest_system` actions (stub until Phase 10 service daemon) |
| G4 | Net Δ arithmetic has cross-tagging double-count errors | Cosmetic — total 76→12 is correct | **Fix**: Recount unique tools per compound, not category-tagged totals |
| G5 | v1 alias mechanism not scoped as deliverable | Migration risk unaddressed | **Fix**: Include in MEU-MC1 as infrastructure deliverable |
| G6 | `seed.ts` toolset restructuring (10→4) not detailed | Implementation gap | **Fix**: Include in MEU-MC4 with deferred loading |

---

## 2. Target Architecture (Validated + Corrected)

### 12 Compound Tools → 4 Toolsets

| Toolset | Compound Tools | Default | Description |
|---------|---------------|---------|-------------|
| `core` | `zorivest_system` | ✅ Always | Settings, diagnostics, GUI, discovery, confirmation tokens |
| `trade` | `zorivest_trade`, `zorivest_report`, `zorivest_plan`, `zorivest_analytics` | ✅ Default | Trade CRUD, reports, plans, all analytics/metrics |
| `data` | `zorivest_market`, `zorivest_account`, `zorivest_watchlist`, `zorivest_import` | ⬜ Deferred | Market data, accounts, watchlists, imports |
| `ops` | `zorivest_policy`, `zorivest_template`, `zorivest_db` | ⬜ Deferred | Scheduling, templates, DB tools |

**Default active: 5 compound tools** (core: 1, trade: 4). Deferred: 7 tools loaded on-demand.

### Corrected Compound Tool Mapping

| # | Compound Tool | Actions | Current Tools Replaced | Notes |
|---|---------------|---------|----------------------|-------|
| 1 | `zorivest_system` | `diagnose`, `settings_get`, `settings_update`, `confirm_token`, `launch_gui`, `email_config`, `toolsets_list`, `toolset_describe`, `toolset_enable`, `emergency_stop`†, `emergency_unlock`† | 8 implemented + 2 stubs | †G3: stub until Phase 10 |
| 2 | `zorivest_trade` | `create`, `list`, `get`, `delete`, `screenshot_attach`, `screenshot_list`, `screenshot_get`, `track_mistake`†, `link_journal`† | 7 implemented + 2 behavioral stubs | †G2: behavioral write ops |
| 3 | `zorivest_report` | `create`, `get` | 2 implemented | |
| 4 | `zorivest_plan` | `create`, `list`, `delete` | 3 implemented | |
| 5 | `zorivest_analytics` | `expectancy`, `sqn`, `drawdown`, `strategy`, `fees`, `pfof`, `cost_of_free`, `round_trips`, `excursion`, `execution_quality`, `options_detect`, `ai_review`, `position_size`, `streaks`, `mistake_summary`†, `estimate_tax`‡, `find_wash_sales`‡, `harvest_losses`‡, `manage_lots`‡ | 14 implemented + 1 behavioral + 4 tax stubs | †G2 ‡G1: stubs |
| 6 | `zorivest_market` | `quote`, `news`, `search`, `filings`, `providers`, `test_provider`, `disconnect` | 7 implemented | |
| 7 | `zorivest_account` | `list`, `get`, `create`, `update`, `delete`, `archive`, `reassign`, `balance`, `checklist` | 9 implemented | Destructive: delete, reassign |
| 8 | `zorivest_watchlist` | `list`, `get`, `create`, `add_ticker`, `remove_ticker` | 5 implemented | Relocate from trade-planning |
| 9 | `zorivest_import` | `broker_csv`, `broker_pdf`, `bank_statement`, `sync_broker` | 3 stubs (501) + 1 implemented | |
| 10 | `zorivest_policy` | `list`, `create`, `update`, `delete`, `schedule`, `run`, `history`, `emulate`, `preview` | 9 implemented | Destructive: delete, run |
| 11 | `zorivest_template` | `list`, `get`, `create`, `update`, `delete`, `preview` | 6 implemented | |
| 12 | `zorivest_db` | `tables`, `samples`, `validate_sql`, `step_types`, `provider_capabilities` | 5 implemented | |

**Totals**: 76 individual tools → 12 compound tools. 5 default-loaded (core+trade toolsets).

---

## 3. MEU Sequence

### Dependency Graph

```
MEU-MC1 (infrastructure + zorivest_system)
    ↓
MEU-MC2 (template + watchlist + account + import)
    ↓
MEU-MC3 (trade + report + plan + analytics)
    ↓
MEU-MC4 (market + policy + db + deferred loading + CI gate)
    ↓
MEU-MC5 (build plan sync + baseline + documentation)
```

All MEUs are sequential — each depends on the previous. No parallelism.

---

### MEU-MC1: Compound Tool Infrastructure + `zorivest_system`

| Field | Value |
|-------|-------|
| **Slug** | `mcp-compound-infra` |
| **Matrix Item** | 5.N |
| **Build Plan Ref** | [05-mcp-server.md §5.11](file:///p:/zorivest/docs/build-plan/05-mcp-server.md), [05a](file:///p:/zorivest/docs/build-plan/05a-mcp-zorivest-settings.md), [05b](file:///p:/zorivest/docs/build-plan/05b-mcp-zorivest-diagnostics.md), [05j](file:///p:/zorivest/docs/build-plan/05j-mcp-discovery.md) |
| **Effort** | ~4h |
| **Risk** | Low |

**Scope:**
1. Create `CompoundToolRouter` base class in `mcp-server/src/lib/compound-router.ts`:
   - Zod discriminated union action dispatch
   - Per-action handler isolation
   - Error normalization (action not found → MCP error)
   - v1 alias registry: maps old tool names → compound(action) calls
2. Consolidate `core` (4 tools) + `discovery` (4 tools) → `zorivest_system` (10 actions)
3. Register v1 aliases for all 8 replaced tools
4. Add `emergency_stop`/`emergency_unlock` as stub actions (501 until Phase 10)

**Acceptance Criteria:**
- AC-1: `zorivest_system(action: "diagnose")` returns same output as `zorivest_diagnose`
- AC-2: `zorivest_system(action: "settings_get")` returns same output as `get_settings`
- AC-3: v1 alias `get_settings` forwards to `zorivest_system(action: "settings_get")` transparently
- AC-4: All existing core+discovery Vitest tests pass with compound tool names
- AC-5: `zorivest_system(action: "emergency_stop")` returns 501 Not Implemented
- AC-6: CompoundToolRouter validates action parameter and rejects unknown actions with MCP error

**Validation:** `npx vitest run` (all existing tests pass + new compound tests)

---

### MEU-MC2: CRUD Compound Tools — Template + Watchlist + Account + Import

| Field | Value |
|-------|-------|
| **Slug** | `mcp-crud-compounds` |
| **Matrix Item** | 5.O |
| **Build Plan Ref** | [05f](file:///p:/zorivest/docs/build-plan/05f-mcp-accounts.md) |
| **Effort** | ~4h |
| **Risk** | Low–Medium |

**Scope:**
1. `zorivest_template` — 6 actions (from pipeline-security toolset)
2. `zorivest_watchlist` — 5 actions (relocate from trade-planning toolset)
3. `zorivest_account` — 9 actions (largest CRUD family; migrate confirmation gates for delete/reassign)
4. `zorivest_import` — 4 actions (3 × 501 stubs + sync_broker)
5. Register v1 aliases for all ~26 replaced tools
6. Remove individual tool registrations for migrated tools

**Acceptance Criteria:**
- AC-1: All 6 template CRUD operations work via `zorivest_template(action: ...)`
- AC-2: All 5 watchlist operations work via `zorivest_watchlist(action: ...)`
- AC-3: `zorivest_account(action: "delete", ...)` still requires confirmation_token
- AC-4: `zorivest_import(action: "broker_csv")` returns 501 Not Implemented
- AC-5: v1 aliases for all 26 replaced tools forward correctly
- AC-6: All existing CRUD Vitest tests pass with compound tool names

**Validation:** `npx vitest run`

---

### MEU-MC3: Trade Compound Tools — Trade + Report + Plan + Analytics

| Field | Value |
|-------|-------|
| **Slug** | `mcp-trade-compounds` |
| **Matrix Item** | 5.P |
| **Build Plan Ref** | [05c](file:///p:/zorivest/docs/build-plan/05c-mcp-trade-analytics.md), [05d](file:///p:/zorivest/docs/build-plan/05d-mcp-trade-planning.md) |
| **Effort** | ~4h |
| **Risk** | Medium |

**Scope:**
1. `zorivest_trade` — 7 core actions + 2 behavioral stub actions (track_mistake, link_journal)
2. `zorivest_report` — 2 actions (create, get)
3. `zorivest_plan` — 3 actions (create, list, delete)
4. `zorivest_analytics` — 19 actions (13 implemented + 1 behavioral stub + 4 tax stubs + streaks)
5. Register v1 aliases for all ~28 replaced tools
6. Remove individual tool registrations

**Acceptance Criteria:**
- AC-1: `zorivest_trade(action: "create", ...)` still requires confirmation_token
- AC-2: `zorivest_analytics(action: "position_size", ...)` returns same output as `calculate_position_size`
- AC-3: `zorivest_analytics(action: "estimate_tax")` returns 501 Not Implemented
- AC-4: `zorivest_trade(action: "track_mistake")` returns 501 Not Implemented
- AC-5: v1 aliases for all replaced tools forward correctly
- AC-6: All existing trade/analytics Vitest tests pass

**Validation:** `npx vitest run`

---

### MEU-MC4: Data + Ops Compounds + Deferred Loading + CI Gate

| Field | Value |
|-------|-------|
| **Slug** | `mcp-deferred-loading` |
| **Matrix Item** | 5.Q |
| **Build Plan Ref** | [05e](file:///p:/zorivest/docs/build-plan/05e-mcp-market-data.md), [05g](file:///p:/zorivest/docs/build-plan/05g-mcp-scheduling.md) |
| **Effort** | ~4h |
| **Risk** | Medium–High |

**Scope:**
1. `zorivest_market` — 7 actions
2. `zorivest_policy` — 9 actions (migrate confirmation gates for delete/run)
3. `zorivest_db` — 5 actions
4. Register v1 aliases for all ~21 replaced tools
5. Restructure `seed.ts`: 10 toolsets → 4 (core, trade, data, ops)
6. Re-enable deferred loading: `data` + `ops` toolsets load only on `zorivest_system(action: "toolset_enable")`
7. Verify `--toolsets` CLI flag works with 4-toolset structure
8. Add CI gate: fail if `tool_count > 12` in baseline-snapshot.json validation

**Acceptance Criteria:**
- AC-1: `zorivest_policy(action: "delete", ...)` still requires confirmation_token
- AC-2: MCP server starts with only 5 tools visible (core: 1, trade: 4)
- AC-3: `zorivest_system(action: "toolset_enable", toolset: "data")` loads 4 additional tools
- AC-4: `--toolsets trade,data` CLI flag loads 9 tools (core always + trade + data)
- AC-5: `--toolsets all` loads all 12 tools
- AC-6: CI gate rejects tool_count > 12
- AC-7: v1 aliases for all replaced tools forward correctly
- AC-8: All existing scheduling/market Vitest tests pass

**Validation:** `npx vitest run` + manual `--toolsets` flag verification

---

### MEU-MC5: Build Plan Sync + Baseline + Documentation

| Field | Value |
|-------|-------|
| **Slug** | `mcp-buildplan-sync` |
| **Matrix Item** | 5.R |
| **Build Plan Ref** | All 05x files, mcp-tool-index.md, BUILD_PLAN.md |
| **Effort** | ~3h |
| **Risk** | Low (documentation only) |

**Scope:**
1. Rewrite `mcp-tool-index.md` — 74-row flat catalog → 12-row compound catalog with action sub-tables
2. Update `05-mcp-server.md` §5.11 — toolset definitions (9→4), registration index, metrics middleware tool names
3. Update category files (05a–05k) — tool name references to compound equivalents
4. Update index files: `input-index.md`, `output-index.md`, `gui-actions-index.md`
5. Update `build-priority-matrix.md` — add P2.5f MCP Consolidation section
6. Update `BUILD_PLAN.md` — add MEU-MC1 through MEU-MC5 to Phase 5 MCP section
7. Update `meu-registry.md` — add P2.5f section
8. Regenerate `baseline-snapshot.json` (76→12)
9. Run `/mcp-audit` and verify 12-tool baseline passes
10. Run full `validate_codebase.py`
11. Update `known-issues.md` — archive [MCP-TOOLPROLIFERATION]

**Acceptance Criteria:**
- AC-1: `mcp-tool-index.md` contains exactly 12 tool entries with action sub-tables
- AC-2: `baseline-snapshot.json` has exactly 12 tools
- AC-3: `/mcp-audit` passes with 12-tool baseline
- AC-4: `validate_codebase.py` passes
- AC-5: All 05x category files reference compound tool names
- AC-6: BUILD_PLAN.md and meu-registry.md contain MC1–MC5 entries

**Validation:** `/mcp-audit` + `validate_codebase.py`

---

## 4. Exit Criteria (Full Project)

- [ ] Total MCP tools registered: **≤ 12**
- [ ] Default-loaded tools: **≤ 5** (core + trade toolsets)
- [ ] All existing `/mcp-audit` CRUD tests pass with compound tool names
- [ ] v1 aliases registered for all 76 replaced tool names
- [ ] `--toolsets` CLI flag works with 4-toolset structure
- [ ] Deferred loading verified (data + ops load on `toolset_enable`)
- [ ] CI gate: fail if `tool_count > 12`
- [ ] Build plan files updated (all files from deviation analysis §Build Plan Files)
- [ ] `mcp-tool-index.md` reflects compound-tool catalog
- [ ] `baseline-snapshot.json` updated to 12-tool baseline
- [ ] [MCP-TOOLPROLIFERATION] archived in known-issues.md

---

## 5. Risk Mitigation

| Risk | Mitigation | MEU |
|------|------------|-----|
| Breaking existing agent workflows | v1 alias registry forwards old tool names → compound(action) | MC1 |
| Complex Zod discriminated union validation | CompoundToolRouter base class validates once; per-action schemas are isolated | MC1 |
| Confirmation gate regression | Each destructive action migrates its gate explicitly; test coverage per AC | MC2–MC4 |
| Deferred loading regression | Test with `--toolsets` flag before enabling; fallback to `--toolsets all` | MC4 |
| Build plan drift during consolidation | MC5 is documentation-only and runs last | MC5 |

---

## 6. Effort Summary

| MEU | Slug | Effort | Risk | Net Tool Δ |
|-----|------|--------|------|-----------|
| MC1 | `mcp-compound-infra` | ~4h | Low | 8 → 1 (−7) |
| MC2 | `mcp-crud-compounds` | ~4h | Low–Med | 26 → 4 (−22) |
| MC3 | `mcp-trade-compounds` | ~4h | Medium | 28 → 4 (−24) |
| MC4 | `mcp-deferred-loading` | ~4h | Med–High | 21 → 3 (−18) + deferred loading |
| MC5 | `mcp-buildplan-sync` | ~3h | Low | Documentation only |
| **Total** | | **~19h** | | **76 → 12** |
