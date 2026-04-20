# Data Flow Gap Analysis: External Fetch → Local Storage

> Companion to [Template Rendering Gap Analysis](file:///C:/Users/Mat/.gemini/antigravity/brain/4ada31bd-2bda-4889-97a1-6d6963e442d6/template_rendering_gap_analysis.md)

---

## 1. Architecture Overview

The data pipeline implements a **5-step sequential executor** pattern, orchestrated by `PipelineRunner`:

```
Policy Trigger (cron / manual / MCP)
       │
       ▼
SchedulingService.trigger_run()
       │ ── guardrails (approval check, rate limit)
       │ ── create run record (pending)
       ▼
PipelineRunner.run()
       │ ── inject 9 runtime deps into StepContext.outputs
       │ ── sequential step execution
       │
       ├─→ FetchStep (external HTTP → raw data)
       ├─→ TransformStep (field mapping → Pandera validation → DB write)
       ├─→ StoreReportStep (SQL queries → snapshot hash → report persist)
       ├─→ RenderStep (Jinja2 + Plotly → HTML/PDF)
       └─→ SendStep (SMTP email delivery)
```

---

## 2. Policy Trigger Flow

### 2.1 Entry Points

| Trigger Type | Source | Code Path |
|---|---|---|
| **Manual** | GUI "Run Now" button | `POST /api/v1/scheduling/policies/{id}/run` → `SchedulingService.trigger_run(trigger_type="manual")` |
| **Scheduled** | APScheduler cron job | `SchedulerService._execute_job()` → `SchedulingService.trigger_run(trigger_type="scheduled")` |
| **MCP** | AI agent `run_pipeline` tool | `POST /api/v1/scheduling/policies/{id}/run` → via MCP HTTP bridge |

### 2.2 Guardrail Gates (Pre-Execution)

Before any pipeline runs, `trigger_run()` enforces two guardrail checks:

1. **Approval Check** ([scheduling_service.py:289-294](file:///p:/zorivest/packages/core/src/zorivest_core/services/scheduling_service.py#L289-L294)):
   - `check_policy_approved(policy_id, content_hash)` — verifies `approved=True` AND `approved_hash == content_hash`
   - If the policy was modified after approval, the hash mismatch blocks execution

2. **Rate Limit** ([scheduling_service.py:297-299](file:///p:/zorivest/packages/core/src/zorivest_core/services/scheduling_service.py#L297-L299)):
   - `check_can_execute()` — enforces per-hour execution caps

### 2.3 Run Record Lifecycle

```
trigger_run()        → creates run record (status: "pending")
PipelineRunner.run() → updates to "running"
  ├─ all steps pass  → updates to "success"
  ├─ step fails      → updates to "failed" + error message
  └─ runner crashes  → SchedulingService catch block updates to "failed"
```

The **dual-write elimination** fix (MEU-PW5) ensures the run record is created exactly once — either by `SchedulingService` (pre-created `run_id`) or by `PipelineRunner` (fallback for backwards compat), never both.

---

## 3. Fetch Stage Deep Dive

### 3.1 FetchStep Execution Flow

```python
# packages/core/src/zorivest_core/pipeline_steps/fetch_step.py

FetchStep.execute(params, context)
  │
  ├─ 1. Resolve criteria (CriteriaResolver)
  │     ├─ Static criteria: {"symbol": "AAPL"}
  │     ├─ Relative dates: {"start": {"relative": "-30d"}}
  │     └─ DB query criteria: {"query": "SELECT ticker FROM watchlist"}
  │
  ├─ 2. Check cache (if use_cache=True)
  │     ├─ Compute entity_key from (provider, data_type, resolved_criteria)
  │     ├─ Look up FetchCacheModel via fetch_cache_repo
  │     ├─ If fresh → return cached content (status: "hit")
  │     └─ If stale → return stale metadata (etag, last_modified) for revalidation
  │
  ├─ 3. Market-hours TTL extension
  │     └─ For OHLCV data, if market is closed → TTL × 4 (weekends, after-hours)
  │
  ├─ 4. Fetch from provider
  │     ├─ Rate limiter: aiolimiter leaky-bucket per provider
  │     ├─ URL builder: registry dispatch (Yahoo, Polygon, Finnhub, Generic)
  │     ├─ HTTP cache revalidation: If-None-Match / If-Modified-Since headers
  │     ├─ 304 → return revalidated cached content
  │     └─ 200 → return fresh content + update cache
  │
  └─ 5. Return FetchResult
        ├─ content: raw bytes
        ├─ content_hash: SHA-256
        ├─ cache_status: "hit" | "miss" | "revalidated"
        └─ provider, data_type, entity_key metadata
```

### 3.2 MarketDataProviderAdapter

The concrete adapter ([market_data_adapter.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/market_data/market_data_adapter.py)) handles:

| Concern | Implementation | Status |
|---|---|---|
| URL construction | Registry-based `get_url_builder()` dispatch | ✅ Tested (22 unit tests) |
| Rate limiting | `execute_with_limits()` wrapping actual HTTP call | ✅ Tested |
| HTTP cache revalidation | `If-None-Match` / `If-Modified-Since` headers | ✅ Tested |
| Ticker resolution | `_resolve_tickers()` from criteria | ✅ Tested |
| Provider headers | Forward `headers_template` from provider config | ✅ Tested |

> [!WARNING]
> **[PIPE-URLBUILD]** — Known issue: URL builders for some providers may construct incorrect paths for certain `data_type` values. Tracked in `known-issues.md`.

---

## 4. Transform Stage Deep Dive

### 4.1 TransformStep Execution Flow

```python
TransformStep.execute(params, context)
  │
  ├─ 1. Retrieve source data from prior step output
  │     └─ Resolved via RefResolver: {"ref": "ctx.fetch_data.output.content"}
  │
  ├─ 2. Apply field mapping
  │     ├─ Map provider-specific field names → canonical schema
  │     ├─ e.g. {"c": "close", "h": "high", "l": "low"} for Polygon OHLCV
  │     └─ Handle missing fields with defaults
  │
  ├─ 3. Pandera validation gate
  │     ├─ Schema validation per data_type (ohlcv, quote, etc.)
  │     ├─ Records below quality threshold → quarantined
  │     └─ Quality ratio check: valid/total ≥ threshold (default 0.8)
  │
  ├─ 4. Write to database
  │     ├─ Table allowlist: only permitted tables/columns accepted
  │     ├─ Write disposition: "append" | "replace" | "upsert"
  │     └─ DbWriteAdapter handles actual SQL execution
  │
  └─ 5. Return result
        ├─ rows_written, rows_quarantined
        └─ quality_ratio
```

### 4.2 Security Controls

| Control | Detail |
|---|---|
| **Table allowlist** | Only tables in `WRITE_ALLOWLIST` can be targeted |
| **Column allowlist** | Only columns in the per-table allowlist are permitted |
| **Financial precision** | `parse_monetary()` + micros round-trip for decimal accuracy |

---

## 5. Store Report Stage

### 5.1 StoreReportStep Execution Flow

```python
StoreReportStep.execute(params, context)
  │
  ├─ 1. Execute sandboxed SQL queries
  │     ├─ SQLite set_authorizer → read-only (SELECT only)
  │     ├─ PRAGMA query_only enforcement
  │     └─ SQL blocklist as defense-in-depth
  │
  ├─ 2. Compute snapshot hash
  │     └─ SHA-256 of canonical JSON serialization of query results
  │
  └─ 3. Persist report via repository
        ├─ ReportModel with spec_json, snapshot_json, snapshot_hash
        └─ Triggers version archival on UPDATE
```

---

## 6. Runtime Dependency Injection

`PipelineRunner.__init__` accepts 12 parameters. Nine are runtime services injected into `StepContext.outputs`:

| Dep Key | Consumer Step | Injected In `main.py` | Status |
|---|---|---|---|
| `provider_adapter` | FetchStep | `MarketDataProviderAdapter` | ✅ Wired |
| `fetch_cache_repo` | FetchStep | `FetchCacheRepository` via UoW | ✅ Wired |
| `pipeline_state_repo` | FetchStep | `PipelineStateRepository` via UoW | ✅ Wired |
| `db_writer` | TransformStep | `DbWriteAdapter` | ✅ Wired |
| `db_connection` | StoreReportStep | SQLCipher raw connection | ✅ Wired |
| `report_repository` | StoreReportStep | `ReportRepository` via UoW | ✅ Wired |
| `template_engine` | RenderStep | Jinja2 `Environment` | ✅ Wired |
| `delivery_repository` | SendStep | `DeliveryRepository` via UoW | ✅ Wired |
| `smtp_config` | SendStep | `get_smtp_runtime_config()` | ✅ Wired |

> [!IMPORTANT]
> **Template engine is injected into the runner and available in context** — the disconnection identified in the [template rendering report](file:///C:/Users/Mat/.gemini/antigravity/brain/4ada31bd-2bda-4889-97a1-6d6963e442d6/template_rendering_gap_analysis.md) is at the **SendStep level**, not the runner level. The engine is available as `context.outputs["template_engine"]` but SendStep ignores it.

---

## 7. Test Coverage Assessment

### 7.1 Coverage Matrix

| Component | Unit Tests | Integration Tests | Total | Coverage Quality |
|---|---|---|---|---|
| **FetchStep** | 30 tests (`test_fetch_step.py`) | 5 tests (`test_pipeline_fetch_e2e.py`) | **35** | 🟢 Strong |
| **TransformStep** | 19 tests (`test_transform_step.py`) | — | **19** | 🟡 Good (unit-only) |
| **StoreReportStep** | 11 tests (`test_store_render_step.py`) | — | **11** | 🟡 Good (unit-only) |
| **RenderStep** | 7 tests (`test_store_render_step.py`) | — | **7** | 🟡 Adequate |
| **SendStep** | ~20 tests (`test_send_step.py`) | — | **~20** | 🟡 Good (unit-only) |
| **MarketDataAdapter** | 12 tests (`test_market_data_adapter.py`) | — | **12** | 🟢 Strong |
| **URL Builders** | 24 tests (`test_url_builders.py`) | — | **24** | 🟢 Strong |
| **Pipeline E2E** | — | 8 test classes (`test_pipeline_e2e.py`) | **8 classes** | 🟢 Strong |
| **Pipeline Wiring** | — | 1 test (`test_pipeline_wiring.py`) | **1** | 🟡 Minimal |

### 7.2 What's Tested Well

| Scenario | Evidence |
|---|---|
| FetchStep cache hit/miss/revalidation | 5 integration tests with mocked HTTP + cache repo |
| Rate limiter invocation during fetch | `test_PW2_AC7_rate_limiter_called_during_fetch` |
| Market-closed TTL extension | `test_PW2_AC4_*` (4 scenarios: weekend, after-hours, no-extension-for-news) |
| ETag / If-None-Match 304 revalidation | `test_PW2_AC7_etag_revalidation_304` |
| Transform field mapping + Pandera validation | `test_AC_T3` through `test_AC_T9` |
| Transform quality gate threshold | `test_AC_T7_quality_below/above_threshold` |
| SQL sandbox read-only enforcement | `test_AC_SR5/SR6/SR7_authorizer_*` |
| Pipeline lifecycle (create → run → finalize) | `TestPipelineExecution` class in E2E |
| Error modes (fail_pipeline, log_and_continue) | `TestErrorModes` class |
| Dry-run and skip conditions | `TestDryRunAndSkip` class |
| Cancellation infrastructure | `TestCancellation` class |
| Zombie recovery | `TestZombieRecovery` class |
| Dedup key computation (with fallback) | `test_send_step.py` (recently fixed) |

### 7.3 What's NOT Tested / Gaps

| Gap | Severity | Detail |
|---|---|---|
| **No end-to-end fetch→transform→store→render→send** | 🔴 High | Pipeline E2E tests use mock steps, never exercising the real FetchStep→TransformStep data handoff |
| **No transform integration with real data shapes** | 🟡 Medium | Transform tests use synthetic data dicts, never a real provider API response shape |
| **No cache upsert after successful fetch** | 🟡 Medium | FetchStep cache *reading* is tested, but *writing back* to cache after HTTP 200 is not integration-tested |
| **No provider credential forwarding test** | 🟡 Medium | API key injection via `headers_template` is tested via `test_AC8_adapter_forwards_provider_headers`, but not through the full FetchStep path |
| **No pipeline state (high-water mark) persistence test** | 🟡 Medium | `pipeline_state_repo` is injected but incremental cursor tracking is not integration-tested |
| **Template rendering in SendStep** | 🔴 High | Covered in [template rendering report](file:///C:/Users/Mat/.gemini/antigravity/brain/4ada31bd-2bda-4889-97a1-6d6963e442d6/template_rendering_gap_analysis.md) |
| **Real SMTP delivery** | 🟡 Medium | Only mocked; no mailhog/mailtrap integration test |
| **Scheduler cron job firing** | 🟡 Medium | APScheduler integration is tested at class level but not wired through `SchedulingService.trigger_run()` |

---

## 8. Planned Policy Use Cases (from Build Plan)

Based on [09-scheduling.md](file:///p:/zorivest/docs/build-plan/09-scheduling.md) and [09b-pipeline-hardening.md](file:///p:/zorivest/docs/build-plan/09b-pipeline-hardening.md):

### 8.1 Core Pipeline Steps (§9.4–§9.8)

| Use Case | Spec Section | Status |
|---|---|---|
| **Fetch OHLCV data** from external provider (Yahoo, Polygon, Finnhub) | §9.4a | ✅ Implemented + tested |
| **Fetch quote data** (current price, bid/ask) | §9.4a | ✅ Implemented |
| **Criteria resolution** — static, relative dates, DB query | §9.4b | ✅ Implemented + tested |
| **Rate limiting** per provider (leaky bucket via aiolimiter) | §9.4c | ✅ Implemented + tested |
| **HTTP cache revalidation** (ETag / Last-Modified / 304) | §9.4e | ✅ Implemented + tested |
| **Freshness TTL** with market-hours-aware extension (4x outside hours) | §9.4f | ✅ Implemented + tested |
| **Field mapping** from provider-specific → canonical schema | §9.5b | ✅ Implemented + tested |
| **Pandera validation gate** with quality threshold | §9.5c | ✅ Implemented + tested |
| **Write disposition** (append / replace / upsert) | §9.5d | ✅ Implemented + tested |
| **Financial precision** (micros round-trip for decimal accuracy) | §9.5e | ✅ Implemented + tested |
| **Sandboxed SQL queries** for report generation | §9.6c | ✅ Implemented + tested |
| **Report snapshot hashing** for deduplication | §9.6a | ✅ Implemented + tested |
| **Jinja2 HTML rendering** with financial filters | §9.7b | ✅ Implemented + tested |
| **Plotly chart rendering** (candlestick, scatter) | §9.7c | ✅ Implemented + tested |
| **PDF generation** via Playwright headless Chromium | §9.7d | ✅ Implemented + tested |
| **Async email delivery** via aiosmtplib | §9.8b | ✅ Implemented (SMTP wiring fixed) |
| **SHA-256 dedup** for idempotent email delivery | §9.8a | ✅ Implemented (fallback fixed) |
| **Delivery tracking** per report/recipient | §9.8c | ✅ Implemented |

### 8.2 Policy Lifecycle (§9.1, §9.9, §9.10)

| Use Case | Spec Section | Status |
|---|---|---|
| **Policy creation** via REST/MCP with validation | §9.1c, §9.10 | ✅ Implemented |
| **Policy validation** (schema, refs, cron, SQL blocklist) | §9.1g | ✅ Implemented + tested |
| **Step type registry** (__init_subclass__ auto-registration) | §9.1f | ✅ Implemented + tested |
| **Human-in-the-loop approval** before first execution | §9.9c | ✅ Implemented + tested |
| **Approval reset** on policy modification (hash mismatch) | §9.9c | ✅ Implemented + tested |
| **Rate limits** on policy creation and execution | §9.9b | ✅ Implemented + tested |
| **Content hash versioning** for change detection | §9.1g | ✅ Implemented |
| **Schedule patching** (cron/enabled/timezone) without full round-trip | §9.10 | ✅ Implemented |

### 8.3 Pipeline Infrastructure (§9.3, §9B)

| Use Case | Spec Section | Status |
|---|---|---|
| **Sequential async execution** with retry + backoff | §9.3a | ✅ Implemented + tested |
| **RefResolver** for cross-step data references | §9.3b | ✅ Implemented + tested |
| **ConditionEvaluator** (10 operators for skip_if) | §9.3c | ✅ Implemented + tested |
| **APScheduler integration** (cron jobs, misfire grace) | §9.3d | ✅ Implemented |
| **Zombie detection** (orphaned "running" runs → FAILED on startup) | §9.3e, §9B.3 | ✅ Implemented + tested |
| **Resume from step** (re-run from failed step ID) | §9.3a | ✅ Implemented |
| **Dry-run mode** (skip side-effect steps) | §9.3a | ✅ Implemented + tested |
| **Cooperative cancellation** (CancelledError propagation) | §9B.5 | ✅ Implemented + tested |
| **Charmap encoding fix** (UTF-8 structlog, bytes-safe JSON) | §9B.2 | ✅ Implemented + tested |
| **Dual-write elimination** (single run record per execution) | §9B.3 | ✅ Implemented + tested |
| **Provider URL builder registry** (Yahoo, Polygon, Finnhub, Generic) | §9B.4 | ✅ Implemented + tested |
| **Pipeline end-to-end test harness** | §9B.6 | ✅ Implemented |

### 8.4 REST API Endpoints (§9.10)

| Endpoint | Method | Status |
|---|---|---|
| `/policies` | POST (create) | ✅ |
| `/policies` | GET (list) | ✅ |
| `/policies/{id}` | GET (detail) | ✅ |
| `/policies/{id}` | PUT (update) | ✅ |
| `/policies/{id}` | DELETE | ✅ |
| `/policies/{id}/approve` | POST | ✅ |
| `/policies/{id}/run` | POST (trigger) | ✅ |
| `/policies/{id}/runs` | GET (history) | ✅ |
| `/policies/{id}/schedule` | PATCH | ✅ |
| `/runs` | GET (recent) | ✅ |
| `/runs/{id}` | GET (detail) | ✅ |
| `/runs/{id}/steps` | GET (step detail) | ✅ |
| `/runs/{id}/cancel` | POST | ✅ |
| `/scheduler/status` | GET | ✅ |
| `/schema/step-types` | GET | ✅ |
| `/schema/policy` | GET | ✅ |

### 8.5 Planned but NOT Yet Implemented

| Use Case | Spec Section | Status |
|---|---|---|
| **Sleep/wake IPC handler** (trigger APScheduler wakeup on resume from sleep) | §9.3f | ⬜ Planned (service daemon dependency) |
| **Incremental fetch** (pipeline_state high-water mark cursors) | §9.4b | ⬜ Model exists, cursor tracking not exercised |
| **MCP tools** (6 tools + 2 resources from TypeScript MCP server) | §9.11 | ⬜ Planned (TypeScript not scaffolded) |
| **GUI scheduling page** (policy approval flow, step-level detail panel) | §9.12 | ✅ Partially implemented (MEU-72 pending Codex) |
| **Template rendering in SendStep** | §9.8a | 🔴 Disconnected (see template report) |

---

## 9. Summary & Recommendations

### Architecture Strengths
- **Dependency injection** via `StepContext.outputs` is clean and testable
- **Security defense-in-depth** (SQL sandbox + allowlist + blocklist) is layered correctly
- **Cache revalidation** with ETag/Last-Modified is production-grade
- **Market-hours TTL extension** is well-designed for cost reduction

### Priority Fixes

| # | Issue | Impact | Effort |
|---|---|---|---|
| 1 | **Template rendering in SendStep** | Emails are plain text instead of styled HTML | Low (wiring fix) |
| 2 | **End-to-end integration test** (fetch→transform→store with real data shapes) | Confidence gap in data handoff | Medium |
| 3 | **Cache upsert integration test** | Verify write-back after HTTP 200 works correctly | Low |
| 4 | **Pipeline state cursor tracking** | Incremental fetch feature is modeled but unused | Medium |
