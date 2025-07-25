import os
import time
import datetime as dt
import pandas as pd
import pytest

from the_alchemiser.core.trading.strategy_manager import MultiStrategyManager, StrategyType
from the_alchemiser.core.data.data_provider import UnifiedDataProvider


def _preload_symbol_data(data_provider, symbols, start, end):
    """Fetch all required historical data in one shot."""
    symbol_data = {}
    for sym in symbols:
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
    return symbol_data


def _update_provider_cache(data_provider, symbol_data, current_day):
    """Update provider cache with data up to current_day."""
    for sym, df in symbol_data.items():
        slice_df = df[df.index < current_day]
        data_provider.cache[(sym, "1y", "1d")] = (time.time(), slice_df)


def run_backtest(start, end, initial_equity=100000):
    dp = UnifiedDataProvider(paper_trading=True, cache_duration=0)
    manager = MultiStrategyManager(shared_data_provider=dp)
    all_syms = list(set(manager.nuclear_engine.all_symbols + manager.tecl_engine.all_symbols))

    symbol_data = _preload_symbol_data(dp, all_syms, start - dt.timedelta(days=400), end)

    equity = initial_equity
    equity_curve = []
    prev_weights = {sym: 0 for sym in all_syms}

    for current_day in pd.date_range(start, end, freq='B'):
        _update_provider_cache(dp, symbol_data, current_day)
        signals, portfolio = manager.run_all_strategies()
        daily_ret = 0.0
        for sym, weight in prev_weights.items():
            if weight == 0:
                continue
            df = symbol_data[sym]
            if current_day not in df.index:
                continue
            prev_close = df[df.index < current_day]['Close'].iloc[-1]
            close_today = df.loc[current_day, 'Close']
            ret = (close_today - prev_close) / prev_close
            daily_ret += weight * ret
        equity *= (1 + daily_ret)
        equity_curve.append(equity)
        prev_weights = {sym: portfolio.get(sym, 0) for sym in all_syms}

    return equity_curve


@pytest.mark.slow
def test_backtest_smoke():
    if not (os.getenv('ALPACA_PAPER_KEY') and os.getenv('ALPACA_PAPER_SECRET')):
        pytest.skip('Alpaca credentials not available')

    end = dt.datetime.now() - dt.timedelta(days=5)
    start = end - dt.timedelta(days=30)
    curve = run_backtest(start, end)
    assert len(curve) > 0
