---
date: "2026-05-12"
review_mode: "handoff"
target_plan: "docs/execution/plans/2026-05-12-tax-logic-expansion/implementation-plan.md"
verdict: "corrections_applied"
findings_count: 0
template_version: "2.1"
requested_verbosity: "standard"
agent: "GPT-5.5 Codex"
---

# Critical Review: tax-logic-expansion

> **Review Mode**: `handoff`
> **Verdict**: `changes_required`

---

## Scope

**Target**: `.agent/context/handoffs/2026-05-12-tax-logic-expansion-handoff.md`
**Review Type**: implementation handoff review for `docs/execution/plans/2026-05-12-tax-logic-expansion/`
**Checklist Applied**: execution-critical-review IR/DR/PR plus implementation checklist IR-1 through IR-6

### Correlation Rationale

The user supplied the execution critical review workflow and the handoff path. The handoff frontmatter identifies `project: tax-logic-expansion` and `meus: [MEU-125, MEU-126]`, matching the plan folder `docs/execution/plans/2026-05-12-tax-logic-expansion/`. Because this is a two-MEU project, the seed handoff was expanded to include the correlated `implementation-plan.md`, `task.md`, reflection, metrics row, BUILD_PLAN status, claimed source files, and all claimed test files.

### Artifacts Reviewed

- `.agent/context/handoffs/2026-05-12-tax-logic-expansion-handoff.md`
- `docs/execution/plans/2026-05-12-tax-logic-expansion/implementation-plan.md`
- `docs/execution/plans/2026-05-12-tax-logic-expansion/task.md`
- `docs/execution/reflections/2026-05-12-tax-logic-expansion-reflection.md`
- `docs/execution/metrics.md`
- `docs/BUILD_PLAN.md`
- `packages/core/src/zorivest_core/domain/tax/__init__.py`
- `packages/core/src/zorivest_core/domain/tax/lot_selector.py`
- `packages/core/src/zorivest_core/domain/tax/gains_calculator.py`
- `packages/core/src/zorivest_core/services/tax_service.py`
- `tests/unit/test_lot_selector.py`
- `tests/unit/test_gains_calculator.py`
- `tests/unit/test_tax_service.py`
- `tests/integration/test_tax_service_integration.py`

---

## Commands Executed

| Command | Result |
|---------|--------|
| `git status --short *> C:\Temp\zorivest\review-git-status.txt` | Working tree includes untracked tax logic files plus unrelated modified `ui/electron.vite.config.ts` |
| `git diff --stat *> C:\Temp\zorivest\review-git-diff-stat.txt` | Tracked diff only shows `.agent/context/current-focus.md`, `docs/execution/metrics.md`, `ui/electron.vite.config.ts`; most reviewed files are untracked |
| `uv run pytest tests/unit/test_lot_selector.py tests/unit/test_gains_calculator.py tests/unit/test_tax_service.py tests/integration/test_tax_service_integration.py -x --tb=short -v *> C:\Temp\zorivest\review-targeted-pytest.txt` | 72 passed, 1 warning |
| `uv run pytest tests/ -x --tb=short *> C:\Temp\zorivest\review-full-pytest.txt` | 3114 passed, 23 skipped, 3 warnings |
| `uv run pyright packages/ *> C:\Temp\zorivest\review-pyright.txt` | 0 errors, 0 warnings |
| `uv run ruff check packages/ *> C:\Temp\zorivest\review-ruff.txt` | All checks passed |
| `uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\review-meu-gate.txt` | 8/8 blocking PASS; advisory A3 warns handoff is missing Evidence/FAIL_TO_PASS, Pass-fail/Commands, Commands/Codex Report |
| `rg -n "TaxService|close_lot|reassign_basis|simulate_impact|TaxLot|CostBasisMethod|wash_sale|cost basis|tax lot" docs/build-plan docs/architecture.md .agent/docs/architecture.md *> C:\Temp\zorivest\review-spec-rg.txt` | Found relevant local canon; also confirmed `docs/architecture.md` path does not exist |
| `rg -n "MEU-125|MEU-126|tax-logic-expansion|tax-lot-tracking|tax-gains-calc" .agent/context/meu-registry.md docs/BUILD_PLAN.md docs/execution/metrics.md *> C:\Temp\zorivest\review-shared-artifacts.txt` | Metrics row present; BUILD_PLAN rows still `⬜`; no registry hit |

External source check: official IBKR Trader Workstation "Lot Matching Methods" page confirms the MLG/MLL/MSG/MSL tier ordering and was last updated October 8, 2025. The lot selector implementation matches those published tier rules.

---

## Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 1 | High | `TaxService` method signatures do not satisfy the local API/service contract. Local canon calls `service.simulate_impact(body)`, `service.get_lots(account_id, ticker, status, sort_by)`, `service.close_lot(lot_id)`, and `service.reassign_basis(lot_id, body)`, but the implementation exposes positional/internal signatures with different arity and types. API wiring in MEU-148 would raise `TypeError` or pass wrong values as soon as these routes are connected. | `docs/build-plan/04f-api-tax.md:78`, `docs/build-plan/04f-api-tax.md:114`, `docs/build-plan/04f-api-tax.md:172`, `docs/build-plan/04f-api-tax.md:179`, `packages/core/src/zorivest_core/services/tax_service.py:71`, `packages/core/src/zorivest_core/services/tax_service.py:96`, `packages/core/src/zorivest_core/services/tax_service.py:147`, `packages/core/src/zorivest_core/services/tax_service.py:179` | Add contract-compatible service entry points or adapt the implementation to accept the planned DTO/body shapes, status/sort parameters, and lot close/reassign call forms before declaring the service layer complete. Add tests that call the service exactly as the planned API will call it. | open |
| 2 | High | `close_lot()` does not fulfill the close-lot contract. The plan says close should derive sale price, close date, closed quantity, and realized gain/loss from the sell trade; the API canon says the returned lot includes realized gain/loss. The implementation only sets `is_closed`, `close_date`, and per-share `proceeds`; it ignores `trade.action`, `trade.quantity`, account matching, partial-close/split behavior, `linked_trade_ids`, and realized gain/loss calculation. A buy trade with matching ticker could close a lot. | `docs/execution/plans/2026-05-12-tax-logic-expansion/implementation-plan.md:43`, `docs/build-plan/04f-api-tax.md:170`, `packages/core/src/zorivest_core/services/tax_service.py:118`, `packages/core/src/zorivest_core/services/tax_service.py:133`, `packages/core/src/zorivest_core/services/tax_service.py:138`, `packages/core/src/zorivest_core/domain/entities.py:213` | Validate the linked trade is a sell/cover for the same account/ticker, enforce quantity rules, record the linked trade, handle partial closes or explicitly reject them, and return/persist realized gain/loss according to the service/API contract. Add negative tests for non-sell trades, account mismatch, oversized quantity, and partial close behavior. | open |
| 3 | High | `reassign_basis()` is effectively a no-op. AC-125.4 says it changes the cost basis method within the T+1 window, but `TaxLot` has no per-lot basis-method field and the method parameter is never applied to any entity. The implementation updates and commits the unchanged lot, so every valid reassignment reports success while changing nothing. | `docs/execution/plans/2026-05-12-tax-logic-expansion/implementation-plan.md:44`, `packages/core/src/zorivest_core/services/tax_service.py:147`, `packages/core/src/zorivest_core/services/tax_service.py:174`, `packages/core/src/zorivest_core/domain/entities.py:199`, `packages/core/src/zorivest_core/domain/entities.py:250` | Decide the storage target for basis reassignment, such as a per-lot override, pending trade-lot match, or TaxProfile update, then persist it and test the before/after state with real persistence. If the current domain model cannot support it, mark the task blocked instead of complete. | open |
| 4 | High | `simulate_impact()` omits required wash-risk output and bypasses the specified TaxProfile source for tax rates. AC-126.4 and local canon require wash risk in the result, while the result dataclass only contains lot details, ST/LT totals, and estimated tax. The plan also classifies tax rate application as sourced from `TaxProfile.federal_bracket + state_tax_rate`, but the implementation takes ad hoc float parameters and never reads `tax_profiles`. | `docs/execution/plans/2026-05-12-tax-logic-expansion/implementation-plan.md:94`, `docs/execution/plans/2026-05-12-tax-logic-expansion/implementation-plan.md:106`, `docs/build-plan/03-service-layer.md:352`, `docs/build-plan/04f-api-tax.md:78`, `packages/core/src/zorivest_core/services/tax_service.py:48`, `packages/core/src/zorivest_core/services/tax_service.py:186`, `packages/core/src/zorivest_core/services/tax_service.py:265`, `packages/core/src/zorivest_core/domain/entities.py:244` | Include the wash-risk field/structure promised by the contract, source tax rates from TaxProfile or document a source-backed exception, and add unit/integration tests that fail if wash risk is absent or TaxProfile is ignored. | open |
| 5 | Medium | Test rigor is not strong enough to prove the service contract. `test_reassign_within_t1_succeeds` only checks that commit was called, so the no-op reassignment passes green. `test_close_lot_sets_fields` checks only three mutated fields and misses action/account/quantity/link/gain behavior. `test_simulate_estimated_tax` claims TaxProfile rates but supplies rates directly to the method. Lot selector coverage is mostly strong, but several MAX method tier fallbacks are not exhaustively covered across all four tiers. | `tests/unit/test_tax_service.py:139`, `tests/unit/test_tax_service.py:189`, `tests/unit/test_tax_service.py:268`, `tests/unit/test_lot_selector.py:300`, `tests/unit/test_lot_selector.py:365`, `tests/unit/test_lot_selector.py:414` | Strengthen tests before corrections: assert persisted state changes, call the service through canon-compatible shapes, verify all close-lot invalid paths, require TaxProfile-backed rates, and add missing 4-tier fallback cases for MLL/MSG/MSL. | open |
| 6 | Medium | Completion evidence and project state are inconsistent. The MEU gate reports advisory A3 because the handoff lacks required FAIL_TO_PASS and command evidence sections. The plan also says post-implementation should update BUILD_PLAN to yellow and add registry entries, but `docs/BUILD_PLAN.md` still marks MEU-125/126 as `⬜`, and the registry search found no matching entries. | `C:\Temp\zorivest\review-meu-gate.txt:19`, `.agent/context/handoffs/2026-05-12-tax-logic-expansion-handoff.md:32`, `docs/execution/plans/2026-05-12-tax-logic-expansion/implementation-plan.md:138`, `docs/BUILD_PLAN.md:616`, `docs/BUILD_PLAN.md:617` | Add the missing evidence sections or link to a walkthrough containing them, then reconcile BUILD_PLAN/registry status with the actual review outcome. If changes remain required, avoid marking the MEUs as complete. | open |

---

## Checklist Results

### Implementation Review (IR)

| Check | Result | Evidence |
|-------|--------|----------|
| IR-1 Live runtime evidence | pass with caveat | Real SQLite integration tests exist and were run: 8 integration tests included in the 72-test targeted run. They do not cover several broken service contracts above. |
| IR-2 Stub behavioral compliance | n/a | No stubs were modified in this implementation review scope. |
| IR-3 Error mapping completeness | n/a | No API route implementation was changed in this MEU; however, service signatures are incompatible with planned API calls. |
| IR-4 Fix generalization | fail | Contract mismatches appear across all four implemented TaxService methods, not one isolated call. |
| IR-5 Test rigor audit | fail | `test_lot_selector.py`: Strong/Adequate, missing some MAX-tier fallback breadth. `test_gains_calculator.py`: Strong. `test_tax_service.py`: Weak in reassignment/close/simulate contract assertions. `test_tax_service_integration.py`: Adequate, but not broad enough to catch close/reassign contract defects. |
| IR-6 Boundary validation coverage | n/a for implemented code | Plan says no external input surfaces in MEU-125/126. The issue is service/API contract compatibility rather than boundary schemas in this pass. |

### Documentation / Artifact Review (DR/PR)

| Check | Result | Evidence |
|-------|--------|----------|
| Scope correlation correct | pass | Handoff, task, reflection, and plan all use `2026-05-12-tax-logic-expansion` and MEU-125/126. |
| Handoff exists and is readable | pass | Seed handoff read successfully. |
| Commands independently runnable | pass | Targeted pytest, full pytest, pyright, ruff, and MEU gate reproduced. |
| Evidence bundle complete | fail | MEU gate A3 reports missing Evidence/FAIL_TO_PASS, Pass-fail/Commands, Commands/Codex Report. |
| Anti-placeholder scan clean | pass | MEU gate anti-placeholder and anti-deferral checks passed. |
| Shared status artifacts consistent | fail | Handoff/task say complete; BUILD_PLAN still shows MEU-125/126 as `⬜`; no registry match was found. |

---

## Open Questions / Assumptions

- I treated `docs/build-plan/04f-api-tax.md` and `docs/build-plan/03-service-layer.md` as local canon because the implementation plan cites them as sources for these methods.
- I did not review unrelated modified `ui/electron.vite.config.ts`; it appears outside the tax logic review scope.
- The lot selector's IBKR tier ordering was checked against the official IBKR Trader Workstation documentation and appears correct.

---

## Verdict

`changes_required` - blocking checks are green, but the core `TaxService` contract is not implemented correctly. The implementation currently passes because key tests assert thin behavior or direct internal signatures, while local canon and the plan require API-compatible service shapes, meaningful close/reassign behavior, wash-risk output, TaxProfile-backed rates, and stronger evidence.

### Required Follow-Up Actions

1. Route fixes through `/execution-corrections`; do not patch under this review workflow.
2. Start by correcting the `TaxService` external service contract shape and add tests that call it as the future API route will call it.
3. Make `close_lot`, `reassign_basis`, and `simulate_impact` behavior observable in persisted state or explicitly mark unsupported behavior as blocked.
4. Strengthen tests before implementation corrections so the current no-op and missing-output cases fail red.
5. Reconcile evidence and project status after code corrections pass.

---

## Recheck (2026-05-12)

**Workflow**: `/execution-critical-review` recheck  
**Agent**: GPT-5.5 Codex  
**Verdict**: `changes_required`

### Commands Executed

| Command | Result |
|---------|--------|
| `git status --short *> C:\Temp\zorivest\recheck-git-status.txt` | Corrections are present in tax/domain/infra/test files; unrelated `ui/electron.vite.config.ts` remains modified |
| `git diff --stat *> C:\Temp\zorivest\recheck-git-diff-stat.txt` | 8 tracked files changed; new tax service/domain tax files remain untracked |
| `rg -n "def close_lot|def reassign_basis|def simulate_impact|..." ... *> C:\Temp\zorivest\recheck-line-refs.txt` | Reconfirmed service signatures, local canon call sites, correction tests, and repository mappings |
| `uv run pytest tests/unit/test_tax_service.py tests/integration/test_tax_service_integration.py -x --tb=short -v *> C:\Temp\zorivest\recheck-target-taxsvc.txt` | 36 passed, 1 warning |
| `uv run pytest tests/ -x --tb=short *> C:\Temp\zorivest\recheck-full-pytest.txt` | 3126 passed, 23 skipped, 3 warnings |
| `uv run pyright packages/ *> C:\Temp\zorivest\recheck-pyright.txt` | 0 errors, 0 warnings |
| `uv run ruff check packages/ *> C:\Temp\zorivest\recheck-ruff.txt` | All checks passed |
| `uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\recheck-meu-gate.txt` | 8/8 blocking PASS; advisory A3 still reports missing Pass-fail/Commands and Commands/Codex Report |

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|--------------|----------------|
| F1: TaxService method signatures incompatible with local API/service canon | open | Partially fixed; still open |
| F2: `close_lot()` incomplete | open | Partially fixed; still open |
| F3: `reassign_basis()` no-op | open | Fixed |
| F4: `simulate_impact()` missing wash-risk output and TaxProfile rates | open | Fixed for current MEU scope |
| F5: Weak service tests | open | Partially fixed; still open through remaining F1/F2 test gaps |
| F6: Evidence/project state inconsistent | open | Partially fixed; still open as advisory evidence gap |

### Confirmed Fixes

- `reassign_basis()` now persists `lot.cost_basis_method = method` before update/commit, closing the no-op defect for the current entity model: `packages/core/src/zorivest_core/services/tax_service.py:188`, `packages/core/src/zorivest_core/services/tax_service.py:213`, `packages/core/src/zorivest_core/domain/entities.py:214`, `packages/infrastructure/src/zorivest_infra/database/models.py:879`, `packages/infrastructure/src/zorivest_infra/database/tax_repository.py:63`, `packages/infrastructure/src/zorivest_infra/database/tax_repository.py:197`.
- `close_lot()` now rejects non-`SLD` trades, rejects account mismatches, and records `sell_trade_id` in `linked_trade_ids`: `packages/core/src/zorivest_core/services/tax_service.py:153`, `packages/core/src/zorivest_core/services/tax_service.py:168`, `packages/core/src/zorivest_core/services/tax_service.py:178`.
- `simulate_impact()` now includes `SimulationResult.wash_risk`, checks selected lots for existing `wash_sale_adjustment`, and prefers current-year `TaxProfile` rates over explicit fallback rates: `packages/core/src/zorivest_core/services/tax_service.py:71`, `packages/core/src/zorivest_core/services/tax_service.py:262`, `packages/core/src/zorivest_core/services/tax_service.py:312`, `packages/core/src/zorivest_core/services/tax_service.py:316`, `packages/core/src/zorivest_core/services/tax_service.py:331`.
- New correction tests increased `test_tax_service.py` from 16 to 28 tests; the targeted service/integration command now reports 36 passed.

### Remaining Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| R1 | High | F1 remains partially open. `get_lots()` now accepts `status` and `sort_by`, but the service still does not support the local API canon call shapes for the other planned methods: `service.simulate_impact(body)`, `service.close_lot(lot_id)`, and `service.reassign_basis(lot_id, body)`. The current implementation still requires expanded positional inputs for simulation, a required `sell_trade_id` for close, and a raw `CostBasisMethod` for reassign. | `docs/build-plan/04f-api-tax.md:79`, `docs/build-plan/04f-api-tax.md:172`, `docs/build-plan/04f-api-tax.md:179`, `packages/core/src/zorivest_core/services/tax_service.py:118`, `packages/core/src/zorivest_core/services/tax_service.py:188`, `packages/core/src/zorivest_core/services/tax_service.py:220` | Add canon-compatible adapter methods or broaden these methods to accept the planned body/request shapes. Add tests that call the service exactly as `04f-api-tax.md` calls it. | open |
| R2 | High | F2 remains partially open. `close_lot()` now validates action/account and records a link, but still ignores `trade.quantity`, has no partial-close or oversize-quantity behavior, and does not return or persist any realized gain/loss field despite the close-lot contract saying the response includes realized gain/loss. The new `test_close_lot_computes_realized_gain` still only asserts per-share `proceeds` and `is_closed`, so it would pass without any realized-gain calculation. | `docs/execution/plans/2026-05-12-tax-logic-expansion/implementation-plan.md:43`, `docs/build-plan/04f-api-tax.md:170`, `packages/core/src/zorivest_core/services/tax_service.py:118`, `packages/core/src/zorivest_core/services/tax_service.py:174`, `tests/unit/test_tax_service.py:384` | Define and implement quantity semantics: exact close, partial split, or explicit rejection. Add negative tests for trade quantity smaller/larger than lot quantity and a real assertion for realized gain/loss output or documented unsupported status. | open |
| R3 | Medium | F6 remains partially open. The handoff now has FAIL_TO_PASS evidence and updated counts, and BUILD_PLAN rows were changed, but the MEU gate still reports evidence advisory A3: missing Pass-fail/Commands and Commands/Codex Report. | `.agent/context/handoffs/2026-05-12-tax-logic-expansion-handoff.md:88`, `C:\Temp\zorivest\recheck-meu-gate.txt:19` | Add the exact sections expected by the evidence bundle validator or link a compliant walkthrough. | open |

### Checklist Results

| Check | Result | Evidence |
|-------|--------|----------|
| IR-1 Live runtime evidence | pass with caveat | Service integration tests still run against real SQLite and pass, but they do not cover R1/R2 call-shape and quantity semantics. |
| IR-4 Fix generalization | fail | Corrections fixed several direct instances but did not generalize to all prior TaxService contract mismatch surfaces. |
| IR-5 Test rigor audit | fail | New tests improved coverage, but R1 lacks canon-call-shape tests and R2’s realized-gain test still asserts only `proceeds`/closed state. |
| PR evidence quality | fail | MEU gate A3 still reports evidence-bundle omissions. |

### Verdict

`changes_required` - the correction pass improved the implementation and all blocking gates are green, but two high-severity contract findings remain open: service methods still do not match local canon call shapes, and `close_lot()` still lacks quantity/partial-close and realized-gain semantics. A smaller evidence-bundle advisory also remains.

---

## Recheck (2026-05-12 Round 2)

**Workflow**: `/execution-critical-review` recheck  
**Agent**: GPT-5.5 Codex  
**Verdict**: `changes_required`

### Commands Executed

| Command | Result |
|---------|--------|
| `git status --short *> C:\Temp\zorivest\recheck2-git-status.txt` | Tax implementation/review files are still uncommitted; unrelated workflow/UI edits remain in the working tree |
| `git diff --stat *> C:\Temp\zorivest\recheck2-git-diff-stat.txt` | 14 tracked files changed; new tax service/domain/test/review files remain untracked |
| `rg -n "...partial close..." ... *> C:\Temp\zorivest\recheck2-final-line-refs.txt` | Reconfirmed the remaining partial-close contract mismatch and evidence advisory line |
| `uv run pytest tests/unit/test_tax_service.py tests/unit/test_tax_entities.py tests/integration/test_tax_service_integration.py -x --tb=short -v *> C:\Temp\zorivest\recheck2-target-tax.txt` | 60 passed, 1 warning |
| `uv run pytest tests/ -x --tb=short *> C:\Temp\zorivest\recheck2-full-pytest.txt` | 3133 passed, 23 skipped, 3 warnings |
| `uv run pyright packages/ *> C:\Temp\zorivest\recheck2-pyright.txt` | 0 errors, 0 warnings |
| `uv run ruff check packages/ *> C:\Temp\zorivest\recheck2-ruff.txt` | All checks passed |
| `uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\recheck2-meu-gate.txt` | 8/8 blocking PASS; advisory A3 still reports missing Commands/Codex Report |

### Prior Recheck Summary

| Finding | Previous Status | Round 2 Result |
|---------|-----------------|----------------|
| R1: TaxService canon call shapes | open | Mostly fixed for current MEU scope; `close_lot(lot_id)` now works, while API DTO/body adapters remain future MEU-148 concerns because the plan marks external boundaries/API routes out of scope |
| R2: `close_lot()` quantity and realized gain semantics | open | Partially fixed; exact-close quantity validation and realized gain/loss are implemented, but partial-close split behavior remains missing |
| R3: Evidence bundle naming | open | Partially fixed; only `Commands/Codex Report` remains as a MEU-gate advisory |

### Confirmed Fixes Since Prior Recheck

- `close_lot()` now accepts `sell_trade_id: str | None = None`, supports `close_lot(lot_id)` auto-discovery through `trades.list_for_account()`, and has tests for success, no-match failure, and explicit sell-trade behavior: `packages/core/src/zorivest_core/services/tax_service.py:118`, `packages/core/src/zorivest_core/services/tax_service.py:160`, `tests/unit/test_tax_service.py:617`.
- `TaxLot.realized_gain_loss` is now modeled and persisted through entity, ORM model, and repository mapper/update paths: `packages/core/src/zorivest_core/domain/entities.py:215`, `packages/infrastructure/src/zorivest_infra/database/models.py:880`, `packages/infrastructure/src/zorivest_infra/database/tax_repository.py:64`, `packages/infrastructure/src/zorivest_infra/database/tax_repository.py:199`.
- `close_lot()` now rejects quantity mismatches and computes realized gain/loss for exact closes, with positive and negative realized-gain tests: `packages/core/src/zorivest_core/services/tax_service.py:193`, `packages/core/src/zorivest_core/services/tax_service.py:216`, `tests/unit/test_tax_service.py:577`, `tests/unit/test_tax_service.py:610`.
- The handoff now includes `FAIL_TO_PASS Evidence`, `Commands Executed`, and a `Pass/fail matrix`; the MEU gate only flags the remaining `Commands/Codex Report` label.

### Remaining Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| RR2-1 | High | Partial-close behavior is still contrary to the approved plan. The implementation and test suite now explicitly reject `trade.quantity < lot.quantity`, but the implementation plan classifies partial close as `Spec` and says it creates a split lot. This means a normal sale that closes only part of a purchase lot cannot be represented by `close_lot()`, even though the planned contract requires it. | `docs/execution/plans/2026-05-12-tax-logic-expansion/implementation-plan.md:67`, `packages/core/src/zorivest_core/services/tax_service.py:193`, `packages/core/src/zorivest_core/services/tax_service.py:198`, `tests/unit/test_tax_service.py:566` | Replace the rejection with split-lot behavior: close the sold quantity with proceeds/realized gain/linkage, leave the remaining quantity in an open lot with inherited basis/open date/wash adjustment, and add unit plus real-SQLite integration tests for the round trip. If product intentionally rejects partial closes, update the plan through a correction decision before approval. | open |
| RR2-2 | Medium | Evidence is close but still not fully compliant with the repository validator. The MEU gate is green on all blocking checks, but advisory A3 still reports the handoff is missing `Commands/Codex Report`. | `C:\Temp\zorivest\recheck2-meu-gate.txt:18` | Add the exact `Commands/Codex Report` section or adjust the evidence validator only if the new handoff format is intentionally canonical. | open |

### Checklist Results

| Check | Result | Evidence |
|-------|--------|----------|
| IR-1 Live runtime evidence | pass with caveat | Real SQLite tax service integration tests ran and passed: 8 integration tests included in the 60-test targeted command. |
| IR-4 Fix generalization | fail | Exact-close and realized-gain semantics were fixed, but the plan-required partial-close case remains unimplemented. |
| IR-5 Test rigor audit | fail | New tests assert realized gains and quantity errors, but `test_close_lot_rejects_partial_close` encodes behavior that contradicts the approved plan. |
| Evidence quality | advisory fail | MEU gate A3 flags only `Commands/Codex Report`; all blocking checks pass. |

### Verdict

`changes_required` - the implementation is materially improved and the blocking gates are clean, but approval is still blocked by the partial-close split requirement in the approved plan. The remaining evidence issue is advisory, not the primary blocker.

---

## Corrections Applied (2026-05-12 Round 3)

**Workflow**: `/execution-corrections`
**Agent**: Antigravity (Gemini)
**Verdict**: `corrections_applied`

### Findings Addressed

| # | Severity | Finding | Resolution |
|---|----------|---------|------------|
| RR2-1 | High | Partial-close rejection contradicts plan spec (line 67: "Creates split lot") | Implemented split-lot behavior: partial close creates a remainder lot with inherited basis/dates, closes the sold portion with realized gain |
| RR2-2 | Medium | Evidence handoff missing `Commands run` section → MEU gate A3 advisory | Added `### Commands run` section matching validator regex pattern |

### Changes Made

**`packages/core/src/zorivest_core/services/tax_service.py`**:
- Replaced `trade.quantity != lot.quantity` rejection with branching logic:
  - `trade.quantity > lot.quantity` → reject (oversize)
  - `trade.quantity < lot.quantity` → create remainder lot (`{lot_id}-R`), close sold portion
  - `trade.quantity == lot.quantity` → exact close (unchanged)
- Remainder lot inherits `account_id`, `ticker`, `open_date`, `cost_basis`, `wash_sale_adjustment`
- Original lot narrowed to sold quantity before close
- Moved `TaxLot` import from TYPE_CHECKING to runtime (needed for constructing remainder)

**`tests/unit/test_tax_service.py`**:
- Removed `test_close_lot_rejects_partial_close` (contradicted plan spec)
- Added 3 new split-lot tests:
  - `test_close_lot_partial_close_creates_remainder` — verifies split creation and remainder qty
  - `test_close_lot_partial_close_remainder_inherits_basis` — verifies basis/date/wash inheritance
  - `test_close_lot_partial_close_realized_gain_on_sold_portion` — gain computed on sold qty only

**`.agent/context/handoffs/2026-05-12-tax-logic-expansion-handoff.md`**:
- Added `### Commands run` section (validator A3 compliance)
- Updated test counts and regression totals

### Verification Results

| Check | Result |
|-------|--------|
| Red phase | 1 FAILED (BusinessRuleError: Partial closes not supported) |
| Green phase | 54 passed (unit), 8 passed (integration) |
| Full regression | 3135 passed, 23 skipped, 0 failed |
| pyright | 0 errors, 0 warnings |
| ruff | All checks passed |
| MEU gate | 8/8 blocking PASS, A3 evidence: "All evidence fields present" |

### TDD Evidence

```
# Red phase:
FAILED test_close_lot_partial_close_creates_remainder - BusinessRuleError: Partial closes are not supported.

# Green phase (after split-lot implementation):
54 passed, 0 failed (unit)
8 passed, 0 failed (integration)
3135 passed, 23 skipped (full regression)
```

---

## Recheck (2026-05-12 Round 3)

**Workflow**: `/execution-critical-review` recheck  
**Agent**: GPT-5.5 Codex  
**Verdict**: `changes_required`

### Commands Executed

| Command | Result |
|---------|--------|
| `git status --short *> C:\Temp\zorivest\recheck3-git-status.txt` | Tax implementation/review files remain uncommitted; unrelated workflow/UI edits remain in the working tree |
| `git diff --stat *> C:\Temp\zorivest\recheck3-git-diff-stat.txt` | 14 tracked files changed; new tax service/domain/test/review files remain untracked |
| `rg -n "partial_close|partial close|split lot|tax_lots\.save|Commands run|Commands/Codex Report|All evidence fields present|MEU gate" ... *> C:\Temp\zorivest\recheck3-line-refs.txt` | Confirmed split-lot unit tests and handoff evidence section; no split-lot integration test found |
| `uv run pytest tests/unit/test_tax_service.py tests/unit/test_tax_entities.py tests/integration/test_tax_service_integration.py -x --tb=short -v *> C:\Temp\zorivest\recheck3-target-tax.txt` | 62 passed, 1 warning |
| `uv run pytest tests/ -x --tb=short *> C:\Temp\zorivest\recheck3-full-pytest.txt` | 3135 passed, 23 skipped, 3 warnings |
| `uv run pyright packages/ *> C:\Temp\zorivest\recheck3-pyright.txt` | 0 errors, 0 warnings |
| `uv run ruff check packages/ *> C:\Temp\zorivest\recheck3-ruff.txt` | All checks passed |
| `uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\recheck3-meu-gate.txt` | 8/8 blocking PASS; A3 reports all evidence fields present |

### Prior Recheck Summary

| Finding | Previous Status | Round 3 Result |
|---------|-----------------|----------------|
| RR2-1: Partial-close split behavior missing | open | Functionally corrected in service code and mocked unit tests; integration coverage still missing |
| RR2-2: Evidence missing `Commands/Codex Report` | open | Fixed; MEU gate A3 now reports all evidence fields present |

### Confirmed Fixes Since Round 2

- `close_lot()` now branches on quantity: oversize rejects, partial close creates a remainder lot, and exact close keeps the prior path: `packages/core/src/zorivest_core/services/tax_service.py:193`, `packages/core/src/zorivest_core/services/tax_service.py:205`, `packages/core/src/zorivest_core/services/tax_service.py:217`.
- New unit tests assert the split result, inherited remainder basis/date/wash adjustment, and realized gain on only the sold quantity: `tests/unit/test_tax_service.py:566`, `tests/unit/test_tax_service.py:591`, `tests/unit/test_tax_service.py:611`.
- The handoff now has `### Commands run`, and the reproduced MEU gate reports `Evidence Bundle: All evidence fields present in 2026-05-12-tax-logic-expansion-handoff.md`.

### Remaining Finding

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| RR3-1 | Medium | The split-lot correction is not covered by a real SQLite integration test. The service now calls `tax_lots.save(remainder_lot)` and then updates the sold lot, but the only tests for this behavior use a mocked UoW. `test_tax_service_integration.py` still covers exact close only, so it would not catch mapper/schema/session failures in the newly added persistence path. This is the integration half of the Round 2 recommendation still missing. | `packages/core/src/zorivest_core/services/tax_service.py:205`, `packages/core/src/zorivest_core/services/tax_service.py:217`, `tests/unit/test_tax_service.py:566`, `tests/integration/test_tax_service_integration.py:121` | Add a real SQLite integration test that closes part of a persisted lot, then reopens the UoW and asserts: sold lot is closed with sold quantity and realized gain, remainder lot exists with leftover quantity and inherited basis/open date/wash adjustment, and total quantity is conserved. | open |

### Checklist Results

| Check | Result | Evidence |
|-------|--------|----------|
| IR-1 Live runtime evidence | fail for new persistence path | Existing integration tests run and pass, but none exercise the new partial-close save/update transaction. |
| IR-4 Fix generalization | pass with caveat | The code generalizes the prior quantity handling defect to oversize/exact/partial branches. |
| IR-5 Test rigor audit | fail | Unit assertions are specific and meaningful, but the persistence-sensitive split path lacks real integration coverage. |
| Evidence quality | pass | MEU gate A3 now reports all evidence fields present. |

### Verdict

`changes_required` - the high-severity partial-close implementation blocker is fixed and all blocking gates are green, but review approval is still held by missing real SQLite coverage for the new split-lot persistence path.

---

## Corrections Applied (2026-05-12 Round 4)

**Workflow**: `/execution-corrections`
**Agent**: Antigravity (Gemini)
**Verdict**: `corrections_applied`

### Findings Addressed

| # | Severity | Finding | Resolution |
|---|----------|---------|------------|
| RR3-1 | Medium | Split-lot persistence path lacks real SQLite integration test | Added `test_close_lot_partial_close_roundtrip`: seeds 100-share lot + 40-share sell, verifies sold lot (qty=40, gain=1860 with wash-sale adjustment), remainder lot (qty=60, inherited basis/dates/wash), and quantity conservation |

### Changes Made

**`tests/integration/test_tax_service_integration.py`**:
- Added `test_close_lot_partial_close_roundtrip` to `TestCloseLotIntegration`
- Test seeds its own data (no shared fixture dependency) with `wash_sale_adjustment=3.50`
- Initial run surfaced that gain formula accounts for wash-sale adjustment: `(250 - 203.50) * 40 = 1860` not `2000`
- Verifies 11 assertions across sold lot (closed, qty, gain, close_date) and remainder lot (open, qty, cost_basis, open_date, wash_sale_adjustment, account_id, ticker)
- Asserts quantity conservation: `sold.quantity + remainder.quantity == 100.0`

### Verification Results

| Check | Result |
|-------|--------|
| Integration tests | 9 passed (was 8) |
| Full regression | 3136 passed, 23 skipped, 0 failed |
| pyright | 0 errors, 0 warnings |
| ruff | All checks passed |
| MEU gate | 8/8 blocking PASS, A3 evidence present |

### Bonus Finding

The integration test surfaced that the unit test `test_close_lot_partial_close_realized_gain_on_sold_portion` had `wash_sale_adjustment=0` (via the `_lot()` helper), so it didn't exercise the wash-sale-adjusted gain path. The integration test with `wash_sale_adjustment=3.50` correctly validated the full domain formula, demonstrating the value of real persistence testing over mocked UoW.
