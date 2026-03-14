# GUI Shell Foundation — Feature Scope

> MEU-43 (Electron Lifecycle), MEU-44 (AppShell + Navigation), MEU-45 (Command Palette + Window State)
> Decision scope: Phase 6 GUI infrastructure — no content views

---

## What It Builds

The GUI shell is the Electron + React infrastructure that hosts all future trading views. It includes:

| Component | MEU | Responsibility |
|-----------|-----|---------------|
| Electron main process | MEU-43 | Window management, Python spawn, IPC bridge, security |
| React renderer bootstrap | MEU-43 | TanStack Router, Query client, Zustand stores, globals.css |
| AppShell layout | MEU-44 | Navigation rail, header bar, content area, status footer |
| Settings panel | MEU-44 | Theme, density, persistence via `usePersistedState` |
| Command palette | MEU-45 | Fuzzy search, keyboard-driven navigation, command registry |
| Window state persistence | MEU-45 | Bounds, panel sizes via electron-store |

## What Data It Consumes

- **REST API** from Python backend (FastAPI on `localhost:{dynamic_port}`)
  - 30+ endpoints across accounts, trades, planning, scheduling, market data
  - All requests authenticated with ephemeral Bearer token (nonce-based, per-launch)
- **No direct database access** — SQLCipher is Python-only
- **IPC bridge** exposes minimal API via `contextBridge.exposeInMainWorld()`

## Variations

| Variation | Dev Mode | Production Mode |
|-----------|----------|----------------|
| Build tool | `electron-vite dev` (HMR) | `electron-vite build` + `electron-builder` |
| Python | `uv run uvicorn` (system Python + uv) | PyInstaller `--onedir` binary in `extraResources` |
| Styling | Hot-reloading Tailwind CSS | Pre-compiled CSS bundle |
| Source maps | Enabled | Stripped (optional V8 bytecode) |
| Logging | `stdio: 'pipe'` (visible in terminal) | `stdio: 'ignore'` (prevents 64KB buffer overflow) |

## Happy Path

1. User launches Electron app
2. Splash window appears immediately (lightweight HTML, no React)
3. Main process spawns Python subprocess with ephemeral Bearer token + dynamic port
4. Health check polls `GET /health` with exponential backoff (100ms → 200ms → 400ms → ...)
5. Python responds healthy → splash transitions to main BrowserWindow
6. React renderer boots: TanStack Router, Query client, Zustand stores
7. AppShell renders: navigation rail, content outlet displays Accounts home
8. User navigates via rail clicks, keyboard shortcuts, or command palette

## Edge Cases

| Edge Case | Handling Strategy |
|-----------|------------------|
| Python fails to start | Splash shows error + retry button after 30s timeout |
| Python crashes mid-session | Health check detects, shows reconnection overlay |
| Port conflict | Dynamic port via `net.createServer(0)` — always unique |
| Cold start latency (5-10s) | Splash window masks delay; PyInstaller `--onedir` reduces to ~3s |
| Stdio buffer overflow | Production mode uses `stdio: 'ignore'` |
| Window state corruption | electron-store validates bounds against current display |
| Orphaned Python process | Python checks parent PID heartbeat; Electron kills process tree on exit |
| User closes during startup | `will-quit` handler sends `/shutdown` to Python before exit |
| Local malware queries API | Ephemeral Bearer token rejects unauthenticated requests |
| Auto-update during trading | Background download only; user-initiated restart |

## Out of Scope (Deferred to Content MEUs)

- Trade entry forms (MEU-47+)
- Data grids / position tables (MEU-46)
- Chart rendering (MEU-65)
- Market data WebSocket handling (MEU-65)
- `<Activity>` component for tab persistence (content MEUs)
- `useEffectEvent` for subscription handlers (MEU-65)
