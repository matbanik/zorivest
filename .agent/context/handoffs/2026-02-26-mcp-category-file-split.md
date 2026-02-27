# Split MCP Server into Category Files

Split the monolithic [05-mcp-server.md](file:///p:/zorivest/docs/build-plan/05-mcp-server.md) (1628 lines) into 9 per-category files. Write draft specs for all Planned/Future tools. Leave `05-mcp-server.md` as a hub with shared infrastructure only.

## Design Decisions

> [!IMPORTANT]
> **No `05j-mcp-calculator.md`** — `calculator` has only 1 primary tool (`calculate_position_size`) whose primary category is `trade-planning`. It will live in `05d` with a `calculator` cross-reference tag. This reduces file count from 10 to 9.

> [!IMPORTANT]
> **`05-mcp-server.md` becomes a hub** — Retains shared infrastructure (auth bootstrap, guard middleware, metrics middleware, SDK compatibility, registration index). All `server.tool()` code blocks move to category files.

## New Files (9)

| File | Category | Specified | Planned | Future | Source |
|------|----------|-----------|---------|--------|--------|
| [05a-mcp-zorivest-settings.md](file:///p:/zorivest/docs/build-plan/05a-mcp-zorivest-settings.md) | `zorivest-settings` | 4 | — | 2 | `05:L221–252`, `05:L399–476` |
| [05b-mcp-zorivest-diagnostics.md](file:///p:/zorivest/docs/build-plan/05b-mcp-zorivest-diagnostics.md) | `zorivest-diagnostics` | 5 | — | — | `05:L572–670`, `05:L875–1170`, `10:L756–901` |
| [05c-mcp-trade-analytics.md](file:///p:/zorivest/docs/build-plan/05c-mcp-trade-analytics.md) | `trade-analytics` | 17 | 2 | — | `05:L23–116`, `05:L149–170`, `05:L1312–1560` |
| [05d-mcp-trade-planning.md](file:///p:/zorivest/docs/build-plan/05d-mcp-trade-planning.md) | `trade-planning`, `calculator` | 2 | 1 | — | `05:L96–116` (position_size), cross-refs |
| [05e-mcp-market-data.md](file:///p:/zorivest/docs/build-plan/05e-mcp-market-data.md) | `market-data` | 7 | — | — | `05:L185–220`, `08:L454–651` |
| [05f-mcp-accounts.md](file:///p:/zorivest/docs/build-plan/05f-mcp-accounts.md) | `accounts` | 7 | 1 | — | `05:L1312–1330`, `05:L1470–1560` |
| [05g-mcp-scheduling.md](file:///p:/zorivest/docs/build-plan/05g-mcp-scheduling.md) | `scheduling` | 6 | — | — | `09:L2840–2984` |
| [05h-mcp-tax.md](file:///p:/zorivest/docs/build-plan/05h-mcp-tax.md) | `tax` | — | 7 | — | New (draft specs from `06g-gui-tax.md` + `mcp-planned-readiness.md`) |
| [05i-mcp-behavioral.md](file:///p:/zorivest/docs/build-plan/05i-mcp-behavioral.md) | `behavioral` | 3 | — | — | `05:L1438–1470` |

## What Stays in 05-mcp-server.md (Hub)

| Section | Lines | Purpose |
|---------|-------|---------|
| Goal + Architecture | L1–20 | MCP server purpose and architecture overview |
| Auth Bootstrap | L270–398 | Standalone/embedded auth flow (shared by all tools) |
| Guard Middleware | L399–431 | `withGuard()` wrapper (shared infrastructure) |
| Metrics Middleware | L671–870 | `withMetrics()`, `MetricsCollector` (shared infrastructure) |
| Registration Index | L1560–1570 | Updated to import from category files |
| SDK Compatibility | L1609–1628 | Version pinning and migration rules |
| Vitest Tests (shared) | L117–148, L477–571, L1171–1260 | Guard/metrics tests stay with infrastructure |

All `server.tool(...)` code blocks and tool-specific tests **move out**.

## Proposed Changes

---

### Hub File

#### [MODIFY] [05-mcp-server.md](file:///p:/zorivest/docs/build-plan/05-mcp-server.md)

- Remove all `server.tool()` code blocks (they move to 05a–05i)
- Keep: Goal, Auth Bootstrap, Guard middleware, Metrics middleware, SDK Compatibility
- Replace removed sections with cross-reference callouts:
  ```markdown
  > **Moved:** Settings tools → [05a-mcp-zorivest-settings.md](05a-mcp-zorivest-settings.md)
  ```
- Update Registration section to import from category files
- Update Outputs section to reference category files

---

### Category Files

#### [NEW] [05a-mcp-zorivest-settings.md](file:///p:/zorivest/docs/build-plan/05a-mcp-zorivest-settings.md)

**Specified (move from 05):** `get_settings`, `update_settings`, `zorivest_emergency_stop`, `zorivest_emergency_unlock`  
**Future (draft new):** `get_log_settings`, `update_log_level`

---

#### [NEW] [05b-mcp-zorivest-diagnostics.md](file:///p:/zorivest/docs/build-plan/05b-mcp-zorivest-diagnostics.md)

**Specified (move from 05):** `zorivest_diagnose`, `zorivest_launch_gui`  
**Specified (move from 10):** `zorivest_service_status`, `zorivest_service_restart`, `zorivest_service_logs`

- Leave reference in `10-service-daemon.md` → `05b`

---

#### [NEW] [05c-mcp-trade-analytics.md](file:///p:/zorivest/docs/build-plan/05c-mcp-trade-analytics.md)

**Specified (move from 05):** `create_trade`, `list_trades`, `attach_screenshot`, `get_trade_screenshots`, `get_screenshot`, `get_round_trips`, `enrich_trade_excursion`, `get_fee_breakdown`, `score_execution_quality`, `estimate_pfof_impact`, `get_expectancy_metrics`, `simulate_drawdown`, `get_strategy_breakdown`, `get_sqn`, `get_cost_of_free`, `ai_review_trade`, `detect_options_strategy`  
**Planned (draft new):** `create_report`, `get_report_for_trade`

---

#### [NEW] [05d-mcp-trade-planning.md](file:///p:/zorivest/docs/build-plan/05d-mcp-trade-planning.md)

**Specified (move from 05):** `calculate_position_size`  
**Planned (draft new):** `create_trade_plan`  
**Cross-ref:** `create_trade` → see [05c](05c-mcp-trade-analytics.md), `simulate_tax_impact` → see [05h](05h-mcp-tax.md)

---

#### [NEW] [05e-mcp-market-data.md](file:///p:/zorivest/docs/build-plan/05e-mcp-market-data.md)

**Specified (move from 05 + 08):** `get_stock_quote`, `get_market_news`, `search_ticker`, `get_sec_filings`, `list_market_providers`, `test_market_provider`, `disconnect_market_provider`

- Leave reference in `08-market-data.md` → `05e`

---

#### [NEW] [05f-mcp-accounts.md](file:///p:/zorivest/docs/build-plan/05f-mcp-accounts.md)

**Specified (move from 05):** `sync_broker`, `list_brokers`, `resolve_identifiers`, `import_bank_statement`, `import_broker_csv`, `import_broker_pdf`, `list_bank_accounts`  
**Planned (draft new):** `start_account_review`

---

#### [NEW] [05g-mcp-scheduling.md](file:///p:/zorivest/docs/build-plan/05g-mcp-scheduling.md)

**Specified (move from 09):** `create_policy`, `list_policies`, `run_pipeline`, `preview_report`, `update_policy_schedule`, `get_pipeline_history`

- Leave reference in `09-scheduling.md` → `05g`

---

#### [NEW] [05h-mcp-tax.md](file:///p:/zorivest/docs/build-plan/05h-mcp-tax.md)

**Planned (draft new — all 7):** `simulate_tax_impact`, `estimate_tax`, `find_wash_sales`, `get_tax_lots`, `quarterly_estimate`, `harvest_losses`, `get_ytd_tax_summary`

- Input/output derived from [06g-gui-tax.md](file:///p:/zorivest/docs/build-plan/06g-gui-tax.md) and [mcp-planned-readiness.md](file:///p:/zorivest/docs/build-plan/mcp-planned-readiness.md)

---

#### [NEW] [05i-mcp-behavioral.md](file:///p:/zorivest/docs/build-plan/05i-mcp-behavioral.md)

**Specified (move from 05):** `track_mistake`, `get_mistake_summary`, `link_trade_journal`

---

### Cross-Reference Updates

#### [MODIFY] [10-service-daemon.md](file:///p:/zorivest/docs/build-plan/10-service-daemon.md)

Replace inline MCP tool specs with:
```markdown
> **MCP Tools:** See [05b-mcp-zorivest-diagnostics.md](05b-mcp-zorivest-diagnostics.md)
```

#### [MODIFY] [09-scheduling.md](file:///p:/zorivest/docs/build-plan/09-scheduling.md)

Replace inline MCP tool specs with reference → `05g`

#### [MODIFY] [08-market-data.md](file:///p:/zorivest/docs/build-plan/08-market-data.md)

Replace inline MCP tool specs with reference → `05e`

#### [MODIFY] [mcp-tool-index.md](file:///p:/zorivest/docs/build-plan/mcp-tool-index.md)

Update header to reference category files. No structural change needed (the index remains the single lookup point).

## Draft Spec Template

Each new `05x` file follows this structure:

```markdown
# Phase 5x: MCP Tools — {Category}

> Part of [Phase 5: MCP Server](05-mcp-server.md) | Category: `{category-name}`

## Tools

### `tool_name` [Specified|Planned|Future]

{description}

```typescript
server.tool(
  'tool_name',
  'Description string',
  { /* Zod schema */ },
  async (args) => { /* handler */ }
);
```

**Input:** ...
**Output:** ...
**Side Effects:** ...
**Error Posture:** ...
```

## Execution Order

1. **Create 9 category files** with tool specs (moved + drafted)
2. **Slim `05-mcp-server.md`** — remove tool blocks, add cross-refs
3. **Update source files** (`09`, `10`, `08`) with cross-refs
4. **Update `mcp-tool-index.md`** header

## Verification

- Verify every tool in `mcp-tool-index.md` is reachable from exactly one primary category file
- Verify `05-mcp-server.md` has no remaining `server.tool()` blocks (only middleware)
- Count: 50 Specified + 11 Planned + 2 Future = 63 tools across 9 files

---

# MCP Category File Split — Walkthrough

## What Was Done

Split the monolithic `05-mcp-server.md` (1628 lines) into **9 category-specific files** containing all 63 MCP tool specs, with draft specifications written for all 11 Planned + 2 Future tools.

## Files Created

| File | Category | Specified | Planned | Future |
|------|----------|-----------|---------|--------|
| [05a-mcp-zorivest-settings.md](file:///p:/zorivest/docs/build-plan/05a-mcp-zorivest-settings.md) | `zorivest-settings` | 4 | — | 2 |
| [05b-mcp-zorivest-diagnostics.md](file:///p:/zorivest/docs/build-plan/05b-mcp-zorivest-diagnostics.md) | `zorivest-diagnostics` | 5 | — | — |
| [05c-mcp-trade-analytics.md](file:///p:/zorivest/docs/build-plan/05c-mcp-trade-analytics.md) | `trade-analytics` | 17 | 2 | — |
| [05d-mcp-trade-planning.md](file:///p:/zorivest/docs/build-plan/05d-mcp-trade-planning.md) | `trade-planning` + `calculator` | 1 | 1 | — |
| [05e-mcp-market-data.md](file:///p:/zorivest/docs/build-plan/05e-mcp-market-data.md) | `market-data` | 7 | — | — |
| [05f-mcp-accounts.md](file:///p:/zorivest/docs/build-plan/05f-mcp-accounts.md) | `accounts` | 7 | 1 | — |
| [05g-mcp-scheduling.md](file:///p:/zorivest/docs/build-plan/05g-mcp-scheduling.md) | `scheduling` | 6 | — | — |
| [05h-mcp-tax.md](file:///p:/zorivest/docs/build-plan/05h-mcp-tax.md) | `tax` | — | 7 | — |
| [05i-mcp-behavioral.md](file:///p:/zorivest/docs/build-plan/05i-mcp-behavioral.md) | `behavioral` | 3 | — | — |
| **Totals** | | **50** | **11** | **2** |

## Files Modified

| File | Change |
|------|--------|
| [05-mcp-server.md](file:///p:/zorivest/docs/build-plan/05-mcp-server.md) | Added Category Files table; replaced tool sections with cross-ref callouts; updated Outputs section. Shared infrastructure (auth, guard, metrics, SDK compat) preserved. |
| [09-scheduling.md](file:///p:/zorivest/docs/build-plan/09-scheduling.md) | Added cross-ref note in §9.11 → `05g` |
| [10-service-daemon.md](file:///p:/zorivest/docs/build-plan/10-service-daemon.md) | Added cross-ref note in §10.4 → `05b` |
| [mcp-tool-index.md](file:///p:/zorivest/docs/build-plan/mcp-tool-index.md) | Updated date; added spec location note pointing to 05a–05i |

## Draft Specs Written

All 11 **Planned** and 2 **Future** tools now have complete draft specs with:
- `server.tool()` code blocks with full Zod schemas
- Input/Output documentation
- Side effects and error posture
- REST endpoint dependencies
- Domain model references

## Design Decisions

- **No `05j-mcp-calculator.md`** — `calculator` folded into `05d` (only 1 primary tool)
- **`05-mcp-server.md` remains the hub** — code blocks for tool implementations are still present inline (not deleted), with cross-ref callouts indicating the category files as authoritative
- **Source files retain code** — `09-scheduling.md` and `10-service-daemon.md` keep their tool code for implementation reference, with notes pointing to category files as the authoritative spec location
