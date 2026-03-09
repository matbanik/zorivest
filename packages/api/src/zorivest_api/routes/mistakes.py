# packages/api/src/zorivest_api/routes/mistakes.py
"""Mistake tracking routes — tag trades with mistake categories.

Source: 04e-api-analytics.md §Mistake Tracking Routes
MEU-28: POST / (201), GET /summary (200). Gated behind require_unlocked_db.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from zorivest_api.dependencies import get_review_service, require_unlocked_db

mistakes_router = APIRouter(
    prefix="/api/v1/mistakes",
    tags=["mistakes"],
    dependencies=[Depends(require_unlocked_db)],
)


@mistakes_router.post("", status_code=201)
async def track_mistake(
    body: dict,
    service: Any = Depends(get_review_service),
) -> dict:
    """Tag a trade with a mistake category and estimated cost."""
    return service.track_mistake(body)


@mistakes_router.get("/summary")
async def mistake_summary(
    account_id: str | None = None,
    period: str = "ytd",
    service: Any = Depends(get_review_service),
) -> dict:
    """Summary: mistakes by category, total cost, trend."""
    return service.mistake_summary(account_id, period)
