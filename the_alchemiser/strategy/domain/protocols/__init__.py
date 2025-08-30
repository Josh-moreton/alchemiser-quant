"""Business Unit: strategy & signal generation | Status: current."""

from __future__ import annotations

from .strategy_engine import StrategyEngine

# DEPRECATION NOTICE: MarketDataPort from this module is deprecated.
# Use the canonical MarketDataPort from:
# the_alchemiser.domain.market_data.protocols.market_data_port
#
# For strategies expecting DataFrame methods, use StrategyMarketDataAdapter:
# from the_alchemiser.anti_corruption.market_data.strategy_adapter_mapping import StrategyMarketDataAdapter

__all__ = ["StrategyEngine"]
