"""Business Unit: utilities; Status: current.

Error handling infrastructure for The Alchemiser Trading System.

Provides centralized error handling with:
- Exception classes for domain-specific errors
- Translation decorators for exception mapping

Note: This is a minimal implementation to support migration from services.errors
"""

from __future__ import annotations

from .decorators import (
    translate_config_errors,
    translate_market_data_errors,
    translate_service_errors,
    translate_streaming_errors,
    translate_trading_errors,
)
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
    # Translation decorators
    "translate_config_errors",
    "translate_market_data_errors",
    "translate_service_errors",
    "translate_streaming_errors",
    "translate_trading_errors",
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