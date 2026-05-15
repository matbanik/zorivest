---
date: "2026-05-13"
project: "wash-sale-engine"
meu: "MEU-130, MEU-131, MEU-132"
status: "complete"
action_required: "VALIDATE_AND_APPROVE"
template_version: "2.1"
verbosity: "standard"
plan_source: "docs/execution/plans/2026-05-13-wash-sale-engine/implementation-plan.md"
build_plan_section: "bp57-59"
agent: "antigravity"
reviewer: "codex"
predecessor: "2026-05-12-tax-logic-expansion-handoff.md"
---

# Handoff: 2026-05-13-wash-sale-engine-handoff

> **Status**: `complete`
> **Action Required**: `VALIDATE_AND_APPROVE`

---

## Scope

**MEU**: MEU-130/131/132 — Phase 3B Wash Sale Engine (detection, chain tracking, cross-account aggregation)
**Build Plan Section**: build-priority-matrix §3B (items 57–59)
**Predecessor**: [2026-05-12-tax-logic-expansion-handoff.md](2026-05-12-tax-logic-expansion-handoff.md)

---

## Acceptance Criteria

### MEU-130: Wash Sale Detection

| AC | Description | Source | Test(s) | Status |
|----|-------------|--------|---------|--------|
| AC-130.1 | WashSaleStatus enum: DISALLOWED, ABSORBED, RELEASED, DESTROYED | Spec | test_wash_sale.py::TestWashSaleStatus | ✅ |
| AC-130.2 | WashSaleEventType enum: 5 event types | Spec | test_wash_sale.py::TestWashSaleEventType | ✅ |
| AC-130.3 | WashSaleChain mutable entity with required fields | Spec | test_wash_sale.py::TestWashSaleChain | ✅ |
| AC-130.4 | WashSaleEntry frozen entity with account_id | Spec | test_wash_sale.py::TestWashSaleEntry | ✅ |
| AC-130.5 | detect_wash_sales() 30-day before + after window | Research-backed (IRS Pub 550) | test_wash_sale_detector.py::TestDetectWashSalesWindow | ✅ |
| AC-130.6 | Same ticker matching, different ticker exclusion | Spec | test_wash_sale_detector.py::TestDetectWashSalesTickerMatch | ✅ |
| AC-130.7 | Partial quantity proportional disallowance | Research-backed (IRS Pub 550) | test_wash_sale_detector.py::TestDetectWashSalesPartial | ✅ |
| AC-130.8 | WashSaleChainRepository protocol on ports.py | Local Canon | test_wash_sale_repository.py::TestWashSaleChainRepositoryProtocol | ✅ |
| AC-130.9 | WashSaleChainModel + WashSaleEntryModel (2 tables) | Spec | test_models.py (44 tables), test_wash_sale_repository.py::TestWashSaleModels | ✅ |
| AC-130.10 | SqlWashSaleChainRepository CRUD | Local Canon | test_wash_sale_repository.py::TestSqlWashSaleChainRepository | ✅ |
| AC-130.11 | UoW wiring + clean exports | Local Canon | test_wash_sale_repository.py::test_uow_has_wash_sale_chains_attribute | ✅ |

### MEU-131: Chain Tracking

| AC | Description | Source | Test(s) | Status |
|----|-------------|--------|---------|--------|
| AC-131.1 | WashSaleChainManager class with 6 public methods | Spec | test_wash_sale_chain_manager.py::TestChainManagerAPI | ✅ |
| AC-131.2 | start_chain() creates DISALLOWED chain + LOSS_DISALLOWED entry | Spec | test_wash_sale_chain_manager.py::TestStartChain | ✅ |
| AC-131.3 | absorb_loss() adjusts replacement lot basis | Spec | test_wash_sale_chain_manager.py::TestAbsorbLoss | ✅ |
| AC-131.4 | Holding period tacking: replacement inherits loss_open_date | Research-backed (IRS Pub 550) | test_wash_sale_chain_manager.py::TestHoldingPeriodTacking | ✅ |
| AC-131.5 | release_chain() → RELEASED status | Spec | test_wash_sale_chain_manager.py::TestReleaseChain | ✅ |
| AC-131.6 | continue_chain() adds CONTINUED entry | Spec | test_wash_sale_chain_manager.py::TestContinueChain | ✅ |
| AC-131.7 | get_trapped_losses() returns ABSORBED chains | Spec | test_wash_sale_chain_manager.py::TestGetTrappedLosses | ✅ |
| AC-131.8 | TaxService.detect_and_apply_wash_sales() + get_trapped_losses() | Local Canon | test_tax_service_wash_sale.py::TestTaxServiceWashSaleMethod | ✅ |

### MEU-132: Cross-Account Aggregation

| AC | Description | Source | Test(s) | Status |
|----|-------------|--------|---------|--------|
| AC-132.1 | Cross-account detection matches across accounts | Research-backed (IRS Pub 550) | test_wash_sale_cross_account.py::TestMultiAccountDetection | ✅ |
| AC-132.2 | IRA permanent loss destruction (DESTROYED status) | Research-backed (IRS Pub 550) | test_wash_sale_cross_account.py::TestIraLossDestruction | ✅ |
| AC-132.3 | destroy_chain() prevents absorb | Spec | test_wash_sale_cross_account.py::test_cannot_absorb_after_destroy | ✅ |
| AC-132.4 | Taxable-to-taxable = DISALLOWED not DESTROYED | Spec | test_wash_sale_cross_account.py::test_taxable_to_taxable | ✅ |
| AC-132.5 | TaxService.scan_cross_account_wash_sales() | Local Canon | test_tax_service_wash_sale.py::TestTaxServiceCrossAccountMethod | ✅ |
| AC-132.6 | Entry provenance: account_id on every WashSaleEntry | Spec | test_wash_sale_cross_account.py::TestEntryAccountProvenance | ✅ |
| AC-132.7 | Spousal account toggle (include_spousal parameter) | Spec | test_tax_service_wash_sale.py::test_scan_method_accepts_spousal_param | ✅ |

<!-- CACHE BOUNDARY -->
<!-- Content above this line is stable across revision passes (KV cache prefix). -->
<!-- Content below this line changes between passes (evidence, results, corrections). -->

---

## Evidence

### FAIL_TO_PASS

Tests were written first (Red phase) and confirmed failing before implementation. All 50 wash sale tests transition from FAIL → PASS.

| Phase | Red Output | Green Output |
|-------|-----------|-------------|
| MEU-130 (27 tests) | All import/attribute errors | 27 passed |
| MEU-131 (13 tests) | All import/attribute errors | 13 passed |
| MEU-132 (9 tests) | All import/attribute errors | 9 passed |
| Spousal toggle (1 test) | N/A (added with implementation) | 1 passed |

### Commands Executed

| Command | Exit Code | Key Output |
|---------|-----------|------------|
| `uv run pytest tests/unit/ -x --tb=short -q` | 0 | 2982 passed, 1 skipped |
| `uv run pyright packages/core/ packages/infrastructure/` | 0 | 0 errors |
| `uv run ruff check packages/core/ packages/infrastructure/` | 0 | All checks passed |
| `uv run python tools/validate_codebase.py --scope meu` | 0 | 8/8 blocking checks passed (35.09s) |

### Quality Gate Results

```
pyright: 0 errors, 0 warnings
ruff: 0 violations
pytest: 2982 passed, 1 skipped
anti-placeholder: 0 matches
anti-deferral: 0 matches
```

---

## Changed Files

| File | Action | Summary |
|------|--------|---------|
| `packages/core/src/zorivest_core/domain/enums.py` | modified | Added WashSaleStatus (4 members) + WashSaleEventType (5 members) |
| `packages/core/src/zorivest_core/domain/tax/wash_sale.py` | new | WashSaleChain (mutable) + WashSaleEntry (frozen) entities |
| `packages/core/src/zorivest_core/domain/tax/wash_sale_detector.py` | new | detect_wash_sales() pure function + WashSaleMatch result type |
| `packages/core/src/zorivest_core/domain/tax/wash_sale_chain_manager.py` | new | WashSaleChainManager state machine (6 methods) |
| `packages/core/src/zorivest_core/domain/tax/__init__.py` | modified | Exports WashSaleChain, WashSaleEntry, WashSaleChainManager |
| `packages/core/src/zorivest_core/application/ports.py` | modified | WashSaleChainRepository protocol + UoW.wash_sale_chains |
| `packages/core/src/zorivest_core/services/tax_service.py` | modified | 4 new methods: detect_and_apply_wash_sales, get_trapped_losses, scan_cross_account_wash_sales, _get_spousal_account_ids |
| `packages/infrastructure/src/zorivest_infra/database/wash_sale_models.py` | new | WashSaleChainModel + WashSaleEntryModel (2 tables) |
| `packages/infrastructure/src/zorivest_infra/database/wash_sale_repository.py` | new | SqlWashSaleChainRepository (full CRUD) |
| `packages/infrastructure/src/zorivest_infra/database/unit_of_work.py` | modified | wash_sale_chains wired to real repo |
| `tests/unit/domain/tax/test_wash_sale.py` | new | 6 entity/enum tests |
| `tests/unit/domain/tax/test_wash_sale_detector.py` | new | 12 detection algorithm tests |
| `tests/unit/domain/tax/test_wash_sale_chain_manager.py` | new | 11 chain state machine tests |
| `tests/unit/domain/tax/test_wash_sale_cross_account.py` | new | 9 cross-account + IRA tests |
| `tests/unit/services/test_tax_service_wash_sale.py` | new | 4 TaxService integration tests |
| `tests/unit/infrastructure/test_wash_sale_repository.py` | new | 7 repository protocol + CRUD tests |
| `tests/unit/test_models.py` | modified | Table count 42→44 |
| `tests/unit/test_market_data_models.py` | modified | Table count 42→44 |
| `tests/unit/test_ports.py` | modified | Protocol count 22→23, class count 23→24 |

---

## Codex Validation Report

_Left blank for reviewer agent._

---

## Deferred Items

| Item | Reason | Follow-up |
|------|--------|-----------|
| K401 permanent loss destruction (Task 31) | blocked — IRS Pub 550 does not explicitly name 401(k); requires human approval | Blocked in task.md as `[B]` |

---

## History

| Event | Date | Agent | Detail |
|-------|------|-------|--------|
| Created | 2026-05-13 | antigravity | Initial handoff for MEU-130/131/132 |
| Submitted for review | 2026-05-13 | antigravity | All 50 wash sale tests GREEN, MEU gate passed |
