# tests/unit/test_store_render_step.py
"""TDD Red-phase tests for StoreReportStep + RenderStep (MEU-87).

Acceptance criteria AC-SR1..AC-SR15 per implementation-plan §9.6, §9.7.
"""

from __future__ import annotations

import sqlite3
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError


# ---------------------------------------------------------------------------
# AC-SR1: StoreReportStep auto-registers with type_name="store_report"
# ---------------------------------------------------------------------------


def test_AC_SR1_store_report_step_auto_registers():
    """StoreReportStep auto-registers in STEP_REGISTRY."""
    from zorivest_core.domain.step_registry import STEP_REGISTRY, get_step

    import zorivest_core.pipeline_steps  # noqa: F401

    from zorivest_core.pipeline_steps.store_report_step import StoreReportStep

    assert "store_report" in STEP_REGISTRY
    assert get_step("store_report") is StoreReportStep


# ---------------------------------------------------------------------------
# AC-SR2: RenderStep auto-registers with type_name="render"
# ---------------------------------------------------------------------------


def test_AC_SR2_render_step_auto_registers():
    """RenderStep auto-registers in STEP_REGISTRY."""
    from zorivest_core.domain.step_registry import STEP_REGISTRY, get_step

    import zorivest_core.pipeline_steps  # noqa: F401

    from zorivest_core.pipeline_steps.render_step import RenderStep

    assert "render" in STEP_REGISTRY
    assert get_step("render") is RenderStep


# ---------------------------------------------------------------------------
# AC-SR3: ReportSpec model validates section types
# ---------------------------------------------------------------------------


def test_AC_SR3_report_spec_validates_sections():
    """ReportSpec model validates section types."""
    from zorivest_core.domain.report_spec import (
        ChartSection,
        DataTableSection,
        MetricCardSection,
        ReportSpec,
    )

    spec = ReportSpec(
        name="Test Report",
        sections=[
            DataTableSection(title="Table", query="SELECT 1"),
            MetricCardSection(title="Metric", query="SELECT COUNT(*)", label="Total"),
            ChartSection(title="Chart", chart_type="candlestick", query="SELECT * FROM prices"),
        ],
    )

    assert len(spec.sections) == 3
    assert spec.sections[0].section_type == "data_table"
    assert spec.sections[1].section_type == "metric_card"
    assert spec.sections[2].section_type == "chart"


# ---------------------------------------------------------------------------
# AC-SR4: DataTableSection rejects max_rows > 1000
# ---------------------------------------------------------------------------


def test_AC_SR4_data_table_max_rows_limit():
    """DataTableSection rejects max_rows > 1000."""
    from zorivest_core.domain.report_spec import DataTableSection

    # Valid
    s = DataTableSection(title="Test", query="SELECT 1", max_rows=1000)
    assert s.max_rows == 1000

    # Invalid
    with pytest.raises(ValidationError):
        DataTableSection(title="Test", query="SELECT 1", max_rows=1001)


# ---------------------------------------------------------------------------
# AC-SR5: report_authorizer allows SELECT
# ---------------------------------------------------------------------------


def test_AC_SR5_authorizer_allows_select():
    """report_authorizer allows SELECT operations."""
    from zorivest_infra.security.sql_sandbox import report_authorizer

    # sqlite3.SQLITE_SELECT = 21
    result = report_authorizer(21, None, None, None, None)
    assert result == sqlite3.SQLITE_OK


# ---------------------------------------------------------------------------
# AC-SR6: report_authorizer denies INSERT/UPDATE/DELETE/DROP
# ---------------------------------------------------------------------------


def test_AC_SR6_authorizer_denies_writes():
    """report_authorizer denies INSERT/UPDATE/DELETE/DROP operations."""
    from zorivest_infra.security.sql_sandbox import report_authorizer

    # sqlite3.SQLITE_INSERT = 18, SQLITE_UPDATE = 23, SQLITE_DELETE = 9, SQLITE_DROP_TABLE = 11
    for action_code in [18, 23, 9, 11]:
        result = report_authorizer(action_code, None, None, None, None)
        assert result == sqlite3.SQLITE_DENY, f"Should deny action code {action_code}"


# ---------------------------------------------------------------------------
# AC-SR7: create_sandboxed_connection sets query_only
# ---------------------------------------------------------------------------


def test_AC_SR7_sandboxed_connection_query_only():
    """create_sandboxed_connection sets PRAGMA query_only."""
    from zorivest_infra.security.sql_sandbox import create_sandboxed_connection

    conn = create_sandboxed_connection(":memory:")

    # query_only should be enabled
    cursor = conn.execute("PRAGMA query_only")
    value = cursor.fetchone()[0]
    assert value == 1

    conn.close()


# ---------------------------------------------------------------------------
# AC-SR8: create_template_engine registers currency/percent filters
# ---------------------------------------------------------------------------


def test_AC_SR8_template_engine_filters():
    """create_template_engine registers currency and percent filters."""
    from zorivest_infra.rendering.template_engine import create_template_engine

    env = create_template_engine()

    assert "currency" in env.filters
    assert "percent" in env.filters

    # Test currency filter
    currency_fn = env.filters["currency"]
    assert currency_fn(1234.567) == "$1,234.57"

    # Test percent filter
    percent_fn = env.filters["percent"]
    assert percent_fn(0.1234) == "12.34%"


# ---------------------------------------------------------------------------
# AC-SR9: StoreReportStep Params validates required fields
# ---------------------------------------------------------------------------


def test_AC_SR9_store_report_params():
    """StoreReportStep.Params validates required fields."""
    from zorivest_core.pipeline_steps.store_report_step import StoreReportStep

    p = StoreReportStep.Params(
        report_name="Daily P&L",
        spec={"name": "test", "sections": []},
    )
    assert p.report_name == "Daily P&L"

    with pytest.raises(ValidationError):
        StoreReportStep.Params()  # Missing report_name


# ---------------------------------------------------------------------------
# AC-SR10: RenderStep Params defaults output_format="both"
# ---------------------------------------------------------------------------


def test_AC_SR10_render_step_params_defaults():
    """RenderStep.Params defaults output_format to 'both'."""
    from zorivest_core.pipeline_steps.render_step import RenderStep

    p = RenderStep.Params(template="default")
    assert p.output_format == "both"


# ---------------------------------------------------------------------------
# AC-SR11: render_candlestick returns dict with html and png keys
# ---------------------------------------------------------------------------


def test_AC_SR11_render_candlestick_keys():
    """render_candlestick returns dict with html and png_data_uri keys."""
    from zorivest_infra.rendering.chart_renderer import render_candlestick

    data = {
        "dates": ["2026-01-01", "2026-01-02"],
        "open": [100.0, 101.0],
        "high": [105.0, 106.0],
        "low": [99.0, 100.0],
        "close": [103.0, 104.0],
    }

    result = render_candlestick(data)

    assert "html" in result
    assert "png_data_uri" in result
    assert len(result["html"]) > 0
    # Verify png_data_uri is a valid base64 data URI (requires kaleido)
    if result["png_data_uri"]:  # Non-empty when kaleido is installed
        assert result["png_data_uri"].startswith("data:image/png;base64,")
        # Verify the base64 payload is non-trivial (> 100 chars for a real PNG)
        payload = result["png_data_uri"][len("data:image/png;base64,"):]
        assert len(payload) > 100, f"PNG payload too small: {len(payload)} chars"
    # Value: verify HTML contains valid plotly content markers
    assert "plotly" in result["html"].lower() or "<div" in result["html"]


# ---------------------------------------------------------------------------
# AC-SR12: render_pdf creates output directory
# ---------------------------------------------------------------------------


def test_AC_SR12_render_pdf_creates_directory(tmp_path):
    """render_pdf creates output directory if missing and produces a valid PDF."""
    from zorivest_infra.rendering.pdf_renderer import render_pdf

    output_dir = tmp_path / "reports" / "nested"
    output_file = output_dir / "test.pdf"

    result = render_pdf(
        html_content="<html><body><h1>Test Report</h1></body></html>",
        output_path=str(output_file),
    )

    # Directory was created
    assert output_dir.exists()
    # PDF file was actually produced
    assert output_file.exists()
    assert output_file.stat().st_size > 0
    # Return value matches output path
    assert result == str(output_file)


# ---------------------------------------------------------------------------
# AC-SR13: Both steps have side_effects=True
# ---------------------------------------------------------------------------


def test_AC_SR13_both_steps_have_side_effects():
    """StoreReportStep and RenderStep both declare side_effects=True."""
    from zorivest_core.pipeline_steps.render_step import RenderStep
    from zorivest_core.pipeline_steps.store_report_step import StoreReportStep

    assert StoreReportStep.side_effects is True
    assert RenderStep.side_effects is True


# ---------------------------------------------------------------------------
# AC-SR14: Live UoW test — ReportRepository persists snapshot fields
# ---------------------------------------------------------------------------


def test_AC_SR14_live_uow_report_snapshot():
    """ReportRepository.create() persists snapshot_json and snapshot_hash via live UoW."""
    from sqlalchemy import create_engine

    from zorivest_infra.database.models import Base
    from zorivest_infra.database.unit_of_work import SqlAlchemyUnitOfWork

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    uow = SqlAlchemyUnitOfWork(engine)
    with uow:
        report_id = uow.reports.create(
            name="Test Report",
            spec_json='{"sections": []}',
            snapshot_json='{"data": [1, 2, 3]}',
            snapshot_hash="abc123hash",
        )
        uow.commit()

        report = uow.reports.get_by_id(report_id)
        assert report is not None
        assert report.snapshot_json == '{"data": [1, 2, 3]}'
        assert report.snapshot_hash == "abc123hash"


# ---------------------------------------------------------------------------
# AC-SR15: ReportRepository.create() accepts snapshot fields
# ---------------------------------------------------------------------------


def test_AC_SR15_report_repo_snapshot_fields():
    """ReportRepository.create() accepts and persists snapshot_json + snapshot_hash."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from zorivest_infra.database.models import Base
    from zorivest_infra.database.scheduling_repositories import ReportRepository

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        repo = ReportRepository(session)
        report_id = repo.create(
            name="Snapshot Test",
            spec_json='{}',
            snapshot_json='{"snapshot": true}',
            snapshot_hash="deadbeef",
        )
        session.commit()

        report = repo.get_by_id(report_id)
        assert report.snapshot_json == '{"snapshot": true}'
        assert report.snapshot_hash == "deadbeef"


# ---------------------------------------------------------------------------
# AC-SR16: StoreReportStep.execute() computes snapshot hash from data_queries
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_AC_SR16_store_report_step_execute_snapshot():
    """StoreReportStep.execute() with empty data_queries computes a
    deterministic SHA-256 snapshot hash and returns query_count=0."""
    import hashlib
    import json

    from zorivest_core.domain.pipeline import StepContext
    from zorivest_core.pipeline_steps.store_report_step import StoreReportStep

    mock_repo = MagicMock()
    mock_repo.create.return_value = "rpt-1"

    step = StoreReportStep()
    context = StepContext(
        run_id="run-1",
        policy_id="pol-1",
        outputs={"report_repository": mock_repo},
    )

    # Empty queries — no db_connection needed
    result = await step.execute(
        params={"report_name": "Daily P&L", "data_queries": []},
        context=context,
    )

    assert result.status.value == "success"
    assert result.output["report_name"] == "Daily P&L"
    assert result.output["query_count"] == 0
    # Verify snapshot hash is a valid 64-char hex digest
    assert len(result.output["snapshot_hash"]) == 64
    assert all(c in "0123456789abcdef" for c in result.output["snapshot_hash"])
    # Verify hash is deterministic: empty snapshots
    expected_snapshots = {}
    expected_json = json.dumps(expected_snapshots, sort_keys=True, separators=(",", ":"), default=str)
    expected_hash = hashlib.sha256(expected_json.encode()).hexdigest()
    assert result.output["snapshot_hash"] == expected_hash
    assert result.output["report_id"] == "rpt-1"


# ---------------------------------------------------------------------------
# AC-SR16b: StoreReportStep executes SQL via injected sandboxed connection
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_AC_SR16b_store_report_step_executes_sandboxed_sql():
    """When db_connection is injected, _execute_sandboxed_sql() runs real
    SQL queries and returns actual rows in the snapshot."""
    import sqlite3

    from zorivest_core.domain.pipeline import StepContext
    from zorivest_core.pipeline_steps.store_report_step import StoreReportStep

    # Create in-memory DB with test data
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE positions (symbol TEXT, qty INTEGER)")
    conn.execute("INSERT INTO positions VALUES ('AAPL', 100)")
    conn.execute("INSERT INTO positions VALUES ('MSFT', 50)")
    conn.commit()

    mock_repo = MagicMock()
    mock_repo.create.return_value = "rpt-sql"

    step = StoreReportStep()
    context = StepContext(
        run_id="run-1",
        policy_id="pol-1",
        outputs={"db_connection": conn, "report_repository": mock_repo},
    )

    queries = [{"name": "positions", "sql": "SELECT symbol, qty FROM positions"}]
    result = await step.execute(
        params={"report_name": "Test Report", "data_queries": queries},
        context=context,
    )

    assert result.status.value == "success"
    # Parse snapshot_json to verify actual query results
    import json
    snapshots = json.loads(result.output["snapshot_json"])
    assert "positions" in snapshots
    rows = snapshots["positions"]["rows"]
    assert len(rows) == 2
    assert rows[0]["symbol"] == "AAPL"
    assert rows[0]["qty"] == 100
    assert rows[1]["symbol"] == "MSFT"
    conn.close()


# ---------------------------------------------------------------------------
# AC-SR16c: StoreReportStep._persist_report() calls injected repo
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_AC_SR16c_store_report_persists_via_repository():
    """When report_repository is injected, _persist_report() calls
    repo.create() and returns the report_id. Verifies spec_json is
    the authored report spec, not the snapshot."""
    import json

    from zorivest_core.domain.pipeline import StepContext
    from zorivest_core.pipeline_steps.store_report_step import StoreReportStep

    mock_repo = MagicMock()
    mock_repo.create.return_value = "rpt-42"

    step = StoreReportStep()
    context = StepContext(
        run_id="run-1",
        policy_id="pol-1",
        outputs={"report_repository": mock_repo},
    )

    spec = {"sections": ["summary", "pnl"], "layout": "two-column"}
    result = await step.execute(
        params={"report_name": "Monthly Summary", "spec": spec, "data_queries": []},
        context=context,
    )

    assert result.status.value == "success"
    assert result.output["report_id"] == "rpt-42"
    mock_repo.create.assert_called_once()
    call_kwargs = mock_repo.create.call_args.kwargs
    assert call_kwargs["name"] == "Monthly Summary"
    # spec_json must be the authored spec, not snapshot
    spec_json_received = call_kwargs["spec_json"]
    parsed_spec = json.loads(spec_json_received)
    assert parsed_spec == spec, f"spec_json should be the authored spec, got {parsed_spec}"
    assert "snapshot_json" in call_kwargs
    assert "snapshot_hash" in call_kwargs
    # Verify spec_json != snapshot_json (they track different things)
    assert call_kwargs["spec_json"] != call_kwargs["snapshot_json"] or spec == {}


# ---------------------------------------------------------------------------
# AC-SR17: RenderStep.execute() produces HTML output with report data
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_AC_SR17_render_step_execute_produces_html():
    """RenderStep.execute(output_format='both') returns FAILED status
    when Playwright is unavailable and PDF cannot be produced."""
    from zorivest_core.domain.pipeline import StepContext
    from zorivest_core.pipeline_steps.render_step import RenderStep

    step = RenderStep()
    context = StepContext(
        run_id="run-1",
        policy_id="pol-1",
        outputs={"report_data": {"report_name": "Daily Portfolio"}},
    )

    result = await step.execute(
        params={"template": "portfolio_report", "output_format": "both"},
        context=context,
    )

    # With 'both' format and no Playwright, step reports failure
    assert result.status.value == "failed"
    assert "PDF" in result.error
    html = result.output["html"]
    assert html is not None
    assert "<!DOCTYPE html>" in html
    assert "Daily Portfolio" in html
    assert result.output["pdf_path"] is None
    assert result.output["template"] == "portfolio_report"
    assert result.output["output_format"] == "both"


# ---------------------------------------------------------------------------
# AC-SR17b: RenderStep._render_html() uses injected template engine
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_AC_SR17b_render_step_uses_template_engine():
    """When template_engine is injected via context.outputs,
    _render_html() uses Jinja2 rendering instead of fallback HTML."""
    from jinja2 import Environment, BaseLoader

    from zorivest_core.domain.pipeline import StepContext
    from zorivest_core.pipeline_steps.render_step import RenderStep

    # Create a real Jinja2 environment
    env = Environment(loader=BaseLoader(), autoescape=True)

    step = RenderStep()
    context = StepContext(
        run_id="run-1",
        policy_id="pol-1",
        outputs={
            "report_data": {"report_name": "Jinja Report", "total": 42},
            "template_engine": env,
        },
    )

    result = await step.execute(
        params={"template": "test_template", "output_format": "html"},
        context=context,
    )

    assert result.status.value == "success"
    html = result.output["html"]
    assert html is not None
    assert "Jinja Report" in html
    assert "<!DOCTYPE html>" in html
    # Verify Jinja2 rendered the template (check for data items)
    assert "report_name" in html
    assert result.output["pdf_path"] is None  # html-only


@pytest.mark.asyncio
async def test_AC_SR17c_render_step_html_only_no_pdf():
    """RenderStep.execute(output_format='html') returns HTML but no pdf_path."""
    from zorivest_core.domain.pipeline import StepContext
    from zorivest_core.pipeline_steps.render_step import RenderStep

    step = RenderStep()
    context = StepContext(run_id="run-1", policy_id="pol-1")

    result = await step.execute(
        params={"template": "minimal", "output_format": "html"},
        context=context,
    )

    assert result.status.value == "success"
    assert result.output["html"] is not None
    assert result.output["pdf_path"] is None
    # Value: verify HTML has valid structure
    assert "<!DOCTYPE html>" in result.output["html"] or "<html" in result.output["html"]


# ---------------------------------------------------------------------------
# AC-SR18: StoreReportStep raises ValueError when report_repository is missing
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_AC_SR18_store_report_step_raises_without_repository():
    """StoreReportStep.execute() raises ValueError when report_repository
    is not injected via context.outputs."""
    from zorivest_core.domain.pipeline import StepContext
    from zorivest_core.pipeline_steps.store_report_step import StoreReportStep

    step = StoreReportStep()
    context = StepContext(run_id="run-1", policy_id="pol-1")

    with pytest.raises(ValueError, match="report_repository required"):
        await step.execute(
            params={"report_name": "Test", "data_queries": []},
            context=context,
        )


# ---------------------------------------------------------------------------
# AC-CR1: CriteriaResolver per-field resolution with static passthrough
# ---------------------------------------------------------------------------


def test_AC_CR1_criteria_resolver_per_field_with_static():
    """CriteriaResolver resolves typed fields and passes static fields through."""
    from zorivest_core.services.criteria_resolver import CriteriaResolver

    resolver = CriteriaResolver()
    result = resolver.resolve({
        "start_date": {"type": "relative", "expr": "-30d"},
        "symbol": "AAPL",
        "exchange": "NYSE",
    })

    # Static fields pass through unchanged
    assert result["symbol"] == "AAPL"
    assert result["exchange"] == "NYSE"
    # Typed field is resolved to a dict with start_date and end_date
    assert "start_date" in result["start_date"]
    assert "end_date" in result["start_date"]


# ---------------------------------------------------------------------------
# AC-SR20: _execute_sandboxed_sql raises ValueError without db_connection
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_AC_SR20_execute_sandboxed_sql_raises_without_connection():
    """_execute_sandboxed_sql raises ValueError when data_queries is
    non-empty but db_connection is not injected."""

    from zorivest_core.domain.pipeline import StepContext
    from zorivest_core.pipeline_steps.store_report_step import StoreReportStep

    mock_repo = MagicMock()
    mock_repo.create.return_value = "rpt-1"

    step = StoreReportStep()
    context = StepContext(
        run_id="run-1",
        policy_id="pol-1",
        outputs={"report_repository": mock_repo},
    )

    queries = [{"name": "test", "sql": "SELECT 1"}]
    with pytest.raises(ValueError, match="db_connection required"):
        await step.execute(
            params={"report_name": "Test", "data_queries": queries},
            context=context,
        )
