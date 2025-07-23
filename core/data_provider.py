import pandas as pd
import time
import os
import logging
from typing import cast
from datetime import datetime, timedelta
from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockLatestQuoteRequest
from alpaca.data.timeframe import TimeFrame
from .config import Config
from .secrets_manager import SecretsManager

# Load environment variables from .env file

class DataProvider:
    """Fetch market data with caching using Alpaca API ONLY."""
    def __init__(self, cache_duration=None):
        if cache_duration is None:
            config = Config()
            cache_duration = config['data']['cache_duration']
        
        self.cache = {}
        self.cache_duration = cache_duration  # seconds
        
                # Initialize Alpaca client with REAL trading keys
        secrets_manager = SecretsManager(region_name="eu-west-2")
        self.api_key, self.secret_key = secrets_manager.get_alpaca_keys(paper_trading=False)
        
        if not self.api_key or not self.secret_key:
            raise ValueError("Alpaca API keys not found in AWS Secrets Manager for live trading")
        
        self.data_client = StockHistoricalDataClient(self.api_key, self.secret_key)
        logging.info("Initialized Alpaca DataProvider with real trading keys")

    def get_data(self, symbol, period="1y", interval="1d"):
        now = time.time()
        cache_key = (symbol, period, interval)
        
        # Check cache
        if cache_key in self.cache:
            cached_time, data = self.cache[cache_key]
            if now - cached_time < self.cache_duration:
                return data
        
        # Fetch data from Alpaca ONLY
        df = self._get_alpaca_data(symbol, period, interval)
        
        if df is not None and not df.empty:
            self.cache[cache_key] = (now, df)
            return df
        
        return pd.DataFrame()  # Return empty DataFrame if download fails

    def _get_alpaca_data(self, symbol, period="1y", interval="1d"):
        """Get data from Alpaca API"""
        try:
            # Convert period to start/end dates
            end_date = datetime.now()
            
            if period == "1y":
                start_date = end_date - timedelta(days=365)
            elif period == "6mo":
                start_date = end_date - timedelta(days=180)
            elif period == "3mo":
                start_date = end_date - timedelta(days=90)
            elif period == "1mo":
                start_date = end_date - timedelta(days=30)
            elif period == "200d":
                start_date = end_date - timedelta(days=200)
            else:
                start_date = end_date - timedelta(days=365)  # Default to 1 year
            
            # Convert interval to TimeFrame
            if interval == "1d":
                timeframe = TimeFrame.Day
            elif interval == "1h":
                timeframe = TimeFrame.Hour
            elif interval == "1m":
                timeframe = TimeFrame.Minute
            else:
                timeframe = TimeFrame.Day
            
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=cast(TimeFrame, timeframe),
                start=start_date
                # Don't set end - let it default to 15 minutes ago for free tier
            )
            
            bars = self.data_client.get_stock_bars(request)
            
            if bars:
                try:
                    # BarSet objects have a data attribute that contains the actual bar data
                    if hasattr(bars, 'data') and bars.data:
                        bar_data = bars.data.get(symbol, [])
                    else:
                        # Try direct access
                        bar_data = getattr(bars, symbol, [])
                    
                    if bar_data:
                        # Convert to DataFrame with proper structure
                        data = []
                        for bar in bar_data:
                            data.append({
                                'Open': float(bar.open),
                                'High': float(bar.high),
                                'Low': float(bar.low),
                                'Close': float(bar.close),
                                'Volume': int(bar.volume)
                            })
                        
                        df = pd.DataFrame(data)
                        
                        # Set proper datetime index
                        df.index = pd.to_datetime([bar.timestamp for bar in bar_data])
                        df.index.name = 'Date'
                        
                        logging.info(f"Successfully fetched {len(df)} bars for {symbol} from Alpaca")
                        return df
                    
                except Exception as e:
                    logging.error(f"Error processing bar data for {symbol}: {e}")
            
            logging.warning(f"No data returned from Alpaca for {symbol}")
            return pd.DataFrame()
            
        except Exception as e:
            logging.error(f"Error fetching Alpaca data for {symbol}: {e}")
            return pd.DataFrame()

    def get_current_price(self, symbol):
        """Get current price from Alpaca"""
        if os.getenv("TEST_MODE"):
            return 100.0
        try:
            # Try Alpaca latest quote first
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
            except Exception as e:
                logging.warning(f"Alpaca current price failed for {symbol}: {e}")
            
            # Fall back to using recent historical data
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
            logging.error(f"Error getting current price for {symbol}: {e}")
            if os.getenv("TEST_MODE"):
                return 100.0
            return None

class AlpacaDataProvider:
    """Fetch market and account data from Alpaca API."""
    def __init__(self, paper_trading=False, endpoint=None, paper_endpoint=None):
        self.paper_trading = paper_trading
        from core.config import Config
        config = Config()
        
        # Initialize secrets manager
        secrets_manager = SecretsManager(region_name="eu-west-2")
        
        # Get API keys from AWS Secrets Manager
        self.api_key, self.secret_key = secrets_manager.get_alpaca_keys(paper_trading=paper_trading)
        
        if not self.api_key or not self.secret_key:
            raise ValueError(f"Alpaca API keys not found in AWS Secrets Manager for {'paper' if paper_trading else 'live'} trading")
        
        # Set endpoints
        if paper_trading:
            self.api_endpoint = paper_endpoint or config['alpaca'].get('paper_endpoint', 'https://paper-api.alpaca.markets/v2')
        else:
            self.api_endpoint = endpoint or config['alpaca'].get('endpoint', 'https://api.alpaca.markets')
            
        self.trading_client = TradingClient(self.api_key, self.secret_key, paper=paper_trading)
        self.data_client = StockHistoricalDataClient(self.api_key, self.secret_key)
        
        logging.info(f"Initialized AlpacaDataProvider with {'paper' if paper_trading else 'live'} trading keys")

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


class UnifiedDataProvider:
    """
    Unified data provider that consolidates market data and trading functionality.
    
    This class combines the best features of both DataProvider and AlpacaDataProvider:
    - Proper paper_trading parameter handling
    - Unified caching system
    - Consistent error handling
    - Both market data and trading functionality
    - Proper type safety
    """
    
    def __init__(self, paper_trading=True, cache_duration=None):
        """
        Initialize unified data provider.
        
        Args:
            paper_trading: Whether to use paper trading keys (default: True for safety)
            cache_duration: Cache duration in seconds (default from config)
        """
        self.paper_trading = paper_trading
        self.config = Config()
        
        # Set cache duration
        if cache_duration is None:
            cache_duration = self.config['data']['cache_duration']
        self.cache_duration = cache_duration
        self.cache = {}
        
        # Initialize secrets manager
        secrets_manager = SecretsManager(region_name="eu-west-2")
        
        # Get API keys from AWS Secrets Manager
        self.api_key, self.secret_key = secrets_manager.get_alpaca_keys(paper_trading=paper_trading)
        
        if not self.api_key or not self.secret_key:
            raise ValueError(f"Alpaca API keys not found in AWS Secrets Manager for {'paper' if paper_trading else 'live'} trading")
        
        # Initialize Alpaca clients
        self.data_client = StockHistoricalDataClient(self.api_key, self.secret_key)
        self.trading_client = TradingClient(self.api_key, self.secret_key, paper=paper_trading)
        
        # Set endpoints (for reference)
        if paper_trading:
            self.api_endpoint = self.config['alpaca'].get('paper_endpoint', 'https://paper-api.alpaca.markets/v2')
        else:
            self.api_endpoint = self.config['alpaca'].get('endpoint', 'https://api.alpaca.markets')
        
        logging.info(f"Initialized UnifiedDataProvider with {'paper' if paper_trading else 'live'} trading keys")
    
    def get_data(self, symbol, period="1y", interval="1d"):
        """
        Get historical market data with caching.
        
        Args:
            symbol: Stock symbol
            period: Time period (1y, 6mo, 3mo, 1mo, 200d)
            interval: Data interval (1d, 1h, 1m)
            
        Returns:
            pandas.DataFrame with OHLCV data
        """
        now = time.time()
        cache_key = (symbol, period, interval)
        
        # Check cache
        if cache_key in self.cache:
            cached_time, data = self.cache[cache_key]
            if now - cached_time < self.cache_duration:
                logging.debug(f"Returning cached data for {symbol}")
                return data
        
        # Fetch fresh data
        try:
            df = self._fetch_historical_data(symbol, period, interval)
            
            if df is not None and not df.empty:
                # Cache the data
                self.cache[cache_key] = (now, df)
                logging.info(f"Fetched and cached {len(df)} bars for {symbol}")
                return df
            else:
                logging.warning(f"No data returned for {symbol}")
                return pd.DataFrame()
                
        except Exception as e:
            logging.error(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()
    
    def _fetch_historical_data(self, symbol, period="1y", interval="1d"):
        """Fetch historical data from Alpaca API."""
        try:
            # Convert period to start/end dates
            end_date = datetime.now()
            
            period_mapping = {
                "1y": 365,
                "6mo": 180,
                "3mo": 90,
                "1mo": 30,
                "200d": 200
            }
            days = period_mapping.get(period, 365)
            start_date = end_date - timedelta(days=days)
            
            # Convert interval to TimeFrame
            interval_mapping = {
                "1d": TimeFrame.Day,
                "1h": TimeFrame.Hour,
                "1m": TimeFrame.Minute
            }
            timeframe = interval_mapping.get(interval, TimeFrame.Day)
            
            # Create request
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=cast(TimeFrame, timeframe),
                start=start_date
                # Don't set end - let it default to 15 minutes ago for free tier
            )
            
            # Fetch data
            bars = self.data_client.get_stock_bars(request)
            
            if not bars:
                return pd.DataFrame()
            
            # Extract bar data - handle different response formats safely
            bar_data = None
            try:
                # Try direct symbol access first (most common)
                if hasattr(bars, symbol):
                    bar_data = getattr(bars, symbol)
                # Try data dictionary access as fallback
                elif hasattr(bars, 'data'):
                    data_dict = getattr(bars, 'data', {})
                    if hasattr(data_dict, 'get'):
                        bar_data = data_dict.get(symbol, [])
                    elif symbol in data_dict:
                        bar_data = data_dict[symbol]
            except (AttributeError, KeyError, TypeError):
                pass
            
            if not bar_data:
                return pd.DataFrame()
            
            # Convert to DataFrame
            data_rows = []
            timestamps = []
            
            for bar in bar_data:
                if hasattr(bar, 'open') and hasattr(bar, 'high'):  # Validate bar structure
                    data_rows.append({
                        'Open': float(bar.open),
                        'High': float(bar.high),
                        'Low': float(bar.low),
                        'Close': float(bar.close),
                        'Volume': int(bar.volume) if hasattr(bar, 'volume') else 0
                    })
                    timestamps.append(bar.timestamp)
            
            if not data_rows:
                return pd.DataFrame()
            
            # Create DataFrame with datetime index
            df = pd.DataFrame(data_rows)
            df.index = pd.to_datetime(timestamps)
            df.index.name = 'Date'
            
            return df
            
        except Exception as e:
            logging.error(f"Error fetching historical data for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_current_price(self, symbol):
        """
        Get current market price for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            float: Current price or None if unavailable
        """
        # Handle test mode
        if os.getenv("TEST_MODE"):
            return 100.0
        
        try:
            # Try to get latest quote
            request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
            latest_quote = self.data_client.get_stock_latest_quote(request)
            
            if latest_quote and symbol in latest_quote:
                quote = latest_quote[symbol]
                
                # Extract bid/ask prices safely
                bid = 0.0
                ask = 0.0
                
                if hasattr(quote, 'bid_price') and quote.bid_price:
                    bid = float(quote.bid_price)
                if hasattr(quote, 'ask_price') and quote.ask_price:
                    ask = float(quote.ask_price)
                
                # Return midpoint if both available
                if bid > 0 and ask > 0:
                    return (bid + ask) / 2
                elif bid > 0:
                    return bid
                elif ask > 0:
                    return ask
            
            # Fallback to recent historical data
            logging.debug(f"No current quote for {symbol}, falling back to historical data")
            df = self.get_data(symbol, period="1d", interval="1m")
            
            if df is not None and not df.empty and 'Close' in df.columns:
                price = df['Close'].iloc[-1]
                
                # Ensure scalar value
                if hasattr(price, 'item'):
                    price = price.item()
                
                price = float(price)
                return price if not pd.isna(price) else None
            
            return None
            
        except Exception as e:
            logging.error(f"Error getting current price for {symbol}: {e}")
            return None
    
    def get_historical_data(self, symbol, start, end, timeframe=None):
        """
        Get historical data for a specific date range.
        
        Args:
            symbol: Stock symbol
            start: Start datetime
            end: End datetime  
            timeframe: TimeFrame enum or string
            
        Returns:
            List of bar objects or empty list
        """
        try:
            # Handle timeframe parameter
            if timeframe is None:
                timeframe = TimeFrame.Day
            elif isinstance(timeframe, str):
                # Convert string to TimeFrame enum
                timeframe_mapping = {
                    'Day': TimeFrame.Day,
                    'Hour': TimeFrame.Hour,
                    'Minute': TimeFrame.Minute,
                    '1d': TimeFrame.Day,
                    '1h': TimeFrame.Hour,
                    '1m': TimeFrame.Minute
                }
                timeframe = timeframe_mapping.get(timeframe, TimeFrame.Day)
            
            # Create request
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=cast(TimeFrame, timeframe),
                start=start,
                end=end
            )
            
            # Fetch data
            bars = self.data_client.get_stock_bars(request)
            
            # Extract bars for the symbol safely
            try:
                # Try direct symbol access first
                if hasattr(bars, symbol):
                    return getattr(bars, symbol)
                # Try data dictionary access as fallback
                elif hasattr(bars, 'data'):
                    data_dict = getattr(bars, 'data', {})
                    if hasattr(data_dict, 'get'):
                        return data_dict.get(symbol, [])
                    elif symbol in data_dict:
                        return data_dict[symbol]
            except (AttributeError, KeyError, TypeError):
                pass
            
            return []
                
        except Exception as e:
            logging.error(f"Error fetching historical data for {symbol} from {start} to {end}: {e}")
            return []
    
    def get_account_info(self):
        """Get account information."""
        try:
            return self.trading_client.get_account()
        except Exception as e:
            logging.error(f"Error fetching account info: {e}")
            return None
    
    def get_positions(self):
        """Get all positions."""
        try:
            return self.trading_client.get_all_positions()
        except Exception as e:
            logging.error(f"Error fetching positions: {e}")
            return []
    
    def clear_cache(self):
        """Clear the data cache."""
        self.cache.clear()
        logging.info("Data cache cleared")
    
    def get_cache_stats(self):
        """Get cache statistics."""
        return {
            'cache_size': len(self.cache),
            'cache_duration': self.cache_duration,
            'paper_trading': self.paper_trading
        }
