"""Tests for structlog trading helpers."""

from __future__ import annotations

import json
import logging
from decimal import Decimal
from io import StringIO
from unittest.mock import patch

import pytest

from the_alchemiser.shared.logging.structlog_config import (
    configure_structlog_lambda,
    get_structlog_logger,
)
from the_alchemiser.shared.logging.structlog_trading import (
    bind_trading_context,
    log_data_integrity_checkpoint,
    log_order_flow,
    log_repeg_operation,
    log_trade_event,
)


@pytest.fixture
def _setup_structlog() -> None:
    """Set up structlog for tests that need it outside of patching.

    Note: Most tests should configure structlog inside the patch context manager
    to ensure output is captured correctly.
    """
    configure_structlog_lambda()


def test_log_trade_event_basic() -> None:
    """Test that log_trade_event logs with proper structure."""
    with patch("sys.stdout", new=StringIO()) as fake_out:
        configure_structlog_lambda()
        logger = get_structlog_logger(__name__)
        log_trade_event(logger, "order_placed", "AAPL", quantity=100, price=Decimal("150.25"))

        output = fake_out.getvalue()
        log_entry = json.loads(output)

        assert log_entry["event"] == "Trading event"
        assert log_entry["event_type"] == "order_placed"
        assert log_entry["symbol"] == "AAPL"
        assert log_entry["quantity"] == 100
        assert log_entry["price"] == "150.25"
        assert "timestamp" in log_entry


def test_log_order_flow_with_all_fields() -> None:
    """Test log_order_flow with all optional fields."""
    with patch("sys.stdout", new=StringIO()) as fake_out:
        configure_structlog_lambda()
        logger = get_structlog_logger(__name__)
        log_order_flow(
            logger,
            stage="filled",
            symbol="TSLA",
            quantity=Decimal("50"),
            price=Decimal("250.00"),
            order_id="ord-123",
            broker="alpaca",
        )

        output = fake_out.getvalue()
        log_entry = json.loads(output)

        assert log_entry["event"] == "Order flow"
        assert log_entry["stage"] == "filled"
        assert log_entry["symbol"] == "TSLA"
        assert log_entry["quantity"] == "50"
        assert log_entry["price"] == "250.00"
        assert log_entry["order_id"] == "ord-123"
        assert log_entry["broker"] == "alpaca"


def test_log_order_flow_without_optional_fields() -> None:
    """Test log_order_flow without optional fields."""
    with patch("sys.stdout", new=StringIO()) as fake_out:
        configure_structlog_lambda()
        logger = get_structlog_logger(__name__)
        log_order_flow(logger, stage="submission", symbol="GOOG", quantity=Decimal("25"))

        output = fake_out.getvalue()
        log_entry = json.loads(output)

        assert log_entry["event"] == "Order flow"
        assert log_entry["stage"] == "submission"
        assert log_entry["symbol"] == "GOOG"
        assert log_entry["quantity"] == "25"
        assert "price" not in log_entry
        assert "order_id" not in log_entry


def test_log_repeg_operation() -> None:
    """Test log_repeg_operation with price improvement calculation."""
    with patch("sys.stdout", new=StringIO()) as fake_out:
        configure_structlog_lambda()
        logger = get_structlog_logger(__name__)
        log_repeg_operation(
            logger,
            operation="replace_order",
            symbol="NVDA",
            old_price=Decimal("500.00"),
            new_price=Decimal("505.00"),
            quantity=Decimal("10"),
            reason="market_movement",
            order_id="old-123",
        )

        output = fake_out.getvalue()
        log_entry = json.loads(output)

        assert log_entry["event"] == "Repeg operation"
        assert log_entry["operation"] == "replace_order"
        assert log_entry["symbol"] == "NVDA"
        assert log_entry["old_price"] == "500.00"
        assert log_entry["new_price"] == "505.00"
        assert log_entry["quantity"] == "10"
        assert log_entry["reason"] == "market_movement"
        assert log_entry["price_improvement"] == "5.00"
        assert log_entry["order_id"] == "old-123"


def test_bind_trading_context_all_fields() -> None:
    """Test bind_trading_context with all fields."""
    with patch("sys.stdout", new=StringIO()) as fake_out:
        configure_structlog_lambda()
        logger = get_structlog_logger(__name__)
        bound_logger = bind_trading_context(
            logger,
            symbol="MSFT",
            strategy="momentum",
            portfolio="tech",
            order_id="ord-456",
        )

        bound_logger.info("test event")

        output = fake_out.getvalue()
        log_entry = json.loads(output)

        assert log_entry["symbol"] == "MSFT"
        assert log_entry["strategy"] == "momentum"
        assert log_entry["portfolio"] == "tech"
        assert log_entry["order_id"] == "ord-456"
        assert log_entry["event"] == "test event"


def test_bind_trading_context_partial_fields() -> None:
    """Test bind_trading_context with only some fields."""
    with patch("sys.stdout", new=StringIO()) as fake_out:
        configure_structlog_lambda()
        logger = get_structlog_logger(__name__)
        bound_logger = bind_trading_context(logger, symbol="AMZN", strategy="value")

        bound_logger.info("partial context")

        output = fake_out.getvalue()
        log_entry = json.loads(output)

        assert log_entry["symbol"] == "AMZN"
        assert log_entry["strategy"] == "value"
        assert "portfolio" not in log_entry
        assert "order_id" not in log_entry


def test_log_data_integrity_checkpoint_with_valid_data() -> None:
    """Test log_data_integrity_checkpoint with valid data."""
    data = {"AAPL": 0.3, "MSFT": 0.3, "GOOG": 0.4}

    with patch("sys.stdout", new=StringIO()) as fake_out:
        configure_structlog_lambda()
        logger = get_structlog_logger(__name__)
        log_data_integrity_checkpoint(
            logger, stage="portfolio_allocation", data=data, context="rebalance"
        )

        output = fake_out.getvalue()
        log_entry = json.loads(output)

        assert log_entry["event"] == "Data transfer checkpoint"
        assert log_entry["stage"] == "portfolio_allocation"
        assert log_entry["context"] == "rebalance"
        assert log_entry["data_count"] == 3
        assert log_entry["data_checksum"] == pytest.approx(1.0, rel=0, abs=1e-6)
        assert log_entry["data_sample"] == {"AAPL": 0.3, "MSFT": 0.3, "GOOG": 0.4}


def test_log_data_integrity_checkpoint_with_null_data() -> None:
    """Test log_data_integrity_checkpoint with null data."""
    with patch("sys.stdout", new=StringIO()) as fake_out:
        configure_structlog_lambda()
        logger = get_structlog_logger(__name__)
        log_data_integrity_checkpoint(logger, stage="data_fetch", data=None, context="API call")

        output = fake_out.getvalue()
        log_entry = json.loads(output)

        assert log_entry["event"] == "Data integrity violation"
        assert log_entry["stage"] == "data_fetch"
        assert log_entry["issue"] == "null_data_detected"
        assert log_entry["context"] == "API call"


def test_log_data_integrity_checkpoint_warns_on_empty_data() -> None:
    """Test log_data_integrity_checkpoint warns on empty data."""
    data: dict[str, float] = {}

    with patch("sys.stdout", new=StringIO()) as fake_out:
        configure_structlog_lambda()
        logger = get_structlog_logger(__name__)
        log_data_integrity_checkpoint(logger, stage="processing", data=data)

        output = fake_out.getvalue()
        lines = output.strip().split("\n")

        # First line is checkpoint, subsequent lines are warnings
        # Empty data triggers both empty warning and allocation warning (sum is 0.0, not 1.0)
        assert len(lines) >= 2, f"Expected at least 2 log lines, got {len(lines)}"

        checkpoint = json.loads(lines[0])
        warning = json.loads(lines[1])

        assert checkpoint["event"] == "Data transfer checkpoint"
        assert checkpoint["data_count"] == 0
        assert warning["event"] == "Empty data detected"


def test_log_data_integrity_checkpoint_warns_on_allocation_anomaly() -> None:
    """Test log_data_integrity_checkpoint warns on portfolio allocation anomaly."""
    # Sum is 0.8, not close to 1.0
    data = {"AAPL": 0.3, "MSFT": 0.5}

    with patch("sys.stdout", new=StringIO()) as fake_out:
        configure_structlog_lambda()
        logger = get_structlog_logger(__name__)
        log_data_integrity_checkpoint(logger, stage="allocation", data=data)

        output = fake_out.getvalue()
        lines = output.strip().split("\n")

        # First line is checkpoint, second is warning
        assert len(lines) == 2

        checkpoint = json.loads(lines[0])
        warning = json.loads(lines[1])

        assert checkpoint["event"] == "Data transfer checkpoint"
        assert checkpoint["data_checksum"] == pytest.approx(0.8, rel=0, abs=1e-6)
        assert warning["event"] == "Portfolio allocation anomaly"
        assert warning["allocation_sum"] == pytest.approx(0.8, rel=0, abs=1e-6)
        assert warning["expected_sum"] == 1.0


def test_log_data_integrity_checkpoint_with_decimal_values() -> None:
    """Test log_data_integrity_checkpoint with Decimal values."""
    data = {
        "AAPL": Decimal("0.33"),
        "MSFT": Decimal("0.33"),
        "GOOG": Decimal("0.34"),
    }

    with patch("sys.stdout", new=StringIO()) as fake_out:
        configure_structlog_lambda()
        logger = get_structlog_logger(__name__)
        log_data_integrity_checkpoint(logger, stage="allocation", data=data)

        output = fake_out.getvalue()
        log_entry = json.loads(output)

        assert log_entry["event"] == "Data transfer checkpoint"
        assert log_entry["data_count"] == 3
        assert abs(log_entry["data_checksum"] - 1.0) < 0.01
