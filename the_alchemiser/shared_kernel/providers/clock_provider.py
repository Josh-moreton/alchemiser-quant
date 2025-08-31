"""Business Unit: utilities; Status: current.

Deterministic clock provider for smoke validation.

Provides fixed timestamps to ensure deterministic behavior during
smoke validation and testing scenarios.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol


class ClockPort(Protocol):
    """Protocol for clock providers."""

    def now(self) -> datetime:
        """Get current timestamp."""
        ...


class DeterministicClockProvider(ClockPort):
    """Clock provider that returns fixed timestamps.

    Useful for smoke validation where deterministic behavior is required.
    """

    def __init__(self, fixed_time: datetime | None = None) -> None:
        """Initialize with optional fixed time.

        Args:
            fixed_time: Fixed timestamp to return. If None, uses a default fixed time.

        """
        self._fixed_time = fixed_time or datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)

    def now(self) -> datetime:
        """Return the fixed timestamp."""
        return self._fixed_time

    def advance_seconds(self, seconds: int) -> None:
        """Advance the fixed time by specified seconds.

        Args:
            seconds: Number of seconds to advance

        """
        from datetime import timedelta

        self._fixed_time = self._fixed_time + timedelta(seconds=seconds)


class SystemClockProvider(ClockPort):
    """Real system clock provider for production use."""

    def now(self) -> datetime:
        """Return current system time."""
        return datetime.now(UTC)
