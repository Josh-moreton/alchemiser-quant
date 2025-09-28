#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Integration tests for extended hours trading end-to-end configuration.

Tests the complete flow from environment variable to order execution.
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from the_alchemiser.execution_v2.core.execution_manager import ExecutionManager
from the_alchemiser.shared.config.config import Settings, load_settings


class TestExtendedHoursIntegration:
    """Integration tests for extended hours trading configuration."""

    @patch.dict(os.environ, {}, clear=True)
    def test_extended_hours_disabled_by_default(self):
        """Test that extended hours is disabled by default."""
        # Clear environment and create new settings
        settings = Settings()
        assert settings.alpaca.enable_extended_hours is False

    @patch.dict(os.environ, {"ALPACA__ENABLE_EXTENDED_HOURS": "true"})
    def test_extended_hours_enabled_via_env_var_true(self):
        """Test that extended hours can be enabled via environment variable 'true'."""
        settings = Settings()
        assert settings.alpaca.enable_extended_hours is True

    @patch.dict(os.environ, {"ALPACA__ENABLE_EXTENDED_HOURS": "1"})
    def test_extended_hours_enabled_via_env_var_one(self):
        """Test that extended hours can be enabled via environment variable '1'."""
        settings = Settings()
        assert settings.alpaca.enable_extended_hours is True

    @patch.dict(os.environ, {"ALPACA__ENABLE_EXTENDED_HOURS": "yes"})
    def test_extended_hours_enabled_via_env_var_yes(self):
        """Test that extended hours can be enabled via environment variable 'yes'."""
        settings = Settings()
        assert settings.alpaca.enable_extended_hours is True

    @patch.dict(os.environ, {"ALPACA__ENABLE_EXTENDED_HOURS": "false"})
    def test_extended_hours_disabled_via_env_var_false(self):
        """Test that extended hours can be explicitly disabled via environment variable."""
        settings = Settings()
        assert settings.alpaca.enable_extended_hours is False

    @patch.dict(os.environ, {"ALPACA__ENABLE_EXTENDED_HOURS": "0"})
    def test_extended_hours_disabled_via_env_var_zero(self):
        """Test that extended hours can be disabled via environment variable '0'."""
        settings = Settings()
        assert settings.alpaca.enable_extended_hours is False

    @patch.dict(os.environ, {"ALPACA__ENABLE_EXTENDED_HOURS": "true"})
    def test_end_to_end_extended_hours_flow(self):
        """Test end-to-end flow from environment variable to order execution."""
        # Mock credentials
        api_key = "test_key"
        secret_key = "test_secret"
        
        # Mock trading client and WebSocket manager at the module level
        with patch('the_alchemiser.shared.brokers.alpaca_manager.TradingClient') as mock_trading_client_class, \
             patch('the_alchemiser.shared.services.websocket_manager.WebSocketConnectionManager') as mock_ws_manager_class:
            
            # Set up mock instances
            mock_trading_client = MagicMock()
            mock_ws_manager = MagicMock()
            mock_trading_client_class.return_value = mock_trading_client
            mock_ws_manager_class.return_value = mock_ws_manager
            
            # Mock order creation and submission
            mock_order = MagicMock()
            mock_order.id = "test_order_123"
            mock_order.status = "accepted"
            mock_trading_client.submit_order.return_value = mock_order
            
            # Create ExecutionManager which should pick up the extended hours setting
            execution_manager = ExecutionManager.create_with_config(
                api_key=api_key,
                secret_key=secret_key,
                paper=True,
            )
            
            # Access the underlying trading service to verify extended hours is enabled
            alpaca_manager = execution_manager.alpaca_manager
            trading_service = alpaca_manager._trading_service
            
            # Verify that extended hours is enabled
            assert trading_service.extended_hours_enabled is True
            
            # Place a market order to verify extended_hours parameter is passed through
            trading_service.place_market_order("AAPL", "buy", qty=10)
            
            # Verify that submit_order was called
            assert mock_trading_client.submit_order.called
            
            # Get the order request that was passed
            order_request = mock_trading_client.submit_order.call_args[0][0]
            
            # Verify extended_hours is set correctly in the actual order
            assert hasattr(order_request, 'extended_hours')
            assert order_request.extended_hours is True

    def test_example_usage_documentation(self):
        """Test that demonstrates how to use extended hours trading.
        
        This test serves as living documentation for the feature.
        """
        # Example 1: Enable extended hours via environment variable
        with patch.dict(os.environ, {"ALPACA__ENABLE_EXTENDED_HOURS": "true"}):
            settings = Settings()
            assert settings.alpaca.enable_extended_hours is True
            
        # Example 2: Disable extended hours (default behavior)
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.alpaca.enable_extended_hours is False
            
        # Example 3: Configuration via .env file would work the same way
        # Just add: ALPACA__ENABLE_EXTENDED_HOURS=true to your .env file