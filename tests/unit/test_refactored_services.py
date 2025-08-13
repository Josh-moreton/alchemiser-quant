"""
Unit tests for the refactored service-based architecture.

Tests all services with mocked dependencies to ensure proper functionality
without external API calls.
"""

from datetime import datetime
from unittest.mock import Mock, patch

import pandas as pd
import pytest
from pytest import approx

from tests.conftest import ABS_TOL, REL_TOL
from the_alchemiser.domain.models import (
    AccountModel,
    BarModel,
    PositionModel,
    StrategySignalModel,
)
from the_alchemiser.services.account_service import AccountService
from the_alchemiser.services.cache_manager import CacheManager
from the_alchemiser.services.config_service import ConfigService
from the_alchemiser.services.error_handling import (
    ErrorHandler,
    ServiceMetrics,
    handle_service_errors,
)
from the_alchemiser.services.exceptions import (
    ConfigurationError,
    MarketDataError,
)
from the_alchemiser.services.market_data_client import MarketDataClient
from the_alchemiser.services.secrets_service import SecretsService
from the_alchemiser.services.trading_client_service import TradingClientService


class TestConfigService:
    """Test configuration service functionality."""

    def test_config_service_initialization(self):
        """Test config service initialization with mock config."""
        with patch("the_alchemiser.services.config_service.load_settings") as mock_load:
            mock_config = Mock()
            mock_config.data.cache_duration = 1800
            mock_config.alpaca.paper_endpoint = "https://paper-api.alpaca.markets"
            mock_config.alpaca.endpoint = "https://api.alpaca.markets"
            mock_load.return_value = mock_config

            service = ConfigService()

            assert service.config == mock_config
            assert service.cache_duration == 1800
            assert service.paper_endpoint == "https://paper-api.alpaca.markets"
            assert service.live_endpoint == "https://api.alpaca.markets"

    def test_get_endpoint_paper_trading(self):
        """Test endpoint selection for paper trading."""
        mock_config = Mock()
        mock_config.alpaca.paper_endpoint = "https://paper-api.alpaca.markets"
        mock_config.alpaca.endpoint = "https://api.alpaca.markets"

        service = ConfigService(mock_config)
        assert service.get_endpoint(True) == "https://paper-api.alpaca.markets"
        assert service.get_endpoint(False) == "https://api.alpaca.markets"


class TestSecretsService:
    """Test secrets service functionality."""

    @patch("the_alchemiser.core.services.secrets_service.SecretsManager")
    def test_secrets_service_success(self, mock_secrets_manager):
        """Test successful credential retrieval."""
        mock_manager = Mock()
        mock_manager.get_alpaca_keys.return_value = ("test_key", "test_secret")
        mock_secrets_manager.return_value = mock_manager

        service = SecretsService()
        api_key, secret_key = service.get_alpaca_credentials(True)

        assert api_key == "test_key"
        assert secret_key == "test_secret"
        mock_manager.get_alpaca_keys.assert_called_once_with(paper_trading=True)

    @patch("the_alchemiser.core.services.secrets_service.SecretsManager")
    def test_secrets_service_missing_credentials(self, mock_secrets_manager):
        """Test error when credentials are missing."""
        mock_manager = Mock()
        mock_manager.get_alpaca_keys.return_value = (None, None)
        mock_secrets_manager.return_value = mock_manager

        service = SecretsService()

        with pytest.raises(ConfigurationError, match="Alpaca API keys not found"):
            service.get_alpaca_credentials(True)


class TestMarketDataClient:
    """Test market data client functionality."""

    def test_market_data_client_initialization(self):
        """Test market data client initialization."""
        client = MarketDataClient("test_key", "test_secret")
        assert client.api_key == "test_key"
        assert client.secret_key == "test_secret"

    @patch("the_alchemiser.core.services.market_data_client.StockHistoricalDataClient")
    def test_get_historical_bars_success(self, mock_client_class):
        """Test successful historical data retrieval."""
        # Mock the Alpaca client
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Mock bar response
        mock_bar = Mock()
        mock_bar.open = 100.0
        mock_bar.high = 105.0
        mock_bar.low = 99.0
        mock_bar.close = 103.0
        mock_bar.volume = 1000
        mock_bar.timestamp = datetime.now()

        mock_bars = Mock()
        mock_bars.AAPL = [mock_bar]
        mock_client.get_stock_bars.return_value = mock_bars

        client = MarketDataClient("test_key", "test_secret")
        df = client.get_historical_bars("AAPL", "1y", "1d")

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert df.iloc[0]["Open"] == approx(100.0, rel=REL_TOL, abs=ABS_TOL)
        assert df.iloc[0]["Close"] == approx(103.0, rel=REL_TOL, abs=ABS_TOL)

    @patch("the_alchemiser.core.services.market_data_client.StockHistoricalDataClient")
    def test_get_latest_quote_success(self, mock_client_class):
        """Test successful quote retrieval."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_quote = Mock()
        mock_quote.bid_price = 100.50
        mock_quote.ask_price = 100.75

        mock_response = {"AAPL": mock_quote}
        mock_client.get_stock_latest_quote.return_value = mock_response

        client = MarketDataClient("test_key", "test_secret")
        bid, ask = client.get_latest_quote("AAPL")

        assert bid == approx(100.50, rel=REL_TOL, abs=ABS_TOL)
        assert ask == approx(100.75, rel=REL_TOL, abs=ABS_TOL)


class TestTradingClientService:
    """Test trading client service functionality."""

    @patch("the_alchemiser.core.services.trading_client_service.AlpacaTradingClient")
    def test_trading_client_initialization(self, mock_client_class):
        """Test trading client initialization."""
        service = TradingClientService("test_key", "test_secret", True)
        assert service.api_key == "test_key"
        assert service.secret_key == "test_secret"
        assert service.paper_trading is True

    @patch("the_alchemiser.core.services.trading_client_service.AlpacaTradingClient")
    def test_get_account_info_success(self, mock_client_class):
        """Test successful account info retrieval."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_account = Mock()
        mock_account.model_dump.return_value = {
            "account_id": "test123",
            "equity": "10000.0",
            "cash": "5000.0",
            "buying_power": "8000.0",
            "day_trades_remaining": 3,
            "portfolio_value": "10000.0",
            "last_equity": "9900.0",
            "daytrading_buying_power": "8000.0",
            "regt_buying_power": "8000.0",
            "status": "ACTIVE",
        }
        mock_client.get_account.return_value = mock_account

        service = TradingClientService("test_key", "test_secret", True)
        account_info = service.get_account_info()

        assert account_info is not None
        assert account_info["account_id"] == "test123"
        assert account_info["equity"] == "10000.0"


class TestCacheManager:
    """Test cache manager functionality."""

    def test_cache_manager_initialization(self):
        """Test cache manager initialization."""
        cache = CacheManager[str](maxsize=100, default_ttl=300)
        assert cache.maxsize == 100
        assert cache._default_ttl == 300

    def test_cache_set_and_get(self):
        """Test cache set and get operations."""
        cache = CacheManager[str](maxsize=100, default_ttl=3600)

        cache.set("test_key", "test_value", "test_type")
        result = cache.get("test_key", "test_type")

        assert result == "test_value"

    def test_cache_expiry(self):
        """Test cache expiry functionality."""
        cache = CacheManager[str](maxsize=100, default_ttl=1)

        cache.set("test_key", "test_value", "test_type")

        # Immediately should be available
        result = cache.get("test_key", "test_type")
        assert result == "test_value"

        # Mock time passage
        import time

        original_time = time.time
        time.time = lambda: original_time() + 2  # 2 seconds later

        try:
            result = cache.get("test_key", "test_type")
            assert result is None  # Should be expired
        finally:
            time.time = original_time

    def test_cache_stats(self):
        """Test cache statistics."""
        cache = CacheManager[str](maxsize=100, default_ttl=3600)

        cache.set("key1", "value1", "type1")
        cache.set("key2", "value2", "type2")

        stats = cache.get_stats()
        assert stats["cache_size"] == 2
        assert stats["max_size"] == 100
        assert "type1" in stats["type_breakdown"]
        assert "type2" in stats["type_breakdown"]


class TestAccountService:
    """Test account service functionality."""

    def test_account_service_initialization(self):
        """Test account service initialization."""
        mock_trading_service = Mock()
        service = AccountService(
            mock_trading_service, "test_key", "test_secret", "https://api.alpaca.markets"
        )
        assert service._trading_client_service == mock_trading_service

    def test_get_account_info_model(self):
        """Test getting account info as typed model."""
        mock_trading_service = Mock()
        mock_trading_service.get_account_info.return_value = {
            "account_id": "test123",
            "equity": "10000.0",
            "cash": "5000.0",
            "buying_power": "8000.0",
            "day_trades_remaining": 3,
            "portfolio_value": "10000.0",
            "last_equity": "9900.0",
            "daytrading_buying_power": "8000.0",
            "regt_buying_power": "8000.0",
            "status": "ACTIVE",
        }

        service = AccountService(
            mock_trading_service, "test_key", "test_secret", "https://api.alpaca.markets"
        )

        account = service.get_account_info()
        assert isinstance(account, AccountModel)
        assert account.account_id == "test123"
        assert account.equity == approx(10000.0, rel=REL_TOL, abs=ABS_TOL)

    def test_get_positions_summary(self):
        """Test positions summary calculation."""
        mock_trading_service = Mock()
        mock_trading_service.get_all_positions.return_value = [
            {
                "symbol": "AAPL",
                "qty": "10",
                "side": "long",
                "market_value": "1500.0",
                "cost_basis": "1400.0",
                "unrealized_pl": "100.0",
                "unrealized_plpc": "0.071",
                "current_price": "150.0",
            },
            {
                "symbol": "GOOGL",
                "qty": "5",
                "side": "long",
                "market_value": "500.0",
                "cost_basis": "600.0",
                "unrealized_pl": "-100.0",
                "unrealized_plpc": "-0.167",
                "current_price": "100.0",
            },
        ]

        service = AccountService(
            mock_trading_service, "test_key", "test_secret", "https://api.alpaca.markets"
        )

        summary = service.get_positions_summary()
        assert summary["total_positions"] == 2
        assert summary["profitable_positions"] == 1
        assert summary["losing_positions"] == 1
        assert summary["total_unrealized_pnl"] == approx(0.0, rel=REL_TOL, abs=ABS_TOL)  # 100 - 100


class TestErrorHandling:
    """Test error handling utilities."""

    def test_error_handler_log_and_raise(self):
        """Test error handler log and raise functionality."""
        with patch("logging.getLogger") as mock_logger:
            mock_log = Mock()
            mock_logger.return_value = mock_log

            handler = ErrorHandler(mock_log)

            with pytest.raises(MarketDataError, match="Test error"):
                handler.log_and_raise(
                    MarketDataError, "Test error", {"symbol": "AAPL"}, ValueError("Original error")
                )

            mock_log.error.assert_called()

    def test_service_error_decorator(self):
        """Test service error decorator."""

        @handle_service_errors(default_return="error_result")
        def test_function():
            raise ConnectionError("Network error")

        result = test_function()
        assert result == "error_result"

    def test_service_metrics(self):
        """Test service metrics collection."""
        metrics = ServiceMetrics()

        metrics.record_call("test_service.test_method")
        metrics.record_error("test_service.test_method", "ConnectionError")

        result = metrics.get_metrics()
        assert result["call_counts"]["test_service.test_method"] == 1
        assert result["error_counts"]["test_service.test_method:ConnectionError"] == 1


class TestDomainModels:
    """Test domain model functionality."""

    def test_account_model_creation(self):
        """Test account model creation and conversion."""
        account_data = {
            "account_id": "test123",
            "equity": "10000.0",
            "cash": "5000.0",
            "buying_power": "8000.0",
            "day_trades_remaining": 3,
            "portfolio_value": "10000.0",
            "last_equity": "9900.0",
            "daytrading_buying_power": "8000.0",
            "regt_buying_power": "8000.0",
            "status": "ACTIVE",
        }

        model = AccountModel.from_dict(account_data)
        assert model.account_id == "test123"
        assert model.equity == approx(10000.0, rel=REL_TOL, abs=ABS_TOL)
        assert model.status == "ACTIVE"

        # Test conversion back to dict
        converted = model.to_dict()
        assert converted["account_id"] == "test123"
        assert converted["equity"] == approx(10000.0, rel=REL_TOL, abs=ABS_TOL)

    def test_position_model_properties(self):
        """Test position model properties."""
        position_data = {
            "symbol": "AAPL",
            "qty": "10",
            "side": "long",
            "market_value": "1500.0",
            "cost_basis": "1400.0",
            "unrealized_pl": "100.0",
            "unrealized_plpc": "0.071",
            "current_price": "150.0",
        }

        model = PositionModel.from_dict(position_data)
        assert model.is_profitable is True
        assert model.is_long is True
        assert model.shares_count == 10
        assert model.percentage_return == approx(7.1, rel=REL_TOL, abs=ABS_TOL)

    def test_bar_model_validation(self):
        """Test bar model OHLC validation."""
        bar_data = {
            "symbol": "AAPL",
            "timestamp": "2023-01-01T00:00:00Z",
            "open": 100.0,
            "high": 105.0,
            "low": 95.0,
            "close": 103.0,
            "volume": 1000,
        }

        model = BarModel.from_dict(bar_data)
        assert model.is_valid_ohlc is True
        assert model.symbol == "AAPL"
        assert model.open == approx(100.0, rel=REL_TOL, abs=ABS_TOL)

    def test_strategy_signal_model(self):
        """Test strategy signal model."""
        signal_data = {
            "symbol": "AAPL",
            "action": "BUY",
            "confidence": 0.85,
            "reasoning": "Strong upward trend",
            "allocation_percentage": 10.0,
        }

        model = StrategySignalModel.from_dict(signal_data)
        assert model.is_buy_signal is True
        assert model.is_high_confidence is True
        assert model.confidence_level == "HIGH"


@pytest.fixture
def mock_config():
    """Fixture providing mock configuration."""
    config = Mock()
    config.data.cache_duration = 3600
    config.alpaca.paper_endpoint = "https://paper-api.alpaca.markets"
    config.alpaca.endpoint = "https://api.alpaca.markets"
    return config


@pytest.fixture
def mock_secrets_manager():
    """Fixture providing mock secrets manager."""
    with patch("the_alchemiser.core.services.secrets_service.SecretsManager") as mock_sm:
        mock_instance = Mock()
        mock_instance.get_alpaca_keys.return_value = ("test_api_key", "test_secret_key")
        mock_sm.return_value = mock_instance
        yield mock_instance


class TestIntegration:
    """Integration tests for service composition."""

    def test_service_composition(self, mock_config, mock_secrets_manager):
        """Test that services work together correctly."""
        # Initialize all services
        config_service = ConfigService(mock_config)
        secrets_service = SecretsService()

        api_key, secret_key = secrets_service.get_alpaca_credentials(True)

        market_data_client = MarketDataClient(api_key, secret_key)
        trading_client_service = TradingClientService(api_key, secret_key, True)

        # Verify services are properly initialized
        assert config_service.cache_duration == 3600
        assert api_key == "test_api_key"
        assert market_data_client.api_key == "test_api_key"
        assert trading_client_service.paper_trading is True

    @patch("the_alchemiser.core.services.market_data_client.StockHistoricalDataClient")
    def test_cache_integration(self, mock_client_class, mock_config):
        """Test cache integration with market data client."""
        cache = CacheManager[pd.DataFrame](maxsize=100, default_ttl=3600)

        # Mock successful data fetch
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_bar = Mock()
        mock_bar.open = 100.0
        mock_bar.high = 105.0
        mock_bar.low = 99.0
        mock_bar.close = 103.0
        mock_bar.volume = 1000
        mock_bar.timestamp = datetime.now()

        mock_bars = Mock()
        mock_bars.AAPL = [mock_bar]
        mock_client.get_stock_bars.return_value = mock_bars

        market_data_client = MarketDataClient("test_key", "test_secret")

        # First call - should fetch from API
        df1 = market_data_client.get_historical_bars("AAPL", "1y", "1d")
        cache.set("AAPL:1y:1d", df1, "historical_data")

        # Second call - should return from cache
        cached_df = cache.get("AAPL:1y:1d", "historical_data")

        assert cached_df is not None
        pd.testing.assert_frame_equal(df1, cached_df)


if __name__ == "__main__":
    # Run tests with coverage
    pytest.main(
        [
            __file__,
            "-v",
            "--cov=the_alchemiser.core.services",
            "--cov=the_alchemiser.core.models",
            "--cov-report=term-missing",
            "--cov-report=html",
        ]
    )
