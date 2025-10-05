#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

Strategy_v2 error types and exceptions.

Provides typed exceptions for strategy execution with module context
for traceability and error handling. These errors extend the shared
AlchemiserError base class for consistency across the system.

All errors include:
- module: Module path for error origin tracking
- correlation_id: Optional correlation ID for workflow tracking
- context: Additional contextual information for debugging
- to_dict(): Structured data export for logging/reporting
"""

from __future__ import annotations

from typing import Any

from the_alchemiser.shared.types.exceptions import AlchemiserError


class StrategyV2Error(AlchemiserError):
    """Base exception for strategy_v2 module.
    
    Extends AlchemiserError with strategy-specific context tracking.
    All strategy_v2 exceptions should inherit from this class.
    
    Examples:
        >>> error = StrategyV2Error(
        ...     "Strategy failed",
        ...     module="strategy_v2.core",
        ...     correlation_id="abc-123"
        ... )
        >>> error.module
        'strategy_v2.core'
        >>> error.correlation_id
        'abc-123'

    """

    def __init__(
        self,
        message: str,
        module: str = "strategy_v2",
        correlation_id: str | None = None,
        **kwargs: str | float | int | bool | None,
    ) -> None:
        """Initialize strategy error.

        Args:
            message: Error message describing what went wrong
            module: Module path where error occurred (e.g., "strategy_v2.core.orchestrator")
            correlation_id: Optional correlation ID for tracking across workflow
            **kwargs: Additional error context (symbol, strategy_id, etc.)

        Raises:
            None: This is an exception class; it gets raised, not called

        """
        # Build context including strategy-specific fields
        context: dict[str, Any] = dict(kwargs)
        context["module"] = module
        if correlation_id:
            context["correlation_id"] = correlation_id
        
        super().__init__(message, context)
        self.module = module
        self.correlation_id = correlation_id


class StrategyExecutionError(StrategyV2Error):
    """Error during strategy execution.
    
    Raised when a strategy engine fails during execution, including issues with:
    - Strategy computation or calculation errors
    - Invalid strategy outputs
    - Engine-specific failures
    
    Examples:
        >>> error = StrategyExecutionError(
        ...     "Nuclear strategy failed: division by zero",
        ...     strategy_id="nuclear",
        ...     symbol="SPY",
        ...     correlation_id="xyz-789"
        ... )
        >>> error.strategy_id
        'nuclear'

    """

    def __init__(
        self,
        message: str,
        strategy_id: str | None = None,
        correlation_id: str | None = None,
        **kwargs: str | float | int | bool | None,
    ) -> None:
        """Initialize strategy execution error.

        Args:
            message: Error message describing the execution failure
            strategy_id: Strategy identifier that failed (e.g., "nuclear", "tecl")
            correlation_id: Optional correlation ID for tracking
            **kwargs: Additional context (symbol, timeframe, etc.)

        Raises:
            None: This is an exception class; it gets raised, not called

        """
        super().__init__(message, "strategy_v2.core.orchestrator", correlation_id, **kwargs)
        self.strategy_id = strategy_id


class StrategyConfigurationError(StrategyV2Error):
    """Error in strategy configuration or context.
    
    Raised when strategy setup or configuration is invalid, including:
    - Missing required configuration parameters
    - Invalid strategy context (missing symbols, timeframe)
    - Configuration validation failures
    
    Note: Renamed from ConfigurationError to avoid conflict with
    shared.types.exceptions.ConfigurationError (general config errors).
    
    Examples:
        >>> error = StrategyConfigurationError(
        ...     "Strategy context missing symbols",
        ...     strategy_id="nuclear",
        ...     config_key="symbols"
        ... )
        >>> error.context["config_key"]
        'symbols'

    """

    def __init__(
        self, 
        message: str,
        correlation_id: str | None = None,
        **kwargs: str | float | int | bool | None
    ) -> None:
        """Initialize configuration error.

        Args:
            message: Error message describing the configuration issue
            correlation_id: Optional correlation ID for tracking
            **kwargs: Additional context (config_key, strategy_id, etc.)

        Raises:
            None: This is an exception class; it gets raised, not called

        """
        super().__init__(message, "strategy_v2.models.context", correlation_id, **kwargs)


class StrategyMarketDataError(StrategyV2Error):
    """Error accessing or processing market data for strategy execution.
    
    Raised when market data operations fail during strategy execution:
    - Failed data fetches from Alpaca or other data sources
    - Invalid or missing data for required symbols
    - Data processing errors (bad timestamps, missing values)
    
    Note: Renamed from MarketDataError to avoid conflict with
    shared.types.exceptions.MarketDataError (general data errors).
    
    Examples:
        >>> error = StrategyMarketDataError(
        ...     "Failed to fetch historical bars for SPY",
        ...     symbol="SPY",
        ...     timeframe="1D",
        ...     correlation_id="xyz-789"
        ... )
        >>> error.symbol
        'SPY'

    """

    def __init__(
        self,
        message: str,
        symbol: str | None = None,
        correlation_id: str | None = None,
        **kwargs: str | float | int | bool | None,
    ) -> None:
        """Initialize market data error.

        Args:
            message: Error message describing the data access failure
            symbol: Symbol that caused the error (e.g., "SPY", "QQQ")
            correlation_id: Optional correlation ID for tracking
            **kwargs: Additional context (timeframe, lookback_days, etc.)

        Raises:
            None: This is an exception class; it gets raised, not called

        """
        super().__init__(
            message, 
            "strategy_v2.adapters.market_data_adapter", 
            correlation_id, 
            **kwargs
        )
        self.symbol = symbol
