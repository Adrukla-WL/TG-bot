"""Utility module for sending email notifications."""
from __future__ import annotations

import logging
import os
from email.message import EmailMessage
from smtplib import SMTP, SMTP_SSL

LOGGER = logging.getLogger(__name__)


def send_email(subject: str, body: str, *, to: list[str] | None = None) -> None:
    """Send an email using SMTP configuration from environment variables.

    Parameters
    ----------
    subject: str
        Email subject line.
    body: str
        Plain text email body.
    to: list[str] | None
        Optional list of recipients. When omitted, the ``EMAIL_RECIPIENTS``
        environment variable is used (comma-separated values).
    """
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    default_recipients = os.getenv("EMAIL_RECIPIENTS", "").split(",")
    recipients = [addr.strip() for addr in (to or default_recipients) if addr.strip()]

    if not (smtp_host and smtp_port and smtp_user and smtp_password and recipients):
        LOGGER.warning("Email configuration incomplete; skipping email dispatch.")
        return

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = smtp_user
    message["To"] = ", ".join(recipients)
    message.set_content(body)

    use_ssl = os.getenv("SMTP_USE_SSL", "true").lower() == "true"

    try:
        if use_ssl:
            with SMTP_SSL(smtp_host, int(smtp_port)) as client:
                client.login(smtp_user, smtp_password)
                client.send_message(message)
        else:
            with SMTP(smtp_host, int(smtp_port)) as client:
                client.starttls()
                client.login(smtp_user, smtp_password)
                client.send_message(message)
        LOGGER.info("Email sent to %s", recipients)
    except Exception as exc:  # pragma: no cover - network operations
        LOGGER.exception("Failed to send email: %s", exc)
