# Task Handoff Template

## Task

- **Date:** 2026-02-28
- **Task slug:** docs-build-plan-foundation-coding-readiness-rerecheck
- **Owner role:** reviewer
- **Scope:** Re-check whether issues from `2026-02-28-docs-build-plan-foundation-coding-readiness-critical-review.md` are now corrected.

## Inputs

- User request:
  - "run re-check to see if issues have been corrected"
- Specs/docs referenced:
  - `.agent/context/handoffs/2026-02-28-docs-build-plan-foundation-coding-readiness-critical-review.md`
  - `.agent/context/handoffs/2026-02-28-docs-build-plan-foundation-coding-readiness-corrections.md`
  - `docs/build-plan/01-domain-layer.md`
  - `docs/build-plan/01a-logging.md`
  - `docs/build-plan/02-infrastructure.md`
  - `docs/build-plan/02a-backup-restore.md`
  - `docs/build-plan/dependency-manifest.md`

## Role Plan

1. orchestrator
2. tester
3. reviewer

## Coder Output

- Changed files:
  - `.agent/context/handoffs/2026-02-28-docs-build-plan-foundation-coding-readiness-rerecheck.md`
- Design notes:
  - Review-only session; no product-doc edits.
- Commands run:
  - Targeted `rg` contract checks
  - Numbered file reads for corrected blocks
- Results:
  - Most findings are corrected; one consistency blocker remains.

## Tester Output

- Commands run:
  - `rg -n "DisplayModeFlag|dollar_visible|percent_visible|display\\.hide_dollars|display\\.hide_percentages|sys\\.platform|import sys|WAL|journal_mode=wal|test_wal|Exit Criteria|Test Plan|Column\\(Float|Numeric\\(|SettingsValidator|def validate\\(|def _resolve_spec" docs/build-plan/01-domain-layer.md docs/build-plan/01a-logging.md docs/build-plan/02-infrastructure.md docs/build-plan/02a-backup-restore.md`
  - Numbered block reads for all matched correction regions.
- Pass/fail matrix:
  - Prior findings closed: 12/13
  - Prior findings still open: 1/13
  - New regressions: 0

## Reviewer Output

- Findings by severity:

  - **High**
    - **Still open: internal contradiction in Phase 2 financial type plan.**
      - The new warning/resolution says key monetary/tax columns "must use `Numeric(precision=15, scale=6)`".
      - The model snippets still define those same columns with `Float` (e.g., `commission`, `realized_pnl`, `balance`, `amount`, `estimated_cost`, `net_debit_credit`).
      - Evidence:
        - `docs/build-plan/02-infrastructure.md:29-33`
        - `docs/build-plan/02-infrastructure.md:142`
        - `docs/build-plan/02-infrastructure.md:234`
        - `docs/build-plan/02-infrastructure.md:279`
        - `docs/build-plan/02-infrastructure.md:293`
        - `docs/build-plan/02-infrastructure.md:307`
        - `docs/build-plan/02-infrastructure.md:341`
        - `docs/build-plan/02-infrastructure.md:364`

- Closed items (verified):
  - `SettingsValidator` control flow fixed: `docs/build-plan/02a-backup-restore.md:262-284`
  - Settings naming alignment fixed (`hide_dollars` / `hide_percentages`): `docs/build-plan/01-domain-layer.md:193-194`, `docs/build-plan/02-infrastructure.md:159`, `docs/build-plan/02a-backup-restore.md:52-53`
  - Image repository contract alignment fixed: `docs/build-plan/01-domain-layer.md:468-471`, `docs/build-plan/02-infrastructure.md:429`, `docs/build-plan/02-infrastructure.md:446`
  - Backup signature mismatch fixed: `docs/build-plan/02a-backup-restore.md:600-614`, `docs/build-plan/02a-backup-restore.md:931-937`
  - `_app_version` initialization fixed: `docs/build-plan/02a-backup-restore.md:705-710`
  - Phase-1 Pydantic dependency contradiction fixed: `docs/build-plan/01-domain-layer.md:9`, `docs/build-plan/dependency-manifest.md:27`
  - Logging route contradiction fixed (`__name__` -> `misc.jsonl`): `docs/build-plan/01a-logging.md:119`, `docs/build-plan/01a-logging.md:128`
  - Platform check fixed and import present (`sys.platform` + `import sys`): `docs/build-plan/01a-logging.md:258`, `docs/build-plan/01a-logging.md:298`
  - WAL gating now enforced in test plan and exit criteria: `docs/build-plan/02-infrastructure.md:492`, `docs/build-plan/02-infrastructure.md:501`
  - Compression wording corrected (no gzip claim): `docs/build-plan/02a-backup-restore.md:57`
  - Dependency manifest corrections verified (`pyright` added, pip-audit deduped in commands): `docs/build-plan/dependency-manifest.md:31`, `docs/build-plan/dependency-manifest.md:53`

- Verdict:
  - **changes_required** (single remaining high-severity inconsistency)

- Residual risk:
  - If implemented as-is, monetary columns may follow contradictory guidance, causing schema churn and migration rework during implementation.

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status:
  - Re-check complete; all but one prior issue are corrected.
- Next steps:
  1. Update Phase 2 model snippets to actually use `Numeric` where the resolution says "must use Numeric", or relax the resolution wording to match current `Float` examples.
