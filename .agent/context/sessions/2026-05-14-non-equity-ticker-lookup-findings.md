# Non-Equity Ticker Lookup — Feasibility Analysis

> **Date**: 2026-05-14
> **Scope**: Position Calculator auto-mode switching for futures, forex, crypto, options
> **Conversation**: Contributing docs session (5faa3388)

---

## 1. Question

Can the existing ticker search support lookup for futures, options, forex, and crypto so the Position Calculator auto-switches mode when a non-equity instrument is selected?

## 2. Current State

### Backend: `_yahoo_search()` explicitly filters non-equity types

**File**: `packages/core/src/zorivest_core/services/market_data_service.py`, lines 237–272

```python
_EXCLUDED_TYPES = {
    "FUTURE", "CURRENCY", "CRYPTOCURRENCY",
    "INDEX", "MUTUALFUND",
}
```

Yahoo Finance's `/v1/finance/search` API **already returns** futures, forex, and crypto results — each tagged with a `quoteType` field (`"FUTURE"`, `"CURRENCY"`, `"CRYPTOCURRENCY"`). The service **explicitly filters them out** before returning results.

### DTO: `TickerSearchResult` has no instrument type field

**File**: `packages/core/src/zorivest_core/application/market_dtos.py`, lines 46–53

```python
class TickerSearchResult(BaseModel):
    symbol: str
    name: str
    exchange: Optional[str] = None
    currency: Optional[str] = None
    provider: str
```

No `instrument_type` or `quote_type` field exists. Even if filtering were removed, the UI has no way to know the instrument type from search results.

### UI: Client-side regex heuristics for auto-switching

**File**: `ui/src/renderer/src/features/planning/PositionCalculatorModal.tsx`, lines 201–218

The `handleTickerSelect` callback uses pattern matching:
- **Futures**: matches against `FUTURES_PRESETS` keys (ES, NQ, YM, CL, GC)
- **Forex**: regex for `EUR/USD`, `EURUSD` patterns  
- **Crypto**: regex for `BTC`, `ETH`, `SOL`, etc. with optional `-USD` suffix

This is fragile — a ticker like "SOLAR" could false-positive on the SOL pattern. Server-provided `quoteType` would be reliable.

### API: Simple passthrough, no filtering logic

**File**: `packages/api/src/zorivest_api/routes/market_data.py`, lines 173–182

The `/search` endpoint is a thin passthrough to `service.search_ticker(query)`. No additional filtering or transformation happens here.

### Quote fetching: Yahoo chart API works for all instrument types

`_yahoo_quote()` uses `/v8/finance/chart/{ticker}` which works for forex (e.g., `EURUSD=X`), crypto (e.g., `BTC-USD`), and futures (e.g., `ES=F`). **No implementation needed for price data** — it already works if the correct ticker format is used.

## 3. What Needs to Change

### Layer 1 — Core DTO (small)
Add `instrument_type` to `TickerSearchResult`:

```python
class TickerSearchResult(BaseModel):
    symbol: str
    name: str
    exchange: Optional[str] = None
    currency: Optional[str] = None
    instrument_type: Optional[str] = None  # NEW: "EQUITY", "FUTURE", "CURRENCY", "CRYPTOCURRENCY"
    provider: str
```

### Layer 2 — Service (small)
Modify `_yahoo_search()`:
1. Remove or make `_EXCLUDED_TYPES` configurable (e.g., only exclude `INDEX`, `MUTUALFUND`)
2. Pass `quoteType` from Yahoo response into `instrument_type` field

```python
# Before
if q.get("quoteType") not in _EXCLUDED_TYPES

# After  
_EXCLUDED_TYPES = {"INDEX", "MUTUALFUND"}  # Keep filtering irrelevant types
# ...
TickerSearchResult(
    symbol=q["symbol"],
    name=q.get("shortname") or q.get("longname") or q["symbol"],
    exchange=q.get("exchange"),
    currency=None,
    instrument_type=q.get("quoteType"),  # NEW
    provider="Yahoo Finance",
)
```

### Layer 3 — API (zero change)
The passthrough endpoint requires no changes.

### Layer 4 — UI (small)
Replace regex heuristics in `handleTickerSelect` with server-provided type:

```typescript
const handleTickerSelect = useCallback((result: { symbol: string; instrument_type?: string }) => {
    const sym = result.symbol
    setTicker(sym)

    // Use server-provided instrument type instead of regex heuristics
    switch (result.instrument_type) {
        case 'FUTURE':
            setCalcMode('futures')
            // Auto-fill preset if symbol matches known futures
            if (sym.toUpperCase() in FUTURES_PRESETS) {
                setFuturesPreset(sym.toUpperCase())
                setFuturesInputs(FUTURES_PRESETS[sym.toUpperCase()])
            }
            break
        case 'CURRENCY':
            setCalcMode('forex')
            break
        case 'CRYPTOCURRENCY':
            setCalcMode('crypto')
            break
        default:
            // EQUITY or unknown — keep current mode
            break
    }
    // ... rest of quote fetching
}, [setStatus])
```

### Layer 5 — TickerAutocomplete component
The `TickerAutocomplete` component (`ui/src/renderer/src/components/TickerAutocomplete.tsx`) needs to pass the full search result object (including `instrument_type`) through its `onSelect` callback, not just `{ symbol: string }`.

## 4. Effort Estimate

| Change | Effort | Risk |
|:-------|:-------|:-----|
| DTO field addition | ~10 min | None — additive, Optional field |
| Service filter + field mapping | ~20 min | Low — may surface unexpected symbols in search |
| UI auto-switch refactor | ~30 min | Low — replaces fragile regex with reliable server data |
| TickerAutocomplete prop update | ~15 min | Low — additive |
| Tests (unit + integration) | ~1 hour | None |
| **Total** | **~2 hours** | **Low** |

## 5. Free Provider Coverage for Non-Equity Types

### Ticker Search + Price Data

| Provider | Futures | Forex | Crypto | Options | Free Tier | Already Integrated |
|:---------|:-------:|:-----:|:------:|:-------:|:----------|:------------------:|
| **Yahoo Finance** | ✅ | ✅ | ✅ | ✅ (chain only†) | Unlimited (unofficial) | ✅ |
| **Alpha Vantage** | ❌ | ✅ | ✅ | ✅ | 25 req/day | ✅ (registered) |
| **Finnhub** | ✅ | ✅ | ✅ | ❌ | 60 req/min | ✅ (registered) |
| **Twelve Data** | ❌ | ✅ | ✅ | ❌ | 800 req/day | ❌ |
| **Polygon.io** | ✅ | ✅ | ✅ | ✅ | 5 req/min (delayed) | ✅ (registered) |

† Yahoo options data is available via `/v7/finance/options/{symbol}`, not via ticker search.

### Key Finding

**Yahoo Finance (already integrated) covers all four non-equity types.** No new provider needed.

- **Futures, forex, crypto**: Available via `/v1/finance/search` (currently filtered out) and `/v8/finance/chart/{ticker}` for quotes. Just stop filtering and pipe `quoteType` through.
- **Options**: Available via a **separate endpoint** — `/v7/finance/options/{symbol}`. Returns the full options chain (calls + puts) with strike prices, expiration dates, bid/ask, volume, open interest, and implied volatility. However, options don't appear in the ticker search results — they use a different access pattern where you search for the underlying equity first, then browse its options chain.

### Yahoo Finance Endpoint Map by Type

| Type | Example Tickers | Search Endpoint | Data Endpoint |
|:-----|:----------------|:----------------|:--------------|
| Equity | `AAPL`, `MSFT` | `/v1/finance/search` | `/v8/finance/chart/AAPL` |
| Futures | `ES=F`, `NQ=F`, `CL=F` | `/v1/finance/search` | `/v8/finance/chart/ES=F` |
| Forex | `EURUSD=X`, `GBPJPY=X` | `/v1/finance/search` | `/v8/finance/chart/EURUSD=X` |
| Crypto | `BTC-USD`, `ETH-USD` | `/v1/finance/search` | `/v8/finance/chart/BTC-USD` |
| Options | `AAPL250620C00200000` | N/A (browse via underlying) | `/v7/finance/options/AAPL` |

### Yahoo Options Chain Endpoint Detail

```
GET https://query1.finance.yahoo.com/v7/finance/options/{symbol}
```

**Returns**: JSON with `optionChain.result[0]` containing:
- `expirationDates`: array of Unix timestamps for available expirations
- `strikes`: array of available strike prices
- `options[0].calls`: array of call contracts with `strike`, `lastPrice`, `bid`, `ask`, `volume`, `openInterest`, `impliedVolatility`, `expiration`
- `options[0].puts`: same structure for puts

**Access pattern**: Unlike search (type a query → get results), options require a two-step flow:
1. Search for the underlying equity (e.g., `AAPL`)
2. Fetch `/v7/finance/options/AAPL` to browse the chain
3. Optionally filter by expiration: `/v7/finance/options/AAPL?date={unix_timestamp}`

**UI implication**: Options support in the Position Calculator would need an "Options Chain Browser" component — not just auto-mode-switching from search. This is a separate, larger feature.

## 6. Recommendation

### Phase A: Ticker Search + Auto-Switch (~2 hours, micro-MEU)

Covers **futures, forex, crypto**. No new providers needed:
1. Add `instrument_type` to `TickerSearchResult` DTO
2. Remove `FUTURE`/`CURRENCY`/`CRYPTOCURRENCY` from Yahoo's exclusion set
3. Pass `quoteType` through as `instrument_type`
4. Use `instrument_type` in UI instead of regex heuristics

### Phase B: Options Chain Browser (larger MEU, ~1–2 days)

Covers **options**. Yahoo provides the data for free via `/v7/finance/options/{symbol}`:
1. Add `get_options_chain()` method to `MarketDataService`
2. Add `/api/v1/market-data/options/{symbol}` API endpoint
3. Build "Options Chain Browser" UI component (expiration picker, strike table, call/put toggle)
4. Wire auto-switch: when user selects an options contract, switch calculator to options mode
5. No new provider needed — Yahoo covers it. Alpha Vantage / Polygon.io are fallback options for higher reliability.

**Suggested MEU scope**: Phase A is standalone. Phase B should be its own MEU under the Position Calculator feature group.
