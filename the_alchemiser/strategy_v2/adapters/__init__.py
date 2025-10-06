#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

Strategy data adapters and feature pipelines.

Provides thin wrappers around shared data sources for strategy consumption.

Public API:
    FeaturePipeline: Utility for computing features from raw market data
    MarketDataProvider: Protocol defining market data provider interface
    StrategyMarketDataAdapter: Alpaca-backed market data adapter implementation

Module boundaries:
    - Imports from shared only (no portfolio/execution dependencies)
    - Re-exports adapter interfaces for strategy orchestration
    - Enforces dependency inversion via Protocol pattern
"""

from __future__ import annotations

from .feature_pipeline import FeaturePipeline
from .market_data_adapter import MarketDataProvider, StrategyMarketDataAdapter

__all__ = [
    "FeaturePipeline",
    "MarketDataProvider",
    "StrategyMarketDataAdapter",
]

# Version for compatibility tracking
__version__ = "2.0.0"
