# MCP Server Tests

Per-test rating table for Phase 1 IR-5 audit.

Summary: 156 tests audited | 🟢 151 | 🟡 5 | 🔴 0

| Rating | File | Line | Test | Reason |
|---|---|---:|---|---|
| 🟢 | `mcp-server/tests/accounts-tools.test.ts` | 92 | `POSTs to /brokers/{broker_id}/sync with broker_id param` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `mcp-server/tests/accounts-tools.test.ts` | 121 | `GETs /brokers with no params` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/accounts-tools.test.ts` | 152 | `POSTs structured identifiers wrapped as JSON to /identifiers/resolve` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/accounts-tools.test.ts` | 198 | `uploads multipart to /banking/import with file_path, account_id, format_hint` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `mcp-server/tests/accounts-tools.test.ts` | 233 | `uploads multipart to /import/csv with file_path, account_id, broker_hint` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `mcp-server/tests/accounts-tools.test.ts` | 267 | `uploads multipart to /import/pdf with file_path, account_id` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `mcp-server/tests/accounts-tools.test.ts` | 300 | `GETs /banking/accounts with no params` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/accounts-tools.test.ts` | 334 | `fetches both /brokers and /banking/accounts and returns structured review` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `mcp-server/tests/accounts-tools.test.ts` | 387 | `filters to stale_only by default` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/analytics-tools.test.ts` | 59 | `get_round_trips calls GET /round-trips with query params` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/analytics-tools.test.ts` | 83 | `enrich_trade_excursion calls POST /analytics/excursion/{id}` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/analytics-tools.test.ts` | 98 | `get_fee_breakdown calls GET /fees/summary with period` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/analytics-tools.test.ts` | 113 | `score_execution_quality calls GET /analytics/execution-quality with trade_id` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/analytics-tools.test.ts` | 128 | `estimate_pfof_impact calls GET /analytics/pfof-report` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/analytics-tools.test.ts` | 143 | `get_expectancy_metrics calls GET /analytics/expectancy` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/analytics-tools.test.ts` | 158 | `simulate_drawdown calls GET /analytics/drawdown with simulations` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/analytics-tools.test.ts` | 173 | `get_strategy_breakdown calls GET /analytics/strategy-breakdown` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/analytics-tools.test.ts` | 188 | `get_sqn calls GET /analytics/sqn with period` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/analytics-tools.test.ts` | 203 | `get_cost_of_free calls GET /analytics/cost-of-free` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/analytics-tools.test.ts` | 218 | `ai_review_trade calls POST /analytics/ai-review with body` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/analytics-tools.test.ts` | 236 | `detect_options_strategy calls POST /analytics/options-strategy with leg_exec_ids` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/analytics-tools.test.ts` | 258 | `create_report calls POST /trades/{trade_id}/report with body` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/analytics-tools.test.ts` | 295 | `get_report_for_trade calls GET /trades/{trade_id}/report` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/analytics-tools.test.ts` | 317 | `registers all 14 tools with correct annotations` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `mcp-server/tests/calculator-tools.test.ts` | 55 | `calls POST /calculator/position-size with all params` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/calculator-tools.test.ts` | 101 | `returns error envelope on API failure` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/cli.test.ts` | 31 | `returns { kind: 'all' } when --toolsets all is passed` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/cli.test.ts` | 38 | `returns { kind: 'explicit', names } when --toolsets has comma-separated names` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/cli.test.ts` | 53 | `handles single toolset name without comma` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/cli.test.ts` | 60 | `returns { kind: 'defaults' } when no --toolsets flag is present` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/cli.test.ts` | 67 | `type ToolsetSelection has kind discriminant` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/cli.test.ts` | 82 | `falls back to defaults when ZORIVEST_TOOLSET_CONFIG points to missing file` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/cli.test.ts` | 90 | `--toolsets flag takes precedence over ZORIVEST_TOOLSET_CONFIG` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/client-detection.test.ts` | 52 | `returns 'anthropic' when ZORIVEST_CLIENT_MODE=anthropic` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/client-detection.test.ts` | 58 | `returns 'dynamic' when ZORIVEST_CLIENT_MODE=dynamic` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/client-detection.test.ts` | 64 | `returns 'static' when ZORIVEST_CLIENT_MODE=static` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/client-detection.test.ts` | 73 | `returns 'anthropic' for claude-code` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/client-detection.test.ts` | 78 | `returns 'anthropic' for claude-desktop` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/client-detection.test.ts` | 83 | `returns 'dynamic' for antigravity` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/client-detection.test.ts` | 88 | `returns 'dynamic' for cline` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/client-detection.test.ts` | 93 | `returns 'dynamic' for roo-code` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/client-detection.test.ts` | 98 | `returns 'dynamic' for gemini-cli` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/client-detection.test.ts` | 106 | `returns 'static' for cursor` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/client-detection.test.ts` | 111 | `returns 'static' for windsurf` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/client-detection.test.ts` | 116 | `returns 'static' for unknown client names` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/client-detection.test.ts` | 121 | `returns 'static' when client version is undefined` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/client-detection.test.ts` | 130 | `returns 'detailed' or 'concise' as ResponseFormat type` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/client-detection.test.ts` | 138 | `returns non-empty string with comprehensive instructions` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `mcp-server/tests/client-detection.test.ts` | 144 | `mentions toolsets in instructions` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/confirmation.test.ts` | 37 | `passes through without requiring confirmation_token` | specific value or behavioral assertions |
| 🟡 | `mcp-server/tests/confirmation.test.ts` | 54 | `rejects destructive tool without confirmation_token` | weak structural or mock-only assertions |
| 🟢 | `mcp-server/tests/confirmation.test.ts` | 69 | `allows destructive tool with valid token from createConfirmationToken` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/confirmation.test.ts` | 82 | `rejects arbitrary truthy string as token` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `mcp-server/tests/confirmation.test.ts` | 96 | `rejects token issued for a different action` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `mcp-server/tests/confirmation.test.ts` | 111 | `rejects token used a second time (single-use)` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `mcp-server/tests/confirmation.test.ts` | 127 | `passes through for non-destructive tools even on static mode` | specific value or behavioral assertions |
| 🟡 | `mcp-server/tests/confirmation.test.ts` | 150 | `%s requires confirmation on static clients` | weak structural or mock-only assertions |
| 🟢 | `mcp-server/tests/confirmation.test.ts` | 163 | `generates a token starting with ctk_ prefix` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/confirmation.test.ts` | 169 | `throws for unknown destructive action` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/confirmation.test.ts` | 177 | `returns true for destructive tools` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/confirmation.test.ts` | 182 | `returns false for non-destructive tools` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/diagnostics-tools.test.ts` | 105 | `returns full report when backend is reachable` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `mcp-server/tests/diagnostics-tools.test.ts` | 143 | `reports unreachable when backend is down` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/diagnostics-tools.test.ts` | 167 | `never reveals API keys in provider list` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/diagnostics-tools.test.ts` | 212 | `returns providers: [] when provider endpoint returns 404` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/diagnostics-tools.test.ts` | 251 | `includes per-tool metrics section when verbose=true` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `mcp-server/tests/diagnostics-tools.test.ts` | 273 | `returns summary-only metrics when verbose=false` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `mcp-server/tests/diagnostics-tools.test.ts` | 294 | `returns "unavailable" for auth-dependent fields when guard endpoint fails` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/diagnostics-tools.test.ts` | 345 | `passes auth headers to mcp-guard and market-data endpoints` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `mcp-server/tests/diagnostics-tools.test.ts` | 378 | `registers tool with correct annotations and _meta` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `mcp-server/tests/discovery-tools.test.ts` | 103 | `returns all registered toolsets with counts` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/discovery-tools.test.ts` | 137 | `returns tool details for known toolset` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/discovery-tools.test.ts` | 156 | `returns isError for unknown toolset` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/discovery-tools.test.ts` | 185 | `returns info if toolset already loaded` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/discovery-tools.test.ts` | 211 | `returns error for unknown toolset` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/discovery-tools.test.ts` | 237 | `enables unloaded toolset and returns enabled status` | specific value or behavioral assertions |
| 🟡 | `mcp-server/tests/discovery-tools.test.ts` | 268 | `calls sendToolListChanged after enabling toolset` | weak structural or mock-only assertions |
| 🟢 | `mcp-server/tests/discovery-tools.test.ts` | 304 | `rejects when dynamicLoadingEnabled is false` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/discovery-tools.test.ts` | 337 | `blocks when MCP Guard is locked` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/discovery-tools.test.ts` | 374 | `generates token locally for destructive action` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/discovery-tools.test.ts` | 399 | `returns isError for non-destructive action` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/discovery-tools.test.ts` | 432 | `registers all 4 tools with correct annotations` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `mcp-server/tests/guard.test.ts` | 23 | `calls POST /mcp-guard/check and returns result` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/guard.test.ts` | 42 | `returns blocked on network failure (fail-closed)` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/guard.test.ts` | 63 | `allows tool execution when guard returns allowed=true` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/guard.test.ts` | 80 | `blocks tool execution when guard is locked` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/guard.test.ts` | 100 | `blocks tool execution when rate limit exceeded` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/guard.test.ts` | 122 | `includes unlock guidance in error message` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/guard.test.ts` | 140 | `blocks on network failure (fail-closed safety)` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/gui-tools.test.ts` | 71 | `returns gui_found: false with setup_instructions when no GUI discovered` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `mcp-server/tests/gui-tools.test.ts` | 94 | `returns gui_found: true with packaged method when installed app found` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `mcp-server/tests/gui-tools.test.ts` | 117 | `returns gui_found: true with dev-mode method when dev repo detected` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/gui-tools.test.ts` | 141 | `returns gui_found: true with path method when found on PATH` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/gui-tools.test.ts` | 170 | `returns gui_found: true with env-var method via ZORIVEST_GUI_PATH` | specific value or behavioral assertions |
| 🟡 | `mcp-server/tests/gui-tools.test.ts` | 193 | `does not call guard (unguarded tool)` | weak structural or mock-only assertions |
| 🟢 | `mcp-server/tests/gui-tools.test.ts` | 208 | `honors wait_for_close=true by awaiting launchAndWait` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `mcp-server/tests/integration.test.ts` | 244 | `create_trade round-trip: POST /trades → verify response` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `mcp-server/tests/integration.test.ts` | 269 | `list_trades round-trip: GET /trades → verify array` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `mcp-server/tests/integration.test.ts` | 285 | `get_settings round-trip: GET /settings → verify object` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `mcp-server/tests/integration.test.ts` | 293 | `calculate_position_size round-trip: POST /calculator/position-size → verify result` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `mcp-server/tests/market-data-tools.test.ts` | 62 | `calls GET /market-data/quote with ticker` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `mcp-server/tests/market-data-tools.test.ts` | 88 | `calls GET /market-data/news with default count` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `mcp-server/tests/market-data-tools.test.ts` | 103 | `includes ticker filter when provided` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/market-data-tools.test.ts` | 123 | `calls GET /market-data/search with query` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `mcp-server/tests/market-data-tools.test.ts` | 144 | `calls GET /market-data/sec-filings with ticker` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `mcp-server/tests/market-data-tools.test.ts` | 165 | `calls GET /market-data/providers` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `mcp-server/tests/market-data-tools.test.ts` | 185 | `calls DELETE /market-data/providers/{name}/key` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `mcp-server/tests/market-data-tools.test.ts` | 209 | `calls POST /market-data/providers/{name}/test` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `mcp-server/tests/metrics.test.ts` | 26 | `records latency and computes percentiles` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/metrics.test.ts` | 39 | `tracks error count and rate` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/metrics.test.ts` | 48 | `warns when error rate exceeds 10%` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/metrics.test.ts` | 58 | `warns when p95 exceeds 2000ms for non-network tool` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/metrics.test.ts` | 69 | `excludes network tools from slow warnings` | specific value or behavioral assertions |
| 🟡 | `mcp-server/tests/metrics.test.ts` | 91 | `uses ring buffer to bound memory` | right target, but weak assertions only |
| 🟢 | `mcp-server/tests/metrics.test.ts` | 102 | `omits per_tool when verbose=false` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `mcp-server/tests/metrics.test.ts` | 112 | `computes session-level totals and rates` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/metrics.test.ts` | 123 | `identifies slowest and most-errored tools` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/metrics.test.ts` | 135 | `tracks average payload size` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/metrics.test.ts` | 148 | `records successful call metrics` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/metrics.test.ts` | 165 | `records failed call metrics and re-throws` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/metrics.test.ts` | 181 | `records isError results as errors` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/metrics.test.ts` | 200 | `exports a singleton MetricsCollector instance` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/metrics.test.ts` | 209 | `executes both metrics and guard layers in composition` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/metrics.test.ts` | 242 | `records guard-blocked call as error in metrics` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `mcp-server/tests/planning-tools.test.ts` | 68 | `registers with correct name and accepts full input schema` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `mcp-server/tests/planning-tools.test.ts` | 143 | `accepts minimal required fields (without optional strategy_description and account_id)` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/planning-tools.test.ts` | 177 | `returns error envelope on API failure (non-2xx)` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `mcp-server/tests/planning-tools.test.ts` | 209 | `calls guard check before API (withGuard middleware)` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `mcp-server/tests/planning-tools.test.ts` | 241 | `POSTs to /watchlists/ with name and description` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `mcp-server/tests/planning-tools.test.ts` | 265 | `returns error on duplicate name (409)` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/planning-tools.test.ts` | 285 | `GETs /watchlists/ with pagination params` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/planning-tools.test.ts` | 304 | `returns error on API failure (500)` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/planning-tools.test.ts` | 324 | `GETs /watchlists/{id} with items` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/planning-tools.test.ts` | 343 | `returns error when not found (404)` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/planning-tools.test.ts` | 363 | `POSTs to /watchlists/{id}/items with ticker and notes` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/planning-tools.test.ts` | 386 | `returns error on duplicate ticker (409)` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/planning-tools.test.ts` | 406 | `DELETEs /watchlists/{id}/items/{ticker}` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/planning-tools.test.ts` | 423 | `returns error when watchlist not found (404)` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/registration.test.ts` | 71 | `calls register() on every toolset in the registry` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/registration.test.ts` | 87 | `stores returned handles in registry via storeHandles()` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `mcp-server/tests/registration.test.ts` | 107 | `enables all toolsets when selection is { kind: 'all' }` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/registration.test.ts` | 130 | `disables non-named, non-alwaysLoaded toolsets for explicit selection` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `mcp-server/tests/registration.test.ts` | 163 | `enables only default and alwaysLoaded toolsets for defaults selection` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `mcp-server/tests/registration.test.ts` | 188 | `sets dynamicLoadingEnabled to false for static mode` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/registration.test.ts` | 200 | `keeps dynamicLoadingEnabled true for dynamic mode` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/settings-tools.test.ts` | 53 | `calls GET /settings when no key provided` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/settings-tools.test.ts` | 77 | `calls GET /settings/{key} when key provided` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/settings-tools.test.ts` | 97 | `calls PUT /settings with string-valued JSON map` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/settings-tools.test.ts` | 130 | `returns error envelope on API failure` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/trade-tools.test.ts` | 53 | `calls POST /trades with correct payload and returns envelope` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `mcp-server/tests/trade-tools.test.ts` | 126 | `defaults time to current ISO string when omitted` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `mcp-server/tests/trade-tools.test.ts` | 175 | `calls GET /trades with query params and returns envelope` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/trade-tools.test.ts` | 206 | `calls GET /trades without query when no params given` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/trade-tools.test.ts` | 222 | `decodes base64, sends multipart POST to /trades/{id}/images` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/trade-tools.test.ts` | 260 | `calls GET /trades/{id}/images and returns envelope` | specific value or behavioral assertions |
| 🟢 | `mcp-server/tests/trade-tools.test.ts` | 289 | `fetches metadata (JSON) then full image (binary), returns mixed content` | exact behavior asserted despite weaker auxiliary checks |
