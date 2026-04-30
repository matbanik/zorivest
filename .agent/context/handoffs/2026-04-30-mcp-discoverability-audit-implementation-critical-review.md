---
date: "2026-04-30"
review_mode: "handoff"
target_plan: "docs/execution/plans/2026-04-30-mcp-discoverability-audit/implementation-plan.md"
verdict: "approved"
findings_count: 0
template_version: "2.1"
requested_verbosity: "standard"
agent: "GPT-5.5 Codex"
---

# Critical Review: 2026-04-30-mcp-discoverability-audit

> **Review Mode**: `handoff`
> **Verdict**: `approved`

---

## Scope

**Target**: `.agent/context/handoffs/2026-04-30-mcp-discoverability-audit-handoff.md`
**Correlated Plan**: `docs/execution/plans/2026-04-30-mcp-discoverability-audit/`
**Review Type**: implementation handoff review
**Checklist Applied**: IR, DR, PR

Correlation rationale: the user provided the MEU-TD1 handoff path directly. Its frontmatter project slug matches `docs/execution/plans/2026-04-30-mcp-discoverability-audit/`. The project has one work handoff, so no multi-handoff expansion was required.

Reviewed artifacts:

- `.agent/context/handoffs/2026-04-30-mcp-discoverability-audit-handoff.md`
- `docs/execution/plans/2026-04-30-mcp-discoverability-audit/implementation-plan.md`
- `docs/execution/plans/2026-04-30-mcp-discoverability-audit/task.md`
- 13 compound MCP tool files under `mcp-server/src/compound/`
- `mcp-server/src/client-detection.ts`
- `.agent/docs/emerging-standards.md`
- `.agent/context/meu-registry.md`
- `docs/BUILD_PLAN.md`
- `docs/execution/metrics.md`
- `docs/execution/reflections/2026-04-30-mcp-discoverability-audit-reflection.md`
- Relevant canonical scheduling docs and runtime guardrails for policy approval behavior

---

## Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 1 | High | The delivered policy workflow still omits the GUI-only approval gate before pipeline execution. `zorivest_policy` tells agents to `create -> emulate -> run` and lists only backend availability as prerequisite, while server instructions tell agents to `create`, `emulate`, then `run dry_run:false`. Runtime behavior checks approval before any run and canonical docs state approval is GUI-only and not agent-callable. This leaves the original scheduling discoverability gap unresolved and actively teaches agents the wrong lifecycle. | `mcp-server/src/compound/policy-tool.ts:248`, `mcp-server/src/client-detection.ts:128`, `packages/core/src/zorivest_core/services/scheduling_service.py:300`, `packages/core/src/zorivest_core/services/pipeline_guardrails.py:121`, `docs/build-plan/05g-mcp-scheduling.md:125`, `docs/build-plan/06e-gui-scheduling.md:181` | Update both `zorivest_policy` and `getServerInstructions()` to state: policy execution requires GUI approval; agents cannot approve policies; unapproved or modified policies return an approval/re-approval error; updates reset approval. Re-run M7 validation and build/test checks. | open |
| 2 | Medium | The verification gate is too weak to catch the known approval-gate omission. The task says the policy description needs `create -> approve -> run`, but the validation command only greps for `lifecycle`, arrow, `policy_json`, and `pipeline://`, so the current broken `create -> emulate -> run` text passes. The policy compound tests assert routing only and do not inspect tool descriptions. | `docs/execution/plans/2026-04-30-mcp-discoverability-audit/task.md:19`, `docs/execution/plans/2026-04-30-mcp-discoverability-audit/implementation-plan.md:55`, `mcp-server/tests/compound/policy-tool.test.ts:44` | Add a targeted static check or test assertion for `approve`/`approval`/`GUI-only` in the policy tool description and server instructions. Keep the generic M7 marker count, but do not rely on it for domain-specific acceptance criteria. | open |
| 3 | Low | The handoff's changed-file summary is incomplete. It lists the compound descriptions, `client-detection.ts`, `emerging-standards.md`, and `meu-registry.md`, but the worktree and task table also show changes to `docs/BUILD_PLAN.md`, `docs/execution/metrics.md`, the reflection, known-issues context files, and generated `mcp-server/zorivest-tools.json`. This does not break runtime behavior, but it weakens auditability for cross-vendor review. | `.agent/context/handoffs/2026-04-30-mcp-discoverability-audit-handoff.md:16`, `docs/execution/plans/2026-04-30-mcp-discoverability-audit/task.md:34` | In the correction pass, update the work handoff or correction handoff with the full changed-file set and mark generated/session-context artifacts separately from product source. | open |

---

## Commands Executed

| Command | Result |
|---------|--------|
| `git status --short` | Worktree contains the claimed MCP files plus additional session/context/build artifacts. |
| `git diff --name-only` | Confirmed modified compound tool files, `client-detection.ts`, `emerging-standards.md`, registry/build-plan/metrics artifacts, and generated `mcp-server/zorivest-tools.json`. |
| `git diff -- mcp-server/src/compound mcp-server/src/client-detection.ts .agent/docs/emerging-standards.md .agent/context/meu-registry.md docs/BUILD_PLAN.md docs/execution/metrics.md ...` | Confirmed policy/server instruction text and status/metrics changes. |
| `rg -i "workflow:|prerequisite:|returns:|errors:" mcp-server/src/compound/ --count` | PASS: all 13 compound files have at least 3 marker matches. |
| `rg -n 'approve|approved|approval|dry_run|run_pipeline' docs/build-plan mcp-server/src packages mcp-server/tests` | Found canonical approval requirements and confirmed new policy description/server instructions omit the GUI approval step. |
| `rg -n "TODO|FIXME|NotImplementedError" mcp-server/src/compound/` | PASS: no matches. |
| `cd mcp-server; npx tsc --noEmit` | PASS: exit code 0. |
| `cd mcp-server; npx vitest run` | PASS: 38 test files, 376 tests passed. |
| `cd mcp-server; npm run build` | PASS: generated 13 tools across 4 toolsets, exit code 0. |

Receipt files are under `C:\Temp\zorivest\review-*.txt`.

---

## Checklist Results

### Implementation Review (IR)

| Check | Result | Evidence |
|-------|--------|----------|
| IR-1 Live runtime evidence | N/A | Metadata-only MEU; no runtime handler changes. Fresh MCP regression suite passed: 376 tests. |
| IR-2 Stub behavioral compliance | N/A | No stub behavior changed. |
| IR-3 Error mapping completeness | N/A | No REST/API error mapping changed. Finding 1 covers metadata that misstates the approval error path. |
| IR-4 Fix generalization | FAIL | Scheduling approval was the documented worst-case gap, but the remediation missed the policy execution approval workflow in both policy tool metadata and server instructions. |
| IR-5 Test rigor audit | PARTIAL | Existing `policy-tool.test.ts` routing assertions are adequate for router behavior, but no test/static assertion checks the domain-specific description requirement. Generic marker grep passed while the approval prerequisite remained missing. |
| IR-6 Boundary validation coverage | N/A | No external input boundaries changed. |

### Docs Review (DR)

| Check | Result | Evidence |
|-------|--------|----------|
| DR-1 Claim-to-state match | FAIL | Task row 1 claims `create -> approve -> run`; delivered policy description says `create -> emulate -> run`. |
| DR-2 Residual old terms | PASS | No stale `9 MCP toolset descriptions` wording found in the updated BUILD_PLAN TD1 row; current issue text remains active because Finding 1 means the discoverability issue is not fully resolved. |
| DR-3 Downstream references updated | PARTIAL | BUILD_PLAN, registry, metrics, and reflection were updated, but handoff changed-file list does not include all artifacts. |
| DR-4 Verification robustness | FAIL | Marker/phrase grep would not catch the missed approval prerequisite. |
| DR-5 Evidence auditability | PARTIAL | Build/test/M7 evidence is reproducible; changed-file inventory is incomplete. |
| DR-6 Cross-reference integrity | FAIL | Runtime/canonical docs require GUI approval; new MCP metadata omits it. |
| DR-7 Evidence freshness | PASS | Fresh reviewer-run checks reproduced `tsc`, `vitest`, `build`, M7 marker count, and placeholder scan. |
| DR-8 Completion vs residual risk | FAIL | Handoff marks complete, but a core M7 known gap remains open. |

### Post-Implementation Review (PR)

| Check | Result | Evidence |
|-------|--------|----------|
| Evidence bundle complete | PARTIAL | Main command results present and reproduced, but handoff changed-file list is incomplete. |
| FAIL_TO_PASS table present | N/A | Human-approved metadata-only exception used grep/build/test evidence instead of red/green tests. |
| Commands independently runnable | PASS | Reviewer reran the relevant commands successfully with receipt files. |
| Anti-placeholder scan clean | PASS | `rg "TODO|FIXME|NotImplementedError" mcp-server/src/compound/` returned no matches. |

---

## Test Rigor Notes

Relevant tests reviewed:

- `mcp-server/tests/compound/policy-tool.test.ts` - Adequate for router URL/method behavior; weak for this MEU's metadata contract because it does not inspect `description`.
- `mcp-server/tests/tool-count-gate.test.ts` - Strong for 13-tool/4-toolset count behavior; not intended to validate M7 content.
- `mcp-server/tests/compound/system-tool.test.ts` count gate section - Strong for tool presence/removal assertions; not a discoverability-content test.

The human-approved TDD exception for metadata-only work is understandable, but the replacement grep criteria must assert domain-specific terms for known gaps. Generic M7 marker count is insufficient on its own.

---

## Verdict

`changes_required` - The TypeScript build and test evidence is clean, and most M7 marker enrichment is present. However, the highest-risk documented discoverability gap, policy execution approval, remains missing from both the policy tool description and server instructions. Agents would still be guided into an invalid `create -> run` workflow.

---

## Follow-Up Actions

1. Fix `zorivest_policy` description to include GUI-only approval and re-approval semantics before any run.
2. Fix `getServerInstructions()` Pipeline Automation workflow to include the required user GUI approval step and make clear agents cannot approve policies.
3. Strengthen validation for the policy workflow with an approval-specific static assertion or grep check.
4. Update review/correction evidence with the complete changed-file inventory, separating generated/session artifacts from source changes.
5. Re-run `npx tsc --noEmit`, `npx vitest run`, `npm run build`, M7 marker validation, and the new approval-specific check.

---

## Corrections Applied — 2026-04-30T20:22Z

**Agent:** Gemini (execution-corrections workflow)
**Findings actioned:** 3 verified, 2 resolved in this pass, 1 deferred

### Finding 1 (High) — RESOLVED

**Root cause:** Policy tool description and server instructions omitted the GUI-only approval gate that runtime guardrails enforce (`pipeline_guardrails.py:104-129`, `scheduling_service.py:300`).

**Corrections applied:**

1. **`policy-tool.ts:248-251`** — Updated workflow from `create → emulate → run` to `create → emulate → approve via GUI → run`. Added prerequisite text: "Policy must be approved via GUI before any run (agents cannot approve policies — approval is a human-in-the-loop security gate). Content updates reset approval — re-approval required after changes. Unapproved runs return an approval error."

2. **`client-detection.ts:126-134`** — Inserted step 6 in Pipeline Automation workflow: "**User approves policy via GUI** (agents cannot approve policies)". Renumbered subsequent steps (7→preview, 8→execute).

3. **`client-detection.ts:147`** — Updated tool index entry from "create, emulate, run" to "create, emulate, approve (GUI-only), run".

4. **`policy-tool.test.ts:105-115`** — Added new test "description includes GUI-only approval gate (M7/AC-2)" asserting `approve`, `GUI`, and `agents cannot` terms in the tool description.

### Finding 2 (Medium) — PARTIALLY RESOLVED

**Code-side fix:** Added approval-specific test assertion in `policy-tool.test.ts` (Fix 4 above). This test would have caught the original gap.

**Deferred to `/plan-corrections`:** `task.md:19` and `implementation-plan.md:52` validation commands need updating. These are forbidden writes for `/execution-corrections`.

### Finding 3 (Low) — RESOLVED

**`2026-04-30-mcp-discoverability-audit-handoff.md`** — Added missing changed-file entries: `docs/BUILD_PLAN.md`, `docs/execution/metrics.md`, reflection artifact, and session/context artifacts (known-issues, triage-report, zorivest-tools.json). Separated source changes from generated/session artifacts.

### Evidence Bundle (Fresh)

| Check | Result |
|-------|--------|
| `npx tsc --noEmit` | ✅ 0 errors |
| `npx vitest run` | ✅ 377 passed (+1 new), 38 test files |
| `npm run build` | ✅ 13 tools, 4 toolsets |
| M7 markers (all 13 files ≥3) | ✅ All pass |
| Anti-placeholder scan | ✅ 0 matches |
| Approval terms in `policy-tool.ts` | ✅ `approve`, `GUI`, `agents cannot` present |
| Approval step in `client-detection.ts` | ✅ Step 6 + tool index updated |

### Cross-Doc Sweep

Searched for old pattern (`create → emulate → run` without approval) across compound tools and server instructions:

```
rg -n -i "approve|approval|GUI" mcp-server/src/compound/policy-tool.ts
rg -n -i "approve|GUI.*cannot|agents cannot" mcp-server/src/client-detection.ts
```

Result: Both files now contain approval gate documentation. No sibling compound tools reference policy approval (expected — only `zorivest_policy` handles policy lifecycle).

### Changed Files (This Correction Pass)

| File | Change |
|------|--------|
| `mcp-server/src/compound/policy-tool.ts` | Workflow + prerequisite + approval semantics |
| `mcp-server/src/client-detection.ts` | Pipeline Automation step 6 + tool index |
| `mcp-server/tests/compound/policy-tool.test.ts` | +1 approval gate description test |
| `.agent/context/handoffs/2026-04-30-mcp-discoverability-audit-handoff.md` | Completed changed-file inventory |
| `.agent/context/handoffs/2026-04-30-mcp-discoverability-audit-implementation-critical-review.md` | This corrections log |

### Deferred Items

| Item | Reason | Route |
|------|--------|-------|
| Update `task.md:19` validation command to assert approval terms | `task.md` is a forbidden write for execution-corrections | `/plan-corrections` |
| Update `implementation-plan.md:52` AC-2 description to reflect approval gate | `implementation-plan.md` is a forbidden write for execution-corrections | `/plan-corrections` |

---

## Recheck (2026-04-30)

**Workflow**: `/execution-critical-review` recheck  
**Agent**: GPT-5.5 Codex

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|--------------|----------------|
| F1 High: policy workflow omitted GUI-only approval gate | open | Fixed |
| F2 Medium: verification gate too weak to catch approval omission | open | Fixed for implementation via targeted test |
| F3 Low: changed-file inventory incomplete | open | Fixed via correction log and expanded work handoff inventory |

### Confirmed Fixes

- `mcp-server/src/compound/policy-tool.ts:248` now documents `create -> emulate -> approve via GUI -> run`.
- `mcp-server/src/compound/policy-tool.ts:249` states that policies must be approved via GUI before any run.
- `mcp-server/src/compound/policy-tool.ts:250` states that agents cannot approve policies.
- `mcp-server/src/compound/policy-tool.ts:251` documents re-approval after content updates and the unapproved-run error path.
- `mcp-server/src/client-detection.ts:132` adds the required GUI approval step to Pipeline Automation.
- `mcp-server/src/client-detection.ts:147` updates the `zorivest_policy` summary to include `approve (GUI-only)`.
- `mcp-server/tests/compound/policy-tool.test.ts:106` adds a targeted description test asserting `approve`, `GUI`, and `agents cannot`.
- `.agent/context/handoffs/2026-04-30-mcp-discoverability-audit-handoff.md:62` now lists additional source/session/generated artifacts omitted from the original changed-file inventory.

### Commands Executed

| Command | Result |
|---------|--------|
| `git status --short` | Confirmed correction files include `policy-tool.ts`, `client-detection.ts`, `policy-tool.test.ts`, handoff artifacts, generated manifest, and existing session artifacts. |
| `git diff -- mcp-server/src/compound/policy-tool.ts mcp-server/src/client-detection.ts mcp-server/tests/compound/policy-tool.test.ts ...` | Confirmed the approval-gate text and targeted test changes. |
| `rg -n -i "approve|approval|GUI|agents cannot|re-approval|Unapproved" mcp-server/src/compound/policy-tool.ts mcp-server/src/client-detection.ts mcp-server/tests/compound/policy-tool.test.ts` | PASS: policy description, server instructions, and test all contain approval-gate terms. |
| `rg -n "create -> (optional: emulate to test) -> run|create -> emulate -> run|dry_run:false) ... execute pipeline" mcp-server/src/compound/policy-tool.ts mcp-server/src/client-detection.ts` | PASS: no stale no-approval workflow pattern found. |
| `rg -i "workflow:|prerequisite:|returns:|errors:" mcp-server/src/compound/ --count` | PASS: all 13 compound files have at least 3 marker matches. |
| `rg -n "TODO|FIXME|NotImplementedError" mcp-server/src/compound/` | PASS: no matches. |
| `cd mcp-server; npx tsc --noEmit` | PASS: exit code 0. |
| `cd mcp-server; npx vitest run` | PASS: 38 test files, 377 tests passed. |
| `cd mcp-server; npm run build` | PASS: generated 13 tools across 4 toolsets, exit code 0. |

Receipt files are under `C:\Temp\zorivest\recheck-*.txt`.

### Remaining Findings

None.

### Residual Risk

The original plan/task text still contains stale metadata-only validation wording, and the correction log routes that to `/plan-corrections` because those files were out of write scope for `/execution-corrections`. This is non-blocking for the implementation recheck because the source metadata and test coverage now enforce the approval-gate contract.

### Verdict

`approved` - All prior implementation-review findings are resolved or reduced to non-blocking plan hygiene outside execution-corrections write scope. Fresh TypeScript, Vitest, build, M7, approval-term, stale-pattern, and placeholder checks all pass.
