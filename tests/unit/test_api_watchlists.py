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
        resp = client.post(BASE + "/", json={"name": "Tech", "description": "Tech stocks"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Tech"
        assert data["id"] > 0

    def test_create_duplicate_409(self, client: TestClient) -> None:
        client.post(BASE + "/", json={"name": "Dups"})
        resp = client.post(BASE + "/", json={"name": "Dups"})
        assert resp.status_code == 409


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
