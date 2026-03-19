---
meu: 49
slug: gui-notifications
phase: 6
priority: P0
status: ready_for_review
agent: antigravity
iteration: 1
files_changed: 4
tests_added: 17
tests_passing: 17
---

# MEU-49: GUI Notifications

## Scope

Notification system for the Electron GUI with 5 spec-aligned categories, REST-backed suppression preferences, and proper toast rendering via `sonner`. Implements build plan [06a §Notification System](../../../docs/build-plan/06a-gui-shell.md).

## Feature Intent Contract

### Intent Statement
The GUI has a fully functional notification system where users can suppress non-critical categories, errors always display, and confirmation suppression triggers a safe default action.

### Acceptance Criteria

- AC-1 (Source: Spec): `useNotifications()` hook exposes `notify({ category, message, description?, duration?, defaultAction? })` with 5 categories: `success`, `info`, `warning`, `error`, `confirmation`
- AC-2 (Source: Spec): `error` category toast always displays regardless of suppression preferences
- AC-3 (Source: Spec): When `confirmation` is suppressed, the `defaultAction` (cancel) executes automatically
- AC-4 (Source: Spec): Suppressed notifications are logged to `console.log` with `[suppressed:{category}]` prefix
- AC-5 (Source: Spec): Notification preferences read from `GET /api/v1/settings` via TanStack Query, using keys `notification.{category}.enabled`
- AC-6 (Source: Spec): `sonner` `Toaster` component renders positioned bottom-right with dark theme tokens
- AC-7 (Source: Spec): Unit tests verify: error always shows, category suppression works, console logging on suppress

### Negative Cases

- Must NOT: suppress error notifications under any circumstances
- Must NOT: silently swallow suppressed notifications (must log to console)
- Must NOT: use old category names (`trade`, `system`, `data`, `schedule`)
- Must NOT: use `/api/settings/` endpoint paths (must use `/api/v1/settings/`)

### Test Mapping

| Criterion | Test File | Test Function |
|-----------|-----------|---------------|
| AC-1 | `hooks/__tests__/useNotifications.test.tsx` | `should accept "{category}" category and call toast.{method}` (×5) |
| AC-2 | `hooks/__tests__/useNotifications.test.tsx` | `should always show error notifications even when suppressed`, `should NOT suppress error even when error preference is false` |
| AC-3 | `hooks/__tests__/useNotifications.test.tsx` | `should execute defaultAction (cancel) when confirmation is suppressed` |
| AC-4 | `hooks/__tests__/useNotifications.test.tsx` | `should log suppressed notifications with [suppressed:{category}] prefix`, `should NOT log when notifications are shown` |
| AC-5 | `hooks/__tests__/useNotifications.test.tsx` | `should read notification preferences from /api/v1/settings` |
| AC-7 | `hooks/__tests__/useNotifications.test.tsx` | `should suppress {category} when preference is false` (×3) |

## Design Decisions & Known Risks

- **Decision**: Replaced `useCallback([preferences])` with `useRef` pattern — **Reasoning**: TanStack Query data updates trigger re-renders, but useCallback with stale closure can't read latest preferences. useRef ensures notify always reads current data.
- **Decision**: Added `preferencesLoaded` to context value — **Reasoning**: Enables tests to `waitFor` preference loading before testing suppression. Also useful for UI loading states.
- **Decision**: Per-category preference fetch (4 requests) — **Reasoning**: Each category (`success.enabled`, `info.enabled`, `warning.enabled`, `confirmation.enabled`) is fetched individually via `GET /api/v1/settings/notification.{category}.enabled`. This avoids the need for a bulk settings endpoint and aligns with the existing `usePersistedState` pattern. Error category has no preference (always shown).

## Changed Files

| File | Action | Description |
|------|--------|-------------|
| `ui/src/renderer/src/hooks/useNotifications.tsx` | Modified (rewrite) | 5 spec categories, REST preferences via TanStack Query, error-always-shows, confirmation→defaultAction, console logging |
| `ui/src/renderer/src/hooks/__tests__/useNotifications.test.tsx` | Created | 17 unit tests covering all ACs |
| `ui/src/renderer/src/hooks/usePersistedState.ts` | Modified | Endpoint paths `/api/settings/{key}` → `/api/v1/settings/{key}` |
| `ui/tests/e2e/pages/AppPage.ts` | Modified | Build path `build/main/index.js` → `out/main/index.js` (prerequisite fix) |

## Commands Executed

| Command | Result | Notes |
|---------|--------|-------|
| `npx vitest run src/renderer/src/hooks/__tests__/useNotifications.test.tsx` | PASS (17 tests) | All green |
| `npx vitest run` | PASS (73 tests, 9 files) | No regressions |
| `npx tsc --noEmit` | PASS | No type errors |

## FAIL_TO_PASS Evidence

| Test | Before | After |
|------|--------|-------|
| `should accept "success" category` | FAIL (wrong categories) | PASS |
| `should always show error even when suppressed` | FAIL (no suppression logic) | PASS |
| `should execute defaultAction when confirmation suppressed` | FAIL (not implemented) | PASS |
| `should log suppressed with [suppressed:{category}]` | FAIL (not implemented) | PASS |
| `should read preferences from /api/v1/settings` | FAIL (wrong endpoints) | PASS |
| `should suppress {category} when preference is false` (×3) | FAIL (not implemented) | PASS |

---
## Codex Validation Report
{Left blank — Codex fills this section during validation-review workflow}
