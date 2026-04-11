# tests/unit/test_api_backups.py
"""Tests for MEU-74: Backup & Restore API routes.

Red phase — written FIRST per TDD protocol.
FIC Acceptance Criteria: AC-1..AC-5.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from zorivest_api.main import create_app


@pytest.fixture()
def client():
    """HTTP test client with lifespan (services initialized)."""
    app = create_app()
    with TestClient(app, raise_server_exceptions=False) as c:
        app.state.db_unlocked = True
        app.state.start_time = __import__("time").time()
        yield c


# ── AC-1: POST /api/v1/backups (Create manual backup) ───────────────


class TestCreateBackup:
    """MEU-74: Create manual backup."""

    def test_create_returns_200(self, client: TestClient) -> None:
        """AC-1: POST /backups returns 200 on success."""
        mock_manager = MagicMock()
        mock_manager.create_backup.return_value = MagicMock(
            status=MagicMock(value="success"),
            backup_path=Path("/tmp/test.zvbak"),
            files_backed_up=2,
            elapsed_seconds=1.5,
            error=None,
        )
        client.app.state.backup_manager = mock_manager  # type: ignore[union-attr]
        resp = client.post("/api/v1/backups")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"

    def test_create_returns_error_on_failure(self, client: TestClient) -> None:
        """AC-1: POST /backups returns error details on failure."""
        mock_manager = MagicMock()
        mock_manager.create_backup.return_value = MagicMock(
            status=MagicMock(value="failed"),
            backup_path=None,
            files_backed_up=0,
            elapsed_seconds=0.1,
            error="No database files found",
        )
        client.app.state.backup_manager = mock_manager  # type: ignore[union-attr]
        resp = client.post("/api/v1/backups")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "failed"
        assert "error" in data

    def test_create_403_when_locked(self) -> None:
        """AC-5: POST /backups is mode-gated."""
        app = create_app()
        app.state.db_unlocked = False
        app.state.start_time = __import__("time").time()
        locked_client = TestClient(app)
        resp = locked_client.post("/api/v1/backups")
        assert resp.status_code == 403


# ── AC-2: GET /api/v1/backups (List backups) ─────────────────────────


class TestListBackups:
    """MEU-74: List backup files."""

    def test_list_returns_200(self, client: TestClient) -> None:
        """AC-2: GET /backups returns 200."""
        mock_manager = MagicMock()
        mock_manager.list_backups.return_value = []
        client.app.state.backup_manager = mock_manager  # type: ignore[union-attr]
        resp = client.get("/api/v1/backups")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_list_returns_backup_entries(
        self, client: TestClient, tmp_path: Path
    ) -> None:
        """AC-2: GET /backups returns file info for each backup."""
        # Create a real temp file so stat() works
        bak = tmp_path / "test-2026-01-01.zvbak"
        bak.write_text("dummy")
        mock_manager = MagicMock()
        mock_manager.list_backups.return_value = [bak]
        client.app.state.backup_manager = mock_manager  # type: ignore[union-attr]
        resp = client.get("/api/v1/backups")
        data = resp.json()
        assert len(data) == 1
        assert "path" in data[0]
        assert "size_bytes" in data[0]
        assert "modified_at" in data[0]

    def test_list_403_when_locked(self) -> None:
        """AC-5: GET /backups is mode-gated."""
        app = create_app()
        app.state.db_unlocked = False
        app.state.start_time = __import__("time").time()
        locked_client = TestClient(app)
        resp = locked_client.get("/api/v1/backups")
        assert resp.status_code == 403


# ── AC-3: POST /api/v1/backups/verify ────────────────────────────────


class TestVerifyBackup:
    """MEU-74: Non-destructive backup verification."""

    def test_verify_returns_200(self, client: TestClient) -> None:
        """AC-3: POST /backups/verify returns 200."""
        mock_recovery = MagicMock()
        mock_recovery.verify_backup.return_value = MagicMock(
            status=MagicMock(value="valid"),
            error=None,
        )
        client.app.state.backup_recovery_manager = mock_recovery  # type: ignore[union-attr]
        resp = client.post("/api/v1/backups/verify", json={"path": "/tmp/test.zvbak"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "valid"

    def test_verify_missing_path_422(self, client: TestClient) -> None:
        """AC-3: Missing path field → 422."""
        resp = client.post("/api/v1/backups/verify", json={})
        assert resp.status_code == 422


# ── AC-4: POST /api/v1/backups/restore ───────────────────────────────


class TestRestoreBackup:
    """MEU-74: Restore from backup file."""

    def test_restore_returns_200(self, client: TestClient) -> None:
        """AC-4: POST /backups/restore returns 200."""
        mock_recovery = MagicMock()
        mock_recovery.restore_backup.return_value = MagicMock(
            status=MagicMock(value="success"),
            error=None,
        )
        client.app.state.backup_recovery_manager = mock_recovery  # type: ignore[union-attr]
        resp = client.post("/api/v1/backups/restore", json={"path": "/tmp/test.zvbak"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"

    def test_restore_missing_path_422(self, client: TestClient) -> None:
        """AC-4: Missing path field → 422."""
        resp = client.post("/api/v1/backups/restore", json={})
        assert resp.status_code == 422

    def test_restore_403_when_locked(self) -> None:
        """AC-5: POST /backups/restore is mode-gated."""
        app = create_app()
        app.state.db_unlocked = False
        app.state.start_time = __import__("time").time()
        locked_client = TestClient(app)
        resp = locked_client.post(
            "/api/v1/backups/restore", json={"path": "/tmp/test.zvbak"}
        )
        assert resp.status_code == 403
