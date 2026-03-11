# Market Data Infrastructure — Implementation Plan

> **Project slug:** `market-data-infrastructure`
> **Date:** 2026-03-11
> **MEUs:** 59, 62, 60 (in execution order)
> **Build plan:** [08-market-data.md](file:///p:/zorivest/docs/build-plan/08-market-data.md) §8.2c, §8.2e, §8.2d, §8.3a
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
| MEU-60 | `market-connection-svc` | §8.3a + §8.6 | `ProviderConnectionService` (test, configure, list, remove) |

### Out-of-Scope

- MEU-61 `market-data-service` (MarketDataService — depends on MEU-60)
- MEU-63 `market-data-api` (REST routes — depends on MEU-61)
- MEU-64 `market-data-mcp` (MCP tools — depends on MEU-63)
- MEU-65 `market-data-gui` (GUI settings — depends on MEU-63)
- Response normalizers (part of MEU-61)

### Execution Order

```
MEU-59 (registry) → MEU-62 (rate limiter + log redaction) → MEU-60 (connection service)
```

---

## Spec Sufficiency

### MEU-59: Provider Registry

| Behavior / Contract | Source Type | Source | Resolved? | Notes |
|---------------------|------------|--------|-----------|-------|
| 12 providers with ProviderConfig entries | Spec | [08 §8.2c](file:///p:/zorivest/docs/build-plan/08-market-data.md#L208-350) | ✅ | All 12 provider configs fully specified (name, base_url, auth_method, auth_param_name, headers_template, test_endpoint, default_rate_limit, signup_url, response_validator_key) |
| ProviderConfig frozen dataclass | Spec | [08 §8.1b](file:///p:/zorivest/docs/build-plan/08-market-data.md#L65-86) | ✅ | Already implemented in MEU-56 |
| AuthMethod enum | Spec | [08 §8.1a](file:///p:/zorivest/docs/build-plan/08-market-data.md#L52-63) | ✅ | Already implemented in MEU-56 |
| Lookup by provider name | Local Canon | `ProviderConnectionService` uses `PROVIDER_REGISTRY[name]` in §8.3a | ✅ | Dict keyed by provider name is the contract |
| `get_provider_config(name)` helper | Spec | §8.2c (implicit — registry used by connection/data service) | ✅ | Need a typed helper that raises `KeyError` with clear message on unknown provider |
| `list_provider_names()` helper | Spec | §8.3a `list_providers()` iterates all | ✅ | Convenience function for service layer |

### MEU-62: Rate Limiter + Log Redaction

| Behavior / Contract | Source Type | Source | Resolved? | Notes |
|---------------------|------------|--------|-----------|-------|
| Token-bucket rate limiter | Spec | [08 §8.2e](file:///p:/zorivest/docs/build-plan/08-market-data.md#L375-401) | ✅ | `RateLimiter(max_per_minute)` with sliding window `deque` |
| `async wait_if_needed()` blocks until slot | Spec | §8.2e | ✅ | Pops expired timestamps, sleeps if full |
| `mask_api_key(key) → "[REDACTED]"` | Spec | [08 §8.2d](file:///p:/zorivest/docs/build-plan/08-market-data.md#L353-373) | ✅ | Full replacement per security policy — no partial masking |
| `sanitize_url_for_logging(text, api_key)` | Spec | §8.2d | ✅ | Replace key with `[REDACTED]` in any string |
| Log redaction delegates to central policy | Spec | §8.2d comment: "delegates to central redaction policy in 01a-logging.md" | ✅ | Redaction functions are utilities; integration with logging filters is in MEU-1A (already done) |
| Rate limiter per-provider | Spec | §8.3b `rate_limiters: dict[str, RateLimiter]` | ✅ | Each provider gets own RateLimiter instance |

### MEU-60: ProviderConnectionService

| Behavior / Contract | Source Type | Source | Resolved? | Notes |
|---------------------|------------|--------|-----------|-------|
| `list_providers() → list[dict]` | Spec | [08 §8.3a](file:///p:/zorivest/docs/build-plan/08-market-data.md#L407-438) | ✅ | List all providers with status |
| `configure_provider(name, api_key, rate_limit?, timeout?)` | Spec | §8.3a | ✅ | Encrypt and store API key |
| `test_connection(provider_name) → (bool, str)` | Spec | §8.3a + [§8.6](file:///p:/zorivest/docs/build-plan/08-market-data.md#L669-716) | ✅ | Full validation rules table per provider |
| `remove_api_key(provider_name)` | Spec | §8.3a | ✅ | Remove key, disable provider |
| HTTP status interpretation (200, 401, 403, 429, timeout, connection error) | Spec | §8.6 HTTP Status Interpretation table | ✅ | 6 status scenarios with user messages |
| Response validation per provider | Spec | §8.6 response validation rules table | ✅ | 9 providers with expected keys |
| Concurrency guard (Semaphore) for test_all | Spec | §8.6 `asyncio.Semaphore(2)` | ✅ | Limit concurrent tests |
| `test_all_providers() → list[(name, success, msg)]` | Spec | §8.6 | ✅ | Guarded concurrent test of enabled providers |
| Dual-key support (Alpaca) | Spec | §8.2c Alpaca config + §8.3a `api_secret` | ✅ | `configure_provider` must accept optional `api_secret` |
| Fernet encryption on store | Local Canon | [api_key_encryption.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/security/api_key_encryption.py) (MEU-58) | ✅ | Already implemented |
| MarketProviderSettingModel persistence | Local Canon | [models.py L197-211](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/models.py#L197-L211) (MEU-58) | ✅ | Already implemented |

---

## Feature Intent Contracts (FICs)

### FIC-59: Provider Registry

**Purpose:** Static registry of all 12 market data provider configurations.

| AC | Description | Source |
|----|-------------|--------|
| AC-1 | `PROVIDER_REGISTRY` is a `dict[str, ProviderConfig]` with exactly 12 entries | Spec §8.2c |
| AC-2 | Each entry has all required fields populated (name, base_url, auth_method, auth_param_name, headers_template, test_endpoint, default_rate_limit) | Spec §8.2c |
| AC-3 | Provider names match spec exactly: "Alpha Vantage", "Polygon.io", "Finnhub", "Financial Modeling Prep", "EODHD", "Nasdaq Data Link", "SEC API", "API Ninjas", "Benzinga", "OpenFIGI", "Alpaca", "Tradier" | Spec §8.2c |
| AC-4 | `get_provider_config(name)` returns `ProviderConfig` for known providers, raises `KeyError` for unknown | Local Canon (implicit from service usage) |
| AC-5 | `list_provider_names()` returns sorted list of all 12 provider names | Local Canon (implicit from `list_providers()` in §8.3a) |
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

**Purpose:** Service for managing provider credentials and testing connectivity.

| AC | Description | Source |
|----|-------------|--------|
| AC-1 | `list_providers()` returns all 12 providers with status (enabled, has_api_key, last_test_status, rate_limit, timeout) | Spec §8.3a |
| AC-2 | `configure_provider(name, api_key, api_secret?, rate_limit?, timeout?)` encrypts key via Fernet and persists to `MarketProviderSettingModel` | Spec §8.3a |
| AC-3 | `configure_provider` with already-encrypted key (ENC: prefix) passes through without double-encryption | Local Canon (api_key_encryption.py) |
| AC-4 | `test_connection(name)` returns `(True, "Connection successful")` for HTTP 200 with valid JSON matching provider's `response_validator_key` | Spec §8.6 |
| AC-5 | `test_connection` returns `(False, "Invalid API key")` for HTTP 401 | Spec §8.6 |
| AC-6 | `test_connection` returns `(False, "Rate limit exceeded")` for HTTP 429 | Spec §8.6 |
| AC-7 | `test_connection` returns `(False, "Connection timeout")` for timeout errors | Spec §8.6 |
| AC-8 | `test_connection` returns `(False, "Connection failed")` for DNS/network errors | Spec §8.6 |
| AC-9 | FMP-specific: HTTP 403 with "Legacy Endpoint" treated as success | Spec §8.6 |
| AC-10 | `remove_api_key(name)` clears encrypted_api_key/secret and sets is_enabled=False | Spec §8.3a |
| AC-11 | `test_all_providers()` uses `asyncio.Semaphore(2)` to limit concurrent tests | Spec §8.6 |
| AC-12 | `test_all_providers()` only tests providers that have API keys configured | Spec §8.6 |
| AC-13 | Connection test updates `last_tested_at` and `last_test_status` in the DB | Spec §8.3a (implied by MarketProviderSettingModel fields) |
| AC-14 | All HTTP calls use the rate limiter's `wait_if_needed()` before making requests | Spec §8.2e + §8.3b |
| AC-15 | Dual-key provider (Alpaca) correctly stores both `api_key` and `api_secret` | Spec §8.2c + §8.3a |

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

#### [NEW] [log_redaction.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/market_data/log_redaction.py)

`mask_api_key()` and `sanitize_url_for_logging()` from spec §8.2d.

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

### MEU-60: ProviderConnectionService

#### [NEW] [provider_connection_service.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/provider_connection_service.py)

`ProviderConnectionService` class implementing the 4 operations from §8.3a + `test_all_providers` from §8.6. Dependencies injected: `uow`, `fernet`, `http_client`, `rate_limiters`, `provider_registry`.

#### [NEW] [test_provider_connection_service.py](file:///p:/zorivest/tests/unit/test_provider_connection_service.py)

Tests (all with mocked HTTP client and in-memory UoW):
- `list_providers` returns all 12 providers with correct shape
- `configure_provider` encrypts and stores API key
- `configure_provider` handles dual-key (Alpaca) with `api_secret`
- `configure_provider` with already-encrypted key doesn't double-encrypt
- `test_connection` success (200 + valid JSON)
- `test_connection` invalid key (401)
- `test_connection` rate limited (429)
- `test_connection` timeout
- `test_connection` DNS failure
- `test_connection` FMP 403 "Legacy Endpoint" treated as success
- `test_connection` updates `last_tested_at` and `last_test_status`
- `remove_api_key` clears key and disables provider
- `test_all_providers` only tests providers with keys
- `test_all_providers` respects semaphore concurrency limit

---

### BUILD_PLAN.md Hub Update

#### [MODIFY] [BUILD_PLAN.md](file:///p:/zorivest/docs/BUILD_PLAN.md)

After MEU execution:
1. Update Phase 8 status to `🟡 In Progress` with updated date
2. Update MEU-59/62/60 status from ⬜ to ✅
3. Update summary table: Phase 8 completed count from 0 → 3 (plus existing 3 = 6 total)
4. Total completed: 22 → 48 (42 P0 + 3 existing Phase 8 + 3 new)

> **Note:** The BUILD_PLAN.md summary counts currently show inconsistencies flagged in the reflection. The Phase 5 completed count shows `1` when it should show `12`. This pre-existing issue will be fixed as part of this project's BUILD_PLAN.md update task.

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
| 7 | Write FIC-60 tests (Red) | coder | `test_provider_connection_service.py` | `uv run pytest tests/unit/test_provider_connection_service.py -v` → all FAIL | ⬜ |
| 8 | Implement ProviderConnectionService (Green) | coder | `provider_connection_service.py` | `uv run pytest tests/unit/test_provider_connection_service.py -v` → all PASS | ⬜ |
| 9 | Refactor + quality pass | coder | Clean code | `uv run ruff check packages/ tests/` + `uv run pyright packages/` | ⬜ |
| 10 | Create handoff 047 (MEU-59) | coder | `047-2026-03-11-market-provider-registry-bp08s8.2.md` | Follows TEMPLATE.md | ⬜ |
| 11 | Create handoff 048 (MEU-62) | coder | `048-2026-03-11-market-rate-limiter-bp08s8.2.md` | Follows TEMPLATE.md | ⬜ |
| 12 | Create handoff 049 (MEU-60) | coder | `049-2026-03-11-market-connection-svc-bp08s8.3+8.6.md` | Follows TEMPLATE.md | ⬜ |
| 13 | Update BUILD_PLAN.md | coder | Updated MEU statuses + summary counts | Verify row statuses match summary table counts | ⬜ |
| 14 | Update meu-registry.md | coder | New MEU rows for 59, 62, 60 | Rows present with ✅ status | ⬜ |
| 15 | Run MEU gate | coder | Gate pass | `uv run python tools/validate_codebase.py --scope meu` | ⬜ |
| 16 | Full regression | coder | All tests pass | `uv run pytest tests/ -v` | ⬜ |
| 17 | Create reflection | coder | `docs/execution/reflections/2026-03-11-market-data-infrastructure-reflection.md` | File exists with lessons learned | ⬜ |
| 18 | Update metrics | coder | New row in `docs/execution/metrics.md` | Row present | ⬜ |
| 19 | Save pomera session state | coder | pomera note | Note saved | ⬜ |
| 20 | Prepare commit messages | coder | Commit messages | Presented to human | ⬜ |

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

1. All 28 FIC acceptance criteria have passing tests
2. 0 ruff / pyright issues in touched files
3. Full regression passes (baseline: 696 passed)
4. All 3 handoffs created with evidence
5. BUILD_PLAN.md row statuses and summary counts agree
