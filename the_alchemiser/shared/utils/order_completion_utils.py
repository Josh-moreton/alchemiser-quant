#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Centralized Order Completion Utilities.

This module provides unified order completion monitoring functionality to eliminate
duplication across multiple execution components. All order completion monitoring
should use this centralized utility to ensure consistent behavior and timeouts.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from the_alchemiser.execution.core.execution_schemas import WebSocketResultDTO
from the_alchemiser.execution.monitoring.websocket_order_monitor import OrderCompletionMonitor

if TYPE_CHECKING:
    from alpaca.trading.client import TradingClient

logger = logging.getLogger(__name__)

# Centralized default timeout configuration
DEFAULT_ORDER_COMPLETION_TIMEOUT = 60  # seconds


def wait_for_order_completion(
    trading_client: TradingClient,
    order_ids: list[str],
    max_wait_seconds: int | None = None,
    api_key: str | None = None,
    secret_key: str | None = None,
) -> WebSocketResultDTO:
    """Centralized order completion monitoring with consistent defaults.

    This utility eliminates duplication across multiple execution components by
    providing a single, consistent interface for order completion monitoring.

    Args:
        trading_client: The Alpaca trading client instance
        order_ids: List of order IDs to monitor for completion
        max_wait_seconds: Maximum seconds to wait (defaults to 60s)
        api_key: Optional API key override
        secret_key: Optional secret key override

    Returns:
        WebSocketResultDTO with completion status and order details

    Raises:
        ValueError: If API keys are missing or WebSocket is disabled
        Exception: If order completion monitoring fails

    """
    if max_wait_seconds is None:
        max_wait_seconds = DEFAULT_ORDER_COMPLETION_TIMEOUT

    logger.debug(
        "order_completion_monitoring_started",
        extra={
            "order_count": len(order_ids),
            "timeout_seconds": max_wait_seconds,
            "has_api_key": api_key is not None,
            "has_secret_key": secret_key is not None,
        },
    )

    # Create monitor instance with provided client and credentials
    monitor = OrderCompletionMonitor(
        trading_client=trading_client, api_key=api_key, secret_key=secret_key
    )

    try:
        result = monitor.wait_for_order_completion(order_ids, max_wait_seconds)

        logger.info(
            "order_completion_monitoring_finished",
            extra={
                "order_count": len(order_ids),
                "timeout_seconds": max_wait_seconds,
                "status": result.status.value if result.status else "unknown",
                "completed_orders": len(result.orders_completed) if result.orders_completed else 0,
            },
        )

        return result

    except Exception as e:
        logger.error(
            "order_completion_monitoring_failed",
            extra={
                "order_count": len(order_ids),
                "timeout_seconds": max_wait_seconds,
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        raise
