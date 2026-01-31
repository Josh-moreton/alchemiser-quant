"""Business Unit: shared | Status: current.

EventBridge publisher for domain events.

Provides a publisher that sends domain events to AWS EventBridge for
decoupled, reliable event-driven architecture between microservices.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

import boto3

from the_alchemiser.shared.logging import get_logger

if TYPE_CHECKING:
    from mypy_boto3_events import EventBridgeClient
    from mypy_boto3_events.type_defs import PutEventsResponseTypeDef

    from the_alchemiser.shared.events.base import BaseEvent

logger = get_logger(__name__)

# Event source prefix for all alchemiser events
EVENT_SOURCE_PREFIX = "alchemiser"

# Mapping from internal event types to EventBridge detail-types
# For WorkflowFailed, source is determined dynamically from the event's source_module
EVENT_TYPE_TO_DETAIL_TYPE: dict[str, tuple[str, str]] = {
    "SignalGenerated": ("strategy", "SignalGenerated"),
    "PartialSignalGenerated": ("strategy", "PartialSignalGenerated"),
    "RebalancePlanned": ("portfolio", "RebalancePlanned"),
    "TradeExecuted": ("execution", "TradeExecuted"),
    "AllTradesCompleted": ("trade_aggregator", "AllTradesCompleted"),  # From TradeAggregator
    "WorkflowCompleted": ("execution", "WorkflowCompleted"),  # Terminal success event
    "WorkflowFailed": ("dynamic", "WorkflowFailed"),  # Source from source_module
    "TradingNotificationRequested": ("notifications", "TradingNotificationRequested"),
    "ErrorNotificationRequested": ("notifications", "ErrorNotificationRequested"),
    "DataLakeUpdateCompleted": ("data", "DataLakeUpdateCompleted"),  # From Data Lambda
    "ScheduleCreated": ("coordinator", "ScheduleCreated"),  # From Schedule Manager
    "HedgeEvaluationCompleted": ("hedge", "HedgeEvaluationCompleted"),
    "HedgeExecuted": ("hedge", "HedgeExecuted"),
    "AllHedgesCompleted": ("hedge", "AllHedgesCompleted"),
    "HedgeRollTriggered": ("hedge", "HedgeRollTriggered"),
}

# Mapping from source_module prefix to EventBridge source suffix
# Used for dynamic source resolution (e.g., WorkflowFailed events)
SOURCE_MODULE_TO_SOURCE: dict[str, str] = {
    "strategy": "strategy",
    "portfolio": "portfolio",
    "execution": "execution",
    "notifications": "notifications",
    "trade": "trade",  # Trade aggregator
    "hedge": "hedge",
}


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal types for EventBridge."""

    def default(self, obj: Any) -> Any:  # noqa: ANN401
        """Convert Decimal to string for JSON serialization."""
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        # Exception instances - serialize to dict with type and message
        if isinstance(obj, Exception):
            result: dict[str, Any] = {
                "type": type(obj).__name__,
                "message": str(obj),
            }
            # Include context if available (e.g., AlchemiserError subclasses)
            if hasattr(obj, "context") and obj.context:
                result["context"] = obj.context
            return result
        return super().default(obj)


class EventBridgePublisher:
    """Publisher that sends domain events to AWS EventBridge.

    This replaces HTTP-based communication between microservices with
    native AWS EventBridge pub/sub, providing:
    - Decoupled services (no endpoint URLs needed)
    - Built-in retry and dead-letter support
    - Native AWS integration and observability
    """

    def __init__(
        self,
        event_bus_name: str | None = None,
        region: str | None = None,
    ) -> None:
        """Initialize the EventBridge publisher.

        Args:
            event_bus_name: Name of the EventBridge event bus. If None,
                uses EVENT_BUS_NAME environment variable.
            region: AWS region. If None, uses AWS_REGION env var.

        """
        self._event_bus_name = event_bus_name or os.environ.get("EVENT_BUS_NAME", "default")
        self._region = region or os.environ.get("AWS_REGION", "us-east-1")
        self._client: EventBridgeClient = boto3.client("events", region_name=self._region)
        logger.info(
            "EventBridge publisher initialized",
            extra={"event_bus": self._event_bus_name, "region": self._region},
        )

    def publish(self, event: BaseEvent) -> PutEventsResponseTypeDef:
        """Publish a domain event to EventBridge.

        Args:
            event: The domain event to publish. Must have event_type attribute.

        Returns:
            The EventBridge PutEvents response.

        Raises:
            ValueError: If the event type is not mapped to a detail-type.
            RuntimeError: If EventBridge returns failed entries.

        """
        event_type = event.event_type
        if event_type not in EVENT_TYPE_TO_DETAIL_TYPE:
            raise ValueError(
                f"Unknown event type '{event_type}'. "
                f"Must be one of: {list(EVENT_TYPE_TO_DETAIL_TYPE.keys())}"
            )

        source_suffix, detail_type = EVENT_TYPE_TO_DETAIL_TYPE[event_type]

        # Handle dynamic source for WorkflowFailed (uses source_module to determine origin)
        if source_suffix == "dynamic":
            source_module = getattr(event, "source_module", "unknown")
            # Extract module prefix (e.g., "strategy_v2" -> "strategy")
            module_prefix = source_module.split("_")[0] if source_module else "unknown"
            source_suffix = SOURCE_MODULE_TO_SOURCE.get(module_prefix, module_prefix)

        source = f"{EVENT_SOURCE_PREFIX}.{source_suffix}"

        # Serialize event to JSON using model_dump for Pydantic models
        event_data = event.model_dump(mode="json")

        logger.info(
            "Publishing event to EventBridge",
            extra={
                "event_type": event_type,
                "detail_type": detail_type,
                "source": source,
                "event_bus": self._event_bus_name,
                "correlation_id": event.correlation_id,
                "event_id": event.event_id,
            },
        )

        response = self._client.put_events(
            Entries=[
                {
                    "Source": source,
                    "DetailType": detail_type,
                    "Detail": json.dumps(event_data, cls=DecimalEncoder),
                    "EventBusName": self._event_bus_name,
                }
            ]
        )

        # Check for failures
        if response.get("FailedEntryCount", 0) > 0:
            failed_entries = response.get("Entries", [])
            error_msg = "; ".join(
                f"{e.get('ErrorCode', 'Unknown')}: {e.get('ErrorMessage', 'No message')}"
                for e in failed_entries
                if e.get("ErrorCode")
            )
            logger.error(
                "Failed to publish event to EventBridge",
                extra={
                    "event_type": event_type,
                    "correlation_id": event.correlation_id,
                    "failed_count": response["FailedEntryCount"],
                    "errors": error_msg,
                },
            )
            raise RuntimeError(f"EventBridge publish failed: {error_msg}")

        logger.info(
            "Event published to EventBridge successfully",
            extra={
                "event_type": event_type,
                "correlation_id": event.correlation_id,
                "event_id": response["Entries"][0].get("EventId"),
            },
        )

        return response


def unwrap_eventbridge_event(event: dict[str, Any]) -> dict[str, Any]:
    """Unwrap an EventBridge event to extract the domain event detail.

    EventBridge wraps events in a standard envelope:
    {
        "version": "0",
        "id": "...",
        "detail-type": "SignalGenerated",
        "source": "alchemiser.strategy",
        "time": "...",
        "region": "...",
        "detail": { ... actual domain event ... }
    }

    Args:
        event: The raw EventBridge event envelope.

    Returns:
        The domain event data from the 'detail' field.

    """
    if "detail" in event:
        logger.debug(
            "Unwrapping EventBridge event",
            extra={
                "detail_type": event.get("detail-type"),
                "source": event.get("source"),
                "eventbridge_id": event.get("id"),
            },
        )
        detail: dict[str, Any] = event["detail"]
        return detail
    # If no 'detail' field, assume it's already unwrapped or direct invocation
    return event


def unwrap_sqs_event(event: dict[str, Any]) -> list[dict[str, Any]]:
    """Unwrap an SQS event to extract domain event(s) from message bodies.

    SQS events contain a Records array:
    {
        "Records": [
            {
                "messageId": "...",
                "body": "{ ... JSON string of EventBridge event ... }",
                ...
            }
        ]
    }

    When EventBridge routes to SQS, the message body contains the
    full EventBridge event envelope.

    Args:
        event: The raw SQS event.

    Returns:
        List of domain event data extracted from SQS message bodies.

    """
    records = event.get("Records", [])
    domain_events = []

    for record in records:
        message_id = record.get("messageId", "unknown")
        body = record.get("body", "{}")

        try:
            # Parse the message body (could be EventBridge envelope or direct)
            parsed_body = json.loads(body) if isinstance(body, str) else body

            # If it's an EventBridge envelope, unwrap it
            if "detail" in parsed_body:
                domain_event = parsed_body["detail"]
                logger.debug(
                    "Unwrapped SQS message (EventBridge envelope)",
                    extra={
                        "message_id": message_id,
                        "detail_type": parsed_body.get("detail-type"),
                    },
                )
            else:
                domain_event = parsed_body
                logger.debug(
                    "Unwrapped SQS message (direct)",
                    extra={"message_id": message_id},
                )

            domain_events.append(domain_event)

        except json.JSONDecodeError as e:
            logger.error(
                "Failed to parse SQS message body",
                extra={"message_id": message_id, "error": str(e)},
            )
            raise

    return domain_events


# Singleton instance for convenience
_publisher: EventBridgePublisher | None = None


def get_eventbridge_publisher() -> EventBridgePublisher:
    """Get the singleton EventBridge publisher instance.

    Returns:
        The EventBridgePublisher singleton.

    """
    global _publisher
    if _publisher is None:
        _publisher = EventBridgePublisher()
    return _publisher


def publish_to_eventbridge(event: BaseEvent) -> PutEventsResponseTypeDef:
    """Publish an event to EventBridge.

    Args:
        event: The domain event to publish.

    Returns:
        The EventBridge PutEvents response.

    """
    return get_eventbridge_publisher().publish(event)
