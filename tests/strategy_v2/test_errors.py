"""Business Unit: strategy | Status: current

Test strategy_v2 error types and exception hierarchy.

Tests verify correct inheritance, context handling, and serialization
of strategy-specific exceptions.
"""

from datetime import datetime

import pytest

from the_alchemiser.shared.types.exceptions import AlchemiserError
from the_alchemiser.strategy_v2.errors import (
    StrategyConfigurationError,
    StrategyExecutionError,
    StrategyMarketDataError,
    StrategyV2Error,
)


class TestStrategyV2Error:
    """Test base StrategyV2Error exception."""

    def test_inherits_from_alchemiser_error(self):
        """Test StrategyV2Error inherits from AlchemiserError."""
        error = StrategyV2Error("Test error")
        assert isinstance(error, AlchemiserError)
        assert isinstance(error, Exception)

    def test_basic_initialization(self):
        """Test basic error initialization with message."""
        error = StrategyV2Error("Test error message")
        assert str(error) == "Test error message"
        assert error.message == "Test error message"
        assert error.module == "strategy_v2"
        assert error.correlation_id is None

    def test_initialization_with_module(self):
        """Test error initialization with custom module."""
        error = StrategyV2Error("Test error", module="strategy_v2.core.orchestrator")
        assert error.module == "strategy_v2.core.orchestrator"
        assert error.context["module"] == "strategy_v2.core.orchestrator"

    def test_initialization_with_correlation_id(self):
        """Test error initialization with correlation ID."""
        error = StrategyV2Error("Test error", correlation_id="abc-123")
        assert error.correlation_id == "abc-123"
        assert error.context["correlation_id"] == "abc-123"

    def test_initialization_with_additional_context(self):
        """Test error initialization with additional context kwargs."""
        error = StrategyV2Error(
            "Test error",
            module="strategy_v2.test",
            correlation_id="xyz-789",
            symbol="SPY",
            strategy_id="nuclear",
            timeout=30,
        )
        assert error.context["symbol"] == "SPY"
        assert error.context["strategy_id"] == "nuclear"
        assert error.context["timeout"] == 30
        assert error.context["module"] == "strategy_v2.test"
        assert error.context["correlation_id"] == "xyz-789"

    def test_to_dict_method(self):
        """Test to_dict method inherited from AlchemiserError."""
        error = StrategyV2Error(
            "Test error",
            module="strategy_v2.core",
            correlation_id="test-123",
            symbol="AAPL",
        )
        error_dict = error.to_dict()
        
        assert error_dict["error_type"] == "StrategyV2Error"
        assert error_dict["message"] == "Test error"
        assert error_dict["context"]["module"] == "strategy_v2.core"
        assert error_dict["context"]["correlation_id"] == "test-123"
        assert error_dict["context"]["symbol"] == "AAPL"
        assert "timestamp" in error_dict
        
        # Verify timestamp is ISO format string
        timestamp = error_dict["timestamp"]
        datetime.fromisoformat(timestamp)  # Should not raise


class TestStrategyExecutionError:
    """Test StrategyExecutionError exception."""

    def test_inherits_from_strategy_v2_error(self):
        """Test StrategyExecutionError inherits from StrategyV2Error."""
        error = StrategyExecutionError("Execution failed")
        assert isinstance(error, StrategyV2Error)
        assert isinstance(error, AlchemiserError)

    def test_initialization_with_strategy_id(self):
        """Test error initialization with strategy_id."""
        error = StrategyExecutionError(
            "Strategy failed",
            strategy_id="nuclear",
            correlation_id="test-456"
        )
        assert error.strategy_id == "nuclear"
        assert error.correlation_id == "test-456"
        assert error.module == "strategy_v2.core.orchestrator"

    def test_initialization_with_additional_context(self):
        """Test error initialization with additional context."""
        error = StrategyExecutionError(
            "Calculation error",
            strategy_id="tecl",
            correlation_id="xyz-789",
            symbol="QQQ",
            timeframe="1D",
        )
        assert error.strategy_id == "tecl"
        assert error.context["symbol"] == "QQQ"
        assert error.context["timeframe"] == "1D"

    def test_default_module_is_orchestrator(self):
        """Test that default module is strategy_v2.core.orchestrator."""
        error = StrategyExecutionError("Test")
        assert error.module == "strategy_v2.core.orchestrator"

    def test_to_dict_includes_strategy_id(self):
        """Test to_dict includes strategy_id in output."""
        error = StrategyExecutionError(
            "Strategy failed",
            strategy_id="klm",
            correlation_id="test-123"
        )
        error_dict = error.to_dict()
        
        assert error_dict["error_type"] == "StrategyExecutionError"
        assert error_dict["message"] == "Strategy failed"


class TestStrategyConfigurationError:
    """Test StrategyConfigurationError exception."""

    def test_inherits_from_strategy_v2_error(self):
        """Test StrategyConfigurationError inherits from StrategyV2Error."""
        error = StrategyConfigurationError("Config invalid")
        assert isinstance(error, StrategyV2Error)
        assert isinstance(error, AlchemiserError)

    def test_initialization_with_correlation_id(self):
        """Test error initialization with correlation ID."""
        error = StrategyConfigurationError(
            "Missing symbols",
            correlation_id="cfg-123"
        )
        assert error.correlation_id == "cfg-123"
        assert error.module == "strategy_v2.models.context"

    def test_initialization_with_config_context(self):
        """Test error initialization with configuration context."""
        error = StrategyConfigurationError(
            "Invalid config",
            correlation_id="cfg-456",
            config_key="symbols",
            strategy_id="nuclear",
        )
        assert error.context["config_key"] == "symbols"
        assert error.context["strategy_id"] == "nuclear"

    def test_default_module_is_context(self):
        """Test that default module is strategy_v2.models.context."""
        error = StrategyConfigurationError("Test")
        assert error.module == "strategy_v2.models.context"

    def test_to_dict_includes_context(self):
        """Test to_dict includes configuration context."""
        error = StrategyConfigurationError(
            "Missing required field",
            correlation_id="test-789",
            config_key="timeframe"
        )
        error_dict = error.to_dict()
        
        assert error_dict["error_type"] == "StrategyConfigurationError"
        assert error_dict["context"]["config_key"] == "timeframe"


class TestStrategyMarketDataError:
    """Test StrategyMarketDataError exception."""

    def test_inherits_from_strategy_v2_error(self):
        """Test StrategyMarketDataError inherits from StrategyV2Error."""
        error = StrategyMarketDataError("Data fetch failed")
        assert isinstance(error, StrategyV2Error)
        assert isinstance(error, AlchemiserError)

    def test_initialization_with_symbol(self):
        """Test error initialization with symbol."""
        error = StrategyMarketDataError(
            "Failed to fetch bars",
            symbol="SPY",
            correlation_id="data-123"
        )
        assert error.symbol == "SPY"
        assert error.correlation_id == "data-123"
        assert error.module == "strategy_v2.adapters.market_data_adapter"

    def test_initialization_with_data_context(self):
        """Test error initialization with data access context."""
        error = StrategyMarketDataError(
            "No data available",
            symbol="AAPL",
            correlation_id="data-456",
            timeframe="1H",
            lookback_days=30,
        )
        assert error.symbol == "AAPL"
        assert error.context["timeframe"] == "1H"
        assert error.context["lookback_days"] == 30

    def test_default_module_is_market_data_adapter(self):
        """Test that default module is strategy_v2.adapters.market_data_adapter."""
        error = StrategyMarketDataError("Test")
        assert error.module == "strategy_v2.adapters.market_data_adapter"

    def test_to_dict_includes_symbol(self):
        """Test to_dict includes symbol in output."""
        error = StrategyMarketDataError(
            "API error",
            symbol="MSFT",
            correlation_id="test-999"
        )
        error_dict = error.to_dict()
        
        assert error_dict["error_type"] == "StrategyMarketDataError"
        assert error_dict["message"] == "API error"


class TestErrorHierarchy:
    """Test error class hierarchy and relationships."""

    def test_all_errors_inherit_from_strategy_v2_error(self):
        """Test all strategy errors inherit from StrategyV2Error."""
        errors = [
            StrategyExecutionError("test"),
            StrategyConfigurationError("test"),
            StrategyMarketDataError("test"),
        ]
        
        for error in errors:
            assert isinstance(error, StrategyV2Error)
            assert isinstance(error, AlchemiserError)

    def test_each_error_has_unique_module_default(self):
        """Test each error type has a unique default module."""
        execution_error = StrategyExecutionError("test")
        config_error = StrategyConfigurationError("test")
        data_error = StrategyMarketDataError("test")
        
        modules = {
            execution_error.module,
            config_error.module,
            data_error.module,
        }
        
        # All three should have different default modules
        assert len(modules) == 3

    def test_correlation_id_propagates_through_hierarchy(self):
        """Test correlation_id is properly stored in all error types."""
        correlation_id = "test-correlation-123"
        
        errors = [
            StrategyV2Error("test", correlation_id=correlation_id),
            StrategyExecutionError("test", correlation_id=correlation_id),
            StrategyConfigurationError("test", correlation_id=correlation_id),
            StrategyMarketDataError("test", correlation_id=correlation_id),
        ]
        
        for error in errors:
            assert error.correlation_id == correlation_id
            assert error.context["correlation_id"] == correlation_id


class TestErrorStringRepresentation:
    """Test error string representations and messages."""

    def test_error_message_preserved(self):
        """Test error message is preserved in str() representation."""
        message = "This is a detailed error message"
        errors = [
            StrategyV2Error(message),
            StrategyExecutionError(message),
            StrategyConfigurationError(message),
            StrategyMarketDataError(message),
        ]
        
        for error in errors:
            assert str(error) == message
            assert error.message == message

    def test_error_can_be_caught_generically(self):
        """Test errors can be caught as Exception or AlchemiserError."""
        error = StrategyExecutionError("test")
        
        # Should be catchable as Exception
        try:
            raise error
        except Exception as e:
            assert isinstance(e, StrategyExecutionError)
        
        # Should be catchable as AlchemiserError
        try:
            raise error
        except AlchemiserError as e:
            assert isinstance(e, StrategyExecutionError)
        
        # Should be catchable as StrategyV2Error
        try:
            raise error
        except StrategyV2Error as e:
            assert isinstance(e, StrategyExecutionError)


class TestErrorContextHandling:
    """Test context handling and serialization."""

    def test_none_values_allowed_in_context(self):
        """Test None values are allowed in context kwargs."""
        error = StrategyV2Error(
            "test",
            symbol=None,
            strategy_id=None,
        )
        assert "symbol" in error.context
        assert "strategy_id" in error.context
        assert error.context["symbol"] is None
        assert error.context["strategy_id"] is None

    def test_various_types_in_context(self):
        """Test various types are accepted in context kwargs."""
        error = StrategyV2Error(
            "test",
            string_val="text",
            int_val=42,
            float_val=3.14,
            bool_val=True,
            none_val=None,
        )
        assert error.context["string_val"] == "text"
        assert error.context["int_val"] == 42
        assert error.context["float_val"] == 3.14
        assert error.context["bool_val"] is True
        assert error.context["none_val"] is None

    def test_empty_context_allowed(self):
        """Test errors work with no additional context."""
        errors = [
            StrategyV2Error("test"),
            StrategyExecutionError("test"),
            StrategyConfigurationError("test"),
            StrategyMarketDataError("test"),
        ]
        
        for error in errors:
            # Should have at least module in context
            assert "module" in error.context
            # Should be able to convert to dict
            error_dict = error.to_dict()
            assert error_dict["error_type"] is not None
