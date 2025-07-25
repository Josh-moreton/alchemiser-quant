
import os
import time
import datetime as dt
import pandas as pd
import pytest
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import track

# Hardcoded Alpaca credentials for local testing (do not use in production)
os.environ['ALPACA_PAPER_KEY'] = 'PKS7WB1KB6VVG72FF8VZ'
os.environ['ALPACA_PAPER_SECRET'] = 'Ibcd2Zy98HL3wabRMQW6R0T1SnSZ2vN1uoLWhIOQ'

from the_alchemiser.core.trading.strategy_manager import MultiStrategyManager, StrategyType
from the_alchemiser.core.data.data_provider import UnifiedDataProvider

console = Console()


def _preload_symbol_data(data_provider, symbols, start, end):
    """Fetch all required historical data in one shot."""
    console.print(f"[yellow]Loading historical data for {len(symbols)} symbols...")
    symbol_data = {}
    for sym in track(symbols, description="Fetching data"):
        bars = data_provider.get_historical_data(sym, start=start, end=end, timeframe="1Day")
        rows = []
        dates = []
        for bar in bars:
            rows.append({
                'Open': float(bar.open),
                'High': float(bar.high),
                'Low': float(bar.low),
                'Close': float(bar.close),
                'Volume': getattr(bar, 'volume', 0)
            })
            dates.append(bar.timestamp)
        symbol_data[sym] = pd.DataFrame(rows, index=pd.to_datetime(dates))
    console.print(f"[green]✓ Data loaded for {len(symbols)} symbols")
    return symbol_data


def run_backtest(start, end, initial_equity=1000, price_type="close"):

    price_type = price_type.lower()
    if price_type == 'close':
        price_selector = lambda row: row['Close']
        price_label = 'Close'
    elif price_type == 'open':
        price_selector = lambda row: row['Open']
        price_label = 'Open'
    elif price_type == 'mid':
        price_selector = lambda row: (row['High'] + row['Low'] + row['Close']) / 3
        price_label = 'Mid (HLC/3)'
    else:
        raise ValueError(f"Unknown price_type: {price_type}")

    console.print(Panel(f"[bold cyan]Starting Backtest[/bold cyan]\n"
                       f"Period: {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}\n"
                       f"Initial Equity: ${initial_equity:,.2f}\n"
                       f"Price Type: {price_label}",
                       title="📊 Backtest Configuration"))

    dp = UnifiedDataProvider(paper_trading=True, cache_duration=0)
    manager = MultiStrategyManager(shared_data_provider=dp)
    all_syms = list(set(manager.nuclear_engine.all_symbols + manager.tecl_engine.all_symbols))

    symbol_data = _preload_symbol_data(dp, all_syms, start - dt.timedelta(days=400), end)

    equity = initial_equity
    equity_curve = []
    prev_weights = {sym: 0 for sym in all_syms}

    # Use actual trading dates from market data instead of artificial business days
    # Get all unique trading dates from our reference symbols within the backtest period
    all_trading_dates = set()
    for sym in ['SPY', 'QQQ']:
        if sym in symbol_data:
            df = symbol_data[sym]
            mask = (df.index.date >= start.date()) & (df.index.date <= end.date())
            trading_dates = df.index[mask]
            all_trading_dates.update(trading_dates)

    date_range = sorted(all_trading_dates)

    console.print(f"\n[yellow]Running backtest for {len(date_range)} actual trading days...")
    console.print(f"[yellow]Trading dates: {[d.strftime('%Y-%m-%d') for d in date_range[:3]]} ... {[d.strftime('%Y-%m-%d') for d in date_range[-3:]]}")

    for current_day in track(date_range, description="Processing days"):
        dp.cache.clear()  # Force fresh fetches every time
        original_fetch_method = dp._fetch_historical_data
        def mock_fetch_historical_data(symbol, period="1y", interval="1d"):
            if symbol in symbol_data:
                df = symbol_data[symbol]
                slice_df = df[df.index < current_day]
                return slice_df
            else:
                return pd.DataFrame()
        dp._fetch_historical_data = mock_fetch_historical_data
        try:
            signals, portfolio = manager.run_all_strategies()
        finally:
            dp._fetch_historical_data = original_fetch_method
        current_weights = {sym: portfolio.get(sym, 0) for sym in all_syms}
        daily_ret = 0.0
        for sym, weight in current_weights.items():
            if weight == 0:
                continue
            df = symbol_data[sym]
            if current_day not in df.index:
                continue
            prev_dates = df.index[df.index < current_day]
            if len(prev_dates) == 0:
                continue
            prev_row = df.loc[prev_dates[-1]]
            curr_row = df.loc[current_day]
            prev_price = price_selector(prev_row)
            curr_price = price_selector(curr_row)
            if prev_price == 0:
                continue
            ret = (curr_price - prev_price) / prev_price
            daily_ret += weight * ret
        equity *= (1 + daily_ret)
        equity_curve.append(equity)
        prev_weights = current_weights

    # Calculate performance metrics
    final_equity = equity_curve[-1]
    total_return = (final_equity / initial_equity - 1) * 100

    # Display results
    table = Table(title=f"📈 Backtest Results [{price_label}]")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Initial Equity", f"${initial_equity:,.2f}")
    table.add_row("Final Equity", f"${final_equity:,.2f}")
    table.add_row("Total Return", f"{total_return:+.2f}%")
    table.add_row("Trading Days", str(len(date_range)))

    if len(equity_curve) > 1:
        daily_returns = [equity_curve[i]/equity_curve[i-1] - 1 for i in range(1, len(equity_curve))]
        volatility = pd.Series(daily_returns).std() * (252**0.5) * 100  # Annualized volatility
        table.add_row("Annualized Volatility", f"{volatility:.2f}%")
        if volatility > 0:
            sharpe_ratio = (total_return / 100) / (volatility / 100) * (252**0.5)
            table.add_row("Sharpe Ratio", f"{sharpe_ratio:.2f}")

    console.print(table)

    # Show equity curve summary
    if len(equity_curve) >= 5:
        console.print(f"\n[yellow]Equity curve (first/last 5 values):")
        console.print(f"Start: {equity_curve[:5]}")
        console.print(f"End:   {equity_curve[-5:]}")

    return equity_curve


def run_backtest_comparison(start, end, initial_equity=1000):
    """Run backtest for all three price types and compare results."""
    console.print(Panel(f"[bold cyan]Starting Backtest Comparison[/bold cyan]\n"
                       f"Period: {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}\n"
                       f"Initial Equity: ${initial_equity:,.2f}\n"
                       f"Testing: Close, Open, Mid (HLC/3) prices",
                       title="📊 Backtest Comparison"))
    
    results = {}
    
    # Run backtest for each price type
    for price_type in ["close", "open", "mid"]:
        console.print(f"\n[bold yellow]Running {price_type.upper()} price backtest...[/bold yellow]")
        equity_curve = run_backtest(start, end, initial_equity, price_type)
        
        # Calculate metrics
        final_equity = equity_curve[-1]
        total_return = (final_equity / initial_equity - 1) * 100
        
        daily_returns = [equity_curve[i]/equity_curve[i-1] - 1 for i in range(1, len(equity_curve))]
        volatility = pd.Series(daily_returns).std() * (252**0.5) * 100
        sharpe_ratio = (total_return / 100) / (volatility / 100) * (252**0.5) if volatility > 0 else 0
        
        results[price_type] = {
            'final_equity': final_equity,
            'total_return': total_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'equity_curve': equity_curve
        }
    
    # Create comparison table
    console.print(f"\n[bold cyan]📊 Backtest Comparison Summary[/bold cyan]")
    
    comparison_table = Table(title="Price Type Comparison")
    comparison_table.add_column("Metric", style="bold cyan")
    comparison_table.add_column("Close", style="green")
    comparison_table.add_column("Open", style="yellow")
    comparison_table.add_column("Mid (HLC/3)", style="blue")
    
    comparison_table.add_row(
        "Final Equity",
        f"${results['close']['final_equity']:,.2f}",
        f"${results['open']['final_equity']:,.2f}",
        f"${results['mid']['final_equity']:,.2f}"
    )
    
    comparison_table.add_row(
        "Total Return",
        f"{results['close']['total_return']:+.2f}%",
        f"{results['open']['total_return']:+.2f}%",
        f"{results['mid']['total_return']:+.2f}%"
    )
    
    comparison_table.add_row(
        "Volatility",
        f"{results['close']['volatility']:.2f}%",
        f"{results['open']['volatility']:.2f}%",
        f"{results['mid']['volatility']:.2f}%"
    )
    
    comparison_table.add_row(
        "Sharpe Ratio",
        f"{results['close']['sharpe_ratio']:.2f}",
        f"{results['open']['sharpe_ratio']:.2f}",
        f"{results['mid']['sharpe_ratio']:.2f}"
    )
    
    console.print(comparison_table)
    
    # Find best performing price type
    best_return = max(results.keys(), key=lambda x: results[x]['total_return'])
    best_sharpe = max(results.keys(), key=lambda x: results[x]['sharpe_ratio'])
    
    console.print(f"\n[bold green]🏆 Best Performance:[/bold green]")
    console.print(f"• Highest Return: [bold]{best_return.upper()}[/bold] ({results[best_return]['total_return']:+.2f}%)")
    console.print(f"• Best Sharpe Ratio: [bold]{best_sharpe.upper()}[/bold] ({results[best_sharpe]['sharpe_ratio']:.2f})")
    
    return results


@pytest.mark.slow
def test_backtest_all_price_types():
    if not (os.getenv('ALPACA_PAPER_KEY') and os.getenv('ALPACA_PAPER_SECRET')):
        pytest.skip('Alpaca credentials not available')

    end = dt.datetime.now() - dt.timedelta(days=5)
    start = end - dt.timedelta(days=365*1)  # Run for the past year, not including last 5 days
    for price_type in ["close", "open", "mid"]:
        curve = run_backtest(start, end, price_type=price_type)
        assert len(curve) > 0


@pytest.mark.slow
def test_backtest_comparison():
    """Test that runs all price types and compares them."""
    if not (os.getenv('ALPACA_PAPER_KEY') and os.getenv('ALPACA_PAPER_SECRET')):
        pytest.skip('Alpaca credentials not available')

    end = dt.datetime.now() - dt.timedelta(days=5)
    start = end - dt.timedelta(days=365*1)  # Run for the past year, not including last 5 days
    results = run_backtest_comparison(start, end)
    
    # Assert all price types have positive equity curves
    for price_type, result in results.items():
        assert len(result['equity_curve']) > 0
        assert result['final_equity'] > 0
