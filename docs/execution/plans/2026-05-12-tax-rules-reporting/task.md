---
project: "2026-05-12-tax-rules-reporting"
source: "docs/execution/plans/2026-05-12-tax-rules-reporting/implementation-plan.md"
meus: ["MEU-127", "MEU-128", "MEU-129"]
status: "in_review"
template_version: "2.0"
---

# Task — Tax Rules & Reporting

> **Project:** `2026-05-12-tax-rules-reporting`
> **Type:** Domain
> **Estimate:** ~10 files changed (3 new domain modules, 3 new test files, 4 modified files)

## Task Table

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| | **MEU-127: Capital Loss Carryforward** | | | | |
| 1 | Write FIC tests for `apply_capital_loss_rules(st_gains, lt_gains, st_carryforward, lt_carryforward, filing_status)` — $3K/$1.5K cap, netting order with separate ST/LT carryforward inputs, edge cases | coder | `tests/unit/test_loss_carryforward.py` | `uv run pytest tests/unit/test_loss_carryforward.py -x --tb=short -v *> C:\Temp\zorivest\pytest-127-red.txt; Get-Content C:\Temp\zorivest\pytest-127-red.txt \| Select-Object -Last 40` — all FAIL | `[x]` |
| 2 | Implement `apply_capital_loss_rules()` + `CapitalLossResult` | coder | `packages/core/src/zorivest_core/domain/tax/loss_carryforward.py` | `uv run pytest tests/unit/test_loss_carryforward.py -x --tb=short -v *> C:\Temp\zorivest\pytest-127-green.txt; Get-Content C:\Temp\zorivest\pytest-127-green.txt \| Select-Object -Last 40` — all PASS | `[x]` |
| 3 | Write FIC tests for `TaxService.get_taxable_gains()` — tax-advantaged exclusion, carryforward application with ST-first allocation per IRS Schedule D ordering | coder | `tests/unit/test_tax_service.py` (extend) | `uv run pytest tests/unit/test_tax_service.py -x --tb=short -v *> C:\Temp\zorivest\pytest-127-svc-red.txt; Get-Content C:\Temp\zorivest\pytest-127-svc-red.txt \| Select-Object -Last 40` — new tests FAIL | `[x]` |
| 4 | Implement `get_taxable_gains()` on TaxService + export from `__init__.py` | coder | `services/tax_service.py`, `domain/tax/__init__.py` | `uv run pytest tests/unit/test_tax_service.py tests/unit/test_loss_carryforward.py -x --tb=short -v *> C:\Temp\zorivest\pytest-127-svc-green.txt; Get-Content C:\Temp\zorivest\pytest-127-svc-green.txt \| Select-Object -Last 40` — all PASS | `[x]` |
| | **MEU-128: Options Assignment/Exercise** | | | | |
| 5 | Write FIC tests for `parse_option_symbol()` — normalized format `"UNDERLYING YYMMDD C/P STRIKE"` parsing, non-option passthrough, malformed input | coder | `tests/unit/test_option_pairing.py` | `uv run pytest tests/unit/test_option_pairing.py -x --tb=short -v *> C:\Temp\zorivest\pytest-128-parse-red.txt; Get-Content C:\Temp\zorivest\pytest-128-parse-red.txt \| Select-Object -Last 40` — all FAIL | `[x]` |
| 6 | Implement `parse_option_symbol()` + `OptionDetails` dataclass | coder | `packages/core/src/zorivest_core/domain/tax/option_pairing.py` | `uv run pytest tests/unit/test_option_pairing.py -x --tb=short -v *> C:\Temp\zorivest\pytest-128-parse-green.txt; Get-Content C:\Temp\zorivest\pytest-128-parse-green.txt \| Select-Object -Last 40` — all PASS | `[x]` |
| 7 | Write FIC tests for `adjust_basis_for_assignment(stock_lot, option_trade, assignment_type)` — all four IRS paths: short put assignment, short call assignment, long call exercise, long put exercise; side derived from `option_trade.action`; mismatch error cases | coder | `tests/unit/test_option_pairing.py` (extend) | `uv run pytest tests/unit/test_option_pairing.py -x --tb=short -v *> C:\Temp\zorivest\pytest-128-adj-red.txt; Get-Content C:\Temp\zorivest\pytest-128-adj-red.txt \| Select-Object -Last 40` — new tests FAIL | `[x]` |
| 8 | Implement `adjust_basis_for_assignment()` with holder/writer distinction | coder | `domain/tax/option_pairing.py` (extend) | `uv run pytest tests/unit/test_option_pairing.py -x --tb=short -v *> C:\Temp\zorivest\pytest-128-adj-green.txt; Get-Content C:\Temp\zorivest\pytest-128-adj-green.txt \| Select-Object -Last 40` — all PASS | `[x]` |
| 9 | Write FIC tests for `TaxService.pair_option_assignment(lot_id, option_exec_id, assignment_type)` — all four scenarios; side derived from loaded option trade's action | coder | `tests/unit/test_tax_service.py` (extend) | `uv run pytest tests/unit/test_tax_service.py -x --tb=short -v *> C:\Temp\zorivest\pytest-128-svc-red.txt; Get-Content C:\Temp\zorivest\pytest-128-svc-red.txt \| Select-Object -Last 40` — new tests FAIL | `[x]` |
| 10 | Implement `pair_option_assignment()` on TaxService + export from `__init__.py` | coder | `services/tax_service.py`, `domain/tax/__init__.py` | `uv run pytest tests/unit/test_tax_service.py tests/unit/test_option_pairing.py -x --tb=short -v *> C:\Temp\zorivest\pytest-128-svc-green.txt; Get-Content C:\Temp\zorivest\pytest-128-svc-green.txt \| Select-Object -Last 40` — all PASS | `[x]` |
| | **MEU-129: YTD P&L by Symbol** | | | | |
| 11 | Write FIC tests for `compute_ytd_pnl()` — per-symbol aggregation, ST/LT split, year filtering, empty list | coder | `tests/unit/test_ytd_pnl.py` | `uv run pytest tests/unit/test_ytd_pnl.py -x --tb=short -v *> C:\Temp\zorivest\pytest-129-red.txt; Get-Content C:\Temp\zorivest\pytest-129-red.txt \| Select-Object -Last 40` — all FAIL | `[x]` |
| 12 | Implement `compute_ytd_pnl()` + `SymbolPnl`, `YtdPnlResult` dataclasses | coder | `packages/core/src/zorivest_core/domain/tax/ytd_pnl.py` | `uv run pytest tests/unit/test_ytd_pnl.py -x --tb=short -v *> C:\Temp\zorivest\pytest-129-green.txt; Get-Content C:\Temp\zorivest\pytest-129-green.txt \| Select-Object -Last 40` — all PASS | `[x]` |
| 13 | Write FIC tests for `TaxService.get_ytd_pnl()` — service orchestration, tax-advantaged exclusion | coder | `tests/unit/test_tax_service.py` (extend) | `uv run pytest tests/unit/test_tax_service.py -x --tb=short -v *> C:\Temp\zorivest\pytest-129-svc-red.txt; Get-Content C:\Temp\zorivest\pytest-129-svc-red.txt \| Select-Object -Last 40` — new tests FAIL | `[x]` |
| 14 | Implement `get_ytd_pnl()` on TaxService + export from `__init__.py` | coder | `services/tax_service.py`, `domain/tax/__init__.py` | `uv run pytest tests/unit/test_tax_service.py tests/unit/test_ytd_pnl.py -x --tb=short -v *> C:\Temp\zorivest\pytest-129-svc-green.txt; Get-Content C:\Temp\zorivest\pytest-129-svc-green.txt \| Select-Object -Last 40` — all PASS | `[x]` |
| | **🔄 Re-Anchor Gate** | | | | |
| 15 | 🔄 `view_file` this `task.md`. Count all `[ ]` rows remaining and list them. If any implementation rows above are still `[ ]`, go back and complete them before proceeding. | coder | Console output confirming 0 unchecked implementation rows | `Select-String '\\[ \\]' docs/execution/plans/2026-05-12-tax-rules-reporting/task.md *> C:\Temp\zorivest\reanchor.txt; Get-Content C:\Temp\zorivest\reanchor.txt` | `[x]` |
| | **Post-Implementation** | | | | |
| 16 | Audit `docs/BUILD_PLAN.md` — update MEU-127/128/129 status ⬜→🟡 | orchestrator | 3 status updates in Phase 3A table | `rg "MEU-127\|MEU-128\|MEU-129" docs/BUILD_PLAN.md *> C:\Temp\zorivest\buildplan-check.txt; Get-Content C:\Temp\zorivest\buildplan-check.txt` | `[x]` |
| 17 | Update `.agent/context/meu-registry.md` — update MEU-127/128/129 statuses ⬜→🟡 and verify entries | orchestrator | 3 status transitions ⬜→🟡 | `rg "MEU-12[7-9].*🟡" .agent/context/meu-registry.md *> C:\Temp\zorivest\registry-status.txt; Get-Content C:\Temp\zorivest\registry-status.txt` — expects 3 matches | `[x]` |
| 18 | Run verification plan (7 checks) | tester | All checks pass | `uv run pytest tests/ -x --tb=short -v *> C:\Temp\zorivest\pytest-full.txt; Get-Content C:\Temp\zorivest\pytest-full.txt \| Select-Object -Last 40` + `uv run pyright packages/ *> C:\Temp\zorivest\pyright.txt; Get-Content C:\Temp\zorivest\pyright.txt \| Select-Object -Last 30` + `uv run ruff check packages/ *> C:\Temp\zorivest\ruff.txt; Get-Content C:\Temp\zorivest\ruff.txt \| Select-Object -Last 20` + `uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate.txt; Get-Content C:\Temp\zorivest\validate.txt \| Select-Object -Last 50` + `rg "TODO\|FIXME\|NotImplementedError" packages/ *> C:\Temp\zorivest\placeholders.txt; Get-Content C:\Temp\zorivest\placeholders.txt` | `[x]` |
| 19 | Save session state to pomera_notes | orchestrator | `Memory/Session/Zorivest-tax-rules-reporting-2026-05-12` | MCP: `pomera_notes(action="search", search_term="Zorivest-tax-rules*")` returns ≥1 result | `[x]` |
| 20 | Create handoff | reviewer | `.agent/context/handoffs/2026-05-12-tax-rules-reporting-handoff.md` | `Test-Path .agent/context/handoffs/2026-05-12-tax-rules-reporting-handoff.md` | `[x]` |
| 21 | Create reflection | orchestrator | `docs/execution/reflections/2026-05-12-tax-rules-reporting-reflection.md` | `Test-Path docs/execution/reflections/2026-05-12-tax-rules-reporting-reflection.md` | `[x]` |
| 22 | Append metrics row | orchestrator | Row appended to `docs/execution/metrics.md` | `Get-Content docs/execution/metrics.md \| Select-Object -Last 3` | `[x]` |

### Status Legend

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Not started |
| `[/]` | In progress |
| `[x]` | Complete |
| `[B]` | Blocked (must link follow-up) |
