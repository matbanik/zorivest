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
