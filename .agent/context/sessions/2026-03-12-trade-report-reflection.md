# Reflection — Trade Report Entity + API (MEU-52/53)

> Date: 2026-03-12
> Project: `trade-report`
> MEUs: 52 (entity/service), 53 (API routes — PARTIAL)

## What Went Well

- **TDD discipline held**: All test suites written RED-first with clear FIC traceability
- **Grade conversion pattern**: Clean boundary separation — API accepts letter grades (A-F), domain stores ints (1-5), with `QUALITY_INT_MAP`/`QUALITY_GRADE_MAP` at the enum layer
- **Corrections workflow**: Two Codex review passes caught real runtime issues (stub wiring, ID hydration, grade contract) that unit tests couldn't surface

## What Needed Correction

1. **StubUnitOfWork gap**: Initial implementation forgot to add `trade_reports` attribute and missed auto-ID assignment for single-entity saves
2. **Context manager pattern**: `ReportService` used `self._uow.method()` directly instead of the established `with self.uow:` pattern
3. **API contract mismatch**: Initial routes accepted `int` grades instead of the spec-mandated `Literal["A","B","C","D","F"]`
4. **Mock-heavy API tests**: All API tests overrode `get_report_service` — missed that real wiring was broken. Fixed by adding `TestReportRouteWiring` with `with TestClient(app)` context manager

## Lessons Learned

- **Always add new repos to StubUoW** when adding domain repositories — the stub is the default runtime
- **Use `with TestClient(app)` not `TestClient(app)`** to trigger FastAPI lifespan startup
- **At least one API test per feature should skip service overrides** to catch wiring bugs
- **Check the spec for field types** — `04a-api-trades.md` specifies `Literal["A"..."F"]`, not `int`

## Test Counts

| Suite | Count |
|-------|-------|
| Full regression | 929 passed, 1 skipped |
| Report service | 9 |
| Report API (mocked) | 10 |
| Report API (wired) | 1 |
| UoW integration | 7 |

## Deferred Work

- MEU-53 MCP tools: `create_report`, `get_report_for_trade` — requires TypeScript implementation
- MEU-53 TypeScript checks: `tsc --noEmit`, `npm run build` — blocked on MCP tools
