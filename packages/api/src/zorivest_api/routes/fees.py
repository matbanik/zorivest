# packages/api/src/zorivest_api/routes/fees.py
"""Fee summary route — fee breakdown by type, broker, and % of P&L.

Source: 04e-api-analytics.md §Fee Summary Routes
MEU-28: GET /summary (200). Gated behind require_unlocked_db.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from zorivest_api.dependencies import get_analytics_service, require_unlocked_db

fees_router = APIRouter(
    prefix="/api/v1/fees",
    tags=["fees"],
    dependencies=[Depends(require_unlocked_db)],
)


@fees_router.get("/summary")
async def fee_summary(
    account_id: str | None = None,
    period: str = "ytd",
    service: Any = Depends(get_analytics_service),
) -> dict:
    """Fee breakdown by type, broker, and % of P&L."""
    return service.fee_summary(account_id, period)
