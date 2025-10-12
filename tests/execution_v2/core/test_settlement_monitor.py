#!/usr/bin/env python3
"""Business Unit: execution_v2 | Status: current.

Comprehensive unit tests for SettlementMonitor.

Tests cover:
- Constructor validation
- Settlement monitoring success and timeout scenarios
- Order status transitions
- Buying power verification with retries
- Event emission validation
- Error handling paths
- Edge cases (empty lists, all timeouts, double-counting prevention)
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import Mock

import pytest

from the_alchemiser.execution_v2.core.settlement_monitor import SettlementMonitor
from the_alchemiser.shared.errors.exceptions import (
    DataProviderError,
    TradingClientError,
)
from the_alchemiser.shared.events import BulkSettlementCompleted
from the_alchemiser.shared.events.bus import EventBus


@pytest.fixture
def mock_alpaca_manager() -> Mock:
    """Create mock AlpacaManager."""
    manager = Mock()
    manager._check_order_completion_status = Mock()
    manager._trading_client = Mock()
    manager.get_buying_power = Mock(return_value=Decimal("10000.00"))
    return manager


@pytest.fixture
def mock_event_bus() -> Mock:
    """Create mock EventBus."""
    bus = Mock(spec=EventBus)
    bus.publish = Mock()
    return bus


@pytest.fixture
def settlement_monitor(mock_alpaca_manager: Mock, mock_event_bus: Mock) -> SettlementMonitor:
    """Create SettlementMonitor with mocked dependencies."""
    return SettlementMonitor(
        alpaca_manager=mock_alpaca_manager,
        event_bus=mock_event_bus,
        polling_interval_seconds=0.1,  # Fast polling for tests
        max_wait_seconds=2,  # Short timeout for tests
    )


class TestSettlementMonitorInit:
    """Test SettlementMonitor initialization and validation."""

    def test_init_valid_parameters(self, mock_alpaca_manager: Mock) -> None:
        """Test initialization with valid parameters."""
        monitor = SettlementMonitor(
            alpaca_manager=mock_alpaca_manager,
            event_bus=None,
            polling_interval_seconds=0.5,
            max_wait_seconds=60,
        )

        assert monitor.alpaca_manager == mock_alpaca_manager
        assert monitor.event_bus is None
        assert monitor.polling_interval == 0.5
        assert monitor.max_wait_seconds == 60
        assert monitor.buying_power_service is not None

    def test_init_negative_polling_interval(self, mock_alpaca_manager: Mock) -> None:
        """Test initialization rejects negative polling interval."""
        with pytest.raises(ValueError, match="polling_interval_seconds must be positive"):
            SettlementMonitor(
                alpaca_manager=mock_alpaca_manager,
                polling_interval_seconds=-1.0,
            )

    def test_init_zero_polling_interval(self, mock_alpaca_manager: Mock) -> None:
        """Test initialization rejects zero polling interval."""
        with pytest.raises(ValueError, match="polling_interval_seconds must be positive"):
            SettlementMonitor(
                alpaca_manager=mock_alpaca_manager,
                polling_interval_seconds=0.0,
            )

    def test_init_negative_max_wait(self, mock_alpaca_manager: Mock) -> None:
        """Test initialization rejects negative max wait."""
        with pytest.raises(ValueError, match="max_wait_seconds must be positive"):
            SettlementMonitor(
                alpaca_manager=mock_alpaca_manager,
                max_wait_seconds=-10,
            )

    def test_init_polling_greater_than_max_wait(self, mock_alpaca_manager: Mock) -> None:
        """Test initialization rejects polling interval >= max wait."""
        with pytest.raises(ValueError, match="must be less than"):
            SettlementMonitor(
                alpaca_manager=mock_alpaca_manager,
                polling_interval_seconds=10.0,
                max_wait_seconds=5,
            )


class TestMonitorSellOrdersSettlement:
    """Test monitor_sell_orders_settlement method."""

    @pytest.mark.asyncio
    async def test_successful_settlement_single_order(
        self, settlement_monitor: SettlementMonitor, mock_alpaca_manager: Mock
    ) -> None:
        """Test successful settlement of a single sell order."""
        order_id = "test-order-1"
        correlation_id = "test-correlation-1"

        # Mock order status as FILLED
        mock_alpaca_manager._check_order_completion_status.return_value = "FILLED"

        # Mock order details
        mock_order = Mock()
        mock_order.symbol = "AAPL"
        mock_order.side = "SELL"
        mock_order.filled_qty = 10
        mock_order.filled_avg_price = 150.50
        mock_order.status = "FILLED"
        mock_alpaca_manager._trading_client.get_order_by_id = Mock(return_value=mock_order)

        # Execute settlement monitoring
        result = await settlement_monitor.monitor_sell_orders_settlement(
            sell_order_ids=[order_id],
            correlation_id=correlation_id,
        )

        # Verify result
        assert isinstance(result, BulkSettlementCompleted)
        assert result.correlation_id == correlation_id
        assert len(result.settled_order_ids) == 1
        assert result.settled_order_ids[0] == order_id
        assert result.total_buying_power_released == Decimal("1505.00")  # 10 * 150.50

    @pytest.mark.asyncio
    async def test_successful_settlement_multiple_orders(
        self, settlement_monitor: SettlementMonitor, mock_alpaca_manager: Mock
    ) -> None:
        """Test successful settlement of multiple sell orders."""
        order_ids = ["order-1", "order-2"]
        correlation_id = "test-correlation-2"

        # Mock order statuses
        mock_alpaca_manager._check_order_completion_status.return_value = "FILLED"

        # Mock order details for both orders
        mock_order_1 = Mock()
        mock_order_1.symbol = "AAPL"
        mock_order_1.side = "SELL"
        mock_order_1.filled_qty = 10
        mock_order_1.filled_avg_price = 150.00
        mock_order_1.status = "FILLED"

        mock_order_2 = Mock()
        mock_order_2.symbol = "GOOGL"
        mock_order_2.side = "SELL"
        mock_order_2.filled_qty = 5
        mock_order_2.filled_avg_price = 2800.00
        mock_order_2.status = "FILLED"

        mock_alpaca_manager._trading_client.get_order_by_id = Mock(
            side_effect=[mock_order_1, mock_order_2]
        )

        # Execute
        result = await settlement_monitor.monitor_sell_orders_settlement(
            sell_order_ids=order_ids,
            correlation_id=correlation_id,
        )

        # Verify
        assert len(result.settled_order_ids) == 2
        expected_total = Decimal("1500.00") + Decimal("14000.00")  # 10*150 + 5*2800
        assert result.total_buying_power_released == expected_total

    @pytest.mark.asyncio
    async def test_settlement_timeout(
        self, settlement_monitor: SettlementMonitor, mock_alpaca_manager: Mock
    ) -> None:
        """Test settlement monitoring timeout."""
        order_id = "timeout-order"
        correlation_id = "test-correlation-timeout"

        # Mock order never reaches final state
        mock_alpaca_manager._check_order_completion_status.return_value = "PENDING"

        # Execute (should timeout)
        result = await settlement_monitor.monitor_sell_orders_settlement(
            sell_order_ids=[order_id],
            correlation_id=correlation_id,
        )

        # Verify timeout handling
        assert len(result.settled_order_ids) == 0
        assert result.total_buying_power_released == Decimal("0")

    @pytest.mark.asyncio
    async def test_empty_order_list(
        self, settlement_monitor: SettlementMonitor, mock_event_bus: Mock
    ) -> None:
        """Test handling of empty order list."""
        result = await settlement_monitor.monitor_sell_orders_settlement(
            sell_order_ids=[],
            correlation_id="test-empty",
        )

        assert len(result.settled_order_ids) == 0
        assert result.total_buying_power_released == Decimal("0")
        # Event should still be published
        mock_event_bus.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_canceled_order_not_counted(
        self, settlement_monitor: SettlementMonitor, mock_alpaca_manager: Mock
    ) -> None:
        """Test that canceled orders are not counted in buying power release."""
        order_id = "canceled-order"

        # Mock order as CANCELED
        mock_alpaca_manager._check_order_completion_status.return_value = "CANCELED"

        mock_order = Mock()
        mock_order.symbol = "AAPL"
        mock_order.side = "SELL"
        mock_order.filled_qty = 0
        mock_order.filled_avg_price = 0
        mock_order.status = "CANCELED"
        mock_alpaca_manager._trading_client.get_order_by_id = Mock(return_value=mock_order)

        result = await settlement_monitor.monitor_sell_orders_settlement(
            sell_order_ids=[order_id],
            correlation_id="test-canceled",
        )

        # Settled but zero buying power
        assert len(result.settled_order_ids) == 1
        assert result.total_buying_power_released == Decimal("0")

    @pytest.mark.asyncio
    async def test_error_handling_continues_monitoring(
        self, settlement_monitor: SettlementMonitor, mock_alpaca_manager: Mock
    ) -> None:
        """Test that errors on one order don't stop monitoring of others."""
        order_ids = ["good-order", "bad-order"]

        # First order succeeds immediately, second order keeps retrying then times out
        def side_effect_func(order_id: str) -> str:
            if order_id == "good-order":
                return "FILLED"
            # For bad-order, raise error to simulate API failure
            raise DataProviderError("API error")

        mock_alpaca_manager._check_order_completion_status.side_effect = side_effect_func

        mock_order = Mock()
        mock_order.symbol = "AAPL"
        mock_order.side = "SELL"
        mock_order.filled_qty = 10
        mock_order.filled_avg_price = 100.00
        mock_order.status = "FILLED"
        mock_alpaca_manager._trading_client.get_order_by_id = Mock(return_value=mock_order)

        result = await settlement_monitor.monitor_sell_orders_settlement(
            sell_order_ids=order_ids,
            correlation_id="test-partial-error",
        )

        # Should have one settled order (the good one)
        assert len(result.settled_order_ids) == 1
        assert "good-order" in result.settled_order_ids


class TestVerifyBuyingPowerAvailableAfterSettlement:
    """Test verify_buying_power_available_after_settlement method."""

    @pytest.mark.asyncio
    async def test_buying_power_immediately_available(
        self, settlement_monitor: SettlementMonitor, mock_alpaca_manager: Mock
    ) -> None:
        """Test when buying power is immediately available."""
        expected_amount = Decimal("5000.00")
        mock_alpaca_manager.get_buying_power = Mock(return_value=Decimal("10000.00"))

        (
            is_available,
            actual,
        ) = await settlement_monitor.verify_buying_power_available_after_settlement(
            expected_buying_power=expected_amount,
            settlement_correlation_id="test-immediate",
            max_wait_seconds=10,
        )

        assert is_available is True
        assert actual == Decimal("10000.00")

    @pytest.mark.asyncio
    async def test_buying_power_insufficient(
        self, settlement_monitor: SettlementMonitor, mock_alpaca_manager: Mock
    ) -> None:
        """Test when buying power remains insufficient."""
        expected_amount = Decimal("15000.00")
        mock_alpaca_manager.get_buying_power = Mock(return_value=Decimal("10000.00"))

        (
            is_available,
            actual,
        ) = await settlement_monitor.verify_buying_power_available_after_settlement(
            expected_buying_power=expected_amount,
            settlement_correlation_id="test-insufficient",
            max_wait_seconds=1,  # Short wait
        )

        assert is_available is False
        assert actual == Decimal("10000.00")


class TestMonitorSingleOrderSettlement:
    """Test _monitor_single_order_settlement private method."""

    @pytest.mark.asyncio
    async def test_order_fills_immediately(
        self, settlement_monitor: SettlementMonitor, mock_alpaca_manager: Mock
    ) -> None:
        """Test order that fills immediately."""
        order_id = "immediate-order"

        mock_alpaca_manager._check_order_completion_status.return_value = "FILLED"

        mock_order = Mock()
        mock_order.symbol = "MSFT"
        mock_order.side = "SELL"
        mock_order.filled_qty = 20
        mock_order.filled_avg_price = 300.00
        mock_order.status = "FILLED"
        mock_alpaca_manager._trading_client.get_order_by_id = Mock(return_value=mock_order)

        result = await settlement_monitor._monitor_single_order_settlement(
            order_id, "test-correlation"
        )

        assert result is not None
        assert result["symbol"] == "MSFT"
        assert result["settled_value"] == Decimal("6000.00")

    @pytest.mark.asyncio
    async def test_order_timeout(
        self, settlement_monitor: SettlementMonitor, mock_alpaca_manager: Mock
    ) -> None:
        """Test order that times out."""
        order_id = "timeout-order"

        mock_alpaca_manager._check_order_completion_status.return_value = "PENDING"

        result = await settlement_monitor._monitor_single_order_settlement(
            order_id, "test-correlation"
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_order_transitions_to_filled(
        self, settlement_monitor: SettlementMonitor, mock_alpaca_manager: Mock
    ) -> None:
        """Test order that transitions from pending to filled."""
        order_id = "transition-order"

        # First check: pending, second check: filled
        mock_alpaca_manager._check_order_completion_status.side_effect = [
            "PENDING",
            "FILLED",
        ]

        mock_order = Mock()
        mock_order.symbol = "TSLA"
        mock_order.side = "SELL"
        mock_order.filled_qty = 5
        mock_order.filled_avg_price = 700.00
        mock_order.status = "FILLED"
        mock_alpaca_manager._trading_client.get_order_by_id = Mock(return_value=mock_order)

        result = await settlement_monitor._monitor_single_order_settlement(
            order_id, "test-correlation"
        )

        assert result is not None
        assert result["settled_value"] == Decimal("3500.00")


class TestGetOrderSettlementDetails:
    """Test _get_order_settlement_details private method."""

    @pytest.mark.asyncio
    async def test_get_details_success(
        self, settlement_monitor: SettlementMonitor, mock_alpaca_manager: Mock
    ) -> None:
        """Test successful order details retrieval."""
        order_id = "detail-order"

        mock_order = Mock()
        mock_order.symbol = "AMZN"
        mock_order.side = "SELL"
        mock_order.filled_qty = 8
        mock_order.filled_avg_price = 3200.00
        mock_order.status = "FILLED"
        mock_alpaca_manager._trading_client.get_order_by_id = Mock(return_value=mock_order)

        result = await settlement_monitor._get_order_settlement_details(order_id)

        assert result is not None
        assert result["symbol"] == "AMZN"
        assert result["side"] == "SELL"
        assert result["settled_quantity"] == Decimal("8")
        assert result["settlement_price"] == Decimal("3200.00")
        assert result["settled_value"] == Decimal("25600.00")

    @pytest.mark.asyncio
    async def test_get_details_api_error(
        self, settlement_monitor: SettlementMonitor, mock_alpaca_manager: Mock
    ) -> None:
        """Test order details retrieval with API error."""
        order_id = "error-order"

        mock_alpaca_manager._trading_client.get_order_by_id = Mock(
            side_effect=TradingClientError("API error")
        )

        result = await settlement_monitor._get_order_settlement_details(order_id)

        assert result is None


class TestWaitForSettlementThreshold:
    """Test wait_for_settlement_threshold method."""

    @pytest.mark.asyncio
    async def test_threshold_reached_immediately(
        self, settlement_monitor: SettlementMonitor, mock_alpaca_manager: Mock
    ) -> None:
        """Test when threshold is reached immediately."""
        target = Decimal("1000.00")
        order_ids = ["order-1"]

        mock_alpaca_manager._check_order_completion_status.return_value = "FILLED"

        mock_order = Mock()
        mock_order.symbol = "AAPL"
        mock_order.side = "SELL"
        mock_order.filled_qty = 10
        mock_order.filled_avg_price = 150.00
        mock_order.status = "FILLED"
        mock_alpaca_manager._trading_client.get_order_by_id = Mock(return_value=mock_order)

        result = await settlement_monitor.wait_for_settlement_threshold(
            target_buying_power=target,
            sell_order_ids=order_ids,
            correlation_id="test-threshold",
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_threshold_timeout(
        self, settlement_monitor: SettlementMonitor, mock_alpaca_manager: Mock
    ) -> None:
        """Test when threshold is not reached before timeout."""
        target = Decimal("10000.00")
        order_ids = ["small-order"]

        mock_order = Mock()
        mock_order.symbol = "AAPL"
        mock_order.side = "SELL"
        mock_order.filled_qty = 1
        mock_order.filled_avg_price = 100.00
        mock_order.status = "FILLED"
        mock_alpaca_manager._trading_client.get_order_by_id = Mock(return_value=mock_order)

        result = await settlement_monitor.wait_for_settlement_threshold(
            target_buying_power=target,
            sell_order_ids=order_ids,
            correlation_id="test-timeout",
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_no_double_counting(
        self, settlement_monitor: SettlementMonitor, mock_alpaca_manager: Mock
    ) -> None:
        """Test that orders are not counted multiple times."""
        target = Decimal("1000.00")
        order_ids = ["order-1"]

        # Order fills with value of 500
        mock_order = Mock()
        mock_order.symbol = "AAPL"
        mock_order.side = "SELL"
        mock_order.filled_qty = 5
        mock_order.filled_avg_price = 100.00
        mock_order.status = "FILLED"
        mock_alpaca_manager._trading_client.get_order_by_id = Mock(return_value=mock_order)

        # This should timeout because target is 1000 but order only provides 500
        # and the order should only be counted once
        result = await settlement_monitor.wait_for_settlement_threshold(
            target_buying_power=target,
            sell_order_ids=order_ids,
            correlation_id="test-no-double-count",
        )

        # Should timeout with only 500 accumulated (not 500 * multiple_polls)
        assert result is False


class TestEventEmission:
    """Test event emission behavior."""

    @pytest.mark.asyncio
    async def test_bulk_settlement_event_emitted(
        self, settlement_monitor: SettlementMonitor, mock_alpaca_manager: Mock, mock_event_bus: Mock
    ) -> None:
        """Test that BulkSettlementCompleted event is emitted."""
        order_id = "event-test-order"

        mock_alpaca_manager._check_order_completion_status.return_value = "FILLED"

        mock_order = Mock()
        mock_order.symbol = "AAPL"
        mock_order.side = "SELL"
        mock_order.filled_qty = 10
        mock_order.filled_avg_price = 100.00
        mock_order.status = "FILLED"
        mock_alpaca_manager._trading_client.get_order_by_id = Mock(return_value=mock_order)

        await settlement_monitor.monitor_sell_orders_settlement(
            sell_order_ids=[order_id],
            correlation_id="test-event",
        )

        # Verify event was published
        mock_event_bus.publish.assert_called()
        call_args = mock_event_bus.publish.call_args[0]
        event = call_args[0]

        assert isinstance(event, BulkSettlementCompleted)
        assert event.correlation_id == "test-event"

    @pytest.mark.asyncio
    async def test_no_event_bus_no_error(
        self, settlement_monitor: SettlementMonitor, mock_alpaca_manager: Mock
    ) -> None:
        """Test that missing event bus doesn't cause errors."""
        # Create monitor without event bus
        monitor = SettlementMonitor(
            alpaca_manager=mock_alpaca_manager,
            event_bus=None,
            polling_interval_seconds=0.1,
            max_wait_seconds=2,
        )

        mock_alpaca_manager._check_order_completion_status.return_value = "FILLED"

        mock_order = Mock()
        mock_order.symbol = "AAPL"
        mock_order.side = "SELL"
        mock_order.filled_qty = 10
        mock_order.filled_avg_price = 100.00
        mock_order.status = "FILLED"
        mock_alpaca_manager._trading_client.get_order_by_id = Mock(return_value=mock_order)

        # Should not raise error even without event bus
        result = await monitor.monitor_sell_orders_settlement(
            sell_order_ids=["order-1"],
            correlation_id="test-no-bus",
        )

        assert isinstance(result, BulkSettlementCompleted)


class TestCleanupCompletedMonitors:
    """Test cleanup_completed_monitors method."""

    def test_cleanup_completed_tasks(self, settlement_monitor: SettlementMonitor) -> None:
        """Test cleanup of completed monitoring tasks."""
        # Create mock tasks
        completed_task = Mock()
        completed_task.done.return_value = True

        active_task = Mock()
        active_task.done.return_value = False

        # Add to active monitors
        settlement_monitor._active_monitors = {
            "completed-1": completed_task,
            "active-1": active_task,
        }

        # Run cleanup
        settlement_monitor.cleanup_completed_monitors()

        # Verify completed task removed
        assert "completed-1" not in settlement_monitor._active_monitors
        assert "active-1" in settlement_monitor._active_monitors

    def test_cleanup_no_completed_tasks(self, settlement_monitor: SettlementMonitor) -> None:
        """Test cleanup when no tasks are completed."""
        active_task = Mock()
        active_task.done.return_value = False

        settlement_monitor._active_monitors = {"active-1": active_task}

        settlement_monitor.cleanup_completed_monitors()

        # Verify task still present
        assert "active-1" in settlement_monitor._active_monitors


class TestGenerateEventId:
    """Test _generate_event_id method."""

    def test_generates_valid_uuid(self, settlement_monitor: SettlementMonitor) -> None:
        """Test that event ID is a valid UUID string."""
        event_id = settlement_monitor._generate_event_id()

        assert isinstance(event_id, str)
        assert len(event_id) == 36  # UUID format: 8-4-4-4-12
        assert event_id.count("-") == 4

    def test_generates_unique_ids(self, settlement_monitor: SettlementMonitor) -> None:
        """Test that consecutive calls generate unique IDs."""
        id1 = settlement_monitor._generate_event_id()
        id2 = settlement_monitor._generate_event_id()

        assert id1 != id2
