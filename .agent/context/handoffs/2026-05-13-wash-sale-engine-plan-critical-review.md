---
date: "2026-05-13"
review_mode: "plan"
target_plan: "docs/execution/plans/2026-05-13-wash-sale-engine/implementation-plan.md"
verdict: "approved"
findings_count: 0
template_version: "2.1"
requested_verbosity: "standard"
agent: "GPT-5 Codex"
---

# Critical Review: 2026-05-13-wash-sale-engine

> **Review Mode**: `plan`
> **Verdict**: `changes_required`

---

## Scope

**Target**: `docs/execution/plans/2026-05-13-wash-sale-engine/implementation-plan.md`, `docs/execution/plans/2026-05-13-wash-sale-engine/task.md`
**Review Type**: plan review
**Checklist Applied**: PR-1 through PR-6, DR-1 through DR-8 where applicable

Canonical context checked:

- `docs/build-plan/build-priority-matrix.md` Phase 3B rows 57-63
- `docs/build-plan/domain-model-reference.md` Module B
- `docs/BUILD_PLAN.md` Phase 3B rows
- `.agent/context/meu-registry.md` Phase 3B rows
- Existing tax domain/infrastructure code paths
- Official IRS Publication 550 (2025) wash sale section for IRA wording

---

## Commands Executed

```powershell
rg -n "MEU-130|MEU-131|MEU-132|Phase 3B|wash sale|WashSale|401|K401|spousal|TaxProfile|wash_sale_adjustment" docs packages tests .agent/context/meu-registry.md *> C:\Temp\zorivest\plan-review-rg.txt
Test-Path .agent/context/handoffs/2026-05-13-wash-sale-engine-plan-critical-review.md *> C:\Temp\zorivest\plan-review-path.txt
git diff -- docs/execution/plans/2026-05-13-wash-sale-engine/implementation-plan.md docs/execution/plans/2026-05-13-wash-sale-engine/task.md *> C:\Temp\zorivest\plan-review-diff.txt
rg -n "B1|B2|B3|B7|Wash Sale|wash sale|spouse|spousal|IRA|401|permanent|substantially identical|Track full chain|trapped|include_spousal" docs/build-plan/domain-model-reference.md *> C:\Temp\zorivest\plan-review-domain-rg.txt
rg -n "Phase 3B|MEU-130|MEU-131|MEU-132|wash-sale" docs/build-plan/build-priority-matrix.md docs/BUILD_PLAN.md .agent/context/meu-registry.md *> C:\Temp\zorivest\plan-review-canon-rg.txt
rg -n "class TaxLot|class TaxProfile|wash_sale_adjustment|include_spousal_accounts|class AccountType|K401|WashSaleMatchingMethod" packages/core/src/zorivest_core/domain/entities.py packages/core/src/zorivest_core/domain/enums.py packages/core/src/zorivest_core/application/ports.py packages/infrastructure/src/zorivest_infra/database/unit_of_work.py packages/infrastructure/src/zorivest_infra/database/models.py *> C:\Temp\zorivest\plan-review-code-rg.txt
```

Evidence:

- Canonical review file did not exist before this pass: `False`.
- `git diff` for the target plan/task files was empty.
- No correlated implementation handoff was found in the target path during scope checks.

---

## Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 1 | Critical | Task validation commands violate the project's P0 redirect-to-file rule. Most task rows define exact validation commands without `*> C:\Temp\zorivest\...` and without a receipt-read step, even though P0 says every terminal command must redirect all streams to `C:\Temp\zorivest`. Executing the task table as written risks the exact PowerShell buffer saturation failure the project forbids. | `docs/execution/plans/2026-05-13-wash-sale-engine/task.md:21`, `task.md:22`, `task.md:29`, `task.md:44` | Rewrite every validation cell into the approved redirect/read pattern, including quick import, `rg`, `Test-Path`, `Get-Content`, and `Select-String` checks where they are intended as workflow commands. | open |
| 2 | High | The task contract does not encode mandatory FIC-based TDD. The first executable rows are production-code tasks (`Add enums`, `Create entities`, `Implement detect_wash_sales`) and there are no per-MEU FIC rows, Red-phase test rows, or fail-to-pass evidence rows. The build matrix says each Phase 3B row is tests-first, and the session instructions require source-backed FIC plus all tests before production code. | `docs/execution/plans/2026-05-13-wash-sale-engine/task.md:20`, `task.md:21`, `task.md:22`, `docs/build-plan/build-priority-matrix.md:343` | Add explicit FIC rows per MEU, then test-authoring and Red-phase validation rows before implementation rows. Include fail-to-pass evidence requirements before any task can be marked complete. | open |
| 3 | High | The plan turns an unresolved human decision into an implementation requirement. The plan says 401(k) permanent loss destruction is not explicitly stated by IRS Pub 550 and asks for confirmation, but AC-132.3 and task row 16 require `AccountType.K401` destruction. The official IRS Publication 550 (2025) wash sale text names IRA/Roth IRA acquisition; the plan has not captured a completed human approval for extending the rule to 401(k). | `docs/execution/plans/2026-05-13-wash-sale-engine/implementation-plan.md:34`, `implementation-plan.md:130`, `implementation-plan.md:141`, `implementation-plan.md:223`, `docs/execution/plans/2026-05-13-wash-sale-engine/task.md:37` | Resolve Q1 before execution. Either record a Human-approved decision for K401 treatment, or remove K401 from required behavior and tests until an approved rule exists. | open |
| 4 | High | The entity mutability contract is internally contradictory. AC-130.1 requires `WashSaleChain` to be a frozen dataclass, while the sufficiency table says `WashSaleChain` needs status mutation and should be mutable. MEU-131 then requires state transitions (`DISALLOWED -> ABSORBED -> RELEASED`), which cannot be implemented cleanly against a frozen entity without copy/replace semantics that the plan does not specify. | `docs/execution/plans/2026-05-13-wash-sale-engine/implementation-plan.md:46`, `implementation-plan.md:66`, `implementation-plan.md:92` | Pick one source-backed entity model. If immutable, specify transition methods return new chains and repository update semantics. If mutable, remove `frozen` from AC-130.1/AC-130.2 and align tests accordingly. | open |
| 5 | Medium | The infrastructure file layout conflicts with current local canon. The plan/task place models under `zorivest_infra/models/` and repositories under `zorivest_infra/repositories/`, but existing tax persistence lives under `zorivest_infra/database/models.py`, `database/tax_repository.py`, and `database/unit_of_work.py`. This undermines the plan's `Local Canon` source label and may produce disconnected repositories/models. | `docs/execution/plans/2026-05-13-wash-sale-engine/implementation-plan.md:77`, `implementation-plan.md:78`, `docs/execution/plans/2026-05-13-wash-sale-engine/task.md:24`, `task.md:25`, `packages/infrastructure/src/zorivest_infra/database/tax_repository.py:4`, `packages/infrastructure/src/zorivest_infra/database/unit_of_work.py:45` | Align paths with the existing `database/` package or document and source a deliberate persistence-layout split. Update file lists, imports, tests, and UoW wiring rows consistently. | open |
| 6 | Medium | Cross-account scope is ambiguous. AC-132.2 says detection scans "ALL taxable accounts" while citing B3's "taxable + IRA + spouse accounts"; AC-132.3 then separately requires IRA/K401 destruction. This wording can lead to an implementation that excludes IRA/401k lots from the general replacement scan and only handles them as an afterthought. | `docs/execution/plans/2026-05-13-wash-sale-engine/implementation-plan.md:129`, `implementation-plan.md:130`, `docs/build-plan/domain-model-reference.md:465`, `docs/build-plan/domain-model-reference.md:466`, `docs/build-plan/domain-model-reference.md:468` | Rephrase AC-132.2 as all eligible accounts in the selected filing scope, explicitly including taxable, IRA, and spouse accounts where enabled. Keep the IRA/401k destruction rule as a downstream outcome, not a separate scan population. | open |

---

## Checklist Results

### Plan Review (PR)

| Check | Result | Evidence |
|-------|--------|----------|
| PR-1 Plan/task alignment | fail | Plan status is `draft` while `task.md` status is `in_progress`; task rows also omit FIC/Red-phase work required by the plan's tests-first source context. |
| PR-2 Not-started confirmation | pass | All task rows remain `[ ]`; target plan/task diff is empty; no canonical review handoff existed before this pass. |
| PR-3 Task contract completeness | partial | Rows include owner/deliverable/validation/status, but validation commands are not P0-compliant and TDD/FIC evidence rows are missing. |
| PR-4 Validation realism | fail | Commands in task rows are not safe/runnable under project P0 shell rules and do not encode Red-phase fail-to-pass evidence. |
| PR-5 Source-backed planning | fail | K401 treatment is marked Human-approved pending, but it is implemented as a requirement before approval. Frozen vs mutable entity behavior is internally unsourced. |
| PR-6 Handoff/corrections readiness | pass | Plan has explicit post-implementation handoff/reflection/metrics rows; findings can be resolved via `/plan-corrections`. |

### Docs Review (DR)

| Check | Result | Evidence |
|-------|--------|----------|
| DR-1 Claim-to-state match | fail | `task.md` says `in_progress`; row state and lack of handoff/diff indicate unstarted work. |
| DR-2 Residual old terms | pass | No slug migration/rename is under review. |
| DR-3 Downstream references updated | fail | Infrastructure paths do not match current database package canon. |
| DR-4 Verification robustness | fail | Task validation would not enforce P0 or fail-to-pass proof. |
| DR-5 Evidence auditability | partial | Implementation plan has a verification section with receipt paths, but the task table does not. |
| DR-6 Cross-reference integrity | fail | K401 and mutable/frozen contracts conflict across the same plan. |
| DR-7 Evidence freshness | pass | Review sweeps were run against current file state. |
| DR-8 Completion vs residual risk | pass | No completion claim is made by the plan. |

---

## Open Questions / Assumptions

- Q1 from the plan remains unresolved: whether `AccountType.K401` should be treated like IRA/Roth IRA for permanent loss destruction.
- I treated official IRS Publication 550 (2025) as the current primary external source for wash sale wording. It supports IRA/Roth IRA handling and basis/holding-period rules, but I did not find explicit 401(k) wording in the reviewed IRS source.
- I assumed `/plan-corrections` is the intended next workflow because this review is findings-only.

---

## Verdict

`changes_required` - Do not start implementation from this task table. The plan needs corrections for P0-safe commands, FIC/TDD sequencing, K401 approval/source treatment, entity mutability, and infrastructure path alignment.

---

## Follow-Up Actions

1. Run `/plan-corrections` against this review file.
2. Resolve K401 treatment before execution by recording a Human-approved decision or removing K401 from required behavior.
3. Rewrite task validations to use `C:\Temp\zorivest\` receipt files consistently.
4. Add FIC, Red-phase, Green-phase, and evidence rows per MEU.
5. Align wash sale persistence paths with existing tax infrastructure canon.

---

## Corrections Applied — 2026-05-13

**Agent**: Gemini (corrections role)
**Verdict**: `corrections_applied`

### Summary

All 6 findings resolved across `implementation-plan.md` and `task.md`.

| # | Severity | Finding | Resolution | Verified |
|---|----------|---------|------------|----------|
| 1 | Critical | P0 validation commands | All 29 `uv run` cells now use `*> C:\Temp\zorivest\` redirect + `Get-Content \| Select-Object -Last N` | ✅ `rg` confirms 0 bare commands |
| 2 | High | TDD sequencing | Added 3 FIC rows + 3 Red-phase rows + 3 Green-phase rows (9 new rows, task count 25→38) | ✅ `rg` confirms presence |
| 3 | High | K401 unapproved | Removed K401 from AC-132.3 (IRA-only). Added task #31 as `[B]` blocked on Q1 human approval | ✅ K401 only in deferred/blocked contexts |
| 4 | High | Frozen vs mutable | AC-130.1 → "mutable dataclass", AC-130.2 stays "frozen dataclass". Spec sufficiency table aligned. | ✅ No contradiction in `rg` output |
| 5 | Medium | Infrastructure paths | All `models/` → `database/`, `repositories/` → `database/`. Source labels corrected. | ✅ 0 hits for old paths |
| 6 | Medium | Cross-account scope | AC-132.2 → "all accounts in the user's filing scope (taxable, IRA, and spousal accounts when enabled)" | ✅ `rg` confirms new wording |

### Additional Fixes

- `task.md` frontmatter `status` corrected: `"in_progress"` → `"draft"` (PR-1/DR-1 alignment)
- `implementation-plan.md` goal section: removed K401 from bullet 5 ("IRA/401k" → "IRA")
- Cross-doc sweep: 1 file checked, 0 updates needed (review file references are historical finding text, not stale refs)

### Checklist Re-Assessment

| Check | Original | After Corrections |
|-------|----------|-------------------|
| PR-1 | fail | expected pass (status aligned, TDD rows present) |
| PR-3 | partial | expected pass (P0 commands + TDD evidence rows) |
| PR-4 | fail | expected pass (all validation cells P0-compliant) |
| PR-5 | fail | expected pass (K401 deferred, frozen/mutable resolved) |
| DR-1 | fail | expected pass (status = draft, matches plan) |
| DR-3 | fail | expected pass (database/ paths aligned) |
| DR-4 | fail | expected pass (redirect pattern + Red/Green gates) |
| DR-6 | fail | expected pass (no internal contradictions) |

### Next Steps

1. Run `/plan-critical-review` to re-validate corrected plan files
2. Resolve Q1 (K401 treatment) — human decision required
3. After review passes → proceed to `/execution-session`

---

## Recheck (2026-05-13)

**Workflow**: `/plan-critical-review` recheck
**Agent**: GPT-5 Codex

### Commands Executed

```powershell
rg -n "K401|401k|IRA/401|IRA/401k|Human-approved \(pending\)|permanent loss destruction" docs/execution/plans/2026-05-13-wash-sale-engine/implementation-plan.md docs/execution/plans/2026-05-13-wash-sale-engine/task.md *> C:\Temp\zorivest\recheck-k401.txt
rg -n "zorivest_infra/(models|repositories)|models/wash_sale_model|repositories/wash_sale_repository|database/wash_sale|database/models.py|database/tax_repository.py" docs/execution/plans/2026-05-13-wash-sale-engine/implementation-plan.md docs/execution/plans/2026-05-13-wash-sale-engine/task.md *> C:\Temp\zorivest\recheck-paths.txt
rg -n "frozen dataclass|mutable dataclass|WashSaleChain|WashSaleEntry|Entity mutability|copy/replace|replace\(" docs/execution/plans/2026-05-13-wash-sale-engine/implementation-plan.md *> C:\Temp\zorivest\recheck-mutability.txt
rg -n "FIC|Red-phase|Green-phase|FAIL_TO_PASS|fail-to-pass|tests first|Write tests|NEW tests FAIL|ALL PASS" docs/execution/plans/2026-05-13-wash-sale-engine/task.md docs/execution/plans/2026-05-13-wash-sale-engine/implementation-plan.md *> C:\Temp\zorivest\recheck-tdd.txt
rg -n "\| [^|]*(uv run|python |rg |Test-Path|Get-Content|Select-String|echo )" docs/execution/plans/2026-05-13-wash-sale-engine/task.md *> C:\Temp\zorivest\recheck-all-validations.txt
git diff -- docs/execution/plans/2026-05-13-wash-sale-engine/implementation-plan.md docs/execution/plans/2026-05-13-wash-sale-engine/task.md .agent/context/handoffs/2026-05-13-wash-sale-engine-plan-critical-review.md *> C:\Temp\zorivest\recheck-diff.txt
Test-Path .agent/context/handoffs/2026-05-13-wash-sale-engine-handoff.md *> C:\Temp\zorivest\recheck-impl-handoff.txt
```

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|--------------|----------------|
| P0 validation commands | open | Fixed for command-based task rows. All pytest/pyright/import/rg/Test-Path rows now route output to `C:\Temp\zorivest\` receipts. |
| Missing FIC/TDD sequencing | open | Partially fixed. FIC, Red-phase, and Green-phase rows were added per MEU, but FIC row validation is not an exact command. |
| K401 unapproved requirement | open | Fixed. K401 is removed from required IRA destruction ACs and deferred to blocked task #31 pending human approval. |
| Frozen vs mutable entity contradiction | open | Fixed. `WashSaleChain` is mutable; `WashSaleEntry` is frozen; sufficiency table aligns with that contract. |
| Infrastructure path drift | open | Fixed. Plan now targets `packages/infrastructure/src/zorivest_infra/database/wash_sale_models.py` and `database/wash_sale_repository.py`. |
| Cross-account scope ambiguity | open | Fixed. AC-132.2 now says all accounts in filing scope, including taxable, IRA, and spousal accounts when enabled. |

### Confirmed Fixes

- `implementation-plan.md:6` and `task.md:5` are both `status: "draft"`, resolving the plan/task status mismatch.
- `implementation-plan.md:46` and `implementation-plan.md:66` align on mutable `WashSaleChain` and frozen `WashSaleEntry`.
- `implementation-plan.md:129` through `implementation-plan.md:132` scope cross-account detection to filing-scope accounts and IRA-only destruction.
- `task.md:21` through `task.md:62` show command-based validation rows using receipt files for pytest, pyright, import, `rg`, `Select-String`, `Test-Path`, and MEU gate checks.
- `task.md:53` keeps K401 as `[B]` blocked pending human approval instead of implementing it as current required behavior.

### Remaining Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| R1 | Medium | The three FIC rows still do not satisfy the plan creation contract's exact-validation requirement. Their validation cells say "Visual confirmation ACs match plan" rather than a reproducible command or file check, so the task table still has non-auditable validation for source-backed FIC creation. | `docs/execution/plans/2026-05-13-wash-sale-engine/task.md:20`, `task.md:33`, `task.md:43` | Replace each FIC row validation with an exact command or MCP-readable artifact check, for example `Test-Path <fic-path> *> C:\Temp\zorivest\<fic-check>.txt; Get-Content ...` plus an `rg "AC-130|Source|Spec|Local Canon|Research-backed|Human-approved" <fic-path> *> ...` receipt. | open |

### Checklist Results

| Check | Result | Evidence |
|-------|--------|----------|
| PR-1 Plan/task alignment | pass | Both files are `draft`; scope remains MEU-130 through MEU-132. |
| PR-2 Not-started confirmation | pass | All implementation rows remain `[ ]`; no implementation handoff exists (`Test-Path` returned `False`). |
| PR-3 Task contract completeness | fail | FIC rows have validation text but not exact validation commands. |
| PR-4 Validation realism | partial | Command-based rows are P0-safe; FIC validation remains non-reproducible. |
| PR-5 Source-backed planning | pass | K401 is deferred, IRA behavior remains research-backed, and mutability conflict is resolved. |
| PR-6 Handoff/corrections readiness | pass | Same canonical rolling review file is updated; remaining issue is resolvable via `/plan-corrections`. |

### Verdict

`changes_required` - The major blockers are resolved, but the plan still needs exact, reproducible validation for the three FIC rows before it should be approved for execution.

---

## Corrections Applied — 2026-05-13 (Pass 2)

**Agent**: Gemini (corrections role)
**Finding**: R1 — FIC row validation cells non-auditable

### Fix

Replaced "Visual confirmation ACs match plan" in 3 FIC rows (task.md L20, L33, L43) with exact, P0-compliant validation commands:

```
Test-Path <fic-path> *> C:\Temp\zorivest\<receipt>.txt
rg "Spec|Local Canon|Research-backed|Human-approved" <fic-path> *>> C:\Temp\zorivest\<receipt>.txt
Get-Content C:\Temp\zorivest\<receipt>.txt
```

Each FIC row now validates: (1) file exists, (2) contains source-backed AC labels.

### Verification

- `rg "Visual confirmation" task.md` → 0 hits ✅
- `rg "Test-Path.*fic-meu" task.md` → 3 hits (L20, L33, L43) ✅

### Verdict

`corrections_applied` — all R1 findings resolved. Ready for `/plan-critical-review` re-review.

---

## Recheck (2026-05-13, Pass 2)

**Workflow**: `/plan-critical-review` recheck
**Agent**: GPT-5 Codex

### Commands Executed

```powershell
rg -n "Visual confirmation|FIC for MEU|Test-Path.*fic|Spec|Local Canon|Research-backed|Human-approved" docs/execution/plans/2026-05-13-wash-sale-engine/task.md *> C:\Temp\zorivest\recheck2-fic.txt
rg -n "K401|401k|Human-approved \(pending\)|IRA/401|IRA/401k|frozen dataclass|mutable dataclass|zorivest_infra/(models|repositories)|models/wash_sale_model|repositories/wash_sale_repository|all taxable accounts|Visual confirmation" docs/execution/plans/2026-05-13-wash-sale-engine/implementation-plan.md docs/execution/plans/2026-05-13-wash-sale-engine/task.md *> C:\Temp\zorivest\recheck2-old-patterns.txt
Test-Path .agent/context/handoffs/2026-05-13-wash-sale-engine-handoff.md *> C:\Temp\zorivest\recheck2-impl-handoff.txt
git diff -- docs/execution/plans/2026-05-13-wash-sale-engine/implementation-plan.md docs/execution/plans/2026-05-13-wash-sale-engine/task.md .agent/context/handoffs/2026-05-13-wash-sale-engine-plan-critical-review.md *> C:\Temp\zorivest\recheck2-diff.txt
```

### Prior Finding Recheck

| Finding | Prior Status | Recheck Result |
|---------|--------------|----------------|
| R1: FIC row validation cells non-auditable | open | Fixed. `task.md:20`, `task.md:33`, and `task.md:43` now use exact `Test-Path` + source-label `rg` commands with `C:\Temp\zorivest\` receipts. |

### Confirmed Fixes

- `rg "Visual confirmation" task.md` is effectively clean: no `Visual confirmation` hit appears in the current FIC-row sweep.
- `task.md:20`, `task.md:33`, and `task.md:43` each validate the expected FIC artifact exists and contains one of the allowed source labels (`Spec`, `Local Canon`, `Research-backed`, `Human-approved`).
- No implementation handoff exists yet: `Test-Path .agent/context/handoffs/2026-05-13-wash-sale-engine-handoff.md` returned `False`, so this remains an unstarted plan review rather than an execution review.
- K401 remains deferred to blocked task #31, not current required behavior.
- Mutability, infrastructure path, and cross-account wording fixes remain in place.

### Checklist Results

| Check | Result | Evidence |
|-------|--------|----------|
| PR-1 Plan/task alignment | pass | Plan/task remain scoped to MEU-130 through MEU-132 and both are draft planning artifacts. |
| PR-2 Not-started confirmation | pass | No implementation handoff exists; all task implementation rows remain unchecked. |
| PR-3 Task contract completeness | pass | Task rows now include owner, deliverable, validation, and status; FIC rows now have exact validation commands. |
| PR-4 Validation realism | pass | FIC rows and test/check rows use reproducible receipt-based commands. |
| PR-5 Source-backed planning | pass | Required K401 behavior is deferred, and source-backed labels are enforced by FIC validation rows. |
| PR-6 Handoff/corrections readiness | pass | Rolling review file updated; no remaining plan-corrections findings. |

### Verdict

`approved` - The corrected plan is ready to proceed to the next human-approved workflow gate. K401 permanent-loss treatment remains a blocked future decision and is not part of the approved execution scope.
