# Unified Market Data Ingestion Layer — Implementation-Ready Spec for 12 Providers

## TL;DR
- **Free-tier reality**: Only Alpaca (200 req/min) and Finnhub (60 req/min) offer genuinely usable free tiers for active development; Alpha Vantage (25/day), Polygon (5/min), EODHD (20/day), and FMP (250/day) hit limits within minutes. **Finnhub `/stock/candle` returns 403 on free accounts since 2024** — use Alpaca, Polygon `/v2/aggs`, or EODHD for OHLCV instead.
- **Pattern variations**: Auth uses 5 mechanisms (BEARER for Alpaca/Tradier/SEC-API, QUERY_PARAM for AlphaVantage/Polygon/Finnhub/Benzinga/EODHD/FMP/Nasdaq, CUSTOM_HEADER X-Api-Key for API-Ninjas, X-OPENFIGI-APIKEY, X-Finnhub-Token alt). **OpenFIGI and SEC-API require POST with JSON body**; everything else is GET. **Finnhub candles return parallel arrays** (`{c:[],h:[],l:[],o:[],t:[],v:[]}`) requiring `zip()`; **Alpha Vantage uses date-keyed dicts** requiring `.items()` iteration.
- **Coverage gaps**: API-Ninjas, OpenFIGI, and Nasdaq Data Link cover narrow slices (utility/identifier/macro). For broad needs combine **Alpaca (OHLCV/quotes) + Finnhub (news/profile/earnings) + FMP (fundamentals) + Polygon (dividends/splits) + Benzinga (calendars, premium) + SEC-API (filings, paid)**.

---

## DELIVERABLE 1 — Provider Capability Matrix

Legend: ✅ free tier, 💰 premium-only, ⚠️ partial/quirky, ❌ not supported.

| data_type | API-Ninjas | Alpaca | AlphaVantage | Benzinga | EODHD | FMP | Finnhub | Nasdaq DL | OpenFIGI | Polygon | SEC-API | Tradier |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| quote | ✅ | ✅ | ✅ | 💰 | ⚠️ | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ |
| ohlcv | ✅ | ✅ | ✅ | 💰 | ✅ | ✅ | 💰 | ⚠️ | ❌ | ✅ | ✅ |
| news | ❌ | ✅ | ✅ | 💰 | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ |
| fundamentals | ⚠️ | ❌ | ✅ | 💰 | ✅ | ✅ | ⚠️ | ❌ | ❌ | ⚠️ | ⚠️beta | ❌ |
| earnings | ✅ | ❌ | ✅ | 💰 | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| dividends | ❌ | ❌ | ⚠️emb | 💰 | ✅ | ✅ | 💰 | ❌ | ❌ | ✅ | ❌ |
| splits | ❌ | ❌ | ⚠️emb | 💰 | ✅ | ✅ | 💰 | ❌ | ❌ | ✅ | ❌ |
| options | ❌ | 💰 | 💰 | 💰 | 💰 | 💰 | 💰 | ❌ | ❌ | 💰 | ❌ | ✅ |
| insider | ❌ | ❌ | ✅ | 💰 | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ |
| institutional | ❌ | ❌ | ✅ | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ |
| etf_holdings | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | 💰 | ❌ | ❌ | ❌ | ❌ | ❌ |
| economic_calendar | ✅ | ❌ | ✅ | 💰 | ✅ | ✅ | ✅ | ⚠️ | ❌ | ⚠️ | ❌ | ❌ |
| sec_filings | ✅ | ❌ | ❌ | 💰 | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ |
| ticker_search | ✅ | ❌ | ✅ | ❌ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ | ✅ |
| company_profile | ⚠️ | ❌ | ✅ | 💰 | ✅ | ✅ | ✅ | ❌ | ⚠️ | ✅ | ⚠️ | ❌ |
| identifier_mapping | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ⚠️ | ❌ | ✅ | ⚠️cusip | ❌ | ❌ |

"emb" = embedded inside TIME_SERIES_DAILY_ADJUSTED for AV.

---

## DELIVERABLE 2 — URL Builder Specifications (YAML-style)

### 1. API Ninjas — `https://api.api-ninjas.com/v1`
Auth: CUSTOM_HEADER `X-Api-Key: {api_key}`. Free: 50,000 calls/month basic.
```yaml
quote:
  method: GET
  url: "{base_url}/stockprice?ticker={ticker}"
  multi_ticker: false  # single only, loop for batches
  pagination: none
ohlcv:
  method: GET
  url: "{base_url}/stockpricehistorical?ticker={ticker}&interval=1d&start={start_unix}&end={end_unix}"
  multi_ticker: false
  pagination: none  # max 100 points per call
  notes: "interval ∈ {1m,5m,15m,30m,1h,4h,1d}; start/end are UNIX seconds"
earnings:
  method: GET
  url: "{base_url}/earnings?ticker={ticker}&year={year}&period={q1|q2|q3|q4|fy}"
  notes: "Pre-2025 history requires premium"
economic_calendar:
  method: GET
  url: "{base_url}/inflation?country={country}"  # also /unemployment, /commodityprice
ticker_search:
  method: GET
  url: "{base_url}/stocksymbol?company={query}"
sec_filings:
  method: GET
  url: "{base_url}/secfiling?ticker={ticker}&form_type={10-K|10-Q|8-K}"
company_profile:
  method: GET
  url: "{base_url}/stocksymbol?ticker={ticker}"
```

### 2. Alpaca Market Data v2 — `https://data.alpaca.markets/v2`
Auth: dual headers `APCA-API-KEY-ID` + `APCA-API-SECRET-KEY` (RAW_HEADER). Free: 200 req/min, IEX feed only, 15-min delay on SIP.
```yaml
ohlcv:
  method: GET
  url: "{base_url}/stocks/bars?symbols={tickers_csv}&timeframe={1Day|1Hour|5Min|1Min}&start={iso8601}&end={iso8601}&limit=10000&adjustment=split&feed=iex"
  multi_ticker: true  # comma-separated symbols
  pagination: cursor  # next_page_token
  notes: "RFC-3339 dates required, no fractional seconds; default feed=iex on free"
quote:
  method: GET
  url: "{base_url}/stocks/quotes/latest?symbols={tickers_csv}&feed=iex"
  multi_ticker: true
  pagination: none
news:
  method: GET
  url: "{base_url}/news?symbols={tickers_csv}&start={iso}&end={iso}&limit=50"
  pagination: cursor  # next_page_token
  notes: "Hosted on data.alpaca.markets/v1beta1/news (NOT v2)"
```

### 3. Alpha Vantage — `https://www.alphavantage.co/query`
Auth: QUERY_PARAM `apikey={api_key}`. Free: **25 req/day**, 5/min.
```yaml
ohlcv:
  method: GET
  url: "{base_url}?function=TIME_SERIES_DAILY_ADJUSTED&symbol={ticker}&outputsize={compact|full}&datatype=json&apikey={api_key}"
  multi_ticker: false
  pagination: none
quote:
  method: GET
  url: "{base_url}?function=GLOBAL_QUOTE&symbol={ticker}&apikey={api_key}"
news:
  method: GET
  url: "{base_url}?function=NEWS_SENTIMENT&tickers={tickers_csv}&time_from={YYYYMMDDTHHMM}&limit=50&apikey={api_key}"
fundamentals:
  method: GET
  url: "{base_url}?function=OVERVIEW&symbol={ticker}&apikey={api_key}"
earnings:
  method: GET
  url: "{base_url}?function=EARNINGS&symbol={ticker}&apikey={api_key}"
insider:
  method: GET
  url: "{base_url}?function=INSIDER_TRANSACTIONS&symbol={ticker}&apikey={api_key}"
institutional:
  method: GET
  url: "{base_url}?function=INSTITUTIONAL_HOLDINGS&symbol={ticker}&apikey={api_key}"
economic_calendar:
  method: GET
  url: "{base_url}?function=EARNINGS_CALENDAR&horizon={3month|6month|12month}&apikey={api_key}"
  notes: "Returns CSV, not JSON, even with datatype=json"
ticker_search:
  method: GET
  url: "{base_url}?function=SYMBOL_SEARCH&keywords={query}&apikey={api_key}"
```

### 4. Benzinga — `https://api.benzinga.com/api/v2`
Auth: QUERY_PARAM `token={api_key}`. **Mostly premium**, contact licensing@benzinga.com. Recommend `parameters[updated]` for delta polling.
```yaml
news:
  method: GET
  url: "{base_url}/news?token={api_key}&tickers={tickers_csv}&pageSize=100&displayOutput=full&updatedSince={unix}"
  multi_ticker: true
  pagination: page  # ?page=N, max 10000 results total
earnings:
  method: GET
  url: "{base_url}/calendar/earnings?token={api_key}&parameters[tickers]={tickers_csv}&parameters[date_from]={YYYY-MM-DD}&parameters[date_to]={YYYY-MM-DD}"
dividends:
  method: GET
  url: "{base_url}/calendar/dividends?token={api_key}&parameters[tickers]={tickers_csv}"
splits:
  method: GET
  url: "{base_url}/calendar/splits?token={api_key}&parameters[tickers]={tickers_csv}"
economic_calendar:
  method: GET
  url: "{base_url}/calendar/economics?token={api_key}&parameters[date_from]={YYYY-MM-DD}"
insider:
  method: GET
  url: "{base_url}/insider/transactions?token={api_key}&parameters[tickers]={tickers_csv}"
sec_filings:
  method: GET
  url: "{base_url}/sec/filings?token={api_key}&parameters[tickers]={tickers_csv}"
fundamentals:
  method: GET
  url: "{base_url}/fundamentals?token={api_key}&symbols={tickers_csv}"
```
Headers: `Accept: application/json` required.

### 5. EODHD — `https://eodhd.com/api`
Auth: QUERY_PARAM `api_token={api_key}`. Free: **20 calls/day, US only, 1yr history**. DEMO key works for AAPL.US/TSLA.US/MSFT.US/AMZN.US/VTI.US/BTC-USD.CC/EURUSD.FOREX.
```yaml
ohlcv:
  method: GET
  url: "{base_url}/eod/{ticker}.{exchange}?api_token={api_key}&from={YYYY-MM-DD}&to={YYYY-MM-DD}&period={d|w|m}&fmt=json"
  multi_ticker: false  # use bulk endpoint for whole exchange
  pagination: none
ohlcv_bulk:
  method: GET
  url: "{base_url}/eod-bulk-last-day/{exchange}?api_token={api_key}&symbols={tickers_csv}&fmt=json"
quote:
  method: GET
  url: "{base_url}/real-time/{ticker}.{exchange}?api_token={api_key}&fmt=json&s={extra_tickers_csv}"
  multi_ticker: true  # via &s= param
fundamentals:
  method: GET
  url: "{base_url}/fundamentals/{ticker}.{exchange}?api_token={api_key}"
dividends:
  method: GET
  url: "{base_url}/div/{ticker}.{exchange}?api_token={api_key}&from={date}&to={date}&fmt=json"
splits:
  method: GET
  url: "{base_url}/splits/{ticker}.{exchange}?api_token={api_key}&fmt=json"
news:
  method: GET
  url: "{base_url}/news?api_token={api_key}&s={ticker}.{exchange}&from={date}&to={date}&limit=50&fmt=json"
earnings:
  method: GET
  url: "{base_url}/calendar/earnings?api_token={api_key}&from={date}&to={date}&symbols={tickers_csv}&fmt=json"
ticker_search:
  method: GET
  url: "{base_url}/search/{query}?api_token={api_key}&fmt=json"
identifier_mapping:
  method: GET
  url: "{base_url}/id-map?api_token={api_key}&type={cusip|isin|figi|cik}&value={id}&fmt=json"
```

### 6. Financial Modeling Prep — `https://financialmodelingprep.com/api/v3` (+ `/v4`, new `/stable`)
Auth: QUERY_PARAM `apikey={api_key}`. Free: **250 req/day, US only**.
```yaml
quote:
  method: GET
  url: "{base_url}/quote/{tickers_csv}?apikey={api_key}"  # v3
  multi_ticker: true  # comma-separated path segment
ohlcv:
  method: GET
  url: "{base_url}/historical-price-full/{ticker}?from={date}&to={date}&apikey={api_key}"
  multi_ticker: true  # accepts comma-separated /AAPL,MSFT but flatter response when single
fundamentals:
  method: GET
  url: "{base_url}/profile/{ticker}?apikey={api_key}"
  related:
    income:    "{base_url}/income-statement/{ticker}?period=quarter&limit=40&apikey={api_key}"
    balance:   "{base_url}/balance-sheet-statement/{ticker}?period=quarter&apikey={api_key}"
    cashflow:  "{base_url}/cash-flow-statement/{ticker}?period=quarter&apikey={api_key}"
    ratios:    "{base_url}/ratios-ttm/{ticker}?apikey={api_key}"
earnings:
  method: GET
  url: "{base_url}/historical/earning_calendar/{ticker}?apikey={api_key}"
  calendar: "{base_url}/earning_calendar?from={date}&to={date}&apikey={api_key}"
dividends:
  method: GET
  url: "{base_url}/historical-price-full/stock_dividend/{ticker}?apikey={api_key}"
  calendar: "{base_url}/stock_dividend_calendar?from={date}&to={date}&apikey={api_key}"
splits:
  method: GET
  url: "{base_url}/historical-price-full/stock_split/{ticker}?apikey={api_key}"
news:
  method: GET
  url: "{base_url}/stock_news?tickers={tickers_csv}&limit=50&apikey={api_key}"
insider:
  method: GET  # v4
  url: "https://financialmodelingprep.com/api/v4/insider-trading?symbol={ticker}&apikey={api_key}"
institutional:
  method: GET
  url: "{base_url}/institutional-holder/{ticker}?apikey={api_key}"
etf_holdings:
  method: GET  # v4
  url: "https://financialmodelingprep.com/api/v4/etf-holdings?symbol={ticker}&apikey={api_key}"
sec_filings:
  method: GET
  url: "{base_url}/sec_filings/{ticker}?type=10-K&limit=100&apikey={api_key}"
economic_calendar:
  method: GET
  url: "{base_url}/economic_calendar?from={date}&to={date}&apikey={api_key}"
ticker_search:
  method: GET
  url: "{base_url}/search?query={q}&limit=10&exchange=NASDAQ&apikey={api_key}"
```
Note: FMP is migrating from `/api/v3/` to `/stable/` paths in 2024-2025; both currently work.

### 7. Finnhub — `https://finnhub.io/api/v1`
Auth: QUERY_PARAM `token={api_key}` OR HEADER `X-Finnhub-Token`. Free: **60 req/min**.
```yaml
quote:
  method: GET
  url: "{base_url}/quote?symbol={ticker}&token={api_key}"
  multi_ticker: false
ohlcv:
  method: GET
  url: "{base_url}/stock/candle?symbol={ticker}&resolution={1|5|15|30|60|D|W|M}&from={unix}&to={unix}&token={api_key}"
  notes: "⚠️ PREMIUM-ONLY since 2024 — returns 403 on free. Use Alpaca/EODHD instead."
news:
  method: GET
  url: "{base_url}/company-news?symbol={ticker}&from={YYYY-MM-DD}&to={YYYY-MM-DD}&token={api_key}"
  multi_ticker: false
news_general:
  method: GET
  url: "{base_url}/news?category={general|forex|crypto|merger}&token={api_key}"
company_profile:
  method: GET
  url: "{base_url}/stock/profile2?symbol={ticker}&token={api_key}"
fundamentals:
  method: GET
  url: "{base_url}/stock/metric?symbol={ticker}&metric=all&token={api_key}"
earnings:
  method: GET
  url: "{base_url}/stock/earnings?symbol={ticker}&token={api_key}"
  calendar: "{base_url}/calendar/earnings?from={date}&to={date}&symbol={ticker}&token={api_key}"
economic_calendar:
  method: GET
  url: "{base_url}/calendar/economic?from={date}&to={date}&token={api_key}"
insider:
  method: GET
  url: "{base_url}/stock/insider-transactions?symbol={ticker}&from={date}&to={date}&token={api_key}"
institutional:
  method: GET
  url: "{base_url}/stock/ownership?symbol={ticker}&limit=20&token={api_key}"
sec_filings:
  method: GET
  url: "{base_url}/stock/filings?symbol={ticker}&from={date}&to={date}&token={api_key}"
ticker_search:
  method: GET
  url: "{base_url}/search?q={query}&token={api_key}"
dividends:
  method: GET
  url: "{base_url}/stock/dividend?symbol={ticker}&from={date}&to={date}&token={api_key}"
  notes: "Premium"
```

### 8. Nasdaq Data Link — `https://data.nasdaq.com/api/v3`
Auth: QUERY_PARAM `api_key={api_key}`. Free: most retail datasets discontinued; **WIKI/EOD shut down**. Free retains FRED, USTREASURY, OPEC, LBMA, etc.
```yaml
ohlcv_timeseries:  # legacy time-series API
  method: GET
  url: "{base_url}/datasets/{database_code}/{dataset_code}.json?api_key={api_key}&start_date={date}&end_date={date}&order={asc|desc}&collapse={daily|weekly|monthly}"
  example: "/datasets/FRED/GDP.json", "/datasets/USTREASURY/YIELD.json"
  multi_ticker: false  # one dataset per call
  pagination: none  # but limit param caps rows
tables:  # for premium "datatables" (e.g., SHARADAR/SEP)
  method: GET
  url: "{base_url}/datatables/{vendor}/{table}.json?api_key={api_key}&qopts.per_page=10000&date.gte={date}&ticker={ticker}"
  pagination: cursor  # qopts.cursor_id from response
metadata:
  method: GET
  url: "{base_url}/databases/{db}.json?api_key={api_key}"
```
Note: legacy `quandl` URL `https://www.quandl.com/api/v3/` redirects.

### 9. OpenFIGI — `https://api.openfigi.com/v3`
Auth: HEADER `X-OPENFIGI-APIKEY: {api_key}` (optional but raises rate limits). **POST with JSON body**.
```yaml
identifier_mapping:
  method: POST
  url: "{base_url}/mapping"
  headers:
    Content-Type: application/json
    X-OPENFIGI-APIKEY: "{api_key}"
  body: |
    [{"idType":"TICKER","idValue":"IBM","exchCode":"US"},
     {"idType":"ID_ISIN","idValue":"US0378331005"}]
  multi_ticker: true  # array of jobs in body, max 100 unauth / 100 auth per request
  pagination: none
ticker_search:
  method: POST
  url: "{base_url}/search"
  body: |
    {"query":"APPLE","exchCode":"US","start":"{cursor}"}
  pagination: cursor  # response.next is start for next call
filter:
  method: POST
  url: "{base_url}/filter"
mapping_values:
  method: GET
  url: "{base_url}/mapping/values/{key}"  # e.g., /idType, /exchCode
```
**v2 sunset July 1, 2026 → returns 410 Gone**. Migrate to v3; `error` key renamed to `warning` for "No identifier found".

### 10. Polygon.io — `https://api.polygon.io` (mixed v1/v2/v3)
Auth: QUERY_PARAM `apiKey={api_key}` OR `Authorization: Bearer {api_key}`. Free: **5 req/min, 2yr history, EOD only**.
```yaml
ohlcv:  # v2 still current for aggregates
  method: GET
  url: "{base_url}/v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{from_date}/{to_date}?adjusted=true&sort=asc&limit=50000&apiKey={api_key}"
  notes: "timespan: minute|hour|day|week|month; max 50000 rows; date format YYYY-MM-DD or millisec timestamp"
quote_snapshot:
  method: GET
  url: "{base_url}/v2/snapshot/locale/us/markets/stocks/tickers/{ticker}?apiKey={api_key}"
quote_last:
  method: GET
  url: "{base_url}/v2/last/trade/{ticker}?apiKey={api_key}"
ticker_search:
  method: GET
  url: "{base_url}/v3/reference/tickers?search={query}&active=true&limit=100&apiKey={api_key}"
  pagination: cursor  # follow next_url field
company_profile:
  method: GET
  url: "{base_url}/v3/reference/tickers/{ticker}?apiKey={api_key}"
news:
  method: GET
  url: "{base_url}/v2/reference/news?ticker={ticker}&published_utc.gte={date}&limit=1000&apiKey={api_key}"
  pagination: cursor  # next_url
dividends:
  method: GET
  url: "{base_url}/v3/reference/dividends?ticker={ticker}&limit=1000&apiKey={api_key}"
splits:
  method: GET
  url: "{base_url}/v3/reference/splits?ticker={ticker}&limit=1000&apiKey={api_key}"
fundamentals:
  method: GET
  url: "{base_url}/vX/reference/financials?ticker={ticker}&timeframe=quarterly&limit=100&apiKey={api_key}"
  notes: "vX is experimental but stable since 2022"
options_chain:
  method: GET
  url: "{base_url}/v3/snapshot/options/{underlying}?apiKey={api_key}"
  notes: "Premium"
options_contracts:
  method: GET
  url: "{base_url}/v3/reference/options/contracts?underlying_ticker={ticker}&apiKey={api_key}"
sec_filings:
  method: GET
  url: "{base_url}/v1/reference/sec/filings?ticker={ticker}&apiKey={api_key}"
economic_calendar_inflation:
  method: GET
  url: "{base_url}/fed/v1/inflation?apiKey={api_key}"
```

### 11. SEC API — `https://api.sec-api.io`
Auth: HEADER `Authorization: {api_key}` OR query `?token={api_key}`. **Mostly POST**, paid (free 100/month).
```yaml
sec_filings:
  method: POST
  url: "{base_url}"
  body: |
    {"query":"ticker:AAPL AND formType:\"10-K\"",
     "from":"0","size":"50",
     "sort":[{"filedAt":{"order":"desc"}}]}
  pagination: offset  # increment "from" by "size" each call, capped at 10000
insider:
  method: POST
  url: "{base_url}/insider-trading"
  body: |
    {"query":"issuer.tradingSymbol:TSLA","from":"0","size":"50"}
institutional:
  method: POST
  url: "{base_url}/form-13f"
  body: |
    {"query":"ticker:AAPL","from":"0","size":"50"}
sec_filings_fulltext:
  method: POST
  url: "{base_url}/full-text-search"
  body: |
    {"query":"\"substantial doubt\"","formTypes":["10-K"],"page":1}
fundamentals_xbrl:
  method: GET
  url: "{base_url}/xbrl-to-json?accession-no={accession}&token={api_key}"
extractor:
  method: GET
  url: "{base_url}/extractor?url={filing_url}&item=1A&type=text&token={api_key}"
```
Lucene query syntax; results capped at 10,000 docs/query — narrow with date or ticker filters.

### 12. Tradier — `https://api.tradier.com/v1` (sandbox: `https://sandbox.tradier.com/v1`)
Auth: HEADER `Authorization: Bearer {api_key}` + `Accept: application/json`. **Brokerage account required**; sandbox is delayed 15min.
```yaml
quote:
  method: GET
  url: "{base_url}/markets/quotes?symbols={tickers_csv}&greeks=false"
  multi_ticker: true
  also: POST {base_url}/markets/quotes  # body x-www-form-urlencoded for >100 symbols
ohlcv:
  method: GET
  url: "{base_url}/markets/history?symbol={ticker}&interval={daily|weekly|monthly}&start={YYYY-MM-DD}&end={YYYY-MM-DD}"
  multi_ticker: false
ohlcv_intraday:
  method: GET
  url: "{base_url}/markets/timesales?symbol={ticker}&interval={tick|1min|5min|15min}&start={YYYY-MM-DD HH:MM}&end={YYYY-MM-DD HH:MM}&session_filter=all"
options_chain:
  method: GET
  url: "{base_url}/markets/options/chains?symbol={ticker}&expiration={YYYY-MM-DD}&greeks=true"
options_expirations:
  method: GET
  url: "{base_url}/markets/options/expirations?symbol={ticker}&includeAllRoots=true&strikes=false"
ticker_search:
  method: GET
  url: "{base_url}/markets/search?q={query}&indexes=false"
fundamentals:
  method: GET
  url: "https://api.tradier.com/beta/markets/fundamentals/company?symbols={tickers_csv}"
  notes: "BETA, Brokerage-only, sources Morningstar"
calendar_clock:
  method: GET
  url: "{base_url}/markets/clock"  # market open/close status
```

---

## DELIVERABLE 3 — Response Extraction Specifications

### API Ninjas — flat list/dict
- **ohlcv**: top-level list of dicts `[{open, high, low, close, volume, timestamp},...]`. `path: $`, `record_type: list_of_dicts`.
- **quote** `/stockprice`: single dict `{ticker, name, price, exchange, updated}`. `record_type: single_dict`.
- **earnings** `/earnings`: list of `{ticker, fiscal_date_ending, period, revenue, net_income, eps_basic, eps_diluted, ...}`.

### Alpaca — symbol-keyed dict
- **ohlcv** `/v2/stocks/bars`: `{bars: {AAPL:[{t,o,h,l,c,v,n,vw},...], MSFT:[...]}, next_page_token}`. `path: $.bars.{symbol}`, `record_type: nested`. Multi-symbol returns dict keyed by symbol; single-symbol legacy `/v2/stocks/{symbol}/bars` returns `{bars:[...], symbol, next_page_token}`.
- **quote latest**: `{quotes: {AAPL: {t,bp,bs,ap,as,bx,ax,c,z}}}`.
- **news**: `{news:[{id,headline,summary,author,created_at,updated_at,url,symbols:[]}], next_page_token}`.

### Alpha Vantage — function-specific dict, **date-keyed sub-objects**
- **ohlcv** `TIME_SERIES_DAILY_ADJUSTED`: `{"Meta Data":{...}, "Time Series (Daily)":{"2025-04-30":{"1. open":"...","2. high":"...","3. low":"...","4. close":"...","5. adjusted close":"...","6. volume":"...","7. dividend amount":"...","8. split coefficient":"..."}, ...}}`. **Iterate `.items()`**, parse date as ticker-implicit timestamp.
- **quote** `GLOBAL_QUOTE`: `{"Global Quote":{"01. symbol":"AAPL","05. price":"...","09. change":"...","10. change percent":"0.5%"}}`. Strip leading `"NN. "` prefix from keys.
- **news** `NEWS_SENTIMENT`: `{items, sentiment_score_definition, feed:[{title,url,time_published,summary,banner_image,source,authors:[],topics:[],overall_sentiment_score,ticker_sentiment:[]}]}`. `path: $.feed`.
- **fundamentals** `OVERVIEW`: single flat dict, ~60 fields.
- **earnings** `EARNINGS`: `{symbol, annualEarnings:[{fiscalDateEnding,reportedEPS}], quarterlyEarnings:[{fiscalDateEnding,reportedDate,reportedEPS,estimatedEPS,surprise,surprisePercentage}]}`.
- **insider**: `{data:[{transaction_date, ticker, executive, executive_title, security_type, acquisition_or_disposal, shares, share_price}]}`.
- **earnings_calendar / IPO_CALENDAR**: returns **CSV bytes** even with `datatype=json` — parse with `csv` module.

### Benzinga — keyed envelope
- **news**: top-level list of articles `[{id, author, created, updated, title, teaser, body, url, image:[{size,url}], channels:[{name}], stocks:[{name}], tags:[{name}]}]`. `record_type: list_of_dicts`.
- **calendar/earnings**: `{earnings:[{id,date,time,ticker,exchange,name,period,period_year,eps_est,eps,eps_prior,revenue_est,revenue,revenue_prior,importance,updated,notes}]}`. `path: $.earnings`.
- **calendar/dividends**: `{dividends:[{id,date,updated,isin,ticker,name,exchange,frequency,dividend,dividend_prior,dividend_type,dividend_yield,ex_dividend_date,payable_date,record_date,importance}]}`.
- **calendar/economics**: `{economics:[{event_name,description,country,date,time,actual,actual_t,consensus,consensus_t,prior,prior_t,importance}]}`.

### EODHD
- **ohlcv** `/eod/{ticker}`: list `[{date,open,high,low,close,adjusted_close,volume},...]`. `record_type: list_of_dicts`.
- **real-time**: single dict `{code,timestamp,gmtoffset,open,high,low,close,volume,previousClose,change,change_p}`. With `&s=` returns list.
- **fundamentals**: nested dict with sections `General`, `Highlights`, `Valuation`, `SharesStats`, `Technicals`, `SplitsDividends`, `AnalystRatings`, `Holders`, `InsiderTransactions`, `OutstandingShares`, `Earnings`, `Financials.Balance_Sheet/Income_Statement/Cash_Flow`, `ETF_Data` (for ETFs only).
- **dividends/splits**: list `[{date,declarationDate,recordDate,paymentDate,period,value,unadjustedValue,currency},...]`.
- **news**: `[{date,title,content,link,symbols:[],tags:[],sentiment:{polarity,neg,neu,pos}}]`.
- **earnings calendar**: `{type, description, symbols:[{code,report_date,date,before_after_market,currency,actual,estimate,difference,percent}]}`.

### FMP
- **quote**: list of dicts `[{symbol,name,price,changesPercentage,change,dayLow,dayHigh,yearHigh,yearLow,marketCap,priceAvg50,priceAvg200,volume,avgVolume,exchange,open,previousClose,eps,pe,earningsAnnouncement,sharesOutstanding,timestamp}]`.
- **historical-price-full**: `{symbol, historical:[{date,open,high,low,close,adjClose,volume,unadjustedVolume,change,changePercent,vwap,label,changeOverTime},...]}`. `path: $.historical`.
- **profile**: list with single object `[{symbol,price,beta,volAvg,mktCap,lastDiv,range,changes,companyName,currency,cik,isin,cusip,exchange,exchangeShortName,industry,website,description,ceo,sector,country,fullTimeEmployees,...}]`.
- **stock_news**: list `[{symbol,publishedDate,title,image,site,text,url}]`.
- **earning_calendar / historical/earning_calendar**: list `[{date,symbol,eps,epsEstimated,time,revenue,revenueEstimated,updatedFromDate,fiscalDateEnding}]`.
- **dividends**: `{symbol, historical:[{date,label,adjDividend,dividend,recordDate,paymentDate,declarationDate}]}`.
- **insider-trading**: list of dicts with `{symbol, filingDate, transactionDate, reportingCik, transactionType, securitiesOwned, securitiesTransacted, price, ...}`.

### Finnhub — **parallel arrays for candles!**
- **quote** `/quote`: flat dict `{c, h, l, o, pc, d, dp, t}` (current, high, low, open, prev_close, change, change_pct, timestamp). Compact letter codes throughout the API.
- **stock/candle** (premium): `{c:[],h:[],l:[],o:[],t:[],v:[],s:"ok"}`. **Requires zip() across arrays** to produce per-bar dicts.
  ```python
  records = [dict(timestamp=t,open=o,high=h,low=l,close=c,volume=v)
             for t,o,h,l,c,v in zip(d['t'],d['o'],d['h'],d['l'],d['c'],d['v'])]
  ```
- **stock/profile2**: flat dict `{country,currency,exchange,ipo,marketCapitalization,name,phone,shareOutstanding,ticker,weburl,logo,finnhubIndustry}`.
- **stock/metric**: nested `{metric:{...60+ ratios...}, metricType, series:{annual:{},quarterly:{}}, symbol}`.
- **company-news**: list `[{category,datetime,headline,id,image,related,source,summary,url}]`. datetime is unix seconds.
- **stock/earnings**: list `[{actual,estimate,period,quarter,surprise,surprisePercent,symbol,year}]`.
- **calendar/earnings**: `{earningsCalendar:[{date,epsActual,epsEstimate,hour,quarter,revenueActual,revenueEstimate,symbol,year}]}`.
- **calendar/economic**: `{economicCalendar:[{actual,country,estimate,event,impact,prev,time,unit}]}`.
- **stock/insider-transactions**: `{data:[{name,share,change,filingDate,transactionDate,transactionCode,transactionPrice}], symbol}`.
- **stock/filings**: list `[{accessNumber,symbol,cik,form,filedDate,acceptedDate,reportUrl,filingUrl}]`.

### Nasdaq Data Link
- **time-series** `/datasets/{db}/{code}.json`: `{dataset:{id,dataset_code,database_code,name,description,refreshed_at,newest_available_date,oldest_available_date,column_names:[],data:[[date,val1,val2,...],...]}}`. **Parallel arrays via column_names + data** — zip to dicts.
- **datatables** `/datatables/{vendor}/{table}.json`: `{datatable:{data:[[...]], columns:[{name,type},...]}, meta:{next_cursor_id}}`.

### OpenFIGI — array-of-arrays response
- **mapping** POST: returns array indexed parallel to request: `[{data:[{figi,securityType,marketSector,ticker,name,exchCode,shareClassFIGI,compositeFIGI,securityType2,securityDescription}]}, {warning:"No identifier found"}, ...]`. Index `i` of response corresponds to mapping job `i`.
- **search/filter**: `{data:[...],next:"cursor_string"}`.

### Polygon
- **ohlcv** `/v2/aggs/...`: `{ticker, queryCount, resultsCount, adjusted, results:[{v,vw,o,c,h,l,t,n}], status, request_id, count, next_url}`. `path: $.results`. `t` is millisecond UNIX.
- **snapshot single**: `{status, request_id, ticker:{ticker, todaysChangePerc, todaysChange, updated, day:{c,h,l,o,v,vw}, lastQuote:{}, lastTrade:{}, min:{}, prevDay:{}}}`.
- **reference/tickers**: `{count, next_url, request_id, results:[{ticker,name,market,locale,primary_exchange,type,active,currency_name,cik,composite_figi,share_class_figi,last_updated_utc}], status}`.
- **reference/news**: `{results:[{id,publisher:{name,homepage_url,logo_url,favicon_url},title,author,published_utc,article_url,tickers:[],amp_url,image_url,description,keywords:[],insights:[]}], next_url, status, request_id, count}`.
- **reference/dividends**: `{results:[{cash_amount, declaration_date, dividend_type, ex_dividend_date, frequency, pay_date, record_date, ticker}], next_url}`.
- **reference/splits**: `{results:[{execution_date, split_from, split_to, ticker}], next_url}`.
- **vX/reference/financials**: `{results:[{cik,company_name,fiscal_period,fiscal_year,start_date,end_date,filing_date,financials:{income_statement:{revenues:{value,unit,label,order},...},balance_sheet:{},cash_flow_statement:{},comprehensive_income:{}}}]}`.

### SEC API
- **POST query**: `{total:{value,relation:"eq"|"gte"}, filings:[{id,accessionNo,cik,ticker,companyName,companyNameLong,formType,description,filedAt,linkToTxt,linkToHtml,linkToXbrl,linkToFilingDetails,entities:[],documentFormatFiles:[],dataFiles:[],seriesAndClassesContractsInformation:[]}]}`. `path: $.filings`.
- **insider-trading**: `{total, transactions:[{accessionNo, filedAt, periodOfReport, issuer:{cik,name,tradingSymbol}, reportingOwner:{cik,name,relationship:{}}, nonDerivativeTable:{transactions:[{securityTitle,coding:{formType,code,equitySwap},amounts:{shares,pricePerShare,acquiredDisposedCode},postTransactionAmounts:{sharesOwnedFollowingTransaction},ownershipNature:{directOrIndirectOwnership}},...]}, derivativeTable:{}, footnotes:[]}]}`.

### Tradier — XML-style nested JSON
- **markets/quotes**: `{quotes:{quote:[{symbol,description,exch,type,last,change,volume,open,high,low,close,bid,ask,change_percentage,average_volume,last_volume,trade_date,prevclose,week_52_high,week_52_low,bidsize,bidexch,bid_date,asksize,askexch,ask_date,root_symbols}]}}`. **Single-symbol quirk**: returns `quote: {...}` (dict) not list — must wrap in list before iterating.
- **markets/history**: `{history:{day:[{date,open,high,low,close,volume},...]}}`. Same single-vs-list quirk for one bar.
- **markets/timesales**: `{series:{data:[{time,timestamp,price,open,high,low,close,volume,vwap}]}}`.
- **markets/options/chains**: `{options:{option:[{symbol,description,exch,type,last,change,volume,open,high,low,close,bid,ask,underlying,strike,greeks:{delta,gamma,theta,vega,rho,phi,bid_iv,mid_iv,ask_iv,smv_vol,updated_at},change_percentage,average_volume,last_volume,trade_date,prevclose,bidsize,asksize,contract_size,expiration_date,expiration_type,option_type,root_symbol}]}}`. `path: $.options.option`.
- **markets/search**: `{securities:{security:[{symbol,exchange,type,description}]}}`. Returns `null` (not empty) when no matches.

---

## DELIVERABLE 4 — Field Mapping Tables (source → canonical)

### OHLCV canonical: `{ticker, timestamp, open, high, low, close, adj_close, volume, vwap, trade_count}`

| Provider | source → canonical |
|---|---|
| API Ninjas | `open→open, high→high, low→low, close→close, volume→volume, timestamp→timestamp` |
| Alpaca | `t→timestamp, o→open, h→high, l→low, c→close, v→volume, n→trade_count, vw→vwap` (timestamp ISO 8601) |
| Alpha Vantage | `(date key)→timestamp, "1. open"→open, "2. high"→high, "3. low"→low, "4. close"→close, "5. adjusted close"→adj_close, "6. volume"→volume, "7. dividend amount"→dividend_amount, "8. split coefficient"→split_coef` |
| EODHD | `date→timestamp, open→open, high→high, low→low, close→close, adjusted_close→adj_close, volume→volume` |
| FMP | `date→timestamp, open→open, high→high, low→low, close→close, adjClose→adj_close, volume→volume, vwap→vwap` |
| Finnhub | `t[i]→timestamp (unix s), o[i]→open, h[i]→high, l[i]→low, c[i]→close, v[i]→volume` |
| Polygon | `t→timestamp (unix ms), o→open, h→high, l→low, c→close, v→volume, vw→vwap, n→trade_count` |
| Tradier | `date→timestamp, open→open, high→high, low→low, close→close, volume→volume` |

### Quote canonical: `{ticker, last, bid, ask, bid_size, ask_size, prev_close, change, change_pct, volume, market_cap, timestamp}`

| Provider | source → canonical |
|---|---|
| Alpaca latest | `S→ticker, ap→ask, as→ask_size, bp→bid, bs→bid_size, t→timestamp` |
| AV GLOBAL_QUOTE | `"01. symbol"→ticker, "05. price"→last, "08. previous close"→prev_close, "09. change"→change, "10. change percent"→change_pct, "06. volume"→volume, "07. latest trading day"→timestamp` |
| EODHD real-time | `code→ticker, close→last, previousClose→prev_close, change→change, change_p→change_pct, open→open, high→high, low→low, volume→volume, timestamp→timestamp` |
| FMP quote | `symbol→ticker, price→last, dayHigh→high, dayLow→low, open→open, previousClose→prev_close, change→change, changesPercentage→change_pct, volume→volume, marketCap→market_cap, pe→pe_ratio, eps→eps, timestamp→timestamp` |
| Finnhub | `c→last, pc→prev_close, h→high, l→low, o→open, d→change, dp→change_pct, t→timestamp` |
| Polygon snapshot | `ticker→ticker, day.c→last, day.o→open, day.h→high, day.l→low, day.v→volume, prevDay.c→prev_close, todaysChange→change, todaysChangePerc→change_pct, updated→timestamp` |
| Tradier | `symbol→ticker, last→last, bid→bid, ask→ask, bidsize→bid_size, asksize→ask_size, prevclose→prev_close, change→change, change_percentage→change_pct, volume→volume, week_52_high→high_52w, week_52_low→low_52w, trade_date→timestamp` |

### News canonical: `{id, ticker, headline, summary, body, url, source, author, published_at, image_url, sentiment_score}`

| Provider | source → canonical |
|---|---|
| Alpaca | `id→id, headline→headline, summary→summary, content→body, url→url, source→source, author→author, created_at→published_at, symbols→tickers, images[0].url→image_url` |
| AV NEWS_SENTIMENT | `title→headline, summary→summary, url→url, source→source, authors→author, time_published→published_at (YYYYMMDDTHHMMSS), banner_image→image_url, overall_sentiment_score→sentiment_score, ticker_sentiment[].ticker→tickers` |
| Benzinga | `id→id, title→headline, teaser→summary, body→body, url→url, author→author, created→published_at, image[0].url→image_url, stocks[].name→tickers, channels→categories` |
| EODHD | `(hash of url)→id, title→headline, content→body, link→url, date→published_at, symbols→tickers, sentiment.polarity→sentiment_score` |
| FMP | `(hash of url)→id, title→headline, text→summary, url→url, site→source, publishedDate→published_at, image→image_url, symbol→ticker` |
| Finnhub | `id→id, headline→headline, summary→summary, url→url, source→source, datetime→published_at (unix s), image→image_url, related→ticker, category→category` |
| Polygon | `id→id, title→headline, description→summary, article_url→url, publisher.name→source, author→author, published_utc→published_at, image_url→image_url, tickers→tickers, insights→sentiment_data` |

### Fundamentals canonical: `{ticker, market_cap, pe_ratio, pb_ratio, ps_ratio, eps, dividend_yield, beta, sector, industry, employees, description, ipo_date, exchange, currency, shares_outstanding, fiscal_year_end}`

| Provider | source → canonical |
|---|---|
| AV OVERVIEW | `Symbol→ticker, MarketCapitalization→market_cap, PERatio→pe_ratio, PriceToBookRatio→pb_ratio, PriceToSalesRatioTTM→ps_ratio, EPS→eps, DividendYield→dividend_yield, Beta→beta, Sector→sector, Industry→industry, FullTimeEmployees→employees, Description→description, Exchange→exchange, Currency→currency, SharesOutstanding→shares_outstanding, FiscalYearEnd→fiscal_year_end, ProfitMargin→profit_margin, ReturnOnEquityTTM→roe, RevenueTTM→revenue_ttm` |
| EODHD | `General.Code→ticker, Highlights.MarketCapitalization→market_cap, Valuation.TrailingPE→pe_ratio, Valuation.PriceBookMRQ→pb_ratio, Valuation.PriceSalesTTM→ps_ratio, Highlights.EarningsShare→eps, Highlights.DividendYield→dividend_yield, Technicals.Beta→beta, General.Sector→sector, General.Industry→industry, General.FullTimeEmployees→employees, General.Description→description, SharesStats.SharesOutstanding→shares_outstanding` |
| FMP profile | `symbol→ticker, mktCap→market_cap, beta→beta, lastDiv→dividend_amount, sector→sector, industry→industry, fullTimeEmployees→employees, description→description, ipoDate→ipo_date, exchange→exchange, currency→currency, ceo→ceo, website→website, image→logo_url, isEtf→is_etf` |
| Finnhub profile2+metric | `ticker→ticker, marketCapitalization→market_cap, metric.peBasicExclExtraTTM→pe_ratio, metric.pbAnnual→pb_ratio, metric.psTTM→ps_ratio, metric.epsBasicExclExtraItemsTTM→eps, metric.dividendYieldIndicatedAnnual→dividend_yield, metric.beta→beta, finnhubIndustry→industry, shareOutstanding→shares_outstanding, ipo→ipo_date, exchange→exchange, currency→currency, name→company_name, weburl→website, logo→logo_url` |
| Polygon ticker details | `ticker→ticker, market_cap→market_cap, name→company_name, sic_description→industry, total_employees→employees, description→description, list_date→ipo_date, primary_exchange→exchange, currency_name→currency, share_class_shares_outstanding→shares_outstanding, weighted_shares_outstanding→shares_outstanding_weighted` |

### Earnings canonical: `{ticker, fiscal_period, fiscal_year, report_date, time_of_day, eps_actual, eps_estimate, eps_surprise, eps_surprise_pct, revenue_actual, revenue_estimate}`

| Provider | source → canonical |
|---|---|
| API Ninjas | `ticker→ticker, period→fiscal_period, year→fiscal_year, fiscal_date_ending→report_date, eps_basic→eps_actual, revenue→revenue_actual, net_income→net_income` |
| AV EARNINGS | `symbol→ticker, fiscalDateEnding→report_date, reportedDate→report_date, reportedEPS→eps_actual, estimatedEPS→eps_estimate, surprise→eps_surprise, surprisePercentage→eps_surprise_pct` |
| Benzinga | `ticker→ticker, period→fiscal_period, period_year→fiscal_year, date→report_date, time→time_of_day, eps→eps_actual, eps_est→eps_estimate, revenue→revenue_actual, revenue_est→revenue_estimate` |
| EODHD calendar | `code→ticker, report_date→report_date, before_after_market→time_of_day, actual→eps_actual, estimate→eps_estimate, difference→eps_surprise, percent→eps_surprise_pct` |
| FMP | `symbol→ticker, fiscalDateEnding→report_date, time→time_of_day, eps→eps_actual, epsEstimated→eps_estimate, revenue→revenue_actual, revenueEstimated→revenue_estimate` |
| Finnhub | `symbol→ticker, period→fiscal_period, year→fiscal_year, hour→time_of_day, date→report_date, epsActual→eps_actual, epsEstimate→eps_estimate, revenueActual→revenue_actual, revenueEstimate→revenue_estimate, surprise→eps_surprise, surprisePercent→eps_surprise_pct` |

### Dividends canonical: `{ticker, dividend_amount, currency, ex_date, record_date, pay_date, declaration_date, frequency, dividend_type}`

| Provider | source → canonical |
|---|---|
| Benzinga | `ticker→ticker, dividend→dividend_amount, currency→currency, ex_dividend_date→ex_date, record_date→record_date, payable_date→pay_date, frequency→frequency, dividend_type→dividend_type` |
| EODHD | `value→dividend_amount, date→ex_date, recordDate→record_date, paymentDate→pay_date, declarationDate→declaration_date, period→frequency, currency→currency, unadjustedValue→dividend_amount_unadj` |
| FMP | `symbol→ticker, adjDividend→dividend_amount, dividend→dividend_amount_raw, date→ex_date, recordDate→record_date, paymentDate→pay_date, declarationDate→declaration_date` |
| Polygon | `ticker→ticker, cash_amount→dividend_amount, ex_dividend_date→ex_date, record_date→record_date, pay_date→pay_date, declaration_date→declaration_date, frequency→frequency, dividend_type→dividend_type` |

### Splits canonical: `{ticker, execution_date, ratio_from, ratio_to, ratio}`

| Provider | source → canonical |
|---|---|
| EODHD | `date→execution_date, split→"{from}/{to}" (parse string)` |
| FMP | `symbol→ticker, date→execution_date, numerator→ratio_to, denominator→ratio_from, label→label` |
| Polygon | `ticker→ticker, execution_date→execution_date, split_from→ratio_from, split_to→ratio_to` |

### Insider transactions canonical: `{ticker, name, title, transaction_date, transaction_code, shares, price, value, shares_owned_after, acquired_disposed}`

| Provider | source → canonical |
|---|---|
| AV | `ticker→ticker, executive→name, executive_title→title, transaction_date→transaction_date, security_type→security_type, acquisition_or_disposal→acquired_disposed, shares→shares, share_price→price` |
| FMP v4 | `symbol→ticker, reportingName→name, typeOfOwner→title, transactionDate→transaction_date, transactionType→transaction_code, securitiesTransacted→shares, price→price, securitiesOwned→shares_owned_after, acquistionOrDisposition→acquired_disposed` |
| Finnhub | `symbol→ticker, name→name, transactionDate→transaction_date, transactionCode→transaction_code, change→shares (signed), transactionPrice→price, share→shares_owned_after, filingDate→filing_date` |
| SEC-API | `issuer.tradingSymbol→ticker, reportingOwner.name→name, periodOfReport→transaction_date, nonDerivativeTable.transactions[].coding.code→transaction_code, .amounts.shares→shares, .amounts.pricePerShare→price, .postTransactionAmounts.sharesOwnedFollowingTransaction→shares_owned_after, .amounts.acquiredDisposedCode→acquired_disposed` |

### Economic calendar canonical: `{event_name, country, release_date, release_time, importance, actual, estimate, previous, unit, currency}`

| Provider | source → canonical |
|---|---|
| AV (CSV) | `name→event_name, country→country, releaseDate→release_date, currency→currency, unit→unit, estimate→estimate` |
| Benzinga | `event_name→event_name, country→country, date→release_date, time→release_time, actual→actual, consensus→estimate, prior→previous, importance→importance` |
| EODHD | `type→event_name, country→country, date→release_date, actual→actual, estimate→estimate, previous→previous` |
| FMP | `event→event_name, country→country, date→release_date, actual→actual, estimate→estimate, previous→previous, change→change, impact→importance` |
| Finnhub | `event→event_name, country→country, time→release_date, actual→actual, estimate→estimate, prev→previous, impact→importance, unit→unit` |

### Options canonical: `{underlying, contract_symbol, expiration, strike, option_type, bid, ask, last, volume, open_interest, iv, delta, gamma, theta, vega, rho}`

| Provider | source → canonical |
|---|---|
| Polygon snapshot | `underlying_asset.ticker→underlying, details.ticker→contract_symbol, details.expiration_date→expiration, details.strike_price→strike, details.contract_type→option_type, last_quote.bid→bid, last_quote.ask→ask, last_trade.price→last, day.volume→volume, open_interest→open_interest, implied_volatility→iv, greeks.delta→delta, greeks.gamma→gamma, greeks.theta→theta, greeks.vega→vega` |
| Tradier | `underlying→underlying, symbol→contract_symbol, expiration_date→expiration, strike→strike, option_type→option_type, bid→bid, ask→ask, last→last, volume→volume, open_interest→open_interest, greeks.mid_iv→iv, greeks.delta→delta, greeks.gamma→gamma, greeks.theta→theta, greeks.vega→vega, greeks.rho→rho` |

---

## DELIVERABLE 5 — Database Schema (SQLite)

```sql
-- 1. OHLCV daily bars
CREATE TABLE IF NOT EXISTS ohlcv_daily (
  ticker         TEXT NOT NULL,
  date           TEXT NOT NULL,            -- ISO YYYY-MM-DD
  open           REAL,
  high           REAL,
  low            REAL,
  close          REAL,
  adj_close      REAL,
  volume         INTEGER,
  vwap           REAL,
  trade_count    INTEGER,
  source_provider TEXT NOT NULL,           -- 'alpaca'|'polygon'|'eodhd'|...
  ingested_at    TEXT NOT NULL DEFAULT (datetime('now')),
  PRIMARY KEY (ticker, date)
);
CREATE INDEX IF NOT EXISTS idx_ohlcv_date    ON ohlcv_daily(date);
CREATE INDEX IF NOT EXISTS idx_ohlcv_provider ON ohlcv_daily(source_provider, date);
-- UPSERT: INSERT INTO ohlcv_daily(...) VALUES(...) ON CONFLICT(ticker,date) DO UPDATE SET
--   close=excluded.close, adj_close=excluded.adj_close, volume=excluded.volume,
--   source_provider=excluded.source_provider, ingested_at=excluded.ingested_at;

-- 2. Fundamentals snapshots
CREATE TABLE IF NOT EXISTS fundamentals_snapshot (
  ticker            TEXT NOT NULL,
  snapshot_date     TEXT NOT NULL,         -- date the snapshot was captured
  market_cap        REAL,
  pe_ratio          REAL,
  pb_ratio          REAL,
  ps_ratio          REAL,
  eps               REAL,
  dividend_yield    REAL,
  beta              REAL,
  sector            TEXT,
  industry          TEXT,
  employees         INTEGER,
  shares_outstanding REAL,
  description       TEXT,
  ipo_date          TEXT,
  exchange          TEXT,
  currency          TEXT,
  source_provider   TEXT NOT NULL,
  raw_payload       TEXT,                   -- JSON dump for fields not yet mapped
  ingested_at       TEXT NOT NULL DEFAULT (datetime('now')),
  PRIMARY KEY (ticker, snapshot_date, source_provider)
);
CREATE INDEX IF NOT EXISTS idx_fund_sector ON fundamentals_snapshot(sector, snapshot_date);

-- 3. Earnings
CREATE TABLE IF NOT EXISTS earnings (
  ticker          TEXT NOT NULL,
  fiscal_year     INTEGER NOT NULL,
  fiscal_period   TEXT NOT NULL,           -- 'Q1'|'Q2'|'Q3'|'Q4'|'FY'
  report_date     TEXT,
  time_of_day     TEXT,                     -- 'bmo'|'amc'|'dmh'
  eps_actual      REAL,
  eps_estimate    REAL,
  eps_surprise    REAL,
  eps_surprise_pct REAL,
  revenue_actual  REAL,
  revenue_estimate REAL,
  source_provider TEXT NOT NULL,
  ingested_at     TEXT NOT NULL DEFAULT (datetime('now')),
  PRIMARY KEY (ticker, fiscal_year, fiscal_period, source_provider)
);
CREATE INDEX IF NOT EXISTS idx_earnings_report_date ON earnings(report_date);

-- 4. Corporate actions (dividends + splits in one log)
CREATE TABLE IF NOT EXISTS corporate_actions (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  ticker          TEXT NOT NULL,
  action_type     TEXT NOT NULL,            -- 'dividend' | 'split'
  ex_date         TEXT NOT NULL,
  record_date     TEXT,
  pay_date        TEXT,
  declaration_date TEXT,
  -- dividend fields
  dividend_amount REAL,
  currency        TEXT,
  frequency       INTEGER,                   -- 1=annual, 4=quarterly, 12=monthly
  dividend_type   TEXT,
  -- split fields
  split_from      REAL,
  split_to        REAL,
  source_provider TEXT NOT NULL,
  ingested_at     TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE (ticker, action_type, ex_date, source_provider)
);
CREATE INDEX IF NOT EXISTS idx_actions_ticker_date ON corporate_actions(ticker, ex_date);

-- 5. News articles (deduplicated cross-provider)
-- Dedup strategy: hash of (lower(headline) + published_date) OR url itself.
-- Prefer url-based when present; fallback to title hash for providers reusing URLs.
CREATE TABLE IF NOT EXISTS news_articles (
  dedup_key       TEXT PRIMARY KEY,         -- sha1(coalesce(url, lower(headline)||published_at))
  headline        TEXT NOT NULL,
  summary         TEXT,
  body            TEXT,
  url             TEXT,
  source          TEXT,
  author          TEXT,
  published_at    TEXT NOT NULL,            -- ISO 8601 UTC
  image_url       TEXT,
  sentiment_score REAL,
  source_provider TEXT NOT NULL,            -- first provider to deliver
  seen_providers  TEXT,                      -- CSV of providers that also have it
  ingested_at     TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS news_tickers (
  dedup_key       TEXT NOT NULL,
  ticker          TEXT NOT NULL,
  PRIMARY KEY (dedup_key, ticker),
  FOREIGN KEY (dedup_key) REFERENCES news_articles(dedup_key) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_news_published ON news_articles(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_news_tickers   ON news_tickers(ticker);

-- 6. Economic calendar
CREATE TABLE IF NOT EXISTS economic_calendar (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  event_name      TEXT NOT NULL,
  country         TEXT NOT NULL,
  release_date    TEXT NOT NULL,
  release_time    TEXT,
  importance      INTEGER,                  -- 0|1|2|3
  actual          REAL,
  estimate        REAL,
  previous        REAL,
  unit            TEXT,
  currency        TEXT,
  source_provider TEXT NOT NULL,
  ingested_at     TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE (event_name, country, release_date, source_provider)
);
CREATE INDEX IF NOT EXISTS idx_econ_date ON economic_calendar(release_date);

-- Cross-table linkage hint to existing trade_executions:
-- trade_executions.ticker references ohlcv_daily.ticker logically (no FK
-- since OHLCV may not exist for all dates traded, e.g., extended-hours fills).
-- For attribution analysis: JOIN trade_executions te ON te.ticker = ohlcv_daily.ticker
-- AND date(te.executed_at) = ohlcv_daily.date.
```

---

## DELIVERABLE 6 — Top 10 Scheduling Recipes (MIXED Trader Profile)

```yaml
- name: nightly_ohlcv_refresh
  cron: "0 22 * * 1-5"          # 10pm ET weekdays, after official close
  provider: alpaca
  data_type: ohlcv
  endpoint: "/v2/stocks/bars?timeframe=1Day&adjustment=split"
  tickers_source: "watchlist + portfolio_holdings"
  retention_days: 3650           # 10 years for backtesting
  fallback_provider: eodhd
  notes: "Use multi-symbol batched calls (50 tickers per call). Idempotent UPSERT keyed on (ticker,date)."

- name: premarket_quote_sweep
  cron: "*/5 4-9 * * 1-5"        # every 5 min, 4am-9am ET (premarket)
  provider: finnhub
  data_type: quote
  endpoint: "/quote"
  tickers_source: "active_day_trade_watchlist"
  retention_days: 30
  fallback_provider: alpaca       # /v2/stocks/quotes/latest
  notes: "Day-trader-focused. 60 req/min budget allows ~300 tickers refreshed every 5min."

- name: weekly_fundamentals_refresh
  cron: "0 6 * * 6"               # 6am Saturday
  provider: fmp
  data_type: fundamentals
  endpoint: "/profile/{ticker} + /ratios-ttm/{ticker}"
  tickers_source: "long_term_holdings + watchlist (sectors of interest)"
  retention_days: 1825            # 5 years of weekly snapshots
  fallback_provider: alphavantage  # OVERVIEW (1 ticker per call, slow)
  notes: "Long-term investor focus. FMP 250/day limit covers ~125 tickers/wk with redundant calls."

- name: earnings_calendar_pull
  cron: "0 5 * * *"               # 5am ET daily
  provider: finnhub
  data_type: earnings
  endpoint: "/calendar/earnings?from=today&to=today+30d"
  tickers_source: "*"
  retention_days: 730
  fallback_provider: fmp           # /earning_calendar
  notes: "Swing-trader focus: anticipate earnings volatility 30 days out. Cross-reference with positions."

- name: dividend_tracker
  cron: "0 7 * * 1"               # 7am Monday
  provider: polygon
  data_type: dividends
  endpoint: "/v3/reference/dividends?ex_dividend_date.gte=today"
  tickers_source: "long_term_holdings + dividend_focus_watchlist"
  retention_days: 3650
  fallback_provider: eodhd
  notes: "Long-term investor: track upcoming ex-dates and pay dates for cashflow planning."

- name: news_stream_realtime
  cron: "*/2 6-20 * * 1-5"        # every 2 min, 6am-8pm ET weekdays
  provider: finnhub
  data_type: news
  endpoint: "/company-news?from=yesterday&to=today"
  tickers_source: "active_watchlist (limit 30 tickers)"
  retention_days: 90
  fallback_provider: polygon       # /v2/reference/news
  notes: "Day+swing focus. Dedup against news_articles.dedup_key. 60/min ÷ 30 tickers = full sweep every 30s if needed."

- name: insider_transactions_daily
  cron: "30 23 * * 1-5"           # 11:30pm ET weekdays
  provider: finnhub
  data_type: insider
  endpoint: "/stock/insider-transactions?from=last_run&to=today"
  tickers_source: "long_term_holdings + watchlist"
  retention_days: 3650
  fallback_provider: fmp           # v4 /insider-trading
  notes: "Long-term investor: catch SEC Form 4 filings. SEC-API better for fresh <300ms latency if budget allows."

- name: economic_calendar_weekly
  cron: "0 6 * * 0"               # 6am Sunday — preview the week
  provider: finnhub
  data_type: economic_calendar
  endpoint: "/calendar/economic?from=monday&to=sunday"
  tickers_source: "n/a"
  retention_days: 1095
  fallback_provider: fmp
  notes: "Mixed-trader macro overlay. Filter to importance >= 2 (medium/high impact)."

- name: options_chain_swing_snapshot
  cron: "30 15 * * 1-5"           # 3:30pm ET weekdays (before close)
  provider: tradier
  data_type: options
  endpoint: "/markets/options/chains?greeks=true"
  tickers_source: "options_watchlist (e.g., SPY, QQQ, top 20 mega-caps)"
  retention_days: 180
  fallback_provider: polygon       # /v3/snapshot/options/{underlying} (premium)
  notes: "Swing-trader focus. Tradier requires brokerage account; sandbox is 15-min delayed."

- name: etf_holdings_monthly
  cron: "0 8 1 * *"                # 8am 1st of month
  provider: fmp
  data_type: etf_holdings
  endpoint: "/api/v4/etf-holdings?symbol={ticker}"
  tickers_source: "etf_watchlist (SPY, QQQ, IWM, sector ETFs held)"
  retention_days: 3650
  fallback_provider: eodhd          # /fundamentals/{ticker}.US ETF_Data section
  notes: "Long-term investor: track sector exposure drift, identify overlap between ETFs."
```

Bonus utility job (essential infrastructure):

```yaml
- name: identifier_mapping_refresh
  cron: "0 4 1 */3 *"              # quarterly
  provider: openfigi
  data_type: identifier_mapping
  endpoint: "POST /v3/mapping with batched array body"
  tickers_source: "all distinct tickers from ohlcv_daily"
  retention_days: forever
  fallback_provider: eodhd           # /id-map
  notes: "Maintain ticker ↔ FIGI ↔ CUSIP ↔ ISIN ↔ CIK crosswalk for joining datasets across providers."
```

---

## DELIVERABLE 7 — Edge Cases & Gotchas

### API Ninjas
- Free 50K calls/month is generous, but `/v1/earnings` history before 2025 is **premium**.
- `/v1/earningstranscript` returns full transcripts — large payloads (sometimes >1MB).
- All time params are **UNIX seconds**, not millis or ISO.
- No multi-ticker support anywhere — must loop.

### Alpaca
- Free tier delivers **IEX feed only** (~5% market volume); SIP feed needs Algo Trader Plus ($99/mo).
- Free tier blocks **last 15 minutes** of historical data — querying recent end times returns subscription error.
- Authentication uses **two headers** (`APCA-API-KEY-ID` + `APCA-API-SECRET-KEY`), not Bearer.
- Multi-symbol bars response shape **differs** from single-symbol (dict-keyed vs list).
- `asof` parameter handles ticker renames (FB→META) automatically.
- Crypto endpoints don't require auth; use `data.alpaca.markets/v1beta3/crypto/us/...`.
- **Trading API is at `paper-api.alpaca.markets` or `api.alpaca.markets`** — separate from data API.

### Alpha Vantage
- **25 calls/day free tier** as of late 2024 (was 500, then 100, now 25). Effectively useless for production — caching mandatory.
- Date keys are nested as **dict-of-dicts**, not arrays — must `for date, vals in payload["Time Series (Daily)"].items()`.
- Field names have **leading numeric prefixes**: `"1. open"`, `"5. adjusted close"` — sanitize.
- `EARNINGS_CALENDAR` and `IPO_CALENDAR` return **CSV bytes** even with `datatype=json`.
- Rate-limit response is HTTP 200 with `{"Note": "..."}` or `{"Information": "..."}` — must inspect body, not status.
- Premium starts at **$49.99/mo for 75/min**, no daily cap.

### Benzinga
- Almost entirely **paid** — contact `licensing@benzinga.com`. No self-serve free tier.
- Pagination: `parameters[updated]` deltas required; offset capped at 100,000 results total per query.
- Default response is JSON only when `Accept: application/json` set (some endpoints default to XML).
- `/api/v2/news` page size limit: 100 articles, max 100 pages = 10,000 result ceiling.

### EODHD
- Free tier: **20 calls/day, US tickers only, 1 year of history**. The `demo` token works only for AAPL.US, TSLA.US, MSFT.US, AMZN.US, VTI.US, BTC-USD.CC, EURUSD.FOREX.
- Calls are **cost-weighted** (1–100 credits per call) — bulk endpoints consume 100/call but per-ticker cost is lower.
- Symbol format `{TICKER}.{EXCHANGE_CODE}` (e.g., `AAPL.US`, `MCD.MX`). Just `AAPL` defaults to US.
- Yahoo-style URL format `/api/table.csv?s=...&a=...&b=...&c=...` is supported but uses **0-indexed months** (Yahoo legacy).

### Financial Modeling Prep
- **250 calls/day free**, US only. Realistic ceiling: ~25 companies fully analyzed (3 calls each) per day.
- API in transition: legacy `/api/v3/` paths coexist with new `/stable/` paths in 2024-2025.
- v4 endpoints (`/api/v4/insider-trading`, `/api/v4/etf-holdings`, `/api/v4/financial-reports-json`) require **paid Starter+** tier in many cases.
- Bulk endpoints (`/historical/earning_calendar/{ticker}`) frequently rate-limit even with paid plans.
- Market cap calculation methodology differs from Bloomberg/Yahoo — verify before using in models.

### Finnhub
- **Critical**: `/stock/candle` started returning **HTTP 403 "You don't have access to this resource"** for free-tier users in 2024 — historical OHLCV is now **premium-only**. Use Alpaca/EODHD/Polygon for free OHLCV instead.
- All timestamps are **UNIX seconds** (not millis).
- Candles use **parallel arrays** `{c:[],h:[],l:[],o:[],t:[],v:[],s:"ok"}` — must `zip()`.
- European/non-US tickers (e.g., `ORP.PA`, `SLB.PA`) frequently 403 even on premium — coverage gap.
- `s` field on candle response = `"ok"` or `"no_data"` — **must check** before unpacking arrays.
- Auth accepts both `?token=` query param and `X-Finnhub-Token` header — pick one.

### Nasdaq Data Link (Quandl rebrand)
- **WIKI/EOD database (free US stocks) was discontinued in 2018** and remains offline. Many tutorials still reference it — they fail.
- 2018 acquisition by Nasdaq, 2021 launched as "Data Link". URLs at both `data.nasdaq.com/api/v3` and legacy `quandl.com/api/v3` (redirects).
- Most "alternative data" tables (Sharadar, ZACKS, etc.) are **paid subscriptions** — free is mostly economic series (FRED mirror, USTREASURY, OPEC, LBMA, BCB).
- Time-series response uses **parallel arrays + column_names** — zip required.
- Tables API uses cursor-based pagination via `qopts.cursor_id`; max 10,000 rows per page.

### OpenFIGI
- **Only POST** API on this list — body is JSON array of mapping jobs.
- v2 sunsets **July 1, 2026** → returns HTTP 410. Migrate to v3 ASAP.
- v3 renamed `error: "No identifier found"` to `warning: "No identifier found"` — code expecting `error` key will silently miss no-match results.
- Free unauthenticated: **25 jobs per request, 25 requests/6sec**. With key: 100 jobs per request, higher rate.
- Requires `Content-Type: application/json` header — missing it returns 400.
- Truly free, no paid tier.

### Polygon.io
- Free **5 req/min, 2-year history, EOD only, no real-time**. Becomes unworkable beyond toy datasets.
- Mixed versioning: aggregates use `/v2/aggs/...`, reference uses `/v3/reference/...`, snapshots mix `/v2/snapshot/...` and `/v3/snapshot/...`, financials use experimental `/vX/reference/financials`. Verify per endpoint.
- Date params accept both `YYYY-MM-DD` and **millisecond UNIX**. Bar timestamps in `t` are **milliseconds**.
- Aggregate `limit` capped at 50,000 — for minute bars that's ~1.5 months. Must paginate via `next_url`.
- `next_url` already includes `apiKey=` — be careful not to log it (secret leakage).
- 15-min delayed on free tier; corrections re-stated post-close (re-fetch next day for accuracy).
- Domain confusion: some docs/clients now reference `massive.com` — Polygon rebranded their public-facing site mid-2025; `api.polygon.io` still works.

### SEC API (sec-api.io)
- **Third-party paid wrapper** around SEC EDGAR — **not** free SEC.gov direct access.
- Free tier: **100 calls/month**. Personal $55/mo, Business $239/mo.
- All search endpoints are **POST** with Lucene-syntax query body.
- Authentication: `Authorization: {key}` header (no `Bearer ` prefix) OR `?token=` query param.
- Response capped at **10,000 documents** per query — narrow with date/ticker filters; for bulk use the bulk download (.jsonl.gz) datasets.
- Insider transactions return **nested derivative + non-derivative tables** — MUST iterate both for complete picture.

### Tradier
- **Brokerage account required** to obtain API token — not signup-and-go.
- Production at `api.tradier.com/v1`; sandbox at `sandbox.tradier.com/v1` is **always 15-min delayed**, even for paid accounts.
- Real-time data only for **Tradier Brokerage account holders**, US equities + options.
- Single-symbol responses **collapse list to dict** (e.g., `quotes.quote` is dict not list when one symbol). Defensive code required: `quotes = q if isinstance(q, list) else [q]`.
- Fundamentals at `/beta/markets/fundamentals/...` — beta, brokerage-only, sourced from Morningstar.
- OAuth 2.0 only available to Partners; retail users use static Bearer tokens.
- POST `/markets/quotes` accepts more symbols than GET (form-encoded body) — recommended for >50 tickers.
- No FK relationship to existing `trade_executions` table by design — link via ticker+date.

### Cross-cutting gotchas
- **Date format chaos**: AV uses `YYYY-MM-DD` strings (also `YYYYMMDDTHHMM` for news), Polygon/Alpaca use ISO 8601 RFC-3339, Finnhub/API-Ninjas use UNIX seconds, Polygon bar timestamps use UNIX **milliseconds**, OpenFIGI doesn't care about dates. Normalize at the TransformStep.
- **Adjusted vs raw**: Default behavior differs. AV `TIME_SERIES_DAILY_ADJUSTED` returns both. Polygon `adjusted=true` default. Tradier history is **not split-adjusted reliably**. Always store both `close` and `adj_close` when available.
- **Provider dedup for news**: Same article via Benzinga, Polygon, AV may have different IDs — dedup on `(lower(headline), date(published_at))` hash.
- **Symbol formats**: BRK.B vs BRK-B vs BRK/B differs across providers. Maintain ticker normalization layer keyed on OpenFIGI compositeFIGI.
- **Authentication storage**: never put Polygon/Finnhub tokens in URL strings that get logged — prefer header-based variants where supported.
- **Rate-limit detection**: AV returns HTTP 200 with `{"Note":...}`; Finnhub returns 429 with `Retry-After`; Polygon returns 429; Alpaca returns 429 with `X-Ratelimit-*` headers; SEC-API returns 429. Implement provider-specific retry/backoff in FetchStep.

---

## Caveats

- Free-tier limits and endpoint availability shift frequently (Alpha Vantage went 500→100→25/day in two years; Finnhub silently moved candles to premium in 2024). **Re-verify rate limits quarterly** — the values here are accurate as of search date but providers don't always update their public docs immediately.
- Benzinga, SEC-API, and most Polygon/EODHD/FMP advanced data are **commercial licenses** — pricing typically not posted publicly for Benzinga; expect $200–$2,000/mo for serious use.
- The `/api.benzinga.com/api/v2` listing of `/api/v2.1/fundamentals` is described in docs as the current version (v2 deprecated); upgrade if your registered code uses v2 fundamentals.
- Field availability within a provider varies by **subscription tier and asset class** — ETF responses differ structurally from stock responses (especially in EODHD `fundamentals` and FMP `profile`). Test against ETFs (SPY, QQQ) and ADRs (TSM, BABA) before declaring mapping complete.
- Market data licensing imposes **redistribution restrictions** (especially Polygon SIP, Alpaca SIP, Tradier real-time, Benzinga). If your trading-analytics platform serves multiple end-users, ensure your contract permits multi-user access — most retail/personal-use plans do not.
- The OpenFIGI v2→v3 sunset (July 1, 2026) will cause silent breakage for code that checks an `error` key on no-match results — explicitly migrate before then.
- SEC-API's relationship to SEC EDGAR: the underlying data is public domain, but sec-api.io's value-add is the indexing/search/standardization. Free SEC EDGAR direct (`data.sec.gov`) is an alternative requiring more parsing work but no per-call cost.
- This research focused on documented behavior; undocumented quirks (e.g., Tradier's single-vs-list collapse) only become apparent in production. Wrap all extractors with defensive `isinstance(x, list)` guards.
