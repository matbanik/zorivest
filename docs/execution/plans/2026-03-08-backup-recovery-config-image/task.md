# Task — backup-recovery-config-image

> Project: `backup-recovery-config-image` | 2026-03-08

## MEU-20: backup-recovery (BackupRecoveryManager)

- [ ] Write FIC + tests (Red phase)
  - [ ] `test_backup_recovery.py` — AC-20.1 through AC-20.9
  - [ ] `test_backup_recovery_integration.py` — full cycle
- [ ] Add `InvalidPassphraseError`, `CorruptedBackupError` to exceptions.py
- [ ] Create `backup_recovery_types.py` (RestoreResult, VerifyResult, RepairResult)
- [ ] Implement `backup_recovery_manager.py` (Green phase)
- [ ] Verify: `uv run pytest tests/unit/test_backup_recovery.py -v`
- [ ] Verify: `uv run pytest tests/integration/test_backup_recovery_integration.py -v`
- [ ] Create handoff: `021-2026-03-08-backup-recovery-bp02as2A.4.md`

## MEU-21: config-export (ConfigExportService)

- [ ] Write FIC + tests (Red phase)
  - [ ] `test_config_export.py` — AC-21.1 through AC-21.7
- [ ] Create `config_export.py` + `ImportValidation` dataclass
- [ ] Implement `ConfigExportService` (Green phase)
- [ ] Verify: `uv run pytest tests/unit/test_config_export.py -v`
- [ ] Create handoff: `022-2026-03-08-config-export-bp02as2A.5.md`

## MEU-22: image-processing

- [ ] Write FIC + tests (Red phase)
  - [ ] `test_image_processing.py` — AC-22.1 through AC-22.8
- [ ] Create `image_processing.py` (validate, standardize, thumbnail)
- [ ] Implement functions (Green phase)
- [ ] Verify: `uv run pytest tests/unit/test_image_processing.py -v`
- [ ] Create handoff: `023-2026-03-08-image-processing-bp03sIMG.md`

## Post-Project

- [ ] Update `docs/BUILD_PLAN.md` (status, phase tracker, summary table)
- [ ] Run MEU gate: `uv run python tools/validate_codebase.py --scope meu`
- [ ] Update `.agent/context/meu-registry.md`
- [ ] Run full regression: `uv run pytest tests/ -v`
- [ ] Create reflection in `docs/execution/reflections/`
- [ ] Update `docs/execution/metrics.md`
- [ ] Save session state to pomera_notes
- [ ] Prepare proposed commit messages
