# Commit Messages — MEU-65 Market Data Providers GUI

> Draft commit messages for all work delivered in the MEU-65 session cluster.
> Group into logical commits for a clean git history.

---

## Commit 1 — Market Data GUI Component

```
feat(gui): add Market Data Providers settings page (MEU-65)

- MarketDataProvidersPage.tsx: list+detail split layout for 14 providers
- Dual-auth support: API Secret field shown only for Alpaca
- Free-provider badge: "Free — no API key required" for AuthMethod.NONE providers
- Actions: Save Changes, Test Connection, Remove Key (disabled when no key), Test All
- Provider info card: "Get API Key" / "View Documentation" external links
- refetchInterval: 5_000 for background status polling (G5)
- Accessible heading hierarchy (h2/h3) and labelled inputs (htmlFor)

Closes MEU-65 Phase 1
```

## Commit 2 — Routing and IPC Wiring

```
feat(gui): add /settings/market route and openExternal IPC bridge

- router.tsx: dedicated /settings/market route for MarketDataProvidersPage
- SettingsLayout.tsx: "Data Sources" nav card → navigates to /settings/market
- commandRegistry.ts: fix settings:market palette path (was /settings)
- main/index.ts: open-external IPC handler via shell.openExternal
- preload/index.ts: expose window.electron.openExternal()

Required by Electron's setWindowOpenHandler blocking window.open()
```

## Commit 3 — Backend: Free Providers and AuthMethod.NONE

```
feat(core): add AuthMethod.NONE and free provider support

- domain/enums.py: AuthMethod.NONE for providers requiring no API key
- provider_status.py: add signup_url field to ProviderStatus
- provider_registry.py: add Yahoo Finance and TradingView (14 providers total)
- stubs.py: seed all 14 providers; free providers default is_enabled=True
- test_market_data_entities.py: update AuthMethod count guard 4→5

Free providers: Yahoo Finance, TradingView
```

## Commit 4 — Backend: Real Service Wiring

```
feat(api): wire real ProviderConnectionService in main.py

- service_factory.py: FernetEncryptionAdapter + HttpxClient (get/post/get_with_cookies)
- main.py: replace StubProviderConnectionService with ProviderConnectionService(uow, ...)
- Add await _http_client.aclose() on shutdown

Tests: test_provider_service_wiring.py (4 new tests, AC-W1 through AC-W4)
```

## Commit 5 — Backend: Provider Connection Fixes

```
fix(infra): fix TradingView and Yahoo Finance connection tests

TradingView:
- Symbol-search/pingpong blocked by Cloudflare → use scanner POST API
- POST to scanner.tradingview.com/america/scan; validate totalCount key

Yahoo Finance:
- Accept: application/json → 406 on getcrumb endpoint
- Use Accept: */* and single AsyncClient session for cookie+crumb flow

Tests: 38 provider connection tests pass
```

## Commit 6 — E2E Wave 6 and Accessibility Fixes

```
test(e2e): add Wave 6 E2E tests for Market Data Providers page

- settings-market-data.test.ts: 7 tests (provider list, detail panel,
  free provider badge, Test Connection, Get API Key, Test All, axe scan)
- Axe injected via file:// URL (Electron sandbox: inline addScriptTag blocked)
- Heading hierarchy fixes: h3→h2 (list panel), h4→h3 (detail sections)
- htmlFor label associations: API Key, API Secret, rate limit, timeout

Known issue documented: [E2E-AXEELECTRON] in known-issues.md
All 7 tests pass (19.0s)
```

## Commit 7 — Test IDs

```
test(e2e): register MARKET_DATA_PROVIDERS test-id constants

Add MARKET_DATA_PROVIDERS block to test-ids.ts with constants for
root, list, item, detail panel, inputs, buttons, and signup link.
```
