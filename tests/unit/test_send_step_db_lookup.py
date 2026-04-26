# tests/unit/test_send_step_db_lookup.py
"""FIC: SendStep DB Lookup Tier (MEU-PH6) — Spec §9E.5a–b.

Acceptance Criteria:
  AC-6.18: SendStep._resolve_body() checks DB before hardcoded registry   [Spec §9E.5a]
  AC-6.19: SendStep._resolve_body() falls through to registry on DB miss  [Spec §9E.5b]
  AC-6.20: SendStep._resolve_body() renders inline via HardenedSandbox    [Spec §9E.5b]
  AC-6.23: SendStep resolves template from context.outputs["template_port"]  [Spec §9E.5a]
  AC-6.24: SendStep falls through when template_port is None               [Local Canon]
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


import pytest

from zorivest_core.domain.pipeline import StepContext


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FakeTemplateDTO:
    """Mimics EmailTemplateDTO without importing from ports (test isolation)."""

    name: str
    description: str | None
    subject_template: str | None
    body_html: str
    body_format: str
    required_variables: list[str]
    sample_data_json: str | None
    is_default: bool


class FakeTemplatePort:
    """Fake implementation of EmailTemplatePort for unit testing."""

    def __init__(self, templates: dict[str, FakeTemplateDTO]) -> None:
        self._templates = templates

    def get_by_name(self, name: str) -> FakeTemplateDTO | None:
        return self._templates.get(name)

    def list_all(self) -> list[FakeTemplateDTO]:
        return list(self._templates.values())


def _make_context(outputs: dict[str, Any] | None = None) -> StepContext:
    """Build a StepContext with optional pre-populated outputs."""
    ctx = StepContext(
        run_id="test-run",
        policy_id="test-policy",
        outputs=outputs or {},
    )
    return ctx


# ---------------------------------------------------------------------------
# AC-6.18 / AC-6.23: DB lookup via template_port
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_resolve_body_db_lookup() -> None:
    """AC-6.18/AC-6.23: template found in DB renders correctly via template_port."""
    from zorivest_core.pipeline_steps.send_step import SendStep

    dto = FakeTemplateDTO(
        name="weekly-report",
        description=None,
        subject_template=None,
        body_html="<p>Weekly report for {{ policy_id }}</p>",
        body_format="html",
        required_variables=["policy_id"],
        sample_data_json=None,
        is_default=False,
    )
    port = FakeTemplatePort({"weekly-report": dto})

    ctx = _make_context({"template_port": port})

    step = SendStep()
    params = step.Params(
        channel="email",
        recipients=["test@example.com"],
        body_template="weekly-report",
    )
    result = step._resolve_body(params, ctx)

    assert "Weekly report for test-policy" in result


# ---------------------------------------------------------------------------
# AC-6.19 / AC-6.24: DB miss falls through
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_resolve_body_db_miss_falls_through() -> None:
    """AC-6.19: Missing DB template falls through to hardcoded registry."""
    from zorivest_core.pipeline_steps.send_step import SendStep

    port = FakeTemplatePort({})  # Empty — no templates in DB
    ctx = _make_context({"template_port": port})

    step = SendStep()
    params = step.Params(
        channel="email",
        recipients=["test@example.com"],
        body_template="nonexistent-template",
    )
    # Should fall through to tier 3 (raw string) since template not in DB or registry
    result = step._resolve_body(params, ctx)
    # With DB miss and registry miss, should return raw body_template string (Tier 3)
    assert result == "nonexistent-template"


# ---------------------------------------------------------------------------
# AC-6.20: Inline template via HardenedSandbox
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_resolve_body_inline_template() -> None:
    """AC-6.20: Inline Jinja2 renders via HardenedSandbox when DB template found."""
    from zorivest_core.pipeline_steps.send_step import SendStep

    dto = FakeTemplateDTO(
        name="inline-test",
        description=None,
        subject_template=None,
        body_html="{{ run_id | upper }}",
        body_format="html",
        required_variables=[],
        sample_data_json=None,
        is_default=False,
    )
    port = FakeTemplatePort({"inline-test": dto})
    ctx = _make_context({"template_port": port})

    step = SendStep()
    params = step.Params(
        channel="email",
        recipients=["test@example.com"],
        body_template="inline-test",
    )
    result = step._resolve_body(params, ctx)
    assert "TEST-RUN" in result


# ---------------------------------------------------------------------------
# AC-6.24: template_port is None → falls through gracefully
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_resolve_body_no_port() -> None:
    """AC-6.24: When template_port is None, DB tier skipped silently."""
    from zorivest_core.pipeline_steps.send_step import SendStep

    # No template_port in context
    ctx = _make_context({})

    step = SendStep()
    params = step.Params(
        channel="email",
        recipients=["test@example.com"],
        body_template="some-template",
    )
    # Should fall through to Tier 2/3 without error
    result = step._resolve_body(params, ctx)
    # Without DB port and without EMAIL_TEMPLATES match, should return raw string
    assert isinstance(result, str)


# ---------------------------------------------------------------------------
# AC-6.25: No core→infra import
# ---------------------------------------------------------------------------


def test_no_core_infra_import() -> None:
    """AC-6.25: send_step.py does not import zorivest_infra at module level."""
    import ast
    import pathlib

    send_step_path = pathlib.Path(
        "packages/core/src/zorivest_core/pipeline_steps/send_step.py"
    )
    source = send_step_path.read_text()
    tree = ast.parse(source)

    # Check top-level imports (not inside functions)
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith("zorivest_infra"), (
                    f"Module-level import of {alias.name} violates dependency rule"
                )
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith("zorivest_infra"):
                pytest.fail(
                    f"Module-level 'from {node.module} import ...' "
                    f"violates core→infra dependency rule"
                )


# ---------------------------------------------------------------------------
# AC-6.26: DB template with body_format="markdown" renders through
#           safe_render_markdown (Codex finding #3)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_db_template_markdown_format_rendered() -> None:
    """AC-6.26: body_format='markdown' passes through safe_render_markdown().

    Regression: Codex finding #3 — DB template with body_format='markdown'
    returned raw markdown instead of sanitized HTML.
    """
    from zorivest_core.pipeline_steps.send_step import SendStep

    dto = FakeTemplateDTO(
        name="md-report",
        description=None,
        subject_template=None,
        body_html="**bold text**",
        body_format="markdown",
        required_variables=[],
        sample_data_json=None,
        is_default=False,
    )
    port = FakeTemplatePort({"md-report": dto})
    ctx = _make_context({"template_port": port})

    step = SendStep()
    params = step.Params(
        channel="email",
        recipients=["test@example.com"],
        body_template="md-report",
    )
    result = step._resolve_body(params, ctx)

    # Should contain HTML-rendered bold, not raw markdown
    assert "<strong>" in result or "<b>" in result
    assert "**bold text**" not in result


@pytest.mark.asyncio
async def test_db_template_html_format_unchanged() -> None:
    """AC-6.27: body_format='html' returns Jinja-rendered HTML directly."""
    from zorivest_core.pipeline_steps.send_step import SendStep

    dto = FakeTemplateDTO(
        name="html-report",
        description=None,
        subject_template=None,
        body_html="<p>Hello {{ policy_id }}</p>",
        body_format="html",
        required_variables=["policy_id"],
        sample_data_json=None,
        is_default=False,
    )
    port = FakeTemplatePort({"html-report": dto})
    ctx = _make_context({"template_port": port})

    step = SendStep()
    params = step.Params(
        channel="email",
        recipients=["test@example.com"],
        body_template="html-report",
    )
    result = step._resolve_body(params, ctx)

    # HTML format returns Jinja-rendered output directly
    assert "<p>Hello test-policy</p>" in result
