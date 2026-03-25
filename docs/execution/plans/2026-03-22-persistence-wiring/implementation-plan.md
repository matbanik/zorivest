# MEU-90a — Persistence Wiring Close-Out (`persistence-wiring`)

> Build plan: [`09a-persistence-integration.md`](../../build-plan/09a-persistence-integration.md)
> Matrix item: 49.0 · Phase: P2.5a
> Date: 2026-03-22
> Prior handoff: [081-2026-03-19-persistence-wiring-meu90a.md](../../../.agent/context/handoffs/081-2026-03-19-persistence-wiring-meu90a.md) — `ready_for_review`, 48 tests added, 1583 passing

---

## Background

MEU-90a implementation is already substantially complete as of the `081` handoff (2026-03-19).
This plan is a **close-out plan**, not a fresh red-phase. The work remaining is stub cleanup and
bookkeeping — not lifespan wiring, which is already shipped and tested.

### Already shipped (do not re-implement)

| Item | Evidence |
|------|----------|
| `SqlAlchemyUnitOfWork` in lifespan | `main.py:152` |
| `create_engine_with_wal` + `Base.metadata.create_all` | `main.py:138–139` |
| Scheduling adapters (Policy/Run/Step/Audit) | `main.py:171–191` |
| `WatchlistService(uow)` wired | `main.py:168` |
| `PipelineGuardrails` dict/ORM dual-path | `pipeline_guardrails.py:117–121` |
| `_isolate_db_url` autouse test fixture | `tests/conftest.py:11–29` |
| Integration tests passing | `tests/integration/test_persistence_wiring.py` — 7 passed |
| `test_unlock_propagates_db_unlocked` | **currently passes** — not a failing test |

---

> [!NOTE]
> **Resolved scope**: `StubMarketDataService` and `StubProviderConnectionService` are Tier 3
> (Heavy — need `EncryptionService` + `HttpClient` + rate limiters). `09a-persistence-integration.md`
> has been updated to defer their retirement to a service-wiring MEU post MEU-60/61.
> MEU-90a Tier 1 scope only: `McpGuardService` relocation + stub/repo removal.

---

## Spec Sufficiency Gate

| Contract | Source | Resolved? |
|----------|--------|:---------:|
| Real `SqlAlchemyUnitOfWork` in lifespan | `09a §9A.3 #2–3` | ✅ Shipped |
| `create_engine_with_wal` + bootstrap | `09a §9A.3 #1, #6` | ✅ Shipped |
| Scheduling stubs replaced with real adapters | `09a §9A.3 #4` | ✅ Shipped |
| `PipelineGuardrails` ORM fix | `09a §9A.3 #5` | ✅ Shipped |
| Test fixtures (per-test DB isolation) | `09a §9A.3 #7` | ✅ Shipped |
| `WatchlistService` persistence (`09a §9A.3 #8`) | `09a §9A.3 #8` | ✅ Shipped |
| `StubUnitOfWork` + `_InMemory*` removed | `09a §Stubs to Remove` | ❌ Still present in `stubs.py` |
| `test_watchlist_service.py` uses real UoW | `known-issues.md:81` | ❌ Still imports `StubUnitOfWork` |
| `McpGuardService` moved out of `stubs.py` | `09a:83, 88` | ❌ Still in `stubs.py` |
| `StubMarketDataService` retired | Deferred — service-wiring MEU (post-MEU-61) | 🔵 Deferred by design |
| `StubProviderConnectionService` retired | Deferred — service-wiring MEU (post-MEU-60) | 🔵 Deferred by design |

---

## Proposed Changes

### Package: `packages/api`

#### [MODIFY] [stubs.py](file:///p:/zorivest/packages/api/src/zorivest_api/stubs.py)

**Remove** the stub classes that are blocked only on this MEU:

- `_InMemoryRepo` (base class)
- `_InMemoryTradeReportRepo`
- `_InMemoryTradePlanRepo`
- `_InMemoryWatchlistRepo`
- `_InMemoryPipelineRunRepo`
- `_StubQuery`
- `_StubSession`
- `StubUnitOfWork`
- `McpGuardService` — **move** to a permanent home (e.g., `packages/api/src/zorivest_api/services/mcp_guard.py` ), update `main.py` import

**Retain** (blocked on future MEUs per stub retirement roadmap):
- `StubAnalyticsService` (MEU-118)
- `StubReviewService` (MEU-118)
- `StubTaxService` (MEU-148)
- `StubMarketDataService` (MEU-61 dependency) — see WARNING above
- `StubProviderConnectionService` (MEU-60 dependency) — see WARNING above

---

### Package: `tests`

#### [MODIFY] [test_watchlist_service.py](file:///p:/zorivest/tests/unit/test_watchlist_service.py)

Replace `StubUnitOfWork` fixture with real in-memory SQLite UoW:

```python
from zorivest_infra.database.unit_of_work import SqlAlchemyUnitOfWork, create_engine_with_wal
from zorivest_infra.database.models import Base

@pytest.fixture
def service() -> WatchlistService:
    engine = create_engine_with_wal("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    uow = SqlAlchemyUnitOfWork(engine)
    return WatchlistService(uow)
```

Remove: `from zorivest_api.stubs import StubUnitOfWork`

---

### Docs: Canonical Tracking Updates

#### [MODIFY] [meu-registry.md](file:///p:/zorivest/.agent/context/meu-registry.md)

- MEU-90a: `⬜ planned` → `🟡 ready_for_review` (already shipped in 081 handoff)
- MEU-90b: `🔴 changes_required` → `✅ approved` (Pass 3 in handoff approved ✅)

#### [MODIFY] [BUILD_PLAN.md](file:///p:/zorivest/docs/BUILD_PLAN.md)

- MEU-90a: `⬜` → `🟡`
- MEU-90b: `🔴` → `✅`

#### [MODIFY] [known-issues.md](file:///p:/zorivest/.agent/context/known-issues.md)

**Phase 1 stub-retirement table** (lines 79–84):

| Stub | Current Status | Correction |
|------|---------------|------------|
| `StubUnitOfWork` + 7 `_InMemory*` repos | `MEU-90a ✅` in table but not yet done | Mark ✅ after T2 execution |
| `McpGuardService` | `MEU-38 ✅` — only needs move | Mark ✅ after T3 execution |
| `StubMarketDataService` | `MEU-61 ✅` — Tier 3 | Retain; clarify blocked on MEU-61 provider integration |
| `StubProviderConnectionService` | `MEU-60 ✅` — Tier 3 | Retain; clarify blocked on MEU-60 provider management |

**Summary line** (line 94): Change "Phase 1 via MEU-90b" → "Phase 1 via MEU-90a (stubs removed); Phase 2 retires each stub with its real service."

---

## Task Table

| # | Task | owner_role | Deliverable | Validation | Status |
|---|------|-----------|-------------|------------|--------|
| T1 | Remove `StubUnitOfWork` + 7 `_InMemory*` + `_StubQuery` + `_StubSession` from `stubs.py` | coder | Pruned `stubs.py` | `python -c "from zorivest_api.stubs import StubUnitOfWork"` raises `ImportError` | ⬜ |
| T2 | Convert `test_watchlist_service.py` fixture to real in-memory SQLite UoW | coder | Updated fixture; no `StubUnitOfWork` import | `uv run pytest tests/unit/test_watchlist_service.py -v` — all existing tests pass | ⬜ |
| T3 | Move `McpGuardService` from `stubs.py` to `packages/api/src/zorivest_api/services/mcp_guard.py`; update `main.py` import | coder | New file; `stubs.py` no longer contains `McpGuardService` | `uv run pytest tests/ --tb=no -q` — 0 failures | ⬜ |
| T4 | Clarify Tier-3 stubs (`StubMarketDataService`, `StubProviderConnectionService`) in `known-issues.md` as MEU-61/60-blocked (not MEU-90a) | coder | Updated `known-issues.md` Phase 1 table and summary line | `rg "MEU-90b" .agent/context/known-issues.md` — 0 stale references | ⬜ |
| T5 | Update `meu-registry.md`: MEU-90a `⬜ → 🟡`; MEU-90b `🔴 → ✅` | coder | Updated registry | `rg -e "MEU-90a" .agent/context/meu-registry.md \| rg "⬜"` → 0 matches | ⬜ |
| T6 | Update `docs/BUILD_PLAN.md`: MEU-90a `⬜ → 🟡`; MEU-90b `🔴 → ✅` | coder | Updated hub | `rg -e "MEU-90a" docs/BUILD_PLAN.md \| rg "⬜"` → 0 matches | ⬜ |
| T7 | Full regression after all edits | tester | 0 failures | `uv run pytest tests/ --tb=no -q` | ⬜ |
| T8 | Ruff + pyright on changed files | tester | 0 errors | `uv run ruff check <files>; uv run pyright <packages>` | ⬜ |
| T9 | Append `Corrections Applied` section to this canonical review handoff | reviewer | Updated handoff | Section contains diffs, fresh test count, and verdict | ⬜ |

---

## Verification Plan

### Automated Tests

```powershell
# Import error check (T1)
uv run python -c "from zorivest_api.stubs import StubUnitOfWork"
# Expected: ImportError (StubUnitOfWork removed)

# Watchlist unit tests (T2)
uv run pytest tests/unit/test_watchlist_service.py -v
# Expected: all existing tests pass

# Full regression (T7)
uv run pytest tests/ --tb=no -q
# Expected: 0 failures (baseline was 1602 pass + 1 failing unlock test
#   which the reviewer confirmed NOW passes — so target: 1602+ passing)

# Lint + types (T8)
uv run ruff check packages/api/src/zorivest_api/stubs.py packages/api/src/zorivest_api/services/mcp_guard.py tests/unit/test_watchlist_service.py
uv run pyright packages/api/src/zorivest_api/ tests/unit/test_watchlist_service.py
```

### Registry / doc validation

```powershell
# T5/T6: no stale ⬜/🔴 refs for MEU-90a/90b
rg -e "MEU-90a" .agent/context/meu-registry.md docs/BUILD_PLAN.md | rg "⬜"
rg -e "MEU-90b" .agent/context/meu-registry.md docs/BUILD_PLAN.md | rg "🔴"
# Expected: 0 matches each

# T4: no stale "Phase 1 via MEU-90b" summary
rg "Phase 1 via MEU-90b" .agent/context/known-issues.md
# Expected: 0 matches

# T3: McpGuardService no longer in stubs.py
rg "class McpGuardService" packages/api/src/zorivest_api/stubs.py
# Expected: 0 matches
```

### OpenAPI drift check

```powershell
# No API routes changed — drift check confirms clean
uv run python tools/export_openapi.py --check openapi.committed.json
# Expected: no drift
```
