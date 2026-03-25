# Market Data Providers GUI — Reflection

**Date:** 2026-03-21 to 2026-03-23
**MEUs:** MEU-65 (`market-data-gui`)
**Review Passes:** 4 (initial + 3 recheck passes across 2 sessions)

## What Went Well

- **Full-stack scope in one MEU:** Component, routing, IPC wiring, backend real service swap, and Wave 6 E2E all shipped together cleanly.
- **Free provider detection pattern:** `AuthMethod.NONE` enum variant + green badge + `is_enabled=True` default is a clean, extensible pattern. Adding future free providers just requires a registry entry.
- **IPC `openExternal` wiring:** Three-file change (main → preload → renderer) worked first time with zero surprises. The pattern is reusable for any future external URL.
- **TDD for service wiring:** `test_provider_service_wiring.py` (4 ACs) caught a potential regression during refactoring immediately.

## What Didn't Go Well

1. **Electron sandbox blocked AxeBuilder entirely.** `@axe-core/playwright`'s `AxeBuilder.analyze()` internally calls `browserContext.newPage()` which Electron rejects with `Target.createTarget: Not supported`. Additionally, `sandbox: true` + `contextIsolation: true` block inline `addScriptTag({ content })`. Required several debug iterations to arrive at the working solution: `addScriptTag({ url: pathToFileURL(axePath).href })`.

2. **Yahoo Finance and TradingView connection failures.** Both required detailed investigation:
   - Yahoo Finance's `getcrumb` endpoint requires `Accept: */*` (not `application/json`) and a single persistent `AsyncClient` session to carry cookies alongside the crumb.
   - TradingView's public symbol-search endpoints return 403 from Cloudflare. Only the scanner POST API works (`scanner.tradingview.com/america/scan`).

3. **Stale close-out artifacts across correction passes.** Reflection, commit-messages, and metrics were not created during the initial session, requiring a separate correction pass.

## Lessons Learned

- **Electron sandbox: use `file://` URLs for third-party scripts.** `addScriptTag({ url: fileUrl })` with `pathToFileURL()` is the only reliable injection method when `sandbox: true` is enabled. Documented in `known-issues.md [E2E-AXEELECTRON]`.
- **Always confirm the scanner is actually running.** When `AxeBuilder.analyze()` throws, the test fails at the scan call — not at `expect(violations).toEqual([])`. If violation logging is guarded by `if (violations.length > 0)`, it is never reached, giving a false impression that no violations exist. Documented in `[E2E-AXESILENT]`.
- **Yahoo Finance crumb flow requires a session cookie.** The crumb endpoint and the API endpoint must be called within the same `AsyncClient` session. Using two separate clients loses the session cookie and causes 401s.
- **TradingView: only the scanner POST endpoint is publicly accessible.** The `symbol-search` and `pingpong` endpoints are Cloudflare-blocked. This is the pattern used by all major Python TradingView libraries.
- **Close out deliverables in the same session.** Reflection, commit-messages, and metrics deferred to a later session cost extra review cycles.

## Process Improvement

- Added `[E2E-AXEELECTRON]` and `[E2E-AXESILENT]` to `known-issues.md` so future E2E test authors writing against Electron components immediately know the correct axe injection pattern.

## Metrics

- Total files changed: 18 (5 UI component/routing/IPC, 1 E2E test file, 2 backend service files, 1 service factory, 1 provider registry, 3 backend test files, 1 API main wiring, 1 stubs, 2 domain model files, 1 E2E test-ids)
- Tests added: 7 E2E (Wave 6) + 4 backend wiring + 62 backend connection = 73 tests confirmed
- Tests total (UI): 207 (15 test files)
- Review findings resolved: 4 High + 1 Med across 4 passes
