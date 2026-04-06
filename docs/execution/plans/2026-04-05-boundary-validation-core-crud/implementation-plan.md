# Boundary Validation — Core CRUD Hardening

> **Project slug:** `boundary-validation-core-crud`
> **Date:** 2026-04-05
> **Source:** Handoff 096 findings F1–F3 (`[BOUNDARY-GAP]` in `known-issues.md`)
> **Build-plan sections:** 04a (trades, plans), 04b (accounts)

## Goal

Harden the three highest-traffic REST write paths (Accounts, Trades, Plans) with strict Pydantic schema enforcement, constrained fields, `extra="forbid"`, and create/update invariant parity. These are the Category A code-level fixes identified in handoff 096.

## User Review Required

> [!IMPORTANT]
> **Scope boundary.** This project covers API-layer schema hardening for Accounts (F1), Trades (F2), and Plans (F3). Configuration write paths (F4–F7: Scheduling, Market Data, Email, Watchlists) and MCP Zod schema hardening are deferred to a follow-up project.

> [!WARNING]
> **Breaking change risk.** Adding `extra="forbid"` to request schemas will reject any request body containing unexpected fields. If any client (GUI, MCP tools, tests) currently sends undocumented fields, those requests will start returning 422. This is the intended behavior per the review findings.

## Proposed Changes

### MEU-BV1: `boundary-validation-accounts` (F1)

Hardens Account create/update schemas and service-layer update invariants.

| Finding | Current State | Fix |
|---------|--------------|-----|
| `account_type: str` | Raw string, `AccountType()` coercion in route handler | Use `AccountType` enum directly in Pydantic model |
| `name: str` | No min_length; command validates but schema doesn't | `Field(min_length=1)` |
| No extra-field rejection | Unknown fields silently ignored | `model_config = {"extra": "forbid"}` |
| Update bypasses invariants | `Account(**{**account.__dict__, **kwargs})` | Validate enum/constraint fields in service before reconstruction |

#### Boundary Inventory

| Boundary | Schema Owner | Extra-Field Policy | Invalid-Input Error | Create/Update Parity | Source |
|----------|-------------|--------------------|---------------------|---------------------|--------|
| POST /api/v1/accounts | `CreateAccountRequest` | `extra="forbid"` → 422 | 422 for invalid enum, blank name | Yes — service validates same invariants | Spec (04b) + Local Canon (096 F1) |
| PUT /api/v1/accounts/{id} | `UpdateAccountRequest` | `extra="forbid"` → 422 | 422 for invalid enum, blank name | Yes — same invariant check as create | Local Canon (096 F1) |

#### Files Modified

- `packages/api/src/zorivest_api/routes/accounts.py` — Schema hardening + route handler cleanup
- `packages/core/src/zorivest_core/services/account_service.py` — Update invariant validation
- `tests/unit/test_api_accounts.py` — Negative input tests

#### Acceptance Criteria

- **AC-1** `[Spec]`: `CreateAccountRequest` uses `AccountType` enum for `account_type` field — invalid values return 422
- **AC-2** `[Local Canon]`: `CreateAccountRequest.name` has `min_length=1` — blank name returns 422
- **AC-3** `[Local Canon]`: Both request schemas have `model_config = {"extra": "forbid"}` — extra fields return 422
- **AC-4** `[Local Canon]`: `UpdateAccountRequest` uses `AccountType` enum for `account_type` — invalid enum on update returns 422
- **AC-5** `[Local Canon]`: Service `update_account()` validates that the reconstructed account has a valid non-blank name — blank name on update returns 422
- **AC-6** `[Research-backed]`: No `ValueError` from `AccountType()` coercion leaks as 500 — all enum validation errors produce 422 (Pydantic handles this natively when enum is in schema)

#### Negative Test Matrix

| Test Case | Input | Expected |
|-----------|-------|----------|
| Invalid account_type on create | `account_type: "INVALID"` | 422 |
| Blank name on create | `name: ""` | 422 |
| Extra field on create | `{"name": "x", ..., "foo": "bar"}` | 422 |
| Invalid account_type on update | `account_type: "INVALID"` | 422 |
| Blank name on update | `name: ""` | 422 |
| Extra field on update | `{"foo": "bar"}` | 422 |

---

### MEU-BV2: `boundary-validation-trades` (F2)

Hardens Trade create/update schemas and service-layer update invariants.

| Finding | Current State | Fix |
|---------|--------------|-----|
| `action: str` | Raw string, `TradeAction()` coercion in route | Use `TradeAction` enum in Pydantic model |
| `quantity: float` | Unconstrained; command validates `> 0` but schema doesn't | `Field(gt=0)` |
| `price: float` | Unconstrained — negative prices accepted | `Field(ge=0)` |
| `instrument: str` | No min_length | `Field(min_length=1)` |
| `exec_id: str` | No min_length at schema level | `Field(min_length=1)` |
| No extra-field rejection | Unknown fields silently ignored | `model_config = {"extra": "forbid"}` |
| Update bypasses invariants | `**kwargs` → service reconstructs without validation | Service validates enum/constraint fields on update |

#### Boundary Inventory

| Boundary | Schema Owner | Extra-Field Policy | Invalid-Input Error | Create/Update Parity | Source |
|----------|-------------|--------------------|---------------------|---------------------|--------|
| POST /api/v1/trades | `CreateTradeRequest` | `extra="forbid"` → 422 | 422 for invalid action, non-positive qty, blank instrument | Yes | Spec (04a) + Local Canon (096 F2) |
| PUT /api/v1/trades/{id} | `UpdateTradeRequest` | `extra="forbid"` → 422 | 422 for invalid action, non-positive qty, blank instrument | Yes — same invariant check | Local Canon (096 F2) |

#### Files Modified

- `packages/api/src/zorivest_api/routes/trades.py` — Schema hardening
- `packages/core/src/zorivest_core/services/trade_service.py` — Update invariant validation
- `tests/unit/test_api_trades.py` — Negative input tests

#### Acceptance Criteria

- **AC-1** `[Spec]`: `CreateTradeRequest` uses `TradeAction` enum for `action` — invalid values return 422
- **AC-2** `[Local Canon]`: `quantity` has `Field(gt=0)` — zero/negative returns 422
- **AC-3** `[Local Canon]`: `price` has `Field(ge=0)` — negative price returns 422
- **AC-4** `[Local Canon]`: `instrument` has `Field(min_length=1)` — blank returns 422
- **AC-5** `[Local Canon]`: `exec_id` has `Field(min_length=1)` — blank returns 422
- **AC-6** `[Local Canon]`: Both schemas have `model_config = {"extra": "forbid"}` — extra fields return 422
- **AC-7** `[Local Canon]`: `UpdateTradeRequest` uses `TradeAction` for `action` — invalid enum on update returns 422
- **AC-8** `[Local Canon]`: Service `update_trade()` validates quantity > 0 and instrument non-blank on update — same invariants as create
- **AC-9** `[Research-backed]`: No `ValueError` from `TradeAction()` coercion leaks as 500

#### Negative Test Matrix

| Test Case | Input | Expected |
|-----------|-------|----------|
| Invalid action on create | `action: "INVALID"` | 422 |
| Zero quantity on create | `quantity: 0` | 422 |
| Negative quantity on create | `quantity: -1` | 422 |
| Negative price on create | `price: -5.0` | 422 |
| Blank instrument on create | `instrument: ""` | 422 |
| Blank exec_id on create | `exec_id: ""` | 422 |
| Extra field on create | `{"exec_id": "x", ..., "foo": "bar"}` | 422 |
| Invalid action on update | `action: "INVALID"` | 422 |
| Zero quantity on update | `quantity: 0` | 422 |
| Blank instrument on update | `instrument: ""` | 422 |
| Extra field on update | `{"foo": "bar"}` | 422 |

---

### MEU-BV3: `boundary-validation-plans` (F3)

Hardens Plan create/update/status-patch schemas and service-layer update invariants.

| Finding | Current State | Fix |
|---------|--------------|-----|
| `direction: str` | Raw string, no enum enforcement | Use `TradeAction` enum |
| `conviction: str` | Raw string, no enum enforcement | Use `ConvictionLevel` enum |
| `status: str` in PatchStatusRequest | Raw string | Use `PlanStatus` enum |
| `ticker: str` | No min_length | `Field(min_length=1)` |
| `strategy_name: str` | No min_length | `Field(min_length=1)` |
| No extra-field rejection | Unknown fields silently ignored | `model_config = {"extra": "forbid"}` |
| Update bypasses invariants | `replace(existing, **updates)` without validation | Service validates enum/constraint fields on update |

#### Boundary Inventory

| Boundary | Schema Owner | Extra-Field Policy | Invalid-Input Error | Create/Update Parity | Source |
|----------|-------------|--------------------|---------------------|---------------------|--------|
| POST /api/v1/trade-plans | `CreatePlanRequest` | `extra="forbid"` → 422 | 422 for invalid direction/conviction, blank ticker | Yes | Spec (04a) + Local Canon (096 F3) |
| PUT /api/v1/trade-plans/{id} | `UpdatePlanRequest` | `extra="forbid"` → 422 | 422 for invalid enums, blank required strings | Yes — same invariants | Local Canon (096 F3) |
| PATCH /api/v1/trade-plans/{id}/status | `PatchStatusRequest` | `extra="forbid"` → 422 | 422 for invalid status | Yes — enum validation consistent | Local Canon (096 F3) |

#### Files Modified

- `packages/api/src/zorivest_api/routes/plans.py` — Schema hardening
- `packages/core/src/zorivest_core/services/report_service.py` — Update invariant validation
- `tests/unit/test_api_plans.py` — Negative input tests

#### Acceptance Criteria

- **AC-1** `[Spec]`: `CreatePlanRequest` uses `TradeAction` for `direction` — invalid values return 422
- **AC-2** `[Spec]`: `CreatePlanRequest` uses `ConvictionLevel` for `conviction` — invalid values return 422
- **AC-3** `[Local Canon]`: `PatchStatusRequest` uses `PlanStatus` for `status` — invalid values return 422
- **AC-4** `[Local Canon]`: `ticker` has `Field(min_length=1)` — blank returns 422
- **AC-5** `[Local Canon]`: `strategy_name` has `Field(min_length=1)` — blank returns 422
- **AC-6** `[Local Canon]`: All three request schemas have `model_config = {"extra": "forbid"}` — extra fields return 422
- **AC-7** `[Local Canon]`: `UpdatePlanRequest` uses the same enum types for `direction`, `conviction`, `status` — invalid enums on update return 422
- **AC-8** `[Local Canon]`: Service `update_plan()` validates ticker non-blank and strategy_name non-blank on update — same invariants as create
- **AC-9** `[Research-backed]`: No raw `str` → enum coercion at service layer — Pydantic handles enum validation at schema level

#### Negative Test Matrix

| Test Case | Input | Expected |
|-----------|-------|----------|
| Invalid direction on create | `direction: "INVALID"` | 422 |
| Invalid conviction on create | `conviction: "INVALID"` | 422 |
| Blank ticker on create | `ticker: ""` | 422 |
| Blank strategy_name on create | `strategy_name: ""` | 422 |
| Extra field on create | `{..., "foo": "bar"}` | 422 |
| Invalid status on patch | `status: "INVALID"` | 422 |
| Extra field on patch | `{"status": "active", "foo": "bar"}` | 422 |
| Invalid direction on update | `direction: "INVALID"` | 422 |
| Invalid conviction on update | `conviction: "INVALID"` | 422 |
| Blank ticker on update | `ticker: ""` | 422 |
| Extra field on update | `{"foo": "bar"}` | 422 |

---

## Spec Sufficiency Table

| Behavior / Contract | Source Type | Source | Resolved? |
|---|---|---|---|
| Enum fields must reject invalid values at API boundary | Research-backed | Pydantic docs: enum types validated natively | ✅ |
| Required string fields must reject blank/empty | Local Canon | 096 review F1–F3, AGENTS.md §Boundary Input Contract | ✅ |
| Extra fields must be rejected on closed contracts | Local Canon | 096 review, code-quality.md §Boundary Validation Standards | ✅ |
| Update paths must enforce same invariants as create | Local Canon | 096 review F1–F3, AGENTS.md §Boundary Input Contract | ✅ |
| Numeric fields must reject non-positive values where applicable | Spec | 01-domain.md (quantity > 0), 096 F2 | ✅ |
| Invalid input produces 422, not 500 | Research-backed | FastAPI docs: Pydantic validation → 422; Python docs: assert not for production validation | ✅ |

## Out of Scope

- **F4–F7** (Scheduling, Market Data, Email, Watchlists) — deferred to follow-up project
- **MCP Zod schema hardening** — API hardening protects the MCP path transitively; Zod defense-in-depth is a follow-up
- **UI form validation** — client-side validation is defense-in-depth; server boundary is the primary fix
- **New enum creation** for `timeframe` — field is genuinely freeform per the build plan

## `docs/BUILD_PLAN.md` Audit

This project hardens existing write paths within Phase 4 (items 12, 13 in the priority matrix). No hub-level structural changes are required. A verification task is included to confirm no stale references exist.

## Verification Plan

### Automated Tests

Per MEU:
```bash
# Red phase — tests fail
uv run pytest tests/unit/test_api_{module}.py -x --tb=short -v *> C:\Temp\zorivest\pytest.txt

# Green phase — tests pass
uv run pytest tests/unit/test_api_{module}.py -x --tb=short -v *> C:\Temp\zorivest\pytest.txt

# Quality checks
uv run pyright packages/core/src/ packages/api/src/ *> C:\Temp\zorivest\pyright.txt
uv run ruff check packages/core/src/ packages/api/src/ *> C:\Temp\zorivest\ruff.txt

# Full regression
uv run pytest -x --tb=short -m "unit" *> C:\Temp\zorivest\pytest-full.txt
```

### Post-execution
```bash
# MEU gate
uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate.txt

# OpenAPI spec regen (API routes modified)
uv run python tools/export_openapi.py -o openapi.committed.json *> C:\Temp\zorivest\openapi.txt
```

## Research References

- Pydantic enum validation: https://docs.pydantic.dev/latest/concepts/types/#enums
- Pydantic extra fields: https://docs.pydantic.dev/latest/concepts/models/#extra-fields
- FastAPI request validation: https://fastapi.tiangolo.com/tutorial/body/
- Python assert not for production: https://docs.python.org/3/reference/simple_stmts.html#the-assert-statement
