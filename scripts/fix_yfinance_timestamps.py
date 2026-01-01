#!/usr/bin/env python3
"""Business Unit: scripts | Status: current.

Fix timezone-naive timestamps for yfinance symbols.

For the 13 symbols that were manually replaced with yfinance data,
this script converts their timezone-naive timestamps to UTC-aware
to match the Alpaca data format.
"""

from __future__ import annotations

import sys

import pandas as pd

# Setup imports for Lambda layers architecture
import _setup_imports  # noqa: F401

from the_alchemiser.shared.data_v2.market_data_store import MarketDataStore
from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)


def fix_symbol_timestamps(
    symbol: str,
    market_data_store: MarketDataStore,
) -> bool:
    """Fix timezone-naive timestamps for a symbol.

    Args:
        symbol: Ticker symbol
        market_data_store: MarketDataStore instance

    Returns:
        True if successful, False otherwise
    """
    logger.info("Fixing timestamps", symbol=symbol)

    # Read existing data
    df = market_data_store.read_symbol_data(symbol, use_cache=False)

    if df is None or df.empty:
        logger.error("No data found for symbol", symbol=symbol)
        return False

    # Check if timestamp column exists
    if "timestamp" not in df.columns:
        logger.error("No timestamp column found", symbol=symbol)
        return False

    # Convert timestamp to UTC-aware (if not already)
    original_dtype = df["timestamp"].dtype
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    new_dtype = df["timestamp"].dtype

    logger.info(
        "Converted timestamps",
        symbol=symbol,
        original_dtype=str(original_dtype),
        new_dtype=str(new_dtype),
        row_count=len(df),
    )

    # Write back to S3
    success = market_data_store.write_symbol_data(symbol, df)

    if success:
        logger.info("Successfully fixed timestamps", symbol=symbol)
    else:
        logger.error("Failed to write data to S3", symbol=symbol)

    return success


def main() -> int:
    """Main entry point."""
    # The 13 symbols that failed with timezone errors
    symbols = [
        "DBMF",
        "FAS",
        "FNGO",
        "GDXU",
        "ISCB",
        "KMLM",
        "NVO",
        "OILD",
        "SAA",
        "SVXY",
        "TMF",
        "UGE",
        "VXX",
    ]

    print("=" * 80)
    print("FIXING YFINANCE TIMESTAMPS")
    print("=" * 80)
    print(f"\nSymbols to process: {len(symbols)}")
    print("This will convert timezone-naive timestamps to UTC-aware.")
    print()

    # Confirmation
    response = input("Continue? [y/N] ").strip().lower()
    if response != "y":
        print("Aborted.")
        return 0

    # Initialize market data store
    market_data_store = MarketDataStore(bucket_name="alchemiser-shared-market-data")

    # Process each symbol
    success_count = 0
    failed_symbols = []

    for i, symbol in enumerate(symbols, 1):
        print(f"\n[{i}/{len(symbols)}] Processing {symbol}...")

        if fix_symbol_timestamps(symbol, market_data_store):
            success_count += 1
            print(f"  ✓ {symbol} fixed successfully")
        else:
            failed_symbols.append(symbol)
            print(f"  ✗ {symbol} failed")

    # Summary
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total symbols: {len(symbols)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {len(failed_symbols)}")

    if failed_symbols:
        print(f"\nFailed symbols: {', '.join(failed_symbols)}")
        return 1

    print("\n✓ All symbols fixed successfully!")
    print("\nNext steps:")
    print("1. Test data refresh: aws lambda invoke --function-name alchemiser-dev-data ...")
    print("2. Verify no more timezone errors in CloudWatch logs")

    return 0


if __name__ == "__main__":
    sys.exit(main())
