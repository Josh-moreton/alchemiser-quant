#!/usr/bin/env python3
"""Business Unit: scripts | Status: current.

CLI for running backtests.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

# Add project root to path
_project_root = Path(__file__).resolve().parents[1]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from scripts.backtest.backtest_runner import BacktestRunner
from scripts.backtest.models.backtest_result import BacktestConfig
from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)


def main() -> None:
    """Main entry point for backtesting."""
    parser = argparse.ArgumentParser(description="Run historical backtest")
    parser.add_argument(
        "--strategy",
        nargs="+",
        help="Strategy files to test",
        default=["KLM.clj"],
    )
    parser.add_argument(
        "--days",
        type=int,
        help="Number of days to backtest",
        default=14,
    )
    parser.add_argument(
        "--start-date",
        help="Start date (YYYY-MM-DD)",
        default=None,
    )
    parser.add_argument(
        "--end-date",
        help="End date (YYYY-MM-DD)",
        default="2025-10-02",
    )
    parser.add_argument(
        "--capital",
        type=float,
        help="Initial capital",
        default=100000.0,
    )
    parser.add_argument(
        "--commission",
        type=float,
        help="Commission per trade",
        default=0.0,
    )
    parser.add_argument(
        "--symbols",
        nargs="+",
        help="Symbols to trade (overrides strategy)",
        default=None,
    )

    args = parser.parse_args()

    # Parse dates
    if args.start_date and args.end_date:
        start_date = datetime.fromisoformat(args.start_date).replace(tzinfo=timezone.utc)
        end_date = datetime.fromisoformat(args.end_date).replace(tzinfo=timezone.utc)
    else:
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=args.days)

    logger.info(
        f"Starting backtest: {start_date.date()} to {end_date.date()}",
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
    )

    # Create backtest config
    config = BacktestConfig(
        strategy_files=args.strategy,
        start_date=start_date,
        end_date=end_date,
        initial_capital=Decimal(str(args.capital)),
        commission_per_trade=Decimal(str(args.commission)),
        symbols=args.symbols,
    )

    # Run backtest
    runner = BacktestRunner()
    result = runner.run_backtest(config)

    # Print results
    print("\n" + "=" * 80)
    print("BACKTEST RESULTS")
    print("=" * 80)
    print(f"\nStrategy: {result.strategy_name}")
    print(f"Period: {result.start_date.date()} to {result.end_date.date()}")
    print(f"Initial Capital: ${result.initial_capital:,.2f}")
    print(f"Final Value: ${result.final_value:,.2f}" if result.final_value else "Final Value: N/A")
    print(
        f"Total Return: {result.total_return:.2f}%" if result.total_return else "Total Return: N/A"
    )
    print(f"Total Trades: {result.total_trades}")
    print(f"\nPerformance Metrics:")
    print(
        f"  Sharpe Ratio: {result.sharpe_ratio:.2f}"
        if result.sharpe_ratio
        else "  Sharpe Ratio: N/A"
    )
    print(
        f"  Max Drawdown: {result.max_drawdown:.2f}%"
        if result.max_drawdown
        else "  Max Drawdown: N/A"
    )
    print(f"  Win Rate: {result.win_rate:.2f}%" if result.win_rate else "  Win Rate: N/A")
    print(f"\nPortfolio Snapshots: {len(result.portfolio_snapshots)}")

    if result.portfolio_snapshots:
        final_snapshot = result.portfolio_snapshots[-1]
        print(f"\nFinal Portfolio:")
        print(f"  Cash: ${final_snapshot.cash:,.2f}")
        print(f"  Positions: {len(final_snapshot.positions)}")
        for symbol, position in final_snapshot.positions.items():
            print(f"    {symbol}: {position.quantity:.2f} shares @ ${position.current_price:.2f}")
            print(f"      Market Value: ${position.market_value:,.2f}")
            print(f"      Unrealized P&L: ${position.unrealized_pnl:,.2f}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
