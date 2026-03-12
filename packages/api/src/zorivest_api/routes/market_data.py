"""Market Data API routes — MEU-63.

Source: docs/build-plan/08-market-data.md §8.4.
8 endpoints for quotes, news, search, SEC filings, and provider management.
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from zorivest_api.dependencies import (
    get_market_data_service,
    get_provider_connection_service,
    require_unlocked_db,
)
from zorivest_core.services.market_data_service import MarketDataError

market_data_router = APIRouter(
    prefix="/api/v1/market-data", tags=["market-data"]
)


# ── Request schemas ─────────────────────────────────────────────────────


class ProviderConfigRequest(BaseModel):
    """Body for PUT /providers/{name}."""

    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    rate_limit: Optional[int] = None
    timeout: Optional[int] = None
    is_enabled: Optional[bool] = None


# ── Quote & News endpoints ──────────────────────────────────────────────


@market_data_router.get(
    "/quote", dependencies=[Depends(require_unlocked_db)]
)
async def get_quote(
    ticker: str = Query(..., description="Stock ticker symbol"),
    service: Any = Depends(get_market_data_service),
) -> Any:
    """Get a real-time stock quote with provider fallback."""
    try:
        return await service.get_quote(ticker)
    except MarketDataError as e:
        raise HTTPException(503, detail=str(e))


@market_data_router.get(
    "/news", dependencies=[Depends(require_unlocked_db)]
)
async def get_news(
    ticker: Optional[str] = Query(None, description="Optional ticker filter"),
    count: int = Query(5, ge=1, le=50, description="Number of articles"),
    service: Any = Depends(get_market_data_service),
) -> Any:
    """Get market news from news-capable providers."""
    try:
        return await service.get_news(ticker, count)
    except MarketDataError as e:
        raise HTTPException(503, detail=str(e))


@market_data_router.get(
    "/search", dependencies=[Depends(require_unlocked_db)]
)
async def search_ticker(
    query: str = Query(..., description="Search query for symbols"),
    service: Any = Depends(get_market_data_service),
) -> Any:
    """Search for ticker symbols across providers."""
    try:
        return await service.search_ticker(query)
    except MarketDataError as e:
        raise HTTPException(503, detail=str(e))


@market_data_router.get(
    "/sec-filings", dependencies=[Depends(require_unlocked_db)]
)
async def get_sec_filings(
    ticker: str = Query(..., description="Stock ticker symbol"),
    service: Any = Depends(get_market_data_service),
) -> Any:
    """Get SEC filings for a company."""
    try:
        return await service.get_sec_filings(ticker)
    except MarketDataError as e:
        raise HTTPException(503, detail=str(e))


# ── Provider management endpoints ───────────────────────────────────────


@market_data_router.get(
    "/providers", dependencies=[Depends(require_unlocked_db)]
)
async def list_providers(
    service: Any = Depends(get_provider_connection_service),
) -> Any:
    """List all providers with their status."""
    return await service.list_providers()


@market_data_router.put(
    "/providers/{name}", dependencies=[Depends(require_unlocked_db)]
)
async def configure_provider(
    name: str,
    body: ProviderConfigRequest,
    service: Any = Depends(get_provider_connection_service),
) -> dict[str, str]:
    """Update provider settings. Omitted fields are left unchanged."""
    try:
        await service.configure_provider(
            name,
            api_key=body.api_key,
            api_secret=body.api_secret,
            rate_limit=body.rate_limit,
            timeout=body.timeout,
            is_enabled=body.is_enabled,
        )
    except KeyError as e:
        raise HTTPException(404, detail=str(e))
    return {"status": "configured"}


@market_data_router.post(
    "/providers/{name}/test", dependencies=[Depends(require_unlocked_db)]
)
async def test_provider(
    name: str,
    service: Any = Depends(get_provider_connection_service),
) -> dict[str, Any]:
    """Test a provider's API connection."""
    try:
        success, message = await service.test_connection(name)
    except KeyError as e:
        raise HTTPException(404, detail=str(e))
    return {"success": success, "message": message}


@market_data_router.delete(
    "/providers/{name}/key", dependencies=[Depends(require_unlocked_db)]
)
async def remove_provider_key(
    name: str,
    service: Any = Depends(get_provider_connection_service),
) -> dict[str, str]:
    """Remove API key and disable provider."""
    try:
        await service.remove_api_key(name)
    except KeyError as e:
        raise HTTPException(404, detail=str(e))
    return {"status": "removed"}
