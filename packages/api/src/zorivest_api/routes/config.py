# packages/api/src/zorivest_api/routes/config.py
"""Config Export/Import API routes.

Source: 06f-gui-settings.md §6f.6
MEU-75: JSON config export with security filtering, import with dry-run preview.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from zorivest_api.dependencies import (
    get_settings_service,
    require_unlocked_db,
)

config_router = APIRouter(prefix="/api/v1/config", tags=["config"])


class ConfigImportRequest(BaseModel):
    """Request body for POST /config/import.

    Uses extra='forbid' per Boundary Input Contract.
    """

    model_config = {"extra": "forbid"}

    config_version: int
    app_version: str | None = None
    created_at: str | None = None
    settings: dict[str, Any]


class ImportPreviewResponse(BaseModel):
    """Import validation result showing key categorization."""

    accepted: list[str]
    rejected: list[str]
    unknown: list[str]
    applied: bool


@config_router.get("/export", dependencies=[Depends(require_unlocked_db)])
async def export_config(
    service: Any = Depends(get_settings_service),
) -> dict[str, Any]:
    """Export portable (exportable + non-sensitive) settings as JSON.

    Returns a config payload with config_version, app_version,
    created_at, and settings dict containing only portable key-value pairs.

    Source: MEU-75 (06f-gui-settings.md §6f.6)
    """
    from zorivest_core.domain.config_export import ConfigExportService

    # Get all resolved settings (key → ResolvedSetting)
    resolved = service.get_all_resolved()
    # ConfigExportService.build_export expects key → value (not ResolvedSetting)
    resolved_values = {key: rs.value for key, rs in resolved.items()}

    export_service = ConfigExportService()
    return export_service.build_export(resolved_values)


@config_router.post("/import", dependencies=[Depends(require_unlocked_db)])
async def import_config(
    body: ConfigImportRequest,
    dry_run: bool = False,
    service: Any = Depends(get_settings_service),
) -> ImportPreviewResponse:
    """Import settings from a config export payload.

    With dry_run=true: validates and returns preview (accepted/rejected/unknown)
    without persisting any changes.

    Without dry_run: validates AND applies accepted keys via bulk_upsert.

    Source: MEU-75 (06f-gui-settings.md §6f.6)
    """
    from zorivest_core.domain.config_export import ConfigExportService

    export_service = ConfigExportService()
    validation = export_service.validate_import(body.model_dump())

    if dry_run:
        return ImportPreviewResponse(
            accepted=validation.accepted,
            rejected=validation.rejected,
            unknown=validation.unknown,
            applied=False,
        )

    # Apply accepted keys only
    if validation.accepted:
        settings_to_apply = {key: body.settings[key] for key in validation.accepted}
        try:
            service.bulk_upsert(settings_to_apply)
        except Exception as e:
            raise HTTPException(
                422,
                detail=f"Failed to apply settings: {e}",
            )

    return ImportPreviewResponse(
        accepted=validation.accepted,
        rejected=validation.rejected,
        unknown=validation.unknown,
        applied=True,
    )
