"""Business Unit: shared; Status: current.

API Helper Utilities.

Provides utilities for API calls including timeout handling and rate limiting
to ensure robust and compliant API interactions.

Key Features:
- Timeout wrapper for API calls
- Rate limiting with exponential backoff
- Structured error handling
"""

from __future__ import annotations

import functools
import time
from collections.abc import Callable
from typing import Any, TypeVar

from the_alchemiser.shared.errors.exceptions import RateLimitError, TradingClientError
from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class RateLimiter:
    """Rate limiter with exponential backoff.

    Tracks API calls and enforces rate limits to prevent exceeding
    broker API quotas.
    """

    def __init__(
        self,
        *,
        calls_per_minute: int = 200,
        calls_per_hour: int = 10000,
        backoff_base: float = 2.0,
        max_backoff: float = 60.0,
    ) -> None:
        """Initialize rate limiter.

        Args:
            calls_per_minute: Maximum calls allowed per minute
            calls_per_hour: Maximum calls allowed per hour
            backoff_base: Base for exponential backoff calculation
            max_backoff: Maximum backoff time in seconds

        """
        self.calls_per_minute = calls_per_minute
        self.calls_per_hour = calls_per_hour
        self.backoff_base = backoff_base
        self.max_backoff = max_backoff

        # Track call timestamps
        self._minute_calls: list[float] = []
        self._hour_calls: list[float] = []
        self._consecutive_errors = 0
        self._last_error_time: float | None = None

    def _cleanup_old_calls(self) -> None:
        """Remove calls outside the tracking windows."""
        current_time = time.time()
        minute_ago = current_time - 60
        hour_ago = current_time - 3600

        self._minute_calls = [t for t in self._minute_calls if t > minute_ago]
        self._hour_calls = [t for t in self._hour_calls if t > hour_ago]

    def check_rate_limit(self) -> tuple[bool, float]:
        """Check if a call can be made now.

        Returns:
            Tuple of (can_call, wait_time_seconds)

        """
        self._cleanup_old_calls()
        current_time = time.time()

        # Check minute limit
        if len(self._minute_calls) >= self.calls_per_minute:
            oldest_call = min(self._minute_calls)
            wait_time = 60 - (current_time - oldest_call)
            return False, max(0, wait_time)

        # Check hour limit
        if len(self._hour_calls) >= self.calls_per_hour:
            oldest_call = min(self._hour_calls)
            wait_time = 3600 - (current_time - oldest_call)
            return False, max(0, wait_time)

        return True, 0.0

    def record_call(self) -> None:
        """Record a successful API call."""
        current_time = time.time()
        self._minute_calls.append(current_time)
        self._hour_calls.append(current_time)
        self._consecutive_errors = 0

    def record_error(self) -> float:
        """Record a rate limit error and calculate backoff.

        Returns:
            Backoff time in seconds

        """
        self._consecutive_errors += 1
        self._last_error_time = time.time()

        # Calculate exponential backoff
        backoff = min(self.backoff_base**self._consecutive_errors, self.max_backoff)

        logger.warning(
            "Rate limit error, applying backoff",
            consecutive_errors=self._consecutive_errors,
            backoff_seconds=backoff,
        )

        return backoff

    def reset_errors(self) -> None:
        """Reset error tracking after successful calls."""
        self._consecutive_errors = 0
        self._last_error_time = None


# Global rate limiter instance
_rate_limiter = RateLimiter()


def with_rate_limiting(func: Callable[..., T]) -> Callable[..., T]:  # noqa: UP047
    """Apply rate limiting to API calls.

    Args:
        func: Function to wrap

    Returns:
        Wrapped function with rate limiting

    Raises:
        RateLimitError: If rate limit exceeded and backoff required

    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:  # noqa: ANN401
        # Check rate limit
        can_call, wait_time = _rate_limiter.check_rate_limit()

        if not can_call:
            logger.warning(
                "Rate limit would be exceeded",
                function=func.__name__,
                wait_time_seconds=wait_time,
            )
            raise RateLimitError(
                f"Rate limit exceeded, retry after {wait_time:.1f} seconds",
                retry_after=int(wait_time) + 1,
            )

        try:
            result = func(*args, **kwargs)
            _rate_limiter.record_call()
            return result
        except Exception as e:
            # Check if it's a rate limit error from the API
            error_str = str(e).lower()
            if (
                "rate limit" in error_str
                or "429" in error_str
                or "too many requests" in error_str
            ):
                backoff = _rate_limiter.record_error()
                raise RateLimitError(
                    f"API rate limit error: {e}",
                    retry_after=int(backoff) + 1,
                ) from e
            raise

    return wrapper


def with_timeout(
    timeout_seconds: float = 10.0,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Apply timeout to API calls.

    Note: This is a simplified implementation. For production use with
    blocking I/O, consider using concurrent.futures or signal-based timeouts.

    Args:
        timeout_seconds: Maximum time to wait for the call

    Returns:
        Decorator function

    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:  # noqa: ANN401
            # For now, just log the timeout intent and call the function
            # Full implementation would require threading or async support
            logger.debug(
                "API call with timeout",
                function=func.__name__,
                timeout_seconds=timeout_seconds,
            )

            # TODO: Implement actual timeout mechanism
            # Options:
            # 1. Use concurrent.futures.ThreadPoolExecutor with timeout
            # 2. Use signal.alarm() on Unix systems
            # 3. Use async/await with asyncio.wait_for()

            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Check for timeout-like errors
                error_str = str(e).lower()
                if "timeout" in error_str or "timed out" in error_str:
                    logger.error(
                        "API call timeout",
                        function=func.__name__,
                        timeout_seconds=timeout_seconds,
                        error=str(e),
                    )
                    raise TradingClientError(
                        f"API call timed out after {timeout_seconds}s: {e}"
                    ) from e
                raise

        return wrapper

    return decorator
