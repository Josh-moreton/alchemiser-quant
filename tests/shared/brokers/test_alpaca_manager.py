"""Business Unit: shared | Status: current.

Comprehensive test suite for AlpacaManager singleton facade.

Tests cover:
- Singleton behavior and instance management
- Credential security (hashing, no exposure)
- Thread safety and concurrent access
- Service delegation correctness
- Cleanup coordination
- Deprecation warnings
"""

from __future__ import annotations

import threading
import time
import warnings
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager, create_alpaca_manager


@pytest.fixture(autouse=True)
def cleanup_instances():
    """Clean up AlpacaManager instances before and after each test."""
    # Clean up before test
    AlpacaManager.cleanup_all_instances()
    yield
    # Clean up after test
    AlpacaManager.cleanup_all_instances()


class TestSingletonBehavior:
    """Test singleton pattern implementation in AlpacaManager."""

    @patch("the_alchemiser.shared.brokers.alpaca_manager.create_trading_client")
    @patch("the_alchemiser.shared.brokers.alpaca_manager.create_data_client")
    @patch("the_alchemiser.shared.services.websocket_manager.WebSocketConnectionManager")
    @patch("the_alchemiser.shared.services.market_data_service.MarketDataService")
    def test_same_credentials_return_same_instance(
        self, mock_mds, mock_ws, mock_data_client, mock_trading_client
    ):
        """Test that same credentials return the same instance."""
        # Arrange
        mock_trading_client.return_value = Mock()
        mock_data_client.return_value = Mock()
        mock_ws.return_value = Mock()
        mock_mds.return_value = Mock()

        # Act
        manager1 = AlpacaManager("test_api", "test_secret", paper=True)
        manager2 = AlpacaManager("test_api", "test_secret", paper=True)

        # Assert
        assert manager1 is manager2, "Same credentials should return same instance"

    @patch("the_alchemiser.shared.brokers.alpaca_manager.create_trading_client")
    @patch("the_alchemiser.shared.brokers.alpaca_manager.create_data_client")
    @patch("the_alchemiser.shared.services.websocket_manager.WebSocketConnectionManager")
    @patch("the_alchemiser.shared.services.market_data_service.MarketDataService")
    def test_different_credentials_return_different_instances(
        self, mock_mds, mock_ws, mock_data_client, mock_trading_client
    ):
        """Test that different credentials return different instances."""
        # Arrange
        mock_trading_client.return_value = Mock()
        mock_data_client.return_value = Mock()
        mock_ws.return_value = Mock()
        mock_mds.return_value = Mock()

        # Act
        manager1 = AlpacaManager("api1", "secret1", paper=True)
        manager2 = AlpacaManager("api2", "secret2", paper=True)

        # Assert
        assert manager1 is not manager2, "Different credentials should return different instances"

    @patch("the_alchemiser.shared.brokers.alpaca_manager.create_trading_client")
    @patch("the_alchemiser.shared.brokers.alpaca_manager.create_data_client")
    @patch("the_alchemiser.shared.services.websocket_manager.WebSocketConnectionManager")
    @patch("the_alchemiser.shared.services.market_data_service.MarketDataService")
    def test_different_paper_mode_return_different_instances(
        self, mock_mds, mock_ws, mock_data_client, mock_trading_client
    ):
        """Test that different paper mode returns different instances."""
        # Arrange
        mock_trading_client.return_value = Mock()
        mock_data_client.return_value = Mock()
        mock_ws.return_value = Mock()
        mock_mds.return_value = Mock()

        # Act
        manager1 = AlpacaManager("test_api", "test_secret", paper=True)
        manager2 = AlpacaManager("test_api", "test_secret", paper=False)

        # Assert
        assert manager1 is not manager2, "Different paper mode should return different instances"

    @patch("the_alchemiser.shared.brokers.alpaca_manager.create_trading_client")
    @patch("the_alchemiser.shared.brokers.alpaca_manager.create_data_client")
    @patch("the_alchemiser.shared.services.websocket_manager.WebSocketConnectionManager")
    @patch("the_alchemiser.shared.services.market_data_service.MarketDataService")
    def test_different_base_url_return_different_instances(
        self, mock_mds, mock_ws, mock_data_client, mock_trading_client
    ):
        """Test that different base URLs return different instances."""
        # Arrange
        mock_trading_client.return_value = Mock()
        mock_data_client.return_value = Mock()
        mock_ws.return_value = Mock()
        mock_mds.return_value = Mock()

        # Act
        manager1 = AlpacaManager("test_api", "test_secret", paper=True, base_url="url1")
        manager2 = AlpacaManager("test_api", "test_secret", paper=True, base_url="url2")

        # Assert
        assert manager1 is not manager2, "Different base URL should return different instances"

    @patch("the_alchemiser.shared.brokers.alpaca_manager.create_trading_client")
    @patch("the_alchemiser.shared.brokers.alpaca_manager.create_data_client")
    @patch("the_alchemiser.shared.services.websocket_manager.WebSocketConnectionManager")
    @patch("the_alchemiser.shared.services.market_data_service.MarketDataService")
    def test_cleanup_resets_singleton_state(
        self, mock_mds, mock_ws, mock_data_client, mock_trading_client
    ):
        """Test that cleanup allows new instances to be created."""
        # Arrange
        mock_trading_client.return_value = Mock()
        mock_data_client.return_value = Mock()
        mock_ws.return_value = Mock()
        mock_mds.return_value = Mock()

        # Act
        manager1 = AlpacaManager("test_api", "test_secret", paper=True)
        instance_id1 = id(manager1)

        AlpacaManager.cleanup_all_instances()

        manager2 = AlpacaManager("test_api", "test_secret", paper=True)
        instance_id2 = id(manager2)

        # Assert
        assert instance_id1 != instance_id2, "Cleanup should allow new instance creation"


class TestCredentialSecurity:
    """Test credential handling security in AlpacaManager."""

    @patch("the_alchemiser.shared.brokers.alpaca_manager.create_trading_client")
    @patch("the_alchemiser.shared.brokers.alpaca_manager.create_data_client")
    @patch("the_alchemiser.shared.services.websocket_manager.WebSocketConnectionManager")
    @patch("the_alchemiser.shared.services.market_data_service.MarketDataService")
    def test_credentials_are_hashed_in_dictionary_keys(
        self, mock_mds, mock_ws, mock_data_client, mock_trading_client
    ):
        """Test that credentials are hashed (using PBKDF2) for dictionary keys."""
        # Arrange
        mock_trading_client.return_value = Mock()
        mock_data_client.return_value = Mock()
        mock_ws.return_value = Mock()
        mock_mds.return_value = Mock()

        api_key = "test_api_key"
        secret_key = "test_secret_key"

        # Act
        manager = AlpacaManager(api_key, secret_key, paper=True)

        # Assert - check that instance is stored with a hashed key
        # With PBKDF2, we can't predict the exact hash due to random salt,
        # but we can verify that:
        # 1. The manager is stored in _instances
        # 2. The hash is a 64-character hex string (32 bytes * 2)
        assert len(AlpacaManager._instances) == 1
        stored_hash = list(AlpacaManager._instances.keys())[0]
        assert len(stored_hash) == 64  # PBKDF2 with 32-byte output = 64 hex chars
        assert all(c in "0123456789abcdef" for c in stored_hash)
        assert AlpacaManager._instances[stored_hash] is manager

        # Verify that the same credentials return the same hash (salt is reused)
        credentials_hash = AlpacaManager._hash_credentials(api_key, secret_key, paper=True)
        assert credentials_hash == stored_hash

    @patch("the_alchemiser.shared.brokers.alpaca_manager.create_trading_client")
    @patch("the_alchemiser.shared.brokers.alpaca_manager.create_data_client")
    @patch("the_alchemiser.shared.services.websocket_manager.WebSocketConnectionManager")
    @patch("the_alchemiser.shared.services.market_data_service.MarketDataService")
    def test_api_key_property_emits_deprecation_warning(
        self, mock_mds, mock_ws, mock_data_client, mock_trading_client
    ):
        """Test that accessing api_key property emits deprecation warning."""
        # Arrange
        mock_trading_client.return_value = Mock()
        mock_data_client.return_value = Mock()
        mock_ws.return_value = Mock()
        mock_mds.return_value = Mock()

        manager = AlpacaManager("test_api", "test_secret", paper=True)

        # Act & Assert
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _ = manager.api_key

            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "api_key property is deprecated" in str(w[0].message)

    @patch("the_alchemiser.shared.brokers.alpaca_manager.create_trading_client")
    @patch("the_alchemiser.shared.brokers.alpaca_manager.create_data_client")
    @patch("the_alchemiser.shared.services.websocket_manager.WebSocketConnectionManager")
    @patch("the_alchemiser.shared.services.market_data_service.MarketDataService")
    def test_secret_key_property_emits_deprecation_warning(
        self, mock_mds, mock_ws, mock_data_client, mock_trading_client
    ):
        """Test that accessing secret_key property emits deprecation warning."""
        # Arrange
        mock_trading_client.return_value = Mock()
        mock_data_client.return_value = Mock()
        mock_ws.return_value = Mock()
        mock_mds.return_value = Mock()

        manager = AlpacaManager("test_api", "test_secret", paper=True)

        # Act & Assert
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _ = manager.secret_key

            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "secret_key property is deprecated" in str(w[0].message)

    @patch("the_alchemiser.shared.brokers.alpaca_manager.create_trading_client")
    @patch("the_alchemiser.shared.brokers.alpaca_manager.create_data_client")
    @patch("the_alchemiser.shared.services.websocket_manager.WebSocketConnectionManager")
    @patch("the_alchemiser.shared.services.market_data_service.MarketDataService")
    def test_credentials_hash_logged_correctly(
        self, mock_mds, mock_ws, mock_data_client, mock_trading_client
    ):
        """Test that credentials hash is logged instead of raw credentials."""
        # Arrange
        mock_trading_client.return_value = Mock()
        mock_data_client.return_value = Mock()
        mock_ws.return_value = Mock()
        mock_mds.return_value = Mock()

        # Act
        with patch("the_alchemiser.shared.brokers.alpaca_manager.logger") as mock_logger:
            manager = AlpacaManager("test_api", "test_secret", paper=True)

            # Assert - check that debug log was called with credentials_hash
            mock_logger.debug.assert_called()
            call_kwargs = mock_logger.debug.call_args[1]
            assert "credentials_hash" in call_kwargs
            assert len(call_kwargs["credentials_hash"]) == 16  # First 16 chars of hash

    @patch("the_alchemiser.shared.brokers.alpaca_manager.create_trading_client")
    @patch("the_alchemiser.shared.brokers.alpaca_manager.create_data_client")
    @patch("the_alchemiser.shared.services.websocket_manager.WebSocketConnectionManager")
    @patch("the_alchemiser.shared.services.market_data_service.MarketDataService")
    def test_repr_does_not_expose_credentials(
        self, mock_mds, mock_ws, mock_data_client, mock_trading_client
    ):
        """Test that __repr__ does not expose credentials."""
        # Arrange
        mock_trading_client.return_value = Mock()
        mock_data_client.return_value = Mock()
        mock_ws.return_value = Mock()
        mock_mds.return_value = Mock()

        manager = AlpacaManager("secret_api", "secret_key", paper=True)

        # Act
        repr_str = repr(manager)

        # Assert
        assert "secret_api" not in repr_str
        assert "secret_key" not in repr_str
        assert "AlpacaManager" in repr_str


class TestThreadSafety:
    """Test thread safety of AlpacaManager singleton."""

    @patch("the_alchemiser.shared.brokers.alpaca_manager.create_trading_client")
    @patch("the_alchemiser.shared.brokers.alpaca_manager.create_data_client")
    @patch("the_alchemiser.shared.services.websocket_manager.WebSocketConnectionManager")
    @patch("the_alchemiser.shared.services.market_data_service.MarketDataService")
    def test_concurrent_instance_creation_is_thread_safe(
        self, mock_mds, mock_ws, mock_data_client, mock_trading_client
    ):
        """Test that concurrent calls to __new__ return same instance."""
        # Arrange
        mock_trading_client.return_value = Mock()
        mock_data_client.return_value = Mock()
        mock_ws.return_value = Mock()
        mock_mds.return_value = Mock()

        instances = []

        def create_manager():
            manager = AlpacaManager("test_api", "test_secret", paper=True)
            instances.append(manager)

        # Act - create managers from 10 concurrent threads
        threads = [threading.Thread(target=create_manager) for _ in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Assert - all threads got the same instance
        assert len(set(id(instance) for instance in instances)) == 1

    @patch("the_alchemiser.shared.brokers.alpaca_manager.create_trading_client")
    @patch("the_alchemiser.shared.brokers.alpaca_manager.create_data_client")
    @patch("the_alchemiser.shared.services.websocket_manager.WebSocketConnectionManager")
    @patch("the_alchemiser.shared.services.market_data_service.MarketDataService")
    def test_cleanup_coordination_with_event(
        self, mock_mds, mock_ws, mock_data_client, mock_trading_client
    ):
        """Test that cleanup coordination uses Event properly."""
        # Arrange
        mock_trading_client.return_value = Mock()
        mock_data_client.return_value = Mock()
        mock_ws.return_value = Mock()
        mock_mds.return_value = Mock()

        manager = AlpacaManager("test_api", "test_secret", paper=True)

        # Act - simulate cleanup in progress
        AlpacaManager._cleanup_in_progress = True
        AlpacaManager._cleanup_event.clear()

        # Start thread that will wait for cleanup
        instances = []

        def delayed_create():
            time.sleep(0.1)  # Brief delay
            AlpacaManager._cleanup_in_progress = False
            AlpacaManager._cleanup_event.set()

        def create_during_cleanup():
            # This should wait for cleanup
            manager2 = AlpacaManager("test_api", "test_secret", paper=True)
            instances.append(manager2)

        cleanup_thread = threading.Thread(target=delayed_create)
        create_thread = threading.Thread(target=create_during_cleanup)

        cleanup_thread.start()
        create_thread.start()

        cleanup_thread.join()
        create_thread.join()

        # Assert - manager was created after cleanup
        assert len(instances) == 1

    @patch("the_alchemiser.shared.brokers.alpaca_manager.create_trading_client")
    @patch("the_alchemiser.shared.brokers.alpaca_manager.create_data_client")
    @patch("the_alchemiser.shared.services.websocket_manager.WebSocketConnectionManager")
    @patch("the_alchemiser.shared.services.market_data_service.MarketDataService")
    def test_multiple_threads_get_same_instance(
        self, mock_mds, mock_ws, mock_data_client, mock_trading_client
    ):
        """Test that multiple threads get the same singleton instance."""
        # Arrange
        mock_trading_client.return_value = Mock()
        mock_data_client.return_value = Mock()
        mock_ws.return_value = Mock()
        mock_mds.return_value = Mock()

        results = []

        def get_manager():
            manager = AlpacaManager("test_api", "test_secret", paper=True)
            results.append(id(manager))

        # Act
        threads = [threading.Thread(target=get_manager) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Assert
        assert len(set(results)) == 1, "All threads should get same instance"


class TestDelegation:
    """Test that AlpacaManager properly delegates to services."""

    @patch("the_alchemiser.shared.brokers.alpaca_manager.create_trading_client")
    @patch("the_alchemiser.shared.brokers.alpaca_manager.create_data_client")
    @patch("the_alchemiser.shared.services.websocket_manager.WebSocketConnectionManager")
    @patch("the_alchemiser.shared.services.market_data_service.MarketDataService")
    def test_get_current_price_delegates_to_market_data_service(
        self, mock_mds, mock_ws, mock_data_client, mock_trading_client
    ):
        """Test that get_current_price delegates to MarketDataService."""
        # Arrange
        mock_trading_client.return_value = Mock()
        mock_data_client.return_value = Mock()
        mock_ws.return_value = Mock()
        mock_service = Mock()
        mock_service.get_current_price.return_value = 123.45
        mock_mds.return_value = mock_service

        manager = AlpacaManager("test_api", "test_secret", paper=True)

        # Act
        price = manager.get_current_price("AAPL")

        # Assert
        mock_service.get_current_price.assert_called_once_with("AAPL")
        assert isinstance(price, Decimal)
        assert price == Decimal("123.45")

    @patch("the_alchemiser.shared.brokers.alpaca_manager.create_trading_client")
    @patch("the_alchemiser.shared.brokers.alpaca_manager.create_data_client")
    @patch("the_alchemiser.shared.services.websocket_manager.WebSocketConnectionManager")
    @patch("the_alchemiser.shared.services.market_data_service.MarketDataService")
    def test_get_current_price_handles_decimal_return(
        self, mock_mds, mock_ws, mock_data_client, mock_trading_client
    ):
        """Test that get_current_price handles Decimal returns without conversion."""
        # Arrange
        mock_trading_client.return_value = Mock()
        mock_data_client.return_value = Mock()
        mock_ws.return_value = Mock()
        mock_service = Mock()
        mock_service.get_current_price.return_value = Decimal("123.45")
        mock_mds.return_value = mock_service

        manager = AlpacaManager("test_api", "test_secret", paper=True)

        # Act
        price = manager.get_current_price("AAPL")

        # Assert
        assert isinstance(price, Decimal)
        assert price == Decimal("123.45")

    @patch("the_alchemiser.shared.brokers.alpaca_manager.create_trading_client")
    @patch("the_alchemiser.shared.brokers.alpaca_manager.create_data_client")
    @patch("the_alchemiser.shared.services.websocket_manager.WebSocketConnectionManager")
    @patch("the_alchemiser.shared.services.market_data_service.MarketDataService")
    def test_get_current_price_returns_none_for_none(
        self, mock_mds, mock_ws, mock_data_client, mock_trading_client
    ):
        """Test that get_current_price returns None when service returns None."""
        # Arrange
        mock_trading_client.return_value = Mock()
        mock_data_client.return_value = Mock()
        mock_ws.return_value = Mock()
        mock_service = Mock()
        mock_service.get_current_price.return_value = None
        mock_mds.return_value = mock_service

        manager = AlpacaManager("test_api", "test_secret", paper=True)

        # Act
        price = manager.get_current_price("INVALID")

        # Assert
        assert price is None

    @patch("the_alchemiser.shared.brokers.alpaca_manager.create_trading_client")
    @patch("the_alchemiser.shared.brokers.alpaca_manager.create_data_client")
    @patch("the_alchemiser.shared.services.websocket_manager.WebSocketConnectionManager")
    @patch("the_alchemiser.shared.services.market_data_service.MarketDataService")
    def test_get_current_prices_delegates_to_market_data_service(
        self, mock_mds, mock_ws, mock_data_client, mock_trading_client
    ):
        """Test that get_current_prices delegates to MarketDataService."""
        # Arrange
        mock_trading_client.return_value = Mock()
        mock_data_client.return_value = Mock()
        mock_ws.return_value = Mock()
        mock_service = Mock()
        mock_service.get_current_prices.return_value = {"AAPL": 150.0, "TSLA": 200.0}
        mock_mds.return_value = mock_service

        manager = AlpacaManager("test_api", "test_secret", paper=True)

        # Act
        prices = manager.get_current_prices(["AAPL", "TSLA"])

        # Assert
        mock_service.get_current_prices.assert_called_once_with(["AAPL", "TSLA"])
        assert prices == {"AAPL": 150.0, "TSLA": 200.0}

    @patch("the_alchemiser.shared.brokers.alpaca_manager.create_trading_client")
    @patch("the_alchemiser.shared.brokers.alpaca_manager.create_data_client")
    @patch("the_alchemiser.shared.services.websocket_manager.WebSocketConnectionManager")
    @patch("the_alchemiser.shared.services.market_data_service.MarketDataService")
    def test_is_paper_trading_property(
        self, mock_mds, mock_ws, mock_data_client, mock_trading_client
    ):
        """Test is_paper_trading property."""
        # Arrange
        mock_trading_client.return_value = Mock()
        mock_data_client.return_value = Mock()
        mock_ws.return_value = Mock()
        mock_mds.return_value = Mock()

        # Act - paper mode
        manager_paper = AlpacaManager("test_api", "test_secret", paper=True)
        # Act - live mode
        manager_live = AlpacaManager("test_api2", "test_secret2", paper=False)

        # Assert
        assert manager_paper.is_paper_trading is True
        assert manager_live.is_paper_trading is False


class TestCleanup:
    """Test cleanup functionality."""

    @patch("the_alchemiser.shared.brokers.alpaca_manager.create_trading_client")
    @patch("the_alchemiser.shared.brokers.alpaca_manager.create_data_client")
    @patch("the_alchemiser.shared.services.websocket_manager.WebSocketConnectionManager")
    @patch("the_alchemiser.shared.services.market_data_service.MarketDataService")
    def test_cleanup_all_instances_clears_all(
        self, mock_mds, mock_ws, mock_data_client, mock_trading_client
    ):
        """Test that cleanup_all_instances clears all instances."""
        # Arrange
        mock_trading_client.return_value = Mock()
        mock_data_client.return_value = Mock()
        mock_ws_instance = Mock()
        mock_ws.return_value = mock_ws_instance
        mock_mds.return_value = Mock()

        manager1 = AlpacaManager("api1", "secret1", paper=True)
        manager2 = AlpacaManager("api2", "secret2", paper=True)

        # Act
        AlpacaManager.cleanup_all_instances()

        # Assert
        assert len(AlpacaManager._instances) == 0
        # Verify cleanup was called on WebSocket managers
        assert mock_ws_instance.cleanup.call_count == 2

    @patch("the_alchemiser.shared.brokers.alpaca_manager.create_trading_client")
    @patch("the_alchemiser.shared.brokers.alpaca_manager.create_data_client")
    @patch("the_alchemiser.shared.services.websocket_manager.WebSocketConnectionManager")
    @patch("the_alchemiser.shared.services.market_data_service.MarketDataService")
    def test_cleanup_errors_isolated_per_instance(
        self, mock_mds, mock_ws, mock_data_client, mock_trading_client
    ):
        """Test that cleanup errors in one instance don't affect others."""
        # Arrange
        mock_trading_client.return_value = Mock()
        mock_data_client.return_value = Mock()

        # First manager's cleanup will fail
        mock_ws_fail = Mock()
        mock_ws_fail.cleanup.side_effect = Exception("Cleanup failed")

        # Second manager's cleanup will succeed
        mock_ws_ok = Mock()

        mock_ws.side_effect = [mock_ws_fail, mock_ws_ok]
        mock_mds.return_value = Mock()

        manager1 = AlpacaManager("api1", "secret1", paper=True)
        manager2 = AlpacaManager("api2", "secret2", paper=True)

        # Act - should not raise even though one cleanup fails
        with patch("the_alchemiser.shared.brokers.alpaca_manager.logger") as mock_logger:
            AlpacaManager.cleanup_all_instances()

            # Assert - error was logged
            mock_logger.error.assert_called()

    @patch("the_alchemiser.shared.brokers.alpaca_manager.create_trading_client")
    @patch("the_alchemiser.shared.brokers.alpaca_manager.create_data_client")
    @patch("the_alchemiser.shared.services.websocket_manager.WebSocketConnectionManager")
    @patch("the_alchemiser.shared.services.market_data_service.MarketDataService")
    def test_post_cleanup_instance_creation_works(
        self, mock_mds, mock_ws, mock_data_client, mock_trading_client
    ):
        """Test that new instances can be created after cleanup."""
        # Arrange
        mock_trading_client.return_value = Mock()
        mock_data_client.return_value = Mock()
        mock_ws.return_value = Mock()
        mock_mds.return_value = Mock()

        # Act
        manager1 = AlpacaManager("test_api", "test_secret", paper=True)
        id1 = id(manager1)

        AlpacaManager.cleanup_all_instances()

        manager2 = AlpacaManager("test_api", "test_secret", paper=True)
        id2 = id(manager2)

        # Assert
        assert id1 != id2, "New instance should be created after cleanup"


class TestFactoryFunction:
    """Test the create_alpaca_manager factory function."""

    @patch("the_alchemiser.shared.brokers.alpaca_manager.create_trading_client")
    @patch("the_alchemiser.shared.brokers.alpaca_manager.create_data_client")
    @patch("the_alchemiser.shared.services.websocket_manager.WebSocketConnectionManager")
    @patch("the_alchemiser.shared.services.market_data_service.MarketDataService")
    def test_factory_creates_alpaca_manager(
        self, mock_mds, mock_ws, mock_data_client, mock_trading_client
    ):
        """Test that factory function creates AlpacaManager instance."""
        # Arrange
        mock_trading_client.return_value = Mock()
        mock_data_client.return_value = Mock()
        mock_ws.return_value = Mock()
        mock_mds.return_value = Mock()

        # Act
        manager = create_alpaca_manager("test_api", "test_secret", paper=True)

        # Assert
        assert isinstance(manager, AlpacaManager)
        assert manager.is_paper_trading is True

    @patch("the_alchemiser.shared.brokers.alpaca_manager.create_trading_client")
    @patch("the_alchemiser.shared.brokers.alpaca_manager.create_data_client")
    @patch("the_alchemiser.shared.services.websocket_manager.WebSocketConnectionManager")
    @patch("the_alchemiser.shared.services.market_data_service.MarketDataService")
    def test_factory_respects_singleton(
        self, mock_mds, mock_ws, mock_data_client, mock_trading_client
    ):
        """Test that factory function respects singleton pattern."""
        # Arrange
        mock_trading_client.return_value = Mock()
        mock_data_client.return_value = Mock()
        mock_ws.return_value = Mock()
        mock_mds.return_value = Mock()

        # Act
        manager1 = create_alpaca_manager("test_api", "test_secret", paper=True)
        manager2 = create_alpaca_manager("test_api", "test_secret", paper=True)

        # Assert
        assert manager1 is manager2
