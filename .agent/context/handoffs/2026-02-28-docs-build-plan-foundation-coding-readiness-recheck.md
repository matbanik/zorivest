# Task Handoff Template

## Task

- **Date:** 2026-02-28
- **Task slug:** docs-build-plan-foundation-coding-readiness-recheck
- **Owner role:** reviewer
- **Scope:** Re-check whether issues from `2026-02-28-docs-build-plan-foundation-coding-readiness-critical-review.md` were corrected.

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
- Constraints:
  - Review-only, no product doc edits.

## Role Plan

1. orchestrator
2. tester
3. reviewer
- Optional roles: researcher (not needed), guardrail (not needed)

## Coder Output

- Changed files:
  - `.agent/context/handoffs/2026-02-28-docs-build-plan-foundation-coding-readiness-recheck.md`
- Design notes:
  - No product changes; verification-only.
- Commands run:
  - targeted `rg` sweeps and numbered block reads
- Results:
  - 13 prior findings re-validated with status matrix below.

## Tester Output

- Commands run:
  - `rg -n "Unknown setting|SettingsValidator|def validate\\(|def _resolve_spec|display\\.hide_dollars|display\\.dollar_visible|display\\.hide_percentages|display\\.percent_visible|ImageRepository|get_for_trade|get_for_owner|restore_backup\\(|verify_backup\\(|_app_version|pydantic|__name__|misc\\.jsonl|app\\.jsonl|os\\.uname|Column\\(Float|journal_mode=wal|sqlite://|compression_enabled|gzip|pyright|pip-audit" docs/build-plan/01-domain-layer.md docs/build-plan/01a-logging.md docs/build-plan/02-infrastructure.md docs/build-plan/02a-backup-restore.md docs/build-plan/dependency-manifest.md`
  - numbered reads of corrected blocks in all target files
- Pass/fail matrix:
  - corrected: 9
  - partially corrected: 3
  - still open/new: 1
- Repro failures:
  - `01a-logging` snippet uses `sys.platform` but does not import `sys` in shown imports.
- Coverage/test gaps:
  - WAL requirement still not tied to a required test in Test Plan/Exit Criteria.

## Reviewer Output

- Findings by severity:

  - **High**
    - **Still open (partial correction): settings-key contract drift remains in Domain enum values.**
      - Infrastructure + 2A are now standardized on `display.hide_dollars` / `display.hide_percentages`.
      - Domain `DisplayModeFlag` still defines `dollar_visible` / `percent_visible` and says these are stored in settings.
      - This can still cause API/serialization drift unless mapped explicitly.
      - Evidence:
        - `docs/build-plan/01-domain-layer.md:191-195`
        - `docs/build-plan/02-infrastructure.md:159`
        - `docs/build-plan/02a-backup-restore.md:52-53`

  - **Medium**
    - **New regression introduced while fixing platform check: missing import for `sys`.**
      - `get_log_directory()` now uses `sys.platform == "darwin"` but `sys` is not imported in that snippet.
      - Evidence:
        - `docs/build-plan/01a-logging.md:254-259`
        - `docs/build-plan/01a-logging.md:297`

    - **Partially corrected: Float precision risk acknowledged but not resolved.**
      - Warning note was added, but model definitions still use `Float` for monetary/tax-relevant fields.
      - Evidence:
        - `docs/build-plan/02-infrastructure.md:16`
        - `docs/build-plan/02-infrastructure.md:29-33`
        - `docs/build-plan/02-infrastructure.md:231-235`
        - `docs/build-plan/02-infrastructure.md:279`
        - `docs/build-plan/02-infrastructure.md:341`
        - `docs/build-plan/02-infrastructure.md:362-364`

    - **Partially corrected: WAL test realism note added, but still not enforced in test plan/exit criteria.**
      - Good: explicit note says in-memory SQLite cannot test WAL and calls for dedicated file-based WAL test.
      - Gap: Test Plan + Exit Criteria still do not require a WAL concurrency test.
      - Evidence:
        - `docs/build-plan/02-infrastructure.md:369-377`
        - `docs/build-plan/02-infrastructure.md:400-402`
        - `docs/build-plan/02-infrastructure.md:491-499`

- Closed items (verified):
  - `F1` SettingsValidator control-flow bug fixed (`02a` validate pipeline now in method body): `docs/build-plan/02a-backup-restore.md:262-284`
  - `F3` Image repository contract alignment fixed in tests (`save(owner_type, owner_id, image)`, `get_for_owner`): `docs/build-plan/02-infrastructure.md:429`, `docs/build-plan/02-infrastructure.md:446`
  - `F4` restore/verify signature mismatch fixed (tests now use session-held passphrase model): `docs/build-plan/02a-backup-restore.md:931-937`
  - `F5` `_app_version` initialization fixed in constructor: `docs/build-plan/02a-backup-restore.md:705-710`
  - `F6` Phase-1 Pydantic contradiction fixed: `docs/build-plan/01-domain-layer.md:9`, `docs/build-plan/dependency-manifest.md:27`
  - `F7` `__name__` routing contradiction fixed to `misc.jsonl`: `docs/build-plan/01a-logging.md:119`, `docs/build-plan/01a-logging.md:128`
  - `F8` `os.uname()` removed (platform check strategy corrected): `docs/build-plan/01a-logging.md:297`
  - `F11` compression terminology fixed (removed gzip wording): `docs/build-plan/02a-backup-restore.md:57`
  - `F12/F13` dependency command issues corrected (`pyright` added, `pip-audit` duplication removed from command section): `docs/build-plan/dependency-manifest.md:31`, `docs/build-plan/dependency-manifest.md:53`

- Verdict:
  - **changes_required** (small remaining set)

- Residual risk:
  - Domain/settings key drift can still propagate into UI/API contracts.
  - Missing `sys` import keeps logging snippet non-runnable as written.
  - WAL and precision concerns remain documented but not enforced by phase gate tests.

- Anti-deferral scan result:
  - 3 partial items and 1 new regression should be patched before marking this stream complete.

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status:
  - Re-check complete; most corrections landed.
- Next steps:
  1. Align `DisplayModeFlag` values with `display.hide_*` contract (or document explicit mapping).
  2. Add missing `import sys` to logging snippet.
  3. Promote WAL file-based test to explicit Test Plan + Exit Criteria.
  4. Decide whether `Float` risk is accepted debt or Phase 2 must switch selected money columns to `Numeric`.
