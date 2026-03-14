# GUI Shell Foundation — Technology Decisions

> Source: Cross-model synthesis of Gemini 3.1 Pro, GPT-5.4, and Claude Opus 4.6
> Date: 2026-03-14 | Decision scope: MEU-43, MEU-44, MEU-45

---

## Decision Summary

| # | Decision | Status | Source |
|---|----------|:------:|--------|
| D1 | Build: electron-vite + electron-builder | ✅ Unanimous | All three models |
| D2 | Router: TanStack Router v1 | ✅ Resolved | Claude recommended, user confirmed |
| D3 | State: Zustand v5 for local UI state | ✅ Resolved | Claude recommended, user confirmed |
| D4 | Monorepo: Standalone `package.json` | ✅ Resolved | REST API is the contract |
| D5 | React Compiler: Enable day 1 | ✅ Resolved | Claude recommended, synthesis adopted |
| D6 | `<Activity>` component: Defer to content MEUs | ✅ Resolved | Design for it, don't implement yet |
| D7 | Security: Ephemeral Bearer token | ✅ Unanimous | Gemini + Claude |

---

## D1: Build Pipeline — electron-vite + electron-builder `[Spec: 06-gui.md]`

**Rationale:**
- electron-vite's `src/main`, `src/preload`, `src/renderer` structure enforces security boundaries at the filesystem level `[Research-backed: Gemini §Build Pipeline, Claude ADR-1]`
- Electron Forge's Vite plugin is experimental with known 1.1GB package bloat regression (issue #4045) `[Research-backed: Claude ADR-1]`
- electron-builder's `extraResources` is essential for bundling PyInstaller binary outside ASAR `[Research-backed: Gemini §Python Lifecycle]`

**Risk:** Low — unanimous agreement, mature tooling.

---

## D2: Router — TanStack Router v1 `[Research-backed: Claude ADR-2; Human-approved: user confirmed]`

**Why TanStack Router over React Router v7:**
- 100% type-safe routing with compile-time checked params and paths
- First-class search params for trading filters (symbol, sort, date range)
- Native TanStack Query integration via `routeContext` + loaders
- Built-in `lazy()` code splitting (replaces `React.lazy()`)
- Hash routing via `createHashHistory()` — required for Electron

**Trade-offs accepted:**
- Smaller ecosystem (~2.1M vs ~16M weekly downloads)
- Different paradigm from React Router (medium learning curve)

**Risk:** Medium — smaller community, but type safety catches navigation errors across 22+ modules at build time.

---

## D3: State Management — Zustand v5 `[Research-backed: Claude ADR-5; Human-approved: user confirmed]`

**Why Zustand over React Context:**
- Selector-based updates prevent re-render cascades across 22+ modules
- Slice pattern maps 1:1 to feature modules
- `persist` middleware integrates with electron-store for window state
- `getState()` enables IPC access outside React components
- Only 1.2KB gzipped

**Coexistence with existing patterns:**
- `usePersistedState` (TanStack Query + REST) remains for server-persisted settings
- Zustand handles fast, client-only UI state only
- electron-store handles window bounds persistence

**Risk:** Low — zero existing code impact (ui/ is greenfield). BUILD_PLAN.md specified React Context but no code exists.

---

## D4: Monorepo Structure — Standalone `package.json` `[Local Canon: mcp-server/ pattern]`

**Decision:** `ui/` gets its own `package.json`, NOT a workspace member.

**Rationale:**
- Matches existing `mcp-server/` pattern
- REST API IS the contract — both consumers generate/consume the same JSON shapes
- No shared TypeScript package needed between `ui/` and `mcp-server/`
- Workspace restructure is easy later if shared schemas multiply

**Risk:** Low — type drift is manageable until it becomes painful.

---

## D5: React Compiler — Enable from Day 1 `[Research-backed: Claude ADR-6]`

**Rationale:**
- Stable since October 2025 (5+ months)
- Automatic memoization eliminates manual `useMemo`/`useCallback`
- 12% faster initial load, 2.5× faster interactions (Meta benchmarks)
- New code avoids edge cases that affect migration

**Configuration:**
```typescript
// electron.vite.config.ts (renderer section)
plugins: [
  react({
    babel: {
      plugins: [['babel-plugin-react-compiler', {}]]
    }
  })
]
```

**Edge case:** Use `useWatch()` not `watch()` with React Hook Form. Escape hatch: `"use no memo"` directive per-component.

**Risk:** Low — greenfield code, trivial workaround for RHF.

---

## D6: `<Activity>` Component — Defer, Design For It `[Research-backed: Claude ADR-8]`

**Decision:** Don't implement in MEU-43, but design TanStack Router root layout so `<Activity>` can be added later without restructuring.

**Rationale:**
- MEU-43 creates AppShell layout + route outlet — no content views to wrap
- `<Activity>` wraps content views for state preservation during tab switches
- Useful starting in MEU-46+ when trading views exist

**Risk:** None — deferral is appropriate.

---

## D7: Security — Ephemeral Bearer Token `[Research-backed: Gemini §Security Architecture, synthesis-final-decisions.md §Adopt-Now]`

**Decision:** Generate `crypto.randomBytes(32).toString('hex')` on each app launch. Pass to:
1. Python subprocess via spawn args
2. React renderer via `contextBridge.exposeInMainWorld()`
3. FastAPI validates token on every REST request

**Why needed:**
- Without it, any local process can query the SQLCipher database via the REST API
- Defense-in-depth against local malware
- Zero user friction (transparent, per-session)

**Risk:** Low — simple implementation, no UX impact.

---

## Version-Locked Dependency Table

| Category | Technology | Version | Confidence |
|----------|-----------|---------|:----------:|
| Build | electron-vite | ~5.0.x | ✅ Unanimous |
| Build | electron-builder | ~26.8.x | ✅ Unanimous |
| Runtime | Electron | Latest stable at init (~41.x) | ✅ Verified |
| Core | React | ~19.2.x | ✅ Unanimous |
| Core | React Compiler | ~1.0 | ✅ Resolved |
| CSS | Tailwind CSS + @tailwindcss/vite | ~4.2.x | ✅ Unanimous |
| Components | shadcn/ui (Mira preset) + Radix | Latest | ✅ Unanimous |
| Router | TanStack Router | ~1.166.x | ✅ Resolved |
| Server State | TanStack Query | ~5.90.x | ✅ Unanimous |
| Local UI State | Zustand | ~5.0.x | ✅ Resolved |
| Data Grids | TanStack Table + Virtual | ~8.21.x + ~3.5.x | ✅ Unanimous |
| Charts | Lightweight Charts | ~4.2.x | ✅ Pre-committed |
| Forms | React Hook Form + Zod | ~7.54+ / ~3.24.x | ✅ Unanimous |
| Fuzzy Search | fuse.js | ~7.0.x | ✅ Pre-committed |
| Toasts | sonner | ~1.7.x | ✅ Pre-committed |
| Window State | electron-store | ~10.0.x (ESM-only) | ✅ Pre-committed |
| Security | Ephemeral Bearer token | Custom | ✅ Resolved |
| Startup UX | Splash window | Custom HTML | ✅ Resolved |
| Testing | Vitest + RTL + Playwright | ~3.0 / ~16.1 / ~1.50 | ✅ Unanimous |

## Insights Adoption Matrix

| Category | Count | Items |
|----------|:-----:|-------|
| **Adopt Now** (MEU-43/44/45) | 9 | Bearer token, stdio:ignore, electron-store ESM, preload testing, React Compiler, Mira preset, splash window, staleTime:0, feature dirs |
| **Defer** (later MEUs) | 4 | `<Activity>`, `useEffectEvent`, V8 bytecode, memory monitoring |
| **Skip** | 3 | PythonManager singleton (reference only), Electron version pin, React Router migration |

---

## Cross-References

- Source prompts: `_inspiration/electron_react_python_research/deep-research-prompts.md`
- Gemini output: `_inspiration/electron_react_python_research/gemini-Electron React Python App Architecture.md`
- GPT-5.4 output: `_inspiration/electron_react_python_research/chatgpt-Technology Stack Validation for an Electron + React Trading Desktop App.md`
- Claude output: `_inspiration/electron_react_python_research/claude-Zorivest architecture decision synthesis.md`
- Cross-model synthesis: `_inspiration/electron_react_python_research/synthesis-gui-shell-foundation.md`
- Final decisions: `_inspiration/electron_react_python_research/synthesis-final-decisions.md`
