"""Tests for Logging Core v2 implementation."""

import json
import logging
import os
from unittest.mock import patch

from the_alchemiser.infrastructure.logging.logging_utils import (
    StructuredFormatter,
    configure_production_logging,
    get_error_id,
    get_request_id,
    get_service_logger,
    set_error_id,
    set_request_id,
    setup_logging,
)


class TestStructuredFormatter:
    """Test the StructuredFormatter for production JSON logging."""

    def test_basic_json_structure(self):
        """Test that basic log structure contains required fields."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.module = "test_module"
        record.funcName = "test_function"

        result = formatter.format(record)
        log_data = json.loads(result)

        # Verify required fields are present
        assert "timestamp" in log_data
        assert log_data["level"] == "INFO"
        assert log_data["logger"] == "test_logger"
        assert log_data["message"] == "Test message"
        assert log_data["module"] == "test_module"
        assert log_data["function"] == "test_function"
        assert log_data["line"] == 42

    def test_context_vars_inclusion(self):
        """Test that request_id and error_id are included when set."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.ERROR,
            pathname="test.py",
            lineno=10,
            msg="Error message",
            args=(),
            exc_info=None,
        )
        record.module = "test"
        record.funcName = "test_func"

        # Set context vars
        set_request_id("req-123")
        set_error_id("err-456")

        result = formatter.format(record)
        log_data = json.loads(result)

        assert log_data["request_id"] == "req-123"
        assert log_data["error_id"] == "err-456"

        # Clean up
        set_request_id(None)
        set_error_id(None)

    def test_context_vars_absent_when_not_set(self):
        """Test that request_id and error_id are not included when not set."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Info message",
            args=(),
            exc_info=None,
        )
        record.module = "test"
        record.funcName = "test_func"

        # Ensure context vars are not set
        set_request_id(None)
        set_error_id(None)

        result = formatter.format(record)
        log_data = json.loads(result)

        assert "request_id" not in log_data
        assert "error_id" not in log_data

    def test_exception_info_included(self):
        """Test that exception information is properly formatted."""
        formatter = StructuredFormatter()

        try:
            raise ValueError("Test exception")
        except ValueError:
            import sys
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test_logger",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Error with exception",
            args=(),
            exc_info=exc_info,
        )
        record.module = "test"
        record.funcName = "test_func"

        result = formatter.format(record)
        log_data = json.loads(result)

        assert "exception" in log_data
        assert log_data["exception"]["type"] == "ValueError"
        assert log_data["exception"]["message"] == "Test exception"
        assert "traceback" in log_data["exception"]

    def test_extra_fields_included(self):
        """Test that extra fields are included in the log output."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Message with extra fields",
            args=(),
            exc_info=None,
        )
        record.module = "test"
        record.funcName = "test_func"
        record.extra_fields = {"symbol": "AAPL", "quantity": 100}

        result = formatter.format(record)
        log_data = json.loads(result)

        assert log_data["symbol"] == "AAPL"
        assert log_data["quantity"] == 100


class TestContextVarHelpers:
    """Test the context variable helper functions."""

    def test_request_id_operations(self):
        """Test setting and getting request ID."""
        # Initially should be None
        assert get_request_id() is None

        # Set and verify
        set_request_id("test-request-123")
        assert get_request_id() == "test-request-123"

        # Clear and verify
        set_request_id(None)
        assert get_request_id() is None

    def test_error_id_operations(self):
        """Test setting and getting error ID."""
        # Initially should be None
        assert get_error_id() is None

        # Set and verify
        set_error_id("test-error-456")
        assert get_error_id() == "test-error-456"

        # Clear and verify
        set_error_id(None)
        assert get_error_id() is None


class TestSetupLogging:
    """Test the centralized logging setup."""

    def setup_method(self):
        """Reset logging state before each test."""
        # Clear root logger handlers
        root_logger = logging.getLogger()
        root_logger.handlers.clear()

    def test_setup_logging_respects_existing_handlers(self):
        """Test that setup_logging respects existing handlers when configured."""
        root_logger = logging.getLogger()

        # Add a dummy handler
        existing_handler = logging.StreamHandler()
        root_logger.addHandler(existing_handler)

        # Setup with respect_existing_handlers=True
        setup_logging(
            log_level=logging.INFO,
            respect_existing_handlers=True,
            structured_format=False,
        )

        # Should still have the original handler plus potentially no new ones
        assert existing_handler in root_logger.handlers

    def test_setup_logging_clears_handlers_when_not_respecting(self):
        """Test that setup_logging clears handlers when not respecting existing ones."""
        root_logger = logging.getLogger()

        # Add a dummy handler
        existing_handler = logging.StreamHandler()
        root_logger.addHandler(existing_handler)

        # Setup with respect_existing_handlers=False (default)
        setup_logging(
            log_level=logging.INFO,
            respect_existing_handlers=False,
            structured_format=False,
        )

        # Should not have the original handler
        assert existing_handler not in root_logger.handlers

    def test_production_logging_uses_structured_format(self):
        """Test that production logging configures structured JSON format."""
        # Reset logging first
        root_logger = logging.getLogger()
        root_logger.handlers.clear()

        configure_production_logging(log_level=logging.INFO)

        # Get a logger and log a message
        logger = logging.getLogger("test.production")

        # Verify that the handlers are configured with StructuredFormatter
        root_logger = logging.getLogger()
        assert len(root_logger.handlers) > 0

        # Check that at least one handler uses StructuredFormatter
        structured_handlers = [
            h for h in root_logger.handlers
            if isinstance(h.formatter, StructuredFormatter)
        ]
        assert len(structured_handlers) > 0


class TestServiceLogger:
    """Test the service logger functionality."""

    def test_get_service_logger_returns_correct_namespace(self):
        """Test that get_service_logger returns properly namespaced logger."""
        logger = get_service_logger("test_service")
        assert logger.name == "the_alchemiser.services.test_service"

    def test_get_service_logger_consistent_instances(self):
        """Test that repeated calls return the same logger instance."""
        logger1 = get_service_logger("test_service")
        logger2 = get_service_logger("test_service")
        assert logger1 is logger2


class TestIntegrationWithMainLoggingConfig:
    """Integration tests with main application logging configuration."""

    def test_production_environment_detection(self):
        """Test that production environment is detected correctly."""
        with patch.dict(os.environ, {"AWS_LAMBDA_FUNCTION_NAME": "test-lambda"}):
            from the_alchemiser.main import configure_application_logging

            # Should not raise an exception
            configure_application_logging()

    def test_development_environment_detection(self):
        """Test that development environment preserves CLI handlers."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove AWS_LAMBDA_FUNCTION_NAME if it exists
            os.environ.pop("AWS_LAMBDA_FUNCTION_NAME", None)

            from the_alchemiser.main import configure_application_logging

            # Add a mock CLI handler
            root_logger = logging.getLogger()
            cli_handler = logging.StreamHandler()
            root_logger.addHandler(cli_handler)

            # Should preserve the CLI handler
            configure_application_logging()
            assert cli_handler in root_logger.handlers


class TestProductionJSONValidation:
    """Test JSON payload validation for production logs."""

    def test_production_json_contains_all_required_fields(self):
        """Test that production logs contain all required fields."""
        # Setup production-style logging
        setup_logging(
            log_level=logging.INFO,
            structured_format=True,
            respect_existing_handlers=False,
        )

        # Set context vars
        set_request_id("prod-req-789")
        set_error_id("prod-err-012")

        # Capture log output
        import io
        log_capture = io.StringIO()

        # Create a test logger with custom handler
        test_logger = logging.getLogger("test.production.validation")
        handler = logging.StreamHandler(log_capture)
        handler.setFormatter(StructuredFormatter())
        test_logger.addHandler(handler)
        test_logger.setLevel(logging.INFO)

        # Log a message
        test_logger.info("Production test message")

        # Parse the JSON output
        log_output = log_capture.getvalue().strip()
        log_data = json.loads(log_output)

        # Verify all required fields are present
        required_fields = [
            "timestamp", "level", "logger", "message",
            "module", "function", "line", "request_id", "error_id"
        ]
        for field in required_fields:
            assert field in log_data, f"Required field '{field}' missing from log output"

        # Verify specific values
        assert log_data["level"] == "INFO"
        assert log_data["message"] == "Production test message"
        assert log_data["request_id"] == "prod-req-789"
        assert log_data["error_id"] == "prod-err-012"

        # Clean up
        set_request_id(None)
        set_error_id(None)
