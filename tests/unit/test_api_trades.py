# tests/unit/test_api_trades.py
"""Tests for MEU-24: Trade CRUD, images, round-trips REST endpoints.

Red phase — written FIRST per TDD protocol.
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from zorivest_core.domain.entities import ImageAttachment, Trade
from zorivest_core.domain.enums import ImageOwnerType, TradeAction
from zorivest_core.domain.exceptions import NotFoundError


@pytest.fixture()
def mock_services():
    """Create mock services for trade, image, and round-trip endpoints."""
    trade_svc = MagicMock()
    image_svc = MagicMock()
    return trade_svc, image_svc


@pytest.fixture()
def client(mock_services):
    """HTTP test client with mocked dependencies."""
    trade_svc, image_svc = mock_services

    from zorivest_api.main import create_app
    from zorivest_api.dependencies import require_unlocked_db

    app = create_app()
    app.state.db_unlocked = True
    app.state.start_time = __import__("time").time()

    # Override dependencies
    app.dependency_overrides[require_unlocked_db] = lambda: None

    # Inject mock services via dependency overrides
    from zorivest_api import dependencies as deps
    app.dependency_overrides[deps.get_trade_service] = lambda: trade_svc
    app.dependency_overrides[deps.get_image_service] = lambda: image_svc

    return TestClient(app), trade_svc, image_svc


def _sample_trade(**overrides) -> Trade:
    defaults = {
        "exec_id": "E001",
        "time": datetime(2025, 1, 15, 10, 30),
        "instrument": "AAPL",
        "action": TradeAction.BOT,
        "quantity": 100.0,
        "price": 150.50,
        "account_id": "ACC001",
        "commission": 1.0,
        "realized_pnl": 0.0,
    }
    defaults.update(overrides)
    return Trade(**defaults)


def _sample_image(image_id: int = 1) -> ImageAttachment:
    return ImageAttachment(
        id=image_id,
        owner_type=ImageOwnerType.TRADE,
        owner_id="E001",
        data=b"\x00" * 100,
        width=800,
        height=600,
        file_size=100,
        created_at=datetime(2025, 1, 15),
        mime_type="image/webp",
        caption="chart",
    )


# ── Trade CRUD ──────────────────────────────────────────────────────────

class TestCreateTrade:
    def test_create_trade_201(self, client) -> None:
        """AC-1: POST /trades creates trade and returns 201."""
        http, trade_svc, _ = client
        trade_svc.create_trade.return_value = _sample_trade()

        resp = http.post("/api/v1/trades", json={
            "exec_id": "E001",
            "time": "2025-01-15T10:30:00",
            "instrument": "AAPL",
            "action": "BOT",
            "quantity": 100.0,
            "price": 150.50,
            "account_id": "ACC001",
        })

        assert resp.status_code == 201
        data = resp.json()
        assert data["exec_id"] == "E001"
        trade_svc.create_trade.assert_called_once()


class TestListTrades:
    def test_list_trades_default(self, client) -> None:
        """AC-2: GET /trades returns paginated list."""
        http, trade_svc, _ = client
        trade_svc.list_trades.return_value = [_sample_trade()]

        resp = http.get("/api/v1/trades")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert len(data["items"]) == 1

    def test_list_trades_with_account_filter(self, client) -> None:
        """AC-2: GET /trades supports account_id filter."""
        http, trade_svc, _ = client
        trade_svc.list_trades.return_value = []

        resp = http.get("/api/v1/trades?account_id=ACC001")
        assert resp.status_code == 200
        trade_svc.list_trades.assert_called_once()
        call_kwargs = trade_svc.list_trades.call_args
        assert call_kwargs.kwargs.get("account_id") == "ACC001" or \
               (call_kwargs.args and "ACC001" in str(call_kwargs))

    def test_list_trades_with_sort(self, client) -> None:
        """AC-3: GET /trades supports sort param."""
        http, trade_svc, _ = client
        trade_svc.list_trades.return_value = []

        resp = http.get("/api/v1/trades?sort=-time")
        assert resp.status_code == 200


class TestGetTrade:
    def test_get_trade_200(self, client) -> None:
        """AC-4: GET /trades/{exec_id} returns trade."""
        http, trade_svc, _ = client
        trade_svc.get_trade.return_value = _sample_trade()

        resp = http.get("/api/v1/trades/E001")
        assert resp.status_code == 200
        assert resp.json()["exec_id"] == "E001"

    def test_get_trade_404(self, client) -> None:
        """AC-4: GET /trades/{exec_id} returns 404 for missing trade."""
        http, trade_svc, _ = client
        trade_svc.get_trade.side_effect = NotFoundError("Trade not found: E999")

        resp = http.get("/api/v1/trades/E999")
        assert resp.status_code == 404


class TestUpdateTrade:
    def test_update_trade_200(self, client) -> None:
        """AC-5: PUT /trades/{exec_id} updates trade."""
        http, trade_svc, _ = client
        trade_svc.update_trade.return_value = _sample_trade(commission=5.0)

        resp = http.put("/api/v1/trades/E001", json={"commission": 5.0})
        assert resp.status_code == 200


class TestDeleteTrade:
    def test_delete_trade_204(self, client) -> None:
        """AC-6: DELETE /trades/{exec_id} returns 204."""
        http, trade_svc, _ = client

        resp = http.delete("/api/v1/trades/E001")
        assert resp.status_code == 204
        trade_svc.delete_trade.assert_called_once_with("E001")


# ── Trade images ────────────────────────────────────────────────────────

class TestTradeImages:
    def test_list_trade_images(self, client) -> None:
        """AC-8: GET /trades/{exec_id}/images returns image list."""
        http, _, image_svc = client
        image_svc.get_images_for_owner.return_value = [_sample_image()]

        resp = http.get("/api/v1/trades/E001/images")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1


# ── Global image routes ─────────────────────────────────────────────────

class TestGlobalImages:
    def test_get_image_metadata(self, client) -> None:
        """AC-9: GET /images/{id} returns image metadata."""
        http, _, image_svc = client
        image_svc.get_image.return_value = _sample_image(42)

        resp = http.get("/api/v1/images/42")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == 42

    def test_get_thumbnail(self, client) -> None:
        """AC-9: GET /images/{id}/thumbnail returns image/webp bytes."""
        http, _, image_svc = client
        image_svc.get_thumbnail.return_value = b"\x00" * 10

        resp = http.get("/api/v1/images/42/thumbnail")
        assert resp.status_code == 200
        assert resp.headers.get("content-type") == "image/webp"

    def test_get_full_image(self, client) -> None:
        """AC-10: GET /images/{id}/full returns full image bytes."""
        http, _, image_svc = client
        image_svc.get_full_image.return_value = b"\x00" * 500

        resp = http.get("/api/v1/images/42/full")
        assert resp.status_code == 200


# ── Round-trips ─────────────────────────────────────────────────────────

class TestRoundTrips:
    def test_list_round_trips(self, client) -> None:
        """AC-11: GET /round-trips returns list via list_round_trips."""
        http, trade_svc, _ = client
        trade_svc.list_round_trips.return_value = [{"instrument": "AAPL"}]

        resp = http.get("/api/v1/round-trips?account_id=ACC001")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        trade_svc.list_round_trips.assert_called_once()

    def test_round_trips_accepts_canonical_filters(self, client) -> None:
        """AC-11b: Round-trip endpoint passes all canonical filters to service."""
        http, trade_svc, _ = client
        trade_svc.list_round_trips.return_value = []

        resp = http.get(
            "/api/v1/round-trips?account_id=ACC001&status=closed&ticker=AAPL&limit=25&offset=10"
        )
        assert resp.status_code == 200
        call_kwargs = trade_svc.list_round_trips.call_args
        assert call_kwargs.kwargs.get("status") == "closed"
        assert call_kwargs.kwargs.get("ticker") == "AAPL"
        assert call_kwargs.kwargs.get("limit") == 25
        assert call_kwargs.kwargs.get("offset") == 10


# ── Image upload ────────────────────────────────────────────────────────

class TestImageUpload:
    def test_upload_trade_image_201(self, client) -> None:
        """AC-12: POST /trades/{exec_id}/images uploads and attaches image."""
        http, _, image_svc = client
        image_svc.attach_image.return_value = 42

        resp = http.post(
            "/api/v1/trades/E001/images",
            files={"file": ("chart.webp", b"\x00" * 100, "image/webp")},
            data={"caption": "entry chart"},
        )
        assert resp.status_code == 201
        assert resp.json()["image_id"] == 42
        image_svc.attach_image.assert_called_once()
