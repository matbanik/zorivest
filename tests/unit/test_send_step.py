# tests/unit/test_send_step.py
"""TDD Red-phase tests for SendStep + email delivery (MEU-88).

Acceptance criteria AC-S1..AC-S20 per implementation-plan §9.8a–c.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError


# ---------------------------------------------------------------------------
# AC-S1: SendStep auto-registers with type_name="send" in STEP_REGISTRY
# ---------------------------------------------------------------------------


def test_ac_s1_send_step_auto_registers():
    """SendStep auto-registers in STEP_REGISTRY."""
    from zorivest_core.domain.step_registry import STEP_REGISTRY, get_step

    import zorivest_core.pipeline_steps  # noqa: F401

    from zorivest_core.pipeline_steps.send_step import SendStep

    assert "send" in STEP_REGISTRY
    assert get_step("send") is SendStep


# ---------------------------------------------------------------------------
# AC-S2: SendStep.side_effects is True
# ---------------------------------------------------------------------------


def test_ac_s2_send_step_side_effects():
    """SendStep declares side_effects=True."""
    from zorivest_core.pipeline_steps.send_step import SendStep

    assert SendStep.side_effects is True


# ---------------------------------------------------------------------------
# AC-S3: SendStep.Params requires channel field
# ---------------------------------------------------------------------------


def test_ac_s3_params_requires_channel():
    """SendStep.Params requires channel field."""
    from zorivest_core.pipeline_steps.send_step import SendStep

    with pytest.raises(ValidationError):
        SendStep.Params(recipients=["test@example.com"])

    p = SendStep.Params(channel="email", recipients=["test@example.com"])
    assert p.channel == "email"


# ---------------------------------------------------------------------------
# AC-S4: SendStep.Params.recipients enforces max_length=5
# ---------------------------------------------------------------------------


def test_ac_s4_params_recipients_max_length():
    """SendStep.Params.recipients enforces max_length=5."""
    from zorivest_core.pipeline_steps.send_step import SendStep

    # Valid: 5 recipients
    p = SendStep.Params(
        channel="email",
        recipients=["a@x.com", "b@x.com", "c@x.com", "d@x.com", "e@x.com"],
    )
    assert len(p.recipients) == 5

    # Invalid: 6 recipients
    with pytest.raises(ValidationError):
        SendStep.Params(
            channel="email",
            recipients=["a@x.com", "b@x.com", "c@x.com", "d@x.com", "e@x.com", "f@x.com"],
        )


# ---------------------------------------------------------------------------
# AC-S5: SendStep.Params.subject and body_template default to empty string
# ---------------------------------------------------------------------------


def test_ac_s5_params_defaults():
    """SendStep.Params subject and body_template default to empty string."""
    from zorivest_core.pipeline_steps.send_step import SendStep

    p = SendStep.Params(channel="email", recipients=["test@example.com"])
    assert p.subject == ""
    assert p.body_template == ""


# ---------------------------------------------------------------------------
# AC-S6: execute() returns FAILED for unknown channel
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ac_s6_execute_fails_unknown_channel():
    """execute() returns FAILED for unknown channel."""
    from zorivest_core.domain.pipeline import StepContext
    from zorivest_core.pipeline_steps.send_step import SendStep

    step = SendStep()
    context = StepContext(run_id="run-1", policy_id="pol-1")

    result = await step.execute(
        params={"channel": "carrier_pigeon", "recipients": ["test@example.com"]},
        context=context,
    )

    assert result.status.value == "failed"
    assert "carrier_pigeon" in result.error


# ---------------------------------------------------------------------------
# AC-S7: execute() dispatches to _send_emails for channel="email"
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ac_s7_execute_dispatches_email():
    """execute() dispatches to _send_emails for channel='email'."""
    from zorivest_core.domain.pipeline import StepContext
    from zorivest_core.pipeline_steps.send_step import SendStep

    step = SendStep()
    step._send_emails = AsyncMock(return_value={"sent": 1, "failed": 0, "deliveries": []})

    context = StepContext(run_id="run-1", policy_id="pol-1")

    result = await step.execute(
        params={"channel": "email", "recipients": ["test@example.com"]},
        context=context,
    )

    step._send_emails.assert_called_once()
    assert result.status.value == "success"


# ---------------------------------------------------------------------------
# AC-S8: execute() dispatches to _save_local for channel="local_file"
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ac_s8_execute_dispatches_local_file():
    """execute() dispatches to _save_local for channel='local_file'."""
    from zorivest_core.domain.pipeline import StepContext
    from zorivest_core.pipeline_steps.send_step import SendStep

    step = SendStep()
    step._save_local = AsyncMock(return_value={"sent": 1, "failed": 0, "deliveries": []})

    context = StepContext(run_id="run-1", policy_id="pol-1")

    result = await step.execute(
        params={"channel": "local_file", "recipients": ["/tmp/report.pdf"]},
        context=context,
    )

    step._save_local.assert_called_once()
    assert result.status.value == "success"


# ---------------------------------------------------------------------------
# AC-S9: execute() returns sent/failed counts in output
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ac_s9_execute_returns_counts():
    """execute() returns sent/failed counts in output."""
    from zorivest_core.domain.pipeline import StepContext
    from zorivest_core.pipeline_steps.send_step import SendStep

    step = SendStep()
    step._send_emails = AsyncMock(
        return_value={"sent": 2, "failed": 1, "deliveries": []}
    )

    context = StepContext(run_id="run-1", policy_id="pol-1")

    result = await step.execute(
        params={
            "channel": "email",
            "recipients": ["a@x.com", "b@x.com", "c@x.com"],
        },
        context=context,
    )

    assert result.output["sent"] == 2
    assert result.output["failed"] == 1


# ---------------------------------------------------------------------------
# AC-S10: compute_dedup_key produces deterministic SHA-256 hex string
# ---------------------------------------------------------------------------


def test_ac_s10_compute_dedup_key_deterministic():
    """compute_dedup_key produces deterministic SHA-256 hex string."""
    from zorivest_infra.email.delivery_tracker import compute_dedup_key

    key1 = compute_dedup_key(
        report_id="rpt-1",
        channel="email",
        recipient="test@example.com",
        snapshot_hash="abc123",
    )
    key2 = compute_dedup_key(
        report_id="rpt-1",
        channel="email",
        recipient="test@example.com",
        snapshot_hash="abc123",
    )

    assert key1 == key2
    assert len(key1) == 64
    assert all(c in "0123456789abcdef" for c in key1)


# ---------------------------------------------------------------------------
# AC-S11: compute_dedup_key changes when any input field changes
# ---------------------------------------------------------------------------


def test_ac_s11_compute_dedup_key_changes():
    """compute_dedup_key changes when any input field changes."""
    from zorivest_infra.email.delivery_tracker import compute_dedup_key

    base_args = {
        "report_id": "rpt-1",
        "channel": "email",
        "recipient": "test@example.com",
        "snapshot_hash": "abc123",
    }

    base_key = compute_dedup_key(**base_args)

    # Change each field independently
    for field, alt_value in [
        ("report_id", "rpt-2"),
        ("channel", "local_file"),
        ("recipient", "other@example.com"),
        ("snapshot_hash", "def456"),
    ]:
        altered = {**base_args, field: alt_value}
        alt_key = compute_dedup_key(**altered)
        assert alt_key != base_key, f"Key should differ when {field} changes"


# ---------------------------------------------------------------------------
# AC-S12: send_report_email builds correct MIME multipart structure
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ac_s12_send_report_email_mime():
    """send_report_email builds correct MIME multipart structure."""
    from zorivest_infra.email.email_sender import send_report_email

    with patch("zorivest_infra.email.email_sender.aiosmtplib") as mock_smtp:
        mock_smtp.send = AsyncMock()

        success, msg = await send_report_email(
            smtp_host="smtp.example.com",
            smtp_port=587,
            sender="sender@example.com",
            recipient="recipient@example.com",
            subject="Test Report",
            html_body="<h1>Report</h1>",
        )

        assert success is True
        mock_smtp.send.assert_called_once()

        # Verify MIME message structure
        sent_msg = mock_smtp.send.call_args[0][0]
        assert sent_msg["From"] == "sender@example.com"
        assert sent_msg["To"] == "recipient@example.com"
        assert sent_msg["Subject"] == "Test Report"


# ---------------------------------------------------------------------------
# AC-S13: send_report_email attaches PDF when pdf_path is provided
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ac_s13_send_report_email_pdf_attachment(tmp_path):
    """send_report_email attaches PDF when pdf_path is provided."""
    from zorivest_infra.email.email_sender import send_report_email

    pdf_file = tmp_path / "report.pdf"
    pdf_file.write_bytes(b"%PDF-1.4 test content")

    with patch("zorivest_infra.email.email_sender.aiosmtplib") as mock_smtp:
        mock_smtp.send = AsyncMock()

        success, msg = await send_report_email(
            smtp_host="smtp.example.com",
            smtp_port=587,
            sender="sender@example.com",
            recipient="recipient@example.com",
            subject="Test Report",
            html_body="<h1>Report</h1>",
            pdf_path=str(pdf_file),
        )

        assert success is True
        sent_msg = mock_smtp.send.call_args[0][0]

        # Verify attachment is present
        parts = list(sent_msg.walk())
        content_types = [p.get_content_type() for p in parts]
        assert "application/pdf" in content_types


# ---------------------------------------------------------------------------
# AC-S14: send_report_email returns (False, error_msg) on SMTP failure
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ac_s14_send_report_email_smtp_failure():
    """send_report_email returns (False, error_msg) on SMTP failure."""
    from zorivest_infra.email.email_sender import send_report_email

    with patch("zorivest_infra.email.email_sender.aiosmtplib") as mock_smtp:
        mock_smtp.send = AsyncMock(side_effect=Exception("Connection refused"))

        success, msg = await send_report_email(
            smtp_host="smtp.example.com",
            smtp_port=587,
            sender="sender@example.com",
            recipient="recipient@example.com",
            subject="Test Report",
            html_body="<h1>Report</h1>",
        )

        assert success is False
        assert "Connection refused" in msg


# ---------------------------------------------------------------------------
# AC-S15: params_schema() returns non-empty dict
# ---------------------------------------------------------------------------


def test_ac_s15_params_schema():
    """params_schema() returns non-empty dict."""
    from zorivest_core.pipeline_steps.send_step import SendStep

    schema = SendStep.params_schema()
    assert isinstance(schema, dict)
    assert len(schema) > 0
    assert "properties" in schema


# ---------------------------------------------------------------------------
# AC-S16: _send_emails checks DeliveryRepository and skips if key exists
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ac_s16_send_emails_skips_duplicate():
    """_send_emails checks DeliveryRepository.get_by_dedup_key() and skips
    send if key already exists."""
    from zorivest_core.domain.pipeline import StepContext
    from zorivest_core.pipeline_steps.send_step import SendStep

    # Mock delivery_repo that returns a model (key exists)
    mock_delivery_repo = MagicMock()
    mock_delivery_repo.get_by_dedup_key.return_value = MagicMock()  # existing delivery

    step = SendStep()
    context = StepContext(
        run_id="run-1",
        policy_id="pol-1",
        outputs={"delivery_repository": mock_delivery_repo},
    )

    params = SendStep.Params(
        channel="email",
        recipients=["test@example.com"],
        subject="Test",
        report_id="rpt-1",
        snapshot_hash="abc123",
    )

    result = await step._send_emails(params, context)

    # Should not have called send, should have skipped
    assert result["sent"] == 0
    mock_delivery_repo.get_by_dedup_key.assert_called_once()


# ---------------------------------------------------------------------------
# AC-S17: _send_emails records ReportDeliveryModel after successful send
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ac_s17_send_emails_records_delivery():
    """_send_emails records ReportDeliveryModel row via
    DeliveryRepository.create() after successful send."""
    from zorivest_core.domain.pipeline import StepContext
    from zorivest_core.pipeline_steps.send_step import SendStep

    mock_delivery_repo = MagicMock()
    mock_delivery_repo.get_by_dedup_key.return_value = None  # not yet delivered

    step = SendStep()
    context = StepContext(
        run_id="run-1",
        policy_id="pol-1",
        outputs={"delivery_repository": mock_delivery_repo},
    )

    params = SendStep.Params(
        channel="email",
        recipients=["test@example.com"],
        subject="Test",
        report_id="rpt-1",
        snapshot_hash="abc123",
    )

    with patch(
        "zorivest_infra.email.email_sender.send_report_email",
        new_callable=AsyncMock,
        return_value=(True, "Sent"),
    ) as _mock_send:
        result = await step._send_emails(params, context)

    assert result["sent"] == 1
    mock_delivery_repo.create.assert_called_once()
    call_kwargs = mock_delivery_repo.create.call_args.kwargs
    assert call_kwargs["channel"] == "email"
    assert call_kwargs["recipient"] == "test@example.com"
    assert call_kwargs["status"] == "sent"
    assert "dedup_key" in call_kwargs


# ---------------------------------------------------------------------------
# AC-S18: DeliveryRepository.get_by_dedup_key() returns None/model
# ---------------------------------------------------------------------------


def test_ac_s18_delivery_repo_get_by_dedup_key():
    """DeliveryRepository.get_by_dedup_key() returns None for unknown key
    and model for known key."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from zorivest_infra.database.models import Base, ReportDeliveryModel, ReportModel
    from zorivest_infra.database.scheduling_repositories import DeliveryRepository

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        # Create prerequisite report
        report = ReportModel(
            id="rpt-1",
            name="Test Report",
            version=1,
            spec_json="{}",
            format="pdf",
            created_at=datetime.now(timezone.utc),
        )
        session.add(report)
        session.flush()

        repo = DeliveryRepository(session)

        # Unknown key
        assert repo.get_by_dedup_key("unknown-key") is None

        # Insert a delivery
        session.add(
            ReportDeliveryModel(
                report_id="rpt-1",
                channel="email",
                recipient="test@example.com",
                status="sent",
                dedup_key="known-key",
            )
        )
        session.flush()

        # Known key
        result = repo.get_by_dedup_key("known-key")
        assert result is not None
        assert result.dedup_key == "known-key"


# ---------------------------------------------------------------------------
# AC-S19: DeliveryRepository.create() persists row with correct fields
# ---------------------------------------------------------------------------


def test_ac_s19_delivery_repo_create():
    """DeliveryRepository.create() persists row with correct dedup_key,
    channel, recipient, status."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from zorivest_infra.database.models import Base, ReportDeliveryModel, ReportModel
    from zorivest_infra.database.scheduling_repositories import DeliveryRepository

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        # Create prerequisite report
        report = ReportModel(
            id="rpt-1",
            name="Test Report",
            version=1,
            spec_json="{}",
            format="pdf",
            created_at=datetime.now(timezone.utc),
        )
        session.add(report)
        session.flush()

        repo = DeliveryRepository(session)
        delivery_id = repo.create(
            report_id="rpt-1",
            channel="email",
            recipient="test@example.com",
            status="sent",
            dedup_key="unique-key-123",
        )
        session.flush()

        # Verify persisted
        delivery = session.get(ReportDeliveryModel, delivery_id)
        assert delivery is not None
        assert delivery.channel == "email"
        assert delivery.recipient == "test@example.com"
        assert delivery.status == "sent"
        assert delivery.dedup_key == "unique-key-123"
        assert delivery.report_id == "rpt-1"


# ---------------------------------------------------------------------------
# AC-S20: SendStep.Params accepts optional ref-resolved fields
# ---------------------------------------------------------------------------


def test_ac_s20_params_accepts_optional_ref_fields():
    """SendStep.Params accepts optional ref-resolved fields (report_id,
    snapshot_hash, pdf_path, html_body) without validation error."""
    from zorivest_core.pipeline_steps.send_step import SendStep

    # Minimal — no optional fields
    p1 = SendStep.Params(channel="email", recipients=["test@example.com"])
    assert p1.report_id is None
    assert p1.snapshot_hash is None
    assert p1.pdf_path is None
    assert p1.html_body is None

    # With all optional fields
    p2 = SendStep.Params(
        channel="email",
        recipients=["test@example.com"],
        report_id="rpt-1",
        snapshot_hash="abc123",
        pdf_path="/tmp/report.pdf",
        html_body="<h1>Hello</h1>",
    )
    assert p2.report_id == "rpt-1"
    assert p2.snapshot_hash == "abc123"
    assert p2.pdf_path == "/tmp/report.pdf"
    assert p2.html_body == "<h1>Hello</h1>"


# ---------------------------------------------------------------------------
# F1 regression: execute() returns FAILED when deliveries fail
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_execute_returns_failed_when_deliveries_fail():
    """execute() returns FAILED status when _send_emails reports failures."""
    from zorivest_core.domain.pipeline import StepContext
    from zorivest_core.pipeline_steps.send_step import SendStep

    step = SendStep()
    step._send_emails = AsyncMock(
        return_value={"sent": 0, "failed": 2, "deliveries": []}
    )

    context = StepContext(run_id="run-1", policy_id="pol-1")

    result = await step.execute(
        params={
            "channel": "email",
            "recipients": ["a@x.com", "b@x.com"],
        },
        context=context,
    )

    assert result.status.value == "failed"
    assert result.output["failed"] == 2


# ---------------------------------------------------------------------------
# F4: _save_local() copies file to destination path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_save_local_copies_file(tmp_path):
    """_save_local() copies source PDF to destination paths."""
    from zorivest_core.domain.pipeline import StepContext
    from zorivest_core.pipeline_steps.send_step import SendStep

    # Create a source file
    source = tmp_path / "source.pdf"
    source.write_bytes(b"%PDF-1.4 test content")

    dest = tmp_path / "output" / "report.pdf"
    dest.parent.mkdir(parents=True)

    step = SendStep()
    context = StepContext(run_id="run-1", policy_id="pol-1")

    params = SendStep.Params(
        channel="local_file",
        recipients=[str(dest)],
        pdf_path=str(source),
    )

    result = await step._save_local(params, context)

    assert result["sent"] == 1
    assert result["failed"] == 0
    assert dest.read_bytes() == b"%PDF-1.4 test content"


# ---------------------------------------------------------------------------
# F4: _save_local() fails when pdf_path is None
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_save_local_fails_without_pdf_path():
    """_save_local() returns all-failed when pdf_path is None."""
    from zorivest_core.domain.pipeline import StepContext
    from zorivest_core.pipeline_steps.send_step import SendStep

    step = SendStep()
    context = StepContext(run_id="run-1", policy_id="pol-1")

    params = SendStep.Params(
        channel="local_file",
        recipients=["/tmp/out.pdf"],
        # pdf_path deliberately omitted (None)
    )

    result = await step._save_local(params, context)

    assert result["sent"] == 0
    assert result["failed"] == 1
    assert "No pdf_path" in result["deliveries"][0]["error"]

