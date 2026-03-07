# Task Handoff Template

## Task

- **Date:** 2026-03-07
- **Task slug:** workflow-critical-review-feedback-planning-corrections
- **Owner role:** reviewer
- **Scope:** Review the latest edits to `.agent/workflows/critical-review-feedback.md` and `.agent/workflows/planning-corrections.md` for auto-discovery correctness, workflow consistency, and repository-rule compliance

## Inputs

- User request: Review the workflow changes and create a handoff review
- Specs/docs referenced:
  - `.agent/workflows/critical-review-feedback.md`
  - `.agent/workflows/planning-corrections.md`
  - `.agent/workflows/create-plan.md`
  - `AGENTS.md`
  - `.agent/context/handoffs/TEMPLATE.md`
- Constraints:
  - Review only, no fixes in this session
  - Findings first
  - Use live file state and command output as source of truth

## Role Plan

1. orchestrator
2. tester
3. reviewer
- Optional roles: researcher, guardrail

## Coder Output

- No product changes; review-only
- Changed files:
  - `.agent/context/handoffs/2026-03-07-workflow-critical-review-feedback-planning-corrections-critical-review.md`
- Commands run:
  - `apply_patch` to add this handoff
- Results:
  - Review handoff created

## Tester Output

- Commands run:
  - `Get-Content -Raw SOUL.md`
  - `Get-Content -Raw GEMINI.md`
  - `Get-Content -Raw .agent/context/current-focus.md`
  - `Get-Content -Raw .agent/context/known-issues.md`
  - `pomera_notes search "Zorivest"`
  - `git status --short`
  - `Get-Content -Raw .agent/workflows/critical-review-feedback.md`
  - `Get-Content -Raw .agent/workflows/planning-corrections.md`
  - `Get-Content -Raw .agent/workflows/create-plan.md`
  - `Get-Content -Raw .agent/context/handoffs/TEMPLATE.md`
  - `git diff -- .agent/workflows/critical-review-feedback.md`
  - `git diff -- .agent/workflows/planning-corrections.md`
  - `Get-ChildItem .agent/context/handoffs/*.md -Exclude README.md,TEMPLATE.md | Sort-Object LastWriteTime -Descending | Select-Object -First 5 Name,LastWriteTime`
  - `Get-ChildItem .agent/context/handoffs/*.md -Exclude README.md,TEMPLATE.md | Where-Object { $_.Name -notmatch 'critical-review|recheck|corrections' } | Sort-Object LastWriteTime -Descending | Select-Object -First 3 Name,LastWriteTime`
  - `Get-ChildItem .agent/context/handoffs/*critical-review*.md, .agent/context/handoffs/*-corrections*.md, .agent/context/handoffs/*-recheck*.md | Sort-Object LastWriteTime -Descending | Select-Object -First 10 FullName,Name,LastWriteTime`
  - `Get-ChildItem docs/execution/plans -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 3 Name,LastWriteTime`
  - `rg -n "coder|fixes|planning-corrections|create-plan|notify_user|view_file|replace_file_content|multi_replace_file_content|implementation_plan\\.md|implementation-plan\\.md" .agent/workflows/critical-review-feedback.md .agent/workflows/planning-corrections.md .agent/workflows/create-plan.md`
  - Numbered `Get-Content` sweeps for:
    - `.agent/workflows/critical-review-feedback.md`
    - `.agent/workflows/planning-corrections.md`
- Pass/fail matrix:
  - Diff inspection: PASS
  - Critical-review auto-discovery dry-run: FAIL
  - Planning-corrections auto-discovery dry-run: FAIL
  - Session-discipline alignment check: FAIL
  - Corrections execution-contract alignment check: FAIL
- Repro failures:
  - Critical-review auto-discovery selects the newest handoff of any type, which currently resolves to a prior `*-critical-review-recheck.md` instead of the newest non-review work handoff
  - Planning-corrections auto-discovery emits duplicate `*-critical-review-recheck.md` rows because the glob patterns overlap
  - Both new prerequisites sections omit the mandatory `pomera_notes` preflight from `AGENTS.md`
  - Planning-corrections still points to `implementation_plan.md` and unsupported tool names (`view_file`, `multi_replace_file_content`, `replace_file_content`)
- Coverage/test gaps:
  - Review-only session; no runtime code changed
- Evidence bundle location:
  - `.agent/context/handoffs/2026-03-07-workflow-critical-review-feedback-planning-corrections-critical-review.md`
- FAIL_TO_PASS / PASS_TO_PASS result:
  - Not applicable
- Mutation score:
  - Not applicable
- Contract verification status:
  - `changes_required`

## Reviewer Output

- Findings by severity:
  1. **High:** `.agent/workflows/critical-review-feedback.md:47-60`, `.agent/workflows/critical-review-feedback.md:119-122` — the new auto-discovery is too broad to be safe. It always chooses the newest handoff of any kind as the primary review target and the newest execution-plan folder globally as secondary scope. In the current repo state, that means the workflow would review `2026-03-07-domain-entities-ports-plan-critical-review-recheck.md` instead of the newest non-review work handoff `2026-03-07-meu-2-enums.md`, and it can also pair a handoff with an unrelated plan folder. That turns "no user paths required" into silent target drift or recursive review-of-review behavior.
  2. **Medium:** `.agent/workflows/planning-corrections.md:35-45` — the new auto-discovery command uses overlapping globs: `*critical-review*.md` already matches `*-critical-review-recheck.md`, so adding `*-recheck*.md` makes recheck files appear twice. Running the exact command returned `2026-03-07-domain-entities-ports-plan-critical-review-recheck.md` two times. Because the workflow then truncates to `Select-Object -First 3`, duplicate rows can crowd the originating review out of the result set and make the "trace back to its originating review" step unreliable.
  3. **Medium:** `.agent/workflows/critical-review-feedback.md:17-25`, `.agent/workflows/planning-corrections.md:17-25`, `AGENTS.md:49-50` — the new prerequisites sections regress repository session discipline. `AGENTS.md` requires every session to read `SOUL.md`, check `pomera_notes` with `search_term: "Zorivest"`, then read current focus and known issues. Both workflows now stop at `known-issues.md` and no longer require the notes lookup; `critical-review-feedback.md` previously had that Zorivest-specific step explicitly. The standardization to match `create-plan.md` leaves all three workflow docs out of sync with the repo rule.
  4. **Medium:** `.agent/workflows/planning-corrections.md:79-100`, `.agent/workflows/planning-corrections.md:112-113`, `.agent/workflows/create-plan.md:77-85`, `AGENTS.md:101-104` — retaining the coder role is fine, but the execution contract is still not internally consistent. The workflow tells the agent to use `view_file`, `multi_replace_file_content`, and `replace_file_content`, then write an `implementation_plan.md` artifact. The repo's documented artifact name is `implementation-plan.md`, and the documented MCP surface points agents at the `text-editor` server via `get_text_file_contents`. As written, the corrections workflow is not executable end-to-end across the repo's documented agent setup.
- Open questions:
  - Should `/critical-review-feedback` exclude `*critical-review*`, `*-recheck*`, and `*-corrections*` by default when the prompt says "latest handoff," so it reviews latest work instead of latest review artifact?
  - For `/planning-corrections`, do you want the workflow to resolve a single authoritative source review first, then use recheck/corrections files only as chain context?
- Verdict:
  - `changes_required`
- Residual risk:
  - If these workflows are used as written, the repo can end up reviewing the wrong artifact, tracing the wrong review chain, and skipping session memory that AGENTS treats as mandatory. The result is false confidence rather than a deterministic review/correction loop.
- Anti-deferral scan result:
  - Findings are concrete, reproducible, and tied to exact commands and file lines; no placeholder-only objections

## Guardrail Output (If Required)

- Safety checks:
  - Not required for this docs-only review
- Blocking risks:
  - None beyond the workflow findings above
- Verdict:
  - Not applicable

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status:
  - Review complete; verdict is `changes_required`
- Next steps:
  - Narrow critical-review auto-discovery so "latest handoff" does not default to a review/recheck artifact
  - Deduplicate planning-corrections discovery and choose the originating review deterministically
  - Restore the `pomera_notes` preflight in workflow prerequisites or fix the shared prerequisite source so all workflows match `AGENTS.md`
  - Normalize planning-corrections tool/file references to the repo's documented conventions before relying on the coder phase
