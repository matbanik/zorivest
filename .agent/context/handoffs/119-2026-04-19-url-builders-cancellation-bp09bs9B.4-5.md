---
handoff_id: 119
date: 2026-04-19
slug: url-builders-cancellation
build_plan_section: "bp09bs9B.4-5"
meus: ["MEU-PW6", "MEU-PW7"]
status: complete
verbosity: standard
---

# Handoff 119 — URL Builders + Pipeline Cancellation

> **MEU-PW6** (URL Builders) + **MEU-PW7** (Pipeline Cancellation)
> **Build Plan:** §9B.4, §9B.5

<!-- CACHE BOUNDARY -->

## Summary

Implemented two pipeline infrastructure MEUs:

1. **MEU-PW6**: Registry-based URL builder dispatch (`YahooUrlBuilder`, `PolygonUrlBuilder`, `FinnhubUrlBuilder`, `GenericUrlBuilder`) with factory function and ticker resolution helper.
2. **MEU-PW7**: Cooperative pipeline cancellation infrastructure — `CANCELLING` enum state, task tracking in `PipelineRunner`, delegation through `SchedulingService`, and REST endpoint with UUID boundary validation.

## Changed Files

### New Files
- `packages/infrastructure/src/zorivest_infra/market_data/url_builders.py` — 4 builder classes + registry + helper
- `tests/unit/test_url_builders.py` — 22 tests (PW6)
- `tests/unit/test_pipeline_cancellation.py` — 15 tests (PW7)

### Modified Files

```diff
# packages/core/src/zorivest_core/domain/enums.py
+    CANCELLING = "cancelling"  # New PipelineStatus member

# packages/core/src/zorivest_core/services/pipeline_runner.py
+    self._active_tasks: dict[str, asyncio.Task[Any]] = {}
+    async def cancel_run(self, run_id: str) -> bool:

# packages/core/src/zorivest_core/services/scheduling_service.py
+    async def cancel_run(self, run_id: str) -> RunResult:

# packages/api/src/zorivest_api/routes/scheduling.py
+    from fastapi import Path  # Added import
+    @scheduling_router.post("/runs/{run_id}/cancel")
+    async def cancel_run(run_id: str = Path(..., pattern=UUID_REGEX)):

# tests/unit/test_pipeline_enums.py
-    assert len(PipelineStatus) == 6
+    assert len(PipelineStatus) == 7

# openapi.committed.json — regenerated with cancel endpoint
# .agent/context/meu-registry.md — PW6+PW7 entries added
```

## Evidence

### FAIL_TO_PASS Evidence

**Red phase (PW6):** 22 tests written first, all FAILED before implementation.
**Red phase (PW7):** 15 tests written first, all FAILED before implementation.
**Green phase:** All 37 tests pass after implementation.

### Commands Executed

```
uv run pytest tests/unit/test_url_builders.py -v → 22 passed
uv run pytest tests/unit/test_pipeline_cancellation.py -v → 15 passed
uv run pytest tests/ -q → 2064 passed, 15 skipped
uv run pyright packages/ → 0 errors, 0 warnings
uv run ruff check packages/ → All checks passed
uv run python tools/export_openapi.py --check openapi.committed.json → OK
uv run python tools/validate_codebase.py --scope meu → All 8 blocking checks passed
```

### Codex Validation Report

N/A — awaiting Codex validation trigger.

## Deferred Work

- **Adapter refactor** (tasks 3-4 from plan): `MarketDataProviderAdapter._build_url()` replacement with builder dispatch and `http_cache.py` header forwarding. These are integration tasks that require deeper adapter testing infrastructure. Deferred to a follow-up MEU.

## Residual Risk

- The `cancel_run()` in `PipelineRunner` uses `asyncio.Task.cancel()` which is cooperative — if a step doesn't yield to the event loop, cancellation will be delayed until the next `await` point. This is by design and matches the spec.
- The adapter refactor (deferred) means the URL builders exist but aren't yet wired into the actual data fetch path.
