# tests/unit/test_emulator_api.py
"""Tests for MEU-PH9: Emulator + template CRUD + db-schema + validate-sql REST endpoints.

Covers: AC-16 through AC-30m (REST portion — MCP tool tests are in test_mcp_pipeline_security.py).
Source: 09f §9F.1 (emulator), 09e §9E.2 (template CRUD), 05g (schema discovery)
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.unit


# ── Fixtures ────────────────────────────────────────────────────────────


class FakeTemplateRepo:
    """In-memory email template repository for REST endpoint tests."""

    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {}

    def get_by_name(self, name: str) -> Any:
        """Return template DTO or None."""
        data = self._store.get(name)
        if data is None:
            return None
        from zorivest_core.ports.email_template_port import EmailTemplateDTO

        return EmailTemplateDTO(**data)

    def get_model_by_name(self, name: str) -> Any:
        """Return raw dict (simulates ORM model)."""
        return self._store.get(name)

    def list_all(self) -> list[Any]:
        """Return all templates as DTOs."""
        from zorivest_core.ports.email_template_port import EmailTemplateDTO

        return [EmailTemplateDTO(**d) for d in self._store.values()]

    def create(self, template: Any) -> Any:
        """Insert a template."""
        if template.name in self._store:
            raise ValueError(f"Duplicate template: {template.name}")
        self._store[template.name] = {
            "name": template.name,
            "description": template.description,
            "subject_template": template.subject_template,
            "body_html": template.body_html,
            "body_format": template.body_format,
            "required_variables": [],
            "sample_data_json": template.sample_data_json,
            "is_default": getattr(template, "is_default", False),
        }
        return template

    def update(self, name: str, **kwargs: object) -> Any:
        """Update fields on a template."""
        if name not in self._store:
            raise ValueError(f"Template not found: {name}")
        self._store[name].update(kwargs)
        return self._store[name]

    def delete(self, name: str) -> None:
        """Delete a template."""
        data = self._store.get(name)
        if data is None:
            raise ValueError(f"Template not found: {name}")
        if data.get("is_default"):
            raise ValueError(f"Cannot delete default template: {name}")
        del self._store[name]


class FakeEmulator:
    """Minimal emulator mock for REST endpoint tests."""

    async def emulate(self, policy_dict: dict, phases: list[str] | None = None) -> Any:
        """Return a structured EmulatorResult-like object."""
        from zorivest_core.domain.emulator_models import EmulatorResult

        result = EmulatorResult()
        result.phase = (phases or ["PARSE", "VALIDATE", "SIMULATE", "RENDER"])[-1]
        return result


class FakeBudget:
    """Minimal budget mock — always allows."""

    def check_budget(self, policy_hash: str, response_bytes: int) -> None:
        pass


class FakeBudgetExceeded:
    """Budget mock that always raises SecurityError."""

    def check_budget(self, policy_hash: str, response_bytes: int) -> None:
        from zorivest_core.services.sql_sandbox import SecurityError

        raise SecurityError("Session byte budget exceeded: 70000 > 65536")


class FakeSqlSandbox:
    """Minimal SQL sandbox mock for REST endpoint tests."""

    DENY_TABLES = frozenset(
        {
            "settings",
            "market_provider_settings",
            "email_provider",
            "broker_configs",
            "mcp_guard",
        }
    )

    def __init__(self) -> None:
        import sqlite3

        self._connection = sqlite3.connect(":memory:", check_same_thread=False)
        # Create a trades table for samples test
        self._connection.execute(
            "CREATE TABLE trades (exec_id TEXT, instrument TEXT, price REAL)"
        )

    def validate_sql(self, sql: str) -> list[str]:
        """Simple validation — reject write statements."""
        upper = sql.strip().upper()
        for keyword in ("INSERT", "UPDATE", "DELETE", "DROP", "ALTER"):
            if upper.startswith(keyword):
                return [f"Blocked: {keyword} statement"]
        return []


@pytest.fixture()
def fake_template_repo() -> FakeTemplateRepo:
    return FakeTemplateRepo()


@pytest.fixture()
def fake_emulator() -> FakeEmulator:
    return FakeEmulator()


@pytest.fixture()
def fake_budget() -> FakeBudget:
    return FakeBudget()


@pytest.fixture()
def fake_sql_sandbox() -> FakeSqlSandbox:
    return FakeSqlSandbox()


@pytest.fixture()
def client(fake_template_repo, fake_emulator, fake_budget, fake_sql_sandbox):
    """HTTP test client with PH9 services wired via dependency overrides."""
    from zorivest_api.main import create_app
    from zorivest_api.dependencies import require_unlocked_db
    from zorivest_api import dependencies as deps

    app = create_app()
    app.state.db_unlocked = True
    app.state.start_time = __import__("time").time()

    # Wire PH9 services into app state
    app.state.template_repo = fake_template_repo
    app.state.policy_emulator = fake_emulator
    app.state.session_budget = fake_budget
    app.state.sql_sandbox = fake_sql_sandbox

    # Override DI providers
    app.dependency_overrides[require_unlocked_db] = lambda: None
    app.dependency_overrides[deps.get_trade_service] = lambda: MagicMock()
    app.dependency_overrides[deps.get_image_service] = lambda: MagicMock()
    app.dependency_overrides[deps.get_scheduling_service] = lambda: MagicMock()
    app.dependency_overrides[deps.get_scheduler_service] = lambda: MagicMock()

    return TestClient(app)


# ── Emulator Endpoint (AC-16) ───────────────────────────────────────────


class TestEmulatorRun:
    """AC-16: POST /scheduling/emulator/run returns structured EmulatorResult."""

    def test_emulator_run_returns_200(self, client) -> None:
        resp = client.post(
            "/api/v1/scheduling/emulator/run",
            json={
                "policy_json": {
                    "name": "test",
                    "trigger": {"cron_expression": "0 9 * * *", "enabled": True},
                    "steps": [{"id": "s1", "type": "fetch", "params": {}}],
                },
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        # F5: Strengthen — assert concrete types, not just key presence
        assert isinstance(data["valid"], bool)
        assert isinstance(data["errors"], list)
        assert "phase" in data

    def test_emulator_run_extra_field_422(self, client) -> None:
        """EmulateRequest(extra='forbid') rejects unknown fields."""
        resp = client.post(
            "/api/v1/scheduling/emulator/run",
            json={
                "policy_json": {"name": "test"},
                "extra_field": True,
            },
        )
        assert resp.status_code == 422

    def test_emulator_run_empty_policy_422(self, client) -> None:
        """Empty policy_json dict → 422."""
        resp = client.post(
            "/api/v1/scheduling/emulator/run",
            json={"policy_json": {}},
        )
        assert resp.status_code == 422

    def test_emulator_run_invalid_phase_422(self, client) -> None:
        """Invalid phase name → 422."""
        resp = client.post(
            "/api/v1/scheduling/emulator/run",
            json={
                "policy_json": {"name": "test"},
                "phases": ["PARSE", "INVALID"],
            },
        )
        assert resp.status_code == 422

    def test_emulator_run_budget_exceeded_returns_429(
        self, fake_emulator, fake_sql_sandbox, fake_template_repo
    ) -> None:
        """F1: When budget.check_budget raises SecurityError, endpoint returns 429."""
        from zorivest_api.main import create_app
        from zorivest_api.dependencies import require_unlocked_db
        from zorivest_api import dependencies as deps

        exceeded_budget = FakeBudgetExceeded()
        app = create_app()
        app.state.db_unlocked = True
        app.state.start_time = __import__("time").time()
        app.state.template_repo = fake_template_repo
        app.state.policy_emulator = fake_emulator
        app.state.session_budget = exceeded_budget
        app.state.sql_sandbox = fake_sql_sandbox
        app.dependency_overrides[require_unlocked_db] = lambda: None
        app.dependency_overrides[deps.get_trade_service] = lambda: MagicMock()
        app.dependency_overrides[deps.get_image_service] = lambda: MagicMock()
        app.dependency_overrides[deps.get_scheduling_service] = lambda: MagicMock()
        app.dependency_overrides[deps.get_scheduler_service] = lambda: MagicMock()

        exceeded_client = TestClient(app)
        resp = exceeded_client.post(
            "/api/v1/scheduling/emulator/run",
            json={
                "policy_json": {
                    "name": "test",
                    "trigger": {"cron_expression": "0 9 * * *", "enabled": True},
                    "steps": [{"id": "s1", "type": "fetch", "params": {}}],
                },
            },
        )
        assert resp.status_code == 429
        assert "budget" in resp.json()["detail"].lower()


# ── Validate SQL (AC-17) ────────────────────────────────────────────────


class TestValidateSql:
    """AC-17: POST /scheduling/validate-sql returns {valid, errors}."""

    def test_validate_sql_returns_200(self, client) -> None:
        resp = client.post(
            "/api/v1/scheduling/validate-sql",
            json={"sql": "SELECT * FROM trades"},
        )
        assert resp.status_code == 200
        data = resp.json()
        # F5: Strengthen — assert concrete value for valid SQL
        assert data["valid"] is True
        assert data["errors"] == []

    def test_validate_sql_write_returns_invalid(self, client) -> None:
        """F5: Write SQL should return valid=False with error detail."""
        resp = client.post(
            "/api/v1/scheduling/validate-sql",
            json={"sql": "DROP TABLE trades"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is False
        assert len(data["errors"]) > 0
        assert "DROP" in data["errors"][0]

    def test_validate_sql_extra_field_422(self, client) -> None:
        """ValidateSqlRequest(extra='forbid') rejects unknown fields."""
        resp = client.post(
            "/api/v1/scheduling/validate-sql",
            json={"sql": "SELECT 1", "extra": True},
        )
        assert resp.status_code == 422

    def test_validate_sql_empty_string_422(self, client) -> None:
        """Empty sql string → 422 (min_length=1)."""
        resp = client.post(
            "/api/v1/scheduling/validate-sql",
            json={"sql": ""},
        )
        assert resp.status_code == 422


# ── DB Schema Discovery (AC-19, AC-20) ──────────────────────────────────


class TestDbSchema:
    """AC-19: GET /scheduling/db-schema excludes DENY_TABLES."""

    def test_db_schema_returns_200(self, client) -> None:
        resp = client.get("/api/v1/scheduling/db-schema")
        assert resp.status_code == 200

    def test_db_schema_excludes_deny_tables(self, client) -> None:
        resp = client.get("/api/v1/scheduling/db-schema")
        assert resp.status_code == 200
        data = resp.json()
        table_names = [t["name"] for t in data]
        # DENY_TABLES from SqlSandbox
        for denied in ["settings", "market_provider_settings", "email_provider"]:
            assert denied not in table_names


class TestDbSamples:
    """AC-20: GET /scheduling/db-schema/samples/{table} rejects DENY_TABLES."""

    def test_denied_table_returns_403(self, client) -> None:
        resp = client.get("/api/v1/scheduling/db-schema/samples/settings")
        assert resp.status_code == 403

    def test_allowed_table_returns_200(self, client) -> None:
        resp = client.get("/api/v1/scheduling/db-schema/samples/trades")
        assert resp.status_code == 200

    def test_sql_injection_join_returns_error(self, client) -> None:
        """F3: Crafted table name with JOIN bypasses deny-only check."""
        resp = client.get(
            "/api/v1/scheduling/db-schema/samples/trades%20JOIN%20settings%20ON%201%3D1--"
        )
        # Must NOT return 200 — either 403 (denied) or 404 (not a real table)
        assert resp.status_code in (403, 404)

    def test_unknown_table_returns_404(self, client) -> None:
        """F3: Table that doesn't exist in sqlite_master → 404."""
        resp = client.get("/api/v1/scheduling/db-schema/samples/nonexistent_table_xyz")
        assert resp.status_code == 404

    def test_sql_injection_semicolon_returns_error(self, client) -> None:
        """F3: Semicolon injection attempt."""
        resp = client.get(
            "/api/v1/scheduling/db-schema/samples/trades%3B%20DROP%20TABLE%20trades"
        )
        assert resp.status_code in (403, 404)


# ── Template CRUD (AC-21..AC-25, AC-30m) ────────────────────────────────


class TestTemplateCreate:
    """AC-21: POST /scheduling/templates creates a template."""

    def test_create_returns_201(self, client) -> None:
        resp = client.post(
            "/api/v1/scheduling/templates",
            json={
                "name": "test-template",
                "body_html": "<h1>Hello</h1>",
                "body_format": "html",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["name"] == "test-template"

    def test_create_duplicate_returns_409(self, client, fake_template_repo) -> None:
        """AC-21: Duplicate name → 409."""
        # Pre-seed a template
        fake_template_repo._store["existing"] = {
            "name": "existing",
            "description": None,
            "subject_template": None,
            "body_html": "<p>Hi</p>",
            "body_format": "html",
            "required_variables": [],
            "sample_data_json": None,
            "is_default": False,
        }
        resp = client.post(
            "/api/v1/scheduling/templates",
            json={
                "name": "existing",
                "body_html": "<h1>Dup</h1>",
                "body_format": "html",
            },
        )
        assert resp.status_code == 409

    def test_create_extra_field_422(self, client) -> None:
        """EmailTemplateCreateRequest(extra='forbid') rejects unknown fields."""
        resp = client.post(
            "/api/v1/scheduling/templates",
            json={
                "name": "test",
                "body_html": "<h1>Hi</h1>",
                "body_format": "html",
                "extra": True,
            },
        )
        assert resp.status_code == 422

    def test_create_invalid_name_422(self, client) -> None:
        """Name must match ^[a-z0-9][a-z0-9_-]*$."""
        resp = client.post(
            "/api/v1/scheduling/templates",
            json={
                "name": "UPPER_CASE",
                "body_html": "<h1>Hi</h1>",
            },
        )
        assert resp.status_code == 422

    def test_create_invalid_body_format_422(self, client) -> None:
        """body_format must be 'html' or 'markdown'."""
        resp = client.post(
            "/api/v1/scheduling/templates",
            json={
                "name": "test-tpl",
                "body_html": "<h1>Hi</h1>",
                "body_format": "rtf",
            },
        )
        assert resp.status_code == 422


class TestTemplateGet:
    """AC-22: GET /scheduling/templates/{name}."""

    def test_get_returns_200(self, client, fake_template_repo) -> None:
        fake_template_repo._store["my-template"] = {
            "name": "my-template",
            "description": "Test",
            "subject_template": None,
            "body_html": "<h1>Hi</h1>",
            "body_format": "html",
            "required_variables": [],
            "sample_data_json": None,
            "is_default": False,
        }
        resp = client.get("/api/v1/scheduling/templates/my-template")
        assert resp.status_code == 200
        assert resp.json()["name"] == "my-template"

    def test_get_not_found_returns_404(self, client) -> None:
        resp = client.get("/api/v1/scheduling/templates/nonexistent")
        assert resp.status_code == 404


class TestTemplateList:
    """AC-23: GET /scheduling/templates returns all templates."""

    def test_list_returns_200(self, client, fake_template_repo) -> None:
        # F5: Seed a template and assert list content, not just status/type
        fake_template_repo._store["seeded"] = {
            "name": "seeded",
            "description": "Seeded",
            "subject_template": None,
            "body_html": "<p>Hi</p>",
            "body_format": "html",
            "required_variables": [],
            "sample_data_json": None,
            "is_default": False,
        }
        resp = client.get("/api/v1/scheduling/templates")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        names = [t["name"] for t in data]
        assert "seeded" in names


class TestTemplateUpdate:
    """AC-24: PATCH /scheduling/templates/{name}."""

    def test_update_returns_200(self, client, fake_template_repo) -> None:
        fake_template_repo._store["updatable"] = {
            "name": "updatable",
            "description": "Old",
            "subject_template": None,
            "body_html": "<p>old</p>",
            "body_format": "html",
            "required_variables": [],
            "sample_data_json": None,
            "is_default": False,
        }
        resp = client.patch(
            "/api/v1/scheduling/templates/updatable",
            json={"description": "New description"},
        )
        assert resp.status_code == 200
        # F5: Assert the updated value is returned and persisted
        assert resp.json()["description"] == "New description"
        assert (
            fake_template_repo._store["updatable"]["description"] == "New description"
        )

    def test_update_not_found_returns_404(self, client) -> None:
        resp = client.patch(
            "/api/v1/scheduling/templates/nonexistent",
            json={"description": "x"},
        )
        assert resp.status_code == 404


class TestTemplateDelete:
    """AC-30m: DELETE /scheduling/templates/{name}."""

    def test_delete_returns_204(self, client, fake_template_repo) -> None:
        fake_template_repo._store["deletable"] = {
            "name": "deletable",
            "description": None,
            "subject_template": None,
            "body_html": "<p>x</p>",
            "body_format": "html",
            "required_variables": [],
            "sample_data_json": None,
            "is_default": False,
        }
        resp = client.delete("/api/v1/scheduling/templates/deletable")
        assert resp.status_code == 204

    def test_delete_default_returns_403(self, client, fake_template_repo) -> None:
        """AC-30m: Deleting a default template → 403."""
        fake_template_repo._store["morning-check-in"] = {
            "name": "morning-check-in",
            "description": "Default",
            "subject_template": None,
            "body_html": "<p>Morning</p>",
            "body_format": "html",
            "required_variables": [],
            "sample_data_json": None,
            "is_default": True,
        }
        resp = client.delete("/api/v1/scheduling/templates/morning-check-in")
        assert resp.status_code == 403

    def test_delete_not_found_returns_404(self, client) -> None:
        resp = client.delete("/api/v1/scheduling/templates/nonexistent")
        assert resp.status_code == 404


class TestTemplatePreview:
    """AC-25: POST /scheduling/templates/{name}/preview."""

    def test_preview_returns_200(self, client, fake_template_repo) -> None:
        fake_template_repo._store["previewable"] = {
            "name": "previewable",
            "description": None,
            "subject_template": "Test — {{ date }}",
            "body_html": "<h1>Hello {{ name }}</h1>",
            "body_format": "html",
            "required_variables": ["date", "name"],
            "sample_data_json": '{"date": "2026-04-26", "name": "Mat"}',
            "is_default": False,
        }
        resp = client.post(
            "/api/v1/scheduling/templates/previewable/preview",
            json={},
        )
        assert resp.status_code == 200
        data = resp.json()
        # F5: Assert rendered content, not just status
        assert "body_rendered" in data
        assert "Mat" in data["body_rendered"]
        assert "subject_rendered" in data
        assert "2026-04-26" in data["subject_rendered"]

    def test_preview_not_found_returns_404(self, client) -> None:
        resp = client.post(
            "/api/v1/scheduling/templates/nonexistent/preview",
            json={},
        )
        assert resp.status_code == 404

    def test_preview_extra_field_422(self, client, fake_template_repo) -> None:
        """PreviewRequest(extra='forbid') rejects unknown fields."""
        fake_template_repo._store["previewable"] = {
            "name": "previewable",
            "description": None,
            "subject_template": None,
            "body_html": "<h1>Hi</h1>",
            "body_format": "html",
            "required_variables": [],
            "sample_data_json": None,
            "is_default": False,
        }
        resp = client.post(
            "/api/v1/scheduling/templates/previewable/preview",
            json={"extra": True},
        )
        assert resp.status_code == 422


# ── Emulator Mock Data Endpoint (AC-27: pipeline://emulator/mock-data) ──


class TestEmulatorMockData:
    """R1 correction: GET /scheduling/emulator/mock-data returns sample mock data per step type."""

    def test_emulator_mock_data_returns_200(self, client) -> None:
        """Endpoint returns 200 with a dict of step-type mock data sets."""
        resp = client.get("/api/v1/scheduling/emulator/mock-data")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict)

    def test_emulator_mock_data_contains_known_step_types(self, client) -> None:
        """Response includes mock data for fetch, query, transform, compose, send."""
        resp = client.get("/api/v1/scheduling/emulator/mock-data")
        data = resp.json()
        for step_type in ("fetch", "query", "transform", "compose", "send"):
            assert step_type in data, f"Missing mock data for step type: {step_type}"

    def test_emulator_mock_data_entry_structure(self, client) -> None:
        """Each step-type entry has _source_type and output keys."""
        resp = client.get("/api/v1/scheduling/emulator/mock-data")
        data = resp.json()
        for step_type, mock_entry in data.items():
            assert "_source_type" in mock_entry, f"{step_type}: missing _source_type"
            assert "output" in mock_entry, f"{step_type}: missing output"

    def test_emulator_mock_data_fetch_has_quotes(self, client) -> None:
        """Fetch step mock data includes a quotes array with ticker/price."""
        resp = client.get("/api/v1/scheduling/emulator/mock-data")
        data = resp.json()
        fetch_output = data["fetch"]["output"]
        assert "quotes" in fetch_output
        assert isinstance(fetch_output["quotes"], list)
        assert len(fetch_output["quotes"]) > 0
        assert "ticker" in fetch_output["quotes"][0]
        assert "price" in fetch_output["quotes"][0]
