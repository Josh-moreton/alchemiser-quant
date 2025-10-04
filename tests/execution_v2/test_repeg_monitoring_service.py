"""Business Unit: execution | Status: current

Unit tests for RepegMonitoringService refactoring.
Tests specifically validate the cognitive complexity reduction.
"""

import asyncio
import time
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, Mock

import pytest

from the_alchemiser.execution_v2.models.execution_result import OrderResult
from the_alchemiser.execution_v2.utils.repeg_monitoring_service import (
    RepegMonitoringService,
)


@pytest.fixture
def mock_smart_strategy():
    """Create a mock smart strategy for testing."""
    strategy = Mock()
    strategy.check_and_repeg_orders = AsyncMock(return_value=[])
    strategy.get_active_order_count = Mock(return_value=0)
    strategy.order_tracker.get_active_orders = Mock(return_value={})
    return strategy


@pytest.fixture
def sample_orders():
    """Create sample order results for testing."""
    return [
        OrderResult(
            symbol="TECL",
            action="BUY",
            trade_amount=Decimal("1000.00"),
            shares=Decimal("10"),
            price=Decimal("100.00"),
            order_id="test-order-1",
            success=True,
            error_message=None,
            timestamp=datetime.now(UTC),
            order_type="MARKET",  # Default to MARKET for tests
            filled_at=datetime.now(UTC),  # Set filled_at for successful order
        )
    ]


@pytest.mark.asyncio
async def test_check_and_process_repegs_no_strategy():
    """Test _check_and_process_repegs when smart_strategy is None."""
    service = RepegMonitoringService(smart_strategy=None)
    orders = []
    last_repeg_time = time.time()

    result_time, result_orders = await service._check_and_process_repegs(
        phase_type="BUY",
        orders=orders,
        attempts=0,
        elapsed_total=1.0,
        last_repeg_action_time=last_repeg_time,
    )

    # Time should not change when no strategy available
    assert result_time == last_repeg_time
    assert result_orders == orders


@pytest.mark.asyncio
async def test_check_and_process_repegs_no_results(mock_smart_strategy):
    """Test _check_and_process_repegs when no repeg results."""
    service = RepegMonitoringService(smart_strategy=mock_smart_strategy)
    orders = []
    last_repeg_time = time.time()

    result_time, result_orders = await service._check_and_process_repegs(
        phase_type="BUY",
        orders=orders,
        attempts=0,
        elapsed_total=1.0,
        last_repeg_action_time=last_repeg_time,
    )

    # check_and_repeg_orders should be called
    mock_smart_strategy.check_and_repeg_orders.assert_called_once()
    
    # Time should not change when no repeg results
    assert result_time == last_repeg_time
    assert result_orders == orders


@pytest.mark.asyncio
async def test_check_and_process_repegs_with_results(mock_smart_strategy, sample_orders):
    """Test _check_and_process_repegs when repeg results are present."""
    # Setup mock repeg result
    mock_result = Mock()
    mock_result.success = True
    mock_result.order_id = "new-order-1"
    mock_result.execution_strategy = "repeg"
    mock_result.repegs_used = 1
    mock_result.symbol = "TECL"
    mock_result.metadata = {"original_order_id": "test-order-1"}
    
    mock_smart_strategy.check_and_repeg_orders = AsyncMock(return_value=[mock_result])
    
    service = RepegMonitoringService(smart_strategy=mock_smart_strategy)
    last_repeg_time = time.time()
    
    # Sleep a tiny bit to ensure time difference
    await asyncio.sleep(0.01)
    
    result_time, result_orders = await service._check_and_process_repegs(
        phase_type="BUY",
        orders=sample_orders,
        attempts=0,
        elapsed_total=1.0,
        last_repeg_action_time=last_repeg_time,
    )

    # check_and_repeg_orders should be called
    mock_smart_strategy.check_and_repeg_orders.assert_called_once()
    
    # Time should be updated when repeg results exist
    assert result_time > last_repeg_time
    
    # Orders should be updated with new order ID
    assert len(result_orders) == 1
    assert result_orders[0].order_id == "new-order-1"


@pytest.mark.asyncio
async def test_execute_repeg_monitoring_loop_simplified_structure(mock_smart_strategy, sample_orders):
    """Test that execute_repeg_monitoring_loop uses the simplified structure."""
    service = RepegMonitoringService(smart_strategy=mock_smart_strategy)
    
    config = {
        "max_total_wait": 1,  # Short timeout
        "wait_between_checks": 0.1,
        "fill_wait_seconds": 10,
    }
    
    start_time = time.time()
    
    # Mock escalate to return same orders
    service._escalate_remaining_orders = AsyncMock(return_value=sample_orders)
    
    result_orders = await service.execute_repeg_monitoring_loop(
        phase_type="BUY",
        orders=sample_orders,
        config=config,
        start_time=start_time,
    )
    
    # Should complete successfully
    assert result_orders is not None
    assert len(result_orders) == len(sample_orders)
    
    # _escalate_remaining_orders should be called at the end
    service._escalate_remaining_orders.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
