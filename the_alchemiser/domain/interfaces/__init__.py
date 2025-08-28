"""Business Unit: utilities; Status: current.

Domain Layer Interfaces.

This module defines the core interfaces for our trading system, following the
eventual architecture vision while being compatible with current implementations.

These interfaces represent the contracts that our service and application layers
will depend on, allowing us to swap implementations and improve testability.
"""
from __future__ import annotations


from .account_repository import AccountRepository
from .market_data_repository import MarketDataRepository
from .trading_repository import TradingRepository

__all__ = [
    "AccountRepository",
    "MarketDataRepository",
    "TradingRepository",
]
