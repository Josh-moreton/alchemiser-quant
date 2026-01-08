"""Unit tests for MarketCalendarService.

Tests verify that:
1. Market calendar data is fetched and cached correctly
2. Trading day checks work for open and closed days
3. Early close detection works properly
4. should_trade_now logic handles various time scenarios
5. Cache expiration and refresh works as expected
"""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from unittest.mock import Mock

import pytest

from the_alchemiser.shared.errors.exceptions import TradingClientError
from the_alchemiser.shared.services.market_calendar_service import (
    MarketCalendarService,
    MarketDay,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_trading_client() -> Mock:
    """Create a mock Alpaca TradingClient."""
    return Mock()


@pytest.fixture
def mock_calendar_data() -> list[Mock]:
    """Create mock calendar data for a typical week.

    Returns mock data for Mon-Fri with normal hours (9:30-16:00)
    and one early close day (13:00).
    """
    # Create a week of trading days
    base_date = date(2026, 1, 5)  # Monday
    
    calendar = []
    for i in range(5):  # Mon-Fri
        day = Mock()
        day_date = base_date + timedelta(days=i)
        day.date = day_date.isoformat()
        day.open = "09:30"
        # Early close on Wednesday
        day.close = "13:00" if i == 2 else "16:00"
        calendar.append(day)
    
    return calendar


@pytest.fixture
def calendar_service(mock_trading_client: Mock) -> MarketCalendarService:
    """Create a MarketCalendarService with mocked client."""
    return MarketCalendarService(mock_trading_client)


# =============================================================================
# INITIALIZATION TESTS
# =============================================================================


def test_init_requires_trading_client() -> None:
    """Test that MarketCalendarService requires a trading client."""
    with pytest.raises(ValueError, match="trading_client cannot be None"):
        MarketCalendarService(None)  # type: ignore


def test_init_success(mock_trading_client: Mock) -> None:
    """Test successful initialization."""
    service = MarketCalendarService(mock_trading_client)
    assert service._trading_client == mock_trading_client
    assert service._calendar_cache == {}
    assert service._cache_timestamp == 0


# =============================================================================
# CALENDAR FETCHING TESTS
# =============================================================================


def test_fetch_calendar_success(
    calendar_service: MarketCalendarService,
    mock_trading_client: Mock,
    mock_calendar_data: list[Mock],
) -> None:
    """Test successful calendar fetch from API."""
    mock_trading_client.get_calendar.return_value = mock_calendar_data
    
    start_date = date(2026, 1, 5)
    end_date = date(2026, 1, 9)
    
    result = calendar_service._fetch_calendar_from_api(start_date, end_date)
    
    assert len(result) == 5
    assert all(isinstance(day, MarketDay) for day in result)
    
    # Check Monday
    monday = result[0]
    assert monday.date == date(2026, 1, 5)
    assert monday.open_time == time(9, 30)
    assert monday.close_time == time(16, 0)
    assert not monday.is_early_close
    
    # Check Wednesday (early close)
    wednesday = result[2]
    assert wednesday.date == date(2026, 1, 7)
    assert wednesday.open_time == time(9, 30)
    assert wednesday.close_time == time(13, 0)
    assert wednesday.is_early_close


def test_fetch_calendar_missing_fields(
    calendar_service: MarketCalendarService,
    mock_trading_client: Mock,
) -> None:
    """Test handling of calendar data with missing fields."""
    bad_day = Mock()
    bad_day.date = "2026-01-05"
    bad_day.open = None  # Missing open time
    bad_day.close = "16:00"
    
    mock_trading_client.get_calendar.return_value = [bad_day]
    
    start_date = date(2026, 1, 5)
    end_date = date(2026, 1, 5)
    
    # Should skip day with missing data and return empty list
    result = calendar_service._fetch_calendar_from_api(start_date, end_date)
    assert result == []


def test_fetch_calendar_api_error(
    calendar_service: MarketCalendarService,
    mock_trading_client: Mock,
) -> None:
    """Test handling of API errors during calendar fetch."""
    mock_trading_client.get_calendar.side_effect = Exception("API error")
    
    start_date = date(2026, 1, 5)
    end_date = date(2026, 1, 9)
    
    with pytest.raises(TradingClientError, match="Failed to fetch market calendar"):
        calendar_service._fetch_calendar_from_api(start_date, end_date)


# =============================================================================
# TRADING DAY CHECK TESTS
# =============================================================================


def test_is_trading_day_true(
    calendar_service: MarketCalendarService,
    mock_trading_client: Mock,
    mock_calendar_data: list[Mock],
) -> None:
    """Test is_trading_day returns True for trading days."""
    mock_trading_client.get_calendar.return_value = mock_calendar_data
    
    # Monday Jan 5, 2026
    target_date = date(2026, 1, 5)
    assert calendar_service.is_trading_day(target_date)


def test_is_trading_day_false_weekend(
    calendar_service: MarketCalendarService,
    mock_trading_client: Mock,
    mock_calendar_data: list[Mock],
) -> None:
    """Test is_trading_day returns False for weekends."""
    mock_trading_client.get_calendar.return_value = mock_calendar_data
    
    # Saturday Jan 3, 2026
    target_date = date(2026, 1, 3)
    assert not calendar_service.is_trading_day(target_date)


def test_is_trading_day_false_holiday(
    calendar_service: MarketCalendarService,
    mock_trading_client: Mock,
) -> None:
    """Test is_trading_day returns False for holidays."""
    # Return empty calendar (no trading days)
    mock_trading_client.get_calendar.return_value = []
    
    # Any date should be non-trading
    target_date = date(2026, 1, 1)
    assert not calendar_service.is_trading_day(target_date)


# =============================================================================
# MARKET DAY INFO TESTS
# =============================================================================


def test_get_market_day_returns_info(
    calendar_service: MarketCalendarService,
    mock_trading_client: Mock,
    mock_calendar_data: list[Mock],
) -> None:
    """Test get_market_day returns MarketDay info for trading days."""
    mock_trading_client.get_calendar.return_value = mock_calendar_data
    
    target_date = date(2026, 1, 5)
    market_day = calendar_service.get_market_day(target_date)
    
    assert market_day is not None
    assert market_day.date == target_date
    assert market_day.open_time == time(9, 30)
    assert market_day.close_time == time(16, 0)


def test_get_market_day_returns_none_for_closed_day(
    calendar_service: MarketCalendarService,
    mock_trading_client: Mock,
    mock_calendar_data: list[Mock],
) -> None:
    """Test get_market_day returns None for non-trading days."""
    mock_trading_client.get_calendar.return_value = mock_calendar_data
    
    # Saturday
    target_date = date(2026, 1, 3)
    market_day = calendar_service.get_market_day(target_date)
    
    assert market_day is None


def test_get_market_day_early_close_detected(
    calendar_service: MarketCalendarService,
    mock_trading_client: Mock,
    mock_calendar_data: list[Mock],
) -> None:
    """Test get_market_day detects early close days."""
    mock_trading_client.get_calendar.return_value = mock_calendar_data
    
    # Wednesday with early close
    target_date = date(2026, 1, 7)
    market_day = calendar_service.get_market_day(target_date)
    
    assert market_day is not None
    assert market_day.is_early_close
    assert market_day.close_time == time(13, 0)


# =============================================================================
# CACHE TESTS
# =============================================================================


def test_cache_prevents_multiple_api_calls(
    calendar_service: MarketCalendarService,
    mock_trading_client: Mock,
    mock_calendar_data: list[Mock],
) -> None:
    """Test that cache prevents redundant API calls."""
    mock_trading_client.get_calendar.return_value = mock_calendar_data
    
    target_date = date(2026, 1, 5)
    
    # First call - should hit API
    calendar_service.get_market_day(target_date)
    assert mock_trading_client.get_calendar.call_count == 1
    
    # Second call - should use cache
    calendar_service.get_market_day(target_date)
    assert mock_trading_client.get_calendar.call_count == 1


def test_cache_expires_after_ttl(
    calendar_service: MarketCalendarService,
    mock_trading_client: Mock,
    mock_calendar_data: list[Mock],
) -> None:
    """Test that cache expires after TTL."""
    mock_trading_client.get_calendar.return_value = mock_calendar_data
    
    target_date = date(2026, 1, 5)
    
    # First call - should hit API
    calendar_service.get_market_day(target_date)
    assert mock_trading_client.get_calendar.call_count == 1
    
    # Expire cache by setting timestamp to past
    calendar_service._cache_timestamp = 0
    
    # Second call - should hit API again
    calendar_service.get_market_day(target_date)
    assert mock_trading_client.get_calendar.call_count == 2


# =============================================================================
# SHOULD_TRADE_NOW TESTS
# =============================================================================


def test_should_trade_now_before_open(
    calendar_service: MarketCalendarService,
    mock_trading_client: Mock,
    mock_calendar_data: list[Mock],
) -> None:
    """Test should_trade_now returns False before market open."""
    mock_trading_client.get_calendar.return_value = mock_calendar_data
    
    # Monday 9:00 AM (before 9:30 open)
    check_time = datetime(2026, 1, 5, 9, 0, 0, tzinfo=UTC)
    
    should_trade, reason = calendar_service.should_trade_now(check_time=check_time)
    
    assert not should_trade
    assert "Before market open" in reason


def test_should_trade_now_after_open(
    calendar_service: MarketCalendarService,
    mock_trading_client: Mock,
    mock_calendar_data: list[Mock],
) -> None:
    """Test should_trade_now returns True during market hours."""
    mock_trading_client.get_calendar.return_value = mock_calendar_data
    
    # Monday 10:00 AM (after 9:30 open, well before 16:00 close)
    check_time = datetime(2026, 1, 5, 10, 0, 0, tzinfo=UTC)
    
    should_trade, reason = calendar_service.should_trade_now(check_time=check_time)
    
    assert should_trade
    assert "sufficient time before close" in reason


def test_should_trade_now_too_close_to_close(
    calendar_service: MarketCalendarService,
    mock_trading_client: Mock,
    mock_calendar_data: list[Mock],
) -> None:
    """Test should_trade_now returns False when too close to market close."""
    mock_trading_client.get_calendar.return_value = mock_calendar_data
    
    # Monday 3:50 PM (10 minutes before 16:00 close, less than 15 min buffer)
    check_time = datetime(2026, 1, 5, 15, 50, 0, tzinfo=UTC)
    
    should_trade, reason = calendar_service.should_trade_now(
        check_time=check_time,
        minutes_before_close=15,
    )
    
    assert not should_trade
    assert "Too close to market close" in reason


def test_should_trade_now_on_closed_day(
    calendar_service: MarketCalendarService,
    mock_trading_client: Mock,
    mock_calendar_data: list[Mock],
) -> None:
    """Test should_trade_now returns False on non-trading days."""
    mock_trading_client.get_calendar.return_value = mock_calendar_data
    
    # Saturday
    check_time = datetime(2026, 1, 3, 10, 0, 0, tzinfo=UTC)
    
    should_trade, reason = calendar_service.should_trade_now(check_time=check_time)
    
    assert not should_trade
    assert "Market is closed" in reason


def test_should_trade_now_early_close_respected(
    calendar_service: MarketCalendarService,
    mock_trading_client: Mock,
    mock_calendar_data: list[Mock],
) -> None:
    """Test should_trade_now respects early close times."""
    mock_trading_client.get_calendar.return_value = mock_calendar_data
    
    # Wednesday 12:50 PM (10 minutes before 13:00 early close)
    check_time = datetime(2026, 1, 7, 12, 50, 0, tzinfo=UTC)
    
    should_trade, reason = calendar_service.should_trade_now(
        check_time=check_time,
        minutes_before_close=15,
    )
    
    assert not should_trade
    assert "Too close to market close" in reason
    assert "13:00" in reason  # Early close time mentioned
