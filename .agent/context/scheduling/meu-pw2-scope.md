# MEU-PW2: Fetch Step Integration

> **Matrix:** P2.5 item 49.5 · **Slug:** `fetch-step-integration`  
> **Status:** ⬜ Planned · **Effort:** M (1 session)  
> **Depends on:** MEU-PW1 (constructor expansion + main.py wiring)  
> **Unblocks:** Full end-to-end pipeline execution (all 5 step types operational)

---

## Objective

Make `FetchStep` fully operational by creating the `MarketDataProviderAdapter`, implementing the cache check stub, integrating the rate limiter, and connecting HTTP cache revalidation. After this MEU, a pipeline with `fetch → transform → store_report → render → send` completes end-to-end.

---

## Gap Items Covered

| Item | Description | Category | Effort |
|------|-------------|----------|--------|
| W-1 | Create `MarketDataProviderAdapter` (new service) | Wiring | M |
| D-2 | Implement `FetchStep._check_cache()` — wire to FetchCacheRepository + FRESHNESS_TTL | Defect | S |
| D-3 | Integrate `PipelineRateLimiter` into adapter/fetch flow | Defect | S |
| D-4 | Connect `fetch_with_cache()` for HTTP ETag/If-Modified-Since revalidation | Defect | S |

**Total: 4 items** (1 M + 3 S)

---

## Deliverables

### 1. Create MarketDataProviderAdapter (W-1)

**New file:** `packages/core/src/zorivest_core/services/market_data_adapter.py`

#### Why a New Service (Not a Wrapper)

[MarketDataService](file:///p:/zorivest/packages/core/src/zorivest_core/services/market_data_service.py#L59) was designed for the GUI layer. It cannot serve as a pipeline adapter because:

| Aspect | MarketDataService | FetchStep expects |
|--------|-------------------|-------------------|
| **Interface** | `get_quote(ticker)` → `MarketQuote` DTO | `fetch(provider, data_type, criteria)` → `bytes` |
| **Return type** | Typed DTOs | Raw bytes (JSON payload) |
| **Provider selection** | Internal fallback chain | Explicit `provider` param from policy |
| **OHLCV** | ❌ No method | Primary use case |
| **Caching** | None | Must use FetchCacheRepository + HTTP cache |

#### Port Interface

```python
# packages/core/src/zorivest_core/ports/market_data_adapter_port.py
from typing import Protocol

class MarketDataAdapterPort(Protocol):
    """Port for pipeline's market data fetch operations."""

    async def fetch(
        self,
        *,
        provider: str,
        data_type: str,
        criteria: dict,
    ) -> bytes:
        """Fetch raw market data from a specific provider.

        Args:
            provider: Provider key (e.g., 'yahoo', 'polygon', 'ibkr')
            data_type: Data type (e.g., 'ohlcv', 'quote', 'news', 'fundamentals')
            criteria: Resolved criteria dict (date ranges, tickers, etc.)

        Returns:
            Raw JSON response as bytes
        """
        ...
```

#### Implementation Strategy

The adapter should:
1. **Dispatch by data_type** to the correct provider API endpoint
2. **Use the provider's HTTP client** (from MarketDataService's provider registry)
3. **Apply rate limiting** via [PipelineRateLimiter.execute_with_limits()](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/market_data/pipeline_rate_limiter.py#L39)
4. **Use HTTP cache** via [fetch_with_cache()](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/market_data/http_cache.py#L16) for ETag/If-Modified-Since revalidation
5. **Return raw bytes** — the TransformStep handles parsing and validation

#### Key Design Decision: OHLCV Support

MarketDataService has no OHLCV method. Options:
- **(a)** Extend MarketDataService with `get_ohlcv()` and have the adapter delegate
- **(b)** Have the adapter call provider HTTP APIs directly for OHLCV

Option (b) is recommended — the adapter already needs direct HTTP access for rate limiting and cache integration. Adding OHLCV to MarketDataService would create a GUI-layer method that's only used by the pipeline.

### 2. Implement FetchStep._check_cache (D-2)

**File:** [fetch_step.py](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/fetch_step.py) L128-132

Current stub:
```python
async def _check_cache(self, provider: str, data_type: str, criteria: dict) -> bytes | None:
    """Check if cached data satisfies freshness requirements."""
    return None  # TODO: Wire to FetchCacheRepository
```

Replace with:
1. Get `fetch_cache_repo` from `context.outputs`
2. Look up cached entry by `(provider, data_type, criteria_hash)`
3. Check TTL using [FRESHNESS_TTL](file:///p:/zorivest/packages/core/src/zorivest_core/domain/pipeline.py#L221) dict
4. Apply market-hours rule: if data type is `ohlcv` or `quote` and [is_market_closed()](file:///p:/zorivest/packages/core/src/zorivest_core/domain/pipeline.py#L252), extend TTL (no point refreshing when market is closed)
5. Return cached bytes if fresh, else `None`

**New context.outputs dependency:** `fetch_cache_repo` (add to PipelineRunner constructor in main.py — extends PW1's work)

### 3. Integrate PipelineRateLimiter (D-3)

**Files:**
- [fetch_step.py](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/fetch_step.py) (`_fetch_from_provider` method)
- Or: `market_data_adapter.py` (adapter handles rate limiting internally)

**Preferred approach:** Rate limiting belongs in the adapter, not in FetchStep. The adapter wraps all HTTP calls through [PipelineRateLimiter.execute_with_limits()](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/market_data/pipeline_rate_limiter.py#L39).

The adapter's constructor takes a `PipelineRateLimiter` instance:

```python
class MarketDataProviderAdapter:
    def __init__(self, http_client, rate_limiter: PipelineRateLimiter):
        self._client = http_client
        self._rate_limiter = rate_limiter

    async def fetch(self, *, provider, data_type, criteria) -> bytes:
        provider_config = await self._get_provider_config(provider)
        url = self._build_url(provider, data_type, criteria)

        return await self._rate_limiter.execute_with_limits(
            provider=provider,
            rate_per_minute=provider_config.rate_limit,
            coro=self._do_fetch(url),
        )
```

### 4. Connect HTTP Cache Revalidation (D-4)

**Integration:** The adapter uses [fetch_with_cache()](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/market_data/http_cache.py#L16) to make HTTP requests. This provides ETag/If-Modified-Since header handling automatically:

```python
async def _do_fetch(self, url: str, cached: FetchCacheModel | None) -> bytes:
    from zorivest_infra.market_data.http_cache import fetch_with_cache
    data, cache_status = await fetch_with_cache(self._client, url, cached)
    return json.dumps(data).encode()
```

### 5. Wire in main.py

**File:** [main.py](file:///p:/zorivest/packages/api/src/zorivest_api/main.py)

Add to the PipelineRunner construction (extending PW1's wiring):

```python
rate_limiter = PipelineRateLimiter(global_concurrency=5)
provider_adapter = MarketDataProviderAdapter(http_client, rate_limiter)

pipeline_runner = PipelineRunner(
    ...,  # existing PW1 params
    provider_adapter=provider_adapter,
    fetch_cache_repo=uow.fetch_cache,
)
```

### 6. Integration Test

**New file:** `tests/integration/test_pipeline_fetch_e2e.py`

Test: A 2-step pipeline (`fetch → transform`) completes end-to-end. Mock the HTTP client to return test OHLCV JSON. Verify:
- FetchResult has correct content_hash
- Cache hit returns cached data on second call
- Rate limiter is invoked
- TransformStep receives the fetched data via step chaining

---

## Bonus Fix: FetchResult Provenance Fields (from spec-vs-code-audit)

The spec (§9.4d) defines `FetchResult` with `raw_payload: dict`, `content_type`, `warnings`, `fetched_at`. Current code uses `content: bytes` and lacks 3 fields. While in this file:

- Add `data_type: str` (for downstream routing)
- Add `warnings: list[str]`  
- Keep `content: bytes` (better for pipeline — raw bytes is more flexible than dict)

---

## Files Changed

| File | Change Type | Package |
|------|-------------|---------|
| `market_data_adapter.py` | **NEW** | core/services |
| `market_data_adapter_port.py` | **NEW** | core/ports |
| `fetch_step.py` | Modify (_check_cache impl) | core/pipeline_steps |
| `pipeline.py` | Modify (FetchResult fields) | core/domain |
| `main.py` | Modify (wire adapter) | api |
| `test_pipeline_fetch_e2e.py` | **NEW** | tests/integration |

**Blast radius:** 3 modified + 3 new = 6 files across 3 packages.

---

## Acceptance Criteria

- **AC-1:** `MarketDataProviderAdapter` implements `MarketDataAdapterPort` with `fetch(provider, data_type, criteria) → bytes`
- **AC-2:** Adapter dispatches correctly for `ohlcv`, `quote`, `news`, `fundamentals` data types
- **AC-3:** `FetchStep._check_cache()` returns cached bytes when TTL is fresh, `None` when stale
- **AC-4:** Cache respects `is_market_closed()` for market-session-aware TTL extension
- **AC-5:** Rate limiter is invoked for every provider HTTP call (`execute_with_limits()`)
- **AC-6:** HTTP ETag/If-Modified-Since headers sent when cached entry has etag/last_modified
- **AC-7:** Integration test: fetch→transform pipeline completes with mocked HTTP
- **AC-8:** All existing tests continue to pass

---

## What This MEU Does NOT Do

- ❌ Does not create market data ORM models (→ MEU-PW3)
- ❌ Does not add Pandera schemas for quotes/news/fundamentals (→ MEU-PW3)
- ❌ Does not add field mappings for non-OHLCV data types (→ MEU-PW3)
- ❌ Does not wire real provider API keys — tests use mocked HTTP
