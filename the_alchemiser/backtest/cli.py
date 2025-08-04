#!/usr/bin/env python3
"""
Command Line Interface for Backtest Engine

This module provides a clean CLI for running various types of backtests:
- Individual strategy backtests
- Multi-strategy combinations
- All weight combinations
- Custom configuration backtests
"""

import argparse
import datetime as dt
import sys
from typing import List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


class BacktestCLI:
    """Command line interface for backtest operations"""

    def __init__(self):
        self.parser = self._create_parser()

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create the argument parser with all available options"""
        parser = argparse.ArgumentParser(
            description="The Alchemiser Backtest Engine",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Individual strategy backtest
  python -m the_alchemiser.backtest.cli individual nuclear --start 2023-01-01 --end 2024-01-01

  # Live configuration backtest
  python -m the_alchemiser.backtest.cli live --start 2023-01-01 --end 2024-01-01

  # All weight combinations
  python -m the_alchemiser.backtest.cli combinations --start 2023-01-01 --end 2024-01-01 --step-size 20

  # Pre-load data cache
  python -m the_alchemiser.backtest.cli preload --start 2023-01-01 --end 2024-01-01
            """,
        )

        # Add subcommands
        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        # Individual strategy command
        individual_parser = subparsers.add_parser(
            "individual", help="Run individual strategy backtest"
        )
        individual_parser.add_argument(
            "strategy", choices=["nuclear", "tecl", "klm"], help="Strategy to backtest"
        )
        self._add_common_args(individual_parser)

        # Live configuration command
        live_parser = subparsers.add_parser(
            "live", help="Run backtest using live trading configuration"
        )
        self._add_common_args(live_parser)

        # All combinations command
        combinations_parser = subparsers.add_parser(
            "combinations", help="Run all weight combinations backtest"
        )
        combinations_parser.add_argument(
            "--step-size", type=int, default=10, help="Weight step size in percent (default: 10)"
        )
        combinations_parser.add_argument(
            "--max-workers",
            type=int,
            default=4,
            help="Maximum number of parallel workers (default: 4)",
        )
        combinations_parser.add_argument(
            "--top-n", type=int, default=10, help="Show top N results (default: 10, 0 for all)"
        )
        self._add_common_args(combinations_parser)

        # Data preload command
        preload_parser = subparsers.add_parser("preload", help="Pre-load data into cache")
        preload_parser.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
        preload_parser.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
        preload_parser.add_argument(
            "--minute-data", action="store_true", help="Include minute data"
        )
        preload_parser.add_argument(
            "--force-refresh", action="store_true", help="Force refresh cache"
        )
        preload_parser.add_argument(
            "--symbols", nargs="*", help="Specific symbols to cache (default: auto-detect all)"
        )

        return parser

    def _add_common_args(self, parser: argparse.ArgumentParser):
        """Add common arguments to a parser"""
        # Date range
        parser.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
        parser.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")

        # Trading parameters
        parser.add_argument(
            "--initial-equity",
            type=float,
            default=1000.0,
            help="Initial equity amount (default: 1000.0)",
        )
        parser.add_argument(
            "--slippage-bps", type=int, default=8, help="Slippage in basis points (default: 8)"
        )
        parser.add_argument(
            "--noise-factor",
            type=float,
            default=0.0015,
            help="Market noise factor (default: 0.0015)",
        )

        # Deposit parameters
        parser.add_argument(
            "--deposit-amount", type=float, default=0.0, help="Regular deposit amount (default: 0)"
        )
        parser.add_argument(
            "--deposit-frequency", choices=["monthly", "weekly"], help="Deposit frequency"
        )
        parser.add_argument(
            "--deposit-day", type=int, default=1, help="Day for deposits (default: 1)"
        )

        # Data options
        parser.add_argument(
            "--minute-data", action="store_true", help="Use minute data for execution"
        )

    def parse_args(self, args: Optional[List[str]] = None) -> argparse.Namespace:
        """Parse command line arguments"""
        return self.parser.parse_args(args)

    def validate_args(self, args: argparse.Namespace) -> bool:
        """Validate parsed arguments"""
        if hasattr(args, "start") and hasattr(args, "end"):
            try:
                start_date = dt.datetime.strptime(args.start, "%Y-%m-%d")
                end_date = dt.datetime.strptime(args.end, "%Y-%m-%d")

                if start_date >= end_date:
                    console.print("[red]❌ Start date must be before end date[/red]")
                    return False

                # Check for reasonable date range
                if (end_date - start_date).days < 30:
                    console.print(
                        "[yellow]⚠️ Warning: Very short backtest period (< 30 days)[/yellow]"
                    )

                if (end_date - start_date).days > 365 * 10:
                    console.print(
                        "[yellow]⚠️ Warning: Very long backtest period (> 10 years)[/yellow]"
                    )

            except ValueError:
                console.print("[red]❌ Invalid date format. Use YYYY-MM-DD[/red]")
                return False

        # Validate trading parameters
        if hasattr(args, "initial_equity") and args.initial_equity <= 0:
            console.print("[red]❌ Initial equity must be positive[/red]")
            return False

        if hasattr(args, "slippage_bps") and (args.slippage_bps < 0 or args.slippage_bps > 1000):
            console.print("[red]❌ Slippage must be between 0 and 1000 basis points[/red]")
            return False

        if hasattr(args, "noise_factor") and (args.noise_factor < 0 or args.noise_factor > 0.1):
            console.print("[red]❌ Noise factor must be between 0 and 0.1[/red]")
            return False

        # Validate step size for combinations
        if hasattr(args, "step_size") and (args.step_size < 1 or args.step_size > 50):
            console.print("[red]❌ Step size must be between 1 and 50 percent[/red]")
            return False

        return True

    def display_help(self):
        """Display help information"""
        self.parser.print_help()

    def display_backtest_summary(self, args: argparse.Namespace):
        """Display a summary of the backtest configuration"""
        console.print(
            Panel(
                f"[bold cyan]Backtest Configuration[/bold cyan]\n"
                f"Command: {args.command}\n"
                f"Period: {args.start} to {args.end}\n"
                f"Initial Equity: £{args.initial_equity:,.2f}\n"
                f"Slippage: {args.slippage_bps} bps\n"
                f"Noise Factor: {args.noise_factor:.4f}\n"
                f"Minute Data: {'Yes' if getattr(args, 'minute_data', False) else 'No'}",
                title="📊 Configuration Summary",
            )
        )

    def display_results_table(self, results: List, title: str = "Backtest Results"):
        """Display results in a formatted table"""
        if not results:
            console.print("[yellow]No results to display[/yellow]")
            return

        table = Table(title=title)
        table.add_column("Rank", style="cyan", width=4)
        table.add_column("Strategy", style="yellow", width=25)
        table.add_column("Total Return %", style="green", justify="right")
        table.add_column("CAGR %", style="green", justify="right")
        table.add_column("Volatility %", style="blue", justify="right")
        table.add_column("Sharpe", style="magenta", justify="right")
        table.add_column("Max DD %", style="red", justify="right")
        table.add_column("Calmar", style="bold green", justify="right")
        table.add_column("Final Equity", style="cyan", justify="right")

        for i, result in enumerate(results, 1):
            # Handle different result types
            if hasattr(result, "strategy_name"):
                # BacktestResult object
                calmar_str = (
                    f"{result.calmar_ratio:.2f}" if result.calmar_ratio != float("inf") else "∞"
                )
                table.add_row(
                    str(i),
                    result.strategy_name,
                    f"{result.total_return:.2f}",
                    f"{result.cagr:.2f}",
                    f"{result.volatility:.2f}",
                    f"{result.sharpe_ratio:.2f}",
                    f"{result.max_drawdown:.2f}",
                    calmar_str,
                    f"£{result.final_equity:,.2f}",
                )
            else:
                # Handle other result formats if needed
                console.print(f"[yellow]⚠️ Unknown result format for item {i}[/yellow]")

        console.print(table)


def main():
    """Main CLI entry point"""
    cli = BacktestCLI()

    try:
        args = cli.parse_args()

        if not args.command:
            cli.display_help()
            return 1

        # Validate arguments
        if not cli.validate_args(args):
            return 1

        # Import the engine here to avoid circular imports
        from the_alchemiser.backtest.engine import BacktestEngine

        # Initialize engine
        engine = BacktestEngine()

        # Display configuration summary
        if args.command != "preload":
            cli.display_backtest_summary(args)

        # Execute the requested command
        if args.command == "individual":
            result = engine.run_individual_strategy(
                strategy=args.strategy,
                start=dt.datetime.strptime(args.start, "%Y-%m-%d"),
                end=dt.datetime.strptime(args.end, "%Y-%m-%d"),
                initial_equity=args.initial_equity,
                slippage_bps=args.slippage_bps,
                noise_factor=args.noise_factor,
                deposit_amount=args.deposit_amount,
                deposit_frequency=args.deposit_frequency,
                deposit_day=args.deposit_day,
                use_minute_candles=args.minute_data,
            )
            cli.display_results_table([result], f"{args.strategy.upper()} Strategy Results")

        elif args.command == "live":
            result = engine.run_live_configuration(
                start=dt.datetime.strptime(args.start, "%Y-%m-%d"),
                end=dt.datetime.strptime(args.end, "%Y-%m-%d"),
                initial_equity=args.initial_equity,
                slippage_bps=args.slippage_bps,
                noise_factor=args.noise_factor,
                deposit_amount=args.deposit_amount,
                deposit_frequency=args.deposit_frequency,
                deposit_day=args.deposit_day,
                use_minute_candles=args.minute_data,
            )
            cli.display_results_table([result], "Live Configuration Results")

        elif args.command == "combinations":
            results = engine.run_all_combinations(
                start=dt.datetime.strptime(args.start, "%Y-%m-%d"),
                end=dt.datetime.strptime(args.end, "%Y-%m-%d"),
                initial_equity=args.initial_equity,
                slippage_bps=args.slippage_bps,
                noise_factor=args.noise_factor,
                deposit_amount=args.deposit_amount,
                deposit_frequency=args.deposit_frequency,
                deposit_day=args.deposit_day,
                use_minute_candles=args.minute_data,
                step_size=args.step_size,
                max_workers=args.max_workers,
            )

            # Show top N results
            if args.top_n > 0:
                results = results[: args.top_n]

            cli.display_results_table(results, f"All Combinations Results (Top {len(results)})")

        elif args.command == "preload":
            engine.preload_data(
                start=dt.datetime.strptime(args.start, "%Y-%m-%d"),
                end=dt.datetime.strptime(args.end, "%Y-%m-%d"),
                symbols=args.symbols,
                include_minute_data=args.minute_data,
                force_refresh=args.force_refresh,
            )
            console.print("[green]✅ Data preloading complete[/green]")

        return 0

    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️ Interrupted by user[/yellow]")
        return 1
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        import traceback

        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        return 1


if __name__ == "__main__":
    sys.exit(main())
