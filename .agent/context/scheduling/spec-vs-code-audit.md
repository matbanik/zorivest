# 09-scheduling.md Spec vs Code Audit

Verified audit of every spec section against the actual codebase. Each finding cites the source file and line.

---

## Legend

| Status | Meaning |
|--------|---------|
| ✅ **PRESENT** | Feature exists and matches spec intent |
| ⚠️ **DEVIATED** | Feature exists but differs from spec |
| ❌ **MISSING** | Feature specified but not implemented |
| 🔧 **STUB** | File/function exists but body is placeholder |

---

## §9.1: Domain Model Layer

### ✅ Enums (§9.1a–b)
- `PipelineStatus` — [enums.py:180](file:///p:/zorivest/packages/core/src/zorivest_core/domain/enums.py#L180)
- `StepErrorMode` — [enums.py:191](file:///p:/zorivest/packages/core/src/zorivest_core/domain/enums.py#L191)

### ✅ Pydantic Models (§9.1c–d)
All present in [pipeline.py](file:///p:/zorivest/packages/core/src/zorivest_core/domain/pipeline.py):
- `RefValue` (L33), `RetryConfig` (L43), `SkipConditionOperator` (L51), `SkipCondition` (L66)
- `PolicyStep` (L79), `TriggerConfig` (L107), `PolicyMetadata` (L122), `PolicyDocument` (L131)
- `StepContext` (L160), `StepResult` (L181), `FetchResult` (L198)

### ⚠️ StepBase Protocol (§9.1e)
- **Spec location:** `pipeline.py`
- **Actual location:** [step_registry.py:25](file:///p:/zorivest/packages/core/src/zorivest_core/domain/step_registry.py#L25)
- **Assessment:** Acceptable cohesion improvement. Protocol + registry colocated.

### ✅ Step Registry (§9.1f)
- `STEP_REGISTRY`, `RegisteredStep`, `get_step`, `has_step`, `list_steps`, `get_all_steps` — [step_registry.py](file:///p:/zorivest/packages/core/src/zorivest_core/domain/step_registry.py)

### ❌ FRESHNESS_TTL / is_market_closed (§9.4f)
- **Spec:** `FRESHNESS_TTL` dict and `is_market_closed()` function in `pipeline.py`
- **Code:** Not present in any file. `rg` confirms zero matches across entire `packages/` tree.
- **Impact:** Fetch step cannot enforce market-hours-aware cache staleness thresholds.

---

## §9.2: Policy Validator

### ✅ PolicyValidator
- [policy_validator.py](file:///p:/zorivest/packages/core/src/zorivest_core/domain/policy_validator.py) — 8,965 bytes
- Includes `compute_content_hash()` (used by PipelineRunner L90)

---

## §9.3: Pipeline Runner

### ✅ PipelineRunner Core (§9.3a)
- [pipeline_runner.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/pipeline_runner.py) — 431 lines
- Sequential async execution ✅, ref resolution ✅, skip conditions ✅, retry with backoff+jitter ✅, dry-run ✅, timeout per step ✅

### ✅ Resume from Failure (§9.3b)
- `resume_from` parameter on `run()` method (L70)
- Loads prior outputs via `_load_prior_output()` (L358)

### ✅ Compensate (§9.3c)
- `compensate()` method on both `StepBase` Protocol (L46) and `RegisteredStep` base class (L96)

### ⚠️ Constructor Missing `provider_adapter` ([SCHED-PIPELINE-WIRING])
- **Spec intent:** PipelineRunner should inject `provider_adapter` into `StepContext.outputs`
- **Code:** Constructor (L50-63) accepts only `uow`, `ref_resolver`, `condition_evaluator`, `delivery_repository`, `smtp_config` — **no `provider_adapter`**
- **Impact:** `FetchStep._fetch_from_provider()` requires `provider_adapter` in context (L117) but nothing injects it
- **Status:** Tracked as `[SCHED-PIPELINE-WIRING]` in known-issues.md

### ✅ APScheduler Integration (§9.3d)
- [scheduler_service.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/scheduler_service.py) — 247 lines
- Wraps `AsyncIOScheduler` with `SQLAlchemyJobStore` ✅
- Picklable module-level callback (L27) ✅
- `schedule_policy`, `unschedule_policy`, `pause_policy`, `resume_policy`, `get_next_run` ✅

### ✅ Zombie Recovery (§9.3e)
- `recover_zombies()` at [pipeline_runner.py:380](file:///p:/zorivest/packages/core/src/zorivest_core/services/pipeline_runner.py#L380)
- Scans for orphaned RUNNING runs, marks FAILED, logs severity based on `side_effects`

### ✅ Power Event / Sleep-Wake (§9.3f — API side)
- [scheduler.py](file:///p:/zorivest/packages/api/src/zorivest_api/routes/scheduler.py) — `POST /api/v1/scheduler/power-event`
- `PowerEventRequest` model with `Literal["suspend", "resume"]` ✅

### ❌ Power Event (§9.3f — Electron side)
- **Spec:** `electron.powerMonitor.on('resume', ...)` sends POST to API
- **Code:** No `powerMonitor` usage found in `ui/` — `rg "powerMonitor" ui/` returns 0 matches
- **Impact:** OS sleep/wake events not forwarded to scheduler. API endpoint exists but has no caller.
- **Note:** This belongs to GUI-layer MEUs (not yet fully wired).

---

## §9.4: Fetch Stage

### ✅ FetchStep Core (§9.4a)
- [fetch_step.py](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/fetch_step.py) — 133 lines
- `type_name = "fetch"`, `side_effects = False`, `Params` model ✅
- Calls `_fetch_from_provider()` with `provider_adapter` from context ✅

### ✅ Criteria Resolver (§9.4b)
- [criteria_resolver.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/criteria_resolver.py) — 5,078 bytes

### ✅ Rate Limiter (§9.4c)
- [pipeline_rate_limiter.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/market_data/pipeline_rate_limiter.py) — `PipelineRateLimiter` class ✅

### ⚠️ FetchResult Envelope (§9.4d)
- **Spec:** `@dataclass FetchResult` with `raw_payload`, `content_type`, `warnings`, `fetched_at`
- **Code:** `FetchResult` at [pipeline.py:198](file:///p:/zorivest/packages/core/src/zorivest_core/domain/pipeline.py#L198) — uses `content: bytes` instead of `raw_payload: dict`, no `content_type`, no `warnings`, no `fetched_at`
- **Impact:** Reduced provenance metadata on fetch outputs

### ✅ HTTP Cache Revalidation (§9.4e)
- [http_cache.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/market_data/http_cache.py) — `fetch_with_cache()` with ETag/If-Modified-Since ✅

### 🔧 FetchStep Cache Check (§9.4a internal)
- `_check_cache()` at [fetch_step.py:128](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/fetch_step.py#L128) — **returns `None` (stub)**
- Not wired to `FetchCacheModel` or `http_cache.py`

---

## §9.5: Transform Stage

### ✅ TransformStep (§9.5a)
- [transform_step.py](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/transform_step.py) — 190 lines
- Pandera validation via `validate_dataframe()` ✅
- Quality threshold check ✅
- Field mapping via `apply_field_mapping()` ✅

### ⚠️ Params Model (§9.5a)
- **Spec:** `mapping: dict`, `validation_rules: list[dict]`
- **Code:** `mapping: str = "auto"`, `validation_rules: str = "ohlcv"`
- **Assessment:** Simplified — uses string keys into infra mapping/schema registries instead of inline dicts. Functionally equivalent but less flexible.

### ✅ Pandera Validation (§9.5c)
- [validation_gate.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/validation_gate.py) — `OHLCV_SCHEMA`, `validate_dataframe()`, `check_quality()` ✅

### ✅ Write Dispositions (§9.5d)
- [write_dispositions.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/repositories/write_dispositions.py) — 168 lines
- `write_append()`, `write_replace()`, `write_merge()` ✅
- Table allowlist + column validation ✅

### ✅ Field Mappings (§9.5b)
- [field_mappings.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/market_data/field_mappings.py) — 2,141 bytes ✅

---

## §9.6: Store Report Stage

### ✅ StoreReportStep (§9.6a)
- [store_report_step.py](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/store_report_step.py) — 5,334 bytes

### ✅ SQL Sandbox (§9.6c)
- [sql_sandbox.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/security/sql_sandbox.py) — 60 lines
- `report_authorizer()` + `create_sandboxed_connection()` ✅
- Default-deny authorizer (only SELECT/READ/FUNCTION) ✅
- `PRAGMA query_only = ON` ✅

### ⚠️ SQLCipher Integration (§9.6c)
- **Spec:** Sandboxed connection should use SQLCipher key
- **Code:** Uses plain `sqlite3.connect()` — no `PRAGMA key` call
- **Impact:** In production with SQLCipher, sandboxed connections won't decrypt the DB. Needs `key` parameter injection.

---

## §9.7: Render Stage

### ✅ RenderStep (§9.7a)
- [render_step.py](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/render_step.py) — 5,187 bytes

### ✅ Rendering Infrastructure
- [chart_renderer.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/rendering/chart_renderer.py) — Plotly ✅
- [pdf_renderer.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/rendering/pdf_renderer.py) — Playwright PDF ✅
- [template_engine.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/rendering/template_engine.py) — Jinja2 ✅

---

## §9.8: Send Stage

### ✅ SendStep (§9.8a)
- [send_step.py](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/send_step.py) — 7,345 bytes

### ✅ Email Infrastructure
- [email_sender.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/email/email_sender.py) — aiosmtplib ✅
- [delivery_tracker.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/email/delivery_tracker.py) — idempotent dedup ✅

### ⚠️ SMTP Config Key Mismatch ([SCHED-PIPELINE-WIRING])
- **Spec intent:** SendStep gets `smtp_config` with `host`, `sender` keys
- **Code:** `EmailProviderService.get_config()` returns `smtp_host`, `from_email` keys — mismatch
- **Impact:** SendStep would receive wrong key names at runtime
- **Status:** Tracked as `[SCHED-PIPELINE-WIRING]` — needs `get_smtp_runtime_config()` bridge

---

## §9.9: SQLAlchemy Models

### ✅ All 9 Models Present
In [models.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/models.py):

| Model | Line | Spec |
|-------|------|------|
| `PolicyModel` | 434 | ✅ |
| `PipelineRunModel` | 460 | ✅ |
| `PipelineStepModel` | 485 | ✅ |
| `PipelineStateModel` | 507 | ✅ |
| `ReportModel` | 532 | ✅ |
| `ReportVersionModel` | 556 | ✅ |
| `ReportDeliveryModel` | 572 | ✅ |
| `FetchCacheModel` | 589 | ✅ |
| `AuditLogModel` | 609 | ✅ |

### ✅ Temporal Triggers (§9.9b)
- `reports_version_on_update` — models.py:639 ✅
- `audit_no_update` — models.py:661 ✅
- `audit_no_delete` — models.py:670 ✅

### ✅ Scheduling Repositories
- [scheduling_repositories.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py) — 12,538 bytes

---

## §9.10: REST API Endpoints

### ✅ All 16 Endpoints Present
In [scheduling.py](file:///p:/zorivest/packages/api/src/zorivest_api/routes/scheduling.py) (324 lines):

| Method | Path | Handler | Line |
|--------|------|---------|------|
| POST | `/policies` | `create_policy` | 129 |
| GET | `/policies` | `list_policies` | 141 |
| GET | `/policies/schema` | `get_policy_schema` | 151 |
| GET | `/policies/{id}` | `get_policy` | 159 |
| PUT | `/policies/{id}` | `update_policy` | 171 |
| DELETE | `/policies/{id}` | `delete_policy` | 184 |
| POST | `/policies/{id}/approve` | `approve_policy` | 193 |
| POST | `/policies/{id}/run` | `trigger_pipeline` | 208 |
| GET | `/policies/{id}/runs` | `get_policy_runs` | 226 |
| GET | `/runs` | `list_runs` | 236 |
| GET | `/runs/{id}` | `get_run_detail` | 245 |
| GET | `/runs/{id}/steps` | `get_run_steps` | 257 |
| GET | `/scheduler/status` | `get_scheduler_status` | 269 |
| GET | `/step-types` | `get_step_types` | 280 |
| PATCH | `/policies/{id}/schedule` | `patch_policy_schedule` | 302 |

Plus in [scheduler.py](file:///p:/zorivest/packages/api/src/zorivest_api/routes/scheduler.py):
| POST | `/scheduler/power-event` | `receive_power_event` | 42 |

**Total: 16 endpoints** ✅

---

## §9.11: MCP Tools

### ✅ All 6 Tools + 2 Resources
In [scheduling-tools.ts](file:///p:/zorivest/mcp-server/src/tools/scheduling-tools.ts) (459 lines):

| Tool | Description |
|------|-------------|
| `create_policy` | Create/validate policy JSON |
| `list_policies` | List policies with status |
| `run_pipeline` | Trigger manual run |
| `preview_report` | Dry-run pipeline |
| `update_policy_schedule` | Patch schedule |
| `get_pipeline_history` | Run history |

Resources: `pipeline://policies/schema`, `pipeline://step-types` ✅

### ⚠️ Registration Pattern
- **Spec:** `server.tool(...)` (vanilla MCP SDK)
- **Code:** `server.registerTool(...)` with annotation metadata, toolset grouping, metrics, and guard middleware
- **Assessment:** Strictly better than spec — adds observability and security layers

---

## §9.12: GUI Scheduling Page

Not audited in detail — this was the subject of MEU-72 (separate conversation). The scheduling page React components exist in `ui/`.

---

## Summary Table

| Category | Present | Deviated | Missing | Stub |
|----------|---------|----------|---------|------|
| **Domain** (§9.1) | 12 | 1 | 1 | 0 |
| **Validator** (§9.2) | 1 | 0 | 0 | 0 |
| **Runner** (§9.3) | 5 | 1 | 1 | 0 |
| **Fetch** (§9.4) | 3 | 1 | 0 | 1 |
| **Transform** (§9.5) | 4 | 1 | 0 | 0 |
| **Store** (§9.6) | 1 | 1 | 0 | 0 |
| **Render** (§9.7) | 4 | 0 | 0 | 0 |
| **Send** (§9.8) | 2 | 1 | 0 | 0 |
| **Models** (§9.9) | 12 | 0 | 0 | 0 |
| **REST** (§9.10) | 16 | 0 | 0 | 0 |
| **MCP** (§9.11) | 8 | 1 | 0 | 0 |
| **TOTAL** | **68** | **7** | **2** | **1** |

---

## Action Items by Priority

### 🔴 Critical (blocks end-to-end execution)

1. **[SCHED-PIPELINE-WIRING]** — Add `provider_adapter` to `PipelineRunner.__init__` and `initial_outputs`. Create `MarketDataProviderAdapter` bridge. Add `get_smtp_runtime_config()` to `EmailProviderService`. → **MEU-PW1**

### 🟡 Important (reduces feature coverage)

2. **FRESHNESS_TTL / is_market_closed** — Add `FRESHNESS_TTL` dict and `is_market_closed()` to `pipeline.py`. Wire into FetchStep for cache staleness decisions.
3. **FetchStep cache integration** — Wire `_check_cache()` stub to `FetchCacheModel` and `http_cache.py`.
4. **FetchResult provenance fields** — Add `content_type`, `warnings`, `fetched_at`, and `data_type` to `FetchResult`.
5. **SQL Sandbox SQLCipher key** — Add `key` parameter to `create_sandboxed_connection()` for encrypted DB access.

### 🟢 Low (Electron integration deferred)

6. **Electron powerMonitor** — Add `powerMonitor` listener in main process to POST sleep/wake to API. Blocked on GUI-layer wiring.

### ℹ️ Acceptable Deviations (no action needed)

- StepBase in `step_registry.py` vs `pipeline.py` — cohesion improvement
- MCP `registerTool()` vs `server.tool()` — strictly better pattern
- TransformStep Params using string keys vs inline dicts — simplified, equivalent
