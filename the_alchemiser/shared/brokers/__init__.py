"""Business Unit: shared | Status: current.

Broker abstractions and utilities.

This package provides broker-agnostic interfaces and utilities that allow
the rest of the system to work with trading operations without being tied
to specific broker implementations.

Contains:
- AlpacaManager: Facade composing focused adapters for backwards compatibility
- Focused adapters: AlpacaTradingAdapter, AlpacaMarketDataAdapter, AlpacaAccountAdapter
- Specialized components: AlpacaStreamingManager, AlpacaAssetCache
- Utilities: alpaca_utils, alpaca_mappers
"""

from __future__ import annotations

from .alpaca_account_adapter import AlpacaAccountAdapter
from .alpaca_assets import AlpacaAssetCache
from .alpaca_manager import AlpacaManager, create_alpaca_manager
from .alpaca_market_data_adapter import AlpacaMarketDataAdapter
from .alpaca_streaming import AlpacaStreamingManager
from .alpaca_trading_adapter import AlpacaTradingAdapter

__all__ = [
    "AlpacaManager",
    "create_alpaca_manager",
    "AlpacaTradingAdapter",
    "AlpacaMarketDataAdapter", 
    "AlpacaAccountAdapter",
    "AlpacaStreamingManager",
    "AlpacaAssetCache",
]
