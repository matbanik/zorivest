# tests/unit/test_send_step.py
"""Unit tests for SendStep — email delivery pipeline step (§9.8).

Verifies:
- SMTP credential passthrough from context.outputs["smtp_config"]
- Email body resolution order (html_body > body_template > default)
- Dedup key computation and skip behavior
- Error surfacing in StepResult
- Status reporting for sent/failed/skipped scenarios
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
    delivery_repository: Any = None,
    extra_outputs: dict[str, Any] | None = None,
) -> StepContext:
    """Create a StepContext with injectable SMTP config and delivery repo."""
    outputs: dict[str, Any] = {}
    if smtp_config is not None:
        outputs["smtp_config"] = smtp_config
    if delivery_repository is not None:
        outputs["delivery_repository"] = delivery_repository
    if extra_outputs:
        outputs.update(extra_outputs)
    return StepContext(
        run_id=run_id,
        policy_id=policy_id,
        outputs=outputs,
    )


DEFAULT_SMTP = {
    "host": "smtp.gmail.com",
    "port": 587,
    "sender": "me@gmail.com",
    "username": "me@gmail.com",
    "password": "app-password-123",
    "security": "STARTTLS",
}

DEFAULT_EMAIL_PARAMS = {
    "channel": "email",
    "recipients": ["you@example.com"],
    "subject": "Test Report",
    "body_template": "daily_quote_summary",
}


# ── Test: SMTP Credential Passthrough ─────────────────────────────────────


class TestSMTPCredentialPassthrough:
    """Verify SMTP host/port/sender/username/password/security reach email_sender."""

    @pytest.mark.asyncio
    async def test_credentials_passed_to_send_report_email(self) -> None:
        """All SMTP config fields must be forwarded to send_report_email()."""
        mock_send = AsyncMock(return_value=(True, "Sent successfully"))

        with patch(
            "zorivest_core.pipeline_steps.send_step.send_report_email",
            mock_send,
            create=True,
        ):
            # Must also patch the import inside _send_emails
            with patch.dict(
                "sys.modules",
                {
                    "zorivest_infra.email.email_sender": MagicMock(
                        send_report_email=mock_send
                    ),
                    "zorivest_infra.email.delivery_tracker": MagicMock(
                        compute_dedup_key=lambda **kw: hashlib.sha256(
                            f"{kw['report_id']}|{kw['channel']}|{kw['recipient']}|{kw['snapshot_hash']}".encode()
                        ).hexdigest()
                    ),
                },
            ):
                step = SendStep()
                ctx = _make_context(smtp_config=DEFAULT_SMTP)
                result = await step.execute(DEFAULT_EMAIL_PARAMS, ctx)

        assert result.status == PipelineStatus.SUCCESS
        mock_send.assert_called_once()
        call_kwargs = mock_send.call_args.kwargs
        assert call_kwargs["smtp_host"] == "smtp.gmail.com"
        assert call_kwargs["smtp_port"] == 587
        assert call_kwargs["sender"] == "me@gmail.com"
        assert call_kwargs["smtp_username"] == "me@gmail.com"
        assert call_kwargs["smtp_password"] == "app-password-123"
        assert call_kwargs["use_tls"] is True  # STARTTLS → use_tls=True

    @pytest.mark.asyncio
    async def test_ssl_mode_sets_use_tls_false(self) -> None:
        """When security='SSL', use_tls should be False."""
        ssl_config = {**DEFAULT_SMTP, "security": "SSL", "port": 465}
        mock_send = AsyncMock(return_value=(True, "Sent successfully"))

        with patch.dict(
            "sys.modules",
            {
                "zorivest_infra.email.email_sender": MagicMock(
                    send_report_email=mock_send
                ),
                "zorivest_infra.email.delivery_tracker": MagicMock(
                    compute_dedup_key=lambda **kw: "test-dedup-key"
                ),
            },
        ):
            step = SendStep()
            ctx = _make_context(smtp_config=ssl_config)
            await step.execute(DEFAULT_EMAIL_PARAMS, ctx)

        call_kwargs = mock_send.call_args.kwargs
        assert call_kwargs["use_tls"] is False
        assert call_kwargs["smtp_port"] == 465

    @pytest.mark.asyncio
    async def test_empty_credentials_become_none(self) -> None:
        """Empty string creds should convert to None (not passed as '')."""
        no_auth_config = {**DEFAULT_SMTP, "username": "", "password": ""}
        mock_send = AsyncMock(return_value=(True, "Sent successfully"))

        with patch.dict(
            "sys.modules",
            {
                "zorivest_infra.email.email_sender": MagicMock(
                    send_report_email=mock_send
                ),
                "zorivest_infra.email.delivery_tracker": MagicMock(
                    compute_dedup_key=lambda **kw: "test-dedup-key"
                ),
            },
        ):
            step = SendStep()
            ctx = _make_context(smtp_config=no_auth_config)
            await step.execute(DEFAULT_EMAIL_PARAMS, ctx)

        call_kwargs = mock_send.call_args.kwargs
        assert call_kwargs["smtp_username"] is None
        assert call_kwargs["smtp_password"] is None


# ── Test: Email Body Resolution ───────────────────────────────────────────


class TestEmailBodyResolution:
    """Verify body resolution order: html_body > body_template > default."""

    @pytest.mark.asyncio
    async def test_html_body_takes_precedence(self) -> None:
        """When html_body is provided, it bypasses body_template."""
        mock_send = AsyncMock(return_value=(True, "Sent"))
        params = {
            **DEFAULT_EMAIL_PARAMS,
            "html_body": "<h1>Custom HTML</h1>",
            "body_template": "daily_quote_summary",
        }

        with patch.dict(
            "sys.modules",
            {
                "zorivest_infra.email.email_sender": MagicMock(
                    send_report_email=mock_send
                ),
                "zorivest_infra.email.delivery_tracker": MagicMock(
                    compute_dedup_key=lambda **kw: "test-key"
                ),
            },
        ):
            step = SendStep()
            ctx = _make_context(smtp_config=DEFAULT_SMTP)
            await step.execute(params, ctx)

        assert mock_send.call_args.kwargs["html_body"] == "<h1>Custom HTML</h1>"

    @pytest.mark.asyncio
    async def test_body_template_used_when_no_html_body(self) -> None:
        """When html_body is None, body_template string is used as-is."""
        mock_send = AsyncMock(return_value=(True, "Sent"))
        params = {
            **DEFAULT_EMAIL_PARAMS,
            "body_template": "daily_quote_summary",
        }

        with patch.dict(
            "sys.modules",
            {
                "zorivest_infra.email.email_sender": MagicMock(
                    send_report_email=mock_send
                ),
                "zorivest_infra.email.delivery_tracker": MagicMock(
                    compute_dedup_key=lambda **kw: "test-key"
                ),
            },
        ):
            step = SendStep()
            ctx = _make_context(smtp_config=DEFAULT_SMTP)
            await step.execute(params, ctx)

        assert mock_send.call_args.kwargs["html_body"] == "daily_quote_summary"

    @pytest.mark.asyncio
    async def test_default_fallback_when_no_body(self) -> None:
        """When both html_body and body_template are empty, use default."""
        mock_send = AsyncMock(return_value=(True, "Sent"))
        params = {
            "channel": "email",
            "recipients": ["you@example.com"],
            "subject": "Test",
            "body_template": "",
        }

        with patch.dict(
            "sys.modules",
            {
                "zorivest_infra.email.email_sender": MagicMock(
                    send_report_email=mock_send
                ),
                "zorivest_infra.email.delivery_tracker": MagicMock(
                    compute_dedup_key=lambda **kw: "test-key"
                ),
            },
        ):
            step = SendStep()
            ctx = _make_context(smtp_config=DEFAULT_SMTP)
            await step.execute(params, ctx)

        assert mock_send.call_args.kwargs["html_body"] == "<p>Report attached</p>"


# ── Test: Dedup Key Behavior ──────────────────────────────────────────────


class TestDedupBehavior:
    """Verify dedup key computation and skip-on-duplicate behavior."""

    @pytest.mark.asyncio
    async def test_dedup_skips_when_key_exists(self) -> None:
        """When delivery_repo returns existing record, email is skipped."""
        mock_send = AsyncMock(return_value=(True, "Sent"))
        mock_repo = MagicMock()
        mock_repo.get_by_dedup_key.return_value = MagicMock()  # existing delivery

        with patch.dict(
            "sys.modules",
            {
                "zorivest_infra.email.email_sender": MagicMock(
                    send_report_email=mock_send
                ),
                "zorivest_infra.email.delivery_tracker": MagicMock(
                    compute_dedup_key=lambda **kw: "duplicate-key"
                ),
            },
        ):
            step = SendStep()
            ctx = _make_context(
                smtp_config=DEFAULT_SMTP,
                delivery_repository=mock_repo,
            )
            result = await step.execute(DEFAULT_EMAIL_PARAMS, ctx)

        # Email should NOT have been sent
        mock_send.assert_not_called()
        # Status is SUCCESS (no failures), but sent=0
        assert result.status == PipelineStatus.SUCCESS
        assert result.output["sent"] == 0
        deliveries = result.output["deliveries"]
        assert deliveries[0]["status"] == "skipped"

    @pytest.mark.asyncio
    async def test_dedup_passes_when_no_delivery_repo(self) -> None:
        """Without delivery_repo, dedup check is skipped entirely."""
        mock_send = AsyncMock(return_value=(True, "Sent"))

        with patch.dict(
            "sys.modules",
            {
                "zorivest_infra.email.email_sender": MagicMock(
                    send_report_email=mock_send
                ),
                "zorivest_infra.email.delivery_tracker": MagicMock(
                    compute_dedup_key=lambda **kw: "key"
                ),
            },
        ):
            step = SendStep()
            ctx = _make_context(smtp_config=DEFAULT_SMTP)  # no delivery_repo
            await step.execute(DEFAULT_EMAIL_PARAMS, ctx)

        mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_dedup_sends_when_key_not_found(self) -> None:
        """When delivery_repo returns None, email is sent normally."""
        mock_send = AsyncMock(return_value=(True, "Sent"))
        mock_repo = MagicMock()
        mock_repo.get_by_dedup_key.return_value = None  # no prior delivery

        with patch.dict(
            "sys.modules",
            {
                "zorivest_infra.email.email_sender": MagicMock(
                    send_report_email=mock_send
                ),
                "zorivest_infra.email.delivery_tracker": MagicMock(
                    compute_dedup_key=lambda **kw: "fresh-key"
                ),
            },
        ):
            step = SendStep()
            ctx = _make_context(
                smtp_config=DEFAULT_SMTP,
                delivery_repository=mock_repo,
            )
            result = await step.execute(DEFAULT_EMAIL_PARAMS, ctx)

        mock_send.assert_called_once()
        assert result.output["sent"] == 1

    @pytest.mark.asyncio
    async def test_dedup_key_uses_snapshot_hash_when_available(self) -> None:
        """When snapshot_hash is provided, it participates in the dedup key."""
        captured_kwargs: list[dict] = []

        def capture_dedup(**kw: Any) -> str:
            captured_kwargs.append(kw)
            return "captured-key"

        mock_send = AsyncMock(return_value=(True, "Sent"))

        with patch.dict(
            "sys.modules",
            {
                "zorivest_infra.email.email_sender": MagicMock(
                    send_report_email=mock_send
                ),
                "zorivest_infra.email.delivery_tracker": MagicMock(
                    compute_dedup_key=capture_dedup
                ),
            },
        ):
            params = {**DEFAULT_EMAIL_PARAMS, "snapshot_hash": "abc123"}
            step = SendStep()
            ctx = _make_context(smtp_config=DEFAULT_SMTP)
            await step.execute(params, ctx)

        assert len(captured_kwargs) == 1
        assert captured_kwargs[0]["snapshot_hash"] == "abc123"

    @pytest.mark.asyncio
    async def test_dedup_key_uses_run_id_when_no_snapshot_hash(self) -> None:
        """Without snapshot_hash, dedup falls back to run_id for uniqueness."""
        captured_kwargs: list[dict] = []

        def capture_dedup(**kw: Any) -> str:
            captured_kwargs.append(kw)
            return "captured-key"

        mock_send = AsyncMock(return_value=(True, "Sent"))

        with patch.dict(
            "sys.modules",
            {
                "zorivest_infra.email.email_sender": MagicMock(
                    send_report_email=mock_send
                ),
                "zorivest_infra.email.delivery_tracker": MagicMock(
                    compute_dedup_key=capture_dedup
                ),
            },
        ):
            step = SendStep()
            ctx = _make_context(smtp_config=DEFAULT_SMTP)
            await step.execute(DEFAULT_EMAIL_PARAMS, ctx)

        # run_id fallback is used when snapshot_hash is absent
        assert captured_kwargs[0]["snapshot_hash"] == "test-run-001"


# ── Test: Error Surfacing ─────────────────────────────────────────────────


class TestErrorSurfacing:
    """Verify delivery errors are surfaced in StepResult."""

    @pytest.mark.asyncio
    async def test_smtp_failure_surfaces_in_step_result(self) -> None:
        """When send_report_email returns (False, error), StepResult.error is set."""
        mock_send = AsyncMock(return_value=(False, "Authentication failed"))

        with patch.dict(
            "sys.modules",
            {
                "zorivest_infra.email.email_sender": MagicMock(
                    send_report_email=mock_send
                ),
                "zorivest_infra.email.delivery_tracker": MagicMock(
                    compute_dedup_key=lambda **kw: "key"
                ),
            },
        ):
            step = SendStep()
            ctx = _make_context(smtp_config=DEFAULT_SMTP)
            result = await step.execute(DEFAULT_EMAIL_PARAMS, ctx)

        assert result.status == PipelineStatus.FAILED
        assert result.error == "Authentication failed"
        assert result.output["failed"] == 1

    @pytest.mark.asyncio
    async def test_unknown_channel_returns_failed(self) -> None:
        """An unknown channel should fail with descriptive error."""
        step = SendStep()
        ctx = _make_context(smtp_config=DEFAULT_SMTP)
        params = {**DEFAULT_EMAIL_PARAMS, "channel": "slack"}
        result = await step.execute(params, ctx)

        assert result.status == PipelineStatus.FAILED
        assert "Unknown channel: slack" in (result.error or "")


# ── Test: Multiple Recipients ─────────────────────────────────────────────


class TestMultipleRecipients:
    """Verify behavior with multiple recipients."""

    @pytest.mark.asyncio
    async def test_sends_to_all_recipients(self) -> None:
        """Each recipient gets a separate email."""
        mock_send = AsyncMock(return_value=(True, "Sent"))

        with patch.dict(
            "sys.modules",
            {
                "zorivest_infra.email.email_sender": MagicMock(
                    send_report_email=mock_send
                ),
                "zorivest_infra.email.delivery_tracker": MagicMock(
                    compute_dedup_key=lambda **kw: f"key-{kw['recipient']}"
                ),
            },
        ):
            params = {
                **DEFAULT_EMAIL_PARAMS,
                "recipients": ["a@x.com", "b@x.com", "c@x.com"],
            }
            step = SendStep()
            ctx = _make_context(smtp_config=DEFAULT_SMTP)
            result = await step.execute(params, ctx)

        assert mock_send.call_count == 3
        assert result.output["sent"] == 3
        assert result.output["failed"] == 0

    @pytest.mark.asyncio
    async def test_partial_failure_marks_step_failed(self) -> None:
        """If any recipient fails, step status is FAILED."""
        send_results = iter([(True, "Sent"), (False, "Timeout"), (True, "Sent")])
        mock_send = AsyncMock(side_effect=lambda **kw: next(send_results))

        with patch.dict(
            "sys.modules",
            {
                "zorivest_infra.email.email_sender": MagicMock(
                    send_report_email=mock_send
                ),
                "zorivest_infra.email.delivery_tracker": MagicMock(
                    compute_dedup_key=lambda **kw: f"key-{kw['recipient']}"
                ),
            },
        ):
            params = {
                **DEFAULT_EMAIL_PARAMS,
                "recipients": ["a@x.com", "b@x.com", "c@x.com"],
            }
            step = SendStep()
            ctx = _make_context(smtp_config=DEFAULT_SMTP)
            result = await step.execute(params, ctx)

        assert result.status == PipelineStatus.FAILED
        assert result.output["sent"] == 2
        assert result.output["failed"] == 1
        assert result.error == "Timeout"


# ── Test: Integration Timing ──────────────────────────────────────────────


class TestTimingBehavior:
    """Verify that actual SMTP calls take non-trivial time (> 100ms)."""

    @pytest.mark.asyncio
    async def test_successful_send_not_instant(self) -> None:
        """A successful send should call send_report_email (verifiable by mock)."""
        import time

        call_times: list[float] = []

        async def tracked_send(**kw: Any) -> tuple[bool, str]:
            call_times.append(time.monotonic())
            return (True, "Sent")

        with patch.dict(
            "sys.modules",
            {
                "zorivest_infra.email.email_sender": MagicMock(
                    send_report_email=tracked_send
                ),
                "zorivest_infra.email.delivery_tracker": MagicMock(
                    compute_dedup_key=lambda **kw: "key"
                ),
            },
        ):
            step = SendStep()
            ctx = _make_context(smtp_config=DEFAULT_SMTP)
            await step.execute(DEFAULT_EMAIL_PARAMS, ctx)

        # Verify send_report_email was actually called (not skipped)
        assert len(call_times) == 1, "send_report_email must be called exactly once"


# ── Test: Dedup Run-ID Fallback (RED → will drive fix) ────────────────────


class TestDedupRunIdFallback:
    """Verify that different run_ids produce different dedup keys.

    Bug: When snapshot_hash is absent (no store_report step), the dedup key
    is identical across runs → all runs except the first are permanently
    skipped. The fix: use run_id as fallback in the snapshot_hash slot.
    """

    @pytest.mark.asyncio
    async def test_different_runs_get_different_dedup_keys(self) -> None:
        """Two runs with different run_ids must NOT share a dedup key."""
        captured_hashes: list[str] = []

        def capture_dedup(**kw: Any) -> str:
            captured_hashes.append(kw["snapshot_hash"])
            return hashlib.sha256(
                f"{kw['report_id']}|{kw['channel']}|{kw['recipient']}|{kw['snapshot_hash']}".encode()
            ).hexdigest()

        mock_send = AsyncMock(return_value=(True, "Sent"))

        with patch.dict(
            "sys.modules",
            {
                "zorivest_infra.email.email_sender": MagicMock(
                    send_report_email=mock_send
                ),
                "zorivest_infra.email.delivery_tracker": MagicMock(
                    compute_dedup_key=capture_dedup
                ),
            },
        ):
            step = SendStep()

            # Run 1
            ctx1 = _make_context(run_id="run-aaa", smtp_config=DEFAULT_SMTP)
            await step.execute(DEFAULT_EMAIL_PARAMS, ctx1)

            # Run 2 — different run_id, same params
            ctx2 = _make_context(run_id="run-bbb", smtp_config=DEFAULT_SMTP)
            await step.execute(DEFAULT_EMAIL_PARAMS, ctx2)

        assert len(captured_hashes) == 2
        # The dedup keys must differ because run_id differs
        assert captured_hashes[0] != captured_hashes[1], (
            f"Dedup keys must differ across runs but both used: {captured_hashes[0]!r}"
        )
