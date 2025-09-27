#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

P&L Command CLI for The Alchemiser Trading System.

This module provides a command-line interface for portfolio profit and loss analysis,
supporting weekly and monthly performance reports using the Alpaca API.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path for script execution
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from the_alchemiser.shared.config.config import load_settings
from the_alchemiser.shared.logging.logging_utils import configure_application_logging
from the_alchemiser.shared.services.pnl_service import PnLService


def setup_logging(verbose: bool) -> None:
    """Set up logging configuration.

    Args:
        verbose: Enable verbose logging
    """
    if verbose:
        configure_application_logging()
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        configure_application_logging()
        logging.getLogger().setLevel(logging.INFO)


def validate_positive_int(value: str) -> int:
    """Validate that a string represents a positive integer.
    
    Args:
        value: String value to validate
        
    Returns:
        Positive integer value
        
    Raises:
        argparse.ArgumentTypeError: If value is not a positive integer
    """
    try:
        ivalue = int(value)
        if ivalue <= 0:
            raise argparse.ArgumentTypeError(f"Must be a positive integer, got {value}")
        return ivalue
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid integer value: {value}")


def main() -> int:
    """Main CLI entry point for P&L analysis.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    parser = argparse.ArgumentParser(
        description="Analyze portfolio profit and loss performance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show last week's P&L
  python -m the_alchemiser.shared.cli.pnl_command --weekly

  # Show last month's P&L with daily breakdown
  python -m the_alchemiser.shared.cli.pnl_command --monthly --detailed

  # Show P&L for last 3 weeks
  python -m the_alchemiser.shared.cli.pnl_command --weekly --periods 3

  # Show P&L using Alpaca period format
  python -m the_alchemiser.shared.cli.pnl_command --period 1M

  # Verbose logging
  python -m the_alchemiser.shared.cli.pnl_command --monthly --verbose
        """,
    )

    # Time period options (mutually exclusive)
    period_group = parser.add_mutually_exclusive_group(required=True)
    
    period_group.add_argument(
        "--weekly",
        action="store_true",
        help="Show weekly P&L report",
    )
    
    period_group.add_argument(
        "--monthly",
        action="store_true",
        help="Show monthly P&L report",
    )
    
    period_group.add_argument(
        "--period",
        help="Use Alpaca period format (1W, 1M, 3M, 1A)",
        metavar="PERIOD",
    )

    # Number of periods back
    parser.add_argument(
        "--periods",
        type=validate_positive_int,
        default=1,
        help="Number of periods back to analyze (default: 1)",
        metavar="N",
    )

    # Output options
    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Show detailed daily breakdown",
    )

    # Logging options
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Set up logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    try:
        # Load configuration and create service
        logger.info("Initializing P&L service...")
        settings = load_settings()
        service = PnLService()

        # Determine analysis type and get data
        if args.weekly:
            logger.info(f"Analyzing weekly P&L for {args.periods} week(s) back...")
            pnl_data = service.get_weekly_pnl(args.periods)
        elif args.monthly:
            logger.info(f"Analyzing monthly P&L for {args.periods} month(s) back...")
            pnl_data = service.get_monthly_pnl(args.periods)
        elif args.period:
            logger.info(f"Analyzing P&L for period: {args.period}")
            pnl_data = service.get_period_pnl(args.period)
        else:
            # This shouldn't happen due to mutually exclusive group
            logger.error("No analysis type specified")
            return 1

        # Generate and display report
        logger.info("Generating P&L report...")
        report = service.format_pnl_report(pnl_data, detailed=args.detailed)
        
        print()
        print(report)
        print()

        # Show data availability status
        if pnl_data.start_value is None:
            print("⚠️  Warning: No portfolio data found for the specified period")
            return 1
        
        # Show success status
        pnl_status = "positive" if (pnl_data.total_pnl or 0) >= 0 else "negative"
        logger.info(f"✅ P&L analysis completed - {pnl_status} performance")
        return 0

    except Exception as e:
        logger.error(f"Error analyzing P&L: {e}")
        if args.verbose:
            logger.exception("Full stack trace:")
        return 1


if __name__ == "__main__":
    sys.exit(main())