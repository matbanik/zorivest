# Session 2: Annotations Sweep

## Goal

Add `#### Annotations` blocks to all 64 tools in `05a`–`05i` (9 files). The format was established in Session 1's `05j-mcp-discovery.md`. Each block appears after the code fence and before the `**Input:**` line.

> [!IMPORTANT]
> **Tracker:** [Session tracker](.agent/context/handoffs/2026-02-26-mcp-integration-session-tracker.md) — this is Session 2 of 6.

---

## Annotation Format

```markdown
#### Annotations

- `readOnlyHint`: true/false
- `destructiveHint`: true/false
- `idempotentHint`: true/false
- `toolset`: <toolset-name>
- `alwaysLoaded`: true/false
```

Inserted between the closing ` ``` ` of the code block and the `**Input:**` line.

---

## Annotation Classification Table

### 05a — `zorivest-settings` (6 tools, toolset: `core`, alwaysLoaded: true)

| Tool | Status | R | D | I | Rationale |
|---|---|---|---|---|---|
| `get_settings` | Specified | ✅ | — | ✅ | Pure read |
| `update_settings` | Specified | — | — | ✅ | Writes settings; not destructive (reversible) |
| `zorivest_emergency_stop` | Specified | — | ✅ | ✅ | Locks all tools — destructive |
| `zorivest_emergency_unlock` | Specified | — | — | ✅ | Unlocks; not destructive (restores access) |
| `get_log_settings` | Future | ✅ | — | ✅ | Pure read (filtered `GET /settings`) |
| `update_log_level` | Future | — | — | ✅ | Writes one setting; reversible |

---

### 05b — `zorivest-diagnostics` (5 tools, toolset: `core`, alwaysLoaded: true)

| Tool | Status | R | D | I | Rationale |
|---|---|---|---|---|---|
| `zorivest_diagnose` | Specified | ✅ | — | ✅ | Read-only health report |
| `zorivest_launch_gui` | Specified | — | — | — | Launches process; not idempotent (each call may launch a new instance) |
| `zorivest_service_status` | Specified | ✅ | — | ✅ | Read-only status check |
| `zorivest_service_restart` | Specified | — | ✅ | ✅ | Restarts backend — destructive |
| `zorivest_service_logs` | Specified | ✅ | — | ✅ | Returns log paths (read-only) |

---

### 05c — `trade-analytics` (19 tools, toolset: `trade-analytics`, alwaysLoaded: false)

| Tool | Status | R | D | I | Rationale |
|---|---|---|---|---|---|
| `create_trade` | Specified | — | — | ✅ | Writes trade; deduplicates by exec_id (idempotent) |
| `list_trades` | Specified | ✅ | — | ✅ | Pure read |
| `attach_screenshot` | Specified | — | — | — | Writes binary; not idempotent (each call adds a new image) |
| `get_trade_screenshots` | Specified | ✅ | — | ✅ | Read-only metadata |
| `get_screenshot` | Specified | ✅ | — | ✅ | Read-only image retrieval |
| `get_round_trips` | Specified | ✅ | — | ✅ | Read-only analytics |
| `enrich_trade_excursion` | Specified | — | — | ✅ | Writes enrichment data; idempotent (overwrites) |
| `get_fee_breakdown` | Specified | ✅ | — | ✅ | Read-only analytics |
| `score_execution_quality` | Specified | ✅ | — | ✅ | Read-only analytics |
| `estimate_pfof_impact` | Specified | ✅ | — | ✅ | Read-only analytics |
| `get_expectancy_metrics` | Specified | ✅ | — | ✅ | Read-only analytics |
| `simulate_drawdown` | Specified | ✅ | — | ✅ | Read-only analytics |
| `get_strategy_breakdown` | Specified | ✅ | — | ✅ | Read-only analytics |
| `get_sqn` | Specified | ✅ | — | ✅ | Read-only analytics |
| `get_cost_of_free` | Specified | ✅ | — | ✅ | Read-only analytics |
| `ai_review_trade` | Specified | ✅ | — | ✅ | Read-only (LLM analysis, no state change) |
| `detect_options_strategy` | Specified | ✅ | — | ✅ | Read-only pattern detection |
| `create_report` | Planned | — | — | — | Writes report; not idempotent (new report each call) |
| `get_report_for_trade` | Planned | ✅ | — | ✅ | Read-only fetch |

---

### 05d — `trade-planning` (2 tools, toolset: `trade-planning`, alwaysLoaded: false)

| Tool | Status | R | D | I | Rationale |
|---|---|---|---|---|---|
| `calculate_position_size` | Specified | ✅ | — | ✅ | Pure calculation, no side effects |
| `create_trade_plan` | Planned | — | — | — | Writes plan; not idempotent |

---

### 05e — `market-data` (7 tools, toolset: `market-data`, alwaysLoaded: false)

| Tool | Status | R | D | I | Rationale |
|---|---|---|---|---|---|
| `get_stock_quote` | Specified | ✅ | — | ✅ | Network read |
| `get_market_news` | Specified | ✅ | — | ✅ | Network read |
| `search_ticker` | Specified | ✅ | — | ✅ | Network read |
| `get_sec_filings` | Specified | ✅ | — | ✅ | Network read |
| `list_market_providers` | Specified | ✅ | — | ✅ | Read-only config |
| `test_market_provider` | Specified | ✅ | — | ✅ | Read-only probe (no state change) |
| `disconnect_market_provider` | Specified | — | ✅ | ✅ | Disconnects provider — destructive |

---

### 05f — `accounts` (8 tools, toolset: `accounts`, alwaysLoaded: false)

| Tool | Status | R | D | I | Rationale |
|---|---|---|---|---|---|
| `sync_broker` | Specified | — | ✅ | — | Syncs external broker; destructive + not idempotent (each sync may create records) |
| `list_brokers` | Specified | ✅ | — | ✅ | Read-only |
| `resolve_identifiers` | Specified | ✅ | — | ✅ | Read-only lookup |
| `import_bank_statement` | Specified | — | — | — | Writes records; not idempotent |
| `import_broker_csv` | Specified | — | — | — | Writes records; not idempotent |
| `import_broker_pdf` | Specified | — | — | — | Writes records; not idempotent |
| `list_bank_accounts` | Specified | ✅ | — | ✅ | Read-only |
| `get_account_review_checklist` | Planned | ✅ | — | ✅ | Read-only |

---

### 05g — `scheduling` (6 tools, toolset: `scheduling`, alwaysLoaded: false)

| Tool | Status | R | D | I | Rationale |
|---|---|---|---|---|---|
| `create_policy` | Specified | — | — | — | Writes policy; not idempotent |
| `list_policies` | Specified | ✅ | — | ✅ | Read-only |
| `run_pipeline` | Specified | — | — | — | Executes pipeline; not idempotent (side effects per run) |
| `preview_report` | Specified | ✅ | — | ✅ | Read-only preview |
| `update_policy_schedule` | Specified | — | — | ✅ | Writes schedule; idempotent (same input → same state) |
| `get_pipeline_history` | Specified | ✅ | — | ✅ | Read-only |

---

### 05h — `tax` (8 tools, toolset: `tax`, alwaysLoaded: false)

| Tool | Status | R | D | I | Rationale |
|---|---|---|---|---|---|
| `simulate_tax_impact` | Planned | ✅ | — | ✅ | Read-only what-if |
| `estimate_tax` | Planned | ✅ | — | ✅ | Read-only computation |
| `find_wash_sales` | Planned | ✅ | — | ✅ | Read-only scan |
| `get_tax_lots` | Planned | ✅ | — | ✅ | Read-only |
| `get_quarterly_estimate` | Planned | ✅ | — | ✅ | Read-only computation |
| `record_quarterly_tax_payment` | Planned | — | — | ✅ | Writes payment; idempotent (same quarter+amount → same record) |
| `harvest_losses` | Planned | ✅ | — | ✅ | Read-only scan |
| `get_ytd_tax_summary` | Planned | ✅ | — | ✅ | Read-only |

---

### 05i — `behavioral` (3 tools, toolset: `behavioral`, alwaysLoaded: false)

| Tool | Status | R | D | I | Rationale |
|---|---|---|---|---|---|
| `track_mistake` | Specified | — | — | — | Writes mistake record; not idempotent |
| `get_mistake_summary` | Specified | ✅ | — | ✅ | Read-only analytics |
| `link_trade_journal` | Specified | — | — | ✅ | Links trade to journal; idempotent (same link = no-op) |

---

## Proposed Changes

### Per-File Editing Strategy

Each file gets the same treatment: for every `### tool_name [Status]` block, insert an `#### Annotations` section after the code fence closing and before `**Input:**`.

#### [MODIFY] [05a-mcp-zorivest-settings.md](docs/build-plan/05a-mcp-zorivest-settings.md) — 6 tools
#### [MODIFY] [05b-mcp-zorivest-diagnostics.md](docs/build-plan/05b-mcp-zorivest-diagnostics.md) — 5 tools
#### [MODIFY] [05c-mcp-trade-analytics.md](docs/build-plan/05c-mcp-trade-analytics.md) — 19 tools
#### [MODIFY] [05d-mcp-trade-planning.md](docs/build-plan/05d-mcp-trade-planning.md) — 2 tools
#### [MODIFY] [05e-mcp-market-data.md](docs/build-plan/05e-mcp-market-data.md) — 7 tools
#### [MODIFY] [05f-mcp-accounts.md](docs/build-plan/05f-mcp-accounts.md) — 8 tools
#### [MODIFY] [05g-mcp-scheduling.md](docs/build-plan/05g-mcp-scheduling.md) — 6 tools
#### [MODIFY] [05h-mcp-tax.md](docs/build-plan/05h-mcp-tax.md) — 8 tools
#### [MODIFY] [05i-mcp-behavioral.md](docs/build-plan/05i-mcp-behavioral.md) — 3 tools

**Total: 64 annotation blocks across 9 files.**

---

## Verification Plan

```powershell
# Count annotation blocks per file (expected: 68 total = 64 new + 4 in 05j)
$files = Get-ChildItem docs\build-plan\05?-mcp-*.md
foreach ($f in $files) { $c = (Select-String '#### Annotations' $f.FullName).Count; Write-Output "$($f.Name): $c" }

# Verify every annotation block has all 5 required fields (deterministic full sweep)
$total = 0; $ok = 0
foreach ($f in $files) {
  $lines = Get-Content $f.FullName
  for ($i=0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match '#### Annotations') {
      $total++
      $block = ($lines[($i+1)..($i+7)] -join "`n")
      $has = @('readOnlyHint','destructiveHint','idempotentHint','toolset','alwaysLoaded') |
        ForEach-Object { $block -match $_ } | Where-Object { $_ -eq $true }
      if ($has.Count -eq 5) { $ok++ }
      else { Write-Output "INCOMPLETE: $($f.Name) line $($i+1)" }
    }
  }
}
Write-Output "Total=$total Complete=$ok"

# Check destructive annotation blocks match Pattern E list from §5.13 (expected: 4)
foreach ($f in $files) { Select-String '^\- `destructiveHint`: true' $f.FullName }
```
