"""Business Unit: utilities; Status: current.

Domain error types for The Alchemiser.

Pure business domain exceptions without side effects (no logging, no network calls).
"""

from __future__ import annotations

from .exceptions import (
    AlchemiserError,
    BuyingPowerError,
    ConfigurationError,
    DataProviderError,
    InsufficientFundsError,
    MarketDataError,
    NotificationError,
    OrderExecutionError,
    PositionValidationError,
    StrategyExecutionError,
    TradingClientError,
    ValidationError,
)

__all__ = [
    "AlchemiserError",
    "BuyingPowerError", 
    "ConfigurationError",
    "DataProviderError",
    "InsufficientFundsError",
    "MarketDataError",
    "NotificationError",
    "OrderExecutionError",
    "PositionValidationError",
    "StrategyExecutionError",
    "TradingClientError",
    "ValidationError",
]