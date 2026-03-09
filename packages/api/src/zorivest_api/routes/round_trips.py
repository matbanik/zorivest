"""Round-trip routes.

Source: 04a-api-trades.md §Round-Trip
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from zorivest_api.dependencies import get_trade_service, require_unlocked_db

round_trip_router = APIRouter(prefix="/api/v1/round-trips", tags=["trades"])


@round_trip_router.get("", dependencies=[Depends(require_unlocked_db)])
async def list_round_trips(
    account_id: str | None = None,
    status: str = "all",
    ticker: str | None = None,
    limit: int = 50,
    offset: int = 0,
    service=Depends(get_trade_service),
):
    """List round-trips with optional filters.

    Canonical query params per 04a-api-trades.md §Round-Trip:
    - account_id: filter by account
    - status: open | closed | all
    - ticker: filter by instrument/ticker
    - limit/offset: pagination
    """
    return service.list_round_trips(
        account_id=account_id, status=status, ticker=ticker,
        limit=limit, offset=offset,
    )
