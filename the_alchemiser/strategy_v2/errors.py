#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

Strategy_v2 error types and exceptions.

Provides typed exceptions for strategy execution with module context
for traceability and error handling.
"""

from __future__ import annotations


class StrategyV2Error(Exception):
    """Base exception for strategy_v2 module."""

    def __init__(
        self,
        message: str,
        module: str = "strategy_v2",
        correlation_id: str | None = None,
        **kwargs: str | float | int | bool | None,
    ) -> None:
        """Initialize strategy error.

        Args:
            message: Error message
            module: Module where error occurred
            correlation_id: Optional correlation ID for tracking
            **kwargs: Additional error context

        """
        super().__init__(message)
        self.module = module
        self.correlation_id = correlation_id
        self.context = kwargs


class StrategyExecutionError(StrategyV2Error):
    """Error during strategy execution."""

    def __init__(
        self,
        message: str,
        strategy_id: str | None = None,
        **kwargs: str | float | int | bool | None,
    ) -> None:
        """Initialize strategy execution error.

        Args:
            message: Error message
            strategy_id: Strategy that failed
            **kwargs: Additional context

        """
        super().__init__(message, module="strategy_v2.core.orchestrator", **kwargs)
        self.strategy_id = strategy_id


class ConfigurationError(StrategyV2Error):
    """Error in strategy configuration or context."""

    def __init__(self, message: str, **kwargs: str | float | int | bool | None) -> None:
        """Initialize configuration error.

        Args:
            message: Error message
            **kwargs: Additional context

        """
        super().__init__(message, module="strategy_v2.models.context", **kwargs)


class MarketDataError(StrategyV2Error):
    """Error accessing or processing market data."""

    def __init__(
        self,
        message: str,
        symbol: str | None = None,
        **kwargs: str | float | int | bool | None,
    ) -> None:
        """Initialize market data error.

        Args:
            message: Error message
            symbol: Symbol that caused the error
            **kwargs: Additional context

        """
        super().__init__(
            message, module="strategy_v2.adapters.market_data_adapter", **kwargs
        )
        self.symbol = symbol
