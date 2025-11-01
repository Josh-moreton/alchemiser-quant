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
from typing import Any, Protocol

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.notifications import EmailCredentials

from .config import EmailConfig

logger = get_logger(__name__)


class S3ClientProtocol(Protocol):
    """Protocol defining the S3 client interface used by EmailClient.

    This protocol defines the minimal interface needed from boto3 S3 client
    for email attachment functionality, improving type safety without
    requiring a hard dependency on boto3 types.
    """

    def get_object(
        self, *, Bucket: str, Key: str, ExpectedBucketOwner: str | None = None
    ) -> dict[str, Any]:
        """Get an object from S3.

        Args:
            Bucket: S3 bucket name
            Key: S3 object key
            ExpectedBucketOwner: AWS account ID that owns the bucket (optional)

        Returns:
            Response dictionary containing Body and metadata

        """
        ...


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

    def _create_base_message(
        self,
        subject: str,
        from_email: str,
        recipient: str,
        html_content: str,
        text_content: str | None,
    ) -> MIMEMultipart:
        """Create base MIME message with text and HTML content.

        Args:
            subject: Email subject line
            from_email: Sender email address
            recipient: Recipient email address
            html_content: HTML email content
            text_content: Plain text fallback (optional)

        Returns:
            MIMEMultipart message with headers and content

        """
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = from_email
        msg["To"] = recipient

        if text_content:
            text_part = MIMEText(text_content, "plain")
            msg.attach(text_part)

        html_part = MIMEText(html_content, "html")
        msg.attach(html_part)

        return msg

    def _attach_local_files(
        self, msg: MIMEMultipart, attachments: list[tuple[str, bytes, str]]
    ) -> None:
        """Attach local file attachments to message.

        Args:
            msg: MIME message to attach files to
            attachments: List of (filename, content_bytes, mime_type) tuples

        """
        for filename, content_bytes, mime_type in attachments:
            attachment = MIMEBase(*mime_type.split("/"))
            attachment.set_payload(content_bytes)
            encoders.encode_base64(attachment)
            attachment.add_header("Content-Disposition", f"attachment; filename={filename}")
            msg.attach(attachment)

    def _parse_s3_uri(self, s3_uri: str) -> tuple[str, str] | None:
        """Parse S3 URI into bucket and key.

        Args:
            s3_uri: S3 URI in format s3://bucket/key

        Returns:
            Tuple of (bucket, key) or None if invalid

        """
        if not s3_uri.startswith("s3://"):
            logger.warning(f"Invalid S3 URI format: {s3_uri}")
            return None

        uri_parts = s3_uri[5:].split("/", 1)
        if len(uri_parts) != 2:
            logger.warning(f"Invalid S3 URI format: {s3_uri}")
            return None

        return uri_parts[0], uri_parts[1]

    def _download_s3_file(
        self,
        s3_client: S3ClientProtocol,
        bucket: str,
        key: str,
        s3_uri: str,
        expected_bucket_owner: str | None,
    ) -> bytes | None:
        """Download file from S3.

        Args:
            s3_client: Boto3 S3 client (or compatible implementation)
            bucket: S3 bucket name
            key: S3 object key
            s3_uri: Full S3 URI for logging
            expected_bucket_owner: AWS account ID that owns the bucket (optional)

        Returns:
            File content bytes or None if download fails

        """
        from botocore.exceptions import ClientError

        try:
            logger.debug(f"Downloading attachment from S3: {s3_uri}")

            # Call S3 with ExpectedBucketOwner parameter for security if provided
            if expected_bucket_owner:
                response = s3_client.get_object(
                    Bucket=bucket, Key=key, ExpectedBucketOwner=expected_bucket_owner
                )
            else:
                response = s3_client.get_object(Bucket=bucket, Key=key)

            content: bytes = response["Body"].read()
            return content

        except ClientError as e:
            logger.error(f"Failed to download S3 attachment {s3_uri}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error processing S3 attachment {s3_uri}: {e}")
            return None

    def _attach_s3_files(
        self,
        msg: MIMEMultipart,
        s3_attachments: list[tuple[str, str, str]],
        expected_bucket_owner: str | None,
    ) -> None:
        """Download and attach S3 files to message.

        Args:
            msg: MIME message to attach files to
            s3_attachments: List of (filename, s3_uri, mime_type) tuples
            expected_bucket_owner: AWS account ID that owns the bucket (optional)

        """
        import boto3

        s3_client = boto3.client("s3")

        for filename, s3_uri, mime_type in s3_attachments:
            parsed = self._parse_s3_uri(s3_uri)
            if not parsed:
                continue

            bucket, key = parsed
            content_bytes = self._download_s3_file(
                s3_client, bucket, key, s3_uri, expected_bucket_owner
            )

            if content_bytes is None:
                continue

            attachment = MIMEBase(*mime_type.split("/"))
            attachment.set_payload(content_bytes)
            encoders.encode_base64(attachment)
            attachment.add_header("Content-Disposition", f"attachment; filename={filename}")
            msg.attach(attachment)

            logger.debug(f"Successfully attached {filename} from S3")

    def send_notification(
        self,
        subject: str,
        html_content: str,
        text_content: str | None = None,
        recipient_email: str | None = None,
        attachments: list[tuple[str, bytes, str]] | None = None,
        s3_attachments: list[tuple[str, str, str]] | None = None,
        expected_bucket_owner: str | None = None,
    ) -> bool:
        """Send an email notification with HTML content.

        Args:
            subject: Email subject line
            html_content: HTML email content
            text_content: Plain text fallback (optional)
            recipient_email: Override recipient email (optional)
            attachments: List of (filename, content_bytes, mime_type) tuples (optional)
            s3_attachments: List of (filename, s3_uri, mime_type) tuples to download and attach (optional)
            expected_bucket_owner: AWS account ID that owns the S3 bucket (optional, recommended for security)

        Returns:
            True if sent successfully, False otherwise

        """
        email_config = self._get_config()
        if not email_config:
            logger.warning("Email configuration not available - skipping email notification")
            return False

        recipient = recipient_email or email_config.recipient_email
        if not recipient:
            logger.error("No recipient email configured")
            return False

        try:
            msg = self._create_base_message(
                subject, email_config.email_address, recipient, html_content, text_content
            )

            if attachments:
                self._attach_local_files(msg, attachments)

            if s3_attachments:
                self._attach_s3_files(msg, s3_attachments, expected_bucket_owner)

            # Send email
            with smtplib.SMTP(email_config.smtp_server, email_config.smtp_port) as server:
                server.starttls()
                server.login(email_config.email_address, email_config.email_password)
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
    s3_attachments: list[tuple[str, str, str]] | None = None,
    expected_bucket_owner: str | None = None,
) -> bool:
    """Send an email notification (backward compatibility function).

    Args:
        subject: Email subject line
        html_content: HTML email content
        text_content: Plain text fallback (optional)
        recipient_email: Override recipient email (optional)
        s3_attachments: List of (filename, s3_uri, mime_type) tuples (optional)
        expected_bucket_owner: AWS account ID that owns the S3 bucket (optional, recommended for security)

    Returns:
        True if sent successfully, False otherwise

    """
    return _email_client.send_notification(
        subject=subject,
        html_content=html_content,
        text_content=text_content,
        recipient_email=recipient_email,
        s3_attachments=s3_attachments,
        expected_bucket_owner=expected_bucket_owner,
    )
