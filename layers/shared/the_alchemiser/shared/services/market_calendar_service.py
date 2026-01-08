"""Business Unit: shared | Status: current.

Market Calendar Service.

This service provides market calendar information to determine if today is
an early close day and what time the market closes.

Key Features:
- Check if today is a trading day
- Get market close time for a specific date
- Detect early market closes (e.g., half-day before holidays)
- Thread-safe caching of calendar data

The service uses Alpaca's calendar API to fetch market schedule data.
"""

from __future__ import annotations

import threading
import time
from datetime import UTC, date, datetime, timedelta
from datetime import time as dt_time
from typing import TYPE_CHECKING, NamedTuple

from the_alchemiser.shared.errors.exceptions import TradingClientError
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.utils.api_helpers import with_rate_limiting, with_timeout

if TYPE_CHECKING:
    from alpaca.trading.client import TradingClient

from alpaca.trading.requests import GetCalendarRequest

logger = get_logger(__name__)

# Standard market hours (Eastern Time)
STANDARD_CLOSE_TIME = dt_time(16, 0)  # 4:00 PM ET


class MarketDay(NamedTuple):
    """Represents a single market trading day."""

    date: date
    open_time: dt_time
    close_time: dt_time
    is_early_close: bool


class MarketCalendarService:
    """Service for market calendar checks and trading hours.

    This service provides market calendar information to determine whether
    trading should occur on a given day and what the market hours are.
    """

    CACHE_TTL = 3600.0  # Cache calendar data for 1 hour
    _API_TIMEOUT = 15.0  # Timeout for API calls in seconds

    def __init__(self, trading_client: TradingClient) -> None:
        """Initialize the market calendar service.

        Args:
            trading_client: Alpaca TradingClient instance for API access

        Raises:
            ValueError: If trading_client is None

        """
        if not trading_client:
            raise ValueError("trading_client cannot be None")

        self._trading_client = trading_client
        self._calendar_cache: dict[str, MarketDay] = {}
        self._cache_timestamp: float = 0
        self._cache_lock = threading.Lock()

    @with_rate_limiting
    @with_timeout(15.0)
    def _fetch_calendar_from_api(self, start_date: date, end_date: date) -> list[MarketDay]:
        """Fetch market calendar from API with rate limiting and timeout.

        Args:
            start_date: Start date for calendar query
            end_date: End date for calendar query

        Returns:
            List of MarketDay objects

        Raises:
            TradingClientError: If API call fails

        """
        try:
            filters = GetCalendarRequest(
                start=start_date,
                end=end_date,
            )
            calendar_data = self._trading_client.get_calendar(filters)

            result: list[MarketDay] = []
            for day in calendar_data:
                # Extract date - Alpaca returns date object or string
                day_date_raw = getattr(day, "date", None)
                if day_date_raw is None:
                    continue

                # Handle both date objects and strings
                if isinstance(day_date_raw, date):
                    day_date = day_date_raw
                else:
                    day_date_str = str(day_date_raw)
                    # Handle datetime strings like "2025-12-24 00:00:00"
                    if " " in day_date_str:
                        day_date_str = day_date_str.split(" ")[0]
                    day_date = date.fromisoformat(day_date_str)

                # Extract open/close times - Alpaca returns time objects or strings
                open_raw = getattr(day, "open", None)
                close_raw = getattr(day, "close", None)

                if open_raw is None or close_raw is None:
                    logger.warning(
                        "Calendar day missing open/close times",
                        date=day_date.isoformat(),
                    )
                    continue

                # Handle both time objects and strings
                if isinstance(open_raw, dt_time):
                    open_time = open_raw
                else:
                    open_str = str(open_raw)
                    # Handle datetime strings like "2025-12-24 09:30:00" -> extract time part
                    if " " in open_str:
                        open_str = open_str.split(" ")[1]
                    # Handle "HH:MM:SS" or "HH:MM" format
                    open_time = dt_time.fromisoformat(open_str)

                if isinstance(close_raw, dt_time):
                    close_time = close_raw
                else:
                    close_str = str(close_raw)
                    # Handle datetime strings like "2025-12-24 16:00:00" -> extract time part
                    if " " in close_str:
                        close_str = close_str.split(" ")[1]
                    # Handle "HH:MM:SS" or "HH:MM" format
                    close_time = dt_time.fromisoformat(close_str)

                # Early close = any close before standard 4:00 PM
                is_early_close = close_time < STANDARD_CLOSE_TIME

                result.append(
                    MarketDay(
                        date=day_date,
                        open_time=open_time,
                        close_time=close_time,
                        is_early_close=is_early_close,
                    )
                )

            return result

        except Exception as e:
            raise TradingClientError(f"Failed to fetch market calendar: {e}") from e

    def _refresh_cache_if_needed(self, target_date: date) -> None:
        """Refresh calendar cache if expired or doesn't contain target date."""
        with self._cache_lock:
            current_time = time.time()
            cache_expired = (current_time - self._cache_timestamp) > self.CACHE_TTL
            date_str = target_date.isoformat()
            date_not_in_cache = date_str not in self._calendar_cache

            if cache_expired or date_not_in_cache:
                start_date = target_date - timedelta(days=15)
                end_date = target_date + timedelta(days=15)

                logger.debug(
                    "Refreshing market calendar cache",
                    start_date=start_date.isoformat(),
                    end_date=end_date.isoformat(),
                )

                calendar_days = self._fetch_calendar_from_api(start_date, end_date)

                self._calendar_cache.clear()
                for day in calendar_days:
                    self._calendar_cache[day.date.isoformat()] = day

                self._cache_timestamp = current_time

                logger.info(
                    "Market calendar cache refreshed",
                    days_cached=len(self._calendar_cache),
                )

    def get_market_day(
        self, target_date: date | None = None, *, correlation_id: str | None = None
    ) -> MarketDay | None:
        """Get market day information for a specific date.

        Args:
            target_date: Date to check (defaults to today)
            correlation_id: Optional correlation ID for tracing

        Returns:
            MarketDay if market is open on that date, None if closed

        Raises:
            TradingClientError: If API call fails

        """
        if target_date is None:
            target_date = datetime.now(UTC).date()

        log_context = {"date": target_date.isoformat()}
        if correlation_id:
            log_context["correlation_id"] = correlation_id

        try:
            self._refresh_cache_if_needed(target_date)

            date_str = target_date.isoformat()
            market_day = self._calendar_cache.get(date_str)

            if market_day:
                logger.debug(
                    "Market is open on date",
                    open_time=market_day.open_time.isoformat(),
                    close_time=market_day.close_time.isoformat(),
                    is_early_close=market_day.is_early_close,
                    **log_context,
                )
            else:
                logger.debug("Market is closed on date", **log_context)

            return market_day

        except TradingClientError:
            raise

    def is_trading_day(
        self, target_date: date | None = None, *, correlation_id: str | None = None
    ) -> bool:
        """Check if a given date is a trading day.

        Args:
            target_date: Date to check (defaults to today)
            correlation_id: Optional correlation ID for tracing

        Returns:
            True if market is open on that date, False otherwise

        """
        market_day = self.get_market_day(target_date, correlation_id=correlation_id)
        return market_day is not None

    def get_close_time(
        self, target_date: date | None = None, *, correlation_id: str | None = None
    ) -> dt_time | None:
        """Get the market close time for a specific date.

        Args:
            target_date: Date to check (defaults to today)
            correlation_id: Optional correlation ID for tracing

        Returns:
            Close time if market is open, None if closed

        """
        market_day = self.get_market_day(target_date, correlation_id=correlation_id)
        return market_day.close_time if market_day else None

    def is_early_close(
        self, target_date: date | None = None, *, correlation_id: str | None = None
    ) -> bool:
        """Check if a given date is an early close day.

        Args:
            target_date: Date to check (defaults to today)
            correlation_id: Optional correlation ID for tracing

        Returns:
            True if market closes early on that date, False otherwise

        """
        market_day = self.get_market_day(target_date, correlation_id=correlation_id)
        return market_day.is_early_close if market_day else False

    def get_execution_time(
        self,
        target_date: date | None = None,
        *,
        minutes_before_close: int = 15,
        correlation_id: str | None = None,
    ) -> datetime | None:
        """Get the optimal execution time for a given trading day.

        Returns the time at which trading should be triggered, accounting for
        early closes. This is `minutes_before_close` before market close.

        Args:
            target_date: Date to check (defaults to today)
            minutes_before_close: How many minutes before close to execute
            correlation_id: Optional correlation ID for tracing

        Returns:
            Datetime in ET for execution, or None if not a trading day

        """
        market_day = self.get_market_day(target_date, correlation_id=correlation_id)
        if not market_day:
            return None

        if target_date is None:
            target_date = datetime.now(UTC).date()

        # Combine date with close time, then subtract buffer
        # Note: Close time is in ET (Eastern Time)
        close_datetime = datetime.combine(target_date, market_day.close_time)
        execution_time = close_datetime - timedelta(minutes=minutes_before_close)

        logger.info(
            "Calculated execution time",
            target_date=target_date.isoformat(),
            close_time=market_day.close_time.isoformat(),
            is_early_close=market_day.is_early_close,
            execution_time=execution_time.isoformat(),
            minutes_before_close=minutes_before_close,
            **({"correlation_id": correlation_id} if correlation_id else {}),
        )

        return execution_time
