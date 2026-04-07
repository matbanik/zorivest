---
project: "{YYYY-MM-DD}-{project-slug}"
date: "{YYYY-MM-DD}"
source: "docs/build-plan/{section-reference}"
meus: ["{MEU-ID-1}", "{MEU-ID-2}"]
status: "draft"
template_version: "2.0"
---

# Implementation Plan: {Project Title}

> **Project**: `{YYYY-MM-DD}-{project-slug}`
> **Build Plan Section(s)**: {bp section reference(s)}
> **Status**: `draft` | `approved` | `changes_required`

---

## Goal

{Brief description of the problem, background context, and what the change accomplishes.}

---

## User Review Required

> [!IMPORTANT]
> {Document anything that requires user review or feedback: breaking changes, significant design decisions, scope questions.}

---

## Proposed Changes

### {Component/MEU Name}

#### Boundary Inventory

| Surface | Schema Owner | Field Constraints | Extra-Field Policy |
|---------|-------------|-------------------|-------------------|
| {REST body\|MCP input\|UI form\|file import} | {Pydantic model\|Zod schema} | {enum/format/range rules} | {extra="forbid"\|exception} |

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-1 | {criterion} | {Spec\|Local Canon\|Research-backed\|Human-approved} | {what invalid input is rejected} |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| {behavior} | {Spec\|Local Canon\|Research-backed\|Human-approved} | {how resolved if under-specified} |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| {path} | {new\|modify\|delete} | {description} |

---

## Out of Scope

- {Item 1}
- {Item 2}

---

## BUILD_PLAN.md Audit

{This project does/does not modify build-plan sections. Validation:}

```powershell
rg "{project-slug}" docs/BUILD_PLAN.md  # Expected: {0 matches | N matches}
```

---

## Verification Plan

### 1. {Check Category}
```powershell
{exact runnable command}
```

### 2. {Check Category}
```powershell
{exact runnable command}
```

---

## Open Questions

> [!WARNING]
> {Any clarifying or design questions for the user that will impact the implementation.}

---

## Research References

- {link to research doc or ADR}
