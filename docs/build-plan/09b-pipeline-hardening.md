# 09b — Pipeline Runtime Hardening

> Phase: P2.5b · MEU-PW4 through MEU-PW8
> Prerequisites: MEU-PW1 ✅, MEU-PW2 ✅, MEU-PW3 ✅
> Unblocks: Reliable end-to-end pipeline execution, GUI "Run Now" / "Cancel" UX, Home Dashboard pipeline widgets
> Resolves: [PIPE-CHARMAP], [PIPE-ZOMBIE], [PIPE-URLBUILD], [PIPE-NOCANCEL]
> Status: ⬜ planned

---

## 9B.1 Problem Statement

Four high-severity bugs discovered during MEU-PW1/PW2 integration testing render the scheduling pipeline non-functional in practice:

| ID | Bug | Severity | Impact |
|----|-----|----------|--------|
| [PIPE-CHARMAP] | `'charmap' codec can't encode characters` on Windows | High | Pipeline crashes on non-ASCII error messages |
| [PIPE-ZOMBIE] | Pipeline runs stuck permanently in "running" state | High | Dual-write creates orphaned records; no cleanup path |
| [PIPE-URLBUILD] | `_build_url()` uses hardcoded URL patterns that don't match providers | High | All fetches fail — Yahoo hangs, Finnhub 404s |
| [PIPE-NOCANCEL] | No mechanism to cancel a running pipeline run | High | Only way to stop a stuck run is to kill the backend process |

Additionally, no integration test infrastructure exists to validate that policies execute correctly through the full service stack.

---

## Step 9B.2: Charmap Encoding Fix (MEU-PW4)

### 9B.2a Background

Windows `cmd.exe` and PowerShell default to `cp1252` encoding, which cannot represent many Unicode characters. When `structlog` writes exception tracebacks containing non-ASCII characters (e.g., `'curl: (56) Recv failure…'` with smart quotes from provider responses), `sys.stderr.write()` raises:

```
UnicodeEncodeError: 'charmap' codec can't encode characters in position 42-48
```

This crashes the pipeline at `pipeline_runner.py:202` and `scheduling_service.py:325`.

Secondary issue: `pipeline_runner.py:354` calls `json.dumps(result.output)` which fails on `bytes` objects returned by HTTP responses.

### 9B.2b Fix — Structlog UTF-8 Configuration

```python
# packages/api/src/zorivest_api/logging_config.py (new module or append to existing)

import io
import sys

import structlog


def configure_structlog_utf8() -> None:
    """Configure structlog with UTF-8 safe output.

    Addresses [PIPE-CHARMAP]: Windows cp1252 encoding crash.
    Must be called once during FastAPI lifespan startup.
    """
    # Force UTF-8 on stderr if not already
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),  # Decode bytes → str
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer()
            if sys.stderr.isatty()
            else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(20),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(
            file=io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
        ),
        cache_logger_on_first_use=True,
    )
```

### 9B.2c Fix — Bytes-Safe JSON Serialization in `_persist_step`

```python
# packages/core/src/zorivest_core/services/pipeline_runner.py
# In _persist_step(), replace json.dumps(result.output) with:

def _safe_json_output(output: dict) -> str | None:
    """Serialize step output to JSON, handling bytes values."""
    if not output:
        return None

    def _default_serializer(obj: Any) -> Any:
        if isinstance(obj, bytes):
            return obj.decode("utf-8", errors="replace")
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

    return json.dumps(output, default=_default_serializer)
```

### 9B.2d Files to Modify

| File | Change |
|------|--------|
| `packages/api/src/zorivest_api/main.py` | Call `configure_structlog_utf8()` in lifespan startup |
| `packages/core/src/zorivest_core/services/pipeline_runner.py` | Add `_safe_json_output()`, replace `json.dumps(result.output)` in `_persist_step()` |
| `packages/api/src/zorivest_api/logging_config.py` | New module: structlog UTF-8 configuration |

### 9B.2e Verification

```bash
# Test with intentional non-ASCII in error messages
uv run pytest tests/unit/test_pipeline_runner.py -k "charmap or utf8" -v

# Confirm structlog doesn't crash on emoji/unicode
uv run python -c "
import structlog
from zorivest_api.logging_config import configure_structlog_utf8
configure_structlog_utf8()
log = structlog.get_logger()
log.error('test_error', msg='Résumé: ñ, ü, ™, 日本語')
print('OK')
"
```

---

## Step 9B.3: Zombie Run Elimination (MEU-PW5)

### 9B.3a Root Cause Analysis

Three interacting problems create zombie runs:

1. **Dual-write architecture:** `SchedulingService.trigger_run()` (line 290-306) creates a run record via `self._runs.create()`, then `PipelineRunner.run()` (line 103-139) creates a SECOND record with a different `run_id`. Only the inner record gets finalized — the outer one stays `status="running"` forever.

2. **Timeout ineffective:** `asyncio.timeout(step_def.timeout)` at `pipeline_runner.py:268` can't cancel httpx when the underlying TCP socket hangs on Windows.

3. **No recovery:** No periodic scan, no manual cleanup, no status reconciliation.

### 9B.3b Fix — Eliminate Dual-Write

The SchedulingService becomes the **sole record creator**. PipelineRunner accepts `run_id` as a parameter and updates the existing record instead of creating a new one:

```python
# packages/core/src/zorivest_core/services/pipeline_runner.py
# PipelineRunner.run() signature change:

async def run(
    self,
    policy: PolicyDocument,
    trigger_type: str,
    dry_run: bool = False,
    resume_from: str | None = None,
    actor: str = "",
    policy_id: str = "",
    run_id: str = "",        # NEW: accept pre-created run_id
) -> dict[str, Any]:
    """Execute a full pipeline.

    If run_id is provided, uses existing run record (no new creation).
    If run_id is empty, creates a new run record (standalone execution).
    """
    if not run_id:
        run_id = str(uuid.uuid4())
        await self._create_run_record(...)  # Only if no external run_id
    else:
        # Update existing record to RUNNING status
        await self._update_run_status(run_id, PipelineStatus.RUNNING)
    # ... rest of execution
```

```python
# packages/core/src/zorivest_core/services/scheduling_service.py
# SchedulingService.trigger_run() change:

async def trigger_run(...) -> RunResult:
    # Create the ONLY run record
    run_id = str(uuid.uuid4())
    run_data = {..., "run_id": run_id, "status": "pending", ...}
    result = await self._runs.create(run_data)

    # Pass run_id INTO the runner — no second create
    run_result = await self._runner.run(
        policy=doc,
        trigger_type=trigger_type,
        dry_run=dry_run,
        policy_id=policy_id,
        run_id=run_id,         # Runner uses THIS record
    )
    # Finalization now happens inside runner
    return RunResult(run=result)
```

### 9B.3c Fix — Enhanced Httpx Timeouts

```python
# packages/infrastructure/src/zorivest_infra/market_data/market_data_adapter.py

import httpx

# Replace single timeout with per-phase control
_DEFAULT_TIMEOUT = httpx.Timeout(
    connect=10.0,   # TCP connect timeout
    read=30.0,      # Per-chunk read timeout
    write=10.0,     # Write timeout
    pool=10.0,      # Connection pool wait
)
```

### 9B.3d Fix — Zombie Recovery at Startup

```python
# packages/core/src/zorivest_core/services/pipeline_runner.py
# recover_zombies() already exists but needs enhancement:

async def recover_zombies(self, max_age_seconds: int = 3600) -> list[dict]:
    """Enhanced zombie recovery.

    Scan for runs stuck in RUNNING/PENDING for longer than max_age_seconds.
    Mark as FAILED with diagnostic message.
    Called during FastAPI lifespan startup AND via periodic health check.
    """
    # ... (existing logic already in place, verify it works with real UoW)
```

### 9B.3e Files to Modify

| File | Change |
|------|--------|
| `packages/core/src/zorivest_core/services/pipeline_runner.py` | Accept `run_id` param; skip `_create_run_record()` when supplied; add `_update_run_status()` |
| `packages/core/src/zorivest_core/services/scheduling_service.py` | Pass `run_id` into `self._runner.run()`; remove duplicate finalization |
| `packages/infrastructure/src/zorivest_infra/market_data/market_data_adapter.py` | Use `httpx.Timeout(connect=10, read=30, write=10, pool=10)` |
| `packages/api/src/zorivest_api/main.py` | Call `pipeline_runner.recover_zombies()` in lifespan startup |

### 9B.3f Verification

```bash
# Unit tests for dual-write elimination
uv run pytest tests/unit/test_scheduling_service.py -k "trigger_run" -v

# Integration test: verify only one pipeline_runs row per execution
uv run pytest tests/integration/test_pipeline_wiring.py -k "single_record" -v
```

---

## Step 9B.4: Provider URL Builders (MEU-PW6)

### 9B.4a Root Cause Analysis

`MarketDataProviderAdapter._build_url()` has three sub-issues:

1. **Criteria key mismatch:** Policy sends `tickers: ["AAPL", "MSFT"]` but `_build_url()` reads `criteria.get("symbol", "")` → empty string → URL like `…/quote?symbol=` → provider hangs.

2. **Missing provider headers:** `_do_fetch()` → `fetch_with_cache()` doesn't pass `headers_template` (User-Agent, Referer) from the provider registry → providers return 403/captcha.

3. **Generic URL patterns:** Same `{base_url}/quote?symbol=` template for all 14 providers. Each provider uses a different URL scheme.

### 9B.4b Fix — Provider-Specific URL Builder Registry

```python
# packages/infrastructure/src/zorivest_infra/market_data/url_builders.py (NEW)

from __future__ import annotations
from typing import Any, Protocol


class UrlBuilder(Protocol):
    """Protocol for provider-specific URL construction."""

    def build_url(
        self,
        base_url: str,
        data_type: str,
        criteria: dict[str, Any],
    ) -> str: ...


class YahooUrlBuilder:
    """Yahoo Finance URL builder.

    Yahoo uses: /v8/finance/chart/{symbol} for OHLCV
                /v6/finance/quote?symbols=AAPL,MSFT for quotes
    """

    def build_url(self, base_url: str, data_type: str, criteria: dict[str, Any]) -> str:
        base = base_url.rstrip("/")
        tickers = _resolve_tickers(criteria)

        if data_type == "ohlcv":
            symbol = tickers[0] if tickers else ""
            date_range = criteria.get("date_range", {})
            period1 = date_range.get("start_date", "")
            period2 = date_range.get("end_date", "")
            return f"{base}/v8/finance/chart/{symbol}?period1={period1}&period2={period2}&interval=1d"

        elif data_type == "quote":
            symbols = ",".join(tickers)
            return f"{base}/v6/finance/quote?symbols={symbols}"

        elif data_type == "news":
            symbol = tickers[0] if tickers else ""
            return f"{base}/v1/finance/search?q={symbol}&newsCount=10"

        return f"{base}/v6/finance/quote?symbols={','.join(tickers)}"


class PolygonUrlBuilder:
    """Polygon.io URL builder.

    Polygon uses: /v2/aggs/ticker/{symbol}/range/1/day/{from}/{to}
                  /v2/snapshot/locale/us/markets/stocks/tickers
    """

    def build_url(self, base_url: str, data_type: str, criteria: dict[str, Any]) -> str:
        base = base_url.rstrip("/")
        tickers = _resolve_tickers(criteria)

        if data_type == "ohlcv":
            symbol = tickers[0] if tickers else ""
            date_range = criteria.get("date_range", {})
            start = date_range.get("start_date", "")
            end = date_range.get("end_date", "")
            return f"{base}/v2/aggs/ticker/{symbol}/range/1/day/{start}/{end}"

        elif data_type == "quote":
            symbols = ",".join(tickers)
            return f"{base}/v2/snapshot/locale/us/markets/stocks/tickers?tickers={symbols}"

        return f"{base}/v2/snapshot/locale/us/markets/stocks/tickers"


class FinnhubUrlBuilder:
    """Finnhub URL builder (single-symbol per request)."""

    def build_url(self, base_url: str, data_type: str, criteria: dict[str, Any]) -> str:
        base = base_url.rstrip("/")
        tickers = _resolve_tickers(criteria)
        symbol = tickers[0] if tickers else ""

        if data_type == "ohlcv":
            date_range = criteria.get("date_range", {})
            return (
                f"{base}/stock/candle"
                f"?symbol={symbol}&resolution=D"
                f"&from={date_range.get('start_date', '')}"
                f"&to={date_range.get('end_date', '')}"
            )

        elif data_type == "quote":
            return f"{base}/quote?symbol={symbol}"

        elif data_type == "news":
            return f"{base}/company-news?symbol={symbol}"

        return f"{base}/quote?symbol={symbol}"


class GenericUrlBuilder:
    """Fallback URL builder for providers without specific implementations."""

    def build_url(self, base_url: str, data_type: str, criteria: dict[str, Any]) -> str:
        base = base_url.rstrip("/")
        tickers = _resolve_tickers(criteria)
        symbols = ",".join(tickers)
        return f"{base}/{data_type}?symbols={symbols}"


# Builder registry — extend as providers are added
URL_BUILDERS: dict[str, UrlBuilder] = {
    "yahoo": YahooUrlBuilder(),
    "polygon": PolygonUrlBuilder(),
    "finnhub": FinnhubUrlBuilder(),
}

DEFAULT_URL_BUILDER = GenericUrlBuilder()


def get_url_builder(provider: str) -> UrlBuilder:
    """Get URL builder for a provider, falling back to GenericUrlBuilder."""
    return URL_BUILDERS.get(provider, DEFAULT_URL_BUILDER)


def _resolve_tickers(criteria: dict[str, Any]) -> list[str]:
    """Extract ticker list from criteria, handling both 'tickers' and 'symbol' keys.

    Policy JSON typically uses `tickers: ["AAPL", "MSFT"]` but the old
    adapter expected `symbol: "AAPL"`. This normalizes both.
    """
    tickers = criteria.get("tickers", [])
    if not tickers:
        symbol = criteria.get("symbol", "")
        tickers = [symbol] if symbol else []
    return tickers
```

### 9B.4c Fix — Pass Headers from Provider Registry

```python
# packages/infrastructure/src/zorivest_infra/market_data/market_data_adapter.py
# In _do_fetch(), forward headers_template from provider config:

async def _do_fetch(
    self,
    url: str,
    *,
    config: Any,    # Provider config from registry
    cached_content: bytes | None = None,
    cached_etag: str | None = None,
    cached_last_modified: str | None = None,
) -> dict[str, Any]:
    headers = dict(getattr(config, "headers_template", {}))
    return await fetch_with_cache(
        client=self._http_client,
        url=url,
        headers=headers,
        cached_content=cached_content,
        cached_etag=cached_etag,
        cached_last_modified=cached_last_modified,
        timeout=self._timeout,
    )
```

### 9B.4d Files to Modify

| File | Change |
|------|--------|
| `packages/infrastructure/src/zorivest_infra/market_data/url_builders.py` | **NEW**: Per-provider URL builder classes + registry |
| `packages/infrastructure/src/zorivest_infra/market_data/market_data_adapter.py` | Replace `_build_url()` with `get_url_builder()` dispatch; pass headers to fetch |
| `packages/infrastructure/src/zorivest_infra/market_data/http_cache.py` | Accept `headers` param in `fetch_with_cache()` |

### 9B.4e Verification

```bash
# Unit tests for URL builders
uv run pytest tests/unit/test_url_builders.py -v

# Test criteria key normalization (tickers vs symbol)
uv run pytest tests/unit/test_market_data_adapter.py -k "tickers or url_build" -v
```

---

## Step 9B.5: Pipeline Cancellation Infrastructure (MEU-PW7)

### 9B.5a Design (Research-Backed)

Sources: Prefect, Temporal, Azure Data Factory REST API patterns.

**State machine:**
```
PENDING → RUNNING → SUCCESS
                  → FAILED
         RUNNING → CANCELLING → CANCELLED
```

**Components:**

1. **PipelineStatus enum extension:** Add `CANCELLING = "cancelling"` (intermediate state)
2. **Task registry:** `PipelineRunner._active_tasks: dict[str, asyncio.Task]` — tracks running pipeline asyncio.Tasks
3. **Cancel endpoint:** `POST /api/v1/scheduling/runs/{run_id}/cancel`
4. **Per-step cooperative check:** At each step boundary, check if status is `CANCELLING`
5. **GUI cancel button:** (deferred to GUI MEU — documented linkage only)

### 9B.5b Domain Changes

```python
# packages/core/src/zorivest_core/domain/enums.py (append to PipelineStatus)

class PipelineStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"
    CANCELLING = "cancelling"     # NEW: Intermediate cancel state
```

### 9B.5c Pipeline Runner — Task Registry + Cancel Support

```python
# packages/core/src/zorivest_core/services/pipeline_runner.py (additions)

class PipelineRunner:
    def __init__(self, ...):
        ...
        self._active_tasks: dict[str, asyncio.Task] = {}

    async def run(self, ..., run_id: str = "") -> dict[str, Any]:
        # Wrap execution in a tracked task
        task = asyncio.current_task()
        if task and run_id:
            self._active_tasks[run_id] = task

        try:
            # ... existing step loop with new cooperative check:
            for step_def in policy.steps:
                # Cooperative cancellation check at step boundary
                if await self._is_cancelling(run_id):
                    final_status = PipelineStatus.CANCELLED
                    run_error = "Pipeline cancelled by user"
                    break
                # ... rest of step execution
        except asyncio.CancelledError:
            final_status = PipelineStatus.CANCELLED
            run_error = "Pipeline cancelled"
        finally:
            self._active_tasks.pop(run_id, None)

    async def cancel_run(self, run_id: str, grace_seconds: float = 30.0) -> bool:
        """Cancel a running pipeline.

        1. Set status to CANCELLING (cooperative cancellation at step boundaries)
        2. If still running after grace_seconds, force-cancel via asyncio.Task.cancel()
        3. Return True if cancellation was initiated

        Idempotent: calling on already-cancelled/completed run returns True.
        """
        task = self._active_tasks.get(run_id)
        if task is None:
            # Run is not active — may be completed or not found
            return True

        # Set status to CANCELLING
        await self._update_run_status(run_id, PipelineStatus.CANCELLING)

        # Wait for cooperative cancellation
        try:
            await asyncio.wait_for(asyncio.shield(task), timeout=grace_seconds)
        except asyncio.TimeoutError:
            # Force cancel
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        except asyncio.CancelledError:
            pass

        return True

    async def _is_cancelling(self, run_id: str) -> bool:
        """Check if a run has been marked for cancellation."""
        if self.uow is None:
            return False
        run = self.uow.pipeline_runs.get_by_id(run_id)
        return run is not None and run.status == PipelineStatus.CANCELLING.value
```

### 9B.5d REST API — Cancel Endpoint

```python
# packages/api/src/zorivest_api/routes/scheduling.py (append)

@router.post("/runs/{run_id}/cancel", summary="Cancel a running pipeline")
async def cancel_run(
    run_id: str,
    scheduling_service: SchedulingServiceDep,
) -> dict[str, Any]:
    """Cancel a running pipeline run.

    Idempotent: calling on already-cancelled/completed run returns 200.
    Returns 404 if run_id not found.

    Pattern: Azure Data Factory REST API cancel semantics.
    """
    result = await scheduling_service.cancel_run(run_id)
    if result is None:
        raise HTTPException(404, "Run not found")
    return {"run_id": run_id, "status": result.get("status", "cancelling")}
```

### 9B.5e SchedulingService — Cancel Delegation

```python
# packages/core/src/zorivest_core/services/scheduling_service.py (append)

async def cancel_run(self, run_id: str) -> dict[str, Any] | None:
    """Cancel a running pipeline run.

    Delegates to PipelineRunner.cancel_run(). Idempotent.
    """
    run = await self._runs.get_by_id(run_id)
    if not run:
        return None

    status = run.get("status", "")
    if status in ("success", "failed", "cancelled"):
        # Already terminal — return current state
        return run

    cancelled = await self._runner.cancel_run(run_id)
    await self._audit.log("pipeline.cancel", "pipeline_run", run_id)

    # Re-fetch updated status
    return await self._runs.get_by_id(run_id)
```

### 9B.5f Files to Modify

| File | Change |
|------|--------|
| `packages/core/src/zorivest_core/domain/enums.py` | Add `CANCELLING = "cancelling"` to PipelineStatus |
| `packages/core/src/zorivest_core/services/pipeline_runner.py` | Add `_active_tasks` dict; `cancel_run()` method; cooperative check in step loop; `_is_cancelling()` check |
| `packages/core/src/zorivest_core/services/scheduling_service.py` | Add `cancel_run()` method |
| `packages/api/src/zorivest_api/routes/scheduling.py` | Add `POST /runs/{run_id}/cancel` endpoint |

### 9B.5g Verification

```bash
uv run pytest tests/unit/test_pipeline_runner.py -k "cancel" -v
uv run pytest tests/unit/test_scheduling_service.py -k "cancel" -v
uv run pytest tests/unit/test_api_scheduling.py -k "cancel" -v
```

---

## Step 9B.6: Pipeline End-to-End Test Harness (MEU-PW8)

### 9B.6a Rationale

No integration tests currently validate that a policy document traverses the complete execution path:

```
SchedulingService.trigger_run()
     → PipelineRunner.run()
          → Step type lookup (registry)
               → RefResolver (param resolution)
                    → Step.execute() (all 5 types)
                         → Persistence hooks
                              → Audit trail
```

The test harness creates reusable test policies (fixtures) and validates every service layer from input to database state.

### 9B.6b Test Policy Fixtures

```python
# tests/fixtures/policies.py (NEW)

"""Reusable test policy documents for pipeline integration testing.

Each fixture is a valid PolicyDocument JSON dict ready for use with
SchedulingService.create_policy() or PipelineRunner.run().
"""

# Happy path: mock fetch → transform → store (3 step types)
SMOKE_POLICY_BASIC = {
    "schema_version": 1,
    "name": "smoke-basic",
    "trigger": {"cron_expression": "0 9 * * 1-5", "timezone": "UTC", "enabled": True},
    "steps": [
        {"id": "fetch_data", "type": "mock_fetch", "params": {"data": [1, 2, 3]}},
        {"id": "transform_data", "type": "mock_transform", "params": {"source": {"ref": "ctx.fetch_data.output.data"}}},
        {"id": "store_result", "type": "mock_store", "params": {"data": {"ref": "ctx.transform_data.output.result"}}},
    ],
}

# Error mode: fail_pipeline (default)
POLICY_ERROR_FAIL = {
    "schema_version": 1,
    "name": "smoke-error-fail",
    "trigger": {"cron_expression": "0 0 * * *", "timezone": "UTC", "enabled": True},
    "steps": [
        {"id": "will_fail", "type": "mock_fail", "params": {"error_msg": "intentional"}},
        {"id": "never_reached", "type": "mock_fetch", "params": {}},
    ],
}

# Error mode: log_and_continue
POLICY_ERROR_CONTINUE = {
    "schema_version": 1,
    "name": "smoke-error-continue",
    "trigger": {"cron_expression": "0 0 * * *", "timezone": "UTC", "enabled": True},
    "steps": [
        {"id": "will_fail", "type": "mock_fail", "params": {"error_msg": "non-fatal"},
         "on_error": "log_and_continue"},
        {"id": "should_run", "type": "mock_fetch", "params": {"data": [42]}},
    ],
}

# Dry-run: side-effect step should be skipped
POLICY_DRY_RUN = {
    "schema_version": 1,
    "name": "smoke-dry-run",
    "trigger": {"cron_expression": "0 0 * * *", "timezone": "UTC", "enabled": True},
    "steps": [
        {"id": "fetch", "type": "mock_fetch", "params": {"data": [1]}},
        {"id": "side_effect", "type": "mock_side_effect", "params": {}},
    ],
}

# Skip condition
POLICY_SKIP_CONDITION = {
    "schema_version": 1,
    "name": "smoke-skip",
    "trigger": {"cron_expression": "0 0 * * *", "timezone": "UTC", "enabled": True},
    "steps": [
        {"id": "fetch", "type": "mock_fetch", "params": {"data": []}},
        {"id": "conditional", "type": "mock_transform", "params": {},
         "skip_if": {"field": "ctx.fetch.output.count", "operator": "eq", "value": 0}},
    ],
}

# Cancel: deliberately slow step
POLICY_CANCELLABLE = {
    "schema_version": 1,
    "name": "smoke-cancel",
    "trigger": {"cron_expression": "0 0 * * *", "timezone": "UTC", "enabled": True},
    "steps": [
        {"id": "slow_step", "type": "mock_slow", "params": {"delay_seconds": 60}},
        {"id": "after_cancel", "type": "mock_fetch", "params": {}},
    ],
}

# Unicode resilience (PW4 regression)
POLICY_UNICODE_ERROR = {
    "schema_version": 1,
    "name": "smoke-unicode",
    "trigger": {"cron_expression": "0 0 * * *", "timezone": "UTC", "enabled": True},
    "steps": [
        {"id": "unicode_fail", "type": "mock_fail",
         "params": {"error_msg": "Résumé: ñ, ü, ™, 日本語 — error with non-ASCII"}},
    ],
}
```

### 9B.6c Mock Step Implementations

```python
# tests/fixtures/mock_steps.py (NEW)

"""Mock step implementations for pipeline integration testing.

Auto-registered in the StepRegistry via __init_subclass__.
Must be imported before tests that use them.
"""

import asyncio
from typing import Any

from zorivest_core.domain.enums import PipelineStatus
from zorivest_core.domain.pipeline import StepContext, StepResult
from zorivest_core.domain.step_registry import RegisteredStep


class MockFetchStep(RegisteredStep):
    """Returns canned data from params. No HTTP calls."""
    type_name = "mock_fetch"
    side_effects = False

    async def execute(self, params: dict, context: StepContext) -> StepResult:
        return StepResult(
            status=PipelineStatus.SUCCESS,
            output={"data": params.get("data", []), "count": len(params.get("data", []))},
        )


class MockTransformStep(RegisteredStep):
    """Passthrough transform — returns source data as result."""
    type_name = "mock_transform"
    side_effects = False

    async def execute(self, params: dict, context: StepContext) -> StepResult:
        return StepResult(
            status=PipelineStatus.SUCCESS,
            output={"result": params.get("source", params)},
        )


class MockStoreStep(RegisteredStep):
    """Mock store — logs data without actual DB write."""
    type_name = "mock_store"
    side_effects = True

    async def execute(self, params: dict, context: StepContext) -> StepResult:
        return StepResult(
            status=PipelineStatus.SUCCESS,
            output={"stored": True, "row_count": len(params.get("data", []))},
        )


class MockFailStep(RegisteredStep):
    """Always fails with configurable error message."""
    type_name = "mock_fail"
    side_effects = False

    async def execute(self, params: dict, context: StepContext) -> StepResult:
        return StepResult(
            status=PipelineStatus.FAILED,
            error=params.get("error_msg", "Mock failure"),
        )


class MockSlowStep(RegisteredStep):
    """Deliberately slow step for cancel testing."""
    type_name = "mock_slow"
    side_effects = False

    async def execute(self, params: dict, context: StepContext) -> StepResult:
        delay = params.get("delay_seconds", 10)
        await asyncio.sleep(delay)
        return StepResult(status=PipelineStatus.SUCCESS, output={"waited": delay})


class MockSideEffectStep(RegisteredStep):
    """Step with side_effects=True for dry-run testing."""
    type_name = "mock_side_effect"
    side_effects = True

    async def execute(self, params: dict, context: StepContext) -> StepResult:
        return StepResult(
            status=PipelineStatus.SUCCESS,
            output={"side_effect": "executed"},
        )
```

### 9B.6d Integration Test Suite

```python
# tests/integration/test_pipeline_e2e.py (NEW — outline)

"""End-to-end pipeline integration tests.

Validates the complete policy execution lifecycle through all service layers:
SchedulingService → PipelineRunner → Steps → Persistence → Audit

Uses SQLAlchemy in-memory SQLite (real UoW, no stubs).
"""

import pytest
# Import fixtures to register mock steps
import tests.fixtures.mock_steps  # noqa: F401

class TestPolicyLifecycle:
    """Test create → approve → run → history → delete."""
    async def test_create_approve_run_success(self): ...
    async def test_run_unapproved_policy_rejected(self): ...
    async def test_delete_policy_unschedules(self): ...

class TestPipelineExecution:
    """Test step execution through PipelineRunner."""
    async def test_all_steps_execute_in_order(self): ...
    async def test_ref_resolution_across_steps(self): ...
    async def test_step_output_persisted_to_db(self): ...

class TestErrorModes:
    """Test fail_pipeline, log_and_continue, retry_then_fail."""
    async def test_fail_pipeline_aborts(self): ...
    async def test_log_and_continue_proceeds(self): ...
    async def test_retry_exhaustion_fails(self): ...

class TestDryRunAndSkip:
    """Test dry_run mode and skip_if conditions."""
    async def test_dry_run_skips_side_effects(self): ...
    async def test_skip_condition_evaluated(self): ...

class TestCancellation:
    """Test cancel infrastructure (PW7)."""
    async def test_cancel_running_pipeline(self): ...
    async def test_cancel_idempotent_on_completed(self): ...

class TestZombieRecovery:
    """Test zombie detection and cleanup (PW5)."""
    async def test_startup_zombie_recovery(self): ...
    async def test_no_dual_write_records(self): ...

class TestResilience:
    """Test encoding and edge cases (PW4, PW6)."""
    async def test_unicode_error_messages_no_crash(self): ...
    async def test_bytes_output_serializable(self): ...

class TestAuditTrail:
    """Test audit log completeness."""
    async def test_run_creates_audit_entry(self): ...
    async def test_cancel_creates_audit_entry(self): ...
```

### 9B.6e Files to Create / Modify

| File | Change |
|------|--------|
| `tests/fixtures/__init__.py` | **NEW**: Package init |
| `tests/fixtures/policies.py` | **NEW**: Test policy document fixtures |
| `tests/fixtures/mock_steps.py` | **NEW**: Mock step implementations for testing |
| `tests/integration/test_pipeline_e2e.py` | **NEW**: End-to-end integration test suite |
| `tests/conftest.py` | Add async SQLAlchemy fixtures for pipeline E2E tests |

### 9B.6f Verification

```bash
# Run full E2E suite
uv run pytest tests/integration/test_pipeline_e2e.py -v

# Coverage report for pipeline services
uv run pytest tests/ -k "pipeline" --cov=packages/core/src/zorivest_core/services --cov-report=term
```

---

## 9B.7 Dependency Graph

```
                    ┌────────┐
                    │ MEU-PW4│ ← Charmap fix (quick win, no deps)
                    └────┬───┘
                         │
                    ┌────▼───┐
                    │ MEU-PW5│ ← Zombie fix (needs PW4 for clean logs)
                    └────┬───┘
                         │
              ┌──────────┼──────────┐
              │                     │
         ┌────▼───┐           ┌────▼───┐
         │ MEU-PW6│           │ MEU-PW7│  ← PW6 and PW7 are parallel
         │  URLs  │           │ Cancel │    after PW5
         └────┬───┘           └────┬───┘
              │                     │
              └──────────┬──────────┘
                    ┌────▼───┐
                    │ MEU-PW8│ ← E2E test harness (needs all fixes)
                    └────────┘
```

## 9B.8 Risk Assessment

| Risk | Mitigation |
|------|-----------|
| Structlog reconfiguration breaks existing log formatting | Test log output format before/after |
| Dual-write elimination changes `run_id` semantics | Backward-compatible: `run_id=""` preserves old behavior |
| URL builders may not cover all 14 providers | GenericUrlBuilder fallback; extend per-provider as needed |
| Cancel + asyncio.Task.cancel() may not interrupt httpx | Cooperative step-boundary check provides reliable cancellation |
| Mock steps pollute the global step registry | Scoped registration in conftest; cleanup after test session |

## 9B.9 Overall Verification Plan

```bash
# MEU gate after all PW4-PW8 complete
uv run python tools/validate_codebase.py --scope meu

# Full pipeline test suite
uv run pytest tests/ -k "pipeline" -v

# Type checking
uv run pyright packages/core packages/infrastructure packages/api

# Lint
uv run ruff check packages/
```
