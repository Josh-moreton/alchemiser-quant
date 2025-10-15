#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Amazon EventBridge implementation of EventBus.

Provides durable, async, distributed event routing with:
- Event persistence and replay via EventBridge
- Automatic retries with exponential backoff
- Dead-letter queue for failed events
- CloudWatch observability and tracing
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime

from ..logging import get_logger
from ..utils.serialization import event_to_detail_str
from .base import BaseEvent
from .bus import EventBus, HandlerType
from .errors import EventPublishError

logger = get_logger(__name__)


class EventBridgeBus(EventBus):
    """EventBus implementation using Amazon EventBridge.

    Provides durable, async, distributed event routing with:
    - Event persistence and replay
    - Automatic retries with exponential backoff
    - Dead-letter queue for failed events
    - CloudWatch observability

    This bus publishes events to EventBridge while maintaining the same
    EventBus interface for backward compatibility. Local handlers can
    optionally be enabled for testing/hybrid mode.
    """

    def __init__(
        self,
        event_bus_name: str | None = None,
        source_prefix: str = "alchemiser",
        *,
        enable_local_handlers: bool = False,
    ) -> None:
        """Initialize EventBridge bus.

        Args:
            event_bus_name: Name of the EventBridge event bus. If None, reads from
                environment variable EVENTBRIDGE_BUS_NAME or defaults to
                "alchemiser-trading-events-dev"
            source_prefix: Prefix for event sources (e.g., "alchemiser.strategy")
            enable_local_handlers: If True, keep in-memory handlers for testing

        """
        super().__init__()
        self.event_bus_name = event_bus_name or os.environ.get(
            "EVENTBRIDGE_BUS_NAME", "alchemiser-trading-events-dev"
        )
        self.source_prefix = source_prefix
        self.enable_local_handlers = enable_local_handlers

        # Initialize EventBridge client (lazy import to avoid runtime dependency in tests)
        self._events_client: object | None = None

        # Track EventBridge-specific events (not inherited from parent)
        self._eventbridge_count: int = 0

        logger.info(
            "EventBridgeBus initialized",
            event_bus_name=self.event_bus_name,
            source_prefix=source_prefix,
            enable_local_handlers=enable_local_handlers,
        )

    @property
    def events_client(self) -> object:
        """Get or create EventBridge client (lazy initialization).

        Returns:
            EventBridge client instance

        """
        if self._events_client is None:
            import boto3

            self._events_client = boto3.client("events")
        return self._events_client

    def publish(self, event: BaseEvent) -> None:
        """Publish event to EventBridge.

        Events are serialized to JSON and published to EventBridge with:
        - Source: {source_prefix}.{source_module} (e.g., "alchemiser.strategy")
        - DetailType: event.event_type (e.g., "SignalGenerated")
        - Detail: JSON-serialized event data

        Errors are raised to allow upstream retry/circuit breaker logic to handle failures.

        Args:
            event: Event to publish

        Raises:
            EventPublishError: When EventBridge publish fails or returns errors

        """
        try:
            # Determine source based on module
            source = f"{self.source_prefix}.{event.source_module}"

            # Serialize event to JSON string using canonical serialization
            detail_str = event_to_detail_str(event)

            # Build EventBridge entry with proper type annotations
            resources: list[str] = []
            if event.correlation_id:
                resources.append(f"correlation:{event.correlation_id}")
            if event.causation_id:
                resources.append(f"causation:{event.causation_id}")

            entry: dict[str, object] = {
                "Time": datetime.now(UTC),
                "Source": source,
                "DetailType": event.event_type,
                "Detail": detail_str,
                "EventBusName": self.event_bus_name,
                "Resources": resources,
            }

            # Publish to EventBridge
            # Type ignore needed because boto3 client returns untyped dict response
            response = self.events_client.put_events(Entries=[entry])  # type: ignore[attr-defined]

            # Check for failures
            if response.get("FailedEntryCount", 0) > 0:
                failed = response["Entries"][0]
                error_code = failed.get("ErrorCode", "Unknown")
                error_message = failed.get("ErrorMessage", "No error message provided")

                logger.error(
                    "Failed to publish event to EventBridge",
                    event_type=event.event_type,
                    error_code=error_code,
                    error_message=error_message,
                    event_id=event.event_id,
                    correlation_id=event.correlation_id,
                )

                raise EventPublishError(
                    f"{error_code}: {error_message}",
                    event_id=event.event_id,
                    correlation_id=event.correlation_id,
                    error_code=error_code,
                )
            # Only increment counter on successful publish
            self._eventbridge_count += 1
            logger.info(
                "Event published to EventBridge",
                event_type=event.event_type,
                event_id=event.event_id,
                correlation_id=event.correlation_id,
                source=source,
                event_bus_name=self.event_bus_name,
            )

            # Also trigger local handlers if enabled (for testing/hybrid mode)
            if self.enable_local_handlers:
                # Call parent publish to invoke local handlers
                super().publish(event)

        except EventPublishError:
            # Re-raise EventPublishError as-is
            raise
        except Exception as e:
            # Import ClientError dynamically to avoid boto3 dependency at module level
            try:
                from botocore.exceptions import ClientError

                if isinstance(e, ClientError):
                    logger.error(
                        "EventBridge client error",
                        error=str(e),
                        error_type=type(e).__name__,
                        event_type=event.event_type,
                        event_id=event.event_id,
                        correlation_id=event.correlation_id,
                        exc_info=True,
                    )
                    # Re-raise ClientError as-is for AWS SDK retry logic
                    raise
            except ImportError:
                pass

            # Wrap unexpected errors as EventPublishError
            logger.error(
                "Unexpected error publishing to EventBridge",
                error=str(e),
                error_type=type(e).__name__,
                event_type=event.event_type,
                event_id=event.event_id,
                correlation_id=event.correlation_id,
                exc_info=True,
            )
            raise EventPublishError(
                f"Unexpected error: {e!s}",
                event_id=event.event_id,
                correlation_id=event.correlation_id,
            ) from e

    def subscribe(self, event_type: str, handler: HandlerType) -> None:
        """Subscribe handler to event type.

        Note: With EventBridge, subscriptions are managed via CloudFormation
        EventRules, not programmatically. This method is kept for local testing
        when enable_local_handlers=True.

        Args:
            event_type: Type of event to subscribe to
            handler: Handler instance

        """
        if self.enable_local_handlers:
            super().subscribe(event_type, handler)
            logger.debug(
                "Local handler subscribed (EventBridge rules should also be configured)",
                event_type=event_type,
                handler=type(handler).__name__,
            )
        else:
            logger.warning(
                "subscribe() called on EventBridgeBus - use CloudFormation EventRules instead",
                event_type=event_type,
                handler=type(handler).__name__,
            )

    def get_event_count(self) -> int:
        """Get total count of events published to EventBridge.

        Returns:
            Number of events successfully published to EventBridge.
            Does not include local handler invocations.

        """
        return self._eventbridge_count

    def set_client_for_testing(self, mock_client: object) -> None:
        """Set a mock EventBridge client for testing.

        This method allows dependency injection of a mock boto3 client during tests,
        avoiding actual AWS API calls. Intended for use in test fixtures only.

        Args:
            mock_client: Mock EventBridge client to use for testing

        """
        self._events_client = mock_client
        logger.debug("EventBridge client replaced with mock for testing")
