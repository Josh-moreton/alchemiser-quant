"""Tests for structlog trading helpers."""

from __future__ import annotations

import logging
from decimal import Decimal
from io import StringIO
from unittest.mock import patch

import pytest

from the_alchemiser.shared.logging.structlog_config import (
    configure_structlog,
    get_structlog_logger,
)
from the_alchemiser.shared.logging.structlog_trading import (
    bind_trading_context,
    log_data_integrity_checkpoint,
    log_order_flow,
    log_repeg_operation,
    log_trade_event,
)


def _assert_contains(text: str, expected: list[str]) -> None:
    for part in expected:
        assert part in text


@pytest.fixture
def _setup_structlog() -> None:
    """Set up structlog for tests that need it outside of patching.

    Note: Most tests should configure structlog inside the patch context manager
    to ensure output is captured correctly.
    """
    configure_structlog(console_level=logging.DEBUG, file_level=logging.DEBUG)


def test_log_trade_event_basic() -> None:
    """Test that log_trade_event logs with proper structure."""
    with patch("sys.stdout", new=StringIO()) as fake_out:
        configure_structlog(console_level=logging.DEBUG, file_level=logging.DEBUG)
        logger = get_structlog_logger(__name__)
        log_trade_event(logger, "order_placed", "AAPL", quantity=100, price=Decimal("150.25"))

        output = fake_out.getvalue()
        _assert_contains(
            output,
            [
                "Trading event",
                "event_type='order_placed'",
                "symbol='AAPL'",
                "quantity=100",
                "price='150.25'",
            ],
        )


def test_log_order_flow_with_all_fields() -> None:
    """Test log_order_flow with all optional fields."""
    with patch("sys.stdout", new=StringIO()) as fake_out:
        configure_structlog(console_level=logging.DEBUG, file_level=logging.DEBUG)
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
        _assert_contains(
            output,
            [
                "Order flow",
                "stage='filled'",
                "symbol='TSLA'",
                "quantity='50'",
                "price='250.00'",
                "order_id='ord-123'",
                "broker='alpaca'",
            ],
        )


def test_log_order_flow_without_optional_fields() -> None:
    """Test log_order_flow without optional fields."""
    with patch("sys.stdout", new=StringIO()) as fake_out:
        configure_structlog(console_level=logging.DEBUG, file_level=logging.DEBUG)
        logger = get_structlog_logger(__name__)
        log_order_flow(logger, stage="submission", symbol="GOOG", quantity=Decimal("25"))

        output = fake_out.getvalue()
        _assert_contains(
            output,
            ["Order flow", "stage='submission'", "symbol='GOOG'", "quantity='25'"],
        )
        assert "price=" not in output
        assert "order_id=" not in output


def test_log_repeg_operation() -> None:
    """Test log_repeg_operation with price improvement calculation."""
    with patch("sys.stdout", new=StringIO()) as fake_out:
        configure_structlog(console_level=logging.DEBUG, file_level=logging.DEBUG)
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
        _assert_contains(
            output,
            [
                "Repeg operation",
                "operation='replace_order'",
                "symbol='NVDA'",
                "old_price='500.00'",
                "new_price='505.00'",
                "quantity='10'",
                "reason='market_movement'",
                "price_improvement='5.00'",
                "order_id='old-123'",
            ],
        )


def test_bind_trading_context_all_fields() -> None:
    """Test bind_trading_context with all fields."""
    with patch("sys.stdout", new=StringIO()) as fake_out:
        configure_structlog(console_level=logging.DEBUG, file_level=logging.DEBUG)
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
        _assert_contains(
            output,
            [
                "symbol='MSFT'",
                "strategy='momentum'",
                "portfolio='tech'",
                "order_id='ord-456'",
                "test event",
            ],
        )


def test_bind_trading_context_partial_fields() -> None:
    """Test bind_trading_context with only some fields."""
    with patch("sys.stdout", new=StringIO()) as fake_out:
        configure_structlog(console_level=logging.DEBUG, file_level=logging.DEBUG)
        logger = get_structlog_logger(__name__)
        bound_logger = bind_trading_context(logger, symbol="AMZN", strategy="value")

        bound_logger.info("partial context")

        output = fake_out.getvalue()
        _assert_contains(output, ["symbol='AMZN'", "strategy='value'", "partial context"])
        assert "portfolio=" not in output
        assert "order_id=" not in output


def test_log_data_integrity_checkpoint_with_valid_data() -> None:
    """Test log_data_integrity_checkpoint with valid data."""
    data = {"AAPL": 0.3, "MSFT": 0.3, "GOOG": 0.4}

    with patch("sys.stdout", new=StringIO()) as fake_out:
        configure_structlog(console_level=logging.DEBUG, file_level=logging.DEBUG)
        logger = get_structlog_logger(__name__)
        log_data_integrity_checkpoint(
            logger, stage="portfolio_allocation", data=data, context="rebalance"
        )

        output = fake_out.getvalue()
        _assert_contains(
            output,
            [
                "Data transfer checkpoint",
                "stage='portfolio_allocation'",
                "context='rebalance'",
                "data_count=3",
            ],
        )


def test_log_data_integrity_checkpoint_with_null_data() -> None:
    """Test log_data_integrity_checkpoint with null data."""
    with patch("sys.stdout", new=StringIO()) as fake_out:
        configure_structlog(console_level=logging.DEBUG, file_level=logging.DEBUG)
        logger = get_structlog_logger(__name__)
        log_data_integrity_checkpoint(logger, stage="data_fetch", data=None, context="API call")

        output = fake_out.getvalue()
        _assert_contains(
            output,
            [
                "Data integrity violation",
                "stage='data_fetch'",
                "issue='null_data_detected'",
                "context='API call'",
            ],
        )


def test_log_data_integrity_checkpoint_warns_on_empty_data() -> None:
    """Test log_data_integrity_checkpoint warns on empty data."""
    data: dict[str, float] = {}

    with patch("sys.stdout", new=StringIO()) as fake_out:
        configure_structlog(console_level=logging.DEBUG, file_level=logging.DEBUG)
        logger = get_structlog_logger(__name__)
        log_data_integrity_checkpoint(logger, stage="processing", data=data)

        output = fake_out.getvalue()
        lines = output.strip().split("\n")

        assert len(lines) >= 2, f"Expected at least 2 log lines, got {len(lines)}"

        _assert_contains(lines[0], ["Data transfer checkpoint", "data_count=0"])
        assert "Empty data detected" in lines[1]


def test_log_data_integrity_checkpoint_warns_on_allocation_anomaly() -> None:
    """Test log_data_integrity_checkpoint warns on portfolio allocation anomaly."""
    # Sum is 0.8, not close to 1.0
    data = {"AAPL": 0.3, "MSFT": 0.5}

    with patch("sys.stdout", new=StringIO()) as fake_out:
        configure_structlog(console_level=logging.DEBUG, file_level=logging.DEBUG)
        logger = get_structlog_logger(__name__)
        log_data_integrity_checkpoint(logger, stage="allocation", data=data)

        output = fake_out.getvalue()
        lines = output.strip().split("\n")

        assert len(lines) == 2

        _assert_contains(lines[0], ["Data transfer checkpoint", "data_checksum=0.8"])
        _assert_contains(lines[1], ["Portfolio allocation anomaly", "allocation_sum=0.8"])


def test_log_data_integrity_checkpoint_with_decimal_values() -> None:
    """Test log_data_integrity_checkpoint with Decimal values."""
    data = {
        "AAPL": Decimal("0.33"),
        "MSFT": Decimal("0.33"),
        "GOOG": Decimal("0.34"),
    }

    with patch("sys.stdout", new=StringIO()) as fake_out:
        configure_structlog(console_level=logging.DEBUG, file_level=logging.DEBUG)
        logger = get_structlog_logger(__name__)
        log_data_integrity_checkpoint(logger, stage="allocation", data=data)

        output = fake_out.getvalue()
        _assert_contains(output, ["Data transfer checkpoint", "data_count=3"])
