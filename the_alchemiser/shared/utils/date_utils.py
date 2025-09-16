#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Date and time utilities for The Alchemiser Trading System.

This module provides common date/time conversion functions with consistent UTC
handling for timestamps, datetime objects, and unix time operations.
"""

from __future__ import annotations

from datetime import UTC, datetime


def get_current_utc_time() -> datetime:
    """Get current UTC time as timezone-aware datetime."""
    return datetime.now(UTC)


def convert_unix_to_datetime(unix_timestamp: float | int) -> datetime:
    """Convert unix timestamp (seconds) to timezone-aware UTC datetime."""
    return datetime.fromtimestamp(unix_timestamp, tz=UTC)


def convert_datetime_to_unix(dt: datetime) -> float:
    """Convert datetime to unix timestamp (seconds), ensuring UTC timezone."""
    if dt.tzinfo is None:
        # Assume naive datetime is UTC
        dt = dt.replace(tzinfo=UTC)
    return dt.timestamp()


def convert_timestamp_to_datetime(timestamp: str | float | int) -> datetime:
    """Convert various timestamp formats to timezone-aware UTC datetime."""
    if isinstance(timestamp, str):
        # Handle ISO format strings
        if timestamp.endswith("Z"):
            timestamp = timestamp[:-1] + "+00:00"
        return datetime.fromisoformat(timestamp).replace(tzinfo=UTC)
    
    # Handle numeric timestamps (assume unix seconds)
    return convert_unix_to_datetime(float(timestamp))


def convert_datetime_to_timestamp(dt: datetime) -> str:
    """Convert datetime to ISO timestamp string in UTC format."""
    dt = dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.astimezone(UTC)
    return dt.isoformat()


def get_start_of_day_unix(date: datetime | None = None) -> float:
    """Get unix timestamp for start of day (00:00:00) in UTC."""
    if date is None:
        date = get_current_utc_time()
    
    if date.tzinfo is None:
        date = date.replace(tzinfo=UTC)
    
    # Convert to UTC and get start of day
    utc_date = date.astimezone(UTC)
    start_of_day = utc_date.replace(hour=0, minute=0, second=0, microsecond=0)
    return start_of_day.timestamp()


def get_end_of_day_unix(date: datetime | None = None) -> float:
    """Get unix timestamp for end of day (23:59:59.999999) in UTC."""
    if date is None:
        date = get_current_utc_time()
    
    if date.tzinfo is None:
        date = date.replace(tzinfo=UTC)
    
    # Convert to UTC and get end of day
    utc_date = date.astimezone(UTC)
    end_of_day = utc_date.replace(hour=23, minute=59, second=59, microsecond=999999)
    return end_of_day.timestamp()


def get_days_between_timestamps(start_timestamp: float | int, end_timestamp: float | int) -> int:
    """Get number of whole days between two unix timestamps."""
    start_dt = convert_unix_to_datetime(start_timestamp)
    end_dt = convert_unix_to_datetime(end_timestamp)
    
    # Calculate difference and return whole days
    delta = end_dt - start_dt
    return delta.days