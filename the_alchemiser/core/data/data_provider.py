import pandas as pd
import time
import os
import logging
import requests
from typing import cast, Optional
from datetime import datetime, timedelta
from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockLatestQuoteRequest
from alpaca.data.timeframe import TimeFrame
from the_alchemiser.core.config import Config
from the_alchemiser.core.secrets.secrets_manager import SecretsManager
import requests


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
    
    def __init__(self, paper_trading=True, cache_duration=None, config=None, enable_real_time=True):
        """
        Initialize UnifiedDataProvider for Alpaca market data and trading.
        
        Args:
            paper_trading: Whether to use paper trading keys (default: True for safety)
            cache_duration: Cache duration in seconds (default from config)
            config: Configuration object. If None, will load from global config.
            enable_real_time: Whether to enable real-time WebSocket pricing (default: True)
        """
        self.paper_trading = paper_trading
        
        # Use provided config or load global config
        if config is None:
            from the_alchemiser.core.config import get_config
            config = get_config()
        self.config = config
        
        # Set cache duration
        if cache_duration is None:
            cache_duration = self.config['data']['cache_duration']
        self.cache_duration = cache_duration
        self.cache = {}
        
        # Initialize secrets manager - region will be loaded from config
        secrets_manager = SecretsManager()
        
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
        
        # Initialize real-time pricing service
        self.real_time_pricing: Optional['RealTimePricingManager'] = None
        if enable_real_time:
            try:
                from the_alchemiser.core.data.real_time_pricing import RealTimePricingManager
                self.real_time_pricing = RealTimePricingManager(
                    self.api_key, 
                    self.secret_key, 
                    paper_trading
                )
                self.real_time_pricing.set_fallback_provider(self.get_current_price_rest)
                self.real_time_pricing.start()
                logging.info("✅ Real-time pricing enabled")
            except Exception as e:
                logging.warning(f"Failed to initialize real-time pricing: {e}")
                self.real_time_pricing = None
        
        logging.debug(f"Initialized UnifiedDataProvider with {'paper' if paper_trading else 'live'} trading keys")
    
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
                logging.debug(f"Fetched and cached {len(df)} bars for {symbol}")
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
        Get current market price for a symbol with real-time data priority.
        Uses just-in-time subscription for efficient resource usage.
        
        Args:
            symbol: Stock symbol
        Returns:
            float: Current price or None if unavailable
        """
        # Try real-time pricing first if available
        if self.real_time_pricing and self.real_time_pricing.is_connected():
            # Just-in-time subscription: subscribe only when we need pricing
            self.real_time_pricing.subscribe_for_trading(symbol)
            
            # Give a moment for real-time data to flow
            import time
            time.sleep(0.5)  # Brief wait for subscription to activate
            
            # Get real-time price
            price = self.real_time_pricing.get_current_price(symbol)
            if price is not None:
                logging.debug(f"Real-time price for {symbol}: ${price:.2f}")
                return price
        
        # Fallback to REST API
        return self.get_current_price_rest(symbol)
    
    def get_current_price_for_order(self, symbol):
        """
        Get current price specifically for order placement with optimized subscription management.
        
        This method:
        1. Subscribes to real-time data for the symbol
        2. Gets the most accurate price available
        3. Returns both price and cleanup function
        
        Args:
            symbol: Stock symbol
        Returns:
            tuple: (price, cleanup_function) where cleanup_function unsubscribes
        """
        def cleanup():
            """Cleanup function to unsubscribe after order placement."""
            if self.real_time_pricing:
                self.real_time_pricing.unsubscribe_after_trading(symbol)
                logging.debug(f"Unsubscribed from real-time data for {symbol}")
        
        # Try real-time pricing with just-in-time subscription
        if self.real_time_pricing and self.real_time_pricing.is_connected():
            # Subscribe for trading with high priority
            self.real_time_pricing.subscribe_for_trading(symbol)
            logging.debug(f"Subscribed to real-time data for {symbol} (order placement)")
            
            # Give a moment for real-time data to flow
            import time
            time.sleep(0.8)  # Slightly longer wait for order placement accuracy
            
            # Try to get real-time price
            price = self.real_time_pricing.get_current_price(symbol)
            if price is not None:
                logging.info(f"Using real-time price for {symbol} order: ${price:.2f}")
                return price, cleanup
            else:
                logging.debug(f"Real-time price not yet available for {symbol}, using REST API")
        
        # Fallback to REST API
        price = self.get_current_price_rest(symbol)
        logging.info(f"Using REST API price for {symbol} order: ${price:.2f}")
        return price, cleanup
    
    def get_current_price_rest(self, symbol):
        """
        Get current market price for a symbol using REST API.
        
        Args:
            symbol: Stock symbol
        Returns:
            float: Current price or None if unavailable
        """
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

    def get_latest_quote(self, symbol):
        """Get the latest bid and ask quote for a symbol."""
        try:
            request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
            latest_quote = self.data_client.get_stock_latest_quote(request)
            if latest_quote and symbol in latest_quote:
                quote = latest_quote[symbol]
                bid = float(getattr(quote, 'bid_price', 0) or 0)
                ask = float(getattr(quote, 'ask_price', 0) or 0)
                return bid, ask
        except Exception as e:
            logging.error(f"Error fetching latest quote for {symbol}: {e}")
        return 0.0, 0.0
    
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
        logging.debug("Data cache cleared")
    
    def get_cache_stats(self):
        """Get cache statistics."""
        return {
            'cache_size': len(self.cache),
            'cache_duration': self.cache_duration,
            'paper_trading': self.paper_trading
        }
    
    def get_portfolio_history(self, intraday_reporting="market_hours", pnl_reset="per_day", timeframe="1D"):
        """
        Get account portfolio history (closed P&L, equity curve).
        Returns: dict with keys: timestamp, equity, profit_loss, profit_loss_pct, base_value, etc.
        """
        url = f"{self.api_endpoint}/account/portfolio/history"
        params = {
            "intraday_reporting": intraday_reporting,
            "pnl_reset": pnl_reset,
            "timeframe": timeframe
        }
        headers = {
            "accept": "application/json",
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.secret_key
        }
        try:
            import requests
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"Error fetching portfolio history: {e}")
            return {}

    def get_open_positions(self):
        """
        Get all open positions (for open P&L, market value, etc).
        Returns: list of position dicts.
        """
        url = f"{self.api_endpoint}/positions"
        headers = {
            "accept": "application/json",
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.secret_key
        }
        try:
            import requests
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"Error fetching open positions: {e}")
            return []
