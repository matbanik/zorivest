# Task Handoff

## Task

- **Date:** 2026-02-18
- **Task slug:** build-plan-settings-validation-critical-review
- **Owner role:** reviewer
- **Scope:** Critical review of updated build-plan contracts for settings validation, cache integration, REST 422 behavior, and GUI validation error handling.

## Inputs

- User request:
  - Review recent build-plan updates in `02a-backup-restore.md`, `04-rest-api.md`, and `06f-gui-settings.md`.
  - Create a new critical-review handoff in `.agent/context/handoffs`.
- Specs/docs referenced:
  - `docs/build-plan/02a-backup-restore.md`
  - `docs/build-plan/04-rest-api.md`
  - `docs/build-plan/06f-gui-settings.md`
  - `docs/build-plan/06a-gui-shell.md`
  - `docs/build-plan/02-infrastructure.md`
  - `docs/build-plan/01a-logging.md`
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
  - `.agent/context/handoffs/2026-02-18-build-plan-settings-validation-critical-review.md` (new)
- Design notes:
  - Documentation-only review artifact; no runtime code changes.
- Commands run:
  - `rg -n` for contract tracing across updated docs
  - `Get-Content` with line numbering for evidence capture
  - `git diff -- docs/build-plan/04-rest-api.md docs/build-plan/06f-gui-settings.md docs/build-plan/02a-backup-restore.md`
- Results:
  - Multiple contract regressions identified in current settings validation and cache design.

## Tester Output

- Commands run:
  - Documentation consistency inspection only.
- Pass/fail matrix:
  - Not applicable (no executable code changed).
- Repro failures:
  - Not applicable.
- Coverage/test gaps:
  - Current test contracts do not verify the all-or-nothing persistence guarantee or per-key error payload shape for all failure classes.

## Reviewer Output

- Findings by severity:

  - **Critical:** New unknown-key rejection breaks existing settings namespace contracts (`ui.*`, `notification.*`) used by GUI pages.
    - Evidence:
      - Settings routes are documented for UI state + notification persistence: `docs/build-plan/04-rest-api.md:180`.
      - GUI shell writes namespaced keys like `ui.theme` and `notification.*` through `PUT /settings`: `docs/build-plan/06a-gui-shell.md:31`, `docs/build-plan/06a-gui-shell.md:162`, `docs/build-plan/06a-gui-shell.md:166`.
      - Validator now hard-rejects any unknown key: `docs/build-plan/02a-backup-restore.md:243`, `docs/build-plan/02a-backup-restore.md:245`.
      - API contract explicitly expects unknown key -> 422: `docs/build-plan/04-rest-api.md:255`, `docs/build-plan/04-rest-api.md:257`.
      - The new default registry enumerates only 16 keys and does not include the documented `ui.*`/`notification.*` namespace: `docs/build-plan/02a-backup-restore.md:43`, `docs/build-plan/02a-backup-restore.md:58`.
    - Risk:
      - Existing settings writes will fail at runtime once validation is enforced, causing preference persistence regressions across GUI workflows.
    - Recommendation:
      - Either (A) include all existing settings keys in `SettingSpec` registry before enabling unknown-key rejection, or (B) scope strict validation to managed prefixes and preserve backward-compatible pass-through for legacy keys.

  - **Critical:** Cache integration can return shape-inconsistent payloads from `GET /settings/{key}` depending on call order.
    - Evidence:
      - Cache stores `dict[str, Any]` and `get()` returns `Any`: `docs/build-plan/02a-backup-restore.md:361`, `docs/build-plan/02a-backup-restore.md:366`.
      - `SettingsService.get()` returns cached value directly despite signature `Optional[ResolvedSetting]`: `docs/build-plan/02a-backup-restore.md:413`, `docs/build-plan/02a-backup-restore.md:417`.
      - `get_all()` caches raw DB map (`dict[str, str]`) from `_load_all_from_db()`: `docs/build-plan/02a-backup-restore.md:420`, `docs/build-plan/02a-backup-restore.md:425`, `docs/build-plan/02a-backup-restore.md:426`.
      - REST doc still models single-setting response as structured object (`key`, `value`, `value_type`): `docs/build-plan/04-rest-api.md:193`, `docs/build-plan/04-rest-api.md:196`, `docs/build-plan/04-rest-api.md:216`.
    - Risk:
      - API response shape becomes non-deterministic (raw value vs structured object), leading to client breakage and difficult-to-debug cache-order bugs.
    - Recommendation:
      - Split cache layers by contract (`/settings`, `/settings/{key}`, `/settings/resolved`) or cache only canonical `SettingResponse` objects for single-key reads.

  - **High:** Boolean validation is not strict; invalid tokens are silently accepted.
    - Evidence:
      - Bool parser maps any non-matching string to `False` instead of raising: `docs/build-plan/02a-backup-restore.md:172`, `docs/build-plan/02a-backup-restore.md:173`.
      - Type stage trusts parser success for validation: `docs/build-plan/02a-backup-restore.md:277`, `docs/build-plan/02a-backup-restore.md:280`.
      - Multiple bool settings rely on type-check-only validation: `docs/build-plan/02a-backup-restore.md:70`, `docs/build-plan/02a-backup-restore.md:76`.
    - Risk:
      - Inputs like `"not-a-bool"` will be accepted and coerced to false, undermining 422-based user feedback and causing silent state corruption.
    - Recommendation:
      - Make bool parsing strict (`true/false/1/0/yes/no` only) and raise `ValueError` for unknown literals; add tests for invalid bool tokens.

  - **High:** Passphrase contract remains internally inconsistent in Phase 2A restore flow.
    - Evidence:
      - Restore sequence still says to prompt for passphrase: `docs/build-plan/02a-backup-restore.md:599`.
      - Backup endpoints specify session-held passphrase with no per-call passphrase parameter: `docs/build-plan/02a-backup-restore.md:763`, `docs/build-plan/02a-backup-restore.md:776`.
      - GUI behavior also states no second passphrase prompt: `docs/build-plan/06f-gui-settings.md:483`.
    - Risk:
      - Teams can implement conflicting UX/API behavior (prompt vs session auth), causing restore/verify flow drift.
    - Recommendation:
      - Update Step 2A.4 sequence to match the session-unlock model and replace passphrase prompt with re-auth/session-refresh branch.

  - **Medium:** REST code sample for 422 handling references `SettingsValidationError` without import.
    - Evidence:
      - Imports include `SettingsService` only: `docs/build-plan/04-rest-api.md:188`.
      - Exception handler uses `SettingsValidationError`: `docs/build-plan/04-rest-api.md:234`.
    - Risk:
      - Direct implementation from doc will fail at runtime (`NameError`), reducing trust in the contract snippet.
    - Recommendation:
      - Add explicit import path for `SettingsValidationError` in the route snippet.

  - **Medium:** New validation tests do not fully prove per-key error contract or all-or-nothing behavior.
    - Evidence:
      - Only one negative test checks `detail.errors` key mapping: `docs/build-plan/04-rest-api.md:247`.
      - Other 422 tests assert only status code: `docs/build-plan/04-rest-api.md:252`, `docs/build-plan/04-rest-api.md:257`.
      - No test verifies mixed valid+invalid payload leaves DB unchanged.
    - Risk:
      - Regressions in error payload shape and transactional semantics may pass unnoticed.
    - Recommendation:
      - Add e2e test: submit mixed payload (`valid + invalid`), assert 422 with per-key errors and verify no setting persisted.

- Open questions:
  - Is `PUT /settings` now intended to be strict allowlist-only, or should generic UI preference keys remain supported?
  - Should `SettingsCache` serve only one endpoint contract (`resolved` or `raw`) instead of mixed read paths?
  - Should restore flow ever prompt passphrase directly, or always rely on session re-auth only?

- Verdict:
  - Direction is improved, but **not implementation-safe yet** due two critical contract regressions and unresolved passphrase-flow inconsistency.

- Residual risk:
  - If implemented as-is, likely outcomes are broken preference persistence, nondeterministic settings API payloads, and silent boolean coercion bugs.

## Guardrail Output (If Required)

- Safety checks:
  - Documentation-only review output.
- Blocking risks:
  - No runtime changes in this task; blockers are design-contract level only.
- Verdict:
  - Safe to proceed with targeted doc correction before implementation.

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status:
  - Critical review completed and documented.
- Next steps:
  1. Resolve unknown-key policy and backward compatibility for existing settings namespaces.
  2. Correct cache contract so single-key and bulk settings responses remain type/shape stable.
  3. Tighten bool validation and expand e2e tests for all-or-nothing + per-key 422 payload guarantees.
