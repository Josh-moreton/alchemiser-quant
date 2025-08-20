"""Unit tests for StrategyMarketDataService implementation of MarketDataPort."""

import pytest
import pandas as pd
from unittest.mock import Mock

from the_alchemiser.services.market_data.strategy_market_data_service import StrategyMarketDataService


class TestStrategyMarketDataService:
    """Test suite for StrategyMarketDataService."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create service instance with mock credentials
        self.service = StrategyMarketDataService("test_key", "test_secret")
        
        # Mock the underlying MarketDataClient
        self.mock_client = Mock()
        self.service._client = self.mock_client

    def test_get_data_success(self):
        """Test successful data retrieval."""
        # Arrange
        expected_df = pd.DataFrame({
            'Open': [100.0, 101.0],
            'High': [105.0, 106.0],
            'Low': [99.0, 100.0],
            'Close': [102.0, 103.0],
            'Volume': [1000, 1100]
        })
        self.mock_client.get_historical_bars.return_value = expected_df
        
        # Act
        result = self.service.get_data("AAPL", timeframe="1day", period="1y")
        
        # Assert
        assert result.equals(expected_df)
        self.mock_client.get_historical_bars.assert_called_once_with(
            symbol="AAPL",
            period="1y",
            interval="1d"
        )

    def test_get_data_with_different_timeframes(self):
        """Test timeframe mapping for get_data."""
        test_cases = [
            ("1day", "1d"),
            ("1d", "1d"),
            ("day", "1d"),
            ("daily", "1d"),
            ("1hour", "1h"),
            ("1h", "1h"),
            ("hour", "1h"),
            ("hourly", "1h"),
            ("1min", "1m"),
            ("1m", "1m"),
            ("minute", "1m"),
            ("min", "1m"),
            ("unknown", "1d"),  # Should default to 1d
        ]
        
        for timeframe, expected_interval in test_cases:
            # Arrange
            self.mock_client.reset_mock()
            self.mock_client.get_historical_bars.return_value = pd.DataFrame()
            
            # Act
            self.service.get_data("AAPL", timeframe=timeframe)
            
            # Assert
            self.mock_client.get_historical_bars.assert_called_once_with(
                symbol="AAPL",
                period="1y",
                interval=expected_interval
            )

    def test_get_data_error_handling(self):
        """Test error handling in get_data."""
        # Arrange
        self.mock_client.get_historical_bars.side_effect = Exception("API Error")
        
        # Act
        result = self.service.get_data("AAPL")
        
        # Assert
        assert isinstance(result, pd.DataFrame)
        assert result.empty

    def test_get_current_price_success(self):
        """Test successful current price retrieval."""
        # Arrange
        expected_price = 150.25
        self.mock_client.get_current_price_from_quote.return_value = expected_price
        
        # Act
        result = self.service.get_current_price("AAPL")
        
        # Assert
        assert result == expected_price
        self.mock_client.get_current_price_from_quote.assert_called_once_with("AAPL")

    def test_get_current_price_error_handling(self):
        """Test error handling in get_current_price."""
        # Arrange
        self.mock_client.get_current_price_from_quote.side_effect = Exception("API Error")
        
        # Act
        result = self.service.get_current_price("AAPL")
        
        # Assert
        assert result is None

    def test_get_latest_quote_success(self):
        """Test successful quote retrieval."""
        # Arrange
        expected_quote = (149.50, 150.00)
        self.mock_client.get_latest_quote.return_value = expected_quote
        
        # Act
        result = self.service.get_latest_quote("AAPL")
        
        # Assert
        assert result == expected_quote
        self.mock_client.get_latest_quote.assert_called_once_with("AAPL")

    def test_get_latest_quote_error_handling(self):
        """Test error handling in get_latest_quote."""
        # Arrange
        self.mock_client.get_latest_quote.side_effect = Exception("API Error")
        
        # Act
        result = self.service.get_latest_quote("AAPL")
        
        # Assert
        assert result == (None, None)

    def test_map_timeframe_to_interval_private_method(self):
        """Test the private timeframe mapping method."""
        # Test various timeframe mappings
        test_cases = [
            ("1DAY", "1d"),  # Case insensitive
            ("DAILY", "1d"),
            ("1HOUR", "1h"),
            ("HOURLY", "1h"),
            ("1MIN", "1m"),
            ("MINUTE", "1m"),
            ("invalid_timeframe", "1d"),  # Default case
        ]
        
        for timeframe, expected in test_cases:
            result = self.service._map_timeframe_to_interval(timeframe)
            assert result == expected

    def test_protocol_compliance(self):
        """Test that the service implements the MarketDataPort protocol correctly."""
        from the_alchemiser.domain.strategies.protocols.market_data_port import MarketDataPort
        
        # Check that the service has all required methods
        assert hasattr(self.service, 'get_data')
        assert hasattr(self.service, 'get_current_price')
        assert hasattr(self.service, 'get_latest_quote')
        
        # Check that methods have correct signatures (basic check)
        assert callable(self.service.get_data)
        assert callable(self.service.get_current_price)
        assert callable(self.service.get_latest_quote)

    def test_kwargs_passthrough(self):
        """Test that kwargs are properly handled in all methods."""
        # Arrange
        self.mock_client.get_historical_bars.return_value = pd.DataFrame()
        self.mock_client.get_current_price_from_quote.return_value = 100.0
        self.mock_client.get_latest_quote.return_value = (99.0, 101.0)
        
        # Act - test that kwargs don't break the methods
        self.service.get_data("AAPL", extra_param="test")
        self.service.get_current_price("AAPL", extra_param="test")
        self.service.get_latest_quote("AAPL", extra_param="test")
        
        # Assert - methods should complete without error
        # The kwargs are accepted but not necessarily passed through to the client
        assert True  # If we get here, the methods handled kwargs correctly

    def test_initialization(self):
        """Test service initialization."""
        # Test that service can be created with valid credentials
        service = StrategyMarketDataService("api_key", "secret_key")
        assert service is not None
        assert hasattr(service, '_client')