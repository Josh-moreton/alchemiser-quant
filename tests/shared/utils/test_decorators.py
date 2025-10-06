#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Comprehensive tests for decorators module.

Tests cover:
- Exception translation correctness
- Exception chaining preservation
- Default return behavior
- Type correctness
- Edge cases and error conditions
- Contract validation
"""

from __future__ import annotations

from typing import Any

import pytest

from the_alchemiser.shared.types.exceptions import (
    ConfigurationError,
    DataProviderError,
    MarketDataError,
    StreamingError,
    TradingClientError,
)
from the_alchemiser.shared.utils.decorators import (
    translate_config_errors,
    translate_market_data_errors,
    translate_service_errors,
    translate_streaming_errors,
    translate_trading_errors,
)


class TestTranslateServiceErrors:
    """Test suite for translate_service_errors decorator."""

    @pytest.mark.unit
    def test_translates_connection_error_to_data_provider_error(self) -> None:
        """Verify ConnectionError is translated to DataProviderError."""

        @translate_service_errors()
        def failing_function() -> None:
            raise ConnectionError("Connection failed")

        with pytest.raises(DataProviderError) as exc_info:
            failing_function()

        assert "Service error in failing_function" in str(exc_info.value)
        assert "Connection failed" in str(exc_info.value)

    @pytest.mark.unit
    def test_translates_timeout_error_to_data_provider_error(self) -> None:
        """Verify TimeoutError is translated to DataProviderError."""

        @translate_service_errors()
        def failing_function() -> None:
            raise TimeoutError("Request timed out")

        with pytest.raises(DataProviderError) as exc_info:
            failing_function()

        assert "Service error in failing_function" in str(exc_info.value)
        assert "Request timed out" in str(exc_info.value)

    @pytest.mark.unit
    def test_translates_value_error_to_data_provider_error(self) -> None:
        """Verify ValueError is translated to DataProviderError."""

        @translate_service_errors()
        def failing_function() -> None:
            raise ValueError("Invalid value")

        with pytest.raises(DataProviderError) as exc_info:
            failing_function()

        assert "Service error in failing_function" in str(exc_info.value)
        assert "Invalid value" in str(exc_info.value)

    @pytest.mark.unit
    def test_translates_key_error_to_data_provider_error(self) -> None:
        """Verify KeyError is translated to DataProviderError."""

        @translate_service_errors()
        def failing_function() -> None:
            raise KeyError("missing_key")

        with pytest.raises(DataProviderError) as exc_info:
            failing_function()

        assert "Service error in failing_function" in str(exc_info.value)

    @pytest.mark.unit
    def test_preserves_exception_chain(self) -> None:
        """Verify original exception is preserved in __cause__."""

        @translate_service_errors()
        def failing_function() -> None:
            raise ConnectionError("Original error")

        with pytest.raises(DataProviderError) as exc_info:
            failing_function()

        assert exc_info.value.__cause__ is not None
        assert isinstance(exc_info.value.__cause__, ConnectionError)
        assert str(exc_info.value.__cause__) == "Original error"

    @pytest.mark.unit
    def test_successful_function_execution_unchanged(self) -> None:
        """Verify decorator doesn't affect successful function execution."""

        @translate_service_errors()
        def successful_function(x: int, y: int) -> int:
            return x + y

        result = successful_function(2, 3)
        assert result == 5

    @pytest.mark.unit
    def test_custom_error_types_mapping(self) -> None:
        """Verify custom error type mapping works correctly."""

        @translate_service_errors(
            error_types={
                ValueError: MarketDataError,
                KeyError: TradingClientError,
            }
        )
        def failing_function(error_type: str) -> None:
            if error_type == "value":
                raise ValueError("Value error")
            raise KeyError("Key error")

        with pytest.raises(MarketDataError):
            failing_function("value")

        with pytest.raises(TradingClientError):
            failing_function("key")

    @pytest.mark.unit
    def test_default_return_suppresses_exception(self) -> None:
        """Verify default_return parameter suppresses exceptions."""

        @translate_service_errors(default_return="fallback_value")
        def failing_function() -> str:
            raise ConnectionError("Connection failed")

        result = failing_function()
        assert result == "fallback_value"

    @pytest.mark.unit
    def test_default_return_none_does_not_suppress_exception(self) -> None:
        """Verify default_return=None does not suppress exceptions.

        Note: The decorator checks 'if default_return is not None', so None
        is treated as 'no default provided' and exceptions are raised.
        """

        @translate_service_errors(default_return=None)
        def failing_function() -> str | None:
            raise ConnectionError("Connection failed")

        # None is the default, so exceptions should still be raised
        with pytest.raises(DataProviderError):
            failing_function()

    @pytest.mark.unit
    def test_default_return_with_different_types(self) -> None:
        """Verify default_return works with various types."""

        @translate_service_errors(default_return={"error": True})
        def dict_function() -> dict[str, bool]:
            raise ValueError("Error")

        result = dict_function()
        assert result == {"error": True}

        @translate_service_errors(default_return=[])
        def list_function() -> list[object]:
            raise ValueError("Error")

        result = list_function()
        assert result == []

        @translate_service_errors(default_return=0)
        def int_function() -> int:
            raise ValueError("Error")

        result = int_function()
        assert result == 0

    @pytest.mark.unit
    def test_unexpected_exception_translated_to_data_provider_error(self) -> None:
        """Verify unexpected exceptions are caught and translated."""

        @translate_service_errors()
        def failing_function() -> None:
            raise RuntimeError("Unexpected error")

        with pytest.raises(DataProviderError) as exc_info:
            failing_function()

        assert "Unexpected error in failing_function" in str(exc_info.value)
        assert isinstance(exc_info.value.__cause__, RuntimeError)

    @pytest.mark.unit
    def test_preserves_function_metadata(self) -> None:
        """Verify decorator preserves function name and docstring."""

        @translate_service_errors()
        def documented_function() -> None:
            """Document a test function."""

        assert documented_function.__name__ == "documented_function"
        assert documented_function.__doc__ == "Document a test function."

    @pytest.mark.unit
    def test_handles_functions_with_args_and_kwargs(self) -> None:
        """Verify decorator handles functions with various argument patterns."""

        @translate_service_errors()
        def function_with_args(a: int, b: int, *args: int, **kwargs: int) -> int:
            if a < 0:
                raise ValueError("Negative value")
            return a + b + sum(args) + sum(kwargs.values())

        # Test successful execution
        result = function_with_args(1, 2, 3, 4, x=5, y=6)
        assert result == 21

        # Test error handling
        with pytest.raises(DataProviderError):
            function_with_args(-1, 2)

    @pytest.mark.unit
    def test_empty_error_types_dict(self) -> None:
        """Verify decorator handles empty error_types dict."""

        @translate_service_errors(error_types={})
        def failing_function() -> None:
            raise ValueError("Error")

        # Should use catch-all handler
        with pytest.raises(DataProviderError) as exc_info:
            failing_function()

        assert "Unexpected error in failing_function" in str(exc_info.value)


class TestTranslateMarketDataErrors:
    """Test suite for translate_market_data_errors decorator."""

    @pytest.mark.unit
    def test_translates_to_market_data_error(self) -> None:
        """Verify exceptions are translated to MarketDataError."""

        @translate_market_data_errors()
        def failing_function() -> None:
            raise ConnectionError("Market data unavailable")

        with pytest.raises(MarketDataError) as exc_info:
            failing_function()

        assert "Market data unavailable" in str(exc_info.value)

    @pytest.mark.unit
    def test_multiple_error_types(self) -> None:
        """Verify multiple exception types are translated correctly."""

        @translate_market_data_errors()
        def failing_function(error_type: str) -> None:
            if error_type == "connection":
                raise ConnectionError("Connection failed")
            if error_type == "timeout":
                raise TimeoutError("Timeout")
            if error_type == "value":
                raise ValueError("Invalid value")
            raise KeyError("Missing key")

        for error_type in ["connection", "timeout", "value", "key"]:
            with pytest.raises(MarketDataError):
                failing_function(error_type)

    @pytest.mark.unit
    def test_with_default_return(self) -> None:
        """Verify default return works with market data errors."""

        @translate_market_data_errors(default_return={})
        def failing_function() -> dict[str, Any]:
            raise ConnectionError("Failed")

        result = failing_function()
        assert result == {}


class TestTranslateTradingErrors:
    """Test suite for translate_trading_errors decorator."""

    @pytest.mark.unit
    def test_translates_to_trading_client_error(self) -> None:
        """Verify exceptions are translated to TradingClientError."""

        @translate_trading_errors()
        def failing_function() -> None:
            raise ConnectionError("Trading API unavailable")

        with pytest.raises(TradingClientError) as exc_info:
            failing_function()

        assert "Trading API unavailable" in str(exc_info.value)

    @pytest.mark.unit
    def test_preserves_exception_chain_for_trading_errors(self) -> None:
        """Verify exception chaining works for trading errors."""

        @translate_trading_errors()
        def failing_function() -> None:
            raise TimeoutError("Order timeout")

        with pytest.raises(TradingClientError) as exc_info:
            failing_function()

        assert isinstance(exc_info.value.__cause__, TimeoutError)

    @pytest.mark.unit
    def test_with_default_return(self) -> None:
        """Verify default return works with trading errors."""

        @translate_trading_errors(default_return=False)
        def failing_function() -> bool:
            raise ConnectionError("Failed")

        result = failing_function()
        assert result is False


class TestTranslateStreamingErrors:
    """Test suite for translate_streaming_errors decorator."""

    @pytest.mark.unit
    def test_translates_to_streaming_error(self) -> None:
        """Verify exceptions are translated to StreamingError."""

        @translate_streaming_errors()
        def failing_function() -> None:
            raise ConnectionError("Stream disconnected")

        with pytest.raises(StreamingError) as exc_info:
            failing_function()

        assert "Stream disconnected" in str(exc_info.value)

    @pytest.mark.unit
    def test_handles_timeout_errors(self) -> None:
        """Verify timeout errors are handled correctly."""

        @translate_streaming_errors()
        def failing_function() -> None:
            raise TimeoutError("Stream timeout")

        with pytest.raises(StreamingError):
            failing_function()

    @pytest.mark.unit
    def test_handles_value_errors(self) -> None:
        """Verify value errors are handled correctly."""

        @translate_streaming_errors()
        def failing_function() -> None:
            raise ValueError("Invalid stream data")

        with pytest.raises(StreamingError):
            failing_function()

    @pytest.mark.unit
    def test_with_default_return(self) -> None:
        """Verify default return works with streaming errors."""

        @translate_streaming_errors(default_return=[])
        def failing_function() -> list[str]:
            raise ConnectionError("Failed")

        result = failing_function()
        assert result == []


class TestTranslateConfigErrors:
    """Test suite for translate_config_errors decorator."""

    @pytest.mark.unit
    def test_translates_file_not_found_to_configuration_error(self) -> None:
        """Verify FileNotFoundError is translated to ConfigurationError."""

        @translate_config_errors()
        def failing_function() -> None:
            raise FileNotFoundError("Config file not found")

        with pytest.raises(ConfigurationError) as exc_info:
            failing_function()

        assert "Config file not found" in str(exc_info.value)

    @pytest.mark.unit
    def test_translates_value_error_to_configuration_error(self) -> None:
        """Verify ValueError is translated to ConfigurationError."""

        @translate_config_errors()
        def failing_function() -> None:
            raise ValueError("Invalid config value")

        with pytest.raises(ConfigurationError) as exc_info:
            failing_function()

        assert "Invalid config value" in str(exc_info.value)

    @pytest.mark.unit
    def test_translates_key_error_to_configuration_error(self) -> None:
        """Verify KeyError is translated to ConfigurationError."""

        @translate_config_errors()
        def failing_function() -> None:
            raise KeyError("missing_config_key")

        with pytest.raises(ConfigurationError) as exc_info:
            failing_function()

        assert "Service error in failing_function" in str(exc_info.value)

    @pytest.mark.unit
    def test_preserves_exception_chain_for_config_errors(self) -> None:
        """Verify exception chaining works for configuration errors."""

        @translate_config_errors()
        def failing_function() -> None:
            raise FileNotFoundError("Missing file")

        with pytest.raises(ConfigurationError) as exc_info:
            failing_function()

        assert isinstance(exc_info.value.__cause__, FileNotFoundError)

    @pytest.mark.unit
    def test_with_default_return(self) -> None:
        """Verify default return works with configuration errors."""

        @translate_config_errors(default_return={"default": "config"})
        def failing_function() -> dict[str, str]:
            raise FileNotFoundError("Failed")

        result = failing_function()
        assert result == {"default": "config"}


class TestDecoratorEdgeCases:
    """Test suite for edge cases and corner cases."""

    @pytest.mark.unit
    def test_nested_decorators(self) -> None:
        """Verify multiple decorators can be stacked.

        Note: When decorators are nested, the outer decorator catches exceptions
        from the inner decorator. Since the inner decorator raises TradingClientError,
        which is not in the outer decorator's error_types, it gets caught by the
        catch-all handler and wrapped in DataProviderError with 'Unexpected error'.
        """

        @translate_market_data_errors()
        @translate_trading_errors()
        def failing_function() -> None:
            raise ConnectionError("Error")

        # Innermost decorator (trading_errors) translates to TradingClientError
        # Outermost decorator (market_data_errors) catches it as unexpected and wraps in DataProviderError
        with pytest.raises(DataProviderError) as exc_info:
            failing_function()

        # Verify it mentions "Unexpected error" since TradingClientError is not in market_data_errors mapping
        assert "Unexpected error" in str(exc_info.value)

    @pytest.mark.unit
    def test_decorator_with_class_methods(self) -> None:
        """Verify decorator works with class methods."""

        class TestClass:
            @translate_service_errors()
            def instance_method(self) -> str:
                raise ValueError("Error")

            @translate_service_errors()
            @classmethod
            def class_method(cls) -> str:
                raise ValueError("Error")

            @translate_service_errors()
            @staticmethod
            def static_method() -> str:
                raise ValueError("Error")

        obj = TestClass()

        with pytest.raises(DataProviderError):
            obj.instance_method()

        with pytest.raises(DataProviderError):
            TestClass.class_method()

        with pytest.raises(DataProviderError):
            TestClass.static_method()

    @pytest.mark.unit
    def test_decorator_with_generator_function(self) -> None:
        """Verify decorator behavior with generator functions.

        Note: The decorator wraps the generator creation, not the generator execution.
        Exceptions raised during generator execution are not caught by the decorator.
        """

        from collections.abc import Generator

        @translate_service_errors()
        def generator_function() -> Generator[int, None, None]:
            yield 1
            raise ValueError("Error in generator")

        gen = generator_function()
        assert next(gen) == 1

        # Generator exceptions are not caught by the decorator since they occur
        # during iteration, not during the function call that creates the generator
        with pytest.raises(ValueError) as exc_info:
            next(gen)

        assert "Error in generator" in str(exc_info.value)

    @pytest.mark.unit
    def test_decorator_with_async_function(self) -> None:
        """Verify decorator with async functions (note: decorator is sync-only)."""

        @translate_service_errors()
        async def async_function() -> None:
            raise ValueError("Error")

        # Decorator should still wrap the function
        assert async_function.__name__ == "async_function"

    @pytest.mark.unit
    def test_original_exception_message_preserved(self) -> None:
        """Verify original exception message is fully preserved in translation."""
        original_message = "This is a very specific error message with details"

        @translate_service_errors()
        def failing_function() -> None:
            raise ConnectionError(original_message)

        with pytest.raises(DataProviderError) as exc_info:
            failing_function()

        assert original_message in str(exc_info.value)

    @pytest.mark.unit
    def test_function_with_return_annotation(self) -> None:
        """Verify decorator preserves return type annotations."""

        @translate_service_errors()
        def typed_function(x: int) -> int:
            if x < 0:
                raise ValueError("Negative")
            return x * 2

        # Verify successful execution maintains return value
        assert typed_function(5) == 10

        # Verify error handling
        with pytest.raises(DataProviderError):
            typed_function(-1)

    @pytest.mark.unit
    def test_exception_from_nested_call(self) -> None:
        """Verify exceptions from nested function calls are caught."""

        def inner_function() -> None:
            raise ConnectionError("Inner error")

        @translate_service_errors()
        def outer_function() -> None:
            inner_function()

        with pytest.raises(DataProviderError) as exc_info:
            outer_function()

        assert "Inner error" in str(exc_info.value)
        assert isinstance(exc_info.value.__cause__, ConnectionError)
