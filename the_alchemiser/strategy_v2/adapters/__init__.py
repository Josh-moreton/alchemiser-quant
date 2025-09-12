#!/usr/bin/env python3
"""Business Unit: strategy | Status: current

Strategy data adapters and feature pipelines.

Provides thin wrappers around shared data sources for strategy consumption.
"""

from __future__ import annotations

from .feature_pipeline import FeaturePipeline
from .market_data_adapter import MarketDataProvider, StrategyMarketDataAdapter

__all__ = [
    "FeaturePipeline",
    "MarketDataProvider",
    "StrategyMarketDataAdapter",
]
