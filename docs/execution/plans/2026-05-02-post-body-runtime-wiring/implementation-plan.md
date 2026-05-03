---
project: "2026-05-02-post-body-runtime-wiring"
date: "2026-05-02"
source: "docs/build-plan/08a-market-data-expansion.md §8a.8, docs/BUILD_PLAN.md §P1.5a, .agent/context/meu-registry.md, prior handoff (2026-05-02-market-data-builders-extractors)"
meus: ["MEU-189"]
status: "draft"
template_version: "2.0"
---

# Implementation Plan: POST-Body Runtime Wiring

> **Project**: `2026-05-02-post-body-runtime-wiring`
> **Build Plan Section(s)**: 08a-market-data-expansion.md §8a.8 (POST-Body Runtime Wiring), BUILD_PLAN.md §P1.5a
> **Status**: `draft`

---

## Goal

Wire the POST-body runtime dispatch layer so that providers classified as `builder_mode="post_body"` (OpenFIGI, SEC API, TradingView) can actually execute HTTP POST requests through the market data adapter and pipeline fetch infrastructure. Currently, `RequestSpec` dataclass and `build_request()` methods exist on all three builders (MEU-186), and extractors for their response shapes exist (MEU-188), but the adapter and `fetch_with_cache()` are hardcoded to GET-only. This MEU bridges that gap.

Additionally resolves three known issues:
- **[MKTDATA-OPENFIGI405]**: OpenFIGI returns 405 because test flow sends GET to POST-only `/v3/mapping` endpoint
- **[MKTDATA-TRADINGVIEW-NOPUBLICAPI]**: POST runtime blocker — builders/extractors exist but can't execute
- **[MKTDATA-POLYGON-REBRAND]**: Investigation of 405 error — verify URL construction correctness

---

## User Review Required

> [!IMPORTANT]
> **Design Decision: fetch_with_cache POST extension vs. separate function.**
> The plan extends `fetch_with_cache()` with optional `method` and `json_body` parameters (backward-compatible). Alternative was creating a separate `fetch_post()` function, but that would duplicate cache revalidation logic. The extension approach keeps a single function with POST support gated by parameters.
>
> **Polygon 405 investigation** is included as a diagnostic task. If the root cause is NOT a URL construction error but requires domain migration (api.polygon.io → api.massive.com), that migration will be deferred to a standalone mini-MEU.

---

## Proposed Changes

### MEU-189: POST-Body Runtime Wiring

#### Spec Sufficiency Table

| Behavior / Contract | Source Type | Source | Resolved? | Notes |
|---|---|---|---|---|
| POST-body providers must send POST method with JSON body | Spec | 08a §8a.8 (updated) + capabilities registry `builder_mode="post_body"` | ✅ | OpenFIGI, SEC API, TradingView |
| `fetch_with_cache()` must support POST with JSON body | Local Canon | `http_cache.py` line 69 — currently hardcoded `client.get()` | ✅ | Extend with `method` and `json_body` params |
| Adapter must detect POST providers and use `build_request()` | Local Canon | `url_builders.py` RequestSpec + `build_request()` methods | ✅ | Check `hasattr(builder, 'build_request')` or use capabilities registry |
| OpenFIGI test must use POST to `/v3/mapping` | Research-backed | OpenFIGI API docs: v3/mapping is POST-only, `X-OPENFIGI-APIKEY` header | ✅ | [MKTDATA-OPENFIGI405] |
| OpenFIGI requires `Content-Type: application/json` | Research-backed | OpenFIGI API docs | ✅ | Must be set on POST requests |
| POST requests skip ETag/If-None-Match cache revalidation | Research-backed | HTTP/1.1 RFC 9110 §9.3.3: POST responses are not cacheable by default | ✅ | POST path skips conditional headers |
| `HttpxClient.post()` already exists | Local Canon | `service_factory.py:71-79` | ✅ | No changes needed to HttpxClient |

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-1 | `fetch_with_cache()` accepts `method="POST"` and `json_body` params; dispatches to `client.post()` with JSON body | Spec (08a §8a.8) + Local Canon | `method="PATCH"` raises ValueError |
| AC-2 | `fetch_with_cache()` with `method="GET"` (default) behaves identically to current implementation | Local Canon | Existing tests remain green |
| AC-3 | POST requests skip ETag/If-Modified-Since conditional headers | Research-backed (RFC 9110 §9.3.3) | POST with cached_etag set does NOT send If-None-Match |
| AC-4 | POST responses still capture ETag/Last-Modified from response headers | Spec (08a §8a.8) | POST returning ETag header → captured in result |
| AC-5 | POST non-2xx responses raise `HttpFetchError` same as GET | Local Canon | POST returning 400 → HttpFetchError |
| AC-6 | `MarketDataProviderAdapter._do_fetch()` accepts `method` and `json_body` params | Local Canon | — |
| AC-7 | `MarketDataProviderAdapter.fetch()` detects POST-body providers via `hasattr(builder, 'build_request')`, calls `build_request()`, and passes `RequestSpec.method` + `RequestSpec.body` to `_do_fetch()` | Spec (08a §8a.8) + Local Canon | GET provider still uses `build_url()` path |
| AC-8 | Adapter multi-ticker path (`_fetch_multi_ticker`) supports POST dispatch | Spec (08a §8a.8) | Multi-ticker POST provider uses build_request per ticker |
| AC-9 | `provider_connection_service` OpenFIGI test uses POST with `[{"idType":"TICKER","idValue":"IBM"}]` body | Research-backed (OpenFIGI v3 API docs) + [MKTDATA-OPENFIGI405] | OpenFIGI GET request → 405 (this is the current bug) |
| AC-10 | `provider_connection_service` SEC API test validates existing GET path still works (test_endpoint is GET `/mapping/ticker/AAPL`) | Research-backed (SEC API docs: GET-only mapping endpoints) | No change needed — SEC API test_endpoint is GET |
| AC-11 | Polygon URL construction verified — no double-path issue | [MKTDATA-POLYGON-REBRAND] | `base_url + test_endpoint` produces valid URL |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/infrastructure/src/zorivest_infra/market_data/http_cache.py` | modify | Add `method` and `json_body` params to `fetch_with_cache()`; POST dispatch; skip conditional headers for POST |
| `packages/infrastructure/src/zorivest_infra/market_data/market_data_adapter.py` | modify | Extend `_do_fetch()` with POST params; detect POST builders in `fetch()` and `_fetch_multi_ticker()` |
| `packages/core/src/zorivest_core/services/provider_connection_service.py` | modify | Add `_test_openfigi_post()` method for OpenFIGI POST test flow |
| `tests/unit/test_http_cache.py` | modify | Add POST dispatch tests (AC-1 through AC-5) |
| `tests/unit/test_market_data_adapter.py` | modify | Add POST provider dispatch tests (AC-6 through AC-8) |
| `tests/unit/test_provider_connection_service.py` | modify | Add OpenFIGI POST test (AC-9), verify Polygon URL (AC-11) |

---

## Out of Scope

- MEU-190/191 (service methods) — depends on this MEU; next project
- TradingView exchange routing, rate limiting, multi-ticker batching — deferred per [MKTDATA-TRADINGVIEW-NOPUBLICAPI]
- Yahoo Finance expansion (fundamentals/earnings/dividends/splits) — separate mini-MEU per [MKTDATA-YAHOO-UNOFFICIAL]
- Polygon domain migration (api.polygon.io → api.massive.com) — if 405 root cause is domain/auth, not URL construction
- OpenFIGI response extractor changes — already implemented in MEU-188

---

## BUILD_PLAN.md Audit

This project updates MEU-189 status from ⬜ to ✅ upon completion. MEU-185 through MEU-188 are already ✅ in both BUILD_PLAN.md and the MEU registry (corrected 2026-05-02). No additional registry corrections needed beyond MEU-189.

```powershell
rg "MEU-189" docs/BUILD_PLAN.md  # Expected: 1 match (status row to update)
```

---

## Verification Plan

### 1. Unit Tests — POST Dispatch
```powershell
uv run pytest tests/unit/test_http_cache.py tests/unit/test_market_data_adapter.py tests/unit/test_provider_connection_service.py -x --tb=short -v *> C:\Temp\zorivest\pytest-189.txt; Get-Content C:\Temp\zorivest\pytest-189.txt | Select-Object -Last 40
```

### 2. Full Regression
```powershell
uv run pytest tests/ -x --tb=short -q *> C:\Temp\zorivest\pytest-full.txt; Get-Content C:\Temp\zorivest\pytest-full.txt | Select-Object -Last 20
```

### 3. Type Check
```powershell
uv run pyright packages/ *> C:\Temp\zorivest\pyright.txt; Get-Content C:\Temp\zorivest\pyright.txt | Select-Object -Last 30
```

### 4. Lint
```powershell
uv run ruff check packages/ *> C:\Temp\zorivest\ruff.txt; Get-Content C:\Temp\zorivest\ruff.txt | Select-Object -Last 20
```

### 5. Anti-Placeholder
```powershell
rg "TODO|FIXME|NotImplementedError" packages/infrastructure/src/zorivest_infra/market_data/ packages/core/src/zorivest_core/services/provider_connection_service.py *> C:\Temp\zorivest\placeholder.txt; Get-Content C:\Temp\zorivest\placeholder.txt
```

### 6. MEU Gate
```powershell
uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate.txt; Get-Content C:\Temp\zorivest\validate.txt | Select-Object -Last 50
```

---

## Open Questions

> [!WARNING]
> 1. **Polygon 405 root cause**: If curl testing reveals the 405 is NOT a URL construction issue but a domain/auth migration problem, should we defer the full Polygon migration to a separate MEU or attempt it in this project? **Recommendation**: Defer to standalone mini-MEU if it requires changes beyond registry `base_url` update.
> 2. **SEC API test_endpoint**: The current `test_endpoint="/mapping/ticker/AAPL"` is a GET endpoint that works. The POST endpoints (`/LATEST/search-index`) are for actual data retrieval, not connection testing. Should the SEC API connection test remain GET-based? **Recommendation**: Yes — keep GET test for connection validation; POST path is tested via adapter unit tests.

---

## Research References

- [OpenFIGI API v3 docs](https://www.openfigi.com/api) — POST-only `/v3/mapping`, header format `X-OPENFIGI-APIKEY`
- [RFC 9110 §9.3.3](https://www.rfc-editor.org/rfc/rfc9110#section-9.3.3) — POST responses not cacheable by default
- Known issues: [MKTDATA-OPENFIGI405], [MKTDATA-POLYGON-REBRAND], [MKTDATA-TRADINGVIEW-NOPUBLICAPI]
- Prior handoff: `.agent/context/handoffs/2026-05-02-market-data-builders-extractors-handoff.md` §POST-Body Runtime Deferral
