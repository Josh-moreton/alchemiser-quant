#!/usr/bin/env python3
"""Reproduce exactly what the strategy engine sees for RSI calculation."""

import pandas as pd
from datetime import date, datetime, timezone

from the_alchemiser.shared.data_v2.market_data_store import MarketDataStore


class HistoricalMarketDataAdapter:
    def __init__(self, cutoff_date):
        self.cutoff_date = cutoff_date
        self.market_data_store = MarketDataStore()
        self._cache = {}

    def _get_dataframe(self, symbol):
        if symbol not in self._cache:
            df = self.market_data_store.read_symbol_data(symbol)
            if df is None or df.empty:
                self._cache[symbol] = pd.DataFrame()
            else:
                if 'timestamp' in df.columns:
                    df = df.set_index('timestamp')
                if not isinstance(df.index, pd.DatetimeIndex):
                    df.index = pd.to_datetime(df.index)
                self._cache[symbol] = df
        return self._cache[symbol]

    def get_bars(self, symbol, period, timeframe):
        symbol_str = str(symbol)
        df = self._get_dataframe(symbol_str)
        if df.empty:
            return []

        cutoff_datetime = pd.Timestamp(self.cutoff_date, tz=timezone.utc)
        if df.index.tz is None:
            df.index = df.index.tz_localize(timezone.utc)

        df_filtered = df[df.index.normalize() <= cutoff_datetime]
        return df_filtered


def wilder_rsi(prices, window=10):
    """Wilder's RSI using exponential smoothing."""
    delta = prices.diff()
    gains = delta.clip(lower=0)
    losses = (-delta).clip(lower=0)
    
    alpha = 1.0 / window
    avg_gain = gains.ewm(alpha=alpha, min_periods=window, adjust=False).mean()
    avg_loss = losses.ewm(alpha=alpha, min_periods=window, adjust=False).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return float(rsi.iloc[-1])


if __name__ == "__main__":
    cutoff = date(2026, 1, 7)
    adapter = HistoricalMarketDataAdapter(cutoff)

    print("=" * 70)
    print(f"REPRODUCING STRATEGY ENGINE DATA (cutoff {cutoff})")
    print("=" * 70)
    
    for symbol in ['KMLM', 'XLK']:
        df = adapter.get_bars(symbol, '1D', '1D')
        print(f'\n{symbol} - last 5 bars:')
        print(df.tail(5)[['close']])
        print(f'Total bars: {len(df)}')
        
        rsi = wilder_rsi(df['close'], 10)
        print(f'RSI(10): {rsi:.2f}')
    
    print("\n" + "=" * 70)
    print("EXPECTED from strategy trace:")
    print("  XLK RSI(10) = 59.26")
    print("  KMLM RSI(10) = 77.57")
    print("=" * 70)
