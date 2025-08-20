"""Integration test demonstrating full MarketDataPort usage.

This test demonstrates that the StrategyMarketDataService correctly implements
the MarketDataPort protocol and integrates properly with the existing infrastructure.
"""

from unittest.mock import Mock

import pandas as pd

from the_alchemiser.domain.strategies.protocols.market_data_port import MarketDataPort
from the_alchemiser.services.market_data.strategy_market_data_service import (
    StrategyMarketDataService,
)


class TestMarketDataPortIntegration:
    """Integration tests for MarketDataPort implementation."""

    def test_service_satisfies_protocol(self):
        """Test that StrategyMarketDataService satisfies MarketDataPort protocol."""
        # Create service
        service = StrategyMarketDataService("test_key", "test_secret")

        # Check protocol compliance at runtime
        assert isinstance(service, MarketDataPort)

    def test_end_to_end_data_flow(self):
        """Test complete data flow from service through protocol interface."""
        # Arrange
        service = StrategyMarketDataService("test_key", "test_secret")

        # Mock the underlying client to simulate successful API responses
        mock_client = Mock()
        mock_client.get_historical_bars.return_value = pd.DataFrame(
            {
                "Open": [100.0, 101.0, 102.0],
                "High": [105.0, 106.0, 107.0],
                "Low": [99.0, 100.0, 101.0],
                "Close": [104.0, 105.0, 106.0],
                "Volume": [1000, 1100, 1200],
            }
        )
        mock_client.get_current_price_from_quote.return_value = 150.75
        mock_client.get_latest_quote.return_value = (150.50, 151.00)

        service._client = mock_client

        # Act - use service through MarketDataPort protocol interface
        market_data_port: MarketDataPort = service

        # Test get_data
        data = market_data_port.get_data("AAPL", timeframe="1day", period="6m")
        assert isinstance(data, pd.DataFrame)
        assert len(data) == 3
        assert "Close" in data.columns

        # Test get_current_price
        price = market_data_port.get_current_price("AAPL")
        assert price == 150.75

        # Test get_latest_quote
        bid, ask = market_data_port.get_latest_quote("AAPL")
        assert bid == 150.50
        assert ask == 151.00

        # Assert correct underlying calls were made
        mock_client.get_historical_bars.assert_called_once_with(
            symbol="AAPL", period="6m", interval="1d"
        )
        mock_client.get_current_price_from_quote.assert_called_once_with("AAPL")
        mock_client.get_latest_quote.assert_called_once_with("AAPL")

    def test_error_resilience(self):
        """Test that service handles errors gracefully through protocol interface."""
        # Arrange
        service = StrategyMarketDataService("test_key", "test_secret")

        # Mock client with errors
        mock_client = Mock()
        mock_client.get_historical_bars.side_effect = Exception("Network error")
        mock_client.get_current_price_from_quote.side_effect = Exception("Quote error")
        mock_client.get_latest_quote.side_effect = Exception("Quote error")

        service._client = mock_client

        # Act through protocol interface
        market_data_port: MarketDataPort = service

        # Test that errors are handled gracefully
        data = market_data_port.get_data("INVALID")
        assert isinstance(data, pd.DataFrame)
        assert data.empty

        price = market_data_port.get_current_price("INVALID")
        assert price is None

        quote = market_data_port.get_latest_quote("INVALID")
        assert quote == (None, None)

    def test_protocol_type_constraints(self):
        """Test that protocol enforces correct return types."""
        service = StrategyMarketDataService("test_key", "test_secret")

        # Mock client with proper returns
        mock_client = Mock()
        mock_client.get_historical_bars.return_value = pd.DataFrame()
        mock_client.get_current_price_from_quote.return_value = 100.0
        mock_client.get_latest_quote.return_value = (99.0, 101.0)

        service._client = mock_client

        # Use service through protocol
        port: MarketDataPort = service

        # Verify return types match protocol
        data = port.get_data("TEST")
        assert isinstance(data, pd.DataFrame)

        price = port.get_current_price("TEST")
        assert isinstance(price, float | type(None))

        quote = port.get_latest_quote("TEST")
        assert isinstance(quote, tuple)
        assert len(quote) == 2
        assert all(isinstance(x, float | type(None)) for x in quote)

    def test_strategy_usage_pattern(self):
        """Test the intended usage pattern for strategies."""
        # This test demonstrates how a strategy would actually use the service

        # Arrange - create service and mock data
        service = StrategyMarketDataService("test_key", "test_secret")
        mock_client = Mock()

        # Mock different data for different symbols
        def mock_get_data(symbol, **kwargs):
            if symbol == "AAPL":
                return pd.DataFrame({"Close": [150, 151, 152]})
            elif symbol == "MSFT":
                return pd.DataFrame({"Close": [300, 301, 302]})
            else:
                return pd.DataFrame()

        mock_client.get_historical_bars.side_effect = mock_get_data
        service._client = mock_client

        # Act - simulate strategy using the service
        symbols = ["AAPL", "MSFT", "GOOGL"]
        market_data_results = {}

        for symbol in symbols:
            data = service.get_data(symbol)
            if not data.empty:
                market_data_results[symbol] = data

        # Assert - verify results match expected pattern
        assert len(market_data_results) == 2  # AAPL and MSFT have data
        assert "AAPL" in market_data_results
        assert "MSFT" in market_data_results
        assert "GOOGL" not in market_data_results  # Empty data filtered out

        # Check that each symbol got the correct data
        assert market_data_results["AAPL"]["Close"].iloc[-1] == 152
        assert market_data_results["MSFT"]["Close"].iloc[-1] == 302
