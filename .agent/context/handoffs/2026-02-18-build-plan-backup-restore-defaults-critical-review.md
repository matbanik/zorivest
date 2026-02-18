# Task Handoff

## Task

- **Date:** 2026-02-18
- **Task slug:** build-plan-backup-restore-defaults-critical-review
- **Owner role:** reviewer
- **Scope:** Critical review of build-plan updates for backup/restore, settings defaults, and config export/import.

## Inputs

- User request:
  - Review recent build-plan updates for backup/restore and settings default/export/import behavior.
  - Create a critical-review handoff in `.agent/context/handoffs`.
- Specs/docs referenced:
  - `docs/build-plan/00-overview.md`
  - `docs/build-plan/02-infrastructure.md`
  - `docs/build-plan/02a-backup-restore.md`
  - `docs/build-plan/03-service-layer.md`
  - `docs/build-plan/04-rest-api.md`
  - `docs/build-plan/05-mcp-server.md`
  - `docs/build-plan/06f-gui-settings.md`
  - `docs/build-plan/build-priority-matrix.md`
  - `docs/build-plan/dependency-manifest.md`
  - `.agent/context/handoffs/TEMPLATE.md`
- Constraints:
  - Findings-first, severity-ranked, with concrete file/line evidence.
  - Focus on behavioral/security/regression risk, not style.

## Role Plan

1. orchestrator
2. reviewer
3. coder (doc output only)
4. tester (doc consistency verification)
- Optional roles: researcher, guardrail (not used)

## Coder Output

- Changed files:
  - `.agent/context/handoffs/2026-02-18-build-plan-backup-restore-defaults-critical-review.md` (new)
- Design notes:
  - Documentation-only review artifact; no runtime code changes.
- Commands run:
  - `git diff -- docs/build-plan/...`
  - `Get-Content` with line numbering for cited files
  - `rg -n` for cross-file contract tracing
- Results:
  - Cross-file contract and implementation-risk gaps identified in current docs.

## Tester Output

- Commands run:
  - Document consistency and cross-reference inspection only.
- Pass/fail matrix:
  - Not applicable (no executable code changed).
- Repro failures:
  - Not applicable.
- Coverage/test gaps:
  - Missing explicit Phase 4 e2e acceptance criteria for new backup/config/reset routes despite claiming they are implemented in Phase 4.

## Reviewer Output

- Findings by severity:

  - **Critical:** Backup verify/restore API contract requires passphrase, but GUI contract omits passphrase capture path.
    - Evidence:
      - Restore flow explicitly prompts for `backup file path + passphrase`: `docs/build-plan/02a-backup-restore.md:313`.
      - Backup verify/restore endpoints require `passphrase` request body field: `docs/build-plan/02a-backup-restore.md:460`, `docs/build-plan/02a-backup-restore.md:470`.
      - Settings GUI backup layout has no passphrase input/prompt state: `docs/build-plan/06f-gui-settings.md:445`.
      - GUI behavior for verify/restore does not define passphrase handling: `docs/build-plan/06f-gui-settings.md:470`, `docs/build-plan/06f-gui-settings.md:471`.
    - Risk:
      - Restore/verify flows are not implementable as documented, or will push teams toward ad hoc secret caching/UI workarounds.
    - Recommendation:
      - Add explicit passphrase UX + API contract (prompt timing, memory lifetime, failure states, retry/lockout).
      - If session-unlock should satisfy backup operations, remove per-call passphrase from backup endpoints and define secure server-side key handling.

  - **High:** Settings key contract drift for percent mode creates non-deterministic behavior across defaults/export/UI.
    - Evidence:
      - Phase 2A registry/export uses `display.percent_mode`: `docs/build-plan/02a-backup-restore.md:54`, `docs/build-plan/02a-backup-restore.md:353`.
      - GUI settings table uses `display.use_percent_mode`: `docs/build-plan/06f-gui-settings.md:301`.
      - Existing infrastructure comment also points to `display.percent_mode`: `docs/build-plan/02-infrastructure.md:159`.
    - Risk:
      - Reset-to-default/export/import can target a different key than the UI reads, causing silent config drift.
    - Recommendation:
      - Canonicalize one key name and patch all phase docs plus tests.
      - Add a regression test that export→import preserves the exact display mode key consumed by UI.

  - **High:** Import validation contract is weaker than export security invariant.
    - Evidence:
      - Security invariant requires `exportable == True` and `sensitivity == NON_SENSITIVE`: `docs/build-plan/02a-backup-restore.md:361`.
      - `build_export()` enforces both checks: `docs/build-plan/02a-backup-restore.md:380`.
      - `validate_import()` checks only `exportable` and ignores `sensitivity`: `docs/build-plan/02a-backup-restore.md:398`.
    - Risk:
      - Sensitive keys can be accidentally accepted on import if metadata drifts or is mis-specified.
    - Recommendation:
      - Use one shared predicate for both export and import authorization.
      - Add tests that sensitive keys are rejected even when present in import payloads.

  - **High:** Typed settings model in Phase 2A conflicts with string-only API/MCP settings boundary contract.
    - Evidence:
      - Phase 2A resolver returns typed values and config JSON example emits booleans/ints: `docs/build-plan/02a-backup-restore.md:107`, `docs/build-plan/02a-backup-restore.md:350`.
      - REST settings response currently defines value as string: `docs/build-plan/04-rest-api.md:195`.
      - MCP settings convention says all setting values are strings at API/MCP boundary: `docs/build-plan/05-mcp-server.md:253`.
    - Risk:
      - Ambiguous coercion rules between `/settings`, `/settings/resolved`, and `/config/import` can produce inconsistent persisted values and diff previews.
    - Recommendation:
      - Define canonical wire-type rules per endpoint (string-only vs typed JSON) and conversion ownership.
      - Align MCP/REST docs so typed routes are explicitly excluded from the string-only rule.

  - **Medium:** Build order overview was not fully updated for the new Phase 2A dependency.
    - Evidence:
      - Overview still states Phase 3 depends on Phase 1 and 2 only: `docs/build-plan/00-overview.md:51`.
      - Phase 3 doc now requires Phase 2A: `docs/build-plan/03-service-layer.md:3`.
      - Overview ASCII dependency chain still omits Phase 2A placement: `docs/build-plan/00-overview.md:15`.
    - Risk:
      - Planning/execution can start Phase 3 without required Phase 2A contracts complete.
    - Recommendation:
      - Update overview table and dependency diagram to include Phase 2A before Phase 3.

  - **Medium:** Duplicate section numbering in settings doc creates ambiguous references.
    - Evidence:
      - Logging section labeled `6f.5`: `docs/build-plan/06f-gui-settings.md:353`.
      - Backup section also labeled `6f.5`: `docs/build-plan/06f-gui-settings.md:422`.
    - Risk:
      - Broken anchors and ambiguous citations across handoffs/plans.
    - Recommendation:
      - Renumber sections consistently (for example, logging `6f.4`, backup `6f.5`, config `6f.6`, reset `6f.7`).

  - **Low:** `06f` output statement no longer matches endpoint usage after new pages were added.
    - Evidence:
      - Outputs claim all settings pages consume `PUT /api/v1/settings`: `docs/build-plan/06f-gui-settings.md:555`.
      - New sections consume dedicated backup/config/reset endpoints: `docs/build-plan/06f-gui-settings.md:462`, `docs/build-plan/06f-gui-settings.md:513`, `docs/build-plan/06f-gui-settings.md:531`.
    - Risk:
      - Minor implementation confusion for API integration ownership.
    - Recommendation:
      - Update outputs to reflect mixed endpoint set (`/settings`, `/settings/resolved`, `/backups`, `/config`).

- Open questions:
  - Should backup verify/restore always require an explicit passphrase entry, or rely on an already-unlocked secure session?
  - What is the canonical percent-display key: `display.percent_mode` or `display.use_percent_mode`?
  - Is the “string-only settings boundary” intended to apply only to `GET/PUT /settings`, not to `GET /settings/resolved` and config import/export routes?

- Verdict:
  - Direction is strong, but **not implementation-safe yet** due one critical and multiple high-severity contract mismatches.

- Residual risk:
  - If implemented as-is, likely outcomes are broken restore UX, settings key drift in production, and inconsistent import/export behavior across GUI/MCP/API.

## Guardrail Output (If Required)

- Safety checks:
  - Documentation-only review output.
- Blocking risks:
  - No runtime changes in this task; blockers are design-contract level only.
- Verdict:
  - Safe to proceed with targeted doc correction pass before implementation.

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status:
  - Critical review completed and documented.
- Next steps:
  1. Resolve the critical passphrase UX/API contract mismatch first.
  2. Canonicalize settings key names and typed/string wire contracts across Phases 2A/4/5/6f.
  3. Update overview dependency graph and section numbering, then run a focused reviewer pass for consistency.
