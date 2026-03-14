# Zorivest architecture decision synthesis

**The optimal stack for Zorivest in 2026 is: electron-vite + electron-builder, React 19.2, shadcn/ui with Tailwind v4, Zustand, TanStack Router, and React Hook Form with Zod.** This combination maximizes type safety, performance for data-dense trading UIs, and ecosystem cohesion across 22+ modules. Every recommendation below favors production stability and long-running desktop reliability over bleeding-edge novelty — a deliberate bias for a financial application. The decisions are tightly interdependent: shadcn/ui requires Tailwind, TanStack Router integrates natively with TanStack Query, and Zod schemas flow from form validation through API contracts to the existing MCP server.

---

## ADR 1: electron-vite plus electron-builder is the safest build pipeline

**Decision: Use electron-vite v5 for development, electron-builder v26 for packaging.**

The Electron build tool landscape in 2026 has three viable paths, and the hybrid approach wins decisively. **electron-vite** (by alex8088, ~241K weekly npm downloads, 5.2K GitHub stars) reached v5.0.0 in December 2025 with a unified single-file config (`electron.vite.config.ts`) covering main, preload, and renderer processes. Its HMR is excellent — instant for renderer, hot-reload for main and preload. The v5 release introduced isolated builds with intelligent shared chunk handling, improving sandbox support. A unique feature is **V8 bytecode compilation** for source code protection, valuable for proprietary trading logic.

**electron-builder** (v26.8.1, ~1.2M weekly downloads, 14.5K stars, 601 contributors) handles everything electron-vite does not: packaging to every format (NSIS, DMG, AppImage, DEB, RPM, Snap, Flatpak), code signing for macOS and Windows, and auto-update via `electron-updater` with differential downloads and staged rollouts. This is the most battle-tested packaging tool in the ecosystem.

The alternative — **Electron Forge with Vite plugin** (v7.11.1) — carries two disqualifying problems for a financial app. First, the Vite plugin is **explicitly marked experimental** with no API stability guarantees. Second, issue #4045 (November 2025) introduced a dependency pruning regression causing **1.1GB package bloat** in v7.5.0+. While Forge is officially maintained by the Electron team and Forge v8 (alpha) aims to graduate the Vite plugin to stable, the timeline is uncertain. For a trading application handling real money, experimental tooling is an unacceptable risk.

| Criterion | electron-vite v5 | Forge + Vite v7.11 | electron-builder + manual Vite |
|---|---|---|---|
| Vite stability | ✅ Stable | ⚠️ Experimental | N/A (manual) |
| Config complexity | 1 file | 4+ files | Moderate |
| Packaging | Via electron-builder | Built-in | Built-in |
| Auto-update | Via electron-updater | Built-in | Built-in |
| npm downloads | ~241K | ~84K | ~1.2M |
| Known critical bugs | Minor (Tailwind v4 edge cases) | Package bloat regression | None major |
| Bus factor | ⚠️ Solo developer | Electron team | Large community |

The solo-maintainer risk for electron-vite is mitigated by two factors: the real packaging complexity lives in electron-builder (which has massive community support), and electron-vite's codebase is small enough that if abandoned, migration to manual Vite config would be straightforward.

---

## ADR 2: React 19.2 brings three killer features for trading desktops

**Decision: Use React 19.2.x with React Compiler enabled.**

React 19 has been stable for **15 months** with three minor releases and multiple patches. Per the State of React 2025 survey (3,760 respondents), **48.4% of daily React users** already run React 19. The React Foundation launched under the Linux Foundation in October 2025 with founding members Amazon, Meta, Microsoft, and Vercel. React 18's last release was v18.3.1 in April 2024 — it is effectively in maintenance-only mode with docs archived at `legacy.reactjs.org`.

Three React 19 features are specifically transformative for Zorivest:

**React Compiler 1.0** (stable since October 2025) automatically memoizes components at build time, eliminating manual `useMemo`, `useCallback`, and `React.memo`. Meta's Quest Store measured **12% faster initial load and 2.5× faster interactions** with neutral memory impact. For a trading dashboard with complex data grids and frequent re-renders from real-time data, automatic memoization is the single highest-impact performance feature available. It works as a Babel or SWC plugin. One caveat: React Hook Form's `watch()` and some TanStack Table patterns have edge cases with the Compiler — both have documented workarounds (use `useWatch()` instead; disable Compiler per-component where needed).

The **Activity component** (`<Activity mode="visible"|"hidden">`, introduced in React 19.2) pre-renders hidden content while preserving state of unmounted views. This is purpose-built for Zorivest's multi-tab trading interface: keep portfolio, watchlist, order book, and chart views as separate Activities. Tab switching becomes instant. Form state persists when navigating away and back. No equivalent exists in React 18.

**useEffectEvent** (React 19.2) separates event logic from effect dependency tracking, directly solving the common problem of WebSocket handlers and real-time price update callbacks that reference latest props/state without re-subscribing.

All committed libraries are compatible: TanStack Query v5 works with React 19 (confirmed in docs), TanStack Table v8 supports React 16.8–19, shadcn/ui has full React 19 + Tailwind v4 support since February 2025, Radix UI peer dependencies include React 19, and Zustand v5 uses `useSyncExternalStore`. The only adjustment: use `useWatch()` instead of `watch()` in React Hook Form — trivial for new code.

---

## ADR 3: shadcn/ui with the Mira preset delivers Bloomberg-grade density

**Decision: shadcn/ui + Radix primitives as the component system, with AG Grid as an optional escape hatch for extreme data grid needs.**

For a data-dense trading application, the component library choice revolves around one question: can you make it look like a professional terminal, not a SaaS marketing page? shadcn/ui answers this definitively with its **Mira preset** — purpose-built for compact, dense interfaces with reduced padding and tight spacing. Because shadcn/ui uses a copy-paste model (components are copied into your codebase, not installed as dependencies), you own every pixel. There is no fighting library internals.

The shadcn/ui CLI v4 (March 2026) added a presets system, scaffolding templates for Vite, and AI agent integration via MCP servers. The ecosystem has exploded: over 1,000 component patterns from third-party registries, including **Metafi** (financial dashboard template). Under the hood, **Radix UI primitives** provide WAI-ARIA-compliant keyboard navigation, focus management, and screen reader support — used by Vercel, Linear, Supabase, and the Node.js official site.

For data tables, shadcn/ui wraps **TanStack Table** (already committed) with styled components providing sorting, filtering, pagination, and column visibility. TanStack Table at ~15KB gzipped handles most Zorivest tables (portfolio views, trade history, watchlists). For edge cases requiring 100K+ rows with pivoting and Excel export, **AG Grid** can complement TanStack Table — they have an official open-source partnership and are designed to be complementary.

**Why not Ant Design 5/6:** Despite strong table components and a Finexus finance template, Ant Design's opinionated visual identity fights a custom trading aesthetic. The bundle is heavier (~200-400KB unpacked), and overriding its design system to achieve a dark terminal look requires extensive effort. Ant Design v6 dropped React 17 support and shifted to CSS Variables, but the core aesthetic constraint remains.

**Why not MUI:** Material Design is deeply embedded in MUI's DNA. The MUI X Data Grid Pro/Premium ($180-588/dev/year) is powerful but carries per-developer licensing — all frontend developers need licenses, not just those working on the grid. The `sx` prop override dance for custom aesthetics is painful at scale.

**Why not Mantine:** The strongest all-around alternative. Mantine v8 has 120+ components, CSS Modules (no runtime overhead), and excellent dark mode. However, it lacks a premium data grid, has a smaller community than shadcn/ui, and is less established for financial-specific interfaces. Solid second choice if the team prefers an installed component library over copy-paste.

---

## ADR 4: Tailwind v4 is non-negotiable given shadcn/ui

**Decision: Tailwind CSS v4 with the `@tailwindcss/vite` plugin.**

This decision follows directly from ADR 3. shadcn/ui is built on Tailwind, so Tailwind is a hard dependency. Fortunately, Tailwind v4 (stable January 2025, currently v4.2) is the best CSS framework available for this stack.

The **Oxide engine** — a complete Rust rewrite — delivers full builds 5× faster and incremental builds **100× faster** (microseconds). The first-party `@tailwindcss/vite` plugin integrates tightly with the electron-vite build pipeline. Configuration moved to **CSS-first** via `@theme` directives, eliminating `tailwind.config.js` entirely. Built-in `@import` handling, vendor prefixing, and CSS nesting remove the need for `postcss-import` and `autoprefixer`.

For Zorivest's trading aesthetic: define the dark palette, compact spacing, and mono fonts in a single `@theme` block. Use `oklch` color space for vivid P&L colors (green/red) on P3 displays. Dark mode via the `dark:` variant toggles programmatically through Electron. `color-mix()` enables opacity adjustments without RGBA. All utility classes resolve at build time — **zero runtime overhead**.

CSS Modules, Vanilla Extract, Panda CSS, and StyleX were all evaluated and rejected primarily because they are **incompatible with shadcn/ui** without abandoning its ecosystem. StyleX (Meta) is designed for Meta-scale problems and is overly restrictive for a 22-module app. Panda CSS (~130K weekly downloads) has good technology but a tiny ecosystem. Vanilla Extract's separate `.css.ts` files add context switching without proportional benefit.

---

## ADR 5: Zustand slices map cleanly to 22 trading modules

**Decision: Zustand v5 for all cross-cutting UI state. Component-local `useState` for truly local state.**

With TanStack Query v5 handling all server state (30+ REST endpoints), the remaining state management need is cross-cutting UI state: panel visibility, sidebar collapse, active tab, modal state, layout preferences, table column visibility, theme, and drag state across 22+ modules.

**Zustand v5** (~20-24M weekly npm downloads, 57K GitHub stars, 1.2KB gzipped core) is the clear winner. Its **slice pattern** maps naturally to module boundaries: each of the 22+ modules gets its own typed slice with actions and selectors, composed into domain stores (UI layout store, panel preferences store, filter state store). The `persist` middleware integrates with `electron-store` via a custom `StateStorage` adapter — layout preferences, column widths, and theme survive app restarts.

Key architectural advantages for Electron: stores are module-level (no Provider needed), `getState()` and `setState()` work outside React components (useful for Electron main↔renderer communication), and selector-based subscriptions mean only components reading changed state re-render. With 22+ modules sharing UI state, this granularity prevents the cascading re-render problem that kills React Context at scale.

**Jotai** (atomic model, ~2.3M downloads) excels when state atoms are deeply interdependent, like collaborative editors. For Zorivest's UI state — mostly independent panel toggles and preferences — the overhead of defining individual atoms per state piece adds boilerplate without proportional benefit. **Valtio** (proxy-based, ~1.2M downloads) introduces debugging complexity from proxies and a mental model split between `snap` (read in render) and `state` (mutate). Neither has the ecosystem breadth or middleware story that Zustand offers.

---

## ADR 6: TanStack Router's type-safe search params are built for trading filters

**Decision: TanStack Router v1 with `createHashHistory()` for Electron.**

Electron apps don't have a URL bar, which makes routing choice less about URL management and more about code organization, code splitting, and state management. **TanStack Router** (v1.166.x, ~2.1M weekly downloads, 12KB gzipped) wins on all three.

**100% type-safe routing** means route params, search params, loader data, and navigation are all compile-time checked. Autocomplete works for route paths in `<Link>` and `navigate()`. This catches navigation errors at build time across 22+ modules — invaluable for refactoring confidence.

**First-class search params** are the killer feature for a trading app. Filter states, sort orders, and view configurations are managed via schema-based, validated, type-safe search params with structural sharing. When a trader configures a positions table to show only tech stocks sorted by P&L descending, that filter state lives in search params — shareable, bookmarkable (in hash history), and type-checked.

**Built-in code splitting** via `lazy()` route components is critical for 22+ modules. Each module loads only when navigated to. TanStack Router also integrates natively with TanStack Query — route loaders can prefetch data, and `routeContext` passes the `queryClient`, creating a seamless fetch-on-navigate pipeline.

For Electron, use `createHashHistory()` — confirmed working in community discussions. Hash routing preserves forward/back navigation and survives page reloads, unlike memory routing.

**React Router v7** (v7.9.0, ~16M downloads) is the safe conventional choice, but in library mode (the only mode relevant for Electron), it offers **minimal type safety** — no typed params, no search param schemas, no autocompleted paths. Code splitting requires manual `React.lazy()`. These gaps are significant for a 22-module app.

---

## ADR 7: React Hook Form plus Zod creates a shared validation layer

**Decision: React Hook Form v7 with `@hookform/resolvers` and Zod schemas.**

React Hook Form (~25M weekly npm downloads, 44.5K stars, 10.7KB gzipped, zero dependencies) uses an **uncontrolled component approach** — inputs register via refs, avoiding re-renders on every keystroke. Only validation state changes trigger re-renders. For trade entry forms where responsiveness directly affects UX, this is the performance-critical differentiator.

The Zod integration via `zodResolver` creates a powerful architecture: define Zod schemas once in a shared `/schemas` directory, use them for frontend form validation, for API request/response typing, and in the existing TypeScript MCP server. This eliminates validation drift between frontend and backend.

```typescript
const tradeSchema = z.object({
  symbol: z.string().min(1).max(10),
  side: z.enum(['buy', 'sell']),
  quantity: z.number().positive().int(),
  orderType: z.enum(['market', 'limit', 'stop']),
  limitPrice: z.number().positive().optional(),
});
// Used in form: resolver: zodResolver(tradeSchema)
// Used in API: type TradeRequest = z.infer<typeof tradeSchema>
```

`useFieldArray` handles dynamic fields (multi-leg trades, alert conditions). `useFormContext` with `FormProvider` supports multi-section settings forms. DevTools (`@hookform/devtools`) provide visual inspection during development.

**TanStack Form** (v1.28.5, ~1M downloads) has superior type safety — field names are compile-time checked against the form shape. However, it has been stable for only one year, uses controlled components (more re-renders by design), recommends `--save-exact` for versions (signaling the API is still settling), and its own lead maintainer stated: "if you're already happy with RHF I wouldn't inherently suggest migrating away." For a production trading platform, ecosystem maturity wins over DX advantages. Revisit TanStack Form for v2 of the app.

**Formik** is effectively abandoned (last meaningful release ~2022, 600+ open issues). **Conform** is designed for server-side form handling in Remix/Next.js and is irrelevant for Electron. React 19's native form features (`useActionState`, `useFormStatus`) are designed for server actions and receive `FormData` (not typed objects) — they complement but do not replace a form library.

---

## ADR 8: Dependency lock manifest

Based on all research findings, the following `package.json` dependencies are recommended with locked major.minor versions:

```jsonc
{
  "dependencies": {
    // ── Core ──────────────────────────────────────
    "react": "~19.2.0",
    "react-dom": "~19.2.0",

    // ── Data ─────────────────────────────────────
    "@tanstack/react-query": "~5.90.0",
    "@tanstack/react-table": "~8.21.0",
    "@tanstack/react-router": "~1.166.0",
    "zod": "~3.24.0",

    // ── UI ───────────────────────────────────────
    // shadcn/ui components are copy-pasted, not installed
    "@radix-ui/react-dialog": "~1.1.0",
    "@radix-ui/react-dropdown-menu": "~2.1.0",
    "@radix-ui/react-popover": "~1.1.0",
    "@radix-ui/react-tabs": "~1.1.0",
    "@radix-ui/react-tooltip": "~1.1.0",
    "@radix-ui/react-scroll-area": "~1.2.0",
    "@radix-ui/react-select": "~2.1.0",
    "@radix-ui/react-slot": "~1.1.0",
    "lightweight-charts": "~4.2.0",
    "lucide-react": "~0.475.0",
    "class-variance-authority": "~0.7.0",
    "clsx": "~2.1.0",
    "tailwind-merge": "~2.6.0",

    // ── State ────────────────────────────────────
    "zustand": "~5.0.0",

    // ── Forms ────────────────────────────────────
    "react-hook-form": "~7.54.0",
    "@hookform/resolvers": "~5.0.0",

    // ── Utility ──────────────────────────────────
    "fuse.js": "~7.0.0",
    "sonner": "~1.7.0",
    "electron-store": "~10.0.0",

    // ── Electron renderer helpers ────────────────
    "@tanstack/react-query-devtools": "~5.90.0"
  },
  "devDependencies": {
    // ── Build ────────────────────────────────────
    "electron": "~34.0.0",
    "electron-vite": "~5.0.0",
    "electron-builder": "~26.8.0",
    "electron-updater": "~6.6.0",
    "typescript": "~5.7.0",
    "tailwindcss": "~4.2.0",
    "@tailwindcss/vite": "~4.2.0",

    // ── React Compiler ───────────────────────────
    "babel-plugin-react-compiler": "~1.0.0",

    // ── Testing ──────────────────────────────────
    "vitest": "~3.0.0",
    "@testing-library/react": "~16.1.0",
    "@testing-library/jest-dom": "~6.6.0",
    "@testing-library/user-event": "~14.5.0",
    "playwright": "~1.50.0",

    // ── Linting / Formatting ─────────────────────
    "eslint": "~9.18.0",
    "prettier": "~3.4.0",
    "@types/react": "~19.0.0",
    "@types/react-dom": "~19.0.0"
  }
}
```

Key notes on version choices: React **19.2.x** is required for Activity and useEffectEvent. TanStack Router **1.x** is stable since mid-2024 with frequent releases. Zustand **5.x** dropped legacy APIs and uses `useSyncExternalStore` for React 19 compatibility. Electron **34.x** should be the latest stable at the time of project initialization — always check electronjs.org for the current stable line. Radix UI packages listed are the most commonly used primitives; add more as shadcn/ui components require them.

---

## ADR 9: Project directory structure for scale

The structure below uses **feature-based organization** for the renderer (each module is self-contained), separates Electron main process concerns, and supports shared types with the external MCP server.

```
zorivest/
├── electron.vite.config.ts           # Unified electron-vite config
├── electron-builder.yml              # Packaging/signing/update config
├── package.json
├── tsconfig.json                     # Base TS config
├── tsconfig.main.json                # Extends base for main process
├── tsconfig.renderer.json            # Extends base for renderer
│
├── src/
│   ├── main/                         # ── Electron Main Process ──
│   │   ├── index.ts                  # App entry: lifecycle, window creation
│   │   ├── python.ts                 # Subprocess spawn, health check, shutdown
│   │   ├── security.ts               # Nonce generation, safeStorage helpers
│   │   ├── updater.ts                # Auto-update logic (electron-updater)
│   │   ├── ipc-handlers.ts           # IPC for window mgmt only
│   │   ├── menu.ts                   # App menu / tray
│   │   └── splash.html               # Lightweight splash (no React)
│   │
│   ├── preload/                      # ── Preload Scripts ──
│   │   ├── index.ts                  # contextBridge.exposeInMainWorld
│   │   └── types.ts                  # Window API type declarations
│   │
│   ├── renderer/                     # ── React Application ──
│   │   ├── index.html                # Vite entry HTML
│   │   ├── main.tsx                  # React root, QueryClient, Router
│   │   ├── App.tsx                   # Root layout, providers
│   │   │
│   │   ├── routes/                   # TanStack Router route definitions
│   │   │   ├── __root.tsx            # Root route with layout shell
│   │   │   ├── portfolio/
│   │   │   │   ├── route.tsx         # /portfolio route config + loader
│   │   │   │   └── index.lazy.tsx    # Lazy-loaded portfolio view
│   │   │   ├── watchlist/
│   │   │   │   ├── route.tsx
│   │   │   │   └── index.lazy.tsx
│   │   │   ├── orders/
│   │   │   │   ├── route.tsx
│   │   │   │   └── index.lazy.tsx
│   │   │   ├── analytics/
│   │   │   │   ├── route.tsx
│   │   │   │   └── index.lazy.tsx
│   │   │   └── settings/
│   │   │       ├── route.tsx
│   │   │       └── index.lazy.tsx
│   │   │
│   │   ├── features/                 # Feature modules (co-located)
│   │   │   ├── portfolio/
│   │   │   │   ├── components/       # PortfolioTable, PositionCard, etc.
│   │   │   │   ├── hooks/            # usePortfolioData, usePositionActions
│   │   │   │   ├── portfolio.store.ts # Zustand slice for portfolio UI state
│   │   │   │   └── portfolio.test.tsx
│   │   │   ├── orders/
│   │   │   │   ├── components/       # OrderForm, OrderBook, OrderHistory
│   │   │   │   ├── hooks/
│   │   │   │   ├── orders.store.ts
│   │   │   │   └── orders.test.tsx
│   │   │   ├── charts/
│   │   │   │   ├── components/       # PriceChart, VolumeChart
│   │   │   │   ├── hooks/            # useChartData, useChartConfig
│   │   │   │   └── charts.store.ts
│   │   │   └── ... (22+ modules)
│   │   │
│   │   ├── components/               # Shared UI components
│   │   │   └── ui/                   # shadcn/ui generated components
│   │   │       ├── button.tsx
│   │   │       ├── dialog.tsx
│   │   │       ├── data-table.tsx
│   │   │       ├── input.tsx
│   │   │       └── ...
│   │   │
│   │   ├── hooks/                    # Shared hooks
│   │   │   ├── use-health-check.ts
│   │   │   └── use-keyboard-shortcut.ts
│   │   │
│   │   ├── lib/                      # Utilities & configuration
│   │   │   ├── api-client.ts         # Fetch wrapper with auth nonce
│   │   │   ├── query-client.ts       # TanStack Query config
│   │   │   ├── query-keys.ts         # Query key factory
│   │   │   └── utils.ts              # cn(), formatCurrency(), etc.
│   │   │
│   │   ├── stores/                   # Global Zustand stores
│   │   │   ├── ui.store.ts           # Theme, sidebar, global layout
│   │   │   └── index.ts
│   │   │
│   │   └── styles/
│   │       └── globals.css           # @theme, Tailwind imports, base styles
│   │
│   └── shared/                       # ── Shared Types ──
│       ├── api-types.ts              # REST API request/response types
│       ├── schemas/                  # Zod schemas (shared w/ MCP server)
│       │   ├── trade.schema.ts
│       │   ├── portfolio.schema.ts
│       │   └── settings.schema.ts
│       └── constants.ts              # Shared enums, config constants
│
├── tests/                            # Integration / E2E tests
│   ├── e2e/                          # Playwright E2E tests
│   │   ├── startup.spec.ts
│   │   └── trade-flow.spec.ts
│   └── setup.ts                      # Vitest global setup
│
└── resources/                        # Build resources
    ├── icon.icns                     # macOS icon
    ├── icon.ico                      # Windows icon
    └── icon.png                      # Linux icon
```

Key structural decisions: **Feature-based organization** (`features/portfolio/`, `features/orders/`) keeps components, hooks, stores, and tests co-located per module — critical for 22+ modules. Route definitions live in `routes/` using TanStack Router's file conventions with `lazy()` for code splitting. **Shared types** in `src/shared/` are importable by both Electron main and renderer processes, and Zod schemas in `src/shared/schemas/` can be published as a package or symlinked to the external MCP server project. Test files are co-located with features (unit tests) while integration and E2E tests live in `tests/`.

For **monorepo considerations**: if the MCP server and Zorivest share significant schema code, consider a pnpm workspace with `packages/shared-schemas` as a shared package. Turborepo or nx can orchestrate builds. However, start with the simpler flat structure above and extract to a monorepo only when the pain of copying schemas becomes real.

---

## ADR 10: Five risks that could sink a trading desktop app

### Python subprocess zombies are the number-one operational risk

When Electron crashes without cleanup, the Python process continues running as an orphan, holding port 8765 and database locks. On Windows, `child.kill('SIGTERM')` does not work reliably — and PyInstaller-bundled executables create an additional child process, so killing the parent PID alone leaves the real process running. The solution is a **multi-layered shutdown**: register handlers on `app.on('will-quit')`, `app.on('before-quit')`, `process.on('SIGTERM')`, and `process.on('uncaughtException')`. On Windows, use `taskkill /F /T /PID` (or the `tree-kill` npm package) to kill the entire process tree. On macOS/Linux, spawn with `{detached: true}` and use `process.kill(-child.pid)` for process group termination. Additionally, always consume stdout/stderr — if Python writes without readers, the 64KB buffer fills and the process blocks.

### Memory leaks compound over 8-16 hour trading sessions

A trading app runs continuously for an entire market day. Leaks invisible in web apps become critical. The primary sources are: unreleased IPC listeners accumulating across component mounts (check with `ipcRenderer.listenerCount()`), TanStack Query cache growth for actively watched queries (which never garbage-collect), and chart instances created without cleanup in `useEffect`. Monitor with `process.memoryUsage()` on 60-second intervals, logging RSS and heapUsed. Alert if growth trend exceeds a threshold. Use **`gcTime: 5 * 60 * 1000`** for inactive queries and ensure every chart/timer/listener has a cleanup function.

### Localhost REST API is accessible to any local process

Any application running under the same user account can reach `http://localhost:8765`. For a financial app, this is unacceptable. Mitigation: on startup, Electron generates a **random nonce** (`crypto.randomBytes(32).toString('hex')`), passes it to Python via command-line argument, and includes it as `X-Auth-Token` on every REST request. FastAPI middleware validates every request. Bind to `127.0.0.1` explicitly (never `0.0.0.0`). Consider using a dynamic port (port 0, OS-assigned) to reduce predictability, with Python reporting the actual port back via stdout. Set `Content-Security-Policy` in BrowserWindow to restrict `connect-src` to the specific localhost port.

### Auto-update must never interrupt an active trading session

macOS requires signed apps for auto-update (Squirrel.Mac requirement). Windows unsigned apps are flagged by SmartScreen. Use `electron-updater` with background downloads and **prompt the user to restart at their convenience** — never force-restart during market hours. Ensure Python is fully shut down before update applies. Back up the SQLCipher database pre-update. `electron-updater` does not natively support rollback, so keep previous version artifacts and implement a manual downgrade mechanism.

### Cold startup takes 5-10 seconds without optimization

Electron main process launch (1-2s) + Python subprocess + FastAPI startup (2-5s) + React renderer load (1-2s) + initial data fetch (0.5-1s) = **5-10 seconds cold start**. Critical optimizations: use PyInstaller `--onedir` mode (not `--onefile`, which adds 2-10s for temp extraction), show a lightweight splash BrowserWindow immediately while Python starts, lazy-load heavy React modules via code splitting, and defer non-critical module loading. The splash → main window transition should be triggered by the Python health check passing.

---

## ADR 11: Ten anti-patterns that are especially dangerous in trading

**Stale data display** is the most dangerous anti-pattern in a trading context. Setting `staleTime: 1 hour` for a balance query means a trader could make decisions based on data that's minutes old. Set `staleTime: 0` for all financial data (always stale, always background-refetch). Use `refetchInterval` by data sensitivity: pending orders at 3s, active positions at 10s, portfolio summary at 30s. Always show "last updated" timestamps. After every mutation, call `queryClient.invalidateQueries()` on all affected query keys.

**Order entry race conditions** are the second most harmful. Double-submitted buy orders execute twice. The fix is three-layered: disable the submit button while `mutation.isPending`, implement **idempotency keys** (generate a unique ID per order attempt, backend deduplicates), and **never use optimistic cache updates for financial transactions**. Wait for server confirmation. Use optimistic updates only for non-critical UI (watchlist toggles, preference changes).

**Blocking the main process** freezes the entire app — the trader cannot interact with order forms, close positions, or see updated prices. Even 100ms of blocking is noticeable. All heavy work belongs in the Python backend, Web Workers for frontend computation, or async operations. Never use synchronous file I/O, synchronous HTTP, or heavy computation in Electron's main process.

**Insecure credential storage** is a silent risk. `electron-store` files are plaintext JSON in the user's app data directory. Its built-in `encryptionKey` option provides only obfuscation. Use **Electron's `safeStorage` API** instead — it leverages OS-native keystores (macOS Keychain, Windows DPAPI, Linux libsecret). Encrypt with `safeStorage.encryptString()`, store the encrypted buffer in electron-store, and decrypt at runtime.

**Ignoring Electron security defaults** (`nodeIntegration: true`, disabled `contextIsolation`) turns any XSS vulnerability into full Remote Code Execution. Real CVEs exist: CVE-2020-15174 (Discord), CVE-2021-43908 (VS Code). Always set `nodeIntegration: false`, `contextIsolation: true`, `sandbox: true`, and use `contextBridge.exposeInMainWorld()` for minimal API exposure. Block navigation and new window creation. Set a strict Content Security Policy.

Additional anti-patterns to guard against: routing all data through IPC instead of direct REST (adds latency and main-process bottleneck), loading all 22+ modules upfront without code splitting (renderer bloat), unclean `useEffect` lifecycle (zombie timers accumulating over 8-hour sessions), running portfolio calculations in the render path (use `useMemo` or push to Python), and storing computation in the renderer when Python has numpy/pandas available.

---

## ADR 12: Integration wiring that makes the architecture real

### TanStack Query configuration for localhost REST

The QueryClient configuration must account for Zorivest's unique architecture: a subprocess-managed backend that might restart, financial data that must never be stale, and mutations that must never auto-retry.

```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 0,                    // Financial data: always refetch
      gcTime: 5 * 60 * 1000,          // 5 min GC to prevent memory bloat
      retry: (failureCount, error) => {
        if (error?.status === 401) return false;
        if (error?.message === 'Failed to fetch') return failureCount < 5;
        return failureCount < 3;
      },
      retryDelay: (attempt) => Math.min(1000 * 2 ** attempt, 30000),
      refetchOnWindowFocus: false,     // Desktop: irrelevant
    },
    mutations: { retry: false },       // NEVER auto-retry financial mutations
  },
});
```

Organize query keys with a **factory pattern** to manage 30+ endpoints: `queryKeys.portfolio.positions()`, `queryKeys.orders.list(filters)`, `queryKeys.market.quotes(symbols)`. This enables surgical invalidation — after placing an order, invalidate `queryKeys.orders.all` and `queryKeys.portfolio.all` without touching market data queries.

### Startup sequence orchestration

The startup flow must handle the async dependency chain gracefully: Electron → Python → health check → React → data ready. Show a lightweight splash window (plain HTML/CSS, no React) immediately on `app.on('ready')`. Generate the auth nonce, spawn Python with the nonce and port as arguments, and poll the `/health` endpoint with exponential backoff (200ms, 400ms, 800ms, capped at 2s, max 30 retries). On success, create the main BrowserWindow with `show: false`, load the React app, then on `ready-to-show` close the splash and show the main window. On failure after max retries, show an error dialog and quit. After startup, maintain a health monitor polling every 10 seconds — on 3 consecutive failures, attempt automatic Python restart.

### Settings persistence split between two stores

**electron-store** owns fast, client-only state: window position/size, UI theme, sidebar collapse, column widths/visibility, last active tab, zoom level. These load synchronously and take effect instantly. **REST API / SQLCipher** owns all financial and backend-dependent data: portfolio configuration, API credentials (encrypted via safeStorage before storage), trading preferences, watchlist contents, alert rules, transaction history. These load asynchronously through TanStack Query on startup. The two stores are intentionally decoupled — electron-store never mirrors backend data. If a setting affects both (e.g., default currency changes display and backend calculations), the mutation writes to REST, TanStack Query cache updates, and React re-renders from the cache.

---

## Conclusion: architectural cohesion drives the recommendations

The recommendations form an interlocking system, not a collection of independent choices. shadcn/ui requires Tailwind v4. TanStack Router integrates natively with TanStack Query v5, enabling fetch-on-navigate with typed loaders. Zod schemas flow from React Hook Form validation through API types to the MCP server. Zustand's persist middleware feeds into electron-store for layout persistence. React 19.2's Activity component solves the multi-tab state preservation problem that would otherwise require significant Zustand complexity.

The single most impactful recommendation is **React Compiler** — automatic memoization at build time eliminates an entire class of performance bugs that plague data-dense trading UIs with frequent re-renders. Combined with TanStack Table's headless architecture, Lightweight Charts' Canvas rendering, and route-level code splitting across 22+ modules, Zorivest should achieve the responsiveness expected of a professional trading application.

Three decisions to revisit in 12 months: TanStack Form v2 may reach the ecosystem maturity needed to replace React Hook Form. Electron Forge v8 may stabilize its Vite plugin enough to replace the electron-vite + electron-builder hybrid. And if Zorivest needs 100K+ row grids with pivoting, AG Grid Enterprise should be evaluated against TanStack Table's expanding feature set.