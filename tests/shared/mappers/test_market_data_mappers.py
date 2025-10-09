#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Comprehensive tests for market_data_mappers module.

Validates correctness of data transformation from external sources to domain models,
with focus on Decimal precision, timezone handling, and error cases.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest

from the_alchemiser.shared.mappers.market_data_mappers import (
    _parse_ts,
    bars_to_domain,
    quote_to_domain,
)
from the_alchemiser.shared.types.market_data import BarModel, QuoteModel


class TestParseTsFunction:
    """Test suite for _parse_ts timestamp parsing function."""

    def test_parse_ts_with_datetime_returns_as_is(self) -> None:
        """Test that datetime objects are returned unchanged."""
        dt = datetime(2024, 1, 1, 10, 30, 0, tzinfo=UTC)
        result = _parse_ts(dt)
        assert result == dt
        assert result is dt  # Same object

    def test_parse_ts_with_iso8601_string(self) -> None:
        """Test parsing ISO8601 string with timezone."""
        result = _parse_ts("2024-01-01T10:30:00+00:00")
        assert result == datetime(2024, 1, 1, 10, 30, 0, tzinfo=UTC)

    def test_parse_ts_with_iso8601_z_suffix(self) -> None:
        """Test parsing ISO8601 string with Z (Zulu/UTC) suffix."""
        result = _parse_ts("2024-01-01T10:30:00Z")
        assert result == datetime(2024, 1, 1, 10, 30, 0, tzinfo=UTC)
        assert result.tzinfo == UTC

    def test_parse_ts_with_unix_seconds(self) -> None:
        """Test parsing Unix timestamp in seconds."""
        # 1609502400 = 2021-01-01 10:00:00 UTC
        result = _parse_ts(1609502400)
        assert result == datetime(2021, 1, 1, 10, 0, 0, tzinfo=UTC)

    def test_parse_ts_with_unix_milliseconds(self) -> None:
        """Test parsing Unix timestamp in milliseconds."""
        # 1609502400000 = 2021-01-01 10:00:00 UTC (in milliseconds)
        result = _parse_ts(1609502400000)
        assert result == datetime(2021, 1, 1, 10, 0, 0, tzinfo=UTC)

    def test_parse_ts_with_float_seconds(self) -> None:
        """Test parsing Unix timestamp as float in seconds."""
        result = _parse_ts(1609502400.5)
        expected = datetime(2021, 1, 1, 10, 0, 0, 500000, tzinfo=UTC)
        assert result == expected

    def test_parse_ts_with_none_returns_none(self) -> None:
        """Test that None input returns None."""
        result = _parse_ts(None)
        assert result is None

    def test_parse_ts_with_invalid_string_returns_none(self) -> None:
        """Test that invalid string returns None instead of raising."""
        result = _parse_ts("not a date")
        assert result is None

    def test_parse_ts_with_empty_string_returns_none(self) -> None:
        """Test that empty string returns None."""
        result = _parse_ts("")
        assert result is None

    def test_parse_ts_with_whitespace_string(self) -> None:
        """Test that string with whitespace is handled correctly."""
        result = _parse_ts("  2024-01-01T10:30:00Z  ")
        assert result == datetime(2024, 1, 1, 10, 30, 0, tzinfo=UTC)

    def test_parse_ts_heuristic_boundary_at_10_to_11(self) -> None:
        """Test the ms/seconds heuristic boundary at 10^11."""
        # Just below threshold - treated as seconds
        just_below = 10**11 - 1
        result_below = _parse_ts(just_below)
        # Just above threshold - treated as milliseconds
        just_above = 10**11 + 1
        result_above = _parse_ts(just_above)
        
        # Both should parse successfully
        assert result_below is not None
        assert result_above is not None
        # Above should be much earlier since divided by 1000
        assert result_above < result_below


class TestBarsToDomainFunction:
    """Test suite for bars_to_domain conversion function."""

    def test_bars_to_domain_with_valid_data(self) -> None:
        """Test successful conversion of valid bar data."""
        rows = [
            {
                "t": "2024-01-01T10:00:00Z",
                "S": "AAPL",
                "o": "150.00",
                "h": "155.00",
                "l": "149.00",
                "c": "154.00",
                "v": 1000000,
            }
        ]
        result = bars_to_domain(rows)
        
        assert len(result) == 1
        bar = result[0]
        assert bar.symbol == "AAPL"
        assert bar.timestamp == datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC)
        assert bar.open == Decimal("150.00")
        assert bar.high == Decimal("155.00")
        assert bar.low == Decimal("149.00")
        assert bar.close == Decimal("154.00")
        assert bar.volume == 1000000

    def test_bars_to_domain_with_long_keys(self) -> None:
        """Test conversion with long-form key names."""
        rows = [
            {
                "timestamp": "2024-01-01T10:00:00Z",
                "symbol": "AAPL",
                "open": 150.00,
                "high": 155.00,
                "low": 149.00,
                "close": 154.00,
                "volume": 1000000,
            }
        ]
        result = bars_to_domain(rows)
        
        assert len(result) == 1
        assert result[0].symbol == "AAPL"
        assert result[0].open == Decimal("150.00")

    def test_bars_to_domain_with_default_symbol(self) -> None:
        """Test using default symbol parameter."""
        rows = [
            {
                "t": "2024-01-01T10:00:00Z",
                "o": "150.00",
                "h": "155.00",
                "l": "149.00",
                "c": "154.00",
                "v": 1000000,
            }
        ]
        result = bars_to_domain(rows, symbol="TSLA")
        
        assert len(result) == 1
        assert result[0].symbol == "TSLA"

    def test_bars_to_domain_preserves_decimal_precision(self) -> None:
        """Test that Decimal precision is maintained through conversion."""
        rows = [
            {
                "t": "2024-01-01T10:00:00Z",
                "S": "AAPL",
                "o": "150.123456789",
                "h": "155.987654321",
                "l": "149.000000001",
                "c": "154.555555555",
                "v": 1000000,
            }
        ]
        result = bars_to_domain(rows)
        
        assert len(result) == 1
        bar = result[0]
        assert bar.open == Decimal("150.123456789")
        assert bar.high == Decimal("155.987654321")
        assert bar.low == Decimal("149.000000001")
        assert bar.close == Decimal("154.555555555")

    def test_bars_to_domain_skips_rows_without_timestamp(self) -> None:
        """Test that rows without valid timestamps are skipped."""
        rows = [
            {"S": "AAPL", "o": "150", "h": "155", "l": "149", "c": "154", "v": 1000},
            {
                "t": "2024-01-01T10:00:00Z",
                "S": "MSFT",
                "o": "250",
                "h": "255",
                "l": "249",
                "c": "254",
                "v": 2000,
            },
        ]
        result = bars_to_domain(rows)
        
        # First row should be skipped, only second row included
        assert len(result) == 1
        assert result[0].symbol == "MSFT"

    def test_bars_to_domain_skips_rows_with_invalid_timestamp(self) -> None:
        """Test that rows with invalid timestamps are skipped."""
        rows = [
            {
                "t": "invalid date",
                "S": "AAPL",
                "o": "150",
                "h": "155",
                "l": "149",
                "c": "154",
                "v": 1000,
            },
            {
                "t": "2024-01-01T10:00:00Z",
                "S": "MSFT",
                "o": "250",
                "h": "255",
                "l": "249",
                "c": "254",
                "v": 2000,
            },
        ]
        result = bars_to_domain(rows)
        
        assert len(result) == 1
        assert result[0].symbol == "MSFT"

    def test_bars_to_domain_with_empty_list_returns_empty(self) -> None:
        """Test that empty input returns empty list."""
        result = bars_to_domain([])
        assert result == []

    def test_bars_to_domain_with_multiple_bars(self) -> None:
        """Test conversion of multiple bars."""
        rows = [
            {
                "t": "2024-01-01T10:00:00Z",
                "S": "AAPL",
                "o": "150",
                "h": "155",
                "l": "149",
                "c": "154",
                "v": 1000,
            },
            {
                "t": "2024-01-01T11:00:00Z",
                "S": "AAPL",
                "o": "154",
                "h": "158",
                "l": "153",
                "c": "157",
                "v": 2000,
            },
            {
                "t": "2024-01-01T12:00:00Z",
                "S": "AAPL",
                "o": "157",
                "h": "160",
                "l": "156",
                "c": "159",
                "v": 3000,
            },
        ]
        result = bars_to_domain(rows)
        
        assert len(result) == 3
        assert result[0].timestamp < result[1].timestamp < result[2].timestamp
        assert all(bar.symbol == "AAPL" for bar in result)

    def test_bars_to_domain_handles_zero_prices(self) -> None:
        """Test that zero prices are handled (defaults from missing data)."""
        rows = [
            {
                "t": "2024-01-01T10:00:00Z",
                "S": "AAPL",
                # Missing o, h, l, c
                "v": 1000,
            }
        ]
        result = bars_to_domain(rows)
        
        assert len(result) == 1
        assert result[0].open == Decimal("0")
        assert result[0].high == Decimal("0")
        assert result[0].low == Decimal("0")
        assert result[0].close == Decimal("0")

    def test_bars_to_domain_handles_zero_volume(self) -> None:
        """Test that zero volume is handled."""
        rows = [
            {
                "t": "2024-01-01T10:00:00Z",
                "S": "AAPL",
                "o": "150",
                "h": "155",
                "l": "149",
                "c": "154",
                # Missing v
            }
        ]
        result = bars_to_domain(rows)
        
        assert len(result) == 1
        assert result[0].volume == 0

    def test_bars_to_domain_defaults_to_unknown_symbol(self) -> None:
        """Test that missing symbol defaults to UNKNOWN."""
        rows = [
            {
                "t": "2024-01-01T10:00:00Z",
                "o": "150",
                "h": "155",
                "l": "149",
                "c": "154",
                "v": 1000,
            }
        ]
        result = bars_to_domain(rows)
        
        assert len(result) == 1
        assert result[0].symbol == "UNKNOWN"

    def test_bars_to_domain_with_unix_timestamps(self) -> None:
        """Test conversion with Unix timestamps."""
        rows = [
            {
                "t": 1609502400,  # 2021-01-01 10:00:00 UTC
                "S": "AAPL",
                "o": "150",
                "h": "155",
                "l": "149",
                "c": "154",
                "v": 1000,
            }
        ]
        result = bars_to_domain(rows)
        
        assert len(result) == 1
        assert result[0].timestamp == datetime(2021, 1, 1, 10, 0, 0, tzinfo=UTC)

    def test_bars_to_domain_skips_rows_on_conversion_error(self) -> None:
        """Test that rows with conversion errors are skipped."""
        rows = [
            {
                "t": "2024-01-01T10:00:00Z",
                "S": "AAPL",
                "o": "not a number",  # Will cause Decimal conversion error
                "h": "155",
                "l": "149",
                "c": "154",
                "v": 1000,
            },
            {
                "t": "2024-01-01T11:00:00Z",
                "S": "MSFT",
                "o": "250",
                "h": "255",
                "l": "249",
                "c": "254",
                "v": 2000,
            },
        ]
        result = bars_to_domain(rows)
        
        # First row should be skipped due to conversion error
        assert len(result) == 1
        assert result[0].symbol == "MSFT"

    def test_bars_to_domain_handles_numeric_prices(self) -> None:
        """Test that numeric (float/int) prices are converted to Decimal."""
        rows = [
            {
                "t": "2024-01-01T10:00:00Z",
                "S": "AAPL",
                "o": 150.25,  # float
                "h": 155,      # int
                "l": 149.75,   # float
                "c": 154.50,   # float
                "v": 1000,
            }
        ]
        result = bars_to_domain(rows)
        
        assert len(result) == 1
        bar = result[0]
        assert isinstance(bar.open, Decimal)
        assert isinstance(bar.high, Decimal)
        assert isinstance(bar.low, Decimal)
        assert isinstance(bar.close, Decimal)


class TestQuoteToDomainFunction:
    """Test suite for quote_to_domain conversion function."""

    def test_quote_to_domain_with_valid_data(self) -> None:
        """Test successful conversion of valid quote data."""
        class MockQuote:
            timestamp = datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC)
            symbol = "AAPL"
            bid_price = 150.25
            ask_price = 150.30
            bid_size = 100
            ask_size = 200

        result = quote_to_domain(MockQuote())
        
        assert result is not None
        assert result.symbol == "AAPL"
        assert result.timestamp == datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC)
        assert result.bid_price == Decimal("150.25")
        assert result.ask_price == Decimal("150.30")
        assert result.bid_size == Decimal("100")
        assert result.ask_size == Decimal("200")

    def test_quote_to_domain_with_none_returns_none(self) -> None:
        """Test that None input returns None."""
        result = quote_to_domain(None)
        assert result is None

    def test_quote_to_domain_missing_timestamp_uses_current_time(self) -> None:
        """Test that missing timestamp falls back to current time."""
        class MockQuote:
            symbol = "AAPL"
            bid_price = 150.25
            ask_price = 150.30
            bid_size = 100
            ask_size = 200
            # No timestamp attribute

        result = quote_to_domain(MockQuote())
        
        assert result is not None
        # Should have a timestamp (current time)
        assert result.timestamp is not None
        assert result.timestamp.tzinfo == UTC

    def test_quote_to_domain_invalid_timestamp_uses_fallback(self) -> None:
        """Test that invalid timestamp falls back to current time."""
        class MockQuote:
            timestamp = "invalid date"
            symbol = "AAPL"
            bid_price = 150.25
            ask_price = 150.30
            bid_size = 100
            ask_size = 200

        result = quote_to_domain(MockQuote())
        
        assert result is not None
        # Should have a timestamp (fallback to current time)
        assert result.timestamp is not None

    def test_quote_to_domain_ensures_timezone_aware(self) -> None:
        """Test that naive timestamps are made timezone-aware."""
        class MockQuote:
            timestamp = datetime(2024, 1, 1, 10, 0, 0)  # naive
            symbol = "AAPL"
            bid_price = 150.25
            ask_price = 150.30
            bid_size = 100
            ask_size = 200

        result = quote_to_domain(MockQuote())
        
        assert result is not None
        assert result.timestamp.tzinfo == UTC

    def test_quote_to_domain_missing_bid_price_returns_none(self) -> None:
        """Test that missing bid price returns None."""
        class MockQuote:
            timestamp = datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC)
            symbol = "AAPL"
            # No bid_price
            ask_price = 150.30
            bid_size = 100
            ask_size = 200

        result = quote_to_domain(MockQuote())
        assert result is None

    def test_quote_to_domain_missing_ask_price_returns_none(self) -> None:
        """Test that missing ask price returns None."""
        class MockQuote:
            timestamp = datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC)
            symbol = "AAPL"
            bid_price = 150.25
            # No ask_price
            bid_size = 100
            ask_size = 200

        result = quote_to_domain(MockQuote())
        assert result is None

    def test_quote_to_domain_defaults_to_zero_sizes(self) -> None:
        """Test that missing sizes default to 0."""
        class MockQuote:
            timestamp = datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC)
            symbol = "AAPL"
            bid_price = 150.25
            ask_price = 150.30
            # No bid_size or ask_size

        result = quote_to_domain(MockQuote())
        
        assert result is not None
        assert result.bid_size == Decimal("0")
        assert result.ask_size == Decimal("0")

    def test_quote_to_domain_defaults_to_unknown_symbol(self) -> None:
        """Test that missing symbol defaults to UNKNOWN."""
        class MockQuote:
            timestamp = datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC)
            bid_price = 150.25
            ask_price = 150.30
            bid_size = 100
            ask_size = 200
            # No symbol

        result = quote_to_domain(MockQuote())
        
        assert result is not None
        assert result.symbol == "UNKNOWN"

    def test_quote_to_domain_preserves_decimal_precision(self) -> None:
        """Test that Decimal precision is maintained."""
        class MockQuote:
            timestamp = datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC)
            symbol = "AAPL"
            bid_price = "150.123456789"
            ask_price = "150.987654321"
            bid_size = 100
            ask_size = 200

        result = quote_to_domain(MockQuote())
        
        assert result is not None
        assert result.bid_price == Decimal("150.123456789")
        assert result.ask_price == Decimal("150.987654321")

    def test_quote_to_domain_handles_string_timestamp(self) -> None:
        """Test parsing string timestamp."""
        class MockQuote:
            timestamp = "2024-01-01T10:00:00Z"
            symbol = "AAPL"
            bid_price = 150.25
            ask_price = 150.30
            bid_size = 100
            ask_size = 200

        result = quote_to_domain(MockQuote())
        
        assert result is not None
        assert result.timestamp == datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC)

    def test_quote_to_domain_handles_unix_timestamp(self) -> None:
        """Test parsing Unix timestamp."""
        class MockQuote:
            timestamp = 1609502400  # 2021-01-01 10:00:00 UTC
            symbol = "AAPL"
            bid_price = 150.25
            ask_price = 150.30
            bid_size = 100
            ask_size = 200

        result = quote_to_domain(MockQuote())
        
        assert result is not None
        assert result.timestamp == datetime(2021, 1, 1, 10, 0, 0, tzinfo=UTC)

    def test_quote_to_domain_returns_none_on_conversion_error(self) -> None:
        """Test that conversion errors return None instead of raising."""
        class MockQuote:
            timestamp = datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC)
            symbol = "AAPL"
            bid_price = "not a number"
            ask_price = 150.30
            bid_size = 100
            ask_size = 200

        result = quote_to_domain(MockQuote())
        # Should return None due to conversion error
        assert result is None

    def test_quote_to_domain_handles_numeric_prices(self) -> None:
        """Test that numeric prices are converted to Decimal."""
        class MockQuote:
            timestamp = datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC)
            symbol = "AAPL"
            bid_price = 150.25  # float
            ask_price = 151     # int
            bid_size = 100
            ask_size = 200

        result = quote_to_domain(MockQuote())
        
        assert result is not None
        assert isinstance(result.bid_price, Decimal)
        assert isinstance(result.ask_price, Decimal)
        assert isinstance(result.bid_size, Decimal)
        assert isinstance(result.ask_size, Decimal)


class TestIntegration:
    """Integration tests for the mappers module."""

    def test_bars_to_domain_produces_valid_bar_models(self) -> None:
        """Test that bars_to_domain produces valid BarModel instances."""
        rows = [
            {
                "t": "2024-01-01T10:00:00Z",
                "S": "AAPL",
                "o": "150.00",
                "h": "155.00",
                "l": "149.00",
                "c": "154.00",
                "v": 1000000,
            }
        ]
        result = bars_to_domain(rows)
        
        # Verify it's a BarModel instance
        assert len(result) == 1
        assert isinstance(result[0], BarModel)
        
        # Verify BarModel is frozen (immutable)
        with pytest.raises(AttributeError):
            result[0].open = Decimal("999")  # type: ignore

    def test_quote_to_domain_produces_valid_quote_model(self) -> None:
        """Test that quote_to_domain produces valid QuoteModel instances."""
        class MockQuote:
            timestamp = datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC)
            symbol = "AAPL"
            bid_price = 150.25
            ask_price = 150.30
            bid_size = 100
            ask_size = 200

        result = quote_to_domain(MockQuote())
        
        # Verify it's a QuoteModel instance
        assert result is not None
        assert isinstance(result, QuoteModel)
        
        # Verify QuoteModel is frozen (immutable)
        with pytest.raises(AttributeError):
            result.bid_price = Decimal("999")  # type: ignore

    def test_end_to_end_bars_conversion_with_real_world_data(self) -> None:
        """Test realistic end-to-end conversion of bars data."""
        # Simulating data from Alpaca API
        alpaca_bars = [
            {
                "t": "2024-01-01T09:30:00Z",
                "S": "AAPL",
                "o": "185.25",
                "h": "186.50",
                "l": "184.75",
                "c": "186.00",
                "v": 5234567,
            },
            {
                "t": "2024-01-01T09:31:00Z",
                "S": "AAPL",
                "o": "186.00",
                "h": "187.25",
                "l": "185.50",
                "c": "186.75",
                "v": 4123456,
            },
        ]
        
        bars = bars_to_domain(alpaca_bars)
        
        assert len(bars) == 2
        # All bars should have correct symbol
        assert all(bar.symbol == "AAPL" for bar in bars)
        # All prices should be Decimal
        assert all(isinstance(bar.open, Decimal) for bar in bars)
        # Timestamps should be ordered
        assert bars[0].timestamp < bars[1].timestamp
        # Volume should be positive
        assert all(bar.volume > 0 for bar in bars)

    def test_end_to_end_quote_conversion_with_real_world_data(self) -> None:
        """Test realistic end-to-end conversion of quote data."""
        # Simulating quote data from Alpaca API
        class AlpacaQuote:
            timestamp = datetime(2024, 1, 1, 9, 30, 0, tzinfo=UTC)
            symbol = "AAPL"
            bid_price = 185.24
            ask_price = 185.26
            bid_size = 500
            ask_size = 300

        quote = quote_to_domain(AlpacaQuote())
        
        assert quote is not None
        assert quote.symbol == "AAPL"
        assert isinstance(quote.bid_price, Decimal)
        assert isinstance(quote.ask_price, Decimal)
        assert quote.bid_price < quote.ask_price  # bid should be lower than ask
        assert quote.timestamp.tzinfo == UTC
