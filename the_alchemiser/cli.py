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
from rich.live import Live

import time
from datetime import datetime, timedelta

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
def signal(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    no_header: bool = typer.Option(False, "--no-header", help="Skip welcome header")
):
    """
    🎯 [bold cyan]Generate and display strategy signals[/bold cyan] (analysis only, no trading)
    
    Analyzes market conditions and generates trading signals from multiple strategies:
    • Nuclear strategy (nuclear sector + market conditions)
    • TECL strategy (tech leverage + volatility hedging)
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
            
            # Get portfolio history for P&L trends
            console.print("\n[bold yellow]Fetching portfolio history...[/bold yellow]")
            portfolio_history = data_provider.get_portfolio_history()
            
            if portfolio_history and 'equity' in portfolio_history:
                equity_data = portfolio_history['equity']
                profit_loss = portfolio_history.get('profit_loss', [])
                profit_loss_pct = portfolio_history.get('profit_loss_pct', [])
                
                if len(equity_data) >= 2:
                    current_equity = equity_data[-1]
                    prev_equity = equity_data[-2] if len(equity_data) > 1 else equity_data[0]
                    daily_change = current_equity - prev_equity
                    daily_change_pct = (daily_change / prev_equity * 100) if prev_equity > 0 else 0
                    
                    # Recent P&L summary
                    recent_pl = profit_loss[-1] if profit_loss else 0
                    recent_pl_pct = profit_loss_pct[-1] if profit_loss_pct else 0
                    
                    pl_content = f"""[bold green]Current Equity:[/bold green] ${current_equity:,.2f}
[bold blue]Daily Change:[/bold blue] ${daily_change:+,.2f} ({daily_change_pct:+.2f}%)
[bold yellow]Recent P&L:[/bold yellow] ${recent_pl:+,.2f} ({recent_pl_pct:+.2f}%)
[bold cyan]Base Value:[/bold cyan] ${portfolio_history.get('base_value', 0):,.2f}"""
                    
                    console.print(Panel(pl_content, title="PORTFOLIO PERFORMANCE", style="bold white"))
            
            # Get open positions for detailed P&L
            console.print("\n[bold yellow]Fetching current positions...[/bold yellow]")
            open_positions = data_provider.get_open_positions()
            
            if open_positions:
                table = Table(title="📈 CURRENT POSITIONS", show_lines=True, expand=True)
                table.add_column("Symbol", style="bold cyan", justify="center")
                table.add_column("Quantity", style="white", justify="right")
                table.add_column("Avg Price", style="white", justify="right")
                table.add_column("Current Price", style="white", justify="right")
                table.add_column("Market Value", style="green", justify="right")
                table.add_column("Unrealized P&L", style="bold", justify="right")
                table.add_column("P&L %", style="bold", justify="right")
                
                total_market_value = 0
                total_unrealized_pl = 0
                
                for position in open_positions:
                    symbol = position.get('symbol', 'N/A')
                    qty = float(position.get('qty', 0))
                    avg_price = float(position.get('avg_entry_price', 0))
                    current_price = float(position.get('current_price', 0))
                    market_value = float(position.get('market_value', 0))
                    unrealized_pl = float(position.get('unrealized_pl', 0))
                    unrealized_plpc = float(position.get('unrealized_plpc', 0)) * 100
                    
                    total_market_value += market_value
                    total_unrealized_pl += unrealized_pl
                    
                    # Color coding for P&L
                    pl_color = "green" if unrealized_pl >= 0 else "red"
                    pl_sign = "+" if unrealized_pl >= 0 else ""
                    
                    table.add_row(
                        symbol,
                        f"{qty:.6f}",
                        f"${avg_price:.2f}",
                        f"${current_price:.2f}",
                        f"${market_value:,.2f}",
                        f"[{pl_color}]{pl_sign}${unrealized_pl:,.2f}[/{pl_color}]",
                        f"[{pl_color}]{pl_sign}{unrealized_plpc:.2f}%[/{pl_color}]"
                    )
                
                # Add totals row
                total_pl_color = "green" if total_unrealized_pl >= 0 else "red"
                total_pl_sign = "+" if total_unrealized_pl >= 0 else ""
                table.add_row(
                    "[bold]TOTAL[/bold]",
                    "-",
                    "-",
                    "-",
                    f"[bold]${total_market_value:,.2f}[/bold]",
                    f"[bold {total_pl_color}]{total_pl_sign}${total_unrealized_pl:,.2f}[/bold {total_pl_color}]",
                    f"[bold {total_pl_color}]{total_pl_sign}{(total_unrealized_pl/total_market_value*100) if total_market_value > 0 else 0:.2f}%[/bold {total_pl_color}]"
                )
                
                console.print(table)
            else:
                console.print(Panel("No open positions", title="CURRENT POSITIONS", style="yellow"))
            
            # Display recent closed position P&L
            if account_info.get('recent_closed_pnl'):
                console.print("\n[bold yellow]Analyzing recent closed positions P&L...[/bold yellow]")
                closed_pnl = account_info['recent_closed_pnl']
                
                if closed_pnl:
                    closed_table = Table(title="📊 RECENT CLOSED POSITIONS P&L (Last 7 Days)", show_lines=True, expand=True)
                    closed_table.add_column("Symbol", style="bold cyan", justify="center")
                    closed_table.add_column("Realized P&L", style="bold", justify="right")
                    closed_table.add_column("P&L %", style="bold", justify="right")
                    closed_table.add_column("Trade Count", style="white", justify="center")
                    closed_table.add_column("Last Trade", style="white", justify="center")
                    
                    total_realized_pnl = 0
                    
                    for position in closed_pnl[:10]:  # Show top 10 closed positions
                        symbol = position.get('symbol', 'N/A')
                        realized_pnl = position.get('realized_pnl', 0)
                        realized_pnl_pct = position.get('realized_pnl_pct', 0)
                        trade_count = position.get('trade_count', 0)
                        last_trade = position.get('last_trade_date', '')
                        
                        total_realized_pnl += realized_pnl
                        
                        # Color coding for P&L
                        pnl_color = "green" if realized_pnl >= 0 else "red"
                        pnl_sign = "+" if realized_pnl >= 0 else ""
                        
                        # Format last trade date
                        try:
                            from datetime import datetime
                            trade_date = datetime.fromisoformat(last_trade.replace('Z', '+00:00'))
                            formatted_date = trade_date.strftime('%m/%d %H:%M')
                        except:
                            formatted_date = last_trade[:10] if last_trade else 'N/A'
                        
                        closed_table.add_row(
                            symbol,
                            f"[{pnl_color}]{pnl_sign}${realized_pnl:,.2f}[/{pnl_color}]",
                            f"[{pnl_color}]{pnl_sign}{realized_pnl_pct:.2f}%[/{pnl_color}]",
                            str(trade_count),
                            formatted_date
                        )
                    
                    # Add total row
                    total_pnl_color = "green" if total_realized_pnl >= 0 else "red"
                    total_pnl_sign = "+" if total_realized_pnl >= 0 else ""
                    closed_table.add_row(
                        "[bold]TOTAL REALIZED[/bold]",
                        f"[bold {total_pnl_color}]{total_pnl_sign}${total_realized_pnl:,.2f}[/bold {total_pnl_color}]",
                        "-",
                        "-",
                        "-"
                    )
                    
                    console.print(closed_table)
                else:
                    console.print(Panel("No closed positions in last 7 days", title="RECENT CLOSED POSITIONS", style="yellow"))
            
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
from the_alchemiser.backtest.test_backtest import run_backtest, run_backtest_comparison, run_backtest_dual_rebalance, run_backtest_all_splits

# --- New CLI command for all-splits backtest ---
@app.command()
def backtest_all_splits(
    start: str = typer.Option("2022-04-25", help="Start date (YYYY-MM-DD)"),
    end: str = typer.Option(
        None,
        help="End date (YYYY-MM-DD, default: yesterday)",
        callback=lambda v: v or (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    ),
    initial_equity: float = typer.Option(4000, help="Initial equity for backtest"),
    slippage_bps: int = typer.Option(None, help="Slippage in basis points (default: from config.yaml)"),
    noise_factor: float = typer.Option(0.001, help="Market noise factor (default: 0.1%)"),
    deposit_amount: float = typer.Option(0.0, help="Deposit amount (e.g. 100 for £100, default: 0)"),
    deposit_frequency: Optional[str] = typer.Option(None, help="Deposit frequency: 'monthly' or 'weekly' (default: None)"),
    deposit_day: int = typer.Option(1, help="Deposit day: for monthly, day of month (1-28); for weekly, weekday (0=Mon, 6=Sun)")
):
    """
    🧪 [bold cyan]Backtest all possible splits between Nuclear and TECL strategies in 10% increments[/bold cyan]
    """
    import datetime as dt
    try:
        start_dt = dt.datetime.strptime(start, "%Y-%m-%d")
        end_dt = dt.datetime.strptime(end, "%Y-%m-%d")
    except Exception as e:
        console.print(f"[red]Invalid date format: {e}[/red]")
        raise typer.Exit(1)
    from the_alchemiser.core.config import get_config
    config = get_config()
    if slippage_bps is None:
        slippage_bps = config['alpaca'].get('slippage_bps', 5)
    console.print(f"[bold green]Running all-splits backtest from {start} to {end} with {slippage_bps} bps slippage and {noise_factor*100:.3f}% noise...")
    run_backtest_all_splits(
        start_dt,
        end_dt,
        initial_equity=initial_equity,
        slippage_bps=slippage_bps,
        noise_factor=noise_factor,
        deposit_amount=deposit_amount,
        deposit_frequency=deposit_frequency,
        deposit_day=deposit_day
    )

@app.command()
def backtest_nuclear_compare(
    start: str = typer.Option("2023-08-01", help="Start date (YYYY-MM-DD)"),
    end: str = typer.Option("2025-07-15", help="End date (YYYY-MM-DD)"),
    initial_equity: float = typer.Option(3000, help="Initial equity for backtest"),
    slippage_bps: int = typer.Option(None, help="Slippage in basis points (default: from config.yaml)"),
    noise_factor: float = typer.Option(0.001, help="Market noise factor (default: 0.1%)"),
    minute_candles: bool = typer.Option(False, "--minute-candles", help="Use minute candles for backtesting (limits historical range)")
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
    from the_alchemiser.core.config import get_config
    config = get_config()
    if slippage_bps is None:
        slippage_bps = config['alpaca'].get('slippage_bps', 5)
    console.print(f"[bold green]Running comprehensive backtest comparison from {start} to {end} with {slippage_bps} bps slippage and {noise_factor*100:.3f}% noise...")
    run_backtest_comparison(start_dt, end_dt, initial_equity=initial_equity, slippage_bps=slippage_bps, noise_factor=noise_factor, use_minute_candles=minute_candles)

@app.command()
def backtest(
    start: str = typer.Option("2022-04-25", help="Start date (YYYY-MM-DD)"),
    end: str = typer.Option("2025-07-15", help="End date (YYYY-MM-DD)"),
    initial_equity: float = typer.Option(3000, help="Initial equity for backtest"),
    price_type: str = typer.Option("open", help="Price type: close, open, mid, or vwap"),
    slippage_bps: int = typer.Option(None, help="Slippage in basis points (default: from config.yaml)"),
    noise_factor: float = typer.Option(0.001, help="Market noise factor (default: 0.1%)"),
    deposit_amount: float = typer.Option(0.0, help="Deposit amount (e.g. 100 for £100, default: 0)"),
    deposit_frequency: Optional[str] = typer.Option(None, help="Deposit frequency: 'monthly' or 'weekly' (default: None)"),
    deposit_day: int = typer.Option(1, help="Deposit day: for monthly, day of month (1-28); for weekly, weekday (0=Mon, 6=Sun)"),
    minute_candles: bool = typer.Option(False, "--minute-candles", help="Use 1-minute candles for precision (limited to ~90 days)")
):
    """
    🧪 [bold cyan]Run a realistic backtest[/bold cyan] for a given date range and price type.
    
    Uses daily candles for extended historical backtests. For higher precision execution,
    add the --minute-candles flag (limited to ~90 days of minute data).
    """
    import datetime as dt
    
    try:
        start_dt = dt.datetime.strptime(start, "%Y-%m-%d")
        end_dt = dt.datetime.strptime(end, "%Y-%m-%d")
    except Exception as e:
        console.print(f"[red]Invalid date format: {e}[/red]")
        raise typer.Exit(1)
    
    from the_alchemiser.core.config import get_config
    config = get_config()
    if slippage_bps is None:
        slippage_bps = config['alpaca'].get('slippage_bps', 5)
    
    mode_str = "1-minute candles" if minute_candles else "daily candles"
    console.print(f"[bold green]Running realistic backtest from {start} to {end} using {price_type} prices with {slippage_bps} bps slippage and {noise_factor*100:.3f}% noise ({mode_str})...")
    
    run_backtest(
        start_dt, end_dt,
        initial_equity=initial_equity,
        price_type=price_type,
        slippage_bps=slippage_bps,
        noise_factor=noise_factor,
        deposit_amount=deposit_amount,
        deposit_frequency=deposit_frequency,
        deposit_day=deposit_day,
        use_minute_candles=minute_candles
    )

@app.command()
def backtest_compare(
    start: str = typer.Option("2022-04-25", help="Start date (YYYY-MM-DD)"),
    end: str = typer.Option("2025-07-15", help="End date (YYYY-MM-DD)"),
    initial_equity: float = typer.Option(3000, help="Initial equity for backtest"),
    slippage_bps: int = typer.Option(None, help="Slippage in basis points (default: from config.yaml)"),
    noise_factor: float = typer.Option(0.001, help="Market noise factor (default: 0.1%)"),
    deposit_amount: float = typer.Option(0.0, help="Deposit amount (e.g. 100 for £100, default: 0)"),
    deposit_frequency: Optional[str] = typer.Option(None, help="Deposit frequency: 'monthly' or 'weekly' (default: None)"),
    deposit_day: int = typer.Option(1, help="Deposit day: for monthly, day of month (1-28); for weekly, weekday (0=Mon, 6=Sun)"),
    minute_candles: bool = typer.Option(False, "--minute-candles", help="Use minute candles for backtesting (limits historical range)")
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
    
    from the_alchemiser.core.config import get_config
    config = get_config()
    if slippage_bps is None:
        slippage_bps = config['alpaca'].get('slippage_bps', 5)
    console.print(f"[bold green]Running realistic backtest comparison from {start} to {end} for all modes with {slippage_bps} bps slippage and {noise_factor*100:.3f}% noise...")
    run_backtest_comparison(
        start_dt, end_dt,
        initial_equity=initial_equity,
        slippage_bps=slippage_bps,
        noise_factor=noise_factor,
        deposit_amount=deposit_amount,
        deposit_frequency=deposit_frequency,
        deposit_day=deposit_day,
        use_minute_candles=minute_candles
    )

@app.command()
def backtest_dual(
    start: str = typer.Option("2022-04-25", help="Start date (YYYY-MM-DD)"),
    end: str = typer.Option("2025-07-15", help="End date (YYYY-MM-DD)"),
    initial_equity: float = typer.Option(3000, help="Initial equity for backtest"),
    slippage_bps: int = typer.Option(None, help="Slippage in basis points (default: from config.yaml)"),
    noise_factor: float = typer.Option(0.001, help="Market noise factor (default: 0.1%)"),
    deposit_amount: float = typer.Option(0.0, help="Deposit amount (e.g. 100 for £100, default: 0)"),
    deposit_frequency: Optional[str] = typer.Option(None, help="Deposit frequency: 'monthly' or 'weekly' (default: None)"),
    deposit_day: int = typer.Option(1, help="Deposit day: for monthly, day of month (1-28); for weekly, weekday (0=Mon, 6=Sun)"),
    minute_candles: bool = typer.Option(False, "--minute-candles", help="Use minute candles for backtesting (limits historical range)")
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
    
    from the_alchemiser.core.config import get_config
    config = get_config()
    if slippage_bps is None:
        slippage_bps = config['alpaca'].get('slippage_bps', 5)
    console.print(f"[bold green]Running dual-rebalance realistic backtest from {start} to {end} with {slippage_bps} bps slippage and {noise_factor*100:.3f}% noise...")
    run_backtest_dual_rebalance(
        start_dt, end_dt,
        initial_equity=initial_equity,
        slippage_bps=slippage_bps,
        noise_factor=noise_factor,
        deposit_amount=deposit_amount,
        deposit_frequency=deposit_frequency,
        deposit_day=deposit_day,
        use_minute_candles=minute_candles
    )

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
