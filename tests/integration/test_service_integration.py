"""
Integration tests for the refactored service-based architecture.

Tests service composition and interaction with real-world scenarios
using mocked external dependencies.
"""

import asyncio
from datetime import datetime
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from the_alchemiser.core.models import AccountModel, BarModel
from the_alchemiser.core.services import (
    CacheManager,
    ConfigService,
    MarketDataClient,
    SecretsService,
    TradingClientService,
)
from the_alchemiser.core.services.account_service import AccountService
from the_alchemiser.core.services.error_handling import handle_service_errors
from the_alchemiser.core.services.price_service import ModernPriceFetchingService


class TestServiceIntegration:
    """Integration tests for service composition and interaction."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration service."""
        config = Mock()
        config.data.cache_duration = 3600
        config.alpaca.paper_endpoint = "https://paper-api.alpaca.markets"
        config.alpaca.endpoint = "https://api.alpaca.markets"
        return config

    @pytest.fixture
    def mock_secrets(self):
        """Mock secrets service."""
        with patch("the_alchemiser.core.services.secrets_service.SecretsManager") as mock_sm:
            mock_instance = Mock()
            mock_instance.get_alpaca_keys.return_value = ("test_api_key", "test_secret_key")
            mock_sm.return_value = mock_instance
            yield mock_instance

    def test_full_service_stack_initialization(self, mock_config, mock_secrets):
        """Test full service stack initialization and dependency injection."""
        # Initialize core services
        config_service = ConfigService(mock_config)
        secrets_service = SecretsService()

        # Get credentials
        api_key, secret_key = secrets_service.get_alpaca_credentials(True)

        # Initialize dependent services
        market_data_client = MarketDataClient(api_key, secret_key)
        trading_client_service = TradingClientService(api_key, secret_key, True)

        # Initialize cache manager
        cache_manager = CacheManager[pd.DataFrame](
            maxsize=100, default_ttl=config_service.cache_duration
        )

        # Initialize account service
        account_service = AccountService(
            trading_client_service, api_key, secret_key, config_service.get_endpoint(True)
        )

        # Verify all services are properly initialized
        assert config_service.cache_duration == 3600
        assert api_key == "test_api_key"
        assert market_data_client.api_key == "test_api_key"
        assert trading_client_service.paper_trading is True
        assert cache_manager.maxsize == 100
        assert account_service._trading_client_service == trading_client_service

    @patch("the_alchemiser.core.services.market_data_client.StockHistoricalDataClient")
    def test_cached_market_data_flow(self, mock_client_class, mock_config):
        """Test market data flow with caching integration."""
        # Setup cache
        cache = CacheManager[pd.DataFrame](maxsize=100, default_ttl=3600)

        # Mock market data client
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

        # First call - should hit API
        cache_key = "AAPL:1y:1d"
        df1 = market_data_client.get_historical_bars("AAPL", "1y", "1d")
        cache.set(cache_key, df1, "historical_data")

        # Verify API was called
        mock_client.get_stock_bars.assert_called_once()

        # Second call - should hit cache
        cached_df = cache.get(cache_key, "historical_data")
        assert cached_df is not None
        pd.testing.assert_frame_equal(df1, cached_df)

        # Verify cache statistics
        stats = cache.get_stats()
        assert stats["cache_size"] == 1
        assert "historical_data" in stats["type_breakdown"]

    @patch("the_alchemiser.core.services.trading_client_service.AlpacaTradingClient")
    def test_account_service_with_trading_client(self, mock_client_class):
        """Test account service integration with trading client."""
        # Mock trading client
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Mock account response
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

        # Mock positions response
        mock_positions = [
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

        # Initialize services
        trading_client_service = TradingClientService("test_key", "test_secret", True)
        trading_client_service.get_all_positions = Mock(return_value=mock_positions)

        account_service = AccountService(
            trading_client_service, "test_key", "test_secret", "https://paper-api.alpaca.markets"
        )

        # Test account info retrieval
        account = account_service.get_account_info()
        assert isinstance(account, AccountModel)
        assert account.account_id == "test123"
        assert account.equity == 10000.0

        # Test positions summary
        summary = account_service.get_positions_summary()
        assert summary["total_positions"] == 2
        assert summary["profitable_positions"] == 1
        assert summary["losing_positions"] == 1
        assert summary["total_unrealized_pnl"] == 0.0

        # Test profitable positions filtering
        profitable = account_service.get_profitable_positions()
        assert len(profitable) == 1
        assert profitable[0].symbol == "AAPL"

    @pytest.mark.asyncio
    async def test_modern_price_fetching_integration(self):
        """Test modern price fetching service integration."""
        # Mock market data client
        mock_market_data = Mock()
        mock_market_data.get_latest_quote.return_value = (150.25, 150.50)

        # Mock streaming service
        mock_streaming = Mock()
        mock_streaming.is_connected.return_value = True

        # Initialize price service
        price_service = ModernPriceFetchingService(mock_market_data, mock_streaming, timeout=5.0)

        # Test async price fetching
        price = await price_service.get_current_price_async("AAPL")
        assert price == 150.375  # Midpoint of bid/ask

        # Test multiple prices
        mock_market_data.get_latest_quote = Mock(
            side_effect=[
                (100.0, 100.25),  # AAPL
                (200.0, 200.50),  # GOOGL
            ]
        )

        prices = await price_service.get_multiple_prices_async(["AAPL", "GOOGL"])
        assert len(prices) == 2
        assert prices["AAPL"] == 100.125
        assert prices["GOOGL"] == 200.25

    def test_error_handling_integration(self):
        """Test error handling integration across services."""
        # Test error handling with mock service
        with patch("logging.getLogger") as mock_logger:
            mock_log = Mock()
            mock_logger.return_value = mock_log

            # Test service error handling
            @handle_service_errors(default_return=None)
            def failing_service_call():
                raise ConnectionError("Network timeout")

            result = failing_service_call()
            assert result is None

            # Verify error was logged
            mock_log.error.assert_called()

    def test_configuration_cascade(self, mock_config):
        """Test configuration cascading through service stack."""
        # Initialize config service
        config_service = ConfigService(mock_config)

        # Verify configuration values propagate correctly
        assert config_service.cache_duration == 3600
        assert config_service.get_endpoint(True) == "https://paper-api.alpaca.markets"
        assert config_service.get_endpoint(False) == "https://api.alpaca.markets"

        # Test cache configuration
        cache = CacheManager[str](
            maxsize=config_service.config.data.get("cache_max_size", 1000),
            default_ttl=config_service.cache_duration,
        )

        # Verify cache inherits configuration
        assert cache._default_ttl == 3600

    @patch("the_alchemiser.core.services.market_data_client.StockHistoricalDataClient")
    def test_data_model_conversion_flow(self, mock_client_class):
        """Test data flow and model conversion throughout the stack."""
        # Mock market data
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Create mock bar data
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

        # Test data flow
        market_data_client = MarketDataClient("test_key", "test_secret")
        df = market_data_client.get_historical_bars("AAPL", "1y", "1d")

        # Convert to domain model
        from the_alchemiser.core.models.market_data import dataframe_to_bars

        bars = dataframe_to_bars(df, "AAPL")

        assert len(bars) == 1
        bar_model = bars[0]
        assert isinstance(bar_model, BarModel)
        assert bar_model.symbol == "AAPL"
        assert bar_model.open == 100.0
        assert bar_model.is_valid_ohlc is True

        # Convert back to DataFrame
        from the_alchemiser.core.models.market_data import bars_to_dataframe

        df_converted = bars_to_dataframe(bars)

        # Verify round-trip conversion
        pd.testing.assert_frame_equal(
            df.reset_index(drop=True), df_converted.reset_index(drop=True)
        )

    def test_service_composition_patterns(self, mock_config, mock_secrets):
        """Test various service composition patterns."""
        # Initialize base services
        config_service = ConfigService(mock_config)
        secrets_service = SecretsService()
        api_key, secret_key = secrets_service.get_alpaca_credentials(True)

        # Composition pattern 1: Direct dependency injection
        trading_client = TradingClientService(api_key, secret_key, True)
        account_service = AccountService(
            trading_client, api_key, secret_key, config_service.get_endpoint(True)
        )

        # Composition pattern 2: Factory pattern
        def create_cache_manager(data_type: str) -> CacheManager:
            return CacheManager(
                maxsize=config_service.config.data.get("cache_max_size", 1000),
                default_ttl=config_service.cache_duration,
            )

        price_cache = create_cache_manager("prices")
        historical_cache = create_cache_manager("historical")

        # Verify different caches are independent
        price_cache.set("AAPL", 150.0, "current_price")
        historical_cache.set("AAPL", "historical_data", "bars")

        assert price_cache.get("AAPL", "current_price") == 150.0
        assert historical_cache.get("AAPL", "bars") == "historical_data"
        assert price_cache.get("AAPL", "bars") is None  # Cross-cache isolation

        # Composition pattern 3: Service registry pattern
        service_registry = {
            "config": config_service,
            "secrets": secrets_service,
            "trading_client": trading_client,
            "account": account_service,
            "price_cache": price_cache,
            "historical_cache": historical_cache,
        }

        # Verify registry provides centralized service access
        assert service_registry["config"].cache_duration == 3600
        assert service_registry["account"]._trading_client_service == trading_client

    def test_performance_characteristics(self):
        """Test performance characteristics of service operations."""
        # Test cache performance
        cache = CacheManager[str](maxsize=1000, default_ttl=3600)

        # Measure cache set/get performance
        import time

        start_time = time.time()

        for i in range(100):
            cache.set(f"key_{i}", f"value_{i}", "test_data")

        set_time = time.time() - start_time

        start_time = time.time()
        for i in range(100):
            value = cache.get(f"key_{i}", "test_data")
            assert value == f"value_{i}"

        get_time = time.time() - start_time

        # Verify reasonable performance (should be very fast)
        assert set_time < 1.0  # Less than 1 second for 100 sets
        assert get_time < 1.0  # Less than 1 second for 100 gets

        # Test cache statistics
        stats = cache.get_stats()
        assert stats["cache_size"] == 100
        assert stats["hit_rate"] > 0  # Should have some hits

    @pytest.mark.asyncio
    async def test_concurrent_service_operations(self):
        """Test concurrent service operations and thread safety."""
        # Test concurrent cache operations
        cache = CacheManager[str](maxsize=1000, default_ttl=3600)

        async def cache_worker(worker_id: int):
            for i in range(10):
                key = f"worker_{worker_id}_key_{i}"
                value = f"worker_{worker_id}_value_{i}"
                cache.set(key, value, "concurrent_test")

                # Verify immediate retrieval
                retrieved = cache.get(key, "concurrent_test")
                assert retrieved == value

        # Run multiple workers concurrently
        workers = [cache_worker(i) for i in range(5)]
        await asyncio.gather(*workers)

        # Verify all data was stored correctly
        stats = cache.get_stats()
        assert stats["cache_size"] == 50  # 5 workers * 10 items each

        # Verify data integrity
        for worker_id in range(5):
            for i in range(10):
                key = f"worker_{worker_id}_key_{i}"
                expected_value = f"worker_{worker_id}_value_{i}"
                actual_value = cache.get(key, "concurrent_test")
                assert actual_value == expected_value


if __name__ == "__main__":
    pytest.main(
        [
            __file__,
            "-v",
            "--cov=the_alchemiser.core.services",
            "--cov-report=term-missing",
        ]
    )
