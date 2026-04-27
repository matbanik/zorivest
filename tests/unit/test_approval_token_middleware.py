"""Tests for approval token middleware — FastAPI dependency for CSRF approval tokens.

Source: 09g §9G.1c, §9G.1d
MEU: PH11 (approval-csrf-token)
ACs: AC-5 through AC-7

These tests validate the FastAPI dependency that enforces the X-Approval-Token
header on the POST /policies/{id}/approve endpoint.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from zorivest_api.middleware.approval_token import (
    ApprovalTokenValidator,
    validate_approval_token,
)


# ── Fixtures ────────────────────────────────────────────────────────────


@pytest.fixture()
def mock_validator() -> ApprovalTokenValidator:
    """Create a mock validator that can be controlled per-test."""
    return ApprovalTokenValidator(
        callback_url="http://127.0.0.1:17788/internal/validate-token"
    )


@pytest.fixture()
def app(mock_validator: ApprovalTokenValidator) -> FastAPI:
    """Create a minimal FastAPI app with the approve endpoint protected."""
    from fastapi import Depends

    test_app = FastAPI()

    # Simulate the approve endpoint with the token dependency
    @test_app.post("/api/v1/scheduling/policies/{policy_id}/approve")
    async def approve_policy(
        policy_id: str,
        _token: None = Depends(validate_approval_token),
    ) -> dict:
        return {"id": policy_id, "approved": True}

    # Inject the validator into app state
    test_app.state.approval_token_validator = mock_validator

    return test_app


@pytest.fixture()
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


# ── Tests ───────────────────────────────────────────────────────────────


class TestApproveWithoutToken:
    """AC-5: POST /approve without X-Approval-Token returns 403."""

    def test_missing_header_returns_403(self, client: TestClient) -> None:
        response = client.post("/api/v1/scheduling/policies/test-policy-1/approve")
        assert response.status_code == 403
        body = response.json()
        assert "CSRF" in body["detail"] or "token" in body["detail"].lower()


class TestApproveWithInvalidToken:
    """AC-6: POST /approve with invalid/random token returns 403."""

    def test_random_token_returns_403(
        self, client: TestClient, mock_validator: ApprovalTokenValidator
    ) -> None:
        # Mock the validator to reject the token
        mock_validator.validate = AsyncMock(
            return_value={"valid": False, "reason": "TOKEN_NOT_FOUND"}
        )

        response = client.post(
            "/api/v1/scheduling/policies/test-policy-1/approve",
            headers={"X-Approval-Token": "random-invalid-token-abc123"},
        )
        assert response.status_code == 403
        body = response.json()
        assert "TOKEN_NOT_FOUND" in body["detail"]


class TestApproveWithValidToken:
    """AC-7: POST /approve with valid token succeeds (200)."""

    def test_valid_token_succeeds(
        self, client: TestClient, mock_validator: ApprovalTokenValidator
    ) -> None:
        # Mock the validator to accept the token
        mock_validator.validate = AsyncMock(return_value={"valid": True})

        response = client.post(
            "/api/v1/scheduling/policies/test-policy-1/approve",
            headers={"X-Approval-Token": "valid-token-abc123"},
        )
        assert response.status_code == 200, (
            f"Expected 200 but got {response.status_code}: {response.json()}"
        )
        body = response.json()
        assert body["id"] == "test-policy-1"
        assert body["approved"] is True
