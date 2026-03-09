# REST API Foundation — Implementation Plan

> Project: `rest-api-foundation` | MEUs: 23, 24, 25, 26 | Date: 2026-03-08

## Goal

Create the FastAPI REST API package (`packages/api`) with the app factory, middleware, shared schemas, and the first four route groups: health/version (foundation), trades, accounts, and auth. This establishes the thin REST layer that delegates to the existing approved service layer. All routes tested via FastAPI `TestClient`.

---

## User Review Required

> [!IMPORTANT]
> **Scoping Decisions for Routes (source-tagged):**
> - **04a (Trades):** Only Trade CRUD (5), trade images (2), global images (3), and round-trips (1) are in-scope.
>   - `Deferred: Trade reports` — entity dep MEU-52 (P1), not yet approved. Source: Local Canon (BUILD_PLAN.md §P1 item 17)
>   - `Deferred: Trade plans` — entity dep MEU-66 (P2), not yet approved. Source: Local Canon (BUILD_PLAN.md §P2 item 31)
>   - `Deferred: Journal linking` — dep MEU-117 (P2.75), not yet approved. Source: Local Canon (BUILD_PLAN.md §P2.75 item 68.4e)
> - **04b (Accounts):** Only Account CRUD (5) + balance recording (1) are in-scope.
>   - `Deferred: Broker sync, banking import, CSV/PDF import, identifier resolution` — service deps MEU-96–103 (P2.75), not yet approved. Source: Local Canon (BUILD_PLAN.md §P2.75 items 50e–57e)
> - **04c (Auth):** All routes in-scope. Full Phase 4c envelope-encryption contract is implemented, including API key hash lookup, Argon2id KDF → KEK → DEK unwrap, `bootstrap.json` persistence, key revocation, and explicit unlock failure modes (401/403/423). Unit tests mock the SQLCipher layer (MEU-16 ✅ approved).

> [!WARNING]
> **New package creation:** This project creates `packages/api`. The root `pyproject.toml` already uses `members = ["packages/*"]`, so `packages/api` is automatically a workspace member once the directory exists. However, the root `[project] dependencies` and `[tool.uv.sources]` sections need `zorivest-api` added (dependency + workspace source entry), matching the existing `zorivest-core` and `zorivest-infra` patterns.

> [!WARNING]
> **Service + port + repo layer gaps (prerequisite):** The current approved service layer is missing several methods required by route handlers. Additionally, the port protocols and repository implementations must be extended *before* those service methods can be written. The prerequisite work is:
> - **Ports:** Add `delete` + `list_filtered` to `TradeRepository`; add `delete` + `update` to `AccountRepository`; add `get_full_data` to `ImageRepository`
> - **Repositories:** Implement the new port methods in SQLAlchemy repos; make `save()` upsert-safe (merge instead of add)
> - **Services:** Add `list_trades`, `update_trade`, `delete_trade` to TradeService; `update_account`, `delete_account` to AccountService; `get_image`, `get_full_image`, `get_images_for_owner` to ImageService

> [!IMPORTANT]
> **Auth dependency:** Phase 4c requires `cryptography` (Fernet for DEK wrapping). The dependency manifest only adds `cryptography` in Phase 8 (Market Data). This project adds `cryptography` to the `zorivest-api` package deps, which is a dependency-manifest amendment. This is noted as an intentional forward-pull justified by the canonical 04c auth spec requiring envelope encryption.

> [!NOTE]
> **Canon scope annotations:** The deferred route groups are now annotated directly in the canonical spec files (`04a-api-trades.md`, `04b-api-accounts.md`) with `[DEFERRED: MEU-XX]` markers on each section header and an implementation-status summary in the file header. This eliminates the scope ambiguity for future agents reading those files. Deferrals are also source-tagged in this plan per `BUILD_PLAN.md` MEU dependency chains.

---

## Proposed Changes

### MEU-Prep: Port, Repository, and Service Extensions (Prerequisite)

> Extends the approved Phase 2 port protocols + repositories ([ports.py](file:///p:/zorivest/packages/core/src/zorivest_core/application/ports.py), [repositories.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/repositories.py)) and Phase 3 service layer ([03-service-layer.md](file:///p:/zorivest/docs/build-plan/03-service-layer.md)) with missing methods required by Phase 4 routes.

**TDD order: tests FIRST → red → implementation → green**

#### [NEW] [test_service_extensions.py](file:///p:/zorivest/tests/unit/test_service_extensions.py)

Write tests FIRST (Red phase) covering:
- `TradeService.list_trades` with limit/offset/account_id/sort
- `TradeService.update_trade` — update fields, verify returned trade
- `TradeService.delete_trade` — delete, verify not found
- `AccountService.update_account` — update fields
- `AccountService.delete_account` — delete, verify not found
- `ImageService.get_image` — returns ImageAttachment or NotFoundError
- `ImageService.get_full_image` — returns bytes
- `ImageService.get_images_for_owner` — list by owner_type/owner_id
- `get_version()` returns SemVer string
- `get_version_context()` returns one of "frozen"/"installed"/"dev"

#### [MODIFY] [ports.py](file:///p:/zorivest/packages/core/src/zorivest_core/application/ports.py)

Extend port protocols:

**TradeRepository** — add:
- `delete(exec_id: str) -> None`
- `list_filtered(limit, offset, account_id=None, sort="-time") -> list[Trade]`
- `update(trade: Trade) -> None`

**AccountRepository** — add:
- `delete(account_id: str) -> None`
- `update(account: Account) -> None`

**ImageRepository** — add:
- `get_full_data(image_id: int) -> bytes` (returns raw image bytes without thumbnail processing)

#### [MODIFY] [repositories.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/repositories.py)

Implement new port methods:

**SqlAlchemyTradeRepository** — add:
- `delete(exec_id)` — get model, `session.delete()`, or raise NotFoundError
- `list_filtered(limit, offset, account_id, sort)` — query with optional filter + sort parsing
- `update(trade)` — `session.merge()` instead of `session.add()` for idempotent save

**SqlAlchemyAccountRepository** — add:
- `delete(account_id)` — get model, `session.delete()`
- `update(account)` — `session.merge()` for upsert-safe write

**SqlAlchemyImageRepository** — add:
- `get_full_data(image_id)` — returns `m.data` bytes directly

#### [MODIFY] [trade_service.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/trade_service.py)

Add methods:
- `list_trades(limit, offset, account_id=None, sort="-time")` → delegates to `uow.trades.list_filtered(...)`
- `update_trade(exec_id, **kwargs)` → get trade, apply updates, `uow.trades.update(trade)`, commit
- `delete_trade(exec_id)` → `uow.trades.delete(exec_id)`, commit

#### [MODIFY] [account_service.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/account_service.py)

Add methods:
- `update_account(account_id, **kwargs)` → get account, apply updates, `uow.accounts.update(account)`, commit
- `delete_account(account_id)` → `uow.accounts.delete(account_id)`, commit

#### [MODIFY] [image_service.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/image_service.py)

Add methods:
- `get_image(image_id)` → returns `ImageAttachment` or raises `NotFoundError`
- `get_full_image(image_id)` → delegates to `uow.images.get_full_data(image_id)`
- Rename `get_trade_images` → `get_images_for_owner(owner_type, owner_id)` for generality

#### [NEW] [version.py](file:///p:/zorivest/packages/core/src/zorivest_core/version.py)

Create version module (required by 04g `VersionResponse`):
- `get_version()` → resolution order: frozen constant (`_VERSION`) → `importlib.metadata` → `.version` file
- `get_version_context()` → returns `"frozen"` | `"installed"` | `"dev"` indicating resolution method

---

### MEU-23: `fastapi-routes` — App Factory + Foundation

> Build Plan: [04-rest-api.md](file:///p:/zorivest/docs/build-plan/04-rest-api.md) § App Factory, Lifespan, Middleware, Shared Schemas + [04g-api-system.md](file:///p:/zorivest/docs/build-plan/04g-api-system.md) § Health, Version

#### [NEW] Package scaffold

Create the `packages/api/` package structure:

```
packages/api/
├── pyproject.toml
└── src/
    └── zorivest_api/
        ├── __init__.py
        ├── main.py              # App factory + lifespan + middleware
        ├── dependencies.py      # DI providers (get_trade_service, etc.)
        ├── schemas/
        │   ├── __init__.py
        │   └── common.py        # PaginatedResponse, ErrorEnvelope
        ├── auth/
        │   ├── __init__.py
        │   └── auth_service.py  # Envelope encryption, session/key/token management
        └── routes/
            ├── __init__.py
            ├── health.py        # GET /api/v1/health
            └── version.py       # GET /api/v1/version/
```

#### [NEW] [pyproject.toml](file:///p:/zorivest/packages/api/pyproject.toml)

Package metadata: `zorivest-api`, depends on `fastapi`, `uvicorn`, `pydantic`, `httpx`, `cryptography`, `argon2-cffi`. Also depends on `zorivest-core` and `zorivest-infra` as workspace sources.

> Note: `cryptography` is forward-pulled from Phase 8 dependency manifest. `argon2-cffi` is already available (installed in Phase 2 for infrastructure). Both are required by the canonical 04c envelope-encryption contract.

#### [NEW] [main.py](file:///p:/zorivest/packages/api/src/zorivest_api/main.py)

- `create_app()` factory function returning `FastAPI` instance
- `lifespan()` async context manager — initializes `app.state.db` on startup, closes on shutdown
- `tags_metadata` list matching build plan (7 tags)
- CORS middleware via `allow_origin_regex=r"^http://localhost(:\d+)?$"` (per [FastAPI CORS docs](https://fastapi.tiangolo.com/tutorial/cors/))
- Request-ID middleware (generates UUID, attaches X-Request-ID header)
- Global exception handler → `ErrorEnvelope`
- `require_unlocked_db` dependency for mode-gating

#### [NEW] [common.py](file:///p:/zorivest/packages/api/src/zorivest_api/schemas/common.py)

- `PaginatedResponse[T]` — Generic Pydantic model with items, total, limit, offset
- `ErrorEnvelope` — error, detail, request_id

#### [NEW] [dependencies.py](file:///p:/zorivest/packages/api/src/zorivest_api/dependencies.py)

- `get_db()` — returns app-state database reference
- `get_trade_service()`, `get_account_service()`, `get_image_service()`, etc.
- `require_unlocked_db()` — raises 403 if DB is locked

#### [NEW] [health.py](file:///p:/zorivest/packages/api/src/zorivest_api/routes/health.py)

Canonical 04g `HealthResponse`:
- `GET /api/v1/health` → `HealthResponse(status, version, uptime_seconds, database)` (no auth required)
- `HealthResponse` fields: `status: str` ("ok"), `version: str`, `uptime_seconds: int`, `database: dict` ({"unlocked": bool})

#### [NEW] [version.py](file:///p:/zorivest/packages/api/src/zorivest_api/routes/version.py)

Canonical 04g `VersionResponse`:
- `GET /api/v1/version/` → `VersionResponse(version, context)` (no auth required)
- `VersionResponse` fields: `version: str` (SemVer), `context: str` ("frozen" | "installed" | "dev")
- Delegates to `zorivest_core.version.get_version()` and `get_version_context()`

#### [MODIFY] [pyproject.toml](file:///p:/zorivest/pyproject.toml)

Add `zorivest-api` to root `[project] dependencies` list and `[tool.uv.sources]` section (workspace source entry). The workspace membership is automatic via `members = ["packages/*"]`.

#### [NEW] [test_api_foundation.py](file:///p:/zorivest/tests/unit/test_api_foundation.py)

Tests for:
- App factory returns FastAPI instance with 7 tags
- Health endpoint returns 200 + `HealthResponse` with uptime_seconds + database.unlocked
- Version endpoint returns 200 + `VersionResponse` with context field
- Request-ID header is present in responses (UUID format)
- ErrorEnvelope format on unhandled exception (500)
- CORS headers present for `http://localhost:3000` origin, absent for other origins
- Mode-gating: 403 when DB locked
- PaginatedResponse schema validation (items, total, limit, offset)

---

### MEU-24: `api-trades` — Trade CRUD REST Endpoints

> Build Plan: [04a-api-trades.md](file:///p:/zorivest/docs/build-plan/04a-api-trades.md)

#### [NEW] [trades.py](file:///p:/zorivest/packages/api/src/zorivest_api/routes/trades.py)

- `POST /api/v1/trades` — create trade (201)
- `GET /api/v1/trades` — list trades via `TradeService.list_trades` with account_id filter + sort param
- `GET /api/v1/trades/{exec_id}` — get single trade
- `PUT /api/v1/trades/{exec_id}` — update trade via `TradeService.update_trade`
- `DELETE /api/v1/trades/{exec_id}` — delete trade via `TradeService.delete_trade` (204)
- `GET /api/v1/trades/{exec_id}/images` — list trade images via `ImageService.get_images_for_owner`
- `POST /api/v1/trades/{exec_id}/images` — upload image (multipart, WebP conversion via Pillow before `AttachImage`)

#### [NEW] [images.py](file:///p:/zorivest/packages/api/src/zorivest_api/routes/images.py)

- `GET /api/v1/images/{image_id}` — image metadata (delegates to `ImageService.get_image`)
- `GET /api/v1/images/{image_id}/thumbnail` — thumbnail bytes via `ImageService.get_thumbnail` (image/webp)
- `GET /api/v1/images/{image_id}/full` — full image bytes via `ImageService.get_full_image`

#### [NEW] [round_trips.py](file:///p:/zorivest/packages/api/src/zorivest_api/routes/round_trips.py)

- `GET /api/v1/round-trips` — list round-trips with filters (account_id, status, ticker)

#### [NEW] Trade schemas

- `CreateTradeRequest` — includes `time: datetime` (aligns with `CreateTrade` command)
- `UpdateTradeRequest` — partial update fields
- `TradeImageResponse` (Pydantic model)
- Image upload route handles: receive multipart → WebP conversion (Pillow) → extract width/height → create `AttachImage` command with `mime_type="image/webp"`

#### [MODIFY] [main.py](file:///p:/zorivest/packages/api/src/zorivest_api/main.py)

Include `trade_router`, `image_router`, `round_trip_router`.

#### [NEW] [test_api_trades.py](file:///p:/zorivest/tests/unit/test_api_trades.py)

Tests for all 11 trade routes:
- Trade CRUD lifecycle (create → get → update → delete)
- `CreateTradeRequest` includes `time` field
- List trades with pagination, account filter, sort
- Image upload + WebP conversion + retrieve thumbnail + full
- 404 on missing trade
- Round-trip list with filters

---

### MEU-25: `api-accounts` — Account REST Endpoints

> Build Plan: [04b-api-accounts.md](file:///p:/zorivest/docs/build-plan/04b-api-accounts.md)

#### [NEW] [accounts.py](file:///p:/zorivest/packages/api/src/zorivest_api/routes/accounts.py)

- `POST /api/v1/accounts` — create account (201)
- `GET /api/v1/accounts` — list accounts
- `GET /api/v1/accounts/{account_id}` — get account
- `PUT /api/v1/accounts/{account_id}` — update account via `AccountService.update_account`
- `DELETE /api/v1/accounts/{account_id}` — delete account via `AccountService.delete_account`
- `POST /api/v1/accounts/{account_id}/balances` — record balance snapshot

#### [NEW] Account schemas

- `CreateAccountRequest`, `AccountResponse`, `BalanceRequest` (Pydantic models)

#### [MODIFY] [main.py](file:///p:/zorivest/packages/api/src/zorivest_api/main.py)

Include `account_router`.

#### [NEW] [test_api_accounts.py](file:///p:/zorivest/tests/unit/test_api_accounts.py)

Tests for all 6 account routes:
- Account CRUD lifecycle
- Balance recording
- 404 on missing account
- Validation errors (missing required fields)

---

### MEU-26: `api-auth` — Auth REST Endpoints (Full 04c Contract)

> Build Plan: [04c-api-auth.md](file:///p:/zorivest/docs/build-plan/04c-api-auth.md)

#### [NEW] [auth.py](file:///p:/zorivest/packages/api/src/zorivest_api/routes/auth.py)

- `POST /api/v1/auth/unlock` — full envelope-encryption unlock flow:
  1. Receive `api_key` in request body
  2. Hash → lookup in `bootstrap.json` key entries
  3. Argon2id KDF → derive KEK from API key
  4. Unwrap DEK using KEK (Fernet decrypt)
  5. Apply `PRAGMA key` with unwrapped DEK (via `zorivest_infra.database.connection`)
  6. Return `UnlockResponse` with session token, role, scopes, expires_in
  7. Error modes: 401 (invalid key), 403 (revoked), 423 (lock contention)
- `POST /api/v1/auth/lock` — lock database, invalidate active sessions
- `GET /api/v1/auth/status` — auth state (locked/unlocked)
- `POST /api/v1/auth/keys` — create API key: generate key, hash for lookup, wrap DEK entry into `bootstrap.json`, return raw key once (201)
- `GET /api/v1/auth/keys` — list API keys (masked, never plaintext)
- `DELETE /api/v1/auth/keys/{key_id}` — revoke key, remove DEK entry from `bootstrap.json` (204)

#### [NEW] [confirmation.py](file:///p:/zorivest/packages/api/src/zorivest_api/routes/confirmation.py)

- `POST /api/v1/confirmation-tokens` — generate time-limited confirmation token (201)
- Validates against `VALID_DESTRUCTIVE_ACTIONS` set
- Returns `ctk_` prefixed token with 60s TTL

#### [NEW] Auth schemas

- `UnlockRequest` (api_key), `UnlockResponse` (session_token, role, scopes, expires_in)
- `KeyCreateRequest` (name, role), `KeyInfo` (key_id, name, role, created_at, masked_key)
- `ConfirmationRequest` (action), `ConfirmationResponse` (token, expires_in_seconds)

#### [NEW] [auth_service.py](file:///p:/zorivest/packages/api/src/zorivest_api/auth/auth_service.py)

`AuthService` module encapsulating the envelope-encryption flow:
- `bootstrap.json` persistence (read/write wrapped DEK entries)
- Argon2id KDF key derivation (via `argon2-cffi`)
- Fernet-based DEK wrapping/unwrapping (via `cryptography`)
- In-memory session token store (dict with TTL expiry)
- In-memory confirmation token store (TTL cache, `ctk_` prefix)
- API key hash storage + masked listing
- Integration with `zorivest_infra.database.connection` for `PRAGMA key` application (mocked in unit tests)

#### [MODIFY] [main.py](file:///p:/zorivest/packages/api/src/zorivest_api/main.py)

Include `auth_router`, `confirm_router`.

#### [NEW] [test_api_auth.py](file:///p:/zorivest/tests/unit/test_api_auth.py)

Tests for all 7 auth routes (SQLCipher mocked via `zorivest_infra.database.connection`):
- Unlock with valid key → session token returned
- Unlock with invalid key → 401
- Unlock with revoked key → 403
- Unlock when already unlocked → 423 (lock contention)
- Lock invalidates session
- Status reflects locked/unlocked state
- API key CRUD lifecycle (create → list → delete)
- Created key is masked in list response (never plaintext)
- Key revocation removes DEK entry
- Confirmation token creation for valid destructive action (201)
- Confirmation token rejection for unknown action (400)
- Token prefix is `ctk_`
- Token includes 60s TTL

---

### Cross-cutting: BUILD_PLAN.md + Dependency Manifest Updates

#### [MODIFY] [BUILD_PLAN.md](file:///p:/zorivest/docs/BUILD_PLAN.md)

- Phase 4 status: ⚪ Not Started → 🔵 In Progress (during execution) → update completed MEU counts
- MEU-23 through MEU-26 status: ⬜ → ✅ (after Codex approval)
- MEU Summary table: P0 Phase 3/4 completed count 1 → 5

#### [MODIFY] [dependency-manifest.md](file:///p:/zorivest/docs/build-plan/dependency-manifest.md)

- Add `cryptography` to Phase 4 REST API line (forward-pull from Phase 8, required by 04c auth)
- Note: `argon2-cffi` already listed in Phase 2 (infrastructure)

**Validation:** `rg -c "⬜" docs/BUILD_PLAN.md` to verify only expected MEUs remain pending.

---

## Spec Sufficiency

### MEU-23: fastapi-routes

| Behavior | Source Type | Source | Resolved? |
|---|---|---|---|
| App factory with openapi_tags | Spec | 04-rest-api.md §App Factory | ✅ |
| Lifespan with SQLCipher init | Spec | 04-rest-api.md §Lifespan | ✅ |
| CORS via `allow_origin_regex` | Spec + Research | 04-rest-api.md §Middleware + FastAPI CORS docs | ✅ |
| Request-ID middleware | Spec | 04-rest-api.md §Middleware | ✅ |
| Error handler → ErrorEnvelope | Spec | 04-rest-api.md §Middleware | ✅ |
| Mode-gating dependency | Spec | 04-rest-api.md §Mode-Gating | ✅ |
| PaginatedResponse[T] | Spec | 04-rest-api.md §Shared Schemas | ✅ |
| ErrorEnvelope schema | Spec | 04-rest-api.md §Shared Schemas | ✅ |
| Health endpoint (HealthResponse) | Spec | 04g-api-system.md §Health | ✅ |
| Version endpoint (VersionResponse) | Spec | 04g-api-system.md §Version | ✅ |
| `get_version()` + `get_version_context()` | Spec | 04g-api-system.md §Version | ✅ (new module) |
| Package deps: fastapi, uvicorn, pydantic, httpx, cryptography | Local Canon + Amendment | dependency-manifest.md (Phase 4 + 04c forward-pull) | ✅ |

### MEU-24: api-trades

| Behavior | Source Type | Source | Resolved? |
|---|---|---|---|
| Trade CRUD (5 routes) | Spec | 04a §Trade CRUD | ✅ |
| Trade image routes (2) | Spec | 04a §Image Routes | ✅ |
| Global image routes (3) | Spec | 04a §Image Routes (Global) | ✅ |
| Round-trip list route | Spec | 04a §Round-Trip | ✅ |
| Sort param + account_id filter | Spec | 04a list_trades | ✅ |
| CreateTradeRequest includes `time` | Spec | 04a + CreateTrade command contract | ✅ |
| Image upload: WebP + width/height | Spec | AttachImage command contract | ✅ |
| Service deps: list_filtered, update, delete | Local Canon | ports.py + repositories.py extension (MEU-Prep) | ✅ |
| Trade reports | Local Canon | BUILD_PLAN.md §P1 item 17 | N/A (deferred: MEU-52) |
| Trade plans | Local Canon | BUILD_PLAN.md §P2 item 31 | N/A (deferred: MEU-66) |
| Journal linking | Local Canon | BUILD_PLAN.md §P2.75 item 68.4e | N/A (deferred: MEU-117) |

### MEU-25: api-accounts

| Behavior | Source Type | Source | Resolved? |
|---|---|---|---|
| Account CRUD (5 routes) | Spec | 04b §Account Routes | ✅ |
| Balance recording | Spec | 04b §Account Routes | ✅ |
| CreateAccountRequest schema | Spec | 04b code snippet | ✅ |
| Service deps: update, delete | Local Canon | ports.py + repositories.py extension (MEU-Prep) | ✅ |
| Broker/banking/import/identifiers | Local Canon | BUILD_PLAN.md §P2.75 items 50e–57e | N/A (deferred: MEU-96–103) |

### MEU-26: api-auth

| Behavior | Source Type | Source | Resolved? |
|---|---|---|---|
| Unlock/lock/status | Spec | 04c §Auth/Unlock | ✅ |
| Envelope encryption (Argon2id→KEK→DEK) | Spec | 04c §Auth/Unlock | ✅ |
| bootstrap.json persistence | Spec + Local Canon | 04c + 02-infrastructure.md §SQLCipher | ✅ |
| PRAGMA key via `zorivest_infra.database.connection` | Local Canon | packages/infrastructure (verified module path) | ✅ |
| API key management (3 routes) | Spec | 04c §API Key | ✅ |
| Key revocation removes DEK entry | Spec | 04c §API Key | ✅ |
| Error modes: 401/403/423 | Spec | 04c §Auth/Unlock | ✅ |
| Confirmation token (1 route) | Spec | 04c §Confirmation | ✅ |
| VALID_DESTRUCTIVE_ACTIONS list | Spec | 04c code snippet | ✅ |
| Session token (in-memory TTL) | Spec | 04c UnlockResponse | ✅ |
| `cryptography` dependency | Amendment | dependency-manifest.md forward-pull from Phase 8 | ✅ |

---

## FIC — Feature Intent Contracts

### MEU-23 FIC: fastapi-routes

| AC | Description | Source |
|---|---|---|
| AC-1 | `create_app()` returns a FastAPI instance with 7 tags | Spec |
| AC-2 | Lifespan initializes `app.state.db` on startup, closes on shutdown | Spec |
| AC-3 | CORS allows localhost origins via `allow_origin_regex=r"^http://localhost(:\d+)?$"` | Spec + Research |
| AC-4 | Every response includes `X-Request-ID` header (UUID) | Spec |
| AC-5 | Unhandled exceptions return `ErrorEnvelope` JSON with 500 status | Spec |
| AC-6 | `require_unlocked_db` raises 403 when DB is locked | Spec |
| AC-7 | `GET /api/v1/health` returns 200 `HealthResponse` with `status`, `version`, `uptime_seconds`, `database.unlocked` | Spec |
| AC-8 | `GET /api/v1/version/` returns 200 `VersionResponse` with `version` (SemVer) and `context` (frozen/installed/dev) | Spec |
| AC-9 | `PaginatedResponse` schema has items, total, limit, offset fields | Spec |
| AC-10 | `ErrorEnvelope` schema has error, detail, request_id fields | Spec |

### MEU-24 FIC: api-trades

| AC | Description | Source |
|---|---|---|
| AC-1 | `POST /trades` creates trade with `time` field and returns 201 with exec_id | Spec |
| AC-2 | `GET /trades` returns paginated list via `list_filtered`; supports `account_id` filter | Spec |
| AC-3 | `GET /trades` supports `sort` param with `-` prefix for descending | Spec |
| AC-4 | `GET /trades/{exec_id}` returns trade or 404 | Spec |
| AC-5 | `PUT /trades/{exec_id}` updates only provided fields via `update_trade` | Spec |
| AC-6 | `DELETE /trades/{exec_id}` returns 204 via `delete_trade` | Spec |
| AC-7 | `POST /trades/{exec_id}/images` accepts multipart, converts to WebP, extracts width/height | Spec |
| AC-8 | `GET /trades/{exec_id}/images` returns list of `TradeImageResponse` via `get_images_for_owner` | Spec |
| AC-9 | `GET /images/{id}/thumbnail` returns image/webp bytes | Spec |
| AC-10 | `GET /images/{id}/full` returns full image bytes via `get_full_image` | Spec |
| AC-11 | `GET /round-trips` returns list; supports status/ticker/account_id filters | Spec |

### MEU-25 FIC: api-accounts

| AC | Description | Source |
|---|---|---|
| AC-1 | `POST /accounts` creates account and returns 201 | Spec |
| AC-2 | `GET /accounts` returns list of all accounts | Spec |
| AC-3 | `GET /accounts/{id}` returns account or 404 | Spec |
| AC-4 | `PUT /accounts/{id}` updates account via `update_account` | Spec |
| AC-5 | `DELETE /accounts/{id}` deletes account via `delete_account` | Spec |
| AC-6 | `POST /accounts/{id}/balances` records balance snapshot | Spec |

### MEU-26 FIC: api-auth

| AC | Description | Source |
|---|---|---|
| AC-1 | `POST /auth/unlock` performs envelope-encryption flow and returns session token, role, scopes, expires_in | Spec |
| AC-2 | `POST /auth/unlock` with invalid key returns 401 | Spec |
| AC-3 | `POST /auth/unlock` with revoked key returns 403 | Spec |
| AC-4 | `POST /auth/unlock` when already unlocked returns 423 | Spec |
| AC-5 | `POST /auth/lock` invalidates active sessions and locks DB | Spec |
| AC-6 | `GET /auth/status` reflects locked/unlocked state | Spec |
| AC-7 | `POST /auth/keys` creates API key, wraps DEK into bootstrap.json, returns raw key once (201) | Spec |
| AC-8 | `GET /auth/keys` returns masked key list (never plaintext) | Spec |
| AC-9 | `DELETE /auth/keys/{key_id}` revokes key, removes DEK entry (204) | Spec |
| AC-10 | `POST /confirmation-tokens` returns `ctk_` token for valid action (201) | Spec |
| AC-11 | `POST /confirmation-tokens` rejects unknown actions (400) | Spec |
| AC-12 | Confirmation token includes 60s TTL | Spec |

---

## Task Table

| # | Task | Owner Role | Deliverable | Validation | Status |
|---|---|---|---|---|---|
| 0a | Create `packages/api` scaffold + pyproject.toml (incl. `cryptography`) | coder | Package files | `uv sync` succeeds | ⬜ |
| 0b | Add `zorivest-api` to root pyproject.toml deps + sources | coder | Modified pyproject.toml | `uv sync` succeeds | ⬜ |
| 0c | **MEU-Prep: Write tests FIRST** (Red phase) | coder | test_service_extensions.py | Tests FAIL (no impl) | ⬜ |
| 0d | Extend ports.py (TradeRepo delete/list_filtered/update, AccountRepo delete/update, ImageRepo get_full_data) | coder | Modified ports.py | Ports protocol updated | ⬜ |
| 0e | Extend repositories.py (implement new port methods) | coder | Modified repositories.py | Tests pass | ⬜ |
| 0f | Extend TradeService (list_trades/update_trade/delete_trade) | coder | Modified trade_service.py | Tests pass | ⬜ |
| 0g | Extend AccountService (update_account/delete_account) | coder | Modified account_service.py | Tests pass | ⬜ |
| 0h | Extend ImageService (get_image/get_full_image/rename) | coder | Modified image_service.py | Tests pass | ⬜ |
| 0i | Create version.py (get_version + get_version_context) | coder | New zorivest_core/version.py | Tests pass | ⬜ |
| 0j | Verify all MEU-Prep tests GREEN | coder | test_service_extensions.py | All pass | ⬜ |
| 1 | MEU-23: Write tests (Red phase) | coder | `test_api_foundation.py` | Tests fail (no impl) | ⬜ |
| 2 | MEU-23: Implement app factory + routes (Green phase) | coder | main.py, schemas, routes | Tests pass | ⬜ |
| 3 | MEU-23: Refactor | coder | Clean code | Tests still pass | ⬜ |
| 4 | MEU-23: Create handoff 024 | coder | Handoff artifact | File exists | ⬜ |
| 5 | MEU-24: Write tests (Red phase) | coder | `test_api_trades.py` | Tests fail | ⬜ |
| 6 | MEU-24: Implement trade routes (Green phase) | coder | trades.py, images.py, round_trips.py | Tests pass | ⬜ |
| 7 | MEU-24: Refactor | coder | Clean code | Tests still pass | ⬜ |
| 8 | MEU-24: Create handoff 025 | coder | Handoff artifact | File exists | ⬜ |
| 9 | MEU-25: Write tests (Red phase) | coder | `test_api_accounts.py` | Tests fail | ⬜ |
| 10 | MEU-25: Implement account routes (Green phase) | coder | accounts.py | Tests pass | ⬜ |
| 11 | MEU-25: Refactor | coder | Clean code | Tests still pass | ⬜ |
| 12 | MEU-25: Create handoff 026 | coder | Handoff artifact | File exists | ⬜ |
| 13 | MEU-26: Write tests (Red phase) | coder | `test_api_auth.py` | Tests fail | ⬜ |
| 14 | MEU-26: Implement auth routes + AuthService (Green phase) | coder | auth.py, confirmation.py, auth_service.py | Tests pass | ⬜ |
| 15 | MEU-26: Refactor | coder | Clean code | Tests still pass | ⬜ |
| 16 | MEU-26: Create handoff 027 | coder | Handoff artifact | File exists | ⬜ |
| 17 | Update BUILD_PLAN.md + dependency-manifest.md | coder | Updated status + deps | No stale references | ⬜ |
| 18 | Update MEU registry | coder | Updated registry | MEU-23–26 rows | ⬜ |
| 19 | Run MEU gate | tester | Gate output | All pass | ⬜ |
| 20 | Run full regression | tester | `pytest` output | All green | ⬜ |
| 21 | Create reflection | coder | Reflection file | File exists | ⬜ |
| 22 | Update metrics | coder | metrics.md | Row added | ⬜ |
| 23 | Save session state | coder | pomera note | Note ID | ⬜ |
| 24 | Propose commit messages | coder | Message text | Presented | ⬜ |

---

## Verification Plan

### Automated Tests

All tests run via TestClient (no live server required):

```powershell
# Per-MEU test runs
uv run pytest tests/unit/test_service_extensions.py -v --tb=short -m unit
uv run pytest tests/unit/test_api_foundation.py -v --tb=short -m unit
uv run pytest tests/unit/test_api_trades.py -v --tb=short -m unit
uv run pytest tests/unit/test_api_accounts.py -v --tb=short -m unit
uv run pytest tests/unit/test_api_auth.py -v --tb=short -m unit

# Full API test suite
uv run pytest tests/unit/test_api_*.py tests/unit/test_service_extensions.py -v --tb=short

# Full regression (all tests)
uv run pytest tests/ -v

# Type checking
uv run pyright packages/api/ packages/core/src/zorivest_core/version.py

# Linting
uv run ruff check packages/api/ packages/core/ packages/infrastructure/

# MEU gate
uv run python tools/validate_codebase.py --scope meu

# Anti-placeholder scan
rg "TODO|FIXME|NotImplementedError" packages/api/ packages/core/src/zorivest_core/version.py
```

### Manual Verification

None required — all routes tested via automated TestClient tests.

---

## Handoff Files

| MEU | Handoff Path |
|---|---|
| MEU-23 | `.agent/context/handoffs/024-2026-03-08-fastapi-routes-bp04s4.0.md` |
| MEU-24 | `.agent/context/handoffs/025-2026-03-08-api-trades-bp04as4a.md` |
| MEU-25 | `.agent/context/handoffs/026-2026-03-08-api-accounts-bp04bs4b.md` |
| MEU-26 | `.agent/context/handoffs/027-2026-03-08-api-auth-bp04cs4c.md` |

---

## Stop Conditions

- **Stop for human** if: `uv sync` fails to resolve workspace dependencies — may indicate a `pyproject.toml` configuration issue
- **Stop for human** if: Argon2id/Fernet integration reveals undocumented behavior requiring design decision
- **Continue** if: tests fail during Red phase (expected) — proceed to Green phase
- **Continue** if: type checking reveals missing type stubs — add `# type: ignore` with justification
