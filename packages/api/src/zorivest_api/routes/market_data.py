"""Market Data API routes — MEU-63 + MEU-192.

Source: docs/build-plan/08-market-data.md §8.4 (base 8 endpoints),
        docs/build-plan/08a-market-data-expansion.md §8a.11 (8 expansion endpoints).
"""

from __future__ import annotations

import re
from datetime import date
from enum import Enum
from typing import Annotated, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.functional_validators import BeforeValidator

from zorivest_api.dependencies import (
    get_market_data_service,
    get_provider_connection_service,
    require_unlocked_db,
)
from zorivest_core.services.market_data_service import MarketDataError
from zorivest_infra.market_data.provider_capabilities import CAPABILITIES_REGISTRY

market_data_router = APIRouter(prefix="/api/v1/market-data", tags=["market-data"])


def _validate_provider_name(provider: str | None) -> None:
    """Validate provider name against CAPABILITIES_REGISTRY.

    Raises HTTPException(404) for unknown providers.
    Source: §8a.11 — provider param must match ProviderCapabilities.
    """
    if provider is not None and provider not in CAPABILITIES_REGISTRY:
        raise HTTPException(
            404,
            detail=(
                f"Unknown provider '{provider}'. "
                f"Available: {', '.join(sorted(CAPABILITIES_REGISTRY))}"
            ),
        )


def _strip_whitespace(v: object) -> object:
    """Strip leading/trailing whitespace so min_length=1 rejects blank strings."""
    return v.strip() if isinstance(v, str) else v


StrippedStr = Annotated[str, BeforeValidator(_strip_whitespace)]


# ── Interval enum ───────────────────────────────────────────────────────


class IntervalEnum(str, Enum):
    """Valid OHLCV interval values. Source: §8a.11."""

    m1 = "1m"
    m5 = "5m"
    m15 = "15m"
    m30 = "30m"
    h1 = "1h"
    d1 = "1d"
    w1 = "1w"
    M1 = "1M"


# ── Ticker regex ────────────────────────────────────────────────────────

_TICKER_PATTERN = re.compile(r"^[A-Z.]{1,10}$")


# ── Expansion query params model ────────────────────────────────────────


class MarketDataExpansionParams(BaseModel):
    """Shared query params for 8 expansion endpoints.

    Source: §8a.11 field constraints table.
    Local Canon: renamed from MarketDataQueryParams to scope to expansion endpoints.
    """

    model_config = ConfigDict(extra="forbid")

    ticker: str = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Stock ticker (1-10 chars, uppercase alpha + dot)",
    )
    provider: Optional[str] = Field(None, description="Provider name override")
    interval: Optional[IntervalEnum] = Field(
        None, description="OHLCV interval (default 1d)"
    )
    start_date: Optional[date] = Field(None, description="Start date (ISO 8601)")
    end_date: Optional[date] = Field(None, description="End date (ISO 8601)")
    limit: Optional[int] = Field(
        None, ge=1, le=1000, description="Max results (1-1000)"
    )
    country: Optional[str] = Field(None, description="ISO 3166-1 alpha-2 code")

    @model_validator(mode="after")
    def _validate_constraints(self) -> MarketDataExpansionParams:
        """AC-3: ticker regex; AC-5: start_date ≤ end_date."""
        if not _TICKER_PATTERN.match(self.ticker):
            msg = f"Ticker must be 1-10 uppercase alpha/dot chars, got '{self.ticker}'"
            raise ValueError(msg)
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.start_date > self.end_date
        ):
            msg = "start_date must be ≤ end_date"
            raise ValueError(msg)
        return self


class EconomicCalendarParams(BaseModel):
    """Query params for economic-calendar (no ticker required)."""

    model_config = ConfigDict(extra="forbid")

    country: Optional[str] = Field(None, description="ISO 3166-1 alpha-2 code")
    start_date: Optional[date] = Field(None, description="Start date")
    end_date: Optional[date] = Field(None, description="End date")
    limit: Optional[int] = Field(None, ge=1, le=1000, description="Max results")


# ── Request schemas ─────────────────────────────────────────────────────


class ProviderConfigRequest(BaseModel):
    """Body for PUT /providers/{name}."""

    model_config = ConfigDict(extra="forbid")

    api_key: Optional[StrippedStr] = Field(None, min_length=1)
    api_secret: Optional[StrippedStr] = Field(None, min_length=1)
    rate_limit: Optional[int] = Field(None, ge=1)
    timeout: Optional[int] = Field(None, ge=1)
    is_enabled: Optional[bool] = None


# ── Quote & News endpoints ──────────────────────────────────────────────


@market_data_router.get("/quote", dependencies=[Depends(require_unlocked_db)])
async def get_quote(
    ticker: str = Query(..., description="Stock ticker symbol"),
    service: Any = Depends(get_market_data_service),
) -> Any:
    """Get a real-time stock quote with provider fallback."""
    try:
        return await service.get_quote(ticker)
    except MarketDataError as e:
        raise HTTPException(503, detail=str(e))


@market_data_router.get("/news", dependencies=[Depends(require_unlocked_db)])
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


@market_data_router.get("/search", dependencies=[Depends(require_unlocked_db)])
async def search_ticker(
    query: str = Query(..., description="Search query for symbols"),
    service: Any = Depends(get_market_data_service),
) -> Any:
    """Search for ticker symbols across providers."""
    try:
        return await service.search_ticker(query)
    except MarketDataError as e:
        raise HTTPException(503, detail=str(e))


@market_data_router.get("/sec-filings", dependencies=[Depends(require_unlocked_db)])
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


@market_data_router.get("/providers", dependencies=[Depends(require_unlocked_db)])
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
) -> dict[str, Any]:
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
    return {"status": "configured", "stub": True}


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
    return {"success": success, "message": message, "stub": True}


@market_data_router.delete(
    "/providers/{name}/key", dependencies=[Depends(require_unlocked_db)]
)
async def remove_provider_key(
    name: str,
    service: Any = Depends(get_provider_connection_service),
) -> dict[str, Any]:
    """Remove API key and disable provider."""
    try:
        await service.remove_api_key(name)
    except KeyError as e:
        raise HTTPException(404, detail=str(e))
    return {"status": "removed", "stub": True}


# ── Market data expansion endpoints (MEU-192) ──────────────────────────


@market_data_router.get("/ohlcv", dependencies=[Depends(require_unlocked_db)])
async def get_ohlcv(
    params: Annotated[MarketDataExpansionParams, Query()],
    service: Any = Depends(get_market_data_service),
) -> Any:
    """Get OHLCV candlestick bars. Source: §8a.11."""
    _validate_provider_name(params.provider)
    try:
        kwargs: dict[str, Any] = {}
        if params.start_date:
            kwargs["start_date"] = params.start_date
        if params.end_date:
            kwargs["end_date"] = params.end_date
        if params.limit:
            kwargs["limit"] = params.limit
        if params.provider:
            kwargs["provider"] = params.provider
        return await service.get_ohlcv(
            params.ticker,
            interval=params.interval.value if params.interval else "1d",
            **kwargs,
        )
    except MarketDataError as e:
        raise HTTPException(502, detail=str(e))


@market_data_router.get("/fundamentals", dependencies=[Depends(require_unlocked_db)])
async def get_fundamentals(
    params: Annotated[MarketDataExpansionParams, Query()],
    service: Any = Depends(get_market_data_service),
) -> Any:
    """Get company fundamentals snapshot. Source: §8a.11."""
    _validate_provider_name(params.provider)
    try:
        kwargs: dict[str, Any] = {}
        if params.provider:
            kwargs["provider"] = params.provider
        return await service.get_fundamentals(params.ticker, **kwargs)
    except MarketDataError as e:
        raise HTTPException(502, detail=str(e))


@market_data_router.get("/earnings", dependencies=[Depends(require_unlocked_db)])
async def get_earnings(
    params: Annotated[MarketDataExpansionParams, Query()],
    service: Any = Depends(get_market_data_service),
) -> Any:
    """Get earnings reports. Source: §8a.11."""
    _validate_provider_name(params.provider)
    try:
        kwargs: dict[str, Any] = {}
        if params.provider:
            kwargs["provider"] = params.provider
        return await service.get_earnings(params.ticker, **kwargs)
    except MarketDataError as e:
        raise HTTPException(502, detail=str(e))


@market_data_router.get("/dividends", dependencies=[Depends(require_unlocked_db)])
async def get_dividends(
    params: Annotated[MarketDataExpansionParams, Query()],
    service: Any = Depends(get_market_data_service),
) -> Any:
    """Get dividend records. Source: §8a.11."""
    _validate_provider_name(params.provider)
    try:
        kwargs: dict[str, Any] = {}
        if params.provider:
            kwargs["provider"] = params.provider
        return await service.get_dividends(params.ticker, **kwargs)
    except MarketDataError as e:
        raise HTTPException(502, detail=str(e))


@market_data_router.get("/splits", dependencies=[Depends(require_unlocked_db)])
async def get_splits(
    params: Annotated[MarketDataExpansionParams, Query()],
    service: Any = Depends(get_market_data_service),
) -> Any:
    """Get stock split history. Source: §8a.11."""
    _validate_provider_name(params.provider)
    try:
        kwargs: dict[str, Any] = {}
        if params.provider:
            kwargs["provider"] = params.provider
        return await service.get_splits(params.ticker, **kwargs)
    except MarketDataError as e:
        raise HTTPException(502, detail=str(e))


@market_data_router.get("/insider", dependencies=[Depends(require_unlocked_db)])
async def get_insider(
    params: Annotated[MarketDataExpansionParams, Query()],
    service: Any = Depends(get_market_data_service),
) -> Any:
    """Get insider transactions. Source: §8a.11."""
    _validate_provider_name(params.provider)
    try:
        kwargs: dict[str, Any] = {}
        if params.provider:
            kwargs["provider"] = params.provider
        return await service.get_insider(params.ticker, **kwargs)
    except MarketDataError as e:
        raise HTTPException(502, detail=str(e))


@market_data_router.get(
    "/economic-calendar", dependencies=[Depends(require_unlocked_db)]
)
async def get_economic_calendar(
    params: Annotated[EconomicCalendarParams, Query()],
    service: Any = Depends(get_market_data_service),
) -> Any:
    """Get economic calendar events. No ticker required. Source: §8a.11."""
    try:
        kwargs: dict[str, Any] = {}
        if params.country:
            kwargs["country"] = params.country
        if params.start_date:
            kwargs["start_date"] = params.start_date
        if params.end_date:
            kwargs["end_date"] = params.end_date
        if params.limit:
            kwargs["limit"] = params.limit
        return await service.get_economic_calendar(**kwargs)
    except MarketDataError as e:
        raise HTTPException(502, detail=str(e))


@market_data_router.get("/company-profile", dependencies=[Depends(require_unlocked_db)])
async def get_company_profile(
    params: Annotated[MarketDataExpansionParams, Query()],
    service: Any = Depends(get_market_data_service),
) -> Any:
    """Get company profile. Source: §8a.11."""
    _validate_provider_name(params.provider)
    try:
        kwargs: dict[str, Any] = {}
        if params.provider:
            kwargs["provider"] = params.provider
        return await service.get_company_profile(params.ticker, **kwargs)
    except MarketDataError as e:
        raise HTTPException(502, detail=str(e))
