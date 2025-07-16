import yfinance as yf
import pandas as pd
import time

class DataProvider:
    """Fetch market data with caching."""
    def __init__(self, cache_duration=300):
        self.cache = {}
        self.cache_duration = cache_duration  # seconds

    def get_data(self, symbol, period="1y", interval="1d"):
        now = time.time()
        cache_key = (symbol, period, interval)
        # Check cache
        if cache_key in self.cache:
            cached_time, data = self.cache[cache_key]
            if now - cached_time < self.cache_duration:
                return data
        # Fetch new data
        df = yf.download(symbol, period=period, interval=interval, progress=False)
        if df is not None and not df.empty:
            self.cache[cache_key] = (now, df)
            return df
        return pd.DataFrame()  # Return empty DataFrame if download fails

    def get_current_price(self, symbol):
        try:
            df = self.get_data(symbol, period="1d", interval="1m")
            if df is not None and not df.empty and 'Close' in df.columns:
                price = df['Close'].iloc[-1]
                # Ensure we return a scalar value, not a Series
                if hasattr(price, 'item'):
                    price = price.item()
                # Convert to float and check if it's valid
                price = float(price)
                return price if not pd.isna(price) else None
            return None
        except Exception as e:
            print(f"Error getting current price for {symbol}: {e}")
            return None
