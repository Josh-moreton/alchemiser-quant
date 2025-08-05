#!/usr/bin/env python3
"""
Custom exception classes for The Alchemiser Quantitative Trading System.

This module defines specific exception types for different failure scenarios
to enable better error handling and debugging throughout the application.
"""

from typing import Any


class AlchemiserError(Exception):
    """Base exception class for all Alchemiser-specific errors."""

    pass


class ConfigurationError(AlchemiserError):
    """Raised when there are configuration-related issues."""

    pass


class DataProviderError(AlchemiserError):
    """Raised when data provider operations fail."""

    pass


class TradingClientError(AlchemiserError):
    """Raised when trading client operations fail."""

    pass


class OrderExecutionError(TradingClientError):
    """Raised when order placement or execution fails."""

    def __init__(
        self, message: str, symbol: str | None = None, order_type: str | None = None
    ) -> None:
        super().__init__(message)
        self.symbol = symbol
        self.order_type = order_type


class InsufficientFundsError(OrderExecutionError):
    """Raised when there are insufficient funds for an order."""

    pass


class PositionValidationError(TradingClientError):
    """Raised when position validation fails."""

    def __init__(
        self,
        message: str,
        symbol: str | None = None,
        requested_qty: float | None = None,
        available_qty: float | None = None,
    ):
        super().__init__(message)
        self.symbol = symbol
        self.requested_qty = requested_qty
        self.available_qty = available_qty


class StrategyExecutionError(AlchemiserError):
    """Raised when strategy execution fails."""

    def __init__(self, message: str, strategy_name: str | None = None) -> None:
        super().__init__(message)
        self.strategy_name = strategy_name


class IndicatorCalculationError(AlchemiserError):
    """Raised when technical indicator calculations fail."""

    def __init__(
        self, message: str, indicator_name: str | None = None, symbol: str | None = None
    ) -> None:
        super().__init__(message)
        self.indicator_name = indicator_name
        self.symbol = symbol


class MarketDataError(DataProviderError):
    """Raised when market data retrieval fails."""

    def __init__(
        self, message: str, symbol: str | None = None, data_type: str | None = None
    ) -> None:
        super().__init__(message)
        self.symbol = symbol
        self.data_type = data_type


class ValidationError(AlchemiserError):
    """Raised when data validation fails."""

    def __init__(
        self, message: str, field_name: str | None = None, value: Any | None = None
    ) -> None:
        super().__init__(message)
        self.field_name = field_name
        self.value = value


class NotificationError(AlchemiserError):
    """Raised when notification sending fails."""

    pass


class S3OperationError(AlchemiserError):
    """Raised when S3 operations fail."""

    def __init__(self, message: str, bucket: str | None = None, key: str | None = None) -> None:
        super().__init__(message)
        self.bucket = bucket
        self.key = key


class RateLimitError(AlchemiserError):
    """Raised when API rate limits are exceeded."""

    def __init__(self, message: str, retry_after: int | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class MarketClosedError(TradingClientError):
    """Raised when attempting to trade while markets are closed."""

    pass


class WebSocketError(DataProviderError):
    """Raised when WebSocket connection issues occur."""

    pass


class LoggingError(AlchemiserError):
    """Raised when logging operations fail."""

    def __init__(self, message: str, logger_name: str | None = None) -> None:
        super().__init__(message)
        self.logger_name = logger_name


class FileOperationError(AlchemiserError):
    """Raised when file operations fail."""

    def __init__(
        self, message: str, file_path: str | None = None, operation: str | None = None
    ) -> None:
        super().__init__(message)
        self.file_path = file_path
        self.operation = operation


class DatabaseError(AlchemiserError):
    """Raised when database operations fail."""

    def __init__(
        self, message: str, table_name: str | None = None, operation: str | None = None
    ) -> None:
        super().__init__(message)
        self.table_name = table_name
        self.operation = operation


class SecurityError(AlchemiserError):
    """Raised when security-related issues occur."""

    pass


class EnvironmentError(ConfigurationError):
    """Raised when environment setup issues occur."""

    def __init__(self, message: str, env_var: str | None = None) -> None:
        super().__init__(message)
        self.env_var = env_var
