# Task — Watchlist + Planning MCP (MEU-68, MEU-69)

## MEU-68: Watchlist Entity + Service + API

| task | owner_role | deliverable | validation | status |
|------|-------|-------------|------------|:------:|
| Add `Watchlist` + `WatchlistItem` dataclasses to `entities.py` | coder | AC-1 | `uv run pytest tests/unit/test_entities.py -k watchlist` | [x] |
| Add `WatchlistRepository` Protocol to `ports.py` | coder | AC-6 | `uv run pyright packages/core/` | [x] |
| Add `SqlAlchemyWatchlistRepository` to `repositories.py` | coder | AC-6 | `uv run pytest tests/integration/test_repositories.py -k watchlist` | [-] deferred to Phase 2 |
| Add `watchlists` to `SqlAlchemyUnitOfWork.__enter__` in `unit_of_work.py` | coder | AC-7 | `uv run pyright packages/infrastructure/` | [-] deferred to Phase 2 |
| Create `watchlist_service.py` with CRUD + item management | coder | AC-2, AC-3, AC-4, AC-5 | `uv run pytest tests/unit/test_watchlist_service.py` | [x] |
| Create `routes/watchlists.py` with 7 REST endpoints | coder | AC-8 | `uv run pytest tests/unit/test_api_watchlists.py` | [x] |
| Add router import + lifespan `app.state.watchlist_service` + router registration in `main.py` | coder | AC-10 | `uv run pytest tests/unit/test_api_watchlists.py` | [x] |
| Add `get_watchlist_service` provider in `dependencies.py` | coder | AC-10 | `uv run pytest tests/unit/test_api_watchlists.py` | [x] |
| Add `_InMemoryWatchlistRepo` + `StubUnitOfWork.watchlists` in `stubs.py` | coder | AC-10 | `uv run pytest tests/unit/test_api_watchlists.py` | [x] |
| Write entity tests in `test_entities.py` (~5 tests) | tester | AC-1 | `uv run pytest tests/unit/test_entities.py -k watchlist -v` | [x] |
| Write `test_watchlist_service.py` (~25 tests) | tester | AC-2–AC-5, AC-9 | `uv run pytest tests/unit/test_watchlist_service.py -v` | [x] |
| Write `test_api_watchlists.py` (~14 tests) | tester | AC-8, AC-10 | `uv run pytest tests/unit/test_api_watchlists.py -v` | [x] |
| Write repo integration tests in `test_repositories.py` (~4 tests) | tester | AC-6 | `uv run pytest tests/integration/test_repositories.py -k watchlist -v` | [-] deferred to Phase 2 |
| TDD cycle: RED → GREEN → REFACTOR | coder | All ACs | Full regression: `uv run pytest tests/ -v` | [x] |
| Create handoff `058-2026-03-12-watchlist-entity-bp03s3.1.md` | reviewer | Handoff | File exists in `.agent/context/handoffs/` | [x] |

## MEU-69: Watchlist MCP Tools

| task | owner_role | deliverable | validation | status |
|------|-------|-------------|------------|:------:|
| Add 5 watchlist tools to `planning-tools.ts` | coder | AC-1–AC-5 | `cd mcp-server && npx vitest run tests/planning-tools.test.ts` | [x] |
| Add watchlist tool entries to `seed.ts` `trade-planning` toolset | coder | AC-6 | `cd mcp-server && npx tsc --noEmit` | [x] |
| Extend `planning-tools.test.ts` with ~10 tests | tester | AC-1–AC-5 | `cd mcp-server && npx vitest run tests/planning-tools.test.ts --reporter=verbose` | [x] |
| TDD cycle: RED → GREEN → REFACTOR | coder | All ACs | Full MCP regression: `cd mcp-server && npx vitest run` | [x] |
| Create handoff `059-2026-03-12-watchlist-mcp-bp05ds5d.md` | reviewer | Handoff | File exists in `.agent/context/handoffs/` | [x] |

## Canonical Doc Updates

| task | owner_role | deliverable | validation | status |
|------|-------|-------------|------------|:------:|
| Add watchlist route entries to `04-rest-api.md` | coder | AC-7 (MEU-69) | `rg -c watchlist docs/build-plan/04-rest-api.md` returns > 0 | [x] |
| Add 5 watchlist MCP tool specs to `05d-mcp-trade-planning.md` | coder | AC-7 (MEU-69) | `rg -c watchlist docs/build-plan/05d-mcp-trade-planning.md` returns > 0 | [x] |
| Update `05-mcp-server.md` toolset inventory (trade-planning 2→7, total 68→73) | coder | Canon sync | `rg "trade-planning.*7" docs/build-plan/05-mcp-server.md` | [x] |

## Post-MEU Deliverables

| task | owner_role | deliverable | validation | status |
|------|-------|-------------|------------|:------:|
| Run MEU gate | tester | Quality gate pass | `uv run pytest tests/ -q` (1018 passed) | [x] |
| Update `meu-registry.md` with MEU-68 + MEU-69 rows | coder | Registry rows | `rg "MEU-68\|MEU-69" .agent/context/meu-registry.md` | [x] |
| Update `BUILD_PLAN.md` status for MEU-68 + MEU-69 | coder | Status ✅ | `rg -c "✅" docs/BUILD_PLAN.md` count +2 | [x] |
| Run full regression | tester | All tests pass | `uv run pytest tests/ -v` (1018 passed), `npx vitest run` (160 passed) | [x] |
| Create reflection file | reviewer | Reflection doc | `docs/execution/reflections/2026-03-13-watchlist-planning-mcp-reflection.md` | [x] |
| Update metrics table | coder | Metrics row | `rg "watchlist" docs/execution/metrics.md` | [x] |
| Save session state to pomera_notes | coder | Note saved | pomera_notes ID 490 | [x] |
| Prepare commit messages | coder | Commit messages | See git commit below | [x] |
