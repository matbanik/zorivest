# Task Handoff Template

## Task

- **Date:** 2026-02-15
- **Task slug:** input-index-critical-review
- **Owner role:** orchestrator
- **Scope:** critical review of `docs/build-plan/input-index.md` for missed contract issues

## Inputs

- User request: critically review `docs/build-plan/input-index.md` and identify anything missed
- Specs/docs referenced:
- `docs/build-plan/input-index.md`
- `docs/build-plan/01-domain-layer.md`
- `docs/build-plan/02-infrastructure.md`
- `docs/build-plan/03-service-layer.md`
- `docs/build-plan/04-rest-api.md`
- `docs/build-plan/05-mcp-server.md`
- `docs/build-plan/06-gui.md`
- `docs/build-plan/08-market-data.md`
- `docs/build-plan/build-priority-matrix.md`
- `docs/build-plan/domain-model-reference.md`
- Constraints:
- severity-ranked, evidence-based findings
- focus on contract and build-plan consistency

## Role Plan

1. orchestrator
2. coder
3. tester
4. reviewer
- Optional roles: researcher, guardrail

## Coder Output

- Changed files:
- `INPUT_INDEX_CRITICAL_FEEDBACK.md`
- `.agent/context/handoffs/2026-02-15-input-index-critical-review.md`
- `.agent/context/current-focus.md`
- Design notes:
- Identified additional defects missed in previous broad review, including unsupported contracts in input index and field-name drifts
- Commands run:
- `Get-Content` with line numbering for `input-index.md` and cross-referenced phase docs
- `rg -n` targeted consistency checks across build-plan files
- Results:
- Produced dedicated critical feedback with actionable remediation

## Tester Output

- Commands run:
- Documentation review only; no runtime tests executed
- Pass/fail matrix:
- N/A
- Repro failures:
- N/A
- Coverage/test gaps:
- No executable validation required for this doc-review task

## Reviewer Output

- Findings by severity:
- Critical:
- Canonical claim conflicts with unsupported OAuth/email/scheduler contracts
- Missing source file reference for `user-input-features.md`
- High:
- Calculator contract drift (`account_id`, direction-based validation)
- Tax profile field-name drift from domain model
- Duplicate-trade behavior conflict (`None` vs REST 201 response path)
- Undocumented `provider_preference` input in market-data query contract
- Medium:
- Trade plan naming/default-status drift
- Over-generalized image owner inputs for current REST route shape
- Summary stats inconsistencies
- Open questions:
- Should non-build-plan/research-only inputs live in this file or a separate appendix?
- Verdict:
- Review complete; additional gaps were found beyond previous feedback
- Residual risk:
- If not corrected, input-index may be used as an invalid implementation contract

## Guardrail Output (If Required)

- Safety checks:
- Not required
- Blocking risks:
- None beyond documented contract drifts
- Verdict:
- N/A

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status:
- Completed
- Next steps:
- Reconcile `input-index.md` with current phase contracts and separate planned/research-only inputs
