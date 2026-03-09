"""Confirmation token route.

Source: 04c-api-auth.md §Confirmation
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from zorivest_api.auth.auth_service import InvalidActionError
from zorivest_api.dependencies import get_auth_service

confirm_router = APIRouter(prefix="/api/v1/confirmation-tokens", tags=["auth"])


class ConfirmationRequest(BaseModel):
    action: str


@confirm_router.post("", status_code=201)
async def create_confirmation_token(
    body: ConfirmationRequest,
    service=Depends(get_auth_service),
):
    """Generate a time-limited confirmation token for a destructive action."""
    try:
        result = service.create_confirmation_token(body.action)
        return result
    except InvalidActionError:
        raise HTTPException(400, f"Unknown destructive action: {body.action}")
