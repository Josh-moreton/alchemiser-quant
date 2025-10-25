"""Business Unit: shared | Status: current.

Tests for error handler module covering error handling and tracking.
"""

from the_alchemiser.shared.errors.error_handler import (
    TradingSystemErrorHandler,
)
from the_alchemiser.shared.errors.error_types import ErrorCategory
from the_alchemiser.shared.errors.exceptions import (
    ConfigurationError,
    InsufficientFundsError,
    MarketDataError,
    OrderExecutionError,
)


class TestTradingSystemErrorHandler:
    """Test TradingSystemErrorHandler class."""

    def test_create_error_handler(self):
        """Test creating error handler."""
        handler = TradingSystemErrorHandler()
        assert handler is not None
        assert handler.errors == []

    def test_categorize_error_trading(self):
        """Test error categorization for trading errors."""
        handler = TradingSystemErrorHandler()
        error = InsufficientFundsError("Not enough funds")
        category = handler.categorize_error(error, "order placement")
        assert category == ErrorCategory.TRADING

    def test_categorize_error_data(self):
        """Test error categorization for data errors."""
        handler = TradingSystemErrorHandler()
        error = MarketDataError("Data unavailable")
        category = handler.categorize_error(error, "data fetch")
        assert category == ErrorCategory.DATA

    def test_categorize_error_configuration(self):
        """Test error categorization for configuration errors."""
        handler = TradingSystemErrorHandler()
        error = ConfigurationError("Invalid config")
        category = handler.categorize_error(error, "config load")
        assert category == ErrorCategory.CONFIGURATION

    def test_get_suggested_action(self):
        """Test getting suggested action for errors."""
        handler = TradingSystemErrorHandler()
        error = InsufficientFundsError("Not enough funds")
        action = handler.get_suggested_action(error, ErrorCategory.TRADING)
        assert isinstance(action, str)
        assert len(action) > 0


class TestTradingSystemErrorHandlerHandleError:
    """Test handle_error method."""

    def test_handle_error_basic(self):
        """Test basic error handling."""
        handler = TradingSystemErrorHandler()
        error = OrderExecutionError("Order failed")

        error_details = handler.handle_error(
            error=error,
            context="order execution",
            component="execution_v2",
        )

        assert error_details is not None
        assert error_details.error == error
        assert error_details.context == "order execution"
        assert error_details.component == "execution_v2"
        assert len(handler.errors) == 1

    def test_handle_error_with_additional_data(self):
        """Test error handling with additional data."""
        handler = TradingSystemErrorHandler()
        error = InsufficientFundsError("Insufficient funds")
        additional = {"symbol": "AAPL", "quantity": 100}

        error_details = handler.handle_error(
            error=error,
            context="order placement",
            component="execution_v2",
            additional_data=additional,
        )

        assert error_details.additional_data == additional
        assert error_details.additional_data["symbol"] == "AAPL"

    def test_handle_error_maps_to_error_code(self):
        """Test that handle_error maps exception to error code."""
        handler = TradingSystemErrorHandler()
        error = InsufficientFundsError("Not enough funds")

        error_details = handler.handle_error(
            error=error,
            context="trading",
            component="execution_v2",
        )

        assert error_details.error_code is not None
        assert error_details.error_code == "TRD_INSUFFICIENT_FUNDS"

    def test_handle_error_unknown_exception_no_code(self):
        """Test that unknown exceptions have no error code."""
        handler = TradingSystemErrorHandler()
        error = ValueError("Unknown error")

        error_details = handler.handle_error(
            error=error,
            context="unknown operation",
            component="test",
        )

        assert error_details.error_code is None

    def test_handle_error_tracks_history(self):
        """Test that errors are tracked in history."""
        handler = TradingSystemErrorHandler()

        # Handle multiple errors
        error1 = OrderExecutionError("Order 1 failed")
        error2 = OrderExecutionError("Order 2 failed")
        error3 = MarketDataError("Data unavailable")

        handler.handle_error(error1, "order 1", "execution")
        handler.handle_error(error2, "order 2", "execution")
        handler.handle_error(error3, "data fetch", "data_provider")

        assert len(handler.errors) == 3
        assert handler.errors[0].error == error1
        assert handler.errors[1].error == error2
        assert handler.errors[2].error == error3

    def test_handle_error_categorization(self):
        """Test that handle_error correctly categorizes errors."""
        handler = TradingSystemErrorHandler()

        error = InsufficientFundsError("Not enough funds")
        error_details = handler.handle_error(
            error=error,
            context="order placement",
            component="execution_v2",
        )

        assert error_details.category == ErrorCategory.TRADING

    def test_handle_error_suggested_action(self):
        """Test that handle_error provides suggested action."""
        handler = TradingSystemErrorHandler()

        error = InsufficientFundsError("Not enough funds")
        error_details = handler.handle_error(
            error=error,
            context="order placement",
            component="execution_v2",
        )

        assert error_details.suggested_action is not None
        assert "balance" in error_details.suggested_action.lower()


class TestTradingSystemErrorHandlerIntegration:
    """Test integration scenarios for error handler."""

    def test_multiple_error_types(self):
        """Test handling multiple different error types."""
        handler = TradingSystemErrorHandler()

        errors = [
            (InsufficientFundsError("No funds"), "trading"),
            (MarketDataError("No data"), "data"),
            (ConfigurationError("Bad config"), "config"),
        ]

        for error, context in errors:
            handler.handle_error(error, context, "test_component")

        assert len(handler.errors) == 3
        assert handler.errors[0].category == ErrorCategory.TRADING
        assert handler.errors[1].category == ErrorCategory.DATA
        assert handler.errors[2].category == ErrorCategory.CONFIGURATION

    def test_error_details_serialization(self):
        """Test that error details can be serialized."""
        handler = TradingSystemErrorHandler()
        error = OrderExecutionError("Order failed")

        error_details = handler.handle_error(
            error=error,
            context="order execution",
            component="execution_v2",
            additional_data={"order_id": "123", "symbol": "AAPL"},
        )

        # Should be serializable
        serialized = error_details.to_dict()
        assert isinstance(serialized, dict)
        assert serialized["error_type"] == "OrderExecutionError"
        assert serialized["context"] == "order execution"
        assert serialized["additional_data"]["order_id"] == "123"
