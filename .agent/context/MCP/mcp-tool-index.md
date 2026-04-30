# MCP Tool Index — Compound Architecture (P2.5f)

> **Source**: [mcp-consolidation-proposal-v3.md](mcp-consolidation-proposal-v3.md)
> **Status**: Target architecture — implementation in progress
> **Total**: 13 compound tools, 85 actions (78 callable + 7 stubs)

---

## Toolset Overview

| Toolset | Tools | Load | Default Visible |
|---------|-------|------|-----------------|
| `core` | `zorivest_system` | ✅ Always | 1 |
| `trade` | `zorivest_trade`, `zorivest_report`, `zorivest_analytics` | ✅ Default | 3 |
| `data` | `zorivest_market`, `zorivest_account`, `zorivest_watchlist`, `zorivest_import`, `zorivest_tax` | ⬜ Deferred | 5 |
| `ops` | `zorivest_plan`, `zorivest_policy`, `zorivest_template`, `zorivest_db` | ⬜ Deferred | 4 |

**Default visible**: 4 (core + trade). Deferred: 9 via `zorivest_system(action:"toolset_enable")`.

---

## Action Mapping

### 1. `zorivest_system` — 9 actions (core, always loaded)

| Action | Source Tool | Notes |
|--------|-----------|-------|
| `diagnose` | `zorivest_diagnose` | System diagnostics |
| `settings_get` | `get_settings` | Read app settings |
| `settings_update` | `update_settings` | Write app settings |
| `confirm_token` | `get_confirmation_token` | Destructive-op token |
| `launch_gui` | `zorivest_launch_gui` | Open Electron GUI |
| `email_config` | `get_email_config` | SMTP configuration |
| `toolsets_list` | `list_available_toolsets` | Toolset discovery |
| `toolset_describe` | `describe_toolset` | Toolset detail |
| `toolset_enable` | `enable_toolset` | Dynamic tool loading |

### 2. `zorivest_trade` — 6 actions (trade, default)

| Action | Source Tool | Notes |
|--------|-----------|-------|
| `create` | `create_trade` | **Destructive** — requires confirmation |
| `list` | `list_trades` | |
| `delete` | `delete_trade` | **Destructive** — requires confirmation |
| `screenshot_attach` | `attach_screenshot` | |
| `screenshot_list` | `get_trade_screenshots` | |
| `screenshot_get` | `get_screenshot` | |

### 3. `zorivest_report` — 2 actions (trade, default)

| Action | Source Tool | Notes |
|--------|-----------|-------|
| `create` | `create_report` | |
| `get` | `get_report_for_trade` | |

### 4. `zorivest_analytics` — 13 actions (trade, default)

| Action | Source Tool | Notes |
|--------|-----------|-------|
| `position_size` | `calculate_position_size` | From calculator-tools.ts |
| `round_trips` | `get_round_trips` | |
| `excursion` | `enrich_trade_excursion` | |
| `fee_breakdown` | `get_fee_breakdown` | |
| `execution_quality` | `score_execution_quality` | |
| `pfof_impact` | `estimate_pfof_impact` | |
| `expectancy` | `get_expectancy_metrics` | |
| `drawdown` | `simulate_drawdown` | |
| `strategy_breakdown` | `get_strategy_breakdown` | |
| `sqn` | `get_sqn` | |
| `cost_of_free` | `get_cost_of_free` | |
| `ai_review` | `ai_review_trade` | |
| `options_strategy` | `detect_options_strategy` | |

### 5. `zorivest_market` — 7 actions (data, deferred)

| Action | Source Tool | Notes |
|--------|-----------|-------|
| `quote` | `get_stock_quote` | |
| `news` | `get_market_news` | |
| `search` | `search_ticker` | |
| `filings` | `get_sec_filings` | |
| `providers` | `list_market_providers` | |
| `test_provider` | `test_market_provider` | |
| `disconnect` | `disconnect_market_provider` | |

### 6. `zorivest_account` — 9 actions (data, deferred)

| Action | Source Tool | Notes |
|--------|-----------|-------|
| `list` | `list_accounts` | |
| `get` | `get_account` | |
| `create` | `create_account` | |
| `update` | `update_account` | |
| `delete` | `delete_account` | **Destructive** — requires confirmation |
| `archive` | `archive_account` | |
| `reassign` | `reassign_trades` | |
| `balance` | `record_balance` | |
| `checklist` | `get_account_review_checklist` | |

### 7. `zorivest_watchlist` — 5 actions (data, deferred)

| Action | Source Tool | Notes |
|--------|-----------|-------|
| `list` | `list_watchlists` | |
| `get` | `get_watchlist` | |
| `create` | `create_watchlist` | |
| `add_ticker` | `add_to_watchlist` | |
| `remove_ticker` | `remove_from_watchlist` | |

### 8. `zorivest_import` — 7 actions (data, deferred)

| Action | Source Tool | Notes |
|--------|-----------|-------|
| `broker_csv` | `import_broker_csv` | |
| `broker_pdf` | `import_broker_pdf` | |
| `bank_statement` | `import_bank_statement` | |
| `sync_broker` | `sync_broker` | |
| `list_brokers` | `list_brokers` | **501 stub** |
| `resolve_identifiers` | `resolve_identifiers` | **501 stub** |
| `list_bank_accounts` | `list_bank_accounts` | **501 stub** |

### 9. `zorivest_tax` — 4 actions (data, deferred)

| Action | Source Tool | Notes |
|--------|-----------|-------|
| `estimate` | `estimate_tax` | **501 stub** |
| `wash_sales` | `find_wash_sales` | **501 stub** |
| `manage_lots` | `manage_lots` | **501 stub** |
| `harvest` | `harvest_losses` | **501 stub** |

### 10. `zorivest_plan` — 3 actions (ops, deferred)

| Action | Source Tool | Notes |
|--------|-----------|-------|
| `create` | `create_trade_plan` | |
| `list` | `list_trade_plans` | |
| `delete` | `delete_trade_plan` | **Destructive** — requires confirmation |

### 11. `zorivest_policy` — 9 actions (ops, deferred)

| Action | Source Tool | Notes |
|--------|-----------|-------|
| `list` | `list_policies` | |
| `create` | `create_policy` | |
| `update` | `update_policy` | |
| `delete` | `delete_policy` | **Destructive** — requires confirmation |
| `schedule` | `update_policy_schedule` | |
| `run` | `run_pipeline` | |
| `history` | `get_pipeline_history` | |
| `emulate` | `emulate_policy` | |
| `preview` | `preview_report` | |

### 12. `zorivest_template` — 6 actions (ops, deferred)

| Action | Source Tool | Notes |
|--------|-----------|-------|
| `list` | `list_email_templates` | |
| `get` | `get_email_template` | |
| `create` | `create_email_template` | |
| `update` | `update_email_template` | |
| `delete` | `delete_email_template` | **Destructive** — requires confirmation |
| `preview` | `preview_email_template` | |

### 13. `zorivest_db` — 5 actions (ops, deferred)

| Action | Source Tool | Notes |
|--------|-----------|-------|
| `tables` | `list_db_tables` | |
| `samples` | `get_db_row_samples` | |
| `validate_sql` | `validate_sql` | |
| `step_types` | `list_step_types` | |
| `provider_capabilities` | `list_provider_capabilities` | |

---

## Coverage Verification

| Metric | Value |
|--------|-------|
| Total compound tools | 13 |
| Total actions | 85 (9+6+2+13+7+9+5+7+4+3+9+6+5) |
| Callable actions | 78 |
| 501 stub actions | 7 |
| Dropped actions | 0 |

## MCP Resources (unchanged — not part of consolidation)

6 resources in `pipeline-security-tools.ts` remain unchanged:
- `pipeline://policies/schema`
- `pipeline://step-types`
- `pipeline://templates`
- `pipeline://providers`
- `pipeline://variables`
- `pipeline://emulator/help`
