---
project: "2026-05-14-tax-optimization-tools"
source: "docs/execution/plans/2026-05-14-tax-optimization-tools/implementation-plan.md"
meus: ["MEU-140", "MEU-142", "MEU-137", "MEU-138", "MEU-139", "MEU-141"]
status: "complete"
template_version: "2.0"
---

# Task — Tax Optimization Tools (Phase 3C)

> **Project:** `2026-05-14-tax-optimization-tools`
> **Type:** Domain
> **Estimate:** 13 files changed (6 new modules + 6 test files + 1 __init__.py update)

## Task Table

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 1 | MEU-140: Write tests for `lot_matcher.py` (ACs 140.1–140.6) | coder | `tests/unit/domain/tax/test_lot_matcher.py` | `uv run pytest tests/unit/domain/tax/test_lot_matcher.py -x --tb=short -v *> C:\Temp\zorivest\pytest-140.txt; Get-Content C:\Temp\zorivest\pytest-140.txt \| Select-Object -Last 30` — all FAIL (Red) | `[x]` |
| 2 | MEU-140: Implement `lot_matcher.py` — `LotDetail`, `get_lot_details()`, `preview_lot_selection()` | coder | `packages/core/src/zorivest_core/domain/tax/lot_matcher.py` | Re-run task 1 validation — all PASS (Green) | `[x]` |
| 3 | MEU-142: Write tests for `rate_comparison.py` (ACs 142.1–142.7) | coder | `tests/unit/domain/tax/test_rate_comparison.py` | `uv run pytest tests/unit/domain/tax/test_rate_comparison.py -x --tb=short -v *> C:\Temp\zorivest\pytest-142.txt; Get-Content C:\Temp\zorivest\pytest-142.txt \| Select-Object -Last 30` — all FAIL (Red) | `[x]` |
| 4 | MEU-142: Implement `rate_comparison.py` — `StLtComparison`, `compare_st_lt_tax()` | coder | `packages/core/src/zorivest_core/domain/tax/rate_comparison.py` | Re-run task 3 validation — all PASS (Green) | `[x]` |
| 5 | MEU-137: Write tests for `tax_simulator.py` (ACs 137.1–137.10) | coder | `tests/unit/domain/tax/test_tax_simulator.py` | `uv run pytest tests/unit/domain/tax/test_tax_simulator.py -x --tb=short -v *> C:\Temp\zorivest\pytest-137.txt; Get-Content C:\Temp\zorivest\pytest-137.txt \| Select-Object -Last 30` — all FAIL (Red) | `[x]` |
| 6 | MEU-137: Implement `tax_simulator.py` — `TaxImpactResult`, `simulate_tax_impact()` | coder | `packages/core/src/zorivest_core/domain/tax/tax_simulator.py` | Re-run task 5 validation — all PASS (Green) | `[x]` |
| 7 | MEU-138: Write tests for `harvest_scanner.py` (ACs 138.1–138.9) | coder | `tests/unit/domain/tax/test_harvest_scanner.py` | `uv run pytest tests/unit/domain/tax/test_harvest_scanner.py -x --tb=short -v *> C:\Temp\zorivest\pytest-138.txt; Get-Content C:\Temp\zorivest\pytest-138.txt \| Select-Object -Last 30` — all FAIL (Red) | `[x]` |
| 8 | MEU-138: Implement `harvest_scanner.py` — `HarvestCandidate`, `HarvestScanResult`, `scan_harvest_candidates()` | coder | `packages/core/src/zorivest_core/domain/tax/harvest_scanner.py` | Re-run task 7 validation — all PASS (Green) | `[x]` |
| 9 | MEU-139: Write tests for `replacement_suggestions.py` (ACs 139.1–139.7) | coder | `tests/unit/domain/tax/test_replacement_suggestions.py` | `uv run pytest tests/unit/domain/tax/test_replacement_suggestions.py -x --tb=short -v *> C:\Temp\zorivest\pytest-139.txt; Get-Content C:\Temp\zorivest\pytest-139.txt \| Select-Object -Last 30` — all FAIL (Red) | `[x]` |
| 10 | MEU-139: Implement `replacement_suggestions.py` — `ReplacementSuggestion`, `REPLACEMENT_TABLE`, `suggest_replacements()`, `suggest_replacements_for_harvest()` | coder | `packages/core/src/zorivest_core/domain/tax/replacement_suggestions.py` | Re-run task 9 validation — all PASS (Green) | `[x]` |
| 11 | MEU-141: Write tests for `lot_reassignment.py` (ACs 141.1–141.7) | coder | `tests/unit/domain/tax/test_lot_reassignment.py` | `uv run pytest tests/unit/domain/tax/test_lot_reassignment.py -x --tb=short -v *> C:\Temp\zorivest\pytest-141.txt; Get-Content C:\Temp\zorivest\pytest-141.txt \| Select-Object -Last 30` — all FAIL (Red) | `[x]` |
| 12 | MEU-141: Implement `lot_reassignment.py` — `ReassignmentEligibility`, `can_reassign_lots()`, `reassign_lots()` | coder | `packages/core/src/zorivest_core/domain/tax/lot_reassignment.py` | Re-run task 11 validation — all PASS (Green) | `[x]` |
| 13 | Update `tax/__init__.py` with all new exports | coder | `packages/core/src/zorivest_core/domain/tax/__init__.py` | `uv run pyright packages/core/src/zorivest_core/domain/tax/__init__.py *> C:\Temp\zorivest\pyright-init.txt; Get-Content C:\Temp\zorivest\pyright-init.txt` — 0 errors | `[x]` |
| | **🔄 Re-Anchor Gate** | | | | |
| 14 | 🔄 `view_file` this `task.md`. Count all `[ ]` rows remaining and list them. If any implementation rows above are still `[ ]`, go back and complete them before proceeding. | coder | Console output confirming 0 unchecked implementation rows | `Select-String '\[ \]' docs/execution/plans/2026-05-14-tax-optimization-tools/task.md *> C:\Temp\zorivest\reanchor.txt; Get-Content C:\Temp\zorivest\reanchor.txt` | `[x]` |
| | **Post-Implementation** | | | | |
| 15 | Update meu-registry.md status for MEU-137..142 → ✅ | orchestrator | `.agent/context/meu-registry.md` rows updated | `rg "MEU-13[789]\|MEU-14[012]" .agent/context/meu-registry.md *> C:\Temp\zorivest\registry-check.txt; Get-Content C:\Temp\zorivest\registry-check.txt` | `[x]` |
| 16 | Audit `docs/BUILD_PLAN.md` P3 summary count | orchestrator | P3 summary row updated | `rg "Phase 3C\|P3.*summary" docs/BUILD_PLAN.md *> C:\Temp\zorivest\buildplan-check.txt; Get-Content C:\Temp\zorivest\buildplan-check.txt` | `[x]` |
| 17 | Run verification plan: unit tests | tester | All tax domain tests pass | `uv run pytest tests/unit/domain/tax/ -x --tb=short -v *> C:\Temp\zorivest\pytest-tax-opt.txt; Get-Content C:\Temp\zorivest\pytest-tax-opt.txt \| Select-Object -Last 40` | `[x]` |
| 18 | Run verification: full pytest regression | tester | All tests pass | `uv run pytest tests/ -x --tb=short -v *> C:\Temp\zorivest\pytest-full.txt; Get-Content C:\Temp\zorivest\pytest-full.txt \| Select-Object -Last 40` | `[x]` |
| 19 | Run verification: type check | tester | 0 pyright errors | `uv run pyright packages/ *> C:\Temp\zorivest\pyright.txt; Get-Content C:\Temp\zorivest\pyright.txt \| Select-Object -Last 30` | `[x]` |
| 20 | Run verification: lint | tester | 0 ruff errors | `uv run ruff check packages/ *> C:\Temp\zorivest\ruff.txt; Get-Content C:\Temp\zorivest\ruff.txt \| Select-Object -Last 20` | `[x]` |
| 21 | Run verification: anti-placeholder scan | tester | 0 matches | `rg "TODO\|FIXME\|NotImplementedError" packages/core/src/zorivest_core/domain/tax/ *> C:\Temp\zorivest\placeholder.txt; Get-Content C:\Temp\zorivest\placeholder.txt` | `[x]` |
| 22 | Run verification: MEU gate | tester | MEU gate passes | `uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate.txt; Get-Content C:\Temp\zorivest\validate.txt \| Select-Object -Last 50` | `[x]` |
| 23 | Save session state to pomera_notes | orchestrator | `Memory/Session/Zorivest-tax-optimization-tools-2026-05-14` | MCP: `pomera_notes(action="search", search_term="Zorivest-tax-optimization*")` returns ≥1 result | `[x]` |
| 24 | Create handoff | reviewer | `.agent/context/handoffs/2026-05-14-tax-optimization-tools-handoff.md` | `Test-Path .agent/context/handoffs/2026-05-14-tax-optimization-tools-handoff.md *> C:\Temp\zorivest\handoff-check.txt; Get-Content C:\Temp\zorivest\handoff-check.txt` | `[x]` |
| 25 | Create reflection | orchestrator | `docs/execution/reflections/2026-05-14-tax-optimization-tools-reflection.md` | `Test-Path docs/execution/reflections/2026-05-14-tax-optimization-tools-reflection.md *> C:\Temp\zorivest\reflection-check.txt; Get-Content C:\Temp\zorivest\reflection-check.txt` | `[x]` |
| 26 | Append metrics row | orchestrator | Row appended to `docs/execution/metrics.md` | `Get-Content docs/execution/metrics.md *> C:\Temp\zorivest\metrics-check.txt; Get-Content C:\Temp\zorivest\metrics-check.txt \| Select-Object -Last 3` | `[x]` |

### Status Legend

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Not started |
| `[/]` | In progress |
| `[x]` | Complete |
| `[B]` | Blocked (must link follow-up) |
