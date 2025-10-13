"""Business Unit: execution | Status: current.

Comprehensive unit tests for OrderMonitor class.

Tests cover order monitoring, re-pegging, escalation, and edge cases for the
order monitoring system. These tests validate proper handling of cancelled orders,
partial fills, market escalation, and configuration management.
"""

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch

import pytest

from the_alchemiser.execution_v2.core.order_monitor import (
    DEFAULT_FILL_WAIT_SECONDS,
    DEFAULT_MAX_REPEGS,
    DEFAULT_MAX_TOTAL_WAIT_SECONDS,
    DEFAULT_WAIT_BETWEEN_CHECKS,
    OrderMonitor,
)
from the_alchemiser.execution_v2.core.smart_execution_strategy import (
    ExecutionConfig,
    SmartOrderRequest,
    SmartOrderResult,
)
from the_alchemiser.execution_v2.models.execution_result import OrderResult
from the_alchemiser.shared.errors.trading_errors import OrderError


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
    """Create an OrderResult for testing.

    Args:
        symbol: Trading symbol
        action: BUY or SELL
        shares: Number of shares
        trade_amount: Dollar amount
        success: Whether order succeeded
        price: Execution price
        order_id: Order ID
        error_message: Error message if failed

    Returns:
        OrderResult instance

    """
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
        order_type="MARKET",
        filled_at=datetime.now(UTC) if success and price else None,
    )


@pytest.mark.asyncio
class TestOrderMonitorConfiguration:
    """Test configuration management and defaults."""

    def test_default_configuration_when_no_execution_config(self):
        """Test that default configuration is used when ExecutionConfig is None."""
        monitor = OrderMonitor(smart_strategy=None, execution_config=None)
        config = monitor._get_repeg_monitoring_config()

        assert config["max_repegs"] == DEFAULT_MAX_REPEGS
        assert config["fill_wait_seconds"] == DEFAULT_FILL_WAIT_SECONDS
        assert config["wait_between_checks"] == DEFAULT_WAIT_BETWEEN_CHECKS
        assert config["max_total_wait"] == DEFAULT_MAX_TOTAL_WAIT_SECONDS

    def test_configuration_from_execution_config(self):
        """Test that configuration is derived from ExecutionConfig when provided."""
        exec_config = ExecutionConfig()
        exec_config.max_repegs_per_order = 5
        exec_config.fill_wait_seconds = 20
        exec_config.order_placement_timeout_seconds = 45

        monitor = OrderMonitor(smart_strategy=None, execution_config=exec_config)
        config = monitor._get_repeg_monitoring_config()

        assert config["max_repegs"] == 5
        assert config["fill_wait_seconds"] == 20
        # wait_between_checks should be dynamically calculated
        assert config["wait_between_checks"] in range(1, 6)
        # max_total_wait should be calculated based on other params
        assert config["max_total_wait"] > 60

    def test_check_interval_calculation(self):
        """Test the check interval calculation logic."""
        monitor = OrderMonitor(smart_strategy=None, execution_config=None)

        # Test with 10 second wait -> should be 2 checks
        assert monitor._calculate_check_interval(10) == 2

        # Test with 25 second wait -> should be 5 checks (max)
        assert monitor._calculate_check_interval(25) == 5

        # Test with 5 second wait -> should be 1 check (min)
        assert monitor._calculate_check_interval(5) == 1

        # Test with 0 or negative -> should be 1 (min)
        assert monitor._calculate_check_interval(0) == 1


@pytest.mark.asyncio
class TestOrderMonitorBasicOperations:
    """Test basic monitoring operations."""

    async def test_monitor_returns_orders_when_no_smart_strategy(self):
        """Test that monitoring returns original orders when smart_strategy is None."""
        monitor = OrderMonitor(smart_strategy=None, execution_config=None)
        orders = [
            _make_order_result(
                "AAPL",
                action="BUY",
                shares=Decimal("10"),
                trade_amount=Decimal("1500"),
                success=True,
                order_id="test-123",
            )
        ]

        result = await monitor.monitor_and_repeg_phase_orders("BUY", orders, "corr-1")
        assert result == orders

    async def test_should_skip_order_logic(self):
        """Test the _should_skip_order method logic."""
        monitor = OrderMonitor(smart_strategy=None, execution_config=None)
        active_orders = {"active-id-1": Mock()}

        # Should skip: no order_id
        order1 = _make_order_result(
            "AAPL",
            action="BUY",
            shares=Decimal("10"),
            trade_amount=Decimal("1500"),
            success=True,
            order_id=None,
        )
        assert monitor._should_skip_order(order1, active_orders) is True

        # Should skip: not successful
        order2 = _make_order_result(
            "AAPL",
            action="BUY",
            shares=Decimal("10"),
            trade_amount=Decimal("1500"),
            success=False,
            order_id="test-123",
        )
        assert monitor._should_skip_order(order2, active_orders) is True

        # Should skip: in active tracking
        order3 = _make_order_result(
            "AAPL",
            action="BUY",
            shares=Decimal("10"),
            trade_amount=Decimal("1500"),
            success=True,
            order_id="active-id-1",
        )
        assert monitor._should_skip_order(order3, active_orders) is True

        # Should NOT skip: valid and not active
        order4 = _make_order_result(
            "AAPL",
            action="BUY",
            shares=Decimal("10"),
            trade_amount=Decimal("1500"),
            success=True,
            order_id="inactive-id",
        )
        assert monitor._should_skip_order(order4, active_orders) is False

    def test_is_cancelled_status(self):
        """Test the _is_cancelled_status method."""
        monitor = OrderMonitor(smart_strategy=None, execution_config=None)

        assert monitor._is_cancelled_status("CANCELED") is True
        assert monitor._is_cancelled_status("EXPIRED") is True
        assert monitor._is_cancelled_status("REJECTED") is True
        assert monitor._is_cancelled_status("FILLED") is False
        assert monitor._is_cancelled_status("PENDING") is False
        assert monitor._is_cancelled_status(None) is False
        assert monitor._is_cancelled_status("") is False


@pytest.mark.asyncio
class TestOrderMonitorEscalation:
    """Test order escalation logic."""

    async def test_cancelled_order_with_unfilled_quantity_triggers_escalation(self):
        """Test that a cancelled order with unfilled quantity triggers market escalation."""
        config = ExecutionConfig()
        mock_smart_strategy = Mock()
        mock_smart_strategy.order_tracker = Mock()
        mock_smart_strategy.order_tracker.get_active_orders = Mock(return_value={})

        # Mock order that was cancelled with partial fill
        order_id = "test-order-123"
        mock_smart_strategy.alpaca_manager = Mock()
        mock_smart_strategy.alpaca_manager._check_order_completion_status = Mock(
            return_value="CANCELED"
        )

        # Mock order result showing partial fill (3 out of 10 shares filled)
        mock_order_result = Mock()
        mock_order_result.filled_qty = 3.0
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

    async def test_expired_order_with_zero_fills_triggers_escalation(self):
        """Test that an expired order with zero fills triggers market escalation."""
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
        call_args = mock_smart_strategy.repeg_manager._escalate_to_market.call_args
        request = call_args[0][1]
        assert request.quantity == Decimal("5")  # All 5 shares unfilled

    async def test_fully_filled_order_does_not_trigger_escalation(self):
        """Test that a fully filled order does not trigger escalation."""
        config = ExecutionConfig()
        mock_smart_strategy = Mock()
        mock_smart_strategy.order_tracker = Mock()
        mock_smart_strategy.order_tracker.get_active_orders = Mock(return_value={})

        order_id = "test-order-complete"
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
                "AAPL",
                action="BUY",
                shares=Decimal("10"),
                trade_amount=Decimal("1500"),
                success=True,
                price=Decimal("150"),
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


@pytest.mark.asyncio
class TestOrderMonitorEdgeCases:
    """Test edge cases and error handling."""

    async def test_no_escalation_when_no_orders_provided(self):
        """Test that escalation handles empty order list gracefully."""
        config = ExecutionConfig()
        mock_smart_strategy = Mock()
        mock_smart_strategy.order_tracker = Mock()
        mock_smart_strategy.order_tracker.get_active_orders = Mock(return_value={})

        monitor = OrderMonitor(mock_smart_strategy, config)

        replacement_map = await monitor._final_escalation_if_active_orders(
            "BUY", "test-corr-id", orders=[]
        )

        assert replacement_map == {}

    async def test_no_escalation_when_orders_is_none(self):
        """Test that escalation handles None orders gracefully."""
        config = ExecutionConfig()
        mock_smart_strategy = Mock()
        mock_smart_strategy.order_tracker = Mock()
        mock_smart_strategy.order_tracker.get_active_orders = Mock(return_value={})

        monitor = OrderMonitor(mock_smart_strategy, config)

        replacement_map = await monitor._final_escalation_if_active_orders(
            "BUY", "test-corr-id", orders=None
        )

        # Should only check active orders, not individual order statuses
        assert isinstance(replacement_map, dict)

    def test_get_order_status_returns_none_when_no_smart_strategy(self):
        """Test that _get_order_status returns None when smart_strategy is None."""
        monitor = OrderMonitor(smart_strategy=None, execution_config=None)

        status = monitor._get_order_status("any-order-id")
        assert status is None

    def test_get_filled_quantity_returns_none_when_no_smart_strategy(self):
        """Test that _get_filled_quantity returns None when smart_strategy is None."""
        monitor = OrderMonitor(smart_strategy=None, execution_config=None)

        qty = monitor._get_filled_quantity("any-order-id")
        assert qty is None

    async def test_replace_order_ids_creates_new_instances(self):
        """Test that _replace_order_ids creates new OrderResult instances (immutability)."""
        monitor = OrderMonitor(smart_strategy=None, execution_config=None)

        original_order = _make_order_result(
            "AAPL",
            action="BUY",
            shares=Decimal("10"),
            trade_amount=Decimal("1500"),
            success=True,
            price=Decimal("150"),
            order_id="old-id-123",
        )

        replacement_map = {"old-id-123": "new-id-456"}

        updated_orders = monitor._replace_order_ids([original_order], replacement_map)

        assert len(updated_orders) == 1
        assert updated_orders[0].order_id == "new-id-456"
        assert updated_orders[0].symbol == "AAPL"
        # Verify immutability - original unchanged
        assert original_order.order_id == "old-id-123"

    async def test_replace_order_ids_handles_empty_map(self):
        """Test that empty replacement map returns original orders."""
        monitor = OrderMonitor(smart_strategy=None, execution_config=None)

        orders = [
            _make_order_result(
                "AAPL",
                action="BUY",
                shares=Decimal("10"),
                trade_amount=Decimal("1500"),
                success=True,
                order_id="id-1",
            )
        ]

        updated_orders = monitor._replace_order_ids(orders, {})
        assert updated_orders == orders


@pytest.mark.asyncio
class TestOrderMonitorDecimalPrecision:
    """Test decimal precision handling for financial calculations."""

    async def test_filled_quantity_uses_decimal(self):
        """Test that filled quantity is converted to Decimal for precision."""
        mock_smart_strategy = Mock()
        mock_order_result = Mock()
        mock_order_result.filled_qty = 3.5  # Float from API
        mock_smart_strategy.alpaca_manager = Mock()
        mock_smart_strategy.alpaca_manager.get_order_execution_result = Mock(
            return_value=mock_order_result
        )

        monitor = OrderMonitor(mock_smart_strategy, None)
        qty = monitor._get_filled_quantity("test-order")

        # Should be Decimal, not float
        assert isinstance(qty, Decimal)
        assert qty == Decimal("3.5")

    async def test_remaining_quantity_calculation_uses_decimal(self):
        """Test that remaining quantity calculation uses Decimal arithmetic."""
        config = ExecutionConfig()
        mock_smart_strategy = Mock()
        mock_smart_strategy.order_tracker = Mock()
        mock_smart_strategy.order_tracker.get_active_orders = Mock(return_value={})

        order_id = "test-order"
        mock_smart_strategy.alpaca_manager = Mock()
        mock_smart_strategy.alpaca_manager._check_order_completion_status = Mock(
            return_value="CANCELED"
        )

        # Fractional shares - requires Decimal precision
        mock_order_result = Mock()
        mock_order_result.filled_qty = 3.333
        mock_smart_strategy.alpaca_manager.get_order_execution_result = Mock(
            return_value=mock_order_result
        )

        mock_escalation_result = SmartOrderResult(
            success=True,
            order_id="new-order",
            final_price=Decimal("100.00"),
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
                "AAPL",
                action="BUY",
                shares=Decimal("10.000"),
                trade_amount=Decimal("1000.00"),
                success=True,
                order_id=order_id,
            )
        ]

        await monitor._final_escalation_if_active_orders("BUY", "corr-1", orders=orders)

        # Verify remaining quantity is Decimal and precisely calculated
        call_args = mock_smart_strategy.repeg_manager._escalate_to_market.call_args
        request = call_args[0][1]
        assert isinstance(request.quantity, Decimal)
        # 10.000 - 3.333 = 6.667
        assert request.quantity == Decimal("6.667")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
