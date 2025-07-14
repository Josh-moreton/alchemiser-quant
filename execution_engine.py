#!/usr/bin/env python3
"""
Execution Engine - Phase 3 of Nuclear Backtest Implementation
Handles different execution timing strategies and transaction costs
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
from nuclear_backtest_framework import BacktestDataProvider, BacktestNuclearStrategy, PortfolioBuilder

class ExecutionEngine:
    """
    Handles portfolio execution with different timing strategies and transaction costs
    """
    
    def __init__(self, strategy: BacktestNuclearStrategy, initial_capital: float = 100000):
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.current_positions = {}  # symbol -> shares
        self.transaction_log = []
        self.portfolio_builder = PortfolioBuilder(strategy)
        self.logger = logging.getLogger(__name__)
        
        # Transaction cost parameters
        self.commission_per_trade = 0.0  # Most brokers are commission-free now
        self.spread_cost = 0.001  # 0.1% spread cost
        self.slippage = 0.0005    # 0.05% slippage
    
    def get_portfolio_value(self, as_of_date: pd.Timestamp) -> float:
        """Calculate current portfolio value including cash and positions"""
        total_value = self.current_capital
        
        for symbol, shares in self.current_positions.items():
            if shares > 0:
                price = self.strategy.data_provider.get_price_at_time(symbol, as_of_date, 'Close')
                if price:
                    total_value += shares * price
        
        return total_value
    
    def calculate_transaction_costs(self, symbol: str, shares: float, price: float, 
                                  is_buy: bool) -> float:
        """Calculate total transaction costs for a trade"""
        notional_value = abs(shares) * price
        
        costs = self.commission_per_trade
        costs += notional_value * self.spread_cost
        costs += notional_value * self.slippage
        
        return costs
    
    def execute_market_on_open(self, target_portfolio: Dict[str, float], 
                              execution_date: pd.Timestamp) -> List[Dict]:
        """Execute trades at market open prices"""
        trades = []
        
        # Get opening prices for execution date
        opening_prices = {}
        for symbol in set(list(target_portfolio.keys()) + list(self.current_positions.keys())):
            price = self.strategy.data_provider.get_price_at_time(symbol, execution_date, 'Open')
            if price:
                opening_prices[symbol] = price
        
        # Calculate required trades
        required_trades = self._calculate_required_trades(target_portfolio, opening_prices)
        
        # Execute trades
        for symbol, shares_to_trade in required_trades.items():
            if abs(shares_to_trade) < 0.01:  # Skip tiny trades
                continue
                
            price = opening_prices[symbol]
            is_buy = shares_to_trade > 0
            
            # Calculate transaction costs
            costs = self.calculate_transaction_costs(symbol, shares_to_trade, price, is_buy)
            
            # Execute the trade
            trade_value = shares_to_trade * price
            self.current_capital -= trade_value + costs
            
            # Update positions
            if symbol in self.current_positions:
                self.current_positions[symbol] += shares_to_trade
            else:
                self.current_positions[symbol] = shares_to_trade
            
            # Remove zero positions
            if abs(self.current_positions[symbol]) < 0.01:
                del self.current_positions[symbol]
            
            # Log the trade
            trade_record = {
                'date': execution_date,
                'symbol': symbol,
                'shares': shares_to_trade,
                'price': price,
                'trade_value': trade_value,
                'costs': costs,
                'execution_type': 'market_open',
                'cash_after': self.current_capital
            }
            trades.append(trade_record)
            self.transaction_log.append(trade_record)
        
        return trades
    
    def execute_market_on_close(self, target_portfolio: Dict[str, float], 
                               execution_date: pd.Timestamp) -> List[Dict]:
        """Execute trades at market close prices"""
        trades = []
        
        # Get closing prices for execution date
        closing_prices = {}
        for symbol in set(list(target_portfolio.keys()) + list(self.current_positions.keys())):
            price = self.strategy.data_provider.get_price_at_time(symbol, execution_date, 'Close')
            if price:
                closing_prices[symbol] = price
        
        # Calculate required trades
        required_trades = self._calculate_required_trades(target_portfolio, closing_prices)
        
        # Execute trades (similar to market_on_open but with close prices)
        for symbol, shares_to_trade in required_trades.items():
            if abs(shares_to_trade) < 0.01:
                continue
                
            price = closing_prices[symbol]
            is_buy = shares_to_trade > 0
            
            costs = self.calculate_transaction_costs(symbol, shares_to_trade, price, is_buy)
            
            trade_value = shares_to_trade * price
            self.current_capital -= trade_value + costs
            
            if symbol in self.current_positions:
                self.current_positions[symbol] += shares_to_trade
            else:
                self.current_positions[symbol] = shares_to_trade
            
            if abs(self.current_positions[symbol]) < 0.01:
                del self.current_positions[symbol]
            
            trade_record = {
                'date': execution_date,
                'symbol': symbol,
                'shares': shares_to_trade,
                'price': price,
                'trade_value': trade_value,
                'costs': costs,
                'execution_type': 'market_close',
                'cash_after': self.current_capital
            }
            trades.append(trade_record)
            self.transaction_log.append(trade_record)
        
        return trades
    
    def execute_hourly_average(self, target_portfolio: Dict[str, float], 
                              execution_date: pd.Timestamp) -> List[Dict]:
        """Execute trades using average of hourly prices throughout the day"""
        trades = []
        
        # For backtesting, we'll approximate with OHLC average
        # In live trading, this would use actual hourly data
        average_prices = {}
        for symbol in set(list(target_portfolio.keys()) + list(self.current_positions.keys())):
            data = self.strategy.data_provider.get_data_up_to_date(symbol, execution_date + pd.Timedelta(days=1))
            if not data.empty and execution_date in data.index:
                day_data = data.loc[execution_date]
                # Average of OHLC as proxy for hourly average
                avg_price = (day_data['Open'] + day_data['High'] + day_data['Low'] + day_data['Close']) / 4
                average_prices[symbol] = avg_price
        
        # Calculate required trades
        required_trades = self._calculate_required_trades(target_portfolio, average_prices)
        
        # Execute trades
        for symbol, shares_to_trade in required_trades.items():
            if abs(shares_to_trade) < 0.01:
                continue
                
            price = average_prices[symbol]
            is_buy = shares_to_trade > 0
            
            # Slightly higher costs for hourly execution due to multiple trades
            costs = self.calculate_transaction_costs(symbol, shares_to_trade, price, is_buy) * 1.2
            
            trade_value = shares_to_trade * price
            self.current_capital -= trade_value + costs
            
            if symbol in self.current_positions:
                self.current_positions[symbol] += shares_to_trade
            else:
                self.current_positions[symbol] = shares_to_trade
            
            if abs(self.current_positions[symbol]) < 0.01:
                del self.current_positions[symbol]
            
            trade_record = {
                'date': execution_date,
                'symbol': symbol,
                'shares': shares_to_trade,
                'price': price,
                'trade_value': trade_value,
                'costs': costs,
                'execution_type': 'hourly_average',
                'cash_after': self.current_capital
            }
            trades.append(trade_record)
            self.transaction_log.append(trade_record)
        
        return trades
    
    def _calculate_required_trades(self, target_portfolio: Dict[str, float], 
                                 prices: Dict[str, float]) -> Dict[str, float]:
        """Calculate the difference between target and current positions"""
        required_trades = {}
        
        # Calculate current portfolio value
        current_value = self.get_portfolio_value(pd.Timestamp.now())
        
        # Symbols that need to be traded
        all_symbols = set(list(target_portfolio.keys()) + list(self.current_positions.keys()))
        
        for symbol in all_symbols:
            if symbol not in prices:
                continue
                
            target_shares = target_portfolio.get(symbol, 0.0)
            current_shares = self.current_positions.get(symbol, 0.0)
            
            shares_difference = target_shares - current_shares
            
            if abs(shares_difference) > 0.01:  # Only trade if significant difference
                required_trades[symbol] = shares_difference
        
        return required_trades
    
    def get_performance_metrics(self) -> Dict:
        """Calculate performance metrics for the execution strategy"""
        if not self.transaction_log:
            return {}
        
        # Calculate total returns
        current_value = self.get_portfolio_value(pd.Timestamp.now())
        total_return = (current_value - self.initial_capital) / self.initial_capital
        
        # Calculate transaction costs
        total_costs = sum(trade['costs'] for trade in self.transaction_log)
        cost_ratio = total_costs / self.initial_capital
        
        # Calculate trading frequency
        trade_dates = list(set(trade['date'] for trade in self.transaction_log))
        trading_frequency = len(trade_dates)
        
        # Calculate turnover
        total_volume = sum(abs(trade['trade_value']) for trade in self.transaction_log)
        turnover_ratio = total_volume / self.initial_capital
        
        return {
            'total_return': total_return,
            'total_costs': total_costs,
            'cost_ratio': cost_ratio,
            'trading_frequency': trading_frequency,
            'turnover_ratio': turnover_ratio,
            'current_value': current_value,
            'cash_position': self.current_capital,
            'number_of_trades': len(self.transaction_log)
        }

class BacktestRunner:
    """
    Runs complete backtests with different execution strategies
    """
    
    def __init__(self, start_date: str, end_date: str, initial_capital: float = 100000):
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.logger = logging.getLogger(__name__)
    
    def run_backtest(self, execution_type: str = 'market_close') -> Dict:
        """
        Run a complete backtest with specified execution strategy
        
        execution_type options:
        - 'market_open': Execute at next day's opening price
        - 'market_close': Execute at signal day's closing price  
        - 'hourly_average': Execute at average price throughout the day
        """
        
        # Initialize components
        data_provider = BacktestDataProvider(self.start_date, self.end_date)
        strategy = BacktestNuclearStrategy(data_provider)
        execution_engine = ExecutionEngine(strategy, self.initial_capital)
        
        # Download data
        all_data = data_provider.download_all_data(strategy.all_symbols)
        self.logger.info(f"Downloaded data for {len(all_data)} symbols")
        
        # Get trading days
        spy_data = all_data['SPY']
        start_dt = pd.Timestamp(self.start_date)
        end_dt = pd.Timestamp(self.end_date)
        trading_days = spy_data.index[(spy_data.index >= start_dt) & (spy_data.index <= end_dt)]
        
        # Track portfolio value over time
        portfolio_history = []
        signal_history = []
        
        self.logger.info(f"Running backtest for {len(trading_days)} trading days")
        
        for i, trade_date in enumerate(trading_days):
            try:
                # Evaluate strategy
                signal, action, reason, indicators, market_data = strategy.evaluate_strategy_at_time(trade_date)
                
                # Build target portfolio
                current_portfolio_value = execution_engine.get_portfolio_value(trade_date)
                target_portfolio = execution_engine.portfolio_builder.build_target_portfolio(
                    signal, action, reason, indicators, current_portfolio_value
                )
                
                # Execute trades based on execution type
                if execution_type == 'market_open' and i < len(trading_days) - 1:
                    # Execute at next day's open
                    next_day = trading_days[i + 1]
                    trades = execution_engine.execute_market_on_open(target_portfolio, next_day)
                elif execution_type == 'market_close':
                    # Execute at current day's close
                    trades = execution_engine.execute_market_on_close(target_portfolio, trade_date)
                elif execution_type == 'hourly_average':
                    # Execute at average price
                    trades = execution_engine.execute_hourly_average(target_portfolio, trade_date)
                
                # Record portfolio value
                portfolio_value = execution_engine.get_portfolio_value(trade_date)
                portfolio_history.append({
                    'date': trade_date,
                    'portfolio_value': portfolio_value,
                    'cash': execution_engine.current_capital,
                    'signal': signal,
                    'action': action
                })
                
                signal_history.append({
                    'date': trade_date,
                    'signal': signal,
                    'action': action,
                    'reason': reason
                })
                
                # Progress logging
                if (i + 1) % 50 == 0:
                    self.logger.info(f"Processed {i + 1}/{len(trading_days)} days, Portfolio: ${portfolio_value:,.0f}")
                    
            except Exception as e:
                self.logger.error(f"Error processing {trade_date.date()}: {e}")
                continue
        
        # Calculate final performance metrics
        performance_metrics = execution_engine.get_performance_metrics()
        
        results = {
            'execution_type': execution_type,
            'portfolio_history': portfolio_history,
            'signal_history': signal_history,
            'transaction_log': execution_engine.transaction_log,
            'performance_metrics': performance_metrics,
            'final_positions': execution_engine.current_positions
        }
        
        return results

# Test the execution engine
def test_execution_engine():
    """Test the execution engine with different strategies"""
    
    # Test parameters
    start_date = '2024-11-01'
    end_date = '2024-11-30'
    
    # Test different execution strategies
    execution_types = ['market_close', 'market_open', 'hourly_average']
    
    for exec_type in execution_types:
        print(f"\n=== Testing {exec_type.upper()} Execution ===")
        
        runner = BacktestRunner(start_date, end_date, initial_capital=100000)
        results = runner.run_backtest(execution_type=exec_type)
        
        metrics = results['performance_metrics']
        print(f"Total Return: {metrics['total_return']:.2%}")
        print(f"Transaction Costs: ${metrics['total_costs']:.2f}")
        print(f"Number of Trades: {metrics['number_of_trades']}")
        print(f"Final Portfolio Value: ${metrics['current_value']:.2f}")

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Run test
    test_execution_engine()
