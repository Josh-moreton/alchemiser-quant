#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

Strategy data adapters and feature pipelines.

Provides thin wrappers around shared data sources for strategy consumption.

Public API:
    FeaturePipeline: Utility for computing features from raw market data
    MarketDataProvider: Protocol defining market data provider interface
    StrategyMarketDataAdapter: Alpaca-backed market data adapter implementation
    IndicatorLambdaClient: Lambda client for invoking Indicators Lambda

Module boundaries:
    - Imports from shared only (no portfolio/execution dependencies)
    - Re-exports adapter interfaces for strategy orchestration
    - Enforces dependency inversion via Protocol pattern

Note: StrategyMarketDataAdapter is lazily imported because it depends on
alpaca-py, which is not available in the Strategy Lambda runtime
(uses cached S3 data via CachedMarketDataAdapter instead).
"""

from __future__ import annotations

from .feature_pipeline import FeaturePipeline
from .indicator_lambda_client import IndicatorLambdaClient

__all__ = [
    "FeaturePipeline",
    "IndicatorLambdaClient",
    "MarketDataProvider",
    "StrategyMarketDataAdapter",
]

# Version for compatibility tracking
__version__ = "2.0.0"


def __getattr__(name: str) -> object:
    """Lazy import for adapters that depend on alpaca-py."""
    if name == "MarketDataProvider":
        from .market_data_adapter import MarketDataProvider

        return MarketDataProvider
    if name == "StrategyMarketDataAdapter":
        from .market_data_adapter import StrategyMarketDataAdapter

        return StrategyMarketDataAdapter
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
