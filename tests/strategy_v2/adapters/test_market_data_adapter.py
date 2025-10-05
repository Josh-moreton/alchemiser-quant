"""Business Unit: strategy | Status: current

Test market data adapter for correctness, error handling, and numerical precision.

Tests focus on:
- Decimal arithmetic for financial precision
- Proper error handling with typed exceptions
- Input validation
- Empty/missing data scenarios
- Timezone-aware datetime handling
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from the_alchemiser.shared.schemas.market_bar import MarketBar
from the_alchemiser.strategy_v2.adapters.market_data_adapter import (
    StrategyMarketDataAdapter,
)
from the_alchemiser.strategy_v2.errors import MarketDataError


class TestStrategyMarketDataAdapter:
    """Test suite for StrategyMarketDataAdapter."""

    @pytest.fixture
    def mock_alpaca_manager(self):
        """Create mock AlpacaManager."""
        mock = Mock()
        mock.validate_connection.return_value = True
        return mock

    @pytest.fixture
    def mock_market_data_service(self):
        """Create mock MarketDataService."""
        return Mock()

    @pytest.fixture
    def adapter(self, mock_alpaca_manager):
        """Create adapter instance with mocked dependencies."""
        return StrategyMarketDataAdapter(mock_alpaca_manager)

    # Tests for get_bars method

    def test_get_bars_empty_symbols(self, adapter):
        """Test get_bars returns empty dict for empty symbols list."""
        result = adapter.get_bars([], "1D", 30)
        assert result == {}

    def test_get_bars_invalid_lookback_days_zero(self, adapter):
        """Test get_bars raises MarketDataError for zero lookback_days."""
        with pytest.raises(MarketDataError) as exc_info:
            adapter.get_bars(["AAPL"], "1D", 0)
        assert "must be positive" in str(exc_info.value)

    def test_get_bars_invalid_lookback_days_negative(self, adapter):
        """Test get_bars raises MarketDataError for negative lookback_days."""
        with pytest.raises(MarketDataError) as exc_info:
            adapter.get_bars(["AAPL"], "1D", -5)
        assert "must be positive" in str(exc_info.value)

    def test_get_bars_empty_timeframe(self, adapter):
        """Test get_bars raises MarketDataError for empty timeframe."""
        with pytest.raises(MarketDataError) as exc_info:
            adapter.get_bars(["AAPL"], "", 30)
        assert "cannot be empty" in str(exc_info.value)

    def test_get_bars_whitespace_timeframe(self, adapter):
        """Test get_bars raises MarketDataError for whitespace-only timeframe."""
        with pytest.raises(MarketDataError) as exc_info:
            adapter.get_bars(["AAPL"], "   ", 30)
        assert "cannot be empty" in str(exc_info.value)

    def test_get_bars_success_single_symbol(self, adapter, mock_market_data_service):
        """Test successful bar fetching for single symbol."""
        # Mock the market data service
        adapter._market_data_service = mock_market_data_service

        # Create mock bar data
        mock_bar_dict = {
            "timestamp": datetime(2025, 1, 1, tzinfo=UTC),
            "open": 100.0,
            "high": 110.0,
            "low": 95.0,
            "close": 105.0,
            "volume": 1000000,
        }

        mock_market_data_service.get_historical_bars.return_value = [mock_bar_dict]

        # Create expected MarketBar
        with patch.object(
            MarketBar, "from_alpaca_bar"
        ) as mock_from_alpaca:
            expected_bar = MarketBar(
                timestamp=datetime(2025, 1, 1, tzinfo=UTC),
                symbol="AAPL",
                timeframe="1D",
                open_price=Decimal("100.0"),
                high_price=Decimal("110.0"),
                low_price=Decimal("95.0"),
                close_price=Decimal("105.0"),
                volume=1000000,
            )
            mock_from_alpaca.return_value = expected_bar

            result = adapter.get_bars(["AAPL"], "1D", 30)

            assert "AAPL" in result
            assert len(result["AAPL"]) == 1
            assert result["AAPL"][0] == expected_bar

    def test_get_bars_multiple_symbols(self, adapter, mock_market_data_service):
        """Test bar fetching for multiple symbols."""
        adapter._market_data_service = mock_market_data_service

        # Mock different responses for different symbols
        def get_bars_side_effect(symbol, **kwargs):
            return [{"timestamp": datetime.now(UTC), "close": 100.0}]

        mock_market_data_service.get_historical_bars.side_effect = get_bars_side_effect

        with patch.object(MarketBar, "from_alpaca_bar") as mock_from_alpaca:
            mock_bar = Mock(spec=MarketBar)
            mock_from_alpaca.return_value = mock_bar

            result = adapter.get_bars(["AAPL", "MSFT", "GOOGL"], "1D", 30)

            assert len(result) == 3
            assert "AAPL" in result
            assert "MSFT" in result
            assert "GOOGL" in result

    def test_get_bars_with_custom_end_date(self, adapter, mock_market_data_service):
        """Test get_bars with custom end_date parameter."""
        adapter._market_data_service = mock_market_data_service
        mock_market_data_service.get_historical_bars.return_value = []

        custom_end = datetime(2025, 1, 1, tzinfo=UTC)
        result = adapter.get_bars(["AAPL"], "1D", 30, end_date=custom_end)

        # Verify the date range calculation
        call_args = mock_market_data_service.get_historical_bars.call_args
        assert call_args is not None

        # Check that dates are formatted correctly
        expected_end = "2025-01-01"
        expected_start = (custom_end - timedelta(days=30)).strftime("%Y-%m-%d")
        assert call_args[1]["end_date"] == expected_end
        assert call_args[1]["start_date"] == expected_start

    def test_get_bars_bar_conversion_error(self, adapter, mock_market_data_service):
        """Test handling of bar conversion errors."""
        adapter._market_data_service = mock_market_data_service

        # Mock bar data that will fail conversion
        mock_bar_dict = {"invalid": "data"}
        mock_market_data_service.get_historical_bars.return_value = [mock_bar_dict]

        with patch.object(
            MarketBar, "from_alpaca_bar", side_effect=ValueError("Invalid bar data")
        ):
            result = adapter.get_bars(["AAPL"], "1D", 30)

            # Should return empty list for symbol with conversion errors
            assert result["AAPL"] == []

    def test_get_bars_api_error_returns_empty_list(self, adapter, mock_market_data_service):
        """Test that API errors result in empty list for affected symbol."""
        adapter._market_data_service = mock_market_data_service

        # Mock API error
        mock_market_data_service.get_historical_bars.side_effect = Exception("API Error")

        result = adapter.get_bars(["AAPL"], "1D", 30)

        assert result["AAPL"] == []

    def test_get_bars_reraises_market_data_error(self, adapter, mock_market_data_service):
        """Test that MarketDataError is re-raised without wrapping."""
        adapter._market_data_service = mock_market_data_service

        # Mock MarketDataError
        mock_market_data_service.get_historical_bars.side_effect = MarketDataError(
            "Custom error", symbol="AAPL"
        )

        with pytest.raises(MarketDataError) as exc_info:
            adapter.get_bars(["AAPL"], "1D", 30)

        assert "Custom error" in str(exc_info.value)
        assert exc_info.value.symbol == "AAPL"

    # Tests for get_current_prices method

    def test_get_current_prices_empty_symbols(self, adapter):
        """Test get_current_prices returns empty dict for empty symbols list."""
        result = adapter.get_current_prices([])
        assert result == {}

    def test_get_current_prices_decimal_precision(self, adapter, mock_market_data_service):
        """Test that mid-price calculation uses Decimal arithmetic."""
        adapter._market_data_service = mock_market_data_service

        # Mock quote with specific prices that would show float precision issues
        quote = {"bid_price": 100.33, "ask_price": 100.67}
        mock_market_data_service.get_quote.return_value = quote

        result = adapter.get_current_prices(["AAPL"])

        # Verify mid-price is calculated correctly: (100.33 + 100.67) / 2 = 100.50
        assert "AAPL" in result
        # Using Decimal should give exact result
        expected_mid_price = 100.50
        assert abs(result["AAPL"] - expected_mid_price) < 0.001

    def test_get_current_prices_valid_quote(self, adapter, mock_market_data_service):
        """Test successful price fetching with valid quote data."""
        adapter._market_data_service = mock_market_data_service

        quote = {"bid_price": 100.0, "ask_price": 102.0}
        mock_market_data_service.get_quote.return_value = quote

        result = adapter.get_current_prices(["AAPL"])

        assert "AAPL" in result
        assert result["AAPL"] == 101.0  # Mid-price

    def test_get_current_prices_missing_bid(self, adapter, mock_market_data_service):
        """Test error when bid price is missing."""
        adapter._market_data_service = mock_market_data_service

        quote = {"ask_price": 102.0}  # Missing bid_price
        mock_market_data_service.get_quote.return_value = quote

        with pytest.raises(MarketDataError) as exc_info:
            adapter.get_current_prices(["AAPL"])

        assert "Incomplete quote data" in str(exc_info.value)
        assert "AAPL" in str(exc_info.value)

    def test_get_current_prices_missing_ask(self, adapter, mock_market_data_service):
        """Test error when ask price is missing."""
        adapter._market_data_service = mock_market_data_service

        quote = {"bid_price": 100.0}  # Missing ask_price
        mock_market_data_service.get_quote.return_value = quote

        with pytest.raises(MarketDataError) as exc_info:
            adapter.get_current_prices(["AAPL"])

        assert "Incomplete quote data" in str(exc_info.value)

    def test_get_current_prices_none_quote(self, adapter, mock_market_data_service):
        """Test error when quote is None."""
        adapter._market_data_service = mock_market_data_service
        mock_market_data_service.get_quote.return_value = None

        with pytest.raises(MarketDataError) as exc_info:
            adapter.get_current_prices(["AAPL"])

        assert "Incomplete quote data" in str(exc_info.value)

    def test_get_current_prices_zero_bid(self, adapter, mock_market_data_service):
        """Test error when bid price is zero or negative."""
        adapter._market_data_service = mock_market_data_service

        quote = {"bid_price": 0.0, "ask_price": 102.0}
        mock_market_data_service.get_quote.return_value = quote

        with pytest.raises(MarketDataError) as exc_info:
            adapter.get_current_prices(["AAPL"])

        assert "Invalid quote prices" in str(exc_info.value)

    def test_get_current_prices_negative_ask(self, adapter, mock_market_data_service):
        """Test error when ask price is negative."""
        adapter._market_data_service = mock_market_data_service

        quote = {"bid_price": 100.0, "ask_price": -5.0}
        mock_market_data_service.get_quote.return_value = quote

        with pytest.raises(MarketDataError) as exc_info:
            adapter.get_current_prices(["AAPL"])

        assert "Invalid quote prices" in str(exc_info.value)

    def test_get_current_prices_api_error(self, adapter, mock_market_data_service):
        """Test that API errors are wrapped in MarketDataError."""
        adapter._market_data_service = mock_market_data_service
        mock_market_data_service.get_quote.side_effect = Exception("API connection failed")

        with pytest.raises(MarketDataError) as exc_info:
            adapter.get_current_prices(["AAPL"])

        assert "Failed to get current price" in str(exc_info.value)
        assert exc_info.value.symbol == "AAPL"

    def test_get_current_prices_multiple_symbols(self, adapter, mock_market_data_service):
        """Test price fetching for multiple symbols."""
        adapter._market_data_service = mock_market_data_service

        # Mock different quotes for different symbols
        def get_quote_side_effect(symbol):
            quotes = {
                "AAPL": {"bid_price": 100.0, "ask_price": 102.0},
                "MSFT": {"bid_price": 200.0, "ask_price": 204.0},
                "GOOGL": {"bid_price": 150.0, "ask_price": 152.0},
            }
            return quotes.get(symbol)

        mock_market_data_service.get_quote.side_effect = get_quote_side_effect

        result = adapter.get_current_prices(["AAPL", "MSFT", "GOOGL"])

        assert len(result) == 3
        assert result["AAPL"] == 101.0
        assert result["MSFT"] == 202.0
        assert result["GOOGL"] == 151.0

    def test_get_current_prices_reraises_market_data_error(
        self, adapter, mock_market_data_service
    ):
        """Test that MarketDataError from get_quote is re-raised."""
        adapter._market_data_service = mock_market_data_service

        mock_market_data_service.get_quote.side_effect = MarketDataError(
            "Custom error", symbol="AAPL"
        )

        with pytest.raises(MarketDataError) as exc_info:
            adapter.get_current_prices(["AAPL"])

        assert "Custom error" in str(exc_info.value)

    # Tests for validate_connection method

    def test_validate_connection_success(self, adapter, mock_alpaca_manager):
        """Test successful connection validation."""
        mock_alpaca_manager.validate_connection.return_value = True

        result = adapter.validate_connection()

        assert result is True
        mock_alpaca_manager.validate_connection.assert_called_once()

    def test_validate_connection_failure(self, adapter, mock_alpaca_manager):
        """Test connection validation failure."""
        mock_alpaca_manager.validate_connection.return_value = False

        result = adapter.validate_connection()

        assert result is False

    def test_validate_connection_exception_handling(self, adapter, mock_alpaca_manager):
        """Test that exceptions are caught and return False."""
        mock_alpaca_manager.validate_connection.side_effect = Exception("Connection error")

        result = adapter.validate_connection()

        assert result is False

    # Property-based tests using Hypothesis (if available)

    @pytest.mark.parametrize(
        "bid,ask,expected_mid",
        [
            (100.0, 102.0, 101.0),
            (50.50, 50.60, 50.55),
            (1.11, 1.13, 1.12),
            (0.01, 0.03, 0.02),
        ],
    )
    def test_get_current_prices_mid_calculation_precision(
        self, adapter, mock_market_data_service, bid, ask, expected_mid
    ):
        """Test mid-price calculation precision with various price levels."""
        adapter._market_data_service = mock_market_data_service

        quote = {"bid_price": bid, "ask_price": ask}
        mock_market_data_service.get_quote.return_value = quote

        result = adapter.get_current_prices(["AAPL"])

        assert "AAPL" in result
        # Allow small floating-point tolerance
        assert abs(result["AAPL"] - expected_mid) < 0.0001

    def test_get_bars_timezone_aware_dates(self, adapter, mock_market_data_service):
        """Test that dates are properly formatted from timezone-aware datetimes."""
        adapter._market_data_service = mock_market_data_service
        mock_market_data_service.get_historical_bars.return_value = []

        # Use timezone-aware datetime
        end_date = datetime(2025, 1, 15, 14, 30, tzinfo=UTC)
        adapter.get_bars(["AAPL"], "1D", 30, end_date=end_date)

        # Verify the service was called with properly formatted dates
        call_args = mock_market_data_service.get_historical_bars.call_args
        assert call_args[1]["end_date"] == "2025-01-15"
        # Start date should be 30 days before
        assert call_args[1]["start_date"] == "2024-12-16"

    def test_initialization(self, mock_alpaca_manager):
        """Test adapter initialization creates necessary dependencies."""
        adapter = StrategyMarketDataAdapter(mock_alpaca_manager)

        assert adapter._alpaca is mock_alpaca_manager
        assert adapter._market_data_service is not None


# Integration-style tests (mark as integration if needed)


class TestMarketDataAdapterIntegration:
    """Integration tests for market data adapter behavior."""

    @pytest.fixture
    def mock_alpaca_manager(self):
        """Create comprehensive mock AlpacaManager."""
        mock = Mock()
        mock.validate_connection.return_value = True
        return mock

    def test_end_to_end_bar_fetching_workflow(self, mock_alpaca_manager):
        """Test complete workflow of fetching and converting bars."""
        adapter = StrategyMarketDataAdapter(mock_alpaca_manager)

        # Mock the internal service
        with patch.object(adapter._market_data_service, "get_historical_bars") as mock_get_bars:
            mock_get_bars.return_value = [
                {
                    "timestamp": datetime(2025, 1, 1, tzinfo=UTC),
                    "open": 100.0,
                    "high": 110.0,
                    "low": 95.0,
                    "close": 105.0,
                    "volume": 1000000,
                }
            ]

            with patch.object(MarketBar, "from_alpaca_bar") as mock_from_alpaca:
                expected_bar = MarketBar(
                    timestamp=datetime(2025, 1, 1, tzinfo=UTC),
                    symbol="AAPL",
                    timeframe="1D",
                    open_price=Decimal("100.0"),
                    high_price=Decimal("110.0"),
                    low_price=Decimal("95.0"),
                    close_price=Decimal("105.0"),
                    volume=1000000,
                )
                mock_from_alpaca.return_value = expected_bar

                result = adapter.get_bars(["AAPL"], "1D", 30)

                assert len(result) == 1
                assert "AAPL" in result
                assert len(result["AAPL"]) == 1

    def test_error_recovery_partial_success(self, mock_alpaca_manager):
        """Test that partial failures in multi-symbol requests are handled gracefully."""
        adapter = StrategyMarketDataAdapter(mock_alpaca_manager)

        call_count = 0

        def get_bars_side_effect(symbol, **kwargs):
            nonlocal call_count
            call_count += 1
            if symbol == "FAIL":
                raise Exception("API Error")
            return []

        with patch.object(
            adapter._market_data_service, "get_historical_bars", side_effect=get_bars_side_effect
        ):
            result = adapter.get_bars(["AAPL", "FAIL", "MSFT"], "1D", 30)

            # Should have results for all symbols
            assert len(result) == 3
            # Failed symbol should have empty list
            assert result["FAIL"] == []
            # Other symbols should succeed
            assert "AAPL" in result
            assert "MSFT" in result
