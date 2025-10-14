#!/usr/bin/env python3
"""Portfolio P&L Analysis CLI.

This script provides portfolio profit and loss analysis using the Alpaca API.
Supports weekly and monthly performance reports that can be run independently
or triggered from Lambda.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from the_alchemiser.shared.config.config import load_settings
from the_alchemiser.shared.logging import configure_application_logging
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
        description="Analyze portfolio profit and loss performance using Alpaca API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show last week's P&L
  python scripts/pnl_analysis.py --weekly

  # Show last month's P&L with daily breakdown
  python scripts/pnl_analysis.py --monthly --detailed

  # Show P&L for last 3 weeks
  python scripts/pnl_analysis.py --weekly --periods 3

  # Show P&L using Alpaca period format
  python scripts/pnl_analysis.py --period 1M

  # Save report to file
  python scripts/pnl_analysis.py --monthly --output /tmp/pnl_report.txt

  # Verbose logging
  python scripts/pnl_analysis.py --monthly --verbose
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

    parser.add_argument(
        "--output",
        help="Save report to file instead of printing to console",
        metavar="PATH",
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
        load_settings()
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

        # Generate report
        logger.info("Generating P&L report...")
        report = service.format_pnl_report(pnl_data, detailed=args.detailed)

        # Output report
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(report, encoding="utf-8")
            logger.info(f"Report saved to: {output_path}")
        else:
            print()
            print(report)
            print()

        # Show data availability status
        if pnl_data.start_value is None:
            print("⚠️  Warning: No portfolio data found for the specified period")
            return 1

        # Show success status with P&L summary
        pnl_sign = "+" if (pnl_data.total_pnl or 0) >= 0 else ""
        pnl_amount = f"${pnl_data.total_pnl:,.2f}" if pnl_data.total_pnl else "N/A"
        pnl_pct = f"({pnl_data.total_pnl_pct:+.2f}%)" if pnl_data.total_pnl_pct else ""

        logger.info(f"✅ P&L analysis completed - Total: {pnl_sign}{pnl_amount} {pnl_pct}")
        return 0

    except Exception as e:
        logger.error(f"Error analyzing P&L: {e}")
        if args.verbose:
            logger.exception("Full stack trace:")
        return 1


if __name__ == "__main__":
    sys.exit(main())
