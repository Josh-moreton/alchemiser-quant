#!/usr/bin/env python3
"""
Baseline Tests for UnifiedDataProvider Refactoring

These tests capture the existing behavior of UnifiedDataProvider before refactoring
to ensure that the new service-based architecture maintains the same functionality.
"""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from the_alchemiser.infrastructure.data_providers.data_provider import UnifiedDataProvider
from the_alchemiser.services.exceptions import ConfigurationError


class TestUnifiedDataProviderBaseline:
    """Baseline tests for current UnifiedDataProvider behavior."""

    @pytest.fixture
    def mock_config(self) -> Mock:
        """Mock configuration object."""
        config = Mock()
        config.data.cache_duration = 3600
        config.alpaca.paper_endpoint = "https://paper-api.alpaca.markets"
        config.alpaca.endpoint = "https://api.alpaca.markets"
        return config

    @pytest.fixture
    def mock_secrets_manager(self) -> Mock:
        """Mock secrets manager that returns valid API keys."""
        with patch("the_alchemiser.core.data.data_provider.SecretsManager") as mock_sm:
            mock_instance = Mock()
            mock_instance.get_alpaca_keys.return_value = ("test_api_key", "test_secret_key")
            mock_sm.return_value = mock_instance
            yield mock_instance

    @pytest.fixture
    def mock_alpaca_clients(self) -> tuple[Mock, Mock]:
        """Mock Alpaca data and trading clients."""
        with (
            patch(
                "the_alchemiser.core.data.data_provider.StockHistoricalDataClient"
            ) as mock_data_client,
            patch("the_alchemiser.core.data.data_provider.TradingClient") as mock_trading_client,
        ):

            data_client_instance = Mock()
            trading_client_instance = Mock()

            mock_data_client.return_value = data_client_instance
            mock_trading_client.return_value = trading_client_instance

            yield data_client_instance, trading_client_instance

    def test_initialization_paper_trading_default(
        self, mock_config, mock_secrets_manager, mock_alpaca_clients
    ):
        """Test that UnifiedDataProvider initializes correctly with default paper trading."""
        data_client, trading_client = mock_alpaca_clients

        provider = UnifiedDataProvider(config=mock_config)

        assert provider.paper_trading is True
        assert provider.cache_duration == 3600
        assert provider.api_key == "test_api_key"
        assert provider.secret_key == "test_secret_key"
        mock_secrets_manager.get_alpaca_keys.assert_called_once_with(paper_trading=True)

    def test_initialization_live_trading(
        self, mock_config, mock_secrets_manager, mock_alpaca_clients
    ):
        """Test that UnifiedDataProvider initializes correctly with live trading."""
        data_client, trading_client = mock_alpaca_clients

        provider = UnifiedDataProvider(paper_trading=False, config=mock_config)

        assert provider.paper_trading is False
        mock_secrets_manager.get_alpaca_keys.assert_called_once_with(paper_trading=False)

    def test_initialization_missing_credentials_raises_error(self, mock_config):
        """Test that missing credentials raise ConfigurationError."""
        with patch("the_alchemiser.core.data.data_provider.SecretsManager") as mock_sm:
            mock_instance = Mock()
            mock_instance.get_alpaca_keys.return_value = (None, None)
            mock_sm.return_value = mock_instance

            with pytest.raises(ConfigurationError, match="Alpaca API keys not found"):
                UnifiedDataProvider(config=mock_config)

    def test_get_data_returns_cached_data(
        self, mock_config, mock_secrets_manager, mock_alpaca_clients
    ):
        """Test that get_data returns cached data when available."""
        data_client, trading_client = mock_alpaca_clients
        provider = UnifiedDataProvider(config=mock_config)

        # Create sample DataFrame
        sample_df = pd.DataFrame(
            {
                "Open": [100.0, 101.0],
                "High": [102.0, 103.0],
                "Low": [99.0, 100.0],
                "Close": [101.0, 102.0],
                "Volume": [1000, 1100],
            }
        )

        # Manually populate cache
        import time

        cache_key = ("AAPL", "1y", "1d")
        provider.cache[cache_key] = (time.time(), sample_df)

        result = provider.get_data("AAPL", "1y", "1d")

        # Should return cached data without calling API
        pd.testing.assert_frame_equal(result, sample_df)
        data_client.get_stock_bars.assert_not_called()

    def test_get_data_fetches_fresh_data_when_cache_expired(
        self, mock_config, mock_secrets_manager, mock_alpaca_clients
    ):
        """Test that get_data fetches fresh data when cache is expired."""
        data_client, trading_client = mock_alpaca_clients
        provider = UnifiedDataProvider(cache_duration=1, config=mock_config)

        # Mock API response
        mock_bar1 = Mock()
        mock_bar1.open = 100.0
        mock_bar1.high = 102.0
        mock_bar1.low = 99.0
        mock_bar1.close = 101.0
        mock_bar1.volume = 1000
        mock_bar1.timestamp = datetime.now()

        mock_response = Mock()
        mock_response.AAPL = [mock_bar1]
        data_client.get_stock_bars.return_value = mock_response

        # Add expired cache entry
        import time

        cache_key = ("AAPL", "1y", "1d")
        provider.cache[cache_key] = (time.time() - 3600, pd.DataFrame())  # Expired

        result = provider.get_data("AAPL", "1y", "1d")

        # Should fetch fresh data
        data_client.get_stock_bars.assert_called_once()
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1

    def test_get_current_price_returns_float_or_none(
        self, mock_config, mock_secrets_manager, mock_alpaca_clients
    ):
        """Test that get_current_price returns float or None."""
        data_client, trading_client = mock_alpaca_clients
        provider = UnifiedDataProvider(enable_real_time=False, config=mock_config)

        # Mock the REST API method
        with patch.object(provider, "get_current_price_rest", return_value=150.75):
            result = provider.get_current_price("AAPL")
            assert result == 150.75
            assert isinstance(result, float)

    def test_get_latest_quote_returns_bid_ask_tuple(
        self, mock_config, mock_secrets_manager, mock_alpaca_clients
    ):
        """Test that get_latest_quote returns (bid, ask) tuple."""
        data_client, trading_client = mock_alpaca_clients
        provider = UnifiedDataProvider(config=mock_config)

        # Mock quote response
        mock_quote = Mock()
        mock_quote.bid_price = 150.50
        mock_quote.ask_price = 150.75

        mock_response = {"AAPL": mock_quote}
        data_client.get_stock_latest_quote.return_value = mock_response

        bid, ask = provider.get_latest_quote("AAPL")

        assert bid == 150.50
        assert ask == 150.75
        assert isinstance(bid, float)
        assert isinstance(ask, float)

    def test_get_account_info_returns_dict_or_none(
        self, mock_config, mock_secrets_manager, mock_alpaca_clients
    ):
        """Test that get_account_info returns dict or None."""
        data_client, trading_client = mock_alpaca_clients
        provider = UnifiedDataProvider(config=mock_config)

        # Mock account response
        mock_account = Mock()
        mock_account.model_dump.return_value = {
            "account_number": "123456",
            "equity": 10000.0,
            "cash": 5000.0,
        }
        trading_client.get_account.return_value = mock_account

        result = provider.get_account_info()

        assert isinstance(result, dict)
        assert result["account_number"] == "123456"
        assert result["equity"] == 10000.0

    def test_get_positions_returns_list_of_dicts(
        self, mock_config, mock_secrets_manager, mock_alpaca_clients
    ):
        """Test that get_positions returns list of dicts."""
        data_client, trading_client = mock_alpaca_clients
        provider = UnifiedDataProvider(config=mock_config)

        # Mock positions response
        mock_position = Mock()
        mock_position.model_dump.return_value = {
            "symbol": "AAPL",
            "qty": "10",
            "market_value": "1500.0",
        }
        trading_client.get_all_positions.return_value = [mock_position]

        result = provider.get_positions()

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], dict)
        assert result[0]["symbol"] == "AAPL"

    def test_cache_functionality(self, mock_config, mock_secrets_manager, mock_alpaca_clients):
        """Test cache clear and stats functionality."""
        data_client, trading_client = mock_alpaca_clients
        provider = UnifiedDataProvider(config=mock_config)

        # Add some cache entries
        import time

        provider.cache[("AAPL", "1y", "1d")] = (time.time(), pd.DataFrame())
        provider.cache[("GOOGL", "1y", "1d")] = (time.time(), pd.DataFrame())

        # Test cache stats
        stats = provider.get_cache_stats()
        assert stats["cache_size"] == 2
        assert stats["cache_duration"] == 3600
        assert stats["paper_trading"] is True

        # Test cache clear
        provider.clear_cache()
        assert len(provider.cache) == 0

        stats_after_clear = provider.get_cache_stats()
        assert stats_after_clear["cache_size"] == 0

    def test_error_handling_preserves_interface(
        self, mock_config, mock_secrets_manager, mock_alpaca_clients
    ):
        """Test that errors are handled gracefully and interface is preserved."""
        data_client, trading_client = mock_alpaca_clients
        provider = UnifiedDataProvider(config=mock_config)

        # Mock API error with a specific exception type that's handled
        data_client.get_stock_bars.side_effect = ValueError("API Error")

        # Should return empty DataFrame on error, not raise
        result = provider.get_data("AAPL")
        assert isinstance(result, pd.DataFrame)
        assert result.empty

        # Reset the side effect for the quote test
        data_client.get_stock_bars.side_effect = None

        # Mock quote error with a specific exception type that's handled
        data_client.get_stock_latest_quote.side_effect = ValueError("Quote Error")

        # Should return (0.0, 0.0) on error
        bid, ask = provider.get_latest_quote("AAPL")
        assert bid == 0.0
        assert ask == 0.0

    def test_historical_data_date_range_interface(
        self, mock_config, mock_secrets_manager, mock_alpaca_clients
    ):
        """Test the get_historical_data interface with date ranges."""
        data_client, trading_client = mock_alpaca_clients
        provider = UnifiedDataProvider(config=mock_config)

        # Mock successful response
        mock_bar = Mock()
        mock_bar.open = 100.0
        mock_bar.timestamp = datetime.now()

        mock_response = Mock()
        mock_response.AAPL = [mock_bar]
        data_client.get_stock_bars.return_value = mock_response

        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()

        result = provider.get_historical_data("AAPL", start_date, end_date)

        assert isinstance(result, list)
        data_client.get_stock_bars.assert_called_once()
