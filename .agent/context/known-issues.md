# Known Issues — Zorivest

> Track bugs, limitations, and workarounds here.
> Resolved issues are archived in [known-issues-archive.md](known-issues-archive.md).

## Active Issues

### [STUB-RETIRE] — stubs.py contains legacy stubs that should be retired progressively
- **Severity:** Low (technical debt)
- **Component:** api (`stubs.py`), tests
- **Discovered:** 2026-03-19
- **Status:** Phase 1+2 cleaned; Phase 3 tracked
- **Phase 2 resolved (MEU-PW1, 2026-04-12):** `StubMarketDataService` and `StubProviderConnectionService` deleted. `MarketQuote` import removed from stubs.py.
- **Phase 3 blocked on:** `StubAnalyticsService` (MEU-104–116), `StubReviewService` (MEU-110), `StubTaxService` (MEU-123–126). Each retires when its real service is implemented.
- **Roadmap:** [09a §Stub Retirement Roadmap](../docs/build-plan/09a-persistence-integration.md)

## Mitigated / Workaround Applied

### [MCP-ZODSTRIP] — `server.tool()` silently strips arguments with z.object()
- **Severity:** Critical
- **Component:** mcp-server
- **Status:** Open — upstream SDK bug (TS-SDK #1291, #1380, PR #1603)
- **Workaround:** Enforce raw shape convention. Startup assertion for non-empty `inputSchema.properties`.

### [MCP-WINDETACH] — Node.js `detached: true` broken on Windows since 2016
- **Severity:** Critical
- **Component:** infrastructure
- **Status:** Open — upstream Node.js bug (#5146, #36808)
- **Workaround:** Windows Job Objects for process group management.

### [MCP-HTTPBROKEN] — Streamable HTTP transport has 5 failure modes
- **Severity:** High
- **Component:** mcp-server
- **Status:** Mitigated by Design (stdio primary). Pin SDK version. Never use stateless mode.

### [MCP-DIST-REBUILD] — MCP server runs from compiled `dist/`, not source `src/`
- **Severity:** High
- **Component:** mcp-server
- **Status:** Active — by design
- **Workaround:** After any `mcp-server/src/` change: `cd mcp-server && npm run build` then restart IDE.

### [UI-ESMSTORE] — electron-store v9+ (ESM-only) crashes electron-vite main process
- **Severity:** Medium
- **Component:** ui
- **Status:** Workaround Applied — pinned to `electron-store@8` (last CJS version)

### [E2E-AXEELECTRON] — `@axe-core/playwright` AxeBuilder incompatible with Electron sandbox
- **Severity:** High
- **Component:** ui (E2E tests)
- **Status:** Workaround Applied — load axe-core via `file://` URL + `page.evaluate()`

### [E2E-AXESILENT] — Accessibility scan failures are silent if the scanner itself crashes
- **Severity:** Medium
- **Component:** ui (E2E tests)
- **Status:** Active — process awareness. Wrap scan in try/catch during debugging.

### [E2E-ELECTRONLAUNCH] — Playwright `Process failed to launch!` in headless/sandboxed environments
- **Severity:** High
- **Component:** ui (E2E tests)
- **Status:** Active — environment-specific. E2E verified locally; Codex validates unit/integration only.
- **Resolution path:** `xvfb-run npx playwright test` in CI.

### [MKTDATA-OPENFIGI405] — OpenFIGI returns HTTP 405 when authenticating with API key
- **Severity:** Medium
- **Component:** infrastructure (market_data)
- **Discovered:** 2026-05-02
- **Status:** Open — needs investigation
- **Details:** When the OpenFIGI provider is updated with an API key in the dashboard, authenticated requests return `405 Method Not Allowed`. Web research confirms the OpenFIGI `/v3/mapping` and `/v3/search` endpoints are **POST-only** — a `GET` request to these endpoints will return 405 regardless of authentication. The 405 is almost certainly an HTTP method mismatch, not an auth failure. Our `provider_capabilities.py` already classifies OpenFIGI as `builder_mode="post_body"`, but the actual URL builder and MCP provider test flow may be defaulting to GET.
- **Additional context:**
  - Header format must be exactly: `X-OPENFIGI-APIKEY: <key>` (not `Authorization: Bearer`)
  - `Content-Type: application/json` is required on the POST body
  - OpenFIGI v2 is **sunset July 1, 2026** — returns `410 Gone`. All code must target v3 (ref: synthesis §9)
  - Rate limits: 25 req/6s authenticated, 5 req/6s unauthenticated, batch of 100 IDs per request
- **Investigation steps:**
  1. Trace the actual HTTP method used when the MCP `zorivest_market` test_provider action hits OpenFIGI
  2. Verify `url_builders.py` OpenFIGI builder sends POST (not GET)
  3. Confirm v3 base URL: `https://api.openfigi.com/v3/mapping`
  4. Test with `curl -X POST -H 'X-OPENFIGI-APIKEY: <key>' -H 'Content-Type: application/json' -d '[{"idType":"TICKER","idValue":"IBM","exchCode":"US"}]' https://api.openfigi.com/v3/mapping`
- **MEU Impact:** MEU-186 (Special-pattern URL builders) must implement POST-body builder for OpenFIGI

### [MKTDATA-POLYGON-REBRAND] — Polygon.io/Massive.com returns HTTP 405 — auth and domain migration
- **Severity:** Critical
- **Component:** infrastructure (market_data), mcp-server, docs
- **Discovered:** 2026-05-02
- **Updated:** 2026-05-02 (user-reported: both old Polygon key and new Massive key give 405)
- **Status:** Open — investigation + migration needed
- **Details:** Polygon.io **rebranded as Massive.com** (Oct 30, 2025). User reports:
  - New Massive.com API key → **HTTP 405** when testing
  - Old Polygon.io API key → **also fails** (key no longer works)
  - Web research confirms: existing Polygon keys SHOULD work with both domains, same endpoints, same auth. 405 = **HTTP method mismatch** (not auth failure).
- **Root cause hypothesis:** Our `provider_registry.py:27` has `base_url="https://api.polygon.io/v2"` and `auth_method=AuthMethod.BEARER_HEADER` with template `"Authorization": "Bearer {api_key}"`. The test endpoint is `/aggs/ticker/AAPL/range/1/day/2024-01-02/2024-01-02`. This is a GET endpoint — the 405 suggests the request is being sent as the wrong HTTP method, OR the base URL + endpoint combination is malformed (e.g., double path segments). Polygon also accepts `?apiKey=` query parameter auth, which may be more reliable than Bearer header.
- **Codebase impact (37 references across 10 files):**
  - `provider_registry.py:25-34` — base_url, auth, signup_url, test_endpoint
  - `provider_capabilities.py:79-98` — capability entry
  - `url_builders.py:94-201` — PolygonUrlBuilder class + registry
  - `response_extractors.py:108-137` — 3 extractors (ohlcv, quote, news)
  - `normalizers.py:44-63,226` — normalize_polygon_quote + registry
  - `field_mappings.py:19,52-136` — alias + 4 mapping tuples (ohlcv/quote/news/fundamentals)
  - `redaction.py:30` — Bearer token redaction comment
  - `provider_connection_service.py:87-92` — validator + test flow (uses standard GET path)
  - `market_data_service.py:393-394` — Polygon quote URL builder
- **Investigation steps:**
  1. Test both domains with curl: `curl -v "https://api.polygon.io/v2/aggs/ticker/AAPL/range/1/day/2024-01-02/2024-01-02?apiKey=KEY"` vs `curl -v "https://api.massive.com/v2/aggs/ticker/AAPL/range/1/day/2024-01-02/2024-01-02?apiKey=KEY"`
  2. Test Bearer header vs query param: `curl -H "Authorization: Bearer KEY" ...` vs `?apiKey=KEY`
  3. Verify the test_endpoint path doesn't result in a double `/v2/v2/` due to base_url having /v2 and builder adding /v2
  4. Check if Massive.com requires different auth header format than Polygon.io
- **Migration scope (once 405 is resolved):**
  - `api.polygon.io` → `api.massive.com` (both still work in parallel)
  - Dashboard: `https://massive.com/dashboard/keys`
  - Docs: `massive.com/docs`
  - No API schema changes — same endpoints, same response shapes
- **MEU Impact:** Blocks MEU-185/186 URL builder work until 405 is diagnosed

### [MKTDATA-YAHOO-UNOFFICIAL] — Yahoo Finance is deeply integrated as default quote provider — expand via yfinance
- **Severity:** Medium (risk) / High (opportunity)
- **Component:** infrastructure (market_data)
- **Discovered:** 2026-05-02
- **Updated:** 2026-05-02 (codebase audit reveals Yahoo is the PRIMARY provider, not just a fallback)
- **Status:** Open — expansion discovery in progress
- **Codebase integration (deeply embedded across 6+ files):**
  - `market_data_service.py:98-113` — **Yahoo is tried FIRST for every quote** (before any API-key provider). `get_quote()` calls `_yahoo_quote()` before the provider loop.
  - `market_data_service.py:245-303` — Full `_yahoo_quote()` implementation using `v8/finance/chart/{ticker}?range=1d&interval=1d` — extracts regularMarketPrice, chartPreviousClose, volume from chart meta.
  - `provider_connection_service.py:338-415` — Dedicated `_test_yahoo_finance_crumb()` with 2-step cookie+crumb dance (`fc.yahoo.com` → `/v1/test/getcrumb`).
  - `provider_registry.py:141-157` — Full ProviderConfig with `base_url="https://query1.finance.yahoo.com"`, browser-like headers (User-Agent, Referer), signup_url pointing to `pypi.org/project/yfinance/`.
  - `url_builders.py:46-75,200` — `YahooUrlBuilder` class using v8/chart epochs.
  - `response_extractors.py:45-107` — 2 extractors: `yahoo/quote` (v8/chart meta), `yahoo/news` (list or items wrapper).
  - `field_mappings.py:18,70-135` — 3 mapping tuples: `yahoo/quote`, `yahoo/news`, `yahoo/fundamentals`.
  - `service_factory.py:88` — GET-with-cookies adapter specifically for Yahoo.
- **Current data coverage vs yfinance potential:**
  | Data Type | Current Status | yfinance Capability | Expansion Path |
  |---|---|---|---|
  | **Quote** | ✅ Default (v8/chart meta) | ✅ `Ticker.info` | Already working |
  | **OHLCV** | ❌ Not wired | ✅ `Ticker.history()` / `yf.download()` | `v8/chart` with full history params |
  | **News** | ⚠️ Extractor exists, broken | ⚠️ `Ticker.news` (fragile) | Needs endpoint update |
  | **Fundamentals** | ⚠️ Field mapping exists, not wired | ✅ `Ticker.info`, `balance_sheet`, `financials`, `cashflow` | `quoteSummary` modules |
  | **Earnings** | ❌ | ✅ `Ticker.calendar`, `get_earnings_dates()` | `/v10/finance/quoteSummary?modules=earnings` |
  | **Dividends** | ❌ | ✅ `Ticker.dividends` | `/v8/finance/chart` includes dividend events |
  | **Splits** | ❌ | ✅ `Ticker.splits` | `/v8/finance/chart` includes split events |
  | **Insider** | ❌ | ❌ Not reliable in yfinance | Use Finnhub/FMP instead |
  | **Economic Calendar** | ❌ | ⚠️ `Calendars` class (fragile) | Not recommended |
- **Risk factors (unchanged):**
  - All Yahoo endpoints are **unofficial/reverse-engineered** (no official API since 2017)
  - v6 `/finance/quote` has returned **404 since ~2024** — v8/chart is current working endpoint
  - Using these endpoints **violates Yahoo's Terms of Service**
  - Endpoints break frequently — the 2-step cookie+crumb dance was added mid-2023
- **Decision update:** Given Yahoo is already the DEFAULT quote provider (tried before all API-key providers), removal is impractical. **Recommended approach: expand cautiously.** Use v8/chart for OHLCV/dividends/splits (same endpoint, different params) and v10/quoteSummary for fundamentals/earnings. Keep as best-effort fallback with graceful degradation. All expanded data types should have API-key-provider fallbacks.
- **Resolved (2026-05-02):** Yahoo OHLCV extractor + field mapping added — same parallel-array zip pattern as Finnhub candles. URL builder already supported ohlcv; now extractor completes the pipeline.
- **Expansion items needing separate planning (mini-MEU or piggyback on MEU-190/191):**
  | Item | Effort | What's needed |
  |------|--------|---------------|
  | **Fundamentals** | Medium | New URL path (`/v10/finance/quoteSummary?modules=defaultKeyStatistics,financialData`), new extractor for deeply-nested module dicts, field mapping already exists |
  | **Earnings** | Medium | Same quoteSummary approach (`modules=earnings,earningsHistory`), new extractor + field mapping |
  | **Dividends** | Medium | URL builder update (`&events=div`), new extractor for `chart.result[0].events.dividends` dict, new field mapping |
  | **Splits** | Medium | URL builder update (`&events=split`), new extractor for `chart.result[0].events.splits` dict, new field mapping |
  | **News endpoint fix** | Low | Existing extractor may need endpoint update — `v1/finance/search` news has been fragile |
- **MEU Impact:** OHLCV resolved. Remaining items can piggyback on MEU-190/191 (service methods) or be a standalone mini-MEU.


### [MKTDATA-TRADINGVIEW-NOPUBLICAPI] — TradingView scanner API already integrated — expand data types cautiously
- **Severity:** Medium (opportunity)
- **Component:** infrastructure (market_data)
- **Discovered:** 2026-05-02
- **Updated:** 2026-05-02 (quote + fundamentals extractors added via scanner column-zip)
- **Status:** Open — partial expansion complete, further items need planning
- **Codebase integration (registered as free provider, actively used for screening):**
  - `provider_registry.py:158-178` — Full ProviderConfig: `base_url="https://scanner.tradingview.com"`, `AuthMethod.NONE`, POST-based with JSON Content-Type.
  - `provider_connection_service.py:343-457` — Dedicated `_test_tradingview_scanner()` method: POST to `/america/scan` with `{"columns": ["name"], "range": [0, 1]}` — returns `{"totalCount": N, "data": [...]}`.
  - `service_factory.py:64,78` — POST-with-JSON adapter specifically for TradingView scanner API, with `follow_redirects=True` for pingpong redirect.
  - `url_builders.py` — `TradingViewUrlBuilder` with `build_request()` → `RequestSpec(method="POST", ...)` supporting quote + fundamentals column sets.
  - `response_extractors.py` — `_tradingview_quote` and `_tradingview_fundamentals` extractors using column-zip pattern for `{data: [{s, d}]}` envelope.
  - `field_mappings.py` — 2 mapping tuples: `tradingview/quote` (identity), `tradingview/fundamentals` (scanner columns → canonical).
  - `test_provider_service_wiring.py:5,59,74,79` — Tests confirm TradingView in provider list (13 total).
  - `test_provider_registry.py:10,47` — Tests confirm `AuthMethod.NONE` classification.
  - `ui/src/renderer/src/features/settings/MarketDataProvidersPage.tsx:44` — Listed in `FREE_PROVIDERS` set.
  - `ui/tests/e2e/settings-market-data.test.ts:105-110` — E2E test for "no-API-key badge".
- **Scanner API data capabilities (from web research + `tradingview-screener` library analysis):**
  - The `scanner.tradingview.com/{exchange}/scan` POST endpoint accepts a `columns` array with **thousands of available fields**.
  - Via unofficial `tradingview-screener` / `tvscreener` Python libraries, the scanner can return:
  | Data Type | Scanner Field Examples | Viability |
  |---|---|---|
  | **Quote** | `close`, `volume`, `change`, `change_abs`, `Recommend.All` | ✅ Current price + technicals |
  | **OHLCV** | `open`, `high`, `low`, `close`, `volume` (snapshot, NOT historical) | ⚠️ Current bar only — no historical candles |
  | **Fundamentals** | `market_cap_basic`, `earnings_per_share_basic_ttm`, `price_earnings_ttm`, `dividend_yield_indication`, `price_book_ratio`, `debt_to_equity` | ✅ Rich fundamental screening data |
  | **Technicals** | RSI, MACD, Bollinger, moving averages, oscillators | ✅ Full technical indicator suite |
  | **Historical OHLCV** | ❌ Not available via scanner | ❌ No candle history endpoint |
  | **News** | ❌ Not available via scanner | ❌ No news endpoint |
  | **Earnings/Dividends/Splits** | `earnings_release_date`, `dividends_yield`, `split_ratio` | ⚠️ Snapshot fields only, no history |
- **Key limitations:**
  - Scanner returns **point-in-time screening data**, NOT historical time series
  - All access is **unofficial** — same TOS risk as Yahoo
  - Rate limiting is undocumented — aggressive requests may be blocked
  - `symbol-search.tradingview.com` is **Cloudflare-blocked (403)** for scripts (already documented in registry)
- **Revised assessment:** TradingView CAN serve as a **supplementary free provider** for real-time quotes and fundamental snapshots, similar to Yahoo's role. It cannot replace API-key providers for historical data, news, or detailed earnings/dividend history.
- **Resolved (2026-05-02):** Quote + fundamentals extractors added via scanner column-zip pattern. URL builder with `build_request()` → `RequestSpec(method="POST")`. Field mappings registered. Same POST runtime deferral as OpenFIGI/SecApi (MEU-189).
- **What would need more planning:**
  | Item | Effort | What's needed |
  |------|--------|---------------|
  | **POST runtime wiring** | MEU-189 | Adapter `_do_fetch()` + `fetch_with_cache()` POST dispatch — same blocker as OpenFIGI/SecApi. Without this, builder/extractor are tested but not runtime-callable. |
  | **Exchange routing** | Medium | Currently hardcoded to `/america/scan`. International tickers need exchange detection logic (e.g., `7203` → `japan`, `VOW3` → `germany`). Decision: auto-detect from ticker format, or require explicit `criteria.exchange`? |
  | **Rate limiting strategy** | Medium | Undocumented limits. Need retry/backoff/429-handling. Could be aggressive since no API key → no accountability. |
  | **Multi-ticker batching** | Medium | Scanner natively supports multiple symbols per POST (`symbols.tickers` array). Current per-ticker adapter loop is wasteful. Needs batch adapter or explicit batch endpoint. |
  | **Response freshness / caching** | Low | Scanner returns latest snapshot only (no time-series). Caching semantics differ from REST GET patterns — needs TTL policy (e.g., 5-min cache vs daily for OHLCV). |
  | **Technicals data type** | Low | Rich technical indicator columns available (RSI, MACD, etc.) but no canonical schema defined yet. Needs data type definition + field mapping. |
- **MEU Impact:** Quote + fundamentals resolved. Remaining items can piggyback on MEU-189 (POST runtime) or be a standalone mini-MEU for exchange routing / batching.

## Archived (see [known-issues-archive.md](known-issues-archive.md))

| ID | Resolved | Summary |
|----|----------|---------|
| PLAN-NOSIZE | 2026-04-11 | position_size full-stack propagation (MEU-70a) |
| BOUNDARY-GAP | 2026-04-11 | 7/7 API validation findings closed |
| PYRIGHT-PREEXIST | 2026-04-11 | TS1+TS2+TS3 all tiers resolved |
| TEST-ISOLATION | 2026-04-06 | Cleanup fixtures added |
| TEST-ISOLATION-2 | 2026-04-11 | Per-module app factory |
| TEST-DRIFT-MDS | 2026-04-12 | All 13 market data service tests pass (silently fixed by MEU-65a) |
| SCHED-PIPELINE-WIRING | 2026-04-12 | Pipeline runtime wiring complete (MEU-PW1) |
| SCHED-WALPICKLE | 2026-03-19 | Module-level callback extraction |
| SCHED-RUNREPO | 2026-03-19 | Key translation in adapter |
| MCP-CONFIRM | 2026-03-19 | Added confirmation_token to schema |
| DOC-STALESLUG | 2026-03-22 | MEU slug reference corrected |
| PIPE-CHARMAP | 2026-04-19 | Pipeline charmap crash fixed — structlog UTF-8 config + bytes-safe JSON (MEU-PW4) |
| PIPE-ZOMBIE | 2026-04-19 | Zombie runs eliminated — dual-write→single-writer, run_id passthrough, recover_zombies (MEU-PW5) |
| PIPE-DEDUP | 2026-04-20 | Dedup blocking fixed — run_id fallback when snapshot_hash absent (TDD-verified) |
| WF-SEGREGATE | 2026-04-19 | Split 2 combined workflows into 4 mode-specific variants with HARD STOP |
| TEMPLATE-RENDER | 2026-04-20 | SendStep template rendering implemented — 4-tier priority chain via Jinja2 (MEU-PW9) |
| PIPE-CURSORS | 2026-04-20 | Pipeline cursor tracking implemented — high-water mark upsert in FetchStep (MEU-PW11) |
| SCHED-TZDISPLAY | 2026-04-20 | Two-part fix: (1) PolicyList migrated to formatTimestamp() with policy timezone (MEU-72a), (2) normalizeUtc() added to formatDate.ts — appends Z to naive ISO strings from SQLAlchemy DateTime columns |
| PIPE-E2E-CHAIN | 2026-04-21 | Integration tests added for Fetch→Transform→Send chain (MEU-PW13) |
| PIPE-CACHEUPSERT | 2026-04-21 | Cache upsert integration test added in test_pipeline_dataflow.py |
| PIPE-STEPKEY | 2026-04-21 | _resolve_source() with 3-tier fallback replaces hardcoded fetch_result key (MEU-PW12) |
| PIPE-TMPLVAR | 2026-04-21 | TransformStep output_key + two-level merge in _resolve_body() feeds template vars (MEU-PW12) |
| PIPE-RAWBLOB | 2026-04-21 | Per-provider response extractors unwrap API envelopes (MEU-PW12) |
| PIPE-PROVNORM | 2026-04-21 | _PROVIDER_SLUG_MAP normalizes display names to registry slugs (MEU-PW12) |
| PIPE-QUOTEFIELD | 2026-04-21 | Presentation mapping (last→price, ticker→symbol) aligns template fields (MEU-PW12) |
| PIPE-SILENTPASS | 2026-04-21 | min_records param + WARNING status on zero records (MEU-PW12) |
| PIPE-URLBUILD | 2026-04-19 | Per-provider URL builder registry + headers_template forwarding (MEU-PW6) |
| PIPE-NOCANCEL | 2026-04-19 | CANCELLING status + cancel endpoint + cooperative step check (MEU-PW7) |
| PIPE-NOLOCALQUERY | 2026-04-25 | QueryStep (MEU-PH4) provides local DB query capability |
| GUI-EMAILTMPL | 2026-04-28 | Email Templates GUI tab in SchedulingLayout (MEU-72b) |
| PIPE-DROPPDF | 2026-04-28 | PDF→Markdown migration, Playwright dep removed (MEU-PW14) |
| MCP-APPROVBYPASS | 2026-04-29 | CSRF approval token: `validate_approval_token` middleware on approve endpoint (MEU-PH11) |
| MCP-POLICYGAP | 2026-04-29 | 3 MCP tools added: `delete_policy`, `update_policy`, `get_email_config` (MEU-PH12) |
| EMULATOR-VALIDATE | 2026-04-29 | VALIDATE phase: EXPLAIN SQL, SMTP check, step wiring validation (MEU-PH13) |
| TRADE-CASCADE | 2026-04-29 | Cascade delete for trade with linked report/images — ORM cascade + service cleanup |
| MCP-TOOLPROLIFERATION | 2026-04-29 | 85→13 compound-tool consolidation complete (P2.5f MC0–MC5). 4 toolsets: core, trade, data, ops |
| PIPE-RUNBYPASS | 2026-04-29 | POST /policies/{id}/run CSRF-gated — `validate_approval_token` added to prevent MCP confirmation bypass via direct API (SEC-1) |
| MCP-TOOLAUDIT | 2026-04-30 | Audit PASS — 46/46 tools, 4/4 critical findings resolved (P2.5f) |
| MCP-TOOLDISCOVERY | 2026-04-30 | MEU-TD1: All 13 compound tool descriptions enriched with M7 metadata |
| MCP-TOOLCAP | 2026-04-30 | 85→13 compound-tool consolidation resolves IDE tool limits permanently |
| MCP-AUTHRACE | 2026-04-30 | TokenRefreshManager singleton with promise coalescing + 30s proactive expiry (MEU-PH14, P2.5g) |

## Template

When adding issues, use this format:

```markdown
### [SHORT-TITLE] — Brief description
- **Severity:** Critical / High / Medium / Low
- **Component:** core / infrastructure / api / ui / mcp-server
- **Discovered:** YYYY-MM-DD
- **Status:** Open / In Progress / Workaround Applied
- **Details:** What happens, how to reproduce
- **Workaround:** (if any)
```
