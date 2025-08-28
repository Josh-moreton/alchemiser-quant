"""Business Unit: utilities; Status: current."""

from __future__ import annotations

from the_alchemiser.domain.strategies.protocols.strategy_engine import StrategyEngine

# DEPRECATION NOTICE: MarketDataPort from this module is deprecated.
# Use the canonical MarketDataPort from:
# the_alchemiser.domain.market_data.protocols.market_data_port
#
# For strategies expecting DataFrame methods, use StrategyMarketDataAdapter:
# from the_alchemiser.strategy.application.mapping.strategy_market_data_adapter import StrategyMarketDataAdapter

__all__ = ["StrategyEngine"]
