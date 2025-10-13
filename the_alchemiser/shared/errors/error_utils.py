#!/usr/bin/env python3
"""Business Unit: shared; Status: current.

Error handling utilities for production resilience.

This module provides retry decorators, circuit breakers, and error
severity categorization utilities.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from functools import wraps
from typing import Any

from the_alchemiser.shared.logging import get_logger

from .error_types import ErrorSeverity

# Import exceptions
try:
    from the_alchemiser.shared.errors.exceptions import (
        AlchemiserError,
        ConfigurationError,
        DataProviderError,
        InsufficientFundsError,
        MarketDataError,
        NotificationError,
        OrderExecutionError,
        PositionValidationError,
    )
except ImportError:
    # Minimal fallback stubs (to avoid circular imports)
    class AlchemiserError(Exception):  # type: ignore[no-redef]
        """Fallback AlchemiserError."""

    class ConfigurationError(AlchemiserError):  # type: ignore[no-redef]
        """Fallback ConfigurationError."""

    class DataProviderError(AlchemiserError):  # type: ignore[no-redef]
        """Fallback DataProviderError."""

    class InsufficientFundsError(AlchemiserError):  # type: ignore[no-redef]
        """Fallback InsufficientFundsError."""

    class MarketDataError(AlchemiserError):  # type: ignore[no-redef]
        """Fallback MarketDataError."""

    class NotificationError(AlchemiserError):  # type: ignore[no-redef]
        """Fallback NotificationError."""

    class OrderExecutionError(AlchemiserError):  # type: ignore[no-redef]
        """Fallback OrderExecutionError."""

    class PositionValidationError(AlchemiserError):  # type: ignore[no-redef]
        """Fallback PositionValidationError."""


logger = get_logger(__name__)


def _is_strategy_execution_error(err: Exception) -> bool:
    """Detect strategy execution errors without cross-module imports.

    Uses string-based class name comparison to avoid circular import issues
    when importing from strategy_v2.errors.

    Args:
        err: Exception to check

    Returns:
        bool: True if exception is a StrategyExecutionError

    """
    return err.__class__.__name__ == "StrategyExecutionError"


def _calculate_jitter_factor(attempt: int) -> float:
    """Calculate jitter factor for retry delay.

    Note: Uses time.time() for non-deterministic jitter in production.
    This is intentional to prevent thundering herd problems in distributed systems.
    Tests should freeze time with freezegun for reproducibility.

    Args:
        attempt: Current retry attempt number

    Returns:
        float: Jitter multiplier between 0.5 and 1.0

    """
    return 0.5 + (hash(str(attempt) + str(int(time.time() * 1000))) % 500) / 1000


def _calculate_retry_delay(
    attempt: int,
    base_delay: float,
    backoff_factor: float,
    max_delay: float,
    *,
    jitter: bool,
) -> float:
    """Calculate retry delay with exponential backoff and optional jitter.

    Args:
        attempt: Current retry attempt number (0-indexed)
        base_delay: Base delay in seconds before first retry
        backoff_factor: Multiplier for exponential backoff (typically 2.0)
        max_delay: Maximum delay cap in seconds
        jitter: Whether to apply random jitter to prevent thundering herd

    Returns:
        float: Calculated delay in seconds to wait before next retry

    """
    delay = min(base_delay * (backoff_factor**attempt), max_delay)
    if jitter:
        delay *= _calculate_jitter_factor(attempt)
    return delay


def _handle_final_retry_attempt(exception: Exception, max_retries: int, func_name: str) -> None:
    """Handle the final retry attempt by adding context and logging.

    Mutates the exception object if it has a retry_count attribute to track
    the number of retries attempted before final failure.

    Args:
        exception: Exception that occurred on final attempt
        max_retries: Maximum number of retries configured
        func_name: Name of the function that failed for logging

    """
    if hasattr(exception, "retry_count"):
        exception.retry_count = max_retries
    logger.error(f"Function {func_name} failed after {max_retries} retries: {exception}")


def retry_with_backoff(
    exceptions: tuple[type[Exception], ...] = (Exception,),
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    *,
    jitter: bool = True,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Retry decorator with exponential backoff and jitter.

    Args:
        exceptions: Tuple of exception types to catch and retry
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds before first retry
        max_delay: Maximum delay in seconds
        backoff_factor: Multiplier for exponential backoff
        jitter: Whether to add random jitter to delays

    Returns:
        Decorated function with retry logic

    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries:
                        _handle_final_retry_attempt(e, max_retries, func.__name__)
                        raise

                    delay = _calculate_retry_delay(
                        attempt, base_delay, backoff_factor, max_delay, jitter=jitter
                    )

                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    time.sleep(delay)
            return None  # This line should never be reached due to raise in loop

        return wrapper

    return decorator


class CircuitBreakerOpenError(AlchemiserError):
    """Raised when circuit breaker is open."""


class CircuitBreaker:
    """Circuit breaker pattern for external service calls.

    Prevents cascading failures by temporarily stopping calls to failing services.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: float = 60.0,
        expected_exception: type[Exception] = Exception,
    ) -> None:
        """Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit (must be > 0)
            timeout: Time in seconds before trying to close circuit (must be > 0)
            expected_exception: Exception type that counts as failure

        Raises:
            ValueError: If failure_threshold or timeout are not positive

        """
        if failure_threshold <= 0:
            raise ValueError(f"failure_threshold must be positive, got {failure_threshold}")
        if timeout <= 0:
            raise ValueError(f"timeout must be positive, got {timeout}")

        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time: float | None = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
        """Apply circuit breaker pattern to a function.

        Args:
            func: Function to wrap with circuit breaker logic

        Returns:
            Callable: Wrapped function that implements circuit breaker pattern

        Raises:
            CircuitBreakerOpenError: When circuit is open and timeout has not elapsed
            Exception: Original exception when circuit allows call through

        """

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
            if self.state == "OPEN":
                if self.last_failure_time and time.time() - self.last_failure_time < self.timeout:
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker is OPEN for {func.__name__}. "
                        f"Retry after {self.timeout}s timeout."
                    )
                self.state = "HALF_OPEN"
                logger.info(f"Circuit breaker moving to HALF_OPEN for {func.__name__}")

            try:
                result = func(*args, **kwargs)
                if self.state == "HALF_OPEN":
                    self.state = "CLOSED"
                    self.failure_count = 0
                    logger.info(f"Circuit breaker CLOSED for {func.__name__}")
                return result
            except self.expected_exception:
                self.failure_count += 1
                self.last_failure_time = time.time()

                if self.failure_count >= self.failure_threshold:
                    self.state = "OPEN"
                    logger.warning(
                        f"Circuit breaker OPENED for {func.__name__} after "
                        f"{self.failure_count} failures"
                    )

                raise

        return wrapper


def categorize_error_severity(error: Exception) -> str:
    """Categorize error severity for monitoring.

    Args:
        error: Exception to categorize

    Returns:
        str: Severity level (LOW, MEDIUM, HIGH, CRITICAL)

    Note:
        Checks specific error types before base AlchemiserError to ensure
        proper severity classification for all exception subtypes.

    """
    # Check specific high-severity errors first
    if isinstance(error, (InsufficientFundsError, OrderExecutionError, PositionValidationError)):
        return ErrorSeverity.HIGH
    if isinstance(error, (MarketDataError, DataProviderError)) or _is_strategy_execution_error(
        error
    ):
        return ErrorSeverity.MEDIUM
    if isinstance(error, ConfigurationError):
        return ErrorSeverity.HIGH
    if isinstance(error, NotificationError):
        return ErrorSeverity.LOW
    # Fallback for base AlchemiserError (after specific subtypes)
    if isinstance(error, AlchemiserError):
        return ErrorSeverity.CRITICAL
    # Default for unknown exceptions
    return ErrorSeverity.MEDIUM
