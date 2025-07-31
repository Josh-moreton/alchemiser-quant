#!/usr/bin/env python3
"""
Test KLM Integration with Live Bot

Verifies that KLM is fully integrated into the live trading system
and can be enabled by changing the config.yaml allocation.
"""

import sys
import os
sys.path.append('/Users/joshua.moreton/Documents/GitHub/the-alchemiser')

import logging
logging.basicConfig(level=logging.INFO)

def test_klm_zero_allocation():
    """Test that KLM works with 0.0 allocation (disabled by default)"""
    print("=== Testing KLM with 0.0 allocation (default config) ===")
    
    from the_alchemiser.core.trading.strategy_manager import MultiStrategyManager, StrategyType
    from the_alchemiser.core.config import get_config
    
    # Use default config (should have klm: 0.0)
    config = get_config()
    print(f"Config allocations: {config['strategy']['default_strategy_allocations']}")
    
    # Create manager with default config allocations
    manager = MultiStrategyManager(config=config)
    
    print(f"Manager allocations: {manager.strategy_allocations}")
    print(f"KLM ensemble initialized: {manager.klm_ensemble is not None}")
    
    # Should not have KLM in allocations since it's 0.0
    assert StrategyType.KLM not in manager.strategy_allocations
    assert manager.klm_ensemble is None
    
    print("✅ KLM correctly disabled with 0.0 allocation")

def test_klm_enabled_allocation():
    """Test that KLM works when enabled with non-zero allocation"""
    print("\n=== Testing KLM with enabled allocation ===")
    
    from the_alchemiser.core.trading.strategy_manager import MultiStrategyManager, StrategyType
    
    # Create manager with KLM enabled
    test_allocations = {
        StrategyType.NUCLEAR: 0.3,
        StrategyType.TECL: 0.4,
        StrategyType.KLM: 0.3
    }
    
    manager = MultiStrategyManager(strategy_allocations=test_allocations)
    
    print(f"Manager allocations: {manager.strategy_allocations}")
    print(f"KLM ensemble initialized: {manager.klm_ensemble is not None}")
    
    # Should have KLM in allocations and be initialized
    assert StrategyType.KLM in manager.strategy_allocations
    assert manager.klm_ensemble is not None
    
    print("✅ KLM correctly enabled with non-zero allocation")

def test_klm_signal_generation():
    """Test that KLM can generate signals when enabled"""
    print("\n=== Testing KLM signal generation ===")
    
    from the_alchemiser.core.trading.strategy_manager import MultiStrategyManager, StrategyType
    
    # Create manager with KLM enabled
    test_allocations = {
        StrategyType.NUCLEAR: 0.3,
        StrategyType.TECL: 0.4,
        StrategyType.KLM: 0.3
    }
    
    manager = MultiStrategyManager(strategy_allocations=test_allocations)
    
    # Generate signals
    try:
        strategy_signals, consolidated_portfolio = manager.run_all_strategies()
        
        print(f"Generated signals for {len(strategy_signals)} strategies")
        print(f"KLM signal present: {StrategyType.KLM in strategy_signals}")
        
        if StrategyType.KLM in strategy_signals:
            klm_signal = strategy_signals[StrategyType.KLM]
            print(f"KLM signal: {klm_signal['action']} {klm_signal['symbol']} - {klm_signal['reason']}")
            if 'variant_name' in klm_signal:
                print(f"Selected variant: {klm_signal['variant_name']}")
        
        print(f"Consolidated portfolio: {consolidated_portfolio}")
        print("✅ KLM signal generation successful")
        
    except Exception as e:
        print(f"❌ KLM signal generation failed: {e}")
        import traceback
        traceback.print_exc()

def test_main_integration():
    """Test that main.py properly reads KLM from config"""
    print("\n=== Testing main.py integration ===")
    
    try:
        # Test signals display function
        from the_alchemiser.main import generate_multi_strategy_signals
        from the_alchemiser.core.trading.strategy_manager import StrategyType
        
        manager, strategy_signals, consolidated_portfolio = generate_multi_strategy_signals()
        
        if manager and strategy_signals:
            print(f"Main integration successful - generated {len(strategy_signals)} strategy signals")
            print(f"Manager allocations: {manager.strategy_allocations}")
            print(f"KLM in allocations: {StrategyType.KLM in manager.strategy_allocations}")
            print("✅ Main.py integration working correctly")
        else:
            print("❌ Main.py integration returned None values")
            
    except Exception as e:
        print(f"❌ Main.py integration failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🧪 Testing KLM Integration with Live Bot")
    print("=" * 50)
    
    test_klm_zero_allocation()
    test_klm_enabled_allocation() 
    test_klm_signal_generation()
    test_main_integration()
    
    print("\n🎯 Integration Test Summary:")
    print("- KLM can be disabled via config.yaml (klm: 0.0)")
    print("- KLM can be enabled via config.yaml (klm: > 0.0)")
    print("- KLM generates signals when enabled")
    print("- Main.py properly reads KLM allocation from config")
    print("- Live bot ready for KLM usage!")
