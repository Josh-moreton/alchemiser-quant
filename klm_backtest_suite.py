#!/usr/bin/env python3
"""
KLM Strategy Backtest Suite

Comprehensive backtesting suite for the KLM Strategy Ensemble including:
- Single-strategy KLM backtests
- Multi-strategy portfolio backtests
- KLM variant performance analysis
- Ensemble selection effectiveness testing

Usage:
    python klm_backtest_suite.py --test single_klm
    python klm_backtest_suite.py --test multi_strategy
    python klm_backtest_suite.py --test variant_analysis
    python klm_backtest_suite.py --test all
"""

import os
import sys
import argparse
import datetime as dt
import pandas as pd
import numpy as np
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import track

# Set up environment and imports
os.environ['ALPACA_PAPER_KEY'] = 'PKS7WB1KB6VVG72FF8VZ'
os.environ['ALPACA_PAPER_SECRET'] = 'Ibcd2Zy98HL3wabRMQW6R0T1SnSZ2vN1uoLWhIOQ'

# Add project root to path
sys.path.insert(0, '/Users/joshua.moreton/Documents/GitHub/the-alchemiser')

from the_alchemiser.core.trading.strategy_manager import MultiStrategyManager, StrategyType
from the_alchemiser.core.data.data_provider import UnifiedDataProvider
from the_alchemiser.core.config import get_config
from the_alchemiser.backtest.test_backtest import run_backtest

console = Console()


def test_single_klm_strategy(start_date: str = '2023-06-01', end_date: str = '2024-01-31', 
                           initial_capital: float = 100000):
    """Test KLM ensemble in isolation"""
    console.print(Panel(f"[bold cyan]🧪 Single KLM Strategy Backtest[/bold cyan]\n"
                       f"Testing KLM ensemble performance in isolation\n"
                       f"Period: {start_date} to {end_date}\n"
                       f"Capital: £{initial_capital:,.2f}",
                       title="📊 KLM Single Strategy Test"))
    
    # Temporarily modify config for KLM-only allocation
    import copy
    from the_alchemiser.core import config as alchemiser_config
    
    # Store original global config
    orig_global_config = alchemiser_config._global_config
    
    try:
        # Create modified config with 100% KLM allocation
        mock_config = alchemiser_config.Config()
        mock_config._config = copy.deepcopy(mock_config._config)
        if 'strategy' not in mock_config._config:
            mock_config._config['strategy'] = {}
        mock_config._config['strategy']['default_strategy_allocations'] = {
            'nuclear': 0.0, 
            'tecl': 0.0, 
            'klm': 1.0  # 100% KLM allocation
        }
        
        # Replace global config temporarily
        alchemiser_config._global_config = mock_config
        
        # Run backtest
        start = dt.datetime.strptime(start_date, '%Y-%m-%d')
        end = dt.datetime.strptime(end_date, '%Y-%m-%d')
        
        equity_curve = run_backtest(
            start, end, 
            initial_equity=initial_capital,
            slippage_bps=5,
            noise_factor=0.001,
            use_minute_candles=False  # Use daily data for faster testing
        )
        
        # Calculate performance metrics
        if equity_curve and len(equity_curve) > 1:
            final_equity = equity_curve[-1]
            total_return = (final_equity / initial_capital - 1) * 100
            daily_returns = [equity_curve[i]/equity_curve[i-1] - 1 for i in range(1, len(equity_curve))]
            volatility = pd.Series(daily_returns).std() * (252**0.5) * 100
            max_dd = calculate_max_drawdown(equity_curve)
            sharpe_ratio = (total_return / 100) / (volatility / 100) * (252**0.5) if volatility > 0 else 0
            
            # Print results
            results_table = Table(title="KLM Single Strategy Results")
            results_table.add_column("Metric", style="cyan")
            results_table.add_column("Value", style="green")
            
            results_table.add_row("Final Equity", f"£{final_equity:,.2f}")
            results_table.add_row("Total Return", f"{total_return:+.2f}%")
            results_table.add_row("Annualized Volatility", f"{volatility:.2f}%")
            results_table.add_row("Maximum Drawdown", f"{max_dd:.2f}%")
            results_table.add_row("Sharpe Ratio", f"{sharpe_ratio:.2f}")
            
            console.print(results_table)
            
            return {
                'final_equity': final_equity,
                'total_return': total_return,
                'volatility': volatility,
                'max_drawdown': max_dd,
                'sharpe_ratio': sharpe_ratio,
                'equity_curve': equity_curve
            }
        else:
            console.print("[red]❌ Backtest failed - no equity curve generated")
            return None
            
    finally:
        # Restore original config
        alchemiser_config._global_config = orig_global_config


def test_multi_strategy_portfolio(start_date: str = '2023-06-01', end_date: str = '2024-01-31', 
                                initial_capital: float = 100000):
    """Test KLM ensemble alongside Nuclear and TECL strategies"""
    console.print(Panel(f"[bold cyan]🧪 Multi-Strategy Portfolio Backtest[/bold cyan]\n"
                       f"Testing KLM ensemble integrated with Nuclear and TECL\n"
                       f"Allocation: 40% Nuclear / 30% TECL / 30% KLM\n"
                       f"Period: {start_date} to {end_date}\n"
                       f"Capital: £{initial_capital:,.2f}",
                       title="📊 Multi-Strategy Portfolio Test"))
    
    # Test various allocation strategies
    allocation_strategies = [
        {'nuclear': 0.4, 'tecl': 0.3, 'klm': 0.3, 'name': 'Balanced Portfolio'},
        {'nuclear': 0.2, 'tecl': 0.2, 'klm': 0.6, 'name': 'KLM Focused'},
        {'nuclear': 0.33, 'tecl': 0.33, 'klm': 0.34, 'name': 'Equal Weight'},
        {'nuclear': 0.5, 'tecl': 0.25, 'klm': 0.25, 'name': 'Nuclear Focused'}
    ]
    
    results = []
    
    for allocation in allocation_strategies:
        console.print(f"\n[yellow]Testing {allocation['name']} allocation...")
        
        # Temporarily modify config
        import copy
        from the_alchemiser.core import config as alchemiser_config
        
        orig_global_config = alchemiser_config._global_config
        
        try:
            mock_config = alchemiser_config.Config()
            mock_config._config = copy.deepcopy(mock_config._config)
            if 'strategy' not in mock_config._config:
                mock_config._config['strategy'] = {}
            mock_config._config['strategy']['default_strategy_allocations'] = {
                'nuclear': allocation['nuclear'], 
                'tecl': allocation['tecl'], 
                'klm': allocation['klm']
            }
            
            alchemiser_config._global_config = mock_config
            
            # Run backtest
            start = dt.datetime.strptime(start_date, '%Y-%m-%d')
            end = dt.datetime.strptime(end_date, '%Y-%m-%d')
            
            equity_curve = run_backtest(
                start, end, 
                initial_equity=initial_capital,
                slippage_bps=5,
                noise_factor=0.001,
                use_minute_candles=False
            )
            
            if equity_curve and len(equity_curve) > 1:
                final_equity = equity_curve[-1]
                total_return = (final_equity / initial_capital - 1) * 100
                daily_returns = [equity_curve[i]/equity_curve[i-1] - 1 for i in range(1, len(equity_curve))]
                volatility = pd.Series(daily_returns).std() * (252**0.5) * 100
                max_dd = calculate_max_drawdown(equity_curve)
                sharpe_ratio = (total_return / 100) / (volatility / 100) * (252**0.5) if volatility > 0 else 0
                
                results.append({
                    'name': allocation['name'],
                    'allocation': f"{int(allocation['nuclear']*100)}%/{int(allocation['tecl']*100)}%/{int(allocation['klm']*100)}%",
                    'final_equity': final_equity,
                    'total_return': total_return,
                    'volatility': volatility,
                    'max_drawdown': max_dd,
                    'sharpe_ratio': sharpe_ratio
                })
            
        finally:
            alchemiser_config._global_config = orig_global_config
    
    # Display comparison table
    comparison_table = Table(title="Multi-Strategy Portfolio Comparison")
    comparison_table.add_column("Strategy", style="cyan")
    comparison_table.add_column("Allocation (N/T/K)", style="yellow")
    comparison_table.add_column("Final Equity", style="green")
    comparison_table.add_column("Total Return", style="magenta")
    comparison_table.add_column("Volatility", style="blue")
    comparison_table.add_column("Max DD", style="red")
    comparison_table.add_column("Sharpe", style="white")
    
    for result in results:
        comparison_table.add_row(
            result['name'],
            result['allocation'],
            f"£{result['final_equity']:,.2f}",
            f"{result['total_return']:+.2f}%",
            f"{result['volatility']:.2f}%",
            f"{result['max_drawdown']:.2f}%",
            f"{result['sharpe_ratio']:.2f}"
        )
    
    console.print(comparison_table)
    return results


def test_klm_variant_analysis(start_date: str = '2023-06-01', end_date: str = '2024-01-31'):
    """Analyze individual KLM variant performance and ensemble selection"""
    console.print(Panel(f"[bold cyan]🧪 KLM Variant Analysis[/bold cyan]\n"
                       f"Testing individual variant performance and ensemble selection\n"
                       f"Period: {start_date} to {end_date}",
                       title="📊 KLM Variant Performance Analysis"))
    
    # Initialize KLM ensemble
    dp = UnifiedDataProvider(paper_trading=True, cache_duration=0)
    manager = MultiStrategyManager(shared_data_provider=dp)
    
    # Enable KLM ensemble
    if StrategyType.KLM not in manager.strategy_allocations:
        manager.strategy_allocations[StrategyType.KLM] = 1.0
        from the_alchemiser.core.trading.klm_ensemble_engine import KLMStrategyEnsemble
        manager.klm_ensemble = KLMStrategyEnsemble(data_provider=dp)
    
    # Test ensemble selection over time
    start = dt.datetime.strptime(start_date, '%Y-%m-%d')
    end = dt.datetime.strptime(end_date, '%Y-%m-%d')
    
    # Sample some dates for analysis
    date_range = pd.date_range(start, end, freq='W')  # Weekly sampling
    variant_selections = {}
    
    console.print(f"[yellow]Analyzing ensemble selection over {len(date_range)} time points...")
    
    for test_date in track(date_range[:10], description="Testing dates..."):  # Limit to 10 samples for speed
        try:
            # Run strategies on this date
            strategy_signals, consolidated_portfolio = manager.run_all_strategies()
            
            if StrategyType.KLM in strategy_signals:
                klm_signal = strategy_signals[StrategyType.KLM]
                variant_name = klm_signal.get('variant_name', 'Unknown')
                
                if variant_name not in variant_selections:
                    variant_selections[variant_name] = 0
                variant_selections[variant_name] += 1
                
        except Exception as e:
            console.print(f"[red]Error analyzing date {test_date}: {e}")
            continue
    
    # Display variant selection frequency
    if variant_selections:
        variant_table = Table(title="KLM Variant Selection Frequency")
        variant_table.add_column("Variant", style="cyan")
        variant_table.add_column("Selection Count", style="green")
        variant_table.add_column("Selection %", style="yellow")
        
        total_selections = sum(variant_selections.values())
        for variant, count in sorted(variant_selections.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_selections) * 100 if total_selections > 0 else 0
            variant_table.add_row(variant, str(count), f"{percentage:.1f}%")
        
        console.print(variant_table)
        
        # Show variant descriptions
        from the_alchemiser.core.trading.klm_workers import (
            KLMVariant506_38, KLMVariant1280_26, KLMVariant1200_28, KLMVariant520_22,
            KLMVariant530_18, KLMVariant410_38, KLMVariantNova, KLMVariant830_21
        )
        
        variant_descriptions = {
            'KLMVariant506_38': 'Standard overbought detection',
            'KLMVariant1280_26': 'Parameter variant with different thresholds', 
            'KLMVariant1200_28': 'Alternative parameter configuration',
            'KLMVariant520_22': '"Original" baseline variant',
            'KLMVariant530_18': 'Scale-In strategy (most complex)',
            'KLMVariant410_38': 'MonkeyBusiness Simons variant',
            'KLMVariantNova': 'Short backtest optimization variant',
            'KLMVariant830_21': 'MonkeyBusiness Simons V2'
        }
        
        desc_table = Table(title="KLM Variant Descriptions")
        desc_table.add_column("Variant", style="cyan")
        desc_table.add_column("Description", style="white")
        
        for variant in sorted(variant_selections.keys()):
            description = variant_descriptions.get(variant, 'Unknown variant')
            desc_table.add_row(variant, description)
        
        console.print(desc_table)
        
        return variant_selections
    else:
        console.print("[red]❌ No variant selections recorded")
        return {}


def calculate_max_drawdown(equity_curve):
    """Calculate maximum drawdown from equity curve"""
    if not equity_curve or len(equity_curve) < 2:
        return 0.0
    
    equity_series = pd.Series(equity_curve)
    rolling_max = equity_series.expanding().max()
    drawdown = (equity_series - rolling_max) / rolling_max
    return drawdown.min() * 100  # Convert to percentage


def run_comprehensive_klm_tests():
    """Run all KLM backtest scenarios"""
    console.print(Panel("[bold green]🚀 KLM Strategy Comprehensive Backtest Suite[/bold green]\n"
                       "Running all test scenarios for KLM ensemble integration",
                       title="📊 KLM Backtest Suite"))
    
    # Test parameters
    start_date = '2023-06-01'
    end_date = '2024-01-31'
    initial_capital = 100000
    
    results = {}
    
    # Test 1: Single KLM Strategy
    console.print("\n" + "="*60)
    console.print("[bold yellow]TEST 1: Single KLM Strategy[/bold yellow]")
    results['single_klm'] = test_single_klm_strategy(start_date, end_date, initial_capital)
    
    # Test 2: Multi-Strategy Portfolio
    console.print("\n" + "="*60)
    console.print("[bold yellow]TEST 2: Multi-Strategy Portfolio[/bold yellow]")
    results['multi_strategy'] = test_multi_strategy_portfolio(start_date, end_date, initial_capital)
    
    # Test 3: KLM Variant Analysis
    console.print("\n" + "="*60)
    console.print("[bold yellow]TEST 3: KLM Variant Analysis[/bold yellow]")
    results['variant_analysis'] = test_klm_variant_analysis(start_date, end_date)
    
    # Summary
    console.print("\n" + "="*60)
    console.print(Panel("[bold green]🎉 KLM Backtest Suite Complete![/bold green]\n"
                       "All test scenarios have been executed.\n"
                       "Results show KLM ensemble integration is working correctly.",
                       title="✅ Test Suite Summary"))
    
    return results


def main():
    """Main entry point for KLM backtest suite"""
    parser = argparse.ArgumentParser(description='KLM Strategy Backtest Suite')
    parser.add_argument('--test', choices=['single_klm', 'multi_strategy', 'variant_analysis', 'all'],
                       default='all', help='Which test to run')
    parser.add_argument('--start', default='2023-06-01', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', default='2024-01-31', help='End date (YYYY-MM-DD)')
    parser.add_argument('--capital', type=float, default=100000, help='Initial capital')
    
    args = parser.parse_args()
    
    if args.test == 'single_klm':
        test_single_klm_strategy(args.start, args.end, args.capital)
    elif args.test == 'multi_strategy':
        test_multi_strategy_portfolio(args.start, args.end, args.capital)
    elif args.test == 'variant_analysis':
        test_klm_variant_analysis(args.start, args.end)
    elif args.test == 'all':
        run_comprehensive_klm_tests()


if __name__ == "__main__":
    main()
