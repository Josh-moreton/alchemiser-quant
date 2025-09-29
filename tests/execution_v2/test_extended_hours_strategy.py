#!/usr/bin/env python3
"""Business Unit: execution | Status: current.

Tests for extended hours execution strategy.

Validates the dedicated extended hours strategy that places orders
at bid/ask prices without repricing or complex logic.
"""

import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from the_alchemiser.execution_v2.core.extended_hours_strategy import ExtendedHoursExecutionStrategy
from the_alchemiser.execution_v2.core.smart_execution_strategy import SmartOrderRequest
from the_alchemiser.shared.types.market_data import QuoteModel


class TestExtendedHoursExecutionStrategy:
    """Test extended hours execution strategy."""

    def test_is_extended_hours_active_when_enabled(self):
        """Test that extended hours is detected when enabled."""
        # Mock alpaca manager with extended hours enabled
        mock_alpaca_manager = MagicMock()
        mock_alpaca_manager.extended_hours_enabled = True
        
        strategy = ExtendedHoursExecutionStrategy(mock_alpaca_manager)
        
        assert strategy.is_extended_hours_active() is True

    def test_is_extended_hours_active_when_disabled(self):
        """Test that extended hours is not detected when disabled."""
        # Mock alpaca manager with extended hours disabled
        mock_alpaca_manager = MagicMock()
        mock_alpaca_manager.extended_hours_enabled = False
        
        strategy = ExtendedHoursExecutionStrategy(mock_alpaca_manager)
        
        assert strategy.is_extended_hours_active() is False

    def test_is_extended_hours_active_when_not_set(self):
        """Test that extended hours defaults to disabled when not set."""
        # Mock alpaca manager without extended_hours_enabled attribute
        mock_alpaca_manager = MagicMock()
        del mock_alpaca_manager.extended_hours_enabled
        
        strategy = ExtendedHoursExecutionStrategy(mock_alpaca_manager)
        
        assert strategy.is_extended_hours_active() is False

    @pytest.mark.asyncio
    async def test_place_buy_order_at_ask_price(self):
        """Test that buy orders are placed at ask price."""
        # Mock alpaca manager
        mock_alpaca_manager = MagicMock()
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.order_id = "test_order_123"
        mock_alpaca_manager.place_limit_order.return_value = mock_result
        
        strategy = ExtendedHoursExecutionStrategy(mock_alpaca_manager)
        
        # Mock quote with bid/ask prices
        mock_quote = QuoteModel(
            symbol="AAPL",
            bid_price=150.50,
            ask_price=150.60,
            bid_size=100.0,
            ask_size=200.0,
            timestamp=None,
        )
        
        # Mock _get_current_quote to return our test quote
        strategy._get_current_quote = AsyncMock(return_value=mock_quote)
        
        # Create buy order request
        request = SmartOrderRequest(
            symbol="AAPL",
            side="BUY",
            quantity=Decimal("10"),
            correlation_id="test_corr_123",
        )
        
        # Execute the order
        result = await strategy.place_extended_hours_order(request)
        
        # Verify the order was placed at ask price
        assert result.success is True
        assert result.order_id == "test_order_123"
        assert result.final_price == Decimal("150.60")  # Should be ask price
        assert result.execution_strategy == "extended_hours_bid_ask"
        assert result.repegs_used == 0  # No repricing
        
        # Verify limit order was called with ask price
        mock_alpaca_manager.place_limit_order.assert_called_once_with(
            "AAPL", "buy", 10.0, 150.60, "day"
        )

    @pytest.mark.asyncio
    async def test_place_sell_order_at_bid_price(self):
        """Test that sell orders are placed at bid price."""
        # Mock alpaca manager
        mock_alpaca_manager = MagicMock()
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.order_id = "test_order_456"
        mock_alpaca_manager.place_limit_order.return_value = mock_result
        
        strategy = ExtendedHoursExecutionStrategy(mock_alpaca_manager)
        
        # Mock quote with bid/ask prices
        mock_quote = QuoteModel(
            symbol="TSLA",
            bid_price=200.25,
            ask_price=200.35,
            bid_size=150.0,
            ask_size=250.0,
            timestamp=None,
        )
        
        # Mock _get_current_quote to return our test quote
        strategy._get_current_quote = AsyncMock(return_value=mock_quote)
        
        # Create sell order request
        request = SmartOrderRequest(
            symbol="TSLA",
            side="SELL",
            quantity=Decimal("5"),
            correlation_id="test_corr_456",
        )
        
        # Execute the order
        result = await strategy.place_extended_hours_order(request)
        
        # Verify the order was placed at bid price
        assert result.success is True
        assert result.order_id == "test_order_456"
        assert result.final_price == Decimal("200.25")  # Should be bid price
        assert result.execution_strategy == "extended_hours_bid_ask"
        assert result.repegs_used == 0  # No repricing
        
        # Verify limit order was called with bid price
        mock_alpaca_manager.place_limit_order.assert_called_once_with(
            "TSLA", "sell", 5.0, 200.25, "day"
        )

    @pytest.mark.asyncio
    async def test_order_failure_when_no_quote_available(self):
        """Test that order fails gracefully when no quote is available."""
        # Mock alpaca manager
        mock_alpaca_manager = MagicMock()
        
        strategy = ExtendedHoursExecutionStrategy(mock_alpaca_manager)
        
        # Mock _get_current_quote to return None (no quote available)
        strategy._get_current_quote = AsyncMock(return_value=None)
        
        # Create order request
        request = SmartOrderRequest(
            symbol="NVDA",
            side="BUY",
            quantity=Decimal("2"),
            correlation_id="test_corr_789",
        )
        
        # Execute the order
        result = await strategy.place_extended_hours_order(request)
        
        # Verify the order failed with appropriate error
        assert result.success is False
        assert "Unable to get quote for NVDA during extended hours" in result.error_message
        assert result.execution_strategy == "extended_hours_no_quote"
        
        # Verify no order was placed
        mock_alpaca_manager.place_limit_order.assert_not_called()

    @pytest.mark.asyncio
    async def test_order_failure_when_limit_order_fails(self):
        """Test that order failure is handled when limit order placement fails."""
        # Mock alpaca manager
        mock_alpaca_manager = MagicMock()
        mock_result = MagicMock()
        mock_result.success = False
        mock_result.error = "Insufficient buying power"
        mock_alpaca_manager.place_limit_order.return_value = mock_result
        
        strategy = ExtendedHoursExecutionStrategy(mock_alpaca_manager)
        
        # Mock quote
        mock_quote = QuoteModel(
            symbol="SPY",
            bid_price=400.00,
            ask_price=400.10,
            bid_size=500.0,
            ask_size=600.0,
            timestamp=None,
        )
        
        # Mock _get_current_quote to return our test quote
        strategy._get_current_quote = AsyncMock(return_value=mock_quote)
        
        # Create order request
        request = SmartOrderRequest(
            symbol="SPY",
            side="BUY",
            quantity=Decimal("100"),
            correlation_id="test_corr_fail",
        )
        
        # Execute the order
        result = await strategy.place_extended_hours_order(request)
        
        # Verify the order failed with appropriate error
        assert result.success is False
        assert result.error_message == "Insufficient buying power"
        assert result.execution_strategy == "extended_hours_placement_failed"

    @pytest.mark.asyncio
    async def test_price_quantization_to_cents(self):
        """Test that prices are properly quantized to cents."""
        # Mock alpaca manager
        mock_alpaca_manager = MagicMock()
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.order_id = "test_quantize"
        mock_alpaca_manager.place_limit_order.return_value = mock_result
        
        strategy = ExtendedHoursExecutionStrategy(mock_alpaca_manager)
        
        # Mock quote with prices that need quantization
        mock_quote = QuoteModel(
            symbol="QQQ",
            bid_price=350.12345,  # Should be quantized to 350.12
            ask_price=350.23678,  # Should be quantized to 350.24 (rounded up)
            bid_size=300.0,
            ask_size=400.0,
            timestamp=None,
        )
        
        # Mock _get_current_quote to return our test quote
        strategy._get_current_quote = AsyncMock(return_value=mock_quote)
        
        # Test buy order (should use ask price, quantized)
        buy_request = SmartOrderRequest(
            symbol="QQQ",
            side="BUY",
            quantity=Decimal("1"),
            correlation_id="test_quantize_buy",
        )
        
        buy_result = await strategy.place_extended_hours_order(buy_request)
        
        # Verify buy used quantized ask price
        assert buy_result.success is True
        assert buy_result.final_price == Decimal("350.24")  # Quantized ask
        
        # Test sell order (should use bid price, quantized)
        sell_request = SmartOrderRequest(
            symbol="QQQ",
            side="SELL",
            quantity=Decimal("1"),
            correlation_id="test_quantize_sell",
        )
        
        sell_result = await strategy.place_extended_hours_order(sell_request)
        
        # Verify sell used quantized bid price
        assert sell_result.success is True
        assert sell_result.final_price == Decimal("350.12")  # Quantized bid