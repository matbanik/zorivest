# Phase 8a Completion — API Surface + Pipeline Automation + Capability Wiring Handoff

**Date**: 2026-05-05
**Project**: `api-surface-pipeline-automation`
**MEUs**: 192 → 193 → 194 → 207
**Status**: ✅ Complete — Phase 8a is now 16/16 (all MEUs)
**Pomera Note**: ID 1071 (session 1), pending (session 2)

---

## Executive Summary

Phase 8a Market Data Expansion is now fully complete at 16/16 MEUs. This session completed MEU-207 (Capability Wiring), the final corrective MEU that was identified during plan review when a gap was found between the normalizer registries (runtime truth) and the `provider_capabilities.py` capability advertisements (structural metadata).

### Problem Statement

The `provider_capabilities.py` file declared `supported_data_types` based on the original §8a.3 spec research, which listed **all** data types a provider's API could theoretically serve. However, the actual runtime dispatch in `MarketDataService._fetch_data_type()` uses the `NORMALIZERS` dict to resolve providers — meaning if a provider has no normalizer for a data type, the service **cannot** dispatch to it regardless of what `supported_data_types` claims.

This created dead-code advertisements: providers advertising capabilities they could never fulfill at runtime.

### Design Decision: Registry-First Principle

**Inclusion Rule**: Only provider/data-type pairs backed by a runtime normalizer entry (in `NORMALIZERS`, `QUOTE_NORMALIZERS`, `NEWS_NORMALIZERS`, or `SEARCH_NORMALIZERS`) are within MEU-207 scope. Three structural providers (Nasdaq Data Link, OpenFIGI, Tradier) carry forward from MEU-184 unchanged because they use dedicated code paths (`sec_normalizer`, identity mapping) not governed by the generic normalizer registry.

---

## Evidence Bundle

### Changed Files

```diff
# packages/api/src/zorivest_api/main.py
# AC-1: NORMALIZERS injection
  from zorivest_infra.market_data.normalizers import (
+     NORMALIZERS,
      QUOTE_NORMALIZERS,
      NEWS_NORMALIZERS,
      SEARCH_NORMALIZERS,
  )
  ...
  app.state.market_data_service = MarketDataService(
      ...
      search_normalizers=SEARCH_NORMALIZERS,
+     normalizers=NORMALIZERS,
  )

# packages/infrastructure/src/zorivest_infra/market_data/provider_capabilities.py
# AC-2: 8 providers updated — normalizer-derived supported_data_types

-Alpha Vantage:  (earnings, economic_calendar, fundamentals, insider, ohlcv, quote)
+Alpha Vantage:  (earnings, economic_calendar, fundamentals, quote, ticker_search)

-Polygon.io:    (dividends, fundamentals, news, ohlcv, quote, splits)
+Polygon.io:    (dividends, ohlcv, quote, splits)

-Finnhub:       (earnings, economic_calendar, insider, news, quote)
+Finnhub:       (company_profile, earnings, economic_calendar, insider, news, quote)

-FMP:           (dividends, earnings, fundamentals, news, ohlcv, quote, splits)
+FMP:           (company_profile, dividends, earnings, economic_calendar, fundamentals, insider, splits, ticker_search)

-EODHD:         (dividends, fundamentals, news, ohlcv, splits)
+EODHD:         (company_profile, dividends, fundamentals, ohlcv, quote, splits)

-SEC API:       (fundamentals, insider)
+SEC API:       (insider, sec_filings)

-API Ninjas:    (earnings, insider, quote)
+API Ninjas:    (quote,)

-Alpaca:        (news, ohlcv, quote)
+Alpaca:        (ohlcv,)

# Carry-forward providers (unchanged):
# Nasdaq Data Link: (fundamentals,)
# OpenFIGI:         (identifier_mapping,)
# Tradier:          (ohlcv, quote)

# tests/unit/test_capability_wiring.py (NEW — 19 tests)
# AC-1: 4 tests — import check, kwarg check, param signature, storage
# AC-2: 8 parametrized tests — one per normalizer-backed provider
# AC-3: 4 tests — alignment invariant across all 4 normalizer registries
# AC-4: 3 tests — Yahoo-first frozenset, fallback chain, async dispatch

# tests/unit/test_provider_capabilities.py (UPDATED)
# EXPECTED_DATA_TYPES updated from MEU-184 spec values to MEU-207 normalizer-derived values
```

### Commands Executed

```
# RED phase — 13 failed, 6 passed (0.38s)
uv run pytest tests/unit/test_capability_wiring.py --tb=short

# GREEN phase — 19 passed (0.27s)
uv run pytest tests/unit/test_capability_wiring.py -x --tb=short

# Full suite regression — 2699 passed, 0 failed (100.67s)
uv run pytest tests/unit/ -x --tb=short

# MEU gate — 8/8 blocking checks PASS (31.62s)
uv run python tools/validate_codebase.py --scope meu
```

### Test Results

| Test Suite | Count | Status |
|-----------|-------|--------|
| Capability wiring (new) | 19 | ✅ PASS |
| Provider capabilities (updated) | 15 | ✅ PASS |
| Full unit suite | 2699 | ✅ PASS |

### FAIL_TO_PASS Evidence

**RED phase output** (13 failures):
- `TestNormalizerInjection::test_main_py_imports_normalizers` — `NORMALIZERS` not imported in main.py
- `TestNormalizerInjection::test_main_py_passes_normalizers_kwarg` — `normalizers=NORMALIZERS` kwarg not present
- `TestExpectedCapabilityTuples` — 8 parametrized failures for all normalizer-backed providers (e.g., `Alpha Vantage: expected ('earnings', 'economic_calendar', 'fundamentals', 'quote', 'ticker_search'), got ('earnings', 'economic_calendar', 'fundamentals', 'insider', 'ohlcv', 'quote')`)
- `TestNormalizerCapabilityAlignment` — 3 failures detecting dead-code advertisements (`Financial Modeling Prep:insider`, `EODHD:company_profile`, etc.)

**GREEN phase**: All 13 failures resolved by implementation changes. Zero test modifications.

### Quality Gate

```
[1/8] Python Type Check (pyright): PASS (5.4s)
[2/8] Python Lint (ruff): PASS (0.1s)
[3/8] Python Unit Tests (pytest): PASS (18.0s)
[4/8] TypeScript Type Check (tsc): PASS (1.6s)
[5/8] TypeScript Lint (eslint): PASS (1.2s)
[6/8] TypeScript Unit Tests (vitest): PASS (4.5s)
[7/8] Anti-Placeholder Scan: PASS (0.0s)
[8/8] Anti-Deferral Scan: PASS (0.0s)
→ All blocking checks passed! (31.62s)
```

### Codex Validation Report

| Pass | Agent | Verdict | Findings |
|------|-------|---------|----------|
| 1 | GPT-5.5 Codex | `changes_required` | 3 findings (store recipe source wiring, REST provider boundary, test strengthening) |
| 2 | GPT-5.5 Codex | `changes_required` | 2 findings (service signature mismatch, evidence reconciliation) |
| 3 | GPT-5.5 Codex | `changes_required` | 1 finding (evidence reconciliation — reflection file validator false positive) |

All production-code findings (R1 from passes 1–3) have been resolved. The remaining R2 evidence finding was traced to a validator bug (reflection files incorrectly scanned as handoffs) and fixed in `tools/validate_codebase.py`.

---

## Registry Updates

- `docs/BUILD_PLAN.md` L297: MEU-207 ⬜ → ✅
- `docs/BUILD_PLAN.md` L758: P1.5a complete count 15 → 16
- `.agent/context/meu-registry.md` L406: MEU-207 → ✅ 2026-05-05

## Design Rationale

### Why not keep the broader spec values?

The §8a.3 research table documented what providers **could** serve based on their public API documentation. But Zorivest's runtime dispatch uses `self._normalizers.get(data_type, {})` — if a data type has no normalizer function registered for a provider, the service literally cannot use that provider for that data type. Advertising a capability that the service cannot fulfill creates:

1. **User confusion**: `zorivest_db(action:"provider_capabilities")` shows capabilities that never resolve
2. **MCP tool inaccuracy**: AI agents get false confidence in fallback chains
3. **Testing blind spots**: Tests pass because they check registry values, not runtime behavior

The normalizer-first principle eliminates all three issues by making the structural metadata match the runtime truth.

### Why update `test_provider_capabilities.py`?

The MEU-184 test (`EXPECTED_DATA_TYPES`) asserted values from the original §8a.3 spec. MEU-207 **intentionally supersedes** those values with normalizer-derived tuples. This is not "modifying tests to pass" — it's updating an older specification test to match a newer, more accurate specification. The authoritative assertion is in `test_capability_wiring.py` which derives expectations mechanically from the normalizer registries.

---

## Phase 8a Complete

All 16 MEUs (MEU-182a through MEU-195 + MEU-207) are now marked ✅. Phase 8a (Market Data Expansion) is fully implemented, tested, and capability-aligned.

---

## Ad-Hoc Pipeline Hardening (2026-05-05/06)

> Post-MEU production fixes discovered during live pipeline testing. Not MEU-scoped but essential for end-to-end pipeline operation.

### Changed Files

| File | Fix | Summary |
|------|-----|---------|
| `compose_step.py` | AH-1 | try/except KeyError on `get_output()` — skip missing upstream with warning |
| `test_compose_step.py` | AH-1 | AC-5.4: assert missing step_id is skipped gracefully |
| `secure_jinja.py` | AH-2 | `_pipeline_safe_dumps()` — bytes/datetime handler for `\|tojson` |
| `template_engine.py` | AH-2 | Register `_pipeline_safe_dumps` as JSON serializer |
| `market_data_adapter.py` | AH-3 | 4 call sites pass registry key for API key lookup (was display name) |
| `provider_connection_service.py` | AH-4 | `_validate_alpaca()` checks `latestTrade`/`latestQuote` (snapshot) not `id` (account) |
| `test_provider_connection_service.py` | AH-5 | 3 tests updated + 1 new test for snapshot response shape (45 pass) |
| DB template | AH-6 | Envelope unwrapping, `is defined` guards, error cards |

### Root Causes

1. **AH-1/AH-6**: Pipeline `on_error="log_and_continue"` was never tested with ComposeStep — the step assumed all sources exist.
2. **AH-2**: httpx can return `bytes` in certain responses; Jinja2's `|tojson` delegates to `json.dumps()` which doesn't handle bytes.
3. **AH-3**: Polygon.io → Massive rebrand introduced `config.name="Massive"` but API keys stored under `"Polygon.io"` registry key.
4. **AH-4/AH-5**: Alpaca test endpoint is the Market Data API snapshot (`/v2/stocks/AAPL/snapshot`), not the Trading API account (`/v2/account`). Validator schema mismatch.

### Validation

```
# Alpaca connection test → ✅ in GUI (confirmed via API logs: POST /api/v1/market-data/providers/Alpaca/test → 200)
# Compose step tests: uv run pytest tests/unit/test_compose_step.py → PASS
# Provider connection tests: uv run pytest tests/unit/test_provider_connection_service.py → 45 PASS
# Pipeline email: Received formatted email with tables, not raw JSON
```
