# Task Handoff

## Task

- **Date:** 2026-03-06
- **Task slug:** build-plan-corrections-validation
- **Owner role:** reviewer
- **Scope:** Validate whether the current `docs/build-plan/` corrections actually satisfy the conditions from `.agent/context/handoffs/2026-03-06-docs-build-plan-friction-agentic-senior-review.md`.

## Inputs

- User request:
  - Validate the corrections in the plan
- Prior review target:
  - `.agent/context/handoffs/2026-03-06-docs-build-plan-friction-agentic-senior-review.md`
- Current files inspected:
  - `docs/build-plan/00-overview.md`
  - `docs/build-plan/01a-logging.md`
  - `docs/build-plan/02a-backup-restore.md`
  - `docs/build-plan/05-mcp-server.md`
  - `docs/build-plan/05j-mcp-discovery.md`
  - `docs/build-plan/06b-gui-trades.md`
  - `docs/build-plan/06c-gui-planning.md`
  - `docs/build-plan/06d-gui-accounts.md`
  - `docs/build-plan/06e-gui-scheduling.md`
  - `docs/build-plan/build-priority-matrix.md`
  - `.agent/context/current-focus.md`
  - `AGENTS.md`
  - `GEMINI.md`
  - `tools/validate_build_plan.py`
- Current-source criteria reused from same-day validation:
  - MCP lifecycle capability negotiation
  - MCP tools structured output compatibility
  - Anthropic simplicity-first guidance

## Role Plan

1. orchestrator
2. tester
3. reviewer

## Coder Output

- Changed files:
  - `.agent/context/handoffs/2026-03-06-build-plan-corrections-validation.md`
- Design notes:
  - Review-only session. No plan docs were modified.
  - `.agent/context/current-focus.md` remained untouched because it already has worktree changes.
- Commands run:
  - `git status --short -- .agent/context/handoffs docs/build-plan .agent/context/current-focus.md AGENTS.md GEMINI.md`
  - `git diff -- docs/build-plan/00-overview.md docs/build-plan/01a-logging.md docs/build-plan/02a-backup-restore.md docs/build-plan/06b-gui-trades.md docs/build-plan/06c-gui-planning.md docs/build-plan/06d-gui-accounts.md docs/build-plan/06e-gui-scheduling.md`
  - `Get-Content -Raw .agent/context/handoffs/2026-03-06-docs-build-plan-friction-agentic-senior-review.md`
  - `rg -n "simplicity-first|prototype mode|single-client production baseline|multi-client|generalized platform|Gate A|Gate B|Gate C|rollout gate|entry gate|evidence gate|capability negotiation|client-name heuristics|outputSchema|structured output|structuredContent|8 to 12|stdio-first|HTTP transport|small tool set|one client target|first MCP slice|expansion only by evidence" docs/build-plan docs/BUILD_PLAN.md`
  - `rg -n "GPT-5.4|GPT 5.3|reviewer/tester baseline|hooks|evals|evidence-first|anti-fake-completion|artifact-based" AGENTS.md GEMINI.md .agent/context/current-focus.md`
  - `python tools/validate_build_plan.py`
  - `Test-Path` checks for relocated `_inspiration` targets
- Results:
  - Verified that the visible file edits are mostly link-relocation changes.
  - Confirmed that major strategic corrections from the prior review are still absent in the live plan state.
  - Identified a validator limitation that now produces false broken-link failures for valid `../../_inspiration/...` targets and `file:///...` references.

## Tester Output

- Commands run:
  - grep sweeps
  - build-plan validator
  - path existence checks
- Pass/fail matrix:
  - `_inspiration` target files exist on disk: pass
  - `python tools/validate_build_plan.py`: fail
  - Prior review conditions re-checked against current plan state: fail
- Repro failures:
  - `python tools/validate_build_plan.py` reports 34 cross-reference errors after the relocation changes.
- Coverage/test gaps:
  - No runtime product tests were relevant; this was a documentation-state validation.

## Reviewer Output

- Findings by severity:
  - **High-1:** The substantive MCP-plan corrections from the prior senior review are still not present. `05-mcp-server.md` still defines a 37-tool default loadout optimized for Cursor at `docs/build-plan/05-mcp-server.md:747`, keeps dynamic toolset loading as a first-class baseline at `docs/build-plan/05-mcp-server.md:782`, and still maps behavior through `clientInfo.name` at `docs/build-plan/05-mcp-server.md:811` and `docs/build-plan/05-mcp-server.md:817`. That does not satisfy the earlier recommendation for a small, static, one-client, capability-first MCP starting point.
  - **High-2:** The structured-output correction has not landed. The earlier review explicitly pushed structured tool outputs as a day-1 contract, but the current plan still says `outputSchema` support exists and is "not yet adopted" at `docs/build-plan/05-mcp-server.md:1000`. That remains inconsistent with the requested correction direction.
  - **Medium-1:** `00-overview.md` has solid execution-integrity language at `docs/build-plan/00-overview.md:100`, `docs/build-plan/00-overview.md:114`, and `docs/build-plan/00-overview.md:118`, but it still does not add the missing rollout staging from the prior review. There is still no explicit `prototype mode` / `single-client production baseline` / `multi-client platform mode` policy in the current build-plan docs.
  - **Medium-2:** Reviewer-baseline governance is still unresolved in live docs. `current-focus.md` still says GPT 5.3 is the active validation baseline at `.agent/context/current-focus.md:11` and `.agent/context/current-focus.md:18`, and still frames GPT-5.4 as undecided at `.agent/context/current-focus.md:30`. `AGENTS.md` and `GEMINI.md` still do not codify the requested baseline/directive updates.
  - **Medium-3:** The relocation-style link corrections appear valid on disk, but the validation pipeline cannot currently certify them. `python tools/validate_build_plan.py` fails with 34 errors, and the cross-reference checker only understands sibling `.md` links and single-parent `../...` links at `tools/validate_build_plan.py:179`. It does not resolve `../../_inspiration/...` or `file:///...` references, so the current validator produces false negatives after the relocation work.

- Open questions:
  - Were these plan corrections intended to address the 2026-03-06 senior-review conditions, or only the `_inspiration` relocation work?
  - Do you want the validator updated so relocation/link corrections can be certified cleanly?
  - Should Phase 5 corrections be applied in `05-mcp-server.md` before any implementation plan is considered approved?

- Verdict:
  - **changes_required**
  - The correction set is not validated. The visible edits are mostly link relocation updates, while the main sequencing/MCP corrections from the prior review remain largely unaddressed.

- Residual risk:
  - As long as the validator is stale and the MCP rollout stance is unchanged, the plan can look more corrected than it actually is.

## Detailed Validation Summary

### What Passed

1. The edited `_inspiration` targets referenced by the changed docs do exist on disk.
2. `00-overview.md` already contains strong evidence/verification language for FIC, phase exit, and FAIL_TO_PASS/PASS_TO_PASS.

### What Did Not Pass

1. The MCP baseline is still broad and toolset-heavy instead of constrained and single-target.
2. `outputSchema` remains deferred instead of being adopted as a first-class contract.
3. The reviewer-baseline decision is still unresolved in current operational docs.
4. The local validator fails after the relocation edits because its link resolver is outdated.

## Final Summary

- Status:
  - Validation completed. Corrections are only partially validated.
- Next steps:
  1. Decide whether you want relocation validation only or full strategic correction validation.
  2. Patch `tools/validate_build_plan.py` to resolve multi-parent and `file:///` links.
  3. Apply the actual Phase 5 and workflow-governance corrections before re-running validation.
