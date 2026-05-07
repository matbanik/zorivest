---
description: Plan-review-only critical review workflow. Reviews unstarted execution plans for accuracy, consistency, and readiness before implementation begins.
---

# Plan Critical Review Workflow

Use this workflow to adversarially review an **unstarted execution plan** before implementation begins. This workflow produces findings only — it never fixes issues or reviews completed implementation work.

This is the workflow for prompts like:

- "Review the newest plan before implementation starts"
- "Check the implementation plan for consistency"
- "Verify the task contract is correct"

// turbo-all
// NOTE: turbo-all sets SafeToAutoRun=true for non-destructive commands (rg, Get-Content, etc.).
// It does NOT override AGENTS.md §Commits: "Never auto-commit." Git commit/push still requires explicit user direction.

## Write Scope (Non-Negotiable)

This is a review-only workflow.

Allowed file writes:

- `.agent/context/handoffs/{plan-folder-name}-plan-critical-review.md`
- optional `pomera_notes` session memory

Forbidden file writes:

- all product code (`packages/`, `ui/`, `mcp-server/`)
- tests
- docs outside the canonical review handoff
- plan files
- existing work handoffs under review

If a finding suggests a fix, record it in the canonical review handoff and stop. Do not patch the repo. Use `/plan-corrections` for fixes.

---

## Role Sequence

1. `orchestrator` (scope + auto-discovery)
2. `tester` (evidence/verification commands for docs, links, grep sweeps)
3. `reviewer` (severity-ranked findings and verdict)

> `researcher` is optional only when external fact-checking is required.
> `guardrail` is usually not required for docs-only review.
> **No coder role.** This workflow produces findings only — never fixes. Use `/plan-corrections` to resolve findings.

---

## Auto-Discovery (No User Input Required)

The agent discovers the review target automatically. The user only needs to invoke the workflow — no file paths required.

### Discovery Steps

```powershell
# 1. Find recent execution plan folders
Get-ChildItem docs/execution/plans/ -Directory |
  Sort-Object LastWriteTime -Descending | Select-Object -First 5

# 2. Inspect the newest candidate plan's task state
Get-Content docs/execution/plans/<candidate>/task.md

# 3. Confirm the plan is genuinely unstarted
# - implementation tasks are still `pending` / unchecked
# - no MEU handoff paths created by the plan exist yet
# - no task items indicate completed coding, testing, or handoff creation
```

### Mode Confirmation

Choose this workflow (plan review) when all of the following are true:

1. No correlated work handoff exists yet for that plan
2. `task.md` shows implementation has not started yet
3. The user did not explicitly request review of a completed handoff

If implementation handoffs already exist for the plan, use `/execution-critical-review` instead.

### Scope Override

If the user provides explicit paths, use those instead of auto-discovery.

If the user provides an execution plan path with no `only` constraint, review the full plan folder (`implementation-plan.md` + `task.md`) even if no handoff exists yet.

### Canonical Review File Rule

Derive the review handoff path from the correlated execution plan folder:

- `.agent/context/handoffs/{plan-folder-name}-plan-critical-review.md`

Example: `docs/execution/plans/2026-03-07-commands-events-analytics/` → `.agent/context/handoffs/2026-03-07-commands-events-analytics-plan-critical-review.md`

If the canonical review file already exists, append a new dated section to it instead of creating another handoff file.

---

## Plan Creation Contract (Required)

When creating a plan for this workflow, every task must include:

- `task`
- `owner_role`
- `deliverable`
- `validation` (exact command(s))
- `status`

### Canonical Plan Template

| task | owner_role | deliverable | validation | status |
|---|---|---|---|---|
| Auto-discover review targets | `orchestrator` | Review mode + target plan folder | `Get-ChildItem` commands above + `Get-Content <task.md>` | `pending` |
| Load context and target artifact | `orchestrator` | Scoped review objective + target list | `Get-Content <target>` | `pending` |
| Run evidence sweeps | `tester` | Command outputs (grep/diff/link checks) | `rg`, `git diff`, file reads | `pending` |
| Produce findings-first review | `reviewer` | Severity-ranked findings + verdict | Cross-check line references | `pending` |
| Write or update canonical review handoff | `reviewer` | Canonical review file for the correlated plan folder | file created or updated + readable | `pending` |

---

## Workflow Steps

## Step 1: Discover and Scope the Review (Orchestrator)

Run the auto-discovery commands to verify this is an unstarted plan. Define:

- **Objective**: what the review is checking (contract completeness, validation quality, source traceability, etc.)
- **Out-of-scope**: what to exclude
- **Required scope**: `implementation-plan.md`, `task.md`, and any canonical docs/specs those files cite as authority
- **Additional scope**: registry, prior approved reflections/handoffs, or build-plan docs if the plan depends on them for carry-forward rules

---

## Step 2: Load Context and Evidence (Orchestrator + Tester)

Read:

1. Primary target: the unstarted execution plan folder
2. `implementation-plan.md` and `task.md`
3. Relevant related files likely to drift (indexes, references, downstream links, registry, prior canon)
4. Canonical docs cited as authority by the plan

---

## Step 3: Run Critical Verification Sweeps (Tester)

Use fast, reproducible command checks. Prefer `rg`.

### Required Sweep Types (Plan Review Mode)

1. **Plan-task consistency** — Do `implementation-plan.md` and `task.md` describe the same project scope, task order, and outputs?
2. **Status readiness** — Does file state really indicate not-started work, or has implementation already begun?
3. **Role/ownership consistency** — Does every task include the required role, deliverable, validation command, and status?
4. **Validation specificity** — Are validation commands exact, runnable, and scoped to the work described?
5. **Dependency/order correctness** — Are MEUs sequenced coherently, with no impossible order or missing prerequisites?
6. **Source-traceability** — Are acceptance criteria and non-spec rules tagged to `Spec`, `Local Canon`, `Research-backed`, or `Human-approved` sources?

### Suggested Commands (Adapt Per Task)

```powershell
# 1) Read the primary review artifact and target files
Get-Content <primary-artifact>
Get-Content docs/execution/plans/<project>/implementation-plan.md

# 2) Check cross-references
rg -n "<old-term>" .agent/workflows/ .agent/docs/ AGENTS.md

# 3) Inspect actual diffs for claimed files
git diff -- <files>

# 4) Verify validation commands are runnable
# Manually inspect each task row's validation column
```

---

## Step 4: Adversarial Review (Reviewer)

Use the reviewer role output contract and report **findings first**.

### Plan Review Checklist (Required)

| # | Check | What To Look For |
|---|---|---|
| PR-1 | Plan/task alignment | `implementation-plan.md` and `task.md` describe the same scope and order |
| PR-2 | Not-started confirmation | No file-state evidence that coding/testing/handoffs already began |
| PR-3 | Task contract completeness | Every task has `task`, `owner_role`, `deliverable`, `validation`, `status` |
| PR-4 | Validation realism | Commands are specific enough to prove the intended work |
| PR-5 | Source-backed planning | Rules beyond explicit spec text are tagged to an allowed source basis |
| PR-6 | Handoff/corrections readiness | Multi-MEU handoff paths are explicit when applicable, and review findings can be resolved via `/plan-corrections` |

### Docs Review Checklist (Required)

| # | Check | What To Look For |
|---|---|---|
| DR-1 | Claim-to-state match | Handoff says a change happened and file state proves it |
| DR-2 | Residual old terms | Old phrase/slug variants still present (`foo bar` and `foo-bar`) |
| DR-3 | Downstream references updated | Indexes, cross-links, and anchors updated after rename/move |
| DR-4 | Verification robustness | Handoff checks would actually catch regressions introduced by the change |
| DR-5 | Evidence auditability | Commands/diffs are reproducible (not placeholders only) |
| DR-6 | Cross-reference integrity | Architectural changes are consistent across all canonical docs |
| DR-7 | Evidence freshness | Handoff-claimed counts match reproduced command output |
| DR-8 | Completion vs residual risk | If residual risk acknowledges known gaps, conclusion must NOT say "implementation complete" |

### Severity Guidance

- `Critical`: Dangerous instructions/security regressions or decisions documented incorrectly
- `High`: Incorrect contracts, false implementation claims, or plan that materially misstates scope
- `Medium`: Portability, maintainability, verification-quality, or navigation issues
- `Low`: Auditability, wording, minor evidence quality gaps

---

## Step 5: Write or Update the Canonical Review Handoff (Required Exit Gate)

Write to: `.agent/context/handoffs/{plan-folder-name}-plan-critical-review.md`

If that file already exists, append a new dated review update section.

The workflow is incomplete until the canonical review handoff exists and is readable.

> **Start from** [`.agent/context/handoffs/REVIEW-TEMPLATE.md`](file:///p:/zorivest/.agent/context/handoffs/REVIEW-TEMPLATE.md) (v2.1)
>
> **Verbosity control**: Set `requested_verbosity` in the review YAML frontmatter. See `.agent/docs/context-compression.md §Verbosity Tiers`.

Fill the template sections:
- `Findings` table with severity-ranked findings and file:line references
- `Checklist Results` with PR/DR check outcomes
- `Verdict` with explicit `approved` or `changes_required`

### Required Review Handoff Content

1. Scope reviewed (including auto-discovered targets)
2. Commands executed
3. Findings with file/line references
4. Explicit verdict (`approved` or `changes_required`)
5. Concrete follow-up actions
6. If this is not the first pass, a dated update heading

---

## Pre-Edit Guard

Before any file edit:

1. derive the canonical review handoff path for plan review mode
2. verify the intended edit target exactly matches that canonical handoff path

If the target path is anything else, abort the edit and continue in findings-only mode.

---

## Step 6: Save Session Memory (Optional but Recommended)

Save a short `pomera_notes` entry summarizing:

- what was reviewed
- key findings
- whether fixes should be applied via `/plan-corrections`

---

## Hard Rules

1. **Never fix issues during this workflow.** This workflow produces findings only. Use `/plan-corrections` to resolve findings.
2. **Do not approve based on phrase-only grep checks** when heading renames or link anchors are involved.
3. **Do not treat the handoff as source of truth**; treat file state + diffs as source of truth.
4. **Do not bury findings behind summaries**; findings come first.
5. **Never review a review.** Auto-discovery excludes `*critical-review*`, `*-corrections*`, and `*-recheck*` handoffs as review seeds.
6. **If no implementation handoff exists yet, review the newest unstarted execution plan.** This is a plan-accuracy and consistency review.
7. **When plan-review findings require changes, route the fix phase through `/plan-corrections`.**
8. **One rolling review file per target.** Keep plan-review updates in the same `-plan-critical-review.md` file.
9. **Do not return a final response until the canonical review handoff has been created or updated successfully.**
10. **Do not modify any file unless the Pre-Edit Guard resolves to the canonical review handoff path.**

---

## Done Checklist

- [ ] No product files were modified
- [ ] Canonical review handoff was created or updated
- [ ] Review mode was correctly identified as `plan`
- [ ] Verdict is explicit (`approved` or `changes_required`)
- [ ] Final user response includes the canonical review handoff path

---

## Output Contract

Return to the user:

- Auto-discovered targets (what was reviewed)
- Findings (severity-ranked, file/line references)
- Open questions / assumptions
- Review verdict (`changes_required` or `approved`)
- Residual risk statement
- Path to the created or updated canonical review handoff

---

## Orchestration Flow

This workflow is part of a four-workflow orchestration cycle:

1. `/create-plan` → plan new work
2. `/plan-critical-review` → review a new plan before implementation (this workflow)
3. `/plan-corrections` → resolve plan-review findings
4. `/execution-critical-review` → review completed implementation work

When to switch:

- Use this workflow immediately after `/create-plan` when a new plan needs adversarial review.
- Use `/plan-corrections` if the verdict is `changes_required` and the user wants fixes applied.
- Use `/execution-critical-review` for reviewing implementation handoffs (not plans).

## HARD STOP

> [!CAUTION]
> **Do NOT autonomously chain into `/plan-corrections` or any other workflow after completing this review.** You MUST stop here and report the canonical review handoff path to the user. The user decides what happens next.

**Workflow complete.** Report the handoff path and wait for user direction.

## Completion Timestamp

The **very last line** of the agent's chat response must be the timestamp skill output, copied verbatim.

This is a hard exit requirement for every `/plan-critical-review` response, including short rechecks.

Required sequence:

1. Invoke the timestamp skill by reading `.agent/skills/timestamp/SKILL.md`.
2. Run the stamp script with the Windows redirect-to-file pattern:

```powershell
# // turbo
python .agent/skills/timestamp/scripts/stamp.py *> C:\Temp\zorivest\stamp.txt
```

3. Read `C:\Temp\zorivest\stamp.txt` with the file viewer.
4. Copy the file's single output line verbatim as the final chat line.

No text, bullets, caveats, or sign-off may appear after the timestamp line.

Compressed variant for rechecks:

```text
Recheck appended to <canonical-review-path>. Verdict: <approved|changes_required>. Key evidence: <one sentence>.
🕐 Completed: YYYY-MM-DD HH:MM (TZ)
```

The compressed variant still requires invoking the timestamp skill and copying its real output verbatim for the last line.
