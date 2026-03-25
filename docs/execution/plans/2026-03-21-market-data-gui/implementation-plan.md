# MEU-65: Market Data Providers GUI

Build the Market Data Providers settings page — a list+detail split layout React component that lets users configure API keys (including dual-credential providers like Alpaca), rate limits, timeouts, and test connections for all 12 market data providers.

**Project slug:** `2026-03-21-market-data-gui`
**MEUs included:** MEU-65 (`market-data-gui`)
**Build-plan sections covered:** [06f §Market Data Settings Page](../../build-plan/06f-gui-settings.md), [build-priority-matrix item 30](../../build-plan/build-priority-matrix.md)
**Phase:** P1.5 — Market Data Aggregation (final item)

## Dependencies — All Satisfied

| Dependency | Status |
|---|---|
| MEU-63 `market-data-api` — 4 provider REST endpoints | ✅ approved |
| MEU-61 `market-data-service` | ✅ approved |
| MEU-60 `market-connection-svc` | ✅ approved |
| MEU-43 `gui-shell` — AppShell, NavRail, SettingsLayout | ✅ approved |

## In-Scope / Out-of-Scope

**In-scope:**
- `MarketDataProvidersPage.tsx` — full list+detail split layout per 06f wireframe
- `MarketDataProvidersPage.test.tsx` — vitest + React Testing Library
- Integration into `SettingsLayout.tsx` as a new card/section (or tab)
- Provider info card: `signup_url` → "Get API Key ↗" link, auth method, default rate limit/timeout
- Conditional `api_secret` field for dual-auth providers (Alpaca)
- `data-testid` attributes on all interactive elements — registered in `ui/tests/e2e/test-ids.ts`
- `refetchInterval: 5_000` on provider status query (G5)
- Status bar feedback on save/test success **and** error paths (useStatusBar)
- "Get API Key ↗" external link per provider (from `ProviderConfig.signup_url`)
- G2 guard: Remove Key button disabled when `has_api_key === false`
- **Wave 6 E2E test file** `ui/tests/e2e/settings-market-data.test.ts` (navigation + provider list render + axe-core scan)

**Out-of-scope:**
- MEU-70a watchlist visual redesign (depends on this MEU)
- Batch quote endpoint (`GET /quotes?tickers=`)
- Email settings, backup settings (separate MEUs: 73, 74)
- Reset to Default feature (MEU-76)

---

## Spec Sufficiency Gate

| Behavior / Contract | Source Type | Source | Resolved? | Notes |
|---|---|---|---|---|
| Provider list from `GET /providers` | Spec | [06f §55–86](../../build-plan/06f-gui-settings.md) | ✅ | `useQuery` with key `['market-providers']` |
| Save via `PUT /providers/{name}` | Spec | [06f §89–103](../../build-plan/06f-gui-settings.md) + [market_data.py L112–132](../../../packages/api/src/zorivest_api/routes/market_data.py) | ✅ | Body: `{api_key, api_secret, rate_limit, timeout, is_enabled}` |
| `api_secret` for dual-auth providers | Spec | [market_data.py L33](../../../packages/api/src/zorivest_api/routes/market_data.py) + [provider_registry.py L123–135](../../../packages/infrastructure/src/zorivest_infra/market_data/provider_registry.py) | ✅ | Alpaca requires both `api_key` and `api_secret` via `APCA-API-SECRET-KEY`; conditionally show field |
| Test via `POST /providers/{name}/test` | Spec | [06f §106–113](../../build-plan/06f-gui-settings.md) + [market_data.py L135–147](../../../packages/api/src/zorivest_api/routes/market_data.py) | ✅ | Returns `{success, message}` |
| Remove key via `DELETE /providers/{name}/key` | Spec | [market_data.py L150–162](../../../packages/api/src/zorivest_api/routes/market_data.py) | ✅ | Not in 06f wireframe code but endpoint exists; add "Remove Key" button |
| Test All Connections | Spec | [06f §115–125](../../build-plan/06f-gui-settings.md) | ✅ | Sequential loop over providers with `has_api_key` |
| Status icons (✅/❌/⚪) | Spec | [06f §127–129](../../build-plan/06f-gui-settings.md) | ✅ | Based on `last_test_status` |
| Enable/disable toggle | Spec | [06f §152–156](../../build-plan/06f-gui-settings.md) | ✅ | `is_enabled` checkbox |
| Provider info card | Local Canon | `ProviderConfig.signup_url` + `ProviderConfig.auth_method` + `ProviderConfig.default_rate_limit` | ✅ | No description or free-tier text in domain model; card renders signup link, auth method, and defaults only |
| Rate limit + timeout fields | Spec | [06f §161–166](../../build-plan/06f-gui-settings.md) | ✅ | Number inputs |
| `data-testid` attrs | Local Canon | [06-gui.md §E2E Waves](../../build-plan/06-gui.md) + [test-ids.ts](../../../ui/tests/e2e/test-ids.ts) | ✅ | Every interactive element; constants in `test-ids.ts` |
| Auto-refresh (G5) | Local Canon | [emerging-standards G5](../../../.agent/docs/emerging-standards.md) | ✅ | `refetchInterval: 5_000` |

---

## Feature Intent Contract (FIC)

### MEU-65: `market-data-gui`

| # | Acceptance Criterion | Source | Validation |
|---|---|---|---|
| AC-1 | Page renders list of all 12 providers from `GET /providers` | Spec: 06f §55–86 | Test: mock fetch, assert 12 `<li>` items |
| AC-2 | Clicking a provider selects it and shows detail panel | Spec: 06f §140–176 | Test: click first provider → detail panel visible |
| AC-3 | API key input saves via `PUT /providers/{name}` on Save | Spec: 06f §89–103 | Test: enter key → click Save → assert PUT called |
| AC-4 | Test Connection calls `POST /providers/{name}/test` | Spec: 06f §106–113 | Test: click Test → assert POST called, status updates |
| AC-5 | Test All calls POST for each provider with `has_api_key` | Spec: 06f §115–125 | Test: 3 providers with keys → 3 POST calls |
| AC-6 | Status icons match `last_test_status` (✅/❌/⚪) | Spec: 06f §127–129 | Test: assert correct emoji per status |
| AC-7 | Rate limit and timeout inputs bind to state and save | Spec: 06f §161–166 | Test: change value → Save → body includes new value |
| AC-8 | Enable/disable toggle saves `is_enabled` | Spec: 06f §152–156 | Test: uncheck → Save → `is_enabled: false` |
| AC-9 | Remove Key calls `DELETE /providers/{name}/key`; disabled when `has_api_key === false` | Spec: market_data.py L150–162 + G2 | Test: click Remove → assert DELETE called; assert button disabled when no key |
| AC-10 | Provider query uses `refetchInterval: 5_000` (G5) | Local Canon: emerging-standards G5 | Test: assert query config |
| AC-11 | All interactive elements have `data-testid` attributes from `test-ids.ts` constants | Local Canon: 06-gui.md §E2E | Test: assert key elements have testids |
| AC-12 | Status bar shows feedback on save/test success **and** error | Local Canon: useStatusBar pattern | Test: assert `setStatus` called on mutation success AND on mutation error with error message |
| AC-13 | API Secret field shown only for dual-auth providers (Alpaca); save sends `api_secret` in PUT body | Spec: provider_registry.py L123–135 | Test: select Alpaca → secret field visible; enter secret → Save → body includes `api_secret` |
| AC-14 | Provider info card renders `signup_url` as "Get API Key ↗" link and shows auth method | Local Canon: ProviderConfig domain | Test: select provider → assert external link href matches `signup_url`; auth method label rendered |

---

## Proposed Changes

### GUI Component

#### [NEW] [MarketDataProvidersPage.tsx](file:///p:/zorivest/ui/src/renderer/src/features/settings/MarketDataProvidersPage.tsx)

List+detail split layout component per 06f wireframe:
- Left panel: provider list with status icons, selectable items
- Right panel: provider detail form (API key, conditional API secret for dual-auth, rate limit, timeout, enable toggle)
- Actions: Save Changes, Test Connection, Remove Key (disabled when `has_api_key === false`, G2)
- Header: "Test All Connections" button
- Provider info card: `signup_url` → "Get API Key ↗" external link, auth method label, default rate limit/timeout
- Uses `apiFetch` from `@/lib/api`, `useStatusBar` for feedback (success + error)
- `refetchInterval: 5_000` on providers query

#### [MODIFY] [SettingsLayout.tsx](file:///p:/zorivest/ui/src/renderer/src/features/settings/SettingsLayout.tsx)

Add the `MarketDataProvidersPage` as a new section/card within the Settings layout, below MCP Guard Controls and above MCP Server Status Panel.

---

### GUI Tests

#### [NEW] [MarketDataProvidersPage.test.tsx](file:///p:/zorivest/ui/src/renderer/src/features/settings/__tests__/MarketDataProvidersPage.test.tsx)

Vitest + React Testing Library tests covering AC-1 through AC-14:
- Mock `apiFetch` to return test provider data (including Alpaca with dual-auth)
- Test provider list rendering (12 items)
- Test selection → detail panel display
- Test Save mutation (PUT body verification including `api_secret` for Alpaca)
- Test Connection mutation (POST call)
- Test All Connections (sequential POST calls)
- Test status icon mapping
- Test Remove Key (DELETE call) + verify button disabled when no key (G2)
- Test `refetchInterval` config
- Test `data-testid` attributes from `test-ids.ts` constants
- Test status bar feedback (success **and** error paths)
- Test provider info card (`signup_url` link, auth method)

---

### E2E Test IDs

#### [MODIFY] [test-ids.ts](file:///p:/zorivest/ui/tests/e2e/test-ids.ts)

Add `MARKET_DATA_PROVIDERS` section to the `SETTINGS` block (or as a new top-level constant):

```typescript
export const MARKET_DATA_PROVIDERS = {
    ROOT: 'market-data-providers',
    PROVIDER_LIST: 'provider-list',
    PROVIDER_ITEM: 'provider-item',
    DETAIL_PANEL: 'provider-detail',
    API_KEY_INPUT: 'provider-api-key-input',
    API_SECRET_INPUT: 'provider-api-secret-input',
    RATE_LIMIT_INPUT: 'provider-rate-limit-input',
    TIMEOUT_INPUT: 'provider-timeout-input',
    ENABLE_TOGGLE: 'provider-enable-toggle',
    SAVE_BUTTON: 'provider-save-btn',
    TEST_BUTTON: 'provider-test-btn',
    TEST_ALL_BUTTON: 'provider-test-all-btn',
    REMOVE_KEY_BUTTON: 'provider-remove-key-btn',
    SIGNUP_LINK: 'provider-signup-link',
} as const
```

---

### BUILD_PLAN.md Update

#### [MODIFY] [BUILD_PLAN.md](file:///p:/zorivest/docs/BUILD_PLAN.md)

- Update MEU-65 status from ⬜ to ✅ (after execution)
- Update Phase 8 status if this completes all P1.5 items

---

## Applicable Emerging Standards

| Standard | How Applied |
|---|---|
| G5 — Auto-Refresh for Externally Mutated Data | `refetchInterval: 5_000` on providers query |
| G6 — Field Name Contracts | Use exact field names from `ProviderStatus` API response |
| G1 — Buttons Must Have Visible Borders | All buttons styled with borders (existing pattern from SettingsLayout) |
| G2 — Destructive Buttons Disabled When Inapplicable | Remove Key button disabled when `has_api_key === false` |

---

## Verification Plan

### Automated Tests (Vitest)

```bash
# Run MEU-65 tests only
cd p:\zorivest\ui && npx vitest run src/renderer/src/features/settings/__tests__/MarketDataProvidersPage.test.tsx --reporter=verbose

# Run all UI tests (regression)
cd p:\zorivest\ui && npx vitest run --reporter=verbose

# Type check
cd p:\zorivest\ui && npx tsc --noEmit
```

### E2E Tests + Accessibility (Wave 6)

MEU-65 activates **Wave 6** of the E2E suite (see [`06-gui.md` §Wave Activation Schedule](../../build-plan/06-gui.md)).

> [!IMPORTANT]
> Build before every E2E run: `cd p:\zorivest\ui && npm run build`

**Wave 6 gate MEU:** MEU-65 `market-data-gui`
**New test file:** `ui/tests/e2e/settings-market-data.test.ts`
**Tests to activate:** navigate to Settings → verify `nav-settings` testid; verify provider list renders; axe-core scan

Axe pattern (from `launch.test.ts`):
```typescript
import AxeBuilder from '@axe-core/playwright'
// In settings-market-data.test.ts:
test('market data settings page has no accessibility violations', async () => {
    await appPage.navigateTo('/settings')
    const results = await new AxeBuilder({ page: appPage.page }).analyze()
    expect(results.violations).toEqual([])
})
```

```bash
# 1. Build first (Playwright runs compiled bundle, not source)
cd p:\zorivest\ui && npm run build

# 2. Register test IDs (verified by grep)
rg "MARKET_DATA_PROVIDERS" ui/tests/e2e/test-ids.ts

# 3. Run Wave 6 E2E tests
cd p:\zorivest\ui && npx playwright test tests/e2e/settings-market-data.test.ts
```

---

## Handoff

- **File:** `.agent/context/handoffs/085-2026-03-21-market-data-gui-bp06fs6f.1.md`
- **Build-plan ref:** `bp06fs6f.1` (06f-gui-settings.md §Market Data Settings Page)

---

## BUILD_PLAN.md Maintenance

**Required UPDATE:** After execution, update MEU-65 row status to ✅ in the P1.5 section of `docs/BUILD_PLAN.md` (line 243). Also update Phase 8 status from "🟡 In Progress" → check if all 10 P1.5 MEUs are now ✅ (MEU-56–65). If so, update Phase 8 status to "✅ Completed" with today's date.

**Validation:**
```bash
rg "MEU-65" docs/BUILD_PLAN.md
# Expect: ✅ in status column
rg "Phase 8" docs/BUILD_PLAN.md
# Verify status reflects completion if all 10 items done
```

---

## Deviations from Original Plan

> Recorded 2026-03-22 for regression review. These are changes made during execution that differ
> from the plan above.

### Scope Additions (not in original plan)

| # | Addition | Rationale |
|---|----------|-----------|
| D1 | **Dedicated `/settings/market` route** instead of embedding in `SettingsLayout` | Embedding caused layout conflicts; standalone page is cleaner and matches the build plan intent for a full settings page |
| D2 | **"Data Sources" nav card in `SettingsLayout`** with chevron → navigates to `/settings/market` | Required once D1 moved the page to its own route; provides the entry point |
| D3 | **`shell.openExternal` IPC wiring** (`main/index.ts` → `preload/index.ts` → `window.electron.openExternal()`) | `window.open()` is blocked by Electron's `setWindowOpenHandler`. Required 3-file change to expose safe external URL opening |
| D4 | **`AuthMethod.NONE` enum variant** added to `zorivest_core/domain/enums.py` | Needed for free providers that require no API key |
| D5 | **Yahoo Finance + TradingView** added to `PROVIDER_REGISTRY` (14 providers total, up from 12) | User request; not in original build plan spec but logically consistent |
| D6 | **Free provider badge** ("✅ Free — no API key required") replaces API key section for `AuthMethod.NONE` providers | UX improvement to avoid confusing users with an empty API key field |
| D7 | **Free providers default `is_enabled=True`** in stub | Yahoo Finance and TradingView work without any configuration, so enabling by default is correct |
| D8 | **`signup_url` added to `ProviderStatus` Pydantic model** | Original plan implied the link came from the frontend config but the cleaner approach is backend-driven via the existing `ProviderConfig.signup_url` |
| D9 | **"View Documentation" button label** for free providers (instead of "Get API Key") | Better UX — free providers link to their library docs, not a signup page |
| D10 | **`AuthMethod` guard test updated** from 4 → 5 members in `test_market_data_entities.py` | Side effect of D4 |
| D11 | **Command palette `settings:market` path corrected** in `commandRegistry.ts` | Bug found during routing work |

### Scope Reductions — All Delivered

> Updated 2026-03-23. All three items originally deferred are now complete.

| # | Item | Status | Completed |
|---|------|--------|-----------|
| R1 | **Wave 6 E2E** `ui/tests/e2e/settings-market-data.test.ts` | ✅ Done | 2026-03-22 — 7/7 pass (19.0s). Axe injected via `file://` URL (Electron sandbox workaround). Heading hierarchy and `htmlFor` labels fixed. |
| R2 | **Live connection testing** (real provider API calls) | ✅ Done | 2026-03-22 — `StubProviderConnectionService` removed from `main.py`; `ProviderConnectionService(uow, ...)` wired. |
| R3 | **API key persistence** (encrypted DB storage) | ✅ Done | 2026-03-22 — keys stored via `FernetEncryptionAdapter` + `SqlAlchemyUnitOfWork`. |

> All MEU-65 work is closed. See `task.md` Steps 1–3 for execution detail and handoff `085` for evidence.

