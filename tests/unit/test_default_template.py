# tests/unit/test_default_template.py
"""Tests for MEU-PH10: morning-check-in default template seed.

Validates that the morning-check-in template:
1. Exists in the database after migration/app startup
2. Has is_default=True (cannot be deleted via API)

Source: 09e §9E.1f (default templates)
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


class TestDefaultTemplateSeed:
    """PH10: morning-check-in template must be seeded and marked is_default."""

    def test_morning_checkin_exists(self, monkeypatch, tmp_path) -> None:
        """morning-check-in template exists after app startup."""
        from zorivest_api.main import create_app
        from zorivest_api.dependencies import require_unlocked_db
        from fastapi.testclient import TestClient

        db_file = tmp_path / "test_seed.db"
        monkeypatch.setenv("ZORIVEST_DB_URL", f"sqlite:///{db_file}")

        app = create_app()
        app.state.db_unlocked = True
        app.state.start_time = __import__("time").time()
        app.dependency_overrides[require_unlocked_db] = lambda: None

        with TestClient(app) as tc:
            resp = tc.get("/api/v1/scheduling/templates/morning-check-in")
            assert resp.status_code == 200
            data = resp.json()
            assert data["name"] == "morning-check-in"
            assert data["is_default"] is True

    def test_morning_checkin_undeletable(self, monkeypatch, tmp_path) -> None:
        """morning-check-in template cannot be deleted (is_default=True → 403)."""
        from zorivest_api.main import create_app
        from zorivest_api.dependencies import require_unlocked_db
        from fastapi.testclient import TestClient

        db_file = tmp_path / "test_seed2.db"
        monkeypatch.setenv("ZORIVEST_DB_URL", f"sqlite:///{db_file}")

        app = create_app()
        app.state.db_unlocked = True
        app.state.start_time = __import__("time").time()
        app.dependency_overrides[require_unlocked_db] = lambda: None

        with TestClient(app) as tc:
            resp = tc.delete("/api/v1/scheduling/templates/morning-check-in")
            assert resp.status_code == 403
