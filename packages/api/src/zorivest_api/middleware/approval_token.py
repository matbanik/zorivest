# packages/api/src/zorivest_api/middleware/approval_token.py
"""FastAPI dependency for CSRF approval token validation.

Validates the X-Approval-Token header on the POST /policies/{id}/approve
endpoint by calling back to the Electron main process's internal HTTP
validation endpoint.

Security: AI agents cannot forge tokens because they don't have access
to Electron's main process where tokens are generated.

Source: 09g §9G.1c
MEU: PH11 (approval-csrf-token)
"""

from __future__ import annotations

import logging
from typing import Any

import httpx
from fastapi import HTTPException, Request

logger = logging.getLogger(__name__)


class ApprovalTokenValidator:
    """Validates CSRF approval tokens via HTTP callback to Electron main process.

    The Electron main process exposes an internal HTTP endpoint on 127.0.0.1
    that validates tokens against its in-memory store. This class makes the
    HTTP call and interprets the response.

    Args:
        callback_url: Full URL to the Electron validation endpoint
                      (e.g., "http://127.0.0.1:17788/internal/validate-token")
    """

    def __init__(self, callback_url: str) -> None:
        self._callback_url = callback_url

    async def validate(self, token: str, policy_id: str) -> dict[str, Any]:
        """Validate a token via HTTP callback to Electron main process.

        Args:
            token: The approval token string from the X-Approval-Token header
            policy_id: The policy UUID from the URL path

        Returns:
            Dict with 'valid' (bool) and optional 'reason' (str) on failure
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    self._callback_url,
                    json={"token": token, "policy_id": policy_id},
                )
                if response.status_code == 200:
                    return response.json()
                return {"valid": False, "reason": "CALLBACK_ERROR"}
        except httpx.ConnectError:
            logger.warning(
                "Approval token callback unreachable at %s — "
                "Electron main process may not be running",
                self._callback_url,
            )
            return {"valid": False, "reason": "CALLBACK_UNREACHABLE"}
        except Exception:
            logger.exception("Unexpected error during approval token validation")
            return {"valid": False, "reason": "CALLBACK_ERROR"}


async def validate_approval_token(request: Request) -> None:
    """FastAPI dependency for approval endpoints.

    Validates the X-Approval-Token header by calling the Electron main
    process's internal validation endpoint.

    Raises:
        HTTPException(403): If the token is missing, invalid, or expired
    """
    token = request.headers.get("X-Approval-Token")
    if not token:
        raise HTTPException(
            status_code=403,
            detail=(
                "Approval requires a CSRF token from the GUI. "
                "This endpoint cannot be called directly by AI agents."
            ),
        )

    # Get the validator from app state (injected during startup)
    validator: ApprovalTokenValidator | None = getattr(
        request.app.state, "approval_token_validator", None
    )
    if validator is None:
        logger.warning(
            "No approval_token_validator configured in app state. "
            "Rejecting token — validator must be initialized at startup."
        )
        raise HTTPException(
            status_code=403,
            detail="Approval token validation is not configured.",
        )

    policy_id = request.path_params.get("policy_id", "")
    result = await validator.validate(token, policy_id)

    if not result.get("valid", False):
        reason = result.get("reason", "UNKNOWN")
        raise HTTPException(
            status_code=403,
            detail=f"Invalid approval token: {reason}",
        )
