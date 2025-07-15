#!/usr/bin/env python3
"""
Alpaca Data Provider for Backtesting
Replaces yfinance with Alpaca Market Data API
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import time
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv

# Alpaca imports
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

load_dotenv()

class AlpacaBacktestDataProvider:
    """
    Alpaca-based data provider for backtesting
    Replaces yfinance functionality with Alpaca Market Data API
    Maintains the same interface as BacktestDataProvider for drop-in replacement
    """
    
    def __init__(self, start_date: str, end_date: str):
        self.start_date = start_date
        self.end_date = end_date
        self.logger = logging.getLogger(__name__)
        
        # Extend start date to ensure we have enough data for 200-day MA
        start_dt = pd.Timestamp(start_date)
        extended_start = start_dt - pd.Timedelta(days=400)  # More conservative buffer
        self.extended_start_date = extended_start.strftime('%Y-%m-%d')
        
        # Initialize Alpaca data client
        self.api_key = os.getenv('ALPACA_PAPER_KEY') or os.getenv('ALPACA_KEY')
        self.secret_key = os.getenv('ALPACA_PAPER_SECRET') or os.getenv('ALPACA_SECRET')
        
        if not self.api_key or not self.secret_key:
            raise ValueError("Alpaca API credentials not found in environment variables")
        
        self.logger.info(f"🔑 Using Alpaca credentials: API Key = {self.api_key[:8]}...")
        
        self.data_client = StockHistoricalDataClient(
            api_key=self.api_key,
            secret_key=self.secret_key
        )
        
        self.logger.info(f"🏦 Alpaca Data Provider initialized for {start_date} to {end_date}")
        
        # Cache for downloaded data (same as original)
        self.cache = {}
        self.all_data = {}
        self.hourly_data = {}
        
    def download_all_data(self, symbols: List[str], retries: int = 3) -> Dict[str, pd.DataFrame]:
        """
        Download historical data for all symbols using Alpaca API
        Returns data in same format as yfinance (OHLCV with datetime index)
        """
        self.logger.info(f"📊 Downloading daily data for {len(symbols)} symbols from Alpaca...")
        
        all_data = {}
        failed_symbols = []
        
        for symbol in symbols:
            try:
                if symbol in self.cache:
                    self.logger.debug(f"Using cached data for {symbol}")
                    all_data[symbol] = self.cache[symbol]
                    continue
                
                # Download with retry logic
                data = self._download_symbol_with_retry(symbol, retries, TimeFrame.Day, None)
                if data is not None and not data.empty:
                    all_data[symbol] = data
                    self.cache[symbol] = data
                    self.logger.info(f"✅ Downloaded {symbol}: {len(data)} daily records")
                else:
                    self.logger.warning(f"❌ No daily data received for {symbol}")
                    failed_symbols.append(symbol)
                    
            except Exception as e:
                self.logger.error(f"❌ Error downloading {symbol}: {e}")
                failed_symbols.append(symbol)
                continue
        
        if failed_symbols:
            self.logger.warning(f"Failed to download daily data: {failed_symbols}")
        
        self.all_data = all_data
        self.logger.info(f"📈 Successfully downloaded daily data for {len(all_data)}/{len(symbols)} symbols")
        return all_data
    
    def download_hourly_data(self, symbols: List[str], retries: int = 3) -> Dict[str, pd.DataFrame]:
        """Download hourly data for execution timing analysis"""
        self.logger.info(f"📊 Downloading hourly data for {len(symbols)} symbols from Alpaca...")
        
        hourly_data = {}
        failed_symbols = []
        
        # Calculate date range for hourly data (Alpaca has different limits than yfinance)
        start_dt = pd.Timestamp(self.start_date)
        end_dt = pd.Timestamp(self.end_date)
        
        # Check if requested period is reasonable for hourly data
        days_requested = (end_dt - start_dt).days
        if days_requested > 365:  # Conservative limit for hourly data
            self.logger.warning(f"Hourly data requested for {days_requested} days. Using last 365 days.")
            start_dt = end_dt - pd.Timedelta(days=365)
            adjusted_start = start_dt.strftime('%Y-%m-%d')
            self.logger.info(f"Adjusted hourly data start date to: {adjusted_start}")
        else:
            adjusted_start = self.start_date
        
        for symbol in symbols:
            try:
                # Download hourly data
                data = self._download_symbol_with_retry(symbol, retries, TimeFrame.Hour, adjusted_start)
                
                if data is not None and not data.empty:
                    # Filter to market hours only (9:30 AM - 4:00 PM ET)
                    # Alpaca data is typically in UTC, convert to ET
                    market_hours = data.between_time('13:30', '20:00')  # UTC equivalent of 9:30-4:00 ET
                    
                    if not market_hours.empty:
                        hourly_data[symbol] = market_hours
                        self.logger.info(f"✅ Downloaded {symbol}: {len(market_hours)} hourly records")
                    else:
                        self.logger.warning(f"❌ No market hours data for {symbol}")
                        failed_symbols.append(symbol)
                else:
                    failed_symbols.append(symbol)
                    
            except Exception as e:
                self.logger.warning(f"Failed hourly download for {symbol}: {e}")
                failed_symbols.append(symbol)
        
        if failed_symbols:
            self.logger.warning(f"Failed hourly downloads: {failed_symbols}")
        
        self.hourly_data = hourly_data
        return hourly_data
    
    def _download_symbol_with_retry(self, symbol: str, retries: int, timeframe, 
                                   custom_start: Optional[str] = None) -> Optional[pd.DataFrame]:
        """Download data for a single symbol with retry logic"""
        
        start_date = custom_start or self.extended_start_date
        
        self.logger.info(f"🔍 Attempting to download {symbol} data...")
        
        for attempt in range(retries + 1):
            try:
                # Create request for bars
                request = StockBarsRequest(
                    symbol_or_symbols=symbol,
                    timeframe=timeframe,
                    start=pd.Timestamp(start_date),
                    end=pd.Timestamp(self.end_date)
                )
                
                self.logger.debug(f"📡 Making Alpaca API request for {symbol}: {start_date} to {self.end_date}")
                
                # Get bars from Alpaca
                response = self.data_client.get_stock_bars(request)
                
                self.logger.debug(f"📊 Alpaca API response for {symbol}: {type(response)}")
                
                # Alpaca returns data in response.data dictionary
                response_data = getattr(response, 'data', None)
                if not response_data or symbol not in response_data:
                    self.logger.warning(f"❌ No data returned for {symbol}")
                    return None
                
                bars = response_data[symbol]
                
                if not bars:
                    self.logger.warning(f"❌ Empty bars list for {symbol}")
                    return None
                
                self.logger.info(f"✅ Retrieved {len(bars)} bars for {symbol}")
                
                # Convert to DataFrame with same structure as yfinance
                data_rows = []
                for bar in bars:
                    data_rows.append({
                        'Open': float(bar.open),
                        'High': float(bar.high),
                        'Low': float(bar.low),
                        'Close': float(bar.close),
                        'Volume': int(bar.volume)
                    })
                
                # Create DataFrame
                df = pd.DataFrame(data_rows)
                
                if df.empty:
                    return None
                
                # Set datetime index from bar timestamps
                df.index = pd.to_datetime([bar.timestamp for bar in bars])
                df.index.name = 'Date'
                
                # Normalize timezone - make timezone-naive like yfinance
                try:
                    # Type ignore for timezone handling
                    if hasattr(df.index, 'tz') and getattr(df.index, 'tz', None) is not None:
                        df.index = getattr(df.index, 'tz_localize')(None)  # type: ignore
                except (AttributeError, TypeError):
                    pass  # Index already timezone-naive or other timezone issue
                
                # Sort by date
                df = df.sort_index()
                
                # Remove any duplicate dates (keep last)
                df = df[~df.index.duplicated(keep='last')]
                
                return df
                
            except Exception as e:
                self.logger.error(f"❌ Error downloading {symbol} (attempt {attempt + 1}): {str(e)}")
                if attempt < retries:
                    wait_time = (attempt + 1) * 2  # Progressive backoff
                    self.logger.warning(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"All {retries + 1} attempts failed for {symbol}")
                    return None
        
        return None
    
    def get_data_up_to_date(self, symbol: str, as_of_date: pd.Timestamp) -> pd.DataFrame:
        """
        Get historical data for symbol up to (but not including) as_of_date
        This prevents look-ahead bias - SAME INTERFACE AS ORIGINAL
        """
        if symbol not in self.all_data:
            return pd.DataFrame()
        
        # Normalize as_of_date (same logic as original)
        if hasattr(as_of_date, 'tz_localize'):
            as_of_date = as_of_date.tz_localize(None) if as_of_date.tz is not None else as_of_date
        else:
            as_of_date = pd.Timestamp(as_of_date).tz_localize(None)
        
        # Get data strictly before as_of_date
        symbol_data = self.all_data[symbol]
        historical_data = symbol_data[symbol_data.index < as_of_date]
        
        return historical_data
    
    def get_price_at_time(self, symbol: str, date: pd.Timestamp, price_type: str = 'Close') -> Optional[float]:
        """Get specific price at exact date - SAME INTERFACE AS ORIGINAL"""
        data = self.get_data_up_to_date(symbol, date + pd.Timedelta(days=1))
        
        if data.empty:
            return None
        
        # Find the exact date or last available date
        target_date = date.normalize()
        if target_date in data.index:
            price_value = data.loc[target_date, price_type]
            return float(price_value) if price_value is not None else None  # type: ignore
        elif not data.empty:
            price_value = data.iloc[-1][price_type]
            return float(price_value) if price_value is not None else None  # type: ignore
        
        return None
    
    def get_hourly_prices_for_date(self, symbol: str, date: pd.Timestamp) -> pd.DataFrame:
        """Get all hourly prices for a specific trading date - SAME INTERFACE AS ORIGINAL"""
        if not hasattr(self, 'hourly_data') or symbol not in self.hourly_data:
            return pd.DataFrame()
        
        hourly_data = self.hourly_data[symbol]
        date_normalized = date.normalize()
        
        # Get all hours for this date
        date_hours = hourly_data[hourly_data.index.date == date_normalized.date()]
        
        return date_hours
    
    def get_price_at_hour(self, symbol: str, date: pd.Timestamp, hour: int) -> Optional[float]:
        """Get price at specific hour - SAME INTERFACE AS ORIGINAL"""
        if not hasattr(self, 'hourly_data') or symbol not in self.hourly_data:
            return None
        
        # Create timestamp for the specific hour (30 minutes past to align with market open)
        target_time = date.normalize() + pd.Timedelta(hours=hour, minutes=30)
        
        hourly_data = self.hourly_data[symbol]
        
        # Find exact hour or closest available
        date_hours = hourly_data[hourly_data.index.date == date.date()]
        if date_hours.empty:
            return None
        
        # Try exact match first
        if target_time in date_hours.index:
            return float(date_hours.loc[target_time, 'Close'])
        
        # Find closest hour
        try:
            closest_idx = date_hours.index.get_loc(target_time, method='nearest')
            return float(date_hours.iloc[closest_idx]['Close'])
        except (KeyError, IndexError):
            return None
    
    def validate_data_coverage(self, symbols: List[str]) -> Dict[str, Dict]:
        """Validate data coverage and quality"""
        coverage_report = {}
        
        for symbol in symbols:
            if symbol not in self.all_data:
                coverage_report[symbol] = {
                    'status': 'missing',
                    'bars': 0,
                    'date_range': None
                }
                continue
            
            data = self.all_data[symbol]
            if data.empty:
                coverage_report[symbol] = {
                    'status': 'empty',
                    'bars': 0,
                    'date_range': None
                }
                continue
            
            # Check data quality
            missing_values = data.isnull().sum().sum()
            zero_volume_days = (data['Volume'] == 0).sum()
            
            coverage_report[symbol] = {
                'status': 'available',
                'bars': len(data),
                'date_range': f"{data.index[0].date()} to {data.index[-1].date()}",
                'missing_values': missing_values,
                'zero_volume_days': zero_volume_days,
                'avg_volume': data['Volume'].mean(),
                'price_range': f"${data['Low'].min():.2f} - ${data['High'].max():.2f}"
            }
        
        return coverage_report

# Test function
def test_alpaca_data_provider():
    """Test the Alpaca data provider"""
    import logging
    
    logging.basicConfig(level=logging.INFO)
    
    # Test with a small date range
    provider = AlpacaBacktestDataProvider('2024-11-01', '2024-12-31')
    
    # Test symbols
    test_symbols = ['SPY', 'QQQ', 'SMR', 'LEU']
    
    # Download data
    data = provider.download_all_data(test_symbols)
    
    print(f"Downloaded data for {len(data)} symbols")
    
    for symbol, df in data.items():
        print(f"{symbol}: {len(df)} bars from {df.index[0].date()} to {df.index[-1].date()}")
    
    # Test point-in-time access
    test_date = pd.Timestamp('2024-11-15')
    spy_data = provider.get_data_up_to_date('SPY', test_date)
    print(f"SPY data up to {test_date.date()}: {len(spy_data)} bars")
    
    # Test price lookup
    spy_price = provider.get_price_at_time('SPY', test_date)
    print(f"SPY price on {test_date.date()}: ${spy_price:.2f}")

if __name__ == "__main__":
    test_alpaca_data_provider()
