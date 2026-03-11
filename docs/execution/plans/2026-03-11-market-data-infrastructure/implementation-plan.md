# Market Data Infrastructure — Implementation Plan

> **Project slug:** `market-data-infrastructure`
> **Date:** 2026-03-11
> **MEUs:** 59, 62, 60 (in execution order)
> **Build plan:** [08-market-data.md](file:///p:/zorivest/docs/build-plan/08-market-data.md) §8.2c, §8.2e, §8.2d, §8.3a, §8.6
> **Phase:** 8 — Market Data Aggregation (P1.5)

---

## Goal

Implement the **infrastructure layer** for market data: the provider registry (12 static provider configs), async token-bucket rate limiter, log redaction utility, and the ProviderConnectionService (test/configure/list/remove provider connections). These are inner-layer components with no REST or MCP surface — they sit between the already-implemented domain entities (MEU-56/57/58) and the upcoming outer layers (MEU-61 MarketDataService, MEU-63 REST routes, MEU-64 MCP tools).

---

## Carry-Forward Rules (from reflection 2026-03-11)

1. Port contracts must use typed returns, never `Any`
2. DTO coverage must include ALL models with serialization tests
3. Run full MEU gate BEFORE claiming completion
4. BUILD_PLAN.md row statuses AND summary table must agree
5. Evidence counts need a final refresh just before handoff

---

## Project Scope

### In-Scope

| MEU | Slug | Build Plan Section | Description |
|-----|------|--------------------|-------------|
| MEU-59 | `market-provider-registry` | §8.2c | `PROVIDER_REGISTRY` dict (12 providers) + lookup helpers |
| MEU-62 | `market-rate-limiter` | §8.2e + §8.2d | Async `RateLimiter` (token-bucket) + `mask_api_key` / `sanitize_url_for_logging` |
| MEU-60 | `market-connection-svc` | §8.3a + §8.6 | `ProviderConnectionService` (test, configure, list, remove) + `MarketProviderSettingsRepository` port + UoW extension |

### Out-of-Scope

- MEU-61 `market-data-service` (MarketDataService — depends on MEU-60)
- MEU-63 `market-data-api` (REST routes — depends on MEU-61)
- MEU-64 `market-data-mcp` (MCP tools — depends on MEU-63)
- MEU-65 `market-data-gui` (GUI settings — depends on MEU-63)
- Response normalizers (part of MEU-61)

### Execution Order

```
MEU-59 (registry) → MEU-62 (rate limiter + log redaction) → MEU-60 (connection service + persistence layer)
```

---

## Spec Sufficiency

### MEU-59: Provider Registry

| Behavior / Contract | Source Type | Source | Resolved? | Notes |
|---------------------|------------|--------|-----------|-------|
| 12 providers with ProviderConfig entries | Spec | [08 §8.2c](file:///p:/zorivest/docs/build-plan/08-market-data.md#L208-350) | ✅ | All 12 provider configs fully specified |
| ProviderConfig frozen dataclass | Spec | [08 §8.1b](file:///p:/zorivest/docs/build-plan/08-market-data.md#L65-86) | ✅ | Already implemented in MEU-56 |
| AuthMethod enum | Spec | [08 §8.1a](file:///p:/zorivest/docs/build-plan/08-market-data.md#L52-63) | ✅ | Already implemented in MEU-56 |
| Lookup by provider name | Local Canon | `ProviderConnectionService` uses `PROVIDER_REGISTRY[name]` in §8.3a | ✅ | Dict keyed by provider name |
| `get_provider_config(name)` helper | Spec | §8.2c (implicit) | ✅ | Typed helper, `KeyError` for unknown |
| `list_provider_names()` helper | Spec | §8.3a `list_providers()` iterates all | ✅ | Convenience function |

### MEU-62: Rate Limiter + Log Redaction

| Behavior / Contract | Source Type | Source | Resolved? | Notes |
|---------------------|------------|--------|-----------|-------|
| Token-bucket rate limiter | Spec | [08 §8.2e](file:///p:/zorivest/docs/build-plan/08-market-data.md#L375-401) | ✅ | `RateLimiter(max_per_minute)` with sliding window `deque` |
| `async wait_if_needed()` blocks until slot | Spec | §8.2e | ✅ | Pops expired timestamps, sleeps if full |
| `mask_api_key(key) → "[REDACTED]"` | Spec | [08 §8.2d](file:///p:/zorivest/docs/build-plan/08-market-data.md#L353-373) | ✅ | Full replacement per security policy |
| `sanitize_url_for_logging(text, api_key)` | Spec | §8.2d | ✅ | Replace key with `[REDACTED]` in any string |
| Log redaction delegates to central policy | Spec | §8.2d + 01a-logging.md | ✅ | Already done in MEU-1A |
| Rate limiter per-provider | Spec | §8.3b `rate_limiters: dict[str, RateLimiter]` | ✅ | Each provider gets own instance |

### MEU-60: ProviderConnectionService

| Behavior / Contract | Source Type | Source | Resolved? | Notes |
|---------------------|------------|--------|-----------|-------|
| `list_providers() → list[ProviderStatus]` | Spec | [08 §8.3a](file:///p:/zorivest/docs/build-plan/08-market-data.md#L407-438) + [§8.6 L706-715](file:///p:/zorivest/docs/build-plan/08-market-data.md#L706-715) + [06f L65-72](file:///p:/zorivest/docs/build-plan/06f-gui-settings.md#L65-72) | ✅ | `ProviderStatus` Pydantic model with fields: `provider_name`, `is_enabled`, `has_api_key`, `rate_limit`, `timeout`, `last_test_status` |
| `configure_provider(name, api_key?, api_secret?, rate_limit?, timeout?, is_enabled?)` | Spec | [§8.3a](file:///p:/zorivest/docs/build-plan/08-market-data.md#L529-540) + [§8.4 ProviderConfigRequest](file:///p:/zorivest/docs/build-plan/08-market-data.md#L554-560) | ✅ | PATCH semantics: all params optional, only update provided fields. `is_enabled` flows through service per REST contract |
| `test_connection(provider_name) → (bool, str)` | Spec | §8.3a + [§8.6](file:///p:/zorivest/docs/build-plan/08-market-data.md#L669-716) | ✅ | Provider-specific validation rules (see FIC below) |
| `remove_api_key(provider_name)` | Spec | §8.3a | ✅ | Remove key, disable provider |
| Provider-specific response validation | Spec | [§8.6 validation table](file:///p:/zorivest/docs/build-plan/08-market-data.md#L673-683) | ✅ | 9 providers with multi-branch rules |
| HTTP status interpretation | Spec | §8.6 HTTP Status table | ✅ | 6 status scenarios including 200+unexpected JSON |
| Concurrency guard (Semaphore) for test_all | Spec | §8.6 `asyncio.Semaphore(2)` | ✅ | Limit concurrent tests |
| `test_all_providers() → list[(name, success, msg)]` | Spec | §8.6 | ✅ | Guarded concurrent test of enabled providers |
| Dual-key support (Alpaca) | Spec | §8.2c + §8.3a `api_secret` | ✅ | `configure_provider` accepts optional `api_secret` |
| Fernet encryption on store | Local Canon | [api_key_encryption.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/security/api_key_encryption.py) (MEU-58) | ✅ | Already implemented |
| MarketProviderSettingModel persistence | Local Canon | [models.py L197-211](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/models.py#L197-L211) (MEU-58) | ✅ | Already implemented. Core-owned `MarketProviderSettings` dataclass maps to this ORM model at the infra boundary. |
| `MarketProviderSettingsRepository` protocol | Local Canon | [ports.py UoW pattern](file:///p:/zorivest/packages/core/src/zorivest_core/application/ports.py#L142-159) | ✅ | New repo protocol needed — follows same pattern as `SettingsRepository`, `TradeRepository`, etc. |
| `UnitOfWork` extension with `market_provider_settings` attr | Local Canon | UoW pattern at ports.py:142-159 | ✅ | Add new attribute to UoW Protocol + concrete impl |

---

## Feature Intent Contracts (FICs)

### FIC-59: Provider Registry

**Purpose:** Static registry of all 12 market data provider configurations.

| AC | Description | Source |
|----|-------------|--------|
| AC-1 | `PROVIDER_REGISTRY` is a `dict[str, ProviderConfig]` with exactly 12 entries | Spec §8.2c |
| AC-2 | Each entry has all required fields populated (name, base_url, auth_method, auth_param_name, headers_template, test_endpoint, default_rate_limit) | Spec §8.2c |
| AC-3 | Provider names match spec exactly: "Alpha Vantage", "Polygon.io", "Finnhub", "Financial Modeling Prep", "EODHD", "Nasdaq Data Link", "SEC API", "API Ninjas", "Benzinga", "OpenFIGI", "Alpaca", "Tradier" | Spec §8.2c |
| AC-4 | `get_provider_config(name)` returns `ProviderConfig` for known providers, raises `KeyError` for unknown | Local Canon |
| AC-5 | `list_provider_names()` returns sorted list of all 12 provider names | Local Canon |
| AC-6 | Auth methods match spec: Alpha Vantage=QUERY_PARAM, Polygon.io=BEARER_HEADER, Finnhub=CUSTOM_HEADER, FMP=QUERY_PARAM, EODHD=QUERY_PARAM, Nasdaq=QUERY_PARAM, SEC API=RAW_HEADER, API Ninjas=CUSTOM_HEADER, Benzinga=QUERY_PARAM, OpenFIGI=CUSTOM_HEADER, Alpaca=CUSTOM_HEADER, Tradier=BEARER_HEADER | Spec §8.2c + §8.7 |

### FIC-62: Rate Limiter + Log Redaction

**Purpose:** Async token-bucket rate limiter and API key log redaction utilities.

| AC | Description | Source |
|----|-------------|--------|
| AC-1 | `RateLimiter(max_per_minute=N)` enforces N requests per 60-second sliding window | Spec §8.2e |
| AC-2 | `wait_if_needed()` is async and blocks (via `asyncio.sleep`) when window is full | Spec §8.2e |
| AC-3 | Expired timestamps (older than 60s) are evicted on each call | Spec §8.2e |
| AC-4 | Burst of N requests completes without blocking; request N+1 blocks | Spec §8.2e |
| AC-5 | `mask_api_key(key)` always returns `"[REDACTED]"` regardless of key length | Spec §8.2d |
| AC-6 | `sanitize_url_for_logging(text, api_key)` replaces all occurrences of the key with `"[REDACTED]"` | Spec §8.2d |
| AC-7 | `sanitize_url_for_logging` with empty or short (<= 4 char) key returns text unchanged | Spec §8.2d |

### FIC-60: ProviderConnectionService

**Purpose:** Service for managing provider credentials and testing connectivity, with typed `ProviderStatus` return and provider-specific connection validation.

| AC | Description | Source |
|----|-------------|--------|
| AC-1 | `ProviderStatus` is a Pydantic model with fields: `provider_name: str`, `is_enabled: bool`, `has_api_key: bool`, `rate_limit: int`, `timeout: int`, `last_test_status: str | None` | Spec §8.6 L706 + 06f L65-72 |
| AC-2 | `list_providers()` returns `list[ProviderStatus]` with all 12 providers | Spec §8.3a |
| AC-3 | `configure_provider(name, api_key?, api_secret?, rate_limit?, timeout?, is_enabled?)` — all params optional, PATCH semantics: only update provided fields | Spec §8.4 ProviderConfigRequest L554-560 |
| AC-4 | `configure_provider` encrypts key via Fernet and persists a core-owned `MarketProviderSettings` entity through UoW | Spec §8.3a + Local Canon |
| AC-5 | `configure_provider` with already-encrypted key (ENC: prefix) passes through without double-encryption | Local Canon (api_key_encryption.py) |
| AC-6 | `configure_provider` with `is_enabled=True/False` updates the `is_enabled` column | Spec §8.4 L538 |
| AC-7 | Alpha Vantage test: success when `"Global Quote"` OR `"Time Series"` top-level key exists | Spec §8.6 L675 |
| AC-8 | Polygon.io test: success when `"results"` OR `"status"` top-level key exists | Spec §8.6 L676 |
| AC-9 | Finnhub test: success when `"c"` key exists AND no `"error"` key | Spec §8.6 L677 |
| AC-10 | FMP test: success when response is non-empty list, OR dict with `"Legacy Endpoint"` in error (HTTP 403) | Spec §8.6 L678 |
| AC-11 | EODHD test: success when `"code"` OR `"close"` top-level key exists | Spec §8.6 L679 |
| AC-12 | Nasdaq test: success when nested `datatable.data` exists | Spec §8.6 L680 |
| AC-13 | SEC API test: success when response is a list; if non-empty, first item has `"ticker"` or `"cik"` | Spec §8.6 L681 |
| AC-14 | API Ninjas test: success when both `"price"` AND `"name"` keys exist | Spec §8.6 L682 |
| AC-15 | Benzinga test: success when response is list, OR dict with `"data"` array | Spec §8.6 L683 |
| AC-16 | HTTP 200 + unexpected JSON → `(False, "Connected but unexpected response")` | Spec §8.6 L690 |
| AC-17 | HTTP 401 → `(False, "Invalid API key")` | Spec §8.6 L691 |
| AC-18 | HTTP 429 → `(False, "Rate limit exceeded")` | Spec §8.6 L693 |
| AC-19 | Timeout → `(False, "Connection timeout")` | Spec §8.6 L694 |
| AC-20 | ConnectionError → `(False, "Connection failed")` | Spec §8.6 L695 |
| AC-21 | `remove_api_key(name)` clears encrypted_api_key/secret and sets is_enabled=False | Spec §8.3a |
| AC-22 | `test_all_providers()` uses `asyncio.Semaphore(2)` to limit concurrent tests | Spec §8.6 L703 |
| AC-23 | `test_all_providers()` only tests providers that have API keys configured | Spec §8.6 L711 |
| AC-24 | Connection test updates `last_tested_at` and `last_test_status` in the DB | Spec §8.3a (implied) |
| AC-25 | All HTTP calls use the rate limiter's `wait_if_needed()` before making requests | Spec §8.2e + §8.3b |
| AC-26 | Dual-key provider (Alpaca) correctly stores both `api_key` and `api_secret` | Spec §8.2c |
| AC-27 | OpenFIGI, Alpaca, Tradier (no validation table entry) — success when HTTP 200 + valid JSON (any shape) | Spec §8.6 (implicit: not in table = generic check) |
| AC-28 | `MarketProviderSettingsRepository` protocol defines `get(name) → Model | None`, `save(model)`, `list_all() → list[Model]`, `delete(name)` | Local Canon (UoW pattern) |
| AC-29 | `UnitOfWork` protocol extended with `market_provider_settings: MarketProviderSettingsRepository` attribute | Local Canon (ports.py:142-159) |
| AC-30 | Concrete `SqlMarketProviderSettingsRepository` implements the protocol using SQLAlchemy, mapping between core `MarketProviderSettings` and ORM `MarketProviderSettingModel` | Local Canon (repositories.py pattern) |

---

## Proposed Changes

### MEU-59: Provider Registry

#### [NEW] [provider_registry.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/market_data/provider_registry.py)

New module containing:
- `PROVIDER_REGISTRY: dict[str, ProviderConfig]` — all 12 provider configs from spec §8.2c
- `get_provider_config(name: str) -> ProviderConfig` — typed lookup with KeyError
- `list_provider_names() -> list[str]` — sorted list of all provider names

#### [NEW] [__init__.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/market_data/__init__.py)

Package init for `zorivest_infra.market_data`.

#### [NEW] [test_provider_registry.py](file:///p:/zorivest/tests/unit/test_provider_registry.py)

Tests:
- Registry contains exactly 12 providers
- All provider names match spec
- All auth methods match spec
- `get_provider_config` returns correct config
- `get_provider_config` raises `KeyError` for unknown
- `list_provider_names` returns sorted list of 12 names
- Each provider has non-empty `base_url`, `test_endpoint`, `auth_param_name`
- Each provider has `default_rate_limit > 0`

---

### MEU-62: Rate Limiter + Log Redaction

#### [NEW] [rate_limiter.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/market_data/rate_limiter.py)

Async token-bucket `RateLimiter` class from spec §8.2e.

#### [NEW] [log_redaction.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/security/log_redaction.py)

`mask_api_key()` and `sanitize_url_for_logging()` from spec §8.2d. Placed in `security/` per spec §8.2d location.

#### [NEW] [test_rate_limiter.py](file:///p:/zorivest/tests/unit/test_rate_limiter.py)

Tests:
- Burst of N requests completes without blocking
- Request N+1 blocks until a slot opens
- Expired timestamps are evicted
- Multiple sequential calls with time advancement work correctly

#### [NEW] [test_log_redaction.py](file:///p:/zorivest/tests/unit/test_log_redaction.py)

Tests:
- `mask_api_key` returns `"[REDACTED]"` for any key
- `mask_api_key` returns `"[REDACTED]"` for empty string
- `sanitize_url_for_logging` replaces key in URL
- `sanitize_url_for_logging` with short key (<= 4) returns unchanged
- `sanitize_url_for_logging` with empty key returns unchanged
- `sanitize_url_for_logging` replaces multiple occurrences

---

### MEU-60: ProviderConnectionService + Persistence Layer

#### [NEW] [provider_status.py](file:///p:/zorivest/packages/core/src/zorivest_core/application/provider_status.py)

`ProviderStatus` Pydantic model with fields matching §8.6 and 06f GUI contract:
- `provider_name: str`
- `is_enabled: bool`
- `has_api_key: bool`
- `rate_limit: int`
- `timeout: int`
- `last_test_status: str | None`

#### [MODIFY] [ports.py](file:///p:/zorivest/packages/core/src/zorivest_core/application/ports.py)

Add `MarketProviderSettingsRepository` protocol (uses core-owned `MarketProviderSettings`, not infra ORM model):
- `get(provider_name: str) -> MarketProviderSettings | None`
- `save(settings: MarketProviderSettings) -> None`
- `list_all() -> list[MarketProviderSettings]`
- `delete(provider_name: str) -> None`

Precondition: [NEW] `market_provider_settings.py` in `core/domain/` defines the `MarketProviderSettings` dataclass.

Extend `UnitOfWork` protocol with:
- `market_provider_settings: MarketProviderSettingsRepository`

#### [NEW] [provider_connection_service.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/provider_connection_service.py)

`ProviderConnectionService` class implementing the PATCH-style `configure_provider` (all params optional, `is_enabled` flows through), typed `list_providers() → list[ProviderStatus]`, provider-specific `test_connection`, `remove_api_key`, and `test_all_providers`. Dependencies: `uow`, `fernet`, `http_client`, `rate_limiters`, `provider_registry`.

#### [MODIFY] [repositories.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/repositories.py)

Add `SqlMarketProviderSettingsRepository` that implements the `MarketProviderSettingsRepository` protocol. Maps between core-owned `MarketProviderSettings` and ORM `MarketProviderSettingModel` via `_setting_to_model`/`_model_to_setting` functions. The protocol and service never see the ORM model.

#### [MODIFY] [unit_of_work.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/unit_of_work.py)

Extend concrete `SqlUnitOfWork` with `market_provider_settings` attribute, wired to `SqlMarketProviderSettingsRepository`.

#### [NEW] [test_provider_connection_service.py](file:///p:/zorivest/tests/unit/test_provider_connection_service.py)

Tests (all with mocked HTTP client and in-memory UoW):
- `list_providers` returns `list[ProviderStatus]` with all 12 providers
- `configure_provider` encrypts and stores API key
- `configure_provider` handles dual-key (Alpaca) with `api_secret`
- `configure_provider` with already-encrypted key doesn't double-encrypt
- `configure_provider` with `is_enabled=False` disables the provider
- `configure_provider` with only `rate_limit` updates just that field (PATCH semantics)
- Provider-specific test_connection: Alpha Vantage (`"Global Quote"` key)
- Provider-specific test_connection: Polygon.io (`"results"` key)
- Provider-specific test_connection: Finnhub (`"c"` key, no `"error"`)
- Provider-specific test_connection: FMP (non-empty list + 403 legacy)
- Provider-specific test_connection: EODHD (`"code"` key)
- Provider-specific test_connection: Nasdaq (nested `datatable.data`)
- Provider-specific test_connection: SEC API (list with `"cik"`)
- Provider-specific test_connection: API Ninjas (`"price"` + `"name"`)
- Provider-specific test_connection: Benzinga (list or `"data"` dict)
- `test_connection` with 200 + unexpected JSON → "Connected but unexpected response"
- `test_connection` invalid key (401)
- `test_connection` rate limited (429)
- `test_connection` timeout
- `test_connection` DNS failure
- `test_connection` updates `last_tested_at` and `last_test_status`
- `remove_api_key` clears key and disables provider
- `test_all_providers` only tests providers with keys
- `test_all_providers` respects semaphore concurrency limit
- `MarketProviderSettingsRepository` CRUD operations

#### [NEW] [test_market_provider_settings_repo.py](file:///p:/zorivest/tests/unit/test_market_provider_settings_repo.py)

Isolated repository tests:
- `save` + `get` round-trip
- `list_all` returns all entries
- `delete` removes entry
- `get` for unknown name returns `None`

---

### BUILD_PLAN.md Hub Update

#### [MODIFY] [BUILD_PLAN.md](file:///p:/zorivest/docs/BUILD_PLAN.md)

After MEU execution:
1. Fix Phase 5 summary count: `1` → `12` (pre-existing error)
2. Update Phase 8 status to `🟡 In Progress`
3. Update MEU-59/62/60 status from ⬜ to ✅
4. Update summary table: Phase 8 completed count from `0` → `6` (3 existing + 3 new)
5. Correct total completed: `45` (approved P0 per meu-registry) + `6` (Phase 8) = `51`

---

## Task Table

| # | Task | Owner Role | Deliverable | Validation | Status |
|---|------|-----------|-------------|------------|--------|
| 1 | Write FIC-59 tests (Red) | coder | `test_provider_registry.py` | `uv run pytest tests/unit/test_provider_registry.py -v` → all FAIL | ⬜ |
| 2 | Implement provider registry (Green) | coder | `provider_registry.py`, `__init__.py` | `uv run pytest tests/unit/test_provider_registry.py -v` → all PASS | ⬜ |
| 3 | Write FIC-62 tests: rate limiter (Red) | coder | `test_rate_limiter.py` | `uv run pytest tests/unit/test_rate_limiter.py -v` → all FAIL | ⬜ |
| 4 | Write FIC-62 tests: log redaction (Red) | coder | `test_log_redaction.py` | `uv run pytest tests/unit/test_log_redaction.py -v` → all FAIL | ⬜ |
| 5 | Implement rate limiter (Green) | coder | `rate_limiter.py` | `uv run pytest tests/unit/test_rate_limiter.py -v` → all PASS | ⬜ |
| 6 | Implement log redaction (Green) | coder | `log_redaction.py` | `uv run pytest tests/unit/test_log_redaction.py -v` → all PASS | ⬜ |
| 7 | Add `MarketProviderSettingsRepository` to ports.py + extend UoW | coder | Updated `ports.py` | `uv run pyright packages/core/src/zorivest_core/application/ports.py` → 0 errors | ⬜ |
| 8 | Add `SqlMarketProviderSettingsRepository` to repositories.py | coder | Updated `repositories.py` | `uv run pyright packages/infrastructure/src/zorivest_infra/database/repositories.py` → 0 errors | ⬜ |
| 9 | Wire UoW concrete impl with new repo | coder | Updated `unit_of_work.py` | `uv run pyright packages/infrastructure/src/zorivest_infra/database/unit_of_work.py` → 0 errors | ⬜ |
| 10 | Write FIC-60 tests (Red) | coder | `test_provider_connection_service.py`, `test_market_provider_settings_repo.py` | `uv run pytest tests/unit/test_provider_connection_service.py tests/unit/test_market_provider_settings_repo.py -v` → all FAIL | ⬜ |
| 11 | Create `ProviderStatus` model | coder | `provider_status.py` | `uv run pyright packages/core/src/zorivest_core/application/provider_status.py` → 0 errors | ⬜ |
| 12 | Implement ProviderConnectionService (Green) | coder | `provider_connection_service.py` | `uv run pytest tests/unit/test_provider_connection_service.py tests/unit/test_market_provider_settings_repo.py -v` → all PASS | ⬜ |
| 13 | Refactor + quality pass | coder | Clean code | `uv run ruff check packages/ tests/` → 0 + `uv run pyright packages/` → 0 | ⬜ |
| 14 | Create handoff 047 (MEU-59) | coder | `047-2026-03-11-market-provider-registry-bp08s8.2.md` | `Test-Path .agent/context/handoffs/047-2026-03-11-market-provider-registry-bp08s8.2.md` | ⬜ |
| 15 | Create handoff 048 (MEU-62) | coder | `048-2026-03-11-market-rate-limiter-bp08s8.2.md` | `Test-Path .agent/context/handoffs/048-2026-03-11-market-rate-limiter-bp08s8.2.md` | ⬜ |
| 16 | Create handoff 049 (MEU-60) | coder | `049-2026-03-11-market-connection-svc-bp08s8.3+8.6.md` | `Test-Path .agent/context/handoffs/049-2026-03-11-market-connection-svc-bp08s8.3+8.6.md` | ⬜ |
| 17 | Update BUILD_PLAN.md | coder | Updated MEU statuses + summary counts | `rg -c "✅" docs/BUILD_PLAN.md` matches expected count + summary table verified | ⬜ |
| 18 | Update meu-registry.md | coder | MEU-59/62/60 rows updated | `rg "MEU-59\|MEU-62\|MEU-60" .agent/context/meu-registry.md` shows ✅ | ⬜ |
| 19 | Run MEU gate | coder | Gate pass | `uv run python tools/validate_codebase.py --scope meu` | ⬜ |
| 20 | Full regression | coder | All tests pass | `uv run pytest tests/ -v --tb=short` | ⬜ |
| 21 | Create reflection | coder | Reflection file | `Test-Path docs/execution/reflections/2026-03-11-market-data-infrastructure-reflection.md` | ⬜ |
| 22 | Update metrics | coder | New row in metrics | `rg "market-data-infrastructure" docs/execution/metrics.md` | ⬜ |
| 23 | Save pomera session state | coder | pomera note | Workflow action: MCP `pomera_notes` invocation (not a shell command) | ⬜ |
| 24 | Prepare commit messages | coder | Commit messages | Workflow action: `notify_user` MCP invocation (not a shell command) | ⬜ |

---

## Handoff Paths

```
.agent/context/handoffs/047-2026-03-11-market-provider-registry-bp08s8.2.md
.agent/context/handoffs/048-2026-03-11-market-rate-limiter-bp08s8.2.md
.agent/context/handoffs/049-2026-03-11-market-connection-svc-bp08s8.3+8.6.md
```

---

## Verification Plan

### Automated Tests

```bash
# Per-MEU validation (run after each Green phase)
uv run pytest tests/unit/test_provider_registry.py -v
uv run pytest tests/unit/test_rate_limiter.py -v
uv run pytest tests/unit/test_log_redaction.py -v
uv run pytest tests/unit/test_market_provider_settings_repo.py -v
uv run pytest tests/unit/test_provider_connection_service.py -v

# Quality gate
uv run ruff check packages/ tests/
uv run pyright packages/

# MEU gate
uv run python tools/validate_codebase.py --scope meu

# Full regression
uv run pytest tests/ -v --tb=short
```

### Manual Verification

None required — all components are inner-layer with no REST/GUI surface. Full coverage via unit tests with mocked HTTP.

---

## Stop Conditions

1. All FIC acceptance criteria have passing tests (6 + 7 + 30 = 43 total)
2. 0 ruff / pyright issues in touched files
3. Full regression passes (baseline: 696 passed)
4. All 3 handoffs created with evidence
5. BUILD_PLAN.md row statuses and summary counts agree (total = 51)
