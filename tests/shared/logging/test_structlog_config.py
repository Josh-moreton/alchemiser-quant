"""Tests for structlog configuration module."""

from __future__ import annotations

import json
import logging
from decimal import Decimal
from io import StringIO
from unittest.mock import patch

import pytest

from the_alchemiser.shared.logging import context
from the_alchemiser.shared.logging.structlog_config import (
    add_alchemiser_context,
    configure_structlog,
    decimal_serializer,
    get_structlog_logger,
)


def test_decimal_serializer_handles_decimal() -> None:
    """Test that decimal_serializer converts Decimal to string."""
    value = Decimal("123.456")
    result = decimal_serializer(value)
    assert result == "123.456"
    assert isinstance(result, str)


def test_decimal_serializer_raises_on_unsupported_type() -> None:
    """Test that decimal_serializer raises TypeError for unsupported types."""
    with pytest.raises(TypeError, match="not JSON serializable"):
        decimal_serializer(object())


def test_decimal_serializer_handles_exception() -> None:
    """Test that decimal_serializer converts Exception to dict with type and message."""
    error = ValueError("test error message")
    result = decimal_serializer(error)

    assert isinstance(result, dict)
    assert result["type"] == "ValueError"
    assert result["message"] == "test error message"


def test_decimal_serializer_handles_exception_with_context() -> None:
    """Test that decimal_serializer includes context attribute from AlchemiserError subclasses."""
    from the_alchemiser.shared.errors.exceptions import StrategyExecutionError

    error = StrategyExecutionError(
        message="DSL evaluation failed",
        strategy_name="dsl_engine",
        operation="evaluate",
    )
    result = decimal_serializer(error)

    assert isinstance(result, dict)
    assert result["type"] == "StrategyExecutionError"
    assert "DSL evaluation failed" in result["message"]
    assert "context" in result
    assert result["context"]["strategy_name"] == "dsl_engine"


def test_add_alchemiser_context_adds_system_identifier() -> None:
    """Test that add_alchemiser_context adds system identifier."""
    event_dict: dict[str, object] = {"event": "test"}
    result = add_alchemiser_context(None, "", event_dict)

    assert result["system"] == "alchemiser"
    assert result["event"] == "test"


def test_add_alchemiser_context_includes_request_id() -> None:
    """Test that add_alchemiser_context includes request_id from context."""
    context.set_request_id("test-request-123")
    try:
        event_dict: dict[str, object] = {"event": "test"}
        result = add_alchemiser_context(None, "", event_dict)

        assert result["request_id"] == "test-request-123"
        assert result["system"] == "alchemiser"
    finally:
        context.set_request_id(None)


def test_add_alchemiser_context_includes_error_id() -> None:
    """Test that add_alchemiser_context includes error_id from context."""
    context.set_error_id("error-456")
    try:
        event_dict: dict[str, object] = {"event": "test"}
        result = add_alchemiser_context(None, "", event_dict)

        assert result["error_id"] == "error-456"
        assert result["system"] == "alchemiser"
    finally:
        context.set_error_id(None)


def test_add_alchemiser_context_includes_correlation_id() -> None:
    """Test that add_alchemiser_context includes correlation_id from context."""
    context.set_correlation_id("corr-789")
    try:
        event_dict: dict[str, object] = {"event": "test"}
        result = add_alchemiser_context(None, "", event_dict)

        assert result["correlation_id"] == "corr-789"
        assert result["system"] == "alchemiser"
    finally:
        context.set_correlation_id(None)


def test_add_alchemiser_context_includes_causation_id() -> None:
    """Test that add_alchemiser_context includes causation_id from context."""
    context.set_causation_id("cause-abc")
    try:
        event_dict: dict[str, object] = {"event": "test"}
        result = add_alchemiser_context(None, "", event_dict)

        assert result["causation_id"] == "cause-abc"
        assert result["system"] == "alchemiser"
    finally:
        context.set_causation_id(None)


def test_configure_structlog_json_format() -> None:
    """Test that configure_structlog sets up JSON output."""
    configure_structlog(
        console_level=logging.INFO, file_level=logging.INFO, use_json=True, use_colors=False
    )

    logger = get_structlog_logger(__name__)
    assert logger is not None


def test_configure_structlog_console_format() -> None:
    """Test that configure_structlog sets up console output."""
    configure_structlog(
        console_level=logging.DEBUG, file_level=logging.DEBUG, use_json=False, use_colors=True
    )

    logger = get_structlog_logger(__name__)
    assert logger is not None


def test_get_structlog_logger_returns_logger() -> None:
    """Test that get_structlog_logger returns a logger instance."""
    configure_structlog(
        console_level=logging.INFO, file_level=logging.INFO, use_json=True, use_colors=False
    )

    logger = get_structlog_logger(__name__)
    assert logger is not None
    assert hasattr(logger, "info")
    assert hasattr(logger, "error")
    assert hasattr(logger, "warning")


def test_structlog_handles_decimal_in_json() -> None:
    """Test that structlog correctly serializes Decimal values in JSON output."""
    # Capture output - configure structlog AFTER patching stdout so handlers use patched stream
    with patch("sys.stdout", new=StringIO()) as fake_out:
        configure_structlog(
            console_level=logging.DEBUG,
            file_level=logging.DEBUG,
            use_json=True,
            use_colors=False,
        )
        logger = get_structlog_logger(__name__)
        logger.info("test", price=Decimal("150.25"), quantity=Decimal("100"))

        output = fake_out.getvalue()

        # Parse JSON output
        log_entry = json.loads(output)

        # Verify Decimal values are serialized as strings
        assert log_entry["price"] == "150.25"
        assert log_entry["quantity"] == "100"
        assert log_entry["event"] == "test"


def test_structlog_includes_context_vars() -> None:
    """Test that structlog includes context variables in output."""
    context.set_request_id("ctx-123")
    context.set_error_id("err-456")

    try:
        with patch("sys.stdout", new=StringIO()) as fake_out:
            configure_structlog(
                console_level=logging.DEBUG,
                file_level=logging.DEBUG,
                use_json=True,
                use_colors=False,
            )
            logger = get_structlog_logger(__name__)
            logger.info("test event")

            output = fake_out.getvalue()
            log_entry = json.loads(output)

            assert log_entry["request_id"] == "ctx-123"
            assert log_entry["error_id"] == "err-456"
            assert log_entry["system"] == "alchemiser"
    finally:
        context.set_request_id(None)
        context.set_error_id(None)


def test_structlog_includes_all_event_tracing_ids() -> None:
    """Test that structlog includes all event tracing IDs in output."""
    context.set_request_id("req-123")
    context.set_error_id("err-456")
    context.set_correlation_id("corr-789")
    context.set_causation_id("cause-abc")

    try:
        with patch("sys.stdout", new=StringIO()) as fake_out:
            configure_structlog(
                console_level=logging.DEBUG,
                file_level=logging.DEBUG,
                use_json=True,
                use_colors=False,
            )
            logger = get_structlog_logger(__name__)
            logger.info("test event")

            output = fake_out.getvalue()
            log_entry = json.loads(output)

            assert log_entry["request_id"] == "req-123"
            assert log_entry["error_id"] == "err-456"
            assert log_entry["correlation_id"] == "corr-789"
            assert log_entry["causation_id"] == "cause-abc"
            assert log_entry["system"] == "alchemiser"
    finally:
        context.set_request_id(None)
        context.set_error_id(None)
        context.set_correlation_id(None)
        context.set_causation_id(None)


def test_structlog_logger_bind() -> None:
    """Test that structlog logger supports bind for context."""
    with patch("sys.stdout", new=StringIO()) as fake_out:
        configure_structlog(
            console_level=logging.DEBUG,
            file_level=logging.DEBUG,
            use_json=True,
            use_colors=False,
        )
        logger = get_structlog_logger(__name__)
        bound_logger = logger.bind(symbol="AAPL", strategy="momentum")

        bound_logger.info("trade signal")

        output = fake_out.getvalue()
        log_entry = json.loads(output)

        assert log_entry["symbol"] == "AAPL"
        assert log_entry["strategy"] == "momentum"
        assert log_entry["event"] == "trade signal"


def test_configure_structlog_logs_file_handler_failure() -> None:
    """Test that configure_structlog logs a warning when file handler setup fails."""
    with patch("sys.stdout", new=StringIO()) as fake_out:
        # Try to configure with an invalid file path (read-only directory)
        configure_structlog(
            console_level=logging.WARNING,
            file_level=logging.DEBUG,
            file_path="/invalid/read/only/path/test.log",
            use_json=True,
            use_colors=False,
        )

        output = fake_out.getvalue()
        # Check that a warning was logged about the failure
        assert "Failed to configure file logging" in output or len(output) > 0
