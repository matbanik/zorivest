# tests/unit/test_confirmation_gates.py
"""PH3: Confirmation & Content Guards — Tests for AC-3.1 through AC-3.9.

Feature Intent Contract (FIC)
==============================

AC-3.1 [Spec §9C.3b]: SendStep raises PolicyExecutionError when
       requires_confirmation=True and context.has_user_confirmation is False.
AC-3.2 [Spec §9C.3b]: SendStep proceeds normally when
       context.has_user_confirmation=True.
AC-3.3 [Spec §9C.3c]: SendStep proceeds when requires_confirmation=False
       and a valid approval snapshot is present (content_hash == approved_hash).
AC-3.4 [Spec §9C.3c]: SendStep raises PolicyExecutionError when
       requires_confirmation=False and no approval snapshot is present.
       Per §9C.3c: "requires_confirmation=False is only honored when the
       policy has a stored approval record."
AC-3.5 [Spec §9C.3c]: SendStep raises PolicyExecutionError when
       requires_confirmation=False and content_hash != approved_hash (drift).
AC-3.6 [Spec §9C.4c L415]: FetchStep raises SecurityError when response
       content-type does not match expected MIME allowlist.
AC-3.7 [Spec §9C.4b L393]: FetchStep raises SecurityError when response
       body exceeds 5 MB.
AC-3.8 [Spec §9C.4c L417, L404]: FetchStep raises ValidationError when
       step requests > 5 URLs.
AC-3.9 [Spec §9C.4d L424, Human-approved]: PipelineRunner._execute_step()
       enforces cumulative 10-URL/policy cap before FetchStep execution.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest

from zorivest_core.domain.approval_snapshot import ApprovalSnapshot
from zorivest_core.domain.pipeline import StepContext, StepResult
from zorivest_core.pipeline_steps.send_step import PolicyExecutionError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_context(
    *,
    has_user_confirmation: bool = False,
    approval_snapshot: ApprovalSnapshot | None = None,
    policy_hash: str = "abc123",
    fetch_url_count: int = 0,
    extra_outputs: dict[str, Any] | None = None,
) -> StepContext:
    """Build a StepContext with PH3-required fields."""
    outputs: dict[str, Any] = {}
    if extra_outputs:
        outputs.update(extra_outputs)
    return StepContext(
        run_id="test-run-001",
        policy_id="test-policy-001",
        outputs=outputs,
        has_user_confirmation=has_user_confirmation,
        approval_snapshot=approval_snapshot,
        policy_hash=policy_hash,
        fetch_url_count=fetch_url_count,
    )


# ===========================================================================
# AC-3.1 through AC-3.5: SendStep confirmation gate
# ===========================================================================


class TestSendStepConfirmationGate:
    """Tests for SendStep confirmation gate (AC-3.1 through AC-3.5)."""

    @pytest.mark.asyncio
    async def test_ac_3_1_send_step_raises_without_confirmation(self) -> None:
        """AC-3.1: requires_confirmation=True + no user confirmation → error."""
        from zorivest_core.pipeline_steps.send_step import SendStep

        step = SendStep()
        ctx = _make_context(has_user_confirmation=False)

        params = {
            "channel": "email",
            "recipients": ["test@example.com"],
            "subject": "Test",
            "requires_confirmation": True,
        }

        with pytest.raises(PolicyExecutionError, match="[Cc]onfirmation"):
            await step.execute(params, ctx)

    @pytest.mark.asyncio
    async def test_ac_3_2_send_step_proceeds_with_confirmation(self) -> None:
        """AC-3.2: has_user_confirmation=True → step proceeds."""
        from zorivest_core.pipeline_steps.send_step import SendStep

        step = SendStep()
        ctx = _make_context(has_user_confirmation=True)

        params = {
            "channel": "local_file",
            "recipients": ["/tmp/report.pdf"],
            "requires_confirmation": True,
            "pdf_path": "/tmp/source.pdf",
        }

        # Should NOT raise — the confirmation gate should pass
        result = await step.execute(params, ctx)
        assert isinstance(result, StepResult)

    @pytest.mark.asyncio
    async def test_ac_3_3_send_step_no_confirm_with_valid_approval(self) -> None:
        """AC-3.3: requires_confirmation=False + valid approval → proceeds."""
        from zorivest_core.pipeline_steps.send_step import SendStep

        step = SendStep()
        snapshot = ApprovalSnapshot(
            approved=True,
            approved_hash="abc123",
            approved_at=None,
        )
        ctx = _make_context(
            has_user_confirmation=False,
            approval_snapshot=snapshot,
            policy_hash="abc123",
        )

        params = {
            "channel": "local_file",
            "recipients": ["/tmp/report.pdf"],
            "requires_confirmation": False,
            "pdf_path": "/tmp/source.pdf",
        }

        result = await step.execute(params, ctx)
        assert isinstance(result, StepResult)

    @pytest.mark.asyncio
    async def test_ac_3_4_send_step_rejects_opt_out_without_approval(self) -> None:
        """AC-3.4: requires_confirmation=False + no approval → rejection.

        Per §9C.3c: "requires_confirmation=False is only honored when the
        policy has a stored approval record." Without an approval snapshot,
        the gate must reject to prevent malicious opt-out bypass.
        """
        from zorivest_core.pipeline_steps.send_step import SendStep

        step = SendStep()
        ctx = _make_context(
            has_user_confirmation=False,
            approval_snapshot=None,
            policy_hash="abc123",
        )

        params = {
            "channel": "local_file",
            "recipients": ["/tmp/report.pdf"],
            "requires_confirmation": False,
            "pdf_path": "/tmp/source.pdf",
        }

        # Must raise — no approval record means opt-out is not honored
        with pytest.raises(
            PolicyExecutionError, match="[Aa]pproval|[Rr]ecord|[Aa]pprove"
        ):
            await step.execute(params, ctx)

    @pytest.mark.asyncio
    async def test_ac_3_5_send_step_rejects_opt_out_with_hash_mismatch(self) -> None:
        """AC-3.5: requires_confirmation=False + hash drift → error."""
        from zorivest_core.pipeline_steps.send_step import SendStep

        step = SendStep()
        snapshot = ApprovalSnapshot(
            approved=True,
            approved_hash="old_hash_from_approval",
            approved_at=None,
        )
        ctx = _make_context(
            has_user_confirmation=False,
            approval_snapshot=snapshot,
            policy_hash="new_hash_after_edit",
        )

        params = {
            "channel": "email",
            "recipients": ["test@example.com"],
            "subject": "Test",
            "requires_confirmation": False,
        }

        with pytest.raises(PolicyExecutionError, match="[Hh]ash|[Dd]rift|[Mm]atch"):
            await step.execute(params, ctx)


# ===========================================================================
# AC-3.6 through AC-3.8: FetchStep content guards
# ===========================================================================


class TestFetchStepContentGuards:
    """Tests for FetchStep content guards (AC-3.6 through AC-3.8)."""

    def _make_mock_adapter(
        self,
        content: bytes = b'{"data": "test"}',
        content_type: str = "application/json",
    ) -> AsyncMock:
        """Create a mock provider adapter with configurable response."""
        adapter = AsyncMock()
        adapter.fetch.return_value = {
            "content": content,
            "content_type": content_type,
            "cache_status": "miss",
        }
        return adapter

    @pytest.mark.asyncio
    async def test_ac_3_6_fetch_step_rejects_mime_mismatch(self) -> None:
        """AC-3.6: Response content-type mismatch → SecurityError."""
        from zorivest_core.pipeline_steps.fetch_step import FetchStep
        from zorivest_core.services.sql_sandbox import SecurityError

        step = FetchStep()
        adapter = self._make_mock_adapter(
            content=b"<script>alert('xss')</script>",
            content_type="text/html",
        )
        ctx = _make_context(
            extra_outputs={
                "provider_adapter": adapter,
            }
        )

        params = {
            "provider": "test_provider",
            "data_type": "ohlcv",
            "criteria": {"ticker": "AAPL"},
            "allowed_mime_types": ["application/json"],
        }

        with pytest.raises(SecurityError, match="[Mm]IME|[Cc]ontent.type"):
            await step.execute(params, ctx)

    @pytest.mark.asyncio
    async def test_ac_3_7_fetch_step_rejects_oversized_body(self) -> None:
        """AC-3.7: Response body > 5 MB → SecurityError."""
        from zorivest_core.pipeline_steps.fetch_step import FetchStep
        from zorivest_core.services.sql_sandbox import SecurityError

        step = FetchStep()
        # 5 MB + 1 byte
        oversized_content = b"x" * (5 * 1024 * 1024 + 1)
        adapter = self._make_mock_adapter(
            content=oversized_content,
            content_type="application/json",
        )
        ctx = _make_context(
            extra_outputs={
                "provider_adapter": adapter,
            }
        )

        params = {
            "provider": "test_provider",
            "data_type": "ohlcv",
            "criteria": {"ticker": "AAPL"},
        }

        with pytest.raises(SecurityError, match="[Ss]ize|5.?MB|exceed"):
            await step.execute(params, ctx)

    @pytest.mark.asyncio
    async def test_ac_3_8_fetch_step_rejects_excess_urls(self) -> None:
        """AC-3.8: > 5 URLs per step → validation error."""
        from zorivest_core.pipeline_steps.fetch_step import FetchStep

        step = FetchStep()
        ctx = _make_context()

        params = {
            "provider": "test_provider",
            "data_type": "ohlcv",
            "criteria": {"ticker": "AAPL"},
            "urls": [
                "https://example.com/1",
                "https://example.com/2",
                "https://example.com/3",
                "https://example.com/4",
                "https://example.com/5",
                "https://example.com/6",  # 6th URL — should be rejected
            ],
        }

        with pytest.raises(
            (ValueError, Exception), match="[Uu]RL|5|[Ee]xceed|[Ll]imit"
        ):
            await step.execute(params, ctx)


# ===========================================================================
# AC-3.9: PipelineRunner._execute_step() enforces 10-URL/policy cap
# ===========================================================================


class TestPipelineUrlCap:
    """Test for policy-level URL cap (AC-3.9) at the runner execution path."""

    @pytest.mark.asyncio
    async def test_ac_3_9_execute_step_enforces_url_cap(self) -> None:
        """AC-3.9: _execute_step() with a fetch step that exceeds
        the cumulative 10-URL/policy cap must raise before execution."""
        from unittest.mock import MagicMock

        from zorivest_core.domain.pipeline import PolicyStep
        from zorivest_core.services.pipeline_runner import PipelineRunner
        from zorivest_core.services.sql_sandbox import SecurityError

        runner = PipelineRunner(
            uow=None,
            ref_resolver=MagicMock(),
            condition_evaluator=MagicMock(),
        )
        # ref_resolver.resolve returns params as-is
        runner.ref_resolver.resolve.side_effect = lambda p, c: p
        # condition_evaluator returns False for skip_if
        runner.condition_evaluator.evaluate.return_value = False

        # Context already at cap
        ctx = _make_context(fetch_url_count=10)

        # Build a fetch step definition
        step_def = PolicyStep(
            id="fetch_1",
            type="fetch",
            params={
                "provider": "test",
                "data_type": "quote",
                "criteria": {"ticker": "AAPL"},
                "urls": ["https://example.com/1"],
            },
        )

        # The runner must reject before executing the step
        with pytest.raises(SecurityError, match="[Uu]RL|[Cc]ap|[Ee]xceed|[Ll]imit"):
            await runner._execute_step(step_def, ctx, "test-run-001")

    def test_ac_3_9_private_helper_still_works(self) -> None:
        """Regression: _check_fetch_url_cap helper raises correctly."""
        from zorivest_core.services.pipeline_runner import PipelineRunner
        from zorivest_core.services.sql_sandbox import SecurityError

        runner = PipelineRunner(
            uow=None,
            ref_resolver=None,
            condition_evaluator=None,
        )

        ctx = _make_context(fetch_url_count=10)

        with pytest.raises(SecurityError, match="[Uu]RL|[Cc]ap|[Ee]xceed|[Ll]imit"):
            runner._check_fetch_url_cap(ctx, url_count=1)
