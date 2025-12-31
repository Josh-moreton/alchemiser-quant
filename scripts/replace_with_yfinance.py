"""Business Unit: data | Status: current.

Replace bad historical data for specific symbols with yfinance data.

For symbols where Alpaca's corporate action adjustments don't match
yfinance, this script fetches clean historical data from yfinance and
replaces the S3 data entirely.
"""

from __future__ import annotations

import sys
import warnings
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf

warnings.filterwarnings("ignore")

# Setup imports for Lambda layers architecture
import _setup_imports  # noqa: F401

from the_alchemiser.shared.data_v2.market_data_store import MarketDataStore
from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)


def fetch_yfinance_data(symbol: str, start_date: str, end_date: str) -> pd.DataFrame | None:
    """Fetch historical data from yfinance.

    Args:
        symbol: Ticker symbol
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

    Returns:
        DataFrame with columns: timestamp, open, high, low, close, volume
    """
    logger.info(f"Fetching {symbol} from yfinance", symbol=symbol, start=start_date, end=end_date)

    try:
        # Add one day to end_date because yfinance is exclusive
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)

        # Fetch data with auto_adjust=False to get Adj Close column
        df = yf.download(
            symbol,
            start=start_date,
            end=end_dt.strftime("%Y-%m-%d"),
            auto_adjust=False,
            progress=False,
        )

        if df is None or df.empty:
            logger.error(f"No data returned from yfinance", symbol=symbol)
            return None

        # Flatten multi-index columns if needed
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Rename columns to match our schema
        df = df.rename(
            columns={
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",  # Use unadjusted close
                "Adj Close": "adj_close",
                "Volume": "volume",
            }
        )

        # Use Adj Close as our close price (this is the adjusted price)
        if "adj_close" in df.columns:
            df["close"] = df["adj_close"]

        # Reset index to get date as column
        df = df.reset_index()
        df = df.rename(columns={"Date": "timestamp"})

        # Ensure timestamp is datetime
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        # Select only required columns
        df = df[["timestamp", "open", "high", "low", "close", "volume"]]

        # Remove any NaN rows
        df = df.dropna()

        logger.info(f"Fetched {len(df)} bars for {symbol}", symbol=symbol, bar_count=len(df))
        return df

    except Exception as e:
        logger.error(f"Failed to fetch data from yfinance", symbol=symbol, error=str(e))
        return None


def replace_symbol_data(
    symbol: str,
    market_data_store: MarketDataStore,
    lookback_days: int = 1825,
) -> bool:
    """Replace S3 data for a symbol with yfinance data.

    Args:
        symbol: Ticker symbol
        market_data_store: MarketDataStore instance
        lookback_days: Number of days of history to fetch (default: 5 years)

    Returns:
        True if successful, False otherwise
    """
    # Calculate date range
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")

    # Fetch from yfinance
    df = fetch_yfinance_data(symbol, start_date, end_date)
    if df is None:
        return False

    # Write to S3 (this replaces existing data)
    logger.info(f"Writing {len(df)} bars to S3", symbol=symbol, bar_count=len(df))
    success = market_data_store.write_symbol_data(symbol, df)

    if success:
        logger.info(f"Successfully replaced S3 data with yfinance", symbol=symbol)
    else:
        logger.error(f"Failed to write data to S3", symbol=symbol)

    return success


def main() -> int:
    """Main entry point."""
    # Symbols with known Alpaca vs yfinance discrepancies
    symbols = [
        "FAS",    # 6% persistent diff
        "SVXY",   # Historical diff (now converged)
        "KMLM",   # Historical diff (now converged)
        "OILD",   # Historical diff (now converged)
        "NVO",    # Small diff
        "FNGO",   # Historical diffs
        "UGE",    # Historical diffs
        "ISCB",   # Historical diffs
        "GDXU",   # Historical diffs
        "SAA",    # Historical diffs
        "DBMF",   # Historical diffs
        "TMF",    # Historical diff (now converged)
        "VXX",    # Historical diffs
    ]

    print("=" * 80)
    print("REPLACING HISTORICAL DATA WITH YFINANCE")
    print("=" * 80)
    print(f"\nSymbols to process: {len(symbols)}")
    print(f"Lookback: 5 years (1825 days)")
    print()

    # Confirmation
    response = input("This will REPLACE existing S3 data. Continue? [y/N] ").strip().lower()
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

        if replace_symbol_data(symbol, market_data_store):
            success_count += 1
            print(f"  ✓ {symbol} replaced successfully")
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

    print("\n✓ All symbols replaced successfully!")
    print("\nNext steps:")
    print("1. Run validation script to verify: poetry run python scripts/validate_s3_against_yfinance.py")
    print("2. Clear bad data markers from DynamoDB")

    return 0


if __name__ == "__main__":
    sys.exit(main())
