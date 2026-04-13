---
project: "2026-04-12-pipeline-runtime-wiring"
date: "2026-04-12"
source: "docs/build-plan/09-scheduling.md §49.4, .agent/context/scheduling/meu-pw1-scope.md"
meus: ["MEU-PW1"]
status: "draft"
template_version: "2.0"
---

# Implementation Plan: Pipeline Runtime Wiring

> **Project**: `2026-04-12-pipeline-runtime-wiring`
> **Build Plan Section(s)**: bp09 §49.4 (P2.5b — Wiring & Quality)
> **Status**: `draft`

---

## Goal

Make 4 of 5 pipeline step types operational by wiring existing service implementations into `PipelineRunner`. Currently the runner is instantiated with only `uow`, `RefResolver`, and `ConditionEvaluator` — step types (`transform`, `store_report`, `render`, `send`) crash at runtime because their required `context.outputs` keys are missing. This MEU expands the constructor, creates one thin adapter, fixes the SMTP config bridge, deletes dead stubs, and verifies end-to-end with an integration test.

After this MEU, pipelines with `transform → store_report → render → send` steps complete without errors. `FetchStep` still requires `provider_adapter` (deferred to MEU-PW2).

---

## User Review Required

> [!IMPORTANT]
> **No breaking changes.** All modifications are additive (new kwargs with `None` defaults). Existing tests are unaffected because the constructor signature is backward-compatible.

> [!NOTE]
> `StubMarketDataService` and `StubProviderConnectionService` are confirmed dead code — real services were wired in main.py at L208/L219 since MEU-65. The stubs.py import in main.py was already narrowed to `StubAnalyticsService, StubReviewService, StubTaxService` (L48-52). Deleting the stub classes is safe.

---

## Proposed Changes

### MEU-PW1: Pipeline Runtime Wiring

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| PipelineRunner accepts 8 keyword params (7 wired, `provider_adapter` = `None` until PW2) | Spec | meu-pw1-scope.md §1 |
| `initial_outputs` populates 8 keys when non-None | Spec | meu-pw1-scope.md §1, pipeline_runner.py L94-98 pattern |
| `get_smtp_runtime_config()` returns `{host, port, sender, username, password}` | Spec + Local Canon | meu-pw1-scope.md §3, send_step.py L108-111 confirms key names |
| SMTP password decryption via Fernet | Local Canon | email_provider_service.py L34-36 `_decrypt_password` pattern |
| `DbWriteAdapter.write(df, table, disposition)` signature | Local Canon | transform_step.py L185-188 confirms call interface |
| DbWriteAdapter internally dispatches to `write_append`/`write_replace`/`write_merge` | Spec | meu-pw1-scope.md §2, write_dispositions.py function signatures |
| Sandboxed connection via `create_sandboxed_connection(db_path)` | Local Canon | `zorivest_infra.security.sql_sandbox` L44 |
| Template engine via `create_template_engine()` | Local Canon | `zorivest_infra.rendering.template_engine` L25 |
| `uow.deliveries`, `uow.reports`, `uow.pipeline_state` exist | Local Canon | unit_of_work.py L71-76 |
| Dead stubs deleted | Spec | meu-pw1-scope.md §5, known-issues.md `[STUB-RETIRE]` |

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-1 | PipelineRunner constructor accepts 8 keyword params (`delivery_repository`, `smtp_config`, `provider_adapter`, `db_writer`, `db_connection`, `report_repository`, `template_engine`, `pipeline_state_repo`) | Spec | `PipelineRunner(uow, rr, ce, unknown_param=1)` raises `TypeError` |
| AC-2 | All 8 keys present in `initial_outputs` dict when runner calls `run()` | Spec | Step accessing `context.outputs.get("db_writer")` returns the injected adapter |
| AC-3 | `EmailProviderService.get_smtp_runtime_config()` returns dict with `host`, `port`, `sender`, `username`, `password` keys | Spec | Missing config row → returns safe defaults with all 5 keys |
| AC-4 | `DbWriteAdapter.write()` dispatches to `write_append`/`write_replace`/`write_merge` by disposition parameter | Spec | Invalid disposition raises `ValueError` |
| AC-5 | `StubMarketDataService` and `StubProviderConnectionService` deleted from stubs.py | Spec | `from zorivest_api.stubs import StubMarketDataService` raises `ImportError` |
| AC-6 | Integration test passes: 3-step pipeline (`store_report→render→send`) completes with `status=COMPLETED` | Spec | Pipeline with `provider_adapter=None` + FetchStep → fails with `ValueError` (expected until PW2) |
| AC-7 | All existing tests continue to pass (`pytest`, `pyright`, `ruff` clean) | Spec | N/A |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| [pipeline_runner.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/pipeline_runner.py) | modify | Add 6 new kwargs to `__init__`; expand `initial_outputs` block |
| [email_provider_service.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/email_provider_service.py) | modify | Add `get_smtp_runtime_config()` method |
| [db_write_adapter.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/adapters/db_write_adapter.py) | **new** | Thin adapter wrapping `write_dispositions.py` functions |
| [main.py](file:///p:/zorivest/packages/api/src/zorivest_api/main.py) | modify | Wire 7 runtime kwargs into PipelineRunner (`provider_adapter` remains `None` until PW2); add imports for `create_sandboxed_connection`, `create_template_engine`, `DbWriteAdapter` |
| [stubs.py](file:///p:/zorivest/packages/api/src/zorivest_api/stubs.py) | modify | Delete `StubMarketDataService` (~18 lines) and `StubProviderConnectionService` (~12 lines); update docstring |
| [test_provider_service_wiring.py](file:///p:/zorivest/tests/unit/test_provider_service_wiring.py) | modify | Remove import of `StubProviderConnectionService`; remove L34-37 negative `isinstance` assertion |
| [test_pipeline_wiring.py](file:///p:/zorivest/tests/integration/test_pipeline_wiring.py) | **new** | Integration test: 3-step pipeline completes; validates all context.outputs keys populated |
| [test_pipeline_runner_constructor.py](file:///p:/zorivest/tests/unit/test_pipeline_runner_constructor.py) | **new** | Unit tests for expanded constructor + initial_outputs injection |
| [test_smtp_runtime_config.py](file:///p:/zorivest/tests/unit/test_smtp_runtime_config.py) | **new** | Unit tests for `get_smtp_runtime_config()` key mapping + decryption |
| [test_db_write_adapter.py](file:///p:/zorivest/tests/unit/test_db_write_adapter.py) | **new** | Unit tests for DbWriteAdapter dispatch logic |

---

## Out of Scope

- ❌ `MarketDataProviderAdapter` creation (→ MEU-PW2)
- ❌ `FetchStep._check_cache()` implementation (→ MEU-PW2)
- ❌ `PipelineRateLimiter` integration (→ MEU-PW2)
- ❌ Market data ORM models (→ MEU-PW3)
- ❌ Pandera schemas for quotes/news/fundamentals (→ MEU-PW3)
- ❌ MCP tool description audit (→ MEU-TD1)

---

## BUILD_PLAN.md Audit

This project completes MEU-PW1. After execution:
1. **Correct** the `docs/BUILD_PLAN.md` MEU-PW1 description to match the refined scope (remove `MarketDataProviderAdapter` reference, clarify `provider_adapter` is a `None` slot)
2. Update status from `⬜` to `✅`
3. Verify no stale refs to `pipeline-runtime-wiring`

---

## Verification Plan

### 1. Unit Tests (TDD Red→Green)
```powershell
uv run pytest tests/unit/test_pipeline_runner_constructor.py tests/unit/test_smtp_runtime_config.py tests/unit/test_db_write_adapter.py -x --tb=short -v *> C:\Temp\zorivest\pytest-pw1-unit.txt; Get-Content C:\Temp\zorivest\pytest-pw1-unit.txt | Select-Object -Last 40
```

### 2. Integration Test
```powershell
uv run pytest tests/integration/test_pipeline_wiring.py -x --tb=short -v *> C:\Temp\zorivest\pytest-pw1-integ.txt; Get-Content C:\Temp\zorivest\pytest-pw1-integ.txt | Select-Object -Last 30
```

### 3. Existing Tests Not Broken
```powershell
uv run pytest tests/ -x --tb=short -v *> C:\Temp\zorivest\pytest-full.txt; Get-Content C:\Temp\zorivest\pytest-full.txt | Select-Object -Last 40
```

### 4. Type Check
```powershell
uv run pyright packages/ *> C:\Temp\zorivest\pyright.txt; Get-Content C:\Temp\zorivest\pyright.txt | Select-Object -Last 30
```

### 5. Lint
```powershell
uv run ruff check packages/ *> C:\Temp\zorivest\ruff.txt; Get-Content C:\Temp\zorivest\ruff.txt | Select-Object -Last 20
```

### 6. Stub Deletion Verification
```powershell
rg "StubMarketDataService|StubProviderConnectionService" packages/ tests/ *> C:\Temp\zorivest\stub-check.txt; Get-Content C:\Temp\zorivest\stub-check.txt
```
Expected: 0 matches.

### 7. Anti-Placeholder Scan
```powershell
rg "TODO|FIXME|NotImplementedError" packages/core/src/zorivest_core/services/pipeline_runner.py packages/core/src/zorivest_core/services/email_provider_service.py packages/infrastructure/src/zorivest_infra/adapters/db_write_adapter.py packages/api/src/zorivest_api/main.py *> C:\Temp\zorivest\placeholder-check.txt; Get-Content C:\Temp\zorivest\placeholder-check.txt
```
Expected: 0 matches.

### 8. OpenAPI Spec Drift Check (main.py modified)
```powershell
uv run python tools/export_openapi.py --check openapi.committed.json *> C:\Temp\zorivest\openapi-check.txt; Get-Content C:\Temp\zorivest\openapi-check.txt
```

### 9. MEU Gate
```powershell
uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate.txt; Get-Content C:\Temp\zorivest\validate.txt | Select-Object -Last 50
```

---

## Open Questions

None. All behaviors are fully specified between the scope document, source code inspection, and local canonical docs.

---

## Research References

- [meu-pw1-scope.md](file:///p:/zorivest/.agent/context/scheduling/meu-pw1-scope.md) — refined scope document
- [pipeline_runner.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/pipeline_runner.py) — current constructor
- [send_step.py](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/send_step.py) — SMTP key contract (L108-111)
- [transform_step.py](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/transform_step.py) — db_writer call interface (L185-188)
- [store_report_step.py](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/store_report_step.py) — db_connection/report_repository usage
- [render_step.py](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/render_step.py) — template_engine usage (L108)
- [write_dispositions.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/repositories/write_dispositions.py) — adapter target functions
- [unit_of_work.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/unit_of_work.py) — repo attributes confirmed (L71-76)
- [known-issues.md](file:///p:/zorivest/.agent/context/known-issues.md) — `[SCHED-PIPELINE-WIRING]`, `[STUB-RETIRE]`
