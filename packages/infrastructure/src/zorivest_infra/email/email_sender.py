# packages/infrastructure/src/zorivest_infra/email/email_sender.py
"""Async email sender using aiosmtplib (§9.8b).

Builds MIME multipart messages with HTML body and optional PDF attachment.
Uses STARTTLS for secure transport.
"""

from __future__ import annotations

from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
from pathlib import Path

import aiosmtplib


async def send_report_email(
    *,
    smtp_host: str,
    smtp_port: int,
    sender: str,
    recipient: str,
    subject: str,
    html_body: str,
    pdf_path: str | None = None,
    use_tls: bool = True,
    smtp_username: str | None = None,
    smtp_password: str | None = None,
) -> tuple[bool, str]:
    """Send a report email with optional PDF attachment.

    Args:
        smtp_host: SMTP server hostname.
        smtp_port: SMTP server port (typically 587 for STARTTLS).
        sender: From address.
        recipient: To address.
        subject: Email subject line.
        html_body: HTML body content.
        pdf_path: Optional path to PDF file to attach.
        use_tls: Whether to use STARTTLS.
        smtp_username: Optional SMTP auth username.
        smtp_password: Optional SMTP auth password.

    Returns:
        Tuple of (success: bool, message: str).
    """
    try:
        # Build MIME message
        msg = MIMEMultipart()
        msg["From"] = sender
        msg["To"] = recipient
        msg["Subject"] = subject
        msg["Date"] = formatdate(localtime=True)

        # HTML body
        msg.attach(MIMEText(html_body, "html"))

        # Optional PDF attachment
        if pdf_path is not None:
            pdf_data = Path(pdf_path).read_bytes()
            pdf_part = MIMEApplication(pdf_data, _subtype="pdf")
            pdf_part.add_header(
                "Content-Disposition",
                "attachment",
                filename=Path(pdf_path).name,
            )
            msg.attach(pdf_part)

        # Send via aiosmtplib
        await aiosmtplib.send(
            msg,
            hostname=smtp_host,
            port=smtp_port,
            start_tls=use_tls,
            username=smtp_username,
            password=smtp_password,
        )

        return (True, "Sent successfully")

    except Exception as exc:
        return (False, str(exc))
