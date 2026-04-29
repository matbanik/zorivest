# packages/infrastructure/src/zorivest_infra/email/email_sender.py
"""Async email sender using aiosmtplib (§9.8b, §9H).

Builds MIME multipart messages with HTML body.
Uses STARTTLS for secure transport.

PDF attachment support removed per §9H (Pipeline Markdown Migration).
Optional .md attachment support added per §9H.2.
"""

from __future__ import annotations

from email import encoders
from email.mime.base import MIMEBase
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
    use_tls: bool = True,
    smtp_username: str | None = None,
    smtp_password: str | None = None,
    attachment_path: str | None = None,
) -> tuple[bool, str]:
    """Send a report email with HTML body and optional .md attachment.

    Args:
        smtp_host: SMTP server hostname.
        smtp_port: SMTP server port (typically 587 for STARTTLS).
        sender: From address.
        recipient: To address.
        subject: Email subject line.
        html_body: HTML body content.
        use_tls: Whether to use STARTTLS.
        smtp_username: Optional SMTP auth username.
        smtp_password: Optional SMTP auth password.
        attachment_path: Optional path to a .md file to attach.
            Only .md files are accepted (§9H.6: "no PDF").
            Raises ValueError for non-.md extensions.

    Returns:
        Tuple of (success: bool, message: str).

    Raises:
        ValueError: If attachment_path does not end with .md.
    """
    # §9H.6: Only .md attachments allowed, no PDF
    if attachment_path is not None:
        p = Path(attachment_path)
        if p.suffix.lower() != ".md":
            raise ValueError(
                f"Only .md attachments are supported (got '{p.suffix}'). "
                f"PDF attachments were removed per §9H."
            )

    try:
        # Build MIME message
        msg = MIMEMultipart()
        msg["From"] = sender
        msg["To"] = recipient
        msg["Subject"] = subject
        msg["Date"] = formatdate(localtime=True)

        # HTML body
        msg.attach(MIMEText(html_body, "html"))

        # Optional .md attachment (§9H.2)
        if attachment_path is not None:
            p = Path(attachment_path)
            content = p.read_bytes()
            part = MIMEBase("text", "markdown")
            part.set_payload(content)
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                "attachment",
                filename=p.name,
            )
            msg.attach(part)

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
