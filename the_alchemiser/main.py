#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Main entry point for The Alchemiser Trading System.

This module handles bootstrap concerns (logging, request correlation)
and delegates business logic to orchestration. Supports programmatic
usage via main() function and minimal backward compatibility for
legacy argument-based calls.

All monetary values in downstream modules use Decimal per copilot instructions.
"""

from __future__ import annotations

__all__ = ["main"]

import sys
from contextlib import suppress
from typing import TYPE_CHECKING

# CLI imports removed - using programmatic interface only
from the_alchemiser.orchestration.system import TradingSystem
from the_alchemiser.shared.errors.error_handler import TradingSystemErrorHandler
from the_alchemiser.shared.errors.exceptions import ConfigurationError
from the_alchemiser.shared.logging import (
    configure_application_logging,
    generate_request_id,
    get_logger,
    set_request_id,
)

if TYPE_CHECKING:
    from the_alchemiser.shared.schemas.trade_run_result import TradeRunResult


class _ArgumentParsing:
    """Parsed argument results for main function."""

    def __init__(
        self,
        mode: str = "trade",
        *,
        show_tracking: bool = False,
        export_tracking_json: str | None = None,
        pnl_type: str | None = None,
        pnl_periods: int = 1,
        pnl_detailed: bool = False,
        pnl_period: str | None = None,
    ) -> None:
        self.mode = mode
        self.show_tracking = show_tracking
        self.export_tracking_json = export_tracking_json
        self.pnl_type = pnl_type
        self.pnl_periods = pnl_periods
        self.pnl_detailed = pnl_detailed
        self.pnl_period = pnl_period


def _parse_arguments(argv: list[str] | None) -> _ArgumentParsing:
    """Parse command line arguments for backward compatibility.

    Args:
        argv: Command line arguments

    Returns:
        Parsed argument configuration

    Examples:
        >>> _parse_arguments(["trade"])
        _ArgumentParsing(mode="trade", show_tracking=False, ...)
        >>> _parse_arguments(["trade", "--show-tracking"])
        _ArgumentParsing(mode="trade", show_tracking=True, ...)
        >>> _parse_arguments(["pnl", "--weekly", "--periods", "3"])
        _ArgumentParsing(mode="pnl", pnl_type="weekly", pnl_periods=3, ...)

    """
    if not argv:
        return _ArgumentParsing()

    # Initialize with defaults
    mode = argv[0]
    show_tracking = False
    export_tracking_json: str | None = None
    pnl_type: str | None = None
    pnl_periods = 1
    pnl_detailed = False
    pnl_period: str | None = None

    # Define flag handlers
    def set_show_tracking() -> None:
        nonlocal show_tracking
        show_tracking = True

    def set_detailed() -> None:
        nonlocal pnl_detailed
        pnl_detailed = True

    def set_weekly() -> None:
        nonlocal pnl_type
        pnl_type = "weekly"

    def set_monthly() -> None:
        nonlocal pnl_type
        pnl_type = "monthly"

    flag_handlers = {
        "--show-tracking": set_show_tracking,
        "--detailed": set_detailed,
        "--weekly": set_weekly,
        "--monthly": set_monthly,
    }

    # Process arguments
    i = 0
    while i < len(argv):
        arg = argv[i]

        # Handle simple flags
        if arg in flag_handlers:
            flag_handlers[arg]()
        # Handle arguments with values
        elif arg == "--export-tracking-json" and i + 1 < len(argv):
            export_tracking_json = argv[i + 1]
            i += 1
        elif arg == "--periods" and i + 1 < len(argv):
            with suppress(ValueError):
                pnl_periods = int(argv[i + 1])
            i += 1
        elif arg == "--period" and i + 1 < len(argv):
            pnl_period = argv[i + 1]
            i += 1

        i += 1

    return _ArgumentParsing(
        mode,
        show_tracking=show_tracking,
        export_tracking_json=export_tracking_json,
        pnl_type=pnl_type,
        pnl_periods=pnl_periods,
        pnl_detailed=pnl_detailed,
        pnl_period=pnl_period,
    )


def _execute_pnl_analysis(args: _ArgumentParsing) -> bool:
    """Execute P&L analysis command.

    Args:
        args: Parsed arguments containing P&L configuration

    Returns:
        True if successful, False otherwise

    """
    try:
        from the_alchemiser.shared.services.pnl_service import PnLService

        service = PnLService()

        # Determine analysis type and get data
        if args.pnl_type == "weekly":
            pnl_data = service.get_weekly_pnl(args.pnl_periods)
        elif args.pnl_type == "monthly":
            pnl_data = service.get_monthly_pnl(args.pnl_periods)
        elif args.pnl_period:
            pnl_data = service.get_period_pnl(args.pnl_period)
        else:
            # Default to weekly if no specific type provided
            pnl_data = service.get_weekly_pnl(1)

        # Generate and display report
        report = service.format_pnl_report(pnl_data, detailed=args.pnl_detailed)
        print()
        print(report)
        print()

        # Return success if we have data
        return pnl_data.start_value is not None

    except Exception as e:
        logger = get_logger(__name__)
        logger.error("P&L analysis failed", error=str(e))
        return False


def _send_error_notification() -> None:
    """Send error notification if needed, using event bus."""
    try:
        from the_alchemiser.shared.config.container import ApplicationContainer
        from the_alchemiser.shared.errors.error_handler import (
            send_error_notification_if_needed,
        )

        # Create container and event bus for error notification
        container = ApplicationContainer()
        event_bus = container.services.event_bus()
        send_error_notification_if_needed(event_bus)
    except Exception as notification_error:  # pragma: no cover (best-effort)
        logger = get_logger(__name__)
        logger.warning("Failed to send error notification", error=str(notification_error))


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

    # Log parsed arguments and mode for observability
    logger = get_logger(__name__)
    logger.info(
        "Application invoked",
        mode=args.mode,
        request_id=request_id,
        show_tracking=args.show_tracking if args.mode == "trade" else None,
        pnl_type=args.pnl_type if args.mode == "pnl" else None,
        pnl_periods=args.pnl_periods if args.mode == "pnl" else None,
        pnl_detailed=args.pnl_detailed if args.mode == "pnl" else None,
    )

    # Execute operation with proper error boundary
    try:
        if args.mode == "trade":
            system = TradingSystem()
            return system.execute_trading(
                show_tracking=args.show_tracking,
                export_tracking_json=args.export_tracking_json,
            )
        if args.mode == "pnl":
            return _execute_pnl_analysis(args)

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
