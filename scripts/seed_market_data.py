#!/usr/bin/env python3
"""Business Unit: data | Status: current.

Initial data seeding script for market data store.

This script fetches historical market data from Alpaca for all symbols
configured in the strategy DSL files and stores them in S3 as Parquet files.

Usage:
    # Seed all symbols from strategy configs (1 year lookback)
    poetry run python scripts/seed_market_data.py

    # Seed specific symbols
    poetry run python scripts/seed_market_data.py --symbols AAPL MSFT GOOGL

    # Custom lookback period (days)
    poetry run python scripts/seed_market_data.py --lookback 500

    # Dry run (show what would be fetched without storing)
    poetry run python scripts/seed_market_data.py --dry-run

Environment Variables Required:
    ALPACA__KEY: Alpaca API key
    ALPACA__SECRET: Alpaca API secret
    MARKET_DATA_BUCKET: S3 bucket name (optional, will construct from APP__STAGE)
    APP__STAGE: Environment stage (dev/prod)
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Ensure the package is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from the_alchemiser.data_v2.data_refresh_service import (
    DEFAULT_INITIAL_LOOKBACK_DAYS,
    DataRefreshService,
)
from the_alchemiser.data_v2.symbol_extractor import get_all_configured_symbols
from the_alchemiser.shared.logging import configure_application_logging, get_logger

configure_application_logging()
logger = get_logger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Seed historical market data from Alpaca to S3",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--symbols",
        nargs="+",
        help="Specific symbols to seed (default: all from strategy configs)",
    )

    parser.add_argument(
        "--lookback",
        type=int,
        default=DEFAULT_INITIAL_LOOKBACK_DAYS,
        help=f"Days of historical data to fetch (default: {DEFAULT_INITIAL_LOOKBACK_DAYS})",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be fetched without storing data",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )

    return parser.parse_args()


def validate_environment() -> bool:
    """Validate required environment variables are set."""
    required_vars = ["ALPACA__KEY", "ALPACA__SECRET"]
    missing = [v for v in required_vars if not os.environ.get(v)]

    if missing:
        logger.error(
            "Missing required environment variables",
            missing=missing,
        )
        print(f"Error: Missing environment variables: {', '.join(missing)}")
        print("Set them in your environment or .env file")
        return False

    # Check for bucket configuration
    bucket = os.environ.get("MARKET_DATA_BUCKET")
    stage = os.environ.get("APP__STAGE", "dev")

    if not bucket:
        # Construct bucket name from stage
        bucket = f"alchemiser-{stage}-market-data"
        os.environ["MARKET_DATA_BUCKET"] = bucket
        logger.info(
            "Using constructed bucket name",
            bucket=bucket,
            stage=stage,
        )

    return True


def main() -> int:
    """Main entry point for data seeding."""
    args = parse_args()

    print("=" * 60)
    print("Alchemiser Market Data Seeding")
    print("=" * 60)

    # Validate environment
    if not validate_environment():
        return 1

    # Get symbols to seed
    if args.symbols:
        symbols = args.symbols
        print(f"\nSeeding specific symbols: {', '.join(symbols)}")
    else:
        print("\nDiscovering symbols from strategy configurations...")
        symbols = sorted(get_all_configured_symbols())
        print(f"Found {len(symbols)} unique symbols")

    if args.verbose:
        print(f"Symbols: {', '.join(symbols)}")

    print(f"\nLookback period: {args.lookback} days")

    if args.dry_run:
        print("\n[DRY RUN] Would fetch data for:")
        for symbol in symbols:
            print(f"  - {symbol}")
        print(f"\nTotal: {len(symbols)} symbols")
        return 0

    # Confirm before proceeding
    bucket = os.environ.get("MARKET_DATA_BUCKET", "unknown")
    print(f"\nTarget S3 bucket: {bucket}")
    print(f"This will fetch data for {len(symbols)} symbols.")

    response = input("\nProceed? [y/N] ").strip().lower()
    if response != "y":
        print("Aborted.")
        return 0

    print("\nStarting data seeding...")
    print("-" * 60)

    try:
        # Create service and seed data
        service = DataRefreshService()
        results = service.seed_initial_data(
            symbols=list(symbols),
            lookback_days=args.lookback,
        )

        # Print results
        print("\n" + "=" * 60)
        print("Seeding Complete")
        print("=" * 60)

        success_count = sum(results.values())
        failed_count = len(results) - success_count

        print(f"\nTotal symbols: {len(results)}")
        print(f"Successful: {success_count}")
        print(f"Failed: {failed_count}")

        if failed_count > 0:
            print("\nFailed symbols:")
            for symbol, ok in sorted(results.items()):
                if not ok:
                    print(f"  - {symbol}")

        return 0 if failed_count == 0 else 1

    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        return 130

    except Exception as e:
        logger.error(
            "Seeding failed with exception",
            error=str(e),
            exc_info=True,
        )
        print(f"\nError: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
