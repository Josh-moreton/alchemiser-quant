"""Business Unit: shared | Status: current.

AWS Lambda Handler for The Alchemiser Quantitative Trading System.

This module provides the entry point for running The Alchemiser trading system
as an AWS Lambda function, enabling serverless execution and automated trading
in the cloud environment.

The handler wraps the main application entry point and provides appropriate
response formatting for AWS Lambda integration. It supports different trading
modes based on the event payload.
"""

from __future__ import annotations

import json
from typing import Any

from the_alchemiser.main import main
from the_alchemiser.shared.config.secrets_adapter import get_alpaca_keys
from the_alchemiser.shared.errors.error_handler import (
    handle_trading_error,
    send_error_notification_if_needed,
)
from the_alchemiser.shared.errors.exceptions import (
    DataProviderError,
    NotificationError,
    StrategyExecutionError,
    TradingClientError,
)
from the_alchemiser.shared.logging import (
    generate_request_id,
    get_logger,
    set_request_id,
)
from the_alchemiser.shared.schemas import LambdaEvent

# Set up logging
logger = get_logger(__name__)

# Public API
__all__ = [
    "lambda_handler",
    "parse_event_mode",
]


def _sanitize_event_for_logging(event: LambdaEvent | dict[str, Any] | None) -> dict[str, Any]:
    """Sanitize event for logging by removing sensitive fields.

    Args:
        event: Lambda event to sanitize

    Returns:
        Sanitized event dict safe for logging

    """
    if not event:
        return {}

    if isinstance(event, dict):
        event_dict = event.copy()
    else:
        # Use mode="json" to ensure all types (Decimal, datetime) are JSON-serializable
        event_dict = event.model_dump(mode="json") if hasattr(event, "model_dump") else {}

    # Remove sensitive fields if present
    sensitive_keys = ["api_key", "secret_key", "password", "token", "credentials"]
    for key in sensitive_keys:
        if key in event_dict:
            event_dict[key] = "***REDACTED***"

    return event_dict


def _determine_trading_mode(mode: str) -> str:
    """Determine trading mode based on endpoint configuration.

    Args:
        mode: The execution mode (currently only 'trade').

    Returns:
        Trading mode string (paper or live). Returns 'n/a' for unsupported modes.

    """
    if mode != "trade":
        return "n/a"

    _, _, endpoint = get_alpaca_keys()
    return "paper" if endpoint and "paper" in endpoint.lower() else "live"


def _build_response_message(trading_mode: str, *, result: bool) -> str:
    """Build response message based on trading mode and result.

    Args:
        trading_mode: Trading mode (paper/live/n/a)
        result: Execution result

    Returns:
        Formatted response message

    """
    mode_str = trading_mode.title()
    return f"{mode_str} trading completed successfully" if result else f"{mode_str} trading failed"


## Monthly summary path removed intentionally. Use CLI scripts/send_monthly_summary.py for any
# ad-hoc reporting outside Lambda.


def _handle_error(
    error: Exception,
    event: LambdaEvent | None,
    request_id: str,
    context_suffix: str = "",
    command_args: list[str] | None = None,
    *,
    is_critical: bool = False,
) -> None:
    """Handle errors with detailed reporting and notification.

    Args:
        error: The exception that occurred
        event: Original Lambda event
        request_id: Request correlation ID
        context_suffix: Additional context to append to error context
        command_args: Parsed command arguments (optional)
        is_critical: Whether this is a critical system error

    """
    try:
        context = f"lambda function execution{context_suffix}"
        additional_data = {
            "event": event,
            "request_id": request_id,
            "parsed_command": command_args,
        }

        if is_critical:
            additional_data["original_error"] = type(error).__name__

        handle_trading_error(
            error=error,
            context=context,
            component="lambda_handler.lambda_handler",
            additional_data=additional_data,
        )

        # Create container and event bus for error notification
        try:
            from the_alchemiser.shared.config.container import ApplicationContainer

            container = ApplicationContainer()
            event_bus = container.services.event_bus()
            send_error_notification_if_needed(event_bus)
        except Exception as setup_error:
            logger.warning(
                "Failed to setup event bus for error notification", error=str(setup_error)
            )

    except NotificationError as notification_error:
        logger.warning("Failed to send error notification: %s", notification_error)
    except (
        ImportError,
        AttributeError,
        ValueError,
        KeyError,
        TypeError,
    ) as notification_error:
        if is_critical:
            logger.warning("Failed to send error notification: %s", notification_error)
        else:
            # Re-raise for non-critical errors if notification system itself fails
            raise


def _handle_trading_error(
    error: Exception,
    event: LambdaEvent | None,
    request_id: str,
    command_args: list[str] | None = None,
) -> None:
    """Handle trading-related errors with detailed reporting.

    Args:
        error: The exception that occurred
        event: Original Lambda event
        request_id: Request correlation ID
        command_args: Parsed command arguments (optional)

    """
    _handle_error(error, event, request_id, "", command_args, is_critical=False)


def _handle_critical_error(
    error: Exception,
    event: LambdaEvent | None,
    request_id: str,
    command_args: list[str] | None = None,
) -> None:
    """Handle critical system errors with detailed reporting.

    Args:
        error: The exception that occurred
        event: Original Lambda event
        request_id: Request correlation ID
        command_args: Parsed command arguments (optional)

    """
    _handle_error(error, event, request_id, " - unexpected error", command_args, is_critical=True)


def _extract_correlation_id(event: LambdaEvent | dict[str, Any] | None) -> str:
    """Extract or generate correlation ID from event.

    Args:
        event: Lambda event that may contain a correlation_id

    Returns:
        Correlation ID string (extracted from event or newly generated)

    """
    if event and isinstance(event, dict) and event.get("correlation_id"):
        return str(event["correlation_id"])
    if event and hasattr(event, "correlation_id") and event.correlation_id:
        return str(event.correlation_id)
    return generate_request_id()


def _has_correlation_id(event: LambdaEvent | dict[str, Any] | None) -> bool:
    """Check if event has a correlation ID.

    Args:
        event: Lambda event to check

    Returns:
        True if event contains a correlation_id, False otherwise

    """
    if not event:
        return False
    if isinstance(event, dict):
        return bool(event.get("correlation_id"))
    return bool(hasattr(event, "correlation_id") and event.correlation_id)


def _is_domain_event(event: dict[str, Any] | LambdaEvent | None) -> bool:
    """Detect if event is a domain event (vs. command/scheduler event).

    Domain events are business events published by the trading system modules
    (WorkflowStarted, SignalGenerated, etc.) that should be routed to
    lambda_handler_eventbridge for processing.

    Command events are scheduler invocations or direct Lambda calls that should
    be processed by lambda_handler (this module).

    Args:
        event: Lambda event payload

    Returns:
        True if domain event (WorkflowStarted, SignalGenerated, etc.)
        False if command event (Scheduled Event, direct invocation)

    """
    if not isinstance(event, dict):
        return False

    detail_type = event.get("detail-type", "")
    source = event.get("source", "")

    # Known domain event types that should route to lambda_handler_eventbridge
    domain_event_types = {
        "WorkflowStarted",
        "SignalGenerated",
        "RebalancePlanned",
        "TradeExecuted",
        "WorkflowCompleted",
        "WorkflowFailed",
    }

    # Check if it's a domain event from alchemiser modules
    return detail_type in domain_event_types and source.startswith("alchemiser.")


def _build_error_response(
    mode: str,
    trading_mode: str,
    error_message: str,
    request_id: str,
) -> dict[str, Any]:
    """Build error response dictionary.

    Args:
        mode: Execution mode
        trading_mode: Trading mode (paper/live/n/a)
        error_message: Error message to include
        request_id: Request correlation ID

    Returns:
        Error response dictionary

    """
    return {
        "status": "failed",
        "mode": mode,
        "trading_mode": trading_mode,
        "message": error_message,
        "request_id": request_id,
    }


def parse_event_mode(event: dict[str, Any] | LambdaEvent) -> list[str]:
    """Parse Lambda event data to extract command-line arguments for execution.

    Determines the execution mode from event payload and returns appropriate
    command arguments for the main function. Supports trading, P&L analysis,
    and bot modes with various configuration options.

    Args:
        event: AWS Lambda event data (may be EventBridge envelope or direct payload)

    Returns:
        List of command arguments for the main function

    """
    # Unwrap EventBridge envelope if present
    # EventBridge wraps events with metadata: version, id, detail-type, source, etc.
    # The actual event data is nested in the 'detail' field
    if isinstance(event, dict) and "detail-type" in event and "detail" in event:
        logger.debug(
            "Detected EventBridge envelope; extracting detail payload",
            detail_type=event.get("detail-type"),
            source=event.get("source"),
        )
        event = event["detail"]

    # Validate event shape
    event_obj = LambdaEvent(**event) if isinstance(event, dict) else event

    # P&L analysis action
    if isinstance(event_obj, LambdaEvent) and getattr(event_obj, "action", None) == "pnl_analysis":
        logger.info("Parsed event to action: pnl_analysis")
        command_args = ["pnl"]

        # Add P&L-specific arguments
        if getattr(event_obj, "pnl_type", None) == "weekly":
            command_args.append("--weekly")
        elif getattr(event_obj, "pnl_type", None) == "monthly":
            command_args.append("--monthly")

        if getattr(event_obj, "pnl_period", None):
            command_args.extend(["--period", str(event_obj.pnl_period)])

        pnl_periods_val = getattr(event_obj, "pnl_periods", None)
        if isinstance(pnl_periods_val, int) and pnl_periods_val > 1:
            command_args.extend(["--periods", str(event_obj.pnl_periods)])

        if getattr(event_obj, "pnl_detailed", None):
            command_args.append("--detailed")

        return command_args

    logger.info("Parsed event to command: trade")
    return ["trade"]


def lambda_handler(
    event: LambdaEvent | None = None, context: object | None = None
) -> dict[str, Any]:
    """AWS Lambda function handler for The Alchemiser trading system.

    This function serves as the entry point when the trading system is deployed
    as an AWS Lambda function. It supports multiple trading modes based on the
    event configuration and returns detailed status information.

    Args:
        event: AWS Lambda event data containing mode configuration.
            See parse_event_mode() for expected structure.
        context: AWS Lambda runtime context object
            containing information about the Lambda function execution environment.

    Returns:
        dict: A dictionary containing the execution status with the following structure:
            {
                "status": "success" | "failed",
                "mode": str,                    # The executed mode
                "trading_mode": str,            # The trading mode (if applicable)
                "message": str,                 # Human-readable status message
                "request_id": str               # Lambda request ID (if available)
            }

    Examples:
        Paper trading event:
        >>> event = {"mode": "trade", "trading_mode": "paper"}
        >>> result = lambda_handler(event, context)
        >>> print(result)
        {
            "status": "success",
            "mode": "trade",
            "trading_mode": "paper",
            "message": "Paper trading completed successfully",
            "request_id": "12345-abcde"
        }

        Live trading event (default):
        >>> event = {"mode": "trade", "trading_mode": "live"}
        >>> result = lambda_handler(event, context)
        >>> print(result)
        {
            "status": "success",
            "mode": "trade",
            "trading_mode": "live",
            "message": "Live trading completed successfully",
            "request_id": "12345-abcde"
        }

        P&L analysis event:
        >>> event = {"action": "pnl_analysis", "pnl_type": "weekly"}
        >>> result = lambda_handler(event, context)
        >>> print(result)
        {
            "status": "success",
            "mode": "pnl",
            "trading_mode": "n/a",
            "message": "N/A trading completed successfully",
            "request_id": "12345-abcde"
        }

    Backward Compatibility:
        - Empty event defaults to paper trading with market hours ignored for safety
        - This allows testing outside market hours without risking live trades
        - Maintains safe behavior while supporting new event-driven modes

    """
    # Extract request ID for tracking
    request_id = getattr(context, "aws_request_id", "unknown") if context else "local"

    # Generate and set correlation request ID for all downstream logs
    # Use event correlation_id if provided (for idempotency)
    correlation_id = _extract_correlation_id(event)
    set_request_id(correlation_id)

    logger.info(
        "Lambda invoked",
        aws_request_id=request_id,
        correlation_id=correlation_id,
        event_has_correlation_id=_has_correlation_id(event),
    )

    # Circuit breaker: Skip error notification events to prevent infinite error loops
    # When an error occurs, it publishes ErrorNotificationRequested to EventBridge,
    # which triggers this Lambda again. Without this check, one error creates a cascade.
    if isinstance(event, dict):
        detail_type = event.get("detail-type")
        if detail_type == "ErrorNotificationRequested":
            logger.info(
                "Skipping ErrorNotificationRequested event to prevent error cascade",
                detail_type=detail_type,
            )
            return {
                "status": "skipped",
                "mode": "error_notification",
                "trading_mode": "n/a",
                "message": "Error notification event skipped (circuit breaker)",
                "request_id": request_id,
            }

    # Smart routing: Detect domain events and route to eventbridge handler
    # Domain events (WorkflowStarted, SignalGenerated, etc.) have different schemas
    # than command events (Scheduled Event, direct invocations) and need different processing
    if _is_domain_event(event):
        # Type assertion: _is_domain_event already verified event is dict
        if not isinstance(event, dict):
            logger.error("Event should be dict after _is_domain_event check")
            return {
                "status": "failed",
                "mode": "unknown",
                "trading_mode": "n/a",
                "message": "Invalid event type for domain event routing",
                "request_id": request_id,
            }

        logger.info(
            "Routing to eventbridge_handler for domain event",
            detail_type=event.get("detail-type"),
            source=event.get("source"),
            correlation_id=correlation_id,
        )
        from the_alchemiser.lambda_handler_eventbridge import eventbridge_handler

        return eventbridge_handler(event, context)

    # TODO: Add idempotency check using DynamoDB or EventBridge event deduplication
    # if _is_duplicate_request(correlation_id):
    #     logger.warning("Duplicate request detected; skipping execution", correlation_id=correlation_id)
    #     return {"status": "skipped", "message": "Duplicate request", "request_id": request_id}

    try:
        # Log the incoming event for debugging (sanitize secrets)
        event_for_logging = _sanitize_event_for_logging(event) if event else None
        event_json = json.dumps(event_for_logging) if event_for_logging else "None"
        logger.info(
            "Lambda invoked with event", event_data=event_json, correlation_id=correlation_id
        )

        # Parse event to determine command arguments
        command_args = parse_event_mode(event or {})

        # Extract mode information for response
        # Determine from command_args: first arg is mode (trade/pnl/bot)
        mode = command_args[0] if command_args else "trade"

        # Determine trading mode based on endpoint URL
        trading_mode = _determine_trading_mode(mode)

        logger.info("Executing command", command=" ".join(command_args))

        # main() loads settings internally; do not pass unsupported kwargs
        result = main(command_args)

        # Normalize result for response formatting
        result_ok = bool(result.success) if hasattr(result, "success") else bool(result)

        # Build response message
        message = _build_response_message(trading_mode, result=result_ok)

        response = {
            "status": "success" if result_ok else "failed",
            "mode": mode,
            "trading_mode": trading_mode,
            "message": message,
            "request_id": request_id,
        }

        logger.info("Lambda execution completed", response=response)
        return response

    except (DataProviderError, StrategyExecutionError, TradingClientError) as e:
        # Safely get variables that might not be defined
        mode = locals().get("mode", "unknown")
        trading_mode = locals().get("trading_mode", "unknown")
        parsed_command_args = locals().get("command_args")  # type: list[str] | None

        error_message = f"Lambda execution error ({type(e).__name__}): {e!s}"
        logger.error(
            "Lambda execution error",
            error_message=error_message,
            error_type=type(e).__name__,
            operation="lambda_execution",
            function="lambda_handler",
            mode=mode,
            trading_mode=trading_mode,
            request_id=request_id,
            exc_info=True,
        )

        # Enhanced error handling with detailed reporting
        _handle_trading_error(e, event, request_id, parsed_command_args)

        return _build_error_response(mode, trading_mode, error_message, request_id)
    except (ImportError, AttributeError, ValueError, KeyError, TypeError, OSError) as e:
        critical_command_args = locals().get("command_args")  # type: list[str] | None

        error_message = f"Lambda execution critical error: {e!s}"
        logger.error(
            "Lambda execution critical error",
            error_message=error_message,
            error_type="unexpected_critical_error",
            original_error=type(e).__name__,
            operation="lambda_execution",
            function="lambda_handler",
            request_id=request_id,
            exc_info=True,
        )

        # Enhanced error handling with detailed reporting
        _handle_critical_error(e, event, request_id, critical_command_args)

        return _build_error_response("unknown", "unknown", error_message, request_id)
