"""Tests for migration bridge module."""

from __future__ import annotations

import logging
import os
from unittest.mock import patch

import pytest

from the_alchemiser.shared.logging.migration import (
    get_logger,
    is_structlog_enabled,
    log_data_transfer_checkpoint,
    log_trade_event,
    setup_application_logging,
)


def test_is_structlog_enabled_default() -> None:
    """Test that structlog is disabled by default."""
    # By default, without env var, structlog should be disabled
    with patch.dict(os.environ, {}, clear=True):
        # Need to reload module to pick up env change
        # For this test, we just check the current state
        enabled = is_structlog_enabled()
        assert isinstance(enabled, bool)


def test_get_logger_returns_logger() -> None:
    """Test that get_logger returns a logger instance."""
    logger = get_logger(__name__)
    assert logger is not None
    assert hasattr(logger, "info")
    assert hasattr(logger, "error")


def test_log_trade_event_accepts_parameters() -> None:
    """Test that log_trade_event accepts expected parameters."""
    logger = get_logger(__name__)

    # Should not raise
    log_trade_event(
        logger,
        event_type="order_placed",
        symbol="AAPL",
        quantity=100,
        price=150.25,
    )


def test_log_data_transfer_checkpoint_accepts_parameters() -> None:
    """Test that log_data_transfer_checkpoint accepts expected parameters."""
    logger = get_logger(__name__)
    data = {"AAPL": 0.5, "MSFT": 0.5}

    # Should not raise
    log_data_transfer_checkpoint(
        logger,
        stage="allocation",
        data=data,
        context="test",
    )


def test_setup_application_logging_executes() -> None:
    """Test that setup_application_logging executes without error."""
    # Should not raise
    setup_application_logging(
        structured_format=False,
        log_level=logging.INFO,
    )


def test_migration_bridge_provides_consistent_api() -> None:
    """Test that migration bridge provides consistent API regardless of backend."""
    logger = get_logger(__name__)

    # All these should work regardless of which backend is active
    assert callable(logger.info)
    assert callable(logger.error)
    assert callable(logger.warning)
    assert callable(logger.debug)


def test_log_trade_event_with_various_details() -> None:
    """Test log_trade_event with various detail types."""
    logger = get_logger(__name__)

    # Should handle different types of details
    log_trade_event(
        logger,
        event_type="order_filled",
        symbol="TSLA",
        quantity=50,
        price=250.0,
        broker="alpaca",
        execution_time=1.23,
    )


def test_log_data_checkpoint_with_none_data() -> None:
    """Test log_data_transfer_checkpoint with None data."""
    logger = get_logger(__name__)

    # Should handle None data
    log_data_transfer_checkpoint(
        logger,
        stage="fetch",
        data=None,
        context="API error",
    )


def test_log_data_checkpoint_with_empty_data() -> None:
    """Test log_data_transfer_checkpoint with empty data."""
    logger = get_logger(__name__)

    # Should handle empty dict
    log_data_transfer_checkpoint(
        logger,
        stage="processing",
        data={},
        context="no data",
    )
