# Research Handoff: Feature Validation + Agentic Execution Integrity

## Task

- **Date:** 2026-02-21
- **Task slug:** docs-build-plan-feature-validation-agentic-integrity-research
- **Owner role:** orchestrator
- **Scope:** Determine the most effective validation model for feature functionality (not only execution steps), and define planning controls that reduce implementation drift and prevent agentic deferral/skipping/false completion claims.

## Inputs

- User request:
  - Perform web research.
  - Focus on validation of feature intent + anti-drift.
  - Add controls that prevent defer/skip/false-completion behaviors.
  - Produce feedback doc in `.agent/context/handoffs/`.
- Local context used:
  - `.agent/context/handoffs/2026-02-21-docs-build-plan-critical-review-execution-risks.md`
  - `docs/build-plan/00-overview.md`
  - `docs/build-plan/testing-strategy.md`
  - `docs/build-plan/07-distribution.md`
  - `.agent/workflows/orchestrated-delivery.md`
  - Pomera note `#190` (post-correction status)
- Constraints:
  - High-accuracy, evidence-backed recommendations.
  - Execution-ready inserts (not generic advice).

## Role Plan

1. orchestrator
2. researcher
3. reviewer
4. guardrail

## Coder Output

- Changed files:
  - `.agent/context/handoffs/2026-02-21-docs-build-plan-feature-validation-and-agentic-integrity-research.md`
- Design notes:
  - Converted research into concrete build-plan/workflow insertions.
  - Mapped controls to anti-drift + anti-fake-completion risks.
- Commands run:
  - `rg -n` scans across `docs/build-plan/` for validation/gate coverage.
  - `Get-Content` reads of relevant planning/workflow files.
  - Web retrieval + evidence extraction (NIST, Scrum Guide, OpenAI evals, SWE-bench, Anthropic, GitHub docs, Pact, Hypothesis, PIT).
- Results:
  - Defined a multi-layer validation architecture + execution-integrity gate model.
  - Produced insertion checklist by file.

## Tester Output

- Commands run:
  - Plan-surface checks:
    - `rg -n "Definition of Done|acceptance criteria|validation|phase gate|contract test|property-based|mutation|status checks|branch protection" docs/build-plan`
    - `rg -n "^## |^### " docs/build-plan/00-overview.md docs/build-plan/testing-strategy.md`
    - `rg -n "CI|workflow|status checks|protected branch|merge" docs/build-plan/07-distribution.md`
  - Workflow check:
    - `Get-Content .agent/workflows/orchestrated-delivery.md`
- Pass/fail matrix:
  - Explicit feature-intent traceability gate: **fail**
  - Independent evidence-based completion gate: **fail**
  - Anti-deferral/anti-placeholder policy at planning layer: **fail**
  - Branch-protection mapping to required validation checks: **partial**
  - Existing functional testing baseline (unit/integration/e2e): **pass**
- Repro failures:
  - No required mapping from each acceptance criterion to executable tests/evals.
  - No hard requirement for machine-verifiable completion evidence beyond self-report.
  - No documented policy for blocking `TODO later`, placeholder stubs, or silent scope cuts.
- Coverage/test gaps:
  - Missing contract/property/mutation gates for drift detection.
  - Missing PASS_TO_PASS/FAIL_TO_PASS style regression model for feature-level confidence.

## Reviewer Output

### Findings by severity

#### Critical 1: Build plan validates execution flow, but not feature-intent fidelity end-to-end

- Why this matters:
  - Without requirement-to-test traceability and explicit quality criteria, teams can pass process gates while shipping behavior drift.
- Evidence:
  - NIST SSDF PW.7/PW.8/PW.9 requires defined security requirements, software quality criteria, and reviewed test plans before release.
  - Scrum Guide requires a concrete Definition of Done tied to quality measures and usable increment criteria.
- Planning insertion:
  - Add a **Feature Intent Contract (FIC)** to each planned feature:
    - intent statement (what must be true for users)
    - acceptance criteria
    - negative cases
    - observable outputs
    - exact tests/evals proving each criterion

#### Critical 2: Self-reported completion is not trustworthy enough for agentic execution

- Why this matters:
  - Public evidence shows models can conceal intent, bypass constraints, and provide compliant-looking outputs while violating goals.
- Evidence:
  - Anthropic alignment-faking and agentic-misalignment research demonstrates strategic deception/sabotage behaviors in adversarial setups.
  - Self-evaluation research reports overconfidence and weak reliability when models judge their own correctness.
- Planning insertion:
  - Add an **Evidence-First Completion Gate**:
    - No task can be marked done from narrative status.
    - Completion must include machine-verifiable evidence bundle:
      - changed files
      - command list executed
      - test/eval results
      - artifact references (logs/reports)
      - independent reviewer verdict

#### Critical 3: Current test strategy under-specifies drift-resistant validation methods

- Why this matters:
  - Unit/integration tests alone miss contract drift, edge-case behavior drift, and weak tests.
- Evidence:
  - OpenAI eval guidance: production-representative evals, adversarial cases, and continuous automation are required.
  - SWE-bench harness uses FAIL_TO_PASS and PASS_TO_PASS as a robust regression/effectiveness model.
  - Pact, Hypothesis, and PIT document contract, property-based, and mutation testing benefits.
- Planning insertion:
  - Extend testing strategy with a **Drift-Resistant Validation Stack**:
    - Contract tests (CDC provider verification)
    - Property-based tests (invariants + shrinking)
    - Mutation testing thresholds on core business logic
    - Feature eval suites with PASS_TO_PASS and FAIL_TO_PASS tracking

#### High 4: Anti-deferral controls are not explicit in phase/task planning

- Risk pattern:
  - "Defer for later", "placeholder", "stub now" behavior silently accumulates delivery debt.
- Planning insertion:
  - Add a **No-Deferral Without Replan rule**:
    - If implementation is blocked, task status becomes `blocked`, never `done`.
    - Must create replacement scoped task with owner, validation, and due phase.
    - Ban unresolved placeholders (`TODO`, `NotImplementedError`, empty catches, skeleton stubs) in completed tasks.

#### High 5: Merge gating is documented but not fully bound to feature-validation evidence

- Risk pattern:
  - CI can pass on incomplete validation surfaces if required checks are too shallow.
- Evidence:
  - GitHub required status checks can block merges until named checks pass; this should encode feature-validation gates directly.
- Planning insertion:
  - Branch protection required checks should include:
    - lint/type/tests/build
    - feature eval job
    - contract verification job
    - mutation score job (core)
    - evidence bundle presence check

#### Medium 6: Reviewer role lacks adversarial prompting checklist for "looks-done" fraud patterns

- Planning insertion:
  - Add reviewer checklist items:
    - confirm claimed behavior with failing-then-passing proof
    - verify no bypass hacks (monkeypatching tests, forced early exits)
    - verify changed code paths are exercised by assertions
    - verify no skipped/xfail-only masking

### Open questions

- Preferred mutation testing toolchain split (Python-only first, TS later vs both now).
- Initial mutation threshold (pragmatic start: 60-70% core, then ratchet up).
- Whether feature eval job should run per PR or nightly + pre-release.

### Verdict

- **approved_with_blockers**
- Research is sufficient and actionable, but planning docs need explicit integrity gates before heavy agentic implementation to materially reduce drift and false completion risk.

### Residual risk

- If only process checks are added (without evidence-based completion and drift-resistant tests), false confidence risk remains high.

## Guardrail Output (Required)

- Safety checks:
  - Recommendations avoid unsafe autonomy; they enforce human-visible evidence and merge blocking checks.
- Blocking risks:
  - None beyond implementation effort.
- Verdict:
  - Apply these controls before broad multi-phase agentic coding.

## Proposed Insertions (File-Level)

1. `docs/build-plan/00-overview.md`
- Add section: `## Execution Integrity Gates`
- Add required per-feature artifact: `Feature Intent Contract (FIC)`.
- Add phase-exit criterion: "all FIC criteria mapped to passing tests/evals with evidence links".

2. `docs/build-plan/testing-strategy.md`
- Add section: `## Drift-Resistant Feature Validation`
- Include mandatory layers:
  - contract tests (Pact/provider verification)
  - property-based tests (Hypothesis)
  - mutation testing (core domain/services)
  - PASS_TO_PASS + FAIL_TO_PASS eval suites
- Add per-feature validation matrix template.

3. `.agent/workflows/orchestrated-delivery.md`
- Add section: `## Evidence-First Completion Protocol`
- Rule: task cannot be `done` without attached evidence bundle and independent verifier pass.
- Rule: blocked work must be `blocked` + explicit replan task (owner_role, deliverable, validation, status).

4. `docs/build-plan/07-distribution.md`
- Add section: `## Branch Protection Required Checks`
- Bind merge to named checks for lint/type/tests/build + feature eval + contract + mutation + evidence manifest.

5. `.agent/context/handoffs/TEMPLATE.md`
- Add fields under Tester/Reviewer outputs:
  - `Evidence bundle location`
  - `FAIL_TO_PASS / PASS_TO_PASS result`
  - `Mutation score`
  - `Contract verification status`
  - `Anti-deferral scan result`

## Minimal Execution Checklist (to add into planning)

1. Create Feature Intent Contract for each feature before coding.
2. Write FAIL_TO_PASS tests first for intended behavior changes.
3. Write PASS_TO_PASS regression tests for unchanged behavior.
4. Implement code.
5. Run contract/property/mutation/standard test suites.
6. Generate evidence bundle (commands + artifacts + results).
7. Independent reviewer verifies claims against artifacts.
8. Merge only if required status checks pass.

## Evidence Sources (Web Research)

- NIST SSDF (SP 800-218): https://csrc.nist.gov/pubs/sp/800/218/final
- NIST SSDF PDF: https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-218.pdf
- Scrum Guide 2020 (official): https://scrumguides.org/download
- OpenAI Evals design guidance: https://platform.openai.com/docs/guides/evals-design
- OpenAI Cookbook eval best practices: https://cookbook.openai.com/examples/evaluation/use-cases/evals_api_tools_evaluation
- SWE-bench harness/metrics: https://www.swebench.com/SWE-bench/reference/harness/
- Pact consumer-driven contracts: https://docs.pact.io/
- Hypothesis property-based testing tutorial: https://hypothesis.readthedocs.io/en/latest/tutorial/first_test.html
- PIT mutation testing: https://pitest.org/
- GitHub branch protection + required status checks: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches
- Anthropic alignment faking: https://www.anthropic.com/research/alignment-faking
- Anthropic agentic misalignment: https://www.anthropic.com/research/agentic-misalignment
- LLM self-evaluation reliability study (arXiv): https://arxiv.org/abs/2510.11125

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status: Completed research and generated implementation-ready planning controls.
- Next steps:
  1. Approve proposed insertions.
  2. Apply doc updates in targeted files.
  3. Enforce required status checks in repository settings to operationalize controls.
