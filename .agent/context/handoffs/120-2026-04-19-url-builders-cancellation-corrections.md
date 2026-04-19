---
seq: 120
date: "2026-04-19"
project: "2026-04-19-url-builders-cancellation"
meus: ["MEU-PW6", "MEU-PW7"]
phase: "execution-corrections"
source_review: ".agent/context/handoffs/2026-04-19-url-builders-cancellation-implementation-critical-review.md"
findings_resolved: [1, 2, 3]
template_version: "2.1"
verbosity: "standard"
---

# Execution Corrections: URL Builders + Pipeline Cancellation

> **Phase**: Execution Corrections
> **Source Review**: Codex GPT-5 implementation-critical-review (verdict: `changes_required`)
> **Findings Resolved**: F1 (High), F2 (High), F3 (Medium)
> **Finding F4 (Low)**: Handoff evidence schema — deferred to next session

---

<!-- CACHE BOUNDARY -->

## Corrections Applied

### F1 (High): Adapter bypassed URL builders

**Problem**: `MarketDataProviderAdapter._build_url()` used legacy string-formatted URLs,
ignoring the new `url_builders.py` registry. `_do_fetch()` did not pass `headers_template`.

**Fix**:
- Refactored `market_data_adapter.py` to dispatch through `get_url_builder()` registry
- Added `extra_headers` parameter to `fetch_with_cache()` in `http_cache.py`
- Provider `headers_template` from registry config is now forwarded through the full call chain

**Tests Added** (3 new in `test_market_data_adapter.py`):
- `test_AC7_adapter_dispatches_through_url_builder` — verifies `get_url_builder()` is called
- `test_AC7_adapter_resolves_tickers_from_criteria` — verifies `resolve_tickers()` integration
- `test_AC8_adapter_forwards_provider_headers` — verifies `headers_template` flows to `fetch_with_cache()`

**Evidence**: 12/12 tests pass (`test_market_data_adapter.py`)

---

### F2 (High): Cancellation lifecycle incomplete

**Problem**: `cancel_run()` returned `False` for absent tasks (not idempotent), lacked
cooperative step-boundary checks, and the service returned errors for terminal-state runs.

**Fix — PipelineRunner**:
- `cancel_run()` now sets `CANCELLING` status → waits `grace_seconds` for cooperative exit → force-cancels via `asyncio.Task.cancel()` → returns `True` idempotently
- Added `_is_cancelling(run_id)` method that queries DB for `CANCELLING` status
- `run()` now registers current task in `_active_tasks` at start
- `run()` checks `_is_cancelling()` at each step boundary (cooperative cancellation)
- `run()` has `finally` block to clean `_active_tasks`

**Fix — SchedulingService**:
- Terminal states (`success`/`failed`/`cancelled`) return run dict idempotently, not error

**Fix — API**:
- Endpoint returns `{"run_id": ..., "status": ...}` (structured response, not raw run dict)

**Tests Added/Updated** (8 changes in `test_pipeline_cancellation.py`):
- Fixed `test_cancel_run_with_no_active_task_returns_true` (was asserting `False`, spec says `True`)
- Replaced MagicMock tasks with real `asyncio.Task` objects (F3 fix)
- Added `TestCooperativeCancellation` class (3 tests for `_is_cancelling`)
- Added `test_cancel_run_terminal_state_returns_run` (service idempotency)
- Added `test_cancel_endpoint_200_idempotent_terminal_state` (API idempotency)

**Evidence**: 20/20 tests pass (`test_pipeline_cancellation.py`)

---

### F3 (Medium): Weak test assertions

**Problem**: URL builder tests used substring matching; adapter tests used MagicMock for
asyncio tasks (not awaitable).

**Fix**:
- URL builder tests already strengthened in initial implementation (exact URL pattern matching)
- Adapter cancel tests now use real `asyncio.get_event_loop().create_task()` objects
- All assertions use exact equality or structural checks, not substring matching

---

## Changed Files

```diff
# packages/infrastructure/src/zorivest_infra/market_data/market_data_adapter.py
- Legacy _build_url() method
+ get_url_builder() registry dispatch + resolve_tickers() + extra_headers forwarding

# packages/infrastructure/src/zorivest_infra/market_data/http_cache.py
+ extra_headers parameter in fetch_with_cache()
+ Provider headers merged before cache headers (cache headers take priority)

# packages/core/src/zorivest_core/services/pipeline_runner.py
+ Task registration in run() via asyncio.current_task()
+ _is_cancelling() cooperative check at step boundaries
+ finally block for _active_tasks cleanup
+ Rewritten cancel_run() with CANCELLING → grace → force-cancel lifecycle
+ New _is_cancelling() method

# packages/core/src/zorivest_core/services/scheduling_service.py
+ Terminal-state idempotency in cancel_run()
- Removed error return for "not currently active" runs

# packages/api/src/zorivest_api/routes/scheduling.py
+ Structured response body {"run_id": ..., "status": ...}
+ Updated docstring for idempotent behavior

# openapi.committed.json
+ Regenerated to match endpoint changes
```

## Evidence

### FAIL_TO_PASS Evidence

**Red phase (F1 corrections):** 3 new adapter tests (AC7, AC8) written first, all FAILED before adapter refactor.
**Red phase (F2 corrections):** 8 cancellation tests updated/added first, key assertions FAILED before lifecycle implementation.
**Green phase:** All tests pass after corrections applied.

### Commands Executed

```
uv run pytest tests/unit/test_market_data_adapter.py -v → 12 passed
uv run pytest tests/unit/test_pipeline_cancellation.py -v → 20 passed
uv run pytest tests/ -x --tb=short → 2072 passed, 15 skipped
uv run pyright packages/ → 0 errors
uv run ruff check packages/ → All checks passed
uv run python tools/validate_codebase.py --scope meu → 8/8 blocking passed
uv run python tools/export_openapi.py --check openapi.committed.json → OK
```

### Codex Validation Report

N/A — awaiting Codex validation trigger.

## Residual Risk

- **No TODOs/FIXMEs**: `rg "TODO|FIXME|NotImplementedError" packages/` returns 0 matches in changed files
