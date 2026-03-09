"""Version route.

Source: 04g-api-system.md §Version
Canonical VersionResponse: version, context.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from zorivest_core.version import get_version, get_version_context

version_router = APIRouter(tags=["system"])


class VersionResponse(BaseModel):
    """Canonical 04g version response."""
    version: str
    context: str


@version_router.get("/api/v1/version/", response_model=VersionResponse)
async def get_version_info() -> VersionResponse:
    """Version info endpoint (no auth required)."""
    return VersionResponse(
        version=get_version(),
        context=get_version_context(),
    )
