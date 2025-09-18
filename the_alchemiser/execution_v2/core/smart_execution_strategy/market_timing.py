"""Business Unit: execution | Status: current.

Market timing logic for smart execution strategy.

This module handles market timing restrictions and validation to ensure orders
are placed at appropriate times relative to market conditions.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from datetime import time as dt_time
from zoneinfo import ZoneInfo

from .models import ExecutionConfig

logger = logging.getLogger(__name__)


def should_place_order_now(config: ExecutionConfig) -> bool:
    """Check if it's appropriate to place orders based on market timing.

    Uses America/New_York timezone for accurate ET handling to avoid
    issues with local timezone assumptions.

    Args:
        config: Execution configuration with timing parameters

    Returns:
        True if orders can be placed, False if market timing is poor

    """
    now = datetime.now(UTC)

    # Convert to ET for market timing using explicit America/New_York timezone
    et_time = now.astimezone(ZoneInfo("America/New_York"))
    current_time = et_time.time()

    # Check if we're in the restricted window (9:30-9:35am ET)
    market_open_time = dt_time(9, 30)  # 9:30am ET
    restricted_end_time = dt_time(9, 30 + config.market_open_delay_minutes)  # 9:35am ET

    if market_open_time <= current_time <= restricted_end_time:
        logger.info(
            f"⏰ Delaying order placement - within restricted window "
            f"({market_open_time} - {restricted_end_time} ET)"
        )
        return False

    return True
