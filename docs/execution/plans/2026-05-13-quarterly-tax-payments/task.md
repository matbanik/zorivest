---
project: "2026-05-13-quarterly-tax-payments"
source: "docs/execution/plans/2026-05-13-quarterly-tax-payments/implementation-plan.md"
meus: ["MEU-143", "MEU-144", "MEU-145", "MEU-146", "MEU-147"]
status: "corrections_applied"
template_version: "2.0"
---

# Task — Quarterly Tax Payments & Tax Brackets

> **Project:** `2026-05-13-quarterly-tax-payments`
> **Type:** Domain
> **Estimate:** 9 files changed (4 new, 5 modified)

## Task Table

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| | **MEU-146: Marginal Tax Rate Calculator** | | | | |
| 1 | Write FIC for MEU-146 (6 ACs: brackets.py) | coder | FIC in test file docstring | Visual review | `[x]` |
| 2 | Write `tests/unit/test_tax_brackets.py` — RED phase (~20 tests: marginal rate, effective rate, tax liability, capital gains, 2025/2026, all filing statuses, edge cases) | coder | All tests fail (no implementation) | `uv run pytest tests/unit/test_tax_brackets.py -v *> C:\Temp\zorivest\brackets-red.txt; Get-Content C:\Temp\zorivest\brackets-red.txt \| Select-Object -Last 40` | `[x]` |
| 3 | Implement `packages/core/src/zorivest_core/domain/tax/brackets.py` — GREEN phase (bracket tables, compute_marginal_rate, compute_effective_rate, compute_tax_liability, compute_capital_gains_tax) | coder | All tests pass | `uv run pytest tests/unit/test_tax_brackets.py -v *> C:\Temp\zorivest\brackets-green.txt; Get-Content C:\Temp\zorivest\brackets-green.txt \| Select-Object -Last 40` | `[x]` |
| 4 | Export new functions from `domain/tax/__init__.py` | coder | Clean import | `uv run pyright packages/core/ *> C:\Temp\zorivest\pyright-146.txt; Get-Content C:\Temp\zorivest\pyright-146.txt \| Select-Object -Last 20` | `[x]` |
| | **MEU-147: NIIT Threshold Alert** | | | | |
| 5 | Write FIC for MEU-147 (5 ACs: niit.py) | coder | FIC in test file docstring | Visual review | `[x]` |
| 6 | Write `tests/unit/test_tax_niit.py` — RED phase (~10 tests: all filing statuses, boundary cases, proximity alert, Decimal precision) | coder | All tests fail | `uv run pytest tests/unit/test_tax_niit.py -v *> C:\Temp\zorivest\niit-red.txt; Get-Content C:\Temp\zorivest\niit-red.txt \| Select-Object -Last 30` | `[x]` |
| 7 | Implement `packages/core/src/zorivest_core/domain/tax/niit.py` — GREEN phase | coder | All tests pass | `uv run pytest tests/unit/test_tax_niit.py -v *> C:\Temp\zorivest\niit-green.txt; Get-Content C:\Temp\zorivest\niit-green.txt \| Select-Object -Last 30` | `[x]` |
| 8 | Export NIIT functions from `domain/tax/__init__.py` | coder | Clean import | `uv run pyright packages/core/ *> C:\Temp\zorivest\pyright-147.txt; Get-Content C:\Temp\zorivest\pyright-147.txt \| Select-Object -Last 20` | `[x]` |
| | **MEU-143: QuarterlyEstimate Entity + Safe Harbor** | | | | |
| 9 | Write FIC for MEU-143 (6 ACs: entity + safe harbor) | coder | FIC in test file docstring | Visual review | `[x]` |
| 10 | Add `QuarterlyEstimate` dataclass to `entities.py` | coder | Entity with 9 fields per spec | `uv run pyright packages/core/ *> C:\Temp\zorivest\pyright-entity.txt; Get-Content C:\Temp\zorivest\pyright-entity.txt \| Select-Object -Last 20` | `[x]` |
| 11 | Add `QuarterlyEstimateRepository` protocol to `ports.py` + wire to `UnitOfWork` | coder | Port with get/save/update/list_for_year methods | `uv run pyright packages/core/ *> C:\Temp\zorivest\pyright-port.txt; Get-Content C:\Temp\zorivest\pyright-port.txt \| Select-Object -Last 20` | `[x]` |
| 12 | Write `tests/unit/test_tax_quarterly.py` — RED phase (~15 safe harbor tests: both methods, 110% threshold, MFS exception, recommend-lower logic) | coder | All tests fail | `uv run pytest tests/unit/test_tax_quarterly.py -v *> C:\Temp\zorivest\quarterly-red.txt; Get-Content C:\Temp\zorivest\quarterly-red.txt \| Select-Object -Last 40` | `[x]` |
| 13 | Implement safe harbor calculator in `domain/tax/quarterly.py` — GREEN phase | coder | All tests pass | `uv run pytest tests/unit/test_tax_quarterly.py -v *> C:\Temp\zorivest\quarterly-green.txt; Get-Content C:\Temp\zorivest\quarterly-green.txt \| Select-Object -Last 40` | `[x]` |
| | **MEU-144: Annualized Income Method** | | | | |
| 14 | Write FIC for MEU-144 (5 ACs: annualized income) | coder | FIC in test file docstring | Visual review | `[x]` |
| 15 | Add annualized income tests to `test_tax_quarterly.py` — RED phase (~12 tests: factors, cumulative, flooring, edge cases) | coder | All new tests fail | `uv run pytest tests/unit/test_tax_quarterly.py -v -k "annualized" *> C:\Temp\zorivest\annualized-red.txt; Get-Content C:\Temp\zorivest\annualized-red.txt \| Select-Object -Last 30` | `[x]` |
| 16 | Implement annualized income method in `domain/tax/quarterly.py` — GREEN phase | coder | All tests pass | `uv run pytest tests/unit/test_tax_quarterly.py -v *> C:\Temp\zorivest\annualized-green.txt; Get-Content C:\Temp\zorivest\annualized-green.txt \| Select-Object -Last 40` | `[x]` |
| | **MEU-145: Due Dates + Underpayment Penalty** | | | | |
| 17 | Write FIC for MEU-145 (7 ACs: due dates, penalty, service methods) | coder | FIC in test file docstring | Visual review | `[x]` |
| 18 | Add due date + penalty tests to `test_tax_quarterly.py` — RED phase (~15 tests: weekend shift, penalty math, YTD summary, boundary cases) | coder | All new tests fail | `uv run pytest tests/unit/test_tax_quarterly.py -v -k "due_date or penalty" *> C:\Temp\zorivest\penalty-red.txt; Get-Content C:\Temp\zorivest\penalty-red.txt \| Select-Object -Last 30` | `[x]` |
| 19 | Implement due date engine + penalty calculator in `domain/tax/quarterly.py` — GREEN phase; add penalty rate constants to `brackets.py` | coder | All tests pass | `uv run pytest tests/unit/test_tax_quarterly.py -v *> C:\Temp\zorivest\penalty-green.txt; Get-Content C:\Temp\zorivest\penalty-green.txt \| Select-Object -Last 40` | `[x]` |
| 20 | Add `TaxService.quarterly_estimate()` and `TaxService.record_payment()` methods | coder | `quarterly_estimate()` fully implemented with UoW orchestration; `record_payment()` is signature-only contract (validates inputs, raises `NotImplementedError` with MEU-148 link) | `uv run pytest tests/unit/test_tax_service.py -v -k "quarterly" *> C:\Temp\zorivest\svc-quarterly.txt; Get-Content C:\Temp\zorivest\svc-quarterly.txt \| Select-Object -Last 30` | `[B]` |
| 21 | Export all quarterly functions from `domain/tax/__init__.py` | coder | Clean imports | `uv run pyright packages/core/ *> C:\Temp\zorivest\pyright-final.txt; Get-Content C:\Temp\zorivest\pyright-final.txt \| Select-Object -Last 20` | `[x]` |
| | **🔄 Re-Anchor Gate** | | | | |
| 22 | 🔄 `view_file` this `task.md`. Count all `[ ]` rows remaining and list them. If any implementation rows above are still `[ ]`, go back and complete them before proceeding. | coder | Console output confirming 0 unchecked implementation rows | `rg "\[ \]" docs/execution/plans/2026-05-13-quarterly-tax-payments/task.md *> C:\Temp\zorivest\reanchor.txt; Get-Content C:\Temp\zorivest\reanchor.txt` | `[x]` |
| | **Post-Implementation** | | | | |
| 23 | Verify BUILD_PLAN.md MEU-143–147 status rows | orchestrator | 5 MEU rows with updated status | `rg -n "MEU-14[3-7]" docs/BUILD_PLAN.md *> C:\Temp\zorivest\build-plan-check.txt; Get-Content C:\Temp\zorivest\build-plan-check.txt` | `[x]` |
| 24 | Run full verification plan (pytest, pyright, ruff, anti-placeholder) | tester | All checks pass | See implementation-plan.md §Verification Plan | `[x]` |
| 25 | Run MEU gate | tester | MEU-scoped validation passes | `uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate.txt; Get-Content C:\Temp\zorivest\validate.txt \| Select-Object -Last 50` | `[x]` |
| 26 | Save session state to pomera_notes | orchestrator | `Memory/Session/Zorivest-quarterly-tax-2026-05-13` | MCP: `pomera_notes(action="search", search_term="Zorivest-quarterly*")` returns ≥1 result | `[x]` |
| 27 | Create handoff | reviewer | `.agent/context/handoffs/2026-05-13-quarterly-tax-payments-handoff.md` | `Test-Path .agent/context/handoffs/2026-05-13-quarterly-tax-payments-handoff.md *> C:\Temp\zorivest\handoff-check.txt; Get-Content C:\Temp\zorivest\handoff-check.txt` | `[x]` |
| 28 | Create reflection | orchestrator | `docs/execution/reflections/2026-05-13-quarterly-tax-payments-reflection.md` | `Test-Path docs/execution/reflections/2026-05-13-quarterly-tax-payments-reflection.md` | `[x]` |
| 29 | Append metrics row | orchestrator | Row appended to `docs/execution/metrics.md` | `Get-Content docs/execution/metrics.md \| Select-Object -Last 3` | `[x]` |

### Status Legend

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Not started |
| `[/]` | In progress |
| `[x]` | Complete |
| `[B]` | Blocked (must link follow-up) |

### Notes

- **Task 20 (`record_payment`)**: Status `[B]` (blocked on MEU-148). Method signature + input validation implemented; body raises `NotImplementedError("MEU-148: requires QuarterlyEstimate SQLAlchemy model")`. This is the *only* `NotImplementedError` in the project — all domain/service functions must be fully implemented. Follow-up: MEU-148 (Phase 3E).
- **Execution order**: MEU-146 → MEU-147 → MEU-143 → MEU-144 → MEU-145 (dependency-ordered: brackets → NIIT → entity+safe-harbor → annualized → dates+penalty+service).
