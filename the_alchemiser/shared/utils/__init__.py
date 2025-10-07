"""Utility functions and helpers.

Business Unit: shared | Status: current

Cross-cutting utilities and error handling.
"""

from __future__ import annotations

# Core exception types - most commonly used
from ..errors.exceptions import (
    AlchemiserError,
    ConfigurationError,
    DataProviderError,
    OrderExecutionError,
    PortfolioError,
    StrategyExecutionError,
    TradingClientError,
    ValidationError,
)

# Alpaca error handling utilities
from .alpaca_error_handler import AlpacaErrorHandler, alpaca_retry_context

# Error reporting utilities
from .error_reporter import ErrorReporter, get_error_reporter, report_error_globally

__all__ = [
    "AlchemiserError",
    "AlpacaErrorHandler",
    "ConfigurationError",
    "DataProviderError",
    "ErrorReporter",
    "OrderExecutionError",
    "PortfolioError",
    "StrategyExecutionError",
    "TradingClientError",
    "ValidationError",
    "alpaca_retry_context",
    "get_error_reporter",
    "report_error_globally",
]
