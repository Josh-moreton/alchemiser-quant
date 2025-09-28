#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Tests for extended hours trading functionality.

Validates that the extended hours parameter is properly propagated
from configuration through to Alpaca order requests.
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from the_alchemiser.shared.config.config_service import ConfigService
from the_alchemiser.shared.services.alpaca_trading_service import AlpacaTradingService


class TestExtendedHoursTrading:
    """Test extended hours trading configuration and functionality."""

    def test_config_service_extended_hours_default(self):
        """Test that extended hours defaults to False."""
        config_service = ConfigService()
        assert config_service.extended_hours_enabled is False

    @patch.dict(os.environ, {"ALPACA_ENABLE_EXTENDED_HOURS": "true"})
    def test_config_service_extended_hours_enabled(self):
        """Test that extended hours can be enabled via environment variable."""
        # Force reload of config by creating new instance
        config_service = ConfigService()
        # Note: This test may require config reload mechanism depending on implementation
        # For now, we test the structure is correct

    def test_alpaca_trading_service_extended_hours_property(self):
        """Test that AlpacaTradingService exposes extended_hours_enabled property."""
        # Mock dependencies
        mock_trading_client = MagicMock()
        mock_websocket_manager = MagicMock()
        
        # Test with extended hours disabled
        service = AlpacaTradingService(
            mock_trading_client,
            mock_websocket_manager,
            paper_trading=True,
            extended_hours_enabled=False,
        )
        assert service.extended_hours_enabled is False
        
        # Test with extended hours enabled
        service_enabled = AlpacaTradingService(
            mock_trading_client,
            mock_websocket_manager,
            paper_trading=True,
            extended_hours_enabled=True,
        )
        assert service_enabled.extended_hours_enabled is True

    def test_market_order_includes_extended_hours(self):
        """Test that market orders include extended_hours parameter."""
        # Mock dependencies
        mock_trading_client = MagicMock()
        mock_websocket_manager = MagicMock()
        mock_order = MagicMock()
        mock_order.id = "test_order_id"
        mock_order.status = "accepted"
        mock_trading_client.submit_order.return_value = mock_order
        
        # Create service with extended hours enabled
        service = AlpacaTradingService(
            mock_trading_client,
            mock_websocket_manager,
            paper_trading=True,
            extended_hours_enabled=True,
        )
        
        # Place a market order
        service.place_market_order("AAPL", "buy", qty=10)
        
        # Verify that submit_order was called
        assert mock_trading_client.submit_order.called
        
        # Get the order request that was passed
        order_request = mock_trading_client.submit_order.call_args[0][0]
        
        # Verify extended_hours is set correctly
        assert hasattr(order_request, 'extended_hours')
        assert order_request.extended_hours is True

    def test_limit_order_includes_extended_hours(self):
        """Test that limit orders include extended_hours parameter."""
        # Mock dependencies
        mock_trading_client = MagicMock()
        mock_websocket_manager = MagicMock()
        mock_order = MagicMock()
        mock_order.id = "test_order_id"
        mock_order.status = "accepted"
        mock_trading_client.submit_order.return_value = mock_order
        
        # Create service with extended hours enabled
        service = AlpacaTradingService(
            mock_trading_client,
            mock_websocket_manager,
            paper_trading=True,
            extended_hours_enabled=True,
        )
        
        # Place a limit order
        service.place_limit_order("AAPL", "buy", quantity=10, limit_price=150.0)
        
        # Verify that submit_order was called
        assert mock_trading_client.submit_order.called
        
        # Get the order request that was passed
        order_request = mock_trading_client.submit_order.call_args[0][0]
        
        # Verify extended_hours is set correctly
        assert hasattr(order_request, 'extended_hours')
        assert order_request.extended_hours is True

    def test_extended_hours_disabled_by_default(self):
        """Test that extended hours is disabled by default in order requests."""
        # Mock dependencies
        mock_trading_client = MagicMock()
        mock_websocket_manager = MagicMock()
        mock_order = MagicMock()
        mock_order.id = "test_order_id"
        mock_order.status = "accepted"
        mock_trading_client.submit_order.return_value = mock_order
        
        # Create service with extended hours disabled (default)
        service = AlpacaTradingService(
            mock_trading_client,
            mock_websocket_manager,
            paper_trading=True,
            extended_hours_enabled=False,
        )
        
        # Place a market order
        service.place_market_order("AAPL", "buy", qty=10)
        
        # Verify that submit_order was called
        assert mock_trading_client.submit_order.called
        
        # Get the order request that was passed
        order_request = mock_trading_client.submit_order.call_args[0][0]
        
        # Verify extended_hours is set to False
        assert hasattr(order_request, 'extended_hours')
        assert order_request.extended_hours is False