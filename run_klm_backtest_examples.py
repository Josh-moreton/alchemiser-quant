#!/usr/bin/env python3
"""
Run KLM backtests using the existing test_backtest.py framework

This script shows how to use the existing sophisticated backtest infrastructure
to test KLM strategy performance.
"""

import sys
import os
import datetime as dt
sys.path.append('/Users/joshua.moreton/Documents/GitHub/the-alchemiser')

# Import the existing backtest framework
from the_alchemiser.backtest.test_backtest import run_backtest
from the_alchemiser.core.trading.strategy_manager import MultiStrategyManager, StrategyType
from the_alchemiser.core.data.data_provider import UnifiedDataProvider

def run_klm_backtest_examples():
    """Run various KLM backtest examples using existing framework"""
    
    print("🚀 KLM Strategy Backtests using test_backtest.py")
    print("=" * 60)
    
    # Set up common parameters
    end_date = dt.datetime.now() - dt.timedelta(days=7)
    start_date = end_date - dt.timedelta(days=180)  # 6 months
    
    print(f"📅 Backtest Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"💰 Initial Capital: £10,000")
    print(f"⚡ Using existing test_backtest.py framework")
    print()
    
    # Example 1: Pure KLM Strategy
    print("🎯 Example 1: Pure KLM Strategy (100% allocation)")
    print("-" * 50)
    
    # Temporarily modify the global config to use 100% KLM
    from the_alchemiser.core import config as alchemiser_config
    
    # Store original config
    orig_global_config = alchemiser_config._global_config
    
    # Create mock config with KLM allocation
    mock_config = alchemiser_config.Config()
    mock_config._config = mock_config._config.copy()
    if 'strategy' not in mock_config._config:
        mock_config._config['strategy'] = {}
    mock_config._config['strategy']['default_strategy_allocations'] = {
        'nuclear': 0.0, 
        'tecl': 0.0, 
        'klm': 1.0
    }
    
    # Set the global config
    alchemiser_config._global_config = mock_config
    
    try:
        # Run backtest using the existing framework
        equity_curve = run_backtest(
            start=start_date,
            end=end_date,
            initial_equity=10000.0,
            price_type="close",
            slippage_bps=5,
            noise_factor=0.001,
            use_minute_candles=False
        )
        
        if equity_curve:
            final_equity = equity_curve[-1]
            total_return = (final_equity / 10000.0 - 1) * 100
            print(f"✅ KLM Pure Strategy Return: {total_return:+.2f}%")
        else:
            print("❌ KLM backtest failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        # Restore original config
        alchemiser_config._global_config = orig_global_config
    
    print()
    
    # Example 2: Multi-Strategy with KLM
    print("🎯 Example 2: Multi-Strategy Portfolio (33% KLM + 33% Nuclear + 34% TECL)")
    print("-" * 70)
    
    # Create balanced allocation config
    mock_config = alchemiser_config.Config()
    mock_config._config = mock_config._config.copy()
    if 'strategy' not in mock_config._config:
        mock_config._config['strategy'] = {}
    mock_config._config['strategy']['default_strategy_allocations'] = {
        'nuclear': 0.33, 
        'tecl': 0.34, 
        'klm': 0.33
    }
    
    alchemiser_config._global_config = mock_config
    
    try:
        equity_curve = run_backtest(
            start=start_date,
            end=end_date,
            initial_equity=10000.0,
            price_type="close",
            slippage_bps=5,
            noise_factor=0.001,
            use_minute_candles=False
        )
        
        if equity_curve:
            final_equity = equity_curve[-1]
            total_return = (final_equity / 10000.0 - 1) * 100
            print(f"✅ Multi-Strategy Return: {total_return:+.2f}%")
        else:
            print("❌ Multi-strategy backtest failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        # Restore original config
        alchemiser_config._global_config = orig_global_config
    
    print()
    
    # Example 3: Show how to use test_backtest.py directly for more control
    print("💡 Example 3: Direct Usage of test_backtest.py")
    print("-" * 45)
    print("To run KLM backtests directly with test_backtest.py:")
    print()
    print("# Single KLM strategy:")
    print("python3 -m the_alchemiser.backtest.test_backtest \\")
    print(f"  --start {start_date.strftime('%Y-%m-%d')} \\")
    print(f"  --end {end_date.strftime('%Y-%m-%d')} \\")
    print("  --initial-equity 10000 \\")
    print("  --price-type close \\")
    print("  --slippage-bps 5")
    print()
    print("# With minute-level execution:")
    print("python3 -m the_alchemiser.backtest.test_backtest \\")
    print(f"  --start {start_date.strftime('%Y-%m-%d')} \\")
    print(f"  --end {end_date.strftime('%Y-%m-%d')} \\")
    print("  --use-minute-candles \\")
    print("  --price-type vwap")
    print()
    print("# Test all price execution types:")
    print("python3 -m the_alchemiser.backtest.test_backtest \\")
    print(f"  --start {start_date.strftime('%Y-%m-%d')} \\")
    print(f"  --end {end_date.strftime('%Y-%m-%d')} \\")
    print("  --all-splits")
    print()
    
    print("✅ KLM is now fully integrated with the existing backtest framework!")
    print("🎯 You can use all the sophisticated features of test_backtest.py with KLM")
    print("📊 Features available: realistic execution, slippage modeling, minute candles, etc.")


if __name__ == "__main__":
    run_klm_backtest_examples()
