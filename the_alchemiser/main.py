#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Main entry point for The Alchemiser Trading System.

This module handles bootstrap concerns (logging, request correlation)
and delegates business logic to orchestration. Supports programmatic
usage via main() function and minimal backward compatibility for
legacy argument-based calls.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

# CLI imports removed - using programmatic interface only
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
        argv: Command line arguments - supports ["trade"] for backward compatibility
              with legacy calls, but primarily for programmatic usage

    Returns:
        TradeRunResultDTO for trade execution, or bool for other operations

    """
    # Setup logging and request tracking
    configure_application_logging()
    request_id = generate_request_id()
    set_request_id(request_id)

    # Simple argument handling for backward compatibility
    # Primary usage should be programmatic via TradingSystem class
    mode = "trade"  # Default mode
    show_tracking = False
    export_tracking_json = None

    if argv:
        if len(argv) > 0:
            mode = argv[0]
        # For backward compatibility, check for additional arguments
        # but don't require full argument parsing
        for i, arg in enumerate(argv):
            if arg == "--show-tracking":
                show_tracking = True
            elif arg == "--export-tracking-json" and i + 1 < len(argv):
                export_tracking_json = argv[i + 1]

    # Execute operation with proper error boundary
    try:
        system = TradingSystem()

        if mode == "trade":
            return system.execute_trading(
                show_tracking=show_tracking,
                export_tracking_json=export_tracking_json,
            )

        return False

    except (ConfigurationError, ValueError, ImportError) as e:
        error_handler = TradingSystemErrorHandler()
        error_handler.handle_error(
            error=e,
            context="application initialization and execution",
            component="main",
            additional_data={
                "mode": mode,
                "request_id": request_id,
                "argv": argv,
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

        return False

    except Exception as e:  # pragma: no cover (broad fallback)
        error_handler = TradingSystemErrorHandler()
        error_handler.handle_error(
            error=e,
            context="application execution - unhandled exception",
            component="main",
            additional_data={
                "mode": mode,
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

        return False


if __name__ == "__main__":
    result = main()
    # Handle both TradeRunResultDTO and boolean return types
    if hasattr(result, "success"):
        sys.exit(0 if getattr(result, "success", False) else 1)
    sys.exit(0 if result else 1)
