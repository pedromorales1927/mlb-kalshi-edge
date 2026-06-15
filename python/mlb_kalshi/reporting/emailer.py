import base64
import logging
from datetime import datetime

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Attachment,
    Content,
    Disposition,
    Email,
    FileContent,
    FileName,
    FileType,
    Mail,
    To,
)

LOGGER = logging.getLogger(__name__)


class SendGridEmailer:
    def __init__(self, api_key: str | None, sender: str | None, recipient: str | None) -> None:
        self.api_key = api_key
        self.sender = sender
        self.recipient = recipient

    def send_report(self, subject: str, html: str, csv_text: str) -> bool:
        if not self.api_key or not self.sender or not self.recipient:
            LOGGER.warning("SendGrid settings incomplete; skipping report email")
            return False
        message = Mail(
            from_email=Email(self.sender),
            to_emails=To(self.recipient),
            subject=subject,
            html_content=Content("text/html", html),
        )
        csv_encoded = base64.b64encode(csv_text.encode("utf-8")).decode("ascii")
        html_encoded = base64.b64encode(html.encode("utf-8")).decode("ascii")
        message.add_attachment(
            Attachment(
                FileContent(csv_encoded),
                FileName("mlb-kalshi-edge-report.csv"),
                FileType("text/csv"),
                Disposition("attachment"),
            )
        )
        message.add_attachment(
            Attachment(
                FileContent(html_encoded),
                FileName("mlb-kalshi-edge-report.html"),
                FileType("text/html"),
                Disposition("attachment"),
            )
        )
        SendGridAPIClient(self.api_key).send(message)
        return True

    def send_error(self, recipient: str | None, failed_step: str, error: Exception) -> None:
        target = recipient or self.recipient
        if not self.api_key or not self.sender or not target:
            LOGGER.error("Pipeline failed at %s: %s", failed_step, error)
            return
        html = f"""
<h1>MLB Kalshi Pipeline Failure</h1>
<p><strong>Timestamp:</strong> {datetime.utcnow().isoformat()}Z</p>
<p><strong>Failed step:</strong> {failed_step}</p>
<p><strong>Error:</strong> {error}</p>
"""
        message = Mail(
            from_email=Email(self.sender),
            to_emails=To(target),
            subject=f"MLB Kalshi Pipeline Failure - {failed_step}",
            html_content=Content("text/html", html),
        )
        SendGridAPIClient(self.api_key).send(message)
