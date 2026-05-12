---
project: "2026-05-11-tax-foundation-entities"
source: "docs/execution/plans/2026-05-11-tax-foundation-entities/implementation-plan.md"
meus: ["MEU-123", "MEU-124"]
status: "complete"
template_version: "2.0"
---

# Task — Tax Foundation Entities

> **Project:** `2026-05-11-tax-foundation-entities`
> **Type:** Domain + Infrastructure
> **Estimate:** 9 files modified/created

## Task Table

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| | **MEU-123 TDD Cycle: TaxLot + CostBasisMethod** | | | | |
| 1 | Write unit tests: `test_tax_enums.py` (CostBasisMethod 8-value membership, str coercion, invalid value rejection) + `test_tax_entities.py` (TaxLot construction, 11 stored fields, `holding_period_days` computation, `is_long_term` 365/366 boundary) | coder | 2 new test files | `uv run pytest tests/unit/test_tax_enums.py tests/unit/test_tax_entities.py -x --tb=short -v *> C:\Temp\zorivest\pytest-tax-unit.txt; Get-Content C:\Temp\zorivest\pytest-tax-unit.txt \| Select-Object -Last 40` — expect RED (ImportError: no enums/entities yet) | `[x]` |
| 2 | Implement `CostBasisMethod` enum (8 values) in `enums.py` + `TaxLot` dataclass (11 stored fields + 2 computed properties) in `entities.py` | coder | Enum + entity classes | `uv run pytest tests/unit/test_tax_enums.py tests/unit/test_tax_entities.py -x --tb=short -v *> C:\Temp\zorivest\pytest-tax-unit.txt; Get-Content C:\Temp\zorivest\pytest-tax-unit.txt \| Select-Object -Last 40` — expect GREEN for MEU-123 tests | `[x]` |
| | **MEU-124 TDD Cycle: TaxProfile + FilingStatus + WashSaleMatchingMethod** | | | | |
| 3 | Write unit tests: `test_tax_enums.py` (FilingStatus 4 values, WashSaleMatchingMethod 2 values) + `test_tax_entities.py` (TaxProfile 14-field construction, default values for boolean flags) | coder | Test methods appended to existing files | `uv run pytest tests/unit/test_tax_enums.py tests/unit/test_tax_entities.py -x --tb=short -v *> C:\Temp\zorivest\pytest-tax-unit.txt; Get-Content C:\Temp\zorivest\pytest-tax-unit.txt \| Select-Object -Last 40` — expect RED (new tests fail) | `[x]` |
| 4 | Implement `FilingStatus` enum (4 values), `WashSaleMatchingMethod` enum (2 values) in `enums.py` + `TaxProfile` dataclass in `entities.py` | coder | Enum + entity classes | `uv run pytest tests/unit/test_tax_enums.py tests/unit/test_tax_entities.py -x --tb=short -v *> C:\Temp\zorivest\pytest-tax-unit.txt; Get-Content C:\Temp\zorivest\pytest-tax-unit.txt \| Select-Object -Last 40` — expect GREEN (all unit tests pass) | `[x]` |
| | **Infrastructure TDD Cycle: Repos + Models + Stubs** | | | | |
| 5 | Add `TaxLotRepository` + `TaxProfileRepository` protocols to `ports.py`; extend `UnitOfWork` with `tax_lots` and `tax_profiles` attributes | coder | 2 new Protocol classes + UoW extension | `uv run pyright packages/core/ *> C:\Temp\zorivest\pyright.txt; Get-Content C:\Temp\zorivest\pyright.txt \| Select-Object -Last 10` | `[x]` |
| 6 | Write integration tests: `test_tax_repo_integration.py` (CRUD for TaxLot + TaxProfile repos against in-memory SQLite) | coder | 1 new test file | `uv run pytest tests/integration/test_tax_repo_integration.py -x --tb=short -v *> C:\Temp\zorivest\pytest-tax-integ.txt; Get-Content C:\Temp\zorivest\pytest-tax-integ.txt \| Select-Object -Last 40` — expect RED (no models/repos yet) | `[x]` |
| 7 | Implement `TaxLotModel` + `TaxProfileModel` SQLAlchemy models in `models.py` (11 stored columns for TaxLot — no computed columns; all 14 columns for TaxProfile) | coder | 2 new SQLAlchemy models | `uv run pyright packages/infrastructure/ *> C:\Temp\zorivest\pyright.txt; Get-Content C:\Temp\zorivest\pyright.txt \| Select-Object -Last 10` | `[x]` |
| 8 | Implement `SqlTaxLotRepository` + `SqlTaxProfileRepository` in `tax_repository.py` | coder | 2 new repository implementations | `uv run pyright packages/infrastructure/ *> C:\Temp\zorivest\pyright.txt; Get-Content C:\Temp\zorivest\pyright.txt \| Select-Object -Last 10` | `[x]` |
| 9 | Implement `InMemoryTaxLotRepository` + `InMemoryTaxProfileRepository` in `stubs.py` | coder | 2 new stub implementations | N/A — InMemory stubs retired per MEU-90a | `[B]` |
| 10 | Wire `tax_lots` + `tax_profiles` repos into `SqlAlchemyUnitOfWork` | coder | UoW wiring | `uv run pytest tests/integration/test_tax_repo_integration.py -x --tb=short -v *> C:\Temp\zorivest\pytest-tax-integ.txt; Get-Content C:\Temp\zorivest\pytest-tax-integ.txt \| Select-Object -Last 40` — expect GREEN | `[x]` |
| 11 | Full regression: ensure no regressions in existing tests | tester | All existing tests still pass (3036 passed, 0 failed) | `uv run pytest tests/ -x --tb=short *> C:\Temp\zorivest\pytest.txt; Get-Content C:\Temp\zorivest\pytest.txt \| Select-Object -Last 40` | `[x]` |
| | **🔄 Re-Anchor Gate** | | | | |
| 12 | 🔄 `view_file` this `task.md`. Count all `[ ]` rows remaining and list them. If any implementation rows above are still `[ ]`, go back and complete them before proceeding. | coder | Console output confirming 0 unchecked implementation rows | `Select-String '\[ \]' docs/execution/plans/2026-05-11-tax-foundation-entities/task.md` | `[x]` |
| | **Post-Implementation** | | | | |
| 13 | Audit `docs/BUILD_PLAN.md` — update MEU-123, MEU-124 status ⬜→✅ | orchestrator | No refs found (MEUs not in BUILD_PLAN.md — they are in build-priority-matrix refs only) | `rg "MEU-123" docs/BUILD_PLAN.md; rg "MEU-124" docs/BUILD_PLAN.md` (returns 0 — clean) | `[x]` |
| 14 | Register MEU-123 and MEU-124 in `.agent/context/meu-registry.md` | orchestrator | Phase 3A section added with 2 rows ✅ 2026-05-11 | `rg -n "MEU-123" .agent/context/meu-registry.md; rg -n "MEU-124" .agent/context/meu-registry.md` (expect 2 rows) | `[x]` |
| 15 | Run verification plan (pyright + ruff + full regression + anti-placeholder) | tester | All 8 blocking checks passed (34.14s) | `uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate.txt; Get-Content C:\Temp\zorivest\validate.txt \| Select-Object -Last 50` | `[x]` |
| 16 | Save session state to pomera_notes | orchestrator | Saved as note ID 1097 | MCP: `pomera_notes(action="search", search_term="Zorivest-tax-foundation*")` returns ≥1 result | `[x]` |
| 17 | Create handoff | reviewer | `.agent/context/handoffs/2026-05-11-tax-foundation-entities-handoff.md` | `Test-Path .agent/context/handoffs/2026-05-11-tax-foundation-entities-handoff.md` | `[x]` |
| 18 | Create reflection | orchestrator | `docs/execution/reflections/2026-05-11-tax-foundation-entities-reflection.md` | `Test-Path docs/execution/reflections/2026-05-11-tax-foundation-entities-reflection.md` | `[x]` |
| 19 | Append metrics row | orchestrator | Row appended to `docs/execution/metrics.md` | `Get-Content docs/execution/metrics.md \| Select-Object -Last 3` | `[x]` |


### Status Legend

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Not started |
| `[/]` | In progress |
| `[x]` | Complete |
| `[B]` | Blocked (must link follow-up) |
