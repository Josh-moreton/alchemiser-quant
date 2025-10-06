#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

Strategy_v2 error types and exceptions.

Provides typed exceptions for strategy execution with module context
for traceability and error handling. Supports correlation_id and causation_id
for event-driven workflows, with structured context for observability.

All exceptions support:
- correlation_id: Track requests across the system
- causation_id: Link events in event-driven workflows
- module: Identify error source for filtering
- context: Additional error metadata (kwargs)
- to_dict(): Serialize for structured logging

Example:
    >>> try:
    ...     raise StrategyExecutionError(
    ...         "Strategy failed",
    ...         strategy_id="nuclear",
    ...         correlation_id="signal-123",
    ...         causation_id="event-456",
    ...         symbol="SPY",
    ...     )
    ... except StrategyV2Error as e:
    ...     logger.error("Strategy error", extra=e.to_dict())
"""

from __future__ import annotations

from typing import Any


class StrategyV2Error(Exception):
    """Base exception for strategy_v2 module.
    
    Supports event-driven workflow patterns with correlation_id and causation_id.
    All context is preserved in the context dict for structured logging.
    """

    def __init__(
        self,
        message: str,
        module: str = "strategy_v2",
        correlation_id: str | None = None,
        causation_id: str | None = None,
        **kwargs: str | float | int | bool | None,
    ) -> None:
        """Initialize strategy error with traceability context.

        Args:
            message: Error message describing the failure
            module: Module where error occurred (defaults to "strategy_v2")
            correlation_id: Optional correlation ID for tracking across systems
            causation_id: Optional causation ID for event-driven workflows
            **kwargs: Additional error context (any JSON-serializable values)

        Example:
            >>> error = StrategyV2Error(
            ...     "Calculation failed",
            ...     correlation_id="req-123",
            ...     causation_id="event-456",
            ...     symbol="AAPL",
            ... )
        """
        super().__init__(message)
        self.message = message
        self.module = module
        self.correlation_id = correlation_id
        self.causation_id = causation_id
        self.context = kwargs

    def to_dict(self) -> dict[str, Any]:
        """Convert error to structured data for logging and reporting.
        
        Returns:
            Dictionary with error type, message, module, IDs, and context.
            
        Example:
            >>> error = StrategyV2Error("Test", correlation_id="123")
            >>> error.to_dict()
            {
                'error_type': 'StrategyV2Error',
                'message': 'Test',
                'module': 'strategy_v2',
                'correlation_id': '123',
                'causation_id': None,
                'context': {}
            }
        """
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "module": self.module,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "context": self.context,
        }


class StrategyExecutionError(StrategyV2Error):
    """Error during strategy execution.
    
    Raised when a strategy encounters an error during its execution phase.
    Includes strategy_id for identification and supports full traceability.
    """

    def __init__(
        self,
        message: str,
        strategy_id: str | None = None,
        correlation_id: str | None = None,
        causation_id: str | None = None,
        **kwargs: str | float | int | bool | None,
    ) -> None:
        """Initialize strategy execution error with strategy context.

        Args:
            message: Error message describing the execution failure
            strategy_id: Identifier of the strategy that failed (e.g., "nuclear", "tecl")
            correlation_id: Optional correlation ID for tracking
            causation_id: Optional causation ID for event workflows
            **kwargs: Additional context (e.g., symbol, reason, timestamp)

        Example:
            >>> error = StrategyExecutionError(
            ...     "Nuclear strategy failed",
            ...     strategy_id="nuclear",
            ...     correlation_id="req-123",
            ...     symbol="SPY",
            ... )
        """
        super().__init__(
            message,
            module="strategy_v2.core.orchestrator",
            correlation_id=correlation_id,
            causation_id=causation_id,
            **kwargs,
        )
        self.strategy_id = strategy_id


class ConfigurationError(StrategyV2Error):
    """Error in strategy configuration or context.
    
    Raised when strategy configuration is invalid or missing required values.
    Used during strategy initialization and context validation.
    """

    def __init__(
        self,
        message: str,
        correlation_id: str | None = None,
        causation_id: str | None = None,
        **kwargs: str | float | int | bool | None,
    ) -> None:
        """Initialize configuration error with validation context.

        Args:
            message: Error message describing the configuration issue
            correlation_id: Optional correlation ID for tracking
            causation_id: Optional causation ID for event workflows
            **kwargs: Additional context (e.g., config_key, expected_type)

        Example:
            >>> error = ConfigurationError(
            ...     "symbols cannot be empty",
            ...     config_key="symbols",
            ...     provided_value=[],
            ... )
        """
        super().__init__(
            message,
            module="strategy_v2.models.context",
            correlation_id=correlation_id,
            causation_id=causation_id,
            **kwargs,
        )


class MarketDataError(StrategyV2Error):
    """Error accessing or processing market data.
    
    Raised when market data fetching or processing fails. Includes symbol
    for tracking which asset caused the error.
    """

    def __init__(
        self,
        message: str,
        symbol: str | None = None,
        correlation_id: str | None = None,
        causation_id: str | None = None,
        **kwargs: str | float | int | bool | None,
    ) -> None:
        """Initialize market data error with data context.

        Args:
            message: Error message describing the data failure
            symbol: Symbol that caused the error (e.g., "AAPL", "SPY")
            correlation_id: Optional correlation ID for tracking
            causation_id: Optional causation ID for event workflows
            **kwargs: Additional context (e.g., timeframe, start_date, data_source)

        Example:
            >>> error = MarketDataError(
            ...     "Failed to fetch bars",
            ...     symbol="AAPL",
            ...     timeframe="1Day",
            ...     correlation_id="req-123",
            ... )
        """
        super().__init__(
            message,
            module="strategy_v2.adapters.market_data_adapter",
            correlation_id=correlation_id,
            causation_id=causation_id,
            **kwargs,
        )
        self.symbol = symbol
