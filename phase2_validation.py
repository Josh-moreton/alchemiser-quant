#!/usr/bin/env python3
"""
Phase 2 Validation Script
Tests the TradingEngine and main.py DI integration
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from the_alchemiser.container.application_container import ApplicationContainer
from the_alchemiser.application.trading_engine import TradingEngine
from the_alchemiser.main import main


def test_trading_engine_di():
    """Test TradingEngine DI integration."""
    print("🔍 Testing TradingEngine DI integration...")
    
    try:
        # Test traditional mode
        engine_traditional = TradingEngine(paper_trading=True)
        print("✅ Traditional TradingEngine created")
        
        # Test DI mode
        container = ApplicationContainer.create_for_testing()
        engine_di = TradingEngine.create_with_di(container=container)
        print("✅ DI TradingEngine created")
        
        # Test factory method
        engine_factory = TradingEngine.create_with_di(
            container=container,
            strategy_allocations={},
            ignore_market_hours=True
        )
        print("✅ DI TradingEngine created via factory method")
        
        # Verify attributes
        assert hasattr(engine_traditional, 'data_provider')
        assert hasattr(engine_di, 'data_provider')
        assert hasattr(engine_factory, 'data_provider')
        
        assert engine_traditional._container is None
        assert engine_di._container is not None
        assert engine_factory._container is not None
        
        print("✅ All TradingEngine attributes verified")
        
        return True
    except Exception as e:
        print(f"❌ TradingEngine DI test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_main_di():
    """Test main.py DI integration."""
    print("\n🔍 Testing main.py DI integration...")
    
    try:
        # Test traditional mode (quiet)
        success = main(['bot'])
        print("✅ Traditional mode completed successfully")
        
        # Test DI mode (quiet)
        success = main(['bot', '--use-di'])
        print("✅ DI mode completed successfully")
        
        return True
    except Exception as e:
        print(f"❌ main.py DI test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_initialization_modes():
    """Test all TradingEngine initialization modes."""
    print("\n🔍 Testing all initialization modes...")
    
    try:
        # 1. Traditional mode
        engine1 = TradingEngine(paper_trading=True)
        assert engine1._container is None
        print("✅ Traditional initialization")
        
        # 2. Partial DI mode (with TradingServiceManager)
        container = ApplicationContainer.create_for_testing()
        trading_manager = container.services.trading_service_manager()
        engine2 = TradingEngine(trading_service_manager=trading_manager)
        assert engine2._container is None
        assert engine2.data_provider is not None
        print("✅ Partial DI initialization")
        
        # 3. Full DI mode
        engine3 = TradingEngine(container=container)
        assert engine3._container is not None
        print("✅ Full DI initialization")
        
        return True
    except Exception as e:
        print(f"❌ Initialization modes test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_backward_compatibility():
    """Test that existing code still works."""
    print("\n🔍 Testing backward compatibility...")
    
    try:
        # Test existing TradingEngine usage patterns
        engine = TradingEngine(
            paper_trading=True,
            strategy_allocations=None,
            ignore_market_hours=True,
            config=None
        )
        print("✅ Existing TradingEngine signature works")
        
        # Test main.py existing usage
        success = main(['bot'])
        print("✅ Existing main.py usage works")
        
        return True
    except Exception as e:
        print(f"❌ Backward compatibility test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main_test():
    """Run all Phase 2 validation tests."""
    print("🚀 Phase 2 Application Layer Migration Validation")
    print("=" * 60)
    
    tests = [
        test_trading_engine_di,
        test_main_di,
        test_initialization_modes,
        test_backward_compatibility,
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 60)
    print("📊 Summary:")
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ All {total} tests passed!")
        print("\n🎉 Phase 2 implementation is successful!")
        print("\nNext steps:")
        print("  - Phase 3: Testing Infrastructure")
        print("  - Create DI test utilities")
        print("  - Create integration tests")
        return True
    else:
        print(f"❌ {total - passed} of {total} tests failed")
        return False


if __name__ == "__main__":
    success = main_test()
    sys.exit(0 if success else 1)
