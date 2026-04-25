# Phase 6a: GUI Shell (Electron + React Infrastructure)

> Part of [Phase 6: GUI](06-gui.md) | Prerequisites: [Phase 4](04-rest-api.md) | Outputs: [Phase 7](07-distribution.md)

---

## Goal

Build the Electron shell and foundational React infrastructure that all other GUI pages depend on. The Electron main process spawns the Python backend as a child process; the React UI communicates with it via REST on localhost.

---

## Notification System

> **Source**: Adapted from [`_gui-settings-architecture.md`](../../_inspiration/_gui-settings-architecture.md) DialogManager pattern. Category-based dialog suppression with error-always-show safety guarantee.

### Notification Categories

| Category | Suppressible | Default | Examples |
|----------|-------------|---------|----------|
| `success` | ✅ Yes | Enabled | Trade created, settings saved |
| `info` | ✅ Yes | Enabled | Balance updated, import progress |
| `warning` | ✅ Yes | Enabled | API rate limit approaching |
| `error` | ❌ **Locked** | Enabled | Connection failed, invalid data |
| `confirmation` | ✅ Yes | Enabled | Delete trade?, Remove API key? |

**Rules**:
- `error` toasts are hardcoded to always show — users must see errors
- When `confirmation` is suppressed, the dialog's `defaultAction` executes (default: cancel)
- Suppressed notifications are logged to the console (info is never lost)
- Preferences persisted in `SettingModel` via `PUT /api/v1/settings`

### Implementation

```typescript
// ui/src/components/NotificationProvider.tsx

import { Toaster, toast } from 'sonner';
import { useQuery } from '@tanstack/react-query';
import { apiFetch } from '../lib/api';

type NotificationCategory = 'success' | 'info' | 'warning' | 'error' | 'confirmation';

interface NotificationPreference {
  category: NotificationCategory;
  enabled: boolean;
  defaultAction: 'cancel' | 'confirm';  // for confirmation only
}

export function useNotifications() {
  const { data: prefs } = useQuery<Record<string, string>>({
    queryKey: ['settings'],
    queryFn: () => apiFetch<Record<string, string>>('/settings'),
    select: (data) => data,  // extract notification.*.enabled keys
  });

  const notify = (category: NotificationCategory, message: string) => {
    // Errors always show (locked category)
    if (category === 'error') {
      toast.error(message);
      return;
    }

    // Check suppression preference
    const key = `notification.${category}.enabled`;
    if (prefs?.[key] === 'false') {
      console.log(`[suppressed:${category}] ${message}`);
      return;
    }

    toast[category === 'success' ? 'success' : category === 'warning' ? 'warning' : 'message'](message);
  };

  return { notify };
}
```

---

## UI State Persistence

> **Source**: Adapted from [`_gui-settings-architecture.md`](../../_inspiration/_gui-settings-architecture.md) PersistenceManager. Extends the existing `DisplayModeFlag` persistence to cover all UI state.

### Persisted State

| State | Storage | Restore On | Priority |
|-------|---------|------------|----------|
| Window bounds (x, y, w, h) | `electron-store` (main process) | App launch | P0 |
| Theme (light/dark) | `SettingModel` via REST | App launch | P1 |
| Active page (route) | `SettingModel` via REST | App launch | P1 |
| Panel collapse states | `SettingModel` via REST | Page render | P2 |
| Sidebar width | Zustand + localStorage *(electron-store deferred, see note)* | App launch | P2 |

> [!NOTE]
> **`[UI-ESMSTORE]`**: `electron-store` v9+ is ESM-only, which crashes the electron-vite CJS main process. Pinned to `electron-store@8` (last CJS version). The preload IPC bridge (`window.electronStore`) exists but integration with Zustand's persist middleware is untested. Sidebar width and panel collapse currently use Zustand's default localStorage storage as an interim solution. Will migrate to electron-store bridge when integration is validated.

### Window State (Electron Main Process)

```typescript
// ui/electron/main.ts (additions)

import Store from 'electron-store';

const store = new Store<{ windowBounds: Electron.Rectangle }>();

function createWindow() {
  const bounds = store.get('windowBounds', { x: undefined, y: undefined, width: 1280, height: 800 });
  const win = new BrowserWindow({ ...bounds, /* existing config */ });

  // Save on move/resize (debounced)
  let saveTimeout: NodeJS.Timeout;
  const saveBounds = () => {
    clearTimeout(saveTimeout);
    saveTimeout = setTimeout(() => store.set('windowBounds', win.getBounds()), 500);
  };
  win.on('resize', saveBounds);
  win.on('move', saveBounds);
}
```

### React Persisted State Hook

```typescript
// ui/src/hooks/usePersistedState.ts

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useRef } from 'react';
import { apiFetch } from '../lib/api';  // Uses contextBridge baseUrl + Bearer token

export function usePersistedState<T extends string>(key: string, defaultValue: T): [T, (value: T) => void] {
  const queryClient = useQueryClient();
  const debounceRef = useRef<NodeJS.Timeout>();

  const { data } = useQuery<string>({
    queryKey: ['settings', key],
    queryFn: () => apiFetch<{ value: string }>(`/settings/${key}`).then(d => d.value),
    placeholderData: defaultValue,
  });

  const mutation = useMutation({
    mutationFn: (value: string) =>
      apiFetch(`/settings`, {
        method: 'PUT',
        body: JSON.stringify({ [key]: value }),
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['settings', key] }),
  });

  // React Compiler handles memoization — no useCallback needed
  const setValue = (value: T) => {
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => mutation.mutate(value), 500);
  };

  return [data as T ?? defaultValue, setValue];
}
```

### Settings Key Convention

UI state keys that require server persistence follow namespaced dot notation in the `SettingModel` table (see [Phase 2](02-infrastructure.md)). Client-only state (sidebar width, window bounds) uses Zustand + localStorage *(electron-store deferred `[UI-ESMSTORE]`)*.

| Key Pattern | Example Value |
|---|---|
| `ui.theme` | `"dark"` |
| `ui.activePage` | `"/trades"` |
| `ui.panel.screenshot.collapsed` | `"true"` |
| `notification.success.enabled` | `"true"` |
| `notification.info.enabled` | `"true"` |
| `notification.warning.enabled` | `"true"` |
| `notification.confirmation.enabled` | `"true"` |

---

## Command Palette + Registry

> **Source**: Adapted from [`_gui-settings-architecture.md`](../../_inspiration/_gui-settings-architecture.md) ToolSearchPalette. Implements a VS Code / Linear-style Ctrl+K command palette with a static TypeScript registry for known entries and dynamic composition for data-driven items.

### Why Build This Early

The command palette requires a **registry of all navigable items** — pages, actions, settings sections. Building this registry from the start means every new page/feature automatically registers itself, avoiding a painful retrofit later. The registry also serves as a single source of truth for keyboard shortcuts.

### CommandRegistryEntry Type

```typescript
// ui/src/registry/types.ts

export interface CommandRegistryEntry {
  id: string;              // unique key, e.g. "nav:dashboard", "action:new-trade"
  label: string;           // display text: "Dashboard", "New Trade"
  category: 'navigation' | 'action' | 'settings' | 'search';
  keywords: string[];      // extra search terms for fuzzy matching
  icon?: string;           // icon identifier
  action: () => void;      // callback on selection
  shortcut?: string;       // e.g. "Ctrl+N"
}
```

### Static Registry

```typescript
// ui/src/registry/commandRegistry.ts
// Uses TanStack Router's navigate() — routes aligned with 06-gui.md nav rail table

import { CommandRegistryEntry } from './types';
import { router } from '../router';

const navigate = (to: string) => router.navigate({ to });

// Populated at app init — every page/action registers here
export const staticRegistry: CommandRegistryEntry[] = [
  // Navigation — routes match 06-gui.md nav rail (canonical route map)
  { id: 'nav:home',        label: 'Home',             category: 'navigation', keywords: ['home', 'overview', 'dashboard', 'startup'], action: () => navigate('/'),            shortcut: 'Ctrl+1' },
  { id: 'nav:accounts',    label: 'Accounts',         category: 'navigation', keywords: ['broker', 'bank', 'balance', 'portfolio'], action: () => navigate('/accounts'),    shortcut: 'Ctrl+2' },
  { id: 'nav:trades',      label: 'Trades',           category: 'navigation', keywords: ['executions', 'positions', 'journal', 'review'], action: () => navigate('/trades'),      shortcut: 'Ctrl+3' },
  { id: 'nav:planning',    label: 'Planning',         category: 'navigation', keywords: ['plans', 'thesis', 'strategy', 'watchlists', 'tickers'], action: () => navigate('/planning'),    shortcut: 'Ctrl+4' },
  { id: 'nav:scheduling',  label: 'Scheduling',       category: 'navigation', keywords: ['schedules', 'cron', 'pipeline', 'report', 'jobs'], action: () => navigate('/scheduling'),  shortcut: 'Ctrl+5' },
  { id: 'nav:settings',    label: 'Settings',         category: 'navigation', keywords: ['config', 'preferences', 'theme', 'display'],      action: () => navigate('/settings'),    shortcut: 'Ctrl+,' },

  // Actions
  { id: 'action:calc',     label: 'Position Calculator', category: 'action', keywords: ['size', 'risk', 'shares'],   action: () => openCalculator(),       shortcut: 'Ctrl+Shift+C' },
  { id: 'action:import',   label: 'Import Trades',       category: 'action', keywords: ['upload', 'csv', 'ibkr'],    action: () => openImport() },
  { id: 'action:review',   label: 'Account Review',      category: 'action', keywords: ['balance', 'wizard', 'update'], action: () => openAccountReview() },

  // Settings — subroutes within /settings
  { id: 'settings:market',        label: 'Market Data Providers', category: 'settings', keywords: ['api', 'keys', 'polygon'], action: () => navigate('/settings/market') },
  { id: 'settings:email',         label: 'Email Provider',        category: 'settings', keywords: ['smtp', 'gmail', 'brevo'], action: () => navigate('/settings/email') },
  { id: 'settings:display',       label: 'Display Preferences',   category: 'settings', keywords: ['privacy', 'dollar', 'percent'], action: () => navigate('/settings/display') },
  { id: 'settings:notifications', label: 'Notification Preferences', category: 'settings', keywords: ['toasts', 'alerts', 'suppress'], action: () => navigate('/settings/notifications') },
  { id: 'settings:logging',       label: 'Logging Settings',      category: 'settings', keywords: ['logs', 'debug', 'level', 'jsonl'], action: () => navigate('/settings/logging') },
];
```

### Dynamic Entry Composition

Data-driven entries (trades, tickers) are composed at runtime from existing TanStack Query caches — no separate fetch needed:

```typescript
// ui/src/registry/useDynamicEntries.ts

import { useQueryClient } from '@tanstack/react-query';
import { CommandRegistryEntry } from './types';

export function useDynamicEntries(): CommandRegistryEntry[] {
  const queryClient = useQueryClient();

  // Pull from existing cached data (no extra API calls)
  const trades = queryClient.getQueryData<Trade[]>(['trades']) ?? [];
  const watchlists = queryClient.getQueryData<Watchlist[]>(['watchlists']) ?? [];

  return [
    ...trades.slice(0, 20).map(t => ({
      id: `search:trade:${t.exec_id}`,
      label: `${t.instrument} ${t.action} ${t.quantity}@${t.price}`,
      category: 'search' as const,
      keywords: [t.exec_id, t.instrument, t.account_id],
      action: () => navigate(`/trades/${t.exec_id}`),
    })),
    ...watchlists.flatMap(wl =>
      wl.items.map(item => ({
        id: `search:ticker:${item.ticker}`,
        label: item.ticker,
        category: 'search' as const,
        keywords: [wl.name],
        action: () => navigate(`/planning/watchlists/${wl.id}?ticker=${item.ticker}`),
      }))
    ),
  ];
}
```

### CommandPalette Component

```
┌──────────────────────────────────────────────────┐
│  🔍  Type to search...                    Ctrl+K │
├──────────────────────────────────────────────────┤
│  NAVIGATION                                      │
│  ▸ Dashboard                           Ctrl+1    │
│  ▸ Trades                              Ctrl+2    │
│  ▸ Trade Plans                         Ctrl+3    │
│                                                  │
│  ACTIONS                                         │
│  ▸ Position Calculator               Ctrl+⇧+C   │
│  ▸ Import Trades                                 │
│  ▸ Account Review                                │
│                                                  │
│  SETTINGS                                        │
│  ▸ Market Data Providers                         │
│  ▸ Email Provider                                │
│  ▸ Display Preferences                           │
│  ▸ Notification Preferences                      │
├──────────────────────────────────────────────────┤
│  ↑↓ Navigate  ⏎ Select  Esc Close               │
└──────────────────────────────────────────────────┘
```

```typescript
// ui/src/components/CommandPalette.tsx

import { useState, useEffect } from 'react';
import Fuse from 'fuse.js';
import { staticRegistry } from '../registry/commandRegistry';
import { useDynamicEntries } from '../registry/useDynamicEntries';
import { CommandRegistryEntry } from '../registry/types';

// NOTE: React Compiler handles memoization automatically — do NOT add useMemo/useCallback
export function CommandPalette() {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const dynamicEntries = useDynamicEntries();

  const allEntries = [...staticRegistry, ...dynamicEntries];

  const fuse = new Fuse(allEntries, { keys: ['label', 'keywords'], threshold: 0.4 });

  const results = query
    ? fuse.search(query).map(r => r.item)
    : allEntries;  // show all when empty, grouped by category

  // Global Ctrl+K listener
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.key === 'k') {
        e.preventDefault();
        setIsOpen(prev => !prev);
        setQuery('');
        setSelectedIndex(0);
      }
      if (e.key === 'Escape') setIsOpen(false);
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  // Keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') setSelectedIndex(i => Math.min(i + 1, results.length - 1));
    if (e.key === 'ArrowUp') setSelectedIndex(i => Math.max(i - 1, 0));
    if (e.key === 'Enter' && results[selectedIndex]) {
      results[selectedIndex].action();
      setIsOpen(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="command-palette-overlay" onClick={() => setIsOpen(false)}>
      <div className="command-palette" onClick={e => e.stopPropagation()}>
        <input
          autoFocus
          placeholder="Type to search..."
          value={query}
          onChange={e => { setQuery(e.target.value); setSelectedIndex(0); }}
          onKeyDown={handleKeyDown}
        />
        <ul>
          {results.map((entry, i) => (
            <li key={entry.id}
                className={i === selectedIndex ? 'selected' : ''}
                onClick={() => { entry.action(); setIsOpen(false); }}>
              <span className={`badge badge-${entry.category}`}>{entry.category}</span>
              <span>{entry.label}</span>
              {entry.shortcut && <kbd>{entry.shortcut}</kbd>}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
```

### Design Decisions (vs. Inspiration Doc)

| Inspiration Feature | Build Plan Decision | Rationale |
|---|---|---|
| `rapidfuzz` (Python) | `fuse.js` (JavaScript) | JS equivalent, ~5KB gzipped, zero deps |
| Database-backed tool registry | Static TS registry + query cache composition | All entries known at compile time; data items come from existing caches |
| Compact bar showing current tool | Full-screen overlay palette | Standard desktop pattern (VS Code/Linear); overlay avoids layout shifts |
| Recent/favorite tool tracking | Recent picks shown when query empty | Defer favorites to later — recents are sufficient for MVP |

---

## Build Tool — electron-vite `[Research-backed: Gemini §Build Pipeline, Claude ADR-1]`

electron-vite replaces standalone Vite for Electron-aware builds. It provides three separate Vite configs (main, preload, renderer) in a single `electron.vite.config.ts`. See `docs/research/gui-shell-foundation/ai-instructions.md` §2 for the config template.

---

## Security — Ephemeral Bearer Token `[Research-backed: Gemini §Security Architecture]`

Every app launch generates a `crypto.randomBytes(32).toString('hex')` nonce:
1. Passed to Python subprocess via spawn args: `['--token', nonce]`
2. Exposed to renderer via `contextBridge.exposeInMainWorld('api', { token })`
3. TanStack Query `queryFn` includes `Authorization: Bearer {token}` header
4. FastAPI middleware validates token on every request
5. BrowserWindow CSP: `default-src 'self'; connect-src 'self' http://localhost:*`

See `docs/research/gui-shell-foundation/ai-instructions.md` §3 for BrowserWindow settings and §4 for PythonManager skeleton.

---

## Startup — Splash Window + Python Health Check `[Research-backed: Claude ADR-7]`

1. `splash.html` — lightweight HTML/CSS (no React), shown immediately via `BrowserWindow({ show: true })`
2. Main window created with `show: false`
3. PythonManager spawns Python, polls `GET /health` with exponential backoff (100ms → 5s cap)
4. On healthy: hide splash, show main window
5. On timeout (30s): show error + retry button in splash

See `docs/research/gui-shell-foundation/ai-instructions.md` §4 for PythonManager class.

---

## TanStack Query Configuration `[Research-backed: Claude ADR-3, synthesis §staleTime]`

```typescript
// Trading-specific query client defaults
queries: {
  staleTime: 0,              // Financial data is ALWAYS stale — always background-refetch
  gcTime: 5 * 60 * 1000,     // 5min — prevent cache bloat in 8-16hr sessions
  refetchOnWindowFocus: true, // Re-validate when trader returns
  retry: 2,                  // Retry failed reads twice
}
mutations: {
  retry: false,              // NEVER auto-retry financial transactions
}
```

Show "last updated" timestamps on all data displays.

---

## Local UI State — Zustand `[Research-backed: Claude ADR-5, synthesis §Zustand]`

Zustand handles fast, client-only UI state that doesn't need server persistence:
- Sidebar drag width, dialog visibility, column sort order, command palette state
- Slice pattern: one store per feature module (`useTradesStore`, `useLayoutStore`)
- `persist` middleware pipes to localStorage *(electron-store deferred `[UI-ESMSTORE]`)*
- `getState()` available outside React (IPC handlers, Electron main → renderer)

**Coexistence**: `usePersistedState` (TanStack Query + REST → SQLCipher) remains for server-persisted settings (theme, active account, panel collapse). Zustand is a **different layer**.

See `docs/research/gui-shell-foundation/ai-instructions.md` §7 for store pattern.

---

## React Compiler `[Research-backed: Claude ADR-6, synthesis §React Compiler]`

Enabled as Babel plugin in electron-vite renderer config (see `ai-instructions.md` §2).

**Rules for new code:**
- Do NOT write manual `useMemo`, `useCallback`, or `React.memo` — compiler handles it
- Use `useWatch()` not `watch()` with React Hook Form
- Escape hatch: `"use no memo"` directive per-component if compiler causes issues

---

## shadcn/ui Mira Preset `[Research-backed: Claude ADR-4]`

- Initialize with `npx shadcn@latest init --defaults --force`
- Mira preset provides compact, dense spacing for Bloomberg-grade trading density
- Dark-first theme with Dracula-based tokens from `style-guide-zorivest.md`
- Covers Tier 1 accessibility: ARIA landmarks, focus-visible ring, skip-to-content, heading hierarchy

---

## Python Spawn — Production Mode `[Research-backed: Gemini §Python Lifecycle, Claude ADR-7]`

- **Dev**: `uv run uvicorn` with `stdio: 'pipe'`
- **Production**: PyInstaller `--onedir` binary at `process.resourcesPath/python/zorivest.exe` with `stdio: 'ignore'`
- `stdio: 'ignore'` prevents the 64KB OS pipe buffer from filling when Python logs heavily
- Process tree kill on Windows (`taskkill /T`) when app exits to prevent orphaned Python processes
- Orphan detection: Python checks parent PID heartbeat

See `docs/research/gui-shell-foundation/ai-instructions.md` §4 for PythonManager.

---

## Accessibility Infrastructure `[Spec: WCAG 2.1 AA; Research-backed: style-guide-zorivest.md §9]`

Tier 1 features built into the shell (MEU-43):
- Keyboard navigation (Tab order, focus management)
- Focus-visible ring: `2px solid cyan`, `2px` offset
- ARIA landmarks: `<nav>`, `<main>`, `<aside>`, `<header>`
- Skip-to-content link (hidden until focused)
- Heading hierarchy: single `<h1>`, sequential structure
- `<html lang="en">`
- `prefers-reduced-motion` media query
- Color contrast ≥ 4.5:1 (enforced via token palette)
- Semantic HTML (`<button>`, `<a>`, `<input>`, never `<div onClick>`)

See `docs/research/gui-shell-foundation/style-guide-zorivest.md` §9 for full table.

---

## Design System Reference `[Research-backed: style-guide-zorivest.md]`

The visual design system is defined in `docs/research/gui-shell-foundation/style-guide-zorivest.md`:
- §0: Cognitive Load Balance Equation + 5-point per-screen protocol
- §1-§6: Design tokens (colors, typography, spacing, radius, effects, motion)
- §9: Accessibility infrastructure (Tier 1)
- §10: Tailwind `@theme` block template for `globals.css`

---

## Exit Criteria

- Electron app launches with splash window, spawns Python backend with ephemeral Bearer token
- Health check polling detects Python readiness, transitions splash → main window
- Notification toasts display by category with suppression preferences
- Window position/size restored on app restart (via Zustand + localStorage; electron-store deferred `[UI-ESMSTORE]`)
- Command palette opens on Ctrl+K, fuzzy-searches all registered entries
- Theme preference persists across sessions (via `usePersistedState`)
- All registered pages/actions/settings reachable via command palette
- TanStack Router hash routing works for all 5 primary routes
- Accessibility: skip-to-content link, focus-visible ring, ARIA landmarks present
- Security: Bearer token validated on REST requests, CSP header set

## Outputs

- Electron main process with PythonManager lifecycle management + ephemeral Bearer token
- Splash window (`splash.html`) for cold start
- React components: `NotificationProvider`, `CommandPalette`, `AppShell`, `NavRail`
- React hooks: `useNotifications()`, `usePersistedState()`
- TanStack Router configuration with hash history
- TanStack Query client with trading-specific defaults
- Zustand layout store with persist middleware
- Static command registry: `commandRegistry.ts` (routes aligned with `06-gui.md`)
- Dynamic entry composition: `useDynamicEntries.ts`
- Window state persistence via localStorage *(electron-store deferred `[UI-ESMSTORE]`)*
- `globals.css` with Tailwind `@theme` block from style guide
- Settings key convention for all UI state
