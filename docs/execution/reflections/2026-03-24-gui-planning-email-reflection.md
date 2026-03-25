# Reflection: GUI Planning + Email Provider Settings

**Date:** 2026-03-24
**MEUs:** MEU-70 (gui-planning), MEU-73 (gui-email-settings)
**Phase:** 6C (MEU-70), 6F (MEU-73)

---

## What Worked Well

- **Singleton pattern reuse**: `EmailProviderModel` (id=1) followed the exact same pattern as `MarketProviderSettingModel`, making the implementation predictable and fast.
- **Dependency injection consistency**: `EmailProviderService` received UoW + encryption adapter via constructor — zero changes to the FastAPI app startup pattern.
- **Route shadowing prevention**: Registering `email_settings_router` before `settings_router` (which has a `/{key}` catch-all) was a non-obvious correctness requirement that was caught proactively.
- **MEU-70 speed**: Position calculator `data-testid` fix was surgical — in and out in one edit.

---

## What Went Wrong / Lessons Learned

### 1. Core→Infra Dependency Violation (F7 — Low, but Late)
`email_provider_service.py` initially imported `SqlAlchemyEmailProviderRepository`, `EmailProviderModel`, `encrypt_api_key`, and `decrypt_api_key` from `zorivest_infra`. This violates the AGENTS.md dependency rule ("Domain → Application → Infrastructure. Never import infra from core."). The fix required adding `save_config(data, password_encrypted)` to the repo layer so model construction stays in infra.

**New rule**: Before writing any service in `zorivest_core`, scan its import list and reject all `zorivest_infra` imports. Services should only see ports/protocols.

### 2. Encryption Test Was Too Shallow (F5 — Medium)
The initial `test_fernet_encryption_at_rest` only checked `has_password=True` and `"password" not in config`. This proves the API surface but not the stored representation. A test that reads the raw database row and checks that `row.password_encrypted != b"plaintext-secret"` is the actual encryption-at-rest proof.

**New rule**: Encryption tests must read the storage layer directly. Service-level assertions are necessary but not sufficient for "encrypted at rest" claims.

### 3. Evidence Drift Accumulated Over Correction Rounds (F6 — Medium, recurring)
After adding 5 new tests in corrections, several evidence artifacts were updated (scope line, commands table) but the Changed Files descriptions and FAIL_TO_PASS section still reflected the original 16-test count. Evidence consistency across all sections of the handoff requires a final consistency sweep before marking corrections complete.

**New rule**: After each corrections pass, do a sweep: frontmatter → scope → commands → Changed Files descriptions → FAIL_TO_PASS. Every count reference must agree.

### 4. `SimpleNamespace` Cannot Be Session-Added (SQLAlchemy)
Attempted to remove the `EmailProviderModel` import from core service by using `types.SimpleNamespace()` as a stand-in. Worked for attribute access but fails at `session.add(config)` because SQLAlchemy requires a mapped instance. Correct fix is a `save_config(data, enc)` method on the repo.

**New rule**: Removing model imports from services requires pushing object construction into the repo (infra layer), not substituting a plain namespace object.

---

## Rule Adherence Check (Top 10)

| Rule | Adhered? | Notes |
|------|----------|-------|
| Read build plan section before implementing | ✅ | `06f-gui-settings.md §Email Provider` consulted |
| No infra imports in core | ❌ → ✅ | Violated initially; fixed in corrections (F7) |
| Encryption tests read storage layer | ❌ → ✅ | Shallow test initially; strengthened in corrections (F5) |
| Evidence counts consistent across all sections | ❌ → ✅ | Required 3 additional corrections rounds (F6) |
| Use `git commit -m` (never bare) | ✅ | Used agent-commit.ps1 script |
| Singleton pattern for single-config rows | ✅ | id=1 pattern followed exactly |
| Register specific routes before catch-all generic route | ✅ | `email_settings_router` before `settings_router` |
| Return `has_password: bool` not raw password | ✅ | AC-E1 verified in all code paths |
| Conventional commit message format | ✅ | `feat(meu-73):` prefix |
| Update meu-registry + BUILD_PLAN on completion | ✅ | Both updated to ✅ |

**Rule adherence: 80%** (2 rules violated initially, both resolved in corrections)

---

## Metrics

- **Tests added**: 21 (12 Python [10 unit + 2 integration], 9 Vitest)
- **Review rounds**: 3 correction passes (Round 1: F1–F4; Round 2: F5–F7; Round 3: stale inventory rows; Round 4: FAIL_TO_PASS count)
- **Dominant finding category**: Evidence-quality drift (stale counts, incomplete FAIL_TO_PASS coverage, overstated claims)
- **Files changed**: 17 (12 backend, 3 frontend, 2 test)
