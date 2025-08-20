"""Tests for Alert value object."""

import pytest
from datetime import datetime, UTC

from the_alchemiser.domain.strategies.value_objects.alert import Alert
from the_alchemiser.domain.trading.value_objects.symbol import Symbol


class TestAlert:
    """Test cases for Alert value object."""

    def test_valid_alert_creation(self) -> None:
        """Test creating valid alerts."""
        symbol = Symbol("AAPL")
        
        # Test with all fields
        alert = Alert(
            message="Test alert message",
            severity="WARNING",
            symbol=symbol,
        )
        
        assert alert.message == "Test alert message"
        assert alert.severity == "WARNING"
        assert alert.symbol == symbol
        assert isinstance(alert.timestamp, datetime)

    def test_alert_without_symbol(self) -> None:
        """Test creating alert without symbol."""
        alert = Alert(
            message="System alert",
            severity="INFO",
        )
        
        assert alert.message == "System alert"
        assert alert.severity == "INFO"
        assert alert.symbol is None

    def test_all_severity_levels(self) -> None:
        """Test all valid severity levels."""
        severities = ["INFO", "WARNING", "ERROR"]
        
        for severity in severities:
            alert = Alert(
                message=f"Test {severity} message",
                severity=severity,  # type: ignore
            )
            assert alert.severity == severity

    def test_invalid_severity(self) -> None:
        """Test that invalid severity values raise errors."""
        with pytest.raises(ValueError, match="Invalid alert severity"):
            Alert(
                message="Test message",
                severity="INVALID",  # type: ignore
            )

        with pytest.raises(ValueError, match="Invalid alert severity"):
            Alert(
                message="Test message",
                severity="DEBUG",  # type: ignore
            )

    def test_alert_immutability(self) -> None:
        """Test that Alert objects are immutable."""
        alert = Alert(message="Test", severity="INFO")
        
        # Should not be able to modify fields
        with pytest.raises(AttributeError):
            alert.message = "Modified"  # type: ignore

        with pytest.raises(AttributeError):
            alert.severity = "ERROR"  # type: ignore

    def test_alert_with_custom_timestamp(self) -> None:
        """Test alert with custom timestamp."""
        custom_time = datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC)
        alert = Alert(
            message="Test message",
            severity="ERROR",
            timestamp=custom_time,
        )
        
        assert alert.timestamp == custom_time

    def test_default_timestamp_is_utc(self) -> None:
        """Test that default timestamp is in UTC."""
        alert = Alert(message="Test", severity="INFO")
        
        assert alert.timestamp.tzinfo == UTC
        # Should be very recent (within last few seconds)
        now = datetime.now(UTC)
        time_diff = (now - alert.timestamp).total_seconds()
        assert time_diff < 5  # Should be created within 5 seconds

    def test_alert_equality(self) -> None:
        """Test alert equality comparison."""
        timestamp = datetime.now(UTC)
        symbol = Symbol("AAPL")
        
        alert1 = Alert(
            message="Test",
            severity="INFO",
            symbol=symbol,
            timestamp=timestamp,
        )
        alert2 = Alert(
            message="Test",
            severity="INFO",
            symbol=symbol,
            timestamp=timestamp,
        )
        alert3 = Alert(
            message="Different",
            severity="INFO",
            symbol=symbol,
            timestamp=timestamp,
        )
        
        assert alert1 == alert2
        assert alert1 != alert3

    def test_alert_with_symbol_validation(self) -> None:
        """Test that alert works with valid Symbol objects."""
        # Valid symbol
        symbol = Symbol("TSLA")
        alert = Alert(
            message="Stock alert",
            severity="WARNING",
            symbol=symbol,
        )
        
        assert alert.symbol == symbol
        assert alert.symbol.value == "TSLA"