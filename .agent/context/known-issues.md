# Known Issues — Zorivest

> Track bugs, limitations, and workarounds here.
> Resolved issues are archived in [known-issues-archive.md](known-issues-archive.md).

## Active Issues

### [MCP-FINNHUB-NEWS] — Finnhub news endpoint returns 422
- **Severity:** Medium
- **Component:** infrastructure (market_data)
- **Discovered:** 2026-05-14 (MCP Audit v3+)
- **Status:** Open — KNOWN since audit v3
- **Details:** `zorivest_market(action:"news")` returns 503 because Finnhub's company news endpoint returns HTTP 422. No fallback provider configured for news.
- **Audit ref:** I-5

### [MCP-SEC-FILINGS] — SEC filings normalizer not configured
- **Severity:** Medium
- **Component:** infrastructure (market_data)
- **Discovered:** 2026-05-14 (MCP Audit v3+)
- **Status:** Open — KNOWN since audit v3
- **Details:** `zorivest_market(action:"filings")` returns 503. SEC filing response normalizer is not implemented in any provider adapter.
- **Audit ref:** I-6

### [MCP-FMP-DEPRECATED] — Financial Modeling Prep endpoint deprecated
- **Severity:** Low
- **Component:** infrastructure (market_data)
- **Discovered:** 2026-05-14 (MCP Audit v3+)
- **Status:** Open — informational, provider still responds
- **Details:** `zorivest_market(action:"test_provider", provider:"FMP")` returns "endpoint deprecated" message. Provider still passes connectivity but may stop working.
- **Audit ref:** I-7

### [MCP-WATCHLIST-NODELETE] — No delete_watchlist action
- **Severity:** Low
- **Component:** mcp-server, api
- **Discovered:** 2026-05-14 (MCP Audit v3+)
- **Status:** Open — KNOWN since audit v3
- **Details:** `zorivest_watchlist` has no `delete` action. Residual test watchlists accumulate with no cleanup path via MCP.
- **Audit ref:** I-8

### [MCP-IMPORT-STUBS] — 3 import actions return 501 Not Implemented
- **Severity:** Low
- **Component:** api, mcp-server
- **Discovered:** 2026-05-14 (MCP Audit v3+)
- **Status:** Open — KNOWN since audit v3
- **Details:** `list_brokers`, `resolve_identifiers`, `list_bank_accounts` all return 501. These are unimplemented backend stubs.
- **Audit ref:** I-9

### [TAX-PROFILE-BLOCKED] — MEU-156 toggle persistence blocked on missing TaxProfile CRUD API
- **Severity:** Medium
- **Component:** api, ui (tax)
- **Discovered:** 2026-05-14
- **Status:** Tracked — MEU-148a (`tax-profile-api`) registered in BUILD_PLAN.md, matrix item 75a
- **Details:** `TaxProfileSettings` page is read-only because no `GET`/`PUT /api/v1/tax/profile` endpoint exists. MEU-156 (`tax-section-toggles`) cannot persist Section 475/1256/Forex elections without it. MEU-148a spec added to `04f-api-tax.md` §TaxProfile CRUD. Dependency chain: MEU-156 → MEU-148a → MEU-18 ✅, MEU-124 ✅, MEU-148 ✅.
- **Resolution:** Implement MEU-148a before MEU-156.

### [TAX-HARDCODED-IRS] — IRS-dependent constants hardcoded in Python source files
- **Severity:** Medium (maintenance risk)
- **Component:** core (domain/tax)
- **Discovered:** 2026-05-14
- **Status:** Open — no MEU registered yet (candidate: MEU-148b `tax-schedule-data`)
- **Details:** All IRS-dependent values are hardcoded as Python dict literals and module-level constants across 4 files. Adding a new tax year requires a code change + redeploy. Inventory:
  - `brackets.py`: 56 federal bracket threshold/rate pairs + 24 LTCG pairs + penalty rates (annual/quarterly IRS updates)
  - `niit.py`: NIIT rate (3.8%) + MAGI thresholds ($200K/$250K/$125K) — statutory but could change
  - `quarterly.py`: safe harbor AGI thresholds ($150K/$75K) — statutory
  - `loss_carryforward.py`: capital loss deduction caps ($3K/$1.5K) — statutory since 1978
- **Recommended fix:** Externalize into data layer (JSON files for bracket tables, SettingsRegistry for scalars), add `GET`/`PUT /api/v1/tax/schedule/{year}` endpoints, add separate "Tax Schedule" settings page distinct from "Tax Profile" page. Phase 3E, matrix item 75b.
- **Workaround:** Currently functional for 2025/2026 tax years. Manual code update required for 2027.
- **Analysis:** [Full inventory & design options](sessions/2026-05-14-tax-irs-externalization-analysis.md)

### [STUB-RETIRE] — stubs.py contains legacy stubs that should be retired progressively
- **Severity:** Low (technical debt)
- **Component:** api (`stubs.py`), tests
- **Discovered:** 2026-03-19
- **Status:** Phase 1+2 cleaned; Phase 3 tracked
- **Phase 2 resolved (MEU-PW1, 2026-04-12):** `StubMarketDataService` and `StubProviderConnectionService` deleted. `MarketQuote` import removed from stubs.py.
- **Phase 3 blocked on:** `StubAnalyticsService` (MEU-104–116), `StubReviewService` (MEU-110), `StubTaxService` (MEU-123–126). Each retires when its real service is implemented.
- **Roadmap:** [09a §Stub Retirement Roadmap](../docs/build-plan/09a-persistence-integration.md)

### [TICKER-NONEQUITY-FILTER] — Yahoo search filters out futures, forex, and crypto results; options need chain browser
- **Severity:** Medium (feature gap)
- **Component:** core (market_data_service), ui (PositionCalculatorModal)
- **Discovered:** 2026-05-14
- **Status:** Open — Phase A is a candidate micro-MEU (~2 hours), Phase B is a separate MEU (~1–2 days)
- **Details:** `_yahoo_search()` in `market_data_service.py` explicitly excludes `FUTURE`, `CURRENCY`, `CRYPTOCURRENCY` quote types. Yahoo's API already returns these — we just filter them out. Additionally, `TickerSearchResult` DTO has no `instrument_type` field, so the UI uses fragile client-side regex heuristics for auto-mode-switching. Yahoo also provides options chain data via `/v7/finance/options/{symbol}` (calls, puts, strikes, expirations, greeks) — but options don't appear in search results and need a dedicated chain browser UI.
- **Impact:** Position Calculator cannot auto-switch to futures/forex/crypto mode based on ticker selection. Options mode has no data integration at all.
- **Resolution path:**
  - **Phase A** (futures/forex/crypto): (1) Add `instrument_type` to `TickerSearchResult` DTO, (2) remove non-equity types from exclusion set, (3) pass Yahoo's `quoteType` through, (4) use server-provided type in UI. No new provider needed.
  - **Phase B** (options): (1) Add `get_options_chain()` to `MarketDataService` using Yahoo `/v7/finance/options/{symbol}`, (2) add API endpoint, (3) build Options Chain Browser UI component. No new provider needed — Yahoo covers it.
- **Analysis:** [Full findings & provider comparison](sessions/2026-05-14-non-equity-ticker-lookup-findings.md)

### [MCP-DEADTOOLS] — 11 standalone tool files in mcp-server/src/tools/ are dead code
- **Severity:** Low (technical debt)
- **Component:** mcp-server
- **Discovered:** 2026-05-15 (MEU-218a/b session)
- **Status:** Open — cleanup candidate, no runtime impact
- **Details:** After the MC4 compound tool consolidation (85→13 tools), 11 of 13 files in `mcp-server/src/tools/` are never imported. They compile into `dist/` but are unreachable dead code. Only `scheduling-tools.ts` and `pipeline-security-tools.ts` remain active (for MCP resource registration, not tools).
- **Dead files (11):**
  - `tax-tools.ts` — 4× 501 stubs + standalone `sync_tax_lots` (all superseded by compound `zorivest_tax`)
  - `accounts-tools.ts` — superseded by `compound/account-tool.ts`
  - `analytics-tools.ts` — superseded by `compound/analytics-tool.ts`
  - `trade-tools.ts` — superseded by `compound/trade-tool.ts`
  - `market-data-tools.ts` — superseded by `compound/market-tool.ts`
  - `planning-tools.ts` — superseded by `compound/plan-tool.ts`
  - `calculator-tools.ts` — superseded by compound tools
  - `diagnostics-tools.ts` — superseded by `compound/system-tool.ts`
  - `discovery-tools.ts` — superseded by compound tools
  - `gui-tools.ts` — superseded by compound tools
  - `settings-tools.ts` — superseded by compound tools
- **Alive files (2):** `scheduling-tools.ts`, `pipeline-security-tools.ts` (resource registration only)
- **Verification command:** `cd mcp-server/src && rg -l "from.*tools/(accounts|analytics|calculator|diagnostics|discovery|gui|market-data|planning|settings|tax|trade)-tools" --type ts` — should return 0 results
- **Resolution:** Delete dead files, verify `tsc --noEmit` + `npm run build` still pass, confirm tool count unchanged in `zorivest-tools.json`

### [GUI-ARIA-GAP] — Tax components have near-zero ARIA coverage; other features inconsistent
- **Severity:** Medium (accessibility compliance / WCAG 2.1 AA gap)
- **Component:** ui (features/tax, features/*, components/)
- **Discovered:** 2026-05-16
- **Status:** Partial — tax module remediated (MEU-218h, 2026-05-16); **other GUI areas still need deep audit**
- **Details:** Surface-level scan (`rg "aria-|role="`) reveals a significant disparity:
  - **Tax features (10 components, ~100KB TSX):** Only **1** ARIA attribute total (`role="status"` on `TaxDisclaimer.tsx`). Zero `aria-label`, zero `aria-live`, zero `role="button"`, zero `role="tablist"` across `TaxDashboard`, `TaxLayout`, `TaxLotViewer`, `TaxProfileManager` (31KB), `WhatIfSimulator`, `WashSaleMonitor`, `QuarterlyTracker`, `LossHarvestingTool`, `TransactionAudit`.
  - **Shared components (15 files):** Good coverage — `alertdialog` + `aria-modal` + `aria-labelledby` on all 3 modals, `role="listbox"` + `aria-selected` on autocomplete, `aria-label` on nav buttons, `role="status"` on loading skeleton. ~40+ ARIA attributes.
  - **Planning (3 files):** Moderate — `role="group"` + `aria-pressed` on status toggles, `role="dialog"` + `aria-modal` on calculator, `role="switch"` + `aria-checked` on apply toggles. ~12 ARIA attributes.
  - **Settings (2 files):** Moderate — `aria-hidden="true"` on decorative emoji, `aria-label` on provider status. ~12 ARIA attributes.
  - **Trades (4 files):** Sparse — `aria-disabled`, `aria-label`, `role="region"`. ~5 attributes.
  - **Accounts (1 file):** Minimal — 1× `aria-label`. ~1 attribute.
- **Preliminary gap categories (tax):**
  1. **Forms** — `<select>`, `<input>`, filter controls have no `aria-label`
  2. **Tables** — data tables have no `aria-label` or `role="table"`
  3. **Action buttons** — "Close", "Reassign", "Simulate" missing `aria-label`
  4. **Interactive lists** — wash sale chain items are clickable `<div>`s with no `role="button"` or keyboard event handlers
  5. **Detail/result panels** — no `aria-live` regions for dynamic content rendering
  6. **Tab navigation** — tax tabs use `data-testid` but lack `role="tablist"` / `role="tab"` / `aria-selected`
- **⚠️ Action required before remediation:**
  1. **Deep scan** all GUI components (not just `rg` for `aria-`) to identify missing semantic HTML (`<nav>`, `<main>`, `<section>`, `<aside>`), missing `<label>` associations, keyboard trap risks, focus management gaps, and color contrast issues
  2. **Sequential thinking audit** to classify each gap by WCAG 2.1 AA criterion, prioritize by user impact, and determine whether the fix is per-component or warrants a shared accessible primitive (e.g., reusable `TabList`, `DataTable`, `DetailPanel` wrappers)
  3. **Cross-reference** against existing E2E axe scans (only `tax-dashboard.test.ts` runs axe currently) to determine which pages have automated coverage and which are untested
  4. Register as MEU once audit is complete (candidate: Phase 12 or Phase 6 GUI polish)
- **E2E axe evidence:** Dashboard axe scan required `heading-order` exclusion (h3 without h2) — see MEU-218g in `implementation-plan.md`. No other pages have axe E2E coverage.

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

### [MKTDATA-POLYGON-REBRAND] — Polygon.io → Massive.com domain migration
- **Severity:** Low
- **Component:** infrastructure (market_data)
- **Discovered:** 2026-05-02
- **Status:** Tracked — MEU-195 (`polygon-massive-migration`) ⬜ planned in Phase 8a
- **Details:** Polygon.io rebranded as Massive.com (Oct 2025). `api.polygon.io` still works in parallel. No API schema changes. Simple `base_url` + `signup_url` swap.
- **MEU Impact:** MEU-195 is small and independent. Piggybacks on Phase 8a L4 batch.

### [MKTDATA-YAHOO-UNOFFICIAL] — Yahoo Finance expansion (unofficial API)
- **Severity:** Medium (risk) / High (opportunity)
- **Component:** infrastructure (market_data)
- **Discovered:** 2026-05-02
- **Status:** Open — OHLCV resolved (2026-05-02); remaining expansion tracked
- **Details:** Yahoo is the DEFAULT quote provider (tried before API-key providers). Deeply embedded across 6+ files. All endpoints are unofficial (no official API since 2017, TOS violation).
- **Resolved:** OHLCV extractor + field mapping added (2026-05-02).
- **Remaining:** Fundamentals (v10/quoteSummary), earnings, dividends (`v8/chart?events=div`), splits, news endpoint fix. All piggyback on MEU-190/191.
- **Research detail:** See [08a-market-data-expansion.md](../../docs/build-plan/08a-market-data-expansion.md) and [issue-triage-report.md](issue-triage-report.md) for full capability tables.

### [MKTDATA-TRADINGVIEW-NOPUBLICAPI] — TradingView scanner expansion (unofficial API)
- **Severity:** Medium (opportunity)
- **Component:** infrastructure (market_data)
- **Discovered:** 2026-05-02
- **Status:** Open — quote + fundamentals resolved (2026-05-02); POST runtime resolved (MEU-189 ✅)
- **Details:** TradingView scanner (`scanner.tradingview.com`) registered as free provider. Column-zip extractors for quote + fundamentals. Same TOS risk as Yahoo.
- **Remaining:** Exchange routing (hardcoded `/america/scan`), multi-ticker batching, rate limiting, caching TTL, technicals schema. All are opportunistic P4 items.
- **Research detail:** See [issue-triage-report.md](issue-triage-report.md) for full scanner capability analysis.

### [MEU-128-COLLISION] — MEU-128 ID assigned to both tax and GUI components
- **Severity:** Low (documentation)
- **Component:** docs (build-plan)
- **Discovered:** 2026-05-12
- **Status:** Tracked — deferred to GUI doc maintenance
- **Details:** MEU-128 is `options-assignment` in BUILD_PLAN.md (tax, canonical) but `gui-screenshot` in `06-gui.md:428` and `testing-strategy.md:554`. No runtime conflict — purely a doc cross-reference collision.
- **Resolution:** Renumber the GUI screenshot MEU during the next GUI phase plan update.

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
| MCP-TOOLAUDIT | 2026-05-14 | Audit v4.1 — 69/75 pass, 0 regressions, 4 tax failures RESOLVED (inline migration), tax expanded 4→8 actions, market 7→15 actions |
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
