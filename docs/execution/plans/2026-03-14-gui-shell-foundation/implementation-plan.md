# GUI Shell Foundation — MEU-43 + MEU-44 + MEU-45

Bootstrap the Electron + React desktop application from scratch. This is a greenfield `ui/` package — no code exists yet. All three MEUs live in [06a-gui-shell.md](file:///p:/zorivest/docs/build-plan/06a-gui-shell.md) and share the same research deliverables.

## User Review Required

> [!IMPORTANT]
> **Greenfield package.** The `ui/` directory does not exist. This plan creates ~30 new files from scratch. No existing code is modified — only `BUILD_PLAN.md` and `meu-registry.md` metadata updates.

> [!WARNING]
> **Not a working app yet.** After this project, the app will launch and display the AppShell with stubbed route pages. Content pages (Accounts Home dashboard, Trades table, etc.) are MEU-46+ and out of scope.

> [!IMPORTANT]
> **Python backend NOT spawned during tests.** MEU-43 tests mock the Python subprocess. Actual Electron↔Python integration requires a running Python backend, which is tested manually or in future E2E tests.

---

## Project Scope

| Field | Value |
|---|---|
| **Slug** | `gui-shell-foundation` |
| **MEUs** | MEU-43, MEU-44, MEU-45 |
| **Execution Order** | MEU-43 → MEU-44 → MEU-45 |
| **Build-Plan Sections** | [06a](file:///p:/zorivest/docs/build-plan/06a-gui-shell.md) §all |
| **Handoff Names** | `063-2026-03-14-gui-shell-bp06as6a.md`, `064-2026-03-14-command-registry-bp06as6a.md`, `065-2026-03-14-window-state-bp06as6a.md` |

**In-scope:**
- Electron main process (BrowserWindow, PythonManager, splash, preload bridge)
- React renderer (TanStack Router, Query, Zustand, AppShell, NavRail, Header)
- shadcn/ui Mira preset + globals.css with Tailwind @theme
- Command registry types + static entries + CommandPalette component
- Window state persistence (electron-store)
- Notification system (sonner toasts)
- usePersistedState hook + apiFetch wrapper
- Accessibility infrastructure (skip link, focus ring, ARIA landmarks)
- Startup performance logging IPC
- Vitest test infrastructure

**Out-of-scope:**
- Content pages (Accounts Home data, Trades table, etc.) → MEU-46+
- Production Python packaging → Distribution phase
- Playwright E2E tests → future MEU

---

## Spec Sufficiency

All behaviors resolved. Key source documents:

| Source | Type | What It Resolves |
|---|---|---|
| [06a-gui-shell.md](file:///p:/zorivest/docs/build-plan/06a-gui-shell.md) | Spec | Notification system, command palette, UI state persistence, exit criteria |
| [06-gui.md](file:///p:/zorivest/docs/build-plan/06-gui.md) | Spec | AppShell layout, NavRail routes, startup sequence, AccountContext |
| [ai-instructions.md](file:///p:/zorivest/docs/research/gui-shell-foundation/ai-instructions.md) | Research-backed | Directory structure, code templates (§1-§9) |
| [style-guide-zorivest.md](file:///p:/zorivest/docs/research/gui-shell-foundation/style-guide-zorivest.md) | Research-backed | Design tokens (§1-§6), globals.css template (§10), accessibility (§9) |
| [decision.md](file:///p:/zorivest/docs/research/gui-shell-foundation/decision.md) | Research-backed | Technology decisions + version locks |
| [dependency-manifest.md](file:///p:/zorivest/docs/build-plan/dependency-manifest.md) | Local Canon | npm package list |

No unsourced acceptance criteria. No human decision gates required.

---

## MEU-43: GUI Shell — Feature Intent Contract

**Matrix item 15** | Build-plan ref: [06a §all](file:///p:/zorivest/docs/build-plan/06a-gui-shell.md)

### Acceptance Criteria

| AC | Description | Source |
|---|---|---|
| AC-1 | `ui/` package scaffolded with electron-vite, all dependencies installed, `npx electron-vite build` succeeds | Local Canon: dependency-manifest.md |
| AC-2 | Electron main process creates BrowserWindow with security settings (contextIsolation, sandbox, no nodeIntegration) | Research-backed: ai-instructions §3 |
| AC-3 | PythonManager class: token generation, port allocation, spawn, health check with exponential backoff, graceful shutdown | Research-backed: ai-instructions §4 |
| AC-4 | Splash window shown on launch, hidden when main window ready | Research-backed: 06a §Startup |
| AC-5 | Preload bridge exposes `api.baseUrl`, `api.token`, `electronStore.get/set` via contextBridge | Research-backed: ai-instructions §3-§4 |
| AC-6 | TanStack Router configured with hash history, 5 primary routes matching [06-gui.md nav rail](file:///p:/zorivest/docs/build-plan/06-gui.md#L240-L246), lazy loading for all routes except `/` | Spec: 06-gui.md; Research-backed: ai-instructions §5 |
| AC-7 | TanStack Query client configured with `staleTime: 0`, `gcTime: 5min`, `mutations.retry: false` | Research-backed: ai-instructions §6 |
| AC-8 | `apiFetch()` wrapper includes Bearer token header from contextBridge | Research-backed: ai-instructions §6 |
| AC-9 | AppShell component renders NavRail (5 items) + Header + `<Outlet />` with ARIA landmarks (`<nav>`, `<main>`, `<header>`) | Spec: 06-gui.md §App Shell Architecture |
| AC-10 | globals.css contains Tailwind `@theme` block with all Zorivest design tokens (colors, fonts, spacing, radius) | Research-backed: style-guide §10 |
| AC-11 | Accessibility: skip-to-content link, focus-visible ring (`2px solid cyan`), `<html lang="en">`, `prefers-reduced-motion` support | Spec: 06a §Accessibility; Research-backed: style-guide §9 |
| AC-12 | Notification system: `useNotifications()` hook with 5 categories, error locked to always show, suppressible via settings | Spec: 06a §Notification System |
| AC-13 | `usePersistedState()` hook reads/writes UI settings via REST API | Spec: 06a §React Persisted State Hook |
| AC-14 | Zustand `useLayoutStore` with sidebar width, rail collapsed, command palette state; persisted via electron-store | Research-backed: ai-instructions §7 |
| AC-15 | shadcn/ui initialized with Mira-inspired compact density overrides | Research-backed: ai-instructions §8 |
| AC-16 | Startup performance metrics forwarded via IPC bridge | Spec: 06-gui.md §Performance Logging |

---

## MEU-44: Command Registry — Feature Intent Contract

**Matrix item 15c** | Build-plan ref: [06a §Command Palette](file:///p:/zorivest/docs/build-plan/06a-gui-shell.md#L172)

### Acceptance Criteria

| AC | Description | Source |
|---|---|---|
| AC-1 | `CommandRegistryEntry` interface with id, label, category, keywords, icon, action, shortcut fields | Spec: 06a §CommandRegistryEntry Type |
| AC-2 | Static registry with ≥13 entries: 5 navigation + 3 actions + 5 settings | Spec: 06a §Static Registry |
| AC-3 | All navigation entries use TanStack Router's `router.navigate()` and match [06-gui.md canonical routes](file:///p:/zorivest/docs/build-plan/06-gui.md#L240-L246) | Spec: 06-gui.md + 06a §Static Registry |
| AC-4 | All static registry entries have unique `id` values | Spec: build-priority-matrix item 15c |
| AC-5 | CommandPalette component opens on Ctrl+K, closes on Esc | Spec: 06a §CommandPalette Component |
| AC-6 | Fuzzy search via Fuse.js filters results by label + keywords, threshold 0.4 | Spec: 06a §CommandPalette Component |
| AC-7 | Keyboard navigation: ↑/↓ to select, Enter to execute, selected item highlighted | Spec: 06a §CommandPalette Component |
| AC-8 | Results grouped by category when query is empty | Spec: 06a §CommandPalette Component |
| AC-9 | Dynamic entry composition hook (`useDynamicEntries`) returns entries from TanStack Query cache | Spec: 06a §Dynamic Entry Composition |

---

## MEU-45: Window State Persistence — Feature Intent Contract

**Matrix item 15d** | Build-plan ref: [06a §UI State Persistence](file:///p:/zorivest/docs/build-plan/06a-gui-shell.md#L80)

### Acceptance Criteria

| AC | Description | Source |
|---|---|---|
| AC-1 | Window bounds (x, y, width, height) saved to `electron-store` on resize/move with 500ms debounce | Spec: 06a §Window State |
| AC-2 | Window bounds restored from `electron-store` on app launch with fallback defaults (1280×800) | Spec: 06a §Window State |
| AC-3 | `electron-store` configured with TypeScript-typed schema for `windowBounds` | Research-backed: ai-instructions §1 |

---

## Proposed Changes

### MEU-43: Electron + React Infrastructure

#### [NEW] `ui/` package scaffold

~30 new files created per [ai-instructions §1](file:///p:/zorivest/docs/research/gui-shell-foundation/ai-instructions.md#L8) directory structure:

| Category | Files |
|---|---|
| Config | `package.json`, `electron.vite.config.ts`, `electron-builder.yml`, `tsconfig.json`, `tsconfig.node.json`, `tsconfig.web.json`, `components.json` |
| Electron main | `src/main/index.ts`, `src/main/python-manager.ts`, `src/main/splash.html` |
| Preload | `src/preload/index.ts` |
| Renderer core | `src/renderer/index.html`, `src/renderer/src/app.tsx`, `src/renderer/src/router.tsx`, `src/renderer/src/globals.css`, `src/renderer/src/env.d.ts` |
| Lib | `src/renderer/src/lib/api.ts`, `src/renderer/src/lib/query-client.ts`, `src/renderer/src/lib/utils.ts` |
| Layout | `src/renderer/src/components/layout/AppShell.tsx`, `src/renderer/src/components/layout/NavRail.tsx`, `src/renderer/src/components/layout/Header.tsx`, `src/renderer/src/components/layout/StatusFooter.tsx` |
| Hooks | `src/renderer/src/hooks/usePersistedState.ts`, `src/renderer/src/hooks/useNotifications.tsx` |
| Stores | `src/renderer/src/stores/layout.ts` |
| Stubs | `src/renderer/src/features/accounts/AccountsHome.tsx`, + 4 stub modules |
| Components | `src/renderer/src/components/ModuleSkeleton.tsx`, `src/renderer/src/components/SkipLink.tsx` |

---

### MEU-44: Command Registry + Palette

#### [NEW] Registry + Component files

| File | Purpose |
|---|---|
| `src/renderer/src/registry/types.ts` | `CommandRegistryEntry` interface |
| `src/renderer/src/registry/commandRegistry.ts` | Static registry (≥13 entries) |
| `src/renderer/src/registry/useDynamicEntries.ts` | Dynamic entries from Query cache |
| `src/renderer/src/components/CommandPalette.tsx` | Overlay component with Fuse.js search |

---

### MEU-45: Window State Persistence

#### [MODIFY] `src/main/index.ts`

Add electron-store import, window bounds save (debounced) and restore logic to the BrowserWindow creation function.

---

### Metadata Updates

#### [MODIFY] [BUILD_PLAN.md](file:///p:/zorivest/docs/BUILD_PLAN.md)

- Update Phase 6 status: `⬜ Not Started` → `🔵 In Progress`
- Update MEU-43/44/45 status columns from `⬜` to final status

#### [MODIFY] [meu-registry.md](file:///p:/zorivest/.agent/context/meu-registry.md)

- Add Phase 6 section with MEU-43/44/45 rows

---

## Verification Plan

### Automated Tests (Vitest)

All tests run from `ui/` directory:

```powershell
cd ui
npx vitest run --reporter=verbose
```

#### MEU-43 Tests

| Test File | What It Validates |
|---|---|
| `src/main/__tests__/python-manager.test.ts` | PythonManager: token gen (64 hex chars), port allocation (≥1024), health check polling, graceful shutdown |
| `src/renderer/src/lib/__tests__/api.test.ts` | apiFetch: includes Bearer token, throws on non-ok response, sets Content-Type |
| `src/renderer/src/lib/__tests__/query-client.test.ts` | Query client defaults: staleTime=0, gcTime=300000, mutations.retry=false |
| `src/renderer/src/__tests__/app.test.tsx` | React Testing Library: AppShell renders, ARIA landmarks present (nav, main, header), skip-to-content link exists |

#### MEU-44 Tests

| Test File | What It Validates |
|---|---|
| `src/renderer/src/registry/__tests__/commandRegistry.test.ts` | All entries have unique ids, all categories valid, all navigation entries have shortcuts, ≥13 entries |
| `src/renderer/src/components/__tests__/CommandPalette.test.tsx` | Opens on Ctrl+K, closes on Esc, fuzzy search filters correctly, keyboard navigation works |

#### MEU-45 Tests

| Test File | What It Validates |
|---|---|
| `src/main/__tests__/window-state.test.ts` | Bounds saved with debounce, restored on launch, defaults used when no stored state |

### Build Verification

```powershell
# TypeScript type checking
cd ui && npx tsc --noEmit

# Lint
cd ui && npx eslint src/ --max-warnings 0

# electron-vite build succeeds
cd ui && npx electron-vite build
```

### Manual Verification

After `npx electron-vite dev`:
1. Splash window appears briefly, then main window shows
2. NavRail shows 5 items (Accounts, Trades, Planning, Scheduling, Settings)
3. Ctrl+K opens command palette, typing filters entries, Esc closes
4. Window resize → close → reopen → window position/size restored
5. Skip-to-content link visible on Tab press
6. Focus ring visible when tabbing through nav items

> [!NOTE]
> Manual verification requires a running Python backend. If unavailable, PythonManager will timeout after 30s — the splash window should remain visible with an error message and Retry button (per [06a §Startup L408](file:///p:/zorivest/docs/build-plan/06a-gui-shell.md#L408)). The main window must NOT appear on timeout.

### Codex Validation

Submit handoffs for adversarial review per `/validation-review` workflow.
