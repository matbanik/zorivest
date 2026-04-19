# [WF-SEGREGATE] Workflow Segregation — Plan vs Execution Mode Split

Split `/planning-corrections` and `/critical-review-feedback` into 4 mode-specific workflows to eliminate mode confusion, prevent size bloat, and enforce mandatory HARD STOP after handoff creation.

**Source basis for non-spec rules:**
- **HARD STOP after handoff**: `Local Canon` — [WF-SEGREGATE] known-issues.md entry, distilled from 2026-04-19 session friction where agent autonomously chained workflows
- **Immutable historical handoffs**: `Local Canon` — AGENTS.md §Handoff continuity ("keep one rolling review handoff file… append updates to the same file instead of creating new variants")
- **Breaking command cutover (4 new replaces 2 old)**: `Human-approved` — user directed the split in the WF-SEGREGATE known issue and approved the implementation plan
- **Write scope separation (plan vs code)**: `Local Canon` — AGENTS.md §Operating Model (PLANNING vs EXECUTION mode separation)

## User Review Required

> [!IMPORTANT]
> **Breaking change to workflow invocations.** After this change, `/planning-corrections` and `/critical-review-feedback` will no longer exist. They are replaced by 4 new slash commands. All active workflow references will be updated, but historical handoff files (which reference old names) will NOT be modified — they are immutable records (`Local Canon` — AGENTS.md §Handoff continuity).

### New Slash Commands

| Old Command | Replacement(s) |
|---|---|
| `/critical-review-feedback` | `/plan-critical-review` + `/execution-critical-review` |
| `/planning-corrections` | `/plan-corrections` + `/execution-corrections` |

### HARD STOP Rule (`Local Canon` — WF-SEGREGATE)

Every new workflow ends with a mandatory `## HARD STOP` section that forbids autonomous chaining into subsequent workflows. The agent must stop and report the handoff path to the user after each workflow completes.

---

## Proposed Changes

### Component 1: New Workflow Files

#### [NEW] [plan-critical-review.md](file:///p:/zorivest/.agent/workflows/plan-critical-review.md)

Extracted from `critical-review-feedback.md` — **plan review mode only**.

- PR-1..PR-6 (Plan Review) + DR (Documentation Review) checklists
- Auto-discovery scoped to `docs/execution/plans/` for plan files
- Output: `-plan-critical-review.md` handoff
- No IR (Implementation Review) checklist — completely removed
- Mandatory HARD STOP section at end

#### [NEW] [execution-critical-review.md](file:///p:/zorivest/.agent/workflows/execution-critical-review.md)

Extracted from `critical-review-feedback.md` — **implementation review mode only**.

- IR-1..IR-6 (Implementation Review) + DR checklists
- Auto-discovery scoped to `.agent/context/handoffs/` for MEU handoffs
- Project-correlation expansion for multi-MEU review sets
- Output: `-implementation-critical-review.md` handoff
- No PR (Plan Review) checklist — completely removed
- Mandatory HARD STOP section at end

#### [NEW] [plan-corrections.md](file:///p:/zorivest/.agent/workflows/plan-corrections.md)

Extracted from `planning-corrections.md` — **plan/design document corrections only**.

- Allowed: Edit plan files, task files, build-plan docs, ADRs, FICs (`Local Canon` — AGENTS.md §Operating Model PLANNING mode)
- Forbidden: Editing production code in `packages/`, `ui/`, `mcp-server/`
- Input: Plan review handoff with findings (from `/plan-critical-review`)
- Output: Updated plan files + corrections handoff
- Mandatory HARD STOP section at end

#### [NEW] [execution-corrections.md](file:///p:/zorivest/.agent/workflows/execution-corrections.md)

Extracted from `planning-corrections.md` — **production code corrections only**.

- Allowed: Edit production code, tests, infrastructure files (`Local Canon` — AGENTS.md §Operating Model EXECUTION mode)
- Forbidden: Editing plan structure or build-plan docs (route to `/plan-corrections`)
- Input: Implementation review handoff with findings (from `/execution-critical-review`)
- Output: Code changes + corrections handoff
- TDD discipline applies: new tests for new fixes (`Local Canon` — AGENTS.md §Testing & TDD Protocol)
- Mandatory HARD STOP section at end

---

### Component 2: Delete Old Workflows

#### [DELETE] [planning-corrections.md](file:///p:/zorivest/.agent/workflows/planning-corrections.md)

Replaced by `plan-corrections.md` and `execution-corrections.md`.

#### [DELETE] [critical-review-feedback.md](file:///p:/zorivest/.agent/workflows/critical-review-feedback.md)

Replaced by `plan-critical-review.md` and `execution-critical-review.md`.

---

### Component 3: Update Cross-References

#### [MODIFY] [AGENTS.md](file:///p:/zorivest/AGENTS.md)

§Workflow Invocation (lines 163-175): Replace 2 old entries with 4 new entries:

```diff
-- `/planning-corrections` → Read and follow `.agent/workflows/planning-corrections.md`
-- `/critical-review-feedback` → Read and follow `.agent/workflows/critical-review-feedback.md`
++ `/plan-corrections` → Read and follow `.agent/workflows/plan-corrections.md`
++ `/execution-corrections` → Read and follow `.agent/workflows/execution-corrections.md`
++ `/plan-critical-review` → Read and follow `.agent/workflows/plan-critical-review.md`
++ `/execution-critical-review` → Read and follow `.agent/workflows/execution-critical-review.md`
```

#### [MODIFY] [session-meta-review.md](file:///p:/zorivest/.agent/workflows/session-meta-review.md)

Lines 39, 198, 225: Update references from old to new workflow names.

#### [MODIFY] [meu-handoff.md](file:///p:/zorivest/.agent/workflows/meu-handoff.md)

Line 13: Update reference from `/critical-review-feedback` to `/execution-critical-review`.

#### [MODIFY] [execution-session.md](file:///p:/zorivest/.agent/workflows/execution-session.md)

Line 76: Update reference from `/critical-review-feedback` to `/execution-critical-review`.

#### [MODIFY] [emerging-standards.md](file:///p:/zorivest/.agent/docs/emerging-standards.md)

Lines 3, 11, 12: Update references from old to new workflow names.

#### [MODIFY] [SKILL.md (pre-handoff-review)](file:///p:/zorivest/.agent/skills/pre-handoff-review/SKILL.md)

Line 14: Update reference from `/planning-corrections` to `/plan-corrections` or `/execution-corrections`.

#### [MODIFY] [README.md (docs/execution)](file:///p:/zorivest/docs/execution/README.md)

Line 26: Update reference from `.agent/workflows/critical-review-feedback.md` to the new plan/execution review workflow names.

#### [MODIFY] [known-issues.md](file:///p:/zorivest/.agent/context/known-issues.md)

Move [WF-SEGREGATE] entry to `known-issues-archive.md` after completion.

---

## Not In Scope

- **Historical handoff files** — These are immutable records and will NOT be modified even though they reference old workflow names. (`Local Canon` — AGENTS.md §Handoff continuity)
- **Session MD files** — Historical records, not active workflows.
- **Conversation logs** — Not modified.

## Verification Plan

### Automated Checks

1. `rg "critical-review-feedback|planning-corrections" AGENTS.md .agent/workflows/ .agent/docs/ .agent/skills/ .agent/roles/ docs/execution/README.md` → 0 matches (excludes old workflow files which will be deleted, excludes historical handoffs/plans)
2. HARD STOP structural compliance (run from repo root):
   ```
   foreach ($f in @('.agent/workflows/plan-critical-review.md','.agent/workflows/execution-critical-review.md','.agent/workflows/plan-corrections.md','.agent/workflows/execution-corrections.md')) { $h2s = Select-String '^## ' $f; $lastH2 = $h2s[-1].Line.Trim(); $raw = Get-Content $f -Raw; $tail = $raw.Substring($raw.IndexOf('## HARD STOP')); $pass = ($lastH2 -eq '## HARD STOP') -and ($tail -match '\[!CAUTION\]') -and ($tail -match 'Do NOT|MUST NOT|forbidden') -and ($tail -match 'handoff'); "$f : $(if($pass){'PASS'}else{'FAIL'})" }
   ```
   → 4 lines, all `PASS` (verifies last-H2 position, CAUTION block presence, anti-chaining language, and handoff-path stop requirement)
3. `Test-Path .agent/workflows/planning-corrections.md` → False (deleted)
4. `Test-Path .agent/workflows/critical-review-feedback.md` → False (deleted)
5. Verify each new workflow is self-contained (no cross-file assembly required)

### Manual Verification

- User reviews the 4 new workflow files for completeness and correctness
- User confirms AGENTS.md workflow invocation section is correct
