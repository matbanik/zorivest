# packages/core/src/zorivest_core/pipeline_steps/render_step.py
"""RenderStep — render reports to HTML/Markdown (§9.7, §9H).

Spec: 09-scheduling.md §9.7a–c, 09h-pipeline-markdown-migration.md
MEU: 87, PW14
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from zorivest_core.domain.enums import PipelineStatus
from zorivest_core.domain.pipeline import StepContext, StepResult
from zorivest_core.domain.step_registry import RegisteredStep

# Valid output formats after PDF removal (§9H.4)
_VALID_OUTPUT_FORMATS = {"html", "markdown"}


class RenderStep(RegisteredStep):
    """Render reports to HTML and/or Markdown.

    Auto-registers as ``type_name="render"`` in the step registry.

    Output formats (§9H.4):
    - "html" (default): Jinja2 template rendering for email body
    - "markdown": Markdown table rendering for MCP/file/AI consumption
    """

    type_name = "render"
    side_effects = True

    class Params(BaseModel):
        """RenderStep parameter schema."""

        model_config = {"extra": "forbid"}

        template: str = Field(..., description="Jinja2 template name")
        output_format: str = Field(
            default="html",
            description="Output format: 'html' or 'markdown'",
        )
        chart_settings: dict[str, Any] = Field(
            default_factory=dict,
            description="Chart rendering configuration",
        )

    async def execute(self, params: dict, context: StepContext) -> StepResult:
        """Execute the render step.

        1. Validate params and output_format
        2. Render HTML via _render_html() hook (Jinja2 when available)
        3. Or render Markdown via _render_markdown()
        4. Return output content
        """
        p = self.Params(**params)

        # §9H.4: Reject removed formats
        if p.output_format not in _VALID_OUTPUT_FORMATS:
            raise ValueError(
                f"Invalid output_format '{p.output_format}'. "
                f"Allowed: {sorted(_VALID_OUTPUT_FORMATS)}"
            )

        # Get report data from context (set by StoreReportStep)
        report_data: dict[str, Any] = context.outputs.get("report_data", {})
        report_name = report_data.get("report_name", "unnamed")

        output: dict[str, Any] = {
            "template": p.template,
            "output_format": p.output_format,
        }

        if p.output_format == "html":
            html = self._render_html(
                report_name=report_name,
                report_data=report_data,
                template=p.template,
                context=context,
            )
            output["html"] = html
        elif p.output_format == "markdown":
            markdown = self._render_markdown(report_data, template_name=p.template)
            output["markdown"] = markdown

        return StepResult(
            status=PipelineStatus.SUCCESS,
            output=output,
        )

    def _render_html(
        self,
        *,
        report_name: str,
        report_data: dict[str, Any],
        template: str,
        context: StepContext,
    ) -> str:
        """Render report HTML using Jinja2 template engine.

        Looks for 'template_engine' in context.outputs. If present,
        renders the template with report data. If absent, produces
        a minimal valid HTML document.
        """
        template_engine = context.outputs.get("template_engine")
        if template_engine is not None:
            try:
                tmpl = template_engine.from_string(
                    "<!DOCTYPE html><html><head>"
                    "<title>{{ report_name }}</title></head>"
                    "<body><h1>{{ report_name }}</h1>"
                    "{% for key, val in data.items() %}"
                    "<p>{{ key }}: {{ val }}</p>"
                    "{% endfor %}"
                    "</body></html>"
                )
                return tmpl.render(report_name=report_name, data=report_data)
            except Exception:
                pass  # Fall through to default

        return (
            f"<!DOCTYPE html><html><head><title>{report_name}</title></head>"
            f"<body><h1>{report_name}</h1>"
            f"<p>Template: {template}</p>"
            f"</body></html>"
        )

    def _render_markdown(self, data: dict, template_name: str | None) -> str:
        """Convert report data to structured Markdown tables (§9H.3).

        Auto-detects columns from the first record's keys and formats
        them as a Markdown table.
        """
        lines: list[str] = []
        lines.append(f"# {data.get('report_name', 'Report')}")
        lines.append(f"*Generated: {data.get('date', 'N/A')}*\n")

        records = data.get("records", data.get("quotes", []))
        if not records:
            lines.append("*No data available.*")
            return "\n".join(lines)

        # Auto-detect columns from first record
        if isinstance(records[0], dict):
            headers = list(records[0].keys())
            lines.append("| " + " | ".join(headers) + " |")
            lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
            for row in records:
                values = [str(row.get(h, "")) for h in headers]
                lines.append("| " + " | ".join(values) + " |")

        return "\n".join(lines)
