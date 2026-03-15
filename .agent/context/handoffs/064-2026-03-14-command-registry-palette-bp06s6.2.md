---
meu: 44
slug: command-registry-palette
phase: 6
priority: P1
status: ready_for_review
agent: opus-4.6
iteration: 1
files_changed: 6
tests_added: 25
tests_passing: 25
---

# MEU-44: Command Registry + Palette

## Scope

Implements the command registry system and CommandPalette overlay component. Provides a `CommandRegistryEntry` type, 13 static entries (5 navigation + 3 actions + 5 settings), a `useDynamicEntries` hook for TanStack Query cache, and a Fuse.js-powered fuzzy search overlay with keyboard navigation.

Build plan reference: [06a-gui-shell.md §Command Palette](file:///p:/zorivest/docs/build-plan/06a-gui-shell.md)

## Feature Intent Contract

### Intent Statement
Users can press Ctrl+K (or click the header hint) to open a command palette, search commands by fuzzy match, navigate with keyboard, and execute actions.

### Acceptance Criteria
- AC-1 (Spec): `CommandRegistryEntry` interface with id, label, category (`navigation|action|settings|search`), keywords, icon, action, shortcut fields
- AC-2 (Spec): Static registry with 13 entries: 5 navigation + 3 action + 5 settings per 06a-gui-shell.md
- AC-3 (Spec): Navigation entries call `router.navigate()` with correct paths
- AC-4 (Spec): All static registry entries have unique `id` values
- AC-5 (Spec): Action entries are spec-aligned stubs (Position Calculator, Import Trades, Account Review)
- AC-6 (Spec): Settings entries navigate to `/settings/*` sub-routes
- AC-7 (Spec): CommandPalette opens on Ctrl+K, closes on Esc
- AC-8 (Spec): Fuzzy search via Fuse.js filters by label + keywords, threshold 0.4
- AC-9 (Spec): Keyboard navigation: ↑/↓ to select, Enter to execute, selected item highlighted
- AC-10 (Spec): Results grouped by category when query is empty
- AC-11 (Spec): `useDynamicEntries` hook returns entries from TanStack Query cache (category: 'search')

### Negative Cases
- Must NOT: Allow duplicate entry IDs in the static registry
- Must NOT: Fire handleKeyDown twice per keystroke (double-firing bug fixed via single handler on input)

### Test Mapping
| Criterion | Test File | Test Function |
|-----------|-----------|---------------|
| AC-1 | `registry/__tests__/commandRegistry.test.ts` | type contract (3 tests) |
| AC-2,3,4,5,6 | `registry/__tests__/commandRegistry.test.ts` | static registry (7 tests) |
| AC-7 | `__tests__/app.test.tsx` | Ctrl+K opens/closes CommandPalette |
| AC-8 | `components/__tests__/CommandPalette.test.tsx` | filter results when typing |
| AC-9 | `components/__tests__/CommandPalette.test.tsx` | aria-selected, Enter execute, navigate side-effect |
| AC-10 | `components/__tests__/CommandPalette.test.tsx` | group by category |
| AC-11 | `registry/__tests__/useDynamicEntries.test.tsx` | empty cache, populated, reactive update, 10-cap (4 tests) |

## Design Decisions & Known Risks

- **Decision**: Used refs (`selectedIndexRef`, `flatResultsRef`) instead of state in `handleKeyDown` callbacks — **Reasoning**: Avoids stale closure bug where React batches state updates between synchronous `fireEvent` calls in tests, and also prevents Enter from reading outdated selectedIndex in production.
- **Decision**: Removed duplicate `onKeyDown` from container div — **Reasoning**: Having `onKeyDown` on both the input and its parent container caused ArrowDown to fire twice via event bubbling.

## Changed Files

| File | Action | Description |
|------|--------|-------------|
| `src/renderer/src/registry/types.ts` | Created | `CommandRegistryEntry` interface |
| `src/renderer/src/registry/commandRegistry.ts` | Created | 13 static entries with Lucide icons |
| `src/renderer/src/registry/useDynamicEntries.ts` | Created | Dynamic entries from Query cache |
| `src/renderer/src/components/CommandPalette.tsx` | Created | Overlay with Fuse.js, keyboard nav, categories |
| `src/renderer/src/components/layout/AppShell.tsx` | Modified | Added Ctrl+K handler + CommandPalette mount |
| `src/renderer/src/components/layout/Header.tsx` | Modified | Made Ctrl+K hint clickable |

## Commands Executed

| Command | Result | Notes |
|---------|--------|-------|
| `npx vitest run --reporter=verbose` | PASS (56 tests total, 25 MEU-44) | All green |
| `npx tsc --noEmit` | PASS | 0 errors |
| `npx eslint src/ --max-warnings 0` | PASS | 0 warnings |

## FAIL_TO_PASS Evidence

| Test | Before | After |
|------|--------|-------|
| `commandRegistry.test.ts` (10 tests) | FAIL (module not found) | PASS |
| `CommandPalette.test.tsx` (9 tests) | FAIL (component not found) | PASS |

> Navigate side-effect test: selecting Accounts entry calls `mockNavigate({ to: '/' })`.

---
## Codex Validation Report
{Left blank — Codex fills this section during validation-review workflow}
