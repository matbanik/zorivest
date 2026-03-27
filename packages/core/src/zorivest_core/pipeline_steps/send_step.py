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


class SendStep(RegisteredStep):
    """Deliver rendered reports via email or local file copy.

    Auto-registers as ``type_name="send"`` in the step registry.
    """

    type_name = "send"
    side_effects = True

    class Params(BaseModel):
        """SendStep parameter schema — validated before execute()."""

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

    async def execute(self, params: dict, context: StepContext) -> StepResult:
        """Execute the send step.

        1. Validate params via Pydantic model
        2. Dispatch to _send_emails() or _save_local() based on channel
        3. Return deliveries list with sent/failed counts
        """
        p = self.Params(**params)

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
        return StepResult(
            status=status,
            output={
                "channel": p.channel,
                "sent": delivery_result["sent"],
                "failed": delivery_result["failed"],
                "deliveries": delivery_result.get("deliveries", []),
            },
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

        for recipient in params.recipients:
            # Compute dedup key
            dedup_key = compute_dedup_key(
                report_id=params.report_id or "",
                channel="email",
                recipient=recipient,
                snapshot_hash=params.snapshot_hash or "",
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

            # Send email
            html_body = (
                params.html_body or params.body_template or "<p>Report attached</p>"
            )
            success, msg = await send_report_email(
                smtp_host=smtp_host,
                smtp_port=smtp_port,
                sender=sender,
                recipient=recipient,
                subject=params.subject,
                html_body=html_body,
                pdf_path=params.pdf_path,
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
