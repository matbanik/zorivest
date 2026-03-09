# packages/api/src/zorivest_api/routes/service.py
"""Service lifecycle routes — status and graceful shutdown.

Source: 04g-api-system.md §Service Routes
MEU-30: GET /status (auth), POST /graceful-shutdown (admin).
"""

from __future__ import annotations

import logging
import os
import signal
import sys
import time
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, Request
from pydantic import BaseModel

from zorivest_api.dependencies import require_authenticated, require_admin

service_router = APIRouter(prefix="/api/v1/service", tags=["service"])

logger = logging.getLogger("zorivest.service")


class ServiceStatusResponse(BaseModel):
    """Process metrics response."""

    pid: int
    uptime_seconds: float
    memory_mb: float
    cpu_percent: float
    python_version: str


@service_router.get("/status", status_code=200)
async def service_status(
    request: Request,
    _user: Any = Depends(require_authenticated),
) -> ServiceStatusResponse:
    """Process metrics: PID, uptime, memory, CPU, Python version.
    Requires authenticated user."""
    start_time = getattr(request.app.state, "start_time", time.time())
    uptime = time.time() - start_time

    # Memory info — use psutil if available, fallback to 0
    memory_mb = 0.0
    cpu_percent = 0.0
    try:
        import psutil
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / (1024 * 1024)
        cpu_percent = process.cpu_percent(interval=0.1)
    except ImportError:
        pass

    return ServiceStatusResponse(
        pid=os.getpid(),
        uptime_seconds=round(uptime, 2),
        memory_mb=round(memory_mb, 2),
        cpu_percent=round(cpu_percent, 2),
        python_version=sys.version.split()[0],
    )


def _shutdown_process() -> None:
    """Flush logs and send SIGINT to trigger graceful shutdown.

    The service wrapper (systemd/launchd/NSSM) auto-restarts the process.
    Source: 04g-api-system.md §Service Routes
    """
    logger.info("Graceful shutdown initiated — flushing logs and sending SIGINT")
    logging.shutdown()
    # Brief delay to allow 202 response to be sent
    time.sleep(0.5)
    os.kill(os.getpid(), signal.SIGINT)


@service_router.post("/graceful-shutdown", status_code=202)
async def graceful_shutdown(
    background_tasks: BackgroundTasks,
    _user: Any = Depends(require_admin),
) -> dict[str, str]:
    """Trigger graceful shutdown. Requires admin role.
    Flushes logs, closes DB connections, then exits.
    Service wrapper (systemd/launchd/NSSM) auto-restarts."""
    background_tasks.add_task(_shutdown_process)
    return {"status": "shutdown_initiated"}
