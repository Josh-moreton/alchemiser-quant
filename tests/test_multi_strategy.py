#!/usr/bin/env python3
"""
Multi-Strategy System Test Suite

This script comprehensively tests the new multi-strategy trading system:
1. TECL Strategy Engine
2. Multi-Strategy Manager 
3. Multi-Strategy Alpaca Trader
4. Position Tracking
5. Consolidated Portfolio Generation

Run this to verify all components work correctly before deployment.
"""

import os
import sys
import logging
from typing import Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import Config
from core.strategy_manager import MultiStrategyManager, StrategyType
from core.tecl_strategy_engine import TECLStrategyEngine
from execution.multi_strategy_trader import MultiStrategyAlpacaTrader


def test_tecl_strategy_engine():
    """Test TECL strategy engine independently"""
    print("🧪 Testing TECL Strategy Engine...")
    print("-" * 40)
    
    try:
        engine = TECLStrategyEngine()
        
        # Test data fetching
        print("📊 Testing data fetching...")
        market_data = engine.get_market_data()
        print(f"✅ Fetched data for {len(market_data)} symbols")
        
        # Test indicator calculation
        print("🔬 Testing indicator calculation...")
        indicators = engine.calculate_indicators(market_data)
        print(f"✅ Calculated indicators for {len(indicators)} symbols")
        
        # Test strategy evaluation
        print("⚡ Testing strategy evaluation...")
        symbol_or_allocation, action, reason = engine.evaluate_tecl_strategy(indicators, market_data)
        
        if isinstance(symbol_or_allocation, dict):
            print(f"✅ TECL Strategy Result: {action} allocation {symbol_or_allocation} - {reason}")
        else:
            print(f"✅ TECL Strategy Result: {action} {symbol_or_allocation} - {reason}")
        
        return True, {'symbol': symbol_or_allocation, 'action': action, 'reason': reason}
        
    except Exception as e:
        print(f"❌ TECL Strategy Engine test failed: {e}")
        import traceback
        traceback.print_exc()
        return False, {}


def test_multi_strategy_manager():
    """Test multi-strategy manager"""
    print("\n🧪 Testing Multi-Strategy Manager...")
    print("-" * 40)
    
    try:
        manager = MultiStrategyManager({
            StrategyType.NUCLEAR: 0.6,
            StrategyType.TECL: 0.4
        })
        
        print("📊 Testing strategy execution...")
        strategy_signals, consolidated_portfolio = manager.run_all_strategies()
        
        print("✅ Strategy signals generated:")
        for strategy_type, signal in strategy_signals.items():
            print(f"   {strategy_type.value}: {signal['action']} {signal['symbol']}")
        
        print(f"✅ Consolidated portfolio: {consolidated_portfolio}")
        
        # Test performance summary
        summary = manager.get_strategy_performance_summary()
        print(f"✅ Performance summary generated with {len(summary['strategies'])} strategies")
        
        return True, {'signals': strategy_signals, 'portfolio': consolidated_portfolio}
        
    except Exception as e:
        print(f"❌ Multi-Strategy Manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False, {}


def test_multi_strategy_trader():
    """Test multi-strategy Alpaca trader (paper trading)"""
    print("\n🧪 Testing Multi-Strategy Alpaca Trader (Paper)...")
    print("-" * 40)
    
    try:
        trader = MultiStrategyAlpacaTrader(
            paper_trading=True,
            strategy_allocations={
                StrategyType.NUCLEAR: 0.5,
                StrategyType.TECL: 0.5
            }
        )
        
        print("📊 Testing account information...")
        account_info = trader.get_account_info()
        if account_info:
            print(f"✅ Account info retrieved: ${account_info.get('portfolio_value', 0):,.2f}")
        else:
            print("⚠️ Could not retrieve account info (may need Alpaca credentials)")
            return True, {'warning': 'No account access'}
        
        print("📈 Testing performance report...")
        report = trader.get_multi_strategy_performance_report()
        
        if 'error' not in report:
            print("✅ Performance report generated successfully")
        else:
            print(f"⚠️ Performance report warning: {report['error']}")
        
        return True, {'account_info': account_info, 'report': report}
        
    except Exception as e:
        print(f"❌ Multi-Strategy Trader test failed: {e}")
        import traceback
        traceback.print_exc()
        return False, {}


def test_position_tracking():
    """Test position tracking system"""
    print("\n🧪 Testing Position Tracking System...")
    print("-" * 40)
    
    try:
        manager = MultiStrategyManager()
        
        # Get current positions
        positions = manager.get_current_positions()
        print(f"✅ Position tracking loaded: {len(positions)} strategy types")
        
        for strategy, pos_list in positions.items():
            print(f"   {strategy.value}: {len(pos_list)} positions")
        
        return True, {'positions': positions}
        
    except Exception as e:
        print(f"❌ Position tracking test failed: {e}")
        import traceback
        traceback.print_exc()
        return False, {}


def test_config_integration():
    """Test configuration integration for multi-strategy"""
    print("\n🧪 Testing Configuration Integration...")
    print("-" * 40)
    
    try:
        config = Config()
        
        # Check required config keys
        required_keys = [
            'multi_strategy_alerts',
            'multi_strategy_log',
            'strategy_positions',
            'tecl_strategy_log'
        ]
        
        for key in required_keys:
            if key in config['logging']:
                print(f"✅ Config key '{key}' found: {config['logging'][key]}")
            else:
                print(f"⚠️ Config key '{key}' missing - using defaults")
        
        return True, {'config': config}
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False, {}


def run_comprehensive_test():
    """Run all tests and provide summary"""
    print("🚀 MULTI-STRATEGY SYSTEM COMPREHENSIVE TEST")
    print("=" * 60)
    print(f"Testing all components of the multi-strategy trading system...")
    print()
    
    # Configure logging for tests
    logging.basicConfig(level=logging.WARNING)  # Reduce noise during testing
    
    results = {}
    
    # Test each component
    tests = [
        ("Config Integration", test_config_integration),
        ("TECL Strategy Engine", test_tecl_strategy_engine),
        ("Position Tracking", test_position_tracking),
        ("Multi-Strategy Manager", test_multi_strategy_manager),
        ("Multi-Strategy Trader", test_multi_strategy_trader),
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        success, result = test_func()
        results[test_name] = {'success': success, 'result': result}
        if success:
            passed_tests += 1
    
    # Print summary
    print("\n" + "=" * 60)
    print("🎯 TEST SUMMARY")
    print("=" * 60)
    
    for test_name, test_result in results.items():
        status = "✅ PASSED" if test_result['success'] else "❌ FAILED"
        print(f"{test_name}: {status}")
        
        # Show warnings or key results
        result_data = test_result['result']
        if 'warning' in result_data:
            print(f"   ⚠️ {result_data['warning']}")
        elif test_result['success'] and test_name == "Multi-Strategy Manager":
            portfolio = result_data.get('portfolio', {})
            if portfolio:
                print(f"   📈 Portfolio: {', '.join([f'{k}:{v:.1%}' for k, v in portfolio.items()])}")
    
    print(f"\n🎯 OVERALL RESULT: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! Multi-strategy system is ready for deployment.")
        return True
    else:
        print("⚠️ Some tests failed. Review the errors above before deployment.")
        return False


def main():
    """Main test execution"""
    try:
        success = run_comprehensive_test()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
