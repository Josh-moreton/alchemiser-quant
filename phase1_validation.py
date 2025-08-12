#!/usr/bin/env python3
"""
Phase 1 Validation Script
Tests the dependency injection container infrastructure
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from the_alchemiser.container.application_container import ApplicationContainer
from the_alchemiser.services.service_factory import ServiceFactory


def test_container_creation():
    """Test that containers can be created successfully."""
    print("🔍 Testing container creation...")

    try:
        # Test basic container
        container = ApplicationContainer()
        print("✅ Basic container created")

        # Test environment-specific containers
        test_container = ApplicationContainer.create_for_environment("test")
        print("✅ Test environment container created")

        prod_container = ApplicationContainer.create_for_environment("production")
        print("✅ Production environment container created")

        # Test testing container with mocks
        testing_container = ApplicationContainer.create_for_testing()
        print("✅ Testing container with mocks created")

        return True
    except Exception as e:
        print(f"❌ Container creation failed: {e}")
        return False


def test_service_creation():
    """Test that all services can be created via DI."""
    print("\n🔍 Testing service creation...")

    try:
        container = ApplicationContainer.create_for_testing()

        # Test individual enhanced services
        order_service = container.services.order_service()
        print("✅ OrderService created")

        position_service = container.services.position_service()
        print("✅ PositionService created")

        market_data_service = container.services.market_data_service()
        print("✅ MarketDataService created")

        account_service = container.services.account_service()
        print("✅ AccountService created")

        # Test TradingServiceManager
        trading_manager = container.services.trading_service_manager()
        print("✅ TradingServiceManager created")

        # Verify they have expected attributes
        assert hasattr(order_service, "_trading")
        assert hasattr(position_service, "_trading")
        assert hasattr(market_data_service, "_market_data")
        assert hasattr(account_service, "account_repository")
        assert hasattr(trading_manager, "alpaca_manager")

        print("✅ All services have expected dependencies injected")

        return True
    except Exception as e:
        print(f"❌ Service creation failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_service_factory():
    """Test the optional ServiceFactory."""
    print("\n🔍 Testing ServiceFactory...")

    try:
        # Test factory initialization
        container = ApplicationContainer.create_for_testing()
        ServiceFactory.initialize(container)
        print("✅ ServiceFactory initialized")

        # Test service creation through factory
        trading_manager = ServiceFactory.create_trading_service_manager()
        print("✅ TradingServiceManager created via factory")

        # Test backward compatibility (no DI)
        ServiceFactory.initialize(None)
        traditional_manager = ServiceFactory.create_trading_service_manager(
            api_key="test_key", secret_key="test_secret", paper=True
        )
        print("✅ TradingServiceManager created via factory (traditional mode)")

        return True
    except Exception as e:
        print(f"❌ ServiceFactory test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_backward_compatibility():
    """Test that existing code still works."""
    print("\n🔍 Testing backward compatibility...")

    try:
        # Test direct TradingServiceManager creation (existing code)
        from the_alchemiser.services.enhanced.trading_service_manager import TradingServiceManager

        manager = TradingServiceManager("test_key", "test_secret", paper=True)
        print("✅ TradingServiceManager direct instantiation works")

        # Test enhanced services direct creation
        from the_alchemiser.services.enhanced.order_service import OrderService
        from the_alchemiser.services.alpaca_manager import AlpacaManager

        alpaca_manager = AlpacaManager("test_key", "test_secret", paper=True)
        order_service = OrderService(trading_repo=alpaca_manager)
        print("✅ Enhanced services direct instantiation works")

        return True
    except Exception as e:
        print(f"❌ Backward compatibility test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all Phase 1 validation tests."""
    print("🚀 Phase 1 DI Infrastructure Validation")
    print("=" * 50)

    tests = [
        test_container_creation,
        test_service_creation,
        test_service_factory,
        test_backward_compatibility,
    ]

    results = []
    for test in tests:
        results.append(test())

    print("\n" + "=" * 50)
    print("📊 Summary:")
    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"✅ All {total} tests passed!")
        print("\n🎉 Phase 1 implementation is successful!")
        print("\nNext steps:")
        print("  - Phase 2: Application Layer Migration")
        print("  - Update TradingEngine for DI support")
        print("  - Update main.py and lambda_handler.py")
        return True
    else:
        print(f"❌ {total - passed} of {total} tests failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
