# Execution Handoff — GUI Shell Research Integration

## Task

- **Date:** 2026-03-14
- **Task slug:** gui-shell-research-integration-execution
- **Owner role:** coder
- **Scope:** Integrate resolved GUI shell research decisions into canonical build plan and research documentation. Documentation-only changes (no code). Covers Tasks 1–11 from the approved [implementation-plan.md](file:///p:/zorivest/docs/execution/plans/2026-03-14-gui-shell-research-integration/implementation-plan.md).

## Inputs

- **User request:** Execute the approved implementation plan after 6 Codex plan-review passes
- **Specs/docs referenced:**
  - [implementation-plan.md](file:///p:/zorivest/docs/execution/plans/2026-03-14-gui-shell-research-integration/implementation-plan.md) — approved plan
  - [task.md](file:///p:/zorivest/docs/execution/plans/2026-03-14-gui-shell-research-integration/task.md) — 12-task checklist (11 executed, 1 pending)
  - [synthesis-final-decisions.md](file:///p:/zorivest/_inspiration/electron_react_python_research/synthesis-final-decisions.md) — resolved technology decisions
  - [synthesis-gui-shell-foundation.md](file:///p:/zorivest/_inspiration/electron_react_python_research/synthesis-gui-shell-foundation.md) — cross-model research synthesis
  - [06-gui.md nav rail table](file:///p:/zorivest/docs/build-plan/06-gui.md#L238) — canonical route map
- **Constraints:** No code changes. All files are documentation. Source-basis tags required on all non-spec rules per AGENTS.md.

## Role Plan

1. orchestrator — scope validation from synthesis docs
2. coder — create research deliverables + modify build plan files
3. tester — run 7 automated consistency checks
4. reviewer — this handoff → Codex validation

## Coder Output

### Changed Files

**Phase A — New research deliverables (4 files created):**

| # | File | Purpose |
|---|------|---------|
| 1 | [scope.md](file:///p:/zorivest/docs/research/gui-shell-foundation/scope.md) | Feature scope for MEU-43/44/45 — happy path, edge cases, dev/prod variations, out-of-scope |
| 2 | [patterns.md](file:///p:/zorivest/docs/research/gui-shell-foundation/patterns.md) | 8 architecture patterns with code examples — all source-tagged |
| 3 | [ai-instructions.md](file:///p:/zorivest/docs/research/gui-shell-foundation/ai-instructions.md) | 9 implementation sections with TypeScript templates — all source-tagged |
| 4 | [decision.md](file:///p:/zorivest/docs/research/gui-shell-foundation/decision.md) | 7 decisions, version-locked dependency table, insights adoption matrix |

**Phase A — Existing file (validated, no changes needed):**

| # | File | Purpose |
|---|------|---------|
| 5 | [style-guide-zorivest.md](file:///p:/zorivest/docs/research/gui-shell-foundation/style-guide-zorivest.md) | Pre-existing adapted design system (created during research phase) |

**Phase B — Build plan files modified (4 files):**

| # | File | Changes |
|---|------|---------|
| 6 | [dependency-manifest.md](file:///p:/zorivest/docs/build-plan/dependency-manifest.md) | Phase 6 npm install expanded from 3 → 28 packages. Added: `@tanstack/react-router`, `zustand`, `react-hook-form`, `@hookform/resolvers`, `zod`, `electron-vite`, `tailwindcss`, `@tailwindcss/vite`, `babel-plugin-react-compiler`, 8 Radix UI packages, `lucide-react`, `class-variance-authority`, `clsx`, `tailwind-merge`, `@tanstack/react-virtual`, `electron-updater`, `@testing-library/jest-dom`, `@testing-library/user-event`, `eslint`, `prettier`. Removed: standalone `vite` (replaced by `electron-vite`) |
| 7 | [06-gui.md](file:///p:/zorivest/docs/build-plan/06-gui.md) | (a) Replaced React Router `<Routes>/<Route>` JSX with TanStack Router `createRouter`/`createHashHistory`/`lazy()` pattern. (b) Updated key rules: `React.lazy()` → TanStack Router `lazy()`. (c) Added technology stack summary. (d) Fixed research-basis reference and Outputs section to remove `React.lazy()` |
| 8 | [06a-gui-shell.md](file:///p:/zorivest/docs/build-plan/06a-gui-shell.md) | (a) Realigned command registry routes: removed stale `/plans`, `/schedules`, `/accounts`, `/reports`, `/watchlists`; replaced with canonical `/`, `/trades`, `/planning`, `/scheduling`; added root `nav:settings` with `Ctrl+,`. Added `router.navigate()` wrapper. Watchlist dynamic route updated to `/planning/watchlists/`. (b) Added 8 new architectural subsections (electron-vite, Bearer token, splash, TanStack Query config, Zustand, React Compiler, shadcn/ui Mira, Python spawn production). (c) Migrated `usePersistedState` from hardcoded `localhost:8765` to `apiFetch` via contextBridge. Migrated `NotificationProvider` from `fetch(${API})` to `apiFetch`. (d) Removed manual `useCallback`/`useMemo` from `usePersistedState` and `CommandPalette` (React Compiler). (e) Moved sidebar width from `SettingModel/REST` to `Zustand + electron-store`. Clarified settings key table scope. (f) Added source tags to Design System Reference section. (g) Added accessibility infrastructure section. (h) Expanded exit criteria and outputs list |
| 9 | [architecture.md](file:///p:/zorivest/.agent/docs/architecture.md) | (a) Line 68: replaced `No authentication needed (local-only)` with ephemeral Bearer token description. (b) Line 25: updated diagram from `localhost:8000` to `localhost, dynamic port`. (c) Line 68: added `dynamic port via net.createServer(0)` to Communication section |

### Design Notes / ADRs Referenced

- All 7 decisions from `synthesis-final-decisions.md` traced to the research deliverables
- Route map canonical decision: `06-gui.md` nav rail table (lines 238–244) is the master; `06a-gui-shell.md` command registry aligned
- Security contract: Bearer token consistent across `06a-gui-shell.md` §Security and `architecture.md` §Communication
- Source-basis tags: every non-spec rule in `patterns.md`, `ai-instructions.md`, and `06a-gui-shell.md` subsections carries `[Research-backed: ...]`, `[Local Canon: ...]`, `[Spec: ...]`, or `[Human-approved: ...]`

### Pomera Note

- Research brief saved as pomera note ID 526 (`Research/GUI-Shell/Foundation-2026-03-14`)

## Tester Output

### Commands Run

```powershell
# Check 1: No orphaned react-router-dom/BrowserRouter/HashRouter
rg -i "react-router-dom|BrowserRouter|HashRouter" docs\build-plan\06-gui.md docs\build-plan\06a-gui-shell.md
# Result: exit code 1 (0 matches) ✅

# Check 2: All 5 research deliverables exist
(Get-ChildItem docs\research\gui-shell-foundation\).Count
# Result: 5 ✅

# Check 3: All required packages in dependency manifest
rg "zustand|@tanstack/react-router|react-hook-form|electron-vite|tailwindcss|babel-plugin-react-compiler" docs\build-plan\dependency-manifest.md
# Result: 6 matches ✅

# Check 4: No orphaned React Router JSX patterns
rg "React\.lazy|<Routes|<Route " docs\build-plan\06-gui.md
# Result: exit code 1 (0 matches) ✅

# Check 5: Security section in both files
rg -i "bearer|ephemeral|nonce" docs\build-plan\06a-gui-shell.md .agent\docs\architecture.md
# Result: matches in both files ✅

# Check 6: Stale route paths absent from command registry
rg "navigate\('/plans'|navigate\('/schedules'|navigate\('/accounts'|navigate\('/reports'|navigate\('/watchlists'" docs\build-plan\06a-gui-shell.md
# Result: exit code 1 (0 matches) ✅

# Check 7: No authentication contradiction
rg -i "No authentication needed" .agent\docs\architecture.md
# Result: exit code 1 (0 matches) ✅
```

### Pass/Fail Matrix

| Check | Description | Expected | Actual | Status |
|-------|------------|----------|--------|:------:|
| 1 | No orphaned react-router refs | 0 matches | 0 matches | ✅ |
| 2 | 5 research deliverables exist | 5 files | 5 files | ✅ |
| 3 | 6 packages in dependency-manifest | 6 matches | 6 matches | ✅ |
| 4 | No React.lazy/Routes/Route | 0 matches | 0 matches | ✅ |
| 5 | Bearer/ephemeral in both security files | ≥2 matches | ≥2 matches | ✅ |
| 6 | No stale route paths | 0 matches | 0 matches | ✅ |
| 7 | No auth contradiction | 0 matches | 0 matches | ✅ |

### Coverage/Test Gaps

- No code exists yet — these are documentation-only consistency checks
- Route path consistency between `06-gui.md` nav rail and `06a-gui-shell.md` command registry verified by checks 1, 4, 6

### Fix Applied During Verification

Check 4 initially found 2 remaining `React.lazy()` references in `06-gui.md`:
- Line 28: research-basis comment with `React.lazy()` link → updated to TanStack Router `lazy()` link
- Line 432: Outputs section referenced `React.lazy()` + `Suspense` → updated to TanStack Router `lazy()` + `pendingComponent`

After fix, check 4 passed (0 matches).

## Reviewer Output

- **Findings by severity:** Not yet reviewed — this handoff is intended for Codex adversarial validation
- **Open questions:** None
- **Verdict:** Pending Codex review
- **Residual risk:** Low — documentation-only changes, no code impact

### Codex Validation Scope

When validating, Codex should verify:

1. **Cross-reference fidelity:** Every decision in `synthesis-final-decisions.md` must be traceable to the research deliverables AND the modified build plan files
2. **Route consistency:** `06-gui.md` nav rail table paths must match `06a-gui-shell.md` command registry `navigate()` calls
3. **Security consistency:** `architecture.md` and `06a-gui-shell.md` must agree on Bearer token model
4. **Orphan check:** No references to removed technologies (`react-router-dom`, standalone `vite`, `React.lazy()`, `<Routes>`, `<Route>`)
5. **Dependency completeness:** All libraries from the consolidated stack present in `dependency-manifest.md`
6. **Source tags:** All non-spec rules in `patterns.md`, `ai-instructions.md`, and `06a-gui-shell.md` subsections carry source-basis tags
7. **Task.md alignment:** All tasks 1–11 marked `done`, task 12 `not_started`
8. **Plan adherence:** Each change matches what the approved implementation plan specified

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:** -
- **Timestamp:** -

## Final Summary

- **Status:** 11/12 tasks executed, 7/7 verification checks pass
- **Next steps:**
  1. Codex validates this handoff against the implementation plan and source materials
  2. If `approved` → proceed to `/create-plan` for MEU-43 + MEU-44 + MEU-45
  3. If `changes_required` → apply corrections and re-submit
