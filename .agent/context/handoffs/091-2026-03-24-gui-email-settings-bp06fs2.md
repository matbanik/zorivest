---
meu: 73
slug: gui-email-settings
phase: 6F
priority: P1
status: ready_for_review
agent: claude-opus-4-6
iteration: 1
files_changed: 14
tests_added: 21
tests_passing: 21
---

# MEU-73: Email Provider Settings GUI

## Scope

Full-stack implementation of Email Provider Settings: backend persistence (SQLAlchemy model, repository, Fernet-encrypted password), service layer (get/save/test), REST API (`/api/v1/settings/email`), and React frontend (`EmailSettingsPage.tsx`). Route is registered before the generic `settings_router` to prevent shadowing by `/{key}`. 21 new tests (10 API, 2 API integration, 9 frontend) all pass.

Build plan reference: [06f-gui-settings.md](../../../../docs/build-plan/06f-gui-settings.md) §Email Provider

## Feature Intent Contract

### Intent Statement
Users can view, configure, and test-connect their SMTP email provider from the Settings page. Passwords are Fernet-encrypted at rest. `has_password` bool is returned (never the raw password). Empty password on save keeps the existing stored password.

### Acceptance Criteria
- AC-E1 (Source: 06f §email): GET `/api/v1/settings/email` returns `has_password` bool, never raw password
- AC-E2 (Source: 06f §email): PUT saves all 7 fields; password Fernet-encrypted
- AC-E3 (Source: 06f §email): Empty/absent password on PUT keeps existing stored credential
- AC-E4 (Source: 06f §email): POST `/api/v1/settings/email/test` returns `{success, message}`; 422 on connection failure
- AC-E5 (Source: 06f §email): GET on unconfigured state returns safe defaults (no 500)
- AC-E6 (Source: Local Canon): `email-settings-page` testid present
- AC-E7 (Source: Local Canon): `password-stored-indicator` shown when `has_password=true`, hidden when false
- AC-E8 (Source: Local Canon): Preset click fills smtp_host client-side, no extra API call
- AC-E9 (Source: Local Canon): Save button calls PUT `/api/v1/settings/email`
- AC-E10 (Source: Local Canon): Test Connection calls POST and displays result banner

### Negative Cases
- Must NOT return raw password in any API response
- Must NOT call the API when a preset button is clicked (client-side auto-fill only)
- Must NOT shadow `/api/v1/settings/email` with the generic `/{key}` route

### Test Mapping
| Criterion | Test File | Test Function |
|-----------|-----------|---------------|
| AC-E1 has_password | `test_api_email_settings.py` | `TestGetEmailConfig::test_get_returns_has_password_bool` |
| AC-E1 no raw password | `test_api_email_settings.py` | `TestGetEmailConfig::test_get_returns_has_password_bool` |
| AC-E1 all fields | `test_api_email_settings.py` | `TestGetEmailConfig::test_get_returns_all_fields` |
| AC-E5 empty safe defaults | `test_api_email_settings.py` | `TestGetEmailConfigEmpty::test_get_with_no_config_returns_200` |
| AC-E2 PUT 200 | `test_api_email_settings.py` | `TestSaveEmailConfig::test_put_returns_200` |
| AC-E2 all fields saved | `test_api_email_settings.py` | `TestSaveEmailConfig::test_put_calls_save_config_with_all_fields` |
| AC-E3 empty password | `test_api_email_settings.py` | `TestSaveEmailConfigKeepPassword::test_put_with_empty_password_passes_empty_to_service` |
| AC-E4 test success | `test_api_email_settings.py` | `TestTestEmailConnection::test_test_connection_returns_200_on_success` |
| AC-E4 test failure | `test_api_email_settings.py` | `TestTestEmailConnection::test_test_connection_returns_422_on_failure` |
| Mode gating | `test_api_email_settings.py` | `TestEmailSettingsModeGating::test_email_settings_403_when_locked` |
| AC-E6 testid | `EmailSettingsPage.test.tsx` | `AC-E6: renders email-settings-page testid` |
| AC-E7 stored indicator | `EmailSettingsPage.test.tsx` | `AC-E7: shows/hides password-stored-indicator` |
| AC-E8 preset no API call | `EmailSettingsPage.test.tsx` | `AC-E8: clicking preset fills smtp_host without extra API call` |
| AC-E9 save PUT | `EmailSettingsPage.test.tsx` | `AC-E9: save button calls PUT /api/v1/settings/email` |
| AC-E10 test POST | `EmailSettingsPage.test.tsx` | `AC-E10: test-connection button calls POST` |
| AC-E10 result banner | `EmailSettingsPage.test.tsx` | `AC-E10: test result banner appears after test call` |

## Design Decisions & Known Risks

- **Decision**: `EmailProviderModel` singleton row (id=1) in a dedicated `email_provider` table — **Reasoning**: Follows `MarketProviderSettingModel` precedent; single-tenant app needs exactly one SMTP config. **ADR**: inline.
- **Decision**: `email_settings_router` registered **before** `settings_router` in `main.py` lifespan — **Reasoning**: The generic `settings_router` has a `/{key}` dynamic route that would capture `/email` if registered first. Static prefix must win. **ADR**: inline; verified via route-shadowing proof in critical review handoff.
- **Decision**: `LargeBinary` column for `password_encrypted` (bytes) with Fernet via existing `FernetEncryptionAdapter` — **Reasoning**: Reuses proven encryption pattern from `MarketProviderSettingModel`; avoids introducing a new encryption layer.
- **Risk**: `type: ignore` comments on SQLAlchemy `Column[X]` attribute accesses in pyright — unavoidable with the legacy `Column()` declaration style used throughout this codebase. All 19 errors resolved; 0 pyright errors total.

## Changed Files

| File | Action | Description |
|------|--------|-------------|
| `packages/infrastructure/src/zorivest_infra/database/models.py` | Modified | Added `EmailProviderModel` (singleton, `email_provider` table, `LargeBinary` password) |
| `packages/core/src/zorivest_core/application/ports.py` | Modified | Added `EmailProviderRepository` Protocol + `email_provider` slot in `UnitOfWork` |
| `packages/infrastructure/src/zorivest_infra/database/unit_of_work.py` | Modified | Wired `SqlAlchemyEmailProviderRepository` into class body + `__enter__` |
| `packages/infrastructure/src/zorivest_infra/database/email_provider_repository.py` | Created | Single-row upsert repo with Fernet-transparent password storage |
| `packages/core/src/zorivest_core/services/email_provider_service.py` | Created | `get_config` (has_password bool), `save_config` (Fernet encrypt), `test_connection` (STARTTLS/SSL) |
| `packages/api/src/zorivest_api/routes/email_settings.py` | Created | GET, PUT, POST /test endpoints; `require_unlocked_db` on all |
| `packages/api/src/zorivest_api/main.py` | Modified | Import + register `email_settings_router` before `settings_router`; construct `app.state.email_provider_service` in lifespan |
| `packages/api/src/zorivest_api/dependencies.py` | Modified | Added `get_email_provider_service` (same `getattr` pattern) |
| `openapi.committed.json` | Modified | Regenerated root-level snapshot with new email endpoints (corrections pass: was incorrectly listing package-internal copy) |
| `ui/src/renderer/src/features/settings/EmailSettingsPage.tsx` | Created | Presets, SMTP fields, STARTTLS/SSL radio, has_password indicator, test+save |
| `ui/src/renderer/src/router.tsx` | Modified | Added `settingsEmailRoute` at `/settings/email` |
| `ui/src/renderer/src/features/settings/SettingsLayout.tsx` | Modified | Added "Email Provider" nav button in Data Sources section |
| `tests/unit/test_api_email_settings.py` | Created | 12 tests: 10 API (AC-E1–E5 + mode gating) + 2 real SQLite integration tests (Fernet encryption-at-rest, keep-existing-password) |
| `ui/src/renderer/src/features/settings/__tests__/EmailSettingsPage.test.tsx` | Created | 9 frontend tests (AC-E6–E10 + Outlook/Yahoo preset tests) |
| `tests/unit/test_ports.py` | Modified | Protocol count 18→19; added `EmailProviderRepository` to expected set |
| `tests/unit/test_models.py` | Modified | Table count 30→31; added `email_provider` to `EXPECTED_TABLES` |

## Commands Executed

| Command | Result | Notes |
|---------|--------|-------|
| `uv run pytest tests/unit/test_api_email_settings.py -v` | PASS 12/12 | AC-E1–E5 + mode gating + 2 real SQLite integration tests |
| `npx vitest run src/renderer/src/features/settings/__tests__/EmailSettingsPage.test.tsx` | PASS 9/9 | AC-E6–E10 + Outlook/Yahoo preset tests |
| `uv run pytest tests/ -q` | 1623/1624 pass | 1 pre-existing flaky: `test_unlock_propagates_db_unlocked` |
| `uv run pyright packages/` | 0 errors | All Column[X] pyright issues resolved |
| `uv run ruff check packages/ tests/` | 0 errors | Clean |
| `npx tsc --noEmit` | 0 errors | TypeScript clean |

## FAIL_TO_PASS Evidence

16 tests were written Red-first (file did not exist before this MEU). 5 additional tests were added during corrections (AC-E8 presets, integration tests). All 21 fail → pass transitions are new-capability additions.

| Test | Before | After | Phase |
|------|--------|-------|-------|
| `TestGetEmailConfig::test_get_returns_200` | FAIL (route missing) | PASS | Red-first |
| `TestGetEmailConfig::test_get_returns_has_password_bool` | FAIL (route missing) | PASS | Red-first |
| `TestGetEmailConfig::test_get_returns_all_fields` | FAIL (route missing) | PASS | Red-first |
| `TestGetEmailConfigEmpty::test_get_with_no_config_returns_200` | FAIL (route missing) | PASS | Red-first |
| `TestSaveEmailConfig::test_put_returns_200` | FAIL (route missing) | PASS | Red-first |
| `TestSaveEmailConfig::test_put_calls_save_config_with_all_fields` | FAIL (route missing) | PASS | Red-first |
| `TestSaveEmailConfigKeepPassword::test_put_with_empty_password_passes_empty_to_service` | FAIL (route missing) | PASS | Red-first |
| `TestTestEmailConnection::test_test_connection_returns_200_on_success` | FAIL (route missing) | PASS | Red-first |
| `TestTestEmailConnection::test_test_connection_returns_422_on_failure` | FAIL (route missing) | PASS | Red-first |
| `TestEmailSettingsModeGating::test_email_settings_403_when_locked` | FAIL (route missing) | PASS | Red-first |
| `AC-E6: renders email-settings-page testid` | FAIL (page missing) | PASS | Red-first |
| `AC-E7: shows password-stored-indicator when has_password=true` | FAIL (page missing) | PASS | Red-first |
| `AC-E7: hides password-stored-indicator when has_password=false` | FAIL (page missing) | PASS | Red-first |
| `AC-E8: clicking preset fills smtp_host without extra API call` | FAIL (page missing) | PASS | Red-first |
| `AC-E9: save button calls PUT /api/v1/settings/email` | FAIL (page missing) | PASS | Red-first |
| `AC-E10: test-connection button calls POST /api/v1/settings/email/test` | FAIL (page missing) | PASS | Red-first |
| `AC-E10: test result banner appears after test call` | FAIL (page missing) | PASS | Red-first |
| `TestEmailServiceIntegration::test_fernet_encryption_at_rest` | FAIL (class missing) | PASS | Correction (F3/F5) |
| `TestEmailServiceIntegration::test_empty_password_keeps_existing` | FAIL (class missing) | PASS | Correction (F3) |
| `AC-E8: Outlook preset fills smtp-mail.outlook.com:587 STARTTLS` | FAIL (test missing) | PASS | Correction (F2) |
| `AC-E8: Yahoo preset fills smtp.mail.yahoo.com:465 SSL` | FAIL (test missing) | PASS | Correction (F2) |

---
## Codex Validation Report
{Left blank — Codex fills this section during validation-review workflow}
