"""Business Unit: execution | Status: current.

Market timing utilities for smart execution.

Provides market hour awareness, timing restrictions, and trading session information
to support smart execution strategies that need to respect market conditions.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, time, timedelta
from typing import NamedTuple
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)


class MarketSession(NamedTuple):
    """Market session information."""
    
    is_open: bool
    is_pre_market: bool
    is_after_hours: bool
    is_opening_period: bool  # 9:30-9:35 ET
    session_start: time | None
    session_end: time | None


class MarketTimingUtils:
    """Utilities for market timing and session awareness."""
    
    # Market times in ET
    MARKET_OPEN = time(9, 30)
    MARKET_CLOSE = time(16, 0)
    OPENING_VOLATILITY_END = time(9, 35)  # Avoid orders until this time
    
    PRE_MARKET_START = time(4, 0)
    AFTER_HOURS_END = time(20, 0)

    @classmethod
    def get_market_session(cls, now: datetime | None = None) -> MarketSession:
        """Get current market session information.
        
        Args:
            now: Current time (defaults to now in UTC)
            
        Returns:
            MarketSession with current market state

        """
        if now is None:
            now = datetime.now(UTC)
            
        # Convert to ET with proper DST handling
        et_timezone = ZoneInfo("America/New_York")
        et_time = now.astimezone(et_timezone)
        current_time = et_time.time()
        
        # Determine session state
        is_open = cls.MARKET_OPEN <= current_time <= cls.MARKET_CLOSE
        is_pre_market = cls.PRE_MARKET_START <= current_time < cls.MARKET_OPEN
        is_after_hours = cls.MARKET_CLOSE < current_time <= cls.AFTER_HOURS_END
        is_opening_period = cls.MARKET_OPEN <= current_time <= cls.OPENING_VOLATILITY_END
        
        return MarketSession(
            is_open=is_open,
            is_pre_market=is_pre_market,
            is_after_hours=is_after_hours,
            is_opening_period=is_opening_period,
            session_start=cls.MARKET_OPEN if is_open else None,
            session_end=cls.MARKET_CLOSE if is_open else None,
        )

    @classmethod
    def should_delay_for_opening(cls, now: datetime | None = None) -> bool:
        """Check if orders should be delayed due to market opening volatility.
        
        Args:
            now: Current time (defaults to now in UTC)
            
        Returns:
            True if orders should be delayed

        """
        session = cls.get_market_session(now)
        return session.is_opening_period

    @classmethod
    def get_time_until_safe_execution(cls, now: datetime | None = None) -> timedelta | None:
        """Get time until safe execution (after opening period).
        
        Args:
            now: Current time (defaults to now in UTC)
            
        Returns:
            Time until safe execution, or None if already safe

        """
        if now is None:
            now = datetime.now(UTC)
            
        session = cls.get_market_session(now)
        
        if not session.is_opening_period:
            return None
            
        # Calculate time until 9:35 ET
        et_time = now - timedelta(hours=5)
        safe_time = datetime.combine(et_time.date(), cls.OPENING_VOLATILITY_END)
        safe_time_utc = safe_time + timedelta(hours=5)
        
        return safe_time_utc - now

    @classmethod
    def is_market_open(cls, now: datetime | None = None) -> bool:
        """Check if market is currently open.
        
        Args:
            now: Current time (defaults to now in UTC)
            
        Returns:
            True if market is open

        """
        session = cls.get_market_session(now)
        return session.is_open

    @classmethod
    def log_market_status(cls, now: datetime | None = None) -> None:
        """Log current market status for debugging."""
        session = cls.get_market_session(now)
        
        if session.is_opening_period:
            logger.info("🔴 Market in opening volatility period - delaying orders")
        elif session.is_open:
            logger.info("🟢 Market open - normal trading")
        elif session.is_pre_market:
            logger.info("🟡 Pre-market hours")
        elif session.is_after_hours:
            logger.info("🟡 After-hours trading")
        else:
            logger.info("🔴 Market closed")