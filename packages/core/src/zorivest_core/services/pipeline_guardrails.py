# packages/core/src/zorivest_core/services/pipeline_guardrails.py
"""Security guardrails for the Scheduling & Pipeline Engine (Phase 9, §9.9).

Enforces rate limits, approval requirements, and audit-based counting
for pipeline operations.

Spec: 09-scheduling.md §9.9b–§9.9d
MEU: MEU-90 (scheduling-guardrails)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Protocol


# ---------------------------------------------------------------------------
# §9.9b: Configurable Rate Limits
# ---------------------------------------------------------------------------


@dataclass
class PipelineRateLimits:
    """Configurable rate limits for pipeline operations.

    Stored in settings table, checked before execution.
    """

    max_policy_creates_per_day: int = 20
    max_pipeline_executions_per_hour: int = 60
    max_emails_per_day: int = 50
    max_report_queries_per_hour: int = 100


# ---------------------------------------------------------------------------
# Ports for guardrail dependencies
# ---------------------------------------------------------------------------


class AuditCounter(Protocol):
    """Count audit log entries within a time window."""

    async def count_actions_since(self, action: str, since: datetime) -> int: ...


class PolicyLookup(Protocol):
    """Minimal policy lookup for approval checks."""

    async def get_by_id(self, policy_id: str) -> Any: ...


# ---------------------------------------------------------------------------
# §9.9b–c: Pipeline Guardrails
# ---------------------------------------------------------------------------


class PipelineGuardrails:
    """Enforce rate limits and security policies.

    Checks audit_log counts via AuditCounter protocol and policy
    approval status via PolicyLookup protocol.
    """

    def __init__(
        self,
        audit_counter: AuditCounter,
        policy_lookup: PolicyLookup,
        limits: PipelineRateLimits | None = None,
    ) -> None:
        self._audit = audit_counter
        self._policies = policy_lookup
        self.limits = limits or PipelineRateLimits()

    async def check_can_create_policy(self) -> tuple[bool, str]:
        """Check if a new policy can be created within rate limits."""
        count = await self._count_audit_actions("policy.create", hours=24)
        if count >= self.limits.max_policy_creates_per_day:
            return False, (
                f"Daily policy creation limit reached "
                f"({self.limits.max_policy_creates_per_day})"
            )
        return True, ""

    async def check_can_execute(self) -> tuple[bool, str]:
        """Check if a pipeline can be executed within rate limits."""
        count = await self._count_audit_actions("pipeline.run", hours=1)
        if count >= self.limits.max_pipeline_executions_per_hour:
            return False, (
                f"Hourly execution limit reached "
                f"({self.limits.max_pipeline_executions_per_hour})"
            )
        return True, ""

    async def check_can_send_email(self) -> tuple[bool, str]:
        """Check if an email can be sent within rate limits."""
        count = await self._count_audit_actions("report.send", hours=24)
        if count >= self.limits.max_emails_per_day:
            return False, (
                f"Daily email limit reached "
                f"({self.limits.max_emails_per_day})"
            )
        return True, ""

    async def check_policy_approved(
        self, policy_id: str, content_hash: str
    ) -> tuple[bool, str]:
        """Check if a policy is approved for execution.

        The content_hash at execution time must match the approved_hash.
        If the policy has been modified since approval, block execution.
        """
        policy = await self._policies.get_by_id(policy_id)
        if not policy:
            return False, "Policy not found"
        # Support both dict (Phase 4 stubs) and ORM objects (PolicyModel)
        approved = (
            policy.get("approved", False)
            if isinstance(policy, dict)
            else getattr(policy, "approved", False)
        )
        if not approved:
            return False, "Policy requires approval before execution"
        approved_hash = (
            policy.get("approved_hash")
            if isinstance(policy, dict)
            else getattr(policy, "approved_hash", None)
        )
        if approved_hash != content_hash:
            return False, (
                "Policy modified since approval \u2014 re-approval required"
            )
        return True, ""

    async def _count_audit_actions(self, action: str, hours: int) -> int:
        """Count audit log entries for an action within a time window."""
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        return await self._audit.count_actions_since(action, since)
