# Phase 8a: Market Data Expansion

> Part of [Zorivest Build Plan](../BUILD_PLAN.md) | Prerequisites: [Phase 8](08-market-data.md) (MEU-56→65 ✅) | Consumers: [Phase 5](05-mcp-server.md), [Phase 6](06-gui.md), [Phase 9](09-scheduling.md)
>
> **Source**: [market-data-research-synthesis.md](../../_inspiration/data-provider-api-expansion-research/market-data-research-synthesis.md) `[Spec]`, [market-data-expansion-doc-update-plan.md](../../_inspiration/data-provider-api-expansion-research/market-data-expansion-doc-update-plan.md) `[Local Canon]`

---

## Goal

Expand the market data aggregation layer from authentication-only stubs to a fully functional, multi-provider data pipeline. Implements 8 new data types (OHLCV, fundamentals, earnings, dividends, splits, insider, economic calendar, company profile) across 11 API-key providers with dedicated URL builders, response extractors, field mappings, normalizers, REST endpoints, MCP actions, and pipeline persistence.

> [!IMPORTANT]
> Phase 8 (MEU-56→65) established the provider registry, auth infrastructure, and connection testing. Phase 8a builds the **data retrieval layer** on top of that foundation.

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        Phase 8a Expansion Layers                        │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Layer 6: Pipeline Persistence + Scheduling Recipes (MEU-193, 194)      │
│     ↑                                                                    │
│  Layer 5: API Routes + MCP Actions (MEU-192)                            │
│     ↑                                                                    │
│  Layer 4: Service Methods + Normalizers (MEU-190, 191)                  │
│     ↑                                                                    │
│  Layer 3: Extractors + Field Mappings (MEU-187, 188, 189)               │
│     ↑                                                                    │
│  Layer 2: URL Builders (MEU-184, 185, 186)                              │
│     ↑                                                                    │
│  Layer 1: Domain Models + DB Tables (MEU-182, 183)                      │
│     ↑                                                                    │
│  Layer 0: Benzinga Code Purge (MEU-182a)                                │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Layer 0: Benzinga Code Purge (1 MEU)

### Step 8a.0: Remove Benzinga Provider Code (MEU-182a `benzinga-code-purge`)

> **Rationale**: Benzinga was removed from all documentation in this phase. The code must be purged to match `[Human-approved, 2026-05-01]`. Without this, the provider registry reports 12 entries but docs say 11.

**Files to modify (production):**

| File | What to Remove |
|------|---------------|
| `packages/infrastructure/src/zorivest_infra/market_data/provider_registry.py` | `"Benzinga": ProviderConfig(...)` entry (lines 103–112) |
| `packages/infrastructure/src/zorivest_infra/market_data/normalizers.py` | `normalize_benzinga_news()` function (lines 190–215) + dispatch table entry (line 262) |
| `packages/core/src/zorivest_core/services/market_data_service.py` | Fallback message mentioning Benzinga (line 151) + `elif name == "Benzinga"` branch (line 431) |
| `packages/core/src/zorivest_core/services/provider_connection_service.py` | `@_register_validator("Benzinga")` + `_validate_benzinga()` function (lines 149–150) |
| `packages/infrastructure/src/zorivest_infra/logging/redaction.py` | Comment mentioning Benzinga (line 23) |

**Files to modify (tests):**

| File | What to Remove |
|------|---------------|
| `tests/unit/test_provider_registry.py` | `"Benzinga"` from provider list (line 37) + auth method entry (line 64) |
| `tests/unit/test_normalizers.py` | `normalize_benzinga_news` import + `benzinga_news_data` fixture + `TestNormalizeBenzingaNews` class (~30 lines) |
| `tests/unit/test_provider_connection_service.py` | `"Benzinga": ProviderConfig(...)` in fixture + `TestBenzingaValidation` class (~20 lines) |

**Validation:**

```powershell
# 1. No Benzinga refs remain in production/test code
rg -i benzinga packages/ tests/ --glob "!*.pyc" → 0 matches

# 2. All tests pass
uv run pytest tests/ -x --tb=short -v

# 3. Type check clean
uv run pyright packages/
```

---

## Layer 1: Domain Models (2 MEUs)

### Step 8a.1: New DTOs (MEU-182 `market-expansion-dtos`)

7 new DTOs extending the existing `MarketQuote`, `MarketNewsItem`, `TickerSearchResult`, `SecFiling` from Phase 8:

```python
# packages/core/src/zorivest_core/application/market_expansion_dtos.py

@dataclass(frozen=True)
class OHLCVBar:
    ticker: str
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    adj_close: Decimal | None
    volume: int
    vwap: Decimal | None
    trade_count: int | None
    provider: str

@dataclass(frozen=True)
class FundamentalsSnapshot:
    ticker: str
    market_cap: Decimal | None
    pe_ratio: Decimal | None
    pb_ratio: Decimal | None
    ps_ratio: Decimal | None
    eps: Decimal | None
    dividend_yield: Decimal | None
    beta: Decimal | None
    sector: str | None
    industry: str | None
    employees: int | None
    provider: str
    timestamp: datetime

@dataclass(frozen=True)
class EarningsReport:
    ticker: str
    fiscal_period: str  # Q1, Q2, Q3, Q4, FY
    fiscal_year: int
    report_date: date
    eps_actual: Decimal | None
    eps_estimate: Decimal | None
    eps_surprise: Decimal | None
    revenue_actual: Decimal | None
    revenue_estimate: Decimal | None
    provider: str

@dataclass(frozen=True)
class DividendRecord:
    ticker: str
    dividend_amount: Decimal
    currency: str
    ex_date: date
    record_date: date | None
    pay_date: date | None
    declaration_date: date | None
    frequency: str | None  # quarterly, semi-annual, annual
    provider: str

@dataclass(frozen=True)
class StockSplit:
    ticker: str
    execution_date: date
    ratio_from: int
    ratio_to: int
    provider: str

@dataclass(frozen=True)
class InsiderTransaction:
    ticker: str
    name: str
    title: str | None
    transaction_date: date
    transaction_code: str  # P=purchase, S=sale, etc.
    shares: int
    price: Decimal | None
    value: Decimal | None
    shares_owned_after: int | None
    provider: str

@dataclass(frozen=True)
class EconomicCalendarEvent:
    event: str
    country: str
    date: date
    time: time | None
    impact: str | None  # low, medium, high
    actual: str | None
    forecast: str | None
    previous: str | None
    provider: str
```

Updated `MarketDataPort` protocol — add 8 new methods:

```python
class MarketDataPort(Protocol):
    # Existing (Phase 8)
    async def get_stock_quote(self, ticker: str, ...) -> MarketQuote: ...
    async def get_market_news(self, ...) -> list[MarketNewsItem]: ...
    async def search_ticker(self, query: str) -> list[TickerSearchResult]: ...
    async def get_sec_filings(self, ticker: str) -> list[SecFiling]: ...

    # New (Phase 8a)
    async def get_ohlcv(self, ticker: str, interval: str = "1d", ...) -> list[OHLCVBar]: ...
    async def get_fundamentals(self, ticker: str) -> FundamentalsSnapshot: ...
    async def get_earnings(self, ticker: str) -> list[EarningsReport]: ...
    async def get_dividends(self, ticker: str) -> list[DividendRecord]: ...
    async def get_splits(self, ticker: str) -> list[StockSplit]: ...
    async def get_insider(self, ticker: str) -> list[InsiderTransaction]: ...
    async def get_economic_calendar(self, ...) -> list[EconomicCalendarEvent]: ...
    async def get_company_profile(self, ticker: str) -> FundamentalsSnapshot: ...
```

### Step 8a.2: Database Tables (MEU-183 `market-expansion-tables`)

4 new SQLAlchemy models (via `Base.metadata.create_all()`):

| Table | Primary Key | Unique Constraint | Notes |
|-------|------------|-------------------|-------|
| `market_earnings` | `id` (auto) | `(ticker, fiscal_period, fiscal_year)` | EPS actual/estimate/surprise |
| `market_dividends` | `id` (auto) | `(ticker, ex_date)` | Amount, dates, frequency |
| `market_splits` | `id` (auto) | `(ticker, execution_date)` | Ratio from/to |
| `market_insider` | `id` (auto) | `(ticker, name, transaction_date, transaction_code)` | Transaction details |

> [!NOTE]
> OHLCV uses existing `market_ohlcv` table. Fundamentals use existing `market_quotes` with extended columns. Economic calendar events are transient (not persisted to dedicated table — used in report templates only).

---

## Layer 2: URL Builders (3 MEUs)

### Step 8a.3: Provider Capabilities Registry (MEU-184 `provider-capabilities`)

```python
# packages/infrastructure/src/zorivest_infra/market_data/provider_capabilities.py

@dataclass(frozen=True)
class ProviderCapabilities:
    builder_mode: Literal["simple_get", "function_get", "dataset_get", "post_body"]
    auth_mode: Literal["header", "query", "bearer", "dual_header"]
    multi_symbol_style: Literal["csv", "repeated_filter", "body_array", "none"]
    pagination_style: Literal["offset_limit", "next_page_token", "next_cursor_id", "next_url", "none"]
    extractor_shape: Literal["root_object", "root_array", "wrapper_array", "symbol_keyed_dict", "named_section_object", "parallel_arrays"]
    supported_data_types: list[str]
    free_tier: FreeTierConfig

@dataclass(frozen=True)
class FreeTierConfig:
    requests_per_minute: int | None
    requests_per_day: int | None
    history_depth_years: int | None
    delay_minutes: int  # 0 = real-time
```

Capability entries for all 11 API-key providers:

| Provider | Builder Mode | Extractor Shape | Supported Types |
|----------|-------------|-----------------|-----------------|
| Alpha Vantage | `function_get` | `named_section_object` | quote, ohlcv, earnings, fundamentals, insider, economic_calendar |
| Polygon.io | `simple_get` | `wrapper_array` | quote, ohlcv, news, dividends, splits, fundamentals |
| Finnhub | `simple_get` | `parallel_arrays` / `root_array` | quote, news, earnings, insider, economic_calendar |
| FMP | `simple_get` | `root_array` | quote, ohlcv, fundamentals, earnings, dividends, splits, news |
| EODHD | `simple_get` | `root_object` / `root_array` | ohlcv, fundamentals, dividends, splits, news |
| Nasdaq Data Link | `dataset_get` | `parallel_arrays` | fundamentals |
| SEC API | `post_body` | `root_array` | fundamentals, insider |
| API Ninjas | `simple_get` | `root_object` | quote, earnings, insider |
| OpenFIGI | `post_body` | `root_array` | identifier_mapping |
| Alpaca | `simple_get` | `symbol_keyed_dict` / `root_array` | quote, ohlcv, news |
| Tradier | `simple_get` | `root_object` | quote, ohlcv |

### Step 8a.4: Simple GET Builders (MEU-185 `simple-get-builders`)

5 dedicated builders following the `base_url + path + query_params` pattern:

| Builder | Provider | Key Endpoints |
|---------|----------|---------------|
| `AlpacaUrlBuilder` | Alpaca | `/v2/stocks/{symbol}/bars`, `/v2/stocks/snapshots` |
| `FMPUrlBuilder` | FMP | `/api/v3/quote/{symbol}`, `/api/v3/income-statement/{symbol}` |
| `EODHDUrlBuilder` | EODHD | `/api/eod/{symbol}.US`, `/api/fundamentals/{symbol}.US` |
| `APINinjasUrlBuilder` | API Ninjas | `/v1/stockprice`, `/v1/earnings` |
| `TradierUrlBuilder` | Tradier | `/v1/markets/quotes`, `/v1/markets/history` |

### Step 8a.5: Special-Pattern Builders (MEU-186 `special-pattern-builders`)

4 builders with non-standard URL construction:

| Builder | Pattern | Example |
|---------|---------|---------|
| `AlphaVantageUrlBuilder` | Function-dispatch GET | `?function=TIME_SERIES_DAILY&symbol=AAPL` |
| `NasdaqDataLinkUrlBuilder` | Dataset/table GET | `/datatables/SHARADAR/SF1.json?ticker=AAPL` |
| `OpenFIGIUrlBuilder` | POST with JSON body | `POST /v3/mapping [{"idType":"TICKER","idValue":"AAPL"}]` |
| `SECAPIUrlBuilder` | POST with Lucene query | `POST /full-text-search {"query":"AAPL","formType":"10-K"}` |

---

## Layer 3: Extractors + Field Mappings (3 MEUs)

### Step 8a.6: Standard Extractors (MEU-187 `extractors-standard`)

Standard JSON envelope extractors for 5 simple-GET providers + ~25 field mapping tuples:

| Provider | Extraction Pattern | Gotchas |
|----------|-------------------|---------|
| Alpaca | Multi-symbol → dict-keyed; single → flat list | Shape varies by call pattern |
| FMP | Root array; some endpoints return object | Check `isinstance(data, list)` |
| EODHD | Root object for EOD; nested sections for fundamentals | Section-aware flattening |
| API Ninjas | Root object with flat keys | Minimal transformation |
| Tradier | Root object; single-result collapses dict→list | `isinstance(x, list)` guard needed |

### Step 8a.7: Complex Extractors (MEU-188 `extractors-complex`)

Complex extractors for providers with non-standard response shapes + ~20 field mappings:

| Provider | Complexity | Pattern |
|----------|-----------|---------|
| Alpha Vantage OHLCV | Date-keyed dicts `{"2024-01-01": {"1. open": "150"}}` | `.items()` iterate + key prefix stripping |
| Alpha Vantage Earnings | **Returns CSV bytes** even with `datatype=json` | CSV parser required |
| Alpha Vantage Rate Limit | HTTP 200 with `{"Note": "..."}` (not 429) | Response body inspection |
| Finnhub Candles | Parallel arrays `{c:[],h:[],l:[],o:[],t:[],v:[]}` | `zip()` transformation |
| Nasdaq Data Link | Parallel arrays + `column_names` header | Column-name-aware zip |
| Polygon Timestamps | Millisecond UNIX timestamps | `t / 1000` before `datetime` |

> [!WARNING]
> **Finnhub OHLCV returns 403 on free tier since 2024.** The `FinnhubUrlBuilder` for OHLCV must be disabled or gated. Use Alpaca/EODHD/Polygon as primary OHLCV sources.

### Step 8a.8: POST-Body Runtime Wiring (MEU-189 `post-body-runtime`)

Wire the POST-body runtime dispatch layer so that providers classified as `builder_mode="post_body"` (OpenFIGI, SEC API, TradingView) can execute HTTP POST requests through the market data adapter and pipeline fetch infrastructure.

**Runtime dispatch changes:**

| Component | Change | Notes |
|-----------|--------|-------|
| `fetch_with_cache()` | Add `method` and `json_body` params; dispatch to `client.post()` for POST; skip ETag/If-None-Match conditional headers for POST (RFC 9110 §9.3.3) | Backward-compatible — GET default preserved |
| `MarketDataProviderAdapter._do_fetch()` | Accept `method` and `json_body`; detect POST builders via `hasattr(builder, 'build_request')` | Uses `RequestSpec` from MEU-186 builders |
| `provider_connection_service` | Add `_test_openfigi_post()` for OpenFIGI POST connection test (`/v3/mapping`, `X-OPENFIGI-APIKEY` header) | Resolves [MKTDATA-OPENFIGI405] |

**POST-body extractor notes (implemented in MEU-188):**

| Provider | Notes |
|----------|-------|
| OpenFIGI v3 | Renamed `error` → `warning` for no-match. **v2 sunsets July 1, 2026 (410 Gone).** |
| SEC API | Lucene response format; results in `filings` array |

---

## Layer 4: Service Methods + Normalizers (2 MEUs)

### Step 8a.9: Core Service Methods (MEU-190 `service-methods-core`)

3 high-value methods with provider fallback chains:

| Method | Primary | Fallbacks | Rationale |
|--------|---------|-----------|-----------|
| `get_ohlcv()` | Alpaca | EODHD, Polygon | 200/min, multi-ticker, 7yr history |
| `get_fundamentals()` | FMP | EODHD, Alpha Vantage | 250/day, broadest surface |
| `get_earnings()` | Finnhub | FMP, Alpha Vantage | Free calendar + history |

Each method includes a per-provider normalizer function that transforms raw extractor output → canonical DTO.

### Step 8a.10: Extended Service Methods (MEU-191 `service-methods-extended`)

5 additional methods:

| Method | Primary | Fallbacks |
|--------|---------|-----------|
| `get_dividends()` | Polygon | EODHD, FMP |
| `get_splits()` | Polygon | EODHD, FMP |
| `get_insider()` | Finnhub | FMP, SEC API |
| `get_economic_calendar()` | Finnhub | FMP, Alpha Vantage |
| `get_company_profile()` | FMP | Finnhub, EODHD |

---

## Layer 5: API Routes + MCP Actions (1 MEU)

### Step 8a.11: Routes + MCP (MEU-192 `market-routes-mcp`)

8 new REST endpoints:

| Method | Endpoint | Response DTO |
|--------|----------|-------------|
| `GET` | `/api/v1/market-data/ohlcv` | `list[OHLCVBar]` |
| `GET` | `/api/v1/market-data/fundamentals` | `FundamentalsSnapshot` |
| `GET` | `/api/v1/market-data/earnings` | `list[EarningsReport]` |
| `GET` | `/api/v1/market-data/dividends` | `list[DividendRecord]` |
| `GET` | `/api/v1/market-data/splits` | `list[StockSplit]` |
| `GET` | `/api/v1/market-data/insider` | `list[InsiderTransaction]` |
| `GET` | `/api/v1/market-data/economic-calendar` | `list[EconomicCalendarEvent]` |
| `GET` | `/api/v1/market-data/company-profile` | `FundamentalsSnapshot` |

8 new MCP action mappings added to `zorivest_market` compound tool:

| Action | Maps To |
|--------|---------|
| `ohlcv` | `GET /market-data/ohlcv` |
| `fundamentals` | `GET /market-data/fundamentals` |
| `earnings` | `GET /market-data/earnings` |
| `dividends` | `GET /market-data/dividends` |
| `splits` | `GET /market-data/splits` |
| `insider` | `GET /market-data/insider` |
| `economic_calendar` | `GET /market-data/economic-calendar` |
| `company_profile` | `GET /market-data/company-profile` |

#### Boundary Input Contract — MEU-192

| Boundary | Schema Owner | Extra-Field Policy | Error Mapping |
|----------|-------------|-------------------|---------------|
| REST query params | Pydantic `MarketDataQueryParams` | `extra="forbid"` | Invalid → 422; provider not found → 404; upstream error → 502 |
| MCP tool input | Zod `.strict()` schema | `.strict()` | Invalid → MCP error with 422 detail |
| Provider API responses | Per-provider extractor | `extra="allow"` `[Research-backed]` | Malformed → logged warning + empty result |

> **Create/Update Parity**: Read-only endpoints (`GET` only). No create/update paths.

**Field Constraints — `MarketDataQueryParams` (REST + MCP):**

| Field | Type | Constraint | Required | Default | Invalid → |
|-------|------|-----------|----------|---------|----------|
| `ticker` | `str` | 1–10 chars, uppercase alpha + `.` | Yes (except economic_calendar) | — | 422 |
| `provider` | `str \| None` | Must match `ProviderCapabilities` registry key | No | auto (fallback chain) | 404 |
| `interval` | `str` | Enum: `1m`, `5m`, `15m`, `30m`, `1h`, `1d`, `1w`, `1M` | No (ohlcv only) | `1d` | 422 |
| `start_date` | `date \| None` | ISO 8601 (`YYYY-MM-DD`), ≤ today | No | provider default | 422 |
| `end_date` | `date \| None` | ISO 8601, ≥ `start_date` | No | today | 422 |
| `limit` | `int \| None` | 1–1000 | No | 100 | 422 |
| `country` | `str \| None` | ISO 3166-1 alpha-2 (economic_calendar only) | No | `US` | 422 |
| `filing_type` | `str \| None` | Enum: `10-K`, `10-Q`, `8-K`, `S-1`, `DEF 14A` (filings only) | No | all types | 422 |

---

## Layer 6: Pipeline Persistence + Scheduling (2 MEUs)

### Step 8a.12: Market Data Store Step (MEU-193 `market-store-step`)

New `MarketDataStoreStep` (type: `market_data_store`) for pipeline policies:

- Routes normalized DTOs to canonical DB tables via `DbWriteAdapter`
- Supports `INSERT` and `UPSERT` (dedup by ticker+timestamp) write modes
- Validates via per-table Pandera schemas before write

#### Boundary Input Contract — MEU-193

| Boundary | Schema Owner | Extra-Field Policy | Error Mapping |
|----------|-------------|-------------------|---------------|
| Pipeline `steps[].config` | Pydantic `MarketDataStoreConfig` (`extra="forbid"`) | `extra="forbid"` | Invalid → policy VALIDATE phase error |
| DTO → SQLAlchemy write | Column constraints (`Numeric(18,8)`, `DateTime(tz=True)`, `String(10)`) | Extra columns rejected | Constraint violation → logged error + skip row |

> **Create/Update Parity**: `INSERT` and `UPSERT` both use same `MarketDataStoreConfig` with identical field constraints.

**Field Constraints — `MarketDataStoreConfig`:**

| Field | Type | Constraint | Required | Default | Invalid → |
|-------|------|-----------|----------|---------|----------|
| `data_type` | `str` | Enum: `ohlcv`, `earnings`, `dividends`, `splits`, `insider`, `fundamentals` | Yes | — | VALIDATE error |
| `target_table` | `str \| None` | Must match canonical table name if provided | No | auto from `data_type` | VALIDATE error |
| `write_mode` | `str` | Enum: `insert`, `upsert` | No | `upsert` | VALIDATE error |
| `ticker` | `str` | 1–10 chars, uppercase alpha + `.` | Yes | — | VALIDATE error |
| `provider` | `str \| None` | Must match `ProviderCapabilities` registry key | No | auto (fallback chain) | VALIDATE error |
| `batch_size` | `int` | 1–5000 | No | 1000 | VALIDATE error |

### Step 8a.13: Scheduling Recipes (MEU-194 `scheduling-recipes`)

10 pre-built policy templates seeded via Alembic migration:

| # | Recipe | Cron | Primary | Fallback |
|---|--------|------|---------|----------|
| 1 | Nightly OHLCV refresh | `0 22 * * 1-5` | Alpaca | EODHD |
| 2 | Pre-market quote sweep | `*/5 4-9 * * 1-5` | Finnhub | Alpaca |
| 3 | Weekly fundamentals | `0 6 * * 6` | FMP | Alpha Vantage |
| 4 | Daily earnings calendar | `0 5 * * *` | Finnhub | FMP |
| 5 | Weekly dividend tracker | `0 7 * * 1` | Polygon | EODHD |
| 6 | Near-real-time news | `*/2 6-20 * * 1-5` | Finnhub | Polygon |
| 7 | Daily insider transactions | `30 23 * * 1-5` | Finnhub | FMP |
| 8 | Weekly economic calendar | `0 6 * * 0` | Finnhub | FMP |
| 9 | Daily options chain | `30 15 * * 1-5` | Tradier | Polygon |
| 10 | Monthly ETF holdings | `0 8 1 * *` | FMP | EODHD |

---

## Dependency Chain

```
MEU-182a → MEU-182 → MEU-183 ─┐
                              ├→ MEU-190 → MEU-191 → MEU-192 → MEU-193 → MEU-194
MEU-182a → MEU-184 → MEU-185 → MEU-187 ─┤
                  └→ MEU-186 → MEU-188 ─┤
                             └→ MEU-189 ─┘
```

## Free-Tier Rate Limits (Verified 2026)

> [!CAUTION]
> Alpha Vantage dropped to **25/day**. Our `provider_registry.py` may have stale limits.

| Provider | Free Tier | Per-Minute | Notes |
|---|---|---|---|
| API Ninjas | 50K/month | ~1,600/day | Generous |
| **Alpaca** | **200/min** | **200** | Best free tier; IEX feed, 15-min delay |
| Alpha Vantage | **25/day** | 5 (paid) | Effectively unusable for production |
| EODHD | **20/day** | 1,000 (paid) | Fundamentals = 10 credits |
| FMP | **250/day** | 300 (paid) | US-only on free |
| **Finnhub** | **60/min** | **60** | OHLCV candles premium-only since 2024 |
| Nasdaq DL | 50K/day | 300/10s | Useful free data mostly macro |
| OpenFIGI | 25 req/6s | ~250 | Batches of 100 |
| Polygon | **5/min** | **5** | 2yr history, EOD-only |
| SEC API | **100/month** | — | Paid wrapper around EDGAR |
| Tradier | Generous | ~120 | Requires brokerage account |

---

## Test Plan

| Test File | What It Tests |
|-----------|---------------|
| `tests/unit/test_market_expansion_dtos.py` | DTO construction, validation, immutability |
| `tests/unit/test_provider_capabilities.py` | Capability registry completeness, enum coverage |
| `tests/unit/test_url_builders.py` | URL construction for all 4 builder modes × providers |
| `tests/unit/test_response_extractors.py` | Fixture-based extraction for each provider × data_type |
| `tests/unit/test_field_mappings.py` | Mapping completeness, canonical field coverage |
| `tests/unit/test_service_methods.py` | Normalizer + fallback chain with mocked HTTP |
| `tests/unit/test_market_routes.py` | REST endpoints via TestClient |
| `tests/unit/test_market_store_step.py` | Pipeline step config validation + DB write |
| `tests/typescript/mcp/market-expansion.test.ts` | MCP action mappings with mocked fetch |

---

## Exit Criteria

1. All 7 new DTOs pass construction + immutability tests
2. 4 new DB tables created via `Base.metadata.create_all()`
3. `ProviderCapabilities` entries exist for all 11 API-key providers
4. URL builders produce correct URLs for all provider × data_type combinations
5. Response extractors correctly unwrap fixture data for all supported providers
6. Field mappings cover all provider × data_type canonical fields
7. 8 new service methods return normalized data with fallback chains
8. 8 new REST endpoints return correct responses via TestClient
9. 8 new MCP actions map correctly to REST endpoints
10. `MarketDataStoreStep` writes validated data to correct DB tables
11. 10 scheduling recipes seed correctly via migration

---

## Outputs

- 7 new DTO dataclasses in `zorivest_core/application/market_expansion_dtos.py`
- 4 new SQLAlchemy models (no Alembic — `create_all()` pattern per Local Canon)
- `ProviderCapabilities` dataclass + 11 registry entries
- 9 dedicated URL builders (5 simple + 4 special)
- ~55 field mapping tuples across all provider × data_type pairs
- ~30 response extractor functions
- 8 new `MarketDataService` methods with normalizers
- 8 new REST API endpoints
- 8 new MCP action mappings
- `MarketDataStoreStep` pipeline step
- 10 pre-built scheduling recipe templates
