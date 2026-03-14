# MEU-99: CSV Import + Broker Auto-Detection

## Task

- **Date:** 2026-03-13
- **Task slug:** csv-import
- **Build plan ref:** P2.75 item 53e
- **Scope:** CSV parser framework, TOS + NinjaTrader parsers, ImportService orchestrator

## Inputs

- **User request:** Build universal CSV import framework with broker auto-detection
- **Specs referenced:** [Build Plan Expansion Ideas §18](../../../_inspiration/import_research/Build%20Plan%20Expansion%20Ideas.md) (Broker CSV Import Framework), [implementation plan](../../docs/execution/plans/2026-03-13-ibkr-csv-import-foundation/implementation-plan.md) FIC-99
- **Depends on:** MEU-96 (shared domain types, `BrokerFileAdapter` Protocol)

## Role Plan

1. orchestrator
2. coder
3. tester
4. reviewer (Codex)

## Coder Output

### Changed Files

| File | Action | Description |
|---|---|---|
| `packages/infrastructure/src/zorivest_infra/broker_adapters/csv_base.py` | NEW | `CSVParserBase` ABC — encoding detection (chardet), BOM removal, `parse_file()` aggregation |
| `packages/infrastructure/src/zorivest_infra/broker_adapters/tos_csv.py` | NEW | `ThinkorSwimCSVParser` — multi-section CSV, TOS option symbol normalization |
| `packages/infrastructure/src/zorivest_infra/broker_adapters/ninjatrader_csv.py` | NEW | `NinjaTraderCSVParser` — pre-paired round-trip format, MFE/MAE preservation |
| `packages/core/src/zorivest_core/services/import_service.py` | NEW | `ImportService` orchestrator + `UnknownBrokerFormat` exception |
| `tests/unit/test_csv_import.py` | NEW | 31 tests across 5 test classes |

### Design Decisions

- `CSVParserBase._extract_data_lines()` is an override hook for multi-section CSVs (TOS overrides it)
- TOS commission calculated from `(Price - Net Price) × Qty`
- NinjaTrader: all instruments classified as `FUTURE` (NinjaTrader is primarily a futures platform)
- NinjaTrader `Strategy`, `MAE`, `MFE` preserved in `raw_data` for downstream enrichment
- `ImportService._csv_adapters` uses `typing.cast` for pyright-safe Protocol narrowing
- `auto_detect_csv_broker()` scans first 10 lines for header matching across all registered parsers

## Tester Output

### Commands Run

```
uv run pytest tests/unit/test_csv_import.py -v                # 32 passed
uv run pytest tests/ --tb=no -q                                # 1232 passed, 1 skipped
uv run pyright .../import_service.py .../broker_adapters/      # 0 errors
uv run ruff check <all touched files>                          # 0 remaining
```

### Pass/Fail Matrix

| AC | Description | Tests | Status |
|---|---|---|---|
| AC-1 | `CSVParserBase.parse_file()` encoding + delegation | `TestCSVParserBaseEncoding` (3 tests) | ✅ |
| AC-2 | TOS header fingerprint detection | `TestThinkorSwimParser::test_detect_*` (2 tests) | ✅ |
| AC-3 | TOS multi-section extraction | `TestThinkorSwimParser::test_parse_file_*` (2 tests) | ✅ |
| AC-4 | TOS options symbol normalization | `TestThinkorSwimParser::test_option_*` (1 test) | ✅ |
| AC-5 | NinjaTrader pre-paired format | `TestNinjaTraderParser::test_parse_*` (2 tests) | ✅ |
| AC-6 | MFE/MAE in raw_data | `TestNinjaTraderParser::test_mfe_mae_*` (1 test) | ✅ |
| AC-7 | Auto-detection (TOS + NT) | `TestImportServiceRouting::test_import_csv_auto_detects_*` (2 tests) | ✅ |
| AC-8 | `broker_hint` override | `TestImportServiceRouting::test_broker_hint_*` (1 test) | ✅ |
| AC-9 | Unknown format error | `TestImportServiceRouting::test_unknown_*` + `TestEdgeCases::test_empty_*` (3 tests) | ✅ |
| AC-10 | BOM/Latin-1 encoding | `TestCSVParserBaseEncoding` + `TestEdgeCases::test_csv_with_bom` + `test_bom_csv_through_import_service` (5 tests) | ✅ |

### Regression

- **Before:** 1166 passed, 1 skipped
- **After:** 1232 passed, 1 skipped (+66 new across MEU-96 + MEU-99, 0 regressions)

- Evidence bundle location: This handoff
- FAIL_TO_PASS / PASS_TO_PASS result: 32 FAIL_TO_PASS (Red → Green), 1200 PASS_TO_PASS
- Mutation score: Not run
- Contract verification status: Codex review pending

## Reviewer Output

- Findings by severity: Pending Codex review
- Open questions: None
- Verdict: `pending`
- Residual risk: None identified
- Anti-deferral scan result: 0 TODOs/FIXMEs

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- **Status:** Implementation complete, ready for Codex validation
- **Test evidence:** 32/32 MEU-99 tests pass, 1232/1232 full regression
- **Quality gates:** pyright 0 errors, ruff 0 issues, 0 TODOs
- **Next steps:** Codex validation → handoff approval → post-MEU deliverables
