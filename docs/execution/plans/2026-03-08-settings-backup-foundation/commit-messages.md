# Commit Messages — settings-backup-foundation

## Implementation (MEU-17, 18, 19)

```
feat(core): add SettingSpec registry, SettingsResolver, Validator, Cache (MEU-17/18)

- 24-entry SETTINGS_REGISTRY with SettingSpec dataclass + Sensitivity enum
- Three-tier resolution: hardcoded → app_default → user_override
- SettingsValidator with range/pattern/enum checks
- SettingsCache with TTL-based invalidation
- seed_defaults() for AppDefaultModel population

feat(core): add SettingsService with full CRUD surface (MEU-18)

- get(), get_all(), get_all_resolved(), bulk_upsert(), reset_to_default()
- Wired to SettingsResolver, Validator, Cache via constructor injection
- All-or-nothing validation on bulk_upsert

feat(infra): add BackupManager with Argon2id + GFS rotation (MEU-19)

- SQLite Online Backup API for consistent snapshots
- AES-encrypted ZIP via pyzipper with Argon2id-derived key
- BackupManifest with file hashes and KDF params
- GFS rotation: 5 daily, 4 weekly, 3 monthly
- Post-backup verification (manifest hash + file presence)
```

## Corrections (from critical review)

```
feat(infra): add SqlAlchemy settings/app-defaults repositories and UoW wiring

- SqlAlchemySettingsRepository (CRUD on SettingModel)
- SqlAlchemyAppDefaultsRepository (read-only on AppDefaultModel)
- Wired settings + app_defaults into SqlAlchemyUnitOfWork

feat(infra): replace PBKDF2 with Argon2id for backup key derivation

- Install argon2-cffi dependency
- Use argon2.low_level.hash_secret_raw() with Type.ID
- Params: time_cost=3, memory_cost=65536, parallelism=4, hash_len=32

test(backup): add security and integrity tests for BackupManager

- wrong-password decryption failure
- manifest SHA-256 hash integrity verification
- KDF domain separation (zorivest-backup-v1)
- KDF algorithm assertion (argon2id)
- GFS rotation excess removal
- verify_backup file presence check

feat(core): add get_all() to SettingsService

chore(docs): update BUILD_PLAN.md and meu-registry.md for Phase 2A
```
