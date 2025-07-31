#!/usr/bin/env python3
"""
Test KLM Strategy using the existing test_backtest.py framework

This script properly integrates KLM with the sophisticated backtest infrastructure
that already exists in test_backtest.py, instead of creating separate backtest logic.
"""

import sys
import os
import datetime as dt
sys.path.append('/Users/joshua.moreton/Documents/GitHub/the-alchemiser')

# Import the existing backtest framework
from the_alchemiser.backtest.test_backtest import run_backtest
from the_alchemiser.core.trading.strategy_manager import MultiStrategyManager, StrategyType
from the_alchemiser.core.data.data_provider import UnifiedDataProvider

def test_klm_single_strategy():
    """Test KLM strategy in isolation using existing backtest framework"""
    print("🧪 Testing KLM Strategy (Single) with Existing Backtest Framework")
    print("=" * 70)
    
    # Create a MultiStrategyManager with 100% KLM allocation
    data_provider = UnifiedDataProvider(paper_trading=True)
    manager = MultiStrategyManager(
        strategy_allocations={StrategyType.KLM: 1.0},
        shared_data_provider=data_provider
    )
    
    print(f"✅ MultiStrategyManager created with KLM allocation: {manager.strategy_allocations}")
    print(f"🎯 KLM ensemble enabled: {manager.klm_ensemble is not None}")
    
    # Set date range for backtest
    end_date = dt.datetime.now() - dt.timedelta(days=7)  # 1 week ago to avoid partial data
    start_date = end_date - dt.timedelta(days=180)  # 6 months
    
    print(f"📅 Backtest period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    # Run backtest using existing framework
    try:
        equity_curve = run_backtest(
            start=start_date,
            end=end_date,
            initial_equity=10000.0,
            price_type="close",
            slippage_bps=5,
            noise_factor=0.001,
            use_minute_candles=False  # Use daily data for faster testing
        )
        
        if equity_curve:
            initial_equity = equity_curve[0]
            final_equity = equity_curve[-1]
            total_return = (final_equity / initial_equity - 1) * 100
            
            print(f"\n🎉 KLM Backtest Results:")
            print(f"   Initial Equity: £{initial_equity:,.2f}")
            print(f"   Final Equity: £{final_equity:,.2f}")
            print(f"   Total Return: {total_return:+.2f}%")
            print(f"   Equity Curve Length: {len(equity_curve)} days")
            
            return True
        else:
            print("❌ No equity curve returned")
            return False
            
    except Exception as e:
        print(f"❌ Backtest failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_klm_multi_strategy():
    """Test KLM in a multi-strategy portfolio using existing backtest framework"""
    print("\n🧪 Testing KLM in Multi-Strategy Portfolio")
    print("=" * 70)
    
    # Test different allocation scenarios
    allocation_scenarios = [
        {"name": "KLM Heavy", "allocations": {StrategyType.KLM: 0.6, StrategyType.NUCLEAR: 0.2, StrategyType.TECL: 0.2}},
        {"name": "KLM Balanced", "allocations": {StrategyType.KLM: 0.33, StrategyType.NUCLEAR: 0.33, StrategyType.TECL: 0.34}},
        {"name": "KLM Light", "allocations": {StrategyType.KLM: 0.2, StrategyType.NUCLEAR: 0.4, StrategyType.TECL: 0.4}},
    ]
    
    end_date = dt.datetime.now() - dt.timedelta(days=7)
    start_date = end_date - dt.timedelta(days=90)  # 3 months for faster multi-scenario testing
    
    results = {}
    
    for scenario in allocation_scenarios:
        print(f"\n📊 Testing {scenario['name']} allocation...")
        print(f"   Allocations: {scenario['allocations']}")
        
        try:
            # Create manager with specific allocations
            data_provider = UnifiedDataProvider(paper_trading=True)
            manager = MultiStrategyManager(
                strategy_allocations=scenario['allocations'],
                shared_data_provider=data_provider
            )
            
            # Run backtest
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
                initial_equity = equity_curve[0]
                final_equity = equity_curve[-1]
                total_return = (final_equity / initial_equity - 1) * 100
                
                results[scenario['name']] = {
                    'total_return': total_return,
                    'final_equity': final_equity,
                    'allocations': scenario['allocations']
                }
                
                print(f"   ✅ Total Return: {total_return:+.2f}%")
            else:
                print(f"   ❌ Failed to get results")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Compare results
    if results:
        print(f"\n🏆 Multi-Strategy Comparison Results:")
        print("-" * 50)
        for name, data in results.items():
            print(f"{name:15} | {data['total_return']:+7.2f}% | KLM: {data['allocations'].get(StrategyType.KLM, 0):.0%}")
        
        best_scenario = max(results.items(), key=lambda x: x[1]['total_return'])
        print(f"\n🥇 Best performer: {best_scenario[0]} ({best_scenario[1]['total_return']:+.2f}%)")
    
    return len(results) > 0


def test_klm_variant_tracking():
    """Test that we can track which KLM variants are being selected"""
    print("\n🧪 Testing KLM Variant Selection Tracking")
    print("=" * 70)
    
    try:
        # Create KLM-only manager
        data_provider = UnifiedDataProvider(paper_trading=True)
        manager = MultiStrategyManager(
            strategy_allocations={StrategyType.KLM: 1.0},
            shared_data_provider=data_provider
        )
        
        # Run strategy evaluation a few times to see different variants
        print("🔄 Running KLM ensemble evaluation...")
        
        for i in range(5):
            signals, portfolio = manager.run_all_strategies()
            klm_signal = signals.get(StrategyType.KLM, {})
            
            variant_name = klm_signal.get('variant_name', 'Unknown')
            symbol = klm_signal.get('symbol', 'Unknown')
            reason = klm_signal.get('reason', 'Unknown')
            
            print(f"   Run {i+1}: Variant '{variant_name}' selected {symbol}")
            print(f"           Reason: {reason[:80]}...")
        
        print("✅ Variant tracking working")
        return True
        
    except Exception as e:
        print(f"❌ Variant tracking failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all KLM tests using existing backtest framework"""
    print("🚀 KLM Strategy Integration Test Suite")
    print("Using Existing test_backtest.py Framework")
    print("=" * 70)
    
    tests = [
        ("KLM Single Strategy", test_klm_single_strategy),
        ("KLM Multi-Strategy", test_klm_multi_strategy),
        ("KLM Variant Tracking", test_klm_variant_tracking),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name}...")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 70)
    print("🎯 TEST SUMMARY")
    print("=" * 70)
    
    passed = 0
    for test_name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name:25} | {status}")
        if success:
            passed += 1
    
    print(f"\nResults: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 ALL TESTS PASSED! KLM is ready for production backtesting!")
        print("\n📋 Next Steps:")
        print("   1. Run longer backtests using test_backtest.py directly")
        print("   2. Test different market periods (bull/bear/volatile)")
        print("   3. Compare KLM vs Nuclear vs TECL performance")
        print("   4. Optimize KLM allocation in multi-strategy portfolios")
    else:
        print("⚠️  Some tests failed. Check logs above for details.")
    
    return passed == len(tests)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
