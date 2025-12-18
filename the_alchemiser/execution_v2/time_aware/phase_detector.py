"""Business Unit: Execution | Status: current.

Phase detector for time-aware execution framework.

Determines the current execution phase based on:
- Current time (ET)
- Market calendar (trading days, early closes)
- Execution policy phase boundaries
"""

from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

from the_alchemiser.execution_v2.time_aware.execution_policy import ExecutionPolicy
from the_alchemiser.execution_v2.time_aware.models import (
    ExecutionPhase,
    ExecutionTickContext,
)

# US Eastern timezone for market hours
ET = ZoneInfo("America/New_York")


class PhaseDetector:
    """Detects current execution phase based on time and policy.

    The detector handles:
    - Regular trading days (09:30-16:00 ET)
    - Early close days (09:30-13:00 ET)
    - Weekends and holidays
    - Phase boundary transitions
    """

    def __init__(
        self,
        policy: ExecutionPolicy,
        market_holidays: frozenset[str] | None = None,
    ) -> None:
        """Initialize phase detector.

        Args:
            policy: Execution policy with phase boundaries
            market_holidays: Set of holiday dates as "YYYY-MM-DD" strings

        """
        self.policy = policy
        self.market_holidays = market_holidays or frozenset()

        # Pre-compute phase boundaries from policy
        self._phase_boundaries = self._build_phase_boundaries()

    def _build_phase_boundaries(
        self,
    ) -> list[tuple[time, time, ExecutionPhase]]:
        """Build sorted list of phase time boundaries."""
        boundaries = [
            (
                self.policy.open_avoidance.get_start_time(),
                self.policy.open_avoidance.get_end_time(),
                ExecutionPhase.OPEN_AVOIDANCE,
            ),
            (
                self.policy.passive_accumulation.get_start_time(),
                self.policy.passive_accumulation.get_end_time(),
                ExecutionPhase.PASSIVE_ACCUMULATION,
            ),
            (
                self.policy.urgency_ramp.get_start_time(),
                self.policy.urgency_ramp.get_end_time(),
                ExecutionPhase.URGENCY_RAMP,
            ),
            (
                self.policy.deadline_close.get_start_time(),
                self.policy.deadline_close.get_end_time(),
                ExecutionPhase.DEADLINE_CLOSE,
            ),
        ]
        # Sort by start time
        return sorted(boundaries, key=lambda x: x[0])

    def is_trading_day(self, date: datetime) -> bool:
        """Check if given date is a trading day.

        Args:
            date: Date to check (any timezone, converted to ET)

        Returns:
            True if market is open on this day

        """
        et_date = date.astimezone(ET)
        date_str = et_date.strftime("%Y-%m-%d")

        # Weekend check (Saturday = 5, Sunday = 6)
        if et_date.weekday() >= 5:
            return False

        # Holiday check - return False if date is a holiday
        return date_str not in self.market_holidays

    def is_early_close(self, date: datetime) -> bool:
        """Check if given date is an early close day.

        Common early closes:
        - Day before Independence Day (if weekday)
        - Day after Thanksgiving (Black Friday)
        - Christmas Eve (if weekday)
        - New Year's Eve (if weekday)

        Args:
            date: Date to check

        Returns:
            True if early close day

        """
        et_date = date.astimezone(ET)
        month, day = et_date.month, et_date.day

        # Simplified early close detection
        # In production, use a market calendar library
        early_close_dates = [
            (7, 3),  # July 3 (day before July 4)
            (11, 29),  # Black Friday (approximate)
            (12, 24),  # Christmas Eve
            (12, 31),  # New Year's Eve
        ]

        if (month, day) in early_close_dates:
            return et_date.weekday() < 5  # Only if weekday

        return False

    def get_market_hours(self, date: datetime) -> tuple[datetime, datetime] | tuple[None, None]:
        """Get market open and close times for a date.

        Args:
            date: Date to get hours for

        Returns:
            Tuple of (open_time, close_time) in UTC, or (None, None) if closed

        """
        if not self.is_trading_day(date):
            return None, None

        et_date = date.astimezone(ET)
        market_date = et_date.date()

        # Standard hours
        open_time = time(9, 30)
        close_time = time(16, 0)

        # Adjust for early close
        if self.is_early_close(date):
            close_time = time(13, 0)

        market_open = datetime.combine(market_date, open_time, tzinfo=ET)
        market_close = datetime.combine(market_date, close_time, tzinfo=ET)

        return market_open.astimezone(UTC), market_close.astimezone(UTC)

    def detect_phase(self, current_time: datetime) -> ExecutionPhase:
        """Detect current execution phase.

        Args:
            current_time: Current time (any timezone)

        Returns:
            Current ExecutionPhase

        """
        if not self.is_trading_day(current_time):
            return ExecutionPhase.MARKET_CLOSED

        et_time = current_time.astimezone(ET)
        current_time_of_day = et_time.time()

        # Check if before market open
        if current_time_of_day < time(9, 30):
            return ExecutionPhase.MARKET_CLOSED

        # Check for early close
        close_time = time(13, 0) if self.is_early_close(current_time) else time(16, 0)
        if current_time_of_day >= close_time:
            return ExecutionPhase.MARKET_CLOSED

        # Adjust phase boundaries for early close
        if self.is_early_close(current_time) and self.policy.early_close_adjustment:
            return self._detect_phase_early_close(current_time_of_day)

        # Standard phase detection
        for start, end, phase in self._phase_boundaries:
            if start <= current_time_of_day < end:
                return phase

        # If past all phases but before close, we're in deadline phase
        if current_time_of_day >= self._phase_boundaries[-1][1]:
            return ExecutionPhase.DEADLINE_CLOSE

        return ExecutionPhase.MARKET_CLOSED

    def _detect_phase_early_close(self, current_time: time) -> ExecutionPhase:
        """Detect phase for early close days.

        On early close days (13:00 close), phases are compressed:
        - OPEN_AVOIDANCE: 09:30-10:00 (30 min vs 60 min)
        - PASSIVE_ACCUMULATION: 10:00-11:30 (90 min vs 240 min)
        - URGENCY_RAMP: 11:30-12:30 (60 min vs 60 min)
        - DEADLINE_CLOSE: 12:30-13:00 (30 min vs 30 min)
        """
        if current_time < time(10, 0):
            return ExecutionPhase.OPEN_AVOIDANCE
        if current_time < time(11, 30):
            return ExecutionPhase.PASSIVE_ACCUMULATION
        if current_time < time(12, 30):
            return ExecutionPhase.URGENCY_RAMP
        return ExecutionPhase.DEADLINE_CLOSE

    def build_tick_context(self, current_time: datetime) -> ExecutionTickContext:
        """Build complete tick context for current time.

        Args:
            current_time: Current time (any timezone)

        Returns:
            ExecutionTickContext with all timing information

        """
        market_open, market_close = self.get_market_hours(current_time)
        current_phase = self.detect_phase(current_time)
        is_trading = self.is_trading_day(current_time)

        utc_time = current_time.astimezone(UTC)

        # Determine if market is currently open
        is_open = False
        if market_open and market_close:
            is_open = market_open <= utc_time < market_close

        return ExecutionTickContext(
            tick_time=utc_time,
            market_open=market_open or utc_time,  # Fallback for non-trading days
            market_close=market_close or utc_time,
            current_phase=current_phase,
            is_trading_day=is_trading,
            is_market_open=is_open,
            is_early_close=self.is_early_close(current_time),
            halt_symbols=frozenset(),  # Populated by caller if needed
        )

    def time_until_phase_end(self, current_time: datetime, phase: ExecutionPhase) -> float:
        """Calculate seconds until current phase ends.

        Args:
            current_time: Current time
            phase: Phase to check

        Returns:
            Seconds until phase ends, or 0 if not in this phase

        """
        if self.detect_phase(current_time) != phase:
            return 0.0

        et_time = current_time.astimezone(ET)

        # Find phase end time
        for _start, end, p in self._phase_boundaries:
            if p == phase:
                phase_end = datetime.combine(et_time.date(), end, tzinfo=ET)
                delta = phase_end - et_time
                return max(0.0, delta.total_seconds())

        return 0.0

    def get_next_tick_time(self, current_time: datetime) -> datetime | None:
        """Calculate next scheduled tick time.

        Args:
            current_time: Current time

        Returns:
            Next tick time, or None if no more ticks today

        """
        _, market_close = self.get_market_hours(current_time)
        if not market_close:
            return None

        utc_time = current_time.astimezone(UTC)

        # Calculate next tick
        interval_seconds = self.policy.tick_interval_minutes * 60
        seconds_since_midnight = utc_time.hour * 3600 + utc_time.minute * 60 + utc_time.second
        next_tick_offset = (seconds_since_midnight // interval_seconds + 1) * interval_seconds

        next_tick = utc_time.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(
            seconds=next_tick_offset
        )

        # Don't schedule past market close
        if next_tick >= market_close:
            return None

        return next_tick
