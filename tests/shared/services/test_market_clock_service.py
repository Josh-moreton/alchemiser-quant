"""Business Unit: shared | Status: current.

Tests for MarketClockService.

Tests market status detection and clock information retrieval.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock, Mock, patch

import pytest

from the_alchemiser.shared.errors.exceptions import (
    DataProviderError,
    TradingClientError,
)
from the_alchemiser.shared.services.market_clock_service import (
    MarketClockData,
    MarketClockService,
    MarketStatus,
)


class TestMarketClockServiceInitialization:
    """Test MarketClockService initialization."""

    def test_initialization_with_valid_client(self) -> None:
        """Test successful initialization with valid trading client."""
        mock_client = Mock()
        service = MarketClockService(mock_client)

        assert service._trading_client is mock_client

    def test_initialization_fails_with_none_client(self) -> None:
        """Test initialization fails when trading_client is None."""
        with pytest.raises(ValueError, match="trading_client cannot be None"):
            MarketClockService(None)  # type: ignore


class TestMarketClockServiceGetMarketStatus:
    """Test market status detection."""

    def test_get_market_status_when_open(self) -> None:
        """Test market status returns OPEN when market is open."""
        mock_client = Mock()
        mock_clock = Mock()
        mock_clock.is_open = True
        mock_clock.timestamp = datetime.now(UTC)
        mock_clock.next_open = None
        mock_clock.next_close = datetime.now(UTC)
        mock_client.get_clock.return_value = mock_clock

        service = MarketClockService(mock_client)
        status = service.get_market_status()

        assert status == MarketStatus.OPEN
        mock_client.get_clock.assert_called_once()

    def test_get_market_status_when_closed(self) -> None:
        """Test market status returns CLOSED when market is closed."""
        mock_client = Mock()
        mock_clock = Mock()
        mock_clock.is_open = False
        mock_clock.timestamp = datetime.now(UTC)
        mock_clock.next_open = datetime.now(UTC)
        mock_clock.next_close = None
        mock_client.get_clock.return_value = mock_clock

        service = MarketClockService(mock_client)
        status = service.get_market_status()

        assert status == MarketStatus.CLOSED
        mock_client.get_clock.assert_called_once()

    def test_get_market_status_with_correlation_id(self) -> None:
        """Test market status includes correlation_id in logging context."""
        mock_client = Mock()
        mock_clock = Mock()
        mock_clock.is_open = True
        mock_clock.timestamp = datetime.now(UTC)
        mock_clock.next_open = None
        mock_clock.next_close = datetime.now(UTC)
        mock_client.get_clock.return_value = mock_clock

        service = MarketClockService(mock_client)
        correlation_id = "test-correlation-123"

        status = service.get_market_status(correlation_id=correlation_id)

        assert status == MarketStatus.OPEN

    def test_get_market_status_raises_on_api_error(self) -> None:
        """Test market status raises TradingClientError on API failure."""
        mock_client = Mock()
        mock_client.get_clock.side_effect = Exception("API error")

        service = MarketClockService(mock_client)

        with pytest.raises(TradingClientError, match="Failed to fetch market clock"):
            service.get_market_status()

    def test_get_market_status_raises_on_missing_attribute(self) -> None:
        """Test market status handles missing attributes gracefully with defaults."""
        mock_client = Mock()
        mock_clock = Mock(spec=[])  # Empty spec - no attributes
        mock_client.get_clock.return_value = mock_clock

        service = MarketClockService(mock_client)

        # Should not raise - uses defaults from getattr
        status = service.get_market_status()

        # Should return CLOSED (is_open defaults to False)
        assert status == MarketStatus.CLOSED


class TestMarketClockServiceIsMarketOpen:
    """Test is_market_open convenience method."""

    def test_is_market_open_returns_true_when_open(self) -> None:
        """Test is_market_open returns True when market is open."""
        mock_client = Mock()
        mock_clock = Mock()
        mock_clock.is_open = True
        mock_clock.timestamp = datetime.now(UTC)
        mock_clock.next_open = None
        mock_clock.next_close = datetime.now(UTC)
        mock_client.get_clock.return_value = mock_clock

        service = MarketClockService(mock_client)
        is_open = service.is_market_open()

        assert is_open is True

    def test_is_market_open_returns_false_when_closed(self) -> None:
        """Test is_market_open returns False when market is closed."""
        mock_client = Mock()
        mock_clock = Mock()
        mock_clock.is_open = False
        mock_clock.timestamp = datetime.now(UTC)
        mock_clock.next_open = datetime.now(UTC)
        mock_clock.next_close = None
        mock_client.get_clock.return_value = mock_clock

        service = MarketClockService(mock_client)
        is_open = service.is_market_open()

        assert is_open is False

    def test_is_market_open_with_correlation_id(self) -> None:
        """Test is_market_open passes correlation_id correctly."""
        mock_client = Mock()
        mock_clock = Mock()
        mock_clock.is_open = True
        mock_clock.timestamp = datetime.now(UTC)
        mock_clock.next_open = None
        mock_clock.next_close = datetime.now(UTC)
        mock_client.get_clock.return_value = mock_clock

        service = MarketClockService(mock_client)
        correlation_id = "test-corr-456"

        is_open = service.is_market_open(correlation_id=correlation_id)

        assert is_open is True


class TestMarketClockServiceGetClockInfo:
    """Test get_clock_info method."""

    def test_get_clock_info_returns_complete_data(self) -> None:
        """Test get_clock_info returns all clock data fields."""
        mock_client = Mock()
        now = datetime.now(UTC)
        next_open_time = datetime(2025, 10, 18, 13, 30, tzinfo=UTC)
        next_close_time = datetime(2025, 10, 18, 20, 0, tzinfo=UTC)

        mock_clock = Mock()
        mock_clock.is_open = True
        mock_clock.timestamp = now
        mock_clock.next_open = next_open_time
        mock_clock.next_close = next_close_time
        mock_client.get_clock.return_value = mock_clock

        service = MarketClockService(mock_client)
        clock_info = service.get_clock_info()

        assert isinstance(clock_info, MarketClockData)
        assert clock_info.is_open is True
        assert clock_info.timestamp == now
        assert clock_info.next_open == next_open_time
        assert clock_info.next_close == next_close_time

    def test_get_clock_info_with_correlation_id(self) -> None:
        """Test get_clock_info includes correlation_id in logging."""
        mock_client = Mock()
        mock_clock = Mock()
        mock_clock.is_open = False
        mock_clock.timestamp = datetime.now(UTC)
        mock_clock.next_open = datetime.now(UTC)
        mock_clock.next_close = None
        mock_client.get_clock.return_value = mock_clock

        service = MarketClockService(mock_client)
        correlation_id = "test-corr-789"

        clock_info = service.get_clock_info(correlation_id=correlation_id)

        assert isinstance(clock_info, MarketClockData)

    def test_get_clock_info_raises_on_api_error(self) -> None:
        """Test get_clock_info raises TradingClientError on API failure."""
        mock_client = Mock()
        mock_client.get_clock.side_effect = Exception("Connection failed")

        service = MarketClockService(mock_client)

        with pytest.raises(TradingClientError, match="Failed to fetch market clock"):
            service.get_clock_info()


class TestMarketClockDataNamedTuple:
    """Test MarketClockData NamedTuple."""

    def test_market_clock_data_creation(self) -> None:
        """Test MarketClockData can be created with all fields."""
        now = datetime.now(UTC)
        next_open = datetime(2025, 10, 18, 13, 30, tzinfo=UTC)
        next_close = datetime(2025, 10, 18, 20, 0, tzinfo=UTC)

        clock_data = MarketClockData(
            is_open=True,
            timestamp=now,
            next_open=next_open,
            next_close=next_close,
        )

        assert clock_data.is_open is True
        assert clock_data.timestamp == now
        assert clock_data.next_open == next_open
        assert clock_data.next_close == next_close

    def test_market_clock_data_with_none_values(self) -> None:
        """Test MarketClockData accepts None for optional fields."""
        now = datetime.now(UTC)

        clock_data = MarketClockData(
            is_open=False,
            timestamp=now,
            next_open=None,
            next_close=None,
        )

        assert clock_data.is_open is False
        assert clock_data.timestamp == now
        assert clock_data.next_open is None
        assert clock_data.next_close is None


class TestMarketStatusEnum:
    """Test MarketStatus enumeration."""

    def test_market_status_values(self) -> None:
        """Test MarketStatus enum has correct values."""
        assert MarketStatus.OPEN.value == "open"
        assert MarketStatus.CLOSED.value == "closed"
        assert MarketStatus.EXTENDED_HOURS.value == "extended_hours"

    def test_market_status_string_comparison(self) -> None:
        """Test MarketStatus can be compared with strings."""
        assert MarketStatus.OPEN == "open"
        assert MarketStatus.CLOSED == "closed"
        assert MarketStatus.EXTENDED_HOURS == "extended_hours"
