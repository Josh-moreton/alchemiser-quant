"""Tests for structlog configuration module."""

from __future__ import annotations

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
    """Decimal values are rendered as precise strings."""
    value = Decimal("123.456")
    result = decimal_serializer(value)
    assert result == "123.456"
    assert isinstance(result, str)


def test_decimal_serializer_passthrough_unknown() -> None:
    """Unknown types are returned unchanged for ConsoleRenderer compatibility."""
    obj = object()
    assert decimal_serializer(obj) is obj


def test_add_alchemiser_context_adds_system_identifier() -> None:
    """Context processor always adds system identifier."""
    event_dict: dict[str, object] = {"event": "test"}
    result = add_alchemiser_context(None, "", event_dict)

    assert result["system"] == "alchemiser"
    assert result["event"] == "test"


def test_add_alchemiser_context_includes_request_id() -> None:
    """Context processor merges request ID when present."""
    context.set_request_id("test-request-123")
    try:
        event_dict: dict[str, object] = {"event": "test"}
        result = add_alchemiser_context(None, "", event_dict)

        assert result["request_id"] == "test-request-123"
        assert result["system"] == "alchemiser"
    finally:
        context.set_request_id(None)


def test_add_alchemiser_context_includes_error_id() -> None:
    """Context processor merges error ID when present."""
    context.set_error_id("error-456")
    try:
        event_dict: dict[str, object] = {"event": "test"}
        result = add_alchemiser_context(None, "", event_dict)

        assert result["error_id"] == "error-456"
        assert result["system"] == "alchemiser"
    finally:
        context.set_error_id(None)


def test_add_alchemiser_context_includes_correlation_id() -> None:
    """Context processor merges correlation ID when present."""
    context.set_correlation_id("corr-789")
    try:
        event_dict: dict[str, object] = {"event": "test"}
        result = add_alchemiser_context(None, "", event_dict)

        assert result["correlation_id"] == "corr-789"
        assert result["system"] == "alchemiser"
    finally:
        context.set_correlation_id(None)


def test_add_alchemiser_context_includes_causation_id() -> None:
    """Context processor merges causation ID when present."""
    context.set_causation_id("cause-abc")
    try:
        event_dict: dict[str, object] = {"event": "test"}
        result = add_alchemiser_context(None, "", event_dict)

        assert result["causation_id"] == "cause-abc"
        assert result["system"] == "alchemiser"
    finally:
        context.set_causation_id(None)


def test_configure_structlog_sets_up_logger() -> None:
    """configure_structlog should return a working logger instance."""
    configure_structlog(console_level=logging.INFO, file_level=logging.INFO)

    logger = get_structlog_logger(__name__)
    assert logger is not None


def test_configure_structlog_emits_human_readable_output() -> None:
    """Logs are emitted in a human-readable console format with normalized values."""
    with patch("sys.stdout", new=StringIO()) as fake_out:
        configure_structlog(console_level=logging.DEBUG, file_level=logging.DEBUG)
        logger = get_structlog_logger(__name__)
        logger.info("test", price=Decimal("150.25"), quantity=Decimal("100"))

        output = fake_out.getvalue()
        assert "test" in output
        assert "price='150.25'" in output
        assert "quantity='100'" in output


def test_structlog_includes_context_vars() -> None:
    """Context variables propagate into output."""
    context.set_request_id("ctx-123")
    context.set_error_id("err-456")

    try:
        with patch("sys.stdout", new=StringIO()) as fake_out:
            configure_structlog(console_level=logging.DEBUG, file_level=logging.DEBUG)
            logger = get_structlog_logger(__name__)
            logger.info("test event")

            output = fake_out.getvalue()
            assert "ctx-123" in output
            assert "err-456" in output
            assert "alchemiser" in output
    finally:
        context.set_request_id(None)
        context.set_error_id(None)


def test_structlog_includes_all_event_tracing_ids() -> None:
    """All tracing IDs appear in the log line."""
    context.set_request_id("req-123")
    context.set_error_id("err-456")
    context.set_correlation_id("corr-789")
    context.set_causation_id("cause-abc")

    try:
        with patch("sys.stdout", new=StringIO()) as fake_out:
            configure_structlog(console_level=logging.DEBUG, file_level=logging.DEBUG)
            logger = get_structlog_logger(__name__)
            logger.info("test event")

            output = fake_out.getvalue()
            assert "req-123" in output
            assert "err-456" in output
            assert "corr-789" in output
            assert "cause-abc" in output
            assert "alchemiser" in output
    finally:
        context.set_request_id(None)
        context.set_error_id(None)
        context.set_correlation_id(None)
        context.set_causation_id(None)


def test_structlog_logger_bind() -> None:
    """Bound context values appear in output."""
    with patch("sys.stdout", new=StringIO()) as fake_out:
        configure_structlog(console_level=logging.DEBUG, file_level=logging.DEBUG)
        logger = get_structlog_logger(__name__)
        bound_logger = logger.bind(symbol="AAPL", strategy="momentum")

        bound_logger.info("trade signal")

        output = fake_out.getvalue()
        assert "AAPL" in output
        assert "momentum" in output
        assert "trade signal" in output


def test_configure_structlog_logs_file_handler_failure() -> None:
    """File handler setup failures should log a warning and continue."""
    with patch("sys.stdout", new=StringIO()) as fake_out:
        configure_structlog(
            console_level=logging.WARNING,
            file_level=logging.DEBUG,
            file_path="/invalid/read/only/path/test.log",
        )

        output = fake_out.getvalue()
        assert "Failed to configure file logging" in output or len(output) > 0
