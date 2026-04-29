# tests/unit/test_pipeline_markdown_migration.py
"""TDD Red-phase tests for Pipeline Markdown Migration (MEU-PW14).

Feature Intent Contract:
  Spec: 09h-pipeline-markdown-migration.md
  MEU: PW14
  Resolves: [PIPE-DROPPDF]

Acceptance Criteria:
  AC-PW14-1: _render_pdf() removed from RenderStep [Spec §9H.2]
  AC-PW14-2: _render_markdown() added to RenderStep [Spec §9H.3]
  AC-PW14-3: output_format enum: "html" (default), "markdown" only;
             "pdf"/"both" raise ValueError [Spec §9H.4]
  AC-PW14-4: pdf_renderer.py deleted [Spec §9H.2]
  AC-PW14-5: SendStep.Params.pdf_path field removed [Spec §9H.2]
  AC-PW14-6: _save_local() replaced with _save_local_markdown()
             — writes .md file from HTML body [Spec §9H.2]
  AC-PW14-7: email_sender.send_report_email() — pdf_path parameter
             removed, no MIME PDF attachment [Spec §9H.2]
  AC-PW14-8: ReportModel.format default → "html" [Spec §9H.2]
  AC-PW14-9: ReportRepository.create() format default → "html" [Spec §9H.2]
  AC-PW14-10: Playwright removed from pyproject.toml [Spec §9H.2]
"""

from __future__ import annotations

import inspect
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# AC-PW14-1: _render_pdf() removed from RenderStep
# ---------------------------------------------------------------------------


def test_AC_PW14_1_render_pdf_method_removed():
    """RenderStep must NOT have a _render_pdf method after migration."""
    from zorivest_core.pipeline_steps.render_step import RenderStep

    assert not hasattr(RenderStep, "_render_pdf"), (
        "_render_pdf() should be removed from RenderStep"
    )


# ---------------------------------------------------------------------------
# AC-PW14-2: _render_markdown() produces Markdown table from data
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_AC_PW14_2a_render_markdown_produces_table():
    """_render_markdown() converts data dict with records to Markdown table."""
    from zorivest_core.pipeline_steps.render_step import RenderStep

    step = RenderStep()
    data = {
        "report_name": "Daily P&L",
        "date": "2026-04-28",
        "records": [
            {"symbol": "AAPL", "pnl": 150.0},
            {"symbol": "MSFT", "pnl": -30.0},
        ],
    }

    result = step._render_markdown(data, template_name=None)

    # Must contain report title
    assert "# Daily P&L" in result
    # Must contain generated date
    assert "2026-04-28" in result
    # Must contain table headers
    assert "| symbol | pnl |" in result
    # Must contain separator row
    assert "| --- | --- |" in result
    # Must contain data rows
    assert "| AAPL | 150.0 |" in result
    assert "| MSFT | -30.0 |" in result


@pytest.mark.asyncio
async def test_AC_PW14_2b_render_markdown_empty_data():
    """_render_markdown() returns '*No data available.*' when records are empty."""
    from zorivest_core.pipeline_steps.render_step import RenderStep

    step = RenderStep()
    data = {
        "report_name": "Empty Report",
        "date": "2026-04-28",
        "records": [],
    }

    result = step._render_markdown(data, template_name=None)

    assert "*No data available.*" in result
    assert "# Empty Report" in result


@pytest.mark.asyncio
async def test_AC_PW14_2c_render_markdown_uses_quotes_fallback():
    """_render_markdown() falls back to 'quotes' key when 'records' is absent."""
    from zorivest_core.pipeline_steps.render_step import RenderStep

    step = RenderStep()
    data = {
        "report_name": "Quotes Report",
        "quotes": [
            {"ticker": "SPY", "price": 450.00},
        ],
    }

    result = step._render_markdown(data, template_name=None)

    assert "| ticker | price |" in result
    assert "| SPY | 450.0 |" in result


# ---------------------------------------------------------------------------
# AC-PW14-3: output_format enum: "html" (default), "markdown" only
# ---------------------------------------------------------------------------


def test_AC_PW14_3a_render_step_default_format_is_html():
    """RenderStep.Params defaults output_format to 'html'."""
    from zorivest_core.pipeline_steps.render_step import RenderStep

    p = RenderStep.Params(template="default")
    assert p.output_format == "html"


@pytest.mark.asyncio
async def test_AC_PW14_3b_pdf_format_rejected():
    """output_format='pdf' raises ValueError during execute."""
    from zorivest_core.domain.pipeline import StepContext
    from zorivest_core.pipeline_steps.render_step import RenderStep

    step = RenderStep()
    context = StepContext(run_id="run-1", policy_id="pol-1")

    with pytest.raises(ValueError, match="[Ii]nvalid output_format.*pdf"):
        await step.execute(
            params={"template": "test", "output_format": "pdf"},
            context=context,
        )


@pytest.mark.asyncio
async def test_AC_PW14_3c_both_format_rejected():
    """output_format='both' raises ValueError during execute."""
    from zorivest_core.domain.pipeline import StepContext
    from zorivest_core.pipeline_steps.render_step import RenderStep

    step = RenderStep()
    context = StepContext(run_id="run-1", policy_id="pol-1")

    with pytest.raises(ValueError, match="[Ii]nvalid output_format.*both"):
        await step.execute(
            params={"template": "test", "output_format": "both"},
            context=context,
        )


@pytest.mark.asyncio
async def test_AC_PW14_3d_html_format_still_works():
    """RenderStep with output_format='html' produces HTML output successfully."""
    from zorivest_core.domain.pipeline import StepContext
    from zorivest_core.pipeline_steps.render_step import RenderStep

    step = RenderStep()
    context = StepContext(
        run_id="run-1",
        policy_id="pol-1",
        outputs={"report_data": {"report_name": "Test Report"}},
    )

    result = await step.execute(
        params={"template": "test", "output_format": "html"},
        context=context,
    )

    assert result.status.value == "success"
    assert result.output["html"] is not None
    assert "<!DOCTYPE html>" in result.output["html"]
    assert result.output["output_format"] == "html"


@pytest.mark.asyncio
async def test_AC_PW14_3e_markdown_format_works():
    """RenderStep with output_format='markdown' produces Markdown output."""
    from zorivest_core.domain.pipeline import StepContext
    from zorivest_core.pipeline_steps.render_step import RenderStep

    step = RenderStep()
    context = StepContext(
        run_id="run-1",
        policy_id="pol-1",
        outputs={
            "report_data": {
                "report_name": "Markdown Report",
                "date": "2026-04-28",
                "records": [{"symbol": "AAPL", "qty": 100}],
            }
        },
    )

    result = await step.execute(
        params={"template": "test", "output_format": "markdown"},
        context=context,
    )

    assert result.status.value == "success"
    assert result.output["markdown"] is not None
    assert "# Markdown Report" in result.output["markdown"]
    assert result.output["output_format"] == "markdown"


# ---------------------------------------------------------------------------
# AC-PW14-4: pdf_renderer.py deleted
# ---------------------------------------------------------------------------


def test_AC_PW14_4_pdf_renderer_deleted():
    """pdf_renderer.py must not exist after migration."""
    repo_root = Path(__file__).resolve().parents[2]
    pdf_path = (
        repo_root
        / "packages"
        / "infrastructure"
        / "src"
        / "zorivest_infra"
        / "rendering"
        / "pdf_renderer.py"
    )
    assert not pdf_path.exists(), f"pdf_renderer.py should be deleted: {pdf_path}"


# ---------------------------------------------------------------------------
# AC-PW14-5: SendStep.Params.pdf_path field removed
# ---------------------------------------------------------------------------


def test_AC_PW14_5_send_step_no_pdf_path_param():
    """SendStep.Params must NOT have a pdf_path field."""
    from zorivest_core.pipeline_steps.send_step import SendStep

    fields = SendStep.Params.model_fields
    assert "pdf_path" not in fields, "pdf_path should be removed from SendStep.Params"


# ---------------------------------------------------------------------------
# AC-PW14-6: _save_local_markdown() writes .md file
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_AC_PW14_6_save_local_writes_md_file(tmp_path):
    """SendStep local_file channel writes a .md file from html_body content."""
    from zorivest_core.domain.pipeline import StepContext
    from zorivest_core.pipeline_steps.send_step import SendStep

    step = SendStep()
    dest = tmp_path / "report.md"

    # Build an approved context to pass confirmation gate
    mock_snapshot = MagicMock()
    mock_snapshot.approved = True
    mock_snapshot.approved_hash = "test-hash"

    context = StepContext(
        run_id="run-1",
        policy_id="pol-1",
        policy_hash="test-hash",
        approval_snapshot=mock_snapshot,
        outputs={},
    )

    result = await step.execute(
        params={
            "channel": "local_file",
            "recipients": [str(dest)],
            "subject": "Report",
            "html_body": "<h1>Test Report</h1><p>Content here</p>",
        },
        context=context,
    )

    assert result.status.value == "success"
    assert result.output["sent"] == 1
    assert dest.exists()
    content = dest.read_text(encoding="utf-8")
    # File should contain some form of the content
    assert len(content) > 0


# ---------------------------------------------------------------------------
# AC-PW14-7: email_sender has no pdf_path parameter
# ---------------------------------------------------------------------------


def test_AC_PW14_7a_email_sender_no_pdf_path_param():
    """send_report_email() must NOT accept pdf_path parameter."""
    from zorivest_infra.email.email_sender import send_report_email

    sig = inspect.signature(send_report_email)
    assert "pdf_path" not in sig.parameters, (
        "pdf_path should be removed from send_report_email()"
    )


def test_AC_PW14_7b_email_sender_no_mime_application_import():
    """email_sender module should not import MIMEApplication (PDF attachment)."""
    import zorivest_infra.email.email_sender as mod

    source = inspect.getsource(mod)
    assert "MIMEApplication" not in source, (
        "MIMEApplication import should be removed from email_sender"
    )


# ---------------------------------------------------------------------------
# AC-PW14-8: ReportModel.format default → "html"
# ---------------------------------------------------------------------------


def test_AC_PW14_8_report_model_format_default_html():
    """ReportModel.format column default must be 'html' (not 'pdf')."""
    from zorivest_infra.database.models import ReportModel

    col = ReportModel.__table__.columns["format"]
    default_val = col.default.arg if col.default else None
    assert default_val == "html", (
        f"ReportModel.format default should be 'html', got '{default_val}'"
    )


# ---------------------------------------------------------------------------
# AC-PW14-9: ReportRepository.create() format default → "html"
# ---------------------------------------------------------------------------


def test_AC_PW14_9_report_repo_create_default_html():
    """ReportRepository.create() format parameter default must be 'html'."""
    from zorivest_infra.database.scheduling_repositories import ReportRepository

    sig = inspect.signature(ReportRepository.create)
    format_param = sig.parameters["format"]
    assert format_param.default == "html", (
        f"ReportRepository.create() format default should be 'html', "
        f"got '{format_param.default}'"
    )


# ---------------------------------------------------------------------------
# AC-PW14-10: Playwright removed from pyproject.toml rendering extras
# ---------------------------------------------------------------------------


def test_AC_PW14_10_playwright_removed_from_pyproject():
    """Playwright must not appear in infrastructure pyproject.toml."""
    repo_root = Path(__file__).resolve().parents[2]
    pyproject_path = repo_root / "packages" / "infrastructure" / "pyproject.toml"
    content = pyproject_path.read_text(encoding="utf-8")
    assert "playwright" not in content.lower(), (
        "Playwright should be removed from pyproject.toml"
    )


# ---------------------------------------------------------------------------
# F2: optional .md attachment support (Spec §9H.2, §9H.6)
#
# §9H.2 line 39: "Add optional .md attachment support"
# §9H.6 line 108: "Email attachments: optional .md, no PDF"
# ---------------------------------------------------------------------------


def test_F2a_send_step_has_optional_attachment_path():
    """SendStep.Params must have an optional attachment_path field (Spec §9H.2).

    Defaults to None so existing policies without attachments are unaffected.
    """
    from zorivest_core.pipeline_steps.send_step import SendStep

    fields = SendStep.Params.model_fields
    assert "attachment_path" in fields, (
        "SendStep.Params must have attachment_path per §9H.2"
    )
    # Must be optional with None default
    p = SendStep.Params(channel="email", recipients=["test@example.com"])
    assert p.attachment_path is None


def test_F2b_email_sender_accepts_attachment_path():
    """send_report_email() must accept an optional attachment_path param (Spec §9H.2)."""
    from zorivest_infra.email.email_sender import send_report_email

    sig = inspect.signature(send_report_email)
    assert "attachment_path" in sig.parameters, (
        "send_report_email() must accept attachment_path per §9H.2"
    )
    # Must have a default of None (optional)
    assert sig.parameters["attachment_path"].default is None


@pytest.mark.asyncio
async def test_F2c_email_attachment_md_file_attached(tmp_path):
    """When a .md file is provided, email includes it as a MIME attachment (Spec §9H.6).

    Uses monkeypatch to capture the MIME message without actually sending.
    """
    from email.mime.multipart import MIMEMultipart

    from zorivest_infra.email.email_sender import send_report_email

    md_file = tmp_path / "report.md"
    md_file.write_text("# Test Report\n\nData here.", encoding="utf-8")

    # Capture the MIME message by mocking aiosmtplib.send
    captured_msg = {}

    async def mock_send(msg, **kwargs):
        captured_msg["msg"] = msg

    with patch(
        "zorivest_infra.email.email_sender.aiosmtplib.send", side_effect=mock_send
    ):
        success, message = await send_report_email(
            smtp_host="localhost",
            smtp_port=587,
            sender="test@zorivest.local",
            recipient="user@example.com",
            subject="Test Report",
            html_body="<h1>Test</h1>",
            attachment_path=str(md_file),
        )

    assert success is True
    msg = captured_msg["msg"]
    assert isinstance(msg, MIMEMultipart)
    # Must have at least 2 parts: HTML body + attachment
    payloads = msg.get_payload()
    assert isinstance(payloads, list), f"Expected list payload, got {type(payloads)}"
    assert len(payloads) >= 2, f"Expected ≥2 MIME parts, got {len(payloads)}"
    # Last part should be the attachment
    attachment_part = payloads[-1]
    from email.message import Message as _Msg

    assert isinstance(attachment_part, _Msg), (
        f"Expected Message, got {type(attachment_part)}"
    )
    assert "report.md" in (attachment_part.get_filename() or "")


@pytest.mark.asyncio
async def test_F2d_email_attachment_pdf_rejected(tmp_path):
    """When a .pdf file path is provided, send_report_email() raises ValueError (Spec §9H.6).

    §9H.6 exit criteria: "Email attachments: optional .md, no PDF"
    """
    from zorivest_infra.email.email_sender import send_report_email

    pdf_file = tmp_path / "report.pdf"
    pdf_file.write_bytes(b"%PDF-1.4 fake content")

    with pytest.raises(ValueError, match=r"\.md"):
        await send_report_email(
            smtp_host="localhost",
            smtp_port=587,
            sender="test@zorivest.local",
            recipient="user@example.com",
            subject="Test Report",
            html_body="<h1>Test</h1>",
            attachment_path=str(pdf_file),
        )


@pytest.mark.asyncio
async def test_F2e_email_attachment_none_no_attachment():
    """When attachment_path is None, email is HTML-only — no attachment parts (Spec §9H.2 'optional').

    This ensures backward compatibility: existing policies without attachment_path
    continue to produce simple HTML emails.
    """

    from zorivest_infra.email.email_sender import send_report_email

    captured_msg = {}

    async def mock_send(msg, **kwargs):
        captured_msg["msg"] = msg

    with patch(
        "zorivest_infra.email.email_sender.aiosmtplib.send", side_effect=mock_send
    ):
        success, message = await send_report_email(
            smtp_host="localhost",
            smtp_port=587,
            sender="test@zorivest.local",
            recipient="user@example.com",
            subject="Test Report",
            html_body="<h1>Test</h1>",
            attachment_path=None,
        )

    assert success is True
    msg = captured_msg["msg"]
    # Only 1 part: HTML body, no attachment
    payloads = msg.get_payload()
    assert len(payloads) == 1, f"Expected 1 MIME part (HTML only), got {len(payloads)}"
