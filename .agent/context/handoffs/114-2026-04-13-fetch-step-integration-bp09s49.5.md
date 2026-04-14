# MEU-PW2 Fetch Step Integration Handoff

- **MEU**: MEU-PW2
- **Slug**: `fetch-step-integration`
- **Matrix Item**: 49.5
- **Build Plan Ref**: [09 §9.4](../../docs/build-plan/09-scheduling.md)
- **Date**: 2026-04-13
- **Status**: ✅ Complete (post-corrections)

---

## Summary

Implemented the fetch step integration layer: `MarketDataProviderAdapter`, `MarketDataAdapterPort` Protocol, `FetchAdapterResult` TypedDict, `FetchStep._check_cache()` with TTL freshness + market-closed extension (weekday after-hours aware), stale-cache metadata forwarding for HTTP 304 revalidation, cache upsert after fetch, entity_key computation (normalized to resolved criteria), `warnings` field on `FetchResult`, and full wiring in `main.py` (PipelineRunner 8→9 kwargs). Updated all PW1 contract tests for the expanded interface.

### Corrections Applied (Codex Review Findings)

| Finding | Severity | Fix |
|---------|----------|-----|
| F1: Stale cache metadata not forwarded to adapter | High | `_check_cache` returns `stale` dict; `_fetch_from_provider` forwards `cached_*` kwargs |
| F2: Entity key uses raw vs resolved criteria | High | Criteria resolution moved before `_check_cache`; both read/write use `resolved_criteria` |
| F3: `_is_market_closed()` weekend-only | High | Deleted; replaced with canonical `is_market_closed()` from domain.pipeline |
| F4: 3 ruff errors + private-method patching | Medium | Fixed lint, rewrote `test_AC_F11` with real cache repo mock |

## Changed Files

| File | Change |
|------|--------|
| `packages/core/src/zorivest_core/ports.py` | +`FetchAdapterResult` TypedDict, +`MarketDataAdapterPort` Protocol |
| `packages/core/src/zorivest_core/pipeline_steps/fetch_step.py` | +`_compute_entity_key()`, 3-state `_check_cache()`, stale metadata forwarding, canonical `is_market_closed()` |
| `packages/core/src/zorivest_core/domain/pipeline.py` | +`warnings: list[str]` field on `FetchResult` |
| `packages/core/src/zorivest_core/services/pipeline_runner.py` | +`fetch_cache_repo` (9th kwarg), injected into context |
| `packages/infrastructure/src/zorivest_infra/market_data/http_cache.py` | +`timeout: int = 30` param on `fetch_with_cache()` |
| `packages/infrastructure/src/zorivest_infra/market_data/market_data_adapter.py` | New: `MarketDataProviderAdapter` class |
| `packages/api/src/zorivest_api/main.py` | Wired `PipelineRateLimiter`, `MarketDataProviderAdapter`, `fetch_cache_repo` |
| `tests/unit/test_market_data_adapter.py` | 7 unit tests, removed unused `patch` import |
| `tests/unit/test_fetch_step.py` | Rewrote `test_AC_F11` (real cache repo), +2 regression tests (F2, F3) |
| `tests/unit/test_pipeline_runner_constructor.py` | 8→9 kwargs, `fetch_cache_repo` assertions |
| `tests/unit/test_ports.py` | Excluded `FetchAdapterResult` TypedDict from Protocol checks |
| `tests/integration/test_pipeline_wiring.py` | `provider_adapter is not None`, 7→9 expected keys |
| `tests/integration/test_pipeline_fetch_e2e.py` | Rewrote ETag revalidation test (full execute() path) |

## Evidence

### Quality Gates
- **pyright**: 0 errors, 0 warnings
- **ruff**: All checks passed (3 errors fixed: F841 ×2, F401 ×1)
- **pytest**: 1928 passed, 15 skipped, 0 failed
- **MEU gate**: 8/8 blocking checks pass

### Commands Executed
```
uv run ruff check tests/unit/test_market_data_adapter.py tests/unit/test_fetch_step.py tests/integration/test_pipeline_fetch_e2e.py
uv run pytest tests/unit/test_fetch_step.py tests/unit/test_market_data_adapter.py tests/integration/test_pipeline_fetch_e2e.py -x --tb=short -v  # 44 passed
uv run pytest tests/ -x --tb=short -q  # 1928 passed, 15 skipped
uv run pyright packages/core/src/zorivest_core/pipeline_steps/fetch_step.py  # 0 errors
uv run python tools/validate_codebase.py --scope meu  # 8/8 pass
```

### FAIL_TO_PASS Evidence
- Red phase: All adapter, cache, and e2e tests failed (original Tasks 1-4)
- Correction regression tests:
  - `test_PW2_AC4_weekday_after_hours_extends_ttl` — would fail with old weekend-only `_is_market_closed()`
  - `test_PW2_F2_entity_key_uses_resolved_criteria` — would fail with old `params.criteria` read path
  - `test_PW2_AC7_etag_revalidation_304` — would fail with old execute() path (no stale forwarding)
- Green phase: All 1928 tests pass after corrections

### Codex Validation Report
- **Review file**: `2026-04-13-fetch-step-integration-implementation-critical-review.md`
- **Verdict**: `changes_required` → runtime findings closed, evidence structure corrected
- **Passes**: Initial review + recheck (2 passes)

## Acceptance Criteria Verification

| AC | Description | Status | Evidence |
|----|-------------|--------|----------|
| AC-2 | Adapter dispatches by data_type, returns `FetchAdapterResult` | ✅ | `test_market_data_adapter.py` |
| AC-3 | `_check_cache()` returns hit/stale/None (3-state) | ✅ | `test_fetch_step.py::test_PW2_AC3_*` |
| AC-4 | Cache respects `is_market_closed()` — extends TTL 4× (weekends + after-hours) | ✅ | `test_PW2_AC4_*` (4 tests incl. weekday after-hours) |
| AC-5 | Every HTTP call goes through `PipelineRateLimiter.execute_with_limits()` | ✅ | `test_market_data_adapter.py::test_PW2_AC5_*` |
| AC-6 | ETag/If-Modified-Since conditional headers sent | ✅ | `test_market_data_adapter.py::test_PW2_AC6_*` |
| AC-7 | Integration test: fetch→transform with revalidation through execute() | ✅ | `test_pipeline_fetch_e2e.py` (5 tests, revalidation via execute()) |
| AC-8 | All existing tests pass after wiring changes | ✅ | 1928 passed full regression |
| F2-reg | Entity key uses resolved_criteria consistently | ✅ | `test_PW2_F2_entity_key_uses_resolved_criteria` |

## Downstream Impact

- **MEU-PW3** (`market-data-schemas`): Can now build on the adapter's response parsing
- **PipelineRunner**: Now has 9 kwargs — future MEUs adding params must update constructor tests
- **main.py**: `provider_adapter` is now a real `MarketDataProviderAdapter` (was `None`)
