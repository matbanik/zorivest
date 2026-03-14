# Task — IBKR & CSV Import Foundation (MEU-96 + MEU-99)

## MEU-96: IBKR FlexQuery Adapter

- [x] Add `BrokerType`, `AssetClass`, `ImportStatus` enums to `enums.py`
- [x] Create `RawExecution`, `ImportError`, `ImportResult` Pydantic models in `import_types.py`
- [x] Add `BrokerFileAdapter`, `CSVBrokerAdapter` Protocols to existing `ports.py`
- [x] Write MEU-96 tests in Red phase (`test_ibkr_flexquery.py`) — ~25 tests
- [x] Implement `IBKRFlexQueryAdapter` in `ibkr_flexquery.py` — Green phase
- [x] Create MEU-96 handoff (`061-2026-03-13-ibkr-adapter-bpMs50e.md`)

## MEU-99: CSV Import + Broker Auto-Detection

- [x] Write MEU-99 tests in Red phase (`test_csv_import.py` + fixtures in `conftest.py`) — ~30 tests
- [x] Implement `CSVParserBase` ABC in `csv_base.py`
- [x] Implement `ThinkorSwimCSVParser` in `tos_csv.py`
- [x] Implement `NinjaTraderCSVParser` in `ninjatrader_csv.py`
- [x] Implement `ImportService` in `import_service.py`
- [x] Create MEU-99 handoff (`062-2026-03-13-csv-import-bpMs53e.md`)

## Post-MEU Deliverables

- [x] Run MEU gate: `uv run python tools/validate_codebase.py --scope meu`
- [x] Update `meu-registry.md` (add MEU-96, MEU-99 rows)
- [x] Update `BUILD_PLAN.md` (MEU-96/99 status ⬜→✅, summary 58→60)
- [x] Create reflection: `docs/execution/reflections/2026-03-13-ibkr-csv-import-reflection.md`
- [x] Update metrics table: `docs/execution/metrics.md`
- [x] Save session state to `pomera_notes`
- [x] Prepare commit messages
