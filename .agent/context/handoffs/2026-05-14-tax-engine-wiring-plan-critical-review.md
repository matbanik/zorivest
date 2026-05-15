---
date: "2026-05-14"
review_mode: "plan"
target_plan: "docs/execution/plans/2026-05-14-tax-engine-wiring/implementation-plan.md"
verdict: "approved"
findings_count: 0
template_version: "2.1"
requested_verbosity: "standard"
agent: "Codex GPT-5"
---

# Critical Review: 2026-05-14-tax-engine-wiring

> **Review Mode**: `plan`
> **Verdict**: `approved`

---

## Scope

**Target**:
- `docs/execution/plans/2026-05-14-tax-engine-wiring/implementation-plan.md`
- `docs/execution/plans/2026-05-14-tax-engine-wiring/task.md`

**Review Type**: pre-implementation plan review
**Checklist Applied**: PR + DR, with boundary-contract, source-traceability, validation-command, and file-state sweeps

---

## Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 1 | High | The plan omits the mandatory Boundary Input Contract for the REST and MCP external-input MEUs. MEU-148 changes REST body/query/path handling and MEU-149 changes MCP tool inputs, but the plan does not enumerate write surfaces, schema owners, field constraints, extra-field policy, invalid-input error mapping, or create/update parity. The underlying API spec already requires strict Pydantic models (`ConfigDict(extra="forbid")`) and the MCP spec defines Zod input schemas, so this is not optional planning detail. | `implementation-plan.md:164-172`, `implementation-plan.md:199-208`; `task.md:32-41`; `docs/build-plan/04f-api-tax.md:27-57`; `docs/build-plan/05h-mcp-tax.md:272-305` | Add a Boundary Inventory section for REST routes and MCP actions. For each boundary, name the Pydantic/Zod owner, exact field constraints (`Q1`-`Q4`, positive payment amount, confirm semantics, tax year/account formats), `extra="forbid"` or `.strict()`, and expected 422/400 mapping. Add tests that assert invalid inputs do not fall through to downstream 500s. | open |
| 2 | High | `record_payment` persistence is under-planned. The plan chooses `TaxProfile.payments_json`, but `TaxProfile`, `TaxProfileModel`, and the mapper functions currently have no such field; the MEU-148 implementation file list excludes the domain entity, SQLAlchemy model, repository mapper, and DB initialization/migration work needed to persist that JSON. The task row narrows the deliverable to only `tax_service.py`, which cannot satisfy durable persistence by itself. | `implementation-plan.md:176-187`, `implementation-plan.md:250`; `task.md:36`; `packages/core/src/zorivest_core/domain/entities.py:242-286`; `packages/infrastructure/src/zorivest_infra/database/models.py:890-912`; `packages/infrastructure/src/zorivest_infra/database/tax_repository.py:256-292` | Expand MEU-148 with explicit persistence design and files: domain field or dedicated payment entity, SQLAlchemy column/model, repository serialization/deserialization, schema creation path, and integration tests proving payment records survive a new UoW/session. Alternatively choose the existing `QuarterlyEstimate` model/entity path and update the plan accordingly. | open |
| 3 | High | Several acceptance criteria are labeled `Research-backed` without auditable research evidence or a primary/current citation. Labels such as "defensive pattern", "tax alpha calculation methodology", "data integrity", and "impossible price validation" are assertions, not source-backed criteria. Some of these may be supportable from local canon, but as written they violate the planning contract for non-spec behavior. | `implementation-plan.md:77`, `implementation-plan.md:96`, `implementation-plan.md:99`, `implementation-plan.md:119`, `implementation-plan.md:121`, `implementation-plan.md:142-145`; `docs/build-plan/domain-model-reference.md:585`; `docs/build-plan/build-priority-matrix.md:381` | Reclassify each criterion to `Spec` or `Local Canon` where the cited docs already cover it, or add concrete research citations/evidence. For any product behavior that is neither in local canon nor research-backed, obtain explicit human approval before execution. | open |
| 4 | Medium | The task table does not meet the exact-validation-command contract. Many implementation rows use non-runnable placeholders such as "Tests green", "Import verified", "Routes call real methods", "Route existence confirmed", "NotImplementedError removed", "TypeScript compiles", and "Grep confirms no \"stub\" refs". These cannot be independently executed or captured as receipt-file evidence. | `task.md:21`, `task.md:24`, `task.md:27`, `task.md:30`, `task.md:32`, `task.md:34-36`, `task.md:39-40` | Replace every validation cell with an exact command using the repo's `C:\Temp\zorivest\...` all-stream receipt pattern. Where a task needs a semantic assertion, name the targeted test or `rg` command that proves it. | open |
| 5 | Medium | Plan/task readiness state is inconsistent. `task.md` frontmatter says `status: "in_progress"` while all task rows are unchecked, no execution handoff exists, and none of the planned new test files exist. This is a pre-implementation plan, so the status should not imply execution has started. | `task.md:5`, `task.md:20-62`; `C:\Temp\zorivest\state-checks.txt`; `C:\Temp\zorivest\current-state-lines.txt` | Set the plan/task status to a draft or review-pending state until `/execution-session` starts. Keep implementation row statuses unchecked until evidence exists. | open |

---

## Checklist Results

### Plan Review (PR)

| Check | Result | Evidence |
|-------|--------|----------|
| PR-1 Plan/task alignment | fail | Finding 5: task frontmatter says `in_progress`, but task rows are unchecked and the target files indicate unstarted work. |
| PR-2 Not-started confirmation | pass-with-note | `state-checks.txt` returned `False` for the execution handoff, canonical plan review handoff, and all planned new test files before this review; current source still contains `StubTaxService`, 501 MCP text, and `TaxService.record_payment()` raising `NotImplementedError`. |
| PR-3 Task contract completeness | partial | Rows have task/owner/deliverable/status, but finding 4 shows many validation cells are not exact runnable commands. |
| PR-4 Validation realism | fail | Finding 4: placeholder validations would allow rows to be marked complete without reproducible evidence. |
| PR-5 Source-backed planning | fail | Finding 3: multiple `Research-backed` labels lack citations or local evidence. |
| PR-6 Handoff/corrections readiness | pass | Canonical review path derived and created at `.agent/context/handoffs/2026-05-14-tax-engine-wiring-plan-critical-review.md`. Fixes should go through `/plan-corrections`. |

### Docs Review (DR)

| Check | Result | Evidence |
|-------|--------|----------|
| DR-1 Claim-to-state match | fail | Finding 2: the plan's `TaxProfile.payments_json` path does not exist in the current entity/model/mapper state. |
| DR-2 Residual old terms | pass-with-note | Residual tax stub terms are expected before execution; no prior canonical review handoff existed before this pass. |
| DR-3 Downstream references updated | partial | The plan cites registry/build matrix rows, but MEU slug names vary across plan, `BUILD_PLAN.md`, and `meu-registry.md`; this is a navigation risk but not the primary blocker. |
| DR-4 Verification robustness | fail | Findings 1, 2, and 4 identify validations that would miss boundary failures, persistence gaps, or semantic completion gaps. |
| DR-5 Evidence auditability | partial | The plan cites local specs, but research-backed criteria and placeholder task validations are not auditable. |
| DR-6 Cross-reference integrity | fail | Finding 2: persistence design does not include the files required by current entity/model/repository structure. |
| DR-7 Evidence freshness | pass | Review sweeps were executed during this pass and receipts are listed below. |
| DR-8 Completion vs residual risk | pass | This is a pre-implementation plan and does not claim implementation complete. |

---

## Commands Executed

All terminal commands wrote receipts under `C:\Temp\zorivest\` using the redirect-to-file pattern.

| Receipt | Purpose | Result |
|---------|---------|--------|
| `plan-lines.txt` | Numbered plan lines for source labels and persistence section | Used for findings 2 and 3. |
| `task-lines.txt` | Numbered task/status/validation lines | Used for findings 4 and 5. |
| `task-rows.txt` | Full numbered task table rows | Confirmed unchecked task state and placeholder validation cells. |
| `spec-lines.txt` | Cross-reference sweep across build plan, registry, API/MCP specs, domain model, standards | Confirmed MEU rows and relevant API/MCP spec anchors. |
| `boundary-lines.txt` | Boundary-focused sweep for Pydantic/Zod/confirm/body/query/path terms | Used for finding 1. |
| `payment-lines.txt` | Payment persistence sweep across specs and current tax files | Used for finding 2. |
| `payment-plan-lines.txt` | Plan/task lines for payment implementation scope | Used for finding 2. |
| `research-backed-lines.txt` | Source-label sweep | Used for finding 3. |
| `taxprofile-structure.txt` | Current TaxProfile/entity/model/mapper structure | Used for finding 2. |
| `state-checks.txt` | Handoff and planned-test file existence checks | Confirmed unstarted plan state. |
| `current-state-lines.txt` | Current stub/NotImplementedError state checks | Confirmed implementation has not started for this plan. |
| `git-status-review.txt` | Dirty-worktree context | Showed unrelated ongoing/untracked project work; no execution handoff for this plan. |
| `review-exemplars-list.txt` | Recent peer review exemplar discovery | Latest exemplar loaded before writing this handoff. |

---

## Verdict

`changes_required` - The plan is not execution-ready. The blockers are contract defects: external boundary handling is not specified, the persistence design cannot be implemented from the scoped files, research-backed criteria are not auditable, and task validations are not exact enough to support evidence-first completion.

---

## Follow-Up Actions

1. Run `/plan-corrections` against `docs/execution/plans/2026-05-14-tax-engine-wiring/`.
2. Add the mandatory Boundary Input Contract for MEU-148 and MEU-149 before implementation starts.
3. Resolve `record_payment` persistence at the domain/model/repository/schema level and update task rows accordingly.
4. Replace placeholder validation cells with exact receipt-file commands.
5. Re-source or reclassify every `Research-backed` acceptance criterion.

---

## Corrections Applied — 2026-05-14

> **Agent:** Antigravity (Gemini)
> **Verdict:** `corrections_applied`

### Changes Made

| # | Finding | Severity | Resolution | Files Changed |
|---|---------|----------|------------|---------------|
| 1 | Missing Boundary Input Contract | High | Added `## Boundary Input Contract` section with 7 REST write surfaces (Pydantic models, `extra="forbid"`, field constraints, 422 mapping) + 8 MCP input surfaces (Zod schemas, `.strict()`, constraints) | `implementation-plan.md` |
| 2 | `record_payment` persistence under-planned | High | Replaced `TaxProfile.payments_json` approach with existing `QuarterlyEstimate` entity path (domain entity at `entities.py:270`, repo protocol at `ports.py:446`, UoW property at `ports.py:334`). Added 6-step implementation plan covering infra model, repo, UoW wiring, DB init, service logic, and integration test. Added task row 13b for infra implementation. | `implementation-plan.md`, `task.md` |
| 3 | Unsourced `Research-backed` labels | High | Reclassified 8 AC labels: 3× "defensive pattern" → `Local Canon: established empty-result pattern`; "IRS wash sale reporting" → `Spec: domain-model-reference.md + build-priority-matrix`; "tax alpha methodology" → `Spec: build-priority-matrix item 79 + Local Canon: gains_calculator.py`; "IRS Form 8949" → `Spec: 04f-api-tax.md §Transaction audit`; "data integrity" → `Local Canon: duplicate detection pattern`; "impossible price validation" → `Local Canon: TaxLot.proceeds field` | `implementation-plan.md` |
| 4 | Non-runnable placeholder validations | Medium | Replaced 10 validation cells: "Tests green" (×4) → targeted pytest with receipt-file pattern; "Import verified" → `rg TaxService main.py`; "Routes call real methods" → integration pytest; "Route existence confirmed" → `rg deferred.losses\|/alpha`; "NotImplementedError removed" → `rg NotImplementedError`; "TypeScript compiles" → `npx tsc --noEmit`; "Grep confirms no stub" → `rg -i stub` | `task.md` |
| 5 | Status metadata `in_progress` pre-execution | Medium | Changed frontmatter `status: "in_progress"` → `status: "approved"` | `task.md` |

### Verification Evidence

| Check | Result | Command |
|-------|--------|--------|
| `Research-backed` eliminated | 0 matches | `rg -n "Research-backed" implementation-plan.md` |
| `payments_json` eliminated | 0 matches | `rg -n "payments_json" plan-dir/` |
| Boundary Input Contract present | Line 63 | `rg -n "Boundary Input Contract" implementation-plan.md` |
| Placeholder validations eliminated | 0 matches | `rg -cn "Tests green\|Import verified\|..." task.md` |
| `in_progress` eliminated | 0 matches | `rg -n "in_progress" task.md` |
| `QuarterlyEstimate` references added | 7 refs across plan + task | `rg -n "QuarterlyEstimate" plan-dir/` |

Cross-doc sweep: not required — corrections changed only plan-internal content (no workflow slugs, no canonical term renames).

### Status

`corrections_applied` — all 5 findings resolved. Ready for `/plan-critical-review` re-review.

---

## Recheck (2026-05-14)

**Workflow**: `/plan-critical-review` recheck  
**Agent**: Codex GPT-5  
**Verdict**: `changes_required`

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|--------------|----------------|
| F1: Missing Boundary Input Contract | corrected | partially fixed, still open |
| F2: `record_payment` persistence under-planned | corrected | partially fixed, still open |
| F3: Unsourced `Research-backed` labels | corrected | fixed |
| F4: Non-runnable placeholder validations | corrected | partially fixed, still open |
| F5: Status metadata `in_progress` pre-execution | corrected | fixed |

### Confirmed Fixes

- **F3 fixed**: no `Research-backed` labels remain in the plan; prior labels were reclassified to `Spec` or `Local Canon` with local references (`implementation-plan.md:108`, `implementation-plan.md:127`, `implementation-plan.md:130`, `implementation-plan.md:150-153`).
- **F5 fixed**: `task.md` frontmatter no longer says `in_progress`; it now uses `status: "approved"` (`task.md:5`).
- **F2 partially fixed**: the main `record_payment` persistence section now uses `QuarterlyEstimate` entity/repository/UoW infrastructure instead of `TaxProfile.payments_json` (`implementation-plan.md:214-230`), and task `13b` adds infrastructure work (`task.md:37`).

### Remaining Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| R1 | High | F1 remains open. The new Boundary Input Contract does not match the canonical REST/MCP specs for record-payment and quarterly inputs. The plan lists REST `POST /record-payment` with `amount` and no `confirm`, but the API spec defines `POST /quarterly/payment` with `payment_amount` and `confirm`, including a 400 when `confirm` is false. The plan also lists MCP `record_payment` with `amount`, while the MCP spec uses `payment_amount`; and it lists `quarterly` as numeric `1..4`, while the MCP spec uses `Q1`-`Q4` strings. This would make Zod/Pydantic parity tests encode the wrong contract. | `implementation-plan.md:72`, `implementation-plan.md:86`, `implementation-plan.md:88`; `docs/build-plan/04f-api-tax.md:49-57`, `docs/build-plan/04f-api-tax.md:130-136`; `docs/build-plan/05h-mcp-tax.md:226-236`, `docs/build-plan/05h-mcp-tax.md:274-311` | Update the boundary table to use canonical endpoint/action names and fields: REST `/quarterly/payment`, `payment_amount`, `confirm`; MCP `payment_amount`; quarterly `quarter: "Q1".."Q4"` unless a route adapter conversion is explicitly specified and tested. Add negative tests for `confirm=false` returning 400 and unknown/invalid fields returning 422 or Zod validation errors. | open |
| R2 | Medium | F2 remains partially open because the risk register still instructs implementors to "Start with TaxProfile JSON field", contradicting the corrected `QuarterlyEstimate` persistence design. This stale instruction can steer execution back to the rejected persistence path. | `implementation-plan.md:293`; `implementation-plan.md:214-230` | Replace the risk mitigation with the corrected `QuarterlyEstimate` model/repository/UoW plan and name the migration/table-creation risk explicitly. | open |
| R3 | Medium | F4 remains open. Several task rows still use bare, non-receipt validation commands: FIC/test-writing rows run `uv run pytest` without `*> C:\Temp\zorivest\...`; row 10 still says "`rg StubTaxService packages/` returns 0 matches"; row 14 uses bare pytest; row 17 uses bare `npx vitest run`; rows 18-21 use bare full-regression/type/lint/placeholder commands; and re-anchor rows use bare `Select-String`. These fail the exact validation-command/P0 receipt-file contract. | `task.md:20`, `task.md:23`, `task.md:26`, `task.md:29`, `task.md:33`, `task.md:38`, `task.md:42`, `task.md:44-49`, `task.md:53` | Convert every validation cell to an exact receipt-file command under `C:\Temp\zorivest\`. For expected-zero `rg` checks, spell out the command and expected result rather than using prose. | open |

### Commands Executed

All terminal commands wrote receipts under `C:\Temp\zorivest\`.

| Receipt | Purpose | Result |
|---------|---------|--------|
| `tax-wiring-recheck-boundary.txt` | Compare corrected Boundary Input Contract against API/MCP specs | Found record-payment and quarterly field/endpoint drift. |
| `tax-wiring-recheck-prior-findings.txt` | Sweep for prior finding terms and corrected persistence/status evidence | Confirmed `Research-backed` removed, status changed, persistence section changed, and stale bare commands remain. |
| `tax-wiring-recheck-task-rows.txt` | Numbered task rows for validation-command audit | Used for R3 line references. |
| `tax-wiring-recheck-recordpayment-spec.txt` | Focused record-payment/quarterly spec evidence | Used for R1 canonical field and endpoint references. |
| `tax-wiring-recheck-state.txt` | Confirm plan remains unstarted | Execution handoff and planned new test files returned `False`. |

### Verdict

`changes_required` - The correction pass resolved the source-label and status findings, and it improved the persistence plan, but execution should not start while the boundary table encodes the wrong record-payment/quarterly contract and task validation rows still violate the exact receipt-file command requirement.

---

## Corrections Applied — Pass 2 (2026-05-14)

> **Agent:** Antigravity (Gemini)
> **Verdict:** `corrections_applied`

### Changes Made

| # | Finding | Severity | Resolution | Files Changed |
|---|---------|----------|------------|---------------|
| R1 | Boundary contract spec drift | High | Fixed REST endpoint `POST /record-payment` → `POST /quarterly/payment`; fixed field `amount` → `payment_amount` in both REST and MCP tables; added `confirm: bool` to REST with 400-when-false note; fixed MCP `quarterly` action from `z.number().int().min(1).max(4)` → `z.enum(["Q1",..."Q4"])` + added `estimation_method`; added `tax_year` to MCP `record_payment` | `implementation-plan.md` |
| R2 | Stale risk register row | Medium | Replaced "Start with TaxProfile JSON field; upgrade to dedicated model if needed" → "Use QuarterlyEstimate entity + QuarterlyEstimateRepository (domain layer exists; infra model/repo/UoW wiring planned in task 13b)" | `implementation-plan.md` |
| R3 | Bare validation commands | Medium | Converted 14 task rows to receipt-file pattern: 4 FIC rows (1,3,5,7), row 10 (rg prose→command), row 14 (integration pytest), row 17 (vitest), rows 18–21 (verification suite), rows 22–23 (re-anchor gates), row 24 (buildplan audit). Total receipt-pattern rows now: 25. | `task.md` |

### Verification Evidence

| Check | Result | Command |
|-------|--------|--------|
| `/record-payment` endpoint eliminated | 0 matches | `rg "record-payment" implementation-plan.md` |
| `payment_amount` present | 2 refs (REST + MCP) | `rg -cn "payment_amount" implementation-plan.md` |
| Numeric quarter eliminated | 0 matches | `rg "z.number().int().min(1).max(4)" implementation-plan.md` |
| `confirm` field present | 4 refs | `rg -n "confirm" implementation-plan.md` |
| "TaxProfile JSON" eliminated | 0 matches | `rg "TaxProfile JSON" plan-dir/` |
| Receipt-file pattern coverage | 25 rows | `rg -c "Temp.zorivest" task.md` |

Cross-doc sweep: not required — corrections changed only boundary table values and risk register text (no workflow slugs, no canonical term renames).

### Status

`corrections_applied` — all 3 recheck findings resolved. Ready for `/plan-critical-review` re-review.

---

## Recheck (2026-05-14, Pass 2)

**Workflow**: `/plan-critical-review` recheck  
**Agent**: Codex GPT-5  
**Verdict**: `changes_required`

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|--------------|----------------|
| R1: Boundary contract spec drift | corrected | fixed |
| R2: Stale risk register row | corrected | fixed |
| R3: Bare validation commands | corrected | partially fixed, still open |

### Confirmed Fixes

- **R1 fixed**: the boundary table now uses REST `POST /quarterly/payment`, `payment_amount`, `confirm`, and MCP `payment_amount`; quarterly MCP input is now `Q1`-`Q4` with `estimation_method` (`implementation-plan.md:72`, `implementation-plan.md:86`, `implementation-plan.md:88`). These match the API/MCP specs (`04f-api-tax.md:49-57`, `04f-api-tax.md:130-136`, `05h-mcp-tax.md:226-236`, `05h-mcp-tax.md:274-311`).
- **R2 fixed**: the risk register now references `QuarterlyEstimate` + `QuarterlyEstimateRepository` and explicitly calls out table creation verification in `database_init.py` (`implementation-plan.md:293`).
- **R3 mostly fixed**: implementation and core verification rows now use receipt-file commands for pytest, pyright, ruff, vitest, `rg`, and re-anchor checks (`task.md:20-54`).

### Remaining Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| RR1 | Medium | R3 remains partially open. Most task rows were corrected, but several closeout/verification rows still do not provide exact runnable validation commands. Task 25 says only "Full verification commands from implementation-plan.md"; task 27 describes `view_file` actions but not concrete artifact paths/exemplar discovery commands; tasks 28-31 use summary phrases such as "Structural markers present", "All 11 sections + metrics + YAML", "Last 3 lines show new row", and "Run completion-preflight §Structural Marker Checklist". The plan/task contract requires every task validation cell to include exact command(s), so these rows can still be marked complete without reproducible evidence. | `task.md:55`, `task.md:58-63` | Replace rows 25 and 27-31 with exact validation commands or explicit tool-call recipes. For closeout structural checks, list the required `rg` marker commands from `completion-preflight` and receipt-file outputs for metrics/template/exemplar reads. | open |

### Commands Executed

All terminal commands wrote receipts under `C:\Temp\zorivest\`.

| Receipt | Purpose | Result |
|---------|---------|--------|
| `tax-wiring-recheck2-boundary.txt` | Recheck API/MCP boundary table against canonical specs | R1 fixed. |
| `tax-wiring-recheck2-persistence.txt` | Recheck persistence section and risk register | R2 fixed. |
| `tax-wiring-recheck2-task.txt` | Recheck task validation rows | R3 mostly fixed; closeout rows still not exact. |
| `tax-wiring-recheck2-regression.txt` | Sweep for stale prior-finding terms | Empty output; stale prior terms removed. |
| `tax-wiring-recheck2-state.txt` | Confirm plan remains unstarted | Execution handoff and planned new test files returned `False`. |

### Verdict

`changes_required` - The substantive boundary and persistence contract issues are resolved. The remaining blocker is narrower: the task table still needs exact validation commands for the full-verification and closeout rows before the plan is evidence-ready.

---

## Corrections Applied — Pass 3 (2026-05-14)

> **Agent:** Antigravity (Gemini)
> **Verdict:** `corrections_applied`

### Changes Made

| # | Finding | Severity | Resolution | Files Changed |
|---|---------|----------|------------|---------------|
| RR1 | Closeout/verification rows use prose validations | Medium | Replaced 6 task rows (25, 27–31) with exact receipt-file commands: row 25 → explicit pytest+pyright+ruff receipt chain; row 27 → `Test-Path`+`Get-ChildItem` exemplar discovery; rows 28–29 → `rg` structural marker commands from completion-preflight skill (AC-, CACHE BOUNDARY, Evidence, Friction Log, sections:, etc.); row 30 → `Get-Content -Tail 3`; row 31 → `rg` closeout gate with ≥3 marker assertion. Total receipt-pattern rows now: 31. | `task.md` |

### Verification Evidence

| Check | Result | Command |
|-------|--------|--------|
| Prose validations eliminated | 0 matches | `rg "Full verification commands\|Structural markers present\|All 11 sections\|Last 3 lines\|Run .completion-preflight\|view_file:" task.md` |
| Receipt-file pattern coverage | 31 rows | `rg -c "Temp.zorivest" task.md` |

Cross-doc sweep: not required — corrections changed only task validation cells (no workflow slugs, no canonical term renames).

### Status

`corrections_applied` — RR1 resolved. All task validation cells now use exact receipt-file commands. Ready for `/plan-critical-review` re-review.

---

## Recheck (2026-05-14, Pass 3)

**Workflow**: `/plan-critical-review` recheck  
**Agent**: Codex GPT-5  
**Verdict**: `approved`

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|--------------|----------------|
| RR1: Closeout/verification rows use prose validations | corrected | fixed |

### Confirmed Fixes

- **RR1 fixed**: task rows 25 and 27-31 now include receipt-file validation commands for full verification, template/exemplar checks, handoff markers, reflection markers, metrics tail, and closeout-gate marker checks (`task.md:55`, `task.md:58-63`).
- **Prior contract fixes remain stable**: the stale-term sweep returned empty output for prior blockers (`tax-wiring-recheck3-stale.txt`), the boundary/persistence sweep still shows canonical `/quarterly/payment`, `payment_amount`, `confirm`, `QuarterlyEstimate`, and `database_init.py` references (`tax-wiring-recheck3-contracts.txt`).
- **Plan remains unstarted**: execution handoff and planned new test files still returned `False` (`tax-wiring-recheck3-state.txt`).

### Remaining Findings

None.

### Commands Executed

All terminal commands wrote receipts under `C:\Temp\zorivest\`.

| Receipt | Purpose | Result |
|---------|---------|--------|
| `tax-wiring-recheck3-stale.txt` | Sweep for stale prior-finding terms | Empty output; prior stale terms removed. |
| `tax-wiring-recheck3-task.txt` | Recheck rows 25 and 27-31 | Exact receipt-file commands now present. |
| `tax-wiring-recheck3-contracts.txt` | Recheck boundary and persistence contracts | Boundary/persistence corrections remain in place. |
| `tax-wiring-recheck3-state.txt` | Confirm plan remains unstarted | Execution handoff and planned new test files returned `False`. |
| `tax-wiring-recheck3-reviewstate.txt` | Inspect rolling review metadata before update | Found correction-pass metadata; superseded by this approved recheck. |

### Verdict

`approved` - The plan is now ready for the next human-authorized workflow. This approval is for the plan contract only; it does not authorize implementation or merge.

---

## Focused Recheck (2026-05-14, TAX-DBMIGRATION)

**Workflow**: `/plan-critical-review` focused recheck  
**Agent**: Codex GPT-5  
**Scope**: Newly added `Ad-Hoc: TAX-DBMIGRATION` sections in `implementation-plan.md` and `task.md`  
**Verdict**: `changes_required`

### Confirmed Context

- The new ad-hoc direction is locally plausible: `packages/api/src/zorivest_api/main.py:239-260` uses `Base.metadata.create_all()` plus `_inline_migrations`, and the repository has no Alembic runtime scaffold at `packages/api/alembic.ini`, `packages/api/alembic`, root `alembic.ini`, or `packages/api/migrations` (`tax-dbmigration-paths.txt`).
- The model/source diagnosis is real: `TaxLotModel` defines `cost_basis_method`, `realized_gain_loss`, and `acquisition_source` at `packages/infrastructure/src/zorivest_infra/database/models.py:879-887`, while the live `packages/api/zorivest.db` `tax_lots` table currently has only the original 11 columns (`tax-dbmigration-schema.txt`).
- The MCP audit source exists and ties the four runtime failures to the same schema gap (`.agent/context/MCP/mcp-tool-audit-report.md:233-236`).

### Remaining Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| MIG-R1 | High | The ad-hoc bug fix does not plan a Red phase or dedicated regression test before editing production code. AGENTS requires failing tests before bug fixes and FAIL_TO_PASS evidence (`AGENTS.md:227-228`, `AGENTS.md:237-246`), but the task jumps directly from adding `ALTER TABLE` statements to manual MCP checks and a full pytest run. This leaves AC-MIG.6 and AC-MIG.7 unproven because the existing full suite mostly uses fresh `Base.metadata.create_all()` databases, not a pre-Phase-3B `tax_lots` schema missing the three columns. | `implementation-plan.md:351-352`, `implementation-plan.md:356-371`; `task.md:67-72` | Add a first task to write a failing migration regression test. The test should create an old-shape `tax_lots` table in a temporary SQLite DB, trigger the startup/inline migration path or extracted migration helper, assert all three columns exist, and prove repeat startup is idempotent. Capture the failing receipt before changing `main.py`. | open |
| MIG-R2 | Medium | The ad-hoc validation rows are not exact, runnable evidence. Rows 33-36 use pseudo MCP calls with `<test-account-id>` placeholders and no receipt/artifact path; row 37 is assigned to AC-MIG.6 and AC-MIG.7 but only runs full pytest, which does not directly verify a fresh DB delete/restart path or an already-migrated DB startup. The task template and workflow require exact validation commands (`TASK-TEMPLATE.md:19-20`, `.agent/workflows/plan-critical-review.md:107`, `.agent/workflows/plan-critical-review.md:155`). | `task.md:68-72`; `implementation-plan.md:365-371` | Replace rows 33-36 with exact executable validation recipes, including the concrete account ID already shown in the plan or a deterministic setup step, plus receipt paths for the MCP/API responses. Split AC-MIG.6 and AC-MIG.7 into explicit tests or commands instead of bundling them into the generic full-regression row. | open |

### Commands Executed

All terminal commands wrote receipts under `C:\Temp\zorivest\` using the redirect-to-file pattern.

| Receipt | Purpose | Result |
|---------|---------|--------|
| `tax-dbmigration-plan.txt` | Locate TAX-DBMIGRATION plan/task/known-issue references | Found the new ad-hoc plan and task rows plus stale Alembic wording in known issues/audit. |
| `tax-dbmigration-paths.txt` | Check migration scaffold/runtime DB paths | Confirmed no Alembic files at checked paths; `main.py` and runtime `zorivest.db` exist. |
| `tax-dbmigration-code2.txt` | Sweep code/tests for TaxLot fields, create_all, inline migrations | Confirmed model/repository fields and current startup migration pattern. |
| `tax-dbmigration-startup.txt` | Inspect current `main.py` startup migration anchors | Confirmed `_inline_migrations` at `main.py:243-253`. |
| `tax-dbmigration-schema.txt` | Inspect live runtime `tax_lots` schema | Confirmed the three planned columns are missing from `packages/api/zorivest.db`. |
| `tax-dbmigration-mcp-audit.txt` | Verify MCP audit source for runtime failures | Confirmed I-1 through I-4 map to the tax_lots schema drift. |
| `tax-dbmigration-testsweep.txt` | Search existing tests for startup/create_all/migration coverage | Existing tests show fresh create_all/lifespan coverage, not old-schema migration coverage. |
| `tax-dbmigration-task-coverage.txt` | Map AC-MIG rows to task validations | Used for MIG-R1 and MIG-R2 line evidence. |
| `tax-dbmigration-tdd-contract.txt` | Verify local TDD/FAIL_TO_PASS requirements | Used for MIG-R1. |
| `tax-dbmigration-validation-contract.txt` | Verify exact-command task validation requirements | Used for MIG-R2. |

### Verdict

`changes_required` - The inline migration approach is the right local direction, but the ad-hoc plan is not evidence-ready. It needs a failing migration regression test and exact validation rows before execution should proceed.

---

## Corrections Applied — Pass 4 (2026-05-14, TAX-DBMIGRATION)

> **Agent:** Antigravity (Gemini)
> **Verdict:** `corrections_applied`

### Changes Made

| # | Finding | Severity | Resolution | Files Changed |
|---|---------|----------|------------|---------------|
| MIG-R1 | No Red-phase migration regression test planned | High | Added `### Migration Regression Test (Red Phase — FAIL_TO_PASS)` subsection with 5-step test design: old-shape table creation, inline migration execution, 3-column assertion, idempotency assertion, fresh-DB `create_all` assertion. Added task row 32 (write failing test BEFORE code change) and row 34 (Green phase re-run). Test file: `tests/integration/test_inline_migrations.py`. | `implementation-plan.md`, `task.md` |
| MIG-R2 | Placeholder validation commands with `<test-account-id>` | Medium | Replaced 6 pseudo-MCP rows (33–37) with 7 exact rows (35–41): 4 `Invoke-RestMethod` commands with concrete account ID `99bb9b00-fc7a-44cf-b816-a6bb4dabfaca` and receipt paths (`mig-lots.txt`, `mig-estimate.txt`, `mig-simulate.txt`, `mig-ytd.txt`). Split AC-MIG.6 and AC-MIG.7 into dedicated rows 39 (`-k "fresh"`) and 40 (`-k "idempotent"`) with separate pytest receipt files. Total ad-hoc rows: 10 (was 6). | `task.md` |

### Verification Evidence

| Check | Result | Command |
|-------|--------|---------|
| `<test-account-id>` placeholder eliminated | 0 matches | `rg "test-account-id" task.md` |
| Receipt-file pattern coverage | 41 rows (was 31) | `rg -c "Temp.zorivest" task.md` |
| Red phase / FAIL_TO_PASS present | 6 refs | `rg "Red phase\|FAIL_TO_PASS\|test_inline_migrations" implementation-plan.md` |
| AC-MIG.6 / AC-MIG.7 in separate rows | 3 refs (row 32, 39, 40) | `rg "AC-MIG.6\|AC-MIG.7" task.md` |

Cross-doc sweep: not required — corrections changed only ad-hoc plan/task sections (no workflow slugs, no canonical term renames).

### Status

`corrections_applied` — both TAX-DBMIGRATION recheck findings resolved. Ready for `/plan-critical-review` re-review.

---

## Recheck (2026-05-14, TAX-DBMIGRATION Pass 4)

**Workflow**: `/plan-critical-review` focused recheck  
**Agent**: Codex GPT-5  
**Verdict**: `approved`

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|--------------|----------------|
| MIG-R1: No Red-phase migration regression test planned | corrected | fixed |
| MIG-R2: Placeholder validation commands / generic AC-MIG.6-7 evidence | corrected | fixed |

### Confirmed Fixes

- **MIG-R1 fixed**: the plan now adds a dedicated `Migration Regression Test (Red Phase — FAIL_TO_PASS)` section requiring `tests/integration/test_inline_migrations.py` to create an old-shape `tax_lots` table, run inline migration logic, assert the three missing columns, prove idempotency, and verify the fresh `create_all` path (`implementation-plan.md:354-366`). The task table now starts the ad-hoc work with a failing Red-phase test receipt before `main.py` changes (`task.md:67`), followed by a Green-phase rerun (`task.md:69`).
- **MIG-R2 fixed**: placeholder MCP rows were replaced with exact executable validation rows. The runtime endpoint checks now use concrete REST requests with the account ID from the plan and receipt files (`task.md:70-73`). AC-MIG.6 and AC-MIG.7 are split into separate targeted pytest rows for fresh-DB and idempotency assertions (`task.md:74-75`), and the full regression remains a separate final row (`task.md:76`).
- **Local direction still holds**: the current codebase still uses inline startup migrations in `main.py`, and no Alembic scaffold was found in the checked runtime paths from the prior focused pass. The ad-hoc plan now tests that inline mechanism directly before applying the three `tax_lots` ALTER statements.

### Remaining Findings

None.

### Commands Executed

All terminal commands wrote receipts under `C:\Temp\zorivest\` using the redirect-to-file pattern.

| Receipt | Purpose | Result |
|---------|---------|--------|
| `tax-dbmigration-recheck4-plan.txt` | Recheck corrected TAX-DBMIGRATION plan/task references | Confirmed Red/Green migration-test plan and exact ad-hoc task rows. |
| `tax-dbmigration-recheck4-code.txt` | Recheck current inline migration anchors in code/tests | Confirmed `main.py` still has `_inline_migrations`; no migration test exists yet, as expected pre-execution. |
| `tax-dbmigration-recheck4-validation.txt` | Recheck placeholder elimination and validation specificity | Confirmed concrete REST receipt rows and targeted pytest receipts for Red, Green, fresh, and idempotent checks. |
| `tax-dbmigration-recheck4-status.txt` | Recheck ad-hoc unchecked rows/status context | Confirmed only the new TAX-DBMIGRATION rows remain unchecked. |

### Verdict

`approved` - The TAX-DBMIGRATION ad-hoc plan is now evidence-ready for the next human-authorized execution workflow. This approval is for the plan contract only; it does not authorize implementation, merge, release, or deploy.
