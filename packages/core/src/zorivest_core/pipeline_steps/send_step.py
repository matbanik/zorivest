# packages/core/src/zorivest_core/pipeline_steps/send_step.py
"""SendStep — delivers rendered reports via email or local file (§9.8).

Spec: 09-scheduling.md §9.8a–c
MEU: 88
"""

from __future__ import annotations

import shutil
from typing import Any, Optional

from pydantic import BaseModel, Field

from zorivest_core.domain.enums import PipelineStatus
from zorivest_core.domain.pipeline import StepContext, StepResult
from zorivest_core.domain.step_registry import RegisteredStep


class PolicyExecutionError(Exception):
    """Raised when a pipeline step violates a security policy gate."""


class SendStep(RegisteredStep):
    """Deliver rendered reports via email or local file copy.

    Auto-registers as ``type_name="send"`` in the step registry.
    """

    type_name = "send"
    side_effects = True

    class Params(BaseModel):
        """SendStep parameter schema — validated before execute()."""

        model_config = {"extra": "forbid"}

        channel: str = Field(
            ..., description="Delivery channel: 'email' or 'local_file'"
        )
        recipients: list[str] = Field(
            ..., max_length=5, description="List of recipients (max 5)"
        )
        subject: str = Field(default="", description="Email subject line")
        body_template: str = Field(default="", description="HTML body template name")
        # Ref-resolved fields from prior pipeline steps (Local Canon §9.3a)
        report_id: Optional[str] = Field(
            default=None, description="Report ID from store_report step"
        )
        snapshot_hash: Optional[str] = Field(
            default=None, description="Snapshot hash from store_report step"
        )
        pdf_path: Optional[str] = Field(
            default=None, description="PDF path from render step"
        )
        html_body: Optional[str] = Field(
            default=None, description="HTML body from render step"
        )
        requires_confirmation: bool = Field(
            default=False,
            description="Whether this send requires UI confirmation (§9C.3b)",
        )

    async def execute(self, params: dict, context: StepContext) -> StepResult:
        """Execute the send step.

        1. Validate params via Pydantic model
        2. Dispatch to _send_emails() or _save_local() based on channel
        3. Return deliveries list with sent/failed counts
        """
        p = self.Params(**params)

        # §9C.3b: Confirmation gate
        self._check_confirmation_gate(p, context)

        if p.channel == "email":
            delivery_result = await self._send_emails(p, context)
        elif p.channel == "local_file":
            delivery_result = await self._save_local(p, context)
        else:
            return StepResult(
                status=PipelineStatus.FAILED,
                error=f"Unknown channel: {p.channel}",
            )

        status = (
            PipelineStatus.SUCCESS
            if delivery_result["failed"] == 0
            else PipelineStatus.FAILED
        )
        # Surface first delivery error in StepResult.error for UI visibility
        error_msg: str | None = None
        if status == PipelineStatus.FAILED:
            for d in delivery_result.get("deliveries", []):
                if d.get("error"):
                    error_msg = d["error"]
                    break
            if error_msg is None:
                error_msg = f"Send failed: {delivery_result['failed']} delivery(ies)"
        return StepResult(
            status=status,
            error=error_msg,
            output={
                "channel": p.channel,
                "sent": delivery_result["sent"],
                "failed": delivery_result["failed"],
                "deliveries": delivery_result.get("deliveries", []),
            },
        )

    def _check_confirmation_gate(self, params: Params, context: StepContext) -> None:
        """§9C.3b-c: Confirmation gate for SendStep.

        Two modes:
        1. requires_confirmation=True → user must have confirmed (UI button)
        2. requires_confirmation=False + approval_snapshot present →
           content_hash must match approved_hash (no drift)
        3. requires_confirmation=False + no snapshot → rejected per §9C.3c
           (approval record required to honor opt-out)
        """
        if params.requires_confirmation:
            # §9C.3b: Explicit confirmation required
            if not context.has_user_confirmation:
                raise PolicyExecutionError(
                    "SendStep requires user confirmation but "
                    "has_user_confirmation is False"
                )
        else:
            # §9C.3c: Opt-out mode — requires stored approval record
            snapshot = context.approval_snapshot
            if snapshot is None:
                # No approval record → reject opt-out to prevent malicious bypass
                raise PolicyExecutionError(
                    "requires_confirmation=False requires a stored policy approval "
                    "record. Use POST /api/v1/scheduling/policies/{id}/approve first."
                )
            if not snapshot.approved:
                raise PolicyExecutionError(
                    "SendStep requires an approved policy but "
                    "approval_snapshot.approved is False"
                )
            # Drift detection — content must match approved version
            if snapshot.approved_hash != context.policy_hash:
                raise PolicyExecutionError(
                    f"Policy content hash drift detected: "
                    f"approved_hash={snapshot.approved_hash!r} != "
                    f"current_hash={context.policy_hash!r}"
                )

    async def _send_emails(
        self, params: Params, context: StepContext
    ) -> dict[str, Any]:
        """Send emails to all recipients with dedup checking."""
        try:
            from zorivest_infra.email.delivery_tracker import compute_dedup_key
            from zorivest_infra.email.email_sender import send_report_email
        except ImportError:
            return {
                "sent": 0,
                "failed": len(params.recipients),
                "deliveries": [{"error": "zorivest_infra.email not available"}],
            }

        delivery_repo = context.outputs.get("delivery_repository")
        sent = 0
        failed = 0
        deliveries: list[dict[str, Any]] = []

        # SMTP config from context (or defaults for testing)
        smtp_config = context.outputs.get("smtp_config", {})
        smtp_host = smtp_config.get("host", "localhost")
        smtp_port = smtp_config.get("port", 587)
        sender = smtp_config.get("sender", "noreply@zorivest.local")
        smtp_username = smtp_config.get("username") or None
        smtp_password = smtp_config.get("password") or None
        security = smtp_config.get("security", "STARTTLS")

        for recipient in params.recipients:
            # Compute dedup key — use run_id as fallback when no snapshot_hash
            # so each pipeline execution can deliver independently
            effective_hash = params.snapshot_hash or context.run_id or ""
            dedup_key = compute_dedup_key(
                report_id=params.report_id or "",
                channel="email",
                recipient=recipient,
                snapshot_hash=effective_hash,
            )

            # Check for existing delivery
            if delivery_repo is not None:
                existing = delivery_repo.get_by_dedup_key(dedup_key)
                if existing is not None:
                    deliveries.append(
                        {
                            "recipient": recipient,
                            "status": "skipped",
                            "reason": "duplicate",
                        }
                    )
                    continue

            # Resolve email body: html_body > rendered template > raw > fallback
            html_body = self._resolve_body(params, context)
            success, msg = await send_report_email(
                smtp_host=smtp_host,
                smtp_port=smtp_port,
                sender=sender,
                recipient=recipient,
                subject=params.subject,
                html_body=html_body,
                pdf_path=params.pdf_path,
                use_tls=security != "SSL",
                smtp_username=smtp_username,
                smtp_password=smtp_password,
            )

            if success:
                sent += 1
                # Record delivery
                if delivery_repo is not None:
                    delivery_repo.create(
                        report_id=params.report_id or "",
                        channel="email",
                        recipient=recipient,
                        status="sent",
                        dedup_key=dedup_key,
                    )
                deliveries.append({"recipient": recipient, "status": "sent"})
            else:
                failed += 1
                deliveries.append(
                    {
                        "recipient": recipient,
                        "status": "failed",
                        "error": msg,
                    }
                )

        return {"sent": sent, "failed": failed, "deliveries": deliveries}

    def _resolve_body(self, params: Params, context: StepContext) -> str:
        """Resolve email body with five-tier priority chain (§9E.5a).

        Priority order:
        1. params.html_body   — explicit override from prior step (e.g. render)
        2. DB lookup via template_port — user-managed templates from database
        3. EMAIL_TEMPLATES lookup + Jinja2 render — hardcoded registry templates
        4. Raw body_template string — graceful fallback for unknown names
        5. Default "<p>Report attached</p>" — when nothing is provided

        Template context variables provided to Jinja2:
        - generated_at: ISO timestamp of rendering time
        - policy_id: from StepContext
        - run_id: from StepContext
        - All keys from context.outputs (pipeline step results)
        """
        from datetime import datetime, timezone as tz

        # Tier 1: explicit html_body from a prior render step
        if params.html_body:
            return params.html_body

        # Tier 5 early exit: nothing provided
        if not params.body_template:
            return "<p>Report attached</p>"

        # Build render context (shared by Tier 2 and 3)
        render_ctx: dict[str, Any] = {
            "generated_at": datetime.now(tz.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "policy_id": context.policy_id,
            "run_id": context.run_id,
        }
        for key, value in context.outputs.items():
            if key not in render_ctx:
                render_ctx[key] = value
            if isinstance(value, dict):
                for inner_key, inner_value in value.items():
                    if inner_key not in render_ctx:
                        render_ctx[inner_key] = inner_value

        # Tier 2: DB lookup via template_port (§9E.5a)
        template_port = context.outputs.get("template_port")
        if template_port is not None:
            dto = template_port.get_by_name(params.body_template)
            if dto is not None:
                # Render via HardenedSandbox for security
                from zorivest_core.services.secure_jinja import HardenedSandbox

                sandbox = HardenedSandbox()
                rendered = sandbox.render_safe(dto.body_html, render_ctx)
                # §9E.4a: Honor body_format — render markdown through
                # safe_render_markdown() for sanitized HTML output
                if dto.body_format == "markdown":
                    from zorivest_core.services.safe_markdown import (
                        safe_render_markdown,
                    )

                    return safe_render_markdown(rendered)
                return rendered

        # Tier 3: look up body_template in EMAIL_TEMPLATES registry
        template_source: str | None = None
        try:
            from zorivest_infra.rendering.email_templates import EMAIL_TEMPLATES

            template_source = EMAIL_TEMPLATES.get(params.body_template)
        except ImportError:
            pass  # infra not available — fall through to tier 4

        if template_source is None:
            # Tier 4: unknown template name → raw string fallback
            return params.body_template

        # Render the template via Jinja2 engine
        engine = context.outputs.get("template_engine")
        if engine is None:
            # Create default Environment with financial filters (AC-6)
            try:
                from zorivest_infra.rendering.template_engine import (
                    create_template_engine,
                )

                engine = create_template_engine()
            except ImportError:
                from jinja2 import BaseLoader, Environment

                engine = Environment(loader=BaseLoader(), autoescape=True)

        tmpl = engine.from_string(template_source)

        return tmpl.render(**render_ctx)

    async def _save_local(self, params: Params, context: StepContext) -> dict[str, Any]:
        """Copy rendered output to local file paths."""
        sent = 0
        failed = 0
        deliveries: list[dict[str, Any]] = []

        source_path = params.pdf_path
        if source_path is None:
            return {
                "sent": 0,
                "failed": len(params.recipients),
                "deliveries": [{"error": "No pdf_path provided"}],
            }

        for dest_path in params.recipients:
            try:
                shutil.copy2(source_path, dest_path)
                sent += 1
                deliveries.append({"recipient": dest_path, "status": "sent"})
            except Exception as exc:
                failed += 1
                deliveries.append(
                    {
                        "recipient": dest_path,
                        "status": "failed",
                        "error": str(exc),
                    }
                )

        return {"sent": sent, "failed": failed, "deliveries": deliveries}
