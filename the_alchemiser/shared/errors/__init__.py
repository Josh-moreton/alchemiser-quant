"""Business Unit: shared | Status: current.

Error handling and exception types for The Alchemiser.

This package provides error handling utilities, custom exceptions, and error
context management for The Alchemiser Trading System. It includes the main
error handler facade, error categorization, and detailed error reporting.
"""

from __future__ import annotations

# Re-export public API from decomposed modules
from .error_details import ErrorDetails
from .error_handler import (
    TradingSystemErrorHandler,
    get_error_handler,
    handle_errors_with_retry,
    handle_trading_error,
    send_error_notification_if_needed,
)
from .error_reporter import (
    EnhancedErrorReporter,
    get_enhanced_error_reporter,
    get_global_error_reporter,
)
from .error_types import (
    ErrorCategory,
    ErrorNotificationData,
    ErrorSeverity,
)
from .error_utils import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    categorize_error_severity,
    retry_with_backoff,
)
from .exceptions import (
    AlchemiserError,
    BuyingPowerError,
    ConfigurationError,
    DataProviderError,
    EventBusError,
    ExecutionManagerError,
    HandlerInvocationError,
    MarketDataError,
    MarketDataServiceError,
    OrderExecutionError,
    PriceValidationError,
    ReportGenerationError,
    SchemaValidationError,
    SettlementError,
    StrategyExecutionError,
    SymbolValidationError,
    TimeframeValidationError,
    TradingClientError,
    TradingServiceError,
    TypeConversionError,
    ValidationError,
    WebSocketConnectionError,
)

__all__ = [
    "AlchemiserError",
    "BuyingPowerError",
    "CircuitBreaker",
    "CircuitBreakerOpenError",
    "ConfigurationError",
    "DataProviderError",
    "EnhancedErrorReporter",
    "ErrorCategory",
    "ErrorDetails",
    "ErrorNotificationData",
    "ErrorSeverity",
    "EventBusError",
    "ExecutionManagerError",
    "HandlerInvocationError",
    "MarketDataError",
    "MarketDataServiceError",
    "OrderExecutionError",
    "PriceValidationError",
    "ReportGenerationError",
    "SchemaValidationError",
    "SettlementError",
    "StrategyExecutionError",
    "SymbolValidationError",
    "TimeframeValidationError",
    "TradingClientError",
    "TradingServiceError",
    "TradingSystemErrorHandler",
    "TypeConversionError",
    "ValidationError",
    "WebSocketConnectionError",
    "categorize_error_severity",
    "get_enhanced_error_reporter",
    "get_error_handler",
    "get_global_error_reporter",
    "handle_errors_with_retry",
    "handle_trading_error",
    "retry_with_backoff",
    "send_error_notification_if_needed",
]
