#!/usr/bin/env python3
"""Monthly Summary Email CLI.

This script generates and sends monthly portfolio and strategy performance
summaries via email. Supports dry-run mode and month selection.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from the_alchemiser.shared.notifications.client import EmailClient
from the_alchemiser.shared.notifications.templates.email_facade import EmailTemplates
from the_alchemiser.shared.services.monthly_summary_service import MonthlySummaryService


def setup_logging(verbose: bool) -> None:
    """Set up logging configuration.

    Args:
        verbose: Enable verbose logging

    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def parse_month(month_str: str) -> tuple[int, int]:
    """Parse month string to year and month integers.

    Args:
        month_str: Month string in YYYY-MM format

    Returns:
        Tuple of (year, month)

    Raises:
        ValueError: If month string is invalid

    """
    try:
        year, month = month_str.split("-")
        year_int = int(year)
        month_int = int(month)

        if not (1 <= month_int <= 12):
            raise ValueError(f"Month must be 1-12, got {month_int}")

        if year_int < 2000 or year_int > 2100:
            raise ValueError(f"Year must be reasonable, got {year_int}")

        return year_int, month_int

    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid month format '{month_str}'. Expected YYYY-MM") from e


def get_previous_month() -> tuple[int, int]:
    """Get the previous calendar month.

    Returns:
        Tuple of (year, month) for previous month

    """
    now = datetime.now(UTC)
    if now.month == 1:
        return now.year - 1, 12
    else:
        return now.year, now.month - 1


def infer_mode() -> str:
    """Infer trading mode from environment.

    Returns:
        Trading mode string (PAPER or LIVE)

    """
    # Simple heuristic - look for common env vars that indicate live trading
    stage = os.getenv("STAGE", "").upper()
    mode = os.getenv("TRADING_MODE", "").upper()

    if stage == "PROD" or mode == "LIVE":
        return "LIVE"
    else:
        return "PAPER"


def main() -> int:
    """Main CLI entry point.

    Returns:
        Exit code (0 for success, 1 for error)

    """
    parser = argparse.ArgumentParser(
        description="Generate and send monthly portfolio and strategy performance summary",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Send summary for previous month (default)
  python scripts/send_monthly_summary.py

  # Generate for specific month and preview only
  python scripts/send_monthly_summary.py --month 2025-08 --dry-run --preview-file /tmp/summary.html

  # Send to different recipient
  python scripts/send_monthly_summary.py --to custom@example.com

  # Verbose logging
  python scripts/send_monthly_summary.py --verbose
        """,
    )

    parser.add_argument(
        "--month",
        help="Target month in YYYY-MM format (default: previous month)",
        metavar="YYYY-MM",
    )

    parser.add_argument(
        "--account-id",
        help="Explicit account ID. If omitted, uses latest available account",
        metavar="ACCOUNT_ID",
    )

    parser.add_argument(
        "--to",
        help="Override recipient email address",
        metavar="EMAIL",
    )

    parser.add_argument(
        "--subject",
        help="Override email subject",
        metavar="SUBJECT",
    )

    parser.add_argument(
        "--mode",
        choices=["PAPER", "LIVE"],
        help="Trading mode for display (default: inferred from environment)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate summary but don't send email",
    )

    parser.add_argument(
        "--preview-file",
        help="Write generated HTML to file for inspection",
        metavar="PATH",
    )

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
        # Determine target month
        if args.month:
            year, month = parse_month(args.month)
        else:
            year, month = get_previous_month()

        logger.info(f"Generating monthly summary for {year}-{month:02d}")

        # Determine trading mode
        mode = args.mode or infer_mode()
        logger.info(f"Using trading mode: {mode}")

        # Generate monthly summary
        logger.info("Computing monthly summary data...")
        service = MonthlySummaryService()
        summary = service.compute_monthly_summary(year, month, args.account_id)

        # Generate HTML content
        logger.info("Generating email template...")
        html_content = EmailTemplates.monthly_financial_summary(summary, mode)

        # Write preview file if requested
        if args.preview_file:
            preview_path = Path(args.preview_file)
            preview_path.parent.mkdir(parents=True, exist_ok=True)
            preview_path.write_text(html_content, encoding="utf-8")
            logger.info(f"Preview written to: {preview_path}")

        # Handle dry-run mode
        if args.dry_run:
            print(f"✅ Dry run completed for {summary.month_label}")
            print(f"Portfolio P&L: {summary.portfolio_pnl_abs} ({summary.portfolio_pnl_pct}%)")
            print(f"Strategy count: {len(summary.strategy_rows)}")
            if summary.notes:
                print(f"Notes: {', '.join(summary.notes)}")
            return 0

        # Send email
        logger.info("Sending email...")
        subject = args.subject or f"The Alchemiser — Monthly Summary ({summary.month_label})"

        client = EmailClient()
        success = client.send_notification(
            subject=subject,
            html_content=html_content,
            recipient_email=args.to,
        )

        if success:
            logger.info("✅ Monthly summary email sent successfully")
            return 0
        else:
            logger.error("❌ Failed to send monthly summary email")
            return 1

    except Exception as e:
        logger.error(f"Error generating monthly summary: {e}")
        if args.verbose:
            logger.exception("Full stack trace:")
        return 1


if __name__ == "__main__":
    sys.exit(main())