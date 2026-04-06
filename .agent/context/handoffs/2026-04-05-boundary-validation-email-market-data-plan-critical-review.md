# 2026-04-05 Boundary Validation Email Market Data - Plan Critical Review

> Date: 2026-04-05
> Review mode: plan
> Target plan: `docs/execution/plans/2026-04-05-boundary-validation-email-market-data/`
> Canonical review file: `.agent/context/handoffs/2026-04-05-boundary-validation-email-market-data-plan-critical-review.md`

## Scope and Correlation

- Plan review mode was selected because the user provided the plan folder artifacts directly and current file state still shows pre-implementation route/test schemas for both targets.
- Reviewed artifacts:
  - `docs/execution/plans/2026-04-05-boundary-validation-email-market-data/implementation-plan.md`
  - `docs/execution/plans/2026-04-05-boundary-validation-email-market-data/task.md`
  - `docs/build-plan/08-market-data.md`
  - `docs/build-plan/06f-gui-settings.md`
  - `docs/build-plan/input-index.md`
  - `ui/src/renderer/src/features/settings/EmailSettingsPage.tsx`
  - `ui/src/renderer/src/features/settings/__tests__/EmailSettingsPage.test.tsx`
  - `packages/api/src/zorivest_api/routes/market_data.py`
  - `packages/api/src/zorivest_api/routes/email_settings.py`
  - `packages/core/src/zorivest_core/domain/email_provider.py`
  - `packages/infrastructure/src/zorivest_infra/database/models.py`
  - `tests/unit/test_market_data_api.py`
  - `tests/unit/test_api_email_settings.py`
- Not-started confirmation:
  - `ProviderConfigRequest` and `EmailConfigRequest` are still unconstrained raw optional strings/ints in current route state (`packages/api/src/zorivest_api/routes/market_data.py:27-33`, `packages/api/src/zorivest_api/routes/email_settings.py:42-49`).
  - The proposed boundary-validation test classes do not yet exist in the current unit files.

## Findings

### High - The plan's email `security` contract is source-drifted and proposes an unsupported `NONE` value

- The plan explicitly proposes `Literal["STARTTLS", "SSL", "NONE"]` and claims the GUI currently uses "these three options" (`docs/execution/plans/2026-04-05-boundary-validation-email-market-data/implementation-plan.md:15`, `docs/execution/plans/2026-04-05-boundary-validation-email-market-data/implementation-plan.md:47`, `docs/execution/plans/2026-04-05-boundary-validation-email-market-data/implementation-plan.md:111`).
- The canonical build-plan spec defines email security as `STARTTLS / SSL`, not three values (`docs/build-plan/06f-gui-settings.md:236`), and the preset map only uses those two modes (`docs/build-plan/06f-gui-settings.md:245-250`).
- The input index also documents the field as a `radio` with `STARTTLS / SSL` only (`docs/build-plan/input-index.md:430`).
- The current GUI implementation matches the spec, not the plan note: presets map only to `STARTTLS` or `SSL`, and the rendered control iterates only `['STARTTLS', 'SSL']` (`ui/src/renderer/src/features/settings/EmailSettingsPage.tsx:21-27`, `ui/src/renderer/src/features/settings/EmailSettingsPage.tsx:167`).
- Current Python-side canonical comments also only document `STARTTLS | SSL` (`packages/core/src/zorivest_core/domain/email_provider.py:25`, `packages/infrastructure/src/zorivest_infra/database/models.py:244`).
- This is not just wording drift: if implemented as written, the plan would formalize a third persisted value the actual spec/UI do not support and mislabel that rule as `Spec`.

### High - The plan leaves `provider_preset` under-validated even though the spec treats it as a finite choice set

- The plan's only `provider_preset` hardening is "whitespace-only rejected" plus `Optional[StrippedStr] = Field(None, min_length=1)` (`docs/execution/plans/2026-04-05-boundary-validation-email-market-data/implementation-plan.md:95`, `docs/execution/plans/2026-04-05-boundary-validation-email-market-data/implementation-plan.md:108`).
- Canonical docs define `provider_preset` as a dropdown/select tied to a specific preset map, not an arbitrary free-form string (`docs/build-plan/06f-gui-settings.md:233`, `docs/build-plan/06f-gui-settings.md:245-250`, `docs/build-plan/input-index.md:427`).
- The shipped GUI also hard-codes a closed preset set: `Gmail`, `Brevo`, `SendGrid`, `Outlook`, `Yahoo`, `Custom` (`ui/src/renderer/src/features/settings/EmailSettingsPage.tsx:21-27`, `ui/src/renderer/src/features/settings/EmailSettingsPage.tsx:117`).
- As planned, payloads like `{"provider_preset":"NotARealPreset"}` would still pass boundary validation even though the field is spec-defined as a bounded choice. That means the project would leave one of the email boundary's enum-like inputs effectively unconstrained while claiming the boundary is hardened.

## Commands Executed

```powershell
rg --files docs/execution/plans/2026-04-05-boundary-validation-email-market-data .agent/context/handoffs .agent/context packages/api/src tests/unit
Test-Path 'P:\zorivest\.agent\context\handoffs\2026-04-05-boundary-validation-email-market-data-plan-critical-review.md'
rg -n "ProviderConfigRequest|EmailConfigRequest|StrippedStr|_strip_whitespace|class TestProviderConfigBoundaryValidation|class TestEmailConfigBoundaryValidation|security|password|provider_preset|rate_limit|timeout" packages/api/src/zorivest_api/routes/market_data.py packages/api/src/zorivest_api/routes/email_settings.py tests/unit/test_market_data_api.py tests/unit/test_api_email_settings.py
rg -n "8\.4|Provider Settings|/providers/\{name\}|Email|/settings/email|security|password|provider_preset|smtp_host|port|test connection" docs/build-plan/08-market-data.md docs/build-plan/06f-gui-settings.md
rg -n "BOUNDARY-GAP|MEU-BV4|MEU-BV5|market-data|email settings|F5|F6" docs/BUILD_PLAN.md .agent/context/known-issues.md .agent/context/meu-registry.md
rg -n StrippedStr packages/api/src packages/core/src tests/unit
rg -n _strip_whitespace packages/api/src packages/core/src tests/unit
rg -n "class EmailProviderService|STARTTLS|SSL|NONE|empty = keep existing|password" packages/core/src packages/infrastructure/src
rg -n "provider_preset|smtp_host|from_email|security|STARTTLS|SSL|Yahoo|Custom" docs/build-plan/input-index.md docs/build-plan/06f-gui-settings.md docs/execution/plans/2026-03-24-gui-planning-email/implementation-plan.md
rg -n "STARTTLS|SSL|NONE|security" ui packages/api/src packages/core/src tests/unit docs/execution/plans/2026-03-24-gui-planning-email
rg -n "three options|provider_preset|AC-EM4|AC-EM8|STARTTLS/SSL/NONE|Literal" docs/execution/plans/2026-04-05-boundary-validation-email-market-data/implementation-plan.md
rg -n "security: 'STARTTLS'|security: 'SSL'|\['STARTTLS', 'SSL'\]|provider_preset|PRESETS|Custom|Yahoo" ui/src/renderer/src/features/settings/EmailSettingsPage.tsx ui/src/renderer/src/features/settings/__tests__/EmailSettingsPage.test.tsx docs/build-plan/06f-gui-settings.md docs/build-plan/input-index.md packages/core/src/zorivest_core/domain/email_provider.py packages/infrastructure/src/zorivest_infra/database/models.py
rg -n "provider_preset: Optional\[str\]|security: Optional\[str\]|from_email: Optional\[str\]|class EmailConfigRequest|class ProviderConfigRequest|api_key: Optional\[str\]|api_secret: Optional\[str\]|rate_limit: Optional\[int\]|timeout: Optional\[int\]" packages/api/src/zorivest_api/routes/email_settings.py packages/api/src/zorivest_api/routes/market_data.py
```

## Plan Review Checklist

| Check | Result | Notes |
|---|---|---|
| PR-1 Plan/task alignment | Pass | `implementation-plan.md` and `task.md` describe the same two-MEU boundary project. |
| PR-2 Not-started confirmation | Pass | Current route/test state is still pre-hardening. |
| PR-3 Task contract completeness | Pass | The implementation plan task table includes task, owner, deliverable, validation, status. |
| PR-4 Validation realism | Pass with concern | Commands are concrete, but the email AC set is incomplete because one finite-choice field remains under-constrained. |
| PR-5 Source-backed planning | Fail | The plan labels `STARTTLS/SSL/NONE` as `Spec`, but the actual spec/UI/local canon only support `STARTTLS` and `SSL`. |
| PR-6 Handoff/corrections readiness | Pass | Canonical review handoff path is clear; issues are resolvable via `/planning-corrections`. |

## Open Questions / Assumptions

- The strongest unresolved follow-up is whether `from_email` should remain only non-blank or be upgraded to an explicit email-address format validator. Canonical docs call it a "Sender address" and delegate validation to the server, but the current plan does not make that rule explicit.

## Verdict

`changes_required`

## Concrete Follow-Up Actions

1. Replace the email `security` proposal with a two-value contract only: `STARTTLS` and `SSL`.
2. Update the plan note to match current UI/file state: the GUI uses radio choices for two values, not a three-option dropdown.
3. Harden `provider_preset` as a closed choice set sourced from the documented preset map (`Gmail`, `Brevo`, `SendGrid`, `Outlook`, `Yahoo`, `Custom`) and add a negative test for an unknown preset.
4. Revisit `from_email` and make an explicit source-backed decision on whether syntactic email validation belongs in this boundary-hardening project.

## Residual Risk

- If executed as written, the plan would still leave one enum-like email boundary field effectively open-ended and would document an unsupported transport-security mode as if it were canonical product behavior.

---

## Corrections Applied — 2026-04-05

**Agent:** Opus (Antigravity)
**Workflow:** `/planning-corrections`

### Finding Resolution

| # | Finding | Resolution | Evidence |
|---|---------|-----------|----------|
| F1 | `security` Literal included `NONE` | Changed to `Literal["STARTTLS", "SSL"]` | `implementation-plan.md` L111: now says `Literal["STARTTLS", "SSL"]`. Verified GUI L167: `['STARTTLS', 'SSL']`, spec 06f L236: `STARTTLS / SSL`, input-index L430: `radio STARTTLS / SSL`. |
| F2 | `provider_preset` free-form string | Changed to `Literal["Gmail", "Brevo", "SendGrid", "Outlook", "Yahoo", "Custom"]` | `implementation-plan.md` L108: now says `Literal[...]`. Verified GUI L22–27: 6 preset keys. Added AC-EM4 (unknown preset → 422) and AC-EM11 (whitespace-only preset → 422). |
| FU1 | `from_email` format question | Resolved: spec says "Sender address" `text` type. No format validation — server validates. Keep `StrippedStr`. | `input-index.md` L433: type `string`, no format constraint. `06f-gui-settings.md` L239: type `text`. |
| FU2 | Plan note claims "three options" | Merged into F1 fix — note now correctly states two-value radio. | `implementation-plan.md` L14–15: corrected text. |

### Changes Made

- `implementation-plan.md`: 9 edits across User Review, Sufficiency Table, FIC, schema description, and task table
- `task.md`: Updated BV5 test count from 10 to 11

### Verdict

`approved` — all findings resolved. Plan ready for TDD execution.
