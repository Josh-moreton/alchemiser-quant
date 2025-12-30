"""Business Unit: notifications | Status: current.

AWS SNS publisher for sending notifications.

This module provides SNS-based notification delivery, replacing SMTP for Lambda deployments.
SNS with email subscriptions offers simple, reliable delivery without SMTP credentials.

Note: SNS email protocol only supports plain text. HTML templates are converted to
structured plain text for delivery.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import boto3

from the_alchemiser.shared.logging import get_logger

if TYPE_CHECKING:
    from mypy_boto3_sns import SNSClient

logger = get_logger(__name__)


class SNSNotificationPublisher:
    """AWS SNS publisher for sending notifications.

    Publishes messages to an SNS topic which has email subscription(s).
    The topic must be created in template.yaml with email subscribers.

    Environment Variables:
        SNS_NOTIFICATION_TOPIC_ARN: ARN of the SNS topic for notifications
        AWS_REGION: AWS region (default: us-east-1)

    """

    def __init__(
        self,
        topic_arn: str | None = None,
        region: str | None = None,
    ) -> None:
        """Initialize SNS publisher.

        Args:
            topic_arn: ARN of SNS topic (falls back to env var)
            region: AWS region

        """
        self.topic_arn = topic_arn or os.environ.get("SNS_NOTIFICATION_TOPIC_ARN")
        self.region = region or os.environ.get("AWS_REGION", "us-east-1")
        self._client: SNSClient = boto3.client("sns", region_name=self.region)

    def publish(
        self,
        subject: str,
        message: str,
    ) -> bool:
        """Publish a notification to SNS.

        Args:
            subject: Email subject line (max 100 chars for email)
            message: Plain text message body

        Returns:
            True if published successfully, False otherwise

        """
        if not self.topic_arn:
            logger.error("SNS topic ARN not configured - set SNS_NOTIFICATION_TOPIC_ARN env var")
            return False

        try:
            # Truncate subject if needed (SNS email limit is 100 chars)
            truncated_subject = subject[:100] if len(subject) > 100 else subject

            response = self._client.publish(
                TopicArn=self.topic_arn,
                Subject=truncated_subject,
                Message=message,
            )

            message_id = response.get("MessageId", "unknown")
            logger.info(
                "Notification published to SNS",
                extra={
                    "message_id": message_id,
                    "topic_arn": self.topic_arn,
                    "subject_preview": truncated_subject[:50],
                },
            )
            return True

        except Exception as e:
            logger.error(
                f"Failed to publish to SNS: {e}",
                extra={
                    "topic_arn": self.topic_arn,
                    "error_type": type(e).__name__,
                },
            )
            return False


# Module-level singleton
_sns_publisher: SNSNotificationPublisher | None = None


def get_sns_publisher() -> SNSNotificationPublisher:
    """Get or create the global SNS publisher instance.

    Returns:
        Singleton SNSNotificationPublisher instance

    """
    global _sns_publisher
    if _sns_publisher is None:
        _sns_publisher = SNSNotificationPublisher()
    return _sns_publisher


def publish_notification(
    subject: str,
    message: str,
) -> bool:
    """Publish a notification via SNS (convenience function).

    Args:
        subject: Email subject line
        message: Plain text message body

    Returns:
        True if published successfully, False otherwise

    """
    return get_sns_publisher().publish(subject=subject, message=message)
