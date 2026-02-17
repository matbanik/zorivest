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

type NotificationCategory = 'success' | 'info' | 'warning' | 'error' | 'confirmation';

interface NotificationPreference {
  category: NotificationCategory;
  enabled: boolean;
  defaultAction: 'cancel' | 'confirm';  // for confirmation only
}

export function useNotifications() {
  const { data: prefs } = useQuery<Record<string, string>>({
    queryKey: ['settings'],
    queryFn: () => fetch(`${API}/settings`).then(r => r.json()),
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
| Sidebar width | `SettingModel` via REST | App launch | P2 |

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
import { useCallback, useRef } from 'react';

const API = (window as any).__ZORIVEST_API_URL__ ?? 'http://localhost:8765/api/v1';

export function usePersistedState<T extends string>(key: string, defaultValue: T): [T, (value: T) => void] {
  const queryClient = useQueryClient();
  const debounceRef = useRef<NodeJS.Timeout>();

  const { data } = useQuery<string>({
    queryKey: ['settings', key],
    queryFn: () => fetch(`${API}/settings/${key}`).then(r => r.json()).then(d => d.value),
    placeholderData: defaultValue,
  });

  const mutation = useMutation({
    mutationFn: (value: string) =>
      fetch(`${API}/settings`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ [key]: value }),
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['settings', key] }),
  });

  const setValue = useCallback((value: T) => {
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => mutation.mutate(value), 500);
  }, [mutation]);

  return [data as T ?? defaultValue, setValue];
}
```

### Settings Key Convention

All UI state keys follow namespaced dot notation persisted in the `SettingModel` table (see [Phase 2](02-infrastructure.md)):

| Key Pattern | Example Value |
|---|---|
| `ui.theme` | `"dark"` |
| `ui.activePage` | `"/trades"` |
| `ui.panel.screenshot.collapsed` | `"true"` |
| `ui.sidebar.width` | `"280"` |
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

import { CommandRegistryEntry } from './types';

// Populated at app init — every page/action registers here
export const staticRegistry: CommandRegistryEntry[] = [
  // Navigation
  { id: 'nav:dashboard',   label: 'Dashboard',        category: 'navigation', keywords: ['home', 'overview'],         action: () => navigate('/'),          shortcut: 'Ctrl+1' },
  { id: 'nav:trades',      label: 'Trades',           category: 'navigation', keywords: ['executions', 'positions'],  action: () => navigate('/trades'),    shortcut: 'Ctrl+2' },
  { id: 'nav:plans',       label: 'Trade Plans',      category: 'navigation', keywords: ['thesis', 'strategy'],       action: () => navigate('/plans'),     shortcut: 'Ctrl+3' },
  { id: 'nav:reports',     label: 'Trade Reports',    category: 'navigation', keywords: ['journal', 'review'],        action: () => navigate('/reports') },
  { id: 'nav:watchlists',  label: 'Watchlists',       category: 'navigation', keywords: ['tickers', 'monitor'],       action: () => navigate('/watchlists') },
  { id: 'nav:accounts',    label: 'Accounts',         category: 'navigation', keywords: ['broker', 'bank', 'balance'], action: () => navigate('/accounts') },
  { id: 'nav:schedules',   label: 'Scheduled Jobs',   category: 'navigation', keywords: ['cron', 'pipeline', 'report'], action: () => navigate('/schedules') },

  // Actions
  { id: 'action:calc',     label: 'Position Calculator', category: 'action', keywords: ['size', 'risk', 'shares'],   action: () => openCalculator(),       shortcut: 'Ctrl+Shift+C' },
  { id: 'action:import',   label: 'Import Trades',       category: 'action', keywords: ['upload', 'csv', 'ibkr'],    action: () => openImport() },
  { id: 'action:review',   label: 'Account Review',      category: 'action', keywords: ['balance', 'wizard', 'update'], action: () => openAccountReview() },

  // Settings
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
        action: () => navigate(`/watchlists/${wl.id}?ticker=${item.ticker}`),
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

import { useState, useEffect, useMemo } from 'react';
import Fuse from 'fuse.js';
import { staticRegistry } from '../registry/commandRegistry';
import { useDynamicEntries } from '../registry/useDynamicEntries';
import { CommandRegistryEntry } from '../registry/types';

export function CommandPalette() {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const dynamicEntries = useDynamicEntries();

  const allEntries = useMemo(
    () => [...staticRegistry, ...dynamicEntries],
    [dynamicEntries]
  );

  const fuse = useMemo(
    () => new Fuse(allEntries, { keys: ['label', 'keywords'], threshold: 0.4 }),
    [allEntries]
  );

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

## Exit Criteria

- Electron app launches, spawns Python backend
- Notification toasts display by category with suppression preferences
- Window position/size restored on app restart
- Command palette opens on Ctrl+K, fuzzy-searches all registered entries
- Theme preference persists across sessions
- All registered pages/actions/settings reachable via command palette

## Outputs

- Electron main process with Python backend lifecycle management
- React components: `NotificationProvider`, `CommandPalette`
- React hooks: `useNotifications()`, `usePersistedState()`
- Static command registry: `commandRegistry.ts`
- Dynamic entry composition: `useDynamicEntries.ts`
- Window state persistence via `electron-store`
- Settings key convention for all UI state
