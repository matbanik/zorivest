---
seq: "107"
date: "2026-04-11"
project: "2026-04-11-boundary-validation-phase2"
meu: "MEU-BV6, MEU-BV7, MEU-BV8"
status: "complete"
action_required: "VALIDATE_AND_APPROVE"
template_version: "2.1"
verbosity: "standard"
plan_source: "docs/execution/plans/2026-04-11-boundary-validation-phase2/implementation-plan.md"
build_plan_section: "bp09s9.10, bp04-inline+06c, bp04ds1"
agent: "Antigravity (Gemini)"
reviewer: "GPT-5.4 Codex"
predecessor: "106-2026-04-11-quality-pipeline-hardening-ci.md"
---

# Handoff 107 — Boundary Validation Phase 2 (BV6 + BV7 + BV8)

> **Status**: `complete`
> **Action Required**: `VALIDATE_AND_APPROVE`

---

## Scope

**MEU**: MEU-BV6 (scheduling), MEU-BV7 (watchlists), MEU-BV8 (settings)
**Build Plan Section**: 09 §9.10 (scheduling), 04 inline + 06c (watchlists), 04d §1 (settings)
**Predecessor**: [106-quality-pipeline-hardening](106-2026-04-11-quality-pipeline-hardening-ci.md)

Hardened all remaining API write surfaces with `[BOUNDARY-GAP]` findings (F4, F7, Settings). All 7/7 original BOUNDARY-GAP findings are now closed.

---

## Acceptance Criteria

### MEU-BV6 (Scheduling)

| AC | Description | Source | Test(s) | Status |
|----|-------------|--------|---------|--------|
| AC-1 | `PolicyCreateRequest` has `extra="forbid"` — extra fields → 422 | Local Canon (BV1) | `test_api_scheduling.py::TestSchedulingBoundaryValidation::test_create_policy_extra_field_422` | ✅ |
| AC-2 | `RunTriggerRequest` has `extra="forbid"` — extra fields → 422 | Local Canon (BV1) | `test_api_scheduling.py::TestSchedulingBoundaryValidation::test_trigger_run_extra_field_422` | ✅ |
| AC-3 | `PolicyCreateRequest.policy_json` rejects empty dict → 422 | Spec (09 §9.10) | `test_api_scheduling.py::TestSchedulingBoundaryValidation::test_create_policy_empty_policy_json_422` | ✅ |
| AC-4 | PATCH `cron_expression` whitespace-only → 422 | Local Canon (BV1) | `test_api_scheduling.py::TestSchedulingBoundaryValidation::test_patch_blank_cron_expression_422` | ✅ |
| AC-5 | PATCH `timezone` whitespace-only → 422 | Local Canon (BV1) | `test_api_scheduling.py::TestSchedulingBoundaryValidation::test_patch_blank_timezone_422` | ✅ |
| AC-6 | PATCH blank `cron_expression` → 422 | Local Canon (BV1) | `test_api_scheduling.py::TestSchedulingBoundaryValidation::test_patch_blank_cron_expression_422` | ✅ |

### MEU-BV7 (Watchlists)

| AC | Description | Source | Test(s) | Status |
|----|-------------|--------|---------|--------|
| AC-1 | `CreateWatchlistRequest` has `extra="forbid"` — extra fields → 422 | Local Canon (BV1) | `test_api_watchlists.py::TestWatchlistBoundaryValidation::test_create_extra_field_422` | ✅ |
| AC-2 | `CreateWatchlistRequest.name` blank → 422 | Local Canon (BV1) | `test_api_watchlists.py::TestWatchlistBoundaryValidation::test_create_blank_name_422` | ✅ |
| AC-3 | `UpdateWatchlistRequest` has `extra="forbid"` — extra fields → 422 | Local Canon (BV1) | `test_api_watchlists.py::TestWatchlistBoundaryValidation::test_update_extra_field_422` | ✅ |
| AC-4 | `UpdateWatchlistRequest.name` blank on update → 422 (parity) | Local Canon (BV1) | `test_api_watchlists.py::TestWatchlistBoundaryValidation::test_update_blank_name_422` | ✅ |
| AC-5 | `AddTickerRequest` has `extra="forbid"` — extra fields → 422 | Local Canon (BV1) | `test_api_watchlists.py::TestWatchlistBoundaryValidation::test_add_ticker_extra_field_422` | ✅ |
| AC-6 | `AddTickerRequest.ticker` blank → 422 | Local Canon (BV1) | `test_api_watchlists.py::TestWatchlistBoundaryValidation::test_add_blank_ticker_422` | ✅ |
| AC-7 | Whitespace-only name on create → 422 | Local Canon (BV1) | `test_api_watchlists.py::TestWatchlistBoundaryValidation::test_create_whitespace_name_422` | ✅ |
| AC-8 | Whitespace-only name on update → 422 (parity) | Local Canon (BV1) | `test_api_watchlists.py::TestWatchlistBoundaryValidation::test_update_whitespace_name_422` | ✅ |
| AC-9 | Whitespace-only ticker on add → 422 | Local Canon (BV1) | `test_api_watchlists.py::TestWatchlistBoundaryValidation::test_add_whitespace_ticker_422` | ✅ |

### MEU-BV8 (Settings)

| AC | Description | Source | Test(s) | Status |
|----|-------------|--------|---------|--------|
| AC-1 | Bulk PUT with empty body → 422 | Spec (04d §1) | `test_api_settings.py::TestSettingsBoundaryValidation::test_bulk_put_empty_dict_422` | ✅ |
| AC-2 | `UpdateSettingRequest` has `extra="forbid"` — extra fields → 422 | Local Canon (BV1) | `test_api_settings.py::TestSettingsBoundaryValidation::test_single_put_extra_field_422` | ✅ |
| AC-3 | Single-key PUT requires `value` field | Spec (04d §1) | `test_api_settings.py::TestSettingsBoundaryValidation::test_single_put_no_value_422` | ✅ |

<!-- CACHE BOUNDARY -->
<!-- Content above this line is stable across revision passes (KV cache prefix). -->
<!-- Content below this line changes between passes (evidence, results, corrections). -->

---

## Evidence

### FAIL_TO_PASS

| Test | Red Output (snippet) | Green Output | File:Line |
|------|---------------------|--------------|-----------|
| `test_create_policy_extra_field_422` | `assert 201 == 422` | `PASSED` | `test_api_scheduling.py:566` |
| `test_create_extra_field_422` | `assert 201 == 422` | `PASSED` | `test_api_watchlists.py:205` |
| `test_bulk_put_empty_dict_422` | `assert 200 == 422` | `PASSED` | `test_api_settings.py:260` |
| `test_update_blank_name_422` | `assert 200 == 422` | `PASSED` | `test_api_watchlists.py:251` |
| `test_update_whitespace_name_422` | `assert 200 == 422` | `PASSED` | `test_api_watchlists.py:257` |

### Commands Executed

| Command | Exit Code | Key Output |
|---------|-----------|------------|
| `uv run pytest tests/unit/test_api_scheduling.py -k "Boundary" -x --tb=short -v` | 0 | `6 passed, 56 deselected` |
| `uv run pytest tests/unit/test_api_watchlists.py -k "Boundary" -x --tb=short -v` | 0 | `9 passed, 15 deselected` |
| `uv run pytest tests/unit/test_api_settings.py -k "Boundary" -x --tb=short -v` | 0 | `3 passed, 15 deselected` |
| `uv run pytest tests/unit/test_api_scheduling.py tests/unit/test_api_watchlists.py tests/unit/test_api_settings.py -x --tb=short -v` | 0 | `76 passed in 11.90s` |
| `uv run python tools/validate_codebase.py --scope meu` | 0 | `8/8 blocking checks passed` |
| `uv run python tools/export_openapi.py -o openapi.committed.json` | 0 | OpenAPI spec regenerated |
| `uv run ruff check packages/api/` | 0 | No violations |

### Quality Gate Results

```
pyright: 0 errors (scoped to packages/)
ruff: 0 violations
pytest: 76 passed, 0 failed (scheduling + watchlists + settings)
anti-placeholder: 0 matches
anti-deferral: 0 matches
```

---

## Changed Files

| File | Action | Lines | Summary |
|------|--------|-------|---------|
| `packages/api/src/zorivest_api/routes/scheduling.py` | modified | ~30 | `extra="forbid"` on 2 models, `field_validator` on `policy_json`, strip-reject on PATCH params |
| `packages/api/src/zorivest_api/routes/watchlists.py` | modified | ~25 | `StrippedStr` type alias, `extra="forbid"` on 3 models, `Field(min_length=1)` on name/ticker |
| `packages/api/src/zorivest_api/routes/settings.py` | modified | ~20 | `UpdateSettingRequest` model, empty-body guard on bulk PUT |
| `tests/unit/test_api_scheduling.py` | modified | +63 | 6 BV6 negative test methods |
| `tests/unit/test_api_watchlists.py` | modified | +73 | 9 BV7 negative test methods (7 original + 2 update-parity) |
| `tests/unit/test_api_settings.py` | modified | +36 | 3 BV8 negative test methods |
| `.agent/context/known-issues.md` | modified | ~15 | BOUNDARY-GAP marked ✅ fully resolved (7/7) |
| `.agent/context/meu-registry.md` | modified | +3 | BV6, BV7, BV8 rows added |
| `openapi.committed.json` | regenerated | — | Reflects new request schemas |

```diff
# packages/api/src/zorivest_api/routes/scheduling.py
+from pydantic import field_validator
+from pydantic.functional_validators import BeforeValidator
+from typing import Annotated
+
+class PolicyCreateRequest(BaseModel):
+    model_config = {"extra": "forbid"}
+    @field_validator("policy_json")
+    @classmethod
+    def policy_json_not_empty(cls, v): ...
+
+class RunTriggerRequest(BaseModel):
+    model_config = {"extra": "forbid"}
```

```diff
# packages/api/src/zorivest_api/routes/watchlists.py
+StrippedStr = Annotated[str, BeforeValidator(_strip_whitespace)]
+
+class CreateWatchlistRequest(BaseModel):
+    model_config = {"extra": "forbid"}
+    name: StrippedStr = Field(min_length=1)
+
+class UpdateWatchlistRequest(BaseModel):
+    model_config = {"extra": "forbid"}
+    name: Optional[StrippedStr] = Field(default=None, min_length=1)
```

```diff
# packages/api/src/zorivest_api/routes/settings.py
+class UpdateSettingRequest(BaseModel):
+    model_config = {"extra": "forbid"}
+    value: Any
+
 @settings_router.put("/api/v1/settings")
 async def update_settings(...):
+    if not body:
+        raise HTTPException(status_code=422, detail="Empty body")
```

---

## Design Decisions

1. **Query param whitespace handling:** FastAPI `Query(min_length=1)` does not strip whitespace before length check. Used explicit strip-then-reject pattern in the route handler (not BeforeValidator, which doesn't compose with FastAPI Query params).
2. **Settings bulk PUT contract preserved:** The bulk PUT still accepts `dict[str, Any]` (flat map). Only hardening added is empty-body guard.
3. **Single-key PUT typed:** Replaced `dict[str, Any]` with `UpdateSettingRequest(value: Any)` with `extra="forbid"`. Non-breaking — existing callers already send `{"value": ...}`.

---

## Codex Validation Report

_Left blank for reviewer agent. Reviewer fills this section during `/validation-review`._

### Recheck Protocol

1. Read Scope + AC table
2. Verify each AC against Evidence section (file:line, not memory)
3. Run all Commands Executed and compare output
4. Run Quality Gate commands independently
5. Record findings below

### Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|

### Verdict

`pending` — awaiting reviewer

---

## Deferred Items

None. All boundary gaps closed.

---

## History

| Event | Date | Agent | Detail |
|-------|------|-------|---------|
| Created | 2026-04-11 | Antigravity | Initial handoff (7 AC BV7 + 6 AC BV6 + 3 AC BV8) |
| Corrections (F1/F2/F3) | 2026-04-11 | Antigravity | Rebuilt to template v2.1; added 2 update-parity tests; synced plan status |
| Corrections (F4/F5) | 2026-04-11 | Antigravity | Fixed 6 stale test names in AC/FAIL_TO_PASS tables; corrected watchlist source label from 04b §1 to 04 inline + 06c |
