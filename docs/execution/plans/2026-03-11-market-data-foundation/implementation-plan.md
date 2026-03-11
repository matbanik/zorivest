# Market Data Foundation — Implementation Plan

> **Project slug**: `market-data-foundation`
> **Date**: 2026-03-11
> **Phase**: 8 — Market Data Aggregation
> **Build Plan**: [08-market-data.md](file:///p:/zorivest/docs/build-plan/08-market-data.md) §8.1a–§8.1d, §8.2a–§8.2b

---

## Goal

Establish the **data foundation** for Phase 8 (Market Data) by implementing all domain-layer and infrastructure-layer type definitions: the `AuthMethod` enum, `ProviderConfig` value object, normalized response DTOs (Pydantic), `MarketDataPort` protocol, `MarketProviderSettingModel` DB column addition, and the API key encryption module. These types underpin every subsequent Phase 8 MEU (registry, services, API, MCP tools, GUI).

---

## MEUs Included (Execution Order)

| MEU | Slug | Matrix | Build Plan Ref | Description |
|-----|------|:------:|----------------|-------------|
| MEU-56 | `market-provider-entity` | 21 | [08 §8.1a–§8.1d](file:///p:/zorivest/docs/build-plan/08-market-data.md) | AuthMethod enum + ProviderConfig value object + MarketDataPort Protocol |
| MEU-57 | `market-response-dtos` | 22 | [08 §8.1c](file:///p:/zorivest/docs/build-plan/08-market-data.md) | MarketQuote, MarketNewsItem, TickerSearchResult, SecFiling Pydantic DTOs |
| MEU-58 | `market-provider-settings` | 23 | [08 §8.2a–§8.2b](file:///p:/zorivest/docs/build-plan/08-market-data.md) | MarketProviderSettingModel update + API key encryption module |

---

## Scope Boundary

**In-scope:**
- `AuthMethod` enum (4 members) appended to `enums.py`
- `ProviderConfig` frozen dataclass in new `domain/market_data.py`
- `MarketDataPort` Protocol appended to `ports.py`
- 4 Pydantic response DTOs in new `application/market_dtos.py`
- `encrypted_api_secret` column added to `MarketProviderSettingModel`
- New `api_key_encryption.py` module in `packages/infrastructure/src/zorivest_infra/security/`
- Unit tests for all deliverables

**Out-of-scope** (next project):
- Provider registry with 12 hardcoded configs (MEU-59)
- Connection service (MEU-60), rate limiter (MEU-62), data service (MEU-61)
- Market data REST API (MEU-63), MCP tools (MEU-64), GUI (MEU-65)

---

## User Review Required

> [!IMPORTANT]
> **MarketProviderSettingModel already exists** in `models.py` (lines 197-210) — scaffolded during Phase 2. It is missing the `encrypted_api_secret` column specified in `08-market-data.md §8.2a`. MEU-58 will add this column and verify the existing model is spec-compliant.

> [!IMPORTANT]
> **Existing DTOs use frozen dataclasses**, but the build plan specifies market-data DTOs as **Pydantic BaseModel**s. To avoid mixing paradigms in the same file, market-data DTOs will live in a new file `application/market_dtos.py` rather than appending to `dtos.py`.

---

## Proposed Changes

### Domain Layer — MEU-56

Summary: Add market-data domain types to the core package.

#### [MODIFY] [enums.py](file:///p:/zorivest/packages/core/src/zorivest_core/domain/enums.py)

Append `AuthMethod` StrEnum after existing enums (4 members: `QUERY_PARAM`, `BEARER_HEADER`, `CUSTOM_HEADER`, `RAW_HEADER`).

#### [NEW] [market_data.py](file:///p:/zorivest/packages/core/src/zorivest_core/domain/market_data.py)

`ProviderConfig` frozen dataclass with fields per §8.1b: `name`, `base_url`, `auth_method`, `auth_param_name`, `headers_template`, `test_endpoint`, `default_rate_limit`, `default_timeout`, `signup_url`, `response_validator_key`.

#### [MODIFY] [ports.py](file:///p:/zorivest/packages/core/src/zorivest_core/application/ports.py)

Append `MarketDataPort` Protocol with 4 async methods per §8.1d: `get_quote`, `get_news`, `search_ticker`, `get_sec_filings`.

---

### Application Layer — MEU-57

Summary: Add normalized Pydantic response DTOs for market data and declare `pydantic` dependency.

#### [NEW] [market_dtos.py](file:///p:/zorivest/packages/core/src/zorivest_core/application/market_dtos.py)

4 Pydantic `BaseModel` classes per §8.1c:
- `MarketQuote` — price, change, volume, etc.
- `MarketNewsItem` — title, source, url, tickers
- `TickerSearchResult` — symbol, name, exchange
- `SecFiling` — ticker, company_name, cik, filing_type

#### [MODIFY] [pyproject.toml](file:///p:/zorivest/packages/core/pyproject.toml)

Add `dependencies = ["pydantic>=2.0"]` to `[project]` section (currently has zero declared dependencies).

---

### Infrastructure Layer — MEU-58

Summary: Update the existing DB model, add API key encryption, and declare `cryptography` dependency.

#### [MODIFY] [models.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/models.py)

Add `encrypted_api_secret` column to `MarketProviderSettingModel` (Text, nullable=True) for dual-key providers (Alpaca).

#### [MODIFY] [pyproject.toml](file:///p:/zorivest/packages/infrastructure/pyproject.toml)

Add `cryptography>=44.0.0` to `dependencies` array.

#### [NEW] [security/__init__.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/security/__init__.py)

Empty `__init__.py` for new security subpackage.

#### [NEW] [api_key_encryption.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/security/api_key_encryption.py)

Fernet-based encrypt/decrypt module per §8.2b:
- `ENC_PREFIX = "ENC:"`
- `encrypt_api_key(api_key: str, fernet: Fernet) -> str`
- `decrypt_api_key(encrypted_key: str, fernet: Fernet) -> str`
- `derive_fernet_key(password: str, salt: bytes) -> Fernet` (PBKDF2 derivation helper — [Research-backed], not in spec)

---

### Test Files

#### [NEW] [test_market_data_entities.py](file:///p:/zorivest/tests/unit/test_market_data_entities.py)

MEU-56 tests:
- `AuthMethod` enum membership (4 members), string values
- `ProviderConfig` creation with all fields, immutability (frozen), default values
- `ProviderConfig` missing required field raises `TypeError`
- `MarketDataPort` Protocol structural check (duck-typing test)

#### [NEW] [test_market_dtos.py](file:///p:/zorivest/tests/unit/test_market_dtos.py)

MEU-57 tests:
- `MarketQuote` creation with all fields, optional field handling, JSON round-trip
- `MarketNewsItem` creation, empty tickers list default
- `TickerSearchResult` creation, optional exchange/currency
- `SecFiling` creation, default provider field
- Validation: invalid types rejected by Pydantic

#### [NEW] [test_api_key_encryption.py](file:///p:/zorivest/tests/unit/test_api_key_encryption.py)

MEU-58 tests:
- Encrypt/decrypt round-trip with real Fernet key
- `ENC:` prefix added on encrypt, stripped on decrypt
- Already-encrypted key is not double-encrypted (idempotent)
- Empty string and None pass-through
- Non-encrypted key passes through `decrypt_api_key` unchanged
- `derive_fernet_key` produces valid Fernet from password + salt
- Decryption with wrong key raises `InvalidToken`

#### Existing Test Updates

- [test_enums.py](file:///p:/zorivest/tests/unit/test_enums.py) — Update exact-count assertion from **14→15** enum classes; add `"AuthMethod"` to expected set (line 47); update `len` assertion (line 51)
- [test_ports.py](file:///p:/zorivest/tests/unit/test_ports.py) — Update exact-count assertion from **11→12** protocol classes; add `"MarketDataPort"` to expected set (line 275); test class name assertion (line 267)
- [test_models.py](file:///p:/zorivest/tests/unit/test_models.py) — Add test for `encrypted_api_secret` column on `MarketProviderSettingModel`

---

### BUILD_PLAN.md Hub Update

> [!WARNING]
> Phase 5 closeout (MEU-42 ✅, Phase 5 → Completed) is **deferred** until the MEU-42 review thread reaches `approved`. This plan only updates Phase 8 status.

#### [MODIFY] [BUILD_PLAN.md](file:///p:/zorivest/docs/BUILD_PLAN.md)

| Change | What |
|--------|------|
| Phase 8 status | `⚪ Not Started` → `🟡 In Progress` |
| MEU-56/57/58 rows | Add to Phase 8 table with ✅ status after implementation |

---

## Spec Sufficiency Gate

### MEU-56 — `market-provider-entity`

| Behavior / Contract | Source Type | Source | Resolved? | Notes |
|---------------------|------------|--------|:---------:|-------|
| AuthMethod enum with 4 members | Spec | 08 §8.1a | ✅ | Members: QUERY_PARAM, BEARER_HEADER, CUSTOM_HEADER, RAW_HEADER |
| ProviderConfig frozen dataclass | Spec | 08 §8.1b | ✅ | 10 fields per spec |
| MarketDataPort Protocol | Spec | 08 §8.1d | ✅ | 4 async methods |
| Port import location | Local Canon | ports.py | ✅ | Append to existing ports file |

### MEU-57 — `market-response-dtos`

| Behavior / Contract | Source Type | Source | Resolved? | Notes |
|---------------------|------------|--------|:---------:|-------|
| MarketQuote Pydantic model | Spec | 08 §8.1c | ✅ | 11 fields per spec |
| MarketNewsItem Pydantic model | Spec | 08 §8.1c | ✅ | 7 fields per spec |
| TickerSearchResult Pydantic model | Spec | 08 §8.1c | ✅ | 5 fields per spec |
| SecFiling Pydantic model | Spec | 08 §8.1c | ✅ | 7 fields per spec |
| Separate file from existing dtos.py | Local Canon | dtos.py conventions | ✅ | Avoid mixing dataclass DTOs and Pydantic models |

### MEU-58 — `market-provider-settings`

| Behavior / Contract | Source Type | Source | Resolved? | Notes |
|---------------------|------------|--------|:---------:|-------|
| encrypted_api_secret column | Spec | 08 §8.2a | ✅ | Text, nullable=True for Alpaca dual-key |
| ENC: prefix convention | Spec | 08 §8.2b | ✅ | Encrypt returns "ENC:" + base64 |
| Fernet + PBKDF2 key derivation | Spec | 08 §8.2b | ✅ | Same pattern as SMTP credentials |
| Idempotent encrypt (no double-encrypt) | Spec | 08 §8.2b | ✅ | Check ENC: prefix before encrypting |
| Pass-through for non-encrypted values | Spec | 08 §8.2b | ✅ | decrypt_api_key returns as-is if no ENC: |
| Existing model columns correct | Local Canon | models.py:197-210 | ✅ | Matches spec except missing api_secret |

---

## Feature Intent Contract (FIC)

### MEU-56 FIC

- **AC-1** [Local Canon]: `AuthMethod` StrEnum defines exactly 4 members with lowercase string values (spec uses `(str, Enum)` but all 14 existing project enums use `StrEnum` per local convention)
- **AC-2** [Spec]: `ProviderConfig` is a frozen dataclass with 10 fields matching §8.1b
- **AC-3** [Spec]: `ProviderConfig.headers_template` accepts `dict[str, str]`
- **AC-4** [Spec]: `ProviderConfig.default_timeout` defaults to 30
- **AC-5** [Spec]: `ProviderConfig.signup_url` defaults to empty string
- **AC-6** [Spec]: `ProviderConfig.response_validator_key` defaults to empty string
- **AC-7** [Spec]: `MarketDataPort` Protocol defines 4 async method signatures matching §8.1d

### MEU-57 FIC

- **AC-1** [Spec]: `MarketQuote` has required `ticker`, `price`, `provider` + 8 optional fields
- **AC-2** [Spec]: `MarketNewsItem` has required `title`, `source`, `provider` + 4 optional fields
- **AC-3** [Spec]: `MarketNewsItem.tickers` defaults to empty list via `Field(default_factory=list)`
- **AC-4** [Spec]: `TickerSearchResult` has required `symbol`, `name`, `provider` + 2 optional fields
- **AC-5** [Spec]: `SecFiling` has required `ticker`, `company_name`, `cik` + 3 optional fields
- **AC-6** [Spec]: `SecFiling.provider` defaults to `"SEC API"`
- **AC-7** [Spec]: All DTOs serialize to/from JSON via Pydantic `model_dump`/`model_validate`

### MEU-58 FIC

- **AC-1** [Spec]: `MarketProviderSettingModel` gains `encrypted_api_secret` Text column (nullable=True)
- **AC-2** [Spec]: `encrypt_api_key` returns `"ENC:" + base64(fernet.encrypt(key))`
- **AC-3** [Spec]: `decrypt_api_key` strips `"ENC:"` prefix and decrypts
- **AC-4** [Spec]: Already-encrypted keys (ENC: prefix) are not double-encrypted
- **AC-5** [Spec]: Empty/None input passes through both encrypt and decrypt unchanged
- **AC-6** [Research-backed]: `derive_fernet_key` uses PBKDF2HMAC with SHA256, 480,000 iterations (OWASP PBKDF2 recommendation; not specified in 08-market-data.md §8.2b)
- **AC-7** [Spec]: Decryption with wrong Fernet key raises `InvalidToken`

---

## Task Table

| # | Task | Owner Role | Deliverable | Validation | Status |
|---|------|-----------|-------------|------------|:------:|
| 1 | Write `test_market_data_entities.py` (Red) | coder | Test file | `uv run pytest tests/unit/test_market_data_entities.py -v` → all FAILED | ⬜ |
| 2 | Implement `AuthMethod` enum + `ProviderConfig` + `MarketDataPort` | coder | 3 source files | `uv run pytest tests/unit/test_market_data_entities.py -v` → all PASSED | ⬜ |
| 3 | Update `test_enums.py` (14→15) + `test_ports.py` (11→12) integrity counts | coder | 2 test updates | `uv run pytest tests/unit/test_enums.py tests/unit/test_ports.py -v` → PASSED | ⬜ |
| 4 | Write `test_market_dtos.py` (Red) | coder | Test file | `uv run pytest tests/unit/test_market_dtos.py -v` → all FAILED | ⬜ |
| 5 | Implement market data Pydantic DTOs + add `pydantic>=2.0` to `core/pyproject.toml` | coder | `market_dtos.py` + `pyproject.toml` | `uv run pytest tests/unit/test_market_dtos.py -v` → all PASSED | ⬜ |
| 6 | Write `test_api_key_encryption.py` (Red) | coder | Test file | `uv run pytest tests/unit/test_api_key_encryption.py -v` → all FAILED | ⬜ |
| 7 | Implement `api_key_encryption.py` + update `models.py` + add `cryptography>=44.0` to `infra/pyproject.toml` | coder | 3 source files | `uv run pytest tests/unit/test_api_key_encryption.py -v` → all PASSED | ⬜ |
| 8 | Update `test_models.py` with `encrypted_api_secret` test | coder | Test update | `uv run pytest tests/unit/test_models.py -v` → PASSED | ⬜ |
| 9 | Refactor pass (all 3 MEUs) | coder | Clean code | `uv run pytest tests/ -v` → all PASSED | ⬜ |
| 10 | MEU gate | coder | Gate pass | `uv run python tools/validate_codebase.py --scope meu` → exit 0 | ⬜ |
| 11 | Create handoff 044 for MEU-56 | coder | Handoff file | `Test-Path .agent/context/handoffs/044-*.md` → True | ⬜ |
| 12 | Create handoff 045 for MEU-57 | coder | Handoff file | `Test-Path .agent/context/handoffs/045-*.md` → True | ⬜ |
| 13 | Create handoff 046 for MEU-58 | coder | Handoff file | `Test-Path .agent/context/handoffs/046-*.md` → True | ⬜ |
| 14 | Update `meu-registry.md` (3 new MEU rows) | coder | Registry file | `rg 'MEU-56|MEU-57|MEU-58' .agent/context/meu-registry.md` → 3 matches | ⬜ |
| 15 | Update `BUILD_PLAN.md` (Phase 8 🟡, MEU-56/57/58 statuses) | coder | Hub file | `rg -n 'Market Data.*In Progress' docs/BUILD_PLAN.md` → 1 match; `rg 'MEU-56.*✅' docs/BUILD_PLAN.md` + `rg 'MEU-57.*✅' docs/BUILD_PLAN.md` + `rg 'MEU-58.*✅' docs/BUILD_PLAN.md` → each 1 match | ⬜ |
| 16 | Create reflection file | coder | Reflection doc | `Test-Path docs/execution/reflections/2026-03-11-*.md` → True | ⬜ |
| 17 | Update `docs/execution/metrics.md` | coder | Metrics row | `rg 'market-data-foundation' docs/execution/metrics.md` → 1 match | ⬜ |
| 18 | Save session state to pomera_notes + export | coder | Note + file | `Test-Path docs/execution/plans/2026-03-11-market-data-foundation/session-state.md` → True (local export proves pomera_notes save happened) | ⬜ |
| 19 | Prepare commit messages | coder | Commit text file | `Test-Path docs/execution/plans/2026-03-11-market-data-foundation/commit-messages.md` → True | ⬜ |

---

## Verification Plan

### Automated Tests

```bash
# Per-MEU Red→Green cycle
uv run pytest tests/unit/test_market_data_entities.py -v     # MEU-56
uv run pytest tests/unit/test_enums.py -v                     # MEU-56 enum integrity
uv run pytest tests/unit/test_ports.py -v                     # MEU-56 ports integrity
uv run pytest tests/unit/test_market_dtos.py -v               # MEU-57
uv run pytest tests/unit/test_api_key_encryption.py -v        # MEU-58
uv run pytest tests/unit/test_models.py -v                    # MEU-58 model integration

# Full regression
uv run pytest tests/ -v

# Type checking
uv run pyright packages/core/src/zorivest_core/domain/market_data.py
uv run pyright packages/core/src/zorivest_core/application/market_dtos.py
uv run pyright packages/infrastructure/src/zorivest_infra/security/api_key_encryption.py

# Lint
uv run ruff check packages/ tests/

# MEU gate
uv run python tools/validate_codebase.py --scope meu
```

### Manual Verification

None required — all deliverables are code-testable.
