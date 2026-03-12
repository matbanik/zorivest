# MEU-52: TradeReport Entity + Service

## Task

- **Date:** 2026-03-12
- **Task slug:** trade-report-entity-service
- **Owner role:** coder
- **Scope:** TradeReport entity, enums, ports, repository, UoW wiring, ReportService

## Inputs

- User request: Implement TradeReport entity and service layer per build plan
- Specs/docs referenced: `docs/build-plan/01-domain-layer.md`, `docs/build-plan/03-service-layer.md` L387-409, `docs/build-plan/04a-api-trades.md` L126-151
- Constraints: TDD-first, method names from 04a (authoritative): create, get_for_trade, update, delete

## Coder Output

- Changed files:
  - `packages/core/src/zorivest_core/domain/enums.py` — +`QualityGrade` (A-F, StrEnum), +`EmotionalState` (9 values), +`QUALITY_INT_MAP`, +`QUALITY_GRADE_MAP`
  - `packages/core/src/zorivest_core/domain/entities.py` — +`TradeReport` dataclass (10 fields), `Trade.report` type updated to `Optional[TradeReport]`
  - `packages/core/src/zorivest_core/application/ports.py` — +`TradeReportRepository` Protocol (get, save, get_for_trade, update, delete), +`UoW.trade_reports`
  - `packages/infrastructure/src/zorivest_infra/database/repositories.py` — +`SqlAlchemyTradeReportRepository` with `_report_to_model`/`_model_to_report` mappers
  - `packages/infrastructure/src/zorivest_infra/database/unit_of_work.py` — +`trade_reports` attribute + `__enter__` wiring
  - `packages/core/src/zorivest_core/services/report_service.py` — **[NEW]** `ReportService` with create/get_for_trade/update/delete
  - `tests/unit/test_entities.py` — +14 tests (TradeReport, QualityGrade, EmotionalState, maps, Trade.report type)
  - `tests/unit/test_report_service.py` — **[NEW]** 9 tests (create, get_for_trade, update, delete + error cases)
  - `tests/integration/test_repositories.py` — +4 tests (CRUD + get_for_trade FK lookup)
  - `tests/unit/test_enums.py` — Module integrity: 15 → 17 enums
  - `tests/unit/test_ports.py` — Module integrity: 13 → 14 protocols
- Design notes: EmotionalState uses 9-value superset merging MCP + GUI specs. QualityGrade uses StrEnum A-F with separate integer conversion maps. ReportService uses `dataclasses.replace()` for update.
- Commands run: `uv run pytest tests/unit/test_entities.py tests/unit/test_report_service.py tests/integration/test_repositories.py -v`
- Results: 55 passed

## Tester Output

- Commands run: `uv run pytest tests/ -v --tb=short -q`
- Pass/fail matrix: 927/927 passed, 1 skipped
- Coverage/test gaps: None identified — all 4 CRUD verbs tested at entity, service, repo, and API layers
- Evidence bundle location: This handoff
- FAIL_TO_PASS / PASS_TO_PASS result: RED confirmed (ImportError/ModuleNotFoundError before implementation)

## Final Summary

- Status: GREEN — all 927 tests pass, 0 failures
- Next steps: Handoff to Codex for validation review
