# Market Data Provider Research — Cross-Platform Synthesis

> Synthesized 2026-05-01 from ChatGPT, Claude, and Gemini deep research outputs.
> Status: **Decision-ready** — review findings and approve next steps.
>
---

## Executive Summary

Three AI research platforms independently analyzed all 11 API-key market data providers. The research confirms:

1. **Authentication is solved** — all 11 providers have working auth in the codebase
2. **Data retrieval is NOT wired** — only 3 of 11 providers have URL builders, only 2 have response extractors
3. **Free-tier reality is harsh** — only Alpaca (200/min) and Finnhub (60/min) offer usable free tiers; Alpha Vantage dropped to 25/day, EODHD to 20/day, Polygon to 5/min
4. **No single provider covers everything** — a minimum 4-provider stack is needed for full data coverage

> [!WARNING]
> **Breaking change discovered**: Finnhub `/stock/candle` (OHLCV) returns **403 on free tier since 2024**. Our existing `FinnhubUrlBuilder` for OHLCV will fail. Must use Alpaca/EODHD/Polygon for OHLCV instead.

---

## 1. Consensus Capability Matrix

Cross-referencing all three sources. Legend: ✅ Free, 💰 Paid, ⚠️ Partial/quirky, ❌ Not available.

| data_type | API Ninjas | Alpaca | AlphaVantage | EODHD | FMP | Finnhub | Nasdaq DL | OpenFIGI | Polygon | SEC API | Tradier |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **quote** | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | ✅ |
| **ohlcv** | ✅ | ✅ | ✅ | ✅ | ✅ | 💰⚠️ | ⚠️ | ❌ | ✅ | ❌ | ✅ |
| **news** | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ |
| **fundamentals** | ⚠️ | ❌ | ✅ | ✅ | ✅ | ⚠️ | ❌ | ❌ | ⚠️ | ⚠️ | ⚠️beta |
| **earnings** | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **dividends** | ❌ | ⚠️ | ⚠️ | ✅ | ✅ | 💰 | ❌ | ❌ | ✅ | ❌ | ❌ |
| **splits** | ❌ | ⚠️ | ⚠️ | ✅ | ✅ | 💰 | ❌ | ❌ | ✅ | ❌ | ❌ |
| **options** | ❌ | 💰 | 💰 | 💰 | 💰 | 💰 | ❌ | ❌ | 💰 | ❌ | ✅ |
| **insider** | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ |
| **institutional** | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ |
| **etf_holdings** | ❌ | ❌ | ❌ | ✅ | ✅ | 💰 | ❌ | ❌ | ❌ | ❌ | ❌ |
| **economic_calendar** | ⚠️ | ❌ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ❌ | ⚠️ | ❌ | ❌ |
| **sec_filings** | ✅ | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ |
| **ticker_search** | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ | ✅ |
| **company_profile** | ⚠️ | ❌ | ✅ | ✅ | ✅ | ✅ | ❌ | ⚠️ | ✅ | ⚠️ | ❌ |
| **identifier_mapping** | ❌ | ❌ | ❌ | ✅ | ❌ | ⚠️ | ❌ | ✅ | ⚠️ | ❌ | ❌ |

---

## 2. Best-Source Recommendations (All 3 sources agree)

| Data Type | Primary | Fallback | Rationale |
|---|---|---|---|
| **Quotes (batch)** | **Alpaca** | Tradier, Finnhub | 200/min, multi-symbol, cleanest envelope |
| **OHLCV daily** | **Alpaca** | EODHD, Polygon | Multi-ticker batching, 7yr history on free |
| **News** | **Finnhub** | Alpaca, Polygon | 60/min, free, per-ticker news |
| **Fundamentals** | **FMP** | EODHD, Alpha Vantage | 250/day, broadest fundamental surface |
| **Earnings** | **Finnhub** | FMP, Alpha Vantage | Free calendar + history, 60/min |
| **Dividends** | **Polygon** | EODHD, FMP | Clean API, cursor pagination |
| **Splits** | **Polygon** | EODHD, FMP | Same as dividends — same architecture |
| **Options** | **Tradier** | Polygon (paid) | Free with brokerage, Greeks included |
| **Insider** | **Finnhub** | FMP, SEC API | Free, structured, per-ticker |
| **SEC Filings** | **Finnhub** | FMP, SEC API | Free; SEC API (paid) for Lucene search |
| **Economic Calendar** | **Finnhub** | FMP, Alpha Vantage | Free, structured, impact levels |
| **Ticker Search** | **FMP** | Finnhub, Polygon | Clean array response, multi-exchange |
| **Company Profile** | **FMP** | Finnhub, EODHD | Rich fields: CIK, ISIN, CUSIP, CEO |
| **ID Mapping** | **OpenFIGI** | EODHD | Only dedicated mapping service |

---

## 3. Free-Tier Rate Limits (Verified 2026)

> [!CAUTION]
> Alpha Vantage's free tier dropped to **25/day** (from historical 500→100→25). Multiple sources confirm this. Our `provider_registry.py` may still have stale rate limits.

| Provider | Free Tier | Per-Minute | Notes |
|---|---|---|---|
| API Ninjas | 50K/month | Unspecified | ~1,600/day average |
| **Alpaca** | **200/min** | **200** | Best free tier. IEX feed only, 15-min delay |
| Alpha Vantage | **25/day** | 5 (paid) | Effectively unusable for production |

| EODHD | **20/day** | 1,000 (paid) | Cost-weighted: fundamentals = 10 credits |
| FMP | **250/day** | 300 (paid) | US-only on free; 84 symbols |
| **Finnhub** | **60/min** | **60** | OHLCV candles are premium-only since 2024 |
| Nasdaq DL | 50K/day | 300/10s | But useful free data = mostly macro (FRED) |
| OpenFIGI | 25 req/6s | ~250 | Free with API key, batches of 100 |
| Polygon | **5/min** | **5** | 2yr history, EOD-only, extremely slow |
| SEC API | **100/month** | — | Paid wrapper around EDGAR |
| Tradier | Generous | ~120 | Requires brokerage account |

---

## 4. URL Builder Architecture Families

All three sources agree on 4 distinct builder modes required:

| Mode | Providers | Pattern |
|---|---|---|
| **Simple GET** | API Ninjas, Alpaca, EODHD, FMP, Finnhub, Tradier | `base_url + path + query_params` |
| **Function-Dispatch GET** | Alpha Vantage | `base_url?function=XXX&symbol=YYY` — one base, many functions |
| **Dataset/Table GET** | Nasdaq Data Link | `/datatables/{vendor}/{table}.json` — dataset code is the identity |
| **POST-Body Mapping** | OpenFIGI, SEC API | POST with JSON body array/Lucene query |

> [!IMPORTANT]
> ChatGPT specifically emphasizes: "you should not treat every provider as `base_url + path + query` and we're done." The GenericUrlBuilder currently used for 9 providers will not work for Alpha Vantage, Nasdaq DL, OpenFIGI, or SEC API.

---

## 5. Response Extraction Gotchas (Critical)

All three sources converge on these hard problems:

| Provider | Gotcha | Impact |
|---|---|---|
| **Finnhub candles** | Parallel arrays `{c:[],h:[],l:[],o:[],t:[],v:[]}` — must `zip()` | Custom extractor required |
| **Alpha Vantage OHLCV** | Date-keyed dicts `{"2024-01-01": {"1. open": "150"}}` — must `.items()` iterate | Custom extractor + key prefix stripping |
| **Alpha Vantage earnings calendar** | Returns **CSV bytes** even with `datatype=json` | CSV parser, not JSON |
| **Alpha Vantage rate limit** | HTTP 200 with `{"Note": "..."}` — not a standard 429 | Must inspect response body |
| **Tradier** | Single-result collapses dict→list: `quote: {...}` vs `quote: [...]` | `isinstance(x, list)` guard on every response |
| **EODHD fundamentals** | Nested sections `{General:{}, Highlights:{}, Financials:{}}` | Section-aware flattening |
| **Polygon timestamps** | Millisecond UNIX (`t / 1000` before datetime) | Easy to mix with Finnhub's second-based |
| **Nasdaq DL** | Parallel arrays + `column_names` — must zip | Similar to Finnhub but column-named |
| **OpenFIGI** | v3 renamed `error` to `warning` for no-match | Silent misses if checking `error` key |
| **Alpaca** | Multi-symbol = dict-keyed, single-symbol = flat list | Shape varies by call pattern |

---

## 6. Proposed Canonical Data Schemas

Claude provided complete SQLite schemas. All three sources agree on these canonical field sets:

### OHLCV: `{ticker, timestamp, open, high, low, close, adj_close, volume, vwap, trade_count}`
### Quote: `{ticker, last, bid, ask, bid_size, ask_size, prev_close, change, change_pct, volume, market_cap, timestamp}`
### News: `{id, ticker, headline, summary, body, url, source, author, published_at, image_url, sentiment_score}`
### Fundamentals: `{ticker, market_cap, pe_ratio, pb_ratio, ps_ratio, eps, dividend_yield, beta, sector, industry, employees, ...}`
### Earnings: `{ticker, fiscal_period, fiscal_year, report_date, eps_actual, eps_estimate, eps_surprise, revenue_actual, revenue_estimate}`
### Dividends: `{ticker, dividend_amount, currency, ex_date, record_date, pay_date, declaration_date, frequency}`
### Splits: `{ticker, execution_date, ratio_from, ratio_to}`
### Insider: `{ticker, name, title, transaction_date, transaction_code, shares, price, value, shares_owned_after}`

> [!NOTE]
> Claude's full SQL DDL for 6 tables (ohlcv_daily, fundamentals_snapshot, earnings, corporate_actions, news_articles + news_tickers, economic_calendar) is ready for direct adoption. See [Claude research](file:///p:/zorivest/_inspiration/data-provider-api-expansion-research/claude-Unified%20Market%20Data%20Ingestion%20Layer%20%E2%80%94%20Implementation-Ready%20Spec%20for%2012%20Providers.md#L662-L806).

---

## 7. Provider Capability Registry Schema

ChatGPT proposes extending each provider entry with:

```python
@dataclass
class ProviderCapabilities:
    builder_mode: Literal["simple_get", "function_get", "dataset_get", "post_body"]
    auth_mode: Literal["header", "query", "bearer", "dual_header"]
    multi_symbol_style: Literal["csv", "repeated_filter", "body_array", "none"]
    pagination_style: Literal["offset_limit", "next_page_token", "next_cursor_id", "next_url", "none"]
    extractor_shape: Literal["root_object", "root_array", "wrapper_array", "symbol_keyed_dict", "named_section_object", "parallel_arrays"]
    supported_data_types: list[str]  # ["quote", "ohlcv", "news", ...]
    free_tier: FreeTierConfig  # rate limits, history depth, delay
```

This is the missing piece in `provider_registry.py` — currently has auth config but no capability metadata.

---

## 8. Top 10 Scheduling Recipes (Consensus)

| # | Recipe | Cron | Primary Provider | Fallback |
|---|---|---|---|---|
| 1 | **Nightly OHLCV refresh** | `0 22 * * 1-5` | Alpaca (batch 50/call) | EODHD |
| 2 | **Pre-market quote sweep** | `*/5 4-9 * * 1-5` | Finnhub | Alpaca |
| 3 | **Weekly fundamentals** | `0 6 * * 6` | FMP | Alpha Vantage |
| 4 | **Daily earnings calendar** | `0 5 * * *` | Finnhub | FMP |
| 5 | **Weekly dividend tracker** | `0 7 * * 1` | Polygon | EODHD |
| 6 | **Near-real-time news** | `*/2 6-20 * * 1-5` | Finnhub | Polygon |
| 7 | **Daily insider transactions** | `30 23 * * 1-5` | Finnhub | FMP |
| 8 | **Weekly economic calendar** | `0 6 * * 0` | Finnhub | FMP |
| 9 | **Daily options chain** | `30 15 * * 1-5` | Tradier | Polygon (paid) |
| 10 | **Monthly ETF holdings** | `0 8 1 * *` | FMP | EODHD |
| **+** | **Quarterly ID mapping** | `0 4 1 */3 *` | OpenFIGI | EODHD |

---

## 9. Research Gaps & Unverified Endpoints

> [!WARNING]
> These need manual doc-checks before implementation:

| Provider | Issue | Source |
|---|---|---|
| **Finnhub** | ChatGPT could not resolve official endpoint pages cleanly | ChatGPT |
| **OpenFIGI** | Body schemas and current rate headers not fully extracted | ChatGPT |
| **SEC API** | Not enumerated endpoint-by-endpoint in ChatGPT run | ChatGPT |
| **Polygon** | Docs redirect to `massive.com`; full stock/options matrix incomplete | ChatGPT |
| **EODHD** | Search and options exact REST paths not captured cleanly | ChatGPT |
| **FMP** | Earnings symbol-scoped endpoint may be misrendered in docs | ChatGPT |
| **OpenFIGI v2** | Sunset **July 1, 2026** — returns 410 Gone. Migrate to v3 now | Claude |
| **Alpha Vantage** | EARNINGS_CALENDAR returns CSV, not JSON | Claude |

---

## 10. Codebase Impact Assessment

### Files Requiring Changes

| File | Current State | Required Work |
|---|---|---|
| `url_builders.py` | 3 builders (Yahoo, Polygon, Finnhub) | Add 9 dedicated builders + fix Finnhub OHLCV |
| `response_extractors.py` | 2 providers (Yahoo, Polygon) | Add extractors for all 11 × data_types |
| `field_mappings.py` | 4 mappings (Yahoo, Polygon, Finnhub, generic) | Add ~60+ (provider, data_type) mapping tuples |
| `provider_registry.py` | Auth-only config | Add `ProviderCapabilities` (builder_mode, data_types, etc.) |
| `normalizers.py` | Quote normalizers for 5 providers | Extend to all data_types per provider |
| Database models | No market data tables | Add 6 tables (Claude's DDL) |
| `market_data_service.py` | Stub service | Wire real data-type dispatch |
| API routes | Only quote/news/search | Add ohlcv, fundamentals, earnings, dividends, etc. |

### Estimated Implementation Scope

| Component | MEU Count | Complexity | Dependencies |
|---|---|---|---|
| Provider capability registry | 1 MEU | Low | None |
| URL builders (9 providers) | 2-3 MEUs | Medium | Capability registry |
| Response extractors | 2-3 MEUs | High | URL builders for testing |
| Field mappings | 1 MEU | Low | Extractors defined first |
| Database tables | 1 MEU | Medium | Schema design (Claude DDL) |
| Service wiring | 1-2 MEUs | High | All of the above |
| Scheduling recipes | 1 MEU | Medium | Service wiring complete |
| **Total** | **~9-12 MEUs** | | |

---

## Decision Points for Review

> [!IMPORTANT]
> **These decisions need your input before we can plan:**

### D1: Implementation Strategy
- **Option A**: Full expansion — build all 11 providers × all data_types (~55+ endpoint integrations)
- **Option B**: Tiered rollout — wire the "best source" for each data_type first (6-8 providers × 1 data_type each), then expand
- **Option C**: Core-4 first — Alpaca + Finnhub + FMP + Polygon cover 90% of use cases; wire those, add others later

**Recommendation**: Option B — delivers maximum data coverage with minimum work. The best-source table in §2 is the roadmap.

### D2: Free vs Paid Tier Assumptions
- Should we design only for free tiers (conservative rate limiting)?
- Or assume paid plans will be acquired for key providers (FMP Starter, Polygon Stocks Starter)?
- This affects batch sizes, polling intervals, and fallback chain design.

### D3: Database Tables
- Adopt Claude's 6-table DDL as-is?
- Or fold into existing SQLAlchemy models with Alembic migrations?
- The corporate_actions table (dividends + splits combined) vs separate tables?

### D4: Scheduling Engine Integration
- Wire recipes directly into the existing pipeline policy system?
- Or build a "market data refresh" subsystem that feeds the pipeline?

### D5: Immediate Fixes
- Fix `FinnhubUrlBuilder` to remove OHLCV candle (403 on free) — **do this now?**
- Update `provider_registry.py` rate limits (Alpha Vantage 25/day) — **do this now?**
