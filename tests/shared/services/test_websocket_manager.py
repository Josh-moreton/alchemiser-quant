"""Tests for WebSocket Connection Manager.

Business Unit: shared | Status: current.

Comprehensive tests for the WebSocketConnectionManager class including:
- Singleton behavior with credential hashing
- Reference counting correctness
- Thread safety under concurrent access
- Service lifecycle management
- Error handling and recovery
- Timeout protection
- Cleanup scenarios
"""

from __future__ import annotations

import threading
import time
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from the_alchemiser.shared.errors.exceptions import WebSocketError
from the_alchemiser.shared.services.websocket_manager import WebSocketConnectionManager

if TYPE_CHECKING:
    pass


class TestWebSocketConnectionManagerSingleton:
    """Test singleton pattern with credential hashing."""

    def test_singleton_same_credentials_returns_same_instance(self):
        """Test that same credentials return the same instance."""
        manager1 = WebSocketConnectionManager("key1", "secret1", paper_trading=True)
        manager2 = WebSocketConnectionManager("key1", "secret1", paper_trading=True)

        assert manager1 is manager2

    def test_singleton_different_credentials_returns_different_instances(self):
        """Test that different credentials return different instances."""
        manager1 = WebSocketConnectionManager("key1", "secret1", paper_trading=True)
        manager2 = WebSocketConnectionManager("key2", "secret2", paper_trading=True)

        assert manager1 is not manager2

    def test_singleton_different_paper_trading_returns_different_instances(self):
        """Test that same credentials but different paper_trading flag returns different instances."""
        manager1 = WebSocketConnectionManager("key1", "secret1", paper_trading=True)
        manager2 = WebSocketConnectionManager("key1", "secret1", paper_trading=False)

        assert manager1 is not manager2

    def test_credentials_are_hashed_not_stored_plaintext(self):
        """Test that credentials are hashed (using PBKDF2) for dictionary keys."""
        api_key = "test_key"
        secret_key = "test_secret"
        paper_trading = True

        manager = WebSocketConnectionManager(api_key, secret_key, paper_trading=paper_trading)

        # With PBKDF2, we can't predict the exact hash due to random salt,
        # but we can verify that:
        # 1. The hash is a 64-character hex string (32 bytes * 2)
        # 2. The same credentials return the same hash (salt is reused)
        assert len(manager._credentials_hash) == 64  # PBKDF2 with 32-byte output
        assert all(c in "0123456789abcdef" for c in manager._credentials_hash)

        # Check that instance keys in the class are hashed
        assert manager._credentials_hash in WebSocketConnectionManager._instances

        # Verify that the same credentials return the same hash (salt is reused)
        credentials_hash = WebSocketConnectionManager._hash_credentials(
            api_key, secret_key, paper_trading=paper_trading
        )
        assert credentials_hash == manager._credentials_hash

    def test_hash_credentials_static_method(self):
        """Test the static hash_credentials method produces consistent PBKDF2 hashes."""
        api_key = "test_key"
        secret_key = "test_secret"
        paper_trading = True

        # First call creates a salt
        result1 = WebSocketConnectionManager._hash_credentials(
            api_key, secret_key, paper_trading=paper_trading
        )

        # Second call with same credentials should return the same hash (salt is reused)
        result2 = WebSocketConnectionManager._hash_credentials(
            api_key, secret_key, paper_trading=paper_trading
        )

        # Verify hash properties
        assert len(result1) == 64  # PBKDF2 with 32-byte output = 64 hex chars
        assert all(c in "0123456789abcdef" for c in result1)
        assert result1 == result2  # Same credentials = same hash

        # Different credentials should produce different hash
        result3 = WebSocketConnectionManager._hash_credentials(
            "different_key", secret_key, paper_trading=paper_trading
        )
        assert result1 != result3


class TestWebSocketConnectionManagerReferenceCountingPricing:
    """Test reference counting for pricing service."""

    @patch("the_alchemiser.shared.services.websocket_manager.RealTimePricingService")
    def test_get_pricing_service_increments_ref_count(self, mock_service_class):
        """Test that getting pricing service increments reference count."""
        mock_service = MagicMock()
        mock_service.start.return_value = True
        mock_service_class.return_value = mock_service

        manager = WebSocketConnectionManager("key", "secret", paper_trading=True)

        assert manager._pricing_ref_count == 0

        manager.get_pricing_service()
        assert manager._pricing_ref_count == 1

        manager.get_pricing_service()
        assert manager._pricing_ref_count == 2

    @patch("the_alchemiser.shared.services.websocket_manager.RealTimePricingService")
    def test_release_pricing_service_decrements_ref_count(self, mock_service_class):
        """Test that releasing pricing service decrements reference count."""
        mock_service = MagicMock()
        mock_service.start.return_value = True
        mock_service_class.return_value = mock_service

        manager = WebSocketConnectionManager("key", "secret", paper_trading=True)

        manager.get_pricing_service()
        manager.get_pricing_service()
        assert manager._pricing_ref_count == 2

        manager.release_pricing_service()
        assert manager._pricing_ref_count == 1

        manager.release_pricing_service()
        assert manager._pricing_ref_count == 0

    @patch("the_alchemiser.shared.services.websocket_manager.RealTimePricingService")
    def test_release_pricing_service_stops_when_ref_count_zero(self, mock_service_class):
        """Test that pricing service is stopped when ref count reaches zero."""
        mock_service = MagicMock()
        mock_service.start.return_value = True
        mock_service_class.return_value = mock_service

        manager = WebSocketConnectionManager("key", "secret", paper_trading=True)

        manager.get_pricing_service()
        assert manager._pricing_service is not None

        manager.release_pricing_service()
        assert manager._pricing_service is None
        mock_service.stop.assert_called_once()

    @patch("the_alchemiser.shared.services.websocket_manager.RealTimePricingService")
    @patch("the_alchemiser.shared.services.websocket_manager.logger")
    def test_release_pricing_service_warns_on_negative_count(self, mock_logger, mock_service_class):
        """Test that releasing when ref count is 0 logs a warning."""
        manager = WebSocketConnectionManager("key", "secret", paper_trading=True)

        manager.release_pricing_service()

        # Check that warning was logged
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args
        assert "reference count was already 0 or negative" in call_args[0][0]


class TestWebSocketConnectionManagerReferenceCountingTrading:
    """Test reference counting for trading service."""

    @patch("the_alchemiser.shared.services.websocket_manager.TradingStream")
    def test_get_trading_service_increments_ref_count(self, mock_stream_class):
        """Test that getting trading service increments reference count."""
        mock_stream = MagicMock()
        mock_stream_class.return_value = mock_stream

        manager = WebSocketConnectionManager("key", "secret", paper_trading=True)
        callback = AsyncMock()

        assert manager._trading_ref_count == 0

        manager.get_trading_service(callback)
        assert manager._trading_ref_count == 1

        manager.get_trading_service(callback)
        assert manager._trading_ref_count == 2

    @patch("the_alchemiser.shared.services.websocket_manager.TradingStream")
    def test_release_trading_service_decrements_ref_count(self, mock_stream_class):
        """Test that releasing trading service decrements reference count."""
        mock_stream = MagicMock()
        mock_stream_class.return_value = mock_stream

        manager = WebSocketConnectionManager("key", "secret", paper_trading=True)
        callback = AsyncMock()

        manager.get_trading_service(callback)
        manager.get_trading_service(callback)
        assert manager._trading_ref_count == 2

        manager.release_trading_service()
        assert manager._trading_ref_count == 1

        manager.release_trading_service()
        assert manager._trading_ref_count == 0

    @patch("the_alchemiser.shared.services.websocket_manager.TradingStream")
    def test_release_trading_service_stops_when_ref_count_zero(self, mock_stream_class):
        """Test that trading service is stopped when ref count reaches zero."""
        mock_stream = MagicMock()
        mock_stream_class.return_value = mock_stream

        manager = WebSocketConnectionManager("key", "secret", paper_trading=True)
        callback = AsyncMock()

        manager.get_trading_service(callback)
        assert manager._trading_stream is not None

        manager.release_trading_service()
        time.sleep(0.1)  # Give timeout thread time to complete

        assert manager._trading_stream is None
        mock_stream.stop.assert_called_once()

    @patch("the_alchemiser.shared.services.websocket_manager.TradingStream")
    @patch("the_alchemiser.shared.services.websocket_manager.logger")
    def test_release_trading_service_warns_on_negative_count(self, mock_logger, mock_stream_class):
        """Test that releasing when ref count is 0 logs a warning."""
        manager = WebSocketConnectionManager("key", "secret", paper_trading=True)

        manager.release_trading_service()

        # Check that warning was logged
        mock_logger.warning.assert_called()
        call_args = mock_logger.warning.call_args
        assert "reference count was already 0 or negative" in call_args[0][0]


class TestWebSocketConnectionManagerErrorHandling:
    """Test error handling and typed exceptions."""

    @patch("the_alchemiser.shared.services.websocket_manager.RealTimePricingService")
    def test_get_pricing_service_raises_websocket_error_on_start_failure(self, mock_service_class):
        """Test that WebSocketError is raised when pricing service fails to start."""
        mock_service = MagicMock()
        mock_service.start.return_value = False
        mock_service_class.return_value = mock_service

        manager = WebSocketConnectionManager("key", "secret", paper_trading=True)

        with pytest.raises(WebSocketError) as exc_info:
            manager.get_pricing_service()

        assert "Failed to start real-time pricing service" in str(exc_info.value)

    @patch("the_alchemiser.shared.services.websocket_manager.TradingStream")
    def test_get_trading_service_returns_false_on_failure(self, mock_stream_class):
        """Test that get_trading_service returns False on failure."""
        mock_stream_class.side_effect = Exception("Connection failed")

        manager = WebSocketConnectionManager("key", "secret", paper_trading=True)
        callback = AsyncMock()

        result = manager.get_trading_service(callback)

        assert result is False
        assert manager._trading_ws_connected is False


class TestWebSocketConnectionManagerThreadSafety:
    """Test thread safety under concurrent access."""

    @patch("the_alchemiser.shared.services.websocket_manager.RealTimePricingService")
    def test_concurrent_get_pricing_service_thread_safe(self, mock_service_class):
        """Test that concurrent access to get_pricing_service is thread-safe."""
        mock_service = MagicMock()
        mock_service.start.return_value = True
        mock_service_class.return_value = mock_service

        manager = WebSocketConnectionManager("key", "secret", paper_trading=True)

        def get_service():
            manager.get_pricing_service()

        threads = [threading.Thread(target=get_service) for _ in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # All threads should have incremented the ref count
        assert manager._pricing_ref_count == 10
        # Service should only be created once
        assert mock_service_class.call_count == 1

    def test_singleton_creation_thread_safe(self):
        """Test that singleton creation is thread-safe."""
        instances = []

        def create_instance():
            manager = WebSocketConnectionManager("key", "secret", paper_trading=True)
            instances.append(manager)

        threads = [threading.Thread(target=create_instance) for _ in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # All threads should get the same instance
        assert all(instance is instances[0] for instance in instances)


class TestWebSocketConnectionManagerHealthCheck:
    """Test health check and statistics."""

    @patch("the_alchemiser.shared.services.websocket_manager.RealTimePricingService")
    def test_get_connection_health_redacts_credentials(self, mock_service_class):
        """Test that get_connection_health redacts credential hashes in output."""
        mock_service = MagicMock()
        mock_service.start.return_value = True
        mock_service.get_stats.return_value = {"status": "connected"}
        mock_service.is_connected.return_value = True
        mock_service_class.return_value = mock_service

        manager = WebSocketConnectionManager("key", "secret", paper_trading=True)
        manager.get_pricing_service()

        health = WebSocketConnectionManager.get_connection_health()

        # Check that credential keys are redacted (only first 8 chars + "...")
        for key in health["instances"].keys():
            assert len(key) <= 11  # 8 chars + "..."
            if len(key) > 8:
                assert key.endswith("...")

    def test_is_service_available_returns_false_when_no_service(self):
        """Test that is_service_available returns False when no service exists."""
        manager = WebSocketConnectionManager("key", "secret", paper_trading=True)

        assert manager.is_service_available() is False

    def test_is_trading_service_available_returns_false_when_no_service(self):
        """Test that is_trading_service_available returns False when no service exists."""
        manager = WebSocketConnectionManager("key", "secret", paper_trading=True)

        assert manager.is_trading_service_available() is False


class TestWebSocketConnectionManagerCleanup:
    """Test cleanup scenarios and event-based synchronization."""

    @patch("the_alchemiser.shared.services.websocket_manager.RealTimePricingService")
    @patch("the_alchemiser.shared.services.websocket_manager.TradingStream")
    def test_cleanup_all_instances_stops_all_services(self, mock_stream_class, mock_service_class):
        """Test that cleanup_all_instances stops all services."""
        mock_service = MagicMock()
        mock_service.start.return_value = True
        mock_service_class.return_value = mock_service

        mock_stream = MagicMock()
        mock_stream_class.return_value = mock_stream

        # Create multiple managers
        manager1 = WebSocketConnectionManager("key1", "secret1", paper_trading=True)
        manager2 = WebSocketConnectionManager("key2", "secret2", paper_trading=True)

        manager1.get_pricing_service()
        manager2.get_trading_service(AsyncMock())

        # Cleanup
        WebSocketConnectionManager.cleanup_all_instances()

        # All services should be stopped
        mock_service.stop.assert_called()
        mock_stream.stop.assert_called()

        # Instances should be cleared
        assert len(WebSocketConnectionManager._instances) == 0

    def test_cleanup_uses_event_not_busy_wait(self):
        """Test that cleanup sets event for synchronization."""
        # Initially event should be set
        assert WebSocketConnectionManager._cleanup_event.is_set()

        # During cleanup it should be cleared then set
        with patch.object(WebSocketConnectionManager, "_instances", {}):
            WebSocketConnectionManager.cleanup_all_instances()

        # After cleanup, event should be set again
        assert WebSocketConnectionManager._cleanup_event.is_set()


class TestWebSocketConnectionManagerCorrelationID:
    """Test correlation_id support for distributed tracing."""

    @patch("the_alchemiser.shared.services.websocket_manager.RealTimePricingService")
    @patch("the_alchemiser.shared.services.websocket_manager.logger")
    def test_get_pricing_service_logs_correlation_id(self, mock_logger, mock_service_class):
        """Test that get_pricing_service includes correlation_id in logs."""
        mock_service = MagicMock()
        mock_service.start.return_value = True
        mock_service_class.return_value = mock_service

        manager = WebSocketConnectionManager("key", "secret", paper_trading=True)
        correlation_id = "test-correlation-123"

        manager.get_pricing_service(correlation_id=correlation_id)

        # Check that correlation_id was logged
        logged_with_correlation = False
        for call in mock_logger.info.call_args_list:
            if call[1].get("correlation_id") == correlation_id:
                logged_with_correlation = True
                break

        assert logged_with_correlation

    @patch("the_alchemiser.shared.services.websocket_manager.TradingStream")
    @patch("the_alchemiser.shared.services.websocket_manager.logger")
    def test_release_trading_service_logs_correlation_id(self, mock_logger, mock_stream_class):
        """Test that release_trading_service includes correlation_id in logs."""
        mock_stream = MagicMock()
        mock_stream_class.return_value = mock_stream

        manager = WebSocketConnectionManager("key", "secret", paper_trading=True)
        callback = AsyncMock()
        correlation_id = "test-correlation-456"

        manager.get_trading_service(callback)
        manager.release_trading_service(correlation_id=correlation_id)

        # Check that correlation_id was logged
        time.sleep(0.1)  # Give timeout thread time
        logged_with_correlation = False
        for call in mock_logger.info.call_args_list:
            if call[1].get("correlation_id") == correlation_id:
                logged_with_correlation = True
                break

        assert logged_with_correlation


class TestWebSocketConnectionManagerTimeoutProtection:
    """Test timeout protection on stop() calls."""

    @patch("the_alchemiser.shared.services.websocket_manager.TradingStream")
    @patch("the_alchemiser.shared.services.websocket_manager.logger")
    def test_release_trading_service_logs_timeout_warning(self, mock_logger, mock_stream_class):
        """Test that timeout is logged when stream.stop() hangs."""
        mock_stream = MagicMock()
        # Make stop() hang
        mock_stream.stop.side_effect = lambda: time.sleep(10)
        mock_stream_class.return_value = mock_stream

        manager = WebSocketConnectionManager("key", "secret", paper_trading=True)
        callback = AsyncMock()

        manager.get_trading_service(callback)
        manager.release_trading_service()

        # Wait for timeout
        time.sleep(6)

        # Check that timeout was logged
        timeout_logged = False
        for call in mock_logger.warning.call_args_list:
            if "timed out" in str(call):
                timeout_logged = True
                break

        assert timeout_logged


# Cleanup after all tests
@pytest.fixture(autouse=True)
def cleanup_singleton():
    """Clean up singleton instances after each test."""
    yield
    # Clear instances after each test to avoid interference
    WebSocketConnectionManager._instances.clear()
    WebSocketConnectionManager._cleanup_in_progress = False
    WebSocketConnectionManager._cleanup_event.set()
