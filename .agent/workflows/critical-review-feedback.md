---
description: Reusable findings-first critical review workflow for completed work handoffs, correlated multi-handoff project sets, and related docs/files (consistency, regressions, missing updates, weak verification).
---

# Critical Review Feedback Workflow

Use this workflow when work is already done and you want an adversarial review + feedback handoff (not implementation). The agent automatically discovers what to review — no file paths required — and expands from the seed handoff to the full correlated project handoff set when one project produced multiple MEU handoffs.

This is the workflow for prompts like:

- "Critically review the latest handoff"
- "Check if the claimed changes were actually completed"
- "Find regressions/missed references after a docs refactor"

// turbo-all

## Prerequisites

Read these files in order:

1. `SOUL.md`
2. `GEMINI.md`
3. `AGENTS.md`
4. `.agent/context/current-focus.md`
5. `.agent/context/known-issues.md`
6. `pomera_notes` search (`Zorivest`, `Memory/Session/*`, `Memory/Decisions/*`)

---

## Role Sequence

1. `orchestrator` (scope + auto-discovery)
2. `tester` (evidence/verification commands for docs, links, grep sweeps)
3. `reviewer` (severity-ranked findings and verdict)

> `researcher` is optional only when external fact-checking is required.
> `guardrail` is usually not required for docs-only review.
> **No coder role.** This workflow produces findings only — never fixes. Use `/planning-corrections` to resolve findings.

---

## Auto-Discovery (No User Input Required)

The agent discovers the review target automatically. The user only needs to invoke the workflow — no file paths required.

### Discovery Steps

```powershell
# 1. Find most recent WORK handoffs (exclude review artifacts to prevent review-of-review)
Get-ChildItem .agent/context/handoffs/*.md -Exclude README.md,TEMPLATE.md |
  Where-Object { $_.Name -notmatch '(critical-review|corrections|recheck)' } |
  Sort-Object LastWriteTime -Descending | Select-Object -First 3

# 2. Find execution plan folder related to the discovered handoff
#    Match by date prefix or slug from the handoff filename
Get-ChildItem docs/execution/plans/ -Directory |
  Sort-Object LastWriteTime -Descending | Select-Object -First 3
```

From the results:

- **Primary review target**: the most recent work handoff (by `LastWriteTime`)
- **Secondary scope**: the execution plan folder whose date/slug matches the handoff. If no match, use the most recent plan folder as fallback.
- If the handoff references specific files or folders, those become **additional scope**

### Correlation Rule

The agent must correlate the handoff and plan folder — not blindly pair the newest of each. Use the date prefix and slug to match. For example, `2026-03-07-meu-2-enums.md` pairs with `docs/execution/plans/2026-03-07-domain-entities-ports/` if that plan contains MEU-2.

### Project-Integrated Handoff Expansion (Required)

When the correlated plan folder represents a multi-MEU project, the latest handoff is only the **seed** for discovery — it is not the full review scope.

Expand the review to the full correlated handoff set when any of these are true:

1. `implementation-plan.md` has a `Handoff Naming` section with multiple handoff paths
2. `task.md` has multiple `Create handoff:` checklist items
3. The plan, reflection, or registry states that multiple MEUs were executed in the same project
4. Multiple same-date sequenced handoffs clearly belong to the correlated plan folder

When expansion triggers, required scope becomes:

- every handoff produced by that project
- the correlated `implementation-plan.md` and `task.md`
- shared project artifacts updated by the project (`meu-registry.md`, reflection, metrics, session summary artifacts)
- all changed files claimed across the full handoff set

The reviewer must explicitly say how the sibling handoffs were discovered (for example: plan `Handoff Naming`, task checklist, matching sequenced handoff files).

### Scope Override

If the user provides explicit paths, use those instead of auto-discovery. Auto-discovery is the default when no paths are given.

If the user provides one handoff path from a multi-MEU integrated project but does not explicitly say `only` that file, default to expanding to the full correlated handoff set.

### Zorivest Build-Plan Default (Required)

When the target artifact describes work on `docs/build-plan/` (including plan/walkthrough/handoff files for build-plan sessions):

- Treat `docs/build-plan/` as **required review scope** even if the user only provides `.agent/context/handoffs/*.md` files.
- Always inspect the **actual `docs/build-plan` file state/changes** (not just handoff claims).
- If `git diff` is not sufficient (for example untracked files), use direct file reads + deterministic checks and explicitly say so.

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
| Auto-discover review targets | `orchestrator` | Seed handoff + correlated plan folder + expanded handoff set (if multi-MEU) | `Get-ChildItem` commands above | `pending` |
| Load context and target artifact | `orchestrator` | Scoped review objective + target list | `Get-Content <target>` | `pending` |
| Run evidence sweeps | `tester` | Command outputs (grep/diff/link checks) | `rg`, `git diff`, file reads | `pending` |
| Produce findings-first review | `reviewer` | Severity-ranked findings + verdict | Cross-check line references | `pending` |
| Write review handoff | `reviewer` | `.agent/context/handoffs/{date}-{slug}-critical-review.md` | file created + readable | `pending` |

---

## Workflow Steps

## Step 1: Discover and Scope the Review (Orchestrator)

Run the auto-discovery commands to identify the seed handoff and correlated plan folder. Verify the handoff–plan correlation before proceeding, then enumerate the full handoff set when the project is multi-MEU. Then define:

- **Objective**: what the review is checking (contract drift, missed updates, regressions, validation quality, etc.)
- **Out-of-scope**: what to exclude

Also identify the **claimed changes** from every artifact in scope:

- files changed
- phrases renamed
- sections removed/added
- verification commands/results

---

## Step 2: Load Context and Evidence (Orchestrator + Tester)

Read:

1. Seed handoff / artifact (auto-discovered or user-specified)
2. Correlated execution plan (`implementation-plan.md` and `task.md` from `docs/execution/plans/`)
3. Every sibling handoff identified from the correlated project
4. Claimed files from the full handoff set
5. Relevant related files likely to drift (indexes, references, downstream links)
6. Current diffs (`git diff`) for the claimed files when available

For Zorivest build-plan review sessions (required):

7. The actual changed `docs/build-plan/*` files referenced or implied by the artifact
8. `git status --short -- docs/build-plan` and `git diff -- docs/build-plan/<claimed-files>` when applicable
9. If files are untracked or `git diff` is incomplete, perform direct file-state checks (counts, anchors, headings, annotation blocks, etc.) against `docs/build-plan/*`

---

## Step 3: Run Critical Verification Sweeps (Tester)

Use fast, reproducible command checks. Prefer `rg`.

### Required Sweep Types (Docs/Handoff Reviews)

1. **Claim verification**
   - Did the files/lines/phrases mentioned in the handoff actually change?
2. **Residual references**
   - Old names/phrases/slugs/anchors still present?
3. **Cross-file consistency**
   - Renamed headings updated in downstream links/indexes?
4. **Cross-handoff consistency**
   - Shared totals, phase-gate claims, registry state, and artifact timing consistent across the full project handoff set?
5. **Verification quality**
   - Are handoff checks strong enough, or do they create false confidence?
6. **Evidence quality**
   - Are diffs/commands reproducible and auditable?
7. **Actual build-plan file changes (Zorivest required when in scope)**
   - Did the claimed changes materially appear in `docs/build-plan/*`, with evidence tied to file lines/state?

### Suggested Commands (Adapt Per Task)

```powershell
# 1) Read the claimed artifact and target files
Get-Content .agent/context/handoffs/<target>.md
Get-Content docs/execution/plans/<project>/implementation-plan.md

# 2) Check exact and variant phrases (space + slug forms)
rg -n -i "embedded mode|embedded-mode|standalone mode|standalone-mode" docs/build-plan

# 3) Find stale anchors after heading renames
rg -n "old-anchor-slug" docs/build-plan

# 4) Inspect actual diffs for claimed files
git diff -- docs/build-plan/<file1>.md docs/build-plan/<file2>.md

# 5) List current build-plan changes (helps catch untracked files)
git status --short -- docs/build-plan

# 6) Search for handoff-specific links in canonical docs (portability risk)
rg -n "\.agent/context/handoffs" docs/build-plan
```

> If a markdown link checker is available, run it. If not, do targeted anchor checks with `rg`.

---

## Step 4: Adversarial Review (Reviewer)

Use the reviewer role output contract and report **findings first**.

### Priorities (in order)

1. Broken behavior/contracts (including broken links/anchors in docs)
2. Contradictions between handoff claims and actual file state
3. Missed downstream updates (indexes, references, summaries, counts)
4. Weak or misleading verification evidence
5. Residual risk / testing gaps

### Severity Guidance (Docs Reviews)

- `Critical`: Dangerous instructions/security regressions or decisions documented incorrectly
- `High`: Broken navigation/anchors, incorrect contracts, false implementation claims
- `Medium`: Portability, maintainability, or verification-quality issues
- `Low`: Auditability, wording, minor evidence quality gaps

### Docs Review Checklist (run every time)

| # | Check | What To Look For |
|---|---|---|
| DR-1 | Claim-to-state match | Handoff says a change happened and file state proves it |
| DR-2 | Residual old terms | Old phrase/slug variants still present (`foo bar` and `foo-bar`) |
| DR-3 | Downstream references updated | Indexes, cross-links, and anchors updated after rename/move |
| DR-4 | Verification robustness | Handoff checks would actually catch regressions introduced by the change |
| DR-5 | Evidence auditability | Commands/diffs are reproducible (not placeholders only) |

> If code changes are also in scope, additionally apply the reviewer role's Adversarial Verification Checklist (AV-1..AV-5).

---

## Step 5: Write the Review Handoff (Reviewer)

Create a new handoff in:

`.agent/context/handoffs/{YYYY-MM-DD}-{task-slug}-critical-review.md`

Use `.agent/context/handoffs/TEMPLATE.md`, but for review-only tasks:

- `Coder Output`: note "No product changes; review-only"
- `Tester Output`: include grep/diff/link-check commands and failures found
- `Reviewer Output`: findings by severity, questions, verdict, residual risk

### Required Review Handoff Content

1. Scope reviewed (including auto-discovered targets and correlation rationale)
2. Commands executed
3. Findings with file/line references
4. Explicit verdict (`approved` or `changes_required`)
5. Concrete follow-up actions

---

## Step 6: Save Session Memory (Optional but Recommended)

Save a short `pomera_notes` entry summarizing:

- what was reviewed
- key findings
- whether fixes should be applied via `/planning-corrections`

If `.agent/context/current-focus.md` already has unrelated user edits in progress, do not overwrite it during a review-only session.

---

## Hard Rules

1. **Never fix issues during this workflow.** This workflow produces findings only. Use `/planning-corrections` to resolve findings.
2. **Do not approve based on phrase-only grep checks** when heading renames or link anchors are involved.
3. **Do not treat the handoff as source of truth**; treat file state + diffs as source of truth.
4. **Do not bury findings behind summaries**; findings come first.
5. **For Zorivest build-plan work, always inspect and cite actual `docs/build-plan/*` file changes** (or explicit file-state checks when diffs are unavailable). A handoff-only review is invalid.
6. **When a correlated project produced multiple MEU handoffs, load all of them.** The newest work handoff is only the discovery seed.
7. **Never review a review.** Auto-discovery excludes `*critical-review*`, `*-corrections*`, and `*-recheck*` handoffs. Only work handoffs are valid targets.

---

## Output Contract

Return to the user:

- Auto-discovered targets (what was reviewed, why, and how handoff–plan were correlated)
- Findings (severity-ranked, file/line references)
- Open questions / assumptions
- Review verdict (`changes_required` or `approved`)
- Residual risk statement
- Path to the newly created review handoff

If no findings are discovered, say so explicitly and list remaining verification gaps (if any).

---

## Orchestration Flow

This workflow is part of a three-workflow orchestration cycle:

1. `/create-plan` → plan and execute new work
2. `/critical-review-feedback` → review completed work (this workflow)
3. `/planning-corrections` → resolve findings from this workflow

When to switch:

- Use `/planning-corrections` if the verdict is `changes_required` and the user wants fixes applied.
- Use `/create-plan` to start new implementation work.
