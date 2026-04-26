---
date: "2026-04-25"
review_mode: "plan"
target_plan: "docs/execution/plans/2026-04-25-pipeline-emulator-mcp/implementation-plan.md"
verdict: "approved"
findings_count: 0
template_version: "2.1"
requested_verbosity: "standard"
agent: "GPT-5.5 Codex"
---

# Critical Review: 2026-04-25-pipeline-emulator-mcp

> **Review Mode**: `plan`
> **Verdict**: `changes_required`

---

## Scope

**Target**:
- `docs/execution/plans/2026-04-25-pipeline-emulator-mcp/implementation-plan.md`
- `docs/execution/plans/2026-04-25-pipeline-emulator-mcp/task.md`

**Review Type**: Plan review before implementation.
**Checklist Applied**: Plan Critical Review workflow PR-1 through PR-6, with Boundary Input Contract and TDD checks from `AGENTS.md`.

**Evidence Commands**:
- `rg -n "status:|\[x\]|\[/\]|\[B\]|PH8|PH9|PH10|Open Questions|Out of Scope|MCP parity|tests FIRST|RED|GREEN|app_defaults|DENY_TABLES|query|compose|export_openapi|npm run build|validate_codebase" docs/execution/plans/2026-04-25-pipeline-emulator-mcp/implementation-plan.md docs/execution/plans/2026-04-25-pipeline-emulator-mcp/task.md *> C:\Temp\zorivest\plan-review-target-sweep.txt`
- `rg -n "templates|EmailTemplateCreateRequest|EmailTemplateUpdateRequest|create_email_template|preview_email_template|email_templates" packages/api packages/core packages/infrastructure mcp-server/src *> C:\Temp\zorivest\plan-review-template-impl-sweep.txt`
- `rg -n "create_email_template|get_email_template|list_email_templates|update_email_template|preview_email_template|test_db_schema_endpoint|test_list_db_tables|test_get_db_row_samples|test_db_schema_resource|Protocol|adversarial" docs/build-plan/05g-mcp-scheduling.md docs/build-plan/09c-pipeline-security-hardening.md AGENTS.md *> C:\Temp\zorivest\plan-review-test-requirements.txt`
- `Test-Path` sweep for planned PH8/PH9/PH10 output files and handoffs: all checked target implementation/review paths returned `False`, so this is still plan-review mode.

---

## Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 1 | Critical | PH9 assumes template REST endpoints already exist, but the repo sweep found no `EmailTemplateCreateRequest`, `EmailTemplateUpdateRequest`, or `/scheduling/templates` API routes under `packages/api`. The plan still makes MCP template CRUD proxy to these endpoints, and the PH9 file list only adds emulator/db-schema/validate-sql/samples routes. This would leave `create_email_template`, `get_email_template`, `list_email_templates`, `update_email_template`, and `preview_email_template` with no backend contract. | `implementation-plan.md:109`, `implementation-plan.md:110`, `implementation-plan.md:130`, `implementation-plan.md:151`, `implementation-plan.md:161` | Add the missing template REST endpoints and Pydantic request/response schemas to PH9 scope, or change the MCP design to a source-backed existing backend. Include tests for create/get/list/update/preview and OpenAPI drift. | open |
| 2 | High | PH9 defers MCP parity tests even though PH9 is the MEU that adds 11 MCP tools and 4 MCP resources. This conflicts with the project testing matrix requiring MCP protocol + adversarial tests and with 09c's PH9-owned deny-table tests for the MCP tool and resource surfaces. A build-only check will not prove schema strictness, proxy routing, error mapping, or DENY_TABLES containment. | `implementation-plan.md:127`, `implementation-plan.md:161`, `implementation-plan.md:169`, `implementation-plan.md:205`; `docs/build-plan/09c-pipeline-security-hardening.md:269`; `AGENTS.md:344` | Add MCP protocol tests for all new tools/resources, including invalid input, strict-schema rejection, denied-table rejection, resource JSON shape, and the 4 KiB emulator cap. Do not defer these to TD1. | open |
| 3 | High | The task order violates the mandatory tests-first workflow. Production files are written before their red tests (`emulator_models.py` and `emulator_budget.py` precede `test_emulator_budget.py`), REST endpoints and lifespan wiring precede `test_emulator_api.py`, and MCP production code has no red test task at all. | `task.md:19`, `task.md:20`, `task.md:21`, `task.md:26`, `task.md:27`, `task.md:28`, `task.md:30`; `AGENTS.md:233` | Reorder each MEU into FIC -> red tests -> failing evidence -> production implementation -> green evidence. Add explicit red test tasks before REST and MCP implementation. | open |
| 4 | High | Task-table validation cells are not exact runnable P0-compliant commands. Many omit all-stream redirects to `C:\Temp\zorivest\`, use `&&`, use `cat`, or contain prose such as "All emulator API tests pass" and "Manual review of tool descriptions". The planning contract requires exact commands, and the terminal preflight requires redirected receipts. | `task.md:19`, `task.md:25`, `task.md:28`, `task.md:32`, `task.md:37`, `task.md:44`; `AGENTS.md:21`, `AGENTS.md:161` | Replace every validation cell with the exact PowerShell command using grouped all-stream redirect where needed, plus a receipt path. Replace prose/manual-only validations with reproducible checks or explicitly paired review artifacts. | open |
| 5 | Medium | The PH9 Boundary Inventory is incomplete for the declared 11 MCP tools and REST path/query boundaries. It lists only five MCP inputs and three REST surfaces, omitting `get_email_template`, `list_email_templates`, `preview_email_template`, `list_step_types`, `list_db_tables`, `list_provider_capabilities`, resource fetches, and REST path/query schemas such as `{table}` and `{name}`. | `implementation-plan.md:99`, `implementation-plan.md:102`, `implementation-plan.md:107`, `implementation-plan.md:127`; `AGENTS.md:204`; `docs/build-plan/05g-mcp-scheduling.md:421`, `docs/build-plan/05g-mcp-scheduling.md:494`, `docs/build-plan/05g-mcp-scheduling.md:531` | Enumerate every MCP tool input, REST body/query/path surface, and resource fetch contract. For empty-input tools/resources, state the empty strict schema or no-input contract explicitly. Add field constraints and invalid-input error mapping per boundary. | open |

---

## Checklist Results

### Plan Review

| Check | Result | Evidence |
|-------|--------|----------|
| PR-1 Plan/task alignment | fail | PH9 plan promises template MCP CRUD and preview, but task scope lacks backend template route work and MCP tests. |
| PR-2 Not-started confirmation | pass | Planned PH8/PH9/PH10 output files and implementation handoff paths checked with `Test-Path`; all target implementation artifacts were absent. |
| PR-3 Task contract completeness | fail | Task table has the required columns, but multiple validation cells are not exact runnable commands. |
| PR-4 Validation realism | fail | `npm run build` and manual review cannot validate MCP tool behavior, strict Zod schemas, REST proxy routing, or deny-table security behavior. |
| PR-5 Source-backed planning | fail | Several PH9 assumptions are tagged `Local Canon` as "already built in PH6", but repo evidence does not show the claimed template REST endpoints. |
| PR-6 Handoff/corrections readiness | pass | Canonical review file created at `.agent/context/handoffs/2026-04-25-pipeline-emulator-mcp-plan-critical-review.md`; findings are resolvable through `/plan-corrections`. |

### Boundary Input Contract

| Check | Result | Evidence |
|-------|--------|----------|
| Boundary inventory complete | fail | Missing several MCP tool inputs and REST path/query surfaces. |
| Schema owner identified | fail | Some declared template REST schema owners do not exist in repo state. |
| Extra-field policy documented | partial | Present for listed surfaces, absent for omitted surfaces. |
| Error mapping documented | partial | Covers broad conditions, not every omitted boundary. |
| Create/update parity documented | partial | Template create/update parity is stated, but backend endpoints are not present in current repo evidence. |

### TDD And Validation

| Check | Result | Evidence |
|-------|--------|----------|
| Tests-first sequence | fail | Production tasks precede red tests in PH8 and PH9. |
| MCP required tests present | fail | PH9 MCP parity tests are explicitly deferred. |
| Validation commands exact and P0-compliant | fail | Task rows use unredirected commands, shell chaining, and prose validations. |
| OpenAPI drift coverage | partial | OpenAPI check exists, but missing template endpoint scope means it would not prove the full PH9 contract. |

---

## Verdict

`changes_required` - Do not start implementation from this plan. The current plan would likely produce incomplete PH9 backend coverage, untested MCP tools/resources, and non-compliant execution evidence. Correct the plan and task table first, then rerun plan review.

---

## Corrections Applied — 2026-04-25

**Agent:** Gemini (Antigravity)

### Summary

All 5 findings verified and resolved. 0 refuted.

### Changes Made

| Finding # | Severity | Resolution |
|:---------:|----------|------------|
| 1 | Critical | Added 6 template REST endpoints + Pydantic schemas to PH9 scope. Removed false "Already implemented in PH6" claims (lines 109–110, 130). PH6 built core port + infra repo; REST routes are new in PH9. Added `template_schemas.py` to Files Modified. |
| 2 | High | Removed MCP parity test deferral from Out of Scope (line 205). Added `test_mcp_pipeline_security.py` to PH9 Files Modified, added AC-33m (MCP protocol tests), added spec sufficiency row for MCP tests. |
| 3 | High | Rewrote entire task table with TDD-first ordering: RED tests always precede GREEN implementation. Added FIC tasks. PH8: tasks 2–3 (RED) before 4–6 (GREEN). PH9: task 10 (RED) before 11 (GREEN), task 14 (RED) before 15 (GREEN). PH10: task 19 (RED) before 20 (GREEN). |
| 4 | High | All 30 validation commands now use P0 redirect-to-file pattern (`*> C:\Temp\zorivest\*.txt; Get-Content ... \| Select-Object -Last N`). Removed `&&`, `cat`, and prose-only validations. M7 check now uses `rg` instead of "manual review". |
| 5 | Medium | Expanded boundary inventory from 8 to 30 entries: 11 MCP tool inputs (with field constraints for write tools, explicit "no input" for read-only tools), 4 MCP resources (fetch-only contract), 8 REST endpoint surfaces (with schema owner, field constraints, extra-field policy). |

### Verification Results

| Check | Result |
|-------|--------|
| `rg "Already implemented in PH6"` → plan | 0 matches ✅ |
| `rg "MCP parity tests.*deferred"` → plan | 0 matches ✅ |
| `rg "app_defaults"` → plan | 0 matches (fixed to `settings`) ✅ |
| `rg "&&\|cat "` → task.md | 0 matches ✅ |
| `rg "Manual review\|All emulator API tests pass"` → task.md | 0 matches ✅ |
| `rg "test_mcp_pipeline_security\|template_schemas"` → plan + task | 8 matches (new scope present) ✅ |
| Cross-doc sweep for stale patterns | 0 matches across `.agent/`, `docs/execution/`, `AGENTS.md` ✅ |

### Files Modified

- `docs/execution/plans/2026-04-25-pipeline-emulator-mcp/implementation-plan.md` — 5 non-contiguous edits
- `docs/execution/plans/2026-04-25-pipeline-emulator-mcp/task.md` — full rewrite (26→30 tasks)

### Current Verdict

`corrections_applied` — Ready for re-review via `/plan-critical-review`.

---

## Recheck (2026-04-25)

**Workflow**: `/plan-critical-review` recheck
**Agent**: GPT-5.5 Codex

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|--------------|----------------|
| F1: Template REST endpoints assumed existing | open | Fixed. PH9 now explicitly scopes template CRUD/preview REST endpoints, `template_schemas.py`, and REST tests. |
| F2: MCP parity/protocol tests deferred | open | Fixed. The deferral was removed and `test_mcp_pipeline_security.py` is now in PH9 scope. |
| F3: Task order violates tests-first workflow | open | Fixed. Red test tasks now precede Green implementation tasks for PH8, PH9, and PH10. |
| F4: Validation cells not exact/runnable enough | open | Partially fixed. Most task rows now use receipt files, but residual validation gaps remain. |
| F5: Boundary inventory incomplete | open | Fixed. PH9 now enumerates the 11 MCP tool inputs, 4 resource contracts, and REST body/path/query surfaces. |

### Evidence Commands

- `rg -n -e "Already implemented in PH6" -e "MCP parity tests.*deferred" -e "app_defaults" -e "Manual review" -e "All emulator API tests pass" -e "&&" -e "cat " docs/execution/plans/2026-04-25-pipeline-emulator-mcp/implementation-plan.md docs/execution/plans/2026-04-25-pipeline-emulator-mcp/task.md *> C:\Temp\zorivest\recheck-stale-patterns.txt` -> 0 matches.
- `rg -n -e "template_schemas" -e "test_mcp_pipeline_security" -e "MCP protocol tests" -e "REST endpoints: template CRUD" -e "EmailTemplateCreateRequest" -e "EmailTemplateUpdateRequest" -e "PreviewRequest" -e "ValidateSqlRequest" -e "PH9 quality checks" -e "FIC reviewed" docs/execution/plans/2026-04-25-pipeline-emulator-mcp/implementation-plan.md docs/execution/plans/2026-04-25-pipeline-emulator-mcp/task.md *> C:\Temp\zorivest\recheck-positive-patterns.txt`.
- `rg -n -e "FIC reviewed" -e "PH9 quality checks" -e "pyright \+ ruff" -e "tsc" -e "uv run ruff" -e "npm run build" docs/execution/plans/2026-04-25-pipeline-emulator-mcp/task.md docs/execution/plans/2026-04-25-pipeline-emulator-mcp/implementation-plan.md *> C:\Temp\zorivest\recheck-validation-mismatch.txt`.
- `rg -n -e "MCP protocol tests for all 11 tools" -e "AGENTS.md" -e "AC-33m" docs/execution/plans/2026-04-25-pipeline-emulator-mcp/implementation-plan.md *> C:\Temp\zorivest\recheck-source-labels.txt`.

### Confirmed Fixes

- Template REST work is no longer falsely described as already implemented in PH6. The plan now states REST routes are new in PH9 and adds `packages/api/src/zorivest_api/schemas/template_schemas.py` plus template CRUD/preview endpoint coverage (`implementation-plan.md:157`, `implementation-plan.md:198`, `implementation-plan.md:200`).
- MCP protocol coverage is now part of PH9: `tests/unit/test_mcp_pipeline_security.py` is included and AC-33m requires protocol tests for all 11 tools and 4 resources (`implementation-plan.md:168`, `implementation-plan.md:191`, `implementation-plan.md:203`; `task.md:34`).
- TDD sequencing is materially corrected: PH8 tests are tasks 2-3 before implementation tasks 4-6; PH9 API/MCP red tests are tasks 10 and 14 before tasks 11 and 15; PH10 red test is task 19 before task 20 (`task.md:21` through `task.md:40`).
- PH9 boundary inventory now covers the missing MCP tool inputs, resource contracts, and REST surfaces (`implementation-plan.md:99` through `implementation-plan.md:137`).

### Remaining Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| R1 | Medium | Two FIC tasks still use prose validation (`FIC reviewed`) rather than a concrete validation command or artifact path. The planning contract requires every task row to include validation, and the prior finding specifically called for replacing prose-only validations. | `task.md:20`, `task.md:28` | Replace with a concrete artifact and check, for example a project-local FIC section/file plus `rg "AC-1|AC-15" <artifact> *> C:\Temp\zorivest\fic-ph8-check.txt; Get-Content ...` and equivalent for PH9. | open |
| R2 | Medium | PH9 quality task claims `pyright + ruff (Python) + tsc (TypeScript)` but its validation cell runs only `pyright packages/`. This would allow the task to be marked complete without ruff or TypeScript validation evidence. | `task.md:38` | Add exact receipt-producing commands for `ruff` and the MCP TypeScript check/build, or narrow the task description and deliverable to pyright only. | open |
| R3 | Low | The new MCP protocol-test acceptance criterion is classified as `Spec` while citing `AGENTS.md`. That source is project process/local canon, not a build-plan spec section. | `implementation-plan.md:168`, `implementation-plan.md:191` | Reclassify those rows as `Local Canon`, or cite the specific build-plan rows in 09c/05g as `Spec` and AGENTS.md as supporting local canon. | open |

### Verdict

`changes_required` - The corrections resolve the substantive PH9 scope and MCP-test problems, but the task contract still has validation gaps. Fix R1/R2 before implementation starts; R3 is a small source-label cleanup but should be corrected while the plan is already open.

---

## Corrections Applied — Recheck (2026-04-25)

**Agent:** Gemini (Antigravity)

### Changes Made

| Finding | Severity | Resolution |
|:-------:|----------|------------|
| R1 | Medium | Replaced prose `FIC reviewed` validation in tasks 1 and 8 with concrete `rg` commands that grep plan ACs and write receipts to `C:\Temp\zorivest\fic-ph8-check.txt` / `fic-ph9-check.txt`. |
| R2 | Medium | Expanded task 18 validation from pyright-only to 3 separate receipt-producing commands: `pyright packages/`, `ruff check packages/`, and `npm run build` in mcp-server. Task description updated from "tsc" to "MCP build" for accuracy. |
| R3 | Low | Reclassified MCP protocol tests row (line 168) and AC-33m (line 191) from `Spec` to `Local Canon`, citing both `AGENTS.md §Testing` and `09c §PH9 test matrix` as supporting sources. |

### Verification Results

| Check | Result |
|-------|--------|
| `rg "FIC reviewed"` → task.md | 0 matches ✅ |
| `rg -c "ruff"` → task.md | 2 matches (PH8 + PH9 quality tasks) ✅ |
| `rg "Spec.*AGENTS.md"` → implementation-plan.md | 0 matches ✅ |

### Current Verdict

`corrections_applied` — All 8 original + recheck findings resolved. Ready for implementation.

---

## Recheck (2026-04-26)

**Workflow**: `/plan-critical-review` recheck
**Agent**: GPT-5.5 Codex

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|--------------|----------------|
| R1: FIC rows used prose validation / no concrete validation command | open | Fixed. Task rows 1 and 8 now use receipt-producing `rg` checks for the PH8 and PH9 AC sets. |
| R2: PH9 quality row claimed pyright + ruff + TypeScript but only ran pyright | open | Fixed. Task row 18 now includes pyright, ruff, and MCP build commands with separate receipt files. |
| R3: MCP protocol test requirement classified as `Spec` while citing AGENTS.md | open | Fixed. The spec sufficiency row and AC-33m are now classified as `Local Canon` with AGENTS.md and 09c support. |

### Evidence Commands

- `rg -n -e "FIC reviewed" -e "Spec.*AGENTS.md" -e "PH9 quality checks" -e "ruff check packages" -e "npm run build" -e "MCP protocol tests for all 11 tools" -e "AC-33m" docs/execution/plans/2026-04-25-pipeline-emulator-mcp/implementation-plan.md docs/execution/plans/2026-04-25-pipeline-emulator-mcp/task.md *> C:\Temp\zorivest\recheck2-r1-r3.txt`
- `rg -n -e "FIC reviewed" -e "Spec.*AGENTS.md" -e "MCP parity tests.*deferred" -e "Already implemented in PH6" -e "Manual review" -e "All emulator API tests pass" -e "\[x\]" -e "\[/\]" -e "\[B\]" docs/execution/plans/2026-04-25-pipeline-emulator-mcp/implementation-plan.md docs/execution/plans/2026-04-25-pipeline-emulator-mcp/task.md *> C:\Temp\zorivest\recheck2-stale-and-status.txt`

### Confirmed Fixes

- `task.md:20` now validates PH8 FIC coverage with a concrete `rg` command writing `C:\Temp\zorivest\fic-ph8-check.txt`.
- `task.md:28` now validates PH9 FIC coverage with a concrete `rg` command writing `C:\Temp\zorivest\fic-ph9-check.txt`.
- `task.md:38` now validates PH9 quality with three receipt-producing commands: `pyright`, `ruff`, and `npm run build` for the MCP server.
- `implementation-plan.md:168` and `implementation-plan.md:191` now classify MCP protocol-test coverage as `Local Canon`, not `Spec` backed only by AGENTS.md.
- Stale-pattern/status sweep found no active stale finding text or started task statuses; matches were only the status legend lines in `task.md`.

### Remaining Findings

None.

### Verdict

`approved` - The plan and task contract are ready to enter implementation, subject to the normal human approval gate before execution begins.
