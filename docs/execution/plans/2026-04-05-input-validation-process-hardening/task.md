# Task — Input Validation Process Hardening

## Category B: `.agent` Process Hardening (12 corrections)

| # | Task | Owner Role | Deliverable | Validation | Status |
|---|------|-----------|-------------|------------|--------|
| B1 | Add Boundary Input Contract section to `AGENTS.md` under Planning Contract | coder | `AGENTS.md` lines 189–201 | `rg -n "Boundary Input Contract" AGENTS.md` | ✅ done |
| B2 | Add Boundary Inventory Table to Spec Sufficiency Gate in `create-plan.md` | coder | `create-plan.md` lines 93–98 | `rg -n "Boundary Inventory Row" .agent/workflows/create-plan.md` | ✅ done |
| B3 | Add boundary contract to FIC + negative tests to Red Phase in `tdd-implementation.md` | coder | `tdd-implementation.md` lines 32–33, 42–50 | `rg -n "Boundary contract\|negative input tests" .agent/workflows/tdd-implementation.md` | ✅ done |
| B4 | Add Boundary Contract section to `meu-handoff.md` template | coder | `meu-handoff.md` lines 75–80 | `rg -n "Boundary Contract" .agent/workflows/meu-handoff.md` | ✅ done |
| B5 | Add AV-7, AV-8, AV-9 adversarial checks to `validation-review.md` | coder | `validation-review.md` lines 80–82 | `rg -n "AV-7\|AV-8\|AV-9" .agent/workflows/validation-review.md` | ✅ done |
| B6 | Add IR-6 boundary validation coverage to `critical-review-feedback.md` | coder | `critical-review-feedback.md` line 400 | `rg -n "IR-6" .agent/workflows/critical-review-feedback.md` | ✅ done |
| B7 | Add boundary validation gap correction category to `planning-corrections.md` | coder | `planning-corrections.md` line 101 | `rg -n "boundary validation gap" .agent/workflows/planning-corrections.md` | ✅ done |
| B8 | Add multi-pattern boundary validation audit (check #11) to `quality-gate/SKILL.md` | coder | `quality-gate/SKILL.md` lines 53–72 | `rg -n "Boundary validation audit" .agent/skills/quality-gate/SKILL.md` | ✅ done |
| B9 | Add Step 6b Boundary Validation Audit to `pre-handoff-review/SKILL.md` | coder | `pre-handoff-review/SKILL.md` lines 142–157 | `rg -n "Step 6b" .agent/skills/pre-handoff-review/SKILL.md` | ✅ done |
| B10 | Expand input validation into Boundary Validation Standards in `code-quality.md` | coder | `code-quality.md` lines 20–47 | `rg -n "Boundary Validation Standards" .agent/docs/code-quality.md` | ✅ done |
| B11 | Add Write-Boundary Test Matrix to `testing-strategy.md` | coder | `testing-strategy.md` lines 109–124 | `rg -n "Write-Boundary" .agent/docs/testing-strategy.md` | ✅ done |
| B12 | Add item 8 boundary validation responsibilities to `reviewer.md` | coder | `reviewer.md` lines 28–33 | `rg -n "boundary validation" .agent/roles/reviewer.md` | ✅ done |

## Tracking & Documentation

| # | Task | Owner Role | Deliverable | Validation | Status |
|---|------|-----------|-------------|------------|--------|
| T1 | Add `[BOUNDARY-GAP]` to `known-issues.md` for deferred Category A findings | coder | `known-issues.md` lines 7–15 | `rg -n "BOUNDARY-GAP" .agent/context/known-issues.md` | ✅ done |
| T2 | Update handoff 096 with Corrections Applied section | coder | Handoff 096 lines 225–267 | Verify dated section present in handoff | ✅ done |
| T3 | Save session state to pomera notes | coder | Pomera note #739 | `pomera_notes get --note_id 739` | ✅ done |
| T4 | Create canonical plan at `docs/execution/plans/` | coder | `implementation-plan.md` | File exists at canonical path | ✅ done |
| T5 | Create task file at canonical path | coder | `task.md` | File exists at canonical path | ✅ done |

## Plan Review Corrections

| # | Task | Owner Role | Deliverable | Validation | Status |
|---|------|-----------|-------------|------------|--------|
| C1 | Remove `.agent/` absolute links from `implementation-plan.md` | coder | No `file:///p:/zorivest/.agent/` links | `rg "file:///p:/zorivest/\.agent" docs/execution/plans/2026-04-05-input-validation-process-hardening/` returns 0 | ✅ done |
| C2 | Expand quality-gate check #11 to multi-pattern audit | coder | 4-pattern audit in `quality-gate/SKILL.md` | `rg -A2 "Check 11" .agent/skills/quality-gate/SKILL.md` | ✅ done |
| C3 | Convert `task.md` to contract-table format | coder | Tables with `Task`, `Owner Role`, `Deliverable`, `Validation`, `Status` columns | `rg "Owner Role" docs/execution/plans/2026-04-05-input-validation-process-hardening/task.md` | ✅ done |
