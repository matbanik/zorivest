# packages/api/src/zorivest_api/routes/mcp_guard.py
"""MCP Guard routes — circuit breaker + panic button for MCP tool access.

Source: 04g-api-system.md §MCP Guard Routes
MEU-30: 5 guard routes (status, config, lock, unlock, check).
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from zorivest_api.dependencies import get_guard_service, require_unlocked_db

guard_router = APIRouter(prefix="/api/v1/mcp-guard", tags=["mcp-guard"])


# ── Schemas ─────────────────────────────────────────────────────────────


class McpGuardStatus(BaseModel):
    """Guard state response."""

    is_enabled: bool
    is_locked: bool
    locked_at: Optional[str] = None
    lock_reason: Optional[str] = None
    calls_per_minute_limit: int
    calls_per_hour_limit: int
    recent_calls_1min: int
    recent_calls_1hr: int


class McpGuardConfigUpdate(BaseModel):
    """Guard configuration update request."""

    is_enabled: Optional[bool] = None
    calls_per_minute_limit: Optional[int] = Field(None, ge=1, le=10000)
    calls_per_hour_limit: Optional[int] = Field(None, ge=1, le=100000)


class McpGuardLockRequest(BaseModel):
    """Lock request with reason."""

    reason: str = "manual"


# ── Routes ──────────────────────────────────────────────────────────────


@guard_router.get("/status", status_code=200)
async def guard_status(
    service: Any = Depends(get_guard_service),
) -> McpGuardStatus:
    """Return current guard state. Available pre-unlock."""
    state = service.get_status()
    return McpGuardStatus(**state)


@guard_router.put(
    "/config",
    status_code=200,
    dependencies=[Depends(require_unlocked_db)],
)
async def update_guard_config(
    body: McpGuardConfigUpdate,
    service: Any = Depends(get_guard_service),
) -> McpGuardStatus:
    """Update guard thresholds. Requires unlocked DB."""
    state = service.update_config(body.model_dump(exclude_none=True))
    return McpGuardStatus(**state)


@guard_router.post(
    "/lock",
    status_code=200,
    dependencies=[Depends(require_unlocked_db)],
)
async def lock_mcp(
    body: McpGuardLockRequest,
    service: Any = Depends(get_guard_service),
) -> McpGuardStatus:
    """Panic button — immediately lock all MCP tools."""
    state = service.lock(body.reason)
    return McpGuardStatus(**state)


@guard_router.post(
    "/unlock",
    status_code=200,
    dependencies=[Depends(require_unlocked_db)],
)
async def unlock_mcp(
    service: Any = Depends(get_guard_service),
) -> McpGuardStatus:
    """Re-enable MCP tools. Requires unlocked DB."""
    state = service.unlock()
    return McpGuardStatus(**state)


@guard_router.post(
    "/check",
    status_code=200,
    dependencies=[Depends(require_unlocked_db)],
)
async def guard_check(
    service: Any = Depends(get_guard_service),
) -> dict[str, Any]:
    """Lightweight check called by MCP middleware on each tool call."""
    return service.check()
