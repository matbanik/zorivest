# Commit Messages — backup-recovery-config-image

## MEU-20: BackupRecoveryManager

```
feat(infra): add BackupRecoveryManager — restore, verify, repair

- Implement restore_backup() with AES decryption + SHA-256 verification
- Add verify_backup() for non-destructive validation
- Add repair_database() with PRAGMA integrity_check + export/reimport
- Support legacy formats (.zip, .db, .db.gz)
- Callback-based maintenance hooks for connection management
- Store KDF salt in ZIP comment for independent recovery
- Add InvalidPassphraseError, CorruptedBackupError to exceptions
- 13 unit + 5 integration tests, all passing
```

## MEU-21: ConfigExportService

```
feat(core): add ConfigExportService — JSON config export/import

- build_export() filters settings via _is_portable() predicate
- validate_import() categorizes keys as accepted/rejected/unknown
- Symmetric security filtering (exportable + non-sensitive only)
- ImportValidation frozen dataclass for import categorization
- Round-trip test: validate_import(build_export(...)) works correctly
- Update build-plan spec to resolved_values API (SRP)
- 17 unit tests, all passing
```

## MEU-22: Image Processing

```
feat(infra): add image processing — validate, standardize, thumbnail

- validate_image() with magic-byte detection (PNG, JPEG, GIF, WebP)
- Enforce 10MB size limit
- standardize_to_webp() converts to WebP (quality=85)
- generate_thumbnail() creates 200×200 max thumbnails (LANCZOS)
- Preserve alpha channels for transparent images
- Add Pillow>=11.0.0 dependency to infrastructure package
- 16 unit tests, all passing
```
