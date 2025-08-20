"""
Centralized error handling and logging utilities.

Provides decorators and context managers for consistent error handling
across all services with custom exception hierarchy.
"""

import functools
import logging
import traceback
from collections.abc import Callable
from typing import Any, TypeVar

from the_alchemiser.services.errors.exceptions import (
    ConfigurationError,
    DataProviderError,
    MarketDataError,
    StreamingError,
    TradingClientError,
)

F = TypeVar("F", bound=Callable[..., Any])


class ErrorHandler:
    """Centralized error handler with logging and exception management."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """
        Initialize error handler.

        Args:
            logger: Logger instance to use, defaults to module logger
        """
        self.logger = logger or logging.getLogger(__name__)

    def log_and_raise(
        self,
        error_type: type[Exception],
        message: str,
        context: dict[str, Any] | None = None,
        original_error: Exception | None = None,
    ) -> None:
        """
        Log error with context and raise custom exception.

        Args:
            error_type: Type of exception to raise
            message: Error message
            context: Additional context for logging
            original_error: Original exception if this is a re-raise
        """
        context = context or {}

        # Log with context
        log_message = f"{message}"
        if context:
            context_str = ", ".join(f"{k}={v}" for k, v in context.items())
            log_message += f" [Context: {context_str}]"

        if original_error:
            log_message += f" [Original: {original_error}]"

        self.logger.error(log_message)

        # Log stack trace for debugging
        if original_error:
            self.logger.debug(f"Original traceback: {traceback.format_exc()}")

        # Raise the custom exception
        if original_error:
            raise error_type(message) from original_error
        else:
            raise error_type(message)

    def log_and_handle(
        self,
        error: Exception,
        context: dict[str, Any] | None = None,
        default_return: Any = None,
    ) -> Any:
        """
        Log error and return default value instead of raising.

        Args:
            error: Exception that occurred
            context: Additional context for logging
            default_return: Value to return instead of raising

        Returns:
            Default return value
        """
        context = context or {}

        # Log with context
        log_message = f"Handled error: {error}"
        if context:
            context_str = ", ".join(f"{k}={v}" for k, v in context.items())
            log_message += f" [Context: {context_str}]"

        self.logger.error(log_message)
        self.logger.debug(f"Traceback: {traceback.format_exc()}")

        return default_return


def handle_service_errors(
    error_types: dict[type[Exception], type[Exception]] | None = None,
    default_return: Any = None,
    log_context: dict[str, Any] | None = None,
) -> Callable[[F], F]:
    """
    Decorator to handle and convert service errors.

    Args:
        error_types: Mapping of original exceptions to custom exceptions
        default_return: Default return value on error
        log_context: Additional logging context

    Returns:
        Decorated function
    """
    if error_types is None:
        error_types = {
            ConnectionError: DataProviderError,
            TimeoutError: DataProviderError,
            ValueError: DataProviderError,
            KeyError: DataProviderError,
        }

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            error_handler = ErrorHandler()
            context = (log_context or {}).copy()
            context.update(
                {
                    "function": func.__name__,
                    "module": func.__module__,
                }
            )

            try:
                return func(*args, **kwargs)
            except tuple(error_types.keys()) as e:
                # Convert to custom exception type
                custom_error_type = error_types.get(type(e), DataProviderError)
                if default_return is not None:
                    return error_handler.log_and_handle(e, context, default_return)
                else:
                    error_handler.log_and_raise(
                        custom_error_type,
                        f"Service error in {func.__name__}: {e}",
                        context,
                        e,
                    )
            except Exception as e:
                # Handle unexpected errors
                if default_return is not None:
                    return error_handler.log_and_handle(e, context, default_return)
                else:
                    error_handler.log_and_raise(
                        DataProviderError,
                        f"Unexpected error in {func.__name__}: {e}",
                        context,
                        e,
                    )

        return wrapper  # type: ignore[return-value]

    return decorator


def handle_market_data_errors(default_return: Any = None) -> Callable[[F], F]:
    """Decorator specifically for market data service errors."""
    return handle_service_errors(
        error_types={
            ConnectionError: MarketDataError,
            TimeoutError: MarketDataError,
            ValueError: MarketDataError,
            KeyError: MarketDataError,
        },
        default_return=default_return,
        log_context={"service": "market_data"},
    )


def handle_trading_errors(default_return: Any = None) -> Callable[[F], F]:
    """Decorator specifically for trading service errors."""
    return handle_service_errors(
        error_types={
            ConnectionError: TradingClientError,
            TimeoutError: TradingClientError,
            ValueError: TradingClientError,
            KeyError: TradingClientError,
        },
        default_return=default_return,
        log_context={"service": "trading"},
    )


def handle_streaming_errors(default_return: Any = None) -> Callable[[F], F]:
    """Decorator specifically for streaming service errors."""
    return handle_service_errors(
        error_types={
            ConnectionError: StreamingError,
            TimeoutError: StreamingError,
            ValueError: StreamingError,
        },
        default_return=default_return,
        log_context={"service": "streaming"},
    )


def handle_config_errors(default_return: Any = None) -> Callable[[F], F]:
    """Decorator specifically for configuration errors."""
    return handle_service_errors(
        error_types={
            FileNotFoundError: ConfigurationError,
            ValueError: ConfigurationError,
            KeyError: ConfigurationError,
        },
        default_return=default_return,
        log_context={"service": "config"},
    )


class ErrorContext:
    """Context manager for error handling with automatic logging."""

    def __init__(
        self,
        error_handler: ErrorHandler,
        context: dict[str, Any] | None = None,
        reraise: bool = True,
    ) -> None:
        """
        Initialize error context.

        Args:
            error_handler: Error handler instance
            context: Logging context
            reraise: Whether to reraise exceptions
        """
        self.error_handler = error_handler
        self.context = context or {}
        self.reraise = reraise

    def __enter__(self) -> "ErrorContext":
        """Enter context manager."""
        return self

    def __exit__(
        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: Any
    ) -> bool:
        """Exit context manager and handle any exceptions."""
        if exc_type is not None and exc_val is not None:
            if self.reraise:
                # Log and reraise
                if isinstance(exc_val, Exception):
                    self.error_handler.log_and_handle(exc_val, self.context)
                return False  # Let exception propagate
            else:
                # Log and suppress
                if isinstance(exc_val, Exception):
                    self.error_handler.log_and_handle(exc_val, self.context)
                return True  # Suppress exception

        return False  # No exception occurred


def create_service_logger(service_name: str, level: int = logging.INFO) -> logging.Logger:
    """
    [DEPRECATED] Create a standardized logger for a service.
    
    This function is deprecated. Use get_service_logger from 
    the_alchemiser.infrastructure.logging.logging_utils instead,
    which uses centralized logging configuration.

    Args:
        service_name: Name of the service
        level: Logging level (ignored - use central config)

    Returns:
        Configured logger using central configuration
    """
    # Import here to avoid circular imports
    from the_alchemiser.infrastructure.logging.logging_utils import get_service_logger

    return get_service_logger(service_name)


class ServiceMetrics:
    """Simple metrics collection for service monitoring."""

    def __init__(self) -> None:
        """Initialize metrics collection."""
        self._error_counts: dict[str, int] = {}
        self._call_counts: dict[str, int] = {}

    def record_call(self, service_method: str) -> None:
        """Record a service method call."""
        self._call_counts[service_method] = self._call_counts.get(service_method, 0) + 1

    def record_error(self, service_method: str, error_type: str) -> None:
        """Record a service method error."""
        key = f"{service_method}:{error_type}"
        self._error_counts[key] = self._error_counts.get(key, 0) + 1

    def get_metrics(self) -> dict[str, Any]:
        """Get collected metrics."""
        return {
            "error_counts": self._error_counts.copy(),
            "call_counts": self._call_counts.copy(),
        }

    def reset_metrics(self) -> None:
        """Reset all metrics."""
        self._error_counts.clear()
        self._call_counts.clear()


# Global metrics instance
service_metrics = ServiceMetrics()


def with_metrics(service_name: str) -> Callable[[F], F]:
    """Decorator to add metrics collection to service methods."""

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            method_name = f"{service_name}.{func.__name__}"
            service_metrics.record_call(method_name)

            try:
                return func(*args, **kwargs)
            except Exception as e:
                service_metrics.record_error(method_name, type(e).__name__)
                raise

        return wrapper  # type: ignore[return-value]

    return decorator
