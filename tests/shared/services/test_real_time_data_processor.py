"""Unit tests for RealTimeDataProcessor.

Tests extraction, validation, and conversion of real-time market data with
emphasis on Decimal precision for financial data per Alchemiser guardrails.
"""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from the_alchemiser.shared.errors.exceptions import DataProviderError
from the_alchemiser.shared.services.real_time_data_processor import RealTimeDataProcessor
from the_alchemiser.shared.types.market_data import QuoteExtractionResult


class TestRealTimeDataProcessor:
    """Test suite for RealTimeDataProcessor."""

    @pytest.fixture
    def processor(self) -> RealTimeDataProcessor:
        """Create a processor instance for testing."""
        return RealTimeDataProcessor()

    @pytest.fixture
    def sample_timestamp(self) -> datetime:
        """Create a sample timestamp for testing."""
        return datetime(2025, 1, 6, 12, 0, 0, tzinfo=UTC)


class TestExtractSymbolFromQuote(TestRealTimeDataProcessor):
    """Tests for extract_symbol_from_quote method."""

    def test_extract_from_dict_with_s_key(self, processor: RealTimeDataProcessor) -> None:
        """Test symbol extraction from dict with 'S' key."""
        data = {"S": "AAPL", "bp": 150.25}
        result = processor.extract_symbol_from_quote(data)
        assert result == "AAPL"

    def test_extract_from_object_with_symbol_attr(self, processor: RealTimeDataProcessor) -> None:
        """Test symbol extraction from object with symbol attribute."""
        class MockQuote:
            symbol = "TSLA"
        
        data = MockQuote()
        result = processor.extract_symbol_from_quote(data)
        assert result == "TSLA"

    def test_raises_error_when_symbol_missing(self, processor: RealTimeDataProcessor) -> None:
        """Test that DataProviderError is raised when symbol is missing."""
        data = {"bp": 150.25}  # No symbol
        with pytest.raises(DataProviderError, match="Symbol missing or empty"):
            processor.extract_symbol_from_quote(data)

    def test_raises_error_when_symbol_empty(self, processor: RealTimeDataProcessor) -> None:
        """Test that DataProviderError is raised when symbol is empty."""
        data = {"S": "", "bp": 150.25}
        with pytest.raises(DataProviderError, match="Symbol missing or empty"):
            processor.extract_symbol_from_quote(data)

    def test_raises_error_when_symbol_whitespace(self, processor: RealTimeDataProcessor) -> None:
        """Test that DataProviderError is raised when symbol is whitespace."""
        data = {"S": "   ", "bp": 150.25}
        with pytest.raises(DataProviderError, match="Symbol missing or empty"):
            processor.extract_symbol_from_quote(data)


class TestExtractQuoteValues(TestRealTimeDataProcessor):
    """Tests for extract_quote_values method."""

    def test_extract_from_dict_format(
        self, processor: RealTimeDataProcessor, sample_timestamp: datetime
    ) -> None:
        """Test quote extraction from Alpaca dict format."""
        data = {
            "bp": 150.25,
            "ap": 150.27,
            "bs": 100,
            "as": 200,
            "t": sample_timestamp
        }
        result = processor.extract_quote_values(data)
        
        assert isinstance(result, QuoteExtractionResult)
        assert result.bid_price == Decimal("150.25")
        assert result.ask_price == Decimal("150.27")
        assert result.bid_size == Decimal("100")
        assert result.ask_size == Decimal("200")
        assert result.timestamp_raw == sample_timestamp

    def test_extract_from_object_format(
        self, processor: RealTimeDataProcessor, sample_timestamp: datetime
    ) -> None:
        """Test quote extraction from Alpaca object format."""
        class MockQuote:
            bid_price = 150.25
            ask_price = 150.27
            bid_size = 100
            ask_size = 200
            timestamp = sample_timestamp
        
        data = MockQuote()
        result = processor.extract_quote_values(data)
        
        assert isinstance(result, QuoteExtractionResult)
        assert result.bid_price == Decimal("150.25")
        assert result.ask_price == Decimal("150.27")
        assert result.bid_size == Decimal("100")
        assert result.ask_size == Decimal("200")
        assert result.timestamp_raw == sample_timestamp

    def test_handles_none_values(self, processor: RealTimeDataProcessor) -> None:
        """Test that None values are handled correctly."""
        data = {"bp": None, "ap": None, "bs": None, "as": None, "t": None}
        result = processor.extract_quote_values(data)
        
        assert result.bid_price is None
        assert result.ask_price is None
        assert result.bid_size is None
        assert result.ask_size is None
        assert result.timestamp_raw is None

    def test_decimal_precision_maintained(self, processor: RealTimeDataProcessor) -> None:
        """Test that Decimal precision is maintained for financial data."""
        data = {
            "bp": "150.123456789",
            "ap": "150.987654321",
            "bs": 100,
            "as": 200,
            "t": None
        }
        result = processor.extract_quote_values(data)
        
        # Verify exact Decimal precision
        assert result.bid_price == Decimal("150.123456789")
        assert result.ask_price == Decimal("150.987654321")

    def test_result_is_frozen(self, processor: RealTimeDataProcessor) -> None:
        """Test that QuoteExtractionResult is immutable/frozen."""
        data = {"bp": 150.25, "ap": 150.27, "bs": 100, "as": 200, "t": None}
        result = processor.extract_quote_values(data)
        
        # Should raise FrozenInstanceError when trying to modify
        with pytest.raises(Exception):  # dataclass frozen=True raises FrozenInstanceError
            result.bid_price = Decimal("999.99")  # type: ignore


class TestExtractSymbolFromTrade(TestRealTimeDataProcessor):
    """Tests for extract_symbol_from_trade method."""

    def test_extract_from_dict_with_symbol_key(self, processor: RealTimeDataProcessor) -> None:
        """Test symbol extraction from dict with 'symbol' key."""
        data = {"symbol": "AAPL", "price": 150.25}
        result = processor.extract_symbol_from_trade(data)
        assert result == "AAPL"

    def test_extract_from_object_with_symbol_attr(self, processor: RealTimeDataProcessor) -> None:
        """Test symbol extraction from object with symbol attribute."""
        class MockTrade:
            symbol = "TSLA"
        
        data = MockTrade()
        result = processor.extract_symbol_from_trade(data)
        assert result == "TSLA"

    def test_raises_error_when_symbol_missing(self, processor: RealTimeDataProcessor) -> None:
        """Test that DataProviderError is raised when symbol is missing."""
        data = {"price": 150.25}  # No symbol
        with pytest.raises(DataProviderError, match="Symbol missing or empty"):
            processor.extract_symbol_from_trade(data)


class TestExtractTradeValues(TestRealTimeDataProcessor):
    """Tests for extract_trade_values method."""

    def test_extract_from_dict_format(
        self, processor: RealTimeDataProcessor, sample_timestamp: datetime
    ) -> None:
        """Test trade extraction from dict format."""
        data = {
            "price": 150.25,
            "size": 100,
            "volume": 100,
            "timestamp": sample_timestamp
        }
        price, volume, timestamp = processor.extract_trade_values(data)
        
        assert price == Decimal("150.25")
        assert volume == Decimal("100")
        assert timestamp == sample_timestamp

    def test_extract_from_object_format(
        self, processor: RealTimeDataProcessor, sample_timestamp: datetime
    ) -> None:
        """Test trade extraction from object format."""
        class MockTrade:
            price = 150.25
            size = 100
            volume = 100
            timestamp = sample_timestamp
        
        data = MockTrade()
        price, volume, timestamp = processor.extract_trade_values(data)
        
        assert price == Decimal("150.25")
        assert volume == Decimal("100")
        assert timestamp == sample_timestamp

    def test_raises_error_when_price_missing(
        self, processor: RealTimeDataProcessor, sample_timestamp: datetime
    ) -> None:
        """Test that DataProviderError is raised when price is missing."""
        data = {"size": 100, "timestamp": sample_timestamp}
        with pytest.raises(DataProviderError, match="Price missing"):
            processor.extract_trade_values(data)

    def test_raises_error_when_price_invalid(
        self, processor: RealTimeDataProcessor, sample_timestamp: datetime
    ) -> None:
        """Test that DataProviderError is raised when price is invalid."""
        data = {"price": "invalid", "size": 100, "timestamp": sample_timestamp}
        with pytest.raises(DataProviderError, match="Invalid price"):
            processor.extract_trade_values(data)

    def test_raises_error_when_timestamp_missing(self, processor: RealTimeDataProcessor) -> None:
        """Test that DataProviderError is raised when timestamp is missing."""
        data = {"price": 150.25, "size": 100}
        with pytest.raises(DataProviderError, match="timestamp missing or invalid"):
            processor.extract_trade_values(data)

    def test_decimal_precision_for_price(
        self, processor: RealTimeDataProcessor, sample_timestamp: datetime
    ) -> None:
        """Test that Decimal precision is maintained for price."""
        data = {
            "price": "150.123456789",
            "size": 100,
            "timestamp": sample_timestamp
        }
        price, _, _ = processor.extract_trade_values(data)
        
        assert price == Decimal("150.123456789")

    def test_volume_can_be_none(
        self, processor: RealTimeDataProcessor, sample_timestamp: datetime
    ) -> None:
        """Test that volume can be None."""
        data = {
            "price": 150.25,
            "size": None,
            "volume": None,
            "timestamp": sample_timestamp
        }
        _, volume, _ = processor.extract_trade_values(data)
        
        assert volume is None


class TestGetQuoteTimestamp(TestRealTimeDataProcessor):
    """Tests for get_quote_timestamp method."""

    def test_returns_datetime_when_valid(
        self, processor: RealTimeDataProcessor, sample_timestamp: datetime
    ) -> None:
        """Test that valid datetime is returned."""
        result = processor.get_quote_timestamp(sample_timestamp)
        assert result == sample_timestamp

    def test_raises_error_when_none(self, processor: RealTimeDataProcessor) -> None:
        """Test that DataProviderError is raised when timestamp is None."""
        with pytest.raises(DataProviderError, match="timestamp missing or invalid"):
            processor.get_quote_timestamp(None)

    def test_raises_error_when_not_datetime(self, processor: RealTimeDataProcessor) -> None:
        """Test that DataProviderError is raised when timestamp is not datetime."""
        with pytest.raises(DataProviderError, match="timestamp missing or invalid"):
            processor.get_quote_timestamp("2025-01-06")  # type: ignore


class TestGetTradeTimestamp(TestRealTimeDataProcessor):
    """Tests for get_trade_timestamp method."""

    def test_returns_datetime_when_valid(
        self, processor: RealTimeDataProcessor, sample_timestamp: datetime
    ) -> None:
        """Test that valid datetime is returned."""
        result = processor.get_trade_timestamp(sample_timestamp)
        assert result == sample_timestamp

    def test_raises_error_when_none(self, processor: RealTimeDataProcessor) -> None:
        """Test that DataProviderError is raised when timestamp is None."""
        with pytest.raises(DataProviderError, match="timestamp missing or invalid"):
            processor.get_trade_timestamp(None)

    def test_raises_error_when_not_datetime(self, processor: RealTimeDataProcessor) -> None:
        """Test that DataProviderError is raised when timestamp is not datetime."""
        with pytest.raises(DataProviderError, match="timestamp missing or invalid"):
            processor.get_trade_timestamp("2025-01-06")


class TestSafeDecimalConvert(TestRealTimeDataProcessor):
    """Tests for _safe_decimal_convert method."""

    def test_converts_int_to_decimal(self, processor: RealTimeDataProcessor) -> None:
        """Test conversion of int to Decimal."""
        result = processor._safe_decimal_convert(150)
        assert result == Decimal("150")

    def test_converts_float_to_decimal(self, processor: RealTimeDataProcessor) -> None:
        """Test conversion of float to Decimal."""
        result = processor._safe_decimal_convert(150.25)
        assert result == Decimal("150.25")

    def test_converts_string_to_decimal(self, processor: RealTimeDataProcessor) -> None:
        """Test conversion of string to Decimal."""
        result = processor._safe_decimal_convert("150.25")
        assert result == Decimal("150.25")

    def test_returns_none_for_none_input(self, processor: RealTimeDataProcessor) -> None:
        """Test that None input returns None."""
        result = processor._safe_decimal_convert(None)
        assert result is None

    def test_returns_none_for_invalid_string(self, processor: RealTimeDataProcessor) -> None:
        """Test that invalid string returns None."""
        result = processor._safe_decimal_convert("invalid")
        assert result is None

    def test_maintains_precision(self, processor: RealTimeDataProcessor) -> None:
        """Test that precision is maintained with many decimal places."""
        result = processor._safe_decimal_convert("150.123456789012345")
        assert result == Decimal("150.123456789012345")


class TestSafeDatetimeConvert(TestRealTimeDataProcessor):
    """Tests for _safe_datetime_convert method."""

    def test_returns_datetime_when_datetime(
        self, processor: RealTimeDataProcessor, sample_timestamp: datetime
    ) -> None:
        """Test that datetime is returned when input is datetime."""
        result = processor._safe_datetime_convert(sample_timestamp)
        assert result == sample_timestamp

    def test_returns_none_for_non_datetime(self, processor: RealTimeDataProcessor) -> None:
        """Test that None is returned for non-datetime input."""
        result = processor._safe_datetime_convert("2025-01-06")
        assert result is None

    def test_returns_none_for_none(self, processor: RealTimeDataProcessor) -> None:
        """Test that None is returned for None input."""
        result = processor._safe_datetime_convert(None)
        assert result is None


class TestLogQuoteDebug(TestRealTimeDataProcessor):
    """Tests for log_quote_debug method."""

    def test_logs_quote_with_correlation_id(self, processor: RealTimeDataProcessor) -> None:
        """Test that quote is logged with correlation_id."""
        # This test verifies the method doesn't raise an error
        # Actual logging verification would require mocking the logger
        processor.log_quote_debug(
            symbol="AAPL",
            bid_price=Decimal("150.25"),
            ask_price=Decimal("150.27"),
            correlation_id="test-correlation-123"
        )

    def test_logs_quote_without_correlation_id(self, processor: RealTimeDataProcessor) -> None:
        """Test that quote is logged without correlation_id."""
        processor.log_quote_debug(
            symbol="AAPL",
            bid_price=Decimal("150.25"),
            ask_price=Decimal("150.27")
        )

    def test_logs_quote_with_none_values(self, processor: RealTimeDataProcessor) -> None:
        """Test that quote with None values is logged."""
        processor.log_quote_debug(
            symbol="AAPL",
            bid_price=None,
            ask_price=None
        )


class TestHandleQuoteError(TestRealTimeDataProcessor):
    """Tests for handle_quote_error method."""

    def test_handles_error_with_correlation_id(self, processor: RealTimeDataProcessor) -> None:
        """Test that error is handled with correlation_id."""
        error = ValueError("Test error")
        processor.handle_quote_error(error, correlation_id="test-correlation-123")

    def test_handles_error_without_correlation_id(self, processor: RealTimeDataProcessor) -> None:
        """Test that error is handled without correlation_id."""
        error = ValueError("Test error")
        processor.handle_quote_error(error)

    def test_handles_different_error_types(self, processor: RealTimeDataProcessor) -> None:
        """Test that different error types are handled."""
        errors = [
            ValueError("Value error"),
            TypeError("Type error"),
            DataProviderError("Data provider error")
        ]
        for error in errors:
            processor.handle_quote_error(error)
