# Execution Handoff — GUI Shell Research Integration Implementation Critical Review

## Task

- **Date:** 2026-03-14
- **Task slug:** gui-shell-research-integration-implementation-critical-review
- **Owner role:** reviewer
- **Scope:** Critical implementation review of `.agent/context/handoffs/2026-03-14-gui-shell-research-integration-execution.md`, correlated plan folder `docs/execution/plans/2026-03-14-gui-shell-research-integration/`, and the actual `docs/build-plan/*` / research file state the handoff claims to have updated

## Inputs

- User request: Review the provided critical-review workflow and execution handoff
- Specs/docs referenced:
  - `.agent/workflows/critical-review-feedback.md`
  - `.agent/context/handoffs/2026-03-14-gui-shell-research-integration-execution.md`
  - `docs/execution/plans/2026-03-14-gui-shell-research-integration/implementation-plan.md`
  - `docs/execution/plans/2026-03-14-gui-shell-research-integration/task.md`
  - `docs/build-plan/06-gui.md`
  - `docs/build-plan/06a-gui-shell.md`
  - `docs/build-plan/dependency-manifest.md`
  - `.agent/docs/architecture.md`
  - `docs/research/gui-shell-foundation/{scope,patterns,ai-instructions,decision,style-guide-zorivest}.md`
  - `_inspiration/electron_react_python_research/{synthesis-final-decisions,synthesis-gui-shell-foundation}.md`
- Constraints:
  - Review-only workflow; no product fixes
  - Zorivest build-plan files required as live review scope
  - Findings-first verdict with evidence from current file state

## Role Plan

1. orchestrator
2. tester
3. reviewer
- Optional roles: researcher, guardrail

## Coder Output

- Changed files: No product changes; review-only
- Design notes / ADRs referenced: None added
- Commands run:
  - `git status --short -- docs/build-plan docs/research/gui-shell-foundation .agent/docs/architecture.md docs/execution/plans/2026-03-14-gui-shell-research-integration .agent/context/handoffs/2026-03-14-gui-shell-research-integration-execution.md`
  - `git diff -- docs/build-plan/06-gui.md docs/build-plan/06a-gui-shell.md docs/build-plan/dependency-manifest.md .agent/docs/architecture.md docs/research/gui-shell-foundation/scope.md docs/research/gui-shell-foundation/patterns.md docs/research/gui-shell-foundation/ai-instructions.md docs/research/gui-shell-foundation/decision.md docs/research/gui-shell-foundation/style-guide-zorivest.md docs/execution/plans/2026-03-14-gui-shell-research-integration/implementation-plan.md docs/execution/plans/2026-03-14-gui-shell-research-integration/task.md .agent/context/handoffs/2026-03-14-gui-shell-research-integration-execution.md`
  - `rg` sweeps for route drift, source-tag coverage, startup/splash wording, port/base-URL drift, and React Compiler contradictions
- Results:
  - Explicit handoff path correlated cleanly to plan folder by shared date/slug `2026-03-14-gui-shell-research-integration`
  - No prior canonical implementation review file existed for this target

## Tester Output

- Commands run:
  ```powershell
  rg -n "/watchlists|/plans|/schedules|/accounts|/reports" docs/build-plan/06a-gui-shell.md docs/build-plan/06-gui.md docs/research/gui-shell-foundation docs/execution/plans/2026-03-14-gui-shell-research-integration .agent/context/handoffs/2026-03-14-gui-shell-research-integration-execution.md
  rg -n "navigate\('/planning'|navigate\('/scheduling'|navigate\('/trades'|navigate\('/settings'" docs/build-plan/06a-gui-shell.md
  rg -n "navigate\(`/watchlists|navigate\('/watchlists|useMemo|useCallback|React\.memo" docs/build-plan/06a-gui-shell.md docs/build-plan/06-gui.md
  rg -n "No full-screen splash/spinner|splash window|splash.html|show: false|show: true|ready-to-show|app shell is the splash screen" docs/build-plan/06-gui.md docs/build-plan/06a-gui-shell.md docs/research/gui-shell-foundation/scope.md
  rg -n "localhost:8000|localhost:8765|dynamic port|dynamic_port|__ZORIVEST_API_URL__|net\.createServer\(0\)|127\.0\.0\.1:\$\{this\.port\}" docs/build-plan/06a-gui-shell.md docs/research/gui-shell-foundation/scope.md docs/research/gui-shell-foundation/patterns.md docs/research/gui-shell-foundation/ai-instructions.md .agent/docs/architecture.md
  rg -n "Research-backed|Local Canon|Spec|Human-approved" docs/research/gui-shell-foundation/patterns.md docs/research/gui-shell-foundation/ai-instructions.md docs/build-plan/06a-gui-shell.md
  ```
- Pass/fail matrix:
  - Route-reconciliation claim: **FAIL**. Exact Task 9 validation only finds `/trades`, `/planning`, `/scheduling`; no root `navigate('/settings')`. A stale template-string route remains at `docs/build-plan/06a-gui-shell.md:261`.
  - Zustand propagation: **FAIL**. Old `SettingModel`/REST sidebar-width contract remains alongside new Zustand/electron-store contract.
  - Startup/splash propagation: **FAIL**. `docs/build-plan/06-gui.md` still documents the old shell-first startup narrative while `docs/build-plan/06a-gui-shell.md` now requires a separate splash window.
  - API base URL/port propagation: **FAIL**. Dynamic-port research docs conflict with `localhost:8000` and `localhost:8765` examples.
  - Source-basis tagging completeness: **FAIL**. Untagged guidance remains in `docs/research/gui-shell-foundation/ai-instructions.md` and `docs/build-plan/06a-gui-shell.md`.
  - Pomera note claim: **PASS**. `pomera_notes.get(note_id=526)` returned `Research/GUI-Shell/Foundation-2026-03-14`.
- Repro failures:
  - `task.md:99-102` validation is not reproducible from current file state
  - Handoff Check 6 grep at `.agent/context/handoffs/2026-03-14-gui-shell-research-integration-execution.md:92-94` misses template-string routes and therefore gives false confidence
- Coverage/test gaps:
  - Review was documentation-only; no runtime/UI scaffold exists yet
  - Cross-plan propagation outside the immediate GUI shell docs was spot-checked, not exhaustively normalized across all future Phase 5/6/7 docs
- Evidence bundle location:
  - This file + terminal command history in this session
- FAIL_TO_PASS / PASS_TO_PASS result:
  - Not applicable; review-only
- Mutation score:
  - Not applicable
- Contract verification status:
  - **changes_required**

## Reviewer Output

- Findings by severity:
  - **High** — The route-reconciliation completion claim is false. `task.md:99-102` requires four canonical route hits including `navigate('/settings')`, but `docs/build-plan/06a-gui-shell.md:212-214` only provides `/trades`, `/planning`, and `/scheduling`, while settings is only exposed as subroutes at `docs/build-plan/06a-gui-shell.md:221-227`. On top of that, a stale watchlist route still exists at `docs/build-plan/06a-gui-shell.md:261`. The handoff states those stale paths were removed at `.agent/context/handoffs/2026-03-14-gui-shell-research-integration-execution.md:53`, and Check 6 reports success at `.agent/context/handoffs/2026-03-14-gui-shell-research-integration-execution.md:92-94`, but that grep only searches single-quoted `navigate('...')` calls and never inspects the remaining template-string route.
  - **High** — Zustand adoption was not propagated through the existing GUI shell contract. `docs/build-plan/06a-gui-shell.md:91` and `docs/build-plan/06a-gui-shell.md:165` still specify sidebar width as `SettingModel`/REST state under `ui.sidebar.width`, while the new Zustand section says sidebar drag width is client-only and persisted via electron-store at `docs/build-plan/06a-gui-shell.md:440-446`, with outputs reinforcing the Zustand path at `docs/build-plan/06a-gui-shell.md:532`. Those are mutually incompatible implementation directions.
  - **Medium** — The startup contract is now internally inconsistent. `docs/build-plan/06-gui.md:36-50` still walks through the old hidden-main-window `ready-to-show` flow, and `docs/build-plan/06-gui.md:115` still says "the app shell is the splash screen", but `docs/build-plan/06a-gui-shell.md:409-415` and `docs/build-plan/06a-gui-shell.md:513` now require a separate `splash.html` window that appears before the main UI.
  - **Medium** — The integrated docs do not agree on the UI→API connection contract. The new research docs repeat a dynamic-port design at `docs/research/gui-shell-foundation/scope.md:23`, `docs/research/gui-shell-foundation/scope.md:56`, `docs/research/gui-shell-foundation/patterns.md:82`, and `docs/research/gui-shell-foundation/ai-instructions.md:174-209`, but canonical docs still claim `localhost:8000` at `.agent/docs/architecture.md:25` and `.agent/docs/architecture.md:68`, while `docs/build-plan/06a-gui-shell.md:125` still hardcodes `http://localhost:8765/api/v1`. The review assumes the new research docs reflect intended behavior because multiple new artifacts repeat that contract; if not, the research deliverables themselves need correction.
  - **Medium** — The React Compiler rule was added as policy but not propagated through existing examples. `docs/build-plan/06a-gui-shell.md:457-459` says not to write manual `useMemo`/`useCallback`, yet the same file still prescribes `useCallback` in `usePersistedState` at `docs/build-plan/06a-gui-shell.md:123` and `docs/build-plan/06a-gui-shell.md:147`, plus `useMemo` in `CommandPalette` at `docs/build-plan/06a-gui-shell.md:297` and `docs/build-plan/06a-gui-shell.md:309-317`. `docs/build-plan/06-gui.md:350` and `docs/build-plan/06-gui.md:362` still show `useCallback` in the account-context example as well.
  - **Medium** — The source-basis tagging claim is overstated. The handoff says every non-spec rule is tagged at `.agent/context/handoffs/2026-03-14-gui-shell-research-integration-execution.md:61`, and `docs/research/gui-shell-foundation/ai-instructions.md:4` repeats that promise, but `docs/research/gui-shell-foundation/ai-instructions.md:431-452` contains untagged guidance sections (`Implementation Notes`, `Content MEU Guidance`, `Cognitive Load Protocol`). `docs/build-plan/06a-gui-shell.md:501-507` also adds an untagged `Design System Reference` section.
  - **Low** — `docs/build-plan/dependency-manifest.md` was only partially normalized. The install commands were expanded at `docs/build-plan/dependency-manifest.md:48-65`, but the Phase 6 summary row at `docs/build-plan/dependency-manifest.md:99` still lists the older, smaller stack and omits the newly adopted router/state/forms/build dependencies.
- Open questions:
  - Is the canonical GUI connection contract now dynamic port, or should the new research deliverables be revised back to a fixed port?
  - Should the command palette expose a root `Settings` navigation command, or is settings-only subroute navigation the intended UX? Either answer requires the task validation and handoff wording to be updated.
- Verdict:
  - **changes_required**
- Residual risk:
  - If corrected narrowly, there is still follow-up risk across adjacent GUI/MCP/distribution docs that currently assume fixed localhost ports.
- Anti-deferral scan result:
  - No product changes made during review. Findings require follow-up via the corrections workflow, not silent approval.

## Guardrail Output (If Required)

- Safety checks: Not required for docs-only review
- Blocking risks: None beyond the documentation contract drift listed above
- Verdict: Not applicable

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status:
  - Canonical implementation critical review created
  - Verdict: `changes_required`
- Next steps:
  - Patch the route reconciliation and validation evidence first
  - Resolve the sidebar-width/Zustand contract conflict
  - Choose and normalize one startup/API-port contract across the touched docs
  - Re-run the review against the same canonical file after corrections

## Recheck Update — 2026-03-14

### Scope Reviewed

- Rechecked the same implementation target after documentation corrections
- Focused on the prior findings in:
  - `docs/build-plan/06-gui.md`
  - `docs/build-plan/06a-gui-shell.md`
  - `docs/build-plan/dependency-manifest.md`
  - `.agent/docs/architecture.md`
  - `docs/research/gui-shell-foundation/ai-instructions.md`
  - `docs/execution/plans/2026-03-14-gui-shell-research-integration/task.md`
  - `.agent/context/handoffs/2026-03-14-gui-shell-research-integration-execution.md`

### Commands Executed

```powershell
rg -i "bearer|ephemeral|nonce" docs\build-plan\06a-gui-shell.md
rg "navigate\('/planning'|navigate\('/scheduling'|navigate\('/trades'|navigate\('/settings'" docs\build-plan\06a-gui-shell.md
rg "navigate\('/plans'|navigate\('/schedules'|navigate\('/accounts'|navigate\('/reports'|navigate\('/watchlists'" docs\build-plan\06a-gui-shell.md
rg -i "No authentication needed" .agent\docs\architecture.md
rg -n "ui\.sidebar\.width|Sidebar width|useMemo|useCallback|React\.memo|plan-critical-review|implementation-critical-review" docs\build-plan\06a-gui-shell.md docs\build-plan\06-gui.md docs\research\gui-shell-foundation\ai-instructions.md docs\execution\plans\2026-03-14-gui-shell-research-integration\task.md
Select-String -Path .agent\context\handoffs\2026-03-14-gui-shell-research-integration-plan-critical-review.md -Pattern "verdict"
```

### Recheck Findings

- **High** — The `NotificationProvider` example is now broken against the updated API contract. `docs/build-plan/06a-gui-shell.md:49-53` still calls `fetch(`${API}/settings`)`, but there is no `API` definition anywhere in the file after the dynamic-port/Bearer-token migration. The same file now points other examples to `apiFetch` and contextBridge-backed base URLs at `docs/build-plan/06a-gui-shell.md:122-151`, so this snippet would fail if implemented as written.
- **Medium** — The sidebar-width persistence contract is still internally inconsistent. `docs/build-plan/06a-gui-shell.md:85-91` now says sidebar width is stored via Zustand + electron-store, but `docs/build-plan/06a-gui-shell.md:155-168` still lists `ui.sidebar.width` under settings keys persisted in `SettingModel`. That leaves two contradictory storage locations for the same state.
- **Medium** — Task 12 still validates the wrong artifact. `docs/execution/plans/2026-03-14-gui-shell-research-integration/task.md:156-165` checks `.agent/context/handoffs/2026-03-14-gui-shell-research-integration-plan-critical-review.md` for a `verdict`, even though this phase requires the implementation-review artifact. That check already returns matches, so Task 12 could be marked complete without consulting the canonical implementation review file.

### Resolved Since Prior Pass

- Route reconciliation now includes root settings navigation at `docs/build-plan/06a-gui-shell.md:214`, and the stale watchlist route is gone in favor of `docs/build-plan/06a-gui-shell.md:261`.
- Startup/splash wording is aligned between `docs/build-plan/06-gui.md` and `docs/build-plan/06a-gui-shell.md`.
- Dynamic-port language is now propagated into `.agent/docs/architecture.md`.
- React Compiler examples no longer prescribe manual `useMemo` / `useCallback` in the touched snippets.
- Source-basis tags were added to the previously untagged sections in `docs/research/gui-shell-foundation/ai-instructions.md` and `docs/build-plan/06a-gui-shell.md`.
- The Phase 6 dependency summary row in `docs/build-plan/dependency-manifest.md` now reflects the expanded stack.

### Recheck Verdict

- **Verdict:** `changes_required`
- **Residual risk:** Narrowed. The earlier cross-doc drift is largely resolved, but the remaining broken snippet plus stale completion-validation path still make the implementation artifact set unsafe to approve.

## Recheck Update — 2026-03-14 (Pass 3)

### Scope Reviewed

- Rechecked the same implementation target after the latest corrections to:
  - `docs/build-plan/06a-gui-shell.md`
  - `docs/execution/plans/2026-03-14-gui-shell-research-integration/task.md`
  - `.agent/context/handoffs/2026-03-14-gui-shell-research-integration-execution.md`
  - `.agent/docs/architecture.md`

### Commands Executed

```powershell
rg -i "react-router|react-router-dom|BrowserRouter|HashRouter" docs\build-plan\06-gui.md docs\build-plan\06a-gui-shell.md
rg "React\.lazy|<Routes|<Route " docs\build-plan\06-gui.md
rg -i "bearer|ephemeral|nonce" docs\build-plan\06a-gui-shell.md .agent\docs\architecture.md
rg "navigate\('/plans'|navigate\('/schedules'|navigate\('/accounts'|navigate\('/reports'|navigate\('/watchlists'" docs\build-plan\06a-gui-shell.md
Select-String -Path .agent\context\handoffs\2026-03-14-gui-shell-research-integration-implementation-critical-review.md -Pattern "verdict"
```

### Recheck Findings

- **Medium** — Task 11 still contains a non-reproducible validation command. `docs/execution/plans/2026-03-14-gui-shell-research-integration/task.md:127-129` expects zero matches from `rg -i "react-router|react-router-dom|BrowserRouter|HashRouter"`, but the correct TanStack Router import at `docs/build-plan/06-gui.md:140` legitimately matches `react-router`. The execution handoff sidesteps that by running a narrower command at `.agent/context/handoffs/2026-03-14-gui-shell-research-integration-execution.md:72-74`, so the approved task validation and the recorded verification evidence are no longer aligned. As written, Task 11 cannot be reproduced cleanly from the task artifact.
- **Low** — The execution handoff is no longer a complete audit summary of the final corrected state. `.agent/context/handoffs/2026-03-14-gui-shell-research-integration-execution.md:53-54` still summarizes `06a-gui-shell.md` as reconciling only `/`, `/trades`, `/planning`, and `/scheduling`, and only mentions the line-68 security change in `architecture.md`, while the current final state also includes root settings navigation at `docs/build-plan/06a-gui-shell.md:210-214` and the dynamic-port diagram update at `.agent/docs/architecture.md:25`.

### Resolved Since Prior Pass

- The `NotificationProvider` example now uses `apiFetch` correctly at `docs/build-plan/06a-gui-shell.md:40-53`.
- The sidebar-width persistence contradiction is resolved; client-only state is now explicitly separated from `SettingModel` persistence at `docs/build-plan/06a-gui-shell.md:158`.
- Task 12 now validates the implementation review artifact, not the plan review artifact, at `docs/execution/plans/2026-03-14-gui-shell-research-integration/task.md:162-165`.
- The earlier route, startup, dynamic-port, source-tag, React Compiler example, and dependency-summary issues remain resolved in the live docs.

### Recheck Verdict

- **Verdict:** `changes_required`
- **Residual risk:** Narrowed to validation/auditability. I did not find any remaining live build-plan contract contradiction in the corrected docs, but the task checklist still contains a self-failing verification command, so the implementation artifact set is not yet cleanly auditable.

---

## Corrections Applied (Pass 3) — 2026-03-14T14:11 (Opus)

### Discovery

- **Canonical file:** scope override
- **Latest update:** Recheck (Pass 3) at lines 170-205, verdict: `changes_required`
- **Working set:** 2 findings (1 Medium, 1 Low)

### Verified Findings

| # | Severity | Finding | Verified? | Current Line | Category | Siblings |
|---|----------|---------|:---------:|:------------:|----------|----------|
| P3-1 | **Medium** | Task 11 Check 1 regex `react-router` too broad — matches `@tanstack/react-router` import at `06-gui.md:140` | ✅ | task.md:128 | overly-broad-validation | 0 |
| P3-2 | **Low** | Execution handoff lines 53-54 stale — missing settings nav, apiFetch, dynamic-port diagram, sidebar-width, source tags | ✅ | execution.md:53-54 | stale-audit-summary | 0 |

### Changes Made

| File | Edit |
|------|------|
| `docs/execution/plans/.../task.md` | P3-1: Narrowed Check 1 regex from `react-router\|react-router-dom\|...` to `react-router-dom\|BrowserRouter\|HashRouter` |
| `.agent/context/handoffs/...-execution.md` | P3-2: Updated 06a summary (line 53) to include: `nav:settings`, `apiFetch` migration, sidebar-width fix, React Compiler cleanup, source tags, watchlist route. Updated architecture.md summary (line 54) with dynamic-port diagram + Communication section |

### Verification Results

```powershell
# P3-1: Narrowed regex produces 0 matches
rg -i "react-router-dom|BrowserRouter|HashRouter" docs\build-plan\06-gui.md docs\build-plan\06a-gui-shell.md
# Result: exit code 1 (0 matches) ✅

# P3-2: Execution handoff mentions settings nav
rg "nav:settings" .agent\context\handoffs\2026-03-14-gui-shell-research-integration-execution.md
# Result: line 53 ✅

# Prior fixes still hold:
rg "fetch.*API" docs\build-plan\06a-gui-shell.md          # 0 matches ✅
rg "ui\.sidebar\.width" docs\build-plan\06a-gui-shell.md   # 0 matches ✅
```

### Cross-Doc Sweep

P3-1 category (overly-broad-validation): no other task.md command uses bare `react-router` without `-dom`.
P3-2 category (stale-audit-summary): execution handoff is the only audit summary for this project.

Cross-doc sweep: 3 files checked, 0 additional updates needed.

### Verdict

**All 2 Pass 3 findings resolved.** Ready for recheck.

## Recheck Update — 2026-03-14 (Pass 4)

### Scope Reviewed

- Rechecked the same implementation target after the Pass 3 corrections recorded above.
- Verified current state in:
  - `docs/execution/plans/2026-03-14-gui-shell-research-integration/task.md`
  - `.agent/context/handoffs/2026-03-14-gui-shell-research-integration-execution.md`
  - `docs/build-plan/06-gui.md`
  - `docs/build-plan/06a-gui-shell.md`
  - `.agent/docs/architecture.md`

### Commands Executed

```powershell
rg -i "react-router-dom|BrowserRouter|HashRouter" docs\build-plan\06-gui.md docs\build-plan\06a-gui-shell.md
(Get-ChildItem docs\research\gui-shell-foundation\).Count
rg "zustand|@tanstack/react-router|react-hook-form|electron-vite|tailwindcss|babel-plugin-react-compiler" docs\build-plan\dependency-manifest.md
rg "React\.lazy|<Routes|<Route " docs\build-plan\06-gui.md
rg -i "bearer|ephemeral|nonce" docs\build-plan\06a-gui-shell.md .agent\docs\architecture.md
rg "navigate\('/plans'|navigate\('/schedules'|navigate\('/accounts'|navigate\('/reports'|navigate\('/watchlists'" docs\build-plan\06a-gui-shell.md
rg -i "No authentication needed" .agent\docs\architecture.md
Get-ChildItem .agent\context\handoffs\ -Filter "*gui-shell-research-integration*"
Select-String -Path .agent\context\handoffs\2026-03-14-gui-shell-research-integration-implementation-critical-review.md -Pattern "verdict"
```

### Recheck Findings

- No remaining findings. The prior Task 11 validation defect is corrected at `docs/execution/plans/2026-03-14-gui-shell-research-integration/task.md:127-129`, the execution handoff summary is updated at `.agent/context/handoffs/2026-03-14-gui-shell-research-integration-execution.md:53-54`, and the current Task 11 / Task 12 validation set reproduces cleanly from live file state.

### Recheck Verdict

- **Verdict:** `approved`
- **Residual risk:** Low. This remains a documentation-only review; there is still no runtime GUI scaffold to execute, so approval here covers documentation accuracy and verification auditability only.
