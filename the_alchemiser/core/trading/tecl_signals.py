#!/usr/bin/env python3
"""
TECL Signal Generator

This module implements the signal generation layer for the TECL strategy, including:
- Market regime detection using SPY vs 200-day MA
- RSI-based timing signals and sector rotation (XLK vs KMLM)
- Dynamic allocation between TECL, BIL, UVXY, SQQQ, and BSV
- Volatility protection and defensive positioning
- Technical indicator calculation, alert generation, and S3 integration
- Both continuous and one-shot execution modes

This file handles data fetching, orchestration, and signal generation for the TECL strategy,
while pure strategy logic resides in tecl_strategy_engine.py.
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
from the_alchemiser.core.indicators.indicators import TechnicalIndicators
from the_alchemiser.core.config import get_config
from the_alchemiser.core.logging.logging_utils import setup_logging

warnings.filterwarnings('ignore')
setup_logging()  # Centralized logging setup


# Import Alert from alert_service
from the_alchemiser.core.alerts.alert_service import Alert

# Import UnifiedDataProvider from the new module
from the_alchemiser.core.data.data_provider import UnifiedDataProvider

from enum import Enum

# Import ActionType from common module
from the_alchemiser.core.utils.common import ActionType


class TECLStrategyEngine:
    """TECL Strategy Engine - Orchestrates data, indicators, and strategy logic"""

    def __init__(self, data_provider=None):
        if data_provider is None:
            raise ValueError("data_provider is required for TECLStrategyEngine")
        self.data_provider = data_provider
        self.indicators = TechnicalIndicators()
        
        # Import the pure strategy engine
        from the_alchemiser.core.trading.tecl_strategy_engine import TECLStrategyEngine as PureStrategyEngine
        self.strategy = PureStrategyEngine(data_provider=self.data_provider)

        # TECL strategy symbols
        self.market_symbols = ['SPY', 'XLK', 'KMLM']
        self.tecl_symbols = ['TECL', 'BIL', 'UVXY', 'SQQQ', 'BSV']
        self.tech_symbols = ['TQQQ', 'SPXL']  # For oversold signals

        # All symbols needed for TECL strategy
        self.all_symbols = (
            self.market_symbols + self.tecl_symbols + self.tech_symbols
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
        """Calculate all technical indicators needed for TECL strategy"""
        indicators = {}
        for symbol, df in market_data.items():
            if df.empty:
                continue
            close = df['Close']
            indicators[symbol] = {
                'rsi_9': self.safe_get_indicator(close, self.indicators.rsi, 9),
                'rsi_10': self.safe_get_indicator(close, self.indicators.rsi, 10),
                'rsi_20': self.safe_get_indicator(close, self.indicators.rsi, 20),
                'ma_200': self.safe_get_indicator(close, self.indicators.moving_average, 200),
                'ma_20': self.safe_get_indicator(close, self.indicators.moving_average, 20),
                'current_price': float(close.iloc[-1]),
            }
        return indicators

    def evaluate_tecl_strategy(self, indicators, market_data=None):
        """
        Evaluate the TECL strategy using the pure strategy logic.
        Returns: (recommended_symbol, action, reason)
        """
        return self.strategy.evaluate_tecl_strategy(indicators, market_data)


class TECLSignalGenerator:
    """TECL Signal Generator"""
    
    def __init__(self):
        self.strategy = TECLStrategyEngine()
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
            print(f"Error converting price to scalar: {e}")
            return None
        
    def load_config(self):
        """Load configuration"""
        try:
            # Try to load from S3 first, then local
            from the_alchemiser.core.utils.s3_utils import get_s3_handler
            import os
            s3_handler = get_s3_handler()
            
            # Check if file exists in S3 bucket
            from the_alchemiser.core.config import get_config
            global_config = get_config()
            s3_uri = global_config['alerts'].get('alert_config_s3', 's3://the-alchemiser-s3/alert_config.json')
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
            
        # Default config if nothing found - use global config values
        from the_alchemiser.core.config import get_config
        global_config = get_config()
        self.config = {
            "alerts": {
                "cooldown_minutes": global_config['alerts'].get('cooldown_minutes', 30)
            }
        }
    
    def handle_tecl_portfolio_signal(self, symbol, action, reason, indicators, market_data=None):
        """Delegate alert creation to alert_service.create_alerts_from_signal"""
        from the_alchemiser.core.alerts.alert_service import create_alerts_from_signal
        return create_alerts_from_signal(
            symbol, action, reason, indicators, market_data,
            self.strategy.data_provider, self._ensure_scalar_price, self.strategy
        )
    
    def run_analysis(self):
        """Run complete TECL strategy analysis"""
        logging.info("Starting TECL strategy analysis...")
        
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
        symbol, action, reason = self.strategy.evaluate_tecl_strategy(indicators, market_data)
        
        # Handle TECL portfolio signal properly
        alerts = self.handle_tecl_portfolio_signal(symbol, action, reason, indicators, market_data)
        
        logging.info(f"Analysis complete: {action} {symbol} - {reason}")
        return alerts
    
    def log_alert(self, alert):
        """Log alert to file - delegates to alert service"""
        from the_alchemiser.core.alerts.alert_service import log_alert_to_file
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
                # Multi-asset TECL portfolio signal
                print(f"🚨 TECL PORTFOLIO SIGNAL: {len(alerts)} assets allocated")
                print(f"\n🔵 TECL PORTFOLIO ALLOCATION:")
                for alert in alerts:
                    if alert.action != 'HOLD':
                        print(f"   🟢 {alert.action} {alert.symbol} at ${alert.price:.2f}")
                        print(f"      Reason: {alert.reason}")
                    else:
                        print(f"   ⚪ {alert.action} {alert.symbol} at ${alert.price:.2f}")
                        print(f"      Reason: {alert.reason}")
            else:
                # Single signal
                alert = alerts[0]
                if alert.action != 'HOLD':
                    print(f"🚨 TECL TRADING SIGNAL: {alert.action} {alert.symbol} at ${alert.price:.2f}")
                    print(f"   Reason: {alert.reason}")
                else:
                    print(f"📊 TECL Analysis: {alert.action} {alert.symbol} at ${alert.price:.2f}")
                    print(f"   Reason: {alert.reason}")
            
            # Print technical indicator values for key symbols
            if alerts and hasattr(self.strategy, 'calculate_indicators'):
                market_data = self.strategy.get_market_data()
                indicators = self.strategy.calculate_indicators(market_data)
                logging.info("\n🔬 Technical Indicators Used for TECL Signal Generation:")
                for symbol in ['SPY', 'XLK', 'KMLM', 'TECL']:
                    if symbol in indicators:
                        logging.info(f"  {symbol}: RSI(10)={indicators[symbol].get('rsi_10'):.1f}, RSI(20)={indicators[symbol].get('rsi_20'):.1f}")
            
            return alerts[0]  # Return first alert for compatibility
        else:
            print("❌ Unable to generate TECL strategy signal")
            return None
    
    def run_continuous(self, interval_minutes=15, max_errors=10):
        """Run analysis continuously with error limits"""
        import time
        
        logging.info(f"Starting continuous TECL strategy analysis (every {interval_minutes} minutes)")
        error_count = 0
        
        while True:
            try:
                self.run_once()
                error_count = 0  # Reset error count on success
                time.sleep(interval_minutes * 60)
            except KeyboardInterrupt:
                logging.info("Stopping TECL bot...")
                break
            except Exception as e:
                error_count += 1
                logging.error(f"Error in continuous run ({error_count}/{max_errors}): {e}")
                
                if error_count >= max_errors:
                    logging.error(f"Too many consecutive errors ({max_errors}), stopping...")
                    break
                    
                # Exponential backoff for errors
                backoff_time = min(60 * (2 ** min(error_count, 5)), 300)  # Max 5 minutes
                logging.info(f"Backing off for {backoff_time} seconds...")
                time.sleep(backoff_time)
    
    def get_current_portfolio_allocation(self):
        """Get current TECL portfolio allocation for display purposes"""
        # Get market data and indicators
        market_data = self.strategy.get_market_data()
        if not market_data:
            return None
        
        indicators = self.strategy.calculate_indicators(market_data)
        if not indicators:
            return None
        
        # Get strategy recommendation
        symbol, action, reason = self.strategy.evaluate_tecl_strategy(indicators, market_data)
        
        # Return current allocation with prices
        if isinstance(symbol, dict):
            # Multi-asset allocation
            portfolio_with_prices = {}
            for asset_symbol, weight in symbol.items():
                if asset_symbol in indicators:
                    current_price = indicators[asset_symbol]['current_price']
                    portfolio_with_prices[asset_symbol] = {
                        'weight': weight,
                        'current_price': current_price,
                        'market_value': 10000 * weight,  # Assuming $10k portfolio
                        'shares': (10000 * weight) / current_price if current_price > 0 else 0
                    }
            return portfolio_with_prices
        elif symbol in indicators:
            # Single asset allocation
            current_price = indicators[symbol]['current_price']
            return {
                symbol: {
                    'weight': 1.0,
                    'current_price': current_price,
                    'market_value': 10000,
                    'shares': 10000 / current_price if current_price > 0 else 0
                }
            }
        
        return None
