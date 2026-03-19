---
description: GUI-API seam testing workflow — validates integration boundaries between GUI and API for every feature that adds or modifies CRUD endpoints.
---

# GUI Integration Testing Workflow

## Purpose

This workflow ensures that **every GUI feature** is tested at the integration seams — the boundaries between the TypeScript GUI and the Python API where most runtime bugs hide. Standard unit tests miss these bugs because they test each layer in isolation.

## When to Use

Run this workflow for **every MEU that adds or modifies**:
- API CRUD endpoints consumed by the GUI
- GUI forms that POST/PUT/DELETE to the API
- TypeScript interfaces that mirror API response models
- Table/list views that render API response data

## Bug Classes This Catches

| # | Bug Class | Example | How Caught |
|---|-----------|---------|------------|
| 1 | **Field name mismatch** | GUI uses `created_at`, API returns `time` | Field alignment test |
| 2 | **Missing update fields** | `UpdateTradeRequest` only had 3 of 9 fields | Schema completeness test |
| 3 | **Response format crash** | `apiFetch` calls `.json()` on 204 No Content | Response format test |
| 4 | **Type coercion crash** | SQLAlchemy Numeric → string breaks `.toFixed()` | Numeric type test |
| 5 | **Silent field drop** | Service filters out valid fields | Every-field update test |
| 6 | **Schema migration gap** | Model adds column but existing DB lacks it | Startup migration test |

## Steps

### Step 0: Visual Consistency Check

Verify that table columns render consistently at all widths (e.g., 60% with detail panel open vs 100% without).

**Alignment Rule:** Header and cell alignment must use the same source of truth.

```typescript
// ✅ CORRECT — shared helper, impossible to drift
const getAlignClass = (meta: unknown): string =>
    (meta as any)?.align === 'right' ? 'text-right' : 'text-left'

// <th> uses: getAlignClass(header.column.columnDef.meta)
// <td> uses: getAlignClass(cell.column.columnDef.meta)
```

```typescript
// ❌ WRONG — duplicated logic, will drift apart
// <th>: className="text-left"              ← always left
// <td>: className={meta?.align === 'right' ? 'text-right' : ''}  ← right for numbers
```

**Checklist:**
- [ ] All `<th>` and `<td>` use the same `getAlignClass()` helper
- [ ] Numeric columns set `meta: { align: 'right' }` in column definitions
- [ ] Table tested at both narrow (detail panel open) and full width
- [ ] No hardcoded `text-left` or `text-right` in table rendering

### Step 1: Field Alignment Check

Verify that the GUI's TypeScript interface field names match the API's Pydantic response model.

```python
# In test_gui_api_seams.py
GUI_FIELDS = {"exec_id", "instrument", "action", "quantity", ...}
response_fields = set(ResponseModel.model_fields.keys())
missing = GUI_FIELDS - response_fields
assert not missing, f"API response missing GUI fields: {missing}"
```

**What to check manually:**
- Open the GUI's TypeScript `interface` (e.g., `TradesTable.tsx`)
- Open the API's Pydantic response model (e.g., `TradeResponse`)
- Every field in the TS interface must exist in the Pydantic model

### Step 2: Schema Completeness Check

Verify that `Update*Request` schemas cover all non-readonly fields of the domain entity.

```python
trade_fields = set(Trade.__dataclass_fields__.keys())
update_fields = set(UpdateTradeRequest.model_fields.keys())
READONLY = {"exec_id", "images", "report"}
missing = (trade_fields - READONLY) - update_fields
assert not missing
```

### Step 3: Every-Field Update Round-Trip

Write a test for **every** field the GUI can edit. One test per field.

```python
def test_update_action_bot_to_sld(self, client):
    r = client.put("/api/v1/trades/ID", json={"action": "SLD"})
    assert r.status_code == 200
    assert r.json()["action"] == "SLD"
```

**Rule:** If the GUI has an input/select for a field, there MUST be a round-trip test for it.

### Step 4: Response Format Validation

Test that:
- DELETE returns 204 with empty body (not JSON)
- List returns `{"items": [...]}` with proper types
- All numeric fields are `int|float`, not strings
- Datetime fields are ISO strings

```python
def test_delete_returns_204_empty(self, client):
    r = client.delete("/api/v1/trades/ID")
    assert r.status_code == 204
    assert r.content == b""
```

### Step 5: Run Quality Gate

```bash
// turbo
uv run pytest tests/integration/test_gui_api_seams.py -v
```

### Step 6: DB Migration Check

If any ORM model gained a new column, verify:
1. `Base.metadata.create_all()` handles fresh databases
2. `ALTER TABLE` migration exists in `main.py` lifespan for existing databases

## Checklist Template

Copy this into MEU handoffs for any GUI+API feature:

```markdown
### GUI-API Seam Tests
- [ ] TS interface fields ⊆ Pydantic response fields
- [ ] Update schema covers all non-readonly domain fields
- [ ] Round-trip test for every updateable field
- [ ] DELETE returns 204 empty body
- [ ] List items have correct numeric types (not strings)
- [ ] DB migration for new columns on existing tables
- [ ] `apiFetch` handles response status (200 JSON, 204 empty, 4xx error)
```

## Files

| File | Purpose |
|------|---------|
| `tests/integration/test_gui_api_seams.py` | Seam tests (run with pytest) |
| `tests/unit/test_schema_contracts.py` | Schema↔Domain contract tests |
| `tests/integration/test_api_roundtrip.py` | Basic CRUD round-trip tests |
| `docs/build-plan/testing-strategy.md` | Strategy doc (§GUI-API Seam Testing) |
