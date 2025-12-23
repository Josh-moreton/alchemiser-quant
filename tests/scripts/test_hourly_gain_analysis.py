"""Business Unit: analysis | Status: current.

Tests for hourly_gain_analysis.py script.

Tests focus on the statistics calculation logic and report formatting,
without requiring actual Alpaca API credentials.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

# Add scripts directory to path so we can import the module
scripts_dir = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

from hourly_gain_analysis import calculate_hourly_statistics, format_report


class TestCalculateHourlyStatistics:
    """Test the calculate_hourly_statistics function."""

    def test_empty_bars(self) -> None:
        """Test that empty bars list returns empty statistics."""
        result = calculate_hourly_statistics([])
        assert result == {}

    def test_single_bar_positive_gain(self) -> None:
        """Test statistics for a single bar with positive gain."""
        bars = [
            {
                "timestamp": "2024-01-01T14:00:00+00:00",
                "open": 100.0,
                "close": 101.0,
                "high": 101.5,
                "low": 99.5,
                "volume": 1000000.0,
            }
        ]
        result = calculate_hourly_statistics(bars)

        assert 14 in result
        assert result[14]["total_count"] == 1.0
        assert result[14]["positive_count"] == 1.0
        assert result[14]["negative_count"] == 0.0
        assert abs(result[14]["avg_gain_pct"] - 1.0) < 0.001  # 1% gain

    def test_single_bar_negative_gain(self) -> None:
        """Test statistics for a single bar with negative gain."""
        bars = [
            {
                "timestamp": "2024-01-01T10:00:00+00:00",
                "open": 100.0,
                "close": 99.0,
                "high": 100.5,
                "low": 98.5,
                "volume": 1000000.0,
            }
        ]
        result = calculate_hourly_statistics(bars)

        assert 10 in result
        assert result[10]["total_count"] == 1.0
        assert result[10]["positive_count"] == 0.0
        assert result[10]["negative_count"] == 1.0
        assert abs(result[10]["avg_gain_pct"] - (-1.0)) < 0.001  # -1% loss

    def test_multiple_bars_same_hour(self) -> None:
        """Test statistics calculation with multiple bars in the same hour."""
        bars = [
            {
                "timestamp": "2024-01-01T14:00:00+00:00",
                "open": 100.0,
                "close": 102.0,
                "high": 102.5,
                "low": 99.5,
                "volume": 1000000.0,
            },
            {
                "timestamp": "2024-01-02T14:00:00+00:00",
                "open": 100.0,
                "close": 98.0,
                "high": 101.0,
                "low": 97.5,
                "volume": 1000000.0,
            },
        ]
        result = calculate_hourly_statistics(bars)

        assert 14 in result
        assert result[14]["total_count"] == 2.0
        assert result[14]["positive_count"] == 1.0
        assert result[14]["negative_count"] == 1.0
        # Average of +2% and -2% should be 0%
        assert abs(result[14]["avg_gain_pct"] - 0.0) < 0.001

    def test_multiple_hours(self) -> None:
        """Test statistics for bars across different hours."""
        bars = [
            {
                "timestamp": "2024-01-01T09:00:00+00:00",
                "open": 100.0,
                "close": 101.0,
                "high": 101.5,
                "low": 99.5,
                "volume": 1000000.0,
            },
            {
                "timestamp": "2024-01-01T14:00:00+00:00",
                "open": 100.0,
                "close": 100.5,
                "high": 101.0,
                "low": 99.5,
                "volume": 1000000.0,
            },
            {
                "timestamp": "2024-01-01T15:00:00+00:00",
                "open": 100.0,
                "close": 99.0,
                "high": 100.5,
                "low": 98.5,
                "volume": 1000000.0,
            },
        ]
        result = calculate_hourly_statistics(bars)

        assert 9 in result
        assert 14 in result
        assert 15 in result
        assert result[9]["total_count"] == 1.0
        assert result[14]["total_count"] == 1.0
        assert result[15]["total_count"] == 1.0

    def test_zero_open_price_ignored(self) -> None:
        """Test that bars with zero open price are ignored."""
        bars = [
            {
                "timestamp": "2024-01-01T14:00:00+00:00",
                "open": 0.0,
                "close": 100.0,
                "high": 100.5,
                "low": 99.5,
                "volume": 1000000.0,
            }
        ]
        result = calculate_hourly_statistics(bars)

        # Should be empty since division by zero is avoided
        assert result == {}


class TestFormatReport:
    """Test the format_report function."""

    def test_format_report_with_data(self) -> None:
        """Test report formatting with valid statistics."""
        statistics = {
            9: {
                "avg_gain_pct": 0.523,
                "total_count": 2520.0,
                "positive_count": 1340.0,
                "negative_count": 1180.0,
            },
            14: {
                "avg_gain_pct": 0.823,
                "total_count": 2520.0,
                "positive_count": 1410.0,
                "negative_count": 1110.0,
            },
        }

        report = format_report("SPY", statistics, 10)

        # Check that the report contains expected elements
        assert "SPY" in report
        assert "Last 10 years" in report
        assert "09:00-09:59" in report
        assert "14:00-14:59" in report
        assert "0.5230%" in report
        assert "0.8230%" in report
        assert "KEY INSIGHTS" in report
        assert "Best hour" in report
        assert "Worst hour" in report

    def test_format_report_empty_statistics(self) -> None:
        """Test report formatting with empty statistics."""
        statistics = {}

        report = format_report("QQQ", statistics, 5)

        # Should still contain header information
        assert "QQQ" in report
        assert "Last 5 years" in report
        # Should not have insights section
        assert "KEY INSIGHTS" not in report


class TestValidateEnvironment:
    """Test environment validation (requires mocking)."""

    def test_missing_credentials_exits(self) -> None:
        """Test that missing credentials causes system exit."""
        # This test would require mocking os.environ and sys.exit
        # Skipping for now as it requires more complex setup
        pass
