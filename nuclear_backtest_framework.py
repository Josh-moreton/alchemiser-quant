#!/usr/bin/env python3
"""
Nuclear Energy Trading Bot - Robust Backtesting Framework
Step 1: Enhanced Data Provider with Point-in-Time Access
"""

import yfinance as yf
import pandas as pd
import numpy as np
import datetime as dt
from datetime import timedelta
import logging
from typing import Dict, List, Optional, Tuple
import sys
import os

# Import the original strategy components
try:
    from nuclear_trading_bot import NuclearStrategyEngine, TechnicalIndicators
except ImportError:
    print("Error: Could not import nuclear_trading_bot. Make sure it's in the same directory.")
    sys.exit(1)

class BacktestDataProvider:
    """
    Enhanced data provider that ensures point-in-time data access
    Prevents look-ahead bias by only providing data available at decision time
    """
    
    def __init__(self, start_date: str, end_date: str):
        self.start_date = start_date
        self.end_date = end_date
        self.cache = {}
        self.logger = logging.getLogger(__name__)
        
    def download_all_data(self, symbols: List[str]) -> Dict[str, pd.DataFrame]:
        """Download all historical data for symbols"""
        self.logger.info(f"Downloading complete dataset for {len(symbols)} symbols...")
        
        all_data = {}
        failed_symbols = []
        
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                
                # Download daily data
                daily_data = ticker.history(
                    start=self.start_date, 
                    end=self.end_date, 
                    interval='1d',
                    auto_adjust=True
                )
                
                if not daily_data.empty:
                    # Normalize timezone
                    if daily_data.index.tz is not None:
                        daily_data.index = daily_data.index.tz_localize(None)
                    
                    all_data[symbol] = daily_data
                    self.logger.info(f"Downloaded {symbol}: {len(daily_data)} daily records")
                else:
                    failed_symbols.append(symbol)
                    
            except Exception as e:
                self.logger.error(f"Failed to download {symbol}: {e}")
                failed_symbols.append(symbol)
        
        if failed_symbols:
            self.logger.warning(f"Failed to download: {failed_symbols}")
        
        self.all_data = all_data
        return all_data
    
    def get_data_up_to_date(self, symbol: str, as_of_date: pd.Timestamp) -> pd.DataFrame:
        """
        Get historical data for symbol up to (but not including) as_of_date
        This prevents look-ahead bias
        """
        if symbol not in self.all_data:
            return pd.DataFrame()
        
        # Normalize as_of_date
        if hasattr(as_of_date, 'tz_localize'):
            as_of_date = as_of_date.tz_localize(None) if as_of_date.tz is not None else as_of_date
        else:
            as_of_date = pd.Timestamp(as_of_date).tz_localize(None)
        
        # Get data strictly before as_of_date
        symbol_data = self.all_data[symbol]
        historical_data = symbol_data[symbol_data.index < as_of_date]
        
        return historical_data
    
    def get_price_at_time(self, symbol: str, date: pd.Timestamp, price_type: str = 'Close') -> Optional[float]:
        """Get specific price at exact date"""
        data = self.get_data_up_to_date(symbol, date + pd.Timedelta(days=1))
        
        if data.empty:
            return None
        
        # Find the exact date or last available date
        target_date = date.normalize()
        if target_date in data.index:
            return float(data.loc[target_date, price_type])
        elif not data.empty:
            return float(data.iloc[-1][price_type])
        
        return None

class BacktestNuclearStrategy:
    """
    Wrapper around the original NuclearStrategyEngine for backtesting
    Ensures point-in-time evaluation without look-ahead bias
    """
    
    def __init__(self, data_provider: BacktestDataProvider):
        self.data_provider = data_provider
        self.original_strategy = NuclearStrategyEngine()
        self.indicators_calc = TechnicalIndicators()
        self.logger = logging.getLogger(__name__)
        
        # Get all required symbols
        self.all_symbols = self.original_strategy.all_symbols
        
    def calculate_indicators_at_time(self, as_of_date: pd.Timestamp) -> Dict:
        """
        Calculate all indicators as of specific date using only historical data
        This replicates the original strategy's indicator calculation
        """
        indicators = {}
        market_data = {}
        
        for symbol in self.all_symbols:
            # Get historical data up to (but not including) as_of_date
            hist_data = self.data_provider.get_data_up_to_date(symbol, as_of_date)
            
            if hist_data.empty or len(hist_data) < 200:  # Need sufficient data for 200-day MA
                continue
            
            market_data[symbol] = hist_data
            close = hist_data['Close']
            
            try:
                indicators[symbol] = {
                    'rsi_10': self._safe_indicator(close, self.indicators_calc.rsi, 10),
                    'rsi_20': self._safe_indicator(close, self.indicators_calc.rsi, 20),
                    'ma_200': self._safe_indicator(close, self.indicators_calc.moving_average, 200),
                    'ma_20': self._safe_indicator(close, self.indicators_calc.moving_average, 20),
                    'ma_return_90': self._safe_indicator(close, self.indicators_calc.moving_average_return, 90),
                    'cum_return_60': self._safe_indicator(close, self.indicators_calc.cumulative_return, 60),
                    'current_price': float(close.iloc[-1]),
                    'price_history': close.tail(90).values.tolist() if len(close) >= 90 else close.values.tolist()
                }
            except Exception as e:
                self.logger.warning(f"Failed to calculate indicators for {symbol} on {as_of_date}: {e}")
                continue
        
        return indicators, market_data
    
    def _safe_indicator(self, data, indicator_func, *args, **kwargs):
        """Safely calculate indicator with fallback"""
        try:
            result = indicator_func(data, *args, **kwargs)
            if hasattr(result, 'iloc') and len(result) > 0:
                value = float(result.iloc[-1])
                return value if not pd.isna(value) else 50.0
            return 50.0
        except:
            return 50.0
    
    def evaluate_strategy_at_time(self, as_of_date: pd.Timestamp) -> Tuple[str, str, str, Dict, Dict]:
        """
        Evaluate the nuclear strategy at a specific point in time
        Returns: (signal, action, reason, indicators, market_data)
        """
        # Calculate indicators using only historical data
        indicators, market_data = self.calculate_indicators_at_time(as_of_date)
        
        if not indicators:
            return 'SPY', 'HOLD', "Insufficient data", {}, {}
        
        # Use original strategy logic
        signal, action, reason = self.original_strategy.evaluate_nuclear_strategy(indicators, market_data)
        
        return signal, action, reason, indicators, market_data

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
        nuclear_symbols = self.strategy.original_strategy.nuclear_symbols
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
    signal, action, reason, indicators, market_data = strategy.evaluate_strategy_at_time(test_date)
    
    print(f"Strategy Signal on {test_date.date()}: {action} {signal}")
    print(f"Reason: {reason}")
    
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
