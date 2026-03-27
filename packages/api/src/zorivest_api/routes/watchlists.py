"""Watchlist REST endpoints (MEU-68).

Source: implementation-plan.md §MEU-68 AC-8.
7 endpoints under /api/v1/watchlists for CRUD + item management.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from zorivest_api.dependencies import get_watchlist_service

watchlist_router = APIRouter(prefix="/api/v1/watchlists", tags=["watchlists"])


# ── Request/Response schemas ────────────────────────────────────────────


class CreateWatchlistRequest(BaseModel):
    name: str
    description: str = ""


class UpdateWatchlistRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class AddTickerRequest(BaseModel):
    ticker: str
    notes: str = ""


class WatchlistItemResponse(BaseModel):
    id: int
    watchlist_id: int
    ticker: str
    added_at: str
    notes: str = ""


class WatchlistResponse(BaseModel):
    id: int
    name: str
    description: str
    created_at: str
    updated_at: str
    items: list[WatchlistItemResponse] = []
    model_config = {"from_attributes": True}


# ── Watchlist routes ────────────────────────────────────────────────────


@watchlist_router.post("/", status_code=201)
async def create_watchlist(
    body: CreateWatchlistRequest,
    service=Depends(get_watchlist_service),
):
    """Create a new watchlist."""
    try:
        wl = service.create(name=body.name, description=body.description)
        return _to_response(wl, service)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e


@watchlist_router.get("/")
async def list_watchlists(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    service=Depends(get_watchlist_service),
):
    """List watchlists with pagination."""
    watchlists = service.list_all(limit=limit, offset=offset)
    return [_to_response(wl, service) for wl in watchlists]


@watchlist_router.get("/{watchlist_id}")
async def get_watchlist(
    watchlist_id: int,
    service=Depends(get_watchlist_service),
):
    """Get a watchlist by ID with items."""
    wl = service.get(watchlist_id)
    if wl is None:
        raise HTTPException(
            status_code=404, detail=f"Watchlist {watchlist_id} not found"
        )
    return _to_response(wl, service)


@watchlist_router.put("/{watchlist_id}")
async def update_watchlist(
    watchlist_id: int,
    body: UpdateWatchlistRequest,
    service=Depends(get_watchlist_service),
):
    """Update watchlist metadata."""
    try:
        updates = body.model_dump(exclude_unset=True)
        wl = service.update(watchlist_id, updates)
        return _to_response(wl, service)
    except ValueError as e:
        detail = str(e)
        if "not found" in detail.lower():
            raise HTTPException(status_code=404, detail=detail) from e
        raise HTTPException(status_code=409, detail=detail) from e


@watchlist_router.delete("/{watchlist_id}", status_code=204)
async def delete_watchlist(
    watchlist_id: int,
    service=Depends(get_watchlist_service),
):
    """Delete a watchlist (cascades items)."""
    try:
        service.delete(watchlist_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@watchlist_router.post("/{watchlist_id}/items", status_code=201)
async def add_ticker(
    watchlist_id: int,
    body: AddTickerRequest,
    service=Depends(get_watchlist_service),
):
    """Add a ticker to a watchlist."""
    try:
        item = service.add_ticker(
            watchlist_id=watchlist_id,
            ticker=body.ticker,
            notes=body.notes,
        )
        return {
            "id": item.id,
            "watchlist_id": item.watchlist_id,
            "ticker": item.ticker,
            "added_at": str(item.added_at),
            "notes": item.notes,
        }
    except ValueError as e:
        detail = str(e)
        if "not found" in detail.lower():
            raise HTTPException(status_code=404, detail=detail) from e
        raise HTTPException(status_code=409, detail=detail) from e


@watchlist_router.delete("/{watchlist_id}/items/{ticker}", status_code=204)
async def remove_ticker(
    watchlist_id: int,
    ticker: str,
    service=Depends(get_watchlist_service),
):
    """Remove a ticker from a watchlist."""
    try:
        service.remove_ticker(watchlist_id=watchlist_id, ticker=ticker)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


# ── Helpers ─────────────────────────────────────────────────────────────


def _to_response(wl: object, service: object) -> dict:
    """Convert Watchlist entity to response dict with items."""
    wl_id = getattr(wl, "id", 0)
    raw_items = service.get_items(wl_id)  # type: ignore[union-attr]
    items = [
        {
            "id": i.id,
            "watchlist_id": i.watchlist_id,
            "ticker": i.ticker,
            "added_at": str(i.added_at),
            "notes": i.notes,
        }
        for i in raw_items
    ]

    return {
        "id": wl_id,
        "name": getattr(wl, "name", ""),
        "description": getattr(wl, "description", ""),
        "created_at": str(getattr(wl, "created_at", "")),
        "updated_at": str(getattr(wl, "updated_at", "")),
        "items": items,
    }
