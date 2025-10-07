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
from the_alchemiser.shared.config.config import load_settings
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
## ad-hoc reporting outside Lambda.


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


def parse_event_mode(event: LambdaEvent | dict[str, Any]) -> list[str]:
    """Parse the Lambda event.

    Supports two paths:
    - Trading (default): returns ['trade']
    - P&L analysis: returns ['pnl', ...] with P&L-specific arguments

    Args:
        event: AWS Lambda event data

    Returns:
        List of command arguments for the main function

    """
    # Validate event shape
    event_obj = LambdaEvent(**event) if isinstance(event, dict) else event

    # Monthly summary action is no longer supported via Lambda
    if (
        isinstance(event_obj, LambdaEvent)
        and getattr(event_obj, "action", None) == "monthly_summary"
    ):
        raise ValueError(
            "Unsupported action 'monthly_summary' via Lambda. Use the CLI script 'scripts/send_monthly_summary.py' instead."
        )

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

        Signals only event:
        >>> event = {"mode": "bot"}
        >>> result = lambda_handler(event, context)
        >>> print(result)
        {
            "status": "success",
            "mode": "bot",
            "trading_mode": "n/a",
            "message": "Signal analysis completed successfully",
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
    correlation_id = generate_request_id()
    set_request_id(correlation_id)

    try:
        # Log the incoming event for debugging
        event_json = json.dumps(event) if event else "None"
        logger.info("Lambda invoked with event", event_data=event_json)

        # Parse event to determine command arguments
        command_args = parse_event_mode(event or {})

        # Extract mode information for response (trade-only)
        mode = "trade"

        # Determine trading mode based on endpoint URL
        trading_mode = _determine_trading_mode(mode)

        logger.info("Executing command", command=" ".join(command_args))

        _settings = load_settings()
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

        return {
            "status": "failed",
            "mode": mode,
            "trading_mode": trading_mode,
            "message": error_message,
            "request_id": request_id,
        }
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
        logger.error(error_message, exc_info=True)

        # Enhanced error handling with detailed reporting
        _handle_critical_error(e, event, request_id, critical_command_args)

        return {
            "status": "failed",
            "mode": "unknown",
            "trading_mode": "unknown",
            "message": error_message,
            "request_id": request_id,
        }
