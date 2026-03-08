# Infrastructure & Services — MEU 12–16

> **Project slug:** `2026-03-08-infra-services`
> **MEUs:** 12 (service-layer), 13 (sqlalchemy-models), 14 (repositories), 15 (unit-of-work), 16 (sqlcipher)
> **Build-plan sections:** [03 §3.1](../../build-plan/03-service-layer.md), [02 §2.1–§2.3](../../build-plan/02-infrastructure.md)
> **Phase gate:** This project completes Phase 2 core infrastructure (MEU-12 through MEU-16). Phase 2A (backup/restore, MEU-17–21) remains separate.

---

## User Review Required

> [!IMPORTANT]
> **MEU-12 scope decision.** Build-priority-matrix item 6 scopes this MEU to **"trade, account, image, calculator"**. This plan delivers exactly those **four P0 services**: `TradeService`, `AccountService`, `ImageService`, `SystemService` (calculator wrapper). Remaining services (Import, Tax, Analytics, Report, Review, MarketData) are **out of scope** — they belong to later phases. No stub/placeholder files are created (per GEMINI.md no-deferral rule).

> [!IMPORTANT]
> **Port extension required.** The UoW Protocol in `ports.py` currently has only `trades` and `images`. MEU-12 adds: (a) `AccountRepository` and `BalanceSnapshotRepository` Protocols, (b) `exists_by_fingerprint_since()` and `list_for_account()` methods to `TradeRepository`, (c) `RoundTripRepository` Protocol, (d) `accounts`, `balance_snapshots`, and `round_trips` attributes to `UnitOfWork`. This is normal Phase 2 evolution — not breaking, since no concrete UoW exists yet.

> [!WARNING]
> **sqlcipher3 Windows risk.** `sqlcipher3` requires compiling native C code (OpenSSL + SQLCipher amalgamation). If `uv add sqlcipher3` fails on Windows, fallbacks are: (a) `sqlcipher3-binary` pre-built wheel, (b) `pysqlcipher3` fork, (c) skip SQLCipher in MEU-16 and use plain SQLite with application-layer encryption via `cryptography`. The plan proceeds with `sqlcipher3` as primary; fallback evaluation happens during execution only if needed.

> [!IMPORTANT]
> **BUILD_PLAN.md drift.** Phase 1 status shows "🟡 In Progress" but all 11 MEUs are ✅ approved. The MEU Summary table shows "8" completed but should show "11". A dedicated task corrects this drift.

---

## Proposed Changes

### MEU-12: Service Layer (Matrix 6)

Service classes depend only on the UoW Protocol (ports). Tested with mock UoW — no database required.

#### [MODIFY] [ports.py](file:///p:/zorivest/packages/core/src/zorivest_core/application/ports.py)

Extend with:
- `AccountRepository` Protocol: `get()`, `save()`, `list_all()`
- `BalanceSnapshotRepository` Protocol: `save()`, `list_for_account()`
- `RoundTripRepository` Protocol: `save()`, `list_for_account()`
- `TradeRepository` additions: `exists_by_fingerprint_since(fingerprint, lookback_days)`, `list_for_account(account_id)`
- `UnitOfWork` additions: `accounts`, `balance_snapshots`, `round_trips` attributes

Note: Services use actual command names from `commands.py` (`CreateTrade`, `AttachImage`, `CreateAccount`, `UpdateBalance`), NOT the spec's `CreateTradeCommand`/`AttachImageCommand` aliases.

#### [NEW] [exceptions.py](file:///p:/zorivest/packages/core/src/zorivest_core/domain/exceptions.py)

Domain exception hierarchy (6 classes per spec):
- `ZorivestError` (base)
- `ValidationError`
- `NotFoundError`
- `BusinessRuleError`
- `BudgetExceededError`
- `ImportError` — file import parsing/format detection failures

Source: [03-service-layer.md §exceptions](../../build-plan/03-service-layer.md) lines 61–77

#### [NEW] [trade_service.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/trade_service.py)

`TradeService` with `create_trade(command: CreateTrade)` (exec_id + fingerprint dedup using `exists_by_fingerprint_since`), `get_trade()`, and `match_round_trips()`. Uses actual `CreateTrade` command from `commands.py` (not spec's `CreateTradeCommand` alias). Trade fingerprint is a domain function in `domain/trades/identity.py`.

#### [NEW] [identity.py](file:///p:/zorivest/packages/core/src/zorivest_core/domain/trades/identity.py)

`trade_fingerprint(trade) → str` — deterministic hash from core trade fields.

#### [NEW] [account_service.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/account_service.py)

`AccountService` with `create_account()`, `get_account()`, `list_accounts()`, `add_balance_snapshot()`.

#### [NEW] [image_service.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/image_service.py)

`ImageService` with `attach_image(command: AttachImage)`, `get_trade_images()`, `get_thumbnail()`. Uses actual `AttachImage` command from `commands.py` which carries `owner_type`/`owner_id`/`data` (not spec's `trade_id`/`image_data` aliases).

#### [NEW] [system_service.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/system_service.py)

`SystemService` — calculator wrapper per matrix item 6. Delegates to `domain.calculator.calculate_position_size()`. No backup/config logic (those belong to Phase 2A `BackupService`).

#### [NEW] [services/__init__.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/__init__.py)

Package marker re-exporting `TradeService`, `AccountService`, `ImageService`, `SystemService`.

---

### MEU-13: SQLAlchemy Models (Matrix 7)

All ORM models from [02 §2.1](../../build-plan/02-infrastructure.md). Created table-by-table with relationships.

#### [NEW] [models.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/models.py)

All `Base` subclasses from the spec:
- **Core P0:** `TradeModel`, `ImageModel`, `AccountModel`, `BalanceSnapshotModel`, `TradeReportModel`, `TradePlanModel`, `WatchlistModel`, `WatchlistItemModel`, `SettingModel`, `AppDefaultModel`, `MarketProviderSettingModel`, `McpGuardModel`
- **Expansion:** `RoundTripModel`, `ExcursionMetricsModel`, `IdentifierCacheModel`, `TransactionLedgerModel`, `OptionsStrategyModel`, `MistakeEntryModel`, `BrokerConfigModel`, `BankTransactionModel`, `BankImportConfigModel`

#### [NEW] [database/__init__.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/__init__.py)

Package marker with `Base` re-export.

---

### MEU-14: Repositories (Matrix 8)

Concrete SQLAlchemy repository implementations.

#### [NEW] [repositories.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/repositories.py)

- `SqlAlchemyTradeRepository` — implements `TradeRepository` Protocol (incl. `exists_by_fingerprint_since`, `list_for_account`)
- `SqlAlchemyImageRepository` — implements `ImageRepository` Protocol
- `SqlAlchemyAccountRepository` — implements `AccountRepository` Protocol
- `SqlAlchemyBalanceSnapshotRepository` — implements `BalanceSnapshotRepository` Protocol
- `SqlAlchemyRoundTripRepository` — implements `RoundTripRepository` Protocol

Each repo takes a `Session` in its constructor and maps between domain entities and ORM models.

---

### MEU-15: Unit of Work (Matrix 9)

#### [NEW] [unit_of_work.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/unit_of_work.py)

`SqlAlchemyUnitOfWork` implementing the `UnitOfWork` Protocol:
- Constructor takes `session_factory: sessionmaker`
- `__enter__` creates a `Session` and instantiates all repos (`trades`, `images`, `accounts`, `balance_snapshots`, `round_trips`)
- `__exit__` rolls back on exception, otherwise no-op (caller must explicitly `commit()`)
- `commit()` calls `session.commit()`
- `rollback()` calls `session.rollback()`

---

### MEU-16: SQLCipher Connection (Matrix 10)

#### [NEW] [connection.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/connection.py)

- `create_encrypted_connection(db_path, passphrase)` — returns SQLAlchemy `Engine` with SQLCipher
- `derive_key(password, salt)` — Argon2id KDF producing 256-bit key
- `create_engine_with_pragmas(url)` — standard engine with WAL mode + synchronous=NORMAL pragmas

---

### BUILD_PLAN.md Drift Correction

#### [MODIFY] [BUILD_PLAN.md](file:///p:/zorivest/docs/BUILD_PLAN.md)

1. Phase 1 status: `🟡 In Progress` → `✅ Completed`, date `2026-03-07`
2. Phase 2 status: `⚪ Not Started` → `🟡 In Progress`, date `2026-03-08`
3. MEU Summary: Phase 1 completed count: `8` → `11`
4. Validate no other stale references remain

---

## Spec Sufficiency per MEU

### MEU-12: Service Layer

| Behavior / Contract | Source Type | Source | Resolved? |
|---|---|---|---|
| TradeService.create_trade dedup (exec_id + fingerprint) | Spec | [03 §3.1](../../build-plan/03-service-layer.md) | ✅ |
| TradeService.get_trade | Spec | 03 §3.1 | ✅ |
| TradeService.match_round_trips | Spec | 03 §3.1 TradeService | ✅ |
| TradeRepository.exists_by_fingerprint_since | Spec | 03 §3.1 line 176 | ✅ |
| TradeRepository.list_for_account | Spec | 03 §3.1 line 187 | ✅ |
| trade_fingerprint deterministic hash | Spec | 03 §TradeFingerprint | ✅ |
| ImageService.attach_image (uses AttachImage cmd) raises NotFoundError | Spec | 03 §ImageService | ✅ |
| ImageService.get_trade_images / get_thumbnail | Spec | 03 §ImageService | ✅ |
| SystemService calculator wrapper | Spec | 03 §SystemService + matrix-6 | ✅ |
| AccountService CRUD + balance snapshots | Local Canon | domain-model-reference §Account | ✅ |
| Domain exception hierarchy (6 classes incl ImportError) | Spec | 03 §exceptions lines 61–77 | ✅ |
| RoundTripRepository Protocol | Spec | 03 §3.1 line 191 | ✅ |
| UoW Protocol extension (accounts, balance_snapshots, round_trips) | Local Canon + Spec | entities + 03 §TradeService | ✅ |
| Service→Command alignment (CreateTrade, AttachImage) | Local Canon | commands.py actual names | ✅ |

### MEU-13: SQLAlchemy Models

| Behavior / Contract | Source Type | Source | Resolved? |
|---|---|---|---|
| All 21 model classes with correct columns | Spec | [02 §2.1](../../build-plan/02-infrastructure.md) | ✅ |
| Numeric(15,6) for monetary columns | Spec | 02 §WARNING box | ✅ |
| Float for display-only columns | Spec | 02 §WARNING box | ✅ |
| Relationships (TradeModel → AccountModel, etc.) | Spec | 02 §2.1 | ✅ |
| McpGuardModel singleton pattern | Spec | 02 §McpGuardModel | ✅ |

### MEU-14: Repositories

| Behavior / Contract | Source Type | Source | Resolved? |
|---|---|---|---|
| Trade repo: get, save, list_all, exists, exists_by_fingerprint_since, list_for_account | Spec | ports.py TradeRepository (extended) | ✅ |
| Image repo: save, get, get_for_owner, delete, get_thumbnail | Spec | ports.py ImageRepository | ✅ |
| Account repo: get, save, list_all | Local Canon | Port extension (MEU-12) | ✅ |
| BalanceSnapshot repo: save, list_for_account | Local Canon | Port extension (MEU-12) | ✅ |
| RoundTrip repo: save, list_for_account | Spec | 03 §TradeService line 191 | ✅ |
| Domain→ORM mapping (dataclass ↔ model) | Spec | 02 §2.2 test pattern | ✅ |

### MEU-15: Unit of Work

| Behavior / Contract | Source Type | Source | Resolved? |
|---|---|---|---|
| Context manager (__enter__/__exit__) | Spec | ports.py UnitOfWork Protocol | ✅ |
| Commit/rollback semantics | Spec | ports.py + 02 §2.2 | ✅ |
| Session factory injection | Spec | testing-strategy.md conftest | ✅ |
| Transaction rollback tests | Spec | 02 §test_plan | ✅ |

### MEU-16: SQLCipher

| Behavior / Contract | Source Type | Source | Resolved? |
|---|---|---|---|
| create_encrypted_connection round-trip | Spec | 02 §2.3 | ✅ |
| Argon2 KDF (32-byte / 256-bit key) | Spec | 02 §2.3 | ✅ |
| Raw sqlite3 read fails without passphrase | Spec | 02 §2.3 test | ✅ |
| WAL mode pragma on connect | Spec | 02 §2.2 IMPORTANT box | ✅ |

---

## FIC — Feature Intent Contracts

### FIC-12: Service Layer

| AC | Description | Source | Test |
|---|---|---|---|
| AC-12.1 | `TradeService.create_trade(CreateTrade)` rejects duplicate exec_id with `BusinessRuleError` | Spec | `test_trade_service.py::test_create_trade_deduplicates_by_exec_id` |
| AC-12.2 | `TradeService.create_trade()` rejects fingerprint match within 30-day window via `exists_by_fingerprint_since` | Spec | `test_trade_service.py::test_create_trade_deduplicates_by_fingerprint` |
| AC-12.3 | `TradeService.create_trade()` saves and commits on success | Spec | `test_trade_service.py::test_create_trade_success` |
| AC-12.4 | `TradeService.match_round_trips()` groups executions via `list_for_account` and saves to `round_trips` repo | Spec | `test_trade_service.py::test_match_round_trips` |
| AC-12.5 | `ImageService.attach_image(AttachImage)` raises `NotFoundError` for nonexistent owner | Spec | `test_image_service.py::test_attach_image_to_nonexistent_trade_raises` |
| AC-12.6 | `ImageService.get_trade_images()` returns all images for a trade | Spec | `test_image_service.py::test_get_images_for_trade` |
| AC-12.7 | `AccountService.create_account(CreateAccount)` persists via UoW | Local Canon | `test_account_service.py::test_create_account` |
| AC-12.8 | `AccountService.add_balance_snapshot(UpdateBalance)` raises `NotFoundError` for unknown account | Local Canon | `test_account_service.py::test_add_snapshot_unknown_account` |
| AC-12.9 | `SystemService.calculate()` delegates to `calculate_position_size()` | Spec | `test_system_service.py::test_calculate_delegates` |
| AC-12.10 | `trade_fingerprint()` is deterministic and collision-resistant | Spec | `test_trade_fingerprint.py::test_deterministic` |
| AC-12.11 | Domain exceptions hierarchy: 6 classes with correct inheritance (incl `ImportError`) | Spec | `test_exceptions.py::test_hierarchy` |
| AC-12.12 | `TradeRepository` Protocol includes `exists_by_fingerprint_since` and `list_for_account` | Spec | pyright type check passes |
| AC-12.13 | `UnitOfWork` Protocol includes `round_trips` attribute | Spec | pyright type check passes |

### FIC-13: SQLAlchemy Models

| AC | Description | Source | Test |
|---|---|---|---|
| AC-13.1 | All 21 model classes define correct `__tablename__` | Spec | `test_models.py::test_tablenames` |
| AC-13.2 | `Base.metadata.create_all()` succeeds on in-memory SQLite | Spec | `test_models.py::test_create_all` |
| AC-13.3 | Monetary columns use `Numeric(15, 6)` | Spec | `test_models.py::test_monetary_precision` |
| AC-13.4 | Relationships are navigable (TradeModel.account_rel, etc.) | Spec | `test_models.py::test_relationships` |
| AC-13.5 | McpGuardModel has default `id=1` (singleton) | Spec | `test_models.py::test_mcp_guard_defaults` |

### FIC-14: Repositories

| AC | Description | Source | Test |
|---|---|---|---|
| AC-14.1 | `SqlAlchemyTradeRepository.save()` + `get()` round-trip | Spec | `test_repositories.py::test_trade_save_and_get` |
| AC-14.2 | `SqlAlchemyTradeRepository.exists()` returns True/False | Spec | `test_repositories.py::test_trade_exists` |
| AC-14.3 | `SqlAlchemyTradeRepository.exists_by_fingerprint_since()` finds fingerprint within window | Spec | `test_repositories.py::test_trade_exists_by_fingerprint` |
| AC-14.4 | `SqlAlchemyTradeRepository.list_for_account()` returns trades for account | Spec | `test_repositories.py::test_trade_list_for_account` |
| AC-14.5 | `SqlAlchemyImageRepository.save()` + `get()` round-trip including binary data | Spec | `test_repositories.py::test_image_save_and_retrieve` |
| AC-14.6 | `SqlAlchemyImageRepository.get_for_owner()` returns all images for owner | Spec | `test_repositories.py::test_get_images_for_trade` |
| AC-14.7 | `SqlAlchemyAccountRepository.save()` + `get()` round-trip | Local Canon | `test_repositories.py::test_account_save_and_get` |
| AC-14.8 | `SqlAlchemyBalanceSnapshotRepository.save()` + `list_for_account()` | Local Canon | `test_repositories.py::test_balance_snapshot_round_trip` |
| AC-14.9 | `SqlAlchemyRoundTripRepository.save()` + `list_for_account()` | Spec | `test_repositories.py::test_round_trip_round_trip` |

### FIC-15: Unit of Work

| AC | Description | Source | Test |
|---|---|---|---|
| AC-15.1 | `__enter__` creates session and exposes `trades`, `images`, `accounts`, `balance_snapshots`, `round_trips` repos | Spec | `test_unit_of_work.py::test_enter_exposes_repos` |
| AC-15.2 | `commit()` persists changes across sessions | Spec | `test_unit_of_work.py::test_commit_persists` |
| AC-15.3 | `rollback()` discards uncommitted changes | Spec | `test_unit_of_work.py::test_rollback_discards` |
| AC-15.4 | Uncommitted changes are auto-rolled-back on `__exit__` with exception | Spec | `test_unit_of_work.py::test_exit_on_exception_rollbacks` |

### FIC-16: SQLCipher

| AC | Description | Source | Test |
|---|---|---|---|
| AC-16.1 | `create_encrypted_connection()` creates a usable encrypted DB | Spec | `test_database_connection.py::test_create_encrypted_database` |
| AC-16.2 | Plain sqlite3 open fails on encrypted DB | Spec | `test_database_connection.py::test_plaintext_read_fails` |
| AC-16.3 | `derive_key()` is deterministic with same password+salt | Spec | `test_database_connection.py::test_argon2_deterministic` |
| AC-16.4 | `derive_key()` produces 32 bytes (256-bit) | Spec | `test_database_connection.py::test_key_length` |
| AC-16.5 | Engine with WAL pragmas returns `journal_mode=wal` | Spec | `test_wal_concurrency.py::test_wal_enabled` |

---

## Task Table

| # | Task | Owner | Deliverable | Validation | Status |
|---|---|---|---|---|---|
| 1 | MEU-12: Domain exceptions (6 classes incl ImportError) | coder | `domain/exceptions.py` + tests | `pytest tests/unit/test_exceptions.py -x` | ⬜ |
| 2 | MEU-12: Port extensions (Account/BalanceSnapshot/RoundTrip repos, TradeRepo methods, UoW) | coder | Updated `ports.py` | `pyright packages/core/` | ⬜ |
| 3 | MEU-12: Trade fingerprint | coder | `domain/trades/identity.py` + tests | `pytest tests/unit/test_trade_fingerprint.py -x` | ⬜ |
| 4 | MEU-12: TradeService + tests (uses `CreateTrade` cmd) | coder | `services/trade_service.py` + tests | `pytest tests/unit/test_trade_service.py -x` | ⬜ |
| 5 | MEU-12: AccountService + tests (uses `CreateAccount`/`UpdateBalance` cmds) | coder | `services/account_service.py` + tests | `pytest tests/unit/test_account_service.py -x` | ⬜ |
| 6 | MEU-12: ImageService + tests (uses `AttachImage` cmd) | coder | `services/image_service.py` + tests | `pytest tests/unit/test_image_service.py -x` | ⬜ |
| 7 | MEU-12: SystemService (calculator wrapper) + tests | coder | `services/system_service.py` + tests | `pytest tests/unit/test_system_service.py -x` | ⬜ |
| 8 | MEU-12: `services/__init__.py` (re-exports 4 services) | coder | Package init | `pyright packages/core/` | ⬜ |
| 9 | MEU-12: Quality gate | tester | Clean pyright + ruff | `uv run python tools/validate_codebase.py --scope meu --files packages/core/src/zorivest_core/domain/exceptions.py packages/core/src/zorivest_core/domain/trades/identity.py packages/core/src/zorivest_core/services/trade_service.py packages/core/src/zorivest_core/services/account_service.py packages/core/src/zorivest_core/services/image_service.py packages/core/src/zorivest_core/services/system_service.py packages/core/src/zorivest_core/services/__init__.py packages/core/src/zorivest_core/application/ports.py tests/unit/test_exceptions.py tests/unit/test_trade_fingerprint.py tests/unit/test_trade_service.py tests/unit/test_account_service.py tests/unit/test_image_service.py tests/unit/test_system_service.py` | ⬜ |
| 10 | MEU-12: Handoff | coder | `013-2026-03-08-service-layer-bp03s3.1.md` | `python -c "f=open('.agent/context/handoffs/013-2026-03-08-service-layer-bp03s3.1.md'); c=f.read(); print('sections:', c.count('## ')); assert c.count('## ')>=9"` | ⬜ |
| 11 | MEU-13: Install SQLAlchemy dependency | coder | Updated `pyproject.toml` | `uv sync` succeeds | ⬜ |
| 12 | MEU-13: SQLAlchemy models | coder | `database/models.py` + tests | `pytest tests/unit/test_models.py -x` | ⬜ |
| 13 | MEU-13: Quality gate | tester | Clean pyright + ruff | `uv run python tools/validate_codebase.py --scope meu --files packages/infrastructure/src/zorivest_infra/database/models.py packages/infrastructure/src/zorivest_infra/database/__init__.py tests/unit/test_models.py` | ⬜ |
| 14 | MEU-13: Handoff | coder | `014-2026-03-08-sqlalchemy-models-bp02s2.1.md` | `python -c "f=open('.agent/context/handoffs/014-2026-03-08-sqlalchemy-models-bp02s2.1.md'); c=f.read(); print('sections:', c.count('## ')); assert c.count('## ')>=9"` | ⬜ |
| 15 | MEU-14: Repositories (incl RoundTripRepository) | coder | `database/repositories.py` + integration tests | `pytest tests/integration/test_repositories.py -x` | ⬜ |
| 16 | MEU-14: Quality gate | tester | Clean pyright + ruff | `uv run python tools/validate_codebase.py --scope meu --files packages/infrastructure/src/zorivest_infra/database/repositories.py tests/integration/test_repositories.py` | ⬜ |
| 17 | MEU-14: Handoff | coder | `015-2026-03-08-repositories-bp02s2.2.md` | `python -c "f=open('.agent/context/handoffs/015-2026-03-08-repositories-bp02s2.2.md'); c=f.read(); print('sections:', c.count('## ')); assert c.count('## ')>=9"` | ⬜ |
| 18 | MEU-15: Unit of Work (5 repos) | coder | `database/unit_of_work.py` + integration tests | `pytest tests/integration/test_unit_of_work.py -x` | ⬜ |
| 19 | MEU-15: Quality gate | tester | Clean pyright + ruff | `uv run python tools/validate_codebase.py --scope meu --files packages/infrastructure/src/zorivest_infra/database/unit_of_work.py tests/integration/test_unit_of_work.py` | ⬜ |
| 20 | MEU-15: Handoff | coder | `016-2026-03-08-unit-of-work-bp02s2.2.md` | `python -c "f=open('.agent/context/handoffs/016-2026-03-08-unit-of-work-bp02s2.2.md'); c=f.read(); print('sections:', c.count('## ')); assert c.count('## ')>=9"` | ⬜ |
| 21 | MEU-16: Install sqlcipher3 + argon2-cffi dependencies | coder | Updated `pyproject.toml` | `uv sync` succeeds | ⬜ |
| 22 | MEU-16: SQLCipher connection | coder | `database/connection.py` + integration tests | `pytest tests/integration/test_database_connection.py tests/integration/test_wal_concurrency.py -x` | ⬜ |
| 23 | MEU-16: Quality gate | tester | Clean pyright + ruff | `uv run python tools/validate_codebase.py --scope meu --files packages/infrastructure/src/zorivest_infra/database/connection.py tests/integration/test_database_connection.py tests/integration/test_wal_concurrency.py` | ⬜ |
| 24 | MEU-16: Handoff | coder | `017-2026-03-08-sqlcipher-bp02s2.3.md` | `python -c "f=open('.agent/context/handoffs/017-2026-03-08-sqlcipher-bp02s2.3.md'); c=f.read(); print('sections:', c.count('## ')); assert c.count('## ')>=9"` | ⬜ |
| 25 | BUILD_PLAN.md drift correction | coder | Updated status tracker + MEU summary | `rg -c '✅ Completed' docs/BUILD_PLAN.md && rg -c '🟡 In Progress' docs/BUILD_PLAN.md` | ⬜ |
| 26 | MEU registry update | coder | Updated `meu-registry.md` with Phase 2 MEUs | `rg -c 'MEU-1[2-6]' .agent/context/meu-registry.md` | ⬜ |
| 27 | Post-project reflection | coder | `docs/execution/reflections/2026-03-08-infra-services-reflection.md` | `python -c "f=open('docs/execution/reflections/2026-03-08-infra-services-reflection.md'); c=f.read(); print('sections:', c.count('## ')); assert c.count('## ')>=4"` | ⬜ |
| 28 | Post-project metrics table | coder | Updated metrics in handoff/reflection | `rg -c 'MEU-1[2-6]' docs/execution/reflections/2026-03-08-infra-services-reflection.md` | ⬜ |
| 29 | Proposed commit messages | coder | `docs/execution/plans/2026-03-08-infra-services/commit-messages.md` | `python -c "f=open('docs/execution/plans/2026-03-08-infra-services/commit-messages.md'); lines=[l for l in f.read().splitlines() if l.startswith('feat:')]; print(len(lines),'messages'); assert len(lines)>=5"` | ⬜ |

---

## Verification Plan

### Automated Tests

All tests run via:

```bash
# MEU-12 unit tests (mock UoW, no DB)
uv run pytest tests/unit/test_exceptions.py tests/unit/test_trade_fingerprint.py tests/unit/test_trade_service.py tests/unit/test_account_service.py tests/unit/test_image_service.py tests/unit/test_system_service.py -x --tb=short

# MEU-13 model tests (in-memory SQLite schema creation)
uv run pytest tests/unit/test_models.py -x --tb=short

# MEU-14 integration tests (in-memory SQLite)
uv run pytest tests/integration/test_repositories.py -x --tb=short

# MEU-15 integration tests
uv run pytest tests/integration/test_unit_of_work.py -x --tb=short

# MEU-16 integration tests (file-based SQLite for WAL, SQLCipher requires file)
uv run pytest tests/integration/test_database_connection.py tests/integration/test_wal_concurrency.py -x --tb=short

# Full suite
uv run pytest tests/unit/ tests/integration/ -x --tb=short

# Quality gate (per-MEU, scoped to source + test files — see task table rows 9/13/16/19/23 for exact file lists)
uv run python tools/validate_codebase.py --scope meu --files <per task table>
```

### Manual Verification

None required — all MEUs in this project are pure Python with automated tests.

---

## Handoff Naming

| MEU | Handoff File |
|-----|-------------|
| MEU-12 | `013-2026-03-08-service-layer-bp03s3.1.md` |
| MEU-13 | `014-2026-03-08-sqlalchemy-models-bp02s2.1.md` |
| MEU-14 | `015-2026-03-08-repositories-bp02s2.2.md` |
| MEU-15 | `016-2026-03-08-unit-of-work-bp02s2.2.md` |
| MEU-16 | `017-2026-03-08-sqlcipher-bp02s2.3.md` |

---

## Stop Conditions

- **Red flag:** `sqlcipher3` fails to install → evaluate fallbacks before proceeding with MEU-16
- **Red flag:** pyright shows unresolvable type errors across package boundaries → investigate package configuration
- **Green exit:** All `pytest` tests pass, all quality gates clean, all handoffs created
