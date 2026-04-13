# MEU-PW1: Pipeline Runtime Wiring (Refined)

> **Matrix:** P2.5 item 49.4 · **Slug:** `pipeline-runtime-wiring`  
> **Status:** ⬜ Planned · **Effort:** S-M (1 session)  
> **Depends on:** MEU-90a ✅, MEU-85 ✅, MEU-88 ✅  
> **Resolves:** `[SCHED-PIPELINE-WIRING]` + partial `[STUB-RETIRE]`

---

## Objective

Make **4 of 5** pipeline step types operational by expanding `PipelineRunner`'s constructor, creating one thin adapter, fixing the SMTP bridge, and wiring everything in `main.py`. After this MEU, pipelines with `transform → store_report → render → send` steps complete without errors.

> [!NOTE]
> This MEU was originally scoped to include the `MarketDataProviderAdapter` (W-1). That work has been split into **MEU-PW2** because creating a new service with its own port interface, provider dispatch, and rate-limiting integration is a fundamentally different concern from wiring existing services.

---

## Gap Items Covered

| Item | Description | Category | Effort |
|------|-------------|----------|--------|
| W-9 | Add 6 missing constructor params to PipelineRunner | Wiring | S |
| W-2 | Create `DbWriteAdapter` (wraps `write_dispositions.py`) | Wiring | S |
| W-3 | Wire `ReportRepository` into initial_outputs | Wiring | XS |
| W-4 | Wire sandboxed `db_connection` into initial_outputs | Wiring | XS |
| W-5 | Wire `PipelineStateRepository` into initial_outputs | Wiring | XS |
| W-6 | Wire `template_engine` into initial_outputs | Wiring | XS |
| W-7 | Pass `delivery_repository` in main.py | Wiring | XS |
| W-8 | Pass `smtp_config` in main.py | Wiring | XS |
| D-1 | Fix SMTP key mismatch (`get_smtp_runtime_config()`) | Defect | S |
| D-5 | Delete dead stubs (`StubMarketDataService`, `StubProviderConnectionService`) | Hygiene | XS |

**Total: 10 items** (3 S + 7 XS)

---

## Deliverables

### 1. Expand PipelineRunner Constructor (W-9)

**File:** [pipeline_runner.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/pipeline_runner.py)

Add 6 new keyword-only params to `__init__` (L50-58):

```python
def __init__(
    self,
    uow: Any,
    ref_resolver: Any,
    condition_evaluator: Any,
    *,
    delivery_repository: Any | None = None,   # existing
    smtp_config: Any | None = None,           # existing
    provider_adapter: Any | None = None,      # NEW
    db_writer: Any | None = None,             # NEW
    db_connection: Any | None = None,         # NEW
    report_repository: Any | None = None,     # NEW
    template_engine: Any | None = None,       # NEW
    pipeline_state_repo: Any | None = None,   # NEW
) -> None:
```

Update `initial_outputs` injection block (L94-98) to include all 8 keys.

### 2. Create DbWriteAdapter (W-2)

**New file:** `packages/infrastructure/src/zorivest_infra/adapters/db_write_adapter.py`

Thin adapter wrapping [write_dispositions.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/repositories/write_dispositions.py) functions:

```python
class DbWriteAdapter:
    """Bridge between TransformStep and write_dispositions functions."""

    def __init__(self, session_factory):
        self._session_factory = session_factory

    async def write(self, df, table: str, disposition: str = "append"):
        """Dispatch to write_append/write_replace/write_merge."""
        ...
```

### 3. Fix SMTP Key Mismatch (D-1)

**File:** [email_provider_service.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/email_provider_service.py)

Add new method:

```python
async def get_smtp_runtime_config(self) -> dict[str, str | int]:
    """Return SMTP config with keys matching SendStep contract.

    Translates internal keys:
      smtp_host → host, from_email → sender
    Includes decrypted password for SMTP auth.
    """
    ...
```

**Key mapping:**

| SendStep expects | EmailProviderService stores | Translation |
|-----------------|---------------------------|-------------|
| `host` | `smtp_host` | Rename key |
| `port` | `port` | Pass through |
| `sender` | `from_email` | Rename key |
| `username` | `username` | Pass through |
| `password` | Fernet-encrypted | Decrypt + include |

### 4. Wire All Services in main.py (W-3 to W-8)

**File:** [main.py](file:///p:/zorivest/packages/api/src/zorivest_api/main.py) L241

Change from:
```python
pipeline_runner = PipelineRunner(uow, RefResolver(), ConditionEvaluator())
```

To:
```python
pipeline_runner = PipelineRunner(
    uow,
    RefResolver(),
    ConditionEvaluator(),
    delivery_repository=uow.deliveries,
    smtp_config=await email_svc.get_smtp_runtime_config(),
    # provider_adapter=...,  # Deferred to MEU-PW2
    db_writer=db_write_adapter,
    db_connection=create_sandboxed_connection(db_path),
    report_repository=uow.reports,
    template_engine=create_template_engine(),
    pipeline_state_repo=uow.pipeline_state,
)
```

### 5. Delete Dead Stubs (D-5)

**File:** [stubs.py](file:///p:/zorivest/packages/api/src/zorivest_api/stubs.py)

- Delete `StubMarketDataService` class (~25 lines)
- Delete `StubProviderConnectionService` class (~25 lines)
- Update docstring (L10-11) to remove references to deleted stubs

**File:** [test_provider_service_wiring.py](file:///p:/zorivest/tests/unit/test_provider_service_wiring.py)

- Remove L21: `from zorivest_api.stubs import StubProviderConnectionService`
- Remove L34-37: Negative `isinstance` assertion (L39 positive check is sufficient)

### 6. Integration Test

**New file:** `tests/integration/test_pipeline_wiring.py`

Test: A pipeline policy with `store_report → render → send` steps completes without ValueError. Mock the store_report query results; verify all context.outputs keys are populated.

---

## Files Changed

| File | Change Type | Package |
|------|-------------|---------|
| `pipeline_runner.py` | Modify (constructor + initial_outputs) | core |
| `email_provider_service.py` | Modify (new method) | core |
| `db_write_adapter.py` | **NEW** | infra |
| `main.py` | Modify (wiring block) | api |
| `stubs.py` | Modify (delete 2 classes) | api |
| `test_provider_service_wiring.py` | Modify (remove dead import) | tests |
| `test_pipeline_wiring.py` | **NEW** | tests |

**Blast radius:** 5 modified + 2 new = 7 files across 4 packages.

---

## Acceptance Criteria

- **AC-1:** PipelineRunner constructor accepts 8 keyword params (delivery_repository, smtp_config, provider_adapter, db_writer, db_connection, report_repository, template_engine, pipeline_state_repo)
- **AC-2:** All 8 keys present in `initial_outputs` dict when runner calls `run()`
- **AC-3:** `EmailProviderService.get_smtp_runtime_config()` returns dict with `host`, `port`, `sender`, `username`, `password` keys
- **AC-4:** `DbWriteAdapter.write()` dispatches to `write_append`/`write_replace`/`write_merge` by disposition parameter
- **AC-5:** `StubMarketDataService` and `StubProviderConnectionService` deleted from stubs.py
- **AC-6:** Integration test passes: 3-step pipeline (store_report→render→send) completes with status=COMPLETED
- **AC-7:** All existing tests continue to pass (`pytest`, `pyright`, `ruff` clean)

---

## What This MEU Does NOT Do

- ❌ Does not create `MarketDataProviderAdapter` (→ MEU-PW2)
- ❌ Does not implement `FetchStep._check_cache()` (→ MEU-PW2)
- ❌ Does not integrate `PipelineRateLimiter` (→ MEU-PW2)
- ❌ Does not create market data ORM models (→ MEU-PW3)
- ❌ Does not add Pandera schemas for quotes/news/fundamentals (→ MEU-PW3)

After this MEU, `FetchStep` still crashes (provider_adapter=None). That's intentional — PW2 addresses it.
