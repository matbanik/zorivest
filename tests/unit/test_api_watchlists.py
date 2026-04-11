# tests/unit/test_api_watchlists.py
"""Watchlist API route tests (MEU-68).

Tests AC-8 (7 REST endpoints) and AC-10 (runtime wiring).
"""

from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from zorivest_api.main import create_app

BASE = "/api/v1/watchlists"


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    """Create a test client with full app wiring (lifespan-triggered)."""
    app = create_app()
    with TestClient(app) as c:
        yield c


# ── POST /api/v1/watchlists ─────────────────────────────────────────────


class TestCreateWatchlist:
    def test_create_201(self, client: TestClient) -> None:
        resp = client.post(
            BASE + "/", json={"name": "Tech", "description": "Tech stocks"}
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Tech"
        assert data["id"] > 0

    def test_create_duplicate_409(self, client: TestClient) -> None:
        client.post(BASE + "/", json={"name": "Dups"})
        resp = client.post(BASE + "/", json={"name": "Dups"})
        assert resp.status_code == 409
        # Value: verify error detail
        data = resp.json()
        assert "detail" in data


# ── GET /api/v1/watchlists ──────────────────────────────────────────────


class TestListWatchlists:
    def test_list_empty(self, client: TestClient) -> None:
        resp = client.get(BASE + "/")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_returns_created(self, client: TestClient) -> None:
        client.post(BASE + "/", json={"name": "A"})
        client.post(BASE + "/", json={"name": "B"})
        resp = client.get(BASE + "/")
        assert len(resp.json()) == 2


# ── GET /api/v1/watchlists/{id} ─────────────────────────────────────────


class TestGetWatchlist:
    def test_get_existing(self, client: TestClient) -> None:
        create_resp = client.post(BASE + "/", json={"name": "Fetch"})
        wl_id = create_resp.json()["id"]
        resp = client.get(f"{BASE}/{wl_id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Fetch"

    def test_get_nonexistent_404(self, client: TestClient) -> None:
        resp = client.get(f"{BASE}/999")
        assert resp.status_code == 404
        # Value: verify error detail
        data = resp.json()
        assert "detail" in data


# ── PUT /api/v1/watchlists/{id} ─────────────────────────────────────────


class TestUpdateWatchlist:
    def test_update_200(self, client: TestClient) -> None:
        create_resp = client.post(BASE + "/", json={"name": "Old"})
        wl_id = create_resp.json()["id"]
        resp = client.put(f"{BASE}/{wl_id}", json={"name": "New"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "New"

    def test_update_nonexistent_404(self, client: TestClient) -> None:
        resp = client.put(f"{BASE}/999", json={"name": "X"})
        assert resp.status_code == 404
        # Value: verify error detail
        data = resp.json()
        assert "detail" in data

    def test_update_duplicate_name_409(self, client: TestClient) -> None:
        client.post(BASE + "/", json={"name": "First"})
        create_resp = client.post(BASE + "/", json={"name": "Second"})
        wl_id = create_resp.json()["id"]
        resp = client.put(f"{BASE}/{wl_id}", json={"name": "First"})
        assert resp.status_code == 409


# ── DELETE /api/v1/watchlists/{id} ──────────────────────────────────────


class TestDeleteWatchlist:
    def test_delete_204(self, client: TestClient) -> None:
        create_resp = client.post(BASE + "/", json={"name": "Del"})
        wl_id = create_resp.json()["id"]
        resp = client.delete(f"{BASE}/{wl_id}")
        assert resp.status_code == 204

    def test_delete_nonexistent_404(self, client: TestClient) -> None:
        resp = client.delete(f"{BASE}/999")
        assert resp.status_code == 404
        # Value: verify error detail
        data = resp.json()
        assert "detail" in data


# ── POST /api/v1/watchlists/{id}/items ──────────────────────────────────


class TestAddTicker:
    def test_add_ticker_201(self, client: TestClient) -> None:
        create_resp = client.post(BASE + "/", json={"name": "Items"})
        wl_id = create_resp.json()["id"]
        resp = client.post(f"{BASE}/{wl_id}/items", json={"ticker": "AAPL"})
        assert resp.status_code == 201
        assert resp.json()["ticker"] == "AAPL"

    def test_add_duplicate_ticker_409(self, client: TestClient) -> None:
        create_resp = client.post(BASE + "/", json={"name": "DupItems"})
        wl_id = create_resp.json()["id"]
        client.post(f"{BASE}/{wl_id}/items", json={"ticker": "SPY"})
        resp = client.post(f"{BASE}/{wl_id}/items", json={"ticker": "SPY"})
        assert resp.status_code == 409


# ── DELETE /api/v1/watchlists/{id}/items/{ticker} ───────────────────────


class TestRemoveTicker:
    def test_remove_ticker_204(self, client: TestClient) -> None:
        create_resp = client.post(BASE + "/", json={"name": "RemItems"})
        wl_id = create_resp.json()["id"]
        client.post(f"{BASE}/{wl_id}/items", json={"ticker": "MSFT"})
        resp = client.delete(f"{BASE}/{wl_id}/items/MSFT")
        assert resp.status_code == 204


# ── Item-load failure path (F2 regression) ──────────────────────────────


@pytest.fixture()
def no_raise_client() -> Generator[TestClient, None, None]:
    """Test client that returns error responses instead of raising."""
    app = create_app()
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


class TestGetWatchlistItemLoadFailure:
    """Regression test: get_items() failure must surface as 500, not empty items."""

    def test_get_items_failure_returns_500(self, no_raise_client: TestClient) -> None:
        create_resp = no_raise_client.post(BASE + "/", json={"name": "FailItems"})
        wl_id = create_resp.json()["id"]

        # Monkeypatch get_items to raise
        original_get_items = no_raise_client.app.state.watchlist_service.get_items  # type: ignore[union-attr]

        def _raise(*a: object, **kw: object) -> None:
            raise ValueError("repo failure")

        no_raise_client.app.state.watchlist_service.get_items = _raise  # type: ignore[union-attr]

        try:
            resp = no_raise_client.get(f"{BASE}/{wl_id}")
            assert resp.status_code == 500
            data = resp.json()
            assert data["error"] == "internal_error"
        finally:
            no_raise_client.app.state.watchlist_service.get_items = original_get_items  # type: ignore[union-attr]


# ── Boundary Validation (MEU-BV7) ──────────────────────────────────────


class TestWatchlistBoundaryValidation:
    """BV7: Boundary hardening negative tests for watchlist write surfaces.

    Verifies extra="forbid", StrippedStr + min_length=1 per
    implementation-plan.md §MEU-BV7.
    """

    # AC-1: CreateWatchlistRequest extra fields → 422
    def test_create_extra_field_422(self, client: TestClient) -> None:
        resp = client.post(BASE + "/", json={"name": "Good", "sneaky": True})
        assert resp.status_code == 422

    # AC-2: UpdateWatchlistRequest extra fields → 422
    def test_update_extra_field_422(self, client: TestClient) -> None:
        create_resp = client.post(BASE + "/", json={"name": "Target"})
        wl_id = create_resp.json()["id"]
        resp = client.put(f"{BASE}/{wl_id}", json={"name": "Ok", "sneaky": True})
        assert resp.status_code == 422

    # AC-3: AddTickerRequest extra fields → 422
    def test_add_ticker_extra_field_422(self, client: TestClient) -> None:
        create_resp = client.post(BASE + "/", json={"name": "Tickers"})
        wl_id = create_resp.json()["id"]
        resp = client.post(
            f"{BASE}/{wl_id}/items", json={"ticker": "AAPL", "sneaky": True}
        )
        assert resp.status_code == 422

    # AC-4: Blank name on create → 422
    def test_create_blank_name_422(self, client: TestClient) -> None:
        resp = client.post(BASE + "/", json={"name": ""})
        assert resp.status_code == 422

    # AC-5: Whitespace-only name on create → 422
    def test_create_whitespace_name_422(self, client: TestClient) -> None:
        resp = client.post(BASE + "/", json={"name": "   "})
        assert resp.status_code == 422

    # AC-6: Blank ticker on add → 422
    def test_add_blank_ticker_422(self, client: TestClient) -> None:
        create_resp = client.post(BASE + "/", json={"name": "TickerBlank"})
        wl_id = create_resp.json()["id"]
        resp = client.post(f"{BASE}/{wl_id}/items", json={"ticker": ""})
        assert resp.status_code == 422

    # AC-7: Whitespace-only ticker on add → 422
    def test_add_whitespace_ticker_422(self, client: TestClient) -> None:
        create_resp = client.post(BASE + "/", json={"name": "TickerWS"})
        wl_id = create_resp.json()["id"]
        resp = client.post(f"{BASE}/{wl_id}/items", json={"ticker": "   "})
        assert resp.status_code == 422

    # AC-8: Blank name on update → 422 (create/update parity)
    def test_update_blank_name_422(self, client: TestClient) -> None:
        create_resp = client.post(BASE + "/", json={"name": "UpdateBlank"})
        wl_id = create_resp.json()["id"]
        resp = client.put(f"{BASE}/{wl_id}", json={"name": ""})
        assert resp.status_code == 422

    # AC-9: Whitespace-only name on update → 422 (create/update parity)
    def test_update_whitespace_name_422(self, client: TestClient) -> None:
        create_resp = client.post(BASE + "/", json={"name": "UpdateWS"})
        wl_id = create_resp.json()["id"]
        resp = client.put(f"{BASE}/{wl_id}", json={"name": "   "})
        assert resp.status_code == 422
