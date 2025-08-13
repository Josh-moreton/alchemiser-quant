"""
Comprehensive unit tests for services layer.

Tests all service components with mocked dependencies and complete error scenarios.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from decimal import Decimal
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from the_alchemiser.services.enhanced.trading_service_manager import TradingServiceManager
from the_alchemiser.services.enhanced.order_service import OrderService
from the_alchemiser.services.enhanced.position_service import PositionService
from the_alchemiser.services.enhanced.account_service import AccountService
from the_alchemiser.services.enhanced.market_data_service import MarketDataService
from the_alchemiser.services.alpaca_manager import AlpacaManager
from the_alchemiser.services.cache_manager import CacheManager
from the_alchemiser.services.error_handling import TradingSystemErrorHandler
from the_alchemiser.services.exceptions import (
    TradingClientError,
    DataProviderError,
    ValidationError,
    ConfigurationError,
)


class TestTradingServiceManager:
    """Test the main trading service facade."""

    @pytest.fixture
    def mock_alpaca_manager(self, mocker):
        """Create a mocked AlpacaManager."""
        mock = mocker.Mock(spec=AlpacaManager)
        mock.paper_trading = True
        return mock

    @pytest.fixture
    def trading_service_manager(self, mock_alpaca_manager):
        """Create TradingServiceManager with mocked dependencies."""
        with patch(
            "the_alchemiser.services.enhanced.trading_service_manager.AlpacaManager"
        ) as mock_cls:
            mock_cls.return_value = mock_alpaca_manager
            return TradingServiceManager("test_api_key", "test_secret", paper=True)

    def test_initialization_paper_trading(self, trading_service_manager, mock_alpaca_manager):
        """Test TradingServiceManager initialization in paper mode."""
        assert trading_service_manager.paper_trading is True
        assert trading_service_manager.alpaca_manager == mock_alpaca_manager

    def test_initialization_live_trading(self, mocker):
        """Test TradingServiceManager initialization in live mode."""
        mock_alpaca = mocker.Mock(spec=AlpacaManager)
        mock_alpaca.paper_trading = False

        with patch(
            "the_alchemiser.services.enhanced.trading_service_manager.AlpacaManager"
        ) as mock_cls:
            mock_cls.return_value = mock_alpaca
            tsm = TradingServiceManager("test_api_key", "test_secret", paper=False)

        assert tsm.paper_trading is False

    def test_place_market_order(self, trading_service_manager, mock_alpaca_manager):
        """Test market order placement."""
        # Setup mock response
        mock_alpaca_manager.place_order.return_value = {
            "id": "order_123",
            "status": "new",
            "symbol": "AAPL",
            "qty": "100",
            "side": "buy",
        }

        result = trading_service_manager.place_market_order("AAPL", 100, "buy")

        assert result["id"] == "order_123"
        assert result["symbol"] == "AAPL"
        mock_alpaca_manager.place_order.assert_called_once()

    def test_place_limit_order(self, trading_service_manager, mock_alpaca_manager):
        """Test limit order placement."""
        mock_alpaca_manager.place_order.return_value = {
            "id": "order_456",
            "status": "new",
            "symbol": "TSLA",
            "qty": "50",
            "side": "sell",
            "limit_price": "250.00",
        }

        result = trading_service_manager.place_limit_order("TSLA", 50, "sell", Decimal("250.00"))

        assert result["id"] == "order_456"
        assert result["limit_price"] == "250.00"

    def test_get_account_info(self, trading_service_manager, mock_alpaca_manager):
        """Test account information retrieval."""
        mock_alpaca_manager.get_account.return_value = {
            "id": "account_123",
            "buying_power": "50000.00",
            "cash": "10000.00",
            "portfolio_value": "100000.00",
        }

        account_info = trading_service_manager.get_account_info()

        assert account_info["id"] == "account_123"
        assert account_info["buying_power"] == "50000.00"
        mock_alpaca_manager.get_account.assert_called_once()

    def test_get_positions(self, trading_service_manager, mock_alpaca_manager):
        """Test position retrieval."""
        mock_positions = [
            {"symbol": "AAPL", "qty": "100", "market_value": "15000.00", "unrealized_pl": "500.00"},
            {"symbol": "TSLA", "qty": "50", "market_value": "12500.00", "unrealized_pl": "-250.00"},
        ]
        mock_alpaca_manager.get_all_positions.return_value = mock_positions

        positions = trading_service_manager.get_all_positions()

        assert len(positions) == 2
        assert positions[0]["symbol"] == "AAPL"
        assert positions[1]["symbol"] == "TSLA"

    def test_error_handling(self, trading_service_manager, mock_alpaca_manager):
        """Test error handling and propagation."""
        mock_alpaca_manager.place_order.side_effect = TradingClientError("API Error")

        with pytest.raises(TradingClientError):
            trading_service_manager.place_market_order("AAPL", 100, "buy")

    def test_smart_order_execution(self, trading_service_manager, mock_alpaca_manager):
        """Test smart order execution with validation."""
        # Mock account validation
        mock_alpaca_manager.get_account.return_value = {
            "buying_power": "50000.00",
            "cash": "10000.00",
        }

        # Mock successful order
        mock_alpaca_manager.place_order.return_value = {
            "id": "smart_order_123",
            "status": "accepted",
        }

        result = trading_service_manager.execute_smart_order("AAPL", 100, "buy")

        assert result["id"] == "smart_order_123"
        # Should call account validation first
        mock_alpaca_manager.get_account.assert_called()


class TestOrderService:
    """Test the order service implementation."""

    @pytest.fixture
    def mock_alpaca_manager(self, mocker):
        """Create mocked AlpacaManager for OrderService."""
        return mocker.Mock(spec=AlpacaManager)

    @pytest.fixture
    def order_service(self, mock_alpaca_manager):
        """Create OrderService with mocked dependencies."""
        return OrderService(mock_alpaca_manager)

    def test_place_market_order_success(self, order_service, mock_alpaca_manager):
        """Test successful market order placement."""
        mock_alpaca_manager.place_order.return_value = {
            "id": "test_order_123",
            "status": "new",
            "symbol": "AAPL",
        }

        result = order_service.place_market_order("AAPL", Decimal("100"), "buy")

        assert result["id"] == "test_order_123"
        mock_alpaca_manager.place_order.assert_called_once()

    def test_place_limit_order_success(self, order_service, mock_alpaca_manager):
        """Test successful limit order placement."""
        mock_alpaca_manager.place_order.return_value = {
            "id": "limit_order_456",
            "status": "new",
            "limit_price": "150.00",
        }

        result = order_service.place_limit_order("AAPL", Decimal("100"), "buy", Decimal("150.00"))

        assert result["id"] == "limit_order_456"
        assert result["limit_price"] == "150.00"

    def test_place_stop_order_success(self, order_service, mock_alpaca_manager):
        """Test successful stop order placement."""
        mock_alpaca_manager.place_order.return_value = {
            "id": "stop_order_789",
            "status": "new",
            "stop_price": "140.00",
        }

        result = order_service.place_stop_order("AAPL", Decimal("100"), "sell", Decimal("140.00"))

        assert result["id"] == "stop_order_789"
        assert result["stop_price"] == "140.00"

    def test_order_validation_invalid_quantity(self, order_service):
        """Test order validation with invalid quantity."""
        with pytest.raises(ValidationError):
            order_service.place_market_order("AAPL", Decimal("0"), "buy")

        with pytest.raises(ValidationError):
            order_service.place_market_order("AAPL", Decimal("-10"), "buy")

    def test_order_validation_invalid_side(self, order_service):
        """Test order validation with invalid side."""
        with pytest.raises(ValidationError):
            order_service.place_market_order("AAPL", Decimal("100"), "invalid_side")

    def test_get_order_by_id(self, order_service, mock_alpaca_manager):
        """Test order retrieval by ID."""
        mock_alpaca_manager.get_order.return_value = {
            "id": "order_123",
            "symbol": "AAPL",
            "status": "filled",
        }

        order = order_service.get_order("order_123")

        assert order["id"] == "order_123"
        assert order["status"] == "filled"

    def test_cancel_order(self, order_service, mock_alpaca_manager):
        """Test order cancellation."""
        mock_alpaca_manager.cancel_order.return_value = True

        result = order_service.cancel_order("order_123")

        assert result is True
        mock_alpaca_manager.cancel_order.assert_called_once_with("order_123")

    def test_get_open_orders(self, order_service, mock_alpaca_manager):
        """Test retrieval of open orders."""
        mock_orders = [
            {"id": "order_1", "status": "new"},
            {"id": "order_2", "status": "partially_filled"},
        ]
        mock_alpaca_manager.get_orders.return_value = mock_orders

        orders = order_service.get_open_orders()

        assert len(orders) == 2
        assert orders[0]["status"] == "new"

    def test_order_error_handling(self, order_service, mock_alpaca_manager):
        """Test error handling in order operations."""
        mock_alpaca_manager.place_order.side_effect = TradingClientError("Order rejected")

        with pytest.raises(TradingClientError):
            order_service.place_market_order("AAPL", Decimal("100"), "buy")


class TestPositionService:
    """Test the position service implementation."""

    @pytest.fixture
    def mock_alpaca_manager(self, mocker):
        """Create mocked AlpacaManager for PositionService."""
        return mocker.Mock(spec=AlpacaManager)

    @pytest.fixture
    def position_service(self, mock_alpaca_manager):
        """Create PositionService with mocked dependencies."""
        return PositionService(mock_alpaca_manager)

    def test_get_all_positions(self, position_service, mock_alpaca_manager):
        """Test retrieval of all positions."""
        mock_positions = [
            {
                "symbol": "AAPL",
                "qty": "100",
                "market_value": "15000.00",
                "unrealized_pl": "500.00",
                "side": "long",
            },
            {
                "symbol": "TSLA",
                "qty": "50",
                "market_value": "12500.00",
                "unrealized_pl": "-250.00",
                "side": "long",
            },
        ]
        mock_alpaca_manager.get_all_positions.return_value = mock_positions

        positions = position_service.get_all_positions()

        assert len(positions) == 2
        assert positions[0]["symbol"] == "AAPL"
        assert positions[1]["symbol"] == "TSLA"

    def test_get_position_by_symbol(self, position_service, mock_alpaca_manager):
        """Test retrieval of position by symbol."""
        mock_position = {"symbol": "AAPL", "qty": "100", "market_value": "15000.00"}
        mock_alpaca_manager.get_position.return_value = mock_position

        position = position_service.get_position("AAPL")

        assert position["symbol"] == "AAPL"
        assert position["qty"] == "100"

    def test_close_position(self, position_service, mock_alpaca_manager):
        """Test position closure."""
        mock_alpaca_manager.close_position.return_value = {
            "id": "close_order_123",
            "status": "filled",
        }

        result = position_service.close_position("AAPL")

        assert result["id"] == "close_order_123"
        mock_alpaca_manager.close_position.assert_called_once_with("AAPL")

    def test_close_all_positions(self, position_service, mock_alpaca_manager):
        """Test closure of all positions."""
        mock_alpaca_manager.close_all_positions.return_value = [
            {"symbol": "AAPL", "status": "closed"},
            {"symbol": "TSLA", "status": "closed"},
        ]

        results = position_service.close_all_positions()

        assert len(results) == 2
        assert all(result["status"] == "closed" for result in results)

    def test_calculate_portfolio_value(self, position_service, mock_alpaca_manager):
        """Test portfolio value calculation."""
        mock_positions = [
            {"symbol": "AAPL", "market_value": "15000.00"},
            {"symbol": "TSLA", "market_value": "12500.00"},
        ]
        mock_alpaca_manager.get_all_positions.return_value = mock_positions
        mock_alpaca_manager.get_account.return_value = {"cash": "5000.00"}

        portfolio_value = position_service.calculate_portfolio_value()

        assert portfolio_value == Decimal("32500.00")  # 15000 + 12500 + 5000

    def test_validate_position_quantity(self, position_service, mock_alpaca_manager):
        """Test position quantity validation."""
        mock_alpaca_manager.get_position.return_value = {"symbol": "AAPL", "qty": "100"}

        # Valid sell quantity
        assert position_service.validate_sell_quantity("AAPL", Decimal("50")) is True

        # Invalid sell quantity (exceeds position)
        assert position_service.validate_sell_quantity("AAPL", Decimal("150")) is False

    def test_position_not_found(self, position_service, mock_alpaca_manager):
        """Test handling of non-existent positions."""
        mock_alpaca_manager.get_position.side_effect = DataProviderError("Position not found")

        with pytest.raises(DataProviderError):
            position_service.get_position("NONEXISTENT")


class TestAccountService:
    """Test the account service implementation."""

    @pytest.fixture
    def mock_alpaca_manager(self, mocker):
        """Create mocked AlpacaManager for AccountService."""
        return mocker.Mock(spec=AlpacaManager)

    @pytest.fixture
    def account_service(self, mock_alpaca_manager):
        """Create AccountService with mocked dependencies."""
        return AccountService(mock_alpaca_manager)

    def test_get_account_info(self, account_service, mock_alpaca_manager):
        """Test account information retrieval."""
        mock_account = {
            "id": "account_123",
            "buying_power": "50000.00",
            "cash": "10000.00",
            "portfolio_value": "100000.00",
            "equity": "90000.00",
        }
        mock_alpaca_manager.get_account.return_value = mock_account

        account_info = account_service.get_account_info()

        assert account_info["id"] == "account_123"
        assert account_info["buying_power"] == "50000.00"

    def test_get_buying_power(self, account_service, mock_alpaca_manager):
        """Test buying power retrieval."""
        mock_account = {"buying_power": "25000.00"}
        mock_alpaca_manager.get_account.return_value = mock_account

        buying_power = account_service.get_buying_power()

        assert buying_power == Decimal("25000.00")

    def test_get_cash_balance(self, account_service, mock_alpaca_manager):
        """Test cash balance retrieval."""
        mock_account = {"cash": "15000.00"}
        mock_alpaca_manager.get_account.return_value = mock_account

        cash = account_service.get_cash_balance()

        assert cash == Decimal("15000.00")

    def test_validate_buying_power_sufficient(self, account_service, mock_alpaca_manager):
        """Test buying power validation with sufficient funds."""
        mock_account = {"buying_power": "50000.00"}
        mock_alpaca_manager.get_account.return_value = mock_account

        is_valid = account_service.validate_buying_power(Decimal("25000.00"))

        assert is_valid is True

    def test_validate_buying_power_insufficient(self, account_service, mock_alpaca_manager):
        """Test buying power validation with insufficient funds."""
        mock_account = {"buying_power": "10000.00"}
        mock_alpaca_manager.get_account.return_value = mock_account

        is_valid = account_service.validate_buying_power(Decimal("25000.00"))

        assert is_valid is False

    def test_get_portfolio_value(self, account_service, mock_alpaca_manager):
        """Test portfolio value retrieval."""
        mock_account = {"portfolio_value": "150000.00"}
        mock_alpaca_manager.get_account.return_value = mock_account

        portfolio_value = account_service.get_portfolio_value()

        assert portfolio_value == Decimal("150000.00")

    def test_account_error_handling(self, account_service, mock_alpaca_manager):
        """Test error handling in account operations."""
        mock_alpaca_manager.get_account.side_effect = TradingClientError("Account access error")

        with pytest.raises(TradingClientError):
            account_service.get_account_info()


class TestMarketDataService:
    """Test the market data service implementation."""

    @pytest.fixture
    def mock_alpaca_manager(self, mocker):
        """Create mocked AlpacaManager for MarketDataService."""
        return mocker.Mock(spec=AlpacaManager)

    @pytest.fixture
    def market_data_service(self, mock_alpaca_manager):
        """Create MarketDataService with mocked dependencies."""
        return MarketDataService(mock_alpaca_manager)

    def test_get_current_price(self, market_data_service, mock_alpaca_manager):
        """Test current price retrieval."""
        mock_alpaca_manager.get_latest_quote.return_value = {
            "symbol": "AAPL",
            "bid": 149.95,
            "ask": 150.05,
        }

        price = market_data_service.get_current_price("AAPL")

        assert price == Decimal("150.00")  # Mid price

    def test_get_quote(self, market_data_service, mock_alpaca_manager):
        """Test quote retrieval."""
        mock_quote = {
            "symbol": "AAPL",
            "bid": 149.95,
            "ask": 150.05,
            "bid_size": 100,
            "ask_size": 200,
        }
        mock_alpaca_manager.get_latest_quote.return_value = mock_quote

        quote = market_data_service.get_quote("AAPL")

        assert quote["symbol"] == "AAPL"
        assert quote["bid"] == 149.95

    def test_get_historical_bars(self, market_data_service, mock_alpaca_manager):
        """Test historical bars retrieval."""
        mock_bars = [
            {
                "timestamp": "2024-01-01T09:30:00Z",
                "open": 148.00,
                "high": 151.00,
                "low": 147.50,
                "close": 150.00,
                "volume": 1000000,
            }
        ]
        mock_alpaca_manager.get_bars.return_value = mock_bars

        bars = market_data_service.get_historical_bars("AAPL", "1Day", limit=10)

        assert len(bars) == 1
        assert bars[0]["symbol"] == "AAPL"  # Should be added by service

    def test_get_multiple_quotes(self, market_data_service, mock_alpaca_manager):
        """Test multiple quotes retrieval."""
        mock_quotes = {
            "AAPL": {"bid": 149.95, "ask": 150.05},
            "TSLA": {"bid": 248.50, "ask": 249.50},
        }
        mock_alpaca_manager.get_latest_quotes.return_value = mock_quotes

        quotes = market_data_service.get_multiple_quotes(["AAPL", "TSLA"])

        assert len(quotes) == 2
        assert "AAPL" in quotes
        assert "TSLA" in quotes

    def test_market_data_caching(self, market_data_service, mock_alpaca_manager):
        """Test market data caching functionality."""
        mock_quote = {"symbol": "AAPL", "bid": 149.95, "ask": 150.05}
        mock_alpaca_manager.get_latest_quote.return_value = mock_quote

        # First call should hit the API
        quote1 = market_data_service.get_quote("AAPL")

        # Second call should use cache (within TTL)
        quote2 = market_data_service.get_quote("AAPL")

        assert quote1 == quote2
        # Should only call API once due to caching
        mock_alpaca_manager.get_latest_quote.assert_called_once()

    def test_market_data_error_handling(self, market_data_service, mock_alpaca_manager):
        """Test error handling in market data operations."""
        mock_alpaca_manager.get_latest_quote.side_effect = DataProviderError("Data unavailable")

        with pytest.raises(DataProviderError):
            market_data_service.get_quote("INVALID_SYMBOL")


class TestCacheManager:
    """Test the cache manager implementation."""

    @pytest.fixture
    def cache_manager(self):
        """Create CacheManager instance."""
        return CacheManager(max_size=100, default_ttl=300)

    def test_cache_set_and_get(self, cache_manager):
        """Test basic cache set and get operations."""
        cache_manager.set("test_key", "test_value")

        value = cache_manager.get("test_key")
        assert value == "test_value"

    def test_cache_miss(self, cache_manager):
        """Test cache miss behavior."""
        value = cache_manager.get("nonexistent_key")
        assert value is None

    def test_cache_ttl_expiration(self, cache_manager):
        """Test cache TTL expiration."""
        # Set with very short TTL
        cache_manager.set("short_ttl_key", "value", ttl=0.1)

        # Should be available immediately
        assert cache_manager.get("short_ttl_key") == "value"

        # Wait for expiration
        import time

        time.sleep(0.2)

        # Should be expired
        assert cache_manager.get("short_ttl_key") is None

    def test_cache_max_size_eviction(self, cache_manager):
        """Test cache eviction when max size is reached."""
        # Fill cache to capacity
        for i in range(100):
            cache_manager.set(f"key_{i}", f"value_{i}")

        # Add one more item (should trigger eviction)
        cache_manager.set("new_key", "new_value")

        # Cache should still be at max size
        assert len(cache_manager._cache) <= 100

    def test_cache_clear(self, cache_manager):
        """Test cache clear operation."""
        cache_manager.set("key1", "value1")
        cache_manager.set("key2", "value2")

        cache_manager.clear()

        assert cache_manager.get("key1") is None
        assert cache_manager.get("key2") is None

    def test_cache_statistics(self, cache_manager):
        """Test cache statistics tracking."""
        # Generate some hits and misses
        cache_manager.set("test_key", "test_value")

        cache_manager.get("test_key")  # Hit
        cache_manager.get("missing_key")  # Miss

        stats = cache_manager.get_stats()

        assert stats["hits"] >= 1
        assert stats["misses"] >= 1
        assert "hit_rate" in stats

    def test_cache_delete(self, cache_manager):
        """Test cache item deletion."""
        cache_manager.set("delete_me", "value")
        assert cache_manager.get("delete_me") == "value"

        cache_manager.delete("delete_me")
        assert cache_manager.get("delete_me") is None


class TestErrorHandling:
    """Test error handling and recovery mechanisms."""

    @pytest.fixture
    def error_handler(self):
        """Create error handler instance."""
        return TradingSystemErrorHandler()

    def test_error_categorization(self, error_handler):
        """Test error categorization functionality."""
        # Trading error
        trading_error = TradingClientError("Order rejected")
        category = error_handler.categorize_error(trading_error)
        assert category == "TRADING"

        # Data error
        data_error = DataProviderError("API timeout")
        category = error_handler.categorize_error(data_error)
        assert category == "DATA"

        # Configuration error
        config_error = ConfigurationError("Missing API key")
        category = error_handler.categorize_error(config_error)
        assert category == "CONFIGURATION"

    def test_error_logging_and_reporting(self, error_handler, mocker):
        """Test error logging and reporting."""
        mock_logger = mocker.patch("the_alchemiser.services.error_handling.logger")

        error = TradingClientError("Test error")

        error_handler.handle_error(
            error=error,
            component="TestComponent",
            context="test_context",
            additional_data={"symbol": "AAPL"},
        )

        # Should log the error
        mock_logger.error.assert_called()

    def test_error_recovery_suggestions(self, error_handler):
        """Test error recovery suggestions."""
        trading_error = TradingClientError("Insufficient buying power")
        suggestions = error_handler.get_recovery_suggestions(trading_error)

        assert isinstance(suggestions, list)
        assert len(suggestions) > 0

    def test_error_notification(self, error_handler, mocker):
        """Test error notification functionality."""
        mock_email = mocker.patch("the_alchemiser.services.error_handling.send_error_notification")

        critical_error = TradingClientError("Critical system failure")

        error_handler.handle_critical_error(
            error=critical_error, component="TradingEngine", context="order_execution"
        )

        # Should trigger email notification for critical errors
        mock_email.assert_called()


class TestServiceIntegration:
    """Test integration between different services."""

    @pytest.fixture
    def mock_services(self, mocker):
        """Create mocked service dependencies."""
        return {
            "alpaca_manager": mocker.Mock(spec=AlpacaManager),
            "cache_manager": mocker.Mock(spec=CacheManager),
            "error_handler": mocker.Mock(spec=TradingSystemErrorHandler),
        }

    def test_service_coordination(self, mock_services):
        """Test coordination between services."""
        # Setup mock responses
        mock_services["alpaca_manager"].get_account.return_value = {"buying_power": "50000.00"}
        mock_services["alpaca_manager"].place_order.return_value = {"id": "order_123"}

        # Create services
        account_service = AccountService(mock_services["alpaca_manager"])
        order_service = OrderService(mock_services["alpaca_manager"])

        # Test workflow: Check buying power, then place order
        buying_power = account_service.get_buying_power()
        assert buying_power == Decimal("50000.00")

        order = order_service.place_market_order("AAPL", Decimal("100"), "buy")
        assert order["id"] == "order_123"

    def test_error_propagation_between_services(self, mock_services):
        """Test error propagation between services."""
        # Setup error in underlying manager
        mock_services["alpaca_manager"].get_account.side_effect = TradingClientError("API Error")

        account_service = AccountService(mock_services["alpaca_manager"])

        # Error should propagate up
        with pytest.raises(TradingClientError):
            account_service.get_account_info()

    def test_cache_integration_with_services(self, mock_services):
        """Test cache integration with services."""
        # Mock cache behavior
        mock_services["cache_manager"].get.return_value = None  # Cache miss
        mock_services["cache_manager"].set.return_value = True

        # Mock API response
        mock_services["alpaca_manager"].get_latest_quote.return_value = {
            "symbol": "AAPL",
            "bid": 149.95,
            "ask": 150.05,
        }

        market_data_service = MarketDataService(mock_services["alpaca_manager"])

        # First call should hit API and cache result
        quote = market_data_service.get_quote("AAPL")

        assert quote["symbol"] == "AAPL"
        mock_services["alpaca_manager"].get_latest_quote.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
