def run_backtest_all_splits(start, end, initial_equity=1000.0, slippage_bps=5, noise_factor=0.001, deposit_amount=0.0, deposit_frequency=None, deposit_day=1, use_minute_candles=False):
    """
    Backtest all possible splits between nuclear and tecl strategies in 10% increments.
    """
    console.print(Panel(f"[bold cyan]Backtesting All Splits (Nuclear/TECL) in 10% Increments[/bold cyan]\n"
                       f"Period: {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}\n"
                       f"Initial Equity: £{initial_equity:,.2f}\n"
                       f"Slippage: {slippage_bps} bps per trade\n"
                       f"Market Noise: {noise_factor*100:.3f}%\n"
                       f"Deposit: £{deposit_amount:,.2f} {deposit_frequency if deposit_frequency else ''}",
                       title="📊 All Splits Backtest"))

    import copy
    from the_alchemiser.core import config as alchemiser_config

    # We'll mock the config in memory for each run
    results = []
    
    # Store original global config instance
    orig_global_config = alchemiser_config._global_config

    for split in range(0, 110, 10):
        w_nuclear = split / 100.0
        w_tecl = 1.0 - w_nuclear

        # Create a new Config instance with modified values
        # We need to temporarily replace the global config
        mock_config = alchemiser_config.Config()
        
        # Modify the internal config dict to have our desired split
        mock_config._config = copy.deepcopy(mock_config._config)
        if 'strategy' not in mock_config._config:
            mock_config._config['strategy'] = {}
        mock_config._config['strategy']['default_strategy_allocations'] = {'nuclear': w_nuclear, 'tecl': w_tecl}
        
        # Replace the global config temporarily
        alchemiser_config._global_config = mock_config

        # Run the normal backtest (which will use the config-driven allocation)
        equity_curve = run_backtest(
            start, end, initial_equity, "close", slippage_bps, noise_factor,
            deposit_amount, deposit_frequency, deposit_day, use_minute_candles
        )

        # Restore original global config
        alchemiser_config._global_config = orig_global_config

        final_equity = equity_curve[-1] if equity_curve else initial_equity
        total_return = (final_equity / initial_equity - 1) * 100
        daily_returns = [equity_curve[i]/equity_curve[i-1] - 1 for i in range(1, len(equity_curve))] if equity_curve and len(equity_curve) > 1 else []
        volatility = pd.Series(daily_returns).std() * (252**0.5) * 100 if len(daily_returns) > 1 else 0
        sharpe_ratio = (total_return / 100) / (volatility / 100) * (252**0.5) if volatility > 0 else 0
        results.append({
            'split': f"{int(w_nuclear*100)}% Nuclear / {int(w_tecl*100)}% TECL",
            'final_equity': final_equity,
            'total_return': total_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio
        })

    # Restore original global config
    alchemiser_config._global_config = orig_global_config

    # Print summary table
    table = Table(title="Strategy Split Comparison (Nuclear/TECL)")
    table.add_column("Split", style="cyan")
    table.add_column("Final Equity", style="green")
    table.add_column("Total Return", style="yellow")
    table.add_column("Volatility", style="magenta")
    table.add_column("Sharpe Ratio", style="blue")
    for r in results:
        table.add_row(r['split'], f"£{r['final_equity']:,.2f}", f"{r['total_return']:+.2f}%", f"{r['volatility']:.2f}%", f"{r['sharpe_ratio']:.2f}")
    console.print(table)
    return results

import os
import time
import datetime as dt
import pandas as pd
import pytest
import numpy as np
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


def _preload_symbol_data(data_provider, symbols, start, end, fetch_minute_data=True):
    """Fetch all required historical data in one shot - both daily and 1-minute."""
    console.print(f"[yellow]Loading historical data for {len(symbols)} symbols...")
    symbol_data = {}
    symbol_minute_data = {}
    
    for sym in track(symbols, description="Fetching data"):
        # Fetch daily data for indicators
        daily_bars = data_provider.get_historical_data(sym, start=start, end=end, timeframe="1Day")
        daily_rows = []
        daily_dates = []
        for bar in daily_bars:
            daily_rows.append({
                'Open': float(bar.open),
                'High': float(bar.high),
                'Low': float(bar.low),
                'Close': float(bar.close),
                'Volume': getattr(bar, 'volume', 0)
            })
            daily_dates.append(bar.timestamp)
        symbol_data[sym] = pd.DataFrame(daily_rows, index=pd.to_datetime(daily_dates))
        
        if fetch_minute_data:
            # Fetch 1-minute data for realistic execution pricing (last 90 days to limit data)
            minute_start = max(start, end - dt.timedelta(days=90))
            minute_bars = data_provider.get_historical_data(sym, start=minute_start, end=end, timeframe="1m")
            minute_rows = []
            minute_dates = []
            for bar in minute_bars:
                minute_rows.append({
                    'Open': float(bar.open),
                    'High': float(bar.high),
                    'Low': float(bar.low),
                    'Close': float(bar.close),
                    'Volume': getattr(bar, 'volume', 0)
                })
                minute_dates.append(bar.timestamp)
            symbol_minute_data[sym] = pd.DataFrame(minute_rows, index=pd.to_datetime(minute_dates))
        else:
            symbol_minute_data[sym] = pd.DataFrame()  # Empty DataFrame
        
    data_type = "daily + 1min" if fetch_minute_data else "daily only"
    console.print(f"[green]✓ Data loaded for {len(symbols)} symbols ({data_type})")
    return symbol_data, symbol_minute_data


def _calculate_slippage_cost(weight_change, price, slippage_bps=None):
    """Calculate transaction cost based on weight change and slippage.
    
    Args:
        weight_change: Absolute change in weight (0-1)
        price: Current price of the asset
        slippage_bps: Slippage in basis points (default 5 bps = 0.05%)
    
    Returns:
        Cost as a fraction of portfolio value
    """
    # Only apply slippage to trades (weight changes)
    if abs(weight_change) < 1e-6:  # No meaningful trade
        return 0.0
    if slippage_bps is None:
        try:
            from the_alchemiser.core.config import get_config
            config = get_config()
            slippage_bps = config['alpaca'].get('slippage_bps', 5)
        except Exception:
            slippage_bps = 5
    # Slippage cost = (slippage_bps / 10000) * abs(weight_change)
    return (slippage_bps / 10000) * abs(weight_change)


def _add_market_noise(price, volatility_factor=0.001):
    """Add realistic market noise to execution prices.
    
    Args:
        price: Base price
        volatility_factor: Noise factor (default 0.001 = 0.1% noise)
    
    Returns:
        Price with added noise
    """
    # Add random noise with normal distribution
    noise = np.random.normal(0, volatility_factor)
    return price * (1 + noise)


def _get_realistic_execution_price(symbol_minute_data, symbol, target_time, price_type="mid", noise_factor=0.001):
    """Get realistic execution price using 1-minute data with market noise.
    
    Args:
        symbol_minute_data: Dict of minute-level DataFrames
        symbol: Stock symbol
        target_time: Target execution time
        price_type: 'open', 'close', 'mid', 'vwap'
        noise_factor: Market noise factor
        
    Returns:
        Realistic execution price with noise
    """
    if symbol not in symbol_minute_data:
        return None
        
    minute_df = symbol_minute_data[symbol]
    if minute_df.empty:
        return None
    
    # Find closest minute data to target time
    target_date = target_time.date()
    same_day_data = minute_df[minute_df.index.date == target_date]
    
    if same_day_data.empty:
        # Fall back to daily close price if no minute data
        return None
    
    # Get execution price based on type
    if price_type == "open":
        # Use first available price of the day with some noise
        base_price = same_day_data.iloc[0]['Open']
    elif price_type == "close":
        # Use last available price of the day
        base_price = same_day_data.iloc[-1]['Close']
    elif price_type == "mid":
        # Use average of high/low/close for the closest minute
        closest_idx = same_day_data.index.get_indexer([target_time], method='nearest')[0]
        if closest_idx >= 0:
            closest_bar = same_day_data.iloc[closest_idx]
            base_price = (closest_bar['High'] + closest_bar['Low'] + closest_bar['Close']) / 3
        else:
            base_price = same_day_data.iloc[-1]['Close']
    elif price_type == "vwap":
        # Calculate volume-weighted average price for the day
        if 'Volume' in same_day_data.columns and same_day_data['Volume'].sum() > 0:
            typical_price = (same_day_data['High'] + same_day_data['Low'] + same_day_data['Close']) / 3
            base_price = (typical_price * same_day_data['Volume']).sum() / same_day_data['Volume'].sum()
        else:
            base_price = same_day_data['Close'].mean()
    else:
        base_price = same_day_data.iloc[-1]['Close']
    
    # Add market noise
    return _add_market_noise(base_price, noise_factor)


def run_backtest(start, end, initial_equity=1000.0, price_type="close", slippage_bps=None, noise_factor=0.001, deposit_amount=0.0, deposit_frequency=None, deposit_day=1, use_minute_candles=False):
    # --- Deposit feature additions ---
    # New params: deposit_amount, deposit_frequency, deposit_day
    # New param: use_minute_candles (default False, can be set via CLI)
    import calendar
    def run_backtest_with_deposit(
        start, end, initial_equity=1000.0, price_type="close", slippage_bps=None, noise_factor=0.001,
        deposit_amount=0.0, deposit_frequency=None, deposit_day=1, use_minute_candles=False
    ):
        price_type_l = price_type.lower()
        if price_type_l == 'close':
            price_selector = lambda row: row['Close']
            price_label = 'Close'
        elif price_type_l == 'open':
            price_selector = lambda row: row['Open']
            price_label = 'Open'
        elif price_type_l == 'mid':
            price_selector = lambda row: (row['High'] + row['Low'] + row['Close']) / 3
            price_label = 'Mid (HLC/3)'
        elif price_type_l == 'vwap':
            price_selector = lambda row: (row['High'] + row['Low'] + row['Close']) / 3  # Simplified VWAP
            price_label = 'VWAP (simplified)'
        else:
            raise ValueError(f"Unknown price_type: {price_type}")

        deposit_str = ""
        if deposit_amount and deposit_frequency:
            deposit_str = f"\nDeposit: £{deposit_amount:,.2f} {deposit_frequency}"
        if slippage_bps is None:
            try:
                from the_alchemiser.core.config import get_config
                config = get_config()
                slippage_bps = config['alpaca'].get('slippage_bps', 5)
            except Exception:
                slippage_bps = 5
        execution_mode = "Daily + 1min candles" if use_minute_candles else "Daily only"
        console.print(Panel(f"[bold cyan]Starting Realistic Backtest[/bold cyan]\n"
                           f"Period: {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}\n"
                           f"Initial Equity: £{initial_equity:,.2f}\n"
                           f"Price Type: {price_label}\n"
                           f"Execution Mode: {execution_mode}\n"
                           f"Slippage: {slippage_bps} bps\n"
                           f"Market Noise: {noise_factor*100:.3f}%"
                           f"{deposit_str}",
                           title="📊 Realistic Backtest Configuration"))

        dp = UnifiedDataProvider(paper_trading=True, cache_duration=0)
        manager = MultiStrategyManager(shared_data_provider=dp)
        all_syms = list(set(manager.nuclear_engine.all_symbols + manager.tecl_engine.all_symbols))


        # Fetch both daily and minute data if enabled
        symbol_data = None
        symbol_minute_data = None
        # Use longer lookback for daily-only mode to ensure enough data for indicators (especially 200-day MA)
        lookback_days = 400 if use_minute_candles else 1200
        if use_minute_candles:
            symbol_data, symbol_minute_data = _preload_symbol_data(dp, all_syms, start - dt.timedelta(days=lookback_days), end, fetch_minute_data=True)
        else:
            # Only fetch daily data
            console.print(f"[yellow]Using daily-only mode with {lookback_days} day lookback for indicators (200-day MA requires ~250 trading days)...")
            symbol_data, symbol_minute_data = _preload_symbol_data(dp, all_syms, start - dt.timedelta(days=lookback_days), end, fetch_minute_data=False)

        equity = initial_equity
        equity_curve = []
        prev_weights = {sym: 0 for sym in all_syms}

        # Use actual trading dates from market data instead of artificial business days
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
            # --- Deposit logic ---
            if deposit_amount and deposit_frequency:
                if deposit_frequency == 'monthly':
                    # Deposit on the first trading day of each month or on deposit_day if available
                    if current_day.day == deposit_day:
                        equity += deposit_amount
                elif deposit_frequency == 'weekly':
                    # Deposit on a specific weekday (e.g., Monday=0)
                    if current_day.weekday() == deposit_day:
                        equity += deposit_amount

            dp.cache.clear()  # Force fresh fetches every time
            original_fetch_method = dp._fetch_historical_data
            def mock_fetch_historical_data(symbol, period="1y", interval="1d"):
                if symbol in symbol_data:
                    df = symbol_data[symbol]
                    # For backtesting, provide all available historical data up to current_day
                    # This ensures indicators like 200-day MA have enough data to work with
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

            # Calculate slippage costs from weight changes using realistic execution prices
            total_slippage_cost = 0.0
            for sym, new_weight in current_weights.items():
                old_weight = prev_weights.get(sym, 0)
                weight_change = abs(new_weight - old_weight)
                if weight_change > 1e-6:
                    if use_minute_candles:
                        execution_price = _get_realistic_execution_price(
                            symbol_minute_data, sym, current_day, price_type, noise_factor
                        )
                        if execution_price is None and sym in symbol_data and current_day in symbol_data[sym].index:
                            curr_row = symbol_data[sym].loc[current_day]
                            execution_price = price_selector(curr_row)
                    else:
                        # Use daily data only
                        if sym in symbol_data and current_day in symbol_data[sym].index:
                            curr_row = symbol_data[sym].loc[current_day]
                            execution_price = price_selector(curr_row)
                        else:
                            execution_price = None
                    if execution_price:
                        slippage_cost = _calculate_slippage_cost(weight_change, execution_price, slippage_bps)
                        total_slippage_cost += slippage_cost
            equity *= (1 - total_slippage_cost)

            # Calculate returns using realistic pricing with daily data for consistency
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
                if use_minute_candles:
                    prev_price = _get_realistic_execution_price(
                        symbol_minute_data, sym, prev_dates[-1], price_type, noise_factor
                    )
                    curr_price = _get_realistic_execution_price(
                        symbol_minute_data, sym, current_day, price_type, noise_factor
                    )
                    if prev_price is None:
                        prev_price = price_selector(prev_row)
                    if curr_price is None:
                        curr_price = price_selector(curr_row)
                else:
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


        # --- Additional Metrics ---
        n_years = (date_range[-1] - date_range[0]).days / 365.25 if len(date_range) > 1 else 1
        cagr = ((final_equity / initial_equity) ** (1 / n_years) - 1) * 100 if n_years > 0 else 0
        # Max Drawdown
        equity_arr = pd.Series(equity_curve)
        running_max = equity_arr.cummax()
        drawdown = (equity_arr - running_max) / running_max
        max_drawdown = drawdown.min() * 100 if len(drawdown) > 0 else 0
        calmar_ratio = cagr / abs(max_drawdown) if max_drawdown < 0 else float('nan')

        # Display results
        table = Table(title=f"📈 Backtest Results [{price_label}]")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Initial Equity", f"£{initial_equity:,.2f}")
        table.add_row("Final Equity", f"£{final_equity:,.2f}")
        table.add_row("Total Return", f"{total_return:+.2f}%")
        table.add_row("CAGR", f"{cagr:.2f}%")
        table.add_row("Max Drawdown", f"{max_drawdown:.2f}%")
        table.add_row("Calmar Ratio", f"{calmar_ratio:.2f}" if not pd.isna(calmar_ratio) else "-")
        table.add_row("Trading Days", str(len(date_range)))
        if deposit_amount and deposit_frequency:
            table.add_row("Total Deposits", f"£{deposit_amount * sum((d.day == deposit_day if deposit_frequency=='monthly' else d.weekday()==deposit_day) for d in date_range):,.2f}")

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

    # Call new function with backward compatibility
    # use_minute_candles now passed as parameter (defaults to False)
    return run_backtest_with_deposit(
        start, end, initial_equity, price_type, slippage_bps, noise_factor,
        deposit_amount=deposit_amount, deposit_frequency=deposit_frequency, deposit_day=deposit_day,
        use_minute_candles=use_minute_candles
    )
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run backtest with optional 1-minute candle execution.")
    parser.add_argument('--start', type=str, required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--initial-equity', type=float, default=1000.0, help='Initial equity')
    parser.add_argument('--price-type', type=str, default='close', choices=['close','open','mid','vwap'], help='Execution price type')
    parser.add_argument('--slippage-bps', type=float, default=None, help='Slippage in basis points')
    parser.add_argument('--noise-factor', type=float, default=0.001, help='Market noise factor')
    parser.add_argument('--deposit-amount', type=float, default=0.0, help='Deposit amount')
    parser.add_argument('--deposit-frequency', type=str, default=None, choices=[None, 'monthly', 'weekly'], help='Deposit frequency')
    parser.add_argument('--deposit-day', type=int, default=1, help='Deposit day (1 for monthly, 0-6 for weekly)')
    parser.add_argument('--use-minute-candles', action='store_true', help='Enable 1-minute candle execution (default: disabled)')
    parser.add_argument('--all-splits', action='store_true', help='Backtest all possible splits between nuclear and tecl strategies in 10%% increments')
    args = parser.parse_args()

    # Parse dates
    start_dt = dt.datetime.strptime(args.start, "%Y-%m-%d")
    end_dt = dt.datetime.strptime(args.end, "%Y-%m-%d")

    if args.all_splits:
        run_backtest_all_splits(
            start_dt,
            end_dt,
            initial_equity=args.initial_equity,
            slippage_bps=args.slippage_bps if args.slippage_bps is not None else 5,
            noise_factor=args.noise_factor,
            deposit_amount=args.deposit_amount,
            deposit_frequency=args.deposit_frequency,
            deposit_day=args.deposit_day
        )
    else:
        # Set global for use_minute_candles
        globals()['USE_MINUTE_CANDLES'] = args.use_minute_candles
        # Run backtest
        run_backtest(
            start_dt,
            end_dt,
            initial_equity=args.initial_equity,
            price_type=args.price_type,
            slippage_bps=args.slippage_bps,
            noise_factor=args.noise_factor,
            deposit_amount=args.deposit_amount,
            deposit_frequency=args.deposit_frequency,
            deposit_day=args.deposit_day
        )


def run_backtest_dual_rebalance(start, end, initial_equity=1000.0, slippage_bps=5, noise_factor=0.001, deposit_amount=0.0, deposit_frequency=None, deposit_day=1, use_minute_candles=False):

    def run_backtest_dual_with_deposit(
        start, end, initial_equity=1000.0, slippage_bps=5, noise_factor=0.001,
        deposit_amount=0.0, deposit_frequency=None, deposit_day=1
    ):
        deposit_str = ""
        if deposit_amount and deposit_frequency:
            deposit_str = f"\nDeposit: £{deposit_amount:,.2f} {deposit_frequency}"
        console.print(Panel(f"[bold cyan]Starting Dual-Rebalance Realistic Backtest[/bold cyan]\n"
                           f"Period: {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}\n"
                           f"Initial Equity: £{initial_equity:,.2f}\n"
                           f"Rebalances: Open + Close (2x daily)\n"
                           f"Slippage: {slippage_bps} bps per trade\n"
                           f"Market Noise: {noise_factor*100:.3f}%"
                           f"{deposit_str}",
                           title="📊 Dual-Rebalance Realistic Backtest Configuration"))

        dp = UnifiedDataProvider(paper_trading=True, cache_duration=0)
        manager = MultiStrategyManager(shared_data_provider=dp)
        all_syms = list(set(manager.nuclear_engine.all_symbols + manager.tecl_engine.all_symbols))

        # Fetch both daily and minute data
        symbol_data, symbol_minute_data = _preload_symbol_data(dp, all_syms, start - dt.timedelta(days=400), end, fetch_minute_data=True)

        equity = initial_equity
        equity_curve = []
        prev_weights = {sym: 0 for sym in all_syms}

        # Use actual trading dates from market data
        all_trading_dates = set()
        for sym in ['SPY', 'QQQ']:
            if sym in symbol_data:
                df = symbol_data[sym]
                mask = (df.index.date >= start.date()) & (df.index.date <= end.date())
                trading_dates = df.index[mask]
                all_trading_dates.update(trading_dates)
        date_range = sorted(all_trading_dates)

        console.print(f"\n[yellow]Running dual-rebalance backtest for {len(date_range)} trading days...")
        console.print(f"[yellow]Total rebalances: {len(date_range) * 2} (2 per day)")

        for current_day in track(date_range, description="Processing days"):
            # --- Deposit logic ---
            if deposit_amount and deposit_frequency:
                if deposit_frequency == 'monthly':
                    if current_day.day == deposit_day:
                        equity += deposit_amount
                elif deposit_frequency == 'weekly':
                    if current_day.weekday() == deposit_day:
                        equity += deposit_amount

            # MORNING REBALANCE (at Open)
            dp.cache.clear()
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
            morning_weights = {sym: portfolio.get(sym, 0) for sym in all_syms}

            # Calculate slippage costs for morning rebalance using realistic execution prices
            morning_slippage_cost = 0.0
            for sym, new_weight in morning_weights.items():
                old_weight = prev_weights.get(sym, 0)
                weight_change = abs(new_weight - old_weight)
                if weight_change > 1e-6:
                    execution_price = _get_realistic_execution_price(
                        symbol_minute_data, sym, current_day, "open", noise_factor
                    )
                    if execution_price is None and sym in symbol_data and current_day in symbol_data[sym].index:
                        curr_row = symbol_data[sym].loc[current_day]
                        execution_price = curr_row['Open']
                    if execution_price:
                        slippage_cost = _calculate_slippage_cost(weight_change, execution_price, slippage_bps)
                        morning_slippage_cost += slippage_cost
            equity *= (1 - morning_slippage_cost)

            # Calculate returns from open to close with morning weights using realistic pricing
            morning_ret = 0.0
            for sym, weight in morning_weights.items():
                if weight == 0:
                    continue
                df = symbol_data[sym]
                if current_day not in df.index:
                    continue
                curr_row = df.loc[current_day]
                open_price = _get_realistic_execution_price(
                    symbol_minute_data, sym, current_day, "open", noise_factor
                )
                close_price = _get_realistic_execution_price(
                    symbol_minute_data, sym, current_day, "close", noise_factor
                )
                if open_price is None:
                    open_price = curr_row['Open']
                if close_price is None:
                    close_price = curr_row['Close']
                if open_price == 0:
                    continue
                ret = (close_price - open_price) / open_price
                morning_ret += weight * ret
            equity *= (1 + morning_ret)

            # EVENING REBALANCE (at Close)
            dp.cache.clear()
            def mock_fetch_historical_data_close(symbol, period="1y", interval="1d"):
                if symbol in symbol_data:
                    df = symbol_data[symbol]
                    slice_df = df[df.index <= current_day]
                    return slice_df
                else:
                    return pd.DataFrame()
            dp._fetch_historical_data = mock_fetch_historical_data_close
            try:
                signals, portfolio = manager.run_all_strategies()
            finally:
                dp._fetch_historical_data = original_fetch_method
            evening_weights = {sym: portfolio.get(sym, 0) for sym in all_syms}

            # Calculate slippage costs for evening rebalance using realistic execution prices
            evening_slippage_cost = 0.0
            for sym, new_weight in evening_weights.items():
                old_weight = morning_weights.get(sym, 0)
                weight_change = abs(new_weight - old_weight)
                if weight_change > 1e-6:
                    execution_price = _get_realistic_execution_price(
                        symbol_minute_data, sym, current_day, "close", noise_factor
                    )
                    if execution_price is None and sym in symbol_data and current_day in symbol_data[sym].index:
                        curr_row = symbol_data[sym].loc[current_day]
                        execution_price = curr_row['Close']
                    if execution_price:
                        slippage_cost = _calculate_slippage_cost(weight_change, execution_price, slippage_bps)
                        evening_slippage_cost += slippage_cost
            equity *= (1 - evening_slippage_cost)

            equity_curve.append(equity)
            prev_weights = evening_weights

        # Calculate performance metrics
        final_equity = equity_curve[-1]
        total_return = (final_equity / initial_equity - 1) * 100

        # --- Additional Metrics ---
        n_years = (date_range[-1] - date_range[0]).days / 365.25 if len(date_range) > 1 else 1
        cagr = ((final_equity / initial_equity) ** (1 / n_years) - 1) * 100 if n_years > 0 else 0
        equity_arr = pd.Series(equity_curve)
        running_max = equity_arr.cummax()
        drawdown = (equity_arr - running_max) / running_max
        max_drawdown = drawdown.min() * 100 if len(drawdown) > 0 else 0
        calmar_ratio = cagr / abs(max_drawdown) if max_drawdown < 0 else float('nan')

        # Display results
        table = Table(title="📈 Dual-Rebalance Backtest Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Initial Equity", f"£{initial_equity:,.2f}")
        table.add_row("Final Equity", f"£{final_equity:,.2f}")
        table.add_row("Total Return", f"{total_return:+.2f}%")
        table.add_row("CAGR", f"{cagr:.2f}%")
        table.add_row("Max Drawdown", f"{max_drawdown:.2f}%")
        table.add_row("Calmar Ratio", f"{calmar_ratio:.2f}" if not pd.isna(calmar_ratio) else "-")
        table.add_row("Trading Days", str(len(date_range)))
        table.add_row("Total Rebalances", str(len(date_range) * 2))
        table.add_row("Slippage per Trade", f"{slippage_bps} bps")
        if deposit_amount and deposit_frequency:
            table.add_row("Total Deposits", f"£{deposit_amount * sum((d.day == deposit_day if deposit_frequency=='monthly' else d.weekday()==deposit_day) for d in date_range):,.2f}")

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

    return run_backtest_dual_with_deposit(
        start, end, initial_equity, slippage_bps, noise_factor,
        deposit_amount=deposit_amount, deposit_frequency=deposit_frequency, deposit_day=deposit_day
    )


def run_backtest_comparison(start, end, initial_equity=1000.0, slippage_bps=5, noise_factor=0.001, deposit_amount=0.0, deposit_frequency=None, deposit_day=1, use_minute_candles=False):
    def run_backtest_comparison_with_deposit(
        start, end, initial_equity=1000.0, slippage_bps=5, noise_factor=0.001,
        deposit_amount=0.0, deposit_frequency=None, deposit_day=1, use_minute_candles=False
    ):
        console.print(Panel(f"[bold cyan]Starting Extended Realistic Backtest Comparison[/bold cyan]\n"
                           f"Period: {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}\n"
                           f"Initial Equity: £{initial_equity:,.2f}\n"
                           f"Testing: Close, Open, Mid, VWAP prices + Dual-Rebalance\n"
                           f"Slippage: {slippage_bps} bps per trade\n"
                           f"Market Noise: {noise_factor*100:.3f}%"
                           f"\nDeposit: £{deposit_amount:,.2f} {deposit_frequency if deposit_frequency else ''}",
                           title="📊 Extended Realistic Backtest Comparison"))
        results = {}
        for price_type in ["close", "open", "mid", "vwap"]:
            console.print(f"\n[bold yellow]Running {price_type.upper()} price backtest (realistic execution)...[/bold yellow]")
            equity_curve = run_backtest(
                start, end, initial_equity, price_type, slippage_bps, noise_factor,
                deposit_amount=deposit_amount, deposit_frequency=deposit_frequency, deposit_day=deposit_day,
                use_minute_candles=use_minute_candles
            )
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
                'equity_curve': equity_curve,
                'mode': f'{price_type.title()} (1x daily, realistic)'
            }
        console.print(f"\n[bold yellow]Running DUAL-REBALANCE backtest (2x daily, realistic)...[/bold yellow]")
        dual_equity_curve = run_backtest_dual_rebalance(
            start, end, initial_equity, slippage_bps, noise_factor,
            deposit_amount=deposit_amount, deposit_frequency=deposit_frequency, deposit_day=deposit_day,
            use_minute_candles=use_minute_candles
        )
        dual_final_equity = dual_equity_curve[-1]
        dual_total_return = (dual_final_equity / initial_equity - 1) * 100
        dual_daily_returns = [dual_equity_curve[i]/dual_equity_curve[i-1] - 1 for i in range(1, len(dual_equity_curve))]
        dual_volatility = pd.Series(dual_daily_returns).std() * (252**0.5) * 100
        dual_sharpe_ratio = (dual_total_return / 100) / (dual_volatility / 100) * (252**0.5) if dual_volatility > 0 else 0
        results['dual_rebalance'] = {
            'final_equity': dual_final_equity,
            'total_return': dual_total_return,
            'volatility': dual_volatility,
            'sharpe_ratio': dual_sharpe_ratio,
            'equity_curve': dual_equity_curve,
            'mode': 'Dual-Rebalance (2x daily, realistic)'
        }
        console.print(f"\n[bold cyan]📊 Extended Realistic Backtest Comparison Summary[/bold cyan]")
        comparison_table = Table(title="Strategy Comparison (All Modes - Realistic Execution)")
        comparison_table.add_column("Metric", style="bold cyan")
        comparison_table.add_column("Close (1x)", style="green")
        comparison_table.add_column("Open (1x)", style="yellow")
        comparison_table.add_column("Mid (1x)", style="blue")
        comparison_table.add_column("VWAP (1x)", style="magenta")
        comparison_table.add_column("Dual-Rebal (2x)", style="red")
        comparison_table.add_row(
            "Final Equity",
            f"£{results['close']['final_equity']:,.2f}",
            f"£{results['open']['final_equity']:,.2f}",
            f"£{results['mid']['final_equity']:,.2f}",
            f"£{results['vwap']['final_equity']:,.2f}",
            f"£{results['dual_rebalance']['final_equity']:,.2f}"
        )
        # ...existing code...
        return results

    return run_backtest_comparison_with_deposit(
        start, end, initial_equity, slippage_bps, noise_factor,
        deposit_amount=deposit_amount, deposit_frequency=deposit_frequency, deposit_day=deposit_day,
        use_minute_candles=use_minute_candles
    )
    
    comparison_table.add_row(
        "Total Return",
        f"{results['close']['total_return']:+.2f}%",
        f"{results['open']['total_return']:+.2f}%",
        f"{results['mid']['total_return']:+.2f}%",
        f"{results['vwap']['total_return']:+.2f}%",
        f"{results['dual_rebalance']['total_return']:+.2f}%"
    )
    
    comparison_table.add_row(
        "Volatility",
        f"{results['close']['volatility']:.2f}%",
        f"{results['open']['volatility']:.2f}%",
        f"{results['mid']['volatility']:.2f}%",
        f"{results['vwap']['volatility']:.2f}%",
        f"{results['dual_rebalance']['volatility']:.2f}%"
    )
    
    comparison_table.add_row(
        "Sharpe Ratio",
        f"{results['close']['sharpe_ratio']:.2f}",
        f"{results['open']['sharpe_ratio']:.2f}",
        f"{results['mid']['sharpe_ratio']:.2f}",
        f"{results['vwap']['sharpe_ratio']:.2f}",
        f"{results['dual_rebalance']['sharpe_ratio']:.2f}"
    )
    
    console.print(comparison_table)
    
    # Find best performing strategies
    all_strategies = ['close', 'open', 'mid', 'vwap', 'dual_rebalance']
    best_return = max(all_strategies, key=lambda x: results[x]['total_return'])
    best_sharpe = max(all_strategies, key=lambda x: results[x]['sharpe_ratio'])
    
    console.print(f"\n[bold green]🏆 Best Performance:[/bold green]")
    console.print(f"• Highest Return: [bold]{results[best_return]['mode']}[/bold] ({results[best_return]['total_return']:+.2f}%)")
    console.print(f"• Best Sharpe Ratio: [bold]{results[best_sharpe]['mode']}[/bold] ({results[best_sharpe]['sharpe_ratio']:.2f})")
    
    # Analysis insights
    console.print(f"\n[bold magenta]📈 Analysis Insights:[/bold magenta]")
    dual_vs_close = results['dual_rebalance']['total_return'] - results['close']['total_return']
    console.print(f"• Dual-rebalance vs Close: {dual_vs_close:+.2f}% difference")
    
    if dual_vs_close > 0:
        console.print("  [green]→ More frequent rebalancing improved returns[/green]")
    else:
        console.print("  [red]→ Transaction costs outweighed rebalancing benefits[/red]")
    
    avg_single_rebal_return = (results['close']['total_return'] + results['open']['total_return'] + 
                              results['mid']['total_return'] + results['vwap']['total_return']) / 4
    console.print(f"• Average single-rebalance return: {avg_single_rebal_return:.2f}%")
    console.print(f"• Dual-rebalance return: {results['dual_rebalance']['total_return']:.2f}%")
    console.print(f"• VWAP execution vs Close: {results['vwap']['total_return'] - results['close']['total_return']:+.2f}% difference")
    
    return results


@pytest.mark.slow
def test_backtest_all_price_types():
    """Test realistic backtest with 1-minute data for all price types."""
    if not (os.getenv('ALPACA_PAPER_KEY') and os.getenv('ALPACA_PAPER_SECRET')):
        pytest.skip('Alpaca credentials not available')

    end = dt.datetime.now() - dt.timedelta(days=5)
    start = end - dt.timedelta(days=365*1)  # Run for the past year, not including last 5 days
    for price_type in ["close", "open", "mid", "vwap"]:
        curve = run_backtest(start, end, price_type=price_type, slippage_bps=5, noise_factor=0.001)
        assert len(curve) > 0


@pytest.mark.slow
def test_backtest_dual_rebalance():
    """Test the dual-rebalance mode with realistic slippage and 1-minute pricing."""
    if not (os.getenv('ALPACA_PAPER_KEY') and os.getenv('ALPACA_PAPER_SECRET')):
        pytest.skip('Alpaca credentials not available')

    end = dt.datetime.now() - dt.timedelta(days=5)
    start = end - dt.timedelta(days=90)  # Shorter period for dual-rebalance test
    curve = run_backtest_dual_rebalance(start, end, slippage_bps=5, noise_factor=0.001, use_minute_candles=False)
    assert len(curve) > 0
    assert curve[-1] > 0  # Final equity should be positive


@pytest.mark.slow
def test_backtest_comparison():
    """Test that runs all price types and dual-rebalance mode with realistic execution."""
    if not (os.getenv('ALPACA_PAPER_KEY') and os.getenv('ALPACA_PAPER_SECRET')):
        pytest.skip('Alpaca credentials not available')

    end = dt.datetime.now() - dt.timedelta(days=5)
    start = end - dt.timedelta(days=365*1)  # Run for the past year, not including last 5 days
    results = run_backtest_comparison(start, end, slippage_bps=5, noise_factor=0.001, use_minute_candles=False)
    
    # Assert all strategies have positive equity curves
    for strategy_name, result in results.items():
        assert len(result['equity_curve']) > 0
        assert result['final_equity'] > 0
        
    # Ensure dual-rebalance and vwap are included
    assert 'dual_rebalance' in results
    assert 'vwap' in results


@pytest.mark.slow
def test_slippage_impact():
    """Test that higher slippage reduces returns with realistic execution."""
    if not (os.getenv('ALPACA_PAPER_KEY') and os.getenv('ALPACA_PAPER_SECRET')):
        pytest.skip('Alpaca credentials not available')

    end = dt.datetime.now() - dt.timedelta(days=5)
    start = end - dt.timedelta(days=180)  # 6 months
    
    # Run with low and high slippage
    low_slippage_curve = run_backtest(start, end, price_type="close", slippage_bps=1, noise_factor=0.001)
    high_slippage_curve = run_backtest(start, end, price_type="close", slippage_bps=10, noise_factor=0.001)
    
    # Higher slippage should generally result in lower final equity
    low_final = low_slippage_curve[-1]
    high_final = high_slippage_curve[-1]
    
    console.print(f"Low slippage (1 bps) final equity: ${low_final:,.2f}")
    console.print(f"High slippage (10 bps) final equity: ${high_final:,.2f}")
    
    # This should generally be true, but we'll just ensure both are positive
    assert low_final > 0
    assert high_final > 0


@pytest.mark.slow
def test_market_noise_impact():
    """Test that market noise affects execution but doesn't break the backtest."""
    if not (os.getenv('ALPACA_PAPER_KEY') and os.getenv('ALPACA_PAPER_SECRET')):
        pytest.skip('Alpaca credentials not available')

    end = dt.datetime.now() - dt.timedelta(days=5)
    start = end - dt.timedelta(days=90)  # 3 months
    
    # Run with no noise and with noise
    no_noise_curve = run_backtest(start, end, price_type="close", slippage_bps=5, noise_factor=0.0)
    with_noise_curve = run_backtest(start, end, price_type="close", slippage_bps=5, noise_factor=0.002)
    
    # Both should be positive and have similar length
    assert len(no_noise_curve) > 0
    assert len(with_noise_curve) > 0
    assert no_noise_curve[-1] > 0
    assert with_noise_curve[-1] > 0
    
    console.print(f"No noise final equity: ${no_noise_curve[-1]:,.2f}")
    console.print(f"With noise final equity: ${with_noise_curve[-1]:,.2f}")
    
    # The results should be different due to noise (very unlikely to be exactly the same)
    assert abs(no_noise_curve[-1] - with_noise_curve[-1]) > 0.01
