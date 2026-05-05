---
date: "2026-05-05"
project: "2026-05-03-service-methods-layer4"
type: "execution-corrections"
source_review: ".agent/context/handoffs/2026-05-03-service-methods-layer4-implementation-critical-review.md"
findings_resolved: 7
findings_total: 7
pass: 3
verdict: "all_findings_resolved"
---

# Corrections Handoff — Service Methods Layer 4 (Pass 3)

> **Source Review**: `2026-05-03-service-methods-layer4-implementation-critical-review.md`
> **Pass 1**: Resolved F2 (fallback order) + F4 (display_name). Left F1 + F3 open.
> **Pass 2**: Resolved R1 (POST dispatch) + R2 (Finnhub endpoints) + R3 (test coverage) + R4 (this handoff).
> **Pass 3**: Resolved R1 (7-provider base_url mismatch) + R2 (production integration tests) + R3 (stale claim).
> **Result**: 7/7 cumulative findings fully resolved.

---

## Pass 2 Changed Files

```diff
# packages/infrastructure/src/zorivest_infra/market_data/url_builders.py (R2)
# FinnhubUrlBuilder.build_url() — added 4 missing endpoint cases
+ if data_type == "company_profile":
+     return f"{base_url}/stock/profile2?symbol={symbol}"
+ if data_type == "insider":
+     return f"{base_url}/stock/insider-transactions?symbol={symbol}"
+ if data_type == "earnings":
+     return f"{base_url}/stock/earnings?symbol={symbol}"
+ if data_type == "economic_calendar":
+     return f"{base_url}/calendar/economic"

# packages/core/src/zorivest_core/services/market_data_service.py (R1)
# HttpClient Protocol — added post() method
+ async def post(
+     self, url: str, headers: dict[str, str], timeout: int, json: Any = None,
+ ) -> Any: ...

# _fetch_data_type — thread criteria kwargs to _generic_api_fetch
- data = await self._generic_api_fetch(name, data_type, ticker, setting)
+ data = await self._generic_api_fetch(name, data_type, ticker, setting, criteria=kwargs)

# _generic_api_fetch — add POST dispatch via hasattr(builder, "build_request")
- url = builder.build_url(config.base_url, data_type, [ticker], {})
- response = await self._http.get(url, headers, setting.timeout or 30)
+ build_request_fn = getattr(builder, "build_request", None)
+ if build_request_fn is not None:
+     spec = build_request_fn(config.base_url, data_type, [ticker], resolved_criteria)
+     url = spec.url; http_method = spec.method; json_body = spec.body
+ else:
+     url = builder.build_url(config.base_url, data_type, [ticker], resolved_criteria)
+ if http_method == "POST":
+     response = await self._http.post(url, headers, timeout, json=json_body)
+ else:
+     response = await self._http.get(url, headers, timeout)

# tests/unit/test_service_methods.py (R3)
+ TestFinnhubEndpoints (4 tests): company_profile, insider, earnings, calendar
+ TestPOSTDispatch (2 tests): SEC API POST, FMP GET regression
```

## Test Evidence

| Suite | Result |
|-------|--------|
| `test_service_methods.py` | 29 passed (23 pass 1 + 6 pass 2) |
| pyright (changed files) | 0 errors |
| ruff (changed files) | All checks passed |

## Finding Resolution Map (Full — Pass 1 + Pass 2)

| Finding | Pass | Fix | Test | Key Assertion |
|---------|------|-----|------|---------------|
| F1/R1: POST dispatch + criteria | 2 | `_generic_api_fetch` POST/GET branch + criteria threading | `TestPOSTDispatch::test_sec_api_insider_uses_post` | SEC API calls `post()` with `search-index` URL |
| F2: Fallback order | 1 | Removed `sorted()` in `_get_enabled_providers` | `TestFallbackOrder::test_fundamentals_order_fmp_eodhd_av` | FMP → EODHD → AV (insertion order) |
| F3/R2: Finnhub endpoints | 2 | Added 4 cases to `FinnhubUrlBuilder.build_url()` | `TestFinnhubEndpoints` (4 tests) | `/stock/profile2`, `/stock/insider-transactions`, `/stock/earnings`, `/calendar/economic` |
| F3/R3: Test coverage | 2 | 6 new tests across 2 classes | `TestFinnhubEndpoints` + `TestPOSTDispatch` | URL assertions + HTTP method assertions |
| F4: display_name | 1 | `Polygon.io` → `Massive` rebranding | `TestDisplayNameRegression` | display_name renders correctly in registry + UI |

## TDD Evidence

| Phase | Tests | Key Failure Message |
|-------|-------|---------------------|
| Red | 5 failed, 1 passed | `Expected /stock/profile2, got /quote?symbol=AAPL` ¦ `SEC API should use POST, but no post calls were made` |
| Green | 6 passed | All URL + method assertions satisfied |
| Full regression | 29 passed | No regressions |

---

## Pass 3 — Registry/Builder base_url Alignment

### Changed Files

```diff
# packages/infrastructure/src/zorivest_infra/market_data/provider_registry.py
# 7 providers: strip path prefix from base_url, update test_endpoint to full path
- base_url="https://financialmodelingprep.com/api/v3"
+ base_url="https://financialmodelingprep.com"
- base_url="https://eodhd.com/api"
+ base_url="https://eodhd.com"
- base_url="https://api.alpaca.markets/v2"
+ base_url="https://data.alpaca.markets"
- base_url="https://api.api-ninjas.com/v1"
+ base_url="https://api.api-ninjas.com"
- base_url="https://api.tradier.com/v1"
+ base_url="https://api.tradier.com"
- base_url="https://www.alphavantage.co/query"
+ base_url="https://www.alphavantage.co"
- base_url="https://data.nasdaq.com/api/v3"
+ base_url="https://data.nasdaq.com"

# tests/unit/test_service_methods.py — add TestProductionRegistryURLIntegration (8 tests)
# tests/unit/test_service_methods.py — fix FMP + AV fixtures
# tests/unit/test_market_data_service.py — fix AV + FMP fixtures
# tests/unit/test_market_data_entities.py — fix AV fixture
# tests/unit/test_provider_connection_service.py — fix AV fixture
```

### Test Evidence

| Suite | Result |
|-------|--------|
| `TestProductionRegistryURLIntegration` | 8/8 passed (7 red→green + 1 always-green) |
| Full market data regression (6 files) | 293 passed, 0 failed |
| pyright (registry) | 0 errors |
| ruff (registry) | All checks passed |

### Finding Resolution Map (Pass 3)

| Finding | Fix | Test | Key Assertion |
|---------|-----|------|---------------|
| R1: 7 double-prefix base_urls | Strip path segments from registry | `test_fmp_no_double_prefix` + 6 siblings | No `/api/v3/api/v3/` in built URL |
| R2: Tests mask production wiring | Import real PROVIDER_REGISTRY + builders | `test_all_providers_produce_valid_urls` | All 13 providers build valid https:// URLs |
| R3: Stale handoff claim | Updated metadata + Pass 3 section | This section | Accurate resolution count |
