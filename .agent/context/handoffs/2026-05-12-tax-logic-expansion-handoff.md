---
project: tax-logic-expansion
meus: [MEU-125, MEU-126]
session_date: 2026-05-12
status: complete
verbosity: standard
---

<!-- CACHE BOUNDARY -->

# Tax Logic Expansion — Handoff

**MEU-125 (TaxLotTracking) + MEU-126 (TaxGainsCalc)**

## Outcome

All 9 implementation tasks + 4 post-impl tasks completed. MEU gate 8/8 PASS. Full regression 3114 passed, 0 failed.

## Changed Files

```diff
+ packages/core/src/zorivest_core/domain/tax/__init__.py
+ packages/core/src/zorivest_core/domain/tax/lot_selector.py
+ packages/core/src/zorivest_core/domain/tax/gains_calculator.py
+ packages/core/src/zorivest_core/services/tax_service.py
+ tests/unit/test_lot_selector.py
+ tests/unit/test_tax_service.py
+ tests/unit/test_gains_calculator.py
+ tests/integration/test_tax_service_integration.py
```

## Evidence Bundle

| Check | Result |
|-------|--------|
| pytest (full) | 3114 passed, 23 skipped, 0 failed |
| pyright | 0 errors, 0 warnings |
| ruff | All checks passed |
| MEU gate | 8/8 blocking PASS |
| Anti-placeholder | Clean |

### Test Counts by File

| Test File | Count | Scope |
|-----------|-------|-------|
| test_lot_selector.py | 38 | 8 cost basis methods, IBKR 4-tier priority |
| test_tax_service.py | 16 | get_lots, close_lot, reassign_basis, simulate_impact |
| test_gains_calculator.py | 10 | RealizedGainResult, ST/LT, wash sale |
| test_tax_service_integration.py | 8 | Real SQLite round-trip |

## Acceptance Criteria Coverage

### MEU-125: TaxLotTracking

| AC | Description | Status | Evidence |
|----|-------------|--------|----------|
| AC-125.1 | TaxService constructor takes UoW | ✅ | test_constructor_accepts_uow |
| AC-125.2 | get_lots returns filtered lots | ✅ | test_returns_lots_for_account, test_returns_empty_when_no_match |
| AC-125.3 | close_lot derives fields from sell trade | ✅ | test_close_lot_sets_fields + 4 error tests |
| AC-125.4 | reassign_basis enforces T+1 window | ✅ | test_reassign_within_t1, test_reassign_outside_t1 |

### MEU-126: TaxGainsCalc

| AC | Description | Status | Evidence |
|----|-------------|--------|----------|
| AC-126.1 | calculate_realized_gain returns RealizedGainResult | ✅ | test_long_term_gain, test_short_term_gain, test_loss, test_zero_gain |
| AC-126.2 | RealizedGainResult is frozen dataclass | ✅ | test_fields_present, test_is_frozen |
| AC-126.3 | wash_sale_adjustment in basis | ✅ | test_wash_sale_adjustment_increases_basis, test_wash_sale_adjustment_turns_gain_to_loss |
| AC-126.4 | simulate_impact returns ST/LT split + tax estimate | ✅ | test_simulate_st_lt_split, test_simulate_estimated_tax |
| AC-126.5 | simulate_impact uses select_lots + calculate_realized_gain | ✅ | test_simulate_returns_lot_breakdown, test_simulate_correct_lot_order |
| AC-126.6 | Integration round-trip with real SQLite | ✅ | test_simulate_lt_st_split (integ), test_simulate_with_tax_estimate (integ) |

## Corrections Applied (2026-05-12)

Resolved 6 findings from `2026-05-12-tax-logic-expansion-implementation-critical-review.md`.

### Corrections Summary

| Finding | Severity | Correction | Files |
|---------|----------|------------|-------|
| F1 | High | `get_lots` → `status` + `sort_by` params per FIC/service spec | tax_service.py, test_tax_service_integration.py |
| F2 | High | `close_lot` → validate SLD action, account match, linked_trade_ids | tax_service.py |
| F3 | High | `reassign_basis` → add `cost_basis_method` field to TaxLot + persist | entities.py, models.py, tax_repository.py, tax_service.py |
| F4 | High | `simulate_impact` → `wash_risk` output + TaxProfile rate lookup | tax_service.py |
| F5 | Medium | 12 new correction tests cover F1–F4 | test_tax_service.py |
| F6 | Medium | BUILD_PLAN ⬜→✅/🟡, handoff evidence sections | BUILD_PLAN.md |
| R1 | High | `close_lot(lot_id)` auto-discovery: `sell_trade_id` now optional | tax_service.py, test_tax_service.py |
| R2 | High | Quantity validation + `realized_gain_loss` field + compute on close | entities.py, models.py, tax_repository.py, tax_service.py, test_tax_entities.py |
| R3 | Medium | Evidence section naming (Commands Executed, Pass/fail matrix) | handoff |
| RR2-1 | High | Split-lot on partial close (plan spec: "Creates split lot") | tax_service.py, test_tax_service.py |
| RR2-2 | Medium | Evidence `Commands run` section for validator A3 advisory | handoff |
| RR3-1 | Medium | Split-lot persistence path missing real SQLite integration test | test_tax_service_integration.py |

### FAIL_TO_PASS Evidence

```
# Red phase — 12 correction tests all FAILED before implementation:
FAILED tests/unit/test_tax_service.py::TestCloseLotCorrections::test_close_lot_rejects_buy_trade - DID NOT RAISE
  → After fix: close_lot validates trade.action != SLD → BusinessRuleError

# Green phase — 12/12 passed after implementation:
12 passed, 16 deselected, 1 warning in 0.30s

# Round 2 Red phase — 7 recheck tests all FAILED:
FAILED tests/unit/test_tax_service.py::TestCloseLotQuantityAndGain::test_close_lot_rejects_oversize_quantity - DID NOT RAISE
  → After fix: close_lot validates trade.quantity == lot.quantity

# Round 2 Green phase — 7/7 passed:
60 passed (52 unit + 8 integration), 0 failed
```

### Updated Evidence Bundle

| Check | Result |
|-------|--------|
| pytest (full) | 3136 passed, 23 skipped, 0 failed |
| pyright | 0 errors, 0 warnings |
| ruff | All checks passed |
| Anti-placeholder | Clean |

### Commands Executed

```
uv run pytest tests/unit/test_tax_service.py -x --tb=short -v    # Red phase → 7 FAILED (DID NOT RAISE)
uv run pytest tests/unit/test_tax_service.py tests/unit/test_tax_entities.py -x --tb=short -v  # Green phase → 52 passed
uv run pytest tests/integration/test_tax_service_integration.py -x --tb=short -v  # Integration → 8 passed
uv run pytest tests/ -x --tb=short -v   # Full regression → 3133 passed, 23 skipped
uv run pyright packages/                 # Type check → 0 errors
uv run ruff check packages/              # Lint → All checks passed
```

### Pass/fail matrix

| Finding | Tests Added | Red Phase | Green Phase |
|---------|------------|-----------|-------------|
| R2 | 4 (quantity/gain) | 4 FAILED (DID NOT RAISE) | 4 PASSED |
| R1 | 3 (auto-discovery) | 3 FAILED (DID NOT RAISE) | 3 PASSED |
| R3 | 0 (docs only) | N/A | N/A |
| RR2-1 | 3 (split-lot) | 3 FAILED (BusinessRuleError: Partial closes) | 3 PASSED |
| RR2-2 | 0 (docs only) | N/A | N/A |
| RR3-1 | 1 (integration) | 1 FAILED (gain=1860 surfaced wash-sale adjustment; test fixed) | 1 PASSED |

### Commands run

```
uv run pytest tests/integration/test_tax_service_integration.py -x --tb=short -v  # Red → 1 FAILED (gain mismatch from wash_sale_adjustment)
uv run pytest tests/integration/test_tax_service_integration.py -x --tb=short -v  # Green → 9 passed
uv run pytest tests/ -x --tb=short -q  # Full regression → 3136 passed, 23 skipped
uv run pyright packages/  # 0 errors
uv run ruff check packages/  # All checks passed
uv run python tools/validate_codebase.py --scope meu  # 8/8 PASS, A3 evidence present
```

### Updated Test Count

| Test File | Count | Scope |
|-----------|-------|-------|
| test_lot_selector.py | 38 | 8 cost basis methods, IBKR 4-tier priority |
| test_tax_service.py | 36 | 16 original + 12 F1–F4 + 5 R1/R2 + 3 RR2-1 split-lot |
| test_gains_calculator.py | 10 | RealizedGainResult, ST/LT, wash sale |
| test_tax_service_integration.py | 9 | Real SQLite round-trip + partial-close persistence |

## Key Design Decisions

1. **IBKR 4-tier priority**: MAX_* methods sort lots by per-share gain/loss magnitude, requiring `sale_price` parameter
2. **IRS 366-day boundary**: `holding_period_days >= 366` = long-term classification
3. **Wash sale formula**: `adjusted_basis = cost_basis + wash_sale_adjustment`
4. **Proportional gain scaling**: `simulate_impact` scales gains by `qty / lot.quantity` for partial fills
5. **Result types**: `SimulationResult` and `LotDetail` are frozen dataclasses exported from `tax_service.py`
6. **Per-lot cost basis override**: `TaxLot.cost_basis_method` (Optional) — None = use TaxProfile default
7. **TaxProfile rate fallback**: `simulate_impact` prefers TaxProfile rates, falls back to explicit params

## Next Steps

- Trigger `/execution-critical-review` re-review for final MEU approval
- Phase 3C: Wash sale detection (MEU-127)
- Phase 3D: Tax estimation and quarterly payments
- API endpoint wiring for `/api/v1/tax/simulate` (MEU-148)
