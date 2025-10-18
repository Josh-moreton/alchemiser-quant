#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Tests for Alpaca utilities factory functions.

Validates:
- Factory functions create correct client types
- Credential validation works correctly
- Error handling is proper
- Logging occurs as expected
- Edge cases are handled gracefully
"""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest
from alpaca.data.enums import DataFeed
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.live import StockDataStream
from alpaca.data.requests import StockBarsRequest, StockLatestQuoteRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.trading.client import TradingClient
from alpaca.trading.stream import TradingStream

from the_alchemiser.shared.brokers.alpaca_utils import (
    DEFAULT_DATA_FEED,
    DEFAULT_PAPER_TRADING,
    VALID_DATA_FEEDS,
    VALID_TIMEFRAME_UNITS,
    create_data_client,
    create_stock_bars_request,
    create_stock_data_stream,
    create_stock_latest_quote_request,
    create_timeframe,
    create_trading_client,
    create_trading_stream,
    get_alpaca_quote_type,
    get_alpaca_trade_type,
)
from the_alchemiser.shared.errors.exceptions import ConfigurationError


class TestCredentialValidation:
    """Test credential validation for factory functions."""

    def test_empty_api_key_raises_error(self) -> None:
        """Test that empty API key raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            create_trading_client("", "valid_secret")

        assert "API key cannot be empty" in str(exc_info.value)
        assert exc_info.value.config_key == "api_key"

    def test_whitespace_api_key_raises_error(self) -> None:
        """Test that whitespace-only API key raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            create_trading_client("   ", "valid_secret")

        assert "API key cannot be empty" in str(exc_info.value)

    def test_empty_secret_key_raises_error(self) -> None:
        """Test that empty secret key raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            create_data_client("valid_api", "")

        assert "secret key cannot be empty" in str(exc_info.value)
        assert exc_info.value.config_key == "secret_key"

    def test_whitespace_secret_key_raises_error(self) -> None:
        """Test that whitespace-only secret key raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            create_data_client("valid_api", "   ")

        assert "secret key cannot be empty" in str(exc_info.value)

    def test_none_api_key_raises_error(self) -> None:
        """Test that None API key raises ConfigurationError."""
        with pytest.raises((ConfigurationError, AttributeError)):
            create_trading_client(None, "valid_secret")  # type: ignore[arg-type]

    def test_none_secret_key_raises_error(self) -> None:
        """Test that None secret key raises ConfigurationError."""
        with pytest.raises((ConfigurationError, AttributeError)):
            create_trading_client("valid_api", None)  # type: ignore[arg-type]


class TestTradingClientFactory:
    """Test create_trading_client factory function."""

    @patch("the_alchemiser.shared.brokers.alpaca_utils.TradingClient")
    def test_creates_trading_client_with_defaults(self, mock_trading_client: Mock) -> None:
        """Test factory creates TradingClient with default parameters."""
        mock_instance = Mock(spec=TradingClient)
        mock_trading_client.return_value = mock_instance

        result = create_trading_client("test_api", "test_secret")

        mock_trading_client.assert_called_once_with(
            api_key="test_api",
            secret_key="test_secret",
            paper=DEFAULT_PAPER_TRADING,
        )
        assert result == mock_instance

    @patch("the_alchemiser.shared.brokers.alpaca_utils.TradingClient")
    def test_creates_trading_client_with_paper_false(self, mock_trading_client: Mock) -> None:
        """Test factory creates TradingClient with paper=False."""
        mock_instance = Mock(spec=TradingClient)
        mock_trading_client.return_value = mock_instance

        result = create_trading_client("test_api", "test_secret", paper=False)

        mock_trading_client.assert_called_once_with(
            api_key="test_api",
            secret_key="test_secret",
            paper=False,
        )
        assert result == mock_instance

    @patch("the_alchemiser.shared.brokers.alpaca_utils.TradingClient")
    def test_raises_configuration_error_on_failure(self, mock_trading_client: Mock) -> None:
        """Test that client creation failure raises ConfigurationError."""
        mock_trading_client.side_effect = RuntimeError("Connection failed")

        with pytest.raises(ConfigurationError) as exc_info:
            create_trading_client("test_api", "test_secret")

        assert "Failed to initialize Alpaca TradingClient" in str(exc_info.value)
        assert exc_info.value.config_key == "trading_client"

    @patch("the_alchemiser.shared.brokers.alpaca_utils.logger")
    @patch("the_alchemiser.shared.brokers.alpaca_utils.TradingClient")
    def test_logs_client_creation(self, mock_trading_client: Mock, mock_logger: Mock) -> None:
        """Test that client creation is logged."""
        mock_instance = Mock(spec=TradingClient)
        mock_trading_client.return_value = mock_instance

        create_trading_client("test_api", "test_secret", paper=True)

        mock_logger.debug.assert_called_once()
        assert "Creating TradingClient" in str(mock_logger.debug.call_args)


class TestDataClientFactory:
    """Test create_data_client factory function."""

    @patch("the_alchemiser.shared.brokers.alpaca_utils.StockHistoricalDataClient")
    def test_creates_data_client(self, mock_data_client: Mock) -> None:
        """Test factory creates StockHistoricalDataClient."""
        mock_instance = Mock(spec=StockHistoricalDataClient)
        mock_data_client.return_value = mock_instance

        result = create_data_client("test_api", "test_secret")

        mock_data_client.assert_called_once_with(
            api_key="test_api",
            secret_key="test_secret",
        )
        assert result == mock_instance

    @patch("the_alchemiser.shared.brokers.alpaca_utils.StockHistoricalDataClient")
    def test_raises_configuration_error_on_failure(self, mock_data_client: Mock) -> None:
        """Test that client creation failure raises ConfigurationError."""
        mock_data_client.side_effect = RuntimeError("API error")

        with pytest.raises(ConfigurationError) as exc_info:
            create_data_client("test_api", "test_secret")

        assert "Failed to initialize Alpaca StockHistoricalDataClient" in str(exc_info.value)
        assert exc_info.value.config_key == "data_client"


class TestTradingStreamFactory:
    """Test create_trading_stream factory function."""

    @patch("the_alchemiser.shared.brokers.alpaca_utils.TradingStream")
    def test_creates_trading_stream(self, mock_trading_stream: Mock) -> None:
        """Test factory creates TradingStream."""
        mock_instance = Mock(spec=TradingStream)
        mock_trading_stream.return_value = mock_instance

        result = create_trading_stream("test_api", "test_secret")

        mock_trading_stream.assert_called_once_with(
            api_key="test_api",
            secret_key="test_secret",
            paper=DEFAULT_PAPER_TRADING,
        )
        assert result == mock_instance

    @patch("the_alchemiser.shared.brokers.alpaca_utils.TradingStream")
    def test_creates_trading_stream_with_paper_false(self, mock_trading_stream: Mock) -> None:
        """Test factory creates TradingStream with paper=False."""
        mock_instance = Mock(spec=TradingStream)
        mock_trading_stream.return_value = mock_instance

        result = create_trading_stream("test_api", "test_secret", paper=False)

        mock_trading_stream.assert_called_once_with(
            api_key="test_api",
            secret_key="test_secret",
            paper=False,
        )
        assert result == mock_instance


class TestStockDataStreamFactory:
    """Test create_stock_data_stream factory function."""

    @patch("the_alchemiser.shared.brokers.alpaca_utils.StockDataStream")
    def test_creates_stock_data_stream_with_default_feed(self, mock_stream: Mock) -> None:
        """Test factory creates StockDataStream with default IEX feed."""
        mock_instance = Mock(spec=StockDataStream)
        mock_stream.return_value = mock_instance

        result = create_stock_data_stream("test_api", "test_secret")

        mock_stream.assert_called_once_with(
            api_key="test_api",
            secret_key="test_secret",
            feed=DataFeed.IEX,
        )
        assert result == mock_instance

    @patch("the_alchemiser.shared.brokers.alpaca_utils.StockDataStream")
    def test_creates_stock_data_stream_with_iex_feed(self, mock_stream: Mock) -> None:
        """Test factory creates StockDataStream with IEX feed."""
        mock_instance = Mock(spec=StockDataStream)
        mock_stream.return_value = mock_instance

        result = create_stock_data_stream("test_api", "test_secret", feed="iex")

        mock_stream.assert_called_once_with(
            api_key="test_api",
            secret_key="test_secret",
            feed=DataFeed.IEX,
        )
        assert result == mock_instance

    @patch("the_alchemiser.shared.brokers.alpaca_utils.StockDataStream")
    def test_creates_stock_data_stream_with_sip_feed(self, mock_stream: Mock) -> None:
        """Test factory creates StockDataStream with SIP feed."""
        mock_instance = Mock(spec=StockDataStream)
        mock_stream.return_value = mock_instance

        result = create_stock_data_stream("test_api", "test_secret", feed="sip")

        mock_stream.assert_called_once_with(
            api_key="test_api",
            secret_key="test_secret",
            feed=DataFeed.SIP,
        )
        assert result == mock_instance

    @patch("the_alchemiser.shared.brokers.alpaca_utils.StockDataStream")
    def test_feed_is_case_insensitive(self, mock_stream: Mock) -> None:
        """Test that feed parameter is case insensitive."""
        mock_instance = Mock(spec=StockDataStream)
        mock_stream.return_value = mock_instance

        create_stock_data_stream("test_api", "test_secret", feed="IEX")

        mock_stream.assert_called_once_with(
            api_key="test_api",
            secret_key="test_secret",
            feed=DataFeed.IEX,
        )

    @patch("the_alchemiser.shared.brokers.alpaca_utils.logger")
    @patch("the_alchemiser.shared.brokers.alpaca_utils.StockDataStream")
    def test_unknown_feed_defaults_to_iex_with_warning(
        self, mock_stream: Mock, mock_logger: Mock
    ) -> None:
        """Test that unknown feed defaults to IEX with warning."""
        mock_instance = Mock(spec=StockDataStream)
        mock_stream.return_value = mock_instance

        result = create_stock_data_stream("test_api", "test_secret", feed="unknown")

        mock_stream.assert_called_once_with(
            api_key="test_api",
            secret_key="test_secret",
            feed=DataFeed.IEX,
        )
        mock_logger.warning.assert_called_once()
        assert "Unknown data feed" in str(mock_logger.warning.call_args)


class TestTimeframeFactory:
    """Test create_timeframe factory function."""

    def test_creates_timeframe_with_minute_unit(self) -> None:
        """Test factory creates TimeFrame with minute unit."""
        result = create_timeframe(5, "minute")

        assert isinstance(result, TimeFrame)
        assert result.amount == 5
        assert result.unit == TimeFrameUnit.Minute

    def test_creates_timeframe_with_hour_unit(self) -> None:
        """Test factory creates TimeFrame with hour unit."""
        result = create_timeframe(1, "hour")

        assert isinstance(result, TimeFrame)
        assert result.amount == 1
        assert result.unit == TimeFrameUnit.Hour

    def test_creates_timeframe_with_day_unit(self) -> None:
        """Test factory creates TimeFrame with day unit."""
        result = create_timeframe(1, "day")

        assert isinstance(result, TimeFrame)
        assert result.amount == 1
        assert result.unit == TimeFrameUnit.Day

    def test_creates_timeframe_with_week_unit(self) -> None:
        """Test factory creates TimeFrame with week unit."""
        result = create_timeframe(1, "week")

        assert isinstance(result, TimeFrame)
        assert result.amount == 1
        assert result.unit == TimeFrameUnit.Week

    def test_creates_timeframe_with_month_unit(self) -> None:
        """Test factory creates TimeFrame with month unit."""
        result = create_timeframe(1, "month")

        assert isinstance(result, TimeFrame)
        assert result.amount == 1
        assert result.unit == TimeFrameUnit.Month

    def test_unit_is_case_insensitive(self) -> None:
        """Test that unit parameter is case insensitive."""
        result = create_timeframe(1, "DAY")

        assert result.unit == TimeFrameUnit.Day

    def test_raises_error_for_invalid_unit(self) -> None:
        """Test that invalid unit raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            create_timeframe(1, "invalid")

        assert "Unknown time frame unit" in str(exc_info.value)
        assert exc_info.value.config_key == "timeframe_unit"
        # Check that valid units are included in error message
        assert "minute" in str(exc_info.value)

    def test_raises_error_for_zero_amount(self) -> None:
        """Test that zero amount raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            create_timeframe(0, "day")

        assert "amount must be positive" in str(exc_info.value)
        assert exc_info.value.config_key == "timeframe_amount"
        assert exc_info.value.config_value == 0

    def test_raises_error_for_negative_amount(self) -> None:
        """Test that negative amount raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            create_timeframe(-5, "day")

        assert "amount must be positive" in str(exc_info.value)
        assert exc_info.value.config_value == -5


class TestStockBarsRequestFactory:
    """Test create_stock_bars_request factory function."""

    def test_creates_stock_bars_request_with_no_kwargs(self) -> None:
        """Test factory creates StockBarsRequest with no parameters."""
        # This should raise an error from StockBarsRequest itself
        with pytest.raises(ConfigurationError):
            create_stock_bars_request()

    def test_creates_stock_bars_request_with_kwargs(self) -> None:
        """Test factory creates StockBarsRequest with parameters."""
        # Create a minimal valid request
        result = create_stock_bars_request(
            symbol_or_symbols=["AAPL"],
            timeframe=TimeFrame.Day,
        )

        assert isinstance(result, StockBarsRequest)


class TestStockLatestQuoteRequestFactory:
    """Test create_stock_latest_quote_request factory function."""

    def test_creates_stock_latest_quote_request_with_no_kwargs(self) -> None:
        """Test factory creates StockLatestQuoteRequest with no parameters."""
        # This should raise an error from StockLatestQuoteRequest itself
        with pytest.raises(ConfigurationError):
            create_stock_latest_quote_request()

    def test_creates_stock_latest_quote_request_with_kwargs(self) -> None:
        """Test factory creates StockLatestQuoteRequest with parameters."""
        result = create_stock_latest_quote_request(symbol_or_symbols=["AAPL", "GOOGL"])

        assert isinstance(result, StockLatestQuoteRequest)


class TestTypeGetters:
    """Test get_alpaca_quote_type and get_alpaca_trade_type."""

    def test_get_alpaca_quote_type_returns_type(self) -> None:
        """Test that get_alpaca_quote_type returns the Quote type."""
        result = get_alpaca_quote_type()

        assert isinstance(result, type)
        assert result.__name__ == "Quote"

    def test_get_alpaca_trade_type_returns_type(self) -> None:
        """Test that get_alpaca_trade_type returns the Trade type."""
        result = get_alpaca_trade_type()

        assert isinstance(result, type)
        assert result.__name__ == "Trade"

    def test_quote_type_can_be_used_for_isinstance(self) -> None:
        """Test that returned Quote type works with isinstance."""
        from alpaca.data.models import Quote

        QuoteType = get_alpaca_quote_type()

        # Create a mock quote-like object
        quote = Mock(spec=Quote)

        # This should work without errors
        assert isinstance(quote, QuoteType)

    def test_trade_type_can_be_used_for_isinstance(self) -> None:
        """Test that returned Trade type works with isinstance."""
        from alpaca.data.models import Trade

        TradeType = get_alpaca_trade_type()

        # Create a mock trade-like object
        trade = Mock(spec=Trade)

        # This should work without errors
        assert isinstance(trade, TradeType)


class TestModuleConstants:
    """Test module-level constants."""

    def test_default_paper_trading_is_true(self) -> None:
        """Test that DEFAULT_PAPER_TRADING is True."""
        assert DEFAULT_PAPER_TRADING is True

    def test_default_data_feed_is_iex(self) -> None:
        """Test that DEFAULT_DATA_FEED is 'iex'."""
        assert DEFAULT_DATA_FEED == "iex"

    def test_valid_timeframe_units_list(self) -> None:
        """Test that VALID_TIMEFRAME_UNITS contains expected values."""
        assert "minute" in VALID_TIMEFRAME_UNITS
        assert "hour" in VALID_TIMEFRAME_UNITS
        assert "day" in VALID_TIMEFRAME_UNITS
        assert "week" in VALID_TIMEFRAME_UNITS
        assert "month" in VALID_TIMEFRAME_UNITS

    def test_valid_data_feeds_list(self) -> None:
        """Test that VALID_DATA_FEEDS contains expected values."""
        assert "iex" in VALID_DATA_FEEDS
        assert "sip" in VALID_DATA_FEEDS


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @patch("the_alchemiser.shared.brokers.alpaca_utils.TradingClient")
    def test_very_long_api_key(self, mock_client: Mock) -> None:
        """Test that very long API key is accepted."""
        mock_instance = Mock(spec=TradingClient)
        mock_client.return_value = mock_instance

        long_key = "a" * 10000
        result = create_trading_client(long_key, "test_secret")

        assert result == mock_instance

    def test_timeframe_with_large_amount(self) -> None:
        """Test timeframe with very large amount."""
        result = create_timeframe(1000, "day")

        assert result.amount == 1000
        assert result.unit == TimeFrameUnit.Day

    @patch("the_alchemiser.shared.brokers.alpaca_utils.StockDataStream")
    def test_mixed_case_feed(self, mock_stream: Mock) -> None:
        """Test that mixed case feed works correctly."""
        mock_instance = Mock(spec=StockDataStream)
        mock_stream.return_value = mock_instance

        create_stock_data_stream("test_api", "test_secret", feed="IeX")

        mock_stream.assert_called_once()
        assert mock_stream.call_args[1]["feed"] == DataFeed.IEX
