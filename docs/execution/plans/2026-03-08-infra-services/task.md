# Task Checklist — infra-services (MEU 12–16)

## MEU-12: Service Layer (Matrix 6)

- [x] Domain exceptions hierarchy (6 classes incl `ImportError`) + tests
- [x] Port extensions: `AccountRepository`, `BalanceSnapshotRepository`, `RoundTripRepository`, `TradeRepository.exists_by_fingerprint_since`/`list_for_account`, `UnitOfWork` adds `accounts`/`balance_snapshots`/`round_trips`
- [x] Trade fingerprint (`domain/trades/identity.py` + tests)
- [x] `TradeService` + unit tests (mock UoW, uses `CreateTrade` cmd)
- [x] `AccountService` + unit tests (mock UoW, uses `CreateAccount`/`UpdateBalance` cmds)
- [x] `ImageService` + unit tests (mock UoW, uses `AttachImage` cmd)
- [x] `SystemService` (calculator wrapper) + unit tests
- [x] `services/__init__.py` (re-exports 4 services)
- [x] Quality gate (pyright + ruff on source + test files via `--scope meu --files`)
- [x] Handoff: `013-2026-03-08-service-layer-bp03s3.1.md`

## MEU-13: SQLAlchemy Models (Matrix 7)

- [x] Install SQLAlchemy dependency (`pyproject.toml`)
- [x] All 21 ORM models in `database/models.py`
- [x] Unit tests (schema creation, column types, relationships)
- [x] Quality gate (`--scope meu --files`)
- [x] Handoff: `014-2026-03-08-sqlalchemy-models-bp02s2.1.md`

## MEU-14: Repositories (Matrix 8)

- [x] Repositories (Trade, Image, Account, BalanceSnapshot, RoundTrip)
- [x] Integration tests (in-memory SQLite)
- [x] Quality gate (`--scope meu --files`)
- [x] Handoff: `015-2026-03-08-repositories-bp02s2.2.md`

## MEU-15: Unit of Work (Matrix 9)

- [x] `SqlAlchemyUnitOfWork` implementation (5 repos)
- [x] Integration tests (commit/rollback)
- [x] Quality gate (`--scope meu --files`)
- [x] Handoff: `016-2026-03-08-unit-of-work-bp02s2.2.md`

## MEU-16: SQLCipher (Matrix 10)

- [x] Install sqlcipher3 + argon2-cffi dependencies (`pyproject.toml`)
- [x] `create_encrypted_connection()` + `derive_key()`
- [x] Engine with WAL pragmas
- [x] Integration tests (file-based SQLite)
- [x] Quality gate (`--scope meu --files`)
- [x] Handoff: `017-2026-03-08-sqlcipher-bp02s2.3.md`

## Post-Project

- [x] BUILD_PLAN.md drift correction (Phase 1 ✅, Phase 2 🟡, MEU count fix)
- [x] MEU registry update (add Phase 2 statuses)
- [x] Reflection file
- [x] Metrics table update
- [x] Proposed commit messages
