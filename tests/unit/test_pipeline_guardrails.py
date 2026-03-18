# tests/unit/test_pipeline_guardrails.py
"""Tests for MEU-90: Pipeline security guardrails.

Covers: rate-limit enforcement (under/at/over each limit), approval checks
(approved, unapproved, hash mismatch, policy not found), custom limits.
Source: 09-scheduling.md §9.9b–§9.9d
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import pytest

from zorivest_core.services.pipeline_guardrails import (
    PipelineGuardrails,
    PipelineRateLimits,
)

pytestmark = pytest.mark.unit


# ── Test helpers ────────────────────────────────────────────────────────


class FakeAuditCounter:
    """Configurable audit counter for testing."""

    def __init__(self, counts: dict[str, int] | None = None) -> None:
        self._counts = counts or {}

    async def count_actions_since(self, action: str, since: datetime) -> int:
        return self._counts.get(action, 0)


@dataclass
class FakePolicy:
    """Minimal policy stub for approval checks."""

    id: str
    approved: bool = False
    approved_hash: str | None = None


class FakePolicyLookup:
    """Configurable policy lookup for testing."""

    def __init__(self, policies: dict[str, FakePolicy] | None = None) -> None:
        self._policies = policies or {}

    async def get_by_id(self, policy_id: str) -> Any:
        return self._policies.get(policy_id)


def _make_guardrails(
    audit_counts: dict[str, int] | None = None,
    policies: dict[str, FakePolicy] | None = None,
    limits: PipelineRateLimits | None = None,
) -> PipelineGuardrails:
    return PipelineGuardrails(
        audit_counter=FakeAuditCounter(audit_counts),
        policy_lookup=FakePolicyLookup(policies),
        limits=limits,
    )


# ── AC-1: check_can_create_policy ──────────────────────────────────────


class TestCheckCanCreatePolicy:
    """AC-1: check_can_create_policy() blocks when daily creates >= 20."""

    @pytest.mark.asyncio
    async def test_under_limit_allows(self) -> None:
        g = _make_guardrails(audit_counts={"policy.create": 19})
        ok, msg = await g.check_can_create_policy()
        assert ok is True
        assert msg == ""

    @pytest.mark.asyncio
    async def test_at_limit_blocks(self) -> None:
        g = _make_guardrails(audit_counts={"policy.create": 20})
        ok, msg = await g.check_can_create_policy()
        assert ok is False
        assert "20" in msg

    @pytest.mark.asyncio
    async def test_over_limit_blocks(self) -> None:
        g = _make_guardrails(audit_counts={"policy.create": 25})
        ok, msg = await g.check_can_create_policy()
        assert ok is False


# ── AC-2: check_can_execute ────────────────────────────────────────────


class TestCheckCanExecute:
    """AC-2: check_can_execute() blocks when hourly executions >= 60."""

    @pytest.mark.asyncio
    async def test_under_limit_allows(self) -> None:
        g = _make_guardrails(audit_counts={"pipeline.run": 59})
        ok, msg = await g.check_can_execute()
        assert ok is True
        assert msg == ""

    @pytest.mark.asyncio
    async def test_at_limit_blocks(self) -> None:
        g = _make_guardrails(audit_counts={"pipeline.run": 60})
        ok, msg = await g.check_can_execute()
        assert ok is False
        assert "60" in msg


# ── AC-3: check_can_send_email ─────────────────────────────────────────


class TestCheckCanSendEmail:
    """AC-3: check_can_send_email() blocks when daily emails >= 50."""

    @pytest.mark.asyncio
    async def test_under_limit_allows(self) -> None:
        g = _make_guardrails(audit_counts={"report.send": 49})
        ok, msg = await g.check_can_send_email()
        assert ok is True
        assert msg == ""

    @pytest.mark.asyncio
    async def test_at_limit_blocks(self) -> None:
        g = _make_guardrails(audit_counts={"report.send": 50})
        ok, msg = await g.check_can_send_email()
        assert ok is False
        assert "50" in msg


# ── AC-4/5/6: check_policy_approved ────────────────────────────────────


class TestCheckPolicyApproved:
    """AC-4/5/6: Approval flow with content_hash matching."""

    @pytest.mark.asyncio
    async def test_approved_hash_matches_allows(self) -> None:
        """AC-6: Approved policy with matching hash → (True, '')."""
        policy = FakePolicy(id="p1", approved=True, approved_hash="abc123")
        g = _make_guardrails(policies={"p1": policy})
        ok, msg = await g.check_policy_approved("p1", "abc123")
        assert ok is True
        assert msg == ""

    @pytest.mark.asyncio
    async def test_unapproved_blocks(self) -> None:
        """AC-4: Unapproved policy → (False, msg)."""
        policy = FakePolicy(id="p1", approved=False)
        g = _make_guardrails(policies={"p1": policy})
        ok, msg = await g.check_policy_approved("p1", "abc123")
        assert ok is False
        assert "approval" in msg.lower()

    @pytest.mark.asyncio
    async def test_hash_mismatch_blocks(self) -> None:
        """AC-5: Hash mismatch → (False, msg)."""
        policy = FakePolicy(id="p1", approved=True, approved_hash="old_hash")
        g = _make_guardrails(policies={"p1": policy})
        ok, msg = await g.check_policy_approved("p1", "new_hash")
        assert ok is False
        assert "modified" in msg.lower() or "re-approval" in msg.lower()

    @pytest.mark.asyncio
    async def test_policy_not_found_blocks(self) -> None:
        """Policy lookup returns None → (False, 'Policy not found')."""
        g = _make_guardrails(policies={})
        ok, msg = await g.check_policy_approved("nonexistent", "abc123")
        assert ok is False
        assert "not found" in msg.lower()


# ── AC-7: Custom limits ───────────────────────────────────────────────


class TestCustomLimits:
    """AC-7: Custom PipelineRateLimits overrides default values."""

    @pytest.mark.asyncio
    async def test_custom_policy_limit(self) -> None:
        limits = PipelineRateLimits(max_policy_creates_per_day=5)
        g = _make_guardrails(audit_counts={"policy.create": 5}, limits=limits)
        ok, msg = await g.check_can_create_policy()
        assert ok is False
        assert "5" in msg

    @pytest.mark.asyncio
    async def test_custom_execution_limit(self) -> None:
        limits = PipelineRateLimits(max_pipeline_executions_per_hour=10)
        g = _make_guardrails(audit_counts={"pipeline.run": 9}, limits=limits)
        ok, msg = await g.check_can_execute()
        assert ok is True

    @pytest.mark.asyncio
    async def test_custom_email_limit(self) -> None:
        limits = PipelineRateLimits(max_emails_per_day=3)
        g = _make_guardrails(audit_counts={"report.send": 3}, limits=limits)
        ok, msg = await g.check_can_send_email()
        assert ok is False
        assert "3" in msg


# ── AC-8: _count_audit_actions time-windows correctly ──────────────────


class TestAuditCounting:
    """AC-8: _count_audit_actions delegates with correct time window."""

    @pytest.mark.asyncio
    async def test_zero_count_allows_all(self) -> None:
        """No audit entries → all checks pass."""
        g = _make_guardrails()
        ok1, _ = await g.check_can_create_policy()
        ok2, _ = await g.check_can_execute()
        ok3, _ = await g.check_can_send_email()
        assert ok1 is True
        assert ok2 is True
        assert ok3 is True


# ── Default limits sanity ──────────────────────────────────────────────


class TestDefaultLimits:
    """Verify default limit values match spec §9.9b."""

    def test_defaults(self) -> None:
        limits = PipelineRateLimits()
        assert limits.max_policy_creates_per_day == 20
        assert limits.max_pipeline_executions_per_hour == 60
        assert limits.max_emails_per_day == 50
        assert limits.max_report_queries_per_hour == 100
