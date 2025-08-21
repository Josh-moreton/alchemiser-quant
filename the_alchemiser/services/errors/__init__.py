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

# Backward compatibility imports from old modules
# NOTE: Most items from error_handling are now deprecated
from .error_handling import create_service_logger  # Keep for backward compatibility
from .handler import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    EnhancedAlchemiserError,
    EnhancedDataError,
    EnhancedErrorReporter,
    EnhancedTradingError,
    ErrorCategory,
    ErrorDetails,
    ErrorSeverity,
    TradingSystemErrorHandler,
    categorize_error_severity,
    create_enhanced_error,
    get_enhanced_error_reporter,
    get_error_handler,
    get_global_error_reporter,
    handle_errors_with_retry,
    handle_trading_error,
    retry_with_backoff,
    send_error_notification_if_needed,
)
from .scope import ErrorScope, create_error_scope

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
    "EnhancedErrorReporter",
    "get_error_handler",
    "get_enhanced_error_reporter",
    "get_global_error_reporter",
    "handle_trading_error",
    "handle_errors_with_retry",
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
    # Legacy compatibility - minimal set
    "create_service_logger",  # Keep for backward compatibility
    # Legacy aliases (deprecated)
    "ErrorContext",  # Use ErrorScope instead
]
