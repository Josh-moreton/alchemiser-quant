"""Business Unit: data | Status: current.

Shared data utilities for market data storage and retrieval.

This module provides utilities for reading/writing market data to S3:
- CachedMarketDataAdapter: Adapter for reading market data from S3 Parquet files
- MarketDataStore: Low-level S3 Parquet read/write operations

These utilities are used by:
- DataFunction: Writes market data to S3
- StrategyFunction: Reads market data from S3 for indicators
- Other Lambdas: Can read historical data from S3 as needed
"""

from __future__ import annotations

__all__: list[str] = []
