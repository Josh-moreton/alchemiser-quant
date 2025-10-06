"""Business Unit: shared | Status: current

Comprehensive unit tests for trading error classification module.

This test suite provides coverage for OrderError exception class and
classify_exception utility function.
"""

import pytest

from the_alchemiser.shared.types.exceptions import (
    AlchemiserError,
    ConfigurationError,
    OrderExecutionError,
)
from the_alchemiser.shared.types.trading_errors import OrderError, classify_exception


class TestOrderError:
    """Test OrderError exception class."""

    def test_order_error_basic_initialization(self):
        """Test basic OrderError initialization without optional parameters."""
        error = OrderError("Order placement failed")

        assert str(error) == "Order placement failed"
        assert error.message == "Order placement failed"
        assert error.order_id is None
        assert error.context == {}
        assert hasattr(error, "timestamp")

    def test_order_error_with_order_id(self):
        """Test OrderError initialization with order_id."""
        error = OrderError("Order failed", order_id="order-123")

        assert error.message == "Order failed"
        assert error.order_id == "order-123"
        assert error.context["order_id"] == "order-123"

    def test_order_error_with_context(self):
        """Test OrderError initialization with custom context."""
        context = {"symbol": "AAPL", "quantity": 100, "side": "buy"}
        error = OrderError("Invalid order parameters", context=context)

        assert error.message == "Invalid order parameters"
        assert error.context["symbol"] == "AAPL"
        assert error.context["quantity"] == 100
        assert error.context["side"] == "buy"
        assert error.order_id is None

    def test_order_error_with_order_id_and_context(self):
        """Test OrderError with both order_id and context."""
        context = {"symbol": "TSLA", "reason": "insufficient_funds"}
        error = OrderError("Order rejected", order_id="order-456", context=context)

        assert error.message == "Order rejected"
        assert error.order_id == "order-456"
        assert error.context["order_id"] == "order-456"
        assert error.context["symbol"] == "TSLA"
        assert error.context["reason"] == "insufficient_funds"

    def test_order_error_context_not_mutated_when_none(self):
        """Test that passing None for context creates empty dict."""
        error = OrderError("Test error", context=None)

        assert error.context == {}
        assert isinstance(error.context, dict)

    def test_order_error_context_order_id_override(self):
        """Test that order_id parameter adds to context dict."""
        # Pre-existing order_id in context should be overridden by parameter
        context = {"order_id": "old-id", "extra": "data"}
        error = OrderError("Test", order_id="new-id", context=context)

        assert error.order_id == "new-id"
        assert error.context["order_id"] == "new-id"
        assert error.context["extra"] == "data"

    def test_order_error_inherits_from_alchemiser_error(self):
        """Test that OrderError properly inherits from AlchemiserError."""
        error = OrderError("Test error")

        assert isinstance(error, OrderError)
        assert isinstance(error, AlchemiserError)
        assert isinstance(error, Exception)

    def test_order_error_to_dict_method(self):
        """Test that OrderError inherits to_dict() from AlchemiserError."""
        error = OrderError("Test error", order_id="order-789")

        error_dict = error.to_dict()

        assert error_dict["error_type"] == "OrderError"
        assert error_dict["message"] == "Test error"
        assert error_dict["context"]["order_id"] == "order-789"
        assert "timestamp" in error_dict

    def test_order_error_can_be_raised_and_caught(self):
        """Test that OrderError can be raised and caught as exception."""
        with pytest.raises(OrderError) as exc_info:
            raise OrderError("Test exception", order_id="test-order")

        assert exc_info.value.message == "Test exception"
        assert exc_info.value.order_id == "test-order"

    def test_order_error_context_with_complex_data(self):
        """Test OrderError with complex context data types."""
        context = {
            "symbol": "NVDA",
            "quantity": 50.5,
            "price": 875.23,
            "metadata": {"retry_count": 3, "timeout": 30.0},
            "tags": ["high_priority", "urgent"],
        }
        error = OrderError("Complex error", order_id="complex-1", context=context)

        assert error.context["quantity"] == 50.5
        assert error.context["price"] == 875.23
        assert error.context["metadata"]["retry_count"] == 3
        assert "high_priority" in error.context["tags"]


class TestClassifyException:
    """Test classify_exception utility function."""

    def test_classify_order_error(self):
        """Test classification of OrderError exception."""
        error = OrderError("Test order error")

        classification = classify_exception(error)

        assert classification == "order_error"

    def test_classify_alchemiser_error(self):
        """Test classification of AlchemiserError (non-OrderError)."""
        error = AlchemiserError("Generic alchemiser error")

        classification = classify_exception(error)

        assert classification == "alchemiser_error"

    def test_classify_configuration_error(self):
        """Test classification of ConfigurationError (subclass of AlchemiserError)."""
        error = ConfigurationError("Config missing")

        classification = classify_exception(error)

        assert classification == "alchemiser_error"

    def test_classify_order_execution_error(self):
        """Test classification of OrderExecutionError (subclass of AlchemiserError)."""
        error = OrderExecutionError("Execution failed")

        classification = classify_exception(error)

        # OrderExecutionError is AlchemiserError but not OrderError
        assert classification == "alchemiser_error"

    def test_classify_generic_exception(self):
        """Test classification of standard Python exception."""
        error = ValueError("Invalid value")

        classification = classify_exception(error)

        assert classification == "general_error"

    def test_classify_runtime_error(self):
        """Test classification of RuntimeError."""
        error = RuntimeError("Runtime issue")

        classification = classify_exception(error)

        assert classification == "general_error"

    def test_classify_custom_exception(self):
        """Test classification of custom exception not in hierarchy."""
        class CustomError(Exception):
            pass

        error = CustomError("Custom error")

        classification = classify_exception(error)

        assert classification == "general_error"

    def test_classify_exception_type_checking_order(self):
        """Test that isinstance checks happen in correct order."""
        # OrderError should match before AlchemiserError
        error = OrderError("Test")
        assert classify_exception(error) == "order_error"

        # Non-OrderError AlchemiserError should match second
        error = AlchemiserError("Test")
        assert classify_exception(error) == "alchemiser_error"

        # Other exceptions should match last
        error = Exception("Test")
        assert classify_exception(error) == "general_error"


class TestOrderErrorIntegration:
    """Integration tests for OrderError with error handling patterns."""

    def test_order_error_in_try_except_block(self):
        """Test OrderError in typical try-except error handling."""
        order_id = "integration-test-001"

        try:
            # Simulate order failure
            raise OrderError("Order timeout", order_id=order_id)
        except OrderError as e:
            assert e.order_id == order_id
            assert "Order timeout" in str(e)
            classification = classify_exception(e)
            assert classification == "order_error"

    def test_order_error_context_preservation(self):
        """Test that context is preserved through exception handling."""
        context = {"symbol": "AAPL", "attempt": 3}

        try:
            raise OrderError("Retry exhausted", order_id="retry-001", context=context)
        except OrderError as e:
            assert e.context["symbol"] == "AAPL"
            assert e.context["attempt"] == 3
            assert e.context["order_id"] == "retry-001"

    def test_multiple_error_types_in_except_chain(self):
        """Test handling multiple error types including OrderError."""

        def process_order(order_type: str):
            if order_type == "order":
                raise OrderError("Order failed", order_id="test-order")
            elif order_type == "config":
                raise ConfigurationError("Config invalid")
            else:
                raise ValueError("Invalid type")

        # Test OrderError path
        try:
            process_order("order")
        except OrderError as e:
            assert classify_exception(e) == "order_error"

        # Test ConfigurationError path
        try:
            process_order("config")
        except ConfigurationError as e:
            assert classify_exception(e) == "alchemiser_error"

        # Test general exception path
        try:
            process_order("unknown")
        except ValueError as e:
            assert classify_exception(e) == "general_error"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_order_error_empty_string_message(self):
        """Test OrderError with empty string message."""
        error = OrderError("")

        assert error.message == ""
        assert str(error) == ""

    def test_order_error_empty_order_id(self):
        """Test OrderError with empty string order_id."""
        error = OrderError("Test", order_id="")

        # Empty string is falsy, so it should not be added to context
        assert error.order_id == ""
        assert "order_id" not in error.context

    def test_order_error_none_order_id_explicit(self):
        """Test OrderError with explicitly passed None order_id."""
        error = OrderError("Test", order_id=None)

        assert error.order_id is None
        assert "order_id" not in error.context

    def test_order_error_context_empty_dict(self):
        """Test OrderError with explicitly passed empty dict."""
        error = OrderError("Test", context={})

        assert error.context == {}
        assert isinstance(error.context, dict)

    def test_classify_exception_with_deeply_nested_inheritance(self):
        """Test classification with deep exception inheritance chain."""

        class Level1(AlchemiserError):
            pass

        class Level2(Level1):
            pass

        class Level3(Level2):
            pass

        error = Level3("Deep error")
        classification = classify_exception(error)

        # Should classify as alchemiser_error due to inheritance
        assert classification == "alchemiser_error"

    def test_order_error_with_special_characters_in_message(self):
        """Test OrderError with special characters and unicode."""
        message = "Order failed: 'AAPL' → $100.50 × 10 shares ✗"
        error = OrderError(message, order_id="unicode-test")

        assert error.message == message
        assert message in str(error)
