#!/usr/bin/env python3
"""Business Unit: backtest | Status: current.

CLI script for running backtests on DSL strategies.

Provides a command-line interface for backtesting .clj strategy files
or entire portfolios (from config JSON) against historical market data.

Usage:
    # Single strategy
    python scripts/run_backtest.py strategies/core/main.clj \\
        --start 2023-01-01 --end 2024-01-01 \\
        --capital 100000 --output results/backtest.json

    # Portfolio from config file
    python scripts/run_backtest.py the_alchemiser/config/strategy.dev.json \\
        --portfolio --start 2024-01-01 --end 2024-12-01

"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from the_alchemiser.backtest_v2 import BacktestConfig, BacktestEngine
from the_alchemiser.backtest_v2.core.portfolio_engine import (
    PortfolioBacktestConfig,
    PortfolioBacktestEngine,
)
from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)


def parse_date(date_str: str) -> datetime:
    """Parse date string to timezone-aware datetime.

    Args:
        date_str: Date in YYYY-MM-DD format

    Returns:
        Timezone-aware datetime (UTC)

    """
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.replace(tzinfo=UTC)


def main() -> int:
    """Run backtest from command line arguments.

    Returns:
        Exit code (0 for success, 1 for error)

    """
    parser = argparse.ArgumentParser(
        description="Backtest DSL strategies against historical market data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Single strategy backtest
    python scripts/run_backtest.py strategies/core/main.clj --start 2023-01-01 --end 2024-01-01

    # Portfolio backtest from config file
    python scripts/run_backtest.py the_alchemiser/config/strategy.dev.json \\
        --portfolio --start 2024-01-01 --end 2024-12-01

    # With custom capital and output
    python scripts/run_backtest.py strategies/core/main.clj \\
        --start 2023-01-01 --end 2024-01-01 \\
        --capital 50000 --output results/my_backtest.json

    # Adjust slippage
    python scripts/run_backtest.py strategies/core/main.clj \\
        --start 2023-01-01 --end 2024-01-01 \\
        --slippage 10
        """,
    )

    parser.add_argument(
        "strategy",
        type=str,
        help="Path to .clj strategy file OR .json portfolio config file (with --portfolio)",
    )

    parser.add_argument(
        "--portfolio",
        "-p",
        action="store_true",
        help="Run portfolio backtest using JSON config file with strategy allocations",
    )

    parser.add_argument(
        "--start",
        type=str,
        required=True,
        help="Backtest start date (YYYY-MM-DD)",
    )

    parser.add_argument(
        "--end",
        type=str,
        required=True,
        help="Backtest end date (YYYY-MM-DD)",
    )

    parser.add_argument(
        "--capital",
        type=float,
        default=100_000,
        help="Initial capital (default: 100000)",
    )

    parser.add_argument(
        "--data-dir",
        type=str,
        default="data/historical",
        help="Path to historical data directory (default: data/historical)",
    )

    parser.add_argument(
        "--strategies-dir",
        type=str,
        default="the_alchemiser/strategy_v2/strategies",
        help="Base directory for strategy files (default: the_alchemiser/strategy_v2/strategies)",
    )

    parser.add_argument(
        "--slippage",
        type=float,
        default=5,
        help="Slippage in basis points (default: 5 = 0.05%%)",
    )

    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Output file path for JSON results (optional)",
    )

    parser.add_argument(
        "--csv",
        type=str,
        help="Output file path for equity curve CSV (optional)",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )

    args = parser.parse_args()

    # Validate input file
    input_path = Path(args.strategy)
    if not input_path.exists():
        print(f"Error: File not found: {input_path}", file=sys.stderr)
        return 1

    # Validate data directory
    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        print(f"Error: Data directory not found: {data_dir}", file=sys.stderr)
        return 1

    # Parse dates
    try:
        start_date = parse_date(args.start)
        end_date = parse_date(args.end)
    except ValueError as e:
        print(f"Error: Invalid date format. Use YYYY-MM-DD. {e}", file=sys.stderr)
        return 1

    # Route to portfolio or single strategy backtest
    if args.portfolio:
        return run_portfolio_backtest_cli(args, input_path, start_date, end_date, data_dir)
    else:
        return run_single_strategy_backtest(args, input_path, start_date, end_date, data_dir)


def run_portfolio_backtest_cli(
    args: argparse.Namespace,
    config_path: Path,
    start_date: datetime,
    end_date: datetime,
    data_dir: Path,
) -> int:
    """Run portfolio backtest from config file.

    Args:
        args: Parsed command line arguments
        config_path: Path to portfolio config JSON
        start_date: Backtest start date
        end_date: Backtest end date
        data_dir: Historical data directory

    Returns:
        Exit code

    """
    # Create portfolio configuration
    try:
        config = PortfolioBacktestConfig.from_config_file(
            config_path=config_path,
            start_date=start_date,
            end_date=end_date,
            initial_capital=args.capital,
            data_dir=data_dir,
            strategies_base_dir=args.strategies_dir,
            slippage_bps=args.slippage,
        )
    except (ValueError, FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error: Invalid portfolio configuration: {e}", file=sys.stderr)
        return 1

    # Print configuration
    print("=" * 70)
    print("PORTFOLIO BACKTEST CONFIGURATION")
    print("=" * 70)
    print(f"Config File:     {config_path}")
    print(f"Strategies:      {len(config.strategies)}")
    print(f"Start Date:      {start_date.date()}")
    print(f"End Date:        {end_date.date()}")
    print(f"Initial Capital: ${args.capital:,.2f}")
    print(f"Slippage:        {args.slippage} bps")
    print(f"Data Directory:  {data_dir}")
    print("-" * 70)
    print("Strategy Allocations:")
    for s in config.strategies:
        print(f"  {s.name or s.strategy_path}: {float(s.weight) * 100:.1f}%")
    print("=" * 70)
    print()

    # Run backtest
    try:
        engine = PortfolioBacktestEngine(config)
        result = engine.run()
    except Exception as e:
        print(f"Error: Portfolio backtest failed: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

    # Print summary
    print(result.summary())

    # Save JSON output if requested
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(result.to_dict(), f, indent=2, default=str)

        print(f"\nResults saved to: {output_path}")

    # Save CSV equity curve if requested
    if args.csv:
        csv_path = Path(args.csv)
        csv_path.parent.mkdir(parents=True, exist_ok=True)

        # Combine portfolio and benchmark curves
        combined = result.equity_curve.copy()
        if not result.benchmark_curve.empty:
            combined["benchmark"] = result.benchmark_curve["close"]
        combined.to_csv(csv_path)

        print(f"Equity curve saved to: {csv_path}")

    # Print errors if any
    if result.errors:
        print(f"\nWarning: {len(result.errors)} evaluation errors occurred.")
        if args.verbose:
            for err in result.errors[:10]:  # Show first 10
                strategy = err.get("strategy", "unknown")
                print(f"  - [{strategy}] {err['date']}: {err['error']}")
            if len(result.errors) > 10:
                print(f"  ... and {len(result.errors) - 10} more")

    return 0


def run_single_strategy_backtest(
    args: argparse.Namespace,
    strategy_path: Path,
    start_date: datetime,
    end_date: datetime,
    data_dir: Path,
) -> int:
    """Run single strategy backtest.

    Args:
        args: Parsed command line arguments
        strategy_path: Path to strategy file
        start_date: Backtest start date
        end_date: Backtest end date
        data_dir: Historical data directory

    Returns:
        Exit code

    """

    # Create configuration
    try:
        config = BacktestConfig(
            strategy_path=strategy_path,
            start_date=start_date,
            end_date=end_date,
            initial_capital=Decimal(str(args.capital)),
            data_dir=data_dir,
            slippage_bps=Decimal(str(args.slippage)),
        )
    except ValueError as e:
        print(f"Error: Invalid configuration: {e}", file=sys.stderr)
        return 1

    # Print configuration
    print("=" * 60)
    print("BACKTEST CONFIGURATION")
    print("=" * 60)
    print(f"Strategy:        {strategy_path}")
    print(f"Start Date:      {start_date.date()}")
    print(f"End Date:        {end_date.date()}")
    print(f"Initial Capital: ${args.capital:,.2f}")
    print(f"Slippage:        {args.slippage} bps")
    print(f"Data Directory:  {data_dir}")
    print("=" * 60)
    print()

    # Run backtest
    try:
        engine = BacktestEngine(config)
        result = engine.run()
    except Exception as e:
        print(f"Error: Backtest failed: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1

    # Print summary
    print(result.summary())

    # Save JSON output if requested
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(result.to_dict(), f, indent=2, default=str)

        print(f"\nResults saved to: {output_path}")

    # Save CSV equity curve if requested
    if args.csv:
        csv_path = Path(args.csv)
        csv_path.parent.mkdir(parents=True, exist_ok=True)

        # Combine strategy and benchmark curves
        combined = result.equity_curve.copy()
        combined["benchmark"] = result.benchmark_curve["close"]
        combined.to_csv(csv_path)

        print(f"Equity curve saved to: {csv_path}")

    # Print errors if any
    if result.errors:
        print(f"\nWarning: {len(result.errors)} evaluation errors occurred.")
        if args.verbose:
            for err in result.errors[:5]:  # Show first 5
                print(f"  - {err['date']}: {err['error']}")
            if len(result.errors) > 5:
                print(f"  ... and {len(result.errors) - 5} more")

    return 0


if __name__ == "__main__":
    sys.exit(main())
