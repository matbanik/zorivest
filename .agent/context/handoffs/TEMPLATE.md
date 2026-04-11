---
seq: "{SEQ}"
date: "{YYYY-MM-DD}"
project: "{project-slug}"
meu: "{MEU-ID}"
status: "draft"
action_required: "VALIDATE_AND_APPROVE"
template_version: "2.1"
verbosity: "standard"
plan_source: "docs/execution/plans/{YYYY-MM-DD}-{project-slug}/implementation-plan.md"
build_plan_section: "bp{NN}s{X.Y}"
agent: "{agent-name}"
reviewer: "{reviewer-name}"
predecessor: "{previous-handoff-filename or none}"
---

# Handoff: {SEQ}-{YYYY-MM-DD}-{project-slug}-bp{NN}s{X.Y}

> **Status**: `draft` | `in_progress` | `complete` | `blocked`
> **Action Required**: `VALIDATE_AND_APPROVE` | `REVIEW_CORRECTIONS` | `EXECUTE`

---

## Scope

**MEU**: {MEU-ID} — {brief description}
**Build Plan Section**: {section reference}
**Predecessor**: {link to previous handoff or "none"}

---

## Acceptance Criteria

| AC | Description | Source | Test(s) | Status |
|----|-------------|--------|---------|--------|
| AC-1 | {criterion} | {Spec\|Local Canon\|Research-backed\|Human-approved} | {test file:function} | ⬜ |
| AC-2 | {criterion} | {source} | {test reference} | ⬜ |

<!-- CACHE BOUNDARY -->
<!-- Content above this line is stable across revision passes (KV cache prefix). -->
<!-- Content below this line changes between passes (evidence, results, corrections). -->

---

## Evidence

> **Test output rule**: Include only failing test names, assertion messages, and relevant stack frames. Summarize passing tests as `{N} passed`. See `.agent/docs/context-compression.md` for full rules.

### FAIL_TO_PASS

| Test | Red Output (hash/snippet) | Green Output | File:Line |
|------|--------------------------|--------------|-----------|
| {test_name} | {failure message} | {pass message} | {file:line} |

### Commands Executed

| Command | Exit Code | Key Output |
|---------|-----------|------------|
| `{exact command}` | 0 | {relevant output} |

### Quality Gate Results

```
pyright: X errors, Y warnings
ruff: X violations
pytest: X passed, Y failed
anti-placeholder: 0 matches
```

---

## Changed Files

> **Delta-only rule**: Show unified diff blocks (` ```diff `) for modifications. Do not inline full source code. See `.agent/docs/context-compression.md §Delta-Only Code Sections`.

| File | Action | Lines | Summary |
|------|--------|-------|---------|
| {path} | {new\|modified\|deleted} | {range} | {what changed} |

_For each modified file, include a fenced diff excerpt showing the key changes:_

```diff
 unchanged context line
-old_line_removed
+new_line_added
 unchanged context line
```

---

## Codex Validation Report

_Left blank for reviewer agent. Reviewer fills this section during `/validation-review`._

### Recheck Protocol

1. Read Scope + AC table
2. Verify each AC against Evidence section (file:line, not memory)
3. Run all Commands Executed and compare output
4. Run Quality Gate commands independently
5. Record findings below

### Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 1 | {High\|Medium\|Low} | {description} | {file:line} | {fix} | {open\|fixed} |

### Verdict

`{approved | changes_required}` — {rationale}

---

## Corrections Applied ({YYYY-MM-DD})

_Repeatable section. Add one per correction round._

**Findings resolved**: {N}/{N}

| # | Finding | Fix Applied | Verification |
|---|---------|-------------|--------------|
| 1 | {finding} | {fix} | {evidence} |

---

## Deferred Items

_Optional. Skip this section if no items are deferred._

| Item | Reason | Follow-up |
|------|--------|-----------|
| {item} | {blocked\|out-of-scope\|future-MEU} | {link to tracking} |

---

## History

| Event | Date | Agent | Detail |
|-------|------|-------|--------|
| Created | {date} | {agent} | Initial handoff |
| Submitted for review | {date} | {agent} | Sent to {reviewer} |
| Review complete | {date} | {reviewer} | Verdict: {verdict} |
| Corrections applied | {date} | {agent} | {N} findings resolved |
