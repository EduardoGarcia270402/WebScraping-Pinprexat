from __future__ import annotations

import smtplib
from email.message import EmailMessage

from config.settings import get_settings


def send_email(subject: str, body: str) -> bool:
    settings = get_settings()
    required = (
        settings.email_smtp_host,
        settings.email_user,
        settings.email_password,
        settings.email_destinatario,
    )
    if not all(required):
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.email_user
    message["To"] = settings.email_destinatario
    message.set_content(body)

    with smtplib.SMTP(settings.email_smtp_host, settings.email_smtp_port) as smtp:
        smtp.starttls()
        smtp.login(settings.email_user or "", settings.email_password or "")
        smtp.send_message(message)

    return True
