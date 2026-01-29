"""Business Unit: shared | Status: current.

Emergency kill switch service for options hedging.

Manages the emergency kill switch state that can halt all hedge operations.
Kill switch can be triggered manually or automatically based on failure thresholds.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Literal

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from the_alchemiser.shared.errors.exceptions import (
    DatabaseError,
    KillSwitchActiveError,
)
from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class KillSwitchState:
    """Kill switch state record."""

    is_active: bool
    trigger_reason: str | None = None
    triggered_at: datetime | None = None
    triggered_by: str | None = None  # "manual" or "automatic"
    failure_count: int = 0
    last_failure_at: datetime | None = None


class KillSwitchService:
    """Manages emergency kill switch state for hedging operations.

    The kill switch provides a circuit breaker mechanism to halt all hedge
    operations when safety conditions are violated or manual intervention
    is required.

    Features:
    - Manual activation/deactivation
    - Automatic activation on repeated failures
    - Failure tracking and threshold enforcement
    - DynamoDB-backed persistence
    """

    # Configuration constants
    KILL_SWITCH_KEY = "HEDGE_KILL_SWITCH"
    FAILURE_THRESHOLD = 3  # Activate kill switch after 3 consecutive failures
    FAILURE_WINDOW_HOURS = 24  # Count failures within 24-hour window

    def __init__(self, table_name: str | None = None) -> None:
        """Initialize kill switch service.

        Args:
            table_name: DynamoDB table name for state storage.
                       Defaults to HEDGE_KILL_SWITCH_TABLE env var.

        """
        self._table_name = table_name or os.environ.get("HEDGE_KILL_SWITCH_TABLE", "")
        if not self._table_name:
            logger.warning(
                "Kill switch table not configured, kill switch will not persist state",
                env_var="HEDGE_KILL_SWITCH_TABLE",
            )
            self._table = None
        else:
            dynamodb = boto3.resource("dynamodb")
            self._table = dynamodb.Table(self._table_name)

    def check_kill_switch(self, correlation_id: str | None = None) -> None:
        """Check if kill switch is active and raise if so.

        Args:
            correlation_id: Correlation ID for error tracing

        Raises:
            KillSwitchActiveError: If kill switch is active

        """
        state = self.get_state()

        if state.is_active:
            logger.warning(
                "Kill switch is ACTIVE - halting hedge operations",
                trigger_reason=state.trigger_reason,
                triggered_at=state.triggered_at.isoformat() if state.triggered_at else None,
                triggered_by=state.triggered_by,
                correlation_id=correlation_id,
            )
            raise KillSwitchActiveError(
                message="Emergency kill switch is active - hedge operations halted",
                trigger_reason=state.trigger_reason,
                triggered_at=state.triggered_at.isoformat() if state.triggered_at else None,
                correlation_id=correlation_id,
            )

        logger.debug("Kill switch check passed - inactive", correlation_id=correlation_id)

    def get_state(self) -> KillSwitchState:
        """Get current kill switch state.

        Returns:
            Current kill switch state

        """
        if not self._table:
            # No table configured - default to inactive
            return KillSwitchState(is_active=False)

        try:
            response = self._table.get_item(Key={"switch_id": self.KILL_SWITCH_KEY})

            if "Item" not in response:
                # No record - default to inactive
                return KillSwitchState(is_active=False)

            item = response["Item"]

            # Parse datetime fields with explicit UTC timezone
            triggered_at = None
            if item.get("triggered_at"):
                # Cast to str for type safety with DynamoDB responses
                triggered_at_str = str(item["triggered_at"])
                triggered_at = datetime.fromisoformat(triggered_at_str)
                # Ensure timezone-aware
                if triggered_at.tzinfo is None:
                    triggered_at = triggered_at.replace(tzinfo=UTC)

            last_failure_at = None
            if item.get("last_failure_at"):
                # Cast to str for type safety with DynamoDB responses
                last_failure_at_str = str(item["last_failure_at"])
                last_failure_at = datetime.fromisoformat(last_failure_at_str)
                # Ensure timezone-aware
                if last_failure_at.tzinfo is None:
                    last_failure_at = last_failure_at.replace(tzinfo=UTC)

            return KillSwitchState(
                is_active=bool(item.get("is_active", False)),
                trigger_reason=str(item["trigger_reason"]) if item.get("trigger_reason") else None,
                triggered_at=triggered_at,
                triggered_by=str(item["triggered_by"]) if item.get("triggered_by") else None,
                failure_count=int(item.get("failure_count", 0)),
                last_failure_at=last_failure_at,
            )

        except (BotoCoreError, ClientError) as e:
            logger.error(
                "Failed to read kill switch state from DynamoDB",
                table_name=self._table_name,
                error=str(e),
                exc_info=True,
            )
            # Fail closed - assume kill switch is active on read errors
            raise DatabaseError(
                message=f"Failed to read kill switch state: {e!s}",
                table_name=self._table_name,
                operation="get_item",
            ) from e

    def activate(
        self,
        reason: str,
        triggered_by: Literal["manual", "automatic"] = "manual",
    ) -> None:
        """Activate kill switch manually.

        Args:
            reason: Reason for activation
            triggered_by: Who/what triggered activation

        """
        if not self._table:
            logger.warning(
                "Kill switch table not configured - cannot persist activation",
                reason=reason,
                triggered_by=triggered_by,
            )
            return

        now = datetime.now(UTC)

        try:
            # Use update_item to preserve failure tracking fields
            self._table.update_item(
                Key={"switch_id": self.KILL_SWITCH_KEY},
                UpdateExpression="SET is_active = :active, trigger_reason = :reason, triggered_at = :at, triggered_by = :by, updated_at = :now",
                ExpressionAttributeValues={
                    ":active": True,
                    ":reason": reason,
                    ":at": now.isoformat(),
                    ":by": triggered_by,
                    ":now": now.isoformat(),
                },
            )

            logger.warning(
                "Kill switch ACTIVATED",
                reason=reason,
                triggered_by=triggered_by,
                triggered_at=now.isoformat(),
            )

        except (BotoCoreError, ClientError) as e:
            logger.error(
                "Failed to activate kill switch in DynamoDB",
                table_name=self._table_name,
                error=str(e),
                exc_info=True,
            )
            raise DatabaseError(
                message=f"Failed to activate kill switch: {e!s}",
                table_name=self._table_name,
                operation="update_item",
            ) from e

    def deactivate(self) -> None:
        """Deactivate kill switch manually."""
        if not self._table:
            logger.warning("Kill switch table not configured - cannot persist deactivation")
            return

        now = datetime.now(UTC)

        try:
            self._table.put_item(
                Item={
                    "switch_id": self.KILL_SWITCH_KEY,
                    "is_active": False,
                    "trigger_reason": None,
                    "triggered_at": None,
                    "triggered_by": None,
                    "failure_count": 0,
                    "last_failure_at": None,
                    "updated_at": now.isoformat(),
                }
            )

            logger.info("Kill switch DEACTIVATED", deactivated_at=now.isoformat())

        except (BotoCoreError, ClientError) as e:
            logger.error(
                "Failed to deactivate kill switch in DynamoDB",
                table_name=self._table_name,
                error=str(e),
                exc_info=True,
            )
            raise DatabaseError(
                message=f"Failed to deactivate kill switch: {e!s}",
                table_name=self._table_name,
                operation="put_item",
            ) from e

    def record_failure(self, failure_reason: str) -> None:
        """Record a hedge failure and auto-activate kill switch if threshold exceeded.

        Args:
            failure_reason: Reason for the failure

        """
        if not self._table:
            logger.warning(
                "Kill switch table not configured - cannot track failures",
                failure_reason=failure_reason,
            )
            return

        state = self.get_state()

        # If already active, don't increment failure count
        if state.is_active:
            logger.debug(
                "Kill switch already active, not incrementing failure count",
                failure_reason=failure_reason,
            )
            return

        now = datetime.now(UTC)

        # Check if last failure was outside the window - if so, reset counter
        window_start = now - timedelta(hours=self.FAILURE_WINDOW_HOURS)
        should_reset = (
            state.last_failure_at is None or state.last_failure_at < window_start
        )

        if should_reset:
            logger.info(
                "Last failure outside window or no previous failures, resetting counter",
                last_failure_at=state.last_failure_at.isoformat()
                if state.last_failure_at
                else None,
                window_hours=self.FAILURE_WINDOW_HOURS,
            )
            new_failure_count = 1
        else:
            new_failure_count = state.failure_count + 1

        logger.warning(
            "Hedge failure recorded",
            failure_reason=failure_reason,
            failure_count=new_failure_count,
            threshold=self.FAILURE_THRESHOLD,
            window_hours=self.FAILURE_WINDOW_HOURS,
        )

        # Check if threshold exceeded
        if new_failure_count >= self.FAILURE_THRESHOLD:
            logger.error(
                "Failure threshold exceeded - activating kill switch automatically",
                failure_count=new_failure_count,
                threshold=self.FAILURE_THRESHOLD,
                latest_failure=failure_reason,
            )
            self.activate(
                reason=f"Automatic activation after {new_failure_count} failures: {failure_reason}",
                triggered_by="automatic",
            )
        else:
            # Update failure count without activating - use update_item for atomic operation
            try:
                self._table.update_item(
                    Key={"switch_id": self.KILL_SWITCH_KEY},
                    UpdateExpression="SET failure_count = :count, last_failure_at = :last, updated_at = :now, is_active = if_not_exists(is_active, :false)",
                    ExpressionAttributeValues={
                        ":count": new_failure_count,
                        ":last": now.isoformat(),
                        ":now": now.isoformat(),
                        ":false": False,
                    },
                )
            except (BotoCoreError, ClientError) as e:
                logger.error(
                    "Failed to update failure count in DynamoDB",
                    table_name=self._table_name,
                    error=str(e),
                    exc_info=True,
                )

    def reset_failures(self) -> None:
        """Reset failure counter (typically after successful hedge execution)."""
        if not self._table:
            return

        state = self.get_state()

        # Only reset if there are failures to reset and kill switch is not active
        if state.failure_count > 0 and not state.is_active:
            now = datetime.now(UTC)

            try:
                self._table.update_item(
                    Key={"switch_id": self.KILL_SWITCH_KEY},
                    UpdateExpression="SET failure_count = :zero, last_failure_at = :null, updated_at = :now",
                    ExpressionAttributeValues={
                        ":zero": 0,
                        ":null": None,
                        ":now": now.isoformat(),
                    },
                )

                logger.info(
                    "Failure counter reset after successful hedge",
                    previous_count=state.failure_count,
                )

            except (BotoCoreError, ClientError) as e:
                logger.error(
                    "Failed to reset failure counter in DynamoDB",
                    table_name=self._table_name,
                    error=str(e),
                    exc_info=True,
                )
