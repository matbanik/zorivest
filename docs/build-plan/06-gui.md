# Phase 6: GUI (Electron + React)

> Part of [Zorivest Build Plan](../BUILD_PLAN.md) | Prerequisites: [Phase 4](04-rest-api.md) | Market Data Settings page requires [Phase 8](08-market-data.md) | Outputs: [Phase 7](07-distribution.md)

---

## Goal

Build the desktop GUI last — it's the outermost layer. The Electron shell spawns the Python backend as a child process and the React UI communicates with it via REST on localhost. Use TanStack Table for data grids, Lightweight Charts for financial charts.

This phase is split into eight domain-specific sub-files:

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

---

## Loading & Startup (Performance-Tracked)

> **Research basis**: OpenAI GPT-5.2 analysis of Electron startup best practices ([BrowserWindow API](https://www.electronjs.org/docs/api/browser-window), [context isolation](https://www.electronjs.org/docs/latest/tutorial/context-isolation)) and React code-splitting via [`React.lazy()`](https://react.dev/reference/react/lazy). Professional trading platform patterns (thinkorswim, TradingView Desktop, TradeStation) consistently use "shell first, content second" rendering.

### Startup Sequence

```
 Electron Main Process                  Renderer (React)
 ─────────────────────                  ─────────────────
 1. Create BrowserWindow                
    show: false                         
    backgroundColor: store.get('theme') === 'light'
      ? '#f5f5f5' : '#1a1a2e'
    (reads persisted theme from electron-store)

 2. Start Python backend ──────────────▶ (child_process.spawn)
    └─ Log: startup.python_spawn_ms     

 3. Load index.html ───────────────────▶ 4. React mounts AppShell
    └─ Log: startup.renderer_load_ms       └─ Nav rail renders (sync)
                                            └─ Accounts Home skeleton
                                            └─ Log: startup.shell_paint_ms

 5. win.once('ready-to-show')           
    └─ win.show() ─────────────────────▶ 6. User sees app structure
    └─ Log: startup.window_show_ms         (skeleton screens, not blank)

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
- **No full-screen splash/spinner** — the app shell is the splash screen
- **Skeleton screens** over shimmer effects (trading context; shimmer is distracting)
- **`React.lazy()`** for all routes except Accounts Home (Accounts Home is in the main bundle)
- **Idle pre-caching**: after Accounts Home renders, use `requestIdleCallback` to pre-import lazy modules

```typescript
// ui/src/App.tsx — route-level code splitting

import { lazy, Suspense } from 'react';
import { AppShell } from './components/AppShell';
import { AccountsHome } from './pages/AccountsHome';  // in main bundle
import { ModuleSkeleton } from './components/ModuleSkeleton';

const Trades        = lazy(() => import('./pages/Trades'));
const TradePlanning = lazy(() => import('./pages/TradePlanning'));
const Scheduling    = lazy(() => import('./pages/Scheduling'));
const Settings      = lazy(() => import('./pages/Settings'));
const TaxEstimator  = lazy(() => import('./pages/TaxEstimator'));

export function App() {
  return (
    <AppShell>
      <Suspense fallback={<ModuleSkeleton />}>
        <Routes>
          <Route path="/" element={<AccountsHome />} />
          <Route path="/trades/*" element={<Trades />} />
          <Route path="/planning/*" element={<TradePlanning />} />
          <Route path="/scheduling/*" element={<Scheduling />} />
          <Route path="/settings/*" element={<Settings />} />
          <Route path="/tax/*" element={<TaxEstimator />} />
          {/* Sub-routes handled within each lazy module */}
        </Routes>
      </Suspense>
    </AppShell>
  );
}
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
| Top (1st) | 💰 | Accounts | `/` | `Ctrl+1` | **Default route** — Accounts Home dashboard |
| Top (2nd) | 📈 | Trades | `/trades` | `Ctrl+2` | Trade log, journal, screenshots |
| Top (3rd) | 📊 | Planning | `/planning` | `Ctrl+3` | Trade plans, watchlists, calculator access |
| Top (4th) | 📅 | Scheduling | `/scheduling` | `Ctrl+4` | Pipeline management |
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
| Settings | Market Data · Email · Display · Tax Profile · Logging · Backup | [06f](06f-gui-settings.md) |

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

import { createContext, useContext, useState, useCallback } from 'react';

interface AccountContextValue {
  activeAccountId: string;       // '' = no account selected
  selectAccount: (accountId: string) => void;
}

const AccountContext = createContext<AccountContextValue>(/* ... */);

export function AccountProvider({ children }: { children: React.ReactNode }) {
  const [activeAccountId, setActiveAccountId] = usePersistedState('ui.accounts.active', '');

  const selectAccount = useCallback((id: string) => {
    setActiveAccountId(id);
    // Update MRU list
    updateMruList(id);
  }, []);

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
- Market Data Settings page displays all 9 providers with connection status
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

## Outputs

- Electron main process with Python backend lifecycle management
- **AppShell component** with left nav rail + content header + route outlet
- **AccountsHome page** with MRU cards, "Add New" card, and All Accounts table
- **AccountContext provider** for global account selection
- **Startup performance logging** via preload bridge → REST → Python logger
- **Route-level code splitting** via `React.lazy()` + `Suspense` + `ModuleSkeleton`
- React components across all 8 sub-files (see table above)
- React hooks: `useNotifications()`, `usePersistedState()`, `useCommandPalette()`, `useAccountContext()`
- TanStack Table integration with image badge column
- Static command registry: `commandRegistry.ts`
- Window state persistence via `electron-store`
