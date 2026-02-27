# MCP Tool Index

Generated from docs/build-plan/ on 2026-02-26. This index is agent-facing and optimized for reliable tool selection and invocation.

> **Tool spec locations:** Full MCP tool contracts (Zod schemas, handlers, side effects, error posture) live in category files [05a](05a-mcp-zorivest-settings.md)–[05j](05j-mcp-discovery.md). Shared infrastructure (auth, guard, metrics, toolsets, client detection) remains in [05-mcp-server.md](05-mcp-server.md).

## Description Style Used

- Give each tool a clear action intent (use_when) so the agent can decide when to call it.
- Keep input contracts explicit and schema-first; avoid ambiguous free-form args.
- State expected output shape and error posture up front so downstream planning is deterministic.
- Mark side effects and safety constraints (locks, restarts, writes, external spend) in notes.
- Keep non-canonical aliases/deprecated names visible to prevent drift during implementation.

## Tool Catalog

| Tool | Status | Categories | Use When | Input | Expected Output | Notes |
|---|---|---|---|---|---|---|
| calculate_position_size | Specified | `trade-planning`, `calculator` | Calculate risk-based position sizing for a candidate trade. | balance; risk_pct (default 1.0); entry; stop; target. | JSON text with risk_per_share; account_risk_1r; share_size; position_size; reward_risk_ratio; potential_profit. | Pure calculation; no side effects. |
| create_trade | Specified | `trade-analytics`, `trade-planning` | Record a new execution. | exec_id; instrument; action (BOT/SLD); quantity; price; account_id. | JSON text for created trade or dedup conflict details. | Writes trade; deduplicates by exec_id. |
| list_trades | Specified | `trade-analytics` | Read trades for review/export. | limit (default 50); offset (default 0). | JSON text list/page of trades. | Read-only. |
| attach_screenshot | Specified | `trade-analytics` | Attach image evidence to a trade from MCP context. | trade_id; image_base64; mime_type (advisory); caption. | JSON text for stored image metadata/IDs. | MCP decodes base64 and uploads multipart file. |
| get_trade_screenshots | Specified | `trade-analytics` | List screenshot metadata for a trade. | trade_id. | JSON text array of image metadata. | Read-only metadata. |
| get_screenshot | Specified | `trade-analytics` | Retrieve a screenshot with display-ready content. | image_id. | Mixed MCP content: text metadata plus image(base64). | Returns image payload, not just JSON text. |
| get_settings | Specified | `zorivest-settings` | Read app settings for UI/agent behavior. | optional key (string). | JSON text key-value payload (string-valued settings boundary). | Use for logging/ui/display toggles. |
| update_settings | Specified | `zorivest-settings` | Update one or more settings keys. | settings map string->string. | JSON text update result. | Writes settings; values are strings at MCP boundary. |
| zorivest_emergency_stop | Specified | `zorivest-settings` | Immediately lock all guarded MCP tool access. | reason (default agent_self_lock). | Text confirmation that tools are locked. | Always callable; not guard-blocked. |
| zorivest_emergency_unlock | Specified | `zorivest-settings` | Re-enable MCP tools after emergency lock. | confirm literal UNLOCK. | Text confirmation of unlocked/failed state. | Always callable; requires explicit token. |
| zorivest_diagnose | Specified | `zorivest-diagnostics` | Inspect backend reachability, guard state, providers, and MCP runtime health. | verbose bool (default false). | Structured JSON text report: backend; version; database; guard; providers; mcp_server; metrics. | Must never leak API keys. |
| zorivest_launch_gui | Specified | `zorivest-diagnostics` | Launch GUI from agent session, or guide installation if missing. | wait_for_close bool (default false). | JSON text with gui_found; method; message; optional setup_instructions. | Side effect: may launch app or open releases page. |
| get_stock_quote | Specified | `market-data` | Fetch latest quote for a ticker. | ticker. | JSON text quote object. | Network-bound; expected variable latency. |
| get_market_news | Specified | `market-data` | Fetch recent market news globally or by ticker. | optional ticker; count (default 5). | JSON text array/list of articles. | Network-bound. |
| search_ticker | Specified | `market-data` | Resolve partial symbol/company name to candidates. | query. | JSON text list of ticker matches. | Network-bound. |
| get_sec_filings | Specified | `market-data` | Retrieve SEC filings for ticker. | ticker. | JSON text filings list. | Network-bound. |
| list_market_providers | Specified | `market-data`, `zorivest-settings` | Inspect configured market-data provider status. | none. | JSON text list with enabled/key/test status. | Read-only provider status. |
| test_market_provider | Specified | `market-data`, `zorivest-diagnostics` | Validate a provider API key/connection. | provider_name. | JSON text success/failure message/details. | No persistent data write. |
| disconnect_market_provider | Specified | `market-data`, `zorivest-settings` | Remove provider key and disable provider. | provider_name; confirm_destructive (must be true). | JSON text removal status. | Destructive; requires explicit confirmation. |
| create_policy | Specified | `scheduling` | Create a scheduling policy document with validation. | policy_json (full policy document). | Text payload with created policy or validation errors. | Writes scheduling policy. |
| list_policies | Specified | `scheduling` | List policies and schedule/approval state. | enabled_only bool (default false). | JSON text list of policies. | Read-only. |
| run_pipeline | Specified | `scheduling` | Trigger a manual policy run. | policy_id; dry_run (default false). | Text payload with run_id/initial status or failure detail. | Executes pipeline side effects unless dry_run. |
| preview_report | Specified | `scheduling` | Dry-run a pipeline and inspect rendered preview. | policy_id. | Text payload with preview result from dry-run run endpoint. | No email/file side effects expected. |
| update_policy_schedule | Specified | `scheduling` | Change cron/timezone/enabled state for policy. | policy_id; optional cron_expression; enabled; timezone. | Text payload with updated policy info. | Writes policy schedule config. |
| get_pipeline_history | Specified | `scheduling` | Inspect recent policy execution history. | optional policy_id; limit (default 10). | JSON text run history (including step-level metadata route targets). | Read-only. |
| zorivest_service_status | Specified | `zorivest-diagnostics` | Check backend service process-level runtime health. | none. | JSON text with backend state; pid; uptime; cpu/memory; scheduler/db hints, or unreachable error. | Read-only; combines /health + /service/status. |
| zorivest_service_restart | Specified | `zorivest-diagnostics` | Request graceful backend restart via service wrapper. | confirm literal RESTART. | JSON text restarted status when healthy again, or timeout/failure error. | Operational side effect: service restart; requires confirmation. |
| zorivest_service_logs | Specified | `zorivest-diagnostics` | Locate service log directory/files for troubleshooting. | none. | JSON text with log_directory; log_files; hint. | Reads filesystem metadata only. |
| sync_broker | Specified | `accounts` | Trigger broker sync/import workflow. | broker_id (e.g., ibkr_pro/alpaca_paper). | JSON text sync summary/status. | Writes imported data. |
| list_brokers | Specified | `accounts` | List configured broker adapters. | none. | JSON text list of broker configs/status. | Read-only. |
| get_round_trips | Specified | `trade-analytics` | Analyze closed/open execution pairs. | optional account_id; status (open/closed/all, default all). | JSON text round-trip list. | Read-only analytics query. |
| enrich_trade_excursion | Specified | `trade-analytics` | Compute MFE/MAE/BSO metrics for a trade. | trade_exec_id. | JSON text excursion metric payload. | Analytics compute side effect only. |
| get_fee_breakdown | Specified | `trade-analytics` | Summarize fee attribution. | optional account_id; period (default ytd). | JSON text fee decomposition by type. | Read-only analytics query. |
| score_execution_quality | Specified | `trade-analytics` | Grade fill quality vs market benchmarks. | trade_exec_id. | JSON text quality score/grade details. | Depends on benchmark data availability. |
| estimate_pfof_impact | Specified | `trade-analytics` | Estimate routing cost impact from PFOF behavior. | account_id; period (default ytd). | JSON text estimate report. | Explicitly probabilistic estimate. |
| get_expectancy_metrics | Specified | `trade-analytics` | Compute expectancy/edge/Kelly metrics. | optional account_id; period (default all). | JSON text expectancy metrics. | Read-only analytics query. |
| simulate_drawdown | Specified | `trade-analytics`, `calculator` | Run Monte Carlo drawdown simulations. | optional account_id; simulations (100-100000, default 10000). | JSON text probability table/recommended risk outputs. | Compute-heavy analytical call. |
| get_strategy_breakdown | Specified | `trade-analytics` | Break P&L down by strategy tags. | optional account_id. | JSON text strategy-level breakdown. | Read-only analytics query. |
| get_sqn | Specified | `trade-analytics` | Compute System Quality Number metrics. | optional account_id; period (default all). | JSON text SQN value + grade/classification. | Read-only analytics query. |
| get_cost_of_free | Specified | `trade-analytics` | Compute hidden costs from free-routing model. | optional account_id; period (default ytd). | JSON text cost-of-free report. | Read-only analytics query. |
| ai_review_trade | Specified | `trade-analytics`, `behavioral` | Run multi-persona AI review on a trade. | trade_exec_id; review_type (single/weekly); optional budget_cap cents. | JSON text structured review output. | Potentially external-AI spend; budget-cap aware. |
| track_mistake | Specified | `behavioral` | Tag a trade with mistake category/cost for behavior analytics. | trade_exec_id; category; optional estimated_cost; notes. | JSON text created/updated mistake entry. | Writes behavioral data. |
| get_mistake_summary | Specified | `behavioral` | Aggregate mistake patterns over period. | optional account_id; period (default ytd). | JSON text category totals/trend summary. | Read-only analytics query. |
| link_trade_journal | Specified | `behavioral`, `trade-analytics` | Create bidirectional link between trade and journal entry. | trade_exec_id; journal_entry_id. | JSON text link confirmation. | Writes link relation. |
| resolve_identifiers | Specified | `accounts` | Resolve CUSIP/ISIN/SEDOL/FIGI to tradable identifiers. | identifiers array of {id_type,id_value}. | JSON text resolution list (batch). | Read-only/lookup service. |
| import_bank_statement | Specified | `accounts` | Import banking statement files into account ledger. | file_path; account_id; format_hint (auto/csv/ofx/qif). | JSON text import summary (rows/duplicates/errors style payload). | Multipart upload from local file path. |
| import_broker_csv | Specified | `accounts` | Import broker CSV with format detection. | file_path; account_id; broker_hint (default auto). | JSON text import summary. | Multipart upload from local file path. |
| import_broker_pdf | Specified | `accounts` | Import broker PDF statement. | file_path; account_id. | JSON text extraction/import summary. | Multipart upload from local file path. |
| list_bank_accounts | Specified | `accounts` | List linked bank accounts and balances. | none. | JSON text account list with balance/updated fields. | Read-only. |
| detect_options_strategy | Specified | `trade-analytics` | Classify multi-leg options structure from executions. | leg_exec_ids array (min 2). | JSON text detected strategy classification. | Read-only analytics classification. |
| create_report | Specified | `trade-analytics` | Create post-trade TradeReport via MCP. | trade_id; setup_quality (A-F); execution_quality (A-F); followed_plan; emotional_state; optional lessons_learned; tags[]. | JSON with created report ID + echoed fields. | REST: `POST /api/v1/trades/{id}/report`. Needs `isError` on failure. |
| get_report_for_trade | Specified | `trade-analytics` | Fetch report linked to a specific trade. | trade_id. | JSON TradeReport payload or isError not-found. | REST: `GET /api/v1/trades/{id}/report`. Read-only. |
| create_trade_plan | Specified | `trade-planning` | Create forward-looking TradePlan from agent research. | ticker; direction; conviction; strategy_name; entry; stop; target; conditions; timeframe; optional account_id. | JSON with created plan ID + computed risk_reward_ratio + status. | REST: `POST /api/v1/trade-plans`. |
| get_account_review_checklist | Specified | `accounts` | Generate read-only account staleness checklist. | scope (all/stale_only/broker_only/bank_only); stale_threshold_days (default 7). | JSON with account review checklist and suggested actions. | Read-only; uses existing endpoints. |
| estimate_tax | Specified | `tax`, `calculator` | Compute overall tax estimate from profile + trading data. | tax_year; account_id (opt); filing_status; include_unrealized. | Federal + state tax estimate with bracket breakdown. | REST: `POST /api/v1/tax/estimate`. |
| find_wash_sales | Specified | `tax`, `trade-analytics` | Detect wash sale chains/conflicts. | account_id; ticker (opt); date_range_start (opt); date_range_end (opt). | Wash sale chains with disallowed amounts, affected tickers. | REST: `POST /api/v1/tax/wash-sales`. |
| simulate_tax_impact | Specified | `tax`, `calculator`, `trade-planning` | Pre-trade what-if tax simulation for proposed sale. | ticker; action; quantity; price; account_id; cost_basis_method. | Lot-level close preview; ST/LT split; estimated tax; wash risk; hold-savings. | REST: `POST /api/v1/tax/simulate`. |
| get_tax_lots | Specified | `tax` | List/inspect lots for tax-aware lot selection. | account_id; ticker (opt); status (open/closed/all); sort_by. | Tax lot list with basis/holding period/gain-loss fields + summary. | REST: `GET /api/v1/tax/lots`. |
| get_quarterly_estimate | Specified | `tax` | Compute quarterly estimated tax payment obligations (read-only). | quarter (Q1-Q4); tax_year; estimation_method. | Quarterly required/paid/due/penalty/due_date. | REST: `GET /api/v1/tax/quarterly`. |
| record_quarterly_tax_payment | Specified | `tax` | Record an actual quarterly tax payment. | quarter; tax_year; payment_amount; confirm (must be true). | Recorded payment confirmation with updated totals. | REST: `POST /api/v1/tax/quarterly/payment`. Writes; requires confirm. |
| harvest_losses | Specified | `tax`, `trade-analytics` | Scan portfolio for harvestable losses. | optional account_id; min_loss_threshold; exclude_wash_risk. | Ranked loss opportunities + wash-risk annotations + totals. | REST: `GET /api/v1/tax/harvest`. Read-only scan. |
| get_ytd_tax_summary | Specified | `tax` | Return year-to-date tax summary dashboard data. | tax_year; account_id (opt). | Aggregated YTD summary (ST/LT; wash adjustments; estimated tax). | REST: `GET /api/v1/tax/ytd-summary`. |
| get_log_settings | Specified | `zorivest-settings` | Read logging.* settings for runtime log controls. | optional logging key/prefix filter. | Key-value logging settings payload. | Depends on Phase 1A logging. Uses existing settings endpoints. |
| update_log_level | Specified | `zorivest-settings` | Update per-feature runtime log levels. | logging.<feature>.level keys and values. | Update acknowledgement/status. | Depends on Phase 1A logging. Uses existing settings endpoints. |
| list_available_toolsets | Specified | `discovery` | Discover available toolset groups before enabling them. | (none). | JSON: `{ toolsets: [{ name, description, tool_count, loaded, always_loaded }], total_tools }`. | Always loaded. Read-only. |
| describe_toolset | Specified | `discovery` | Inspect tools in a specific toolset before deciding to enable it. | toolset_name. | JSON: `{ name, description, loaded, tools: [{ name, description, annotations }] }`. | Always loaded. Read-only. |
| enable_toolset | Specified | `discovery` | Dynamically activate a deferred toolset for the current session. | toolset_name. | Text confirmation or guidance for static clients. | Sends `notifications/tools/list_changed`. Dynamic clients only. |
| get_confirmation_token | Specified | `discovery` | Obtain a time-limited token before executing a destructive operation. | action (tool name); params_summary. | JSON: `{ token, action, params_summary, expires_in_seconds }`. | Always loaded. 60s TTL. Required on annotation-unaware clients. |


---

## Category Summary

| Category | Specified | Planned | Future | Total |
|----------|-----------|---------|--------|-------|
| `trade-analytics` | 19 | — | — | 19 |
| `accounts` | 8 | — | — | 8 |
| `market-data` | 7 | — | — | 7 |
| `tax` | 8 | — | — | 8 |
| `scheduling` | 6 | — | — | 6 |
| `zorivest-settings` | 6 | — | — | 6 |
| `zorivest-diagnostics` | 5 | — | — | 5 |
| `trade-planning` | 3 | — | — | 3 |
| `behavioral` | 3 | — | — | 3 |
| `calculator` | 1 | — | — | 1 |
| `discovery` | 4 | — | — | 4 |

> **Note:** Tools with multiple categories are counted in each. Primary category listed first in the Categories column. Unique tool count: 68 (all Specified).

---

## Toolset Definitions

> Authoritative source: [05-mcp-server.md §5.11](05-mcp-server.md#step-511-toolset-configuration)

| Toolset | Category File(s) | Tools | Default Loaded | Description |
|---------|-----------------|-------|---------------|-------------|
| `core` | 05a, 05b | 11 | ✅ Always | Settings, emergency stop/unlock, diagnostics, GUI launch, service tools |
| `discovery` | 05j | 4 | ✅ Always | Meta-tools for toolset browsing, enabling, and confirmation tokens |
| `trade-analytics` | 05c | 19 | ✅ Default | Trade CRUD, screenshots, analytics, reports |
| `trade-planning` | 05c, 05d | 3 | ✅ Default | Position calculator, trade plans (includes `create_trade` cross-tagged from 05c) |
| `market-data` | 05e | 7 | ⬜ Deferred | Stock quotes, news, SEC filings, ticker search |
| `accounts` | 05f | 8 | ⬜ Deferred | Account management, broker sync, CSV import |
| `scheduling` | 05g | 6 | ⬜ Deferred | Policy CRUD, pipeline execution, scheduler status |
| `tax` | 05h | 8 | ⬜ Deferred | Tax estimation, wash sales, lot management, harvesting |
| `behavioral` | 05i | 3 | ⬜ Deferred | Mistake tracking, expectancy, Monte Carlo |

**Default active:** `core` + `discovery` + `trade-analytics` + `trade-planning` = **37 tools** (fits under Cursor’s 40-tool limit).


## Reference Map (All Mentions in docs/build-plan/)



> **Primary spec locations:** Each tool's authoritative contract is in its category file (`05a`–`05j`). References below list all mentions across build-plan docs (deduplicated per file).



### calculate_position_size

- **05d-mcp-*.md** ← primary spec

- docs/build-plan/gui-actions-index.md

- docs/build-plan/01-domain-layer.md



### create_trade

- **05c-mcp-*.md** ← primary spec

- docs/build-plan/testing-strategy.md

- docs/build-plan/input-index.md

- docs/build-plan/gui-actions-index.md

- docs/build-plan/05-mcp-server.md

- docs/build-plan/01a-logging.md

- docs/build-plan/04-rest-api.md

- docs/build-plan/03-service-layer.md

- docs/build-plan/05d-mcp-trade-planning.md



### list_trades

- **05c-mcp-*.md** ← primary spec

- docs/build-plan/04-rest-api.md



### attach_screenshot

- **05c-mcp-*.md** ← primary spec

- docs/build-plan/gui-actions-index.md

- docs/build-plan/05-mcp-server.md



### get_trade_screenshots

- **05c-mcp-*.md** ← primary spec

- docs/build-plan/05-mcp-server.md



### get_screenshot

- **05c-mcp-*.md** ← primary spec

- docs/build-plan/05-mcp-server.md



### get_settings

- **05a-mcp-*.md** ← primary spec

- docs/build-plan/input-index.md

- docs/build-plan/build-priority-matrix.md

- docs/build-plan/05-mcp-server.md



### update_settings

- **05a-mcp-*.md** ← primary spec

- docs/build-plan/input-index.md

- docs/build-plan/build-priority-matrix.md

- docs/build-plan/04-rest-api.md

- docs/build-plan/05-mcp-server.md



### zorivest_emergency_stop

- **05a-mcp-*.md** ← primary spec

- docs/build-plan/gui-actions-index.md

- docs/build-plan/05-mcp-server.md



### zorivest_emergency_unlock

- **05a-mcp-*.md** ← primary spec

- docs/build-plan/gui-actions-index.md

- docs/build-plan/05-mcp-server.md



### zorivest_diagnose

- **05b-mcp-*.md** ← primary spec

- docs/build-plan/05-mcp-server.md

- docs/build-plan/testing-strategy.md

- docs/build-plan/output-index.md

- docs/build-plan/gui-actions-index.md

- docs/build-plan/06f-gui-settings.md

- docs/build-plan/build-priority-matrix.md

- docs/build-plan/10-service-daemon.md



### zorivest_launch_gui

- **05b-mcp-*.md** ← primary spec

- docs/build-plan/05-mcp-server.md

- docs/build-plan/testing-strategy.md

- docs/build-plan/output-index.md

- docs/build-plan/build-priority-matrix.md



### get_stock_quote

- **05e-mcp-*.md** ← primary spec

- docs/build-plan/input-index.md

- docs/build-plan/05-mcp-server.md

- docs/build-plan/08-market-data.md



### get_market_news

- **05e-mcp-*.md** ← primary spec

- docs/build-plan/08-market-data.md

- docs/build-plan/05-mcp-server.md



### search_ticker

- **05e-mcp-*.md** ← primary spec

- docs/build-plan/05-mcp-server.md

- docs/build-plan/08-market-data.md



### get_sec_filings

- **05e-mcp-*.md** ← primary spec

- docs/build-plan/05-mcp-server.md

- docs/build-plan/08-market-data.md



### list_market_providers

- **05e-mcp-*.md** ← primary spec

- docs/build-plan/08-market-data.md



### test_market_provider

- **05e-mcp-*.md** ← primary spec

- docs/build-plan/08-market-data.md

- docs/build-plan/gui-actions-index.md



### disconnect_market_provider

- **05e-mcp-*.md** ← primary spec

- docs/build-plan/gui-actions-index.md

- docs/build-plan/08-market-data.md



### create_policy

- **05g-mcp-*.md** ← primary spec

- docs/build-plan/06e-gui-scheduling.md

- docs/build-plan/gui-actions-index.md

- docs/build-plan/09-scheduling.md



### list_policies

- **05g-mcp-*.md** ← primary spec

- docs/build-plan/06e-gui-scheduling.md

- docs/build-plan/09-scheduling.md



### run_pipeline

- **05g-mcp-*.md** ← primary spec

- docs/build-plan/input-index.md

- docs/build-plan/gui-actions-index.md

- docs/build-plan/06e-gui-scheduling.md

- docs/build-plan/09-scheduling.md



### preview_report

- **05g-mcp-*.md** ← primary spec

- docs/build-plan/gui-actions-index.md

- docs/build-plan/09-scheduling.md

- docs/build-plan/06e-gui-scheduling.md



### update_policy_schedule

- **05g-mcp-*.md** ← primary spec

- docs/build-plan/09-scheduling.md

- docs/build-plan/06e-gui-scheduling.md

- docs/build-plan/gui-actions-index.md



### get_pipeline_history

- **05g-mcp-*.md** ← primary spec

- docs/build-plan/gui-actions-index.md

- docs/build-plan/06e-gui-scheduling.md

- docs/build-plan/09-scheduling.md



### zorivest_service_status

- **05b-mcp-*.md** ← primary spec

- docs/build-plan/testing-strategy.md

- docs/build-plan/input-index.md

- docs/build-plan/05-mcp-server.md

- docs/build-plan/build-priority-matrix.md

- docs/build-plan/10-service-daemon.md



### zorivest_service_restart

- **05b-mcp-*.md** ← primary spec

- docs/build-plan/05-mcp-server.md

- docs/build-plan/testing-strategy.md

- docs/build-plan/gui-actions-index.md

- docs/build-plan/10-service-daemon.md



### zorivest_service_logs

- **05b-mcp-*.md** ← primary spec

- docs/build-plan/testing-strategy.md

- docs/build-plan/05-mcp-server.md

- docs/build-plan/gui-actions-index.md

- docs/build-plan/10-service-daemon.md

- docs/build-plan/output-index.md

- docs/build-plan/input-index.md



### sync_broker

- **05f-mcp-*.md** ← primary spec

- docs/build-plan/testing-strategy.md

- docs/build-plan/05-mcp-server.md

- docs/build-plan/04-rest-api.md



### list_brokers

- **05f-mcp-*.md** ← primary spec

- docs/build-plan/05-mcp-server.md

- docs/build-plan/04-rest-api.md



### get_round_trips

- **05c-mcp-*.md** ← primary spec

- docs/build-plan/05-mcp-server.md

- docs/build-plan/03-service-layer.md



### enrich_trade_excursion

- **05c-mcp-*.md** ← primary spec

- docs/build-plan/05-mcp-server.md



### get_fee_breakdown

- **05c-mcp-*.md** ← primary spec

- docs/build-plan/05-mcp-server.md



### score_execution_quality

- **05c-mcp-*.md** ← primary spec

- docs/build-plan/05-mcp-server.md



### estimate_pfof_impact

- **05c-mcp-*.md** ← primary spec

- docs/build-plan/05-mcp-server.md



### get_expectancy_metrics

- **05c-mcp-*.md** ← primary spec

- docs/build-plan/05-mcp-server.md

- docs/build-plan/testing-strategy.md



### simulate_drawdown

- **05c-mcp-*.md** ← primary spec

- docs/build-plan/05-mcp-server.md

- docs/build-plan/testing-strategy.md



### get_strategy_breakdown

- **05c-mcp-*.md** ← primary spec

- docs/build-plan/04-rest-api.md

- docs/build-plan/05-mcp-server.md



### get_sqn

- **05c-mcp-*.md** ← primary spec

- docs/build-plan/05-mcp-server.md

- docs/build-plan/04-rest-api.md



### get_cost_of_free

- **05c-mcp-*.md** ← primary spec

- docs/build-plan/05-mcp-server.md

- docs/build-plan/04-rest-api.md



### ai_review_trade

- **05c-mcp-*.md** ← primary spec

- docs/build-plan/05-mcp-server.md

- docs/build-plan/04-rest-api.md



### track_mistake

- **05i-mcp-*.md** ← primary spec

- docs/build-plan/testing-strategy.md

- docs/build-plan/04-rest-api.md

- docs/build-plan/05-mcp-server.md



### get_mistake_summary

- **05i-mcp-*.md** ← primary spec

- docs/build-plan/05-mcp-server.md



### link_trade_journal

- **05i-mcp-*.md** ← primary spec

- docs/build-plan/05-mcp-server.md

- docs/build-plan/04-rest-api.md

- docs/build-plan/05c-mcp-trade-analytics.md



### resolve_identifiers

- **05f-mcp-*.md** ← primary spec

- docs/build-plan/05-mcp-server.md

- docs/build-plan/testing-strategy.md



### import_bank_statement

- **05f-mcp-*.md** ← primary spec

- docs/build-plan/05-mcp-server.md

- docs/build-plan/04-rest-api.md

- docs/build-plan/testing-strategy.md



### import_broker_csv

- **05f-mcp-*.md** ← primary spec

- docs/build-plan/05-mcp-server.md

- docs/build-plan/04-rest-api.md



### import_broker_pdf

- **05f-mcp-*.md** ← primary spec

- docs/build-plan/05-mcp-server.md

- docs/build-plan/04-rest-api.md



### list_bank_accounts

- **05f-mcp-*.md** ← primary spec

- docs/build-plan/05-mcp-server.md

- docs/build-plan/04-rest-api.md



### detect_options_strategy

- **05c-mcp-*.md** ← primary spec

- docs/build-plan/05-mcp-server.md



### create_report

- **05c-mcp-*.md** ← primary spec

- docs/build-plan/build-priority-matrix.md



### get_report_for_trade

- **05c-mcp-*.md** ← primary spec

- docs/build-plan/build-priority-matrix.md



### create_trade_plan

- **05d-mcp-*.md** ← primary spec

- docs/build-plan/input-index.md

- docs/build-plan/gui-actions-index.md



### get_account_review_checklist

- **05f-mcp-*.md** ← primary spec



### estimate_tax

- **05h-mcp-*.md** ← primary spec

- docs/build-plan/build-priority-matrix.md



### find_wash_sales

- **05h-mcp-*.md** ← primary spec

- docs/build-plan/05c-mcp-trade-analytics.md

- docs/build-plan/build-priority-matrix.md



### simulate_tax_impact

- **05h-mcp-*.md** ← primary spec

- docs/build-plan/input-index.md

- docs/build-plan/gui-actions-index.md

- docs/build-plan/domain-model-reference.md

- docs/build-plan/build-priority-matrix.md

- docs/build-plan/05d-mcp-trade-planning.md



### get_tax_lots

- **05h-mcp-*.md** ← primary spec

- docs/build-plan/build-priority-matrix.md



### get_quarterly_estimate

- **05h-mcp-*.md** ← primary spec



### record_quarterly_tax_payment

- **05h-mcp-*.md** ← primary spec



### harvest_losses

- **05h-mcp-*.md** ← primary spec

- docs/build-plan/output-index.md

- docs/build-plan/05c-mcp-trade-analytics.md

- docs/build-plan/input-index.md

- docs/build-plan/06g-gui-tax.md

- docs/build-plan/gui-actions-index.md

- docs/build-plan/build-priority-matrix.md



### get_ytd_tax_summary

- **05h-mcp-*.md** ← primary spec

- docs/build-plan/build-priority-matrix.md



### get_log_settings

- **05a-mcp-*.md** ← primary spec



### update_log_level

- **05a-mcp-*.md** ← primary spec

