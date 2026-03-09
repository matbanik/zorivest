# packages/api/src/zorivest_api/routes/settings.py
"""Settings API routes — configuration CRUD with validation.

Source: 04d-api-settings.md §Settings Routes
MEU-27: Core settings GET/PUT routes only (Phase 2A delegated routes out-of-scope).
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from zorivest_api.dependencies import get_settings_service, require_unlocked_db
from zorivest_core.domain.settings_validator import SettingsValidationError

settings_router = APIRouter(prefix="/api/v1/settings", tags=["settings"])


class SettingResponse(BaseModel):
    """Single setting response shape per 04d spec."""

    key: str
    value: Any
    value_type: str


@settings_router.get("", dependencies=[Depends(require_unlocked_db)])
async def get_all_settings(
    service: Any = Depends(get_settings_service),
) -> Any:
    """Bulk read all settings as key-value dict.

    Returns all raw user settings. For resolved settings with
    source attribution, use GET /settings/resolved (Phase 2A).
    """
    rows = service.get_all()
    return {getattr(r, "key", r.get("key") if isinstance(r, dict) else None): getattr(r, "value", r.get("value") if isinstance(r, dict) else None) for r in rows}


@settings_router.get("/{key}", dependencies=[Depends(require_unlocked_db)])
async def get_setting(
    key: str,
    service: Any = Depends(get_settings_service),
) -> SettingResponse:
    """Read a single setting by key.

    Returns the resolved value through three-tier chain:
    user override → app default → hardcoded fallback.
    Returns 404 if key is not in the settings registry.
    """
    try:
        result = service.get(key)
    except KeyError:
        raise HTTPException(404, f"Setting '{key}' not found")
    if result is None:
        raise HTTPException(404, f"Setting '{key}' not found")
    # Handle both dict results (from in-memory store) and namespace objects
    if isinstance(result, dict):
        return SettingResponse(
            key=result.get("key", key),
            value=result.get("value"),
            value_type=result.get("value_type", "str"),
        )
    return SettingResponse(
        key=result.key,
        value=result.value,
        value_type=result.value_type,
    )


@settings_router.put("", dependencies=[Depends(require_unlocked_db)])
async def update_settings(
    body: dict[str, Any],
    service: Any = Depends(get_settings_service),
) -> dict[str, Any]:
    """Bulk upsert settings with validation.

    Returns 422 if any setting fails validation, with per-key error details.
    All-or-nothing: no settings are written if any key fails.
    Body: {"key1": "value1", "key2": "value2"}
    """
    try:
        return service.bulk_upsert(body)
    except SettingsValidationError as e:
        raise HTTPException(422, detail={"errors": e.per_key_errors})
