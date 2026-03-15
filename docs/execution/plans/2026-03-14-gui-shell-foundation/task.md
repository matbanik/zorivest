# GUI Shell Foundation — Task List

## Phase A: MEU-43 — Electron + React Infrastructure

### Task 1 — Scaffold `ui/` package with electron-vite
- **owner_role:** coder
- **Deliverable:** `ui/package.json` + config files + directory structure
- **Status:** `pending`
- **Validation:**
```powershell
Test-Path ui\package.json
Test-Path ui\electron.vite.config.ts
Test-Path ui\tsconfig.json
```

### Task 2 — Install all dependencies
- **owner_role:** coder
- **Deliverable:** `ui/node_modules/` populated, `package-lock.json` created
- **Status:** `pending`
- **Validation:**
```powershell
cd ui && npm ls electron-vite @tanstack/react-router zustand fuse.js sonner electron-store
# Expected: all packages listed without errors
```

### Task 3 — Initialize shadcn/ui with Mira preset
- **owner_role:** coder
- **Deliverable:** `ui/components.json` + initial shadcn components
- **Status:** `pending`
- **Validation:**
```powershell
Test-Path ui\components.json
Test-Path ui\src\renderer\src\components\ui\button.tsx
```

### Task 4 — Write MEU-43 tests (Red phase)
- **owner_role:** tester
- **Deliverable:** 4 test files, all FAIL (Red)
- **Status:** `pending`
- **Validation:**
```powershell
cd ui && npx vitest run --reporter=verbose 2>&1 | Select-String "FAIL"
# Expected: all tests fail (Red phase — no implementation yet)
```

### Task 5 — Implement Electron main process + PythonManager + splash
- **owner_role:** coder
- **Deliverable:** `src/main/index.ts`, `python-manager.ts`, `splash.html`
- **Status:** `pending`
- **Validation:**
```powershell
Test-Path ui\src\main\index.ts
Test-Path ui\src\main\python-manager.ts
Test-Path ui\src\main\splash.html
```

### Task 6 — Implement preload bridge
- **owner_role:** coder
- **Deliverable:** `src/preload/index.ts`
- **Status:** `pending`
- **Validation:**
```powershell
rg "contextBridge.exposeInMainWorld" ui\src\preload\index.ts
# Expected: ≥1 match
```

### Task 7 — Implement React renderer: app.tsx, router.tsx, globals.css
- **owner_role:** coder
- **Deliverable:** Core renderer files
- **Status:** `pending`
- **Validation:**
```powershell
Test-Path ui\src\renderer\src\app.tsx
Test-Path ui\src\renderer\src\router.tsx
rg "@theme" ui\src\renderer\src\globals.css
# Expected: @theme block present
```

### Task 8 — Implement AppShell, NavRail, Header, StatusFooter
- **owner_role:** coder
- **Deliverable:** Layout components with ARIA landmarks
- **Status:** `pending`
- **Validation:**
```powershell
rg "role=|<nav|<main|<header|aria-label" ui\src\renderer\src\components\layout\AppShell.tsx ui\src\renderer\src\components\layout\NavRail.tsx
# Expected: ARIA landmarks present
```

### Task 9 — Implement lib modules: apiFetch, query-client, utils
- **owner_role:** coder
- **Deliverable:** `lib/api.ts`, `lib/query-client.ts`, `lib/utils.ts`
- **Status:** `pending`
- **Validation:**
```powershell
rg "Bearer" ui\src\renderer\src\lib\api.ts
rg "staleTime.*0" ui\src\renderer\src\lib\query-client.ts
# Expected: Bearer token in api.ts, staleTime: 0 in query-client.ts
```

### Task 10 — Implement hooks: usePersistedState, useNotifications
- **owner_role:** coder
- **Deliverable:** `hooks/usePersistedState.ts`, `hooks/useNotifications.tsx`
- **Status:** `pending`
- **Validation:**
```powershell
Test-Path ui\src\renderer\src\hooks\usePersistedState.ts
Test-Path ui\src\renderer\src\hooks\useNotifications.tsx
```

### Task 11 — Implement Zustand layout store
- **owner_role:** coder
- **Deliverable:** `stores/layout.ts`
- **Status:** `pending`
- **Validation:**
```powershell
rg "useLayoutStore" ui\src\renderer\src\stores\layout.ts
# Expected: store exported
```

### Task 12 — Implement stub route pages + SkipLink + ModuleSkeleton
- **owner_role:** coder
- **Deliverable:** 5 stub pages + accessibility components
- **Status:** `pending`
- **Validation:**
```powershell
Test-Path ui\src\renderer\src\features\accounts\AccountsHome.tsx
Test-Path ui\src\renderer\src\components\SkipLink.tsx
Test-Path ui\src\renderer\src\components\ModuleSkeleton.tsx
```

### Task 13 — Verify MEU-43 tests pass (Green phase)
- **owner_role:** tester
- **Deliverable:** All MEU-43 tests pass
- **Status:** `pending`
- **Validation:**
```powershell
cd ui && npx vitest run --reporter=verbose
# Expected: all MEU-43 tests pass
```

### Task 14 — Verify build + lint
- **owner_role:** tester
- **Deliverable:** Build, type check, and lint all pass
- **Status:** `pending`
- **Validation:**
```powershell
cd ui && npx tsc --noEmit
cd ui && npx eslint src/ --max-warnings 0
cd ui && npx electron-vite build
# Expected: all succeed
```

---

## Phase B: MEU-44 — Command Registry + Palette

### Task 15 — Write MEU-44 tests (Red phase)
- **owner_role:** tester
- **Deliverable:** 2 test files, all FAIL
- **Status:** `pending`
- **Validation:**
```powershell
cd ui && npx vitest run --reporter=verbose src/renderer/src/registry src/renderer/src/components/__tests__/CommandPalette 2>&1 | Select-String "FAIL"
# Expected: tests fail (Red phase)
```

### Task 16 — Implement registry types + static entries
- **owner_role:** coder
- **Deliverable:** `registry/types.ts`, `registry/commandRegistry.ts`
- **Status:** `pending`
- **Validation:**
```powershell
Test-Path ui\src\renderer\src\registry\types.ts
Test-Path ui\src\renderer\src\registry\commandRegistry.ts
```

### Task 17 — Implement CommandPalette component + useDynamicEntries
- **owner_role:** coder
- **Deliverable:** `components/CommandPalette.tsx`, `registry/useDynamicEntries.ts`
- **Status:** `pending`
- **Validation:**
```powershell
rg "Fuse" ui\src\renderer\src\components\CommandPalette.tsx
Test-Path ui\src\renderer\src\registry\useDynamicEntries.ts
# Expected: Fuse.js import present
```

### Task 18 — Verify MEU-44 tests pass (Green phase)
- **owner_role:** tester
- **Deliverable:** All MEU-44 tests pass
- **Status:** `pending`
- **Validation:**
```powershell
cd ui && npx vitest run --reporter=verbose
# Expected: all tests pass (MEU-43 + MEU-44)
```

---

## Phase C: MEU-45 — Window State Persistence

### Task 19 — Write MEU-45 tests (Red phase)
- **owner_role:** tester
- **Deliverable:** 1 test file, FAIL
- **Status:** `pending`
- **Validation:**
```powershell
cd ui && npx vitest run --reporter=verbose src/main/__tests__/window-state 2>&1 | Select-String "FAIL"
# Expected: tests fail (Red phase)
```

### Task 20 — Implement electron-store window bounds logic
- **owner_role:** coder
- **Deliverable:** `src/main/index.ts` updated with persist/restore
- **Status:** `pending`
- **Validation:**
```powershell
rg "electron-store|windowBounds" ui\src\main\index.ts
# Expected: ≥2 matches
```

### Task 21 — Verify MEU-45 tests pass (Green phase)
- **owner_role:** tester
- **Deliverable:** All MEU-45 tests pass
- **Status:** `pending`
- **Validation:**
```powershell
cd ui && npx vitest run --reporter=verbose
# Expected: all tests pass (MEU-43 + MEU-44 + MEU-45)
```

---

## Phase D: Quality + Handoffs

### Task 22 — Run full quality gate (tests + types + lint + build)
- **owner_role:** tester
- **Deliverable:** All green
- **Status:** `pending`
- **Validation:**
```powershell
cd ui && npx vitest run --reporter=verbose
cd ui && npx tsc --noEmit
cd ui && npx eslint src/ --max-warnings 0
cd ui && npx electron-vite build
# Expected: all pass
```

### Task 23 — Create MEU-43 handoff
- **owner_role:** orchestrator
- **Deliverable:** `.agent/context/handoffs/063-2026-03-14-gui-shell-bp06as6a.md`
- **Status:** `pending`
- **Validation:**
```powershell
Test-Path .agent\context\handoffs\063-2026-03-14-gui-shell-bp06as6a.md
rg "AC-1|AC-16|FAIL_TO_PASS|PASS_TO_PASS" .agent\context\handoffs\063-2026-03-14-gui-shell-bp06as6a.md
# Expected: file exists with AC references and evidence sections
```

### Task 24 — Create MEU-44 handoff
- **owner_role:** orchestrator
- **Deliverable:** `.agent/context/handoffs/064-2026-03-14-command-registry-bp06as6a.md`
- **Status:** `pending`
- **Validation:**
```powershell
Test-Path .agent\context\handoffs\064-2026-03-14-command-registry-bp06as6a.md
rg "AC-1|AC-9|FAIL_TO_PASS|PASS_TO_PASS" .agent\context\handoffs\064-2026-03-14-command-registry-bp06as6a.md
# Expected: file exists with AC references and evidence sections
```

### Task 25 — Create MEU-45 handoff
- **owner_role:** orchestrator
- **Deliverable:** `.agent/context/handoffs/065-2026-03-14-window-state-bp06as6a.md`
- **Status:** `pending`
- **Validation:**
```powershell
Test-Path .agent\context\handoffs\065-2026-03-14-window-state-bp06as6a.md
rg "AC-1|AC-3|FAIL_TO_PASS|PASS_TO_PASS" .agent\context\handoffs\065-2026-03-14-window-state-bp06as6a.md
# Expected: file exists with AC references and evidence sections
```

### Task 26 — Update MEU registry
- **owner_role:** orchestrator
- **Deliverable:** `.agent/context/meu-registry.md` updated with Phase 6 section
- **Status:** `pending`
- **Validation:**
```powershell
rg "MEU-43|MEU-44|MEU-45" .agent\context\meu-registry.md
# Expected: 3 rows with updated status
```

### Task 27 — Update BUILD_PLAN.md
- **owner_role:** orchestrator
- **Deliverable:** `docs/BUILD_PLAN.md` Phase 6 status updated, MEU-43/44/45 rows updated
- **Status:** `pending`
- **Validation:**
```powershell
rg "MEU-43.*gui-shell" docs\BUILD_PLAN.md
# Expected: status updated from ⬜ to completion status
```

### Task 28 — Run MEU gate
- **owner_role:** tester
- **Deliverable:** MEU gate pass
- **Status:** `pending`
- **Validation:**
```powershell
# Python codebase gate (existing tooling)
uv run python tools/validate_codebase.py --scope meu
# UI-specific gate (explicit, not N/A)
cd ui && npx vitest run --reporter=verbose
cd ui && npx tsc --noEmit
cd ui && npx eslint src/ --max-warnings 0
cd ui && npx electron-vite build
# Expected: all pass
```

### Task 29 — Create reflection file
- **owner_role:** orchestrator
- **Deliverable:** `docs/execution/reflections/2026-03-14-gui-shell-foundation-reflection.md`
- **Status:** `pending`
- **Validation:**
```powershell
Test-Path docs\execution\reflections\2026-03-14-gui-shell-foundation-reflection.md
```

### Task 30 — Update metrics table
- **owner_role:** orchestrator
- **Deliverable:** `docs/execution/metrics.md` updated with 3 new rows
- **Status:** `pending`
- **Validation:**
```powershell
rg "gui-shell|command-registry|window-state" docs\execution\metrics.md
# Expected: 3 new rows
```

### Task 31 — Submit to Codex for adversarial review
- **owner_role:** reviewer
- **Deliverable:** Codex verdict = `approved` or `changes_required`
- **Status:** `pending`
- **Validation:**
```powershell
Test-Path .agent\context\handoffs\063-2026-03-14-gui-shell-bp06as6a.md
Test-Path .agent\context\handoffs\064-2026-03-14-command-registry-bp06as6a.md
Test-Path .agent\context\handoffs\065-2026-03-14-window-state-bp06as6a.md
rg "verdict" .agent\context\handoffs\063-2026-03-14-gui-shell-bp06as6a.md .agent\context\handoffs\064-2026-03-14-command-registry-bp06as6a.md .agent\context\handoffs\065-2026-03-14-window-state-bp06as6a.md
# Expected: 3 files exist, each contains a verdict line
```

### Task 32 — Save session state to pomera notes
- **owner_role:** orchestrator
- **Deliverable:** Pomera note ID logged
- **Status:** `pending`
- **Validation (MCP):**
```
# Execute via MCP tool (not a shell command):
pomera_notes action=search search_term="gui-shell-foundation*" limit=1
# Expected: ≥1 result with session state content
```
```powershell
# Shell fallback: verify note was saved by checking handoff references it
rg "pomera.*note.*ID|Pomera note" .agent\context\handoffs\063-2026-03-14-gui-shell-bp06as6a.md
# Expected: ≥1 match referencing the saved note ID
```

### Task 33 — Prepare commit messages
- **owner_role:** orchestrator
- **Deliverable:** Commit messages presented to human via `notify_user`
- **Status:** `pending`
- **Validation:**
```powershell
git status --short -- ui/ docs/ .agent/
# Expected: modified/staged files listed (commit scope)
rg -c "feat:|fix:|chore:|docs:" .agent\context\handoffs\063-2026-03-14-gui-shell-bp06as6a.md
# Expected: ≥1 match — commit messages documented in handoff
```
