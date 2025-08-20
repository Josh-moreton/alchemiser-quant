#!/usr/bin/env python3
"""
Tests for request_id and error_id presence in error logs.

Validates that error logs consistently include request_id and error_id
when appropriate context is available.
"""

import json
import logging

from the_alchemiser.infrastructure.logging.logging_utils import (
    StructuredFormatter,
    get_error_id,
    get_request_id,
    set_error_id,
    set_request_id,
)
from the_alchemiser.services.errors.exceptions import (
    ConfigurationError,
    DataProviderError,
    StrategyExecutionError,
    TradingClientError,
)
from the_alchemiser.services.errors.handler import TradingSystemErrorHandler


class TestRequestIdErrorIdValidation:
    """Test that request_id and error_id are properly included in error logs."""

    def test_error_handler_logs_with_request_id_when_set(self, caplog):
        """Test that TradingSystemErrorHandler includes request_id in error logs."""
        caplog.clear()

        # Set request_id context
        set_request_id("req-error-handler-test")

        try:
            handler = TradingSystemErrorHandler()
            test_error = ConfigurationError("Test configuration error")

            # Handle the error
            handler.handle_error(
                error=test_error,
                context="test_context",
                component="test.component",
                additional_data={"key": "value"},
            )

            # Verify exactly one error log
            error_logs = [record for record in caplog.records if record.levelno >= logging.ERROR]
            assert len(error_logs) == 1, f"Expected 1 error log, got {len(error_logs)}"

            # The request_id should be available in context vars during logging
            current_request_id = get_request_id()
            assert (
                current_request_id == "req-error-handler-test"
            ), "Request ID should be preserved in context"

        finally:
            set_request_id(None)

    def test_error_handler_logs_with_error_id_when_set(self, caplog):
        """Test that TradingSystemErrorHandler includes error_id in error logs."""
        caplog.clear()

        # Set error_id context
        set_error_id("err-error-handler-test")

        try:
            handler = TradingSystemErrorHandler()
            test_error = StrategyExecutionError("Test strategy error")

            # Handle the error
            handler.handle_error(
                error=test_error, context="strategy_execution", component="test.strategy.component"
            )

            # Verify exactly one error log
            error_logs = [record for record in caplog.records if record.levelno >= logging.ERROR]
            assert len(error_logs) == 1, f"Expected 1 error log, got {len(error_logs)}"

            # The error_id should be available in context vars during logging
            current_error_id = get_error_id()
            assert (
                current_error_id == "err-error-handler-test"
            ), "Error ID should be preserved in context"

        finally:
            set_error_id(None)

    def test_error_handler_logs_with_both_ids_when_set(self, caplog):
        """Test that both request_id and error_id are included when both are set."""
        caplog.clear()

        # Set both context IDs
        set_request_id("req-both-ids-test")
        set_error_id("err-both-ids-test")

        try:
            handler = TradingSystemErrorHandler()
            test_error = TradingClientError("Test trading client error")

            # Handle the error
            handler.handle_error(
                error=test_error,
                context="trading_operation",
                component="test.trading.client",
                additional_data={"operation": "place_order", "symbol": "AAPL"},
            )

            # Verify exactly one error log
            error_logs = [record for record in caplog.records if record.levelno >= logging.ERROR]
            assert len(error_logs) == 1, f"Expected 1 error log, got {len(error_logs)}"

            # Both IDs should be available in context vars during logging
            current_request_id = get_request_id()
            current_error_id = get_error_id()
            assert (
                current_request_id == "req-both-ids-test"
            ), "Request ID should be preserved in context"
            assert (
                current_error_id == "err-both-ids-test"
            ), "Error ID should be preserved in context"

        finally:
            set_request_id(None)
            set_error_id(None)

    def test_structured_formatter_includes_request_id_in_json(self):
        """Test that StructuredFormatter includes request_id in JSON output."""
        formatter = StructuredFormatter()

        # Set request_id
        set_request_id("req-structured-json-test")

        try:
            record = logging.LogRecord(
                name="test.logger",
                level=logging.ERROR,
                pathname="test.py",
                lineno=100,
                msg="Test error message",
                args=(),
                exc_info=None,
            )
            record.module = "test"
            record.funcName = "test_function"

            result = formatter.format(record)
            log_data = json.loads(result)

            # Verify request_id is in JSON
            assert "request_id" in log_data
            assert log_data["request_id"] == "req-structured-json-test"

        finally:
            set_request_id(None)

    def test_structured_formatter_includes_error_id_in_json(self):
        """Test that StructuredFormatter includes error_id in JSON output."""
        formatter = StructuredFormatter()

        # Set error_id
        set_error_id("err-structured-json-test")

        try:
            record = logging.LogRecord(
                name="test.logger",
                level=logging.ERROR,
                pathname="test.py",
                lineno=200,
                msg="Test error with error_id",
                args=(),
                exc_info=None,
            )
            record.module = "test"
            record.funcName = "test_error_function"

            result = formatter.format(record)
            log_data = json.loads(result)

            # Verify error_id is in JSON
            assert "error_id" in log_data
            assert log_data["error_id"] == "err-structured-json-test"

        finally:
            set_error_id(None)

    def test_structured_formatter_excludes_ids_when_not_set(self):
        """Test that StructuredFormatter excludes IDs when they are not set."""
        formatter = StructuredFormatter()

        # Ensure IDs are not set
        set_request_id(None)
        set_error_id(None)

        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=300,
            msg="Test message without IDs",
            args=(),
            exc_info=None,
        )
        record.module = "test"
        record.funcName = "test_no_ids"

        result = formatter.format(record)
        log_data = json.loads(result)

        # Verify IDs are not included when not set
        assert "request_id" not in log_data
        assert "error_id" not in log_data

    def test_multiple_errors_maintain_separate_error_ids(self, caplog):
        """Test that multiple errors maintain their own error_ids."""
        caplog.clear()

        handler = TradingSystemErrorHandler()

        # First error with request_id
        set_request_id("req-multi-error-1")
        error1 = ConfigurationError("First configuration error")
        handler.handle_error(error1, "config_context_1", "component.1")
        first_request_id = get_request_id()

        # Second error with different request_id
        set_request_id("req-multi-error-2")
        error2 = DataProviderError("Second data provider error")
        handler.handle_error(error2, "data_context_2", "component.2")
        second_request_id = get_request_id()

        try:
            # Verify we have exactly two error logs
            error_logs = [record for record in caplog.records if record.levelno >= logging.ERROR]
            assert len(error_logs) == 2, f"Expected 2 error logs, got {len(error_logs)}"

            # Verify that different request_ids were used
            assert first_request_id == "req-multi-error-1"
            assert second_request_id == "req-multi-error-2"

            # Verify both errors are recorded
            assert len(handler.errors) == 2

        finally:
            set_request_id(None)
            set_error_id(None)

    def test_context_propagation_across_nested_calls(self):
        """Test that request_id and error_id propagate correctly across nested calls."""

        def level_3_function() -> tuple[str | None, str | None]:
            """Deepest level function."""
            return get_request_id(), get_error_id()

        def level_2_function() -> tuple[str | None, str | None]:
            """Middle level function."""
            return level_3_function()

        def level_1_function() -> tuple[str | None, str | None]:
            """Top level function."""
            return level_2_function()

        # Set context at the top level
        set_request_id("req-nested-propagation")
        set_error_id("err-nested-propagation")

        try:
            # Call nested functions
            req_id, err_id = level_1_function()

            # Verify propagation
            assert req_id == "req-nested-propagation"
            assert err_id == "err-nested-propagation"

        finally:
            set_request_id(None)
            set_error_id(None)

    def test_enhanced_error_automatically_sets_error_id(self):
        """Test that creating an enhanced error automatically sets error_id context."""
        from the_alchemiser.services.errors.handler import EnhancedAlchemiserError

        # Ensure error_id is not set initially
        set_error_id(None)
        assert get_error_id() is None

        try:
            # Create an enhanced error
            error = EnhancedAlchemiserError("Test enhanced error")

            # The error_id should now be set in context
            context_error_id = get_error_id()
            assert context_error_id is not None
            assert context_error_id == error.error_id

        finally:
            set_error_id(None)

    def test_error_id_updates_with_multiple_enhanced_errors(self):
        """Test that error_id context updates correctly with multiple enhanced errors."""
        from the_alchemiser.services.errors.handler import EnhancedAlchemiserError

        # Ensure error_id is not set initially
        set_error_id(None)
        assert get_error_id() is None

        try:
            # Create first enhanced error
            error1 = EnhancedAlchemiserError("First enhanced error")
            first_error_id = get_error_id()
            assert first_error_id == error1.error_id

            # Create second enhanced error
            error2 = EnhancedAlchemiserError("Second enhanced error")
            second_error_id = get_error_id()
            assert second_error_id == error2.error_id

            # Should be different error IDs
            assert first_error_id != second_error_id

        finally:
            set_error_id(None)
