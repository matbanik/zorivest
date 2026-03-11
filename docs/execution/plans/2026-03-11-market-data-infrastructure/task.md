# Task — Market Data Infrastructure

> Project: `market-data-infrastructure` | MEUs: 59, 62, 60
> Plan: [implementation-plan.md](implementation-plan.md)

## TDD Implementation

### MEU-59: Provider Registry
- [ ] Write FIC-59 tests (Red) — `test_provider_registry.py`
- [ ] Implement provider registry (Green) — `provider_registry.py` + `__init__.py`
- [ ] Refactor MEU-59

### MEU-62: Rate Limiter + Log Redaction
- [ ] Write FIC-62 tests: rate limiter (Red) — `test_rate_limiter.py`
- [ ] Write FIC-62 tests: log redaction (Red) — `test_log_redaction.py`
- [ ] Implement rate limiter (Green) — `rate_limiter.py`
- [ ] Implement log redaction (Green) — `security/log_redaction.py`
- [ ] Refactor MEU-62

### MEU-60: ProviderConnectionService + Persistence
- [ ] Add `MarketProviderSettingsRepository` to `ports.py` + extend `UnitOfWork`
- [ ] Add `SqlMarketProviderSettingsRepository` to `repositories.py`
- [ ] Wire UoW concrete impl with new repo in `unit_of_work.py`
- [ ] Create `ProviderStatus` Pydantic model — `provider_status.py`
- [ ] Write FIC-60 tests (Red) — `test_provider_connection_service.py` + `test_market_provider_settings_repo.py`
- [ ] Implement ProviderConnectionService (Green) — `provider_connection_service.py`
- [ ] Refactor MEU-60

## Quality Gate
- [ ] `uv run ruff check packages/ tests/` — 0 issues
- [ ] `uv run pyright packages/` — 0 errors

## Handoffs
- [ ] Create handoff 047 — MEU-59 provider registry
- [ ] Create handoff 048 — MEU-62 rate limiter + log redaction
- [ ] Create handoff 049 — MEU-60 connection service

## Post-MEU Deliverables
- [ ] Run MEU gate: `uv run python tools/validate_codebase.py --scope meu`
- [ ] Update `.agent/context/meu-registry.md` — MEU-59, 62, 60 → ✅
- [ ] Update `docs/BUILD_PLAN.md` — fix P5 count, MEU statuses, total=51
- [ ] Full regression: `uv run pytest tests/ -v`
- [ ] Create reflection: `docs/execution/reflections/2026-03-11-market-data-infrastructure-reflection.md`
- [ ] Update metrics: `docs/execution/metrics.md`
- [ ] Save session state to pomera_notes
- [ ] Prepare commit messages
