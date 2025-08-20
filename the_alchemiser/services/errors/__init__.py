"""
Error handling package for The Alchemiser Trading System.

This package provides consolidated error handling with:
- TradingSystemErrorHandler as the single facade
- ErrorContextData for standardized error context
- ErrorScope context manager (renamed from ErrorContext to avoid collision)
- Exception translation decorators

Re-exports all components for backward compatibility.
"""

# New consolidated API
from .context import ErrorContextData, create_error_context
from .decorators import (
    translate_config_errors,
    translate_market_data_errors,
    translate_service_errors,
    translate_streaming_errors,
    translate_trading_errors,
)
from .handler import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    EnhancedAlchemiserError,
    EnhancedDataError,
    EnhancedTradingError,
    ErrorCategory,
    ErrorDetails,
    ErrorSeverity,
    TradingSystemErrorHandler,
    categorize_error_severity,
    create_enhanced_error,
    get_error_handler,
    handle_trading_error,
    retry_with_backoff,
    send_error_notification_if_needed,
)
from .scope import ErrorScope, create_error_scope

# Backward compatibility imports from old modules
from .error_handling import (
    ErrorHandler,
    ServiceMetrics,
    create_service_logger,
    handle_config_errors,
    handle_market_data_errors,
    handle_service_errors,
    handle_streaming_errors,
    handle_trading_errors,
    service_metrics,
    with_metrics,
)

# Legacy ErrorContext - kept temporarily for backward compatibility
# The old ErrorContext from error_handling.py is now available as ErrorScope
# The old ErrorContext from error_handler.py is now ErrorContextData

# TODO: Add deprecation warnings for old ErrorContext usage
# import warnings

# Legacy compatibility aliases - these should be deprecated in future versions
ErrorContext = ErrorScope  # Context manager from error_handling.py
# For the data context from error_handler.py, use ErrorContextData instead

__all__ = [
    # New consolidated API
    "ErrorContextData",
    "create_error_context",
    "ErrorScope", 
    "create_error_scope",
    "TradingSystemErrorHandler",
    "ErrorCategory",
    "ErrorSeverity",
    "ErrorDetails",
    "EnhancedAlchemiserError",
    "EnhancedTradingError",
    "EnhancedDataError",
    "get_error_handler",
    "handle_trading_error",
    "send_error_notification_if_needed",
    "categorize_error_severity",
    "create_enhanced_error",
    "retry_with_backoff",
    "CircuitBreaker",
    "CircuitBreakerOpenError",
    # Translation decorators
    "translate_service_errors",
    "translate_market_data_errors", 
    "translate_trading_errors",
    "translate_streaming_errors",
    "translate_config_errors",
    # Legacy compatibility from error_handling.py
    "ErrorHandler",
    "handle_service_errors",
    "handle_market_data_errors",
    "handle_trading_errors",
    "handle_streaming_errors",
    "handle_config_errors",
    "create_service_logger",
    "ServiceMetrics",
    "service_metrics",
    "with_metrics",
    # Legacy aliases (deprecated)
    "ErrorContext",  # Use ErrorScope instead
]
