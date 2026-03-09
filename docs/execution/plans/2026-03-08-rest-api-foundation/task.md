# Task — REST API Foundation

> Project: `rest-api-foundation` | MEUs: 23, 24, 25, 26

## Package Scaffold

- [x] Create `packages/api/` directory structure
- [x] Create `packages/api/pyproject.toml` (incl. `cryptography`, `argon2-cffi`)
- [x] Add `zorivest-api` to root `pyproject.toml` deps + sources (workspace membership auto via `packages/*`)
- [x] Run `uv sync` to verify resolution — 17 packages installed

## MEU-Prep: Port + Repository + Service Extensions (Prerequisite, TDD-first)

- [x] **Write `test_service_extensions.py` FIRST (Red phase)**
- [x] Verify tests FAIL (14 failed in 0.05s)
- [x] Extend `ports.py`: TradeRepo (delete/list_filtered/update), AccountRepo (delete/update), ImageRepo (get_full_data)
- [x] Extend `repositories.py`: implement new port methods in SQLAlchemy repos (delete, list_filtered, merge for update)
- [x] Extend `TradeService` with `list_trades`, `update_trade`, `delete_trade`
- [x] Extend `AccountService` with `update_account`, `delete_account`
- [x] Extend `ImageService` with `get_image`, `get_full_image`, `get_images_for_owner`
- [x] Create `zorivest_core/version.py` (`get_version`, `get_version_context`)
- [x] Verify all MEU-Prep tests PASS (Green phase) — 14/14 passed

## MEU-23: fastapi-routes (App Factory + Foundation)

- [x] Write `test_api_foundation.py` (Red phase)
- [x] Implement `main.py` (app factory, lifespan, CORS via `allow_origin_regex`, request-ID, error handler, 7 tags)
- [x] Implement `schemas/common.py` (PaginatedResponse, ErrorEnvelope)
- [x] Implement `dependencies.py` (DI providers, mode-gating)
- [x] Implement `routes/health.py` (canonical HealthResponse: status, version, uptime_seconds, database)
- [x] Implement `routes/version.py` (canonical VersionResponse: version, context via `get_version_context()`)
- [x] Verify tests PASS (Green phase) — 16/16 passed
- [x] Create handoff `024-2026-03-08-fastapi-routes-bp04s4.0.md`

## MEU-24: api-trades (Trade CRUD)

- [x] Write `test_api_trades.py` (Red phase)
- [x] Implement `routes/trades.py` (5 CRUD + 1 nested image route)
- [x] Implement `routes/images.py` (3 global image routes)
- [x] Implement `routes/round_trips.py` (1 route)
- [x] Register routers in `main.py`
- [x] Verify tests PASS (Green phase) — 13/13 passed
- [x] Create handoff `025-2026-03-08-api-trades-bp04as4a.md`

## MEU-25: api-accounts (Account CRUD)

- [x] Write `test_api_accounts.py` (Red phase)
- [x] Implement `routes/accounts.py` (5 CRUD + 1 balance route)
- [x] Register router in `main.py`
- [x] Verify tests PASS (Green phase) — 7/7 passed (1 bug fixed: AccountType case normalization)
- [x] Create handoff `026-2026-03-08-api-accounts-bp04bs4b.md`

## MEU-26: api-auth (Auth Route Surface + Error Modes — crypto stubs)

- [x] Write `test_api_auth.py` (Red phase)
- [x] Implement `auth/auth_service.py` (Argon2id KDF stubs, Fernet stubs, session store, key hash-and-store, confirmation tokens)
- [x] Implement `routes/auth.py` (unlock/lock/status + API key CRUD, 401/403/423 error modes)
- [x] Implement `routes/confirmation.py` (confirmation tokens, `ctk_` prefix, 60s TTL)
- [x] Register routers in `main.py`
- [x] Verify tests PASS (Green phase) — 12/12 passed
- [x] Create handoff `027-2026-03-08-api-auth-bp04cs4c.md`

## Post-Project

- [x] Update `docs/BUILD_PLAN.md` (phase status + MEU statuses)
- [x] Update `docs/build-plan/dependency-manifest.md` (add `cryptography`, `argon2-cffi` to Phase 4)
- [x] Update `.agent/context/meu-registry.md` (add Phase 4 section)
- [ ] Run MEU gate: `uv run python tools/validate_codebase.py --scope meu`
- [x] Run full regression: `uv run pytest tests/unit/ -q` — 527/527 passed (3.98s)
- [x] Create reflection at `docs/execution/reflections/`
- [x] Update `docs/execution/metrics.md`
- [ ] Save session state to `pomera_notes`
- [ ] Propose commit messages
