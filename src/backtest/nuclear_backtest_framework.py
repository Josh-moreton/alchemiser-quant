#!/usr/bin/env python3
"""
Nuclear Energy Trading Bot - Robust Backtesting Framework
Enhanced to use Alpaca Market Data API instead of yfinance
"""

import pandas as pd
import numpy as np
import datetime as dt
from datetime import timedelta
import logging
from typing import Dict, List, Optional, Tuple, Union
import sys
import os

# Import Alpaca data provider
from .alpaca_data_provider import AlpacaBacktestDataProvider

# Import the original strategy components
try:
    from ..core.nuclear_trading_bot import NuclearStrategyEngine, TechnicalIndicators
except ImportError:
    try:
        # Fallback for direct execution
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))
        from nuclear_trading_bot import NuclearStrategyEngine, TechnicalIndicators
    except ImportError:
        print("Error: Could not import nuclear_trading_bot. Make sure it's in the src/core directory.")
        sys.exit(1)

# Alias for backward compatibility - using Alpaca data provider
BacktestDataProvider = AlpacaBacktestDataProvider

class BacktestNuclearStrategy:
    """
    Wrapper around the original NuclearStrategyEngine for backtesting
    Ensures point-in-time evaluation without look-ahead bias
    Now works with Alpaca Market Data API
    """
    
    def __init__(self, data_provider: Union[AlpacaBacktestDataProvider, 'BacktestDataProvider']):
        self.data_provider = data_provider
        # Create a NEW strategy engine 
        self.strategy_engine = NuclearStrategyEngine()
        # We'll replace the data provider dynamically per evaluation
        self.backtest_wrapper = None
        self.indicators_calc = TechnicalIndicators()
        self.logger = logging.getLogger(__name__)
        
        # Get all required symbols
        self.all_symbols = self.strategy_engine.all_symbols
        
    def _create_backtest_data_provider(self):
        """Create a backtest-compatible data provider that mimics the live one"""
        
        class BacktestDataProviderWrapper:
            """Wraps our backtest data provider to look like the live DataProvider"""
            
            def __init__(self, backtest_provider, current_date):
                self.backtest_provider = backtest_provider
                self.current_date = current_date
                self.cache = {}
                self.cache_duration = 300
            
            def get_data(self, symbol, period="1y"):
                """Get historical data up to current_date (mimics live behavior)"""
                return self.backtest_provider.get_data_up_to_date(symbol, self.current_date)
            
            def get_current_price(self, symbol):
                """Get 'current' price as of the backtest date"""
                data = self.get_data(symbol, period="5d")
                if not data.empty:
                    return float(data['Close'].iloc[-1])
                return 0.0
        
        wrapper = BacktestDataProviderWrapper(self.data_provider, pd.Timestamp('2024-11-01'))
        return wrapper
    
    def evaluate_strategy_at_time(self, as_of_date: pd.Timestamp) -> Tuple[str, str, str, Dict, Dict]:
        """
        Evaluate the nuclear strategy at a specific point in time
        Returns: (signal, action, reason, indicators, market_data)
        """
        # Create a fresh wrapper for this evaluation date
        self.backtest_wrapper = self._create_backtest_data_provider()
        self.backtest_wrapper.current_date = as_of_date
        
        # Temporarily replace the data provider (ignore type checker)
        original_provider = self.strategy_engine.data_provider
        self.strategy_engine.data_provider = self.backtest_wrapper  # type: ignore
        
        try:
            # Use the EXACT same method as the live bot
            market_data = self.strategy_engine.get_market_data()
            if not market_data:
                return 'SPY', 'HOLD', "No market data available", {}, {}
            
            # Calculate indicators using the EXACT same method as the live bot
            indicators = self.strategy_engine.calculate_indicators(market_data)
            if not indicators:
                return 'SPY', 'HOLD', "No indicators calculated", {}, {}
            
            # Add price_history to indicators for portfolio building
            for symbol in indicators:
                if symbol in market_data and not market_data[symbol].empty:
                    indicators[symbol]['price_history'] = market_data[symbol]['Close'].tolist()
            
            # Use the EXACT same strategy evaluation as the live bot
            signal, action, reason = self.strategy_engine.evaluate_nuclear_strategy(indicators, market_data)
            
            return signal, action, reason, indicators, market_data
            
        finally:
            # Restore original provider
            self.strategy_engine.data_provider = original_provider

class SignalTracker:
    """
    Tracks signal changes over time to identify when portfolio rebalancing should occur
    """
    
    def __init__(self):
        self.signal_history = []
        self.logger = logging.getLogger(__name__)
    
    def add_signal(self, date: pd.Timestamp, signal: str, action: str, reason: str):
        """Add new signal to history"""
        self.signal_history.append({
            'date': date,
            'signal': signal,
            'action': action,
            'reason': reason
        })
    
    def get_signal_changes(self) -> List[Dict]:
        """Get list of dates when signals changed"""
        if len(self.signal_history) < 2:
            return []
        
        changes = []
        prev_signal = self.signal_history[0]
        
        for i in range(1, len(self.signal_history)):
            curr_signal = self.signal_history[i]
            
            # Check if signal actually changed
            if (curr_signal['signal'] != prev_signal['signal'] or 
                curr_signal['action'] != prev_signal['action']):
                
                changes.append({
                    'date': curr_signal['date'],
                    'from_signal': prev_signal['signal'],
                    'to_signal': curr_signal['signal'],
                    'from_action': prev_signal['action'],
                    'to_action': curr_signal['action'],
                    'reason': curr_signal['reason']
                })
            
            prev_signal = curr_signal
        
        return changes
    
    def get_current_signal(self, as_of_date: pd.Timestamp) -> Optional[Dict]:
        """Get the most recent signal as of a specific date"""
        valid_signals = [s for s in self.signal_history if s['date'] <= as_of_date]
        
        if valid_signals:
            return valid_signals[-1]
        return None

class PortfolioBuilder:
    """
    Converts strategy signals into concrete portfolio allocations
    Handles the complex portfolio logic from the original strategy
    """
    
    def __init__(self, strategy: BacktestNuclearStrategy):
        self.strategy = strategy
        self.logger = logging.getLogger(__name__)
    
    def build_target_portfolio(self, signal: str, action: str, reason: str, 
                             indicators: Dict, portfolio_value: float) -> Dict[str, float]:
        """
        Convert strategy signal into target portfolio allocation (symbol -> shares)
        """
        target_positions = {}
        
        if signal == 'NUCLEAR_PORTFOLIO' and action == 'BUY':
            target_positions = self._build_nuclear_portfolio(indicators, portfolio_value)
            
        elif signal == 'UVXY_BTAL_PORTFOLIO' and action == 'BUY':
            target_positions = self._build_uvxy_btal_portfolio(indicators, portfolio_value)
            
        elif signal == 'BEAR_PORTFOLIO' and action == 'BUY':
            target_positions = self._build_bear_portfolio(reason, indicators, portfolio_value)
            
        elif action == 'BUY' and signal in indicators:
            # Single stock signal
            current_price = indicators[signal]['current_price']
            if current_price > 0:
                target_positions[signal] = portfolio_value / current_price
                
        elif action == 'HOLD':
            # Stay in cash or maintain current positions
            pass
        
        return target_positions
    
    def _build_nuclear_portfolio(self, indicators: Dict, portfolio_value: float) -> Dict[str, float]:
        """Build nuclear energy portfolio with inverse volatility weighting"""
        nuclear_symbols = self.strategy.strategy_engine.nuclear_symbols
        nuclear_performance = []
        
        # Get performance for available nuclear stocks
        for symbol in nuclear_symbols:
            if symbol in indicators:
                performance = indicators[symbol]['ma_return_90']
                nuclear_performance.append((symbol, performance))
        
        # Sort by performance and get top 3
        nuclear_performance.sort(key=lambda x: x[1], reverse=True)
        top_3_stocks = nuclear_performance[:3]
        
        if not top_3_stocks:
            return {}
        
        # Calculate inverse volatility weights (simplified)
        portfolio = {}
        total_weight = 0
        
        for symbol, performance in top_3_stocks:
            if symbol in indicators:
                # Use price history for volatility calculation
                price_history = indicators[symbol]['price_history']
                if len(price_history) >= 14:
                    returns = []
                    for i in range(1, min(91, len(price_history))):
                        ret = (price_history[i] - price_history[i-1]) / price_history[i-1]
                        returns.append(ret)
                    
                    if returns:
                        volatility = np.std(returns) * np.sqrt(252)
                        inv_vol = 1.0 / max(volatility, 0.01)  # Avoid division by zero
                        total_weight += inv_vol
                        portfolio[symbol] = inv_vol
        
        # Normalize weights and convert to shares
        target_positions = {}
        if total_weight > 0:
            for symbol, weight in portfolio.items():
                normalized_weight = weight / total_weight
                current_price = indicators[symbol]['current_price']
                if current_price > 0:
                    target_value = portfolio_value * normalized_weight
                    target_positions[symbol] = target_value / current_price
        
        return target_positions
    
    def _build_uvxy_btal_portfolio(self, indicators: Dict, portfolio_value: float) -> Dict[str, float]:
        """Build UVXY 75% + BTAL 25% portfolio"""
        target_positions = {}
        
        allocations = [('UVXY', 0.75), ('BTAL', 0.25)]
        
        for symbol, weight in allocations:
            if symbol in indicators:
                current_price = indicators[symbol]['current_price']
                if current_price > 0:
                    target_value = portfolio_value * weight
                    target_positions[symbol] = target_value / current_price
        
        return target_positions
    
    def _build_bear_portfolio(self, reason: str, indicators: Dict, portfolio_value: float) -> Dict[str, float]:
        """Build bear market portfolio from reason string"""
        import re
        target_positions = {}
        
        # Extract portfolio allocation from reason string
        portfolio_matches = re.findall(r'(\w+) \((\d+\.?\d*)%\)', reason)
        
        for symbol, weight_str in portfolio_matches:
            if symbol in indicators:
                weight = float(weight_str) / 100.0
                current_price = indicators[symbol]['current_price']
                if current_price > 0:
                    target_value = portfolio_value * weight
                    target_positions[symbol] = target_value / current_price
        
        return target_positions

# Example usage and testing
def test_backtest_framework():
    """Test the backtesting framework components"""
    
    # Setup
    start_date = '2024-10-01'
    end_date = '2024-12-31'
    
    # Initialize components
    data_provider = BacktestDataProvider(start_date, end_date)
    strategy = BacktestNuclearStrategy(data_provider)
    signal_tracker = SignalTracker()
    portfolio_builder = PortfolioBuilder(strategy)
    
    # Download data
    all_data = data_provider.download_all_data(strategy.all_symbols)
    print(f"Downloaded data for {len(all_data)} symbols")
    
    # Test strategy evaluation at specific date
    test_date = pd.Timestamp('2024-11-01')
    
    # Debug: Check available data for a key symbol
    spy_data = data_provider.get_data_up_to_date('SPY', test_date)
    print(f"SPY data available up to {test_date.date()}: {len(spy_data)} records")
    if not spy_data.empty:
        print(f"SPY data range: {spy_data.index[0].date()} to {spy_data.index[-1].date()}")
    
    signal, action, reason, indicators, market_data = strategy.evaluate_strategy_at_time(test_date)
    
    print(f"Strategy Signal on {test_date.date()}: {action} {signal}")
    print(f"Reason: {reason}")
    print(f"Indicators calculated for {len(indicators)} symbols")
    
    # Test portfolio building
    if indicators:
        target_portfolio = portfolio_builder.build_target_portfolio(
            signal, action, reason, indicators, 100000
        )
        
        print(f"Target Portfolio:")
        for symbol, shares in target_portfolio.items():
            if shares > 0:
                price = indicators[symbol]['current_price']
                value = shares * price
                print(f"  {symbol}: {shares:.2f} shares @ ${price:.2f} = ${value:,.0f}")

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Run test
    test_backtest_framework()
