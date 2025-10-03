#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

CLI entry point for backtesting system.
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime, timedelta

from scripts.backtest.analysis.reporting import print_report
from scripts.backtest.backtest_runner import BacktestRunner
from scripts.backtest.data_manager import DataManager
from scripts.backtest.storage.data_store import DataStore


def download_data(args: argparse.Namespace) -> int:
    """Download historical data for backtesting.
    
    Args:
        args: Command-line arguments
        
    Returns:
        Exit code (0 for success)

    """
    print("📥 Downloading historical data...")

    # Get symbols from strategy config or use defaults
    symbols = args.symbols or ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA"]
    lookback_days = args.lookback or 365

    try:
        manager = DataManager()
        results = manager.download_lookback(
            symbols=symbols,
            lookback_days=lookback_days,
            force_refresh=args.force,
        )

        print("\n✅ Download complete:")
        for symbol, count in results.items():
            print(f"  {symbol}: {count} bars")

        return 0

    except Exception as e:
        print(f"❌ Error downloading data: {e}")
        return 1


def run_backtest(args: argparse.Namespace) -> int:
    """Run backtest.
    
    Args:
        args: Command-line arguments
        
    Returns:
        Exit code (0 for success)

    """
    print("📈 Running backtest...")

    # Parse dates
    if args.start and args.end:
        start_date = datetime.fromisoformat(args.start).replace(tzinfo=UTC)
        end_date = datetime.fromisoformat(args.end).replace(tzinfo=UTC)
    else:
        # Default: 1 year lookback
        end_date = datetime.now(UTC)
        start_date = end_date - timedelta(days=365)

    # Get strategy config
    strategy_path = args.strategy or "strategies/KLM.clj"
    
    # Get symbols
    symbols = args.symbols or ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA"]

    print(f"Period: {start_date.date()} to {end_date.date()}")
    print(f"Strategy: {strategy_path}")
    print(f"Symbols: {', '.join(symbols)}")
    print()

    try:
        # Initialize components
        data_store = DataStore()
        runner = BacktestRunner(
            strategy_config_path=strategy_path,
            data_store=data_store,
        )

        # Run backtest
        result = runner.run(start_date, end_date, symbols)

        # Print results
        print()
        print_report(result)

        return 0

    except Exception as e:
        print(f"❌ Error running backtest: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main() -> int:
    """Main CLI entry point.
    
    Returns:
        Exit code

    """
    parser = argparse.ArgumentParser(
        description="Historical Backtesting System for The Alchemiser"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Download command
    download_parser = subparsers.add_parser(
        "download", help="Download historical data"
    )
    download_parser.add_argument(
        "--symbols",
        nargs="+",
        help="Symbols to download (default: AAPL GOOGL MSFT TSLA NVDA)",
    )
    download_parser.add_argument(
        "--lookback",
        type=int,
        default=365,
        help="Days of history to download (default: 365)",
    )
    download_parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-download even if data exists",
    )

    # Run command
    run_parser = subparsers.add_parser("run", help="Run backtest")
    run_parser.add_argument(
        "--start", help="Start date (YYYY-MM-DD)", required=False
    )
    run_parser.add_argument(
        "--end", help="End date (YYYY-MM-DD)", required=False
    )
    run_parser.add_argument(
        "--strategy",
        help="Path to strategy .clj file (default: strategies/KLM.clj)",
    )
    run_parser.add_argument(
        "--symbols",
        nargs="+",
        help="Symbols to trade (default: AAPL GOOGL MSFT TSLA NVDA)",
    )

    args = parser.parse_args()

    if args.command == "download":
        return download_data(args)
    if args.command == "run":
        return run_backtest(args)
    
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
