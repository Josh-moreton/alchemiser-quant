"""Business Unit: notifications | Status: current.

Lambda handler for event-driven notifications microservice.

Consumes TradeExecuted events from EventBridge and sends email notifications
using the NotificationService.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import uuid4

from the_alchemiser.notifications_v2.service import NotificationService
from the_alchemiser.shared.config.container import ApplicationContainer
from the_alchemiser.shared.events.eventbridge_publisher import unwrap_eventbridge_event
from the_alchemiser.shared.events.schemas import TradingNotificationRequested
from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Handle TradeExecuted events and send notifications.

    This Lambda is triggered by EventBridge when TradeExecuted events are published.
    It builds a TradingNotificationRequested event and processes it through the
    NotificationService to send emails.

    Args:
        event: EventBridge event containing TradeExecuted details
        context: Lambda context

    Returns:
        Response with status code and message

    """
    correlation_id = str(uuid4())

    try:
        # Unwrap EventBridge envelope to get the actual event payload
        unwrapped = unwrap_eventbridge_event(event)
        detail = unwrapped.get("detail", {})
        detail_type = unwrapped.get("detail-type", "")
        source = unwrapped.get("source", "")

        # Extract correlation_id from event if available
        correlation_id = detail.get("correlation_id", correlation_id)

        logger.info(
            "Notifications Lambda invoked",
            extra={
                "correlation_id": correlation_id,
                "detail_type": detail_type,
                "source": source,
            },
        )

        # Only process TradeExecuted events
        if detail_type != "TradeExecuted":
            logger.debug(
                f"Ignoring non-TradeExecuted event: {detail_type}",
                extra={"correlation_id": correlation_id},
            )
            return {
                "statusCode": 200,
                "body": f"Ignored event type: {detail_type}",
            }

        # Create ApplicationContainer for dependencies
        logger.info("Creating ApplicationContainer", extra={"environment": "production"})
        container = ApplicationContainer()
        logger.info(
            "ApplicationContainer created successfully", extra={"environment": "production"}
        )

        # Build TradingNotificationRequested from TradeExecuted event
        notification_event = _build_trading_notification(detail, correlation_id, container)

        # Create NotificationService and process the event
        notification_service = NotificationService(container)
        notification_service.handle_event(notification_event)

        logger.info(
            "Trading notification processed successfully",
            extra={
                "correlation_id": correlation_id,
                "trading_success": notification_event.trading_success,
                "orders_placed": notification_event.orders_placed,
            },
        )

        return {
            "statusCode": 200,
            "body": f"Notification sent for correlation_id: {correlation_id}",
        }

    except Exception as e:
        logger.error(
            f"Notifications Lambda failed: {e}",
            exc_info=True,
            extra={
                "correlation_id": correlation_id,
                "error_type": type(e).__name__,
            },
        )
        # Don't raise - notifications shouldn't fail the workflow
        return {
            "statusCode": 500,
            "body": f"Notification failed: {e!s}",
        }


def _build_trading_notification(
    trade_executed_detail: dict[str, Any],
    correlation_id: str,
    container: ApplicationContainer,
) -> TradingNotificationRequested:
    """Build TradingNotificationRequested from TradeExecuted event detail.

    Args:
        trade_executed_detail: The detail payload from TradeExecuted event
        correlation_id: Correlation ID for tracing
        container: Application container for config access

    Returns:
        TradingNotificationRequested event ready for processing

    """
    # Determine trading mode from container config
    mode_str = "LIVE" if not container.config.paper_trading() else "PAPER"

    # Extract fields from TradeExecuted event
    orders_placed = trade_executed_detail.get("orders_placed", 0)
    orders_succeeded = trade_executed_detail.get("orders_succeeded", 0)
    trading_success = orders_succeeded > 0 and orders_succeeded == orders_placed

    # Build execution data for email template
    execution_data: dict[str, Any] = {
        "orders_executed": trade_executed_detail.get("orders_executed", []),
        "execution_summary": trade_executed_detail.get("execution_summary", {}),
    }

    # Calculate total trade value from execution summary or orders
    total_trade_value = Decimal(str(_extract_trade_value(trade_executed_detail)))

    # Extract error details if present
    error_message = trade_executed_detail.get("error_message")
    error_code = trade_executed_detail.get("error_code")

    return TradingNotificationRequested(
        correlation_id=correlation_id,
        causation_id=trade_executed_detail.get("event_id", correlation_id),
        event_id=f"trading-notification-{uuid4()}",
        timestamp=datetime.now(UTC),
        source_module="notifications_v2.lambda_handler",
        source_component="NotificationsLambda",
        trading_success=trading_success,
        trading_mode=mode_str,
        orders_placed=orders_placed,
        orders_succeeded=orders_succeeded,
        total_trade_value=total_trade_value,
        execution_data=execution_data,
        error_message=error_message,
        error_code=error_code,
    )


def _extract_trade_value(trade_executed_detail: dict[str, Any]) -> float:
    """Extract total trade value from TradeExecuted event.

    Args:
        trade_executed_detail: The detail payload from TradeExecuted event

    Returns:
        Total trade value as float

    """
    # Try execution_summary first
    execution_summary = trade_executed_detail.get("execution_summary", {})
    if isinstance(execution_summary, dict):
        total_value = execution_summary.get("total_trade_value")
        if total_value is not None:
            try:
                return float(total_value)
            except (TypeError, ValueError):
                pass

    # Fall back to summing orders
    orders = trade_executed_detail.get("orders_executed", [])
    if isinstance(orders, list):
        total = 0.0
        for order in orders:
            if isinstance(order, dict):
                try:
                    value = order.get("filled_value") or order.get("notional") or 0
                    total += float(value)
                except (TypeError, ValueError):
                    pass
        return total

    return 0.0
