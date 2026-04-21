# packages/core/src/zorivest_core/pipeline_steps/render_step.py
"""RenderStep — render reports to HTML/PDF (§9.7).

Spec: 09-scheduling.md §9.7a–c
MEU: 87
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from zorivest_core.domain.enums import PipelineStatus
from zorivest_core.domain.pipeline import StepContext, StepResult
from zorivest_core.domain.step_registry import RegisteredStep


class RenderStep(RegisteredStep):
    """Render reports to HTML and/or PDF.

    Auto-registers as ``type_name="render"`` in the step registry.
    """

    type_name = "render"
    side_effects = True

    class Params(BaseModel):
        """RenderStep parameter schema."""

        model_config = {"extra": "forbid"}

        template: str = Field(..., description="Jinja2 template name")
        output_format: str = Field(
            default="both",
            description="Output format: 'html', 'pdf', or 'both'",
        )
        chart_settings: dict[str, Any] = Field(
            default_factory=dict,
            description="Chart rendering configuration",
        )

    async def execute(self, params: dict, context: StepContext) -> StepResult:
        """Execute the render step.

        1. Get report data from prior step context
        2. Render HTML via _render_html() hook (Jinja2 when available)
        3. Render PDF via _render_pdf() hook (Playwright when available)
        4. Return output paths/content
        """
        p = self.Params(**params)

        # 1. Get report data from context (set by StoreReportStep)
        report_data: dict[str, Any] = context.outputs.get("report_data", {})
        report_name = report_data.get("report_name", "unnamed")

        # 2. Render HTML via hook
        html: str | None = None
        if p.output_format in ("html", "both"):
            html = self._render_html(
                report_name=report_name,
                report_data=report_data,
                template=p.template,
                context=context,
            )

        # 3. Render PDF via hook
        pdf_path: str | None = None
        if p.output_format in ("pdf", "both") and html:
            pdf_path = self._render_pdf(
                html_content=html,
                report_name=report_name,
                context=context,
            )

        output: dict[str, Any] = {
            "html": html,
            "pdf_path": pdf_path,
            "template": p.template,
            "output_format": p.output_format,
        }

        # If PDF was requested but rendering failed, report failure
        if p.output_format in ("pdf", "both") and pdf_path is None:
            return StepResult(
                status=PipelineStatus.FAILED,
                output=output,
                error="PDF rendering failed: Playwright unavailable",
            )

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

    def _render_pdf(
        self,
        *,
        html_content: str,
        report_name: str,
        context: StepContext,
    ) -> str | None:
        """Render PDF from HTML content using Playwright.

        Attempts to import render_pdf from infrastructure. If available,
        generates a real PDF file. If not available, returns None.
        """
        try:
            from zorivest_infra.rendering.pdf_renderer import render_pdf

            output_path = f"reports/{report_name}.pdf"
            return render_pdf(html_content=html_content, output_path=output_path)
        except (ImportError, Exception):
            # ImportError: infrastructure not available
            # Other: Playwright sync API inside asyncio loop
            return None
