#!/usr/bin/env python3
"""Business Unit: backtest | Status: current.

CLI script for fetching historical market data for backtesting.

Fetch data from Alpaca and store locally as Parquet files for use in
backtesting. Supports fetching specific symbols, extracting symbols from
strategy files, or refreshing all local data.

Usage:
    # Fetch specific symbols
    python scripts/fetch_backtest_data.py --symbols SPY AAPL QQQ

    # Fetch symbols from a strategy file
    python scripts/fetch_backtest_data.py --strategy strategies/core/main.clj

    # Fetch symbols from portfolio config
    python scripts/fetch_backtest_data.py --portfolio the_alchemiser/config/strategy.dev.json

    # Refresh all existing local data
    python scripts/fetch_backtest_data.py --refresh

    # Check which symbols are missing
    python scripts/fetch_backtest_data.py --check --strategy strategies/core/main.clj
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from the_alchemiser.backtest_v2.adapters.data_fetcher import (
    DEFAULT_LOOKBACK_DAYS,
    BacktestDataFetcher,
)
from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)

# Common benchmark and reference symbols
BENCHMARK_SYMBOLS = ["SPY", "AGG", "BND", "BIL"]


def extract_symbols_from_clj(strategy_path: Path) -> set[str]:
    """Extract ticker symbols from a .clj strategy file.

    Args:
        strategy_path: Path to the strategy file

    Returns:
        Set of ticker symbols found in the file

    """
    symbols: set[str] = set()

    if not strategy_path.exists():
        return symbols

    content = strategy_path.read_text()

    # Pattern for symbols in quotes: "SPY", "AAPL", etc.
    quote_pattern = r'"([A-Z]{1,5})"'
    symbols.update(re.findall(quote_pattern, content))

    # Pattern for :symbol keywords: :symbol "SPY"
    symbol_pattern = r':symbol\s+"([A-Z]{1,5})"'
    symbols.update(re.findall(symbol_pattern, content))

    # Pattern for symbols in function calls: (avg "SPY" ...)
    func_pattern = r'\(\s*(?:avg|sma|ema|rsi|momentum|price|close|volatility)\s+"([A-Z]{1,5})"'
    symbols.update(re.findall(func_pattern, content))

    return symbols


def extract_symbols_from_portfolio_config(config_path: Path) -> set[str]:
    """Extract all symbols from a portfolio config file.

    Loads the config and extracts symbols from all referenced strategy files.

    Args:
        config_path: Path to the portfolio JSON config

    Returns:
        Set of ticker symbols needed

    """
    symbols: set[str] = set()

    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}", file=sys.stderr)
        return symbols

    with config_path.open() as f:
        config = json.load(f)

    # Get strategies base directory
    strategies = config.get("strategies", [])
    strategies_base = Path("the_alchemiser/strategy_v2/strategies")

    for strategy_config in strategies:
        dsl_file = strategy_config.get("dsl_file", "")
        if dsl_file:
            strategy_path = strategies_base / dsl_file
            if strategy_path.exists():
                symbols.update(extract_symbols_from_clj(strategy_path))

    return symbols


def main() -> int:
    """Run data fetch from command line arguments.

    Returns:
        Exit code (0 for success, 1 for error)

    """
    parser = argparse.ArgumentParser(
        description="Fetch historical market data for backtesting",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Fetch specific symbols
    python scripts/fetch_backtest_data.py --symbols SPY AAPL QQQ

    # Fetch symbols from a strategy file
    python scripts/fetch_backtest_data.py --strategy strategies/core/main.clj

    # Fetch symbols from portfolio config
    python scripts/fetch_backtest_data.py --portfolio the_alchemiser/config/strategy.dev.json

    # Refresh all existing local data
    python scripts/fetch_backtest_data.py --refresh

    # Check which symbols are missing
    python scripts/fetch_backtest_data.py --check --strategy strategies/core/main.clj

    # Force full refresh (not incremental)
    python scripts/fetch_backtest_data.py --symbols SPY --full

Environment Variables:
    ALPACA__KEY     - Alpaca API key
    ALPACA__SECRET  - Alpaca API secret
        """,
    )

    # Symbol sources (mutually exclusive)
    source_group = parser.add_mutually_exclusive_group()

    source_group.add_argument(
        "--symbols",
        "-s",
        nargs="+",
        help="List of ticker symbols to fetch",
    )

    source_group.add_argument(
        "--strategy",
        type=str,
        help="Extract symbols from a .clj strategy file",
    )

    source_group.add_argument(
        "--portfolio",
        "-p",
        type=str,
        help="Extract symbols from all strategies in a portfolio config JSON",
    )

    source_group.add_argument(
        "--refresh",
        action="store_true",
        help="Refresh all existing local data",
    )

    # Options
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data/historical",
        help="Path to historical data directory (default: data/historical)",
    )

    parser.add_argument(
        "--lookback",
        type=int,
        default=DEFAULT_LOOKBACK_DAYS,
        help=f"Days of history to fetch for new symbols (default: {DEFAULT_LOOKBACK_DAYS})",
    )

    parser.add_argument(
        "--full",
        "-f",
        action="store_true",
        help="Force full data fetch (not incremental)",
    )

    parser.add_argument(
        "--check",
        "-c",
        action="store_true",
        help="Only check which symbols are missing (no fetch)",
    )

    parser.add_argument(
        "--include-benchmarks",
        "-b",
        action="store_true",
        help="Include benchmark symbols (SPY, AGG, BND, BIL)",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )

    args = parser.parse_args()

    # Check for API credentials (combine nested if)
    if not args.check and (
        not os.environ.get("ALPACA__KEY") or not os.environ.get("ALPACA__SECRET")
    ):
        print("Error: Alpaca credentials not set.", file=sys.stderr)
        print("Set ALPACA__KEY and ALPACA__SECRET environment variables.", file=sys.stderr)
        return 1

    # Collect symbols based on source
    symbols: set[str] = set()

    if args.symbols:
        symbols.update(s.upper() for s in args.symbols)

    elif args.strategy:
        strategy_path = Path(args.strategy)
        if not strategy_path.exists():
            print(f"Error: Strategy file not found: {strategy_path}", file=sys.stderr)
            return 1
        symbols.update(extract_symbols_from_clj(strategy_path))
        if args.verbose:
            print(f"Extracted {len(symbols)} symbols from {strategy_path}")

    elif args.portfolio:
        config_path = Path(args.portfolio)
        if not config_path.exists():
            print(f"Error: Portfolio config not found: {config_path}", file=sys.stderr)
            return 1
        symbols.update(extract_symbols_from_portfolio_config(config_path))
        if args.verbose:
            print(f"Extracted {len(symbols)} symbols from portfolio config")

    elif args.refresh:
        # Will be populated from existing data
        pass

    else:
        parser.print_help()
        return 1

    # Add benchmark symbols if requested
    if args.include_benchmarks:
        symbols.update(BENCHMARK_SYMBOLS)

    # Initialize fetcher
    data_dir = Path(args.data_dir)
    fetcher = BacktestDataFetcher(data_dir=data_dir)

    # Handle refresh mode
    if args.refresh:
        symbols.update(fetcher.get_available_symbols())

    if not symbols:
        print("No symbols to fetch.", file=sys.stderr)
        return 1

    # Check mode
    if args.check:
        missing = fetcher.get_missing_symbols(list(symbols))
        print("=" * 60)
        print("DATA AVAILABILITY CHECK")
        print("=" * 60)
        print(f"Required symbols: {len(symbols)}")
        print(f"Available locally: {len(symbols) - len(missing)}")
        print(f"Missing: {len(missing)}")

        if missing:
            print("-" * 60)
            print("Missing symbols:")
            for sym in sorted(missing):
                print(f"  {sym}")

        # Also check freshness of existing data
        stale = []
        for sym in symbols:
            if sym not in missing and not fetcher.check_data_freshness(sym, max_age_days=7):
                stale.append(sym)

        if stale:
            print("-" * 60)
            print(f"Stale data (>7 days old): {len(stale)}")
            for sym in sorted(stale)[:20]:
                print(f"  {sym}")
            if len(stale) > 20:
                print(f"  ... and {len(stale) - 20} more")

        print("=" * 60)
        return 0

    # Fetch mode
    print("=" * 60)
    print("FETCH BACKTEST DATA")
    print("=" * 60)
    print(f"Symbols to fetch: {len(symbols)}")
    print(f"Data directory: {data_dir}")
    print(f"Lookback days: {args.lookback}")
    print(f"Mode: {'Full' if args.full else 'Incremental'}")
    print("=" * 60)

    if args.verbose:
        print("Symbols:", ", ".join(sorted(symbols)))
        print("-" * 60)

    # Run fetch
    results = fetcher.fetch_symbols(
        symbols=list(symbols),
        lookback_days=args.lookback,
        force_full=args.full,
    )

    # Print summary
    success_count = sum(results.values())
    failed_symbols = [s for s, ok in results.items() if not ok]

    print()
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Total: {len(results)}")
    print(f"Success: {success_count}")
    print(f"Failed: {len(failed_symbols)}")

    if failed_symbols:
        print("-" * 60)
        print("Failed symbols:")
        for sym in sorted(failed_symbols):
            print(f"  {sym}")

    print("=" * 60)

    return 0 if not failed_symbols else 1


if __name__ == "__main__":
    sys.exit(main())
