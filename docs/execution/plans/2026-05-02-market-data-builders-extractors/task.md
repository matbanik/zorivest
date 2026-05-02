---
project: "2026-05-02-market-data-builders-extractors"
source: "docs/execution/plans/2026-05-02-market-data-builders-extractors/implementation-plan.md"
meus: ["MEU-185", "MEU-186", "MEU-187", "MEU-188"]
status: "in_progress"
template_version: "2.0"
---

# Task — Market Data Builders & Extractors

> **Project:** `2026-05-02-market-data-builders-extractors`
> **Type:** Infrastructure
> **Estimate:** 6 files changed (~1,900 lines added)

## Task Table

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| | **MEU-185: Simple GET Builders** | | | | |
| 1 | Write FIC + red-phase tests for MEU-185 | tester | `test_url_builders.py` extended with ~40 new tests for Alpaca, FMP, EODHD, API Ninjas, Tradier | `uv run pytest tests/unit/test_url_builders.py -x --tb=short -v -k "alpaca or fmp or eodhd or api_ninjas or tradier" *> C:\Temp\zorivest\meu185-red.txt; Get-Content C:\Temp\zorivest\meu185-red.txt \| Select-Object -Last 30` → all FAIL | `[x]` |
| 2 | Implement 5 simple-GET builders (MEU-185) | coder | `AlpacaUrlBuilder`, `FMPUrlBuilder`, `EODHDUrlBuilder`, `APINinjasUrlBuilder`, `TradierUrlBuilder` + registry | `uv run pytest tests/unit/test_url_builders.py -x --tb=short -v -k "alpaca or fmp or eodhd or api_ninjas or tradier" *> C:\Temp\zorivest\meu185-green.txt; Get-Content C:\Temp\zorivest\meu185-green.txt \| Select-Object -Last 30` → all PASS | `[x]` |
| | **MEU-186: Special-Pattern Builders** | | | | |
| 3 | Write FIC + red-phase tests for MEU-186 (incl. RequestSpec) | tester | `test_url_builders.py` extended with ~27 new tests for Alpha Vantage, Nasdaq DL, OpenFIGI, SEC API + RequestSpec | `uv run pytest tests/unit/test_url_builders.py -x --tb=short -v -k "alpha_vantage or nasdaq or openfigi or sec_api or request_spec" *> C:\Temp\zorivest\meu186-red.txt; Get-Content C:\Temp\zorivest\meu186-red.txt \| Select-Object -Last 30` → all FAIL | `[x]` |
| 4 | Implement RequestSpec + 4 special-pattern builders (MEU-186) | coder | `RequestSpec` dataclass + `AlphaVantageUrlBuilder`, `NasdaqDataLinkUrlBuilder`, `OpenFIGIUrlBuilder`, `SECAPIUrlBuilder` + registry | `uv run pytest tests/unit/test_url_builders.py -x --tb=short -v -k "alpha_vantage or nasdaq or openfigi or sec_api or request_spec" *> C:\Temp\zorivest\meu186-green.txt; Get-Content C:\Temp\zorivest\meu186-green.txt \| Select-Object -Last 30` → all PASS | `[x]` |
| | **MEU-187: Standard Extractors** | | | | |
| 5 | Write FIC + red-phase tests for MEU-187 | tester | `test_response_extractors.py` + `test_field_mappings.py` extended with ~50 new tests for 5 simple-GET providers + slug map + field mappings | `uv run pytest tests/unit/test_response_extractors.py tests/unit/test_field_mappings.py -x --tb=short -v -k "alpaca or fmp or eodhd or api_ninjas or tradier or slug" *> C:\Temp\zorivest\meu187-red.txt; Get-Content C:\Temp\zorivest\meu187-red.txt \| Select-Object -Last 30` → all FAIL | `[x]` |
| 6 | Implement slug map + standard extractors + field mappings (MEU-187) | coder | 9 slug map entries + extractors for Alpaca, FMP, EODHD, API Ninjas, Tradier + ~25 field mapping tuples | `uv run pytest tests/unit/test_response_extractors.py tests/unit/test_field_mappings.py -x --tb=short -v -k "alpaca or fmp or eodhd or api_ninjas or tradier or slug" *> C:\Temp\zorivest\meu187-green.txt; Get-Content C:\Temp\zorivest\meu187-green.txt \| Select-Object -Last 30` → all PASS | `[x]` |
| | **MEU-188: Complex Extractors** | | | | |
| 7 | Write FIC + red-phase tests for MEU-188 | tester | `test_response_extractors.py` + `test_field_mappings.py` extended with ~40 new tests for Alpha Vantage (OHLCV + CSV + rate-limit), Finnhub candles, Nasdaq DL, Polygon timestamps + field mappings | `uv run pytest tests/unit/test_response_extractors.py tests/unit/test_field_mappings.py -x --tb=short -v -k "alpha_vantage or finnhub_candle or nasdaq_dl or polygon_timestamp" *> C:\Temp\zorivest\meu188-red.txt; Get-Content C:\Temp\zorivest\meu188-red.txt \| Select-Object -Last 30` → all FAIL | `[x]` |
| 8 | Implement complex extractors + field mappings (MEU-188) | coder | Alpha Vantage (date-keyed + CSV earnings + rate-limit), Finnhub candle (parallel arrays), Nasdaq DL (parallel arrays), Polygon (ms timestamps) + ~20 field mapping tuples | `uv run pytest tests/unit/test_response_extractors.py tests/unit/test_field_mappings.py -x --tb=short -v -k "alpha_vantage or finnhub_candle or nasdaq_dl or polygon_timestamp" *> C:\Temp\zorivest\meu188-green.txt; Get-Content C:\Temp\zorivest\meu188-green.txt \| Select-Object -Last 30` → all PASS | `[x]` |
| | **Quality Gate & Boilerplate** | | | | |
| 9 | Run full test suite + quality gate | tester | 0 failures, 0 pyright errors, 0 ruff violations | `uv run pytest tests/ -x --tb=short -v *> C:\Temp\zorivest\pytest.txt; Get-Content C:\Temp\zorivest\pytest.txt \| Select-Object -Last 40`; `uv run pyright packages/ *> C:\Temp\zorivest\pyright.txt; Get-Content C:\Temp\zorivest\pyright.txt \| Select-Object -Last 30`; `uv run ruff check packages/ *> C:\Temp\zorivest\ruff.txt; Get-Content C:\Temp\zorivest\ruff.txt \| Select-Object -Last 20` | `[x]` |
| 10 | Run MEU gate validation | tester | 8/8 blocking checks pass | `uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate.txt; Get-Content C:\Temp\zorivest\validate.txt \| Select-Object -Last 50` | `[x]` |
| 11 | Anti-placeholder scan | tester | 0 matches in market_data directory | `rg "TODO\|FIXME\|NotImplementedError" packages/infrastructure/src/zorivest_infra/market_data/ *> C:\Temp\zorivest\placeholder-scan.txt; Get-Content C:\Temp\zorivest\placeholder-scan.txt` → 0 | `[x]` |
| 12 | Update `docs/BUILD_PLAN.md` Phase 8a tracker rows | orchestrator | MEU-185, 186, 187, 188 marked in-progress/complete | `rg "MEU-185\|MEU-186\|MEU-187\|MEU-188" docs/BUILD_PLAN.md *> C:\Temp\zorivest\buildplan-check.txt; Get-Content C:\Temp\zorivest\buildplan-check.txt` | `[x]` |
| 13 | Save session state to pomera_notes | orchestrator | `Memory/Session/Zorivest-market-data-builders-extractors-2026-05-02` | MCP: `pomera_notes(action="search", search_term="Zorivest-market-data-builders*")` returns ≥1 result | `[x]` |
| 14 | Create handoff | reviewer | `.agent/context/handoffs/2026-05-02-market-data-builders-extractors-handoff.md` | `Test-Path .agent/context/handoffs/2026-05-02-market-data-builders-extractors-handoff.md` | `[x]` |
| 15 | Create reflection | orchestrator | `docs/execution/reflections/2026-05-02-market-data-builders-extractors-reflection.md` | `Test-Path docs/execution/reflections/2026-05-02-market-data-builders-extractors-reflection.md` | `[x]` |
| 16 | Append metrics row | orchestrator | Row appended to `docs/execution/metrics.md` | `Get-Content docs/execution/metrics.md \| Select-Object -Last 3` | `[x]` |
| | **Addendum: Yahoo OHLCV** | | | | |
| 17 | Yahoo OHLCV extractor + field mapping (TDD: 6 red→green + 1 mapping + 1 registry) | coder | `_yahoo_ohlcv` registered, `("yahoo","ohlcv")` in FIELD_MAPPINGS | `uv run pytest tests/unit/test_response_extractors.py::TestYahooOHLCVExtraction tests/unit/test_field_mappings.py::TestOhlcvMappings -v` → 8 passed | `[x]` |
| 18 | Full regression + static analysis | tester | 2662 passed, pyright 0, ruff clean | `uv run pytest tests/ -x --tb=short -q` → 0 failures | `[x]` |
| | **Addendum: TradingView Scanner** | | | | |
| 19 | TradingView builder + extractors + mappings (TDD: 13 red→green + 2 mapping + 6 builder) | coder | `TradingViewUrlBuilder` registered, `_tradingview_quote` + `_tradingview_fundamentals` extractors, 2 field mapping tuples | `uv run pytest tests/unit/test_url_builders.py::TestTradingViewUrlBuilder tests/unit/test_response_extractors.py::TestTradingViewQuoteExtractor tests/unit/test_response_extractors.py::TestTradingViewFundamentalsExtractor tests/unit/test_field_mappings.py::TestTradingViewMappings -v` → 14 passed | `[x]` |
| 20 | Full regression + static analysis | tester | 2714 passed, pyright 0, ruff clean | `uv run pytest tests/ -x --tb=short -q` → 0 failures | `[x]` |
| | **Addendum: Pipeline Approval Drift Fix** | | | | |
| 21 | Fix `triggerRun()` missing CSRF token (403 Forbidden) | coder | `X-Approval-Token` header sent via IPC handshake | GUI Run Now / Test Run returns 200 OK | `[x]` |
| 22 | Normalize `trigger.enabled` in `compute_content_hash()` | coder | Hash stable across enable/disable toggle | `approved_hash == content_hash` after `PATCH /schedule?enabled=true` | `[x]` |
| 23 | Remove redundant normalization in `patch_schedule()` | coder | Uses centralized `_compute_hash(pj)` | No manual `pj_for_hash` dict copy | `[x]` |
| 24 | MCP + direct API security verification (8 tests) | tester | All CSRF gates hold | MCP blocked, fake tokens rejected, no bypass | `[x]` |
| 25 | Rebuild MCP server | coder | 13 tools / 4 toolsets compiled | `npm run build` clean | `[x]` |


### Status Legend

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Not started |
| `[/]` | In progress |
| `[x]` | Complete |
| `[B]` | Blocked (must link follow-up) |
