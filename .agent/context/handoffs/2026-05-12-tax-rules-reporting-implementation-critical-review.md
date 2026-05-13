---
date: "2026-05-12"
review_mode: "multi-handoff"
target_plan: "docs/execution/plans/2026-05-12-tax-rules-reporting/implementation-plan.md"
verdict: "approved"
findings_count: 5
template_version: "2.1"
requested_verbosity: "standard"
agent: "GPT-5 Codex"
---

# Critical Review: 2026-05-12-tax-rules-reporting

> **Review Mode**: `multi-handoff`
> **Verdict**: `approved`

---

## Scope

**Target**: `.agent/context/handoffs/2026-05-12-tax-rules-reporting-handoff.md`
**Review Type**: implementation handoff review, expanded to full correlated project scope
**Correlation rationale**: User supplied the seed handoff. Its frontmatter project slug and MEU set match `docs/execution/plans/2026-05-12-tax-rules-reporting/`, covering MEU-127/128/129. The plan, task, reflection, registry entries, BUILD_PLAN rows, and all claimed source/test files were in scope.
**Checklist Applied**: IR + DR + execution-critical-review implementation checklist

Reviewed files/artifacts:
- `.agent/context/handoffs/2026-05-12-tax-rules-reporting-handoff.md`
- `docs/execution/plans/2026-05-12-tax-rules-reporting/implementation-plan.md`
- `docs/execution/plans/2026-05-12-tax-rules-reporting/task.md`
- `docs/execution/reflections/2026-05-12-tax-rules-reporting-reflection.md`
- `.agent/context/meu-registry.md`
- `docs/BUILD_PLAN.md`
- `packages/core/src/zorivest_core/domain/tax/loss_carryforward.py`
- `packages/core/src/zorivest_core/domain/tax/option_pairing.py`
- `packages/core/src/zorivest_core/domain/tax/ytd_pnl.py`
- `packages/core/src/zorivest_core/services/tax_service.py`
- `packages/core/src/zorivest_core/domain/tax/__init__.py`
- `packages/core/src/zorivest_core/services/__init__.py`
- `tests/unit/test_loss_carryforward.py`
- `tests/unit/test_option_pairing.py`
- `tests/unit/test_ytd_pnl.py`
- `tests/unit/test_tax_service.py`
- `tests/integration/test_tax_service_integration.py`

Direct file reads were required because several reviewed implementation files are currently untracked, so `git diff` is not sufficient source-of-truth evidence.

---

## Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 1 | High | `get_taxable_gains()` and `get_ytd_pnl()` aggregate only the first repository page of closed lots. Both call `list_filtered(is_closed=True)` without overriding the port default `limit=100`; the SQL repository enforces `.limit(limit)`. Annual taxable gains and YTD P&L will silently omit lot 101+ in real persistence, violating AC-127.4/127.5 and AC-129.4/129.5. | `packages/core/src/zorivest_core/services/tax_service.py:434`, `packages/core/src/zorivest_core/services/tax_service.py:558`, `packages/core/src/zorivest_core/application/ports.py:363`, `packages/infrastructure/src/zorivest_infra/database/tax_repository.py:97` | Add an all-pages retrieval path for aggregate tax reports, or a repository method intended for unpaginated reporting queries. Add an integration/regression test with more than 100 closed lots proving all lots are included. | fixed on recheck |
| 2 | High | Option assignment/exercise accepts mismatched put/call paths. The code parses `option_details` and validates underlying ticker, but never checks `option_details.put_call` against `assignment_type` before applying one of the four basis/proceeds formulas. A written call can be processed as `WRITTEN_PUT_ASSIGNMENT`, incorrectly reducing basis instead of increasing sale proceeds. | `packages/core/src/zorivest_core/domain/tax/option_pairing.py:174`, `packages/core/src/zorivest_core/domain/tax/option_pairing.py:201` | Enforce `AssignmentType` to option-kind compatibility: written put and long put require `P`; written call and long call require `C`. Add negative tests for all mismatched combinations and keep the action-side validation. | fixed on recheck |
| 3 | Medium | AC-128.6 service persistence coverage is narrower than the handoff claims. `TestPairOptionAssignment` exercises only short put persistence plus not-found cases; it does not test short call, long call, long put, or that the option trade ID is linked. The handoff claims service persistence for all four IRS scenarios. | `tests/unit/test_tax_service.py:877`, `tests/unit/test_tax_service.py:896`, `tests/unit/test_tax_service.py:923` | Add service-level tests for all four assignment paths, including exact persisted `cost_basis`/`proceeds` and `linked_trade_ids` assertions. | fixed on recheck |
| 4 | Medium | `test_applies_carryforward_from_tax_profile` is a weak IR-5 test. Its only postcondition is `result.deductible_loss >= 0`, which would pass if the service ignored `TaxProfile.capital_loss_carryforward` entirely. This does not prove AC-127.5. | `tests/unit/test_tax_service.py:815`, `tests/unit/test_tax_service.py:852` | Assert exact `deductible_loss`, `remaining_st_carryforward`, `remaining_lt_carryforward`, and net ST/LT outputs for a profile-backed scenario. | fixed on recheck |
| 5 | Low | The MEU gate reports the handoff evidence bundle is incomplete: missing `Evidence/FAIL_TO_PASS`, `Pass-fail/Commands`, and `Commands/Codex Report`. Blocking checks pass, but the review artifact is less auditable than the workflow requires. | `C:\Temp\zorivest\validate-review.txt:18` | Update the work handoff or correction handoff with compressed FAIL_TO_PASS and command evidence after fixes. | warning on recheck |

---

## Checklist Results

### Implementation Review (IR)

| Check | Result | Evidence |
|-------|--------|----------|
| IR-1 Live runtime evidence | fail | Existing integration test file covers MEU-126 `get_lots`/`close_lot`/`simulate_impact`; `rg` found MEU-127/128/129 service method tests only in `tests/unit/test_tax_service.py`, not integration tests. |
| IR-2 Stub behavioral compliance | n/a | Scope is core domain/service logic, not API stubs. |
| IR-3 Error mapping completeness | n/a | No REST/API write routes in this MEU scope. |
| IR-4 Fix generalization | pass | Prior task post-implementation rows are complete; no correction fix series reviewed here. |
| IR-5 Test rigor audit | fail | `test_loss_carryforward.py`: Strong. `test_option_pairing.py`: Adequate, but missing option-kind mismatch negatives. `test_ytd_pnl.py`: Strong. `test_tax_service.py`: Weak for carryforward assertion and incomplete pair-option service persistence coverage. |
| IR-6 Boundary validation coverage | n/a | No external input boundaries were added (no REST/MCP/UI/file/env write surface). |

### Docs Review (DR)

| Check | Result | Evidence |
|-------|--------|----------|
| DR-1 Claim-to-state match | fail | Handoff claims AC-128.6 all four service scenarios; file state shows only `test_pair_short_put_assignment` plus two not-found tests. |
| DR-2 Residual old terms | pass | `docs/BUILD_PLAN.md:618-620` and `.agent/context/meu-registry.md:445-447` show MEU-127/128/129 at validation status. |
| DR-3 Downstream references updated | pass | BUILD_PLAN and registry rows match the project status intent. |
| DR-4 Verification robustness | fail | Current tests pass while the option-kind mismatch probe accepts an invalid scenario and aggregate reporting truncates real repo results after 100 lots. |
| DR-5 Evidence auditability | fail | MEU gate advisory A3 reports missing handoff evidence sections. |
| DR-6 Cross-reference integrity | pass | Known MEU-128 GUI ID collision remains documented in known issues and is out of this runtime scope. |
| DR-7 Evidence freshness | pass | Reproduced full pytest matches handoff: `3196 passed, 23 skipped`. |
| DR-8 Completion vs residual risk | fail | Handoff says "Known Issues: None introduced", but review found runtime correctness defects and weak tests. |

### Test Rigor Ratings (IR-5)

| Test File | Rating | Rationale |
|-----------|--------|-----------|
| `tests/unit/test_loss_carryforward.py` | Strong | Specific cap, netting, negative-carryforward, and character-preservation assertions. |
| `tests/unit/test_option_pairing.py` | Adequate | Covers four positive formulas and action mismatches, but misses put/call-to-assignment mismatches. |
| `tests/unit/test_ytd_pnl.py` | Strong | Specific totals, ST/LT split, year filtering, ticker aggregation, and loss assertions. |
| `tests/unit/test_tax_service.py` | Weak in MEU-127/128 sections | Carryforward assertion is non-specific; option service coverage only proves one of four persistence paths and omits link assertion. |

---

## Commands Executed

All command output was redirected to `C:\Temp\zorivest\*.txt` and read from receipt files.

| Command | Receipt | Result |
|---------|---------|--------|
| `git status --short` | `C:\Temp\zorivest\review-git-status.txt` | Dirty worktree with reviewed implementation files currently untracked. |
| `git diff -- <claimed tracked files>` | `C:\Temp\zorivest\review-git-diff.txt` | Confirmed BUILD_PLAN, registry, metrics, and service export diffs; untracked new files required direct reads. |
| `rg -n "TODO|FIXME|NotImplementedError" packages/` | `C:\Temp\zorivest\review-placeholders.txt` | One pre-existing `step_registry.py:88` `NotImplementedError`, matching handoff note. |
| `uv run pytest tests/unit/test_loss_carryforward.py tests/unit/test_option_pairing.py tests/unit/test_ytd_pnl.py tests/unit/test_tax_service.py -x --tb=short -v` | `C:\Temp\zorivest\pytest-review-tax.txt` | `97 passed, 1 warning in 0.58s`. |
| `uv run pyright packages/` | `C:\Temp\zorivest\pyright-review.txt` | `0 errors, 0 warnings, 0 informations`. |
| `uv run ruff check packages/` | `C:\Temp\zorivest\ruff-review.txt` | `All checks passed!` |
| `uv run python tools/validate_codebase.py --scope meu` | `C:\Temp\zorivest\validate-review.txt` | 8/8 blocking checks PASS; advisory A3 reports missing handoff evidence sections. |
| `uv run pytest tests/ -x --tb=short -v` | `C:\Temp\zorivest\pytest-review-full.txt` | `3196 passed, 23 skipped, 3 warnings in 192.49s`. |
| Python probe for mismatched option kind | `C:\Temp\zorivest\review-option-mismatch-probe.txt` | `accepted_invalid_option_type 145.00 0.00`, confirming Finding 2. |
| Targeted `rg` line-reference sweeps | `C:\Temp\zorivest\review-lines.txt`, `review-pagination-lines.txt`, `review-method-test-lines.txt` | Produced file:line evidence for findings. |

External source check:
- IRS Publication 550 (2025), "Puts and Calls": holder call/put and writer put/call adjustments are distinct (`https://www.irs.gov/publications/p550`, lines 6041, 6065-6066, 6077-6082 in fetched page).
- IRS Schedule D Instructions (2025), "Capital Losses": $3,000 / $1,500 capital loss limit (`https://www.irs.gov/instructions/i1040sd`, line 584 in fetched page).

---

## Verdict

`changes_required` - The blocking gates pass and the broad direction of the implementation is sound, but there are two runtime correctness defects: aggregate tax reports are capped at 100 closed lots, and option assignment accepts the wrong put/call path for a requested IRS adjustment. The service tests also overstate AC-128.6 coverage and include one weak carryforward assertion that would not catch a no-op implementation.

Required follow-up actions:
1. Fix aggregate closed-lot retrieval for `get_taxable_gains()` and `get_ytd_pnl()` so all matching lots are included.
2. Validate option `put_call` compatibility with `AssignmentType`, with mismatch tests.
3. Strengthen service tests for carryforward exact outputs and all four option persistence paths, including link persistence.
4. Re-run targeted tests, full pytest, pyright, ruff, MEU gate, and update the evidence bundle.

---

## Residual Risk

The domain-level loss carryforward and YTD P&L functions are well covered, and full pytest/MEU gate are green. Residual risk is concentrated in service orchestration against real repositories and option-path validation. No product files were modified during this review.

---

## Corrections Applied (2026-05-12)

**Verdict update**: `changes_required` → `corrections_applied`

### Changes Made

| Finding | Fix | Files Modified |
|---------|-----|----------------|
| F1 (High) | Added `list_all_filtered()` port + repo + switched both aggregate service methods | `ports.py`, `tax_repository.py`, `tax_service.py` |
| F2 (High) | Added `_REQUIRED_PUT_CALL` mapping + validation in `adjust_basis_for_assignment` | `option_pairing.py` |
| F3 (Med) | Added 3 service tests (short call, long call, long put) + `linked_trade_ids` assertion | `test_tax_service.py` |
| F4 (Med) | Replaced `>= 0` with exact values (`deductible_loss=3000`, `remaining_st=4000`) | `test_tax_service.py` |
| F5 (Low) | Updated evidence bundle (this section) | This file |

### FAIL_TO_PASS Evidence

```
FAILED test_option_pairing.py::TestPutCallAssignmentMismatch::test_call_option_with_written_put_assignment_raises - DID NOT RAISE
FAILED test_option_pairing.py::TestPutCallAssignmentMismatch::test_put_option_with_written_call_assignment_raises - DID NOT RAISE
FAILED test_option_pairing.py::TestPutCallAssignmentMismatch::test_put_option_with_long_call_exercise_raises - DID NOT RAISE
FAILED test_option_pairing.py::TestPutCallAssignmentMismatch::test_call_option_with_long_put_exercise_raises - DID NOT RAISE
FAILED test_tax_service.py::TestAggregatePaginationRegression::test_get_taxable_gains_includes_all_150_lots - Decimal('0') != Decimal('1500.00')
FAILED test_tax_service.py::TestAggregatePaginationRegression::test_get_ytd_pnl_includes_all_150_lots - Decimal('0') != Decimal('1500.00')
```

After production fixes: 6 FAIL → 6 PASS.

### Quality Gates

```
pytest:   3205 passed, 0 failed, 23 skipped (190s)
pyright:  0 errors, 0 warnings
ruff:     All checks passed
```

---

## Recheck (2026-05-12)

**Workflow**: `/execution-critical-review` recheck
**Agent**: GPT-5 Codex
**Verdict**: `approved`

### Prior Findings

| Finding | Prior Status | Recheck Result |
|---------|-------------|----------------|
| F1: Aggregate reports capped at first 100 closed lots | open | Fixed. `TaxLotRepository.list_all_filtered()` exists, SQL implementation uses `.all()` without `.limit()`, and `TaxService.get_taxable_gains()` / `get_ytd_pnl()` call it. Runtime SQL probe: `list_filtered 100`, `list_all_filtered 150`. |
| F2: Option assignment accepts mismatched put/call paths | open | Fixed. `_REQUIRED_PUT_CALL` maps each `AssignmentType` to expected `P`/`C`, and `adjust_basis_for_assignment()` raises `BusinessRuleError` on mismatch. |
| F3: Service persistence coverage only tested short put | open | Fixed. Service tests now cover short put, short call, long call, and long put with exact persisted cost basis/proceeds plus `linked_trade_ids`. |
| F4: Weak carryforward assertion | open | Fixed. TaxProfile carryforward service test now asserts exact deductible loss, remaining ST/LT carryforward, and net ST/LT outputs. |
| F5: Handoff evidence bundle incomplete | open | Partially fixed. Correction evidence is present in this canonical review file; `validate_codebase.py --scope meu` still reports advisory A3 against the original work handoff. This is auditability-only and not a runtime blocker. |

### Commands Executed

| Command | Receipt | Result |
|---------|---------|--------|
| `git status --short` | `C:\Temp\zorivest\recheck-git-status.txt` | Dirty worktree confirmed; reviewed files are still in local pending changes/untracked state. |
| `rg -n -F ...` line evidence sweep | `C:\Temp\zorivest\recheck-lines-clean.txt` | Confirmed `list_all_filtered`, `_REQUIRED_PUT_CALL`, mismatch tests, pagination regression tests, and new service path tests. |
| `uv run pytest tests/unit/test_option_pairing.py tests/unit/test_tax_service.py -x --tb=short -v` | `C:\Temp\zorivest\pytest-recheck-targeted.txt` | `73 passed, 1 warning`. |
| `uv run pytest tests/unit/test_loss_carryforward.py tests/unit/test_option_pairing.py tests/unit/test_ytd_pnl.py tests/unit/test_tax_service.py tests/integration/test_tax_service_integration.py -x --tb=short -v` | `C:\Temp\zorivest\pytest-recheck-tax-scope.txt` | `115 passed, 1 warning`. |
| `uv run pytest tests/ -x --tb=short -v` | `C:\Temp\zorivest\pytest-recheck-full.txt` | `3205 passed, 23 skipped, 3 warnings`. |
| `uv run pyright packages/` | `C:\Temp\zorivest\pyright-recheck.txt` | `0 errors, 0 warnings, 0 informations`. |
| `uv run ruff check packages/` | `C:\Temp\zorivest\ruff-recheck.txt` | `All checks passed!` |
| `uv run python tools/validate_codebase.py --scope meu` | `C:\Temp\zorivest\validate-recheck.txt` | 8/8 blocking checks PASS; advisory A3 remains for original work handoff evidence sections. |
| SQL repository pagination probe | `C:\Temp\zorivest\recheck-sql-list-all-probe.txt` | `list_filtered 100`, `list_all_filtered 150`. |

### Checklist Results

| Check | Result | Evidence |
|-------|--------|----------|
| IR-1 Live runtime evidence | pass | SQL repository probe verifies the real repository method returns all 150 seeded rows; tax integration suite also passes. |
| IR-4 Fix generalization | pass | Both aggregate service methods were moved from `list_filtered(is_closed=True)` to `list_all_filtered(is_closed=True)`. |
| IR-5 Test rigor audit | pass | Previously weak carryforward and option service tests now assert exact values and all four option paths. |
| DR-5 Evidence auditability | warning | Original work handoff still triggers validate advisory A3; correction evidence is preserved here. |
| DR-7 Evidence freshness | pass | Reproduced full pytest result matches correction claim: `3205 passed, 23 skipped`. |

### Verdict

`approved` - The two runtime correctness defects and two medium test-rigor findings are resolved. Remaining risk is a low, non-blocking auditability warning: the original handoff artifact still lacks validate-recognized evidence section headings, although this review file contains the correction evidence and command receipts.
