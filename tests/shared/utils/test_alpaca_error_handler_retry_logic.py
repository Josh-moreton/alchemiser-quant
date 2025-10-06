"""Business Unit: shared | Status: current.

Test Alpaca error handler's retry logic and helper functions.

This test validates the retry context manager, delay calculations,
and error result creation methods to supplement existing tests.
"""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from the_alchemiser.shared.utils.alpaca_error_handler import (
    AlpacaErrorHandler,
    _calculate_retry_delay,
    alpaca_retry_context,
)


class TestCalculateRetryDelay:
    """Test retry delay calculation with exponential backoff and jitter."""

    def test_delay_increases_exponentially(self) -> None:
        """Test that delay increases exponentially with attempts."""
        base_delay = 1.0
        backoff_factor = 2.0

        delay1 = _calculate_retry_delay(base_delay, backoff_factor, 1)
        delay2 = _calculate_retry_delay(base_delay, backoff_factor, 2)
        delay3 = _calculate_retry_delay(base_delay, backoff_factor, 3)

        # Due to jitter, we can't test exact values, but we can test ranges
        # Attempt 1: base_delay * 2^0 * jitter(0.8-1.2) = 1.0 * 1.0 * (1.0-1.2) = 1.0-1.2
        assert 1.0 <= delay1 <= 1.2

        # Attempt 2: base_delay * 2^1 * jitter(0.8-1.2) = 1.0 * 2.0 * (1.0-1.2) = 2.0-2.4
        assert 2.0 <= delay2 <= 2.4

        # Attempt 3: base_delay * 2^2 * jitter(0.8-1.2) = 1.0 * 4.0 * (1.0-1.2) = 4.0-4.8
        assert 4.0 <= delay3 <= 4.8

    def test_jitter_adds_randomness(self) -> None:
        """Test that jitter adds randomness to prevent thundering herd."""
        delays = [_calculate_retry_delay(1.0, 2.0, 1) for _ in range(10)]

        # With jitter, we should see variation in delays
        # All should be in range [1.0, 1.2]
        assert all(1.0 <= d <= 1.2 for d in delays)

        # At least some should be different (not all exactly 1.0)
        assert len(set(delays)) > 1

    def test_base_delay_affects_result(self) -> None:
        """Test that base delay parameter affects the result."""
        delay_small = _calculate_retry_delay(0.5, 2.0, 1)
        delay_large = _calculate_retry_delay(2.0, 2.0, 1)

        # Large base should produce larger delays
        assert delay_large > delay_small

    def test_backoff_factor_affects_growth(self) -> None:
        """Test that backoff factor affects exponential growth."""
        # Factor of 1.5 should grow slower than factor of 3.0
        delay_slow = _calculate_retry_delay(1.0, 1.5, 3)
        delay_fast = _calculate_retry_delay(1.0, 3.0, 3)

        # Fast backoff should produce much larger delays
        assert delay_fast > delay_slow
        # 1.5^2 = 2.25, 3.0^2 = 9.0
        assert delay_fast / delay_slow > 2.0  # Should be roughly 4x


class TestAlpacaRetryContext:
    """Test the alpaca_retry_context context manager.
    
    Note: Testing retry context managers is complex because exceptions raised
    inside the yield cause generator protocol issues. These tests focus on
    verifying the helper functions and integration with real usage patterns.
    """

    def test_success_on_first_attempt(self) -> None:
        """Test that successful operation completes without retry."""
        call_count = [0]

        with alpaca_retry_context(max_retries=3, operation_name="Test operation"):
            call_count[0] += 1

        assert call_count[0] == 1


class TestCreateErrorResult:
    """Test error result creation methods."""

    def test_create_error_result_basic(self) -> None:
        """Test basic error result creation."""
        error = Exception("Test error")

        result = AlpacaErrorHandler.create_error_result(
            error=error, context="Order placement", order_id="test-123"
        )

        assert result.success is False
        assert result.order_id == "test-123"
        assert result.status == "rejected"
        assert result.filled_qty == Decimal("0")
        assert result.avg_fill_price is None
        assert "Order placement failed" in result.error
        assert "Test error" in result.error

    def test_create_error_result_with_defaults(self) -> None:
        """Test error result with default parameters."""
        error = Exception("Test error")

        result = AlpacaErrorHandler.create_error_result(error=error)

        assert result.success is False
        assert result.order_id == "unknown"
        assert "Operation failed" in result.error

    def test_create_executed_order_error_result_basic(self) -> None:
        """Test executed order error result creation."""
        result = AlpacaErrorHandler.create_executed_order_error_result(
            order_id="ERR-123",
            symbol="AAPL",
            side="buy",
            qty=100.0,
            error_message="Insufficient buying power",
        )

        assert result.order_id == "ERR-123"
        assert result.symbol == "AAPL"
        assert result.action == "BUY"
        assert result.quantity == Decimal("100")
        assert result.filled_quantity == Decimal("0")
        assert result.status == "REJECTED"
        assert result.error_message == "Insufficient buying power"

    def test_create_executed_order_handles_none_symbol(self) -> None:
        """Test that None symbol is handled gracefully."""
        result = AlpacaErrorHandler.create_executed_order_error_result(
            order_id="ERR-123",
            symbol=None,  # type: ignore[arg-type]
            side="buy",
            qty=100.0,
            error_message="Error",
        )

        assert result.symbol == "UNKNOWN"

    def test_create_executed_order_handles_invalid_side(self) -> None:
        """Test that invalid side defaults to BUY."""
        result = AlpacaErrorHandler.create_executed_order_error_result(
            order_id="ERR-123", symbol="AAPL", side="invalid", qty=100.0, error_message="Error"
        )

        assert result.action == "BUY"

    def test_create_executed_order_handles_none_qty(self) -> None:
        """Test that None quantity is handled gracefully."""
        result = AlpacaErrorHandler.create_executed_order_error_result(
            order_id="ERR-123", symbol="AAPL", side="buy", qty=None, error_message="Error"
        )

        assert result.quantity == Decimal("0.01")

    def test_create_executed_order_handles_negative_qty(self) -> None:
        """Test that negative quantity is handled gracefully."""
        result = AlpacaErrorHandler.create_executed_order_error_result(
            order_id="ERR-123", symbol="AAPL", side="sell", qty=-50.0, error_message="Error"
        )

        assert result.quantity == Decimal("0.01")

    def test_create_executed_order_sell_side(self) -> None:
        """Test sell side is properly handled."""
        result = AlpacaErrorHandler.create_executed_order_error_result(
            order_id="ERR-123", symbol="AAPL", side="sell", qty=100.0, error_message="Error"
        )

        assert result.action == "SELL"


class TestHandleMarketOrderErrors:
    """Test handle_market_order_errors wrapper function."""

    def test_successful_operation(self) -> None:
        """Test that successful operation returns result directly."""
        from datetime import UTC, datetime

        from the_alchemiser.shared.schemas.execution_report import ExecutedOrder

        expected_result = ExecutedOrder(
            order_id="123",
            symbol="AAPL",
            action="BUY",
            quantity=Decimal("100"),
            filled_quantity=Decimal("100"),
            price=Decimal("150.00"),
            total_value=Decimal("15000.00"),
            status="FILLED",
            execution_timestamp=datetime.now(UTC),
        )

        result = AlpacaErrorHandler.handle_market_order_errors(
            symbol="AAPL", side="buy", qty=100.0, operation_func=lambda: expected_result
        )

        assert result == expected_result

    def test_handles_value_error(self) -> None:
        """Test that ValueError is caught and converted to error result."""

        def failing_op():
            raise ValueError("Invalid parameters")

        result = AlpacaErrorHandler.handle_market_order_errors(
            symbol="AAPL", side="buy", qty=100.0, operation_func=failing_op
        )

        assert result.order_id == "INVALID"
        assert result.status == "REJECTED"
        assert "Invalid parameters" in result.error_message

    def test_handles_generic_exception(self) -> None:
        """Test that generic Exception is caught and converted to error result."""

        def failing_op():
            raise RuntimeError("Network timeout")

        result = AlpacaErrorHandler.handle_market_order_errors(
            symbol="AAPL", side="buy", qty=100.0, operation_func=failing_op
        )

        assert result.order_id == "FAILED"
        assert result.status == "REJECTED"
        assert "Network timeout" in result.error_message


class TestSanitizeErrorMessage:
    """Test error message sanitization."""

    def test_sanitize_transient_error(self) -> None:
        """Test that transient errors return clean reason."""
        error = Exception("502 Bad Gateway")

        sanitized = AlpacaErrorHandler.sanitize_error_message(error)

        assert sanitized == "502 Bad Gateway"

    def test_sanitize_html_error(self) -> None:
        """Test that HTML errors are sanitized."""
        error = Exception("<html><body>Some very long error page content...</body></html>")

        sanitized = AlpacaErrorHandler.sanitize_error_message(error)

        # The sanitize function first checks for transient errors (HTML matches the _check_html_error)
        # which returns "HTTP 5xx HTML error" when no specific code is found
        assert sanitized == "HTTP 5xx HTML error"

    def test_sanitize_normal_error(self) -> None:
        """Test that normal errors pass through."""
        error = Exception("Insufficient buying power")

        sanitized = AlpacaErrorHandler.sanitize_error_message(error)

        assert sanitized == "Insufficient buying power"
