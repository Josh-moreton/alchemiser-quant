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
    TradingClientError,
)

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


# Signal command removed as part of CLI simplification.
# Use 'alchemiser trade' for strategy execution with integrated signal analysis.


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
        # Legacy TradingServiceManager migrated to execution_v2.ExecutionManager

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
            from the_alchemiser.shared.cli.strategy_tracking_utils import (
                display_detailed_strategy_positions,
            )

            display_detailed_strategy_positions(paper_trading=paper_trading)

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


# DSL count command removed as part of CLI simplification.
# DSL functionality has been fully removed from the system.


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


# Indicator validation command removed as part of CLI simplification.
# Technical indicators are tested through standard unit tests instead.


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
