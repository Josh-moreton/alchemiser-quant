#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Tests for shared.types.market_data module.

Validates correctness of domain models, conversions, and financial data handling.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pandas as pd
import pytest

from the_alchemiser.shared.types.market_data import (
    BarModel,
    PriceDataModel,
    QuoteModel,
    bars_to_dataframe,
    dataframe_to_bars,
)
from the_alchemiser.shared.value_objects.core_types import (
    MarketDataPoint,
    PriceData,
    QuoteData,
)


class TestBarModel:
    """Tests for BarModel dataclass."""

    def test_bar_model_is_frozen(self) -> None:
        """Test that BarModel is immutable."""
        bar = BarModel(
            symbol="AAPL",
            timestamp=datetime(2024, 1, 1, tzinfo=UTC),
            open=Decimal("150.0"),
            high=Decimal("155.0"),
            low=Decimal("149.0"),
            close=Decimal("154.0"),
            volume=1000000,
        )
        with pytest.raises(AttributeError):
            bar.open = Decimal("160.0")  # type: ignore

    def test_from_dict_creates_bar_model(self) -> None:
        """Test from_dict creates valid BarModel from TypedDict."""
        data: MarketDataPoint = {
            "symbol": "AAPL",
            "timestamp": "2024-01-01T10:00:00+00:00",
            "open": Decimal("150.00"),
            "high": Decimal("155.00"),
            "low": Decimal("149.00"),
            "close": Decimal("154.00"),
            "volume": 1000000,
        }
        bar = BarModel.from_dict(data)
        assert bar.symbol == "AAPL"
        assert bar.timestamp == datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC)
        assert bar.open == Decimal("150.00")
        assert bar.volume == 1000000

    def test_from_dict_handles_z_suffix(self) -> None:
        """Test from_dict handles ISO timestamps with Z suffix."""
        data: MarketDataPoint = {
            "symbol": "AAPL",
            "timestamp": "2024-01-01T10:00:00Z",
            "open": Decimal("150.00"),
            "high": Decimal("155.00"),
            "low": Decimal("149.00"),
            "close": Decimal("154.00"),
            "volume": 1000000,
        }
        bar = BarModel.from_dict(data)
        assert bar.timestamp.tzinfo == UTC

    def test_to_dict_converts_back_to_typed_dict(self) -> None:
        """Test to_dict produces valid MarketDataPoint TypedDict."""
        bar = BarModel(
            symbol="AAPL",
            timestamp=datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC),
            open=Decimal("150.0"),
            high=Decimal("155.0"),
            low=Decimal("149.0"),
            close=Decimal("154.0"),
            volume=1000000,
        )
        result = bar.to_dict()
        assert result["symbol"] == "AAPL"
        assert isinstance(result["open"], Decimal)
        assert result["timestamp"] == "2024-01-01T10:00:00+00:00"

    def test_is_valid_ohlc_returns_true_for_valid_bar(self) -> None:
        """Test is_valid_ohlc returns True for valid OHLC relationships."""
        bar = BarModel(
            symbol="AAPL",
            timestamp=datetime(2024, 1, 1, tzinfo=UTC),
            open=Decimal("150.0"),
            high=Decimal("155.0"),
            low=Decimal("149.0"),
            close=Decimal("154.0"),
            volume=1000000,
        )
        assert bar.is_valid_ohlc is True

    def test_is_valid_ohlc_returns_false_when_high_too_low(self) -> None:
        """Test is_valid_ohlc returns False when high < max(open, close)."""
        bar = BarModel(
            symbol="AAPL",
            timestamp=datetime(2024, 1, 1, tzinfo=UTC),
            open=Decimal("150.0"),
            high=Decimal("145.0"),  # Invalid: high < open
            low=Decimal("144.0"),
            close=Decimal("148.0"),
            volume=1000000,
        )
        assert bar.is_valid_ohlc is False

    def test_is_valid_ohlc_returns_false_when_low_too_high(self) -> None:
        """Test is_valid_ohlc returns False when low > min(open, close)."""
        bar = BarModel(
            symbol="AAPL",
            timestamp=datetime(2024, 1, 1, tzinfo=UTC),
            open=Decimal("150.0"),
            high=Decimal("155.0"),
            low=Decimal("151.0"),  # Invalid: low > open
            close=Decimal("154.0"),
            volume=1000000,
        )
        assert bar.is_valid_ohlc is False

    def test_is_valid_ohlc_returns_false_for_negative_prices(self) -> None:
        """Test is_valid_ohlc returns False for negative prices."""
        bar = BarModel(
            symbol="AAPL",
            timestamp=datetime(2024, 1, 1, tzinfo=UTC),
            open=Decimal("-150.0"),
            high=Decimal("155.0"),
            low=Decimal("149.0"),
            close=Decimal("154.0"),
            volume=1000000,
        )
        assert bar.is_valid_ohlc is False


class TestQuoteModel:
    """Tests for QuoteModel dataclass."""

    def test_quote_model_is_frozen(self) -> None:
        """Test that QuoteModel is immutable."""
        quote = QuoteModel(
            symbol="AAPL",
            bid_price=Decimal("149.0"),
            ask_price=Decimal("150.0"),
            bid_size=Decimal("100.0"),
            ask_size=Decimal("100.0"),
            timestamp=datetime(2024, 1, 1, tzinfo=UTC),
        )
        with pytest.raises(AttributeError):
            quote.bid_price = Decimal("150.0")  # type: ignore

    def test_from_dict_creates_quote_model(self) -> None:
        """Test from_dict creates valid QuoteModel from TypedDict."""
        data: QuoteData = {
            "bid_price": Decimal("149.00"),
            "ask_price": Decimal("150.00"),
            "bid_size": Decimal("100"),
            "ask_size": Decimal("100"),
            "timestamp": "2024-01-01T10:00:00+00:00",
        }
        quote = QuoteModel.from_dict(data, "AAPL")
        assert quote.symbol == "AAPL"
        assert quote.bid_price == Decimal("149.00")
        assert quote.ask_price == Decimal("150.00")

    def test_spread_property(self) -> None:
        """Test spread calculation."""
        quote = QuoteModel(
            symbol="AAPL",
            bid_price=Decimal("149.0"),
            ask_price=Decimal("150.0"),
            bid_size=Decimal("100.0"),
            ask_size=Decimal("100.0"),
            timestamp=datetime(2024, 1, 1, tzinfo=UTC),
        )
        assert quote.spread == Decimal("1.0")

    def test_mid_price_property(self) -> None:
        """Test mid-price calculation."""
        quote = QuoteModel(
            symbol="AAPL",
            bid_price=Decimal("149.0"),
            ask_price=Decimal("150.0"),
            bid_size=Decimal("100.0"),
            ask_size=Decimal("100.0"),
            timestamp=datetime(2024, 1, 1, tzinfo=UTC),
        )
        assert quote.mid_price == Decimal("149.5")


class TestPriceDataModel:
    """Tests for PriceDataModel dataclass."""

    def test_price_data_model_is_frozen(self) -> None:
        """Test that PriceDataModel is immutable."""
        price_data = PriceDataModel(
            symbol="AAPL",
            price=Decimal("150.0"),
            timestamp=datetime(2024, 1, 1, tzinfo=UTC),
        )
        with pytest.raises(AttributeError):
            price_data.price = Decimal("160.0")  # type: ignore

    def test_from_dict_creates_price_data_model(self) -> None:
        """Test from_dict creates valid PriceDataModel from TypedDict."""
        data: PriceData = {
            "symbol": "AAPL",
            "price": Decimal("150.00"),
            "timestamp": "2024-01-01T10:00:00+00:00",
            "bid": Decimal("149.00"),
            "ask": Decimal("150.00"),
            "volume": 1000000,
        }
        price_data = PriceDataModel.from_dict(data)
        assert price_data.symbol == "AAPL"
        assert price_data.price == Decimal("150.00")
        assert price_data.bid == Decimal("149.00")
        assert price_data.ask == Decimal("150.00")
        assert price_data.volume == 1000000

    def test_from_dict_handles_none_values(self) -> None:
        """Test from_dict handles None for optional fields."""
        data: PriceData = {
            "symbol": "AAPL",
            "price": Decimal("150.00"),
            "timestamp": "2024-01-01T10:00:00+00:00",
            "bid": None,
            "ask": None,
            "volume": None,
        }
        price_data = PriceDataModel.from_dict(data)
        assert price_data.bid is None
        assert price_data.ask is None
        assert price_data.volume is None

    def test_has_quote_data_returns_true(self) -> None:
        """Test has_quote_data returns True when bid and ask present."""
        price_data = PriceDataModel(
            symbol="AAPL",
            price=Decimal("150.0"),
            timestamp=datetime(2024, 1, 1, tzinfo=UTC),
            bid=Decimal("149.0"),
            ask=Decimal("150.0"),
        )
        assert price_data.has_quote_data is True

    def test_has_quote_data_returns_false_when_missing(self) -> None:
        """Test has_quote_data returns False when bid or ask missing."""
        price_data = PriceDataModel(
            symbol="AAPL",
            price=Decimal("150.0"),
            timestamp=datetime(2024, 1, 1, tzinfo=UTC),
            bid=None,
            ask=None,
        )
        assert price_data.has_quote_data is False


class TestDataFrameConversions:
    """Tests for DataFrame conversion utilities."""

    def test_bars_to_dataframe_creates_valid_dataframe(self) -> None:
        """Test bars_to_dataframe creates valid DataFrame."""
        bars = [
            BarModel(
                symbol="AAPL",
                timestamp=datetime(2024, 1, 1, tzinfo=UTC),
                open=Decimal("150.0"),
                high=Decimal("155.0"),
                low=Decimal("149.0"),
                close=Decimal("154.0"),
                volume=1000000,
            ),
            BarModel(
                symbol="AAPL",
                timestamp=datetime(2024, 1, 2, tzinfo=UTC),
                open=Decimal("154.0"),
                high=Decimal("156.0"),
                low=Decimal("153.0"),
                close=Decimal("155.0"),
                volume=900000,
            ),
        ]
        df = bars_to_dataframe(bars)
        assert len(df) == 2
        assert list(df.columns) == ["Open", "High", "Low", "Close", "Volume"]
        assert df.index.name == "Date"

    def test_bars_to_dataframe_handles_empty_list(self) -> None:
        """Test bars_to_dataframe handles empty list."""
        df = bars_to_dataframe([])
        assert len(df) == 0

    def test_dataframe_to_bars_creates_valid_bars(self) -> None:
        """Test dataframe_to_bars creates valid bars."""
        data = {
            "Open": [Decimal("150.0"), Decimal("154.0")],
            "High": [Decimal("155.0"), Decimal("156.0")],
            "Low": [Decimal("149.0"), Decimal("153.0")],
            "Close": [Decimal("154.0"), Decimal("155.0")],
            "Volume": [1000000, 900000],
        }
        df = pd.DataFrame(
            data,
            index=[
                datetime(2024, 1, 1, tzinfo=UTC),
                datetime(2024, 1, 2, tzinfo=UTC),
            ],
        )
        bars = dataframe_to_bars(df, "AAPL")
        assert len(bars) == 2
        assert bars[0].symbol == "AAPL"
        assert bars[0].open == Decimal("150.0")
        assert bars[1].close == Decimal("155.0")

    def test_dataframe_to_bars_handles_missing_volume(self) -> None:
        """Test dataframe_to_bars handles missing Volume column."""
        data = {
            "Open": [Decimal("150.0")],
            "High": [Decimal("155.0")],
            "Low": [Decimal("149.0")],
            "Close": [Decimal("154.0")],
        }
        df = pd.DataFrame(data, index=[datetime(2024, 1, 1, tzinfo=UTC)])
        bars = dataframe_to_bars(df, "AAPL")
        assert len(bars) == 1
        assert bars[0].volume == 0

    def test_round_trip_conversion(self) -> None:
        """Test bars → DataFrame → bars round-trip conversion."""
        original_bars = [
            BarModel(
                symbol="AAPL",
                timestamp=datetime(2024, 1, 1, tzinfo=UTC),
                open=Decimal("150.0"),
                high=Decimal("155.0"),
                low=Decimal("149.0"),
                close=Decimal("154.0"),
                volume=1000000,
            ),
        ]
        df = bars_to_dataframe(original_bars)
        converted_bars = dataframe_to_bars(df, "AAPL")
        
        assert len(converted_bars) == len(original_bars)
        assert converted_bars[0].open == original_bars[0].open
        assert converted_bars[0].close == original_bars[0].close
        assert converted_bars[0].volume == original_bars[0].volume


class TestPrecisionCorrectness:
    """Tests demonstrating precision correctness with Decimal usage.
    
    These tests verify that Decimal types maintain precision in financial
    calculations, as required by Alchemiser guardrails.
    """

    def test_decimal_preserves_precision(self) -> None:
        """Verify Decimal preserves high precision values."""
        data: MarketDataPoint = {
            "symbol": "AAPL",
            "timestamp": "2024-01-01T10:00:00+00:00",
            "open": Decimal("150.123456789"),  # High precision
            "high": Decimal("155.987654321"),
            "low": Decimal("149.111111111"),
            "close": Decimal("154.999999999"),
            "volume": 1000000,
        }
        bar = BarModel.from_dict(data)
        result = bar.to_dict()
        
        # Precision is preserved with Decimal
        assert result["open"] == Decimal("150.123456789")
        assert result["high"] == Decimal("155.987654321")
        assert result["low"] == Decimal("149.111111111")
        assert result["close"] == Decimal("154.999999999")

    def test_decimal_arithmetic_precision(self) -> None:
        """Verify Decimal arithmetic maintains precision."""
        quote = QuoteModel(
            symbol="AAPL",
            bid_price=Decimal("0.1") + Decimal("0.2"),
            ask_price=Decimal("0.3"),
            bid_size=Decimal("100.0"),
            ask_size=Decimal("100.0"),
            timestamp=datetime(2024, 1, 1, tzinfo=UTC),
        )
        # With Decimal, 0.1 + 0.2 = 0.3 exactly
        assert quote.bid_price == Decimal("0.3")
        assert quote.spread == Decimal("0.0")

    def test_mid_price_calculation_exact(self) -> None:
        """Verify mid-price calculation is exact with Decimal."""
        quote = QuoteModel(
            symbol="AAPL",
            bid_price=Decimal("100.111111"),
            ask_price=Decimal("100.222222"),
            bid_size=Decimal("100.0"),
            ask_size=Decimal("100.0"),
            timestamp=datetime(2024, 1, 1, tzinfo=UTC),
        )
        # Mid-price should be exact
        expected = (Decimal("100.111111") + Decimal("100.222222")) / Decimal("2")
        assert quote.mid_price == expected
