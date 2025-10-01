"""Business Unit: execution | Status: current

Test for replace_order functionality in RepegManager.

This test module verifies that the RepegManager correctly uses Alpaca's
replace_order API instead of cancel-and-resubmit, with proper fallback behavior.
"""

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import Mock

import pytest

from the_alchemiser.execution_v2.core.smart_execution_strategy.models import (
    ExecutionConfig,
    SmartOrderRequest,
)
from the_alchemiser.execution_v2.core.smart_execution_strategy.repeg import RepegManager
from the_alchemiser.execution_v2.core.smart_execution_strategy.tracking import OrderTracker
from the_alchemiser.shared.schemas.broker import OrderExecutionResult


@pytest.fixture
def mock_alpaca_manager():
    """Mock Alpaca manager for testing."""
    manager = Mock()
    manager.cancel_order = Mock(return_value=True)
    manager.place_limit_order = Mock()
    manager.get_order_execution_result = Mock()
    manager.replace_order = Mock()
    manager._check_order_completion_status = Mock(return_value=None)
    return manager


@pytest.fixture
def mock_quote_provider():
    """Mock quote provider for testing."""
    provider = Mock()
    quote = Mock()
    quote.bid_price = 100.0
    quote.ask_price = 100.50
    quote.bid_size = 1000
    quote.ask_size = 1000
    provider.get_quote_with_validation = Mock(return_value=(quote, True))
    return provider


@pytest.fixture
def mock_pricing_calculator():
    """Mock pricing calculator for testing."""
    calculator = Mock()
    calculator.calculate_repeg_price = Mock(return_value=Decimal("100.25"))
    return calculator


@pytest.fixture
def order_tracker():
    """Real order tracker for testing."""
    return OrderTracker()


@pytest.fixture
def execution_config_with_replace():
    """Execution configuration with replace_order enabled."""
    return ExecutionConfig(
        max_repegs_per_order=5,
        fill_wait_seconds=30,
        use_replace_order=True,
        replace_order_fallback=True,
    )


@pytest.fixture
def execution_config_without_replace():
    """Execution configuration with replace_order disabled."""
    return ExecutionConfig(
        max_repegs_per_order=5,
        fill_wait_seconds=30,
        use_replace_order=False,
        replace_order_fallback=True,
    )


@pytest.fixture
def repeg_manager_with_replace(
    mock_alpaca_manager,
    mock_quote_provider,
    mock_pricing_calculator,
    order_tracker,
    execution_config_with_replace,
):
    """RepegManager instance with replace_order enabled."""
    return RepegManager(
        alpaca_manager=mock_alpaca_manager,
        quote_provider=mock_quote_provider,
        pricing_calculator=mock_pricing_calculator,
        order_tracker=order_tracker,
        config=execution_config_with_replace,
    )


@pytest.fixture
def repeg_manager_without_replace(
    mock_alpaca_manager,
    mock_quote_provider,
    mock_pricing_calculator,
    order_tracker,
    execution_config_without_replace,
):
    """RepegManager instance with replace_order disabled."""
    return RepegManager(
        alpaca_manager=mock_alpaca_manager,
        quote_provider=mock_quote_provider,
        pricing_calculator=mock_pricing_calculator,
        order_tracker=order_tracker,
        config=execution_config_without_replace,
    )


@pytest.mark.asyncio
async def test_replace_order_success(
    repeg_manager_with_replace, mock_alpaca_manager, order_tracker
):
    """Test successful replace_order operation."""
    # Setup initial order
    order_id = "test-order-123"
    original_qty = Decimal("100")
    filled_qty = Decimal("40")  # Partial fill
    remaining_qty = original_qty - filled_qty

    request = SmartOrderRequest(
        symbol="TECL",
        side="SELL",
        quantity=original_qty,
        correlation_id="test-correlation-123",
        is_complete_exit=False,
    )

    # Add order to tracker
    order_tracker.add_order(
        order_id=order_id,
        request=request,
        placement_time=datetime.now(UTC),
        anchor_price=Decimal("100.00"),
    )

    # Mock order execution result with partial fill
    mock_order_result = OrderExecutionResult(
        success=True,
        order_id=order_id,
        status="partially_filled",
        filled_qty=filled_qty,
        avg_fill_price=Decimal("100.10"),
        submitted_at=datetime.now(UTC),
    )
    mock_alpaca_manager.get_order_execution_result.return_value = mock_order_result

    # Mock successful replace_order result
    replace_result = OrderExecutionResult(
        success=True,
        order_id=order_id,  # Same order ID
        status="accepted",
        filled_qty=filled_qty,
        avg_fill_price=Decimal("100.10"),
        submitted_at=datetime.now(UTC),
    )
    mock_alpaca_manager.replace_order.return_value = replace_result

    # Execute replace
    result = await repeg_manager_with_replace._attempt_replace(order_id, request)

    # Verify replace_order was called
    mock_alpaca_manager.replace_order.assert_called_once()
    call_args = mock_alpaca_manager.replace_order.call_args

    # Verify the request had correct parameters
    assert call_args[0][0] == order_id
    replace_request = call_args[0][1]
    assert replace_request.qty == float(remaining_qty)
    assert replace_request.limit_price == 100.25  # From mock pricing calculator

    # Verify success
    assert result.success is True
    assert result.order_id == order_id  # Same order ID
    assert "replace" in result.execution_strategy

    # Verify order tracking was updated in place (same ID)
    assert order_tracker.get_repeg_count(order_id) == 1
    assert order_tracker.get_anchor_price(order_id) == Decimal("100.25")

    # Verify cancel_order was NOT called
    mock_alpaca_manager.cancel_order.assert_not_called()


@pytest.mark.asyncio
async def test_replace_order_falls_back_on_error(
    repeg_manager_with_replace, mock_alpaca_manager, order_tracker
):
    """Test that replace_order falls back to cancel-and-resubmit on errors."""
    # Setup initial order
    order_id = "test-order-123"
    original_qty = Decimal("100")

    request = SmartOrderRequest(
        symbol="TECL",
        side="SELL",
        quantity=original_qty,
        correlation_id="test-correlation-123",
        is_complete_exit=False,
    )

    # Add order to tracker
    order_tracker.add_order(
        order_id=order_id,
        request=request,
        placement_time=datetime.now(UTC),
        anchor_price=Decimal("100.00"),
    )

    # Mock order execution result
    mock_order_result = OrderExecutionResult(
        success=True,
        order_id=order_id,
        status="accepted",
        filled_qty=Decimal("0"),
        avg_fill_price=None,
        submitted_at=datetime.now(UTC),
    )
    mock_alpaca_manager.get_order_execution_result.return_value = mock_order_result

    # Mock replace_order to raise "order not replaceable" error
    mock_alpaca_manager.replace_order.side_effect = Exception(
        "Order not replaceable in current state"
    )

    # Mock successful fallback cancel
    mock_alpaca_manager.cancel_order.return_value = True
    mock_alpaca_manager._check_order_completion_status.return_value = "CANCELED"

    # Mock successful fallback order placement
    new_order = Mock()
    new_order.success = True
    new_order.order_id = "550e8400-e29b-41d4-a716-446655440000"  # Valid UUID
    mock_alpaca_manager.place_limit_order.return_value = new_order

    # Execute replace (should fall back)
    result = await repeg_manager_with_replace._attempt_replace(order_id, request)

    # Verify replace_order was attempted
    mock_alpaca_manager.replace_order.assert_called_once()

    # Verify fallback to cancel-and-resubmit was triggered
    mock_alpaca_manager.cancel_order.assert_called_once_with(order_id)
    mock_alpaca_manager.place_limit_order.assert_called_once()

    # Verify result
    assert result.success is True
    assert result.order_id == "550e8400-e29b-41d4-a716-446655440000"  # New order ID from fallback


@pytest.mark.asyncio
async def test_replace_order_disabled_uses_cancel_resubmit(
    repeg_manager_without_replace, mock_alpaca_manager, order_tracker
):
    """Test that when replace_order is disabled, cancel-and-resubmit is used."""
    # Setup initial order
    order_id = "test-order-123"
    original_qty = Decimal("100")

    request = SmartOrderRequest(
        symbol="TECL",
        side="SELL",
        quantity=original_qty,
        correlation_id="test-correlation-123",
        is_complete_exit=False,
    )

    # Add order to tracker
    order_tracker.add_order(
        order_id=order_id,
        request=request,
        placement_time=datetime.now(UTC),
        anchor_price=Decimal("100.00"),
    )

    # Mock order execution result
    mock_order_result = OrderExecutionResult(
        success=True,
        order_id=order_id,
        status="accepted",
        filled_qty=Decimal("0"),
        avg_fill_price=None,
        submitted_at=datetime.now(UTC),
    )
    mock_alpaca_manager.get_order_execution_result.return_value = mock_order_result

    # Mock successful cancel
    mock_alpaca_manager.cancel_order.return_value = True
    mock_alpaca_manager._check_order_completion_status.return_value = "CANCELED"

    # Mock successful order placement
    new_order = Mock()
    new_order.success = True
    new_order.order_id = "550e8400-e29b-41d4-a716-446655440000"  # Valid UUID
    mock_alpaca_manager.place_limit_order.return_value = new_order

    # Execute repeg (should use cancel-and-resubmit)
    result = await repeg_manager_without_replace._attempt_repeg(order_id, request)

    # Verify replace_order was NOT called
    mock_alpaca_manager.replace_order.assert_not_called()

    # Verify cancel-and-resubmit was used
    mock_alpaca_manager.cancel_order.assert_called_once_with(order_id)
    mock_alpaca_manager.place_limit_order.assert_called_once()

    # Verify result
    assert result.success is True
    assert result.order_id == "550e8400-e29b-41d4-a716-446655440000"  # New order ID


@pytest.mark.asyncio
async def test_order_tracker_update_in_place(order_tracker):
    """Test that OrderTracker.update_order_in_place maintains the same order ID."""
    # Setup initial order
    order_id = "test-order-123"
    original_qty = Decimal("100")
    original_price = Decimal("100.00")

    request = SmartOrderRequest(
        symbol="TECL",
        side="SELL",
        quantity=original_qty,
        correlation_id="test-correlation-123",
        is_complete_exit=False,
    )

    # Add order to tracker
    order_tracker.add_order(
        order_id=order_id,
        request=request,
        placement_time=datetime.now(UTC),
        anchor_price=original_price,
    )

    # Verify initial state
    assert order_tracker.get_repeg_count(order_id) == 0
    assert order_tracker.get_anchor_price(order_id) == original_price
    assert len(order_tracker.get_price_history(order_id)) == 1

    # Update in place (as replace_order would)
    new_price = Decimal("100.25")
    order_tracker.update_order_in_place(
        order_id=order_id,
        new_anchor_price=new_price,
        placement_time=datetime.now(UTC),
    )

    # Verify order ID is still the same
    assert order_tracker.get_order_request(order_id) == request

    # Verify updates were applied
    assert order_tracker.get_repeg_count(order_id) == 1
    assert order_tracker.get_anchor_price(order_id) == new_price
    assert len(order_tracker.get_price_history(order_id)) == 2
    assert order_tracker.get_price_history(order_id)[0] == original_price
    assert order_tracker.get_price_history(order_id)[1] == new_price


@pytest.mark.asyncio
async def test_replace_order_with_failed_result(
    repeg_manager_with_replace, mock_alpaca_manager, order_tracker
):
    """Test that failed replace_order result triggers fallback."""
    # Setup initial order
    order_id = "test-order-123"
    original_qty = Decimal("100")

    request = SmartOrderRequest(
        symbol="TECL",
        side="SELL",
        quantity=original_qty,
        correlation_id="test-correlation-123",
        is_complete_exit=False,
    )

    # Add order to tracker
    order_tracker.add_order(
        order_id=order_id,
        request=request,
        placement_time=datetime.now(UTC),
        anchor_price=Decimal("100.00"),
    )

    # Mock order execution result
    mock_order_result = OrderExecutionResult(
        success=True,
        order_id=order_id,
        status="accepted",
        filled_qty=Decimal("0"),
        avg_fill_price=None,
        submitted_at=datetime.now(UTC),
    )
    mock_alpaca_manager.get_order_execution_result.return_value = mock_order_result

    # Mock failed replace_order result (success=False)
    replace_result = OrderExecutionResult(
        success=False,
        order_id=order_id,
        status="rejected",
        filled_qty=Decimal("0"),
        error="Order cannot be replaced",
        submitted_at=datetime.now(UTC),
    )
    mock_alpaca_manager.replace_order.return_value = replace_result

    # Mock successful fallback cancel
    mock_alpaca_manager.cancel_order.return_value = True
    mock_alpaca_manager._check_order_completion_status.return_value = "CANCELED"

    # Mock successful fallback order placement
    new_order = Mock()
    new_order.success = True
    new_order.order_id = "550e8400-e29b-41d4-a716-446655440000"  # Valid UUID
    mock_alpaca_manager.place_limit_order.return_value = new_order

    # Execute replace (should fall back due to failed result)
    result = await repeg_manager_with_replace._attempt_replace(order_id, request)

    # Verify replace_order was attempted
    mock_alpaca_manager.replace_order.assert_called_once()

    # Verify fallback was triggered
    mock_alpaca_manager.cancel_order.assert_called_once_with(order_id)
    mock_alpaca_manager.place_limit_order.assert_called_once()

    # Verify result
    assert result.success is True
    assert result.order_id == "550e8400-e29b-41d4-a716-446655440000"
