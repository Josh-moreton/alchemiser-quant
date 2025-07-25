
#!/usr/bin/env python3
"""
Modern CLI for The Alchemiser Trading Bot
Built with Typer and Rich for a beautiful command-line experience
"""

import typer
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.live import Live
import time
from datetime import datetime

from the_alchemiser.core.ui.cli_formatter import render_header, render_footer

# Initialize Typer app and Rich console
app = typer.Typer(
    name="alchemiser",
    help="🧪 The Alchemiser - Advanced Multi-Strategy Trading Bot",
    add_completion=False,
    rich_markup_mode="rich"
)
console = Console()

def show_welcome():
    """Display a beautiful welcome message"""
    welcome_text = Text()
    welcome_text.append("🧪 The Alchemiser Trading Bot\n", style="bold cyan")
    welcome_text.append("Advanced Multi-Strategy Nuclear Trading System", style="italic")
    
    panel = Panel(
        welcome_text,
        title="[bold blue]Welcome[/bold blue]",
        subtitle="[italic]Nuclear • TECL • Multi-Strategy[/italic]",
        border_style="blue",
        padding=(1, 2)
    )
    console.print(panel)
    console.print()

@app.command()
def bot(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    no_header: bool = typer.Option(False, "--no-header", help="Skip welcome header")
):
    """
    🎯 [bold cyan]Show multi-strategy signals[/bold cyan] (no trading)
    
    Displays signals from Nuclear and TECL strategies with technical indicators,
    portfolio allocations, and market analysis without executing any trades.
    """
    if not no_header:
        show_welcome()
    
    console.print("[bold yellow]📊 Analyzing market conditions...[/bold yellow]")
    
    # Progress indicator while analyzing
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task("Generating strategy signals...", total=None)
        
        try:
            # Import and run the main logic
            from the_alchemiser.main import run_all_signals_display
            success = run_all_signals_display()
            
            if success:
                console.print("\n[bold green]✅ Signal analysis completed successfully![/bold green]")
            else:
                console.print("\n[bold red]❌ Signal analysis failed![/bold red]")
                raise typer.Exit(1)
                
        except Exception as e:
            console.print(f"\n[bold red]❌ Error: {e}[/bold red]")
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
    
    Runs both Nuclear and TECL strategies with automatic portfolio allocation.
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
    console.print(f"[bold yellow]🚀 Starting {mode_display} trading...[/bold yellow]")
    
    try:
        # Import and run the main trading logic
        from the_alchemiser.main import run_multi_strategy_trading

        console.print("[dim]Analyzing market conditions...[/dim]")
        time.sleep(0.5)  # Brief pause for UI

        console.print("[dim]Generating strategy signals...[/dim]")
        result = run_multi_strategy_trading(
            live_trading=live,
            ignore_market_hours=ignore_market_hours
        )

        console.print("[dim]Trading completed![/dim]")

        if result == "market_closed":
            console.print("\n[bold yellow]⏰ Market is closed - no trades executed[/bold yellow]")
        elif result:
            console.print(f"\n[bold green]✅ {mode_display} trading completed successfully![/bold green]")
        else:
            console.print(f"\n[bold red]❌ {mode_display} trading failed![/bold red]")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"\n[bold red]❌ Error: {e}[/bold red]")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)

@app.command()
def status():
    """
    📈 [bold blue]Show account status and positions[/bold blue]
    
    Displays current account balance, positions, and portfolio performance.
    """
    show_welcome()
    
    console.print("[bold yellow]📊 Fetching account status...[/bold yellow]")
    
    try:
        from the_alchemiser.execution.alpaca_trader import AlpacaTradingBot
        from the_alchemiser.core.ui.cli_formatter import render_account_info
        
        # Create trader to get account info
        trader = AlpacaTradingBot(paper_trading=True)  # Always use paper for status
        account_info = trader.get_account_info()
        
        if account_info:
            render_account_info(account_info)
            console.print("[bold green]✅ Account status retrieved successfully![/bold green]")
        else:
            console.print("[bold red]❌ Could not retrieve account status![/bold red]")
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"[bold red]❌ Error: {e}[/bold red]")
        raise typer.Exit(1)

@app.command()
def deploy():
    """
    🚀 [bold cyan]Deploy to AWS Lambda[/bold cyan]
    
    Builds Docker image and deploys to AWS Lambda using ECR.
    """
    show_welcome()
    
    console.print("[bold yellow]🔨 Building and deploying to AWS Lambda...[/bold yellow]")
    
    deploy_script = "/Users/joshmoreton/GitHub/The-Alchemiser/scripts/build_and_push_lambda.sh"
    
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
    version_info.append("🧪 The Alchemiser Trading Bot\n", style="bold cyan")
    version_info.append(f"Version: 2.0.0\n", style="bold")
    version_info.append(f"Built: {datetime.now().strftime('%Y-%m-%d')}\n", style="dim")
    version_info.append("Strategies: Nuclear, TECL, Multi-Strategy\n", style="green")
    version_info.append("Platform: Alpaca Markets", style="blue")
    
    console.print(Panel(
        version_info,
        title="[bold]Version Info[/bold]",
        border_style="cyan"
    ))

# Clean imports now that backtest functions are in the main package
from the_alchemiser.backtest.test_backtest import run_backtest, run_backtest_comparison, run_backtest_dual_rebalance

@app.command()
def backtest_nuclear_compare(
    start: str = typer.Option("2023-08-01", help="Start date (YYYY-MM-DD)"),
    end: str = typer.Option("2025-07-15", help="End date (YYYY-MM-DD)"),
    initial_equity: float = typer.Option(10000, help="Initial equity for backtest"),
    slippage_bps: int = typer.Option(5, help="Slippage in basis points (default: 5 bps)"),
    noise_factor: float = typer.Option(0.001, help="Market noise factor (default: 0.1%)")
):
    """
    ⚖️ [bold cyan]Compare nuclear portfolio strategies[/bold cyan]
    
    Runs a comprehensive backtest comparison with realistic execution pricing.
    """
    import datetime as dt
    try:
        start_dt = dt.datetime.strptime(start, "%Y-%m-%d")
        end_dt = dt.datetime.strptime(end, "%Y-%m-%d")
    except Exception as e:
        console.print(f"[red]Invalid date format: {e}[/red]")
        raise typer.Exit(1)
    console.print(f"[bold green]Running comprehensive backtest comparison from {start} to {end} with {slippage_bps} bps slippage and {noise_factor*100:.3f}% noise...")
    run_backtest_comparison(start_dt, end_dt, initial_equity=initial_equity, slippage_bps=slippage_bps, noise_factor=noise_factor)

@app.command()
def backtest(
    start: str = typer.Option("2023-01-01", help="Start date (YYYY-MM-DD)"),
    end: str = typer.Option("2025-07-15", help="End date (YYYY-MM-DD)"),
    initial_equity: float = typer.Option(10000, help="Initial equity for backtest"),
    price_type: str = typer.Option("open", help="Price type: close, open, mid, or vwap"),
    slippage_bps: int = typer.Option(5, help="Slippage in basis points (default: 5 bps)"),
    noise_factor: float = typer.Option(0.001, help="Market noise factor (default: 0.1%)")
):
    """
    🧪 [bold cyan]Run a realistic backtest[/bold cyan] for a given date range and price type.
    
    Uses 1-minute candles for realistic execution pricing with market noise simulation.
    """
    import datetime as dt
    
    try:
        start_dt = dt.datetime.strptime(start, "%Y-%m-%d")
        end_dt = dt.datetime.strptime(end, "%Y-%m-%d")
    except Exception as e:
        console.print(f"[red]Invalid date format: {e}[/red]")
        raise typer.Exit(1)
    
    console.print(f"[bold green]Running realistic backtest from {start} to {end} using {price_type} prices with {slippage_bps} bps slippage and {noise_factor*100:.3f}% noise...")
    run_backtest(start_dt, end_dt, initial_equity=initial_equity, price_type=price_type, slippage_bps=slippage_bps, noise_factor=noise_factor)

@app.command()
def backtest_compare(
    start: str = typer.Option("2023-01-01", help="Start date (YYYY-MM-DD)"),
    end: str = typer.Option("2025-07-15", help="End date (YYYY-MM-DD)"),
    initial_equity: float = typer.Option(10000, help="Initial equity for backtest"),
    slippage_bps: int = typer.Option(5, help="Slippage in basis points (default: 5 bps)"),
    noise_factor: float = typer.Option(0.001, help="Market noise factor (default: 0.1%)")
):
    """
    📊 [bold cyan]Compare realistic backtest results[/bold cyan] across all price types and dual-rebalance.
    
    Tests close, open, mid, VWAP execution with 1-minute realistic pricing and market noise.
    """
    import datetime as dt
    
    try:
        start_dt = dt.datetime.strptime(start, "%Y-%m-%d")
        end_dt = dt.datetime.strptime(end, "%Y-%m-%d")
    except Exception as e:
        console.print(f"[red]Invalid date format: {e}[/red]")
        raise typer.Exit(1)
    
    console.print(f"[bold green]Running realistic backtest comparison from {start} to {end} for all modes with {slippage_bps} bps slippage and {noise_factor*100:.3f}% noise...")
    run_backtest_comparison(start_dt, end_dt, initial_equity=initial_equity, slippage_bps=slippage_bps, noise_factor=noise_factor)

@app.command()
def backtest_dual(
    start: str = typer.Option("2023-01-01", help="Start date (YYYY-MM-DD)"),
    end: str = typer.Option("2025-07-15", help="End date (YYYY-MM-DD)"),
    initial_equity: float = typer.Option(10000, help="Initial equity for backtest"),
    slippage_bps: int = typer.Option(5, help="Slippage in basis points (default: 5 bps)"),
    noise_factor: float = typer.Option(0.001, help="Market noise factor (default: 0.1%)")
):
    """
    🔄 [bold cyan]Run a dual-rebalance realistic backtest[/bold cyan] with 2 rebalances per day.
    
    Performs portfolio rebalancing at both market open and close using 1-minute candles
    for realistic execution pricing with market noise simulation.
    """
    import datetime as dt
    
    try:
        start_dt = dt.datetime.strptime(start, "%Y-%m-%d")
        end_dt = dt.datetime.strptime(end, "%Y-%m-%d")
    except Exception as e:
        console.print(f"[red]Invalid date format: {e}[/red]")
        raise typer.Exit(1)
    
    console.print(f"[bold green]Running dual-rebalance realistic backtest from {start} to {end} with {slippage_bps} bps slippage and {noise_factor*100:.3f}% noise...")
    run_backtest_dual_rebalance(start_dt, end_dt, initial_equity=initial_equity, slippage_bps=slippage_bps, noise_factor=noise_factor)

@app.callback()
def main(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress non-essential output")
):
    """
    🧪 [bold cyan]The Alchemiser[/bold cyan] - Advanced Multi-Strategy Trading Bot
    
    A sophisticated trading system combining Nuclear and TECL strategies
    with beautiful CLI interface and comprehensive market analysis.
    
    [bold]Quick Start:[/bold]
    • [cyan]alchemiser bot[/cyan]               - Show strategy signals
    • [cyan]alchemiser trade[/cyan]             - Paper trading
    • [cyan]alchemiser trade --live[/cyan]      - Live trading (⚠️ real money)
    • [cyan]alchemiser status[/cyan]            - Account information
    
    [bold]Backtesting (Realistic with 1-min data):[/bold]
    • [cyan]alchemiser backtest[/cyan]          - Single rebalance backtest
    • [cyan]alchemiser backtest-dual[/cyan]     - Dual rebalance (2x daily)
    • [cyan]alchemiser backtest-compare[/cyan]  - Compare all execution modes
    • [cyan]alchemiser backtest-nuclear-compare[/cyan] - Nuclear strategy comparison
    
    [dim]Use --help with any command for detailed information.[/dim]
    """
    # Set global verbosity
    if verbose:
        console.print("[dim]Verbose mode enabled[/dim]")
    
    # Store context for subcommands
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['quiet'] = quiet

if __name__ == "__main__":
    app()
