---
project: "2026-05-12-tax-rules-reporting"
meus: ["MEU-127", "MEU-128", "MEU-129"]
status: "implementation_complete"
verdict: "awaiting_validation"
verbosity: "standard"
completed: "2026-05-12T20:02:00-04:00"
---

# Handoff — Tax Rules & Reporting

## Summary

Implemented all three Phase 3A Tax Engine MEUs (127-129) following strict TDD workflow. All 60 new tests pass, full suite green (3196 passed), pyright/ruff clean.

<!-- CACHE BOUNDARY -->

## Evidence Bundle

### MEU-127: Capital Loss Carryforward

**Changed Files:**
- `packages/core/src/zorivest_core/domain/tax/loss_carryforward.py` — `apply_capital_loss_rules()`, `CapitalLossResult`
- `packages/core/src/zorivest_core/services/tax_service.py` — `get_taxable_gains()`, `TaxableGainsResult`
- `tests/unit/test_loss_carryforward.py` — 22 tests
- `tests/unit/test_tax_service.py` — 4 tests (TestGetTaxableGains)

**Acceptance Criteria:**
- AC-127.1: Function signature + return type ✅ (test_returns_capital_loss_result, test_result_has_all_fields)
- AC-127.2: $3K cap SINGLE/MJ/HoH, $1.5K MARRIED_SEPARATE ✅ (4 filing status tests + under-cap test)
- AC-127.3: IRS Schedule D netting order ✅ (8 tests: within-pool, cross-net, wipeout, character preservation)
- AC-127.4: Tax-advantaged account exclusion ✅ (test_excludes_tax_advantaged_accounts)
- AC-127.5: Carryforward from TaxProfile ✅ (test_applies_carryforward_from_tax_profile)

### MEU-128: Options Assignment/Exercise

**Changed Files:**
- `packages/core/src/zorivest_core/domain/tax/option_pairing.py` — `parse_option_symbol()`, `OptionDetails`, `AssignmentType`, `adjust_basis_for_assignment()`, `AdjustedBasisResult`
- `packages/core/src/zorivest_core/services/tax_service.py` — `pair_option_assignment()`
- `tests/unit/test_option_pairing.py` — 17 tests
- `tests/unit/test_tax_service.py` — 3 tests (TestPairOptionAssignment)

**Acceptance Criteria:**
- AC-128.1: parse_option_symbol normalized format ✅ (8 tests: call, put, non-option, malformed, empty, OCC)
- AC-128.2: Short put assignment reduces basis ✅ (test_reduces_cost_basis_by_premium)
- AC-128.3: Short call assignment increases proceeds ✅ (test_increases_proceeds_by_premium)
- AC-128.4: Long call exercise adds to basis ✅ (test_adds_premium_to_cost_basis)
- AC-128.5: Long put exercise reduces proceeds ✅ (test_reduces_proceeds_by_premium)
- AC-128.6: Service persists adjusted basis ✅ (test_pair_short_put_assignment)
- AC-128.7: OptionDetails frozen dataclass ✅ (test_frozen_dataclass)
- AC-128.9: Action consistency validation ✅ (test_wrong_action_raises × 2)

### MEU-129: YTD P&L by Symbol

**Changed Files:**
- `packages/core/src/zorivest_core/domain/tax/ytd_pnl.py` — `compute_ytd_pnl()`, `SymbolPnl`, `YtdPnlResult`
- `packages/core/src/zorivest_core/services/tax_service.py` — `get_ytd_pnl()`
- `tests/unit/test_ytd_pnl.py` — 11 tests
- `tests/unit/test_tax_service.py` — 3 tests (TestGetYtdPnl)

**Acceptance Criteria:**
- AC-129.1: Return type with breakdown + totals ✅ (3 tests)
- AC-129.2: SymbolPnl fields ✅ (test_symbol_pnl_fields)
- AC-129.3: Year filtering ✅ (3 tests: included, excluded, mixed)
- AC-129.4: Service orchestration with tax-advantaged exclusion ✅ (3 service tests)
- AC-129.5: Ticker aggregation ✅ (4 tests: same ticker, different, mixed ST/LT, losses)

### Shared Changes

- `packages/core/src/zorivest_core/domain/tax/__init__.py` — full re-exports of all domain types
- `packages/core/src/zorivest_core/services/__init__.py` — TaxService export added

### Quality Gates

| Check | Result |
|-------|--------|
| pytest (full) | 3196 passed, 23 skipped |
| pyright | 0 errors |
| ruff | All checks passed |
| anti-placeholder | Clean (1 pre-existing abstract in step_registry.py) |

## Known Issues

None introduced by this session.

## Next Steps

1. Trigger `/execution-critical-review` for validation
2. Upon validation pass, transition MEU-127/128/129 from 🟡 to ✅
3. Proceed to Phase 3B (Wash Sale Engine) or 3C (Tax Bracket Estimation)
