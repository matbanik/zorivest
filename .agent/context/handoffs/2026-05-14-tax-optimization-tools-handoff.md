---
project: "2026-05-14-tax-optimization-tools"
meus: ["MEU-137", "MEU-138", "MEU-139", "MEU-140", "MEU-141", "MEU-142"]
status: "complete"
verbosity: "standard"
---

<!-- CACHE BOUNDARY -->

# Handoff — Tax Optimization Tools (Phase 3C)

> **Date:** 2026-05-14
> **MEUs:** 137–142 (6 of 6 complete)
> **Status:** ✅ All implementation and verification complete

## Summary

Implemented all 6 Phase 3C Tax Optimization domain modules using strict TDD (Red→Green) with 100% AC coverage. All modules are pure domain functions with no I/O, consistent with the Zorivest architecture.

## Changed Files

### New Production Modules (6)

```diff
+ packages/core/src/zorivest_core/domain/tax/tax_simulator.py        # MEU-137
+ packages/core/src/zorivest_core/domain/tax/harvest_scanner.py       # MEU-138
+ packages/core/src/zorivest_core/domain/tax/replacement_suggestions.py # MEU-139
+ packages/core/src/zorivest_core/domain/tax/lot_matcher.py           # MEU-140
+ packages/core/src/zorivest_core/domain/tax/lot_reassignment.py      # MEU-141
+ packages/core/src/zorivest_core/domain/tax/rate_comparison.py       # MEU-142
```

### New Test Files (6)

```diff
+ tests/unit/domain/tax/test_tax_simulator.py           # 15 tests
+ tests/unit/domain/tax/test_harvest_scanner.py          # 10 tests
+ tests/unit/domain/tax/test_replacement_suggestions.py  # 13 tests
+ tests/unit/domain/tax/test_lot_matcher.py              # 10 tests (prior session)
+ tests/unit/domain/tax/test_lot_reassignment.py         # 12 tests
+ tests/unit/domain/tax/test_rate_comparison.py          # 11 tests (prior session)
```

### Modified Files (1)

```diff
~ packages/core/src/zorivest_core/domain/tax/__init__.py  # Added 20 new exports
```

## Evidence Bundle

| Gate | Result |
|------|--------|
| pytest (tax domain) | 146 passed, 0 failed |
| pytest (full suite) | 3545 passed, 23 skipped, 0 failed |
| pyright (packages/) | 0 errors, 0 warnings |
| ruff (packages/) | All checks passed |
| anti-placeholder | Clean |
| MEU gate (validate_codebase.py) | All 8/8 blocking checks passed |

## Design Decisions

1. **Pure domain pattern:** All modules are pure functions — no I/O, no repositories, no mocks needed. Consistent with existing tax domain modules.
2. **Formula consistency:** ST gains use `compute_marginal_rate × gain`; LT gains use `compute_capital_gains_tax()`; state tax via `compute_combined_rate()`. Same pattern across tax_simulator and rate_comparison.
3. **ETF replacement table:** Static hardcoded table with 10 categories and ~40 tickers covering Vanguard, iShares, Schwab, SPDR families. Bidirectional lookup (VOO→IVV and IVV→VOO).
4. **Settlement window:** Default T+1 per SEC rule (effective May 2024). Configurable via `settlement_days` parameter for future broker flexibility.

## Registry Updates

- `meu-registry.md`: MEU-137 through MEU-142 all marked ✅ 2026-05-14

## Remaining Work

- Tasks 23, 25, 26 in task.md are session-end administrative tasks (pomera save, reflection, metrics) — deferred to session close.
- Phase 3C is now **fully complete** (6/6 MEUs). Next up: Phase 3E (Reports & Full-Stack Wiring) or MEU-133/134/135/136 (wash sale extensions).
