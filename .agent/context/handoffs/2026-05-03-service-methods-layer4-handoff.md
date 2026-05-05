---
project: "2026-05-03-service-methods-layer4"
meus: ["MEU-195", "MEU-190", "MEU-191"]
status: "complete"
verbosity: "standard"
---

# Handoff — Phase 8a Layer 4: Service Methods + Polygon Migration

> **Completed**: 2026-05-04T21:42Z
> **MEUs**: MEU-195, MEU-190, MEU-191
> **Plan**: [implementation-plan.md](../../../docs/execution/plans/2026-05-03-service-methods-layer4/implementation-plan.md)
> **Task**: [task.md](../../../docs/execution/plans/2026-05-03-service-methods-layer4/task.md)

<!-- CACHE BOUNDARY -->

## Scope

Phase 8a Layer 4 — 8 service methods on `MarketDataService` (3 core + 5 extended), 24 per-provider normalizer functions, Yahoo-first fallback chains for 4 data types, plus Polygon.io → Massive.com full-stack migration (domain, auth, display name, URL builder, GUI).

## Feature Intent Contract

### MEU-195: Polygon → Massive Migration + API Hardening

| AC | Description | Status |
|----|-------------|--------|
| AC-195-1 | `base_url` → `https://api.massive.com` (no `/v2`) | ✅ |
| AC-195-2 | `signup_url` → `https://massive.com/pricing` | ✅ |
| AC-195-3 | Provider key remains `"Polygon.io"` | ✅ |
| AC-195-4 | All existing tests pass | ✅ |
| AC-195-5 | Auth → `QUERY_PARAM` with `apiKey` | ✅ |
| AC-195-6 | Test endpoint → `/v3/reference/tickers?limit=1&apiKey={api_key}` | ✅ |
| AC-195-7 | `config.name` = `"Massive"` (display name) | ✅ |
| AC-195-8 | `display_name` on ProviderStatus DTO | ✅ |
| AC-195-9 | GUI renders `display_name` via `label()` helper | ✅ |
| AC-195-10 | PolygonUrlBuilder with `/v2/`+`/v3/` version prefixes | ✅ |

### MEU-190: Core Service Methods

| AC | Description | Status |
|----|-------------|--------|
| AC-190-1 | `get_ohlcv()` Yahoo → Alpaca → EODHD → Polygon | ✅ |
| AC-190-2 | `get_fundamentals()` Yahoo → FMP → EODHD → AV | ✅ |
| AC-190-3 | `get_earnings()` Finnhub → FMP → AV (no Yahoo) | ✅ |
| AC-190-4–8 | Yahoo helpers, normalizers, capabilities check, logging | ✅ |

### MEU-191: Extended Service Methods

| AC | Description | Status |
|----|-------------|--------|
| AC-191-1 | `get_dividends()` Yahoo → Polygon → EODHD → FMP | ✅ |
| AC-191-2 | `get_splits()` Yahoo → Polygon → EODHD → FMP | ✅ |
| AC-191-3 | `get_insider()` Finnhub → FMP → SEC API | ✅ |
| AC-191-4 | `get_economic_calendar()` Finnhub → FMP → AV | ✅ |
| AC-191-5 | `get_company_profile()` FMP → Finnhub → EODHD | ✅ |
| AC-191-6–8 | Yahoo helpers, normalizers | ✅ |

## Design Decisions

1. **Base URL without version prefix**: Removed `/v2` from `base_url` and moved version prefixes into `PolygonUrlBuilder` paths (`/v2/aggs/`, `/v2/snapshot/`, `/v3/reference/`). Reason: Massive uses mixed API versions — v2 for market data, v3 for reference data. A single-version base URL would break one or the other.

2. **QUERY_PARAM auth instead of BEARER_HEADER**: Massive's REST Quickstart documents `?apiKey=` query parameter authentication. Bearer header also works but is not the documented primary method. Switching to query param resolved 403 errors the user was experiencing.

3. **Free-tier test endpoint**: Changed from `/aggs/ticker/AAPL/prev` (requires paid subscription) to `/v3/reference/tickers?limit=1` (available on all plans). The `{api_key}` placeholder in the test endpoint URL is essential — without it, the connection test hits the API unauthenticated.

4. **display_name field on ProviderStatus**: Rather than renaming the dict key from `"Polygon.io"` to `"Massive"` (which would break existing DB entries, encrypted API key storage, and all API URL paths that use the provider name), added a `display_name` optional field. The GUI's `label()` helper prefers `display_name` when present.

## Changed Files

```diff
# packages/infrastructure/src/zorivest_infra/market_data/provider_registry.py
-        name="Polygon.io",
-        base_url="https://api.polygon.io/v2",
-        auth_method=AuthMethod.BEARER_HEADER,
-        headers_template={"Authorization": "Bearer {api_key}"},
-        test_endpoint="/aggs/ticker/AAPL/prev",
+        name="Massive",
+        base_url="https://api.massive.com",
+        auth_method=AuthMethod.QUERY_PARAM,
+        auth_param_name="apiKey",
+        headers_template={},
+        test_endpoint="/v3/reference/tickers?limit=1&apiKey={api_key}",
+        signup_url="https://massive.com/pricing",

# packages/infrastructure/src/zorivest_infra/market_data/url_builders.py
- /aggs/ticker/{symbol}/range/... → /v2/aggs/ticker/{symbol}/range/...
- /snapshot/locale/... → /v2/snapshot/locale/...
- /ticker/{symbol} → /v3/reference/tickers/{symbol}
+ added /v3/reference/dividends and /v3/reference/splits endpoints

# packages/core/src/zorivest_core/application/provider_status.py
+ display_name: str | None = None

# packages/core/src/zorivest_core/services/provider_connection_service.py
+ if config.name != name: status.display_name = config.name

# ui/src/renderer/src/features/settings/MarketDataProvidersPage.tsx
+ display_name?: string | null (ProviderStatus interface)
+ label(p) helper: returns display_name ?? provider_name
```

Plus: `market_data_service.py` (8 methods + 4 Yahoo helpers), `normalizers.py` (24 functions), `test_service_methods.py`, `test_expansion_normalizers.py`, `test_provider_registry.py`, `test_url_builders.py`.

## Commands Executed

| Command | Result |
|---------|--------|
| `pytest tests/ -x --tb=short -q` | 2830 passed, 0 failed |
| `pyright packages/` | 0 errors |
| `ruff check packages/` | All checks passed |
| `validate_codebase.py --scope meu` | 8/8 PASS |
| `rg "api.polygon.io" packages/ tests/` | 0 matches |
| `vitest run MarketDataProvidersPage.test.tsx` | 25 passed |
| Live GUI test: Massive connection | ✅ Connected (HTTP 200) |

## FAIL_TO_PASS Evidence

MEU-190/191 TDD cycle completed in prior session (tasks 3–16 in task.md). MEU-195 hardening was ad-hoc user-driven (live GUI testing revealed 403 → auth fix → display name → URL builder fix → test endpoint fix), each verified incrementally against 2830-test regression suite.

## Test Mapping

| AC | Test Function(s) |
|----|-------------------|
| AC-195-1/2 | `test_provider_registry.py::TestPolygonMigration` |
| AC-195-5 | `test_provider_registry.py::TestAuthMethodsAC6::test_auth_method_matches_spec[Polygon.io-query_param]` |
| AC-195-7 | `test_provider_registry.py::TestPolygonMigration::test_massive_display_name` |
| AC-195-10 | `test_url_builders.py::TestPolygonUrlBuilder` (3 tests) |
| AC-190-1–8 | `test_service_methods.py::TestGetOhlcv`, `TestGetFundamentals`, `TestGetEarnings` |
| AC-191-1–8 | `test_service_methods.py::TestGetDividends`, `TestGetSplits`, `TestGetInsider`, `TestGetEconomicCalendar`, `TestGetCompanyProfile` |
| Normalizers | `test_expansion_normalizers.py` (22 test classes, 66 tests) |
