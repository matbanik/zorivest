# GUI Shell Foundation — Architecture Patterns

> Consolidated from Gemini 3.1 Pro, GPT-5.4, and Claude Opus 4.6 research outputs.
> All patterns tagged per AGENTS.md source-basis requirement.

---

## 1. Build Pipeline Pattern `[Research-backed: Gemini §Build Pipeline, Claude ADR-1]`

**Tool:** electron-vite + electron-builder

**Directory structure enforced by electron-vite:**
```
ui/
├── src/
│   ├── main/           # Electron main process (Node.js)
│   │   ├── index.ts    # BrowserWindow, Python spawn, IPC
│   │   └── splash.html # Lightweight splash (no React)
│   ├── preload/        # contextBridge (isolated)
│   │   └── index.ts    # Expose minimal API to renderer
│   └── renderer/       # React application
│       ├── src/
│       │   ├── app.tsx
│       │   ├── router.tsx
│       │   ├── globals.css
│       │   └── features/   # Feature-based modules
│       └── index.html
├── electron.vite.config.ts
├── electron-builder.yml
└── package.json
```

**Key configuration:**
- electron-vite handles main/preload/renderer as separate Vite builds
- electron-builder uses `extraResources` for PyInstaller binary (outside ASAR)
- Production build: `electron-vite build && electron-builder`
- Dev mode: `electron-vite dev` (HMR for renderer, restart for main)

---

## 2. Security Pattern `[Research-backed: Gemini §Security Architecture, Claude ADR-7]`

**Zero-trust posture for Electron:**

| Setting | Value | Rationale |
|---------|-------|-----------|
| `nodeIntegration` | `false` | Prevent renderer from accessing Node.js |
| `contextIsolation` | `true` | Separate renderer and preload contexts |
| `sandbox` | `true` | OS-level sandboxing for renderer |
| `webSecurity` | `true` | Enforce same-origin policy |

**Ephemeral Bearer Token flow:**
1. Main process generates `crypto.randomBytes(32).toString('hex')` on launch
2. Token passed to Python via spawn args: `['--token', nonce]`
3. Token exposed to renderer via `contextBridge.exposeInMainWorld('api', { token })`
4. TanStack Query `queryFn` includes `Authorization: Bearer {token}` header
5. FastAPI middleware validates token on every request

**Content-Security-Policy:**
```
default-src 'self';
script-src 'self';
style-src 'self' 'unsafe-inline';
connect-src 'self' http://localhost:*;
img-src 'self' data:;
```

**Additional measures:**
- `will-navigate` event intercepted to block external navigation
- `new-window` creation blocked
- `safeStorage` API for credentials (never electron-store)
- electron-store restricted to UI preferences only

---

## 3. Python Lifecycle Pattern `[Research-backed: Gemini §Python Lifecycle, Claude ADR-7]`

**PythonManager class responsibilities:**

```
Startup:
  1. Allocate dynamic port via net.createServer(0)
  2. Spawn Python: child_process.spawn(pythonPath, [...args, '--port', port, '--token', nonce])
  3. Dev: stdio='pipe' | Production: stdio='ignore'
  4. Health check: poll GET /health with exponential backoff (100ms → 30s cap)
  5. On healthy: emit 'ready' event, transition splash → main window

Shutdown:
  1. Send POST /shutdown to FastAPI
  2. Wait 5s for graceful exit
  3. If still running: kill process tree (taskkill /T on Windows)

Error Recovery:
  - Health check failure: show reconnection overlay
  - Spawn failure: show error in splash + retry button
  - Orphan prevention: Python checks parent PID heartbeat
```

**Production paths:**
- Dev: `uv run uvicorn` (system Python + uv)
- Production: `path.join(process.resourcesPath, 'python', 'zorivest.exe')` (PyInstaller --onedir)

---

## 4. State Management Pattern `[Research-backed: Claude ADR-5, synthesis §Zustand]`

**Three-layer state architecture:**

```
┌─────────────────────────────────────────────────┐
│ Server State (TanStack Query → REST API)        │
│ Accounts, trades, plans, schedules, market data │
│ staleTime: 0, gcTime: 5min, retry: false (mut.) │
└─────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────┐
│ Persisted Settings (usePersistedState → REST)   │
│ Theme, active account, panel collapse states    │
│ Server-persisted via SQLCipher                  │
└─────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────┐
│ Local UI State (Zustand → electron-store)       │
│ Sidebar width, dialog open, sort column, etc.   │
│ Client-only, persist middleware for window       │
└─────────────────────────────────────────────────┘
```

**Zustand slice pattern:**
- One store per feature module (`useTradesStore`, `useLayoutStore`)
- `persist` middleware pipes to electron-store for window bounds
- `getState()` available outside React (IPC handlers, Electron main → renderer)

**TanStack Query config for trading:**
- `staleTime: 0` — financial data is always stale, always background-refetch
- `gcTime: 5 * 60 * 1000` — prevent cache bloat in 8-16hr sessions
- `mutations.retry: false` — never auto-retry financial transactions
- Show "last updated" timestamps on all data displays

---

## 5. Directory Structure Pattern `[Research-backed: Claude ADR-9]`

**Feature-based organization:**
```
ui/src/renderer/src/
├── app.tsx                    # Root component
├── router.tsx                 # TanStack Router config
├── globals.css                # Tailwind @theme tokens
├── components/                # Shared UI components
│   ├── ui/                    # shadcn/ui components
│   └── layout/                # AppShell, NavRail, Header
├── features/                  # Feature modules
│   ├── accounts/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── stores/            # Zustand slice
│   │   └── __tests__/
│   ├── trades/
│   ├── planning/
│   ├── scheduling/
│   └── settings/
├── hooks/                     # Shared hooks
│   └── usePersistedState.ts
├── lib/                       # Utilities
│   ├── api.ts                 # fetch wrapper with Bearer token
│   └── query-client.ts        # TanStack Query config
└── stores/                    # Global Zustand stores
    └── layout.ts              # Sidebar, theme, app-level state
```

---

## 6. Router Pattern `[Research-backed: Claude ADR-2; Human-approved: user confirmed]`

**TanStack Router with hash history:**
- `createHashHistory()` required for Electron (no file:// server)
- File-based route definitions with `lazy()` code splitting
- Type-safe route params and search params with Zod validation
- `routeContext` for dependency injection (Query client, auth token)

**Canonical route map** `[Local Canon: 06-gui.md nav rail table, lines 190-196]`:

| Route | Module | Nav Rail Label |
|-------|--------|---------------|
| `/` | Accounts Home | Accounts |
| `/trades/*` | Trade views | Trades |
| `/planning/*` | Trade planning | Planning |
| `/scheduling/*` | Scheduled jobs | Scheduling |
| `/settings/*` | App settings | Settings |

Sub-routes (reports, watchlists, tax) are nested within their parent modules.

---

## 7. Form Pattern `[Research-backed: Claude §RHF, GPT-5.4 §Forms]`

**React Hook Form + Zod for client-side validation:**
- Uncontrolled components via refs = no re-render on keystroke
- `zodResolver` for schema-driven validation
- `useFieldArray` for multi-leg trades and dynamic fields
- REST JSON is the contract — no shared TypeScript package between `ui/` and `mcp-server/`
- Use `useWatch()` not `watch()` (React Compiler compatibility)

---

## 8. Component Pattern `[Research-backed: Claude ADR-4]`

**shadcn/ui + Radix UI with Mira preset:**
- Code-ownership model: copy-paste into `components/ui/`, not npm dependency
- Mira preset for compact, dense interfaces (Bloomberg-grade density)
- Built on Radix primitives: WAI-ARIA, keyboard navigation, focus management
- Native TanStack Table integration via shadcn/ui Data Table component
- Dark-first theme with Dracula-based tokens from `style-guide-zorivest.md`
