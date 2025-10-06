#!/usr/bin/env python3
"""Business Unit: shared; Status: current.

Custom exception classes for The Alchemiser Quantitative Trading System.

This module defines specific exception types for different failure scenarios
to enable better error handling and debugging throughout the application.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any


class AlchemiserError(Exception):
    """Base exception class for all Alchemiser-specific errors."""

    def __init__(
        self,
        message: str,
        context: dict[str, Any] | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Initialize base error with optional contextual data and correlation ID.

        Args:
            message: Error message
            context: Optional context dictionary with error details
            correlation_id: Optional correlation ID for distributed tracing
        """
        super().__init__(message)
        self.message = message
        self.context = context or {}
        self.correlation_id = correlation_id
        if correlation_id:
            self.context["correlation_id"] = correlation_id
        self.timestamp = datetime.now(UTC)

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to structured data for logging/reporting."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
        }


class ConfigurationError(AlchemiserError):
    """Raised when there are configuration-related issues."""

    def __init__(
        self,
        message: str,
        config_key: str | None = None,
        config_value: str | int | float | bool | None = None,  # noqa: FBT001
        correlation_id: str | None = None,
    ) -> None:
        """Raise when configuration values are missing or invalid."""
        context = {}
        if config_key:
            context["config_key"] = config_key
        if config_value is not None:
            context["config_value"] = str(config_value)  # Convert to string for safety
        super().__init__(message, context, correlation_id=correlation_id)
        self.config_key = config_key
        self.config_value = config_value


class DataProviderError(AlchemiserError):
    """Raised when data provider operations fail."""

    def __init__(
        self, message: str, correlation_id: str | None = None
    ) -> None:
        """Raise when data provider operations fail."""
        super().__init__(message, correlation_id=correlation_id)


class TradingClientError(AlchemiserError):
    """Raised when trading client operations fail."""

    def __init__(
        self, message: str, correlation_id: str | None = None
    ) -> None:
        """Raise when trading client operations fail."""
        super().__init__(message, correlation_id=correlation_id)


class OrderExecutionError(TradingClientError):
    """Raised when order placement or execution fails."""

    def __init__(
        self,
        message: str,
        symbol: str | None = None,
        order_type: str | None = None,
        order_id: str | None = None,
        quantity: Decimal | None = None,
        price: Decimal | None = None,
        account_id: str | None = None,
        retry_count: int = 0,
        correlation_id: str | None = None,
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
            context["quantity"] = str(quantity)
        if price is not None:
            context["price"] = str(price)
        if account_id:
            context["account_id"] = account_id
        if retry_count > 0:
            context["retry_count"] = retry_count

        super().__init__(message, correlation_id=correlation_id)
        # Merge context after super().__init__ to preserve correlation_id
        self.context.update(context)
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
        quantity: Decimal | None = None,
        price: Decimal | None = None,
        reason: str | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Create an order placement error for None order ID scenarios."""
        super().__init__(
            message=message,
            symbol=symbol,
            order_type=order_type,
            quantity=quantity,
            price=price,
            correlation_id=correlation_id,
        )
        self.reason = reason
        if reason:
            self.context["reason"] = reason


class OrderTimeoutError(OrderExecutionError):
    """Raised when order execution times out during limit order sequence."""

    def __init__(
        self,
        message: str,
        symbol: str | None = None,
        order_id: str | None = None,
        timeout_seconds: float | None = None,
        attempt_number: int | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Create an order timeout error for re-pegging scenarios."""
        super().__init__(
            message=message, symbol=symbol, order_id=order_id, correlation_id=correlation_id
        )
        self.timeout_seconds = timeout_seconds
        self.attempt_number = attempt_number
        if timeout_seconds is not None:
            self.context["timeout_seconds"] = timeout_seconds
        if attempt_number is not None:
            self.context["attempt_number"] = attempt_number


class SpreadAnalysisError(DataProviderError):
    """Raised when spread analysis fails and cannot determine appropriate pricing."""

    def __init__(
        self,
        message: str,
        symbol: str | None = None,
        bid: Decimal | None = None,
        ask: Decimal | None = None,
        spread_cents: Decimal | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Create a spread analysis error for pricing failures."""
        context: dict[str, Any] = {}
        if symbol:
            context["symbol"] = symbol
        if bid is not None:
            context["bid"] = str(bid)
        if ask is not None:
            context["ask"] = str(ask)
        if spread_cents is not None:
            context["spread_cents"] = str(spread_cents)

        super().__init__(message, correlation_id=correlation_id)
        self.context.update(context)
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
        required_amount: Decimal | None = None,
        available_amount: Decimal | None = None,
        shortfall: Decimal | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Create a buying power error with financial context."""
        super().__init__(message=message, symbol=symbol, correlation_id=correlation_id)
        self.required_amount = required_amount
        self.available_amount = available_amount
        self.shortfall = shortfall
        if required_amount is not None:
            self.context["required_amount"] = str(required_amount)
        if available_amount is not None:
            self.context["available_amount"] = str(available_amount)
        if shortfall is not None:
            self.context["shortfall"] = str(shortfall)


class InsufficientFundsError(OrderExecutionError):
    """Raised when there are insufficient funds for an order."""

    def __init__(
        self, message: str, correlation_id: str | None = None
    ) -> None:
        """Raise when there are insufficient funds for an order."""
        super().__init__(message, correlation_id=correlation_id)


class PositionValidationError(TradingClientError):
    """Raised when position validation fails."""

    def __init__(
        self,
        message: str,
        symbol: str | None = None,
        requested_qty: Decimal | None = None,
        available_qty: Decimal | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Initialize position validation error."""
        context: dict[str, Any] = {}
        if symbol:
            context["symbol"] = symbol
        if requested_qty is not None:
            context["requested_qty"] = str(requested_qty)
        if available_qty is not None:
            context["available_qty"] = str(available_qty)

        super().__init__(message, correlation_id=correlation_id)
        self.context.update(context)
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


class NegativeCashBalanceError(PortfolioError):
    """Raised when account has negative or zero cash balance."""

    def __init__(
        self,
        message: str,
        cash_balance: Decimal | None = None,
        module: str | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Initialize negative cash balance error with context."""
        super().__init__(
            message, module=module, operation="cash_balance_check", correlation_id=correlation_id
        )
        self.cash_balance = cash_balance
        if cash_balance is not None:
            self.context["cash_balance"] = str(cash_balance)


class IndicatorCalculationError(AlchemiserError):
    """Raised when technical indicator calculations fail."""

    def __init__(
        self,
        message: str,
        indicator_name: str | None = None,
        symbol: str | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Raise when an indicator cannot be computed."""
        context: dict[str, Any] = {}
        if indicator_name:
            context["indicator_name"] = indicator_name
        if symbol:
            context["symbol"] = symbol

        super().__init__(message, context, correlation_id=correlation_id)
        self.indicator_name = indicator_name
        self.symbol = symbol


class MarketDataError(DataProviderError):
    """Raised when market data retrieval fails."""

    def __init__(
        self,
        message: str,
        symbol: str | None = None,
        data_type: str | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Raise when market data retrieval fails."""
        context: dict[str, Any] = {}
        if symbol:
            context["symbol"] = symbol
        if data_type:
            context["data_type"] = data_type

        super().__init__(message, correlation_id=correlation_id)
        self.context.update(context)
        self.symbol = symbol
        self.data_type = data_type


class ValidationError(AlchemiserError):
    """Raised when data validation fails."""

    def __init__(
        self,
        message: str,
        field_name: str | None = None,
        value: str | int | float | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Create a validation error for invalid user data."""
        context: dict[str, Any] = {}
        if field_name:
            context["field_name"] = field_name
        if value is not None:
            context["value"] = str(value)

        super().__init__(message, context, correlation_id=correlation_id)
        self.field_name = field_name
        self.value = value


class NotificationError(AlchemiserError):
    """Raised when notification sending fails."""

    def __init__(
        self, message: str, correlation_id: str | None = None
    ) -> None:
        """Raise when notification sending fails."""
        super().__init__(message, correlation_id=correlation_id)


class S3OperationError(AlchemiserError):
    """Raised when S3 operations fail."""

    def __init__(
        self,
        message: str,
        bucket: str | None = None,
        key: str | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Raise when interacting with Amazon S3 fails."""
        context: dict[str, Any] = {}
        if bucket:
            context["bucket"] = bucket
        if key:
            context["key"] = key

        super().__init__(message, context, correlation_id=correlation_id)
        self.bucket = bucket
        self.key = key


class RateLimitError(AlchemiserError):
    """Raised when API rate limits are exceeded."""

    def __init__(
        self,
        message: str,
        retry_after: int | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Raise when API rate limit is exceeded."""
        context: dict[str, Any] = {}
        if retry_after is not None:
            context["retry_after"] = retry_after

        super().__init__(message, context, correlation_id=correlation_id)
        self.retry_after = retry_after


class MarketClosedError(TradingClientError):
    """Raised when attempting to trade while markets are closed."""

    def __init__(
        self, message: str, correlation_id: str | None = None
    ) -> None:
        """Raise when attempting to trade while markets are closed."""
        super().__init__(message, correlation_id=correlation_id)


class WebSocketError(DataProviderError):
    """Raised when WebSocket connection issues occur."""

    def __init__(
        self, message: str, correlation_id: str | None = None
    ) -> None:
        """Raise when WebSocket connection issues occur."""
        super().__init__(message, correlation_id=correlation_id)


class StreamingError(DataProviderError):
    """Raised when streaming data issues occur."""

    def __init__(
        self, message: str, correlation_id: str | None = None
    ) -> None:
        """Raise when streaming data issues occur."""
        super().__init__(message, correlation_id=correlation_id)


class LoggingError(AlchemiserError):
    """Raised when logging operations fail."""

    def __init__(
        self,
        message: str,
        logger_name: str | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Raise when logging infrastructure fails."""
        context: dict[str, Any] = {}
        if logger_name:
            context["logger_name"] = logger_name

        super().__init__(message, context, correlation_id=correlation_id)
        self.logger_name = logger_name


class FileOperationError(AlchemiserError):
    """Raised when file operations fail."""

    def __init__(
        self,
        message: str,
        file_path: str | None = None,
        operation: str | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Raise when a filesystem operation fails."""
        context: dict[str, Any] = {}
        if file_path:
            context["file_path"] = file_path
        if operation:
            context["operation"] = operation

        super().__init__(message, context, correlation_id=correlation_id)
        self.file_path = file_path
        self.operation = operation


class DatabaseError(AlchemiserError):
    """Raised when database operations fail."""

    def __init__(
        self,
        message: str,
        table_name: str | None = None,
        operation: str | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Raise when a database operation fails."""
        context: dict[str, Any] = {}
        if table_name:
            context["table_name"] = table_name
        if operation:
            context["operation"] = operation

        super().__init__(message, context, correlation_id=correlation_id)
        self.table_name = table_name
        self.operation = operation


class SecurityError(AlchemiserError):
    """Raised when security-related issues occur."""

    def __init__(
        self, message: str, correlation_id: str | None = None
    ) -> None:
        """Raise when security-related issues occur."""
        super().__init__(message, correlation_id=correlation_id)


class EnvironmentError(ConfigurationError):
    """Raised when environment setup issues occur."""

    def __init__(
        self,
        message: str,
        env_var: str | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Raise when an environment variable configuration is invalid."""
        super().__init__(message, config_key=env_var, correlation_id=correlation_id)
        self.env_var = env_var


class StrategyExecutionError(AlchemiserError):
    """Raised when strategy execution fails."""

    def __init__(
        self,
        message: str,
        strategy_name: str | None = None,
        symbol: str | None = None,
        operation: str | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Raise when strategy execution encounters an error."""
        context: dict[str, Any] = {}
        if strategy_name:
            context["strategy_name"] = strategy_name
        if symbol:
            context["symbol"] = symbol
        if operation:
            context["operation"] = operation

        super().__init__(message, context, correlation_id=correlation_id)
        self.strategy_name = strategy_name
        self.symbol = symbol
        self.operation = operation


class StrategyValidationError(StrategyExecutionError):
    """Raised when strategy validation fails."""

    def __init__(
        self, message: str, correlation_id: str | None = None
    ) -> None:
        """Raise when strategy validation fails."""
        super().__init__(message, correlation_id=correlation_id)
