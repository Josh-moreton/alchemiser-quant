import yfinance as yf
import pandas as pd
import time
import os
import logging
from typing import cast
from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockLatestQuoteRequest
from alpaca.data.timeframe import TimeFrame
from .config import Config

class DataProvider:
    """Fetch market data with caching."""
    def __init__(self, cache_duration=None):
        if cache_duration is None:
            config = Config()
            cache_duration = config['data']['cache_duration']
        
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

class AlpacaDataProvider:
    """Fetch market and account data from Alpaca API."""
    def __init__(self, paper_trading=True, endpoint=None, paper_endpoint=None):
        self.paper_trading = paper_trading
        from core.config import Config
        config = Config()
        # API keys still loaded from .env for security
        if paper_trading:
            self.api_key = os.getenv('ALPACA_PAPER_KEY')
            self.secret_key = os.getenv('ALPACA_PAPER_SECRET')
            self.api_endpoint = paper_endpoint or config['alpaca'].get('paper_endpoint', 'https://paper-api.alpaca.markets/v2')
        else:
            self.api_key = os.getenv('ALPACA_KEY')
            self.secret_key = os.getenv('ALPACA_SECRET')
            self.api_endpoint = endpoint or config['alpaca'].get('endpoint', 'https://api.alpaca.markets')
        self.trading_client = TradingClient(self.api_key, self.secret_key, paper=paper_trading)
        self.data_client = StockHistoricalDataClient(self.api_key, self.secret_key)

    def get_current_price(self, symbol):
        """Get the latest midpoint price for a symbol."""
        try:
            request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
            latest_quote = self.data_client.get_stock_latest_quote(request)
            if latest_quote and symbol in latest_quote:
                quote = latest_quote[symbol]
                bid = float(getattr(quote, 'bid_price', 0) or 0)
                ask = float(getattr(quote, 'ask_price', 0) or 0)
                if bid > 0 and ask > 0:
                    return (bid + ask) / 2
                elif bid > 0:
                    return bid
                elif ask > 0:
                    return ask
            return None
        except Exception as e:
            logging.error(f"Error fetching Alpaca price for {symbol}: {e}")
            return None

    def get_historical_data(self, symbol, start, end, timeframe=None):
        """Fetch historical bars for a symbol."""
        try:
            # Default to TimeFrame.Day if not provided
            if timeframe is None:
                timeframe = TimeFrame.Day
            # Convert string timeframe to TimeFrame enum if needed
            elif isinstance(timeframe, str):
                try:
                    # Try to get the TimeFrame by name/value
                    for tf in [TimeFrame.Day, TimeFrame.Hour, TimeFrame.Minute]:
                        if str(tf) == timeframe or tf.name == timeframe:
                            timeframe = tf
                            break
                    else:
                        timeframe = TimeFrame.Day
                except Exception:
                    timeframe = TimeFrame.Day
            
            # Type assertion to help type checker
            timeframe_obj = cast(TimeFrame, timeframe)
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=timeframe_obj,
                start=start,
                end=end
            )
            bars = self.data_client.get_stock_bars(request)
            return bars[symbol] if bars and symbol in bars else []
        except Exception as e:
            logging.error(f"Error fetching Alpaca historical data for {symbol}: {e}")
            return []

    def get_account_info(self):
        try:
            return self.trading_client.get_account()
        except Exception as e:
            logging.error(f"Error fetching Alpaca account info: {e}")
            return None

    def get_positions(self):
        try:
            return self.trading_client.get_all_positions()
        except Exception as e:
            logging.error(f"Error fetching Alpaca positions: {e}")
            return []
