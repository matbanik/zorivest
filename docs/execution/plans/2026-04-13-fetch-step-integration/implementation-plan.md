---
project: "2026-04-13-fetch-step-integration"
date: "2026-04-13"
source: "docs/build-plan/09-scheduling.md §9.4, .agent/context/scheduling/meu-pw2-scope.md"
meus: ["MEU-PW2"]
status: "draft"
template_version: "2.0"
---

# Implementation Plan: Fetch Step Integration (MEU-PW2)

> **Project**: `2026-04-13-fetch-step-integration`
> **Build Plan Section(s)**: [09-scheduling.md §9.4](../../build-plan/09-scheduling.md), [meu-pw2-scope.md](../../../.agent/context/scheduling/meu-pw2-scope.md)
> **Status**: `draft`

---

## Goal

Complete the pipeline engine's fetch capability by creating `MarketDataProviderAdapter`, implementing cache freshness checks with market-hours awareness, integrating `PipelineRateLimiter`, and wiring HTTP cache revalidation. After this MEU, a pipeline with `fetch → transform → store_report → render → send` can execute end-to-end with real HTTP calls (mocked in tests).

**Predecessor**: MEU-PW1 (`pipeline-runtime-wiring`) expanded PipelineRunner with 8 keyword params and left `provider_adapter=None` as a deferred slot for this MEU.

---

## User Review Required

> [!IMPORTANT]
> **Dependency direction clarification**: The scope document suggests placing the adapter in `core/services/`. However, the adapter needs to import `PipelineRateLimiter` and `fetch_with_cache` from `zorivest_infra`, which would violate the Domain → Infra dependency rule. The plan places the **port protocol** in `core/application/ports.py` and the **concrete implementation** in `packages/infrastructure/src/zorivest_infra/market_data/market_data_adapter.py`. This follows the exact same pattern used for all other infra adapters (DbWriteAdapter, encryption adapters, etc.).

> [!IMPORTANT]
> **Two-layer caching design**: FetchStep uses two cache layers:
> 1. **Application-level** (FetchCacheRepository TTL check) — decides whether to skip fetching entirely
> 2. **HTTP-level** (fetch_with_cache with ETag/If-Modified-Since) — minimizes bandwidth when a re-fetch is needed
>
> If the application cache is fresh → return immediately (no HTTP call). If stale → make conditional HTTP request via the adapter (which uses fetch_with_cache internally). After successful fetch, FetchStep upserts the result back to the cache.

---

## Proposed Changes

### Component 1: Port Protocol (Core Layer)

#### [MODIFY] [ports.py](file:///p:/zorivest/packages/core/src/zorivest_core/application/ports.py)

Add `MarketDataAdapterPort` — the pipeline-facing protocol for market data fetching. This is distinct from the existing `MarketDataPort` which serves the GUI layer with typed DTOs.

Also add `FetchAdapterResult` TypedDict to carry structured cache metadata back from the adapter, enabling `FetchStep` to upsert cache entries with etag/last_modified values.

#### Boundary Inventory

| Surface | Schema Owner | Field Constraints | Extra-Field Policy |
|---------|-------------|-------------------|-------------------|
| Port method `fetch()` | `MarketDataAdapterPort` Protocol | `provider`: str (must match registry key); `data_type`: str ∈ {ohlcv, quote, news, fundamentals}; `criteria`: dict (resolved by CriteriaResolver); `cached_content`: optional bytes; `cached_etag`: optional str; `cached_last_modified`: optional str | N/A (Protocol, not Pydantic) |

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-1 | `MarketDataAdapterPort` defines `async def fetch(*, provider, data_type, criteria, cached_content=None, cached_etag=None, cached_last_modified=None) → FetchAdapterResult` where `FetchAdapterResult` is a TypedDict with keys `content: bytes`, `cache_status: str`, `etag: str \| None`, `last_modified: str \| None` | Spec (meu-pw2-scope §Deliverable 1), refined per Codex review F1 | Type checker catches missing method on implementors |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/core/src/zorivest_core/application/ports.py` | modify | Add `FetchAdapterResult` TypedDict + `MarketDataAdapterPort` Protocol at end of file |

---

### Component 2: Adapter Implementation (Infrastructure Layer)

#### [NEW] [market_data_adapter.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/market_data/market_data_adapter.py)

Concrete implementation of `MarketDataAdapterPort`. Handles:
- URL construction per `data_type` using provider registry configs
- Rate limiting via `PipelineRateLimiter.execute_with_limits()`
- HTTP cache revalidation via `fetch_with_cache()` — returns `FetchAdapterResult` dict
- API key decryption for authenticated providers
- Accepts optional `cached_content`, `cached_etag`, `cached_last_modified` for conditional revalidation

#### Boundary Inventory

| Surface | Schema Owner | Field Constraints | Extra-Field Policy |
|---------|-------------|-------------------|-------------------|
| `fetch()` method | FetchStep.Params validates upstream | provider ∈ PROVIDER_REGISTRY keys; data_type ∈ {ohlcv, quote, news, fundamentals}; criteria contains resolved date ranges; cached_* params optional | N/A |

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-2 | Adapter dispatches correctly for `ohlcv`, `quote`, `news`, `fundamentals` data types (builds appropriate URL per type) and returns `FetchAdapterResult` dict with `content`, `cache_status`, `etag`, `last_modified` keys | Spec (meu-pw2-scope §AC-2), refined per Codex review F1 | Unknown data_type raises ValueError |
| AC-5 | Every provider HTTP call goes through `PipelineRateLimiter.execute_with_limits()` | Spec (meu-pw2-scope §AC-5) | Mock rate limiter verifies call count |
| AC-6 | HTTP ETag/If-Modified-Since headers sent when cached entry has etag/last_modified via `fetch_with_cache()` | Spec (meu-pw2-scope §AC-6) | Mock HTTP client verifies conditional headers |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| URL construction per data_type | Spec | Each data_type maps to a provider-specific endpoint pattern |
| API key retrieval | Local Canon | Same pattern as MarketDataService: UoW → market_provider_settings → encryption.decrypt |
| Unknown provider handling | Spec | Raise KeyError with available provider list (same as `get_provider_config`) |
| OHLCV URL format per provider | Research-backed | Polygon: `/aggs/ticker/{symbol}/range/1/day/{from}/{to}`; Yahoo: yfinance pattern. Adapter builds provider-specific URLs |
| `fetch_with_cache()` `timeout` param | Codex review F2 | `fetch_with_cache()` must pass `timeout` to `client.get()` to compose with `HttpxClient.get(url, headers, timeout)`. Default: 30s |

#### Prerequisite: `fetch_with_cache()` Client Contract Bridge (F2)

> [!IMPORTANT]
> `fetch_with_cache()` currently calls `client.get(url, headers=headers)` but `HttpxClient.get()` requires `timeout` as a mandatory arg. This must be fixed **before** implementing the adapter.

**Fix**: Add `timeout: int = 30` param to `fetch_with_cache()` and pass `timeout=timeout` in the `client.get()` call.

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/infrastructure/src/zorivest_infra/market_data/market_data_adapter.py` | new | `MarketDataProviderAdapter` class (~120 lines) |
| `packages/infrastructure/src/zorivest_infra/market_data/http_cache.py` | modify | Add `timeout` param to `fetch_with_cache()` (~2 lines) |

---

### Component 3: FetchStep Cache Logic (Core Layer)

#### [MODIFY] [fetch_step.py](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/fetch_step.py)

Replace `_check_cache` stub with real implementation:
1. Get `fetch_cache_repo` from `context.outputs`
2. Build deterministic `entity_key` from criteria hash
3. Query `FetchCacheRepository.get_cached(provider, data_type, entity_key)`
4. Check freshness using `FRESHNESS_TTL[data_type]`
5. If `data_type` is `ohlcv` or `quote` and `is_market_closed()`, multiply TTL by 4

After successful fetch (in `execute()`), upsert result to cache.

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-3 | `_check_cache()` returns cached bytes when TTL is fresh, `None` when stale | Spec (meu-pw2-scope §AC-3) | Expired cache entry returns None |
| AC-4 | Cache respects `is_market_closed()` — extends TTL for ohlcv/quote when market is closed | Spec (meu-pw2-scope §AC-4) | During market hours, standard TTL applies; outside hours, 4× TTL |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| TTL values per data_type | Spec | FRESHNESS_TTL dict: quote=60s, ohlcv=3600s, news=1800s, fundamentals=86400s |
| Market-closed TTL multiplier | Spec (meu-pw2-scope §D-2) | 4× multiplier when is_market_closed() returns True |
| Entity key format | Local Canon | SHA-256 of sorted JSON criteria, truncated to 16 chars |
| Cache miss when repo unavailable | Local Canon | Return None gracefully (no crash if fetch_cache_repo not in context) |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/core/src/zorivest_core/pipeline_steps/fetch_step.py` | modify | Replace `_check_cache` stub (~35 lines); add cache-save after fetch (~10 lines) |

---

### Component 4: FetchResult Provenance Fields (Core Layer)

#### [MODIFY] [pipeline.py](file:///p:/zorivest/packages/core/src/zorivest_core/domain/pipeline.py)

Add provenance fields to `FetchResult` dataclass:
- `warnings: list[str]` — for non-fatal issues (rate limit near, slow response, etc.)

Note: `data_type` already exists as a field. The scope also mentions adding it, but it's already present.

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/core/src/zorivest_core/domain/pipeline.py` | modify | Add `warnings` field to FetchResult (~2 lines) |

---

### Component 5: PipelineRunner + main.py Wiring

#### [MODIFY] [pipeline_runner.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/pipeline_runner.py)

Add `fetch_cache_repo` parameter to constructor and inject into context outputs. This expands the constructor from 8→9 keyword params.

#### [MODIFY] [main.py](file:///p:/zorivest/packages/api/src/zorivest_api/main.py)

Wire the adapter and rate limiter:
1. Create `PipelineRateLimiter` with provider limits from PROVIDER_REGISTRY
2. Create `MarketDataProviderAdapter` with http_client, rate_limiter
3. Pass `provider_adapter` (now a real adapter, no longer None) and `fetch_cache_repo` to PipelineRunner

#### PW1 Contract Blast Radius (F5)

> [!IMPORTANT]
> MEU-PW1 froze the runner at 8 kwargs / 8 injected keys, and tests assert these exact counts. PW2 adds `fetch_cache_repo` (9th param) and wires `provider_adapter` to a real adapter (no longer None). The following test suites MUST be updated:
>
> 1. **`tests/unit/test_pipeline_runner_constructor.py`**: Update "8 keyword params" → "9 keyword params" in AC-1/AC-2 descriptions. Add `fetch_cache_repo` to `_make_runner()` helper, expected key sets, and attribute assertions.
> 2. **`tests/integration/test_pipeline_wiring.py`**: Change `test_pipeline_runner_provider_adapter_is_none` → assert `is not None` (now wired). Add `test_pipeline_runner_has_fetch_cache_repo`. Update `expected_keys` set in `test_run_with_inspector_step_populates_outputs` (7→8 non-None deps). Remove assertion `"provider_adapter" not in captured_outputs`.

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-8 | All existing tests continue to pass after wiring changes (including updated PW1 contract tests) | Spec (meu-pw2-scope §AC-8), refined per Codex review F5 | Full regression suite including `test_pipeline_runner_constructor.py` and `test_pipeline_wiring.py` |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/core/src/zorivest_core/services/pipeline_runner.py` | modify | Add `fetch_cache_repo` param (~5 lines) |
| `packages/api/src/zorivest_api/main.py` | modify | Wire adapter, rate limiter, cache repo (~10 lines) |
| `tests/unit/test_pipeline_runner_constructor.py` | modify | Update 8→9 keys, add `fetch_cache_repo` assertions |
| `tests/integration/test_pipeline_wiring.py` | modify | Wire `provider_adapter` check, add `fetch_cache_repo` check, update key counts |

---

### Component 6: Integration Test

#### [NEW] [test_pipeline_fetch_e2e.py](file:///p:/zorivest/tests/integration/test_pipeline_fetch_e2e.py)

End-to-end test: `fetch → transform` pipeline with mocked HTTP.

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-7 | Integration test: fetch→transform pipeline completes with mocked HTTP returning OHLCV JSON | Spec (meu-pw2-scope §AC-7) | Adapter raises on HTTP error |

#### Test Scenarios

1. **Happy path**: Mock HTTP returns OHLCV JSON → FetchStep succeeds → TransformStep receives data
2. **Cache hit**: First call fetches, second call returns cache hit without HTTP
3. **Rate limiter invoked**: Mock rate limiter records call count  
4. **ETag revalidation**: Mock returns 304 → adapter returns cached content
5. **Market-closed TTL extension**: Patch `is_market_closed()` → verify extended TTL

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `tests/integration/test_pipeline_fetch_e2e.py` | new | 5 test functions (~200 lines) |

---

## Out of Scope

- ❌ Market data ORM models beyond existing FetchCacheModel (→ MEU-PW3)
- ❌ Pandera schemas for quotes/news/fundamentals (→ MEU-PW3)
- ❌ Real provider API key wiring — all tests use mocked HTTP
- ❌ Field mappings for non-OHLCV data types (→ MEU-PW3)

---

## BUILD_PLAN.md Audit

> [!IMPORTANT]
> MEU-PW2 row does **NOT** currently exist in the P2.5b table. Only MEU-PW1 and MEU-TD1 are present. The executor must **add** a new MEU-PW2 row with the approved description, then mark it ✅.

Validation (before adding row):

```powershell
rg "MEU-PW2" docs/BUILD_PLAN.md  # Expected: 0 matches (row does not exist yet)
```

Validation (after adding row):

```powershell
rg "MEU-PW2" docs/BUILD_PLAN.md  # Expected: ≥1 match (new row with ✅)
```

Row content: `| MEU-PW2 | fetch-step-integration | 49.5 | [09 §9.4](build-plan/09-scheduling.md) | Create MarketDataProviderAdapter + MarketDataAdapterPort; implement FetchStep._check_cache with TTL + market-hours; wire adapter/rate-limiter/cache-repo in main.py; update PW1 contract tests 8→9 kwargs · Depends on: MEU-PW1 ✅ | ✅ |`

---

## Verification Plan

### 1. Unit Tests (Red → Green)
```powershell
uv run pytest tests/unit/test_fetch_step.py tests/unit/test_market_data_adapter.py -x --tb=short -v *> C:\Temp\zorivest\pytest-pw2-unit.txt; Get-Content C:\Temp\zorivest\pytest-pw2-unit.txt | Select-Object -Last 40
```

### 2. Integration Test
```powershell
uv run pytest tests/integration/test_pipeline_fetch_e2e.py -x --tb=short -v *> C:\Temp\zorivest\pytest-pw2-integration.txt; Get-Content C:\Temp\zorivest\pytest-pw2-integration.txt | Select-Object -Last 40
```

### 3. Type Check
```powershell
uv run pyright packages/ *> C:\Temp\zorivest\pyright-pw2.txt; Get-Content C:\Temp\zorivest\pyright-pw2.txt | Select-Object -Last 30
```

### 4. Lint
```powershell
uv run ruff check packages/ *> C:\Temp\zorivest\ruff-pw2.txt; Get-Content C:\Temp\zorivest\ruff-pw2.txt | Select-Object -Last 20
```

### 5. MEU Gate
```powershell
uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate-pw2.txt; Get-Content C:\Temp\zorivest\validate-pw2.txt | Select-Object -Last 50
```

### 6. Regression (full test suite)
```powershell
uv run pytest tests/ -x --tb=short -v *> C:\Temp\zorivest\pytest-pw2-full.txt; Get-Content C:\Temp\zorivest\pytest-pw2-full.txt | Select-Object -Last 40
```

---

## Open Questions

None — all design decisions resolved during planning:
1. Adapter location → infra layer (dependency rule)
2. Two-layer cache design → application TTL + HTTP conditional requests
3. FetchResult changes → add `warnings` field (data_type already exists)

---

## Research References

- [MEU-PW2 Scope](file:///p:/zorivest/.agent/context/scheduling/meu-pw2-scope.md)
- [09-scheduling.md §9.4](file:///p:/zorivest/docs/build-plan/09-scheduling.md) — FetchStep spec
- [MEU-PW1 Handoff](file:///p:/zorivest/.agent/context/handoffs/) — PipelineRunner constructor expansion
