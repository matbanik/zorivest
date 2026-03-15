---
meu: 43
slug: electron-react-infra
phase: 6
priority: P0
status: ready_for_review
agent: opus-4.6
iteration: 1
files_changed: 30
tests_added: 17
tests_passing: 17
---

# MEU-43: Electron + React Infrastructure

## Scope

Scaffolds the entire `ui/` Electron + React application from zero: project structure, build pipeline (electron-vite), Dracula theme, layout components (AppShell, NavRail, Header, StatusFooter, SkipLink), TanStack Router with 5 stub routes, TanStack Query, Python backend lifecycle manager with splash/retry, native menu with Zorivest-specific Help links, and custom app icon.

Build plan reference: [06a-gui-shell.md](file:///p:/zorivest/docs/build-plan/06a-gui-shell.md)

## Feature Intent Contract

### Intent Statement
Users can launch the Electron app, see a branded splash screen, transition to the main AppShell with 5-route navigation, and interact with a fully themed Dracula dark-mode UI.

### Acceptance Criteria
- AC-1 (Spec): Electron main process starts, creates splash window, starts Python backend
- AC-2 (Spec): PythonManager allocates random port, generates auth token, runs health checks with 30s timeout
- AC-3 (Spec): Splash window shows error + retry button on backend timeout
- AC-4 (Spec): AppShell renders NavRail (nav), Header (banner), main content, StatusFooter
- AC-5 (Spec): NavRail has 5 routes: Accounts, Trades, Planning, Scheduling, Settings
- AC-6 (Spec): ARIA landmarks: nav, banner, main, skip-to-content link
- AC-7 (Spec): Native menu with Zorivest-specific Help links (GitHub, Discord)
- AC-8 (Spec): Custom app icon (converted from zorivest.jpeg)
- AC-9 (Spec): Dracula theme with CSS custom properties

### Test Mapping
| Criterion | Test File | Test Function |
|-----------|-----------|---------------|
| AC-1,2,3 | `src/main/__tests__/python-manager.test.ts` | 6 tests covering port/token/health/timeout/retry |
| AC-4,5,6 | `src/renderer/src/__tests__/app.test.tsx` | 6 tests: landmarks, NavRail, skip link |

## Changed Files

| File | Action | Description |
|------|--------|-------------|
| `ui/package.json` | Created | Electron + React deps, scripts |
| `ui/electron.vite.config.ts` | Created | Build config with splash copy plugin |
| `ui/tsconfig.*.json` | Created | 3 TS configs (root, node, web) |
| `ui/vitest.config.ts` | Created | Test config with jsdom |
| `ui/eslint.config.js` | Created | ESLint flat config |
| `ui/tailwind.config.js` | Created | Dracula theme tokens |
| `ui/src/main/index.ts` | Created | Main process with Python lifecycle |
| `ui/src/main/python-manager.ts` | Created | Backend manager with health checks |
| `ui/src/main/splash.html` | Created | Branded splash screen |
| `ui/src/preload/index.ts` | Created | Secure preload bridge |
| `ui/src/renderer/src/app.tsx` | Created | React root with providers |
| `ui/src/renderer/src/router.tsx` | Created | TanStack Router with 5 routes |
| `ui/src/renderer/src/globals.css` | Created | Dracula theme CSS variables |
| `ui/src/renderer/src/components/layout/*.tsx` | Created | AppShell, NavRail, Header, StatusFooter |
| `ui/src/renderer/src/components/SkipLink.tsx` | Created | Accessibility skip link |
| `ui/src/renderer/src/features/*/` | Created | 5 stub feature modules |
| `ui/build/icon.ico`, `icon.png` | Created | Converted from zorivest.jpeg |

## Commands Executed

| Command | Result | Notes |
|---------|--------|-------|
| `npx vitest run --reporter=verbose` | PASS (56 tests total, 17 MEU-43) | All green |
| `npx tsc --noEmit` | PASS | 0 errors |
| `npx eslint src/ --max-warnings 0` | PASS | 0 warnings |

> **Note:** AC-1/AC-2 (Python backend startup) validated by `python-manager.test.ts` unit tests (10 tests). Dev mode skips Python startup by design (`isDev` check in `main/index.ts`); production mode runs the full startup sequence.

## FAIL_TO_PASS Evidence

| Test | Before | After |
|------|--------|-------|
| `python-manager.test.ts` (10 tests) | FAIL (module not found) | PASS |
| `app.test.tsx` (7 tests) | FAIL (components not found) | PASS |

---
## Codex Validation Report
{Left blank — Codex fills this section during validation-review workflow}
