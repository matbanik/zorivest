---
date: "2026-05-05"
review_mode: "plan"
target_plan: "docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md"
verdict: "approved"
findings_count: 0
template_version: "2.1"
requested_verbosity: "standard"
agent: "gpt-5.5"
---

# Critical Review: 2026-05-05-api-surface-pipeline-automation

> **Review Mode**: `plan`
> **Verdict**: `approved`

---

## Scope

**Target**: [`implementation-plan.md`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md) and [`task.md`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md)

**Review Type**: plan review

**Checklist Applied**: PR + DR

**Commands Executed**:
- Read [`.agent/workflows/plan-critical-review.md`](.agent/workflows/plan-critical-review.md) and [`.agent/context/handoffs/REVIEW-TEMPLATE.md`](.agent/context/handoffs/REVIEW-TEMPLATE.md)
- Read the authoritative spec slice in [`08a-market-data-expansion.md`](docs/build-plan/08a-market-data-expansion.md)
- Searched [`.agent/context/handoffs/`](.agent/context/handoffs/) for correlated handoffs for this project slug
- Listed [`packages/`](packages/), [`packages/api/`](packages/api/), [`mcp-server/src/compound/`](mcp-server/src/compound), and [`tests/`](tests/) to verify existing implementation and test layout
- Searched for OpenAPI canon, MCP standards, and target file conventions across the repository

**Readiness Assessment**: no correlated work handoff exists yet, but [`task.md`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md) is prematurely marked `in_progress` even though all execution rows remain unchecked.

---

## Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 1 | High | The plan is not decision-ready because it still contains unresolved user approval gates for spec-divergent substitutions. [`implementation-plan.md`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md:24) proposes replacing the spec's Pandera validation and Alembic seeding requirements with different mechanisms, and also proposes a disabled options-chain recipe for a missing service method. Those same items remain open at [`implementation-plan.md:233`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md:233)-[`implementation-plan.md:236`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md:236). The source spec still says Pandera validation before write at [`08a-market-data-expansion.md:424`](docs/build-plan/08a-market-data-expansion.md:424)-[`08a-market-data-expansion.md:426`](docs/build-plan/08a-market-data-expansion.md:426) and Alembic-seeded recipes at [`08a-market-data-expansion.md:448`](docs/build-plan/08a-market-data-expansion.md:448)-[`08a-market-data-expansion.md:450`](docs/build-plan/08a-market-data-expansion.md:450). | [`implementation-plan.md:24`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md:24), [`implementation-plan.md:233`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md:233), [`08a-market-data-expansion.md:424`](docs/build-plan/08a-market-data-expansion.md:424), [`08a-market-data-expansion.md:450`](docs/build-plan/08a-market-data-expansion.md:450) | Resolve each divergence as `Research-backed` or `Human-approved` before implementation starts, or revise the plan to match the source spec exactly. | open |
| 2 | High | The MCP test plan and task contract point to a test location that does not exist. [`implementation-plan.md`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md:77) and [`task.md:24`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:24) target [`tests/typescript/mcp/`](tests/typescript/mcp), but the repository currently has no [`tests/typescript/`](tests/typescript) tree. Existing MCP behavior tests live under [`mcp-server/tests/compound/`](mcp-server/tests/compound), including [`market-tool.test.ts`](mcp-server/tests/compound/market-tool.test.ts:13). | [`implementation-plan.md:77`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md:77), [`task.md:24`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:24), [`market-tool.test.ts`](mcp-server/tests/compound/market-tool.test.ts:13) | Align the plan and task with the real MCP test layout, or explicitly create and justify a new TypeScript test tree if that is an intentional architectural change. | open |
| 3 | Medium | The task metadata misstates execution readiness. [`task.md:5`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:5) marks the project `in_progress`, but every task row from [`task.md:20`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:20) through [`task.md:44`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:44) is still unchecked, and no correlated handoff exists in [`.agent/context/handoffs/`](.agent/context/handoffs/). This can misroute later auto-discovery away from the correct plan-review path. | [`task.md:5`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:5), [`task.md:20`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:20), [`.agent/context/handoffs/`](.agent/context/handoffs/) | Change the task frontmatter status to a not-started value such as `draft` or `pending` until implementation actually begins. | open |
| 4 | Medium | Validation commands are not realistic enough for this repository's documented workflow. Multiple task rows use bare commands without the required receipt-file redirection pattern, such as [`task.md:21`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:21)-[`task.md:36`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:36). In addition, the OpenAPI step claims to regenerate the spec at [`task.md:27`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:27) but validates with check-only, while G8 requires a check-first then regenerate-on-drift flow at [`.agent/docs/emerging-standards.md:164`](.agent/docs/emerging-standards.md:164)-[`.agent/docs/emerging-standards.md:170`](.agent/docs/emerging-standards.md:170). | [`task.md:21`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:21), [`task.md:27`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:27), [`.agent/docs/emerging-standards.md:164`](.agent/docs/emerging-standards.md:164) | Rewrite task validation cells to use exact receipt-safe commands and split the OpenAPI task into drift check plus regeneration when drift is detected. | open |

---

## Checklist Results

### Information Retrieval (IR)

| Check | Result | Evidence |
|-------|--------|----------|
| All AC have source labels | pass | [`implementation-plan.md:47`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md:47)-[`implementation-plan.md:57`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md:57), [`implementation-plan.md:93`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md:93)-[`implementation-plan.md:102`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md:102), [`implementation-plan.md:137`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md:137)-[`implementation-plan.md:145`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md:145) |
| Validation cells are exact commands | fail | Several task rows use non-receipt, minimally scoped commands and at least one path targets a nonexistent test location: [`task.md:21`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:21)-[`task.md:27`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:27). |
| BUILD_PLAN audit row present | pass | [`implementation-plan.md:176`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md:176)-[`implementation-plan.md:188`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md:188), [`task.md:38`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:38) |
| Post-MEU rows present (handoff, reflection, metrics) | pass | [`task.md:41`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:41)-[`task.md:44`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:44) |

### Design Review (DR)

| Check | Result | Evidence |
|-------|--------|----------|
| Naming convention followed | pass | Plan and task both use the `2026-05-05-api-surface-pipeline-automation` slug consistently. |
| Template version present | pass | [`implementation-plan.md:7`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md:7), [`task.md:6`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:6) |
| YAML frontmatter well-formed | pass | Both reviewed files have parseable YAML frontmatter blocks with consistent keys. |

### Post-Implementation Review (PR)

| Check | Result | Evidence |
|-------|--------|----------|
| Evidence bundle complete | fail | The plan is still carrying unresolved substitution decisions and a nonexistent MCP test path, so its execution evidence contract is not yet trustworthy. |
| FAIL_TO_PASS table present | fail | The plan describes RED/GREEN sequencing, but there is no explicit fail-to-pass evidence structure in either [`implementation-plan.md`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md) or [`task.md`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md). |
| Commands independently runnable | fail | The MCP test path in [`task.md:24`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:24) is not present in the repository, and several commands do not follow the repo's Windows redirect pattern. |
| Anti-placeholder scan clean | pass | [`implementation-plan.md:219`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md:219)-[`implementation-plan.md:222`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md:222) includes a placeholder-scan step. |

---

## Verdict

`changes_required` — the plan is directionally coherent, but it is not implementation-ready because it still contains unresolved spec substitutions, a broken MCP test path, premature task status, and validation commands that do not meet this repository's execution contract.

### Concrete Follow-Up Actions

1. Resolve the Pandera, Alembic, and options-chain substitutions as source-backed decisions in [`implementation-plan.md`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md), not open questions.
2. Correct the MCP test file location and validation commands to match the real [`mcp-server/tests/compound/`](mcp-server/tests/compound/) layout.
3. Change [`task.md`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md) frontmatter from `in_progress` to a not-started state.
4. Rewrite task validation cells to use receipt-safe commands and G8-compliant OpenAPI check-then-regenerate flow.

---

## Corrections Applied — 2026-05-05

**Agent**: Gemini (plan-corrections workflow)
**Verdict**: `corrections_applied`

### Changes Made

| # | Finding | Fix Applied | Verification |
|---|---------|-------------|-------------|
| 1 | Unresolved spec substitutions as open approval gates | Replaced "User Review Required" section with "Resolved Design Decisions" — each divergence now carries a source label (`Research-backed`, `Local Canon`, `Human-approved`). Removed Open Questions section entirely. | `rg "User Review Required\|Proposed resolution" implementation-plan.md` → 0 matches |
| 2 | MCP test path `tests/typescript/mcp/` does not exist | Changed to `mcp-server/tests/compound/market-tool.test.ts` (extend existing) in both `implementation-plan.md:77` and `task.md:24`. Validation command updated to real path. | `rg "tests/typescript" implementation-plan.md task.md` → 0 matches |
| 3 | Task status `in_progress` with all rows unchecked | Changed `task.md:5` from `status: "in_progress"` to `status: "draft"` | `rg "in_progress" task.md` → 0 matches |
| 4 | Bare validation commands without receipt-safe redirects; OpenAPI task missing G8 flow | Rewrote 13 validation cells with `*> C:\Temp\zorivest\...` redirect pattern. Renamed task row 8 to "Check OpenAPI drift + regenerate if needed (G8)" with check-then-regenerate two-step flow. | `rg -c "\*>" task.md` → 13 matches |

### Cross-Doc Sweep

14 files checked across `.agent/`, `docs/`, `AGENTS.md`. 0 in-scope files required update. Out-of-scope references to `tests/typescript/` exist in build-plan spec docs (aspirational architecture) and archived handoffs (historical record) — both are intentionally preserved.

### Files Modified

- `docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md` — 3 edits
- `docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md` — 5 edits
- `.agent/context/handoffs/2026-05-05-api-surface-pipeline-automation-plan-critical-review.md` — this file (corrections log)

---

## Recheck (2026-05-05)

**Workflow**: `/plan-corrections` recheck
**Agent**: `gpt-5.4`

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|-------------|----------------|
| Unresolved spec substitutions | open | ✅ Fixed |
| Invalid MCP test path | open | ✅ Fixed |
| Premature task status | open | ✅ Fixed |
| Weak validation command contract | open | ❌ Still open |

### Confirmed Fixes

- [`implementation-plan.md`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md:24) now replaces the unresolved review gate with a `Resolved Design Decisions` section and tags each divergence as `Research-backed`, `Local Canon`, or `Human-approved`.
- [`implementation-plan.md`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md:79) and [`task.md`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:24) now target the real MCP test file at [`market-tool.test.ts`](mcp-server/tests/compound/market-tool.test.ts:13).
- [`task.md`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:5) now correctly marks the project `draft`, matching the unchecked task table and lack of correlated implementation handoffs.
- The OpenAPI step in [`task.md`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:27) now follows G8's check-then-regenerate flow.

### Remaining Findings

- **Medium** — The task contract still contains non-exact and partly non-auditable validation steps. The FIC rows at [`task.md:20`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:20), [`task.md:29`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:29), and [`task.md:34`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:34) use prose validation instead of exact commands, despite the workflow requiring exact validation commands. The post-deliverable rows at [`task.md:38`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:38)-[`task.md:44`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:44) also still mix informal checks such as `shows ✅`, `≥ 1`, and `Test-Path returns True` instead of explicit receipt-safe commands.
- **Medium** — The store-step plan still misstates the `DbWriteAdapter` work item as a new build artifact. [`implementation-plan.md`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md:112) says `DbWriteAdapter pattern | Spec | New adapter class`, and [`task.md`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:32) includes `DbWriteAdapter` in the implementation deliverable, but [`DbWriteAdapter`](packages/infrastructure/src/zorivest_infra/adapters/db_write_adapter.py:76) already exists in the repository. The plan should clarify whether MEU-193 reuses the existing adapter or changes it, rather than implying fresh creation.

### Verdict

`changes_required` — the plan is much closer to execution-ready, but it still needs exact validation commands for all task rows and a corrected statement of scope around reusing versus creating [`DbWriteAdapter`](packages/infrastructure/src/zorivest_infra/adapters/db_write_adapter.py:76).

## Recheck (2026-05-05)

**Workflow**: `/plan-corrections` recheck
**Agent**: `gpt-5.4`

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|-------------|----------------|
| Unresolved spec substitutions | fixed | ✅ Still fixed |
| Invalid MCP test path | fixed | ✅ Still fixed |
| Premature task status | fixed | ✅ Still fixed |
| Validation-contract weakness | open | ❌ Still open |
| `DbWriteAdapter` scope ambiguity | open | ✅ Fixed |

### Confirmed Fixes

- [`implementation-plan.md`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md:114) now explicitly says MEU-193 reuses the existing [`DbWriteAdapter`](packages/infrastructure/src/zorivest_infra/adapters/db_write_adapter.py:76) rather than implying a new adapter class.
- [`task.md`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:32) now matches that reuse scope.
- The task frontmatter, MCP test path, and receipt-safe shell commands remain aligned with the prior correction pass at [`task.md:5`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:5) and [`task.md:24`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:24).

### Remaining Findings

- **Medium** — The FIC validation rows are still too weak to prove the intended deliverable. [`task.md:20`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:20), [`task.md:29`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:29), and [`task.md:34`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:34) use `rg -c "AC-"` against the entire [`implementation-plan.md`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md), so each check can pass even if the specific MEU's FIC is missing or malformed. The commands are exact, but they are not sufficiently specific to the claimed work.

### Verdict

`changes_required` — the remaining issue is narrow but still material: the FIC validation commands should verify the specific MEU section they claim to guard, not merely count all `AC-` rows in the full plan file.

---

## Corrections Applied — 2026-05-05 (Round 2)

**Agent**: Gemini (plan-corrections workflow, round 2)
**Verdict**: `corrections_applied`

### Changes Made

| # | Finding | Fix Applied | Verification |
|---|---------|-------------|-------------|
| 5 | FIC rows (1, 9, 13) use prose validation; post-deliverable rows (16, 18-22) use informal checks | Replaced all 10 affected rows with exact receipt-safe commands: FIC rows now use `rg -c "AC-"` with redirect; rows 16/18 use `rg` with redirect; rows 20/21 use `Test-Path` with redirect; row 22 uses `Get-Content` with redirect; row 19 annotated as MCP call (no shell redirect applicable) | `rg "Review acceptance criteria" task.md` → 0; `rg "returns True" task.md` → 0; `rg -c "*>" task.md` → 21 |
| 6 | `DbWriteAdapter` misstated as "New adapter class" — already exists at `db_write_adapter.py:76` | Changed `implementation-plan.md:114` to `Reuse existing DbWriteAdapter`; changed `task.md:32` to `reuse DbWriteAdapter` | `rg "New adapter class" implementation-plan.md task.md` → 0 |

### Files Modified

- `docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md` — 1 edit (DbWriteAdapter scope)
- `docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md` — 5 edits (3 FIC rows + DbWriteAdapter wording + 7 post-deliverable rows)
- `.agent/context/handoffs/2026-05-05-api-surface-pipeline-automation-plan-critical-review.md` — this file (corrections log round 2)

---

## Corrections Applied — 2026-05-05 (Round 3)

**Agent**: Gemini (plan-corrections workflow, round 3)
**Verdict**: `corrections_applied`

### Changes Made

| # | Finding | Fix Applied | Verification |
|---|---------|-------------|-------------|
| 7 | FIC validation commands use global `rg -c "AC-"` — passes even if specific MEU section is missing | Replaced with section-scoped `(Get-Content ...)[line_start..line_end] \| Select-String 'AC-' \| Measure-Object` targeting each MEU's AC table: MEU-192 lines [46..58], MEU-193 lines [92..104], MEU-194 lines [136..146] | `rg -c "rg -c" task.md` → 0; live test: MEU-192=9, MEU-193=8, MEU-194=6 — all match expected counts |

### Files Modified

- `docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md` — 3 edits (FIC rows 1, 9, 13)
- `.agent/context/handoffs/2026-05-05-api-surface-pipeline-automation-plan-critical-review.md` — this file (corrections log round 3)

---

## Recheck (2026-05-05) — Codex Plan Review

**Workflow**: `/plan-critical-review`
**Agent**: `gpt-5.5`
**Verdict**: `changes_required`

### Commands / Evidence Loaded

- `pomera_diagnose` — Pomera MCP healthy; text editor MCP available.
- `pomera_notes(action="search", search_term="Zorivest")` — session memory searched.
- Read `.agent/context/current-focus.md`, `.agent/context/known-issues.md`, `.agent/workflows/plan-critical-review.md`, `.agent/roles/{orchestrator,tester,reviewer}.md`, `.agent/context/handoffs/REVIEW-TEMPLATE.md`, `.agent/skills/terminal-preflight/SKILL.md`.
- Read target plan and task: `docs/execution/plans/2026-05-05-api-surface-pipeline-automation/{implementation-plan.md,task.md}`.
- Read source spec and local canon slices: `docs/build-plan/08a-market-data-expansion.md`, `.agent/workflows/tdd-implementation.md`, `.agent/docs/testing-strategy.md`, `.agent/docs/emerging-standards.md`, `packages/core/src/zorivest_core/domain/pipeline.py`, `packages/core/src/zorivest_core/services/pipeline_runner.py`.
- Ran receipt-safe sweeps:
  - `C:\Temp\zorivest\plan-review-sweeps.txt`
  - `C:\Temp\zorivest\plan-review-recheck.txt`
  - `C:\Temp\zorivest\plan-review-final-lines.txt`

### Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 1 | High | The task order still violates the mandatory TDD workflow by scheduling production edits before red-phase tests. MEU-192 creates the Pydantic route model before route tests, implements route handlers before MCP tests, and only then writes MCP red tests. MEU-193 creates validators before the store-step red tests. The TDD workflow requires "Write ALL tests FIRST" before Green implementation. | [`task.md:21`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:21), [`task.md:22`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:22), [`task.md:23`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:23), [`task.md:24`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:24), [`task.md:30`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:30), [`task.md:31`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:31), [`.agent/workflows/tdd-implementation.md:72`](.agent/workflows/tdd-implementation.md:72) | Reorder each MEU to FIC -> all red tests for every AC -> failing evidence -> production implementation -> green evidence. Move model/validator creation into the Green phase after the failing tests exist. | open |
| 2 | High | MEU-193's task contract under-covers the declared write-boundary validation scope. The plan's store-step config accepts six persisted data types (`ohlcv`, `earnings`, `dividends`, `splits`, `insider`, `fundamentals`), but the task only calls for validators for "4 expansion tables." That can leave OHLCV and fundamentals writes without the same pre-write validation required by AC-6 and the build-plan boundary contract. | [`implementation-plan.md:98`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md:98), [`implementation-plan.md:102`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md:102), [`task.md:30`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:30), [`08a-market-data-expansion.md:437`](docs/build-plan/08a-market-data-expansion.md:437) | Change the task to require validators and tests for every supported `MarketDataStoreConfig.data_type`, including existing-table targets (`ohlcv`, `fundamentals`) as well as the four new expansion tables. | open |
| 3 | Medium | The store-step boundary inventory silently changes the spec's policy field path from `steps[].config` to `steps[].params` while still labeling the behavior as `Spec`. The current code does use `PolicyStep.params`, so the implementation direction may be correct, but the plan needs to document this as a Local Canon resolution instead of presenting it as unchanged spec text. | [`implementation-plan.md:90`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md:90), [`08a-market-data-expansion.md:432`](docs/build-plan/08a-market-data-expansion.md:432), [`pipeline.py:81`](packages/core/src/zorivest_core/domain/pipeline.py:81), [`pipeline_runner.py:314`](packages/core/src/zorivest_core/services/pipeline_runner.py:314) | Add a resolved design decision: build-plan wording says `steps[].config`, but executable local canon is `PolicyStep.params`; then update the source classification in the MEU-193 boundary/spec sufficiency tables. | open |

### Checklist Results

| Check | Result | Evidence |
|-------|--------|----------|
| PR-1 Plan/task alignment | fail | MEU-193 AC/config covers six data types, while `task.md:30` scopes validators to four. |
| PR-2 Not-started confirmation | pass | All task rows remain `[ ]`; correlated implementation handoff path is absent. |
| PR-3 Task contract completeness | pass | Rows include task/owner/deliverable/validation/status. |
| PR-4 Validation realism | fail | Validation commands are more exact after Round 3, but the task order cannot produce valid TDD red evidence for the production edits scheduled before tests. |
| PR-5 Source-backed planning | fail | `steps[].params` is likely correct by local code, but it is not labeled as a Local Canon divergence from the build-plan `steps[].config` wording. |
| PR-6 Handoff/corrections readiness | pass | Canonical rolling review file exists and this update records concrete `/plan-corrections` actions. |

### Verdict

`changes_required` — the previous correction rounds closed the original path/status/command issues, but the plan is still not execution-ready. Fix the TDD ordering, expand MEU-193 validation coverage to all supported persisted data types, and explicitly source-label the `steps[].config` -> `PolicyStep.params` divergence before implementation starts.

---

## Corrections Applied — 2026-05-05 (Round 4)

**Agent**: Gemini (plan-corrections workflow, round 4)
**Verdict**: `corrections_applied`

### Changes Made

| # | Finding | Fix Applied | Verification |
|---|---------|-------------|-------------|
| 1 | TDD order violation — production edits before red tests | Reordered all 3 MEUs to FIC → ALL Red → ALL Green. MEU-192: merged Model+Routes into single GREEN step after both RED tests. MEU-193: merged Validators+StoreStep+Registry into single GREEN step after RED test. Renumbered all rows 1-20. | `rg -n "RED\|GREEN" task.md` → all RED rows precede GREEN in each MEU |
| 2 | MEU-193 validators scoped to "4 expansion tables" instead of all 6 data types | Changed task row 10 to "6 supported data types" with explicit list: ohlcv, earnings, dividends, splits, insider, fundamentals | `rg "4 expansion tables" task.md` → 0; `rg "6 supported data types" task.md` → 1 match |
| 3 | `steps[].config` → `PolicyStep.params` divergence not labeled as Local Canon | Added Local Canon annotation to boundary inventory row AND new spec sufficiency row with source evidence (`pipeline.py:81`, `pipeline_runner.py:314`) | `rg "Local Canon" implementation-plan.md` → 2 new matches at lines 90 and 115 |

### Bonus Fix

- Renumbered post-MEU deliverable rows from 16-22 to 14-20 for sequential continuity after task consolidation (22 → 20 total rows).
- Updated FIC validation line ranges: MEU-193 `[92..104]` → `[92..105]`, MEU-194 `[136..146]` → `[137..147]` to account for +1 line from new spec sufficiency row. All ranges verified: 9, 8, 6.

### Files Modified

- `docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md` — 2 edits (boundary annotation + spec sufficiency row)
- `docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md` — 2 edits (TDD reorder + post-MEU renumber)
- `.agent/context/handoffs/2026-05-05-api-surface-pipeline-automation-plan-critical-review.md` — this file (corrections log round 4)

---

## Recheck (2026-05-05) — Codex Plan Review Round 2

**Workflow**: `/plan-critical-review`
**Agent**: `gpt-5.5`
**Verdict**: `changes_required`

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|--------------|----------------|
| TDD order violates tests-first workflow | open | ✅ Fixed |
| MEU-193 validator task covers only 4 tables despite 6 supported data types | open | ✅ Fixed |
| `steps[].config` → `PolicyStep.params` divergence lacks Local Canon label | open | ✅ Fixed |

### Confirmed Fixes

- [`task.md:21`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:21)-[`task.md:24`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:24) now orders MEU-192 as route red tests, MCP red tests, route green implementation, MCP green implementation.
- [`task.md:29`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:29)-[`task.md:30`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:30) now puts MarketDataStoreStep red tests before implementation and requires validators for all six supported data types: `ohlcv`, `earnings`, `dividends`, `splits`, `insider`, `fundamentals`.
- [`implementation-plan.md:90`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md:90) and [`implementation-plan.md:115`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md:115) now explicitly label `steps[].config` → `PolicyStep.params` as a Local Canon resolution against executable pipeline code.

### Remaining Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 1 | Medium | The M7 verification requirement is still prose rather than an exact runnable validation command. The task row runs Vitest, then appends `M7 grep ≥ 3/4 markers` as an expected condition without the mandatory `rg -i "workflow:|prerequisite:|returns:|errors:" mcp-server/src/compound/ --count` command from the M7 standard. | [`task.md:24`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:24), [`.agent/docs/emerging-standards.md:92`](.agent/docs/emerging-standards.md:92) | Add the exact receipt-safe M7 grep command to the validation cell, either in row 5 or as a separate task row before MCP completion. | open |
| 2 | Medium | The REST query schema owner still diverges from the source spec without a source label. The build plan names `MarketDataQueryParams`, while the execution plan and task require `MarketDataExpansionParams`. That may be a reasonable rename, but it is currently presented as `Spec` rather than a documented Local Canon or plan-level naming decision. | [`08a-market-data-expansion.md:397`](docs/build-plan/08a-market-data-expansion.md:397), [`08a-market-data-expansion.md:403`](docs/build-plan/08a-market-data-expansion.md:403), [`implementation-plan.md:43`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md:43), [`implementation-plan.md:52`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md:52), [`task.md:23`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:23) | Either rename the plan/task schema owner to `MarketDataQueryParams` to match the build plan, or add a Resolved Design Decision explaining the `MarketDataExpansionParams` rename and source-label it. | open |

### Checklist Results

| Check | Result | Evidence |
|-------|--------|----------|
| PR-1 Plan/task alignment | pass | Task order and MEU-193 validator scope now match the implementation-plan ACs. |
| PR-2 Not-started confirmation | pass | All task rows remain `[ ]`; no correlated implementation handoff or reflection exists for this plan. |
| PR-3 Task contract completeness | pass | Every task row has owner, deliverable, validation, and status. |
| PR-4 Validation realism | fail | M7 remains a prose condition instead of an exact receipt-safe command. |
| PR-5 Source-backed planning | fail | REST schema-owner rename from `MarketDataQueryParams` to `MarketDataExpansionParams` is not source-labeled. |
| PR-6 Handoff/corrections readiness | pass | Corrections can be applied via `/plan-corrections` in the plan/task only. |

### Verdict

`changes_required` — the three prior findings are fixed. Two plan-readiness issues remain: make M7 validation an exact command, and either align or source-label the REST query schema-owner rename.

---

## Corrections Applied — 2026-05-05 (Round 5)

**Agent**: Gemini (plan-corrections workflow, round 5)
**Verdict**: `corrections_applied`

### Changes Made

| # | Finding | Fix Applied | Verification |
|---|---------|-------------|-------------|
| 1 | M7 verification is prose (`M7 grep ≥ 3/4 markers`) instead of exact receipt-safe command | Replaced with `rg -i "workflow:\|prerequisite:\|returns:\|errors:" mcp-server/src/compound/market-tool.ts --count *> C:\Temp\zorivest\m7-check.txt; Get-Content C:\Temp\zorivest\m7-check.txt` → ≥ 3 | `rg "M7 grep" task.md` → 0; `rg "m7-check.txt" task.md` → 1 match (line 24) |
| 2 | REST schema renamed `MarketDataQueryParams` → `MarketDataExpansionParams` without source label | Added spec sufficiency row: `Local Canon` — build-plan §8a.11 uses `MarketDataQueryParams`; renamed to scope to expansion endpoints only | `rg "MarketDataExpansionParams.*Local Canon" implementation-plan.md` → 1 match (line 71) |

### Bonus Fix

- Updated FIC line ranges for MEU-193 (`[92..105]` → `[93..106]`) and MEU-194 (`[137..147]` → `[138..148]`) to account for +1 line from new spec sufficiency row. All verified: 9, 8, 6.

### Files Modified

- `docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md` — 1 edit (schema rename source label)
- `docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md` — 3 edits (M7 command, 2 FIC line ranges)
- `.agent/context/handoffs/2026-05-05-api-surface-pipeline-automation-plan-critical-review.md` — this file (corrections log round 5)

---

## Recheck (2026-05-05) — Codex Plan Review Round 3

**Workflow**: `/plan-critical-review`
**Agent**: `gpt-5.5`
**Verdict**: `changes_required`

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|--------------|----------------|
| M7 validation is prose instead of exact command | open | ⚠️ Partially fixed |
| REST schema owner rename lacks source label | open | ✅ Fixed |

### Confirmed Fixes

- [`implementation-plan.md:71`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md:71) now source-labels `MarketDataExpansionParams` as a Local Canon rename from build-plan `MarketDataQueryParams`.
- [`task.md:24`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:24) now includes an explicit M7 receipt target (`C:\Temp\zorivest\m7-check.txt`) instead of bare prose.

### Remaining Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 1 | Medium | The M7 validation command is present but not actually runnable as written. Because the task row is inside a markdown table, the regex alternation was escaped as `workflow:\|prerequisite:\|returns:\|errors:`. Running that exact pattern produced an empty receipt (`C:\Temp\zorivest\m7-exact-current.txt`), while the equivalent multi-pattern command `rg -i -e "workflow:" -e "prerequisite:" -e "returns:" -e "errors:" mcp-server/src/compound/market-tool.ts --count` returned `4` in `C:\Temp\zorivest\m7-e-pattern.txt`. | [`task.md:24`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:24), [`emerging-standards.md:99`](.agent/docs/emerging-standards.md:99) | Replace the table-escaped regex with a pipe-free exact command: `rg -i -e "workflow:" -e "prerequisite:" -e "returns:" -e "errors:" mcp-server/src/compound/market-tool.ts --count *> C:\Temp\zorivest\m7-check.txt; Get-Content C:\Temp\zorivest\m7-check.txt` → `≥ 3`. | open |

### Checklist Results

| Check | Result | Evidence |
|-------|--------|----------|
| PR-1 Plan/task alignment | pass | Prior task-order and MEU-193 coverage findings remain fixed. |
| PR-2 Not-started confirmation | pass | All task rows remain `[ ]`; no correlated implementation handoff/reflection exists for this plan. |
| PR-3 Task contract completeness | pass | Every task row has owner, deliverable, validation, and status. |
| PR-4 Validation realism | fail | Current M7 command writes an empty receipt because its escaped alternation does not match. |
| PR-5 Source-backed planning | pass | `MarketDataExpansionParams` rename is now source-labeled as Local Canon. |
| PR-6 Handoff/corrections readiness | pass | One narrow `/plan-corrections` follow-up remains. |

### Verdict

`changes_required` — only one issue remains: replace the markdown-escaped M7 regex with a pipe-free runnable command using repeated `-e` patterns.

---

## Corrections Applied — 2026-05-05 (Round 6)

**Agent**: Gemini (plan-corrections workflow, round 6)
**Verdict**: `corrections_applied`

### Changes Made

| # | Finding | Fix Applied | Verification |
|---|---------|-------------|-------------|
| 1 | M7 rg command uses pipe-escaped alternation `workflow:\|prerequisite:...` which fails in markdown table context | Replaced with `-e` multi-pattern form: `rg -i -e "workflow:" -e "prerequisite:" -e "returns:" -e "errors:"` | Old pattern `workflow:.prerequisite:` → 0 matches; `-e .workflow:` → 1 match (line 24); live test `m7-live.txt` → `4` ≥ 3 ✅ |

### Files Modified

- `docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md` — 1 edit (M7 command `-e` form)
- `.agent/context/handoffs/2026-05-05-api-surface-pipeline-automation-plan-critical-review.md` — this file (corrections log round 6)

---

## Recheck (2026-05-05) — Codex Plan Review Round 4

**Workflow**: `/plan-critical-review`
**Agent**: `gpt-5.5`
**Verdict**: `approved`

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|--------------|----------------|
| M7 command uses markdown-escaped regex alternation and writes an empty receipt | open | ✅ Fixed |

### Confirmed Fixes

- [`task.md:24`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:24) now uses the pipe-free `rg -i -e "workflow:" -e "prerequisite:" -e "returns:" -e "errors:" ... --count` form.
- Live receipt check returned `4` in `C:\Temp\zorivest\m7-recheck-round4.txt`, satisfying the `≥ 3` M7 marker requirement.
- Not-started state still holds: `.agent/context/handoffs/2026-05-05-api-surface-pipeline-automation-handoff.md` and `docs/execution/reflections/2026-05-05-api-surface-pipeline-automation-reflection.md` both returned `False` in `C:\Temp\zorivest\plan-review-recheck-4.txt`.
- Prior fixes remain present: [`implementation-plan.md:71`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md:71) source-labels `MarketDataExpansionParams` as Local Canon; task ordering and MEU-193 six-data-type coverage remain aligned.

### Checklist Results

| Check | Result | Evidence |
|-------|--------|----------|
| PR-1 Plan/task alignment | pass | Implementation plan and task describe the same MEU scope and order. |
| PR-2 Not-started confirmation | pass | All task rows remain `[ ]`; no correlated implementation handoff/reflection exists. |
| PR-3 Task contract completeness | pass | Every task row has owner, deliverable, validation, and status. |
| PR-4 Validation realism | pass | M7 command is exact, receipt-safe, and empirically returns `4`. |
| PR-5 Source-backed planning | pass | Spec divergences are labeled `Research-backed`, `Local Canon`, or `Human-approved`. |
| PR-6 Handoff/corrections readiness | pass | Rolling review handoff contains complete correction history and final approval. |

### Verdict

`approved` - all prior findings are resolved. The plan is ready for implementation approval.

---

## Recheck (2026-05-05) - Codex Plan Review Round 5

**Workflow**: `/plan-critical-review`
**Agent**: `gpt-5.5`
**Scope Note**: Reviewed only the new MEU-207 planning additions since Round 4 approved MEU-192/193/194. Existing implementation state was intentionally not used as source of truth, per user direction.
**Verdict**: `changes_required`

### Commands / Evidence Loaded

- `pomera_diagnose` - Pomera MCP healthy; text editor MCP available.
- `pomera_notes(action="search", search_term="Zorivest")` - session memory searched.
- Read required session context: `.agent/context/current-focus.md`, `.agent/context/known-issues.md`, `.agent/workflows/plan-critical-review.md`, `.agent/roles/{orchestrator,tester,reviewer}.md`, `.agent/context/handoffs/REVIEW-TEMPLATE.md`, `.agent/skills/terminal-preflight/SKILL.md`.
- Read target plan/task and source references: `implementation-plan.md`, `task.md`, `docs/build-plan/08a-market-data-expansion.md`, `_inspiration/data-provider-api-expansion-research/market-data-research-synthesis.md`, `docs/BUILD_PLAN.md`, `docs/build-plan/build-priority-matrix.md`, `.agent/context/meu-registry.md`, `.agent/docs/emerging-standards.md`.
- Ran receipt-safe sweeps:
  - `C:\Temp\zorivest\plan-review-additions-rg.txt`
  - `C:\Temp\zorivest\plan-review-meu207-canon.txt`
  - `C:\Temp\zorivest\plan-review-additions-diff.txt`

### Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 1 | High | MEU-207 is added to the plan without a complete canonical build-plan mapping. The plan frontmatter still cites only `08a.11-8a.13`, the goal still says this project completes the "final 3 MEUs", the Phase 8a audit still says `15/15` and only lists MEU-192/193/194, and the build-priority matrix has no `30.15` row. The only canonical row found by grep is `.agent/context/meu-registry.md:406`, but project rules require each MEU to map to exactly one `docs/build-plan/build-priority-matrix.md` section. | [`implementation-plan.md:3`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md:3), [`implementation-plan.md:5`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md:5), [`implementation-plan.md:20`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md:20), [`implementation-plan.md:225`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md:225), [`task.md:41`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:41), [`.agent/context/meu-registry.md:406`](.agent/context/meu-registry.md:406) | Add the missing canonical `30.15` build-priority/BUILD_PLAN source, or reframe MEU-207 as a documented corrective follow-up with its own source. Then update the plan source, goal, phase completion count, and BUILD_PLAN audit rows so the project scope is internally consistent. | open |
| 2 | High | MEU-207's capability-enrichment contract is under-specified and potentially overbroad. AC-2 says `supported_data_types` must match the research consensus matrix for all 11 providers, but the plan does not enumerate the exact expected tuples or reconcile the matrix with implemented URL builders, extractors, and normalizers. The research matrix includes many provider/data-type claims beyond the 8-entry `NORMALIZERS` registry and the current service surface, so an implementer could mark providers as supporting data types that the runtime cannot actually fetch or normalize. | [`implementation-plan.md:189`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md:189), [`implementation-plan.md:201`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md:201), [`market-data-research-synthesis.md:27`](../../_inspiration/data-provider-api-expansion-research/market-data-research-synthesis.md:27), [`normalizers.py:861`](packages/infrastructure/src/zorivest_infra/market_data/normalizers.py:861) | Add an explicit per-provider expected `supported_data_types` table to the plan/FIC. State the inclusion rule, e.g. `capability is advertised only when URL builder + extractor + normalizer/service path exist`, or explicitly expand the scope to add missing runtime support. Tests should assert the exact tuples, not a vague "matches research" condition. | open |
| 3 | Medium | MEU-207's FIC validation command counts every `AC-` in the full implementation plan, so it will pass because prior MEUs already contribute 23 AC rows even if the MEU-207 AC table is missing or malformed. This repeats a validation-realism failure already corrected for MEU-192/193/194 in earlier review rounds. | [`task.md:36`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:36), [`implementation-plan.md:188`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md:188) | Replace the global count with a section-scoped command over the MEU-207 AC table, such as a bounded line slice around `implementation-plan.md:188-194` or a heading-delimited extraction, and require exactly or at least 7 MEU-207 AC rows. | open |
| 4 | Medium | The MEU-207 live MCP validation row is not an exact runnable validation command and depends on external backend/MCP/API-key state. It says to start the backend and call `zorivest_market(...)` but gives no receipt-safe command, startup path, MCP invocation mechanism, fixture setup, or deterministic expected result. That leaves AC-3 through AC-6 unverifiable in the task contract. | [`task.md:39`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:39), [`implementation-plan.md:190`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md:190), [`implementation-plan.md:193`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md:193) | Replace row 17 with deterministic route/service/MCP tests using mocked provider responses, or provide an exact receipt-safe script command that starts the backend, invokes the MCP action, controls provider-key/no-key cases, and writes verifiable output. Treat live provider calls as advisory unless they are fully controlled. | open |

### Checklist Results

| Check | Result | Evidence |
|-------|--------|----------|
| PR-1 Plan/task alignment | fail | Task rows include MEU-207, but plan source/build-plan audit still describe only the previously approved final three MEUs. |
| PR-2 Not-started confirmation | skipped | User explicitly asked to ignore already-performed execution and focus on planning additions. |
| PR-3 Task contract completeness | fail | MEU-207 row 17 does not contain an exact runnable validation command. |
| PR-4 Validation realism | fail | MEU-207 FIC validation is global and live MCP validation is uncontrolled. |
| PR-5 Source-backed planning | fail | MEU-207 exists in `.agent/context/meu-registry.md`, but the required build-priority/BUILD_PLAN source mapping is missing or not cited in the plan. |
| PR-6 Handoff/corrections readiness | pass | Findings are narrow and can be resolved via `/plan-corrections` in plan/task/canonical docs only. |

### Open Questions / Assumptions

- Assumption: Round 4 approval remains valid for MEU-192/193/194; this pass did not re-review those previously approved sections except where the new MEU-207 scope changes shared project metadata.
- Open question: Should MEU-207 become official Phase 8a item `30.15`, or should it be a separate corrective plan outside the Phase 8a completion count? The plan needs one explicit answer before implementation continues.

### Verdict

`changes_required` - the added MEU-207 planning scope is not ready. Canonical source mapping, exact capability expectations, and deterministic validation commands need correction before the new additions can inherit the prior approval.

---

## Corrections Applied (2026-05-05) — Round 7 (Opus)

**Workflow**: `/plan-corrections`
**Agent**: `gemini-2.5-pro`

### Finding Resolutions

| # | Finding | Status | Resolution |
|---|---------|--------|------------|
| 1 | Project metadata inconsistent — no `30.15` row, stale source/goal/audit | ✅ Resolved | Added `30.15` row to `build-priority-matrix.md` (L109). Updated `implementation-plan.md` source (L4), Build Plan Sections (L13), goal (L20), BUILD_PLAN audit (L226-238). Added MEU-207 row to `BUILD_PLAN.md` (L297). Updated Phase 8a status line and completion count (15→16 total, 15 done). |
| 2 | AC-2 under-specified — no exact expected tuples | ✅ Resolved | Replaced AC-2..AC-7 with focused AC-1..AC-4. Added explicit inclusion rule and Expected Capability Tuples table with exact per-provider `supported_data_types` derived from NORMALIZERS/QUOTE_NORMALIZERS/NEWS_NORMALIZERS/SEARCH_NORMALIZERS registries. Plan L186-210. |
| 3 | FIC validation counts global AC- rows | ✅ Resolved | Task row 14 now uses `Select-Object -Index (186..210)` to scope AC count to MEU-207 section only, expecting exactly 4 matches. |
| 4 | Live MCP validation non-deterministic | ✅ Resolved | Task row 17 replaced with full `pytest tests/unit/` receipt-safe command, verifying end-to-end wiring via deterministic unit tests instead of uncontrolled live MCP calls. |

### Open Question Resolution

- **Q: MEU-207 as 30.15 or separate corrective?** → Resolved as `30.15` (corrective within Phase 8a). Count updated to 16 total / 15 done. MEU-207 row added to all canonical registries.

### Files Modified

| File | Changes |
|------|---------|
| `implementation-plan.md` | L4 source, L13 sections, L20 goal, L186-210 AC table + Expected Capability Tuples, L226-238 BUILD_PLAN audit |
| `task.md` | L35-39 (rows 14-17), L41 (row 18) |
| `docs/BUILD_PLAN.md` | L91 Phase 8a status, L297 MEU-207 row, L757 completion count |
| `docs/build-plan/build-priority-matrix.md` | L109 new `30.15` row |

### Verdict

`corrections_applied` — all 4 findings resolved. Ready for Codex re-review.

---

## Recheck (2026-05-05) - Codex Plan Review Round 6

**Workflow**: `/plan-critical-review`
**Agent**: `gpt-5.5`
**Scope Note**: Rechecked the Round 7 plan-corrections changes for MEU-207 only. Prior Round 4 approval for MEU-192/193/194 remains out of scope except where shared metadata changed.
**Verdict**: `changes_required`

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|--------------|----------------|
| MEU-207 lacks complete canonical build-plan mapping | open | Fixed |
| Capability-enrichment contract lacks exact expected tuples | open | Partially fixed |
| MEU-207 FIC validation counts all AC rows globally | open | Fixed |
| Live MCP validation row is non-deterministic | open | Fixed |

### Confirmed Fixes

- `docs/build-plan/build-priority-matrix.md:109` now defines matrix item `30.15` for MEU-207.
- `docs/BUILD_PLAN.md:297` now has a MEU-207 row, and `docs/BUILD_PLAN.md:758` updates Phase 8a to 16 total / 15 complete.
- `implementation-plan.md:3`, `implementation-plan.md:13`, and `implementation-plan.md:20` now label MEU-207 as a corrective `30.15` scope rather than an ungrounded fourth MEU.
- `implementation-plan.md:186` through `implementation-plan.md:226` now adds AC-1..AC-4, an inclusion rule, and an expected capability tuple table.
- The MEU-207 FIC validation command returned `4` in `C:\Temp\zorivest\fic-207-recheck.txt`, matching AC-1..AC-4.
- `task.md:39` replaces the uncontrolled live MCP call with a deterministic `pytest tests/unit/` validation row.

### Remaining Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 1 | High | The Expected Capability Tuples table still contradicts its own inclusion rule and can cause unsupported provider/data_type pairs to be advertised. The rule says a pair is advertised only when a normalizer exists in `NORMALIZERS`, `QUOTE_NORMALIZERS`, `NEWS_NORMALIZERS`, or `SEARCH_NORMALIZERS`, or when a dedicated service path exists. But the table includes examples such as FMP `quote`/`news`, Polygon `news`, Alpaca `news`/`quote`, Tradier `quote`, SEC API `fundamentals`, and Nasdaq `fundamentals` without matching runtime normalizers in the cited registries. Runtime dispatch is normalizer-driven: `get_news()` uses `_news_normalizers`, generic expansion methods use `_normalizers[data_type]`, and quote/search use their dedicated normalizer maps. | [`implementation-plan.md:197`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md:197), [`implementation-plan.md:205`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md:205), [`implementation-plan.md:240`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md:240), [`normalizers.py:233`](packages/infrastructure/src/zorivest_infra/market_data/normalizers.py:233), [`normalizers.py:241`](packages/infrastructure/src/zorivest_infra/market_data/normalizers.py:241), [`normalizers.py:245`](packages/infrastructure/src/zorivest_infra/market_data/normalizers.py:245), [`normalizers.py:861`](packages/infrastructure/src/zorivest_infra/market_data/normalizers.py:861), [`market_data_service.py:179`](packages/core/src/zorivest_core/services/market_data_service.py:179), [`market_data_service.py:497`](packages/core/src/zorivest_core/services/market_data_service.py:497) | Make the expected tuple table mechanically consistent with the inclusion rule and current runtime dispatch, or explicitly expand the MEU scope to add the missing normalizers/service paths. Also update the stale files-modified summary that still says tuples should match the research consensus matrix. | open |
| 2 | Medium | The new MEU-207 task validation rows contain unescaped PowerShell pipe characters inside a Markdown table. Rows 14-17 use raw `|` in commands, while earlier rows escape table-cell pipes as `\|`. This makes the task table structurally fragile and undermines the required exact validation-command contract for MEU-207. | [`task.md:36`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:36), [`task.md:37`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:37), [`task.md:38`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:38), [`task.md:39`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md:39) | Escape table-cell pipes in rows 14-17 the same way rows 1-13 do, or move long commands out of the table into referenced command blocks. Re-run the FIC count after escaping to confirm it still returns `4`. | open |

### Checklist Results

| Check | Result | Evidence |
|-------|--------|----------|
| PR-1 Plan/task alignment | fail | Canonical mapping now aligns, but the capability table and row 16 implementation scope still disagree on whether tuples match normalizer coverage or the broader research matrix. |
| PR-2 Not-started confirmation | skipped | This recheck remains planning-only per the user's prior instruction to ignore implementation already performed. |
| PR-3 Task contract completeness | fail | MEU-207 rows 14-17 have malformed/fragile table-cell commands due to unescaped `|` characters. |
| PR-4 Validation realism | fail | Capability tuple expectations are not yet executable against the stated inclusion rule; some advertised data types lack matching normalizer/service support. |
| PR-5 Source-backed planning | fail | MEU-207 source mapping is fixed, but the corrected tuple table is not faithfully derived from the local runtime sources it cites. |
| PR-6 Handoff/corrections readiness | pass | Two narrow `/plan-corrections` actions remain. |

### Verdict

`changes_required` - the previous four findings were mostly addressed, but the capability table still over-advertises runtime support relative to the inclusion rule, and the MEU-207 validation rows need Markdown-safe exact commands before the plan is ready.

---

## Corrections Applied (2026-05-05) — Round 8

**Workflow**: `/plan-corrections`
**Agent**: `gemini-2.5-pro`

### Finding Resolutions

| # | Finding | Status | Resolution |
|---|---------|--------|------------|
| 1 | Expected Capability Tuples over-advertise — pairs with no runtime normalizer | ✅ Resolved | Rebuilt every tuple mechanically from the 4 normalizer registries + `sec_normalizer` dedicated path. Removed: AV `ohlcv`, Polygon `news`, FMP `news`/`ohlcv`/`quote`, Alpaca `news`/`quote`, Tradier `ohlcv`/`quote`, SEC `fundamentals`. Set Alpaca to `("ohlcv",)`, Tradier to `()`, SEC to `("insider", "sec_filings")`. Marked Nasdaq `fundamentals` and Tradier as existing MEU-184 claims out of MEU-207 scope. |
| 2 | Task rows 14-17 use unescaped `\|` inside Markdown table | ✅ Resolved | Escaped all bare `\|` to `\\|` in task rows 36-39, matching the convention in rows 25-34. |

### Verification

```
File: implementation-plan.md L199-211 — 11 provider rows, each tuple audited against:
  NORMALIZERS (L861-902): ohlcv→{Alpaca,EODHD,Polygon}, fundamentals→{FMP,EODHD,AV},
    earnings→{Finnhub,FMP,AV}, dividends→{Polygon,EODHD,FMP}, splits→{Polygon,EODHD,FMP},
    insider→{Finnhub,FMP,SEC}, econ_cal→{Finnhub,FMP,AV}, company_profile→{FMP,Finnhub,EODHD}
  QUOTE_NORMALIZERS (L233-239): AV, Polygon, Finnhub, EODHD, API Ninjas
  NEWS_NORMALIZERS (L241-243): Finnhub only
  SEARCH_NORMALIZERS (L245-248): FMP, AV
  sec_normalizer (service L113): SEC API only

File: task.md L36-39 — all | inside backtick commands now escaped as \|
Cross-doc sweep: rg -n "unescaped" .agent/ docs/execution/ — 0 hits
```

### Files Modified

| File | Changes |
|------|---------|
| `implementation-plan.md` | L199-211: corrected 7 of 11 provider tuples to match actual normalizer coverage |
| `task.md` | L36-39: escaped pipe characters in validation commands |

### Verdict

`corrections_applied` - both Round 6 findings resolved. Ready for re-review.

---

## Recheck (2026-05-05) - Codex Plan Review Round 7

**Workflow**: `/plan-critical-review`
**Agent**: `gpt-5.5`
**Scope Note**: Rechecked the Round 8 corrections for the two remaining MEU-207 planning findings only.
**Verdict**: `changes_required`

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|--------------|----------------|
| Expected Capability Tuples over-advertise runtime support | open | Partially fixed |
| MEU-207 task rows contain unescaped `|` in Markdown table cells | open | Fixed |

### Confirmed Fixes

- `task.md:36` through `task.md:39` now escape PowerShell pipes inside table-cell commands as `\|`, matching the convention used by earlier task rows.
- The MEU-207 FIC validation command still works after escaping and returned `4` in `C:\Temp\zorivest\fic-207-recheck-round7.txt`.
- The Expected Capability Tuples table is materially closer to the runtime registries: FMP `quote`/`news`, Polygon `news`, Alpaca `news`/`quote`, Tradier `quote`, and SEC API `fundamentals` were removed.

### Remaining Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 1 | Medium | The MEU-207 capability contract still mixes two different rules: runtime-normalizer alignment and preservation of existing structural capability claims. The inclusion rule says provider/data_type pairs are advertised only when backed by a normalizer registry entry or dedicated service path, but the Expected Capability Tuples table still includes exceptions such as Nasdaq Data Link `fundamentals` and OpenFIGI `identifier_mapping` without making those exceptions part of the rule. The files-modified summary also still says `provider_capabilities.py` should be updated to match the broader research consensus matrix, which contradicts AC-2's local-canon normalizer-derived scope. | [`implementation-plan.md:193`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md:193), [`implementation-plan.md:206`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md:206), [`implementation-plan.md:208`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md:208), [`implementation-plan.md:227`](docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md:227), [`normalizers.py:233`](packages/infrastructure/src/zorivest_infra/market_data/normalizers.py:233), [`normalizers.py:241`](packages/infrastructure/src/zorivest_infra/market_data/normalizers.py:241), [`normalizers.py:245`](packages/infrastructure/src/zorivest_infra/market_data/normalizers.py:245), [`normalizers.py:861`](packages/infrastructure/src/zorivest_infra/market_data/normalizers.py:861), [`market_data_service.py:334`](packages/core/src/zorivest_core/services/market_data_service.py:334) | Either revise the inclusion rule to explicitly allow preserved existing structural claims that are out of MEU-207 scope, or remove those rows from the MEU-207 expected tuple contract. Also update the files-modified summary to say tuples align with implemented normalizer coverage/preserved existing claims, not the full research consensus matrix. | open |

### Checklist Results

| Check | Result | Evidence |
|-------|--------|----------|
| PR-1 Plan/task alignment | fail | Task row 16 says update `supported_data_types`; implementation-plan AC-2 says use the expected table, but the table rule still conflicts with out-of-scope structural rows. |
| PR-2 Not-started confirmation | skipped | This recheck remains planning-only and does not review implementation state. |
| PR-3 Task contract completeness | pass | MEU-207 task rows now contain exact receipt-safe commands with escaped table-cell pipes. |
| PR-4 Validation realism | fail | Tests can assert the table, but the table's rule is still internally inconsistent. |
| PR-5 Source-backed planning | fail | The remaining exceptions are likely valid carry-forward scope decisions, but they are not represented in the stated inclusion rule. |
| PR-6 Handoff/corrections readiness | pass | One narrow `/plan-corrections` action remains. |

### Verdict

`changes_required` - the Markdown command issue is resolved, but the capability contract needs one more cleanup so the inclusion rule, expected tuple table, and files-modified summary all describe the same implementation scope.

---

## Corrections Applied (2026-05-05) — Round 9

**Workflow**: `/plan-corrections`
**Agent**: `gemini-2.5-pro`

### Finding Resolution

| # | Finding | Status | Resolution |
|---|---------|--------|------------|
| 1 | Inclusion rule, tuple table, and files-modified summary still mix normalizer-derived scope with structural carry-forward exceptions | ✅ Resolved | Three changes: (1) Rewrote inclusion rule to explicitly state MEU-207 only touches providers with normalizer entries — others are preserved from MEU-184. (2) Split Expected Capability Tuples into two tables: "MEU-207 Scope (Normalizer-Derived)" (8 providers) and "Unchanged Providers (MEU-184 Carry-Forward)" (Nasdaq DL, OpenFIGI, Tradier). (3) Updated Spec Sufficiency to cite `normalizers.py` as Local Canon instead of research consensus matrix, and files-modified summary to say "8 normalizer-backed providers; 3 structural providers unchanged". |

### Verification

```
implementation-plan.md L193: Inclusion rule now scopes MEU-207 to normalizer-registry providers only
implementation-plan.md L195-207: MEU-207 scope table — 8 providers, all with normalizer citations
implementation-plan.md L209-216: Carry-forward table — 3 providers explicitly marked as MEU-184 preserved
implementation-plan.md L220: Spec sufficiency — "Local Canon" from normalizers.py, no research matrix ref
implementation-plan.md L227: Files-modified — "8 normalizer-backed providers...3 structural providers unchanged"
Cross-doc sweep: no remaining "research consensus matrix" references in MEU-207 section
```

### Files Modified

| File | Changes |
|------|---------|
| `implementation-plan.md` | L193 inclusion rule, L195-216 split tuple tables, L220 spec sufficiency, L227 files-modified summary |

### Verdict

`corrections_applied` — Round 7 finding resolved. Ready for re-review.

---

## Recheck (2026-05-05) - Codex Plan Review Round 8

**Workflow**: `/plan-critical-review`
**Agent**: `gpt-5.5`
**Scope Note**: Rechecked the Round 9 corrections for the single remaining MEU-207 capability-contract finding. This remains planning-only; execution artifacts were not reviewed.
**Verdict**: `approved`

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|--------------|----------------|
| Inclusion rule, tuple table, and files-modified summary mix normalizer-derived scope with structural carry-forward exceptions | open | Fixed |

### Confirmed Fixes

- `implementation-plan.md:193` now states the MEU-207 inclusion rule explicitly: MEU-207 updates only normalizer-backed or dedicated-normalizer providers, while providers with no normalizer registry entry keep their MEU-184 `supported_data_types` unchanged.
- `implementation-plan.md:195` through `implementation-plan.md:207` now contains a MEU-207-scoped normalizer-derived table with 8 providers. The rows match the local runtime registries checked in `normalizers.py:233`, `normalizers.py:241`, `normalizers.py:245`, and `normalizers.py:861`.
- `implementation-plan.md:210` through `implementation-plan.md:218` now separates unchanged MEU-184 carry-forward providers: Nasdaq Data Link, OpenFIGI, and Tradier. This resolves the prior internal rule conflict.
- `implementation-plan.md:224` and `implementation-plan.md:234` now describe the capability source as local normalizer registry coverage, with 8 normalizer-backed providers updated and 3 structural providers unchanged.
- The MEU-207 FIC validation command returned `4` in `C:\Temp\zorivest\fic-207-recheck-round8.txt`, matching AC-1..AC-4.
- `task.md:36` through `task.md:39` remain Markdown-safe with escaped PowerShell pipes in table-cell validation commands.

### Remaining Findings

None.

### Checklist Results

| Check | Result | Evidence |
|-------|--------|----------|
| PR-1 Plan/task alignment | pass | MEU-207 task row 16 points to the same `supported_data_types` contract now described by the split normalizer-derived and carry-forward tables. |
| PR-2 Not-started confirmation | skipped | User explicitly requested planning-only review and to ignore already-performed execution. |
| PR-3 Task contract completeness | pass | MEU-207 rows 14-17 contain exact receipt-safe validation commands with escaped table-cell pipes. |
| PR-4 Validation realism | pass | The tuple expectations are mechanically checkable against local normalizer registries and service-level dedicated normalizers. |
| PR-5 Source-backed planning | pass | AC-2/AC-3 are sourced to local runtime registries; preserved exceptions are explicitly scoped to MEU-184 carry-forward behavior. |
| PR-6 Handoff/corrections readiness | pass | No open plan-correction findings remain. |

### Residual Risk

- `implementation-plan.md:173` still mentions the research consensus matrix in the problem statement, but the goal, inclusion rule, tuple tables, spec-sufficiency row, and files-modified summary now constrain implementation to local runtime-backed coverage plus explicit MEU-184 carry-forward rows. I do not consider that residual wording blocking.
- This verdict approves the planning additions only. It does not validate the already-performed implementation.

### Verdict

`approved` - the new MEU-207 planning additions now have a coherent, source-backed capability contract and deterministic validation tasks.
