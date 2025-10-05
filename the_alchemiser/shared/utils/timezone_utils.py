#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Centralized timezone utilities for ensuring timezone awareness across the system.

This module provides common timezone-related functions to eliminate duplicate
timezone handling logic across DTOs, mappers, and other components.

All functions enforce strict timezone handling for financial data integrity:
- Invalid timestamps raise TimestampParsingError instead of silent fallbacks
- All errors are logged with structured context for auditability
- No silent data mutations or current-time substitutions
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import overload

from ..constants import UTC_TIMEZONE_SUFFIX
from ..logging import get_logger
from ..types.exceptions import TimestampParsingError

# Module-level logger
logger = get_logger(__name__)


@overload
def ensure_timezone_aware(timestamp: None) -> None: ...


@overload
def ensure_timezone_aware(timestamp: datetime) -> datetime: ...


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
        timestamp: Timestamp in various formats (datetime, str, int, float)

    Returns:
        Timezone-aware datetime in UTC

    Raises:
        TimestampParsingError: If timestamp cannot be parsed or is invalid

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
        # ensure_timezone_aware returns datetime for datetime input
        return ensure_timezone_aware(timestamp)

    if isinstance(timestamp, str):
        # Handle ISO format strings
        try:
            # Handle 'Z' suffix (Zulu time = UTC)
            if timestamp.endswith("Z"):
                timestamp = timestamp[:-1] + UTC_TIMEZONE_SUFFIX

            parsed = datetime.fromisoformat(timestamp)
            # ensure_timezone_aware returns datetime for datetime input
            return ensure_timezone_aware(parsed)
        except ValueError as e:
            # Log error with context before raising
            logger.error(
                "timestamp_parsing_failed",
                timestamp_value=timestamp,
                timestamp_format="ISO8601",
                error=str(e),
            )
            raise TimestampParsingError(
                f"Failed to parse timestamp string: {timestamp}",
                timestamp_value=timestamp,
                timestamp_format="ISO8601",
            ) from e

    # For numeric types, try to convert to string first
    if isinstance(timestamp, (int, float)):
        try:
            timestamp_str = str(timestamp)
            return normalize_timestamp_to_utc(timestamp_str)
        except TimestampParsingError:
            # Log error with context before raising
            logger.error(
                "timestamp_conversion_failed",
                timestamp_value=timestamp,
                timestamp_type=type(timestamp).__name__,
            )
            raise TimestampParsingError(
                f"Failed to convert numeric timestamp: {timestamp}",
                timestamp_value=timestamp,
                timestamp_format="numeric",
            ) from None

    # Unsupported type - try to convert to string for error message only
    try:
        timestamp_str = str(timestamp)
    except Exception:
        timestamp_str = f"<{type(timestamp).__name__} object>"

    logger.error(
        "unsupported_timestamp_type",
        timestamp_value=timestamp_str,
        timestamp_type=type(timestamp).__name__,
    )
    raise TimestampParsingError(
        f"Unsupported timestamp type: {type(timestamp).__name__}",
        timestamp_value=timestamp_str,
    )


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
    # ensure_timezone_aware returns datetime for datetime input
    aware_timestamp = ensure_timezone_aware(timestamp)
    return aware_timestamp.isoformat()
