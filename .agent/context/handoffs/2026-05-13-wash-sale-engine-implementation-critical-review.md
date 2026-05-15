---
date: "2026-05-13"
review_mode: "handoff"
target_plan: "docs/execution/plans/2026-05-13-wash-sale-engine/implementation-plan.md"
verdict: "approved"
findings_count: 0
template_version: "2.1"
requested_verbosity: "standard"
agent: "codex"
---

# Critical Review: 2026-05-13-wash-sale-engine

> **Review Mode**: `handoff`
> **Verdict**: `approved`

---

## Scope

**Target**: `.agent/context/handoffs/2026-05-13-wash-sale-engine-handoff.md`
**Correlated Plan**: `docs/execution/plans/2026-05-13-wash-sale-engine/`
**Review Type**: implementation handoff review
**Checklist Applied**: execution critical review IR checklist, reviewer adversarial checklist, IR-5 test rigor audit

Correlation rationale: the user supplied the work handoff and execution-critical-review workflow directly. The handoff frontmatter points to `docs/execution/plans/2026-05-13-wash-sale-engine/implementation-plan.md`, and `task.md` is for MEU-130/131/132 with the same slug/date. No sibling work handoffs were found for this plan folder; the supplied handoff is the seed and full work handoff set.

---

## Commands Executed

| Command | Result | Evidence |
|---------|--------|----------|
| `git status --short` | PASS | Receipt: `C:\Temp\zorivest\git-status-review.txt`; wash-sale implementation files are modified/untracked as expected. |
| `git diff -- <claimed files>` | PASS | Receipt: `C:\Temp\zorivest\git-diff-review.txt`; claimed docs/source/test changes are present. |
| `uv run pytest tests/unit/domain/tax/test_wash_sale.py tests/unit/domain/tax/test_wash_sale_detector.py tests/unit/domain/tax/test_wash_sale_chain_manager.py tests/unit/domain/tax/test_wash_sale_cross_account.py tests/unit/services/test_tax_service_wash_sale.py tests/unit/infrastructure/test_wash_sale_repository.py -q` | PASS with skip | `50 passed, 1 skipped, 1 warning`. |
| `uv run python tools/validate_codebase.py --scope meu` | PASS | `8/8` blocking checks passed. |
| `rg -n "TODO\|FIXME\|NotImplementedError\|pass # placeholder\|pass  # placeholder\|@pytest.mark.skip\|xfail\|pytest.skip" <wash-sale scope>` | WARN | One in-scope skip at `tests/unit/infrastructure/test_wash_sale_repository.py:95`. |
| `rg -n "SqlWashSaleChainRepository\|wash_sale_chains\|detect_and_apply_wash_sales\|scan_cross_account_wash_sales\|destroy_chain\|LOSS_DESTROYED\|pytest.skip" tests packages/...` | PASS | Confirmed no stronger service/repository behavior tests elsewhere. |

---

## Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 1 | High | `detect_and_apply_wash_sales()` over-adjusts basis when one loss lot has multiple replacement lots. It sums all match losses into one chain, then calls `absorb_loss(chain, repl_lot)` for each replacement. Since `absorb_loss()` applies `chain.disallowed_amount`, every replacement receives the total disallowed loss instead of its own `match.disallowed_loss`. | `packages/core/src/zorivest_core/services/tax_service.py:616`, `packages/core/src/zorivest_core/services/tax_service.py:626`, `packages/core/src/zorivest_core/domain/tax/wash_sale_chain_manager.py:66` | Add a failing service/manager test with two replacement lots and assert per-lot basis adjustments. Pass the per-match disallowed amount into the basis-adjustment path or model per-replacement entries explicitly. | open |
| 2 | High | IRA permanent-loss destruction is not wired into detection/service flow. `scan_cross_account_wash_sales()` only returns `WashSaleMatch` values; it does not inspect replacement account type, create a chain, call `destroy_chain()`, persist a `DESTROYED` chain, or emit `LOSS_DESTROYED` provenance. The handoff claims AC-132.2/132.3 as complete. | `packages/core/src/zorivest_core/services/tax_service.py:649`, `tests/unit/domain/tax/test_wash_sale_cross_account.py:91` | Implement and test the actual taxable-to-IRA service path: replacement account lookup, `DESTROYED` chain creation, no basis adjustment, repository save, and persisted entry account provenance. | open |
| 3 | High | `destroy_chain()` does not prevent later absorption. `absorb_loss()` has no status guard, and the test named `test_cannot_absorb_after_destroy` never calls `absorb_loss()`; its comment says absorb should still work at manager level, contradicting AC-132.3 and the handoff claim that destroy prevents absorb. | `packages/core/src/zorivest_core/domain/tax/wash_sale_chain_manager.py:66`, `tests/unit/domain/tax/test_wash_sale_cross_account.py:116` | Add a real negative test that calls `absorb_loss()` after `destroy_chain()` and expects a domain error, then guard `absorb_loss()` against `DESTROYED` and `RELEASED` chains. | open |
| 4 | Medium | Release entries violate the entry-provenance contract. `release_chain()` creates `LOSS_RELEASED` entries with `account_id=""`, so not every `WashSaleEntry` identifies the account that triggered the event. The AC-132.6 tests cover loss and absorb entries only. | `packages/core/src/zorivest_core/domain/tax/wash_sale_chain_manager.py:112`, `packages/core/src/zorivest_core/domain/tax/wash_sale_chain_manager.py:141` | Require account provenance in `release_chain()` parameters or resolve it in the service before appending the entry; add a test asserting non-empty release entry account ID. | open |
| 5 | Medium | Test rigor does not support several completion claims. The handoff labels TaxService tests as integration coverage, but they only assert method existence/signature. The repository "CRUD" suite uses introspection and skips the only DB behavior test, with no replacement integration test found by reference sweep. | `tests/unit/services/test_tax_service_wash_sale.py:15`, `tests/unit/services/test_tax_service_wash_sale.py:29`, `tests/unit/infrastructure/test_wash_sale_repository.py:92`, `tests/unit/infrastructure/test_wash_sale_repository.py:95` | Add behavior tests for service orchestration and real repository save/get/update/list round trips. Until then, downgrade the handoff claims or leave the MEU incomplete. | open |

---

## Checklist Results

### Implementation Review (IR)

| Check | Result | Evidence |
|-------|--------|----------|
| IR-1 Live runtime evidence | FAIL | No real repository CRUD round-trip test exists for `SqlWashSaleChainRepository`; the only DB behavior test is skipped at `tests/unit/infrastructure/test_wash_sale_repository.py:95`. |
| IR-2 Stub behavioral compliance | N/A | This MEU does not add or modify API stubs. |
| IR-3 Error mapping completeness | N/A | No REST/API write routes are in scope. |
| IR-4 Fix generalization | WARN | Multiple status-transition paths were added, but only release has a status guard; destroy/absorb transition parity was not covered. |
| IR-5 Test rigor audit | FAIL | Two in-scope test files are weak, and one negative test is misleading. Ratings below. |
| IR-6 Boundary validation coverage | N/A | No external REST/MCP/UI/file/env write boundary is introduced in this domain/infrastructure MEU. |

### IR-5 Test Rigor Ratings

| Test File | Rating | Rationale |
|-----------|--------|-----------|
| `tests/unit/domain/tax/test_wash_sale.py` | Adequate | Specific enum/entity assertions, but field-count comments drift from the implemented `loss_open_date` field. |
| `tests/unit/domain/tax/test_wash_sale_detector.py` | Adequate | Good window/ticker/quantity coverage; partial tests should also assert `disallowed_loss` values. |
| `tests/unit/domain/tax/test_wash_sale_chain_manager.py` | Adequate | Exercises main lifecycle but misses invalid absorb states and release provenance. |
| `tests/unit/domain/tax/test_wash_sale_cross_account.py` | Weak | IRA tests manually call `destroy_chain()` instead of testing detection/service behavior; `test_cannot_absorb_after_destroy` does not test the claimed rejection. |
| `tests/unit/services/test_tax_service_wash_sale.py` | Weak | Method existence/signature checks only; no orchestration behavior or persistence assertions. |
| `tests/unit/infrastructure/test_wash_sale_repository.py` | Weak | Introspection-only repository checks; only behavior test is skipped. |

### Reviewer Adversarial Checklist

| Check | Result | Evidence |
|-------|--------|----------|
| AV-1 Failing-then-passing proof | WARN | Handoff has a FAIL_TO_PASS table, but the red outputs are summarized rather than preserved with failing test names. |
| AV-2 No bypass hacks | FAIL | `test_cannot_absorb_after_destroy` is a bypassed negative test: it asserts pre-state instead of executing the prohibited operation. |
| AV-3 Changed paths exercised by assertions | FAIL | `TaxService.detect_and_apply_wash_sales()`, `scan_cross_account_wash_sales()`, and repository CRUD behavior are not meaningfully asserted. |
| AV-4 No skipped/xfail masking | FAIL | In-scope repository behavior test is skipped. |
| AV-5 No unresolved placeholders | PASS | Placeholder/deferral sweep found no product placeholders in wash-sale scope. |
| AV-6 Source-backed criteria | WARN | K401 is correctly blocked, but enum comments still mention IRA/401k destruction while K401 is explicitly deferred. |

### Evidence and Claim Audit

| Check | Result | Evidence |
|-------|--------|----------|
| Claimed files present | PASS | Source/test files listed in the handoff exist in the working tree. |
| Claimed quality gates reproducible | PASS | Wash-sale slice passed; MEU gate passed. |
| Handoff claim accuracy | FAIL | "TaxService integration tests" and "SqlWashSaleChainRepository CRUD" claims are stronger than the actual tests. |
| Documentation/build-plan scope | PASS | `docs/BUILD_PLAN.md` marks MEU-130/131/132 complete; docs are not the blocking issue. |

---

## Verdict

`changes_required` — Blocking behavioral gaps remain in multi-replacement basis allocation, IRA destruction integration, destroyed-chain transition safety, and test rigor. Green tests and the MEU gate are reproducible, but the tests do not currently prove several handoff ACs.

---

## Follow-Up Actions

1. Use `/execution-corrections` for this same plan folder.
2. Add failing tests before fixes for findings 1-4.
3. Replace weak method-existence and repository-introspection tests with behavior assertions.
4. Re-run the wash-sale test slice and `uv run python tools/validate_codebase.py --scope meu`.
5. Re-submit this same canonical review file for recheck rather than creating a new variant.

---

## Recheck (2026-05-13)

**Workflow**: `/execution-critical-review` recheck
**Agent**: codex

### Commands Executed

| Command | Result | Evidence |
|---------|--------|----------|
| `uv run pytest tests/unit/domain/tax/test_wash_sale.py tests/unit/domain/tax/test_wash_sale_detector.py tests/unit/domain/tax/test_wash_sale_chain_manager.py tests/unit/domain/tax/test_wash_sale_cross_account.py tests/unit/services/test_tax_service_wash_sale.py tests/unit/infrastructure/test_wash_sale_repository.py tests/integration/test_wash_sale_repo_integration.py -q` | PASS | `68 passed, 1 warning` |
| `uv run python tools/validate_codebase.py --scope meu` | PASS | `8/8` blocking checks passed |
| `rg -n "TODO|FIXME|NotImplementedError|pass # placeholder|pass  # placeholder|@pytest.mark.skip|xfail|pytest.skip" <wash-sale scope>` | PASS | no matches in wash-sale source/tests |
| `rg -n 'AccountType\.IRA|is_tax_advantaged|DESTROYED|destroy_chain|LOSS_DESTROYED' <tax service + wash-sale artifacts>` | FAIL | no TaxService IRA destruction or `destroy_chain()` service path found |

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|--------------|----------------|
| C1: multi-replacement basis over-allocation | open | Fixed. `TaxService.detect_and_apply_wash_sales()` now passes `amount=match.disallowed_loss`; manager/service tests assert per-match allocation. |
| C2: IRA destruction not wired into service flow | open | Still open. `scan_cross_account_wash_sales()` still only returns matches and does not create/persist a `DESTROYED` chain. |
| C3: destroyed chain can still be absorbed | open | Fixed. `absorb_loss()` now rejects `DESTROYED` and `RELEASED`; tests execute the prohibited absorb calls. |
| C4: release entry provenance empty | open | Fixed for explicit callers. `release_chain()` accepts `account_id`, and a test asserts non-empty release provenance. |
| C5: weak service/repository tests | open | Fixed for C1/C3/C4 and repository CRUD. Service tests are materially stronger, and repository CRUD has integration round-trip coverage. |

### Confirmed Fixes

- C1 fixed: `packages/core/src/zorivest_core/services/tax_service.py:627` passes per-match disallowed loss into `absorb_loss()`, with assertions in `tests/unit/services/test_tax_service_wash_sale.py:137` and `tests/unit/domain/tax/test_wash_sale_chain_manager.py:269`.
- C3 fixed: `packages/core/src/zorivest_core/domain/tax/wash_sale_chain_manager.py:66` rejects invalid absorb states, with negative tests at `tests/unit/domain/tax/test_wash_sale_cross_account.py:114`.
- C4 fixed for explicit release callers: `packages/core/src/zorivest_core/domain/tax/wash_sale_chain_manager.py:127` accepts `account_id`, with a provenance test at `tests/unit/domain/tax/test_wash_sale_chain_manager.py:242`.
- C5 fixed for repository runtime evidence: `tests/integration/test_wash_sale_repo_integration.py:1` adds real save/get/update/list round-trip coverage; the targeted wash-sale suite now reports `68 passed`.

### Remaining Findings

| # | Severity | Finding | File:Line | Required Action | Status |
|---|----------|---------|-----------|-----------------|--------|
| 1 | High | IRA permanent-loss destruction remains unwired in the service path. The plan requires `AccountType.IRA` replacement purchases to produce a `DESTROYED` chain with `LOSS_DESTROYED` entry, but `scan_cross_account_wash_sales()` still only returns `WashSaleMatch` objects and never looks up account type, calls `destroy_chain()`, or persists a destroyed chain. The correction handoff claims C2 was fixed by validating existing scan behavior, but that does not satisfy AC-132.3. | `docs/execution/plans/2026-05-13-wash-sale-engine/implementation-plan.md:130`, `packages/core/src/zorivest_core/services/tax_service.py:651`, `tests/unit/services/test_tax_service_wash_sale.py:258` | Add a failing TaxService test for taxable loss + IRA replacement that asserts a persisted `WashSaleChain(status=DESTROYED)` with a `LOSS_DESTROYED` entry and no replacement basis adjustment; then wire account lookup and `destroy_chain()` into the service path. | open |

### Verdict

`changes_required` - the correction pass closed the allocation, invalid-transition, provenance, and repository-evidence findings, and validation is green. Approval is still blocked by the missing IRA destruction service behavior for AC-132.3.

---

## Corrections Applied (2026-05-13)

**Workflow**: `/execution-corrections`
**Agent**: opus

### Finding Resolved

| # | Severity | Finding | Fix | Verified |
|---|----------|---------|-----|----------|
| 1 | High | IRA permanent-loss destruction not wired in `scan_cross_account_wash_sales()` — method returned matches without inspecting replacement account type, creating chains, or calling `destroy_chain()` | Wired account lookup + IRA routing into `scan_cross_account_wash_sales()`. Each match now: (1) looks up replacement account via `accounts.get()`, (2) if `is_tax_advantaged` → `start_chain()` + `destroy_chain()` (no basis adjustment), (3) if taxable → `start_chain()` + `absorb_loss()` + `tax_lots.update()`. Per-match chain creation with `commit()` after all matches. | ✅ 3 new tests pass |

### TDD Evidence

**Red phase**: `test_ira_replacement_creates_destroyed_chain` failed — `wash_sale_chains.save` called 0 times (service returned matches without chain creation).

**Green phase**: All 3 new tests pass after service wiring:
- `test_ira_replacement_creates_destroyed_chain` — DESTROYED chain, LOSS_DESTROYED entry, no `tax_lots.update`
- `test_taxable_replacement_creates_absorbed_chain` — ABSORBED chain, BASIS_ADJUSTED entry, `tax_lots.update` called
- `test_mixed_ira_and_taxable_replacements` — 2 chains (1 DESTROYED + 1 ABSORBED), only taxable gets basis update

### Changed Files

```diff
# packages/core/src/zorivest_core/services/tax_service.py (L651-740)
- scan_cross_account_wash_sales() returns matches only
+ Now inspects replacement account type per match:
+   IRA → start_chain() + destroy_chain() (no basis adjustment)
+   Taxable → start_chain() + absorb_loss() + tax_lots.update()
+ Commits once after all matches processed

# tests/unit/services/test_tax_service_wash_sale.py
+ _mock_uow() now wires accounts.get() side_effect from account list
+ test_ira_replacement_creates_destroyed_chain (AC-132.3)
+ test_taxable_replacement_creates_absorbed_chain (cross-account taxable)
+ test_mixed_ira_and_taxable_replacements (boundary: IRA + taxable)
```

### Quality Gates

| Gate | Result |
|------|--------|
| Wash sale test suite | 71 passed |
| Full regression | 3276 passed, 23 skipped, 0 failed |
| Pyright (touched files) | 0 errors |
| Ruff (touched files) | All checks passed |
| Cross-doc sweep | 15 references checked, 0 stale |

### Verdict

`corrections_applied` — The single remaining finding (IRA destruction service wiring) is now resolved. AC-132.3 is satisfied: `scan_cross_account_wash_sales()` inspects replacement account type and routes IRA replacements to `destroy_chain()` (permanently non-deductible) while taxable replacements get standard `absorb_loss()` treatment. Ready for `/execution-critical-review` recheck.

---

## Recheck (2026-05-13, Pass 2)

**Workflow**: `/execution-critical-review` recheck
**Agent**: codex

### Commands Executed

| Command | Result | Evidence |
|---------|--------|----------|
| `git status --short` | PASS | Receipt: `C:\Temp\zorivest\recheck2-git-status.txt`; wash-sale correction files and this review file are modified as expected. |
| `rg` reference sweep over wash-sale scope | PASS | Receipt: `C:\Temp\zorivest\recheck2-reference-sweep.txt`; confirmed the service now calls `destroy_chain()` and tests assert IRA destruction behavior. |
| `uv run pytest tests/unit/domain/tax/test_wash_sale.py tests/unit/domain/tax/test_wash_sale_detector.py tests/unit/domain/tax/test_wash_sale_chain_manager.py tests/unit/domain/tax/test_wash_sale_cross_account.py tests/unit/services/test_tax_service_wash_sale.py tests/unit/infrastructure/test_wash_sale_repository.py tests/integration/test_wash_sale_repo_integration.py -q` | PASS | `71 passed, 1 warning` |
| `uv run python tools/validate_codebase.py --scope meu` | PASS | `All blocking checks passed`; `8/8` blocking checks passed. |
| `rg` placeholder/skip sweep over wash-sale scope | PASS | Receipt: `C:\Temp\zorivest\recheck2-placeholder-skip-sweep.txt`; no matches. |
| `rg` account-scope sweep over plan, service, and tests | FAIL | Receipt: `C:\Temp\zorivest\recheck2-account-scope.txt`; service uses `is_tax_advantaged`, while the plan requires IRA-only destruction and leaves K401 blocked. |

### Prior Remaining Finding

| Finding | Prior Status | Recheck Result |
|---------|--------------|----------------|
| C2: IRA destruction not wired into service flow | open | Fixed for IRA-positive behavior. `scan_cross_account_wash_sales()` now creates and saves a `DESTROYED` chain, emits `LOSS_DESTROYED`, and avoids replacement-basis adjustment when the replacement account is marked tax-advantaged. |

### Confirmed Fix

- C2 core behavior is now implemented at `packages/core/src/zorivest_core/services/tax_service.py:718` and `packages/core/src/zorivest_core/services/tax_service.py:725`.
- Tests cover the IRA/taxable split at `tests/unit/services/test_tax_service_wash_sale.py:313`, `tests/unit/services/test_tax_service_wash_sale.py:374`, and `tests/unit/services/test_tax_service_wash_sale.py:412`.

### Remaining Finding

| # | Severity | Finding | File:Line | Required Action | Status |
|---|----------|---------|-----------|-----------------|--------|
| 1 | High | IRA destruction is now wired, but the implementation over-generalizes the rule to every account where `is_tax_advantaged=True`. The approved plan explicitly says this MEU implements IRA-only destruction, AC-132.3 names `AccountType.IRA`, and K401 permanent-loss destruction is deferred pending human approval. Because `Account` also carries `account_type`, the current predicate can silently apply the deferred K401 behavior if a K401 account is marked tax-advantaged. | `docs/execution/plans/2026-05-13-wash-sale-engine/implementation-plan.md:34`, `docs/execution/plans/2026-05-13-wash-sale-engine/implementation-plan.md:130`, `docs/execution/plans/2026-05-13-wash-sale-engine/implementation-plan.md:141`, `docs/execution/plans/2026-05-13-wash-sale-engine/task.md:48`, `docs/execution/plans/2026-05-13-wash-sale-engine/task.md:53`, `packages/core/src/zorivest_core/services/tax_service.py:718` | Gate destruction on `replacement_account.account_type == AccountType.IRA` unless a human-approved source expands the rule. Add a regression test with a non-IRA tax-advantaged replacement account, such as `AccountType.K401`, proving it does not trigger `DESTROYED` while row 31 remains blocked. | open |

### Verdict

`changes_required` - the original C2 service-wiring defect is fixed and validation is green, but approval is still blocked by an over-broad retirement-account predicate that implements deferred K401 behavior without the required human approval.

---

## Corrections Applied (2026-05-13, Pass 2)

**Workflow**: `/execution-corrections`
**Agent**: opus

### Finding Resolved

| # | Severity | Finding | Fix | Verified |
|---|----------|---------|-----|----------|
| 1 | High | IRA destruction predicate over-generalizes: `is_tax_advantaged` matches K401 and other tax-advantaged accounts, silently implementing deferred K401 destruction without human approval | Narrowed predicate from `repl_account.is_tax_advantaged` to `repl_account.account_type == AccountType.IRA`. Added `AccountType` import. K401 accounts now get standard ABSORBED treatment. | ✅ K401 regression test passes |

### TDD Evidence

**Red phase**: `test_k401_replacement_not_destroyed` failed — K401 account with `is_tax_advantaged=True` incorrectly triggered DESTROYED (expected ABSORBED).

**Green phase**: After narrowing predicate to `AccountType.IRA`:
- `test_k401_replacement_not_destroyed` — K401 replacement gets ABSORBED (standard treatment)
- `test_ira_replacement_creates_destroyed_chain` — IRA still correctly gets DESTROYED
- All 6 cross-account tests pass

### Changed Files

```diff
# packages/core/src/zorivest_core/services/tax_service.py
-from zorivest_core.domain.enums import CostBasisMethod, TradeAction
+from zorivest_core.domain.enums import AccountType, CostBasisMethod, TradeAction

 # L716-720: Narrowed predicate
-                    is_ira = (
-                        repl_account is not None
-                        and repl_account.is_tax_advantaged
-                    )
+                    # AC-132.3: Only IRA triggers permanent destruction.
+                    # K401 destruction is deferred pending human approval.
+                    is_ira = (
+                        repl_account is not None
+                        and repl_account.account_type == AccountType.IRA
+                    )

# tests/unit/services/test_tax_service_wash_sale.py
+ AccountType import added at module level
+ account_type set on all mock accounts (IRA, BROKER)
+ test_k401_replacement_not_destroyed regression test added
+ list[object] → list[Any] to fix pyright reportAttributeAccessIssue
```

### Quality Gates

| Gate | Result |
|------|--------|
| Cross-account tests | 6 passed |
| Wash sale test suite | 72 passed |
| Full regression | 3277 passed, 23 skipped, 0 failed |
| Pyright (touched files) | 0 errors |
| Ruff (touched files) | All checks passed |

### Verdict

`corrections_applied` — The over-broad retirement-account predicate is now narrowed to `AccountType.IRA` only, with a K401 regression test proving non-IRA tax-advantaged accounts get standard ABSORBED treatment. Ready for `/execution-critical-review` recheck.

---

## Recheck (2026-05-13, Pass 3)

**Workflow**: `/execution-critical-review` recheck
**Agent**: codex

### Commands Executed

| Command | Result | Evidence |
|---------|--------|----------|
| `rg` account-scope sweep over plan, service, and tests | PASS with non-blocking doc drift | Receipt: `C:\Temp\zorivest\recheck3-account-scope.txt`; service predicate now uses `account_type == AccountType.IRA`, K401 task remains `[B]`, and K401 regression coverage exists. One stale method docstring still says "other tax-advantaged account"; runtime behavior and tests are correct. |
| `git diff -- packages/core/src/zorivest_core/services/tax_service.py tests/unit/services/test_tax_service_wash_sale.py <review>` | PASS | Receipt: `C:\Temp\zorivest\recheck3-diff-scope.txt`; correction imports `AccountType`, narrows the predicate, and adds K401 regression coverage. |
| `uv run pytest tests/unit/domain/tax/test_wash_sale.py tests/unit/domain/tax/test_wash_sale_detector.py tests/unit/domain/tax/test_wash_sale_chain_manager.py tests/unit/domain/tax/test_wash_sale_cross_account.py tests/unit/services/test_tax_service_wash_sale.py tests/unit/infrastructure/test_wash_sale_repository.py tests/integration/test_wash_sale_repo_integration.py -q` | PASS | `72 passed, 1 warning` |
| `uv run python tools/validate_codebase.py --scope meu` | PASS | `All blocking checks passed`; `8/8` blocking checks passed. Advisory warnings only: coverage, bandit, and corrections-handoff evidence bundle shape. |
| `rg` placeholder/skip sweep over wash-sale scope | PASS | Receipt: `C:\Temp\zorivest\recheck3-placeholder-skip-sweep.txt`; no matches. |
| `git status --short` | PASS | Receipt: `C:\Temp\zorivest\recheck3-git-status.txt`; wash-sale correction files and this review file are modified/untracked as expected. |

### Prior Remaining Finding

| Finding | Prior Status | Recheck Result |
|---------|--------------|----------------|
| Over-broad retirement-account predicate used `is_tax_advantaged`, silently applying deferred K401 destruction behavior | open | Fixed. `scan_cross_account_wash_sales()` now gates permanent destruction on `replacement_account.account_type == AccountType.IRA`; K401 tax-advantaged accounts receive standard ABSORBED treatment. |

### Confirmed Fixes

- Predicate narrowed at `packages/core/src/zorivest_core/services/tax_service.py:720` to `AccountType.IRA`.
- K401 regression coverage added at `tests/unit/services/test_tax_service_wash_sale.py:481`, asserting `AccountType.K401` with `is_tax_advantaged=True` saves an `ABSORBED` chain and updates replacement basis.
- IRA-positive behavior remains covered at `tests/unit/services/test_tax_service_wash_sale.py:313`, asserting `DESTROYED` and `LOSS_DESTROYED` with no basis update.

### Residual Notes

- Non-blocking cleanup: `packages/core/src/zorivest_core/services/tax_service.py:661` still says "IRA (or other tax-advantaged account)" in the method docstring. The executable logic and regression tests now enforce IRA-only destruction, so this is not a runtime blocker, but the docstring should be aligned during the next correction/docs cleanup.
- `tools/validate_codebase.py --scope meu` reports only advisory warnings; no blocking check failed.

### Verdict

`approved` - all previously blocking implementation findings are fixed, the K401 deferred-scope guard is now covered by regression tests, and the wash-sale slice plus MEU gate are green.
