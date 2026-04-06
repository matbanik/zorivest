"""Integration test — MEU-65: ProviderConnectionService wired into app lifespan.

Acceptance criteria (from implementation-plan.md Remaining Work):
  AC-W1: app.state.provider_connection_service is ProviderConnectionService, not a stub
  AC-W2: provider list returns all 14 registered providers (incl Yahoo Finance + TradingView)
  AC-W3: signup_url is present on each ProviderStatus returned by the real service
  AC-W4: free providers (AuthMethod.NONE) are returned without has_api_key requirement

Source: docs/execution/plans/2026-03-21-market-data-gui/implementation-plan.md
        §Remaining Work to Close MEU-65 → Step 1
"""

from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from zorivest_api.main import create_app
from zorivest_api.stubs import StubProviderConnectionService
from zorivest_core.services.provider_connection_service import ProviderConnectionService


class TestProviderConnectionServiceNotStubbed:
    """AC-W1: The real ProviderConnectionService must be wired in main.py lifespan."""

    def test_provider_connection_service_is_real_not_stub(self) -> None:
        """AC-W1: app.state.provider_connection_service is ProviderConnectionService."""
        app = create_app()
        with TestClient(app) as _:  # triggers lifespan; client not needed
            svc = app.state.provider_connection_service
            # Should NOT be the stub
            assert not isinstance(svc, StubProviderConnectionService), (
                "StubProviderConnectionService is still wired — "
                "replace it with ProviderConnectionService(uow, ...) in main.py lifespan"
            )
            # Should be the real service
            assert isinstance(svc, ProviderConnectionService), (
                "app.state.provider_connection_service must be ProviderConnectionService"
            )


class TestProviderListViaRealService:
    """AC-W2/W3/W4: Real service returns all 14 providers with correct fields."""

    @pytest.fixture()
    def client(self) -> Generator[TestClient, None, None]:
        app = create_app()
        # DB must be unlocked for providers endpoint to respond (auth guard)
        with (
            pytest.MonkeyPatch().context() as mp,
            TestClient(app) as c,
        ):
            mp.setenv("ZORIVEST_DEV_UNLOCK", "1")
            app.state.db_unlocked = True
            yield c

    def test_provider_list_returns_14_providers(self, client: TestClient) -> None:
        """AC-W2: List endpoint returns all 14 registered providers."""
        resp = client.get("/api/v1/market-data/providers")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 14, (
            f"Expected 14 providers (12 registry + Yahoo Finance + TradingView), "
            f"got {len(data)}"
        )

    def test_all_providers_have_signup_url_field(self, client: TestClient) -> None:
        """AC-W3: signup_url field is present on all providers."""
        resp = client.get("/api/v1/market-data/providers")
        assert resp.status_code == 200
        for provider in resp.json():
            # Field must be present (may be None for providers without a URL)
            assert "signup_url" in provider, (
                f"Provider {provider.get('provider_name')} missing signup_url field"
            )

    def test_free_providers_are_included(self, client: TestClient) -> None:
        """AC-W4: Yahoo Finance and TradingView appear in the list."""
        resp = client.get("/api/v1/market-data/providers")
        assert resp.status_code == 200
        names = {p["provider_name"] for p in resp.json()}
        assert "Yahoo Finance" in names, "Yahoo Finance must be in provider list"
        assert "TradingView" in names, "TradingView must be in provider list"
