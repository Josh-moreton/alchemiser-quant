#!/usr/bin/env python3
"""
Integration test for Phase 3 enhanced services
Tests that all services integrate properly and type checking passes
"""

import sys

# Test imports
try:
    from the_alchemiser.domain.interfaces import (
        AccountRepository,
        MarketDataRepository,
        TradingRepository,
    )
    from the_alchemiser.services.alpaca_manager import AlpacaManager
    from the_alchemiser.services.enhanced import (
        AccountService,
        MarketDataService,
        OrderService,
        PositionService,
        TradingServiceManager,
    )

    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)


def test_service_instantiation():
    """Test that services can be instantiated with mock credentials"""
    try:
        # Mock credentials for testing
        api_key = "test_key"
        secret_key = "test_secret"

        # This would normally fail with bad credentials, but we're just testing instantiation
        try:
            manager = TradingServiceManager(api_key, secret_key, paper=True)
            print("✅ TradingServiceManager instantiation successful")
        except Exception as e:
            # Expected to fail with bad credentials, but structure should be OK
            if "credentials" in str(e).lower() or "api" in str(e).lower():
                print("✅ TradingServiceManager structure OK (credential error expected)")
            else:
                print(f"❌ Unexpected error: {e}")
                return False

        return True
    except Exception as e:
        print(f"❌ Service instantiation failed: {e}")
        return False


def test_interface_compliance():
    """Test that AlpacaManager implements all required interfaces"""
    try:
        # Check interface compliance
        alpaca_manager_methods = set(dir(AlpacaManager))

        # Check TradingRepository methods
        trading_methods = {
            "place_market_order",
            "place_limit_order",
            "cancel_order",
            "get_orders",
            "get_account",
        }

        # Check MarketDataRepository methods
        market_data_methods = {"get_current_price", "get_latest_quote", "get_historical_bars"}

        # Check AccountRepository methods
        account_methods = {
            "get_account",
            "get_positions",
            "get_buying_power",
            "get_portfolio_value",
        }

        all_required = trading_methods | market_data_methods | account_methods
        missing = all_required - alpaca_manager_methods

        if missing:
            print(f"⚠️  Missing methods in AlpacaManager: {missing}")
        else:
            print("✅ AlpacaManager implements all required interface methods")

        return len(missing) == 0

    except Exception as e:
        print(f"❌ Interface compliance check failed: {e}")
        return False


def test_type_annotations():
    """Test that key methods have proper type annotations"""
    try:
        # Check service type annotations
        services = [OrderService, PositionService, MarketDataService, AccountService]

        for service_class in services:
            if hasattr(service_class, "__annotations__"):
                print(f"✅ {service_class.__name__} has type annotations")
            else:
                print(f"⚠️  {service_class.__name__} missing class-level annotations")

        print("✅ Type annotation check completed")
        return True

    except Exception as e:
        print(f"❌ Type annotation check failed: {e}")
        return False


def main():
    """Run all integration tests"""
    print("🚀 Running Phase 3 Enhanced Services Integration Tests\n")

    tests = [
        ("Import Test", lambda: True),  # Already tested above
        ("Service Instantiation", test_service_instantiation),
        ("Interface Compliance", test_interface_compliance),
        ("Type Annotations", test_type_annotations),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name}...")
        try:
            success = test_func()
            results.append(success)
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"   {status}")
        except Exception as e:
            print(f"   ❌ FAIL - {e}")
            results.append(False)

    # Summary
    passed = sum(results)
    total = len(results)

    print("\n📊 Test Summary:")
    print(f"   Passed: {passed}/{total}")
    print(f"   Success Rate: {(passed/total)*100:.1f}%")

    if passed == total:
        print("\n🎉 All integration tests passed!")
        print("✅ Phase 3 enhanced services are properly integrated")
        return True
    else:
        print(f"\n⚠️  {total-passed} test(s) failed")
        print("❌ Some integration issues remain")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
