"""Business Unit: notifications | Status: current.

AWS SES publisher for sending email notifications.

This module provides SES-based notification delivery with HTML + plain text templates,
environment-safe routing, retry logic, and structured logging.

Replaces SNS email sending for better control over formatting, branding, and deliverability.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import boto3
from botocore.exceptions import ClientError

from the_alchemiser.shared.logging import get_logger

if TYPE_CHECKING:
    from mypy_boto3_ses import SESClient

logger = get_logger(__name__)


class SESEmailPublisher:
    """AWS SES publisher for sending email notifications.

    Sends HTML + plain text emails via Amazon SES with environment-safe routing.
    Each environment gets its own NOTIFICATION_EMAIL configured via CI/CD.

    Environment Variables:
        SES_FROM_ADDRESS: Email sender address (required)
        SES_FROM_NAME: Display name for email sender (optional, e.g., "The Alchemiser")
        SES_REPLY_TO_ADDRESS: Reply-to address (optional)
        SES_REGION: AWS region for SES (default: us-east-1)
        SES_CONFIGURATION_SET: SES configuration set for tracking (optional)
        NOTIFICATION_EMAIL: Recipient email address(es), set per-environment via CI/CD
        NOTIFICATIONS_OVERRIDE_TO: Force recipient override (comma-separated, optional)
        APP__STAGE: Deployment stage (dev/staging/prod)

    """

    def __init__(
        self,
        from_address: str | None = None,
        from_name: str | None = None,
        reply_to_address: str | None = None,
        region: str | None = None,
        configuration_set: str | None = None,
    ) -> None:
        """Initialize SES publisher.

        Args:
            from_address: Sender email address (falls back to env var)
            from_name: Display name for sender (falls back to env var)
            reply_to_address: Reply-to address (falls back to env var)
            region: AWS region for SES
            configuration_set: SES configuration set name

        """
        _from_address = from_address or os.environ.get("SES_FROM_ADDRESS")
        if not _from_address:
            raise ValueError("SES_FROM_ADDRESS environment variable is required")
        self.from_address: str = _from_address

        self.from_name = from_name or os.environ.get("SES_FROM_NAME")
        self.reply_to_address = reply_to_address or os.environ.get("SES_REPLY_TO_ADDRESS")
        self.region = region or os.environ.get("SES_REGION", "us-east-1")
        self.configuration_set = configuration_set or os.environ.get("SES_CONFIGURATION_SET")
        self.stage = os.environ.get("APP__STAGE", "dev")

        # Environment-safe routing
        self.allow_real_emails = os.environ.get("ALLOW_REAL_EMAILS", "false").lower() == "true"
        self.override_to = os.environ.get("NOTIFICATIONS_OVERRIDE_TO")

        self._client: SESClient = boto3.client("ses", region_name=self.region)

    def send_email(
        self,
        to_addresses: list[str],
        subject: str,
        html_body: str,
        text_body: str,
        cc_addresses: list[str] | None = None,
        bcc_addresses: list[str] | None = None,
    ) -> dict[str, str]:
        """Send an email via SES.

        Args:
            to_addresses: List of recipient email addresses
            subject: Email subject line
            html_body: HTML version of email body
            text_body: Plain text version of email body
            cc_addresses: Optional CC recipients
            bcc_addresses: Optional BCC recipients

        Returns:
            dict with 'message_id' on success, or 'error' on failure

        Raises:
            ValueError: If required fields are missing

        """
        if not to_addresses:
            raise ValueError("At least one recipient email address is required")

        if not subject or not html_body or not text_body:
            raise ValueError("Subject, html_body, and text_body are required")

        # Apply environment-safe routing
        actual_to, routing_note = self._apply_routing_safety(to_addresses)

        # Routing note is logged but no longer injected into email body
        # Users know which environment they're in from the subject line

        # Build SES message
        destination = {"ToAddresses": actual_to}
        if cc_addresses:
            destination["CcAddresses"] = cc_addresses
        if bcc_addresses:
            destination["BccAddresses"] = bcc_addresses

        message = {
            "Subject": {"Data": subject, "Charset": "UTF-8"},
            "Body": {
                "Text": {"Data": text_body, "Charset": "UTF-8"},
                "Html": {"Data": html_body, "Charset": "UTF-8"},
            },
        }

        # Build SendEmail request
        send_params = {
            "Source": self._format_source(),
            "Destination": destination,
            "Message": message,
        }

        if self.reply_to_address:
            send_params["ReplyToAddresses"] = [self.reply_to_address]

        if self.configuration_set:
            send_params["ConfigurationSetName"] = self.configuration_set

        try:
            response = self._client.send_email(**send_params)
            message_id = response.get("MessageId", "unknown")

            logger.info(
                "Email sent via SES",
                extra={
                    "message_id": message_id,
                    "to_addresses": actual_to,
                    "subject_preview": subject[:100],
                    "routing_override": routing_note is not None,
                    "stage": self.stage,
                },
            )

            return {"message_id": message_id, "status": "sent"}

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]

            logger.error(
                f"SES send failed ({error_code}): {error_message}",
                extra={
                    "error_code": error_code,
                    "error_message": error_message,
                    "to_addresses": actual_to,
                    "subject_preview": subject[:100],
                    "stage": self.stage,
                },
            )

            return {"error": error_code, "message": error_message, "status": "failed"}

        except Exception as e:
            logger.error(
                f"Failed to send email via SES: {e}",
                exc_info=True,
                extra={
                    "error_type": type(e).__name__,
                    "to_addresses": actual_to,
                    "subject_preview": subject[:100],
                    "stage": self.stage,
                },
            )

            return {"error": type(e).__name__, "message": str(e), "status": "failed"}

    def _apply_routing_safety(self, to_addresses: list[str]) -> tuple[list[str], str | None]:
        """Apply environment-safe routing.

        Each environment has its own NOTIFICATION_EMAIL configured via CI/CD,
        so the passed-in addresses are already correct for the environment.
        This method allows optional override for testing.

        Args:
            to_addresses: Recipient addresses (already environment-specific)

        Returns:
            Tuple of (actual_recipients, routing_note)
            routing_note is None if no override applied

        """
        # Override configured - use it (for testing)
        if self.override_to:
            override_addresses = [addr.strip() for addr in self.override_to.split(",")]
            routing_note = (
                f"NOTE: Recipient override active (stage={self.stage}). "
                f"Original recipients suppressed: {', '.join(to_addresses)}"
            )
            logger.info(
                "Applying recipient override",
                extra={
                    "stage": self.stage,
                    "original_recipients": to_addresses,
                    "override_recipients": override_addresses,
                },
            )
            return override_addresses, routing_note

        # Use passed-in addresses (already correct for environment via CI/CD)
        return to_addresses, None

    def _format_source(self) -> str:
        """Format Source field for SES using RFC 5322 format.

        Returns:
            RFC 5322 formatted source if from_name is set, otherwise bare email

        Examples:
            With name: "The Alchemiser" <noreply@mail.octarine.capital>
            Without name: noreply@mail.octarine.capital

        """
        if self.from_name:
            # RFC 5322: "Display Name" <email@domain.com>
            return f'"{self.from_name}" <{self.from_address}>'
        return self.from_address


# Module-level singleton
_ses_publisher: SESEmailPublisher | None = None


def get_ses_publisher() -> SESEmailPublisher:
    """Get or create the global SES publisher instance.

    Returns:
        Singleton SESEmailPublisher instance

    """
    global _ses_publisher
    if _ses_publisher is None:
        _ses_publisher = SESEmailPublisher()
    return _ses_publisher


def send_email(
    to_addresses: list[str],
    subject: str,
    html_body: str,
    text_body: str,
    cc_addresses: list[str] | None = None,
    bcc_addresses: list[str] | None = None,
) -> dict[str, str]:
    """Send an email via SES (convenience function).

    Args:
        to_addresses: List of recipient email addresses
        subject: Email subject line
        html_body: HTML version of email body
        text_body: Plain text version of email body
        cc_addresses: Optional CC recipients
        bcc_addresses: Optional BCC recipients

    Returns:
        dict with 'message_id' on success, or 'error' on failure

    """
    return get_ses_publisher().send_email(
        to_addresses=to_addresses,
        subject=subject,
        html_body=html_body,
        text_body=text_body,
        cc_addresses=cc_addresses,
        bcc_addresses=bcc_addresses,
    )
