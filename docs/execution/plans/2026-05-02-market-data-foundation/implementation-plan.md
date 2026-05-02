---
project: "2026-05-02-market-data-foundation"
date: "2026-05-02"
source: "docs/build-plan/08a-market-data-expansion.md"
meus: ["MEU-182a", "MEU-182", "MEU-183", "MEU-184"]
status: "draft"
template_version: "2.0"
---

# Implementation Plan: Market Data Foundation

> **Project**: `2026-05-02-market-data-foundation`
> **Build Plan Section(s)**: [08a §Layer 0–2](../../../build-plan/08a-market-data-expansion.md)
> **Status**: `draft`

---

## Goal

Establish the foundational data layer for Phase 8a Market Data Expansion. This project:

1. **Purges stale Benzinga provider code** (MEU-182a) — aligns codebase to the 11-provider documentation
2. **Creates 7 new DTOs** (MEU-182) — frozen dataclasses for OHLCV, Fundamentals, Earnings, Dividends, Splits, Insider, EconomicCalendar + MarketDataPort extension
3. **Adds 4 new DB tables** (MEU-183) — `market_earnings`, `market_dividends`, `market_splits`, `market_insider`
4. **Builds the ProviderCapabilities registry** (MEU-184) — capability metadata for all 11 providers

These 4 MEUs form Layer 0–2 of the Phase 8a dependency chain and are prerequisites for all URL builders, extractors, and service methods.

---

## User Review Required

> [!IMPORTANT]
> **DTO style decision**: The spec defines new DTOs as `@dataclass(frozen=True)` while existing Phase 8 DTOs (`MarketQuote`, `MarketNewsItem`, etc.) use Pydantic `BaseModel`. This plan follows the spec — new DTOs will be frozen dataclasses in a separate file (`market_expansion_dtos.py`), coexisting with the existing Pydantic models. The frozen dataclass approach is appropriate because these DTOs are internal data carriers, not API response models. `[Spec + Local Canon]`
>
> **No Alembic**: The codebase uses `Base.metadata.create_all()` instead of Alembic migrations (confirmed in `models.py` line 761: "no Alembic infrastructure"). MEU-183 will follow this pattern — adding models directly to `models.py`. `[Local Canon]`

---

## Proposed Changes

### MEU-182a: Benzinga Code Purge

#### Boundary Inventory

N/A — code deletion only, no external input surfaces.

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-1 | `ProviderConfig("Benzinga", ...)` entry removed from `provider_registry.py` | Spec | N/A |
| AC-2 | `normalize_benzinga_news()` function + dispatch table entry removed from `normalizers.py` | Spec | N/A |
| AC-3 | `elif name == "Benzinga"` branch + fallback message removed from `market_data_service.py` | Spec | N/A |
| AC-4 | `@_register_validator("Benzinga")` + `_validate_benzinga()` removed from `provider_connection_service.py` | Spec | N/A |
| AC-5 | Benzinga comment removed from `redaction.py` | Spec | N/A |
| AC-6 | All Benzinga test fixtures, imports, and test classes removed from 3 test files | Spec | N/A |
| AC-7 | `rg -i benzinga packages/ tests/ --glob "!*.pyc"` returns 0 matches | Spec | N/A |
| AC-8 | All existing tests pass without modification | Local Canon | N/A |
| AC-9 | `pyright` + `ruff check` clean | Local Canon | N/A |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| Which files to modify | Spec | 5 production + 3 test files explicitly listed |
| What to remove per file | Spec | Line ranges provided in spec |
| Verification command | Spec | `rg -i benzinga` = 0 matches |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/infrastructure/src/zorivest_infra/market_data/provider_registry.py` | modify | Remove Benzinga ProviderConfig entry |
| `packages/infrastructure/src/zorivest_infra/market_data/normalizers.py` | modify | Remove `normalize_benzinga_news()` + dispatch entry |
| `packages/core/src/zorivest_core/services/market_data_service.py` | modify | Remove Benzinga branch + fallback message |
| `packages/core/src/zorivest_core/services/provider_connection_service.py` | modify | Remove `_validate_benzinga()` |
| `packages/infrastructure/src/zorivest_infra/logging/redaction.py` | modify | Remove Benzinga comment |
| `tests/unit/test_provider_registry.py` | modify | Remove Benzinga from provider lists |
| `tests/unit/test_normalizers.py` | modify | Remove Benzinga import, fixture, test class |
| `tests/unit/test_provider_connection_service.py` | modify | Remove Benzinga fixture entry + test class |

---

### MEU-182: Market Expansion DTOs

#### Boundary Inventory

N/A — frozen dataclass definitions with no external input surfaces.

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-1 | `OHLCVBar` frozen dataclass with 11 fields: ticker, timestamp, open, high, low, close, adj_close, volume, vwap, trade_count, provider | Spec | `FrozenInstanceError` on attribute assignment |
| AC-2 | `FundamentalsSnapshot` frozen dataclass with 13 fields | Spec | `FrozenInstanceError` on attribute assignment |
| AC-3 | `EarningsReport` frozen dataclass with 10 fields | Spec | `FrozenInstanceError` on attribute assignment |
| AC-4 | `DividendRecord` frozen dataclass with 9 fields | Spec | `FrozenInstanceError` on attribute assignment |
| AC-5 | `StockSplit` frozen dataclass with 5 fields | Spec | `FrozenInstanceError` on attribute assignment |
| AC-6 | `InsiderTransaction` frozen dataclass with 10 fields | Spec | `FrozenInstanceError` on attribute assignment |
| AC-7 | `EconomicCalendarEvent` frozen dataclass with 9 fields | Spec | `FrozenInstanceError` on attribute assignment |
| AC-8 | All 7 DTOs constructed with valid data without error | Spec | Missing required field → `TypeError` |
| AC-9 | `MarketDataPort` extended with 8 new async method signatures | Spec | N/A (Protocol — no runtime enforcement) |
| AC-10 | All new DTOs importable from `market_expansion_dtos` module | Local Canon | N/A |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| DTO field names and types | Spec | All 7 dataclasses fully defined in §8a.1 |
| Frozen enforcement | Spec | `@dataclass(frozen=True)` explicit |
| File location | Spec + Local Canon — agreed | Spec (§8a.1 line 90) and local architecture both place new DTOs in `application/market_expansion_dtos.py`. Original spec path `entities/market_data.py` was corrected during plan review to match codebase convention. `[Human-approved]` |
| Port method signatures | Spec | 8 method signatures with return types explicit |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/core/src/zorivest_core/application/market_expansion_dtos.py` | new | 7 frozen dataclass DTOs |
| `packages/core/src/zorivest_core/application/ports.py` | modify | Add 8 new method signatures to `MarketDataPort` |
| `tests/unit/test_market_expansion_dtos.py` | new | Construction, immutability, required-field tests |

---

### MEU-183: Market Expansion Tables

#### Boundary Inventory

N/A — DB schema definition. Write surface is internal pipeline/service only.

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-1 | `MarketEarningsModel` with `(ticker, fiscal_period, fiscal_year)` unique constraint | Spec | Duplicate insert → `IntegrityError` |
| AC-2 | `MarketDividendsModel` with `(ticker, ex_date)` unique constraint | Spec | Duplicate insert → `IntegrityError` |
| AC-3 | `MarketSplitsModel` with `(ticker, execution_date)` unique constraint | Spec | Duplicate insert → `IntegrityError` |
| AC-4 | `MarketInsiderModel` with `(ticker, name, transaction_date, transaction_code)` unique constraint | Spec | Duplicate insert → `IntegrityError` |
| AC-5 | All 4 tables created via `Base.metadata.create_all()` | Local Canon | N/A |
| AC-6 | Column types match DTO field types (Decimal→Numeric(18,8), date→Date, etc.) | Spec + Local Canon | N/A |
| AC-7 | `market_ohlcv` table NOT duplicated (uses existing `MarketOHLCVModel`) | Spec | N/A |
| AC-8 | Economic calendar events NOT persisted (transient — no table) | Spec | N/A |
| AC-9 | All existing tests pass without modification | Local Canon | N/A |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| Table names + unique constraints | Spec | Explicitly listed in §8a.2 |
| Column types | Spec + Local Canon | Derived from DTO fields; follow existing model patterns (Numeric precision, String lengths) |
| Migration approach | Local Canon | `Base.metadata.create_all()` — no Alembic (line 761 models.py) |
| Existing table reuse | Spec | OHLCV uses existing; fundamentals extend existing |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/infrastructure/src/zorivest_infra/database/models.py` | modify | Add 4 new SQLAlchemy models after existing market data models |
| `tests/unit/test_market_expansion_tables.py` | new | Model creation, unique constraint, column type tests |

---

### MEU-184: Provider Capabilities Registry

#### Boundary Inventory

N/A — frozen dataclass lookup registry. No external user input.

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-1 | `ProviderCapabilities` frozen dataclass with 7 fields: builder_mode, auth_mode, multi_symbol_style, pagination_style, extractor_shape, supported_data_types, free_tier | Spec | `FrozenInstanceError` on assignment |
| AC-2 | `FreeTierConfig` frozen dataclass with 4 fields: requests_per_minute, requests_per_day, history_depth_years, delay_minutes | Spec | `FrozenInstanceError` on assignment |
| AC-3 | Registry contains exactly 11 entries (Alpha Vantage, Polygon, Finnhub, FMP, EODHD, Nasdaq DL, SEC API, API Ninjas, OpenFIGI, Alpaca, Tradier) | Spec | N/A |
| AC-4 | Each provider's `builder_mode` matches spec table | Spec | N/A |
| AC-5 | Each provider's `extractor_shape` matches spec table | Spec | N/A |
| AC-6 | Each provider's `supported_data_types` matches spec table | Spec | N/A |
| AC-7 | Free tier config values match verified 2026 rate limits | Spec + Research-backed | N/A |
| AC-8 | `get_capabilities(name)` returns correct `ProviderCapabilities` for known provider | Local Canon | N/A |
| AC-9 | `get_capabilities(name)` for unknown provider raises `KeyError` | Local Canon | `get_capabilities("Unknown")` → `KeyError` |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| Dataclass fields and Literal types | Spec | Fully defined in §8a.3 |
| 11 provider entries | Spec | Complete table with all values |
| Free tier rate limits | Research-backed | Verified 2026 values in §8a rate limit table |
| Lookup function signature | Local Canon | Follow existing `provider_registry.py` pattern |
| File location | Local Canon | New file `provider_capabilities.py` in `market_data/` |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/infrastructure/src/zorivest_infra/market_data/provider_capabilities.py` | new | `ProviderCapabilities` + `FreeTierConfig` dataclasses + 11 registry entries |
| `tests/unit/test_provider_capabilities.py` | new | Dataclass construction, registry completeness, Literal validation |

---

## Out of Scope

- URL builders (MEU-185, 186) — Session 2
- Response extractors (MEU-187, 188, 189) — Session 2–3
- Service methods (MEU-190, 191) — Session 4
- REST routes + MCP actions (MEU-192) — Session 5
- Pipeline persistence + scheduling (MEU-193, 194) — Session 5
- Any runtime HTTP calls to provider APIs

---

## BUILD_PLAN.md Audit

Phase 8a MEU rows (MEU-182a → MEU-194) already exist in `BUILD_PLAN.md` at lines 281–294. No duplicate rows needed. Prior stale references (12-provider at line 73, Alembic at line 283) were corrected during plan review. One documentation gap remains:

- **Line 91**: Phase 8a status tracker row is missing (tracker jumps from Phase 8 at line 90 to Phase 9 at line 91)

```powershell
rg "^\| 8a —" docs/BUILD_PLAN.md  # Expected: 1 match (new tracker row) after fix
rg "MEU-182" docs/BUILD_PLAN.md  # Expected: existing rows at lines 281-282
```

---

## Verification Plan

### 1. Benzinga Purge Verification
```powershell
rg -i benzinga packages/ tests/ --glob "!*.pyc" *> C:\Temp\zorivest\benzinga-check.txt; Get-Content C:\Temp\zorivest\benzinga-check.txt
# Expected: 0 matches
```

### 2. Unit Tests
```powershell
uv run pytest tests/ -x --tb=short -v *> C:\Temp\zorivest\pytest.txt; Get-Content C:\Temp\zorivest\pytest.txt | Select-Object -Last 40
# Expected: All pass (existing + new)
```

### 3. Type Check
```powershell
uv run pyright packages/ *> C:\Temp\zorivest\pyright.txt; Get-Content C:\Temp\zorivest\pyright.txt | Select-Object -Last 30
# Expected: 0 errors
```

### 4. Lint Check
```powershell
uv run ruff check packages/ *> C:\Temp\zorivest\ruff.txt; Get-Content C:\Temp\zorivest\ruff.txt | Select-Object -Last 20
# Expected: 0 errors
```

### 5. Anti-Placeholder Scan
```powershell
rg "TODO|FIXME|NotImplementedError" packages/ *> C:\Temp\zorivest\placeholder.txt; Get-Content C:\Temp\zorivest\placeholder.txt
# Expected: 0 new matches
```

### 6. MEU Gate
```powershell
uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate.txt; Get-Content C:\Temp\zorivest\validate.txt | Select-Object -Last 50
```

---

## Open Questions

None — all 4 MEUs are fully specified with explicit acceptance criteria.

---

## Research References

- [08a-market-data-expansion.md](../../build-plan/08a-market-data-expansion.md) `[Spec]`
- [market-data-research-synthesis.md](../../_inspiration/data-provider-api-expansion-research/market-data-research-synthesis.md) `[Research-backed]`
- [market-data-expansion-doc-update-plan.md](../../_inspiration/data-provider-api-expansion-research/market-data-expansion-doc-update-plan.md) `[Local Canon]`
