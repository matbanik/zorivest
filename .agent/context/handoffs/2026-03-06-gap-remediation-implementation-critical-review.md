# Task Handoff Template

## Task

- **Date:** 2026-03-06
- **Task slug:** gap-remediation-implementation-critical-review
- **Owner role:** reviewer
- **Scope:** Review the current uncommitted gap-remediation implementation changes in `.agent/`, `AGENTS.md`, `GEMINI.md`, `docs/execution/`, `docs/decisions/`, and `.agent/skills/` for correctness, cross-file consistency, and verification quality.

## Inputs

- User request:
  - Review the files pending commit in git
  - Use `.agent/workflows/critical-review-feedback.md`
  - Provide a findings-first critical review handoff
- Specs/docs referenced:
  - `SOUL.md`
  - `.agent/context/current-focus.md`
  - `.agent/context/known-issues.md`
  - `.agent/workflows/critical-review-feedback.md`
  - `AGENTS.md`
  - `GEMINI.md`
  - `.agent/context/handoffs/TEMPLATE.md`
  - `.agent/roles/coder.md`
  - `.agent/roles/orchestrator.md`
  - `.agent/workflows/execution-session.md`
  - `.agent/workflows/meu-handoff.md`
  - `.agent/workflows/validation-review.md`
  - `docs/execution/README.md`
  - `docs/execution/metrics.md`
  - `docs/execution/reflections/TEMPLATE.md`
  - `docs/execution/prompts/TEMPLATE.md`
  - `docs/build-plan/01-domain-layer.md`
  - `docs/decisions/README.md`
  - `docs/decisions/TEMPLATE.md`
  - `.agent/skills/README.md`
- Constraints:
  - Review-only; do not apply fixes
  - Use actual pending file state and diffs as source of truth
  - Focus on the implemented remediation files; prior review handoffs were not treated as the implementation target

## Role Plan

1. orchestrator
2. tester
3. reviewer
4. coder
- Optional roles: researcher, guardrail

## Coder Output

- Changed files:
  - `.agent/context/handoffs/2026-03-06-gap-remediation-implementation-critical-review.md`
- Design notes / ADRs referenced:
  - No product or workflow files were changed in this session.
  - Review scope centered on the actual pending implementation files, plus downstream files needed to validate the new contracts.
- Commands run:
  - Documentation inspection, diff review, and targeted consistency sweeps only
- Results:
  - Critical review handoff created

## Tester Output

- Commands run:
  - `Get-Content -Raw SOUL.md`
  - `Get-Content -Raw .agent/context/current-focus.md`
  - `Get-Content -Raw .agent/context/known-issues.md`
  - `pomera_notes search "Zorivest"`
  - `Get-Content -Raw .agent/workflows/critical-review-feedback.md`
  - `git status --short`
  - `git diff --stat -- .agent/context/handoffs/TEMPLATE.md .agent/roles/coder.md .agent/roles/orchestrator.md .agent/workflows/execution-session.md .agent/workflows/meu-handoff.md AGENTS.md GEMINI.md docs/execution/README.md docs/execution/metrics.md docs/execution/reflections/TEMPLATE.md`
  - `git diff -- .agent/context/handoffs/TEMPLATE.md .agent/roles/coder.md .agent/roles/orchestrator.md .agent/workflows/execution-session.md .agent/workflows/meu-handoff.md AGENTS.md GEMINI.md docs/execution/README.md docs/execution/metrics.md docs/execution/reflections/TEMPLATE.md`
  - `Get-ChildItem -Recurse docs/decisions`
  - `Get-ChildItem -Recurse .agent/skills`
  - `Get-Content` with line numbers for:
    - `AGENTS.md`
    - `GEMINI.md`
    - `.agent/context/handoffs/TEMPLATE.md`
    - `.agent/roles/coder.md`
    - `.agent/roles/orchestrator.md`
    - `.agent/workflows/execution-session.md`
    - `.agent/workflows/meu-handoff.md`
    - `.agent/workflows/validation-review.md`
    - `docs/execution/README.md`
    - `docs/execution/metrics.md`
    - `docs/execution/reflections/TEMPLATE.md`
    - `docs/execution/prompts/TEMPLATE.md`
    - `docs/decisions/README.md`
    - `docs/decisions/TEMPLATE.md`
    - `.agent/skills/README.md`
    - `docs/build-plan/01-domain-layer.md`
  - `Test-Path docs/execution/prompts/TEMPLATE.md`
  - `Get-ChildItem docs/execution/prompts -Force`
  - `rg -n "\{YYYY-MM-DD\}-\{slug\}\.md|\{YYYY-MM-DD\}-meu-\{N\}-\{slug\}\.md|human orchestrator creates prompts|Agent A \(GPT-5\.4\)|creates prompts" docs/execution .agent`
  - `rg -n -i "time and token usage are not constraints|time and token usage|time.*not constraints|token.*not constraints|quality, wisdom" AGENTS.md GEMINI.md`
  - `rg -n -i "time is not a constraint|token usage is not a constraint|one task = one session|human approval|pomera_notes|current-focus" AGENTS.md GEMINI.md`
  - `rg -n -i "docs/decisions/ADR-0001-architecture\.md|ADR-0001|ADR-NNNN|ADR-000" docs .agent AGENTS.md GEMINI.md`
  - `Test-Path docs/decisions/ADR-0001-architecture.md`
- Pass/fail matrix:
  - Pending diff capture: PASS
  - ADR registry creation: PASS
  - Skills directory creation: PASS
  - Metrics schema alignment: PASS
  - Prompt-contract consistency: FAIL
  - Build-plan ADR scaffold alignment: FAIL
  - AGENTS/GEMINI dedup completeness: FAIL
- Repro failures:
  - `Test-Path docs/decisions/ADR-0001-architecture.md` returns `False`.
  - Prompt naming/ownership sweep shows conflicting contracts between `docs/execution/README.md`, `.agent/workflows/execution-session.md`, and `docs/execution/reflections/TEMPLATE.md`.
- Coverage/test gaps:
  - No live Antigravity/Codex session was run against the new docs.
  - Review is limited to pending file state and cross-file contract inspection.
- Evidence bundle location:
  - `.agent/context/handoffs/2026-03-06-gap-remediation-implementation-critical-review.md`
- FAIL_TO_PASS / PASS_TO_PASS result:
  - N/A for docs review
- Mutation score:
  - N/A
- Contract verification status:
  - FAIL. The implementation closes most planned gaps but still leaves cross-file execution drift.

## Reviewer Output

- Findings by severity:
  - **High:** `docs/execution/README.md:10-11`, `docs/execution/README.md:26`, `docs/execution/README.md:31`, `docs/execution/README.md:64`, `.agent/workflows/execution-session.md:23-25`, `docs/execution/reflections/TEMPLATE.md:5` — the new execution prompt contract is internally inconsistent. README now says prompts are MEU-scoped files named `docs/execution/prompts/{YYYY-MM-DD}-meu-{N}-{slug}.md` and drafted by Agent A (GPT-5.4), but `execution-session.md` still instructs agents to load `docs/execution/prompts/{YYYY-MM-DD}-{slug}.md` and says the human orchestrator creates prompts. The reflection template also records the old path. A session following the workflow as written will look for and log the wrong prompt artifact.
  - **Medium:** `docs/decisions/README.md:1-4`, `docs/build-plan/01-domain-layer.md:19-20` — the ADR registry is added, but the repo still does not contain the scaffolded `docs/decisions/ADR-0001-architecture.md` file that the build plan declares should exist. `docs/decisions/` is therefore only partially aligned with the existing scaffold, and `Test-Path docs/decisions/ADR-0001-architecture.md` currently returns false.
  - **Medium:** `AGENTS.md:46-50`, `GEMINI.md:44`, `GEMINI.md:82`, `GEMINI.md:107` — the AGENTS/GEMINI deduplication is incomplete. The commit removes duplicate session-discipline bullets from `GEMINI.md`'s Execution Contract, but the same governance still appears elsewhere: time/token policy remains restated in `GEMINI.md`'s Quality-First Policy, and `pomera_notes` save requirements are still repeated in the TDD-First and Handoff sections. That means the implemented change does not fully deliver the stated "no duplicate instructions remain" outcome.
- Open questions:
  - Do you want `execution-session.md` to adopt the new Agent-A-authored MEU prompt contract, or should `docs/execution/README.md` be pulled back to the older human-authored prompt model?
  - Should `ADR-0001-architecture.md` be created now to match the scaffold, or should `docs/build-plan/01-domain-layer.md` be updated so the scaffold no longer implies it already exists?
  - Is the dedup goal "remove duplicates from the Execution Contract only" or "remove repeated governance across AGENTS/GEMINI entirely"?
- Verdict:
  - `changes_required`
- Residual risk:
  - If these changes are committed as-is, the repository will advertise a newer execution lifecycle than the actual workflow/template files implement. That creates prompt-file lookup errors and ambiguous operating behavior before the first MEU session even starts.
- Anti-deferral scan result:
  - No placeholder markers found in this review artifact.

## Guardrail Output (If Required)

- Safety checks:
  - Not required for docs-only review
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
  - Pending changes reviewed
  - Findings recorded
  - No fixes applied
- Next steps:
  1. Reconcile the prompt path/ownership contract across `docs/execution/README.md`, `.agent/workflows/execution-session.md`, and `docs/execution/reflections/TEMPLATE.md`.
  2. Decide whether `ADR-0001-architecture.md` should be created now or whether the build-plan scaffold should be updated.
  3. Tighten the AGENTS/GEMINI deduplication goal and patch whichever repeated governance statements are still intentional drift.
