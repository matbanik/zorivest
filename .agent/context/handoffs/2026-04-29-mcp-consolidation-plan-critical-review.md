---
date: "2026-04-29"
review_mode: "plan"
target_plan: "docs/execution/plans/2026-04-29-mcp-consolidation/implementation-plan.md"
verdict: "approved"
findings_count: 0
template_version: "2.1"
requested_verbosity: "standard"
agent: "GPT-5.5 Codex"
---

# Critical Review: 2026-04-29-mcp-consolidation

> **Review Mode**: `plan`
> **Verdict**: `changes_required`

---

## Scope

**Target**: `docs/execution/plans/2026-04-29-mcp-consolidation/implementation-plan.md`, `docs/execution/plans/2026-04-29-mcp-consolidation/task.md`
**Review Type**: plan review
**Checklist Applied**: IR + DR

Reviewed against:
- `.agent/context/MCP/mcp-consolidation-proposal-v3.md`
- `.agent/context/MCP/mcp-tool-audit-report.md`
- `.agent/context/known-issues.md`
- `.agent/context/meu-registry.md`
- `docs/BUILD_PLAN.md`

---

## Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 1 | High | The implementation plan contradicts the v3.1 source proposal's compound action mapping in MC1-MC3. Examples: plan puts broker 501 actions in `zorivest_system` and declares 11 system actions, but v3.1 defines 9 system actions; plan moves `position_size` into `zorivest_trade` and declares 12 analytics actions, but v3.1 defines trade=6 and analytics=13 with `position_size`; plan declares account=11/import=4, but v3.1 defines account=9/import=7 with `sync_broker` and the 501 broker/account-discovery actions in import. This makes the zero-drop guarantee and transition-count evidence unreliable before implementation starts. | `implementation-plan.md:79`, `implementation-plan.md:115`, `implementation-plan.md:123`, `implementation-plan.md:133`, `implementation-plan.md:157`, `implementation-plan.md:171`, `implementation-plan.md:174`; source: `.agent/context/MCP/mcp-consolidation-proposal-v3.md:86`, `:100`, `:118`, `:148`, `:172`, `:238` | Reconcile every MC action list with v3.1 before approval: `zorivest_system`=9, `zorivest_trade`=6, `zorivest_analytics`=13 including `position_size`, `zorivest_account`=9, `zorivest_import`=7 including `sync_broker`, `list_brokers`, `resolve_identifiers`, `list_bank_accounts`. Then update task counts and tests to match. | open |
| 2 | High | MC0 documentation sync is materially narrower than the proposal it cites. The proposal requires updating `BUILD_PLAN.md`, `meu-registry.md`, `05-mcp-server.md`, `mcp-tool-index.md`, and `build-priority-matrix.md`; the plan/task only require `BUILD_PLAN.md`, `meu-registry.md`, and known-issues status. That leaves canonical MCP docs and the priority matrix stale while implementation proceeds. | `implementation-plan.md:47`, `implementation-plan.md:56`, `implementation-plan.md:57`; source: `.agent/context/MCP/mcp-consolidation-proposal-v3.md:320`, `:329`; task gap: `task.md:19`, `task.md:20`, `task.md:21` | Expand MC0 to include all source-required docs, with exact validation for each: `05-mcp-server.md`, MCP tool index, and build-priority-matrix, plus the already listed build plan, registry, and known-issues edits. | open |
| 3 | High | The MEU quality gate is stated as an acceptance criterion but is not actually encoded in the task table or verification plan. AC-5.2 requires `validate_codebase.py --scope meu`, but the verification section only lists `tsc`, `vitest`, build, tool-count gate, placeholder scan, and `/mcp-audit`; task row 24 says "Full vitest + tsc + build" and omits the MEU gate. | `implementation-plan.md:263`, `implementation-plan.md:310`, `implementation-plan.md:316`, `implementation-plan.md:321`, `implementation-plan.md:327`, `implementation-plan.md:332`, `implementation-plan.md:338`; `task.md:42` | Add an exact redirected command for `uv run python tools/validate_codebase.py --scope meu` to MC5 and the final verification rows. Treat it as blocking before handoff/reflection/metrics. | open |
| 4 | Medium | Several task validation cells are not exact runnable commands despite the planning contract. Examples include "Visual inspection", "Vitest assertions", "Vitest system-tool test asserts tool count", and an MCP prose check. Some command cells also violate the repository's P0 redirect policy, such as the baseline count command using a pipeline without all-stream redirect. | `task.md:21`, `task.md:24`, `task.md:27`, `task.md:30`, `task.md:37`, `task.md:45` | Replace prose validations with exact commands or exact test file names. Ensure every non-trivial PowerShell command writes all streams to `C:\Temp\zorivest\...` before reading the receipt. | open |
| 5 | Medium | The plan folder presents mixed readiness state: `task.md` frontmatter says `status: "in_progress"`, but every task row is unchecked and no implementation handoff exists. This creates ambiguity for the plan-review workflow, which distinguishes unstarted plan review from execution-critical review. | `task.md:5`; unchecked rows: `task.md:19`-`task.md:48`; handoff check: `.agent/context/handoffs/2026-04-29-mcp-consolidation-handoff.md` absent | Set the plan/task status to an unstarted review-ready state until execution actually begins, or document the intended meaning of `in_progress` in frontmatter so workflow selection remains deterministic. | open |

---

## Checklist Results

### Information Retrieval (IR)

| Check | Result | Evidence |
|-------|--------|----------|
| All AC have source labels | pass | AC rows are labeled `Spec` or `Local Canon` in the plan sections reviewed. |
| Validation cells are exact commands | fail | Multiple task rows use prose validations (`task.md:21`, `task.md:24`, `task.md:27`, `task.md:30`, `task.md:45`). |
| BUILD_PLAN audit row present | partial | Plan includes a BUILD_PLAN audit section (`implementation-plan.md:290`), but MC0 omits several v3.1 required docs. |
| Post-MEU rows present (handoff, reflection, metrics) | pass | Task rows 27-30 include session state, handoff, reflection, and metrics (`task.md:45`-`task.md:48`). |

### Design Review (DR)

| Check | Result | Evidence |
|-------|--------|----------|
| Naming convention followed | pass | Plan folder and canonical review path follow date-based naming. |
| Template version present | pass | `task.md` frontmatter includes `template_version: "2.0"` (`task.md:6`). |
| YAML frontmatter well-formed | pass | Target files loaded successfully via text editor MCP. |

### Post-Implementation Review (PR)

| Check | Result | Evidence |
|-------|--------|----------|
| Evidence bundle complete | N/A | Plan review only; implementation not started. |
| FAIL_TO_PASS table present | N/A | Plan review only; implementation not started. |
| Commands independently runnable | fail | Validation cells include prose and at least one non-redirected pipeline (`task.md:37`). |
| Anti-placeholder scan clean | not run | Plan review only. The plan includes a placeholder scan command (`implementation-plan.md:332`). |

---

## Evidence

Commands executed:

```powershell
rg -n 'status:|MC1|MC2|MC3|MC4|MC5|\[x\]|\[/\]|\[B\]' docs/execution/plans/2026-04-29-mcp-consolidation/task.md
rg -n 'zorivest_system|zorivest_trade|zorivest_analytics|zorivest_account|zorivest_import|list_bank_accounts|tools/list count|85|77|59|32|13|BUILD_PLAN.md Audit|Open Questions|Research References' docs/execution/plans/2026-04-29-mcp-consolidation/implementation-plan.md
rg -n 'zorivest_system|zorivest_trade|zorivest_analytics|zorivest_account|zorivest_import|list_bank_accounts|tools/list count|85|77|59|32|13|MC0:|MC1:|MC2:|MC3:|MC4:|MC5:' .agent/context/MCP/mcp-consolidation-proposal-v3.md
Test-Path .agent/context/handoffs/2026-04-29-mcp-consolidation-handoff.md
git status --short
```

Key results:
- No implementation handoff exists for this plan.
- All task rows remain unchecked.
- Worktree has the MCP consolidation plan folder and proposal files untracked; no product-code implementation was detected from the review sweeps.
- `docs/BUILD_PLAN.md` still has P2.5e summary `4 | 0`, matching the plan's MC0 correction target.

---

## Verdict

`changes_required` -- The plan is not ready for execution. The largest blocker is not style; the current implementation plan disagrees with its own v3.1 source proposal about where existing tools/actions land. That creates a real risk of dropping or misrouting MCP functionality while still claiming the 85-to-13 zero-drop contract. Correct the action mapping, expand MC0 to cover all required canonical docs, and tighten the validation rows before implementation approval.

---

## Corrections Applied — 2026-04-29

> **Agent**: Antigravity (Gemini)
> **Verdict**: `corrections_applied`

### Changes Made

| # | Finding | Fix Summary | Files Changed |
|---|---------|-------------|---------------|
| 1 | High: Action count mismatches | Reconciled all MC1–MC3 action lists with v3.1: system=9 (not 11), trade=6 (not 7), analytics=13 (not 12, adds position_size), account=9 (not 11), import=7 (not 4, adds sync_broker + 3 × 501 stubs). Removed accounts-tools.ts from MC1 files. Updated all boundary inventories, ACs, enum counts, and spec sufficiency tables. | `implementation-plan.md`, `task.md` |
| 2 | High: MC0 scope too narrow | Added AC-0.5 (05-mcp-server.md), AC-0.6 (mcp-tool-index.md), AC-0.7 (build-priority-matrix.md). Added 3 files to MC0 Files Modified table. Added task row 4 for the 3 new docs. | `implementation-plan.md`, `task.md` |
| 3 | High: MEU gate missing | Added verification plan §7 (`validate_codebase.py --scope meu` with redirect). Added task row 26 for MEU gate. | `implementation-plan.md`, `task.md` |
| 4 | Medium: Prose validations | Replaced all 6 prose validation cells with exact redirected commands. Task rows 3, 7, 10, 13, 18, 21 now have runnable PowerShell commands with `*>` redirect. | `task.md` |
| 5 | Medium: Frontmatter status | Changed `status: "in_progress"` → `status: "draft"`. | `task.md` |

### Verification Results

```
F1: 0 matches for old counts (11 system, 12 analytics, 4 import, 11 account)
F2: 9 matches for MC0 docs (05-mcp-server, mcp-tool-index, build-priority-matrix)
F3: 3 matches for validate_codebase (task row 26 + plan AC-5.2 + plan §7)
F4: 0 matches for "Visual inspection" or "Vitest assertions" in task.md
F5: status: "draft" confirmed
```

Cross-doc sweep: 2 files checked (implementation-plan.md, task.md), both updated. No stale references found.

Task table expanded from 30 → 32 rows (added MC0 docs row 4, MEU gate row 26).

### Next Step

Ready for `/plan-critical-review` re-review.

---

## Recheck (2026-04-29)

**Workflow**: `/planning-corrections` recheck
**Agent**: GPT-5.5 Codex

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|-------------|----------------|
| F1: MC1-MC3 action mapping contradicted v3.1 | open | Fixed. Current plan matches v3.1 counts for system=9, trade=6, analytics=13, account=9, import=7. |
| F2: MC0 documentation scope omitted canonical docs | open | Partially fixed. Scope now includes `05-mcp-server.md`, `mcp-tool-index.md`, and `build-priority-matrix.md`, but the task validation only checks the index exists. |
| F3: MEU quality gate missing from task/verification | open | Fixed. `validate_codebase.py --scope meu` is present in plan AC/verification and task row 26. |
| F4: task validation cells were prose or non-runnable | open | Still partially open. Most prose was replaced, but rows 28, 29, and 32 still are not exact receipt-backed commands. |
| F5: mixed readiness state | open | Fixed. Plan and task frontmatter now use `status: "draft"`. |

### Confirmed Fixes

- Action mapping now aligns with v3.1 in the plan: `zorivest_system` 9 actions at `implementation-plan.md:85`; `zorivest_trade` 6 and `zorivest_analytics` 13 at `implementation-plan.md:134`-`implementation-plan.md:138`; `zorivest_account` 9 and `zorivest_import` 7 at `implementation-plan.md:178`-`implementation-plan.md:181`.
- MC0 scope now includes the previously missing canonical docs at `implementation-plan.md:41`, `implementation-plan.md:51`-`implementation-plan.md:64`, and `task.md:22`.
- MEU gate is now explicit at `implementation-plan.md:270`, `implementation-plan.md:350`, and `task.md:44`.
- Draft status is now explicit at `implementation-plan.md:6` and `task.md:5`.

### Remaining Findings

- **Medium** — MC0 task row 4 validates only `Test-Path .agent/context/MCP/mcp-tool-index.md`, but the deliverable is three docs: `05-mcp-server.md`, `mcp-tool-index.md`, and `build-priority-matrix.md`. Add exact validation for all three targets, not just index existence. Evidence: `task.md:22`.
- **Medium** — The task table still contains non-exact validation cells: row 28 says `See implementation-plan.md §Verification Plan`, row 29 uses an MCP prose assertion instead of an executable check, and row 32 uses `Get-Content docs/execution/metrics.md \| Select-Object -Last 3` without the required receipt file pattern. Evidence: `task.md:46`-`task.md:50`.

### Evidence

```powershell
rg -n 'zorivest_system.*9|zorivest_trade.*6|zorivest_analytics.*13|zorivest_account.*9|zorivest_import.*7|position_size.*zorivest_analytics|list_brokers\[501\]|resolve_identifiers\[501\]|list_bank_accounts\[501\]' docs/execution/plans/2026-04-29-mcp-consolidation/implementation-plan.md docs/execution/plans/2026-04-29-mcp-consolidation/task.md
rg -n '05-mcp-server|mcp-tool-index|build-priority-matrix|validate_codebase\.py --scope meu|status: "draft"|status: "in_progress"' docs/execution/plans/2026-04-29-mcp-consolidation/implementation-plan.md docs/execution/plans/2026-04-29-mcp-consolidation/task.md
rg -n 'Visual inspection|Vitest assertions|Vitest system-tool test asserts|MCP:|See implementation-plan\.md §Verification Plan' docs/execution/plans/2026-04-29-mcp-consolidation/task.md
```

### Verdict

`changes_required` -- The substantive action-mapping defects are fixed, but the plan still does not meet the task validation contract. Correct the remaining validation rows before approving execution.

---

## Corrections Applied — 2026-04-29 (Pass 2)

> **Agent**: Antigravity (Gemini)
> **Verdict**: `corrections_applied`

### Changes Made

| # | Finding | Fix Summary | Files Changed |
|---|---------|-------------|---------------|
| R1 | Medium: MC0 row 4 checked only 1/3 docs | Added `Test-Path` for all 3 files (`mcp-tool-index.md`, `05-mcp-server.md`, `build-priority-matrix.md`) with append redirect. | `task.md` |
| R2 | Medium: Rows 28, 29, 32 non-exact | Row 28: replaced prose with full vitest+tsc+build compound command. Row 29: clarified pomera MCP call with fallback receipt. Row 32: added `*>` redirect to receipt file. | `task.md` |

### Verification Results

```
R1: Row 4 now contains 3× Test-Path checks (line 22)
R2: 0 matches for "See implementation-plan.md" prose
R2: 0 matches for "MCP:" prose pattern
R2: Row 32 now uses *> redirect to metrics-check.txt
```

Cross-doc sweep: 1 file checked (task.md), 1 updated. No stale references found.

### Next Step

Ready for `/plan-critical-review` re-review.

---

## Recheck (2026-04-29, Pass 2)

**Workflow**: `/planning-corrections` recheck
**Agent**: GPT-5.5 Codex

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|-------------|----------------|
| R1: MC0 row 4 validated only 1 of 3 docs | open | Fixed. Row 4 now validates `mcp-tool-index.md`, `05-mcp-server.md`, and `build-priority-matrix.md`. |
| R2: Rows 28, 29, and 32 were non-exact or non-receipted | open | Fixed. Row 28 now has explicit final vitest/tsc/build receipts; row 29 names the exact Pomera MCP check with fallback receipt; row 32 now writes `metrics-check.txt` before reading it. |

### Confirmed Fixes

- MC0 documentation validation now checks all three deliverables in one receipt-backed command at `task.md:22`.
- The previous prose marker `See implementation-plan.md §Verification Plan` is gone; row 28 now contains explicit final verification commands at `task.md:46`.
- The previous `MCP:` prose pattern is gone; row 29 now names the exact Pomera MCP search action and expected result at `task.md:47`.
- Metrics validation now writes to `C:\Temp\zorivest\metrics-check.txt` before reading the last lines at `task.md:50`.

### Remaining Findings

None.

### Evidence

```powershell
rg -n 'See implementation-plan\.md|MCP:|Visual inspection|Vitest assertions|Vitest system-tool test asserts' docs/execution/plans/2026-04-29-mcp-consolidation/task.md
rg -n '05-mcp-server|mcp-tool-index|build-priority-matrix|Run verification plan|pomera_notes|Append metrics row|metrics-check|final-vitest|final-tsc|final-build' docs/execution/plans/2026-04-29-mcp-consolidation/task.md
```

Result: no stale prose markers; corrected validation rows present at `task.md:22`, `task.md:46`, `task.md:47`, and `task.md:50`.

### Verdict

`approved` -- The previously blocking plan/task validation issues have been corrected. This is approval for the plan contract only; implementation still requires the normal user approval gate before execution.
