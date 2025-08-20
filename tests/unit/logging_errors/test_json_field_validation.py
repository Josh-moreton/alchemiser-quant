#!/usr/bin/env python3
"""
Tests for JSON field validation in structured production logs.

Validates that production logs contain all required fields and proper formatting
in accordance with the logging specification.
"""

import io
import json
import logging

from the_alchemiser.infrastructure.logging.logging_utils import (
    StructuredFormatter,
    set_error_id,
    set_request_id,
    setup_logging,
)


class TestProductionJSONFieldValidation:
    """Test JSON payload validation for production structured logs."""

    def test_structured_log_contains_all_required_fields(self):
        """Test that structured logs contain all mandatory JSON fields."""
        formatter = StructuredFormatter()

        # Create a realistic log record
        record = logging.LogRecord(
            name="the_alchemiser.services.trading",
            level=logging.INFO,
            pathname="/app/the_alchemiser/services/trading/order_service.py",
            lineno=127,
            msg="Order executed successfully",
            args=(),
            exc_info=None,
        )
        record.module = "order_service"
        record.funcName = "place_market_order"

        # Set context variables for realistic production scenario
        set_request_id("req-12345-trading")
        set_error_id("err-67890-trading")

        try:
            result = formatter.format(record)
            log_data = json.loads(result)

            # Verify all required fields are present
            required_fields = [
                "timestamp",
                "level",
                "logger",
                "message",
                "module",
                "function",
                "line",
                "request_id",
                "error_id",
            ]

            for field in required_fields:
                assert field in log_data, f"Required field '{field}' missing from structured log"

            # Verify field types and values
            assert isinstance(log_data["timestamp"], str)
            assert log_data["level"] == "INFO"
            assert log_data["logger"] == "the_alchemiser.services.trading"
            assert log_data["message"] == "Order executed successfully"
            assert log_data["module"] == "order_service"
            assert log_data["function"] == "place_market_order"
            assert log_data["line"] == 127
            assert log_data["request_id"] == "req-12345-trading"
            assert log_data["error_id"] == "err-67890-trading"

        finally:
            # Clean up context
            set_request_id(None)
            set_error_id(None)

    def test_structured_log_with_exception_info(self):
        """Test that structured logs properly include exception information."""
        formatter = StructuredFormatter()

        # Create exception for testing
        try:
            raise ValueError("Test trading error")
        except ValueError:
            import sys

            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="the_alchemiser.services.errors",
            level=logging.ERROR,
            pathname="/app/the_alchemiser/services/errors/handler.py",
            lineno=234,
            msg="Trading operation failed",
            args=(),
            exc_info=exc_info,
        )
        record.module = "handler"
        record.funcName = "handle_error"

        set_request_id("req-error-test")
        set_error_id("err-exception-test")

        try:
            result = formatter.format(record)
            log_data = json.loads(result)

            # Verify base fields
            assert log_data["level"] == "ERROR"
            assert log_data["message"] == "Trading operation failed"
            assert log_data["request_id"] == "req-error-test"
            assert log_data["error_id"] == "err-exception-test"

            # Verify exception information is properly structured
            assert "exception" in log_data
            exception_data = log_data["exception"]
            assert exception_data["type"] == "ValueError"
            assert exception_data["message"] == "Test trading error"
            assert "traceback" in exception_data
            assert len(exception_data["traceback"]) > 0

        finally:
            set_request_id(None)
            set_error_id(None)

    def test_structured_log_with_extra_fields(self):
        """Test that structured logs include extra fields from the log record."""
        formatter = StructuredFormatter()

        record = logging.LogRecord(
            name="the_alchemiser.domain.strategies",
            level=logging.INFO,
            pathname="/app/the_alchemiser/domain/strategies/nuclear.py",
            lineno=45,
            msg="Strategy signal generated",
            args=(),
            exc_info=None,
        )
        record.module = "nuclear"
        record.funcName = "generate_signals"

        # Add extra fields typical in trading logs
        record.extra_fields = {
            "symbol": "AAPL",
            "signal": "BUY",
            "confidence": 0.85,
            "allocation": 0.25,
            "strategy": "nuclear",
        }

        set_request_id("req-strategy-signal")

        try:
            result = formatter.format(record)
            log_data = json.loads(result)

            # Verify required fields
            assert log_data["level"] == "INFO"
            assert log_data["message"] == "Strategy signal generated"
            assert log_data["request_id"] == "req-strategy-signal"

            # Verify extra fields are included
            assert log_data["symbol"] == "AAPL"
            assert log_data["signal"] == "BUY"
            assert log_data["confidence"] == 0.85
            assert log_data["allocation"] == 0.25
            assert log_data["strategy"] == "nuclear"

        finally:
            set_request_id(None)
            set_error_id(None)

    def test_structured_log_without_context_vars(self):
        """Test that structured logs work correctly when context vars are not set."""
        formatter = StructuredFormatter()

        record = logging.LogRecord(
            name="the_alchemiser.infrastructure.aws",
            level=logging.WARNING,
            pathname="/app/the_alchemiser/infrastructure/aws/s3.py",
            lineno=89,
            msg="S3 connection retry",
            args=(),
            exc_info=None,
        )
        record.module = "s3"
        record.funcName = "upload_file"

        # Ensure context vars are cleared
        set_request_id(None)
        set_error_id(None)

        result = formatter.format(record)
        log_data = json.loads(result)

        # Verify required fields (except context vars)
        expected_fields = ["timestamp", "level", "logger", "message", "module", "function", "line"]
        for field in expected_fields:
            assert field in log_data, f"Required field '{field}' missing"

        # Verify context vars are not included when not set
        assert "request_id" not in log_data
        assert "error_id" not in log_data

        # Verify values
        assert log_data["level"] == "WARNING"
        assert log_data["message"] == "S3 connection retry"
        assert log_data["module"] == "s3"
        assert log_data["function"] == "upload_file"
        assert log_data["line"] == 89

    def test_production_setup_uses_structured_format(self):
        """Test that production logging setup creates proper structured format."""
        # Clear any existing handlers
        root_logger = logging.getLogger()
        original_handlers = root_logger.handlers[:]
        root_logger.handlers.clear()

        try:
            # Setup production-style logging
            setup_logging(
                log_level=logging.INFO,
                structured_format=True,
                respect_existing_handlers=False,
            )

            # Verify structured formatter is in use
            root_logger = logging.getLogger()
            assert len(root_logger.handlers) > 0

            structured_handlers = [
                h for h in root_logger.handlers if isinstance(h.formatter, StructuredFormatter)
            ]
            assert len(structured_handlers) > 0, "No StructuredFormatter found in handlers"

            # Test actual log output
            log_capture = io.StringIO()
            test_logger = logging.getLogger("test.production.json")
            handler = logging.StreamHandler(log_capture)
            handler.setFormatter(StructuredFormatter())
            test_logger.addHandler(handler)
            test_logger.setLevel(logging.INFO)

            set_request_id("prod-test-123")
            set_error_id("prod-error-456")

            test_logger.info("Production test message")

            log_output = log_capture.getvalue().strip()
            assert log_output, "No log output captured"

            # Parse as JSON to verify structure
            log_data = json.loads(log_output)
            assert log_data["message"] == "Production test message"
            assert log_data["request_id"] == "prod-test-123"
            assert log_data["error_id"] == "prod-error-456"

        finally:
            # Restore original handlers
            root_logger.handlers.clear()
            for handler in original_handlers:
                root_logger.addHandler(handler)
            set_request_id(None)
            set_error_id(None)

    def test_structured_log_json_serialization_edge_cases(self):
        """Test structured logging handles edge cases in JSON serialization."""
        formatter = StructuredFormatter()

        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test with edge cases",
            args=(),
            exc_info=None,
        )
        record.module = "test"
        record.funcName = "test_func"

        # Add edge case values that could break JSON serialization
        record.extra_fields = {
            "none_value": None,
            "empty_string": "",
            "unicode_chars": "Special chars: ñáéíóú",
            "numbers": [1, 2.5, -3],
            "boolean_values": [True, False],
            "nested_dict": {"key": "value", "number": 42},
        }

        result = formatter.format(record)

        # Should be valid JSON
        log_data = json.loads(result)

        # Verify edge case values are preserved
        assert log_data["none_value"] is None
        assert log_data["empty_string"] == ""
        assert log_data["unicode_chars"] == "Special chars: ñáéíóú"
        assert log_data["numbers"] == [1, 2.5, -3]
        assert log_data["boolean_values"] == [True, False]
        assert log_data["nested_dict"] == {"key": "value", "number": 42}
