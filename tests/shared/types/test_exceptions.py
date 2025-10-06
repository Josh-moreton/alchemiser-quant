"""Business Unit: shared | Status: current.

Comprehensive tests for exception hierarchy in shared.types.exceptions.

This test suite validates the exception classes defined in the base
exception module, ensuring correct initialization, context handling,
and inheritance patterns.
"""

import pytest
from datetime import datetime, UTC
from decimal import Decimal

from the_alchemiser.shared.types.exceptions import (
    AlchemiserError,
    ConfigurationError,
    DataProviderError,
    TradingClientError,
    OrderExecutionError,
    OrderPlacementError,
    OrderTimeoutError,
    SpreadAnalysisError,
    BuyingPowerError,
    InsufficientFundsError,
    PositionValidationError,
    PortfolioError,
    NegativeCashBalanceError,
    IndicatorCalculationError,
    MarketDataError,
    ValidationError,
    NotificationError,
    S3OperationError,
    RateLimitError,
    MarketClosedError,
    WebSocketError,
    StreamingError,
    LoggingError,
    FileOperationError,
    DatabaseError,
    SecurityError,
    EnvironmentError,
    StrategyExecutionError,
    StrategyValidationError,
)


class TestAlchemiserErrorBase:
    """Test AlchemiserError base exception class."""

    def test_basic_initialization(self):
        """Test basic error initialization with message only."""
        error = AlchemiserError("Test error message")

        assert str(error) == "Test error message"
        assert error.message == "Test error message"
        assert error.context == {}
        assert error.correlation_id is None
        assert isinstance(error.timestamp, datetime)
        assert error.timestamp.tzinfo == UTC

    def test_initialization_with_context(self):
        """Test error initialization with context dict."""
        context = {"key": "value", "count": 42}
        error = AlchemiserError("Test error", context=context)

        assert error.message == "Test error"
        assert error.context == context
        assert error.context["key"] == "value"
        assert error.context["count"] == 42
        assert error.correlation_id is None

    def test_initialization_with_correlation_id(self):
        """Test error initialization with correlation_id."""
        error = AlchemiserError("Test error", correlation_id="corr-123")

        assert error.message == "Test error"
        assert error.correlation_id == "corr-123"
        assert error.context["correlation_id"] == "corr-123"

    def test_initialization_with_context_and_correlation_id(self):
        """Test error initialization with both context and correlation_id."""
        context = {"key": "value"}
        error = AlchemiserError("Test error", context=context, correlation_id="corr-456")

        assert error.message == "Test error"
        assert error.context["key"] == "value"
        assert error.context["correlation_id"] == "corr-456"
        assert error.correlation_id == "corr-456"

    def test_initialization_with_none_context(self):
        """Test error initialization with None context creates empty dict."""
        error = AlchemiserError("Test error", context=None)

        assert error.context == {}
        assert isinstance(error.context, dict)

    def test_to_dict_serialization(self):
        """Test to_dict() serialization method."""
        context = {"symbol": "AAPL", "quantity": 100}
        error = AlchemiserError("Test error", context=context)

        result = error.to_dict()

        assert result["error_type"] == "AlchemiserError"
        assert result["message"] == "Test error"
        assert result["context"] == context
        assert "timestamp" in result
        assert isinstance(result["timestamp"], str)  # ISO format

    def test_timestamp_is_utc_aware(self):
        """Test that timestamp is timezone-aware and in UTC."""
        error = AlchemiserError("Test error")

        assert error.timestamp.tzinfo is not None
        assert error.timestamp.tzinfo == UTC

    def test_can_be_raised_and_caught(self):
        """Test that error can be raised and caught as exception."""
        with pytest.raises(AlchemiserError) as exc_info:
            raise AlchemiserError("Test exception")

        assert exc_info.value.message == "Test exception"
        assert isinstance(exc_info.value, Exception)


class TestConfigurationError:
    """Test ConfigurationError exception class."""

    def test_basic_initialization(self):
        """Test basic initialization with message only."""
        error = ConfigurationError("Config missing")

        assert error.message == "Config missing"
        assert error.config_key is None
        assert error.config_value is None
        assert error.context == {}

    def test_initialization_with_config_key(self):
        """Test initialization with config_key."""
        error = ConfigurationError("Invalid config", config_key="API_KEY")

        assert error.config_key == "API_KEY"
        assert error.context["config_key"] == "API_KEY"
        assert "config_value" not in error.context

    def test_initialization_with_config_value(self):
        """Test initialization with config_value."""
        error = ConfigurationError("Bad value", config_key="timeout", config_value=30)

        assert error.config_key == "timeout"
        assert error.config_value == 30
        assert error.context["config_key"] == "timeout"
        assert error.context["config_value"] == "30"  # Converted to string

    def test_config_value_string_conversion(self):
        """Test that config_value is converted to string for safety."""
        # Test with different types
        error = ConfigurationError("Test", config_value=42.5)
        assert error.context["config_value"] == "42.5"

        error = ConfigurationError("Test", config_value=True)
        assert error.context["config_value"] == "True"

    def test_inherits_from_alchemiser_error(self):
        """Test inheritance chain."""
        error = ConfigurationError("Test")

        assert isinstance(error, ConfigurationError)
        assert isinstance(error, AlchemiserError)
        assert isinstance(error, Exception)


class TestDataProviderError:
    """Test DataProviderError exception class."""

    def test_basic_initialization(self):
        """Test basic initialization."""
        error = DataProviderError("Data fetch failed")

        assert error.message == "Data fetch failed"
        assert isinstance(error, AlchemiserError)

    def test_inherits_from_alchemiser_error(self):
        """Test inheritance chain."""
        error = DataProviderError("Test")

        assert isinstance(error, DataProviderError)
        assert isinstance(error, AlchemiserError)


class TestTradingClientError:
    """Test TradingClientError exception class."""

    def test_basic_initialization(self):
        """Test basic initialization."""
        error = TradingClientError("Trading operation failed")

        assert error.message == "Trading operation failed"
        assert isinstance(error, AlchemiserError)

    def test_inherits_from_alchemiser_error(self):
        """Test inheritance chain."""
        error = TradingClientError("Test")

        assert isinstance(error, TradingClientError)
        assert isinstance(error, AlchemiserError)


class TestOrderExecutionError:
    """Test OrderExecutionError exception class."""

    def test_basic_initialization(self):
        """Test basic initialization with message only."""
        error = OrderExecutionError("Order failed")

        assert error.message == "Order failed"
        assert error.symbol is None
        assert error.order_type is None
        assert error.order_id is None
        assert error.quantity is None
        assert error.price is None
        assert error.account_id is None
        assert error.retry_count == 0

    def test_initialization_with_all_parameters(self):
        """Test initialization with all parameters."""
        error = OrderExecutionError(
            "Order execution failed",
            symbol="AAPL",
            order_type="limit",
            order_id="ord-123",
            quantity=Decimal("100.0"),
            price=Decimal("150.50"),
            account_id="acc-456",
            retry_count=3,
            correlation_id="corr-789",
        )

        assert error.symbol == "AAPL"
        assert error.order_type == "limit"
        assert error.order_id == "ord-123"
        assert error.quantity == Decimal("100.0")
        assert error.price == Decimal("150.50")
        assert error.account_id == "acc-456"
        assert error.retry_count == 3
        assert error.correlation_id == "corr-789"

    def test_context_dict_population(self):
        """Test that context dict is properly populated."""
        error = OrderExecutionError(
            "Test",
            symbol="TSLA",
            order_type="market",
            order_id="ord-789",
            quantity=Decimal("50.0"),
            price=Decimal("200.0"),
            account_id="acc-111",
            retry_count=2,
        )

        assert error.context["symbol"] == "TSLA"
        assert error.context["order_type"] == "market"
        assert error.context["order_id"] == "ord-789"
        assert error.context["quantity"] == "50.0"
        assert error.context["price"] == "200.0"
        assert error.context["account_id"] == "acc-111"
        assert error.context["retry_count"] == 2

    def test_none_values_not_in_context(self):
        """Test that None values are not added to context."""
        error = OrderExecutionError("Test", symbol="AAPL")

        assert "symbol" in error.context
        assert "order_type" not in error.context
        assert "order_id" not in error.context
        assert "quantity" not in error.context
        assert "retry_count" not in error.context  # Zero is not added

    def test_inherits_from_trading_client_error(self):
        """Test inheritance chain."""
        error = OrderExecutionError("Test")

        assert isinstance(error, OrderExecutionError)
        assert isinstance(error, TradingClientError)
        assert isinstance(error, AlchemiserError)


class TestOrderPlacementError:
    """Test OrderPlacementError exception class."""

    def test_basic_initialization(self):
        """Test basic initialization."""
        error = OrderPlacementError("Placement failed")

        assert error.message == "Placement failed"
        assert error.reason is None

    def test_initialization_with_reason(self):
        """Test initialization with reason parameter."""
        error = OrderPlacementError(
            "Order rejected",
            symbol="AAPL",
            order_type="limit",
            quantity=Decimal("100.0"),
            price=Decimal("150.0"),
            reason="insufficient_funds",
        )

        assert error.reason == "insufficient_funds"
        assert error.symbol == "AAPL"
        assert error.context["reason"] == "insufficient_funds"

    def test_inherits_from_order_execution_error(self):
        """Test inheritance chain."""
        error = OrderPlacementError("Test")

        assert isinstance(error, OrderPlacementError)
        assert isinstance(error, OrderExecutionError)
        assert isinstance(error, TradingClientError)


class TestOrderTimeoutError:
    """Test OrderTimeoutError exception class."""

    def test_basic_initialization(self):
        """Test basic initialization."""
        error = OrderTimeoutError("Order timed out")

        assert error.message == "Order timed out"
        assert error.timeout_seconds is None
        assert error.attempt_number is None

    def test_initialization_with_timeout_info(self):
        """Test initialization with timeout parameters."""
        error = OrderTimeoutError(
            "Timeout during execution",
            symbol="NVDA",
            order_id="ord-999",
            timeout_seconds=30.0,
            attempt_number=3,
        )

        assert error.timeout_seconds == 30.0
        assert error.attempt_number == 3
        assert error.symbol == "NVDA"
        assert error.order_id == "ord-999"

    def test_inherits_from_order_execution_error(self):
        """Test inheritance chain."""
        error = OrderTimeoutError("Test")

        assert isinstance(error, OrderTimeoutError)
        assert isinstance(error, OrderExecutionError)


class TestPortfolioError:
    """Test PortfolioError exception class."""

    def test_basic_initialization(self):
        """Test basic initialization."""
        error = PortfolioError("Portfolio operation failed")

        assert error.message == "Portfolio operation failed"
        assert error.module is None
        assert error.operation is None
        assert error.correlation_id is None

    def test_initialization_with_all_context(self):
        """Test initialization with all context parameters."""
        error = PortfolioError(
            "Rebalance failed",
            module="portfolio_v2",
            operation="rebalance",
            correlation_id="corr-123",
        )

        assert error.module == "portfolio_v2"
        assert error.operation == "rebalance"
        assert error.correlation_id == "corr-123"
        assert error.context["module"] == "portfolio_v2"
        assert error.context["operation"] == "rebalance"
        assert error.context["correlation_id"] == "corr-123"

    def test_inherits_from_alchemiser_error(self):
        """Test inheritance chain."""
        error = PortfolioError("Test")

        assert isinstance(error, PortfolioError)
        assert isinstance(error, AlchemiserError)


class TestStrategyExecutionError:
    """Test StrategyExecutionError exception class."""

    def test_basic_initialization(self):
        """Test basic initialization."""
        error = StrategyExecutionError("Strategy failed")

        assert error.message == "Strategy failed"
        assert error.strategy_name is None
        assert error.symbol is None
        assert error.operation is None

    def test_initialization_with_context(self):
        """Test initialization with context parameters."""
        error = StrategyExecutionError(
            "Signal generation failed",
            strategy_name="momentum",
            symbol="AAPL",
            operation="generate_signal",
        )

        assert error.strategy_name == "momentum"
        assert error.symbol == "AAPL"
        assert error.operation == "generate_signal"
        assert error.context["strategy_name"] == "momentum"
        assert error.context["symbol"] == "AAPL"
        assert error.context["operation"] == "generate_signal"

    def test_inherits_from_alchemiser_error(self):
        """Test inheritance chain."""
        error = StrategyExecutionError("Test")

        assert isinstance(error, StrategyExecutionError)
        assert isinstance(error, AlchemiserError)


class TestRateLimitError:
    """Test RateLimitError exception class."""

    def test_basic_initialization(self):
        """Test basic initialization."""
        error = RateLimitError("Rate limit exceeded")

        assert error.message == "Rate limit exceeded"
        assert error.retry_after is None

    def test_initialization_with_retry_after(self):
        """Test initialization with retry_after parameter."""
        error = RateLimitError("Rate limited", retry_after=60)

        assert error.retry_after == 60

    def test_inherits_from_alchemiser_error(self):
        """Test inheritance chain."""
        error = RateLimitError("Test")

        assert isinstance(error, RateLimitError)
        assert isinstance(error, AlchemiserError)


class TestFileOperationError:
    """Test FileOperationError exception class."""

    def test_basic_initialization(self):
        """Test basic initialization."""
        error = FileOperationError("File operation failed")

        assert error.message == "File operation failed"
        assert error.file_path is None
        assert error.operation is None

    def test_initialization_with_parameters(self):
        """Test initialization with file_path and operation."""
        error = FileOperationError(
            "Read failed",
            file_path="/tmp/data.csv",
            operation="read",
        )

        assert error.file_path == "/tmp/data.csv"
        assert error.operation == "read"


class TestDatabaseError:
    """Test DatabaseError exception class."""

    def test_basic_initialization(self):
        """Test basic initialization."""
        error = DatabaseError("Database operation failed")

        assert error.message == "Database operation failed"
        assert error.table_name is None
        assert error.operation is None

    def test_initialization_with_parameters(self):
        """Test initialization with table_name and operation."""
        error = DatabaseError(
            "Insert failed",
            table_name="trades",
            operation="insert",
        )

        assert error.table_name == "trades"
        assert error.operation == "insert"


class TestEmptyExceptionClasses:
    """Test exception classes with no custom initialization."""

    def test_insufficient_funds_error(self):
        """Test InsufficientFundsError."""
        error = InsufficientFundsError("Insufficient funds")
        assert isinstance(error, OrderExecutionError)

    def test_notification_error(self):
        """Test NotificationError."""
        error = NotificationError("Notification failed")
        assert isinstance(error, AlchemiserError)

    def test_market_closed_error(self):
        """Test MarketClosedError."""
        error = MarketClosedError("Market is closed")
        assert isinstance(error, TradingClientError)

    def test_websocket_error(self):
        """Test WebSocketError."""
        error = WebSocketError("WebSocket connection failed")
        assert isinstance(error, DataProviderError)

    def test_streaming_error(self):
        """Test StreamingError."""
        error = StreamingError("Stream interrupted")
        assert isinstance(error, DataProviderError)

    def test_security_error(self):
        """Test SecurityError."""
        error = SecurityError("Security violation")
        assert isinstance(error, AlchemiserError)

    def test_strategy_validation_error(self):
        """Test StrategyValidationError."""
        error = StrategyValidationError("Strategy validation failed")
        assert isinstance(error, StrategyExecutionError)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_string_message(self):
        """Test exception with empty string message."""
        error = AlchemiserError("")
        assert error.message == ""
        assert str(error) == ""

    def test_unicode_in_message(self):
        """Test exception with unicode characters."""
        message = "Error: 'AAPL' → $100.50 × 10 shares ✗"
        error = AlchemiserError(message)
        assert error.message == message

    def test_complex_context_data(self):
        """Test exception with complex nested context data."""
        context = {
            "symbol": "AAPL",
            "metadata": {
                "retry_count": 3,
                "timeout": 30.0,
            },
            "tags": ["high_priority", "urgent"],
        }
        error = AlchemiserError("Complex error", context=context)

        assert error.context["metadata"]["retry_count"] == 3
        assert "high_priority" in error.context["tags"]

    def test_exception_with_zero_values(self):
        """Test exception with zero numeric values."""
        error = OrderExecutionError("Test", quantity=Decimal("0.0"), price=Decimal("0.0"))

        # Zero values should be in context (they're not None)
        assert error.context["quantity"] == "0.0"
        assert error.context["price"] == "0.0"


class TestInheritanceChains:
    """Test complex inheritance chains."""

    def test_order_execution_error_chain(self):
        """Test OrderExecutionError inheritance chain."""
        error = OrderExecutionError("Test")

        assert isinstance(error, OrderExecutionError)
        assert isinstance(error, TradingClientError)
        assert isinstance(error, AlchemiserError)
        assert isinstance(error, Exception)

    def test_order_placement_error_chain(self):
        """Test OrderPlacementError inheritance chain."""
        error = OrderPlacementError("Test")

        assert isinstance(error, OrderPlacementError)
        assert isinstance(error, OrderExecutionError)
        assert isinstance(error, TradingClientError)
        assert isinstance(error, AlchemiserError)

    def test_configuration_error_chain(self):
        """Test ConfigurationError inheritance chain."""
        error = ConfigurationError("Test")

        assert isinstance(error, ConfigurationError)
        assert isinstance(error, AlchemiserError)
        assert isinstance(error, Exception)

    def test_environment_error_chain(self):
        """Test EnvironmentError inheritance chain."""
        error = EnvironmentError("Test")

        assert isinstance(error, EnvironmentError)
        assert isinstance(error, ConfigurationError)
        assert isinstance(error, AlchemiserError)


class TestContextPropagation:
    """Test that context is properly propagated through exception hierarchy."""

    def test_configuration_error_context(self):
        """Test ConfigurationError builds context dict."""
        error = ConfigurationError("Test", config_key="API_KEY", config_value="***")

        assert "config_key" in error.context
        assert error.context["config_key"] == "API_KEY"

    def test_order_execution_error_context(self):
        """Test OrderExecutionError builds context dict."""
        error = OrderExecutionError("Test", symbol="AAPL", quantity=Decimal("100.0"))

        assert "symbol" in error.context
        assert "quantity" in error.context

    def test_portfolio_error_context(self):
        """Test PortfolioError builds context dict with correlation_id."""
        error = PortfolioError("Test", correlation_id="corr-123")

        assert "correlation_id" in error.context
        assert error.context["correlation_id"] == "corr-123"

    def test_strategy_execution_error_context(self):
        """Test StrategyExecutionError builds context dict."""
        error = StrategyExecutionError("Test", strategy_name="momentum", correlation_id="corr-456")

        assert "strategy_name" in error.context
        assert error.context["strategy_name"] == "momentum"
        assert "correlation_id" in error.context
        assert error.context["correlation_id"] == "corr-456"
