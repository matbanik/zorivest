# Validation Corrections — Source Code Audit

> Systematic verification of every factual claim in `known-issues-meu-analysis.md` against actual source code.
> Date: 2026-04-12

---

## Validation Matrix

| # | Claim | Source File(s) Checked | Verdict | Impact |
|---|-------|----------------------|---------|--------|
| 1 | [TEST-DRIFT-MDS] resolved, all 13 tests pass | `pytest` run output | ✅ Confirmed | None |
| 2 | `StubMarketDataService` is dead code | `rg` across all `*.py` — no imports | ✅ Confirmed | None |
| 3 | `StubProviderConnectionService` is dead code | `rg` across all `*.py` | ⚠️ **Partial** | Test import exists |
| 4 | Real services wired in `main.py` L208/L219 | [main.py:208-225](file:///p:/zorivest/packages/api/src/zorivest_api/main.py#L208-L225) | ✅ Confirmed | None |
| 5 | PipelineRunner has `provider_adapter` constructor param | [pipeline_runner.py:50-58](file:///p:/zorivest/packages/core/src/zorivest_core/services/pipeline_runner.py#L50-L58) | ❌ **Wrong** | Must be added |
| 6 | FetchStep reads `provider_adapter` from `context.outputs` | [fetch_step.py:117-120](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/fetch_step.py#L117-L120) | ✅ Confirmed | None |
| 7 | SendStep reads `smtp_config` + `delivery_repository` | [send_step.py:102-111](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/send_step.py#L102-L111) | ✅ Confirmed | None |
| 8 | PipelineRunner constructed without kwargs | [main.py:241](file:///p:/zorivest/packages/api/src/zorivest_api/main.py#L241) | ✅ Confirmed | None |
| 9 | 3 remaining stubs used in `main.py` | [main.py:197-199](file:///p:/zorivest/packages/api/src/zorivest_api/main.py#L197-L199) | ✅ Confirmed | None |
| 10 | MCP tool descriptions lack workflow context | [scheduling-tools.ts](file:///p:/zorivest/mcp-server/src/tools/scheduling-tools.ts) | ✅ Confirmed | None |
| 11 | No existing pending MEUs need modification | MEU-74/75/76/91-95 scope review | ✅ Confirmed | None |
| 12 | No `ProviderAdapter` class exists yet | `rg` — zero hits for class definition | ✅ Confirmed | Must create |
| 13 | `smtp_config` from `EmailProviderService.get_config()` | [email_provider_service.py:40-66](file:///p:/zorivest/packages/core/src/zorivest_core/services/email_provider_service.py#L40-L66) | ⚠️ **Incomplete** | Key mismatch |
| 14 | `delivery_repository` from `uow.deliveries` | [unit_of_work.py:75](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/unit_of_work.py#L75) | ✅ Confirmed | None |

---

## Correction Details

### Correction 1: `provider_adapter` NOT in PipelineRunner constructor

**Claimed:** PipelineRunner constructor accepts `provider_adapter`, `smtp_config`, `delivery_repository` as optional params.

**Actual** ([pipeline_runner.py:50-58](file:///p:/zorivest/packages/core/src/zorivest_core/services/pipeline_runner.py#L50-L58)):
```python
def __init__(
    self,
    uow: Any,
    ref_resolver: Any,
    condition_evaluator: Any,
    *,
    delivery_repository: Any | None = None,  # ✅ exists
    smtp_config: Any | None = None,          # ✅ exists
    # provider_adapter: ❌ DOES NOT EXIST
) -> None:
```

The initial_outputs injection block ([L94-98](file:///p:/zorivest/packages/core/src/zorivest_core/services/pipeline_runner.py#L94-L98)) only handles `delivery_repository` and `smtp_config`.

> [!IMPORTANT]
> **MEU-PW1 must ADD `provider_adapter` to the constructor AND the initial_outputs injection block.** This is a production code change to `pipeline_runner.py`, not just a wiring change in `main.py`.

---

### Correction 2: `StubProviderConnectionService` has active test import

**Claimed:** Dead code — can be deleted immediately.

**Actual** ([test_provider_service_wiring.py:21,34-36](file:///p:/zorivest/tests/unit/test_provider_service_wiring.py#L21)):
```python
from zorivest_api.stubs import StubProviderConnectionService  # L21

assert not isinstance(svc, StubProviderConnectionService), (  # L34
    "StubProviderConnectionService is still wired — "            # L35
    "replace it with ProviderConnectionService(uow, ...) in main.py lifespan"  # L36
)
```

The test uses the stub class solely for a negative isinstance assertion. The positive check at L39 (`assert isinstance(svc, ProviderConnectionService)`) is sufficient.

> [!NOTE]
> **Fix is trivial:** Delete L21 import + L34-37 negative assertion. The positive assertion at L39 catches the same defect. But this IS a test file change that must be included in MEU-PW1 scope.

---

### Correction 3: SMTP config key name mismatch

**Claimed:** Wire `smtp_config` from `EmailProviderService.get_config()`.

**Actual key mismatch:**

| SendStep reads (L108-111) | EmailProviderService returns (L40-66) | Match? |
|--------------------------|--------------------------------------|:------:|
| `smtp_config["host"]` | `"smtp_host"` | ❌ |
| `smtp_config["port"]` | `"port"` | ✅ |
| `smtp_config["sender"]` | `"from_email"` | ❌ |

**Also:** `get_config()` returns `has_password: bool` — never exposes the actual password. For SMTP auth during pipeline execution, the service needs a new method (e.g., `get_smtp_runtime_config()`) that:
1. Returns correct key names for SendStep consumption
2. Includes the decrypted password for SMTP login

> [!WARNING]
> **MEU-PW1 scope is larger than originally estimated.** Must either:
> - (a) Add a `get_smtp_runtime_config()` method to `EmailProviderService` that returns `{"host": ..., "port": ..., "sender": ..., "username": ..., "password": ...}`
> - (b) Create a mapping adapter in `main.py` that bridges the key names
>
> Option (a) is cleaner — keeps the bridge logic in the service that owns the data.

---

## Impact on MEU Definitions

### MEU-PW1 `pipeline-runtime-wiring` — Scope Refinements

The 3 corrections add these implementation tasks:

1. **Add `provider_adapter` param to `PipelineRunner.__init__`** + inject into `initial_outputs` (pipeline_runner.py)
2. **Create `MarketDataProviderAdapter`** class with `async fetch(provider, data_type, criteria) -> bytes` bridging `MarketDataService`
3. **Add `get_smtp_runtime_config()` to `EmailProviderService`** — returns SendStep-compatible dict with decrypted password
4. **Update `test_provider_service_wiring.py`** — remove negative isinstance assertion for deleted stub

**Revised effort estimate:** Medium → Medium-High (touches 4+ files across core + infra + api + tests)

### MEU-TD1 `mcp-tool-discovery-audit` — No changes needed

Analysis confirmed. Tool descriptions are functional but lack workflow context, return shapes, and prerequisite documentation.

---

## Stubs.py Docstring Accuracy

Lines 10-11 of [stubs.py](file:///p:/zorivest/packages/api/src/zorivest_api/stubs.py#L10-L11) list `StubMarketDataService` and `StubProviderConnectionService` as "Retained stubs (blocked on future MEUs)" — this is inaccurate since their real services are already wired. The docstring should be updated to note they're dead code awaiting deletion. This is a trivial fix folded into MEU-PW1.
