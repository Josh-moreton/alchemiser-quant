#!/usr/bin/env python3
"""
Nuclear Energy Trading Strategy Backtester
Tests the nuclear trading bot against historical data with multiple execution strategies:
1. Trade at market open
2. Trade at specific hour (using hourly data)
3. Trade at market close
4. Trade at signal generation time (intraday precision)
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
import seaborn as sns
from typing import Dict, List, Tuple, Optional, Union
import concurrent.futures
from dataclasses import dataclass
import pickle
import os

warnings.filterwarnings('ignore')

# Import the nuclear trading bot components
from nuclear_trading_bot import NuclearStrategyEngine, TechnicalIndicators, DataProvider

@dataclass
class BacktestResult:
    """Container for backtest results"""
    strategy_name: str
    total_return: float
    annual_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    portfolio_values: pd.Series
    trades: List[dict]
    benchmark_return: float

@dataclass
class Trade:
    """Container for trade information"""
    date: dt.datetime
    symbol: str
    action: str
    price: float
    shares: float
    value: float
    reason: str
    portfolio_value_before: float
    portfolio_value_after: float

class BacktestDataProvider:
    """Enhanced data provider for backtesting with multiple timeframes"""
    
    def __init__(self, start_date: str, end_date: str):
        self.start_date = start_date
        self.end_date = end_date
        self.cache = {}
        self.logger = logging.getLogger(__name__)
    
    def get_historical_data(self, symbols: List[str], period: Optional[str] = None, interval: str = "1d") -> Dict[str, pd.DataFrame]:
        """
        Get historical data for multiple symbols with caching
        
        Args:
            symbols: List of ticker symbols
            period: Period string (ignored if start/end dates provided)
            interval: Data interval ('1d', '1h', '5m', etc.)
        """
        cache_key = f"{'-'.join(sorted(symbols))}_{interval}_{self.start_date}_{self.end_date}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        data = {}
        failed_symbols = []
        
        # Download data in batches to avoid API limits
        batch_size = 10
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i + batch_size]
            self.logger.info(f"Downloading batch {i//batch_size + 1}: {batch}")
            
            try:
                # Download batch data
                batch_data = yf.download(
                    tickers=batch,
                    start=self.start_date,
                    end=self.end_date,
                    interval=interval,
                    group_by='ticker',
                    auto_adjust=True,
                    prepost=True,
                    threads=True,
                    progress=False
                )
                
                if batch_data is None or batch_data.empty:
                    failed_symbols.extend(batch)
                    continue
                
                # Handle single vs multiple tickers
                if len(batch) == 1:
                    symbol = batch[0]
                    if batch_data is not None and not batch_data.empty:
                        # Single ticker - no MultiIndex
                        data[symbol] = batch_data.copy()
                        # Ensure we have the standard OHLCV columns
                        if 'Adj Close' in data[symbol].columns:
                            data[symbol]['Close'] = data[symbol]['Adj Close']
                else:
                    # Multiple tickers - MultiIndex columns
                    for symbol in batch:
                        try:
                            # Check if we have MultiIndex columns and symbol exists
                            if (batch_data is not None and 
                                hasattr(batch_data, 'columns') and 
                                hasattr(batch_data.columns, 'nlevels') and 
                                batch_data.columns.nlevels > 1):
                                
                                # Try to extract symbol data from MultiIndex
                                try:
                                    symbol_data = batch_data[symbol]
                                    if not symbol_data.empty and len(symbol_data.dropna()) > 0:
                                        # Ensure we have the standard OHLCV columns
                                        if 'Adj Close' in symbol_data.columns:
                                            symbol_data['Close'] = symbol_data['Adj Close']
                                        data[symbol] = symbol_data.copy()
                                    else:
                                        failed_symbols.append(symbol)
                                except (KeyError, IndexError):
                                    failed_symbols.append(symbol)
                            else:
                                failed_symbols.append(symbol)
                        except Exception as e:
                            self.logger.warning(f"Failed to extract data for {symbol}: {e}")
                            failed_symbols.append(symbol)
                            
            except Exception as e:
                self.logger.error(f"Failed to download batch {batch}: {e}")
                failed_symbols.extend(batch)
        
        if failed_symbols:
            self.logger.warning(f"Failed to download data for: {failed_symbols}")
        
        # Cache the results
        self.cache[cache_key] = data
        return data
    
    def get_intraday_price(self, symbol: str, target_date: dt.datetime, target_hour: Optional[int] = None) -> Optional[float]:
        """
        Get price at specific hour on target date using hourly data
        
        Args:
            symbol: Ticker symbol
            target_date: Target date
            target_hour: Hour to get price (0-23), if None uses close price
        """
        if target_hour is None:
            # Use daily close price
            daily_data = self.get_historical_data([symbol], interval="1d")
            if symbol in daily_data and not daily_data[symbol].empty:
                target_date_str = target_date.strftime('%Y-%m-%d')
                price_data = daily_data[symbol]
                if target_date_str in price_data.index.strftime('%Y-%m-%d'):
                    return float(price_data.loc[price_data.index.strftime('%Y-%m-%d') == target_date_str, 'Close'].iloc[0])
            return None
        
        # Use hourly data for specific hour
        hourly_data = self.get_historical_data([symbol], interval="1h")
        if symbol not in hourly_data or hourly_data[symbol].empty:
            return None
        
        price_data = hourly_data[symbol]
        target_datetime = target_date.replace(hour=target_hour, minute=0, second=0, microsecond=0)
        
        # Find closest available hourly data point
        available_times = price_data.index
        closest_time = min(available_times, key=lambda x: abs((x - target_datetime).total_seconds()))
        
        # Only use if within 2 hours of target
        if abs((closest_time - target_datetime).total_seconds()) <= 7200:  # 2 hours
            return float(price_data.loc[closest_time, 'Close'])
        
        return None

class NuclearBacktester:
    """Main backtesting engine for the Nuclear Energy strategy"""
    
    def __init__(self, start_date: str, end_date: str, initial_capital: float = 100000):
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.data_provider = BacktestDataProvider(start_date, end_date)
        self.strategy_engine = NuclearStrategyEngine()
        self.indicators = TechnicalIndicators()
        
        # Get all symbols needed for the strategy
        self.all_symbols = self.strategy_engine.all_symbols
        
        # Results storage
        self.results = {}
        
    def download_all_data(self):
        """Download all required data for backtesting"""
        self.logger.info("Downloading historical data for backtesting...")
        
        # Download daily data
        self.daily_data = self.data_provider.get_historical_data(self.all_symbols, interval="1d")
        
        # Download hourly data for intraday execution
        self.hourly_data = self.data_provider.get_historical_data(self.all_symbols, interval="1h")
        
        self.logger.info(f"Downloaded data for {len(self.daily_data)} symbols (daily) and {len(self.hourly_data)} symbols (hourly)")
        
        # Create a combined dataset for strategy evaluation
        self.combined_data = self.daily_data.copy()
        
    def calculate_indicators_for_date(self, target_date: dt.datetime) -> Dict:
        """Calculate indicators for all symbols as of target_date"""
        indicators = {}
        
        for symbol in self.all_symbols:
            if symbol not in self.daily_data:
                continue
                
            df = self.daily_data[symbol]
            if df.empty:
                continue
            
            # Get data up to target_date
            mask = df.index <= target_date
            historical_data = df[mask]
            
            if len(historical_data) < 20:  # Need minimum data for indicators
                continue
            
            close = historical_data['Close']
            
            try:
                indicators[symbol] = {
                    'rsi_10': self._safe_indicator(close, self.indicators.rsi, 10),
                    'rsi_20': self._safe_indicator(close, self.indicators.rsi, 20),
                    'ma_200': self._safe_indicator(close, self.indicators.moving_average, 200),
                    'ma_20': self._safe_indicator(close, self.indicators.moving_average, 20),
                    'ma_return_90': self._safe_indicator(close, self.indicators.moving_average_return, 90),
                    'cum_return_60': self._safe_indicator(close, self.indicators.cumulative_return, 60),
                    'current_price': float(close.iloc[-1]),
                    'price_history': close.tail(90).values.tolist() if len(close) >= 90 else close.values.tolist()
                }
            except Exception as e:
                self.logger.warning(f"Failed to calculate indicators for {symbol} on {target_date}: {e}")
                continue
        
        return indicators
    
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
    
    def get_execution_price(self, symbol: str, date: dt.datetime, execution_strategy: str, hour: int = None) -> float:
        """
        Get execution price based on strategy
        
        Args:
            symbol: Ticker symbol
            date: Execution date
            execution_strategy: 'open', 'close', 'hour', 'signal'
            hour: Specific hour for 'hour' strategy (9-16 for market hours)
        """
        if symbol not in self.daily_data:
            return None
        
        daily_df = self.daily_data[symbol]
        
        # Find the exact date or next available trading day
        target_date = date.strftime('%Y-%m-%d')
        available_dates = daily_df.index.strftime('%Y-%m-%d')
        
        if target_date in available_dates:
            day_data = daily_df[daily_df.index.strftime('%Y-%m-%d') == target_date]
        else:
            # Find next available trading day
            future_dates = daily_df[daily_df.index > date]
            if future_dates.empty:
                return None
            day_data = future_dates.head(1)
        
        if day_data.empty:
            return None
        
        if execution_strategy == 'open':
            return float(day_data['Open'].iloc[0])
        elif execution_strategy == 'close':
            return float(day_data['Close'].iloc[0])
        elif execution_strategy == 'hour' and hour is not None:
            # Use hourly data for specific hour execution
            return self.data_provider.get_intraday_price(symbol, date, hour)
        elif execution_strategy == 'signal':
            # For signal timing, we'll use a random hour between 9:30 AM and 4 PM
            # to simulate real-time signal generation
            signal_hour = np.random.choice(range(10, 16))  # 10 AM to 3 PM
            intraday_price = self.data_provider.get_intraday_price(symbol, date, signal_hour)
            if intraday_price is not None:
                return intraday_price
            else:
                # Fallback to daily close if hourly data unavailable
                return float(day_data['Close'].iloc[0])
        
        return float(day_data['Close'].iloc[0])  # Default fallback
    
    def run_backtest(self, execution_strategy: str = 'close', execution_hour: int = None, 
                    rebalance_frequency: str = 'daily') -> BacktestResult:
        """
        Run backtest with specified execution strategy
        
        Args:
            execution_strategy: 'open', 'close', 'hour', 'signal'
            execution_hour: Hour for 'hour' strategy (9-16)
            rebalance_frequency: 'daily', 'weekly', 'monthly'
        """
        self.logger.info(f"Running backtest: {execution_strategy} execution")
        
        # Initialize portfolio
        portfolio_value = self.initial_capital
        cash = self.initial_capital
        positions = {}  # {symbol: shares}
        
        # Results tracking
        portfolio_values = []
        trades = []
        dates = []
        
        # Generate trading dates based on rebalance frequency
        trading_dates = self._generate_trading_dates(rebalance_frequency)
        
        # Get benchmark data (SPY)
        spy_data = self.daily_data.get('SPY', pd.DataFrame())
        
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
                trades_executed = self._execute_rebalancing(
                    positions, new_positions, date, execution_strategy, execution_hour
                )
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
        if portfolio_values:
            portfolio_series = pd.Series(portfolio_values, index=dates)
            benchmark_return = self._calculate_benchmark_return(spy_data)
            
            result = self._calculate_performance_metrics(
                portfolio_series, trades, benchmark_return, execution_strategy
            )
            
            return result
        else:
            self.logger.error("No portfolio values calculated")
            return None
    
    def _generate_trading_dates(self, frequency: str) -> List[dt.datetime]:
        """Generate trading dates based on frequency"""
        start = dt.datetime.strptime(self.start_date, '%Y-%m-%d')
        end = dt.datetime.strptime(self.end_date, '%Y-%m-%d')
        
        dates = []
        current = start
        
        if frequency == 'daily':
            while current <= end:
                # Only include weekdays (Monday=0, Sunday=6)
                if current.weekday() < 5:
                    dates.append(current)
                current += timedelta(days=1)
        elif frequency == 'weekly':
            # Trade every Friday
            while current <= end:
                if current.weekday() == 4:  # Friday
                    dates.append(current)
                current += timedelta(days=1)
        elif frequency == 'monthly':
            # Trade on last trading day of month
            while current <= end:
                next_month = current.replace(day=28) + timedelta(days=4)
                last_day_month = next_month - timedelta(days=next_month.day)
                # Find last weekday of month
                while last_day_month.weekday() >= 5:
                    last_day_month -= timedelta(days=1)
                if current.date() == last_day_month.date():
                    dates.append(current)
                current += timedelta(days=1)
        
        return dates
    
    def _calculate_target_positions(self, signal_symbol: str, action: str, reason: str, 
                                  indicators: Dict, portfolio_value: float) -> Dict[str, float]:
        """Calculate target position allocation based on strategy signal"""
        target_positions = {}
        
        # Handle different signal types
        if signal_symbol == 'NUCLEAR_PORTFOLIO':
            # Nuclear portfolio allocation
            nuclear_portfolio = self.strategy_engine.get_nuclear_portfolio(indicators, self.daily_data)
            for symbol, allocation in nuclear_portfolio.items():
                if symbol in self.daily_data:
                    current_price = indicators.get(symbol, {}).get('current_price', 0)
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
                    
        elif signal_symbol == 'BEAR_PORTFOLIO':
            # Extract bear portfolio from reason
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
                # Stay in cash or maintain current positions
                pass
        
        return target_positions
    
    def _execute_rebalancing(self, current_positions: Dict[str, float], target_positions: Dict[str, float],
                           date: dt.datetime, execution_strategy: str, execution_hour: int) -> List[Trade]:
        """Execute trades to rebalance from current to target positions"""
        trades = []
        
        # Calculate current portfolio value
        current_value = self._calculate_portfolio_value(current_positions, date)
        
        # Sell positions not in target
        for symbol in list(current_positions.keys()):
            if symbol not in target_positions:
                # Sell entire position
                shares_to_sell = current_positions[symbol]
                if shares_to_sell > 0:
                    price = self.get_execution_price(symbol, date, execution_strategy, execution_hour)
                    if price is not None:
                        trade_value = shares_to_sell * price
                        trade = Trade(
                            date=date,
                            symbol=symbol,
                            action='SELL',
                            price=price,
                            shares=-shares_to_sell,
                            value=-trade_value,
                            reason='Portfolio rebalancing',
                            portfolio_value_before=current_value,
                            portfolio_value_after=current_value
                        )
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
                    
                    trade = Trade(
                        date=date,
                        symbol=symbol,
                        action=action,
                        price=price,
                        shares=shares_diff,
                        value=trade_value,
                        reason='Portfolio rebalancing',
                        portfolio_value_before=current_value,
                        portfolio_value_after=current_value
                    )
                    trades.append(trade)
                    current_positions[symbol] = target_shares
        
        return trades
    
    def _calculate_portfolio_value(self, positions: Dict[str, float], date: dt.datetime) -> float:
        """Calculate total portfolio value at given date"""
        total_value = 0
        
        for symbol, shares in positions.items():
            if shares > 0:
                price = self.get_execution_price(symbol, date, 'close')
                if price is not None:
                    total_value += shares * price
        
        return total_value if total_value > 0 else self.initial_capital
    
    def _calculate_benchmark_return(self, spy_data: pd.DataFrame) -> float:
        """Calculate benchmark (SPY) return over backtest period"""
        if spy_data.empty:
            return 0.0
        
        start_date = dt.datetime.strptime(self.start_date, '%Y-%m-%d')
        end_date = dt.datetime.strptime(self.end_date, '%Y-%m-%d')
        
        # Get start and end prices
        start_price = None
        end_price = None
        
        for i, (date, row) in enumerate(spy_data.iterrows()):
            if date >= start_date and start_price is None:
                start_price = row['Close']
            if date <= end_date:
                end_price = row['Close']
        
        if start_price and end_price:
            return (end_price / start_price) - 1
        return 0.0
    
    def _calculate_performance_metrics(self, portfolio_series: pd.Series, trades: List[Trade], 
                                     benchmark_return: float, strategy_name: str) -> BacktestResult:
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
            trades=[trade.__dict__ for trade in trades],
            benchmark_return=benchmark_return
        )
    
    def run_comprehensive_backtest(self) -> Dict[str, BacktestResult]:
        """Run backtests for all execution strategies"""
        
        # Download all data first
        self.download_all_data()
        
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
            except Exception as e:
                self.logger.error(f"Failed backtest for {strategy_name}: {e}")
        
        return results
    
    def generate_report(self, results: Dict[str, BacktestResult], save_path: str = None):
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
        best_strategy = max(results.items(), key=lambda x: x[1].sharpe_ratio)
        print(f"\nBEST STRATEGY (by Sharpe Ratio): {best_strategy[0]}")
        print(f"  Sharpe Ratio: {best_strategy[1].sharpe_ratio:.2f}")
        print(f"  Total Return: {best_strategy[1].total_return:.2%}")
        print(f"  Max Drawdown: {best_strategy[1].max_drawdown:.2%}")
        
        # Create visualizations
        self._create_visualizations(results, save_path)
        
        # Save detailed results
        if save_path:
            summary_df.to_csv(f"{save_path}_summary.csv", index=False)
            with open(f"{save_path}_detailed.json", 'w') as f:
                detailed_results = {}
                for name, result in results.items():
                    detailed_results[name] = {
                        'metrics': {
                            'total_return': result.total_return,
                            'annual_return': result.annual_return,
                            'sharpe_ratio': result.sharpe_ratio,
                            'max_drawdown': result.max_drawdown,
                            'win_rate': result.win_rate,
                            'total_trades': result.total_trades,
                            'benchmark_return': result.benchmark_return
                        },
                        'portfolio_values': result.portfolio_values.to_dict(),
                        'trades': result.trades
                    }
                json.dump(detailed_results, f, indent=2, default=str)
            
            self.logger.info(f"Results saved to {save_path}_summary.csv and {save_path}_detailed.json")
    
    def _create_visualizations(self, results: Dict[str, BacktestResult], save_path: str = None):
        """Create performance visualizations"""
        
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
        colors = plt.cm.Set3(np.linspace(0, 1, len(strategies)))
        bars = ax2.bar(strategies, returns, color=colors)
        ax2.set_title('Total Returns by Strategy')
        ax2.set_ylabel('Total Return')
        ax2.tick_params(axis='x', rotation=45)
        
        # Add benchmark line
        benchmark_return = list(results.values())[0].benchmark_return
        ax2.axhline(y=benchmark_return, color='red', linestyle='--', label=f'SPY Benchmark ({benchmark_return:.2%})')
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
        bars = ax4.bar(strategies, drawdowns, color=colors)
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
    else:
        print("❌ No backtest results generated")

if __name__ == "__main__":
    main()
