"""Business Unit: utilities; Status: current.

Error handling infrastructure for The Alchemiser Trading System.

Provides centralized error handling with:
- Exception classes for domain-specific errors

Note: This is a minimal implementation to support migration from services.errors
"""

from __future__ import annotations

from .exceptions import (
    AlchemiserError,
    ConfigurationError,
    DataProviderError,
    InsufficientFundsError,
    MarketDataError,
    NotificationError,
    OrderExecutionError,
    PositionValidationError,
    StrategyExecutionError,
    TradingClientError,
)

__all__ = [
    # Exception classes
    "AlchemiserError",
    "ConfigurationError",
    "DataProviderError",
    "InsufficientFundsError",
    "MarketDataError",
    "NotificationError",
    "OrderExecutionError",
    "PositionValidationError",
    "StrategyExecutionError",
    "TradingClientError",
]