# tests/unit/test_tax_sync_parity.py
"""G25 Cross-Surface Parity Tests — MEU-218 AC-218-9, AC-218-10.

Feature Intent Contract (G25 compliance):
  The sync_lots operation must produce identical results whether
  invoked via the service layer, API endpoint, or MCP tool.

  AC-218-9: Service and API return structurally identical SyncReport
  AC-218-10: All three surfaces (service, API, MCP) expose sync_lots

These tests verify structural parity, not integration — each surface
is tested independently with the same mock data.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from zorivest_api.dependencies import get_tax_service, require_unlocked_db
from zorivest_api.routes.tax import tax_router
from zorivest_core.services.tax_service import SyncConflict, SyncReport


def _canonical_report() -> SyncReport:
    """Canonical SyncReport for parity comparison."""
    return SyncReport(
        account_id=None,
        created=3,
        updated=1,
        skipped=5,
        conflicts=1,
        orphaned=2,
        conflict_details=[
            SyncConflict(
                lot_id="lot-T1",
                old_hash="aaa",
                new_hash="bbb",
                reason="User-modified lot has stale source hash",
            )
        ],
    )


# ── AC-218-9: Service ↔ API parity ──────────────────────────────────────


class TestServiceApiParity:
    """AC-218-9: API response is structurally identical to SyncReport fields."""

    def test_api_response_mirrors_service_report(self) -> None:
        """All SyncReport fields appear in the API JSON response."""
        report = _canonical_report()
        mock_svc = MagicMock()
        mock_svc.sync_lots.return_value = report

        app = FastAPI()
        app.include_router(tax_router)
        app.dependency_overrides[require_unlocked_db] = lambda: None
        app.dependency_overrides[get_tax_service] = lambda: mock_svc

        client = TestClient(app)
        response = client.post("/api/v1/tax/sync-lots")

        assert response.status_code == 200
        data = response.json()

        # All SyncReport fields must be present
        assert data["account_id"] is None
        assert data["created"] == report.created
        assert data["updated"] == report.updated
        assert data["skipped"] == report.skipped
        assert data["conflicts"] == report.conflicts
        assert data["orphaned"] == report.orphaned

        # Conflict details structure
        assert len(data["conflict_details"]) == 1
        detail = data["conflict_details"][0]
        assert detail["lot_id"] == "lot-T1"
        assert detail["old_hash"] == "aaa"
        assert detail["new_hash"] == "bbb"
        assert detail["reason"] == "User-modified lot has stale source hash"


# ── AC-218-10: All three surfaces expose sync_lots ──────────────────────


class TestTriSurfaceAvailability:
    """AC-218-10: Verify all three surfaces expose the sync_lots action."""

    def test_service_has_sync_lots_method(self) -> None:
        """Service layer exposes sync_lots()."""
        from zorivest_core.services.tax_service import TaxService

        assert hasattr(TaxService, "sync_lots")
        assert callable(getattr(TaxService, "sync_lots"))

    def test_api_has_sync_lots_route(self) -> None:
        """API router includes POST /sync-lots."""
        from starlette.routing import Route

        route_paths = [r.path for r in tax_router.routes if isinstance(r, Route)]
        assert "/api/v1/tax/sync-lots" in route_paths

    def test_mcp_tool_source_references_sync_lots(self) -> None:
        """MCP compound tax-tool.ts includes sync_lots action registration.

        This is a source-level check (file content), not a runtime check,
        since the MCP server is TypeScript and can't be imported in pytest.
        """
        import pathlib
        import os

        # Resolve from project root
        project_root = pathlib.Path(os.environ.get("ZORIVEST_ROOT", ".")).resolve()
        mcp_file = project_root / "mcp-server" / "src" / "compound" / "tax-tool.ts"
        if not mcp_file.exists():
            # Fall back to p:\zorivest if we're running from a different cwd
            mcp_file = pathlib.Path("p:/zorivest/mcp-server/src/compound/tax-tool.ts")
        assert mcp_file.exists(), f"MCP compound tax-tool.ts not found at {mcp_file}"

        content = mcp_file.read_text(encoding="utf-8")
        assert "sync_lots" in content, (
            "sync_lots action not registered in compound tax-tool.ts"
        )
        assert "/tax/sync-lots" in content, (
            "MCP tool does not call the correct API endpoint"
        )

    def test_gui_has_sync_button_testid(self) -> None:
        """GUI TaxDashboard includes data-testid='tax-sync-button'.

        Source-level check since the GUI is a React component.
        """
        import pathlib
        import os

        project_root = pathlib.Path(os.environ.get("ZORIVEST_ROOT", ".")).resolve()
        dashboard_file = (
            project_root
            / "ui"
            / "src"
            / "renderer"
            / "src"
            / "features"
            / "tax"
            / "TaxDashboard.tsx"
        )
        if not dashboard_file.exists():
            dashboard_file = pathlib.Path(
                "p:/zorivest/ui/src/renderer/src/features/tax/TaxDashboard.tsx"
            )
        assert dashboard_file.exists(), (
            f"TaxDashboard.tsx not found at {dashboard_file}"
        )

        content = dashboard_file.read_text(encoding="utf-8")
        assert "SYNC_BUTTON" in content, (
            "GUI does not reference TAX_TEST_IDS.SYNC_BUTTON"
        )
        assert "/api/v1/tax/sync-lots" in content, (
            "GUI does not call the correct API endpoint"
        )

        # Verify the test ID constant maps to the expected string
        test_ids_file = dashboard_file.parent / "test-ids.ts"
        assert test_ids_file.exists(), "test-ids.ts not found"
        test_ids_content = test_ids_file.read_text(encoding="utf-8")
        assert "tax-sync-button" in test_ids_content, (
            "test-ids.ts does not contain 'tax-sync-button' string"
        )
