
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


def run_backtest(start, end, initial_equity=100000):
    console.print(Panel(f"[bold cyan]Starting Backtest[/bold cyan]\n"
                       f"Period: {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}\n"
                       f"Initial Equity: ${initial_equity:,.2f}", 
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
    for sym in ['SPY', 'QQQ']:  # Use liquid reference symbols to get trading calendar
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
            prev_close = df.loc[prev_dates[-1], 'Close']
            close_today = df.loc[current_day, 'Close']
            ret = (close_today - prev_close) / prev_close
            daily_ret += weight * ret
        equity *= (1 + daily_ret)
        equity_curve.append(equity)
        prev_weights = current_weights

    # Calculate performance metrics
    final_equity = equity_curve[-1]
    total_return = (final_equity / initial_equity - 1) * 100
    
    # Display results
    table = Table(title="📈 Backtest Results")
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


@pytest.mark.slow
def test_backtest_smoke():
    if not (os.getenv('ALPACA_PAPER_KEY') and os.getenv('ALPACA_PAPER_SECRET')):
        pytest.skip('Alpaca credentials not available')

    end = dt.datetime.now() - dt.timedelta(days=5)
    start = end - dt.timedelta(days=365)  # Run for the past year, not including last 5 days
    curve = run_backtest(start, end)
    assert len(curve) > 0
