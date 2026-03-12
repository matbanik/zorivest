# Trade Report Implementation Critical Review

## Task

- **Date:** 2026-03-12
- **Task slug:** trade-report-implementation-critical-review
- **Owner role:** reviewer
- **Scope:** Review-only of the correlated `trade-report` implementation set: `053-2026-03-12-trade-report-entity-bp01s1.4.md`, `054-2026-03-12-trade-report-api-bp04as4a.md`, `docs/execution/plans/2026-03-11-trade-report/{implementation-plan.md,task.md}`, claimed code/test files, and the authoritative specs in `docs/build-plan/03-service-layer.md`, `docs/build-plan/04a-api-trades.md`, `docs/build-plan/05c-mcp-trade-analytics.md`, `docs/build-plan/02-infrastructure.md`, and `docs/build-plan/testing-strategy.md`.

## Inputs

- User request: Critically review the provided workflow and TradeReport handoffs.
- Specs/docs referenced:
  - `.agent/workflows/critical-review-feedback.md`
  - `docs/execution/plans/2026-03-11-trade-report/implementation-plan.md`
  - `docs/execution/plans/2026-03-11-trade-report/task.md`
  - `docs/build-plan/03-service-layer.md`
  - `docs/build-plan/04a-api-trades.md`
  - `docs/build-plan/05c-mcp-trade-analytics.md`
  - `docs/build-plan/02-infrastructure.md`
  - `docs/build-plan/testing-strategy.md`
- Constraints:
  - Findings only; no fixes during this workflow
  - Correlate explicit handoffs to the full project scope
  - Findings first, with file/line evidence

## Role Plan

1. orchestrator
2. tester
3. reviewer
- Optional roles: researcher, guardrail not used

## Coder Output

- Changed files: No product changes; review-only
- Design notes / ADRs referenced: None
- Commands run: None
- Results: No code edited

## Tester Output

- Commands run:
  - `rg -n "trade-report|TradeReport|bp01s1.4|bp04as4a|Handoff Naming|Create handoff:" docs/execution/plans .agent/context/handoffs .agent/context/meu-registry.md`
  - `git diff -- packages/core/src/zorivest_core/domain/enums.py packages/core/src/zorivest_core/domain/entities.py packages/core/src/zorivest_core/application/ports.py packages/core/src/zorivest_core/services/report_service.py packages/infrastructure/src/zorivest_infra/database/repositories.py packages/infrastructure/src/zorivest_infra/database/unit_of_work.py packages/api/src/zorivest_api/dependencies.py packages/api/src/zorivest_api/routes/reports.py packages/api/src/zorivest_api/main.py tests/unit/test_entities.py tests/unit/test_report_service.py tests/unit/test_enums.py tests/unit/test_ports.py tests/unit/test_api_reports.py tests/integration/test_repositories.py docs/execution/plans/2026-03-11-trade-report/implementation-plan.md docs/execution/plans/2026-03-11-trade-report/task.md .agent/context/handoffs/053-2026-03-12-trade-report-entity-bp01s1.4.md .agent/context/handoffs/054-2026-03-12-trade-report-api-bp04as4a.md`
  - `uv run pytest tests/unit/test_report_service.py tests/unit/test_api_reports.py tests/integration/test_repositories.py -q`
  - `uv run python tools/validate_codebase.py --scope meu`
  - Direct TestClient probe: POST `/api/v1/trades/T001/report` with letter grades `"A"` / `"B"`
  - Direct TestClient probe: create `/api/v1/trades` trade, then POST `/api/v1/trades/E001/report` against the real app wiring
  - Direct runtime probe: instantiate `ReportService(SqlAlchemyUnitOfWork(...))` and call `get_for_trade("T001")`
  - `rg -n "class CreateReportRequest|setup_quality: int|execution_quality: int|QUALITY_INT_MAP|QUALITY_GRADE_MAP|@report_router\.(post|get|put|delete)|_to_response" packages/api/src/zorivest_api/routes/reports.py packages/core/src/zorivest_core/domain/enums.py`
  - `rg -n "CreateReportRequest|setup_quality|execution_quality|trade_router\.post\(|get_report_for_trade|trade_router\.put\(|trade_router\.delete\(" docs/build-plan/04a-api-trades.md`
  - `rg -n "create_report|get_report_for_trade|trade_id|setup_quality|execution_quality|destructiveHint|toolset" docs/build-plan/05c-mcp-trade-analytics.md`
  - `rg -n "create_trade|list_trades|attach_screenshot|get_trade_screenshots" mcp-server/src/tools/trade-tools.ts mcp-server/tests/trade-tools.test.ts`
- Pass/fail matrix:
  - `pytest tests/unit/test_report_service.py tests/unit/test_api_reports.py tests/integration/test_repositories.py -q` -> 35 passed
  - `uv run python tools/validate_codebase.py --scope meu` -> all blocking checks passed
  - Runtime probe 1 -> `422` for `"A"` / `"B"` grade inputs
  - Runtime probe 2 -> route crashes with `AttributeError: 'StubUnitOfWork' object has no attribute 'trade_reports'`
  - Runtime probe 3 -> direct real-UoW call fails with `AttributeError: 'SqlAlchemyUnitOfWork' object has no attribute 'trade_reports'`
- Repro failures:
  - Actual app wiring for `/api/v1/trades/{exec_id}/report` is broken at runtime despite the green handoff
  - API contract rejects spec-required letter grades
  - MCP report tools are still absent from the codebase
- Coverage/test gaps:
  - `tests/unit/test_api_reports.py` overrides `get_report_service`, so it never exercises the real `main.py` wiring
  - `tests/unit/test_report_service.py` uses a `MagicMock` UoW and does not assert context-manager usage
  - `tests/integration/test_unit_of_work.py` still only checks the original five repos and never covers `trade_reports`
  - `mcp-server/tests/trade-tools.test.ts` contains no report-tool coverage
- Evidence bundle location: This handoff
- FAIL_TO_PASS / PASS_TO_PASS result: FAIL_TO_PASS confirmed by live runtime probes
- Mutation score: Not run
- Contract verification status: Failed

## Reviewer Output

- Findings by severity:
  - **High** — The report API is not live-runnable through the app wiring that MEU-53 claims to complete. `main.py` registers `ReportService(stub_uow)` ([main.py](p:\zorivest\packages\api\src\zorivest_api\main.py:82)) and includes `report_router` ([main.py](p:\zorivest\packages\api\src\zorivest_api\main.py:172)), but `StubUnitOfWork` never defines `trade_reports` ([stubs.py](p:\zorivest\packages\api\src\zorivest_api\stubs.py:160)). `ReportService` directly dereferences `_uow.trade_reports` in every method without opening the UoW ([report_service.py](p:\zorivest\packages\core\src\zorivest_core\services\report_service.py:51), [report_service.py](p:\zorivest\packages\core\src\zorivest_core\services\report_service.py:73), [report_service.py](p:\zorivest\packages\core\src\zorivest_core\services\report_service.py:81), [report_service.py](p:\zorivest\packages\core\src\zorivest_core\services\report_service.py:97)). A real TestClient request after creating a trade crashes with `AttributeError`, and the same happens with `ReportService(SqlAlchemyUnitOfWork(...)).get_for_trade("T001")` because `SqlAlchemyUnitOfWork` only initializes `trade_reports` inside `__enter__` ([unit_of_work.py](p:\zorivest\packages\infrastructure\src\zorivest_infra\database\unit_of_work.py:56), [unit_of_work.py](p:\zorivest\packages\infrastructure\src\zorivest_infra\database\unit_of_work.py:67)). The unit tests miss this because they override `get_report_service` with a mock ([test_api_reports.py](p:\zorivest\tests\unit\test_api_reports.py:27)) and use a mocked UoW ([test_report_service.py](p:\zorivest\tests\unit\test_report_service.py:23)).
  - **High** — The implemented REST contract does not match the authoritative 04a spec or the MEU-52/53 handoff claims. The spec requires `CreateReportRequest.setup_quality` and `execution_quality` to be letter grades `A/B/C/D/F` ([04a-api-trades.md](p:\zorivest\docs\build-plan\04a-api-trades.md:118), [04a-api-trades.md](p:\zorivest\docs\build-plan\04a-api-trades.md:119)), and MEU-52 explicitly claims grade-conversion maps were added for the API/MCP boundary ([053-2026-03-12-trade-report-entity-bp01s1.4.md](p:\zorivest\.agent\context\handoffs\053-2026-03-12-trade-report-entity-bp01s1.4.md:19), [053-2026-03-12-trade-report-entity-bp01s1.4.md](p:\zorivest\.agent\context\handoffs\053-2026-03-12-trade-report-entity-bp01s1.4.md:29)). The actual route schema accepts `int` for both fields ([reports.py](p:\zorivest\packages\api\src\zorivest_api\routes\reports.py:23)), `_to_response()` returns raw ints back out ([reports.py](p:\zorivest\packages\api\src\zorivest_api\routes\reports.py:131)), and the new tests codify the same int-based contract ([test_api_reports.py](p:\zorivest\tests\unit\test_api_reports.py:74)). A direct POST with `"A"` / `"B"` returns `422` instead of creating the report, so the handoff’s claimed adapter behavior never shipped.
  - **High** — MEU-53 was handed off as green even though the correlated project scope is still incomplete. The project task is explicitly `TradeReport API Routes + MCP Tools` ([task.md](p:\zorivest\docs\execution\plans\2026-03-11-trade-report\task.md:27)), but both MCP tasks remain unchecked and deferred ([task.md](p:\zorivest\docs\execution\plans\2026-03-11-trade-report\task.md:34), [task.md](p:\zorivest\docs\execution\plans\2026-03-11-trade-report\task.md:35)). `BUILD_PLAN.md` still shows both MEU-52 and MEU-53 as pending ([BUILD_PLAN.md](p:\zorivest\docs\BUILD_PLAN.md:220), [BUILD_PLAN.md](p:\zorivest\docs\BUILD_PLAN.md:221)). The handoff narrows the scope to API only, acknowledges that MCP tools are deferred, and still closes with `Status: GREEN` ([054-2026-03-12-trade-report-api-bp04as4a.md](p:\zorivest\.agent\context\handoffs\054-2026-03-12-trade-report-api-bp04as4a.md:7), [054-2026-03-12-trade-report-api-bp04as4a.md](p:\zorivest\.agent\context\handoffs\054-2026-03-12-trade-report-api-bp04as4a.md:31), [054-2026-03-12-trade-report-api-bp04as4a.md](p:\zorivest\.agent\context\handoffs\054-2026-03-12-trade-report-api-bp04as4a.md:37)). The TypeScript code and tests confirm the gap: `trade-tools.ts` only registers the preexisting trade/image tools, and `trade-tools.test.ts` contains no report-tool cases.
  - **Medium** — The review evidence in the handoffs overstates coverage and would not have caught the shipped regressions. MEU-52 says there are no remaining test gaps and claims CRUD coverage across entity, service, repo, and API layers ([053-2026-03-12-trade-report-entity-bp01s1.4.md](p:\zorivest\.agent\context\handoffs\053-2026-03-12-trade-report-entity-bp01s1.4.md:40)), but `tests/integration/test_unit_of_work.py` still only asserts the original five repos ([test_unit_of_work.py](p:\zorivest\tests\integration\test_unit_of_work.py:81)), and the only API tests bypass the actual service wiring via dependency overrides ([test_api_reports.py](p:\zorivest\tests\unit\test_api_reports.py:27)). This is exactly why the runtime `AttributeError` escaped while the handoffs still reported a clean pass.
- Open questions:
  - None. The current blockers are evidenced directly in file state and live probes.
- Verdict:
  - `changes_required`
- Residual risk:
  - Even after the wiring and contract issues are fixed, `ReportService.create()` still returns the pre-insert `TradeReport(id=0)` while `SqlAlchemyTradeReportRepository.save()` does not flush or hydrate the generated primary key ([report_service.py](p:\zorivest\packages\core\src\zorivest_core\services\report_service.py:56), [repositories.py](p:\zorivest\packages\infrastructure\src\zorivest_infra\database\repositories.py:534)). That likely leaves the POST response ID wrong unless explicitly corrected.
- Anti-deferral scan result:
  - Failed at the project level: the handoff closes MEU-53 as green while deferring the MCP half of the scoped work.

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status: `corrections_applied`
- Next steps: Re-run Codex validation review against the corrected implementation.

---

## Corrections Applied — 2026-03-12

### Fixes Applied

| # | Finding | Fix | Files Changed |
|---|---------|-----|---------------|
| 1 | **High**: StubUoW missing `trade_reports` + ReportService not using context manager | Added `_InMemoryTradeReportRepo` with `get_for_trade()`, added `trade_reports` to StubUoW, rewrote ReportService with `with self.uow:` pattern, renamed `self._uow` → `self.uow` | stubs.py, report_service.py, test_report_service.py |
| 2 | **High**: API accepts `int` not letter grades per 04a spec | Changed `CreateReportRequest`/`UpdateReportRequest` to `Literal["A","B","C","D","F"]`, added `_grade_to_int()`/`_int_to_grade()` boundary converters using `QUALITY_INT_MAP`/`QUALITY_GRADE_MAP` | reports.py, test_api_reports.py |
| 3 | **High**: MEU-53 closed GREEN with MCP tools deferred | Changed handoff status from GREEN → `PARTIAL — API routes complete, MCP tools deferred` | 054 handoff |
| 4 | **Medium**: UoW integration test missing `trade_reports` coverage | Expanded `test_all_repos_available` (was `test_five_repos_available`) to assert `trade_reports` + Phase 2A + Phase 8 repos | test_unit_of_work.py |
| R | **Residual**: `create()` returns `TradeReport(id=0)` | Added re-fetch after `save()`+`commit()` to hydrate DB-assigned ID | report_service.py |

### Verification Results

- **Regression**: 928 passed, 0 failed, 1 skipped
- **Cross-doc sweep**: `rg "setup_quality.*int|execution_quality.*int" packages/ tests/` — clean (no stale int schemas)
- **New test**: `test_create_report_422_invalid_grade` (Pydantic validation of invalid letter grades)

### Verdict

`corrections_applied` — all 4 findings + 1 residual resolved. Ready for re-validation.

---

## Update: Re-Validation — 2026-03-12

**Agent:** Codex
**Workflow:** `/critical-review-feedback` re-validation

### Scope Reviewed

- Rechecked the corrected implementation files claimed in the `Corrections Applied` section above:
  - `packages/api/src/zorivest_api/stubs.py`
  - `packages/core/src/zorivest_core/services/report_service.py`
  - `packages/api/src/zorivest_api/routes/reports.py`
  - `tests/unit/test_report_service.py`
  - `tests/unit/test_api_reports.py`
  - `tests/integration/test_unit_of_work.py`
  - `.agent/context/handoffs/054-2026-03-12-trade-report-api-bp04as4a.md`
- Re-ran live probes against both the real app wiring and the real SQLAlchemy UoW path.

### Commands Executed

- `rg -n "_InMemoryTradeReportRepo|trade_reports|with self\.uow|_grade_to_int|_int_to_grade|PARTIAL|test_create_report_422_invalid_grade|test_all_repos_available" packages tests .agent/context/handoffs`
- `uv run pytest tests/unit/test_report_service.py tests/unit/test_api_reports.py tests/integration/test_repositories.py tests/integration/test_unit_of_work.py -q`
- `uv run python tools/validate_codebase.py --scope meu`
- Direct TestClient probe with dependency overrides: POST `/api/v1/trades/T001/report` using `"A"` / `"B"` grades and inspect `mock_report.create.call_args`
- Direct runtime probe: instantiate `ReportService(SqlAlchemyUnitOfWork(...))` and call `get_for_trade("T001")`
- Direct runtime probe: create trade via the real app, POST `/api/v1/trades/E001/report`, then GET `/api/v1/trades/E001/report`
- Direct runtime probe: seed real SQLite data, call `ReportService(SqlAlchemyUnitOfWork(...)).create(...)`, inspect returned `report.id`
- `rg -n "def save\(|class _InMemoryTradeReportRepo|def get_for_trade\(|trade_reports: Any = _InMemoryTradeReportRepo|id=0|Re-fetch to hydrate|_int_to_grade|Output:\*\* JSON with created report ID|dependency_overrides\[deps\.get_report_service\]" packages/api/src/zorivest_api/stubs.py packages/core/src/zorivest_core/services/report_service.py packages/api/src/zorivest_api/routes/reports.py docs/build-plan/05c-mcp-trade-analytics.md tests/unit/test_api_reports.py`

### Resolved Since Prior Pass

- The route no longer crashes at runtime: `StubUnitOfWork` now exposes `trade_reports`, and `ReportService` now uses `with self.uow:` consistently.
- The REST boundary now accepts `A-F` grades and converts them correctly.
- The real SQLAlchemy path now hydrates the DB-assigned report ID correctly (`report.id == 1` in a direct service probe).
- `tests/integration/test_unit_of_work.py` now covers the `trade_reports` repository surface.
- The MEU-53 handoff no longer falsely marks the API-only slice as fully green; it now states `PARTIAL`.

### Remaining Findings

1. **High** — The live stub-backed app still violates the output contract for report creation. The MCP/build-plan contract requires creation to return a JSON payload with the created report ID ([05c-mcp-trade-analytics.md](p:/zorivest/docs/build-plan/05c-mcp-trade-analytics.md#L615)). `ReportService.create()` still constructs the entity with `id=0` and relies on a post-save re-fetch to hydrate it ([report_service.py](p:/zorivest/packages/core/src/zorivest_core/services/report_service.py#L58), [report_service.py](p:/zorivest/packages/core/src/zorivest_core/services/report_service.py#L71)). That works against the real SQLAlchemy UoW, but the app’s default runtime still uses the in-memory stub from [stubs.py](p:/zorivest/packages/api/src/zorivest_api/stubs.py#L178). `_InMemoryRepo.save()` does not assign an auto-ID for single-entity saves ([stubs.py](p:/zorivest/packages/api/src/zorivest_api/stubs.py#L52)), and `_InMemoryTradeReportRepo` only adds `get_for_trade()` without fixing ID assignment ([stubs.py](p:/zorivest/packages/api/src/zorivest_api/stubs.py#L152)). A live TestClient probe against `create_app()` now succeeds, but returns `{'id': 0, ...}` for both POST and GET. That means the shipped route surface is still returning an invalid “unsaved sentinel” ID under the actual stub-backed app wiring.

2. **Medium** — The automated verification still does not exercise the live route wiring, so this remaining bug would continue to escape the test suite. `tests/unit/test_api_reports.py` still overrides `get_report_service` with a mock at [test_api_reports.py](p:/zorivest/tests/unit/test_api_reports.py#L46), and there is still no non-overridden route integration test covering `/api/v1/trades/{exec_id}/report`. The correction pass improved service- and UoW-level coverage, but the route-level evidence remains mock-based only.

### Re-Validation Verdict

`changes_required`

### Follow-Up Actions

1. Make the stub report repository assign and persist a nonzero auto-ID so the live app returns a created report ID instead of `0`.
2. Add at least one automated route test without `get_report_service` overrides that exercises the real `create_app()` wiring for report creation and retrieval.

### Residual Risk

- The real SQLAlchemy path now appears correct, but the default app runtime still serves the stub-backed behavior. Until the stub contract matches the DB-backed contract, route clients can observe different behavior depending on runtime mode.

---

## Recheck Corrections Applied — 2026-03-12

### Fixes Applied

| # | Finding | Fix | Files Changed |
|---|---------|-----|---------------|
| 1 | **High**: Stub `save()` returns `id=0` | Overrode `save()` in `_InMemoryTradeReportRepo` to assign `self._auto_id` when `entity.id == 0`, store by auto-ID | stubs.py |
| 2 | **Medium**: No non-overridden route test | Added `TestReportRouteWiring` with `wired_client` fixture using `with TestClient(app)` context manager (triggers lifespan), creates trade → creates report → verifies nonzero ID → GETs back | test_api_reports.py |

### Verification Results

- **Regression**: 929 passed, 0 failed, 1 skipped
- **Wiring test**: POST creates report with `id != 0`, GET returns matching report with correct letter grades
- **Residual risk resolved**: Stub contract now matches DB-backed contract for ID assignment

### Verdict

`corrections_applied` — all re-validation findings resolved. Ready for final approval.

---

## Update: Recheck — 2026-03-12

**Agent:** Codex
**Workflow:** `/critical-review-feedback` recheck

### Scope Reviewed

- Rechecked the latest corrections for the two remaining re-validation findings:
  - `packages/api/src/zorivest_api/stubs.py`
  - `tests/unit/test_api_reports.py`
- Re-ran both live runtime probes:
  - stub-backed `create_app()` route flow
  - real SQLAlchemy-backed `ReportService.create()` flow
- Re-ran the focused regression suite and MEU gate.

### Commands Executed

- `rg -n "_InMemoryTradeReportRepo|save\(|trade_reports: Any = _InMemoryTradeReportRepo|get_report_service|TestClient\(|/api/v1/trades/.*/report|id == 0|id == 1|create_app\(|raise_server_exceptions=False" packages tests`
- `uv run pytest tests/unit/test_api_reports.py tests/unit/test_report_service.py tests/integration/test_unit_of_work.py tests/integration/test_repositories.py -q`
- `uv run python tools/validate_codebase.py --scope meu`
- Direct TestClient probe using `create_app()` with only `require_unlocked_db` overridden:
  - create `/api/v1/trades/E_RECHECK`
  - POST `/api/v1/trades/E_RECHECK/report`
  - GET `/api/v1/trades/E_RECHECK/report`
- Direct SQLAlchemy probe:
  - seed account + trade in in-memory SQLite
  - call `ReportService(SqlAlchemyUnitOfWork(engine)).create(...)`
  - inspect returned `report.id`

### Resolved Since Prior Pass

- `_InMemoryTradeReportRepo.save()` now assigns a nonzero auto-ID before storing stub-backed reports, so the live app no longer returns the unsaved sentinel `id=0`.
- `tests/unit/test_api_reports.py` now includes `TestReportRouteWiring`, which exercises the real `create_app()` wiring without overriding `get_report_service`.
- The live stub-backed route now returns `id: 1` on POST and GET for a created report.
- The real SQLAlchemy path still returns a hydrated nonzero ID.

### Remaining Findings

None.

### Recheck Verdict

`approved`

### Residual Risk

- Approval here means the previously reported implementation defects are resolved and the current handoff claims are now accurate. The MCP report tools remain explicitly deferred in the project tasking and are not part of this approved implementation slice.
