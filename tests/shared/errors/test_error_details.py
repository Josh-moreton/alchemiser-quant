"""Business Unit: shared | Status: current.

Tests for error details and categorization logic.
"""

from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from the_alchemiser.shared.errors.error_details import (
    ErrorDetails,
    categorize_by_context,
    categorize_by_exception_type,
    categorize_error,
    get_suggested_action,
)
from the_alchemiser.shared.errors.error_types import ErrorCategory
from the_alchemiser.shared.errors.exceptions import (
    ConfigurationError,
    DataProviderError,
    InsufficientFundsError,
    MarketDataError,
    NotificationError,
    OrderExecutionError,
    PositionValidationError,
    TradingClientError,
)


class TestErrorDetails:
    """Test ErrorDetails class."""

    def test_create_error_details(self):
        """Test creating ErrorDetails with required fields."""
        error = ValueError("Test error")
        details = ErrorDetails(
            error=error,
            category=ErrorCategory.CRITICAL,
            context="test context",
            component="test_component",
        )
        assert details.error == error
        assert details.category == ErrorCategory.CRITICAL
        assert details.context == "test context"
        assert details.component == "test_component"
        assert isinstance(details.timestamp, datetime)
        assert details.additional_data == {}

    def test_create_error_details_with_additional_data(self):
        """Test creating ErrorDetails with additional data."""
        error = RuntimeError("Runtime error")
        additional = {"key": "value", "count": 42}
        details = ErrorDetails(
            error=error,
            category=ErrorCategory.DATA,
            context="data fetch",
            component="data_provider",
            additional_data=additional,
        )
        assert details.additional_data == additional

    def test_create_error_details_with_suggested_action(self):
        """Test creating ErrorDetails with suggested action."""
        error = Exception("Test")
        details = ErrorDetails(
            error=error,
            category=ErrorCategory.TRADING,
            context="order execution",
            component="execution_v2",
            suggested_action="Retry with backoff",
        )
        assert details.suggested_action == "Retry with backoff"

    def test_create_error_details_with_error_code(self):
        """Test creating ErrorDetails with error code."""
        error = Exception("Test")
        details = ErrorDetails(
            error=error,
            category=ErrorCategory.CONFIGURATION,
            context="config load",
            component="config_loader",
            error_code="CONF_MISSING_ENV",
        )
        assert details.error_code == "CONF_MISSING_ENV"

    def test_error_details_captures_traceback(self):
        """Test that ErrorDetails captures traceback."""
        error = ValueError("Test error")
        details = ErrorDetails(
            error=error,
            category=ErrorCategory.CRITICAL,
            context="test",
            component="test",
        )
        assert isinstance(details.traceback, str)
        assert len(details.traceback) > 0


class TestErrorDetailsToDict:
    """Test ErrorDetails.to_dict() method."""

    def test_to_dict_basic(self):
        """Test to_dict with basic error details."""
        error = ValueError("Test error")
        details = ErrorDetails(
            error=error,
            category=ErrorCategory.DATA,
            context="data processing",
            component="processor",
        )
        result = details.to_dict()

        assert result["error_type"] == "ValueError"
        assert result["error_message"] == "Test error"
        assert result["category"] == ErrorCategory.DATA
        assert result["context"] == "data processing"
        assert result["component"] == "processor"
        assert "timestamp" in result
        assert "traceback" in result

    def test_to_dict_with_all_fields(self):
        """Test to_dict with all optional fields."""
        error = RuntimeError("Runtime error")
        details = ErrorDetails(
            error=error,
            category=ErrorCategory.TRADING,
            context="order placement",
            component="execution_v2",
            additional_data={"order_id": "123", "symbol": "AAPL"},
            suggested_action="Check market hours",
            error_code="TRD_MARKET_CLOSED",
        )
        result = details.to_dict()

        assert result["error_type"] == "RuntimeError"
        assert result["additional_data"]["order_id"] == "123"
        assert result["suggested_action"] == "Check market hours"
        assert result["error_code"] == "TRD_MARKET_CLOSED"

    def test_to_dict_timestamp_is_iso_format(self):
        """Test that timestamp is in ISO format."""
        error = Exception("Test")
        details = ErrorDetails(
            error=error,
            category=ErrorCategory.CRITICAL,
            context="test",
            component="test",
        )
        result = details.to_dict()
        # Should be parseable as ISO datetime
        parsed = datetime.fromisoformat(result["timestamp"])
        assert isinstance(parsed, datetime)

    def test_to_dict_includes_schema_version(self):
        """Test that to_dict includes schema_version field."""
        error = ValueError("Test error")
        details = ErrorDetails(
            error=error,
            category=ErrorCategory.DATA,
            context="test",
            component="test",
        )
        result = details.to_dict()
        assert "schema_version" in result
        assert result["schema_version"] == "1.0"


class TestErrorDetailsImmutability:
    """Test ErrorDetails immutability (frozen dataclass)."""

    def test_error_details_is_immutable(self):
        """Test that ErrorDetails instances cannot be modified after creation."""
        error = ValueError("Test error")
        details = ErrorDetails(
            error=error,
            category=ErrorCategory.CRITICAL,
            context="test",
            component="test",
        )
        # Attempting to modify should raise FrozenInstanceError
        with pytest.raises(Exception):  # dataclasses.FrozenInstanceError
            details.category = "new_category"  # type: ignore[misc]

    def test_error_details_additional_data_default_is_not_shared(self):
        """Test that default additional_data is not shared between instances."""
        error1 = ValueError("Error 1")
        details1 = ErrorDetails(
            error=error1,
            category=ErrorCategory.DATA,
            context="test1",
            component="test",
        )

        error2 = ValueError("Error 2")
        details2 = ErrorDetails(
            error=error2,
            category=ErrorCategory.DATA,
            context="test2",
            component="test",
        )

        # Both should have empty dicts, but they should be different instances
        assert details1.additional_data == {}
        assert details2.additional_data == {}
        # Since ErrorDetails is frozen, we can't modify, but we can verify they're independent
        assert details1.additional_data is not details2.additional_data


class TestCategorizeByExceptionType:
    """Test categorize_by_exception_type function."""

    def test_categorize_insufficient_funds_error(self):
        """Test categorization of InsufficientFundsError."""
        error = InsufficientFundsError("Not enough funds")
        result = categorize_by_exception_type(error)
        assert result == ErrorCategory.TRADING

    def test_categorize_order_execution_error(self):
        """Test categorization of OrderExecutionError."""
        error = OrderExecutionError("Order failed")
        result = categorize_by_exception_type(error)
        assert result == ErrorCategory.TRADING

    def test_categorize_position_validation_error(self):
        """Test categorization of PositionValidationError."""
        error = PositionValidationError("Invalid position")
        result = categorize_by_exception_type(error)
        assert result == ErrorCategory.TRADING

    def test_categorize_market_data_error(self):
        """Test categorization of MarketDataError."""
        error = MarketDataError("Data unavailable")
        result = categorize_by_exception_type(error)
        assert result == ErrorCategory.DATA

    def test_categorize_data_provider_error(self):
        """Test categorization of DataProviderError."""
        error = DataProviderError("Provider failed")
        result = categorize_by_exception_type(error)
        assert result == ErrorCategory.DATA

    def test_categorize_configuration_error(self):
        """Test categorization of ConfigurationError."""
        error = ConfigurationError("Invalid config")
        result = categorize_by_exception_type(error)
        assert result == ErrorCategory.CONFIGURATION

    def test_categorize_notification_error(self):
        """Test categorization of NotificationError."""
        error = NotificationError("Email failed")
        result = categorize_by_exception_type(error)
        assert result == ErrorCategory.NOTIFICATION

    def test_categorize_strategy_execution_error(self):
        """Test categorization of StrategyExecutionError by name."""
        # Create a mock exception with the right class name
        class StrategyExecutionError(Exception):
            pass

        error = StrategyExecutionError("Strategy failed")
        result = categorize_by_exception_type(error)
        assert result == ErrorCategory.STRATEGY

    def test_categorize_unknown_error_returns_none(self):
        """Test that unknown errors return None."""
        error = ValueError("Unknown error")
        result = categorize_by_exception_type(error)
        assert result is None


class TestCategorizeByContext:
    """Test categorize_by_context function."""

    def test_categorize_trading_context(self):
        """Test categorization with 'trading' keyword."""
        result = categorize_by_context("trading operation failed")
        assert result == ErrorCategory.TRADING

    def test_categorize_order_context(self):
        """Test categorization with 'order' keyword."""
        result = categorize_by_context("order placement failed")
        assert result == ErrorCategory.TRADING

    def test_categorize_data_context(self):
        """Test categorization with 'data' keyword."""
        result = categorize_by_context("data fetch failed")
        assert result == ErrorCategory.DATA

    def test_categorize_price_context(self):
        """Test categorization with 'price' keyword."""
        result = categorize_by_context("price retrieval failed")
        assert result == ErrorCategory.DATA

    def test_categorize_strategy_context(self):
        """Test categorization with 'strategy' keyword."""
        result = categorize_by_context("strategy calculation failed")
        assert result == ErrorCategory.STRATEGY

    def test_categorize_signal_context(self):
        """Test categorization with 'signal' keyword."""
        result = categorize_by_context("signal generation failed")
        assert result == ErrorCategory.STRATEGY

    def test_categorize_config_context(self):
        """Test categorization with 'config' keyword."""
        result = categorize_by_context("config loading failed")
        assert result == ErrorCategory.CONFIGURATION

    def test_categorize_auth_context(self):
        """Test categorization with 'auth' keyword."""
        result = categorize_by_context("auth validation failed")
        assert result == ErrorCategory.CONFIGURATION

    def test_categorize_unknown_context(self):
        """Test categorization with unknown context defaults to CRITICAL."""
        result = categorize_by_context("unknown operation failed")
        assert result == ErrorCategory.CRITICAL

    def test_categorize_case_insensitive(self):
        """Test that categorization is case-insensitive."""
        result1 = categorize_by_context("TRADING failed")
        result2 = categorize_by_context("Trading failed")
        result3 = categorize_by_context("trading failed")
        assert result1 == result2 == result3 == ErrorCategory.TRADING


class TestCategorizeError:
    """Test categorize_error function with priority logic."""

    def test_categorize_by_exception_type_first(self):
        """Test that exception type takes priority over context."""
        error = InsufficientFundsError("Not enough funds")
        # Context suggests DATA, but exception type should win
        result = categorize_error(error, "data fetch failed")
        assert result == ErrorCategory.TRADING

    def test_categorize_trading_client_error_with_order_context(self):
        """Test TradingClientError categorized as CRITICAL (AlchemiserError subclass)."""
        error = TradingClientError("Client error")
        result = categorize_error(error, "order placement failed")
        # TradingClientError is AlchemiserError, so it's categorized as CRITICAL
        assert result == ErrorCategory.CRITICAL

    def test_categorize_trading_client_error_with_position_context(self):
        """Test TradingClientError categorized as CRITICAL (AlchemiserError subclass)."""
        error = TradingClientError("Client error")
        result = categorize_error(error, "position validation failed")
        # TradingClientError is AlchemiserError, so it's categorized as CRITICAL
        assert result == ErrorCategory.CRITICAL

    def test_categorize_trading_client_error_without_trading_context(self):
        """Test TradingClientError categorized as CRITICAL (AlchemiserError subclass)."""
        error = TradingClientError("Client error")
        result = categorize_error(error, "data fetch failed")
        # TradingClientError is AlchemiserError, so it's categorized as CRITICAL
        assert result == ErrorCategory.CRITICAL

    def test_categorize_unknown_exception_by_context(self):
        """Test that unknown exceptions fall back to context."""
        error = ValueError("Unknown error")
        result = categorize_error(error, "strategy calculation failed")
        assert result == ErrorCategory.STRATEGY

    def test_categorize_error_no_context(self):
        """Test categorization with empty context."""
        error = ValueError("Unknown error")
        result = categorize_error(error, "")
        assert result == ErrorCategory.CRITICAL


class TestGetSuggestedAction:
    """Test get_suggested_action function."""

    def test_suggested_action_for_insufficient_funds(self):
        """Test suggested action for InsufficientFundsError."""
        error = InsufficientFundsError("Not enough funds")
        action = get_suggested_action(error, ErrorCategory.TRADING)
        assert "balance" in action.lower() or "funds" in action.lower()

    def test_suggested_action_for_order_execution_error(self):
        """Test suggested action for OrderExecutionError."""
        error = OrderExecutionError("Order failed")
        action = get_suggested_action(error, ErrorCategory.TRADING)
        assert "market hours" in action.lower() or "order" in action.lower()

    def test_suggested_action_for_position_validation_error(self):
        """Test suggested action for PositionValidationError."""
        error = PositionValidationError("Invalid position")
        action = get_suggested_action(error, ErrorCategory.TRADING)
        assert "position" in action.lower()

    def test_suggested_action_for_market_data_error(self):
        """Test suggested action for MarketDataError."""
        error = MarketDataError("Data unavailable")
        action = get_suggested_action(error, ErrorCategory.DATA)
        assert "api" in action.lower() or "data" in action.lower()

    def test_suggested_action_for_configuration_error(self):
        """Test suggested action for ConfigurationError."""
        error = ConfigurationError("Invalid config")
        action = get_suggested_action(error, ErrorCategory.CONFIGURATION)
        assert "config" in action.lower() or "credential" in action.lower()

    def test_suggested_action_for_strategy_execution_error(self):
        """Test suggested action for StrategyExecutionError."""

        class StrategyExecutionError(Exception):
            pass

        error = StrategyExecutionError("Strategy failed")
        action = get_suggested_action(error, ErrorCategory.STRATEGY)
        assert "strategy" in action.lower()

    def test_suggested_action_for_data_category(self):
        """Test suggested action for DATA category."""
        error = Exception("Unknown error")
        action = get_suggested_action(error, ErrorCategory.DATA)
        assert "data" in action.lower() or "api" in action.lower()

    def test_suggested_action_for_trading_category(self):
        """Test suggested action for TRADING category."""
        error = Exception("Unknown error")
        action = get_suggested_action(error, ErrorCategory.TRADING)
        assert "trading" in action.lower() or "permission" in action.lower()

    def test_suggested_action_for_critical_category(self):
        """Test suggested action for CRITICAL category."""
        error = Exception("Unknown error")
        action = get_suggested_action(error, ErrorCategory.CRITICAL)
        assert "log" in action.lower() or "system" in action.lower()

    def test_suggested_action_for_unknown_category(self):
        """Test suggested action for unknown category."""
        error = Exception("Unknown error")
        action = get_suggested_action(error, "unknown_category")
        assert "log" in action.lower() or "support" in action.lower()


class TestErrorDetailsIntegration:
    """Test integration scenarios for error details."""

    def test_full_error_workflow(self):
        """Test complete error handling workflow."""
        # Create an error
        error = InsufficientFundsError("Account balance too low")

        # Categorize it
        category = categorize_error(error, "order placement")
        assert category == ErrorCategory.TRADING

        # Get suggested action
        action = get_suggested_action(error, category)
        assert "balance" in action.lower()

        # Create error details
        details = ErrorDetails(
            error=error,
            category=category,
            context="order placement",
            component="execution_v2",
            additional_data={"symbol": "AAPL", "quantity": 100},
            suggested_action=action,
            error_code="TRD_INSUFFICIENT_FUNDS",
        )

        # Serialize
        result = details.to_dict()
        assert result["category"] == ErrorCategory.TRADING
        assert result["error_code"] == "TRD_INSUFFICIENT_FUNDS"
        assert result["additional_data"]["symbol"] == "AAPL"
