"""GUI-API Seam Tests — catch integration bugs at layer boundaries.

These tests validate the contracts between the GUI and API that
standard unit tests miss. They cover:

1. Every updateable field round-trips correctly through PUT
2. UpdateTradeRequest covers all non-readonly Trade fields
3. DELETE returns 204 with empty body (no JSON)
4. List endpoint returns proper numeric types (not strings)
5. TradeResponse field names are a superset of what the GUI needs

Source: Seam testing gap analysis (2026-03-19)
"""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

os.environ["ZORIVEST_DEV_UNLOCK"] = "1"

from zorivest_api.main import app  # noqa: E402
from zorivest_api.routes.trades import (  # noqa: E402
    CreateTradeRequest,
    TradeResponse,
    UpdateTradeRequest,
)
from zorivest_core.domain.entities import Trade  # noqa: E402


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


SAMPLE_TRADE = {
    "exec_id": "SEAM-001",
    "time": "2026-03-19T10:00:00",
    "instrument": "SPY",
    "action": "BOT",
    "quantity": 100,
    "price": 500.00,
    "account_id": "DU999",
    "commission": 1.50,
    "realized_pnl": 0.0,
    "notes": "",
}


# ── 1. Every updateable field round-trips ───────────────────────────────


class TestUpdateFieldRoundTrips:
    """Each test updates ONE field and verifies it persists."""

    def _seed(self, client: TestClient) -> None:
        client.post("/api/v1/trades", json=SAMPLE_TRADE)

    def test_update_action_bot_to_sld(self, client: TestClient) -> None:
        self._seed(client)
        r = client.put("/api/v1/trades/SEAM-001", json={"action": "SLD"})
        assert r.status_code == 200
        assert r.json()["action"] == "SLD"

    def test_update_quantity(self, client: TestClient) -> None:
        self._seed(client)
        r = client.put("/api/v1/trades/SEAM-001", json={"quantity": 250})
        assert r.status_code == 200
        assert r.json()["quantity"] == 250

    def test_update_price(self, client: TestClient) -> None:
        self._seed(client)
        r = client.put("/api/v1/trades/SEAM-001", json={"price": 123.45})
        assert r.status_code == 200
        assert r.json()["price"] == 123.45

    def test_update_instrument(self, client: TestClient) -> None:
        self._seed(client)
        r = client.put("/api/v1/trades/SEAM-001", json={"instrument": "QQQ"})
        assert r.status_code == 200
        assert r.json()["instrument"] == "QQQ"

    def test_update_account_id(self, client: TestClient) -> None:
        self._seed(client)
        r = client.put("/api/v1/trades/SEAM-001", json={"account_id": "DU123"})
        assert r.status_code == 200
        assert r.json()["account_id"] == "DU123"

    def test_update_commission(self, client: TestClient) -> None:
        self._seed(client)
        r = client.put("/api/v1/trades/SEAM-001", json={"commission": 9.99})
        assert r.status_code == 200
        assert r.json()["commission"] == 9.99

    def test_update_realized_pnl(self, client: TestClient) -> None:
        self._seed(client)
        r = client.put("/api/v1/trades/SEAM-001", json={"realized_pnl": -50.0})
        assert r.status_code == 200
        assert r.json()["realized_pnl"] == -50.0

    def test_update_notes(self, client: TestClient) -> None:
        self._seed(client)
        r = client.put("/api/v1/trades/SEAM-001", json={"notes": "journal entry"})
        assert r.status_code == 200
        assert r.json()["notes"] == "journal entry"

    def test_update_time(self, client: TestClient) -> None:
        self._seed(client)
        r = client.put("/api/v1/trades/SEAM-001", json={"time": "2026-06-15T14:30:00"})
        assert r.status_code == 200
        assert "2026-06-15" in r.json()["time"]

    def test_update_multiple_fields_at_once(self, client: TestClient) -> None:
        self._seed(client)
        r = client.put("/api/v1/trades/SEAM-001", json={
            "action": "SLD",
            "quantity": 50,
            "price": 510.00,
            "notes": "closed half",
        })
        assert r.status_code == 200
        data = r.json()
        assert data["action"] == "SLD"
        assert data["quantity"] == 50
        assert data["price"] == 510.00
        assert data["notes"] == "closed half"


# ── 2. Schema completeness — UpdateTradeRequest covers Trade fields ─────


class TestUpdateSchemaCompleteness:
    """Verify UpdateTradeRequest covers all non-readonly Trade fields.

    The GUI sends all visible form fields on PUT. If the API schema is
    missing a field, the update is silently dropped — the exact bug class
    that caused 'cannot change Action from BOT to SLD'.
    """

    # Fields that are identity/system-managed, not editable via PUT
    READONLY_FIELDS = {"exec_id", "images", "report"}

    def test_update_schema_covers_all_editable_trade_fields(self) -> None:
        trade_fields = set(Trade.__dataclass_fields__.keys())
        update_fields = set(UpdateTradeRequest.model_fields.keys())
        editable = trade_fields - self.READONLY_FIELDS

        missing = editable - update_fields
        assert not missing, (
            f"UpdateTradeRequest is missing fields that Trade has: {missing}. "
            f"The GUI sends these on PUT but they will be silently dropped."
        )


# ── 3. Response format — DELETE returns empty body ──────────────────────


class TestResponseFormats:
    """Validate response shapes match what the GUI's apiFetch expects."""

    def _seed(self, client: TestClient) -> None:
        client.post("/api/v1/trades", json=SAMPLE_TRADE)

    def test_delete_returns_204_with_empty_body(self, client: TestClient) -> None:
        """apiFetch must not call .json() on 204 responses."""
        self._seed(client)
        r = client.delete("/api/v1/trades/SEAM-001")
        assert r.status_code == 204
        assert r.content == b"", (
            f"DELETE should return empty body, got: {r.content!r}"
        )

    def test_list_returns_items_array(self, client: TestClient) -> None:
        self._seed(client)
        r = client.get("/api/v1/trades?limit=10&offset=0")
        assert r.status_code == 200
        data = r.json()
        assert "items" in data, "List response must have 'items' key"
        assert isinstance(data["items"], list)

    def test_list_items_have_numeric_quantity(self, client: TestClient) -> None:
        """Quantity must be a number, not a string — prevents .toLocaleString() crash."""
        self._seed(client)
        r = client.get("/api/v1/trades?limit=10&offset=0")
        items = r.json()["items"]
        assert len(items) > 0
        for item in items:
            assert isinstance(item["quantity"], (int, float)), (
                f"quantity should be numeric, got {type(item['quantity']).__name__}: {item['quantity']}"
            )

    def test_list_items_have_numeric_commission(self, client: TestClient) -> None:
        self._seed(client)
        r = client.get("/api/v1/trades?limit=10&offset=0")
        items = r.json()["items"]
        for item in items:
            assert isinstance(item["commission"], (int, float)), (
                f"commission should be numeric, got {type(item['commission']).__name__}: {item['commission']}"
            )


# ── 4. GUI↔API field name alignment ────────────────────────────────────


class TestGuiApiFieldAlignment:
    """Verify TradeResponse fields are a superset of what the GUI needs.

    The GUI's TypeScript Trade interface must be a subset of TradeResponse.
    If TradeResponse is missing a field, the GUI shows undefined/blank.
    """

    # Fields the GUI Trade interface expects (from TradesTable.tsx)
    GUI_TRADE_FIELDS = {
        "exec_id", "instrument", "action", "quantity", "price",
        "account_id", "commission", "realized_pnl", "notes", "time",
    }

    # GUI expects image_count but it's computed, not from TradeResponse
    GUI_COMPUTED_FIELDS = {"image_count"}

    def test_trade_response_has_all_gui_fields(self) -> None:
        response_fields = set(TradeResponse.model_fields.keys())
        required = self.GUI_TRADE_FIELDS - self.GUI_COMPUTED_FIELDS

        missing = required - response_fields
        assert not missing, (
            f"TradeResponse is missing fields the GUI needs: {missing}. "
            f"The GUI will show 'undefined' or 'Invalid Date' for these."
        )

    def test_create_request_has_all_create_fields(self) -> None:
        """CreateTradeRequest must accept all fields the GUI sends on POST."""
        create_fields = set(CreateTradeRequest.model_fields.keys())
        # GUI sends these on create
        gui_create_fields = {
            "exec_id", "time", "instrument", "action", "quantity",
            "price", "account_id", "commission", "realized_pnl", "notes",
        }
        missing = gui_create_fields - create_fields
        assert not missing, (
            f"CreateTradeRequest is missing fields the GUI sends: {missing}."
        )
