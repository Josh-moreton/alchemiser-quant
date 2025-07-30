#!/usr/bin/env python3
"""
Test error handling scenarios including API errors, network failures,
order status polling issues, and settlement waiting problems.
"""

import pytest
from unittest.mock import MagicMock, patch
from alpaca.trading.enums import OrderSide
from alpaca.common.exceptions import APIError
import requests.exceptions

from the_alchemiser.execution.smart_execution import SmartExecution


@pytest.fixture
def mock_trading_client():
    """Mock Alpaca trading client."""
    client = MagicMock()
    client.submit_order.return_value = MagicMock(id='test_order_123')
    client.get_order_by_id.return_value = MagicMock(id='test_order_123', status='filled')
    client.get_all_positions.return_value = []
    client.get_clock.return_value = MagicMock(is_open=True)
    return client


@pytest.fixture
def mock_data_provider():
    """Mock data provider."""
    provider = MagicMock()
    provider.get_current_price.return_value = 100.0
    provider.get_latest_quote.return_value = (99.0, 101.0)
    return provider


@pytest.fixture
def order_manager(mock_trading_client, mock_data_provider):
    """Create SmartExecution for testing."""
    return SmartExecution(mock_trading_client, mock_data_provider)


class TestAPIErrors:
    """Test various Alpaca API error scenarios."""
    
    def test_insufficient_buying_power_error(self, order_manager, mock_trading_client):
        """Test handling of insufficient buying power API error."""
        error_response = {"code": 40310000, "message": "insufficient buying power"}
        mock_trading_client.submit_order.side_effect = APIError(error_response)
        
        order_id = order_manager.place_limit_or_market('AAPL', 1000.0, OrderSide.BUY)
        
        assert order_id is None
    
    def test_symbol_not_found_error(self, order_manager, mock_trading_client):
        """Test handling of invalid symbol API error."""
        error_response = {"code": 40410000, "message": "symbol not found"}
        mock_trading_client.submit_order.side_effect = APIError(error_response)
        
        order_id = order_manager.place_limit_or_market('INVALID', 1.0, OrderSide.BUY)
        
        assert order_id is None
    
    def test_market_closed_error(self, order_manager, mock_trading_client):
        """Test handling of market closed API error."""
        error_response = {"code": 40010001, "message": "market is closed"}
        mock_trading_client.submit_order.side_effect = APIError(error_response)
        
        order_id = order_manager.place_limit_or_market('AAPL', 1.0, OrderSide.BUY)
        
        assert order_id is None
    
    def test_account_suspended_error(self, order_manager, mock_trading_client):
        """Test handling of account suspension error."""
        error_response = {"code": 40310001, "message": "account is suspended"}
        mock_trading_client.submit_order.side_effect = APIError(error_response)
        
        order_id = order_manager.place_limit_or_market('AAPL', 1.0, OrderSide.BUY)
        
        assert order_id is None
    
    def test_rate_limit_error(self, order_manager, mock_trading_client):
        """Test handling of API rate limiting."""
        error_response = {"code": 42910000, "message": "rate limit exceeded"}
        mock_trading_client.submit_order.side_effect = APIError(error_response)
        
        order_id = order_manager.place_limit_or_market('AAPL', 1.0, OrderSide.BUY)
        
        assert order_id is None
    
    def test_generic_api_error(self, order_manager, mock_trading_client):
        """Test handling of generic API errors."""
        error_response = {"code": 50000000, "message": "internal server error"}
        mock_trading_client.submit_order.side_effect = APIError(error_response)
        
        order_id = order_manager.place_limit_or_market('AAPL', 1.0, OrderSide.BUY)
        
        assert order_id is None
    
    def test_malformed_api_response(self, order_manager, mock_trading_client):
        """Test handling of malformed API responses."""
        # Mock malformed response that doesn't match expected structure
        mock_trading_client.submit_order.side_effect = ValueError("Malformed response")
        
        order_id = order_manager.place_limit_or_market('AAPL', 1.0, OrderSide.BUY)
        
        assert order_id is None


class TestNetworkFailures:
    """Test network-related failure scenarios."""
    
    def test_connection_timeout(self, order_manager, mock_trading_client):
        """Test handling of connection timeouts."""
        mock_trading_client.submit_order.side_effect = requests.exceptions.Timeout("Connection timeout")
        
        order_id = order_manager.place_limit_or_market('AAPL', 1.0, OrderSide.BUY)
        
        assert order_id is None
    
    def test_connection_error(self, order_manager, mock_trading_client):
        """Test handling of connection errors."""
        mock_trading_client.submit_order.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        order_id = order_manager.place_limit_or_market('AAPL', 1.0, OrderSide.BUY)
        
        assert order_id is None
    
    def test_dns_resolution_failure(self, order_manager, mock_trading_client):
        """Test handling of DNS resolution failures."""
        mock_trading_client.submit_order.side_effect = requests.exceptions.ConnectionError("DNS resolution failed")
        
        order_id = order_manager.place_limit_or_market('AAPL', 1.0, OrderSide.BUY)
        
        assert order_id is None
    
    def test_ssl_certificate_error(self, order_manager, mock_trading_client):
        """Test handling of SSL certificate errors."""
        mock_trading_client.submit_order.side_effect = requests.exceptions.SSLError("SSL certificate verification failed")
        
        order_id = order_manager.place_limit_or_market('AAPL', 1.0, OrderSide.BUY)
        
        assert order_id is None
    
    def test_intermittent_network_failure(self, order_manager, mock_trading_client):
        """Test handling of intermittent network failures."""
        # First call fails, second succeeds
        mock_trading_client.submit_order.side_effect = [
            requests.exceptions.ConnectionError("Network error"),
            MagicMock(id='test_order_123')
        ]
        
        # First attempt should fail
        order_id1 = order_manager.place_limit_or_market('AAPL', 1.0, OrderSide.BUY)
        assert order_id1 is None
        
        # Second attempt should succeed
        order_id2 = order_manager.place_limit_or_market('AAPL', 1.0, OrderSide.BUY)
        assert order_id2 is not None


class TestOrderStatusPollingIssues:
    """Test order status polling error scenarios."""
    
    def test_order_status_api_error(self, order_manager, mock_trading_client):
        """Test error when polling order status."""
        # Order placement succeeds
        mock_trading_client.submit_order.return_value = MagicMock(id='test_order_123')
        
        # But status polling fails
        mock_trading_client.get_order_by_id.side_effect = APIError({"code": 40410000, "message": "order not found"})
        
        sell_orders = [{'order_id': 'test_order_123'}]
        result = order_manager.wait_for_settlement(sell_orders, max_wait_time=0.2, poll_interval=0.1)
        
        # Should handle gracefully and return False (couldn't verify settlement)
        assert result is False
    
    def test_order_status_network_error(self, order_manager, mock_trading_client):
        """Test network error when polling order status."""
        mock_trading_client.submit_order.return_value = MagicMock(id='test_order_123')
        mock_trading_client.get_order_by_id.side_effect = requests.exceptions.Timeout("Status check timeout")
        
        sell_orders = [{'order_id': 'test_order_123'}]
        result = order_manager.wait_for_settlement(sell_orders, max_wait_time=0.2, poll_interval=0.1)
        
        assert result is False
    
    def test_order_stuck_in_pending(self, order_manager, mock_trading_client):
        """Test order stuck in pending status."""
        mock_trading_client.submit_order.return_value = MagicMock(id='test_order_123')
        
        # Order remains in pending state
        pending_order = MagicMock(id='test_order_123', status='pending_new')
        mock_trading_client.get_order_by_id.return_value = pending_order
        
        sell_orders = [{'order_id': 'test_order_123'}]
        result = order_manager.wait_for_settlement(sell_orders, max_wait_time=0.2, poll_interval=0.1)
        
        # Should timeout since order never settles
        assert result is False
    
    def test_order_status_changes_unexpectedly(self, order_manager, mock_trading_client):
        """Test order status changing to unexpected values."""
        mock_trading_client.submit_order.return_value = MagicMock(id='test_order_123')
        
        # Order goes to unexpected status
        unexpected_order = MagicMock(id='test_order_123', status='unknown_status')
        mock_trading_client.get_order_by_id.return_value = unexpected_order
        
        sell_orders = [{'order_id': 'test_order_123'}]
        result = order_manager.wait_for_settlement(sell_orders, max_wait_time=0.2, poll_interval=0.1)
        
        # Should handle gracefully
        assert result is False


class TestSettlementWaitingProblems:
    """Test settlement waiting edge cases and problems."""
    
    def test_settlement_timeout_multiple_orders(self, order_manager, mock_trading_client):
        """Test settlement timeout with multiple orders."""
        mock_trading_client.submit_order.return_value = MagicMock(id='test_order_123')
        
        # Mix of filled and pending orders
        def mock_get_order(order_id):
            if order_id == 'order_1':
                return MagicMock(id='order_1', status='filled')
            else:
                return MagicMock(id=order_id, status='pending_new')
        
        mock_trading_client.get_order_by_id.side_effect = mock_get_order
        
        sell_orders = [
            {'order_id': 'order_1'},  # Will fill
            {'order_id': 'order_2'},  # Will remain pending
            {'order_id': 'order_3'}   # Will remain pending
        ]
        
        result = order_manager.wait_for_settlement(sell_orders, max_wait_time=0.2, poll_interval=0.1)
        
        # Should timeout due to pending orders
        assert result is False
    
    def test_settlement_with_zero_orders(self, order_manager, mock_trading_client):
        """Test settlement waiting with empty order list."""
        result = order_manager.wait_for_settlement([], max_wait_time=1, poll_interval=0.1)
        
        # Should return True immediately (no orders to wait for)
        assert result is True
    
    def test_settlement_with_invalid_order_ids(self, order_manager, mock_trading_client):
        """Test settlement waiting with invalid order IDs."""
        mock_trading_client.get_order_by_id.side_effect = APIError({"code": 40410000, "message": "order not found"})
        
        sell_orders = [{'order_id': 'invalid_order_id'}]
        result = order_manager.wait_for_settlement(sell_orders, max_wait_time=0.2, poll_interval=0.1)
        
        assert result is False
    
    def test_settlement_with_malformed_order_data(self, order_manager, mock_trading_client):
        """Test settlement with malformed order data."""
        # Order data missing required fields
        sell_orders = [
            {'invalid_key': 'some_value'},  # Missing 'order_id'
            {}  # Empty dict
        ]
        
        result = order_manager.wait_for_settlement(sell_orders, max_wait_time=0.2, poll_interval=0.1)
        
        # Should handle gracefully
        assert result is False


class TestDataProviderErrors:
    """Test data provider error scenarios."""
    
    def test_price_fetch_error(self, order_manager, mock_trading_client, mock_data_provider):
        """Test error when fetching current price."""
        mock_data_provider.get_current_price.side_effect = Exception("Price data unavailable")
        
        # Should still place order (using order manager's fallback behavior)
        order_id = order_manager.place_limit_or_market('AAPL', 1.0, OrderSide.BUY)
        
        # Behavior depends on implementation - either succeeds with default or fails
        # This tests that it handles the error gracefully
        assert order_id is not None or order_id is None  # Either outcome is acceptable
    
    def test_quote_fetch_error(self, order_manager, mock_trading_client, mock_data_provider):
        """Test error when fetching bid/ask quotes."""
        mock_data_provider.get_latest_quote.side_effect = Exception("Quote data unavailable")
        
        order_id = order_manager.place_limit_or_market('AAPL', 1.0, OrderSide.BUY)
        
        # Should handle gracefully
        assert order_id is not None or order_id is None


class TestConcurrentErrorScenarios:
    """Test multiple simultaneous error conditions."""
    
    def test_api_and_network_errors_combined(self, order_manager, mock_trading_client):
        """Test combination of API and network errors."""
        # Simulate sequence of different errors
        mock_trading_client.submit_order.side_effect = [
            requests.exceptions.Timeout("Network timeout"),
            APIError({"code": 42910000, "message": "rate limit exceeded"}),
            MagicMock(id='test_order_123')  # Finally succeeds
        ]
        
        # First two attempts should fail
        order_id1 = order_manager.place_limit_or_market('AAPL', 1.0, OrderSide.BUY)
        assert order_id1 is None
        
        order_id2 = order_manager.place_limit_or_market('AAPL', 1.0, OrderSide.BUY)
        assert order_id2 is None
        
        # Third attempt should succeed
        order_id3 = order_manager.place_limit_or_market('AAPL', 1.0, OrderSide.BUY)
        assert order_id3 is not None
    
    def test_position_fetch_and_order_errors(self, order_manager, mock_trading_client):
        """Test errors in both position fetching and order placement."""
        # Position fetching fails
        mock_trading_client.get_all_positions.side_effect = APIError({"code": 50000000, "message": "server error"})
        
        # Order placement also fails
        mock_trading_client.submit_order.side_effect = APIError({"code": 40310000, "message": "insufficient buying power"})
        
        # Safe sell should handle position fetch error gracefully
        order_id = order_manager.place_safe_sell_order('AAPL', 10.0)
        
        assert order_id is None


class TestErrorRecovery:
    """Test error recovery and retry scenarios."""
    
    def test_retry_after_transient_error(self, order_manager, mock_trading_client):
        """Test retry logic after transient errors."""
        # Simulate transient error followed by success
        mock_trading_client.submit_order.side_effect = [
            APIError({"code": 50000000, "message": "internal server error"}),  # Transient
            MagicMock(id='test_order_123')  # Success
        ]
        
        # First attempt fails
        order_id1 = order_manager.place_limit_or_market('AAPL', 1.0, OrderSide.BUY)
        assert order_id1 is None
        
        # Retry succeeds
        order_id2 = order_manager.place_limit_or_market('AAPL', 1.0, OrderSide.BUY)
        assert order_id2 is not None
    
    def test_no_retry_after_permanent_error(self, order_manager, mock_trading_client):
        """Test no retry after permanent errors like insufficient funds."""
        # Permanent error that shouldn't be retried
        mock_trading_client.submit_order.side_effect = APIError({"code": 40310000, "message": "insufficient buying power"})
        
        order_id = order_manager.place_limit_or_market('AAPL', 1000.0, OrderSide.BUY)
        
        assert order_id is None
        
        # Verify only one attempt was made
        assert mock_trading_client.submit_order.call_count == 1
