# Handoff 085 — MEU-65 `gui-settings-market-data` — bp06fs6f.1

**Date:** 2026-03-22  
**Agent:** Opus (implementation)  
**Status:** 🟡 ready_for_review  
**Scope verdict:** On spec — full GUI + real service wiring + free provider fixes + Wave 6 E2E

---

## MEU Summary

| Field | Value |
|-------|-------|
| Registry slug | `gui-settings-market-data` |
| Matrix item | P1.5 / 06f-s6f |
| Build plan | `06f-settings-market-data.md`, `08-market-data.md` |
| Execution plan | `docs/execution/plans/2026-03-21-market-data-gui/` |

---

## Feature Intent Contract (FIC)

**Intent statement:** The Market Data Providers settings page allows users to view, enable, configure, and test connections to all 14 supported market data providers. Free providers (Yahoo Finance, TradingView) are clearly distinguished from API-key providers. Connection tests run against the real backend service. The page is accessible to WCAG 2.1 AA.

**Acceptance criteria:**

| # | Criterion | Source | Test |
|---|-----------|--------|------|
| AC-1 | Provider list renders all 14 providers | Spec §8.6 | `settings-market-data.test.ts:provider list renders all 14 providers` |
| AC-2 | Selecting a provider shows the detail panel | Spec §8.6 | `settings-market-data.test.ts:selecting a provider shows the detail panel` |
| AC-3 | Free providers show "Free — no API key required" badge | MEU-65, spec §8.7 | `settings-market-data.test.ts:free providers show the "Free" badge` |
| AC-4 | Test Connection button is present in detail panel | Spec §8.6 | `settings-market-data.test.ts:detail panel shows Test Connection button` |
| AC-5 | "Get API Key" button is present for API-key providers | Spec §8.6 | `settings-market-data.test.ts:details panel shows Get API Key button` |
| AC-6 | "Test All" button is present in the provider list | Spec §8.6 | `settings-market-data.test.ts:provider list shows Test All button` |
| AC-7 | Page has no WCAG 2.1 AA accessibility violations | Legal/WCAG | `settings-market-data.test.ts:page has no accessibility violations` |

**Negative cases:**
- `AuthMethod.NONE` providers must NOT show API Key input or "Get API Key" button
- Headed hierarchy must have no level-skip (h1 → h2 → h3)

---

## FAIL → PASS Evidence

### Wave 6 E2E — 7 Tests

> **Environment prerequisite:** E2E tests require a built Electron app (`npm run build`) **and**
> a display server. In headless environments (CI/Linux without Xvfb), Electron fails to launch
> with `Process failed to launch!`. This is a known environment limitation — same pattern as
> MEU-46/47/49 (`metrics.md` row 34, `known-issues.md [E2E-AXEELECTRON]`). Tests pass in any
> environment with a display (Windows, macOS, Linux+Xvfb).

```
npx playwright test tests/e2e/settings-market-data.test.ts
  ✔  1 settings-market-data.test.ts:27:5 › provider list renders all 14 providers
  ✔  2 settings-market-data.test.ts:47:5 › selecting a provider shows the detail panel
  ✔  3 settings-market-data.test.ts:66:5 › free providers show the "Free" badge
  ✔  4 settings-market-data.test.ts:84:5 › detail panel shows Test Connection button
  ✔  5 settings-market-data.test.ts:100:5 › details panel shows Get API Key button
  ✔  6 settings-market-data.test.ts:118:5 › provider list shows Test All button
  ✔  7 settings-market-data.test.ts:126:5 › page has no accessibility violations

  7 passed (19.0s)
```

### UI Unit Tests

```
npm run test
  Test Files  15 passed (15)
  Tests       207 passed (207)
```

### TypeScript

```
npm run typecheck
  → 0 errors
```

### Backend Unit Tests (isolated)

```
.venv\Scripts\python.exe -m pytest tests/unit/ -x -q
  → 282 passed, 15 skipped
```

> **Note:** Full `tests/` suite shows `TestAppStateWiring::test_unlock_propagates_db_unlocked` failing in ordering context only — passes in isolation and is unrelated to MEU-65 (last modified in MEU-89/90 scheduling work, commit `86e4254`). Pre-existing issue tracked separately.

### Backend: Provider Connection Tests

```
uv run pytest tests/unit/test_provider_connection_service.py -q
→ 38 passed ✅

uv run pytest tests/unit/test_provider_service_wiring.py -v
→ 4 passed ✅
```

---

## Files Changed

| File | Change |
|------|--------|
| `ui/src/renderer/src/features/settings/MarketDataProvidersPage.tsx` | **New** — 14-provider list+detail component; free provider badges; "Get API Key" / "View Documentation" buttons via IPC; heading hierarchy h2/h3; htmlFor label associations |
| `ui/src/renderer/src/features/settings/__tests__/MarketDataProvidersPage.test.tsx` | **New** — 15 unit tests (AC-1 through AC-14) |
| `ui/src/renderer/src/features/settings/SettingsLayout.tsx` | Added "Data Sources" nav card |
| `ui/src/renderer/src/router.tsx` | Added `/settings/market` route |
| `ui/src/renderer/src/registry/commandRegistry.ts` | Fixed `/settings/market` palette path |
| `ui/src/main/index.ts` | Added `open-external` IPC handler |
| `ui/src/preload/index.ts` | Exposed `window.electron.openExternal()` |
| `ui/tests/e2e/settings-market-data.test.ts` | **New** — 7 Wave 6 E2E tests; axe injected via `file://` URL (Electron sandbox workaround) |
| `ui/tests/e2e/test-ids.ts` | Added `MARKET_DATA_PROVIDERS` constants |
| `packages/core/src/zorivest_core/application/provider_status.py` | Added `signup_url` field |
| `packages/core/src/zorivest_core/domain/enums.py` | Added `AuthMethod.NONE` |
| `packages/infrastructure/.../provider_registry.py` | Yahoo Finance + TradingView entries; TradingView endpoint → scanner POST; Yahoo `Accept: */*` |
| `packages/infrastructure/.../provider_connection_service.py` | `_test_tradingview_scanner()` (POST); `_test_yahoo_finance_crumb()` (single-session crumb flow) |
| `packages/infrastructure/.../service_factory.py` | **New** — `FernetEncryptionAdapter`, `HttpxClient` (get/post/get_with_cookies) |
| `packages/api/src/zorivest_api/main.py` | Wired real `ProviderConnectionService`; removed `StubProviderConnectionService` |
| `packages/api/src/zorivest_api/stubs.py` | Seeded all 14 providers with free defaults enabled |
| `tests/unit/test_market_data_entities.py` | Updated `AuthMethod` count 4 → 5 |
| `tests/unit/test_provider_service_wiring.py` | **New** — 4 wiring tests (AC-W1 through AC-W4) |
| `.agent/context/known-issues.md` | Added `[E2E-AXEELECTRON]` + `[E2E-AXESILENT]` |

---

## Notable Technical Decisions

**Axe-core / Electron sandbox incompatibility:** `@axe-core/playwright`'s `AxeBuilder.analyze()` calls `browserContext.newPage()` which Electron rejects. Inline `addScriptTag({ content })` is also blocked by `sandbox: true`. Solution: `addScriptTag({ url: pathToFileURL(axePath).href })` — Electron sandbox allows local `file://` assets. Documented in `[E2E-AXEELECTRON]`.

**Yahoo Finance:** `getcrumb` endpoint requires `Accept: */*` (not `application/json`) and a persistent cookie session to carry the crumb across requests.

**TradingView:** Public symbol endpoints return 403 (Cloudflare). Scanner POST API (`scanner.tradingview.com/america/scan`) is used by all major Python TradingView libraries and returns 200.

---

## Codex Validation Checklist

- [ ] Confirm `npx playwright test tests/e2e/settings-market-data.test.ts` → 7 passed
- [ ] Confirm heading structure: `h1 "Zorivest"` → `h2 "Market Data Providers"` → `h3` sections (no level skips)
- [ ] Confirm `rg "StubProviderConnectionService" packages/api/src/zorivest_api/main.py` → 0 matches
- [ ] Confirm `uv run pytest tests/unit/test_provider_service_wiring.py -v` → 4 passed
- [ ] Confirm `uv run pytest tests/unit/test_provider_connection_service.py -q` → 38 passed
- [ ] Confirm `npm run test` → 15 test files / 207 tests passed
- [ ] Confirm `npm run typecheck` → 0 errors
- [ ] Confirm free providers (Yahoo Finance, TradingView) show "Free — no API key required" badge and no API Key input
- [ ] Confirm `[E2E-AXEELECTRON]` entry exists in `known-issues.md`
