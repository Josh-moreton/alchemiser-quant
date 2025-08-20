#!/usr/bin/env python3
"""
Tests to verify that decorators do not perform logging.

Validates that exception translation decorators only translate exceptions
without performing any logging operations. Logging should be handled
explicitly by orchestrators/services using the error handler.
"""

from unittest.mock import Mock, patch

import pytest

from the_alchemiser.services.errors.decorators import (
    translate_config_errors,
    translate_market_data_errors,
    translate_service_errors,
    translate_streaming_errors,
    translate_trading_errors,
)
from the_alchemiser.services.errors.exceptions import (
    ConfigurationError,
    DataProviderError,
    MarketDataError,
    StreamingError,
    TradingClientError,
)


class TestDecoratorLoggingBehavior:
    """Test that decorators do not perform any logging operations."""

    def test_translate_service_errors_does_not_log(self):
        """Test that translate_service_errors decorator does not log anything."""
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            @translate_service_errors()
            def failing_function() -> None:
                raise ConnectionError("Connection failed")

            with pytest.raises(DataProviderError):
                failing_function()

            # Verify no logging calls were made
            mock_logger.error.assert_not_called()
            mock_logger.warning.assert_not_called()
            mock_logger.info.assert_not_called()
            mock_logger.debug.assert_not_called()
            mock_logger.critical.assert_not_called()

    def test_translate_market_data_errors_does_not_log(self):
        """Test that translate_market_data_errors decorator does not log anything."""
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            @translate_market_data_errors()
            def failing_market_data_function() -> None:
                raise TimeoutError("Market data timeout")

            with pytest.raises(MarketDataError):
                failing_market_data_function()

            # Verify no logging calls were made
            mock_logger.error.assert_not_called()
            mock_logger.warning.assert_not_called()
            mock_logger.info.assert_not_called()
            mock_logger.debug.assert_not_called()
            mock_logger.critical.assert_not_called()

    def test_translate_trading_errors_does_not_log(self):
        """Test that translate_trading_errors decorator does not log anything."""
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            @translate_trading_errors()
            def failing_trading_function() -> None:
                raise ConnectionError("Trading connection failed")

            with pytest.raises(TradingClientError):
                failing_trading_function()

            # Verify no logging calls were made
            mock_logger.error.assert_not_called()
            mock_logger.warning.assert_not_called()
            mock_logger.info.assert_not_called()
            mock_logger.debug.assert_not_called()
            mock_logger.critical.assert_not_called()

    def test_translate_streaming_errors_does_not_log(self):
        """Test that translate_streaming_errors decorator does not log anything."""
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            @translate_streaming_errors()
            def failing_streaming_function() -> None:
                raise ConnectionError("Streaming connection lost")

            with pytest.raises(StreamingError):
                failing_streaming_function()

            # Verify no logging calls were made
            mock_logger.error.assert_not_called()
            mock_logger.warning.assert_not_called()
            mock_logger.info.assert_not_called()
            mock_logger.debug.assert_not_called()
            mock_logger.critical.assert_not_called()

    def test_translate_config_errors_does_not_log(self):
        """Test that translate_config_errors decorator does not log anything."""
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            @translate_config_errors()
            def failing_config_function() -> None:
                raise FileNotFoundError("Configuration file not found")

            with pytest.raises(ConfigurationError):
                failing_config_function()

            # Verify no logging calls were made
            mock_logger.error.assert_not_called()
            mock_logger.warning.assert_not_called()
            mock_logger.info.assert_not_called()
            mock_logger.debug.assert_not_called()
            mock_logger.critical.assert_not_called()

    def test_multiple_decorator_calls_no_logging(self):
        """Test that multiple decorator calls do not log anything."""
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            @translate_service_errors()
            def first_function() -> None:
                raise ValueError("First error")

            @translate_market_data_errors()
            def second_function() -> None:
                raise KeyError("Second error")

            # Call both functions and catch their exceptions
            with pytest.raises(DataProviderError):
                first_function()

            with pytest.raises(MarketDataError):
                second_function()

            # Verify no logging calls were made across all calls
            mock_logger.error.assert_not_called()
            mock_logger.warning.assert_not_called()
            mock_logger.info.assert_not_called()
            mock_logger.debug.assert_not_called()
            mock_logger.critical.assert_not_called()

    def test_decorator_with_successful_call_no_logging(self):
        """Test that decorators don't log anything even on successful calls."""
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            @translate_service_errors()
            def successful_function() -> str:
                return "success"

            result = successful_function()
            assert result == "success"

            # Verify no logging calls were made
            mock_logger.error.assert_not_called()
            mock_logger.warning.assert_not_called()
            mock_logger.info.assert_not_called()
            mock_logger.debug.assert_not_called()
            mock_logger.critical.assert_not_called()

    def test_decorator_with_default_return_no_logging(self):
        """Test that decorators with default_return don't log anything."""
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            @translate_service_errors(default_return="default")
            def function_with_default() -> str:
                raise ConnectionError("Connection failed")

            result = function_with_default()
            assert result == "default"

            # Verify no logging calls were made
            mock_logger.error.assert_not_called()
            mock_logger.warning.assert_not_called()
            mock_logger.info.assert_not_called()
            mock_logger.debug.assert_not_called()
            mock_logger.critical.assert_not_called()

    def test_nested_decorated_functions_no_logging(self):
        """Test that nested decorated functions do not log anything."""
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            @translate_service_errors()
            def outer_function() -> None:
                inner_function()

            @translate_market_data_errors()
            def inner_function() -> None:
                raise TimeoutError("Inner timeout")

            with pytest.raises(DataProviderError):
                outer_function()

            # Verify no logging calls were made despite nested decorated calls
            mock_logger.error.assert_not_called()
            mock_logger.warning.assert_not_called()
            mock_logger.info.assert_not_called()
            mock_logger.debug.assert_not_called()
            mock_logger.critical.assert_not_called()

    def test_decorator_preserves_original_exception_chain(self):
        """Test that decorators preserve original exception without logging."""
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            @translate_service_errors()
            def chained_error_function() -> None:
                try:
                    raise ValueError("Original error")
                except ValueError as e:
                    raise ConnectionError("Wrapped error") from e

            with pytest.raises(DataProviderError) as exc_info:
                chained_error_function()

            # Verify exception chain is preserved
            assert exc_info.value.__cause__.__class__ is ConnectionError
            assert exc_info.value.__cause__.__cause__.__class__ is ValueError

            # Verify no logging calls were made
            mock_logger.error.assert_not_called()
            mock_logger.warning.assert_not_called()
            mock_logger.info.assert_not_called()
            mock_logger.debug.assert_not_called()
            mock_logger.critical.assert_not_called()

    def test_decorator_with_custom_error_mapping_no_logging(self):
        """Test that decorators with custom error mapping don't log anything."""
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            custom_mapping = {
                ValueError: ConfigurationError,
                KeyError: ConfigurationError,
            }

            @translate_service_errors(error_types=custom_mapping)
            def custom_mapped_function() -> None:
                raise ValueError("Custom mapped error")

            with pytest.raises(ConfigurationError):
                custom_mapped_function()

            # Verify no logging calls were made
            mock_logger.error.assert_not_called()
            mock_logger.warning.assert_not_called()
            mock_logger.info.assert_not_called()
            mock_logger.debug.assert_not_called()
            mock_logger.critical.assert_not_called()

    def test_all_decorators_combined_no_logging(self, caplog):
        """Test that using all decorators in sequence produces no logs."""
        caplog.clear()

        @translate_service_errors()
        def service_function() -> None:
            market_data_function()

        @translate_market_data_errors()
        def market_data_function() -> None:
            trading_function()

        @translate_trading_errors()
        def trading_function() -> None:
            streaming_function()

        @translate_streaming_errors()
        def streaming_function() -> None:
            config_function()

        @translate_config_errors()
        def config_function() -> None:
            raise FileNotFoundError("Config file not found")

        with pytest.raises(DataProviderError):
            service_function()

        # Verify no log records were generated by decorators
        all_logs = list(caplog.records)
        assert (
            len(all_logs) == 0
        ), f"Decorators should not log anything, but found {len(all_logs)} log records"
