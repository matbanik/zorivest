# Task Handoff

## Task

- **Date:** 2026-03-06
- **Task slug:** docs-inspiration-relocation
- **Owner role:** orchestrator
- **Scope:** move selected reference docs from `docs/` to `_inspiration/`, repair `.agent` / `docs/build-plan` references, and normalize remaining stale `_inspiration/` links

## Inputs

- User request:
  Move these files from `docs/` to `_inspiration/` and correct references in `.agent` files or build-plan files:
  `_tjs_inspired_features.md`, `_todo_considerations.txt`, `DESIGN_PROPOSAL.md`, `APPLICATION_PURPOSE.md`, `TRADER_READINESS_PROTOCOL.md`, `AI_IMPROVEMENT_DIVIDEND.md`, `agentic-coding-research.md`, `_SCHEDULER_EMAIL_SERVICE_RESEARCH.md`, `API_INTEGRATION_RESEARCH.md`, `_RELEASE_PROCESS.md`, `_notes-architecture.md`, `_versioning-release-architecture.md`, `_backup-restore-architecture.md`, `_settings-architecture.md`, `_security-architecture.md`, `_logging-architecture.md`
- Specs/docs referenced:
  `AGENTS.md`, `SOUL.md`, `.agent/context/current-focus.md`, `.agent/context/known-issues.md`, `.agent/context/handoffs/TEMPLATE.md`
- Constraints:
  Do not disturb unrelated dirty worktree changes. Update only the requested reference surface unless broader edits are explicitly requested.

## Role Plan

1. orchestrator
2. coder
3. tester
4. reviewer
- Optional roles: researcher, guardrail

## Coder Output

- Changed files:
  - Moved 16 files from `docs/` to `_inspiration/`
  - Updated:
    - `docs/build-plan/00-overview.md`
    - `docs/build-plan/01a-logging.md`
    - `docs/build-plan/02a-backup-restore.md`
    - `docs/build-plan/06b-gui-trades.md`
    - `docs/build-plan/06c-gui-planning.md`
    - `docs/build-plan/06d-gui-accounts.md`
    - `docs/build-plan/06e-gui-scheduling.md`
    - `_inspiration/_SCHEDULER_EMAIL_SERVICE_RESEARCH.md`
    - `_inspiration/import_research/Build Plan Expansion Ideas.md`
    - `.agent/context/current-focus.md`
- Design notes:
  - `_inspiration/` is now the canonical home for the moved reference docs.
  - `docs/build-plan/` links were rewritten from `../*.md` to `../../_inspiration/*.md`.
  - Remaining absolute `file:///p:/zorivest/...` links were normalized to relative Markdown links inside `_inspiration/`.
  - No `.agent` files referenced the moved files at the time of verification.
- Commands run:
  - `Get-Content -Raw SOUL.md`
  - `Get-Content -Raw .agent/context/current-focus.md`
  - `Get-Content -Raw .agent/context/known-issues.md`
  - `rg --files docs _inspiration | rg "(...target files...)$"`
  - `rg -n --glob ".agent/**" --glob "docs/build-plan/**" "(...target files...)" .`
  - `rg -n "(...target files...)" .`
  - `Move-Item` loop for the 16 requested files
  - post-move `rg` verification for `.agent` and `docs/build-plan`
  - final `rg` verification for stale absolute `file:///p:/zorivest/...` links and `docs/...` references
- Results:
  - All 16 requested files were moved successfully.
  - All requested `.agent` / `docs/build-plan` path fixes were applied.
  - Remaining stale links in `_inspiration/` were normalized.
  - `docs/` no longer contains any of the moved files.

## Tester Output

- Commands run:
  - reference discovery and post-change `rg` verification only
- Pass/fail matrix:
  - Move operation: PASS
  - `.agent` stale references to moved files: PASS (none found)
  - `docs/build-plan` stale references to old `docs/` paths: PASS
  - `_inspiration` stale absolute/file-root references: PASS
  - destination presence in `_inspiration/`: PASS
- Repro failures:
  - none
- Coverage/test gaps:
  - No unit/integration test suite was run; this was a documentation/file-path refactor only.
- Evidence bundle location:
  - git diff + repository state
- FAIL_TO_PASS / PASS_TO_PASS result:
  - Not applicable for this documentation relocation task
- Mutation score:
  - Not applicable
- Contract verification status:
  - Requested contract satisfied

## Reviewer Output

- Findings by severity:
  - None for the requested scope after normalization.
- Open questions:
  - none
- Verdict:
  - Requested change completed and verified
- Residual risk:
  - Low: future docs added outside the checked patterns could still introduce hard-coded absolute workspace paths.
- Anti-deferral scan result:
  - No requested work deferred.

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status:
  Completed the requested relocation from `docs/` to `_inspiration/`, repaired all matching `.agent` / `docs/build-plan` references, and normalized the remaining stale `_inspiration/` links found in verification.
- Next steps:
  No immediate follow-up required for this path-normalization task.
