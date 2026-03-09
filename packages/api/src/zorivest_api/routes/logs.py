# packages/api/src/zorivest_api/routes/logs.py
"""Logging ingestion route — append-only log from Electron renderer.

Source: 04g-api-system.md §Logging Route
MEU-30: POST /api/v1/logs → 204, no auth required (localhost-only).
"""

from __future__ import annotations

import logging
from typing import Any, Literal, Optional

from fastapi import APIRouter
from pydantic import BaseModel

log_router = APIRouter(prefix="/api/v1/logs", tags=["system"])
logger = logging.getLogger("zorivest.frontend")

_LEVEL_MAP = {
    "debug": logger.debug,
    "info": logger.info,
    "warning": logger.warning,
    "error": logger.error,
    "critical": logger.critical,
}


class LogEntry(BaseModel):
    """Log entry from Electron renderer."""

    level: Literal["debug", "info", "warning", "error", "critical"] = "info"
    component: str = "unknown"
    message: str
    data: Optional[dict[str, Any]] = None


@log_router.post("", status_code=204)
async def ingest_log(entry: LogEntry) -> None:
    """Append-only log ingestion from Electron renderer. No auth required."""
    log_fn = _LEVEL_MAP[entry.level]
    log_fn(f"[{entry.component}] {entry.message}", extra={"data": entry.data})
