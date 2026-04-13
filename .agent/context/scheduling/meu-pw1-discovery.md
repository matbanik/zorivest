# MEU-PW1: Pipeline Runtime Wiring — Discovery & Work Items

> **Matrix:** P2.5 item 49.4 · **Slug:** `pipeline-runtime-wiring` · **Status:** ⬜ Planned  
> **Resolves:** `[SCHED-PIPELINE-WIRING]` known issue + partial `[STUB-RETIRE]`

---

## Problem Statement

All five pipeline steps (`FetchStep`, `TransformStep`, `StoreReportStep`, `RenderStep`, `SendStep`) are individually implemented and registered in the step registry. However, `PipelineRunner` does not inject the service dependencies they require at runtime. An end-to-end pipeline execution will fail with `ValueError: provider_adapter required in context.outputs for FetchStep`.

This MEU bridges the gap between the **already-built** pipeline engine (items 42–49) and the **already-built** market data + email infrastructure (Phase 8, MEU-73) by wiring service adapters into `PipelineRunner.__init__` and the `initial_outputs` injection block.

---

## Root Cause Analysis

### 1. Missing `provider_adapter` in PipelineRunner

**Where it's needed — FetchStep:**
- [fetch_step.py:117-121](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/fetch_step.py#L117-L121) — `_fetch_from_provider()` reads `context.outputs.get("provider_adapter")` and raises `ValueError` if `None`

**Where it should be injected — PipelineRunner:**
- [pipeline_runner.py:50-63](file:///p:/zorivest/packages/core/src/zorivest_core/services/pipeline_runner.py#L50-L63) — Constructor accepts `uow`, `ref_resolver`, `condition_evaluator`, `delivery_repository`, `smtp_config` but **no `provider_adapter`**
- [pipeline_runner.py:93-98](file:///p:/zorivest/packages/core/src/zorivest_core/services/pipeline_runner.py#L93-L98) — `initial_outputs` dict only injects `delivery_repository` and `smtp_config`

**Where it's wired — main.py:**
- [main.py:241](file:///p:/zorivest/packages/api/src/zorivest_api/main.py#L241) — `PipelineRunner(uow, RefResolver(), ConditionEvaluator())` — no keyword args for `delivery_repository`, `smtp_config`, or `provider_adapter`

### 2. SMTP Config Key Mismatch

**What SendStep expects:**
- [send_step.py:108-111](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/send_step.py#L108-L111):
  ```python
  smtp_host = smtp_config.get("host", "localhost")
  smtp_port = smtp_config.get("port", 587)
  sender = smtp_config.get("sender", "noreply@zorivest.local")
  ```

**What EmailProviderService returns:**
- [email_provider_service.py:49-56](file:///p:/zorivest/packages/core/src/zorivest_core/services/email_provider_service.py#L49-L56):
  ```python
  "smtp_host": row.smtp_host,    # ← key is "smtp_host" not "host"
  "from_email": row.from_email,  # ← key is "from_email" not "sender"
  ```

**Impact:** SendStep would get `None` for all SMTP fields and fall back to defaults (`localhost:587`, `noreply@zorivest.local`).

### 3. Dead Stubs Awaiting Deletion

**Location:** Previously in `stubs.py` — `StubMarketDataService` and `StubProviderConnectionService` were documented as "Retained stubs (blocked on future MEUs)" but their real services are already wired at:
- [main.py:208](file:///p:/zorivest/packages/api/src/zorivest_api/main.py#L208) — `MarketDataService` (real)
- [main.py:219](file:///p:/zorivest/packages/api/src/zorivest_api/main.py#L219) — `ProviderConnectionService` (real)

**Test that references the dead stub:**
- [test_provider_service_wiring.py:21](file:///p:/zorivest/tests/unit/test_provider_service_wiring.py#L21) — imports `StubProviderConnectionService` for negative assertion
- [test_provider_service_wiring.py:34-37](file:///p:/zorivest/tests/unit/test_provider_service_wiring.py#L34-L37) — `assert not isinstance(svc, StubProviderConnectionService)` — this negative check becomes impossible once the stub is deleted (the positive assertion at L39 already verifies correctness)

### 4. TransformStep `db_writer` Not Injected

**Where it's needed:**
- [transform_step.py:182-184](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/transform_step.py#L182-L184) — `_write_data()` reads `context.outputs.get("db_writer")` and raises `ValueError` if `None`

**Impact:** TransformStep will fail at the write phase because `db_writer` is never put into `initial_outputs`.

---

## Work Items

### WI-1: Add `provider_adapter` to PipelineRunner

| Aspect | Detail |
|--------|--------|
| **File** | [pipeline_runner.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/pipeline_runner.py) |
| **Change** | Add `provider_adapter: Any | None = None` to `__init__` (L50-58) |
| **Change** | Add `provider_adapter` to `initial_outputs` dict (L93-98) |
| **Spec ref** | [09-scheduling.md §9.3a](file:///p:/zorivest/docs/build-plan/09-scheduling.md) — PipelineRunner must inject service deps into StepContext |

### WI-2: Create `MarketDataProviderAdapter`

| Aspect | Detail |
|--------|--------|
| **New file** | `packages/core/src/zorivest_core/services/market_data_adapter.py` |
| **Purpose** | Bridge between `MarketDataService` (Phase 8) and the `provider_adapter` protocol expected by `FetchStep` |
| **Interface** | `async fetch(*, provider: str, data_type: str, criteria: dict) -> bytes` |
| **Wraps** | `MarketDataService.get_quotes()`, `.get_ohlcv()`, `.get_news()`, `.get_fundamentals()` — dispatches by `data_type` |
| **Spec ref** | [09-scheduling.md §9.4a](file:///p:/zorivest/docs/build-plan/09-scheduling.md) — FetchStep expects `provider_adapter` in context |

### WI-3: Add `get_smtp_runtime_config()` to EmailProviderService

| Aspect | Detail |
|--------|--------|
| **File** | [email_provider_service.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/email_provider_service.py) |
| **Change** | Add new method `get_smtp_runtime_config() -> dict` that returns keys matching what `SendStep` expects: `host`, `port`, `sender` |
| **Logic** | Translates internal keys: `smtp_host` → `host`, `from_email` → `sender`, `port` → `port` |
| **Password** | Must decrypt and include `password` and `username` for SMTP auth |
| **Spec ref** | [09-scheduling.md §9.8](file:///p:/zorivest/docs/build-plan/09-scheduling.md) — SendStep receives SMTP config from context |

### WI-4: Add `db_writer` to PipelineRunner

| Aspect | Detail |
|--------|--------|
| **File** | [pipeline_runner.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/pipeline_runner.py) |
| **Change** | Add `db_writer: Any | None = None` to `__init__` and inject into `initial_outputs` |
| **Purpose** | TransformStep reads `context.outputs["db_writer"]` to call `write_dispositions` functions |
| **Implementation** | Create thin adapter wrapping `write_append()`/`write_replace()`/`write_merge()` from [write_dispositions.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/repositories/write_dispositions.py) |
| **Spec ref** | [09-scheduling.md §9.5d](file:///p:/zorivest/docs/build-plan/09-scheduling.md) — Transform step writes via disposition functions |

### WI-5: Wire All Services in main.py

| Aspect | Detail |
|--------|--------|
| **File** | [main.py](file:///p:/zorivest/packages/api/src/zorivest_api/main.py) |
| **Current** (L241) | `PipelineRunner(uow, RefResolver(), ConditionEvaluator())` |
| **Target** | Add keyword args: `provider_adapter=market_data_adapter`, `delivery_repository=uow.deliveries`, `smtp_config=email_svc.get_smtp_runtime_config()`, `db_writer=db_write_adapter` |
| **Dependencies** | Requires `MarketDataProviderAdapter` (WI-2) and `DbWriteAdapter` (WI-4) to be available |

### WI-6: Delete Dead Stubs

| Aspect | Detail |
|--------|--------|
| **Files** | Remove `StubMarketDataService` and `StubProviderConnectionService` from wherever they exist |
| **Test update** | [test_provider_service_wiring.py:21,34-37](file:///p:/zorivest/tests/unit/test_provider_service_wiring.py#L21) — Remove import and negative `isinstance` assertion; positive assertion at L39 is sufficient |
| **Known issue** | `[STUB-RETIRE]` — partially resolved by this deletion |

### WI-7: Integration Test

| Aspect | Detail |
|--------|--------|
| **New test** | `tests/integration/test_pipeline_e2e.py` |
| **Scope** | Verify `PipelineRunner.run()` with a minimal 2-step policy (fetch + transform) completes without `ValueError` |
| **Approach** | Mock the `MarketDataProviderAdapter.fetch()` to return test data; verify `StepContext.outputs` contains all injected services |

---

## Build Doc References

| Document | Section | Relevance |
|----------|---------|-----------|
| [09-scheduling.md §9.3a](file:///p:/zorivest/docs/build-plan/09-scheduling.md) | PipelineRunner | Constructor spec, service injection |
| [09-scheduling.md §9.4a](file:///p:/zorivest/docs/build-plan/09-scheduling.md) | FetchStep | `provider_adapter` protocol |
| [09-scheduling.md §9.5d](file:///p:/zorivest/docs/build-plan/09-scheduling.md) | TransformStep | Write dispositions, `db_writer` expected |
| [09-scheduling.md §9.8a](file:///p:/zorivest/docs/build-plan/09-scheduling.md) | SendStep | SMTP config key contract |
| [build-priority-matrix.md §P2.5](file:///p:/zorivest/docs/build-plan/build-priority-matrix.md#L106) | Item 49.4 | MEU-PW1 matrix entry |
| [known-issues.md](file:///p:/zorivest/.agent/context/known-issues.md) | `[SCHED-PIPELINE-WIRING]` | Root known issue |
| [spec-vs-code-audit.md](file:///p:/zorivest/.agent/context/scheduling/spec-vs-code-audit.md) | Full audit | 09-scheduling.md compliance |

---

## Source Code Cross-Reference

| File | Lines | Role |
|------|-------|------|
| [pipeline_runner.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/pipeline_runner.py) | 50-63, 93-98 | Constructor + initial_outputs (modify) |
| [fetch_step.py](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/fetch_step.py) | 117-121 | Consumer of `provider_adapter` (read-only) |
| [transform_step.py](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/transform_step.py) | 182-184 | Consumer of `db_writer` (read-only) |
| [send_step.py](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/send_step.py) | 108-111 | Consumer of `smtp_config` (read-only) |
| [email_provider_service.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/email_provider_service.py) | 40-66 | get_config() key names (modify) |
| [write_dispositions.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/repositories/write_dispositions.py) | 78-168 | Write functions to wrap (read-only) |
| [main.py](file:///p:/zorivest/packages/api/src/zorivest_api/main.py) | 241 | Wiring site (modify) |
| [test_provider_service_wiring.py](file:///p:/zorivest/tests/unit/test_provider_service_wiring.py) | 21, 34-37 | Dead stub reference (modify) |

---

## Dependency Graph

```
WI-2 (MarketDataProviderAdapter) ──┐
WI-3 (get_smtp_runtime_config)  ───┤
WI-4 (DbWriteAdapter)          ───┼──→ WI-1 (PipelineRunner.__init__) ──→ WI-5 (main.py wiring)
                                   │
WI-6 (Delete dead stubs)       ───┘    WI-7 (Integration test)
                                              ↑
                                       depends on WI-5
```

**Recommended execution order:** WI-2 → WI-3 → WI-4 → WI-1 → WI-5 → WI-6 → WI-7
