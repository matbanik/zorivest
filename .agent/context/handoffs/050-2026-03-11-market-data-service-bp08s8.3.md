# MEU-61: MarketDataService + Response Normalizers

## Task

- **Date:** 2026-03-11
- **Task slug:** market-data-service
- **Owner role:** coder
- **Scope:** MarketDataService + 10 response normalizers with provider fallback

## Inputs

- User request: Implement MarketDataService and response normalizers (§8.3b, §8.3c)
- Specs/docs referenced: `docs/build-plan/08-market-data.md` §8.3b, §8.3c
- Constraints: Constructor injection for normalizers, same DI pattern as ProviderConnectionService

## Coder Output

- Changed files:
  - `packages/infrastructure/src/zorivest_infra/market_data/normalizers.py` — 10 normalizer functions + 3 registries (QUOTE, NEWS, SEARCH)
  - `packages/core/src/zorivest_core/services/market_data_service.py` — Service with provider fallback, SEC normalizer injected via constructor
  - `tests/unit/test_normalizers.py` — 27 tests (10 classes)
  - `tests/unit/test_market_data_service.py` — 9 tests (5 classes)
- Design notes: Normalizer registries injected via constructor. SEC normalizer also injected (no core→infra import). SEARCH_NORMALIZERS includes both FMP and Alpha Vantage. Finnhub quote normalizer takes `ticker` kwarg.
- Commands run: `uv run pytest tests/unit/test_normalizers.py tests/unit/test_market_data_service.py -q`
- Results: 36 passed

## Tester Output

- Commands run: `uv run pytest tests/unit/test_normalizers.py tests/unit/test_market_data_service.py -v --tb=short`
- Pass/fail matrix: 36/36 passed
- Coverage/test gaps: SEC filings tested only for "not configured" error (full SEC API flow deferred to integration)
- Evidence bundle location: This handoff
- FAIL_TO_PASS / PASS_TO_PASS result: RED confirmed (ImportError before implementation)

## Final Summary

- Status: GREEN — all 36 tests pass
- Next steps: Handoff to Codex for validation review
