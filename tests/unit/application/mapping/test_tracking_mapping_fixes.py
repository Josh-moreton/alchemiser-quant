#!/usr/bin/env python3
"""
Tests for tracking_mapping.py fixes - specifically the normalize_timestamp function.

Tests the updated function that handles timezone normalization correctly
without unreachable code.
"""

from datetime import UTC, datetime

from the_alchemiser.application.mapping.tracking_mapping import normalize_timestamp


class TestTrackingMappingFixes:
    """Test cases for tracking mapping fixes."""

    def test_normalize_timestamp_with_naive_datetime(self) -> None:
        """Test normalize_timestamp adds UTC timezone to naive datetime."""
        naive_dt = datetime(2023, 12, 25, 10, 30, 45)

        result = normalize_timestamp(naive_dt)

        assert result.tzinfo == UTC
        assert result.year == 2023
        assert result.month == 12
        assert result.day == 25
        assert result.hour == 10
        assert result.minute == 30
        assert result.second == 45

    def test_normalize_timestamp_with_aware_datetime(self) -> None:
        """Test normalize_timestamp preserves timezone-aware datetime."""
        aware_dt = datetime(2023, 12, 25, 10, 30, 45, tzinfo=UTC)

        result = normalize_timestamp(aware_dt)

        assert result == aware_dt
        assert result.tzinfo == UTC

    def test_normalize_timestamp_with_different_timezone(self) -> None:
        """Test normalize_timestamp preserves different timezones."""
        import datetime as dt

        eastern = dt.timezone(dt.timedelta(hours=-5))  # EST
        aware_dt = datetime(2023, 12, 25, 15, 30, 45, tzinfo=eastern)

        result = normalize_timestamp(aware_dt)

        assert result == aware_dt
        assert result.tzinfo == eastern

    def test_normalize_timestamp_with_iso_string(self) -> None:
        """Test normalize_timestamp parses ISO format string."""
        iso_string = "2023-12-25T10:30:45"

        result = normalize_timestamp(iso_string)

        assert result.tzinfo == UTC
        assert result.year == 2023
        assert result.month == 12
        assert result.day == 25
        assert result.hour == 10
        assert result.minute == 30
        assert result.second == 45

    def test_normalize_timestamp_with_iso_string_z_suffix(self) -> None:
        """Test normalize_timestamp handles ISO string with 'Z' suffix."""
        iso_string = "2023-12-25T10:30:45Z"

        result = normalize_timestamp(iso_string)

        assert result.tzinfo == UTC
        assert result.year == 2023
        assert result.month == 12
        assert result.day == 25
        assert result.hour == 10
        assert result.minute == 30
        assert result.second == 45

    def test_normalize_timestamp_with_iso_string_timezone(self) -> None:
        """Test normalize_timestamp handles ISO string with timezone."""
        iso_string = "2023-12-25T10:30:45+00:00"

        result = normalize_timestamp(iso_string)

        assert result.tzinfo == UTC
        assert result.year == 2023
        assert result.month == 12
        assert result.day == 25
        assert result.hour == 10
        assert result.minute == 30
        assert result.second == 45

    def test_normalize_timestamp_with_invalid_string_fallback(self) -> None:
        """Test normalize_timestamp falls back to current time for invalid strings."""
        invalid_string = "not-a-valid-timestamp"

        # Should not raise an error, but fall back to current time
        result = normalize_timestamp(invalid_string)

        assert result.tzinfo == UTC
        # Should be recent (within last minute)
        now = datetime.now(UTC)
        time_diff = abs((now - result).total_seconds())
        assert time_diff < 60  # Within 1 minute

    def test_normalize_timestamp_with_microseconds(self) -> None:
        """Test normalize_timestamp preserves microseconds."""
        iso_string = "2023-12-25T10:30:45.123456"

        result = normalize_timestamp(iso_string)

        assert result.microsecond == 123456
        assert result.tzinfo == UTC

    def test_normalize_timestamp_function_type_safety(self) -> None:
        """Test that normalize_timestamp works with both string and datetime inputs."""
        # Test string input
        string_result = normalize_timestamp("2023-01-01T00:00:00Z")
        assert isinstance(string_result, datetime)
        assert string_result.tzinfo == UTC

        # Test datetime input
        dt_input = datetime(2023, 1, 1)
        dt_result = normalize_timestamp(dt_input)
        assert isinstance(dt_result, datetime)
        assert dt_result.tzinfo == UTC

    def test_normalize_timestamp_edge_cases(self) -> None:
        """Test normalize_timestamp with various edge cases."""
        # Test with empty string (should fallback)
        result1 = normalize_timestamp("")
        assert result1.tzinfo == UTC

        # Test with malformed ISO (should fallback)
        result2 = normalize_timestamp("2023-13-32T25:61:61")  # Invalid date/time
        assert result2.tzinfo == UTC

        # Test with partial ISO string (should fallback or parse)
        result3 = normalize_timestamp("2023-12-25")
        assert result3.tzinfo == UTC
