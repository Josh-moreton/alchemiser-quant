#!/usr/bin/env python3
"""
Custom exception classes for The Alchemiser Quantitative Trading System.

This module defines specific exception types for different failure scenarios
to enable better error handling and debugging throughout the application.
"""
from typing import Optional, Any


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
    
    def __init__(self, message: str, symbol: Optional[str] = None, order_type: Optional[str] = None):
        super().__init__(message)
        self.symbol = symbol
        self.order_type = order_type


class InsufficientFundsError(OrderExecutionError):
    """Raised when there are insufficient funds for an order."""
    pass


class PositionValidationError(TradingClientError):
    """Raised when position validation fails."""
    
    def __init__(self, message: str, symbol: Optional[str] = None, requested_qty: Optional[float] = None, available_qty: Optional[float] = None):
        super().__init__(message)
        self.symbol = symbol
        self.requested_qty = requested_qty
        self.available_qty = available_qty


class StrategyExecutionError(AlchemiserError):
    """Raised when strategy execution fails."""
    
    def __init__(self, message: str, strategy_name: Optional[str] = None):
        super().__init__(message)
        self.strategy_name = strategy_name


class IndicatorCalculationError(AlchemiserError):
    """Raised when technical indicator calculations fail."""
    
    def __init__(self, message: str, indicator_name: Optional[str] = None, symbol: Optional[str] = None):
        super().__init__(message)
        self.indicator_name = indicator_name
        self.symbol = symbol


class MarketDataError(DataProviderError):
    """Raised when market data retrieval fails."""
    
    def __init__(self, message: str, symbol: Optional[str] = None, data_type: Optional[str] = None):
        super().__init__(message)
        self.symbol = symbol
        self.data_type = data_type


class BacktestError(AlchemiserError):
    """Raised when backtesting operations fail."""
    pass


class ValidationError(AlchemiserError):
    """Raised when data validation fails."""
    
    def __init__(self, message: str, field_name: Optional[str] = None, value: Optional[Any] = None):
        super().__init__(message)
        self.field_name = field_name
        self.value = value


class NotificationError(AlchemiserError):
    """Raised when notification sending fails."""
    pass


class S3OperationError(AlchemiserError):
    """Raised when S3 operations fail."""
    
    def __init__(self, message: str, bucket: Optional[str] = None, key: Optional[str] = None):
        super().__init__(message)
        self.bucket = bucket
        self.key = key


class RateLimitError(AlchemiserError):
    """Raised when API rate limits are exceeded."""
    
    def __init__(self, message: str, retry_after: Optional[int] = None):
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
    
    def __init__(self, message: str, logger_name: Optional[str] = None):
        super().__init__(message)
        self.logger_name = logger_name


class FileOperationError(AlchemiserError):
    """Raised when file operations fail."""
    
    def __init__(self, message: str, file_path: Optional[str] = None, operation: Optional[str] = None):
        super().__init__(message)
        self.file_path = file_path
        self.operation = operation


class DatabaseError(AlchemiserError):
    """Raised when database operations fail."""
    
    def __init__(self, message: str, table_name: Optional[str] = None, operation: Optional[str] = None):
        super().__init__(message)
        self.table_name = table_name
        self.operation = operation


class SecurityError(AlchemiserError):
    """Raised when security-related issues occur."""
    pass


class EnvironmentError(ConfigurationError):
    """Raised when environment setup issues occur."""
    
    def __init__(self, message: str, env_var: Optional[str] = None):
        super().__init__(message)
        self.env_var = env_var
