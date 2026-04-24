# Known Issues — Zorivest

> Track bugs, limitations, and workarounds here.
> Resolved issues are archived in [known-issues-archive.md](known-issues-archive.md).

## Active Issues


### [PIPE-NOLOCALQUERY] — No pipeline step type for querying local DB tables (trades, plans, watchlists, accounts)
- **Severity:** Medium (feature gap)
- **Component:** core (`pipeline_steps/`), infrastructure (`adapters/`)
- **Discovered:** 2026-04-21
- **Status:** Open — needs MEU scoping
- **Details:** `FetchStep` is hard-wired to `MarketDataProviderAdapter` (external HTTP only). It cannot query local DB tables like `trades`, `trade_plans`, `watchlists`, or `accounts`. `StoreReportStep` has `data_queries` (sandboxed SQL → snapshot), but that output goes into `report_data` / `snapshot_json`, not into the transform pipeline. `CriteriaResolver` supports `db_query` criteria type, but only for resolving date ranges — not for fetching record sets.
- **Impact:** Policies cannot build reports that combine external market data with internal portfolio data (e.g., "show my watchlist tickers with current prices" or "compare trade plan targets vs actual prices").
- **Proposed fix:** New `QueryStep` (`type_name="query"`) — a lightweight step that:
  1. Accepts `sql` (parameterized) + `output_key` in params
  2. Executes read-only SQL via `context.outputs["db_connection"]` (same sandbox as `StoreReportStep`)
  3. Returns records in the same `{output_key: [...]}` shape as `TransformStep` output
  4. Feeds directly into `TransformStep` (via `source_step_id`) or `SendStep` template context
  5. No external HTTP, no cache, no provider — pure local data extraction
- **Alternative considered:** Extending `FetchStep` with `provider: "local"` — rejected because it conflates external I/O (rate-limited, cached, provider-specific) with local SQL (instant, no auth, no envelope). Separate step type is cleaner.
- **MEU scope:** New MEU under Phase 9 (Scheduling). Depends on: existing `db_connection` injection (already wired in `main.py`), `StepContext.outputs` pattern, `RegisteredStep` auto-registration.


### [PIPE-DROPPDF] — Drop PDF output, replace with Markdown rendering for AI-friendly reports
- **Severity:** Medium (architectural decision)
- **Component:** core (`render_step.py`, `send_step.py`), infrastructure (`pdf_renderer.py`, `email_sender.py`, `models.py`)
- **Discovered:** 2026-04-21
- **Status:** Open — needs MEU scoping
- **Decision:** PDF output is dropped from the pipeline. Markdown is the replacement format — it's AI-agent consumable, MCP-friendly, lightweight, and doesn't require Playwright/Chromium.
- **Dependencies to remove:**
  1. `pdf_renderer.py` — entire file (`zorivest_infra.rendering.pdf_renderer`). Playwright dependency can be removed.
  2. `render_step.py` — `_render_pdf()` method, `output_format` enum values `"pdf"` and `"both"`, PDF failure handling
  3. `send_step.py` — `pdf_path` param, `pdf_path` in `_send_emails()` call, entire `_save_local()` method (copies PDF to disk)
  4. `email_sender.py` — `pdf_path` param, MIME PDF attachment logic (`MIMEApplication` block)
  5. `models.py` — `ReportModel.format` column default `"pdf"` → `"md"` or `"html"`
  6. `scheduling_repositories.py` — `format: str = "pdf"` default
- **Replacement approach:**
  - `RenderStep.output_format`: `"html"` (default, for email body) or `"markdown"` (for MCP/file/AI consumption)
  - Add `_render_markdown()` to RenderStep — converts report data to structured Markdown tables
  - `SendStep.local_file` channel: writes `.md` file instead of PDF
  - Email attachment: optional `.md` attachment instead of PDF
- **MEU scope:** Cleanup MEU under Phase 9. No new dependencies required — Markdown rendering is stdlib string formatting.


### [STUB-RETIRE] — stubs.py contains legacy stubs that should be retired progressively
- **Severity:** Low (technical debt)
- **Component:** api (`stubs.py`), tests
- **Discovered:** 2026-03-19
- **Status:** Phase 1+2 cleaned; Phase 3 tracked
- **Phase 2 resolved (MEU-PW1, 2026-04-12):** `StubMarketDataService` and `StubProviderConnectionService` deleted. `MarketQuote` import removed from stubs.py.
- **Phase 3 blocked on:** `StubAnalyticsService` (MEU-104–116), `StubReviewService` (MEU-110), `StubTaxService` (MEU-123–126). Each retires when its real service is implemented.
- **Roadmap:** [09a §Stub Retirement Roadmap](../docs/build-plan/09a-persistence-integration.md)


### [MCP-TOOLDISCOVERY] — MCP tool descriptions lack workflow context and examples for AI discoverability
- **Severity:** Medium
- **Component:** mcp-server
- **Discovered:** 2026-04-12
- **Status:** Open — requires full audit of all 9 toolsets
- **Details:** Server instructions and tool descriptions are too terse for AI agents to discover and correctly use multi-step workflows. Confirmed gaps in scheduling toolset: (1) server instructions say only "Automated task scheduling" — no mention of policy CRUD or pipeline execution, (2) `run_pipeline` description doesn't explain the approval prerequisite or error return shape, (3) `create_policy` has no example of the expected `policy_json` structure, (4) `pipeline://policies/schema` and `pipeline://step-types` MCP resources aren't referenced in any tool description, (5) no workflow guidance for the `create → approve → run` lifecycle. Similar gaps likely exist across `accounts`, `trade-analytics`, `trade-planning`, `market-data`, and other toolsets.
- **Sub-issue — Template registry not exposed to MCP layer (2026-04-20):**
  - `create_policy` input is `z.record(z.unknown())` — completely opaque. AI agents cannot discover available template names (`daily_quote_summary`, `generic_report`), their required Jinja2 variables (`quotes`, `records`), variable field shapes (`q.symbol`, `q.price`, etc.), or how steps must be wired for data to flow into the template.
  - No `pipeline://templates` resource exists. `EMAIL_TEMPLATES` dict lives only in Python infrastructure, invisible to the MCP layer.
  - **Pre-implementation research:** [mcp-template-discoverability-gap.md](scheduling/mcp-template-discoverability-gap.md) — proposed solutions include a `pipeline://templates` MCP resource, enriched `create_policy` description, and `GET /scheduling/templates` backend endpoint.
  - **Dependency:** MEU-PW12 must land first (defines final template variable contracts); TD1 then exposes them through MCP.
- **Next steps:** Full audit of all toolset descriptions against their actual API contracts. Improve server instructions with toolset workflow summaries. Add `policy_json` examples to `create_policy`. Reference MCP resources from tool descriptions. Add `pipeline://templates` resource exposing template registry with variable contracts. Ensure all tool descriptions include prerequisite state, return shape hints, and error conditions.



### [PIPE-URLBUILD] — MarketDataProviderAdapter._build_url() uses hardcoded URL patterns that don't match provider APIs
- **Severity:** High | **Component:** infrastructure (`market_data_adapter.py`) | **Discovered:** 2026-04-14 | **Status:** Open
- **Details:** Three sub-issues in `_build_url()` and `_do_fetch()`:
  1. **Criteria key mismatch:** Policy sends `tickers: ["AAPL", "MSFT"]` but `_build_url()` reads `criteria.get("symbol", "")` → empty string → URL like `…/quote?symbol=` → Yahoo hangs.
  2. **Missing provider headers:** `_do_fetch()` → `fetch_with_cache()` doesn't pass `headers_template` (UA, Referer) from registry → Yahoo returns 403/captcha.
  3. **Generic URL patterns:** Same `{base_url}/quote?symbol=` template for all 14 providers. Yahoo uses `symbols=` (plural, comma-sep), Finnhub uses single-symbol, Polygon uses snapshot endpoints.
- **Root cause:** `_build_url()` was a skeleton from MEU-PW2, never provider-specialized.
- **Fix:** Refactor to per-provider URL builders, pass `headers_template` into `fetch_with_cache()`, support `tickers` list → comma-joined `symbols=` param.


### [PIPE-NOCANCEL] — No mechanism to cancel a running pipeline run (API, GUI, or internal)
- **Severity:** High | **Component:** core, api, ui (Scheduling page) | **Discovered:** 2026-04-14 | **Status:** Open
- **Details:** Zero cancellation infrastructure exists. No cancel endpoint, no `asyncio.Task` tracking in `PipelineRunner`, no `CancelledError` handling, no GUI cancel button. Once a run starts, the only way to stop it is to kill the backend process. This directly causes zombie runs (see PIPE-ZOMBIE) — a stuck fetch step runs indefinitely with no user intervention path.
- **Research-backed fix approach** (sources: Prefect docs, Temporal docs, Azure Data Factory REST API, REST API design best practices, React AbortController patterns):
  1. **Backend — Task registry:** `PipelineRunner` must store `asyncio.Task` references in a `dict[str, asyncio.Task]` keyed by `run_id`. This enables `task.cancel()` which raises `CancelledError` inside the step's `await`.
  2. **Backend — Cancelling state:** Add `"cancelling"` to `PipelineStatus` enum as an intermediate status (Prefect pattern: run → cancelling → cancelled). Set on cancel request; runner checks this between steps and after `CancelledError`.
  3. **Backend — Cancel endpoint:** `POST /api/v1/scheduling/runs/{run_id}/cancel` (Azure Data Factory pattern). Idempotent — calling on already-cancelled/completed run returns 200. Sets status to `"cancelling"`, calls `task.cancel()`, waits up to grace period (default 30s per Prefect), then force-kills via `asyncio.Task.cancel()`.
  4. **Backend — Per-step token check:** Before each step execution in the runner loop, check `if run_status == "cancelling": break`. This provides cooperative cancellation at step boundaries even if `asyncio.Task.cancel()` can't interrupt a blocked I/O call (PIPE-ZOMBIE problem 2).
  5. **GUI — Cancel button:** Run detail page: red "Cancel Run" button visible when `status === "running"`. On click → confirmation dialog → `POST .../cancel` → button changes to "Cancelling…" (disabled) → poll/SSE until status reaches `"cancelled"` or `"failed"`. UX: don't show error toast on user-initiated cancel (AbortController pattern).
  6. **GUI — Run list indicator:** Show `🔴 Cancelling` badge in run history table during the intermediate state.








## Mitigated / Workaround Applied

### [MCP-TOOLCAP] — IDE tool limits render 68-tool flat registration non-viable
- **Severity:** Critical
- **Component:** mcp-server
- **Status:** Mitigated by Design — three-tier strategy (static ≤40 for Cursor, dynamic toolsets for VS Code, full for CLI/API)

### [MCP-ZODSTRIP] — `server.tool()` silently strips arguments with z.object()
- **Severity:** Critical
- **Component:** mcp-server
- **Status:** Open — upstream SDK bug (TS-SDK #1291, #1380, PR #1603)
- **Workaround:** Enforce raw shape convention. Startup assertion for non-empty `inputSchema.properties`.

### [MCP-AUTHRACE] — Token refresh race condition under concurrent tool execution
- **Severity:** Critical
- **Component:** mcp-server
- **Status:** Open — needs architectural mitigation
- **Workaround:** In-memory mutex for refresh; proactive JWT expiry check.

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
