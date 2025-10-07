#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

Comprehensive tests for strategy_v2 error handling.

Tests cover:
- Error initialization and context handling
- Correlation ID propagation
- Module attribution
- Error serialization
- Backward compatibility
"""

from __future__ import annotations

import pytest

from the_alchemiser.strategy_v2.errors import (
    ConfigurationError,
    MarketDataError,
    StrategyExecutionError,
    StrategyV2Error,
)


@pytest.mark.unit
class TestStrategyV2Error:
    """Test base StrategyV2Error exception."""

    def test_create_basic_error(self):
        """Test creating error with message only."""
        error = StrategyV2Error("Test error")
        assert str(error) == "Test error"
        assert error.module == "strategy_v2"
        assert error.correlation_id is None
        assert error.context == {}

    def test_create_error_with_module(self):
        """Test creating error with custom module."""
        error = StrategyV2Error("Test error", module="strategy_v2.custom")
        assert error.module == "strategy_v2.custom"

    def test_create_error_with_correlation_id(self):
        """Test creating error with correlation ID."""
        correlation_id = "test-corr-123"
        error = StrategyV2Error("Test error", correlation_id=correlation_id)
        assert error.correlation_id == correlation_id

    def test_create_error_with_causation_id(self):
        """Test creating error with causation ID."""
        causation_id = "test-cause-456"
        error = StrategyV2Error("Test error", causation_id=causation_id)
        assert error.causation_id == causation_id

    def test_create_error_with_both_ids(self):
        """Test creating error with both correlation and causation IDs."""
        correlation_id = "test-corr-123"
        causation_id = "test-cause-456"
        error = StrategyV2Error(
            "Test error",
            correlation_id=correlation_id,
            causation_id=causation_id,
        )
        assert error.correlation_id == correlation_id
        assert error.causation_id == causation_id

    def test_create_error_with_context(self):
        """Test creating error with additional context."""
        error = StrategyV2Error(
            "Test error",
            symbol="AAPL",
            quantity=100,
            price=150.5,
            flag=True,
        )
        assert error.context["symbol"] == "AAPL"
        assert error.context["quantity"] == 100
        assert error.context["price"] == 150.5
        assert error.context["flag"] is True

    def test_create_error_with_mixed_types(self):
        """Test context accepts multiple types."""
        error = StrategyV2Error(
            "Test error",
            str_val="test",
            int_val=42,
            float_val=3.14,
            bool_val=True,
            none_val=None,
        )
        assert error.context["str_val"] == "test"
        assert error.context["int_val"] == 42
        assert error.context["float_val"] == 3.14
        assert error.context["bool_val"] is True
        assert error.context["none_val"] is None

    def test_error_is_exception(self):
        """Test that StrategyV2Error is an Exception."""
        error = StrategyV2Error("Test error")
        assert isinstance(error, Exception)

    def test_error_can_be_raised(self):
        """Test that error can be raised and caught."""
        with pytest.raises(StrategyV2Error) as exc_info:
            raise StrategyV2Error("Test error", correlation_id="test-123")
        assert str(exc_info.value) == "Test error"
        assert exc_info.value.correlation_id == "test-123"

    def test_to_dict_serialization(self):
        """Test that error can be serialized to dict."""
        error = StrategyV2Error(
            "Test error",
            correlation_id="corr-123",
            causation_id="cause-456",
            symbol="AAPL",
        )
        result = error.to_dict()
        assert result["error_type"] == "StrategyV2Error"
        assert result["message"] == "Test error"
        assert result["module"] == "strategy_v2"
        assert result["correlation_id"] == "corr-123"
        assert result["causation_id"] == "cause-456"
        assert result["context"]["symbol"] == "AAPL"

    def test_to_dict_with_no_context(self):
        """Test to_dict with minimal error."""
        error = StrategyV2Error("Simple error")
        result = error.to_dict()
        assert result["error_type"] == "StrategyV2Error"
        assert result["message"] == "Simple error"
        assert result["module"] == "strategy_v2"
        assert result["correlation_id"] is None
        assert result["causation_id"] is None
        assert result["context"] == {}


@pytest.mark.unit
class TestStrategyExecutionError:
    """Test StrategyExecutionError exception."""

    def test_create_basic_execution_error(self):
        """Test creating execution error with message only."""
        error = StrategyExecutionError("Execution failed")
        assert str(error) == "Execution failed"
        assert error.module == "strategy_v2.core.orchestrator"
        assert error.correlation_id is None
        assert error.strategy_id is None

    def test_create_execution_error_with_strategy_id(self):
        """Test creating execution error with strategy ID."""
        error = StrategyExecutionError("Execution failed", strategy_id="nuclear")
        assert error.strategy_id == "nuclear"

    def test_create_execution_error_with_context(self):
        """Test creating execution error with additional context."""
        error = StrategyExecutionError(
            "Execution failed",
            strategy_id="tecl",
            symbol="TECL",
            reason="timeout",
        )
        assert error.strategy_id == "tecl"
        assert error.context["symbol"] == "TECL"
        assert error.context["reason"] == "timeout"

    def test_execution_error_inherits_from_base(self):
        """Test that StrategyExecutionError inherits from StrategyV2Error."""
        error = StrategyExecutionError("Test")
        assert isinstance(error, StrategyV2Error)
        assert isinstance(error, Exception)

    def test_execution_error_hardcoded_module(self):
        """Test that execution error has hardcoded module."""
        error = StrategyExecutionError("Test")
        assert error.module == "strategy_v2.core.orchestrator"

    def test_execution_error_forces_none_correlation_id(self):
        """Test that execution error accepts correlation_id."""
        # Updated: execution error now accepts correlation_id
        error = StrategyExecutionError(
            "Test",
            strategy_id="test",
            correlation_id="corr-123",
            causation_id="cause-456",
        )
        assert error.correlation_id == "corr-123"
        assert error.causation_id == "cause-456"

    def test_execution_error_to_dict(self):
        """Test execution error serialization."""
        error = StrategyExecutionError(
            "Test",
            strategy_id="nuclear",
            correlation_id="corr-123",
            symbol="SPY",
        )
        result = error.to_dict()
        assert result["error_type"] == "StrategyExecutionError"
        # strategy_id is not in base to_dict() method, it's only an instance attribute
        assert "strategy_id" not in result
        assert result["correlation_id"] == "corr-123"
        assert result["context"]["symbol"] == "SPY"
        # strategy_id is stored as attribute but not in to_dict by default
        assert error.strategy_id == "nuclear"


@pytest.mark.unit
class TestConfigurationError:
    """Test ConfigurationError exception."""

    def test_create_basic_configuration_error(self):
        """Test creating configuration error with message only."""
        error = ConfigurationError("Invalid config")
        assert str(error) == "Invalid config"
        assert error.module == "strategy_v2.models.context"
        assert error.correlation_id is None

    def test_create_configuration_error_with_context(self):
        """Test creating configuration error with context."""
        error = ConfigurationError(
            "Invalid symbols",
            symbols=["AAPL", "GOOGL"],
            reason="duplicate",
        )
        assert error.context["symbols"] == ["AAPL", "GOOGL"]
        assert error.context["reason"] == "duplicate"

    def test_configuration_error_inherits_from_base(self):
        """Test that ConfigurationError inherits from StrategyV2Error."""
        error = ConfigurationError("Test")
        assert isinstance(error, StrategyV2Error)
        assert isinstance(error, Exception)

    def test_configuration_error_hardcoded_module(self):
        """Test that configuration error has hardcoded module."""
        error = ConfigurationError("Test")
        assert error.module == "strategy_v2.models.context"

    def test_configuration_error_forces_none_correlation_id(self):
        """Test that configuration error accepts correlation_id."""
        # Updated: configuration error now accepts correlation_id
        error = ConfigurationError(
            "Test",
            config_key="test",
            correlation_id="corr-123",
            causation_id="cause-456",
        )
        assert error.correlation_id == "corr-123"
        assert error.causation_id == "cause-456"


@pytest.mark.unit
class TestMarketDataError:
    """Test MarketDataError exception."""

    def test_create_basic_market_data_error(self):
        """Test creating market data error with message only."""
        error = MarketDataError("Data fetch failed")
        assert str(error) == "Data fetch failed"
        assert error.module == "strategy_v2.adapters.market_data_adapter"
        assert error.correlation_id is None
        assert error.symbol is None

    def test_create_market_data_error_with_symbol(self):
        """Test creating market data error with symbol."""
        error = MarketDataError("Data fetch failed", symbol="AAPL")
        assert error.symbol == "AAPL"

    def test_create_market_data_error_with_context(self):
        """Test creating market data error with additional context."""
        error = MarketDataError(
            "Data fetch failed",
            symbol="SPY",
            timeframe="1Day",
            start_date="2024-01-01",
        )
        assert error.symbol == "SPY"
        assert error.context["timeframe"] == "1Day"
        assert error.context["start_date"] == "2024-01-01"

    def test_market_data_error_inherits_from_base(self):
        """Test that MarketDataError inherits from StrategyV2Error."""
        error = MarketDataError("Test")
        assert isinstance(error, StrategyV2Error)
        assert isinstance(error, Exception)

    def test_market_data_error_hardcoded_module(self):
        """Test that market data error has hardcoded module."""
        error = MarketDataError("Test")
        assert error.module == "strategy_v2.adapters.market_data_adapter"

    def test_market_data_error_forces_none_correlation_id(self):
        """Test that market data error accepts correlation_id."""
        # Updated: market data error now accepts correlation_id
        error = MarketDataError(
            "Test",
            symbol="AAPL",
            correlation_id="corr-123",
            causation_id="cause-456",
        )
        assert error.correlation_id == "corr-123"
        assert error.causation_id == "cause-456"


@pytest.mark.unit
class TestErrorContextPropagation:
    """Test error context propagation patterns."""

    def test_correlation_id_in_base_error(self):
        """Test that correlation ID is accessible in base error."""
        correlation_id = "signal-123"
        error = StrategyV2Error("Test", correlation_id=correlation_id)
        assert error.correlation_id == correlation_id

    def test_causation_id_in_base_error(self):
        """Test that causation ID is accessible in base error."""
        causation_id = "event-456"
        error = StrategyV2Error("Test", causation_id=causation_id)
        assert error.causation_id == causation_id

    def test_both_ids_propagate(self):
        """Test that both IDs propagate through error hierarchy."""
        correlation_id = "corr-123"
        causation_id = "cause-456"

        exec_error = StrategyExecutionError(
            "Test",
            strategy_id="nuclear",
            correlation_id=correlation_id,
            causation_id=causation_id,
        )
        assert exec_error.correlation_id == correlation_id
        assert exec_error.causation_id == causation_id

        config_error = ConfigurationError(
            "Test",
            correlation_id=correlation_id,
            causation_id=causation_id,
        )
        assert config_error.correlation_id == correlation_id
        assert config_error.causation_id == causation_id

        data_error = MarketDataError(
            "Test",
            symbol="AAPL",
            correlation_id=correlation_id,
            causation_id=causation_id,
        )
        assert data_error.correlation_id == correlation_id
        assert data_error.causation_id == causation_id

    def test_module_context_in_errors(self):
        """Test that module context is preserved in all errors."""
        base_error = StrategyV2Error("Test")
        exec_error = StrategyExecutionError("Test")
        config_error = ConfigurationError("Test")
        data_error = MarketDataError("Test")

        assert base_error.module == "strategy_v2"
        assert exec_error.module == "strategy_v2.core.orchestrator"
        assert config_error.module == "strategy_v2.models.context"
        assert data_error.module == "strategy_v2.adapters.market_data_adapter"

    def test_kwargs_context_preserved(self):
        """Test that kwargs context is preserved across error types."""
        for error_cls in [
            StrategyV2Error,
            StrategyExecutionError,
            ConfigurationError,
            MarketDataError,
        ]:
            error = error_cls("Test", extra_key="extra_value")
            assert error.context["extra_key"] == "extra_value"


@pytest.mark.unit
class TestErrorCatchability:
    """Test that errors can be caught at different hierarchy levels."""

    def test_catch_specific_execution_error(self):
        """Test catching specific StrategyExecutionError."""
        with pytest.raises(StrategyExecutionError):
            raise StrategyExecutionError("Test")

    def test_catch_execution_error_as_base(self):
        """Test catching StrategyExecutionError as StrategyV2Error."""
        with pytest.raises(StrategyV2Error):
            raise StrategyExecutionError("Test")

    def test_catch_configuration_error_as_base(self):
        """Test catching ConfigurationError as StrategyV2Error."""
        with pytest.raises(StrategyV2Error):
            raise ConfigurationError("Test")

    def test_catch_market_data_error_as_base(self):
        """Test catching MarketDataError as StrategyV2Error."""
        with pytest.raises(StrategyV2Error):
            raise MarketDataError("Test")

    def test_catch_all_as_exception(self):
        """Test catching any error as base Exception."""
        with pytest.raises(Exception):
            raise StrategyV2Error("Test")


@pytest.mark.unit
class TestErrorMessages:
    """Test error message formatting."""

    def test_simple_message_preservation(self):
        """Test that simple messages are preserved."""
        msg = "Simple error message"
        error = StrategyV2Error(msg)
        assert str(error) == msg

    def test_multiline_message_preservation(self):
        """Test that multiline messages are preserved."""
        msg = "Line 1\nLine 2\nLine 3"
        error = StrategyV2Error(msg)
        assert str(error) == msg

    def test_message_with_special_characters(self):
        """Test message with special characters."""
        msg = "Error: Symbol 'AAPL' failed @ $150.50"
        error = StrategyV2Error(msg)
        assert str(error) == msg


@pytest.mark.unit
class TestErrorAttributes:
    """Test that all expected attributes are present."""

    def test_base_error_attributes(self):
        """Test base error has all expected attributes."""
        error = StrategyV2Error("Test", correlation_id="123", extra="data")
        assert hasattr(error, "module")
        assert hasattr(error, "correlation_id")
        assert hasattr(error, "context")

    def test_execution_error_attributes(self):
        """Test execution error has all expected attributes."""
        error = StrategyExecutionError("Test", strategy_id="nuclear")
        assert hasattr(error, "module")
        assert hasattr(error, "correlation_id")
        assert hasattr(error, "context")
        assert hasattr(error, "strategy_id")

    def test_error_has_message_attribute(self):
        """Test that error has message attribute for structured logging."""
        error = StrategyV2Error("Test message")
        assert hasattr(error, "message")
        assert error.message == "Test message"

    def test_market_data_error_attributes(self):
        """Test market data error has all expected attributes."""
        error = MarketDataError("Test", symbol="AAPL")
        assert hasattr(error, "module")
        assert hasattr(error, "correlation_id")
        assert hasattr(error, "causation_id")
        assert hasattr(error, "context")
        assert hasattr(error, "symbol")
        assert hasattr(error, "message")


@pytest.mark.unit
class TestErrorSerialization:
    """Test error serialization for observability."""

    def test_base_error_serialization(self):
        """Test base error to_dict includes all fields."""
        error = StrategyV2Error(
            "Test error",
            correlation_id="corr-123",
            causation_id="cause-456",
            extra_field="extra",
        )
        result = error.to_dict()

        assert "error_type" in result
        assert "message" in result
        assert "module" in result
        assert "correlation_id" in result
        assert "causation_id" in result
        assert "context" in result

        assert result["error_type"] == "StrategyV2Error"
        assert result["message"] == "Test error"
        assert result["correlation_id"] == "corr-123"
        assert result["causation_id"] == "cause-456"
        assert result["context"]["extra_field"] == "extra"

    def test_subclass_error_serialization(self):
        """Test that subclass errors serialize correctly."""
        error = StrategyExecutionError(
            "Execution failed",
            strategy_id="nuclear",
            correlation_id="corr-123",
            symbol="SPY",
        )
        result = error.to_dict()

        assert result["error_type"] == "StrategyExecutionError"
        assert result["message"] == "Execution failed"
        assert result["module"] == "strategy_v2.core.orchestrator"
        assert result["correlation_id"] == "corr-123"
        assert result["context"]["symbol"] == "SPY"

    def test_serialization_handles_none_values(self):
        """Test that serialization handles None values gracefully."""
        error = StrategyV2Error("Test")
        result = error.to_dict()

        assert result["correlation_id"] is None
        assert result["causation_id"] is None
        assert result["context"] == {}

    def test_serialization_preserves_types(self):
        """Test that serialization preserves context value types."""
        error = StrategyV2Error(
            "Test",
            int_val=42,
            float_val=3.14,
            str_val="test",
            bool_val=True,
            none_val=None,
        )
        result = error.to_dict()
        context = result["context"]

        assert isinstance(context["int_val"], int)
        assert isinstance(context["float_val"], float)
        assert isinstance(context["str_val"], str)
        assert isinstance(context["bool_val"], bool)
        assert context["none_val"] is None
