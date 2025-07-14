#!/usr/bin/env python3
"""
Comprehensive Nuclear Strategy Backtest Report
Using optimal 9:30 AM execution timing with real hourly data
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
import warnings
import json
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
warnings.filterwarnings('ignore')

from nuclear_backtest_framework import BacktestDataProvider, BacktestNuclearStrategy, PortfolioBuilder
from hourly_execution_engine import HourlyExecutionEngine

class ComprehensiveBacktestReporter:
    """
    Generate comprehensive backtest report with all key performance metrics
    """
    
    def __init__(self, start_date: str, end_date: str, initial_capital: float = 100000):
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.logger = logging.getLogger(__name__)
        
        # Benchmark symbols for comparison
        self.benchmarks = ['SPY', 'QQQ', 'TLT', 'IEF']
        
        # Risk-free rate (approximate 10-year treasury)
        self.risk_free_rate = 0.045  # 4.5% annual
        
    def run_comprehensive_backtest(self) -> Dict:
        """Run comprehensive backtest with detailed metrics"""
        
        print("🚀 COMPREHENSIVE NUCLEAR STRATEGY BACKTEST")
        print("=" * 60)
        print(f"Period: {self.start_date} to {self.end_date}")
        print(f"Initial Capital: ${self.initial_capital:,.2f}")
        print(f"Execution: 9:30 AM (Market Open) - Real Hourly Data")
        print()
        
        # 1. Run optimal hourly execution (9:30 AM)
        hourly_engine = HourlyExecutionEngine(self.start_date, self.end_date, self.initial_capital)
        
        # Get the 9:30 AM results specifically
        print("📊 Running Nuclear Strategy at Optimal Time (9:30 AM)...")
        nuclear_result = hourly_engine._run_hourly_backtest(9, '09:30')
        
        # 2. Calculate benchmark performance
        print("📈 Calculating Benchmark Performance...")
        benchmark_results = self._calculate_benchmark_performance()
        
        # 3. Generate comprehensive metrics
        print("🔢 Calculating Performance Metrics...")
        performance_metrics = self._calculate_comprehensive_metrics(nuclear_result)
        
        # 4. Trade analysis
        trade_analysis = self._analyze_trades(nuclear_result['transaction_log'])
        
        # 5. Portfolio composition analysis
        portfolio_analysis = self._analyze_portfolio_composition(nuclear_result)
        
        # 6. Risk metrics
        risk_metrics = self._calculate_risk_metrics(nuclear_result, benchmark_results)
        
        # 7. Generate report
        report = {
            'execution_summary': {
                'start_date': self.start_date,
                'end_date': self.end_date,
                'initial_capital': self.initial_capital,
                'execution_time': '09:30 AM',
                'used_hourly_data': nuclear_result.get('used_hourly_data', False),
                'total_trading_days': len(nuclear_result['portfolio_history'])
            },
            'performance_metrics': performance_metrics,
            'benchmark_comparison': benchmark_results,
            'risk_metrics': risk_metrics,
            'trade_analysis': trade_analysis,
            'portfolio_analysis': portfolio_analysis,
            'nuclear_result': nuclear_result
        }
        
        # 8. Display comprehensive report
        self._display_comprehensive_report(report)
        
        # 9. Save detailed results
        self._save_detailed_results(report)
        
        return report
    
    def _calculate_benchmark_performance(self) -> Dict:
        """Calculate benchmark performance for comparison"""
        data_provider = BacktestDataProvider(self.start_date, self.end_date)
        
        benchmark_results = {}
        
        for symbol in self.benchmarks:
            try:
                # Get benchmark data
                data = data_provider.download_all_data([symbol])[symbol]
                start_dt = pd.Timestamp(self.start_date)
                end_dt = pd.Timestamp(self.end_date)
                
                # Filter to backtest period
                period_data = data[(data.index >= start_dt) & (data.index <= end_dt)]
                
                if len(period_data) > 0:
                    start_price = period_data.iloc[0]['Close']
                    end_price = period_data.iloc[-1]['Close']
                    total_return = (end_price - start_price) / start_price
                    
                    # Calculate daily returns for additional metrics
                    daily_returns = period_data['Close'].pct_change().dropna()
                    
                    benchmark_results[symbol] = {
                        'total_return': total_return,
                        'start_price': start_price,
                        'end_price': end_price,
                        'daily_returns': daily_returns,
                        'volatility': daily_returns.std() * np.sqrt(252),  # Annualized
                        'sharpe_ratio': (daily_returns.mean() * 252 - self.risk_free_rate) / (daily_returns.std() * np.sqrt(252))
                    }
                    
            except Exception as e:
                self.logger.warning(f"Error calculating benchmark for {symbol}: {e}")
                
        return benchmark_results
    
    def _calculate_comprehensive_metrics(self, nuclear_result: Dict) -> Dict:
        """Calculate comprehensive performance metrics"""
        
        portfolio_history = nuclear_result['portfolio_history']
        if not portfolio_history:
            return {}
            
        # Convert to DataFrame for easier analysis
        df = pd.DataFrame(portfolio_history)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # Calculate returns
        df['daily_return'] = df['portfolio_value'].pct_change().fillna(0)
        df['cumulative_return'] = (df['portfolio_value'] / self.initial_capital) - 1
        
        # Basic metrics
        final_value = df['portfolio_value'].iloc[-1]
        total_return = (final_value - self.initial_capital) / self.initial_capital
        
        # Time period
        start_date = df['date'].iloc[0]
        end_date = df['date'].iloc[-1]
        total_days = (end_date - start_date).days
        total_years = total_days / 365.25
        
        # CAGR
        cagr = (final_value / self.initial_capital) ** (1 / total_years) - 1
        
        # Volatility (annualized)
        daily_returns = df['daily_return'].dropna()
        volatility = daily_returns.std() * np.sqrt(252)
        
        # Sharpe Ratio
        excess_return = daily_returns.mean() * 252 - self.risk_free_rate
        sharpe_ratio = excess_return / volatility if volatility > 0 else 0
        
        # Sortino Ratio (downside deviation)
        downside_returns = daily_returns[daily_returns < 0]
        downside_deviation = downside_returns.std() * np.sqrt(252)
        sortino_ratio = excess_return / downside_deviation if downside_deviation > 0 else 0
        
        # Maximum Drawdown
        df['peak'] = df['portfolio_value'].expanding(min_periods=1).max()
        df['drawdown'] = (df['portfolio_value'] - df['peak']) / df['peak']
        max_drawdown = df['drawdown'].min()
        
        # Maximum Drawdown Duration
        df['is_peak'] = df['portfolio_value'] == df['peak']
        drawdown_periods = []
        current_dd_start = None
        
        for idx, row in enumerate(df.itertuples()):
            if row.is_peak and current_dd_start is not None:
                # End of drawdown
                drawdown_periods.append(idx - current_dd_start)
                current_dd_start = None
            elif not row.is_peak and current_dd_start is None:
                # Start of drawdown
                current_dd_start = idx
                
        max_dd_duration = max(drawdown_periods) if drawdown_periods else 0
        
        # Win Rate
        winning_days = len(daily_returns[daily_returns > 0])
        total_trading_days = len(daily_returns)
        win_rate = winning_days / total_trading_days if total_trading_days > 0 else 0
        
        # Best and Worst Days
        best_day_return = daily_returns.max()
        worst_day_return = daily_returns.min()
        
        # Calmar Ratio (CAGR / Max Drawdown)
        calmar_ratio = abs(cagr / max_drawdown) if max_drawdown != 0 else 0
        
        return {
            'total_return': total_return,
            'cagr': cagr,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'max_drawdown': max_drawdown,
            'max_drawdown_duration_days': max_dd_duration,
            'calmar_ratio': calmar_ratio,
            'win_rate': win_rate,
            'best_day_return': best_day_return,
            'worst_day_return': worst_day_return,
            'final_value': final_value,
            'total_days': total_days,
            'total_years': total_years,
            'trading_days': total_trading_days
        }
    
    def _analyze_trades(self, transaction_log: List[Dict]) -> Dict:
        """Analyze trading patterns and performance"""
        
        if not transaction_log:
            return {'total_trades': 0}
            
        trades_df = pd.DataFrame(transaction_log)
        
        # Basic trade statistics
        total_trades = len(trades_df)
        total_costs = trades_df['costs'].sum()
        
        # Trades by symbol
        trades_by_symbol = trades_df.groupby('symbol').agg({
            'shares': 'sum',
            'trade_value': 'sum',
            'costs': 'sum'
        }).sort_values('trade_value', key=abs, ascending=False)
        
        # Monthly trade frequency
        trades_df['date'] = pd.to_datetime(trades_df['date'])
        trades_df['month'] = trades_df['date'].dt.to_period('M')
        monthly_trades = trades_df.groupby('month').size()
        
        # Long vs Short positions
        long_trades = trades_df[trades_df['shares'] > 0]
        short_trades = trades_df[trades_df['shares'] < 0]
        
        return {
            'total_trades': total_trades,
            'total_costs': total_costs,
            'avg_cost_per_trade': total_costs / total_trades if total_trades > 0 else 0,
            'long_trades': len(long_trades),
            'short_trades': len(short_trades),
            'avg_monthly_trades': monthly_trades.mean(),
            'trades_by_symbol': trades_by_symbol.to_dict('index'),
            'largest_trade_value': abs(trades_df['trade_value']).max(),
            'smallest_trade_value': abs(trades_df['trade_value']).min()
        }
    
    def _analyze_portfolio_composition(self, nuclear_result: Dict) -> Dict:
        """Analyze portfolio composition and allocations"""
        
        portfolio_history = nuclear_result['portfolio_history']
        final_positions = nuclear_result['final_positions']
        
        if not portfolio_history:
            return {}
            
        # Get final portfolio value
        final_portfolio_value = portfolio_history[-1]['portfolio_value']
        final_cash = portfolio_history[-1]['cash']
        
        # Calculate final allocation percentages
        position_values = {}
        data_provider = BacktestDataProvider(self.start_date, self.end_date)
        
        for symbol, shares in final_positions.items():
            # Get final price
            price = data_provider.get_price_at_time(symbol, pd.Timestamp(self.end_date), 'Close')
            if price and shares != 0:
                position_values[symbol] = shares * price
        
        # Calculate allocations
        allocations = {}
        for symbol, value in position_values.items():
            allocations[symbol] = value / final_portfolio_value
            
        cash_allocation = final_cash / final_portfolio_value
        
        # Signal analysis
        signal_history = nuclear_result['signal_history']
        signals_df = pd.DataFrame(signal_history)
        
        signal_counts = signals_df['signal'].value_counts() if not signals_df.empty else pd.Series()
        action_counts = signals_df['action'].value_counts() if not signals_df.empty else pd.Series()
        
        return {
            'final_positions': final_positions,
            'position_values': position_values,
            'allocations': allocations,
            'cash_allocation': cash_allocation,
            'final_cash': final_cash,
            'signal_distribution': signal_counts.to_dict() if len(signal_counts) > 0 else {},
            'action_distribution': action_counts.to_dict() if len(action_counts) > 0 else {},
            'number_of_positions': len([v for v in final_positions.values() if abs(v) > 0.01])
        }
    
    def _calculate_risk_metrics(self, nuclear_result: Dict, benchmark_results: Dict) -> Dict:
        """Calculate additional risk metrics"""
        
        portfolio_history = nuclear_result['portfolio_history']
        if not portfolio_history:
            return {}
            
        df = pd.DataFrame(portfolio_history)
        df['daily_return'] = df['portfolio_value'].pct_change().fillna(0)
        daily_returns = df['daily_return'].dropna()
        
        # Value at Risk (VaR) - 5% and 1%
        var_5 = np.percentile(daily_returns, 5)
        var_1 = np.percentile(daily_returns, 1)
        
        # Conditional Value at Risk (CVaR)
        cvar_5 = daily_returns[daily_returns <= var_5].mean()
        cvar_1 = daily_returns[daily_returns <= var_1].mean()
        
        # Beta calculation (vs SPY if available)
        beta = None
        correlation_spy = None
        if 'SPY' in benchmark_results:
            spy_returns = benchmark_results['SPY']['daily_returns']
            # Align dates
            common_dates = daily_returns.index.intersection(spy_returns.index)
            if len(common_dates) > 10:
                strategy_aligned = daily_returns.loc[common_dates]
                spy_aligned = spy_returns.loc[common_dates]
                
                correlation_spy = strategy_aligned.corr(spy_aligned)
                beta = strategy_aligned.cov(spy_aligned) / spy_aligned.var()
        
        # Information Ratio (vs SPY)
        information_ratio = None
        if 'SPY' in benchmark_results and correlation_spy is not None:
            excess_returns = daily_returns.mean() * 252 - benchmark_results['SPY']['total_return']
            tracking_error = (daily_returns - benchmark_results['SPY']['daily_returns'].reindex(daily_returns.index, fill_value=0)).std() * np.sqrt(252)
            information_ratio = excess_returns / tracking_error if tracking_error > 0 else 0
        
        return {
            'var_5_percent': var_5,
            'var_1_percent': var_1,
            'cvar_5_percent': cvar_5,
            'cvar_1_percent': cvar_1,
            'beta_vs_spy': beta,
            'correlation_vs_spy': correlation_spy,
            'information_ratio_vs_spy': information_ratio
        }
    
    def _display_comprehensive_report(self, report: Dict):
        """Display comprehensive backtest report"""
        
        perf = report['performance_metrics']
        trade = report['trade_analysis']
        portfolio = report['portfolio_analysis']
        risk = report['risk_metrics']
        
        print("\n" + "="*80)
        print("📈 NUCLEAR STRATEGY COMPREHENSIVE BACKTEST REPORT")
        print("="*80)
        
        # Executive Summary
        print(f"\n🎯 EXECUTIVE SUMMARY")
        print(f"{'─'*40}")
        print(f"Total Return:      {perf['total_return']:+8.2%}")
        print(f"CAGR:              {perf['cagr']:+8.2%}")
        print(f"Sharpe Ratio:      {perf['sharpe_ratio']:8.2f}")
        print(f"Max Drawdown:      {perf['max_drawdown']:8.2%}")
        print(f"Win Rate:          {perf['win_rate']:8.2%}")
        
        # Performance Metrics
        print(f"\n📊 PERFORMANCE METRICS")
        print(f"{'─'*40}")
        print(f"Initial Capital:   ${self.initial_capital:>12,.2f}")
        print(f"Final Value:       ${perf['final_value']:>12,.2f}")
        print(f"Total Return:      {perf['total_return']:>12.2%}")
        print(f"CAGR:              {perf['cagr']:>12.2%}")
        print(f"Volatility:        {perf['volatility']:>12.2%}")
        print(f"Best Day:          {perf['best_day_return']:>12.2%}")
        print(f"Worst Day:         {perf['worst_day_return']:>12.2%}")
        
        # Risk Metrics
        print(f"\n⚠️  RISK METRICS")
        print(f"{'─'*40}")
        print(f"Sharpe Ratio:      {perf['sharpe_ratio']:>12.2f}")
        print(f"Sortino Ratio:     {perf['sortino_ratio']:>12.2f}")
        print(f"Calmar Ratio:      {perf['calmar_ratio']:>12.2f}")
        print(f"Max Drawdown:      {perf['max_drawdown']:>12.2%}")
        print(f"Max DD Duration:   {perf['max_drawdown_duration_days']:>9.0f} days")
        print(f"VaR (5%):          {risk.get('var_5_percent', 0):>12.2%}")
        print(f"CVaR (5%):         {risk.get('cvar_5_percent', 0):>12.2%}")
        if risk.get('beta_vs_spy'):
            print(f"Beta vs SPY:       {risk['beta_vs_spy']:>12.2f}")
            print(f"Correlation SPY:   {risk['correlation_vs_spy']:>12.2f}")
        
        # Trading Activity
        print(f"\n🔄 TRADING ACTIVITY")
        print(f"{'─'*40}")
        print(f"Total Trades:      {trade['total_trades']:>12,}")
        print(f"Long Trades:       {trade['long_trades']:>12,}")
        print(f"Short Trades:      {trade['short_trades']:>12,}")
        print(f"Total Costs:       ${trade['total_costs']:>11,.2f}")
        print(f"Avg Cost/Trade:    ${trade['avg_cost_per_trade']:>11,.2f}")
        print(f"Monthly Avg:       {trade['avg_monthly_trades']:>12.1f}")
        
        # Portfolio Composition
        print(f"\n💼 FINAL PORTFOLIO COMPOSITION")
        print(f"{'─'*40}")
        print(f"Cash Allocation:   {portfolio['cash_allocation']:>12.2%}")
        print(f"Active Positions:  {portfolio['number_of_positions']:>12,}")
        
        if portfolio['allocations']:
            print(f"\nTop Holdings:")
            sorted_allocations = sorted(portfolio['allocations'].items(), 
                                      key=lambda x: abs(x[1]), reverse=True)
            for symbol, allocation in sorted_allocations[:10]:
                print(f"  {symbol:6s}: {allocation:>8.2%}")
        
        # Benchmark Comparison
        if report['benchmark_comparison']:
            print(f"\n📈 BENCHMARK COMPARISON")
            print(f"{'─'*40}")
            print(f"{'Strategy':>12s}: {perf['total_return']:>8.2%}")
            
            for symbol, benchmark in report['benchmark_comparison'].items():
                print(f"{symbol:>12s}: {benchmark['total_return']:>8.2%}")
        
        # Signal Analysis
        if portfolio['signal_distribution']:
            print(f"\n🎯 SIGNAL DISTRIBUTION")
            print(f"{'─'*40}")
            for signal, count in portfolio['signal_distribution'].items():
                print(f"{signal:>12s}: {count:>8,} days")
                
    def _save_detailed_results(self, report: Dict):
        """Save detailed results to files"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save main report
        report_file = f'data/backtest_results/nuclear_comprehensive_report_{timestamp}.json'
        
        # Convert non-serializable objects
        serializable_report = self._make_serializable(report)
        
        with open(report_file, 'w') as f:
            json.dump(serializable_report, f, indent=2, default=str)
        
        print(f"\n💾 REPORT SAVED")
        print(f"{'─'*40}")
        print(f"Detailed Report: {report_file}")
        
        # Save trade log as CSV
        if report['nuclear_result']['transaction_log']:
            trades_df = pd.DataFrame(report['nuclear_result']['transaction_log'])
            trades_file = f'data/backtest_results/nuclear_trades_{timestamp}.csv'
            trades_df.to_csv(trades_file, index=False)
            print(f"Trade Log:       {trades_file}")
        
        # Save portfolio history
        if report['nuclear_result']['portfolio_history']:
            portfolio_df = pd.DataFrame(report['nuclear_result']['portfolio_history'])
            portfolio_file = f'data/backtest_results/nuclear_portfolio_{timestamp}.csv'
            portfolio_df.to_csv(portfolio_file, index=False)
            print(f"Portfolio Data:  {portfolio_file}")
    
    def _make_serializable(self, obj):
        """Convert objects to JSON-serializable format"""
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(v) for v in obj]
        elif isinstance(obj, (pd.Series, pd.DataFrame)):
            return obj.to_dict()
        elif isinstance(obj, (pd.Timestamp, datetime)):
            return obj.isoformat()
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return obj

def run_comprehensive_nuclear_backtest():
    """Run comprehensive nuclear strategy backtest"""
    
    # Test parameters - 3 months of data
    START_DATE = '2024-07-01'
    END_DATE = '2024-09-30'
    INITIAL_CAPITAL = 100000
    
    # Setup logging
    logging.basicConfig(
        level=logging.WARNING,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Run comprehensive backtest
    reporter = ComprehensiveBacktestReporter(START_DATE, END_DATE, INITIAL_CAPITAL)
    results = reporter.run_comprehensive_backtest()
    
    return results

if __name__ == "__main__":
    results = run_comprehensive_nuclear_backtest()
    print(f"\n✅ Comprehensive backtest completed successfully!")
