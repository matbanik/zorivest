---
project: "2026-04-19-url-builders-cancellation"
date: "2026-04-19"
source: "docs/build-plan/09b-pipeline-hardening.md"
meus: ["MEU-PW6", "MEU-PW7"]
status: "draft"
template_version: "2.0"
---

# Implementation Plan: Provider URL Builders + Pipeline Cancellation

> **Project**: `2026-04-19-url-builders-cancellation`
> **Build Plan Section(s)**: [09b §9B.4](../../build-plan/09b-pipeline-hardening.md), [09b §9B.5](../../build-plan/09b-pipeline-hardening.md)
> **Status**: `draft`

---

## Goal

Complete Pipeline Runtime Hardening Group 2: fix [PIPE-URLBUILD] (all provider fetches fail due to hardcoded URL patterns and criteria key mismatch) and [PIPE-NOCANCEL] (no way to stop a stuck pipeline run). This unblocks MEU-PW8 (E2E Test Harness).

---

## User Review Required

> [!IMPORTANT]
> **PW7 adds a new REST endpoint** (`POST /runs/{run_id}/cancel`). This requires OpenAPI spec regeneration after implementation. No breaking changes to existing endpoints.

> [!IMPORTANT]
> **PW7 adds `CANCELLING` to `PipelineStatus` enum.** This is additive — existing consumers that switch on status values will not break, but the Alembic migration (if one exists) may need a matching DB column update. Current implementation uses string storage for status, so no migration is required.

---

## MEU-PW6: Provider URL Builders

### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| Per-provider URL builder classes (Yahoo, Polygon, Finnhub) | Spec | §9B.4b — explicit URL patterns documented |
| GenericUrlBuilder fallback for unregistered providers | Spec | §9B.4b — `{base}/{data_type}?symbols={s}` |
| Criteria key normalization (`tickers[]` ↔ `symbol`) | Spec | §9B.4b — `_resolve_tickers()` well-defined |
| Forward `headers_template` from provider registry to HTTP fetch | Spec | §9B.4c — explicit code snippet |
| `fetch_with_cache()` accepts `headers` param | Spec | §9B.4d — listed in files-to-modify |

### Boundary Inventory

_MEU-PW6 has no external input surface — it refactors internal adapter plumbing._

### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-PW6-1 | `YahooUrlBuilder.build_url()` produces correct URLs for `ohlcv`, `quote`, `news` data types | Spec (§9B.4b) | Empty tickers list → URL contains empty symbol segment |
| AC-PW6-2 | `PolygonUrlBuilder.build_url()` produces correct URLs for `ohlcv`, `quote` | Spec (§9B.4b) | N/A |
| AC-PW6-3 | `FinnhubUrlBuilder.build_url()` produces correct URLs for `ohlcv`, `quote`, `news` | Spec (§9B.4b) | N/A |
| AC-PW6-4 | `GenericUrlBuilder.build_url()` produces fallback URLs for any data type | Spec (§9B.4b) | N/A |
| AC-PW6-5 | `_resolve_tickers()` normalizes both `tickers: ["AAPL"]` and `symbol: "AAPL"` to `["AAPL"]` | Spec (§9B.4b) | No key present → empty list |
| AC-PW6-6 | `get_url_builder("yahoo")` returns `YahooUrlBuilder`, unknown provider returns `GenericUrlBuilder` | Spec (§9B.4b) | N/A |
| AC-PW6-7 | `MarketDataProviderAdapter._build_url()` replaced with `get_url_builder(provider).build_url()` dispatch | Spec (§9B.4d) | N/A |
| AC-PW6-8 | `_do_fetch()` passes `headers_template` from provider config to `fetch_with_cache()` | Spec (§9B.4c) | N/A |
| AC-PW6-9 | `fetch_with_cache()` accepts and merges `headers` kwarg into revalidation headers | Spec (§9B.4d) | N/A |

### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/infrastructure/src/zorivest_infra/market_data/url_builders.py` | new | `UrlBuilder` Protocol + `YahooUrlBuilder`, `PolygonUrlBuilder`, `FinnhubUrlBuilder`, `GenericUrlBuilder`, `URL_BUILDERS` registry, `get_url_builder()`, `_resolve_tickers()` |
| `packages/infrastructure/src/zorivest_infra/market_data/market_data_adapter.py` | modify | Replace `_build_url()` with `get_url_builder()` dispatch; pass provider name to builder; forward `headers_template` in `_do_fetch()` |
| `packages/infrastructure/src/zorivest_infra/market_data/http_cache.py` | modify | Add `headers` kwarg to `fetch_with_cache()` and merge with revalidation headers |
| `tests/unit/test_url_builders.py` | new | 15+ tests covering all builders, `_resolve_tickers()`, registry, and edge cases |
| `tests/unit/test_market_data_adapter.py` | modify | Add tests for tickers-key normalization and header forwarding |

---

## MEU-PW7: Pipeline Cancellation Infrastructure

### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| `CANCELLING` intermediate status in `PipelineStatus` enum | Spec | §9B.5b |
| `_active_tasks: dict[str, asyncio.Task]` task registry | Spec | §9B.5c |
| `cancel_run()` with cooperative + forced cancellation | Spec | §9B.5c — explicit code snippet |
| `_is_cancelling()` per-step cooperative check | Spec | §9B.5c |
| `asyncio.CancelledError` handler in `run()` | Spec | §9B.5c — already partially present |
| `POST /runs/{run_id}/cancel` REST endpoint | Spec | §9B.5d — explicit route definition |
| `SchedulingService.cancel_run()` delegation | Spec | §9B.5e — explicit code snippet |
| Idempotent: cancel on terminal run returns 200 | Spec | §9B.5d docstring |
| Cancel on non-existent run returns 404 | Spec | §9B.5d docstring |

### Boundary Inventory

| Surface | Schema Owner | Field Constraints | Extra-Field Policy | Error Mapping |
|---------|-------------|-------------------|--------------------|---------------|
| `POST /runs/{run_id}/cancel` path param | FastAPI path parameter (UUID type annotation) | `run_id: UUID` — FastAPI auto-validates UUID format | N/A (no body) | 422 → malformed `run_id`; 404 → well-formed but unknown run; 200 → cancellation initiated or already terminal |

### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-PW7-1 | `PipelineStatus.CANCELLING` enum member exists with value `"cancelling"` | Spec (§9B.5b) | N/A |
| AC-PW7-2 | `PipelineRunner._active_tasks` tracks running pipeline tasks by `run_id` | Spec (§9B.5c) | Task removed from registry after run completes |
| AC-PW7-3 | `PipelineRunner.cancel_run()` sets status to `CANCELLING`, waits `grace_seconds`, then force-cancels | Spec (§9B.5c) | Cancel on inactive run_id returns True |
| AC-PW7-4 | Cooperative cancellation check at step boundaries stops pipeline with `CANCELLED` status | Spec (§9B.5c) | N/A |
| AC-PW7-5 | `asyncio.CancelledError` caught in `run()` sets `CANCELLED` status (already present, verify) | Spec (§9B.5c) | N/A |
| AC-PW7-6 | `SchedulingService.cancel_run()` returns `None` for non-existent runs, current state for terminal runs, delegates for active runs | Spec (§9B.5e) | Non-existent run_id → None |
| AC-PW7-7 | `POST /runs/{run_id}/cancel` returns 422 for malformed `run_id`, 404 for well-formed but unknown runs, 200 with status for valid runs | Local Canon (AGENTS.md L203) | Malformed run_id → 422 |
| AC-PW7-8 | Cancel is idempotent: calling on completed/cancelled run returns 200 | Spec (§9B.5d) | N/A |
| AC-PW7-9 | `_active_tasks` cleanup occurs in `finally` block of `run()` | Spec (§9B.5c) | N/A |

### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/core/src/zorivest_core/domain/enums.py` | modify | Add `CANCELLING = "cancelling"` to `PipelineStatus` |
| `packages/core/src/zorivest_core/services/pipeline_runner.py` | modify | Add `_active_tasks` dict to `__init__`; register/cleanup current task in `run()`; add `cancel_run()` method; add `_is_cancelling()` check; add cooperative check at step boundary |
| `packages/core/src/zorivest_core/services/scheduling_service.py` | modify | Add `cancel_run()` method delegating to runner |
| `packages/api/src/zorivest_api/routes/scheduling.py` | modify | Add `CancelRunResponse` model; add `POST /runs/{run_id}/cancel` endpoint |
| `tests/unit/test_pipeline_runner.py` | modify | Add 6+ tests for cancel_run(), _is_cancelling(), task registry, cooperative cancellation |
| `tests/unit/test_scheduling_service.py` | modify | Add 3+ tests for cancel_run() delegation, idempotency, not-found |
| `tests/unit/test_api_scheduling.py` | modify | Add 3+ tests for cancel endpoint (200, 404, idempotent) |

---

## Out of Scope

- GUI cancel button (deferred to GUI MEU per §9B.5a)
- URL builders for all 14 providers (only Yahoo, Polygon, Finnhub per spec; `GenericUrlBuilder` covers rest)
- MEU-PW8 (E2E test harness — blocked on PW6+PW7 completion)

---

## BUILD_PLAN.md Audit

This project does not modify build-plan sections. After execution, `docs/BUILD_PLAN.md` status column for MEU-PW6 and MEU-PW7 must be updated from ⬜ to ✅.

```powershell
rg "MEU-PW6|MEU-PW7" docs/BUILD_PLAN.md  # Expected: 2 matches (status rows) — update ⬜ → ✅
```

---

## Verification Plan

### 1. Unit Tests — PW6 URL Builders
```powershell
uv run pytest tests/unit/test_url_builders.py -v *> C:\Temp\zorivest\pytest-pw6.txt; Get-Content C:\Temp\zorivest\pytest-pw6.txt | Select-Object -Last 40
```

### 2. Unit Tests — PW6 Adapter Integration
```powershell
uv run pytest tests/unit/test_market_data_adapter.py -k "tickers or url_build or headers" -v *> C:\Temp\zorivest\pytest-pw6-adapter.txt; Get-Content C:\Temp\zorivest\pytest-pw6-adapter.txt | Select-Object -Last 30
```

### 3. Unit Tests — PW7 Cancel
```powershell
uv run pytest tests/unit/test_pipeline_runner.py -k "cancel" -v *> C:\Temp\zorivest\pytest-pw7-runner.txt; Get-Content C:\Temp\zorivest\pytest-pw7-runner.txt | Select-Object -Last 30
```

### 4. Unit Tests — PW7 Service + API
```powershell
uv run pytest tests/unit/test_scheduling_service.py tests/unit/test_api_scheduling.py -k "cancel" -v *> C:\Temp\zorivest\pytest-pw7-svc.txt; Get-Content C:\Temp\zorivest\pytest-pw7-svc.txt | Select-Object -Last 30
```

### 5. Type Check
```powershell
uv run pyright packages/core packages/infrastructure packages/api *> C:\Temp\zorivest\pyright.txt; Get-Content C:\Temp\zorivest\pyright.txt | Select-Object -Last 30
```

### 6. Lint
```powershell
uv run ruff check packages/ *> C:\Temp\zorivest\ruff.txt; Get-Content C:\Temp\zorivest\ruff.txt | Select-Object -Last 20
```

### 7. MEU Gate
```powershell
uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate.txt; Get-Content C:\Temp\zorivest\validate.txt | Select-Object -Last 50
```

### 8. OpenAPI Drift Check + Regeneration (PW7 adds endpoint)
```powershell
uv run python tools/export_openapi.py --check openapi.committed.json *> C:\Temp\zorivest\openapi-check.txt; Get-Content C:\Temp\zorivest\openapi-check.txt
uv run python tools/export_openapi.py -o openapi.committed.json *> C:\Temp\zorivest\openapi-regen.txt; Get-Content C:\Temp\zorivest\openapi-regen.txt
```

---

## Open Questions

_None — both MEUs are well-specified in §9B.4 and §9B.5. All behaviors are classified as `Spec` with explicit code snippets in the build plan._

---

## Research References

- [09b-pipeline-hardening.md §9B.4](../../build-plan/09b-pipeline-hardening.md) — Provider URL Builders spec
- [09b-pipeline-hardening.md §9B.5](../../build-plan/09b-pipeline-hardening.md) — Pipeline Cancellation spec
- [Prefect, Temporal, Azure Data Factory REST API patterns](§9B.5a) — cancel semantics research source
- [G8 emerging standard](../../.agent/docs/emerging-standards.md) — OpenAPI drift prevention
- [G15 emerging standard](../../.agent/docs/emerging-standards.md) — API error surfacing
