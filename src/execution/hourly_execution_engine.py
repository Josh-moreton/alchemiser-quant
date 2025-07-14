#!/usr/bin/env python3
"""
Hourly Execution Engine - Enhanced with Real Hourly Data
Tests different execution hours using actual hourly price data from yfinance
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
import warnings
warnings.filterwarnings('ignore')

from nuclear_backtest_framework import BacktestDataProvider, BacktestNuclearStrategy, PortfolioBuilder

class HourlyExecutionEngine:
    """
    Enhanced execution engine that tests execution at different hours of the trading day
    Uses real hourly price data to find optimal execution timing
    """
    
    def __init__(self, start_date: str, end_date: str, initial_capital: float = 100000):
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.logger = logging.getLogger(__name__)
        
        # Trading hours to test (9:30 AM to 4:00 PM ET)
        self.trading_hours = {
            '09:30': 9,   # Market open (hour 9)
            '10:30': 10,  # 1 hour after open
            '11:30': 11,  # Mid-morning
            '12:30': 12,  # Lunch time
            '13:30': 13,  # Afternoon
            '14:30': 14,  # Late afternoon  
            '15:30': 15,  # 30 min before close
            '16:00': 16   # Market close
        }
        
        # Transaction cost parameters
        self.commission_per_trade = 0.0
        self.spread_cost = 0.001
        self.slippage = 0.0005
    
    def test_all_execution_hours(self) -> Dict:
        """Test strategy execution at each hour of the trading day"""
        
        print("🕐 HOURLY EXECUTION ANALYSIS")
        print("=" * 50)
        print(f"Testing execution at {len(self.trading_hours)} different hours")
        print(f"Period: {self.start_date} to {self.end_date}")
        print()
        
        results = {}
        
        for hour_label, hour_value in self.trading_hours.items():
            print(f"  Testing execution at {hour_label}...")
            
            try:
                result = self._run_hourly_backtest(hour_value, hour_label)
                results[hour_label] = result
                
                metrics = result['performance_metrics']
                print(f"    {hour_label}: {metrics['total_return']:.1%} return, ${metrics['total_costs']:.0f} costs")
                
            except Exception as e:
                self.logger.error(f"Error testing {hour_label}: {e}")
                print(f"    {hour_label}: ERROR - {e}")
                continue
        
        # Find best hour
        best_hour = None
        best_return = -float('inf')
        
        for hour, result in results.items():
            if 'performance_metrics' in result:
                hour_return = result['performance_metrics']['total_return']
                if hour_return > best_return:
                    best_return = hour_return
                    best_hour = hour
        
        print(f"\n🏆 BEST EXECUTION HOUR: {best_hour} ({best_return:.1%} return)")
        
        return {
            'results': results,
            'best_hour': best_hour,
            'best_return': best_return,
            'summary': self._generate_hourly_summary(results)
        }
    
    def _run_hourly_backtest(self, execution_hour: int, hour_label: str) -> Dict:
        """Run backtest with execution at specific hour"""
        
        # Initialize framework components
        data_provider = BacktestDataProvider(self.start_date, self.end_date)
        strategy = BacktestNuclearStrategy(data_provider)
        
        # Download both daily and hourly data
        daily_data = data_provider.download_all_data(strategy.all_symbols)
        
        # Download hourly data for price execution
        try:
            hourly_data = data_provider.download_hourly_data(strategy.all_symbols)
            # Set the hourly data on the provider so get_price_at_hour can access it
            data_provider.hourly_data = hourly_data
            use_hourly = len(hourly_data) > 0
            if not use_hourly:
                self.logger.warning(f"No hourly data available, falling back to daily approximation")
        except Exception as e:
            self.logger.warning(f"Hourly data download failed: {e}, using daily approximation")
            use_hourly = False
        
        # Initialize execution state
        current_capital = self.initial_capital
        current_positions = {}
        transaction_log = []
        portfolio_history = []
        signal_history = []
        
        # Get trading days
        spy_data = daily_data['SPY']
        start_dt = pd.Timestamp(self.start_date)
        end_dt = pd.Timestamp(self.end_date)
        trading_days = spy_data.index[(spy_data.index >= start_dt) & (spy_data.index <= end_dt)]
        
        portfolio_builder = PortfolioBuilder(strategy)
        
        for i, trade_date in enumerate(trading_days):
            try:
                # 1. Evaluate strategy using daily data (as normal)
                signal, action, reason, indicators, market_data = strategy.evaluate_strategy_at_time(trade_date)
                
                # 2. Build target portfolio
                current_portfolio_value = self._calculate_portfolio_value(
                    current_positions, current_capital, data_provider, trade_date
                )
                
                target_portfolio = portfolio_builder.build_target_portfolio(
                    signal, action, reason, indicators, current_portfolio_value
                )
                
                # 3. Execute trades at specific hour using hourly prices
                if use_hourly:
                    execution_prices = self._get_hourly_execution_prices(
                        target_portfolio, current_positions, data_provider, trade_date, execution_hour
                    )
                else:
                    # Fallback to daily approximation
                    execution_prices = self._get_daily_execution_prices(
                        target_portfolio, current_positions, data_provider, trade_date, execution_hour
                    )
                
                # 4. Execute trades
                trades = self._execute_trades(
                    target_portfolio, current_positions, execution_prices, 
                    trade_date, hour_label, current_capital
                )
                
                # 5. Update portfolio state
                for trade in trades:
                    current_capital -= trade['trade_value'] + trade['costs']
                    
                    symbol = trade['symbol']
                    shares = trade['shares']
                    
                    if symbol in current_positions:
                        current_positions[symbol] += shares
                    else:
                        current_positions[symbol] = shares
                    
                    # Clean up zero positions
                    if abs(current_positions[symbol]) < 0.01:
                        del current_positions[symbol]
                
                transaction_log.extend(trades)
                
                # 6. Record portfolio state
                portfolio_value = self._calculate_portfolio_value(
                    current_positions, current_capital, data_provider, trade_date
                )
                
                portfolio_history.append({
                    'date': trade_date,
                    'portfolio_value': portfolio_value,
                    'cash': current_capital,
                    'signal': signal,
                    'action': action
                })
                
                signal_history.append({
                    'date': trade_date,
                    'signal': signal,
                    'action': action,
                    'reason': reason
                })
                
            except Exception as e:
                self.logger.error(f"Error processing {trade_date.date()} for hour {hour_label}: {e}")
                continue
        
        # Calculate performance metrics
        final_value = self._calculate_portfolio_value(
            current_positions, current_capital, data_provider, trading_days[-1]
        ) if trading_days.size > 0 else self.initial_capital
        
        total_return = (final_value - self.initial_capital) / self.initial_capital
        total_costs = sum(trade['costs'] for trade in transaction_log)
        
        performance_metrics = {
            'total_return': total_return,
            'total_costs': total_costs,
            'current_value': final_value,
            'number_of_trades': len(transaction_log),
            'cash_position': current_capital
        }
        
        return {
            'execution_hour': hour_label,
            'portfolio_history': portfolio_history,
            'signal_history': signal_history,
            'transaction_log': transaction_log,
            'performance_metrics': performance_metrics,
            'final_positions': current_positions,
            'used_hourly_data': use_hourly
        }
    
    def _get_hourly_execution_prices(self, target_portfolio: Dict, current_positions: Dict,
                                   data_provider: BacktestDataProvider, trade_date: pd.Timestamp,
                                   execution_hour: int) -> Dict[str, float]:
        """Get execution prices using real hourly data"""
        execution_prices = {}
        
        all_symbols = set(list(target_portfolio.keys()) + list(current_positions.keys()))
        
        for symbol in all_symbols:
            price = data_provider.get_price_at_hour(symbol, trade_date, execution_hour)
            
            if price is not None:
                # Handle case where price might be a pandas Series
                try:
                    if isinstance(price, pd.Series):
                        price = price.iloc[0] if len(price) > 0 else None
                    
                    if price is not None:
                        execution_prices[symbol] = float(price)
                    else:
                        # Fallback to daily close price
                        fallback_price = data_provider.get_price_at_time(symbol, trade_date, 'Close')
                        if fallback_price:
                            execution_prices[symbol] = float(fallback_price)
                except (ValueError, TypeError, IndexError):
                    # Fallback to daily close price on any conversion error
                    fallback_price = data_provider.get_price_at_time(symbol, trade_date, 'Close')
                    if fallback_price:
                        execution_prices[symbol] = float(fallback_price)
            else:
                # Fallback to daily close price
                fallback_price = data_provider.get_price_at_time(symbol, trade_date, 'Close')
                if fallback_price:
                    execution_prices[symbol] = float(fallback_price)
        
        return execution_prices
    
    def _get_daily_execution_prices(self, target_portfolio: Dict, current_positions: Dict,
                                  data_provider: BacktestDataProvider, trade_date: pd.Timestamp,
                                  execution_hour: int) -> Dict[str, float]:
        """Fallback: estimate execution prices using daily OHLC data"""
        execution_prices = {}
        
        all_symbols = set(list(target_portfolio.keys()) + list(current_positions.keys()))
        
        for symbol in all_symbols:
            data = data_provider.get_data_up_to_date(symbol, trade_date + pd.Timedelta(days=1))
            
            if not data.empty and trade_date in data.index:
                day_data = data.loc[trade_date]
                
                # Estimate price based on hour of day
                if execution_hour <= 10:  # Morning
                    price = (day_data['Open'] + day_data['Low']) / 2
                elif execution_hour <= 13:  # Midday
                    price = (day_data['High'] + day_data['Low']) / 2
                elif execution_hour <= 15:  # Afternoon
                    price = (day_data['High'] + day_data['Close']) / 2
                else:  # Near close
                    price = day_data['Close']
                
                # Ensure price is a scalar value for float conversion
                try:
                    if isinstance(price, pd.Series):
                        price = price.iloc[0] if len(price) > 0 else float(price.iloc[0])
                    execution_prices[symbol] = float(price)
                except (ValueError, TypeError, IndexError) as e:
                    self.logger.warning(f"Price conversion error for {symbol}: {e}")
                    continue
        
        return execution_prices
    
    def _execute_trades(self, target_portfolio: Dict, current_positions: Dict,
                       execution_prices: Dict, trade_date: pd.Timestamp,
                       hour_label: str, current_capital: float) -> List[Dict]:
        """Execute trades at the given prices"""
        trades = []
        
        # Calculate required trades
        for symbol in set(list(target_portfolio.keys()) + list(current_positions.keys())):
            if symbol not in execution_prices:
                continue
            
            target_shares = target_portfolio.get(symbol, 0.0)
            current_shares = current_positions.get(symbol, 0.0)
            shares_to_trade = target_shares - current_shares
            
            if abs(shares_to_trade) < 0.01:  # Skip tiny trades
                continue
            
            price = execution_prices[symbol]
            trade_value = shares_to_trade * price
            
            # Calculate costs
            notional_value = abs(trade_value)
            costs = notional_value * (self.spread_cost + self.slippage)
            
            trade_record = {
                'date': trade_date,
                'hour': hour_label,
                'symbol': symbol,
                'shares': shares_to_trade,
                'price': price,
                'trade_value': trade_value,
                'costs': costs,
                'execution_type': f'hourly_{hour_label}'
            }
            
            trades.append(trade_record)
        
        return trades
    
    def _calculate_portfolio_value(self, positions: Dict, cash: float,
                                 data_provider: BacktestDataProvider,
                                  as_of_date: pd.Timestamp) -> float:
        """Calculate total portfolio value"""
        total_value = cash
        
        for symbol, shares in positions.items():
            if shares > 0:
                price = data_provider.get_price_at_time(symbol, as_of_date, 'Close')
                if price:
                    total_value += shares * price
        
        return total_value
    
    def _generate_hourly_summary(self, results: Dict) -> Dict:
        """Generate summary of hourly execution results"""
        summary = {
            'hours_tested': len(results),
            'successful_hours': len([r for r in results.values() if 'performance_metrics' in r]),
            'returns_by_hour': {},
            'costs_by_hour': {},
            'best_hour': None,
            'worst_hour': None
        }
        
        best_return = -float('inf')
        worst_return = float('inf')
        
        for hour, result in results.items():
            if 'performance_metrics' in result:
                metrics = result['performance_metrics']
                return_pct = metrics['total_return']
                costs = metrics['total_costs']
                
                summary['returns_by_hour'][hour] = return_pct
                summary['costs_by_hour'][hour] = costs
                
                if return_pct > best_return:
                    best_return = return_pct
                    summary['best_hour'] = hour
                
                if return_pct < worst_return:
                    worst_return = return_pct
                    summary['worst_hour'] = hour
        
        return summary

def test_hourly_execution():
    """Test execution at different hours of the trading day"""
    
    # Test parameters - adjust as needed
    START_DATE = '2024-11-01'
    END_DATE = '2024-11-30'  # Shorter period for hourly data availability
    INITIAL_CAPITAL = 100000
    
    # Initialize hourly execution engine
    engine = HourlyExecutionEngine(START_DATE, END_DATE, INITIAL_CAPITAL)
    
    # Run hourly analysis
    results = engine.test_all_execution_hours()
    
    # Display results
    print("\n📊 HOURLY EXECUTION SUMMARY")
    print("=" * 40)
    
    summary = results['summary']
    print(f"Hours Tested: {summary['hours_tested']}")
    print(f"Successful Tests: {summary['successful_hours']}")
    print(f"Best Hour: {summary['best_hour']} ({summary['returns_by_hour'].get(summary['best_hour'], 0):.1%})")
    print(f"Worst Hour: {summary['worst_hour']} ({summary['returns_by_hour'].get(summary['worst_hour'], 0):.1%})")
    
    print(f"\n⏰ RETURNS BY HOUR:")
    for hour in sorted(summary['returns_by_hour'].keys()):
        return_pct = summary['returns_by_hour'][hour]
        costs = summary['costs_by_hour'][hour]
        marker = "🏆" if hour == summary['best_hour'] else "  "
        print(f"{marker} {hour}: {return_pct:.1%} (${costs:.0f} costs)")
    
    return results

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.WARNING,  # Reduce noise
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Run hourly execution test
    results = test_hourly_execution()