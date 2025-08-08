#!/usr/bin/env python3
"""
Retry Decorator with Exponential Backoff.

This module provides retry functionality with exponential backoff and jitter
for robust error handling according to the error handling improvement plan.
"""

import logging
import random
import time
from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

logger = logging.getLogger(__name__)

P = ParamSpec("P")
T = TypeVar("T")


def retry_with_backoff(
    exceptions: tuple[type[Exception], ...] = (Exception,),
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Retry decorator with exponential backoff and jitter."""

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            last_exception: Exception | None = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == max_retries:
                        # Add retry context to exception
                        if hasattr(e, "retry_count"):
                            e.retry_count = attempt
                        raise

                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (backoff_factor**attempt), max_delay)
                    if jitter:
                        delay *= 0.5 + random.random() * 0.5  # Add 50% jitter

                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    time.sleep(delay)

            # This should never be reached due to the raise in the except block
            if last_exception:
                raise last_exception
            raise RuntimeError("Unexpected state in retry logic")

        return wrapper

    return decorator


# Common retry configurations for different scenarios


def retry_api_call(
    max_retries: int = 3, base_delay: float = 1.0
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Retry decorator for API calls with common exceptions."""
    from the_alchemiser.services.exceptions import DataProviderError, TradingClientError

    return retry_with_backoff(
        exceptions=(DataProviderError, TradingClientError, ConnectionError, TimeoutError),
        max_retries=max_retries,
        base_delay=base_delay,
    )


def retry_data_fetch(
    max_retries: int = 3, base_delay: float = 0.5
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Retry decorator for data fetching operations."""
    from the_alchemiser.services.exceptions import DataProviderError

    return retry_with_backoff(
        exceptions=(DataProviderError, ConnectionError, TimeoutError),
        max_retries=max_retries,
        base_delay=base_delay,
    )


def retry_order_execution(
    max_retries: int = 2, base_delay: float = 0.5
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Retry decorator for order execution with limited retries."""
    from the_alchemiser.services.exceptions import OrderExecutionError

    return retry_with_backoff(
        exceptions=(OrderExecutionError,),
        max_retries=max_retries,
        base_delay=base_delay,
    )
