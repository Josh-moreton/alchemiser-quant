"""Utility functions and helpers.

Business Unit: shared | Status: current

Cross-cutting utilities and error handling.

Note: Alpaca-specific utilities are NOT imported at module level to avoid
pulling in alpaca-py for Lambdas that don't need it (e.g., Strategy Lambda).
Use explicit imports: `from the_alchemiser.shared.utils.alpaca_error_handler import ...`
"""

from __future__ import annotations

from typing import TYPE_CHECKING

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

# Lazy imports for Alpaca utilities to avoid importing alpaca-py at module load
# These are accessed via __getattr__ below
if TYPE_CHECKING:
    from .alpaca_error_handler import AlpacaErrorHandler, alpaca_retry_context


def __getattr__(name: str) -> object:
    """Lazy import for Alpaca utilities to avoid importing alpaca-py at module load."""
    if name in ("AlpacaErrorHandler", "alpaca_retry_context"):
        from .alpaca_error_handler import AlpacaErrorHandler, alpaca_retry_context

        if name == "AlpacaErrorHandler":
            return AlpacaErrorHandler
        return alpaca_retry_context
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "AlchemiserError",
    "AlpacaErrorHandler",
    "ConfigurationError",
    "DataProviderError",
    "OrderExecutionError",
    "PortfolioError",
    "StrategyExecutionError",
    "TradingClientError",
    "ValidationError",
    "alpaca_retry_context",
]
