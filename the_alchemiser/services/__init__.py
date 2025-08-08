"""
Core services for the trading system.

This package contains modularized services that replace the monolithic UnifiedDataProvider:
- ConfigService: Configuration management
- SecretsService: Credential management
- MarketDataClient: Market data retrieval
- TradingClientService: Trading operations
- StreamingService: Real-time data streaming
- CacheManager: Configurable caching with TTL
- AccountService: Account and position management
"""

# Note: Lazy imports to avoid circular dependencies and initialization issues
# Import services individually as needed rather than all at once

__all__ = [
    "ConfigService",
    "SecretsService",
    "MarketDataClient",
    "TradingClientService",
    "StreamingService",
    "CacheManager",
    "AccountService",
]
