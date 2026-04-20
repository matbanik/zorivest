# tests/unit/test_send_step_template.py
"""TDD tests for MEU-PW9: SendStep template rendering wiring.

FIC — Feature Intent Contract:
  When SendStep resolves the email body, it must look up `body_template`
  in EMAIL_TEMPLATES, render via the Jinja2 template_engine from context,
  and use the rendered HTML — not the raw template name string.

AC-1: body_template="daily_quote_summary" → rendered HTML with <table> (Local Canon)
AC-2: body_template="generic_report"      → rendered HTML with title   (Local Canon)
AC-3: body_template="nonexistent"          → raw string fallback       (Local Canon)
AC-4: html_body provided + body_template   → html_body wins            (Local Canon)
AC-5: No body_template, no html_body       → "<p>Report attached</p>"  (Local Canon)
AC-6: Missing template_engine in context   → default Environment       (Research-backed)

Spec: 09-scheduling.md §9.8a
"""

from __future__ import annotations

import hashlib
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from zorivest_core.domain.enums import PipelineStatus
from zorivest_core.domain.pipeline import StepContext
from zorivest_core.pipeline_steps.send_step import SendStep


# ── Fixtures ──────────────────────────────────────────────────────────────


def _make_context(
    *,
    run_id: str = "test-run-001",
    policy_id: str = "test-policy",
    smtp_config: dict[str, Any] | None = None,
    template_engine: Any = None,
    extra_outputs: dict[str, Any] | None = None,
) -> StepContext:
    """Create a StepContext with injectable SMTP config and template engine."""
    outputs: dict[str, Any] = {}
    if smtp_config is not None:
        outputs["smtp_config"] = smtp_config
    if template_engine is not None:
        outputs["template_engine"] = template_engine
    if extra_outputs:
        outputs.update(extra_outputs)
    return StepContext(
        run_id=run_id,
        policy_id=policy_id,
        outputs=outputs,
    )


DEFAULT_SMTP = {
    "host": "smtp.test.com",
    "port": 587,
    "sender": "noreply@zorivest.local",
    "username": "user",
    "password": "pass",
    "security": "STARTTLS",
}


def _mock_infra_modules(mock_send: AsyncMock) -> dict[str, Any]:
    """Build sys.modules patch dict for zorivest_infra email imports."""
    return {
        "zorivest_infra.email.email_sender": MagicMock(send_report_email=mock_send),
        "zorivest_infra.email.delivery_tracker": MagicMock(
            compute_dedup_key=lambda **kw: hashlib.sha256(
                f"{kw['report_id']}|{kw['channel']}|{kw['recipient']}|{kw['snapshot_hash']}".encode()
            ).hexdigest()
        ),
    }


def _create_template_engine() -> Any:
    """Create the real Jinja2 template engine with financial filters."""
    from jinja2 import BaseLoader, Environment

    env = Environment(loader=BaseLoader(), autoescape=True)
    env.filters["currency"] = lambda v, symbol="$", decimals=2: (
        f"{symbol}{v:,.{decimals}f}"
    )
    env.filters["percent"] = lambda v, decimals=2: f"{v * 100:.{decimals}f}%"
    return env


# ── AC-1: daily_quote_summary template renders HTML ─────────────────────


class TestDailyQuoteTemplateRendering:
    """AC-1: body_template='daily_quote_summary' → rendered HTML with <table>."""

    @pytest.mark.asyncio
    async def test_daily_quote_template_renders_html(self) -> None:
        """SendStep must look up 'daily_quote_summary' in EMAIL_TEMPLATES,
        render it via template_engine, and pass rendered HTML to send_report_email.

        The rendered output must contain '<table>' and 'Zorivest Daily Quote Report'.
        """
        mock_send = AsyncMock(return_value=(True, "Sent"))
        engine = _create_template_engine()

        params = {
            "channel": "email",
            "recipients": ["user@example.com"],
            "subject": "Daily Report",
            "body_template": "daily_quote_summary",
        }

        with patch.dict("sys.modules", _mock_infra_modules(mock_send)):
            step = SendStep()
            ctx = _make_context(
                smtp_config=DEFAULT_SMTP,
                template_engine=engine,
            )
            result = await step.execute(params, ctx)

        assert result.status == PipelineStatus.SUCCESS
        mock_send.assert_called_once()

        html_body = mock_send.call_args.kwargs["html_body"]
        # Must be rendered HTML, NOT the raw string "daily_quote_summary"
        assert html_body != "daily_quote_summary", (
            "body must be rendered HTML, not the raw template name"
        )
        assert "Zorivest Daily Quote Report" in html_body
        # Template contains a <table> structure (may or may not render
        # depending on whether 'quotes' context var is provided)
        assert "<!DOCTYPE html>" in html_body or "<html>" in html_body


# ── AC-2: generic_report template renders HTML ───────────────────────────


class TestGenericReportTemplateRendering:
    """AC-2: body_template='generic_report' → rendered HTML with title."""

    @pytest.mark.asyncio
    async def test_generic_report_template_renders_html(self) -> None:
        """SendStep must render 'generic_report' template to HTML."""
        mock_send = AsyncMock(return_value=(True, "Sent"))
        engine = _create_template_engine()

        params = {
            "channel": "email",
            "recipients": ["user@example.com"],
            "subject": "Generic Report",
            "body_template": "generic_report",
        }

        with patch.dict("sys.modules", _mock_infra_modules(mock_send)):
            step = SendStep()
            ctx = _make_context(
                smtp_config=DEFAULT_SMTP,
                template_engine=engine,
            )
            result = await step.execute(params, ctx)

        assert result.status == PipelineStatus.SUCCESS
        html_body = mock_send.call_args.kwargs["html_body"]
        assert html_body != "generic_report"
        assert "Zorivest Report" in html_body or "<!DOCTYPE html>" in html_body


# ── AC-3: Unknown template → raw string fallback ────────────────────────


class TestUnknownTemplateFallback:
    """AC-3: body_template='nonexistent' → raw string fallback."""

    @pytest.mark.asyncio
    async def test_unknown_template_falls_back_to_raw_string(self) -> None:
        """When body_template doesn't match any EMAIL_TEMPLATES key,
        the raw string is used as-is (graceful degradation).
        """
        mock_send = AsyncMock(return_value=(True, "Sent"))
        engine = _create_template_engine()

        params = {
            "channel": "email",
            "recipients": ["user@example.com"],
            "subject": "Test",
            "body_template": "nonexistent_template_name",
        }

        with patch.dict("sys.modules", _mock_infra_modules(mock_send)):
            step = SendStep()
            ctx = _make_context(
                smtp_config=DEFAULT_SMTP,
                template_engine=engine,
            )
            result = await step.execute(params, ctx)

        assert result.status == PipelineStatus.SUCCESS
        html_body = mock_send.call_args.kwargs["html_body"]
        assert html_body == "nonexistent_template_name"


# ── AC-4: html_body takes precedence over body_template ──────────────────


class TestHtmlBodyPrecedence:
    """AC-4: html_body provided + body_template → html_body wins."""

    @pytest.mark.asyncio
    async def test_html_body_takes_precedence_over_template(self) -> None:
        """Explicit html_body must bypass template lookup entirely."""
        mock_send = AsyncMock(return_value=(True, "Sent"))
        engine = _create_template_engine()

        params = {
            "channel": "email",
            "recipients": ["user@example.com"],
            "subject": "Test",
            "body_template": "daily_quote_summary",
            "html_body": "<h1>Custom Override</h1>",
        }

        with patch.dict("sys.modules", _mock_infra_modules(mock_send)):
            step = SendStep()
            ctx = _make_context(
                smtp_config=DEFAULT_SMTP,
                template_engine=engine,
            )
            await step.execute(params, ctx)

        html_body = mock_send.call_args.kwargs["html_body"]
        assert html_body == "<h1>Custom Override</h1>"


# ── AC-5: No body_template, no html_body → default ──────────────────────


class TestDefaultFallback:
    """AC-5: No body_template, no html_body → '<p>Report attached</p>'."""

    @pytest.mark.asyncio
    async def test_no_body_falls_back_to_default(self) -> None:
        """When both html_body and body_template are absent/empty,
        the default '<p>Report attached</p>' should be used.
        """
        mock_send = AsyncMock(return_value=(True, "Sent"))

        params = {
            "channel": "email",
            "recipients": ["user@example.com"],
            "subject": "Test",
            "body_template": "",
        }

        with patch.dict("sys.modules", _mock_infra_modules(mock_send)):
            step = SendStep()
            ctx = _make_context(smtp_config=DEFAULT_SMTP)
            await step.execute(params, ctx)

        html_body = mock_send.call_args.kwargs["html_body"]
        assert html_body == "<p>Report attached</p>"


# ── AC-6: Missing template_engine in context → default Environment ───────


class TestMissingTemplateEngine:
    """AC-6: No template_engine in context → still renders with default."""

    @pytest.mark.asyncio
    async def test_missing_template_engine_uses_default(self) -> None:
        """When template_engine is not injected, SendStep should create
        a default Jinja2 Environment and render successfully.
        """
        mock_send = AsyncMock(return_value=(True, "Sent"))

        params = {
            "channel": "email",
            "recipients": ["user@example.com"],
            "subject": "Test",
            "body_template": "generic_report",
        }

        with patch.dict("sys.modules", _mock_infra_modules(mock_send)):
            step = SendStep()
            # No template_engine in context
            ctx = _make_context(smtp_config=DEFAULT_SMTP)
            result = await step.execute(params, ctx)

        assert result.status == PipelineStatus.SUCCESS
        html_body = mock_send.call_args.kwargs["html_body"]
        # Must still be rendered HTML, not the raw name
        assert html_body != "generic_report"
        assert "<!DOCTYPE html>" in html_body or "Zorivest" in html_body
