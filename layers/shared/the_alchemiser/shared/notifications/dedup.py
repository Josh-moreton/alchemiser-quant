"""Business Unit: notifications | Status: current.

Notification deduplication and recovery tracking.

This module implements failure deduplication to prevent notification spam
and recovery tracking to send "fixed" emails when errors clear.

Dedup key format: (component, env, failed_step, error_hash)
"""

from __future__ import annotations

import hashlib
import os
import re
import time
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

import boto3
from botocore.exceptions import ClientError

from the_alchemiser.shared.logging import get_logger

if TYPE_CHECKING:
    from mypy_boto3_dynamodb import DynamoDBClient
    from mypy_boto3_dynamodb.type_defs import GetItemOutputTypeDef

logger = get_logger(__name__)


class NotificationDedupManager:
    """Manages notification deduplication and recovery tracking in DynamoDB.

    Prevents notification spam by suppressing repeat failures within a quiet period.
    Tracks recovery to send a single "fixed" email when errors clear.

    DynamoDB schema:
        PK: dedup_key (component#env#failed_step#error_hash)
        status: FAILING | RECOVERED
        first_seen_time_utc: ISO timestamp
        last_seen_time_utc: ISO timestamp
        repeat_count: int
        last_run_id: str
        last_email_sent_time_utc: ISO timestamp
        ttl: UNIX timestamp for DynamoDB TTL (90 days retention)

    """

    def __init__(
        self,
        table_name: str | None = None,
        quiet_period_minutes: int | None = None,
        region: str | None = None,
    ) -> None:
        """Initialize dedup manager.

        Args:
            table_name: DynamoDB table name (falls back to env var)
            quiet_period_minutes: Quiet period for suppressing repeats (default: 120)
            region: AWS region

        """
        self.table_name = table_name or os.environ.get("NOTIFICATION_DEDUP_TABLE_NAME")
        self.quiet_period_minutes = quiet_period_minutes or int(
            os.environ.get("DEDUP_QUIET_PERIOD_MINUTES", "120")
        )
        self.region = region or os.environ.get("AWS_REGION", "us-east-1")

        if not self.table_name:
            raise ValueError("NOTIFICATION_DEDUP_TABLE_NAME environment variable is required")

        self._client: DynamoDBClient = boto3.client("dynamodb", region_name=self.region)

    def should_send_failure_email(
        self,
        component: str,
        env: str,
        failed_step: str,
        error_details: dict[str, Any],
        run_id: str,
    ) -> bool:
        """Check if a failure email should be sent or suppressed due to dedup.

        Args:
            component: Component name (e.g., "Daily Run", "Data Lake Update")
            env: Environment (dev/staging/prod)
            failed_step: Failed step identifier
            error_details: Error details for hash generation
            run_id: Current run ID

        Returns:
            True if email should be sent, False if suppressed

        """
        dedup_key = self._generate_dedup_key(component, env, failed_step, error_details)

        try:
            # Get existing dedup record
            response: GetItemOutputTypeDef = self._client.get_item(
                TableName=self.table_name,
                Key={"PK": {"S": dedup_key}},
                ConsistentRead=True,
            )

            if "Item" not in response:
                # First occurrence - send email and create record
                self._create_dedup_record(dedup_key, run_id)
                logger.info(
                    "First failure occurrence - sending email",
                    extra={"dedup_key": dedup_key, "run_id": run_id},
                )
                return True

            # Record exists - check if within quiet period
            item = response["Item"]
            last_email_sent = item.get("last_email_sent_time_utc", {}).get("S")

            if last_email_sent:
                last_sent_dt = datetime.fromisoformat(last_email_sent)
                time_since_last = datetime.now(UTC) - last_sent_dt

                if time_since_last < timedelta(minutes=self.quiet_period_minutes):
                    # Within quiet period - suppress and increment counter
                    self._increment_repeat_count(dedup_key, run_id)
                    logger.info(
                        "Failure within quiet period - suppressing email",
                        extra={
                            "dedup_key": dedup_key,
                            "run_id": run_id,
                            "time_since_last_minutes": int(time_since_last.total_seconds() / 60),
                            "quiet_period_minutes": self.quiet_period_minutes,
                        },
                    )
                    return False

            # Outside quiet period - send email and update record
            self._update_dedup_record(dedup_key, run_id)
            logger.info(
                "Failure outside quiet period - sending email",
                extra={"dedup_key": dedup_key, "run_id": run_id},
            )
            return True

        except ClientError as e:
            # Log error but default to sending email (fail-open)
            logger.error(
                f"Dedup check failed ({e.response['Error']['Code']}): {e.response['Error']['Message']}",
                extra={"dedup_key": dedup_key, "run_id": run_id},
            )
            return True

        except Exception as e:
            # Log error but default to sending email (fail-open)
            logger.error(
                f"Dedup check failed: {e}",
                exc_info=True,
                extra={
                    "error_type": type(e).__name__,
                    "dedup_key": dedup_key,
                    "run_id": run_id,
                },
            )
            return True

    def check_recovery(
        self,
        component: str,
        env: str,
        run_id: str,
    ) -> dict[str, Any] | None:
        """Check if any previous failures for this component have recovered.

        Args:
            component: Component name
            env: Environment
            run_id: Current successful run ID

        Returns:
            Recovery info dict if recovery detected, None otherwise

        """
        # Query all dedup records for this component + env
        # In production, you'd use a GSI on component#env for efficient querying
        # For MVP, we'll scan (acceptable given low volume)

        try:
            # Scan for FAILING records matching component#env prefix
            prefix = f"{component}#{env}#"
            response = self._client.scan(
                TableName=self.table_name,
                FilterExpression="begins_with(PK, :prefix) AND #status = :failing_status",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={
                    ":prefix": {"S": prefix},
                    ":failing_status": {"S": "FAILING"},
                },
            )

            items = response.get("Items", [])

            if not items:
                # No failing records - no recovery
                return None

            # Mark all as RECOVERED and return summary
            recovery_info = {
                "component": component,
                "env": env,
                "recovering_run_id": run_id,
                "recovered_keys": [],
            }

            for item in items:
                dedup_key = item["PK"]["S"]
                first_seen = item.get("first_seen_time_utc", {}).get("S")
                last_seen = item.get("last_seen_time_utc", {}).get("S")
                repeat_count = int(item.get("repeat_count", {}).get("N", "0"))

                # Mark as RECOVERED
                self._mark_recovered(dedup_key, run_id)

                recovery_info["recovered_keys"].append(
                    {
                        "dedup_key": dedup_key,
                        "first_seen_time": first_seen,
                        "last_seen_time": last_seen,
                        "repeat_count": repeat_count,
                    }
                )

                logger.info(
                    "Recovery detected - marking as RECOVERED",
                    extra={
                        "dedup_key": dedup_key,
                        "run_id": run_id,
                        "repeat_count": repeat_count,
                    },
                )

            return recovery_info if recovery_info["recovered_keys"] else None

        except Exception as e:
            logger.error(
                f"Recovery check failed: {e}",
                exc_info=True,
                extra={
                    "error_type": type(e).__name__,
                    "component": component,
                    "env": env,
                    "run_id": run_id,
                },
            )
            return None

    def _generate_dedup_key(
        self,
        component: str,
        env: str,
        failed_step: str,
        error_details: dict[str, Any],
    ) -> str:
        """Generate dedup key from failure signature.

        Args:
            component: Component name
            env: Environment
            failed_step: Failed step
            error_details: Error details for hashing

        Returns:
            Dedup key string: component#env#failed_step#error_hash

        """
        error_hash = self._hash_error(error_details)
        return f"{component}#{env}#{failed_step}#{error_hash}"

    def _hash_error(self, error_details: dict[str, Any]) -> str:
        """Generate stable hash from error details.

        Normalizes error messages by stripping timestamps, UUIDs, and run IDs
        to detect identical errors across runs.

        Args:
            error_details: Error details dict

        Returns:
            Short hash string (first 8 chars of SHA256)

        """
        # Extract key fields for hashing
        exception_type = error_details.get("exception_type", "")
        exception_message = error_details.get("exception_message", "")

        # Normalize exception message (strip timestamps, UUIDs, run IDs)
        normalized_message = self._normalize_error_message(exception_message)

        # Build signature for hashing
        signature = f"{exception_type}|{normalized_message}"

        # Generate SHA256 hash and take first 8 chars
        hash_obj = hashlib.sha256(signature.encode("utf-8"))
        return hash_obj.hexdigest()[:8]

    def _normalize_error_message(self, message: str) -> str:
        """Normalize error message for consistent hashing.

        Args:
            message: Raw error message

        Returns:
            Normalized message with dynamic values removed

        """
        # Remove ISO timestamps
        message = re.sub(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[.\d]*Z?", "<TIMESTAMP>", message)

        # Remove UUIDs
        message = re.sub(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            "<UUID>",
            message,
            flags=re.IGNORECASE,
        )

        # Remove run IDs (short hex)
        message = re.sub(r"run_id=[0-9a-f]{6,}", "run_id=<RUN_ID>", message, flags=re.IGNORECASE)

        # Remove request IDs
        message = re.sub(
            r"request[_-]id[=:]\S+", "request_id=<REQUEST_ID>", message, flags=re.IGNORECASE
        )

        return message.strip()

    def _create_dedup_record(self, dedup_key: str, run_id: str) -> None:
        """Create new dedup record in DynamoDB.

        Args:
            dedup_key: Dedup key
            run_id: Current run ID

        """
        now_utc = datetime.now(UTC).isoformat()
        ttl = int(time.time()) + (90 * 24 * 60 * 60)  # 90 days TTL

        try:
            self._client.put_item(
                TableName=self.table_name,
                Item={
                    "PK": {"S": dedup_key},
                    "status": {"S": "FAILING"},
                    "first_seen_time_utc": {"S": now_utc},
                    "last_seen_time_utc": {"S": now_utc},
                    "repeat_count": {"N": "0"},
                    "last_run_id": {"S": run_id},
                    "last_email_sent_time_utc": {"S": now_utc},
                    "ttl": {"N": str(ttl)},
                },
            )
        except Exception as e:
            logger.error(
                f"Failed to create dedup record: {e}",
                extra={"dedup_key": dedup_key, "run_id": run_id},
            )

    def _update_dedup_record(self, dedup_key: str, run_id: str) -> None:
        """Update existing dedup record (email sent after quiet period).

        Args:
            dedup_key: Dedup key
            run_id: Current run ID

        """
        now_utc = datetime.now(UTC).isoformat()

        try:
            self._client.update_item(
                TableName=self.table_name,
                Key={"PK": {"S": dedup_key}},
                UpdateExpression=(
                    "SET last_seen_time_utc = :now, "
                    "last_run_id = :run_id, "
                    "last_email_sent_time_utc = :now"
                ),
                ExpressionAttributeValues={
                    ":now": {"S": now_utc},
                    ":run_id": {"S": run_id},
                },
            )
        except Exception as e:
            logger.error(
                f"Failed to update dedup record: {e}",
                extra={"dedup_key": dedup_key, "run_id": run_id},
            )

    def _increment_repeat_count(self, dedup_key: str, run_id: str) -> None:
        """Increment repeat count for suppressed failure.

        Args:
            dedup_key: Dedup key
            run_id: Current run ID

        """
        now_utc = datetime.now(UTC).isoformat()

        try:
            self._client.update_item(
                TableName=self.table_name,
                Key={"PK": {"S": dedup_key}},
                UpdateExpression=(
                    "SET last_seen_time_utc = :now, last_run_id = :run_id ADD repeat_count :one"
                ),
                ExpressionAttributeValues={
                    ":now": {"S": now_utc},
                    ":run_id": {"S": run_id},
                    ":one": {"N": "1"},
                },
            )
        except Exception as e:
            logger.error(
                f"Failed to increment repeat count: {e}",
                extra={"dedup_key": dedup_key, "run_id": run_id},
            )

    def _mark_recovered(self, dedup_key: str, run_id: str) -> None:
        """Mark dedup record as RECOVERED.

        Args:
            dedup_key: Dedup key
            run_id: Recovering run ID

        """
        now_utc = datetime.now(UTC).isoformat()

        try:
            self._client.update_item(
                TableName=self.table_name,
                Key={"PK": {"S": dedup_key}},
                UpdateExpression=(
                    "SET #status = :recovered, "
                    "recovered_run_id = :run_id, "
                    "recovered_time_utc = :now"
                ),
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={
                    ":recovered": {"S": "RECOVERED"},
                    ":run_id": {"S": run_id},
                    ":now": {"S": now_utc},
                },
            )
        except Exception as e:
            logger.error(
                f"Failed to mark recovered: {e}",
                extra={"dedup_key": dedup_key, "run_id": run_id},
            )


# Module-level singleton
_dedup_manager: NotificationDedupManager | None = None


def get_dedup_manager() -> NotificationDedupManager:
    """Get or create the global dedup manager instance.

    Returns:
        Singleton NotificationDedupManager instance

    """
    global _dedup_manager
    if _dedup_manager is None:
        _dedup_manager = NotificationDedupManager()
    return _dedup_manager
