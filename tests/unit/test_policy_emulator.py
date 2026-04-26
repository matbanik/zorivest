# tests/unit/test_policy_emulator.py
"""RED phase tests for PolicyEmulator — AC-1..AC-11 (09f §9F.1/§9F.3).

Tests:
  - AC-1:  Valid policy passes PARSE
  - AC-2:  Invalid schema returns SCHEMA_INVALID EmulatorError
  - AC-3:  Broken ref returns REF_UNRESOLVED
  - AC-4:  SQL INSERT returns SQL_BLOCKED
  - AC-5:  Missing template returns TEMPLATE_MISSING
  - AC-6:  Existing template passes validation
  - AC-7:  SIMULATE populates mock outputs
  - AC-8:  RENDER returns SHA-256 hash, not raw content
  - AC-9:  Named template compiles with simulated data
  - AC-10: Phase subset works (PARSE only)
  - AC-11: Parse failure prevents VALIDATE/SIMULATE/RENDER
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from zorivest_core.ports.email_template_port import EmailTemplateDTO, EmailTemplatePort
from zorivest_core.services.policy_emulator import PolicyEmulator
from zorivest_core.services.secure_jinja import HardenedSandbox
from zorivest_core.services.sql_sandbox import SqlSandbox

# Trigger step type auto-registration so validate_policy's has_step() works
import zorivest_core.pipeline_steps  # noqa: F401


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_valid_policy_json(
    *,
    schema_version: int = 2,
    with_query_step: bool = False,
    with_send_step: bool = False,
    send_template_name: str = "",
    broken_ref: bool = False,
    insert_sql: bool = False,
) -> dict:
    """Build a valid policy JSON dict for testing.

    Uses schema_version=2 by default to allow query/compose steps.
    All send_params use only valid SendStep.Params fields.
    """
    steps: list[dict] = [
        {
            "id": "fetch_data",
            "type": "fetch",
            "params": {
                "provider": "yahoo",
                "data_type": "quote",
                "criteria": {"tickers": ["AAPL"]},
            },
        },
    ]

    if with_query_step:
        sql = "INSERT INTO trades VALUES (1)" if insert_sql else "SELECT * FROM trades"
        steps.append(
            {
                "id": "query_data",
                "type": "query",
                "params": {
                    "queries": [{"sql": sql, "binds": {}}],
                },
            }
        )

    if with_send_step:
        send_params: dict = {
            "channel": "email",
            "recipients": ["test@example.com"],
            "subject": "Test",
        }
        if send_template_name:
            send_params["body_template"] = send_template_name
        if broken_ref:
            # Use a valid SendStep.Params field (report_id) with a ref marker
            send_params["report_id"] = {"ref": "ctx.nonexistent_step.output"}

        steps.append(
            {
                "id": "send_email",
                "type": "send",
                "params": send_params,
            }
        )

    return {
        "schema_version": schema_version,
        "name": "test-policy",
        "trigger": {
            "cron_expression": "0 9 * * 1-5",
        },
        "steps": steps,
    }


class MockTemplatePort(EmailTemplatePort):
    """In-memory stub for EmailTemplatePort."""

    def __init__(self, templates: dict[str, EmailTemplateDTO] | None = None):
        self._templates = templates or {}

    def get_by_name(self, name: str) -> EmailTemplateDTO | None:
        return self._templates.get(name)

    def list_all(self) -> list[EmailTemplateDTO]:
        return list(self._templates.values())


def _make_template_dto(name: str = "morning-report") -> EmailTemplateDTO:
    return EmailTemplateDTO(
        name=name,
        description="Test template",
        subject_template="Subject: {{ date }}",
        body_html="<h1>Hello {{ name }}</h1>",
        body_format="html",
        required_variables=["date", "name"],
        sample_data_json='{"date": "2026-01-01", "name": "Test"}',
        is_default=False,
    )


@pytest.fixture
def sandbox() -> MagicMock:
    """Mock SqlSandbox — we only need validate_sql() for emulator tests."""
    mock = MagicMock(spec=SqlSandbox)
    mock.validate_sql.return_value = []  # Default: valid SQL
    return mock


@pytest.fixture
def template_engine() -> HardenedSandbox:
    """Real HardenedSandbox — no mocking needed for render tests."""
    return HardenedSandbox()


@pytest.fixture
def empty_template_port() -> MockTemplatePort:
    """Template port with no templates registered."""
    return MockTemplatePort()


@pytest.fixture
def populated_template_port() -> MockTemplatePort:
    """Template port with one template registered."""
    tmpl = _make_template_dto("morning-report")
    return MockTemplatePort({"morning-report": tmpl})


@pytest.fixture
def emulator(
    sandbox: MagicMock,
    template_engine: HardenedSandbox,
    empty_template_port: MockTemplatePort,
) -> PolicyEmulator:
    """PolicyEmulator with empty template port (default)."""
    return PolicyEmulator(
        sandbox=sandbox,
        template_engine=template_engine,
        template_port=empty_template_port,
    )


@pytest.fixture
def emulator_with_templates(
    sandbox: MagicMock,
    template_engine: HardenedSandbox,
    populated_template_port: MockTemplatePort,
) -> PolicyEmulator:
    """PolicyEmulator with populated template port."""
    return PolicyEmulator(
        sandbox=sandbox,
        template_engine=template_engine,
        template_port=populated_template_port,
    )


# ---------------------------------------------------------------------------
# AC-1: Valid policy passes PARSE
# ---------------------------------------------------------------------------


class TestParseValidPolicy:
    """AC-1: Valid policy JSON passes PARSE phase."""

    @pytest.mark.asyncio
    async def test_parse_valid_policy(self, emulator: PolicyEmulator) -> None:
        policy_json = _make_valid_policy_json()
        result = await emulator.emulate(policy_json)
        assert result.valid is True
        assert len(result.errors) == 0


# ---------------------------------------------------------------------------
# AC-2: Invalid schema returns SCHEMA_INVALID
# ---------------------------------------------------------------------------


class TestParseInvalidSchema:
    """AC-2: Invalid policy JSON returns structured EmulatorError."""

    @pytest.mark.asyncio
    async def test_parse_invalid_schema(self, emulator: PolicyEmulator) -> None:
        invalid_json = {"name": "missing-trigger-and-steps"}
        result = await emulator.emulate(invalid_json)
        assert result.valid is False
        assert any(e.phase == "PARSE" for e in result.errors)
        assert any(e.error_type == "SCHEMA_INVALID" for e in result.errors)

    @pytest.mark.asyncio
    async def test_parse_empty_dict(self, emulator: PolicyEmulator) -> None:
        result = await emulator.emulate({})
        assert result.valid is False
        assert result.errors[0].phase == "PARSE"


# ---------------------------------------------------------------------------
# AC-3: Broken ref returns REF_UNRESOLVED
# ---------------------------------------------------------------------------


class TestValidateRefIntegrity:
    """AC-3: Broken step reference returns REF_UNRESOLVED error."""

    @pytest.mark.asyncio
    async def test_validate_ref_integrity(self, emulator: PolicyEmulator) -> None:
        policy_json = _make_valid_policy_json(with_send_step=True, broken_ref=True)
        result = await emulator.emulate(policy_json)
        assert result.valid is False
        assert any(e.error_type == "REF_UNRESOLVED" for e in result.errors)


# ---------------------------------------------------------------------------
# AC-4: SQL INSERT returns SQL_BLOCKED
# ---------------------------------------------------------------------------


class TestValidateSqlBlocked:
    """AC-4: SQL with INSERT returns SQL_BLOCKED."""

    @pytest.mark.asyncio
    async def test_validate_sql_blocked(
        self,
        sandbox: MagicMock,
        template_engine: HardenedSandbox,
        empty_template_port: MockTemplatePort,
    ) -> None:
        # Configure sandbox to reject INSERT
        sandbox.validate_sql.return_value = ["DML/DDL blocked: Insert"]

        emu = PolicyEmulator(
            sandbox=sandbox,
            template_engine=template_engine,
            template_port=empty_template_port,
        )
        policy_json = _make_valid_policy_json(with_query_step=True, insert_sql=True)
        result = await emu.emulate(policy_json)
        assert result.valid is False
        assert any(e.error_type == "SQL_BLOCKED" for e in result.errors)


# ---------------------------------------------------------------------------
# AC-5: Missing template returns TEMPLATE_MISSING
# ---------------------------------------------------------------------------


class TestValidateTemplateMissing:
    """AC-5: Missing template returns TEMPLATE_MISSING."""

    @pytest.mark.asyncio
    async def test_validate_template_missing(self, emulator: PolicyEmulator) -> None:
        policy_json = _make_valid_policy_json(
            with_send_step=True, send_template_name="nonexistent"
        )
        result = await emulator.emulate(policy_json)
        assert result.valid is False
        assert any(e.error_type == "TEMPLATE_MISSING" for e in result.errors)


# ---------------------------------------------------------------------------
# AC-6: Existing template passes validation
# ---------------------------------------------------------------------------


class TestValidateTemplateExists:
    """AC-6: Existing template passes validation."""

    @pytest.mark.asyncio
    async def test_validate_template_exists(
        self, emulator_with_templates: PolicyEmulator
    ) -> None:
        policy_json = _make_valid_policy_json(
            with_send_step=True, send_template_name="morning-report"
        )
        result = await emulator_with_templates.emulate(policy_json)
        # Should have no TEMPLATE_MISSING errors
        template_errors = [
            e for e in result.errors if e.error_type == "TEMPLATE_MISSING"
        ]
        assert len(template_errors) == 0


# ---------------------------------------------------------------------------
# AC-7: SIMULATE populates mock outputs
# ---------------------------------------------------------------------------


class TestSimulateProducesMockOutputs:
    """AC-7: SIMULATE populates mock outputs for all steps."""

    @pytest.mark.asyncio
    async def test_simulate_produces_mock_outputs(
        self, emulator: PolicyEmulator
    ) -> None:
        policy_json = _make_valid_policy_json()
        result = await emulator.emulate(policy_json)
        assert result.mock_outputs is not None
        assert "fetch_data" in result.mock_outputs


# ---------------------------------------------------------------------------
# AC-8: RENDER returns SHA-256 hash, not raw content
# ---------------------------------------------------------------------------


class TestRenderReturnsHash:
    """AC-8: RENDER returns SHA-256 hash, never raw content."""

    @pytest.mark.asyncio
    async def test_render_returns_hash(
        self, emulator_with_templates: PolicyEmulator
    ) -> None:
        policy_json = _make_valid_policy_json(
            with_send_step=True,
            send_template_name="morning-report",
        )
        result = await emulator_with_templates.emulate(policy_json)
        assert result.template_preview_hash is not None
        # SHA-256 hex digest is exactly 64 chars
        assert len(result.template_preview_hash) == 64
        # Must not contain HTML
        assert "<" not in result.template_preview_hash


# ---------------------------------------------------------------------------
# AC-9: Named template compiles with simulated data
# ---------------------------------------------------------------------------


class TestRenderNamedTemplate:
    """AC-9: Named template compiles with simulated data."""

    @pytest.mark.asyncio
    async def test_render_named_template(
        self, emulator_with_templates: PolicyEmulator
    ) -> None:
        policy_json = _make_valid_policy_json(
            with_send_step=True,
            send_template_name="morning-report",
        )
        result = await emulator_with_templates.emulate(policy_json)
        # Should succeed — named template should compile
        assert result.valid is True
        assert result.template_preview_hash is not None


# ---------------------------------------------------------------------------
# AC-10: Phase subset (PARSE only)
# ---------------------------------------------------------------------------


class TestPhaseSubset:
    """AC-10: Can run individual phases (e.g., PARSE only)."""

    @pytest.mark.asyncio
    async def test_phase_subset(self, emulator: PolicyEmulator) -> None:
        policy_json = _make_valid_policy_json()
        result = await emulator.emulate(policy_json, phases=["PARSE"])
        assert result.valid is True
        assert result.phase == "PARSE"
        # SIMULATE didn't run → no mock outputs
        assert result.mock_outputs is None


# ---------------------------------------------------------------------------
# AC-11: Parse failure prevents VALIDATE/SIMULATE/RENDER
# ---------------------------------------------------------------------------


class TestEarlyStopOnParseError:
    """AC-11: Parse failure prevents VALIDATE/SIMULATE/RENDER."""

    @pytest.mark.asyncio
    async def test_early_stop_on_parse_error(self, emulator: PolicyEmulator) -> None:
        invalid_json = {"name": "bad", "no_trigger": True}
        result = await emulator.emulate(invalid_json)
        assert result.valid is False
        # Only PARSE errors — no VALIDATE/SIMULATE/RENDER errors
        assert all(e.phase == "PARSE" for e in result.errors)
        assert result.phase == "PARSE"
        assert result.mock_outputs is None
        assert result.template_preview_hash is None
