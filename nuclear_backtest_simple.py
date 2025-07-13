#!/usr/bin/env python3
"""
Nuclear Energy Trading Strategy Backtester - Simplified Version
Tests the nuclear trading bot against historical data with multiple execution strategies.
"""

import yfinance as yf
import pandas as pd
import numpy as np
import datetime as dt
from datetime import timedelta
import json
import logging
import warnings
import matplotlib.pyplot as plt
import sys
import os

warnings.filterwarnings('ignore')

# Import the nuclear trading bot components
try:
    from nuclear_trading_bot import NuclearStrategyEngine, TechnicalIndicators
except ImportError:
    print("Error: Could not import nuclear_trading_bot. Make sure it's in the same directory.")
    sys.exit(1)

class BacktestResult:
    """Container for backtest results"""
    def __init__(self, strategy_name, total_return, annual_return, sharpe_ratio, 
                 max_drawdown, win_rate, total_trades, portfolio_values, trades, benchmark_return):
        self.strategy_name = strategy_name
        self.total_return = total_return
        self.annual_return = annual_return
        self.sharpe_ratio = sharpe_ratio
        self.max_drawdown = max_drawdown
        self.win_rate = win_rate
        self.total_trades = total_trades
        self.portfolio_values = portfolio_values
        self.trades = trades
        self.benchmark_return = benchmark_return

class Trade:
    """Container for trade information"""
    def __init__(self, date, symbol, action, price, shares, value, reason):
        self.date = date
        self.symbol = symbol
        self.action = action
        self.price = price
        self.shares = shares
        self.value = value
        self.reason = reason

class NuclearBacktester:
    """Simplified Nuclear Energy Strategy Backtester"""
    
    def __init__(self, start_date, end_date, initial_capital=100000):
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        
        # Setup logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
        # Initialize strategy components
        self.strategy_engine = NuclearStrategyEngine()
        self.indicators = TechnicalIndicators()
        
        # Get all symbols needed
        self.all_symbols = self.strategy_engine.all_symbols
        
        # Data storage
        self.daily_data = {}
        self.hourly_data = {}
    
    def download_data(self):
        """Download all required data"""
        self.logger.info("Downloading historical data...")
        
        # Download daily data
        for symbol in self.all_symbols:
            try:
                ticker = yf.Ticker(symbol)
                data = ticker.history(start=self.start_date, end=self.end_date, interval='1d')
                if not data.empty:
                    self.daily_data[symbol] = data
                    self.logger.info(f"Downloaded daily data for {symbol}: {len(data)} records")
                else:
                    self.logger.warning(f"No daily data for {symbol}")
            except Exception as e:
                self.logger.error(f"Failed to download {symbol}: {e}")
        
        # Download hourly data for key symbols (limited to avoid API limits)
        key_symbols = ['SPY', 'QQQ', 'TQQQ', 'UVXY', 'SMR', 'BWXT', 'TLT']
        for symbol in key_symbols:
            if symbol in self.all_symbols:
                try:
                    ticker = yf.Ticker(symbol)
                    data = ticker.history(start=self.start_date, end=self.end_date, interval='1h')
                    if not data.empty:
                        self.hourly_data[symbol] = data
                        self.logger.info(f"Downloaded hourly data for {symbol}: {len(data)} records")
                except Exception as e:
                    self.logger.warning(f"Failed to download hourly data for {symbol}: {e}")
        
        self.logger.info(f"Data download complete. Daily: {len(self.daily_data)}, Hourly: {len(self.hourly_data)}")
    
    def calculate_indicators_for_date(self, target_date):
        """Calculate indicators for all symbols as of target_date"""
        indicators = {}
        
        for symbol in self.all_symbols:
            if symbol not in self.daily_data:
                continue
                
            df = self.daily_data[symbol]
            if df.empty:
                continue
            
            # Get data up to target_date
            historical_data = df[df.index <= target_date]
            
            if len(historical_data) < 20:  # Need minimum data for indicators
                continue
            
            close = historical_data['Close']
            
            try:
                indicators[symbol] = {
                    'rsi_10': self._safe_rsi(close, 10),
                    'rsi_20': self._safe_rsi(close, 20),
                    'ma_200': self._safe_ma(close, 200),
                    'ma_20': self._safe_ma(close, 20),
                    'ma_return_90': self._safe_ma_return(close, 90),
                    'cum_return_60': self._safe_cum_return(close, 60),
                    'current_price': float(close.iloc[-1]),
                    'price_history': close.tail(90).values.tolist() if len(close) >= 90 else close.values.tolist()
                }
            except Exception as e:
                self.logger.warning(f"Failed to calculate indicators for {symbol} on {target_date}: {e}")
                continue
        
        return indicators
    
    def _safe_rsi(self, data, window):
        """Safely calculate RSI"""
        try:
            rsi = self.indicators.rsi(data, window)
            if hasattr(rsi, 'iloc') and len(rsi) > 0:
                value = float(rsi.iloc[-1])
                return value if not pd.isna(value) else 50.0
            return 50.0
        except:
            return 50.0
    
    def _safe_ma(self, data, window):
        """Safely calculate moving average"""
        try:
            ma = self.indicators.moving_average(data, window)
            if hasattr(ma, 'iloc') and len(ma) > 0:
                value = float(ma.iloc[-1])
                return value if not pd.isna(value) else float(data.iloc[-1])
            return float(data.iloc[-1])
        except:
            return float(data.iloc[-1])
    
    def _safe_ma_return(self, data, window):
        """Safely calculate moving average return"""
        try:
            ma_ret = self.indicators.moving_average_return(data, window)
            if hasattr(ma_ret, 'iloc') and len(ma_ret) > 0:
                value = float(ma_ret.iloc[-1])
                return value if not pd.isna(value) else 0.0
            return 0.0
        except:
            return 0.0
    
    def _safe_cum_return(self, data, window):
        """Safely calculate cumulative return"""
        try:
            cum_ret = self.indicators.cumulative_return(data, window)
            if hasattr(cum_ret, 'iloc') and len(cum_ret) > 0:
                value = float(cum_ret.iloc[-1])
                return value if not pd.isna(value) else 0.0
            return 0.0
        except:
            return 0.0
    
    def get_execution_price(self, symbol, date, execution_strategy, hour=None):
        """Get execution price based on strategy"""
        if symbol not in self.daily_data:
            return None
        
        daily_df = self.daily_data[symbol]
        
        # Find the exact date or next available trading day
        target_date = pd.Timestamp(date).normalize()
        available_data = daily_df[daily_df.index >= target_date]
        
        if available_data.empty:
            return None
        
        day_data = available_data.iloc[0]
        
        if execution_strategy == 'open':
            return float(day_data['Open'])
        elif execution_strategy == 'close':
            return float(day_data['Close'])
        elif execution_strategy == 'hour' and hour is not None:
            # Try to get hourly data for specific hour
            if symbol in self.hourly_data:
                hourly_df = self.hourly_data[symbol]
                target_datetime = pd.Timestamp(date).replace(hour=hour, minute=0)
                
                # Find closest hourly data
                closest_data = hourly_df[hourly_df.index >= target_datetime]
                if not closest_data.empty:
                    return float(closest_data.iloc[0]['Close'])
            
            # Fallback to daily close
            return float(day_data['Close'])
        elif execution_strategy == 'signal':
            # Simulate random hour between 10 AM and 3 PM
            signal_hour = np.random.choice(range(10, 16))
            return self.get_execution_price(symbol, date, 'hour', signal_hour)
        
        return float(day_data['Close'])
    
    def run_backtest(self, execution_strategy='close', execution_hour=None):
        """Run backtest with specified execution strategy"""
        self.logger.info(f"Running backtest: {execution_strategy} execution")
        
        # Initialize portfolio
        portfolio_value = self.initial_capital
        positions = {}  # {symbol: shares}
        
        # Results tracking
        portfolio_values = []
        trades = []
        dates = []
        
        # Generate trading dates (daily)
        start_dt = pd.Timestamp(self.start_date)
        end_dt = pd.Timestamp(self.end_date)
        trading_dates = pd.bdate_range(start=start_dt, end=end_dt, freq='B')  # Business days only
        
        # Get benchmark data
        spy_data = self.daily_data.get('SPY')
        
        for i, date in enumerate(trading_dates):
            try:
                # Calculate indicators for this date
                indicators = self.calculate_indicators_for_date(date)
                
                if not indicators:
                    continue
                
                # Get strategy signal
                symbol, action, reason = self.strategy_engine.evaluate_nuclear_strategy(indicators, self.daily_data)
                
                # Handle portfolio rebalancing
                new_positions = self._calculate_target_positions(symbol, action, reason, indicators, portfolio_value)
                
                # Execute trades
                trades_executed = self._execute_rebalancing(positions, new_positions, date, execution_strategy, execution_hour)
                trades.extend(trades_executed)
                
                # Update portfolio value
                portfolio_value = self._calculate_portfolio_value(positions, date)
                
                portfolio_values.append(portfolio_value)
                dates.append(date)
                
                if i % 50 == 0:
                    self.logger.info(f"Processed {i+1}/{len(trading_dates)} dates, Portfolio: ${portfolio_value:,.0f}")
                    
            except Exception as e:
                self.logger.error(f"Error processing date {date}: {e}")
                continue
        
        # Calculate performance metrics
        if portfolio_values and spy_data is not None:
            portfolio_series = pd.Series(portfolio_values, index=dates)
            benchmark_return = self._calculate_benchmark_return(spy_data)
            
            result = self._calculate_performance_metrics(
                portfolio_series, trades, benchmark_return, execution_strategy
            )
            
            return result
        else:
            self.logger.error("No portfolio values calculated or missing SPY data")
            return None
    
    def _calculate_target_positions(self, signal_symbol, action, reason, indicators, portfolio_value):
        """Calculate target position allocation based on strategy signal"""
        target_positions = {}
        
        # Handle different signal types
        if signal_symbol == 'NUCLEAR_PORTFOLIO':
            # Nuclear portfolio allocation
            nuclear_portfolio = self.strategy_engine.get_nuclear_portfolio(indicators, self.daily_data)
            for symbol, allocation in nuclear_portfolio.items():
                if symbol in indicators:
                    current_price = indicators[symbol]['current_price']
                    if current_price > 0:
                        target_value = portfolio_value * allocation['weight']
                        target_positions[symbol] = target_value / current_price
                        
        elif signal_symbol == 'UVXY_BTAL_PORTFOLIO':
            # UVXY 75% + BTAL 25%
            for symbol, weight in [('UVXY', 0.75), ('BTAL', 0.25)]:
                if symbol in indicators:
                    current_price = indicators[symbol]['current_price']
                    target_value = portfolio_value * weight
                    target_positions[symbol] = target_value / current_price
                    
        elif 'PORTFOLIO' in signal_symbol:
            # Parse portfolio from reason string
            import re
            portfolio_matches = re.findall(r'(\w+) \((\d+\.?\d*)%\)', reason)
            for symbol, weight_str in portfolio_matches:
                if symbol in indicators:
                    weight = float(weight_str) / 100.0
                    current_price = indicators[symbol]['current_price']
                    target_value = portfolio_value * weight
                    target_positions[symbol] = target_value / current_price
                    
        else:
            # Single symbol signal
            if action == 'BUY' and signal_symbol in indicators:
                current_price = indicators[signal_symbol]['current_price']
                # Allocate 100% to single symbol
                target_positions[signal_symbol] = portfolio_value / current_price
            elif action == 'HOLD':
                # Keep existing positions or stay in cash
                pass
        
        return target_positions
    
    def _execute_rebalancing(self, current_positions, target_positions, date, execution_strategy, execution_hour):
        """Execute trades to rebalance portfolio"""
        trades = []
        
        # Sell positions not in target
        for symbol in list(current_positions.keys()):
            if symbol not in target_positions:
                shares_to_sell = current_positions[symbol]
                if shares_to_sell > 0:
                    price = self.get_execution_price(symbol, date, execution_strategy, execution_hour)
                    if price is not None:
                        trade_value = shares_to_sell * price
                        trade = Trade(date, symbol, 'SELL', price, -shares_to_sell, -trade_value, 'Portfolio rebalancing')
                        trades.append(trade)
                        del current_positions[symbol]
        
        # Adjust or create positions in target
        for symbol, target_shares in target_positions.items():
            current_shares = current_positions.get(symbol, 0)
            shares_diff = target_shares - current_shares
            
            if abs(shares_diff) > 0.01:  # Minimum trade threshold
                price = self.get_execution_price(symbol, date, execution_strategy, execution_hour)
                if price is not None:
                    trade_value = shares_diff * price
                    action = 'BUY' if shares_diff > 0 else 'SELL'
                    
                    trade = Trade(date, symbol, action, price, shares_diff, trade_value, 'Portfolio rebalancing')
                    trades.append(trade)
                    current_positions[symbol] = target_shares
        
        return trades
    
    def _calculate_portfolio_value(self, positions, date):
        """Calculate total portfolio value at given date"""
        total_value = 0
        
        for symbol, shares in positions.items():
            if shares > 0:
                price = self.get_execution_price(symbol, date, 'close')
                if price is not None:
                    total_value += shares * price
        
        return total_value if total_value > 0 else self.initial_capital
    
    def _calculate_benchmark_return(self, spy_data):
        """Calculate benchmark (SPY) return over backtest period"""
        try:
            start_dt = pd.Timestamp(self.start_date)
            end_dt = pd.Timestamp(self.end_date)
            
            # Get start and end prices
            start_data = spy_data[spy_data.index >= start_dt]
            end_data = spy_data[spy_data.index <= end_dt]
            
            if not start_data.empty and not end_data.empty:
                start_price = float(start_data.iloc[0]['Close'])
                end_price = float(end_data.iloc[-1]['Close'])
                return (end_price / start_price) - 1
        except Exception as e:
            self.logger.error(f"Error calculating benchmark return: {e}")
        
        return 0.0
    
    def _calculate_performance_metrics(self, portfolio_series, trades, benchmark_return, strategy_name):
        """Calculate comprehensive performance metrics"""
        
        # Basic returns
        total_return = (portfolio_series.iloc[-1] / portfolio_series.iloc[0]) - 1
        
        # Annual return
        days = (portfolio_series.index[-1] - portfolio_series.index[0]).days
        annual_return = (1 + total_return) ** (365.25 / days) - 1
        
        # Daily returns for risk metrics
        daily_returns = portfolio_series.pct_change().dropna()
        
        # Sharpe ratio (assuming 2% risk-free rate)
        excess_returns = daily_returns - (0.02 / 252)
        sharpe_ratio = excess_returns.mean() / excess_returns.std() * np.sqrt(252) if excess_returns.std() > 0 else 0
        
        # Maximum drawdown
        cumulative = (1 + daily_returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # Win rate
        profitable_trades = sum(1 for trade in trades if trade.value > 0)
        win_rate = profitable_trades / len(trades) if trades else 0
        
        return BacktestResult(
            strategy_name=strategy_name,
            total_return=total_return,
            annual_return=annual_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            total_trades=len(trades),
            portfolio_values=portfolio_series,
            trades=trades,
            benchmark_return=benchmark_return
        )
    
    def run_comprehensive_backtest(self):
        """Run backtests for all execution strategies"""
        
        # Download all data first
        self.download_data()
        
        strategies = [
            ('Open Execution', 'open', None),
            ('Close Execution', 'close', None),
            ('10AM Execution', 'hour', 10),
            ('2PM Execution', 'hour', 14),
            ('Signal Timing', 'signal', None)
        ]
        
        results = {}
        
        for strategy_name, execution_strategy, hour in strategies:
            self.logger.info(f"Running backtest: {strategy_name}")
            try:
                result = self.run_backtest(execution_strategy, hour)
                if result:
                    results[strategy_name] = result
                    self.logger.info(f"Completed {strategy_name}: {result.total_return:.2%} return")
            except Exception as e:
                self.logger.error(f"Failed backtest for {strategy_name}: {e}")
        
        return results
    
    def generate_report(self, results, save_path=None):
        """Generate comprehensive backtest report"""
        
        # Create summary table
        summary_data = []
        for name, result in results.items():
            summary_data.append({
                'Strategy': name,
                'Total Return': f"{result.total_return:.2%}",
                'Annual Return': f"{result.annual_return:.2%}",
                'Sharpe Ratio': f"{result.sharpe_ratio:.2f}",
                'Max Drawdown': f"{result.max_drawdown:.2%}",
                'Win Rate': f"{result.win_rate:.2%}",
                'Total Trades': result.total_trades,
                'vs Benchmark': f"{result.total_return - result.benchmark_return:.2%}"
            })
        
        summary_df = pd.DataFrame(summary_data)
        
        # Print summary
        print("\n" + "="*80)
        print("NUCLEAR ENERGY STRATEGY BACKTEST RESULTS")
        print("="*80)
        print(f"Backtest Period: {self.start_date} to {self.end_date}")
        print(f"Initial Capital: ${self.initial_capital:,.0f}")
        print("\nSUMMARY BY EXECUTION STRATEGY:")
        print(summary_df.to_string(index=False))
        
        # Find best strategy
        if results:
            best_strategy = max(results.items(), key=lambda x: x[1].sharpe_ratio)
            print(f"\nBEST STRATEGY (by Sharpe Ratio): {best_strategy[0]}")
            print(f"  Sharpe Ratio: {best_strategy[1].sharpe_ratio:.2f}")
            print(f"  Total Return: {best_strategy[1].total_return:.2%}")
            print(f"  Max Drawdown: {best_strategy[1].max_drawdown:.2%}")
        
        # Create visualizations
        self._create_visualizations(results, save_path)
        
        # Save results
        if save_path:
            summary_df.to_csv(f"{save_path}_summary.csv", index=False)
            self.logger.info(f"Results saved to {save_path}_summary.csv")
    
    def _create_visualizations(self, results, save_path=None):
        """Create performance visualizations"""
        
        if not results:
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Nuclear Energy Strategy Backtest Results', fontsize=16)
        
        # Portfolio value over time
        ax1 = axes[0, 0]
        for name, result in results.items():
            normalized_values = result.portfolio_values / result.portfolio_values.iloc[0]
            ax1.plot(result.portfolio_values.index, normalized_values, label=name, linewidth=2)
        
        ax1.set_title('Normalized Portfolio Value Over Time')
        ax1.set_ylabel('Normalized Value')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Return comparison
        ax2 = axes[0, 1]
        strategies = list(results.keys())
        returns = [results[s].total_return for s in strategies]
        ax2.bar(strategies, returns)
        ax2.set_title('Total Returns by Strategy')
        ax2.set_ylabel('Total Return')
        ax2.tick_params(axis='x', rotation=45)
        
        # Add benchmark line
        benchmark_return = list(results.values())[0].benchmark_return
        ax2.axhline(y=benchmark_return, color='red', linestyle='--', 
                   label=f'SPY Benchmark ({benchmark_return:.2%})')
        ax2.legend()
        
        # Risk-Return scatter
        ax3 = axes[1, 0]
        returns = [r.annual_return for r in results.values()]
        sharpe_ratios = [r.sharpe_ratio for r in results.values()]
        ax3.scatter(returns, sharpe_ratios, s=100, alpha=0.7)
        
        for i, name in enumerate(results.keys()):
            ax3.annotate(name, (returns[i], sharpe_ratios[i]), xytext=(5, 5), 
                        textcoords='offset points', fontsize=8)
        
        ax3.set_title('Risk-Return Profile')
        ax3.set_xlabel('Annual Return')
        ax3.set_ylabel('Sharpe Ratio')
        ax3.grid(True, alpha=0.3)
        
        # Drawdown comparison
        ax4 = axes[1, 1]
        strategies = list(results.keys())
        drawdowns = [abs(results[s].max_drawdown) for s in strategies]
        ax4.bar(strategies, drawdowns)
        ax4.set_title('Maximum Drawdown by Strategy')
        ax4.set_ylabel('Max Drawdown (Absolute)')
        ax4.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(f"{save_path}_charts.png", dpi=300, bbox_inches='tight')
            self.logger.info(f"Charts saved to {save_path}_charts.png")
        
        plt.show()

def main():
    """Main function to run comprehensive backtests"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Nuclear Energy Strategy Backtester')
    parser.add_argument('--start-date', type=str, default='2020-01-01',
                       help='Start date for backtest (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, default='2024-12-31',
                       help='End date for backtest (YYYY-MM-DD)')
    parser.add_argument('--capital', type=float, default=100000,
                       help='Initial capital for backtest')
    parser.add_argument('--save-path', type=str, default='nuclear_backtest_results',
                       help='Path prefix for saving results')
    
    args = parser.parse_args()
    
    # Create backtester
    backtester = NuclearBacktester(
        start_date=args.start_date,
        end_date=args.end_date,
        initial_capital=args.capital
    )
    
    # Run comprehensive backtest
    print("Starting comprehensive backtest of Nuclear Energy Strategy...")
    print(f"Period: {args.start_date} to {args.end_date}")
    print(f"Initial Capital: ${args.capital:,.0f}")
    
    results = backtester.run_comprehensive_backtest()
    
    if results:
        # Generate report
        backtester.generate_report(results, args.save_path)
        
        # Print additional insights
        print("\n" + "="*80)
        print("KEY INSIGHTS:")
        print("="*80)
        
        if len(results) > 1:
            # Compare strategies
            strategy_returns = {name: result.total_return for name, result in results.items()}
            best_return = max(strategy_returns.items(), key=lambda x: x[1])
            worst_return = min(strategy_returns.items(), key=lambda x: x[1])
            
            print(f"📊 Best Performing Strategy: {best_return[0]} ({best_return[1]:.2%})")
            print(f"📊 Worst Performing Strategy: {worst_return[0]} ({worst_return[1]:.2%})")
            
            # Check if timing matters
            timing_strategies = ['Open Execution', '10AM Execution', '2PM Execution', 'Close Execution']
            timing_returns = {name: strategy_returns[name] for name in timing_strategies if name in strategy_returns}
            
            if len(timing_returns) > 1:
                timing_range = max(timing_returns.values()) - min(timing_returns.values())
                print(f"📊 Timing Impact: {timing_range:.2%} difference between best and worst timing")
                
                if timing_range > 0.05:  # 5% difference
                    print("🎯 TIMING MATTERS! Consider optimizing execution time.")
                else:
                    print("✅ Timing has minimal impact on this strategy.")
        
        print(f"\n✅ Backtest complete! Results saved with prefix: {args.save_path}")
    else:
        print("❌ No backtest results generated")

if __name__ == "__main__":
    main()
