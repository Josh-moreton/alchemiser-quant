#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Comprehensive tests for MarketBar DTO.

Tests cover:
- Field validation and normalization
- OHLC cross-validation
- Conversion methods (from_dict, from_alpaca_bar, to_dict, to_legacy_dict)
- Error cases and boundary conditions
- Property-based tests for OHLC invariants
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis.strategies import decimals
from pydantic import ValidationError

from the_alchemiser.shared.schemas.market_bar import MarketBar


class TestMarketBarBasicValidation:
    """Tests for basic field validation."""

    def test_create_valid_market_bar(self) -> None:
        """Test creating a valid MarketBar instance."""
        bar = MarketBar(
            timestamp=datetime(2024, 1, 1, 9, 30, tzinfo=UTC),
            symbol="AAPL",
            timeframe="1D",
            open_price=Decimal("150.00"),
            high_price=Decimal("155.00"),
            low_price=Decimal("149.00"),
            close_price=Decimal("154.00"),
            volume=1000000,
        )

        assert bar.symbol == "AAPL"
        assert bar.timeframe == "1D"
        assert bar.open_price == Decimal("150.00")
        assert bar.high_price == Decimal("155.00")
        assert bar.low_price == Decimal("149.00")
        assert bar.close_price == Decimal("154.00")
        assert bar.volume == 1000000
        assert bar.schema_version == "1.0"

    def test_schema_version_default(self) -> None:
        """Test that schema_version has correct default."""
        bar = MarketBar(
            timestamp=datetime(2024, 1, 1, 9, 30, tzinfo=UTC),
            symbol="AAPL",
            timeframe="1D",
            open_price=Decimal("150.00"),
            high_price=Decimal("155.00"),
            low_price=Decimal("149.00"),
            close_price=Decimal("154.00"),
            volume=1000000,
        )
        assert bar.schema_version == "1.0"

    def test_immutability(self) -> None:
        """Test that MarketBar instances are immutable."""
        bar = MarketBar(
            timestamp=datetime(2024, 1, 1, 9, 30, tzinfo=UTC),
            symbol="AAPL",
            timeframe="1D",
            open_price=Decimal("150.00"),
            high_price=Decimal("155.00"),
            low_price=Decimal("149.00"),
            close_price=Decimal("154.00"),
            volume=1000000,
        )

        with pytest.raises(ValidationError):
            bar.symbol = "MSFT"  # type: ignore

    def test_negative_price_rejected(self) -> None:
        """Test that negative prices are rejected."""
        with pytest.raises(ValidationError):
            MarketBar(
                timestamp=datetime(2024, 1, 1, 9, 30, tzinfo=UTC),
                symbol="AAPL",
                timeframe="1D",
                open_price=Decimal("-10.00"),
                high_price=Decimal("155.00"),
                low_price=Decimal("149.00"),
                close_price=Decimal("154.00"),
                volume=1000000,
            )

    def test_zero_price_rejected(self) -> None:
        """Test that zero prices are rejected."""
        with pytest.raises(ValidationError):
            MarketBar(
                timestamp=datetime(2024, 1, 1, 9, 30, tzinfo=UTC),
                symbol="AAPL",
                timeframe="1D",
                open_price=Decimal("0.00"),
                high_price=Decimal("155.00"),
                low_price=Decimal("149.00"),
                close_price=Decimal("154.00"),
                volume=1000000,
            )

    def test_negative_volume_rejected(self) -> None:
        """Test that negative volume is rejected."""
        with pytest.raises(ValidationError):
            MarketBar(
                timestamp=datetime(2024, 1, 1, 9, 30, tzinfo=UTC),
                symbol="AAPL",
                timeframe="1D",
                open_price=Decimal("150.00"),
                high_price=Decimal("155.00"),
                low_price=Decimal("149.00"),
                close_price=Decimal("154.00"),
                volume=-1000,
            )

    def test_empty_symbol_rejected(self) -> None:
        """Test that empty symbol is rejected."""
        with pytest.raises(ValidationError):
            MarketBar(
                timestamp=datetime(2024, 1, 1, 9, 30, tzinfo=UTC),
                symbol="",
                timeframe="1D",
                open_price=Decimal("150.00"),
                high_price=Decimal("155.00"),
                low_price=Decimal("149.00"),
                close_price=Decimal("154.00"),
                volume=1000000,
            )


class TestMarketBarNormalization:
    """Tests for field normalization."""

    def test_symbol_normalized_to_uppercase(self) -> None:
        """Test that symbol is normalized to uppercase."""
        bar = MarketBar(
            timestamp=datetime(2024, 1, 1, 9, 30, tzinfo=UTC),
            symbol="aapl",
            timeframe="1D",
            open_price=Decimal("150.00"),
            high_price=Decimal("155.00"),
            low_price=Decimal("149.00"),
            close_price=Decimal("154.00"),
            volume=1000000,
        )
        assert bar.symbol == "AAPL"

    def test_symbol_whitespace_stripped(self) -> None:
        """Test that symbol whitespace is stripped."""
        bar = MarketBar(
            timestamp=datetime(2024, 1, 1, 9, 30, tzinfo=UTC),
            symbol="  AAPL  ",
            timeframe="1D",
            open_price=Decimal("150.00"),
            high_price=Decimal("155.00"),
            low_price=Decimal("149.00"),
            close_price=Decimal("154.00"),
            volume=1000000,
        )
        assert bar.symbol == "AAPL"

    def test_timeframe_normalized_to_uppercase(self) -> None:
        """Test that timeframe is normalized to uppercase."""
        bar = MarketBar(
            timestamp=datetime(2024, 1, 1, 9, 30, tzinfo=UTC),
            symbol="AAPL",
            timeframe="1d",
            open_price=Decimal("150.00"),
            high_price=Decimal("155.00"),
            low_price=Decimal("149.00"),
            close_price=Decimal("154.00"),
            volume=1000000,
        )
        assert bar.timeframe == "1D"

    def test_timeframe_whitespace_stripped(self) -> None:
        """Test that timeframe whitespace is stripped."""
        bar = MarketBar(
            timestamp=datetime(2024, 1, 1, 9, 30, tzinfo=UTC),
            symbol="AAPL",
            timeframe="  1D  ",
            open_price=Decimal("150.00"),
            high_price=Decimal("155.00"),
            low_price=Decimal("149.00"),
            close_price=Decimal("154.00"),
            volume=1000000,
        )
        assert bar.timeframe == "1D"

    def test_timezone_aware_timestamp_preserved(self) -> None:
        """Test that timezone-aware timestamps are preserved."""
        ts = datetime(2024, 1, 1, 9, 30, tzinfo=UTC)
        bar = MarketBar(
            timestamp=ts,
            symbol="AAPL",
            timeframe="1D",
            open_price=Decimal("150.00"),
            high_price=Decimal("155.00"),
            low_price=Decimal("149.00"),
            close_price=Decimal("154.00"),
            volume=1000000,
        )
        assert bar.timestamp.tzinfo is not None

    def test_naive_timestamp_gets_utc(self) -> None:
        """Test that naive timestamps get UTC timezone."""
        bar = MarketBar(
            timestamp=datetime(2024, 1, 1, 9, 30),
            symbol="AAPL",
            timeframe="1D",
            open_price=Decimal("150.00"),
            high_price=Decimal("155.00"),
            low_price=Decimal("149.00"),
            close_price=Decimal("154.00"),
            volume=1000000,
        )
        assert bar.timestamp.tzinfo is not None


class TestMarketBarOHLCValidation:
    """Tests for OHLC cross-validation."""

    def test_high_must_be_greater_than_or_equal_to_low(self) -> None:
        """Test that high price must be >= low price."""
        with pytest.raises(ValueError, match="High price must be >= low price"):
            MarketBar(
                timestamp=datetime(2024, 1, 1, 9, 30, tzinfo=UTC),
                symbol="AAPL",
                timeframe="1D",
                open_price=Decimal("150.00"),
                high_price=Decimal("145.00"),  # Lower than low_price
                low_price=Decimal("149.00"),
                close_price=Decimal("150.00"),
                volume=1000000,
            )

    def test_low_must_be_less_than_or_equal_to_high(self) -> None:
        """Test that low price must be <= high price."""
        with pytest.raises(ValueError, match="High price must be >= low price"):
            MarketBar(
                timestamp=datetime(2024, 1, 1, 9, 30, tzinfo=UTC),
                symbol="AAPL",
                timeframe="1D",
                open_price=Decimal("150.00"),
                high_price=Decimal("155.00"),
                low_price=Decimal("160.00"),  # Higher than high_price
                close_price=Decimal("154.00"),
                volume=1000000,
            )

    def test_open_must_be_within_low_high_range(self) -> None:
        """Test that open price must be within [low, high] range."""
        with pytest.raises(ValueError, match="Open price must be within"):
            MarketBar(
                timestamp=datetime(2024, 1, 1, 9, 30, tzinfo=UTC),
                symbol="AAPL",
                timeframe="1D",
                open_price=Decimal("160.00"),  # Above high_price
                high_price=Decimal("155.00"),
                low_price=Decimal("149.00"),
                close_price=Decimal("154.00"),
                volume=1000000,
            )

    def test_open_below_low_rejected(self) -> None:
        """Test that open price below low is rejected."""
        with pytest.raises(ValueError, match="Open price must be within"):
            MarketBar(
                timestamp=datetime(2024, 1, 1, 9, 30, tzinfo=UTC),
                symbol="AAPL",
                timeframe="1D",
                open_price=Decimal("140.00"),  # Below low_price
                high_price=Decimal("155.00"),
                low_price=Decimal("149.00"),
                close_price=Decimal("154.00"),
                volume=1000000,
            )

    def test_close_must_be_within_low_high_range(self) -> None:
        """Test that close price must be within [low, high] range."""
        with pytest.raises(ValueError, match="Close price must be within"):
            MarketBar(
                timestamp=datetime(2024, 1, 1, 9, 30, tzinfo=UTC),
                symbol="AAPL",
                timeframe="1D",
                open_price=Decimal("150.00"),
                high_price=Decimal("155.00"),
                low_price=Decimal("149.00"),
                close_price=Decimal("160.00"),  # Above high_price
                volume=1000000,
            )

    def test_close_below_low_rejected(self) -> None:
        """Test that close price below low is rejected."""
        with pytest.raises(ValueError, match="Close price must be within"):
            MarketBar(
                timestamp=datetime(2024, 1, 1, 9, 30, tzinfo=UTC),
                symbol="AAPL",
                timeframe="1D",
                open_price=Decimal("150.00"),
                high_price=Decimal("155.00"),
                low_price=Decimal("149.00"),
                close_price=Decimal("140.00"),  # Below low_price
                volume=1000000,
            )

    def test_valid_ohlc_equal_values(self) -> None:
        """Test that equal OHLC values are valid."""
        bar = MarketBar(
            timestamp=datetime(2024, 1, 1, 9, 30, tzinfo=UTC),
            symbol="AAPL",
            timeframe="1D",
            open_price=Decimal("150.00"),
            high_price=Decimal("150.00"),
            low_price=Decimal("150.00"),
            close_price=Decimal("150.00"),
            volume=1000000,
        )
        assert bar.open_price == bar.close_price == bar.high_price == bar.low_price

    def test_open_at_high_boundary(self) -> None:
        """Test that open price at high boundary is valid."""
        bar = MarketBar(
            timestamp=datetime(2024, 1, 1, 9, 30, tzinfo=UTC),
            symbol="AAPL",
            timeframe="1D",
            open_price=Decimal("155.00"),  # Equal to high
            high_price=Decimal("155.00"),
            low_price=Decimal("149.00"),
            close_price=Decimal("154.00"),
            volume=1000000,
        )
        assert bar.open_price == bar.high_price

    def test_close_at_low_boundary(self) -> None:
        """Test that close price at low boundary is valid."""
        bar = MarketBar(
            timestamp=datetime(2024, 1, 1, 9, 30, tzinfo=UTC),
            symbol="AAPL",
            timeframe="1D",
            open_price=Decimal("150.00"),
            high_price=Decimal("155.00"),
            low_price=Decimal("149.00"),
            close_price=Decimal("149.00"),  # Equal to low
            volume=1000000,
        )
        assert bar.close_price == bar.low_price


class TestMarketBarToDictConversion:
    """Tests for to_dict conversion."""

    def test_to_dict_converts_to_json_serializable(self) -> None:
        """Test that to_dict produces JSON-serializable dictionary."""
        bar = MarketBar(
            timestamp=datetime(2024, 1, 1, 9, 30, tzinfo=UTC),
            symbol="AAPL",
            timeframe="1D",
            open_price=Decimal("150.00"),
            high_price=Decimal("155.00"),
            low_price=Decimal("149.00"),
            close_price=Decimal("154.00"),
            volume=1000000,
        )

        data = bar.to_dict()

        assert isinstance(data["timestamp"], str)
        assert isinstance(data["open_price"], str)
        assert isinstance(data["high_price"], str)
        assert isinstance(data["low_price"], str)
        assert isinstance(data["close_price"], str)
        assert data["symbol"] == "AAPL"
        assert data["volume"] == 1000000

    def test_to_dict_with_optional_fields(self) -> None:
        """Test to_dict with optional fields present."""
        bar = MarketBar(
            timestamp=datetime(2024, 1, 1, 9, 30, tzinfo=UTC),
            symbol="AAPL",
            timeframe="1D",
            open_price=Decimal("150.00"),
            high_price=Decimal("155.00"),
            low_price=Decimal("149.00"),
            close_price=Decimal("154.00"),
            volume=1000000,
            vwap=Decimal("152.50"),
            trade_count=5000,
        )

        data = bar.to_dict()

        assert isinstance(data["vwap"], str)
        assert data["vwap"] == "152.50"
        assert data["trade_count"] == 5000


class TestMarketBarFromDictConversion:
    """Tests for from_dict conversion."""

    def test_from_dict_recreates_market_bar(self) -> None:
        """Test that from_dict recreates MarketBar from dictionary."""
        data = {
            "timestamp": "2024-01-01T09:30:00+00:00",
            "symbol": "AAPL",
            "timeframe": "1D",
            "open_price": "150.00",
            "high_price": "155.00",
            "low_price": "149.00",
            "close_price": "154.00",
            "volume": 1000000,
        }

        bar = MarketBar.from_dict(data)

        assert bar.symbol == "AAPL"
        assert bar.timeframe == "1D"
        assert bar.open_price == Decimal("150.00")
        assert bar.volume == 1000000

    def test_from_dict_handles_z_suffix_timestamp(self) -> None:
        """Test that from_dict handles Z suffix in timestamp."""
        data = {
            "timestamp": "2024-01-01T09:30:00Z",
            "symbol": "AAPL",
            "timeframe": "1D",
            "open_price": "150.00",
            "high_price": "155.00",
            "low_price": "149.00",
            "close_price": "154.00",
            "volume": 1000000,
        }

        bar = MarketBar.from_dict(data)

        assert bar.timestamp.tzinfo is not None

    def test_from_dict_with_optional_fields(self) -> None:
        """Test from_dict with optional fields."""
        data = {
            "timestamp": "2024-01-01T09:30:00+00:00",
            "symbol": "AAPL",
            "timeframe": "1D",
            "open_price": "150.00",
            "high_price": "155.00",
            "low_price": "149.00",
            "close_price": "154.00",
            "volume": 1000000,
            "vwap": "152.50",
            "trade_count": 5000,
        }

        bar = MarketBar.from_dict(data)

        assert bar.vwap == Decimal("152.50")
        assert bar.trade_count == 5000

    def test_from_dict_round_trip(self) -> None:
        """Test that to_dict -> from_dict is a round trip."""
        original = MarketBar(
            timestamp=datetime(2024, 1, 1, 9, 30, tzinfo=UTC),
            symbol="AAPL",
            timeframe="1D",
            open_price=Decimal("150.00"),
            high_price=Decimal("155.00"),
            low_price=Decimal("149.00"),
            close_price=Decimal("154.00"),
            volume=1000000,
        )

        data = original.to_dict()
        recreated = MarketBar.from_dict(data)

        assert recreated.symbol == original.symbol
        assert recreated.open_price == original.open_price
        assert recreated.close_price == original.close_price
        assert recreated.volume == original.volume

    def test_from_dict_invalid_timestamp_raises_error(self) -> None:
        """Test that invalid timestamp format raises ValueError."""
        data = {
            "timestamp": "invalid-timestamp",
            "symbol": "AAPL",
            "timeframe": "1D",
            "open_price": "150.00",
            "high_price": "155.00",
            "low_price": "149.00",
            "close_price": "154.00",
            "volume": 1000000,
        }

        with pytest.raises(ValueError, match="Invalid timestamp format"):
            MarketBar.from_dict(data)

    def test_from_dict_invalid_decimal_raises_error(self) -> None:
        """Test that invalid decimal value raises ValueError."""
        data = {
            "timestamp": "2024-01-01T09:30:00+00:00",
            "symbol": "AAPL",
            "timeframe": "1D",
            "open_price": "invalid",
            "high_price": "155.00",
            "low_price": "149.00",
            "close_price": "154.00",
            "volume": 1000000,
        }

        with pytest.raises(ValueError, match="Invalid open_price value"):
            MarketBar.from_dict(data)


class TestMarketBarFromAlpacaBar:
    """Tests for from_alpaca_bar conversion."""

    def test_from_alpaca_bar_creates_market_bar(self) -> None:
        """Test that from_alpaca_bar creates MarketBar from Alpaca dict."""
        alpaca_dict = {
            "t": "2024-01-01T09:30:00Z",
            "o": 150.00,
            "h": 155.00,
            "l": 149.00,
            "c": 154.00,
            "v": 1000000,
        }

        bar = MarketBar.from_alpaca_bar(alpaca_dict, "AAPL", "1D")

        assert bar.symbol == "AAPL"
        assert bar.timeframe == "1D"
        assert bar.open_price == Decimal("150.00")
        assert bar.volume == 1000000
        assert bar.data_source == "alpaca"

    def test_from_alpaca_bar_with_vwap_and_trade_count(self) -> None:
        """Test from_alpaca_bar with optional fields."""
        alpaca_dict = {
            "t": "2024-01-01T09:30:00Z",
            "o": 150.00,
            "h": 155.00,
            "l": 149.00,
            "c": 154.00,
            "v": 1000000,
            "vw": 152.50,
            "n": 5000,
        }

        bar = MarketBar.from_alpaca_bar(alpaca_dict, "AAPL", "1D")

        assert bar.vwap == Decimal("152.50")
        assert bar.trade_count == 5000

    def test_from_alpaca_bar_handles_timestamp_key(self) -> None:
        """Test from_alpaca_bar handles 'timestamp' key."""
        alpaca_dict = {
            "timestamp": "2024-01-01T09:30:00Z",
            "o": 150.00,
            "h": 155.00,
            "l": 149.00,
            "c": 154.00,
            "v": 1000000,
        }

        bar = MarketBar.from_alpaca_bar(alpaca_dict, "AAPL", "1D")

        assert bar.symbol == "AAPL"

    def test_from_alpaca_bar_handles_datetime_timestamp(self) -> None:
        """Test from_alpaca_bar handles datetime timestamp."""
        alpaca_dict = {
            "t": datetime(2024, 1, 1, 9, 30, tzinfo=UTC),
            "o": 150.00,
            "h": 155.00,
            "l": 149.00,
            "c": 154.00,
            "v": 1000000,
        }

        bar = MarketBar.from_alpaca_bar(alpaca_dict, "AAPL", "1D")

        assert bar.timestamp.year == 2024

    def test_from_alpaca_bar_missing_timestamp_raises_error(self) -> None:
        """Test that missing timestamp raises ValueError."""
        alpaca_dict = {
            "o": 150.00,
            "h": 155.00,
            "l": 149.00,
            "c": 154.00,
            "v": 1000000,
        }

        with pytest.raises(ValueError, match="Missing timestamp"):
            MarketBar.from_alpaca_bar(alpaca_dict, "AAPL", "1D")

    def test_from_alpaca_bar_missing_required_field_raises_error(self) -> None:
        """Test that missing required field raises ValueError."""
        alpaca_dict = {
            "t": "2024-01-01T09:30:00Z",
            "o": 150.00,
            # Missing 'h', 'l', 'c', 'v'
        }

        with pytest.raises(ValueError, match="Invalid Alpaca bar data"):
            MarketBar.from_alpaca_bar(alpaca_dict, "AAPL", "1D")


class TestMarketBarToLegacyDict:
    """Tests for to_legacy_dict conversion."""

    def test_to_legacy_dict_produces_expected_format(self) -> None:
        """Test that to_legacy_dict produces expected format."""
        bar = MarketBar(
            timestamp=datetime(2024, 1, 1, 9, 30, tzinfo=UTC),
            symbol="AAPL",
            timeframe="1D",
            open_price=Decimal("150.00"),
            high_price=Decimal("155.00"),
            low_price=Decimal("149.00"),
            close_price=Decimal("154.00"),
            volume=1000000,
        )

        legacy = bar.to_legacy_dict()

        assert isinstance(legacy["o"], float)
        assert isinstance(legacy["h"], float)
        assert isinstance(legacy["l"], float)
        assert isinstance(legacy["c"], float)
        assert legacy["o"] == 150.00
        assert legacy["v"] == 1000000

    def test_to_legacy_dict_with_optional_fields(self) -> None:
        """Test to_legacy_dict with optional fields."""
        bar = MarketBar(
            timestamp=datetime(2024, 1, 1, 9, 30, tzinfo=UTC),
            symbol="AAPL",
            timeframe="1D",
            open_price=Decimal("150.00"),
            high_price=Decimal("155.00"),
            low_price=Decimal("149.00"),
            close_price=Decimal("154.00"),
            volume=1000000,
            vwap=Decimal("152.50"),
            trade_count=5000,
        )

        legacy = bar.to_legacy_dict()

        assert isinstance(legacy["vw"], float)
        assert legacy["vw"] == 152.50
        assert legacy["n"] == 5000

    def test_to_legacy_dict_with_none_vwap(self) -> None:
        """Test to_legacy_dict with None vwap."""
        bar = MarketBar(
            timestamp=datetime(2024, 1, 1, 9, 30, tzinfo=UTC),
            symbol="AAPL",
            timeframe="1D",
            open_price=Decimal("150.00"),
            high_price=Decimal("155.00"),
            low_price=Decimal("149.00"),
            close_price=Decimal("154.00"),
            volume=1000000,
        )

        legacy = bar.to_legacy_dict()

        assert legacy["vw"] is None


class TestMarketBarPropertyBasedTests:
    """Property-based tests for OHLC invariants."""

    @given(
        low=decimals(min_value=1, max_value=1000, places=2),
        high=decimals(min_value=1, max_value=1000, places=2),
    )
    def test_ohlc_invariants_with_random_prices(self, low: Decimal, high: Decimal) -> None:
        """Test OHLC invariants with random valid prices."""
        # Ensure high >= low
        if low > high:
            low, high = high, low

        # Generate open and close within [low, high]
        open_price = low + (high - low) / Decimal("2")
        close_price = low + (high - low) / Decimal("4")

        bar = MarketBar(
            timestamp=datetime(2024, 1, 1, 9, 30, tzinfo=UTC),
            symbol="TEST",
            timeframe="1D",
            open_price=open_price,
            high_price=high,
            low_price=low,
            close_price=close_price,
            volume=1000000,
        )

        # Verify invariants
        assert bar.high_price >= bar.low_price
        assert bar.open_price >= bar.low_price
        assert bar.open_price <= bar.high_price
        assert bar.close_price >= bar.low_price
        assert bar.close_price <= bar.high_price

    @given(
        price=decimals(min_value=1, max_value=1000, places=2),
    )
    def test_equal_ohlc_values_always_valid(self, price: Decimal) -> None:
        """Test that equal OHLC values are always valid."""
        bar = MarketBar(
            timestamp=datetime(2024, 1, 1, 9, 30, tzinfo=UTC),
            symbol="TEST",
            timeframe="1D",
            open_price=price,
            high_price=price,
            low_price=price,
            close_price=price,
            volume=1000000,
        )

        assert bar.open_price == bar.high_price == bar.low_price == bar.close_price
