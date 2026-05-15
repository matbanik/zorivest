---
project: "2026-05-13-wash-sale-extensions"
source: "docs/execution/plans/2026-05-13-wash-sale-extensions/implementation-plan.md"
meus: ["MEU-133", "MEU-134", "MEU-135", "MEU-136"]
status: "complete"
template_version: "2.0"
---

# Task — Wash Sale Extensions

> **Project:** `2026-05-13-wash-sale-extensions`
> **Type:** Domain
> **Estimate:** ~14 files changed

## Task Table

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| | **MEU-134: DRIP Foundation (prerequisite for 133)** | | | | |
| 1 | Write FIC + RED tests for DRIP detection: DRIP lot within window → match with `is_drip_triggered=True`; `include_drip=False` → DRIP excluded; non-DRIP → `is_drip_triggered=False`; AcquisitionSource enum importable | coder | `test_wash_sale_detector.py` updated | `uv run pytest tests/unit/domain/tax/test_wash_sale_detector.py -x --tb=short -v -k "drip" *> C:\Temp\zorivest\t1.txt; Get-Content C:\Temp\zorivest\t1.txt \| Select-Object -Last 30` (expect FAIL) | `[x]` |
| 2 | Add `AcquisitionSource` enum to `enums.py` (7 members: PURCHASE, DRIP, TRANSFER, GIFT, INHERITANCE, EXERCISE, ASSIGNMENT) | coder | `enums.py` updated | `uv run pyright packages/core/ *> C:\Temp\zorivest\t2.txt; Get-Content C:\Temp\zorivest\t2.txt \| Select-Object -Last 20` | `[x]` |
| 3 | Add `acquisition_source: AcquisitionSource \| None = None` to `TaxLot` entity | coder | `entities.py` updated | `uv run pyright packages/core/ *> C:\Temp\zorivest\t3.txt; Get-Content C:\Temp\zorivest\t3.txt \| Select-Object -Last 20` | `[x]` |
| 4 | Add `acquisition_source` column to `TaxLotModel` in `database/models.py` (~line 878) | coder | `models.py` updated | `uv run pyright packages/infrastructure/ *> C:\Temp\zorivest\t4.txt; Get-Content C:\Temp\zorivest\t4.txt \| Select-Object -Last 20` | `[x]` |
| 5 | Add `acquisition_source` to mapper functions (`_lot_model_to_entity`, `_lot_entity_to_model`, `update()`) in `tax_repository.py` | coder | `tax_repository.py` updated | `uv run pyright packages/infrastructure/ *> C:\Temp\zorivest\t5.txt; Get-Content C:\Temp\zorivest\t5.txt \| Select-Object -Last 20` | `[x]` |
| 6 | Add round-trip persistence test for `acquisition_source` field in `test_tax_lot_repository.py` | coder | Persistence test added | `uv run pytest tests/unit/infrastructure/test_tax_lot_repository.py -x --tb=short -v -k "acquisition" *> C:\Temp\zorivest\t6.txt; Get-Content C:\Temp\zorivest\t6.txt \| Select-Object -Last 20` | `[x]` |
| 7 | Add `is_drip_triggered: bool = False` field to `WashSaleMatch` dataclass | coder | `wash_sale_detector.py` updated | `uv run pyright packages/core/ *> C:\Temp\zorivest\t7.txt; Get-Content C:\Temp\zorivest\t7.txt \| Select-Object -Last 20` | `[x]` |
| 8 | Implement `include_drip` param in `detect_wash_sales()` — skip DRIP lots when False, set `is_drip_triggered` when DRIP lot matches (GREEN) | coder | `wash_sale_detector.py` green | `uv run pytest tests/unit/domain/tax/test_wash_sale_detector.py -x --tb=short -v -k "drip" *> C:\Temp\zorivest\t8.txt; Get-Content C:\Temp\zorivest\t8.txt \| Select-Object -Last 30` (expect PASS) | `[x]` |
| 9 | Wire `TaxProfile.include_drip_wash_detection` → `detect_wash_sales(include_drip=...)` in `TaxService.detect_and_apply_wash_sales()` and `scan_cross_account_wash_sales()` | coder | `tax_service.py` updated | `uv run pytest tests/unit/services/test_tax_service_wash_sale.py -x --tb=short -v *> C:\Temp\zorivest\t9.txt; Get-Content C:\Temp\zorivest\t9.txt \| Select-Object -Last 30` | `[x]` |
| | **MEU-133: Options-to-Stock Matching** | | | | |
| 10 | Write FIC + RED tests for options matching: CONSERVATIVE mode option within window → match; AGGRESSIVE mode → no match; malformed option → skip | coder | `test_wash_sale_detector.py` updated | `uv run pytest tests/unit/domain/tax/test_wash_sale_detector.py -x --tb=short -v -k "option" *> C:\Temp\zorivest\t10.txt; Get-Content C:\Temp\zorivest\t10.txt \| Select-Object -Last 30` (expect FAIL) | `[x]` |
| 11 | Implement `wash_sale_method` param in `detect_wash_sales()` — CONSERVATIVE uses `parse_option_symbol()` to match option underlying vs loss lot ticker (GREEN) | coder | `wash_sale_detector.py` green | `uv run pytest tests/unit/domain/tax/test_wash_sale_detector.py -x --tb=short -v -k "option" *> C:\Temp\zorivest\t11.txt; Get-Content C:\Temp\zorivest\t11.txt \| Select-Object -Last 30` (expect PASS) | `[x]` |
| 12 | Wire `TaxProfile.wash_sale_method` → `detect_wash_sales(wash_sale_method=...)` in both `detect_and_apply_wash_sales()` and `scan_cross_account_wash_sales()` | coder | `tax_service.py` updated | `uv run pytest tests/unit/services/test_tax_service_wash_sale.py -x --tb=short -v *> C:\Temp\zorivest\t12.txt; Get-Content C:\Temp\zorivest\t12.txt \| Select-Object -Last 30` | `[x]` |
| | **MEU-135: Rebalance + Spousal Warnings** | | | | |
| 13 | Write FIC + RED tests: rebalance conflict detected; spousal conflict detected; no conflict → empty; spousal excluded when flag=False | coder | `test_wash_sale_warnings.py` created | `uv run pytest tests/unit/domain/tax/test_wash_sale_warnings.py -x --tb=short -v *> C:\Temp\zorivest\t13.txt; Get-Content C:\Temp\zorivest\t13.txt \| Select-Object -Last 30` (expect FAIL) | `[x]` |
| 14 | Create `wash_sale_warnings.py` with `WarningType` enum, `WashSaleWarning` frozen dataclass (5 fields), and `check_wash_sale_conflicts()` pure function | coder | New file in `domain/tax/` | `uv run pyright packages/core/ *> C:\Temp\zorivest\t14.txt; Get-Content C:\Temp\zorivest\t14.txt \| Select-Object -Last 20` | `[x]` |
| 15 | Implement `check_wash_sale_conflicts()` logic — scan for recent losses, compute days_remaining, classify warning type (GREEN) | coder | `wash_sale_warnings.py` green | `uv run pytest tests/unit/domain/tax/test_wash_sale_warnings.py -x --tb=short -v *> C:\Temp\zorivest\t15.txt; Get-Content C:\Temp\zorivest\t15.txt \| Select-Object -Last 30` (expect PASS) | `[x]` |
| 16 | Add `TaxService.check_wash_sale_conflicts()` service method — loads lots from UoW, delegates to pure function | coder | `tax_service.py` updated | `uv run pytest tests/unit/services/test_tax_service_wash_sale.py -x --tb=short -v *> C:\Temp\zorivest\t16.txt; Get-Content C:\Temp\zorivest\t16.txt \| Select-Object -Last 30` | `[x]` |
| | **MEU-136: Pre-Trade Prevention Alerts** | | | | |
| 17 | Write FIC + RED tests: sale at loss with recent purchase → warnings + wait_days > 0; sale at gain → no warnings; purchase older than 30 days → wait_days=0 | coder | `test_pre_trade_alerts.py` created | `uv run pytest tests/unit/services/test_pre_trade_alerts.py -x --tb=short -v *> C:\Temp\zorivest\t17.txt; Get-Content C:\Temp\zorivest\t17.txt \| Select-Object -Last 30` (expect FAIL) | `[x]` |
| 18 | Add `wash_sale_warnings: list[WashSaleWarning]` and `wait_days: int = 0` fields to `SimulationResult` | coder | `tax_service.py` updated | `uv run pyright packages/core/ *> C:\Temp\zorivest\t18.txt; Get-Content C:\Temp\zorivest\t18.txt \| Select-Object -Last 20` | `[x]` |
| 19 | Implement pre-trade alert logic in `simulate_impact()` — check for recent same-ticker purchases, compute wait_days, set `wash_risk = len(warnings) > 0` (GREEN) | coder | `tax_service.py` green | `uv run pytest tests/unit/services/test_pre_trade_alerts.py -x --tb=short -v *> C:\Temp\zorivest\t19.txt; Get-Content C:\Temp\zorivest\t19.txt \| Select-Object -Last 30` (expect PASS) | `[x]` |
| | **Cross-MEU Integration** | | | | |
| 20 | Run full wash sale test suite (all 4 test files + service tests) | tester | All pass | `uv run pytest tests/unit/domain/tax/ tests/unit/services/test_tax_service_wash_sale.py tests/unit/services/test_pre_trade_alerts.py -x --tb=short -v *> C:\Temp\zorivest\t20.txt; Get-Content C:\Temp\zorivest\t20.txt \| Select-Object -Last 40` | `[x]` |
| 21 | Run existing integration tests to confirm no regressions | tester | All pass | `uv run pytest tests/integration/ -x --tb=short -v *> C:\Temp\zorivest\t21.txt; Get-Content C:\Temp\zorivest\t21.txt \| Select-Object -Last 30` | `[x]` |
| | **🔄 Re-Anchor Gate** | | | | |
| 22 | 🔄 `view_file` this `task.md`. Count all `[ ]` rows remaining and list them. If any implementation rows above are still `[ ]`, go back and complete them before proceeding. | coder | Console output confirming 0 unchecked implementation rows | `Select-String '\[ \]' docs/execution/plans/2026-05-13-wash-sale-extensions/task.md *> C:\Temp\zorivest\t22.txt; Get-Content C:\Temp\zorivest\t22.txt` | `[x]` |
| | **Post-Implementation** | | | | |
| 23 | Audit `docs/BUILD_PLAN.md` for stale refs | orchestrator | No changes expected; evidence of clean grep | `rg "wash-sale-extensions" docs/BUILD_PLAN.md *> C:\Temp\zorivest\t23.txt; Get-Content C:\Temp\zorivest\t23.txt` (expect 0 matches) | `[x]` |
| 24 | Run verification plan (all 5 checks from implementation-plan.md) | tester | All checks pass | See implementation-plan.md §Verification Plan | `[x]` |
| 25 | Save session state to pomera_notes | orchestrator | `Memory/Session/Zorivest-wash-sale-extensions-2026-05-13` | MCP: `pomera_notes(action="search", search_term="Zorivest-wash-sale*")` returns ≥1 result | `[x]` |
| 26 | Create handoff | reviewer | `.agent/context/handoffs/2026-05-13-wash-sale-extensions-handoff.md` | `Test-Path .agent/context/handoffs/2026-05-13-wash-sale-extensions-handoff.md *> C:\Temp\zorivest\t26.txt; Get-Content C:\Temp\zorivest\t26.txt` | `[x]` |
| 27 | Create reflection | orchestrator | `docs/execution/reflections/2026-05-13-wash-sale-extensions-reflection.md` | `Test-Path docs/execution/reflections/2026-05-13-wash-sale-extensions-reflection.md *> C:\Temp\zorivest\t27.txt; Get-Content C:\Temp\zorivest\t27.txt` | `[x]` |
| 28 | Append metrics row | orchestrator | Row appended to `docs/execution/metrics.md` | `Get-Content docs/execution/metrics.md *> C:\Temp\zorivest\t28.txt; Get-Content C:\Temp\zorivest\t28.txt \| Select-Object -Last 3` | `[x]` |

### Status Legend

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Not started |
| `[/]` | In progress |
| `[x]` | Complete |
| `[B]` | Blocked (must link follow-up) |
