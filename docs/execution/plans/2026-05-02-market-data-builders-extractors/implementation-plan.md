---
project: "2026-05-02-market-data-builders-extractors"
phase: "8a"
layer: "2+3"
meus: ["MEU-185", "MEU-186", "MEU-187", "MEU-188"]
status: "in_progress"
template_version: "2.0"
build_plan_section: "08a-market-data-expansion §8a.4–8a.7"
predecessor: "2026-05-02-market-data-foundation (MEU-182a, 182, 183, 184)"
---

# Implementation Plan — Market Data Builders & Extractors

> **Project:** `2026-05-02-market-data-builders-extractors`
> **Phase:** 8a Layer 2 (URL Builders) + Layer 3 (Extractors + Field Mappings)
> **MEUs:** MEU-185, MEU-186, MEU-187, MEU-188
> **Predecessor:** MEU-184 (`provider-capabilities`) — ✅ complete

---

## 1. Objective

Wire URL construction for all 11 API-key providers and response extraction for 9 of 11 by implementing:
- **9 new URL builders** (5 simple-GET + 4 special-pattern) → MEU-185, MEU-186
- **Standard response extractors** for 5 simple-GET providers + ~25 field mappings → MEU-187
- **Complex response extractors** for 4 providers with non-standard shapes + ~20 field mappings → MEU-188

After this project, all 11 providers can construct API request URLs, and 9 of 11 can parse response envelopes into flat record dicts ready for field mapping. OpenFIGI and SEC API extractors are deferred to MEU-189.

---

## 2. Scope & Constraints

### In Scope
- 9 new builder classes + registry entries in `url_builders.py`
- `RequestSpec` dataclass for POST-body builders (OpenFIGI, SEC API)
- ~10 new extractor functions in `response_extractors.py`
- ~45 new field mapping tuples in `field_mappings.py`
- `_PROVIDER_SLUG_MAP` updates for all 9 new providers
- Existing builder/extractor tests preserved (22 builder tests + 18 extractor tests)

### Out of Scope
- MEU-189 (POST-body extractors for OpenFIGI/SEC API) — next project
- Service method wiring (MEU-190, 191)
- API routes / MCP actions (MEU-192)
- Live API calls / integration testing against real endpoints

### Known Issues Affecting This Work
- **MKTDATA-OPENFIGI405**: OpenFIGI requires POST, not GET. Addressed by `RequestSpec` + `build_request_body()` in MEU-186. [Spec + Research-backed]
- **Finnhub OHLCV 403**: Free tier blocks `/stock/candle` since 2024. Builder will construct the URL but docstring documents the free-tier limitation. [Research-backed]
- **Alpaca base URL**: Data API lives at `data.alpaca.markets`, not `api.alpaca.markets` (which is trading API). Builder uses data API host internally. [Research-backed]
- **EODHD exchange suffix**: Endpoints require `{symbol}.{exchange}` format (e.g., `AAPL.US`). Builder defaults to `.US`, configurable via criteria. [Research-backed]

---

## 3. Architecture

### 3.1 RequestSpec for POST Builders

```python
@dataclass(frozen=True)
class RequestSpec:
    """HTTP request specification for providers requiring POST bodies."""
    method: Literal["GET", "POST"] = "GET"
    url: str = ""
    body: dict[str, Any] | list[dict[str, Any]] | None = None
```

POST-body builders (OpenFIGI, SEC API, TradingView) implement a `build_request()` method on their concrete classes returning `RequestSpec`. Adapter-level runtime dispatch (`_do_fetch()` → POST, `fetch_with_cache()` → POST support) is deferred to MEU-189; this project delivers the builder-side contract only.

### 3.2 Builder Architecture Families

| Mode | Builders | Pattern |
|------|----------|---------|
| `simple_get` | Alpaca, FMP, EODHD, API Ninjas, Tradier + existing Yahoo, Polygon, Finnhub | `base_url + path + query_params` |
| `function_get` | Alpha Vantage | `base_url?function=XXX&symbol=YYY` |
| `dataset_get` | Nasdaq Data Link | `/datatables/{vendor}/{table}.json?ticker=X` |
| `post_body` | OpenFIGI, SEC API, TradingView | `POST base_url/endpoint` + JSON body |

### 3.3 Extractor Shape Families

| Shape | Providers | Pattern |
|-------|-----------|---------|
| `root_array` | FMP, API Ninjas, EODHD (eod) | Top-level `[{...}, ...]` |
| `root_object` | EODHD (fundamentals), Tradier | Top-level `{key: value}` |
| `wrapper_array` | FMP (historical), Polygon | `{historical: [...]}` or `{results: [...]}` |
| `symbol_keyed_dict` | Alpaca | `{bars: {AAPL: [{...}]}}` |
| `named_section_object` | Alpha Vantage | `{"Time Series (Daily)": {"2024-01-01": {...}}}` |
| `parallel_arrays` | Finnhub candles, Nasdaq DL | `{c:[], h:[], l:[], o:[], t:[], v:[]}` |

---

## 4. Acceptance Criteria

### MEU-185: Simple GET Builders

| AC | Description | Source | Test(s) |
|----|-------------|--------|---------|
| AC-1 | `AlpacaUrlBuilder` produces correct URLs for quote (snapshot), ohlcv (bars), news endpoints using `data.alpaca.markets` host | Spec §8a.4 | `test_alpaca_url_builder_*` |
| AC-2 | `FMPUrlBuilder` produces correct URLs for quote, ohlcv, fundamentals, earnings, news, dividends, splits | Spec §8a.4 | `test_fmp_url_builder_*` |
| AC-3 | `EODHDUrlBuilder` produces correct URLs with `.US` exchange suffix for ohlcv, fundamentals, news, dividends, splits | Spec §8a.4 | `test_eodhd_url_builder_*` |
| AC-4 | `APINinjasUrlBuilder` produces correct URLs for quote, earnings, insider | Spec §8a.4 | `test_api_ninjas_url_builder_*` |
| AC-5 | `TradierUrlBuilder` produces correct URLs for quote (multi-symbol), ohlcv | Spec §8a.4 | `test_tradier_url_builder_*` |
| AC-6 | All 5 builders registered in `_URL_BUILDER_REGISTRY` and returned by `get_url_builder()` | Spec §8a.4 | `test_get_url_builder_*` |

### MEU-186: Special-Pattern Builders

| AC | Description | Source | Test(s) |
|----|-------------|--------|---------|
| AC-7 | `AlphaVantageUrlBuilder` uses `?function=X&symbol=Y` dispatch for quote, ohlcv, fundamentals, earnings, insider | Spec §8a.5 | `test_alpha_vantage_url_builder_*` |
| AC-8 | `NasdaqDataLinkUrlBuilder` uses `/datatables/{vendor}/{table}.json` pattern for fundamentals | Spec §8a.5 | `test_nasdaq_dl_url_builder_*` |
| AC-9 | `OpenFIGIUrlBuilder.build_request()` returns `RequestSpec(method="POST", url=..., body=[...])` for identifier_mapping | Spec §8a.5 | `test_openfigi_url_builder_*` |
| AC-10 | `SECAPIUrlBuilder.build_request()` returns `RequestSpec(method="POST", url=..., body={...})` for fundamentals, insider | Spec §8a.5 | `test_sec_api_url_builder_*` |
| AC-11 | `RequestSpec` frozen dataclass with method, url, body fields; defaults to `method="GET"`, `body=None` | Research-backed | `test_request_spec_*` |
| AC-12 | All 4 builders registered in `_URL_BUILDER_REGISTRY` | Spec §8a.5 | `test_get_url_builder_*` (extended) |

### MEU-187: Standard Extractors

| AC | Description | Source | Test(s) |
|----|-------------|--------|---------|
| AC-13 | Alpaca extractor handles `symbol_keyed_dict` (multi-symbol) and flat list (single-symbol) for bars and snapshots | Research-backed | `test_alpaca_extractor_*` |
| AC-14 | FMP extractor handles root_array for quotes/earnings and `{historical: [...]}` wrapper for ohlcv/dividends/splits | Spec §8a.6 | `test_fmp_extractor_*` |
| AC-15 | EODHD extractor handles root_array for EOD and nested `{General: {}, Highlights: {}}` sections for fundamentals | Spec §8a.6 | `test_eodhd_extractor_*` |
| AC-16 | API Ninjas extractor handles root_object (quote) and root_array (earnings, insider) | Spec §8a.6 | `test_api_ninjas_extractor_*` |
| AC-17 | Tradier extractor handles dict→list collapse (`{quotes: {quote: {...}}}` vs `{quotes: {quote: [{...}]}}`) | Research-backed | `test_tradier_extractor_*` |
| AC-18 | ~25 field mapping tuples added to `FIELD_MAPPINGS` for (provider, data_type) combinations | Spec §8a.6 | `test_field_mappings_*` (extended) |
| AC-19 | `_PROVIDER_SLUG_MAP` updated with all 9 new provider display names → slugs | Local Canon | `test_slug_map_*` |

### MEU-188: Complex Extractors

| AC | Description | Source | Test(s) |
|----|-------------|--------|---------|
| AC-20 | Alpha Vantage OHLCV extractor iterates date-keyed dicts (`{"2024-01-01": {"1. open": "150"}}`) and strips `"N. "` prefix from keys | Spec §8a.7 | `test_alpha_vantage_extractor_ohlcv` |
| AC-21 | Alpha Vantage rate-limit detector identifies HTTP 200 + `{"Note": "..."}` or `{"Information": "..."}` as throttled → returns empty list + warning log | Research-backed | `test_alpha_vantage_rate_limit_*` |
| AC-22 | Finnhub candle extractor zips parallel arrays `{c:[], h:[], l:[], o:[], t:[], v:[]}` into record dicts | Spec §8a.7 | `test_finnhub_extractor_candles` |
| AC-23 | Nasdaq Data Link extractor zips `column_names` with `data` rows from `{datatable: {data: [...], columns: [...]}}` | Spec §8a.7 | `test_nasdaq_dl_extractor_*` |
| AC-24 | Polygon timestamp extractor applies `t / 1000` to millisecond UNIX timestamps before `datetime.fromtimestamp()` conversion | Spec §8a.7 | `test_polygon_extractor_timestamp_*` |
| AC-25 | Alpha Vantage earnings CSV extractor parses CSV bytes (returned even when `datatype=json`) into record dicts with proper column mapping | Spec §8a.7 | `test_alpha_vantage_extractor_earnings_csv` |
| AC-26 | ~20 field mapping tuples added for complex providers (Alpha Vantage, Finnhub extended, Nasdaq DL, Polygon timestamps) | Spec §8a.7 | `test_field_mappings_*` (extended) |

---

## 5. Implementation Tasks

### Task 1: RequestSpec + Infrastructure (MEU-186 prerequisite)
- Add `RequestSpec` frozen dataclass to `url_builders.py`
- Add `build_request()` method to concrete POST builder classes (OpenFIGI, SEC API, TradingView) — not on the `UrlBuilder` Protocol (runtime dispatch deferred to MEU-189)
- **Files:** `url_builders.py`
- **Tests:** `test_request_spec_*` (3 tests)

### Task 2: Simple GET Builders (MEU-185)
- Implement `AlpacaUrlBuilder` (3 data types: quote/snapshot, ohlcv/bars, news)
- Implement `FMPUrlBuilder` (7 data types: quote, ohlcv, fundamentals, earnings, news, dividends, splits)
- Implement `EODHDUrlBuilder` (5 data types: ohlcv, fundamentals, news, dividends, splits)
- Implement `APINinjasUrlBuilder` (3 data types: quote, earnings, insider)
- Implement `TradierUrlBuilder` (2 data types: quote, ohlcv)
- Register all 5 in `_URL_BUILDER_REGISTRY`
- **Files:** `url_builders.py`
- **Tests:** ~40 tests across 5 builder test classes

### Task 3: Special-Pattern Builders (MEU-186)
- Implement `AlphaVantageUrlBuilder` (function-dispatch: 5 data types)
- Implement `NasdaqDataLinkUrlBuilder` (dataset/table: 1 data type)
- Implement `OpenFIGIUrlBuilder` (POST-body: 1 data type) with `build_request()`
- Implement `SECAPIUrlBuilder` (POST-body: 2 data types) with `build_request()`
- Register all 4 in `_URL_BUILDER_REGISTRY`
- **Files:** `url_builders.py`
- **Tests:** ~24 tests across 4 builder test classes

### Task 4: Provider Slug Map + Standard Extractors (MEU-187)
- Update `_PROVIDER_SLUG_MAP` with 9 new provider entries
- Implement extractors: `_alpaca_*`, `_fmp_*`, `_eodhd_*`, `_api_ninjas_*`, `_tradier_*`
- Handle Tradier dict→list collapse and Alpaca symbol-keyed dict
- **Files:** `response_extractors.py`, `field_mappings.py`
- **Tests:** ~40 tests across 5 extractor test classes + slug map tests

### Task 5: Standard Field Mappings (MEU-187)
- Add ~25 field mapping tuples to `FIELD_MAPPINGS` for new simple-GET providers
- Cover: quote, ohlcv, news, fundamentals, earnings, dividends, splits, insider
- **Files:** `field_mappings.py`
- **Tests:** ~10 field mapping tests

### Task 6: Complex Extractors (MEU-188)
- Implement Alpha Vantage extractors (date-keyed dict + prefix stripping, rate-limit detection, CSV earnings parser)
- Implement Finnhub candle extractor (parallel array zip)
- Implement Nasdaq Data Link extractor (column_names + data zip)
- Implement Polygon timestamp normalizer (`t / 1000` for ms UNIX timestamps)
- Add Finnhub OHLCV field mapping
- **Files:** `response_extractors.py`
- **Tests:** ~30 tests across 4 extractor test classes (AV, Finnhub, Nasdaq DL, Polygon)

### Task 7: Complex Field Mappings (MEU-188)
- Add ~20 field mapping tuples for complex providers
- Alpha Vantage: quote, ohlcv, fundamentals, earnings (CSV), insider
- Finnhub: ohlcv (candle), earnings, insider, economic_calendar
- Nasdaq DL: fundamentals
- Polygon: timestamp-normalized ohlcv/quote
- **Files:** `field_mappings.py`
- **Tests:** ~10 field mapping tests

---

## 6. Verification Plan

```powershell
# Unit tests — all builder, extractor, and mapping tests
uv run pytest tests/unit/test_url_builders.py tests/unit/test_response_extractors.py tests/unit/test_field_mappings.py -x --tb=short -v *> C:\Temp\zorivest\pytest-builders-extractors.txt; Get-Content C:\Temp\zorivest\pytest-builders-extractors.txt | Select-Object -Last 50

# Type check
uv run pyright packages/ *> C:\Temp\zorivest\pyright.txt; Get-Content C:\Temp\zorivest\pyright.txt | Select-Object -Last 30

# Lint
uv run ruff check packages/ *> C:\Temp\zorivest\ruff.txt; Get-Content C:\Temp\zorivest\ruff.txt | Select-Object -Last 20

# MEU gate
uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate.txt; Get-Content C:\Temp\zorivest\validate.txt | Select-Object -Last 50

# Anti-placeholder scan
rg "TODO|FIXME|NotImplementedError" packages/infrastructure/src/zorivest_infra/market_data/ *> C:\Temp\zorivest\placeholder-scan.txt; Get-Content C:\Temp\zorivest\placeholder-scan.txt
```

---

## 7. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Alpaca data API URL differs from trading API | Confirmed | High — wrong domain = all requests fail | Builder uses `data.alpaca.markets` internally; documented in docstring |
| Alpha Vantage CSV earnings response | Confirmed | Medium — JSON parser crashes | CSV extractor with fallback; separate from JSON path |
| Tradier dict→list collapse | Confirmed | Medium — TypeError on iteration | `isinstance(x, list)` guard in every response path |
| EODHD exchange suffix mismatch | Low | Medium — 404 for non-US symbols | Default `.US`, configurable via `criteria["exchange"]` |
| Finnhub OHLCV 403 on free tier | Confirmed | Low — builder still works for paid users | Documented in docstring; free-tier users use Alpaca |

---

## 8. File Change Summary

| File | Action | MEU | Estimated Lines |
|------|--------|-----|-----------------|
| `packages/infrastructure/src/zorivest_infra/market_data/url_builders.py` | modify | 185, 186 | +350 |
| `packages/infrastructure/src/zorivest_infra/market_data/response_extractors.py` | modify | 187, 188 | +300 |
| `packages/infrastructure/src/zorivest_infra/market_data/field_mappings.py` | modify | 187, 188 | +200 |
| `tests/unit/test_url_builders.py` | modify | 185, 186 | +500 |
| `tests/unit/test_response_extractors.py` | modify | 187, 188 | +400 |
| `tests/unit/test_field_mappings.py` | modify | 187, 188 | +150 |
| `docs/BUILD_PLAN.md` | modify | all | ~5 |

---

## Addendum: Yahoo OHLCV Expansion (2026-05-02)

**Context:** [MKTDATA-YAHOO-UNOFFICIAL] known issue identified that Yahoo Finance URL builder already supported ohlcv but lacked an extractor and field mapping. Since this uses the same v8/chart parallel-array zip pattern implemented for Finnhub in MEU-188, it was added as a natural extension.

### Additional Acceptance Criteria

| AC | Description | Source | Test(s) |
|----|-------------|--------|---------|
| AC-Y1 | `_yahoo_ohlcv` extractor zips `chart.result[0].timestamp` + `indicators.quote[0]` arrays into flat dicts | Known issue + Spec §8a.7 pattern | `TestYahooOHLCVExtraction::test_yahoo_ohlcv_parallel_arrays_zipped` |
| AC-Y2 | Single-bar response (range=1d) produces one record | Known issue | `TestYahooOHLCVExtraction::test_yahoo_ohlcv_single_bar` |
| AC-Y3 | Empty timestamps → empty list | Known issue | `TestYahooOHLCVExtraction::test_yahoo_ohlcv_empty_timestamps` |
| AC-Y4 | Missing indicators block → empty list | Known issue | `TestYahooOHLCVExtraction::test_yahoo_ohlcv_missing_indicators` |
| AC-Y5 | None values (market-closed bars) preserved | Known issue | `TestYahooOHLCVExtraction::test_yahoo_ohlcv_none_values_preserved` |
| AC-Y6 | Pre-extracted list (multi-ticker adapter) → pass-through | Known issue | `TestYahooOHLCVExtraction::test_yahoo_ohlcv_pre_extracted_list` |
| AC-Y7 | `("yahoo", "ohlcv")` field mapping registered with identity mapping | Known issue | `TestFieldMappingRegistry::test_provider_mapping_exists[yahoo-ohlcv]`, `TestOhlcvMappings::test_yahoo_ohlcv_mapping` |

### Additional Files Changed

| File | Change |
|------|--------|
| `response_extractors.py` | +54 lines: `_yahoo_ohlcv()` extractor |
| `field_mappings.py` | +8 lines: `("yahoo", "ohlcv")` identity mapping |
| `tests/unit/test_response_extractors.py` | +176 lines: 6 tests in `TestYahooOHLCVExtraction` |
| `tests/unit/test_field_mappings.py` | +27 lines: `TestOhlcvMappings` class + registry parametrize |

---

## Addendum: TradingView Scanner Expansion (2026-05-02)

**Context:** [MKTDATA-TRADINGVIEW-NOPUBLICAPI] known issue identified that TradingView is already registered as a free provider with a working connection test, but lacked URL builder, extractors, and field mappings for data pipeline integration. Since the scanner API uses POST with JSON body (same `RequestSpec` pattern as OpenFIGI/SecApi from MEU-186), quote and fundamentals were added as a natural extension.

### Additional Acceptance Criteria

| AC | Description | Source | Test(s) |
|----|-------------|--------|---------|
| AC-TV1 | `TradingViewUrlBuilder.build_request()` returns `RequestSpec(method="POST")` with scanner columns for quote | Known issue | `TestTradingViewUrlBuilder::test_tradingview_quote_request` |
| AC-TV2 | Fundamentals request includes fundamental scanner columns | Known issue | `TestTradingViewUrlBuilder::test_tradingview_fundamentals_request` |
| AC-TV3 | Ticker included in POST body filter | Known issue | `TestTradingViewUrlBuilder::test_tradingview_ticker_filter` |
| AC-TV4 | Exchange routing via `criteria["exchange"]` | Known issue | `TestTradingViewUrlBuilder::test_tradingview_exchange_criteria` |
| AC-TV5 | `build_url()` fallback returns POST URL string | Known issue | `TestTradingViewUrlBuilder::test_tradingview_build_url_fallback` |
| AC-TV6 | Builder registered in `_URL_BUILDER_REGISTRY` | Known issue | `TestTradingViewUrlBuilder::test_tradingview_registered_in_registry` |
| AC-TV7 | Quote extractor zips scanner `{data: [{s, d}]}` with column names | Known issue | `TestTradingViewQuoteExtractor::test_tradingview_quote_scanner_response` |
| AC-TV8 | Multi-ticker response produces multiple records | Known issue | `TestTradingViewQuoteExtractor::test_tradingview_quote_multi_ticker` |
| AC-TV9 | Empty scanner response → empty list | Known issue | `TestTradingViewQuoteExtractor::test_tradingview_quote_empty_data` |
| AC-TV10 | Fundamentals extractor with market_cap and key metrics | Known issue | `TestTradingViewFundamentalsExtractor::test_tradingview_fundamentals_scanner_response` |
| AC-TV11 | `("tradingview", "quote")` field mapping registered (identity) | Known issue | `TestFieldMappingRegistry::test_provider_mapping_exists[tradingview-quote]` |
| AC-TV12 | `("tradingview", "fundamentals")` field mapping registered (scanner → canonical) | Known issue | `TestFieldMappingRegistry::test_provider_mapping_exists[tradingview-fundamentals]` |
| AC-TV13 | Fundamentals mapping: `market_cap_basic` → `market_cap`, `earnings_per_share_basic_ttm` → `eps` | Known issue | `TestTradingViewMappings::test_tradingview_fundamentals_mapping` |

### Additional Files Changed

| File | Change |
|------|--------|
| `url_builders.py` | +65 lines: `TradingViewUrlBuilder` class with `build_request()` + registry entry |
| `response_extractors.py` | +60 lines: `_tradingview_quote()` + `_tradingview_fundamentals()` + shared `_tradingview_scanner_extract()` |
| `field_mappings.py` | +22 lines: slug map entry + 2 field mapping tuples |
| `tests/unit/test_url_builders.py` | +90 lines: `TestTradingViewUrlBuilder` (6 tests) |
| `tests/unit/test_response_extractors.py` | +65 lines: `TestTradingViewQuoteExtractor` (3 tests) + `TestTradingViewFundamentalsExtractor` (1 test) |
| `tests/unit/test_field_mappings.py` | +35 lines: `TestTradingViewMappings` (2 tests) + registry parametrize entries |

---

## Addendum: Ad-Hoc Pipeline Approval Drift Fix

> Discovered during GUI testing of policy execution (2026-05-02). Not part of original MEU scope but resolved in same session.

### Problem

Two issues blocked manual pipeline execution from the Zorivest GUI:

1. **403 Forbidden on Run Now / Test Run**: `triggerRun()` in `ui/.../scheduling/api.ts` was not sending the `X-Approval-Token` header required by the backend's `validate_approval_token` dependency, while `approvePolicy()` in the same file already implemented the correct IPC handshake.

2. **Content hash drift on enable toggle**: `compute_content_hash()` in `policy_validator.py` included `trigger.enabled` in the SHA-256 hash. When a policy was approved at `enabled=false` (Draft→Ready) then toggled to `enabled=true` (Ready→Scheduled via `patch_schedule`), the `content_hash` diverged from `approved_hash`, causing the pipeline guardrails to block execution with "Policy modified since approval — re-approval required".

### Root Cause

The `patch_schedule()` method in `scheduling_service.py` had manual normalization logic that set `enabled=True` before hashing (correctly recognizing it as operational metadata), but `compute_content_hash()` — the canonical hash function used by `approve_policy()`, `create_policy()`, and `update_policy()` — did not normalize. This TOCTOU-like mismatch meant approval stamped one hash while schedule-enable stamped a different one.

### Fix

| File | Change |
|------|--------|
| `ui/src/renderer/src/features/scheduling/api.ts` | `triggerRun()` now calls `electronAPI.generateApprovalToken(policyId)` and sends `X-Approval-Token` header (same pattern as `approvePolicy()`) |
| `packages/core/src/zorivest_core/domain/policy_validator.py` | `compute_content_hash()` normalizes `trigger.enabled` to `True` before hashing — toggling enabled never invalidates approval |
| `packages/core/src/zorivest_core/services/scheduling_service.py` | Removed redundant manual normalization in `patch_schedule()` — now delegates to `_compute_hash()` directly since normalization is centralized |

### Security Verification

| Test | Method | Result |
|------|--------|--------|
| MCP `run` on Draft policy | `zorivest_policy(action:"run")` | 🔴 403 CSRF blocked |
| MCP `run` on Ready policy | `zorivest_policy(action:"run")` | 🔴 403 CSRF blocked |
| Direct API `/run` (no token) | `Invoke-RestMethod POST` | 🔴 403 CSRF blocked |
| Direct API `/run` (fake token) | `X-Approval-Token: fake` | 🔴 `TOKEN_NOT_FOUND` |
| Direct API `/approve` (no token) | `Invoke-RestMethod POST` | 🔴 403 CSRF blocked |
| Direct API `/approve` (fake token) | `X-Approval-Token: injected` | 🔴 `TOKEN_NOT_FOUND` |
| Schedule enable via PATCH | `PATCH /schedule?enabled=true` | 🟢 200 OK, `approved_hash == content_hash` |
| Schedule disable via PATCH | `PATCH /schedule?enabled=false` | 🟢 200 OK, no hash drift |
