# 100 — MEU-BV3 Boundary Validation: Plans

> **Date**: 2026-04-05
> **MEU**: MEU-BV3 (`boundary-validation-plans`)
> **Build Plan Section**: 04a (trade plans)
> **Project**: `2026-04-05-boundary-validation-core-crud`
> **Plan**: [implementation-plan.md](../../docs/execution/plans/2026-04-05-boundary-validation-core-crud/implementation-plan.md)
> **Status**: ✅ Complete

---

## Scope

Harden Plan create/update/status-patch schemas with strict Pydantic enforcement (`TradeAction`/`ConvictionLevel`/`PlanStatus` enums, `Field(min_length=1)` for ticker/strategy_name), `extra="forbid"`, and service-layer update invariant parity. Addresses finding F3 from handoff 096.

## Feature Intent Contract

### Acceptance Criteria

- **AC-1** `[Spec]`: `CreatePlanRequest` uses `TradeAction` for `direction` — invalid values return 422 ✅
- **AC-2** `[Spec]`: `CreatePlanRequest` uses `ConvictionLevel` for `conviction` — invalid values return 422 ✅
- **AC-3** `[Local Canon]`: `PatchStatusRequest` uses `PlanStatus` for `status` — invalid values return 422 ✅
- **AC-4** `[Local Canon]`: `ticker` has `Field(min_length=1)` — blank returns 422 ✅
- **AC-5** `[Local Canon]`: `strategy_name` has `Field(min_length=1)` — blank returns 422 ✅
- **AC-6** `[Local Canon]`: All three request schemas have `model_config = {"extra": "forbid"}` — extra fields return 422 ✅
- **AC-7** `[Local Canon]`: `UpdatePlanRequest` uses the same enum types for `direction`, `conviction`, `status` — invalid enums on update return 422 ✅
- **AC-8** `[Local Canon]`: Service `update_plan()` validates ticker non-blank and strategy_name non-blank on update ✅
- **AC-9** `[Research-backed]`: No raw `str` → enum coercion at service layer — Pydantic handles enum validation at schema level ✅

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Direction normalization | `BeforeValidator(_normalize_direction)` + `CIDirection` | MCP tools send "long"/"short" aliases; map to BOT/SLD before enum validation |
| Three schemas hardened | `CreatePlanRequest`, `UpdatePlanRequest`, `PatchStatusRequest` | Plans have 3 write paths (POST, PUT, PATCH /status) |
| MCP alias fields | `entry`, `stop`, `target`, `conditions` mapped via `model_validator` | Backward compatibility with MCP tools; aliases consumed before `extra="forbid"` fires |
| timeframe not constrained | `str` (no enum) | Field is genuinely freeform per the build plan |

## Changed Files

### API Layer
- `packages/api/src/zorivest_api/routes/plans.py` — `CreatePlanRequest`, `UpdatePlanRequest`, `PatchStatusRequest`: added `model_config = {"extra": "forbid"}`, enum types for direction/conviction/status, `Field(min_length=1)` for ticker/strategy_name

### Service Layer
- `packages/core/src/zorivest_core/services/report_service.py` — `update_plan()`: added ticker non-blank and strategy_name non-blank invariant checks before `replace()`

### Tests
- `tests/unit/test_api_plans.py` — 12 new negative test methods in 3 classes:
  - `TestCreatePlanBoundaryValidation` (5 tests)
  - `TestUpdatePlanBoundaryValidation` (5 tests)
  - `TestPatchPlanStatusBoundaryValidation` (1 test)

## Commands Executed

```bash
# Red phase
uv run pytest tests/unit/test_api_plans.py -x --tb=short -v  # 12 FAIL (boundary tests)

# Green phase
uv run pytest tests/unit/test_api_plans.py -x --tb=short -v  # ALL PASS

# Quality gate
uv run ruff check packages/core/src/ packages/api/src/  # PASS
```

## FAIL_TO_PASS Evidence

| Test | Before | After |
|------|--------|-------|
| `test_invalid_direction_returns_422` | FAIL | PASS (422) |
| `test_invalid_conviction_returns_422` | FAIL | PASS (422) |
| `test_blank_ticker_returns_422` | FAIL | PASS (422) |
| `test_blank_strategy_name_returns_422` | FAIL | PASS (422) |
| `test_extra_field_on_create_returns_422` | FAIL | PASS (422) |
| `test_invalid_direction_on_update_returns_422` | FAIL | PASS (422) |
| `test_invalid_conviction_on_update_returns_422` | FAIL | PASS (422) |
| `test_invalid_status_on_update_returns_422` | FAIL | PASS (422) |
| `test_blank_ticker_on_update_returns_422` | FAIL | PASS (422) |
| `test_extra_field_on_update_returns_422` | FAIL | PASS (422) |
| `test_invalid_status_on_patch_returns_422` | FAIL | PASS (422) |

## Test Mapping

| AC | Test Function |
|----|---------------|
| AC-1 | `test_invalid_direction_returns_422` |
| AC-2 | `test_invalid_conviction_returns_422` |
| AC-3 | `test_invalid_status_on_patch_returns_422` |
| AC-4 | `test_blank_ticker_returns_422`, `test_blank_ticker_on_update_returns_422` |
| AC-5 | `test_blank_strategy_name_returns_422` |
| AC-6 | `test_extra_field_on_create_returns_422`, `test_extra_field_on_update_returns_422` |
| AC-7 | `test_invalid_direction_on_update_returns_422`, `test_invalid_conviction_on_update_returns_422`, `test_invalid_status_on_update_returns_422` |
| AC-8 | `test_blank_ticker_on_update_returns_422` |
| AC-9 | `test_invalid_direction_returns_422` (Pydantic 422, not ValueError 500) |
