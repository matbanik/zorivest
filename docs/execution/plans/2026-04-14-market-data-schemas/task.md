---
project: "2026-04-14-market-data-schemas"
source: "docs/execution/plans/2026-04-14-market-data-schemas/implementation-plan.md"
meus: ["MEU-PW3"]
status: "complete"
template_version: "2.0"
---

# Task — Market Data Schemas

> **Project:** `2026-04-14-market-data-schemas`
> **Type:** Infrastructure/Domain
> **Estimate:** 4 modified + 3 new = 7 files

## Task Table

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 1 | Write source-backed FIC with acceptance criteria (AC-1 through AC-9) | orchestrator | FIC section in `implementation-plan.md` with each AC labeled Spec/Local Canon/Research-backed | `rg -c "AC-[1-9].*\| (Spec\|Local Canon\|Research-backed)" docs/execution/plans/2026-04-14-market-data-schemas/implementation-plan.md *> C:\Temp\zorivest\fic-check.txt` — expect count ≥ 9 | `[x]` |
| 2 | Write `test_market_data_models.py` (Red phase) — ORM model creation, column types, nullable constraints, unique key violations, table count update | coder | `tests/unit/test_market_data_models.py` | `uv run pytest tests/unit/test_market_data_models.py -x --tb=short -v *> C:\Temp\zorivest\pytest-models-red.txt` — all tests FAIL | `[x]` |
| 3 | Write `test_validation_schemas.py` (Red phase) — Pandera schema validation for all 4 data types (valid + invalid data), SCHEMA_REGISTRY resolution | coder | `tests/unit/test_validation_schemas.py` | `uv run pytest tests/unit/test_validation_schemas.py -x --tb=short -v *> C:\Temp\zorivest\pytest-schemas-red.txt` — all tests FAIL | `[x]` |
| 4 | Write `test_field_mappings.py` (Red phase) — field mapping resolution for quote/news/fundamentals × generic/yahoo/polygon providers | coder | `tests/unit/test_field_mappings.py` | `uv run pytest tests/unit/test_field_mappings.py -x --tb=short -v *> C:\Temp\zorivest\pytest-mappings-red.txt` — all tests FAIL | `[x]` |
| 5 | Capture FAIL_TO_PASS evidence — run all 3 test files, confirm all tests FAIL | tester | Saved failure output in `C:\Temp\zorivest\pytest-red-all.txt` | `uv run pytest tests/unit/test_market_data_models.py tests/unit/test_validation_schemas.py tests/unit/test_field_mappings.py --tb=short -v *> C:\Temp\zorivest\pytest-red-all.txt` — all FAIL | `[x]` |
| 6 | Implement 4 SQLAlchemy ORM models in `models.py` (Green phase — AC-1, AC-2, AC-3) | coder | `MarketOHLCVModel`, `MarketQuoteModel`, `MarketNewsModel`, `MarketFundamentalsModel` in `packages/infrastructure/src/zorivest_infra/database/models.py` | `uv run pytest tests/unit/test_market_data_models.py -x --tb=short -v *> C:\Temp\zorivest\pytest-models-green.txt` — all tests PASS | `[x]` |
| 7 | Update `test_models.py` EXPECTED_TABLES set (31→35) and table count assertion (31→35) | coder | Updated `tests/unit/test_models.py` | `uv run pytest tests/unit/test_models.py -x --tb=short -v *> C:\Temp\zorivest\pytest-models-existing.txt` — all tests PASS | `[x]` |
| 8 | Implement 3 Pandera schemas + SCHEMA_REGISTRY in `validation_gate.py` (Green phase — AC-4, AC-5, AC-6) | coder | `QUOTE_SCHEMA`, `NEWS_SCHEMA`, `FUNDAMENTALS_SCHEMA`, `SCHEMA_REGISTRY` in `packages/core/src/zorivest_core/services/validation_gate.py` | `uv run pytest tests/unit/test_validation_schemas.py -x --tb=short -v *> C:\Temp\zorivest\pytest-schemas-green.txt` — all tests PASS | `[x]` |
| 9 | Add 9 field mapping entries in `field_mappings.py` (Green phase — AC-7, AC-8) | coder | 9 new `(provider, data_type)` entries in `packages/infrastructure/src/zorivest_infra/market_data/field_mappings.py` | `uv run pytest tests/unit/test_field_mappings.py -x --tb=short -v *> C:\Temp\zorivest\pytest-mappings-green.txt` — all tests PASS | `[x]` |
| 10 | Sync TABLE_ALLOWLIST column sets with ORM models in `write_dispositions.py` (AC-9) | coder | Updated `packages/infrastructure/src/zorivest_infra/repositories/write_dispositions.py` | `uv run pytest tests/unit/test_market_data_models.py tests/unit/test_validation_schemas.py tests/unit/test_field_mappings.py -x --tb=short -v *> C:\Temp\zorivest\pytest-all-pw3.txt` — all tests PASS | `[x]` |
| 11 | Regression check — existing transform_step and models tests still pass | tester | No regressions | `uv run pytest tests/unit/test_models.py tests/unit/test_transform_step.py tests/unit/test_db_write_adapter.py -x --tb=short -v *> C:\Temp\zorivest\pytest-regression.txt` — all tests PASS | `[x]` |
| 12 | Update `docs/BUILD_PLAN.md` — add MEU-PW3 row to P2.5b table, update MEU Summary counts | orchestrator | MEU-PW3 row added, counts corrected | `rg "MEU-PW3" docs/BUILD_PLAN.md *> C:\Temp\zorivest\bp-grep.txt` — expect 1 match | `[x]` |
| 13 | Run verification plan (MEU gate) | tester | All checks pass | `uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate.txt; Get-Content C:\Temp\zorivest\validate.txt \| Select-Object -Last 50` | `[x]` |
| 14 | Save session state to pomera_notes | orchestrator | `Memory/Session/Zorivest-market-data-schemas-2026-04-14` | MCP: `pomera_notes(action="search", search_term="Zorivest-market-data-schemas*")` returns ≥1 result | `[x]` |
| 15 | Create handoff | reviewer | `.agent/context/handoffs/115-2026-04-14-market-data-schemas-bp09s49.6.md` | `Test-Path .agent/context/handoffs/115-2026-04-14-market-data-schemas-bp09s49.6.md` | `[x]` |
| 16 | Create reflection | orchestrator | `docs/execution/reflections/2026-04-14-market-data-schemas-reflection.md` | `Test-Path docs/execution/reflections/2026-04-14-market-data-schemas-reflection.md` | `[x]` |
| 17 | Append metrics row | orchestrator | Row appended to `docs/execution/metrics.md` | `Get-Content docs/execution/metrics.md \| Select-Object -Last 3` | `[x]` |

### Status Legend

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Not started |
| `[/]` | In progress |
| `[x]` | Complete |
| `[B]` | Blocked (must link follow-up) |
