# Plan Summary: Phase 8a Layer 4 — Service Methods + Polygon Migration (v2)

> **Project**: `2026-05-03-service-methods-layer4`
> **MEUs**: MEU-195 (S), MEU-190 (M), MEU-191 (M)
> **Status**: `draft` — awaiting review
> **Revision**: v2 — Yahoo expansion included (was incorrectly deferred in v1)

---

## Revision Note

> [!IMPORTANT]
> **v1 → v2 change:** Yahoo Finance expansion is now **included** in MEU-190/191 instead of deferred.
>
> **Evidence that deferral was wrong:**
> 1. `known-issues.md` line 78 says *"All piggyback on MEU-190/191"*
> 2. Existing `_yahoo_quote()` pattern (lines 243-301) makes adding Yahoo methods trivial (~20 lines each)
> 3. Yahoo uses private `_yahoo_*()` service methods with direct HTTP — NO new URL builders or extractors needed
> 4. Yahoo field mapping for fundamentals already exists: `(yahoo, fundamentals)` in field_mappings.py line 130

---

## Yahoo Integration Matrix

| Data Type | Yahoo Endpoint | Has Extractor? | Has Field Map? | In-Scope? | MEU |
|---|---|---|---|---|---|
| OHLCV | `v8/finance/chart?range=6mo&interval=1d` | ✅ `_yahoo_ohlcv()` | ✅ `(yahoo, ohlcv)` | ✅ | 190 |
| Fundamentals | `v10/finance/quoteSummary?modules=financialData,defaultKeyStatistics` | ❌ (new private method) | ✅ `(yahoo, fundamentals)` | ✅ | 190 |
| Earnings | `v10/quoteSummary?modules=earningsTrend` | ❌ | ❌ | ❌ Unreliable | — |
| Dividends | `v8/finance/chart?events=div` | ❌ (new private method) | ❌ (new) | ✅ | 191 |
| Splits | `v8/finance/chart?events=split` | ❌ (new private method) | ❌ (new) | ✅ | 191 |
| Insider | — | — | — | ❌ No endpoint | — |
| Econ Calendar | — | — | — | ❌ No endpoint | — |
| Company Profile | — | — | — | ❌ No endpoint | — |

## Project Scope

| MEU | Slug | Scope | Execution Order |
|-----|------|-------|:---:|
| MEU-195 | `polygon-massive-migration` | Update `base_url` + `signup_url` in provider_registry.py | 1 |
| MEU-190 | `service-methods-core` | 3 methods (`get_ohlcv`, `get_fundamentals`, `get_earnings`) + Yahoo OHLCV/fundamentals + 9 API-key normalizers | 2 |
| MEU-191 | `service-methods-extended` | 5 methods (`get_dividends`, `get_splits`, `get_insider`, `get_economic_calendar`, `get_company_profile`) + Yahoo dividends/splits + 15 API-key normalizers | 3 |

## Fallback Chain Design

Each method: **Yahoo first (free)** → **API-key chain (spec-defined)**

| Method | Yahoo? | Primary | Fallback 1 | Fallback 2 |
|--------|:------:|---------|-----------|-----------|
| `get_ohlcv` | ✅ | Alpaca | EODHD | Polygon |
| `get_fundamentals` | ✅ | FMP | EODHD | Alpha Vantage |
| `get_earnings` | ❌ | Finnhub | FMP | Alpha Vantage |
| `get_dividends` | ✅ | Polygon | EODHD | FMP |
| `get_splits` | ✅ | Polygon | EODHD | FMP |
| `get_insider` | ❌ | Finnhub | FMP | SEC API |
| `get_economic_calendar` | ❌ | Finnhub | FMP | Alpha Vantage |
| `get_company_profile` | ❌ | FMP | Finnhub | EODHD |

## Files Changed (~8 files)

| File | MEU | Action |
|------|-----|--------|
| `provider_registry.py` | 195 | Modify — domain swap |
| `market_data_service.py` | 190, 191 | Modify — 8 public methods + 4 Yahoo helpers |
| `normalizers.py` | 190, 191 | Modify — ~24 normalizer functions |
| `test_service_methods.py` | 190, 191 | New — TDD test file (Yahoo + API-key fallback) |
| `test_normalizers.py` | 190, 191 | Modify — normalizer tests |
| `test_provider_registry.py` | 195 | Modify — domain assertions |
| `test_url_builders.py` | 195 | Modify — URL assertions |
| `BUILD_PLAN.md` | all | Modify — status ⬜ → ✅ |

## Task Count: 23

- Tasks 1-2: MEU-195 (Polygon migration)
- Tasks 3-9: MEU-190 (core service methods — TDD, includes Yahoo)
- Tasks 10-16: MEU-191 (extended service methods — TDD, includes Yahoo)
- Tasks 17-23: Verification, BUILD_PLAN audit, handoff, reflection, metrics

## Out of Scope

- Yahoo earnings (no reliable endpoint) `[Research-backed]`
- TradingView expansion (P4 tech debt)
- API routes (MEU-192), MCP actions (MEU-192)
- Pipeline store (MEU-193), scheduling recipes (MEU-194)

## Plan Files

- [implementation-plan.md](file:///p:/zorivest/docs/execution/plans/2026-05-03-service-methods-layer4/implementation-plan.md)
- [task.md](file:///p:/zorivest/docs/execution/plans/2026-05-03-service-methods-layer4/task.md)
