---
meu: 45
slug: window-state-persistence
phase: 6
priority: P1
status: ready_for_review
agent: opus-4.6
iteration: 1
files_changed: 2
tests_added: 5
tests_passing: 5
---

# MEU-45: Window State Persistence

## Scope

Implements window bounds persistence using `electron-store` with a TypeScript-typed schema. Window position and size are saved on resize/move with 500ms debounce, and restored on next app launch with fallback defaults (1280×800).

Build plan reference: [06a-gui-shell.md §UI State Persistence](file:///p:/zorivest/docs/build-plan/06a-gui-shell.md)

## Feature Intent Contract

### Intent Statement
Users' window position and size are remembered across sessions — the app opens where and how big they left it.

### Acceptance Criteria
- AC-1 (Spec): Window bounds (x, y, width, height) saved to `electron-store` on resize/move with 500ms debounce
- AC-2 (Spec): Window bounds restored from `electron-store` on app launch with fallback defaults (1280×800)
- AC-3 (Research-backed): `electron-store` configured with TypeScript-typed schema for `windowBounds`

### Negative Cases
- Must NOT: Write to disk on every pixel during resize (debounce required)
- Must NOT: Crash if stored bounds have no x/y (spread only when defined)
- Must NOT: Save bounds after window is destroyed

### Test Mapping
| Criterion | Test File | Test Function |
|-----------|-----------|---------------|
| AC-2 | `src/main/__tests__/window-state.test.ts` | DEFAULT_BOUNDS (1 test) |
| AC-2 | `src/main/__tests__/window-state.test.ts` | getStoredBounds with/without stored value (2 tests) |
| AC-1 | `src/main/__tests__/window-state.test.ts` | saveWindowBounds (1 test) |
| AC-3 | `src/main/window-state.ts` | TypeScript generic `Store<StoreSchema>` (compile-time) |

## Design Decisions & Known Risks

- **Decision**: Lazy-initialized store via `getStore()` instead of module-level `new Store()` — **Reasoning**: `electron-store` v10 is ESM-only; module-level instantiation fails in vitest's node environment before `vi.mock` takes effect. Lazy init defers construction to first use, after mocks are set up.
- **Decision**: Conditional spread for x/y (`...(storedBounds.x !== undefined && { x: storedBounds.x })`) — **Reasoning**: First launch has no stored x/y; letting Electron pick the default center position is better than forcing undefined coordinates.
- **Risk**: If user's stored bounds are off-screen (e.g., disconnected monitor), window may open invisibly. Future MEU could add bounds-validation against `screen.getAllDisplays()`.

## Changed Files

| File | Action | Description |
|------|--------|-------------|
| `src/main/window-state.ts` | Created | Typed store, get/save functions, lazy init |
| `src/main/index.ts` | Modified | Import window-state, restore bounds on launch, debounced save on resize/move |

## Commands Executed

| Command | Result | Notes |
|---------|--------|-------|
| `npx vitest run --reporter=verbose` | PASS (56 tests total, 5 MEU-45) | All green |
| `npx tsc --noEmit` | PASS | 0 errors |
| `npx eslint src/ --max-warnings 0` | PASS | 0 warnings |

## FAIL_TO_PASS Evidence

| Test | Before | After |
|------|--------|-------|
| `window-state.test.ts` (5 tests) | FAIL (module not found) | PASS |

---
## Codex Validation Report
{Left blank — Codex fills this section during validation-review workflow}
