# Task Handoff

## Task

- **Date:** 2026-03-15
- **Task slug:** agents-gemini-consolidation-critical-review
- **Owner role:** reviewer
- **Scope:** Critical review of the AGENTS.md/GEMINI.md consolidation and its live documentation impact

## Inputs

- User request: Review the AGENTS.md expansion and GEMINI.md thin-shim replacement after critical-review feedback was applied
- Specs/docs referenced:
  - `SOUL.md`
  - `AGENTS.md`
  - `GEMINI.md`
  - `.agent/context/current-focus.md`
  - `.agent/context/known-issues.md`
  - `.agent/workflows/critical-review-feedback.md`
  - `docs/execution/README.md`
  - `docs/execution/reflections/TEMPLATE.md`
  - `docs/execution/metrics.md`
- Constraints:
  - Review-only session
  - Do not overwrite unrelated focus state
  - Findings must cite concrete file lines

## Role Plan

1. reviewer
- Optional roles: tester

## Coder Output

- Changed files:
  - `.agent/context/handoffs/2026-03-15-agents-gemini-consolidation-critical-review.md`
- Design notes / ADRs referenced:
  - None
- Commands run:
  - `git status --short`
  - `git diff -- AGENTS.md GEMINI.md .agent/workflows/critical-review-feedback.md .agent/context/current-focus.md`
  - `rg -n "GEMINI\.md|brain folder|agent workspace|critical-review-feedback|validation-review|create-plan|orchestrated-delivery|planning-corrections|meu-handoff" -S .`
  - `rg -n "GEMINI\.md §|GEMINI\.md" docs/execution .agent/context -S`
- Results:
  - Review artifact created
  - No product changes; review-only

## Tester Output

- Commands run:
  - `pomera_diagnose`
  - `pomera_notes search_term="Zorivest"`
  - `get_text_file_contents` for reviewed files
- Pass/fail matrix:
  - MCP availability: PASS
  - Cross-file consistency after consolidation: FAIL
- Repro failures:
  - `docs/execution/README.md:25,27,50-52` still cites removed `GEMINI.md` sections (`§Mode Transitions`, `§TDD-First Protocol`, `§Execution Contract`)
  - `docs/execution/reflections/TEMPLATE.md:120` still instructs future reflections to cite `GEMINI.md §X`
  - `docs/execution/metrics.md:44` still requires rule sampling from `AGENTS.md + GEMINI.md`, even though `GEMINI.md` is now a shim with no operative rule sections
- Coverage/test gaps:
  - No executable tests apply; this was a documentation consistency review
- Evidence bundle location:
  - `.agent/context/handoffs/2026-03-15-agents-gemini-consolidation-critical-review.md`
- FAIL_TO_PASS / PASS_TO_PASS result:
  - N/A
- Mutation score:
  - N/A
- Contract verification status:
  - Failed due to live docs still pointing at removed `GEMINI.md` section names

## Reviewer Output

- Findings by severity:
  - **High:** `docs/execution/README.md:25,27,50-52` still treats `GEMINI.md` as the source for operational section anchors. After the consolidation, those sections no longer exist in `GEMINI.md`, so the published execution loop now points implementers to dead citations for planning, TDD, and completion safeguards.
  - **Medium:** `docs/execution/reflections/TEMPLATE.md:120` still requires `GEMINI.md §X` as a reflection source example. This guarantees future reflection artifacts will keep emitting broken citations instead of referencing `AGENTS.md`, which undercuts the stated single-source-of-truth model.
  - **Medium:** `docs/execution/metrics.md:44` still instructs agents to sample the top 10 rules from `AGENTS.md + GEMINI.md`. That is no longer a coherent rule source set because `GEMINI.md` is now a shim rather than an operative instruction document.
- Open questions:
  - Should `.agent/context/current-focus.md:17` keep `GEMINI.md` as the Gemini entrypoint file name, or should it explicitly say `GEMINI.md -> AGENTS.md` to reinforce the new model?
  - Are historical reflection files intentionally immutable even when their `GEMINI.md §...` citations no longer resolve?
- Verdict:
  - changes_required
- Residual risk:
  - Leaving the live execution README/template/metrics files unchanged will keep producing stale cross-references and make the consolidation appear incomplete to future agents.
- Anti-deferral scan result:
  - No placeholder issue relevant to this review artifact

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:** 2026-03-15 12:27:11 -04:00

## Final Summary

- Status:
  - Review complete; consolidation is not fully closed due to live cross-document citation drift
- Next steps:
  - Update `docs/execution/README.md` to cite `AGENTS.md` sections instead of removed `GEMINI.md` sections
  - Update `docs/execution/reflections/TEMPLATE.md` to use `AGENTS.md` as the default rule-source example
  - Update `docs/execution/metrics.md` so rule adherence sampling draws from current canonical instruction sources only

---

## 2026-03-15 Recheck Update

### Scope Rechecked

- `docs/execution/README.md`
- `docs/execution/reflections/TEMPLATE.md`
- `docs/execution/metrics.md`
- `.agent/context/current-focus.md`
- `AGENTS.md`
- `GEMINI.md`

### Commands Executed

- `git status --short`
- `git diff -- AGENTS.md GEMINI.md docs/execution/README.md docs/execution/reflections/TEMPLATE.md docs/execution/metrics.md .agent/context/current-focus.md .agent/context/handoffs/2026-03-15-agents-gemini-consolidation-critical-review.md`
- `rg -n "GEMINI\.md §|GEMINI\.md" docs/execution .agent/context/current-focus.md -S`
- `rg -n "AGENTS\.md \+ GEMINI\.md|GEMINI\.md §X|GEMINI\.md" docs/execution/README.md docs/execution/reflections/TEMPLATE.md docs/execution/metrics.md .agent/context/current-focus.md -S`

### Findings

- No remaining findings in the live execution guidance or templates originally called out.
- `docs/execution/README.md` now points to `AGENTS.md` for planning, TDD, and execution-contract citations.
- `docs/execution/reflections/TEMPLATE.md` now uses `AGENTS.md` as the rule-source example.
- `docs/execution/metrics.md` now samples rule adherence from `AGENTS.md`.
- `.agent/context/current-focus.md` now clarifies the runtime relationship as `AGENTS.md` via `GEMINI.md` shim.

### Residual Risk

- Historical reflection files and older archived plan artifacts still contain `GEMINI.md §...` citations. I am treating those as historical records rather than live instruction regressions.

### Verdict

- approved
