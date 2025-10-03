"""Business Unit: shared | Status: current.

Tests for enhanced exception classes with context tracking and retry metadata.
"""

import pytest

from the_alchemiser.shared.errors.context import ErrorContextData
from the_alchemiser.shared.errors.enhanced_exceptions import (
    EnhancedAlchemiserError,
    EnhancedDataError,
    EnhancedTradingError,
)
from the_alchemiser.shared.errors.error_types import ErrorSeverity


class TestEnhancedAlchemiserError:
    """Test EnhancedAlchemiserError base class."""

    def test_create_error_with_message_only(self):
        """Test creating error with just a message."""
        error = EnhancedAlchemiserError("Test error")
        assert str(error) == "Test error"
        assert error.original_message == "Test error"
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.recoverable is True
        assert error.retry_count == 0
        assert error.max_retries == 3

    def test_create_error_with_context_dict(self):
        """Test creating error with context as dict."""
        context = {"module": "test", "correlation_id": "corr-123"}
        error = EnhancedAlchemiserError("Test error", context=context)
        assert error.context == context
        assert error.context["correlation_id"] == "corr-123"

    def test_create_error_with_context_data(self):
        """Test creating error with ErrorContextData."""
        context = ErrorContextData(
            module="strategy_v2",
            function="generate_signal",
            correlation_id="corr-456",
        )
        error = EnhancedAlchemiserError("Signal error", context=context)
        assert error.context["module"] == "strategy_v2"
        assert error.context["function"] == "generate_signal"
        assert error.context["correlation_id"] == "corr-456"

    def test_create_error_with_severity(self):
        """Test creating error with custom severity."""
        error = EnhancedAlchemiserError("Critical error", severity=ErrorSeverity.CRITICAL)
        assert error.severity == ErrorSeverity.CRITICAL

    def test_create_error_with_retry_params(self):
        """Test creating error with custom retry parameters."""
        error = EnhancedAlchemiserError(
            "Retryable error",
            recoverable=True,
            retry_count=1,
            max_retries=5,
        )
        assert error.recoverable is True
        assert error.retry_count == 1
        assert error.max_retries == 5

    def test_error_id_generation(self):
        """Test that error_id is generated and unique."""
        error1 = EnhancedAlchemiserError("Error 1")
        error2 = EnhancedAlchemiserError("Error 2")
        assert error1.error_id is not None
        assert error2.error_id is not None
        assert error1.error_id != error2.error_id

    def test_context_preservation_with_correlation_id(self):
        """Test that correlation_id is preserved in context."""
        correlation_id = "test-correlation-789"
        context = ErrorContextData(correlation_id=correlation_id)
        error = EnhancedAlchemiserError("Test error", context=context)
        assert error.context["correlation_id"] == correlation_id

    def test_context_preservation_with_causation_id(self):
        """Test that causation_id can be preserved in additional_data."""
        context = ErrorContextData(
            correlation_id="corr-123",
            additional_data={"causation_id": "cause-456"},
        )
        error = EnhancedAlchemiserError("Test error", context=context)
        assert error.context["correlation_id"] == "corr-123"
        assert error.context["additional_data"]["causation_id"] == "cause-456"


class TestEnhancedAlchemiserErrorRetry:
    """Test retry-related methods of EnhancedAlchemiserError."""

    def test_should_retry_when_recoverable_and_under_max(self):
        """Test should_retry returns True when conditions are met."""
        error = EnhancedAlchemiserError(
            "Retryable error",
            recoverable=True,
            retry_count=1,
            max_retries=3,
        )
        assert error.should_retry() is True

    def test_should_not_retry_when_not_recoverable(self):
        """Test should_retry returns False when not recoverable."""
        error = EnhancedAlchemiserError(
            "Non-recoverable error",
            recoverable=False,
            retry_count=0,
            max_retries=3,
        )
        assert error.should_retry() is False

    def test_should_not_retry_when_max_retries_reached(self):
        """Test should_retry returns False when max retries reached."""
        error = EnhancedAlchemiserError(
            "Max retries reached",
            recoverable=True,
            retry_count=3,
            max_retries=3,
        )
        assert error.should_retry() is False

    def test_get_retry_delay_exponential_backoff(self):
        """Test get_retry_delay uses exponential backoff."""
        error1 = EnhancedAlchemiserError("Test", retry_count=0)
        error2 = EnhancedAlchemiserError("Test", retry_count=1)
        error3 = EnhancedAlchemiserError("Test", retry_count=2)

        delay1 = error1.get_retry_delay()
        delay2 = error2.get_retry_delay()
        delay3 = error3.get_retry_delay()

        # Delays should increase exponentially
        assert delay1 == 1.0  # 2^0
        assert delay2 == 2.0  # 2^1
        assert delay3 == 4.0  # 2^2

    def test_get_retry_delay_max_cap(self):
        """Test get_retry_delay is capped at 60 seconds."""
        error = EnhancedAlchemiserError("Test", retry_count=10)
        delay = error.get_retry_delay()
        assert delay == 60.0  # Should be capped at max

    def test_increment_retry_creates_new_instance(self):
        """Test increment_retry creates a new instance with incremented count."""
        original = EnhancedAlchemiserError(
            "Test error",
            context={"test": "data"},
            retry_count=1,
            max_retries=5,
        )
        incremented = original.increment_retry()

        # Should be a new instance
        assert incremented is not original
        # Retry count should be incremented
        assert incremented.retry_count == 2
        # Other properties should be preserved
        assert incremented.original_message == original.original_message
        assert incremented.max_retries == original.max_retries
        assert incremented.context == original.context

    def test_increment_retry_preserves_context(self):
        """Test increment_retry preserves correlation and causation IDs."""
        context = ErrorContextData(
            correlation_id="corr-123",
            additional_data={"causation_id": "cause-456"},
        )
        original = EnhancedAlchemiserError("Test", context=context)
        incremented = original.increment_retry()

        assert incremented.context["correlation_id"] == "corr-123"
        assert incremented.context["additional_data"]["causation_id"] == "cause-456"


class TestEnhancedAlchemiserErrorSerialization:
    """Test serialization methods of EnhancedAlchemiserError."""

    def test_to_dict_basic(self):
        """Test to_dict with basic error."""
        error = EnhancedAlchemiserError("Test error")
        result = error.to_dict()

        assert isinstance(result, dict)
        assert result["error_id"] == error.error_id
        assert result["severity"] == ErrorSeverity.MEDIUM
        assert result["recoverable"] is True
        assert result["retry_count"] == 0
        assert result["max_retries"] == 3

    def test_to_dict_with_context(self):
        """Test to_dict preserves context."""
        context = {"module": "test", "correlation_id": "corr-789"}
        error = EnhancedAlchemiserError("Test", context=context)
        result = error.to_dict()

        assert result["context"] == context
        assert result["context"]["correlation_id"] == "corr-789"

    def test_to_dict_with_all_fields(self):
        """Test to_dict with all fields populated."""
        context = ErrorContextData(
            module="portfolio_v2",
            function="rebalance",
            operation="calculate_positions",
            correlation_id="corr-123",
            additional_data={"causation_id": "cause-456"},
        )
        error = EnhancedAlchemiserError(
            "Complex error",
            context=context,
            severity=ErrorSeverity.HIGH,
            recoverable=True,
            retry_count=2,
            max_retries=5,
        )
        result = error.to_dict()

        assert result["severity"] == ErrorSeverity.HIGH
        assert result["recoverable"] is True
        assert result["retry_count"] == 2
        assert result["max_retries"] == 5
        assert result["context"]["module"] == "portfolio_v2"
        assert result["context"]["correlation_id"] == "corr-123"


class TestEnhancedTradingError:
    """Test EnhancedTradingError subclass."""

    def test_create_trading_error_with_symbol(self):
        """Test creating trading error with symbol."""
        error = EnhancedTradingError("Trade failed", symbol="AAPL")
        assert error.symbol == "AAPL"
        assert error.order_id is None
        assert error.quantity is None
        assert error.price is None

    def test_create_trading_error_with_all_fields(self):
        """Test creating trading error with all trading fields."""
        error = EnhancedTradingError(
            "Order execution failed",
            symbol="TSLA",
            order_id="order-123",
            quantity=100.0,
            price=250.50,
        )
        assert error.symbol == "TSLA"
        assert error.order_id == "order-123"
        assert error.quantity == 100.0
        assert error.price == 250.50

    def test_trading_error_to_dict_includes_trading_fields(self):
        """Test to_dict includes trading-specific fields."""
        error = EnhancedTradingError(
            "Trade failed",
            symbol="NVDA",
            order_id="ord-456",
            quantity=50.0,
            price=500.25,
        )
        result = error.to_dict()

        assert result["symbol"] == "NVDA"
        assert result["order_id"] == "ord-456"
        assert result["quantity"] == 50.0
        assert result["price"] == 500.25

    def test_trading_error_inherits_base_functionality(self):
        """Test that trading error inherits all base error functionality."""
        error = EnhancedTradingError(
            "Trade failed",
            symbol="AAPL",
            severity=ErrorSeverity.HIGH,
            retry_count=1,
        )
        assert error.should_retry() is True
        assert error.get_retry_delay() == 2.0


class TestEnhancedDataError:
    """Test EnhancedDataError subclass."""

    def test_create_data_error(self):
        """Test creating data error."""
        error = EnhancedDataError("Data fetch failed")
        assert isinstance(error, EnhancedAlchemiserError)
        assert str(error) == "Data fetch failed"

    def test_data_error_inherits_base_functionality(self):
        """Test that data error inherits all base error functionality."""
        context = ErrorContextData(
            module="data_provider",
            correlation_id="corr-data-123",
        )
        error = EnhancedDataError(
            "Provider timeout",
            context=context,
            severity=ErrorSeverity.MEDIUM,
        )
        assert error.context["correlation_id"] == "corr-data-123"
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.should_retry() is True


class TestEnhancedExceptionsIntegration:
    """Test integration scenarios for enhanced exceptions."""

    def test_retry_workflow(self):
        """Test a complete retry workflow."""
        error = EnhancedAlchemiserError(
            "Initial failure",
            recoverable=True,
            retry_count=0,
            max_retries=3,
        )

        # First attempt
        assert error.should_retry() is True
        assert error.get_retry_delay() == 1.0

        # Increment for retry
        error = error.increment_retry()
        assert error.retry_count == 1
        assert error.should_retry() is True
        assert error.get_retry_delay() == 2.0

        # Second increment
        error = error.increment_retry()
        assert error.retry_count == 2
        assert error.should_retry() is True

        # Third increment - max reached
        error = error.increment_retry()
        assert error.retry_count == 3
        assert error.should_retry() is False

    def test_error_context_propagation(self):
        """Test that context propagates through retry cycles."""
        context = ErrorContextData(
            module="execution_v2",
            operation="place_order",
            correlation_id="corr-exec-123",
            additional_data={
                "causation_id": "cause-signal-456",
                "event_id": "evt-789",
            },
        )

        error = EnhancedAlchemiserError("Execution failed", context=context)

        # Increment multiple times
        for _ in range(3):
            error = error.increment_retry()

        # Context should be preserved
        result = error.to_dict()
        assert result["context"]["correlation_id"] == "corr-exec-123"
        assert result["context"]["additional_data"]["causation_id"] == "cause-signal-456"
        assert result["retry_count"] == 3
