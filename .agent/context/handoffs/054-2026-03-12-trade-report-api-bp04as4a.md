# MEU-53: TradeReport API Routes

## Task

- **Date:** 2026-03-12
- **Task slug:** trade-report-api
- **Owner role:** coder
- **Scope:** REST API routes for TradeReport CRUD, dependency provider, app wiring

## Inputs

- User request: Implement report API routes per build plan
- Specs/docs referenced: `docs/build-plan/04a-api-trades.md` L126-151
- Constraints: TDD-first, nested under `/api/v1/trades/{exec_id}/report` (singular), error mapping: 404 for not found, 409 for duplicate

## Coder Output

- Changed files:
  - `packages/api/src/zorivest_api/dependencies.py` — +`get_report_service` provider
  - `packages/api/src/zorivest_api/routes/reports.py` — **[NEW]** POST/GET/PUT/DELETE on `/{exec_id}/report` with request/response schemas
  - `packages/api/src/zorivest_api/main.py` — +`report_router` import/registration, +`ReportService` in lifespan
  - `tests/unit/test_api_reports.py` — **[NEW]** 9 tests (create 201/404/409, get 200/404, update 200/404, delete 204/404)
- Design notes: Routes use singular `/report` (one report per trade). Error mapping: ValueError with "not found" → 404, "already exists" → 409. Response uses `_to_response()` helper for entity→dict conversion.
- Commands run: `uv run pytest tests/unit/test_api_reports.py -v`
- Results: 9 passed

## Tester Output

- Commands run: `uv run pytest tests/ -v --tb=short -q`
- Pass/fail matrix: 927/927 passed, 1 skipped
- Coverage/test gaps: MCP tools deferred to follow-up session
- Evidence bundle location: This handoff
- FAIL_TO_PASS / PASS_TO_PASS result: RED confirmed (ImportError: `get_report_service` before implementation)

## Final Summary

- Status: PARTIAL — API routes complete, MCP tools deferred to follow-up MEU
- Next steps: Implement MCP report tools in a separate session, then handoff to Codex for final validation
