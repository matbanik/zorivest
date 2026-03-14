# Integrate GUI Shell Research Decisions into Build Plan Documents

Integrate all resolved architecture decisions from the three-model research synthesis (Gemini, GPT-5.4, Claude Opus) into the project's canonical documentation. This produces the `/pre-build-research` deliverables and updates existing build plan files to reflect the locked technology stack.

## User Review Required

> [!IMPORTANT]
> **No code changes.** This plan modifies only documentation files (Markdown). No `ui/` directory exists yet — all Phase 6 GUI code is greenfield. These doc changes align the build plan specifications with the researched and approved technology stack BEFORE `/create-plan` produces the implementation plan for MEU-43/44/45.

> [!WARNING]
> **React Router → TanStack Router.** The `06-gui.md` App.tsx routing example (lines ~121-146) currently shows `<Routes>/<Route>` JSX from React Router. This will be replaced with TanStack Router's `createRouter`/`createHashHistory` pattern. Route paths (`/`, `/trades/*`, `/planning/*`, etc.) remain unchanged.

> [!WARNING]
> **Zustand addition.** This is NOT in the original BUILD_PLAN. Adding it based on Claude's ADR-5 analysis — React Context degrades at 22+ module scale. `usePersistedState` hook remains unchanged for server-persisted settings.

---

## Proposed Changes

### Pre-Build Research Deliverables (4 new files)

These satisfy the `/pre-build-research` workflow's exit criteria.

---

#### [NEW] [scope.md](file:///p:/zorivest/docs/research/gui-shell-foundation/scope.md)

Feature scope for GUI Shell foundation (MEU-43, MEU-44, MEU-45):
- What the GUI shell builds: Electron lifecycle, React infrastructure, AppShell layout, command registry, window state persistence
- What data it consumes: REST API from Python backend (FastAPI, 30+ endpoints)
- Variations: dev mode (vite HMR) vs production (electron-builder package)
- Happy path vs edge cases: Python subprocess lifecycle, cold start latency, localhost security

---

#### [NEW] [patterns.md](file:///p:/zorivest/docs/research/gui-shell-foundation/patterns.md)

Consolidated architecture patterns extracted from 3 model research outputs:
- **Build pipeline pattern**: electron-vite unified config (main/preload/renderer), electron-builder packaging
- **Security pattern**: contextIsolation + sandbox + ephemeral Bearer token + safeStorage
- **Python lifecycle pattern**: PythonManager spawn → health check polling → graceful shutdown
- **State management pattern**: TanStack Query (server state) + Zustand (local UI state) + usePersistedState (server-persisted settings) + electron-store (window bounds)
- **Directory structure pattern**: Feature-based organization with co-located components/hooks/stores/tests
- **Router pattern**: TanStack Router with `createHashHistory()`, file-based routes, `lazy()` code splitting
- **Form pattern**: React Hook Form + Zod schemas for client-side validation (REST JSON is the contract — no shared TypeScript package between `ui/` and `mcp-server/`)
- **TanStack Query config**: `staleTime: 0` for financial data, `mutations: { retry: false }`

---

#### [NEW] [ai-instructions.md](file:///p:/zorivest/docs/research/gui-shell-foundation/ai-instructions.md)

AI instruction set for implementing the GUI shell, including:
- Target directory structure (Claude's ADR-9)
- electron-vite config template
- BrowserWindow security settings
- PythonManager class skeleton
- TanStack Router setup with hash routing
- TanStack Query client config for trading data
- Zustand store pattern for UI state
- shadcn/ui Mira preset initialization
- React Compiler Babel plugin configuration

> All non-spec rules **must** be tagged as `Spec`, `Local Canon`, `Research-backed`, or `Human-approved` per AGENTS.md.

---

#### [NEW] [decision.md](file:///p:/zorivest/docs/research/gui-shell-foundation/decision.md)

Technology decisions with rationale, version locks, and risk assessment:
- All 7 decisions documented (5 unanimous + 2 resolved)
- Version-locked dependency table
- 9 insights adopted, 4 deferred, 3 skipped
- Cross-references to source research papers

---

### Build Plan Document Updates (4 files modified)

---

#### [MODIFY] [dependency-manifest.md](file:///p:/zorivest/docs/build-plan/dependency-manifest.md)

**Lines 43-49** — Replace the Phase 6 npm install commands with the full researched stack:

```diff
 # Phase 6: GUI (Electron + React)
-cd ui
-npm init -y
-npm install react react-dom @tanstack/react-table @tanstack/react-query lightweight-charts fuse.js sonner electron-store
-npm install -D electron electron-builder vite @vitejs/plugin-react typescript vitest
-npm install -D @testing-library/react playwright
-cd ..
+# See docs/research/gui-shell-foundation/decision.md for version rationale
+cd ui
+npm init -y
+# ── Production Dependencies ──
+npm install react react-dom \
+  @tanstack/react-query @tanstack/react-table @tanstack/react-virtual \
+  @tanstack/react-router \
+  zustand \
+  react-hook-form @hookform/resolvers zod \
+  lightweight-charts fuse.js sonner electron-store \
+  lucide-react class-variance-authority clsx tailwind-merge
+# Radix UI primitives (required by shadcn/ui — add more as needed)
+npm install @radix-ui/react-dialog @radix-ui/react-dropdown-menu \
+  @radix-ui/react-popover @radix-ui/react-tabs @radix-ui/react-tooltip \
+  @radix-ui/react-scroll-area @radix-ui/react-select @radix-ui/react-slot
+# ── Dev Dependencies ──
+npm install -D electron electron-vite electron-builder electron-updater \
+  typescript tailwindcss @tailwindcss/vite \
+  @vitejs/plugin-react babel-plugin-react-compiler \
+  vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event \
+  playwright \
+  eslint prettier @types/react @types/react-dom
+cd ..
```

Key changes:
- **Added**: `@tanstack/react-router`, `zustand`, `react-hook-form`, `@hookform/resolvers`, `zod`, `@tanstack/react-virtual`, Radix UI packages, `lucide-react`, `class-variance-authority`, `clsx`, `tailwind-merge`, `tailwindcss`, `@tailwindcss/vite`, `babel-plugin-react-compiler`, `electron-vite`, `electron-updater`
- **Removed**: standalone `vite` (replaced by `electron-vite`)
- **Kept**: everything currently listed

---

#### [MODIFY] [06-gui.md](file:///p:/zorivest/docs/build-plan/06-gui.md)

Three sections to update:

**1. App.tsx routing example (lines ~117-146)**
Replace React Router `<Routes>/<Route>` JSX with TanStack Router equivalent. Code splitting changes from `React.lazy()` to TanStack Router's `lazy()` route definitions.

**2. Route map reconciliation**
Reconcile the navigation rail table (lines ~190-196) with the command registry in `06a-gui-shell.md`. Current canon disagrees:
- `06-gui.md` uses `/planning`, `/scheduling`
- `06a-gui-shell.md` uses `/plans`, `/schedules`, and adds `/reports`, `/watchlists`, `/accounts`

Canonical decision `[Local Canon: 06-gui.md nav rail table, lines 190-196]`: Adopt `06-gui.md`'s nav rail as the master route map (5 primary routes: `/`, `/trades`, `/planning`, `/scheduling`, `/settings`). Update `06a-gui-shell.md` command registry to match. Sub-routes for reports, watchlists, etc. are subroutes within their parent modules.

**3. Tech overview section**
Add mentions of: TanStack Router (routing), Zustand (local UI state), React Compiler (performance), shadcn/ui Mira preset (dense layout), Tailwind CSS v4 (styling).

**Not changed**: `usePersistedState` references, ASCII layout diagram.

---

#### [MODIFY] [06a-gui-shell.md](file:///p:/zorivest/docs/build-plan/06a-gui-shell.md)

Add focused subsections for each new architectural decision. Keep existing content (notifications, `usePersistedState`, command palette) intact.

**New subsections to add (source-basis tagged per AGENTS.md):**
1. **Build Tool — electron-vite** `[Research-backed: Gemini §Build Pipeline, Claude ADR-1]`: electron-vite config, directory structure (src/main, src/preload, src/renderer)
2. **Security — Ephemeral Bearer Token** `[Research-backed: Gemini §Security Architecture]`: nonce generation, Python spawn arg, contextBridge exposure, TanStack Query fetch wrapper, CSP header
3. **Startup — Splash Window + Python Health Check** `[Research-backed: Claude ADR-7]`: splash.html, health poll with exponential backoff, splash→main transition
4. **TanStack Query Configuration** `[Research-backed: Claude ADR-3, synthesis §staleTime]`: `staleTime: 0`, `gcTime: 5 * 60 * 1000`, `mutations: { retry: false }`, trading-specific rationale
5. **Local UI State — Zustand** `[Research-backed: Claude ADR-5, synthesis §Zustand]`: slice pattern, persist middleware → electron-store, distinction from `usePersistedState`
6. **React Compiler** `[Research-backed: Claude ADR-6, synthesis §React Compiler]`: Babel plugin config, `useWatch()` instead of `watch()`, escape hatch directive
7. **shadcn/ui Mira Preset** `[Research-backed: Claude ADR-4]`: initialization, dense spacing, dark theme setup
8. **Python Spawn — Production Mode** `[Research-backed: Gemini §Python Lifecycle, Claude ADR-7]`: `stdio: 'ignore'`, `extraResources` path, process tree kill on Windows

**Modified sections:**
- Command registry `navigate()` calls: update to TanStack Router's `navigate` + align route paths with `06-gui.md` canonical map
- Exit criteria: add security (Bearer token), splash window, Zustand store

---

#### [MODIFY] [architecture.md](file:///p:/zorivest/.agent/docs/architecture.md)

Update the Communication section (line 68) to reflect the new security model:

```diff
-  - **UI ↔ API:** REST over `localhost:8000`. UI uses `fetch`/`httpx`. No authentication needed (local-only).
+  - **UI ↔ API:** REST over `localhost:8000`. Ephemeral Bearer token (nonce-based, generated per-launch) for defense-in-depth against local malware. UI uses `fetch` with token header.
```

This resolves the contradiction between the new ephemeral Bearer token pattern in `06a-gui-shell.md` and the canonical architecture doc. `[Research-backed: Gemini §Security Architecture, synthesis-final-decisions.md §Adopt-Now]`

---

### Zorivest Style Guide (1 new file + build plan additions)

> [!NOTE]
> The matbanik.info [style-guide.md](file:///p:/zorivest/_inspiration/style-guide.md) has been adapted into a Zorivest-specific design system. The adapted guide is a research deliverable, not just a token reference.

---

#### [EXISTING — created during research phase] [style-guide-zorivest.md](file:///p:/zorivest/docs/research/gui-shell-foundation/style-guide-zorivest.md)

Zorivest-adapted design system with cognitive load optimization as its guiding principle. Content:

**§0 Guiding Principle — Optimal Cognitive Load**
- Cognitive Load Balance Equation: Minimize extraneous, maximize germane, accept intrinsic
- 5-point per-screen design protocol (one-thing test, 5-second test, progressive disclosure audit, data-ink audit, color signal check)
- Applied per tool/screen during content MEUs

**§1-§6 Design Tokens (Tier 1 — Build Now in MEU-43)**

| Section | matbanik.info → Zorivest Adaptation |
|---------|--------------------------------------|
| §1 Colors | Dracula base KEPT + added P&L semantic colors (`pnl-profit`, `pnl-loss`, `pnl-neutral`) + order status colors + non-color redundancy rule (arrows/prefixes alongside color) |
| §2 Typography | System fonts KEPT + base reduced to 14px for density + `tabular-nums` rule for all financial numbers + monospace for prices/quantities |
| §3 Spacing | Added `--space-2xs: 2px` micro-gap for data cells + aligned with shadcn/ui Mira compact density |
| §4 Radius | Kept as-is + added `--radius-none: 0px` for table cells |
| §5 Effects | Simplified: depth via borders only, no shadows, blur reserved for command palette overlay |
| §6 Motion | Stripped to signals: 150ms transitions, no hover lifts in tables, added `prefers-reduced-motion` support |

**§9 Accessibility Infrastructure (Tier 1 — Build Now in MEU-43)**

| Feature | WCAG | Shell Responsibility |
|---------|------|---------------------|
| Keyboard navigation | 2.1.1 | Tab order, focus management |
| Focus-visible ring | 2.4.7 | `2px solid cyan`, `2px` offset |
| ARIA landmarks | 1.3.1 | `<nav>`, `<main>`, `<aside>`, `<header>` |
| Skip-to-content link | 2.4.1 | Hidden until focused |
| Heading hierarchy | 1.3.1 | Single `<h1>`, sequential structure |
| `lang` attribute | 3.1.1 | `<html lang="en">` |
| Reduced motion | 2.3.3 | `prefers-reduced-motion` media query |
| Color contrast | 1.4.3 | ≥ 4.5:1 enforced via token palette |
| Semantic HTML | 1.3.1 | `<button>`, `<a>`, `<input>`, never `<div onClick>` |

**§10 Tailwind `@theme` Block**
- Working CSS template for `globals.css` with all Zorivest tokens
- Includes: Dracula colors, P&L semantic colors, trading-adapted spacing, focus ring, skip link, selection styles, reduced motion, tabular-nums utility

---

**§7 Component Principles + §8 Desktop Layout (Tier 2 — Deferred but Tracked)**

The style guide explicitly documents what's deferred and provides a per-component cognitive load checklist so nothing gets lost:

| Deferred Item | Target MEU | Guiding Principle Applied |
|--------------|------------|--------------------------|
| Data grid styling (positions, orders) | MEU-46 (Trades View) | §2 tabular-nums, §3 dense spacing, 5-second test |
| Trade entry form patterns | MEU-47+ | §1 error colors, §6 error shake, form error WCAG 3.3.1 |
| Chart overlays | MEU-65 (Market Data GUI) | §5 limited blur, color signal check |
| Settings panel layout | MEU-44 (Settings) | §3 form spacing, progressive disclosure |
| Command palette glassmorphism | MEU-44 | §5 backdrop blur, focus trap WCAG 2.4.3 |
| Dashboard summary cards | MEU-46+ | §4 radius-lg, data-ink audit, 5-second test |
| Non-color P&L indicators | MEU-46 | §1 arrows + prefixes, WCAG 1.4.1 |
| Screen reader live regions | MEU-65 | `aria-live="polite"`, WCAG 4.1.3 |
| High contrast / forced colors | Accessibility polish MEU | `forced-colors: active` overrides |
| Target size 24×24px | Per-component | WCAG 2.5.8 |
| Text zoom 200% | Layout polish MEU | WCAG 1.4.4 |

> [!IMPORTANT]
> The per-component cognitive load checklist in §7 ensures every future content MEU applies the 5-point protocol. This is not "defer and forget" — it's "defer with a structured quality gate."

---

**Impact on Build Plan Modifications:**

The `06a-gui-shell.md` modification (already in this plan) now ALSO includes:
- Reference to `style-guide-zorivest.md` as the design system source
- Accessibility infrastructure section (9 features from Tier 1 table above)
- `globals.css` `@theme` block template from §10

---

## Verification Plan

### Automated Checks

Since these are documentation-only changes, automated verification is limited to consistency checks:

```powershell
# 1. Verify no orphaned react-router references remain in 06*.md files
rg -i "react-router|react-router-dom|BrowserRouter|HashRouter" docs\build-plan\06-gui.md docs\build-plan\06a-gui-shell.md
# Expected: 0 matches (all replaced with TanStack Router)

# 2. Verify all 5 research deliverables exist
Get-ChildItem docs\research\gui-shell-foundation\
# Expected: scope.md, patterns.md, ai-instructions.md, decision.md, style-guide-zorivest.md

# 3. Verify dependency-manifest.md includes all required packages
rg "zustand|@tanstack/react-router|react-hook-form|electron-vite|tailwindcss|babel-plugin-react-compiler" docs\build-plan\dependency-manifest.md
# Expected: all 6 present

# 4. Verify no orphaned React Router JSX patterns
rg "React\.lazy|<Routes|<Route " docs\build-plan\06-gui.md
# Expected: 0 matches (replaced with TanStack Router lazy())

# 5. Verify security section exists in 06a AND architecture.md is updated
rg -i "bearer|ephemeral|nonce" docs\build-plan\06a-gui-shell.md .agent\docs\architecture.md
# Expected: matches in both files

# 6. Verify stale route paths are absent from 06a command registry
rg "navigate\('/plans'|navigate\('/schedules'|navigate\('/accounts'|navigate\('/reports'|navigate\('/watchlists'" docs\build-plan\06a-gui-shell.md
# Expected: 0 matches (all routes aligned with 06-gui.md canonical map: /, /trades, /planning, /scheduling, /settings)

# 7. Verify no "No authentication" contradiction remains
rg -i "No authentication needed" .agent\docs\architecture.md
# Expected: 0 matches
```

### Codex Validation (Primary)

Submit the implementation plan and all modified files to Codex for adversarial review:
- **Cross-reference**: Every decision in `synthesis-final-decisions.md` must be traceable to the updated build plan docs
- **Consistency**: All 06*.md files that reference routing/state must be consistent with new stack
- **Route map**: `06-gui.md` nav rail and `06a-gui-shell.md` command registry use identical paths
- **Security**: Architecture doc and 06a-gui-shell.md agree on Bearer token model
- **Completeness**: No library from the consolidated stack missing from `dependency-manifest.md`
- **No orphans**: No references to removed technologies (react-router-dom, standalone vite)
- **Source tags**: All non-spec rules in patterns.md and ai-instructions.md carry source basis tags

### Manual Verification

After execution, the user should review:
1. The 5 research files in `docs/research/gui-shell-foundation/`
2. The 4 modified build plan / canonical files for accuracy and completeness
3. Confirm the research brief is saved to pomera notes
