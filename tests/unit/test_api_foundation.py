# tests/unit/test_api_foundation.py
"""Tests for MEU-23: FastAPI app factory, middleware, health, version.

Red phase — written FIRST per TDD protocol.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from zorivest_api.main import create_app


@pytest.fixture()
def app():
    """Create test app with mocked dependencies."""
    application = create_app()
    # Mock db state for testing
    application.state.db_unlocked = True
    application.state.start_time = __import__("time").time()
    return application


@pytest.fixture()
def client(app):
    """HTTP test client."""
    return TestClient(app)


# ── AC-1: App factory returns FastAPI with 7 tags ───────────────────────


class TestAppFactory:
    def test_create_app_returns_fastapi(self) -> None:
        """AC-1: create_app() returns FastAPI instance."""
        from fastapi import FastAPI

        app = create_app()
        assert isinstance(app, FastAPI)
        # Value: verify app has title and routes
        assert app.title is not None
        assert len(app.routes) > 0

    def test_app_has_seven_tags(self) -> None:
        """AC-1: App has 7 tags in openapi_tags."""
        app = create_app()
        tags = app.openapi_tags or []
        assert len(tags) == 10, (
            f"Expected 10 tags, got {len(tags)}: {[t['name'] for t in tags]}"
        )


# ── AC-4: Request-ID header ─────────────────────────────────────────────


class TestRequestIdMiddleware:
    def test_response_has_request_id_header(self, client: TestClient) -> None:
        """AC-4: Every response includes X-Request-ID header (UUID)."""
        resp = client.get("/api/v1/health")
        request_id = resp.headers.get("X-Request-ID")
        assert request_id is not None, "Missing X-Request-ID header"
        # Validate it's a UUID
        parsed = uuid.UUID(request_id)  # raises ValueError if invalid
        assert parsed.version == 4  # Value: verify UUID version

    def test_request_ids_are_unique(self, client: TestClient) -> None:
        """AC-4: Each request gets a unique request ID."""
        r1 = client.get("/api/v1/health")
        r2 = client.get("/api/v1/health")
        assert r1.headers["X-Request-ID"] != r2.headers["X-Request-ID"]


# ── AC-3: CORS ──────────────────────────────────────────────────────────


class TestCors:
    def test_cors_allows_localhost(self, client: TestClient) -> None:
        """AC-3: CORS allows localhost origins."""
        resp = client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert (
            resp.headers.get("access-control-allow-origin") == "http://localhost:3000"
        )

    def test_cors_allows_localhost_default_port(self, client: TestClient) -> None:
        """AC-3: CORS allows localhost without port."""
        resp = client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert resp.headers.get("access-control-allow-origin") == "http://localhost"

    def test_cors_rejects_external_origin(self, client: TestClient) -> None:
        """AC-3: CORS rejects non-localhost origins."""
        resp = client.options(
            "/api/v1/health",
            headers={
                "Origin": "https://evil.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert resp.headers.get("access-control-allow-origin") != "https://evil.com"


# ── AC-7: Health endpoint ───────────────────────────────────────────────


class TestHealthEndpoint:
    def test_health_returns_200(self, client: TestClient) -> None:
        """AC-7: GET /api/v1/health returns 200."""
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        # Value: verify health has expected fields
        data = resp.json()
        assert data["status"] == "ok"

    def test_health_response_fields(self, client: TestClient) -> None:
        """AC-7: HealthResponse has status, version, uptime_seconds, database."""
        resp = client.get("/api/v1/health")
        data = resp.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "uptime_seconds" in data
        assert isinstance(data["uptime_seconds"], (int, float))
        assert "database" in data
        assert "unlocked" in data["database"]

    def test_health_no_auth_required(self, app) -> None:
        """AC-7: Health endpoint requires no auth."""
        # Set DB to locked — health should still work
        app.state.db_unlocked = False
        client = TestClient(app)
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        # Value: verify health body is valid
        data = resp.json()
        assert data["status"] == "ok"


# ── AC-8: Version endpoint ──────────────────────────────────────────────


class TestVersionEndpoint:
    def test_version_returns_200(self, client: TestClient) -> None:
        """AC-8: GET /api/v1/version/ returns 200."""
        resp = client.get("/api/v1/version/")
        assert resp.status_code == 200
        # Value: verify version response is valid JSON
        data = resp.json()
        assert "version" in data

    def test_version_response_fields(self, client: TestClient) -> None:
        """AC-8: VersionResponse has version (SemVer) and context."""
        resp = client.get("/api/v1/version/")
        data = resp.json()
        assert "version" in data
        parts = data["version"].split(".")
        assert len(parts) >= 2, f"Expected SemVer, got: {data['version']}"
        assert data["context"] in {"frozen", "installed", "dev"}


# ── AC-5: ErrorEnvelope ─────────────────────────────────────────────────


class TestErrorEnvelope:
    def test_404_returns_error_envelope(self, client: TestClient) -> None:
        """AC-5: Unhandled HTTP errors return ErrorEnvelope format."""
        resp = client.get("/api/v1/nonexistent-route")
        assert resp.status_code == 404
        data = resp.json()
        assert "error" in data
        assert "detail" in data
        assert "request_id" in data

    def test_unhandled_exception_returns_500_envelope(self, app) -> None:
        """AC-5b: Unhandled exceptions are caught by general Exception handler."""

        @app.get("/api/v1/test-crash")
        async def crash_route():
            raise RuntimeError("kaboom")

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/api/v1/test-crash")
        assert resp.status_code == 500
        data = resp.json()
        assert data["error"] == "internal_error"
        assert "request_id" in data


# ── AC-9, AC-10: Schema validation ──────────────────────────────────────


class TestSchemas:
    def test_paginated_response_fields(self) -> None:
        """AC-9: PaginatedResponse has items, total, limit, offset."""
        from zorivest_api.schemas.common import PaginatedResponse

        resp = PaginatedResponse(items=["a", "b"], total=10, limit=50, offset=0)
        assert resp.items == ["a", "b"]
        assert resp.total == 10
        assert resp.limit == 50
        assert resp.offset == 0

    def test_error_envelope_fields(self) -> None:
        """AC-10: ErrorEnvelope has error, detail, request_id."""
        from zorivest_api.schemas.common import ErrorEnvelope

        env = ErrorEnvelope(error="not_found", detail="Not found", request_id="abc-123")
        assert env.error == "not_found"
        assert env.detail == "Not found"
        assert env.request_id == "abc-123"


# ── AC-6: Mode-gating ───────────────────────────────────────────────────


class TestModeGating:
    def test_mode_gating_403_when_locked(self, app) -> None:
        """AC-6: require_unlocked_db raises 403 when DB is locked."""
        from fastapi import Depends
        from zorivest_api.dependencies import require_unlocked_db

        # Add a test route with mode-gating
        @app.get("/api/v1/test-gated")
        async def gated_route(_=Depends(require_unlocked_db)):
            return {"ok": True}

        app.state.db_unlocked = False
        client = TestClient(app)
        resp = client.get("/api/v1/test-gated")
        assert resp.status_code == 403
        # Value: verify error detail
        data = resp.json()
        assert "detail" in data


# ── Integration: app-state wiring ─────────────────────────────────────────────


class TestAppStateWiring:
    """Verify services are wired in lifespan without dependency_overrides."""

    def test_auth_service_wired_in_lifespan(self) -> None:
        """Auth routes should work without dependency overrides."""
        from zorivest_api.main import create_app

        app = create_app()
        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.get("/api/v1/auth/status")
            assert resp.status_code == 200
            assert "locked" in resp.json()

    def test_unlock_propagates_db_unlocked(self) -> None:
        """Unlock should set app.state.db_unlocked so domain routes are 200."""
        from zorivest_api.main import create_app

        app = create_app()
        with TestClient(app, raise_server_exceptions=False) as client:
            # Pre-unlock: domain routes are 403
            resp = client.get("/api/v1/trades")
            assert resp.status_code == 403

            # Create key and unlock
            key_resp = client.post("/api/v1/auth/keys", json={"name": "test"})
            raw_key = key_resp.json()["raw_key"]
            unlock_resp = client.post("/api/v1/auth/unlock", json={"api_key": raw_key})
            assert unlock_resp.status_code == 200

            # Post-unlock: domain routes should not be 403
            resp = client.get("/api/v1/trades")
            assert resp.status_code == 200

    def test_lock_clears_db_unlocked(self) -> None:
        """Lock should set app.state.db_unlocked=False so domain routes return 403."""
        from zorivest_api.main import create_app

        app = create_app()
        with TestClient(app, raise_server_exceptions=False) as client:
            # Unlock first
            key_resp = client.post("/api/v1/auth/keys", json={"name": "test"})
            raw_key = key_resp.json()["raw_key"]
            client.post("/api/v1/auth/unlock", json={"api_key": raw_key})

            # Lock
            lock_resp = client.post("/api/v1/auth/lock")
            assert lock_resp.status_code == 200

            # Post-lock: domain routes should be 403 again
            resp = client.get("/api/v1/trades")
            assert resp.status_code == 403

    def test_domain_services_wired_in_lifespan(self) -> None:
        """Domain routes should return 200 (not 500) when db_unlocked=True."""
        from zorivest_api.main import create_app

        app = create_app()
        with TestClient(app, raise_server_exceptions=False) as client:
            # Force unlock to bypass auth flow
            app.state.db_unlocked = True

            # These should NOT be 500 "Service not configured"
            for path in ["/api/v1/trades", "/api/v1/accounts", "/api/v1/round-trips"]:
                resp = client.get(path)
                assert resp.status_code == 200, (
                    f"{path} returned {resp.status_code}: {resp.text}"
                )
