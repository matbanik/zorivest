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

from typing import Annotated, Any, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from pydantic.functional_validators import BeforeValidator

from zorivest_api.dependencies import get_email_provider_service, require_unlocked_db

email_settings_router = APIRouter(
    prefix="/api/v1/settings/email",
    tags=["email-settings"],
    dependencies=[Depends(require_unlocked_db)],
)


def _strip_whitespace(v: object) -> object:
    """Strip leading/trailing whitespace so min_length=1 rejects blank strings."""
    return v.strip() if isinstance(v, str) else v


StrippedStr = Annotated[str, BeforeValidator(_strip_whitespace)]

# Closed preset set matching GUI PRESETS map (EmailSettingsPage.tsx L22–27)
# and spec (06f-gui-settings.md L245–250).
ProviderPreset = Literal["Gmail", "Brevo", "SendGrid", "Outlook", "Yahoo", "Custom"]

# Transport security matching spec (06f L236), input-index (L430),
# and GUI radio control (EmailSettingsPage.tsx L167).
SecurityMode = Literal["STARTTLS", "SSL"]


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
    model_config = ConfigDict(extra="forbid")

    provider_preset: Optional[ProviderPreset] = None
    smtp_host: Optional[StrippedStr] = Field(None, min_length=1)
    port: Optional[int] = Field(None, ge=1, le=65535)
    security: Optional[SecurityMode] = None
    username: Optional[StrippedStr] = Field(None, min_length=1)
    password: Optional[str] = ""  # empty = keep existing; NOT stripped
    from_email: Optional[StrippedStr] = Field(None, min_length=1)


class TestConnectionResponse(BaseModel):
    success: bool
    message: str


class EmailStatusResponse(BaseModel):
    """Minimal email readiness — no credentials exposed (AC-20)."""

    model_config = ConfigDict(extra="forbid")

    configured: bool
    provider: str | None = None
    host: str | None = None


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


@email_settings_router.get("/status", response_model=EmailStatusResponse)
async def get_email_status(
    svc: Any = Depends(get_email_provider_service),
) -> Any:
    """Get minimal SMTP readiness without exposing credentials.

    AC-20: Returns {configured, provider, host} — no username, password, port.
    Used by MCP get_email_config tool to check email readiness.
    """
    config = svc.get_config()
    has_host = bool(config.get("smtp_host"))
    has_password = bool(config.get("has_password"))
    configured = has_host and has_password

    return EmailStatusResponse(
        configured=configured,
        provider=config.get("provider_preset"),
        host=config.get("smtp_host"),
    )
