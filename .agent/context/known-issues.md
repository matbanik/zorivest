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


### [MCP-TOOLDISCOVERY] — MCP tool descriptions lack workflow context and examples for AI discoverability
- **Severity:** Medium
- **Component:** mcp-server
- **Discovered:** 2026-04-12
- **Status:** Open — requires full audit of all 9 toolsets
- **Details:** Server instructions and tool descriptions are too terse for AI agents to discover and correctly use multi-step workflows. Confirmed gaps in scheduling toolset: (1) server instructions say only "Automated task scheduling" — no mention of policy CRUD or pipeline execution, (2) `run_pipeline` description doesn't explain the approval prerequisite or error return shape, (3) `create_policy` has no example of the expected `policy_json` structure, (4) `pipeline://policies/schema` and `pipeline://step-types` MCP resources aren't referenced in any tool description, (5) no workflow guidance for the `create → approve → run` lifecycle. Similar gaps likely exist across `accounts`, `trade-analytics`, `trade-planning`, `market-data`, and other toolsets.
- **Next steps:** Full audit of all toolset descriptions against their actual API contracts. Improve server instructions with toolset workflow summaries. Add `policy_json` examples to `create_policy`. Reference MCP resources from tool descriptions. Ensure all tool descriptions include prerequisite state, return shape hints, and error conditions.



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





### [PIPE-E2E-CHAIN] — No integration test exercises real FetchStep→TransformStep→StoreReportStep data handoff
- **Severity:** High | **Component:** tests | **Discovered:** 2026-04-20 | **Status:** Open
- **Analysis:** [data_flow_gap_analysis.md](scheduling/data_flow_gap_analysis.md) §7.3, [pipeline-dataflow-deficiency-report.md](scheduling/pipeline-dataflow-deficiency-report.md)
- **Details:** Existing pipeline E2E tests (`test_pipeline_e2e.py`) use **mock steps** — they validate the runner's orchestration logic (lifecycle, error modes, cancellation) but never exercise the actual `FetchStep → TransformStep` data handoff with real provider response shapes. The concrete path — provider JSON → field mapping → Pandera validation → DB write — is only tested at the unit level per-step, never as a chain.
- **Impact:** This gap directly caused 6 undetected data-flow bugs (PIPE-STEPKEY, PIPE-TMPLVAR, PIPE-RAWBLOB, PIPE-PROVNORM, PIPE-QUOTEFIELD, PIPE-SILENTPASS) — all discovered 2026-04-20 when user tested live pipeline.
- **Fix scope:** Add 2-3 integration tests using `FetchStep` with mocked HTTP (real adapter) → `TransformStep` with real field mapping + Pandera → `StoreReportStep` with real SQL sandbox. Use in-memory SQLite.
- **MEU candidate:** Yes — extends MEU-PW8 test harness.


### [PIPE-CACHEUPSERT] — Cache write-back after HTTP 200 fetch is not integration-tested
- **Severity:** Medium | **Component:** tests, infrastructure (`fetch_step.py`, `market_data_adapter.py`) | **Discovered:** 2026-04-20 | **Status:** Open
- **Analysis:** [data_flow_gap_analysis.md](scheduling/data_flow_gap_analysis.md) §7.3
- **Details:** `FetchStep._fetch_from_provider()` calls `fetch_cache_repo.upsert()` after a successful HTTP 200 response. The cache **read** path (hit, miss, stale/revalidated) is well-tested (5 integration tests), but the **write-back** path — confirm that after a 200, a new cache entry exists with correct `payload_json`, `etag`, `content_hash`, `ttl_seconds`, and `fetched_at` — is not verified in any integration test.
- **Fix scope:** Add 1-2 assertions to the existing `test_PW2_AC7_fetch_step_happy_path_ohlcv` or a new focused test.
- **MEU candidate:** No — small enough to be a patch within an existing MEU.




### [PIPE-STEPKEY] — TransformStep hardcodes `"fetch_result"` key instead of resolving actual step output
- **Severity:** Critical | **Component:** core (`transform_step.py`) | **Discovered:** 2026-04-20 | **Status:** Open
- **Analysis:** [pipeline-dataflow-deficiency-report.md](scheduling/pipeline-dataflow-deficiency-report.md) §3.1
- **Details:** `TransformStep.execute()` reads `context.outputs.get("fetch_result", {})` but `PipelineRunner` stores outputs under the step's ID (e.g., `"fetch_yahoo_quotes"`). Key never exists → 0 records → silent data loss. `_apply_mapping()` has the same hardcoded key. Unit tests inject `"fetch_result"` directly, matching the hardcode but not the real wiring.
- **Impact:** **All TransformStep executions in real pipelines receive zero records.** This is the root cause of empty email reports.
- **Fix:** Add `source_step_id` param to TransformStep.Params; policy explicitly declares which step's output to read.

### [PIPE-TMPLVAR] — Email template expects `quotes` variable but no pipeline step produces it
- **Severity:** Critical | **Component:** core (`send_step.py`), infrastructure (`email_templates.py`) | **Discovered:** 2026-04-20 | **Status:** Open
- **Analysis:** [pipeline-dataflow-deficiency-report.md](scheduling/pipeline-dataflow-deficiency-report.md) §3.2
- **Details:** `daily_quote_summary` template checks `{% if quotes %}` to render the table. `_resolve_body()` merges `context.outputs` into template context, producing keys like `fetch_yahoo_quotes`, `transform_quotes`, `provider_adapter` — never `quotes`. Template always falls through to "No quote data available."
- **Impact:** Even with all upstream fixes, the template would still render empty without a mechanism to wire parsed records into a `quotes` template variable.
- **Fix:** Either add a dedicated template-context preparation step, or have TransformStep output include a well-known `quotes` key when `data_type == "quote"`.

### [PIPE-RAWBLOB] — No response envelope extraction for provider API responses
- **Severity:** High | **Component:** core (`fetch_step.py`), infrastructure (`http_cache.py`) | **Discovered:** 2026-04-20 | **Status:** Open
- **Analysis:** [pipeline-dataflow-deficiency-report.md](scheduling/pipeline-dataflow-deficiency-report.md) §3.3
- **Details:** Yahoo `/v6/finance/quote` returns `{"quoteResponse": {"result": [...]}}`. `fetch_with_cache()` stores `response.content` as raw bytes (entire HTTP body). FetchStep passes raw bytes to output. TransformStep would `json.loads()` into the envelope dict, not the records array. No component extracts `data["quoteResponse"]["result"]` to yield the actual quote list. Each provider has a different envelope shape.
- **Fix:** Add per-provider response extractor (method on URL builder or separate registry) that unwraps the API envelope to yield the records array.

### [PIPE-PROVNORM] — Provider name mismatch between provider registry and field mappings
- **Severity:** Medium | **Component:** infrastructure (`field_mappings.py`, `provider_registry.py`) | **Discovered:** 2026-04-20 | **Status:** Open
- **Analysis:** [pipeline-dataflow-deficiency-report.md](scheduling/pipeline-dataflow-deficiency-report.md) §3.4
- **Details:** Provider registry uses display names (`"Yahoo Finance"`, `"Polygon.io"`). Field mappings use short keys (`"yahoo"`, `"polygon"`, `"ibkr"`). `apply_field_mapping(provider="Yahoo Finance", data_type="quote")` looks up `("Yahoo Finance", "quote")` → no match → all fields go to `_extra`, canonical mapping never applied. Silent fallthrough.
- **Fix:** Add slug normalization at field mapping lookup, or standardize on one naming convention.

### [PIPE-QUOTEFIELD] — Quote template fields don't match canonical schema or field mappings
- **Severity:** Medium | **Component:** infrastructure (`email_templates.py`, `field_mappings.py`), core (`validation_gate.py`) | **Discovered:** 2026-04-20 | **Status:** Open
- **Analysis:** [pipeline-dataflow-deficiency-report.md](scheduling/pipeline-dataflow-deficiency-report.md) §3.5
- **Details:** Template expects `q.symbol`, `q.price`, `q.change`, `q.change_pct`, `q.volume`. Field mappings produce `bid`, `ask`, `last`, `volume` (no `price`, `change`, `change_pct`). Pandera validates `ticker`, `last`, `timestamp` (no `symbol`, `price`). Yahoo sends `regularMarketChange`/`regularMarketChangePercent` but these are unmapped. Three-way misalignment: template ↔ mapping ↔ schema.
- **Fix:** Extend Yahoo quote field mappings with `change`, `change_pct`, `symbol` pass-through. Align template to match either canonical or extended fields.

### [PIPE-SILENTPASS] — TransformStep returns SUCCESS with 0 records, masking upstream data loss
- **Severity:** Medium | **Component:** core (`transform_step.py`) | **Discovered:** 2026-04-20 | **Status:** Open
- **Analysis:** [pipeline-dataflow-deficiency-report.md](scheduling/pipeline-dataflow-deficiency-report.md) §3.6
- **Details:** When TransformStep receives 0 records (due to PIPE-STEPKEY or empty fetch), it returns `PipelineStatus.SUCCESS` with `records_written: 0` and `quality_ratio: 0.0`. Pipeline continues normally. User sees "success" with no warning. The `quality_ratio: 0.0` data is buried in step output, never surfaced to UI or logs.
- **Fix:** Return FAILED or WARNING when records == 0 (unless explicitly configured to allow empty). Emit `structlog.warning("transform_zero_records")`. Consider `min_records` param with default 1.


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
