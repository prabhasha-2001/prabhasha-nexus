"""Minimal SMTP email service with graceful degradation."""
from __future__ import annotations

import smtplib
from email.message import EmailMessage

from flask import current_app


def send_email(to: str, subject: str, body: str) -> dict:
    config = current_app.config
    if not config.get("MAIL_ENABLED") or not config.get("SMTP_HOST"):
        current_app.logger.info("Email skipped (SMTP not configured): %s", subject)
        return {"status": "not_configured", "to": to, "subject": subject}

    message = EmailMessage()
    message["From"] = config["MAIL_FROM"]
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    try:
        with smtplib.SMTP(config["SMTP_HOST"], config["SMTP_PORT"], timeout=10) as smtp:
            smtp.ehlo()
            if config["SMTP_PORT"] != 25:
                smtp.starttls()
                smtp.ehlo()
            if config["SMTP_USERNAME"]:
                smtp.login(config["SMTP_USERNAME"], config["SMTP_PASSWORD"])
            smtp.send_message(message)
        return {"status": "sent", "to": to, "subject": subject}
    except Exception as exc:  # pragma: no cover - network dependent
        current_app.logger.warning("Email delivery failed: %s", exc)
        return {"status": "failed", "to": to, "subject": subject, "error": str(exc)}
