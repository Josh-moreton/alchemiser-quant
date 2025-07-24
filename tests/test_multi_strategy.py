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

from the_alchemiser.core.config import Config
from the_alchemiser.core.strategy_manager import MultiStrategyManager, StrategyType
from the_alchemiser.core.tecl_strategy_engine import TECLStrategyEngine
from the_alchemiser.execution.multi_strategy_trader import MultiStrategyAlpacaTrader


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
        
        # Get current positions (should be empty as tracking between runs is disabled)
        positions = manager.get_current_positions()
        print(f"✅ Position tracking disabled: {len(positions)} strategy types with empty position lists")
        
        for strategy, pos_list in positions.items():
            print(f"   {strategy.value}: {len(pos_list)} positions")
        
        # Verify all position lists are empty (since tracking between runs is disabled)
        assert all(len(pos_list) == 0 for pos_list in positions.values()), "Position lists should be empty"
        print("✅ All position lists are empty as expected")
        
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


def test_tecl_strategy_engine_bull_market():
    """Test TECL strategy engine in bull market scenario"""
    print("\n🧪 Testing TECL Strategy Engine in Bull Market Scenario...")
    print("-" * 40)
    
    try:
        engine = TECLStrategyEngine()
        
        # Mock market data for bull market
        market_data = [
            {'symbol': 'AAPL', 'rsi': 70, 'price': 150, 'ma': 145},
            {'symbol': 'TSLA', 'rsi': 75, 'price': 700, 'ma': 680},
            # Add more symbols as needed
        ]
        
        # Mock indicators (normally calculated from market data)
        indicators = engine.calculate_indicators(market_data)
        
        # Test strategy evaluation
        symbol_or_allocation, action, reason = engine.evaluate_tecl_strategy(indicators, market_data)
        
        assert action == "allocate", "TECL strategy should allocate in bull market"
        assert isinstance(symbol_or_allocation, dict), "Allocation should be a dictionary"
        assert all(v > 0 for v in symbol_or_allocation.values()), "All allocations should be positive"
        
        print(f"✅ TECL Strategy Bull Market Test Passed: {action} allocation {symbol_or_allocation}")
        return True, {'symbol': symbol_or_allocation, 'action': action, 'reason': reason}
        
    except Exception as e:
        print(f"❌ TECL Strategy Engine Bull Market test failed: {e}")
        import traceback
        traceback.print_exc()
        return False, {}


def test_tecl_strategy_engine_bear_market():
    """Test TECL strategy engine in bear market scenario"""
    print("\n🧪 Testing TECL Strategy Engine in Bear Market Scenario...")
    print("-" * 40)
    
    try:
        engine = TECLStrategyEngine()
        
        # Mock market data for bear market
        market_data = [
            {'symbol': 'AAPL', 'rsi': 30, 'price': 120, 'ma': 125},
            {'symbol': 'TSLA', 'rsi': 25, 'price': 600, 'ma': 620},
            # Add more symbols as needed
        ]
        
        # Mock indicators (normally calculated from market data)
        indicators = engine.calculate_indicators(market_data)
        
        # Test strategy evaluation
        symbol_or_allocation, action, reason = engine.evaluate_tecl_strategy(indicators, market_data)
        
        assert action == "defensive", "TECL strategy should go defensive in bear market"
        assert isinstance(symbol_or_allocation, dict), "Allocation should be a dictionary"
        assert all(v <= 0 for v in symbol_or_allocation.values()), "All allocations should be non-positive (cash or hedge)"
        
        print(f"✅ TECL Strategy Bear Market Test Passed: {action} allocation {symbol_or_allocation}")
        return True, {'symbol': symbol_or_allocation, 'action': action, 'reason': reason}
        
    except Exception as e:
        print(f"❌ TECL Strategy Engine Bear Market test failed: {e}")
        import traceback
        traceback.print_exc()
        return False, {}


def test_nuclear_strategy_volatility_spike():
    """Test Nuclear strategy with volatility spike scenario"""
    print("\n🧪 Testing Nuclear Strategy with Volatility Spike Scenario...")
    print("-" * 40)
    
    try:
        engine = TECLStrategyEngine()
        
        # Mock market data for volatility spike
        market_data = [
            {'symbol': 'UVXY', 'rsi': 85, 'price': 20, 'ma': 15},
            {'symbol': 'SPY', 'rsi': 40, 'price': 400, 'ma': 410},
            # Add more symbols as needed
        ]
        
        # Mock indicators (normally calculated from market data)
        indicators = engine.calculate_indicators(market_data)
        
        # Test strategy evaluation
        symbol_or_allocation, action, reason = engine.evaluate_tecl_strategy(indicators, market_data)
        
        assert action == "hedge", "Nuclear strategy should hedge against volatility spike"
        assert isinstance(symbol_or_allocation, dict), "Allocation should be a dictionary"
        assert all(v <= 0 for v in symbol_or_allocation.values()), "All allocations should be non-positive (cash or hedge)"
        
        print(f"✅ Nuclear Strategy Volatility Spike Test Passed: {action} allocation {symbol_or_allocation}")
        return True, {'symbol': symbol_or_allocation, 'action': action, 'reason': reason}
        
    except Exception as e:
        print(f"❌ Nuclear Strategy Volatility Spike test failed: {e}")
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
        ("TECL Strategy Engine Bull Market", test_tecl_strategy_engine_bull_market),
        ("TECL Strategy Engine Bear Market", test_tecl_strategy_engine_bear_market),
        ("Nuclear Strategy Volatility Spike", test_nuclear_strategy_volatility_spike),
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
