"""Business Unit: utilities; Status: current.

Error handling infrastructure for The Alchemiser Trading System.

Provides centralized error handling with:
- Exception classes for domain-specific errors
- Translation decorators for exception mapping
- Error context data for structured error information

Note: This is a minimal implementation to support migration from services.errors
"""

from __future__ import annotations

from .context import ErrorContextData, create_error_context
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
from .handler import (
    TradingSystemErrorHandler,
    handle_errors_with_retry,
    handle_trading_error,
)

__all__ = [
    # Error context
    "ErrorContextData",
    "create_error_context",
    # Translation decorators
    "translate_config_errors",
    "translate_market_data_errors",
    "translate_service_errors",
    "translate_streaming_errors",
    "translate_trading_errors",
    # Handler functions
    "TradingSystemErrorHandler",
    "handle_errors_with_retry", 
    "handle_trading_error",
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