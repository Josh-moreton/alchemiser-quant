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
    from the_alchemiser.shared.schemas.trade_results import TradeRunResult


class _ArgumentParsing:
    """Parsed argument results for main function."""

    def __init__(
        self,
        mode: str = "trade",
        *,
        show_tracking: bool = False,
        export_tracking_json: str | None = None,
    ) -> None:
        self.mode = mode
        self.show_tracking = show_tracking
        self.export_tracking_json = export_tracking_json


def _parse_arguments(argv: list[str] | None) -> _ArgumentParsing:
    """Parse command line arguments for backward compatibility.

    Args:
        argv: Command line arguments

    Returns:
        Parsed argument configuration

    """
    if not argv:
        return _ArgumentParsing()

    mode = argv[0] if argv else "trade"
    show_tracking = False
    export_tracking_json = None

    for i, arg in enumerate(argv):
        if arg == "--show-tracking":
            show_tracking = True
        elif arg == "--export-tracking-json" and i + 1 < len(argv):
            export_tracking_json = argv[i + 1]

    return _ArgumentParsing(
        mode, show_tracking=show_tracking, export_tracking_json=export_tracking_json
    )


def _send_error_notification() -> None:
    """Send error notification if needed, with fallback handling."""
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


def _handle_error_with_notification(
    error: Exception,
    context: str,
    additional_data: dict[str, str | list[str] | None] | None = None,
) -> None:
    """Handle error with notification using standard pattern.

    Args:
        error: The exception to handle
        context: Context description for the error
        additional_data: Additional data to include in error report

    """
    error_handler = TradingSystemErrorHandler()
    error_handler.handle_error(
        error=error,
        context=context,
        component="main",
        additional_data=additional_data or {},
    )
    _send_error_notification()


def main(argv: list[str] | None = None) -> TradeRunResult | bool:
    """Serve as main entry point for The Alchemiser Trading System.

    Args:
        argv: Command line arguments - supports ["trade"] for backward compatibility
              with legacy calls, but primarily for programmatic usage

    Returns:
        TradeRunResult for trade execution, or bool for other operations

    """
    # Setup logging and request tracking
    configure_application_logging()
    request_id = generate_request_id()
    set_request_id(request_id)

    # Parse arguments for backward compatibility
    args = _parse_arguments(argv)

    # Execute operation with proper error boundary
    try:
        system = TradingSystem()

        if args.mode == "trade":
            return system.execute_trading(
                show_tracking=args.show_tracking,
                export_tracking_json=args.export_tracking_json,
            )

        return False

    except (ConfigurationError, ValueError, ImportError) as e:
        _handle_error_with_notification(
            error=e,
            context="application initialization and execution",
            additional_data={
                "mode": args.mode,
                "request_id": request_id,
                "argv": argv,
            },
        )
        return False

    except Exception as e:  # pragma: no cover (broad fallback)
        _handle_error_with_notification(
            error=e,
            context="application execution - unhandled exception",
            additional_data={
                "mode": args.mode,
                "error_type": type(e).__name__,
                "request_id": request_id,
            },
        )
        return False


if __name__ == "__main__":
    result = main()
    # Handle both TradeRunResult and boolean return types
    if hasattr(result, "success"):
        sys.exit(0 if getattr(result, "success", False) else 1)
    sys.exit(0 if result else 1)
