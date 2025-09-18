#!/usr/bin/env python3
"""Business Unit: utilities; Status: current.

Custom exception classes for The Alchemiser Quantitative Trading System.

This module defines specific exception types for different failure scenarios
to enable better error handling and debugging throughout the application.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from the_alchemiser.shared.dto import ErrorDTO


class AlchemiserError(Exception):
    """Base exception class for all Alchemiser-specific errors."""

    def __init__(self, message: str, context: dict[str, Any] | None = None) -> None:
        """Initialize base error with optional contextual data."""
        super().__init__(message)
        self.message = message
        self.context = context or {}
        self.timestamp = datetime.now(UTC)

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to structured data for logging/reporting."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
        }

    def to_error_dto(self, category: str | None = None, component: str | None = None) -> ErrorDTO:
        """Convert exception to ErrorDTO for structured error handling.
        
        Args:
            category: Optional error category for grouping
            component: Optional component name where error occurred
            
        Returns:
            ErrorDTO instance representing this error
        """
        from the_alchemiser.shared.dto import ErrorDTO
        
        return ErrorDTO(
            error_type=self.__class__.__name__,
            message=self.message,
            category=category,
            component=component,
            context=self.context,
            timestamp=self.timestamp.isoformat(),
            suggested_action=getattr(self, "suggested_action", None)
        )


class ConfigurationError(AlchemiserError):
    """Raised when there are configuration-related issues."""

    def __init__(
        self,
        message: str,
        config_key: str | None = None,
        config_value: str | int | float | bool | None = None,  # noqa: FBT001
    ) -> None:
        """Raise when configuration values are missing or invalid."""
        context = {}
        if config_key:
            context["config_key"] = config_key
        if config_value is not None:
            context["config_value"] = str(config_value)  # Convert to string for safety
        super().__init__(message, context)
        self.config_key = config_key
        self.config_value = config_value


class DataProviderError(AlchemiserError):
    """Raised when data provider operations fail."""


class TradingClientError(AlchemiserError):
    """Raised when trading client operations fail."""


class OrderExecutionError(TradingClientError):
    """Raised when order placement or execution fails."""

    def __init__(
        self,
        message: str,
        symbol: str | None = None,
        order_type: str | None = None,
        order_id: str | None = None,
        quantity: float | None = None,
        price: float | None = None,
        account_id: str | None = None,
        retry_count: int = 0,
    ) -> None:
        """Create an order execution error with contextual details."""
        context: dict[str, Any] = {}
        if symbol:
            context["symbol"] = symbol
        if order_type:
            context["order_type"] = order_type
        if order_id:
            context["order_id"] = order_id
        if quantity is not None:
            context["quantity"] = quantity
        if price is not None:
            context["price"] = price
        if account_id:
            context["account_id"] = account_id
        if retry_count > 0:
            context["retry_count"] = retry_count

        super().__init__(message, context)
        self.symbol = symbol
        self.order_type = order_type
        self.order_id = order_id
        self.quantity = quantity
        self.price = price
        self.account_id = account_id
        self.retry_count = retry_count


class OrderPlacementError(OrderExecutionError):
    """Raised when order placement fails and returns None ID."""

    def __init__(
        self,
        message: str,
        symbol: str | None = None,
        order_type: str | None = None,
        quantity: float | None = None,
        price: float | None = None,
        reason: str | None = None,
    ) -> None:
        """Create an order placement error for None order ID scenarios."""
        super().__init__(
            message=message,
            symbol=symbol,
            order_type=order_type,
            quantity=quantity,
            price=price,
        )
        self.reason = reason


class OrderTimeoutError(OrderExecutionError):
    """Raised when order execution times out during limit order sequence."""

    def __init__(
        self,
        message: str,
        symbol: str | None = None,
        order_id: str | None = None,
        timeout_seconds: float | None = None,
        attempt_number: int | None = None,
    ) -> None:
        """Create an order timeout error for re-pegging scenarios."""
        super().__init__(message=message, symbol=symbol, order_id=order_id)
        self.timeout_seconds = timeout_seconds
        self.attempt_number = attempt_number


class SpreadAnalysisError(DataProviderError):
    """Raised when spread analysis fails and cannot determine appropriate pricing."""

    def __init__(
        self,
        message: str,
        symbol: str | None = None,
        bid: float | None = None,
        ask: float | None = None,
        spread_cents: float | None = None,
    ) -> None:
        """Create a spread analysis error for pricing failures."""
        super().__init__(message)
        self.symbol = symbol
        self.bid = bid
        self.ask = ask
        self.spread_cents = spread_cents


class BuyingPowerError(OrderExecutionError):
    """Raised when insufficient buying power detected during execution."""

    def __init__(
        self,
        message: str,
        symbol: str | None = None,
        required_amount: float | None = None,
        available_amount: float | None = None,
        shortfall: float | None = None,
    ) -> None:
        """Create a buying power error with financial context."""
        super().__init__(message=message, symbol=symbol)
        self.required_amount = required_amount
        self.available_amount = available_amount
        self.shortfall = shortfall


class InsufficientFundsError(OrderExecutionError):
    """Raised when there are insufficient funds for an order."""


class PositionValidationError(TradingClientError):
    """Raised when position validation fails."""

    def __init__(
        self,
        message: str,
        symbol: str | None = None,
        requested_qty: float | None = None,
        available_qty: float | None = None,
    ) -> None:
        """Initialize position validation error."""
        super().__init__(message)
        self.symbol = symbol
        self.requested_qty = requested_qty
        self.available_qty = available_qty


class PortfolioError(AlchemiserError):
    """Raised when portfolio operations fail."""

    def __init__(
        self,
        message: str,
        module: str | None = None,
        operation: str | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Initialize portfolio error with context."""
        context: dict[str, Any] = {}
        if module:
            context["module"] = module
        if operation:
            context["operation"] = operation
        if correlation_id:
            context["correlation_id"] = correlation_id

        super().__init__(message, context)
        self.module = module
        self.operation = operation
        self.correlation_id = correlation_id


class IndicatorCalculationError(AlchemiserError):
    """Raised when technical indicator calculations fail."""

    def __init__(
        self, message: str, indicator_name: str | None = None, symbol: str | None = None
    ) -> None:
        """Raise when an indicator cannot be computed."""
        super().__init__(message)
        self.indicator_name = indicator_name
        self.symbol = symbol


class MarketDataError(DataProviderError):
    """Raised when market data retrieval fails."""

    def __init__(
        self, message: str, symbol: str | None = None, data_type: str | None = None
    ) -> None:
        """Raise when market data retrieval fails."""
        super().__init__(message)
        self.symbol = symbol
        self.data_type = data_type


class ValidationError(AlchemiserError):
    """Raised when data validation fails."""

    def __init__(
        self,
        message: str,
        field_name: str | None = None,
        value: str | int | float | None = None,
    ) -> None:
        """Create a validation error for invalid user data."""
        super().__init__(message)
        self.field_name = field_name
        self.value = value


class NotificationError(AlchemiserError):
    """Raised when notification sending fails."""


class S3OperationError(AlchemiserError):
    """Raised when S3 operations fail."""

    def __init__(self, message: str, bucket: str | None = None, key: str | None = None) -> None:
        """Raise when interacting with Amazon S3 fails."""
        super().__init__(message)
        self.bucket = bucket
        self.key = key


class RateLimitError(AlchemiserError):
    """Raised when API rate limits are exceeded."""

    def __init__(self, message: str, retry_after: int | None = None) -> None:
        """Raise when API rate limit is exceeded."""
        super().__init__(message)
        self.retry_after = retry_after


class MarketClosedError(TradingClientError):
    """Raised when attempting to trade while markets are closed."""


class WebSocketError(DataProviderError):
    """Raised when WebSocket connection issues occur."""


class StreamingError(DataProviderError):
    """Raised when streaming data issues occur."""


class LoggingError(AlchemiserError):
    """Raised when logging operations fail."""

    def __init__(self, message: str, logger_name: str | None = None) -> None:
        """Raise when logging infrastructure fails."""
        super().__init__(message)
        self.logger_name = logger_name


class FileOperationError(AlchemiserError):
    """Raised when file operations fail."""

    def __init__(
        self, message: str, file_path: str | None = None, operation: str | None = None
    ) -> None:
        """Raise when a filesystem operation fails."""
        super().__init__(message)
        self.file_path = file_path
        self.operation = operation


class DatabaseError(AlchemiserError):
    """Raised when database operations fail."""

    def __init__(
        self, message: str, table_name: str | None = None, operation: str | None = None
    ) -> None:
        """Raise when a database operation fails."""
        super().__init__(message)
        self.table_name = table_name
        self.operation = operation


class SecurityError(AlchemiserError):
    """Raised when security-related issues occur."""


class EnvironmentError(ConfigurationError):
    """Raised when environment setup issues occur."""

    def __init__(self, message: str, env_var: str | None = None) -> None:
        """Raise when an environment variable configuration is invalid."""
        super().__init__(message)
        self.env_var = env_var


class StrategyExecutionError(AlchemiserError):
    """Raised when strategy execution fails."""

    def __init__(
        self,
        message: str,
        strategy_name: str | None = None,
        symbol: str | None = None,
        operation: str | None = None,
    ) -> None:
        """Raise when strategy execution encounters an error."""
        context: dict[str, Any] = {}
        if strategy_name:
            context["strategy_name"] = strategy_name
        if symbol:
            context["symbol"] = symbol
        if operation:
            context["operation"] = operation

        super().__init__(message, context)
        self.strategy_name = strategy_name
        self.symbol = symbol
        self.operation = operation


class StrategyValidationError(StrategyExecutionError):
    """Raised when strategy validation fails."""
