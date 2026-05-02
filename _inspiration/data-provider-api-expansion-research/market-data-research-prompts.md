# Market Data Provider — Deep Research Prompts

> Generated 2026-05-01 for Zorivest market data layer expansion.
>
> **Purpose**: Each prompt targets a specific AI research platform (Gemini, ChatGPT, Claude) to produce a comprehensive API capability mapping for all 12 API-key market data providers. The outputs will be used to:
> 1. Build provider-specific URL builders and response extractors
> 2. Wire data-fetch pipeline steps in the scheduling engine
> 3. Enable agentic AI to construct data-pull policies automatically
> 4. Store fetched data in the local SQLite database

---

## Current Codebase State (Context for All Prompts)

### What EXISTS (✅ Working)
- **Provider Registry**: 14 providers registered with auth configs (`provider_registry.py`)
- **Authentication**: API key encryption/decryption (Fernet), per-provider auth methods (query param, bearer header, custom header, raw header)
- **Connection Testing**: Test endpoint per provider, HTTP status interpretation (200/401/403/429/timeout)
- **Quote Normalizers**: Alpha Vantage, Polygon.io, Finnhub, EODHD, API Ninjas
- **Search Normalizers**: Financial Modeling Prep, Alpha Vantage
- **News Normalizers**: Benzinga, Finnhub
- **SEC Filing Normalizer**: SEC API
- **URL Builders**: Yahoo Finance, Polygon.io, Finnhub (others use GenericUrlBuilder)
- **Response Extractors**: Yahoo (quote/news), Polygon (ohlcv/quote/news), generic fallback
- **Field Mappings**: Yahoo, Polygon, Finnhub, IBKR, generic (for ohlcv/quote/news/fundamentals)
- **Pipeline Adapter**: `MarketDataProviderAdapter` with rate limiting, HTTP cache, multi-ticker support

### What's MISSING (❌ Gaps)
- **URL Builders**: No dedicated builders for Alpha Vantage, EODHD, FMP, Nasdaq Data Link, SEC API, API Ninjas, Benzinga, OpenFIGI, Alpaca, Tradier
- **Response Extractors**: No dedicated extractors for any provider except Yahoo and Polygon
- **Field Mappings**: Only Yahoo, Polygon, Finnhub, generic. Missing: Alpha Vantage, EODHD, FMP, Nasdaq, SEC, API Ninjas, Benzinga, OpenFIGI, Alpaca, Tradier
- **Data Types Beyond Quote**: Most providers only have `quote` wired. Missing: `ohlcv`, `news`, `fundamentals`, `options`, `dividends`, `splits`, `earnings`, `insider_transactions`, `institutional_holdings`, `ETF holdings`, `economic_calendar`
- **Database Storage Schema**: No tables for persisting fetched market data (OHLCV bars, fundamentals, etc.)
- **Provider Capability Registry**: No machine-readable mapping of "which provider supports which data types"

---

## Prompt 1: Gemini Deep Research

> **Target**: Google Gemini with Deep Research mode
> **Strength**: Broad web search + structured synthesis across many sources

```
RESEARCH TASK: Comprehensive API Endpoint Mapping for 12 Financial Data Providers

I'm building a trading portfolio analysis platform (Python backend, SQLite database) that aggregates market data from 12 API providers. I need you to research each provider's REST API documentation and produce a structured capability matrix.

## Providers to Research

1. API Ninjas (api.api-ninjas.com/v1)
2. Alpaca (api.alpaca.markets — Market Data API, NOT trading API)
3. Alpha Vantage (alphavantage.co/query)
4. Benzinga (api.benzinga.com/api/v2)
5. EODHD (eodhd.com/api)
6. Financial Modeling Prep (financialmodelingprep.com/api/v3)
7. Finnhub (finnhub.io/api/v1)
8. Nasdaq Data Link (data.nasdaq.com/api/v3)
9. OpenFIGI (api.openfigi.com/v3)
10. Polygon.io (api.polygon.io/v2)
11. SEC API (api.sec-api.io)
12. Tradier (api.tradier.com/v1)

## For EACH Provider, Research and Document:

### A. Most Popular/Useful Endpoints (Top 5-10 per provider)
For each endpoint, provide:
- **HTTP Method** (GET/POST)
- **URL Path** (relative to base URL)
- **Key Query Parameters** (with required vs optional)
- **Authentication placement** (which header or query param)
- **Response JSON structure** (top-level keys, envelope pattern like `{"results": [...]}` or `{"data": {...}}`)
- **Rate limit** (requests per minute on free tier)
- **Example response snippet** (abbreviated)

### B. Data Types Supported
Classify each provider's endpoints into these categories:
- `quote` — Real-time or delayed stock quotes
- `ohlcv` — Historical OHLCV price bars (daily/weekly/monthly)
- `news` — Financial news articles
- `fundamentals` — Income statement, balance sheet, cash flow, financial ratios
- `options` — Options chain, Greeks, unusual activity
- `dividends` — Dividend history and calendar
- `splits` — Stock split history
- `earnings` — Earnings calendar, estimates, surprises
- `insider_transactions` — SEC Form 4 insider trades
- `institutional_holdings` — 13F institutional ownership
- `etf_holdings` — ETF constituent holdings
- `economic_calendar` — GDP, CPI, Fed funds rate, employment data
- `sec_filings` — SEC EDGAR filings (10-K, 10-Q, 8-K)
- `ticker_search` — Symbol/company name search
- `company_profile` — Company info, sector, industry, market cap
- `identifier_mapping` — CUSIP/ISIN/SEDOL/FIGI cross-reference

### C. Response Normalization Notes
For each provider, note:
- How is the response envelope structured? (e.g., Alpha Vantage uses `"Global Quote": {"01. symbol": ...}`)
- Are field names human-readable or coded? (e.g., Polygon uses single-letter abbreviations: o, h, l, c, v)
- Timestamp format (Unix epoch? ISO 8601? Custom?)
- Pagination mechanism (offset/limit? cursor? next_url?)

### D. Provider Capability Matrix
Create a matrix table:

| Provider | quote | ohlcv | news | fundamentals | options | dividends | splits | earnings | insider | institutional | etf | econ_cal | sec_filings | ticker_search | company_profile | id_mapping |
|----------|-------|-------|------|-------------|---------|-----------|--------|----------|---------|--------------|-----|----------|-------------|---------------|----------------|------------|
| (each)   | ✅/❌  | ...   | ...  | ...         | ...     | ...       | ...    | ...      | ...     | ...          | ... | ...      | ...         | ...           | ...            | ...        |

### E. Scheduling Policy Patterns
For a cron-based scheduling engine, recommend the top 3 most valuable automated data-pull patterns per provider. Example:
- "Nightly OHLCV refresh for watchlist tickers" → `Alpha Vantage /query?function=TIME_SERIES_DAILY`
- "Weekly fundamental snapshot" → `FMP /income-statement/{symbol}?period=annual`

### F. Free Tier Limits Summary
For each provider, document:
- API calls per day/minute on free plan
- Data delay (real-time vs 15-min vs end-of-day)
- Historical data depth (how far back?)
- Any endpoint restrictions on free tier

Focus ONLY on REST API endpoints. Do NOT include WebSocket/streaming, Python SDK wrappers, or GraphQL. I need raw HTTP endpoint details for building URL builders and response parsers.
```

---

## Prompt 2: ChatGPT Deep Research

> **Target**: OpenAI ChatGPT with Deep Research / o3 reasoning
> **Strength**: Deep reasoning about endpoint design patterns + URL construction logic

```
DEEP RESEARCH REQUEST: REST API Endpoint Architecture for 12 Financial Data Providers

## Context
I'm extending a Python trading platform that currently has basic authentication working for 12 market data providers. The system uses:
- A **URL builder pattern** where each provider has a class that constructs endpoint URLs from (base_url, data_type, tickers[], criteria{})
- A **response extractor pattern** that unwraps provider-specific JSON envelopes into flat record lists
- A **field mapping registry** that translates provider-specific field names to canonical names (e.g., Polygon's "o" → "open", "c" → "close")
- A **scheduling engine** that runs data-pull pipelines on cron schedules

I need DETAILED endpoint analysis to build URL builders, response extractors, and field mappings for each provider.

## Providers
1. API Ninjas — api.api-ninjas.com/v1
2. Alpaca — data.alpaca.markets/v2 (Market Data API, paper+live)
3. Alpha Vantage — alphavantage.co/query (function-based dispatch)
4. Benzinga — api.benzinga.com/api/v2
5. EODHD — eodhd.com/api
6. Financial Modeling Prep — financialmodelingprep.com/api/v3
7. Finnhub — finnhub.io/api/v1
8. Nasdaq Data Link — data.nasdaq.com/api/v3
9. OpenFIGI — api.openfigi.com/v3 (POST-based mapping)
10. Polygon.io — api.polygon.io (v2 and v3)
11. SEC API — api.sec-api.io
12. Tradier — api.tradier.com/v1

## Research Deliverables (PER PROVIDER)

### 1. URL Construction Patterns
For each data_type (quote, ohlcv, news, fundamentals, options, dividends, splits, earnings, insider, institutional, company_profile, ticker_search), provide:

```
data_type: "ohlcv"
method: GET
path_template: "/stock/candle"
query_params:
  required: {symbol: "AAPL", resolution: "D", from: 1609459200, to: 1640995200}
  optional: {}
auth_placement: "header:X-Finnhub-Token"
example_url: "https://finnhub.io/api/v1/stock/candle?symbol=AAPL&resolution=D&from=1609459200&to=1640995200"
```

### 2. Response Envelope Extraction
For each endpoint, document the JSON path to the actual records:
```
provider: "Alpha Vantage"
data_type: "ohlcv"
function: "TIME_SERIES_DAILY"
envelope_path: "Time Series (Daily)"  # dict of date→OHLCV
record_type: "dict_of_dicts"  # vs "array" vs "nested_array"
example_keys: ["1. open", "2. high", "3. low", "4. close", "5. volume"]
```

### 3. Field Name Mapping Table
For each provider and data_type, create a source→canonical mapping:
```
provider: "EODHD"
data_type: "ohlcv"
mappings:
  "open" → "open"
  "high" → "high"
  "low" → "low"
  "close" → "close"
  "adjusted_close" → "adj_close"
  "volume" → "volume"
  "date" → "timestamp"
```

### 4. Pagination & Batching
- How does pagination work? (offset/limit, cursor, page token, next_url?)
- Max results per request?
- Can multiple tickers be requested in one call, or is it per-ticker?
- For OHLCV: max date range per request?

### 5. Rate Limit Architecture
- Free tier: calls/minute, calls/day
- How is rate limiting communicated? (HTTP 429? Response body error? X-RateLimit headers?)
- Recommended polling interval for real-time quotes

### 6. Data Type Availability Matrix
Create a provider × data_type matrix showing exact endpoint paths:

| Provider | quote | ohlcv | news | fundamentals | earnings | dividends | splits | options | insider | institutional | sec_filings | search | profile |
|----------|-------|-------|------|-------------|----------|-----------|--------|---------|---------|--------------|-------------|--------|---------|
| API Ninjas | /stockprice | — | — | — | — | — | — | — | — | — | — | — | — |
| Alpha Vantage | /query?fn=GLOBAL_QUOTE | /query?fn=TIME_SERIES_DAILY | /query?fn=NEWS_SENTIMENT | /query?fn=INCOME_STATEMENT | ... | ... | ... | ... | ... | ... | ... | /query?fn=SYMBOL_SEARCH | /query?fn=OVERVIEW |
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |

### 7. Implementation Priority Ranking
Rank the endpoints by value for a retail trader portfolio analysis tool:
1. Which endpoints should we wire FIRST for maximum utility?
2. Which providers are the BEST source for each data_type? (considering accuracy, coverage, freshness, free-tier limits)
3. Which endpoints are UNIQUE to specific providers? (e.g., only Benzinga has real-time news sentiment)

### CRITICAL: Verify All Endpoints Against Current API Documentation
Several providers have deprecated endpoints or changed API versions in 2024-2026:
- Alpha Vantage deprecated several premium functions
- Yahoo Finance v6/finance/quote returns 404 since ~2024
- Polygon moved some v2 endpoints to v3
- Alpaca has separate base URLs for market data vs trading

Verify each endpoint URL is CURRENT and functional. Flag any deprecated or sunset endpoints.
```

---

## Prompt 3: Claude Deep Research

> **Target**: Anthropic Claude with Extended Thinking + Web Search
> **Strength**: Systematic analysis, code-level implementation detail, edge case identification

```
RESEARCH & ANALYSIS: Building a Complete Market Data Aggregation Layer

## System Architecture Context

I have a Python trading analytics platform with this existing infrastructure:

### Provider Registry (14 providers, auth working)
```python
# Each provider has: name, base_url, auth_method, auth_param_name, headers_template, test_endpoint, default_rate_limit
# Auth methods: QUERY_PARAM, BEARER_HEADER, CUSTOM_HEADER, RAW_HEADER, NONE
# Example:
ProviderConfig(
    name="Finnhub",
    base_url="https://finnhub.io/api/v1",
    auth_method=AuthMethod.CUSTOM_HEADER,
    auth_param_name="X-Finnhub-Token",
    headers_template={"X-Finnhub-Token": "{api_key}"},
    test_endpoint="/quote?symbol=AAPL&token={api_key}",
    default_rate_limit=60,
)
```

### URL Builder Pattern (only 3 providers have dedicated builders)
```python
class UrlBuilder(Protocol):
    def build_url(self, base_url: str, data_type: str, tickers: list[str], criteria: dict[str, Any]) -> str: ...

# Currently implemented: YahooUrlBuilder, PolygonUrlBuilder, FinnhubUrlBuilder
# Missing: All 12 API-key providers need dedicated URL builders
```

### Response Extractor Pattern (only Yahoo + Polygon implemented)
```python
def extract_records(raw: bytes, provider: str, data_type: str) -> list[dict]:
    # Registered extractors: yahoo/quote, yahoo/news, polygon/ohlcv, polygon/quote, polygon/news
    # Missing: ALL other providers need extractors
```

### Field Mapping Registry (sparse coverage)
```python
FIELD_MAPPINGS: dict[tuple[str, str], dict[str, str]] = {
    ("yahoo", "quote"): {"regularMarketPrice": "last", "regularMarketVolume": "volume", ...},
    ("polygon", "ohlcv"): {"o": "open", "h": "high", "l": "low", "c": "close", "v": "volume", ...},
    # Missing: Most provider+data_type combinations
}
```

### Scheduling Pipeline (fully working)
- FetchStep → TransformStep → LoadStep → NotifyStep
- FetchStep calls MarketDataProviderAdapter.fetch(provider, data_type, criteria)
- TransformStep calls extract_records() then apply_field_mapping()
- LoadStep writes to SQLite via UPSERT

## Research Task

For EACH of these 12 API-key providers, I need you to research their current REST API and produce implementation-ready specifications:

### Providers
1. **API Ninjas** — api.api-ninjas.com/v1
2. **Alpaca** — data.alpaca.markets/v2 (Alpaca Market Data API, NOT the trading API at api.alpaca.markets)
3. **Alpha Vantage** — alphavantage.co/query
4. **Benzinga** — api.benzinga.com/api/v2
5. **EODHD** — eodhd.com/api
6. **Financial Modeling Prep** — financialmodelingprep.com/api/v3
7. **Finnhub** — finnhub.io/api/v1
8. **Nasdaq Data Link** — data.nasdaq.com/api/v3
9. **OpenFIGI** — api.openfigi.com/v3
10. **Polygon.io** — api.polygon.io/v2 and /v3
11. **SEC API** — api.sec-api.io
12. **Tradier** — api.tradier.com/v1

### Deliverable 1: Provider Capability Matrix

For each provider, classify which of these data_types they support, with the EXACT endpoint path:

| data_type | Description | Which providers support it? |
|-----------|-------------|---------------------------|
| quote | Real-time/delayed price | |
| ohlcv | Historical daily OHLCV bars | |
| news | Financial news articles | |
| fundamentals | Income stmt, balance sheet, ratios | |
| earnings | EPS estimates, actuals, calendar | |
| dividends | Historical + upcoming dividends | |
| splits | Stock split history | |
| options | Options chains, Greeks | |
| insider | SEC Form 4 insider transactions | |
| institutional | 13F institutional holdings | |
| etf_holdings | ETF constituent weights | |
| economic_calendar | Macro economic events | |
| sec_filings | SEC EDGAR filings | |
| ticker_search | Symbol/name lookup | |
| company_profile | Company info, sector, market cap | |
| identifier_mapping | CUSIP/ISIN/FIGI cross-ref | |

### Deliverable 2: URL Builder Specification (per provider)

For each supported data_type, produce a URL construction spec:

```yaml
provider: "Alpha Vantage"
data_types:
  quote:
    method: GET
    url_template: "{base_url}?function=GLOBAL_QUOTE&symbol={ticker}&apikey={api_key}"
    supports_multi_ticker: false
    pagination: none
    notes: "Returns {'Global Quote': {'01. symbol': ..., '05. price': ...}}"
  ohlcv:
    method: GET
    url_template: "{base_url}?function=TIME_SERIES_DAILY_ADJUSTED&symbol={ticker}&outputsize={outputsize}&apikey={api_key}"
    supports_multi_ticker: false
    pagination: none
    params:
      outputsize: "compact (100 days) or full (20+ years)"
    notes: "Returns {'Time Series (Daily)': {'2024-01-02': {'1. open': '...', ...}}}"
  news:
    method: GET
    url_template: "{base_url}?function=NEWS_SENTIMENT&tickers={ticker}&limit={count}&apikey={api_key}"
    supports_multi_ticker: true (comma-separated)
    pagination: none
    notes: "Returns {'feed': [{...}, ...]}"
```

### Deliverable 3: Response Extraction Specification

For each provider+data_type, document the JSON envelope unwrapping:

```yaml
provider: "Finnhub"
extractors:
  quote:
    envelope: "top-level dict (no wrapper)"
    path_to_records: "." # record IS the top-level dict
    record_type: "single_dict"  # wrap in list
    example: {"c": 150.5, "d": -1.2, "dp": -0.79, "h": 152.0, "l": 149.8, "o": 151.0, "pc": 151.7, "t": 1609459200}
  ohlcv:
    envelope: "top-level dict with parallel arrays"
    path_to_records: "zip(c, h, l, o, v, t)"  # Must zip arrays into records
    record_type: "parallel_arrays"
    example: {"c": [150.5, 151.2], "h": [152.0, 153.1], "l": [...], "o": [...], "v": [...], "t": [...], "s": "ok"}
    notes: "Finnhub candles return parallel arrays, NOT an array of records. Must zip c/h/l/o/v/t into [{c:150.5, h:152, ...}, ...]"
```

### Deliverable 4: Field Mapping Tables

For each provider+data_type, create the source→canonical mapping:

```yaml
provider: "EODHD"
field_mappings:
  ohlcv:
    "date": "timestamp"
    "open": "open"
    "high": "high"
    "low": "low"
    "close": "close"
    "adjusted_close": "adj_close"
    "volume": "volume"
  quote:
    "code": "ticker"
    "close": "last"
    "previousClose": "prev_close"
    "change": "change"
    "change_p": "change_pct"
    "volume": "volume"
    "timestamp": "timestamp"
```

### Deliverable 5: Database Schema for Market Data Storage

Based on the data types supported across providers, propose SQLite table schemas for storing:
1. OHLCV price bars (daily)
2. Company fundamentals snapshots
3. Earnings data
4. Dividend/split events
5. News articles (deduplicated across providers)
6. Economic calendar events

Consider: UPSERT keys, indexes for query performance, foreign keys to existing `trade_executions` table.

### Deliverable 6: Top 10 Scheduling Recipes

Propose the 10 most valuable automated data-pull pipeline configurations for a retail trader:

```yaml
- name: "Nightly Watchlist OHLCV Refresh"
  cron: "0 19 * * 1-5"  # 7PM ET, weekdays
  provider: "Polygon.io"
  data_type: "ohlcv"
  tickers: "{{watchlist}}"  # Dynamic from watchlist table
  retention: "rolling_2_years"
  fallback_provider: "Alpha Vantage"

- name: "Weekly Fundamental Snapshot"
  ...
```

### Deliverable 7: Edge Cases & Gotchas

Flag any known issues:
- Endpoints that return different structures on free vs premium tiers
- Providers with aggressive rate limiting or IP blocking
- Date format inconsistencies (some use YYYY-MM-DD, others use Unix timestamps)
- Providers that require special headers beyond authentication
- POST vs GET anomalies (e.g., OpenFIGI uses POST for lookups)
- Providers that changed API versions or deprecated endpoints in 2024-2026
- Endpoints that behave differently for ETFs vs stocks vs crypto
- Any providers that require OAuth2 instead of simple API keys
```

---

## Usage Instructions

1. **Gemini**: Use Deep Research mode. The broad search capability will map the widest range of endpoints across all 12 providers simultaneously.

2. **ChatGPT**: Use Deep Research (o3-powered). The reasoning focus will produce the most precise URL construction patterns and identify deprecated endpoints.

3. **Claude**: Use Extended Thinking with web search enabled. The systematic approach will produce the most implementation-ready specs with edge case analysis.

### Post-Research Integration Plan

After collecting all three research outputs:

1. **Merge capability matrices** — cross-reference to catch any endpoints one model missed
2. **Build URL builders** — one `XxxUrlBuilder` class per provider in `url_builders.py`
3. **Build response extractors** — register `(provider, data_type)` pairs in `response_extractors.py`
4. **Build field mappings** — add to `FIELD_MAPPINGS` dict in `field_mappings.py`
5. **Create provider capability registry** — machine-readable `PROVIDER_CAPABILITIES` dict for agentic policy construction
6. **Design database tables** — SQLAlchemy models for persisted market data
7. **Wire scheduling recipes** — default policy templates for common data-pull patterns

### Files to Modify After Research

| File | Change |
|------|--------|
| `infrastructure/market_data/url_builders.py` | Add 9 new `XxxUrlBuilder` classes |
| `infrastructure/market_data/response_extractors.py` | Add extractors for each provider+data_type |
| `infrastructure/market_data/field_mappings.py` | Add mappings for all provider+data_type combos |
| `infrastructure/market_data/provider_registry.py` | Add `capabilities: list[str]` to `ProviderConfig` |
| `core/services/market_data_service.py` | Extend `_fetch_*_data()` methods for new data types |
| `infrastructure/database/models.py` | Add OHLCV, fundamentals, earnings, news tables |
| `api/routes/market_data.py` | Add new endpoints: `/ohlcv`, `/fundamentals`, `/earnings` |
| `api/routes/scheduling.py` | Add `provider_capabilities` endpoint |
