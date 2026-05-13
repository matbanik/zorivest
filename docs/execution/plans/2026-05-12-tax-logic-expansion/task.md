---
project: "2026-05-12-tax-logic-expansion"
source: "docs/execution/plans/2026-05-12-tax-logic-expansion/implementation-plan.md"
meus: ["MEU-125", "MEU-126"]
status: "not_started"
template_version: "2.0"
---

# Task — Tax Logic Expansion

> **Project:** `2026-05-12-tax-logic-expansion`
> **Type:** Domain + Service Layer
> **Estimate:** ~10 files changed

## Task Table

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| | **MEU-125: TaxLotTracking (item 52)** | | | | |
| 1 | Write FIC + tests for `lot_selector.py` (8 cost basis methods + IBKR 4-tier priority, ~30 tests) | coder | `tests/unit/test_lot_selector.py` | [cmd-lotsel](#cmd-lotsel) | `[x]` |
| 2 | Implement `select_lots_for_closing()` in `domain/tax/lot_selector.py` — RED→GREEN | coder | `packages/core/src/zorivest_core/domain/tax/lot_selector.py` | [cmd-lotsel](#cmd-lotsel) | `[x]` |
| 3 | Write FIC + tests for `TaxService` lot management (mocked UoW, ~10 tests: get_lots, close_lot, reassign_basis) | coder | `tests/unit/test_tax_service.py` | [cmd-taxsvc](#cmd-taxsvc) | `[x]` |
| 4 | Implement `TaxService` with lot management methods in `services/tax_service.py` — RED→GREEN | coder | `packages/core/src/zorivest_core/services/tax_service.py` | [cmd-taxsvc](#cmd-taxsvc) | `[x]` |
| | **MEU-126: TaxGainsCalc (item 53)** | | | | |
| 5 | Write FIC + tests for `gains_calculator.py` (~10 tests) | coder | `tests/unit/test_gains_calculator.py` | [cmd-gains](#cmd-gains) | `[x]` |
| 6 | Implement `calculate_realized_gain()` in `domain/tax/gains_calculator.py` — RED→GREEN | coder | `packages/core/src/zorivest_core/domain/tax/gains_calculator.py` | [cmd-gains](#cmd-gains) | `[x]` |
| 7 | Write FIC + tests for `simulate_impact()` TaxService method (~5 tests with mocked UoW) | coder | `tests/unit/test_tax_service.py` (extend) | [cmd-taxsvc](#cmd-taxsvc) | `[x]` |
| 8 | Implement `simulate_impact()` in `services/tax_service.py` — RED→GREEN | coder | `packages/core/src/zorivest_core/services/tax_service.py` (modify) | [cmd-taxsvc](#cmd-taxsvc) | `[x]` |
| 9 | Write + run integration tests for TaxService with real SQLite (~8 tests: lot CRUD, close, gain calc round-trip) | coder | `tests/integration/test_tax_service_integration.py` | [cmd-taxinteg](#cmd-taxinteg) | `[x]` |
| | **Post-Implementation** | | | | |
| | **🔄 Re-Anchor Gate** | | | | |
| 10 | 🔄 `view_file` this `task.md`. Count all `[ ]` rows remaining and list them. If any implementation rows above are still `[ ]`, go back and complete them before proceeding. | coder | Console output confirming 0 unchecked implementation rows | [cmd-reanchor](#cmd-reanchor) | `[x]` |
| 11 | Audit `docs/BUILD_PLAN.md` for stale refs | orchestrator | No changes expected; evidence of clean grep | [cmd-buildaudit](#cmd-buildaudit) | `[x]` |
| 12 | Run full verification plan (regression + pyright + ruff + MEU gate) | tester | All 4 checks pass | [cmd-full-verify](#cmd-full-verify) | `[x]` |
| 13 | Save session state to pomera_notes | orchestrator | `Memory/Session/Zorivest-tax-logic-expansion-2026-05-12` | `pomera_notes(action="search", search_term="Zorivest-tax-logic*")` returns ≥1 result | `[x]` |
| 14 | Create handoff | reviewer | `.agent/context/handoffs/2026-05-12-tax-logic-expansion-handoff.md` | [cmd-handoff-check](#cmd-handoff-check) | `[x]` |
| 15 | Create reflection | orchestrator | `docs/execution/reflections/2026-05-12-tax-logic-expansion-reflection.md` | [cmd-reflection-check](#cmd-reflection-check) | `[x]` |
| 16 | Append metrics row | orchestrator | Row appended to `docs/execution/metrics.md` | [cmd-metrics-check](#cmd-metrics-check) | `[x]` |

### Status Legend

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Not started |
| `[/]` | In progress |
| `[x]` | Complete |
| `[B]` | Blocked (must link follow-up) |

---

## Validation Commands

Copy-runnable commands referenced by the task table. All commands use the redirect-to-file pattern per AGENTS.md §Terminal.

### cmd-lotsel

```powershell
uv run pytest tests/unit/test_lot_selector.py -x --tb=short -v *> C:\Temp\zorivest\pytest-lotsel.txt; Get-Content C:\Temp\zorivest\pytest-lotsel.txt | Select-Object -Last 40
```

### cmd-taxsvc

```powershell
uv run pytest tests/unit/test_tax_service.py -x --tb=short -v *> C:\Temp\zorivest\pytest-taxsvc.txt; Get-Content C:\Temp\zorivest\pytest-taxsvc.txt | Select-Object -Last 40
```

### cmd-gains

```powershell
uv run pytest tests/unit/test_gains_calculator.py -x --tb=short -v *> C:\Temp\zorivest\pytest-gains.txt; Get-Content C:\Temp\zorivest\pytest-gains.txt | Select-Object -Last 40
```

### cmd-taxinteg

```powershell
uv run pytest tests/integration/test_tax_service_integration.py -x --tb=short -v *> C:\Temp\zorivest\pytest-taxinteg.txt; Get-Content C:\Temp\zorivest\pytest-taxinteg.txt | Select-Object -Last 40
```

### cmd-reanchor

```powershell
Select-String '\[ \]' docs/execution/plans/2026-05-12-tax-logic-expansion/task.md *> C:\Temp\zorivest\reanchor.txt; Get-Content C:\Temp\zorivest\reanchor.txt
```

### cmd-buildaudit

```powershell
rg "tax-logic-expansion" docs/BUILD_PLAN.md *> C:\Temp\zorivest\buildplan-audit.txt; Get-Content C:\Temp\zorivest\buildplan-audit.txt
```

### cmd-full-verify

Run all 4 checks in sequence:

```powershell
# 1. Full regression
uv run pytest tests/ -x --tb=short *> C:\Temp\zorivest\pytest-full.txt; Get-Content C:\Temp\zorivest\pytest-full.txt | Select-Object -Last 40

# 2. Type check
uv run pyright packages/ *> C:\Temp\zorivest\pyright.txt; Get-Content C:\Temp\zorivest\pyright.txt | Select-Object -Last 30

# 3. Lint
uv run ruff check packages/ *> C:\Temp\zorivest\ruff.txt; Get-Content C:\Temp\zorivest\ruff.txt | Select-Object -Last 20

# 4. MEU gate
uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate.txt; Get-Content C:\Temp\zorivest\validate.txt | Select-Object -Last 50
```

### cmd-handoff-check

```powershell
Test-Path .agent/context/handoffs/2026-05-12-tax-logic-expansion-handoff.md *> C:\Temp\zorivest\handoff-check.txt; Get-Content C:\Temp\zorivest\handoff-check.txt
```

### cmd-reflection-check

```powershell
Test-Path docs/execution/reflections/2026-05-12-tax-logic-expansion-reflection.md *> C:\Temp\zorivest\reflection-check.txt; Get-Content C:\Temp\zorivest\reflection-check.txt
```

### cmd-metrics-check

```powershell
Get-Content docs/execution/metrics.md | Select-Object -Last 3 *> C:\Temp\zorivest\metrics-check.txt; Get-Content C:\Temp\zorivest\metrics-check.txt
```
