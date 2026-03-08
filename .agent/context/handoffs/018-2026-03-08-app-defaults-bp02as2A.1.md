# Task Handoff — MEU-17 App Defaults

## Task

- **Date:** 2026-03-08
- **Task slug:** app-defaults
- **Owner role:** coder
- **Scope:** MEU-17 — App Defaults (build-priority-matrix item 11, 02a-backup-restore.md §2A.1)

## Inputs

- User request: Implement SettingSpec registry and idempotent seeding for 24 application defaults
- Specs/docs referenced: `02a-backup-restore.md` §2A.1 L41-66 (settings table), L75-92 (validation rules), L100-128 (SettingSpec schema)
- Constraints: 24 entries matching spec exactly. Idempotent seeding (no Alembic). Categories: dialog, logging, display, backup, ui, notification.

## Role Plan

1. coder
2. tester
- Optional roles: reviewer, guardrail (deferred to project-level review)

## Coder Output

- Changed files:

| File | Change |
|------|--------|
| `packages/core/src/zorivest_core/domain/settings.py` | NEW — `Sensitivity` enum (3 values), `SettingSpec` frozen dataclass (12 fields), `SETTINGS_REGISTRY` (24 entries with validation constraints) |
| `packages/infrastructure/src/zorivest_infra/database/seed_defaults.py` | NEW — `seed_defaults(session, registry)` idempotent upsert-on-key |
| `tests/unit/test_settings_registry.py` | NEW — 14 tests covering AC-17.1 through AC-17.6 |

- Design notes:
  - `SETTINGS_REGISTRY` is a `dict[str, SettingSpec]` keyed by dotted setting names
  - Validation constraints (allowed_values, min/max, max_length) embedded in SettingSpec per spec §2A.1 L75-92
  - `seed_defaults()` uses get-then-upsert pattern (no merge/ON CONFLICT — portable across SQLite/SQLCipher)
  - Dynamic key `ui.panel.*.collapsed` uses wildcard in registry key itself

- Commands run: `uv run pytest tests/unit/test_settings_registry.py -v`, `uv run python -c "from zorivest_core.domain.settings import SETTINGS_REGISTRY; assert len(SETTINGS_REGISTRY) == 24"`
- Results: 14 passed / 0 failed, registry count assertion passes

## Tester Output

- Commands run: `uv run pytest tests/unit/test_settings_registry.py -v --tb=short`
- Pass/fail matrix: 14 passed / 0 failed / 0 skipped
- Test mapping:
  - AC-17.1 `TestRegistryCount`: registry has exactly 24 entries
  - AC-17.2 `TestValueTypes`: all value_types ∈ {str, int, float, bool, json}, all are SettingSpec instances
  - AC-17.3 `TestCategories`: all categories valid, all 6 categories represented
  - AC-17.4 `TestSeedDefaults`: seed populates 24 rows, values match registry, descriptions propagated
  - AC-17.5 `TestIdempotentSeeding`: re-seed doesn't duplicate, re-seed restores stale values
  - AC-17.6 `TestDynamicKey`: `ui.panel.*.collapsed` present and is bool
  - `TestSensitivityEnum`: 3 levels with correct values
- FAIL_TO_PASS: RED phase confirmed (import error before implementation)
- Negative cases: invalid value_type detection, stale DB value restoration on re-seed
- Contract verification: 24 entries match spec table L43-66 column by column

## Reviewer Output

- Findings by severity: Pending Codex review
- Verdict: pending
- Anti-deferral scan: `rg "TODO|FIXME|NotImplementedError" packages/core/src/zorivest_core/domain/settings.py packages/infrastructure/src/zorivest_infra/database/seed_defaults.py` → 0 matches

## Guardrail Output (If Required)

- Not applicable — no high-risk changes

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status: Implementation complete, awaiting Codex validation
- Next steps: Codex validates tests, code quality, contract coverage → verdict
