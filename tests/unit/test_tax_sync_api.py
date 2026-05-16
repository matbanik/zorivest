# tests/unit/test_tax_sync_api.py
"""FIC tests for Tax Sync API Endpoint — MEU-218 ACs 218.1–218.5.

Feature Intent Contract:
  POST /api/v1/tax/sync-lots triggers the sync pipeline and returns a SyncReport.
  The endpoint must produce identical results as the service layer.

  Behaviors:
    - AC-218-1: POST /api/v1/tax/sync-lots returns 200 with SyncReport JSON
    - AC-218-2: Optional account_id query parameter scopes the sync
    - AC-218-3: conflict_resolution='block' returns 409 on conflict
    - AC-218-4: Response includes created/updated/skipped/conflicts/orphaned counts
    - AC-218-5: SyncAbortError maps to 409 Conflict HTTP status

All tests written FIRST (RED phase) per TDD protocol.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from zorivest_api.dependencies import get_tax_service, require_unlocked_db
from zorivest_api.routes.tax import tax_router
from zorivest_core.domain.exceptions import SyncAbortError
from zorivest_core.services.tax_service import SyncConflict, SyncReport


def _make_client(mock_svc: MagicMock) -> TestClient:
    """Create a test client with tax router and dependency overrides."""
    app = FastAPI()
    app.include_router(tax_router)
    app.dependency_overrides[require_unlocked_db] = lambda: None
    app.dependency_overrides[get_tax_service] = lambda: mock_svc
    return TestClient(app)


# ── AC-218-1: POST /api/v1/tax/sync-lots returns 200 ────────────────────


class TestSyncLotsEndpoint:
    """AC-218-1: POST /sync-lots returns 200 with SyncReport JSON."""

    def test_sync_lots_returns_200(self) -> None:
        mock_report = SyncReport(
            account_id=None,
            created=5,
            updated=2,
            skipped=10,
            conflicts=0,
            orphaned=0,
        )
        mock_svc = MagicMock()
        mock_svc.sync_lots.return_value = mock_report

        client = _make_client(mock_svc)
        response = client.post("/api/v1/tax/sync-lots")

        assert response.status_code == 200
        data = response.json()
        assert data["created"] == 5
        assert data["updated"] == 2


# ── AC-218-2: account_id scoping ────────────────────────────────────────


class TestSyncLotsAccountScope:
    """AC-218-2: Optional account_id parameter scopes the sync."""

    def test_account_id_passed_to_service(self) -> None:
        mock_report = SyncReport(
            account_id="ACC-1",
            created=1,
            updated=0,
            skipped=0,
            conflicts=0,
            orphaned=0,
        )
        mock_svc = MagicMock()
        mock_svc.sync_lots.return_value = mock_report

        client = _make_client(mock_svc)
        response = client.post(
            "/api/v1/tax/sync-lots",
            json={"account_id": "ACC-1"},
        )

        assert response.status_code == 200
        mock_svc.sync_lots.assert_called_once_with(
            account_id="ACC-1", conflict_strategy=None
        )


# ── AC-218-4: Response shape ────────────────────────────────────────────


class TestSyncLotsResponseShape:
    """AC-218-4: Response includes all expected fields."""

    def test_response_has_all_count_fields(self) -> None:
        mock_report = SyncReport(
            account_id="ACC-1",
            created=3,
            updated=1,
            skipped=5,
            conflicts=2,
            orphaned=1,
            conflict_details=[
                SyncConflict(
                    lot_id="lot-T1",
                    old_hash="abc",
                    new_hash="def",
                    reason="test",
                )
            ],
        )
        mock_svc = MagicMock()
        mock_svc.sync_lots.return_value = mock_report

        client = _make_client(mock_svc)
        response = client.post(
            "/api/v1/tax/sync-lots",
            params={"account_id": "ACC-1"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "created" in data
        assert "updated" in data
        assert "skipped" in data
        assert "conflicts" in data
        assert "orphaned" in data
        assert "conflict_details" in data
        assert len(data["conflict_details"]) == 1


# ── AC-218-5: SyncAbortError → 409 ─────────────────────────────────────


class TestSyncLotsConflictResponse:
    """AC-218-5: SyncAbortError maps to 409 Conflict."""

    def test_block_mode_returns_409(self) -> None:
        mock_svc = MagicMock()
        mock_svc.sync_lots.side_effect = SyncAbortError(
            "Conflict on lot-T1: user-modified lot has changed source data"
        )

        client = _make_client(mock_svc)
        response = client.post("/api/v1/tax/sync-lots")

        assert response.status_code == 409
        assert "conflict" in response.json()["detail"].lower()


# ── Boundary Input Contract (Finding #2) ────────────────────────────────


class TestSyncLotsBoundaryContract:
    """Strict body schema: unknown fields rejected, conflict_strategy accepted."""

    def test_unknown_fields_rejected_422(self) -> None:
        """POST with unknown JSON fields must return 422, not 200."""
        mock_svc = MagicMock()
        mock_svc.sync_lots.return_value = SyncReport(
            account_id=None,
            created=0,
            updated=0,
            skipped=0,
            conflicts=0,
            orphaned=0,
        )

        client = _make_client(mock_svc)
        response = client.post(
            "/api/v1/tax/sync-lots",
            json={"foo": "bar", "conflict_strategy": "block"},
        )

        assert response.status_code == 422

    def test_conflict_strategy_forwarded_to_service(self) -> None:
        """conflict_strategy from body is passed to service.sync_lots()."""
        mock_report = SyncReport(
            account_id=None,
            created=0,
            updated=0,
            skipped=0,
            conflicts=0,
            orphaned=0,
        )
        mock_svc = MagicMock()
        mock_svc.sync_lots.return_value = mock_report

        client = _make_client(mock_svc)
        response = client.post(
            "/api/v1/tax/sync-lots",
            json={"conflict_strategy": "block"},
        )

        assert response.status_code == 200
        mock_svc.sync_lots.assert_called_once()
        call_kwargs = mock_svc.sync_lots.call_args
        assert call_kwargs.kwargs.get("conflict_strategy") == "block" or (
            len(call_kwargs.args) > 0 and "block" in str(call_kwargs)
        )

    def test_body_accepts_account_id(self) -> None:
        """account_id in body is accepted and forwarded."""
        mock_report = SyncReport(
            account_id="ACC-1",
            created=0,
            updated=0,
            skipped=0,
            conflicts=0,
            orphaned=0,
        )
        mock_svc = MagicMock()
        mock_svc.sync_lots.return_value = mock_report

        client = _make_client(mock_svc)
        response = client.post(
            "/api/v1/tax/sync-lots",
            json={"account_id": "ACC-1"},
        )

        assert response.status_code == 200
        mock_svc.sync_lots.assert_called_once_with(
            account_id="ACC-1",
            conflict_strategy=None,
        )

    def test_invalid_conflict_strategy_returns_422(self) -> None:
        """Invalid conflict_strategy enum value returns 422."""
        mock_svc = MagicMock()
        client = _make_client(mock_svc)
        response = client.post(
            "/api/v1/tax/sync-lots",
            json={"conflict_strategy": "invalid_value"},
        )

        assert response.status_code == 422


# ── Wash Sale Scan Contract (Finding #3) ────────────────────────────────


class TestWashSaleScanTaxYear:
    """Caller-provided tax_year must be forwarded to service, not hardcoded."""

    def test_tax_year_from_body_forwarded_to_service(self) -> None:
        """POST with tax_year=2025 must call service with 2025, not current year."""
        mock_svc = MagicMock()
        mock_svc.scan_cross_account_wash_sales.return_value = []

        client = _make_client(mock_svc)
        response = client.post(
            "/api/v1/tax/wash-sales/scan",
            json={"tax_year": 2025},
        )

        assert response.status_code == 200
        mock_svc.scan_cross_account_wash_sales.assert_called_once_with(2025)

    def test_missing_tax_year_defaults_to_current_year(self) -> None:
        """POST with no body should default to current year."""
        from datetime import datetime, timezone

        mock_svc = MagicMock()
        mock_svc.scan_cross_account_wash_sales.return_value = []

        client = _make_client(mock_svc)
        response = client.post("/api/v1/tax/wash-sales/scan")

        assert response.status_code == 200
        expected_year = datetime.now(tz=timezone.utc).year
        mock_svc.scan_cross_account_wash_sales.assert_called_once_with(expected_year)

    def test_invalid_tax_year_returns_422(self) -> None:
        """tax_year outside valid range returns 422."""
        mock_svc = MagicMock()
        client = _make_client(mock_svc)
        response = client.post(
            "/api/v1/tax/wash-sales/scan",
            json={"tax_year": 1899},
        )

        assert response.status_code == 422
