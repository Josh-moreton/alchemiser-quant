"""Business Unit: shared | Status: current.

Evaluation timestamp provider for consistent market session timing.

This module provides a standardized evaluation timestamp mechanism for
determining market session state and progress. The default evaluation
time is 15:45 ET (Eastern Time), which is:
- 15 minutes before market close (4:00 PM ET)
- After the majority of daily volume has traded
- Before last-minute closing volatility

Usage:
    >>> from the_alchemiser.shared.utils.evaluation_timestamp import (
    ...     EvaluationTimestampProvider,
    ...     get_evaluation_timestamp,
    ... )
    >>> # Get today's evaluation timestamp
    >>> eval_time = get_evaluation_timestamp()
    >>> print(eval_time)  # 2026-01-07T15:45:00-05:00 (or current date)

Architecture:
    - CachedMarketDataAdapter reads completed daily bars from S3
    - IndicatorService computes using the full daily bar series
    - Data refresh after market close ensures today's bar is available

Constants:
    DEFAULT_EVALUATION_HOUR = 15  # 3 PM ET
    DEFAULT_EVALUATION_MINUTE = 45  # :45 minutes
"""

from __future__ import annotations

from datetime import UTC, date, datetime, time
from zoneinfo import ZoneInfo

from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)

# Eastern Time zone for US equity markets
ET_TIMEZONE = ZoneInfo("America/New_York")

# Default evaluation time: 15:45 ET (3:45 PM Eastern)
# This is 15 minutes before regular market close (4:00 PM ET)
DEFAULT_EVALUATION_HOUR = 15
DEFAULT_EVALUATION_MINUTE = 45

# Market session times (regular session)
MARKET_OPEN_HOUR = 9
MARKET_OPEN_MINUTE = 30
MARKET_CLOSE_HOUR = 16
MARKET_CLOSE_MINUTE = 0


class EvaluationTimestampProvider:
    """Provider for consistent evaluation timestamps across backtest and live.

    The evaluation timestamp determines when partial daily bars are "frozen"
    for indicator computation. Using a consistent time ensures that:

    1. Live trading evaluates at the same intraday point
    2. Backtests can reconstruct the same partial bar state
    3. Indicator values are comparable between environments

    Attributes:
        evaluation_hour: Hour in ET (0-23) for evaluation. Default 15 (3 PM).
        evaluation_minute: Minute (0-59) for evaluation. Default 45.

    Example:
        >>> provider = EvaluationTimestampProvider()
        >>> ts = provider.get_evaluation_timestamp()
        >>> print(ts.strftime("%Y-%m-%d %H:%M %Z"))
        2026-01-07 15:45 EST

    """

    def __init__(
        self,
        evaluation_hour: int = DEFAULT_EVALUATION_HOUR,
        evaluation_minute: int = DEFAULT_EVALUATION_MINUTE,
    ) -> None:
        """Initialize evaluation timestamp provider.

        Args:
            evaluation_hour: Hour in ET (0-23). Default 15 (3 PM).
            evaluation_minute: Minute (0-59). Default 45.

        Raises:
            ValueError: If hour or minute is out of valid range.

        """
        if not 0 <= evaluation_hour <= 23:
            raise ValueError(f"evaluation_hour must be 0-23, got {evaluation_hour}")
        if not 0 <= evaluation_minute <= 59:
            raise ValueError(f"evaluation_minute must be 0-59, got {evaluation_minute}")

        self.evaluation_hour = evaluation_hour
        self.evaluation_minute = evaluation_minute

        logger.debug(
            "EvaluationTimestampProvider initialized",
            evaluation_time=f"{evaluation_hour:02d}:{evaluation_minute:02d} ET",
        )

    def get_evaluation_timestamp(
        self,
        for_date: date | None = None,
    ) -> datetime:
        """Get evaluation timestamp for a specific date.

        Returns a timezone-aware datetime in ET (Eastern Time) at the
        configured evaluation hour/minute.

        Args:
            for_date: Date to get evaluation timestamp for. Defaults to today.

        Returns:
            Timezone-aware datetime in Eastern Time at evaluation time.

        Example:
            >>> from datetime import date
            >>> provider = EvaluationTimestampProvider()
            >>> ts = provider.get_evaluation_timestamp(date(2026, 1, 7))
            >>> ts.isoformat()
            '2026-01-07T15:45:00-05:00'

        """
        if for_date is None:
            for_date = datetime.now(ET_TIMEZONE).date()

        eval_time = time(
            hour=self.evaluation_hour,
            minute=self.evaluation_minute,
            second=0,
            microsecond=0,
        )

        # Combine date and time in ET timezone
        eval_datetime = datetime.combine(for_date, eval_time, tzinfo=ET_TIMEZONE)

        logger.debug(
            "Generated evaluation timestamp",
            date=for_date.isoformat(),
            timestamp=eval_datetime.isoformat(),
        )

        return eval_datetime

    def get_evaluation_timestamp_utc(
        self,
        for_date: date | None = None,
    ) -> datetime:
        """Get evaluation timestamp in UTC.

        Convenience method that returns the evaluation timestamp converted
        to UTC timezone for consistent storage and comparison.

        Args:
            for_date: Date to get evaluation timestamp for. Defaults to today.

        Returns:
            Timezone-aware datetime in UTC at evaluation time.

        """
        et_timestamp = self.get_evaluation_timestamp(for_date)
        return et_timestamp.astimezone(UTC)

    def is_before_evaluation_time(
        self,
        timestamp: datetime | None = None,
    ) -> bool:
        """Check if a timestamp is before today's evaluation time.

        Useful for determining whether to use cached data or fetch live data.

        Args:
            timestamp: Timestamp to check. Defaults to current time.

        Returns:
            True if timestamp is before today's evaluation time.

        """
        if timestamp is None:
            timestamp = datetime.now(ET_TIMEZONE)
        elif timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=UTC).astimezone(ET_TIMEZONE)
        else:
            timestamp = timestamp.astimezone(ET_TIMEZONE)

        eval_ts = self.get_evaluation_timestamp(timestamp.date())
        return timestamp < eval_ts

    def is_after_evaluation_time(
        self,
        timestamp: datetime | None = None,
    ) -> bool:
        """Check if a timestamp is after today's evaluation time.

        Args:
            timestamp: Timestamp to check. Defaults to current time.

        Returns:
            True if timestamp is after today's evaluation time.

        """
        return not self.is_before_evaluation_time(timestamp)

    def is_market_hours(
        self,
        timestamp: datetime | None = None,
    ) -> bool:
        """Check if timestamp is during regular market hours (9:30 AM - 4:00 PM ET).

        Does NOT account for holidays or early closes. Use a trading calendar
        for accurate session detection.

        Args:
            timestamp: Timestamp to check. Defaults to current time.

        Returns:
            True if timestamp is during regular market hours.

        """
        if timestamp is None:
            timestamp = datetime.now(ET_TIMEZONE)
        elif timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=UTC).astimezone(ET_TIMEZONE)
        else:
            timestamp = timestamp.astimezone(ET_TIMEZONE)

        market_open = time(MARKET_OPEN_HOUR, MARKET_OPEN_MINUTE)
        market_close = time(MARKET_CLOSE_HOUR, MARKET_CLOSE_MINUTE)

        current_time = timestamp.time()
        return market_open <= current_time < market_close

    def get_session_progress(
        self,
        timestamp: datetime | None = None,
    ) -> float:
        """Get the progress through the trading session as a fraction.

        Returns a value between 0.0 (market open) and 1.0 (market close).
        Returns 0.0 before market open, 1.0 after market close.

        Args:
            timestamp: Timestamp to check. Defaults to current time.

        Returns:
            Float between 0.0 and 1.0 indicating session progress.

        Example:
            >>> provider = EvaluationTimestampProvider()
            >>> # At 12:45 PM ET (halfway through session)
            >>> progress = provider.get_session_progress(some_timestamp)
            >>> print(f"{progress:.1%}")  # "50.0%"

        """
        if timestamp is None:
            timestamp = datetime.now(ET_TIMEZONE)
        elif timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=UTC).astimezone(ET_TIMEZONE)
        else:
            timestamp = timestamp.astimezone(ET_TIMEZONE)

        # Calculate session duration in minutes
        session_start = datetime.combine(
            timestamp.date(),
            time(MARKET_OPEN_HOUR, MARKET_OPEN_MINUTE),
            tzinfo=ET_TIMEZONE,
        )
        session_end = datetime.combine(
            timestamp.date(),
            time(MARKET_CLOSE_HOUR, MARKET_CLOSE_MINUTE),
            tzinfo=ET_TIMEZONE,
        )
        session_duration = (session_end - session_start).total_seconds()

        if timestamp <= session_start:
            return 0.0
        if timestamp >= session_end:
            return 1.0

        elapsed = (timestamp - session_start).total_seconds()
        return elapsed / session_duration


# Module-level singleton for convenience
_default_provider: EvaluationTimestampProvider | None = None


def get_evaluation_timestamp_provider() -> EvaluationTimestampProvider:
    """Get the default evaluation timestamp provider.

    Returns a singleton instance with default settings (15:45 ET).

    Returns:
        EvaluationTimestampProvider singleton instance.

    """
    global _default_provider
    if _default_provider is None:
        _default_provider = EvaluationTimestampProvider()
    return _default_provider


def get_evaluation_timestamp(for_date: date | None = None) -> datetime:
    """Get evaluation timestamp for a date using default provider.

    Convenience function that uses the default provider settings.

    Args:
        for_date: Date to get evaluation timestamp for. Defaults to today.

    Returns:
        Timezone-aware datetime in ET at 15:45.

    """
    return get_evaluation_timestamp_provider().get_evaluation_timestamp(for_date)


def get_evaluation_timestamp_utc(for_date: date | None = None) -> datetime:
    """Get evaluation timestamp in UTC using default provider.

    Args:
        for_date: Date to get evaluation timestamp for. Defaults to today.

    Returns:
        Timezone-aware datetime in UTC.

    """
    return get_evaluation_timestamp_provider().get_evaluation_timestamp_utc(for_date)
