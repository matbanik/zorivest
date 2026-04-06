# 098 — MEU-BV1 Boundary Validation: Accounts

> **Date**: 2026-04-05
> **MEU**: MEU-BV1 (`boundary-validation-accounts`)
> **Build Plan Section**: 04b (accounts)
> **Project**: `2026-04-05-boundary-validation-core-crud`
> **Plan**: [implementation-plan.md](../../docs/execution/plans/2026-04-05-boundary-validation-core-crud/implementation-plan.md)
> **Status**: ✅ Complete

---

## Scope

Harden Account create/update schemas with strict Pydantic enforcement, constrained fields, `extra="forbid"`, and create/update invariant parity. Addresses finding F1 from handoff 096.

## Feature Intent Contract

### Acceptance Criteria

- **AC-1** `[Spec]`: `CreateAccountRequest` uses `AccountType` enum for `account_type` — invalid values return 422 ✅
- **AC-2** `[Local Canon]`: `CreateAccountRequest.name` has `min_length=1` — blank name returns 422 ✅
- **AC-3** `[Local Canon]`: Both request schemas have `model_config = {"extra": "forbid"}` — extra fields return 422 ✅
- **AC-4** `[Local Canon]`: `UpdateAccountRequest` uses `AccountType` enum for `account_type` — invalid enum on update returns 422 ✅
- **AC-5** `[Local Canon]`: Service `update_account()` validates that name is non-blank — blank name on update returns 422 ✅
- **AC-6** `[Research-backed]`: No `ValueError` from `AccountType()` coercion leaks as 500 — all enum validation errors produce 422 via Pydantic ✅

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Case-insensitive AccountType | `BeforeValidator(_normalize_account_type)` + `CIAccountType` annotated type | MCP tools send lowercase; Pydantic enum validation requires exact match unless normalized pre-validation |
| Update invariant location | Service layer (`account_service.update_account`) | Route handler delegates to service; invariant parity matches create path in `CreateAccount` command |
| Extra-field policy | `extra="forbid"` on both Create and Update schemas | Closed contract — unknown fields produce 422 rather than being silently ignored |

## Changed Files

### API Layer
- `packages/api/src/zorivest_api/routes/accounts.py` — `CreateAccountRequest` and `UpdateAccountRequest`: added `model_config = {"extra": "forbid"}`, `CIAccountType` enum field, `Field(min_length=1)` on name

### Service Layer
- `packages/core/src/zorivest_core/services/account_service.py` — `update_account()`: added name blank-check invariant validation before reconstruction

### Tests
- `tests/unit/test_api_accounts.py` — 6 new negative test methods in 2 classes:
  - `TestCreateAccountBoundaryValidation` (3 tests)
  - `TestUpdateAccountBoundaryValidation` (3 tests)

## Commands Executed

```bash
# Red phase — tests written before implementation
uv run pytest tests/unit/test_api_accounts.py -x --tb=short -v  # 6 FAIL

# Green phase — after schema hardening + service invariants
uv run pytest tests/unit/test_api_accounts.py -x --tb=short -v  # ALL PASS

# Quality gate
uv run ruff check packages/core/src/ packages/api/src/  # PASS
```

## FAIL_TO_PASS Evidence

| Test | Before | After |
|------|--------|-------|
| `test_invalid_account_type_returns_422` | FAIL (accepted raw string) | PASS (422) |
| `test_blank_name_returns_422` | FAIL (accepted empty name) | PASS (422) |
| `test_extra_field_on_create_returns_422` | FAIL (ignored extra fields) | PASS (422) |
| `test_invalid_account_type_on_update_returns_422` | FAIL (accepted invalid enum) | PASS (422) |
| `test_blank_name_on_update_returns_422` | FAIL (accepted blank name) | PASS (422) |
| `test_extra_field_on_update_returns_422` | FAIL (ignored extra fields) | PASS (422) |

## Test Mapping

| AC | Test Function |
|----|---------------|
| AC-1 | `test_invalid_account_type_returns_422` |
| AC-2 | `test_blank_name_returns_422` |
| AC-3 | `test_extra_field_on_create_returns_422`, `test_extra_field_on_update_returns_422` |
| AC-4 | `test_invalid_account_type_on_update_returns_422` |
| AC-5 | `test_blank_name_on_update_returns_422` |
| AC-6 | `test_invalid_account_type_returns_422` (Pydantic 422, not ValueError 500) |
