#!/usr/bin/env python3
"""
Quick test of the Nuclear Energy backtester
"""

from nuclear_backtest_simple import NuclearBacktester
import sys

def test_backtester():
    """Test the backtester with a short period"""
    print("Testing Nuclear Energy Backtester...")
    
    # Test with a short period to verify functionality
    backtester = NuclearBacktester(
        start_date='2023-01-01',
        end_date='2023-12-31',
        initial_capital=100000
    )
    
    print("Running single strategy test...")
    
    # Test single strategy
    backtester.download_data()
    result = backtester.run_backtest('close')
    
    if result:
        print(f"✅ Test successful!")
        print(f"   Total Return: {result.total_return:.2%}")
        print(f"   Sharpe Ratio: {result.sharpe_ratio:.2f}")
        print(f"   Total Trades: {result.total_trades}")
        return True
    else:
        print("❌ Test failed - no results generated")
        return False

if __name__ == "__main__":
    success = test_backtester()
    sys.exit(0 if success else 1)
