#!/usr/bin/env python3
"""Business Unit: analysis | Status: current.

Hourly gain/loss analysis for SPY and QQQ.

This script fetches historical hourly data from Alpaca and calculates the average
gain or loss for each hour of the trading day over a specified lookback period.

Usage:
    # Default: Analyze last 10 years of hourly data
    poetry run python scripts/hourly_gain_analysis.py

    # Custom lookback period (in years)
    poetry run python scripts/hourly_gain_analysis.py --years 5

    # Custom symbols
    poetry run python scripts/hourly_gain_analysis.py --symbols SPY QQQ IWM

    # Custom output format
    poetry run python scripts/hourly_gain_analysis.py --format csv

Environment Variables Required:
    ALPACA_KEY or ALPACA__KEY: Alpaca API key
    ALPACA_SECRET or ALPACA__SECRET: Alpaca API secret
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from dotenv import load_dotenv

    # Load environment variables from .env.local if it exists, otherwise from .env
    env_local = project_root / ".env.local"
    if env_local.exists():
        load_dotenv(env_local)
    else:
        load_dotenv()
except ImportError:
    # python-dotenv not available, environment variables must be set externally
    pass

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

from the_alchemiser.shared.logging import configure_application_logging, get_logger

configure_application_logging()
logger = get_logger(__name__)


def validate_environment() -> tuple[str, str]:
    """Validate required environment variables are set.

    Returns:
        Tuple of (api_key, secret_key)

    Raises:
        SystemExit: If required environment variables are missing

    """
    # Accept both single and double underscore formats
    alpaca_key = os.environ.get("ALPACA__KEY") or os.environ.get("ALPACA_KEY")
    alpaca_secret = os.environ.get("ALPACA__SECRET") or os.environ.get("ALPACA_SECRET")

    missing = []
    if not alpaca_key:
        missing.append("ALPACA_KEY or ALPACA__KEY")
    if not alpaca_secret:
        missing.append("ALPACA_SECRET or ALPACA__SECRET")

    if missing:
        logger.error("Missing required environment variables", missing=missing)
        print(f"Error: Missing environment variables: {', '.join(missing)}")
        print("Set them in your environment or .env.local file")
        sys.exit(1)

    return alpaca_key, alpaca_secret


def fetch_hourly_data(
    client: StockHistoricalDataClient,
    symbols: list[str],
    start_date: datetime,
    end_date: datetime,
) -> dict[str, list[dict[str, float | str]]]:
    """Fetch hourly bar data from Alpaca.

    Args:
        client: Alpaca historical data client
        symbols: List of symbols to fetch
        start_date: Start date for data fetch
        end_date: End date for data fetch

    Returns:
        Dictionary mapping symbols to list of bar dictionaries with keys:
        timestamp, open, high, low, close, volume

    """
    logger.info(
        "Fetching hourly data",
        symbols=symbols,
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
    )

    request = StockBarsRequest(
        symbol_or_symbols=symbols,
        timeframe=TimeFrame.Hour,
        start=start_date,
        end=end_date,
    )

    try:
        bars_response = client.get_stock_bars(request)
        result: dict[str, list[dict[str, float | str]]] = {}

        for symbol in symbols:
            if symbol in bars_response.data:
                bars = bars_response.data[symbol]
                result[symbol] = [
                    {
                        "timestamp": bar.timestamp.isoformat(),
                        "open": float(bar.open),
                        "high": float(bar.high),
                        "low": float(bar.low),
                        "close": float(bar.close),
                        "volume": float(bar.volume),
                    }
                    for bar in bars
                ]
                logger.info(f"Fetched {len(result[symbol])} bars for {symbol}")
            else:
                result[symbol] = []
                logger.warning(f"No data available for {symbol}")

        return result

    except Exception as e:
        logger.error("Failed to fetch hourly data", error=str(e), exc_info=True)
        raise


def calculate_hourly_statistics(
    bars: list[dict[str, float | str]],
) -> dict[int, dict[str, float]]:
    """Calculate average gain/loss for each hour of the trading day.

    Args:
        bars: List of bar dictionaries with timestamp, open, close

    Returns:
        Dictionary mapping hour (0-23) to statistics:
        - avg_gain_pct: Average percentage gain for that hour
        - total_count: Number of observations
        - positive_count: Number of positive movements
        - negative_count: Number of negative movements

    """
    hourly_gains: dict[int, list[float]] = {}

    for bar in bars:
        # Parse timestamp and extract hour
        # Note: Alpaca returns UTC timestamps
        timestamp_str = bar["timestamp"]
        if isinstance(timestamp_str, str):
            # Parse ISO format timestamp
            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        else:
            timestamp = timestamp_str  # type: ignore[assignment]

        # Extract hour in UTC (Alpaca returns UTC timestamps)
        hour = timestamp.hour

        # Calculate percentage gain for this bar
        open_price = Decimal(str(bar["open"]))
        close_price = Decimal(str(bar["close"]))

        if open_price > 0:
            gain_pct = float((close_price - open_price) / open_price * 100)

            if hour not in hourly_gains:
                hourly_gains[hour] = []
            hourly_gains[hour].append(gain_pct)

    # Calculate statistics for each hour
    statistics: dict[int, dict[str, float]] = {}
    for hour, gains in hourly_gains.items():
        if gains:
            avg_gain = sum(gains) / len(gains)
            positive_count = sum(1 for g in gains if g > 0)
            negative_count = sum(1 for g in gains if g < 0)

            statistics[hour] = {
                "avg_gain_pct": avg_gain,
                "total_count": float(len(gains)),
                "positive_count": float(positive_count),
                "negative_count": float(negative_count),
            }

    return statistics


def format_report(
    symbol: str,
    statistics: dict[int, dict[str, float]],
    lookback_years: int,
) -> str:
    """Format statistics as human-readable report.

    Args:
        symbol: Symbol being analyzed
        statistics: Hourly statistics dictionary
        lookback_years: Number of years analyzed

    Returns:
        Formatted report string

    """
    lines = []
    lines.append("=" * 80)
    lines.append(f"HOURLY GAIN/LOSS ANALYSIS: {symbol}")
    lines.append(f"Analysis Period: Last {lookback_years} years")
    lines.append("=" * 80)
    lines.append("")
    lines.append(
        f"{'Hour (UTC)':<12} {'Avg Gain %':<12} {'Total Bars':<12} "
        f"{'Positive':<12} {'Negative':<12}"
    )
    lines.append("-" * 80)

    # Sort by hour
    for hour in sorted(statistics.keys()):
        stats = statistics[hour]
        lines.append(
            f"{hour:02d}:00-{hour:02d}:59   "
            f"{stats['avg_gain_pct']:>10.4f}%  "
            f"{int(stats['total_count']):>10}   "
            f"{int(stats['positive_count']):>10}   "
            f"{int(stats['negative_count']):>10}"
        )

    lines.append("=" * 80)
    lines.append("")

    # Find best and worst hours
    if statistics:
        best_hour = max(statistics.items(), key=lambda x: x[1]["avg_gain_pct"])
        worst_hour = min(statistics.items(), key=lambda x: x[1]["avg_gain_pct"])

        lines.append("KEY INSIGHTS:")
        lines.append(
            f"  • Best hour: {best_hour[0]:02d}:00-{best_hour[0]:02d}:59 "
            f"(avg {best_hour[1]['avg_gain_pct']:.4f}%)"
        )
        lines.append(
            f"  • Worst hour: {worst_hour[0]:02d}:00-{worst_hour[0]:02d}:59 "
            f"(avg {worst_hour[1]['avg_gain_pct']:.4f}%)"
        )
        lines.append("")

    return "\n".join(lines)


def save_csv_report(
    symbol: str,
    statistics: dict[int, dict[str, float]],
    output_path: Path,
) -> None:
    """Save statistics as CSV file.

    Args:
        symbol: Symbol being analyzed
        statistics: Hourly statistics dictionary
        output_path: Path to save CSV file

    """
    with output_path.open("w", newline="") as csvfile:
        fieldnames = [
            "hour_utc",
            "avg_gain_pct",
            "total_count",
            "positive_count",
            "negative_count",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for hour in sorted(statistics.keys()):
            stats = statistics[hour]
            writer.writerow(
                {
                    "hour_utc": hour,
                    "avg_gain_pct": stats["avg_gain_pct"],
                    "total_count": int(stats["total_count"]),
                    "positive_count": int(stats["positive_count"]),
                    "negative_count": int(stats["negative_count"]),
                }
            )

    logger.info(f"CSV report saved to {output_path}")


def main() -> int:
    """Main entry point for hourly gain analysis.

    Returns:
        Exit code (0 for success, 1 for error)

    """
    parser = argparse.ArgumentParser(
        description="Analyze hourly gain/loss patterns for stocks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--symbols",
        "-s",
        nargs="+",
        default=["SPY", "QQQ"],
        help="Symbols to analyze (default: SPY QQQ)",
    )

    parser.add_argument(
        "--years",
        "-y",
        type=int,
        default=10,
        help="Number of years to analyze (default: 10)",
    )

    parser.add_argument(
        "--format",
        "-f",
        choices=["text", "csv", "both"],
        default="text",
        help="Output format (default: text)",
    )

    parser.add_argument(
        "--output-dir",
        "-o",
        type=str,
        default="results",
        help="Output directory for reports (default: results)",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )

    args = parser.parse_args()

    # Validate environment
    api_key, secret_key = validate_environment()

    # Calculate date range (accounting for leap years)
    desired_end = datetime.now(UTC)

    # Alpaca subscriptions often disallow querying very recent SIP data.
    # Clip the end_date to `now - safety_window` to avoid 403 errors
    # (e.g., "subscription does not permit querying recent SIP data").
    safety_window = timedelta(minutes=15)
    end_date = desired_end - safety_window

    # Use 365.25 days per year to account for leap years
    days_back = int(args.years * 365.25)
    start_date = end_date - timedelta(days=days_back)

    # If the requested lookback is too small and start >= end after clipping,
    # expand the window to at least one day to ensure a valid range.
    if start_date >= end_date:
        logger.warning(
            "Adjusted start_date because end_date was clipped to avoid recent data window",
            original_start=(desired_end - timedelta(days=days_back)).isoformat(),
            adjusted_start=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )
        # Ensure at least 1 day of data
        start_date = end_date - timedelta(days=1)
        print(
            "Note: end date clipped to avoid recent SIP data (last 15 minutes)."
            " Adjusted start date to ensure valid range."
        )

    print("=" * 80)
    print("HOURLY GAIN/LOSS ANALYSIS")
    print("=" * 80)
    print(f"Symbols: {', '.join(args.symbols)}")
    print(f"Period: {start_date.date()} to {end_date.date()} ({args.years} years)")
    print(f"Output format: {args.format}")
    print("=" * 80)
    print()

    # Create Alpaca client
    try:
        client = StockHistoricalDataClient(api_key=api_key, secret_key=secret_key)
    except Exception as e:
        logger.error("Failed to create Alpaca client", error=str(e))
        print(f"Error: Failed to create Alpaca client: {e}")
        return 1

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Process each symbol
    for symbol in args.symbols:
        try:
            print(f"Analyzing {symbol}...")

            # Fetch hourly data
            data = fetch_hourly_data(client, [symbol], start_date, end_date)

            if not data.get(symbol):
                print(f"  Warning: No data available for {symbol}")
                continue

            # Calculate statistics
            statistics = calculate_hourly_statistics(data[symbol])

            if not statistics:
                print(f"  Warning: Could not calculate statistics for {symbol}")
                continue

            # Output results
            if args.format in ["text", "both"]:
                report = format_report(symbol, statistics, args.years)
                print(report)

            if args.format in ["csv", "both"]:
                csv_path = output_dir / f"hourly_analysis_{symbol.lower()}.csv"
                save_csv_report(symbol, statistics, csv_path)
                print(f"  CSV report saved to: {csv_path}")

        except Exception as e:
            logger.error(f"Failed to analyze {symbol}", error=str(e), exc_info=True)
            print(f"  Error analyzing {symbol}: {e}")
            continue

    print()
    print("Analysis complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
