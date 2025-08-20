#!/usr/bin/env python3
"""
Command-Line Interface for The Alchemiser Quantitative Trading System.

Provides a modern CLI built with Typer and Rich for user interaction, strategy selection,
and reporting. Handles user commands and displays formatted output.
"""

import logging
import subprocess
import time
from datetime import datetime

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

from the_alchemiser.application.trading.engine_service import TradingEngine
from the_alchemiser.infrastructure.logging.logging_utils import (
    get_logger,
    log_error_with_context,
)
from the_alchemiser.infrastructure.secrets.secrets_manager import secrets_manager
from the_alchemiser.interface.cli.cli_formatter import render_account_info
from the_alchemiser.services.errors.exceptions import (
    AlchemiserError,
    StrategyExecutionError,
    TradingClientError,
)
from the_alchemiser.services.errors.handler import TradingSystemErrorHandler
from the_alchemiser.services.trading.trading_service_manager import TradingServiceManager
from the_alchemiser.utils.feature_flags import type_system_v2_enabled

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
    welcome_text.append(" The Alchemiser Quantitative Trading System\n", style="bold cyan")
    welcome_text.append("Advanced Multi-Strategy Trading System", style="italic")

    panel = Panel(
        welcome_text,
        title="[bold blue]Welcome[/bold blue]",
        subtitle="[italic]Nuclear • TECL • KLM • Multi-Strategy[/italic]",
        border_style="blue",
        padding=(1, 2),
    )
    console.print(panel)
    console.print()


@app.command()
def signal(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    no_header: bool = typer.Option(False, "--no-header", help="Skip welcome header"),
) -> None:
    """
    🎯 [bold cyan]Generate and display strategy signals[/bold cyan] (analysis only, no trading)

    Analyzes market conditions and generates trading signals from multiple strategies:
    • Nuclear strategy (nuclear sector + market conditions)
    • TECL strategy (tech leverage + volatility hedging)
    • KLM strategy (ensemble machine learning)
    • Market regime analysis (bull/bear/overbought conditions)

    Perfect for:
    • Market analysis without trading
    • Strategy validation
    • Understanding current market signals
    """
    if not no_header:
        show_welcome()

    console.print("[bold yellow]Analyzing market conditions...[/bold yellow]")

    # Clean progress indication without spinner interference
    console.print("[dim]📊 Generating strategy signals...[/dim]")

    try:
        # Import and run the main logic with DI
        from the_alchemiser.main import main

        # Build argv for main function
        argv = ["signal"]

        success = main(argv=argv)

        if success:
            console.print("\n[bold green]Signal analysis completed successfully![/bold green]")
        else:
            console.print("\n[bold red]Signal analysis failed![/bold red]")
            raise typer.Exit(1)

    except StrategyExecutionError as e:
        error_handler.handle_error(
            error=e,
            context="CLI signal command - strategy execution",
            component="cli.signal",
            additional_data={
                "verbose": verbose,
                "error_type": type(e).__name__
            }
        )
        console.print(f"\n[bold red]Strategy execution error: {e}[/bold red]")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)
    except AlchemiserError as e:
        error_handler.handle_error(
            error=e,
            context="CLI signal command - application error", 
            component="cli.signal",
            additional_data={
                "verbose": verbose,
                "error_type": type(e).__name__
            }
        )
        console.print(f"\n[bold red]Application error: {e}[/bold red]")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)
    except (ImportError, AttributeError, ValueError, KeyError, TypeError, OSError) as e:
        error_handler = TradingSystemErrorHandler()
        error_handler.handle_error(
            error=e,
            context="CLI signal command - unexpected system error",
            component="cli.signal", 
            additional_data={
                "verbose": verbose,
                "error_type": "unexpected_error",
                "original_error": type(e).__name__
            }
        )
        console.print(f"\n[bold red]Unexpected error: {e}[/bold red]")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)


@app.command()
def trade(
    live: bool = typer.Option(False, "--live", help="🚨 Enable LIVE trading (real money)"),
    ignore_market_hours: bool = typer.Option(
        False, "--ignore-market-hours", help="Trade outside market hours (testing only)"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    no_header: bool = typer.Option(False, "--no-header", help="Skip welcome header"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompts"),
) -> None:
    """
    💰 [bold green]Execute multi-strategy trading[/bold green]

    Runs Nuclear, TECL, and KLM strategies with automatic portfolio allocation.
    Default mode is paper trading for safety.

    [bold red]⚠️  Use --live flag for real money trading![/bold red]
    """
    if not no_header:
        show_welcome()

    # Live mode proceeds without interactive confirmations
    if live:
        console.print(
            "[dim yellow]LIVE trading mode active. Proceeding without confirmation.[/dim yellow]"
        )

    mode_display = "[bold red]LIVE[/bold red]" if live else "[bold blue]PAPER[/bold blue]"
    console.print(f"[bold yellow]Starting {mode_display} trading...[/bold yellow]")

    try:
        # Import and run the main trading logic with DI
        from the_alchemiser.main import main

        console.print("[dim]📊 Analyzing market conditions...[/dim]")
        time.sleep(0.5)  # Brief pause for UI

        console.print("[dim]⚡ Generating strategy signals...[/dim]")

        # Build argv for main function
        argv = ["trade"]
        if live:
            argv.append("--live")
        if ignore_market_hours:
            argv.append("--ignore-market-hours")

        result = main(argv=argv)

        console.print("[dim]✅ Trading completed![/dim]")

        if result:
            console.print(
                f"\n[bold green]{mode_display} trading completed successfully![/bold green]"
            )
        else:
            console.print(f"\n[bold red]{mode_display} trading failed![/bold red]")
            raise typer.Exit(1)

    except StrategyExecutionError as e:
        logger = get_logger(__name__)
        log_error_with_context(
            logger,
            e,
            "cli_trading_execution",
            function="trade",
            command="trade",
            live_trading=live,
            ignore_market_hours=ignore_market_hours,
            error_type=type(e).__name__,
        )
        console.print(f"\n[bold red]Strategy execution error: {e}[/bold red]")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)
    except TradingClientError as e:
        logger = get_logger(__name__)
        log_error_with_context(
            logger,
            e,
            "cli_trading_client_error",
            function="trade",
            command="trade",
            live_trading=live,
            ignore_market_hours=ignore_market_hours,
            error_type=type(e).__name__,
        )
        console.print(f"\n[bold red]Trading client error: {e}[/bold red]")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)
    except AlchemiserError as e:
        logger = get_logger(__name__)
        log_error_with_context(
            logger,
            e,
            "cli_trading_application_error",
            function="trade",
            command="trade",
            live_trading=live,
            ignore_market_hours=ignore_market_hours,
            error_type=type(e).__name__,
        )
        console.print(f"\n[bold red]Application error: {e}[/bold red]")
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
            live_trading=live,
            ignore_market_hours=ignore_market_hours,
            error_type="unexpected_error",
            original_error=type(e).__name__,
        )
        console.print(f"\n[bold red]Unexpected error: {e}[/bold red]")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)


@app.command()
def status(
    live: bool = typer.Option(False, "--live", help="🚨 Show LIVE account status (real account)"),
) -> None:
    """
    📈 [bold blue]Show account status and positions[/bold blue]

    Displays current account balance, positions, portfolio performance, and P&L.
    Use --live flag to view live account instead of paper account.
    """
    show_welcome()

    # Determine mode and add safety warning for live mode
    paper_trading = not live
    mode_display = "[bold red]LIVE[/bold red]" if live else "[bold blue]PAPER[/bold blue]"

    if live:
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

        # Create trader and data provider for the specified mode
        trader = TradingEngine(paper_trading=paper_trading)

        account_info = trader.get_account_info()

        # Prefer enriched typed account summary when the feature flag is ON
        tsm: TradingServiceManager | None = None
        if type_system_v2_enabled():
            try:
                api_key, secret_key = secrets_manager.get_alpaca_keys(paper_trading=not live)
                if not api_key or not secret_key:
                    raise RuntimeError("Alpaca credentials not available")
                tsm = TradingServiceManager(api_key, secret_key, paper=not live)
                enriched = tsm.get_account_summary_enriched()
                # If enriched path returned a wrapped structure, use the summary for display
                if isinstance(enriched, dict) and "summary" in enriched:
                    account_info = enriched["summary"]
            except Exception as e:
                console.print(f"[dim yellow]Enriched account summary unavailable: {e}[/dim yellow]")

        if account_info:
            render_account_info(account_info)

            # Optional enriched positions display using the new typed path
            if type_system_v2_enabled():
                try:
                    # Reuse TSM if available, otherwise instantiate
                    if tsm is None:
                        api_key, secret_key = secrets_manager.get_alpaca_keys(
                            paper_trading=not live
                        )
                        if not api_key or not secret_key:
                            raise RuntimeError("Alpaca credentials not available")
                        tsm = TradingServiceManager(api_key, secret_key, paper=not live)
                    enriched_positions = tsm.get_positions_enriched()
                    if enriched_positions:
                        table = Table(
                            title="Open Positions (Enriched)", show_lines=True, expand=True
                        )
                        table.add_column("Symbol", style="bold cyan")
                        table.add_column("Qty", justify="right")
                        table.add_column("Avg Price", justify="right")
                        table.add_column("Current", justify="right")
                        table.add_column("Mkt Value", justify="right")
                        table.add_column("Unrlzd P&L", justify="right")

                        for item in enriched_positions[:50]:  # Cap display to avoid huge tables
                            summary = item.get("summary", {})
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
            console.print("[bold green]Account status retrieved successfully![/bold green]")
        else:
            console.print("[bold red]Could not retrieve account status![/bold red]")
            raise typer.Exit(1)

    except TradingClientError as e:
        error_handler = TradingSystemErrorHandler()
        error_handler.handle_error(
            error=e,
            context="CLI status command - trading client operation", 
            component="cli.status",
            additional_data={
                "live_trading": live,
                "error_type": type(e).__name__
            }
        )
        console.print(f"[bold red]Trading client error: {e}[/bold red]")
        raise typer.Exit(1)
    except AlchemiserError as e:
        error_handler = TradingSystemErrorHandler()
        error_handler.handle_error(
            error=e,
            context="CLI status command - application error",
            component="cli.status", 
            additional_data={
                "live_trading": live,
                "error_type": type(e).__name__
            }
        )
        console.print(f"[bold red]Application error: {e}[/bold red]")
        raise typer.Exit(1)
    except (ImportError, AttributeError, ValueError, KeyError, TypeError, OSError) as e:
        error_handler.handle_error(
            error=e,
            context="CLI status command - unexpected system error",
            component="cli.status",
            additional_data={
                "live_trading": live,
                "error_type": "unexpected_error",
                "original_error": type(e).__name__
            }
        )
        console.print(f"[bold red]Unexpected error: {e}[/bold red]")
        raise typer.Exit(1)


@app.command()
def deploy() -> None:
    """
    🚀 [bold cyan]Deploy to AWS Lambda[/bold cyan]

    Builds and deploys to AWS Lambda using SAM (Serverless Application Model).
    """
    show_welcome()

    console.print("[bold yellow]🔨 Building and deploying to AWS Lambda with SAM...[/bold yellow]")

    deploy_script = "scripts/deploy.sh"

    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
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
    """
    ℹ️  [bold]Show version information[/bold]
    """
    version_info = Text()
    version_info.append(" The Alchemiser Quantitative Trading System\n", style="bold cyan")
    version_info.append("Version: 2.0.0\n", style="bold")
    version_info.append(f"Built: {datetime.now().strftime('%Y-%m-%d')}\n", style="dim")
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
    """
    🔬 [bold blue]Validate technical indicators against TwelveData API[/bold blue]

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
        from the_alchemiser.infrastructure.secrets.secrets_manager import secrets_manager

        api_key = secrets_manager.get_twelvedata_api_key()

        if not api_key:
            console.print("[red]Error: TwelveData API key not found in AWS Secrets Manager.[/red]")
            console.print("Please add TWELVEDATA_KEY to the 'nuclear-secrets' secret.")
            console.print("Get a free API key at: https://twelvedata.com")
            raise typer.Exit(1)

        # Import the validation suite
        from the_alchemiser.infrastructure.validation.indicator_validator import (
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
    """
    [bold]The Alchemiser - Advanced Multi-Strategy Quantitative Trading System[/bold]

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
    from the_alchemiser.infrastructure.logging.logging_utils import setup_logging

    if verbose:
        log_level = logging.DEBUG
        console_level = logging.INFO
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
