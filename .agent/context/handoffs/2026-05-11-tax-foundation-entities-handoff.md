---
date: "2026-05-11"
project: "tax-foundation-entities"
meu: "MEU-123, MEU-124"
status: "draft"
action_required: "VALIDATE_AND_APPROVE"
template_version: "2.1"
verbosity: "standard"
plan_source: "docs/execution/plans/2026-05-11-tax-foundation-entities/implementation-plan.md"
build_plan_section: "04f-api-tax §3A"
agent: "Antigravity"
reviewer: "Codex"
predecessor: "none"
---

# Handoff: 2026-05-11-tax-foundation-entities

> **Status**: `draft`
> **Action Required**: `VALIDATE_AND_APPROVE`

---

## Scope

**MEU**: MEU-123 (TaxLot + CostBasisMethod) + MEU-124 (TaxProfile + FilingStatus + WashSaleMatchingMethod)
**Build Plan Section**: 04f-api-tax §3A — Tax Foundation Entities
**Predecessor**: none

---

## Acceptance Criteria

| AC | Description | Source | Test(s) | Status |
|----|-------------|--------|---------|--------|
| AC-123.1 | CostBasisMethod enum has 8 members (FIFO, LIFO, HIFO, SPEC_ID, MAX_LT_GAIN, MAX_LT_LOSS, MAX_ST_GAIN, MAX_ST_LOSS) | Spec: domain-model-reference.md L395-397 | test_tax_enums.py::TestCostBasisMethod | ✅ |
| AC-123.2 | TaxLot dataclass has 11 stored fields + 2 computed properties | Spec: 04f-api-tax.md | test_tax_entities.py::TestTaxLot | ✅ |
| AC-123.3 | TaxLot.holding_period_days computes correctly, is_long_term uses 365-day boundary | Spec: 04f-api-tax.md | test_tax_entities.py::TestTaxLotComputedProperties | ✅ |
| AC-123.4 | TaxLotRepository protocol with get/save/update/delete/list_for_account/list_filtered/count_filtered | Spec: implementation-plan.md | test_ports.py::TestProtocolConvention | ✅ |
| AC-123.5 | SqlTaxLotRepository CRUD + filtering works against SQLite | Spec: implementation-plan.md | test_tax_repo_integration.py::TestTaxLotCRUD, TestTaxLotFiltering | ✅ |
| AC-124.1 | FilingStatus enum has 4 members, WashSaleMatchingMethod enum has 2 members | Spec: 04f-api-tax.md | test_tax_enums.py::TestFilingStatus, TestWashSaleMatchingMethod | ✅ |
| AC-124.2 | TaxProfile dataclass has 15 fields with correct defaults | Spec: 04f-api-tax.md | test_tax_entities.py::TestTaxProfile | ✅ |
| AC-124.3 | TaxProfileRepository protocol with get/save/update/get_for_year | Spec: implementation-plan.md | test_ports.py::TestProtocolConvention | ✅ |
| AC-124.4 | SqlTaxProfileRepository CRUD + year lookup works against SQLite | Spec: implementation-plan.md | test_tax_repo_integration.py::TestTaxProfileCRUD | ✅ |
| AC-UoW | UnitOfWork extended with tax_lots + tax_profiles attributes, wired in SqlAlchemyUnitOfWork | Spec: implementation-plan.md | test_tax_repo_integration.py::TestUoWTaxWiring (2 tests) | ✅ |

<!-- CACHE BOUNDARY -->
<!-- Content above this line is stable across revision passes (KV cache prefix). -->
<!-- Content below this line changes between passes (evidence, results, corrections). -->

---

## Evidence

### FAIL_TO_PASS

| Test | Red Output (snippet) | Green Output | File:Line |
|------|---------------------|--------------|-----------|
| test_tax_enums.py (15 tests) | ImportError: cannot import name 'CostBasisMethod' | 15 passed | tests/unit/test_tax_enums.py |
| test_tax_entities.py (17 tests) | ImportError: cannot import name 'TaxLot' | 17 passed | tests/unit/test_tax_entities.py |
| test_tax_repo_integration.py (16 tests) | ImportError: cannot import name 'TaxLotModel' | 16 passed | tests/integration/test_tax_repo_integration.py |

### Commands Executed

| Command | Exit Code | Key Output |
|---------|-----------|------------|
| `uv run pytest tests/unit/test_tax_enums.py tests/unit/test_tax_entities.py -x --tb=short -v` | 0 | 32 passed |
| `uv run pytest tests/integration/test_tax_repo_integration.py -x --tb=short -v` | 0 | 16 passed |
| `uv run pytest tests/ -x --tb=short` | 0 | 3036 passed, 23 skipped |
| `uv run pyright packages/` | 0 | 0 errors, 0 warnings |
| `uv run python tools/validate_codebase.py --scope meu` | 0 | All 8 blocking checks passed |

### Quality Gate Results

```
pyright: 0 errors, 0 warnings
ruff: 0 violations
pytest: 3036 passed, 0 failed, 23 skipped
anti-placeholder: 0 matches
anti-deferral: 0 matches
```

---

## Changed Files

| File | Action | Lines | Summary |
|------|--------|-------|---------|
| packages/core/.../domain/enums.py | modified | +40 | Added CostBasisMethod (8), FilingStatus (4), WashSaleMatchingMethod (2) enums |
| packages/core/.../domain/entities.py | modified | +65 | Added TaxLot (11 stored + 2 computed) and TaxProfile (15 fields) dataclasses |
| packages/core/.../application/ports.py | modified | +80 | Added TaxLotRepository and TaxProfileRepository protocols, extended UnitOfWork |
| packages/infrastructure/.../database/models.py | modified | +60 | Added TaxLotModel and TaxProfileModel with Numeric(15,6) financials |
| packages/infrastructure/.../database/tax_repository.py | new | 240 | SqlTaxLotRepository + SqlTaxProfileRepository with full CRUD + filtering |
| packages/infrastructure/.../database/unit_of_work.py | modified | +6 | Wired tax_lots and tax_profiles repos into SqlAlchemyUnitOfWork |
| tests/unit/test_tax_enums.py | new | 115 | 15 unit tests for 3 tax enums |
| tests/unit/test_tax_entities.py | new | 155 | 17 unit tests for TaxLot + TaxProfile entities |
| tests/integration/test_tax_repo_integration.py | new | 230 | 16 integration tests for CRUD + filtering |
| tests/unit/test_entities.py | modified | +2 | Updated expected class set (8→10) |
| tests/unit/test_models.py | modified | +5 | Updated expected table set (40→42) |
| tests/unit/test_market_data_models.py | modified | +2 | Updated table count assertion (40→42) |
| tests/unit/test_ports.py | modified | +5 | Updated protocol counts (20→22, 21→23) |

---

## Codex Validation Report

_Left blank for reviewer agent._

### Recheck Protocol

1. Read Scope + AC table
2. Verify each AC against Evidence section (file:line, not memory)
3. Run all Commands Executed and compare output
4. Run Quality Gate commands independently
5. Record findings below

### Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|

### Verdict



---

## Deferred Items

| Item | Reason | Follow-up |
|------|--------|-----------|
| Task 9: InMemory stubs | InMemory repo stubs retired per MEU-90a (see `packages/api/src/zorivest_api/stubs.py` and `meu-registry.md` MEU-90a entry) | Blocked — plan/task updated to reflect retirement rationale |

---

## History

| Event | Date | Agent | Detail |
|-------|------|-------|--------|
| Created | 2026-05-11 | Antigravity | Initial handoff |
| Submitted for review | 2026-05-11 | Antigravity | Sent to Codex |
