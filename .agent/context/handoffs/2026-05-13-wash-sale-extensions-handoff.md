---
project: "2026-05-13-wash-sale-extensions"
meus: ["MEU-133", "MEU-134", "MEU-135", "MEU-136"]
status: "implementation_complete"
verbosity: "standard"
date: "2026-05-13"
---

<!-- CACHE BOUNDARY -->

# Handoff — Wash Sale Extensions (MEU-133–136)

> **Status:** Implementation complete — all 20 implementation tasks `[x]`  
> **MEU Gate:** All 8 blocking checks passed (pyright, ruff, pytest, tsc, eslint, vitest, anti-placeholder, anti-deferral)

## Summary

Hardened the wash sale engine with four extensions:

1. **MEU-134 (DRIP Foundation):** `AcquisitionSource` enum (7 members), nullable `acquisition_source` field on `TaxLot` + `TaxLotModel`, `is_drip_triggered` on `WashSaleMatch`, `include_drip` parameter on `detect_wash_sales`, full persistence round-trip
2. **MEU-133 (Options-to-Stock):** `WashSaleMatchingMethod` enum, `_is_substantially_identical()` helper using `parse_option_symbol()`, CONSERVATIVE/AGGRESSIVE modes on `detect_wash_sales`  
3. **MEU-135 (Rebalance/Spousal Warnings):** `WashSaleWarning` frozen dataclass, `WarningType` enum (REBALANCE_CONFLICT, SPOUSAL_CONFLICT), `check_conflicts()` pure function, `TaxService.check_wash_sale_conflicts()` service method
4. **MEU-136 (Pre-Trade Alerts):** `SimulationResult` enriched with `wash_sale_warnings` list + `wait_days` int, `simulate_impact()` calls `check_conflicts()` internally, injectable `now` parameter for testability

## Changed Files

```diff
# Domain Layer
+ packages/core/src/zorivest_core/domain/tax/wash_sale_warnings.py  (NEW: WarningType, WashSaleWarning, check_conflicts)
~ packages/core/src/zorivest_core/domain/enums.py                  (AcquisitionSource enum added)
~ packages/core/src/zorivest_core/domain/entities.py               (TaxLot.acquisition_source: AcquisitionSource | None)
~ packages/core/src/zorivest_core/domain/tax/wash_sale_detector.py  (include_drip, wash_sale_method params, is_drip_triggered)

# Service Layer
~ packages/core/src/zorivest_core/services/tax_service.py          (SimulationResult fields, check_wash_sale_conflicts(), wiring)

# Infrastructure
~ packages/infrastructure/src/zorivest_infra/database/models.py    (TaxLotModel.acquisition_source column)
~ packages/infrastructure/src/zorivest_infra/database/tax_repository.py  (mapper updates)

# Tests
+ tests/unit/domain/tax/test_wash_sale_warnings.py     (NEW: 11 tests)
+ tests/unit/services/test_pre_trade_alerts.py          (NEW: 5 tests)
~ tests/unit/domain/tax/test_wash_sale_detector.py      (DRIP + options tests added)
~ tests/unit/test_tax_entities.py                       (field count sentinel 13→14)
~ tests/integration/test_tax_repo_integration.py        (AcquisitionSource round-trip tests)
```

## Evidence

### Test Results
- Unit (domain/tax + services): **107 passed**, 0 failed
- Integration: **257 passed**, 0 failed
- Pre-trade alerts: **5 passed**, 0 failed
- MEU gate: **All 8 blocking checks PASS** (32.9s)

### Anti-Placeholder Scan
```
rg "TODO|FIXME|NotImplementedError" packages/core/src/zorivest_core/domain/tax/ packages/core/src/zorivest_core/services/tax_service.py
→ 0 matches
```

## Design Decisions

| Decision | Choice | Source |
|----------|--------|--------|
| `acquisition_source` nullable | `None` = standard PURCHASE | Spec — backward compat |
| DRIP detection default | `include_drip=True` | Spec — TaxProfile default |
| Options matching default | `CONSERVATIVE` mode | Human-approved — IRS Pub 550 |
| SimulationResult defaults | `wash_sale_warnings=[]`, `wait_days=0` | Spec — backward compat |
| `now` injectable | Optional param on `simulate_impact()` | Research — testability pattern |

## Next Steps

- Trigger Codex validation for MEU-133–136
- After validation: update meu-registry.md status for MEU-133–136
- Phase 3B Session 3 planning (MEU-137+)
