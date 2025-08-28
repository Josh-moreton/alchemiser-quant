"""Business Unit: utilities (shared kernel / cross-cutting) | Status: current.

Retry decorator with exponential backoff.

Pure retry mechanism for robust error handling across all contexts.
"""

from __future__ import annotations

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
    *,
    jitter: bool = True,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Retry decorator with exponential backoff and jitter.

    Args:
        exceptions: Exception types to retry on
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        backoff_factor: Exponential backoff multiplier
        jitter: Whether to add random jitter to delay

    Returns:
        Decorated function with retry logic

    """

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
