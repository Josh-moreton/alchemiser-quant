"""Core services for the trading system.

This package contains modularized services that replace the monolithic
``UnifiedDataProvider``:

* ConfigService: Configuration management
* SecretsService: Credential management
* MarketDataClient: Market data retrieval
* TradingClientService: Trading operations
* StreamingService: Real-time data streaming
* CacheManager: Configurable caching with TTL
* AccountService: Account and position management
"""

from .account_service import AccountService
from .cache_manager import CacheManager
from .config_service import ConfigService
from .market_data_client import MarketDataClient
from .secrets_service import SecretsService
from .streaming_service import StreamingService
from .trading_client_service import TradingClientService

__all__ = [
    "AccountService",
    "CacheManager",
    "ConfigService",
    "MarketDataClient",
    "SecretsService",
    "StreamingService",
    "TradingClientService",
]
