---
project: "2026-04-11-pyright-test-cleanup"
date: "2026-04-11"
source: "docs/BUILD_PLAN.md (MEU-TS2, MEU-TS3)"
meus: ["MEU-TS2", "MEU-TS3"]
status: "approved"
template_version: "2.0"
---

# Implementation Plan: Pyright Test Suite Cleanup

> **Project**: `2026-04-11-pyright-test-cleanup`
> **Build Plan Section(s)**: `docs/BUILD_PLAN.md` MEU-TS2 + MEU-TS3 rows (supporting canon: testing-strategy §1.2, §1.4; 01-domain-layer.md)
> **Status**: `approved`

---

## Goal

Resolve all 205 Pyright type errors in `tests/` to achieve a fully type-checked test suite. Production code (`packages/`) is already clean at 0 errors. This project combines MEU-TS2 (enum literal verification) and MEU-TS3 (entity factory typing + SQLAlchemy descriptor fixes) into a single coherent cleanup pass.

**Current state**: 205 errors across 15 files.
**Target state**: 0 actionable errors (7 `test_encryption_integrity.py` errors excluded per MEU-90c closure).

---

## User Review Required

> [!IMPORTANT]
> **Test-only changes.** All modifications are confined to `tests/` — zero production code (`packages/`) will be touched. No behavioral changes to any test assertions; only type annotation and type-narrowing improvements.

> [!IMPORTANT]
> **SQLAlchemy `type: ignore` strategy.** 59 errors are caused by SQLAlchemy Column descriptor typing where Pyright sees `ColumnElement[bool]` from `==` comparisons on loaded model attributes. The models use legacy `Column(Type)` patterns (not `Mapped[T]`), which is correct for production but causes false positives in tests. The fix is targeted `# type: ignore[reportGeneralTypeIssues]` comments on each affected assertion line. This is the standard approach documented by SQLAlchemy and Pyright communities for legacy Column patterns.

> [!IMPORTANT]
> **MEU-TS2 is effectively a no-op.** The original scope ("replace ~50 raw string literals with enum values") was resolved by boundary validation work (MEU-BV1–BV8) which systematically introduced enum usage. Current Pyright scan shows 0 string-literal-vs-enum errors. MEU-TS2 will be verified as complete with evidence, not re-implemented.

> [!IMPORTANT]
> **Encryption test exclusion.** 7 errors in `test_encryption_integrity.py` (5× `sqlcipher3` unbound, 2× `key_vault` missing import) are excluded per MEU-90c closure ("won't fix locally; CI covered by `crypto-tests` job"). These will remain as-is.

---

## Proposed Changes

### MEU-TS2: Enum Literal Verification (No-Op)

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-1 | Zero string-literal-vs-enum Pyright errors in `tests/` | Spec (BUILD_PLAN.md MEU-TS2 row) | N/A — verification only |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| Enum literals already replaced by BV work | Local Canon (MEU-BV1–BV8 handoffs) | Verify 0 errors remain, mark complete |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| (none) | — | No changes needed; verification only |

---

### MEU-TS3: Entity Factory Typing + SQLAlchemy Descriptor Fixes

Organized by fix strategy group:

---

#### Group 1: Entity Factory Return Types (105 errors → 0)

**Root cause**: 8 `_make_*` helper functions in `test_entities.py` return `-> object` instead of the specific entity type, causing every attribute access on the result to be a Pyright `reportAttributeAccessIssue`.

**Fix**: Change return type annotations to the actual entity type.

| Factory Function | Current Return | Corrected Return |
|-----------------|---------------|-----------------|
| `_make_trade` | `-> object` | `-> Trade` |
| `_make_account` | `-> object` | `-> Account` |
| `_make_image_attachment` | `-> object` | `-> ImageAttachment` |
| `_make_balance_snapshot` | `-> object` | `-> BalanceSnapshot` |
| `_make_trade_report` | `-> object` | `-> TradeReport` |
| `_make_trade_plan` | `-> object` | `-> TradePlan` |
| `_make_watchlist` | `-> object` | `-> Watchlist` |
| `_make_watchlist_item` | `-> object` | `-> WatchlistItem` |

The imports are already present inside each function body (lazy imports). The return type annotation will reference the type from `zorivest_core.domain.entities` — the `from __future__ import annotations` at file top enables forward references.

| File | Action | Summary |
|------|--------|---------|
| `tests/unit/test_entities.py` | modify | Fix 8 factory return types from `-> object` to specific entity types; add top-level `TYPE_CHECKING` imports |

---

#### Group 2: Optional Narrowing Guards (24 errors → 0)

**Root cause**: Functions return `Optional[T]` or `T | None`, and tests access attributes or subscript the result without first asserting `is not None`.

**Fix**: Add `assert obj is not None` before the first attribute access / subscript.

**Subgroups**:

- **reportOptionalMemberAccess** (14 errors, 4 files): Access `.field` on possibly-None object
- **reportOptionalSubscript** (7 errors, 1 file): Subscript `result["key"]` on possibly-None dict
- **reportOperatorIssue** (3 errors, 2 files): `"value" in str_or_none` where RHS is `str | None`

| File | Action | Summary |
|------|--------|---------|
| `tests/unit/test_scheduling_repos.py` | modify | Add `assert ... is not None` before 6 attribute accesses on Optional repo results |
| `tests/unit/test_report_service.py` | modify | Add `assert ... is not None` before 5 attribute accesses on Optional service results |
| `tests/unit/test_store_render_step.py` | modify | Add `assert ... is not None` before 2 attribute accesses + 1 `in` operator |
| `tests/unit/test_pipeline_runner.py` | modify | Add `assert ... is not None` before 1 attribute access |
| `tests/unit/test_scheduling_service.py` | modify | Add `assert result is not None` before 7 dict subscripts |
| `tests/unit/test_send_step.py` | modify | Add `assert ... is not None` before 1 `in` operator |
| `tests/unit/test_transform_step.py` | modify | Add `assert ... is not None` before 1 `in` operator |

---

#### Group 3: SQLAlchemy Column Descriptor Suppressions (59 errors → 0)

**Root cause**: SQLAlchemy models use legacy `Column(Type)` patterns. When Pyright sees `model.field == "value"` on a loaded instance, it resolves the Column descriptor and returns `ColumnElement[bool]` instead of `bool`, causing `reportGeneralTypeIssues`. Similarly, assigning `model.field = value` triggers `reportAttributeAccessIssue`.

**Fix**: Add `# type: ignore[reportGeneralTypeIssues]` on equality assertion lines and `# type: ignore[reportAttributeAccessIssue]` on assignment lines. This is the standard approach for legacy SQLAlchemy models with non-`Mapped` columns.

| File | Errors | Sub-type | Action |
|------|--------|----------|--------|
| `tests/unit/test_scheduling_models.py` | 18 + 5 = 23 | 18 ColumnElement[bool], 5 attribute assignment | Add 23 `# type: ignore` comments |
| `tests/unit/test_scheduling_repos.py` | 12 | ColumnElement[bool] | Add 12 `# type: ignore` comments |
| `tests/unit/test_models.py` | 8 | ColumnElement[bool] | Add 8 `# type: ignore` comments |
| `tests/unit/test_send_step.py` | 6 | ColumnElement[bool] | Add 6 `# type: ignore` comments |
| `tests/unit/test_store_render_step.py` | 4 | ColumnElement[bool] | Add 4 `# type: ignore` comments |
| `tests/unit/test_fetch_step.py` | 3 | ColumnElement[bool] | Add 3 `# type: ignore` comments |
| `tests/unit/test_pipeline_runner.py` | 2 | ColumnElement[bool] | Add 2 `# type: ignore` comments |
| `tests/unit/test_entities.py` | 1 | attribute assignment (is_archived) | Add 1 `# type: ignore` comment |

---

#### Group 4: Constructor & Miscellaneous Fixes (10 errors → 0)

**Root cause**: Various case-specific type errors.

| File | Error(s) | Fix |
|------|----------|-----|
| `tests/unit/test_fetch_step.py` | 2× `reportCallIssue` — missing constructor args | Add missing required params to test data constructors |
| `tests/unit/test_send_step.py` | 1× `reportCallIssue` — missing `channel` arg | Add missing `channel` param |
| `tests/unit/test_store_render_step.py` | 1× `reportCallIssue` — missing `report_name` arg | Add missing `report_name` param |
| `tests/unit/test_transform_step.py` | 1× `reportCallIssue` — missing `target_table` arg | Add missing `target_table` param |
| `tests/unit/test_normalizers.py` | 2× type mismatch (return type + arg type) | Fix return type annotation and add type narrowing |
| `tests/unit/test_pipeline_runner.py` | 1× readonly attr assignment on `PolicyStep.timeout` | Use `object.__setattr__` or mock |
| `tests/unit/test_market_data_service.py` | 1× `MethodType.assert_called` access | Cast mock method to `MagicMock` |
| `tests/unit/test_watchlist_service.py` | 1× `SqlAlchemyUnitOfWork` vs `UnitOfWork` protocol | Cast to `UnitOfWork` or use `# type: ignore` |

| File | Action | Summary |
|------|--------|---------|
| `tests/unit/test_fetch_step.py` | modify | Add 2 missing constructor params |
| `tests/unit/test_send_step.py` | modify | Add 1 missing `channel` param |
| `tests/unit/test_store_render_step.py` | modify | Add 1 missing `report_name` param |
| `tests/unit/test_transform_step.py` | modify | Add 1 missing `target_table` param |
| `tests/unit/test_normalizers.py` | modify | Fix return type + arg type |
| `tests/unit/test_pipeline_runner.py` | modify | Fix readonly attr assignment |
| `tests/unit/test_market_data_service.py` | modify | Cast mock method |
| `tests/unit/test_watchlist_service.py` | modify | Fix protocol type |

---

#### Acceptance Criteria (MEU-TS3)

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-1 | All 8 `_make_*` factories return typed entity, not `object` | Spec (BUILD_PLAN.md MEU-TS3 row) | N/A (type annotation fix) |
| AC-2 | All `Optional` member accesses narrowed with `assert is not None` | Local Canon (testing-strategy.md) | N/A (type narrowing) |
| AC-3 | All SQLAlchemy `ColumnElement[bool]` assertions suppressed with targeted `type: ignore` | Research-backed (SQLAlchemy + Pyright FAQs) | N/A (suppression) |
| AC-4 | All constructor call errors resolved with correct args | Spec (BUILD_PLAN.md MEU-TS3 row) | N/A (test fixture fix) |
| AC-5 | Remaining misc type errors resolved | Spec (BUILD_PLAN.md MEU-TS3 row) | N/A |
| AC-6 | `uv run pyright tests/` reports ≤ 7 errors (only `test_encryption_integrity.py`) | Spec (zero-error target minus MEU-90c exclusion) | N/A |
| AC-7 | `uv run pytest tests/` passes with 0 failures (no regressions) | Local Canon (AGENTS.md §Testing) | N/A |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| Factory return types must match entity types | Spec | BUILD_PLAN.md MEU-TS3 row: "resolve ~121 entity factory typing errors" |
| SQLAlchemy Column descriptor typing is a known limitation | Research-backed | SQLAlchemy docs: legacy Column patterns require type: ignore for Pyright |
| Optional narrowing required before attribute access | Local Canon | testing-strategy.md + AGENTS.md type-check requirements |
| Encryption test exclusion | Human-approved | MEU-90c closed per ADR-001 A+B, human decision |

---

## Out of Scope

- **Production code changes** (`packages/`): Already clean at 0 errors
- **`test_encryption_integrity.py`** (7 errors): MEU-90c closed — sqlcipher3/key_vault are CI-only dependencies
- **SQLAlchemy model migration to `Mapped[T]`**: Would fix ColumnElement errors at source but is a massive production change unrelated to this MEU
- **Pyright strict mode**: Current config is `basic` (standard); no config changes planned

---

## BUILD_PLAN.md Audit

This project modifies status for MEU-TS2 and MEU-TS3 rows in `docs/BUILD_PLAN.md`. Validation:

```powershell
# Confirm MEU-TS2 and MEU-TS3 rows exist and are updated
rg "MEU-TS[23]" docs/BUILD_PLAN.md  # Expected: 2 matches with ✅ status
```

---

## Verification Plan

### 1. Pyright Test Suite (primary gate)
```powershell
uv run pyright tests/ *> C:\Temp\zorivest\pyright-ts3-final.txt; Get-Content C:\Temp\zorivest\pyright-ts3-final.txt | Select-Object -Last 10
# Expected: ≤ 7 errors (all in test_encryption_integrity.py)
```

### 2. Test Regression
```powershell
uv run pytest tests/ -x --tb=short -v *> C:\Temp\zorivest\pytest-ts3.txt; Get-Content C:\Temp\zorivest\pytest-ts3.txt | Select-Object -Last 40
# Expected: 0 failures
```

### 3. Production Code Untouched
```powershell
uv run pyright packages/ *> C:\Temp\zorivest\pyright-packages.txt; Get-Content C:\Temp\zorivest\pyright-packages.txt | Select-Object -Last 5
# Expected: 0 errors (unchanged)
```

### 4. Anti-Placeholder Scan
```powershell
rg "TODO|FIXME|NotImplementedError" tests/ --glob "*.py" *> C:\Temp\zorivest\placeholder-check.txt; Get-Content C:\Temp\zorivest\placeholder-check.txt
# Expected: 0 new hits
```

### 5. MEU Gate
```powershell
uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate-ts3.txt; Get-Content C:\Temp\zorivest\validate-ts3.txt | Select-Object -Last 50
```

---

## Open Questions

None — all design decisions are resolved with existing sources.

---

## Research References

- [SQLAlchemy Pyright typing FAQ](https://docs.sqlalchemy.org/en/20/orm/extensions/mypy.html) — Column descriptor behavior with type checkers
- BUILD_PLAN.md MEU-TS2/TS3 rows
- ADR-001 (MEU-90c closure decision)
- MEU-BV1–BV8 handoffs (enum literal resolution evidence)
