"""Business Unit: shared | Status: current.

Alpaca Error Handling and Retry Logic Utility.

This module provides centralized error handling and retry logic for Alpaca API interactions.
It consolidates error detection, message sanitization, and standardized retry behavior
across all Alpaca-related services.
"""

from __future__ import annotations

import re
import time
from collections.abc import Callable, Generator
from contextlib import contextmanager
from decimal import Decimal
from secrets import randbelow
from typing import Any, Literal

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.broker import OrderExecutionResult
from the_alchemiser.shared.schemas.execution_report import ExecutedOrder
from the_alchemiser.shared.schemas.operations import TerminalOrderError

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
    def _check_filled_state(msg: str) -> tuple[bool, TerminalOrderError | None]:
        """Check if error indicates order is already filled.

        Args:
            msg: Lowercase error message string

        Returns:
            Tuple of (is_filled, error_type) if filled, else (False, None)

        """
        if "42210000" in msg or 'order is already in "filled" state' in msg:
            return True, TerminalOrderError.ALREADY_FILLED
        return False, None

    @staticmethod
    def _check_cancelled_state(msg: str) -> tuple[bool, TerminalOrderError | None]:
        """Check if error indicates order is already cancelled.

        Args:
            msg: Lowercase error message string

        Returns:
            Tuple of (is_cancelled, error_type) if cancelled, else (False, None)

        """
        if (
            'order is already in "canceled" state' in msg
            or 'order is already in "cancelled" state' in msg
        ):
            return True, TerminalOrderError.ALREADY_CANCELLED
        return False, None

    @staticmethod
    def _check_rejected_state(msg: str) -> tuple[bool, TerminalOrderError | None]:
        """Check if error indicates order is already rejected.

        Args:
            msg: Lowercase error message string

        Returns:
            Tuple of (is_rejected, error_type) if rejected, else (False, None)

        """
        if 'order is already in "rejected" state' in msg:
            return True, TerminalOrderError.ALREADY_REJECTED
        return False, None

    @staticmethod
    def _check_expired_state(msg: str) -> tuple[bool, TerminalOrderError | None]:
        """Check if error indicates order is already expired.

        Args:
            msg: Lowercase error message string

        Returns:
            Tuple of (is_expired, error_type) if expired, else (False, None)

        """
        if 'order is already in "expired" state' in msg:
            return True, TerminalOrderError.ALREADY_EXPIRED
        return False, None

    @staticmethod
    def _check_generic_terminal_state(
        msg: str,
    ) -> tuple[bool, TerminalOrderError | None]:
        """Check for generic terminal state pattern and extract state name.

        Args:
            msg: Lowercase error message string

        Returns:
            Tuple of (is_terminal, error_type) if terminal state found, else (False, None)

        """
        if "already in" not in msg or "state" not in msg:
            return False, None

        match = re.search(r'already in ["\']?(\w+)["\']? state', msg)
        if not match:
            return False, None

        state = match.group(1).lower()
        if state == "filled":
            return True, TerminalOrderError.ALREADY_FILLED
        if state in ["canceled", "cancelled"]:
            return True, TerminalOrderError.ALREADY_CANCELLED
        if state == "rejected":
            return True, TerminalOrderError.ALREADY_REJECTED
        if state == "expired":
            return True, TerminalOrderError.ALREADY_EXPIRED

        return False, None

    @staticmethod
    def is_order_already_in_terminal_state(
        error: Exception,
    ) -> tuple[bool, TerminalOrderError | None]:
        r"""Check if cancellation error indicates order is already in a terminal state.

        This handles cases where an order cannot be cancelled because it has already
        been filled, cancelled, or reached another terminal state. This is NOT an error
        condition - it means the order completed successfully or is already inactive.

        Args:
            error: Exception from cancellation attempt

        Returns:
            Tuple of (is_terminal, terminal_error_type) where terminal_error_type is
            a TerminalOrderError enum value or None if not terminal

        Example:
            >>> error = Exception('{"code":42210000,"message":"order is already in \\"filled\\" state"}')
            >>> is_terminal, error_type = AlpacaErrorHandler.is_order_already_in_terminal_state(error)
            >>> print(is_terminal, error_type)
            True TerminalOrderError.ALREADY_FILLED

        """
        msg = str(error).lower()

        # Check each terminal state using dedicated helper methods
        for check_method in [
            AlpacaErrorHandler._check_filled_state,
            AlpacaErrorHandler._check_cancelled_state,
            AlpacaErrorHandler._check_rejected_state,
            AlpacaErrorHandler._check_expired_state,
            AlpacaErrorHandler._check_generic_terminal_state,
        ]:
            is_terminal, terminal_error = check_method(msg)
            if is_terminal:
                return True, terminal_error

        return False, None

    @staticmethod
    def _check_502_error(msg: str) -> tuple[bool, str]:
        """Check if error is a 502 Bad Gateway.

        Args:
            msg: Error message string

        Returns:
            Tuple of (is_502, reason) if match found, else (False, "")

        """
        if "502" in msg or "Bad Gateway" in msg:
            return True, "502 Bad Gateway"
        return False, ""

    @staticmethod
    def _check_503_error(msg: str) -> tuple[bool, str]:
        """Check if error is a 503 Service Unavailable.

        Args:
            msg: Error message string

        Returns:
            Tuple of (is_503, reason) if match found, else (False, "")

        """
        if "503" in msg or "Service Unavailable" in msg:
            return True, "503 Service Unavailable"
        return False, ""

    @staticmethod
    def _check_timeout_error(msg: str) -> tuple[bool, str]:
        """Check if error is a timeout or 504 Gateway Timeout.

        Args:
            msg: Error message string

        Returns:
            Tuple of (is_timeout, reason) if match found, else (False, "")

        """
        msg_lower = msg.lower()
        if "504" in msg or "Gateway Timeout" in msg or "timeout" in msg_lower:
            return True, "Gateway Timeout/Timeout"
        return False, ""

    @staticmethod
    def _check_html_error(msg: str) -> tuple[bool, str]:
        """Check if error contains HTML error page.

        Args:
            msg: Error message string

        Returns:
            Tuple of (is_html_error, reason) with extracted status code if found

        """
        if "<html" not in msg.lower():
            return False, ""

        m = re.search(r"\b(5\d{2})\b", msg)
        code = m.group(1) if m else "5xx"
        return True, f"HTTP {code} HTML error"

    @staticmethod
    def _check_dns_error(msg: str) -> tuple[bool, str]:
        """Check if error is a DNS resolution failure.

        DNS failures are transient - temporary network issues, DNS server
        unavailability, or routing problems.

        Args:
            msg: Error message string

        Returns:
            Tuple of (is_dns_error, reason) if match found, else (False, "")

        """
        msg_lower = msg.lower()
        dns_patterns = [
            "nameresolutionerror",
            "failed to resolve",
            "nodename nor servname",
            "name or service not known",
            "temporary failure in name resolution",
            "getaddrinfo failed",
        ]

        if any(pattern in msg_lower for pattern in dns_patterns):
            return True, "DNS Resolution Error"
        return False, ""

    @staticmethod
    def _check_connection_error(msg: str) -> tuple[bool, str]:
        """Check if error is a network connection failure.

        Connection failures are transient - network issues, firewall problems,
        or temporary service unavailability.

        Args:
            msg: Error message string

        Returns:
            Tuple of (is_connection_error, reason) if match found, else (False, "")

        """
        msg_lower = msg.lower()
        connection_patterns = [
            "connectionerror",
            "connection refused",
            "connection reset",
            "connection aborted",
            "max retries exceeded",  # urllib3 retry exhaustion
            "network is unreachable",
            "no route to host",
        ]

        if any(pattern in msg_lower for pattern in connection_patterns):
            return True, "Network Connection Error"
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

        # Check each error type using dedicated helper methods
        for check_method in [
            AlpacaErrorHandler._check_502_error,
            AlpacaErrorHandler._check_503_error,
            AlpacaErrorHandler._check_timeout_error,
            AlpacaErrorHandler._check_dns_error,
            AlpacaErrorHandler._check_connection_error,
            AlpacaErrorHandler._check_html_error,
        ]:
            is_transient, reason = check_method(msg)
            if is_transient:
                return True, reason

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
        if isinstance(error, RetryException | HTTPError | RequestException):
            return f"Market data API error for {symbol}: {summary}"
        return f"Unexpected error for {symbol}: {summary}"

    @staticmethod
    def create_executed_order_error_result(
        order_id: str,
        symbol: str,
        side: str,
        qty: float | None,
        error_message: str,
    ) -> ExecutedOrder:
        """Create error ExecutedOrder for failed orders.

        This provides a standardized way to create ExecutedOrder objects for error cases,
        ensuring consistent error handling across AlpacaManager and AlpacaTradingService.

        Args:
            order_id: Order identifier (usually error type like "INVALID", "FAILED")
            symbol: Stock symbol
            side: Trading side ("buy" or "sell")
            qty: Order quantity (can be None)
            error_message: Error description

        Returns:
            ExecutedOrder object with error details

        """
        from datetime import UTC, datetime
        from decimal import Decimal

        # Ensure action is a valid Literal type
        action_str = side.upper() if side and side.upper() in ["BUY", "SELL"] else "BUY"
        action: Literal["BUY", "SELL"] = action_str  # type: ignore[assignment]

        return ExecutedOrder(
            order_id=order_id,
            symbol=symbol.upper() if symbol else "UNKNOWN",
            action=action,
            quantity=Decimal(str(qty)) if qty and qty > 0 else Decimal("0.01"),
            filled_quantity=Decimal("0"),
            price=Decimal("0.01"),
            total_value=Decimal("0.01"),  # Must be > 0
            status="REJECTED",
            execution_timestamp=datetime.now(UTC),
            error_message=error_message,
        )

    @staticmethod
    def handle_market_order_errors(
        symbol: str,
        side: str,
        qty: float | None,
        operation_func: Callable[[], ExecutedOrder],
    ) -> ExecutedOrder:
        """Handle common error patterns in market order operations.

        This function provides a standardized way to handle ValueError and Exception
        errors that occur during market order placement, eliminating code duplication
        between AlpacaManager and AlpacaTradingService.

        Args:
            symbol: Stock symbol for error context
            side: Trading side ("buy" or "sell") for error context
            qty: Order quantity for error context
            operation_func: Function that performs the actual order operation

        Returns:
            ExecutedOrder from successful operation or error result

        """
        try:
            return operation_func()
        except ValueError as e:
            logger.error("Invalid order parameters", error=str(e))
            return AlpacaErrorHandler.create_executed_order_error_result(
                "INVALID", symbol, side, qty, str(e)
            )
        except Exception as e:
            logger.error("Failed to place market order for", symbol=symbol, error=str(e))
            return AlpacaErrorHandler.create_executed_order_error_result(
                "FAILED", symbol, side, qty, str(e)
            )


def _calculate_retry_delay(base_delay: float, backoff_factor: float, attempt: int) -> float:
    """Calculate retry delay with exponential backoff and jitter.

    Args:
        base_delay: Base delay in seconds
        backoff_factor: Exponential backoff multiplier
        attempt: Current attempt number (1-based)

    Returns:
        Sleep duration in seconds with jitter applied

    """
    jitter = 1.0 + 0.2 * (randbelow(1000) / 1000.0)
    return base_delay * (backoff_factor ** (attempt - 1)) * jitter


def _should_raise_error(
    transient: bool,  # noqa: FBT001
    attempt: int,
    max_retries: int,
) -> bool:
    """Determine if error should be raised or retry should continue.

    Args:
        transient: Whether error is transient
        attempt: Current attempt number
        max_retries: Maximum number of retries

    Returns:
        True if error should be raised, False if should retry

    """
    return not transient or attempt == max_retries


def _handle_retry_failure(error: Exception, operation_name: str, attempt: int) -> None:
    """Handle final retry failure by logging and raising RuntimeError.

    Args:
        error: Exception that occurred
        operation_name: Name of operation for logging
        attempt: Current attempt number

    Raises:
        RuntimeError: Always raises with formatted error message

    """
    summary = AlpacaErrorHandler.sanitize_error_message(error)
    error_msg = f"{operation_name} failed after {attempt} attempts: {summary}"

    # Check if this is an expected 404 (position/resource doesn't exist)
    error_str = str(error).lower()
    is_404_not_found = (
        "position does not exist" in error_str
        or "40410000" in str(error)
        or "not found" in error_str
    )

    # Use warning for expected 404s (resource doesn't exist), error for everything else
    if is_404_not_found:
        logger.warning(error_msg)
    else:
        logger.error(error_msg)

    raise RuntimeError(error_msg) from error


def _log_retry_attempt(
    operation_name: str,
    reason: str,
    attempt: int,
    max_retries: int,
    sleep_duration: float,
) -> None:
    """Log retry attempt with details.

    Args:
        operation_name: Name of operation
        reason: Reason for retry (error description)
        attempt: Current attempt number
        max_retries: Maximum number of retries
        sleep_duration: Sleep duration in seconds

    """
    logger.warning(
        f"{operation_name} transient error ({reason}); "
        f"retry {attempt}/{max_retries} in {sleep_duration:.2f}s"
    )


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

            if _should_raise_error(transient, attempt, max_retries):
                _handle_retry_failure(e, operation_name, attempt)

            sleep_duration = _calculate_retry_delay(base_delay, backoff_factor, attempt)
            _log_retry_attempt(operation_name, reason, attempt, max_retries, sleep_duration)
            time.sleep(sleep_duration)

    # This should never be reached due to the loop structure, but just in case
    if last_error:
        raise RuntimeError(f"{operation_name} failed after all retries") from last_error
