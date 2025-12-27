#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

Strategy data adapters and feature pipelines.

Provides thin wrappers around shared data sources for strategy consumption.

Public API:
    FeaturePipeline: Utility for computing features from raw market data
    MarketDataProvider: Protocol defining market data provider interface
    StrategyMarketDataAdapter: Alpaca-backed market data adapter implementation
    S3MarketDataAdapter: Read-only S3-backed adapter with EventBridge fetch requests

Module boundaries:
    - Imports from shared only (no portfolio/execution dependencies)
    - Re-exports adapter interfaces for strategy orchestration
    - Enforces dependency inversion via Protocol pattern
"""

from __future__ import annotations

from .feature_pipeline import FeaturePipeline

__all__ = [
    "FeaturePipeline",
    "MarketDataProvider",
    "S3MarketDataAdapter",
    "StrategyMarketDataAdapter",
]

# Version for compatibility tracking
__version__ = "2.0.0"


def __getattr__(name: str) -> object:
    """Lazy import for adapters that depend on alpaca-py or boto3."""
    if name == "MarketDataProvider":
        from .market_data_adapter import MarketDataProvider

        return MarketDataProvider
    if name == "StrategyMarketDataAdapter":
        from .market_data_adapter import StrategyMarketDataAdapter

        return StrategyMarketDataAdapter
    if name == "S3MarketDataAdapter":
        from .s3_market_data_adapter import S3MarketDataAdapter

        return S3MarketDataAdapter
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
