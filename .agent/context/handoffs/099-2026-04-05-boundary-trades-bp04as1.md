# 099 — MEU-BV2 Boundary Validation: Trades

> **Date**: 2026-04-05
> **MEU**: MEU-BV2 (`boundary-validation-trades`)
> **Build Plan Section**: 04a (trades)
> **Project**: `2026-04-05-boundary-validation-core-crud`
> **Plan**: [implementation-plan.md](../../docs/execution/plans/2026-04-05-boundary-validation-core-crud/implementation-plan.md)
> **Status**: ✅ Complete

---

## Scope

Harden Trade create/update schemas with strict Pydantic enforcement (`TradeAction` enum, `Field(gt=0)` for quantity, `Field(ge=0)` for price, `Field(min_length=1)` for instrument/exec_id), `extra="forbid"`, and service-layer update invariant parity. Addresses finding F2 from handoff 096.

## Feature Intent Contract

### Acceptance Criteria

- **AC-1** `[Spec]`: `CreateTradeRequest` uses `TradeAction` enum for `action` — invalid values return 422 ✅
- **AC-2** `[Local Canon]`: `quantity` has `Field(gt=0)` — zero/negative returns 422 ✅
- **AC-3** `[Local Canon]`: `price` has `Field(ge=0)` — negative price returns 422 ✅
- **AC-4** `[Local Canon]`: `instrument` has `Field(min_length=1)` — blank returns 422 ✅
- **AC-5** `[Local Canon]`: `exec_id` has `Field(min_length=1)` — blank returns 422 ✅
- **AC-6** `[Local Canon]`: Both schemas have `model_config = {"extra": "forbid"}` — extra fields return 422 ✅
- **AC-7** `[Local Canon]`: `UpdateTradeRequest` uses `TradeAction` for `action` — invalid enum on update returns 422 ✅
- **AC-8** `[Local Canon]`: Service `update_trade()` validates quantity > 0 and instrument non-blank on update ✅
- **AC-9** `[Research-backed]`: No `ValueError` from `TradeAction()` coercion leaks as 500 ✅

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| TradeAction enum in schema | Direct `TradeAction` type on `action` field | Pydantic validates enum membership at deserialization; no manual coercion needed |
| Quantity constraint | `Field(gt=0)` | Trades with zero/negative quantity are meaningless; matches domain command validation |
| Price constraint | `Field(ge=0)` | Zero price is valid (e.g., stock splits); negative is always invalid |
| Update invariant location | `trade_service.update_trade()` service layer | Validates quantity > 0, instrument non-blank before reconstruction |

## Changed Files

### API Layer
- `packages/api/src/zorivest_api/routes/trades.py` — `CreateTradeRequest` and `UpdateTradeRequest`: added `model_config = {"extra": "forbid"}`, `TradeAction` enum, `Field(gt=0)`, `Field(ge=0)`, `Field(min_length=1)` constraints

### Service Layer
- `packages/core/src/zorivest_core/services/trade_service.py` — `update_trade()`: added quantity > 0 and instrument non-blank invariant checks before reconstruction

### Tests
- `tests/unit/test_api_trades.py` — 11 new negative test methods in 2 classes:
  - `TestCreateTradeBoundaryValidation` (7 tests)
  - `TestUpdateTradeBoundaryValidation` (4 tests)

## Commands Executed

```bash
# Red phase
uv run pytest tests/unit/test_api_trades.py -x --tb=short -v  # 11 FAIL

# Green phase
uv run pytest tests/unit/test_api_trades.py -x --tb=short -v  # ALL PASS

# Quality gate
uv run ruff check packages/core/src/ packages/api/src/  # PASS
```

## FAIL_TO_PASS Evidence

| Test | Before | After |
|------|--------|-------|
| `test_invalid_action_returns_422` | FAIL | PASS (422) |
| `test_zero_quantity_returns_422` | FAIL | PASS (422) |
| `test_negative_quantity_returns_422` | FAIL | PASS (422) |
| `test_negative_price_returns_422` | FAIL | PASS (422) |
| `test_blank_instrument_returns_422` | FAIL | PASS (422) |
| `test_blank_exec_id_returns_422` | FAIL | PASS (422) |
| `test_extra_field_on_create_returns_422` | FAIL | PASS (422) |
| `test_invalid_action_on_update_returns_422` | FAIL | PASS (422) |
| `test_zero_quantity_on_update_returns_422` | FAIL | PASS (422) |
| `test_blank_instrument_on_update_returns_422` | FAIL | PASS (422) |
| `test_extra_field_on_update_returns_422` | FAIL | PASS (422) |

## Test Mapping

| AC | Test Function |
|----|---------------|
| AC-1 | `test_invalid_action_returns_422` |
| AC-2 | `test_zero_quantity_returns_422`, `test_negative_quantity_returns_422` |
| AC-3 | `test_negative_price_returns_422` |
| AC-4 | `test_blank_instrument_returns_422` |
| AC-5 | `test_blank_exec_id_returns_422` |
| AC-6 | `test_extra_field_on_create_returns_422`, `test_extra_field_on_update_returns_422` |
| AC-7 | `test_invalid_action_on_update_returns_422` |
| AC-8 | `test_zero_quantity_on_update_returns_422`, `test_blank_instrument_on_update_returns_422` |
| AC-9 | `test_invalid_action_returns_422` (Pydantic 422, not ValueError 500) |
