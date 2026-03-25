# Task: GUI Planning + Email Settings
# MEUs: MEU-70 + MEU-73 | Date: 2026-03-24

---

## MEU-70 — gui-planning: Fix Failures & Sign Off

| Field | Value |
|---|---|
| **Owner role** | coder → tester |
| **Deliverable** | All 25+ planning.test.tsx suites PASS; position-size.test.ts PASS |
| **Status** | ✅ complete |

### Steps

- [x] Run vitest to expose exact failures (Cwd: `p:\zorivest\ui`)
- [x] Fix C2: add `data-testid="calc-copy-shares-btn"` copy button to `PositionCalculatorModal.tsx`
- [x] Fix any additional implementation gaps revealed by test run
- [x] Re-run vitest — confirm 0 failures
- [x] Run E2E Wave 4 gate — position-size.test.ts PASS
- [x] Write handoff: `.agent/context/handoffs/090-2026-03-24-gui-planning-bp06cs6.md`

---

## MEU-73 — gui-email-settings: Full Build

| Field | Value |
|---|---|
| **Owner role** | coder → tester |
| **Deliverable** | Email config CRUD + test-send; `/settings/email` route live; all tests PASS |
| **Status** | ✅ complete |

### Steps — Backend

- [x] Add `EmailProviderModel` to `models.py` (singleton id=1, `email_provider` table)
- [x] Add `EmailProviderRepository` Protocol to `ports.py` + `UnitOfWork` slot
- [x] Wire `SqlAlchemyEmailProviderRepository` into `unit_of_work.py` (class body + `__enter__`)
- [x] Create `email_provider_repository.py` (Fernet encrypt/decrypt on password field)
- [x] Create `email_provider_service.py` — `get_config` (has_password bool), `save_config` (Fernet), `test_connection` (STARTTLS/SSL)
- [x] Create `routes/email_settings.py` — prefix `/api/v1/settings/email`
- [x] Wire lifespan: `email_settings_router` registered **before** `settings_router`; `app.state.email_provider_service` constructed
- [x] Add `get_email_provider_service` to `dependencies.py`
- [x] Write `tests/unit/test_api_email_settings.py` (AC-E1 through AC-E5) — 10/10 pass

### Steps — Frontend

- [x] Create `EmailSettingsPage.tsx` — presets, SMTP fields, STARTTLS/SSL radio, has_password indicator, test+save actions
- [x] Add `settingsEmailRoute` at `/settings/email` to `router.tsx`
- [x] Add "Email Provider" nav item to `SettingsLayout.tsx` (Data Sources section)
- [x] Write `EmailSettingsPage.test.tsx` (AC-E6 through AC-E10) — 9/9 pass

### Steps — Finalization

- [x] Regenerate `openapi.committed.json`
- [x] Full Python regression — 1623/1624 pass (1 pre-existing flaky: `test_unlock_propagates_db_unlocked`)
- [x] pyright: 0 errors | ruff: 0 errors | TypeScript: clean
- [x] Count tests updated: `test_ports.py` (18→19), `test_models.py` (30→31)
- [x] Update `meu-registry.md`: MEU-73 → ✅ 2026-03-25
- [x] Update `docs/BUILD_PLAN.md`: MEU-73 → ✅
- [x] Write handoff: `.agent/context/handoffs/091-2026-03-24-gui-email-settings-bp06fs2.md`
- [x] Write reflection: `docs/execution/reflections/2026-03-24-gui-planning-email-reflection.md`
- [x] Update `docs/execution/metrics.md`
- [x] Proposed commit messages (see below)

### Commit Messages

```
feat(meu-70): fix position-calculator copy-shares testid

Add data-testid="calc-copy-shares-btn" to PositionCalculatorModal copy button.
Closes MEU-70. Refs: 06c-gui-planning.md

feat(meu-73): Email Provider Settings — full-stack implementation + corrections

Backend: EmailProviderModel, SqlAlchemyEmailProviderRepository (save_config dict
API keeps EmailProviderModel in infra), EmailProviderService (Fernet encrypt/decrypt,
sendmail probe email), REST API GET/PUT/POST /settings/email[/test].

Frontend: EmailSettingsPage.tsx with preset auto-fill (Outlook smtp-mail.outlook.com:587
STARTTLS, Yahoo smtp.mail.yahoo.com:465 SSL), STARTTLS/SSL security radio, has_password
indicator, test+save actions.

Tests: 12 Python (10 unit + 2 real SQLite integration proving Fernet ciphertext-at-rest
and keep-existing-password), 9 Vitest (AC-E6-E10 + Outlook/Yahoo preset tests).

Corrections: SMTP test sends probe email via sendmail; presets corrected to spec;
infra imports removed from core service (dependency rule); root OpenAPI regenerated;
evidence trail refreshed across all handoff sections.

Closes MEU-73. Refs: 06f-gui-settings.md
```
