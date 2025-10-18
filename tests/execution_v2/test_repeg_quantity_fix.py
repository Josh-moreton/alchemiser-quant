"""Business Unit: execution | Status: current

Test for the re-peg quantity fix to ensure partial fills are handled correctly.
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
from the_alchemiser.shared.schemas.operations import OrderCancellationResult


@pytest.fixture
def mock_alpaca_manager():
    """Mock Alpaca manager for testing."""
    manager = Mock()
    manager.cancel_order = Mock(return_value=OrderCancellationResult(success=True))
    manager.place_limit_order = Mock()
    manager.get_order_execution_result = Mock()
    manager._check_order_completion_status = Mock(return_value="CANCELED")
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
def execution_config():
    """Execution configuration for testing."""
    return ExecutionConfig(
        max_repegs_per_order=5,
        fill_wait_seconds=30,
    )


@pytest.fixture
def repeg_manager(
    mock_alpaca_manager,
    mock_quote_provider,
    mock_pricing_calculator,
    order_tracker,
    execution_config,
):
    """RepegManager instance for testing."""
    return RepegManager(
        alpaca_manager=mock_alpaca_manager,
        quote_provider=mock_quote_provider,
        pricing_calculator=mock_pricing_calculator,
        order_tracker=order_tracker,
        config=execution_config,
    )


@pytest.mark.asyncio
async def test_repeg_uses_remaining_quantity_after_partial_fill(
    repeg_manager, mock_alpaca_manager, order_tracker
):
    """Test that re-peg uses remaining quantity after partial fill."""
    # Setup initial order
    order_id = "test-order-123"
    original_qty = Decimal("100")
    filled_qty = Decimal("40")  # Partial fill
    remaining_qty = original_qty - filled_qty

    request = SmartOrderRequest(
        symbol="TECL",
        side="SELL",
        quantity=original_qty,
        correlation_id="test-correlation-id",
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

    # Mock successful order placement
    new_order = OrderExecutionResult(
        success=True,
        order_id="550e8400-e29b-41d4-a716-446655440000",  # Valid UUID
        status="accepted",
        filled_qty=Decimal("0"),
        avg_fill_price=None,
        submitted_at=datetime.now(UTC),
    )
    mock_alpaca_manager.place_limit_order.return_value = new_order

    # Execute repeg
    result = await repeg_manager._attempt_repeg(order_id, request)

    # Verify the order was placed with remaining quantity, not original
    mock_alpaca_manager.place_limit_order.assert_called_once()
    call_args = mock_alpaca_manager.place_limit_order.call_args

    # Check that quantity passed is the remaining quantity (60.0)
    assert call_args[1]["quantity"] == float(remaining_qty)
    assert result.success is True

    # Verify filled quantity was tracked for the NEW order
    assert order_tracker.get_filled_quantity("550e8400-e29b-41d4-a716-446655440000") == filled_qty


@pytest.mark.asyncio
async def test_repeg_handles_insufficient_quantity_error(
    repeg_manager, mock_alpaca_manager, order_tracker
):
    """Test that re-peg handles insufficient quantity errors gracefully."""
    # Setup initial order
    order_id = "test-order-123"
    original_qty = Decimal("100")
    filled_qty = Decimal("70")  # Large partial fill

    request = SmartOrderRequest(
        symbol="TECL",
        side="SELL",
        quantity=original_qty,
        correlation_id="test-correlation-id",
        is_complete_exit=False,
    )

    # Add order to tracker
    order_tracker.add_order(
        order_id=order_id,
        request=request,
        placement_time=datetime.now(UTC),
        anchor_price=Decimal("100.00"),
    )

    # Mock order execution result with large partial fill
    mock_order_result = OrderExecutionResult(
        success=True,
        order_id=order_id,
        status="partially_filled",
        filled_qty=filled_qty,
        avg_fill_price=Decimal("100.10"),
        submitted_at=datetime.now(UTC),
    )
    mock_alpaca_manager.get_order_execution_result.return_value = mock_order_result

    # Mock insufficient quantity error on first attempt
    insufficient_error = Exception(
        '{"code":40310000, "message":"insufficient qty available for order '
        '(requested: 30.000000, available: 20.000000)"}'
    )

    # Mock successful retry with available quantity
    successful_order = OrderExecutionResult(
        success=True,
        order_id="660e8400-e29b-41d4-a716-446655440001",  # Valid UUID
        status="accepted",
        filled_qty=Decimal("0"),
        avg_fill_price=None,
        submitted_at=datetime.now(UTC),
    )

    # Configure mock to fail first, succeed second
    mock_alpaca_manager.place_limit_order.side_effect = [insufficient_error, successful_order]

    # Execute repeg
    result = await repeg_manager._attempt_repeg(order_id, request)

    # Verify retry occurred with available quantity
    assert mock_alpaca_manager.place_limit_order.call_count == 2

    # Check second call used available quantity (20.0)
    second_call_args = mock_alpaca_manager.place_limit_order.call_args_list[1]
    assert second_call_args[1]["quantity"] == 20.0  # Available quantity from error message

    assert result.success is True


@pytest.mark.asyncio
async def test_repeg_completes_order_when_remaining_quantity_too_small(
    repeg_manager, mock_alpaca_manager, order_tracker
):
    """Test that re-peg considers order complete when remaining quantity is too small."""
    # Setup initial order
    order_id = "test-order-123"
    original_qty = Decimal("100")
    filled_qty = Decimal("99.995")  # Almost completely filled

    request = SmartOrderRequest(
        symbol="TECL",
        side="SELL",
        quantity=original_qty,
        correlation_id="test-correlation-id",
        is_complete_exit=False,
    )

    # Add order to tracker
    order_tracker.add_order(
        order_id=order_id,
        request=request,
        placement_time=datetime.now(UTC),
        anchor_price=Decimal("100.00"),
    )

    # Mock order execution result with almost complete fill
    mock_order_result = OrderExecutionResult(
        success=True,
        order_id=order_id,
        status="partially_filled",
        filled_qty=filled_qty,
        avg_fill_price=Decimal("100.10"),
        submitted_at=datetime.now(UTC),
    )
    mock_alpaca_manager.get_order_execution_result.return_value = mock_order_result

    # Execute repeg
    result = await repeg_manager._attempt_repeg(order_id, request)

    # Should return None (remove from tracking) since remaining quantity is tiny
    assert result is None

    # Verify no order placement was attempted
    mock_alpaca_manager.place_limit_order.assert_not_called()


def test_order_tracker_remaining_quantity_calculation(order_tracker):
    """Test that order tracker correctly calculates remaining quantities."""
    order_id = "test-order-123"
    original_qty = Decimal("100")

    request = SmartOrderRequest(
        symbol="TECL",
        side="SELL",
        quantity=original_qty,
        correlation_id="test-correlation-id",
        is_complete_exit=False,
    )

    # Add order to tracker
    order_tracker.add_order(
        order_id=order_id,
        request=request,
        placement_time=datetime.now(UTC),
        anchor_price=Decimal("100.00"),
    )

    # Initially no fills
    assert order_tracker.get_remaining_quantity(order_id) == original_qty

    # Update with partial fill
    filled_qty = Decimal("30")
    order_tracker.update_filled_quantity(order_id, filled_qty)

    expected_remaining = original_qty - filled_qty
    assert order_tracker.get_remaining_quantity(order_id) == expected_remaining

    # Update with larger fill
    filled_qty = Decimal("80")
    order_tracker.update_filled_quantity(order_id, filled_qty)

    expected_remaining = original_qty - filled_qty
    assert order_tracker.get_remaining_quantity(order_id) == expected_remaining

    # Test over-fill protection (should return 0, not negative)
    filled_qty = Decimal("120")  # More than original
    order_tracker.update_filled_quantity(order_id, filled_qty)

    assert order_tracker.get_remaining_quantity(order_id) == Decimal("0")
