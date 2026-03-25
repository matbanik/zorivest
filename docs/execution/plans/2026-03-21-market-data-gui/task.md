# Task — Market Data Providers GUI (MEU-65)

> **STATUS: COMPLETE** — 2026-03-22T23:55 EDT
> All phases and steps done. All deliverables complete (2026-03-23).

---

## Phase 1 — Completed (2026-03-21)

| # | Task | Status |
|---|------|--------|
| 1 | `MarketDataProvidersPage.tsx` (list+detail, 14 providers, CRUD, dual-auth) | ✅ |
| 2 | `MarketDataProvidersPage.test.tsx` (15 tests, AC-1 through AC-14) | ✅ |
| 3 | `MARKET_DATA_PROVIDERS` constants registered in `test-ids.ts` | ✅ |
| 4 | Dedicated `/settings/market` route added to `router.tsx` | ✅ |
| 5 | Command palette `settings:market` path corrected | ✅ |
| 6 | `MarketDataProvidersPage` removed from `SettingsLayout` embed | ✅ |
| 7 | `StubProviderConnectionService.list_providers()` seeded from `PROVIDER_REGISTRY` | ✅ |
| 8 | `signup_url` added to `ProviderStatus` Python model + stub + TS interface | ✅ |
| 9 | "Get API Key" / "View Documentation" button wired via `shell.openExternal` IPC | ✅ |
| 10 | Settings page "Data Sources" nav card → navigates to `/settings/market` | ✅ |
| 11 | `AuthMethod.NONE` added to enum for free providers | ✅ |
| 12 | **Yahoo Finance** + **TradingView** added to `PROVIDER_REGISTRY` (14 total) | ✅ |
| 13 | Free providers (NONE auth) shown with green "Free — no API key required" badge | ✅ |
| 14 | Free providers default to `is_enabled=True` in stub | ✅ |
| 15 | `AuthMethod` guard test updated: 4 → 5 members | ✅ |
| 16 | Full test suite: 207/207 UI tests pass, 43/43 backend market-data tests pass | ✅ |

---

## Phase 2

### Step 1 — Wire Real ProviderConnectionService in `main.py` ✅ DONE

**Completed 2026-03-22.** Three files changed:
- **NEW** `packages/infrastructure/src/zorivest_infra/market_data/service_factory.py`
  — `FernetEncryptionAdapter` (wraps `api_key_encryption` functions as Protocol)
  — `HttpxClient` (wraps `httpx.AsyncClient` as Protocol)
- **MODIFY** `packages/api/src/zorivest_api/main.py` line 166
  — Removed `StubProviderConnectionService` import + assignment
  — Added `ProviderConnectionService(uow, encryption, http_client, rate_limiters, PROVIDER_REGISTRY)`
  — Added `await _http_client.aclose()` on shutdown
- **NEW** `tests/unit/test_provider_service_wiring.py` — 4 tests (AC-W1 through AC-W4) all ✅

### Step 1b — Provider Connection Fixes ✅ DONE

**Completed 2026-03-22.** Both free providers fixed and live-verified:

| Provider | Root Cause | Fix | Live Result |
|---|---|---|---|
| **TradingView** | `symbol-search` (403 Cloudflare) + `pingpong` (301 redirect) | POST to `scanner.tradingview.com/america/scan`; validator checks `totalCount` key | ✅ 200, `totalCount: 19473` |
| **Yahoo Finance** | `Accept: application/json` → 406 on `getcrumb` endpoint | Changed to `Accept: */*`; crumb flow uses single `AsyncClient` session for cookie propagation | ✅ 200, crumb returned; AAPL fundamentals fetched |

Files changed:
- `provider_registry.py` — TradingView base_url + endpoint + POST; Yahoo `Accept: */*`
- `provider_connection_service.py` — `HttpClient.post()` added; `_test_tradingview_scanner()` and `_test_yahoo_finance_crumb()` helpers
- `service_factory.py` — `HttpxClient.post()` implemented; `follow_redirects=True`

```bash
uv run pytest tests/unit/test_provider_connection_service.py -q
# → 38 passed ✅
```

### Step 2 — Wave 6 E2E Tests ✅ DONE

**Completed 2026-03-22.** All 7 tests pass in 19.0s.

Two root causes fixed:

1. **Component accessibility violations** (`MarketDataProvidersPage.tsx`):
   - `h3` → `h2` for "Market Data Providers" list panel title (h1→h3 skip)
   - `h4` → `h3` for all detail panel sections (h2→h4 skip)
   - `htmlFor` added to API Key / API Secret / Requests-per-min / Timeout labels

2. **Electron sandbox incompatibility** (`settings-market-data.test.ts`):
   - `AxeBuilder.analyze()` blocked: internally calls `browserContext.newPage()` which Electron rejects
   - `addScriptTag({ content })` blocked: Electron `sandbox: true` disallows inline script injection
   - **Fix:** `addScriptTag({ url: pathToFileURL(axePath).href })` — file:// URLs are allowed by the renderer sandbox

```bash
npx playwright test tests/e2e/settings-market-data.test.ts
# → 7 passed (19.0s) ✅
```

Regression: `npm run test` → 15 test files passed ✅ | `npm run typecheck` → clean ✅

### Step 3 — Post-MEU Deliverables

- [x] Full regression: `npm run test` → 15/15 test files ✅
- [x] Type check: `npm run typecheck` → clean ✅
- [x] Backend tests: 282 unit passed, 15 skipped ✅ (1 pre-existing ordering failure in `TestAppStateWiring::test_unlock_propagates_db_unlocked` — passes in isolation, unrelated to MEU-65, last touched in MEU-89/90)
- [x] Update `meu-registry.md` — MEU-65 → ✅ in P1.5 section ✅
- [x] Update `BUILD_PLAN.md` — MEU-65 → ✅; check Phase 8 completion status ✅
- [x] Create reflection: `docs/execution/reflections/2026-03-21-market-data-gui-reflection.md` ✅
- [x] Update metrics table: `docs/execution/metrics.md` ✅
- [x] Create handoff: `.agent/context/handoffs/085-2026-03-21-market-data-gui-bp06fs6f.1.md` ✅
- [x] Prepare commit messages: `docs/execution/plans/2026-03-21-market-data-gui/commit-messages.md` ✅

---

## Key Files Modified

| File | Change |
|------|--------|
| `ui/src/renderer/src/features/settings/MarketDataProvidersPage.tsx` | New (Phase 1) + heading/label fixes (Wave 6) |
| `ui/src/renderer/src/features/settings/__tests__/MarketDataProvidersPage.test.tsx` | New — 15 tests |
| `ui/src/renderer/src/features/settings/SettingsLayout.tsx` | Added Data Sources nav card |
| `ui/src/renderer/src/router.tsx` | Added `/settings/market` route |
| `ui/src/renderer/src/registry/commandRegistry.ts` | Fixed `/settings/market` path |
| `ui/src/main/index.ts` | Added `open-external` IPC handler |
| `ui/src/preload/index.ts` | Exposed `window.electron.openExternal()` |
| `ui/tests/e2e/settings-market-data.test.ts` | New — 7 Wave 6 E2E tests |
| `ui/tests/e2e/test-ids.ts` | Added `MARKET_DATA_PROVIDERS` constants |
| `packages/core/src/zorivest_core/application/provider_status.py` | Added `signup_url` field |
| `packages/core/src/zorivest_core/domain/enums.py` | Added `AuthMethod.NONE` |
| `packages/infrastructure/.../provider_registry.py` | Yahoo/TradingView config + endpoint fixes |
| `packages/infrastructure/.../service_factory.py` | `HttpxClient` with `get`, `post`, `get_with_cookies` |
| `packages/core/.../provider_connection_service.py` | Yahoo crumb + TradingView POST helpers |
| `packages/api/src/zorivest_api/stubs.py` | Seeded all 14 providers, free defaults enabled |
| `packages/api/src/zorivest_api/main.py` | Wired real `ProviderConnectionService` |
| `tests/unit/test_market_data_entities.py` | Updated AuthMethod count 4→5 |
| `tests/unit/test_provider_service_wiring.py` | New — 4 wiring tests |

---

## Deviations Summary

Key deviations: standalone route (not embedded), IPC wiring for external URLs (D3),
free providers Yahoo Finance + TradingView (D5), signup_url moved to backend model (D8).

Connection fixes required deeper investigation than originally scoped: Yahoo Finance's unofficial
API now enforces cookie+crumb session (since mid-2023) with a specific `Accept: */*` requirement;
TradingView's public endpoints are Cloudflare-blocked except the scanner POST API used by all
major Python TradingView libraries.

Wave 6 E2E required novel axe-core injection pattern due to Electron sandbox restrictions —
see `[E2E-AXEELECTRON]` in `known-issues.md`.
