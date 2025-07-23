#!/usr/bin/env python3
"""
Nuclear Energy Trading Alert Bot
Based on the "Nuclear Energy with Feaver Frontrunner V5" Composer.trade strategy

This strategy focuses on:
1. Market regime detection via RSI levels
2. Volatility protection with UVXY
3. Nuclear energy stocks in bull markets
4. Tech/bond dynamics in bear markets
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
from .indicators import TechnicalIndicators
from .config import Config

warnings.filterwarnings('ignore')

# Load configuration
config = Config()
logging_config = config['logging']

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(logging_config['nuclear_alerts_log']),
        logging.StreamHandler()
    ]
)


# Import Alert from alert_service
from .alert_service import Alert





# Import UnifiedDataProvider from the new module
from .data_provider import UnifiedDataProvider

from enum import Enum, auto

# ActionType enum for clarity and safety
class ActionType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

class NuclearStrategyEngine:
    def get_nuclear_portfolio(self, indicators, market_data=None, top_n=3):
        """
        Get nuclear energy portfolio with top N stocks and their allocations using inverse volatility weighting.
        Returns a dict: {symbol: {weight, performance}}
        """
        nuclear_performance = []
        for symbol in self.nuclear_symbols:
            if symbol in indicators:
                perf = indicators[symbol].get('ma_return_90', 0)
                nuclear_performance.append((symbol, perf))
        # Sort by performance, descending
        nuclear_performance.sort(key=lambda x: x[1], reverse=True)
        top_stocks = nuclear_performance[:top_n]
        # If not enough, pad with available
        if len(top_stocks) < top_n:
            available = [s for s in self.nuclear_symbols if s in indicators]
            for s in available:
                if s not in [x[0] for x in top_stocks]:
                    top_stocks.append((s, 0.0))
                if len(top_stocks) >= top_n:
                    break
        # Calculate 90-day volatility for each stock
        volatilities = []
        for symbol, _ in top_stocks:
            if market_data and symbol in market_data:
                close = market_data[symbol]['Close']
                returns = close.pct_change().dropna()
                if len(returns) >= 90:
                    vol = returns[-90:].std() * np.sqrt(252)
                    # Ensure vol is a scalar, not a Series
                    if hasattr(vol, 'item'):
                        vol = vol.item()
                    vol = float(vol) if pd.notna(vol) else 0.3
                else:
                    vol = 0.3
            else:
                vol = 0.3  # fallback
            volatilities.append(max(vol, 0.01))
        # Inverse volatility weighting
        inv_vols = [1/v for v in volatilities]
        total_inv = sum(inv_vols)
        portfolio = {}
        for i, (symbol, perf) in enumerate(top_stocks):
            weight = inv_vols[i] / total_inv if total_inv > 0 else 1.0/top_n
            portfolio[symbol] = {'weight': weight, 'performance': perf}
        return portfolio

    def get_best_nuclear_stocks(self, indicators, top_n=3):
        """Get top performing nuclear stocks based on 90-day moving average return."""
        portfolio = self.get_nuclear_portfolio(indicators, top_n=top_n)
        return list(portfolio.keys())[:top_n]
    """Nuclear Energy Strategy Engine"""

    def __init__(self, data_provider=None):
        self.data_provider = data_provider or UnifiedDataProvider(paper_trading=True)
        self.indicators = TechnicalIndicators()

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
        from .strategy_engine import (
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
            if symbol in indicators and indicators[symbol]['rsi_10'] > 79:
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
            result = BullMarketStrategy(self.get_nuclear_portfolio).recommend(indicators, market_data)
            if result:
                return result
        else:
            result = BearMarketStrategy(self._bear_subgroup_1, self._bear_subgroup_2, self._combine_bear_strategies_with_inverse_volatility).recommend(indicators)
            if result:
                return result
        
        # Fallback if no strategy returns a result
        return 'SPY', ActionType.HOLD.value, "No clear signal, holding cash equivalent"


    def _bear_subgroup_1(self, indicators):
        if 'PSQ' in indicators and indicators['PSQ']['rsi_10'] < 35:
            return 'SQQQ', ActionType.BUY.value, "PSQ oversold, aggressive short position (Bear 1)"
        if 'QQQ' in indicators and indicators['QQQ']['cum_return_60'] < -10:
            if self._bonds_stronger_than_psq(indicators):
                return 'TQQQ', ActionType.BUY.value, "Bonds strong vs PSQ, contrarian TQQQ buy (Bear 1)"
            return 'PSQ', ActionType.BUY.value, "QQQ weak, defensive short position (Bear 1)"
        if 'TQQQ' in indicators:
            tqqq_price = indicators['TQQQ']['current_price']
            tqqq_ma_20 = indicators['TQQQ']['ma_20']
            if tqqq_price > tqqq_ma_20:
                if self._bonds_stronger_than_psq(indicators):
                    return 'TQQQ', ActionType.BUY.value, "TQQQ trending up, bonds strong (Bear 1)"
                return 'SQQQ', ActionType.BUY.value, "TQQQ up but bonds weak, short position (Bear 1)"
            else:
                if self._ief_stronger_than_psq(indicators):
                    return 'SQQQ', ActionType.BUY.value, "TQQQ weak, IEF strong, short position (Bear 1)"
                elif self._bonds_stronger_than_psq(indicators):
                    return 'QQQ', ActionType.BUY.value, "TQQQ weak but bonds strong, neutral QQQ (Bear 1)"
                return 'SQQQ', ActionType.BUY.value, "TQQQ weak, bonds weak, short position (Bear 1)"
        return 'SQQQ', ActionType.BUY.value, "Bear market conditions, short tech (Bear 1)"

    def _bear_subgroup_2(self, indicators):
        if 'PSQ' in indicators and indicators['PSQ']['rsi_10'] < 35:
            return 'SQQQ', ActionType.BUY.value, "PSQ oversold, aggressive short position (Bear 2)"
        if 'TQQQ' in indicators:
            tqqq_price = indicators['TQQQ']['current_price']
            tqqq_ma_20 = indicators['TQQQ']['ma_20']
            if tqqq_price > tqqq_ma_20:
                if self._bonds_stronger_than_psq(indicators):
                    return 'TQQQ', ActionType.BUY.value, "TQQQ trending up, bonds strong (Bear 2)"
                return 'SQQQ', ActionType.BUY.value, "TQQQ up but bonds weak, short position (Bear 2)"
            else:
                if self._bonds_stronger_than_psq(indicators):
                    return 'QQQ', ActionType.BUY.value, "TQQQ weak but bonds strong, neutral QQQ (Bear 2)"
                return 'SQQQ', ActionType.BUY.value, "TQQQ weak, bonds weak, short position (Bear 2)"
        return 'SQQQ', ActionType.BUY.value, "Bear market conditions, short tech (Bear 2)"
    
    def _bonds_stronger_than_psq(self, indicators):
        """Check if TLT RSI(20) > PSQ RSI(20)"""
        if 'TLT' in indicators and 'PSQ' in indicators:
            tlt_rsi_20 = indicators['TLT']['rsi_20']
            psq_rsi_20 = indicators['PSQ']['rsi_20']
            return tlt_rsi_20 > psq_rsi_20
        return False
    
    def _ief_stronger_than_psq(self, indicators):
        """Check if IEF RSI(10) > PSQ RSI(20)"""
        if 'IEF' in indicators and 'PSQ' in indicators:
            ief_rsi_10 = indicators['IEF']['rsi_10']
            psq_rsi_20 = indicators['PSQ']['rsi_20']
            return ief_rsi_10 > psq_rsi_20
        return False
    
    def _combine_bear_strategies_with_inverse_volatility(self, bear1_symbol, bear2_symbol, indicators):
        """
        Combine two bear strategy symbols using inverse volatility weighting (14-day window)
        Returns portfolio allocation dictionary or None if calculation fails
        """
        try:
            # Get 14-day volatility for both symbols
            vol1 = self._get_14_day_volatility(bear1_symbol, indicators)
            vol2 = self._get_14_day_volatility(bear2_symbol, indicators)
            
            if vol1 is None or vol2 is None or vol1 <= 0 or vol2 <= 0:
                return None
            
            # Calculate inverse volatility weights
            inv_vol1 = 1.0 / vol1
            inv_vol2 = 1.0 / vol2
            total_inv_vol = inv_vol1 + inv_vol2
            
            # Normalize to get portfolio weights
            weight1 = inv_vol1 / total_inv_vol
            weight2 = inv_vol2 / total_inv_vol
            
            # Return portfolio allocation
            portfolio = {}
            if weight1 > 0.01:  # Only include if weight > 1%
                portfolio[bear1_symbol] = {'weight': weight1, 'performance': 0.0}
            if weight2 > 0.01:  # Only include if weight > 1%
                portfolio[bear2_symbol] = {'weight': weight2, 'performance': 0.0}
            
            return portfolio if portfolio else None
            
        except Exception as e:
            # If anything goes wrong, fall back to None
            return None
    
    def _get_14_day_volatility(self, symbol, indicators):
        """
        Calculate 14-day volatility for a symbol
        Returns volatility or None if not available
        """
        try:
            if symbol in indicators:
                # Use historical data if available
                if 'price_history' in indicators[symbol] and len(indicators[symbol]['price_history']) >= 14:
                    prices = indicators[symbol]['price_history'][-14:]  # Last 14 days
                    returns = []
                    for i in range(1, len(prices)):
                        daily_return = (prices[i] - prices[i-1]) / prices[i-1]
                        returns.append(daily_return)
                    
                    if len(returns) >= 10:  # Need at least 10 daily returns
                        import numpy as np
                        volatility = np.std(returns) * np.sqrt(252)  # Annualized volatility
                        return max(volatility, 0.01)  # Minimum volatility floor
                
                # Fallback: use RSI-based volatility estimate if price history not available
                if 'rsi_10' in indicators[symbol]:
                    rsi = indicators[symbol]['rsi_10']
                    # RSI-based volatility estimate (higher RSI variability = higher volatility)
                    rsi_volatility = abs(50 - rsi) / 100.0  # Normalize RSI deviation
                    estimated_vol = 0.2 + (rsi_volatility * 0.3)  # 20-50% range
                    return estimated_vol
                
                # Last resort: use fixed volatility estimates based on symbol type
                volatility_estimates = {
                    'SQQQ': 0.8,  # High volatility leveraged short ETF
                    'TQQQ': 0.7,  # High volatility leveraged long ETF
                    'QQQ': 0.25,  # Medium volatility index ETF
                    'PSQ': 0.4,   # Medium-high volatility short ETF
                    'TLT': 0.2,   # Lower volatility bond ETF
                    'IEF': 0.15   # Low volatility bond ETF
                }
                return volatility_estimates.get(symbol, 0.3)  # Default 30% volatility
            
            return None
            
        except Exception as e:
            return None

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
            print(f"Error converting price to scalar: {e}")
            return None
        
    def load_config(self):
        """Load configuration"""
        try:
            with open('alert_config.json', 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            self.config = {
                "alerts": {
                    "cooldown_minutes": 30
                }
            }
    
    def handle_nuclear_portfolio_signal(self, symbol, action, reason, indicators, market_data=None):
        """Delegate alert creation to alert_service.create_alerts_from_signal"""
        from .alert_service import create_alerts_from_signal
        return create_alerts_from_signal(
            symbol, action, reason, indicators, market_data,
            self.strategy.data_provider, self._ensure_scalar_price, self.strategy
        )
    
    def run_analysis(self):
        """Run complete strategy analysis"""
        logging.info("Starting Nuclear Energy strategy analysis...")
        
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
        from .alert_service import log_alert_to_file
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
                print(f"🚨 NUCLEAR PORTFOLIO SIGNAL: {len(alerts)} stocks allocated")
                print(f"\n� NUCLEAR PORTFOLIO ALLOCATION:")
                for alert in alerts:
                    if alert.action != 'HOLD':
                        print(f"   🟢 {alert.action} {alert.symbol} at ${alert.price:.2f}")
                        print(f"      Reason: {alert.reason}")
                    else:
                        print(f"   ⚪ {alert.action} {alert.symbol} at ${alert.price:.2f}")
                        print(f"      Reason: {alert.reason}")
                        
                # Show portfolio allocation details
                portfolio = self.get_current_portfolio_allocation()
                if portfolio:
                    print(f"\n� PORTFOLIO DETAILS:")
                    for symbol, data in portfolio.items():
                        print(f"   {symbol}: {data['weight']:.1%}")
            else:
                # Single signal
                alert = alerts[0]
                if alert.action != 'HOLD':
                    print(f"🚨 NUCLEAR TRADING SIGNAL: {alert.action} {alert.symbol} at ${alert.price:.2f}")
                    print(f"   Reason: {alert.reason}")
                else:
                    print(f"📊 Nuclear Analysis: {alert.action} {alert.symbol} at ${alert.price:.2f}")
                    print(f"   Reason: {alert.reason}")
            
            # Print technical indicator values for key symbols
            if alerts and hasattr(self.strategy, 'calculate_indicators'):
                market_data = self.strategy.get_market_data()
                indicators = self.strategy.calculate_indicators(market_data)
                print("\n🔬 Technical Indicators Used for Signal Generation:")
                for symbol in ['IOO', 'SPY', 'TQQQ', 'VTV', 'XLF']:
                    if symbol in indicators:
                        print(f"  {symbol}: RSI(10)={indicators[symbol].get('rsi_10')}, RSI(20)={indicators[symbol].get('rsi_20')}")
            
            return alerts[0]  # Return first alert for compatibility
        else:
            print("❌ Unable to generate nuclear energy signal")
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
                nuclear_portfolio = self.strategy.get_nuclear_portfolio(indicators, market_data)
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

