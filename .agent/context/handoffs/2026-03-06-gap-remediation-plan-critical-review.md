# Task Handoff Template

## Task

- **Date:** 2026-03-06
- **Task slug:** gap-remediation-plan-critical-review
- **Owner role:** reviewer
- **Scope:** Review `_inspiration/agentic_cooperation_research/gap-remediation-plan.md` against the current `.agent/` and `docs/execution/` file state, then capture findings in a handoff without applying the proposed changes.

## Inputs

- User request:
  - Use `.agent/workflows/critical-review-feedback.md`
  - Review `_inspiration/agentic_cooperation_research/gap-remediation-plan.md`
  - Place the feedback document into `.agent/context/handoffs/`
- Specs/docs referenced:
  - `SOUL.md`
  - `AGENTS.md`
  - `GEMINI.md`
  - `.agent/context/current-focus.md`
  - `.agent/context/known-issues.md`
  - `.agent/workflows/critical-review-feedback.md`
  - `.agent/context/handoffs/TEMPLATE.md`
  - `_inspiration/agentic_cooperation_research/gap-remediation-plan.md`
  - `.agent/workflows/meu-handoff.md`
  - `.agent/roles/coder.md`
  - `.agent/workflows/execution-session.md`
  - `docs/execution/metrics.md`
  - `docs/execution/reflections/TEMPLATE.md`
  - `docs/execution/README.md`
  - `docs/build-plan/01-domain-layer.md`
- Constraints:
  - Findings-first review
  - Review-only; do not silently implement the remediation plan
  - Base the review on current file state, not only on the plan text

## Role Plan

1. orchestrator
2. tester
3. reviewer
4. coder
- Optional roles: researcher, guardrail

## Coder Output

- Changed files:
  - `.agent/context/handoffs/2026-03-06-gap-remediation-plan-critical-review.md`
- Design notes:
  - No product or workflow files were modified; this session only produced the review handoff.
  - The target plan is currently untracked, so the review relied on direct file-state inspection rather than `git diff`.
  - `current-focus.md` was left unchanged because this was a review-only session and no repo state was advanced.
- Commands run:
  - Documentation inspection only
- Results:
  - Findings-first review handoff created

## Tester Output

- Commands run:
  - `Get-Content -Raw SOUL.md`
  - `Get-Content -Raw .agent/context/current-focus.md`
  - `Get-Content -Raw .agent/context/known-issues.md`
  - `pomera_notes search "Zorivest"`
  - `Get-Content -Raw _inspiration/agentic_cooperation_research/gap-remediation-plan.md`
  - `Get-Content -Raw .agent/workflows/critical-review-feedback.md`
  - `Get-Content -Raw .agent/context/handoffs/TEMPLATE.md`
  - `Get-Content -Raw GEMINI.md`
  - `Get-Content -Raw .agent/workflows/meu-handoff.md`
  - `Get-Content -Raw .agent/roles/coder.md`
  - `Get-Content -Raw docs/execution/metrics.md`
  - `Get-Content -Raw .agent/workflows/execution-session.md`
  - `Get-Content -Raw docs/execution/README.md`
  - `Get-Content -Raw docs/execution/reflections/TEMPLATE.md`
  - `Get-Content` with line numbers for all files cited in findings
  - `rg -n "\.agent/skills|skills/README|SKILL\.md|progressive skill disclosure|skills are loaded" AGENTS.md GEMINI.md .agent docs`
  - `rg -n "docs/decisions|ADR-0001|Architecture Decision Record|ADR-" docs .agent`
  - `rg -n "Rule Adherence|Handoff Score|top 10 most-relevant rules|which rules were checked" docs/execution .agent`
  - `git status --short -- _inspiration/agentic_cooperation_research/gap-remediation-plan.md .agent/workflows/meu-handoff.md .agent/context/handoffs/TEMPLATE.md .agent/roles/coder.md AGENTS.md GEMINI.md docs/execution/metrics.md .agent/workflows/execution-session.md docs/execution/reflections/TEMPLATE.md docs/execution/README.md`
  - `Get-Command grep`
- Pass/fail matrix:
  - Session context load: PASS
  - Target plan inspection: PASS
  - ADR path consistency check: FAIL
  - Handoff integration coverage check: FAIL
  - Skills loading path check: FAIL
  - Metrics schema alignment check: FAIL
  - Verification portability check: FAIL
- Repro failures:
  - `_inspiration/agentic_cooperation_research/gap-remediation-plan.md` is untracked, so there is no meaningful `git diff` evidence for the target artifact yet.
  - `grep` is not available in the current PowerShell environment, so the plan's proposed instruction-count verification command is not runnable as written.
- Coverage/test gaps:
  - No live agent session was executed with the proposed remediations.
  - Findings are based on current file contracts, path conventions, and verification commands.
- Evidence bundle location:
  - `.agent/context/handoffs/2026-03-06-gap-remediation-plan-critical-review.md`
- FAIL_TO_PASS / PASS_TO_PASS result:
  - N/A for docs review
- Mutation score:
  - N/A
- Contract verification status:
  - FAIL. Several plan outcomes are not fully reachable with the edits it proposes.

## Reviewer Output

- Findings by severity:
  - **High:** `_inspiration/agentic_cooperation_research/gap-remediation-plan.md:19-23`, `_inspiration/agentic_cooperation_research/gap-remediation-plan.md:27-87`, `docs/build-plan/01-domain-layer.md:19-20` - Task 1 creates a new ADR registry at `.agent/context/decisions/`, but the existing build-plan scaffold already defines ADRs under `docs/decisions/ADR-0001-architecture.md`. Executing the plan as written creates two competing ADR homes with no authority split. That is a cross-doc contract break, not just an organizational preference.
  - **High:** `_inspiration/agentic_cooperation_research/gap-remediation-plan.md:21`, `_inspiration/agentic_cooperation_research/gap-remediation-plan.md:91-118`, `.agent/workflows/critical-review-feedback.md:217-227`, `.agent/context/handoffs/TEMPLATE.md:24-49` - The ADR remediation does not reach the handoff path the repo already uses for review work. The plan says decisions are scattered across "114+ handoff files", but it only updates `.agent/workflows/meu-handoff.md` and `.agent/roles/coder.md`. Review handoffs are explicitly created from `.agent/context/handoffs/TEMPLATE.md`, and that template has no ADR field or decision-reference slot. The stated outcome, "referenceable by both agents", is therefore incomplete.
  - **High:** `_inspiration/agentic_cooperation_research/gap-remediation-plan.md:260-309`, `AGENTS.md:43-60`, `AGENTS.md:101-111`, `GEMINI.md:37-39`, `GEMINI.md:114-129` - Task 5 is non-operational as written. It creates `.agent/skills/README.md` and describes a loading strategy, but it does not modify any startup instructions, workflow, or runtime doc that would cause an agent to read `.agent/skills/`. Current repo guidance has no `.agent/skills` references at all, so this adds a directory without changing behavior.
  - **Medium:** `_inspiration/agentic_cooperation_research/gap-remediation-plan.md:197-255`, `_inspiration/agentic_cooperation_research/gap-remediation-plan.md:233-239`, `docs/execution/reflections/TEMPLATE.md:1-112` - Task 4 updates `docs/execution/metrics.md` and `.agent/workflows/execution-session.md`, but it leaves the reflection template untouched. The plan says Rule Adherence should document which rules were checked in the reflection file, yet the current reflection template has no field for sampled rules, no Handoff Score, and no Rule Adherence slot. That makes the new metric hard to audit and creates a three-file schema drift (`metrics.md`, `execution-session.md`, `reflections/TEMPLATE.md`).
  - **Medium:** `_inspiration/agentic_cooperation_research/gap-remediation-plan.md:124-126`, `_inspiration/agentic_cooperation_research/gap-remediation-plan.md:348-355`, `_inspiration/agentic_cooperation_research/gap-remediation-plan.md:417-424` - The instruction-count success criterion is not verifiable with the proposed check. `Get-Command grep` fails in this environment, and the suggested `grep -ciE ... AGENTS.md GEMINI.md` would not produce a reliable combined actionable-instruction count anyway. A key success criterion ("<= 100" and "no duplicate instructions remain") is therefore not auditable as written.
  - **Low:** `_inspiration/agentic_cooperation_research/gap-remediation-plan.md:4` - The plan header uses machine-specific `file:///` source links. That weakens portability for future sessions and for reviewers working outside this exact workstation layout.
- Open questions:
  - Should ADRs be unified under `docs/decisions/`, or do you want a deliberate split between product ADRs and agent-workflow ADRs? If split, the authority boundary needs to be explicit.
  - If `.agent/skills/` should actually influence runtime behavior, which file should load it: `AGENTS.md`, `GEMINI.md`, or a specific workflow entrypoint?
  - Do you want the instruction-count ceiling to remain a hard success criterion, or should it be replaced with a smaller deterministic duplication checklist?
- Verdict:
  - `changes_required`
- Residual risk:
  - If this plan is executed unchanged, it will add more documentation surface area without fully changing agent behavior. The highest-risk result is parallel decision registries plus new metrics that cannot be measured consistently, which increases drift instead of reducing it.
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
  - Review completed
  - Feedback handoff created
  - No remediation plan changes were applied in this session
- Next steps:
  1. Resolve ADR location authority before implementing Task 1.
  2. Expand the ADR and skills proposals to the actual handoff/runtime entrypoints, not just the MEU template.
  3. Normalize the metrics proposal across `metrics.md`, `execution-session.md`, and `docs/execution/reflections/TEMPLATE.md`.
  4. Replace the instruction-count verification with a deterministic PowerShell- or `rg`-based check.
