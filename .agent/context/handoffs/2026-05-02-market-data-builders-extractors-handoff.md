# Handoff — Market Data Builders & Extractors

**Project:** Phase 8a Layer 2–3 (URL Builders + Extractors + Field Mappings)
**MEUs:** MEU-185, MEU-186, MEU-187, MEU-188
**Date:** 2026-05-02
**Status:** ✅ Implementation complete + corrections applied — ready for Codex validation

---

## Scope Summary

Implemented 10 new URL builders (5 simple-GET + 4 special-pattern + 1 POST scanner) and 22 response extractors with 46 field mapping tuples across 4 MEUs, covering 10 market data providers. **Addenda:** Yahoo OHLCV extractor + TradingView scanner (quote/fundamentals) added from known issues. **Corrections applied:** 14 missing field mappings, 5 missing extractors from review findings.

## Changed Files

| File | Change |
|------|--------|
| `packages/infrastructure/src/zorivest_infra/market_data/url_builders.py` | +10 builder classes (Alpaca, FMP, EODHD, APINinjas, Tradier, AlphaVantage, NasdaqDL, OpenFIGI, SecApi, **TradingView**) |
| `packages/infrastructure/src/zorivest_infra/market_data/response_extractors.py` | +22 extractors (15 original + 5 corrections + **2 TradingView**), CSV fallback, slug hoisting, Yahoo OHLCV, **TradingView column-zip** |
| `packages/infrastructure/src/zorivest_infra/market_data/field_mappings.py` | +10 slug-map entries, +46 field mapping tuples (30+14 corrections + **2 TradingView**), Yahoo OHLCV identity |
| `tests/unit/test_url_builders.py` | +90 tests MEU-185/186, **+6 TradingView builder tests** |
| `tests/unit/test_response_extractors.py` | +55 tests MEU-187/188, +6 Yahoo, +5 corrections, **+4 TradingView extractor tests** |
| `tests/unit/test_field_mappings.py` | +55 tests MEU-187/188, +2 Yahoo, +16 corrections, **+4 TradingView mapping tests** |
| `docs/BUILD_PLAN.md` | MEU-185–188 ⬜→✅, Phase 8a tracker updated, total 139→143 |
| `docs/execution/plans/2026-05-02-market-data-builders-extractors/task.md` | Tasks 1–20 marked `[x]` |
| `.agent/context/known-issues.md` | [MKTDATA-YAHOO-UNOFFICIAL] + [MKTDATA-TRADINGVIEW-NOPUBLICAPI] updated with resolved items and planning needs |

## Quality Gate Evidence

- **pytest**: 2714 passed, 23 skipped, 0 failed (189s)
- **pyright**: 0 errors, 0 warnings
- **ruff**: all checks passed
- **anti-placeholder**: `rg "TODO|FIXME|NotImplementedError" packages/infrastructure/src/zorivest_infra/market_data/` → 0 matches

## Commands Executed

| Command | Result |
|---------|--------|
| `uv run pytest tests/ -x --tb=short -q` | 2714 passed, 23 skipped, 0 failed (189s) |
| `uv run pyright packages/infrastructure/src/zorivest_infra/market_data/` | 0 errors, 0 warnings |
| `uv run ruff check packages/infrastructure/src/zorivest_infra/market_data/` | All checks passed |
| `uv run python tools/validate_codebase.py --scope meu` | 8/8 blocking checks passed |
| `rg "TODO\|FIXME\|NotImplementedError" packages/infrastructure/src/zorivest_infra/market_data/` | 0 matches |

## Key Design Decisions

1. **CSV Fallback (AC-25)**: `extract_records` attempts `csv.DictReader` parsing when `json.loads` fails for Alpha Vantage earnings endpoint
2. **Prefix Stripping**: `_av_strip_prefix` removes inconsistent `1.`/`01.` prefixes from AV JSON keys
3. **Slug Hoisting**: Moved slug computation before the JSON try/except block to fix UnboundLocalError in CSV fallback path
4. **Registry Pattern**: All extractors registered in `_EXTRACTORS` dict keyed by `(slug, data_type)` tuple
5. **Yahoo OHLCV (Addendum)**: Same v8/chart parallel-array zip pattern as Finnhub candles — timestamps + indicators.quote[0] arrays zipped into flat dicts with None preservation for market-closed bars
6. **TradingView Scanner (Addendum)**: Column-zip pattern for scanner `{data: [{s, d}]}` envelope — `d` array values zipped with known column names per data_type. Exchange routing via `criteria["exchange"]` defaulting to `america`. Same POST `RequestSpec` deferral as OpenFIGI/SecApi.

## FAIL_TO_PASS Evidence (Corrections)

**F2/F3 RED phase (30 failures):**
```
30 failed, 15 passed — 14 registry parametrize + 14 functional mapping + 2 MEU-188 parametrize failures
```
**GREEN phase (all passing):**
```
45 passed — all 30 previously failing tests now pass
```

## POST-Body Runtime Deferral (F1)

> **POST wiring (`RequestSpec` → adapter `_do_fetch()`) is explicitly deferred to MEU-189.**
>
> This project (MEU-185–188) delivers the `RequestSpec` dataclass and `build_request()` methods on OpenFIGI/SecApi/TradingView builders. The adapter-level support (`MarketDataProviderAdapter._do_fetch()` → POST dispatch, `fetch_with_cache()` → POST support) is MEU-189 scope per `implementation-plan.md` §2 "Out of Scope".
>
> No runtime POST requests can be issued until MEU-189 is implemented.

## Codex Validation Report

Pending — awaiting `/execution-critical-review` approval before Codex validation handoff.

## Remaining Work

All 20/20 tasks complete. Corrections applied for 3 review findings.

## Next Project

MEU-189 (POST-body runtime wiring: adapter + http_cache POST support for OpenFIGI/SEC API/TradingView) → MEU-190–194 (service methods, routes, pipeline, recipes)

**[MKTDATA-YAHOO-UNOFFICIAL] remaining items** (not in current scope — needs mini-MEU):
- Fundamentals: `/v10/finance/quoteSummary` extractor (medium effort)
- Earnings: quoteSummary modules extractor (medium effort)
- Dividends/Splits: v8/chart `&events=div,split` extraction (medium effort)

**[MKTDATA-TRADINGVIEW-NOPUBLICAPI] remaining items** (needs planning — see known-issues.md):
- POST runtime wiring (MEU-189 blocker)
- Exchange routing strategy (auto-detect vs explicit `criteria.exchange`)
- Rate limiting / multi-ticker batching
- Technicals data type (RSI, MACD scanner columns)
