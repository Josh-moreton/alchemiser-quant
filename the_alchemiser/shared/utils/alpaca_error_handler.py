"""Business Unit: shared | Status: current.

Alpaca Error Handling and Retry Logic Utility.

This module provides centralized error handling and retry logic for Alpaca API interactions.
It consolidates error detection, message sanitization, and standardized retry behavior
across all Alpaca-related services.
"""

from __future__ import annotations

import re
import time
from collections.abc import Generator
from contextlib import contextmanager
from decimal import Decimal
from secrets import randbelow
from typing import Any, Literal

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.broker import OrderExecutionResult

# Import exceptions for error handling with type safety
_RetryExcImported: type[Exception]
_HTTPErrorImported: type[Exception]
_RequestExcImported: type[Exception]

try:
    from alpaca.common.exceptions import RetryException as _RetryExcImported
    from requests.exceptions import HTTPError as _HTTPErrorImported
    from requests.exceptions import RequestException as _RequestExcImported
except ImportError:  # pragma: no cover - environment-dependent import
    # Fallback if imports are unavailable
    class _RetryExcImported(Exception):  # type: ignore[no-redef]
        """Fallback RetryException."""

    class _HTTPErrorImported(Exception):  # type: ignore[no-redef]
        """Fallback HTTPError."""

    class _RequestExcImported(Exception):  # type: ignore[no-redef]
        """Fallback RequestException."""


RetryException = _RetryExcImported
HTTPError = _HTTPErrorImported
RequestException = _RequestExcImported

logger = get_logger(__name__)


class AlpacaErrorHandler:
    """Utility for handling Alpaca API errors with retry logic.

    This class provides static methods for error detection, sanitization,
    and standardized error result creation across all Alpaca services.
    """

    @staticmethod
    def is_order_already_in_terminal_state(error: Exception) -> tuple[bool, str]:
        """Check if cancellation error indicates order is already in a terminal state.

        This handles cases where an order cannot be cancelled because it has already
        been filled, cancelled, or reached another terminal state. This is NOT an error
        condition - it means the order completed successfully or is already inactive.

        Args:
            error: Exception from cancellation attempt

        Returns:
            Tuple of (is_terminal, terminal_state) where terminal_state is one of:
            'filled', 'cancelled', 'rejected', 'expired', or empty string if not terminal

        """
        msg = str(error).lower()
        
        # Alpaca error code 42210000: "order is already in \"filled\" state"
        # This is the primary case from the issue
        if "42210000" in msg or 'order is already in "filled" state' in msg:
            return True, "filled"
        
        # Other terminal state patterns
        if 'order is already in "canceled" state' in msg or 'order is already in "cancelled" state' in msg:
            return True, "cancelled"
        
        if 'order is already in "rejected" state' in msg:
            return True, "rejected"
        
        if 'order is already in "expired" state' in msg:
            return True, "expired"
        
        # Generic terminal state check
        if "already in" in msg and "state" in msg:
            # Try to extract the state
            match = re.search(r'already in ["\']?(\w+)["\']? state', msg)
            if match:
                state = match.group(1).lower()
                if state in ["filled", "canceled", "cancelled", "rejected", "expired"]:
                    return True, state
        
        return False, ""

    @staticmethod
    def is_transient_error(error: Exception) -> tuple[bool, str]:
        """Determine if error is transient and should be retried.

        Args:
            error: Exception to check

        Returns:
            Tuple of (is_transient, reason_description)

        """
        msg = str(error)
        # Normalize common transient markers
        if "502" in msg or "Bad Gateway" in msg:
            return True, "502 Bad Gateway"
        if "503" in msg or "Service Unavailable" in msg:
            return True, "503 Service Unavailable"
        if "504" in msg or "Gateway Timeout" in msg or "timeout" in msg.lower():
            return True, "Gateway Timeout/Timeout"
        # HTML error pages from proxies
        if "<html" in msg.lower():
            # Try to extract status code
            m = re.search(r"\b(5\d{2})\b", msg)
            code = m.group(1) if m else "5xx"
            return True, f"HTTP {code} HTML error"
        return False, ""

    @staticmethod
    def sanitize_error_message(error: Exception) -> str:
        """Sanitize error message for logging and display.

        Args:
            error: Exception to sanitize

        Returns:
            Clean error message string

        """
        transient, reason = AlpacaErrorHandler.is_transient_error(error)
        if transient:
            return reason
        # Trim long HTML/text blobs
        msg = str(error)
        if "<html" in msg.lower():
            return "Upstream returned HTML error page"
        return msg

    @staticmethod
    def should_retry(error: Exception, attempt: int, max_retries: int) -> bool:
        """Determine if operation should be retried.

        Args:
            error: Exception that occurred
            attempt: Current attempt number (1-based)
            max_retries: Maximum number of retries allowed

        Returns:
            True if should retry, False otherwise

        """
        if attempt >= max_retries:
            return False

        transient, _ = AlpacaErrorHandler.is_transient_error(error)
        return transient

    @staticmethod
    def create_error_result(
        error: Exception,
        context: str = "Operation",
        order_id: str = "unknown",
        **kwargs: Any,  # noqa: ANN401
    ) -> OrderExecutionResult:
        """Create standardized error result objects.

        Args:
            error: Exception that occurred
            context: Context description for the error
            order_id: Order ID if applicable
            **kwargs: Additional parameters (unused but for interface compatibility)

        Returns:
            OrderExecutionResult with error details

        """
        from datetime import UTC, datetime

        status: Literal["accepted", "filled", "partially_filled", "rejected", "canceled"] = (
            "rejected"
        )

        return OrderExecutionResult(
            success=False,
            order_id=order_id,
            status=status,
            filled_qty=Decimal("0"),
            avg_fill_price=None,
            submitted_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
            error=f"{context} failed: {error!s}",
        )

    @staticmethod
    def format_final_error_message(error: Exception, symbol: str, summary: str) -> str:
        """Format final error message based on exception type.

        Args:
            error: Original exception
            symbol: Stock symbol for context
            summary: Sanitized error summary

        Returns:
            Formatted error message string

        """
        if isinstance(error, (RetryException, HTTPError, RequestException)):
            return f"Market data API error for {symbol}: {summary}"
        return f"Unexpected error for {symbol}: {summary}"


@contextmanager
def alpaca_retry_context(
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    base_delay: float = 1.0,
    operation_name: str = "Alpaca operation",
) -> Generator[None, None, None]:
    """Context manager for Alpaca operations with retry logic.

    Args:
        max_retries: Maximum number of retry attempts
        backoff_factor: Exponential backoff multiplier
        base_delay: Base delay in seconds for first retry
        operation_name: Name of operation for logging

    Raises:
        RuntimeError: If all retries are exhausted

    Yields:
        None

    Example:
        with alpaca_retry_context(max_retries=3, operation_name="Get market data"):
            # Your Alpaca API call here
            result = some_alpaca_api_call()

    """
    last_error: Exception | None = None

    for attempt in range(1, max_retries + 1):
        try:
            yield
            return  # Success, exit the context
        except (RetryException, HTTPError, RequestException, Exception) as e:
            last_error = e
            transient, reason = AlpacaErrorHandler.is_transient_error(e)

            if not transient or attempt == max_retries:
                # Non-transient error or final attempt
                summary = AlpacaErrorHandler.sanitize_error_message(e)
                error_msg = f"{operation_name} failed after {attempt} attempts: {summary}"
                logger.error(error_msg)
                raise RuntimeError(error_msg) from e

            # Calculate delay with exponential backoff and jitter
            jitter = 1.0 + 0.2 * (randbelow(1000) / 1000.0)
            sleep_duration = base_delay * (backoff_factor ** (attempt - 1)) * jitter

            logger.warning(
                f"{operation_name} transient error ({reason}); "
                f"retry {attempt}/{max_retries} in {sleep_duration:.2f}s"
            )
            time.sleep(sleep_duration)

    # This should never be reached due to the loop structure, but just in case
    if last_error:
        raise RuntimeError(f"{operation_name} failed after all retries") from last_error
