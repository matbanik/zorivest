# packages/api/src/zorivest_api/routes/scheduler.py
"""Power event endpoint for the scheduler (Phase 9, §9.3f).

Receives OS suspend/resume events from Electron IPC and triggers
APScheduler wakeup on resume.

Spec: 09-scheduling.md §9.3f
MEU: MEU-89 (scheduling-api-mcp)
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from pydantic.functional_validators import BeforeValidator

from zorivest_api.dependencies import get_scheduler_service


def _strip_whitespace(v: object) -> object:
    """Strip leading/trailing whitespace so min_length=1 rejects blank strings."""
    return v.strip() if isinstance(v, str) else v


StrippedStr = Annotated[str, BeforeValidator(_strip_whitespace)]


scheduler_router = APIRouter(prefix="/api/v1/scheduler", tags=["scheduler"])


class PowerEventRequest(BaseModel):
    """OS power event from Electron IPC."""

    model_config = {"extra": "forbid"}

    event_type: Literal["suspend", "resume"]
    timestamp: StrippedStr = Field(..., min_length=1)


@scheduler_router.post("/power-event")
async def receive_power_event(
    event: PowerEventRequest,
    scheduler: Any = Depends(get_scheduler_service),
) -> dict[str, Any]:
    """Receive OS power events from Electron IPC.

    On 'resume': force APScheduler to re-evaluate missed firings.
    On 'suspend': optionally pause in-flight pipelines.
    """
    if event.event_type == "resume":
        # Force APScheduler wakeup to check missed firings
        if scheduler.scheduler:
            scheduler.scheduler.wakeup()
        status_info = scheduler.get_status()
        return {
            "status": "resumed",
            "pending_jobs": status_info.get("job_count", 0),
        }
    elif event.event_type == "suspend":
        return {"status": "acknowledged"}
    return {"status": "unknown_event"}
