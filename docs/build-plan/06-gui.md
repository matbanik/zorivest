# Phase 6: GUI (Electron + React)

> Part of [Zorivest Build Plan](../BUILD_PLAN.md) | Prerequisites: [Phase 4](04-rest-api.md), [Phase 8](08-market-data.md) | Scheduling page requires [Phase 9](09-scheduling.md) | Service Manager requires [Phase 10](10-service-daemon.md) | Outputs: [Phase 7](07-distribution.md)

---

## Goal

Build the desktop GUI last — it's the outermost layer. The Electron shell spawns the Python backend as a child process and the React UI communicates with it via REST on localhost. Use TanStack Table for data grids, Lightweight Charts for financial charts.

This phase is split into ten domain-specific sub-files:

| # | Sub-File | Domain | Key Components |
|---|----------|--------|----------------|
| 6a | [GUI Shell](06a-gui-shell.md) | Electron lifecycle, window mgmt, notifications, persistence, command palette | `NotificationProvider`, `usePersistedState`, `CommandPalette`, `commandRegistry.ts` |
| 6b | [Trades](06b-gui-trades.md) | Trades table, trade entry/edit, screenshot panel, trade report/journal | `TradesTable`, `TradeDetailPanel`, `ScreenshotPanel`, `TradeReportForm` |
| 6c | [Planning](06c-gui-planning.md) | Trade plans, watchlists | `TradePlanPage`, `WatchlistPage` |
| 6d | [Accounts](06d-gui-accounts.md) | Account management, Account Review wizard, balance history | `AccountPage`, `AccountReviewWizard`, `BalanceHistoryView` |
| 6e | [Scheduling](06e-gui-scheduling.md) | Job scheduling, pipeline monitoring (MCP-first) | `SchedulePage`, `PolicyEditor`, `RunHistoryTable` |
| 6f | [Settings](06f-gui-settings.md) | Market data providers, email config, display mode, tax profile | `ProviderSettingsPage`, `EmailProviderPage`, `DisplayModeSettings` |
| 6g | [Tax Estimator](06g-gui-tax.md) | Tax dashboard, lot viewer, wash sales, what-if, harvesting, quarterly | `TaxDashboard`, `TaxLotViewer`, `WashSaleMonitor`, `WhatIfSimulator`, `LossHarvestingTool`, `QuarterlyPaymentsTracker` |
| 6h | [Calculator](06h-gui-calculator.md) | Position size calculator — Equity, Futures, Options, Forex, Crypto modes | `PositionCalculatorModal`, `InstrumentModeSelector`, `ScenarioComparisonTable`, `CalculationHistory` |
| 6i | [Watchlist Visual](06i-gui-watchlist-visual.md) | Watchlist visual redesign, professional data table, colorblind toggle | `WatchlistTable`, `TickerCard`, `ColorblindToggle` |
| 6j | [Home Dashboard](06j-gui-home.md) | Default startup dashboard, aggregation sections, configurable layout | `HomePage`, `DashboardGrid`, `DashboardSettingsDrawer`, `DashboardSkeleton` |

---

## Loading & Startup (Performance-Tracked)

> **Research basis**: OpenAI GPT-5.2 analysis of Electron startup best practices ([BrowserWindow API](https://www.electronjs.org/docs/api/browser-window), [context isolation](https://www.electronjs.org/docs/latest/tutorial/context-isolation)) and route-level code splitting via TanStack Router's [`lazy()`](https://tanstack.com/router/latest/docs/framework/react/guide/code-splitting) route definitions. Professional trading platform patterns (thinkorswim, TradingView Desktop, TradeStation) consistently use "shell first, content second" rendering.

### Startup Sequence

```
 Electron Main Process                  Renderer (React)
 ─────────────────────                  ─────────────────
 1. Show splash.html (lightweight)
    BrowserWindow with themed background

 2. Start Python backend ──────────────▶ (child_process.spawn)
    └─ Log: startup.python_spawn_ms
    └─ Health check polling (100ms → 5s)

 3. On Python healthy:
    Create main BrowserWindow
    show: false  
    Load index.html ──────────────────▶ 4. React mounts AppShell
    └─ Log: startup.renderer_load_ms       └─ Nav rail renders (sync)
                                            └─ Accounts Home skeleton
                                            └─ Log: startup.shell_paint_ms

 5. win.once('ready-to-show')  
    └─ win.show() ─────────────────────▶ 6. User sees app structure
    └─ Hide splash window                  (skeleton screens, not blank)
    └─ Log: startup.window_show_ms

                                        7. Fetch MRU accounts + balances
                                           └─ Skeleton → data hydrate
                                           └─ Log: startup.data_ready_ms

                                        8. Lazy modules pre-cached on idle
                                           └─ Trade Planning, Scheduling,
                                              Settings, Tax loaded in bg
                                           └─ Log: startup.lazy_preload_ms
```

### Performance Logging

All startup timestamps are emitted to the Python backend logging system via the REST API (`POST /api/v1/logs`). Each metric is logged as a structured event:

| Metric Key | Description | Target |
|---|---|---|
| `startup.python_spawn_ms` | Time from Electron launch to Python process ready | < 2000ms |
| `startup.renderer_load_ms` | Time from `BrowserWindow.loadURL()` to React mount | < 300ms |
| `startup.shell_paint_ms` | Time from React mount to app shell first paint | < 200ms |
| `startup.window_show_ms` | Time from launch to `win.show()` (user sees UI) | < 500ms |
| `startup.data_ready_ms` | Time from launch to MRU accounts data displayed | < 2000ms |
| `startup.lazy_preload_ms` | Time from launch to all lazy modules pre-cached | < 5000ms |

```typescript
// ui/electron/preload.ts — performance bridge

import { contextBridge, ipcRenderer } from 'electron';

contextBridge.exposeInMainWorld('zorivest', {
  logStartupMetric: (key: string, value: number) =>
    ipcRenderer.send('startup-metric', { key, value, timestamp: Date.now() }),
});
```

```typescript
// ui/electron/main.ts — forward metrics to Python backend

ipcMain.on('startup-metric', (_event, metric) => {
  fetch(`${BACKEND_URL}/api/v1/logs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      level: 'info',
      component: 'startup',
      message: `${metric.key}: ${metric.value}ms`,
      data: metric,
    }),
  }).catch((err) => {
    console.warn('[startup-metric] Failed to forward metric:', metric.key, err.message);
  }); // non-blocking — warn but don't crash startup
});
```

### Progressive Loading Strategy

| Time Window | What Renders | Fallback |
|---|---|---|
| 0–500ms | App shell: nav rail + header + Accounts Home skeleton | Themed `backgroundColor` (no white flash) |
| 500ms–2s | MRU cards populate, All Accounts table fills | Skeleton placeholders with pulse animation |
| > 2s | Localized "Still loading…" message per panel | Only in the affected panel, never full-screen block |

**Key rules:**
- **No full-screen splash/spinner in the React app** — Python cold start uses a separate Electron `splash.html` window; once the main window appears, only skeleton screens are shown
- **Skeleton screens** over shimmer effects (trading context; shimmer is distracting)
- **TanStack Router `lazy()`** for all routes except Accounts Home (Accounts Home is in the main bundle)
- **Idle pre-caching**: after Accounts Home renders, use `requestIdleCallback` to pre-import lazy modules

**Technology stack** (see `docs/research/gui-shell-foundation/decision.md` for rationale):
- **Routing**: TanStack Router v1 with `createHashHistory()` (required for Electron)
- **Server state**: TanStack Query v5 (`staleTime: 0` for financial data)
- **Local UI state**: Zustand v5 (slice pattern, `persist` → electron-store)
- **CSS**: Tailwind CSS v4 with `@tailwindcss/vite`
- **Components**: shadcn/ui (Mira preset for dense layout) + Radix UI
- **Performance**: React Compiler 1.0 (Babel plugin, automatic memoization)
- **Forms**: React Hook Form v7 + Zod (`useWatch()` not `watch()` for React Compiler compat)

```typescript
// ui/src/renderer/src/router.tsx — TanStack Router with hash history + lazy code splitting

import {
  createRouter,
  createHashHistory,
  createRootRoute,
  createRoute,
  Outlet,
} from '@tanstack/react-router'
import { AppShell } from './components/layout/AppShell'
import { HomePage } from './features/home/HomePage'  // in main bundle (startup page)
import { ModuleSkeleton } from './components/ModuleSkeleton'

const hashHistory = createHashHistory()

const rootRoute = createRootRoute({
  component: () => (
    <AppShell>
      <Outlet />
    </AppShell>
  ),
  pendingComponent: ModuleSkeleton,
})

const homeRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: HomePage,
})

const accountsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/accounts/$',
}).lazy(() => import('./features/accounts/AccountsHome'))

const tradesRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/trades/$',
}).lazy(() => import('./features/trades/TradesLayout'))

const planningRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/planning/$',
}).lazy(() => import('./features/planning/PlanningLayout'))

const schedulingRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/scheduling/$',
}).lazy(() => import('./features/scheduling/SchedulingLayout'))

const settingsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/settings/$',
}).lazy(() => import('./features/settings/SettingsLayout'))

const taxRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/tax/$',
}).lazy(() => import('./features/tax/TaxEstimator'))

const routeTree = rootRoute.addChildren([
  homeRoute,
  accountsRoute,
  tradesRoute,
  planningRoute,
  schedulingRoute,
  settingsRoute,
  taxRoute,
])

export const router = createRouter({
  routeTree,
  history: hashHistory,
  defaultPreload: 'intent',  // Preload on hover/focus
})
```

---

## Main Window Layout

> **Research basis**: Professional trading platforms uniformly use persistent navigation (thinkorswim module switching, TradeStation desktop/workspaces, TradingView tabs + side panels). A left navigation rail provides stable spatial memory, scales with feature growth, and keeps configuration separate from core workflows.

### App Shell Architecture

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│  ┌──────┐  ┌───────────────────────────────────────────────────────────────────────────┐ │
│  │      │  │  CONTENT HEADER                                                          │ │
│  │  NAV │  │  ┌─────────────────────────────────────┐  🔔 Notifications  ⌘K Search   │ │
│  │ RAIL │  │  │ Active Account: Main Trading (IBKR) │                                 │ │
│  │      │  │  └─────────────────────────────────────┘                                 │ │
│  │ ──── │  ├───────────────────────────────────────────────────────────────────────────┤ │
│  │      │  │                                                                           │ │
│  │  💰  │  │  CONTENT AREA                                                            │ │
│  │ Acct │  │                                                                           │ │
│  │      │  │  (Rendered by active route — Accounts Home is default)                   │ │
│  │  📊  │  │                                                                           │ │
│  │ Plan │  │                                                                           │ │
│  │      │  │                                                                           │ │
│  │  📅  │  │                                                                           │ │
│  │ Sched│  │                                                                           │ │
│  │      │  │                                                                           │ │
│  │      │  │                                                                           │ │
│  │      │  │                                                                           │ │
│  │ ──── │  │                                                                           │ │
│  │  ⚙️  │  │                                                                           │ │
│  │ Sett │  │                                                                           │ │
│  └──────┘  └───────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

### Navigation Rail

| Position | Icon | Label | Route | Shortcut | Notes |
|---|---|---|---|---|---|
| Top (1st) | 🏠 | Home | `/` | `Ctrl+1` | **Default route** — Home Dashboard ([06j](06j-gui-home.md)) |
| Top (2nd) | 💰 | Accounts | `/accounts` | `Ctrl+2` | Account management + balance history |
| Top (3rd) | 📈 | Trades | `/trades` | `Ctrl+3` | Trade log, journal, screenshots |
| Top (4th) | 📊 | Planning | `/planning` | `Ctrl+4` | Trade plans, watchlists, calculator access |
| Top (5th) | 📅 | Scheduling | `/scheduling` | `Ctrl+5` | Pipeline management |
| Bottom | ⚙️ | Settings | `/settings` | `Ctrl+,` | Settings, logging, backup/restore (pinned bottom) |

**Rail behavior:**
- Always visible (no auto-hide)
- Active item highlighted with accent bar
- Collapsed mode on windows < 960px width (icons only, no labels)
- Rail width persisted via `usePersistedState('ui.rail.collapsed')`

### Content Header

Always present above the content area. Contains:
- **Active Account indicator** — shows currently selected account name + institution badge
- **Notification bell** — links to notification center
- **Command palette trigger** — `Ctrl+K` search bar (see [06a-gui-shell.md](06a-gui-shell.md))

### Module Internal Navigation

Each nav rail item maps to a module that may contain internal tabs:

| Module | Internal Tabs | Source Sub-File |
|---|---|---|
| Accounts | (single page: Accounts Home) | [06d](06d-gui-accounts.md) |
| Trades | Table · Detail · Journal · Screenshots | [06b](06b-gui-trades.md) |
| Planning | Plans · Watchlists · (Calculator modal) | [06c](06c-gui-planning.md), [06h](06h-gui-calculator.md) |
| Scheduling | Jobs · Run History | [06e](06e-gui-scheduling.md) |
| Settings | Market Data · Email · Display · Tax Profile · Logging · Backup · Service Manager | [06f](06f-gui-settings.md), [10](10-service-daemon.md) |

---

## Accounts Home Dashboard (Default Route)

> The Accounts Home is the **first thing the user sees** after loading. It prioritizes fast account selection and at-a-glance portfolio awareness.

### Layout

```
┌───────────────────────────────────────────────────────────────────────────────────────┐
│  Accounts Home                                                    [Start Review ▶]   │
├───────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                       │
│  ── Quick Access (Most Recently Used) ───────────────────────────────────────────    │
│                                                                                       │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────┐ │
│  │ 💰 Main Trading     │  │ 💰 Roth IRA         │  │ 🏦 Savings          │  │  +  │ │
│  │ IBKR · BROKER       │  │ Schwab · RETIREMENT  │  │ Chase · BANK        │  │ Add │ │
│  │                     │  │                     │  │                     │  │ New │ │
│  │ Balance:            │  │ Balance:            │  │ Balance:            │  │     │ │
│  │ $83,200.00          │  │ $216,100.00         │  │ $45,120.00          │  │     │ │
│  │                     │  │                     │  │                     │  │     │ │
│  │ Last Trade:         │  │ Last Trade:         │  │ Last Trade:         │  │     │ │
│  │ SPY BOT 100@619.61  │  │ QQQ BOT 50@420.30   │  │ —                   │  │     │ │
│  │ Jan 17, 2025        │  │ Jan 15, 2025        │  │                     │  │     │ │
│  │                     │  │                     │  │                     │  │     │ │
│  │ [Select ▶]          │  │ [Select ▶]          │  │ [Select ▶]          │  │     │ │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘  └─────┘ │
│                                                                                       │
│  ── All Accounts ─────────────────────────────────────────────────────────────────   │
│                                                                                       │
│  Filter: [All Types ▼]  Sort: [Last Used ▼]                   Portfolio: $357,220    │
│                                                                                       │
│  ┌──────┬─────────────────────┬───────────┬──────────────┬───────────┬──────────────┐ │
│  │ Type │ Account             │ Inst.     │ Balance      │ Last Used │ Actions      │ │
│  ├──────┼─────────────────────┼───────────┼──────────────┼───────────┼──────────────┤ │
│  │ 💰   │ Main Trading        │ IBKR      │  $83,200.00  │ Today     │ [Select] [⋮]│ │
│  │ 💰   │ Roth IRA            │ Schwab    │ $216,100.00  │ Yesterday │ [Select] [⋮]│ │
│  │ 🏦   │ Savings             │ Chase     │  $45,120.00  │ Jan 15    │ [Select] [⋮]│ │
│  │ 🏦   │ Checking            │ Chase     │  $12,800.00  │ Jan 12    │ [Select] [⋮]│ │
│  │ 🚗   │ Auto Loan           │ Capital1  │ -$18,500.00  │ Jan 1     │ [Select] [⋮]│ │
│  └──────┴─────────────────────┴───────────┴──────────────┴───────────┴──────────────┘ │
│                                                                                       │
└───────────────────────────────────────────────────────────────────────────────────────┘
```

### MRU Card Fields

Each of the 3 MRU cards displays:

| Field | Source | Notes |
|---|---|---|
| Account name | `Account.name` | Primary text |
| Institution + type badge | `Account.institution`, `Account.account_type` | Subtitle with type icon |
| Balance | Latest `BalanceSnapshot.balance` | Formatted with currency symbol |
| Last trade summary | Most recent `Trade` for this account | `{instrument} {action} {quantity}@{price}` + date |
| Select CTA | Button | Sets this account as the active account context |

The **"+ Add New"** card is always the 4th card in the strip — clicking it opens the Account create form (see [06d-gui-accounts.md](06d-gui-accounts.md)).

### MRU Tracking

| Setting Key | Example Value | Storage |
|---|---|---|
| `ui.accounts.mru` | `'["acc-1","acc-3","acc-2"]'` (JSON string) | `SettingModel` via `usePersistedState` |

Updated on every **Select** action. The MRU list stores account IDs ordered by most recent selection. The top 3 are rendered as cards.

**Encoding contract:** The value is stored as a `JSON.stringify()`-encoded array in the `SettingModel.value` string field. The consuming hook is responsible for `JSON.parse()` on read and `JSON.stringify()` on write. This is consistent with the REST settings contract where all values are strings.

### Account Context Linking

> Inspired by thinkorswim's "linking" concept where selecting a symbol in one panel propagates to linked panels.

When the user selects an account (via MRU card, All Accounts table, or the header account selector), the **active account context** is set globally:

```typescript
// ui/src/context/AccountContext.tsx

import { createContext, useContext, useState } from 'react';

interface AccountContextValue {
  activeAccountId: string;       // '' = no account selected
  selectAccount: (accountId: string) => void;
}

const AccountContext = createContext<AccountContextValue>(/* ... */);

export function AccountProvider({ children }: { children: React.ReactNode }) {
  const [activeAccountId, setActiveAccountId] = usePersistedState('ui.accounts.active', '');

  // React Compiler handles memoization automatically — no useCallback needed
  const selectAccount = (id: string) => {
    setActiveAccountId(id);
    // Update MRU list
    updateMruList(id);
  };

  return (
    <AccountContext.Provider value={{ activeAccountId, selectAccount }}>
      {children}
    </AccountContext.Provider>
  );
}

export const useAccountContext = () => useContext(AccountContext);
```

**Modules that consume account context:**

| Module | Behavior When Account Selected |
|---|---|
| **Trades** ([06b](06b-gui-trades.md)) | Filters trades table to selected account |
| **Trade Planning** ([06c](06c-gui-planning.md)) | Pre-fills account in position calculator |
| **Tax Estimator** ([06g](06g-gui-tax.md)) | Scopes tax calculations to selected account |
| **Account Review** ([06d](06d-gui-accounts.md)) | Starts with selected account highlighted |

### REST Endpoints Consumed

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/v1/accounts` | All accounts for the table |
| `GET` | `/api/v1/accounts/{id}/balances?limit=1` | Latest balance per MRU account |
| `GET` | `/api/v1/trades?account_id={id}&limit=1&sort=-date` | Most recent trade per MRU account |
| `GET` | `/api/v1/settings/ui.accounts.mru` | MRU account ID list |

---

## E2E Testing — Incremental Activation Waves

> Playwright Electron E2E test scaffolding exists at `ui/tests/e2e/` (see [testing-strategy.md](testing-strategy.md) §E2E Testing). Tests activate incrementally as GUI pages are built — each wave adds tests as its `data-testid` dependencies are satisfied.

### Wave Activation Schedule

| Wave | Gate MEU | Tests Activated | Cumulative | `data-testid` to Add |
|:----:|----------|-----------------|:----------:|----------------------|
| 0 | **MEU-46** `gui-mcp-status` | `launch.test.ts` (3), `mcp-tool.test.ts` (2) | **5** | Sidebar: `nav-accounts`, `nav-trades`, `nav-planning`, `nav-scheduling`, `nav-settings` |
| 1 | **MEU-47** `gui-trades` | `trade-entry.test.ts` (5), `mode-gating.test.ts` (2) | **12** | `trades-page`, `trade-list`, `trade-row`, `add-trade-btn`, `trade-*-input` |
| 2 | **MEU-71** `gui-accounts` | `persistence.test.ts` (2) | **14** | `accounts-page`, `account-list`, `add-account-btn` |
| 3 | **MEU-74** `gui-backup-restore` | `backup-restore.test.ts` (2) | **16** | `backup-create-btn`, `backup-restore-btn`, `backup-passphrase-input` |
| 4 | **MEU-48** `gui-plans` | `position-size.test.ts` (2) | **18** | `calc-account-size`, `calc-risk-percent`, `calc-result-shares` |
| 5 | **MEU-96/99** import GUI | `import.test.ts` (2) | **20** | `import-file-input`, `import-submit-btn`, `import-result-count` |
| 6 | **MEU-65** `market-data-gui` | `settings-market-data.test.ts` (3: nav, provider list, axe-core) | **23** | `market-data-providers`, `provider-list`, `provider-item`, `provider-detail`, `provider-save-btn`, `provider-test-btn`, `provider-test-all-btn`, `provider-remove-key-btn` |

> [!IMPORTANT]
> **Build before every E2E run.** Wave 0 tests require `npm run build` (alias for `electron-vite build`) to produce `out/main/index.js` and a healthy Python backend (automated by `global-setup.ts`). Playwright launches the compiled bundle, not source files — source changes are invisible until you rebuild.

### `data-testid` Convention

All test IDs are defined in `ui/tests/e2e/test-ids.ts`. Constants use `SCREAMING_SNAKE_CASE`, values use `kebab-case`.

> [!IMPORTANT]
> When implementing any GUI component, add `data-testid` attributes using the constants from `ui/tests/e2e/test-ids.ts`. The MEU is not complete until its wave's E2E tests pass.

### Exit Criterion

**MEU-170** (`e2e-all-green`): All 20 Playwright E2E tests pass end-to-end after all waves are activated.

#### Implementation Notes (from MEU-47 cycle, 2026-03-18)

**CI**: `electron-vite build` and `tsc --noEmit` were added to `.github/workflows/ci.yml` (UI Tests job) during MEU-47. E2E tests are commented out pending `xvfb` or `windows-latest` runner setup.

**Lessons learned** (GUI critical review, 4 passes):

1. **Stale bundle gate**: Playwright launches `out/main/index.js`, not source files. Every source change to `ui/src/main/` requires `npm run build` before E2E. This caused a 4-pass review loop where source fixes were invisible to E2E. CI now catches this. See [testing-strategy.md §E2E Testing](testing-strategy.md) and [quality-gate skill](../../.agent/skills/quality-gate/SKILL.md) §GUI-Phase Gates.

2. **Splash window isolation**: `AppPage.launch()` must use `waitForEvent('window')` after `firstWindow()` to get the main window, not the splash. The splash is the first `BrowserWindow` created (400×300, frameless) and closes ~500ms later. See [AppPage.ts](../../ui/tests/e2e/pages/AppPage.ts).

3. **Mock-contract drift**: TS unit test mocks must match Python API response shapes exactly. The `locked` vs `is_locked` mismatch passed 122 unit tests while breaking the app at runtime. See [testing-strategy.md §Mock-Contract Validation Rule](testing-strategy.md).

4. **`xvfb` requirement**: Electron E2E on Linux CI needs `xvfb-run` wrapper or `uses: GabrielBB/xvfb-action@v1`. Alternative: use `windows-latest` runner (matches dev environment).

---

## Exit Criteria

- Electron app launches, spawns Python backend
- **App shell (nav rail + header) renders within 500ms** (skeleton state)
- **MRU account cards populate within 2s** from launch
- **Lazy modules load on navigation** without full-page spinner
- **Startup performance metrics logged** to Python backend
- Accounts Home displays MRU cards and All Accounts table
- Account selection sets global context consumed by other modules
- Trades table displays with image badges and full-field columns
- Screenshot panel supports upload, paste, and lightbox viewing
- Display mode toggles ($, %, % mode) work correctly
- Market Data Settings page displays all 12 providers with connection status
- Trade plans and watchlists support CRUD operations
- Position calculator computes all outputs, supports multi-scenario comparison
- Tax Dashboard displays YTD summary cards with live data
- Tax Lot Viewer shows open/closed lots with ST/LT classification
- Wash Sale Monitor visualizes active chains and prevention alerts
- What-If Simulator previews tax impact before trade execution
- Account Review wizard guides balance updates per account
- Schedule page displays pipeline policies with cron previews
- Notification toasts display by category with suppression preferences
- Window position/size restored on app restart
- Command palette opens on Ctrl+K, fuzzy-searches all registered entries
- Theme preference persists across sessions
- Service Manager panel shows status, allows start/stop/restart, toggles auto-start

## Outputs

- Electron main process with Python backend lifecycle management
- **AppShell component** with left nav rail + content header + route outlet
- **AccountsHome page** with MRU cards, "Add New" card, and All Accounts table
- **AccountContext provider** for global account selection
- **Startup performance logging** via preload bridge → REST → Python logger
- **Route-level code splitting** via TanStack Router `lazy()` route definitions + `pendingComponent`
- React components across all 8 sub-files (see table above)
- React hooks: `useNotifications()`, `usePersistedState()`, `useCommandPalette()`, `useAccountContext()`
- TanStack Table integration with image badge column
- Static command registry: `commandRegistry.ts`
- Window state persistence via `electron-store`
