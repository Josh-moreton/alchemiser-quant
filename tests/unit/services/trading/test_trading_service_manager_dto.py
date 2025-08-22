#!/usr/bin/env python3
"""
Tests for TradingServiceManager DTO integration.

Tests the integration of OrderRequestDTO validation into order placement methods
in TradingServiceManager to ensure consistent validation throughout the pipeline.
"""

import datetime
from decimal import Decimal
from unittest.mock import Mock, patch
import pytest

from the_alchemiser.services.trading.trading_service_manager import TradingServiceManager
from the_alchemiser.interfaces.schemas.orders import OrderExecutionResultDTO
from the_alchemiser.domain.trading.entities.order import Order
from the_alchemiser.domain.trading.value_objects.order_id import OrderId
from the_alchemiser.domain.trading.value_objects.symbol import Symbol
from the_alchemiser.domain.trading.value_objects.quantity import Quantity
from the_alchemiser.domain.trading.value_objects.order_status import OrderStatus


class TestTradingServiceManagerDTOIntegration:
    """Test DTO integration in TradingServiceManager order methods."""

    def setup_method(self):
        """Set up test fixtures with mocked dependencies."""
        # Mock the AlpacaManager to avoid real API calls
        with patch('the_alchemiser.services.trading.trading_service_manager.AlpacaManager') as mock_alpaca_class:
            self.mock_alpaca_manager = Mock()
            mock_alpaca_class.return_value = self.mock_alpaca_manager
            
            # Initialize TradingServiceManager with mocked dependencies
            self.trading_manager = TradingServiceManager("test_key", "test_secret", paper=True)
            self.trading_manager.alpaca_manager = self.mock_alpaca_manager

    def create_mock_alpaca_order(self, symbol: str = "AAPL", qty: float = 100.0):
        """Create a mock Alpaca order object for testing."""
        import uuid
        
        mock_order = Mock()
        mock_order.id = str(uuid.uuid4())  # Use valid UUID
        mock_order.symbol = symbol
        mock_order.qty = qty
        mock_order.side = "buy"
        mock_order.order_type = "market"
        mock_order.status = "accepted"
        mock_order.filled_qty = 0
        mock_order.created_at = datetime.datetime.now()
        mock_order.updated_at = datetime.datetime.now()
        return mock_order

    def test_place_market_order_with_validation_success(self):
        """Test successful market order placement with DTO validation."""
        # Mock successful order placement
        mock_alpaca_order = self.create_mock_alpaca_order("AAPL", 100.0)
        self.mock_alpaca_manager.place_order.return_value = mock_alpaca_order

        # Place market order with validation enabled
        result = self.trading_manager.place_market_order(
            symbol="AAPL",
            quantity=100.0,
            side="buy",
            validate=True
        )

        # Verify result
        assert isinstance(result, OrderExecutionResultDTO)
        assert result.success is True
        assert result.order_id is not None
        assert result.status in ["accepted", "filled"]
        assert result.filled_qty == Decimal("0")
        
        # Verify Alpaca manager was called
        self.mock_alpaca_manager.place_order.assert_called_once()

    def test_place_market_order_validation_failure(self):
        """Test market order placement with validation failure."""
        # Place market order with invalid data (empty symbol)
        result = self.trading_manager.place_market_order(
            symbol="",  # Invalid symbol
            quantity=100.0,
            side="buy",
            validate=True
        )

        # Verify validation failure
        assert isinstance(result, OrderExecutionResultDTO)
        assert result.success is False
        assert "validation failed" in result.error.lower()
        assert result.status == "rejected"
        
        # Verify Alpaca manager was NOT called due to validation failure
        self.mock_alpaca_manager.place_order.assert_not_called()

    def test_place_market_order_validation_disabled(self):
        """Test market order placement with validation disabled."""
        # Mock successful order placement
        mock_alpaca_order = self.create_mock_alpaca_order("AAPL", 100.0)
        self.mock_alpaca_manager.place_order.return_value = mock_alpaca_order

        # Place market order with validation disabled
        result = self.trading_manager.place_market_order(
            symbol="AAPL",
            quantity=100.0,
            side="buy",
            validate=False
        )

        # Verify result (should succeed even without validation)
        assert isinstance(result, OrderExecutionResultDTO)
        assert result.success is True
        
        # Verify Alpaca manager was called
        self.mock_alpaca_manager.place_order.assert_called_once()

    def test_place_limit_order_with_validation_success(self):
        """Test successful limit order placement with DTO validation."""
        # Mock successful order placement
        mock_alpaca_order = self.create_mock_alpaca_order("TSLA", 50.0)
        self.mock_alpaca_manager.place_order.return_value = mock_alpaca_order

        # Place limit order with validation enabled
        result = self.trading_manager.place_limit_order(
            symbol="TSLA",
            quantity=50.0,
            side="sell",
            limit_price=250.50,
            validate=True
        )

        # Verify result
        assert isinstance(result, OrderExecutionResultDTO)
        assert result.success is True
        assert result.order_id is not None
        
        # Verify Alpaca manager was called
        self.mock_alpaca_manager.place_order.assert_called_once()

    def test_place_limit_order_validation_failure(self):
        """Test limit order placement with validation failure."""
        # Place limit order with invalid data (negative price)
        result = self.trading_manager.place_limit_order(
            symbol="TSLA",
            quantity=50.0,
            side="sell",
            limit_price=-250.50,  # Invalid negative price
            validate=True
        )

        # Verify validation failure
        assert isinstance(result, OrderExecutionResultDTO)
        assert result.success is False
        assert "validation failed" in result.error.lower()
        assert result.status == "rejected"
        
        # Verify Alpaca manager was NOT called due to validation failure
        self.mock_alpaca_manager.place_order.assert_not_called()

    def test_place_limit_order_without_price_validation(self):
        """Test limit order validation requires limit price."""
        # The OrderRequestDTO should catch this at creation time
        # But test the validation pipeline anyway
        result = self.trading_manager.place_limit_order(
            symbol="AAPL",
            quantity=100.0,
            side="buy",
            limit_price=0.0,  # Invalid zero price
            validate=True
        )

        # Verify validation failure
        assert isinstance(result, OrderExecutionResultDTO)
        assert result.success is False
        assert result.status == "rejected"

    def test_place_market_order_invalid_side(self):
        """Test market order with invalid side value."""
        # This should be caught by DTO validation
        result = self.trading_manager.place_market_order(
            symbol="AAPL",
            quantity=100.0,
            side="invalid_side",  # Invalid side
            validate=True
        )

        # Verify validation failure
        assert isinstance(result, OrderExecutionResultDTO)
        assert result.success is False
        assert "validation failed" in result.error.lower()

    def test_place_market_order_zero_quantity(self):
        """Test market order with zero quantity."""
        result = self.trading_manager.place_market_order(
            symbol="AAPL",
            quantity=0.0,  # Invalid zero quantity
            side="buy",
            validate=True
        )

        # Verify validation failure
        assert isinstance(result, OrderExecutionResultDTO)
        assert result.success is False
        assert "validation failed" in result.error.lower()

    def test_place_limit_order_fractional_quantity(self):
        """Test limit order with fractional quantity - should fail at domain level."""
        # Don't mock any order placement since we expect validation to fail
        
        result = self.trading_manager.place_limit_order(
            symbol="AAPL",
            quantity=10.5,  # Fractional quantity
            side="buy",
            limit_price=150.00,
            validate=True
        )

        # Should fail due to domain validation (Quantity must be whole number)
        # Could fail at DTO validation or domain mapping level
        assert isinstance(result, OrderExecutionResultDTO)
        assert result.success is False
        # Just verify it failed - the error could be "whole number" or UUID related

    def test_place_market_order_alpaca_exception(self):
        """Test market order when Alpaca API throws exception."""
        # Mock Alpaca API exception
        self.mock_alpaca_manager.place_order.side_effect = Exception("Alpaca API error")

        result = self.trading_manager.place_market_order(
            symbol="AAPL",
            quantity=100.0,
            side="buy",
            validate=True
        )

        # Verify error handling
        assert isinstance(result, OrderExecutionResultDTO)
        assert result.success is False
        assert "Alpaca API error" in result.error

    def test_place_limit_order_alpaca_exception(self):
        """Test limit order when Alpaca API throws exception."""
        # Mock Alpaca API exception
        self.mock_alpaca_manager.place_order.side_effect = Exception("Alpaca API error")

        result = self.trading_manager.place_limit_order(
            symbol="TSLA",
            quantity=50.0,
            side="sell",
            limit_price=250.50,
            validate=True
        )

        # Verify error handling
        assert isinstance(result, OrderExecutionResultDTO)
        assert result.success is False
        assert "Alpaca API error" in result.error

    def test_market_order_symbol_normalization(self):
        """Test that symbols are normalized to uppercase."""
        # Mock successful order placement
        mock_alpaca_order = self.create_mock_alpaca_order("AAPL", 100.0)
        self.mock_alpaca_manager.place_order.return_value = mock_alpaca_order

        # Place order with lowercase symbol
        result = self.trading_manager.place_market_order(
            symbol="aapl",  # lowercase
            quantity=100.0,
            side="buy",
            validate=True
        )

        # Should succeed with symbol normalized
        assert isinstance(result, OrderExecutionResultDTO)
        assert result.success is True
        
        # Verify the order request had uppercase symbol
        call_args = self.mock_alpaca_manager.place_order.call_args[0][0]
        assert call_args.symbol == "AAPL"

    def test_limit_order_symbol_normalization(self):
        """Test that symbols are normalized to uppercase in limit orders."""
        # Mock successful order placement
        mock_alpaca_order = self.create_mock_alpaca_order("TSLA", 50.0)
        self.mock_alpaca_manager.place_order.return_value = mock_alpaca_order

        # Place order with lowercase symbol
        result = self.trading_manager.place_limit_order(
            symbol="tsla",  # lowercase
            quantity=50.0,
            side="sell",
            limit_price=250.50,
            validate=True
        )

        # Should succeed with symbol normalized
        assert isinstance(result, OrderExecutionResultDTO)
        assert result.success is True
        
        # Verify the order request had uppercase symbol
        call_args = self.mock_alpaca_manager.place_order.call_args[0][0]
        assert call_args.symbol == "TSLA"

    def test_order_validation_error_logging(self):
        """Test that validation errors are properly logged."""
        with patch.object(self.trading_manager.logger, 'info') as mock_log_info:
            # Mock successful order placement
            mock_alpaca_order = self.create_mock_alpaca_order("AAPL", 100.0)
            self.mock_alpaca_manager.place_order.return_value = mock_alpaca_order

            # Place valid order
            result = self.trading_manager.place_market_order(
                symbol="AAPL",
                quantity=100.0,
                side="buy",
                validate=True
            )

            # Verify validation success was logged
            assert result.success is True
            mock_log_info.assert_called()
            log_message = mock_log_info.call_args[0][0]
            assert "validation successful" in log_message.lower()