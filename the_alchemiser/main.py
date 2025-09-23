#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Main entry point for The Alchemiser Trading System.

This module only handles bootstrap concerns (logging, argument parsing,
request correlation) and delegates business logic to orchestration.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from the_alchemiser.orchestration.cli.argument_parser import create_argument_parser
from the_alchemiser.orchestration.cli.cli_utilities import render_footer
from the_alchemiser.orchestration.system import TradingSystem
from the_alchemiser.shared.errors.error_handler import TradingSystemErrorHandler
from the_alchemiser.shared.logging.logging_utils import (
    configure_application_logging,
    generate_request_id,
    set_request_id,
)
from the_alchemiser.shared.types.exceptions import ConfigurationError

if TYPE_CHECKING:
    from the_alchemiser.shared.dto.trade_run_result_dto import TradeRunResultDTO


def main(argv: list[str] | None = None) -> TradeRunResultDTO | bool:
    """Serve as main entry point for The Alchemiser Trading System.

    Args:
        argv: Command line arguments (uses sys.argv if None)

    Returns:
        TradeRunResultDTO for trade execution, or bool for other operations

    """
    # Setup logging and request tracking
    configure_application_logging()
    request_id = generate_request_id()
    set_request_id(request_id)

    # Parse command line arguments
    parser = create_argument_parser()
    args = parser.parse_args(argv)

    # Execute operation with proper error boundary
    try:
        system = TradingSystem()

        if args.mode == "trade":
            return system.execute_trading(
                show_tracking=getattr(args, "show_tracking", False),
                export_tracking_json=getattr(args, "export_tracking_json", None),
            )

        return False

    except (ConfigurationError, ValueError, ImportError) as e:
        error_handler = TradingSystemErrorHandler()
        error_handler.handle_error(
            error=e,
            context="application initialization and execution",
            component="main",
            additional_data={"mode": getattr(args, "mode", "unknown")},
        )

        try:
            from the_alchemiser.shared.errors.error_handler import (
                send_error_notification_if_needed,
            )

            send_error_notification_if_needed()
        except Exception as notification_error:  # pragma: no cover (best-effort)
            import logging

            logging.getLogger(__name__).warning(
                f"Failed to send error notification: {notification_error}"
            )

        render_footer("System error occurred!")
        return False

    except Exception as e:  # pragma: no cover (broad fallback)
        error_handler = TradingSystemErrorHandler()
        error_handler.handle_error(
            error=e,
            context="application execution - unhandled exception",
            component="main",
            additional_data={
                "mode": getattr(args, "mode", "unknown"),
                "error_type": type(e).__name__,
                "request_id": request_id,
            },
        )

        try:
            from the_alchemiser.shared.errors.error_handler import (
                send_error_notification_if_needed,
            )

            send_error_notification_if_needed()
        except Exception as notification_error:  # pragma: no cover (best-effort)
            import logging

            logging.getLogger(__name__).warning(
                f"Failed to send error notification: {notification_error}"
            )

        render_footer("Unexpected system error occurred!")
        return False


if __name__ == "__main__":
    result = main()
    # Handle both TradeRunResultDTO and boolean return types
    if hasattr(result, "success"):
        sys.exit(0 if getattr(result, "success", False) else 1)
    sys.exit(0 if result else 1)
