---
project: "2026-05-13-quarterly-tax-payments"
meus: ["MEU-143", "MEU-144", "MEU-145", "MEU-146", "MEU-147"]
status: "corrections_applied"
verbosity: "standard"
completed_at: "2026-05-13T18:08:00Z"
---

# Handoff — Quarterly Tax Payments & Tax Brackets

## Summary

Phase 3D implementation complete: 5 MEUs (143-147) delivering the quarterly estimated tax payment engine with IRS-compliant bracket tables, NIIT surtax, safe harbor, annualized income (Form 2210 Schedule AI), due dates, and underpayment penalty logic.

<!-- CACHE BOUNDARY -->

## Evidence Bundle

### Changed Files

| File | Change Type | MEU |
|------|-------------|-----|
| `domain/tax/brackets.py` | NEW | MEU-146 |
| `domain/tax/niit.py` | NEW | MEU-147 |
| `domain/tax/quarterly.py` | NEW | MEU-143/144/145 |
| `tests/unit/test_tax_brackets.py` | NEW | MEU-146 |
| `tests/unit/test_tax_niit.py` | NEW | MEU-147 |
| `tests/unit/test_tax_quarterly.py` | NEW | MEU-143/144/145 |
| `domain/tax/__init__.py` | MODIFIED | All |
| `domain/entities.py` | MODIFIED | MEU-143 |
| `application/ports.py` | MODIFIED | MEU-143 |
| `services/tax_service.py` | MODIFIED | MEU-145 |
| `tests/unit/test_entities.py` | MODIFIED | MEU-143 |
| `tests/unit/test_ports.py` | MODIFIED | MEU-143 |

### Test Results

- **Brackets**: 44 passed (+5 from AC-146.6 `compute_combined_rate`)
- **NIIT**: 15 passed (unchanged)
- **Quarterly**: 39 passed (+8: 3 annualized min() tests, 5 record_payment validation tests)
- **Full suite**: 3472 passed, 0 failed, 23 skipped

### Quality Gates

- Pyright: 0 errors, 0 warnings
- Ruff: All checks passed
- Anti-placeholder: Clean (except allowed `record_payment` `[B]` stub)
- MEU gate: 8/8 blocking checks passed

### FAIL_TO_PASS Evidence

- `quarterly-red.txt`: `ModuleNotFoundError: No module named 'zorivest_core.domain.tax.quarterly'` — 1 error during collection (RED phase)
- `quarterly-green.txt`: 31 passed (GREEN phase)
- `combined-red.txt`: `ImportError: cannot import name 'compute_combined_rate'` (RED phase — AC-146.6)
- `annualized-min-red.txt`: `TypeError: got unexpected keyword argument 'required_annual_payment'` (RED — AC-144.4)
- `record-red.txt`: 4 failed — `NotImplementedError` raised instead of `BusinessRuleError` (RED — AC-145.7)

## Corrections Applied (Session 2)

| Gap | AC | Change | Evidence |
|-----|-----|--------|----------|
| Missing `compute_combined_rate()` | AC-146.6 | Added function to `brackets.py` + 5 tests | `combined-green.txt`: 5 passed |
| Annualized income missing `min(annualized, regular)` | AC-144.4 | Added `required_annual_payment` param + min() logic + 3 tests | `annualized-green.txt`: 12 passed |
| `record_payment()` no input validation | AC-145.7 | Added quarter/amount validation before `NotImplementedError` + 5 tests | `record-green.txt`: 5 passed |
| Stale `Rev. Proc. 2025-XX` | Documentation | Updated to `Rev. Proc. 2025-32` in `brackets.py` | `revproc-final.txt`: 0 matches |

## Blocked Items

| Item | Status | Follow-up |
|------|--------|-----------|
| `TaxService.record_payment()` | `[B]` | MEU-148 infrastructure wiring |

## Design Decisions

1. **Decimal precision**: All financial calculations use `Decimal` with `.quantize(Decimal("0.01"))` for IRS-compliant 2-decimal-place output.
2. **Safe harbor 110% threshold**: $150K for all filing statuses except MFS ($75K), matching IRS Pub 505 §2.
3. **Weekend shift only**: Due dates shift Saturday→Monday and Sunday→Monday. Federal holiday handling deferred to future enhancement.
4. **Annualization factors**: Standard IRS Form 2210 Schedule AI factors `[4, 2.4, 1.5, 1]`. No calendar-year fiscal year variants.
5. **record_payment stub**: Method signature defined with input validation, body raises `NotImplementedError` — requires `QuarterlyEstimate` persistence layer (MEU-148).
6. **`compute_combined_rate()`**: Simple `federal + state` addition with negative-state validation. State rate is a flat passthrough from `TaxProfile.state_tax_rate`, not a graduated bracket lookup.
7. **AC-144.4 `min()` rule**: `required_annual_payment` is keyword-only and optional (default `None`) for backward compatibility. When provided, `regular_installment = 25% × required_annual_payment` and each quarter uses `min(annualized, regular)`.

## Post-Correction Evidence (Recheck Round 2)

### Commands Executed

```powershell
uv run pytest tests/unit/test_tax_service.py -x --tb=short -v -k "quarterly"  # 13 passed
uv run pytest tests/ --tb=no -q                                              # 3472 passed
uv run pyright packages/core/src/zorivest_core/services/tax_service.py        # 0 errors
uv run ruff check packages/core/ tests/unit/                                  # All passed
```

### Corrections Applied

| Correction | Description |
|------------|-------------|
| Method names | `safe_harbor/annualized` → `annualized/prior_year/actual` per 04f-api-tax.md |
| Default method | `safe_harbor` → `annualized` (API spec default) |
| Result fields | Added `paid`, `due`, `penalty` to `QuarterlyEstimateResult` |
| `actual` method | Raises `BusinessRuleError` — deferred to MEU-148 |
| 2026 brackets | Updated to Rev. Proc. 2025-32 thresholds |

### Commands run

```powershell
# Initial TDD phase
uv run pytest tests/unit/test_tax_brackets.py tests/unit/test_tax_niit.py tests/unit/test_tax_quarterly.py -x --tb=short -v  # 98 passed
uv run pytest tests/ --tb=no -q  # 3472 passed, 23 skipped
uv run pyright packages/core/ --outputjson  # 0 errors
uv run ruff check packages/core/ tests/unit/  # All checks passed
uv run python tools/validate_codebase.py --scope meu  # 8/8 blocking passed
```
