# Pipeline Data Flow: PolicyDocument → Service Layers

> Traces every `context.outputs` dependency across all 5 step types.  
> ✅ = Built & wired · 🔧 = Built, not wired · ❌ = Not built · 🔲 = Stub

---

## How the Data Flows

```
┌──────────────────────────────────────────────────────────────────────┐
│  PolicyDocument (JSON)                                               │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ steps: [                                                       │  │
│  │   { type: "fetch",        params: {provider, data_type, ...} } │  │
│  │   { type: "transform",    params: {target_table, ...} }        │  │
│  │   { type: "store_report", params: {report_name, queries, ...} }│  │
│  │   { type: "render",       params: {template, format, ...} }    │  │
│  │   { type: "send",         params: {channel, recipients, ...} } │  │
│  └────────────────────────────────────────────────────────────────┘  │
└───────────────────────────┬──────────────────────────────────────────┘
                            │
                            ↓
┌───────────────────────────────────────────────────────────────────────┐
│  PipelineRunner.run()                                                 │
│                                                                       │
│  initial_outputs = {                                                  │
│    "delivery_repository": ❌ NOT INJECTED (constructor has param,     │
│                               main.py doesn't pass it)                │
│    "smtp_config":          ❌ NOT INJECTED (same — param exists,      │
│                               main.py doesn't pass it)                │
│    "provider_adapter":     ❌ MISSING (no constructor param)          │
│    "db_writer":            ❌ MISSING (no constructor param)          │
│    "db_connection":        ❌ MISSING (no constructor param)          │
│    "report_repository":    ❌ MISSING (no constructor param)          │
│    "template_engine":      ❌ MISSING (no constructor param)          │
│    "pipeline_state_repo":  ❌ MISSING (no constructor param)          │
│  }                                                                    │
│                                                                       │
│  For each step in policy.steps:                                       │
│    step_impl = STEP_REGISTRY[step.type]                               │
│    result = step_impl.execute(step.params, context)                   │
│    context.outputs[step.id] = result.output  ← step chaining          │
└───────────────────────────────────────────────────────────────────────┘
```

---

## Master Checklist: Context Dependencies per Step

### 1. FetchStep (`type: "fetch"`)

| # | `context.outputs` Key | Required? | Infra Service | Built? | Injected by Runner? | Wired in main.py? |
|---|----------------------|-----------|---------------|--------|--------------------|--------------------|
| 1 | `provider_adapter` | **Hard** (ValueError if None) | `MarketDataProviderAdapter` (needs creation) wrapping [MarketDataService](file:///p:/zorivest/packages/core/src/zorivest_core/services/market_data_service.py#L59) | ❌ Adapter not created | ❌ No constructor param | ❌ |
| 2 | `pipeline_state_repo` | Soft (optional for criteria) | [PipelineStateRepository](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py#L278) | ✅ Built | ❌ Not injected | ❌ |
| 3 | `db_connection` | Soft (optional for db_query criteria) | [create_sandboxed_connection](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/security/sql_sandbox.py#L41) | ✅ Built | ❌ Not injected | ❌ |

**Source:** [fetch_step.py:59,60,117](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/fetch_step.py#L59)

**Verdict:** ❌ **Will crash** — `provider_adapter` raises `ValueError` at [L118-121](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/fetch_step.py#L118)

---

### 2. TransformStep (`type: "transform"`)

| # | `context.outputs` Key | Required? | Infra Service | Built? | Injected by Runner? | Wired in main.py? |
|---|----------------------|-----------|---------------|--------|--------------------|--------------------|
| 4 | `fetch_result` | **Hard** (reads content) | Output from prior FetchStep (step chaining) | ✅ Auto-set | ✅ Via step chaining | N/A |
| 5 | `db_writer` | **Hard** (ValueError if None) | Needs adapter wrapping [write_dispositions.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/repositories/write_dispositions.py) (`write_append`, `write_replace`, `write_merge`) | ✅ Functions built | ❌ No constructor param | ❌ |

**Source:** [transform_step.py:72,148,182](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/transform_step.py#L72)

**Verdict:** ❌ **Will crash** — `db_writer` raises `ValueError` at [L183-184](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/transform_step.py#L183) (even if fetch succeeds)

---

### 3. StoreReportStep (`type: "store_report"`)

| # | `context.outputs` Key | Required? | Infra Service | Built? | Injected by Runner? | Wired in main.py? |
|---|----------------------|-----------|---------------|--------|--------------------|--------------------|
| 6 | `db_connection` | Conditional (required when `data_queries` non-empty) | [create_sandboxed_connection](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/security/sql_sandbox.py#L41) | ✅ Built | ❌ Not injected | ❌ |
| 7 | `report_repository` | **Hard** (ValueError if None) | [ReportRepository](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py#L173) | ✅ Built | ❌ No constructor param | ❌ |

**Source:** [store_report_step.py:106,152](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/store_report_step.py#L106)

**Verdict:** ❌ **Will crash** — `report_repository` raises `ValueError` at [L153-156](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/store_report_step.py#L153)

---

### 4. RenderStep (`type: "render"`)

| # | `context.outputs` Key | Required? | Infra Service | Built? | Injected by Runner? | Wired in main.py? |
|---|----------------------|-----------|---------------|--------|--------------------|--------------------|
| 8 | `report_data` | Soft (defaults to `{}`) | Output from prior StoreReportStep (step chaining) | ✅ Auto-set | ✅ Via step chaining | N/A |
| 9 | `template_engine` | Soft (falls back to inline HTML) | [create_template_engine()](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/rendering/template_engine.py#L25) | ✅ Built | ❌ Not injected | ❌ |

**Source:** [render_step.py:52,108](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/render_step.py#L52)

**Verdict:** ⚠️ **Won't crash** but produces minimal fallback HTML. PDF rendering depends on Playwright availability.

---

### 5. SendStep (`type: "send"`)

| # | `context.outputs` Key | Required? | Infra Service | Built? | Injected by Runner? | Wired in main.py? |
|---|----------------------|-----------|---------------|--------|--------------------|--------------------|
| 10 | `smtp_config` | Soft (defaults to `localhost:587`) | [EmailProviderService.get_config()](file:///p:/zorivest/packages/core/src/zorivest_core/services/email_provider_service.py#L40) — **but key names don't match** | ✅ Built (wrong keys) | 🔧 Constructor has param | ❌ Not passed in main.py |
| 11 | `delivery_repository` | Soft (dedup skipped if None) | [DeliveryRepository](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py#L367) | ✅ Built | 🔧 Constructor has param | ❌ Not passed in main.py |

**Source:** [send_step.py:102,108](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/send_step.py#L102)

**Verdict:** ⚠️ **Won't crash** but sends to `localhost:587` with wrong sender, no dedup tracking.

---

## Current Wiring in main.py

```python
# main.py L241 — CURRENT STATE
pipeline_runner = PipelineRunner(uow, RefResolver(), ConditionEvaluator())
#                                 ↑      ↑                ↑
#                                 ✅     ✅               ✅
# Missing keyword args:
#   delivery_repository=???  ← param exists on constructor but not passed
#   smtp_config=???          ← param exists on constructor but not passed
#   provider_adapter=???     ← param DOES NOT EXIST on constructor
#   db_writer=???            ← param DOES NOT EXIST on constructor
#   db_connection=???        ← param DOES NOT EXIST on constructor
#   report_repository=???    ← param DOES NOT EXIST on constructor
#   template_engine=???      ← param DOES NOT EXIST on constructor
#   pipeline_state_repo=???  ← param DOES NOT EXIST on constructor
```

---

## Summary Scorecard

| Step Type | Total Dependencies | Built & Available | Injected by Runner | Wired in main.py | Operational? |
|-----------|-------------------|-------------------|-------------------|------------------|--------------|
| **fetch** | 3 | 1 of 3 | 0 of 3 | 0 of 3 | ❌ Crashes |
| **transform** | 2 | 1 of 2 | 1 of 2 (chaining) | 0 of 1 | ❌ Crashes |
| **store_report** | 2 | 2 of 2 | 0 of 2 | 0 of 2 | ❌ Crashes |
| **render** | 2 | 2 of 2 | 1 of 2 (chaining) | 0 of 1 | ⚠️ Degraded |
| **send** | 2 | 2 of 2 | 0 of 2 | 0 of 2 | ⚠️ Degraded |
| **TOTAL** | **11** | **8 of 11** | **2 of 11** | **0 of 8** | **0 of 5 fully operational** |

> **Key finding:** 8 of 11 infrastructure services are built, but **zero** are wired through `main.py` into `PipelineRunner`. The bottleneck is entirely in the wiring layer (MEU-PW1), not in missing implementations.

---

## SMTP Key Mismatch Detail

| Field | SendStep expects | EmailProviderService returns | Match? |
|-------|-----------------|----------------------------|--------|
| Host | `smtp_config["host"]` | `config["smtp_host"]` | ❌ |
| Port | `smtp_config["port"]` | `config["port"]` | ✅ |
| Sender | `smtp_config["sender"]` | `config["from_email"]` | ❌ |
| Password | `smtp_config["password"]` | **Not returned** (security) | ❌ |
| Username | `smtp_config["username"]` | `config["username"]` | ✅ |

**Fix:** Add `get_smtp_runtime_config()` method to `EmailProviderService` that returns keys matching SendStep's contract and includes the decrypted password for SMTP auth.

---

## What the Screenshot Shows

The policy JSON in the screenshot has:
```json
{
  "steps": [
    { "id": "step_1", "type": "fetch", "params": {} }
  ]
}
```

The error is: **"2 validation errors for Params: provider Field required, data_type Field required"**

This is the **first failure point** — Pydantic validation catches missing required params before the step even tries to call `provider_adapter`. Even with valid params (`provider: "yahoo"`, `data_type: "ohlcv"`), the step would still crash at [fetch_step.py:118](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/fetch_step.py#L118) because `provider_adapter` is not injected.

---

## Database Needs per Step

### FetchStep — DB Dependencies

| Table | Purpose | SQLAlchemy Model | Repository | Notes |
|-------|---------|:-:|:-:|-------|
| `fetch_cache` | Check cached response (ETag, TTL) | ✅ [FetchCacheModel](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/models.py#L589) | ✅ [FetchCacheRepository](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py#L219) | Upsert + invalidate |
| `pipeline_state` | High-water mark for incremental fetches | ✅ [PipelineStateModel](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/models.py#L507) | ✅ [PipelineStateRepository](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py#L278) | UniqueConstraint on policy+provider+type+entity |
| `market_provider_settings` | API key + rate limit for provider | ✅ [MarketProviderSettingModel](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/models.py#L220) | ✅ via MarketDataService | Fernet-encrypted keys |

**Writes:** None — FetchStep returns data in memory via `StepResult.output`.

---

### TransformStep — DB Dependencies (Write Target Tables)

| Target Table | Purpose | SQLAlchemy Model | Column Allowlist | Pandera Schema |
|-------------|---------|:-:|:-:|:-:|
| `market_ohlcv` | OHLCV candlestick data | ❌ **NO MODEL** | ✅ [10 cols](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/repositories/write_dispositions.py#L22) | ✅ [OHLCV_SCHEMA](file:///p:/zorivest/packages/core/src/zorivest_core/services/validation_gate.py#L24) |
| `market_quotes` | Real-time bid/ask/last | ❌ **NO MODEL** | ✅ [7 cols](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/repositories/write_dispositions.py#L35) | ❌ No schema |
| `market_news` | News headlines + sentiment | ❌ **NO MODEL** | ✅ [8 cols](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/repositories/write_dispositions.py#L44) | ❌ No schema |
| `market_fundamentals` | Fundamental metrics | ❌ **NO MODEL** | ✅ [6 cols](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/repositories/write_dispositions.py#L54) | ❌ No schema |

> **Critical:** These 4 tables exist only as column allowlists in `write_dispositions.py`. The `write_append()` function uses raw SQL `INSERT INTO` — no ORM. Tables are created dynamically by SQLite on first INSERT, but **without type constraints, foreign keys, or indexes**. Only `ohlcv` has a Pandera validation schema; the other 3 data types pass through unvalidated.

**Write mechanism:** [write_dispositions.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/repositories/write_dispositions.py) provides 3 functions:
- `write_append()` — INSERT new rows
- `write_replace()` — DELETE all + INSERT
- `write_merge()` — INSERT OR REPLACE (upsert by PK)

All 3 validate `table_name ∈ TABLE_ALLOWLIST` and `columns ⊆ allowed_columns` before executing.

---

### StoreReportStep — DB Dependencies

| Table | Direction | SQLAlchemy Model | Repository | Notes |
|-------|-----------|:-:|:-:|-------|
| *(user tables)* | READ | Via raw `db_connection` | [sql_sandbox.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/security/sql_sandbox.py) | Default-deny authorizer, SELECT-only |
| `reports` | WRITE | ✅ [ReportModel](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/models.py#L532) | ✅ [ReportRepository](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py#L173) | spec_json + snapshot_json + SHA-256 hash |
| `report_versions` | AUTO | ✅ [ReportVersionModel](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/models.py#L556) | ✅ via UPDATE trigger ([L639](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/models.py#L639)) | Append-only version history |

---

### RenderStep — DB Dependencies

**None.** Operates entirely in memory:
- Reads `report_data` from context (step chaining from StoreReportStep)
- Uses [create_template_engine()](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/rendering/template_engine.py#L25) — Jinja2 with `currency`/`percent` filters ✅
- Uses [render_pdf()](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/rendering/pdf_renderer.py#L17) — Playwright headless Chromium ✅ (optional dep)

---

### SendStep — DB Dependencies

| Table | Direction | SQLAlchemy Model | Repository | Notes |
|-------|-----------|:-:|:-:|-------|
| `email_provider` | READ | ✅ [EmailProviderModel](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/models.py#L237) | ✅ [EmailProviderService](file:///p:/zorivest/packages/core/src/zorivest_core/services/email_provider_service.py) | SMTP host/port/credentials (Fernet-encrypted password) |
| `report_delivery` | READ+WRITE | ✅ [ReportDeliveryModel](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/models.py#L572) | ✅ [DeliveryRepository](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py#L367) | SHA-256 dedup key for idempotent delivery |

---

## Database Schema Gap Summary

| Area | SQLAlchemy Models | Pandera Schemas | Write Allowlist | Gap? |
|------|:-:|:-:|:-:|:-:|
| **Scheduling infra** (9 tables: policies, runs, steps, state, reports, report_versions, delivery, cache, audit) | ✅ All 9 | N/A | N/A | None |
| `market_ohlcv` | ❌ No model | ✅ | ✅ 10 cols | **No ORM** — raw SQL insert |
| `market_quotes` | ❌ No model | ❌ | ✅ 7 cols | **No ORM, no validation** |
| `market_news` | ❌ No model | ❌ | ✅ 8 cols | **No ORM, no validation** |
| `market_fundamentals` | ❌ No model | ❌ | ✅ 6 cols | **No ORM, no validation** |

### Impact Assessment

1. **MEU-PW1 (pipeline-runtime-wiring):** Not blocked by schema gaps — the `db_writer` adapter wraps raw SQL functions that don't need ORM models.
2. **MEU-85 (FetchStep + cache):** Should add the 4 market data SQLAlchemy models for proper table creation with type constraints and indexes.
3. **Data quality:** Only `ohlcv` data gets Pandera validation. Quotes/news/fundamentals data flows through unvalidated — needs 3 additional Pandera schemas.

---

## Cross-Reference: Full Integration Gap Analysis

> **See:** [integration-gap-analysis.md](file:///p:/zorivest/.agent/context/scheduling/integration-gap-analysis.md)
>
> The full analysis identifies **22 integration gaps** across 3 categories (service wiring, code defects, data schemas) with a 3-phase execution sequence.

### Critical Finding: MarketDataService ≠ Pipeline Adapter

[MarketDataService](file:///p:/zorivest/packages/core/src/zorivest_core/services/market_data_service.py#L59) was designed for the **GUI layer** — it returns typed DTOs (`MarketQuote`, `MarketNewsItem`), manages provider fallback internally, and has **no OHLCV/historical data method**. The pipeline's FetchStep expects a raw-bytes adapter with explicit provider selection. A **new adapter service** is required (Medium effort), not a thin wrapper around MarketDataService.
