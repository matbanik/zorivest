---
meu: MEU-PW1
slug: pipeline-runtime-wiring
build_plan_ref: "09-scheduling §9.49.4"
date: 2026-04-12
status: complete
verbosity: standard
---

# Handoff — MEU-PW1: Pipeline Runtime Wiring

## Summary

Expanded `PipelineRunner.__init__` with 6 new keyword-only dependencies, created `DbWriteAdapter` to bridge `TransformStep` to `write_dispositions`, added `get_smtp_runtime_config()` to `EmailProviderService` with key remapping and Fernet decryption, wired all 7 runtime deps in `main.py`, deleted 2 dead stubs, and verified dependency wiring with 33 new tests (22 unit + 11 integration).

<!-- CACHE BOUNDARY -->

## Feature Intent Contract

| AC | Description | Source | Tests |
|----|-------------|--------|-------|
| AC-1 | `PipelineRunner` constructor accepts 8 keyword-only params (all default to `None`) | Spec | `test_accepts_all_8_kwargs`, `test_all_kwargs_default_to_none`, `test_unknown_kwarg_raises_type_error`, `test_stores_each_kwarg_on_instance` |
| AC-2 | All non-None deps appear in `context.outputs` when `run()` executes; None deps are excluded | Spec | `test_all_non_none_deps_injected_into_context`, `test_none_deps_excluded_from_initial_outputs`, `test_step_can_access_injected_db_writer` |
| AC-3 | `DbWriteAdapter.write()` dispatches to `write_append/write_replace/write_merge` by disposition | Spec | `test_db_write_adapter.py` (6 tests) |
| AC-4 | `get_smtp_runtime_config()` remaps keys and decrypts password via Fernet | Spec | `test_smtp_runtime_config.py` (8 tests) |
| AC-5 | Dead stubs (`StubMarketDataService`, `StubProviderConnectionService`) are deleted | Spec | `test_stub_market_data_service_not_importable`, `test_stub_provider_connection_service_not_importable` |
| AC-6 | All 7 non-None wired deps reach step execution context when `run()` is called | Spec | `test_run_with_inspector_step_populates_outputs` |
| AC-7 | `provider_adapter=None` deferred to MEU-PW2 | Spec | `test_pipeline_runner_provider_adapter_is_none` |

## Commands Executed

```bash
uv run pytest tests/unit/test_pipeline_runner_constructor.py tests/unit/test_smtp_runtime_config.py tests/unit/test_db_write_adapter.py tests/integration/test_pipeline_wiring.py -x --tb=short -v
uv run pytest tests/ -x --tb=short
uv run pyright packages/
uv run ruff check packages/ tests/
uv run python tools/validate_codebase.py --scope meu
uv run python tools/export_openapi.py --check openapi.committed.json
```

## FAIL_TO_PASS Evidence

- **Red phase**: All 33 tests written before implementation. Constructor tests failed with `TypeError` (missing kwargs), adapter tests failed with `ModuleNotFoundError` (adapter not yet created), SMTP tests failed with `AttributeError` (method not yet added).
- **Green phase**: Implementation added in order — constructor expansion → adapter creation → SMTP method → main.py wiring → stub deletion. Each group turned green sequentially.

## Changed Files

```diff
# packages/core/src/zorivest_core/services/pipeline_runner.py
# Constructor expanded with 6 new kwargs; initial_outputs uses dict comprehension
+    provider_adapter: Any | None = None,
+    db_writer: Any | None = None,
+    db_connection: Any | None = None,
+    report_repository: Any | None = None,
+    template_engine: Any | None = None,
+    pipeline_state_repo: Any | None = None,

# packages/core/src/zorivest_core/services/email_provider_service.py
# New: get_smtp_runtime_config() — key remapping + Fernet decryption
+    def get_smtp_runtime_config(self) -> dict[str, str | int]:

# packages/infrastructure/src/zorivest_infra/adapters/__init__.py [NEW]
# packages/infrastructure/src/zorivest_infra/adapters/db_write_adapter.py [NEW]
# Dispatches to write_append/write_replace/write_merge by disposition

# packages/api/src/zorivest_api/main.py
# Wire 7 runtime deps into PipelineRunner (provider_adapter=None)
+    _db_write_adapter = DbWriteAdapter(session=uow._session)
+    _smtp_runtime_config = app.state.email_provider_service.get_smtp_runtime_config()
+    pipeline_runner = PipelineRunner(uow, RefResolver(), ConditionEvaluator(),
+        delivery_repository=uow.deliveries, smtp_config=_smtp_runtime_config, ...)

# packages/api/src/zorivest_api/stubs.py
# Deleted: StubMarketDataService, StubProviderConnectionService

# tests/unit/test_provider_service_wiring.py
# Removed: StubProviderConnectionService import + negative isinstance assertion
```

## New Test Files

| File | Tests | Coverage |
|------|------:|----------|
| `tests/unit/test_pipeline_runner_constructor.py` | 7 | Constructor signature, instance attrs, initial_outputs with InspectorStep |
| `tests/unit/test_smtp_runtime_config.py` | 8 | Key remapping, decryption, defaults, fallbacks |
| `tests/unit/test_db_write_adapter.py` | 6 | Dispatch, negatives, interface contract |
| `tests/integration/test_pipeline_wiring.py` | 11 | All 7 deps + 1 None slot + stub deletion + run() execution |

## Evidence

| Check | Result |
|-------|--------|
| pytest (MEU scope) | 22 unit + 11 integ = 33 passed |
| pyright | 0 errors |
| ruff | all checks passed |
| MEU gate | 8/8 PASS |
| OpenAPI drift | no drift |
| Anti-placeholder | 0 matches |

## Residual Risk

- `provider_adapter=None` — FetchStep will still fail at runtime. Deferred to MEU-PW2 (MarketDataProviderAdapter).
- 3 remaining stubs (`StubAnalyticsService`, `StubReviewService`, `StubTaxService`) blocked on MEU-104–148.

## Resolved Issues

- `[SCHED-PIPELINE-WIRING]` — fully resolved (moved to archive)
- `[STUB-RETIRE]` — Phase 2 stubs deleted; Phase 3 tracked

## Codex Validation Report

See [critical-review](2026-04-12-pipeline-runtime-wiring-implementation-critical-review.md) for full Codex review thread (original findings → corrections → recheck).

**Runtime bugfix (2026-04-12):** `get_smtp_runtime_config()` — wrapped `_decrypt_password()` in try/except to handle `InvalidToken` from corrupt/plaintext SMTP password data. Without this fix, API startup crashes when the stored password is not a valid Fernet token.
