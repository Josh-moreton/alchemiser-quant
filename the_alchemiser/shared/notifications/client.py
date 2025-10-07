"""Business Unit: utilities; Status: current.

Email client module for sending notifications.

This module handles SMTP operations and message sending functionality.
Replaces the `send_email_notification` function from the original email_utils.py.
"""

from __future__ import annotations

import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.reporting import EmailCredentials

from .config import EmailConfig

logger = get_logger(__name__)


class EmailClient:
    """SMTP email client for sending notifications."""

    def __init__(self) -> None:
        """Initialize email client."""
        self._config: EmailCredentials | None = None
        self._email_config = EmailConfig()

    def _get_config(self) -> EmailCredentials | None:
        """Get email configuration lazily."""
        if not self._config:
            self._config = self._email_config.get_config()
        return self._config

    def send_notification(
        self,
        subject: str,
        html_content: str,
        text_content: str | None = None,
        recipient_email: str | None = None,
        attachments: list[tuple[str, str, str]] | None = None,
    ) -> bool:
        """Send an email notification with HTML content.

        Args:
            subject: Email subject line
            html_content: HTML email content
            text_content: Plain text fallback (optional)
            recipient_email: Override recipient email (optional)
            attachments: List of (filename, content, mime_type) tuples (optional)

        Returns:
            True if sent successfully, False otherwise

        """
        email_config = self._get_config()
        if not email_config:
            logger.warning("Email configuration not available - skipping email notification")
            return False

        smtp_server = email_config.smtp_server
        smtp_port = email_config.smtp_port
        from_email = email_config.email_address
        email_password = email_config.email_password
        default_recipient = email_config.recipient_email

        recipient = recipient_email or default_recipient
        if not recipient:
            logger.error("No recipient email configured")
            return False

        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = from_email
            msg["To"] = recipient

            # Add text version if provided
            if text_content:
                text_part = MIMEText(text_content, "plain")
                msg.attach(text_part)

            # Add HTML version
            html_part = MIMEText(html_content, "html")
            msg.attach(html_part)

            # Add attachments if provided
            if attachments:
                for filename, content, mime_type in attachments:
                    attachment = MIMEBase(*mime_type.split("/"))
                    attachment.set_payload(content)
                    encoders.encode_base64(attachment)
                    attachment.add_header("Content-Disposition", f"attachment; filename={filename}")
                    msg.attach(attachment)

            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(from_email, email_password)
                server.send_message(msg)

            logger.info(f"Email notification sent successfully to {recipient}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return False

    def send_plain_text(
        self, subject: str, text_content: str, recipient_email: str | None = None
    ) -> bool:
        """Send a plain text email notification.

        Args:
            subject: Email subject line
            text_content: Plain text email content
            recipient_email: Override recipient email (optional)

        Returns:
            True if sent successfully, False otherwise

        """
        return self.send_notification(
            subject=subject,
            html_content=f"<pre>{text_content}</pre>",
            text_content=text_content,
            recipient_email=recipient_email,
        )


# Global instance for backward compatibility
_email_client = EmailClient()


def send_email_notification(
    subject: str,
    html_content: str,
    text_content: str | None = None,
    recipient_email: str | None = None,
) -> bool:
    """Send an email notification (backward compatibility function)."""
    return _email_client.send_notification(
        subject=subject,
        html_content=html_content,
        text_content=text_content,
        recipient_email=recipient_email,
    )
