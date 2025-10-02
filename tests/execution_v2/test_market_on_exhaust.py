"""Business Unit: execution | Status: current

Test market-on-exhaust fallback feature for both BUY and SELL flows.

Tests verify that the system correctly triggers market order fallback when:
- Monitoring time/attempts are exhausted
- Remaining quantity > 0
- Config flag is enabled
"""

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch
import uuid

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
):
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
    )


@pytest.mark.asyncio
class TestMarketOnExhaust:
    """Test market-on-exhaust fallback feature."""

    async def test_market_fallback_disabled_by_default(self):
        """Test that market fallback does not trigger when disabled (default behavior)."""
        # Create config with market_on_exhaust disabled (default)
        config = ExecutionConfig()
        assert config.market_on_exhaust_enabled is False

        # Mock smart strategy with active orders
        mock_smart_strategy = Mock()
        mock_smart_strategy.get_active_order_count = Mock(return_value=1)
        mock_smart_strategy.order_tracker = Mock()
        mock_smart_strategy.order_tracker.get_active_orders = Mock(return_value={})
        
        # Create order monitor
        monitor = OrderMonitor(mock_smart_strategy, config)
        
        # Create sample orders
        orders = [
            _make_order_result(
                "BWXT",
                action="BUY",
                shares=Decimal("10"),
                trade_amount=Decimal("1872.00"),
                success=True,
                price=Decimal("187.20"),
                order_id="test-order-1",
            )
        ]
        
        # Call _final_escalation_if_active_orders
        replacement_map = await monitor._final_escalation_if_active_orders("BUY", "test-corr-id")
        
        # Verify no escalation occurred
        assert replacement_map == {}
        mock_smart_strategy.order_tracker.get_active_orders.assert_not_called()

    async def test_market_fallback_enabled_with_active_orders(self):
        """Test that market fallback triggers when enabled with active orders."""
        # Create config with market_on_exhaust enabled
        config = ExecutionConfig(market_on_exhaust_enabled=True)
        assert config.market_on_exhaust_enabled is True

        # Mock smart strategy with active orders
        mock_smart_strategy = Mock()
        mock_smart_strategy.get_active_order_count = Mock(return_value=1)
        
        # Mock active order
        test_order_id = "test-order-1"
        test_request = SmartOrderRequest(
            symbol="BWXT",
            side="BUY",
            quantity=Decimal("10"),
            correlation_id="test-corr-id",
        )
        mock_smart_strategy.order_tracker = Mock()
        mock_smart_strategy.order_tracker.get_active_orders = Mock(
            return_value={test_order_id: test_request}
        )
        
        # Mock repeg manager escalation
        mock_escalation_result = SmartOrderResult(
            success=True,
            order_id="market-order-1",
            final_price=Decimal("187.50"),
            execution_strategy="market_escalation",
            metadata={"original_order_id": test_order_id},
        )
        mock_smart_strategy.repeg_manager = Mock()
        mock_smart_strategy.repeg_manager._escalate_to_market = AsyncMock(
            return_value=mock_escalation_result
        )
        
        # Create order monitor
        monitor = OrderMonitor(mock_smart_strategy, config)
        
        # Call _final_escalation_if_active_orders
        replacement_map = await monitor._final_escalation_if_active_orders("BUY", "test-corr-id")
        
        # Verify escalation occurred
        assert replacement_map == {test_order_id: "market-order-1"}
        mock_smart_strategy.order_tracker.get_active_orders.assert_called_once()
        mock_smart_strategy.repeg_manager._escalate_to_market.assert_called_once_with(
            test_order_id, test_request
        )

    async def test_market_fallback_no_active_orders(self):
        """Test that market fallback does not trigger when no active orders."""
        # Create config with market_on_exhaust enabled
        config = ExecutionConfig(market_on_exhaust_enabled=True)
        
        # Mock smart strategy with NO active orders
        mock_smart_strategy = Mock()
        mock_smart_strategy.get_active_order_count = Mock(return_value=0)
        
        # Create order monitor
        monitor = OrderMonitor(mock_smart_strategy, config)
        
        # Call _final_escalation_if_active_orders
        replacement_map = await monitor._final_escalation_if_active_orders("BUY", "test-corr-id")
        
        # Verify no escalation occurred
        assert replacement_map == {}

    async def test_market_fallback_sell_orders(self):
        """Test that market fallback works for SELL orders."""
        # Create config with market_on_exhaust enabled
        config = ExecutionConfig(market_on_exhaust_enabled=True)

        # Mock smart strategy with active SELL order
        mock_smart_strategy = Mock()
        mock_smart_strategy.get_active_order_count = Mock(return_value=1)
        
        # Mock active SELL order
        test_order_id = "test-sell-order-1"
        test_request = SmartOrderRequest(
            symbol="LEU",
            side="SELL",
            quantity=Decimal("5"),
            correlation_id="test-corr-id",
        )
        mock_smart_strategy.order_tracker = Mock()
        mock_smart_strategy.order_tracker.get_active_orders = Mock(
            return_value={test_order_id: test_request}
        )
        
        # Mock repeg manager escalation
        mock_escalation_result = SmartOrderResult(
            success=True,
            order_id="market-sell-order-1",
            final_price=Decimal("92.50"),
            execution_strategy="market_escalation",
            metadata={"original_order_id": test_order_id},
        )
        mock_smart_strategy.repeg_manager = Mock()
        mock_smart_strategy.repeg_manager._escalate_to_market = AsyncMock(
            return_value=mock_escalation_result
        )
        
        # Create order monitor
        monitor = OrderMonitor(mock_smart_strategy, config)
        
        # Call _final_escalation_if_active_orders
        replacement_map = await monitor._final_escalation_if_active_orders("SELL", "test-corr-id")
        
        # Verify escalation occurred for SELL
        assert replacement_map == {test_order_id: "market-sell-order-1"}
        mock_smart_strategy.repeg_manager._escalate_to_market.assert_called_once_with(
            test_order_id, test_request
        )

    async def test_market_fallback_multiple_active_orders(self):
        """Test that market fallback handles multiple active orders."""
        # Create config with market_on_exhaust enabled
        config = ExecutionConfig(market_on_exhaust_enabled=True)

        # Mock smart strategy with multiple active orders
        mock_smart_strategy = Mock()
        mock_smart_strategy.get_active_order_count = Mock(return_value=2)
        
        # Mock multiple active orders
        order_id_1 = "test-order-1"
        order_id_2 = "test-order-2"
        request_1 = SmartOrderRequest(
            symbol="BWXT",
            side="BUY",
            quantity=Decimal("10"),
            correlation_id="test-corr-id",
        )
        request_2 = SmartOrderRequest(
            symbol="LEU",
            side="BUY",
            quantity=Decimal("5"),
            correlation_id="test-corr-id",
        )
        mock_smart_strategy.order_tracker = Mock()
        mock_smart_strategy.order_tracker.get_active_orders = Mock(
            return_value={order_id_1: request_1, order_id_2: request_2}
        )
        
        # Mock repeg manager escalation for both orders
        result_1 = SmartOrderResult(
            success=True,
            order_id="market-order-1",
            final_price=Decimal("187.50"),
            execution_strategy="market_escalation",
            metadata={"original_order_id": order_id_1},
        )
        result_2 = SmartOrderResult(
            success=True,
            order_id="market-order-2",
            final_price=Decimal("92.50"),
            execution_strategy="market_escalation",
            metadata={"original_order_id": order_id_2},
        )
        mock_smart_strategy.repeg_manager = Mock()
        mock_smart_strategy.repeg_manager._escalate_to_market = AsyncMock(
            side_effect=[result_1, result_2]
        )
        
        # Create order monitor
        monitor = OrderMonitor(mock_smart_strategy, config)
        
        # Call _final_escalation_if_active_orders
        replacement_map = await monitor._final_escalation_if_active_orders("BUY", "test-corr-id")
        
        # Verify escalation occurred for both orders
        assert replacement_map == {
            order_id_1: "market-order-1",
            order_id_2: "market-order-2",
        }
        assert mock_smart_strategy.repeg_manager._escalate_to_market.call_count == 2

    async def test_market_fallback_partial_failure(self):
        """Test that market fallback handles partial failure (one order fails)."""
        # Create config with market_on_exhaust enabled
        config = ExecutionConfig(market_on_exhaust_enabled=True)

        # Mock smart strategy with multiple active orders
        mock_smart_strategy = Mock()
        mock_smart_strategy.get_active_order_count = Mock(return_value=2)
        
        # Mock multiple active orders
        order_id_1 = "test-order-1"
        order_id_2 = "test-order-2"
        request_1 = SmartOrderRequest(
            symbol="BWXT",
            side="BUY",
            quantity=Decimal("10"),
            correlation_id="test-corr-id",
        )
        request_2 = SmartOrderRequest(
            symbol="LEU",
            side="BUY",
            quantity=Decimal("5"),
            correlation_id="test-corr-id",
        )
        mock_smart_strategy.order_tracker = Mock()
        mock_smart_strategy.order_tracker.get_active_orders = Mock(
            return_value={order_id_1: request_1, order_id_2: request_2}
        )
        
        # Mock repeg manager: one success, one failure
        result_1 = SmartOrderResult(
            success=True,
            order_id="market-order-1",
            final_price=Decimal("187.50"),
            execution_strategy="market_escalation",
            metadata={"original_order_id": order_id_1},
        )
        result_2 = SmartOrderResult(
            success=False,
            error_message="Market order rejected",
            execution_strategy="market_escalation_failed",
        )
        mock_smart_strategy.repeg_manager = Mock()
        mock_smart_strategy.repeg_manager._escalate_to_market = AsyncMock(
            side_effect=[result_1, result_2]
        )
        
        # Create order monitor
        monitor = OrderMonitor(mock_smart_strategy, config)
        
        # Call _final_escalation_if_active_orders
        replacement_map = await monitor._final_escalation_if_active_orders("BUY", "test-corr-id")
        
        # Verify only successful escalation is in replacement map
        assert replacement_map == {order_id_1: "market-order-1"}

    async def test_market_fallback_no_smart_strategy(self):
        """Test that market fallback handles case where smart strategy is None."""
        config = ExecutionConfig(market_on_exhaust_enabled=True)
        
        # Create order monitor with no smart strategy
        monitor = OrderMonitor(None, config)
        
        # Call _final_escalation_if_active_orders
        replacement_map = await monitor._final_escalation_if_active_orders("BUY", "test-corr-id")
        
        # Verify no escalation occurred
        assert replacement_map == {}

    async def test_is_market_on_exhaust_enabled_no_config(self):
        """Test _is_market_on_exhaust_enabled with no config."""
        monitor = OrderMonitor(None, None)
        
        # Should return False when no config
        assert monitor._is_market_on_exhaust_enabled() is False

    async def test_is_market_on_exhaust_enabled_with_config(self):
        """Test _is_market_on_exhaust_enabled with valid config."""
        config = ExecutionConfig(market_on_exhaust_enabled=True)
        monitor = OrderMonitor(None, config)
        
        # Should return True when enabled
        assert monitor._is_market_on_exhaust_enabled() is True
        
        # Test with disabled
        config_disabled = ExecutionConfig(market_on_exhaust_enabled=False)
        monitor_disabled = OrderMonitor(None, config_disabled)
        assert monitor_disabled._is_market_on_exhaust_enabled() is False
