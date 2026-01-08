"""Business Unit: shared | Status: current.

Market Calendar Service.

This service provides market calendar checks to determine if trading should
occur on a given day, and what the market hours are (including early closes).

Key Features:
- Check if today is a trading day
- Get market open/close times for a specific date
- Handle early market closes (e.g., half-day before holidays)
- Thread-safe caching of calendar data
- Rate limiting and timeout handling

The service uses Alpaca's calendar API to fetch market schedule data.
"""

from __future__ import annotations

import threading
import time
from datetime import UTC, date, datetime, time as dt_time
from typing import TYPE_CHECKING, NamedTuple

from the_alchemiser.shared.errors.exceptions import (
    DataProviderError,
    TradingClientError,
)
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.utils.api_helpers import with_rate_limiting, with_timeout

if TYPE_CHECKING:
    from alpaca.trading.client import TradingClient

logger = get_logger(__name__)


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

    API_TIMEOUT = 15.0  # Timeout for API calls in seconds
    CACHE_TTL = 3600.0  # Cache calendar data for 1 hour

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
    def _fetch_calendar_from_api(
        self, start_date: date, end_date: date
    ) -> list[MarketDay]:
        """Fetch market calendar from API with rate limiting and timeout.

        Args:
            start_date: Start date for calendar query
            end_date: End date for calendar query

        Returns:
            List of MarketDay objects

        Raises:
            TradingClientError: If API call fails
            DataProviderError: If calendar data is incomplete

        """
        try:
            # Alpaca's get_calendar accepts start and end as date/datetime strings
            calendar_data = self._trading_client.get_calendar(
                start=start_date.isoformat(),
                end=end_date.isoformat(),
            )

            result: list[MarketDay] = []
            for day in calendar_data:
                # Extract date
                day_date_str = str(getattr(day, "date", ""))
                if not day_date_str:
                    continue

                day_date = date.fromisoformat(day_date_str)

                # Extract open/close times
                open_str = str(getattr(day, "open", ""))
                close_str = str(getattr(day, "close", ""))

                if not open_str or not close_str:
                    logger.warning(
                        "Calendar day missing open/close times",
                        date=day_date_str,
                    )
                    continue

                # Parse times (format: "09:30" or "HH:MM")
                open_time = dt_time.fromisoformat(open_str)
                close_time = dt_time.fromisoformat(close_str)

                # Check for early close (typical market close is 4:00 PM ET = 16:00)
                # Early closes are typically 1:00 PM ET = 13:00
                is_early_close = close_time.hour < 16

                result.append(
                    MarketDay(
                        date=day_date,
                        open_time=open_time,
                        close_time=close_time,
                        is_early_close=is_early_close,
                    )
                )

            return result

        except AttributeError as e:
            raise DataProviderError(
                f"Calendar data missing required fields: {e}",
                context={"error": str(e)},
            ) from e
        except Exception as e:
            raise TradingClientError(f"Failed to fetch market calendar: {e}") from e

    def _refresh_cache_if_needed(self, target_date: date) -> None:
        """Refresh calendar cache if expired or doesn't contain target date.

        Args:
            target_date: Date to ensure is in cache

        Raises:
            TradingClientError: If API call fails
            DataProviderError: If calendar data is incomplete

        """
        with self._cache_lock:
            current_time = time.time()
            cache_expired = (current_time - self._cache_timestamp) > self.CACHE_TTL
            date_str = target_date.isoformat()
            date_not_in_cache = date_str not in self._calendar_cache

            if cache_expired or date_not_in_cache:
                # Fetch calendar for a 30-day window around target date
                # This reduces API calls while keeping data fresh
                from datetime import timedelta

                start_date = target_date - timedelta(days=15)
                end_date = target_date + timedelta(days=15)

                logger.debug(
                    "Refreshing market calendar cache",
                    start_date=start_date.isoformat(),
                    end_date=end_date.isoformat(),
                    cache_expired=cache_expired,
                    date_not_in_cache=date_not_in_cache,
                )

                calendar_days = self._fetch_calendar_from_api(start_date, end_date)

                # Update cache
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
            DataProviderError: If calendar data is incomplete

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

        except (TradingClientError, DataProviderError) as e:
            logger.error(
                "Failed to get market day",
                error=str(e),
                error_type=type(e).__name__,
                **log_context,
            )
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

        Raises:
            TradingClientError: If API call fails
            DataProviderError: If calendar data is incomplete

        """
        market_day = self.get_market_day(target_date, correlation_id=correlation_id)
        return market_day is not None

    def should_trade_now(
        self,
        *,
        check_time: datetime | None = None,
        minutes_before_close: int = 15,
        correlation_id: str | None = None,
    ) -> tuple[bool, str]:
        """Check if trading should occur at a given time.

        This method checks:
        1. If today is a trading day
        2. If current time is within trading hours
        3. If there's enough time before market close

        Args:
            check_time: Time to check (defaults to now in UTC)
            minutes_before_close: Minimum minutes before close to allow trading
            correlation_id: Optional correlation ID for tracing

        Returns:
            Tuple of (should_trade: bool, reason: str)

        Raises:
            TradingClientError: If API call fails
            DataProviderError: If calendar data is incomplete

        """
        if check_time is None:
            check_time = datetime.now(UTC)

        check_date = check_time.date()

        log_context = {
            "check_time": check_time.isoformat(),
            "minutes_before_close": minutes_before_close,
        }
        if correlation_id:
            log_context["correlation_id"] = correlation_id

        # Check if today is a trading day
        market_day = self.get_market_day(check_date, correlation_id=correlation_id)

        if market_day is None:
            reason = f"Market is closed on {check_date.isoformat()}"
            logger.info("Trading should not occur - market closed", **log_context)
            return False, reason

        # Market is open - check if we're within trading hours
        # Convert check_time to time component for comparison
        check_time_only = check_time.time()

        if check_time_only < market_day.open_time:
            reason = (
                f"Before market open (opens at {market_day.open_time.isoformat()})"
            )
            logger.info(
                "Trading should not occur - before market open", **log_context
            )
            return False, reason

        # Calculate time until close
        from datetime import timedelta

        close_dt = datetime.combine(check_date, market_day.close_time, tzinfo=UTC)
        time_until_close = close_dt - check_time

        if time_until_close < timedelta(minutes=minutes_before_close):
            reason = (
                f"Too close to market close "
                f"(closes at {market_day.close_time.isoformat()}, "
                f"{int(time_until_close.total_seconds() / 60)} minutes remaining)"
            )
            logger.info(
                "Trading should not occur - too close to close",
                time_until_close_minutes=int(time_until_close.total_seconds() / 60),
                **log_context,
            )
            return False, reason

        # All checks passed
        logger.info(
            "Trading should occur",
            is_early_close=market_day.is_early_close,
            close_time=market_day.close_time.isoformat(),
            **log_context,
        )
        return True, "Market is open and sufficient time before close"
