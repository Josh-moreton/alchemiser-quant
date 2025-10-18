"""Business Unit: execution | Status: current

Test market fallback for cancelled/expired orders with unfilled quantities.

Tests verify the fix for issue #1552 where orders cancelled or expired by the broker
were not triggering market order fallback, leaving unfilled quantities.
"""

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, Mock

import pytest

from the_alchemiser.execution_v2.core.order_monitor import OrderMonitor
from the_alchemiser.execution_v2.core.smart_execution_strategy import (
    ExecutionConfig,
    SmartOrderRequest,
    SmartOrderResult,
)
from the_alchemiser.execution_v2.models.execution_result import OrderResult


def _make_order_result(
    symbol: str,
    *,
    action: str,
    shares: Decimal,
    trade_amount: Decimal,
    success: bool,
    price: Decimal | None = None,
    order_id: str | None = None,
    error_message: str | None = None,
) -> OrderResult:
    """Create an OrderResult for testing."""
    return OrderResult(
        symbol=symbol,
        action=action,
        trade_amount=trade_amount,
        shares=shares,
        price=price,
        order_id=order_id,
        success=success,
        error_message=error_message,
        timestamp=datetime.now(UTC),
        order_type="MARKET",  # Default to MARKET for tests
        filled_at=datetime.now(UTC) if success and price else None,  # Set filled_at if successful
    )


@pytest.mark.asyncio
class TestMarketFallbackCancelledOrders:
    """Test market fallback for cancelled/expired orders."""

    async def test_cancelled_order_with_unfilled_quantity_triggers_market_fallback(self):
        """Test that a cancelled order with unfilled quantity triggers market fallback."""
        # Setup
        config = ExecutionConfig()
        mock_smart_strategy = Mock()
        mock_smart_strategy.order_tracker = Mock()
        mock_smart_strategy.order_tracker.get_active_orders = Mock(return_value={})

        # Mock order that was placed but then cancelled with unfilled quantity
        order_id = "test-order-123"
        mock_smart_strategy.alpaca_manager = Mock()
        mock_smart_strategy.alpaca_manager._check_order_completion_status = Mock(
            return_value="CANCELED"
        )

        # Mock order result showing partial fill
        mock_order_result = Mock()
        mock_order_result.filled_qty = 3.0  # Only 3 out of 10 filled
        mock_smart_strategy.alpaca_manager.get_order_execution_result = Mock(
            return_value=mock_order_result
        )

        # Mock escalation
        mock_escalation_result = SmartOrderResult(
            success=True,
            order_id="market-order-456",
            final_price=Decimal("187.50"),
            execution_strategy="market_escalation",
            metadata={"original_order_id": order_id},
        )
        mock_smart_strategy.repeg_manager = Mock()
        mock_smart_strategy.repeg_manager._escalate_to_market = AsyncMock(
            return_value=mock_escalation_result
        )

        monitor = OrderMonitor(mock_smart_strategy, config)

        # Create order with 10 shares requested
        orders = [
            _make_order_result(
                "BWXT",
                action="BUY",
                shares=Decimal("10"),
                trade_amount=Decimal("1872.00"),
                success=True,
                price=Decimal("187.20"),
                order_id=order_id,
            )
        ]

        # Act
        replacement_map = await monitor._final_escalation_if_active_orders(
            "BUY", "test-corr-id", orders=orders
        )

        # Assert
        assert replacement_map == {order_id: "market-order-456"}
        mock_smart_strategy.repeg_manager._escalate_to_market.assert_called_once()

        # Verify the request had correct remaining quantity (10 - 3 = 7)
        call_args = mock_smart_strategy.repeg_manager._escalate_to_market.call_args
        request = call_args[0][1]
        assert request.quantity == Decimal("7")
        assert request.symbol == "BWXT"
        assert request.side == "BUY"

    async def test_expired_order_with_zero_fills_triggers_market_fallback(self):
        """Test that an expired order with zero fills triggers market fallback."""
        # Setup
        config = ExecutionConfig()
        mock_smart_strategy = Mock()
        mock_smart_strategy.order_tracker = Mock()
        mock_smart_strategy.order_tracker.get_active_orders = Mock(return_value={})

        order_id = "test-order-789"
        mock_smart_strategy.alpaca_manager = Mock()
        mock_smart_strategy.alpaca_manager._check_order_completion_status = Mock(
            return_value="EXPIRED"
        )

        # Mock order result showing no fills
        mock_order_result = Mock()
        mock_order_result.filled_qty = 0
        mock_smart_strategy.alpaca_manager.get_order_execution_result = Mock(
            return_value=mock_order_result
        )

        # Mock escalation
        mock_escalation_result = SmartOrderResult(
            success=True,
            order_id="market-order-999",
            final_price=Decimal("1.05"),
            execution_strategy="market_escalation",
            metadata={"original_order_id": order_id},
        )
        mock_smart_strategy.repeg_manager = Mock()
        mock_smart_strategy.repeg_manager._escalate_to_market = AsyncMock(
            return_value=mock_escalation_result
        )

        monitor = OrderMonitor(mock_smart_strategy, config)

        orders = [
            _make_order_result(
                "LEU",
                action="BUY",
                shares=Decimal("5"),
                trade_amount=Decimal("5.00"),
                success=True,
                price=Decimal("1.00"),
                order_id=order_id,
            )
        ]

        # Act
        replacement_map = await monitor._final_escalation_if_active_orders(
            "BUY", "test-corr-id", orders=orders
        )

        # Assert
        assert replacement_map == {order_id: "market-order-999"}

        # Verify the request had full quantity (5 - 0 = 5)
        call_args = mock_smart_strategy.repeg_manager._escalate_to_market.call_args
        request = call_args[0][1]
        assert request.quantity == Decimal("5")

    async def test_rejected_order_with_unfilled_quantity_triggers_market_fallback(self):
        """Test that a rejected order with unfilled quantity triggers market fallback."""
        # Setup
        config = ExecutionConfig()
        mock_smart_strategy = Mock()
        mock_smart_strategy.order_tracker = Mock()
        mock_smart_strategy.order_tracker.get_active_orders = Mock(return_value={})

        order_id = "test-order-rejected"
        mock_smart_strategy.alpaca_manager = Mock()
        mock_smart_strategy.alpaca_manager._check_order_completion_status = Mock(
            return_value="REJECTED"
        )

        mock_order_result = Mock()
        mock_order_result.filled_qty = 0
        mock_smart_strategy.alpaca_manager.get_order_execution_result = Mock(
            return_value=mock_order_result
        )

        mock_escalation_result = SmartOrderResult(
            success=True,
            order_id="market-order-rejected",
            final_price=Decimal("50.00"),
            execution_strategy="market_escalation",
            metadata={"original_order_id": order_id},
        )
        mock_smart_strategy.repeg_manager = Mock()
        mock_smart_strategy.repeg_manager._escalate_to_market = AsyncMock(
            return_value=mock_escalation_result
        )

        monitor = OrderMonitor(mock_smart_strategy, config)

        orders = [
            _make_order_result(
                "XYZ",
                action="SELL",
                shares=Decimal("20"),
                trade_amount=Decimal("1000.00"),
                success=True,
                price=Decimal("50.00"),
                order_id=order_id,
            )
        ]

        # Act
        replacement_map = await monitor._final_escalation_if_active_orders(
            "SELL", "test-corr-id", orders=orders
        )

        # Assert
        assert replacement_map == {order_id: "market-order-rejected"}

    async def test_fully_filled_cancelled_order_does_not_trigger_fallback(self):
        """Test that a fully filled order (even if cancelled status) doesn't trigger fallback."""
        # Setup
        config = ExecutionConfig()
        mock_smart_strategy = Mock()
        mock_smart_strategy.order_tracker = Mock()
        mock_smart_strategy.order_tracker.get_active_orders = Mock(return_value={})

        order_id = "test-order-filled"
        mock_smart_strategy.alpaca_manager = Mock()
        mock_smart_strategy.alpaca_manager._check_order_completion_status = Mock(
            return_value="CANCELED"
        )

        # Mock order result showing complete fill
        mock_order_result = Mock()
        mock_order_result.filled_qty = 10.0  # Fully filled
        mock_smart_strategy.alpaca_manager.get_order_execution_result = Mock(
            return_value=mock_order_result
        )

        mock_smart_strategy.repeg_manager = Mock()
        mock_smart_strategy.repeg_manager._escalate_to_market = AsyncMock()

        monitor = OrderMonitor(mock_smart_strategy, config)

        orders = [
            _make_order_result(
                "ABC",
                action="BUY",
                shares=Decimal("10"),
                trade_amount=Decimal("100.00"),
                success=True,
                price=Decimal("10.00"),
                order_id=order_id,
            )
        ]

        # Act
        replacement_map = await monitor._final_escalation_if_active_orders(
            "BUY", "test-corr-id", orders=orders
        )

        # Assert - no escalation should occur
        assert replacement_map == {}
        mock_smart_strategy.repeg_manager._escalate_to_market.assert_not_called()

    async def test_filled_status_order_does_not_trigger_fallback(self):
        """Test that an order with FILLED status doesn't trigger fallback."""
        # Setup
        config = ExecutionConfig()
        mock_smart_strategy = Mock()
        mock_smart_strategy.order_tracker = Mock()
        mock_smart_strategy.order_tracker.get_active_orders = Mock(return_value={})

        order_id = "test-order-filled-status"
        mock_smart_strategy.alpaca_manager = Mock()
        mock_smart_strategy.alpaca_manager._check_order_completion_status = Mock(
            return_value="FILLED"
        )

        mock_smart_strategy.repeg_manager = Mock()
        mock_smart_strategy.repeg_manager._escalate_to_market = AsyncMock()

        monitor = OrderMonitor(mock_smart_strategy, config)

        orders = [
            _make_order_result(
                "DEF",
                action="BUY",
                shares=Decimal("5"),
                trade_amount=Decimal("50.00"),
                success=True,
                price=Decimal("10.00"),
                order_id=order_id,
            )
        ]

        # Act
        replacement_map = await monitor._final_escalation_if_active_orders(
            "BUY", "test-corr-id", orders=orders
        )

        # Assert - no escalation should occur for filled orders
        assert replacement_map == {}
        mock_smart_strategy.repeg_manager._escalate_to_market.assert_not_called()

    async def test_handles_missing_order_gracefully(self):
        """Test that missing/not found orders are handled gracefully."""
        # Setup
        config = ExecutionConfig()
        mock_smart_strategy = Mock()
        mock_smart_strategy.order_tracker = Mock()
        mock_smart_strategy.order_tracker.get_active_orders = Mock(return_value={})

        order_id = "test-order-missing"
        mock_smart_strategy.alpaca_manager = Mock()
        mock_smart_strategy.alpaca_manager._check_order_completion_status = Mock(
            return_value="CANCELED"
        )

        # Simulate order not found error
        mock_smart_strategy.alpaca_manager.get_order_execution_result = Mock(
            side_effect=AttributeError("Order not found")
        )

        mock_smart_strategy.repeg_manager = Mock()
        mock_smart_strategy.repeg_manager._escalate_to_market = AsyncMock()

        monitor = OrderMonitor(mock_smart_strategy, config)

        orders = [
            _make_order_result(
                "GHI",
                action="BUY",
                shares=Decimal("10"),
                trade_amount=Decimal("100.00"),
                success=True,
                price=Decimal("10.00"),
                order_id=order_id,
            )
        ]

        # Act - should not raise exception
        replacement_map = await monitor._final_escalation_if_active_orders(
            "BUY", "test-corr-id", orders=orders
        )

        # Assert - no escalation due to error, but doesn't crash
        assert replacement_map == {}

    async def test_handles_api_error_gracefully(self):
        """Test that API errors are handled gracefully with proper logging."""
        # Setup
        config = ExecutionConfig()
        mock_smart_strategy = Mock()
        mock_smart_strategy.order_tracker = Mock()
        mock_smart_strategy.order_tracker.get_active_orders = Mock(return_value={})

        order_id = "test-order-api-error"
        mock_smart_strategy.alpaca_manager = Mock()
        mock_smart_strategy.alpaca_manager._check_order_completion_status = Mock(
            return_value="CANCELED"
        )

        # Simulate unexpected API error
        mock_smart_strategy.alpaca_manager.get_order_execution_result = Mock(
            side_effect=RuntimeError("API connection failed")
        )

        mock_smart_strategy.repeg_manager = Mock()
        mock_smart_strategy.repeg_manager._escalate_to_market = AsyncMock()

        monitor = OrderMonitor(mock_smart_strategy, config)

        orders = [
            _make_order_result(
                "JKL",
                action="BUY",
                shares=Decimal("10"),
                trade_amount=Decimal("100.00"),
                success=True,
                price=Decimal("10.00"),
                order_id=order_id,
            )
        ]

        # Act - should not raise exception
        replacement_map = await monitor._final_escalation_if_active_orders(
            "BUY", "test-corr-id", orders=orders
        )

        # Assert - no escalation due to error, but doesn't crash
        assert replacement_map == {}

    async def test_active_orders_and_cancelled_orders_both_escalated(self):
        """Test that both active orders and cancelled orders are escalated."""
        # Setup
        config = ExecutionConfig()
        mock_smart_strategy = Mock()

        # Active order still in tracking
        active_order_id = "active-order-1"
        active_request = SmartOrderRequest(
            symbol="ACTIVE",
            side="BUY",
            quantity=Decimal("5"),
            correlation_id="test-corr-id",
        )
        mock_smart_strategy.order_tracker = Mock()
        mock_smart_strategy.order_tracker.get_active_orders = Mock(
            return_value={active_order_id: active_request}
        )

        # Cancelled order no longer in tracking
        cancelled_order_id = "cancelled-order-2"
        mock_smart_strategy.alpaca_manager = Mock()
        mock_smart_strategy.alpaca_manager._check_order_completion_status = Mock(
            return_value="CANCELED"
        )

        mock_order_result = Mock()
        mock_order_result.filled_qty = 0
        mock_smart_strategy.alpaca_manager.get_order_execution_result = Mock(
            return_value=mock_order_result
        )

        # Mock escalation for both
        mock_result_1 = SmartOrderResult(
            success=True,
            order_id="market-active",
            final_price=Decimal("10.00"),
            execution_strategy="market_escalation",
            metadata={"original_order_id": active_order_id},
        )
        mock_result_2 = SmartOrderResult(
            success=True,
            order_id="market-cancelled",
            final_price=Decimal("20.00"),
            execution_strategy="market_escalation",
            metadata={"original_order_id": cancelled_order_id},
        )
        mock_smart_strategy.repeg_manager = Mock()
        mock_smart_strategy.repeg_manager._escalate_to_market = AsyncMock(
            side_effect=[mock_result_1, mock_result_2]
        )

        monitor = OrderMonitor(mock_smart_strategy, config)

        orders = [
            _make_order_result(
                "CANCELLED",
                action="BUY",
                shares=Decimal("10"),
                trade_amount=Decimal("200.00"),
                success=True,
                price=Decimal("20.00"),
                order_id=cancelled_order_id,
            )
        ]

        # Act
        replacement_map = await monitor._final_escalation_if_active_orders(
            "BUY", "test-corr-id", orders=orders
        )

        # Assert - both orders escalated
        assert replacement_map == {
            active_order_id: "market-active",
            cancelled_order_id: "market-cancelled",
        }
        assert mock_smart_strategy.repeg_manager._escalate_to_market.call_count == 2

    async def test_decimal_precision_in_quantity_calculation(self):
        """Test that Decimal precision is maintained in quantity calculations."""
        # Setup
        config = ExecutionConfig()
        mock_smart_strategy = Mock()
        mock_smart_strategy.order_tracker = Mock()
        mock_smart_strategy.order_tracker.get_active_orders = Mock(return_value={})

        order_id = "test-order-decimal"
        mock_smart_strategy.alpaca_manager = Mock()
        mock_smart_strategy.alpaca_manager._check_order_completion_status = Mock(
            return_value="CANCELED"
        )

        # Mock partial fill with decimal quantity
        mock_order_result = Mock()
        mock_order_result.filled_qty = 7.333  # Fractional shares filled
        mock_smart_strategy.alpaca_manager.get_order_execution_result = Mock(
            return_value=mock_order_result
        )

        mock_escalation_result = SmartOrderResult(
            success=True,
            order_id="market-order-decimal",
            final_price=Decimal("50.00"),
            execution_strategy="market_escalation",
            metadata={"original_order_id": order_id},
        )
        mock_smart_strategy.repeg_manager = Mock()
        mock_smart_strategy.repeg_manager._escalate_to_market = AsyncMock(
            return_value=mock_escalation_result
        )

        monitor = OrderMonitor(mock_smart_strategy, config)

        orders = [
            _make_order_result(
                "DECIMAL",
                action="BUY",
                shares=Decimal("10.5"),  # Fractional shares ordered
                trade_amount=Decimal("525.00"),
                success=True,
                price=Decimal("50.00"),
                order_id=order_id,
            )
        ]

        # Act
        replacement_map = await monitor._final_escalation_if_active_orders(
            "BUY", "test-corr-id", orders=orders
        )

        # Assert
        assert replacement_map == {order_id: "market-order-decimal"}

        # Verify precise decimal calculation: 10.5 - 7.333 = 3.167
        call_args = mock_smart_strategy.repeg_manager._escalate_to_market.call_args
        request = call_args[0][1]
        assert request.quantity == Decimal("10.5") - Decimal("7.333")
        assert request.quantity == Decimal("3.167")
