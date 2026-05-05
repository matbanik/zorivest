---
project: "2026-05-03-service-methods-layer4"
date: "2026-05-03"
source: "docs/build-plan/08a-market-data-expansion.md §8a.9, §8a.10; .agent/context/known-issues.md §MKTDATA-POLYGON-REBRAND"
meus: ["MEU-195", "MEU-190", "MEU-191"]
status: "draft"
template_version: "2.0"
---

# Implementation Plan: Phase 8a Layer 4 — Service Methods + Polygon Migration

> **Project**: `2026-05-03-service-methods-layer4`
> **Build Plan Section(s)**: [08a §8a.9](../../../build-plan/08a-market-data-expansion.md#step-8a9-core-service-methods-meu-190-service-methods-core), [08a §8a.10](../../../build-plan/08a-market-data-expansion.md#step-8a10-extended-service-methods-meu-191-service-methods-extended), [known-issues.md §MKTDATA-POLYGON-REBRAND](../../../.agent/context/known-issues.md) (MEU-195)
> **Status**: `draft`

---

## Goal

Implement Layer 4 of the Phase 8a market data expansion: 8 new service methods on `MarketDataService` with per-provider normalizer functions and fallback chains, plus the Polygon.io → Massive.com domain migration. The 08a spec tables (§8a.9, §8a.10) define the API-key provider fallback chains. Where Yahoo Finance supports a data type, the existing MEU-91 Local Canon pattern (try Yahoo first — free, no API key — then fall through to the API-key chain) is applied. This connects the URL builders (Layer 2) and extractors (Layer 3) to the application service layer, making all 8 new market data types programmatically available for downstream consumers (API routes, MCP, pipeline).

---

## User Review Required

> [!IMPORTANT]
> **Yahoo Finance as First-Try Fallback**: The existing `get_quote()` and `search_ticker()` methods already try Yahoo first before API-key providers (lines 98-113, 168-183 of `market_data_service.py`). New service methods will follow the same pattern where Yahoo supports the data type: OHLCV, fundamentals, dividends, and splits. Yahoo earnings is excluded — no clean endpoint exists (v10/quoteSummary `earningsTrend` module is unreliable). This is documented in [MKTDATA-YAHOO-UNOFFICIAL] known-issues.md line 78: *"All piggyback on MEU-190/191."*
>
> **Massive.com Display Name**: MEU-195 will update `base_url` and `signup_url` but keep the provider key as `"Polygon.io"` for backward compatibility with stored API keys and provider settings. A comment will note the rebrand.

---

## Proposed Changes

### MEU-195: Polygon.io → Massive.com Domain Migration + API Integration Hardening

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-195-1 | `base_url` updated from `https://api.polygon.io/v2` to `https://api.massive.com` (no `/v2` — version prefixes moved to URL builder paths) | `Spec` — known-issues.md [MKTDATA-POLYGON-REBRAND] | Old domain reference must not appear |
| AC-195-2 | `signup_url` updated from `https://polygon.io/pricing` to `https://massive.com/pricing` | `Spec` — known-issues.md | — |
| AC-195-3 | Provider key remains `"Polygon.io"` for backward compatibility | `Local Canon` — provider_registry.py pattern | — |
| AC-195-4 | All existing tests pass with new domain values | `Local Canon` | — |
| AC-195-5 | Auth method switched from `BEARER_HEADER` to `QUERY_PARAM` with `auth_param_name="apiKey"` | `Research-backed` — Massive REST API Quickstart docs | Connection test fails with bearer auth |
| AC-195-6 | `test_endpoint` updated to `/v3/reference/tickers?limit=1&apiKey={api_key}` (free-tier compatible) | `Research-backed` — Free plan tier testing | Old `/aggs/` endpoint returns 403 on free plan |
| AC-195-7 | `config.name` set to `"Massive"` (display name) while dict key stays `"Polygon.io"` | `Human-approved` — user requested "Massive" display | — |
| AC-195-8 | `display_name` field added to `ProviderStatus` DTO, populated from `config.name` when it differs from provider key | `Local Canon` — DTO pattern | `display_name` is `None` when name matches key |
| AC-195-9 | GUI sidebar and detail header render `display_name` via `label()` helper | `Human-approved` | — |
| AC-195-10 | `PolygonUrlBuilder` paths updated with `/v2/` and `/v3/` version prefixes, plus dividends/splits endpoints | `Research-backed` — Massive API versioned endpoints | — |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| Domain swap | Spec | known-issues.md + 08a build plan |
| Display name vs key separation | Human-approved | User requested "Massive" display, keep "Polygon.io" key for DB compat |
| Auth method change | Research-backed | Massive REST Quickstart uses `?apiKey=` query param |
| Test endpoint change | Research-backed | `/v3/reference/tickers` available on all plans including free |
| URL builder version prefixes | Research-backed | Endpoints use mixed versions: `/v2/aggs`, `/v2/snapshot`, `/v3/reference` |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/infrastructure/src/zorivest_infra/market_data/provider_registry.py` | modify | Update `base_url`, `signup_url`, `auth_method`, `test_endpoint`, `config.name`, `headers_template` |
| `packages/infrastructure/src/zorivest_infra/market_data/url_builders.py` | modify | Add `/v2/`+`/v3/` version prefixes to PolygonUrlBuilder paths, add dividends/splits endpoints |
| `packages/core/src/zorivest_core/application/provider_status.py` | modify | Add `display_name: str \| None` field to ProviderStatus DTO |
| `packages/core/src/zorivest_core/services/provider_connection_service.py` | modify | Populate `display_name` from config.name when it differs from provider key |
| `ui/src/renderer/src/features/settings/MarketDataProvidersPage.tsx` | modify | Add `display_name` to TS interface, `label()` helper for sidebar/header rendering |
| `tests/unit/test_provider_registry.py` | modify | Update assertions for new display name and auth method |
| `tests/unit/test_url_builders.py` | modify | Update URL assertion strings with version prefixes and no-`/v2` base URL |

---

### MEU-190: Core Service Methods

3 high-value methods with Yahoo-first + API-key provider fallback chains.

#### Yahoo Integration Pattern (Local Canon)

The existing `get_quote()` (line 98) establishes the canonical pattern:
1. Try `_yahoo_quote()` first — free, no API key, no provider settings needed
2. On failure/empty, fall through to `_get_enabled_providers()` → API-key chain
3. Yahoo methods are private `_yahoo_{data_type}()` methods with direct HTTP calls

New Yahoo private methods follow the same pattern:
- `_yahoo_ohlcv(ticker, interval)` — `v8/finance/chart/{ticker}?range=6mo&interval={interval}` (extractor already exists)
- `_yahoo_fundamentals(ticker)` — `v10/finance/quoteSummary/{ticker}?modules=financialData,defaultKeyStatistics`
- No Yahoo earnings — endpoint unreliable `[Research-backed]`

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-190-1 | `get_ohlcv(ticker, interval)` tries Yahoo first, then Alpaca → EODHD → Polygon | `Spec` — 08a §8a.9 (API-key chain) + `Local Canon` — MEU-91 Yahoo-first pattern | Empty list when all providers fail |
| AC-190-2 | `get_fundamentals(ticker)` tries Yahoo first, then FMP → EODHD → Alpha Vantage | `Spec` — 08a §8a.9 (API-key chain) + `Local Canon` — MEU-91 Yahoo-first pattern | None/empty when all providers fail |
| AC-190-3 | `get_earnings(ticker)` uses Finnhub → FMP → Alpha Vantage (no Yahoo) | `Spec` — 08a §8a.9 | Empty list when all providers fail |
| AC-190-4 | `_yahoo_ohlcv()` returns `list[OHLCVBar]` from `v8/finance/chart` | `Local Canon` — Yahoo extractor exists | None on HTTP error or empty response |
| AC-190-5 | `_yahoo_fundamentals()` returns `FundamentalsSnapshot` from `v10/finance/quoteSummary` | `Local Canon` + `Research-backed` — v10 endpoint documented in known-issues.md | None on HTTP error or empty response |
| AC-190-6 | Each method has per-provider normalizer functions (API-key providers) | `Spec` — 08a §8a.9 | TypeError on malformed input |
| AC-190-7 | Provider selection uses `ProviderCapabilities` registry to verify data type support | `Local Canon` — provider_capabilities.py (MEU-184) | Skip provider if data type not in `supported_data_types` |
| AC-190-8 | Fallback chain logs provider failures and continues to next provider | `Local Canon` — existing get_quote() pattern | — |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| Method signatures | Spec | 08a §8a.9 + ports.py MarketDataPort |
| API-key provider chains | Spec | 08a §8a.9 table (primary + 2 fallbacks per method) |
| Yahoo-first pattern | Local Canon | market_data_service.py `get_quote()` lines 98-113 |
| Yahoo OHLCV endpoint | Local Canon | Extractor `_yahoo_ohlcv()` exists in response_extractors.py:110 |
| Yahoo fundamentals endpoint | Research-backed | v10/quoteSummary with `financialData,defaultKeyStatistics` modules; documented in known-issues.md [MKTDATA-YAHOO-UNOFFICIAL] |
| No Yahoo earnings | Research-backed | v10/quoteSummary `earningsTrend` module is unreliable — no consistent earnings calendar |
| Normalizer pattern | Local Canon | normalizers.py — existing `normalize_{provider}_quote()` functions |
| Error handling | Local Canon | Existing methods return empty list / raise on total failure |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/core/src/zorivest_core/services/market_data_service.py` | modify | Add `get_ohlcv()`, `get_fundamentals()`, `get_earnings()` + `_yahoo_ohlcv()`, `_yahoo_fundamentals()` |
| `packages/infrastructure/src/zorivest_infra/market_data/normalizers.py` | modify | Add ~9 normalizer functions (3 providers × 3 data types) |
| `tests/unit/test_service_methods.py` | new | TDD tests for all 3 methods + Yahoo + normalizers with mocked HTTP |
| `tests/unit/test_normalizers.py` | modify | Add normalizer unit tests for new functions |

---

### MEU-191: Extended Service Methods

5 additional methods following the same Yahoo-first + API-key chain pattern.

#### Yahoo Integration

- `_yahoo_dividends(ticker)` — `v8/finance/chart/{ticker}?range=5y&interval=1d&events=div` (events in chart response)
- `_yahoo_splits(ticker)` — `v8/finance/chart/{ticker}?range=10y&interval=1d&events=split` (events in chart response)
- No Yahoo insider, economic_calendar, or company_profile — no endpoints available

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-191-1 | `get_dividends(ticker)` tries Yahoo first, then Polygon → EODHD → FMP | `Spec` — 08a §8a.10 (API-key chain) + `Local Canon` — MEU-91 Yahoo-first pattern | Empty list when all providers fail |
| AC-191-2 | `get_splits(ticker)` tries Yahoo first, then Polygon → EODHD → FMP | `Spec` — 08a §8a.10 (API-key chain) + `Local Canon` — MEU-91 Yahoo-first pattern | Empty list when all providers fail |
| AC-191-3 | `get_insider(ticker)` uses Finnhub → FMP → SEC API (no Yahoo) | `Spec` — 08a §8a.10 | Empty list when all providers fail |
| AC-191-4 | `get_economic_calendar()` uses Finnhub → FMP → Alpha Vantage (no Yahoo) | `Spec` — 08a §8a.10 | Empty list when all providers fail |
| AC-191-5 | `get_company_profile(ticker)` uses FMP → Finnhub → EODHD (no Yahoo) | `Spec` — 08a §8a.10 | None/empty when all providers fail |
| AC-191-6 | `_yahoo_dividends()` returns `list[DividendRecord]` from `v8/chart?events=div` | `Local Canon` + `Research-backed` — chart events endpoint | None on HTTP error or empty response |
| AC-191-7 | `_yahoo_splits()` returns `list[StockSplit]` from `v8/chart?events=split` | `Local Canon` + `Research-backed` — chart events endpoint | None on HTTP error or empty response |
| AC-191-8 | Each method has per-provider normalizer functions | `Spec` — 08a §8a.10 | TypeError on malformed input |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| Method signatures | Spec | 08a §8a.10 + ports.py |
| API-key provider chains | Spec | 08a §8a.10 table |
| Yahoo dividends endpoint | Research-backed | v8/chart `?events=div` returns `events.dividends` in chart response |
| Yahoo splits endpoint | Research-backed | v8/chart `?events=split` returns `events.splits` in chart response |
| No Yahoo insider/calendar/profile | Research-backed | No Yahoo endpoints for these data types |
| Normalizer pattern | Local Canon | Same as MEU-190 |
| SEC API POST handling | Local Canon | MEU-189 POST runtime already supports SEC API |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/core/src/zorivest_core/services/market_data_service.py` | modify | Add 5 methods + `_yahoo_dividends()`, `_yahoo_splits()` |
| `packages/infrastructure/src/zorivest_infra/market_data/normalizers.py` | modify | Add ~15 normalizer functions (3 providers × 5 data types) |
| `tests/unit/test_service_methods.py` | modify | Add TDD tests for all 5 methods + Yahoo + normalizers |
| `tests/unit/test_normalizers.py` | modify | Add normalizer unit tests |

---

## Out of Scope

- Yahoo earnings (no reliable endpoint — `v10/quoteSummary?modules=earningsTrend` is unreliable) `[Research-backed]`
- TradingView expansion items (exchange routing, batching) — P4 tech debt
- API routes for new data types (MEU-192 — Layer 5)
- MCP action mappings (MEU-192 — Layer 5)
- Pipeline store step (MEU-193 — Layer 6)
- Scheduling recipes (MEU-194 — Layer 6)

---

## BUILD_PLAN.md Audit

This project completes 3 MEUs in the `P1.5a: Market Data Expansion (Phase 8a)` table (lines 291-293). After execution:
- MEU-195 row: ⬜ → ✅
- MEU-190 row: ⬜ → ✅
- MEU-191 row: ⬜ → ✅

Validation:
```powershell
# Verify status updates applied
rg "MEU-195|MEU-190|MEU-191" docs/BUILD_PLAN.md  # Expected: 3 rows with ✅
```

No other BUILD_PLAN.md sections are affected (no API routes, no MCP, no GUI changes).

---

## Verification Plan

### 1. Unit Tests
```powershell
uv run pytest tests/unit/test_service_methods.py tests/unit/test_normalizers.py -x --tb=short -v *> C:\Temp\zorivest\pytest-svc.txt; Get-Content C:\Temp\zorivest\pytest-svc.txt | Select-Object -Last 40
```

### 2. Full Regression
```powershell
uv run pytest tests/ -x --tb=short -v *> C:\Temp\zorivest\pytest-full.txt; Get-Content C:\Temp\zorivest\pytest-full.txt | Select-Object -Last 40
```

### 3. Type Check
```powershell
uv run pyright packages/ *> C:\Temp\zorivest\pyright.txt; Get-Content C:\Temp\zorivest\pyright.txt | Select-Object -Last 30
```

### 4. Lint
```powershell
uv run ruff check packages/ *> C:\Temp\zorivest\ruff.txt; Get-Content C:\Temp\zorivest\ruff.txt | Select-Object -Last 20
```

### 5. Anti-Placeholder Scan
```powershell
rg "TODO|FIXME|NotImplementedError" packages/core/src/zorivest_core/services/market_data_service.py packages/infrastructure/src/zorivest_infra/market_data/normalizers.py *> C:\Temp\zorivest\placeholder.txt; Get-Content C:\Temp\zorivest\placeholder.txt
```

### 6. MEU Gate
```powershell
uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate.txt; Get-Content C:\Temp\zorivest\validate.txt | Select-Object -Last 50
```

### 7. Polygon Domain Verification
```powershell
rg "api.polygon.io" packages/ tests/ *> C:\Temp\zorivest\polygon-check.txt; Get-Content C:\Temp\zorivest\polygon-check.txt  # Expected: 0 matches
```

---

## Open Questions

> [!WARNING]
> **None.** All behaviors resolved from Spec, Local Canon, or Research-backed sources. Yahoo earnings deferred per research (no reliable endpoint).

---

## Research References

- [08a-market-data-expansion.md](../../build-plan/08a-market-data-expansion.md) `[Spec]`
- [known-issues.md §MKTDATA-YAHOO-UNOFFICIAL](../../../.agent/context/known-issues.md) `[Local Canon]` — "All piggyback on MEU-190/191"
- [market-data-research-synthesis.md](../../../_inspiration/data-provider-api-expansion-research/market-data-research-synthesis.md) `[Spec]`
- [issue-triage-report.md](../../../.agent/context/issue-triage-report.md) `[Local Canon]` — triage batch 1 approval
