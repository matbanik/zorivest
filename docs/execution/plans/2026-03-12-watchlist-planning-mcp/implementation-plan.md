# Watchlist + Planning MCP Tools — MEU-68, MEU-69

> **Project:** `2026-03-12-watchlist-planning-mcp`
> **MEUs:** MEU-68 (`watchlist`), MEU-69 (`plan-watchlist-mcp`)
> **Build Plan Sections:** Matrix items 33 + 34 (P2 — Planning & Watchlists)

## Background

Watchlists are named collections of tickers for forward-looking research. They complement TradePlans (MEU-66/67, ✅ approved) and share the `trade-planning` MCP toolset. The domain model is fully specified in [domain-model-reference.md](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) L64-76.

SQLAlchemy models (`WatchlistModel`, `WatchlistItemModel`) already exist in [models.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/models.py) L132-157 with proper relationships and cascade deletes. The remaining work is: domain entities, repository, UoW integration, service, REST API, MCP tools, and canonical doc updates.

> [!NOTE]
> **Out of scope:** `POST /api/v1/watchlists/{id}/items/bulk` (bulk add) is deferred to MEU-70. The [gui-actions-index.md](file:///p:/zorivest/docs/build-plan/gui-actions-index.md) L88 status was downgraded from ✅ to 📋 Planned to reflect this.

---

## Proposed Changes

### MEU-68: Watchlist Entity + Service + API

#### [MODIFY] [entities.py](file:///p:/zorivest/packages/core/src/zorivest_core/domain/entities.py)

Add `Watchlist` and `WatchlistItem` frozen dataclasses matching [domain-model-reference.md](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) L64-76.

#### [MODIFY] [ports.py](file:///p:/zorivest/packages/core/src/zorivest_core/application/ports.py)

Add `WatchlistRepository` Protocol interface with: `save`, `get`, `delete`, `update`, `list_all`, `exists_by_name`, `add_item`, `remove_item`, `get_items`.

#### [MODIFY] [repositories.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/repositories.py)

Add `SqlAlchemyWatchlistRepository` implementing the Protocol with CRUD + item management + `exists_by_name()`.

#### [MODIFY] [unit_of_work.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/unit_of_work.py)

Add `watchlists: SqlAlchemyWatchlistRepository` attribute + initialization in `__enter__`.

#### [NEW] [watchlist_service.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/watchlist_service.py)

Standalone `WatchlistService` with:
- `create(name, description)` → Watchlist (rejects duplicate names, 409)
- `get(watchlist_id)` → Watchlist | None
- `list_all(limit, offset)` → list[Watchlist]
- `update(watchlist_id, updates)` → Watchlist
- `delete(watchlist_id)` → None
- `add_ticker(watchlist_id, ticker, notes)` → WatchlistItem (rejects duplicate ticker in same watchlist)
- `remove_ticker(watchlist_id, ticker)` → None
- `get_items(watchlist_id)` → list[WatchlistItem]

#### [NEW] [watchlists.py](file:///p:/zorivest/packages/api/src/zorivest_api/routes/watchlists.py)

REST routes under `/api/v1/watchlists`:
- `POST /` — Create watchlist
- `GET /` — List watchlists (pagination)
- `GET /{id}` — Get watchlist with items
- `PUT /{id}` — Update watchlist metadata
- `DELETE /{id}` — Delete watchlist (cascades items)
- `POST /{id}/items` — Add ticker to watchlist
- `DELETE /{id}/items/{ticker}` — Remove ticker from watchlist

#### [MODIFY] [main.py](file:///p:/zorivest/packages/api/src/zorivest_api/main.py)

Three changes following the existing pattern (see [main.py](file:///p:/zorivest/packages/api/src/zorivest_api/main.py) L36, L83, L174):
1. **Import**: `from zorivest_api.routes.watchlists import watchlist_router` + `from zorivest_core.services.watchlist_service import WatchlistService`
2. **Lifespan**: `app.state.watchlist_service = WatchlistService(stub_uow)` in `lifespan()` (after L83)
3. **Router**: `app.include_router(watchlist_router)` in `create_app()` (after L174)

#### [MODIFY] [dependencies.py](file:///p:/zorivest/packages/api/src/zorivest_api/dependencies.py)

Add `get_watchlist_service` dependency provider (resolves from `request.app.state.watchlist_service`).

#### [MODIFY] [stubs.py](file:///p:/zorivest/packages/api/src/zorivest_api/stubs.py)

Add `_InMemoryWatchlistRepo` (extends `_InMemoryRepo` with auto-ID assignment for Watchlist entities) and add `self.watchlists: Any = _InMemoryWatchlistRepo()` to `StubUnitOfWork.__init__`.

---

### MEU-69: Watchlist MCP Tools

#### [MODIFY] [planning-tools.ts](file:///p:/zorivest/mcp-server/src/tools/planning-tools.ts)

Add 5 watchlist MCP tools to the existing `trade-planning` toolset:
- `create_watchlist` — POST /watchlists
- `list_watchlists` — GET /watchlists
- `get_watchlist` — GET /watchlists/{id}
- `add_to_watchlist` — POST /watchlists/{id}/items
- `remove_from_watchlist` — DELETE /watchlists/{id}/items/{ticker}

All tools use `withMetrics(withGuard(...))` wrapping, `trade-planning` toolset, `alwaysLoaded: false`.

#### [MODIFY] [seed.ts](file:///p:/zorivest/mcp-server/src/toolsets/seed.ts)

Add watchlist tool entries to the `trade-planning` toolset's `tools` array (5 new entries).

> **Tool-cap analysis:** Live `seed.ts` has 18 default-loaded tools (core 4 + discovery 4 + trade-analytics 7 + trade-planning 3). Adding 5 → 23 total, well within the 40-tool Cursor cap. The spec's "37 tools" is an aspirational count for when all planned tools are implemented.

---

### Canonical Doc Updates

#### [MODIFY] [04-rest-api.md](file:///p:/zorivest/docs/build-plan/04-rest-api.md)

Add watchlist route registry entries to the REST API route table (7 new endpoints under `/api/v1/watchlists`).

#### [MODIFY] [05d-mcp-trade-planning.md](file:///p:/zorivest/docs/build-plan/05d-mcp-trade-planning.md)

Add 5 watchlist MCP tool specs (input schema, annotations, output, error posture, REST dependency).

#### [MODIFY] [05-mcp-server.md](file:///p:/zorivest/docs/build-plan/05-mcp-server.md)

Update toolset inventory table at L740: `trade-planning` tool count from `3` → `8`. Annotate the default-active total note at L747: the `37` figure is the target count across all specified tools; current implemented total is `23` (18 existing + 5 watchlist).

---

### Project Closeout

#### [MODIFY] [BUILD_PLAN.md](file:///p:/zorivest/docs/BUILD_PLAN.md)

Exact changes:
1. MEU-68 row: ⬜ → ✅
2. MEU-69 row: ⬜ → ✅
3. P2 summary line: completed count 2 → 4
4. Total summary line: completed count 58 → 60

**Validation**: `rg -c "✅" docs/BUILD_PLAN.md` count increases by 2, and `rg "P2.*completed" docs/BUILD_PLAN.md` shows `4`.

#### [MODIFY] [meu-registry.md](file:///p:/zorivest/.agent/context/meu-registry.md)

Add MEU-68 and MEU-69 rows to P2 section with ✅ approved status.

---

## Spec Sufficiency

| Behavior | Source Type | Source | Resolved? |
|---|---|---|---|
| Watchlist entity fields | Spec | [domain-model-reference.md](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) L64-69 | ✅ |
| WatchlistItem entity fields | Spec | [domain-model-reference.md](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) L71-76 | ✅ |
| SQLAlchemy models (pre-existing) | Local Canon | [models.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/models.py) L132-157 | ✅ |
| Service CRUD + item management | Local Canon | [03-service-layer.md](file:///p:/zorivest/docs/build-plan/03-service-layer.md) L33, [build-priority-matrix.md](file:///p:/zorivest/docs/build-plan/build-priority-matrix.md) item 33 | ✅ |
| Duplicate name rejection (409) | Local Canon | [Reflection](file:///p:/zorivest/docs/execution/reflections/2026-03-12-trade-reports-plans-reflection.md) L10: "dedup pattern reuse for watchlists" | ✅ |
| REST API routes | Local Canon | Follows [plans.py](file:///p:/zorivest/packages/api/src/zorivest_api/routes/plans.py) CRUD pattern | ✅ |
| Runtime wiring: `main.py`, `dependencies.py`, `stubs.py` | Local Canon | Live repo wiring pattern | ✅ |
| MCP tools in `trade-planning` toolset | Spec | [build-priority-matrix.md](file:///p:/zorivest/docs/build-plan/build-priority-matrix.md) item 34 | ✅ |
| Annotations + withMetrics + withGuard | Local Canon | [planning-tools.ts](file:///p:/zorivest/mcp-server/src/tools/planning-tools.ts) existing pattern | ✅ |
| Seed registry: `seed.ts` | Local Canon | [seed.ts](file:///p:/zorivest/mcp-server/src/toolsets/seed.ts) L130-155 | ✅ |
| Canon docs: `04-rest-api.md`, `05d-mcp-trade-planning.md` | Local Canon | Both need watchlist entries added | ✅ |

---

## Feature Intent Contracts

### MEU-68 FIC — Watchlist Entity + Service + API

| AC | Description | Source |
|---|---|---|
| AC-1 | `Watchlist` and `WatchlistItem` frozen dataclasses with all fields from [domain-model-reference.md](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) L64-76 | Spec |
| AC-2 | `WatchlistService` CRUD: create, get, list_all, update, delete | Spec ([build-priority-matrix.md](file:///p:/zorivest/docs/build-plan/build-priority-matrix.md) item 33) |
| AC-3 | `WatchlistService.add_ticker()` / `remove_ticker()` for item management | Spec |
| AC-4 | Duplicate watchlist name rejection raises `ValueError` | Local Canon ([reflection](file:///p:/zorivest/docs/execution/reflections/2026-03-12-trade-reports-plans-reflection.md) L10) |
| AC-5 | Duplicate ticker in same watchlist rejection raises `ValueError` | Local Canon (dedup pattern) |
| AC-6 | `SqlAlchemyWatchlistRepository` with CRUD + item queries in [repositories.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/repositories.py) | Local Canon |
| AC-7 | UoW integration: `uow.watchlists` in [unit_of_work.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/unit_of_work.py) | Local Canon |
| AC-8 | REST routes: 7 endpoints under `/api/v1/watchlists` in [watchlists.py](file:///p:/zorivest/packages/api/src/zorivest_api/routes/watchlists.py) | Local Canon (follows [plans.py](file:///p:/zorivest/packages/api/src/zorivest_api/routes/plans.py) pattern) |
| AC-9 | Cascade delete: deleting a watchlist removes all items | Spec ([models.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/models.py) L143 cascade config) |
| AC-10 | Runtime wiring: router in [main.py](file:///p:/zorivest/packages/api/src/zorivest_api/main.py), provider in [dependencies.py](file:///p:/zorivest/packages/api/src/zorivest_api/dependencies.py), stub repo in [stubs.py](file:///p:/zorivest/packages/api/src/zorivest_api/stubs.py) | Local Canon |

### MEU-69 FIC — Watchlist MCP Tools

| AC | Description | Source |
|---|---|---|
| AC-1 | 5 MCP tools registered: `create_watchlist`, `list_watchlists`, `get_watchlist`, `add_to_watchlist`, `remove_from_watchlist` | Spec ([build-priority-matrix.md](file:///p:/zorivest/docs/build-plan/build-priority-matrix.md) item 34) |
| AC-2 | All tools use `readOnlyHint`/`destructiveHint`/`idempotentHint` annotations correctly | Local Canon ([planning-tools.ts](file:///p:/zorivest/mcp-server/src/tools/planning-tools.ts) pattern) |
| AC-3 | All tools in `trade-planning` toolset with `alwaysLoaded: false` | Local Canon |
| AC-4 | All tools wrapped with `withMetrics(withGuard(...))` | Local Canon |
| AC-5 | Tools proxy to REST API: `/api/v1/watchlists` endpoints | Spec |
| AC-6 | [seed.ts](file:///p:/zorivest/mcp-server/src/toolsets/seed.ts) tool entries updated for `trade-planning` toolset | Local Canon |
| AC-7 | Canon docs updated: [05d-mcp-trade-planning.md](file:///p:/zorivest/docs/build-plan/05d-mcp-trade-planning.md) tool specs added | Local Canon |

---

## Verification Plan

### Automated Tests

#### Python (pytest)

```bash
# MEU-68 entity tests
uv run pytest tests/unit/test_entities.py -v -k watchlist

# MEU-68 service tests (new file)
uv run pytest tests/unit/test_watchlist_service.py -v

# MEU-68 API tests (new file)
uv run pytest tests/unit/test_api_watchlists.py -v

# MEU-68 repo integration tests
uv run pytest tests/integration/test_repositories.py -v -k watchlist

# Full regression
uv run pytest tests/ -v
```

#### TypeScript (vitest)

```bash
# MEU-69 MCP tool tests
cd mcp-server && npx vitest run tests/planning-tools.test.ts --reporter=verbose

# Full MCP regression
cd mcp-server && npx vitest run --reporter=verbose
```

#### Quality Gate

```bash
uv run python tools/validate_codebase.py --scope meu
```

### New Test Files

| File | Tests | MEU |
|---|---|---|
| `tests/unit/test_watchlist_service.py` [NEW] | ~15 tests for service CRUD, item management, dedup rejection | MEU-68 |
| `tests/unit/test_api_watchlists.py` [NEW] | ~12 tests for REST endpoint coverage (CRUD + items + error codes) | MEU-68 |
| `tests/unit/test_entities.py` [EXTEND] | ~4 tests for Watchlist/WatchlistItem creation | MEU-68 |
| `tests/integration/test_repositories.py` [EXTEND] | ~4 tests for SqlAlchemy repo integration | MEU-68 |
| `mcp-server/tests/planning-tools.test.ts` [EXTEND] | ~10 tests for 5 watchlist MCP tools | MEU-69 |

---

## Handoff Naming

- MEU-68: `058-2026-03-12-watchlist-entity-bp03s3.1.md`
- MEU-69: `059-2026-03-12-watchlist-mcp-bp05ds5d.md`

---

## Task Table

| task | owner_role | deliverable | validation | status |
|------|------------|-------------|------------|:------:|
| Add `Watchlist` + `WatchlistItem` dataclasses to `entities.py` | coder | AC-1 | `uv run pytest tests/unit/test_entities.py -k watchlist` | [ ] |
| Add `WatchlistRepository` Protocol to `ports.py` | coder | AC-6 | `uv run pyright packages/core/` | [ ] |
| Add `SqlAlchemyWatchlistRepository` to `repositories.py` | coder | AC-6 | `uv run pytest tests/integration/test_repositories.py -k watchlist` | [ ] |
| Add `watchlists` to UoW in `unit_of_work.py` | coder | AC-7 | `uv run pyright packages/infrastructure/` | [ ] |
| Create `watchlist_service.py` with CRUD + item management | coder | AC-2–AC-5 | `uv run pytest tests/unit/test_watchlist_service.py` | [ ] |
| Create `routes/watchlists.py` with 7 REST endpoints | coder | AC-8 | `uv run pytest tests/unit/test_api_watchlists.py` | [ ] |
| Add import + lifespan `app.state.watchlist_service` + router in `main.py` | coder | AC-10 | `uv run pytest tests/unit/test_api_watchlists.py` | [ ] |
| Add `get_watchlist_service` provider in `dependencies.py` | coder | AC-10 | `uv run pytest tests/unit/test_api_watchlists.py` | [ ] |
| Add `_InMemoryWatchlistRepo` + `StubUnitOfWork.watchlists` in `stubs.py` | coder | AC-10 | `uv run pytest tests/unit/test_api_watchlists.py` | [ ] |
| Write entity tests (~4) | tester | AC-1 | `uv run pytest tests/unit/test_entities.py -k watchlist -v` | [ ] |
| Write service tests (~15) | tester | AC-2–AC-5, AC-9 | `uv run pytest tests/unit/test_watchlist_service.py -v` | [ ] |
| Write API tests (~12) | tester | AC-8, AC-10 | `uv run pytest tests/unit/test_api_watchlists.py -v` | [ ] |
| Write repo integration tests (~4) | tester | AC-6 | `uv run pytest tests/integration/test_repositories.py -k watchlist -v` | [ ] |
| Add 5 watchlist MCP tools to `planning-tools.ts` | coder | AC-1–AC-5 (MEU-69) | `cd mcp-server && npx vitest run tests/planning-tools.test.ts` | [ ] |
| Add watchlist entries to `seed.ts` | coder | AC-6 (MEU-69) | `cd mcp-server && npx tsc --noEmit` | [ ] |
| Write MCP tool tests (~10) | tester | AC-1–AC-5 (MEU-69) | `cd mcp-server && npx vitest run tests/planning-tools.test.ts --reporter=verbose` | [ ] |
| Add watchlist routes to `04-rest-api.md` | coder | Canon sync | `rg -c watchlist docs/build-plan/04-rest-api.md` returns > 0 | [ ] |
| Add watchlist tool specs to `05d-mcp-trade-planning.md` | coder | AC-7 (MEU-69) | `rg -c watchlist docs/build-plan/05d-mcp-trade-planning.md` returns > 0 | [ ] |
| Update `05-mcp-server.md` inventory (trade-planning 3→8, total note) | coder | Canon sync | `rg "trade-planning.*8" docs/build-plan/05-mcp-server.md` | [ ] |
| Update `BUILD_PLAN.md`: MEU-68/69 ⬜→✅, P2 count 2→4, total 58→60 | coder | Status ✅ | `rg -c "✅" docs/BUILD_PLAN.md` count +2; P2 completed = 4 | [ ] |
| Update `meu-registry.md` with MEU-68 + MEU-69 rows | coder | Registry rows | `rg "MEU-68\|MEU-69" .agent/context/meu-registry.md` | [ ] |
| TDD cycle: RED → GREEN → REFACTOR (Python) | coder | All MEU-68 ACs | `uv run pytest tests/ -v` | [ ] |
| TDD cycle: RED → GREEN → REFACTOR (TypeScript) | coder | All MEU-69 ACs | `cd mcp-server && npx vitest run` | [ ] |
| Run MEU gate | tester | Quality gate pass | `uv run python tools/validate_codebase.py --scope meu` | [ ] |
| Create handoff `058-*` | reviewer | Handoff | File exists in `.agent/context/handoffs/` | [ ] |
| Create handoff `059-*` | reviewer | Handoff | File exists in `.agent/context/handoffs/` | [ ] |
| Create reflection file | reviewer | Reflection doc | File exists in `docs/execution/reflections/` | [ ] |
| Update metrics table | coder | Metrics row | `rg "watchlist" docs/execution/metrics.md` | [ ] |
| Save session state to pomera_notes | coder | Note saved | pomera_notes search returns entry | [ ] |
| Prepare commit messages | coder | Commit messages | Presented to human | [ ] |
