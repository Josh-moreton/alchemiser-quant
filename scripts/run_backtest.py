#!/usr/bin/env python3
r"""Business Unit: backtest | Status: current.

CLI script for running backtests on DSL strategies.

Provides a command-line interface for backtesting .clj strategy files
or entire portfolios (from config JSON) against historical market data.

Usage:
    # Single strategy
    python scripts/run_backtest.py strategies/core/main.clj \
        --start 2025-01-01 --end 2025-12-01 \
        --capital 100000 --output results/backtest.json

    # Portfolio from config file
    python scripts/run_backtest.py the_alchemiser/config/strategy.dev.json \
        --portfolio --start 2025-01-01 --end 2025-12-01

    # Auto-fetch missing data before running
    python scripts/run_backtest.py strategies/core/main.clj \
        --start 2023-01-01 --end 2024-01-01 --fetch-data

"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
import logging

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def _load_local_env_files() -> None:
    """Load environment variables from .env in project root.

    This helper is intentionally simple: it accepts lines of the form
    KEY=VALUE and skips comments/blank lines. Existing environment
    variables are not overwritten.
    """
    env_files = [project_root / ".env"]
    for ef in env_files:
        if not ef.exists():
            continue
        try:
            for raw in ef.read_text().splitlines():
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip()
                # Strip optional surrounding quotes
                if (val.startswith('"') and val.endswith('"')) or (
                    val.startswith("'") and val.endswith("'")
                ):
                    val = val[1:-1]
                # Only set if not already present in environment
                if key and os.environ.get(key) is None:
                    os.environ[key] = val
        except Exception:
            # Non-fatal: continue with available env vars
            continue


# Load .env early so CLI --auto-fetch and other features
# can pick up credentials from .env automatically.
_load_local_env_files()

# Create logs directory early (file handler added after imports)
logs_dir = project_root / "logs"
logs_dir.mkdir(parents=True, exist_ok=True)
_ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
_logfile = logs_dir / f"backtest_{_ts}.log"

from the_alchemiser.backtest_v2 import BacktestConfig, BacktestEngine
from the_alchemiser.backtest_v2.core.portfolio_engine import (
    PortfolioBacktestConfig,
    PortfolioBacktestEngine,
)
from the_alchemiser.shared.logging import configure_structlog_lambda, get_logger

# Configure structlog to use stdlib logging (required for file handler to work)
configure_structlog_lambda()

# Add file handler to capture logs to file
# This works because configure_structlog_lambda sets up stdlib logging integration
try:
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Ensure all levels are captured
    _fh = logging.FileHandler(_logfile, encoding="utf-8")
    _fh.setLevel(logging.DEBUG)  # Capture all levels to file
    _fh.setFormatter(logging.Formatter("%(message)s"))  # Keep JSON format from structlog
    root_logger.addHandler(_fh)
    print(f"Backtest logs will be written to: {_logfile}")
except Exception:
    # Non-fatal: continue without file logging
    pass

logger = get_logger(__name__)

# Benchmark symbols always needed
BENCHMARK_SYMBOLS = ["SPY"]

# Default results directory for reports
RESULTS_DIR = project_root / "results"


def _generate_report(
    result: object,
    path_arg: str,
    report_type: str,
    strategy_name: str,
) -> None:
    """Generate HTML or PDF report.

    Args:
        result: BacktestResult or PortfolioBacktestResult
        path_arg: Path argument from CLI ("auto" for default, or specific path)
        report_type: "html" or "pdf"
        strategy_name: Strategy name for default filename

    """
    try:
        from the_alchemiser.backtest_v2.reporting import generate_report
    except ImportError as e:
        print(f"Warning: Could not import reporting module: {e}", file=sys.stderr)
        print("Install matplotlib with: poetry install --with dev", file=sys.stderr)
        return

    # Determine output path
    if path_arg == "auto":
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        safe_name = re.sub(r"[^\w\-]", "_", strategy_name)
        filename = f"backtest_{safe_name}_{ts}.{report_type}"
        output_path = RESULTS_DIR / filename
    else:
        output_path = Path(path_arg)
        output_path.parent.mkdir(parents=True, exist_ok=True)

    # Generate report
    try:
        if report_type == "html":
            generate_report(result, output_path)
            print(f"\n📊 HTML report saved to: {output_path}")
        else:
            # PDF not yet supported for portfolio results
            if hasattr(result, "strategy_results"):
                print("Warning: PDF reports not yet supported for portfolio results. Use --report for HTML.", file=sys.stderr)
                return
            from the_alchemiser.backtest_v2.reporting import generate_pdf_report
            generate_pdf_report(result, output_path)
            print(f"\n📄 PDF report saved to: {output_path}")
    except Exception as e:
        print(f"Warning: Failed to generate {report_type.upper()} report: {e}", file=sys.stderr)


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

    return symbols


def extract_symbols_from_portfolio_config(
    config_path: Path,
    strategies_base_dir: str,
) -> set[str]:
    """Extract all symbols from a portfolio config file.

    Args:
        config_path: Path to the portfolio JSON config
        strategies_base_dir: Base directory for strategy files

    Returns:
        Set of ticker symbols needed

    """
    symbols: set[str] = set()

    if not config_path.exists():
        return symbols

    with config_path.open() as f:
        config = json.load(f)

    strategies = config.get("strategies", [])
    strategies_base = Path(strategies_base_dir)

    for strategy_config in strategies:
        dsl_file = strategy_config.get("dsl_file", "")
        if dsl_file:
            strategy_path = strategies_base / dsl_file
            if strategy_path.exists():
                symbols.update(extract_symbols_from_clj(strategy_path))

    return symbols


def fetch_missing_data(
    args: argparse.Namespace,
    input_path: Path,
    data_dir: Path,
) -> int:
    """Fetch missing market data for backtest.

    Args:
        args: Parsed command line arguments
        input_path: Path to strategy or config file
        data_dir: Historical data directory

    Returns:
        Exit code (0 for success, non-zero for error)

    """
    from the_alchemiser.backtest_v2.adapters.data_fetcher import BacktestDataFetcher

    # Check for API credentials
    if not os.environ.get("ALPACA__KEY") or not os.environ.get("ALPACA__SECRET"):
        print("Error: Alpaca credentials not set for --fetch-data.", file=sys.stderr)
        print("Set ALPACA__KEY and ALPACA__SECRET environment variables.", file=sys.stderr)
        return 1

    # Extract symbols
    symbols: set[str] = set()

    if args.portfolio:
        symbols.update(extract_symbols_from_portfolio_config(
            input_path,
            args.strategies_dir,
        ))
    else:
        symbols.update(extract_symbols_from_clj(input_path))

    # Always include benchmark
    symbols.update(BENCHMARK_SYMBOLS)

    if not symbols:
        print("Warning: No symbols extracted from strategy file.", file=sys.stderr)
        return 0

    # Initialize fetcher and check for missing data
    fetcher = BacktestDataFetcher(data_dir=data_dir)
    missing = fetcher.get_missing_symbols(list(symbols))

    if not missing:
        print("All required data is available locally.")
        return 0

    print(f"Fetching {len(missing)} missing symbols: {', '.join(sorted(missing)[:10])}")
    if len(missing) > 10:
        print(f"  ... and {len(missing) - 10} more")

    # Fetch missing data
    results = fetcher.fetch_symbols(list(missing))

    failed = [s for s, ok in results.items() if not ok]
    if failed:
        print(f"Warning: Failed to fetch {len(failed)} symbols: {', '.join(failed[:5])}")
        if args.verbose:
            for sym in failed:
                print(f"  - {sym}")

    return 0


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

    # Generate HTML report (auto-saved to results/)
    python scripts/run_backtest.py strategies/core/main.clj \\
        --start 2023-01-01 --end 2024-01-01 --report

    # Generate PDF report to specific path
    python scripts/run_backtest.py strategies/core/main.clj \\
        --start 2023-01-01 --end 2024-01-01 --pdf results/my_report.pdf
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
        "--fetch-data",
        action="store_true",
        help="Pre-fetch missing data before running backtest (one-time scan)",
    )

    parser.add_argument(
        "--auto-fetch",
        action="store_true",
        help="Auto-fetch missing symbols during backtest (on-the-fly)",
    )

    parser.add_argument(
        "--auto-fetch-lookback",
        type=int,
        default=600,
        help="Lookback days for auto-fetch (default: 600)",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )

    parser.add_argument(
        "--report",
        nargs="?",
        const="auto",
        default=None,
        metavar="PATH",
        help="Generate HTML report. If PATH not given, saves to results/backtest_<timestamp>.html",
    )

    parser.add_argument(
        "--pdf",
        nargs="?",
        const="auto",
        default=None,
        metavar="PATH",
        help="Generate PDF report. If PATH not given, saves to results/backtest_<timestamp>.pdf",
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
        # Create it if fetch-data is enabled
        if args.fetch_data:
            data_dir.mkdir(parents=True, exist_ok=True)
        else:
            print(f"Error: Data directory not found: {data_dir}", file=sys.stderr)
            return 1

    # Parse dates
    try:
        start_date = parse_date(args.start)
        end_date = parse_date(args.end)
    except ValueError as e:
        print(f"Error: Invalid date format. Use YYYY-MM-DD. {e}", file=sys.stderr)
        return 1

    # Fetch missing data if requested
    if args.fetch_data:
        fetch_result = fetch_missing_data(args, input_path, data_dir)
        if fetch_result != 0:
            return fetch_result

    # Route to portfolio or single strategy backtest
    if args.portfolio:
        return run_portfolio_backtest_cli(args, input_path, start_date, end_date, data_dir)
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
    # Check API credentials if auto-fetch is enabled
    if args.auto_fetch:
        if not os.environ.get("ALPACA__KEY") or not os.environ.get("ALPACA__SECRET"):
            print("Error: Alpaca credentials not set for --auto-fetch.", file=sys.stderr)
            print("Set ALPACA__KEY and ALPACA__SECRET environment variables.", file=sys.stderr)
            return 1

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
            auto_fetch_missing=args.auto_fetch,
            auto_fetch_lookback_days=args.auto_fetch_lookback,
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
    if args.auto_fetch:
        print(f"Auto-Fetch:      ENABLED (lookback: {args.auto_fetch_lookback} days)")
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

        with output_path.open("w") as f:
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

    # Generate HTML report if requested
    if args.report:
        _generate_report(result, args.report, "html", config_path.stem)

    # Generate PDF report if requested
    if args.pdf:
        _generate_report(result, args.pdf, "pdf", config_path.stem)

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
    # Check API credentials if auto-fetch is enabled
    if args.auto_fetch:
        if not os.environ.get("ALPACA__KEY") or not os.environ.get("ALPACA__SECRET"):
            print("Error: Alpaca credentials not set for --auto-fetch.", file=sys.stderr)
            print("Set ALPACA__KEY and ALPACA__SECRET environment variables.", file=sys.stderr)
            return 1

    # Create configuration
    try:
        config = BacktestConfig(
            strategy_path=strategy_path,
            start_date=start_date,
            end_date=end_date,
            initial_capital=Decimal(str(args.capital)),
            data_dir=data_dir,
            slippage_bps=Decimal(str(args.slippage)),
            auto_fetch_missing=args.auto_fetch,
            auto_fetch_lookback_days=args.auto_fetch_lookback,
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
    if args.auto_fetch:
        print(f"Auto-Fetch:      ENABLED (lookback: {args.auto_fetch_lookback} days)")
    print("=" * 60)
    print()

    # Run backtest
    try:
        engine = BacktestEngine(config)
        result = engine.run()

        # Report auto-fetched symbols if any
        if args.auto_fetch and engine._fetched_symbols:
            print(f"\n📥 Auto-fetched {len(engine._fetched_symbols)} symbols:")
            for sym in sorted(engine._fetched_symbols):
                print(f"   - {sym}")
            print()
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

        with output_path.open("w") as f:
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

    # Generate HTML report if requested
    if args.report:
        _generate_report(result, args.report, "html", strategy_path.stem)

    # Generate PDF report if requested
    if args.pdf:
        _generate_report(result, args.pdf, "pdf", strategy_path.stem)

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
