---
description: Review known-issues.md, classify each issue into actionable categories, and recommend MEU/build-plan updates to resolve them. Produces a triage report that feeds into /create-plan.
---

# Issue Triage Workflow

Use this workflow when known issues have accumulated and you need to determine which ones
require new MEUs, expanded MEU scope, new build-plan sections, or can be deferred/archived.
This is a **PLANNING-phase-only** workflow — it produces a triage report, not implementation.

// turbo-all

## Prerequisites

Read these files in order:

1. `AGENTS.md`
2. `.agent/context/known-issues.md`
3. `.agent/context/known-issues-archive.md` (scan only — verify nothing was prematurely archived)
4. `.agent/context/meu-registry.md`
5. `docs/build-plan/build-priority-matrix.md`
6. `.agent/context/current-focus.md`

## Classification Taxonomy

Every active issue must be classified into exactly one category:

| Code | Category | Action Required |
|------|----------|----------------|
| `MEU-NEW` | New MEU Required | Create new MEU(s) within an existing build-plan section |
| `MEU-EXPAND` | Expand Existing MEU | Add scope/subtasks to an already-planned (⬜/🟡) MEU |
| `PLAN-NEW` | New Build Plan Section | Write new build-plan file + register new MEUs in the registry |
| `UPSTREAM` | Upstream/External | No MEU action — blocked on third-party fix; track and monitor |
| `ARCH-DECISION` | Architecture Decision Needed | Needs design decision (ADR, human approval) before MEU scoping |
| `RESOLVED` | Already Resolved | Issue has been fixed — archive it now |
| `WORKAROUND-OK` | Workaround Sufficient | Current mitigation is adequate; no further work planned |
| `BLOCKED` | Blocked on Other Work | Will resolve naturally when a dependent MEU completes |
| `TECH-DEBT` | Technical Debt | Low-severity cleanup that can be batched into a debt-reduction project |

## Steps

### 1. Validate & Archive Resolved Issues

> [!IMPORTANT]
> **This step runs FIRST, before any classification or planning.**
> Clean the issue list so that all subsequent analysis operates only on genuinely active issues.

For **every** issue in `known-issues.md` (both "Active Issues" and "Mitigated / Workaround Applied" sections), verify whether it is still valid:

#### 1a. Check issues explicitly marked ✅ Resolved

These are issues whose Status line already says `✅ Resolved` but haven't been moved to the archive yet. Archive them immediately — no further verification needed.

#### 1b. Check issues NOT marked resolved — verify against codebase

For each remaining issue, run targeted verification commands to determine if the underlying problem has actually been fixed since the issue was logged:

**Verification techniques** (use whichever apply):

1. **Grep for fix indicators** — search for code changes that address the issue:
   ```powershell
   # Look for fix patterns related to the issue
   rg "{issue-related-pattern}" packages/ mcp-server/ ui/ *> C:\Temp\zorivest\issue-check.txt; Get-Content C:\Temp\zorivest\issue-check.txt
   ```

2. **Check test coverage** — verify if regression tests exist:
   ```powershell
   # Search for test names that reference the issue
   rg "{ISSUE-ID}" tests/ *> C:\Temp\zorivest\issue-tests.txt; Get-Content C:\Temp\zorivest\issue-tests.txt
   ```

3. **Check MEU completion** — if the issue references a specific MEU, check its status in `meu-registry.md`:
   ```powershell
   Select-String -Path ".agent\context\meu-registry.md" -Pattern "{MEU-ID}" *> C:\Temp\zorivest\meu-check.txt; Get-Content C:\Temp\zorivest\meu-check.txt
   ```

4. **Check upstream status** — for upstream bugs, check if the referenced issue/PR has been merged:
   - Read the upstream issue URL if available
   - Check the pinned dependency version against the fix version

5. **Check workaround relevance** — for mitigated issues, verify the workaround is still in place and still needed:
   ```powershell
   # Verify workaround code still exists
   rg "{workaround-code-pattern}" packages/ mcp-server/ ui/ *> C:\Temp\zorivest\workaround-check.txt; Get-Content C:\Temp\zorivest\workaround-check.txt
   ```

#### 1c. Perform archival

For every issue confirmed as resolved (either marked ✅ or verified fixed through 1b):

1. **Move** the full issue entry from `known-issues.md` to `known-issues-archive.md`
   - Append to the end of the archive file (before any template sections)
   - Add the resolution date

2. **Add** a 1-line summary row to the "Archived" table in `known-issues.md`:
   ```markdown
   | {ID} | {date} | {one-line summary} |
   ```

3. **Verify** the `known-issues.md` line count target (< 100 lines):
   ```powershell
   (Get-Content ".agent\context\known-issues.md" | Measure-Object -Line).Lines *> C:\Temp\zorivest\ki-lines.txt; Get-Content C:\Temp\zorivest\ki-lines.txt
   ```

#### 1d. Summary output

After completing archival, report:
- How many issues were reviewed
- How many were archived (with IDs)
- How many remain active for classification

### 2. Inventory Remaining Active Issues

Read the now-cleaned `.agent/context/known-issues.md` and build a flat list of every **still-active** issue:

```powershell
# Quick count of remaining issue headers
Select-String -Path ".agent\context\known-issues.md" -Pattern "^### \[" *> C:\Temp\zorivest\issue-headers.txt; Get-Content C:\Temp\zorivest\issue-headers.txt
```

For each issue, extract:
- **ID**: The `[SHORT-TITLE]` tag
- **Severity**: Critical / High / Medium / Low
- **Component**: core / infrastructure / api / ui / mcp-server
- **Status**: Open / In Progress / Workaround Applied
- **Has existing MEU?**: Cross-reference against meu-registry.md

### 3. Classify Each Issue

Use sequential thinking to classify each remaining active issue. For each issue, answer:

1. **Is it an upstream bug with no local fix?** → `UPSTREAM`
2. **Is the current workaround sufficient long-term?** → `WORKAROUND-OK`
3. **Is it blocked on unfinished MEU work?** → `BLOCKED` (identify which MEU)
4. **Does it need an architectural decision first?** → `ARCH-DECISION`
5. **Does an existing planned MEU already cover this?** → `MEU-EXPAND`
6. **Can it fit within an existing build-plan section?** → `MEU-NEW`
7. **Does it require an entirely new capability area?** → `PLAN-NEW`
8. **Is it low-severity cleanup?** → `TECH-DEBT`

Document the reasoning for each classification — don't just assign codes.

> Note: `RESOLVED` is no longer in this list — all resolved issues were already archived in Step 1.

### 4. Cross-Reference with MEU Registry

For each `MEU-EXPAND` classification, identify the target MEU:

```powershell
# Search for relevant MEU slugs
Select-String -Path ".agent\context\meu-registry.md" -Pattern "{keyword}" *> C:\Temp\zorivest\meu-search.txt; Get-Content C:\Temp\zorivest\meu-search.txt
```

For each `MEU-NEW` classification, identify the build-plan section it belongs to:

```powershell
# List build plan files to find the right section
Get-ChildItem docs\build-plan\*.md | Select-Object Name *> C:\Temp\zorivest\bp-files.txt; Get-Content C:\Temp\zorivest\bp-files.txt
```

Read the relevant build-plan section to verify the new MEU fits within its scope and doesn't duplicate existing planned work.

### 5. Assess Resolution Priority

For all actionable issues (`MEU-NEW`, `MEU-EXPAND`, `PLAN-NEW`, `ARCH-DECISION`), assign a resolution priority using this matrix:

| Severity \ Impact | Blocks Other Work | Standalone |
|---|---|---|
| **Critical** | P0 — Immediate | P1 — Next session |
| **High** | P1 — Next session | P2 — Near term |
| **Medium** | P2 — Near term | P3 — Backlog |
| **Low** | P3 — Backlog | P4 — Opportunistic |

"Blocks Other Work" means the issue prevents planned MEUs from proceeding or causes CI/test failures.

### 6. Group into Project Batches

Apply the same grouping logic as `/create-plan` Step 3:

- **Dependency order**: foundation first
- **Logical continuity**: issues in the same component or build-plan section
- **Right-sizing**: 2–5 MEUs per project batch (sweet spot for context efficiency)
- **Priority coherence**: don't mix P0 and P4 issues in the same batch

For each batch, define:
- Project slug
- Issues addressed
- MEUs to create or expand (with proposed IDs if new)
- Build-plan section(s) affected
- Priority band
- Estimated complexity (S/M/L)

### 7. Generate Triage Report

Write the triage report to **both** locations:

1. `.agent/context/issue-triage-report.md` — the project-side canonical copy
2. Agent workspace artifact — for UI rendering

The report must include these sections:

```markdown
# Known Issue Triage Report — {YYYY-MM-DD}

## Summary
- Total issues reviewed: N
- Archived in Step 1: N (list IDs)
- Remaining active: N
- Actionable (new/expanded MEUs): N
- Upstream/deferred: N
- Architecture decisions needed: N

## Archival Actions Performed (Step 1)
Issues verified as resolved and moved to `known-issues-archive.md`:
- [ISSUE-ID] — {reason}: {verification method used}

## Classification Table (Active Issues)

| Issue ID | Severity | Component | Classification | Target | Priority | Notes |
|----------|----------|-----------|---------------|--------|----------|-------|

## Recommended Project Batches

### Batch 1: {project-slug} — Priority P{N}
- **Issues addressed**: [X], [Y]
- **New MEUs**: MEU-{ID} `{slug}` — {description}
- **Expanded MEUs**: MEU-{ID} — add {scope}
- **Build-plan section**: `docs/build-plan/{file}`
- **Complexity**: S/M/L
- **Dependencies**: {list or "none"}
- **Next step**: Invoke `/create-plan` with this batch

### Batch 2: ...

## Architecture Decisions Required
Issues needing human/ADR resolution before MEU scoping:
- [ISSUE-ID] — decision needed: {description}
  - Option A: {description}
  - Option B: {description}
  - Recommendation: {A or B, with rationale}

## No Action Required
Issues classified as UPSTREAM, WORKAROUND-OK, or BLOCKED:
| Issue ID | Classification | Rationale |
```

### 8. Present for Review — HARD STOP

> [!CAUTION]
> **MANDATORY HARD STOP — NO EXCEPTIONS.**
> After presenting the triage report, the agent MUST end its turn immediately.
> Do NOT proceed to create plans or execute any implementation.

Present the triage report with:

1. State: **"Issue triage complete. Awaiting your review before plan generation."**
2. Summarize archival actions performed in Step 1
3. List the recommended project batches with their priorities
4. Highlight any architecture decisions requiring human input
5. **END YOUR TURN.**

The user will:
- Review and approve/modify project batches
- Make architecture decisions
- Then invoke `/create-plan` for each approved batch

## Integration with `/create-plan`

After the triage report is approved, each project batch becomes an input to `/create-plan`:

1. The user invokes `/create-plan`
2. During Step 2 (Identify What's Next), the agent reads the approved triage report batch
3. The batch's issue-to-MEU mappings become the project scope
4. Standard `/create-plan` Steps 3–5 proceed normally

If the triage recommends expanding an existing MEU, the `/create-plan` invocation should:
- Read the existing plan for that MEU (if one exists)
- Add the new scope as additional FIC acceptance criteria
- Note the issue ID being resolved

## Exit Criteria

- [ ] Every issue in `known-issues.md` validated against codebase state
- [ ] Resolved issues archived to `known-issues-archive.md` with evidence
- [ ] `known-issues.md` line count verified (< 100 lines target)
- [ ] All remaining active issues classified
- [ ] Cross-referenced against meu-registry.md (no duplicate MEUs)
- [ ] Cross-referenced against build-priority-matrix.md (correct section placement)
- [ ] Triage report written to `.agent/context/issue-triage-report.md`
- [ ] Report presented to human with HARD STOP
