"""Business Unit: strategy & signal generation; Status: current.

Strategy context domain errors.

Strategy-specific exceptions for signal generation, indicator calculation,
and strategy execution failures.
"""

from __future__ import annotations

from typing import Any


class StrategyError(Exception):
    """Base exception for strategy context errors."""

    def __init__(self, message: str, context: dict[str, Any] | None = None) -> None:
        """Initialize strategy error with optional contextual data."""
        super().__init__(message)
        self.message = message
        self.context = context or {}


class StrategyExecutionError(StrategyError):
    """Raised when strategy execution fails."""

    def __init__(self, message: str, strategy_name: str | None = None) -> None:
        """Create a strategy execution error."""
        context = {"strategy_name": strategy_name} if strategy_name else {}
        super().__init__(message, context)
        self.strategy_name = strategy_name


class IndicatorCalculationError(StrategyError):
    """Raised when technical indicator calculations fail."""

    def __init__(
        self, message: str, indicator_name: str | None = None, symbol: str | None = None
    ) -> None:
        """Raise when an indicator cannot be computed."""
        context = {}
        if indicator_name:
            context["indicator_name"] = indicator_name
        if symbol:
            context["symbol"] = symbol
        super().__init__(message, context)
        self.indicator_name = indicator_name
        self.symbol = symbol


class MarketDataError(StrategyError):
    """Raised when market data retrieval fails in strategy context."""

    def __init__(
        self, message: str, symbol: str | None = None, data_type: str | None = None
    ) -> None:
        """Raise when market data retrieval fails."""
        context = {}
        if symbol:
            context["symbol"] = symbol
        if data_type:
            context["data_type"] = data_type
        super().__init__(message, context)
        self.symbol = symbol
        self.data_type = data_type