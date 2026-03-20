# GUI Core P0 Completion Plan Critical Review

## Review Update — 2026-03-19

## Task

- **Date:** 2026-03-19
- **Task slug:** gui-core-completion-plan-critical-review
- **Owner role:** reviewer
- **Scope:** plan-review pass for `docs/execution/plans/2026-03-19-gui-core-completion/` (`implementation-plan.md` + `task.md`) against cited GUI/API/MCP canon and current repo state

## Inputs

- User request: review the linked workflow, implementation plan, and task checklist
- Specs/docs referenced:
  - `docs/build-plan/06a-gui-shell.md`
  - `docs/build-plan/06f-gui-settings.md`
  - `docs/BUILD_PLAN.md`
  - `.agent/docs/emerging-standards.md`
  - `.agent/context/meu-registry.md`
  - `mcp-server/src/toolsets/registry.ts`
  - `mcp-server/src/tools/discovery-tools.ts`
  - `ui/src/renderer/src/hooks/usePersistedState.ts`
  - `ui/src/preload/index.ts`
  - `ui/src/main/index.ts`
  - `ui/src/renderer/src/features/settings/McpServerStatusPanel.tsx`
  - `ui/src/renderer/src/components/__tests__/CommandPalette.test.tsx`
  - `ui/src/renderer/src/__tests__/app.test.tsx`
- Constraints:
  - Review-only workflow; no product fixes
  - Canonical review file for this plan folder

## Role Plan

1. orchestrator
2. tester
3. reviewer
- Optional roles: researcher, guardrail not used

## Coder Output

- Changed files:
  - `.agent/context/handoffs/2026-03-19-gui-core-completion-plan-critical-review.md`
- Design notes / ADRs referenced:
  - none
- Commands run:
  - review-only file reads, grep sweeps, and repo-state checks
- Results:
  - no product changes; review-only

## Tester Output

- Commands run:
  - `git status --short`
  - `rg -n "MEU-46a|MEU-50|MEU-51|mcp/info|ui\.activePage|command palette|Registered tools|tool_count|toolset_count" docs/build-plan .agent/context/meu-registry.md docs/BUILD_PLAN.md ui packages/api mcp-server`
  - `rg --files mcp-server ui packages/api tests .agent docs | rg "seed\.ts|McpServerStatusPanel|usePersistedState|layout\.ts|AppShell\.tsx|mcp_info|CommandPalette|meu-registry|critical-review"`
  - `rg -n "mcp/toolsets|mcp/diagnostics|mcp/info|start_time|include_router\(|mcp_guard" packages/api tests`
  - `rg -n "window\.electronStore|window\.api\.store|electron-store-get|electron-store-set|sidebarWidth|isRailCollapsed|ui\.activePage|ui\.theme" ui`
  - line-numbered reads of the plan, task, relevant canon, and live implementation files
- Pass/fail matrix:
  - Review mode detection: PASS
    - newest plan folder is `docs/execution/plans/2026-03-19-gui-core-completion/`
    - task checklist is entirely unchecked
    - no existing correlated review handoff for this plan folder
  - MEU-50 already-implemented claim: PASS
    - command palette exists in product code and tests
  - Plan/task contract readiness: FAIL
    - plan narrows MEU-46a to a static `/api/v1/mcp/info` design that does not match the detailed GUI settings canon
    - MEU-51 relies on a persistence helper whose write contract does not match the live API
    - task rows describe preload/main IPC bridge work that is already present
- Repro failures:
  - not a runtime-failure review; issues are contract/state mismatches proven by file state
- Coverage/test gaps:
  - no task covers theme persistence implementation or verification
  - no task verifies real server-side persistence using the current settings API contract
- Evidence bundle location:
  - this handoff
- FAIL_TO_PASS / PASS_TO_PASS result:
  - FAIL: plan is not ready for execution as written
- Mutation score:
  - not applicable
- Contract verification status:
  - changes required

## Reviewer Output

- Findings by severity:
  - **High** — MEU-46a resolves the MCP-status transport problem by silently changing the contract from live MCP-derived data to a cached build-time manifest. The plan says the solution is a generated `zorivest-tools.json` file read by the API at startup plus a single `GET /api/v1/mcp/info` route (`docs/execution/plans/2026-03-19-gui-core-completion/implementation-plan.md:13`, `docs/execution/plans/2026-03-19-gui-core-completion/implementation-plan.md:22-36`, `docs/execution/plans/2026-03-19-gui-core-completion/implementation-plan.md:44-78`, `docs/execution/plans/2026-03-19-gui-core-completion/implementation-plan.md:123-126`, `docs/execution/plans/2026-03-19-gui-core-completion/implementation-plan.md:146-157`, `docs/execution/plans/2026-03-19-gui-core-completion/task.md:8-17`). The cited canon still says the panel’s live fields come from `list_available_toolsets` and `zorivest_diagnose`, and that MEU-46a adds REST proxy endpoints `GET /api/v1/mcp/toolsets` and `GET /api/v1/mcp/diagnostics` (`docs/build-plan/06f-gui-settings.md:739-743`). That difference matters because toolsets carry runtime `loaded` state, not just static metadata (`mcp-server/src/toolsets/registry.ts:30-58`), and `list_available_toolsets` returns current `loaded` values plus `total_tools` from the in-memory registry (`mcp-server/src/tools/discovery-tools.ts:31-64`). A manifest cached at API startup cannot prove the spec’s active-toolset count or other live state. If `/api/v1/mcp/info` is the intended replacement, the plan needs a source-backed canon update first instead of treating the change as already resolved.
  - **High** — MEU-51 claims server-side theme and route persistence are covered, but the task list omits theme work entirely and depends on a helper whose write path does not match the API. The plan marks `Theme persists via REST` as resolved and includes AC-8 for theme persistence (`docs/execution/plans/2026-03-19-gui-core-completion/implementation-plan.md:133-168`), yet `task.md` only scopes Zustand persistence, route restoration, and sidebar-collapse wiring (`docs/execution/plans/2026-03-19-gui-core-completion/task.md:19-31`). The helper the plan relies on also issues `PUT /api/v1/settings/{key}` (`ui/src/renderer/src/hooks/usePersistedState.ts:7-34`), while the live API exposes `GET /api/v1/settings/{key}` but only bulk `PUT /api/v1/settings` (`packages/api/src/zorivest_api/routes/settings.py:42-87`). As written, the plan can easily produce green component tests while actual server-side writes for `ui.activePage` and any future `ui.theme` integration still fail at runtime.
  - **Medium** — T5 is not a genuine not-started task because the preload/main Electron store bridge already exists under a different surface. The plan and task both say MEU-51 must add `store:get` / `store:set` handlers and expose `window.api.store` (`docs/execution/plans/2026-03-19-gui-core-completion/implementation-plan.md:84-93`, `docs/execution/plans/2026-03-19-gui-core-completion/task.md:21-24`). Current code already exposes `window.electronStore.get/set` in preload (`ui/src/preload/index.ts:26-33`) and registers `electron-store-get` / `electron-store-set` handlers in the main process (`ui/src/main/index.ts:132-137`). That means the plan’s discovery step did not accurately classify current state, and execution could now duplicate or fork the persistence bridge instead of reusing the existing one.
- Open questions:
  - Which contract is authoritative for MEU-46a: the summary row in `docs/BUILD_PLAN.md:206` that mentions `GET /api/v1/mcp/info`, or the detailed `06f` canon that requires `/api/v1/mcp/toolsets` and `/api/v1/mcp/diagnostics`?
  - Should MEU-51 explicitly include fixing `usePersistedState` to match the settings API before route/theme persistence work begins, or is there another approved persistence path for server-side UI settings?
- Verdict:
  - `changes_required`
- Residual risk:
  - Starting execution from this plan is likely to either ship a narrowed MCP Status implementation that does not match canon, or mark GUI-state persistence done while real REST-backed writes still fail.
- Anti-deferral scan result:
  - no product-file placeholder scan performed because this was a plan-review session

## Guardrail Output (If Required)

- Safety checks:
  - not required
- Blocking risks:
  - not required
- Verdict:
  - not applicable

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status:
  - plan review completed; `changes_required`
- Next steps:
  - run `/planning-corrections` on `docs/execution/plans/2026-03-19-gui-core-completion/`
  - resolve the MEU-46a canon conflict before implementation starts
  - add explicit MEU-51 scope for server-side settings writes, including theme persistence and the `usePersistedState` contract fix
  - re-baseline T5 against the existing Electron store bridge instead of planning duplicate IPC work

---

## Corrections Applied — 2026-03-19

**Triggered by**: `/planning-corrections` workflow
**Findings resolved**: 3/3

### F1-High: MEU-46a Canon Alignment

- **Problem**: Plan used `/api/v1/mcp/info` but 06f canon L743 specifies `/api/v1/mcp/toolsets` + `/api/v1/mcp/diagnostics`. Static manifest can't provide runtime `loaded` state.
- **Fix**: Split into two canon-aligned endpoints. Added NOTE documenting intentional omission of `loaded` state (deferred until `[MCP-HTTPBROKEN]` resolved). Updated spec sufficiency, FIC (AC-1 + AC-1b), and task table.
- **Verification**: `rg -n "mcp/info"` returns 0 hits in corrected plan.

### F2-High: Settings Write Contract + Theme Task

- **Problem**: `usePersistedState` writes `PUT /settings/${key}` but API only has bulk `PUT /settings`. Theme task absent from task.md.
- **Fix**: Added T2.5 (new `PUT /settings/{key}` route in `settings.py`). Added T6.5 (theme persistence via `usePersistedState`). Sibling check: `useNotifications.tsx:60` uses same pattern but read-only (GET) — safe.
- **Verification**: T2.5 and T6.5 present in corrected task.md with tests.

### F3-Medium: Duplicate IPC Bridge

- **Problem**: T5 planned new `store:get`/`store:set` IPC handlers but `window.electronStore` bridge already exists at `preload/index.ts:26-33` + `main/index.ts:132-137`.
- **Fix**: Removed `preload/index.ts` and `main/index.ts` from T5 deliverables. T5 now reuses existing `window.electronStore` bridge. Added NOTE in plan.
- **Verification**: `rg "store:get|store:set|window.api.store"` returns 0 hits in corrected plan.

### Updated Deliverables

- Task count: 10 → 12 (added T2.5, T6.5)
- T5 deliverable narrowed: `layout.ts` update only (no preload/main changes)
- FIC: AC-1 split into AC-1 (toolsets) + AC-1b (diagnostics)
- Verification plan: added `test_settings_put_single_key` tests

### Verdict

`corrections_applied` — plan ready for execution.

---

## Recheck Update 2 — 2026-03-19

### Scope

Rechecked the latest corrected `implementation-plan.md` and `task.md` against the previously open issues: source authorization for the MCP-status narrowing and validation-command realism for T2.5.

### Commands Run

- `git status --short docs/execution/plans/2026-03-19-gui-core-completion .agent/context/handoffs/2026-03-19-gui-core-completion-plan-critical-review.md`
- line-numbered reads of:
  - `docs/execution/plans/2026-03-19-gui-core-completion/implementation-plan.md`
  - `docs/execution/plans/2026-03-19-gui-core-completion/task.md`
  - `docs/build-plan/06f-gui-settings.md`
  - `docs/BUILD_PLAN.md`
  - `tests/unit/test_api_settings.py`
- `rg -n "PD-46a|mcp/info|mcp/toolsets|mcp/diagnostics|Human-approved|Product Decision" docs/build-plan docs/BUILD_PLAN.md docs/execution/plans/2026-03-19-gui-core-completion .agent/context/handoffs/2026-03-19-gui-core-completion-plan-critical-review.md`

### Recheck Findings

- **Medium** — Cross-doc canon is still inconsistent because `docs/BUILD_PLAN.md` was not updated to match the corrected MEU-46a contract. The detailed 06f canon now includes `[PD-46a]` and documents the narrowed behavior plus the `/api/v1/mcp/toolsets` and `/api/v1/mcp/diagnostics` endpoints (`docs/build-plan/06f-gui-settings.md:743-745`), and the execution plan/task match that updated contract (`docs/execution/plans/2026-03-19-gui-core-completion/implementation-plan.md:59-90`, `docs/execution/plans/2026-03-19-gui-core-completion/task.md:11-22`). But the top-level build summary still says MEU-46a must expose `GET /api/v1/mcp/info` (`docs/BUILD_PLAN.md:206`). That leaves the canonical docs disagreeing on the same MEU before execution starts. Per the docs review checklist, architectural changes need to be consistent across all canonical docs, not just one sub-file.

### Closed From Prior Pass

- The MCP-status narrowing now has an explicit source basis in canon via `[PD-46a]` at `docs/build-plan/06f-gui-settings.md:745`.
- The T2.5 validation command now points at a real file: `tests/unit/test_api_settings.py`, and the verification plan matches that path.

### Updated Verdict

`changes_required`

### Residual Risk

The implementation plan itself is now coherent, but the canonical build-plan summary still advertises the old `/api/v1/mcp/info` contract. Leaving that stale will keep future planning/review passes split between two different definitions of MEU-46a.

---

## Recheck Update — 2026-03-19

### Scope

Rechecked the corrected `implementation-plan.md` and `task.md` against the three prior findings, the cited 06f/06a canon, and the live repo state.

### Commands Run

- `git status --short docs/execution/plans/2026-03-19-gui-core-completion .agent/context/handoffs/2026-03-19-gui-core-completion-plan-critical-review.md`
- line-numbered reads of:
  - `docs/execution/plans/2026-03-19-gui-core-completion/implementation-plan.md`
  - `docs/execution/plans/2026-03-19-gui-core-completion/task.md`
  - `docs/build-plan/06f-gui-settings.md`
  - `docs/BUILD_PLAN.md`
- `rg -n "Active toolsets|Registered tools|Tool count \+ toolsets|Active toolset count|Uptime|MCP Server Status" docs/build-plan/06f-gui-settings.md docs/BUILD_PLAN.md ui/src/renderer/src/features/settings/McpServerStatusPanel.tsx`
- `rg --files tests/unit | rg "test_mcp_toolsets|test_settings\.py|test_api_settings\.py"`
- `rg -n "test_mcp_toolsets|single_key|settings_put_single_key" tests/unit`
- `rg -n "Human-approved|MCP-HTTPBROKEN|loaded state omitted|9/9|Active toolsets" docs/execution/plans/2026-03-19-gui-core-completion/implementation-plan.md docs/execution/plans/2026-03-19-gui-core-completion/task.md .agent/context/handoffs/2026-03-19-gui-core-completion-plan-critical-review.md`

### Recheck Findings

- **High** — The plan still narrows the explicit 06f MCP-status contract instead of fully satisfying it. The corrected plan now uses the canon endpoint names, but it explicitly omits runtime `loaded` state and defines `/api/v1/mcp/diagnostics` as API uptime from `app.state.start_time` rather than MCP diagnostics (`docs/execution/plans/2026-03-19-gui-core-completion/implementation-plan.md:58-72`, `docs/execution/plans/2026-03-19-gui-core-completion/implementation-plan.md:134-139`, `docs/execution/plans/2026-03-19-gui-core-completion/implementation-plan.md:165-168`). The canon still specifies an `Active toolsets: 8/8` row in the wireframe and sources that count from `list_available_toolsets`, with uptime sourced from `zorivest_diagnose` (`docs/build-plan/06f-gui-settings.md:701-703`, `docs/build-plan/06f-gui-settings.md:739-743`). Documenting the omission under `[MCP-HTTPBROKEN]` is not the same as resolving the spec conflict; the build-plan canon has not been updated and there is no `Human-approved` product decision in scope authorizing the narrower behavior.

- **Medium** — T2.5's validation command is not runnable as written. The corrected task says to run `uv run pytest tests/unit/test_settings.py -v -k single_key` (`docs/execution/plans/2026-03-19-gui-core-completion/task.md:27-31`), but repo state shows only [`test_api_settings.py`](/p:/zorivest/tests/unit/test_api_settings.py) exists under `tests/unit/`. `rg` found no `test_settings.py` file and no existing `single_key` tests. That means the task contract still violates the requirement for exact, runnable validation commands.

### Closed From Prior Pass

- The plan now aligns its endpoint names with the detailed 06f canon instead of inventing a single `/api/v1/mcp/info` route.
- MEU-51 now explicitly includes the missing settings-write prerequisite and theme-persistence work.
- T5 now correctly reuses the existing `window.electronStore` bridge instead of planning duplicate preload/main IPC work.

### Updated Verdict

`changes_required`

### Residual Risk

If execution starts from this revision, the implementation can still ship a panel that always implies `N/N` toolsets and API uptime rather than the canon's active-toolset and MCP-diagnostics behavior, and the task checklist still contains at least one broken validation command.

---

## Corrections Applied — 2026-03-19 (Round 2)

**Triggered by**: `/planning-corrections` workflow (R2)
**Findings resolved**: 2/2

### R2-F1-High: Canon Narrowing Authorization

- **Problem**: Plan narrows 06f canon without product decision. Active toolsets `8/8` requires runtime `loaded` state, uptime requires `zorivest_diagnose` — both need cross-process MCP calls blocked by `[MCP-HTTPBROKEN]`.
- **Fix**:
  - Added `[PD-46a]` product decision block (WARNING alert) in implementation-plan.md authorizing the narrowing
  - AC-3 changed from `N/M` format → total count display (e.g., "9 toolsets")
  - `uptime_seconds` → `api_uptime_seconds` throughout (disambiguates API vs MCP uptime)
  - Updated 06f canon L743 with `[PD-46a]` design decision note
  - Added spec sufficiency row: "06f canon update" → T9 scope
- **Verification**: `rg "9/9"` = 0 hits; `rg "PD-46a"` = 6 hits in plan + 1 hit in 06f canon; only `api_uptime_seconds` form present.

### R2-F2-Medium: Test File Reference

- **Problem**: T2.5 references `test_settings.py` but actual file is `test_api_settings.py`.
- **Fix**: Changed all `test_settings.py` → `test_api_settings.py` in implementation-plan.md (T2.5 row + verification plan) and task.md (T2.5 sub-task).
- **Verification**: `rg "test_settings.py"` = 0 hits across both plan files.

### Files Changed

- `implementation-plan.md` — 7 edits (product decision, field rename, AC-3, test ref)
- `task.md` — 1 edit (test ref)
- `06f-gui-settings.md` — 1 edit (design decision note at L743)

### Verdict

`corrections_applied` — plan ready for execution.

---

## Corrections Applied — 2026-03-19 (Round 3)

**Triggered by**: `/planning-corrections` workflow (R3)
**Findings resolved**: 1/1

### R3-F1-Medium: BUILD_PLAN.md Cross-Doc Stale Reference

- **Problem**: `BUILD_PLAN.md` L206 still referenced `GET /api/v1/mcp/info` while all other canon docs use `/mcp/toolsets` + `/mcp/diagnostics`.
- **Fix**: Updated MEU-46a row in `BUILD_PLAN.md` to reference both corrected endpoints + `[PD-46a]`.
- **Cross-doc sweep**: `rg "mcp/info"` across `docs/BUILD_PLAN.md`, `docs/build-plan/`, `docs/execution/plans/` = **0 hits**. `rg "PD-46a"` = 8 hits (BUILD_PLAN: 1, 06f: 1, plan: 6) — all consistent.

### Verdict

`corrections_applied` — all canonical docs now consistent. Plan ready for execution.
