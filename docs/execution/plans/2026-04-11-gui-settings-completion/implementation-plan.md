# GUI Settings Completion — Implementation Plan

> **Project:** MEU-76, MEU-75, MEU-74 | **Matrix:** 35f, 35e, 35d
> **Spec:** [06f-gui-settings.md](file:///p:/zorivest/docs/build-plan/06f-gui-settings.md) §6f.5–§6f.7
> **Date:** 2026-04-11

---

## Goal

Complete the remaining Settings GUI pages: **Reset to Default** (35f), **Config Export/Import** (35e), and **Backup & Restore** (35d). All backend services exist — this project adds REST API routes and React GUI pages consuming them.

## User Review Required

> [!IMPORTANT]
> **MEU numbering:** The meu-registry.md does not yet have entries for these items. The prior session used MEU-74/75/76 as working IDs (mapped from matrix items 35d/35e/35f). This plan uses those IDs — they'll be registered formally during execution.

> [!IMPORTANT]
> **Backup passphrase injection:** `BackupManager` and `BackupRecoveryManager` constructors require a `passphrase` argument. The plan injects this from `app.state.passphrase` (set during `POST /auth/unlock`). If the passphrase is not held in app state currently, we'll need to add it during the unlock flow. Confirm this is acceptable.

> [!WARNING]
> **Backup restore file paths:** Since Zorivest is a localhost-only desktop app, the restore API route will accept a filesystem path string in the request body (not a file upload). The Electron GUI uses `dialog.showOpenDialog()` to get the path and sends it to the API. This is a security-acceptable pattern for local desktop apps but would not be valid for a remote API.

---

## Proposed Changes

### Execution Order

```
MEU-76 (Reset to Default) → MEU-75 (Config Export/Import) → MEU-74 (Backup & Restore)
```

**Rationale:**
- MEU-76 is the simplest (2 API routes, 1 hook) and adds `GET /settings/resolved` which MEU-75 needs for export
- MEU-75 builds on resolved settings and adds a moderate-complexity page
- MEU-74 is the most complex (4 routes, file dialog integration, progress states)

---

### MEU-76: Reset to Default (Matrix 35f)

**Summary:** Add `DELETE /settings/{key}` and `GET /settings/resolved` API routes, create a shared `useResetSetting` React hook, and enhance existing settings pages with source indicators and reset buttons.

#### [MODIFY] [settings.py](file:///p:/zorivest/packages/api/src/zorivest_api/routes/settings.py)

Add two new routes:

1. **`DELETE /api/v1/settings/{key}`** — Calls `settings_service.reset_to_default(key)`. Returns 204 on success, 404 if key not found.
2. **`GET /api/v1/settings/resolved`** — Calls `settings_service.get_all_resolved()`. Returns `dict[str, {key, value, value_type, source}]` where `source` is `"user"`, `"default"`, or `"hardcoded"`.

Response model for resolved endpoint:

```python
class ResolvedSettingResponse(BaseModel):
    key: str
    value: Any
    value_type: str
    source: str  # "user" | "default" | "hardcoded"
```

#### [NEW] [useResetSetting.ts](file:///p:/zorivest/ui/src/renderer/src/hooks/useResetSetting.ts)

Shared hook wrapping `DELETE /api/v1/settings/{key}`:

```typescript
export function useResetSetting() {
    const queryClient = useQueryClient()
    const { setStatus } = useStatusBar()

    return useMutation({
        mutationFn: (key: string) =>
            apiFetch(`/api/v1/settings/${key}`, { method: 'DELETE' }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['settings'] })
            setStatus('Setting reset to default ✓', 3000)
        },
    })
}
```

#### [MODIFY] [SettingsLayout.tsx](file:///p:/zorivest/ui/src/renderer/src/features/settings/SettingsLayout.tsx)

- Fetch resolved settings via `GET /settings/resolved` to determine which sections have user overrides
- Add "Reset All Settings" button at bottom of page (with confirmation dialog)

#### Tests

| File | Type | Count (est.) |
|------|------|:---:|
| `tests/unit/routes/test_settings.py` (extend) | Python unit | +4 |
| `ui/src/renderer/src/hooks/__tests__/useResetSetting.test.ts` [NEW] | Vitest | +3 |

**Acceptance Criteria:**
- AC-1: `DELETE /api/v1/settings/{key}` returns 204 and removes user override `[Spec: §6f.7]`
- AC-2: `DELETE /api/v1/settings/{key}` returns 404 for unknown key `[Spec: §6f.7]`
- AC-3: `GET /api/v1/settings/resolved` returns all settings with source attribution `[Spec: §6f.7]`
- AC-4: `useResetSetting` hook invalidates query cache after successful reset `[Local Canon: hook pattern]`

---

### MEU-75: Config Export/Import (Matrix 35e)

**Summary:** Add `GET /config/export` and `POST /config/import` API routes in a new `config.py` module, create DI wiring for `ConfigExportService`, and build a new `ConfigExportImportPage` React component with export download and import preview diff.

#### [NEW] [config.py](file:///p:/zorivest/packages/api/src/zorivest_api/routes/config.py)

Two routes:

1. **`GET /api/v1/config/export`** — Calls `ConfigExportService.build_export(settings_service.get_all_resolved())`. Returns JSON payload with `config_version`, `app_version`, `created_at`, `settings`.
2. **`POST /api/v1/config/import`** — Accepts JSON body (export format). With `?dry_run=true`, returns `ImportValidation` (accepted/rejected/unknown keys). Without dry_run, applies accepted keys via `settings_service.bulk_upsert()`.

Request/Response models:

```python
class ConfigImportRequest(BaseModel):
    model_config = {"extra": "forbid"}
    config_version: int
    app_version: str | None = None
    created_at: str | None = None
    settings: dict[str, Any]

class ImportPreviewResponse(BaseModel):
    accepted: list[str]
    rejected: list[str]
    unknown: list[str]
    applied: bool
```

#### [MODIFY] [dependencies.py](file:///p:/zorivest/packages/api/src/zorivest_api/dependencies.py)

Add `get_config_export_service` provider (resolves from `app.state.config_export_service`).

#### [MODIFY] [main.py](file:///p:/zorivest/packages/api/src/zorivest_api/main.py)

Register `config_router` via `app.include_router(config_router)`.

#### [NEW] [ConfigExportImportPage.tsx](file:///p:/zorivest/ui/src/renderer/src/features/settings/ConfigExportImportPage.tsx)

Layout per spec §6f.6:
- **Export section:** "Export Config" button → triggers `GET /config/export` → downloads as `zorivest-config-{date}.json` using Blob + anchor click
- **Import section:** File select input → reads JSON → `POST /config/import?dry_run=true` → displays diff preview table (showing accepted/rejected/unknown keys with values) → "Apply" button → `POST /config/import` (full apply) → success toast

#### [MODIFY] [router.tsx](file:///p:/zorivest/ui/src/renderer/src/router.tsx)

Add `/settings/config` route with lazy-loaded `ConfigExportImportPage`.

#### [MODIFY] [SettingsLayout.tsx](file:///p:/zorivest/ui/src/renderer/src/features/settings/SettingsLayout.tsx)

Add "Config Export/Import" navigation entry in a new "Maintenance" section.

#### Tests

| File | Type | Count (est.) |
|------|------|:---:|
| `tests/unit/routes/test_config.py` [NEW] | Python unit | +6 |
| `ui/.../settings/__tests__/ConfigExportImportPage.test.tsx` [NEW] | Vitest | +5 |

**Acceptance Criteria:**
- AC-1: `GET /config/export` returns only portable (exportable + non-sensitive) settings `[Spec: §6f.6]`
- AC-2: `POST /config/import?dry_run=true` returns categorized keys without persisting `[Spec: §6f.6]`
- AC-3: `POST /config/import` applies only accepted keys, ignores rejected/unknown `[Spec: §6f.6]`
- AC-4: Export action triggers browser file download with correct filename format `[Spec: §6f.6]`
- AC-5: Import preview shows diff of accepted changes before apply `[Spec: §6f.6]`
- AC-6: `extra="forbid"` on import request model rejects unexpected top-level fields `[Local Canon: BIC]`

---

### MEU-74: Backup & Restore (Matrix 35d)

**Summary:** Add 4 backup-related API routes in a new `backups.py` module, create DI wiring for `BackupManager` and `BackupRecoveryManager`, and build a new `BackupRestorePage` React component with create/list/verify/restore workflow.

#### [NEW] [backups.py](file:///p:/zorivest/packages/api/src/zorivest_api/routes/backups.py)

Four routes:

1. **`POST /api/v1/backups`** — Creates manual backup. Returns `BackupResult` (status, path, elapsed_seconds).
2. **`GET /api/v1/backups`** — Lists available backups. Returns array of `{filename, path, size_bytes, modified_at, type}`.
3. **`POST /api/v1/backups/verify`** — Accepts `{backup_path: str}`. Returns `VerifyResult` (status, file details).
4. **`POST /api/v1/backups/restore`** — Accepts `{backup_path: str}`. Returns `RestoreResult` (status, details). Requires confirmation dialog pattern.

Response models:

```python
class BackupInfo(BaseModel):
    filename: str
    path: str
    size_bytes: int
    modified_at: str
    backup_type: str  # "auto" | "manual"

class BackupListResponse(BaseModel):
    backups: list[BackupInfo]
    total: int

class VerifyRequest(BaseModel):
    model_config = {"extra": "forbid"}
    backup_path: str

class RestoreRequest(BaseModel):
    model_config = {"extra": "forbid"}
    backup_path: str
```

#### [MODIFY] [dependencies.py](file:///p:/zorivest/packages/api/src/zorivest_api/dependencies.py)

Add two providers:
- `get_backup_manager` — resolves from `app.state.backup_manager`
- `get_backup_recovery_manager` — resolves from `app.state.backup_recovery_manager`

#### [MODIFY] [main.py](file:///p:/zorivest/packages/api/src/zorivest_api/main.py)

Register `backup_router` via `app.include_router(backup_router)`.

#### [NEW] [BackupRestorePage.tsx](file:///p:/zorivest/ui/src/renderer/src/features/settings/BackupRestorePage.tsx)

Layout per spec §6f.5:
- **Manual Backup section:** "Create Backup Now" button → `POST /backups` → spinner → result toast with path
- **Auto-Backup Config section:** Uses `usePersistedState` for `backup.auto_interval_seconds`, `backup.change_threshold`, `backup.compression_enabled`
- **Restore section:** File select (Electron `dialog.showOpenDialog()` via IPC or fallback input) → path → Verify button (`POST /backups/verify`) → Restore button (`POST /backups/restore`) with confirmation dialog
- **Backup History table:** `GET /backups` → sorted table with filename, size, date, type, and Verify/Open actions

#### [MODIFY] [router.tsx](file:///p:/zorivest/ui/src/renderer/src/router.tsx)

Add `/settings/backup` route with lazy-loaded `BackupRestorePage`.

#### [MODIFY] [SettingsLayout.tsx](file:///p:/zorivest/ui/src/renderer/src/features/settings/SettingsLayout.tsx)

Add "Backup & Restore" navigation entry in "Maintenance" section (alongside Config Export/Import).

#### Tests

| File | Type | Count (est.) |
|------|------|:---:|
| `tests/unit/routes/test_backups.py` [NEW] | Python unit | +8 |
| `ui/.../settings/__tests__/BackupRestorePage.test.tsx` [NEW] | Vitest | +6 |

**Acceptance Criteria:**
- AC-1: `POST /backups` creates encrypted backup and returns result `[Spec: §6f.5]`
- AC-2: `GET /backups` returns sorted list with metadata `[Spec: §6f.5]`
- AC-3: `POST /backups/verify` returns integrity check result without modifying files `[Spec: §6f.5]`
- AC-4: `POST /backups/restore` applies backup with passphrase from session `[Spec: §6f.5]`
- AC-5: Restore requires confirmation dialog `[Spec: §6f.5]`
- AC-6: `extra="forbid"` on request models `[Local Canon: BIC]`
- AC-7: Auto-backup config uses `usePersistedState` for `backup.*` keys `[Local Canon: hook pattern]`
- AC-8: Backup history table shows file metadata with verify action `[Spec: §6f.5]`

---

### Cross-Cutting: Navigation Update

#### [MODIFY] [SettingsLayout.tsx](file:///p:/zorivest/ui/src/renderer/src/features/settings/SettingsLayout.tsx)

Restructure navigation into logical sections:

```
Data Sources
  ├── 🌐 Market Data Providers  →  /settings/market
  └── ✉️ Email Provider         →  /settings/email

Maintenance
  ├── 💾 Backup & Restore      →  /settings/backup
  └── 📦 Config Export/Import   →  /settings/config

Appearance
  └── 🎨 Theme (Dark/Light)

MCP
  ├── 🛡️ Guard Controls
  └── 📡 Server Status
```

---

## Open Questions

> [!IMPORTANT]
> **Q1: Passphrase in app.state** — Is the unlock passphrase currently stored in `app.state.passphrase` after `POST /auth/unlock`? The backup managers require it. If not, we need to add this during the unlock flow. Confirm this is acceptable.

> [!IMPORTANT]
> **Q2: Electron IPC for file dialogs** — The backup restore and config import flows need file selection. The current Electron preload exposes `window.api.baseUrl` and `window.api.token`. Does the preload also expose file dialog methods (e.g., `window.api.showOpenDialog`)? If not, we'll use a standard HTML `<input type="file">` for config import and a text input for backup paths as a fallback.

> [!NOTE]
> **Q3: TEST-DRIFT-MDS** — 5 pre-existing test failures in `test_market_data_service.py` will not block MEU-scoped validation but will show up in full-phase validation. Should we fix these as part of this project or defer?

---

## Verification Plan

### Automated Tests

```powershell
# Per-MEU gate (after each MEU)
uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate.txt; Get-Content C:\Temp\zorivest\validate.txt | Select-Object -Last 50

# Python unit tests (scoped)
uv run pytest tests/unit/routes/test_settings.py tests/unit/routes/test_config.py tests/unit/routes/test_backups.py -x --tb=short -v *> C:\Temp\zorivest\pytest.txt; Get-Content C:\Temp\zorivest\pytest.txt | Select-Object -Last 40

# TypeScript unit tests (scoped)
npx vitest run src/renderer/src/features/settings src/renderer/src/hooks --reporter=verbose *> C:\Temp\zorivest\vitest.txt; Get-Content C:\Temp\zorivest\vitest.txt | Select-Object -Last 40

# Type checks
uv run pyright packages/ *> C:\Temp\zorivest\pyright.txt; Get-Content C:\Temp\zorivest\pyright.txt | Select-Object -Last 30

# Lint
uv run ruff check packages/ *> C:\Temp\zorivest\ruff.txt; Get-Content C:\Temp\zorivest\ruff.txt | Select-Object -Last 20
```

### Manual Verification

- Settings page navigation shows new "Maintenance" section with working links
- Export downloads a valid JSON file
- Import preview shows correct diff before apply
- Reset to Default removes user override and refreshes value
- Backup create/list/verify cycle works end-to-end (requires unlocked DB session)
