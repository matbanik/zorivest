# 09a — Persistence Integration

> Phase: P2.5a · MEU-90a `persistence-wiring`
> Prerequisites: Phase 2 (MEU-12–16 ✅), Phase 9 repos (MEU-82 ✅)
> Unblocks: Phase 10 Service Daemon (MEU-91+), GUI scheduling (MEU-72)
> Status: ⬜ planned

## 9A.1 Problem Statement

The FastAPI lifespan (`main.py`) constructs a `StubUnitOfWork` (in-memory dicts) for all services instead of the real `SqlAlchemyUnitOfWork` completed in Phase 2 (MEU-15).

**Consequences:**

- **Data loss on restart** — all trades, accounts, settings, policies, and runs are ephemeral
- **Broken approval flow** — `PipelineGuardrails.check_policy_approved()` uses `getattr(policy, "approved")` but stub stores return `dict` objects; `getattr` can't find dict keys
- **Idle repos** — 17 real SQLAlchemy repositories exist in `SqlAlchemyUnitOfWork` but none are used at runtime
- **Phase 10 blocked** — a background service daemon cannot run with in-memory stubs
- **No watchlist persistence** — `_InMemoryWatchlistRepo` doesn't survive restart
- **No market provider settings** — `StubUnitOfWork` is missing `market_provider_settings` repo entirely

## 9A.2 Infrastructure Already Built

### Real SqlAlchemyUnitOfWork (17 repos)

| Repo | Type | MEU | In StubUoW? |
|------|------|-----|:-----------:|
| `trades` | `SqlAlchemyTradeRepository` | MEU-14 | ✅ (stub) |
| `images` | `SqlAlchemyImageRepository` | MEU-14 | ✅ (stub) |
| `accounts` | `SqlAlchemyAccountRepository` | MEU-14 | ✅ (stub) |
| `balance_snapshots` | `SqlAlchemyBalanceSnapshotRepository` | MEU-14 | ✅ (stub) |
| `round_trips` | `SqlAlchemyRoundTripRepository` | MEU-14 | ✅ (stub) |
| `settings` | `SqlAlchemySettingsRepository` | MEU-14 | ✅ (stub) |
| `app_defaults` | `SqlAlchemyAppDefaultsRepository` | MEU-17 | ✅ (stub) |
| `market_provider_settings` | `SqlMarketProviderSettingsRepository` | MEU-58 | ❌ missing |
| `trade_reports` | `SqlAlchemyTradeReportRepository` | MEU-52 | ✅ (stub) |
| `trade_plans` | `SqlAlchemyTradePlanRepository` | MEU-66 | ✅ (stub) |
| `policies` | `PolicyRepository` | MEU-82 | ❌ separate `StubPolicyStore` |
| `pipeline_runs` | `PipelineRunRepository` | MEU-82 | ❌ separate `_InMemoryPipelineRunRepo` |
| `reports` | `ReportRepository` | MEU-82 | ❌ missing |
| `fetch_cache` | `FetchCacheRepository` | MEU-85 | ❌ missing |
| `pipeline_state` | `PipelineStateRepository` | MEU-85 | ❌ missing |
| `audit_log` | `AuditLogRepository` | MEU-82 | ❌ separate `StubAuditCounter` |
| `deliveries` | `DeliveryRepository` | MEU-88 | ❌ missing |

### Supporting Infrastructure

| Component | Location | MEU |
|-----------|----------|-----|
| `SqlAlchemyUnitOfWork` | `packages/infrastructure/.../unit_of_work.py` | MEU-15 |
| `create_engine_with_wal()` | `packages/infrastructure/.../unit_of_work.py` | MEU-15 |
| SQLCipher encrypted connection | `packages/infrastructure/.../sqlcipher.py` | MEU-16 |
| Alembic migrations | `packages/infrastructure/migrations/` | MEU-13 |
| All 21 SQLAlchemy ORM models | `packages/infrastructure/.../models.py` | MEU-13/81 |

## 9A.3 Scope

### Must Do

1. **Engine initialization** — Use `create_engine_with_wal()` (or SQLCipher variant) in `main.py` lifespan to create a real SQLAlchemy engine
2. **Session factory** — Create `sessionmaker(bind=engine)` and pass to `SqlAlchemyUnitOfWork`
3. **Replace StubUnitOfWork** — Construct `SqlAlchemyUnitOfWork(engine)` for all services: `TradeService`, `AccountService`, `ImageService`, `SettingsService`, `ReportService`, `WatchlistService`, `PipelineRunner`
4. **Replace scheduling stubs** — Swap `StubPolicyStore`/`StubRunStore`/`StubStepStore`/`StubAuditCounter` with repos from the real UoW (`policies`, `pipeline_runs`, `audit_log`)
5. **PipelineGuardrails fix** — `check_policy_approved()` L105-122: `getattr(policy, "approved")` fails on dicts → real `PolicyModel` objects have `.approved` attribute. Make it work with both: `getattr(policy, "approved", None) or (isinstance(policy, dict) and policy.get("approved"))`
6. **Alembic bootstrap** — Run `alembic upgrade head` or `Base.metadata.create_all(engine)` at startup
7. **Test fixtures** — Add DB session fixtures for integration tests (per-test transaction rollback)
8. **WatchlistService persistence** — Currently uses `_InMemoryWatchlistRepo`; real UoW doesn't have a watchlist repo yet — either add one or note as follow-up

### Keep Stubs (Out of Scope)

These stub **entire service interfaces** that haven't been implemented:

| Stub | Why Keep |
|------|----------|
| `StubAnalyticsService` | Real analytics service not yet built |
| `StubReviewService` | Review workflow not yet implemented |
| `StubTaxService` | Tax engine is Phase 3 (MEU-123+) |
| `StubMarketDataService` | Aggregator service exists but may need further wiring |
| `StubProviderConnectionService` | Provider connection service exists but may need wiring |
| `McpGuardService` | Already real (not a stub) — lives in `stubs.py` by location only |
| `AuthService` | Already real — no stub replacement needed |

### Stubs to Remove

| Stub | Replacement |
|------|-------------|
| `StubUnitOfWork` | `SqlAlchemyUnitOfWork(engine)` |
| `_InMemoryRepo` | No longer needed as base class |
| `_InMemoryTradeReportRepo` | `SqlAlchemyTradeReportRepository` via UoW |
| `_InMemoryTradePlanRepo` | `SqlAlchemyTradePlanRepository` via UoW |
| `_InMemoryWatchlistRepo` | Needs real repo (see §9A.4) |
| `_InMemoryPipelineRunRepo` | `PipelineRunRepository` via UoW |
| `StubPolicyStore` | `PolicyRepository` via UoW |
| `StubRunStore` | `PipelineRunRepository` via UoW |
| `StubStepStore` | Needs mapping to `PipelineStateRepository` or similar |
| `StubAuditCounter` | `AuditLogRepository` via UoW |

## 9A.4 Open Questions

> [!IMPORTANT]
> These should be resolved during execution planning:

1. **Watchlist repo** — `SqlAlchemyUnitOfWork` doesn't have a `watchlists` attribute. Need to either:
   - Add `SqlAlchemyWatchlistRepository` to infrastructure and UoW, or
   - Keep `_InMemoryWatchlistRepo` temporarily
2. **StubStepStore mapping** — Does `StubStepStore` map to `PipelineStateRepository` or a separate repo?
3. **SQLCipher vs SQLite** — Tests should use plain SQLite; production uses SQLCipher. How to switch? Config flag? Separate engine factory?
4. **Market data services** — `StubMarketDataService` and `StubProviderConnectionService` — are the real services (MEU-60, MEU-61) ready to wire in, or do they need additional integration work?

## 9A.5 Files to Modify

| File | Change |
|------|--------|
| `packages/api/src/zorivest_api/main.py` | Replace `StubUnitOfWork()` with engine + `SqlAlchemyUnitOfWork`; replace all scheduling stubs with UoW repos |
| `packages/api/src/zorivest_api/stubs.py` | Remove repo stubs listed in §9A.3; keep service-level stubs |
| `packages/core/src/.../pipeline_guardrails.py` | Fix `getattr`/dict mismatch in `check_policy_approved()` |
| `packages/infrastructure/.../unit_of_work.py` | Possibly add `watchlists` repo |
| `tests/unit/test_api_scheduling.py` | Update `TestLiveWiring`/`TestLiveExecution` for real DB |
| `tests/conftest.py` | Add DB engine/session fixtures for integration tests |
| `tests/integration/test_unit_of_work.py` | Extend with scheduling repo coverage |

## 9A.6 Known Risks

1. **SQLCipher dependency** — Tests may need plain SQLite; production uses SQLCipher. Need a config switch.
2. **Migration bootstrap** — First-run experience must create tables automatically.
3. **Test isolation** — Integration tests need transaction rollback or per-test DB creation.
4. **Stub → Real transition** — Must verify all 25+ existing scheduling tests still pass with real repos.
5. **Service constructor signatures** — Some services may expect different repo interfaces than what `SqlAlchemyUnitOfWork` provides.

## 9A.7 Verification Plan

```bash
# Unit tests (existing + updated)
uv run pytest tests/unit/test_api_scheduling.py -v

# Full regression
uv run pytest tests/ --tb=no -q

# Type checking
uv run pyright packages/api/src/zorivest_api/main.py

# Integration test: end-to-end trigger_run through real DB
uv run pytest tests/integration/ -k "scheduling or unit_of_work" -v

# Verify all 21 tables created
uv run python -c "from zorivest_infra.database.models import Base; print(len(Base.metadata.tables))"
```
