---
description: Reusable findings-first critical review workflow for completed work handoffs and related docs/files (consistency, regressions, missing updates, weak verification).
---

# Critical Review Feedback Workflow

Use this workflow when work is already done and you want an adversarial review + feedback handoff (not implementation).

This is the workflow for prompts like:

- "Critically review this handoff and docs for inconsistencies"
- "Check if the claimed changes were actually completed"
- "Find regressions/missed references after a docs refactor"

## Primary Use Case

You provide:

1. A completed work artifact (usually `.agent/context/handoffs/*.md`)
2. The related file set to validate (for example `docs/build-plan/`)

The workflow produces:

1. A **findings-first review**
2. A new **review handoff** in `.agent/context/handoffs/`
3. Optional follow-up fix recommendations (no fixes unless explicitly requested)

---

## Default Role Sequence

1. `orchestrator` (scope + plan)
2. `tester` (evidence/verification commands for docs, links, grep sweeps)
3. `reviewer` (severity-ranked findings and verdict)
4. `coder` (optional, only if user requests fixes after review)

> `researcher` is optional only when external fact-checking is required.
> `guardrail` is usually not required for docs-only review.

---

## Input Contract (What the User Should Provide)

Minimum:

- **Target artifact**: path to the handoff or markdown file that documents completed work

Recommended:

- **Scope paths**: folders/files that should be checked for consistency (for example `docs/build-plan/`)
- **Intent**: what kind of review is wanted (contract drift, missed updates, regressions, validation quality, etc.)

### Example Invocation

```text
Use .agent/workflows/critical-review-feedback.md.
Target artifact: .agent/context/handoffs/2026-02-26-remove-embedded-mode.md
Review scope: docs/build-plan/
Goal: find inconsistencies, missed references, and weak verification claims.
```

### Zorivest Build-Plan Default (Required)

For this repository, when the target artifact describes work on `docs/build-plan/` (including plan/walkthrough/handoff files for build-plan sessions):

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
| Load context and target artifact | `orchestrator` | Scoped review objective + target list | `Get-Content <target>` | `pending` |
| Run evidence sweeps | `tester` | Command outputs (grep/diff/link checks) | `rg`, `git diff`, file reads | `pending` |
| Produce findings-first review | `reviewer` | Severity-ranked findings + verdict | Cross-check line references | `pending` |
| Write review handoff | `reviewer` | `.agent/context/handoffs/{date}-{slug}-critical-review.md` | file created + readable | `pending` |
| Apply fixes (optional) | `coder` | patch(es) for accepted findings | targeted checks after edits | `pending` |

---

## Workflow Steps

## Step 1: Scope the Review (Orchestrator)

Define a single objective and out-of-scope items before inspecting files.

Examples:

- Objective: "Validate that embedded-mode removal is complete and consistent across `docs/build-plan`"
- Out-of-scope: "Do not rewrite unrelated build-plan sections"

Also identify the **claimed changes** from the target artifact:

- files changed
- phrases renamed
- sections removed/added
- verification commands/results

---

## Step 2: Load Context and Evidence (Orchestrator + Tester)

Read:

1. Target handoff / artifact
2. Claimed files
3. Relevant related files likely to drift (indexes, references, downstream links)
4. Current diffs (`git diff`) for the claimed files when available

For Zorivest build-plan review sessions (required):

5. The actual changed `docs/build-plan/*` files referenced or implied by the artifact
6. `git status --short -- docs/build-plan` and `git diff -- docs/build-plan/<claimed-files>` when applicable
7. If files are untracked or `git diff` is incomplete, perform direct file-state checks (counts, anchors, headings, annotation blocks, etc.) against `docs/build-plan/*`

For Zorivest sessions, follow session discipline before review:

1. `SOUL.md`
2. `pomera_notes` search (`Zorivest`)
3. `.agent/context/current-focus.md`
4. `.agent/context/known-issues.md`

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
4. **Verification quality**
   - Are handoff checks strong enough, or do they create false confidence?
5. **Evidence quality**
   - Are diffs/commands reproducible and auditable?
6. **Actual build-plan file changes (Zorivest required when in scope)**
   - Did the claimed changes materially appear in `docs/build-plan/*`, with evidence tied to file lines/state?

### Suggested Commands (Adapt Per Task)

```powershell
# 1) Read the claimed artifact and target files
Get-Content .agent/context/handoffs/<target>.md
Get-Content docs/build-plan/<file>.md

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

1. Scope reviewed
2. Commands executed
3. Findings with file/line references
4. Explicit verdict (`approved` or `changes_required`)
5. Concrete follow-up actions

---

## Step 6: Save Session Memory (Optional but Recommended)

Save a short `pomera_notes` entry summarizing:

- what was reviewed
- key findings
- whether fixes were applied or deferred

If `.agent/context/current-focus.md` already has unrelated user edits in progress, do not overwrite it during a review-only session.

---

## Hard Rules

1. **Do not silently fix issues** during the review workflow unless the user explicitly asks for fixes.
2. **Do not approve based on phrase-only grep checks** when heading renames or link anchors are involved.
3. **Do not treat the handoff as source of truth**; treat file state + diffs as source of truth.
4. **Do not bury findings behind summaries**; findings come first.
5. **For Zorivest build-plan work, always inspect and cite actual `docs/build-plan/*` file changes** (or explicit file-state checks when diffs are unavailable). A handoff-only review is invalid.

---

## Output Contract

Return to the user:

- Findings (severity-ranked, file/line references)
- Open questions / assumptions
- Review verdict (`changes_required` or `approved`)
- Residual risk statement
- Path to the newly created review handoff

If no findings are discovered, say so explicitly and list remaining verification gaps (if any).

---

## When to Switch Workflows

- Use `.agent/workflows/orchestrated-delivery.md` if the user asks for fixes/implementation.
- Use this workflow first when the user says "review", "critically review", "find inconsistencies", or "validate claimed changes".
