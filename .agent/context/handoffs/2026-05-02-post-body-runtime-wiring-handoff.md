---
project: "2026-05-02-post-body-runtime-wiring"
meus: ["MEU-189"]
status: "complete"
completion_timestamp: "2026-05-02T23:32:00Z"
verbosity: "standard"
---

# Handoff — POST-Body Runtime Wiring (MEU-189)

## Summary

Implemented POST-body runtime dispatch across the market data infrastructure, enabling OpenFIGI (and future POST providers like SEC API) to use POST requests through the same adapter pipeline as GET providers.

## Changed Files

```diff
# packages/infrastructure/src/zorivest_infra/market_data/http_cache.py
# fetch_with_cache() now accepts method="GET"|"POST" and json_body params
+ method: str = "GET"
+ json_body: Any | None = None
+ POST: bypass conditional headers (ETag/If-Modified-Since) per RFC 9110 §9.3.3
+ POST: call client.post(url, headers, timeout, json=json_body)
+ Validate method ∈ {"GET", "POST"} → raise ValueError

# packages/infrastructure/src/zorivest_infra/market_data/market_data_adapter.py
+ Import RequestSpec from url_builders
+ fetch(): detect hasattr(builder, "build_request") → POST dispatch
+ _do_fetch(): forward method + json_body to fetch_with_cache

# packages/core/src/zorivest_core/services/provider_connection_service.py
+ _validate_openfigi(): list[dict] with 'data' key (not 'error')
+ _test_openfigi_post(): POST to /v3/mapping with [{idType, idValue}]
+ test_connection(): OpenFIGI dispatch before generic GET path

# tests/unit/test_http_cache.py (NEW — 11 tests)
# tests/unit/test_adapter_post_dispatch.py (NEW — 6 tests)
# tests/unit/test_openfigi_connection.py (NEW — 7 tests)
# tests/unit/test_market_data_adapter.py (fixture fix: MagicMock spec)
# tests/unit/test_provider_connection_service.py (fixture fix: response shape)
```

## Evidence Bundle

| Gate | Result |
|------|--------|
| pytest (new tests) | 24/24 pass |
| pytest (full regression) | 2498 pass, 0 fail |
| pyright packages/ | 0 errors |
| ruff packages/ | All checks passed |
| anti-placeholder | 0 matches |

## Fixture Fixes (Not Assertion Changes)

1. `test_market_data_adapter.py::test_AC7_adapter_dispatches_through_url_builder` — `MagicMock()` → `MagicMock(spec=["build_url"])` to prevent `hasattr(builder, "build_request")` returning True for GET-only builders
2. `test_provider_connection_service.py::TestGenericValidation::test_openfigi_generic` — response shape `{"data": [...]}` → `[{"data": [...]}]` to match the real OpenFIGI API format (list of mapping results)

## Polygon Investigation (Task 9)

The Polygon.io URL builder constructs correct paths: `base_url (/v2) + /aggs/ticker/{symbol}/...`. The 405 error reported in [MKTDATA-POLYGON-REBRAND] is an external issue related to Polygon's migration to Massive.com — the endpoint domain has changed but our URL patterns are correct. MEU-195 (`polygon-massive-migration`) will handle the domain update.

## Remaining Work

- MEU-195: Polygon.io → Massive.com domain migration (⬜)
- MEU-190 through MEU-194: Service methods, routes, store step, scheduler (⬜)
