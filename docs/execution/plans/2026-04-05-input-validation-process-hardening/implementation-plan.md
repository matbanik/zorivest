# Input Validation Process Hardening

## Task

- **Date:** 2026-04-05
- **Project slug:** input-validation-process-hardening
- **Source:** Handoff 096 (`096-2026-04-05-create-update-input-validation-review-bp04+05+06+08+09.md`) — cross-boundary input validation review covering REST, service, MCP, and UI write paths across build-plan sections 04, 05, 06, 08, 09.
- **Scope:** Apply Category B `.agent` process hardening corrections from the input validation review. 12 documentation/workflow adjustments encoding boundary validation requirements into the agentic infrastructure.

## Context

A critical review (handoff 096) identified systemic input validation gaps across 7 API/MCP write boundaries. The review produced two categories of findings:

- **Category A (Code-level fixes):** 7 findings requiring TDD-based code changes — deferred to a dedicated `/create-plan` project tracked as `[BOUNDARY-GAP]` in `known-issues.md`.
- **Category B (Process hardening):** 12 `.agent` documentation/workflow adjustments — applied in this project.

## Scope Decision

Category B is applied now because these are documentation-only changes that encode lessons learned into the development process. Future MEUs will be subject to mandatory boundary validation review through the updated workflows, skills, and checklists (though runtime enforcement requires the Category A code changes).

Category A is deferred because each write boundary requires:
- Strict Pydantic boundary schemas (`strict=True`, `extra="forbid"`, constrained fields)
- Negative regression tests (blank strings, invalid enums, non-positive numerics, unexpected fields)
- Create/update invariant parity enforcement
- Full FIC → Red → Green → Quality Gate cycles

## Proposed Changes

### AGENTS.md

#### [MODIFY] AGENTS.md

Add mandatory **Boundary Input Contract** section under §Planning Contract (after Spec Sufficiency Gate). Requires every MEU touching external input to enumerate write surfaces, schema owners, field constraints, extra-field policy, error mapping, and create/update parity. Includes explicit rule that Python `assert` and type annotations alone are not acceptable runtime boundary validation.

---

### Workflows

#### [MODIFY] create-plan.md

Extend Spec Sufficiency Gate to require a **Boundary Inventory Table** per write surface. Plan is not approvable until it identifies every external input surface and documents expected rejection behavior.

#### [MODIFY] tdd-implementation.md

Strengthen Step 2 (FIC) with boundary contract and negative input case requirements. Strengthen Step 3 (Red Phase) with mandatory negative input tests for write-adjacent MEUs (blank strings, invalid enums, non-positive numerics, extra fields, create/update parity). Add rule that handlers/services may not accept raw `dict` or `**kwargs` from external input without prior boundary schema validation.

#### [MODIFY] meu-handoff.md

Add **Boundary Contract** section to the handoff template with table columns: Boundary, Schema, Extra-Field Policy, Negative Tests, Create/Update Parity.

#### [MODIFY] validation-review.md

Add adversarial verification items:
- AV-7: Boundary schema enforcement
- AV-8: Create/update parity
- AV-9: Invalid input produces 4xx

#### [MODIFY] critical-review-feedback.md

Add IR-6 (boundary validation coverage) to Implementation Review Checklist.

#### [MODIFY] planning-corrections.md

Add "boundary validation gap" as a named correction category to Step 2b, requiring search of ALL sibling write paths.

---

### Skills

#### [MODIFY] quality-gate/SKILL.md

Add blocking check #11: multi-pattern boundary validation audit for touched write surfaces. Checks raw dict params, unvalidated reconstruction patterns, missing `extra="forbid"`, and kwargs bypass.

#### [MODIFY] pre-handoff-review/SKILL.md

Add Step 6b: Boundary Validation Audit (Pattern 11) — list every boundary touched, prove rejection via negative tests, confirm create/update parity.

---

### Documentation

#### [MODIFY] code-quality.md

Expand "Every function must have input validation" into Boundary Validation Standards with forbidden patterns (raw dict updates, `replace(**raw_input)`, relying on type hints as runtime validation).

#### [MODIFY] testing-strategy.md

Add Write-Boundary Test Matrix with 9 required test categories for write-adjacent MEUs.

---

### Roles

#### [MODIFY] reviewer.md

Add item 8: explicit boundary validation responsibilities — flag unconstrained DTOs, silent coercion, unknown-field acceptance, and unvalidated update paths.

---

## Category A — Deferred Code Changes

| # | Finding | Files | Severity |
|---|---------|-------|----------|
| F1 | Account create/update unconstrained request + bypass | `accounts.py`, `account_service.py` | High |
| F2 | Trade create/update unconstrained numerics + bypass | `trades.py`, `trade_service.py` | High |
| F3 | Plan create/update/status plain strings, raw dict flow | `plans.py`, `report_service.py` | High |
| F4 | Schedule PATCH raw query params bypass | `scheduling.py`, `scheduling_service.py` | High |
| F5 | Provider config + email unconstrained fields | `market_data.py`, `email_settings.py`, services | High |
| F6 | Watchlist blank strings + MCP unconstrained | `watchlists.py`, MCP tools | Medium |
| F7 | UI hooks no pre-validation | UI mutation hooks | Medium |

Tracked in `known-issues.md` under `[BOUNDARY-GAP]`.

## Verification Plan

```powershell
# Verify all 12 files were updated
rg -n "Boundary" AGENTS.md .agent/workflows/ .agent/skills/ .agent/docs/ .agent/roles/
rg -n "AV-7|AV-8|AV-9|IR-6" .agent/workflows/validation-review.md .agent/workflows/critical-review-feedback.md
rg -n "extra.*forbid|Forbidden Boundary" .agent/docs/code-quality.md
rg -n "Write-Boundary" .agent/docs/testing-strategy.md
rg -n "boundary validation" .agent/roles/reviewer.md
```
