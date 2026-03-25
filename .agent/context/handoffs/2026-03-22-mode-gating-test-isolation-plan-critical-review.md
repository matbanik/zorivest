# Task Handoff

## Task

- **Date:** 2026-03-22
- **Task slug:** mode-gating-test-isolation-plan-critical-review
- **Owner role:** reviewer
- **Scope:** Pre-implementation critical review of `docs/execution/plans/2026-03-22-mode-gating-test-isolation/implementation-plan.md` and `task.md`

## Inputs

- User request: Review `critical-review-feedback.md`, `implementation-plan.md`, and `task.md`
- Specs/docs referenced:
  - `.agent/workflows/critical-review-feedback.md`
  - `docs/execution/plans/2026-03-22-mode-gating-test-isolation/implementation-plan.md`
  - `docs/execution/plans/2026-03-22-mode-gating-test-isolation/task.md`
  - `docs/build-plan/08-market-data.md`
  - `docs/build-plan/09a-persistence-integration.md`
  - `docs/build-plan/build-priority-matrix.md`
  - `docs/BUILD_PLAN.md`
  - `.agent/context/meu-registry.md`
  - `.agent/context/known-issues.md`
  - `tests/unit/test_provider_registry.py`
  - `packages/infrastructure/src/zorivest_infra/market_data/provider_registry.py`
- Constraints:
  - Review-only workflow; no product fixes
  - Plan review mode, not implementation review
  - Findings must cite live file state and executed commands

## Role Plan

1. orchestrator
2. tester
3. reviewer
- Optional roles: researcher, guardrail

## Coder Output

- Changed files:
  - `.agent/context/handoffs/2026-03-22-mode-gating-test-isolation-plan-critical-review.md` (new review handoff)
- Design notes / ADRs referenced:
  - None
- Commands run:
  - None
- Results:
  - No product changes; review-only

## Tester Output

- Commands run:
  - `Get-Content -Raw SOUL.md`
  - `Get-Content -Raw AGENTS.md`
  - `Get-Content -Raw .agent/context/current-focus.md`
  - `Get-Content -Raw .agent/context/known-issues.md`
  - `Get-Content -Raw .agent/workflows/critical-review-feedback.md`
  - `Get-Content -Raw .agent/docs/emerging-standards.md`
  - line-numbered reads of:
    - `docs/execution/plans/2026-03-22-mode-gating-test-isolation/implementation-plan.md`
    - `docs/execution/plans/2026-03-22-mode-gating-test-isolation/task.md`
    - `docs/build-plan/09a-persistence-integration.md`
    - `docs/build-plan/08-market-data.md` (MEU-90b service-wiring section)
    - `docs/BUILD_PLAN.md`
    - `docs/build-plan/build-priority-matrix.md`
    - `.agent/context/meu-registry.md`
    - `.agent/context/known-issues.md`
    - `tests/unit/test_provider_registry.py`
    - `packages/infrastructure/src/zorivest_infra/market_data/provider_registry.py`
  - `rg -n "90b|mode-gating-test-isolation|service-wiring|Yahoo Finance|TradingView|14 providers|12 providers" docs/build-plan .agent/context/meu-registry.md docs/BUILD_PLAN.md tests/unit/test_provider_registry.py packages/api/src/zorivest_api/provider_registry.py .agent/context/known-issues.md`
  - `rg -n "14 providers|12 providers|provider registry \(12 providers\)|All 12 providers|all 12 providers|12 entries|sorted list of 12 names|Static provider registry \(12 providers\)" docs .agent/context tests/unit packages/infrastructure`
  - `rg --files | rg "provider_registry\.py$|08-market-data\.md$|BUILD_PLAN\.md$|TEMPLATE\.md$|testing-strategy\.md$|build-priority-matrix\.md$"`
  - `Get-ChildItem .agent/context/handoffs/*mode-gating-test-isolation* | Select-Object FullName,LastWriteTime`
  - `git status --short -- docs/build-plan .agent/context tests/unit packages/api docs/BUILD_PLAN.md`
  - `uv run pytest tests/unit/test_provider_registry.py -q`
  - `uv run pytest tests/unit/test_api_analytics.py::TestModeGating tests/unit/test_api_tax.py::TestTaxModeGating tests/unit/test_api_system.py::TestMcpGuardAuth tests/unit/test_market_data_api.py::TestGetQuote::test_locked_db_returns_403 tests/unit/test_api_foundation.py::TestModeGating tests/unit/test_api_settings.py::TestSettingsModeGating -q`
- Pass/fail matrix:
  - `tests/unit/test_provider_registry.py`: **FAIL** (`5 failed, 78 passed`) with count/name drift caused by live 14-entry registry
  - Mode-gating regression command: **PASS** (`9 passed`)
  - Plan discovery: **PASS** explicit plan scope, no existing canonical review handoff found
- Repro failures:
  - `tests/unit/test_provider_registry.py::TestProviderRegistryAC1::test_registry_count`
  - `tests/unit/test_provider_registry.py::TestProviderRegistryAC3::test_all_expected_names_present`
  - `tests/unit/test_provider_registry.py::TestProviderRegistryAC3::test_no_unexpected_names`
  - `tests/unit/test_provider_registry.py::TestListProviderNamesAC5::test_returns_12_names`
  - `tests/unit/test_provider_registry.py::TestListProviderNamesAC5::test_matches_expected_names`
- Coverage/test gaps:
  - Review confirmed the failing test premise, but the plan does not yet define whether the correct fix is test expansion or registry/spec rollback
- Evidence bundle location:
  - This handoff
- FAIL_TO_PASS / PASS_TO_PASS result:
  - FAIL present for provider-registry tests
  - PASS present for mode-gating tests
- Mutation score:
  - Not run
- Contract verification status:
  - **Failed**. Canonical docs disagree on provider count and MEU-90b ownership, so the proposed edits are not yet source-backed

## Reviewer Output

- Findings by severity:
  - **High** — The plan converts a failing test contract from 12 providers to 14 without reconciling the canonical spec, so it is currently treating drift as truth instead of proving the intended behavior. The proposed edits in `docs/execution/plans/2026-03-22-mode-gating-test-isolation/implementation-plan.md:16-32` and `task.md:15-22` assume Yahoo Finance and TradingView belong in MEU-59, but the live canon still defines the registry as 12 providers in `docs/BUILD_PLAN.md:237`, `.agent/context/meu-registry.md:92`, `docs/build-plan/build-priority-matrix.md:77`, `docs/build-plan/08-market-data.md:774`, and the test file itself at `tests/unit/test_provider_registry.py:1-10`. Under `AGENTS.md`, tests are specification and non-spec changes must be source-backed; this plan does neither.
  - **High** — The proposed `[DOC-STALESLUG]` fix picks an unresolved target slug and would deepen canon drift instead of removing it. The plan says to change `09a-persistence-integration.md` from `service-wiring` to `mode-gating-test-isolation` at `implementation-plan.md:38-44`, but the same service-wiring ownership is still stated in `docs/build-plan/08-market-data.md:782-788`, while `.agent/context/known-issues.md:136-142` says the correct fix is `MEU-90a persistence-wiring`, and `.agent/context/current-focus.md:7-14` still describes a `90a/b/c/d service-wiring cluster`. This ownership conflict must be resolved across canon before any single-file doc patch is approved.
  - **Medium** — `implementation-plan.md` and `task.md` disagree on the exact test-edit strategy, so the execution instructions are internally contradictory. `implementation-plan.md:19` says to add Yahoo Finance and TradingView to `EXPECTED_NAMES`, but `implementation-plan.md:31-32` says not to add them there, and `task.md:18-20` introduces `ALL_PROVIDER_NAMES` while explicitly keeping `EXPECTED_NAMES` at 12. This fails plan/task alignment and would let two different coders make materially different edits from the same plan.
  - **Medium** — The verification plan is incomplete against the repo’s mandatory MEU gate. `implementation-plan.md:60-78` only schedules `pytest` commands, but `AGENTS.md` requires `uv run python tools/validate_codebase.py --scope meu` plus scoped `pyright`, `ruff`, and anti-placeholder checks before MEU completion. As written, the plan’s verification would create false confidence even if the code change broke typing or lint rules.
  - **Medium** — The plan’s file targeting is inaccurate enough to hurt auditability. The evidence note at `implementation-plan.md:27` references `provider_registry.py` lines `149-170`, and the earlier review draft targeted `packages/api/src/zorivest_api/provider_registry.py`, but no such file exists; the actual registry lives at `packages/infrastructure/src/zorivest_infra/market_data/provider_registry.py:1-197`. A plan that points reviewers or implementers at the wrong package boundary is not ready for execution.
- Open questions:
  - Are Yahoo Finance and TradingView now part of the canonical Phase 8 provider registry, or are they a GUI-layer/free-provider overlay that should not change MEU-59 acceptance criteria?
  - Which MEU now owns market-data service wiring and stub retirement after MEU-90b was repurposed: `MEU-90a`, a still-existing `MEU-90b service-wiring` concept, or a new MEU that has not been registered yet?
  - Should this folder remain a narrow mode-gating/doc-cleanup plan, with provider-registry canon reconciliation split into a separate planning correction?
- Verdict:
  - `changes_required`
- Residual risk:
  - Executing this plan as written risks enshrining two unreviewed drifts: a 12→14 provider contract flip and a second contradictory MEU-90b ownership statement. That would make subsequent reviews harder because both the tests and the docs would have been changed without a single resolved source of truth.
- Anti-deferral scan result:
  - Review-only; no new placeholders introduced

## Guardrail Output (If Required)

- Safety checks:
  - Not required for this docs/plan review
- Blocking risks:
  - Not applicable
- Verdict:
  - Not applicable

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status:
  - Plan reviewed in pre-implementation mode; canonical review file created
- Next steps:
  - Run `/planning-corrections` on `docs/execution/plans/2026-03-22-mode-gating-test-isolation/`
  - First resolve the canonical source of truth for provider count and MEU-90b ownership across `docs/BUILD_PLAN.md`, `.agent/context/meu-registry.md`, `docs/build-plan/08-market-data.md`, `docs/build-plan/09a-persistence-integration.md`, `.agent/context/known-issues.md`, and `.agent/context/current-focus.md`
  - Then rewrite this plan so the chosen fix path, task instructions, and verification commands all align


---

## Corrections Applied - 2026-03-22

- **Workflow:** `/planning-corrections`
- **Verdict after corrections:** `corrections_applied`

### Findings Resolved

| # | Severity | Finding | Resolution |
|---|----------|---------|------------|
| H1 | High | Plan treated registry count drift as truth (12->14) | Preserved `EXPECTED_NAMES` at 12; `== 12` -> `>= 12`; added `FREE_PROVIDER_NAMES` + `TestFreeProvidersAC7` |
| H2 | High | DOC-STALESLUG fix target wrong | Corrected to `MEU-90a persistence-wiring` per `known-issues.md:142` |
| M1 | Medium | `implementation-plan.md` internally contradicted itself | Rewrote with single consistent strategy |
| M2 | Medium | Verification missing quality gate commands | Added `ruff`, `pyright`, and doc sweep commands |
| M3 | Medium | Plan referenced non-existent package path | Corrected to `packages/infrastructure/src/zorivest_infra/market_data/provider_registry.py` |

### Additional Doc Sweep Findings

Doc sweep found 3 additional stale-slug locations beyond the original review:
- `08-market-data.md:782` - section heading `## Service Wiring (MEU-90b)`
- `08-market-data.md:785` - callout `MEU-90b (`service-wiring`)`
- `known-issues.md:77` - phase label `proposed MEU-90b `service-wiring`

All 3 added to the corrected execution plan files.

### Source-of-Truth Used

- `current-focus.md:93` - Yahoo Finance + TradingView are MEU-65 GUI additions, not MEU-59 spec
- `known-issues.md:142` - DOC-STALESLUG correct fix is `MEU-90a persistence-wiring`

### Files Changed (Plan Corrections Only)

- `docs/execution/plans/2026-03-22-mode-gating-test-isolation/implementation-plan.md` - full rewrite
- `docs/execution/plans/2026-03-22-mode-gating-test-isolation/task.md` - full rewrite

---

## Recheck Update - 2026-03-22

- **Trigger:** User requested `recheck` after `/planning-corrections`
- **Verdict after recheck:** `changes_required`

### Commands Executed

- line-numbered rereads of:
  - `docs/execution/plans/2026-03-22-mode-gating-test-isolation/implementation-plan.md`
  - `docs/execution/plans/2026-03-22-mode-gating-test-isolation/task.md`
  - `docs/build-plan/08-market-data.md`
  - `docs/build-plan/09a-persistence-integration.md`
  - `docs/BUILD_PLAN.md`
  - `.agent/context/meu-registry.md`
  - `.agent/context/known-issues.md`
  - `.agent/context/handoffs/2026-03-22-mode-gating-test-isolation-plan-critical-review.md`
- `git status --short -- docs/execution/plans/2026-03-22-mode-gating-test-isolation docs/build-plan/08-market-data.md docs/build-plan/09a-persistence-integration.md docs/BUILD_PLAN.md .agent/context/meu-registry.md .agent/context/known-issues.md .agent/context/current-focus.md tests/unit/test_provider_registry.py packages/infrastructure/src/zorivest_infra/market_data/provider_registry.py .agent/context/handoffs/2026-03-22-mode-gating-test-isolation-plan-critical-review.md`
- `rg -n "14 providers|12 providers|service-wiring|mode-gating-test-isolation|persistence-wiring|Yahoo Finance|TradingView|ALL_PROVIDER_NAMES|EXPECTED_NAMES" docs/execution/plans/2026-03-22-mode-gating-test-isolation docs/build-plan/08-market-data.md docs/build-plan/09a-persistence-integration.md docs/BUILD_PLAN.md .agent/context/meu-registry.md .agent/context/known-issues.md .agent/context/current-focus.md tests/unit/test_provider_registry.py packages/infrastructure/src/zorivest_infra/market_data/provider_registry.py`
- `uv run pytest tests/unit/test_provider_registry.py -q`
- `uv run pytest tests/unit/test_api_analytics.py::TestModeGating tests/unit/test_api_tax.py::TestTaxModeGating tests/unit/test_api_system.py::TestMcpGuardAuth tests/unit/test_market_data_api.py::TestGetQuote::test_locked_db_returns_403 tests/unit/test_api_foundation.py::TestModeGating tests/unit/test_api_settings.py::TestSettingsModeGating -q`
- `uv run ruff check tests/unit/test_provider_registry.py packages/infrastructure/src/zorivest_infra/market_data/provider_registry.py`
- `uv run pyright tests/unit/test_provider_registry.py`
- `rg -n "MEU-90b.*service-wiring|service-wiring.*MEU-90b" docs/build-plan/ .agent/context/`

### Recheck Findings

- **High** — The doc-ownership correction is still not canonically resolved. The revised plan now rewrites service-wiring references to `MEU-90a persistence-wiring` or `MEU-90a + MEU-90b` in `docs/execution/plans/2026-03-22-mode-gating-test-isolation/implementation-plan.md:43-55` and `task.md:30-38`, but the actual MEU descriptions still say `MEU-90a` is persistence/UoW wiring only in `docs/BUILD_PLAN.md:300` and `.agent/context/meu-registry.md:201`, while `MEU-90b` is mode-gating test isolation only in `docs/BUILD_PLAN.md:301` and `.agent/context/meu-registry.md:202`. Rewording `08-market-data.md` to `MEU-90a + MEU-90b` is therefore still an unsourced reassignment of work, not a proven correction.

- **Medium** — The revised test strategy weakens the registry contract too far. The plan now changes exact assertions to `>= 12` and subset checks in `docs/execution/plans/2026-03-22-mode-gating-test-isolation/implementation-plan.md:27-35` and `task.md:20-25`. That would stop the suite from detecting unexpected future providers beyond Yahoo Finance and TradingView. Since the plan already names the only two allowed additions, it should keep a closed contract such as `EXPECTED_NAMES ∪ FREE_PROVIDER_NAMES`, not an open-ended growth allowance.

- **Medium** — The new doc-sweep validation is not runnable as written because it searches historical review artifacts too. The plan expects `0 matches` from `docs/execution/plans/2026-03-22-mode-gating-test-isolation/implementation-plan.md:97-106` and `task.md:46`, but the current pattern already appears in `.agent/context/handoffs/082-2026-03-22-sqlcipher-native-deps-bp02s2.3.md:167` and this rolling review handoff. Even after fixing live canon files, the command will still fail unless the scope excludes handoffs or explicitly limits the search to intended docs.

- **Medium** — Verification improved, but it still does not include the mandatory MEU gate command from `AGENTS.md`. The revised plan adds `ruff` and `pyright` in `implementation-plan.md:86-92`, but it still omits `uv run python tools/validate_codebase.py --scope meu` and the anti-placeholder scan required before MEU completion.

### Recheck Status Notes

- **Resolved since prior pass**
  - The plan no longer points to a non-existent `packages/api/.../provider_registry.py` path.
  - The plan/task contradiction around `EXPECTED_NAMES` vs `ALL_PROVIDER_NAMES` was removed.
  - Scoped `ruff` and `pyright` commands were added.

- **Reproduced evidence**
  - `tests/unit/test_provider_registry.py` still fails in the same 5 places before implementation.
  - Targeted mode-gating tests still pass (`9 passed`).
  - `ruff` and `pyright` both pass on the currently touched registry files.
  - The stale-slug `rg` sweep returns historical handoff matches, so the planned `0 matches` expectation is currently false.


---

## Corrections Applied (Pass 2) - 2026-03-22

- **Trigger:** User re-invoked `/planning-corrections` after recheck
- **Verdict after corrections:** `corrections_applied`

### Recheck Findings Resolved

| # | Severity | Finding | Resolution |
|---|----------|---------|------------|
| R-H1 | High | 08-market-data.md heading `(MEU-90a + MEU-90b)` was unsourced | Removed MEU attribution entirely: `## Service Wiring` |
| R-M1 | Medium | `>= 12` open-ended contract | Changed to exact closed-set: `len(EXPECTED_NAMES) + len(FREE_PROVIDER_NAMES) == 14` |
| R-M2 | Medium | Doc sweep rg hits historical handoffs | Narrowed scope to `docs/build-plan/` only (excludes handoffs) |
| R-M3 | Medium | `validate_codebase.py --scope meu` missing | Added to Quality Gate section in plan + task |

### Files Changed

- `docs/build-plan/08-market-data.md:782` - `## Service Wiring (MEU-90b)` -> `## Service Wiring`
- `docs/build-plan/08-market-data.md:785` - removed MEU-90b attribution from callout
- `docs/execution/plans/2026-03-22-mode-gating-test-isolation/implementation-plan.md` - closed-set strategy, rg scope, validate_codebase.py
- `docs/execution/plans/2026-03-22-mode-gating-test-isolation/task.md` - aligned to closed-set, MEU gate added

---

## Recheck Update 2 - 2026-03-22

- **Trigger:** User requested `recheck` after second correction pass
- **Verdict after recheck:** `approved`

### Commands Executed

- line-numbered rereads of:
  - `docs/execution/plans/2026-03-22-mode-gating-test-isolation/implementation-plan.md`
  - `docs/execution/plans/2026-03-22-mode-gating-test-isolation/task.md`
  - `docs/build-plan/08-market-data.md`
  - `docs/build-plan/09a-persistence-integration.md`
  - `docs/BUILD_PLAN.md`
  - `.agent/context/meu-registry.md`
  - `.agent/context/known-issues.md`
  - `tests/unit/test_provider_registry.py`
  - `.agent/context/handoffs/2026-03-22-mode-gating-test-isolation-plan-critical-review.md`
- `git status --short -- docs/execution/plans/2026-03-22-mode-gating-test-isolation docs/build-plan/08-market-data.md docs/build-plan/09a-persistence-integration.md docs/BUILD_PLAN.md .agent/context/meu-registry.md .agent/context/known-issues.md .agent/context/current-focus.md tests/unit/test_provider_registry.py packages/infrastructure/src/zorivest_infra/market_data/provider_registry.py .agent/context/handoffs/2026-03-22-mode-gating-test-isolation-plan-critical-review.md`
- `uv run pytest tests/unit/test_provider_registry.py -q`
- `uv run pytest tests/unit/test_api_analytics.py::TestModeGating tests/unit/test_api_tax.py::TestTaxModeGating tests/unit/test_api_system.py::TestMcpGuardAuth tests/unit/test_market_data_api.py::TestGetQuote::test_locked_db_returns_403 tests/unit/test_api_foundation.py::TestModeGating tests/unit/test_api_settings.py::TestSettingsModeGating -q`
- `uv run ruff check tests/unit/test_provider_registry.py packages/infrastructure/src/zorivest_infra/market_data/provider_registry.py`
- `uv run pyright tests/unit/test_provider_registry.py`
- `uv run python tools/validate_codebase.py --scope meu`

### Recheck Result

- No new findings.
- The plan now uses a closed-set registry contract in `docs/execution/plans/2026-03-22-mode-gating-test-isolation/implementation-plan.md:23-35` and `task.md:17-26`, which restores meaningful test strength.
- The stale-slug correction strategy no longer invents a new MEU owner in `docs/build-plan/08-market-data.md`; it removes the unsupported attribution instead, while `09a-persistence-integration.md` is targeted for correction to the known-issues workaround.
- The verification plan now includes scoped `ruff`, `pyright`, and the MEU gate command in `docs/execution/plans/2026-03-22-mode-gating-test-isolation/implementation-plan.md:86-100` and `docs/execution/plans/2026-03-22-mode-gating-test-isolation/task.md:41-48`.

### Residual Risk

- This is plan approval only. Implementation still needs to prove that the revised closed-set tests, doc fixes, and status updates land together without reopening canon drift.
