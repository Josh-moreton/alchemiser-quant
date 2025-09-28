"""Business Unit: execution | Status: current

Test for the replace order functionality in repeg operations.
"""

import asyncio
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, Mock
import uuid

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
    """Mock Alpaca manager with replace functionality."""
    manager = Mock()
    manager.cancel_order = Mock(return_value=True)
    manager.place_limit_order = Mock()
    manager.get_order_execution_result = Mock()
    # Add the new replace_order_by_id method
    manager.replace_order_by_id = Mock()
    return manager


@pytest.fixture
def mock_quote_provider():
    """Mock quote provider for testing."""
    provider = Mock()
    provider.get_quote_with_validation = Mock()
    return provider


@pytest.fixture
def mock_pricing_calculator():
    """Mock pricing calculator for testing."""
    calculator = Mock()
    calculator.calculate_repeg_price = Mock()
    return calculator


@pytest.fixture
def order_tracker():
    """Order tracker instance for testing."""
    return OrderTracker()


@pytest.fixture
def execution_config():
    """Execution configuration for testing."""
    return ExecutionConfig(
        max_repegs_per_order=5,
        fill_wait_seconds=30,
    )


@pytest.fixture
def repeg_manager(mock_alpaca_manager, mock_quote_provider, mock_pricing_calculator, order_tracker, execution_config):
    """RepegManager instance for testing."""
    return RepegManager(
        alpaca_manager=mock_alpaca_manager,
        quote_provider=mock_quote_provider,
        pricing_calculator=mock_pricing_calculator,
        order_tracker=order_tracker,
        config=execution_config,
    )


@pytest.mark.asyncio
async def test_replace_for_repeg_success(repeg_manager, mock_alpaca_manager):
    """Test successful order replacement."""
    # Setup test data
    order_id = "test-order-123"
    new_price = Decimal("100.25")
    remaining_qty = Decimal("50")
    
    # Mock successful replace result
    mock_result = OrderExecutionResult(
        order_id=order_id,
        status="accepted",
        success=True,
        filled_qty=Decimal("0"),
        avg_fill_price=None,
        submitted_at=datetime.now(UTC),
        execution_timestamp=datetime.now(UTC),
    )
    mock_alpaca_manager.replace_order_by_id.return_value = mock_result
    
    # Execute replace
    result = await repeg_manager._replace_for_repeg(order_id, new_price, remaining_qty)
    
    # Verify the replace was called with correct parameters
    mock_alpaca_manager.replace_order_by_id.assert_called_once_with(
        order_id=order_id,
        quantity=float(remaining_qty),
        limit_price=float(new_price),
        time_in_force="day"
    )
    
    # Verify the result
    assert result is not None
    assert result.success is True
    assert result.order_id == order_id
    assert result.final_price == new_price
    assert result.execution_strategy == "replace_repeg"


@pytest.mark.asyncio
async def test_replace_for_repeg_failure(repeg_manager, mock_alpaca_manager):
    """Test failed order replacement."""
    # Setup test data
    order_id = "test-order-123"
    new_price = Decimal("100.25")
    remaining_qty = Decimal("50")
    
    # Mock failed replace result
    mock_result = OrderExecutionResult(
        order_id=order_id,
        status="rejected",
        success=False,
        error_message="Insufficient buying power",
        filled_qty=Decimal("0"),
        avg_fill_price=None,
        submitted_at=datetime.now(UTC),
        execution_timestamp=datetime.now(UTC),
    )
    mock_alpaca_manager.replace_order_by_id.return_value = mock_result
    
    # Execute replace
    result = await repeg_manager._replace_for_repeg(order_id, new_price, remaining_qty)
    
    # Verify the result
    assert result is None


@pytest.mark.asyncio
async def test_replace_for_repeg_exception(repeg_manager, mock_alpaca_manager):
    """Test order replacement when exception is raised."""
    # Setup test data
    order_id = "test-order-123"
    new_price = Decimal("100.25")
    remaining_qty = Decimal("50")
    
    # Mock exception during replace
    mock_alpaca_manager.replace_order_by_id.side_effect = Exception("Network error")
    
    # Execute replace
    result = await repeg_manager._replace_for_repeg(order_id, new_price, remaining_qty)
    
    # Verify the result
    assert result is None


@pytest.mark.asyncio
async def test_attempt_repeg_uses_replace_instead_of_cancel(repeg_manager, mock_alpaca_manager, mock_quote_provider, mock_pricing_calculator, order_tracker):
    """Test that _attempt_repeg uses replace functionality instead of cancel+resend."""
    # Setup test data
    order_id = "test-order-123"
    original_qty = Decimal("100")
    remaining_qty = Decimal("75")  # Partial fill
    new_price = Decimal("100.50")
    
    request = SmartOrderRequest(
        symbol="TECL",
        side="BUY", 
        quantity=original_qty,
        is_complete_exit=False,
        correlation_id="test-correlation-123"
    )
    
    # Add order to tracker
    order_tracker.add_order(
        order_id=order_id,
        request=request,
        placement_time=datetime.now(UTC),
        anchor_price=Decimal("100.00"),
    )
    
    # Mock order status check (partial fill)
    order_result = OrderExecutionResult(
        order_id=order_id,
        status="partially_filled",
        success=True,
        filled_qty=original_qty - remaining_qty,  # 25 filled
        avg_fill_price=Decimal("100.00"),
        submitted_at=datetime.now(UTC),
        execution_timestamp=datetime.now(UTC),
    )
    mock_alpaca_manager.get_order_execution_result.return_value = order_result
    
    # Mock quote and pricing
    mock_quote = Mock()
    mock_quote.bid_price = 100.40
    mock_quote.ask_price = 100.60
    mock_quote.bid_size = 1000
    mock_quote.ask_size = 500
    mock_quote_provider.get_quote_with_validation.return_value = (mock_quote, True)
    mock_pricing_calculator.calculate_repeg_price.return_value = new_price
    
    # Mock successful replace
    replace_result = OrderExecutionResult(
        order_id=order_id,
        status="accepted",
        success=True,
        filled_qty=Decimal("0"),
        avg_fill_price=None,
        submitted_at=datetime.now(UTC),
        execution_timestamp=datetime.now(UTC),
    )
    mock_alpaca_manager.replace_order_by_id.return_value = replace_result
    
    # Execute repeg
    result = await repeg_manager._attempt_repeg(order_id, request)
    
    # Verify that replace was called instead of cancel+place
    mock_alpaca_manager.replace_order_by_id.assert_called_once()
    mock_alpaca_manager.cancel_order.assert_not_called()
    mock_alpaca_manager.place_limit_order.assert_not_called()
    
    # Verify the result
    assert result is not None
    assert result.success is True
    assert result.order_id == order_id  # Same order ID since replaced in-place
    assert "replace_repeg" in result.execution_strategy


@pytest.mark.asyncio
async def test_repeg_maintains_same_external_interface(repeg_manager, mock_alpaca_manager, mock_quote_provider, mock_pricing_calculator, order_tracker):
    """Test that the repeg functionality maintains the same external interface despite internal changes."""
    # Setup test data
    order_id = "test-order-456"
    original_qty = Decimal("200")
    remaining_qty = Decimal("150")
    new_price = Decimal("99.75")
    
    request = SmartOrderRequest(
        symbol="TQQQ",
        side="SELL", 
        quantity=original_qty,
        is_complete_exit=False,
        correlation_id="test-correlation-456"
    )
    
    # Add order to tracker
    order_tracker.add_order(
        order_id=order_id,
        request=request,
        placement_time=datetime.now(UTC),
        anchor_price=Decimal("100.00"),
    )
    
    # Mock order status check (partial fill)
    order_result = OrderExecutionResult(
        order_id=order_id,
        status="partially_filled",
        success=True,
        filled_qty=original_qty - remaining_qty,  # 50 filled
        avg_fill_price=Decimal("100.00"),
        submitted_at=datetime.now(UTC),
        execution_timestamp=datetime.now(UTC),
    )
    mock_alpaca_manager.get_order_execution_result.return_value = order_result
    
    # Mock quote and pricing
    mock_quote = Mock()
    mock_quote.bid_price = 99.70
    mock_quote.ask_price = 99.80
    mock_quote.bid_size = 2000
    mock_quote.ask_size = 1500
    mock_quote_provider.get_quote_with_validation.return_value = (mock_quote, True)
    mock_pricing_calculator.calculate_repeg_price.return_value = new_price
    
    # Mock successful replace
    replace_result = OrderExecutionResult(
        order_id=order_id,
        status="accepted",
        success=True,
        filled_qty=Decimal("0"),
        avg_fill_price=None,
        submitted_at=datetime.now(UTC),
        execution_timestamp=datetime.now(UTC),
    )
    mock_alpaca_manager.replace_order_by_id.return_value = replace_result
    
    # Execute repeg
    result = await repeg_manager._attempt_repeg(order_id, request)
    
    # Verify the result maintains expected structure
    assert result is not None
    assert hasattr(result, 'success')
    assert hasattr(result, 'order_id')
    assert hasattr(result, 'final_price')
    assert hasattr(result, 'execution_strategy')
    assert hasattr(result, 'placement_timestamp')
    assert hasattr(result, 'metadata')
    
    # Verify the expected values
    assert result.success is True
    assert result.order_id == order_id
    assert result.final_price == new_price
    assert result.metadata is not None
    assert 'original_order_id' in result.metadata
    assert 'new_price' in result.metadata
    assert 'bid_price' in result.metadata
    assert 'ask_price' in result.metadata