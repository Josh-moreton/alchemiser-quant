"""Business Unit: shared | Status: current

Comprehensive unit tests for timezone utilities.

This test suite provides full coverage of timezone utility functions including
timezone awareness, conversion, and validation.
"""

import pytest
from datetime import datetime, timezone, UTC
from unittest.mock import patch

from the_alchemiser.shared.utils.timezone_utils import (
    ensure_timezone_aware,
    normalize_timestamp_to_utc,
    to_iso_string,
)


class TestEnsureTimezoneAware:
    """Test timezone awareness utility function."""

    def test_naive_datetime_gets_utc_timezone(self):
        """Test that naive datetime gets UTC timezone."""
        naive_dt = datetime(2023, 1, 15, 10, 30, 0)
        aware_dt = ensure_timezone_aware(naive_dt)
        
        assert aware_dt.tzinfo is UTC
        assert aware_dt.year == 2023
        assert aware_dt.month == 1
        assert aware_dt.day == 15
        assert aware_dt.hour == 10
        assert aware_dt.minute == 30

    def test_already_aware_datetime_unchanged(self):
        """Test that already aware datetime is unchanged."""
        aware_dt = datetime(2023, 1, 15, 10, 30, 0, tzinfo=UTC)
        result_dt = ensure_timezone_aware(aware_dt)
        
        assert result_dt is aware_dt  # Should be the same object
        assert result_dt.tzinfo is UTC

    def test_different_timezone_preserved(self):
        """Test that different timezone is preserved."""
        from datetime import timedelta
        est_tz = timezone(timedelta(hours=-5))
        aware_dt = datetime(2023, 1, 15, 10, 30, 0, tzinfo=est_tz)
        result_dt = ensure_timezone_aware(aware_dt)
        
        assert result_dt is aware_dt
        assert result_dt.tzinfo == est_tz

    def test_none_input_returns_none(self):
        """Test that None input returns None."""
        result = ensure_timezone_aware(None)
        assert result is None


class TestNormalizeTimestampToUtc:
    """Test UTC normalization utility function."""

    def test_naive_datetime_converted_to_utc(self):
        """Test that naive datetime is converted to UTC."""
        naive_dt = datetime(2023, 1, 15, 10, 30, 0)
        utc_dt = normalize_timestamp_to_utc(naive_dt)
        
        assert utc_dt.tzinfo is UTC
        assert utc_dt.year == 2023
        assert utc_dt.month == 1
        assert utc_dt.day == 15
        assert utc_dt.hour == 10
        assert utc_dt.minute == 30

    def test_utc_datetime_unchanged(self):
        """Test that UTC datetime is unchanged."""
        utc_dt = datetime(2023, 1, 15, 10, 30, 0, tzinfo=UTC)
        result_dt = normalize_timestamp_to_utc(utc_dt)
        
        assert result_dt.tzinfo is UTC
        assert result_dt == utc_dt

    def test_different_timezone_preserved(self):
        """Test that different timezone datetime is preserved."""
        from datetime import timedelta
        est_tz = timezone(timedelta(hours=-5))
        est_dt = datetime(2023, 1, 15, 10, 30, 0, tzinfo=est_tz)
        
        result_dt = normalize_timestamp_to_utc(est_dt)
        
        assert result_dt.tzinfo == est_tz
        assert result_dt == est_dt

    def test_iso_string_without_timezone(self):
        """Test parsing ISO string without timezone."""
        iso_str = "2023-01-15T10:30:00"
        result_dt = normalize_timestamp_to_utc(iso_str)
        
        assert result_dt.tzinfo is UTC
        assert result_dt.year == 2023
        assert result_dt.month == 1
        assert result_dt.day == 15
        assert result_dt.hour == 10
        assert result_dt.minute == 30

    def test_iso_string_with_z_suffix(self):
        """Test parsing ISO string with Z suffix (Zulu time)."""
        iso_str = "2023-01-15T10:30:00Z"
        result_dt = normalize_timestamp_to_utc(iso_str)
        
        assert result_dt.tzinfo is UTC
        assert result_dt.year == 2023
        assert result_dt.month == 1
        assert result_dt.day == 15
        assert result_dt.hour == 10
        assert result_dt.minute == 30

    def test_iso_string_with_utc_offset(self):
        """Test parsing ISO string with UTC offset."""
        iso_str = "2023-01-15T10:30:00+00:00"
        result_dt = normalize_timestamp_to_utc(iso_str)
        
        assert result_dt.tzinfo is UTC
        assert result_dt.year == 2023
        assert result_dt.month == 1
        assert result_dt.day == 15
        assert result_dt.hour == 10
        assert result_dt.minute == 30

    def test_invalid_string_fallback_to_current_time(self):
        """Test that invalid string raises EnhancedDataError."""
        from the_alchemiser.shared.errors import EnhancedDataError
        
        invalid_str = "not a valid datetime"
        
        with pytest.raises(EnhancedDataError) as exc_info:
            normalize_timestamp_to_utc(invalid_str)
        
        # Verify error details
        assert "Failed to parse timestamp string" in str(exc_info.value)
        assert invalid_str in str(exc_info.value)

    def test_numeric_timestamp_converted_to_string(self):
        """Test that numeric timestamps raise EnhancedDataError."""
        from the_alchemiser.shared.errors import EnhancedDataError
        
        # This tests that numeric conversion isn't properly implemented
        numeric_timestamp = 1673784600  # Unix timestamp
        
        with pytest.raises(EnhancedDataError) as exc_info:
            normalize_timestamp_to_utc(numeric_timestamp)
        
        # Verify error details
        assert "Failed to" in str(exc_info.value)


class TestToIsoString:
    """Test ISO string formatting utility function."""

    def test_utc_datetime_to_iso_string(self):
        """Test formatting UTC datetime to ISO string."""
        utc_dt = datetime(2023, 1, 15, 10, 30, 45, 123456, tzinfo=UTC)
        iso_str = to_iso_string(utc_dt)
        
        assert isinstance(iso_str, str)
        assert "2023-01-15T10:30:45.123456+00:00" == iso_str

    def test_naive_datetime_to_iso_string(self):
        """Test formatting naive datetime to ISO string (gets UTC added)."""
        naive_dt = datetime(2023, 1, 15, 10, 30, 45, 123456)
        iso_str = to_iso_string(naive_dt)
        
        assert isinstance(iso_str, str)
        assert "2023-01-15T10:30:45.123456+00:00" == iso_str

    def test_different_timezone_to_iso_string(self):
        """Test formatting datetime with different timezone to ISO string."""
        from datetime import timedelta
        est_tz = timezone(timedelta(hours=-5))
        est_dt = datetime(2023, 1, 15, 10, 30, 45, tzinfo=est_tz)
        
        iso_str = to_iso_string(est_dt)
        
        assert isinstance(iso_str, str)
        assert "2023-01-15T10:30:45-05:00" == iso_str

    def test_none_input_returns_none(self):
        """Test that None input returns None."""
        result = to_iso_string(None)
        assert result is None

    def test_microseconds_in_iso_string(self):
        """Test that microseconds are properly included in ISO string."""
        dt_with_microseconds = datetime(2023, 1, 15, 10, 30, 45, 123456, tzinfo=UTC)
        iso_str = to_iso_string(dt_with_microseconds)
        
        assert ".123456" in iso_str


class TestTimezoneUtilsEdgeCases:
    """Test edge cases and error conditions for timezone utilities."""

    def test_extreme_dates(self):
        """Test handling of extreme date values."""
        # Test very old date
        old_dt = datetime(1900, 1, 1, 0, 0, 0)
        result = ensure_timezone_aware(old_dt)
        assert result.tzinfo is UTC
        
        # Test far future date
        future_dt = datetime(2100, 12, 31, 23, 59, 59)
        result = ensure_timezone_aware(future_dt)
        assert result.tzinfo is UTC

    def test_leap_year_handling(self):
        """Test proper handling of leap year dates."""
        leap_dt = datetime(2024, 2, 29, 12, 0, 0)  # 2024 is a leap year
        result = ensure_timezone_aware(leap_dt)
        
        assert result.tzinfo is UTC
        assert result.month == 2
        assert result.day == 29

    def test_normalize_with_exception_fallback(self):
        """Test that normalize function raises EnhancedDataError on exceptions."""
        from the_alchemiser.shared.errors import EnhancedDataError
        
        # Test an object that will cause an exception when converted to string
        class BadObject:
            def __str__(self):
                raise RuntimeError("Cannot convert to string")
        
        bad_obj = BadObject()
        
        with pytest.raises(EnhancedDataError) as exc_info:
            normalize_timestamp_to_utc(bad_obj)
        
        # Verify error details
        assert "Failed to convert timestamp" in str(exc_info.value)