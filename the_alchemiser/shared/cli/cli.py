#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Command-Line Interface for The Alchemiser Quantitative Trading System.

Provides a modern CLI built with Typer and Rich for user interaction, strategy selection,
and reporting. Handles user commands and displays formatted output.
"""

from __future__ import annotations

import logging
import subprocess
import time
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

# Delayed import to avoid complex dependency chains during module loading
# from the_alchemiser.strategy.data.market_data_service import MarketDataService
from the_alchemiser.shared.cli.cli_formatter import render_account_info
from the_alchemiser.shared.config.secrets_manager import secrets_manager
from the_alchemiser.shared.errors.error_handler import TradingSystemErrorHandler
from the_alchemiser.shared.logging.logging_utils import (
    get_logger,
    log_error_with_context,
)
from the_alchemiser.shared.types.exceptions import (
    AlchemiserError,
    TradingClientError,
)
from the_alchemiser.shared.types.market_data_port import MarketDataPort
from the_alchemiser.shared.types.quote import QuoteModel
from the_alchemiser.shared.value_objects.symbol import Symbol

# Delayed imports to avoid circular dependency issues during module loading
# from the_alchemiser.strategy.engines.core.trading_engine import TradingEngine
# from the_alchemiser.strategy.dsl.errors import DSLError
# from the_alchemiser.strategy.dsl.parser import DSLParser
# from the_alchemiser.strategy.dsl.strategy_loader import StrategyLoader
# Import domain models for type annotations
# TODO: BarModel was removed with deprecated strategy module
# from the_alchemiser.strategy.types.bar import BarModel

# Constants to avoid duplication
STYLE_BOLD_CYAN = "bold cyan"
STYLE_ITALIC = "italic"
STYLE_BOLD_BLUE = "bold blue"
STYLE_BOLD_GREEN = "bold green"
STYLE_BOLD_RED = "bold red"
STYLE_BOLD_YELLOW = "bold yellow"
STYLE_BOLD_MAGENTA = "bold magenta"
PROGRESS_DESCRIPTION_FORMAT = "[progress.description]{task.description}"

# Initialize Typer app and Rich console
app = typer.Typer(
    name="alchemiser",
    help="The Alchemiser - Advanced Multi-Strategy Quantitative Trading System",
    add_completion=False,
    rich_markup_mode="rich",
)
console = Console()


def show_welcome() -> None:
    """Render the CLI welcome banner.

    Displays a rich-formatted header panel describing the trading system.

    Returns:
        None

    """
    welcome_text = Text()
    welcome_text.append(" The Alchemiser Quantitative Trading System\n", style=STYLE_BOLD_CYAN)
    welcome_text.append("Advanced Multi-Strategy Trading System", style=STYLE_ITALIC)

    panel = Panel(
        welcome_text,
        title=f"[{STYLE_BOLD_BLUE}]Welcome[/{STYLE_BOLD_BLUE}]",
        subtitle=f"[{STYLE_ITALIC}]Nuclear • TECL • KLM • Multi-Strategy[/{STYLE_ITALIC}]",
        border_style="blue",
        padding=(1, 2),
    )
    console.print(panel)
    console.print()


@app.command()
def signal(
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output with detailed logs"
    ),
    strategy: str = typer.Option(
        "all",
        "--strategy",
        "-s",
        help="Strategy to run: nuclear, tecl, klm, or all (default)",
    ),
    dsl_strategy: str | None = typer.Option(
        None,
        "--DSL",
        "--dsl",
        help="Path (or name) of DSL .clj strategy file to evaluate (uses new DSL engine)",
    ),
    show_trace: bool = typer.Option(
        False,
        "--trace",
        help="Display evaluation trace when using --DSL",
    ),
    save_trace: str | None = typer.Option(
        None,
        "--save-trace",
        help="Save evaluation trace JSON to file when using --DSL",
    ),
    tracking: bool = typer.Option(
        False,
        "--tracking",
        help="Include strategy performance tracking table (opt-in; default off)",
    ),
) -> None:
    """🧠 Generate strategy signals.

    Default: legacy multi-strategy signal analysis via main engine.
    With --DSL: evaluate a standalone DSL (.clj) strategy file and display portfolio weights.
    """
    # Initialize error handler
    error_handler = TradingSystemErrorHandler()

    try:
        # DSL mode path -----------------------------------------------------
        if dsl_strategy:
            # TODO: DSL functionality temporarily disabled due to deprecated module removal
            console.print("[bold red]DSL mode temporarily disabled during migration to strategy_v2[/bold red]")
            console.print("Please use the default signal analysis mode.")
            raise typer.Exit(1)
            show_welcome()

            # Resolve strategy file path (allow bare name referencing clj-strategies dir)
            raw_path = dsl_strategy.strip()
            path_candidate = Path(raw_path)
            if not path_candidate.suffix:
                # Add .clj extension if missing
                path_candidate = path_candidate.with_suffix(".clj")
            if not path_candidate.is_file():
                # Try relative to repository clj-strategies root
                repo_root = Path(__file__).resolve().parents[3]
                alt1 = repo_root / "clj-strategies" / path_candidate.name
                alt2 = repo_root / "clj-strategies" / "trading_strategies" / path_candidate.name
                for candidate in (alt1, alt2):
                    if candidate.is_file():
                        path_candidate = candidate
                        break

            console.print(
                f"[{STYLE_BOLD_CYAN}]🔍 Evaluating CLJ strategy:[/{STYLE_BOLD_CYAN}] {path_candidate}"
            )

            if not path_candidate.is_file():
                console.print(f"[bold red]Strategy file not found:[/bold red] {path_candidate}")
                raise typer.Exit(1)

            with Progress(
                SpinnerColumn(),
                TextColumn(PROGRESS_DESCRIPTION_FORMAT),
                console=console,
            ) as progress:
                task = progress.add_task("[cyan]Initializing market data...", total=None)
                time.sleep(0.25)

                # Acquire API keys (paper mode for safety)
                api_key, secret_key = secrets_manager.get_alpaca_keys(paper_trading=True)
                if not api_key or not secret_key:
                    console.print(
                        "[bold red]Alpaca API credentials not available (paper).[/bold red]"
                    )
                    raise typer.Exit(1)

                # Legacy TradingServiceManager import commented out
                # from the_alchemiser.execution.core.trading_services_facade import (
                #     TradingServicesFacade as TradingServiceManager,
                # )
                # tsm = TradingServiceManager(api_key, secret_key, paper=True)

                # Use AlpacaManager directly instead of legacy facade
                from the_alchemiser.shared.brokers import AlpacaManager
                alpaca_manager = AlpacaManager(api_key, secret_key, paper=True)

                # Adapter implementing MarketDataPort
                class _MarketDataPortAdapter(MarketDataPort):
                    """Adapter bridging MarketDataService to Domain MarketDataPort for DSL.

                    Implements required methods of MarketDataPort protocol using the current
                    typed port contract. Returns lightweight objects that satisfy DSL evaluator needs.
                    """

                    def __init__(self, md: MarketDataService) -> None:
                        self._md = md

                    def get_bars(
                        self,
                        symbol: Symbol,
                        period: str,
                        timeframe: str,
                    ) -> list[BarModel]:
                        """Get historical bars for a symbol."""
                        from datetime import datetime
                        from decimal import Decimal

                        from the_alchemiser.strategy.types.bar import BarModel

                        # Handle both Symbol objects and strings
                        symbol_str = str(symbol.value) if hasattr(symbol, "value") else str(symbol)

                        # Reuse existing service method that returns DataFrame-like structure
                        df = self._md.get_data(symbol_str, timeframe=timeframe, period=period)
                        bars: list[BarModel] = []

                        if hasattr(df, "iterrows"):
                            for _idx, row in df.iterrows():
                                # Get close price - handle both 'Close' and 'close' column names
                                close_price = row.get("Close") or row.get("close")
                                if close_price is not None:
                                    # Create minimal BarModel compatible object
                                    # DSL evaluator typically only needs close prices
                                    close_decimal = Decimal(str(close_price))
                                    timestamp = getattr(row, "name", None) or datetime.now(UTC)
                                    if not isinstance(timestamp, datetime):
                                        timestamp = datetime.now(UTC)

                                    bars.append(
                                        BarModel(
                                            ts=timestamp,
                                            open=close_decimal,  # Simplified for DSL
                                            high=close_decimal,
                                            low=close_decimal,
                                            close=close_decimal,
                                            volume=Decimal("0"),
                                        )
                                    )
                        return bars

                    def get_latest_quote(self, symbol: Symbol) -> QuoteModel | None:
                        """Get latest quote for a symbol."""
                        from datetime import datetime
                        from decimal import Decimal

                        from the_alchemiser.shared.types.quote import QuoteModel

                        # Handle both Symbol objects and strings
                        symbol_str = str(symbol.value) if hasattr(symbol, "value") else str(symbol)

                        q = self._md.get_validated_quote(symbol_str)
                        if q is None:
                            return None

                        # Return QuoteModel with bid/ask
                        bid_val = (
                            Decimal(str(q[0])) if len(q) > 0 and q[0] is not None else Decimal("0")
                        )
                        ask_val = (
                            Decimal(str(q[1])) if len(q) > 1 and q[1] is not None else Decimal("0")
                        )

                        return QuoteModel(
                            ts=datetime.now(UTC),
                            bid=bid_val,
                            ask=ask_val,
                        )

                    def get_mid_price(self, symbol: Symbol) -> float | None:
                        """Get mid price for a symbol."""
                        # Handle both Symbol objects and strings
                        symbol_str = str(symbol.value) if hasattr(symbol, "value") else str(symbol)

                        quote = self.get_latest_quote(symbol)
                        if not quote or quote.bid is None or quote.ask is None:
                            # Fallback to last trade/price if available
                            return self._md.get_validated_price(symbol_str)
                        # Convert Decimal result to float for compatibility
                        return float(quote.mid)

                adapter = _MarketDataPortAdapter(tsm.market_data)

                progress.update(task, description="[cyan]Parsing & evaluating DSL strategy...")

                # Load optimization config from environment so .env flags apply
                from the_alchemiser.strategy.dsl.optimization_config import (
                    configure_from_environment,
                )

                _opt_cfg = configure_from_environment()
                loader = StrategyLoader(
                    adapter, optimization_config=_opt_cfg, use_environment=False
                )
                try:
                    portfolio, trace = loader.evaluate_strategy_file(path_candidate)
                except (DSLError, ValueError, OSError) as e:
                    error_handler.handle_error(
                        error=e,
                        context="CLI DSL strategy evaluation",
                        component="cli.signal.dsl",
                        additional_data={
                            "file": str(path_candidate),
                            "error_type": type(e).__name__,
                        },
                    )
                    console.print(f"\n[bold red]DSL evaluation error: {e}[/bold red]")
                    if verbose:
                        console.print_exception()
                    raise typer.Exit(1)
                finally:
                    progress.update(task, completed=1)

            # Display results ------------------------------------------------
            if portfolio:
                total_weight: Decimal = Decimal(str(sum(portfolio.values())))
                table = Table(
                    title=f"DSL Portfolio Weights (Σ={float(total_weight):.6f})",
                    show_lines=True,
                    expand=True,
                )
                table.add_column("Symbol", style=STYLE_BOLD_CYAN)
                table.add_column("Weight", justify="right")
                for symbol, weight in sorted(portfolio.items(), key=lambda x: x[1], reverse=True):
                    table.add_row(symbol, f"{float(weight):.6f}")
                console.print()
                console.print(table)
                console.print(
                    f"[bold green]✅ DSL strategy evaluated successfully with {len(portfolio)} positions[/bold green]"
                )
            else:
                console.print(
                    "[bold yellow]Strategy evaluated to an empty portfolio (no positions).[/bold yellow]"
                )

            # Optional trace handling
            if show_trace and "trace" in locals():
                console.print("\n[bold blue]Evaluation Trace (first 50 entries):[/bold blue]")
                for entry in trace[:50]:
                    console.print(f"[dim]- {entry}")
                if len(trace) > 50:
                    console.print(
                        f"[dim]{len(trace) - 50} more entries not shown (use --save-trace).[/dim]"
                    )

            if save_trace and "trace" in locals():
                out_path = Path(save_trace)
                try:
                    loader.save_trace(trace, out_path)
                    console.print(
                        f"[dim]Trace saved to {out_path.resolve()} ({len(trace)} entries)[/dim]"
                    )
                except Exception as e:  # pragma: no cover - non-critical
                    console.print(f"[dim yellow]Failed to save trace: {e}[/dim yellow]")

            return  # Exit early after DSL mode

        # Legacy multi-strategy signal path ----------------------------------
        show_welcome()

        # Show deprecation warning for --tracking in signal mode
        if tracking:
            console.print(
                "[dim yellow]⚠️  --tracking flag in signal mode is deprecated. "
                "Use 'alchemiser trade --show-tracking' to see performance data after trade execution.[/dim yellow]"
            )

        with Progress(
            SpinnerColumn(),
            TextColumn(PROGRESS_DESCRIPTION_FORMAT),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Analyzing market conditions...", total=None)
            time.sleep(0.5)  # Brief pause for UX

            progress.update(task, description="[cyan]📊 Generating strategy signals...")

            # Use the main entry point to ensure proper DI initialization
            from the_alchemiser.main import main

            # Build argv for main function - signal mode
            argv = ["signal"]
            if tracking:
                argv.append("--tracking")

            success = main(argv=argv)

        if success:
            console.print("\n[bold green]Signal analysis completed successfully![/bold green]")
        else:
            console.print("\n[bold red]Signal analysis failed![/bold red]")
            raise typer.Exit(1)
    except AlchemiserError as e:
        error_handler.handle_error(
            error=e,
            context="CLI signal command - application error",
            component="cli.signal",
            additional_data={"verbose": verbose, "error_type": type(e).__name__},
        )
        console.print(f"\n[bold red]Application error: {e}[/bold red]")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)
    except (ImportError, AttributeError, ValueError, KeyError, TypeError, OSError) as e:
        error_handler.handle_error(
            error=e,
            context="CLI signal command - unexpected system error",
            component="cli.signal",
            additional_data={
                "verbose": verbose,
                "error_type": "unexpected_error",
                "original_error": type(e).__name__,
            },
        )
        console.print(f"\n[bold red]Unexpected error: {e}[/bold red]")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)


@app.command()
def trade(
    # Remove --live flag - trading mode now determined by deployment stage
    ignore_market_hours: bool = typer.Option(
        False, "--ignore-market-hours", help="Trade outside market hours (testing only)"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    no_header: bool = typer.Option(False, "--no-header", help="Skip welcome header"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompts"),
    show_tracking: bool = typer.Option(
        False, "--show-tracking", help="Display strategy performance tracking after execution"
    ),
    export_tracking_json: str | None = typer.Option(
        None, "--export-tracking-json", help="Export tracking summary to JSON file"
    ),
) -> None:
    """💰 [bold green]Execute multi-strategy trading[/bold green].

    Runs Nuclear, TECL, and KLM strategies with automatic portfolio allocation.
    Trading mode (live/paper) is automatically determined by deployment stage.

    [bold blue]🔐 Stage-aware security:[/bold blue]
    - Local/dev: Paper trading only
    - Production: Live trading with production credentials
    """
    if not no_header:
        show_welcome()

    # Determine trading mode from deployment stage
    # Determine trading mode and stage from secrets_manager
    is_live = not secrets_manager.is_paper_trading
    stage = secrets_manager.stage

    if is_live:
        console.print(
            f"[bold red]LIVE trading mode active (stage: {stage.upper()}). Proceeding without confirmation.[/bold red]"
        )
    else:
        console.print(f"[bold blue]PAPER trading mode active (stage: {stage.upper()}).[/bold blue]")

    mode_display = "[bold red]LIVE[/bold red]" if is_live else "[bold blue]PAPER[/bold blue]"
    console.print(f"[bold yellow]Starting {mode_display} trading...[/bold yellow]")

    try:
        # Import and run the main trading logic with DI
        from the_alchemiser.main import main

        console.print("[dim]📊 Analyzing market conditions...[/dim]")
        time.sleep(0.5)  # Brief pause for UI

        console.print("[dim]⚡ Generating strategy signals...[/dim]")

        # Build argv for main function (no --live flag)
        argv = ["trade"]
        if ignore_market_hours:
            argv.append("--ignore-market-hours")
        if show_tracking:
            argv.append("--show-tracking")
        if export_tracking_json:
            argv.extend(["--export-tracking-json", export_tracking_json])

        result = main(argv=argv)

        console.print("[dim]✅ Trading completed![/dim]")

        if result:
            console.print(
                f"\n[bold green]{mode_display} trading completed successfully![/bold green]"
            )
        else:
            console.print(f"\n[bold red]{mode_display} trading failed![/bold red]")
            raise typer.Exit(1)

    except TradingClientError as e:
        logger = get_logger(__name__)
        log_error_with_context(
            logger,
            e,
            "cli_trading_client_error",
            function="trade",
            command="trade",
            ignore_market_hours=ignore_market_hours,
            error_type=type(e).__name__,
        )
        console.print(f"\n[bold red]Trading client error: {e}[/bold red]")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)
    except (ImportError, AttributeError, ValueError, KeyError, TypeError, OSError) as e:
        logger = get_logger(__name__)
        log_error_with_context(
            logger,
            e,
            "cli_trading_execution",
            function="trade",
            command="trade",
            ignore_market_hours=ignore_market_hours,
            error_type="unexpected_error",
            original_error=type(e).__name__,
        )
        console.print(f"\n[bold red]Unexpected error: {e}[/bold red]")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)


@app.command()
def status() -> None:
    """📈 [bold blue]Show account status and positions[/bold blue].

    Displays current account balance, positions, portfolio performance, and P&L.
    Trading mode (live/paper) determined by environment configuration.
    """
    show_welcome()

    # Initialize error handler
    error_handler = TradingSystemErrorHandler()

    # Determine trading mode from endpoint URL
    from the_alchemiser.shared.config.secrets_adapter import get_alpaca_keys

    _, _, endpoint = get_alpaca_keys()
    is_live = endpoint and "paper" not in endpoint.lower()
    paper_trading = not is_live
    mode_display = "[bold red]LIVE[/bold red]" if is_live else "[bold blue]PAPER[/bold blue]"

    if is_live:
        console.print(
            Panel(
                "[bold red]⚠️  LIVE ACCOUNT STATUS[/bold red]\n\n"
                "You are viewing your LIVE trading account with real money.\n"
                "This shows actual positions and P&L from your live account.",
                style="bold red",
                expand=False,
            )
        )

    console.print(f"[bold yellow]Fetching {mode_display} account status...[/bold yellow]")

    try:
        # Initialize DI container through TradingSystem
        from the_alchemiser.main import TradingSystem

        # Create TradingSystem instance to get properly initialized container
        trading_system = TradingSystem()
        container = trading_system.container
        if container is None:
            raise RuntimeError("DI container not available - ensure system is properly initialized")

        # Override the paper_trading provider so downstream providers pick the right keys/endpoints
        try:
            container.config.paper_trading.override(paper_trading)
        except AttributeError:
            # Non-fatal; container may not expose override in some DI test contexts
            pass  # pragma: no cover

        # Create trader using modern bootstrap approach
        from the_alchemiser.shared.config.bootstrap import (
            bootstrap_from_container,
        )

        bootstrap_context = bootstrap_from_container(container)
        from the_alchemiser.strategy.engines.core.trading_engine import TradingEngine

        trader = TradingEngine(
            bootstrap_context=bootstrap_context,
            strategy_allocations={},  # Not needed for status display
            ignore_market_hours=True,  # Status should work anytime
        )
        trader.paper_trading = paper_trading

        account_info: dict[str, Any] = dict(trader.get_account_info())

        # Always use basic account info instead of enriched typed summary
        # Legacy TradingServiceManager import commented out to remove fallback dependencies
        # from the_alchemiser.execution.core.trading_services_facade import (
        #     TradingServicesFacade as TradingServiceManager,
        # )

        # Use basic account info from TradingEngine instead of legacy enriched summary
        # This removes dependency on legacy execution modules

        # AccountInfo is always returned (never None), so this check is always true
        # Cast to dict[str, Any] for render_account_info compatibility
        render_account_info(dict(account_info))

        # Always show enriched positions display using typed path
        try:
            # Reuse TSM if available, otherwise instantiate
            if tsm is None:
                api_key, secret_key = secrets_manager.get_alpaca_keys(paper_trading=not is_live)
                if not api_key or not secret_key:
                    raise RuntimeError("Alpaca credentials not available")
                tsm = TradingServiceManager(api_key, secret_key, paper=not is_live)

            enriched_positions = tsm.get_positions_enriched()
            if enriched_positions:
                table = Table(title="Open Positions (Enriched)", show_lines=True, expand=True)
                table.add_column("Symbol", style=STYLE_BOLD_CYAN)
                table.add_column("Qty", justify="right")
                table.add_column("Avg Price", justify="right")
                table.add_column("Current", justify="right")
                table.add_column("Mkt Value", justify="right")
                table.add_column("Unrlzd P&L", justify="right")

                for item in enriched_positions.positions[:50]:  # Cap display to avoid huge tables
                    summary = item.summary
                    table.add_row(
                        str(summary.get("symbol", "")),
                        f"{float(summary.get('qty', 0.0)):.4f}",
                        f"${float(summary.get('avg_entry_price', 0.0)):.2f}",
                        f"${float(summary.get('current_price', 0.0)):.2f}",
                        f"${float(summary.get('market_value', 0.0)):.2f}",
                        f"${float(summary.get('unrealized_pl', 0.0)):.2f} ({float(summary.get('unrealized_plpc', 0.0)):.2%})",
                    )

                console.print()
                console.print(table)
        except Exception as e:  # Non-fatal UI enhancement
            console.print(f"[dim yellow]Enriched positions unavailable: {e}[/dim yellow]")

        # Display strategy tracking information
        try:
            from the_alchemiser.portfolio.pnl.strategy_order_tracker import (
                StrategyOrderTracker,
            )

            tracker = StrategyOrderTracker(paper_trading=paper_trading)

            # Get positions summary using new DTO methods
            positions_summary = tracker.get_positions_summary()

            if positions_summary:
                strategy_table = Table(
                    title="Strategy Positions (Tracked)", show_lines=True, expand=True
                )
                strategy_table.add_column("Strategy", style=STYLE_BOLD_MAGENTA)
                strategy_table.add_column("Symbol", style=STYLE_BOLD_CYAN)
                strategy_table.add_column("Qty", justify="right")
                strategy_table.add_column("Avg Cost", justify="right")
                strategy_table.add_column("Total Cost", justify="right")
                strategy_table.add_column("Last Updated", justify="center")

                for position in positions_summary:
                    # Format timestamp for display
                    last_updated = position.last_updated.strftime("%m/%d %H:%M")

                    strategy_table.add_row(
                        position.strategy,
                        position.symbol,
                        f"{float(position.quantity):.4f}",
                        f"${float(position.average_cost):.2f}",
                        f"${float(position.total_cost):.2f}",
                        last_updated,
                    )

                console.print()
                console.print(strategy_table)

                # Show P&L summary for each strategy with positions
                strategy_pnl_table = Table(
                    title="Strategy P&L Summary", show_lines=True, expand=True
                )
                strategy_pnl_table.add_column("Strategy", style=STYLE_BOLD_MAGENTA)
                strategy_pnl_table.add_column("Realized P&L", justify="right")
                strategy_pnl_table.add_column("Unrealized P&L", justify="right")
                strategy_pnl_table.add_column("Total P&L", justify="right")
                strategy_pnl_table.add_column("Return %", justify="right")

                strategies_with_data = {pos.strategy for pos in positions_summary}
                for strategy_name in strategies_with_data:
                    try:
                        pnl_summary = tracker.get_pnl_summary(strategy_name)

                        # Color code P&L
                        total_pnl = float(pnl_summary.total_pnl)
                        pnl_color = "green" if total_pnl >= 0 else "red"
                        pnl_sign = "+" if total_pnl >= 0 else ""

                        return_pct = float(pnl_summary.total_return_pct)
                        return_color = "green" if return_pct >= 0 else "red"
                        return_sign = "+" if return_pct >= 0 else ""

                        strategy_pnl_table.add_row(
                            strategy_name,
                            f"${float(pnl_summary.realized_pnl):.2f}",
                            f"${float(pnl_summary.unrealized_pnl):.2f}",
                            f"[{pnl_color}]{pnl_sign}${total_pnl:.2f}[/{pnl_color}]",
                            f"[{return_color}]{return_sign}{return_pct:.2f}%[/{return_color}]",
                        )
                    except Exception as e:
                        console.print(
                            f"[dim yellow]Error getting P&L for {strategy_name}: {e}[/dim yellow]"
                        )

                if strategy_pnl_table.rows:
                    console.print()
                    console.print(strategy_pnl_table)
            else:
                console.print()
                console.print(
                    "[dim yellow]No strategy positions found in tracking system[/dim yellow]"
                )

        except Exception as e:  # Non-fatal UI enhancement
            console.print(f"[dim yellow]Strategy tracking unavailable: {e}[/dim yellow]")

        console.print("[bold green]Account status retrieved successfully![/bold green]")

        # Display order lifecycle information if available
        try:
            # Access TradingServiceManager through the bootstrap context
            tsm = bootstrap_context.get("trading_service_manager")
            if tsm:
                # Get lifecycle metrics and tracked orders
                lifecycle_metrics = tsm.get_lifecycle_metrics()
                tracked_orders = tsm.get_all_tracked_orders()

                if tracked_orders or lifecycle_metrics.get("event_counts"):
                    lifecycle_table = Table(
                        title="Order Lifecycle Status", show_lines=True, expand=True
                    )
                    lifecycle_table.add_column("Metric", style="bold cyan")
                    lifecycle_table.add_column("Value", justify="right")

                    # Add general metrics
                    event_counts = lifecycle_metrics.get("event_counts", {})
                    lifecycle_table.add_row("Total Tracked Orders", str(len(tracked_orders)))
                    lifecycle_table.add_row(
                        "Active Observers", str(lifecycle_metrics.get("total_observers", 0))
                    )

                    if event_counts:
                        lifecycle_table.add_row("", "")  # Separator
                        lifecycle_table.add_row("[bold]Event Counts[/bold]", "")
                        for event_type, count in event_counts.items():
                            lifecycle_table.add_row(f"  {event_type}", str(count))

                    console.print()
                    console.print(lifecycle_table)

                    # If there are recent tracked orders, show them
                    if tracked_orders:
                        orders_table = Table(
                            title="Recent Tracked Orders", show_lines=True, expand=True
                        )
                        orders_table.add_column("Order ID", style="cyan")
                        orders_table.add_column("Lifecycle State", justify="center")

                        # Show last 10 orders
                        for order_id, state in list(tracked_orders.items())[-10:]:
                            # Color code based on state
                            if state.value in ["FILLED"]:
                                state_display = f"[green]{state.value}[/green]"
                            elif state.value in ["CANCELLED", "REJECTED", "ERROR", "EXPIRED"]:
                                state_display = f"[red]{state.value}[/red]"
                            elif state.value in ["PARTIALLY_FILLED"]:
                                state_display = f"[yellow]{state.value}[/yellow]"
                            else:
                                state_display = f"[blue]{state.value}[/blue]"

                            orders_table.add_row(
                                str(order_id).split("(")[1].rstrip(")").split("'")[1][:8]
                                + "...",  # Show short ID
                                state_display,
                            )

                        console.print()
                        console.print(orders_table)

        except Exception as e:
            # Non-fatal: lifecycle display is optional enhancement
            console.print(f"[dim yellow]Order lifecycle info unavailable: {e}[/dim yellow]")

    except TradingClientError as e:
        error_handler.handle_error(
            error=e,
            context="CLI status command - trading client operation",
            component="cli.status",
            additional_data={"live_trading": is_live, "error_type": type(e).__name__},
        )
        console.print(f"[bold red]Trading client error: {e}[/bold red]")
        raise typer.Exit(1)


@app.command("dsl-count")
def dsl_count(
    dsl_strategy: str = typer.Argument(..., help="Path (or name) of DSL .clj strategy file"),
    max_nodes: int | None = typer.Option(
        None,
        "--max-nodes",
        help="Override max node cap for counting (None disables cap)",
    ),
    max_depth: int | None = typer.Option(
        None,
        "--max-depth",
        help="Override max depth cap for counting (None disables cap)",
    ),
) -> None:
    """🔍 Dry-run parse a DSL strategy and report AST size (node count & depth).

    This does NOT evaluate indicators or fetch market data; it only parses the file
    and reports structural complexity so large strategies can be optimized before
    full evaluation.
    """
    # TODO: DSL functionality temporarily disabled due to deprecated module removal
    console = Console()
    console.print("[bold red]DSL functionality temporarily disabled during migration to strategy_v2[/bold red]")
    raise typer.Exit(1)
    show_welcome()

    raw_path = dsl_strategy.strip()
    path_candidate = Path(raw_path)
    if not path_candidate.suffix:
        path_candidate = path_candidate.with_suffix(".clj")
    if not path_candidate.is_file():
        repo_root = Path(__file__).resolve().parents[3]
        alt1 = repo_root / "clj-strategies" / path_candidate.name
        alt2 = repo_root / "clj-strategies" / "trading_strategies" / path_candidate.name
        for c in (alt1, alt2):
            if c.is_file():
                path_candidate = c
                break

    if not path_candidate.is_file():
        console.print(f"[bold red]Strategy file not found:[/bold red] {path_candidate}")
        raise typer.Exit(1)

    # Wording: explicitly reference CLJ file (user-facing clarification)
    console.print(f"[cyan]Parsing CLJ file:[/cyan] {path_candidate}")

    try:
        source = path_candidate.read_text(encoding="utf-8")
    except OSError as e:  # pragma: no cover - filesystem error
        console.print(f"[bold red]Failed to read file: {e}[/bold red]")
        raise typer.Exit(1)

    # Instantiate parser with overrides
    parser = DSLParser(max_nodes=max_nodes, max_depth=max_depth)
    start_time = time.perf_counter()
    try:
        ast_root = parser.parse(source)
    except Exception as e:  # DSLError subclasses already formatted upstream
        console.print(f"[bold red]Parse error:[/bold red] {e}")
        raise typer.Exit(1)
    elapsed = (time.perf_counter() - start_time) * 1000.0

    # Produce summary table
    table = Table(
        title="DSL Structural Complexity", show_header=True, header_style=STYLE_BOLD_MAGENTA
    )
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")
    table.add_row("Nodes", f"{parser.node_count:,}")
    table.add_row("Max Depth", f"{parser.max_depth_seen:,}")
    table.add_row("Parse Time (ms)", f"{elapsed:.2f}")
    table.add_row("Node Cap", str(max_nodes) if max_nodes is not None else "None")
    table.add_row("Depth Cap", str(max_depth) if max_depth is not None else "None")
    table.add_row("Root Type", type(ast_root).__name__)
    console.print()
    console.print(table)

    # Heuristic warnings
    warnings: list[str] = []
    if max_nodes is not None and parser.node_count > 0:
        warn_threshold = max_nodes * 0.8
        if parser.node_count >= warn_threshold:
            warnings.append(
                f"Node count {parser.node_count:,} is ≥ 80% of cap {max_nodes:,}. Consider refactoring repeated blocks."
            )
    if parser.node_count > 1_000_000 and (
        max_nodes is None or parser.node_count / (max_nodes or 1) < 0.8
    ):
        warnings.append(
            "Node count exceeds 1M; evaluation latency and memory use may become significant."
        )
    if parser.max_depth_seen > 2000:
        warnings.append(
            f"Maximum depth {parser.max_depth_seen} is very high; deeply nested conditionals may hurt readability/performance."
        )

    if warnings:
        console.print("\n[bold yellow]Warnings:[/bold yellow]")
        for w in warnings:
            console.print(f"[yellow]- {w}")
    else:
        console.print("\n[green]No structural warnings detected.[/green]")

    console.print(
        "\n[dim]Tip: Use macros/definitions (upcoming) or consolidate repeated RSI ladders to shrink node count.[/dim]"
    )


@app.command()
def deploy() -> None:
    """🚀 Deploy to AWS Lambda.

    Builds and deploys to AWS Lambda using SAM (Serverless Application Model).
    """
    show_welcome()

    console.print("[bold yellow]🔨 Building and deploying to AWS Lambda with SAM...[/bold yellow]")

    deploy_script = "scripts/deploy.sh"

    with Progress(
        SpinnerColumn(),
        TextColumn(PROGRESS_DESCRIPTION_FORMAT),
        console=console,
    ) as progress:
        _task = progress.add_task("Running deployment script...", total=None)

        try:
            result = subprocess.run(
                ["bash", deploy_script], capture_output=True, text=True, check=True
            )

            console.print("[bold green]✅ Deployment completed successfully![/bold green]")
            console.print("\n[dim]Deployment output:[/dim]")
            console.print(result.stdout)

        except subprocess.CalledProcessError as e:
            console.print("[bold red]❌ Deployment failed![/bold red]")
            console.print(f"[dim]Error output:[/dim]\n{e.stderr}")
            raise typer.Exit(1)
        except FileNotFoundError as e:
            console.print(f"[bold red]❌ Deployment script not found: {e}[/bold red]")
            raise typer.Exit(1)
        except PermissionError as e:
            console.print(f"[bold red]❌ Permission denied during deployment: {e}[/bold red]")
            raise typer.Exit(1)
        except (OSError, ValueError, AttributeError) as e:
            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                e,
                "cli_deployment_error",
                function="deploy",
                command="deploy",
                error_type="unexpected_error",
                original_error=type(e).__name__,
            )
            console.print(f"[bold red]❌ Unexpected deployment error: {e}[/bold red]")
            raise typer.Exit(1)


@app.command()
def version() -> None:
    """I  [bold]Show version information[/bold]."""
    version_info = Text()
    version_info.append(" The Alchemiser Quantitative Trading System\n", style=STYLE_BOLD_CYAN)
    version_info.append("Version: 2.0.0\n", style="bold")
    version_info.append(f"Built: {datetime.now(UTC).strftime('%Y-%m-%d')}\n", style="dim")
    version_info.append("Strategies: Nuclear, TECL, KLM, Multi-Strategy\n", style="green")
    version_info.append("Platform: Alpaca Markets", style="blue")

    console.print(Panel(version_info, title="[bold]Version Info[/bold]", border_style="cyan"))


@app.command()
def validate_indicators(
    mode: str = typer.Option("core", help="Validation mode: quick, core, or full"),
    symbols: str | None = typer.Option(None, "--symbols", help="Comma-separated symbols to test"),
    save_file: str | None = typer.Option(None, "--save", help="Save results to JSON file"),
    verbose_validation: bool = typer.Option(
        False, "--verbose-validation", help="Enable verbose validation logging"
    ),
) -> None:
    """🔬 [bold blue]Validate technical indicators against TwelveData API[/bold blue].

    This command runs a comprehensive validation suite that tests all technical
    indicators used by our trading strategies against TwelveData API values.

    Examples:
      alchemiser validate-indicators --mode quick
      alchemiser validate-indicators --symbols SPY,TQQQ --save results.json
      alchemiser validate-indicators --mode full

    Modes:
    • quick: Test core symbols (SPY, QQQ) with main indicators
    • core: Test all strategy symbols with key indicators
    • full: Comprehensive test of all symbols and indicators

    TwelveData API key is automatically retrieved from AWS Secrets Manager.

    """
    show_welcome()

    try:
        # Get API key from secrets manager
        from the_alchemiser.shared.config.secrets_manager import (
            secrets_manager,
        )

        api_key = secrets_manager.get_twelvedata_api_key()

        if not api_key:
            console.print("[red]Error: TwelveData API key not found in AWS Secrets Manager.[/red]")
            console.print("Please add TWELVEDATA_KEY to the 'the-alchemiser-secrets' secret.")
            console.print("Get a free API key at: https://twelvedata.com")
            raise typer.Exit(1)

        # Import the validation suite
        from the_alchemiser.strategy.validation.indicator_validator import (
            IndicatorValidationSuite,
        )

        # Validate mode
        if mode not in ["quick", "core", "full"]:
            console.print(f"[red]Error: Invalid mode '{mode}'. Must be: quick, core, or full[/red]")
            raise typer.Exit(1)

        # Initialize validation suite
        validator = IndicatorValidationSuite(api_key, console)

        # Determine symbols to test
        symbols_list: list[str]
        if symbols:
            symbols_list = [s.strip().upper() for s in symbols.split(",")]
        else:
            if mode == "quick":
                symbols_list = ["SPY", "QQQ"]
            elif mode == "core":
                symbols_list = validator.strategy_symbols["core"]
            else:  # full
                symbols_list = []
                for category in validator.strategy_symbols.values():
                    symbols_list.extend(category)
                symbols_list = list(set(symbols_list))  # Remove duplicates

        console.print(
            f"[bold blue]🔬 Running indicator validation in {mode.upper()} mode...[/bold blue]"
        )
        console.print(
            f"Testing {len(symbols_list)} symbols: {', '.join(symbols_list[:5])}{' ...' if len(symbols_list) > 5 else ''}"
        )

        # Run validation
        summary = validator.run_validation_suite(symbols_list, mode)
        validator.generate_report(summary)

        if save_file:
            validator.save_results(save_file)

        if summary["failed_tests"] == 0:
            console.print("\n[bold green]✅ All indicators validated successfully![/bold green]")
        else:
            console.print(
                f"\n[bold yellow]⚠️  Validation completed with {summary['failed_tests']} failures[/bold yellow]"
            )
            console.print("Check the detailed report above for specific issues.")

    except ImportError as e:
        console.print("[red]Error: Could not import validation suite.[/red]")
        console.print(f"Details: {e}")
        raise typer.Exit(1)
    except AlchemiserError as e:
        logger = get_logger(__name__)
        log_error_with_context(
            logger,
            e,
            "cli_validation_application_error",
            function="validate",
            command="validate",
            error_type=type(e).__name__,
        )
        console.print(f"[red]Application error during validation: {e}[/red]")
        if verbose_validation:
            console.print_exception()
        raise typer.Exit(1)
    except (AttributeError, ValueError, KeyError, TypeError, OSError) as e:
        logger = get_logger(__name__)
        log_error_with_context(
            logger,
            e,
            "cli_validation_unexpected_error",
            function="validate",
            command="validate",
            error_type="unexpected_error",
            original_error=type(e).__name__,
        )
        console.print(f"[red]Unexpected error running validation: {e}[/red]")
        if verbose_validation:
            console.print_exception()
        raise typer.Exit(1)


@app.callback()
def main(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress non-essential output"),
) -> None:
    """[bold]The Alchemiser - Advanced Multi-Strategy Quantitative Trading System[/bold].

    Nuclear • TECL • KLM • Multi-Strategy Trading System

    Available commands:
    • [cyan]alchemiser signal[/cyan]                - Generate strategy signals (analysis only)
    • [cyan]alchemiser trade[/cyan]                 - Execute multi-strategy trading
    • [cyan]alchemiser status[/cyan]                - Show account status and positions
    • [cyan]alchemiser validate-indicators[/cyan]   - Validate indicators against TwelveData API
    • [cyan]alchemiser deploy[/cyan]                - Deploy to AWS Lambda with SAM
    • [cyan]alchemiser version[/cyan]               - Show version information

    [dim]Use --help with any command for detailed information.[/dim]
    """
    # Configure logging based on CLI options
    from the_alchemiser.shared.logging.logging_utils import setup_logging

    if verbose:
        log_level = logging.DEBUG
        console_level = logging.DEBUG
        console.print("[dim]Verbose mode enabled[/dim]")
    elif quiet:
        log_level = logging.WARNING
        console_level = logging.ERROR
    else:
        log_level = logging.WARNING
        console_level = logging.WARNING

    # Setup CLI-friendly logging
    setup_logging(
        log_level=log_level,
        console_level=console_level,
        suppress_third_party=True,
        structured_format=False,  # Human-readable for CLI
    )

    # Store context for subcommands
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet


if __name__ == "__main__":
    app()
