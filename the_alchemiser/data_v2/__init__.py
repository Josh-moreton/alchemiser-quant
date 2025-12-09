"""Business Unit: data | Status: current.

Data management module for historical market data.

This module handles fetching, storing, and retrieving historical market data
from S3 in Parquet format. It eliminates rate limiting issues by maintaining
a local data store that is updated incrementally after market close.

Components:
    - MarketDataStore: S3-backed Parquet storage with local caching
    - DataRefreshService: Orchestrates incremental data updates from Alpaca
    - CachedMarketDataAdapter: MarketDataPort implementation using S3 cache
    - SymbolExtractor: Discovers symbols from strategy DSL files
"""

from the_alchemiser.data_v2.cached_market_data_adapter import (
    CachedMarketDataAdapter,
)
from the_alchemiser.data_v2.data_refresh_service import DataRefreshService
from the_alchemiser.data_v2.market_data_store import MarketDataStore, SymbolMetadata
from the_alchemiser.data_v2.symbol_extractor import (
    get_all_configured_symbols,
)

__all__ = [
    "CachedMarketDataAdapter",
    "DataRefreshService",
    "MarketDataStore",
    "SymbolMetadata",
    "get_all_configured_symbols",
]
