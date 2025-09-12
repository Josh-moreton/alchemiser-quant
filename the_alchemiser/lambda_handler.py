"""Business Unit: utilities; Status: current.

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
import logging
from typing import Any

from the_alchemiser.main import main
from the_alchemiser.shared.dto import LambdaEventDTO
from the_alchemiser.shared.logging.logging_utils import (
    generate_request_id,
    set_request_id,
)
from the_alchemiser.shared.types.exceptions import (
    DataProviderError,
    NotificationError,
    StrategyExecutionError,
    TradingClientError,
)

# Set up logging
logger = logging.getLogger(__name__)


def parse_event_mode(
    event: LambdaEventDTO | dict[str, Any],
) -> list[str]:  # Lambda event can be flexible dict or TypedDict
    """Parse the Lambda event to determine which trading mode to execute.

    Args:
        event: AWS Lambda event data containing mode configuration

    Returns:
        List of command arguments for the main function

    Event Structure:
        {
            "mode": "trade" | "bot",           # Required: Operation mode
            "ignore_market_hours": bool        # Optional: Override market hours (default: false)
        }

    Examples:
        Trading: {"mode": "trade"}
        Signals only: {"mode": "bot"}
        Testing: {"mode": "trade", "ignore_market_hours": true}
        Empty event (safe default): {} or None → trading with market hours ignored

    Note: Trading mode (live/paper) is now determined by deployment environment,
    not by event parameters.

    """
    # Default to trading with market hours ignored for safety
    default_args = ["trade", "--ignore-market-hours"]

    # Convert dict to DTO if needed
    if isinstance(event, dict):
        if not event:
            logger.info(
                "Empty event provided, using default trading mode with market hours ignored"
            )
            return default_args
        # Convert dict to DTO for consistent handling
        event = LambdaEventDTO(**event)

    # Handle None or DTO without mode specified
    if not event or not event.mode:
        logger.info(
            "No event or mode provided, using default trading mode with market hours ignored"
        )
        return default_args

    # Extract mode (bot or trade)
    mode = event.mode or "trade"
    if mode not in ["bot", "trade"]:
        logger.warning(f"Invalid mode '{mode}', defaulting to 'trade'")
        mode = "trade"

    # Build command arguments
    args: list[str] = [mode]

    # Only add trading-specific flags for trade mode
    if mode == "trade" and event.ignore_market_hours:
        args.append("--ignore-market-hours")

    logger.info(f"Parsed event to command: {' '.join(args)}")
    return args


def lambda_handler(event: LambdaEventDTO | None = None, context: Any = None) -> dict[str, Any]:  # noqa: ANN401  # AWS Lambda context is external object
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
        logger.info(f"Lambda invoked with event: {json.dumps(event) if event else 'None'}")

        # Parse event to determine command arguments
        command_args = parse_event_mode(event or {})

        # Extract mode information for response
        mode = command_args[0] if command_args else "unknown"

        # Determine trading mode based on endpoint URL
        from the_alchemiser.shared.config.secrets_adapter import get_alpaca_keys

        _, _, endpoint = get_alpaca_keys()
        if mode == "trade":
            trading_mode = "paper" if endpoint and "paper" in endpoint.lower() else "live"
        else:
            trading_mode = "n/a"

        logger.info(f"Executing command: {' '.join(command_args)}")

        from the_alchemiser.shared.config.config import load_settings

        _settings = load_settings()
        # main() loads settings internally; do not pass unsupported kwargs
        result = main(command_args)

        # Build response message
        if mode == "bot":
            message = (
                "Signal analysis completed successfully" if result else "Signal analysis failed"
            )
        else:
            mode_str = trading_mode.title()
            message = (
                f"{mode_str} trading completed successfully"
                if result
                else f"{mode_str} trading failed"
            )

        response = {
            "status": "success" if result else "failed",
            "mode": mode,
            "trading_mode": trading_mode,
            "message": message,
            "request_id": request_id,
        }

        logger.info(f"Lambda execution completed: {response}")
        return response

    except (DataProviderError, StrategyExecutionError, TradingClientError) as e:
        from the_alchemiser.shared.logging.logging_utils import (
            log_error_with_context,
        )

        # Safely get variables that might not be defined
        mode = locals().get("mode", "unknown")
        trading_mode = locals().get("trading_mode", "unknown")

        error_message = f"Lambda execution error ({type(e).__name__}): {e!s}"
        log_error_with_context(
            logger,
            e,
            "lambda_execution",
            function="lambda_handler",
            error_type=type(e).__name__,
            mode=mode,
            trading_mode=trading_mode,
            request_id=request_id,
        )
        logger.error(error_message, exc_info=True)

        # Enhanced error handling with detailed reporting
        try:
            from the_alchemiser.shared.errors.error_handler import (
                handle_trading_error,
                send_error_notification_if_needed,
            )

            handle_trading_error(
                error=e,
                context="lambda function execution",
                component="lambda_handler.lambda_handler",
                additional_data={
                    "event": event,
                    "request_id": request_id,
                    "parsed_command": locals().get("command_args", None),
                },
            )

            # Send detailed error notification if needed
            send_error_notification_if_needed()

        except NotificationError as notification_error:
            logger.warning("Failed to send error notification: %s", notification_error)

        return {
            "status": "failed",
            "mode": mode,
            "trading_mode": trading_mode,
            "message": error_message,
            "request_id": request_id,
        }
    except (ImportError, AttributeError, ValueError, KeyError, TypeError, OSError) as e:
        from the_alchemiser.shared.logging.logging_utils import (
            log_error_with_context,
        )

        error_message = f"Lambda execution critical error: {e!s}"
        log_error_with_context(
            logger,
            e,
            "lambda_execution",
            function="lambda_handler",
            error_type="unexpected_critical_error",
            original_error=type(e).__name__,
            request_id=request_id,
        )
        logger.error(error_message, exc_info=True)

        # Enhanced error handling with detailed reporting
        try:
            from the_alchemiser.shared.errors.error_handler import (
                handle_trading_error,
                send_error_notification_if_needed,
            )

            handle_trading_error(
                error=e,
                context="lambda function execution - unexpected error",
                component="lambda_handler.lambda_handler",
                additional_data={
                    "event": event,
                    "request_id": request_id,
                    "parsed_command": locals().get("command_args", None),
                    "original_error": type(e).__name__,
                },
            )

            # Send detailed error notification if needed
            send_error_notification_if_needed()

        except (
            NotificationError,
            ImportError,
            AttributeError,
            ValueError,
            KeyError,
            TypeError,
        ) as notification_error:
            logger.warning("Failed to send error notification: %s", notification_error)

        return {
            "status": "failed",
            "mode": "unknown",
            "trading_mode": "unknown",
            "message": error_message,
            "request_id": request_id,
        }
