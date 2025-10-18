"""Business Unit: execution | Status: current.

Comprehensive unit test suite for OrderFinalizer.

Tests order finalization logic, status mapping, UUID validation,
correlation_id tracking, trade value calculation, and error handling.
"""

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from the_alchemiser.execution_v2.core.order_finalizer import (
    DEFAULT_ORDER_COMPLETION_TIMEOUT_SECONDS,
    OrderFinalizer,
)
from the_alchemiser.execution_v2.models.execution_result import OrderResult
from the_alchemiser.shared.schemas.rebalance_plan import RebalancePlanItem

# Test Helpers


def _make_rebalance_item(
    symbol: str = "AAPL",
    *,
    current_weight: Decimal = Decimal("0.1"),
    target_weight: Decimal = Decimal("0.2"),
    trade_amount: Decimal = Decimal("1000"),
    action: str = "BUY",
) -> RebalancePlanItem:
    """Create a test rebalance plan item."""
    weight_diff = target_weight - current_weight
    return RebalancePlanItem(
        symbol=symbol,
        current_weight=current_weight,
        target_weight=target_weight,
        weight_diff=weight_diff,
        target_value=target_weight * Decimal("10000"),
        current_value=current_weight * Decimal("10000"),
        trade_amount=trade_amount,
        action=action,
        priority=1,
    )


def _make_order_result(
    symbol: str = "AAPL",
    *,
    action: str = "BUY",
    shares: Decimal = Decimal("10"),
    trade_amount: Decimal = Decimal("1000"),
    success: bool = True,
    price: Decimal | None = Decimal("100"),
    order_id: str | None = None,
    error_message: str | None = None,
) -> OrderResult:
    """Create a test order result."""
    if order_id is None:
        order_id = str(uuid.uuid4())
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


# Test Fixtures


@pytest.fixture
def mock_alpaca_manager():
    """Mock Alpaca manager."""
    mock = Mock()
    mock.wait_for_order_completion = Mock(return_value=Mock(status="completed"))
    mock.get_order_execution_result = Mock(
        return_value=Mock(
            status="filled",
            avg_fill_price=Decimal("100.50"),
            filled_qty=Decimal("10"),
        )
    )
    return mock


@pytest.fixture
def mock_execution_config():
    """Mock execution config."""
    mock = Mock()
    mock.order_placement_timeout_seconds = 45
    return mock


@pytest.fixture
def order_finalizer(mock_alpaca_manager, mock_execution_config):
    """Create OrderFinalizer with mocked dependencies."""
    return OrderFinalizer(mock_alpaca_manager, mock_execution_config)


@pytest.fixture
def order_finalizer_no_config(mock_alpaca_manager):
    """Create OrderFinalizer without execution config."""
    return OrderFinalizer(mock_alpaca_manager, None)


# Tests for finalize_phase_orders


class TestFinalizePhaseOrders:
    """Test finalize_phase_orders method."""

    def test_empty_orders_returns_empty_results(self, order_finalizer):
        """Test that empty order list returns empty results."""
        orders = []
        items = []
        result_orders, success_count, trade_value = order_finalizer.finalize_phase_orders(
            orders, items, "BUY"
        )

        assert result_orders == []
        assert success_count == 0
        assert trade_value == Decimal("0")

    def test_finalize_successful_orders(self, order_finalizer, mock_alpaca_manager):
        """Test finalizing successful orders updates status correctly."""
        order1 = _make_order_result(
            symbol="AAPL", success=False, price=None, order_id=str(uuid.uuid4())
        )
        order2 = _make_order_result(
            symbol="GOOGL", success=False, price=None, order_id=str(uuid.uuid4())
        )
        item1 = _make_rebalance_item(symbol="AAPL", trade_amount=Decimal("1000"))
        item2 = _make_rebalance_item(symbol="GOOGL", trade_amount=Decimal("2000"))

        mock_alpaca_manager.get_order_execution_result = Mock(
            return_value=Mock(
                status="filled",
                avg_fill_price=Decimal("100.50"),
                filled_qty=Decimal("10"),
            )
        )

        result_orders, success_count, trade_value = order_finalizer.finalize_phase_orders(
            [order1, order2], [item1, item2], "BUY"
        )

        assert len(result_orders) == 2
        assert success_count == 2
        assert trade_value == Decimal("3000")  # 1000 + 2000
        assert result_orders[0].success is True
        assert result_orders[1].success is True
        assert result_orders[0].price == Decimal("100.50")

    def test_finalize_with_correlation_id(self, order_finalizer, mock_alpaca_manager):
        """Test that correlation_id is propagated through logging."""
        order = _make_order_result(order_id=str(uuid.uuid4()))
        item = _make_rebalance_item()
        correlation_id = "test-correlation-123"

        with patch("the_alchemiser.execution_v2.core.order_finalizer.logger") as mock_logger:
            order_finalizer.finalize_phase_orders(
                [order], [item], "BUY", correlation_id=correlation_id
            )

            # Verify correlation_id is in log calls
            log_calls = mock_logger.info.call_args_list + mock_logger.debug.call_args_list
            assert any(
                "correlation_id" in str(call) and correlation_id in str(call) for call in log_calls
            )


# Tests for _derive_max_wait_seconds


class TestDeriveMaxWaitSeconds:
    """Test _derive_max_wait_seconds method."""

    def test_returns_config_timeout_when_present(self, order_finalizer, mock_execution_config):
        """Test that config timeout is used when available."""
        result = order_finalizer._derive_max_wait_seconds()
        assert result == 45

    def test_returns_default_when_no_config(self, order_finalizer_no_config):
        """Test that default timeout is used when no config."""
        result = order_finalizer_no_config._derive_max_wait_seconds()
        assert result == DEFAULT_ORDER_COMPLETION_TIMEOUT_SECONDS

    def test_returns_default_on_exception(self, order_finalizer):
        """Test that default is returned on exception."""
        # Make getattr raise an exception
        order_finalizer.execution_config = Mock()
        delattr(order_finalizer.execution_config, "order_placement_timeout_seconds")

        result = order_finalizer._derive_max_wait_seconds()
        assert result == DEFAULT_ORDER_COMPLETION_TIMEOUT_SECONDS


# Tests for _is_valid_uuid


class TestIsValidUuid:
    """Test _is_valid_uuid static method."""

    def test_valid_uuid_returns_true(self):
        """Test that valid UUID strings return True."""
        valid_uuid = str(uuid.uuid4())
        assert OrderFinalizer._is_valid_uuid(valid_uuid) is True

    def test_invalid_uuid_returns_false(self):
        """Test that invalid UUID strings return False."""
        assert OrderFinalizer._is_valid_uuid("not-a-uuid") is False
        assert OrderFinalizer._is_valid_uuid("12345") is False
        assert OrderFinalizer._is_valid_uuid("") is False

    def test_various_uuid_formats(self):
        """Test various UUID formats."""
        # Standard UUID4
        assert OrderFinalizer._is_valid_uuid(str(uuid.uuid4())) is True

        # UUID with uppercase
        assert OrderFinalizer._is_valid_uuid(str(uuid.uuid4()).upper()) is True

        # UUID without hyphens (should fail)
        uuid_str = str(uuid.uuid4()).replace("-", "")
        assert OrderFinalizer._is_valid_uuid(uuid_str) is False


# Tests for _validate_order_ids


class TestValidateOrderIds:
    """Test _validate_order_ids method."""

    def test_separates_valid_and_invalid_ids(self, order_finalizer):
        """Test that valid and invalid UUIDs are separated correctly."""
        valid_id = str(uuid.uuid4())
        order1 = _make_order_result(order_id=valid_id)
        order2 = _make_order_result(order_id="invalid-id")
        order3 = _make_order_result(order_id=None)

        valid_ids, invalid_ids = order_finalizer._validate_order_ids([order1, order2, order3])

        assert len(valid_ids) == 1
        assert valid_id in valid_ids
        assert len(invalid_ids) == 1
        assert "invalid-id" in invalid_ids

    def test_all_valid_ids(self, order_finalizer):
        """Test with all valid UUIDs."""
        orders = [_make_order_result(order_id=str(uuid.uuid4())) for _ in range(3)]

        valid_ids, invalid_ids = order_finalizer._validate_order_ids(orders)

        assert len(valid_ids) == 3
        assert len(invalid_ids) == 0

    def test_all_invalid_ids(self, order_finalizer):
        """Test with all invalid order IDs."""
        orders = [
            _make_order_result(order_id="bad1"),
            _make_order_result(order_id="bad2"),
        ]

        valid_ids, invalid_ids = order_finalizer._validate_order_ids(orders)

        assert len(valid_ids) == 0
        assert len(invalid_ids) == 2

    def test_empty_order_list(self, order_finalizer):
        """Test with empty order list."""
        valid_ids, invalid_ids = order_finalizer._validate_order_ids([])

        assert len(valid_ids) == 0
        assert len(invalid_ids) == 0


# Tests for _apply_final_status_to_order


class TestApplyFinalStatusToOrder:
    """Test _apply_final_status_to_order method."""

    def test_status_filled(self, order_finalizer):
        """Test that 'filled' status is mapped to success=True."""
        order = _make_order_result(success=False, price=Decimal("90"))
        status_map = {order.order_id: ("filled", Decimal("100.50"))}

        final_price, is_filled, error = order_finalizer._apply_final_status_to_order(
            order, status_map
        )

        assert is_filled is True
        assert final_price == Decimal("100.50")
        assert error is None

    def test_status_partially_filled(self, order_finalizer):
        """Test that 'partially_filled' status is mapped to success=True."""
        order = _make_order_result(success=False)
        status_map = {order.order_id: ("partially_filled", Decimal("99.75"))}

        final_price, is_filled, error = order_finalizer._apply_final_status_to_order(
            order, status_map
        )

        assert is_filled is True
        assert final_price == Decimal("99.75")

    def test_status_rejected(self, order_finalizer):
        """Test that 'rejected' status is mapped to success=False."""
        order = _make_order_result(success=True)
        status_map = {order.order_id: ("rejected", None)}

        final_price, is_filled, error = order_finalizer._apply_final_status_to_order(
            order, status_map
        )

        assert is_filled is False
        assert error == "Order rejected"

    def test_status_canceled(self, order_finalizer):
        """Test that 'canceled' status is mapped to success=False."""
        order = _make_order_result(success=True)
        status_map = {order.order_id: ("canceled", None)}

        final_price, is_filled, error = order_finalizer._apply_final_status_to_order(
            order, status_map
        )

        assert is_filled is False
        assert error == "Order canceled"

    def test_order_not_in_map(self, order_finalizer):
        """Test order not in status map keeps original values."""
        order = _make_order_result(success=True, price=Decimal("100"))
        status_map = {}

        final_price, is_filled, error = order_finalizer._apply_final_status_to_order(
            order, status_map
        )

        assert is_filled is True
        assert final_price == Decimal("100")
        assert error is None

    def test_order_with_no_price_update(self, order_finalizer):
        """Test order status update without price."""
        order = _make_order_result(success=False, price=Decimal("100"))
        status_map = {order.order_id: ("filled", None)}

        final_price, is_filled, error = order_finalizer._apply_final_status_to_order(
            order, status_map
        )

        assert is_filled is True
        assert final_price == Decimal("100")  # Original price retained


# Tests for _calculate_order_trade_value


class TestCalculateOrderTradeValue:
    """Test _calculate_order_trade_value method."""

    def test_calculates_from_matching_item(self, order_finalizer):
        """Test that trade value is calculated from matching rebalance item."""
        order = _make_order_result(trade_amount=Decimal("1000"))
        items = [
            _make_rebalance_item(trade_amount=Decimal("1500")),
            _make_rebalance_item(trade_amount=Decimal("2000")),
        ]

        result = order_finalizer._calculate_order_trade_value(order, items, 0)
        assert result == Decimal("1500")

        result = order_finalizer._calculate_order_trade_value(order, items, 1)
        assert result == Decimal("2000")

    def test_handles_negative_trade_amounts(self, order_finalizer):
        """Test that negative trade amounts are converted to absolute."""
        order = _make_order_result(trade_amount=Decimal("1000"))
        items = [_make_rebalance_item(trade_amount=Decimal("-1500"))]

        result = order_finalizer._calculate_order_trade_value(order, items, 0)
        assert result == Decimal("1500")  # Absolute value

    def test_fallback_on_index_error(self, order_finalizer):
        """Test fallback to order.trade_amount on IndexError."""
        order = _make_order_result(trade_amount=Decimal("1000"))
        items = [_make_rebalance_item(trade_amount=Decimal("1500"))]

        # Access index 5 which doesn't exist
        result = order_finalizer._calculate_order_trade_value(order, items, 5)
        assert result == Decimal("1000")  # Falls back to order.trade_amount

    def test_fallback_on_empty_items(self, order_finalizer):
        """Test fallback when items list is empty."""
        order = _make_order_result(trade_amount=Decimal("1000"))
        items = []

        result = order_finalizer._calculate_order_trade_value(order, items, 0)
        assert result == Decimal("1000")

    def test_logs_index_error(self, order_finalizer):
        """Test that IndexError is logged with proper context."""
        order = _make_order_result(trade_amount=Decimal("1000"), order_id=str(uuid.uuid4()))
        items = []

        with patch("the_alchemiser.execution_v2.core.order_finalizer.logger") as mock_logger:
            order_finalizer._calculate_order_trade_value(order, items, 0)

            # Verify error was logged
            assert mock_logger.debug.called or mock_logger.warning.called


# Tests for _get_order_status_and_price


class TestGetOrderStatusAndPrice:
    """Test _get_order_status_and_price method."""

    def test_successful_status_query(self, order_finalizer, mock_alpaca_manager):
        """Test successful order status query."""
        order_id = str(uuid.uuid4())
        mock_alpaca_manager.get_order_execution_result = Mock(
            return_value=Mock(
                status="filled",
                avg_fill_price=Decimal("101.25"),
                filled_qty=Decimal("10"),
            )
        )

        status, price = order_finalizer._get_order_status_and_price(order_id)

        assert status == "filled"
        assert price == Decimal("101.25")

    def test_status_without_price(self, order_finalizer, mock_alpaca_manager):
        """Test status query when price is not available."""
        order_id = str(uuid.uuid4())
        mock_alpaca_manager.get_order_execution_result = Mock(
            return_value=Mock(
                status="accepted",
                avg_fill_price=None,
                filled_qty=Decimal("0"),
            )
        )

        status, price = order_finalizer._get_order_status_and_price(order_id)

        assert status == "accepted"
        assert price is None

    def test_critical_alert_for_accepted_with_fills(self, order_finalizer, mock_alpaca_manager):
        """Test critical alert when order is accepted but has fills."""
        order_id = str(uuid.uuid4())
        mock_alpaca_manager.get_order_execution_result = Mock(
            return_value=Mock(
                status="accepted",
                avg_fill_price=None,
                filled_qty=Decimal("5"),  # Has fills but no price
            )
        )

        with patch("the_alchemiser.execution_v2.core.order_finalizer.logger") as mock_logger:
            order_finalizer._get_order_status_and_price(order_id)

            # Verify critical error was logged
            assert mock_logger.error.called
            error_call = mock_logger.error.call_args
            assert "potential API issue" in str(error_call).lower()

    def test_exception_returns_rejected(self, order_finalizer, mock_alpaca_manager):
        """Test that exception returns rejected status."""
        order_id = str(uuid.uuid4())
        mock_alpaca_manager.get_order_execution_result = Mock(side_effect=Exception("Broker error"))

        status, price = order_finalizer._get_order_status_and_price(order_id)

        assert status == "rejected"
        assert price is None

    def test_exception_is_logged(self, order_finalizer, mock_alpaca_manager):
        """Test that exceptions are logged with context."""
        order_id = str(uuid.uuid4())
        mock_alpaca_manager.get_order_execution_result = Mock(
            side_effect=ValueError("Invalid order")
        )

        with patch("the_alchemiser.execution_v2.core.order_finalizer.logger") as mock_logger:
            order_finalizer._get_order_status_and_price(order_id)

            # Verify warning was logged
            assert mock_logger.warning.called
            warning_call = mock_logger.warning.call_args
            assert "Failed to refresh order" in str(warning_call)


# Tests for _poll_order_completion


class TestPollOrderCompletion:
    """Test _poll_order_completion method."""

    def test_successful_polling(self, order_finalizer, mock_alpaca_manager):
        """Test successful order completion polling."""
        order_ids = [str(uuid.uuid4()), str(uuid.uuid4())]
        mock_alpaca_manager.wait_for_order_completion = Mock(return_value=Mock(status="completed"))

        # Should not raise
        order_finalizer._poll_order_completion(order_ids, 30, "BUY")

        mock_alpaca_manager.wait_for_order_completion.assert_called_once_with(
            order_ids, max_wait_seconds=30
        )

    def test_warning_on_no_status(self, order_finalizer, mock_alpaca_manager):
        """Test warning when status is None."""
        order_ids = [str(uuid.uuid4())]
        mock_alpaca_manager.wait_for_order_completion = Mock(return_value=Mock(status=None))

        with patch("the_alchemiser.execution_v2.core.order_finalizer.logger") as mock_logger:
            order_finalizer._poll_order_completion(order_ids, 30, "BUY")

            assert mock_logger.warning.called

    def test_exception_handling(self, order_finalizer, mock_alpaca_manager):
        """Test exception handling during polling."""
        order_ids = [str(uuid.uuid4())]
        mock_alpaca_manager.wait_for_order_completion = Mock(side_effect=Exception("Network error"))

        with patch("the_alchemiser.execution_v2.core.order_finalizer.logger") as mock_logger:
            # Should not raise
            order_finalizer._poll_order_completion(order_ids, 30, "BUY")

            # Verify exception was logged
            assert mock_logger.warning.called
            warning_call = mock_logger.warning.call_args
            assert "error while polling" in str(warning_call).lower()


# Tests for _build_final_status_map


class TestBuildFinalStatusMap:
    """Test _build_final_status_map method."""

    def test_invalid_ids_marked_as_rejected(self, order_finalizer):
        """Test that invalid IDs are pre-populated as rejected."""
        valid_ids = []
        invalid_ids = ["bad-id-1", "bad-id-2"]

        status_map = order_finalizer._build_final_status_map(valid_ids, invalid_ids)

        assert len(status_map) == 2
        assert status_map["bad-id-1"] == ("rejected", None)
        assert status_map["bad-id-2"] == ("rejected", None)

    def test_valid_ids_queried_from_broker(self, order_finalizer, mock_alpaca_manager):
        """Test that valid IDs are queried from broker."""
        valid_ids = [str(uuid.uuid4()), str(uuid.uuid4())]
        invalid_ids = []

        mock_alpaca_manager.get_order_execution_result = Mock(
            return_value=Mock(
                status="filled",
                avg_fill_price=Decimal("100"),
                filled_qty=Decimal("10"),
            )
        )

        status_map = order_finalizer._build_final_status_map(valid_ids, invalid_ids)

        assert len(status_map) == 2
        assert all(status == "filled" for status, _ in status_map.values())

    def test_mixed_valid_and_invalid_ids(self, order_finalizer, mock_alpaca_manager):
        """Test with both valid and invalid IDs."""
        valid_ids = [str(uuid.uuid4())]
        invalid_ids = ["bad-id"]

        mock_alpaca_manager.get_order_execution_result = Mock(
            return_value=Mock(
                status="filled",
                avg_fill_price=Decimal("100"),
                filled_qty=Decimal("10"),
            )
        )

        status_map = order_finalizer._build_final_status_map(valid_ids, invalid_ids)

        assert len(status_map) == 2
        assert status_map["bad-id"] == ("rejected", None)
        assert status_map[valid_ids[0]][0] == "filled"


# Integration Tests


class TestIntegration:
    """Integration tests for full finalization flow."""

    def test_full_finalization_flow_all_successful(self, order_finalizer, mock_alpaca_manager):
        """Test complete finalization flow with all orders successful."""
        order_ids = [str(uuid.uuid4()), str(uuid.uuid4())]
        orders = [
            _make_order_result(
                symbol="AAPL",
                success=False,
                price=None,
                order_id=order_ids[0],
                trade_amount=Decimal("1000"),
            ),
            _make_order_result(
                symbol="GOOGL",
                success=False,
                price=None,
                order_id=order_ids[1],
                trade_amount=Decimal("2000"),
            ),
        ]
        items = [
            _make_rebalance_item(symbol="AAPL", trade_amount=Decimal("1000")),
            _make_rebalance_item(symbol="GOOGL", trade_amount=Decimal("2000")),
        ]

        mock_alpaca_manager.get_order_execution_result = Mock(
            return_value=Mock(
                status="filled",
                avg_fill_price=Decimal("105.50"),
                filled_qty=Decimal("10"),
            )
        )

        result_orders, success_count, trade_value = order_finalizer.finalize_phase_orders(
            orders, items, "BUY", correlation_id="test-123"
        )

        assert len(result_orders) == 2
        assert success_count == 2
        assert trade_value == Decimal("3000")
        assert all(order.success for order in result_orders)
        assert all(order.price == Decimal("105.50") for order in result_orders)

    def test_full_finalization_flow_mixed_results(self, order_finalizer, mock_alpaca_manager):
        """Test finalization with mixed success/failure."""
        order_ids = [str(uuid.uuid4()), str(uuid.uuid4())]
        orders = [
            _make_order_result(symbol="AAPL", success=False, order_id=order_ids[0]),
            _make_order_result(symbol="GOOGL", success=False, order_id=order_ids[1]),
        ]
        items = [
            _make_rebalance_item(symbol="AAPL", trade_amount=Decimal("1000")),
            _make_rebalance_item(symbol="GOOGL", trade_amount=Decimal("2000")),
        ]

        def mock_get_result(order_id):
            if order_id == order_ids[0]:
                return Mock(
                    status="filled",
                    avg_fill_price=Decimal("100"),
                    filled_qty=Decimal("10"),
                )
            return Mock(
                status="rejected",
                avg_fill_price=None,
                filled_qty=Decimal("0"),
            )

        mock_alpaca_manager.get_order_execution_result = mock_get_result

        result_orders, success_count, trade_value = order_finalizer.finalize_phase_orders(
            orders, items, "BUY"
        )

        assert len(result_orders) == 2
        assert success_count == 1
        assert trade_value == Decimal("1000")  # Only first order
        assert result_orders[0].success is True
        assert result_orders[1].success is False
        assert result_orders[1].error_message == "Order rejected"
