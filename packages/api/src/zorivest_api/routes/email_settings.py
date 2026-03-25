"""Email provider REST API — single-row SMTP config.

Source: 06f-gui-settings.md §Email Provider (MEU-73)
Endpoints:
  GET  /api/v1/settings/email        — get config (has_password bool)
  PUT  /api/v1/settings/email        — save config
  POST /api/v1/settings/email/test   — test SMTP connection

Registered **before** settings_router in main.py to prevent
the generic /{key} route from shadowing these static paths.
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from zorivest_api.dependencies import get_email_provider_service, require_unlocked_db

email_settings_router = APIRouter(
    prefix="/api/v1/settings/email",
    tags=["email-settings"],
    dependencies=[Depends(require_unlocked_db)],
)


# ── Schemas ────────────────────────────────────────────────────────────────


class EmailConfigResponse(BaseModel):
    provider_preset: Optional[str] = None
    smtp_host: Optional[str] = None
    port: Optional[int] = None
    security: Optional[str] = None
    username: Optional[str] = None
    has_password: bool = False
    from_email: Optional[str] = None


class EmailConfigRequest(BaseModel):
    provider_preset: Optional[str] = None
    smtp_host: Optional[str] = None
    port: Optional[int] = None
    security: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = ""  # empty = keep existing
    from_email: Optional[str] = None


class TestConnectionResponse(BaseModel):
    success: bool
    message: str


# ── Routes ─────────────────────────────────────────────────────────────────


@email_settings_router.get("", response_model=EmailConfigResponse)
async def get_email_config(
    svc: Any = Depends(get_email_provider_service),
) -> Any:
    """Get current email provider config.

    AC-E1: has_password is a bool, raw password is never returned.
    AC-E5: returns safe defaults when not yet configured (no 500).
    """
    return svc.get_config()


@email_settings_router.put("", response_model=EmailConfigResponse)
async def save_email_config(
    body: EmailConfigRequest,
    svc: Any = Depends(get_email_provider_service),
) -> Any:
    """Save email provider config.

    AC-E2: saves all 7 fields.
    AC-E3: empty password field keeps existing stored password.
    """
    svc.save_config(body.model_dump())
    return svc.get_config()


@email_settings_router.post("/test", response_model=TestConnectionResponse)
async def test_email_connection(
    svc: Any = Depends(get_email_provider_service),
) -> Any:
    """Send a test SMTP connection using stored credentials.

    AC-E4: returns {success: bool, message: str}.
    """
    result = svc.test_connection()
    if not result["success"]:
        raise HTTPException(status_code=422, detail=result["message"])
    return result
