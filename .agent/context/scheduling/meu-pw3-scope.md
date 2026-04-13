# MEU-PW3: Market Data Schemas

> **Matrix:** P2.5 item 49.6 · **Slug:** `market-data-schemas`  
> **Status:** ⬜ Planned · **Effort:** S-M (1 session)  
> **Depends on:** None (independent — can run before, after, or parallel with PW1/PW2)  
> **Unblocks:** Proper type enforcement, indexing, and validation for all market data types

---

## Objective

Create SQLAlchemy ORM models for 4 market data tables, add Pandera validation schemas for 3 missing data types, and extend field mappings beyond OHLCV. After this MEU, all market data written by `TransformStep` has proper type constraints, indexes, and runtime validation.

---

## Gap Items Covered

| Item | Description | Category | Effort |
|------|-------------|----------|--------|
| S-1 | Create `MarketOHLCVModel` SQLAlchemy model | Schema | S |
| S-2 | Create `MarketQuoteModel` SQLAlchemy model | Schema | S |
| S-3 | Create `MarketNewsModel` SQLAlchemy model | Schema | S |
| S-4 | Create `MarketFundamentalsModel` SQLAlchemy model | Schema | S |
| S-5 | Create 3 Pandera schemas (quotes, news, fundamentals) | Schema | S |
| S-6 | Add field mappings for non-OHLCV data types | Schema | S |

**Total: 6 items** (all S)

---

## Current State

### What Exists

The 4 tables are defined **only** as column allowlists in [write_dispositions.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/repositories/write_dispositions.py):

```python
TABLE_ALLOWLIST: dict[str, set[str]] = {
    "market_ohlcv": {"ticker", "date", "open", "high", "low", "close", "volume", ...},  # 10 cols
    "market_quotes": {"ticker", "bid", "ask", "last", "volume", "timestamp", "provider"},  # 7 cols
    "market_news": {"ticker", "headline", "source", "url", "published_at", ...},  # 8 cols
    "market_fundamentals": {"ticker", "metric", "value", "period", ...},  # 6 cols
}
```

- The `write_append()` function uses raw SQL `INSERT INTO` which creates tables dynamically in SQLite
- Tables get **no type constraints, no foreign keys, no indexes**
- Only `market_ohlcv` has a Pandera schema ([OHLCV_SCHEMA](file:///p:/zorivest/packages/core/src/zorivest_core/services/validation_gate.py#L24))
- Only `ohlcv` has field mappings in [field_mappings.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/market_data/field_mappings.py) (3 entries: generic, ibkr, polygon)

### What's Missing

1. **4 SQLAlchemy models** with proper column types, constraints, and indexes
2. **3 Pandera DataFrameSchema** definitions for runtime validation
3. **Field mappings** for quotes, news, and fundamentals per provider
4. **Alembic migration** to create tables with proper DDL (instead of dynamic creation)

---

## Deliverables

### 1. SQLAlchemy ORM Models (S-1 through S-4)

**File:** [models.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/models.py) (append after `AuditLogModel`)

#### MarketOHLCVModel

```python
class MarketOHLCVModel(Base):
    """OHLCV candlestick data (daily bars)."""
    __tablename__ = "market_ohlcv"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[int] = mapped_column(BigInteger, nullable=False)
    adjusted_close: Mapped[float | None] = mapped_column(Float)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("ticker", "date", "provider", name="uq_ohlcv_ticker_date_provider"),
        Index("ix_ohlcv_ticker_date", "ticker", "date"),
    )
```

#### MarketQuoteModel

```python
class MarketQuoteModel(Base):
    """Real-time quote snapshots."""
    __tablename__ = "market_quotes"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    bid: Mapped[float | None] = mapped_column(Float)
    ask: Mapped[float | None] = mapped_column(Float)
    last: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[int | None] = mapped_column(BigInteger)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)

    __table_args__ = (
        Index("ix_quote_ticker_timestamp", "ticker", "timestamp"),
    )
```

#### MarketNewsModel

```python
class MarketNewsModel(Base):
    """News articles associated with tickers."""
    __tablename__ = "market_news"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str | None] = mapped_column(String(20), index=True)
    headline: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    sentiment: Mapped[float | None] = mapped_column(Float)
    summary: Mapped[str | None] = mapped_column(Text)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)

    __table_args__ = (
        Index("ix_news_ticker_published", "ticker", "published_at"),
    )
```

#### MarketFundamentalsModel

```python
class MarketFundamentalsModel(Base):
    """Fundamental financial metrics per ticker."""
    __tablename__ = "market_fundamentals"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    metric: Mapped[str] = mapped_column(String(50), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    period: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g., "2024-Q3", "2024-FY"
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("ticker", "metric", "period", "provider", name="uq_fund_ticker_metric_period"),
        Index("ix_fund_ticker_metric", "ticker", "metric"),
    )
```

### 2. Pandera Validation Schemas (S-5)

**File:** [validation_gate.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/validation_gate.py) (append after `OHLCV_SCHEMA`)

```python
QUOTE_SCHEMA = pa.DataFrameSchema({
    "ticker": pa.Column(str, nullable=False),
    "last": pa.Column(float, pa.Check.greater_than(0), nullable=False),
    "bid": pa.Column(float, pa.Check.greater_than_or_equal_to(0), nullable=True),
    "ask": pa.Column(float, pa.Check.greater_than_or_equal_to(0), nullable=True),
    "volume": pa.Column(int, pa.Check.greater_than_or_equal_to(0), nullable=True),
    "timestamp": pa.Column("datetime64[ns]", nullable=False),
    "provider": pa.Column(str, nullable=False),
})

NEWS_SCHEMA = pa.DataFrameSchema({
    "headline": pa.Column(str, pa.Check.str_length(min_value=1), nullable=False),
    "source": pa.Column(str, nullable=False),
    "url": pa.Column(str, pa.Check.str_startswith("http"), nullable=False),
    "published_at": pa.Column("datetime64[ns]", nullable=False),
    "sentiment": pa.Column(float, pa.Check.in_range(-1.0, 1.0), nullable=True),
})

FUNDAMENTALS_SCHEMA = pa.DataFrameSchema({
    "ticker": pa.Column(str, nullable=False),
    "metric": pa.Column(str, nullable=False),
    "value": pa.Column(float, nullable=False),
    "period": pa.Column(str, pa.Check.str_matches(r"^\d{4}-(Q[1-4]|FY|H[12])$"), nullable=False),
})
```

**Update schema registry** in `validate_dataframe()`:

```python
SCHEMA_REGISTRY: dict[str, pa.DataFrameSchema] = {
    "ohlcv": OHLCV_SCHEMA,
    "quote": QUOTE_SCHEMA,       # NEW
    "news": NEWS_SCHEMA,         # NEW
    "fundamentals": FUNDAMENTALS_SCHEMA,  # NEW
}
```

### 3. Field Mappings (S-6)

**File:** [field_mappings.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/market_data/field_mappings.py)

Add provider-specific field mappings for quotes, news, and fundamentals:

```python
FIELD_MAPPINGS["quote"] = {
    "generic": {"bid": "bid", "ask": "ask", "last": "last", ...},
    "yahoo": {"regularMarketBid": "bid", "regularMarketAsk": "ask", ...},
    "polygon": {"bidPrice": "bid", "askPrice": "ask", ...},
}

FIELD_MAPPINGS["news"] = {
    "generic": {"headline": "headline", "source": "source", ...},
    "polygon": {"title": "headline", "publisher.name": "source", ...},
}

FIELD_MAPPINGS["fundamentals"] = {
    "generic": {"metric": "metric", "value": "value", ...},
}
```

### 4. Update write_dispositions.py (optional enhancement)

Consider updating the raw SQL functions to validate DataFrame columns against the ORM model's column types before executing INSERT. This would catch type mismatches at write time rather than leaving them to SQLite's flexible typing.

---

## Files Changed

| File | Change Type | Package |
|------|-------------|---------|
| `models.py` | Modify (4 new models) | infra |
| `validation_gate.py` | Modify (3 new schemas + registry update) | core |
| `field_mappings.py` | Modify (add 3 data type mappings) | infra |
| `write_dispositions.py` | Modify (optional: type validation) | infra |
| `test_market_data_schemas.py` | **NEW** | tests/unit |
| `test_validation_schemas.py` | **NEW** | tests/unit |

**Blast radius:** 4 modified + 2 new = 6 files across 2 packages.

---

## Acceptance Criteria

- **AC-1:** 4 SQLAlchemy models exist with proper column types, nullable constraints, and indexes
- **AC-2:** `UniqueConstraint` prevents duplicate entries per model's natural key
- **AC-3:** `QUOTE_SCHEMA`, `NEWS_SCHEMA`, `FUNDAMENTALS_SCHEMA` defined in Pandera
- **AC-4:** `SCHEMA_REGISTRY` resolves all 4 data types (`ohlcv`, `quote`, `news`, `fundamentals`)
- **AC-5:** `validate_dataframe()` applies the correct schema per data_type parameter
- **AC-6:** `FIELD_MAPPINGS` has entries for all 4 data types with at least `generic` mapping
- **AC-7:** Unit tests verify model creation, schema validation (valid + invalid data), and field mapping resolution
- **AC-8:** All existing tests continue to pass

---

## Relationship to PW1/PW2

| Concern | PW1 | PW2 | PW3 |
|---------|-----|-----|-----|
| Pipeline can execute | ✅ (4/5 steps) | ✅ (5/5 steps) | — |
| Data is validated | — | — | ✅ |
| Tables have indexes | — | — | ✅ |
| Type constraints enforced | — | — | ✅ |

PW3 is a quality-hardening MEU. Pipelines work without it (PW1+PW2), but data quality is weak — no type checking, no indexes, no validation for 3 of 4 data types.
