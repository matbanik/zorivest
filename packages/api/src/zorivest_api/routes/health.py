"""Health check route.

Source: 04g-api-system.md §Health
Canonical HealthResponse: status, version, uptime_seconds, database.
"""

from __future__ import annotations

import time

from fastapi import APIRouter, Request
from pydantic import BaseModel

from zorivest_core.version import get_version

health_router = APIRouter(tags=["system"])


class DatabaseStatus(BaseModel):
    """Database status sub-object."""

    unlocked: bool


class HealthResponse(BaseModel):
    """Canonical 04g health response."""

    status: str
    version: str
    uptime_seconds: int
    database: DatabaseStatus


@health_router.get("/api/v1/health", response_model=HealthResponse)
async def health_check(request: Request) -> HealthResponse:
    """Health check endpoint (no auth required)."""
    start_time = getattr(request.app.state, "start_time", time.time())
    db_unlocked = getattr(request.app.state, "db_unlocked", False)

    return HealthResponse(
        status="ok",
        version=get_version(),
        uptime_seconds=int(time.time() - start_time),
        database=DatabaseStatus(unlocked=db_unlocked),
    )
