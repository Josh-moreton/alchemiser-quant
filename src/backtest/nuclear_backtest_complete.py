#!/usr/bin/env python3
"""
Nuclear Backtest Complete - Phase 4 Final Integration
Complete backtesting system combining all components for comprehensive analysis
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Optional
import logging
import json
from datetime import datetime

from nuclear_backtest_framework import BacktestDataProvider, BacktestNuclearStrategy
from signal_analyzer import SignalAnalyzer
from execution_engine import ExecutionEngine, BacktestRunner

class ComprehensiveBacktester:
    """
    Complete nuclear energy strategy backtesting system
    Integrates signal analysis, execution engine, and performance reporting
    """
    
    def __init__(self, start_date: str, end_date: str, initial_capital: float = 100000):
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.logger = logging.getLogger(__name__)
        
        # Results storage
        self.results = {}
        self.benchmark_results = {}
        
    def run_comprehensive_analysis(self) -> Dict:
        """
        Run complete backtesting analysis including:
        1. Signal pattern analysis
        2. Multiple execution strategies
        3. Benchmark comparisons
        4. Performance analytics
        5. Risk metrics
        """
        
        print("🚀 NUCLEAR ENERGY STRATEGY - COMPREHENSIVE BACKTEST")
        print("=" * 60)
        print(f"Period: {self.start_date} to {self.end_date}")
        print(f"Initial Capital: ${self.initial_capital:,}")
        print()
        
        # Phase 1: Signal Analysis
        print("📊 Phase 1: Signal Pattern Analysis")
        signal_results = self._analyze_signals()
        print(f"✅ Generated {len(signal_results['signals'])} signals")
        print()
        
        # Phase 2: Execution Strategy Testing
        print("⚡ Phase 2: Execution Strategy Testing")
        execution_results = self._test_execution_strategies()
        print("✅ Tested all execution strategies")
        print()
        
        # Phase 3: Benchmark Analysis
        print("📈 Phase 3: Benchmark Comparison")
        benchmark_results = self._run_benchmarks()
        print("✅ Calculated benchmark performance")
        print()
        
        # Phase 4: Risk Analysis
        print("⚠️  Phase 4: Risk Analysis")
        risk_metrics = self._calculate_risk_metrics()
        print("✅ Calculated risk metrics")
        print()
        
        # Phase 5: Generate Report
        print("📑 Phase 5: Generate Comprehensive Report")
        report = self._generate_report(signal_results, execution_results, benchmark_results, risk_metrics)
        print("✅ Report generated")
        
        return report
    
    def _analyze_signals(self) -> Dict:
        """Analyze signal patterns using SignalAnalyzer"""
        analyzer = SignalAnalyzer(self.start_date, self.end_date)
        
        # Generate signals for the entire period
        signals = analyzer.generate_daily_signals()
        
        # Find signal changes
        changes = analyzer.find_signal_changes(signals)
        
        # Analyze signal persistence
        persistence = analyzer.analyze_signal_persistence(signals)
        
        return {
            'signals': signals,
            'changes': changes,
            'persistence': persistence,
            'summary': self._summarize_signals(signals)
        }
    
    def _summarize_signals(self, signals: List[Dict]) -> Dict:
        """Summarize signal patterns"""
        if not signals:
            return {'total_days': 0, 'nuclear_days': 0, 'nuclear_rate': 0.0}
        
        total_days = len(signals)
        nuclear_days = sum(1 for s in signals if s['signal'] == 'NUCLEAR_PORTFOLIO')
        nuclear_rate = nuclear_days / total_days if total_days > 0 else 0.0
        
        return {
            'total_days': total_days,
            'nuclear_days': nuclear_days,
            'nuclear_rate': nuclear_rate
        }
    
    def _test_execution_strategies(self) -> Dict:
        """Test different execution timing strategies"""
        strategies = ['market_close', 'market_open', 'hourly_average']
        results = {}
        
        for strategy in strategies:
            print(f"  Testing {strategy} execution...")
            runner = BacktestRunner(self.start_date, self.end_date, self.initial_capital)
            
            try:
                result = runner.run_backtest(execution_type=strategy)
                results[strategy] = result
                
                metrics = result['performance_metrics']
                print(f"    {strategy}: {metrics['total_return']:.1%} return, {metrics['number_of_trades']} trades")
                
            except Exception as e:
                self.logger.error(f"Error testing {strategy}: {e}")
                continue
        
        return results
    
    def _run_benchmarks(self) -> Dict:
        """Run benchmark comparisons (Buy & Hold strategies)"""
        benchmarks = {
            'SPY': 'S&P 500 ETF',
            'QQQ': 'NASDAQ 100 ETF', 
            'UPRO': '3x Leveraged S&P 500',
            'TQQQ': '3x Leveraged NASDAQ',
            'SMR': 'NuScale Power (Nuclear)',
            'NUCLEAR_EQUAL': 'Equal Weight Nuclear Portfolio'
        }
        
        data_provider = BacktestDataProvider(self.start_date, self.end_date)
        strategy = BacktestNuclearStrategy(data_provider)
        all_data = data_provider.download_all_data(strategy.all_symbols)
        
        results = {}
        
        for symbol, description in benchmarks.items():
            if symbol == 'NUCLEAR_EQUAL':
                # Special case: equal weight nuclear portfolio
                nuclear_symbols = ['SMR', 'LEU', 'OKLO', 'BWXT', 'EXC']
                results[symbol] = self._calculate_equal_weight_return(nuclear_symbols, all_data)
            else:
                # Single asset buy & hold
                if symbol in all_data:
                    results[symbol] = self._calculate_buy_hold_return(symbol, all_data[symbol])
        
        return results
    
    def _calculate_buy_hold_return(self, symbol: str, data: pd.DataFrame) -> Dict:
        """Calculate buy & hold return for a single asset"""
        start_date = pd.Timestamp(self.start_date)
        end_date = pd.Timestamp(self.end_date)
        
        # Filter data to backtest period
        period_data = data[(data.index >= start_date) & (data.index <= end_date)]
        
        if len(period_data) < 2:
            return {'total_return': 0.0, 'error': 'Insufficient data'}
        
        start_price = period_data['Close'].iloc[0]
        end_price = period_data['Close'].iloc[-1]
        
        total_return = (end_price - start_price) / start_price
        
        # Calculate additional metrics
        daily_returns = period_data['Close'].pct_change().dropna()
        volatility = daily_returns.std() * np.sqrt(252)
        sharpe = (daily_returns.mean() * 252) / (volatility) if volatility > 0 else 0
        max_drawdown = self._calculate_max_drawdown(period_data['Close'])
        
        return {
            'total_return': total_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_drawdown,
            'start_price': start_price,
            'end_price': end_price
        }
    
    def _calculate_equal_weight_return(self, symbols: List[str], all_data: Dict) -> Dict:
        """Calculate equal weight portfolio return"""
        start_date = pd.Timestamp(self.start_date)
        end_date = pd.Timestamp(self.end_date)
        
        portfolio_values = []
        dates = None
        
        for symbol in symbols:
            if symbol in all_data:
                data = all_data[symbol]
                period_data = data[(data.index >= start_date) & (data.index <= end_date)]
                
                if not period_data.empty:
                    if dates is None:
                        dates = period_data.index
                    
                    # Normalize to start at 1.0
                    normalized_values = period_data['Close'] / period_data['Close'].iloc[0]
                    portfolio_values.append(normalized_values.reindex(dates, method='ffill'))
        
        if not portfolio_values:
            return {'total_return': 0.0, 'error': 'No data available'}
        
        # Average all normalized values (equal weight)
        portfolio_df = pd.DataFrame(portfolio_values).T
        portfolio_series = portfolio_df.mean(axis=1)
        
        total_return = portfolio_series.iloc[-1] - 1.0
        
        # Calculate metrics
        daily_returns = portfolio_series.pct_change().dropna()
        volatility = daily_returns.std() * np.sqrt(252)
        sharpe = (daily_returns.mean() * 252) / volatility if volatility > 0 else 0
        max_drawdown = self._calculate_max_drawdown(portfolio_series)
        
        return {
            'total_return': total_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_drawdown
        }
    
    def _calculate_max_drawdown(self, price_series: pd.Series) -> float:
        """Calculate maximum drawdown"""
        cumulative = (1 + price_series.pct_change()).cumprod()
        rolling_max = cumulative.expanding().max()
        drawdown = (cumulative - rolling_max) / rolling_max
        return drawdown.min()
    
    def _calculate_risk_metrics(self) -> Dict:
        """Calculate comprehensive risk metrics"""
        # Use the best execution strategy results
        if not hasattr(self, 'results') or not self.results:
            return {}
        
        # Find best strategy
        best_strategy = None
        best_return = -float('inf')
        
        for strategy_name, results in self.results.items():
            if 'performance_metrics' in results:
                strategy_return = results['performance_metrics']['total_return']
                if strategy_return > best_return:
                    best_return = strategy_return
                    best_strategy = strategy_name
        
        if not best_strategy:
            return {}
        
        best_results = self.results[best_strategy]
        portfolio_history = best_results['portfolio_history']
        
        if not portfolio_history:
            return {}
        
        # Convert to DataFrame
        df = pd.DataFrame(portfolio_history)
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')
        
        # Calculate daily returns
        daily_returns = df['portfolio_value'].pct_change().dropna()
        
        # Risk metrics
        volatility = daily_returns.std() * np.sqrt(252)
        sharpe_ratio = (daily_returns.mean() * 252) / volatility if volatility > 0 else 0
        max_drawdown = self._calculate_max_drawdown(df['portfolio_value'])
        
        # Win rate
        winning_days = (daily_returns > 0).sum()
        total_days = len(daily_returns)
        win_rate = winning_days / total_days if total_days > 0 else 0
        
        # Value at Risk (95%)
        var_95 = daily_returns.quantile(0.05)
        
        return {
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'var_95': var_95,
            'best_day': daily_returns.max(),
            'worst_day': daily_returns.min(),
            'total_trading_days': total_days
        }
    
    def _generate_report(self, signals: Dict, execution: Dict, benchmarks: Dict, risk: Dict) -> Dict:
        """Generate comprehensive performance report"""
        
        # Find best execution strategy
        best_strategy = None
        best_metrics = None
        best_return = -float('inf')
        
        for strategy_name, results in execution.items():
            metrics = results['performance_metrics']
            if metrics['total_return'] > best_return:
                best_return = metrics['total_return']
                best_strategy = strategy_name
                best_metrics = metrics
        
        # Store results for risk calculation
        self.results = execution
        
        print("🎯 COMPREHENSIVE BACKTEST RESULTS")
        print("=" * 50)
        
        if best_strategy and best_metrics:
            # Strategy Performance
            print("\n📊 STRATEGY PERFORMANCE")
            print(f"Best Execution Strategy: {best_strategy.upper()}")
            print(f"Total Return: {best_metrics['total_return']:.2%}")
            print(f"Final Portfolio Value: ${best_metrics['current_value']:,.0f}")
            print(f"Total Transaction Costs: ${best_metrics['total_costs']:.2f}")
            print(f"Number of Trades: {best_metrics['number_of_trades']}")
        else:
            print("\n❌ No execution results available")
            return {}
        
        # Signal Analysis
        print("\n📈 SIGNAL ANALYSIS")
        signal_summary = signals['summary']
        print(f"Total Trading Days: {signal_summary['total_days']}")
        print(f"Nuclear Portfolio Days: {signal_summary['nuclear_days']} ({signal_summary['nuclear_rate']:.1%})")
        print(f"Signal Changes: {len(signals['changes'])}")
        
        # Risk Metrics
        if risk:
            print("\n⚠️  RISK ANALYSIS")
            print(f"Volatility: {risk['volatility']:.1%}")
            print(f"Sharpe Ratio: {risk['sharpe_ratio']:.2f}")
            print(f"Maximum Drawdown: {risk['max_drawdown']:.1%}")
            print(f"Win Rate: {risk['win_rate']:.1%}")
        
        # Benchmark Comparison
        print("\n🏆 BENCHMARK COMPARISON")
        strategy_return = best_metrics['total_return']
        
        for benchmark, metrics in benchmarks.items():
            if 'error' not in metrics:
                benchmark_return = metrics['total_return']
                excess_return = strategy_return - benchmark_return
                print(f"{benchmark}: {benchmark_return:.1%} (Strategy +{excess_return:.1%})")
        
        # Execution Strategy Comparison
        print("\n⚡ EXECUTION STRATEGY COMPARISON")
        for strategy_name, results in execution.items():
            metrics = results['performance_metrics']
            marker = "👑" if strategy_name == best_strategy else "  "
            print(f"{marker} {strategy_name}: {metrics['total_return']:.1%} return, ${metrics['total_costs']:.0f} costs")
        
        return {
            'strategy_performance': best_metrics,
            'best_execution': best_strategy,
            'signal_analysis': signals,
            'execution_comparison': execution,
            'benchmark_comparison': benchmarks,
            'risk_metrics': risk,
            'summary': {
                'total_return': best_metrics['total_return'] if best_metrics else 0.0,
                'sharpe_ratio': risk.get('sharpe_ratio', 0.0),
                'max_drawdown': risk.get('max_drawdown', 0.0),
                'win_rate': risk.get('win_rate', 0.0)
            }
        }
    
    def save_results(self, filename: Optional[str] = None):
        """Save results to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data/backtest_results/nuclear_backtest_results_{timestamp}.json"
        
        # Convert results to JSON-serializable format
        json_results = self._convert_to_json_serializable(self.results)
        
        with open(filename, 'w') as f:
            json.dump(json_results, f, indent=2, default=str)
        
        print(f"💾 Results saved to: {filename}")

    def _convert_to_json_serializable(self, obj):
        """Convert pandas/numpy objects to JSON serializable format"""
        if isinstance(obj, dict):
            return {k: self._convert_to_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_to_json_serializable(item) for item in obj]
        elif isinstance(obj, (pd.Timestamp, pd.DatetimeIndex)):
            return str(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.integer, np.floating)):
            return float(obj)
        else:
            return obj

def run_full_backtest():
    """Run the complete nuclear energy strategy backtest"""
    
    # Test parameters - you can modify these
    START_DATE = '2024-10-01'
    END_DATE = '2024-12-31'
    INITIAL_CAPITAL = 100000
    
    # Initialize comprehensive backtester
    backtester = ComprehensiveBacktester(START_DATE, END_DATE, INITIAL_CAPITAL)
    
    # Run complete analysis
    results = backtester.run_comprehensive_analysis()
    
    # Save results
    backtester.save_results()
    
    print("\n🎉 BACKTEST COMPLETE!")
    print("All analysis phases completed successfully.")
    
    return results

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.WARNING,  # Reduce noise for final run
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Run the complete backtest
    results = run_full_backtest()
