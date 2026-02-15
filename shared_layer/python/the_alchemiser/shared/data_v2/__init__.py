"""Business Unit: data | Status: current.

Shared data utilities for market data storage and retrieval.

This module provides utilities for reading/writing market data to S3:
- CachedMarketDataAdapter: Adapter for reading market data from S3 Parquet files
- MarketDataStore: Low-level S3 Parquet read/write operations
- GroupHistoryStore: S3-backed storage for group performance history

These utilities are used by:
- DataFunction: Writes market data to S3
- StrategyFunction: Reads market data from S3 for indicators
- Other Lambdas: Can read historical data from S3 as needed
"""

from __future__ import annotations

from the_alchemiser.shared.data_v2.group_history_store import (
    GroupHistoryStore,
    GroupMetadata,
)
from the_alchemiser.shared.data_v2.market_data_store import (
    AdjustmentInfo,
    MarketDataStore,
    SymbolMetadata,
)

__all__ = [
    "AdjustmentInfo",
    "GroupHistoryStore",
    "GroupMetadata",
    "MarketDataStore",
    "SymbolMetadata",
]
