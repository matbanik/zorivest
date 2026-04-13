# Pipeline Integration Gap Analysis

> **Scope:** Phase 9 Scheduling & Pipeline Engine (MEUs 77–90d)  
> **Status:** All individual MEUs marked ✅ — but **0 of 5 step types are operationally wired**  
> **Date:** 2026-04-12

---

## Situation

Every Phase 9 MEU (77–90d) is marked complete in [BUILD_PLAN.md](file:///p:/zorivest/docs/BUILD_PLAN.md#L279). Each delivered its specified deliverable:
- Domain models ✅ (enums, policies, step registry, validator)
- ORM models ✅ (9 scheduling tables)
- Repositories ✅ (8 repo classes + audit triggers)
- PipelineRunner ✅ (sequential executor with resume, retry, dry-run)
- All 5 step types ✅ (fetch, transform, store_report, render, send)
- API + MCP ✅ (16 endpoints + 8 MCP tools)
- Security guardrails ✅ (rate limits, approval, audit)
- Persistence integration ✅ (MEU-90a: SqlAlchemyUnitOfWork)

**The problem:** Each MEU built its component in isolation. Nobody wired the components together. The `PipelineRunner` in [main.py:241](file:///p:/zorivest/packages/api/src/zorivest_api/main.py#L241) instantiates with only 3 of 11 required dependencies, causing every pipeline execution to crash.

---

## Gap Categories

### Category 1: Service Wiring (MEU-PW1 — already planned)

These are gaps where built infrastructure services are **not injected** into `PipelineRunner.initial_outputs`. This is the [MEU-PW1 discovery](file:///p:/zorivest/.agent/context/scheduling/meu-pw1-discovery.md).

| # | Gap | Severity | What Exists | What's Missing | Effort |
|---|-----|----------|-------------|----------------|--------|
| W-1 | `provider_adapter` not injected | 🔴 **Crash** | [MarketDataService](file:///p:/zorivest/packages/core/src/zorivest_core/services/market_data_service.py#L59) (async, returns `MarketQuote`/`MarketNewsItem` DTOs) | Bridge adapter that: receives `provider` + `data_type` + `criteria` → returns `bytes` (raw response). Must convert between service's DTO API and step's raw-bytes contract. | M |
| W-2 | `db_writer` not injected | 🔴 **Crash** | [write_dispositions.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/repositories/write_dispositions.py) (`write_append`, `write_replace`, `write_merge`) | Adapter class with `.write(df, table, disposition)` method wrapping the raw SQL functions with a session. | S |
| W-3 | `report_repository` not injected | 🔴 **Crash** | [ReportRepository](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py#L173) | Pass through PipelineRunner → initial_outputs. Already built, just not wired. | XS |
| W-4 | `db_connection` not injected | 🟡 **Conditional crash** | [create_sandboxed_connection()](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/security/sql_sandbox.py#L41) | Create sandboxed connection in main.py, pass as initial_output. | XS |
| W-5 | `pipeline_state_repo` not injected | 🟡 **Conditional crash** | [PipelineStateRepository](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py#L278) | Pass through PipelineRunner → initial_outputs. | XS |
| W-6 | `template_engine` not injected | 🟢 **Degraded** | [create_template_engine()](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/rendering/template_engine.py#L25) | Pass through PipelineRunner → initial_outputs. RenderStep falls back to inline HTML without it. | XS |
| W-7 | `delivery_repository` not passed in main.py | 🟢 **Degraded** | [DeliveryRepository](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py#L367), PipelineRunner constructor already has param | Pass it in `main.py:241`. SendStep skips dedup without it. | XS |
| W-8 | `smtp_config` not passed in main.py | 🟢 **Degraded** | [EmailProviderService](file:///p:/zorivest/packages/core/src/zorivest_core/services/email_provider_service.py), PipelineRunner constructor has param | Pass it in `main.py:241`. But: key mismatch — see D-1 below. | XS |
| W-9 | PipelineRunner constructor missing 6 params | 🔴 **Structural** | Constructor only has `uow`, `ref_resolver`, `condition_evaluator`, `delivery_repository`, `smtp_config` ([L50-58](file:///p:/zorivest/packages/core/src/zorivest_core/services/pipeline_runner.py#L50)) | Add `provider_adapter`, `db_writer`, `db_connection`, `report_repository`, `template_engine`, `pipeline_state_repo` constructor params + initial_outputs injection at [L94-98](file:///p:/zorivest/packages/core/src/zorivest_core/services/pipeline_runner.py#L94) | S |

---

### Category 2: Code-Level Defects

These are logic bugs or API mismatches in existing code that prevent correct pipeline execution even after wiring.

| # | Gap | Severity | Location | What's Wrong | Fix |
|---|-----|----------|----------|--------------|-----|
| D-1 | SMTP key mismatch | 🔴 **Wrong behavior** | [EmailProviderService.get_config()](file:///p:/zorivest/packages/core/src/zorivest_core/services/email_provider_service.py#L40) returns `smtp_host`, `from_email` — [SendStep](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/send_step.py#L102) expects `host`, `sender` | Add `get_smtp_runtime_config()` method returning keys matching SendStep contract (`host`, `port`, `sender`, `username`, `password`) |
| D-2 | FetchStep `_check_cache` is a stub | 🟡 **Feature missing** | [fetch_step.py:128-132](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/fetch_step.py#L128) — returns `None` always | Wire to [FetchCacheRepository](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py#L219) with TTL check using [FRESHNESS_TTL](file:///p:/zorivest/packages/core/src/zorivest_core/domain/pipeline.py#L221) and [is_market_closed()](file:///p:/zorivest/packages/core/src/zorivest_core/domain/pipeline.py#L252) |
| D-3 | FetchStep doesn't use [PipelineRateLimiter](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/market_data/pipeline_rate_limiter.py#L22) | 🟡 **Feature missing** | fetch_step.py `_fetch_from_provider()` calls adapter.fetch() directly | Inject `PipelineRateLimiter` and use `execute_with_limits()` to enforce per-provider rate limiting |
| D-4 | FetchStep doesn't use [fetch_with_cache()](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/market_data/http_cache.py#L16) | 🟡 **Feature missing** | HTTP-level cache revalidation (ETag/If-Modified-Since) built but not called | Connect to the adapter's HTTP layer or make adapter cache-aware |
| D-5 | Dead stubs in [stubs.py](file:///p:/zorivest/packages/api/src/zorivest_api/stubs.py#L180) | 🟢 **Hygiene** | `StubMarketDataService` and `StubProviderConnectionService` defined but no longer imported | Delete both classes (~50 lines) |

---

### Category 3: Data Schema Gaps

These are missing ORM models and validation schemas for pipeline write targets.

| # | Gap | Severity | Table | What Exists | What's Missing |
|---|-----|----------|-------|-------------|----------------|
| S-1 | No `market_ohlcv` SQLAlchemy model | 🟡 **Schema risk** | `market_ohlcv` | [Allowlist](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/repositories/write_dispositions.py#L22) (10 columns) + [OHLCV_SCHEMA](file:///p:/zorivest/packages/core/src/zorivest_core/services/validation_gate.py#L24) Pandera | SQLAlchemy model with type constraints, indexes, timestamps |
| S-2 | No `market_quotes` SQLAlchemy model | 🟡 **Schema risk** | `market_quotes` | [Allowlist](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/repositories/write_dispositions.py#L35) (7 columns) | SQLAlchemy model + Pandera schema |
| S-3 | No `market_news` SQLAlchemy model | 🟡 **Schema risk** | `market_news` | [Allowlist](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/repositories/write_dispositions.py#L44) (8 columns) | SQLAlchemy model + Pandera schema |
| S-4 | No `market_fundamentals` SQLAlchemy model | 🟡 **Schema risk** | `market_fundamentals` | [Allowlist](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/repositories/write_dispositions.py#L54) (6 columns) | SQLAlchemy model + Pandera schema |
| S-5 | No Pandera schema for quotes | 🟡 **No validation** | N/A | Only [OHLCV_SCHEMA](file:///p:/zorivest/packages/core/src/zorivest_core/services/validation_gate.py#L24) exists | Add `QUOTE_SCHEMA`, `NEWS_SCHEMA`, `FUNDAMENTALS_SCHEMA` |
| S-6 | Field mappings only cover OHLCV | 🟢 **Partial** | N/A | [FIELD_MAPPINGS](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/market_data/field_mappings.py#L18) has 3 OHLCV entries (generic, ibkr, polygon) | Add mappings for quotes, news, fundamentals per provider |

> **Note on S-1 through S-4:** The current `write_append()` uses raw SQL `INSERT INTO` which creates tables dynamically in SQLite without type constraints, foreign keys, or indexes. This works but produces weak schema enforcement. The write_dispositions functions do **not** go through ORM — they use `session.execute(text(...))`.

---

## Provider Adapter — The Biggest Integration Challenge

The `provider_adapter` (W-1) is the most complex gap because of a **fundamental API mismatch**:

| Aspect | MarketDataService (built) | FetchStep expects |
|--------|--------------------------|-------------------|
| **Interface** | `get_quote(ticker) → MarketQuote` | `adapter.fetch(provider, data_type, criteria) → bytes` |
| **Return type** | Typed DTOs (`MarketQuote`, `MarketNewsItem`) | Raw bytes |
| **Provider selection** | Internal — tries providers in priority order | External — step params specify `provider` explicitly |
| **Data types** | 4 methods: `get_quote`, `get_news`, `search_ticker`, `get_sec_filings` | Single `fetch()` with `data_type` dispatch |
| **OHLCV** | ❌ **Not implemented** — MarketDataService has no OHLCV method | FetchStep's primary use case |

### Critical Finding: MarketDataService cannot serve as a pipeline adapter

[MarketDataService](file:///p:/zorivest/packages/core/src/zorivest_core/services/market_data_service.py#L59) was designed for the **GUI layer** (real-time quotes, search, news). It:
- Returns structured DTOs, not raw data
- Handles provider fallback internally (wrong for pipeline's explicit provider selection)
- Has **no OHLCV/historical data method** — only real-time quotes

**The pipeline needs a different adapter** that:
1. Takes explicit provider + data_type + criteria (date range, tickers)
2. Calls the provider's HTTP API directly (using [PipelineRateLimiter](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/market_data/pipeline_rate_limiter.py#L22))
3. Returns raw bytes (JSON payload) for the TransformStep to parse
4. Supports [fetch_with_cache()](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/market_data/http_cache.py#L16) for HTTP-level caching
5. Uses [FetchCacheRepository](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py#L219) for DB-level caching

This is a **new service**, not a thin wrapper. Estimated effort: **Medium**.

---

## Execution Sequence (Recommended)

### Phase A: Minimum Viable Pipeline (crash → degraded)

Get the pipeline running end-to-end with at least `transform → store_report → render → send`.

| Order | Item | Description | Effort |
|-------|------|-------------|--------|
| 1 | W-9 | Add 6 missing constructor params to PipelineRunner | S |
| 2 | W-3 | Wire ReportRepository | XS |
| 3 | W-4 | Wire sandboxed db_connection | XS |
| 4 | W-5 | Wire PipelineStateRepository | XS |
| 5 | W-6 | Wire template_engine | XS |
| 6 | W-7 | Wire delivery_repository in main.py | XS |
| 7 | D-1 | Fix SMTP key mismatch (add `get_smtp_runtime_config()`) | S |
| 8 | W-8 | Wire smtp_config via the fixed method | XS |
| 9 | W-2 | Create DbWriteAdapter | S |

**After Phase A:** Transform, StoreReport, Render, and Send steps are operational. FetchStep still crashes (no provider_adapter).

### Phase B: FetchStep Operational

| Order | Item | Description | Effort |
|-------|------|-------------|--------|
| 10 | W-1 | Create MarketDataProviderAdapter (new service) | M |
| 11 | D-2 | Wire `_check_cache` to FetchCacheRepository + FRESHNESS_TTL | S |
| 12 | D-3 | Integrate PipelineRateLimiter into adapter | S |
| 13 | D-4 | Connect fetch_with_cache() for HTTP revalidation | S |

**After Phase B:** Full pipeline is operational with all 5 step types.

### Phase C: Data Quality Hardening (optional, can defer)

| Order | Item | Description | Effort |
|-------|------|-------------|--------|
| 14 | S-1–S-4 | Create 4 market data SQLAlchemy models | S |
| 15 | S-5 | Create 3 additional Pandera schemas (quotes, news, fundamentals) | S |
| 16 | S-6 | Add field mappings for quotes/news/fundamentals | S |
| 17 | D-5 | Delete dead stubs | XS |

---

## Blast Radius

| Component | Files Changed |
|-----------|---------------|
| PipelineRunner | [pipeline_runner.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/pipeline_runner.py) (constructor + initial_outputs) |
| EmailProviderService | [email_provider_service.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/email_provider_service.py) (new method) |
| New Adapters | `market_data_provider_adapter.py` (NEW), `db_write_adapter.py` (NEW) |
| Wiring | [main.py](file:///p:/zorivest/packages/api/src/zorivest_api/main.py#L235) (L235–256 service creation block) |
| FetchStep | [fetch_step.py](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/fetch_step.py) (`_check_cache` impl) |
| Stubs | [stubs.py](file:///p:/zorivest/packages/api/src/zorivest_api/stubs.py) (delete dead classes) |
| Models (Phase C) | [models.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/models.py), [validation_gate.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/validation_gate.py) |
| Tests | New integration test: `test_pipeline_e2e.py` |
