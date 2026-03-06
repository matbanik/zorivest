# Task Handoff Template

## Task

- **Date:** 2026-03-06
- **Task slug:** execution-session-critical-review
- **Owner role:** reviewer
- **Scope:** Review `.agent/workflows/execution-session.md` and `docs/execution/` for launch readiness, contract drift, and day-1 execution risk. Provide a corrected day-1 kickoff prompt without silently patching the reviewed workflow docs.

## Inputs

- User request:
  - Review `.agent/workflows/execution-session.md` and `docs/execution/` files/folder structure.
  - Provide critical review feedback on the approach.
  - Provide the first day-1 prompt that should kick off agentic coding.
- Specs/docs referenced:
  - `SOUL.md`
  - `AGENTS.md`
  - `GEMINI.md`
  - `.agent/context/current-focus.md`
  - `.agent/context/known-issues.md`
  - `.agent/context/meu-registry.md`
  - `.agent/workflows/execution-session.md`
  - `.agent/workflows/critical-review-feedback.md`
  - `.agent/workflows/tdd-implementation.md`
  - `.agent/workflows/meu-handoff.md`
  - `.agent/workflows/validation-review.md`
  - `.agent/context/handoffs/TEMPLATE.md`
  - `.agent/context/handoffs/2026-03-06-docs-build-plan-agentic-continuity-review.md`
  - `docs/execution/README.md`
  - `docs/execution/metrics.md`
  - `docs/execution/prompts/2026-03-06-scaffold-meu-1.md`
  - `docs/execution/reflections/TEMPLATE.md`
  - `.agent/docs/prompt-templates.md`
  - `.agent/docs/testing-strategy.md`
  - `docs/build-plan/01-domain-layer.md`
  - `docs/build-plan/testing-strategy.md`
  - `validate.ps1`
- Constraints:
  - Findings-first review.
  - Do not silently patch the reviewed workflow docs during the review.
  - Create a day-1 prompt artifact aligned with current repo rules.

## Role Plan

1. orchestrator
2. tester
3. reviewer
4. coder
- Optional roles: researcher, guardrail

## Coder Output

- Changed files:
  - Added `docs/execution/prompts/2026-03-06-meu-1-calculator-pilot.md`
  - Added this review handoff
- Design notes:
  - Left the reviewed execution docs untouched.
  - Wrote a replacement day-1 prompt that narrows scope to MEU-1 plus the minimum bootstrap required to run it.
  - Removed auto-commit, placeholder-stub, and machine-specific-link instructions from the replacement prompt.
- Commands run:
  - No product-code commands executed; documentation review and prompt authoring only.
- Results:
  - Review handoff created.
  - Replacement kickoff prompt created.

## Tester Output

- Commands run:
  - `Get-ChildItem -Name SOUL.md, .agent\context\current-focus.md, .agent\context\known-issues.md, .agent\workflows\execution-session.md, .agent\workflows\critical-review-feedback.md`
  - `rg --files docs/execution .agent/workflows`
  - `Get-Content` with line numbers for:
    - `AGENTS.md`
    - `GEMINI.md`
    - `.agent/workflows/execution-session.md`
    - `.agent/workflows/critical-review-feedback.md`
    - `.agent/workflows/tdd-implementation.md`
    - `.agent/workflows/meu-handoff.md`
    - `.agent/workflows/validation-review.md`
    - `.agent/context/meu-registry.md`
    - `docs/execution/README.md`
    - `docs/execution/metrics.md`
    - `docs/execution/prompts/2026-03-06-scaffold-meu-1.md`
    - `docs/build-plan/01-domain-layer.md`
    - `.agent/docs/prompt-templates.md`
    - `.agent/docs/testing-strategy.md`
    - `validate.ps1`
  - `Get-ChildItem docs\execution -Recurse`
  - `Get-ChildItem docs\execution\plans`
  - `git status --short -- .agent/workflows docs/execution .agent/context`
  - `rg -n "execution-session|docs/execution|Prompt -> Plan -> Execute -> Reflect|task_boundary|notify_user|BlockedOnUser|implementation_plan\.md|task\.md" .agent docs`
  - `rg -n 'pytest\.mark\.unit|markers|tests/unit/|\-m "unit"' .agent docs validate.ps1 pyproject.toml pytest.ini setup.cfg tox.ini`
- Pass/fail matrix:
  - Session context load: PASS
  - Workflow entrypoint consistency: FAIL
  - Validation-gate consistency: FAIL
  - Commit-policy consistency: FAIL
  - Placeholder-policy consistency: FAIL
  - Metrics-schema consistency: FAIL
  - Prompt-loop closure: FAIL
- Repro failures:
  - No runtime execution attempted; failures are documentation and process-contract mismatches.
- Coverage/test gaps:
  - Did not run Antigravity itself.
  - Did not execute the day-1 prompt live.
  - Review is based on static contract inspection plus repo command/path verification.
- Evidence bundle location:
  - This handoff.
- FAIL_TO_PASS / PASS_TO_PASS result:
  - N/A for docs review.
- Mutation score:
  - N/A.
- Contract verification status:
  - FAIL. Multiple launch-blocking contradictions remain in the reviewed approach.

## Reviewer Output

- Findings by severity:
  - **High:** `.agent/workflows/execution-session.md:178`, `docs/execution/prompts/2026-03-06-scaffold-meu-1.md:183`, `GEMINI.md:13`, `GEMINI.md:56`, `validate.ps1:26` - the completion gate is internally contradictory. The runtime contract says VERIFICATION runs `.\validate.ps1`, but the execution workflow and day-1 prompt only require targeted Python checks. This is not a cosmetic mismatch: `validate.ps1` currently points pytest at `packages/core/tests`, while the execution docs build `tests/unit/`. A first session cannot tell whether "done" means MEU-ready or full-repo clean.
  - **High:** `docs/execution/README.md:42`, `docs/execution/prompts/2026-03-06-scaffold-meu-1.md:5`, `GEMINI.md:116` - the advertised entrypoint is not wired into the runtime docs. Both execution docs tell the user to invoke `/execution-session`, but `GEMINI.md` does not map that slash command. The first launch command is therefore undocumented at the runtime boundary where Antigravity decides how to behave.
  - **High:** `docs/execution/prompts/2026-03-06-scaffold-meu-1.md:92`, `docs/execution/prompts/2026-03-06-scaffold-meu-1.md:115`, `docs/execution/prompts/2026-03-06-scaffold-meu-1.md:254`, `AGENTS.md:78`, `validation-review.md:78` - the day-1 prompt instructs the agent to create future-MEU placeholder modules inside `packages/core`. That conflicts with the repo rule to write complete implementations, not skeletons, and with the reviewer checklist that explicitly rejects skeleton stubs in completed deliverables. A faithful agent will either violate policy or ignore the prompt.
  - **High:** `.agent/workflows/execution-session.md:73`, `docs/execution/prompts/2026-03-06-scaffold-meu-1.md:136`, `docs/execution/prompts/2026-03-06-scaffold-meu-1.md:216`, `docs/execution/prompts/2026-03-06-scaffold-meu-1.md:246`, `AGENTS.md:90` - the execution approach requires auto-commits at checkpoints, but the repo policy explicitly forbids auto-commit and reserves commits for human-reviewed approval. This is a direct governance break, not a stylistic preference.
  - **Medium:** `.agent/workflows/execution-session.md:113`, `docs/execution/metrics.md:5` - the workflow tells the agent to append a key/value metrics table, but `docs/execution/metrics.md` is a row-oriented daily log. Following the workflow as written will corrupt the file format on the first write.
  - **Medium:** `docs/execution/README.md:26`, `.agent/workflows/execution-session.md:21`, `.agent/workflows/execution-session.md:98`, `docs/execution/reflections/TEMPLATE.md:1`, `docs/execution/README.md:10` - the loop claims prompt improvement through reflection, but the `docs/execution` structure has no prompt template and no required "reflection -> next prompt artifact" step. The process still depends on manual prompt writing, so the loop is not actually self-tightening.
  - **Medium:** `docs/execution/prompts/2026-03-06-scaffold-meu-1.md:92`, `docs/build-plan/01-domain-layer.md:11`, `docs/execution/prompts/2026-03-06-scaffold-meu-1.md:149`, `docs/execution/prompts/2026-03-06-scaffold-meu-1.md:164` - the prompt says "Create the directory tree from 01-domain-layer.md section 1.1" and links to build-plan sections with `file:///p:/...` absolute paths, but it actually creates only a reduced subset of that tree and bakes in a Windows-specific path. The intent is reasonable, but the wording makes the scaffold look spec-complete when it is really a minimum bootstrap.
  - **Medium:** `.agent/workflows/tdd-implementation.md:77`, `.agent/context/meu-registry.md:68`, `docs/execution/prompts/2026-03-06-scaffold-meu-1.md:188`, `docs/build-plan/testing-strategy.md:102`, `docs/build-plan/testing-strategy.md:221` - the workflow standardizes on `pytest -m "unit"`, but the day-1 prompt does not require marker config or marker assignment. Without adding pytest markers on day 1, the "full unit suite" command is not deterministic and may select zero tests.
- Open questions:
  - Should `.\validate.ps1` remain a mandatory end-of-session gate for MEU-sized work, or should the repo explicitly define a MEU gate versus a phase/repo gate?
  - Do you want `/execution-session` to be a first-class Antigravity slash command in `GEMINI.md`, or should the execution docs stop advertising slash invocation entirely and rely on explicit file reads?
  - Should `docs/execution/prompts/` gain its own `TEMPLATE.md`, or should the execution workflow point at `.agent/docs/prompt-templates.md` as the canonical template source?
- Verdict:
  - `changes_required`
- Residual risk:
  - Until the entrypoint, validation gate, placeholder policy, and commit policy are normalized, a day-1 run can appear successful while still violating repo governance and producing non-reproducible artifacts.
- Anti-deferral scan result:
  - Review artifacts added in this session contain no `TODO`, `FIXME`, or `NotImplementedError`.

## Guardrail Output (If Required)

- Safety checks:
  - Not required for docs-only review.
- Blocking risks:
  - Not applicable.
- Verdict:
  - Not applicable.

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status:
  - Review completed.
  - Findings recorded.
  - Replacement day-1 prompt created at `docs/execution/prompts/2026-03-06-meu-1-calculator-pilot.md`.
- Next steps:
  1. Decide whether `validate.ps1` is a MEU gate or a later phase gate, then update `GEMINI.md`, `.agent/workflows/execution-session.md`, and the day-1 prompt together.
  2. Add `/execution-session` to `GEMINI.md` or stop advertising the slash command.
  3. Remove auto-commit and future-module placeholder instructions from the original day-1 prompt.
  4. Align metrics-writing instructions with `docs/execution/metrics.md`.
  5. Add a deterministic prompt-template path for `docs/execution/prompts/`.
