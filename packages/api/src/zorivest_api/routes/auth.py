"""Auth REST endpoints.

Source: 04c-api-auth.md
Unlock/lock/status + API key management.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from zorivest_api.auth.auth_service import (
    AlreadyUnlockedError,
    InvalidKeyError,
    RevokedKeyError,
)
from zorivest_api.dependencies import get_auth_service

auth_router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


# ── Schemas ─────────────────────────────────────────────────────────────


class UnlockRequest(BaseModel):
    api_key: str


class KeyCreateRequest(BaseModel):
    name: str
    role: str = "admin"


# ── Routes ──────────────────────────────────────────────────────────────


@auth_router.post("/unlock")
async def unlock(
    body: UnlockRequest, request: Request, service=Depends(get_auth_service)
):
    """Unlock database via envelope-encryption flow."""
    try:
        result = service.unlock(body.api_key)
        # Propagate unlock state to the app-level mode gate
        request.app.state.db_unlocked = True
        return result
    except InvalidKeyError:
        raise HTTPException(401, "Invalid API key")
    except RevokedKeyError:
        raise HTTPException(403, "API key has been revoked")
    except AlreadyUnlockedError:
        raise HTTPException(423, "Database is already unlocked")


@auth_router.post("/lock")
async def lock(request: Request, service=Depends(get_auth_service)):
    """Lock database and invalidate sessions."""
    service.lock()
    # Propagate lock state to the app-level mode gate
    request.app.state.db_unlocked = False
    return {"status": "locked"}


@auth_router.get("/status")
async def auth_status(service=Depends(get_auth_service)):
    """Get current auth status."""
    return service.get_status()


@auth_router.post("/keys", status_code=201)
async def create_api_key(body: KeyCreateRequest, service=Depends(get_auth_service)):
    """Create a new API key. Returns raw key exactly once."""
    result = service.create_key(body.name, body.role)
    return result


@auth_router.get("/keys")
async def list_api_keys(service=Depends(get_auth_service)):
    """List API keys (masked, never plaintext)."""
    return service.list_keys()


@auth_router.delete("/keys/{key_id}", status_code=204)
async def revoke_api_key(key_id: str, service=Depends(get_auth_service)):
    """Revoke an API key."""
    service.revoke_key(key_id)
