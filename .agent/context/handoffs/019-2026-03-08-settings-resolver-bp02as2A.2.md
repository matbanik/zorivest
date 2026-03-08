# Task Handoff — MEU-18 Settings Resolver

## Task

- **Date:** 2026-03-08
- **Task slug:** settings-resolver
- **Owner role:** coder
- **Scope:** MEU-18 — Settings Resolver (build-priority-matrix item 12, 02a-backup-restore.md §2A.2)

## Inputs

- User request: Implement three-tier settings resolution, validation pipeline, TTL cache, service orchestration, and 2 new repository ports
- Specs/docs referenced: `02a-backup-restore.md` §2A.2 L131-203 (resolver), §2A.2b L205-370 (validator), §2A.2c L372-430 (cache), §2A.2d L432-480 (service)
- Constraints: Pure domain logic (no I/O in resolver/validator/cache). Security validation rejects path traversal, SQL injection, script injection. Dynamic key glob matching for `ui.panel.*.collapsed`.

## Role Plan

1. coder
2. tester
- Optional roles: reviewer, guardrail (deferred to project-level review)

## Coder Output

- Changed files:

| File | Change |
|------|--------|
| `packages/core/src/zorivest_core/domain/settings_resolver.py` | NEW — `ResolvedSetting` dataclass, `SettingsResolver` (three-tier resolve, type parsing, exportability check) |
| `packages/core/src/zorivest_core/domain/settings_validator.py` | NEW — `ValidationResult`, `SettingsValidationError`, `SettingsValidator` (type→format→security pipeline, glob pattern resolution, bulk validation) |
| `packages/core/src/zorivest_core/domain/settings_cache.py` | NEW — `SettingsCache` (thread-safe TTL cache with Lock, populate/invalidate, stale detection) |
| `packages/core/src/zorivest_core/services/settings_service.py` | NEW — `SettingsService` (get, get_all_resolved, bulk_upsert with validation, reset_to_default, cache integration) |
| `packages/core/src/zorivest_core/application/ports.py` | MODIFIED — added `SettingsRepository` (get, get_all, bulk_upsert, delete), `AppDefaultsRepository` (get, get_all); extended `UnitOfWork` with settings + app_defaults attributes |
| `tests/unit/test_settings_resolver.py` | NEW — 13 tests |
| `tests/unit/test_settings_validator.py` | NEW — 17 tests |
| `tests/unit/test_settings_cache.py` | NEW — 7 tests |
| `tests/unit/test_settings_service.py` | NEW — 9 tests |
| `tests/unit/test_ports.py` | MODIFIED — protocol count 9→11, UoW settings+app_defaults attr assertions |

- Design notes:
  - `SettingsValidator._resolve_spec()` implements glob pattern fallback for dynamic keys
  - Security regex patterns compiled at module level for performance
  - `SettingsCache` uses `time.monotonic()` for TTL to avoid wall clock issues
  - `SettingsService` uses fake repos in tests (no full SQLAlchemy dependency)

- Commands run: `uv run pytest tests/unit/test_settings_resolver.py tests/unit/test_settings_validator.py tests/unit/test_settings_cache.py tests/unit/test_settings_service.py tests/unit/test_ports.py -v`
- Results: 70 passed / 0 failed

## Tester Output

- Commands run: `uv run pytest tests/unit/test_settings_resolver.py tests/unit/test_settings_validator.py tests/unit/test_settings_cache.py tests/unit/test_settings_service.py -v --tb=short`
- Pass/fail matrix: 46 passed / 0 failed / 0 skipped (MEU-18 tests only); 70 with ports
- Test mapping:
  - **Resolver** (13): three-tier priority (user>default>hardcoded), bool/int/float/str/json parsing, invalid parse errors, exportability (non-sensitive vs sensitive), unknown key raises
  - **Validator** (17): type check pass/fail, enum allowed_values accept/reject, min/max range reject, string length reject, log level constraint, path traversal/SQL injection/script injection rejection, dynamic key glob resolution, unknown key rejection, bulk validation, ValidationResult/Error structure
  - **Cache** (7): empty returns None, populate+get, get_all returns copy, invalidate clears, TTL staleness, fresh cache hit, empty populate returns None
  - **Service** (9): get from cache hit, get from DB fallback, hardcoded fallback, valid bulk_upsert commits, invalid raises SettingsValidationError, upsert invalidates cache, reset_to_default deletes+invalidates, get_all from cache, get_all from DB populates cache
- FAIL_TO_PASS: RED phase confirmed (import errors before implementation)
- Negative cases: invalid bool "maybe", enum "neon" rejected, min/max range violations, path traversal `../../etc/passwd`, SQL injection `'; DROP TABLE`, XSS `<script>`, unknown key rejection
- Contract verification: 3-tier resolution chain, 3-stage validation pipeline, TTL cache lifecycle, UoW 11 protocol count

## Reviewer Output

- Findings by severity: Pending Codex review
- Verdict: pending
- Anti-deferral scan: `rg "TODO|FIXME|NotImplementedError" packages/core/src/zorivest_core/domain/settings_resolver.py packages/core/src/zorivest_core/domain/settings_validator.py packages/core/src/zorivest_core/domain/settings_cache.py packages/core/src/zorivest_core/services/settings_service.py` → 0 matches

## Guardrail Output (If Required)

- Not applicable — no high-risk changes

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status: Implementation complete, awaiting Codex validation
- Next steps: Codex validates tests, code quality, security patterns, contract coverage → verdict
