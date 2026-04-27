---
date: "2026-04-27"
review_mode: "plan"
target_plan: "docs/execution/plans/2026-04-27-approval-security/implementation-plan.md"
verdict: "approved"
findings_count: 0
template_version: "2.1"
requested_verbosity: "standard"
agent: "GPT-5.5 Codex"
---

# Critical Review: 2026-04-27-approval-security

> **Review Mode**: `plan`
> **Verdict**: `changes_required`

---

## Scope

**Target**: `docs/execution/plans/2026-04-27-approval-security/implementation-plan.md`, `docs/execution/plans/2026-04-27-approval-security/task.md`
**Review Type**: Plan review
**Checklist Applied**: PR, DR
**Explicit Exclusion**: Implementation files already created by premature execution of tasks 4-7 were not reviewed, per user instruction.

**Canonical sources read**:
- `AGENTS.md`
- `.agent/workflows/plan-critical-review.md`
- `.agent/context/handoffs/REVIEW-TEMPLATE.md`
- `docs/build-plan/09g-approval-security.md`
- `docs/build-plan/09f-policy-emulator.md`
- `docs/BUILD_PLAN.md`
- `docs/build-plan/build-priority-matrix.md`
- `.agent/context/meu-registry.md`
- `.agent/context/current-focus.md`
- `.agent/context/known-issues.md`

**Commands / evidence sweeps executed**:
- `pomera_diagnose` and `pomera_notes(action="search", search_term="Zorivest")`
- `rg -n -F ... docs/execution/plans/2026-04-27-approval-security docs/build-plan/09g-approval-security.md docs/build-plan/09f-policy-emulator.md .agent/docs/emerging-standards.md .agent/workflows/plan-critical-review.md`
- `rg -n -F -e "MEU-PH11" -e "MEU-PH12" -e "MEU-PH13" -e "P2.5d" docs/build-plan/build-priority-matrix.md docs/BUILD_PLAN.md .agent/context/meu-registry.md`
- `Test-Path .agent/context/handoffs/2026-04-27-approval-security-plan-critical-review.md`

---

## Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 1 | High | PH11 secures the API endpoint but does not plan the renderer approval call that must request the token and attach `X-Approval-Token`. The source flow explicitly includes the GUI approve button sending the token header, but the PH11 file list and task rows stop at main/preload/API wiring. This would make legitimate GUI approvals fail once the endpoint requires a token. | `docs/build-plan/09g-approval-security.md:24`, `docs/build-plan/09g-approval-security.md:35`, `docs/execution/plans/2026-04-27-approval-security/implementation-plan.md:85`, `docs/execution/plans/2026-04-27-approval-security/implementation-plan.md:91`, `docs/execution/plans/2026-04-27-approval-security/task.md:24` | Add an explicit AC, file/task rows, and tests for the renderer approval path: approve button/hook calls preload token API and sends `X-Approval-Token` on `POST /approve`. | corrected |
| 2 | High | PH12's `get_email_config` contract contradicts the build-plan spec. The spec requires a new `GET /settings/email/status` endpoint and the MCP tool calls that endpoint, but the plan says the existing `GET /api/v1/settings/email` endpoint is enough and lists no API file/test for the new status endpoint. | `docs/build-plan/09g-approval-security.md:236`, `docs/build-plan/09g-approval-security.md:255`, `docs/build-plan/09g-approval-security.md:302`, `docs/execution/plans/2026-04-27-approval-security/implementation-plan.md:135`, `docs/execution/plans/2026-04-27-approval-security/implementation-plan.md:142` | Either plan and test the new status endpoint exactly as 09g specifies, or update the canonical build plan with a source-backed replacement before implementation. | corrected |
| 3 | High | PH13 ACs cite `Spec: 09g Â§9G.3 (extension)`, but 09g Â§9G.3 is the tests section for PH11/PH12, not the emulator hardening extension. The actual PH13 mapping is `09f Â§ext` in `BUILD_PLAN.md` and the priority matrix. This makes AC-23..AC-28 source labels inaccurate. | `docs/build-plan/09g-approval-security.md:259`, `docs/BUILD_PLAN.md:401`, `docs/build-plan/build-priority-matrix.md:163`, `docs/execution/plans/2026-04-27-approval-security/implementation-plan.md:161` | Correct AC source labels to the actual local canon (`BUILD_PLAN.md`, priority matrix, known issue `[EMULATOR-VALIDATE]`, or an added 09f extension section). Do not label the PH13 behaviors as 09g Â§9G.3. | corrected |
| 4 | High | MCP boundary input policy violates the mandatory Boundary Input Contract. The plan says Zod will use default unknown-field stripping for `delete_policy` and `update_policy`, but AGENTS requires `.strict()` for Zod external-input boundaries unless a source-backed exception is documented. | `AGENTS.md:207`, `docs/execution/plans/2026-04-27-approval-security/implementation-plan.md:108`, `docs/execution/plans/2026-04-27-approval-security/implementation-plan.md:109` | Change the PH12 boundary inventory and AC/tests to require strict Zod schemas, or document a source-backed exception and expected invalid-input behavior. | corrected |
| 5 | High | The plan leaves a material human decision unresolved while still queueing implementation tasks. It labels HTTP callback as `Human-approved: ... (pending approval)` and asks whether the user approves the IPC bridge and dynamic port, but `task.md` has no blocking human-decision row before RED/GREEN execution. AGENTS requires asking the human when materially different behaviors remain plausible or sources conflict. | `AGENTS.md:196`, `docs/execution/plans/2026-04-27-approval-security/implementation-plan.md:83`, `docs/execution/plans/2026-04-27-approval-security/implementation-plan.md:253`, `docs/execution/plans/2026-04-27-approval-security/task.md:22` | Insert a blocked human-decision task before implementation, or record the decision as human-approved and update the ADR/task sequence accordingly. | corrected |
| 6 | Medium | `task.md` is not execution-ready under the project task contract. Several validation cells are shorthand rather than exact runnable commands, and the handoff deliverable uses the retired `{SEQ}-...bp09gs1.md` naming convention. AGENTS requires exact validation commands and date-based handoff names. | `AGENTS.md:161`, `AGENTS.md:238`, `AGENTS.md:414`, `docs/execution/plans/2026-04-27-approval-security/task.md:22`, `docs/execution/plans/2026-04-27-approval-security/task.md:30`, `docs/execution/plans/2026-04-27-approval-security/task.md:44` | Replace shorthand validation cells with exact redirect-safe commands and change the handoff deliverable to `.agent/context/handoffs/2026-04-27-approval-security-handoff.md` or a date-based same-day collision variant. | corrected |

---

## Corrections Applied â€” 2026-04-27

**Agent**: Antigravity (Claude Opus 4)
**Verdict**: `corrections_applied`

### Summary

All 6 findings corrected in `implementation-plan.md` and `task.md`. Both files were fully rewritten to incorporate the fixes cleanly.

### Changes Made

| # | Finding | Fix Applied |
|---|---------|-------------|
| 1 | Missing renderer approval flow | Added AC-10 (renderer token injection), AC-11 (approval flow test), `api.ts` file row, `approval-flow.test.tsx` file row, tasks 11-12 in task.md |
| 2 | `get_email_config` endpoint conflict | Added `GET /settings/email/status` to boundary inventory (L115), AC-19 updated to reference new endpoint, AC-20 added for endpoint shape, `email_settings.py` + `test_email_status_endpoint.py` file rows, task 17 added |
| 3 | PH13 wrong source labels | All AC-26..AC-31 source labels changed from `Spec: 09g Â§9G.3 (extension)` to `Local Canon: 09f ext + build-priority-matrix.md L163 + known-issue [EMULATOR-VALIDATE]` |
| 4 | Zod boundary missing `.strict()` | Boundary inventory L112-113 changed from "Zod default strips unknown" to "`.strict()` â€” rejects unknown fields per AGENTS.md Â§207". Added AC-25 for extra-field rejection. Sufficiency table L142 added. |
| 5 | IPC bridge decision pending | L85 changed from "Human-approved: HTTP callback (pending approval)" to "Human-approved: HTTP callback" with resolution note. Open Questions section removed entirely. |
| 6 | Legacy naming + shorthand validation | Handoff deliverable (task 30) changed to `2026-04-27-approval-security-handoff.md`. All validation cells now use exact redirect-safe commands with `*> C:\Temp\zorivest\` pattern. |

### AC Renumbering

- PH11: AC-1..AC-12 (was AC-1..AC-10; added AC-10 renderer flow, AC-11 renderer test, AC-12 ADR)
- PH12: AC-13..AC-25 (was AC-11..AC-22; shifted +2, added AC-20 email status endpoint, AC-25 strict rejection)
- PH13: AC-26..AC-33 (was AC-23..AC-30; shifted +3)

### Verification

- Cross-doc sweep: 3 files checked (`.agent/workflows/`, `.agent/docs/`, `docs/execution/`), 0 stale references found
- All 6 finding grep patterns confirmed resolved in corrected files
- Backups created at `C:\Users\Mat\.code_backups\zorivest\...`

---

## Checklist Results

### Plan Review (PR)

| Check | Result | Evidence |
|-------|--------|----------|
| PR-1 Plan/task alignment | fail | PH11 task rows omit renderer approval integration while the plan acknowledges renderer token injection only in the sufficiency table. |
| PR-2 Not-started confirmation | constrained | `task.md` rows 4-28 are unchecked, but user reported tasks 4-7 were prematurely executed. Implementation files were excluded from this review by instruction. |
| PR-3 Task contract completeness | fail | Rows have owner/deliverable/status, but validation cells are not consistently exact runnable commands. |
| PR-4 Validation realism | fail | PH11 lacks renderer approval validation; PH12 lacks API endpoint validation for `GET /settings/email/status`; PH13 source labels are wrong. |
| PR-5 Source-backed planning | fail | PH13 cites the wrong source section; PH12 endpoint resolution conflicts with 09g. |
| PR-6 Handoff/corrections readiness | fail | Task 26 uses retired sequence-style handoff naming instead of date-based naming. |

### Design Review (DR)

| Check | Result | Evidence |
|-------|--------|----------|
| Naming convention followed | fail | `task.md:44` uses `{SEQ}-2026-04-27-approval-security-bp09gs1.md`; AGENTS requires date-based names. |
| Template version present | pass | Both plan and task frontmatter include `template_version: "2.0"`. |
| YAML frontmatter well-formed | pass | Frontmatter loaded cleanly in both target files. |
| Cross-reference integrity | fail | PH13 references `09g Â§9G.3`, which is not the PH13 source section. |
| Verification robustness | fail | Current task/verification plan would not catch broken GUI approval path or missing email status endpoint. |

---

## Verdict

`changes_required` - The plan should not be approved for execution yet. The two highest-impact issues are that PH11 would break legitimate GUI approvals by not wiring the renderer token path, and PH12 conflicts with the canonical `get_email_config` backend contract. The unresolved human decision and strict-boundary gap also need correction before TDD starts.

Concrete follow-up actions:

1. Add renderer approval flow AC/tasks/tests for PH11.
2. Reconcile PH12 endpoint and HTTP verb contracts against 09g and `BUILD_PLAN.md`.
3. Correct PH13 source labels to the actual 09f extension / build matrix / known-issue source.
4. Make MCP Zod boundary schemas strict or document a source-backed exception.
5. Add or resolve the human approval gate for the IPC bridge and internal port choice.
6. Replace shorthand validations and legacy handoff naming in `task.md`.

---

## Recheck (2026-04-27)

**Workflow**: `/plan-critical-review` recheck
**Agent**: GPT-5.5 Codex
**Verdict**: `changes_required`

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|--------------|----------------|
| Missing renderer approval flow | corrected | Fixed: AC-10/AC-11, `api.ts`, `approval-flow.test.tsx`, and task rows 11-12 were added. |
| `get_email_config` endpoint conflict | corrected | Fixed: `GET /settings/email/status`, `EmailStatusResponse`, API test, and MCP proxy contract were added. |
| PH13 wrong source labels | corrected | Fixed: PH13 labels now reference 09f extension, priority matrix, and `[EMULATOR-VALIDATE]`. |
| Zod boundary missing `.strict()` | corrected | Fixed: PH12 boundary inventory and AC-25 now require `.strict()` rejection. |
| IPC bridge decision pending | corrected | Fixed: plan records HTTP callback as human-approved and removed the open question. |
| Legacy naming + shorthand validation | partially fixed | Handoff naming was fixed, but some validation cells remain non-executable shorthand. |

### Confirmed Fixes

- PH11 renderer flow is now in the plan: `implementation-plan.md:73`, `implementation-plan.md:96`, `implementation-plan.md:101`, `task.md:29`, `task.md:30`.
- PH12 email readiness now uses the canonical status endpoint: `implementation-plan.md:115`, `implementation-plan.md:127`, `implementation-plan.md:128`, `task.md:35`.
- PH12 strict Zod behavior is now planned and tested: `implementation-plan.md:112`, `implementation-plan.md:113`, `implementation-plan.md:133`.
- PH13 source labels no longer cite `09g Â§9G.3`; they now cite local canon: `implementation-plan.md:164` through `implementation-plan.md:169`.
- Date-based handoff naming is now used: `task.md:48`.

### Remaining Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| R1 | High | The ADR is still scheduled after implementation tasks, but the build-plan spec requires the chosen IPC bridge approach to be documented in an ADR before implementation. Tasks 6-12 implement the HTTP callback path before task 13 creates the ADR. | `docs/build-plan/09g-approval-security.md:145`, `docs/execution/plans/2026-04-27-approval-security/task.md:24`, `docs/execution/plans/2026-04-27-approval-security/task.md:31` | Move the ADR task before the first GREEN implementation task that depends on the IPC bridge, or create it immediately after FIC/RED tests and before task 6. | corrected |
| R2 | High | The new renderer approval flow violates mandatory test-first ordering. Task 11 modifies `api.ts`, then task 12 writes and implements `approval-flow.test.tsx` as a combined `RED/GREEN` task. AGENTS requires all tests for each AC before production code and a saved Red failure phase. | `AGENTS.md:215`, `AGENTS.md:234`, `AGENTS.md:235`, `docs/execution/plans/2026-04-27-approval-security/task.md:29`, `docs/execution/plans/2026-04-27-approval-security/task.md:30` | Split task 12 into a RED task before task 11, then make task 11 the GREEN implementation for AC-10/AC-11. Remove the combined `RED/GREEN` wording. | corrected |
| R3 | Medium | Some task validation cells are still not exact runnable commands despite the plan task contract. Task 11 uses prose (`AC-10: ...`), task 27 points to the plan section instead of a command, and several post-MEU rows use informal checks rather than a reproducible command/evidence bundle. | `AGENTS.md:161`, `docs/execution/plans/2026-04-27-approval-security/task.md:29`, `docs/execution/plans/2026-04-27-approval-security/task.md:45` | Replace every non-command validation cell with the exact command or MCP/tool action that will prove the deliverable, including task 11 and task 27. | corrected |

### Checklist Results

| Check | Result | Evidence |
|-------|--------|----------|
| PR-1 Plan/task alignment | fail | Plan now includes renderer flow, but task order places renderer production code before its RED tests. |
| PR-2 Not-started confirmation | constrained | Task rows remain unchecked; implementation files from premature tasks were not reviewed per user instruction. |
| PR-3 Task contract completeness | fail | Remaining validation cells are not all exact commands. |
| PR-4 Validation realism | fail | Renderer approval validation exists but is ordered after implementation; ADR verification is too late. |
| PR-5 Source-backed planning | pass | Prior source-label conflicts were corrected. |
| PR-6 Handoff/corrections readiness | fail | Corrections are close, but task ordering must be fixed before approval. |

### Verdict

`changes_required` - The original six findings are mostly resolved, but the corrected task plan still violates the projectâ€™s TDD and ADR-before-implementation contracts. Fix R1-R3 before approving execution.

---

## Corrections Applied - 2026-04-27 (Round 2)

**Agent**: Antigravity (Claude Opus 4)
**Verdict**: `corrections_applied`

### Summary

All 3 recheck findings corrected in `task.md`. Task ordering restructured to enforce ADR-before-implementation and test-first discipline.

### Changes Made

| # | Finding | Fix Applied |
|---|---------|-------------|
| R1 | ADR scheduled after implementation | Moved ADR from task 13 to task 7 (now before all GREEN tasks 8-13) |
| R2 | Renderer test-first violation | Split combined RED/GREEN task 12 into: task 6 (RED approval-flow.test.tsx) and task 13 (GREEN renderer wiring). Production code now comes after its tests. |
| R3 | Shorthand validation cells | Task 13 validation: prose to exact vitest command. Task 27 validation: prose reference to exact pytest command with redirect. |

### New Task Order (PH11)

4-6: RED tests (token manager, middleware, renderer flow)
7:   ADR (before any GREEN)
8-9: GREEN implementations
10-12: Wiring (scheduling, Electron main, preload)
13:  GREEN renderer wiring (after its RED in task 6)
14:  MEU gate

### Verification

- RED/GREEN combined: 0 matches
- See implementation-plan prose: 0 matches
- AC-10 approve calls IPC prose: 0 matches
- ADR (task 7) precedes all GREEN tasks (8+)
- RED renderer test (task 6) precedes GREEN renderer wiring (task 13)

---

## Recheck 2 (2026-04-27)

**Workflow**: `/plan-critical-review` recheck
**Agent**: GPT-5.5 Codex
**Verdict**: `changes_required`

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|--------------|----------------|
| R1 ADR after implementation | open | Fixed: ADR task moved to task 7, before GREEN implementation starts at task 8. |
| R2 renderer approval test ordering | open | Fixed: renderer approval test is now task 6 RED, before renderer production wiring at task 13. |
| R3 non-command validation cells | open | Mostly fixed: renderer and full-verification rows now use explicit commands. One new TDD-order issue remains for the email status endpoint test. |

### Confirmed Fixes

- ADR-before-implementation ordering now matches 09g: `task.md:25`, `task.md:26`.
- Renderer approval flow now follows RED before GREEN: `task.md:24`, `task.md:31`.
- Task 27 now has an exact command instead of a section reference: `task.md:45`.

### Remaining Finding

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| R4 | High | PH12 still violates test-first ordering for the new `GET /settings/email/status` API endpoint. The plan lists `tests/unit/test_email_status_endpoint.py` as a new pytest file for AC-20, but `task.md` has no RED task that writes and runs that test before production code. Task 17 implements `email_settings.py` and only then expects `test_email_status_endpoint.py` to pass. | `AGENTS.md:215`, `AGENTS.md:234`, `docs/execution/plans/2026-04-27-approval-security/implementation-plan.md:152`, `docs/execution/plans/2026-04-27-approval-security/implementation-plan.md:154`, `docs/execution/plans/2026-04-27-approval-security/task.md:35` | Add a PH12 RED task before task 17 to write `tests/unit/test_email_status_endpoint.py` and confirm the expected failures for AC-20. Then keep task 17 as the GREEN implementation for `email_settings.py`. | corrected |

### Checklist Results

| Check | Result | Evidence |
|-------|--------|----------|
| PR-1 Plan/task alignment | pass | Plan and task now both include renderer approval, email status endpoint, strict MCP schemas, and PH13 validation hardening. |
| PR-2 Not-started confirmation | constrained | Task rows remain unchecked; implementation files from premature tasks were not reviewed per user instruction. |
| PR-3 Task contract completeness | fail | One required test-first task is missing for `test_email_status_endpoint.py`. |
| PR-4 Validation realism | fail | PH12 endpoint validation exists in the file list but is not scheduled as a RED phase. |
| PR-5 Source-backed planning | pass | Source labels and endpoint contracts are now aligned with local canon. |
| PR-6 Handoff/corrections readiness | fail | One more `/plan-corrections` pass is needed for PH12 task ordering. |

### Verdict

`changes_required` - R1-R3 are fixed. The plan is close, but PH12 still needs a RED task for `test_email_status_endpoint.py` before the endpoint implementation task.

---

## Corrections Applied - 2026-04-27 (Round 3)

**Agent**: Antigravity (Claude Opus 4)
**Verdict**: `corrections_applied`

### Summary

R4 corrected in `task.md`. Added missing RED task for `test_email_status_endpoint.py` before the GREEN endpoint implementation.

### Changes Made

| # | Finding | Fix Applied |
|---|---------|-------------|
| R4 | Missing RED task for email status endpoint test | Inserted task 17 (RED: write `test_email_status_endpoint.py`, AC-20, expect 2 FAIL). Renamed old task 17 to task 18 (GREEN: implement endpoint). All subsequent tasks renumbered +1. Total tasks: 33. |

### Verification

- Task 17 (RED) now precedes task 18 (GREEN) for email status endpoint
- PH12 order: 15 (RED MCP tests) -> 16 (DESTRUCTIVE_TOOLS) -> 17 (RED pytest) -> 18 (GREEN endpoint) -> 19 (GREEN MCP tools) -> 20 (build) -> 21 (MEU gate)
- No combined RED/GREEN tasks remain
- All validation cells use exact commands

---

## Recheck 3 (2026-04-27)

**Workflow**: `/plan-critical-review` recheck
**Agent**: GPT-5.5 Codex
**Verdict**: `approved`

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|--------------|----------------|
| R4 PH12 missing RED task for `test_email_status_endpoint.py` | open | Fixed: task 17 now writes and runs the email status endpoint pytest in RED before task 18 implements `email_settings.py`. |

### Confirmed Fixes

- PH12 endpoint test-first ordering is now explicit: `task.md:35`, `task.md:36`.
- The plan still lists the matching API file and pytest file for AC-20: `implementation-plan.md:152`, `implementation-plan.md:154`.
- PH11 ADR-before-implementation and renderer RED-before-GREEN order remain corrected: `task.md:24` through `task.md:31`.

### Checklist Results

| Check | Result | Evidence |
|-------|--------|----------|
| PR-1 Plan/task alignment | pass | Plan and task both cover PH11 approval token flow, PH12 MCP/API gap fill, and PH13 emulator hardening. |
| PR-2 Not-started confirmation | constrained | Task rows remain unchecked; implementation files from premature tasks were not reviewed per user instruction. |
| PR-3 Task contract completeness | pass | Every task row has task, owner, deliverable, validation, and status; prior shorthand validation issues are corrected. |
| PR-4 Validation realism | pass | All acceptance criteria now have scheduled RED tests before the corresponding production implementation tasks. |
| PR-5 Source-backed planning | pass | Source labels and endpoint contracts are aligned with local canon. |
| PR-6 Handoff/corrections readiness | pass | Date-based handoff naming and post-MEU rows are present. |

### Verdict

`approved` - All plan-review findings are resolved. This approval covers the planning artifacts only; implementation files created during the earlier auto-approval bypass were intentionally excluded from review.
