---
description: Reusable findings-first critical review workflow for unstarted execution plans, completed work handoffs, correlated multi-handoff project sets, and related docs/files (accuracy, consistency, regressions, missing updates, weak verification).
---

# Critical Review Feedback Workflow

Use this workflow when you want an adversarial review of either:

- a new execution plan that has not started yet, or
- completed work that already produced handoff artifacts

Review continuity is required:

- keep one rolling review handoff file per execution plan folder for plan-review passes
- keep one rolling review handoff file per execution plan folder for project-level implementation critique/recheck passes
- append dated updates to that same file; do not create `-recheck`, `-final`, `-approved`, or similarly fragmented follow-up files for the same target

The agent automatically discovers what to review when no paths are provided. Auto-discovery starts from `docs/execution/plans/` first, then uses correlated handoffs to decide whether the newest plan should be reviewed as a pre-implementation plan or as an implementation artifact set. For implementation reviews it expands from the seed handoff to the full correlated project handoff set when one project produced multiple MEU handoffs. For plan reviews it selects the newest unstarted execution plan folder and reviews it for accuracy and consistency before implementation begins.

This is the workflow for prompts like:

- "Review the newest plan before implementation starts"
- "Critically review the latest handoff"
- "Check if the claimed changes were actually completed"
- "Find regressions/missed references after a docs refactor"

// turbo-all
// NOTE: turbo-all sets SafeToAutoRun=true for non-destructive commands (rg, Get-Content, etc.).
// It does NOT override AGENTS.md §Commits: "Never auto-commit." Git commit/push still requires explicit user direction.

## Prerequisites

Read these files in order:

1. `SOUL.md`
2. `AGENTS.md`
3. `.agent/context/current-focus.md`
4. `.agent/context/known-issues.md`
5. `pomera_notes` search (`Zorivest`, `Memory/Session/*`, `Memory/Decisions/*`)
6. `.agent/docs/emerging-standards.md` — consult when architecture, API/UI contracts, or testing standards are implicated. Do not raise standalone findings for standards drift unless it affects runtime behavior, safety, or test validity.

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

Auto-discovery is **plan-first**:

1. inspect `docs/execution/plans/` for the newest candidate project folder
2. inspect that plan's `task.md` / `implementation-plan.md`
3. then check correlated handoffs to determine whether the plan is still unstarted or has moved into implementation review mode

### Review Modes

Auto-discovery supports two modes:

1. **Plan review mode**: the newest execution plan exists but implementation has not started yet
2. **Implementation review mode**: work handoff artifacts already exist for the target project

### Discovery Steps

```powershell
# 1. Find recent execution plan folders FIRST
Get-ChildItem docs/execution/plans/ -Directory |
  Sort-Object LastWriteTime -Descending | Select-Object -First 5

# 2. Inspect the newest candidate plan's task state
Get-Content docs/execution/plans/<candidate>/task.md

# 3. Find most recent WORK handoffs (exclude review artifacts to prevent review-of-review)
Get-ChildItem .agent/context/handoffs/*.md -Exclude README.md,TEMPLATE.md |
  Where-Object { $_.Name -notmatch '(critical-review|corrections|recheck)' } |
  Sort-Object LastWriteTime -Descending | Select-Object -First 10

# 4. Correlate any handoffs to the candidate plan by date/slug/declared handoff paths
rg -n "<candidate-date>|<candidate-slug>|Create handoff:|Handoff Naming" \
  .agent/context/handoffs docs/execution/plans/<candidate>
```

### Mode Selection Rule

Start from the **newest execution plan folder** as the primary discovery candidate.

Choose **plan review mode** when all of the following are true for that candidate:

1. No correlated work handoff exists yet for that plan
2. `task.md` shows implementation has not started yet
3. The user did not explicitly request review of a completed handoff or review artifact

Treat a plan as **not started** when file state indicates planning/validation only, for example:

- implementation tasks are still `pending` / unchecked
- no MEU handoff paths created by the plan exist yet
- no task items indicate completed coding, testing, or handoff creation

Otherwise choose **implementation review mode** for that same correlated project.

From the results in implementation review mode:

- **Primary review target**: the work handoff set correlated to the newest plan candidate
- **Seed handoff**: the most recent correlated work handoff (by `LastWriteTime`)
- **Secondary scope**: the execution plan folder whose date/slug matches that handoff set. If no match, keep the newest plan folder as the project anchor and explain the fallback.
- If the handoff references specific files or folders, those become **additional scope**

From the results in plan review mode:

- **Primary review target**: the newest unstarted execution plan folder
- **Required scope**: `implementation-plan.md`, `task.md`, and any canonical docs/specs those files cite as authority
- **Additional scope**: registry, prior approved reflections/handoffs, or build-plan docs if the plan depends on them for carry-forward rules

### Correlation Rule

The agent must correlate the handoff and plan folder — not blindly pair the newest of each. Use the date prefix and slug to match. For example, `2026-03-07-meu-2-enums.md` pairs with `docs/execution/plans/2026-03-07-domain-entities-ports/` if that plan contains MEU-2.

For plan review mode, correlate the plan folder to repository state by confirming that no sibling MEU handoffs have been created yet and that the task file still reflects pre-implementation status.

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

If the user provides an execution plan path with no `only` constraint, default to reviewing the full plan folder (`implementation-plan.md` + `task.md`) even if no handoff exists yet.

### Canonical Review File Rule

Derive the review handoff path from the correlated execution plan folder, and reuse it across the full review thread for that target:

- **Plan review mode**: `.agent/context/handoffs/{plan-folder-name}-plan-critical-review.md`
- **Implementation review mode**: `.agent/context/handoffs/{plan-folder-name}-implementation-critical-review.md`

Examples:

- `docs/execution/plans/2026-03-07-commands-events-analytics/` -> `.agent/context/handoffs/2026-03-07-commands-events-analytics-plan-critical-review.md`
- `docs/execution/plans/2026-03-07-commands-events-analytics/` -> `.agent/context/handoffs/2026-03-07-commands-events-analytics-implementation-critical-review.md`

If the canonical review file already exists, append a new dated section to it instead of creating another handoff file.

### Zorivest Build-Plan Scope Rule

When the target artifact describes work on `docs/build-plan/` (including plan/walkthrough/handoff files for build-plan sessions):

- In **plan review mode** or **docs-only review sessions**, treat `docs/build-plan/` as **required review scope** even if the user only provides `.agent/context/handoffs/*.md` files.
- In **implementation review mode**, inspect `docs/build-plan/` only when:
  - the docs are the feature under review,
  - the handoff claims specific build-plan updates as evidence,
  - or a docs discrepancy appears to misstate delivered behavior, contracts, or test coverage.
- When `docs/build-plan/` is in scope, inspect the **actual file state/changes** (not just handoff claims).
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
| Auto-discover review targets | `orchestrator` | Review mode + target plan folder + seed handoff or unstarted-plan target + expanded handoff set (if multi-MEU) | `Get-ChildItem` commands above + `Get-Content <task.md>` | `pending` |
| Load context and target artifact | `orchestrator` | Scoped review objective + target list | `Get-Content <target>` | `pending` |
| Run evidence sweeps | `tester` | Command outputs (grep/diff/link checks) | `rg`, `git diff`, file reads | `pending` |
| Produce findings-first review | `reviewer` | Severity-ranked findings + verdict | Cross-check line references | `pending` |
| Write or update canonical review handoff | `reviewer` | Canonical review file for the correlated plan folder | file created or updated + readable | `pending` |

---

## Workflow Steps

## Step 1: Discover and Scope the Review (Orchestrator)

Run the auto-discovery commands to determine whether this is a **plan review** or an **implementation review**. Start from the newest execution plan folder, identify the target plan folder, then:

- if implementation review: identify the seed handoff, verify handoff-plan correlation, and enumerate the full handoff set when the project is multi-MEU
- if plan review: verify the plan is genuinely unstarted and define the review scope from plan artifacts plus the canonical documents they rely on

Then define:

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

1. Primary target artifact (seed handoff or unstarted plan folder)
2. Correlated execution plan (`implementation-plan.md` and `task.md` from `docs/execution/plans/`)
3. Every sibling handoff identified from the correlated project when in implementation review mode
4. Claimed files from the full handoff set when in implementation review mode
5. Relevant related files likely to drift (indexes, references, downstream links, registry, prior canon)
6. Current diffs (`git diff`) for the claimed files when available

For Zorivest build-plan review sessions (when `docs/build-plan/*` is in scope under the rule above):

7. The actual changed `docs/build-plan/*` files referenced or implied by the artifact
8. `git status --short -- docs/build-plan` and `git diff -- docs/build-plan/<claimed-files>` when applicable
9. If files are untracked or `git diff` is incomplete, perform direct file-state checks (counts, anchors, headings, annotation blocks, etc.) against `docs/build-plan/*`

---

## Step 3: Run Critical Verification Sweeps (Tester)

Use fast, reproducible command checks. Prefer `rg`.

### Required Sweep Types (Implementation Reviews)

1. **Runtime / contract verification**
   - Does the delivered code actually satisfy the claimed API, UI, persistence, and round-trip behavior?
2. **Test rigor audit (required when test files are in scope)**
   - Do tests assert meaningful behavior, or do they trivially pass with weak/vacuous assertions?
   - See IR-5 checklist item for grading criteria
3. **Negative-path / failure-path verification**
   - Do tests and code cover rejected writes, missing data, 404 vs non-404 semantics, invalid transitions, and persistence failures?
4. **Claim verification**
   - Did the files/lines/behaviors mentioned in the handoff actually change?
5. **Cross-handoff consistency**
   - Shared totals, phase-gate claims, registry state, and artifact timing consistent across the full project handoff set?
6. **Verification quality**
   - Are handoff checks strong enough, or do they create false confidence?
7. **Evidence quality**
   - Are commands/tests reproducible and auditable?
8. **Actual build-plan file changes (when in scope)**
   - Did the claimed changes materially appear in `docs/build-plan/*`, with evidence tied to file lines/state?
9. **Residual references / cross-file consistency (when relevant)**
   - Old names/phrases/slugs/anchors still present, or renamed headings left downstream links stale?

### Additional Required Sweep Types (Plan Review Mode)

1. **Plan-task consistency**
   - Do `implementation-plan.md` and `task.md` describe the same project scope, task order, and outputs?
2. **Status readiness**
   - Does file state really indicate not-started work, or has implementation already begun?
3. **Role/ownership consistency**
   - Does every task include the required role, deliverable, validation command, and status?
4. **Validation specificity**
   - Are validation commands exact, runnable, and scoped to the work described?
5. **Dependency/order correctness**
   - Are MEUs sequenced coherently, with no impossible order or missing prerequisites?
6. **Source-traceability**
   - Are acceptance criteria and non-spec rules tagged to `Spec`, `Local Canon`, `Research-backed`, or `Human-approved` sources?

### Suggested Commands (Adapt Per Task)

```powershell
# 1) Read the primary review artifact and target files
Get-Content <primary-artifact>
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

### Functionality-First Rule (Implementation Review Mode)

When reviewing completed work handoffs, prioritize:

1. runtime behavior and API/UI contract correctness
2. TDD/test rigor and negative-path coverage
3. persistence and round-trip correctness
4. handoff claim accuracy
5. documentation consistency

Documentation-only discrepancies are non-blocking by default unless they:

- misstate delivered behavior or contracts
- falsely claim tests, validation, or completeness
- hide missing work or unresolved risk
- create unsafe or misleading operator/developer instructions

### Priorities (in order)

1. Broken runtime behavior / contract mismatches
2. Weak, misleading, or missing tests that allow broken behavior to pass green
3. Persistence, integration, or round-trip gaps
4. Contradictions between plan or handoff claims and actual file state
5. Documentation inconsistencies or downstream reference drift

### Severity Guidance (Docs Reviews)

- `Critical`: Dangerous instructions/security regressions or decisions documented incorrectly
- `High`: Incorrect contracts, false implementation claims, or documentation that materially misstates shipped behavior
- `Medium`: Portability, maintainability, verification-quality, or navigation issues
- `Low`: Auditability, wording, minor evidence quality gaps

### Docs Review Checklist (required for plan review mode, docs-only reviews, or when docs are evidence for implementation claims)

| # | Check | What To Look For |
|---|---|---|
| DR-1 | Claim-to-state match | Handoff says a change happened and file state proves it |
| DR-2 | Residual old terms | Old phrase/slug variants still present (`foo bar` and `foo-bar`) |
| DR-3 | Downstream references updated | Indexes, cross-links, and anchors updated after rename/move |
| DR-4 | Verification robustness | Handoff checks would actually catch regressions introduced by the change |
| DR-5 | Evidence auditability | Commands/diffs are reproducible (not placeholders only) |
| DR-6 | Cross-reference integrity | Architectural changes are consistent across all canonical docs (run `rg` for old pattern across `docs/build-plan/`, `docs/execution/`, `.agent/`) |
| DR-7 | Evidence freshness | Handoff-claimed counts match reproduced command output (any mismatch is LOW minimum) |
| DR-8 | Completion vs residual risk | If residual risk acknowledges known gaps, conclusion must NOT say "implementation complete" or "all ACs met" |

> If code changes are in scope, the Implementation Review Checklist below is primary. Run the Docs Review Checklist only for documentation that is itself under review or is being used as evidence for implementation claims.

### Implementation Review Checklist (required when reviewing work handoffs)

| # | Check | What To Look For |
|---|---|---|
| IR-1 | Live runtime evidence | For route/handler MEUs: integration test without dependency overrides exists and was run |
| IR-2 | Stub behavioral compliance | Stubs honor save→get consistency, filter semantics, correct `exists()` returns; no `__getattr__` silently returning values (explicit-error form permitted) |
| IR-3 | Error mapping completeness | Every write-adjacent route maps `NotFoundError → 404`, `BusinessRuleError → 409`, `ValueError → 422` AND at least one test asserts response body shape (not just status code) |
| IR-4 | Fix generalization | When a finding was fixed, similar instances in other files/routes were also checked and fixed |
| IR-5 | Test rigor audit | Every test file in scope is audited for assertion strength. Each test is rated 🟢 Strong / 🟡 Adequate / 🔴 Weak using the criteria below. Any 🔴 is `Medium` minimum; > 3 🟡 in one file is `Low` |

#### IR-5 Test Rigor Grading Criteria

For each test, check whether it would still pass if the production code were subtly broken:

| Rating | Definition | Example |
|--------|------------|----------|
| 🟢 Strong | Asserts specific values, exercises real behavior, tests both positive and negative paths | `assert delta.days == 30`, `assert result == expected_bytes` |
| 🟡 Adequate | Tests the right thing but uses weak assertions (key-exists, non-empty, mock-was-called without arg check) or couples to private internals | `assert "key" in result`, `mock.assert_called_once()` without verifying args |
| 🔴 Weak | Trivially passes even if code is broken: try/except swallows failures, only checks types not values, patches a private method that may not exist | `try: fn() except: assert dir.exists()` |

Common weakness patterns to flag:

- **Try/except safety nets** that let tests pass when the feature under test actually fails
- **Asserting only key existence** instead of checking the returned value matches expectations
- **Patching private methods** (`_check_cache`, `_internal`) — fragile to refactoring; if method is renamed the patch is silently ignored and test passes vacuously
- **Testing only the "not found" path** without an insert+get round-trip for repository methods
- **Missing boundary assertions** — e.g., testing a 30-day delta but only asserting `start < end` instead of `delta.days == 30`
- **Data format assertions** — checking a data URI key exists but not verifying the `data:image/png;base64,` prefix or payload size

### Plan Review Checklist (required in plan review mode)

| # | Check | What To Look For |
|---|---|---|
| PR-1 | Plan/task alignment | `implementation-plan.md` and `task.md` describe the same scope and order |
| PR-2 | Not-started confirmation | No file-state evidence that coding/testing/handoffs already began |
| PR-3 | Task contract completeness | Every task has `task`, `owner_role`, `deliverable`, `validation`, `status` |
| PR-4 | Validation realism | Commands are specific enough to prove the intended work |
| PR-5 | Source-backed planning | Rules beyond explicit spec text are tagged to an allowed source basis |
| PR-6 | Handoff/corrections readiness | Multi-MEU handoff paths are explicit when applicable, and review findings can be resolved via `/planning-corrections` |

---

## Step 5: Write or Update the Canonical Review Handoff (Reviewer)

Write to the canonical review file derived from the correlated plan folder:

- **Plan review mode**: `.agent/context/handoffs/{plan-folder-name}-plan-critical-review.md`
- **Implementation review mode**: `.agent/context/handoffs/{plan-folder-name}-implementation-critical-review.md`

If that file already exists, append a new dated review update section. Do not fork the same review thread into additional `-recheck`, `-approved`, `-final`, or `-corrections` files.

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
6. If this is not the first pass, a dated update heading so the other agent can read one file and see the full review history in order

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
5. **For implementation reviews, do not elevate documentation drift above broken behavior or weak tests.** Inspect and cite actual `docs/build-plan/*` changes only when docs are in scope under the build-plan scope rule.
6. **When a correlated project produced multiple MEU handoffs, load all of them.** The newest work handoff is only the discovery seed.
7. **Never review a review.** Auto-discovery excludes `*critical-review*`, `*-corrections*`, and `*-recheck*` handoffs as review seeds. Valid targets are work handoffs or unstarted execution plan folders.
8. **If no implementation handoff exists yet, review the newest unstarted execution plan instead of failing discovery.** This is a plan-accuracy and consistency review, not an implementation validation.
9. **When plan-review findings require changes, route the fix phase through `/planning-corrections`.** That workflow applies to plan adjustments as well as post-implementation corrections.
10. **Auto-discovery starts from `docs/execution/plans/` first.** Do not begin by picking the newest handoff unless the user explicitly provides a handoff path.
11. **One rolling review file per target.** For the same execution plan folder, keep plan-review updates in the same `-plan-critical-review.md` file and implementation-review updates in the same `-implementation-critical-review.md` file.
12. **When test files are in review scope, audit every test for assertion strength (IR-5).** A test suite where all tests pass is not evidence of quality — tests that trivially pass with weak assertions (try/except safety nets, key-only checks, private-method patching) must be flagged. Report the per-test rating table in the review handoff.
13. **A weak or misleading test is `Medium` minimum when it can allow broken behavior to pass green.** Documentation-only discrepancies are `Low` by default unless they materially misstate runtime behavior, test coverage, or unresolved risk.

---

## Output Contract

Return to the user:

- Auto-discovered targets (what was reviewed, why, and how handoff–plan were correlated)
- Findings (severity-ranked, file/line references)
- Open questions / assumptions
- Review verdict (`changes_required` or `approved`)
- Residual risk statement
- Path to the created or updated canonical review handoff

If no findings are discovered, say so explicitly and list remaining verification gaps (if any).

---

## Orchestration Flow

This workflow is part of a three-workflow orchestration cycle:

1. `/create-plan` → plan new work
2. `/critical-review-feedback` → review a new plan or completed work (this workflow)
3. `/planning-corrections` → resolve findings from this workflow

When to switch:

- Use this workflow immediately after `/create-plan` when a new plan needs adversarial review before implementation starts.
- Use `/planning-corrections` if the verdict is `changes_required` and the user wants fixes applied.
- Use `/create-plan` to start new implementation work.
