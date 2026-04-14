---
project: "2026-04-14-market-data-schemas"
date: "2026-04-14"
source: "docs/build-plan/09-scheduling.md §9.5, .agent/context/scheduling/meu-pw3-scope.md"
meus: ["MEU-PW3"]
status: "draft"
template_version: "2.0"
---

# Implementation Plan: Market Data Schemas

> **Project**: `2026-04-14-market-data-schemas`
> **Build Plan Section(s)**: P2.5b item 49.6
> **Status**: `draft`

---

## Goal

Replace the dynamic, untyped raw SQL tables used by the market data pipeline with proper SQLAlchemy ORM models, Pandera validation schemas, and provider-specific field mappings. After this MEU, all 4 market data tables have DDL-enforced type constraints, composite indexes for query performance, and runtime validation for all data types (not just OHLCV).

**Current state:** The 4 market data tables exist only as column-name allowlists in `write_dispositions.py`. The `write_append()` function uses raw `INSERT INTO` SQL which creates tables dynamically in SQLite with no type constraints, foreign keys, or indexes. Only the `ohlcv` data type has Pandera validation and field mappings — quotes, news, and fundamentals have none.

---

## User Review Required

> [!IMPORTANT]
> **ORM style decision:** The scope doc uses SQLAlchemy 2.0 `Mapped[T]` + `mapped_column()` style, but ALL 31 existing models in `models.py` use the 1.x `Column()` style. This plan uses **Column() style for consistency** with Local Canon. This is a deliberate deviation from the scope doc code snippets.

> [!IMPORTANT]
> **MarketQuote DTO field mismatch:** The `MarketQuote` DTO has a `price` field, but the TABLE_ALLOWLIST and ORM model use `last`. The field mapping layer (`apply_field_mapping`) handles this translation (`price` → `last`). Similarly, `MarketNewsItem` DTO has `title`, but the model uses `headline`.

> [!IMPORTANT]
> **TABLE_ALLOWLIST sync:** The ORM model column sets will be a **superset** of the current allowlist columns. New columns (`adjusted_close`, `fetched_at`, `summary` etc.) will be added to the allowlist. No existing columns will be removed — backward compatibility with current pipeline writes is preserved.

---

## Proposed Changes

### Component 1: SQLAlchemy ORM Models (S-1 through S-4)

#### Boundary Inventory

N/A — this MEU defines internal schemas, not external input surfaces.

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-1 | 4 SQLAlchemy models exist with proper column types, nullable constraints, and indexes | Spec | Model with NULL in non-nullable column raises IntegrityError |
| AC-2 | UniqueConstraint prevents duplicate entries per model's natural key | Spec | Inserting duplicate (ticker, timestamp, provider) in OHLCV raises IntegrityError |
| AC-3 | `Base.metadata.create_all()` creates all 35 tables (31 existing + 4 new) | Local Canon | Table count assertion fails if any model is malformed |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| 4 ORM models with column types | Spec | Complete column definitions given in scope doc |
| Column() vs Mapped[] style | Local Canon | Use Column() to match existing 31 models |
| `timestamp` column name | Local Canon | Keep `timestamp` (DateTime) to match live pipeline — field_mappings.py:43 and write_dispositions.py:31 both use `timestamp` |
| Volume column type | Research-backed | Use Integer (SQLite doesn't distinguish BigInteger); existing TradeModel uses Float for volume |
| `server_default=func.now()` | Local Canon | Not used by existing models — set `fetched_at` as nullable DateTime instead |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| [models.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/models.py) | modify | Add 4 new model classes after `AuditLogModel` (before scheduling triggers section) |

**4 new models (Column() style, matching existing code):**

1. **`MarketOHLCVModel`** — `market_ohlcv` table
   - Columns: `id` (PK), `ticker` (String(20), indexed), `timestamp` (DateTime, not-null), `open`/`high`/`low`/`close` (Float, not-null), `volume` (Integer, not-null), `vwap` (Float, nullable), `trade_count` (Integer, nullable), `adjusted_close` (Float, nullable), `provider` (String(50), not-null), `data_type` (String(20), nullable), `fetched_at` (DateTime, nullable)
   - UniqueConstraint: `(ticker, timestamp, provider)` → `uq_ohlcv_ticker_timestamp_provider`
   - Composite Index: `ix_ohlcv_ticker_timestamp`

2. **`MarketQuoteModel`** — `market_quotes` table
   - Columns: `id` (PK), `ticker` (String(20), indexed), `bid`/`ask` (Float, nullable), `last` (Float, not-null), `volume` (Integer, nullable), `timestamp` (DateTime, not-null), `provider` (String(50), not-null)
   - Composite Index: `ix_quote_ticker_timestamp`
   - No UniqueConstraint — quotes are append-only snapshots

3. **`MarketNewsModel`** — `market_news` table
   - Columns: `id` (PK), `ticker` (String(20), nullable, indexed), `headline` (Text, not-null), `summary` (Text, nullable), `source` (String(100), not-null), `url` (Text, not-null), `published_at` (DateTime, not-null), `sentiment` (Float, nullable), `provider` (String(50), not-null)
   - UniqueConstraint: `(url, provider)` → `uq_news_url_provider`
   - Composite Index: `ix_news_ticker_published`

4. **`MarketFundamentalsModel`** — `market_fundamentals` table
   - Columns: `id` (PK), `ticker` (String(20), indexed), `metric` (String(50), not-null), `value` (Float, not-null), `period` (String(20), not-null), `provider` (String(50), not-null), `fetched_at` (DateTime, nullable)
   - UniqueConstraint: `(ticker, metric, period, provider)` → `uq_fund_ticker_metric_period`
   - Composite Index: `ix_fund_ticker_metric`

---

### Component 2: Pandera Validation Schemas (S-5)

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-4 | `QUOTE_SCHEMA`, `NEWS_SCHEMA`, `FUNDAMENTALS_SCHEMA` defined with appropriate checks | Spec | Negative price in quote fails validation |
| AC-5 | `SCHEMA_REGISTRY` dict resolves all 4 data types (`ohlcv`, `quote`, `news`, `fundamentals`) | Spec | Unknown schema name raises ValueError |
| AC-6 | `validate_dataframe()` applies correct schema per `schema_name` parameter | Spec | Passing quote data through ohlcv schema quarantines rows |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| 3 new Pandera schemas with check constraints | Spec | Complete definitions in scope doc |
| Registry naming (_SCHEMAS → SCHEMA_REGISTRY) | Local Canon | Promote to public `SCHEMA_REGISTRY` for importability; keep backward-compat alias |
| `strict=False` on new schemas | Research-backed | Match OHLCV_SCHEMA behavior — allow extra columns through |
| Quote timestamp type `datetime64[ns]` | Research-backed | Use `"datetime64[ns]"` string type for Pandera datetime validation |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| [validation_gate.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/validation_gate.py) | modify | Add 3 schemas, rename `_SCHEMAS` → `SCHEMA_REGISTRY`, add `__all__` exports |

**3 new schemas:**

1. **`QUOTE_SCHEMA`** — validates quote data
   - `ticker`: str, not-null
   - `last`: float, >0, not-null
   - `bid`/`ask`: float, ≥0, nullable
   - `volume`: int, ≥0, nullable, coerce=True
   - `timestamp`: datetime64[ns], not-null
   - `provider`: str, not-null

2. **`NEWS_SCHEMA`** — validates news articles
   - `headline`: str, min_length=1, not-null
   - `source`: str, not-null
   - `url`: str, starts_with("http"), not-null
   - `published_at`: datetime64[ns], not-null
   - `sentiment`: float, in_range(-1.0, 1.0), nullable

3. **`FUNDAMENTALS_SCHEMA`** — validates fundamental metrics
   - `ticker`: str, not-null
   - `metric`: str, not-null
   - `value`: float, not-null
   - `period`: str, matches `^\d{4}-(Q[1-4]|FY|H[12])$`, not-null

---

### Component 3: Field Mappings (S-6)

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-7 | `FIELD_MAPPINGS` has entries for all 4 data types with at least `generic` mapping each | Spec | Missing mapping key returns empty dict (graceful fallback) |
| AC-8 | `apply_field_mapping()` correctly translates provider-specific fields to canonical names | Spec | Unmapped fields go to `_extra` dict |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| Concrete field names per provider | Research-backed | Derived from MarketQuote/MarketNewsItem DTOs + provider API docs |
| Generic identity mappings | Spec | 1:1 canonical→canonical for each data type |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| [field_mappings.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/market_data/field_mappings.py) | modify | Add 9 new mapping entries (3 data types × 3 providers) |

**New mapping entries (using existing `(provider, data_type)` tuple key):**

```python
# Quotes
("generic", "quote"):  {"bid": "bid", "ask": "ask", "last": "last", "volume": "volume", "timestamp": "timestamp"}
("yahoo", "quote"):    {"regularMarketBid": "bid", "regularMarketAsk": "ask", "regularMarketPrice": "last", "regularMarketVolume": "volume"}
("polygon", "quote"):  {"bidPrice": "bid", "askPrice": "ask", "lastTrade": "last", "volume": "volume"}

# News
("generic", "news"):   {"headline": "headline", "source": "source", "url": "url", "published_at": "published_at", "sentiment": "sentiment"}
("yahoo", "news"):     {"title": "headline", "publisher": "source", "link": "url", "providerPublishTime": "published_at"}
("polygon", "news"):   {"title": "headline", "publisher": "source", "article_url": "url", "published_utc": "published_at"}

# Fundamentals
("generic", "fundamentals"):  {"metric": "metric", "value": "value", "period": "period"}
("yahoo", "fundamentals"):    {"shortName": "metric", "raw": "value", "fiscalQuarter": "period"}
("polygon", "fundamentals"):  {"label": "metric", "value": "value", "fiscal_period": "period"}
```

---

### Component 4: TABLE_ALLOWLIST Sync

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-9 | `TABLE_ALLOWLIST` column sets are a superset of each ORM model's column names | Local Canon | `validate_columns()` rejects column not in allowlist |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| [write_dispositions.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/repositories/write_dispositions.py) | modify | Sync TABLE_ALLOWLIST column sets with ORM model columns (add `adjusted_close`, `fetched_at`, `summary`) |

---

### Component 5: Tests (TDD — write first)

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| [test_market_data_models.py](file:///p:/zorivest/tests/unit/test_market_data_models.py) | new | ORM model creation, column types, constraints, unique key violations |
| [test_validation_schemas.py](file:///p:/zorivest/tests/unit/test_validation_schemas.py) | new | Pandera schema validation for all 4 data types (valid + invalid data) |
| [test_field_mappings.py](file:///p:/zorivest/tests/unit/test_field_mappings.py) | new | Field mapping resolution for all 4 data types × providers |
| [test_models.py](file:///p:/zorivest/tests/unit/test_models.py) | modify | Update EXPECTED_TABLES (31→35) and table count assertion (31→35) |

---

## Out of Scope

- Alembic migration infrastructure (tables created via `Base.metadata.create_all()` per Local Canon)
- ORM-based write path in `write_dispositions.py` (raw SQL INSERT preserved; ORM models provide DDL + query access)
- TransformStep changes (already references `validate_dataframe()` correctly)
- Provider API client implementations (field mappings are data-only, no network calls)

---

## BUILD_PLAN.md Audit

This project adds MEU-PW3 to the P2.5b table and updates the MEU Summary completion counts.

```powershell
rg "MEU-PW3" docs/BUILD_PLAN.md  # Expected: 1 match (new row added)
```

Changes needed:
1. Add MEU-PW3 row to P2.5b table (after MEU-PW2)
2. Update P2.5b completion count: `3 | 0` → `4 | 2` (PW1 ✅, PW2 ✅ already tracked)
3. Update Total row in MEU Summary

---

## Verification Plan

### 1. Unit Tests
```powershell
uv run pytest tests/unit/test_market_data_models.py tests/unit/test_validation_schemas.py tests/unit/test_field_mappings.py -x --tb=short -v *> C:\Temp\zorivest\pytest-pw3.txt; Get-Content C:\Temp\zorivest\pytest-pw3.txt | Select-Object -Last 40
```

### 2. Existing Test Regression
```powershell
uv run pytest tests/unit/test_models.py tests/unit/test_transform_step.py -x --tb=short -v *> C:\Temp\zorivest\pytest-regression.txt; Get-Content C:\Temp\zorivest\pytest-regression.txt | Select-Object -Last 20
```

### 3. Full Test Suite
```powershell
uv run pytest tests/ -x --tb=short *> C:\Temp\zorivest\pytest-full.txt; Get-Content C:\Temp\zorivest\pytest-full.txt | Select-Object -Last 30
```

### 4. Type Check
```powershell
uv run pyright packages/ *> C:\Temp\zorivest\pyright.txt; Get-Content C:\Temp\zorivest\pyright.txt | Select-Object -Last 30
```

### 5. Lint
```powershell
uv run ruff check packages/ *> C:\Temp\zorivest\ruff.txt; Get-Content C:\Temp\zorivest\ruff.txt | Select-Object -Last 20
```

### 6. MEU Gate
```powershell
uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate.txt; Get-Content C:\Temp\zorivest\validate.txt | Select-Object -Last 50
```

---

## Open Questions

None — all design decisions are resolved using Spec + Local Canon + Research-backed sources.

---

## Research References

- [meu-pw3-scope.md](file:///p:/zorivest/.agent/context/scheduling/meu-pw3-scope.md) — MEU scope document
- [09-scheduling.md §9.5](file:///p:/zorivest/docs/build-plan/09-scheduling.md) — Pipeline data quality spec
- [market_dtos.py](file:///p:/zorivest/packages/core/src/zorivest_core/application/market_dtos.py) — Normalized DTO definitions
- Local Canon: existing `models.py` Column() style, `write_dispositions.py` allowlist pattern
