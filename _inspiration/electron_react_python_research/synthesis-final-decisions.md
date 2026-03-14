# Phase 6 GUI Shell — Final Analysis & Decisions

> Covers: Zustand impact, unique insights adoption, and 6 open question resolutions.

---

## 1. Zustand v5 Impact Assessment

### Finding: ZERO Code Impact — Planning-Only Change ✅

| What Exists | Where | Impact |
|------------|-------|--------|
| Python backend code | `packages/` | ❌ Not affected (Python) |
| MCP server code | `mcp-server/` | ❌ Not affected (TypeScript, no React) |
| GUI code | `ui/` | ✅ **Does not exist yet** — greenfield |
| `usePersistedState` hook | `docs/build-plan/06a-gui-shell.md` | ✅ Remains valid — different concern |
| References to "React Context" | `docs/build-plan/` | ❌ **None found** |

### Why `usePersistedState` Still Works

The BUILD_PLAN's `usePersistedState` hook uses **TanStack Query + REST API** to persist settings to the Python backend (SQLCipher). This is **server-persisted state** — theme preference, active page, panel collapse states that survive across devices.

Zustand handles a **different layer**: fast, client-only UI state that doesn't need server persistence — sidebar width during drag, which dialog is open, column sort order, temporary filter state.

```
Server-persisted (usePersistedState → REST API → SQLCipher)
├── ui.theme = "dark"
├── ui.rail.collapsed = "true"
└── ui.accounts.active = "acc-1"

Client-only (Zustand → electron-store for window bounds)
├── sidebar.dragWidth = 240
├── dialog.tradeEntry.isOpen = false
├── table.positions.sortColumn = "pnl"
└── commandPalette.isVisible = false
```

### Documents to Update

Only 3 planning docs need modification — no code exists to change:

1. **`dependency-manifest.md`** — add `zustand` to Phase 6 npm install
2. **`06a-gui-shell.md`** — add Zustand store pattern section
3. **`06-gui.md`** — reference Zustand for cross-module UI state

> **Verdict: Adopt Zustand v5.** Zero risk, zero code migration.

---

## 2. Unique Insights — Adoption Recommendations

### Adopt Now (integrate into MEU-43/44/45) — 9 items

| # | Insight | Source | Why It Matters |
|---|---------|:------:|----------------|
| 1 | **Ephemeral Bearer token** for localhost REST security | Gemini | CRITICAL gap — without it, any local process can query SQLCipher. Electron generates `crypto.randomBytes(32)`, passes to Python via spawn args and to React via contextBridge |
| 2 | **`stdio: 'ignore'` in production** | Gemini | If Python logs heavily without readers, 64KB OS pipe buffer fills → Python freezes silently |
| 3 | **electron-store is ESM-only** | GPT-5.4 | Requires Electron 30+ and ESM-compatible main process builds. electron-vite handles this, but must verify |
| 4 | **Preload + ESM + sandbox** testing | GPT-5.4 | Real-world race conditions cause "dev works, prod breaks" — add prod build test to verification |
| 5 | **React Compiler 1.0** | Claude | Automatic memoization, 12% faster load. Enable as Babel plugin from day 1 (new code avoids edge cases) |
| 6 | **shadcn/ui Mira preset** | Claude | Purpose-built for compact, dense interfaces — Bloomberg-grade trading density |
| 7 | **Splash window** during cold start | Claude | Show lightweight HTML splash while Python boots (5-10s cold start otherwise) |
| 8 | **`staleTime: 0` + no optimistic mutations** | Claude | All financial data always refetches. NEVER auto-retry financial mutations. Show "last updated" timestamps |
| 9 | **Feature-based directory structure** | Claude | `features/{module}/` with co-located components, hooks, stores, tests — scales to 22+ modules |

### Defer to Later MEUs — 4 items

| # | Insight | Source | Target |
|---|---------|:------:|--------|
| 10 | `<Activity>` component | Claude | Content MEUs (MEU-46+) — needs views to wrap |
| 11 | `useEffectEvent` | Claude | Market data GUI (MEU-65) — WebSocket handlers |
| 12 | V8 bytecode compilation | Gemini | Distribution/packaging MEU |
| 13 | Memory leak monitoring | Claude | Health/ops MEU — `process.memoryUsage()` on 60s intervals |

### Skip — 3 items

| # | Insight | Reason |
|---|---------|--------|
| PythonManager singleton | Reference pattern, not a plan change |
| Electron 41.0.2 specific | Pin at `npm init` time, not declarative |
| React Router v6→v7 | N/A — chose TanStack Router |

---

## 3. Open Questions — Resolved

### Q1: Electron Version Compatibility

**Decision: Use latest stable Electron at `npm init` time.**

| Factor | Detail |
|--------|--------|
| Current stable (Mar 2026) | Electron 41.0.2 (Chromium 146, Node 24.14) per GPT-5.4 |
| electron-vite v5.0.0 | Published Dec 2025, no max Electron version specified |
| electron-store | ESM-only, requires Electron 30+ |
| Compatibility risk | Low — electron-vite operates at build layer, not runtime |

**Verification:** After scaffold, run `npx electron-vite dev` → confirm main, preload, and renderer start. If issues, fall back to highest compatible version.

---

### Q2: Router — **DECIDED: TanStack Router v1** ✅

User confirmed.

---

### Q3: State Management — **DECIDED: Zustand v5** ✅

Zero code impact. See Section 1 above.

---

### Q4: Monorepo Structure

**Decision: Standalone `package.json` (matching `mcp-server/` pattern).**

| Current State | Detail |
|--------------|--------|
| `mcp-server/` | Own `package.json`, NOT a workspace member |
| Root `package.json` | Does NOT exist |
| `packages/` | Python/uv, separate ecosystem |
| Shared types | Both MCP server and GUI consume REST API |

**Rationale:**
- REST API IS the contract — both consumers generate/consume the same JSON shapes
- Type drift is manageable until it becomes painful
- Workspace restructure is easy later if shared schemas multiply
- Follows Claude: *"start simpler, extract when pain is real"*

---

### Q5: React Compiler

**Decision: Enable from day 1.**

| Factor | Detail |
|--------|--------|
| Stability | Stable since October 2025 (5+ months) |
| Setup | Babel plugin in electron-vite renderer config |
| Edge cases | Use `useWatch()` not `watch()` for RHF (trivial for new code) |
| Escape hatch | `"use no memo"` directive per-component |
| Performance win | Eliminates manual `useMemo`/`useCallback`, 12% faster initial load |

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

---

### Q6: `<Activity>` Component

**Decision: Defer implementation, design for it.**

- MEU-43 creates the AppShell layout + route outlet — no content views to wrap
- `<Activity>` wraps content views for state preservation during tab switches
- **Design the TanStack Router root layout** so `<Activity>` can be added later without restructuring
- Document in ai-instructions for content MEUs

---

## 4. Final Consolidated Stack

All decisions resolved:

| Category | Technology | Version | Decision |
|----------|-----------|---------|:--------:|
| Build | electron-vite + electron-builder | ~5.0 / ~26.8 | ✅ |
| Runtime | Electron | Latest stable at init | ✅ |
| Core | React + React Compiler | ~19.2 + ~1.0 | ✅ |
| CSS | Tailwind CSS + @tailwindcss/vite | ~4.2 | ✅ |
| Components | shadcn/ui (Mira preset) + Radix | Latest | ✅ |
| Router | **TanStack Router** | ~1.166 | ✅ |
| Server State | TanStack Query | ~5.90 | ✅ |
| Local UI State | **Zustand** | ~5.0 | ✅ |
| Data Grids | TanStack Table + Virtual | ~8.21 / ~3.5 | ✅ |
| Charts | Lightweight Charts | ~4.2 | ✅ |
| Forms | React Hook Form + Zod | ~7.54 / ~3.24 | ✅ |
| Testing | Vitest + RTL + Playwright | ~3.0 / ~16.1 / ~1.50 | ✅ |
| Security | Ephemeral Bearer token | Custom | ✅ |
| Startup UX | Splash window | Custom HTML | ✅ |

## 5. Next Step

Execute `/pre-build-research` to formalize these decisions into `docs/research/gui-shell-foundation/`, then `/create-plan` for MEU-43 + MEU-44 + MEU-45.
