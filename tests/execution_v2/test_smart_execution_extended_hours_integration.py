#!/usr/bin/env python3
"""Business Unit: execution | Status: current.

Integration tests for smart execution strategy with extended hours support.

Tests the integration between SmartExecutionStrategy and ExtendedHoursExecutionStrategy
to ensure extended hours orders are properly routed to the simplified strategy.
"""

import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from the_alchemiser.execution_v2.core.smart_execution_strategy import (
    SmartExecutionStrategy,
    SmartOrderRequest,
)
from the_alchemiser.shared.types.market_data import QuoteModel


class TestSmartExecutionWithExtendedHours:
    """Test smart execution strategy integration with extended hours."""

    @pytest.mark.asyncio
    async def test_extended_hours_strategy_used_when_enabled(self):
        """Test that extended hours strategy is used when extended hours are enabled."""
        # Mock alpaca manager with extended hours enabled
        mock_alpaca_manager = MagicMock()
        mock_alpaca_manager.extended_hours_enabled = True
        
        # Mock successful order result
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.order_id = "extended_hours_order_123"
        mock_alpaca_manager.place_limit_order.return_value = mock_result
        
        # Create smart execution strategy
        strategy = SmartExecutionStrategy(
            alpaca_manager=mock_alpaca_manager,
            pricing_service=None,
            config=None,
        )
        
        # Mock the extended hours strategy's quote method
        mock_quote = QuoteModel(
            symbol="AAPL",
            bid_price=150.50,
            ask_price=150.60,
            bid_size=100.0,
            ask_size=200.0,
            timestamp=None,
        )
        strategy.extended_hours_strategy._get_current_quote = AsyncMock(return_value=mock_quote)
        
        # Create order request
        request = SmartOrderRequest(
            symbol="AAPL",
            side="BUY",
            quantity=Decimal("10"),
            correlation_id="test_extended_hours",
        )
        
        # Execute the order
        result = await strategy.place_smart_order(request)
        
        # Verify that extended hours strategy was used
        assert result.success is True
        assert result.order_id == "extended_hours_order_123"
        assert result.execution_strategy == "extended_hours_bid_ask"
        assert result.final_price == Decimal("150.60")  # Ask price for buy
        assert result.repegs_used == 0  # No repricing in extended hours
        
        # Verify limit order was placed at ask price for buy
        mock_alpaca_manager.place_limit_order.assert_called_once_with(
            "AAPL", "buy", 10.0, 150.60, "day"
        )

    @pytest.mark.asyncio
    async def test_regular_strategy_used_when_extended_hours_disabled(self):
        """Test that normal smart execution is used when extended hours are disabled."""
        # Mock alpaca manager with extended hours disabled
        mock_alpaca_manager = MagicMock()
        mock_alpaca_manager.extended_hours_enabled = False
        
        # Create smart execution strategy
        strategy = SmartExecutionStrategy(
            alpaca_manager=mock_alpaca_manager,
            pricing_service=None,
            config=None,
        )
        
        # Mock the validation to fail so we can easily verify we're in normal flow
        # (avoiding the complex setup needed for full smart execution)
        mock_validator = MagicMock()
        mock_validation_result = MagicMock()
        mock_validation_result.is_valid = False
        mock_validation_result.error_message = "Test validation failure"
        mock_validator.validate_order.return_value = mock_validation_result
        strategy.validator = mock_validator
        
        # Create order request
        request = SmartOrderRequest(
            symbol="AAPL",
            side="BUY",
            quantity=Decimal("10"),
            correlation_id="test_regular_hours",
        )
        
        # Execute the order
        result = await strategy.place_smart_order(request)
        
        # Verify that normal smart execution validation was called
        assert result.success is False
        assert result.execution_strategy == "validation_failed"
        assert "Test validation failure" in result.error_message
        
        # Verify validator was called (indicating normal flow)
        mock_validator.validate_order.assert_called_once()

    @pytest.mark.asyncio
    async def test_extended_hours_sell_order_uses_bid(self):
        """Test that extended hours sell orders use bid price."""
        # Mock alpaca manager with extended hours enabled
        mock_alpaca_manager = MagicMock()
        mock_alpaca_manager.extended_hours_enabled = True
        
        # Mock successful order result
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.order_id = "extended_sell_order_456"
        mock_alpaca_manager.place_limit_order.return_value = mock_result
        
        # Create smart execution strategy
        strategy = SmartExecutionStrategy(
            alpaca_manager=mock_alpaca_manager,
            pricing_service=None,
            config=None,
        )
        
        # Mock the extended hours strategy's quote method
        mock_quote = QuoteModel(
            symbol="TSLA",
            bid_price=200.75,
            ask_price=200.85,
            bid_size=150.0,
            ask_size=250.0,
            timestamp=None,
        )
        strategy.extended_hours_strategy._get_current_quote = AsyncMock(return_value=mock_quote)
        
        # Create sell order request
        request = SmartOrderRequest(
            symbol="TSLA",
            side="SELL",
            quantity=Decimal("5"),
            correlation_id="test_extended_hours_sell",
        )
        
        # Execute the order
        result = await strategy.place_smart_order(request)
        
        # Verify that extended hours strategy was used with bid price for sell
        assert result.success is True
        assert result.order_id == "extended_sell_order_456"
        assert result.execution_strategy == "extended_hours_bid_ask"
        assert result.final_price == Decimal("200.75")  # Bid price for sell
        assert result.repegs_used == 0  # No repricing in extended hours
        
        # Verify limit order was placed at bid price for sell
        mock_alpaca_manager.place_limit_order.assert_called_once_with(
            "TSLA", "sell", 5.0, 200.75, "day"
        )

    @pytest.mark.asyncio
    async def test_extended_hours_failure_handling(self):
        """Test that extended hours strategy failures are properly handled."""
        # Mock alpaca manager with extended hours enabled
        mock_alpaca_manager = MagicMock()
        mock_alpaca_manager.extended_hours_enabled = True
        
        # Create smart execution strategy
        strategy = SmartExecutionStrategy(
            alpaca_manager=mock_alpaca_manager,
            pricing_service=None,
            config=None,
        )
        
        # Mock the extended hours strategy's quote method to return None (no quote)
        strategy.extended_hours_strategy._get_current_quote = AsyncMock(return_value=None)
        
        # Create order request
        request = SmartOrderRequest(
            symbol="NVDA",
            side="BUY",
            quantity=Decimal("3"),
            correlation_id="test_extended_hours_failure",
        )
        
        # Execute the order
        result = await strategy.place_smart_order(request)
        
        # Verify that extended hours strategy failure was handled
        assert result.success is False
        assert result.execution_strategy == "extended_hours_no_quote"
        assert "Unable to get quote for NVDA during extended hours" in result.error_message
        
        # Verify no order was placed
        mock_alpaca_manager.place_limit_order.assert_not_called()

    def test_extended_hours_strategy_initialization(self):
        """Test that extended hours strategy is properly initialized."""
        # Mock alpaca manager
        mock_alpaca_manager = MagicMock()
        
        # Create smart execution strategy
        strategy = SmartExecutionStrategy(
            alpaca_manager=mock_alpaca_manager,
            pricing_service=None,
            config=None,
        )
        
        # Verify extended hours strategy was initialized
        assert hasattr(strategy, 'extended_hours_strategy')
        assert strategy.extended_hours_strategy is not None
        assert strategy.extended_hours_strategy.alpaca_manager is mock_alpaca_manager