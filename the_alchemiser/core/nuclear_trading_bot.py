#!/usr/bin/env python3
"""
Nuclear Trading Bot Engine

This module provides orchestration and execution for the Nuclear Energy trading strategy, including:
- Data fetching and technical indicator calculation
- Strategy evaluation using pure logic from strategy_engine.py
- Alert generation, logging, and S3 integration
- Portfolio allocation reporting and display
- Both continuous and one-shot execution modes

Pure strategy logic (portfolio construction, signal generation) resides in strategy_engine.py.
This file handles the real-world orchestration, data management, and execution layers.
"""


# Standard library imports
import json
import logging
import warnings
import datetime as dt

# Third-party imports
import pandas as pd
import numpy as np

# Local imports
from the_alchemiser.core.logging_utils import setup_logging
from the_alchemiser.core.config import Config
from the_alchemiser.core.indicators import TechnicalIndicators

# Setup
warnings.filterwarnings('ignore')
config = Config()
logging_config = config['logging']

# Initialize logging once
level_str = logging_config.get('level', 'INFO').upper()
level_map = {
    'CRITICAL': logging.CRITICAL, 'ERROR': logging.ERROR, 'WARNING': logging.WARNING,
    'INFO': logging.INFO, 'DEBUG': logging.DEBUG, 'NOTSET': logging.NOTSET
}
setup_logging(log_level=level_map.get(level_str, logging.INFO))



# Import Alert from alert_service
from the_alchemiser.core.alert_service import Alert





# Import UnifiedDataProvider from the new module
from the_alchemiser.core.data_provider import UnifiedDataProvider

from enum import Enum, auto

# ActionType enum for clarity and safety
class ActionType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

class NuclearStrategyEngine:
    def get_best_nuclear_stocks(self, indicators, top_n=3):
        """Get top performing nuclear stocks based on 90-day moving average return."""
        portfolio = self.strategy.get_nuclear_portfolio(indicators, top_n=top_n)
        return list(portfolio.keys())[:top_n]
    """Nuclear Strategy Engine - Orchestrates data, indicators, and strategy logic"""

    def __init__(self, data_provider=None):
        if data_provider is None:
            raise ValueError("data_provider is required for NuclearStrategyEngine")
        self.data_provider = data_provider
        self.indicators = TechnicalIndicators()
        
        # Import the pure strategy engine
        from the_alchemiser.core.strategy_engine import NuclearStrategyEngine as PureStrategyEngine
        self.strategy = PureStrategyEngine()

        # Core symbols from the Nuclear strategy
        self.market_symbols = ['SPY', 'IOO', 'TQQQ', 'VTV', 'XLF', 'VOX']
        self.volatility_symbols = ['UVXY', 'BTAL']
        self.tech_symbols = ['QQQ', 'SQQQ', 'PSQ', 'UPRO']
        self.bond_symbols = ['TLT', 'IEF']

        # Nuclear energy stocks (the core of this strategy)
        self.nuclear_symbols = ['SMR', 'BWXT', 'LEU', 'EXC', 'NLR', 'OKLO']

        # All symbols
        self.all_symbols = (
            self.market_symbols + self.volatility_symbols +
            self.tech_symbols + self.bond_symbols + self.nuclear_symbols
        )

    def get_market_data(self):
        """Fetch data for all symbols"""
        market_data = {}
        for symbol in self.all_symbols:
            data = self.data_provider.get_data(symbol)
            if not data.empty:
                market_data[symbol] = data
            else:
                logging.warning(f"Could not fetch data for {symbol}")
        return market_data

    def safe_get_indicator(self, data, indicator_func, *args, **kwargs):
        """Safely get indicator value, logging exceptions to surface data problems."""
        try:
            result = indicator_func(data, *args, **kwargs)
            if hasattr(result, 'iloc') and len(result) > 0:
                value = result.iloc[-1]
                # Check if value is NaN - if so, try to find the last valid value
                if pd.isna(value):
                    # Find the last non-NaN value
                    valid_values = result.dropna()
                    if len(valid_values) > 0:
                        value = valid_values.iloc[-1]
                    else:
                        logging.error(f"No valid values for indicator {indicator_func.__name__} on data: {data}")
                        return 50.0  # Fallback only if no valid values
                return float(value)
            logging.error(f"Indicator {indicator_func.__name__} returned no results for data: {data}")
            return 50.0
        except Exception as e:
            logging.error(f"Exception in safe_get_indicator for {indicator_func.__name__}: {e}\nData: {data}")
            return 50.0

    def calculate_indicators(self, market_data):
        """Calculate all technical indicators"""
        indicators = {}
        for symbol, df in market_data.items():
            if df.empty:
                continue
            close = df['Close']
            indicators[symbol] = {
                'rsi_10': self.safe_get_indicator(close, self.indicators.rsi, 10),
                'rsi_20': self.safe_get_indicator(close, self.indicators.rsi, 20),
                'ma_200': self.safe_get_indicator(close, self.indicators.moving_average, 200),
                'ma_20': self.safe_get_indicator(close, self.indicators.moving_average, 20),
                'ma_return_90': self.safe_get_indicator(close, self.indicators.moving_average_return, 90),
                'cum_return_60': self.safe_get_indicator(close, self.indicators.cumulative_return, 60),
                'current_price': float(close.iloc[-1]),
            }
        return indicators

    def evaluate_nuclear_strategy(self, indicators, market_data=None):
        """
        Evaluate the Nuclear Energy strategy using the canonical hierarchical logic from Clojure implementation.
        Returns: (recommended_symbol, action, reason)
        """
        from the_alchemiser.core.strategy_engine import (
            BullMarketStrategy, BearMarketStrategy, OverboughtStrategy, SecondaryOverboughtStrategy, VoxOverboughtStrategy
        )
        if 'SPY' not in indicators:
            return 'SPY', ActionType.HOLD.value, "Missing SPY data"

        # Hierarchical logic matching the Clojure canonical strategy
        spy_rsi_10 = indicators['SPY']['rsi_10']
        
        # Primary overbought check: SPY RSI > 79
        if spy_rsi_10 > 79:
            result = OverboughtStrategy().recommend(indicators)
            if result:
                return result
        
        # Secondary overbought checks in order: IOO, TQQQ, VTV, XLF
        for symbol in ['IOO', 'TQQQ', 'VTV', 'XLF']:
            if symbol in indicators:
                if indicators[symbol]['rsi_10'] > 79:
                    result = SecondaryOverboughtStrategy().recommend(indicators, symbol)
                    if result:
                        return result
        
        # VOX overbought check  
        if 'VOX' in indicators and indicators['VOX']['rsi_10'] > 79:
            result = VoxOverboughtStrategy().recommend(indicators)
            if result:
                return result
        
        # Oversold conditions (TQQQ first, then SPY)
        if 'TQQQ' in indicators and indicators['TQQQ']['rsi_10'] < 30:
            return 'TQQQ', ActionType.BUY.value, "TQQQ oversold, buying dip"
        
        if indicators['SPY']['rsi_10'] < 30:
            return 'UPRO', ActionType.BUY.value, "SPY oversold, buying dip with leverage"
            
        # Bull vs Bear market determination (SPY above/below 200 MA)
        if 'SPY' in indicators and indicators['SPY']['current_price'] > indicators['SPY']['ma_200']:
            result = BullMarketStrategy(self.strategy).recommend(indicators, market_data)
            if result:
                return result
        else:
            result = BearMarketStrategy(self.strategy).recommend(indicators)
            if result:
                return result
        
        # Fallback if no strategy returns a result
        return 'SPY', ActionType.HOLD.value, "No clear signal, holding cash equivalent"


class NuclearTradingBot:
    """Nuclear Energy Trading Bot"""
    
    def __init__(self):
        self.strategy = NuclearStrategyEngine()
        self.load_config()
    
    def _ensure_scalar_price(self, price):
        """Ensure price is a scalar value for JSON serialization and string formatting"""
        if price is None:
            return None
        try:
            # If it's a pandas Series or similar, get the scalar value
            if hasattr(price, 'item') and callable(getattr(price, 'item')):
                price = price.item()
            elif hasattr(price, 'iloc'):
                # If it's still a Series, get the first element
                price = price.iloc[0]
            # Convert to float
            price = float(price)
            return price if not pd.isna(price) else None
        except (ValueError, TypeError, AttributeError) as e:
            return None
        
    def load_config(self):
        """Load configuration"""
        try:
            # Try to load from S3 first, then local
            from the_alchemiser.core.s3_utils import get_s3_handler
            import os
            s3_handler = get_s3_handler()
            
            # Check if file exists in S3 bucket
            s3_uri = "s3://the-alchemiser-s3/alert_config.json"
            if s3_handler.file_exists(s3_uri):
                content = s3_handler.read_text(s3_uri)
                if content:
                    self.config = json.loads(content)
                    return
            
            # Fallback to local file
            if os.path.exists('alert_config.json'):
                with open('alert_config.json', 'r') as f:
                    self.config = json.load(f)
                    return
                    
        except Exception as e:
            logging.warning(f"Could not load alert config: {e}")
            
        # Default config if nothing found
        self.config = {
            "alerts": {
                "cooldown_minutes": 30
            }
        }
    
    def handle_nuclear_portfolio_signal(self, symbol, action, reason, indicators, market_data=None):
        """Delegate alert creation to alert_service.create_alerts_from_signal"""
        from the_alchemiser.core.alert_service import create_alerts_from_signal
        return create_alerts_from_signal(
            symbol, action, reason, indicators, market_data,
            self.strategy.data_provider, self._ensure_scalar_price, self.strategy
        )
    
    def run_analysis(self):
        """Run complete strategy analysis"""
        logging.debug("Starting Nuclear Energy strategy analysis...")
        
        # Get market data
        market_data = self.strategy.get_market_data()
        if not market_data:
            logging.error("No market data available")
            return None
        
        # Calculate indicators
        indicators = self.strategy.calculate_indicators(market_data)
        if not indicators:
            logging.error("No indicators calculated")
            return None
        
        # Evaluate strategy
        symbol, action, reason = self.strategy.evaluate_nuclear_strategy(indicators, market_data)
        
        # Handle nuclear portfolio signal properly
        alerts = self.handle_nuclear_portfolio_signal(symbol, action, reason, indicators, market_data)
        
        logging.info(f"Analysis complete: {action} {symbol} - {reason}")
        return alerts
    
    def log_alert(self, alert):
        """Log alert to file - delegates to alert service"""
        from the_alchemiser.core.alert_service import log_alert_to_file
        log_alert_to_file(alert)
    
    def run_once(self):
        """Run analysis once"""
        alerts = self.run_analysis()
        
        if alerts and len(alerts) > 0:
            # Log all alerts
            for alert in alerts:
                self.log_alert(alert)
            
            # Display results
            if len(alerts) > 1:
                # Nuclear portfolio signal
                logging.info(f"NUCLEAR PORTFOLIO SIGNAL: {len(alerts)} stocks allocated")
                logging.info(f"NUCLEAR PORTFOLIO ALLOCATION:")
                for alert in alerts:
                    if alert.action != 'HOLD':
                        logging.info(f"   {alert.action} {alert.symbol} at ${alert.price:.2f}")
                        logging.info(f"      Reason: {alert.reason}")
                    else:
                        logging.info(f"   {alert.action} {alert.symbol} at ${alert.price:.2f}")
                        logging.info(f"      Reason: {alert.reason}")
                        
                # Show portfolio allocation details
                portfolio = self.get_current_portfolio_allocation()
                if portfolio:
                    logging.info(f"PORTFOLIO DETAILS:")
                    for symbol, data in portfolio.items():
                        logging.info(f"   {symbol}: {data['weight']:.1%}")
            else:
                # Single signal
                alert = alerts[0]
                if alert.action != 'HOLD':
                    logging.info(f"NUCLEAR TRADING SIGNAL: {alert.action} {alert.symbol} at ${alert.price:.2f}")
                    logging.info(f"   Reason: {alert.reason}")
                else:
                    logging.info(f"Nuclear Analysis: {alert.action} {alert.symbol} at ${alert.price:.2f}")
                    logging.info(f"   Reason: {alert.reason}")
            
            # Print technical indicator values for key symbols
            if alerts and hasattr(self.strategy, 'calculate_indicators'):
                market_data = self.strategy.get_market_data()
                indicators = self.strategy.calculate_indicators(market_data)
                logging.info("Technical Indicators Used for Signal Generation:")
                for symbol in ['IOO', 'SPY', 'TQQQ', 'VTV', 'XLF']:
                    if symbol in indicators:
                        logging.info(f"  {symbol}: RSI(10)={indicators[symbol].get('rsi_10')}, RSI(20)={indicators[symbol].get('rsi_20')}")
            
            return alerts[0]  # Return first alert for compatibility
        else:
            logging.info("Unable to generate nuclear energy signal")
            return None
    
    def run_continuous(self, interval_minutes=15):
        """Run analysis continuously"""
        import time
        
        logging.info(f"Starting continuous Nuclear Energy analysis (every {interval_minutes} minutes)")
        
        while True:
            try:
                self.run_once()
                time.sleep(interval_minutes * 60)
            except KeyboardInterrupt:
                logging.info("Stopping Nuclear Energy bot...")
                break
            except Exception as e:
                logging.error(f"Error in continuous run: {e}")
                time.sleep(60)
    
    def get_current_portfolio_allocation(self):
        """Get current portfolio allocation for display purposes"""
        # Get market data and indicators
        market_data = self.strategy.get_market_data()
        if not market_data:
            return None
        
        indicators = self.strategy.calculate_indicators(market_data)
        if not indicators:
            return None
        
        # Get strategy recommendation
        symbol, action, reason = self.strategy.evaluate_nuclear_strategy(indicators, market_data)
        
        # If we're in a bull market, show the nuclear portfolio
        if 'SPY' in indicators:
            spy_price = indicators['SPY']['current_price']
            spy_ma_200 = indicators['SPY']['ma_200']
            
            if spy_price > spy_ma_200 and action == 'BUY':
                nuclear_portfolio = self.strategy.strategy.get_nuclear_portfolio(indicators, market_data)
                if nuclear_portfolio:
                    # Add current prices and market values
                    portfolio_with_prices = {}
                    for symbol, data in nuclear_portfolio.items():
                        if symbol in indicators:
                            current_price = indicators[symbol]['current_price']
                            portfolio_with_prices[symbol] = {
                                'weight': data['weight'],
                                'performance': data['performance'],
                                'current_price': current_price,
                                'market_value': 10000 * data['weight'],  # Assuming $10k portfolio
                                'shares': (10000 * data['weight']) / current_price
                            }
                    return portfolio_with_prices
        
        return None

