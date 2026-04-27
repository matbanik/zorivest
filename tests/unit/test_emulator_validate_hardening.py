"""Tests for PH13: Emulator VALIDATE-phase hardening (AC-26..AC-33).

Source: 09g §9G.3, 09f-policy-emulator.md (extension)
MEU: PH13 (emulator-validate-hardening)

Tests validate 3 new validation checks in _run_validate():
  1. EXPLAIN SQL schema check (AC-26, AC-27)
  2. SMTP readiness for send steps (AC-28, AC-29)
  3. Step wiring validation for body_from_step (AC-30, AC-31, AC-32, AC-33)
"""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import MagicMock

import pytest

from zorivest_core.services.policy_emulator import PolicyEmulator

pytestmark = pytest.mark.unit


# ── Helpers ────────────────────────────────────────────────────────────────


def _run(coro: Any) -> Any:
    """Run an async coroutine synchronously."""
    return asyncio.run(coro)


def _minimal_policy(**overrides: Any) -> dict:
    """Build a minimal valid policy dict, mergeable with overrides."""
    base: dict[str, Any] = {
        "schema_version": 2,
        "name": "test-policy",
        "steps": [{"id": "placeholder", "type": "fetch", "params": {}}],
        "trigger": {"cron_expression": "0 8 * * 1-5"},
    }
    base.update(overrides)
    return base


def _query_step(
    step_id: str = "q1",
    sql: str = "SELECT * FROM trades",
) -> dict:
    """Build a query step dict."""
    return {
        "id": step_id,
        "type": "query",
        "params": {"queries": [{"sql": sql, "label": "test"}]},
    }


def _send_step(
    step_id: str = "s1",
    body_template: str | None = "default-report",
    body_from_step: str | None = None,
    channel: str = "email",
) -> dict:
    """Build a send step dict."""
    params: dict[str, Any] = {"channel": channel}
    if body_template:
        params["body_template"] = body_template
    if body_from_step:
        params["body_from_step"] = body_from_step
    return {"id": step_id, "type": "send", "params": params}


def _render_step(step_id: str = "r1") -> dict:
    """Build a render step dict."""
    return {"id": step_id, "type": "render", "params": {}}


def _make_emulator(
    sandbox: MagicMock,
    engine: MagicMock,
    template_port: MagicMock,
    smtp_configured: bool = True,
) -> PolicyEmulator:
    """Build an emulator with the given mocks."""
    return PolicyEmulator(
        sandbox=sandbox,
        template_engine=engine,
        template_port=template_port,
        email_config_checker=lambda: smtp_configured,
    )


# ── Fixtures ───────────────────────────────────────────────────────────────


@pytest.fixture()
def mock_sandbox() -> MagicMock:
    """SQL sandbox mock with EXPLAIN support."""
    sandbox = MagicMock()
    sandbox.validate_sql.return_value = []  # No AST errors by default
    sandbox.execute.return_value = [{"addr": 0, "opcode": "Init"}]
    return sandbox


@pytest.fixture()
def mock_template_port() -> MagicMock:
    """Template port mock — templates exist by default."""
    port = MagicMock()
    tmpl = MagicMock()
    tmpl.body_html = "<p>Report</p>"
    port.get_by_name.return_value = tmpl
    return port


@pytest.fixture()
def mock_engine() -> MagicMock:
    """Hardened Jinja sandbox mock."""
    engine = MagicMock()
    engine.render_safe.return_value = "<p>Rendered</p>"
    return engine


# ── AC-26/AC-27: EXPLAIN SQL catches schema errors ───────────────────────


class TestExplainSqlSchemaCheck:
    """AC-26/AC-27: EXPLAIN SQL validates column/table references."""

    def test_ac26_explain_catches_missing_table(
        self,
        mock_sandbox: MagicMock,
        mock_template_port: MagicMock,
        mock_engine: MagicMock,
    ) -> None:
        """AC-26: SQL referencing nonexistent table → SQL_SCHEMA_ERROR."""
        mock_sandbox.execute.side_effect = Exception("no such table: nonexistent")

        emulator = _make_emulator(mock_sandbox, mock_engine, mock_template_port)

        policy = _minimal_policy(
            steps=[_query_step(sql="SELECT * FROM nonexistent")],
        )

        result = _run(emulator.emulate(policy, phases=["PARSE", "VALIDATE"]))

        schema_errors = [e for e in result.errors if e.error_type == "SQL_SCHEMA_ERROR"]
        assert len(schema_errors) >= 1
        assert "nonexistent" in schema_errors[0].message.lower()

    def test_ac27_explain_passes_valid_sql(
        self,
        mock_sandbox: MagicMock,
        mock_template_port: MagicMock,
        mock_engine: MagicMock,
    ) -> None:
        """AC-27: Valid SQL with existing tables → no SQL_SCHEMA_ERROR."""
        mock_sandbox.execute.return_value = [{"addr": 0, "opcode": "Init"}]

        emulator = _make_emulator(mock_sandbox, mock_engine, mock_template_port)

        policy = _minimal_policy(
            steps=[_query_step(sql="SELECT * FROM trades")],
        )

        result = _run(emulator.emulate(policy, phases=["PARSE", "VALIDATE"]))

        schema_errors = [e for e in result.errors if e.error_type == "SQL_SCHEMA_ERROR"]
        assert len(schema_errors) == 0


# ── AC-28/AC-29: SMTP readiness for send steps ───────────────────────────


class TestSmtpReadinessCheck:
    """AC-28/AC-29: Send steps require SMTP to be configured."""

    def test_ac28_send_step_without_smtp_emits_error(
        self,
        mock_sandbox: MagicMock,
        mock_template_port: MagicMock,
        mock_engine: MagicMock,
    ) -> None:
        """AC-28: Policy with send step + SMTP not configured → SMTP_NOT_CONFIGURED."""
        emulator = _make_emulator(
            mock_sandbox,
            mock_engine,
            mock_template_port,
            smtp_configured=False,
        )

        policy = _minimal_policy(
            steps=[
                _send_step(
                    step_id="s1", body_template="default-report", channel="email"
                )
            ],
        )

        result = _run(emulator.emulate(policy, phases=["PARSE", "VALIDATE"]))

        smtp_errors = [
            e for e in result.errors if e.error_type == "SMTP_NOT_CONFIGURED"
        ]
        assert len(smtp_errors) >= 1
        assert result.valid is False

    def test_ac29_send_step_with_smtp_no_error(
        self,
        mock_sandbox: MagicMock,
        mock_template_port: MagicMock,
        mock_engine: MagicMock,
    ) -> None:
        """AC-29: Policy with send step + SMTP configured → no SMTP error."""
        emulator = _make_emulator(
            mock_sandbox,
            mock_engine,
            mock_template_port,
            smtp_configured=True,
        )

        policy = _minimal_policy(
            steps=[
                _send_step(
                    step_id="s1", body_template="default-report", channel="email"
                )
            ],
        )

        result = _run(emulator.emulate(policy, phases=["PARSE", "VALIDATE"]))

        smtp_errors = [
            e for e in result.errors if e.error_type == "SMTP_NOT_CONFIGURED"
        ]
        assert len(smtp_errors) == 0

    def test_local_file_send_without_smtp_no_error(
        self,
        mock_sandbox: MagicMock,
        mock_template_port: MagicMock,
        mock_engine: MagicMock,
    ) -> None:
        """Finding #2: local_file send step + SMTP not configured → no SMTP error."""
        emulator = _make_emulator(
            mock_sandbox,
            mock_engine,
            mock_template_port,
            smtp_configured=False,
        )

        policy = _minimal_policy(
            steps=[
                _send_step(
                    step_id="s1", body_template="default-report", channel="local_file"
                )
            ],
        )

        result = _run(emulator.emulate(policy, phases=["PARSE", "VALIDATE"]))

        smtp_errors = [
            e for e in result.errors if e.error_type == "SMTP_NOT_CONFIGURED"
        ]
        assert len(smtp_errors) == 0, (
            "local_file send steps must not trigger SMTP validation"
        )

    def test_mixed_channels_only_email_triggers_smtp_check(
        self,
        mock_sandbox: MagicMock,
        mock_template_port: MagicMock,
        mock_engine: MagicMock,
    ) -> None:
        """Finding #2: mixed policy with email + local_file → SMTP error for email channel."""
        emulator = _make_emulator(
            mock_sandbox,
            mock_engine,
            mock_template_port,
            smtp_configured=False,
        )

        policy = _minimal_policy(
            steps=[
                _send_step(
                    step_id="s1", body_template="default-report", channel="local_file"
                ),
                _send_step(
                    step_id="s2", body_template="default-report", channel="email"
                ),
            ],
        )

        result = _run(emulator.emulate(policy, phases=["PARSE", "VALIDATE"]))

        smtp_errors = [
            e for e in result.errors if e.error_type == "SMTP_NOT_CONFIGURED"
        ]
        assert len(smtp_errors) >= 1, (
            "SMTP check should fire when at least one email-channel send step exists"
        )


# ── AC-30..AC-33: Step wiring validation ──────────────────────────────────


class TestStepWiringValidation:
    """AC-30..AC-33: body_from_step references must point to valid steps."""

    def test_ac30_body_from_step_nonexistent_target(
        self,
        mock_sandbox: MagicMock,
        mock_template_port: MagicMock,
        mock_engine: MagicMock,
    ) -> None:
        """AC-30: body_from_step referencing nonexistent step → STEP_WIRING_ERROR."""
        emulator = _make_emulator(mock_sandbox, mock_engine, mock_template_port)

        policy = _minimal_policy(
            steps=[
                _send_step(
                    step_id="s1",
                    body_template=None,
                    body_from_step="nonexistent_step",
                ),
            ],
        )

        result = _run(emulator.emulate(policy, phases=["PARSE", "VALIDATE"]))

        wiring_errors = [
            e for e in result.errors if e.error_type == "STEP_WIRING_ERROR"
        ]
        assert len(wiring_errors) >= 1
        assert "nonexistent_step" in wiring_errors[0].message

    def test_ac31_body_from_step_wrong_type(
        self,
        mock_sandbox: MagicMock,
        mock_template_port: MagicMock,
        mock_engine: MagicMock,
    ) -> None:
        """AC-31: body_from_step → query step (not render/compose) → STEP_WIRING_ERROR."""
        emulator = _make_emulator(mock_sandbox, mock_engine, mock_template_port)

        policy = _minimal_policy(
            steps=[
                _query_step(step_id="q1"),
                _send_step(
                    step_id="s1",
                    body_template=None,
                    body_from_step="q1",
                ),
            ],
        )

        result = _run(emulator.emulate(policy, phases=["PARSE", "VALIDATE"]))

        wiring_errors = [
            e for e in result.errors if e.error_type == "STEP_WIRING_ERROR"
        ]
        assert len(wiring_errors) >= 1
        assert (
            "query" in wiring_errors[0].message.lower()
            or "render" in wiring_errors[0].message.lower()
        )

    def test_ac32_body_from_step_valid_render(
        self,
        mock_sandbox: MagicMock,
        mock_template_port: MagicMock,
        mock_engine: MagicMock,
    ) -> None:
        """AC-32: body_from_step → render step → no wiring error."""
        emulator = _make_emulator(mock_sandbox, mock_engine, mock_template_port)

        policy = _minimal_policy(
            steps=[
                _render_step(step_id="r1"),
                _send_step(
                    step_id="s1",
                    body_template=None,
                    body_from_step="r1",
                ),
            ],
        )

        result = _run(emulator.emulate(policy, phases=["PARSE", "VALIDATE"]))

        wiring_errors = [
            e for e in result.errors if e.error_type == "STEP_WIRING_ERROR"
        ]
        assert len(wiring_errors) == 0

    def test_ac33_no_send_steps_no_wiring_check(
        self,
        mock_sandbox: MagicMock,
        mock_template_port: MagicMock,
        mock_engine: MagicMock,
    ) -> None:
        """AC-33: Policy without send steps → no wiring validation needed."""
        emulator = _make_emulator(mock_sandbox, mock_engine, mock_template_port)

        policy = _minimal_policy(
            steps=[_query_step(step_id="q1")],
        )

        result = _run(emulator.emulate(policy, phases=["PARSE", "VALIDATE"]))

        wiring_errors = [
            e for e in result.errors if e.error_type == "STEP_WIRING_ERROR"
        ]
        assert len(wiring_errors) == 0


# ── Finding #1: Runtime wiring — email_config_checker in app.state ────────


class TestEmulatorRuntimeWiring:
    """Finding #1: PolicyEmulator must have email_config_checker wired at startup."""

    def test_app_state_emulator_has_email_checker(self) -> None:
        """Finding #1: create_app() → app.state.policy_emulator._email_config_checker is not None."""
        from fastapi.testclient import TestClient
        from zorivest_api.main import create_app

        app = create_app()
        with TestClient(app) as _:  # triggers lifespan
            emulator = app.state.policy_emulator
            assert emulator._email_config_checker is not None, (
                "PolicyEmulator in app.state must have email_config_checker wired "
                "from EmailProviderService — currently None means SMTP validation "
                "is skipped in production"
            )

    def test_app_state_emulator_checker_returns_bool(self) -> None:
        """Finding #1: The wired checker must return a bool (not raise)."""
        from fastapi.testclient import TestClient
        from zorivest_api.main import create_app

        app = create_app()
        with TestClient(app) as _:  # triggers lifespan
            emulator = app.state.policy_emulator
            checker = emulator._email_config_checker
            assert checker is not None
            result = checker()
            assert isinstance(result, bool), (
                f"email_config_checker must return bool, got {type(result)}"
            )
