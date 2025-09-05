#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Migration Guide for Market Data Services.

This script demonstrates how to migrate from the deprecated strategy-specific
MarketDataClient to the new SharedMarketDataService in the shared module.

Example migrations:
1. Direct replacement with SharedMarketDataService
2. Using the compatibility adapter for gradual migration
3. Best practices for the new service
"""

from __future__ import annotations

# --- BEFORE (Deprecated) ---
def old_usage_example() -> None:
    """Example of deprecated MarketDataClient usage."""
    from the_alchemiser.strategy.data.market_data_client import MarketDataClient
    
    # This will now show deprecation warnings
    client = MarketDataClient(api_key="your_key", secret_key="your_secret")
    df = client.get_historical_bars("AAPL", period="1y", interval="1d")
    quote = client.get_latest_quote("AAPL")
    price = client.get_current_price_from_quote("AAPL")


# --- AFTER (Recommended) ---
def new_usage_example() -> None:
    """Example of new SharedMarketDataService usage."""
    from the_alchemiser.shared.services import SharedMarketDataService
    
    # Direct replacement with improved functionality
    service = SharedMarketDataService(api_key="your_key", secret_key="your_secret")
    
    # Same method signatures, better performance
    df = service.get_historical_bars("AAPL", period="1y", interval="1d")
    quote = service.get_latest_quote("AAPL")
    price = service.get_current_price("AAPL")  # Note: method name changed
    
    # New features: caching control
    service.clear_cache()


# --- GRADUAL MIGRATION (Compatibility Adapter) ---
def adapter_usage_example() -> None:
    """Example using compatibility adapter for gradual migration."""
    from the_alchemiser.shared.adapters import create_market_data_adapter
    
    # Drop-in replacement that uses SharedMarketDataService internally
    adapter = create_market_data_adapter(api_key="your_key", secret_key="your_secret")
    
    # Exact same interface as MarketDataClient
    df = adapter.get_historical_bars("AAPL", period="1y", interval="1d")
    quote = adapter.get_latest_quote("AAPL")
    price = adapter.get_current_price_from_quote("AAPL")


# --- FACTORY PATTERN ---
def factory_usage_example() -> None:
    """Example using factory function for consistent configuration."""
    from the_alchemiser.shared.services import create_shared_market_data_service
    
    # Factory function with configuration options
    service = create_shared_market_data_service(
        api_key="your_key",
        secret_key="your_secret",
        paper=True,  # Use paper trading
        cache_ttl_seconds=10,  # Custom cache TTL
        enable_validation=True,  # Enable data validation
    )
    
    df = service.get_historical_bars("AAPL", period="6mo", interval="1d")


if __name__ == "__main__":
    print("Market Data Service Migration Guide")
    print("=" * 40)
    print()
    print("1. OLD (Deprecated): strategy.data.MarketDataClient")
    print("   → Shows deprecation warnings")
    print("   → Limited to strategy module")
    print()
    print("2. NEW (Recommended): shared.services.SharedMarketDataService")
    print("   → Available to all modules")
    print("   → Better caching and validation")
    print("   → Consistent error handling")
    print()
    print("3. GRADUAL: shared.adapters.MarketDataServiceAdapter")
    print("   → Drop-in replacement for existing code")
    print("   → Uses SharedMarketDataService internally")
    print("   → Allows gradual migration")
    print()
    print("See function examples in this file for detailed usage patterns.")