"""Business Unit: data | Status: current.

Data management module for historical market data.

This module handles fetching, storing, and retrieving historical market data
from S3 in Parquet format. It eliminates rate limiting issues by maintaining
a local data store that is updated incrementally after market close.

Components:
    - MarketDataStore: S3-backed Parquet storage with local caching
    - DataRefreshService: Orchestrates incremental data updates from Alpaca (lazy import)
    - CachedMarketDataAdapter: MarketDataPort implementation using S3 cache
    - SymbolExtractor: Discovers symbols from strategy DSL files

Note: DataRefreshService is NOT imported at module level to avoid pulling in
alpaca-py for Lambdas that only need to READ from the cache (e.g., Strategy Lambda).
Use explicit import: `from the_alchemiser.data_v2.data_refresh_service import DataRefreshService`
"""

from typing import TYPE_CHECKING

from the_alchemiser.data_v2.cached_market_data_adapter import (
    CachedMarketDataAdapter,
)
from the_alchemiser.data_v2.market_data_store import MarketDataStore, SymbolMetadata
from the_alchemiser.data_v2.symbol_extractor import (
    get_all_configured_symbols,
)

# Lazy import for DataRefreshService to avoid alpaca-py dependency
if TYPE_CHECKING:
    from the_alchemiser.data_v2.data_refresh_service import DataRefreshService


def __getattr__(name: str) -> object:
    """Lazy import for components that require alpaca-py."""
    if name == "DataRefreshService":
        from the_alchemiser.data_v2.data_refresh_service import DataRefreshService

        return DataRefreshService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "CachedMarketDataAdapter",
    "DataRefreshService",
    "MarketDataStore",
    "SymbolMetadata",
    "get_all_configured_symbols",
]
