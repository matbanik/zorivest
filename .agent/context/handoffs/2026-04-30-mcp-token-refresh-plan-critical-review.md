---
date: "2026-04-30"
review_mode: "plan"
target_plan: "docs/execution/plans/2026-04-30-mcp-token-refresh/implementation-plan.md"
verdict: "approved"
findings_count: 0
template_version: "2.1"
requested_verbosity: "standard"
agent: "GPT-5.5 Codex"
---

# Critical Review: 2026-04-30-mcp-token-refresh

> **Review Mode**: `plan`
> **Verdict**: `approved`

---

## Scope

**Target**: `docs/execution/plans/2026-04-30-mcp-token-refresh/implementation-plan.md`, `docs/execution/plans/2026-04-30-mcp-token-refresh/task.md`
**Review Type**: plan review
**Checklist Applied**: PR + DR, with source-traceability and validation-command checks

Auto-discovery confirmed this is an unstarted implementation plan:

- `.agent/context/handoffs/2026-04-30-mcp-token-refresh-handoff.md`: absent
- `docs/execution/reflections/2026-04-30-mcp-token-refresh-reflection.md`: absent
- `mcp-server/src/utils/token-refresh-manager.ts`: absent
- `mcp-server/tests/token-refresh-manager.test.ts`: absent
- `task.md` implementation rows remain unchecked

---

## Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 1 | High | The plan under-scopes source changes required by making `getAuthHeaders()` async. The plan lists `api-client.ts` and `index.ts` as source modifications, but current code calls `getAuthHeaders()` synchronously from `system-tool.ts`, `mcp-guard.ts`, and `diagnostics-tools.ts`. If the coder follows the plan literally, TypeScript either fails or those callers keep bypassing the refresh manager. | `implementation-plan.md:86-87`, `task.md:21-22`, `mcp-server/src/compound/system-tool.ts:27`, `mcp-server/src/compound/system-tool.ts:186`, `mcp-server/src/middleware/mcp-guard.ts:14`, `mcp-server/src/middleware/mcp-guard.ts:44`, `mcp-server/src/tools/diagnostics-tools.ts:14`, `mcp-server/src/tools/diagnostics-tools.ts:79` | Add the affected source files to the plan and task table. Specify whether `getAuthHeaders()` remains synchronous by hiding async refresh inside manager state, or every caller must `await` it. Add targeted tests for guard and diagnostics callers. | fixed |
| 2 | High | The validation plan does not behaviorally prove the auth integration points that can regress. AC-8 requires both `fetchApi()` and `fetchApiBinary()` to use the manager, and task 4 requires startup initialization from `index.ts`, but the task validates those changes with type-check only. TypeScript cannot prove that the Authorization header uses a fresh token, that `fetchApiBinary()` awaits the manager, or that startup initializes the singleton with the API key. | `implementation-plan.md:67`, `task.md:21-22`, `mcp-server/src/utils/api-client.ts:93`, `mcp-server/src/utils/api-client.ts:156`, `mcp-server/src/index.ts:73` | Add tests that mock the manager and assert `fetchApi()`, `fetchApiBinary()`, `guardCheck()`, diagnostics safe-fetch calls, and startup initialization use the refreshed token path. Keep `tsc` as a compile gate, not as the only proof. | fixed |
| 3 | Medium | Several task validation commands are not directly runnable as exact commands because escaped table pipes are present inside the inline command text. For example, task rows use `Get-Content ... \\| Select-Object`, which is not a PowerShell pipeline if copied literally. The planning contract requires exact runnable validation commands. | `task.md:19-23`, `task.md:25-26`, `task.md:36` | Rewrite command cells so the command artifact is exact. Use fenced command blocks below the table, command IDs, or `&#124;` for Markdown table rendering without adding a literal backslash to the command. | fixed |
| 4 | Medium | Research-backed criteria cite non-primary, non-specific sources. The plan uses `Research-backed` for promise coalescing and `.finally()` cleanup, but the only research reference is a generic note to Stack Overflow, Medium, and GitHub. The repository rules require source-backed criteria; when web research is used for technical claims, primary/current sources are required. | `implementation-plan.md:62`, `implementation-plan.md:78-79`, `implementation-plan.md:187` | Either relabel these criteria as Human-approved if `known-issues.md` is the actual authority, or replace the generic web note with precise primary/current references and document what behavior each source supports. | fixed |
| 5 | Medium | The docs update scope says to add a new `05-mcp-server.md` token-refresh section, but it does not require updating existing canonical snippets that still document `bootstrapAuth()` and synchronous `getAuthHeaders()`. Leaving those sections stale would make the build plan internally contradictory after implementation. | `implementation-plan.md:94`, `task.md:28`, `docs/build-plan/05-mcp-server.md:119`, `docs/build-plan/05-mcp-server.md:122`, `docs/build-plan/05-mcp-server.md:241`, `docs/build-plan/05-mcp-server.md:259`, `docs/build-plan/05-mcp-server.md:1015` | Expand the docs task to update or remove the old auth bootstrap snippets, guard example, and Outputs entry so canonical docs describe one auth model. | fixed |

---

## Checklist Results

### Plan Review (PR)

| Check | Result | Evidence |
|-------|--------|----------|
| PR-1 Plan/task alignment | fail | Scope mostly aligns, but source-file coverage diverges from current callers of `getAuthHeaders()` (`system-tool.ts`, `mcp-guard.ts`, `diagnostics-tools.ts`). |
| PR-2 Not-started confirmation | pass | Implementation handoff, reflection, token manager source, and token manager test files are absent; task rows are unchecked. |
| PR-3 Task contract completeness | pass | Every row has task, owner, deliverable, validation, and status. |
| PR-4 Validation realism | fail | Core auth integration paths are validated by `tsc` only, and task commands with escaped pipes are not exact runnable PowerShell commands. |
| PR-5 Source-backed planning | fail | `Research-backed` rows cite generic secondary sources rather than precise primary/current sources. |
| PR-6 Handoff/corrections readiness | pass | Handoff/reflection/metrics rows are present; fixes should route through `/plan-corrections`. |

### Docs Review (DR)

| Check | Result | Evidence |
|-------|--------|----------|
| DR-1 Claim-to-state match | pass | Plan accurately identifies current `api-client.ts` as containing `authState`, `bootstrapAuth()`, and `expiresAt`. |
| DR-2 Residual old terms | fail | `05-mcp-server.md` still has canonical `bootstrapAuth()` and synchronous `getAuthHeaders()` snippets that the plan does not require updating. |
| DR-3 Downstream references updated | fail | Outputs entry still lists Auth bootstrap as `bootstrapAuth()`, `getAuthHeaders()`. |
| DR-4 Verification robustness | fail | Existing verification would not catch stale docs or missing async caller updates until broad compile/runtime failures. |
| DR-5 Evidence auditability | pass | Planned receipts use `C:\Temp\zorivest\`; command copyability needs correction per Finding 3. |
| DR-6 Cross-reference integrity | fail | Current source and docs show more auth touchpoints than the plan covers. |
| DR-7 Evidence freshness | pass | Review reproduced path and grep checks on 2026-04-30. |
| DR-8 Completion vs residual risk | pass | Plan is still draft/unstarted and does not claim implementation complete. |

---

## Commands Executed

```powershell
Test-Path .agent/context/handoffs/2026-04-30-mcp-token-refresh-plan-critical-review.md *> C:\Temp\zorivest\review-path.txt
git status --short *> C:\Temp\zorivest\git-status-plan-review.txt
rg -n "bootstrapAuth|getAuthHeaders|fetchApiBinary|getValidAccessToken|auth/unlock|expiresAt" mcp-server/src mcp-server/tests docs/execution/plans/2026-04-30-mcp-token-refresh *> C:\Temp\zorivest\mcp-token-review-rg.txt
rg -n "\\\\\||\| Select-Object|Research-backed|StackOverflow|stackoverflow|medium.com|github.com|token-refresh-manager.test|fetchApiBinary|index.ts|bootstrapAuth" docs/execution/plans/2026-04-30-mcp-token-refresh *> C:\Temp\zorivest\plan-sweep.txt
rg -n "bootstrapAuth|getAuthHeaders|Auth bootstrap|Session token|expires_in" docs/build-plan/05-mcp-server.md docs/build-plan/04c-api-auth.md *> C:\Temp\zorivest\canon-auth-rg.txt
Test-Path .agent/context/handoffs/2026-04-30-mcp-token-refresh-handoff.md *> C:\Temp\zorivest\impl-handoff-path.txt
Test-Path docs/execution/reflections/2026-04-30-mcp-token-refresh-reflection.md *> C:\Temp\zorivest\reflection-path.txt
Test-Path mcp-server/src/utils/token-refresh-manager.ts *> C:\Temp\zorivest\trm-source-path.txt
Test-Path mcp-server/tests/token-refresh-manager.test.ts *> C:\Temp\zorivest\trm-test-path.txt
```

---

## Verdict

`changes_required` — the plan identifies the right problem and a reasonable architecture, but it is not execution-ready. The main blocker is that the planned async auth-header change is narrower than the current source graph, and the tests do not prove the runtime auth paths most likely to regress.

---

## Required Follow-Up Actions

1. Use `/plan-corrections` to expand the source scope to every current `getAuthHeaders()` caller or explicitly preserve a synchronous API.
2. Add behavioral tests for `fetchApi()`, `fetchApiBinary()`, guard/diagnostics auth headers, and startup manager initialization.
3. Fix task command copyability so validation cells are exact runnable commands.
4. Replace generic research references with precise authority or relabel as Human-approved where `known-issues.md` is the real source.
5. Expand the docs task to update existing `05-mcp-server.md` auth snippets and Outputs references, not only add a new section.

---

## Corrections Applied — 2026-04-30

> **Agent**: Gemini (Antigravity)
> **Verdict**: `corrections_applied`

All 5 findings verified against live file state, confirmed, and resolved.

### Changes Made

| Finding | Severity | Resolution | Files Changed |
|---------|----------|------------|---------------|
| F1 — Under-scoped callers | High | Added `system-tool.ts`, `mcp-guard.ts`, `diagnostics-tools.ts` to Files Modified table; added new task row #5 for updating callers; added to Research References | `implementation-plan.md`, `task.md` |
| F2 — Missing integration tests | High | Added AC-10 (integration proof with sentinel token mock); added task row #6 for AC-10 tests; task 4 validation now references V5 (behavioral) not just tsc | `implementation-plan.md`, `task.md` |
| F3 — Escaped pipes in commands | Medium | Moved all validation commands out of table cells into a separate "Validation Commands" section with V1-V14 IDs; table cells now reference IDs ("See V1 below") | `task.md` (full rewrite) |
| F4 — Research-backed labels | Medium | Relabeled AC-3 source to `Human-approved (promise coalescing mandated by architecture decision)`; spec sufficiency table entries relabeled to `Human-approved` with full known-issues.md citation; generic web references removed from Research References | `implementation-plan.md` |
| F5 — Stale doc snippets | Medium | Expanded task 12 to include updating stale `bootstrapAuth()`/`getAuthHeaders()` snippets at L119,122,241,259,1015; added V10 validation command; plan Files Modified entry for `05-mcp-server.md` updated | `implementation-plan.md`, `task.md` |

### Verification Evidence

- **F1**: `rg -c "system-tool.ts|mcp-guard.ts|diagnostics-tools.ts" implementation-plan.md` → 7 matches
- **F2**: `rg -c "AC-10" implementation-plan.md` → 3 matches
- **F3**: `rg "\\\|" task.md` → 0 matches (no escaped pipes remain in task cells)
- **F4**: `rg "Research-backed" implementation-plan.md` → 0 matches
- **F5**: `rg "L119|L241|L1015" implementation-plan.md task.md` → 3 matches (both plan and task reference stale lines)
- **Cross-doc sweep**: 1 file checked (review file itself), 0 stale references found outside review context

---

## Recheck (2026-04-30)

**Workflow**: `/plan-critical-review` recheck
**Agent**: GPT-5.5 Codex

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|-------------|----------------|
| F1: Plan under-scopes async `getAuthHeaders()` callers | open | Fixed |
| F2: Auth integration paths validated by type-check only | open | Fixed |
| F3: Task validation commands contain escaped pipes | open | Fixed |
| F4: Research-backed criteria cite non-primary, non-specific sources | open | Fixed |
| F5: Existing `05-mcp-server.md` auth snippets not in docs update scope | open | Fixed |

### Confirmed Fixes

- **F1 fixed**: The plan now lists the direct `getAuthHeaders()` callers as modified files: `system-tool.ts`, `mcp-guard.ts`, and `diagnostics-tools.ts` (`implementation-plan.md:89-91`), and the task table adds a dedicated source-update row (`task.md:23`).
- **F2 fixed**: AC-10 now requires behavioral proof for `fetchApi()`, `fetchApiBinary()`, guard checks, diagnostics safe-fetch, and startup initialization using a sentinel token from `TokenRefreshManager.getValidAccessToken()` (`implementation-plan.md:69`). The task table adds AC-10 integration tests and V5 validation (`task.md:24`, `task.md:57`).
- **F3 fixed**: Validation commands were moved into a separate `Validation Commands` section and the table references V1-V14 IDs (`task.md:41-87`). Recheck grep found 0 literal escaped pipe matches.
- **F4 fixed**: The plan no longer uses `Research-backed` labels or generic Stack Overflow/Medium/GitHub references; promise coalescing and failure cleanup are now sourced to the human-approved `known-issues.md [MCP-AUTHRACE]` contract (`implementation-plan.md:62`, `implementation-plan.md:78-79`, `implementation-plan.md:187`).
- **F5 fixed**: The docs scope now explicitly requires updating stale `bootstrapAuth()` / `getAuthHeaders()` snippets in `05-mcp-server.md` at L119, L122, L241, L259, and L1015 (`implementation-plan.md:95`, `task.md:30`).

### Commands Executed

```powershell
rg -n "system-tool.ts|mcp-guard.ts|diagnostics-tools.ts|AC-10|sentinel|fetchApiBinary|index.ts" docs/execution/plans/2026-04-30-mcp-token-refresh/implementation-plan.md docs/execution/plans/2026-04-30-mcp-token-refresh/task.md *> C:\Temp\zorivest\recheck-scope.txt
rg -n '\\\|' docs/execution/plans/2026-04-30-mcp-token-refresh/task.md *> C:\Temp\zorivest\recheck-escaped-pipes.txt
rg -n "Research-backed|stackoverflow|medium.com|github.com" docs/execution/plans/2026-04-30-mcp-token-refresh/implementation-plan.md *> C:\Temp\zorivest\recheck-research.txt
rg -n "bootstrapAuth\(\)|getAuthHeaders\(\): Record|L119|L122|L241|L259|L1015|Token Refresh Infrastructure" docs/execution/plans/2026-04-30-mcp-token-refresh/implementation-plan.md docs/execution/plans/2026-04-30-mcp-token-refresh/task.md *> C:\Temp\zorivest\recheck-stale-doc-scope.txt
git status --short *> C:\Temp\zorivest\recheck-git-status.txt
& { Test-Path .agent/context/handoffs/2026-04-30-mcp-token-refresh-handoff.md; Test-Path mcp-server/src/utils/token-refresh-manager.ts; Test-Path mcp-server/tests/token-refresh-manager.test.ts } *> C:\Temp\zorivest\recheck-started-state.txt
```

### Remaining Findings

None.

### Verdict

`approved` — all five prior plan-review findings are resolved. The plan is ready for implementation approval.
