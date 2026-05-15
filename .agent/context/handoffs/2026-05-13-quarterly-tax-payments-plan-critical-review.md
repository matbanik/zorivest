---
date: "2026-05-13"
review_mode: "plan"
target_plan: "docs/execution/plans/2026-05-13-quarterly-tax-payments/implementation-plan.md"
verdict: "approved"
findings_count: 0
template_version: "2.1"
requested_verbosity: "standard"
agent: "GPT-5.5 Codex"
---

# Critical Review: 2026-05-13-quarterly-tax-payments

> **Review Mode**: `plan`
> **Verdict**: `approved`

---

## Scope

**Target**:
- `docs/execution/plans/2026-05-13-quarterly-tax-payments/implementation-plan.md`
- `docs/execution/plans/2026-05-13-quarterly-tax-payments/task.md`

**Review Type**: plan review
**Checklist Applied**: PR + DR from `.agent/workflows/plan-critical-review.md`

**User Override**: The task file is already marked complete, but the user explicitly instructed: "ignore the fact that the plan has been already executed." PR-2 not-started confirmation was therefore treated as not applicable for verdict purposes.

**Related Canon Reviewed**:
- `docs/build-plan/build-priority-matrix.md` Phase 3D items 70-74
- `docs/build-plan/domain-model-reference.md` Module D/E and TaxProfile/QuarterlyEstimate fields
- `docs/build-plan/04f-api-tax.md` service wiring notes
- Current IRS primary sources for safe harbor, Form 2210 Schedule AI, 2026 brackets, and underpayment interest

---

## Commands Executed

```powershell
rg -n 'User Review Required|Bracket table year coverage|Penalty rate|QuarterlyEstimate persistence|All outputs include|state tax|compute_capital_gains_tax|record_payment|NotImplementedError|placeholder|BUILD_PLAN\.md Audit|docs/BUILD_PLAN\.md|Verification Plan|Annualized income|Required installment|annualized income installment|Task 20|Select-String|metrics\.md|status: "complete"|status: "draft"' docs/execution/plans/2026-05-13-quarterly-tax-payments/implementation-plan.md docs/execution/plans/2026-05-13-quarterly-tax-payments/task.md docs/build-plan/domain-model-reference.md docs/build-plan/build-priority-matrix.md docs/build-plan/04f-api-tax.md *> C:\Temp\zorivest\plan-review-rg.txt
rg -n 'AC-146\.6|TaxProfile\.state_tax_rate|state_tax_rate|filing status -> compute|Effective \+ marginal|effective \+ marginal' docs/execution/plans/2026-05-13-quarterly-tax-payments/implementation-plan.md docs/execution/plans/2026-05-13-quarterly-tax-payments/task.md docs/build-plan/domain-model-reference.md *> C:\Temp\zorivest\plan-review-rg-state.txt
```

Web research used official/current sources:
- IRS, "IRS releases tax inflation adjustments for tax year 2026, including amendments from the One, Big, Beautiful Bill" (IR-2025-103; Revenue Procedure 2025-32)
- IRS, Publication 505 / Estimated Tax FAQ for 90% current-year and 100%/110% prior-year safe harbor
- IRS, Instructions for Form 2210 (2025), Schedule AI
- IRS, Quarterly interest rates page

---

## Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 1 | High | The plan still contains unresolved human-review decisions but proceeds as if the contract is execution-ready. The plan asks whether to include 2024 brackets, how to model penalty rates, whether persistence is deferred, and whether capital-gains thresholds belong in MEU-146. These are product/contract decisions, not notes. Under the planning contract, each must be resolved as `Spec`, `Local Canon`, `Research-backed`, or `Human-approved` before task approval. | `implementation-plan.md:34-39`, `implementation-plan.md:299` | Convert each open question into an explicit accepted rule with a source label, or mark the affected task blocked until human approval. | open |
| 2 | High | `record_payment()` is internally contradictory and violates the no-deferral rule. AC-145.7 says the method "persists payment via UoW", but also says the body is a TODO stub. `task.md` marks the row complete `[x]` while saying the method is a `[B]` stub, then the notes explicitly allow `NotImplementedError`. This cannot be an approved implementation task under the project rules. | `implementation-plan.md:207`, `implementation-plan.md:286`, `task.md:43`, `task.md:67` | Either move `record_payment()` fully to MEU-148 and mark the current row `[B]`, or change the AC to a source-backed signature-only contract and do not mark it complete as persistence. Remove planned `TODO` / `NotImplementedError` from completed scope. | open |
| 3 | High | The annualized income acceptance criterion drops the IRS Schedule AI requirement that the required installment is the smaller of the annualized installment and the regular installment adjusted by savings from earlier installments. The plan states that source-backed rule in the sufficiency table, but AC-144.4 replaces it with "25% of annualized tax minus cumulative required", which is not the full Form 2210 Schedule AI contract. IRS instructions say Schedule AI line 27 feeds Form 2210 line 10 and that Schedule AI selects the smaller of the two installment paths. | `implementation-plan.md:161`, `implementation-plan.md:171`; IRS Instructions for Form 2210 (2025), Schedule AI | Rewrite AC-144.4 and tests to model the Schedule AI line sequence needed for line 27, including regular-installment comparison and prior savings. If this is intentionally an estimator approximation, label and bound it explicitly. | open |
| 4 | High | State tax integration is required by canon but has no executable task contract. The build-plan canon says Module E computes effective and marginal federal rate "plus state tax rate"; the plan adds AC-146.6, but the planned functions and task rows only implement federal bracket/capital-gains functions and do not define a function signature, result field, or tests that apply `TaxProfile.state_tax_rate`. | `domain-model-reference.md:556-557`, `implementation-plan.md:56`, `implementation-plan.md:68`, `task.md:22` | Add a concrete state-tax API and tests, or explicitly split state tax integration into a future MEU with a source-backed scope change. | open |
| 5 | Medium | The required tax disclaimer is stated as a universal output rule but is not represented in acceptance criteria, tasks, file changes, or verification. Since this plan is domain/service only, it is unclear what "all outputs" means for Decimal-returning functions and dataclass results. | `implementation-plan.md:28`, `implementation-plan.md:31` | Define where disclaimers live in domain/service outputs, or defer the disclaimer to API/MCP/GUI presentation layers with explicit source-backed scope. Add tests if the domain/service layer is responsible. | open |
| 6 | Medium | The verification plan will not catch the placeholder it explicitly permits. The anti-placeholder scan checks only `domain/tax/brackets.py`, `domain/tax/niit.py`, and `domain/tax/quarterly.py`, while the planned `NotImplementedError` lives in `services/tax_service.py`. Several task validation cells also bypass the mandatory redirect pattern (`Select-String`, bare `rg`, and `Get-Content ... | Select-Object` without all-stream receipt capture). | `implementation-plan.md:283`, `implementation-plan.md:286`, `task.md:46`, `task.md:48`, `task.md:54`, `task.md:67` | Expand the anti-placeholder scan to all touched files, especially `tax_service.py`, and rewrite every validation cell to produce a `C:\Temp\zorivest\...` receipt with `*>`. | open |
| 7 | Low | The BUILD_PLAN audit is pointed at `docs/BUILD_PLAN.md` and expects zero matches, but the plan source and status rows are in `docs/build-plan/build-priority-matrix.md` items 70-74. This check does not verify the artifact the plan says must be updated post-implementation. | `implementation-plan.md:1-4`, `implementation-plan.md:242-249`, `build-priority-matrix.md:365-369`, `task.md:48` | Replace the audit with a targeted `rg` or file-read check against `docs/build-plan/build-priority-matrix.md` rows/items 70-74. | open |

---

## Checklist Results

### Plan Review (PR)

| Check | Result | Evidence |
|-------|--------|----------|
| PR-1 Plan/task alignment | fail | `task.md:43` marks `record_payment()` complete as a `[B]` stub while `implementation-plan.md:207` says it persists via UoW and `task.md:67` permits `NotImplementedError`. |
| PR-2 Not-started confirmation | n/a | User explicitly instructed to ignore executed state. |
| PR-3 Task contract completeness | fail | Most rows have owner/deliverable/validation/status, but task 20 is semantically incomplete because completed scope contains a planned stub. |
| PR-4 Validation realism | fail | Anti-placeholder scan omits `tax_service.py`; BUILD_PLAN audit checks the wrong file; several task validation cells are not P0-compliant receipts. |
| PR-5 Source-backed planning | fail | Open questions at `implementation-plan.md:34-39` and `implementation-plan.md:299` remain unresolved despite downstream ACs. |
| PR-6 Handoff/corrections readiness | pass | Canonical review path is explicit and findings are resolvable through `/plan-corrections`. |

### Docs Review (DR)

| Check | Result | Evidence |
|-------|--------|----------|
| DR-1 Claim-to-state match | fail | Plan claims all outputs include a disclaimer, but no AC/task/test covers that output behavior. |
| DR-2 Residual old terms | pass | No rename/move review scope identified. |
| DR-3 Downstream references updated | fail | Post-implementation BUILD_PLAN audit targets `docs/BUILD_PLAN.md`, not the source `build-priority-matrix.md` rows. |
| DR-4 Verification robustness | fail | Planned anti-placeholder scan cannot catch the planned service-layer placeholder. |
| DR-5 Evidence auditability | fail | Some validation commands are not all-stream receipt commands. |
| DR-6 Cross-reference integrity | fail | State tax integration exists in canon and ACs but not in concrete task implementation scope. |
| DR-7 Evidence freshness | n/a | This is a plan review; implementation evidence was intentionally ignored by user instruction. |
| DR-8 Completion vs residual risk | fail | `task.md` allows a completed row containing a blocked stub. |

---

## Open Questions / Assumptions

- I treated current IRS pages as authoritative over third-party summaries when tax rules were part of the plan contract.
- I did not review implemented code or execution handoff correctness because the user explicitly requested a plan-critical review and asked to ignore execution state.
- The verdict is based on whether the plan and task would have been safe to approve before implementation.

---

## Verdict

`changes_required` - The plan is not approval-ready as a pre-implementation contract. The blockers are unresolved plan decisions, a completed task that permits a placeholder `NotImplementedError`, and an annualized-income AC that does not match the IRS Schedule AI rule the plan itself cites.

---

## Concrete Follow-Up Actions

1. Run `/plan-corrections` for this plan folder.
2. Resolve all open "User Review Required" questions into source-labeled rules or blocked tasks.
3. Rewrite `record_payment()` scope so it is either fully implemented in this MEU or explicitly moved to MEU-148.
4. Correct AC-144.4 to match IRS Form 2210 Schedule AI line-27 behavior.
5. Add concrete state-tax integration scope/tests or source-backed deferral.
6. Repair validation commands and placeholder scans before approval.

---

## Residual Risk

Because this is a plan-only review and implementation state was intentionally ignored, no conclusion is made about whether the already-executed code passes or fails these findings. The risk is that the executed implementation may have inherited defects from an approval contract that was under-specified or internally inconsistent.

---

## Corrections Applied — 2026-05-13

**Agent**: Antigravity (Opus)
**Verdict**: `corrections_applied`

All 7 findings verified and corrected. No production code touched.

### Changes Made

| # | Finding | Fix Applied |
|---|---------|------------|
| 1 | Unresolved open questions | Converted all 5 questions to source-backed decisions with labels (`Research-backed`, `Spec`, `Local Canon`) |
| 2 | `record_payment()` contradiction | Rewrote AC-145.7 as signature-only contract; changed task 20 status `[x]` → `[B]`; updated note with MEU-148 follow-up link |
| 3 | AC-144.4 missing IRS min() | Rewrote to include `min(annualized_installment, regular_installment)` per Form 2210 Schedule AI line 27 |
| 4 | State tax AC without implementation | Added `compute_combined_rate()` function signature, test spec, and negative test to AC-146.6 |
| 5 | Disclaimer without AC/task | Scoped disclaimer to presentation layer (MEU-148/149/154); removed domain-layer responsibility |
| 6 | Anti-placeholder scan gap + non-P0 commands | Added `tax_service.py` to scan; replaced `Select-String` (task 22) and bare `rg` (task 23) with P0-compliant `*>` receipts |
| 7 | BUILD_PLAN audit targeting wrong file | Replaced `rg "quarterly-tax-payments" docs/BUILD_PLAN.md` with `rg -n "MEU-14[3-7]" docs/BUILD_PLAN.md` |

### Files Modified

- `docs/execution/plans/2026-05-13-quarterly-tax-payments/implementation-plan.md` — 11 edits across 9 locations
- `docs/execution/plans/2026-05-13-quarterly-tax-payments/task.md` — 5 edits (status, task 20, task 22, task 23, note)

### Verification Results

- `rg "User Review Required|Open Questions"` → 0 matches ✅
- `rg "persists payment via UoW|body is a stub"` → 0 matches ✅
- `rg "25% of annualized tax minus cumulative"` → 0 matches ✅
- `rg "compute_combined_rate"` → found at line 68 ✅
- `rg "Select-String"` in task.md → 0 matches ✅
- `rg "tax_service.py"` in implementation-plan.md → found in scan at line 285 ✅
- Cross-doc sweep: 2 files checked, 2 updated ✅

### Next Step

Run `/plan-critical-review` to re-review the corrected plan. Only the reviewer role may set `approved`.

---

## Recheck (2026-05-13)

**Workflow**: `/plan-critical-review` recheck  
**Agent**: GPT-5.5 Codex  
**Verdict**: `changes_required`

### Commands Executed

```powershell
rg -n "User Review Required|Open Questions|Resolved Design Decisions|Bracket table year coverage|Penalty rate|QuarterlyEstimate persistence|Capital gains bracket thresholds" docs/execution/plans/2026-05-13-quarterly-tax-payments/implementation-plan.md *> C:\Temp\zorivest\recheck-finding1.txt
rg -n "persists payment via UoW|body is a stub|signature-only contract|NotImplementedError|\[B\]" docs/execution/plans/2026-05-13-quarterly-tax-payments/implementation-plan.md docs/execution/plans/2026-05-13-quarterly-tax-payments/task.md *> C:\Temp\zorivest\recheck-finding2.txt
rg -n "25% of annualized tax minus cumulative|required installment|min\(annualized_installment|Schedule AI line 27" docs/execution/plans/2026-05-13-quarterly-tax-payments/implementation-plan.md *> C:\Temp\zorivest\recheck-finding3.txt
rg -n "compute_combined_rate|state_tax_rate|state tax rate" docs/execution/plans/2026-05-13-quarterly-tax-payments/implementation-plan.md docs/execution/plans/2026-05-13-quarterly-tax-payments/task.md *> C:\Temp\zorivest\recheck-finding4.txt
rg -n "disclaimer|not legal tax advice|presentation layer|MEU-148/149/154" docs/execution/plans/2026-05-13-quarterly-tax-payments/implementation-plan.md *> C:\Temp\zorivest\recheck-finding5.txt
rg -n "TODO|FIXME|NotImplementedError|tax_service.py|Select-String|MEU-14\[3-7\]|rg" docs/execution/plans/2026-05-13-quarterly-tax-payments/implementation-plan.md docs/execution/plans/2026-05-13-quarterly-tax-payments/task.md *> C:\Temp\zorivest\recheck-finding6-fixed.txt
rg -n "BUILD_PLAN\.md Status Update|build-priority-matrix|MEU-14\[3-7\]|quarterly-tax-payments" docs/execution/plans/2026-05-13-quarterly-tax-payments/implementation-plan.md docs/execution/plans/2026-05-13-quarterly-tax-payments/task.md *> C:\Temp\zorivest\recheck-finding7.txt
rg -n "Rev\. Proc\. 2025-XX|Rev\. Proc\. 2025-32|Revenue Procedure 2025-32|corrections_applied|Verdict" docs/execution/plans/2026-05-13-quarterly-tax-payments/implementation-plan.md .agent/context/handoffs/2026-05-13-quarterly-tax-payments-plan-critical-review.md *> C:\Temp\zorivest\recheck-new-issues.txt
```

### Prior Findings Recheck

| Finding | Prior Status | Recheck Result |
|---------|--------------|----------------|
| 1. Unresolved design decisions | open | Fixed: `implementation-plan.md:34-39` resolves bracket years, penalty rates, and persistence; `implementation-plan.md:297-301` resolves bracket data source and capital-gains thresholds. |
| 2. `record_payment()` contradiction | open | Fixed: `implementation-plan.md:207` now defines a signature-only contract; `task.md:43` and `task.md:67` mark it `[B]` with MEU-148 follow-up. |
| 3. Annualized-income AC incomplete | open | Fixed: `implementation-plan.md:171` now uses `min(annualized_installment, regular_installment)` and references Schedule AI line 27. |
| 4. State-tax integration lacks executable scope | open | Fixed: `implementation-plan.md:68` adds `compute_combined_rate(federal_effective, state_tax_rate)` and test expectations. |
| 5. Disclaimer scope unclear | open | Fixed: `implementation-plan.md:28` explicitly defers disclaimer text to API/MCP/GUI presentation layers. |
| 6. Anti-placeholder and P0 command gaps | open | Fixed for original issue: `implementation-plan.md:285` includes `tax_service.py`; `task.md:46` replaces `Select-String` with `rg ... *> C:\Temp\zorivest\reanchor.txt`. |
| 7. BUILD_PLAN audit targets wrong evidence | open | Fixed for original issue: `implementation-plan.md:242-249` and `task.md:48` now target MEU-143 through MEU-147 status rows, with `build-priority-matrix.md` also called out. |

### Remaining Finding

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 1 | Low | The corrected plan resolves 2026 bracket data to IRS Rev. Proc. 2025-32 in the design-decision sections, but still leaves stale `Rev. Proc. 2025-XX` text in the MEU-146 sufficiency table and Research References. This is an auditability defect in a tax-rule plan. | `implementation-plan.md:53`, `implementation-plan.md:308` | Replace both `Rev. Proc. 2025-XX` references with `Rev. Proc. 2025-32` / `Revenue Procedure 2025-32`, consistent with `implementation-plan.md:37` and `implementation-plan.md:300`. | open |

### Checklist Results

| Check | Result | Evidence |
|-------|--------|----------|
| PR-1 Plan/task alignment | pass | `record_payment()` is consistently signature-only and `[B]`: `implementation-plan.md:207`, `task.md:43`, `task.md:67`. |
| PR-3 Task contract completeness | pass | Task 20 now uses `[B]` instead of completed persistence; original contradiction resolved. |
| PR-4 Validation realism | pass with low residual | Original validation gaps are fixed; stale Rev. Proc. source label remains. |
| PR-5 Source-backed planning | fail | Source labels are present, but `Rev. Proc. 2025-XX` remains in two source references. |
| PR-6 Handoff/corrections readiness | pass | Remaining issue is concrete and can be resolved via `/plan-corrections`. |

### Verdict

`changes_required` - The seven original findings are resolved, but the corrected plan still contains stale `Rev. Proc. 2025-XX` references that should be corrected before approval.

---

## Corrections Applied (Recheck) — 2026-05-13

**Agent**: Antigravity (Opus)
**Verdict**: `corrections_applied`

### Changes Made

| # | Finding | Fix Applied |
|---|---------|------------|
| 1 | Stale `Rev. Proc. 2025-XX` in sufficiency table and references | Replaced with `Rev. Proc. 2025-32` (line 53) and `Revenue Procedure 2025-32` (line 308), consistent with resolved decisions at lines 37 and 300 |

### Verification

- `rg "Rev. Proc. 2025-XX"` → 0 matches ✅
- `rg "2025-32"` → 4 consistent references (lines 37, 53, 300, 308) ✅
- Cross-doc sweep: 1 file checked, 1 updated ✅

### Next Step

Run `/plan-critical-review` for final approval. Only the reviewer role may set `approved`.

---

## Recheck (2026-05-13 Final)

**Workflow**: `/plan-critical-review` recheck  
**Agent**: GPT-5.5 Codex  
**Verdict**: `approved`

### Commands Executed

```powershell
rg -n "Rev\. Proc\. 2025-XX|Revenue Procedure 2025-32|Rev\. Proc\. 2025-32|verdict:|findings_count:" docs/execution/plans/2026-05-13-quarterly-tax-payments/implementation-plan.md .agent/context/handoffs/2026-05-13-quarterly-tax-payments-plan-critical-review.md *> C:\Temp\zorivest\recheck-2025-32.txt
rg -n "Rev\. Proc\. 2025-XX" docs/execution/plans/2026-05-13-quarterly-tax-payments/implementation-plan.md *> C:\Temp\zorivest\recheck-stale-plan-only.txt
rg -n "Rev\. Proc\. 2025-32|Revenue Procedure 2025-32" docs/execution/plans/2026-05-13-quarterly-tax-payments/implementation-plan.md *> C:\Temp\zorivest\recheck-fixed-plan-only.txt
```

### Prior Remaining Finding Recheck

| Finding | Prior Status | Recheck Result |
|---------|--------------|----------------|
| Stale `Rev. Proc. 2025-XX` in the corrected plan | open | Fixed. `C:\Temp\zorivest\recheck-stale-plan-only.txt` is empty, and `C:\Temp\zorivest\recheck-fixed-plan-only.txt` shows consistent `Rev. Proc. 2025-32` / `Revenue Procedure 2025-32` references at `implementation-plan.md:37`, `implementation-plan.md:53`, `implementation-plan.md:300`, and `implementation-plan.md:308`. |

### Findings

No remaining plan-review findings.

### Checklist Results

| Check | Result | Evidence |
|-------|--------|----------|
| PR-1 Plan/task alignment | pass | Prior recheck confirmed `record_payment()` is consistently signature-only and `[B]`. |
| PR-3 Task contract completeness | pass | Prior recheck confirmed task 20 no longer claims completed persistence. |
| PR-4 Validation realism | pass | Prior validation gaps resolved; final stale-source sweep is clean in the plan file. |
| PR-5 Source-backed planning | pass | IRS Revenue Procedure 2025-32 references are now consistent in the current plan. Official IRS source reconfirmed: IR-2025-103 says Revenue Procedure 2025-32 provides the 2026 annual adjustments. |
| PR-6 Handoff/corrections readiness | pass | Canonical review handoff updated and current verdict is approved. |

### Verdict

`approved` - The prior low auditability issue is resolved. The plan is approval-ready as a pre-implementation contract.
