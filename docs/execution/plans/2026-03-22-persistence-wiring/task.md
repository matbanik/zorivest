# MEU-90a — persistence-wiring Close-Out Task Tracker

> Build plan: `09a-persistence-integration.md` §49.0
> Continuation of: `081-2026-03-19-persistence-wiring-meu90a.md` (status: `ready_for_review`)
> Project folder: `docs/execution/plans/2026-03-22-persistence-wiring/`

---

## Implementation

- [x] T1 — Remove `StubUnitOfWork`, `_InMemoryRepo`, `_InMemoryTradeReportRepo`, `_InMemoryTradePlanRepo`, `_InMemoryWatchlistRepo`, `_InMemoryPipelineRunRepo`, `_StubQuery`, `_StubSession` from `stubs.py`
  - owner_role: coder
  - deliverable: Pruned `stubs.py` (197 lines, 5 retained stubs only)
  - validation: `from zorivest_api.stubs import StubUnitOfWork` → `ImportError` ✅

- [x] T2 — Convert `test_watchlist_service.py` fixture to real in-memory SQLite `SqlAlchemyUnitOfWork`
  - owner_role: coder
  - deliverable: Fixture uses `create_engine_with_wal("sqlite:///:memory:")` + `Base.metadata.create_all`
  - validation: `uv run pytest tests/unit/test_watchlist_service.py -v` — 25 passed ✅

- [x] T3 — Move `McpGuardService` from `stubs.py` to `packages/api/src/zorivest_api/services/mcp_guard.py`; update `main.py` import
  - owner_role: coder
  - deliverable: New `mcp_guard.py` file; `stubs.py` no longer defines `McpGuardService`
  - validation: `rg "class McpGuardService" stubs.py` → 0 matches; 1432 unit + 144 integration tests pass ✅

- [~] T4 — Update `known-issues.md`
  - note: `.agent/context/known-issues.md` does not exist in this repo; pre-existing gap logged in review handoff. Skipped — does not block MEU completion.

- [x] T5 — Update `meu-registry.md`: MEU-90a `✅ approved`
  - owner_role: coder
  - deliverable: Updated registry
  - validation: MEU-90a row shows ✅ approved ✅

- [x] T6 — Update `docs/BUILD_PLAN.md`: MEU-90a `✅`
  - owner_role: coder
  - deliverable: Updated hub
  - validation: MEU-90a row shows ✅ ✅

---

## Verification

- [x] T7 — Full regression: `uv run pytest tests/ --tb=no -q` → 0 failures
  - owner_role: tester
  - result: 1432 unit + 144 integration = 1576 passed, 1 skipped ✅

- [x] T8 — Lint + types: `uv run python tools/validate_codebase.py --scope meu` → all blocking checks passed
  - owner_role: tester
  - result: pyright PASS, ruff PASS, pytest PASS, tsc PASS, eslint PASS ✅

---

## Handoff

- [x] T9 — Append `Execution Complete` section to `.agent/context/handoffs/2026-03-22-persistence-wiring-plan-critical-review.md`
  - owner_role: reviewer
  - deliverable: Handoff updated with execution results and final verdict
