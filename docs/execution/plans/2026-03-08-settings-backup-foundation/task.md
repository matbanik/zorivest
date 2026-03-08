# Task — settings-backup-foundation

> MEU 17, 18, 19 | Phase 2A | 2026-03-08

## MEU-17: app-defaults (bp02a §2A.1)

- [x] Write `SettingSpec` dataclass + `Sensitivity` enum + `SETTINGS_REGISTRY` (24 entries) in `settings.py`
- [x] Write `seed_defaults()` in `seed_defaults.py`
- [x] Write `test_settings_registry.py` (AC-17.1 through AC-17.6)
- [x] RED phase: confirm tests fail
- [x] GREEN phase: implement until tests pass
- [x] MEU gate: `uv run python tools/validate_codebase.py --scope meu`
- [x] Handoff: `018-2026-03-08-app-defaults-bp02as2A.1.md` (9 sections)

## MEU-18: settings-resolver (bp02a §2A.2)

- [x] Write `SettingsResolver` in `settings_resolver.py`
- [x] Write `SettingsValidator` in `settings_validator.py`
- [x] Write `SettingsCache` in `settings_cache.py`
- [x] Add `SettingsRepository` + `AppDefaultsRepository` ports to `ports.py`
- [x] Write `SettingsService` in `settings_service.py`
- [x] Write tests: `test_settings_resolver.py`, `test_settings_validator.py`, `test_settings_cache.py`, `test_settings_service.py`
- [x] Update `test_ports.py` protocol invariant (9 → 11)
- [x] RED → GREEN cycle
- [x] MEU gate
- [x] Handoff: `019-2026-03-08-settings-resolver-bp02as2A.2.md` (9 sections)

## MEU-19: backup-manager (bp02a §2A.3)

- [x] Install pyzipper: `uv add --package zorivest-infra pyzipper`
- [x] Write `BackupManager` in `backup/backup_manager.py`
- [x] Write `BackupResult` + `BackupManifest` in `backup/backup_types.py`
- [x] Write `test_backup_manager.py`
- [x] RED → GREEN cycle
- [x] MEU gate
- [x] Handoff: `020-2026-03-08-backup-manager-bp02as2A.3.md` (9 sections)

## Post-Project

- [x] Update `meu-registry.md` with Phase 2A rows
- [x] Update `BUILD_PLAN.md` Phase 2A status → `🔵 In Progress`
- [x] Run full regression: `uv run pytest tests/ -v` — 447 passed, 1 skipped
- [x] Phase gate: `uv run python tools/validate_codebase.py`
- [x] Reflection + metrics → `2026-03-08-settings-backup-foundation-reflection.md`
- [x] Proposed commit messages → `commit-messages.md`

