#!/usr/bin/env python3
"""Business Unit: scripts | Status: current.

CLI for downloading historical backtesting data.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add project root to path
_project_root = Path(__file__).resolve().parents[1]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from scripts.backtest.data_manager import DataManager
from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)


def main() -> None:
    """Main entry point for data download."""
    parser = argparse.ArgumentParser(
        description="Download historical data for backtesting"
    )
    parser.add_argument(
        "--symbols",
        nargs="+",
        help="Symbols to download (space-separated)",
        default=["SPY", "QQQ", "TECL", "TQQQ"],
    )
    parser.add_argument(
        "--days",
        type=int,
        help="Number of days of history to download",
        default=365,
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-download even if data exists",
    )

    args = parser.parse_args()

    # Calculate date range
    # Set end_date to yesterday to avoid Alpaca subscription limitations
    # (free tier cannot query current day or last 15 minutes of SIP data)
    end_date = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    ) - timedelta(days=1)
    start_date = end_date - timedelta(days=args.days)

    logger.info(
        f"Starting data download for {len(args.symbols)} symbols",
        symbols=args.symbols,
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
    )

    # Initialize data manager
    data_manager = DataManager()

    # Download data
    results = data_manager.download_data(
        symbols=args.symbols,
        start_date=start_date,
        end_date=end_date,
        force=args.force,
    )

    # Print results
    successful = [s for s, success in results.items() if success]
    failed = [s for s, success in results.items() if not success]

    print(f"\n✅ Successfully downloaded data for {len(successful)} symbols:")
    for symbol in successful:
        info = data_manager.get_available_data(symbol)
        if info:
            print(
                f"  {symbol}: {info['bar_count']} bars from {info['start_date'][:10]} to {info['end_date'][:10]}"
            )

    if failed:
        print(f"\n❌ Failed to download data for {len(failed)} symbols:")
        for symbol in failed:
            print(f"  {symbol}")

    # Exit with error code if any failed
    sys.exit(0 if not failed else 1)


if __name__ == "__main__":
    main()
