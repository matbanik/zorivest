# Known Issues — Zorivest

> Track bugs, limitations, and workarounds here.
> Resolved issues are archived in [known-issues-archive.md](known-issues-archive.md).

## Active Issues

### [SCHED-TZDISPLAY] — Policy timestamps display in UTC instead of user's configured timezone
- **Severity:** Medium | **Component:** ui (Scheduling page) | **Discovered:** 2026-04-13 | **Status:** Open
- **Details:** Policy detail and run-history timestamps render in UTC even when user has `America/New_York` configured. Backend stores UTC (correct). Fix is UI-only: create shared `formatTimestamp()` utility using `date-fns-tz` `formatInTimeZone()` with the IANA timezone from Settings.


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


### [TEMPLATE-RENDER] — SendStep ignores template engine and EMAIL_TEMPLATES registry; emails are plain text
- **Severity:** High | **Component:** core (`send_step.py`), infrastructure (`email_templates.py`, `template_engine.py`) | **Discovered:** 2026-04-20 | **Status:** Open
- **Analysis:** [template_rendering_gap_analysis.md](scheduling/template_rendering_gap_analysis.md)
- **Details:** Three-layer disconnection:
  1. **Layer 1 — EMAIL_TEMPLATES registry** (`email_templates.py`): Contains 6 styled Jinja2 templates keyed by name (e.g. `"portfolio_summary"`, `"alert_notification"`). Registry is never imported or queried by any consumer.
  2. **Layer 2 — template_engine** (`template_engine.py`): Jinja2 `Environment` with financial filters (`format_currency`, `format_percent`). Injected into `PipelineRunner → StepContext.outputs["template_engine"]` but `SendStep` never reads it.
  3. **Layer 3 — body_template resolution**: `SendStep._send_emails()` uses `params.get("body_template", "")` as a **raw literal string** in the email body, not as a template key for lookup + rendering.
- **Impact:** All pipeline emails are delivered with the template name as the body text (e.g. body = `"portfolio_summary"`) instead of rendered HTML.
- **Fix scope:** (1) `SendStep._send_emails()` must look up `body_template` in `EMAIL_TEMPLATES`, (2) render via `context.outputs["template_engine"]` with pipeline context data, (3) set email content type to `text/html`. Estimated: ~30 LoC change + 4-6 TDD tests.
- **MEU candidate:** Yes — small, well-scoped, TDD-friendly.


### [PIPE-E2E-CHAIN] — No integration test exercises real FetchStep→TransformStep→StoreReportStep data handoff
- **Severity:** High | **Component:** tests | **Discovered:** 2026-04-20 | **Status:** Open
- **Analysis:** [data_flow_gap_analysis.md](scheduling/data_flow_gap_analysis.md) §7.3
- **Details:** Existing pipeline E2E tests (`test_pipeline_e2e.py`) use **mock steps** — they validate the runner's orchestration logic (lifecycle, error modes, cancellation) but never exercise the actual `FetchStep → TransformStep` data handoff with real provider response shapes. The concrete path — provider JSON → field mapping → Pandera validation → DB write — is only tested at the unit level per-step, never as a chain.
- **Impact:** Field mapping mismatches, Pandera schema drift, or DbWriteAdapter serialization bugs would not be caught until live execution.
- **Fix scope:** Add 2-3 integration tests using `FetchStep` with mocked HTTP (real adapter) → `TransformStep` with real field mapping + Pandera → `StoreReportStep` with real SQL sandbox. Use in-memory SQLite.
- **MEU candidate:** Yes — extends MEU-PW8 test harness.


### [PIPE-CACHEUPSERT] — Cache write-back after HTTP 200 fetch is not integration-tested
- **Severity:** Medium | **Component:** tests, infrastructure (`fetch_step.py`, `market_data_adapter.py`) | **Discovered:** 2026-04-20 | **Status:** Open
- **Analysis:** [data_flow_gap_analysis.md](scheduling/data_flow_gap_analysis.md) §7.3
- **Details:** `FetchStep._fetch_from_provider()` calls `fetch_cache_repo.upsert()` after a successful HTTP 200 response. The cache **read** path (hit, miss, stale/revalidated) is well-tested (5 integration tests), but the **write-back** path — confirm that after a 200, a new cache entry exists with correct `payload_json`, `etag`, `content_hash`, `ttl_seconds`, and `fetched_at` — is not verified in any integration test.
- **Fix scope:** Add 1-2 assertions to the existing `test_PW2_AC7_fetch_step_happy_path_ohlcv` or a new focused test.
- **MEU candidate:** No — small enough to be a patch within an existing MEU.


### [PIPE-CURSORS] — Pipeline state cursor tracking is modeled but unused
- **Severity:** Medium | **Component:** core (`fetch_step.py`), infrastructure (`PipelineStateModel`) | **Discovered:** 2026-04-20 | **Status:** Open
- **Analysis:** [data_flow_gap_analysis.md](scheduling/data_flow_gap_analysis.md) §8.5
- **Details:** `PipelineStateModel` exists with `last_cursor` and `last_hash` columns for incremental fetch high-water marks. `pipeline_state_repo` is injected into `PipelineRunner`. However, `FetchStep` never reads or writes cursor state — each fetch is a full pull regardless of prior runs. The `CriteriaResolver` has an `incremental` mode that references `pipeline_state_repo`, but it is not exercised by any test.
- **Impact:** Repeated pipeline runs re-fetch all data instead of delta-only, increasing API costs and latency.
- **Fix scope:** Implement cursor read/write in `FetchStep.execute()`, add `CriteriaResolver.resolve_incremental()` tests.
- **MEU candidate:** Yes — medium scope, requires FIC + TDD cycle.


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
