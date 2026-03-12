# Market Data Service + API + MCP Tools

> Project: `market-data-service-api-mcp`
> MEUs: 61 (MarketDataService), 63 (REST API), 64 (MCP tools)
> Date: 2026-03-11
> Build Plan: [08-market-data.md](../../../build-plan/08-market-data.md) §8.3b, §8.3c, §8.4; [05e-mcp-market-data.md](../../../build-plan/05e-mcp-market-data.md)

---

## Proposed Changes

### MEU-61: MarketDataService + Response Normalizers (bp08 §8.3b + §8.3c)

#### [NEW] [normalizers.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/market_data/normalizers.py)

Response normalizers converting provider-specific JSON → domain DTOs:

- `normalize_alpha_vantage_quote(data)` → `MarketQuote`
- `normalize_polygon_quote(data)` → `MarketQuote`
- `normalize_finnhub_quote(data)` → `MarketQuote`
- `normalize_eodhd_quote(data)` → `MarketQuote`
- `normalize_api_ninjas_quote(data)` → `MarketQuote`
- `normalize_fmp_search(data)` → `list[TickerSearchResult]`
- `normalize_sec_filing(data)` → `list[SecFiling]`
- `normalize_benzinga_news(data)` → `list[MarketNewsItem]`
- `normalize_finnhub_news(data)` → `list[MarketNewsItem]`

Each normalizer handles the provider's unique JSON structure with safe defaults for missing fields.

#### [NEW] [market_data_service.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/market_data_service.py)

Core service implementing `MarketDataPort` with:

- `get_quote(ticker)` — provider fallback chain, returns first successful `MarketQuote` (implements `MarketDataPort.get_quote`)
- `get_news(ticker, count)` — queries news-capable providers (Finnhub, Benzinga) (implements `MarketDataPort.get_news`)
- `search_ticker(query)` — queries search-capable providers (FMP, Alpha Vantage)
- `get_sec_filings(ticker)` — SEC API only

**Architecture**:
- Protocol-based DI (same pattern as `ProviderConnectionService`): `HttpClient`, `EncryptionService`, `RateLimiterProtocol`
- Provider fallback: tries enabled providers in priority order, catches errors, logs failures with redacted keys
- Uses existing `PROVIDER_REGISTRY` for config, `RateLimiter` for throttling, normalizers for response conversion
- **Normalizer composition:** `MarketDataService` (core) accepts a `normalizer_registry: dict[str, Callable]` via constructor injection. The infra layer provides the registry mapping provider names to normalizer functions. This follows the same pattern as `provider_registry: dict[str, ProviderConfig]` in `ProviderConnectionService`.
- Core layer owns the service interface; infra layer owns normalizers (matches existing `core→infra` boundary)

#### [NEW] [test_normalizers.py](file:///p:/zorivest/tests/unit/test_normalizers.py)

Unit tests for all 9 normalizer functions with fixture JSON data per provider.

#### [NEW] [test_market_data_service.py](file:///p:/zorivest/tests/unit/test_market_data_service.py)

Unit tests for `MarketDataService`:
- Quote retrieval with mocked HTTP (single provider, fallback chain)
- News retrieval (Finnhub, Benzinga)
- Ticker search (FMP, Alpha Vantage)
- SEC filings
- Error handling: all providers fail, rate limiting, timeouts
- Provider ordering: only enabled providers with keys

---

### MEU-63: Market Data REST API (bp08 §8.4)

#### [NEW] [market_data.py](file:///p:/zorivest/packages/api/src/zorivest_api/routes/market_data.py)

8 FastAPI routes under `/api/v1/market-data/`:

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/quote` | Get stock quote |
| `GET` | `/news` | Get market news |
| `GET` | `/search` | Search tickers |
| `GET` | `/sec-filings` | Get SEC filings |
| `GET` | `/providers` | List providers |
| `PUT` | `/providers/{name}` | Configure provider (PATCH semantics) |
| `POST` | `/providers/{name}/test` | Test connection |
| `DELETE` | `/providers/{name}/key` | Remove API key |

Pydantic request/response schemas: `ProviderConfigRequest` (all optional fields).

#### [MODIFY] [dependencies.py](file:///p:/zorivest/packages/api/src/zorivest_api/dependencies.py)

Add two new dependency providers:
- `get_market_data_service` → resolve `MarketDataService` from `app.state`
- `get_provider_connection_service` → resolve `ProviderConnectionService` from `app.state`

#### [MODIFY] [main.py](file:///p:/zorivest/packages/api/src/zorivest_api/main.py)

Register `market_data_router` in the FastAPI app factory (`create_app()` at L81). Wire `MarketDataService` and `ProviderConnectionService` into `app.state` in `lifespan()` (L57-76).

#### [NEW] [test_market_data_api.py](file:///p:/zorivest/tests/unit/test_market_data_api.py)

REST API tests via `TestClient`:
- All 8 endpoints with mocked services
- Error responses (404, 422, 500)
- Provider configuration PATCH semantics
- Connection test success/failure

---

### MEU-64: Market Data MCP Tools (bp05e)

#### [NEW] [market-data-tools.ts](file:///p:/zorivest/mcp-server/src/tools/market-data-tools.ts)

7 MCP tools using `registerTool()` with `_meta.toolset: "market-data"`:

| Tool | Annotations | Middleware |
|------|-----------|------------|
| `get_stock_quote` | readOnly, idempotent | withMetrics |
| `get_market_news` | readOnly, idempotent | withMetrics |
| `search_ticker` | readOnly, idempotent | withMetrics |
| `get_sec_filings` | readOnly, idempotent | withMetrics |
| `list_market_providers` | readOnly, idempotent | withMetrics |
| `test_market_provider` | readOnly, idempotent | withMetrics |
| `disconnect_market_provider` | destructive | withMetrics, withGuard, withConfirmation |

All read-only tools use `withMetrics` only.
`disconnect_market_provider` is destructive: uses full middleware chain + `confirm_destructive` parameter.

#### [MODIFY] [seed.ts](file:///p:/zorivest/mcp-server/src/toolsets/seed.ts)

Update `market-data` toolset entry (L156-182): replace `register: () => []` with `registerMarketDataTools`, expand `tools[]` from 4 to 7 (add `list_market_providers`, `test_market_provider`, `disconnect_market_provider`), rename stale `search_tickers` → `search_ticker` (L170).

#### [NEW] [market-data-tools.test.ts](file:///p:/zorivest/mcp-server/tests/market-data-tools.test.ts)

Vitest tests with mocked `fetch()`:
- All 7 tools exercise the correct REST endpoint
- `disconnect_market_provider` requires `confirm_destructive: true`
- Error responses propagated correctly

---

### BUILD_PLAN.md Updates (Phase 8 Completion Tracking)

#### [MODIFY] [BUILD_PLAN.md](file:///p:/zorivest/docs/BUILD_PLAN.md)

- Update MEU-61, MEU-63, MEU-64 status from ⬜ to ✅
- Fix MEU-64 description: "6 tools" → "7 tools"
- Fix stale MEU Summary counts:
  - Phase 5: 1 → 12 completed
  - Phase 8: 0 → 9 completed (6 current + 3 new)
  - Total Completed count in summary row

---

## Spec Sufficiency

### MEU-61: MarketDataService

| Behavior / Contract | Source Type | Source | Resolved? | Notes |
|---|---|---|---|---|
| `get_quote` with provider fallback | Spec | [08-market-data.md §8.3b](../../../build-plan/08-market-data.md) | ✅ | Implements `MarketDataPort.get_quote` |
| `get_news` from Finnhub/Benzinga | Spec | [08-market-data.md §8.3b](../../../build-plan/08-market-data.md) | ✅ | Implements `MarketDataPort.get_news` |
| `search_ticker` from FMP/Alpha Vantage | Spec | [08-market-data.md §8.3b](../../../build-plan/08-market-data.md) | ✅ | |
| `get_sec_filings` from SEC API | Spec | [08-market-data.md §8.3b](../../../build-plan/08-market-data.md) | ✅ | |
| Normalizer JSON→DTO mapping per provider | Spec | [08-market-data.md §8.3c](../../../build-plan/08-market-data.md) | ✅ | Sample data shown in spec |
| Rate limiter integration | Local Canon | MEU-62 `rate_limiter.py` | ✅ | `wait_if_needed()` protocol |
| Log redaction during HTTP calls | Local Canon | MEU-62 `log_redaction.py` | ✅ | `sanitize_url_for_logging` |
| Protocol-based DI | Local Canon | MEU-60 `provider_connection_service.py` | ✅ | Same `HttpClient`, `EncryptionService` protocols |
| Core↔Infra boundary | Local Canon | AGENTS.md §Architecture | ✅ | Service in core, normalizers in infra |
| Normalizer injection composition | Local Canon | `ProviderConnectionService` pattern | ✅ | Constructor-injected `normalizer_registry: dict[str, Callable]` |

### MEU-63: Market Data REST API

| Behavior / Contract | Source Type | Source | Resolved? | Notes |
|---|---|---|---|---|
| 8 REST endpoints | Spec | [08-market-data.md §8.4](../../../build-plan/08-market-data.md) | ✅ | Code shown |
| `ProviderConfigRequest` PATCH semantics | Spec | [08-market-data.md §8.4](../../../build-plan/08-market-data.md) | ✅ | All fields optional |
| `require_unlocked_db` dependency | Local Canon | `dependencies.py` pattern | ✅ | Existing pattern |
| FMP 403 "Legacy Endpoint" → valid key | Spec | [08-market-data.md §8.6](../../../build-plan/08-market-data.md) | ✅ | Already handled in MEU-60 |

### MEU-64: Market Data MCP Tools

| Behavior / Contract | Source Type | Source | Resolved? | Notes |
|---|---|---|---|---|
| 7 tool definitions | Spec | [05e-mcp-market-data.md](../../../build-plan/05e-mcp-market-data.md) | ✅ | Full tool specs |
| Annotations per tool | Spec | [05e-mcp-market-data.md](../../../build-plan/05e-mcp-market-data.md) | ✅ | readOnly/destructive/idempotent |
| `_meta.toolset: "market-data"` | Spec | [05e-mcp-market-data.md](../../../build-plan/05e-mcp-market-data.md) | ✅ | |
| `confirm_destructive` on `disconnect_market_provider` | Spec | [05e-mcp-market-data.md](../../../build-plan/05e-mcp-market-data.md) | ✅ | `z.literal(true)` |
| `withMetrics`/`withGuard`/`withConfirmation` middleware | Local Canon | `trade-tools.ts` pattern | ✅ | Established in MEU-31 |
| `fetchApi` utility | Local Canon | `api-client.ts` | ✅ | Existing shared utility |

---

## Feature Intent Contracts (FICs)

### FIC-61: MarketDataService

| AC | Description | Source |
|----|-------------|--------|
| AC-1 | `get_quote("AAPL")` returns `MarketQuote` from the first enabled provider with key | Spec |
| AC-2 | If first provider fails (HTTP error/timeout), falls through to next enabled provider | Spec |
| AC-3 | If all providers fail, raises `MarketDataError` with last error message | Spec |
| AC-4 | `get_news(None, 5)` returns `list[MarketNewsItem]` from Finnhub or Benzinga | Spec |
| AC-5 | `get_news("AAPL", 3)` filters news by ticker | Spec |
| AC-6 | `search_ticker("Apple")` returns `list[TickerSearchResult]` from FMP or Alpha Vantage | Spec |
| AC-7 | `get_sec_filings("AAPL")` returns `list[SecFiling]` from SEC API | Spec |
| AC-8 | Rate limiter `wait_if_needed()` is called before every HTTP request | Local Canon |
| AC-9 | API keys are decrypted from DB settings before injection into HTTP request | Local Canon |
| AC-10 | All normalizers handle missing/null fields gracefully with None defaults | Spec |
| AC-11 | Normalizer: Alpha Vantage `Global Quote` → `MarketQuote` (9 field mapping) | Spec |
| AC-12 | Normalizer: Polygon `results[0]` → `MarketQuote` | Spec |
| AC-13 | Normalizer: Finnhub `{c, o, h, l, pc}` → `MarketQuote` | Spec |
| AC-14 | Normalizer: Benzinga `data[]` → `list[MarketNewsItem]` | Spec |
| AC-15 | Normalizer: Finnhub `[{...}]` → `list[MarketNewsItem]` | Spec |
| AC-16 | Normalizer: FMP `[{symbol, name, ...}]` → `list[TickerSearchResult]` | Spec |
| AC-17 | Normalizer: SEC API `[{ticker, cik, ...}]` → `list[SecFiling]` | Spec |
| AC-18 | Log redaction: API keys never appear in log output during HTTP calls | Local Canon |

### FIC-63: Market Data REST API

| AC | Description | Source |
|----|-------------|--------|
| AC-1 | `GET /api/v1/market-data/quote?ticker=AAPL` returns MarketQuote JSON | Spec |
| AC-2 | `GET /api/v1/market-data/news` returns list of MarketNewsItem JSON | Spec |
| AC-3 | `GET /api/v1/market-data/search?query=Apple` returns list of TickerSearchResult JSON | Spec |
| AC-4 | `GET /api/v1/market-data/sec-filings?ticker=AAPL` returns list of SecFiling JSON | Spec |
| AC-5 | `GET /api/v1/market-data/providers` returns all 12 providers with status | Spec |
| AC-6 | `PUT /api/v1/market-data/providers/{name}` applies PATCH semantics (omitted fields unchanged) | Spec |
| AC-7 | `POST /api/v1/market-data/providers/{name}/test` returns `{success, message}` | Spec |
| AC-8 | `DELETE /api/v1/market-data/providers/{name}/key` returns `{status: "removed"}` | Spec |
| AC-9 | All data routes (quote/news/search/sec) require unlocked DB | Local Canon |
| AC-10 | Missing query params return 422 | Local Canon |

### FIC-64: Market Data MCP Tools

| AC | Description | Source |
|----|-------------|--------|
| AC-1 | `get_stock_quote` calls `GET /market-data/quote?ticker=` | Spec |
| AC-2 | `get_market_news` calls `GET /market-data/news` with optional ticker + count | Spec |
| AC-3 | `search_ticker` calls `GET /market-data/search?query=` with URL encoding | Spec |
| AC-4 | `get_sec_filings` calls `GET /market-data/sec-filings?ticker=` | Spec |
| AC-5 | `list_market_providers` calls `GET /market-data/providers` with no input | Spec |
| AC-6 | `test_market_provider` calls `POST /market-data/providers/{name}/test` | Spec |
| AC-7 | `disconnect_market_provider` requires `confirm_destructive: true` and calls `DELETE /market-data/providers/{name}/key` | Spec |
| AC-8 | All tools have correct `annotations` and `_meta.toolset: "market-data"` | Spec |
| AC-9 | All tools return `{content: [{type: "text", text: JSON}]}` | Local Canon |
| AC-10 | Read-only tools use `withMetrics` only; destructive tool uses full middleware chain | Local Canon |

---

## Task Table

| # | Task | owner_role | Deliverable | Validation | Status |
|---|------|------------|-------------|------------|--------|
| 0 | Scope project, verify specs, create plan | orchestrator | `implementation-plan.md` | `Test-Path docs/execution/plans/2026-03-11-market-data-service-api-mcp/implementation-plan.md` | ⬜ |
| 1 | Write normalizer tests (RED) | coder | `test_normalizers.py` | `uv run pytest tests/unit/test_normalizers.py -v` — all FAIL | ⬜ |
| 2 | Implement normalizers | coder | `normalizers.py` | `uv run pytest tests/unit/test_normalizers.py -v` — all PASS | ⬜ |
| 3 | Write MarketDataService tests (RED) | coder | `test_market_data_service.py` | `uv run pytest tests/unit/test_market_data_service.py -v` — all FAIL | ⬜ |
| 4 | Implement MarketDataService | coder | `market_data_service.py` | `uv run pytest tests/unit/test_market_data_service.py -v` — all PASS | ⬜ |
| 5 | Create MEU-61 handoff | coder | `050-2026-03-11-market-data-service-bp08s8.3.md` | `Test-Path .agent/context/handoffs/050-2026-03-11-market-data-service-bp08s8.3.md` | ⬜ |
| 6 | Write REST API tests (RED) | coder | `test_market_data_api.py` | `uv run pytest tests/unit/test_market_data_api.py -v` — all FAIL | ⬜ |
| 7 | Add dependencies + register router + wire lifespan | coder | `dependencies.py`, `main.py` | `uv run python -c "from zorivest_api.dependencies import get_market_data_service, get_provider_connection_service"` | ⬜ |
| 8 | Implement market data routes | coder | `market_data.py` | `uv run pytest tests/unit/test_market_data_api.py -v` — all PASS | ⬜ |
| 9 | Create MEU-63 handoff | coder | `051-2026-03-11-market-data-api-bp08s8.4.md` | `Test-Path .agent/context/handoffs/051-2026-03-11-market-data-api-bp08s8.4.md` | ⬜ |
| 10 | Write MCP tool tests (RED) | coder | `market-data-tools.test.ts` | `cd mcp-server; npx vitest run tests/market-data-tools.test.ts` — all FAIL | ⬜ |
| 11 | Implement MCP tools + update seed.ts | coder | `market-data-tools.ts`, `seed.ts` | `cd mcp-server; npx vitest run tests/market-data-tools.test.ts` — all PASS | ⬜ |
| 12 | Create MEU-64 handoff | coder | `052-2026-03-11-market-data-mcp-bp05es5e.md` | `Test-Path .agent/context/handoffs/052-2026-03-11-market-data-mcp-bp05es5e.md` | ⬜ |
| 13 | Run MEU gate | tester | Pass/fail evidence | `uv run python tools/validate_codebase.py --scope meu` | ⬜ |
| 14 | Update `meu-registry.md` | coder | 3 new MEU rows | `rg -c "MEU-61\|MEU-63\|MEU-64" .agent/context/meu-registry.md` | ⬜ |
| 15 | Update `BUILD_PLAN.md` | coder | Status ✅ for MEU-61/63/64 + fix summary counts | `rg -c "market-data-service\|market-data-api\|market-data-mcp" docs/BUILD_PLAN.md` | ⬜ |
| 16 | Run full regression | tester | All tests pass | `uv run pytest tests/ -v` | ⬜ |
| 17 | Create reflection file | coder | `2026-03-11-market-data-service-api-mcp-reflection.md` | `Test-Path docs/execution/reflections/2026-03-11-market-data-service-api-mcp-reflection.md` | ⬜ |
| 18 | Update metrics table | coder | New row in `metrics.md` | `rg -c "market-data-service-api-mcp" docs/execution/metrics.md` | ⬜ |
| 19 | Save session state to pomera | coder | pomera note ID | `pomera_notes search --search_term "Memory/Session/market-data*"` | ⬜ |
| 20 | Prepare commit messages | coder | Commit messages text | `rg -c "MEU-61\|MEU-63\|MEU-64" .agent/context/handoffs/052*` | ⬜ |
| 21 | Final review and plan–code sync | reviewer | Updated plan artifacts | `rg -n "TODO\|FIXME\|NotImplementedError" packages/ mcp-server/src/` | ⬜ |

---

## Verification Plan

### Automated Tests

```powershell
# MEU-61: Normalizers + MarketDataService
uv run pytest tests/unit/test_normalizers.py tests/unit/test_market_data_service.py -v

# MEU-63: REST API
uv run pytest tests/unit/test_market_data_api.py -v

# MEU-64: MCP tools (run from mcp-server/ — no root package.json)
cd mcp-server; npx vitest run tests/market-data-tools.test.ts

# TypeScript blocking checks (per AGENTS.md)
cd mcp-server; npx tsc --noEmit
cd mcp-server; npx eslint src/ --max-warnings 0
cd mcp-server; npm run build

# Full regression (all Python tests)
uv run pytest tests/ -v

# Quality gates
uv run python tools/validate_codebase.py --scope meu
```

### Manual Verification

None required — all verification is automated via pytest and vitest with mocked HTTP/fetch.
