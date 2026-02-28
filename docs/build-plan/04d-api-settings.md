# Phase 4d: REST API — Settings

> Part of [Phase 4: REST API](04-rest-api.md) | Tag: `settings`
>
> Configuration CRUD, validation, resolved settings. Consumed by GUI for UI state persistence.

---

## Settings Routes

> Settings routes expose the `SettingModel` key-value store (see [Phase 2](02-infrastructure.md)) via REST. Consumed by the GUI for UI state persistence, notification preferences, and display mode toggles.

```python
# packages/api/src/zorivest_api/routes/settings.py

from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from zorivest_core.services.settings_service import SettingsService
from zorivest_core.domain.settings_validator import SettingsValidationError

settings_router = APIRouter(prefix="/api/v1/settings", tags=["settings"])


class SettingResponse(BaseModel):
    key: str
    value: str
    value_type: str


class ResolvedSettingResponse(BaseModel):
    """Used by GET /settings/resolved (Phase 2A). Returns typed values."""
    key: str
    value: Any            # typed: bool, int, float, str — NOT string-only
    source: str           # "user" | "default" | "hardcoded"
    value_type: str


@settings_router.get("/")
async def get_all_settings(service: SettingsService = Depends(get_settings_service)):
    """Bulk read all settings as key-value dict."""
    return service.get_all()


@settings_router.get("/{key}")
async def get_setting(key: str, service: SettingsService = Depends(get_settings_service)):
    """Read a single setting by key."""
    result = service.get(key)
    if result is None:
        raise HTTPException(404, f"Setting '{key}' not found")
    return result


@settings_router.put("/")
async def update_settings(body: dict[str, Any],
                          service: SettingsService = Depends(get_settings_service)):
    """Bulk upsert settings with validation.

    Returns 422 if any setting fails validation, with per-key error details.
    All-or-nothing: no settings are written if any key fails.
    Body: {"key1": "value1", "key2": "value2"}
    """
    try:
        service.bulk_upsert(body)
        return {"status": "updated", "count": len(body)}
    except SettingsValidationError as e:
        raise HTTPException(422, detail={"errors": e.per_key_errors})
```

### Validation Error Tests

```python
# tests/e2e/test_settings_api.py

def test_invalid_setting_rejected(client):
    """PUT with out-of-range value returns 422 with per-key errors."""
    response = client.put("/api/v1/settings", json={"logging.rotation_mb": "-5"})
    assert response.status_code == 422
    assert "logging.rotation_mb" in response.json()["detail"]["errors"]

def test_path_traversal_rejected(client):
    """PUT with path traversal value returns 422 with security error."""
    response = client.put("/api/v1/settings", json={"display.percent_mode": "../../../etc/passwd"})
    assert response.status_code == 422
    assert "display.percent_mode" in response.json()["detail"]["errors"]

def test_unknown_key_rejected(client):
    """PUT with unknown key returns 422 with per-key error."""
    response = client.put("/api/v1/settings", json={"not.a.real.key": "value"})
    assert response.status_code == 422
    assert "not.a.real.key" in response.json()["detail"]["errors"]

def test_valid_setting_accepted(client):
    """PUT with valid values returns 200."""
    response = client.put("/api/v1/settings", json={"logging.rotation_mb": "20"})
    assert response.status_code == 200

def test_mixed_payload_all_or_nothing(client):
    """PUT with one valid and one invalid key returns 422 and persists nothing."""
    response = client.put("/api/v1/settings", json={
        "logging.rotation_mb": "20",       # valid
        "logging.backup_count": "-1",       # invalid (below min)
    })
    assert response.status_code == 422
    errors = response.json()["detail"]["errors"]
    assert "logging.backup_count" in errors
    assert "logging.rotation_mb" not in errors
    # Verify valid key was NOT persisted
    get_resp = client.get("/api/v1/settings/logging.rotation_mb")
    assert get_resp.json()["value"] != "20"

def test_422_per_key_error_shape(client):
    """All 422 responses include detail.errors as dict[str, list[str]]."""
    response = client.put("/api/v1/settings", json={"display.percent_mode": "../hack"})
    assert response.status_code == 422
    errors = response.json()["detail"]["errors"]
    assert isinstance(errors, dict)
    for key, msgs in errors.items():
        assert isinstance(key, str)
        assert isinstance(msgs, list)
        assert all(isinstance(m, str) for m in msgs)

def test_invalid_bool_rejected(client):
    """PUT with non-bool string for bool setting returns 422."""
    response = client.put("/api/v1/settings", json={"display.hide_dollars": "not-a-bool"})
    assert response.status_code == 422
    assert "display.hide_dollars" in response.json()["detail"]["errors"]
```

### Roundtrip Tests

```python
# tests/e2e/test_settings_api.py

def test_settings_roundtrip(client):
    """PUT bulk → GET single → GET all."""
    response = client.put("/api/v1/settings", json={"ui.theme": "dark", "notification.info.enabled": "false"})
    assert response.status_code == 200
    assert response.json()["count"] == 2

    response = client.get("/api/v1/settings/ui.theme")
    assert response.status_code == 200
    assert response.json()["value"] == "dark"

    response = client.get("/api/v1/settings")
    assert response.status_code == 200
    assert "ui.theme" in response.json()

def test_setting_not_found(client):
    response = client.get("/api/v1/settings/nonexistent.key")
    assert response.status_code == 404
```

## Phase 2A Routes (Delegated)

> These endpoints are specified in [Phase 2A](02a-backup-restore.md) and registered in the settings router namespace:

| Method | Path | Description | Phase 2A Ref |
|--------|------|-------------|-------------|
| `GET` | `/api/v1/settings/resolved` | Typed settings with source attribution (user/default/hardcoded) | §2A.3 |
| `POST` | `/api/v1/settings/reset` | Reset settings to defaults | §2A.4 |
| `DELETE` | `/api/v1/settings/{key}` | Remove user override, fall back to default tier | §2A.4 |
| `GET` | `/api/v1/config/export` | Export config to portable JSON (excludes sensitive keys) | §2A.5 |
| `POST` | `/api/v1/config/import` | Import config from JSON (`?dry_run=true` for preview) | §2A.5 |
| `POST` | `/api/v1/backups` | Create encrypted database backup | §2A.1 |
| `GET` | `/api/v1/backups` | List available backups | §2A.1 |
| `POST` | `/api/v1/backups/verify` | Verify backup integrity (hash + open test) | §2A.2 |
| `POST` | `/api/v1/backups/restore` | Restore database from backup | §2A.2 |

See [02a-backup-restore.md](02a-backup-restore.md) for full schemas and validation rules.

## Consumer Notes

- **MCP tools:** `get_settings`, `update_settings` ([05a](05a-mcp-zorivest-settings.md))
- **GUI pages:** [06f-gui-settings.md](06f-gui-settings.md) — settings panel, theme toggle, notification prefs
