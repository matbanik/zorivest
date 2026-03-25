# GUI Shell Foundation — AI Instructions

> Implementation instructions for MEU-43 (Electron Lifecycle), MEU-44 (AppShell + Navigation), MEU-45 (Command Palette + Window State).
> All rules tagged per AGENTS.md source-basis requirement.

---

## 1. Target Directory Structure `[Research-backed: Claude ADR-9]`

Create the following structure when scaffolding `ui/`:

```
ui/
├── src/
│   ├── main/
│   │   ├── index.ts              # BrowserWindow creation, Python spawn, IPC
│   │   ├── python-manager.ts     # PythonManager class
│   │   └── splash.html           # Lightweight splash (pure HTML/CSS, no React)
│   ├── preload/
│   │   └── index.ts              # contextBridge.exposeInMainWorld()
│   └── renderer/
│       ├── index.html            # Entry HTML
│       └── src/
│           ├── app.tsx           # Root with QueryClientProvider + RouterProvider
│           ├── router.tsx        # TanStack Router definition
│           ├── globals.css       # Tailwind @theme block from style-guide-zorivest.md §10
│           ├── components/
│           │   ├── ui/           # shadcn/ui components (Mira preset)
│           │   └── layout/
│           │       ├── AppShell.tsx
│           │       ├── NavRail.tsx
│           │       ├── Header.tsx
│           │       └── StatusFooter.tsx
│           ├── features/
│           │   ├── accounts/     # MEU-46+ content, stub only in MEU-44
│           │   ├── trades/
│           │   ├── planning/
│           │   ├── scheduling/
│           │   └── settings/     # MEU-44 settings panel
│           ├── hooks/
│           │   └── usePersistedState.ts
│           ├── lib/
│           │   ├── api.ts        # Fetch wrapper with Bearer token
│           │   └── query-client.ts
│           └── stores/
│               └── layout.ts     # Global Zustand store
├── electron.vite.config.ts
├── electron-builder.yml
├── package.json
├── tsconfig.json
├── tsconfig.node.json
└── tsconfig.web.json
```

---

## 2. electron-vite Config Template `[Research-backed: Gemini §Build Pipeline, Claude ADR-1]`

```typescript
// electron.vite.config.ts
import { defineConfig, externalizeDepsPlugin } from 'electron-vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  main: {
    plugins: [externalizeDepsPlugin()],
  },
  preload: {
    plugins: [externalizeDepsPlugin()],
  },
  renderer: {
    plugins: [
      react({
        babel: {
          plugins: [['babel-plugin-react-compiler', {}]]  // React Compiler
        }
      }),
      tailwindcss(),
    ],
  },
})
```

---

## 3. BrowserWindow Security Settings `[Research-backed: Gemini §Security Architecture, Claude ADR-7]`

```typescript
// src/main/index.ts
const mainWindow = new BrowserWindow({
  width: 1440,
  height: 900,
  minWidth: 1024,
  minHeight: 600,
  show: false,  // Show after Python is ready
  webPreferences: {
    preload: join(__dirname, '../preload/index.js'),
    nodeIntegration: false,
    contextIsolation: true,
    sandbox: true,
    webSecurity: true,
  },
})

// Block external navigation
mainWindow.webContents.on('will-navigate', (event, url) => {
  if (!url.startsWith('file://')) {
    event.preventDefault()
  }
})

// Block new window creation
mainWindow.webContents.setWindowOpenHandler(() => ({ action: 'deny' }))
```

---

## 4. PythonManager Class Skeleton `[Research-backed: Gemini §Python Lifecycle, Claude ADR-7]`

```typescript
// src/main/python-manager.ts
import { spawn, ChildProcess } from 'child_process'
import { createServer } from 'net'
import { randomBytes } from 'crypto'
import { join } from 'path'
import { app } from 'electron'

export class PythonManager {
  private process: ChildProcess | null = null
  private port: number = 0
  private token: string = ''

  /** Generate ephemeral Bearer token */
  generateToken(): string {
    this.token = randomBytes(32).toString('hex')
    return this.token
  }

  /** Allocate a free port dynamically */
  async allocatePort(): Promise<number> {
    return new Promise((resolve) => {
      const srv = createServer()
      srv.listen(0, () => {
        this.port = (srv.address() as any).port
        srv.close(() => resolve(this.port))
      })
    })
  }

  /** Spawn Python subprocess */
  async start(): Promise<void> {
    const pythonPath = app.isPackaged
      ? join(process.resourcesPath, 'python', 'zorivest.exe')
      : 'uv'

    const args = app.isPackaged
      ? ['--port', String(this.port), '--token', this.token]
      : ['run', 'uvicorn', 'zorivest.api.app:create_app', '--factory',
         '--port', String(this.port), '--host', '127.0.0.1']

    this.process = spawn(pythonPath, args, {
      stdio: app.isPackaged ? 'ignore' : 'pipe',  // [Research-backed: Gemini §Stdio]
    })
  }

  /** Health check with exponential backoff */
  async waitForReady(maxWaitMs = 30_000): Promise<boolean> {
    const startTime = Date.now()
    let delay = 100  // Start at 100ms

    while (Date.now() - startTime < maxWaitMs) {
      try {
        const res = await fetch(`http://127.0.0.1:${this.port}/health`, {
          headers: { Authorization: `Bearer ${this.token}` },
        })
        if (res.ok) return true
      } catch {
        // Python not ready yet
      }
      await new Promise(r => setTimeout(r, delay))
      delay = Math.min(delay * 2, 5_000)  // Cap at 5s
    }
    return false
  }

  /** Graceful shutdown */
  async stop(): Promise<void> {
    if (!this.process) return
    try {
      await fetch(`http://127.0.0.1:${this.port}/shutdown`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${this.token}` },
      })
      // Wait up to 5s for graceful exit
      await new Promise<void>((resolve) => {
        const timer = setTimeout(() => {
          this.process?.kill()  // Force kill if still running
          resolve()
        }, 5_000)
        this.process?.on('exit', () => { clearTimeout(timer); resolve() })
      })
    } catch {
      this.process?.kill()
    }
    this.process = null
  }

  get baseUrl(): string { return `http://127.0.0.1:${this.port}` }
  get authToken(): string { return this.token }
}
```

---

## 5. TanStack Router Setup `[Research-backed: Claude ADR-2; Human-approved: user confirmed]`

```typescript
// src/renderer/src/router.tsx
import { createRouter, createHashHistory, createRootRoute, createRoute } from '@tanstack/react-router'

const hashHistory = createHashHistory()

const rootRoute = createRootRoute({
  component: () => <AppShell />,  // AppShell wraps <Outlet />
})

// Lazy-loaded feature routes
const accountsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: () => import('./features/accounts/AccountsHome'),
})

const tradesRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/trades',
  component: () => import('./features/trades/TradesLayout'),
})

const planningRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/planning',
  component: () => import('./features/planning/PlanningLayout'),
})

const schedulingRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/scheduling',
  component: () => import('./features/scheduling/SchedulingLayout'),
})

const settingsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/settings',
  component: () => import('./features/settings/SettingsLayout'),
})

const routeTree = rootRoute.addChildren([
  accountsRoute,
  tradesRoute,
  planningRoute,
  schedulingRoute,
  settingsRoute,
])

export const router = createRouter({
  routeTree,
  history: hashHistory,
  defaultPreload: 'intent',  // Preload on hover/focus
})
```

---

## 6. TanStack Query Client Config `[Research-backed: Claude ADR-3, synthesis §staleTime]`

```typescript
// src/renderer/src/lib/query-client.ts
import { QueryClient } from '@tanstack/react-query'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 0,              // Financial data is always stale
      gcTime: 5 * 60 * 1000,     // 5min — prevent cache bloat in 8-16hr sessions
      refetchOnWindowFocus: true, // Re-validate when trader returns
      retry: 2,                  // Retry failed reads twice
    },
    mutations: {
      retry: false,              // NEVER auto-retry financial transactions
    },
  },
})
```

```typescript
// src/renderer/src/lib/api.ts
const API_BASE = window.api.baseUrl  // From contextBridge
const TOKEN = window.api.token       // Ephemeral Bearer token

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${TOKEN}`,
      ...init?.headers,
    },
  })
  if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`)
  return res.json()
}
```

---

## 7. Zustand Store Pattern `[Research-backed: Claude ADR-5, synthesis §Zustand]`

```typescript
// src/renderer/src/stores/layout.ts
import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'

interface LayoutState {
  sidebarWidth: number
  isRailCollapsed: boolean
  commandPaletteOpen: boolean
  setSidebarWidth: (width: number) => void
  toggleRail: () => void
  toggleCommandPalette: () => void
}

export const useLayoutStore = create<LayoutState>()(
  persist(
    (set) => ({
      sidebarWidth: 240,
      isRailCollapsed: false,
      commandPaletteOpen: false,
      setSidebarWidth: (width) => set({ sidebarWidth: width }),
      toggleRail: () => set((s) => ({ isRailCollapsed: !s.isRailCollapsed })),
      toggleCommandPalette: () => set((s) => ({ commandPaletteOpen: !s.commandPaletteOpen })),
    }),
    {
      name: 'zorivest-layout',
      storage: createJSONStorage(() => window.electronStore),  // electron-store via contextBridge
    }
  )
)
```

---

## 8. shadcn/ui Mira Preset Initialization `[Research-backed: Claude ADR-4]`

```bash
# Initialize shadcn/ui with Mira preset (run from ui/)
npx shadcn@latest init --defaults --force

# Install core components for AppShell
npx shadcn@latest add button dialog dropdown-menu scroll-area tooltip tabs
```

**Configuration (`components.json`):**
```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "default",
  "rsc": false,
  "tsx": true,
  "tailwind": {
    "config": "",
    "css": "src/renderer/src/globals.css",
    "baseColor": "neutral",
    "cssVariables": true
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils",
    "ui": "@/components/ui"
  }
}
```

**Mira density overrides** (in `globals.css` after `@theme` block):
```css
/* Mira-inspired compact density */
:root {
  --radius: 0.375rem;          /* 6px — smaller than default 8px */
}

/* Global compact spacing for data-dense UI */
.btn { @apply px-3 py-1.5 text-sm; }
.input { @apply h-8 px-2 text-sm; }
.card { @apply p-3; }
```

---

## 9. React Compiler Babel Plugin `[Research-backed: Claude ADR-6, synthesis §React Compiler]`

**Setup:** Already in electron-vite config (Section 2 above).

**Rules for new code:**
- Automatic memoization eliminates need for `useMemo`, `useCallback`, `React.memo`
- Do NOT write manual memoization — let the compiler handle it
- Use `useWatch()` not `watch()` with React Hook Form (compiler compatibility)
- Escape hatch: `"use no memo"` directive at top of component file if compiler causes issues

```typescript
// ✅ Correct with React Compiler
import { useWatch } from 'react-hook-form'

function PriceField({ control }) {
  const price = useWatch({ control, name: 'price' })
  return <span>{price}</span>
}

// ❌ Incorrect — watch() breaks React Compiler
import { useForm } from 'react-hook-form'

function PriceField() {
  const { watch } = useForm()
  const price = watch('price')  // Re-renders everything
  return <span>{price}</span>
}
```

---

## Implementation Notes `[Local Canon: 06-gui.md, 06a-gui-shell.md scope boundaries]`

### Content MEU Guidance (Document Now, Implement Later) `[Local Canon: BUILD_PLAN.md MEU delineation]`

The following patterns are documented for awareness but NOT implemented in MEU-43/44/45:

| Pattern | Target MEU | Key Reference |
|---------|-----------|---------------|
| `<Activity>` component for tab persistence | MEU-46+ | Design root layout to accept it later |
| `useEffectEvent` for WebSocket handlers | MEU-65 | Market data subscriptions |
| V8 bytecode compilation | Distribution MEU | electron-vite supports this |
| Memory leak monitoring | Health/ops MEU | `process.memoryUsage()` on 60s intervals |
| Non-color P&L indicators | MEU-46 | See `style-guide-zorivest.md` §1 |

### Cognitive Load Protocol `[Research-backed: style-guide-zorivest.md §0]`

Apply the 5-point per-screen design protocol from `style-guide-zorivest.md` §0 to every new view:
1. **One-thing test:** What is this screen's single primary purpose?
2. **5-second test:** Can the user orient within 5 seconds?
3. **Progressive disclosure audit:** Is complexity hidden behind expandable sections?
4. **Data-ink audit:** Remove any element that doesn't convey data or enable action
5. **Color signal check:** Does color serve a functional purpose or just decoration?
