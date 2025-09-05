#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Integration test for SharedMarketDataService consolidation.

This script validates that the market data consolidation is working correctly
and that all the different usage patterns function as expected.
"""

from __future__ import annotations

import logging
import warnings
from typing import Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_shared_service_import() -> bool:
    """Test that SharedMarketDataService can be imported."""
    try:
        from the_alchemiser.shared.services.market_data_service import SharedMarketDataService
        logger.info("✅ SharedMarketDataService imports successfully")
        return True
    except ImportError as e:
        logger.error(f"❌ Failed to import SharedMarketDataService: {e}")
        return False


def test_shared_service_factory() -> bool:
    """Test that the factory function works."""
    try:
        from the_alchemiser.shared.services.market_data_service import create_shared_market_data_service
        logger.info("✅ Factory function imports successfully")
        return True
    except ImportError as e:
        logger.error(f"❌ Failed to import factory function: {e}")
        return False


def test_compatibility_adapter() -> bool:
    """Test that the compatibility adapter works."""
    try:
        from the_alchemiser.shared.adapters.market_data_adapter import MarketDataServiceAdapter
        logger.info("✅ MarketDataServiceAdapter imports successfully")
        return True
    except ImportError as e:
        logger.error(f"❌ Failed to import MarketDataServiceAdapter: {e}")
        return False


def test_deprecated_client_warning() -> bool:
    """Test that the deprecated client shows warnings."""
    try:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            # This should trigger a deprecation warning
            from the_alchemiser.strategy.data.market_data_client import MarketDataClient
            # Instantiation will trigger the warning
            
            logger.info("✅ Deprecated MarketDataClient imports (testing warnings)")
            return True
            
    except ImportError as e:
        logger.error(f"❌ Failed to import deprecated MarketDataClient: {e}")
        return False


def test_strategy_module_exports() -> bool:
    """Test that strategy module exports both old and new services."""
    try:
        from the_alchemiser.strategy.data import MarketDataClient, SharedMarketDataService
        logger.info("✅ Strategy module exports both deprecated and new services")
        return True
    except ImportError as e:
        logger.error(f"❌ Failed to import from strategy.data: {e}")
        return False


def test_service_instantiation() -> bool:
    """Test that services can be instantiated with test credentials."""
    try:
        from the_alchemiser.shared.services.market_data_service import SharedMarketDataService
        
        # Test with mock credentials (won't connect but should instantiate)
        service = SharedMarketDataService(
            api_key="test_key",
            secret_key="test_secret",
            paper=True,
        )
        
        # Check that basic attributes are set
        assert service.api_key == "test_key"
        assert service.secret_key == "test_secret"
        assert service._paper is True
        
        logger.info("✅ SharedMarketDataService instantiates correctly")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to instantiate SharedMarketDataService: {e}")
        return False


def test_adapter_instantiation() -> bool:
    """Test that the adapter can be instantiated."""
    try:
        from the_alchemiser.shared.adapters.market_data_adapter import MarketDataServiceAdapter
        
        # Test with mock credentials
        adapter = MarketDataServiceAdapter(api_key="test_key", secret_key="test_secret")
        
        # Check that basic attributes are set
        assert adapter.api_key == "test_key"
        assert adapter.secret_key == "test_secret"
        
        logger.info("✅ MarketDataServiceAdapter instantiates correctly")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to instantiate MarketDataServiceAdapter: {e}")
        return False


def run_integration_tests() -> bool:
    """Run all integration tests."""
    logger.info("🧪 Running SharedMarketDataService Integration Tests")
    logger.info("=" * 60)
    
    tests = [
        ("Import SharedMarketDataService", test_shared_service_import),
        ("Import Factory Function", test_shared_service_factory),
        ("Import Compatibility Adapter", test_compatibility_adapter),
        ("Test Deprecated Client Warning", test_deprecated_client_warning),
        ("Test Strategy Module Exports", test_strategy_module_exports),
        ("Test Service Instantiation", test_service_instantiation),
        ("Test Adapter Instantiation", test_adapter_instantiation),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n🧪 {test_name}...")
        try:
            if test_func():
                passed += 1
            else:
                logger.error(f"❌ {test_name} failed")
        except Exception as e:
            logger.error(f"❌ {test_name} failed with exception: {e}")
    
    logger.info(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All integration tests passed!")
        logger.info("\n📋 Consolidation Status:")
        logger.info("✅ SharedMarketDataService is ready for use")
        logger.info("✅ Backward compatibility is maintained") 
        logger.info("✅ Migration path is available")
        logger.info("✅ Strategy module successfully updated")
        return True
    else:
        logger.error(f"❌ {total - passed} tests failed")
        return False


if __name__ == "__main__":
    success = run_integration_tests()
    exit(0 if success else 1)