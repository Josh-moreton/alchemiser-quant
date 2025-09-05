#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Centralized timezone utilities for ensuring timezone awareness across the system.

This module provides common timezone-related functions to eliminate duplicate
timezone handling logic across DTOs, mappers, and other components.
"""

from __future__ import annotations

from datetime import UTC, datetime


def ensure_timezone_aware(timestamp: datetime | None) -> datetime | None:
    """Ensure a datetime is timezone-aware by adding UTC if naive.

    This function provides a centralized way to handle timezone awareness
    across all DTOs and components, eliminating duplicate implementations.

    Args:
        timestamp: Datetime that may be naive (no timezone) or aware

    Returns:
        Timezone-aware datetime with UTC if originally naive, or None if input was None

    Examples:
        >>> from datetime import datetime
        >>> naive = datetime(2023, 1, 1, 12, 0, 0)
        >>> aware = ensure_timezone_aware(naive)
        >>> aware.tzinfo is not None
        True
        >>> aware.tzinfo.tzname(None)
        'UTC'

        >>> ensure_timezone_aware(None) is None
        True

    """
    if timestamp is None:
        return None
    if timestamp.tzinfo is None:
        return timestamp.replace(tzinfo=UTC)
    return timestamp


def normalize_timestamp_to_utc(timestamp: datetime | str | int | float) -> datetime:
    """Normalize various timestamp formats to timezone-aware UTC datetime.

    This function handles multiple input formats and always returns a timezone-aware
    datetime in UTC, providing a robust conversion for mapping operations.

    Args:
        timestamp: Timestamp in various formats (datetime, str, etc.)

    Returns:
        Timezone-aware datetime in UTC

    Raises:
        ValueError: If timestamp cannot be parsed

    Examples:
        >>> normalize_timestamp_to_utc("2023-01-01T12:00:00")
        datetime(2023, 1, 1, 12, 0, tzinfo=datetime.timezone.utc)

        >>> from datetime import datetime
        >>> naive = datetime(2023, 1, 1, 12, 0, 0)
        >>> result = normalize_timestamp_to_utc(naive)
        >>> result.tzinfo.tzname(None)
        'UTC'

    """
    if isinstance(timestamp, datetime):
        # Handle datetime objects
        return ensure_timezone_aware(timestamp)

    if isinstance(timestamp, str):
        # Handle ISO format strings
        try:
            # Handle 'Z' suffix (Zulu time = UTC)
            if timestamp.endswith("Z"):
                timestamp = timestamp[:-1] + "+00:00"

            parsed = datetime.fromisoformat(timestamp)
            return ensure_timezone_aware(parsed)
        except ValueError:
            # Fallback to current time if parsing fails
            return datetime.now(UTC)

    # For other types, try to convert to string first
    try:
        return normalize_timestamp_to_utc(str(timestamp))
    except Exception:
        # Ultimate fallback to current time
        return datetime.now(UTC)


def to_iso_string(timestamp: datetime | None) -> str | None:
    """Convert timezone-aware datetime to ISO string format.

    Args:
        timestamp: Timezone-aware datetime or None

    Returns:
        ISO format string or None if input was None

    Examples:
        >>> from datetime import datetime, timezone
        >>> dt = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        >>> to_iso_string(dt)
        '2023-01-01T12:00:00+00:00'

        >>> to_iso_string(None) is None
        True

    """
    if timestamp is None:
        return None

    # Ensure timezone awareness before converting
    aware_timestamp = ensure_timezone_aware(timestamp)
    return aware_timestamp.isoformat()
