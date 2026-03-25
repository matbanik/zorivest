"""FastAPI dependency injection providers.

Source: 04-rest-api.md §Dependencies
"""

from __future__ import annotations

from fastapi import HTTPException, Request


async def require_unlocked_db(request: Request) -> None:
    """Mode-gating dependency: raises 403 if database is locked.

    Source: 04-rest-api.md §Mode-Gating
    """
    db_unlocked = getattr(request.app.state, "db_unlocked", False)
    if not db_unlocked:
        raise HTTPException(
            status_code=403,
            detail="Database is locked. Unlock via POST /api/v1/auth/unlock first.",
        )


# ── Service providers ───────────────────────────────────────────────────
# In production: resolved from app.state (set during lifespan/unlock).
# In tests: overridden via app.dependency_overrides.


async def get_trade_service(request: Request):  # noqa: ANN201
    """Resolve TradeService from app state."""
    svc = getattr(request.app.state, "trade_service", None)
    if svc is None:
        raise HTTPException(500, "TradeService not configured")
    return svc


async def get_image_service(request: Request):  # noqa: ANN201
    """Resolve ImageService from app state."""
    svc = getattr(request.app.state, "image_service", None)
    if svc is None:
        raise HTTPException(500, "ImageService not configured")
    return svc


async def get_account_service(request: Request):  # noqa: ANN201
    """Resolve AccountService from app state."""
    svc = getattr(request.app.state, "account_service", None)
    if svc is None:
        raise HTTPException(500, "AccountService not configured")
    return svc


async def get_auth_service(request: Request):  # noqa: ANN201
    """Resolve AuthService from app state."""
    svc = getattr(request.app.state, "auth_service", None)
    if svc is None:
        raise HTTPException(500, "AuthService not configured")
    return svc


async def get_settings_service(request: Request):  # noqa: ANN201
    """Resolve SettingsService from app state."""
    svc = getattr(request.app.state, "settings_service", None)
    if svc is None:
        raise HTTPException(500, "SettingsService not configured")
    return svc


async def get_guard_service(request: Request):  # noqa: ANN201
    """Resolve McpGuardService from app state."""
    svc = getattr(request.app.state, "guard_service", None)
    if svc is None:
        raise HTTPException(500, "McpGuardService not configured")
    return svc


async def get_analytics_service(request: Request):  # noqa: ANN201
    """Resolve StubAnalyticsService from app state."""
    svc = getattr(request.app.state, "analytics_service", None)
    if svc is None:
        raise HTTPException(500, "AnalyticsService not configured")
    return svc


async def get_review_service(request: Request):  # noqa: ANN201
    """Resolve StubReviewService from app state."""
    svc = getattr(request.app.state, "review_service", None)
    if svc is None:
        raise HTTPException(500, "ReviewService not configured")
    return svc


async def get_tax_service(request: Request):  # noqa: ANN201
    """Resolve StubTaxService from app state."""
    svc = getattr(request.app.state, "tax_service", None)
    if svc is None:
        raise HTTPException(500, "TaxService not configured")
    return svc


async def get_market_data_service(request: Request):  # noqa: ANN201
    """Resolve MarketDataService from app state."""
    svc = getattr(request.app.state, "market_data_service", None)
    if svc is None:
        raise HTTPException(500, "MarketDataService not configured")
    return svc


async def get_provider_connection_service(request: Request):  # noqa: ANN201
    """Resolve ProviderConnectionService from app state."""
    svc = getattr(request.app.state, "provider_connection_service", None)
    if svc is None:
        raise HTTPException(500, "ProviderConnectionService not configured")
    return svc


async def get_report_service(request: Request):  # noqa: ANN201
    """Resolve ReportService from app state (MEU-53)."""
    svc = getattr(request.app.state, "report_service", None)
    if svc is None:
        raise HTTPException(500, "ReportService not configured")
    return svc


async def get_watchlist_service(request: Request):  # noqa: ANN201
    """Resolve WatchlistService from app state (MEU-68)."""
    svc = getattr(request.app.state, "watchlist_service", None)
    if svc is None:
        raise HTTPException(500, "WatchlistService not configured")
    return svc


async def get_scheduling_service(request: Request):  # noqa: ANN201
    """Resolve SchedulingService from app state (MEU-89)."""
    svc = getattr(request.app.state, "scheduling_service", None)
    if svc is None:
        raise HTTPException(500, "SchedulingService not configured")
    return svc


async def get_scheduler_service(request: Request):  # noqa: ANN201
    """Resolve SchedulerService from app state (MEU-89)."""
    svc = getattr(request.app.state, "scheduler_service", None)
    if svc is None:
        raise HTTPException(500, "SchedulerService not configured")
    return svc


async def get_email_provider_service(request: Request):  # noqa: ANN201
    """Resolve EmailProviderService from app state (MEU-73)."""
    svc = getattr(request.app.state, "email_provider_service", None)
    if svc is None:
        raise HTTPException(500, "EmailProviderService not configured")
    return svc


# ── Authentication providers ───────────────────────────────────────────


async def require_authenticated(request: Request) -> dict:
    """Resolve session from Authorization: Bearer <token> header.

    Returns session dict if valid, raises 403 if missing/invalid.
    Source: AC-14 (Local Canon — auth_service.py)
    """
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(403, "Authentication required")
    token = auth_header[7:]  # Strip 'Bearer '
    auth_svc = getattr(request.app.state, "auth_service", None)
    if auth_svc is None:
        raise HTTPException(500, "AuthService not configured")
    session = auth_svc._sessions.get(token)
    if session is None:
        raise HTTPException(403, "Invalid or expired session")
    return session


async def require_admin(request: Request) -> dict:
    """Require admin role. Extends require_authenticated.

    Returns session dict if valid admin, raises 403 otherwise.
    """
    session = await require_authenticated(request)
    if session.get("role") != "admin":
        raise HTTPException(403, "Admin role required")
    return session
