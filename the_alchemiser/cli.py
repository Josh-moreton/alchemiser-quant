#!/usr/bin/env python3
"""
Command-Line Interface for The Alchemiser Trading Bot.

Provides a modern CLI built with Typer and Rich for user interaction, strategy selection,
backtesting, and reporting. Handles user commands and displays formatted output.
"""

import typer
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

import time
from datetime import datetime, timedelta

from the_alchemiser.core.ui.cli_formatter import render_header, render_footer

# Initialize Typer app and Rich console
app = typer.Typer(
    name="alchemiser",
    help="The Alchemiser - Advanced Multi-Strategy Trading Bot",
    add_completion=False,
    rich_markup_mode="rich"
)
console = Console()

def show_welcome():
    """Display a beautiful welcome message"""
    welcome_text = Text()
    welcome_text.append(" The Alchemiser Trading Bot\n", style="bold cyan")
    welcome_text.append("Advanced Multi-Strategy Nuclear Trading System", style="italic")
    
    panel = Panel(
        welcome_text,
        title="[bold blue]Welcome[/bold blue]",
        subtitle="[italic]Nuclear • TECL • KLM • Multi-Strategy[/italic]",
        border_style="blue",
        padding=(1, 2)
    )
    console.print(panel)
    console.print()

@app.command()
def signal(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    no_header: bool = typer.Option(False, "--no-header", help="Skip welcome header")
):
    """
    🎯 [bold cyan]Generate and display strategy signals[/bold cyan] (analysis only, no trading)
    
    Analyzes market conditions and generates trading signals from multiple strategies:
    • Nuclear strategy (nuclear sector + market conditions)
    • TECL strategy (tech leverage + volatility hedging)
    • KLM strategy (ensemble machine learning)
    • Market regime analysis (bull/bear/overbought conditions)
    
    Perfect for:
    • Market analysis without trading
    • Strategy validation and backtesting
    • Understanding current market signals
    """
    if not no_header:
        show_welcome()
    
    console.print("[bold yellow]Analyzing market conditions...[/bold yellow]")
    
    # Clean progress indication without spinner interference
    console.print("[dim]📊 Generating strategy signals...[/dim]")
    
    try:
        # Import and run the main logic
        from the_alchemiser.main import run_all_signals_display
        success = run_all_signals_display()
        
        if success:
            console.print("\n[bold green]Signal analysis completed successfully![/bold green]")
        else:
            console.print("\n[bold red]Signal analysis failed![/bold red]")
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"\n[bold red]Error: {e}[/bold red]")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)

@app.command()
def trade(
    live: bool = typer.Option(False, "--live", help="🚨 Enable LIVE trading (real money)"),
    ignore_market_hours: bool = typer.Option(False, "--ignore-market-hours", help="Trade outside market hours (testing only)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    no_header: bool = typer.Option(False, "--no-header", help="Skip welcome header"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompts")
):
    """
    💰 [bold green]Execute multi-strategy trading[/bold green]
    
    Runs Nuclear, TECL, and KLM strategies with automatic portfolio allocation.
    Default mode is paper trading for safety.
    
    [bold red]⚠️  Use --live flag for real money trading![/bold red]
    """
    if not no_header:
        show_welcome()
    
    # Safety confirmation for live trading
    if live and not force:
        console.print(Panel(
            "[bold red]⚠️  LIVE TRADING MODE[/bold red]\n\n"
            "This will place real orders with real money!\n"
            "Make sure you understand the risks.",
            title="[bold red]Warning[/bold red]",
            border_style="red"
        ))
        
        if not Confirm.ask("Are you sure you want to proceed with LIVE trading?"):
            console.print("[yellow]Operation cancelled.[/yellow]")
            raise typer.Exit(0)
    
    mode_display = "[bold red]LIVE[/bold red]" if live else "[bold blue]PAPER[/bold blue]"
    console.print(f"[bold yellow]Starting {mode_display} trading...[/bold yellow]")
    
    try:
        # Import and run the main trading logic
        from the_alchemiser.main import run_multi_strategy_trading

        console.print("[dim]📊 Analyzing market conditions...[/dim]")
        time.sleep(0.5)  # Brief pause for UI

        console.print("[dim]⚡ Generating strategy signals...[/dim]")
        result = run_multi_strategy_trading(
            live_trading=live,
            ignore_market_hours=ignore_market_hours
        )

        console.print("[dim]✅ Trading completed![/dim]")

        if result == "market_closed":
            console.print("\n[bold yellow]Market is closed - no trades executed[/bold yellow]")
        elif result:
            console.print(f"\n[bold green]{mode_display} trading completed successfully![/bold green]")
        else:
            console.print(f"\n[bold red]{mode_display} trading failed![/bold red]")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"\n[bold red]Error: {e}[/bold red]")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)

@app.command()
def status(
    live: bool = typer.Option(False, "--live", help="🚨 Show LIVE account status (real account)")
):
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
        from rich.panel import Panel
        console.print(
            Panel(
                "[bold red]⚠️  LIVE ACCOUNT STATUS[/bold red]\n\n"
                "You are viewing your LIVE trading account with real money.\n"
                "This shows actual positions and P&L from your live account.",
                style="bold red",
                expand=False
            )
        )
    
    console.print(f"[bold yellow]Fetching {mode_display} account status...[/bold yellow]")
    
    try:
        from the_alchemiser.execution.trading_engine import TradingEngine
        from the_alchemiser.core.ui.cli_formatter import render_account_info
        from the_alchemiser.core.data.data_provider import UnifiedDataProvider
        from rich.table import Table
        from rich.panel import Panel
        
        # Create trader and data provider for the specified mode
        trader = TradingEngine(paper_trading=paper_trading)
        data_provider = UnifiedDataProvider(paper_trading=paper_trading)
        
        account_info = trader.get_account_info()
        
        if account_info:
            render_account_info(account_info)
            console.print("[bold green]Account status retrieved successfully![/bold green]")
        else:
            console.print("[bold red]Could not retrieve account status![/bold red]")
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        raise typer.Exit(1)

@app.command()
def deploy():
    """
    🚀 [bold cyan]Deploy to AWS Lambda[/bold cyan]
    
    Builds Docker image and deploys to AWS Lambda using ECR.
    """
    show_welcome()
    
    console.print("[bold yellow]🔨 Building and deploying to AWS Lambda...[/bold yellow]")
    
    deploy_script = "scripts/build_and_push_lambda.sh"
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Running deployment script...", total=None)
        
        try:
            import subprocess
            result = subprocess.run(
                ["bash", deploy_script],
                capture_output=True,
                text=True,
                check=True
            )
            
            console.print("[bold green]✅ Deployment completed successfully![/bold green]")
            console.print("\n[dim]Deployment output:[/dim]")
            console.print(result.stdout)
            
        except subprocess.CalledProcessError as e:
            console.print(f"[bold red]❌ Deployment failed![/bold red]")
            console.print(f"[dim]Error output:[/dim]\n{e.stderr}")
            raise typer.Exit(1)
        except Exception as e:
            console.print(f"[bold red]❌ Error: {e}[/bold red]")
            raise typer.Exit(1)

@app.command()
def version():
    """
    ℹ️  [bold]Show version information[/bold]
    """
    version_info = Text()
    version_info.append(" The Alchemiser Trading Bot\n", style="bold cyan")
    version_info.append(f"Version: 2.0.0\n", style="bold")
    version_info.append(f"Built: {datetime.now().strftime('%Y-%m-%d')}\n", style="dim")
    version_info.append("Strategies: Nuclear, TECL, KLM, Multi-Strategy\n", style="green")
    version_info.append("Platform: Alpaca Markets", style="blue")
    
    console.print(Panel(
        version_info,
        title="[bold]Version Info[/bold]",
        border_style="cyan"
    ))


# Import new clean backtest engine
from the_alchemiser.backtest.engine import (
    BacktestEngine,
    BacktestResult
)

# --- Main Backtest Command (Clean Interface) ---
@app.command()
def backtest(
    mode: str = typer.Option("live", help="Backtest mode: individual, live, or all"),
    strategy: Optional[str] = typer.Option(None, help="Strategy for individual mode: nuclear, tecl, or klm"),
    start: str = typer.Option("2025-01-01", help="Start date (YYYY-MM-DD, default: 2025-01-01)"),
    end: str = typer.Option(
        None,
        help="End date (YYYY-MM-DD, default: 3 days ago)",
        callback=lambda v: v or (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    ),
    initial_equity: float = typer.Option(1000.0, help="Initial equity"),
    slippage_bps: int = typer.Option(8, help="Slippage in basis points"),
    noise_factor: float = typer.Option(0.0015, help="Market noise factor"),
    step_size: int = typer.Option(10, help="Weight increment for all mode (10 = 10% steps)"),
    max_workers: int = typer.Option(4, help="Number of parallel threads for all mode"),
    deposit_amount: float = typer.Option(0.0, help="Regular deposit amount"),
    deposit_frequency: Optional[str] = typer.Option(None, help="Deposit frequency: monthly or weekly"),
    deposit_day: int = typer.Option(1, help="Deposit day"),
    minute_candles: bool = typer.Option(False, "--minute-candles", help="Use minute candles for execution")
):
    """
    Clean backtest interface - individual, live, or all weight combinations
    
    Examples:
      alchemiser backtest --mode individual --strategy nuclear
      alchemiser backtest --mode live  
      alchemiser backtest --mode all --step-size 20 --max-workers 6
    
    This backtest engine uses REAL strategy engines (Nuclear, TECL, KLM) to provide 
    faithful representation of live trading performance.
    """
    
    # Validate mode and strategy combination
    if mode not in ["individual", "live", "all"]:
        console.print(f"[red]Error: Invalid mode '{mode}'. Must be: individual, live, or all")
        raise typer.Exit(1)
    
    if mode == 'individual':
        if not strategy:
            console.print("[red]Error: --strategy required for individual mode[/red]")
            raise typer.Exit(1)
        if strategy.lower() not in ['nuclear', 'tecl', 'klm']:
            console.print("[red]Error: Strategy must be one of: nuclear, tecl, klm[/red]")
            raise typer.Exit(1)
    
    try:
        start_dt = datetime.strptime(start, "%Y-%m-%d")
        end_dt = datetime.strptime(end, "%Y-%m-%d")
    except Exception as e:
        console.print(f"[red]Error parsing dates: {e}[/red]")
        raise typer.Exit(1)
    
    # Run appropriate backtest
    engine = BacktestEngine(use_cache=True)
    
    if mode == 'individual':
        if not strategy:
            console.print("[red]Strategy is required for individual mode[/red]")
            raise typer.Exit(1)
            
        result = engine.run_individual_strategy(
            strategy.lower(), start_dt, end_dt,
            initial_equity=initial_equity,
            slippage_bps=slippage_bps,
            noise_factor=noise_factor,
            deposit_amount=deposit_amount,
            deposit_frequency=deposit_frequency,
            deposit_day=deposit_day,
            use_minute_candles=minute_candles
        )
        
        # Display results
        from rich.table import Table
        table = Table(title="📈 Individual Strategy Backtest Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Strategy", result.strategy_name)
        table.add_row("Final Equity", f"£{result.final_equity:,.2f}")
        table.add_row("Total Return", f"{result.total_return:+.2f}%")
        table.add_row("CAGR", f"{result.cagr:.2f}%")
        table.add_row("Volatility", f"{result.volatility:.2f}%")
        table.add_row("Sharpe Ratio", f"{result.sharpe_ratio:.2f}")
        table.add_row("Max Drawdown", f"{result.max_drawdown:.2f}%")
        table.add_row("Calmar Ratio", f"{result.calmar_ratio:.2f}" if result.calmar_ratio != float('inf') else "∞")
        table.add_row("Trading Days", str(result.trading_days))
        
        console.print(table)
        
    elif mode == 'live':
        result = engine.run_live_configuration(
            start_dt, end_dt,
            initial_equity=initial_equity,
            slippage_bps=slippage_bps,
            noise_factor=noise_factor,
            deposit_amount=deposit_amount,
            deposit_frequency=deposit_frequency,
            deposit_day=deposit_day,
            use_minute_candles=minute_candles
        )
        
        # Display results
        from rich.table import Table
        table = Table(title="📈 Live Trading Configuration Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Strategy", result.strategy_name)
        table.add_row("Final Equity", f"£{result.final_equity:,.2f}")
        table.add_row("Total Return", f"{result.total_return:+.2f}%")
        table.add_row("CAGR", f"{result.cagr:.2f}%")
        table.add_row("Volatility", f"{result.volatility:.2f}%")
        table.add_row("Sharpe Ratio", f"{result.sharpe_ratio:.2f}")
        table.add_row("Max Drawdown", f"{result.max_drawdown:.2f}%")
        table.add_row("Calmar Ratio", f"{result.calmar_ratio:.2f}" if result.calmar_ratio != float('inf') else "∞")
        table.add_row("Trading Days", str(result.trading_days))
        
        console.print(table)
        
    elif mode == 'all':
        results = engine.run_all_combinations(
            start_dt, end_dt,
            initial_equity=initial_equity,
            slippage_bps=slippage_bps,
            noise_factor=noise_factor,
            step_size=step_size,
            max_workers=max_workers,
            deposit_amount=deposit_amount,
            deposit_frequency=deposit_frequency,
            deposit_day=deposit_day,
            use_minute_candles=minute_candles
        )
        # Results are already displayed in the function
    
    console.print("\n[bold green]✅ Backtest complete![/bold green]")


@app.command()
def validate_indicators(
    mode: str = typer.Option("core", help="Validation mode: quick, core, or full"),
    symbols: Optional[str] = typer.Option(None, "--symbols", help="Comma-separated symbols to test"),
    save_file: Optional[str] = typer.Option(None, "--save", help="Save results to JSON file"),
    verbose_validation: bool = typer.Option(False, "--verbose-validation", help="Enable verbose validation logging")
):
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
        from the_alchemiser.core.secrets.secrets_manager import secrets_manager
        api_key = secrets_manager.get_twelvedata_api_key()
        
        if not api_key:
            console.print("[red]Error: TwelveData API key not found in AWS Secrets Manager.[/red]")
            console.print("Please add TWELVEDATA_KEY to the 'nuclear-secrets' secret.")
            console.print("Get a free API key at: https://twelvedata.com")
            raise typer.Exit(1)
        
        # Import the validation suite
        from the_alchemiser.core.validation.indicator_validator import IndicatorValidationSuite
        
        # Validate mode
        if mode not in ["quick", "core", "full"]:
            console.print(f"[red]Error: Invalid mode '{mode}'. Must be: quick, core, or full[/red]")
            raise typer.Exit(1)
        
        # Initialize validation suite
        validator = IndicatorValidationSuite(api_key, console)
        
        # Determine symbols to test
        if symbols:
            symbols_list = [s.strip().upper() for s in symbols.split(',')]
        else:
            if mode == 'quick':
                symbols_list = ['SPY', 'QQQ']
            elif mode == 'core':
                symbols_list = validator.strategy_symbols['core']
            else:  # full
                symbols_list = []
                for category in validator.strategy_symbols.values():
                    symbols_list.extend(category)
                symbols_list = list(set(symbols_list))  # Remove duplicates
        
        console.print(f"[bold blue]🔬 Running indicator validation in {mode.upper()} mode...[/bold blue]")
        console.print(f"Testing {len(symbols_list)} symbols: {', '.join(symbols_list[:5])}{' ...' if len(symbols_list) > 5 else ''}")
        
        # Run validation
        summary = validator.run_validation_suite(symbols_list, mode)
        validator.generate_report(summary)
        
        if save_file:
            validator.save_results(save_file)
        
        if summary['failed_tests'] == 0:
            console.print("\n[bold green]✅ All indicators validated successfully![/bold green]")
        else:
            console.print(f"\n[bold yellow]⚠️  Validation completed with {summary['failed_tests']} failures[/bold yellow]")
            console.print("Check the detailed report above for specific issues.")
            
    except ImportError as e:
        console.print("[red]Error: Could not import validation suite.[/red]")
        console.print(f"Details: {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error running validation: {e}[/red]")
        if verbose_validation:
            console.print_exception()
        raise typer.Exit(1)


@app.callback()
def main(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress non-essential output")
):
    """
    [bold]The Alchemiser - Advanced Multi-Strategy Trading Bot[/bold]
    
    Nuclear • TECL • KLM • Multi-Strategy Trading System
    
    Available commands:
    • [cyan]alchemiser signal[/cyan]                - Generate strategy signals (analysis only)  
    • [cyan]alchemiser trade[/cyan]                 - Execute multi-strategy trading
    • [cyan]alchemiser backtest[/cyan]              - Run comprehensive backtests  
    • [cyan]alchemiser status[/cyan]                - Show account status and positions
    • [cyan]alchemiser validate-indicators[/cyan]   - Validate indicators against TwelveData API
    • [cyan]alchemiser deploy[/cyan]                - Deploy to AWS Lambda
    • [cyan]alchemiser version[/cyan]               - Show version information
    
    [dim]Use --help with any command for detailed information.[/dim]
    """
    # Configure logging based on CLI options
    from the_alchemiser.core.logging.logging_utils import setup_logging
    import logging
    
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
        structured_format=False  # Human-readable for CLI
    )
    
    # Store context for subcommands
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['quiet'] = quiet

if __name__ == "__main__":
    app()
