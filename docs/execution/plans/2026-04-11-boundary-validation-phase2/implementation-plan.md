---
project: "2026-04-11-boundary-validation-phase2"
date: "2026-04-11"
source: "docs/build-plan/09-scheduling.md, docs/build-plan/04-rest-api.md, docs/build-plan/06c-gui-planning.md, docs/build-plan/04d-api-settings.md"
meus: ["MEU-BV6", "MEU-BV7", "MEU-BV8"]
status: "complete"
template_version: "2.0"
---

# Implementation Plan: Boundary Validation Phase 2

> **Project**: `2026-04-11-boundary-validation-phase2`
> **Build Plan Section(s)**: 09 (scheduling), 04 inline + 06c (watchlists), 04d (settings)
> **Status**: `complete`

---

## Goal

Harden the three remaining write boundaries identified in [BOUNDARY-GAP] (known-issues.md): scheduling routes (F4), watchlist routes (F7), and settings routes (Settings). Each gap allows unknown fields, blank strings, or raw dicts to pass through the API boundary without Pydantic schema enforcement. This project applies the same hardening pattern established in BV1–BV5 (handoffs 098–102): `extra="forbid"`, `StrippedStr`, `Field(min_length=1)`, and negative test coverage.

Completing these three MEUs unblocks:
- MEU-72 (`gui-scheduling`)
- MEU-70a (`watchlist-visual-redesign`)
- MEU-76 (`gui-reset-defaults`)

---

## User Review Required

> [!NOTE]
> **Non-breaking hardening**: This plan preserves all existing API contracts. The scheduling PATCH endpoint retains query parameters (with added `Query` validators). The settings bulk PUT retains the flat `dict[str, Any]` body shape (with added empty-body rejection). Only `extra="forbid"` on existing Pydantic body models and `Query(min_length=1)` on string query params are new enforcement.

---

## Proposed Changes

### MEU-BV6: Scheduling Boundary Hardening

#### Boundary Inventory

| Surface | Schema Owner | Field Constraints | Extra-Field Policy |
|---------|-------------|-------------------|-------------------|
| `POST /policies` body | `PolicyCreateRequest` | `policy_json: dict[str, Any]` (non-empty) | `extra="forbid"` |
| `PUT /policies/{id}` body | `PolicyCreateRequest` | Same as above | `extra="forbid"` |
| `POST /policies/{id}/run` body | `RunTriggerRequest` | `dry_run: bool` | `extra="forbid"` |
| `PATCH /policies/{id}/schedule` query | (discrete params) | `cron_expression: Query(min_length=1)`, `enabled: bool`, `timezone: Query(min_length=1)` | N/A (query params) |

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-1 | `PolicyCreateRequest` has `model_config = {"extra": "forbid"}` — extra fields on POST/PUT → 422 | Local Canon (BV1 pattern) | `{"policy_json": {...}, "sneaky": true}` → 422 |
| AC-2 | `RunTriggerRequest` has `model_config = {"extra": "forbid"}` — extra fields on /run → 422 | Local Canon (BV1 pattern) | `{"dry_run": false, "extra": 1}` → 422 |
| AC-3 | PATCH schedule preserves query params; blank/whitespace-only `cron_expression` → 422 | Spec (09-scheduling.md §9.10 defines discrete params) + Local Canon (BV1 min_length) | `params={"cron_expression": "  "}` → 422 |
| AC-4 | Blank/whitespace-only `timezone` in PATCH → 422 | Local Canon (BV1 min_length=1) | `params={"timezone": "  "}` → 422 |
| AC-5 | `policy_json` must be non-empty dict — empty `{}` produces 422 | Local Canon (non-empty dict constraint) | `{"policy_json": {}}` → 422 |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| `extra="forbid"` on body request models | Local Canon | Established in BV1 (handoff 098), accounts.py L47/59 |
| `StrippedStr` for string body inputs | Local Canon | Established in BV1 (accounts.py L30) |
| PATCH retains query params (non-breaking) | Spec | 09-scheduling.md §9.10 defines discrete params; tests/unit/test_api_scheduling.py L309 confirms |
| `Query(min_length=1)` on string query params | Local Canon | BV1 min_length=1 pattern extended to query params |
| Non-empty dict validation | Local Canon | `Field(min_length=1)` cannot apply to dicts — use `@field_validator` |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/api/src/zorivest_api/routes/scheduling.py` | modify | Add `extra="forbid"` to `PolicyCreateRequest` and `RunTriggerRequest`; add `Query(min_length=1)` to PATCH string params; add `policy_json` non-empty validator |
| `tests/unit/test_api_scheduling.py` | modify | Add BV negative test class with 5+ test methods |

---

### MEU-BV7: Watchlist Boundary Hardening

#### Boundary Inventory

| Surface | Schema Owner | Field Constraints | Extra-Field Policy |
|---------|-------------|-------------------|-------------------|
| `POST /` body | `CreateWatchlistRequest` | `name: StrippedStr` (min_length=1), `description: str` | `extra="forbid"` |
| `PUT /{id}` body | `UpdateWatchlistRequest` | `name: Optional[StrippedStr]` (min_length=1), `description: Optional[str]` | `extra="forbid"` |
| `POST /{id}/items` body | `AddTickerRequest` | `ticker: StrippedStr` (min_length=1), `notes: str` | `extra="forbid"` |

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-1 | `CreateWatchlistRequest` has `extra="forbid"` — extra fields → 422 | Local Canon (BV1) | `{"name": "x", "sneaky": true}` → 422 |
| AC-2 | `CreateWatchlistRequest.name` uses `StrippedStr + Field(min_length=1)` — blank name → 422 | Local Canon (BV1) | `{"name": "  "}` → 422 |
| AC-3 | `UpdateWatchlistRequest` has `extra="forbid"` — extra fields → 422 | Local Canon (BV1) | `{"name": "x", "sneaky": true}` → 422 |
| AC-4 | `UpdateWatchlistRequest.name` uses `Optional[StrippedStr] + Field(min_length=1)` — blank name on update → 422 | Local Canon (BV1) | `{"name": "  "}` → 422 |
| AC-5 | `AddTickerRequest` has `extra="forbid"` — extra fields → 422 | Local Canon (BV1) | `{"ticker": "AAPL", "sneaky": true}` → 422 |
| AC-6 | `AddTickerRequest.ticker` uses `StrippedStr + Field(min_length=1)` — blank ticker → 422 | Local Canon (BV1) | `{"ticker": "  "}` → 422 |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| `extra="forbid"` on all 3 request models | Local Canon | BV1 pattern |
| `StrippedStr` for `name` and `ticker` | Local Canon | BV1 pattern |
| Create/update parity for name invariant | Local Canon | BV1 AC-5 established the precedent |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/api/src/zorivest_api/routes/watchlists.py` | modify | Add `StrippedStr`, `Field(min_length=1)`, `extra="forbid"` to all 3 request models |
| `tests/unit/test_api_watchlists.py` | modify | Add BV negative test class with 6+ test methods |

---

### MEU-BV8: Settings Boundary Hardening

#### Boundary Inventory

| Surface | Schema Owner | Field Constraints | Extra-Field Policy |
|---------|-------------|-------------------|-------------------|
| `PUT /` body | `dict[str, Any]` (existing flat-map — preserved) | Non-empty dict check via route guard | N/A (flat-map, no Pydantic model wrapper) |
| `PUT /{key}` body | `UpdateSettingRequest` (NEW) | `value: Any` (required) | `extra="forbid"` |

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-1 | `PUT /` preserves flat-map contract `{"key1": "val"}` — existing callers unchanged | Spec (04d-api-settings.md §Body) | `{"ui.theme": "dark"}` → 200 (unchanged) |
| AC-2 | `PUT /` rejects empty body `{}` → 422 | Local Canon (non-empty constraint) | `{}` → 422 |
| AC-3 | `PUT /{key}` uses `UpdateSettingRequest` with `extra="forbid"` — extra fields → 422 | Local Canon (BV1) | `{"value": "x", "sneaky": true}` → 422 |
| AC-4 | `PUT /{key}` requires `value` field — missing `value` → 422 | Local Canon (Pydantic required field) | `{}` → 422 |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| Flat-map body preserved for bulk PUT | Spec | 04d-api-settings.md defines `Body: {"key1": "value1", "key2": "value2"}`; MCP callers confirmed (settings-tools.ts L71) |
| Empty-body guard on bulk PUT | Local Canon | Non-empty constraint consistent with bulk_upsert contract |
| `extra="forbid"` on single-key PUT model | Local Canon | BV1 pattern |
| `value` required field on single-key PUT | Local Canon | Pydantic required field enforcement |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/api/src/zorivest_api/routes/settings.py` | modify | Add empty-body guard to bulk PUT; create `UpdateSettingRequest` model for single-key PUT; update single-key route signature |
| `tests/unit/test_api_settings.py` | modify | Add BV negative test class with 4+ test methods |

---

## Out of Scope

- Settings key-level validation (already handled by `SettingsRegistry`/`SettingsValidator`)
- Scheduling domain validation (policy_json content validation is handled by `PolicyDocument` Pydantic model in core)
- MCP tool boundary hardening (tracked separately as `[MCP-ZODSTRIP]`)
- GUI callers (blocked on these MEUs being completed first)

---

## BUILD_PLAN.md Audit

This project does not add new build-plan sections. It closes `[BOUNDARY-GAP]` findings F4, F7, and Settings in `known-issues.md`. After execution, `known-issues.md` must be updated to mark all three as ✅ resolved.

```powershell
rg "boundary-validation-phase2" docs/BUILD_PLAN.md  # Expected: 0 matches
```

---

## Verification Plan

### 1. Red Phase — Tests Fail Before Implementation
```powershell
uv run pytest tests/unit/test_api_scheduling.py -k "Boundary" -x --tb=short -v *> C:\Temp\zorivest\bv6-red.txt; Get-Content C:\Temp\zorivest\bv6-red.txt | Select-Object -Last 30
uv run pytest tests/unit/test_api_watchlists.py -k "Boundary" -x --tb=short -v *> C:\Temp\zorivest\bv7-red.txt; Get-Content C:\Temp\zorivest\bv7-red.txt | Select-Object -Last 30
uv run pytest tests/unit/test_api_settings.py -k "Boundary" -x --tb=short -v *> C:\Temp\zorivest\bv8-red.txt; Get-Content C:\Temp\zorivest\bv8-red.txt | Select-Object -Last 30
```

### 2. Green Phase — Tests Pass After Implementation
```powershell
uv run pytest tests/unit/test_api_scheduling.py tests/unit/test_api_watchlists.py tests/unit/test_api_settings.py -x --tb=short -v *> C:\Temp\zorivest\bv-green.txt; Get-Content C:\Temp\zorivest\bv-green.txt | Select-Object -Last 40
```

### 3. Regression — Full Test Suite
```powershell
uv run pytest tests/ -x --tb=short -v *> C:\Temp\zorivest\pytest-full.txt; Get-Content C:\Temp\zorivest\pytest-full.txt | Select-Object -Last 40
```

### 4. Lint + Type Check
```powershell
uv run ruff check packages/api/src/ packages/core/src/ *> C:\Temp\zorivest\ruff.txt; Get-Content C:\Temp\zorivest\ruff.txt | Select-Object -Last 20
```

### 5. OpenAPI Spec Regeneration
```powershell
uv run python tools/export_openapi.py -o openapi.committed.json *> C:\Temp\zorivest\openapi.txt; Get-Content C:\Temp\zorivest\openapi.txt
```

### 6. MEU Gate
```powershell
uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate.txt; Get-Content C:\Temp\zorivest\validate.txt | Select-Object -Last 50
```

---

## Open Questions

None — all behaviors are resolved from Local Canon (BV1–BV5 established pattern).

---

## Research References

- [BV1 handoff (accounts)](../../.agent/context/handoffs/098-2026-04-05-boundary-accounts-bp04bs1.md) — canonical hardening pattern
- [BOUNDARY-GAP known issue](../../.agent/context/known-issues.md) — F4, F7, Settings tracking
